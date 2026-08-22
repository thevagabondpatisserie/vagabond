"""Kiem banh theo MUA: hang san xuat mot lo, ban het la thoi.

Anh Viet dat ngay 17/08/2026, mua Trung thu 2026.

Vi sao khong dung duoc bang kiem banh theo ngay
-----------------------------------------------
Bang theo ngay tra loi cau hoi "hom nay con bao nhieu cai de ban". Moi
sang dem lai tu dau, vi bep lam moi ngay.

Hang mua vu tra loi mot cau khac han: "ca mua nay con bao nhieu cai".
Hop MOONLAPIS in 100 hop la 100, khong co chuyen mai lam them. Khach dat
giao ngay 25/09 va khach dat giao ngay 02/10 deu an vao cung mot con so
100 do. Nen:

  - Nguon hang khong phai ton dau cong bep lam, ma la MOT HAN MUC nhap tay.
    Nha in giao them thi sua len, hop hong thi sua xuong - anh Viet noi ro
    "de cac ban tu nhap tu theo doi".
  - Pham vi dem khong phai mot ngay ma la CA KHOANG MUA.
  - Va can them mot thu bang ngay khong co: LICH THEO NGAY, de sales nhin
    ra ngay nao dang don nhieu ma con lieu chia banh.

Ke thua nguyen si tu bang theo ngay (chot voi anh Viet 01/08, van dung):
  - "Da dat"   = don DA CHOT trong khoang mua.
  - "Cho chot" = don con trang thai Moi - sales dang tu van, giu cho mem.
    TRU AO vao con ban duoc. Voi hang gioi han thi cang phai tru: mot don
    giu cho chua chot van la mot hop khong con de ban cho nguoi khac.
  - "Kenh khac" = ban qua Grab, Shopee, quay - khong di qua Pancake nen
    dem thang tu hoa don ban ra.
  - Trang thai 6 (huy) va 7 (xoa) khong dem.
  - Loc don theo ngay giao bang updateStatus=estimate_delivery_date, moc
    thoi gian la UNIX GIAY (truyen ISO thi Pancake tra 0 don ma khong bao
    loi - he nay da nga o do mot lan).

Ma hang mua vu mang tien to BASS
--------------------------------
Kiem tren he 17/08/2026: toan bo hang mua vu deu la BASS - hai hop
MOONGARDEN va MOONLAPIS, tam banh le 110g, hai banh deo 150g, va ca banh
Ba Trang, Khuc Cay, Panettone cua cac mua truoc.

Nghia la bang kiem banh theo ngay (chi dem BAWC va BAWS) chua bao gio dem
banh trung thu, va do chinh la cho trong ma bang nay lap vao.
"""

import json
from datetime import datetime, timedelta

import frappe
from frappe.utils import cint, getdate, now_datetime

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

DT = "Vagabond Mua Vu"
SI = "Sales Invoice"

# Con duoi bao nhieu phan tram han muc thi hien chip do tren trang chu.
# Anh Viet chot 10 phan tram ngay 18/08/2026.
NGUONG_CANH_BAO = 10.0
BO_QUA_TT = {6, 7}  # da huy, da xoa

# Hang mua vu tren he deu mang tien to BASS.
#
# Chay thu that 17/08/2026 va sua ngay
# ------------------------------------
# Ban dau em cho ca BAWC va BAWS vao day, nghi rang "mot mua co the ban kem
# banh thuong". Dong bo thu mua Trung thu 2026 thi bang phinh ra 67 dong -
# toan bo banh o ban trong ba thang - trong khi hang trung thu chi co 12.
# Sales mo ra phai cuon qua 55 dong khong lien quan moi thay hop MOONLAPIS.
#
# Nen tach lam hai muc:
#   TU_THEM  - chi BASS moi duoc may TU dua vao bang.
#   DEM_CHO  - dong da nam trong bang thi dem, du mang tien to gi. Sales
#              bam Them san pham keo mot banh o vao mua qua tang thi no
#              van duoc dem binh thuong.
TU_THEM = ("BASS",)
TIEN_TO_MA = ("BASS", "BAWC", "BAWS")

MAX_TRANG = 30  # ca mua vai thang, nhieu don hon mot ngay
GIAN_CACH_DONG_BO = 20  # giay. Man tu xin moi 30 giay nen gian cach phai nho hon.

# Tran ngay cua mot mua. Mot mua dai hon nua nam thi gan nhu chac la go
# nham ngay, va keo Pancake ca nam la mot cu goi rat nang.
SO_NGAY_TOI_DA = 200


# ===================================================================
# PHEP THUAN - bo kiem thu chay duoc khong can site
# ===================================================================
#
# Ba phep duoi day la LOI cua ca phan he, va chung nam o day chu khong nam
# trong lop Document. Ly do: lop Document can mot site that moi chay duoc,
# nen neu de phep o do thi bo kiem thu phai co ban sao rieng - dung cai bay
# "hai ban song song" da lam hong ba viec ngay 16/08/2026.
#
# Lop Document GOI ba ham nay. Mot cho tinh, mot cho kiem.


def han_muc_tu_dot(cac_dot):
	"""Han muc that theo tung ma hang, tinh tu cac dot nha in. THUAN.

	cac_dot: list dict co ma_hang, so_luong, da_ve.

	Tra dict RONG neu khong khai dot nao - luc do o go tay giu nguyen hieu
	luc. Mot ma DA khai dot nhung chua dot nao ve thi tra 0, va do la dung:
	hang chua co trong tay.

	Vi sao chi dot DA VE moi cong (anh Viet chot 18/08/2026): mot dot hen
	25/09 ma hom nay moi 20/09 thi so hop do CHUA co that. Cong truoc la ban
	tren mot con so chua ton tai, den 25/09 nha in giao thieu thi hop da vao
	tay khach het roi, khong con duong lui.
	"""
	ra = {}
	for x in cac_dot or []:
		ma = str((x or {}).get("ma_hang") or "").strip()
		if not ma:
			continue
		ra.setdefault(ma, 0)
		if cint((x or {}).get("da_ve")):
			ra[ma] += cint((x or {}).get("so_luong"))
	return ra


def banh_le_trong_hop(dinh_muc, ban_theo_hop):
	"""So banh le bi cac hop an di, theo tung ma banh le. THUAN.

	dinh_muc: list dict co ma_hop, ma_banh, so_luong.
	ban_theo_hop: dict {ma_hop: so hop da ban va dang giu}.

	Vi sao can (anh Viet chot 18/08/2026): ban mot hop MOONGARDEN la lay di
	may cai banh 110g ben trong. Truoc day hai thu dem doc lap, nen ban 2000
	hop van thay banh le "con 192" trong khi lo banh do da vao het trong hop.
	"""
	ra = {}
	for m in dinh_muc or []:
		m = m or {}
		hop = str(m.get("ma_hop") or "").strip()
		banh = str(m.get("ma_banh") or "").strip()
		sl = cint(m.get("so_luong"))
		if not hop or not banh or sl <= 0:
			continue
		ra[banh] = ra.get(banh, 0) + cint((ban_theo_hop or {}).get(hop)) * sl
	return ra


def san_luong_theo_ma(cac_dong):
	"""Tong san luong bep lam duoc, cong theo tung ma hang. THUAN.

	cac_dong: list dict co ma_hang, so_luong.

	Tra dict RONG neu chua ai nhap ngay nao - luc do o "San xuat" go tay giu
	nguyen hieu luc, giong het cach o "Tong nha in giao" ung xu voi cac dot.
	"""
	ra = {}
	for x in cac_dong or []:
		ma = str((x or {}).get("ma_hang") or "").strip()
		if not ma:
			continue
		ra[ma] = ra.get(ma, 0) + cint((x or {}).get("so_luong"))
	return ra


def nguon_cung(san_xuat, nha_in_giao):
	"""Tong nguon cung cua mot dong. THUAN.

	Anh Viet chot 21/08/2026: **cong hai nguon**, vi chung khong trung nhau.
	Nha in giao VO HOP, bep lam RUOT BANH. Mot dong hop thi o bep bang 0,
	mot dong banh le thi o nha in bang 0. Cong lai la con so dung cho ca hai.

	Truoc ban nay chi co mot o "San xuat" gom ca hai thu, nen khong nhin ra
	duoc hop dang thieu vi nha in giao thieu hay vi bep chua lam kip.
	"""
	return cint(san_xuat) + cint(nha_in_giao)


def ma_la_hop(dinh_muc):
	"""Tap cac ma hang la HOP, tuc co mat o cot ma_hop cua dinh muc. THUAN."""
	ra = set()
	for m in dinh_muc or []:
		hop = str((m or {}).get("ma_hop") or "").strip()
		if hop:
			ra.add(hop)
	return ra


def tach_ma_loai_tru(chuoi):
	"""Doc o Ma loai tru thanh mot tap ma, viet HOA het. THUAN.

	O do la Small Text, moi dong mot ma, nguoi go tay duoc nen phai chiu duoc
	dong trong, khoang trang thua, dau phay, va chu thuong.
	"""
	ra = set()
	for khuc in str(chuoi or "").replace(",", "\n").split("\n"):
		ma = khuc.strip().upper()
		if ma:
			ra.add(ma)
	return ra


def them_ma_loai_tru(chuoi, ma):
	"""Them mot ma vao o Ma loai tru, tra ve chuoi moi. THUAN.

	Giu nguyen thu tu cac ma da co roi moi noi ma moi vao cuoi, de nguoi doc
	thay duoc cai nao bi loai truoc cai nao sau. Ma da co thi khong them lan
	hai.
	"""
	ma = str(ma or "").strip().upper()
	cu = []
	for khuc in str(chuoi or "").replace(",", "\n").split("\n"):
		x = khuc.strip().upper()
		if x and x not in cu:
			cu.append(x)
	if ma and ma not in cu:
		cu.append(ma)
	return "\n".join(cu)


def ghep_duoc_tu_ruot(dinh_muc, con_cua_banh, khong_tran=None):
	"""Ruot con lai ghep duoc THEM bao nhieu hop nua, theo tung ma hop. THUAN.

	dinh_muc      : list dict co ma_hop, ma_banh, so_luong
	con_cua_banh  : dict {ma_banh: so con ban duoc cua banh le do}
	khong_tran    : tap ma banh mang co "khong dat tran"

	Tra dict {ma_hop: so hop}. Ma hop nao KHONG co rang buoc ruot nao thi
	KHONG co mat trong dict - de ben goi phan biet duoc "ghep duoc 0 hop" voi
	"khong biet, khong rang buoc".

	Vi sao phai bo qua banh mang co khong_tran (bay lon nhat cua phep nay):
	banh 80g trong MOONGARDEN va MOONLAPIS khong co lo rieng, chi lam theo
	hop, nen han muc cua chung bang 0. De chung vao phep lay nho nhat thi moi
	hop deu ra 0 va ca mua bi chan - chan sai chu khong phai chan dung. Co
	khong_tran sinh ra dung de chan chuyen nay, xem con_sau_khi_them.

	Khong tru hai lan: con_cua_banh da tru phan nam trong hop da ban roi
	(cot trong_hop), nen day dung la so banh le CON TU DO.
	"""
	khong_tran = khong_tran or set()
	ra = {}
	for m in dinh_muc or []:
		m = m or {}
		hop = str(m.get("ma_hop") or "").strip()
		banh = str(m.get("ma_banh") or "").strip()
		sl = cint(m.get("so_luong"))
		if not hop or not banh or sl <= 0:
			continue
		if banh in khong_tran:
			continue
		co = cint((con_cua_banh or {}).get(banh))
		duoc = co // sl if co > 0 else 0
		ra[hop] = duoc if hop not in ra else min(ra[hop], duoc)
	return ra


def con_hop_thuc_te(con_cua_hop, ghep):
	"""So hop THAT SU con ban duoc. THUAN.

	Lay so nho hon giua hai rang buoc:
	  - vo hop con bao nhieu (con_cua_hop, tinh tu o Tong nha in giao)
	  - ruot con ghep duoc bao nhieu (ghep, tra ve tu ghep_duoc_tu_ruot)

	ghep la None nghia la hop chua khai dinh muc, khong co rang buoc ruot nao,
	luc do chi con vo hop noi len. Man hinh phai hien chip canh bao cho truong
	hop do, vi im lang o day la ban lo ma khong ai biet.
	"""
	if ghep is None:
		return cint(con_cua_hop)
	return min(cint(con_cua_hop), cint(ghep))


