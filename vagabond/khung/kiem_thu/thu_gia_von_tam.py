# -*- coding: utf-8 -*-
"""Ca kiểm phép THUẦN của màn Giá vốn tạm tính (Issue #482).

Số liệu mẫu theo đúng hình dạng site thật 16/10/2026: 378 BOM đang chạy mà
chỉ 480/2.055 dòng có `bom_no`, nên phép cộng dồn PHẢI tự tra công thức mặc
định của mã. Mỗi ca ghi trong tên nó chặn đường lỗi nào.
"""

from vagabond import gia_von_tam as G
from vagabond.khung.kiem_thu import nen
from vagabond.khung.kiem_thu.nen import ca, dung, la

KHO = {
	"BOT": [{"actual_qty": 1000, "stock_value": 20000}],      # 20 đ/gram
	"DUONG": [{"actual_qty": 0, "stock_value": 0}],            # hết tồn, rơi xuống giá khai
	"BO": [{"actual_qty": 500, "stock_value": 100000}, {"actual_qty": 500, "stock_value": 200000}],  # 300 đ/gram
}
GIA_ITEM = {"DUONG": 25, "TRUNG": 3000}
GIA_NHAP = {"VANI": 900}


def _gia_la(ma):
	return G.gia_la(KHO.get(ma), GIA_ITEM.get(ma), GIA_NHAP.get(ma))


def _cay(bom_no_cot=None):
	"""Ba tầng: BANH <- KEM (BTP) <- SOT (BTP) <- lá. Dòng BTP để `bom_no`
	rỗng như phần lớn dòng trên site."""
	return {
		"BOM-BANH": {"so_ra": 1, "dong": [
			{"ma": "BOT", "sl": 100}, {"ma": "KEM", "sl": 200, "bom_no": bom_no_cot},
		]},
		"BOM-KEM": {"so_ra": 1000, "dong": [
			{"ma": "BO", "sl": 500}, {"ma": "SOT", "sl": 500},
		]},
		"BOM-SOT": {"so_ra": 2, "dong": [
			{"ma": "DUONG", "sl": 1000}, {"ma": "TRUNG", "sl": 2},
		]},
	}


MA_BOM = {"BANH": "BOM-BANH", "KEM": "BOM-KEM", "SOT": "BOM-SOT"}


@ca("gia von tam: dong BTP de bom_no rong van di xuong cong thuc mac dinh ba tang (chan doc gia ton kho cua BTP)")
def _ba_tang():
	k = G.cong_don(_cay(), MA_BOM, _gia_la)
	# SOT: (1000*25 + 2*3000) / 2 phần = 15500 mỗi phần
	la("gia SOT", k["BOM-SOT"]["gia"], 15500.0)
	# KEM: (500*300 + 500*15500) / 1000 = 7900
	la("gia KEM", k["BOM-KEM"]["gia"], 7900.0)
	# BANH: 100*20 + 200*7900 = 1.582.000
	la("gia BANH", k["BOM-BANH"]["gia"], 1582000.0)
	dung("khong co co vong", not any(v["vong"] for v in k.values()))


@ca("gia von tam: bom_no tro cong thuc da tat thi roi ve cong thuc mac dinh (chan doc cong thuc chet)")
def _bom_no_tat():
	k = G.cong_don(_cay(bom_no_cot="BOM-KEM-CU-DA-TAT"), MA_BOM, _gia_la)
	la("van ra dung gia", k["BOM-BANH"]["gia"], 1582000.0)
	cay = _cay(bom_no_cot="BOM-KEM-2")
	cay["BOM-KEM-2"] = {"so_ra": 1, "dong": [{"ma": "BOT", "sl": 1}]}
	k2 = G.cong_don(cay, MA_BOM, _gia_la)
	la("bom_no dang chay thi giu dung ban do", k2["BOM-BANH"]["gia"], 100 * 20 + 200 * 20.0)


