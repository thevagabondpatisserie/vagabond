# -*- coding: utf-8 -*-
"""Ca kiểm phép THUẦN của màn Giá vốn tạm tính (Issue #482).

Số liệu mẫu theo đúng hình dạng site thật 16/10/2026: 378 BOM đang chạy mà
chỉ 480/2.055 dòng có `bom_no`, nên phép cộng dồn PHẢI tự tra công thức mặc
định của mã. Mỗi ca ghi trong tên nó chặn đường lỗi nào.
"""

import json

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


@ca("gia von tam: v600 gia de xuat = gia von NHAN he so, lam tron LEN toi nghin; bien 1, 20, 20,5, gia von 0 (chan lam tron xuong, chan chia nham)")
def _de_xuat():
	la("Roman 16 voi x4", G.gia_de_xuat(250959, 4), 1004000)
	la("nhan tron khong bi day len nghin sau", G.gia_de_xuat(250000, 4), 1000000)
	la("nhan 3,5 dang chuoi co dau phay", G.gia_de_xuat(100001, "3,5"), 351000)
	la("x1 khong phai muc tieu", G.gia_de_xuat(250959, 1), None)
	la("x20 duoc", G.gia_de_xuat(5000, 20), 100000)
	la("x20,5 qua tay", G.gia_de_xuat(5000, 20.5), None)
	la("gia von 0", G.gia_de_xuat(0, 4), None)
	la("chua dat he so", G.gia_de_xuat(1000, None), None)


@ca("gia von tam: v600 he so hien thi la gia ban / gia von mot so le, % gia von di kem (anh Viet: lai so lan)")
def _he_so_hien():
	la("BOHOL anh chup", (G.he_so_hien(174575, 1060000), G.ty_le_hien(174575, 1060000)), (6.1, 16.5))
	la("Epi 12", G.he_so_hien(52278, 600000), 11.5)
	la("thieu gia ban", G.he_so_hien(1000, 0), None)
	la("gia von 0", G.he_so_hien(0, 1000), None)


@ca("gia von tam: du tam nhanh trang thai, co ca giong Shiopan vuot gia ban, so bang ty so that khong so so da lam tron")
def _trang_thai():
	T = G.trang_thai
	la("chua cong thuc", T(False, False, 0, 0, 0, 4), "chua_cong_thuc")
	la("vong", T(True, True, 2, 0, 65000, 4), "vong")
	la("thieu gia", T(True, False, 1, 379233, 65000, 4), "thieu_gia")
	la("Shiopan 379.233 / 65.000", T(True, False, 0, 379233, 65000, 4), "vuot_gia_ban")
	la("chua gia ban", T(True, False, 0, 10000, 0, 4), "chua_gia_ban")
	la("Roman 16 x3,5 < x4", T(True, False, 0, 250959, 880000, 4), "duoi_muc_tieu")
	la("x4,96 chua dat x5 du lam tron ra 5,0", T(True, False, 0, 100000, 496000, 5), "duoi_muc_tieu")
	la("dung bang x5 la dat", T(True, False, 0, 100000, 500000, 5), "dat")
	la("vuot muc tieu", T(True, False, 0, 23885, 160000, 4), "dat")
	la("chua dat he so", T(True, False, 0, 23885, 160000, None), "chua_dat_muc_tieu")


@ca("gia von tam: lam sach he so muc tieu: o trong la bo, 5,5 duoc, khong lon hon 1 hoac qua 20 va nhom la bi chan")
def _chuan_he_so():
	la("lam sach", G.chuan_he_so({"Bánh lạnh": "5,5", "Bánh khô": "", "Bánh ổ sinh nhật": 4}),
		{"Bánh lạnh": 5.5, "Bánh ổ sinh nhật": 4.0})
	la("nhan chuoi json", G.chuan_he_so('{"Bánh nướng": 6}'), {"Bánh nướng": 6.0})
	for sai in ({"Bánh lạnh": 1}, {"Bánh lạnh": 0.5}, {"Bánh lạnh": 21}, {"Bánh lạnh": "abc"}, {"Nguyên liệu": 5}):
		try:
			G.chuan_he_so(sai)
			raise AssertionError("phai chan %r" % sai)
		except ValueError:
			pass


def _dong(**kw):
	d = {"ma": "BAWC00067", "ten": "Roman 16", "nhom": "Bánh ổ sinh nhật", "dvt": "Cái", "gia_von": 250959,
		"gia_ban": 880000, "he_so_muc_tieu": 4, "gia_de_xuat": 1004000, "trang_thai": "duoi_muc_tieu"}
	d.update(kw)
	return d