def con_ban_duoc(san_xuat, da_dat, cho_chot, don_khac, trong_hop=0):
	"""Con ban duoc cua mot dong. THUAN.

	Tra ve so co the AM: am nghia la da ban lo, va con so am do chinh la
	thu de man hinh to do va de chot chan nem loi. Ep ve 0 la giau mat mot
	su that dang co.
	"""
	return (
		cint(san_xuat)
		- cint(da_dat)
		- cint(cho_chot)
		- cint(don_khac)
		- cint(trong_hop)
	)


def con_sau_khi_them(dong, dinh_muc, ma_hang, so_them):
	"""Neu them so_them cai ma_hang nua thi con lai bao nhieu. THUAN.

	Day la phep chot chan dung truoc khi cho ghi so mot don (anh Viet chot
	18/08/2026: tuyet doi khong cho ban lo).

	Tra (con_lai, cac_dong_bi_am):
	  con_lai       - so con lai cua CHINH ma do sau khi them
	  cac_dong_bi_am - list (ma, con_lai) cua MOI ma bi am, ke ca banh le bi
	                   hop an di. Ban mot hop co the lam am mot banh le chu
	                   khong am chinh cai hop, va do la cho de bo sot nhat.

	Dong bat co "khong_tran" thi KHONG bao gio vao danh sach am (anh Viet
	chot 18/08/2026). Do la banh chi lam theo hop: banh 80gr trong
	MOONGARDEN va MOONLAPIS khong co lo rieng, tran that nam o so hop. De
	chung mang tran 0 thi ban bat cu hop nao cung bi chan, va day la chan
	sai chu khong phai chan dung.
	"""
	so_them = cint(so_them)
	ban_truoc = {}
	theo_ma = {}
	for d in dong or []:
		d = d or {}
		ma = str(d.get("ma_hang") or "").strip()
		if not ma:
			continue
		theo_ma[ma] = d
		ban_truoc[ma] = (
			cint(d.get("da_dat")) + cint(d.get("cho_chot")) + cint(d.get("don_khac"))
		)
	if ma_hang not in theo_ma:
		# Ma khong nam trong mua nay thi khong bi rang buoc han muc.
		return None, []
	ban_sau = dict(ban_truoc)
	ban_sau[ma_hang] = ban_sau.get(ma_hang, 0) + so_them

	# Phai tinh CA HAI moc, truoc va sau khi them (sua 18/08/2026 sau khi
	# nghiem thu bat duoc). Ban dau chi tinh moc sau roi bao moi dong am, va
	# nhu the la sai nang: HOP MOONGARDEN dang -62 vi chua khai dot nha in,
	# nen ban mot HOP MOONLAPIS cung bi chan kem cau "se lay het HOP
	# MOONGARDEN ben trong hop" - mot cau vo nghia vi MOONGARDEN khong nam
	# trong MOONLAPIS. Mot ma ban lo se chan ca mua.
	#
	# Luat dung: don nay chi bi chan boi nhung dong ma CHINH NO lam xau di.
	# Dong da am san tu truoc va don nay khong dung toi thi khong lien quan.
	trong_truoc = banh_le_trong_hop(dinh_muc, ban_truoc)
	trong_sau = banh_le_trong_hop(dinh_muc, ban_sau)
	am, con_cua_ma = [], None
	for ma, d in theo_ma.items():
		# Nguon cung gop hai o: bep lam va nha in giao (anh Viet chot 21/08/2026).
		sx = nguon_cung(d.get("san_xuat"), d.get("nha_in_giao"))
		dat = d.get("da_dat")
		cho, khac = d.get("cho_chot"), d.get("don_khac")
		con_truoc = con_ban_duoc(sx, dat, cho, khac, trong_truoc.get(ma, 0))
		con_sau = con_ban_duoc(sx, dat, cho, khac, trong_sau.get(ma, 0))
		if ma == ma_hang:
			con_sau -= so_them
			con_cua_ma = con_sau
		if con_sau < 0 and con_sau < con_truoc and not cint(d.get("khong_tran")):
			am.append((ma, con_sau))
	return con_cua_ma, am


# --------------------------------------------- bang CO THE BAN theo tung ngay
#
# Anh Viet 22/08/2026: "Cau hinh cac cot y chang nhu man kiem banh hang ngay
# cua banh o va dong bo api de tinh ra so hop banh MOONLAPIS va MOONGARDEN, va
# cac vi banh le co san xuat du cho ngay do de up sale cho khach. So san xuat
# duoc hom do bao nhieu thi bep nhap vao."
#
# Phep o day CHINH LA phep cua vagabond/kiem_banh.py, tung cot mot:
#
#   Ton dau + Bep lam - Da dat - Phat sinh - Cho chot - Kenh khac = Co the ban
#
# Khac dung mot cho, va cho do la ly do phai co ham rieng chu khong goi thang
# ham ben kia: ben theo ngay, ton dau ngay do NGUOI GO TAY theo tung lo NSX,
# vi banh o lam moi sang va de hong. Ben mua vu khong ai go ton dau, vi banh
# trung thu lam mot lot an ca mua - nen may phai CUON tu ngay dau mua den ngay
# dang xem, ngay hom truoc con lai bao nhieu thi ngay hom sau bat dau tu do.
#
# Cuon chu khong lay tong ca mua tru di: sales can biet NGAY DO con du bao
# nhieu de up sale. Ngay 20/09 dat kin ma 21/09 con trong la hai con so khac
# han nhau, tong ca mua khong noi len duoc dieu do.


def cuon_ton_theo_ngay(cac_ngay, mo_so, them_ngay, cam_ngay, dinh_muc):
	"""Cuon ton qua tung ngay cua mua. THUAN.

	cac_ngay  : list "YYYY-MM-DD" tang dan, tu ngay dau mua den ngay can xem.
	mo_so     : {ma: so co san truoc ngay dau danh sach}
	            banh le -> o "Bep lam truoc khi mo so"
	            hop     -> cac dot nha in da ve TRUOC ngay dau danh sach
	them_ngay : {(ma, ngay): so vao them dung ngay do}
	            banh le -> bep nhap o tab Co the ban
	            hop     -> vo hop nha in giao dung ngay do
	cam_ngay  : {(ma, ngay): {"da_dat", "phat_sinh", "cho_chot", "don_khac"}}
	dinh_muc  : list dict co ma_hop, ma_banh, so_luong

	Tra ve {ngay: {ma: {ton_dau, them, da_dat, phat_sinh, cho_chot, don_khac,
	                    trong_hop, co_the_ban}}}

	Am la duoc phep va la CO Y: am nghia la ngay do da nhan qua tay, va con so
	am chinh la thu can hien mau do. Ep ve 0 la giau mat mot su that dang co.
	"""
	hop = ma_la_hop(dinh_muc)
	ma_tat_ca = set(mo_so or {})
	for k in list(them_ngay or {}) + list(cam_ngay or {}):
		ma_tat_ca.add(k[0])

	ton = {ma: cint((mo_so or {}).get(ma)) for ma in ma_tat_ca}
	ra = {}
	for ng in cac_ngay or []:
		# Hop ban trong NGAY NAY an ruot cua chinh ngay nay. Phai tinh truoc
		# vong lap duoi, vi banh le can biet no bi hop an mat bao nhieu.
		ban_hop = {}
		for m in hop:
			c = (cam_ngay or {}).get((m, ng)) or {}
			ban_hop[m] = (
				cint(c.get("da_dat")) + cint(c.get("phat_sinh"))
				+ cint(c.get("cho_chot")) + cint(c.get("don_khac"))
			)
		trong_hop = banh_le_trong_hop(dinh_muc, ban_hop)

		o_ngay = {}
		for ma in ma_tat_ca:
			c = (cam_ngay or {}).get((ma, ng)) or {}
			them = cint((them_ngay or {}).get((ma, ng)))
			dd, ps = cint(c.get("da_dat")), cint(c.get("phat_sinh"))
			cc, dk = cint(c.get("cho_chot")), cint(c.get("don_khac"))
			th = 0 if ma in hop else cint(trong_hop.get(ma))
			dau = cint(ton.get(ma))
			con = dau + them - dd - ps - cc - dk - th
			o_ngay[ma] = {
				"ton_dau": dau, "them": them, "da_dat": dd, "phat_sinh": ps,
				"cho_chot": cc, "don_khac": dk, "trong_hop": th, "co_the_ban": con,
			}
			ton[ma] = con
		ra[ng] = o_ngay
	return ra


def ghep_theo_ngay(o_ngay, dinh_muc, khong_tran=None):
	"""Them hai cot ghep_duoc va con_thuc_te cho cac dong HOP cua mot ngay. THUAN.

	o_ngay: mot ngay lay ra tu cuon_ton_theo_ngay. Sua tai cho roi tra ve chinh
	no, de ben goi khoi phai gan lai.

	Vi sao hop phai co hai cot: vo hop con 300 ma ruot chi ghep duoc 40 thi so
	ban duoc that la 40. Chi nhin mot cot la ban lo ma khong ai biet - dung cai
	bay ma con_hop_thuc_te sinh ra de chan.
	"""
	hop = ma_la_hop(dinh_muc)
	con_banh = {
		ma: cint(o.get("co_the_ban")) for ma, o in (o_ngay or {}).items() if ma not in hop
	}
	ghep = ghep_duoc_tu_ruot(dinh_muc, con_banh, khong_tran or set())
	for ma, o in (o_ngay or {}).items():
		if ma in hop:
			g = ghep.get(ma)
			o["la_hop"] = 1
			o["ghep_duoc"] = cint(g) if g is not None else 0
			o["con_thuc_te"] = con_hop_thuc_te(o.get("co_the_ban"), g)
			o["ruot_khong_rang_buoc"] = 1 if g is None else 0
		else:
			o["la_hop"] = 0
			o["ghep_duoc"] = 0
			o["con_thuc_te"] = cint(o.get("co_the_ban"))
			o["ruot_khong_rang_buoc"] = 0
	return o_ngay


def day_ngay(tu_ngay, den_ngay, toi_da=SO_NGAY_TOI_DA):
	"""Danh sach ngay lien tuc "YYYY-MM-DD" tu tu_ngay den den_ngay. THUAN.

	Cat bot dau danh sach neu dai qua toi_da: cuon mot mua vai thang la vai
	tram vong lap tren mot dict nho, khong nang, nhung van phai co tran de
	mot o ngay go nham nam 2019 khong lam treo may chu.
	"""
	a, b = getdate(tu_ngay), getdate(den_ngay)
	if b < a:
		return []
	ra = []
	x = a
	while x <= b:
		ra.append(str(x))
		x = x + timedelta(days=1)
	return ra[-toi_da:] if len(ra) > toi_da else ra


# Anh Viet chot 18/08/2026: "1 ngay toi da co the lam duoc 150-200 hop
# MOONGARDEN thoi, em warning thanh do voi nhung ngay gan full".
#
# 150 dung bang 75 phan tram cua 200, nen thay vi dong cung hai con so vao
# ma nguon, moi dong mang mot o "Tran moi ngay". Sang nam doi hop khac,
# doi so trong o la xong, khong phai sua code va deploy lai.
TY_LE_VANG = 0.75


def muc_tran(so, tran):
	"""0 binh thuong, 1 gan day (vang), 2 day hoac qua (do). THUAN.

	tran <= 0 nghia la dong nay khong theo doi tran ngay.
	"""
	tran = cint(tran)
	so = cint(so)
	if tran <= 0 or so <= 0:
		return 0
	if so >= tran:
		return 2
	if so >= tran * TY_LE_VANG:
		return 1
	return 0


_BO_TU = ("HOP", "BANH", "TRUNG", "THU", "NHAN", "NAM", "GRAM", "GR")


def _khong_dau(s):
	import unicodedata

	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	s = s.replace("đ", "d").replace("Đ", "D").upper()
	# Dau phay dinh vao chu bien "XIU," thanh mot tu khong phai chu cai va
	# lam mat luon chu do. Tach dau ra thanh khoang trang truoc.
	return "".join(c if c.isalnum() else " " for c in s)