@ca("gia von tam: dung so luong theo don vi kho, chia dung so ra cua cong thuc (chan dung qty dong nhap kg)")
def _don_vi_kho_va_so_ra():
	cay = {"BOM-X": {"so_ra": 4, "dong": [{"ma": "BOT", "sl": 1000}]}}  # dòng nhập 1 kg, kho tính 1000 gram
	k = G.cong_don(cay, {"X": "BOM-X"}, _gia_la)
	la("1000 gram x 20 / 4 phan", k["BOM-X"]["gia"], 5000.0)
	cay0 = {"BOM-Y": {"so_ra": 0, "dong": [{"ma": "BOT", "sl": 10}]}}
	k0 = G.cong_don(cay0, {"Y": "BOM-Y"}, _gia_la)
	dung("so ra 0 gan co, khong chia cho 0", k0["BOM-Y"]["so_ra_loi"] and k0["BOM-Y"]["gia"] == 200.0)


@ca("gia von tam: vong A -> B -> A gan co va dung lai, khong de quy vo tan (chan treo ca luot tinh)")
def _vong():
	cay = {
		"BOM-A": {"so_ra": 1, "dong": [{"ma": "B", "sl": 1}, {"ma": "BOT", "sl": 1}]},
		"BOM-B": {"so_ra": 1, "dong": [{"ma": "A", "sl": 1}]},
		"BOM-C": {"so_ra": 1, "dong": [{"ma": "BOT", "sl": 2}]},
	}
	k = G.cong_don(cay, {"A": "BOM-A", "B": "BOM-B", "C": "BOM-C"}, _gia_la)
	dung("A co co vong", k["BOM-A"]["vong"])
	dung("B co co vong", k["BOM-B"]["vong"])
	dung("C khong lien quan van dung", not k["BOM-C"]["vong"] and k["BOM-C"]["gia"] == 40.0)
	tu_tro = {"BOM-T": {"so_ra": 1, "dong": [{"ma": "T", "sl": 1}]}}
	dung("cong thuc tro vao chinh no cung la vong", G.cong_don(tu_tro, {"T": "BOM-T"}, _gia_la)["BOM-T"]["vong"])


@ca("gia von tam: la thieu gia o tang 3 don co len mon tang 1 (chan bao gia thap ma khong canh bao)")
def _thieu_don_len():
	cay = _cay()
	cay["BOM-SOT"]["dong"].append({"ma": "LA-BAC", "sl": 1})
	k = G.cong_don(cay, MA_BOM, _gia_la)
	la("tang 3", sorted(k["BOM-SOT"]["thieu"]), ["LA-BAC"])
	la("tang 1 cung biet", sorted(k["BOM-BANH"]["thieu"]), ["LA-BAC"])


@ca("gia von tam: thu tu nguon gia cua la: binh quan kho, roi gia khai mat hang, roi bang gia nhap, roi thieu")
def _nguon_gia():
	la("kho", _gia_la("BO"), (300.0, "Giá kho"))
	la("het ton roi xuong gia khai", _gia_la("DUONG"), (25.0, "Giá khai trên mặt hàng"))
	la("khong ton khong khai thi bang gia nhap", _gia_la("VANI"), (900.0, "Bảng giá nhập"))
	la("khong co gi", _gia_la("LA-BAC"), (0.0, "Thiếu giá"))
	la("ton am khong tinh vao binh quan", G.gia_la([{"actual_qty": -5, "stock_value": -50}, {"actual_qty": 10, "stock_value": 300}], 0, 0), (30.0, "Giá kho"))


@ca("gia von tam: gia de xuat lam tron LEN toi nghin, bien 0, 95, 96, gia von 0 (chan lam tron xuong)")
def _de_xuat():
	la("Roman 16 voi 25%", G.gia_de_xuat(250959, 25), 1004000)
	la("chia tron khong bi day len nghin sau", G.gia_de_xuat(250000, 25), 1000000)
	la("nhan 25,5 dang chuoi", G.gia_de_xuat(255000, "25.5"), 1000000)
	la("0%", G.gia_de_xuat(250959, 0), None)
	la("95% duoc", G.gia_de_xuat(95000, 95), 100000)
	la("96%", G.gia_de_xuat(250959, 96), None)
	la("gia von 0", G.gia_de_xuat(0, 25), None)
	la("chua dat ty le", G.gia_de_xuat(1000, None), None)


