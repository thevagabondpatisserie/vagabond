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
import requests
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
GIAN_CACH_DONG_BO = 30  # giay. Keo ca mua nang hon keo mot ngay nen gian ra.

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
	ban = {}
	theo_ma = {}
	for d in dong or []:
		d = d or {}
		ma = str(d.get("ma_hang") or "").strip()
		if not ma:
			continue
		theo_ma[ma] = d
		ban[ma] = cint(d.get("da_dat")) + cint(d.get("cho_chot")) + cint(d.get("don_khac"))
	if ma_hang not in theo_ma:
		# Ma khong nam trong mua nay thi khong bi rang buoc han muc.
		return None, []
	ban[ma_hang] = ban.get(ma_hang, 0) + so_them

	trong = banh_le_trong_hop(dinh_muc, ban)
	am, con_cua_ma = [], None
	for ma, d in theo_ma.items():
		con = con_ban_duoc(
			d.get("san_xuat"),
			d.get("da_dat"),
			d.get("cho_chot"),
			d.get("don_khac"),
			trong.get(ma, 0),
		)
		if ma == ma_hang:
			con -= so_them
			con_cua_ma = con
		if con < 0 and not cint(d.get("khong_tran")):
			am.append((ma, con))
	return con_cua_ma, am


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
	"""Keo het don giao trong khoang mua, lat qua tung trang."""
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


def _dem(dons):
	"""Gop don thanh bon bang. THUAN tren du lieu Pancake, khong doc CSDL.

	Tra ve:
	  dem_chot  {ma: so}          don da chot
	  dem_cho   {ma: so}          don con trang thai Moi
	  theo_ngay {(ma, ngay): {"chot": n, "cho": n, "khach": [..]}}
	  ten, hinh {ma: ...}
	"""
	dem_chot, dem_cho, theo_ngay, ten, hinh = {}, {}, {}, {}, {}
	for o in dons:
		if o.get("status") in BO_QUA_TT:
			continue
		cho = o.get("status") == 0
		ngay = _ngay_giao(o)
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
				o_l = theo_ngay.setdefault((ma, ngay), {"chot": 0, "cho": 0, "khach": []})
				o_l["cho" if cho else "chot"] += sl
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
	try:
		r = frappe.db.sql(
			"""select sii.item_code as ma, sum(sii.qty) as sl
			from `tabSales Invoice Item` sii
			join `tabSales Invoice` si on si.name = sii.parent
			where si.docstatus < 2
			  and ifnull(si.vgb_huy, 0) = 0
			  and si.posting_date between %s and %s
			  and lower(ifnull(si.custom_nguon, '')) not in ('', 'pancake')
			group by sii.item_code""",
			(getdate(tu_ngay), getdate(den_ngay)),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "mua_vu: dem kenh khac loi")
		return {}
	return {
		d["ma"]: cint(d["sl"])
		for d in r
		if str(d.get("ma") or "").upper().startswith(TIEN_TO_MA)
	}


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


@frappe.whitelist()
def dong_bo(mua=None):
	"""Dem lai ca mua tu Pancake: theo san pham va theo tung ngay giao."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
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

	dau, cuoi = _khoang_unix(doc.tu_ngay, doc.den_ngay)
	dons = _keo_don(c, k, dau, cuoi)
	dem_chot, dem_cho, theo_ngay, ten, hinh = _dem(dons)
	khac = _dem_kenh_khac(doc.tu_ngay, doc.den_ngay)

	# Giu nguyen dong san pham nguoi da them va SO LUONG SAN XUAT ho da go.
	# Day la o duy nhat nguoi go, dong bo ma xoa mat no la xoa cong viec
	# cua ho.
	co = {d.ma_hang: d for d in doc.dong}
	for ma in set(list(dem_chot) + list(dem_cho) + list(khac)):
		if ma not in co:
			# CHI hang mua vu moi duoc tu dua vao. Banh thuong ban trong
			# cung khoang ngay thi khong lien quan den han muc mua nay.
			if not ma.upper().startswith(TU_THEM):
				continue
			d = doc.append("dong", {"ma_hang": ma, "ten_banh": ten.get(ma, ""), "san_xuat": 0})
			co[ma] = d
		elif ten.get(ma) and not co[ma].ten_banh:
			co[ma].ten_banh = ten[ma]

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
	doc.set("lich", [])
	for (ma, ngay), o_l in sorted(theo_ngay.items(), key=lambda x: (x[0][1], x[0][0])):
		if not (o_l["chot"] or o_l["cho"]):
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
				"so_luong": o_l["chot"],
				"cho_chot": o_l["cho"],
				"ten_khach": ", ".join(o_l["khach"])[:500],
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

	return {
		"co_so": 1,
		"mua": doc.name,
		"ten_mua": doc.ten_mua,
		"tu_ngay": str(doc.tu_ngay),
		"den_ngay": str(doc.den_ngay),
		"tinh_trang": doc.tinh_trang,
		"dong_bo_luc": str(doc.dong_bo_luc or ""),
		"dong": [
			{
				"ma_hang": d.ma_hang,
				"ten_banh": d.ten_banh or "",
				"hinh": d.hinh or "",
				"nhan_ngan": d.nhan_ngan or "",
				"khong_tran": cint(d.khong_tran),
				"tran_ngay": cint(d.tran_ngay),
				"san_xuat": d.san_xuat or 0,
				"da_dat": d.da_dat or 0,
				"cho_chot": d.cho_chot or 0,
				"don_khac": d.don_khac or 0,
				"trong_hop": d.trong_hop or 0,
				"co_the_ban": d.co_the_ban or 0,
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


SUA_DUOC = {"san_xuat", "ghi_chu", "tran_ngay", "nhan_ngan", "khong_tran"}


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
			if truong == "san_xuat":
				d.san_xuat = max(0, cint(gia_tri))
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
def xoa_dong(mua=None, ma_hang=None):
	"""Bo mot san pham khoi mua. Chi bo duoc khi CHUA co don nao.

	Co don roi ma bo di la giau mat mot con so dang co that: khach van dat,
	don van chay, ma bang khong con dong nao de tru.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	doc = frappe.get_doc(DT, mua)
	giu = []
	for d in doc.dong:
		if d.ma_hang != ma_hang:
			giu.append(d)
			continue
		if (d.da_dat or 0) or (d.cho_chot or 0) or (d.don_khac or 0):
			frappe.throw(
				"Sản phẩm %s đã có %d đơn nên không bỏ khỏi mùa được. Muốn ngừng bán "
				"thì đặt Số lượng sản xuất về 0."
				% (ma_hang, (d.da_dat or 0) + (d.cho_chot or 0) + (d.don_khac or 0))
			)
	doc.set("dong", giu)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(mua)


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