@ca("gia von tam: chot chi luu mon du gia, dem dung ly do bo qua, ghi chu dung mau, dung ngay (chan luu gia thieu)")
def _dong_bang_gia():
	luu, bo = G.dong_bang_gia([
		_dong(),
		_dong(ma="X1", trang_thai="thieu_gia"),
		_dong(ma="X2", trang_thai="thieu_gia"),
		_dong(ma="X3", trang_thai="vong"),
		_dong(ma="X4", trang_thai="chua_dat_muc_tieu", gia_von=0, he_so_muc_tieu=None, gia_de_xuat=None),
		_dong(ma="X5", trang_thai="chua_gia_ban", gia_ban=0, gia_de_xuat=None, he_so_muc_tieu=None),
	], "2026-10-16")
	la("ma duoc luu", [p["item_code"] for p in luu], ["BAWC00067", "X5"])
	la("bo qua", bo, {"Thiếu giá nguyên liệu": 2, "Công thức vòng lặp": 1, "Giá vốn bằng 0": 1})
	la("ngay", luu[0]["valid_from"], "2026-10-16")
	la("don vi kho", luu[0]["uom"], "Cái")
	la("ghi chu", luu[0]["note"],
		"Hệ số mục tiêu x4. Giá bán đề xuất 1.004.000. Giá bán lúc chốt 880.000. Chỉ gồm nguyên liệu.")
	la("ghi chu khi chua co gi", luu[1]["note"], "Chưa đặt hệ số mục tiêu. Chưa có giá bán. Chỉ gồm nguyên liệu.")


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
		{"Bánh lạnh": 6}, {"LA-BAC": "Lá bạc"})
	la("thu tu", [d["ma"] for d in b["dong"]], ["SHIO", "BANH", "THIEU"])
	la("chua cong thuc", b["chua_cong_thuc"], {"so": 1, "ten": ["Bánh mới"]})
	shio = b["dong"][0]
	la("Shiopan", (shio["trang_thai"], shio["ty_le"], shio["he_so"]), ("vuot_gia_ban", 583.4, 0.2))
	la("Banh B x8 (12,5%) vuot muc tieu x6", (b["dong"][1]["he_so"], b["dong"][1]["ty_le"], b["dong"][1]["trang_thai"],
		b["dong"][1]["gia_de_xuat"]), (8.0, 12.5, "dat", 120000))
	la("lan truoc", b["dong"][1]["lan_truoc"], {"ngay": "2026-10-12", "gia": 19500.0, "chenh_pct": 2.6})
	thieu = b["dong"][2]
	la("ten nguyen lieu thieu", (thieu["thieu_so"], thieu["thieu_ten"]), (3, ["BTP-1", "BTP-2", "Lá bạc"]))
	dung("mon thieu gia khong co gia de xuat", thieu["gia_de_xuat"] is None)
	nhom = {n["ten"]: n for n in b["nhom"]}
	la("nhom banh lanh", (nhom["Bánh lạnh"]["so_mon"], nhom["Bánh lạnh"]["chua_cong_thuc"], nhom["Bánh lạnh"]["nhan"]), (2, 1, "Bánh lạnh"))
	la("trung vi he so chi gom mon du gia", nhom["Bánh lạnh"]["trung_vi"], round((0.2 + 8.0) / 2, 1))
	la("muc tieu nhom", nhom["Bánh lạnh"]["he_so_muc_tieu"], 6)


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


def _frappe_gia(roles=("Accounts Manager",), gia_ban=None, gia_nhap=None, quy_doi=None, bom=None):
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
	if bom is not None:
		du["BOM"] = list(bom)

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
		if dt == "UOM Conversion Detail":
			return list(quy_doi or [])
		return list(du.get(dt, []))

	cu = {k: getattr(frappe, k, None) for k in ("get_all", "db", "defaults", "get_roles")}
	frappe.get_all = get_all
	frappe.db = type("DB", (), {"get_single_value": staticmethod(lambda *a: "Standard Selling")})()
	frappe.defaults = type("DF", (), {"get_global_default": staticmethod(lambda k: '{"Bánh lạnh": 5}' if k == G.KHOA_HE_SO else None)})()
	frappe.get_roles = lambda *a, **k: list(roles)
	return cu, doc


def _tra(cu):
	import frappe
	for k, v in cu.items():
		if k == "__ten_khop":
			from vagabond import tim_kiem
			tim_kiem.ten_khop = v
			continue
		setattr(frappe, k, v)


@ca("gia von tam: doc site: dong BOM nhap theo Kg van tinh theo stock_qty don vi kho, doc theo lo (chan dung qty)")
def _doc_site():
	cu, doc = _frappe_gia()
	try:
		bang, he_so = G._bang()
	finally:
		_tra(cu)
	banh = [d for d in bang["dong"] if d["ma"] == "BANH"][0]
	# KEM = 1000 gram x 300 / 1000 = 300 mỗi gram; BANH = 100 x 20 + 200 x 300 = 62.000
	la("gia von", banh["gia_von"], 62000)
	la("he so, ty le va trang thai", (banh["he_so"], banh["ty_le"], banh["trang_thai"]), (5.0, 20.0, "dat"))
	la("de xuat 62000 x5", banh["gia_de_xuat"], 310000)
	la("he so doc dung khoa moi", he_so, {"Bánh lạnh": 5})
	la("mon chua cong thuc", bang["chua_cong_thuc"]["so"], 1)
	# Codex #483 vòng 2 thêm một lượt đọc hệ số đơn vị cho mỗi bảng giá.
	la("so lan doc moi doctype, khong hoi tung ma", sorted(set(doc)), ["BOM", "BOM Item", "Bin", "Item", "Item Price", "UOM Conversion Detail"])
	dung("so lan doc gioi han", len(doc) <= 11)