@ca("gia von tam: du tam nhanh trang thai, co ca giong Shiopan vuot gia ban")
def _trang_thai():
	T = G.trang_thai
	la("chua cong thuc", T(False, False, 0, 0, 0, 25), "chua_cong_thuc")
	la("vong", T(True, True, 2, 0, 65000, 25), "vong")
	la("thieu gia", T(True, False, 1, 379233, 65000, 25), "thieu_gia")
	la("Shiopan 379.233 / 65.000", T(True, False, 0, 379233, 65000, 25), "vuot_gia_ban")
	la("chua gia ban", T(True, False, 0, 10000, 0, 25), "chua_gia_ban")
	la("Roman 16 28,5% > 25%", T(True, False, 0, 250959, 880000, 25), "cao_hon_muc_tieu")
	la("trong muc tieu", T(True, False, 0, 23885, 160000, 25), "dat")
	la("chua dat ty le", T(True, False, 0, 23885, 160000, None), "chua_dat_ty_le")


@ca("gia von tam: lam sach ty le muc tieu: o trong la bo, 25,5 duoc, ngoai 1..95 va nhom la bi chan")
def _chuan_ty_le():
	la("lam sach", G.chuan_ty_le({"Bánh lạnh": "25,5", "Bánh khô": "", "Bánh ổ sinh nhật": 30}),
		{"Bánh lạnh": 25.5, "Bánh ổ sinh nhật": 30.0})
	la("nhan chuoi json", G.chuan_ty_le('{"Bánh nướng": 20}'), {"Bánh nướng": 20.0})
	for sai in ({"Bánh lạnh": 0}, {"Bánh lạnh": 96}, {"Bánh lạnh": "abc"}, {"Nguyên liệu": 20}):
		try:
			G.chuan_ty_le(sai)
			raise AssertionError("phai chan %r" % sai)
		except ValueError:
			pass


def _dong(**kw):
	d = {"ma": "BAWC00067", "ten": "Roman 16", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái", "gia_von": 250959,
		"gia_ban": 880000, "ty_le_muc_tieu": 25, "gia_de_xuat": 1004000, "trang_thai": "cao_hon_muc_tieu"}
	d.update(kw)
	return d


@ca("gia von tam: chot chi luu mon du gia, dem dung ly do bo qua, ghi chu dung mau, dung ngay (chan luu gia thieu)")
def _dong_bang_gia():
	luu, bo = G.dong_bang_gia([
		_dong(),
		_dong(ma="X1", trang_thai="thieu_gia"),
		_dong(ma="X2", trang_thai="thieu_gia"),
		_dong(ma="X3", trang_thai="vong"),
		_dong(ma="X4", trang_thai="chua_dat_ty_le", gia_von=0, ty_le_muc_tieu=None, gia_de_xuat=None),
		_dong(ma="X5", trang_thai="chua_gia_ban", gia_ban=0, gia_de_xuat=None, ty_le_muc_tieu=None),
	], "2026-10-16")
	la("ma duoc luu", [p["item_code"] for p in luu], ["BAWC00067", "X5"])
	la("bo qua", bo, {"Thiếu giá nguyên liệu": 2, "Công thức vòng lặp": 1, "Giá vốn bằng 0": 1})
	la("ngay", luu[0]["valid_from"], "2026-10-16")
	la("don vi kho", luu[0]["uom"], "Cái")
	la("ghi chu", luu[0]["note"],
		"Tỷ lệ mục tiêu 25%. Giá bán đề xuất 1.004.000. Giá bán lúc chốt 880.000. Chỉ gồm nguyên liệu.")
	la("ghi chu khi chua co gi", luu[1]["note"], "Chưa đặt tỷ lệ mục tiêu. Chưa có giá bán. Chỉ gồm nguyên liệu.")


