# -*- coding: utf-8 -*-
"""v668 Gợi ý mua thêm (phần F prompt /banh, anh Việt duyệt 17/11/2026).

Ca chốt:
  - cài đặt điền tay: mọi cách điền hợp lý, trống là mặc định;
  - luật tồn: bánh khô hết ở bếp KHÔNG được gợi ý; dưới ngưỡng không gợi ý;
    viennoiserie (bếp làm theo đơn) luôn được; không ảnh, không giá thì không bày;
  - ghép theo món gốc, theo nhóm món gốc; món trong giỏ không gợi ý lại;
  - xếp hạng: ghim (trong khoảng ngày), rồi hay mua cùng, rồi tồn nhiều;
  - món chưa có cặp duyệt dùng luật nhóm và câu chung;
  - đánh dấu dòng thêm từ gợi ý chỉ giữ mã còn trong đơn; báo cáo chỉ đọc ảnh chụp;
  - cảnh báo mức giữ: chuyển từ bếp làm tồn dưới mức thì cảnh báo, không chặn;
  - bản nháp: câu dưới 40 ký tự, không dấu gạch dài, 3 tới 5 món mỗi món gốc.
"""

import json
import os
import subprocess
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import goi_y_mua as g  # noqa: E402
from vagabond import goi_y_nhap  # noqa: E402

HOM_NAY = "2026-11-17"


def _m(ma, nhom="Bánh khô", anh="/a.jpg", gia=100000):
	return {"ma": ma, "ten": "Món " + ma, "anh": anh, "gia": gia, "nhom": nhom}


@ca("v668 cài đặt gợi ý điền tay: trống là mặc định (bật, 4 món, ngưỡng 3, hai kho bếp); số lạ, số âm, dấu phẩy, dòng câu lý do")
def _cai_dat():
	cd = g.chuan_cai_dat({})
	la("mặc định", (cd["bat_gio"], cd["bat_quay"], cd["bat_dbt"], cd["thanh_mien_phi"], cd["toi_da"], cd["nguong"], cd["nhom"], cd["kho_bep"]),
		(True, True, True, True, 4, 3, ["Bánh khô", "Bánh nướng"], ["Pastry - Thành phẩm - TV", "Baker - Thành phẩm - TV"]))
	cd = g.chuan_cai_dat({"bat_gio": "0", "toi_da": "9", "nguong": "-2", "nhom": "Bánh khô; Bánh lạnh\n", "kho_bep": " Kho A \n\n"})
	la("tắt, trần 6, âm về mặc định, nhiều cách xuống dòng", (cd["bat_gio"], cd["toi_da"], cd["nguong"], cd["nhom"], cd["kho_bep"]),
		(False, 6, 3, ["Bánh khô", "Bánh lạnh"], ["Kho A"]))
	la("chữ lạ", g.chuan_cai_dat({"toi_da": "bốn", "nguong": "2,0"})["toi_da"], 4)
	la("2,0 đọc là 2", g.chuan_cai_dat({"nguong": "2,0"})["nguong"], 2)
	cd = g.chuan_cai_dat({"ly_do_nhom": "Bánh khô | Giòn rụm | Crunchy\nBánh nướng|Mới ra lò\nhỏng"})
	la("câu theo nhóm", (cd["ly_do_nhom"]["Bánh khô"], cd["ly_do_nhom"]["Bánh nướng"]), (("Giòn rụm", "Crunchy"), ("Mới ra lò", "Mới ra lò")))
	dung("dòng hỏng không làm mất câu mặc định", "Đồ uống" in cd["ly_do_nhom"])


@ca("v668 luật tồn (thử theo prompt): món hết ở bếp KHÔNG được gợi ý cho đơn đặt trước; dưới ngưỡng không; viennoiserie luôn được; thiếu ảnh, giá 0 không bày")
def _loc():
	mon = [_m("KHO_HET"), _m("KHO_2"), _m("KHO_3"), _m("KHO_50"), _m("CROI", "Bánh nướng"), _m("KHONG_ANH", anh=""), _m("GIA0", gia=0)]
	uv = g.loc_ung_vien(mon, {"KHO_HET": 0, "KHO_2": 2, "KHO_3": 3, "KHO_50": 50, "KHONG_ANH": 9, "GIA0": 9}, 3)
	la("chỉ còn món đủ tồn và viennoiserie", sorted(uv), ["CROI", "KHO_3", "KHO_50"])
	la("viennoiserie không xét tồn", uv["CROI"]["ton"], None)
	uv = g.loc_ung_vien(mon, {}, 0)
	la("ngưỡng 0 vẫn không gợi ý món tồn 0", sorted(uv), ["CROI"])


