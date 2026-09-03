# -*- coding: utf-8 -*-
"""Nam nut kho hoc tu SAP, anh Viet duyet 03/09/2026.

Nam muc anh chon lam truoc, tu de xuat trong project doc
`nguyen-tac-thiet-ke-man-hinh-app-va-de-xuat-kho-theo-sap`:

  1. Dong bang so sach va khoa ma khi kiem ke (SAP: Physical Inventory).
  2. Dem mu: nguoi dem khong thay ton so, chi quan ly thay hai cot.
  3. Ly do chenh lech chuan, moi ly do mot tai khoan.
  4. Lo va han dung toi thieu theo mon (SAP: batch va SLED).
  5. Dung sai giao thua giao thieu, mac dinh 5 phan tram (SAP: over/under
     delivery tolerance tren tung dong don mua).

Tep nay giu PHEP THUAN: khong cham Frappe, khong doc site, nen kiem thu
duoc khong can cai gi. Phan cham he nam o `kiem_ke.py`, `nhan_hang.py` va
cac hook - chung goi xuong day chu khong tu tinh lai, de mot luat chi nam
o mot cho (QT-19).
"""

EPS = 0.0005

# ------------------------------------------------------- 5. dung sai giao

# Anh Viet chot 03/09/2026: mac dinh 5 phan tram, chinh duoc trong Cai dat.
DUNG_SAI_MAC_DINH = 5.0

# Tran cung: khong ai duoc dat dung sai qua muc nay. Dung sai la duong hop
# phap de nhan hang ngoai don, mo qua rong thi don mua khong con nghia gi.
DUNG_SAI_TRAN = 20.0


def chuan_dung_sai(v, mac_dinh=DUNG_SAI_MAC_DINH):
	"""Doc mot con so dung sai nguoi dung go vao ve khoang cho phep."""
	try:
		x = float(v)
	except (TypeError, ValueError):
		return mac_dinh
	if x < 0:
		return 0.0
	if x > DUNG_SAI_TRAN:
		return DUNG_SAI_TRAN
	return x


def muc_thua_cho_phep(dat, ty_le):
	"""So luong duoc phep nhan VUOT so dat cua mot dong don mua."""
	return abs(float(dat or 0)) * chuan_dung_sai(ty_le) / 100.0


def soat_nhan_thua(dat, da_nhan, dang_nhap, ty_le=DUNG_SAI_MAC_DINH):
	"""Dong nay nhan chung nay co qua so dat khong, va co qua dung sai khong.

	Tra ve {"qua": 0/1, "trong_dung_sai": 0/1, "du": so, "tran": so}.

	  qua = 0             : chua cham toi so dat, khong co gi de noi.
	  qua = 1, trong = 1  : co du nhung con trong dung sai, cho nhan va GHI VET.
	  qua = 1, trong = 0  : du qua muc, CHAN.

	SAP goi day la over-delivery tolerance, dat tren tung dong don mua. Minh
	dat mot muc chung trong Cai dat cho gon, vi tiem chi co mot nhom hang.
	"""
	dat = float(dat or 0)
	da = float(da_nhan or 0)
	them = float(dang_nhap or 0)
	con = dat - da
	du = them - con
	if du <= EPS:
		return {"qua": 0, "trong_dung_sai": 1, "du": 0.0, "tran": muc_thua_cho_phep(dat, ty_le)}
	tran = muc_thua_cho_phep(dat, ty_le)
	return {
		"qua": 1,
		"trong_dung_sai": 1 if du <= tran + EPS else 0,
		"du": du,
		"tran": tran,
	}


def thieu_dong_duoc(dat, da_nhan, ty_le=DUNG_SAI_MAC_DINH):
	"""Phan con lai da du nho de coi nhu giao du chua.

	SAP goi la under-delivery tolerance: nha cung cap giao thieu trong nguong
	thi don coi nhu xong, khong treo mai mot dong le. Minh KHONG tu dong dong
	don - chi tra ve 1 de man hinh moi nguoi bam nut dong phan con lai.
	"""
	dat = float(dat or 0)
	con = dat - float(da_nhan or 0)
	if con <= EPS:
		return 0
	return 1 if con <= muc_thua_cho_phep(dat, ty_le) + EPS else 0