@ca("gia von tam: dung bang: mon chua cong thuc tach rieng, mon can xu len dau nhom, trung vi chi tinh mon du gia")
def _dung_bang():
	ban = [
		{"ma": "BANH", "ten": "Bánh B", "nhom": "Bánh lạnh"},
		{"ma": "SHIO", "ten": "Shiopan", "nhom": "Bánh lạnh"},
		{"ma": "MOI", "ten": "Bánh mới", "nhom": "Bánh lạnh"},
		{"ma": "THIEU", "ten": "Bánh thiếu", "nhom": "Bánh khô"},
	]
	ket = {
		"B1": {"gia": 20000, "thieu": set(), "vong": False},
		"B2": {"gia": 379233, "thieu": set(), "vong": False},
		"B3": {"gia": 5000, "thieu": {"LA-BAC", "BTP-1", "BTP-2"}, "vong": False},
	}
	b = G.dung_bang(ban, {"BANH": "B1", "SHIO": "B2", "THIEU": "B3"}, ket,
		{"BANH": 160000, "SHIO": 65000, "THIEU": 50000}, {"BANH": ("2026-10-12", 19500)},
		{"Bánh lạnh": 15}, {"LA-BAC": "Lá bạc"})
	la("thu tu", [d["ma"] for d in b["dong"]], ["SHIO", "BANH", "THIEU"])
	la("chua cong thuc", b["chua_cong_thuc"], {"so": 1, "ten": ["Bánh mới"]})
	shio = b["dong"][0]
	la("Shiopan", (shio["trang_thai"], shio["ty_le"]), ("vuot_gia_ban", 583.4))
	la("lan truoc", b["dong"][1]["lan_truoc"], {"ngay": "2026-10-12", "gia": 19500.0, "chenh_pct": 2.6})
	thieu = b["dong"][2]
	la("ten nguyen lieu thieu", (thieu["thieu_so"], thieu["thieu_ten"]), (3, ["BTP-1", "BTP-2", "Lá bạc"]))
	dung("mon thieu gia khong co gia de xuat", thieu["gia_de_xuat"] is None)
	nhom = {n["ten"]: n for n in b["nhom"]}
	la("nhom banh lanh", (nhom["Bánh lạnh"]["so_mon"], nhom["Bánh lạnh"]["chua_cong_thuc"], nhom["Bánh lạnh"]["nhan"]), (2, 1, "Bánh lạnh"))
	la("trung vi chi gom mon du gia", nhom["Bánh lạnh"]["trung_vi"], round((583.4 + 12.5) / 2, 1))


@ca("gia von tam: danh sach nhom ban trung voi xuat_phuc_vu_ban, nhan chip toi da 16 ky tu")
def _nhom():
	from vagabond import xuat_phuc_vu_ban as X
	la("cung tap nhom", sorted(G.NHOM_BAN), sorted(X.NGOAI_PHAM_VI[0]["nhom"]))
	dung("nhan chip <= 16", all(len(G.nhan_nhom(n)) <= 16 for n in G.NHOM_BAN))


@ca("gia von tam: loi vao Desk tro dung duong man GVT, khong nhan doi khi chay lai")
def _sidebar():
	from vagabond import duong_app as D
	la("duong", G.muc_sidebar()["url"], "/" + D.slugify(dict((k, t) for k, t, _s in D.MAN)["GVT"]))
	import frappe

	class SB(object):
		def __init__(self):
			self.items, self.luu = [], 0
			self.flags = type("F", (), {})()

		def get(self, k):
			return getattr(self, k)

		def append(self, k, v):
			self.items.append(v)

		def save(self):
			self.luu += 1

	sb = {"Invoicing": SB(), "Manufacturing": SB()}
	cu = (getattr(frappe, "db", None), getattr(frappe, "get_doc", None))
	frappe.db = type("DB", (), {"exists": staticmethod(lambda dt, ten: ten in sb)})()
	frappe.get_doc = lambda dt, ten: sb[ten]
	try:
		la("lan dau them hai", G.dung_sidebar(), 2)
		la("lan hai khong them", G.dung_sidebar(), 0)
		la("moi sidebar mot muc", [len(sb[k].items) for k in ("Invoicing", "Manufacturing")], [1, 1])
	finally:
		frappe.db, frappe.get_doc = cu


class _Dong(dict):
	__getattr__ = dict.get