def nhan_tu_ten(ten, da_dung=None):
	"""Vai chu ngan de hien trong o lich thang. THUAN.

	O lich thang tren dien thoai rong chung 48 diem anh, khong ke duoc
	"Thap Cam Hai San Sot XO" vao do. Nhung "sales nhin o la biet ngay do
	lam gi" moi la thu anh Viet can, nen phai co nhan ngan.

	da_dung: cac nhan da phat cho dong khac trong cung mua, de khong trung.
	"""
	da_dung = set(da_dung or ())
	tu = [t for t in _khong_dau(ten).split() if t.isalpha() and t not in _BO_TU]
	if not tu:
		tu = [t for t in _khong_dau(ten).split() if t.isalpha()] or ["X"]
	goc = "".join(t[0] for t in tu[:3]) if len(tu) >= 2 else tu[0][:3]
	goc = goc[:4] or "X"
	if goc not in da_dung:
		return goc
	# Trung thi noi dan chu tu chinh cai ten, het chu moi danh so.
	nguon = "".join(tu)
	for n in range(len(goc) + 1, min(len(nguon), 6) + 1):
		if nguon[:n] not in da_dung:
			return nguon[:n]
	for i in range(2, 40):
		if goc[:3] + str(i) not in da_dung:
			return goc[:3] + str(i)
	return goc


def _khoang_unix(tu_ngay, den_ngay):
	"""Tu 0h ngay dau den 23h59 ngay cuoi, gio Viet Nam, ra unix giay."""
	from zoneinfo import ZoneInfo

	vn = ZoneInfo("Asia/Ho_Chi_Minh")
	a, b = getdate(tu_ngay), getdate(den_ngay)
	dau = datetime(a.year, a.month, a.day, tzinfo=vn)
	cuoi = datetime(b.year, b.month, b.day, tzinfo=vn) + timedelta(days=1)
	return int(dau.timestamp()), int(cuoi.timestamp()) - 1