@ca("gia von tam: chot va dat ty le chan tai khoan chi duoc xem, truoc khi cham du lieu (chan bo cong quyen)")
def _quyen_chot():
	cu, doc = _frappe_gia(roles=("Accounts User",))
	try:
		for ham, ts in ((G.chot, ()), (G.luu_he_so, ('{"Bánh lạnh": 5}',)),
				(G.luu_thu, ('{"ten_mon": "Thu", "dong": []}',)), (G.bo_thu, ("GT-2610-001",))):
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
	# Codex #483 vòng 2: đổi đơn vị mua về đơn vị kho bằng hệ số; không có hệ số thì bỏ.
	la("doi Kg ve Gram", C([d(20000, uom="Kg")], "Gram", "2026-10-16", {"Kg": 1000}), 20.0)
	la("khong co he so thi bo", C([d(20000, uom="Kg")], "Gram", "2026-10-16", {}), None)
	la("dung don vi kho xep truoc dong phai doi", C([d(30000, uom="Kg"), d(25, uom="Gram")], "Gram", "2026-10-16", {"Kg": 1000}), 25.0)
	la("dong phai doi xep truoc dong khong ghi don vi", C([d(9, uom=None), d(20000, uom="Kg")], "Gram", "2026-10-16", {"Kg": 1000}), 20.0)


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


@ca("gia von tam: Codex #483 v2: bang gia nhap ghi theo don vi mua (Kg) thi doi ve don vi kho (Gram) bang he so, khong bao thieu gia")
def _gia_nhap_doi_don_vi():
	nhap = [_Dong(item_code="BOT", price_list_rate=20000, uom="Kg", valid_from="2026-08-01", valid_upto=None, customer=None, supplier=None, batch_no=None)]
	qd = [_Dong(parent="BOT", uom="Kg", conversion_factor=1000)]
	cu, doc = _frappe_gia(gia_nhap=nhap, quy_doi=qd)
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
	# BOT 100 gram x (20.000 / 1000) = 2.000; chỉ còn BO thiếu giá.
	la("gia von", banh["gia_von"], 2000)
	la("chi BO thieu", banh["thieu_so"], 1)


@ca("gia von tam: Codex #483 v3: nhieu cong thuc dang chay ma khong ban nao mac dinh thi KHONG doan theo thu tu doc (chan gia phu thuoc thu tu co so du lieu)")
def _bom_mo_ho_thuan():
	a = [{"item": "A", "name": "BOM-A-002", "is_default": 0}, {"item": "A", "name": "BOM-A-001", "is_default": 0},
		{"item": "B", "name": "BOM-B-001", "is_default": 0},
		{"item": "C", "name": "BOM-C-002", "is_default": 1}, {"item": "C", "name": "BOM-C-001", "is_default": 0}]
	for ds in (a, a[::-1]):
		la("mo ho khong chon", G.bom_cua_ma(ds).get("A"), None)
		la("chi mot ban thi lay", G.bom_cua_ma(ds).get("B"), "BOM-B-001")
		la("co mac dinh thi lay mac dinh", G.bom_cua_ma(ds).get("C"), "BOM-C-002")
		la("danh sach mo ho da xep", G.ma_mo_ho(ds), {"A": ["BOM-A-001", "BOM-A-002"]})
	b = G.dung_bang([{"ma": "A", "ten": "Bánh A", "nhom": "Bánh lạnh"}, {"ma": "X", "ten": "Bánh X", "nhom": "Bánh lạnh"}],
		{}, {}, {}, {}, {}, None, G.ma_mo_ho(a))
	la("khong co dong gia", b["dong"], [])
	la("tach rieng mon nhieu cong thuc", b["nhieu_cong_thuc"], {"so": 1, "ten": ["Bánh A"]})
	la("mon khong cong thuc van o cho cu", b["chua_cong_thuc"], {"so": 1, "ten": ["Bánh X"]})
	luu, _bo = G.dong_bang_gia(b["dong"], "2026-10-16")
	la("chot khong luu mon mo ho", luu, [])


@ca("gia von tam: Codex #483 v3: doc site: hai cong thuc BANH khong mac dinh, doi thu tu doc van cung ket qua, mon vao khung nhieu cong thuc")
def _bom_mo_ho_site():
	hai = [_Dong(name="B-BANH-2", item="BANH", quantity=1, is_default=0),
		_Dong(name="B-BANH", item="BANH", quantity=1, is_default=0),
		_Dong(name="B-KEM", item="KEM", quantity=1000, is_default=1)]
	ra = []
	for ds in (hai, hai[::-1]):
		cu, doc = _frappe_gia(bom=ds)
		try:
			bang, _t = G._bang()
		finally:
			_tra(cu)
		ra.append(bang)
		la("BANH khong co dong gia", [d["ma"] for d in bang["dong"]], [])
		la("BANH vao khung nhieu cong thuc", bang["nhieu_cong_thuc"], {"so": 1, "ten": ["Bánh B"]})
	la("hai thu tu doc cho cung ket qua", ra[0], ra[1])


