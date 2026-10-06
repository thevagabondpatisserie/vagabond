# -*- coding: utf-8 -*-
"""v582: gói chức vụ theo phân hệ, một người giữ NHIỀU gói, quyền cộng dồn.

Anh Việt chốt 06/10/2026 (docs/quyen-theo-phan-he.md, tám điểm):
  1. Mọi người quầy được tạo đơn bán.
  2. Sales giữ quyền sửa bảng giá và khách hàng.
  3. Khuyến mãi cho mọi Sales và Quản lý cửa hàng.
  4. Dễ giữ quyền quản lý người dùng (nên phải giữ được HAI gói).
  5. Khải chung gói Kế toán.
  6. Bỏ phần thừa.
  7. Kế toán toàn quyền kho và sản xuất.
  8. Giám đốc toàn quyền nghiệp vụ.

Các ca dưới chạy THẬT doan_cac_goi, doc_cac_goi, dat_goi, danh_sach,
danh_sach_goi, chi_tiet trên lớp Frappe giả của thu_quan_ly_nguoi_dung.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_quan_ly_nguoi_dung import (  # noqa: E402
	ND, _Canh, _Site, _UserGia, _nguoi, nd,
)

# Site giả: mọi vai của mọi gói đều có thật, thêm một vai ngoài gói.
CO_THAT = set(nd.VAI_QUAN_LY) | {"Quầy Bar", "All", "Customer"}
G = nd.GOI_THEO_KEY


def _vai(*k):
	ra = set()
	for x in k:
		ra |= set(G[x]["vai"])
	return ra


def _khoa(ds):
	return [g["k"] for g in ds]


# ------------------------------------------------------------- tám điểm đã chốt

@ca("v582 diem 1-3: quay tao don ban, Sales va QLCH co khuyen mai, Sales sua bang gia")
def _diem_1_3():
	dung("quay co Sales User", "Sales User" in G["quay"]["vai"])
	for k in ("sales", "qlch"):
		dung("%s co khuyen mai" % k, "VGB - Quản lý khuyến mãi" in G[k]["vai"])
		dung("%s co Sales Manager (bang gia, khach)" % k, "Sales Manager" in G[k]["vai"])
	dung("quay KHONG co khuyen mai", "VGB - Quản lý khuyến mãi" not in G["quay"]["vai"])


@ca("v582 diem 7: ke toan toan quyen kho va san xuat")
def _diem_7():
	for v in ("Stock Manager", "Stock User", "Manufacturing Manager", "Manufacturing User"):
		dung("ke toan co %s" % v, v in G["ketoan"]["vai"])


@ca("v582 diem 8: giam doc = hop moi goi nghiep vu, KHONG co quan tri he thong")
def _diem_8():
	gd = set(G["giamdoc"]["vai"])
	for g in nd.GOI:
		if g["k"] in ("giamdoc", "chucongty", "shipper"):
			continue
		thieu = set(g["vai"]) - gd
		la("giam doc du vai goi %s" % g["k"], sorted(thieu), [])
	dung("khong System Manager", "System Manager" not in gd)
	dung("khong Shipper", "Shipper" not in gd)
	dung("co Quan ly nguoi dung", nd.VAI_QLND in gd)


@ca("v582: goi cu salesql va ketoantruong da bo, khoa la thi bao ro")
def _bo_goi_cu():
	dung("khong con salesql", "salesql" not in G)
	dung("khong con ketoantruong", "ketoantruong" not in G)
	nem("khoa la", lambda: nd.doc_cac_goi("salesql"), ValueError)


# ------------------------------------------------------------- đoán gói (phép thuần)

@ca("v582: De giu QLCH + Quan ly nguoi dung thi doan ra DU hai goi")
def _doan_hai_goi():
	ds = nd.doan_cac_goi(_vai("qlch", "nhansu"), CO_THAT)
	la("hai goi, goi nang truoc", _khoa(ds), ["nhansu", "qlch"])
	la("ten noi bang dau cong", nd.ten_cac_goi(ds), "Quản lý người dùng + Quản lý cửa hàng")


@ca("v582: goi nam tron trong goi khac thi KHONG hien them (Quay trong Sales trong QLCH)")
def _doan_bo_goi_con():
	la("qlch", _khoa(nd.doan_cac_goi(_vai("qlch"), CO_THAT)), ["qlch"])
	la("sales", _khoa(nd.doan_cac_goi(_vai("sales"), CO_THAT)), ["sales"])
	la("bep ql", _khoa(nd.doan_cac_goi(_vai("bepql"), CO_THAT)), ["bepql"])
	la("giam doc chi la mot goi", _khoa(nd.doan_cac_goi(_vai("giamdoc"), CO_THAT)), ["giamdoc"])


@ca("v582: thieu mot vai cua goi thi KHONG tinh la giu goi do")
def _doan_thieu_vai():
	vai = _vai("sales") - {"VGB - Quản lý khuyến mãi"}
	la("lui ve quay", _khoa(nd.doan_cac_goi(vai, CO_THAT)), ["quay"])
	la("khong vai nao", _khoa(nd.doan_cac_goi(set(), CO_THAT)), [])


@ca("v582: vai ngoai goi (Quay Bar) khong lam lech doan goi va hien la quyen rieng")
def _doan_vai_ngoai():
	vai = _vai("quay") | {"Quầy Bar", "Stock User"}
	ds = nd.doan_cac_goi(vai, CO_THAT)
	la("van la quay", _khoa(ds), ["quay"])
	la("Stock User la quyen rieng, Quay Bar ngoai pham vi", nd._thua_so_voi_goi(vai, ds), ["Stock User"])


@ca("v582: goi co vai chua tao tren site thi doan theo vai co that")
def _doan_vai_chua_co():
	co = CO_THAT - {"VGB - Quản lý khuyến mãi"}
	vai = _vai("sales") - {"VGB - Quản lý khuyến mãi"}
	la("van khop sales", _khoa(nd.doan_cac_goi(vai, co)), ["sales"])


@ca("v582: _thua_so_voi_goi tinh tren HOP cac goi, khong chi goi dau")
def _thua_tren_hop():
	vai = _vai("qlch", "nhansu")
	ds = nd.doan_cac_goi(vai, CO_THAT)
	la("khong thua gi", nd._thua_so_voi_goi(vai, ds), [])
	la("chi goi dau thi thua QLND", nd._thua_so_voi_goi(vai, ds[1]), [nd.VAI_QLND])


# ------------------------------------------------------------- đọc tham số gói

@ca("v582: doc_cac_goi nhan chuoi phay, JSON, danh sach; gop trung, giu thu tu")
def _doc_tham_so():
	la("chuoi", _khoa(nd.doc_cac_goi("qlch,nhansu")), ["qlch", "nhansu"])
	la("co khoang trang", _khoa(nd.doc_cac_goi(" qlch , nhansu ,")), ["qlch", "nhansu"])
	la("json", _khoa(nd.doc_cac_goi('["ketoan","qlch"]')), ["ketoan", "qlch"])
	la("danh sach", _khoa(nd.doc_cac_goi(["sales", "sales"])), ["sales"])
	la("mot khoa nhu cu", _khoa(nd.doc_cac_goi("sales")), ["sales"])
	la("rong", nd.doc_cac_goi(""), [])


# ------------------------------------------------------------- ghi gói thật

class _Kho(object):
	"""Thay tam noi luu goi da chon (Mac dinh cua nguoi dung) bang mot dict."""

	def __init__(self, ban_dau=None):
		self.luu = dict(ban_dau or {})

	def __enter__(self):
		self.cu = (nd._goi_da_luu, nd._luu_goi)
		nd._goi_da_luu = lambda email: list(self.luu.get(email, []))
		nd._luu_goi = lambda email, cac: self.luu.__setitem__(email, [g["k"] for g in cac])
		return self

	def __exit__(self, *a):
		nd._goi_da_luu, nd._luu_goi = self.cu
		return False


def _dat(email, vai_dau, goi, kho=None, doc=None):
	doc = doc or _UserGia(email, set(vai_dau))
	cu_ton = nd.frappe.db.exists
	cu_vet = nd._ghi_vet
	cu_kiem = nd._kiem
	nd.frappe.db.exists = lambda *a, **k: True
	nd._ghi_vet = lambda *a, **k: None
	nd._kiem = lambda *a, **k: None
	try:
		with _Canh(doc, CO_THAT):
			if kho is not None:
				kq = nd.dat_goi(email, goi)
			else:
				with _Kho():
					kq = nd.dat_goi(email, goi)
	finally:
		nd.frappe.db.exists = cu_ton
		nd._ghi_vet = cu_vet
		nd._kiem = cu_kiem
	return doc, kq


@ca("v582: dat_goi hai goi thi vai = HOP hai goi, vai ngoai goi giu nguyen")
def _dat_hai_goi():
	doc, kq = _dat("de@vgb", _vai("quay") | {"Quầy Bar"}, "qlch,nhansu")
	la("vai sau", doc.vai(), _vai("qlch", "nhansu") | {"Quầy Bar"})
	la("ten goi", kq["goi_ten"], "Quản lý cửa hàng + Quản lý người dùng")
	la("cac goi", kq["cac_goi"], ["qlch", "nhansu"])


@ca("v582: bo bot mot goi thi go DUNG vai cua goi do, giu vai goi con lai")
def _dat_bot_goi():
	doc, kq = _dat("de@vgb", _vai("qlch", "nhansu"), "qlch")
	la("vai sau", doc.vai(), _vai("qlch"))
	la("go dung QLND", kq["go"], [nd.VAI_QLND])


@ca("v582: dat_goi khoa la hoac rong thi bao loi, khong dong vao vai")
def _dat_khoa_la():
	nem("khoa la", lambda: _dat("x@vgb", _vai("quay"), "quay,abc"))
	nem("rong", lambda: _dat("x@vgb", _vai("quay"), ""))


# ------------------------------------------------------------- hai màn danh sách

def _site_hai_goi():
	users = [_nguoi("de@vgb"), _nguoi("loan@vgb"), _nguoi("dung@vgb"), _nguoi("moi@vgb")]
	vai = {
		"de@vgb": _vai("qlch", "nhansu"),
		"loan@vgb": _vai("qlch"),
		"dung@vgb": _vai("ketoan"),
		"moi@vgb": set(),
	}
	return users, vai


@ca("v582: nguoi giu hai goi hien o CA HAI goi tren man danh sach va man goi")
def _hai_man_hai_goi():
	users, vai = _site_hai_goi()
	with _Site(users, vai, CO_THAT), _Kho():
		ds = nd.danh_sach()
		loc_ns = nd.danh_sach(goi="nhansu")
		loc_ch = nd.danh_sach(goi="qlch")
		gg = nd.danh_sach_goi()
	de = [r for r in ds["rows"] if r["email"] == "de@vgb"][0]
	la("cac goi cua De", de["cac_goi"], ["nhansu", "qlch"])
	la("loc nhan su", [r["email"] for r in loc_ns["rows"]], ["de@vgb"])
	la("loc qlch", sorted(r["email"] for r in loc_ch["rows"]), ["de@vgb", "loan@vgb"])
	la("dem goi qlch", ds["dem_goi"].get("qlch"), 2)
	la("dem goi nhansu", ds["dem_goi"].get("nhansu"), 1)
	la("dem chua xep", ds["dem_goi"].get(""), 1)
	so = {g["k"]: g["so_nguoi"] for g in gg["goi"]}
	la("man goi dem qlch", so["qlch"], 2)
	la("man goi dem nhansu", so["nhansu"], 1)
	la("man goi chua xep", gg["chua_xep"], 1)
	la("hai man cung so qlch", so["qlch"], ds["dem_goi"].get("qlch"))
	la("De khong co quyen rieng", de["vai_thua"], [])


@ca("v582: chi_tiet tra cac_goi va gom viec lam duoc cua moi goi, khong trung")
def _chi_tiet_hai_goi():
	users, vai = _site_hai_goi()
	with _Site(users, vai, CO_THAT), _Kho():
		cu = nd.frappe.db.get_value
		nd.frappe.db.get_value = lambda *a, **k: nd.frappe._dict(
			name="de@vgb", full_name="Dễ", first_name="", last_name="", enabled=1,
			last_active=None, mobile_no="", phone="", creation=None, user_type="System User")
		try:
			ct = nd.chi_tiet("de@vgb")
		finally:
			nd.frappe.db.get_value = cu
	la("cac goi", ct["cac_goi"], ["nhansu", "qlch"])
	mong = list(G["nhansu"]["lam_duoc"]) + list(G["qlch"]["lam_duoc"])
	la("viec lam duoc", ct["lam_duoc"], mong)
	la("khong thua", ct["vai_thua"], [])


# ------------------------------------------------- Codex #449 P1: gói "ghép"


def _vai_quay_mua():
	return _vai("quay", "muahang")


@ca("Codex #449 P1: Quay + Thu mua du tron vai goi Kho (dung tien de cua finding)")
def _p1_tien_de():
	dung("kho nam tron trong hop quay + thu mua", set(G["kho"]["vai"]) <= _vai_quay_mua())


@ca("Codex #449 P1: chua luu goi thi doan BO NHO NHAT, khong moc them Kho")
def _p1_doan_khong_luu():
	la("chi hai goi", _khoa(nd.doan_cac_goi(_vai_quay_mua(), CO_THAT)), ["muahang", "quay"])


@ca("Codex #449 P1: da luu goi thi chi tra dung goi da chon con du vai")
def _p1_doan_da_luu():
	la("dung hai goi da chon", _khoa(nd.doan_cac_goi(_vai_quay_mua(), CO_THAT, ["quay", "muahang"])),
		["muahang", "quay"])
	# Chon Quay + Sales thi giu ca hai, du Quay nam trong Sales: do la lua chon that.
	la("giu nguyen lua chon", _khoa(nd.doan_cac_goi(_vai("sales"), CO_THAT, ["quay", "sales"])),
		["sales", "quay"])
	# Ai do go mot vai cua Thu mua tren Desk: goi do roi ra, khong doan them.
	vai = _vai_quay_mua() - {"Thu mua"}
	la("thu mua roi ra", _khoa(nd.doan_cac_goi(vai, CO_THAT, ["quay", "muahang"])), ["quay"])
	# Moi goi da luu deu mat vai: quay ve doan tu bo vai.
	la("doan lai", _khoa(nd.doan_cac_goi(_vai("sales"), CO_THAT, ["ketoan"])), ["sales"])


@ca("Codex #449 P1: chuoi thao tac that - xep Quay + Thu mua, mo hop, bo Thu mua, Luu: mat quyen kho")
def _p1_chuoi_that():
	email = "uyen@vgb"
	doc = _UserGia(email, set())
	with _Kho() as kho:
		_dat(email, set(), "quay,muahang", kho=kho, doc=doc)
		la("da luu hai goi", kho.luu[email], ["quay", "muahang"])
		# Hop doi goi chon san theo chi_tiet: doc dung nhu man hinh.
		dang = nd.doan_cac_goi(doc.vai(), CO_THAT, nd._goi_da_luu(email))
		la("hop chon san dung hai goi, khong co Kho", _khoa(dang), ["muahang", "quay"])
		chon = [k for k in _khoa(dang) if k != "muahang"]
		_dat(email, set(), ",".join(chon), kho=kho, doc=doc)
	la("vai sau = dung goi Quay", doc.vai(), _vai("quay"))
	for v in ("Stock Manager", "Stock User", "Item Manager"):
		dung("da go %s" % v, v not in doc.vai())


@ca("Codex #449 P1: moi tai khoan cung luu dung goi da chon")
def _p1_moi_luu():
	src = ND[ND.find("def moi("):]
	src = src[:src.find("\ndef ", 10)]
	dung("moi goi _luu_goi", "_luu_goi(email, cac)" in src)


# ------------------------------------------- Codex #449 vong 2 P1: loi doc kho luu

@ca("Codex #449 vong 2 P1: doc goi da luu hong thi NEM, khong coi nhu chua luu")
def _p1v2_khong_nuot():
	import types
	cu = getattr(nd.frappe, "defaults", None)

	def _hong(*a, **k):
		raise RuntimeError("DefaultValue khoa bang")

	nd.frappe.defaults = types.SimpleNamespace(get_user_default=_hong, set_user_default=_hong)
	try:
		nem("doc hong phai nem", lambda: nd._goi_da_luu("de@vgb"), RuntimeError)
	finally:
		if cu is None:
			del nd.frappe.defaults
		else:
			nd.frappe.defaults = cu


@ca("Codex #449 vong 2 P1: doc goi da luu binh thuong tra dung khoa")
def _p1v2_doc_dung():
	import types
	cu = getattr(nd.frappe, "defaults", None)
	nd.frappe.defaults = types.SimpleNamespace(
		get_user_default=lambda k, u: " qlch , nhansu,abc,qlch" if k == nd.KHOA_GOI_DA_LUU else None)
	try:
		la("khoa sach, bo khoa la va trung", nd._goi_da_luu("de@vgb"), ["qlch", "nhansu"])
	finally:
		if cu is None:
			del nd.frappe.defaults
		else:
			nd.frappe.defaults = cu
	la("rong", nd.doc_khoa_da_luu(None), [])