def _keo_don(c, k, dau, cuoi):
	"""Keo het don giao trong khoang mua, lat qua tung trang.

	requests nap TRONG ham chu khong o dau tep, va do la co y (QT-5): may
	chay CI cua GitHub tay khong, khong co requests. Nap o dau tep thi moi ca
	kiem thu nao cham vao mo dun nay deu no ngay tu luc import, du ca do khong
	he goi mang. Ngay 20/08/2026 CI do ba lan vi dung chuyen nay.
	"""
	import requests

	ra = []
	for trang in range(1, MAX_TRANG + 1):
		r = requests.get(
			"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
			params={
				"api_key": k,
				"updateStatus": "estimate_delivery_date",
				"startDateTime": dau,
				"endDateTime": cuoi,
				"page_size": 100,
				"page_number": trang,
			},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
		ds = (r.json() or {}).get("data") or []
		ra.extend(ds)
		if len(ds) < 100:
			break
	return ra


def _ngay_giao(o):
	"""Ngay giao cua mot don Pancake, dang YYYY-MM-DD. Rong neu khong doc duoc."""
	for o_ten in ("estimate_delivery_date", "time_delivery_at", "inserted_at"):
		v = o.get(o_ten)
		if not v:
			continue
		try:
			return str(getdate(str(v)[:10]))
		except Exception:
			continue
	return ""


def _ngay_tao(o):
	"""Ngay TAO don theo gio Viet Nam, dang YYYY-MM-DD. Rong neu khong doc duoc.

	Dung de tach "Phat sinh" khoi "Da dat", y het bang kiem banh theo ngay:
	don giao hom nay ma cung tao trong hom nay la PHAT SINH, tao tu hom truoc
	la DA DAT.

	Vi sao phai doi mui gio chu khong cat muoi ky tu dau: Pancake tra
	inserted_at dang ISO gio UTC, nen mot don tao luc 0h30 dem gio Viet Nam se
	mang ngay UTC cua hom truoc. Cat thang la don phat sinh bi xep nham thanh
	da dat, va bang bao sai dung vao dip cao diem khi sales chot don ban dem.
	"""
	from zoneinfo import ZoneInfo

	v = str(o.get("inserted_at") or "").strip()
	if not v:
		return ""
	try:
		t = datetime.fromisoformat(v.replace("Z", "+00:00"))
		if t.tzinfo is None:
			t = t.replace(tzinfo=ZoneInfo("UTC"))
		return str(t.astimezone(ZoneInfo("Asia/Ho_Chi_Minh")).date())
	except Exception:
		pass
	try:
		return str(getdate(v[:10]))
	except Exception:
		return ""


def _dem(dons):
	"""Gop don thanh bon bang. THUAN tren du lieu Pancake, khong doc CSDL.

	Tra ve:
	  dem_chot  {ma: so}          don da chot
	  dem_cho   {ma: so}          don con trang thai Moi
	  theo_ngay {(ma, ngay): {"chot", "cho", "phat_sinh", "khach", "khach_ps"}}
	  ten, hinh {ma: ...}

	O "chot" van la TONG don da chot cua ngay do, khong tru phan phat sinh -
	bang Lich thang va phep muc_tran dung con so nay tu truoc den nay. O
	"phat_sinh" la phan cua "chot" duoc tao dung trong ngay giao, nen ben goi
	lay "Da dat" bang chot tru phat_sinh. Lam vay de them cot moi ma khong doi
	nghia cua cot cu, tranh phai sua hai noi.
	"""
	dem_chot, dem_cho, theo_ngay, ten, hinh = {}, {}, {}, {}, {}
	for o in dons:
		if o.get("status") in BO_QUA_TT:
			continue
		cho = o.get("status") == 0
		ngay = _ngay_giao(o)
		ps = (not cho) and bool(ngay) and _ngay_tao(o) == ngay
		ten_khach = (o.get("bill_full_name") or "").strip()
		for it in o.get("items") or []:
			vi = it.get("variation_info") or {}
			ma = str(vi.get("display_id") or it.get("variation_id") or "").strip()
			if not ma.upper().startswith(TIEN_TO_MA):
				continue
			sl = int(it.get("quantity") or 0)
			if cho:
				dem_cho[ma] = dem_cho.get(ma, 0) + sl
			else:
				dem_chot[ma] = dem_chot.get(ma, 0) + sl
			if vi.get("name"):
				ten[ma] = vi["name"]
			anh = vi.get("images") or []
			if anh and anh[0]:
				hinh[ma] = anh[0]
			if ngay:
				o_l = theo_ngay.setdefault(
					(ma, ngay),
					{"chot": 0, "cho": 0, "phat_sinh": 0, "khach": [], "khach_ps": []},
				)
				o_l["cho" if cho else "chot"] += sl
				if ps:
					o_l["phat_sinh"] += sl
					if ten_khach and ten_khach not in o_l["khach_ps"]:
						o_l["khach_ps"].append(ten_khach)
				if ten_khach and ten_khach not in o_l["khach"]:
					o_l["khach"].append(ten_khach)
	return dem_chot, dem_cho, theo_ngay, ten, hinh


def _dem_kenh_khac(tu_ngay, den_ngay):
	"""Banh mua vu ban qua kenh khong di qua Pancake, dem tu hoa don ban ra.

	Giong het cach bang theo ngay dang lam, va co y giong den tung dieu kien:

	  docstatus < 2  - bill con NHAP cung tru. Sales bam don giu cho khach
	                   thi cai hop do khong con de ban cho nguoi khac, du
	                   ke toan chua ghi so.
	  vgb_huy = 0    - bill da huy khong con la hang ban ra, khong duoc tru,
	                   khong thi sales dem thieu hang trong kho.
	  nguon khac Pancake - don Pancake da dem tu API o tren roi, dem lai o
	                   day la tru hai lan.
	"""
	ra = {}
	for (ma, _ng), o in _dem_kenh_khac_ngay(tu_ngay, den_ngay).items():
		ra[ma] = ra.get(ma, 0) + cint(o.get("so"))
	return ra


def _dem_kenh_khac_ngay(tu_ngay, den_ngay):
	"""Nhu tren nhung TACH THEO TUNG NGAY, kem nhan de sales biet so tu don nao.

	Tra ve {(ma, "YYYY-MM-DD"): {"so": n, "mo_ta": ["GrabFood #GF-441 (2)", ..]}}

	Mot nguon duy nhat cho ca hai bang: tong ca mua o tren CONG tu day ra chu
	khong hoi co so du lieu lan hai. Hai duong dem doc lap la hai luat, va hai
	luat se lech nhau vao mot ngay khong ai doan truoc.
	"""
	try:
		r = frappe.db.sql(
			"""select sii.item_code as ma, si.posting_date as ngay,
			       sum(sii.qty) as sl, si.custom_nguon as nguon,
			       si.custom_pancake_display_id as ma_don
			from `tabSales Invoice Item` sii
			join `tabSales Invoice` si on si.name = sii.parent
			where si.docstatus < 2
			  and ifnull(si.vgb_huy, 0) = 0
			  and si.posting_date between %s and %s
			  and lower(ifnull(si.custom_nguon, '')) not in ('', 'pancake')
			group by sii.item_code, si.posting_date, si.name,
			         si.custom_nguon, si.custom_pancake_display_id""",
			(getdate(tu_ngay), getdate(den_ngay)),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "mua_vu: dem kenh khac theo ngay loi")
		return {}
	ra = {}
	for d in r:
		ma = str(d.get("ma") or "").strip()
		if not ma.upper().startswith(TIEN_TO_MA):
			continue
		sl = cint(d.get("sl"))
		if sl <= 0:
			continue
		khoa = (ma, str(getdate(d.get("ngay"))))
		o = ra.setdefault(khoa, {"so": 0, "mo_ta": []})
		o["so"] += sl
		nhan = str(d.get("nguon") or "Kenh khac")
		if d.get("ma_don"):
			nhan += " #" + str(d["ma_don"])
		if sl > 1:
			nhan += " (%d)" % sl
		if nhan not in o["mo_ta"]:
			o["mo_ta"].append(nhan)
	return ra


# ------------------------------------------------------------------ mua vu


@frappe.whitelist()
def danh_sach():
	"""Cac mua vu da lap, mua dang chay len dau."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ds = frappe.get_all(
		DT,
		fields=["name", "ten_mua", "tu_ngay", "den_ngay", "tinh_trang", "dong_bo_luc"],
		order_by="tu_ngay desc",
		limit_page_length=50,
	)
	hom_nay = getdate()
	for d in ds:
		d["dang_chay"] = 1 if (d["tu_ngay"] <= hom_nay <= d["den_ngay"]) else 0
		d["so_sp"] = frappe.db.count("Vagabond Mua Vu Dong", {"parent": d["name"]})
	return {"ds": ds}


@frappe.whitelist()
def tao_mua(ten_mua=None, tu_ngay=None, den_ngay=None):
	"""Lap mot mua vu moi."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ten = (ten_mua or "").strip()
	if not ten:
		frappe.throw("Đặt tên cho mùa vụ giúp em, ví dụ \"Trung thu 2026\".")
	if frappe.db.exists(DT, ten):
		frappe.throw(
			"Đã có mùa vụ tên \"%s\" rồi. Mở mùa đó ra dùng tiếp, hoặc đặt tên khác." % ten
		)
	a, b = getdate(tu_ngay), getdate(den_ngay)
	if b < a:
		frappe.throw("Ngày kết thúc đang trước ngày bắt đầu. Chọn lại hai mốc ngày giúp em.")
	if (b - a).days > SO_NGAY_TOI_DA:
		frappe.throw(
			"Mùa vụ dài %d ngày, quá %d ngày nên nhiều khả năng gõ nhầm năm. Chọn lại "
			"ngày kết thúc giúp em." % ((b - a).days, SO_NGAY_TOI_DA)
		)
	doc = frappe.get_doc(
		{"doctype": DT, "ten_mua": ten, "tu_ngay": a, "den_ngay": b, "tinh_trang": "Dang ban"}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "mua": doc.name}


KHOA_KEO = "vagabond_mua_vu_dang_keo"


def _gianh_khoa(mua, giay=180):
	"""Chi mot luot keo Pancake duoc chay tai mot thoi diem cho mot mua.

	Vi sao can (anh Viet bao 18/08/2026: "bam Dong bo Pancake thi bi dung
	im"): man cu, scheduler va nut bam co the cung goi mot luc. Hai luot
	cung save mot tai lieu thi luot sau nam cho khoa dong CSDL cua luot
	truoc, va nguoi dung ngoi nhin dong ho cat. Gap nhau thi luot sau tra
	so hien co luon, vi no khong them duoc thong tin gi ma van bat cho.
	"""
	try:
		c = frappe.cache()
		k = "%s:%s" % (KHOA_KEO, mua)
		if c.get_value(k):
			return False
		c.set_value(k, "1", expires_in_sec=giay)
		return True
	except Exception:
		# Cache hong thi cu cho chay, khong lay cai phanh de chan ca viec.
		return True


def _tha_khoa(mua):
	try:
		frappe.cache().delete_value("%s:%s" % (KHOA_KEO, mua))
	except Exception:
		pass


@frappe.whitelist()
def xin_dong_bo(mua=None):
	"""Man hinh XIN may chu keo Pancake, va tra ve NGAY, khong doi.

	Anh Viet bao 18/08/2026: bam Dong bo Pancake thi man dung im mai. Doc
	lai ban ghi thi thay may chu chay xong ca ba lan anh bam, ma man van
	nam o khung cho. Nguyen nhan goc: man cu DOI ca luot keo Pancake moi ve
	duoc, ma luot do di ra Internet - mot lan mang chap la trinh duyet treo
	vinh vien vi tu no khong bo cuoc bao gio.

	Nay man ve NGAY bang so trong CSDL, con viec keo giao cho hau truong.
	Man khong con duong nao de treo nua.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not mua or not frappe.db.exists(DT, mua):
		return {"ok": 0}
	# Nhieu may cung mo man thi cung xin moi 30 giay, va man nao cung xin
	# cho cung mot mua. Chan o day de hang doi khong phinh ra vo ich.
	try:
		c = frappe.cache()
		kx = "vagabond_mua_vu_da_xin:%s" % mua
		if c.get_value(kx):
			return {"ok": 1, "da_xin": 1}
		c.set_value(kx, "1", expires_in_sec=15)
	except Exception:
		pass
	frappe.enqueue(
		"vagabond.mua_vu.dong_bo_mot_mua",
		queue="short",
		timeout=300,
		mua=mua,
	)
	return {"ok": 1}


def dong_bo_mot_mua(mua=None):
	"""Cho hang doi nen goi. Nuot loi de khong lam ban nhat ky moi phut."""
	try:
		_keo_ve(mua)
	except Exception:
		frappe.log_error(
			title="Vagabond: dong bo mua vu %s loi" % mua, message=frappe.get_traceback()
		)


def dong_bo_tu_dong():
	"""Cho scheduler goi moi phut: quet moi mua DANG BAN.

	Anh Viet 18/08/2026: "cai dum anh ham de dong bo tu dong tu Pancake ve
	de kip thoi bat don moi (va nhung don bi chinh sua, them san pham...)".
	Keo lai ca mua moi lan chu khong keo them, nen don sua o Pancake cung
	ve dung so - khong co duong nao lech.
	"""
	try:
		for ma in mua_dang_chay():
			dong_bo_mot_mua(ma)
	except Exception:
		frappe.log_error(
			title="Vagabond: nhip dong bo mua vu loi", message=frappe.get_traceback()
		)


@frappe.whitelist()
def dong_bo(mua=None):
	"""Dem lai ca mua tu Pancake: theo san pham va theo tung ngay giao."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return _keo_ve(mua)


def _keo_ve(mua=None):
	"""Ruot cua dong bo. KHONG kiem quyen - nguoi goi tu kiem."""
	doc = frappe.get_doc(DT, mua)

	# Man hinh cua nhieu nguoi tu goi lien tuc. Vua dong bo trong vong
	# GIAN_CACH_DONG_BO giay thi tra bang luon - keo ca mua nang hon keo
	# mot ngay nhieu, khong nen goi Pancake lien tuc.
	if doc.dong_bo_luc and (now_datetime() - doc.dong_bo_luc).total_seconds() < GIAN_CACH_DONG_BO:
		return bang(mua)

	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa điền khoá Pancake trong Cài đặt. Báo em để kiểm tra lại.")

	if not _gianh_khoa(mua):
		# Da co luot keo khac dang chay. Doi no thi cho lau ma khong duoc
		# them gi, nen tra so hien co luon.
		return bang(mua)
	try:
		return _keo_that(doc, mua, c, k)
	finally:
		_tha_khoa(mua)


def _ten_tu_item(ma):
	"""Ten san pham lay ben danh muc Item. Rong thi tra chuoi rong.

	Dung cho dong may TU nhat tu hoa don ban ra: nhung dong do khong di qua
	Pancake nen khong co ten kem theo, va bang se hien tro moi ma hang.
	"""
	try:
		return frappe.db.get_value("Item", ma, "item_name") or ""
	except Exception:
		return ""


def _keo_that(doc, mua, c, k):
	"""Phan that su di ra Pancake va ghi lai. Da nam trong khoa."""
	dau, cuoi = _khoang_unix(doc.tu_ngay, doc.den_ngay)
	dons = _keo_don(c, k, dau, cuoi)
	dem_chot, dem_cho, theo_ngay, ten, hinh = _dem(dons)
	# Kenh khac tach theo ngay, roi CONG len thanh tong ca mua. Mot nguon duy
	# nhat cho ca bang San pham lan bang Co the ban theo ngay.
	khac_ngay = _dem_kenh_khac_ngay(doc.tu_ngay, doc.den_ngay)
	khac = {}
	for (ma_k, _ng_k), o_k in khac_ngay.items():
		khac[ma_k] = khac.get(ma_k, 0) + cint(o_k.get("so"))

	# Giu nguyen dong san pham nguoi da them va SO LUONG SAN XUAT ho da go.
	# Day la o duy nhat nguoi go, dong bo ma xoa mat no la xoa cong viec
	# cua ho.
	# Ma bi nguoi dung bam X gat ra khoi mua. Khong co danh sach nay thi lan
	# dong bo sau lai keo chinh cai ma vua gat ve, va nguoi dung bam X mai
	# khong xong (anh Viet 22/08/2026 voi Banh Ba Trang trong mua Trung thu).
	loai_tru = tach_ma_loai_tru(doc.get("ma_loai_tru"))

	co = {d.ma_hang: d for d in doc.dong}
	for ma in set(list(dem_chot) + list(dem_cho) + list(khac)):
		if ma not in co:
			# CHI hang mua vu moi duoc tu dua vao. Banh thuong ban trong
			# cung khoang ngay thi khong lien quan den han muc mua nay.
			if not ma.upper().startswith(TU_THEM):
				continue
			if ma.upper() in loai_tru:
				continue
			d = doc.append(
				"dong",
				{"ma_hang": ma, "ten_banh": ten.get(ma) or _ten_tu_item(ma), "san_xuat": 0},
			)
			co[ma] = d
		elif not co[ma].ten_banh:
			# Dong may tu nhat tu hoa don ban ra thi khong di qua Pancake nen
			# khong co ten, bang hien tro moi ma hang. Hoi Item de bu vao.
			co[ma].ten_banh = ten.get(ma) or _ten_tu_item(ma)

	for ma, d in co.items():
		d.da_dat = dem_chot.get(ma, 0)
		d.cho_chot = dem_cho.get(ma, 0)
		d.don_khac = khac.get(ma, 0)
		if hinh.get(ma) and hinh[ma] != d.hinh:
			d.hinh = hinh[ma]
		kh = []
		for (m, _ng), o_l in theo_ngay.items():
			if m == ma and o_l["cho"]:
				kh.extend(o_l["khach"])
		d.ten_khach_cho = ", ".join(sorted(set(kh)))[:1000]

	# Dung lai bang lich tu dau moi lan dong bo: don doi ngay giao la
	# chuyen thuong, giu dong cu lai thi bang lich ke ra mot ngay khong con
	# don nao.
	# Don kenh khac cung phai co dong lich cua rieng no: mot ma ban tai quay
	# dung mot ngay khong co don Pancake nao thi ngay do van phai hien tren
	# bang Co the ban, khong thi so ban duoc cua ngay do bao thua.
	for (ma_k, ng_k) in khac_ngay:
		theo_ngay.setdefault(
			(ma_k, ng_k),
			{"chot": 0, "cho": 0, "phat_sinh": 0, "khach": [], "khach_ps": []},
		)

	doc.set("lich", [])
	for (ma, ngay), o_l in sorted(theo_ngay.items(), key=lambda x: (x[0][1], x[0][0])):
		o_k = khac_ngay.get((ma, ngay)) or {}
		if not (o_l["chot"] or o_l["cho"] or cint(o_k.get("so"))):
			continue
		# Lich chi ke san pham CO trong bang. Khong loc thi lich mua trung
		# thu ke ca don banh sinh nhat cua ba thang.
		if ma not in co:
			continue
		doc.append(
			"lich",
			{
				"ngay": ngay,
				"ma_hang": ma,
				# "so_luong" van la TONG don da chot cua ngay, giu nguyen nghia
				# cu vi bang Lich thang va phep muc_tran dang dung no. Phan tao
				# trong ngay giao nam rieng o "phat_sinh", nen Da dat cua bang
				# theo ngay = so_luong tru phat_sinh.
				"so_luong": o_l["chot"],
				"phat_sinh": o_l.get("phat_sinh") or 0,
				"ten_khach_ps": ", ".join(o_l.get("khach_ps") or [])[:500],
				"cho_chot": o_l["cho"],
				"ten_khach": ", ".join(o_l["khach"])[:500],
				"don_khac": cint(o_k.get("so")),
				"ten_khach_khac": ", ".join(o_k.get("mo_ta") or [])[:500],
			},
		)

	doc.dong_bo_luc = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def bang(mua=None):
	"""Du lieu cho man hinh dien thoai."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, mua):
		return {"co_so": 0}
	doc = frappe.get_doc(DT, mua)

	# Bang lich: moi ngay mot dong, cot la san pham. Dung o may chu chu
	# khong o man hinh, de man chi viec ve.
	ngay_co, theo_ngay = [], {}
	for l in doc.lich:
		ng = str(l.ngay)
		if ng not in theo_ngay:
			theo_ngay[ng] = {}
			ngay_co.append(ng)
		theo_ngay[ng][l.ma_hang] = {
			"chot": l.so_luong or 0,
			"cho": l.cho_chot or 0,
			"khach": l.ten_khach or "",
		}

	# Hinh: uu tien anh Pancake keo ve, thieu thi lay anh trong danh muc Mon.
	# Uyen tao Mon truoc roi moi them anh, nen nhieu dong keo ve dung luc
	# chua co anh nao va se mai mai trong neu khong co duong lui nay.
	thieu_anh = [d.ma_hang for d in doc.dong if not str(d.hinh or "").strip()]
	anh_mon = {}
	if thieu_anh:
		for r in frappe.get_all(
			"Item",
			filters={"name": ["in", thieu_anh]},
			fields=["name", "image"],
			limit_page_length=0,
		):
			if r.get("image"):
				anh_mon[r["name"]] = r["image"]

	# Muc canh bao cua tung ngay TINH O DAY chu khong o man hinh (QT-19).
	# Neu man tu tinh thi hai noi cung giu mot luat va se lech nhau vao mot
	# ngay khong ai doan truoc - dung cai bay da lam hong ba viec 16/08.
	tran = {d.ma_hang: cint(d.tran_ngay) for d in doc.dong if cint(d.tran_ngay) > 0}
	muc_ngay, tai_ngay = {}, {}
	for ng, o in theo_ngay.items():
		m, tai = 0, {}
		for ma, t in tran.items():
			so = cint((o.get(ma) or {}).get("chot")) + cint((o.get(ma) or {}).get("cho"))
			if so:
				tai[ma] = so
			m = max(m, muc_tran(so, t))
		muc_ngay[ng] = m
		if tai:
			tai_ngay[ng] = tai

	# Ma nao la hop, va hop nao da khai dinh muc. Tinh o may chu chu khong o
	# man hinh (QT-19): man tu suy la hai noi cung giu mot luat.
	_la_hop = ma_la_hop([m.as_dict() for m in doc.get("dinh_muc") or []])

	# San luong bep theo ngay, gom lai cho man hinh ve tab moi.
	sl_theo_ngay = {}
	for x in doc.get("san_luong") or []:
		ng = str(x.ngay)
		sl_theo_ngay.setdefault(ng, []).append(
			{
				"ma_hang": x.ma_hang,
				"ten_banh": x.ten_banh or "",
				"so_luong": cint(x.so_luong),
				"nguoi_nhap": x.nguoi_nhap or "",
				"ghi_chu": x.ghi_chu or "",
			}
		)

	return {
		"co_so": 1,
		"mua": doc.name,
		"san_luong": [
			{"ngay": ng, "dong": sl_theo_ngay[ng]}
			for ng in sorted(sl_theo_ngay, reverse=True)
		],
		"ten_mua": doc.ten_mua,
		"ma_loai_tru": sorted(tach_ma_loai_tru(doc.get("ma_loai_tru"))),
		"tu_ngay": str(doc.tu_ngay),
		"den_ngay": str(doc.den_ngay),
		"tinh_trang": doc.tinh_trang,
		"dong_bo_luc": str(doc.dong_bo_luc or ""),
		"dong": [
			{
				"ma_hang": d.ma_hang,
				"ten_banh": d.ten_banh or "",
				"hinh": d.hinh or anh_mon.get(d.ma_hang, ""),
				"nhan_ngan": d.nhan_ngan or "",
				"khong_tran": cint(d.khong_tran),
				"tran_ngay": cint(d.tran_ngay),
				"san_xuat": d.san_xuat or 0,
				"nha_in_giao": d.nha_in_giao or 0,
				"da_dat": d.da_dat or 0,
				"cho_chot": d.cho_chot or 0,
				"don_khac": d.don_khac or 0,
				"trong_hop": d.trong_hop or 0,
				"co_the_ban": d.co_the_ban or 0,
				"ghep_duoc": d.ghep_duoc or 0,
				"con_thuc_te": d.con_thuc_te or 0,
				"la_hop": 1 if d.ma_hang in _la_hop else 0,
				"ruot_khong_rang_buoc": cint(d.ruot_khong_rang_buoc),
				"ten_khach_cho": d.ten_khach_cho or "",
				"ghi_chu": d.ghi_chu or "",
			}
			for d in doc.dong
		],
		"lich": {
			"ngay": sorted(ngay_co),
			"o": theo_ngay,
			"muc": muc_ngay,
			"tai": tai_ngay,
			"tran": tran,
			"ty_le_vang": TY_LE_VANG,
		},
		"dot": [
			{
				"ma_hang": x.ma_hang,
				"ten_banh": x.ten_banh or "",
				"so_luong": x.so_luong or 0,
				"ngay_du_kien": str(x.ngay_du_kien or ""),
				"da_ve": cint(x.da_ve),
				"ngay_ve_that": str(x.ngay_ve_that or ""),
				"ghi_chu": x.ghi_chu or "",
			}
			for x in doc.get("dot") or []
		],
		"dinh_muc": [
			{
				"ma_hop": m.ma_hop,
				"ten_hop": m.ten_hop or "",
				"ma_banh": m.ma_banh,
				"ten_banh": m.ten_banh or "",
				"so_luong": m.so_luong or 0,
			}
			for m in doc.get("dinh_muc") or []
		],
	}


# --------------------------------------------- man CO THE BAN theo tung ngay


# Sales mo man ra la thay hom nay va mot tuan toi. Mot tuan chu khong ba ngay
# nhu ben banh o: banh trung thu khach dat truoc ca tuan, va cai sales can
# nhat la nhin thay ngay nao con trong de goi khach doi ngay giao sang do.
SO_NGAY_CHIP = 7


def _mo_so_va_them(doc, cac_ngay):
	"""Do du lieu cua mot mua vu thanh hai bang dau vao cho cuon_ton_theo_ngay.

	Tra ve (mo_so, them_ngay). Cham CSDL nen KHONG thuan, phep tinh that nam
	ben cuon_ton_theo_ngay - mot cho tinh, mot cho kiem (QT-19).
	"""
	dau = cac_ngay[0] if cac_ngay else str(getdate(doc.tu_ngay))
	trong_khoang = set(cac_ngay or [])

	mo_so, them_ngay = {}, {}

	# Banh le: o go tay la ton mo so, cac dong bep nhap la vao them tung ngay.
	# Ma NAO da khai dot nha in. Ma khong co dot nao thi o "Tong nha in giao"
	# go tay GIU NGUYEN HIEU LUC, y het luat cua han_muc_tu_dot ben bang ca mua.
	#
	# Thieu doan nay thi cac dong HOP hien 0 tren bang theo ngay trong khi bang
	# San pham bao 1600, vi mua Trung thu 2026 khong khai dot nao ca, so vo hop
	# la nguoi go thang vao o. Da gap that ngay 22/08/2026.
	co_dot = {
		str((x.ma_hang or "")).strip()
		for x in (doc.get("dot") or [])
		if str((x.ma_hang or "")).strip()
	}

	# Khai HET ma cua mua, ke ca ma dang bang 0. Bo ma 0 di thi san pham do
	# bien mat khoi bang, va sales tuong mua khong co no chu khong phai no
	# dang het - hai chuyen khac han nhau khi dang tu van khach.
	for d in doc.dong:
		mo_so[d.ma_hang] = cint(d.get("sx_dau_mua"))
		if d.ma_hang not in co_dot:
			mo_so[d.ma_hang] += cint(d.get("nha_in_giao"))
	for x in doc.get("san_luong") or []:
		ma = str(x.ma_hang or "").strip()
		if not ma:
			continue
		ng = str(getdate(x.ngay))
		if ng < dau:
			mo_so[ma] = cint(mo_so.get(ma)) + cint(x.so_luong)
		elif ng in trong_khoang:
			them_ngay[(ma, ng)] = cint(them_ngay.get((ma, ng))) + cint(x.so_luong)
		# Ngay sau ngay dang xem thi bo qua: hang chua lam thi chua ban duoc.

	# Hop: vo hop nha in giao. CHI dot DA VE moi tinh, y het han_muc_tu_dot -
	# mot dot hen 25/09 ma hom nay 20/09 thi so hop do chua co that.
	for x in doc.get("dot") or []:
		if not cint(x.da_ve):
			continue
		ma = str(x.ma_hang or "").strip()
		if not ma:
			continue
		ng = str(getdate(x.ngay_ve_that)) if x.ngay_ve_that else ""
		if not ng or ng < dau:
			mo_so[ma] = cint(mo_so.get(ma)) + cint(x.so_luong)
		elif ng in trong_khoang:
			them_ngay[(ma, ng)] = cint(them_ngay.get((ma, ng))) + cint(x.so_luong)

	return mo_so, them_ngay


def _cam_tu_lich(doc, trong_khoang):
	"""Doc bang lich thanh {(ma, ngay): {da_dat, phat_sinh, cho_chot, don_khac}}.

	Dong lich do dong_bo ghi ra, nen ham nay khong goi Pancake: man hinh mo ra
	la co so ngay, khong phai doi mot luot keo vai chuc giay.
	"""
	ra = {}
	for l in doc.get("lich") or []:
		ma = str(l.ma_hang or "").strip()
		ng = str(getdate(l.ngay))
		if not ma or ng not in trong_khoang:
			continue
		ps = cint(l.get("phat_sinh"))
		o = ra.setdefault(
			(ma, ng),
			{"da_dat": 0, "phat_sinh": 0, "cho_chot": 0, "don_khac": 0,
			 "khach": "", "khach_ps": "", "khach_khac": ""},
		)
		# "so_luong" la TONG don da chot cua ngay do, phat_sinh la phan nam
		# trong tong ay. Tru ra moi la Da dat. Kep xuong 0 phong dong lich cu
		# ghi truoc ban nay chua co cot phat_sinh.
		o["da_dat"] += max(0, cint(l.so_luong) - ps)
		o["phat_sinh"] += ps
		o["cho_chot"] += cint(l.cho_chot)
		o["don_khac"] += cint(l.get("don_khac"))
		o["khach"] = l.ten_khach or o["khach"]
		o["khach_ps"] = l.get("ten_khach_ps") or o["khach_ps"]
		o["khach_khac"] = l.get("ten_khach_khac") or o["khach_khac"]
	return ra


@frappe.whitelist()
def bang_ngay(mua=None, ngay=None):
	"""Bang CO THE BAN cua dung mot ngay, cot y het man kiem banh hang ngay.

	Tra ve moi dong day du cac cot: ton dau ngay, bep lam trong ngay, da dat,
	phat sinh, cho chot, kenh khac, va CO THE BAN. Dong HOP co them hai cot
	ruot ghep duoc va con ban duoc that.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, mua):
		return {"co_so": 0}
	doc = frappe.get_doc(DT, mua)

	ng = getdate(ngay) if ngay else getdate()
	# Ngay ngoai khoang mua thi kep vao trong: sales bam nham mot ngay thang
	# sau khong duoc phep tra ve bang rong khong loi giai thich.
	if ng < getdate(doc.tu_ngay):
		ng = getdate(doc.tu_ngay)
	if ng > getdate(doc.den_ngay):
		ng = getdate(doc.den_ngay)

	cac_ngay = day_ngay(doc.tu_ngay, ng)
	trong_khoang = set(cac_ngay)
	mo_so, them_ngay = _mo_so_va_them(doc, cac_ngay)
	cam = _cam_tu_lich(doc, trong_khoang)

	dm = [m.as_dict() for m in doc.get("dinh_muc") or []]
	khong_tran = {d.ma_hang for d in doc.dong if cint(d.khong_tran)}
	cuon = cuon_ton_theo_ngay(cac_ngay, mo_so, them_ngay, cam, dm)
	o_ngay = ghep_theo_ngay(cuon.get(str(ng)) or {}, dm, khong_tran)

	# Anh va ten lay tu bang san pham, de man nay khong phai hoi them lan nao.
	thong_tin = {
		d.ma_hang: {
			"ten_banh": d.ten_banh or "",
			"hinh": d.hinh or "",
			"nhan_ngan": d.nhan_ngan or "",
			"khong_tran": cint(d.khong_tran),
		}
		for d in doc.dong
	}
	thieu_anh = [ma for ma, t in thong_tin.items() if not str(t["hinh"]).strip()]
	if thieu_anh:
		for r in frappe.get_all(
			"Item",
			filters={"name": ["in", thieu_anh]},
			fields=["name", "image"],
			limit_page_length=0,
		):
			if r.get("image"):
				thong_tin[r["name"]]["hinh"] = r["image"]

	dong = []
	for ma, o in o_ngay.items():
		# Ma bi go khoi mua roi thi khong con la san pham cua mua nay.
		if ma not in thong_tin:
			continue
		c = cam.get((ma, str(ng))) or {}
		t = thong_tin[ma]
		dong.append(
			{
				"ma_hang": ma,
				"ten_banh": t["ten_banh"] or ma,
				"hinh": t["hinh"],
				"nhan_ngan": t["nhan_ngan"],
				"khong_tran": t["khong_tran"],
				"ton_dau": o["ton_dau"],
				"bep_lam": o["them"],
				"da_dat": o["da_dat"],
				"phat_sinh": o["phat_sinh"],
				"cho_chot": o["cho_chot"],
				"don_khac": o["don_khac"],
				"trong_hop": o["trong_hop"],
				"co_the_ban": o["co_the_ban"],
				"la_hop": o["la_hop"],
				"ghep_duoc": o["ghep_duoc"],
				"con_thuc_te": o["con_thuc_te"],
				"ruot_khong_rang_buoc": o["ruot_khong_rang_buoc"],
				"ten_khach_ps": c.get("khach_ps") or "",
				"ten_khach_cho": c.get("khach") or "",
				"ten_khach_khac": c.get("khach_khac") or "",
			}
		)
	# Hop len truoc, roi den banh le, trong moi nhom xep theo ten cho de doc.
	dong.sort(key=lambda x: (0 if x["la_hop"] else 1, x["ten_banh"]))

	return {
		"co_so": 1,
		"mua": doc.name,
		"ten_mua": doc.ten_mua,
		"ngay": str(ng),
		"tu_ngay": str(doc.tu_ngay),
		"den_ngay": str(doc.den_ngay),
		"hom_nay": str(getdate()),
		"so_ngay_chip": SO_NGAY_CHIP,
		"dong_bo_luc": str(doc.dong_bo_luc or ""),
		"dong": dong,
	}