@ca("gia von tam: Codex #483 v3: o tren trang chu hien dung tap vai may chu cho xem (chan Thu mua thay o chet)")
def _o_trang_chu_dung_quyen():
	import os
	import re
	goc = os.path.join(os.path.dirname(os.path.abspath(G.__file__)), "public", "js", "bep")
	js = open(os.path.join(goc, "01-khung-app.js"), encoding="utf-8").read()
	m = re.search(r"var QUYEN_GVT = \[([^\]]*)\]", js)
	dung("co tap JS", bool(m))
	la("JS khop may chu", set(re.findall(r"'([^']+)'", m.group(1))), set(G.QUYEN_XEM))
	tc = open(os.path.join(goc, "02-trang-chu.js"), encoding="utf-8").read()
	i = tc.index("card('🧮', 'Giá vốn tạm tính'")
	dung("o boc coQuyenGvt()", tc[i - 20:i].endswith("coQuyenGvt() ? "))


# ------------------------------------------------ v600 phiếu tính giá thử (R&D)


@ca("gia von tam: v600 phieu thu: lam sach dau vao, noi dung dong nao sai (chan luu phieu rong ten, so luong 0, gia am, nhom la)")
def _chuan_phieu():
	p = G.chuan_phieu({"ten_mon": "  Tart chanh dây ", "nhom": "Bánh lạnh", "so_ra": "8", "gia_ban_du_kien": "",
		"dong": [{"item_code": "BOT", "so_luong": "120,5"}, {"ten": "Chanh dây Đà Lạt", "dvt": "Gram", "so_luong": 200, "don_gia_tay": "90"}]})
	la("ten cat khoang trang", p["ten_mon"], "Tart chanh dây")
	la("so ra", p["so_ra"], 8.0)
	la("dong 1 so luong dau phay", p["dong"][0]["so_luong"], 120.5)
	la("dong 2 gia tay", (p["dong"][1]["item_code"], p["dong"][1]["don_gia_tay"]), (None, 90.0))
	la("so ra trong thi 1, don vi mac dinh Cai", (G.chuan_phieu({"ten_mon": "A"})["so_ra"], G.chuan_phieu({"ten_mon": "A"})["dvt_ra"]), (1.0, "Cái"))
	for sai, cau in (
		({"ten_mon": " "}, "Nhập tên món thử."),
		({"ten_mon": "A", "nhom": "Nguyên liệu"}, "Nhóm món không thuộc"),
		({"ten_mon": "A", "so_ra": 0}, "Một mẻ phải ra hơn 0."),
		({"ten_mon": "A", "dong": [{"so_luong": 1}]}, "Dòng 1 chưa có nguyên liệu."),
		({"ten_mon": "A", "dong": [{"item_code": "BOT", "so_luong": 0}]}, "Dòng 1 (BOT): số lượng phải lớn hơn 0."),
		({"ten_mon": "A", "dong": [{"ten": "X", "so_luong": 1, "don_gia_tay": -1}]}, "Dòng 1 (X): giá nhập tay không được âm."),
	):
		try:
			G.chuan_phieu(sai)
			raise AssertionError("phai chan %r" % sai)
		except ValueError as e:
			dung("cau: " + str(e), str(e).startswith(cau))


def _gia_ma(ma):
	return {
		"BOT": {"gia": 20.0, "nguon": "Giá kho", "thieu": 0, "vong": False},
		"KEM": {"gia": 300.0, "nguon": "Công thức", "thieu": 0, "vong": False},
		"BTP-THIEU": {"gia": 50.0, "nguon": "Công thức", "thieu": 2, "vong": False},
		"LA-BAC": {"gia": 0.0, "nguon": "Thiếu giá", "thieu": 1, "vong": False},
	}[ma]