def _frappe_gia(roles=("Accounts Manager",), gia_ban=None, gia_nhap=None):
	"""Frappe giả đủ cho _bang(): trả dữ liệu theo doctype và bộ lọc, ghi lại
	mọi lần đọc để chốt "đọc theo lô, không hỏi từng mã"."""
	import frappe
	doc = []
	du = {
		"BOM": [_Dong(name="B-BANH", item="BANH", quantity=1, is_default=1),
			_Dong(name="B-KEM", item="KEM", quantity=1000, is_default=1)],
		# Dòng nhập theo Kg, kho tính Gram: qty 0,2 nhưng stock_qty 200.
		"BOM Item": [_Dong(parent="B-BANH", item_code="BOT", item_name="Bột", qty=0.1, stock_qty=100, stock_uom="Gram", uom="Kg", bom_no=None),
			_Dong(parent="B-BANH", item_code="KEM", item_name="Kem", qty=0.2, stock_qty=200, stock_uom="Gram", uom="Kg", bom_no=None),
			_Dong(parent="B-KEM", item_code="BO", item_name="Bơ", qty=1, stock_qty=1000, stock_uom="Gram", uom="Kg", bom_no=None)],
		"Bin": [_Dong(item_code="BOT", actual_qty=1000, stock_value=20000), _Dong(item_code="BO", actual_qty=1000, stock_value=300000)],
	}

	def get_all(dt, filters=None, fields=None, limit_page_length=None, order_by=None):
		doc.append(dt)
		f = filters or {}
		if dt == "Item" and "item_group" in f:
			return [_Dong(name="BANH", item_name="Bánh B", item_group="Bánh lạnh", stock_uom="Cái", image=None),
				_Dong(name="MOI", item_name="Bánh mới", item_group="Bánh lạnh", stock_uom="Cái", image=None)]
		if dt == "Item":
			return [_Dong(name=n, item_name=n, stock_uom="Gram", valuation_rate=0) for n in f["name"][1]]
		if dt == "Item Price":
			if f.get("price_list") == "Standard Selling":
				return list(gia_ban or [_Dong(item_code="BANH", price_list_rate=310000, uom="Cái")])
			if f.get("price_list") == "Bảng giá nhập":
				return list(gia_nhap or [])
			return []
		return list(du.get(dt, []))

	cu = {k: getattr(frappe, k, None) for k in ("get_all", "db", "defaults", "get_roles")}
	frappe.get_all = get_all
	frappe.db = type("DB", (), {"get_single_value": staticmethod(lambda *a: "Standard Selling")})()
	frappe.defaults = type("DF", (), {"get_global_default": staticmethod(lambda k: '{"Bánh lạnh": 20}')})()
	frappe.get_roles = lambda *a, **k: list(roles)
	return cu, doc


def _tra(cu):
	import frappe
	for k, v in cu.items():
		setattr(frappe, k, v)


@ca("gia von tam: doc site: dong BOM nhap theo Kg van tinh theo stock_qty don vi kho, doc theo lo (chan dung qty)")
def _doc_site():
	cu, doc = _frappe_gia()
	try:
		bang, ty_le = G._bang()
	finally:
		_tra(cu)
	banh = [d for d in bang["dong"] if d["ma"] == "BANH"][0]
	# KEM = 1000 gram x 300 / 1000 = 300 mỗi gram; BANH = 100 x 20 + 200 x 300 = 62.000
	la("gia von", banh["gia_von"], 62000)
	la("ty le va trang thai", (banh["ty_le"], banh["trang_thai"]), (20.0, "dat"))
	la("de xuat 62000 / 20%", banh["gia_de_xuat"], 310000)
	la("mon chua cong thuc", bang["chua_cong_thuc"]["so"], 1)
	la("so lan doc moi doctype, khong hoi tung ma", sorted(set(doc)), ["BOM", "BOM Item", "Bin", "Item", "Item Price"])
	dung("so lan doc gioi han", len(doc) <= 9)


@ca("gia von tam: chot va dat ty le chan tai khoan chi duoc xem, truoc khi cham du lieu (chan bo cong quyen)")
def _quyen_chot():
	cu, doc = _frappe_gia(roles=("Accounts User",))
	try:
		for ham, ts in ((G.chot, ()), (G.luu_ty_le, ('{"Bánh lạnh": 20}',))):
			try:
				ham(*ts)
				raise AssertionError("%s phai bi chan" % ham.__name__)
			except AssertionError:
				raise
			except Exception as e:
				dung("cau quyen tieng Viet", "không có quyền" in str(e))
		la("chua doc gi", doc, [])
	finally:
		_tra(cu)