@frappe.whitelist()
def dat_san_luong(mua=None, ngay=None, ma_hang=None, so_luong=0):
	"""Bep go thang so lam duoc cua mot vi trong mot ngay. DAT LAI, khong cong.

	Khac them_san_luong o chinh cho do: them_san_luong cong don vao dong da co,
	dung cho nut "Nhap san luong" khi bep lam hai me sang chieu. Ham nay dung
	cho o so tren bang Co the ban, noi nguoi go dang nhin thay con so cu va go
	de LAY con so do - cong don o day la con so tu nhan doi truoc mat ho.

	So 0 thi xoa dong, de bang khong day nhung dong 0 vo nghia.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = _doc_mua(mua)
	ma = str(ma_hang or "").strip()
	if not ma:
		frappe.throw("Chưa chọn mã hàng.")
	if not any(d.ma_hang == ma for d in doc.dong):
		frappe.throw("Không thấy mã %s trong mùa này. Bấm Đồng bộ rồi thử lại." % ma)
	ng = getdate(ngay) if ngay else getdate()
	so = max(0, cint(so_luong))

	con, thay = [], False
	for x in doc.get("san_luong") or []:
		if x.ma_hang == ma and getdate(x.ngay) == ng:
			thay = True
			if so <= 0:
				continue
			con.append(
				{"ngay": ng, "ma_hang": ma, "ten_banh": x.ten_banh, "so_luong": so,
				 "nguoi_nhap": frappe.session.user, "ghi_chu": x.ghi_chu}
			)
		else:
			con.append(
				{"ngay": x.ngay, "ma_hang": x.ma_hang, "ten_banh": x.ten_banh,
				 "so_luong": x.so_luong, "nguoi_nhap": x.nguoi_nhap, "ghi_chu": x.ghi_chu}
			)
	if not thay and so > 0:
		ten = ""
		for d in doc.dong:
			if d.ma_hang == ma:
				ten = d.ten_banh or ""
				break
		con.append(
			{"ngay": ng, "ma_hang": ma, "ten_banh": ten, "so_luong": so,
			 "nguoi_nhap": frappe.session.user, "ghi_chu": ""}
		)
	doc.set("san_luong", [])
	for x in con:
		doc.append("san_luong", x)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang_ngay(doc.name, ng)


SUA_DUOC = {
	"san_xuat",
	# Cung mot o, ten moi. Xem luu_o() de biet vi sao nhan ca hai ten.
	"sx_dau_mua",
	# Them 21/08/2026: o so hop nha in da giao, tach hoi o San xuat cua bep.
	"nha_in_giao",
	"ghi_chu", "tran_ngay", "nhan_ngan", "khong_tran",
}


@frappe.whitelist()
def luu_o(mua=None, ma_hang=None, truong=None, gia_tri=None):
	"""Sua o So luong san xuat, Tran moi ngay, Nhan ngan, Khong dat tran, Ghi chu.

	Cac cot may dem KHONG sua tay duoc tu day - do la ca ly do phan he nay
	ton tai, y het bang kiem banh theo ngay.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if truong not in SUA_DUOC:
		frappe.throw(
			"Cột này máy tự đếm từ đơn Pancake nên không sửa tay được. Chỉ sửa được "
			"ô Số lượng sản xuất, Trần mỗi ngày, Nhãn ngắn, Không đặt trần và Ghi chú."
		)
	doc = frappe.get_doc(DT, mua)
	if doc.tinh_trang == "Da dong":
		frappe.throw("Mùa vụ này đã đóng nên không sửa nữa. Mở lại mùa rồi sửa.")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			if truong in ("san_xuat", "sx_dau_mua"):
				# O "San xuat" nay CHI DOC, no la tong cua hai thu. Nguoi go
				# vao o do that ra dang dat lai phan "bep lam truoc khi mo so
				# ngay", nen ghi vao dung o do. Man hinh cu goi ten "san_xuat"
				# van chay dung, khoi phai deploy hai ben cung luc.
				d.sx_dau_mua = max(0, cint(gia_tri))
			elif truong == "tran_ngay":
				d.tran_ngay = max(0, cint(gia_tri))
			elif truong == "nhan_ngan":
				d.nhan_ngan = _khong_dau(gia_tri).replace(" ", "")[:6]
			elif truong == "khong_tran":
				d.khong_tran = 1 if cint(gia_tri) else 0
			else:
				d.ghi_chu = str(gia_tri or "")[:140]
			doc.save()  # giu quyen that cua nguoi dang sua, de con vet ai sua gi
			frappe.db.commit()
			return {"ok": 1, "co_the_ban": d.co_the_ban, "san_xuat": d.san_xuat}
	frappe.throw("Không thấy mã hàng %s trong mùa này. Bấm Đồng bộ rồi thử lại." % ma_hang)