def cau_nhan_thua(ten_mon, kq, dvt=""):
	"""Cau noi cho nguoi dung khi mot dong nhan vuot so dat."""
	dv = (" " + dvt) if dvt else ""
	if not kq.get("qua"):
		return ""
	if kq.get("trong_dung_sai"):
		return "%s: nhận dư %s%s, còn trong dung sai nên máy cho nhận và ghi lại vết." % (
			ten_mon, _so(kq["du"]), dv,
		)
	return "%s: nhận dư %s%s, vượt mức cho phép %s%s." % (
		ten_mon, _so(kq["du"]), dv, _so(kq["tran"]), dv,
	)


def _so(v):
	v = float(v or 0)
	if abs(v - round(v)) < EPS:
		return "%d" % round(v)
	return ("%.3f" % v).rstrip("0").rstrip(".")


# ------------------------------------------- 4. lo va han dung toi thieu

# So ngay han dung con lai toi thieu khi nhan hang, dung khi mon chua khai
# rieng. 0 nghia la khong soi.
HSD_TOI_THIEU_MAC_DINH = 0


def con_bao_nhieu_ngay(hsd, hom_nay):
	"""So ngay tu hom nay den han dung. Am la da qua han."""
	if not hsd or not hom_nay:
		return None
	return (hsd - hom_nay).days


def soat_han_dung(hsd, hom_nay, toi_thieu):
	"""Han dung cua lo sap nhan co du dai khong.

	Tra ve {"co_han": 0/1, "con": so ngay, "dat": 0/1, "toi_thieu": so}.
	Khong khai han thi khong ket luan gi - viec bat buoc khai nam o
	`bat_buoc_han_dung`, tach ra vi hai cau hoi khac nhau.
	"""
	tt = int(toi_thieu or 0)
	con = con_bao_nhieu_ngay(hsd, hom_nay)
	if con is None:
		return {"co_han": 0, "con": None, "dat": 1, "toi_thieu": tt}
	return {"co_han": 1, "con": con, "dat": 1 if (tt <= 0 or con >= tt) else 0, "toi_thieu": tt}


def bat_buoc_han_dung(theo_lo, toi_thieu=0):
	"""Mon nay nhap kho co bat buoc khai han dung khong.

	Mon quan ly theo lo thi CO. SAP khong cho ghi so mot lo khong han dung
	khi mon co khai SLED, vi lo khong han thi phep lay hang theo han (FEFO)
	khong con biet lay cai nao truoc.
	"""
	return 1 if (theo_lo or int(toi_thieu or 0) > 0) else 0


def cau_han_dung(ten_mon, kq):
	"""Cau noi khi han dung khong du dai."""
	if kq.get("dat"):
		return ""
	con = kq.get("con")
	if con is None:
		return "%s: chưa khai hạn sử dụng." % ten_mon
	if con < 0:
		return "%s: lô này đã quá hạn %d ngày." % (ten_mon, -con)
	return "%s: hạn dùng chỉ còn %d ngày, mặt hàng này cần ít nhất %d ngày." % (
		ten_mon, con, kq.get("toi_thieu") or 0,
	)


# ------------------------------- 1. dong bang so sach va khoa ma khi kiem

# Trang thai cua phieu kiem ke ma trong luc do KHONG duoc dong vao ton cua
# nhung ma dang dem. "Da chot" van khoa: chot xong la cho quan ly ghi so
# chenh lech, ma trong luc cho do ban them ba cai la con so chenh lech tro
# thanh so cua mot ngay khac.
TRANG_THAI_KHOA = ("Đang kiểm", "Chờ duyệt", "Đã chốt")


# Phieu kiem bo quen thi KHONG duoc khoa mai. Khoa ca kho vi mot phieu ai do
# mo hom truoc roi di nghi la ca tiem dung nhap xuat, ma khong ai biet go o
# dau. Qua so ngay nay thi phieu het quyen khoa, va man Cai dat keu len.
SO_NGAY_KHOA = 2