@ca("gia von tam: Codex #483 v1: mon co nhieu dong gia ban (het han, gia rieng khach, tuong lai) chi lay dong dang ap dung (chan so sanh voi gia la)")
def _gia_ap_dung_site():
	hom = str(nen.HOM_NAY)
	ban = [
		_Dong(item_code="BANH", price_list_rate=310000, uom="Cái", valid_from="2026-08-01", valid_upto=None, customer=None, supplier=None, batch_no=None),
		_Dong(item_code="BANH", price_list_rate=999000, uom="Cái", valid_from="2025-01-01", valid_upto="2025-12-31", customer=None, supplier=None, batch_no=None),
		_Dong(item_code="BANH", price_list_rate=50000, uom="Cái", valid_from=None, valid_upto=None, customer="Khách sỉ A", supplier=None, batch_no=None),
		_Dong(item_code="BANH", price_list_rate=777000, uom="Cái", valid_from="2099-01-01", valid_upto=None, customer=None, supplier=None, batch_no=None),
	]
	cu, doc = _frappe_gia(gia_ban=ban)
	try:
		bang, _t = G._bang()
	finally:
		_tra(cu)
	banh = [d for d in bang["dong"] if d["ma"] == "BANH"][0]
	la("gia ban dang ap dung hom " + hom, banh["gia_ban"], 310000.0)


@ca("gia von tam: Codex #483 v1: chon gia ap dung: bo khach/NCC/lo, het han, tuong lai, sai don vi; uu tien dung don vi roi valid_from moi nhat")
def _chon_gia_ap_dung():
	C = G.chon_gia_ap_dung
	d = lambda gia, **kw: dict({"price_list_rate": gia, "uom": "Cái", "valid_from": None, "valid_upto": None}, **kw)
	la("rong", C([], "Cái", "2026-10-16"), None)
	la("chi dong rieng khach, NCC, lo thi coi nhu khong co",
		C([d(1, customer="K"), d(2, supplier="N"), d(3, batch_no="L")], "Cái", "2026-10-16"), None)
	la("bo het han va tuong lai", C([d(1, valid_upto="2026-10-15"), d(2, valid_from="2026-10-17"), d(3)], "Cái", "2026-10-16"), 3.0)
	la("ngay bien van ap dung", C([d(5, valid_from="2026-10-16", valid_upto="2026-10-16")], "Cái", "2026-10-16"), 5.0)
	la("valid_from moi nhat thang", C([d(1, valid_from="2026-01-01"), d(2, valid_from="2026-09-01"), d(3)], "Cái", "2026-10-16"), 2.0)
	la("sai don vi kho bi bo", C([d(9, uom="Hộp"), d(4)], "Cái", "2026-10-16"), 4.0)
	la("dung don vi xep truoc dong khong ghi don vi", C([d(7, uom=None, valid_from="2026-10-01"), d(6, valid_from="2026-01-01")], "Cái", "2026-10-16"), 6.0)


@ca("gia von tam: Codex #483 v1: bang gia nhap cung chi lay dong dang ap dung khi nguyen lieu khong co gia kho")
def _gia_nhap_ap_dung():
	nhap = [
		_Dong(item_code="BOT", price_list_rate=99, uom="Gram", valid_from="2025-01-01", valid_upto="2025-12-31", customer=None, supplier=None, batch_no=None),
		_Dong(item_code="BOT", price_list_rate=20, uom="Gram", valid_from="2026-08-01", valid_upto=None, customer=None, supplier=None, batch_no=None),
		_Dong(item_code="BOT", price_list_rate=5, uom="Gram", valid_from=None, valid_upto=None, customer=None, supplier="NCC rẻ", batch_no=None),
	]
	cu, doc = _frappe_gia(gia_nhap=nhap)
	import frappe
	goc = frappe.get_all

	def bo_ton(dt, **kw):
		return [] if dt == "Bin" else goc(dt, **kw)
	frappe.get_all = bo_ton
	try:
		bang, _t = G._bang()
	finally:
		_tra(cu)
	banh = [d for d in bang["dong"] if d["ma"] == "BANH"][0]
	# BOT 100 gram x 20 (bảng giá nhập đang áp dụng); BO và KEM không còn giá nên thiếu.
	la("thieu dung BO", banh["thieu_so"], 1)
	la("gia von chi tinh phan BOT", banh["gia_von"], 2000)