@frappe.whitelist()
def them_dong(mua=None, ma_hang=None):
	"""Them mot san pham chua co don nao - de sales dat han muc san xuat truoc."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ma = str(ma_hang or "").strip().upper()
	if not ma:
		frappe.throw("Chọn sản phẩm rồi bấm thêm giúp em.")
	doc = frappe.get_doc(DT, mua)
	if any(d.ma_hang == ma for d in doc.dong):
		frappe.throw("Sản phẩm %s đã có trong mùa này rồi." % ma)
	ten = frappe.db.get_value("Item", ma, "item_name") or ""
	doc.append("dong", {"ma_hang": ma, "ten_banh": ten, "san_xuat": 0})
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def xoa_dong(mua=None, ma_hang=None, dong_y_go=0):
	"""Bo mot san pham khoi mua, va ghi ma do vao danh sach loai tru.

	HAI MUC CHAN, KHONG PHAI MOT (anh Viet chot 22/08/2026)
	-------------------------------------------------------
	Don Pancake, tuc da_dat va cho_chot, la LOI HUA VOI KHACH: khach da bam
	dat, don dang chay. Bo dong di la giau mat mot con so dang co that, nen
	van chan cung, khong co duong vong.

	Rieng don_khac thi khac han. No khong phai don, no la con so MAY TU SUY
	ra tu hoa don ban ra trong khoang ngay cua mua. Chinh cho nay sinh ra
	ca bay: Banh Ba Trang la hang Tet Doan Ngo, ban tai quay dung mot cai
	ngay 18/08, mang tien to BASS nen bi may tu keo vao mua Trung thu, roi
	khoa luon khong cho ai go ra. Voi truong hop nay cho go, nhung phai
	truyen dong_y_go=1 de nguoi dung xac nhan mot cau chu khong bam nham.

	Go xong con ghi ma vao o Ma loai tru, neu khong lan dong bo sau lai keo
	dung cai ma vua go ve.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)
	giu, thay = [], None
	for d in doc.dong:
		if d.ma_hang != ma_hang:
			giu.append(d)
			continue
		thay = d
	if thay is None:
		frappe.throw("Không thấy sản phẩm %s trong mùa này." % ma_hang)

	don_that = cint(thay.da_dat) + cint(thay.cho_chot)
	if don_that:
		frappe.throw(
			"Sản phẩm %s đang có %d đơn Pancake nên không bỏ khỏi mùa được. "
			"Muốn ngừng bán thì đặt số Bếp làm và Tổng nhà in giao về 0."
			% (ma_hang, don_that)
		)
	if cint(thay.don_khac) and not cint(dong_y_go):
		frappe.throw(
			"Sản phẩm %s có %d cái đã bán qua kênh khác trong khoảng ngày của mùa. "
			"Đây là số máy tự đếm từ hoá đơn chứ không phải đơn đặt. Xác nhận một lần nữa "
			"nếu món này thực sự không thuộc mùa." % (ma_hang, cint(thay.don_khac))
		)

	doc.set("dong", giu)
	doc.ma_loai_tru = them_ma_loai_tru(doc.get("ma_loai_tru"), ma_hang)
	# Bang lich ke theo ma, khong don thi lich con dong cua mot ma da bi go.
	doc.set("lich", [d for d in (doc.get("lich") or []) if d.ma_hang != ma_hang])
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	_ghi_vet_go(mua, ma_hang, cint(thay.don_khac))
	return bang(mua)


def _ghi_vet_go(mua, ma_hang, so_kenh_khac):
	"""Ghi mot dong Comment len mua, de sau con truy ai go mon nao luc nao.

	QT-20: khong xoa vinh vien ma khong de lai vet. O Ma loai tru cho biet
	ma nao bi go, nhung khong cho biet ai go va luc nao.
	"""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": DT,
				"reference_name": mua,
				"content": "Gỡ sản phẩm %s khỏi mùa và thêm vào danh sách loại trừ. "
				"Số đã bán qua kênh khác lúc gỡ: %d." % (ma_hang, so_kenh_khac),
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "mua_vu: ghi vet go san pham")


@frappe.whitelist()
def doi_tinh_trang(mua=None, tinh_trang=None):
	"""Dong mua khi ban xong, hoac mo lai de sua."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	tt = str(tinh_trang or "").strip()
	if tt not in ("Dang ban", "Da dong"):
		frappe.throw("Tình trạng phải là Đang bán hoặc Đã đóng.")
	frappe.db.set_value(DT, mua, "tinh_trang", tt)
	frappe.db.commit()
	return {"ok": 1, "tinh_trang": tt}


@frappe.whitelist()
def tim_san_pham(tu_khoa="", mua=None):
	"""Goi y san pham de them vao mua. Uu tien hang mua vu (BASS)."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	q = str(tu_khoa or "").strip()
	loc = {"disabled": 0}
	if q:
		loc["item_name"] = ["like", "%%%s%%" % q]
	else:
		loc["item_code"] = ["like", "BASS%"]
	ds = frappe.get_all(
		"Item",
		filters=loc,
		fields=["name", "item_name"],
		limit_page_length=40,
		order_by="name desc",
	)
	da_co = set()
	if mua and frappe.db.exists(DT, mua):
		da_co = {
			d["ma_hang"]
			for d in frappe.get_all(
				"Vagabond Mua Vu Dong", filters={"parent": mua}, fields=["ma_hang"], limit_page_length=0
			)
		}
	return {
		"ds": [
			{"ma": d["name"], "ten": d["item_name"], "da_co": 1 if d["name"] in da_co else 0}
			for d in ds
			if str(d["name"]).upper().startswith(TIEN_TO_MA)
		]
	}


# ===================================================================
# CHOT CHAN BAN LO (anh Viet chot 18/08/2026)
# ===================================================================
#
# "Tuyet doi khong cho phep ban lo. Muon ban them thi phai cap nhat so
# luong cua cac loai hop de co so ma ban tiep."
#
# Chan o dau, va mot chuyen phai noi ro
# -------------------------------------
# Don Pancake duoc TAO o ben Pancake, khong o he minh. Nen he KHONG chan
# duoc luc sales bam luu ben do - minh khong dung giua ho va cai nut. Cho
# he chan duoc la khi don ay keo ve thanh hoa don, va moi cua ghi so khac:
# don tao tay tren app, POS, va duong dong bo Pancake.
#
# Anh Viet chon muc "chan o moi cua ghi so cua he". Nghia la don Pancake
# vuot han muc se bi TREO lai kem ly do ro rang chu khong ghi so, va sales
# phai vao cap nhat dot hang moi day tiep duoc.
#
# Vi sao chan o before_submit chu khong o validate: bill con nhap la sales
# dang go, chan giua luc go la lam ho ket khong luu duoc gi. Ghi so moi la
# luc so that su vao sach.

TT_DANG_BAN = "Dang ban"


def mua_dang_chay(ngay=None):
	"""Cac mua vu dang ban co ngay do nam trong khoang. Tra list ma mua."""
	ng = getdate(ngay) if ngay else getdate()
	return [
		d["name"]
		for d in frappe.get_all(
			DT,
			filters={
				"tinh_trang": TT_DANG_BAN,
				"tu_ngay": ["<=", ng],
				"den_ngay": [">=", ng],
			},
			fields=["name"],
			limit_page_length=0,
		)
	]