CAP = [
	{"mon_goc": "candle", "mon_goi_y": "COCOA", "ly_do_vn": "Cacao đắng hợp sô cô la", "uu_tien": 10},
	{"mon_goc": "candle", "mon_goi_y": "CROI", "ly_do_vn": "Croissant bơ", "uu_tien": 20, "ghim_tu": "2026-11-10", "ghim_den": "2026-11-20"},
	{"mon_goc": "candle", "mon_goi_y": "HAT", "ly_do_vn": "Hạt rang", "uu_tien": 30, "ghim_tu": "2026-11-18"},
	{"mon_goc": "candle", "mon_goi_y": "HET_HANG", "ly_do_vn": "Không còn", "uu_tien": 1},
	{"mon_goc": "", "nhom_goc": "Bánh lạnh", "mon_goi_y": "TRA", "ly_do_vn": "Trà lài", "uu_tien": 10},
]


def _uv():
	return {m: dict(_m(m), ton=t) for m, t in (("COCOA", 5), ("CROI", None), ("HAT", 40), ("TUILE", 9), ("TRA", 7))}


@ca("v668 ghép và xếp hạng: ghim đang hiệu lực đứng đầu, rồi hay mua cùng, rồi tồn nhiều; ghim chưa tới ngày không tính; món hết hàng bị lọc trước")
def _xep():
	ds = g.xep_goi_y([["BAWC00139", "candle"]], _uv(), CAP, {}, HOM_NAY, {"HAT": 4, "COCOA": 1}, 4)
	la("thứ tự", [u["ma"] for u in ds], ["CROI", "HAT", "COCOA"])
	la("câu lý do theo cặp, đánh dấu ghim", [(u["ly_do_vn"], u["ghim"]) for u in ds][:2], [("Croissant bơ", 1), ("Hạt rang", 0)])
	dung("món hết hàng không lọt qua cặp", all(u["ma"] != "HET_HANG" for u in ds))
	ds = g.xep_goi_y([["BAWC00139", "candle"], ["COCOA"]], _uv(), CAP, {}, "2026-11-21", {}, 4)
	la("21/11: Croissant hết ghim, Hạt bắt đầu ghim từ 18/11 (không ngày cuối); Cacao đã trong giỏ không gợi ý lại",
		[(u["ma"], u["ghim"]) for u in ds][:2], [("HAT", 1), ("CROI", 0)])
	dung("Cacao đã trong giỏ không gợi ý lại (giỏ có Cacao chưa có cặp nên thêm món theo nhóm)", "COCOA" not in [u["ma"] for u in ds])
	ds = g.xep_goi_y([["candle"]], {m: u for m, u in _uv().items() if m != "CROI"}, CAP, {}, "2026-11-21", {}, 4)
	la("cùng không ghim, không mua cùng: tồn nhiều trước", [u["ma"] for u in ds], ["HAT", "COCOA"])


@ca("v668 món chưa có cặp duyệt: theo nhóm với câu chung; có cặp thì không lẫn món ngoài cặp; ghép theo Nhóm món gốc")
def _nhom():
	ly = {"Bánh khô": ("Giòn thơm", "Crisp")}
	ds = g.xep_goi_y(["very berry"], _uv(), CAP, ly, HOM_NAY, {}, 4)
	la("không cặp: mọi món đủ điều kiện, câu nhóm", sorted(u["ma"] for u in ds), ["COCOA", "CROI", "HAT", "TRA", "TUILE"])
	la("câu chung", {u["ly_do_vn"] for u in ds}, {"Giòn thơm"})
	ds = g.xep_goi_y(["candle"], _uv(), CAP, ly, HOM_NAY, {}, 4)
	la("có cặp: chỉ món trong cặp (Hạt chưa tới ngày ghim vẫn là cặp)", sorted(u["ma"] for u in ds), ["COCOA", "CROI", "HAT"])
	ds = g.xep_goi_y([["BAWC00139", "candle"], ["X9", "very berry"]], _uv(), CAP, ly, HOM_NAY, {}, 4)
	la("giỏ hai bánh, một bánh chưa có cặp: thêm món theo nhóm, món có cặp vẫn đứng trước", [u["ma"] for u in ds][:3], ["CROI", "HAT", "COCOA"])
	ds = g.xep_goi_y(["NUOC1", "x"], {"TRA": dict(_m("TRA", "Trà"), ton=None)}, CAP, {}, HOM_NAY, {}, 4, nhom_cua_gio={"Bánh lạnh"})
	la("ghép theo nhóm món gốc", [(u["ma"], u["ly_do_vn"]) for u in ds], [("TRA", "Trà lài")])
	la("trần toi_da * 3", len(g.xep_goi_y(["z"], {str(i): dict(_m(str(i)), ton=i + 3) for i in range(30)}, [], {}, HOM_NAY, {}, 2)), 6)