@ca("gia von tam: v600 phieu thu: tinh bang dung nguon gia cua mon dang ban, gia tay thang, chia so ra, de xuat theo he so nhom")
def _tinh_phieu():
	p = G.chuan_phieu({"ten_mon": "Tart", "nhom": "Bánh lạnh", "so_ra": 4, "gia_ban_du_kien": 150000, "dong": [
		{"item_code": "BOT", "so_luong": 1000},             # 20.000
		{"item_code": "KEM", "so_luong": 100},              # 30.000
		{"ten": "Chanh dây", "dvt": "Gram", "so_luong": 200, "don_gia_tay": 50},   # 10.000
	]})
	k = G.tinh_phieu(p, _gia_ma, {"Bánh lạnh": 5})
	la("ca me", k["tong_me"], 60000)
	la("gia von mot cai", k["gia_von"], 15000)
	la("de xuat x5", k["gia_de_xuat"], 75000)
	la("gia ban du kien x10 (10%)", (k["he_so"], k["ty_le"], k["trang_thai"]), (10.0, 10.0, "dat"))
	la("nguon tung dong", [d["nguon"] for d in k["dong"]], ["Giá kho", "Công thức", "Nhập tay"])
	la("thanh tien", [d["thanh_tien"] for d in k["dong"]], [20000.0, 30000.0, 10000.0])
	# Mã thiếu giá: có giá tay thì thắng, không thì thiếu và không đề xuất.
	p2 = G.chuan_phieu({"ten_mon": "T2", "nhom": "Bánh lạnh", "dong": [{"item_code": "LA-BAC", "so_luong": 1}]})
	k2 = G.tinh_phieu(p2, _gia_ma, {"Bánh lạnh": 5})
	la("thieu gia", (k2["trang_thai"], k2["thieu_so"], k2["gia_de_xuat"]), ("thieu_gia", 1, None))
	p2["dong"][0]["don_gia_tay"] = 1200.0
	k3 = G.tinh_phieu(p2, _gia_ma, {"Bánh lạnh": 5})
	la("gia tay chua thieu", (k3["trang_thai"], k3["gia_von"], k3["gia_de_xuat"]), ("chua_gia_ban", 1200, 6000))
	k4 = G.tinh_phieu(G.chuan_phieu({"ten_mon": "T", "dong": [{"item_code": "BTP-THIEU", "so_luong": 1}]}), _gia_ma, {})
	la("ban thanh pham thieu gia o tang duoi cung tinh la thieu", k4["trang_thai"], "thieu_gia")
	la("phieu rong", G.tinh_phieu(G.chuan_phieu({"ten_mon": "R"}), _gia_ma, {})["trang_thai"], "chua_nguyen_lieu")
	la("chua chon nhom thi khong de xuat", G.tinh_phieu(G.chuan_phieu({"ten_mon": "N", "dong": [{"item_code": "BOT", "so_luong": 10}]}), _gia_ma, {"Bánh lạnh": 5})["gia_de_xuat"], None)


class _DocGia(_Dong):
	def __init__(self, **kw):
		_Dong.__init__(self, **kw)
		self.dong = []
		self.flags = _Dong()

	def set(self, k, v):
		setattr(self, k, v)

	def get(self, k, d=None):
		return getattr(self, k, d)

	def append(self, k, v):
		getattr(self, k).append(_Dong(**v))

	# Frappe chạy validate() của bộ điều khiển trước mỗi insert/save. Ca giả
	# gọi đúng hàm validate thật của Vagabond Gia Thu, không gọi phép tính
	# trực tiếp, để luu_thu và Desk đi chung một đường (Codex #486 P2).
	def _validate(self):
		from vagabond.vagabond.doctype.vagabond_gia_thu.vagabond_gia_thu import VagabondGiaThu
		VagabondGiaThu.validate(self)

	def insert(self):
		self._validate()
		self.name = "GT-2610-%03d" % (len(_DocGia.kho) + 1)
		_DocGia.kho[self.name] = self
		_DocGia.ghi.append(("insert", self.name))

	def save(self):
		self._validate()
		_DocGia.ghi.append(("save", self.name))


def _get_all_thu(kho):
	"""get_all giả của Vagabond Gia Thu: hiểu da_bo, ten_mon like, limit_start
	và limit_page_length như Frappe, để ca thấy được phiếu bị rơi khỏi trang."""
	def lam(filters=None, limit_start=0, limit_page_length=None, **kw):
		f = filters or {}
		if isinstance(f, dict):
			f = [[k] + (list(v) if isinstance(v, (list, tuple)) else ["=", v]) for k, v in f.items()]
		ra = []
		for ten, d in kho.items():
			hop = True
			for cot, phep, gt in f:
				co = ten if cot == "name" else d.get(cot)
				if phep == "=" and int(co or 0) != int(gt):
					hop = False
				if phep == "in" and co not in gt:
					hop = False
			if hop:
				ra.append(_Dong(name=ten))
		ra = ra[int(limit_start or 0):]
		return ra[:limit_page_length] if limit_page_length else ra
	return lam