def _doc_mua(ma_mua):
	"""Doc dong va dinh muc cua mot mua thanh dict thuan."""
	doc = frappe.get_doc(DT, ma_mua)
	return (
		[d.as_dict() for d in doc.dong],
		[m.as_dict() for m in doc.get("dinh_muc") or []],
		doc,
	)


def kiem_han_muc(cac_dong_ban, ngay=None, bo_qua_hoa_don=None):
	"""Cac dong hang nay co vuot han muc mua vu nao khong.

	cac_dong_ban: list dict co item_code va qty.

	Tra list cau canh bao, rong nghia la ban duoc. KHONG nem loi o day -
	nguoi goi quyet dinh nem hay chi nhac, vi cung mot phep dung o ba cho
	voi ba muc do khac nhau.

	bo_qua_hoa_don: ma hoa don dang xet. Can thiet vi hoa don do co the DA
	nam trong so dem cua bang (neu no la don Pancake da keo ve), va luc ay
	dem lai la tru hai lan.
	"""
	gop = {}
	for r in cac_dong_ban or []:
		ma = str((r or {}).get("item_code") or "").strip()
		sl = cint((r or {}).get("qty"))
		if ma and sl > 0:
			gop[ma] = gop.get(ma, 0) + sl
	if not gop:
		return []

	nhac = []
	for ma_mua in mua_dang_chay(ngay):
		try:
			dong, dinh_muc, _doc = _doc_mua(ma_mua)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "mua_vu: doc mua %s loi" % ma_mua)
			continue
		ma_trong_mua = {str(d.get("ma_hang") or "") for d in dong}
		# Don nay da nam trong so dem cua bang chua? Neu roi thi khong tru
		# them lan nua - day la cho de sai nhat cua ca chot chan.
		da_dem = _da_dem_trong_bang(bo_qua_hoa_don, ma_mua)
		for ma, sl in gop.items():
			if ma not in ma_trong_mua or da_dem:
				continue
			con, am = con_sau_khi_them(dong, dinh_muc, ma, sl)
			if con is None:
				continue
			for ma_am, con_am in am:
				ten = _ten_dong(dong, ma_am)
				if ma_am == ma:
					nhac.append(
						"%s chỉ còn %d cái bán được mà đơn này lấy %d cái, thiếu %d. "
						"Vào màn Kiểm bánh theo mùa, thêm đợt hàng mới cho %s rồi ghi "
						"sổ lại."
						% (ten, cint(con) + sl, sl, -cint(con_am), ten)
					)
				else:
					nhac.append(
						"Bán %d %s sẽ lấy hết %s bên trong hộp và thiếu %d cái. Vào màn "
						"Kiểm bánh theo mùa, thêm đợt hàng mới cho %s rồi ghi sổ lại."
						% (sl, _ten_dong(dong, ma), ten, -cint(con_am), ten)
					)
	return nhac


def _ten_dong(dong, ma):
	for d in dong or []:
		if str(d.get("ma_hang") or "") == ma:
			return str(d.get("ten_banh") or ma)
	return ma


def _da_dem_trong_bang(ma_hoa_don, ma_mua):
	"""Hoa don nay da duoc bang mua vu dem chua.

	Don Pancake da keo ve thi so cua no NAM SAN trong cot Da dat, nen tru
	them lan nua la tru hai lan. Nhan biet bang cach: hoa don co ma don
	Pancake, va bang vua dong bo sau khi hoa don duoc lap.
	"""
	if not ma_hoa_don:
		return False
	try:
		d = frappe.db.get_value(
			SI, ma_hoa_don, ["custom_nguon", "custom_pancake_display_id"], as_dict=True
		)
		if not d:
			return False
		nguon = str(d.get("custom_nguon") or "").strip().lower()
		if nguon not in ("", "pancake"):
			# Don kenh khac duoc dem qua duong hoa don (cot Kenh khac), va
			# duong do doc theo posting_date nen bill dang ghi so CHUA vao.
			return False
		return bool(str(d.get("custom_pancake_display_id") or "").strip())
	except Exception:
		return False


def chan_ban_lo(doc, method=None):
	"""Hook before_submit cua Sales Invoice: khong cho ghi so don ban lo.

	Chan o BACKEND chu khong chi nhac tren man: nhac tren man thi bo qua
	duoc, ma anh Viet noi "tuyet doi khong cho phep ban lo".

	Hoa don TRA HANG khong bi chan: no tra hang VE, lam han muc rong ra chu
	khong an vao.
	"""
	try:
		if cint(doc.get("is_return")):
			return
		if cint(doc.get("vgb_huy")):
			return
		nhac = kiem_han_muc(
			[{"item_code": d.item_code, "qty": d.qty} for d in doc.get("items") or []],
			doc.get("posting_date"),
			doc.name,
		)
		if nhac:
			frappe.throw(
				"Đơn này vượt số lượng sản xuất của mùa vụ nên chưa ghi sổ được.\n\n"
				+ "\n\n".join(nhac)
			)
	except frappe.ValidationError:
		raise
	except Exception:
		# Chot chan hong KHONG duoc lam nghen ca duong ghi so: mot loi doc
		# bang mua vu khong the chan ke toan chot doanh thu ca ngay.
		frappe.log_error(frappe.get_traceback(), "mua_vu: chan ban lo loi")


@frappe.whitelist()
def kiem_truoc_khi_ban(items=None, ngay=None):
	"""Man POS va man tao don goi truoc khi luu, de nhac som.

	Tra {"duoc": 1} hoac {"duoc": 0, "nhac": [...]}. Man dung de to do va
	chan nut, con chot chan that van nam o before_submit.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if isinstance(items, str):
		try:
			items = json.loads(items)
		except Exception:
			return {"duoc": 1}
	nhac = kiem_han_muc(items, ngay)
	return {"duoc": 0 if nhac else 1, "nhac": nhac}


@frappe.whitelist()
def canh_bao():
	"""Chip do tren trang chu: ma nao con duoi 10 phan tram han muc.

	Anh Viet chot 18/08/2026. Tra ca ma da BAN LO (con so am) len dau, vi do
	la viec phai goi khach ngay hom nay chu khong phai viec de mai.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ra = []
	for ma_mua in mua_dang_chay():
		try:
			dong, _dm, doc = _doc_mua(ma_mua)
		except Exception:
			continue
		for d in dong:
			# Banh chi lam theo hop khong co tran rieng, nen khong bao gio
			# la "sap het" - tran that cua no nam o dong cai hop.
			if cint(d.get("khong_tran")):
				continue
			sx = cint(d.get("san_xuat"))
			con = cint(d.get("co_the_ban"))
			if sx <= 0 and con >= 0:
				continue
			pt = (con * 100.0 / sx) if sx > 0 else -1
			if con < 0 or pt < NGUONG_CANH_BAO:
				ra.append(
					{
						"mua": ma_mua,
						"ma_hang": d.get("ma_hang"),
						"ten": d.get("ten_banh") or d.get("ma_hang"),
						"san_xuat": sx,
						"con": con,
						"phan_tram": round(pt, 1) if sx > 0 else 0,
						"ban_lo": 1 if con < 0 else 0,
					}
				)
	# Ban lo len truoc, roi den cai con it nhat.
	ra.sort(key=lambda x: (0 if x["ban_lo"] else 1, x["con"]))
	return {
		"so": len(ra),
		"so_ban_lo": len([x for x in ra if x["ban_lo"]]),
		"ds": ra[:20],
		"nguong": NGUONG_CANH_BAO,
	}


# ------------------------------------------------------- dot va dinh muc


@frappe.whitelist()
def them_dot(mua=None, ma_hang=None, so_luong=0, ngay_du_kien=None, ghi_chu=""):
	"""Khai mot dot nha in giao (anh Viet chot 18/08/2026).

	Dot moi khai mac dinh CHUA VE. Sales bam Da ve khi hang that su den kho,
	va chi luc do han muc moi nhich len.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ma = str(ma_hang or "").strip().upper()
	if not ma:
		frappe.throw("Chọn sản phẩm cho đợt này giúp em.")
	sl = cint(so_luong)
	if sl <= 0:
		frappe.throw("Số lượng đợt phải lớn hơn 0. Nhập lại giúp em.")
	doc = frappe.get_doc(DT, mua)
	if doc.tinh_trang != TT_DANG_BAN:
		frappe.throw("Mùa vụ này đã đóng nên không thêm đợt nữa. Mở lại mùa rồi thêm.")
	if not any(x.ma_hang == ma for x in doc.dong):
		frappe.throw(
			"Sản phẩm %s chưa có trong mùa này. Bấm Thêm sản phẩm trước rồi khai đợt." % ma
		)
	ten = frappe.db.get_value("Item", ma, "item_name") or ""
	doc.append(
		"dot",
		{
			"ma_hang": ma,
			"ten_banh": ten,
			"so_luong": sl,
			"ngay_du_kien": getdate(ngay_du_kien) if ngay_du_kien else None,
			"da_ve": 0,
			"ghi_chu": str(ghi_chu or "")[:140],
		},
	)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def danh_dau_dot_ve(mua=None, chi_so=None, da_ve=1):
	"""Bam Da ve cho mot dot. Day la luc han muc that nhich len."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)
	i = cint(chi_so)
	cac = doc.get("dot") or []
	if i < 0 or i >= len(cac):
		frappe.throw("Không thấy đợt này. Bấm Đồng bộ rồi thử lại.")
	cac[i].da_ve = 1 if cint(da_ve) else 0
	cac[i].ngay_ve_that = getdate() if cint(da_ve) else None
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def xoa_dot(mua=None, chi_so=None):
	"""Bo mot dot khai nham. Dot DA VE thi khong bo duoc.

	Vi sao chan: dot da ve la hang da nam trong kho va co the da ban ra.
	Bo di la han muc tut xuong duoi so da ban, va bang lap tuc bao ban lo
	mot con so khong ai hieu tu dau ra.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)
	i = cint(chi_so)
	cac = doc.get("dot") or []
	if i < 0 or i >= len(cac):
		frappe.throw("Không thấy đợt này. Bấm Đồng bộ rồi thử lại.")
	if cint(cac[i].da_ve):
		frappe.throw(
			"Đợt này đã đánh dấu hàng về nên không bỏ được. Bấm bỏ dấu Đã về trước, "
			"rồi mới xoá."
		)
	doc.set("dot", [x for k, x in enumerate(cac) if k != i])
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def them_dinh_muc(mua=None, ma_hop=None, ma_banh=None, so_luong=0):
	"""Khai mot hop gom bao nhieu banh le nao (anh Viet chot 18/08/2026)."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	hop = str(ma_hop or "").strip().upper()
	banh = str(ma_banh or "").strip().upper()
	sl = cint(so_luong)
	if not hop or not banh:
		frappe.throw("Chọn cả hộp và bánh lẻ giúp em.")
	if hop == banh:
		frappe.throw("Hộp và bánh lẻ không thể là cùng một mã.")
	if sl <= 0:
		frappe.throw("Số bánh trong một hộp phải lớn hơn 0. Nhập lại giúp em.")
	doc = frappe.get_doc(DT, mua)
	co = {d.ma_hang for d in doc.dong}
	thieu = [x for x in (hop, banh) if x not in co]
	if thieu:
		frappe.throw(
			"Chưa có %s trong mùa này. Bấm Thêm sản phẩm cho nó trước rồi khai định mức."
			% ", ".join(thieu)
		)
	for m in doc.get("dinh_muc") or []:
		if m.ma_hop == hop and m.ma_banh == banh:
			m.so_luong = sl
			doc.flags.ignore_permissions = True
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			return bang(mua)
	doc.append(
		"dinh_muc",
		{
			"ma_hop": hop,
			"ten_hop": frappe.db.get_value("Item", hop, "item_name") or "",
			"ma_banh": banh,
			"ten_banh": frappe.db.get_value("Item", banh, "item_name") or "",
			"so_luong": sl,
		},
	)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