@ca("v668 đánh dấu dòng thêm từ gợi ý: chỉ mã còn trong đơn, bỏ rác; báo cáo tỉ lệ, giá trị trung bình, món thêm nhiều nhất từ ảnh chụp đơn")
def _do():
	la("mã lạ, trùng, không còn trong đơn bị bỏ", g.ma_goi_y(["A", "A", "Z", None, 5], ["A", "B"]), ["A"])
	la("không phải danh sách", g.ma_goi_y("A", ["A"]), [])
	snaps = [json.dumps({"mon": [{"ma": "BANH", "sl": 1, "gia": 650000}, {"ma": "A", "ten": "Canelé", "sl": 2, "gia": 65000}], "goi_y": ["A"]}),
		{"mon": [{"ma": "BANH", "sl": 1, "gia": 880000}]}, "hỏng", {"mon": [{"ma": "B", "ten": "Biscotti", "sl": 1, "gia": 190000}], "goi_y": ["B"]}]
	bc = g.bao_cao(snaps)
	la("báo cáo", (bc["so_don"], bc["don_co_goi_y"], bc["ti_le"], bc["gia_tri_tb"], bc["gia_tri_tb_co_goi_y"]),
		(3, 2, 66.7, (780000 + 880000 + 190000) // 3, (780000 + 190000) // 2))
	la("món thêm nhiều nhất", [(m["ma"], m["sl"]) for m in bc["mon"]], [("A", 2), ("B", 1)])
	la("hay mua cùng", g.mua_cung_dem(snaps), {"A": 1, "B": 1})


@ca("v668 cảnh báo mức giữ tại bếp: chuyển làm tồn dưới mức thì cảnh báo, đúng mức thì không; món không có mức không cảnh báo; hook không chặn lưu phiếu")
def _muc_giu():
	cb = g.canh_bao_xuat([{"ma": "A", "sl": 3}, {"ma": "A", "sl": 2}, {"ma": "B", "sl": 1}, {"ma": "C", "sl": 9}],
		{"A": 10, "B": 6, "C": 9}, {"A": 6, "B": 5, "C": 0}, {"A": "Canelé"})
	la("A còn 5 dưới mức 6; B còn 5 đúng mức; C không giữ", cb, [{"ma": "A", "ten": "Canelé", "con": 5, "muc": 6}])
	dung("câu cảnh báo nói việc", "Phiếu vẫn lưu được" in g.cau_canh_bao(cb) and "Canelé còn 5, mức giữ 6" in g.cau_canh_bao(cb))

	class Dong(dict):
		__getattr__ = dict.get

	doc = um.MagicMock()
	doc.get.return_value = [Dong(item_code="A", qty=5, transfer_qty=5, s_warehouse="Pastry - Thành phẩm - TV", t_warehouse="Kho D1 - TV"),
		Dong(item_code="A", qty=5, s_warehouse="Kho D1 - TV", t_warehouse="Kho NVHTN - TV")]
	doc.flags = um.MagicMock()
	thong, doc_ds = [], []
	with um.patch.object(g, "cai_dat", lambda: g.chuan_cai_dat({})), um.patch.object(g, "_ton", lambda ma, kho: {"A": 8}), \
			um.patch.object(g.frappe, "get_all", lambda dt, **k: (doc_ds.append(k.get("limit_page_length")), [Dong(name="A", item_name="Canelé", vgb_muc_giu_web=6)])[1]), \
			um.patch.object(g.frappe, "msgprint", lambda *a, **k: thong.append((a, k)), create=True), \
			um.patch.object(g.frappe, "throw", lambda *a, **k: (_ for _ in ()).throw(AssertionError("không được chặn")), create=True):
		g.canh_bao_muc_giu(doc)
	la("chỉ dòng từ bếp ra cửa hàng tính: 8 - 5 = 3 dưới 6", len(thong), 1)
	dung("cảnh báo màu cam", thong[0][1].get("indicator") == "orange")
	la("đọc mức giữ, tên món ĐỦ (phiếu hơn 20 dòng, H8 loại 2)", doc_ds, [0, 0])


@ca("v668 bản nháp gieo MỘT lần trong đời site: đã gieo thì Marketing xoá hết dòng, lần deploy sau không gieo lại; bảng đã có dòng thì không gieo")
def _gieo():
	da = {}
	them = []

	class Doc(dict):
		def update(self, d):
			dict.update(self, d)

		def insert(self, **k):
			them.append(dict(self))

	with um.patch.object(g.frappe.db, "get_default", lambda k: da.get(k), create=True), \
			um.patch.object(g.frappe.db, "set_default", lambda k, v: da.__setitem__(k, v), create=True), \
			um.patch.object(g.frappe.db, "count", lambda dt: 0, create=True), \
			um.patch.object(g.frappe.db, "exists", lambda *a: True, create=True), \
			um.patch.object(g.frappe, "new_doc", lambda dt: Doc(), create=True), \
			um.patch.object(g.frappe, "get_all", lambda dt, **k: [type("X", (), {"name": d[1]}) for d in goi_y_nhap.NHAP], create=True):
		n = g.gieo_nhap()
		la("lần đầu gieo đủ, trạng thái Nháp", (n, len(them), {x.get("trang_thai") for x in them}), (len(goi_y_nhap.NHAP), len(goi_y_nhap.NHAP), {"Nháp"}))
		la("lần sau (bảng đã bị xoá hết) không gieo lại", g.gieo_nhap(), 0)
	with um.patch.object(g.frappe.db, "get_default", lambda k: None, create=True), um.patch.object(g.frappe.db, "count", lambda dt: 5, create=True):
		la("bảng đã có dòng", g.gieo_nhap(), 0)


@ca("v668 dòng Món đi kèm: thiếu món gốc, thiếu món gợi ý, trạng thái lạ, câu dài, ngày ghim ngược thì báo việc cần sửa")
def _kiem_cap():
	ok = {"mon_goc": "candle", "mon_goi_y": "A", "trang_thai": "Nháp", "ly_do_vn": "Ngắn"}
	la("đủ", g.kiem_cap(ok), "")
	la("thiếu gốc", g.kiem_cap(dict(ok, mon_goc="")), "Chọn Món gốc hoặc Nhóm món gốc.")
	la("nhóm gốc thay món gốc", g.kiem_cap(dict(ok, mon_goc="", nhom_goc="Bánh lạnh")), "")
	la("thiếu gợi ý", g.kiem_cap(dict(ok, mon_goi_y="")), "Chọn Món gợi ý.")
	la("trạng thái lạ", g.kiem_cap(dict(ok, trang_thai="Duyệt")), "Trạng thái chỉ được Nháp, Đã duyệt hoặc Bỏ.")
	dung("câu dài", "dài quá" in g.kiem_cap(dict(ok, ly_do_vn="x" * 70)))
	la("ghim ngược", g.kiem_cap(dict(ok, ghim_tu="2026-11-20", ghim_den="2026-11-18")), "Ngày ghim đến phải sau ngày ghim từ.")


@ca("v668 bản nháp Món đi kèm: câu dưới 40 ký tự, có câu tiếng Anh, không dấu gạch dài, mỗi món gốc 3 tới 5 món, không trùng cặp")
def _nhap():
	ds = goi_y_nhap.NHAP
	dung("đủ nhiều cặp", len(ds) >= 60)
	la("câu quá 40 ký tự", [d[2] for d in ds if len(d[2]) > 40], [])
	la("thiếu câu tiếng Anh", [d for d in ds if not d[3]], [])
	la("dấu gạch dài", [d for d in ds if "–" in d[2] + d[3] or "—" in d[2] + d[3]], [])
	dem = {}
	for d in ds:
		dem[d[0]] = dem.get(d[0], 0) + 1
	la("món gốc ngoài 3 tới 5 món", {k: v for k, v in dem.items() if not 3 <= v <= 5}, {})
	la("trùng cặp", len({(d[0], d[1]) for d in ds}), len(ds))
	la("món gốc viết thường như khoá thẻ Bánh", [d[0] for d in ds if not d[0].startswith("@") and d[0] != d[0].lower()], [])


def _goi(ma, bo=None, ton=None, cap=None, cd=None, dot=None):
	mon = [_m("CANELE"), _m("BISCOTTI"), _m("CROI", "Bánh nướng")]
	with um.patch.object(g, "cai_dat", lambda: g.chuan_cai_dat(cd or {})), um.patch.object(g, "_mon_nhom", lambda nhom: mon), \
			um.patch.object(g, "_ton", lambda ma, kho: dict(ton or {})), um.patch.object(g, "_khoa_cua_ma", lambda ma: {"BAWC00139": "candle"}), \
			um.patch.object(g, "_cap_duyet", lambda: list(cap or [])), um.patch.object(g, "_snap_moi", lambda n=60: []), \
			um.patch.object(g, "_hom_nay", lambda: HOM_NAY), um.patch.object(g, "_co_ma_pancake", lambda ds: ds), \
			um.patch.object(g.frappe, "get_all", lambda *a, **k: [], create=True):
		if dot is not None:
			from vagabond import dac_biet_tuan as dbt
			with um.patch.object(dbt, "dot_cong_khai", lambda: dot), um.patch.object(dbt, "ma_theo_khoa", lambda d: {"x": {"BAWC00139"}}):
				return g.goi_y_dat_truoc(json.dumps(ma), json.dumps(bo or ma))
		return g.goi_y_dat_truoc(json.dumps(ma), json.dumps(bo or ma))


@ca("v668 cửa giỏ đặt trước: Canelé hết ở bếp không được gợi ý, Biscotti còn 9 được; Croissant luôn được; món vừa thêm từ gợi ý không coi là món gốc, không gợi ý lại; tắt thì không trả món")
def _cua():
	r = _goi(["BAWC00139"], ton={"CANELE": 0, "BISCOTTI": 9})
	la("món gợi ý", sorted(m["ma"] for m in r["mon"]), ["BISCOTTI", "CROI"])
	la("bật, 4 món, thanh miễn phí", (r["bat"], r["toi_da"], r["thanh_mien_phi"]), (1, 4, 1))
	cap = [{"mon_goc": "candle", "mon_goi_y": "BISCOTTI", "ly_do_vn": "Cacao hợp sô cô la"}]
	r = _goi(["BAWC00139"], bo=["BAWC00139", "BISCOTTI"], ton={"BISCOTTI": 9}, cap=cap)
	la("Biscotti đã thêm: không gợi ý lại, không mở luật nhóm vì món gốc vẫn là Candle có cặp", [m["ma"] for m in r["mon"]], [])
	r = _goi(["BAWC00139"], ton={"BISCOTTI": 9}, cap=cap)
	la("câu theo cặp đã duyệt", [(m["ma"], m["ly_do_vn"]) for m in r["mon"]], [("BISCOTTI", "Cacao hợp sô cô la")])
	la("tắt ở giỏ đặt trước", _goi(["BAWC00139"], cd={"bat_gio": "0"}, ton={"BISCOTTI": 9}), {"bat": 0, "toi_da": 4, "thanh_mien_phi": 1, "mon": []})
	la("tắt khi giỏ có món Đặc biệt tuần này", _goi(["BAWC00139"], cd={"bat_dbt": "0"}, ton={"BISCOTTI": 9}, dot={"id": "d"})["bat"], 0)
	la("giỏ chưa có bánh", _goi([], ton={"BISCOTTI": 9})["mon"], [])


GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@ca("v668 chạy thật trang khách (hanh_vi/goi_y_mua_668.mjs: giỏ đặt trước, Tại quầy, khối vẽ) và màn Món đi kèm (hanh_vi/mon_di_kem_668.js) đều đạt")
def _node():
	for t, can in (("goi_y_mua_668.mjs", "9 đạt, 0 hỏng"), ("mon_di_kem_668.js", "5 ca đạt, 0 ca hỏng")):
		r = subprocess.run(["node", os.path.join(GOC, "vagabond/khung/kiem_thu/hanh_vi", t)], capture_output=True, text=True, timeout=120)
		la(t, (r.returncode, can in (r.stdout or ""), (r.stdout or "")[-500:] if r.returncode else ""), (0, True, ""))