@ca("gia von tam: v600 phieu thu doc site: luu tinh lai o may chu, mon BTP lay gia cong thuc, NVL ngoai cong thuc doc gia cung lo; chi ghi vao Vagabond Gia Thu")
def _phieu_site():
	import frappe
	_DocGia.kho, _DocGia.ghi = {}, []
	cu, doc = _frappe_gia()
	cu.update({k: getattr(frappe, k, None) for k in ("new_doc", "get_doc", "delete_doc")})
	goc = frappe.get_all

	def get_all(dt, **kw):
		if dt == "Bin" and "VANI" in ((kw.get("filters") or {}).get("item_code") or ["", []])[1]:
			return goc(dt, **kw) + [_Dong(item_code="VANI", actual_qty=10, stock_value=9000)]
		if dt == G.DT_THU:
			return _get_all_thu(_DocGia.kho)(**kw)
		return goc(dt, **kw)
	frappe.get_all = get_all
	frappe.new_doc = lambda dt: _DocGia(doctype=dt, name=None, modified="2026-10-16 23:00:00", owner="khai@x")
	frappe.get_doc = lambda dt, ten=None: _DocGia.kho[ten]
	frappe.db.exists = lambda dt, ten: ten in _DocGia.kho
	frappe.delete_doc = lambda *a, **k: _DocGia.ghi.append(("delete",) + a)
	try:
		phieu = {"ten_mon": "Tart vani", "nhom": "Bánh lạnh", "so_ra": 2, "gia_ban_du_kien": 50000,
			"dong": [{"item_code": "KEM", "so_luong": 100}, {"item_code": "VANI", "so_luong": 10}, {"ten": "Lá vàng", "dvt": "Lá", "so_luong": 1, "don_gia_tay": 5000}],
			"gia_von": 1}
		kq = G.luu_thu(json.dumps(phieu))
		# KEM theo công thức 300/gram x 100 = 30.000; VANI kho 900 x 10 = 9.000; lá vàng 5.000; chia 2.
		la("gia von tinh lai, khong nhan so may khach", kq["gia_von"], 22000)
		la("de xuat x5", kq["gia_de_xuat"], 110000)
		la("nguon", [d["nguon"] for d in kq["dong"]], ["Công thức", "Giá kho", "Nhập tay"])
		la("ten va don vi lay tu ma", (kq["dong"][1]["ten"], kq["dong"][1]["dvt"]), ("VANI", "Gram"))
		d = _DocGia.kho["GT-2610-001"]
		la("anh chup luu kem", (d.gia_von, d.gia_de_xuat, len(d.dong)), (22000, 110000, 3))
		la("chi ghi phieu thu", _DocGia.ghi, [("insert", "GT-2610-001")])
		dung("khong doc doctype la: %s" % sorted(set(doc)), set(doc) <= {"BOM", "BOM Item", "Bin", "Item", "Item Price", "UOM Conversion Detail", G.DT_THU})
		# Sửa lại cùng phiếu: thay dòng, không tạo phiếu mới.
		phieu.update(name="GT-2610-001", dong=[{"item_code": "KEM", "so_luong": 50}])
		kq2 = G.luu_thu(json.dumps(phieu))
		la("sua phieu cu", (_DocGia.ghi[-1], len(_DocGia.kho), len(d.dong), kq2["gia_von"]), (("save", "GT-2610-001"), 1, 1, 7500))
		ds = G.ds_thu()
		la("danh sach tinh lai", [(p["name"], p["gia_von"], p["trang_thai"]) for p in ds["ds"]], [("GT-2610-001", 7500, "dat")])
		dung("co nhom ban de chon", len(ds["nhom_ban"]) == len(G.NHOM_BAN) and ds["sua_duoc"])
		t = G.tinh_thu(json.dumps({"ten_mon": "Nháp", "dong": [{"item_code": "VANI", "so_luong": 1}]}))
		la("tinh thu khong luu", (t["gia_von"], len(_DocGia.kho)), (900, 1))
	finally:
		_tra(cu)


@ca("gia von tam: v600 doctype phieu thu: vai ghi trung QUYEN_CHOT, vai xem phu QUYEN_XEM, co du truong luu_thu ghi")
def _doctype_thu():
	import os
	goc = os.path.join(os.path.dirname(os.path.abspath(G.__file__)), "vagabond", "doctype")
	cha = json.load(open(os.path.join(goc, "vagabond_gia_thu", "vagabond_gia_thu.json"), encoding="utf-8"))
	con = json.load(open(os.path.join(goc, "vagabond_gia_thu_dong", "vagabond_gia_thu_dong.json"), encoding="utf-8"))
	la("ten", (cha["name"], con["name"], con["istable"]), (G.DT_THU, "Vagabond Gia Thu Dong", 1))
	ghi = {p["role"] for p in cha["permissions"] if p.get("write")}
	xem = {p["role"] for p in cha["permissions"] if p.get("read")}
	la("vai ghi", ghi, G.QUYEN_CHOT)
	la("vai xem", xem, G.QUYEN_XEM)
	truong = {f["fieldname"] for f in cha["fields"]}
	dung("truong cha", {"ten_mon", "nhom", "so_ra", "dvt_ra", "gia_ban_du_kien", "ghi_chu", "dong", "gia_von", "gia_de_xuat"} <= truong)
	la("truong con", [f["fieldname"] for f in con["fields"]], ["item_code", "ten", "so_luong", "dvt", "don_gia_tay"])
	nhom = [f for f in cha["fields"] if f["fieldname"] == "nhom"][0]["options"].split("\n")
	la("lua chon nhom trung NHOM_BAN", nhom, [""] + list(G.NHOM_BAN))
	la("field_order khop fields", cha["field_order"], [f["fieldname"] for f in cha["fields"]])
	quyen_xoa = sorted(p["role"] for p in cha["permissions"] if p.get("delete"))
	la("Codex #486 P1: chỉ System Manager còn quyền xoá cứng trên Desk (QT-20)", quyen_xoa, ["System Manager"])
	dung("có trường bỏ mềm", {"da_bo", "bo_luc", "bo_boi"} <= truong)
	bo = [f for f in cha["fields"] if f["fieldname"] == "da_bo"][0]
	la("trường Đã bỏ chỉ đọc, lọc được", (bo["fieldtype"], bo.get("read_only"), bo.get("in_standard_filter")), ("Check", 1, 1))