@frappe.whitelist()
def xoa_dinh_muc(mua=None, ma_hop=None, ma_banh=None):
	"""Bo mot dong dinh muc."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)
	doc.set(
		"dinh_muc",
		[
			m
			for m in (doc.get("dinh_muc") or [])
			if not (m.ma_hop == ma_hop and m.ma_banh == ma_banh)
		],
	)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)
# ===================================================================
# SAN LUONG BEP THEO NGAY
# ===================================================================
#
# Bep truong nhap moi ngay mot dong cho tung vi banh le. Tong cac dong nay
# chay vao o "San xuat" cua bang dong. O do KHONG trung voi o "Tong nha in
# giao": nha in giao VO HOP, bep lam RUOT BANH (anh Viet chot 21/08/2026).
#
# Moi ham deu nap lai doc roi luu, de validate chay lai va tinh lai ca ba cot
# co_the_ban, ghep_duoc, con_thuc_te. Khong ham nao tu tinh lay - mot cho tinh.


@frappe.whitelist()
def them_san_luong(mua=None, ngay=None, ma_hang=None, so_luong=0, ghi_chu=""):
	"""Bep nhap so lam duoc cua mot vi trong mot ngay.

	Cung mot ma trong cung mot ngay thi CONG DON vao dong da co, khong tao dong
	thu hai. Bep lam hai me sang chieu thi vao go hai lan, va con so phai cong
	lai chu khong phai de hai dong roi ai do tu cong tay.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = _doc_mua(mua)
	ma = str(ma_hang or "").strip()
	ng = getdate(ngay) if ngay else getdate()
	so = cint(so_luong)
	if not ma:
		frappe.throw("Chưa chọn mã hàng.")
	ten = ""
	for d in doc.dong:
		if d.ma_hang == ma:
			ten = d.ten_banh or ""
			break
	for x in doc.get("san_luong") or []:
		if x.ma_hang == ma and getdate(x.ngay) == ng:
			x.so_luong = cint(x.so_luong) + so
			x.nguoi_nhap = frappe.session.user
			if ghi_chu:
				x.ghi_chu = ghi_chu
			break
	else:
		doc.append(
			"san_luong",
			{
				"ngay": ng,
				"ma_hang": ma,
				"ten_banh": ten,
				"so_luong": so,
				"nguoi_nhap": frappe.session.user,
				"ghi_chu": ghi_chu or "",
			},
		)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.name)


@frappe.whitelist()
def sua_san_luong(mua=None, ngay=None, ma_hang=None, so_luong=0):
	"""Dat lai so lam duoc cua mot vi trong mot ngay. Go nham thi sua o day."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = _doc_mua(mua)
	ma = str(ma_hang or "").strip()
	ng = getdate(ngay) if ngay else getdate()
	for x in doc.get("san_luong") or []:
		if x.ma_hang == ma and getdate(x.ngay) == ng:
			x.so_luong = cint(so_luong)
			x.nguoi_nhap = frappe.session.user
			break
	else:
		frappe.throw("Không thấy dòng sản lượng của mã %s ngày %s." % (ma, ng))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.name)


@frappe.whitelist()
def xoa_san_luong(mua=None, ngay=None, ma_hang=None):
	"""Xoa mot dong san luong. Nguon cung tu giam theo, khong phai sua tay."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = _doc_mua(mua)
	ma = str(ma_hang or "").strip()
	ng = getdate(ngay) if ngay else getdate()
	con = [
		x for x in (doc.get("san_luong") or [])
		if not (x.ma_hang == ma and getdate(x.ngay) == ng)
	]
	doc.set("san_luong", [])
	for x in con:
		doc.append(
			"san_luong",
			{
				"ngay": x.ngay, "ma_hang": x.ma_hang, "ten_banh": x.ten_banh,
				"so_luong": x.so_luong, "nguoi_nhap": x.nguoi_nhap, "ghi_chu": x.ghi_chu,
			},
		)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(doc.name)
def mo_so_san_luong_ngay():
	"""Dua so go tay cu vao o moi "Bep lam truoc khi mo so". Chay mot lan.

	Vi sao can (anh Viet 22/08/2026: "tab San luong nhap so vao he thong nuot
	luon"): truoc ban nay, validate() viet `d.san_xuat = tong cac dong san
	luong`, tuc THAY THE chu khong cong. Ai go 1700 cho ca mua, roi bep nhap
	120 cua mot ngay, la con so 1700 bien mat khong mot loi bao.

	Tu ban nay o San xuat chi doc va bang tong hai thu:
	    sx_dau_mua (go tay) + tong cac dong san luong theo ngay

	Ham nay dat sx_dau_mua = san_xuat tru di tong cac dong san luong da co, kep
	xuong 0. Y nghia tung truong hop:

	  - Dong CHUA co dong san luong nao: sx_dau_mua = san_xuat, giu nguyen y
	    so nguoi da go. Day la phan lon cac dong.
	  - Dong DA co dong san luong: so go tay da bi ghi de mat tu truoc, tru ra
	    con 0. Ham nay KHONG doan lai con so da mat - doan la bia. Ten cac ma
	    do duoc ghi vao nhat ky de bao lai cho nguoi go nhap lai.

	LAP LAI DUOC: chi dat khi sx_dau_mua dang bang 0. Chay lan hai khong dung
	vao so ai vua go.
	"""
	doi, can_nhap_lai = 0, []
	for ten in frappe.get_all(DT, pluck="name"):
		try:
			doc = frappe.get_doc(DT, ten)
		except Exception:
			continue
		bep = san_luong_theo_ma([x.as_dict() for x in doc.get("san_luong") or []])
		co_doi = False
		for d in doc.dong:
			if cint(d.get("sx_dau_mua")):
				continue
			cu = cint(d.san_xuat)
			if not cu:
				continue
			d.sx_dau_mua = max(0, cu - cint(bep.get(d.ma_hang, 0)))
			co_doi = True
			if not cint(d.sx_dau_mua) and bep.get(d.ma_hang):
				can_nhap_lai.append("%s/%s" % (ten, d.ma_hang))
		if co_doi:
			doc.save(ignore_permissions=True)
			doi += 1
	if doi:
		frappe.db.commit()
	if can_nhap_lai:
		frappe.logger().info(
			"mo_so_san_luong_ngay: %d dong tung bi ghi de, can go lai so ca mua: %s"
			% (len(can_nhap_lai), ", ".join(can_nhap_lai[:40]))
		)
	return {"mua_da_doi": doi, "can_nhap_lai": can_nhap_lai}


def chuyen_so_nha_in():
	"""Chuyen so hop cu tu o "San xuat" sang o "Tong nha in giao". Chay mot lan.

	Truoc 21/08/2026 chi co MOT o San xuat, va no gom ca hai thu: so vo hop nha
	in giao va so ruot banh bep lam. Tu ban nay tach lam hai o. Neu khong chuyen
	thi cac dong HOP dang co so nam o o San xuat, con o Tong nha in giao bang 0,
	nhin vao tuong nha in chua giao gi.

	Chi dong nao la HOP moi chuyen, tuc co mat o cot ma_hop cua dinh muc. Dong
	banh le thi so trong o San xuat von la so bep lam, dung cho roi, khong dong.

	LAP LAI DUOC: chi chuyen khi o Tong nha in giao dang bang 0. Chay lan thu
	hai khong doi gi, va cung khong de len so ai vua go tay.
	"""
	doi = 0
	for ten in frappe.get_all(DT, pluck="name"):
		try:
			doc = frappe.get_doc(DT, ten)
		except Exception:
			continue
		la_hop = ma_la_hop([m.as_dict() for m in doc.get("dinh_muc") or []])
		if not la_hop:
			continue
		co_doi = False
		for d in doc.dong:
			if d.ma_hang in la_hop and not cint(d.nha_in_giao) and cint(d.san_xuat):
				d.nha_in_giao = cint(d.san_xuat)
				d.san_xuat = 0
				co_doi = True
		if co_doi:
			doc.save(ignore_permissions=True)
			doi += 1
	if doi:
		frappe.db.commit()
	return {"mua_da_doi": doi}
# ===================================================================
# CUA CHO TRANG DAT BANH: NHOM "IN SEASON"
# ===================================================================


def _ruot_cua_hop(dinh_muc, ten_theo_ma):
	"""Chuoi mo ta ruot cua tung hop, vi du "2 x Banh 110g, 4 x Banh 80g". THUAN."""
	ra = {}
	for m in dinh_muc or []:
		m = m or {}
		hop = str(m.get("ma_hop") or "").strip()
		banh = str(m.get("ma_banh") or "").strip()
		sl = cint(m.get("so_luong"))
		if not hop or not banh or sl <= 0:
			continue
		ra.setdefault(hop, []).append(
			"%d x %s" % (sl, (ten_theo_ma or {}).get(banh) or banh)
		)
	return {k: ", ".join(v) for k, v in ra.items()}


@frappe.whitelist(allow_guest=True)
def hang_theo_mua():
	"""Nhom hang mua vu cho trang dat banh order.thevagabondpatisserie.com.

	KHONG dung chung nguon voi bang kiem banh theo ngay (anh Viet chot
	21/08/2026). Hai bang tra loi hai cau hoi khac han: ben ngay hoi "hom nay
	con bao nhieu cai", ben mua hoi "ca mua nay con bao nhieu cai". Hang mua vu
	mang tien to BASS, ma bang theo ngay chi dem BAWC va BAWS, nen tu truoc toi
	nay banh Trung thu chua bao gio len web.

	So dua ra web la **con_thuc_te**, tuc da lay so nho hon giua vo hop con va
	ruot ghep duoc. Dua co_the_ban ra la ban lo nhung hop ma bep khong con ruot
	de lam.

	Mon het hang van tra ve, kem co het = 1. Man hinh phai HIEN ma khoa nut chu
	khong an di: an di thi khach tuong tiem khong lam mon do, con hien ma khoa
	thi khach biet de hoi dot sau.
	"""
	rong = {"co": 0, "mon": []}
	ngay = getdate()
	cac_mua = mua_dang_chay(ngay)
	if not cac_mua:
		return rong
	# Mot mua mot lan. Hai mua cung chay la chuyen hiem va luc do lay mua co
	# ngay ket thuc gan nhat, vi do la mua dang gap.
	ten_mua = sorted(
		cac_mua, key=lambda m: str(frappe.db.get_value(DT, m, "den_ngay") or "9999-12-31")
	)[0]
	try:
		doc = frappe.get_doc(DT, ten_mua)
	except Exception:
		return rong

	ten_theo_ma = {d.ma_hang: (d.ten_banh or d.ma_hang) for d in doc.dong}
	ruot = _ruot_cua_hop([m.as_dict() for m in doc.get("dinh_muc") or []], ten_theo_ma)
	la_hop = ma_la_hop([m.as_dict() for m in doc.get("dinh_muc") or []])

	ds = frappe.get_all(
		"Item",
		filters={"item_code": ["in", [d.ma_hang for d in doc.dong]]},
		fields=["item_code", "item_name", "image", "standard_rate", "disabled", "is_sales_item"],
		limit_page_length=0,
	)
	it = {x["item_code"]: x for x in ds}

	mon = []
	for d in doc.dong:
		x = it.get(d.ma_hang) or {}
		# Mon da tat hoac khong phai hang ban ra thi khong bay len web.
		if cint(x.get("disabled")) or not cint(x.get("is_sales_item", 1)):
			continue
		# Banh chi lam theo hop thi khong ban le, khong dua ra web.
		if cint(d.khong_tran):
			continue
		anh = d.hinh or x.get("image") or ""
		if str(anh).startswith("/private"):
			anh = ""
		con = cint(d.con_thuc_te)
		mon.append(
			{
				"ma": d.ma_hang,
				"ten": x.get("item_name") or d.ten_banh or d.ma_hang,
				"gia": int(x.get("standard_rate") or 0),
				"anh": anh,
				"con": con if con > 0 else 0,
				"het": 0 if con > 0 else 1,
				"la_hop": 1 if d.ma_hang in la_hop else 0,
				"ruot": ruot.get(d.ma_hang, ""),
			}
		)
	if not mon:
		return rong

	# Hop len truoc banh le, roi trong moi nhom thi con hang len truoc.
	mon.sort(key=lambda m: (-m["la_hop"], m["het"], m["ten"]))
	return {
		"co": 1,
		"mua": doc.name,
		"ten_mua": doc.ten_mua,
		"den_ngay": str(doc.den_ngay or ""),
		"mon": mon,
	}