def con_hieu_luc_khoa(ngay_kiem, hom_nay, so_ngay=SO_NGAY_KHOA):
	"""Phieu kiem nay con duoc khoa ma khong."""
	if not ngay_kiem or not hom_nay:
		return 1
	return 1 if (hom_nay - ngay_kiem).days <= int(so_ngay) else 0


def khoa_dang_kiem(phieu):
	"""Tap (kho, ma hang) dang bi khoa, dung tu danh sach phieu dang mo.

	`phieu` la danh sach {"kho", "trang_thai", "ma", "con_hieu_luc"}. Phieu
	khong ghi `con_hieu_luc` thi coi nhu con.
	"""
	ra = set()
	for p in phieu or []:
		if str((p or {}).get("trang_thai") or "") not in TRANG_THAI_KHOA:
			continue
		if not (p or {}).get("con_hieu_luc", 1):
			continue
		kho = str((p or {}).get("kho") or "").strip()
		if not kho:
			continue
		for m in (p or {}).get("ma") or []:
			m = str(m or "").strip()
			if m:
				ra.add((kho, m))
	return ra


def dong_bi_khoa(dong, khoa):
	"""Nhung dong chung tu dang cham vao ma bi khoa.

	`dong` la danh sach {"ma": ..., "kho": [...]} - mot dong co the cham hai
	kho (phieu dieu chuyen), soi ca hai.
	"""
	ra = []
	for d in dong or []:
		ma = str((d or {}).get("ma") or "").strip()
		if not ma:
			continue
		for kho in (d or {}).get("kho") or []:
			kho = str(kho or "").strip()
			if kho and (kho, ma) in khoa:
				ra.append({"ma": ma, "kho": kho})
				break
	return ra


def cau_bi_khoa(vuong, ten_mon=None):
	"""Cau chan, noi ro dang vuong ma nao o kho nao va phai lam gi."""
	ten_mon = ten_mon or {}
	if not vuong:
		return ""
	dong = [
		"%s tại %s" % (ten_mon.get(v["ma"]) or v["ma"], v["kho"])
		for v in vuong[:8]
	]
	them = "" if len(vuong) <= 8 else " và %d mặt hàng nữa" % (len(vuong) - 8)
	return (
		"Đang có phiếu kiểm kê mở trên những mặt hàng này nên chưa ghi sổ "
		"được:<br>%s%s<br><br>Đếm xong và ghi sổ chênh lệch của phiếu kiểm thì "
		"chứng từ này lưu được ngay. Ghi sổ lúc đang đếm thì con số chênh lệch "
		"đếm ra không còn đúng với thời điểm nào cả." % ("<br>".join(dong), them)
	)


# --------------------------------------------------------- 2. dem mu

def duoc_thay_ton_so(trang_thai, la_quan_ly):
	"""Nguoi dang mo phieu co duoc thay cot ton so khong.

	SAP dem mu: nguoi di dem chi go so dem duoc, khong thay may dang ghi bao
	nhieu, de khong "dem cho khop". Quan ly thi thay ca hai cot, vi viec cua
	quan ly la soi chenh lech.
	"""
	if la_quan_ly:
		return 1
	return 0 if str(trang_thai or "") == "Đang kiểm" else 1


def che_ton_so(dong, hien):
	"""Bo cot ton so khoi cac dong gui ve may khach khi dang dem mu."""
	if hien:
		return dong
	ra = []
	for d in dong or []:
		x = dict(d or {})
		x["ton_he_thong"] = None
		x["lech"] = None
		x["dem_mu"] = 1
		ra.append(x)
	return ra


# ------------------------------------------- 3. ly do chenh lech chuan