def _site_thu(kho_dau=None):
	"""Dựng site giả có sẵn các phiếu thử trong kho. Trả (cu, ghi)."""
	import frappe
	_DocGia.kho, _DocGia.ghi = dict(kho_dau or {}), []
	cu, doc = _frappe_gia()
	cu.update({k: getattr(frappe, k, None) for k in ("new_doc", "get_doc", "delete_doc", "session")})
	goc = frappe.get_all

	def get_all(dt, **kw):
		if dt == G.DT_THU:
			return _get_all_thu(_DocGia.kho)(**kw)
		return goc(dt, **kw)
	frappe.get_all = get_all
	frappe.new_doc = lambda dt: _DocGia(doctype=dt, name=None, modified="2026-10-16 23:00:00", owner="khai@x")
	frappe.get_doc = lambda dt, ten=None: _DocGia.kho[ten]
	frappe.db.exists = lambda dt, ten: ten in _DocGia.kho
	frappe.delete_doc = lambda *a, **k: _DocGia.ghi.append(("delete",) + a)
	frappe.session = _Dong(user="khai@x")
	# Bước hỏi SQL của tim_kiem cần site; thay bằng chính phép khop thuần
	# (bước 2 của tim_kiem.ten_khop) chạy trên kho giả. them_loc, loc_ten thật.
	from vagabond import tim_kiem
	cu["__ten_khop"] = tim_kiem.ten_khop

	def ten_khop(dt, q, cot, gioi_han=2000):
		if not tim_kiem.cac_tu(q):
			return None
		return sorted(t for t, d in _DocGia.kho.items() if tim_kiem.khop([t] + [d.get(c) for c in cot if c != "name"], q))
	tim_kiem.ten_khop = ten_khop
	return cu


def _phieu_kho(ten, ten_mon, da_bo=0):
	d = _DocGia(doctype=G.DT_THU, name=ten, ten_mon=ten_mon, nhom="Bánh lạnh", so_ra=1, dvt_ra="Cái",
		gia_ban_du_kien=0, ghi_chu="", modified="2026-10-16 22:00:00", owner="khai@x", da_bo=da_bo)
	d.dong = [_Dong(item_code=None, ten="Lá vàng", dvt="Lá", so_luong=1, don_gia_tay=1000)]
	return d


@ca("gia von tam: Codex #486 P1 bo phieu thu la bo mem: khong goi delete_doc, giu nguyen dong va gia, an khoi danh sach, khong luu de len phieu da bo")
def _bo_mem():
	cu = _site_thu({"GT-2610-001": _phieu_kho("GT-2610-001", "Tart chanh"), "GT-2610-002": _phieu_kho("GT-2610-002", "Mousse xoài")})
	try:
		kq = G.bo_thu("GT-2610-001")
		d = _DocGia.kho.get("GT-2610-001")
		dung("phiếu vẫn còn trong kho", d is not None)
		la("không xoá cứng", [g for g in _DocGia.ghi if g[0] == "delete"], [])
		la("đánh dấu bỏ, ghi người và lúc bỏ", (d.da_bo, d.bo_boi, bool(d.bo_luc)), (1, "khai@x", True))
		la("giữ nguyên dòng nguyên liệu để tra lại", len(d.dong), 1)
		la("trả về ok", kq.get("ok"), 1)
		la("danh sách chỉ còn phiếu chưa bỏ", [p["name"] for p in G.ds_thu()["ds"]], ["GT-2610-002"])
		try:
			G.luu_thu(json.dumps({"name": "GT-2610-001", "ten_mon": "Tart chanh", "dong": [{"ten": "Lá", "dvt": "Lá", "so_luong": 1, "don_gia_tay": 1}]}))
			dung("lưu đè lên phiếu đã bỏ phải bị chặn", False)
		except Exception as e:
			dung("câu chặn nói phiếu đã bỏ: %s" % e, "đã bỏ" in str(e))
	finally:
		_tra(cu)


@ca("gia von tam: Codex #486 P2 luu phieu thu tu Desk cung tinh lai gia von va gia de xuat qua validate, dong co ma lay ten va don vi tu mat hang")
def _desk_luu():
	from vagabond.vagabond.doctype.vagabond_gia_thu.vagabond_gia_thu import VagabondGiaThu
	cu = _site_thu()
	try:
		d = _DocGia(doctype=G.DT_THU, name="GT-2610-009", ten_mon="Bánh Desk", nhom="Bánh lạnh", so_ra=2, dvt_ra="Cái",
			gia_ban_du_kien=0, ghi_chu="", gia_von=1, gia_de_xuat=1)
		# Người dùng Desk gõ mã KEM, để trống tên và đơn vị, sửa số mẻ ra 2.
		d.dong = [_Dong(item_code="KEM", ten="", dvt="", so_luong=100, don_gia_tay=0),
			_Dong(item_code=None, ten="Lá vàng", dvt="Lá", so_luong=1, don_gia_tay=5000)]
		VagabondGiaThu.validate(d)
		# KEM theo công thức 300/gram x 100 = 30.000; lá vàng 5.000; chia 2 = 17.500; x5 = 87.500 -> 88.000.
		la("giá vốn tính lại, không giữ số cũ", (d.gia_von, d.gia_de_xuat), (17500, 88000))
		la("dòng có mã lấy tên và đơn vị kho", (d.dong[0].ten, d.dong[0].dvt), ("KEM", "Gram"))
		d.dong = [_Dong(item_code=None, ten="", dvt="", so_luong=1, don_gia_tay=0)]
		try:
			VagabondGiaThu.validate(d)
			dung("dòng trống phải bị chặn", False)
		except Exception as e:
			dung("câu chặn nói đúng dòng: %s" % e, "Dòng 1" in str(e))
	finally:
		_tra(cu)


@ca("gia von tam: Codex #486 P2 danh sach phieu thu chia trang va tim o may chu: khong phieu nao bi roi khi co nhieu hon mot trang")
def _trang_ds():
	kho = {}
	for i in range(1, 76):
		ten = "GT-2610-%03d" % i
		kho[ten] = _phieu_kho(ten, ("Mousse " if i % 5 == 0 else "Tart ") + str(i))
	kho["GT-2610-076"] = _phieu_kho("GT-2610-076", "Tart bỏ", da_bo=1)
	cu = _site_thu(kho)
	try:
		thay = []
		bat_dau = 0
		for _vong in range(10):
			t = G.ds_thu(bat_dau=bat_dau)
			thay += [p["name"] for p in t["ds"]]
			if not t["con_nua"]:
				break
			bat_dau = t["bat_dau_tiep"]
		la("đi hết các trang thấy đủ 75 phiếu chưa bỏ, không trùng", (len(thay), len(set(thay))), (75, 75))
		la("mỗi trang tối đa TRANG_THU phiếu", len(G.ds_thu()["ds"]), G.TRANG_THU)
		t = G.ds_thu(tu_khoa="MOUSSE")
		la("tìm ở máy chủ qua tim_kiem, không phân biệt hoa thường", sorted(p["name"] for p in t["ds"]), sorted("GT-2610-%03d" % i for i in range(5, 76, 5)))
		la("gõ không dấu vẫn ra, nhưng không ra phiếu đã bỏ", G.ds_thu(tu_khoa="tart bo")["ds"], [])
		la("phiếu đã bỏ thật có khớp chữ, chỉ bị lọc vì đã bỏ", G.tim_kiem.khop(["Tart bỏ"], "tart bo"), True)
	finally:
		_tra(cu)


@ca("gia von tam: Codex #486 chuan_trang lam sach tham so trang: so am, chu, tu khoa dai")
def _chuan_trang():
	la("mặc định", G.chuan_trang(None, None), ("", 0))
	la("số âm về 0, chữ về 0", (G.chuan_trang("", -5)[1], G.chuan_trang("", "abc")[1]), (0, 0))
	la("bỏ khoảng trắng hai đầu, giữ chữ để tim_kiem chuẩn hoá", G.chuan_trang(" Tart chanh ", "30"), ("Tart chanh", 30))
	la("cắt từ khoá dài", len(G.chuan_trang("x" * 500, 0)[0]), 80)


@ca("gia von tam: Codex #486 tim nguyen lieu cho phieu thu di qua tim_kiem (v583), loai nhom banh ban, go mot chu chua tim")
def _tim_nl():
	import frappe
	from vagabond import tim_kiem
	cu, _doc = _frappe_gia()
	goi = []
	cu_tk = tim_kiem.ten_khop
	tim_kiem.ten_khop = lambda dt, q, cot, gioi_han=2000: ["NVLT00001"] if tim_kiem.cac_tu(q) else None

	def get_all(dt, filters=None, **kw):
		goi.append((dt, filters))
		return [_Dong(name="NVLT00001", item_name="Bột mì", stock_uom="Gram", item_group="Nguyên liệu")]
	frappe.get_all = get_all
	try:
		la("một chữ chưa tìm", (G.tim_nl("b"), goi), ([], []))
		kq = G.tim_nl("bot mi")
		la("trả mã, tên, đơn vị, nhóm", kq, [{"ma": "NVLT00001", "ten": "Bột mì", "dvt": "Gram", "nhom": "Nguyên liệu"}])
		loc = goi[0][1]
		dung("lọc theo tên khớp của tim_kiem: %s" % loc, ["name", "in", ["NVLT00001"]] in loc)
		dung("loại nhóm bánh bán ra", ["item_group", "not in", list(G.NHOM_BAN)] in loc)
		dung("không tự viết like", "like" not in json.dumps(loc, ensure_ascii=False))
	finally:
		tim_kiem.ten_khop = cu_tk
		_tra(cu)