# Moi ly do mot tai khoan, giong cach "muc dich xuat dung" dang lam. Cuoi
# thang doc bao cao lech theo ly do la biet nen sua quy trinh nao.
#
# `dau` noi ly do do hop voi chenh lech chieu nao: -1 chi thieu, +1 chi thua,
# 0 la ca hai. Chon ly do nguoc chieu la sai nghia, nen man hinh chi bay ra
# nhung ly do dung chieu.
LY_DO_LECH = [
	{
		"ma": "hao_hut",
		"ten": "Hao hụt tự nhiên",
		"mo": "Bay hơi, rơi vãi, dính bao bì. Chỉ dùng cho mức nhỏ.",
		"dau": -1,
		"tk": "632",
	},
	{
		"ma": "hu_hong",
		"ten": "Hư hỏng, hết hạn",
		"mo": "Hàng còn đó nhưng không dùng được nữa, hoặc đã bỏ mà quên lập phiếu.",
		"dau": -1,
		"tk": "632",
	},
	{
		"ma": "quen_phieu_xuat",
		"ten": "Xuất dùng quên lập phiếu",
		"mo": "Bếp đã lấy dùng mà chưa ai lập phiếu xuất.",
		"dau": -1,
		"tk": "642",
	},
	{
		"ma": "mat",
		"ten": "Mất hàng",
		"mo": "Không giải thích được bằng ba lý do trên. Giám đốc duyệt.",
		"dau": -1,
		"tk": "1381",
	},
	{
		"ma": "quen_phieu_nhap",
		"ten": "Nhập quên lập phiếu",
		"mo": "Hàng đã về kho mà chưa ai lập phiếu nhập.",
		"dau": 1,
		"tk": "3381",
	},
	{
		"ma": "lech_don_vi",
		"ten": "Lệch đơn vị hoặc quy cách",
		"mo": "Đếm theo thùng mà sổ ghi theo gói, hoặc ngược lại.",
		"dau": 0,
		"tk": "632",
	},
	{
		"ma": "lech_dinh_luong",
		"ten": "Định lượng công thức sai",
		"mo": "Công thức trừ nhiều hoặc ít hơn thực tế bếp dùng.",
		"dau": 0,
		"tk": "632",
	},
]

LY_DO_CAN_DUYET = {"mat"}


def ly_do_hop(dau_lech):
	"""Nhung ly do dung chieu voi mot chenh lech."""
	if dau_lech > 0:
		return [x for x in LY_DO_LECH if x["dau"] >= 0]
	if dau_lech < 0:
		return [x for x in LY_DO_LECH if x["dau"] <= 0]
	return list(LY_DO_LECH)


def ly_do_theo_ma(ma):
	for x in LY_DO_LECH:
		if x["ma"] == str(ma or ""):
			return x
	return None


def soat_ly_do(dong):
	"""Dong nao co chenh lech ma chua khai ly do, hoac khai ly do nguoc chieu.

	`dong` la danh sach {"ma", "ten", "lech", "ly_do"}.
	"""
	thieu, nguoc = [], []
	for d in dong or []:
		lech = float((d or {}).get("lech") or 0)
		if abs(lech) <= EPS:
			continue
		ten = (d or {}).get("ten") or (d or {}).get("ma") or ""
		ly = str((d or {}).get("ly_do") or "").strip()
		if not ly:
			thieu.append(ten)
			continue
		x = ly_do_theo_ma(ly)
		if not x:
			thieu.append(ten)
		elif (lech > 0 and x["dau"] < 0) or (lech < 0 and x["dau"] > 0):
			nguoc.append("%s: %s" % (ten, x["ten"]))
	return {"thieu": thieu, "nguoc": nguoc}


def can_giam_doc_duyet(dong):
	"""Phieu nay co dong nao mang ly do phai giam doc duyet khong."""
	for d in dong or []:
		if str((d or {}).get("ly_do") or "") in LY_DO_CAN_DUYET:
			if abs(float((d or {}).get("lech") or 0)) > EPS:
				return 1
	return 0


def gom_theo_ly_do(dong):
	"""Gom chenh lech theo ly do, de bao cao cuoi thang doc mot cai la hieu."""
	ra = {}
	for d in dong or []:
		lech = float((d or {}).get("lech") or 0)
		if abs(lech) <= EPS:
			continue
		ly = str((d or {}).get("ly_do") or "") or "chua_khai"
		o = ra.setdefault(ly, {"so_dong": 0, "lech": 0.0, "tien": 0.0})
		o["so_dong"] += 1
		o["lech"] += lech
		o["tien"] += lech * float((d or {}).get("gia") or 0)
	return ra
