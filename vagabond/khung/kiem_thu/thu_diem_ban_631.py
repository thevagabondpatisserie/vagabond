# -*- coding: utf-8 -*-
"""v631: điểm bán tự nhận theo tài khoản và bảng giá riêng NVH (anh Việt 02/11/2026).

Anh duyệt mẫu bốn màn:
  1. Cài đặt Điểm bán: "Nhân viên đứng điểm này" (gợi ý từ bill 30 ngày) và
     "Bảng giá của điểm" (Giá chung hay Giá riêng) (_chuan_cau_hinh, _kiem).
  2. Tạo mặt hàng: ô giá riêng theo điểm (_doc_gia, _tao_mon).
  3. Bảng giá theo điểm bán: sửa một lượt, Tải/Nạp Excel (_thay_doi, _excel).
  4. Quầy: tài khoản đứng một điểm là vào thẳng điểm đó; MÁY CHỦ tính lại giá
     theo điểm khi lưu bill, không ai sửa tay được (_ap_gia, _thu_tu_may_chu).

Phép thuần chạy thật. Riêng ban_hang (nạp requests, không chạy được ở CI tay
không) thì đọc cây hàm để chốt CHỖ gọi: giá phải đặt lại TRƯỚC khi tính khuyến
mãi và trước khi xét OTP sửa bill; hành vi của phép gọi thì ca _ap_gia chạy thật.
"""

import ast
import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import diem_ban as db  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*p):
	return io.open(os.path.join(GOI, *p), encoding="utf-8").read()


def _loi(ham):
	try:
		ham()
	except Exception as e:
		return str(e)
	return ""


@ca("v631 cấu hình điểm bán: người đứng điểm bỏ trùng, bỏ rỗng; bật Giá riêng thì gắn bảng theo MÃ điểm; tắt thì về giá chung; cấu hình cũ giữ bảng đã lưu")
def _chuan_cau_hinh():
	d = db._chuan({"ma": "nvhtn", "ten": "Nhà Văn Hóa Thanh Niên", "ten_ngan": "NVHTN", "co_quay": 1, "nguon": ["Tại chỗ"],
		"nhan_vien": ["truc@vgb.vn", " ", "truc@vgb.vn", "uyen@vgb.vn"], "gia_rieng": 1})
	la("người đứng điểm", d["nhan_vien"], ["truc@vgb.vn", "uyen@vgb.vn"])
	la("bảng giá theo mã điểm", d["bang_gia"], "Giá riêng NVHTN")
	la("tắt giá riêng", db._chuan({"ma": "NVHTN", "co_quay": 1, "gia_rieng": 0, "bang_gia": "Giá riêng NVHTN"})["bang_gia"], "")
	la("cấu hình đã lưu giữ bảng", db._chuan({"ma": "NVHTN", "co_quay": 1, "bang_gia": "Giá riêng NVHTN"})["bang_gia"], "Giá riêng NVHTN")
	la("điểm cũ chưa khai gì: rỗng, giá chung", (db._chuan(db.MAC_DINH[1])["nhan_vien"], db._chuan(db.MAC_DINH[1])["bang_gia"]), ([], ""))
	la("người gõ thành chuỗi vẫn đọc được", db._chuan({"ma": "TCV", "nhan_vien": "a@x.vn, b@x.vn;a@x.vn"})["nhan_vien"], ["a@x.vn", "b@x.vn"])


@ca("v631 điểm của tài khoản: chỉ điểm đang bật có tên người đó; Gia Bảo đứng District 1 không thấy Sales Online; quản lý đứng hai điểm")
def _diem_cua_nguoi():
	ds = [db._chuan(dict(x, nhan_vien=nv)) for x, nv in zip(db.MAC_DINH, [[], ["bao@vgb.vn", "de@vgb.vn"], ["truc@vgb.vn", "de@vgb.vn"]])]
	la("thu ngân một điểm", db.diem_cua_nguoi(ds, "bao@vgb.vn"), ["TCV"])
	la("quản lý hai điểm", db.diem_cua_nguoi(ds, "de@vgb.vn"), ["TCV", "NVHTN"])
	la("chưa khai", db.diem_cua_nguoi(ds, "moi@vgb.vn"), [])
	ds[2]["bat"] = 0
	la("điểm tắt không tính", db.diem_cua_nguoi(ds, "truc@vgb.vn"), [])
	la("tài khoản rỗng không khớp", db.diem_cua_nguoi(ds, ""), [])


@ca("v631 đọc ô giá gõ tay hay từ Excel: 70000, 70.000, 70,000, '70 000 đ', 70000.0; trống là giá chung; chữ, số lẻ, quá 100 triệu bị chặn")
def _doc_gia():
	la("các cách gõ", [db.doc_gia(x) for x in (70000, "70.000", "70,000", " 70 000 đ", 70000.0, "70000 VND")], [70000] * 6)
	la("trống là giá chung", [db.doc_gia(x) for x in (None, "", "  ", "trống", 0, "0")], [None] * 6)
	for x in ("bảy chục", "70k", 70000.5, 100000000):
		dung("chặn %r" % (x,), _loi(lambda: db.doc_gia(x)) != "")


@ca("v631 máy chủ đặt giá theo điểm: món có giá riêng đổi cả dòng khuyến mãi lẫn dòng hoá đơn; combo và món chưa khai giữ nguyên; điểm giá chung không đụng")
def _ap_gia():
	gia = {"TRA-HL-M": 70000, "KOMB": 80000}
	items = [{"item_code": "TRA-HL-M", "qty": 2, "rate": 95000}, {"item_code": "BANH-MI", "qty": 1, "rate": 30000},
		{"item_code": "KOMB", "qty": 1, "rate": 80000}, {"item_code": "TRA-HL-M", "qty": 1, "rate": 50000, "combo_ma": "CB-1"}]
	rows = [{"item_code": x["item_code"], "rate": x["rate"]} for x in items]
	la("số dòng đổi giá", db.ap_gia_diem(items, rows, gia, db.dong_combo_tao(items)), 1)
	la("dòng khuyến mãi tính trên giá điểm", [x["rate"] for x in items], [70000, 30000, 80000, 50000])
	la("dòng hoá đơn đúng giá điểm", [x["rate"] for x in rows], [70000, 30000, 80000, 50000])
	sua = [{"item_code": "TRA-HL-M", "qty": 1, "rate": 1}]
	db.ap_gia_diem(sua, None, gia)
	la("thu ngân gửi giá tay vẫn về giá điểm", sua[0]["rate"], 70000)
	goc = [{"item_code": "TRA-HL-M", "rate": 95000}]
	la("điểm giá chung: không đổi gì", (db.ap_gia_diem(goc, None, {}), goc[0]["rate"]), (0, 95000))


@ca("v631 Codex PR #532: nhãn combo do máy khách tự gửi (không mã combo) KHÔNG lọt giá điểm; chỉ dòng combo máy chủ xác nhận mới giữ giá")
def _combo_tu_gui():
	gia = {"TEA": 70000}
	# Đúng ca Codex: {item_code: TEA, rate: 1, combo: "anything"} trên điểm giá 70.000.
	items = [{"item_code": "TEA", "qty": 1, "rate": 1, "combo": "anything"}]
	rows = [{"item_code": "TEA", "rate": 1}]
	la("lưu bill: nhãn tự gửi về giá điểm", (db.ap_gia_diem(items, rows, gia, db.dong_combo_tao(items)), items[0]["rate"], rows[0]["rate"]), (1, 70000, 70000))
	la("lưu bill: chỉ dòng có mã combo được miễn", db.dong_combo_tao([{"combo": "x"}, {"combo_ma": "CB-1"}, {"combo_ma": ""}, {}]), {1})
	cu = {
		"D1": {"item_code": "TEA", "vgb_combo_luong": 1, "vgb_combo_ma": "KMCB01"},
		"D2": {"item_code": "TEA", "description": "Trà\n\u25c8 KMCB02 - Combo cũ"},
		"D3": {"item_code": "TEA", "description": "Trà"},
	}
	sua = [{"item_code": "TEA", "rate": 40000, "dong_goc": "D1", "combo": "KMCB01 - Combo"},
		{"item_code": "TEA", "rate": 45000, "dong_goc": "D2", "combo": "KMCB02 - Combo cũ"},
		{"item_code": "TEA", "rate": 1, "dong_goc": "D3", "combo": "anything"},
		{"item_code": "TEA", "rate": 1, "combo": "anything"},
		{"item_code": "TEA", "rate": 1, "dong_goc": "KHONG-CO", "combo": "anything"},
		{"item_code": "TEA", "rate": 40000, "combo_ma": "CB-1", "combo": "KMCB01 - Combo"}]
	mien = db.dong_giu_gia_sua(sua, cu)
	# Codex PR #532 vòng 5: dòng đã lưu (dòng gốc có thật trên hoá đơn) giữ giá đã
	# chốt; dòng 5 có mã combo thì vòng dựng dòng của pos_sua_don kiểm thành phần.
	la("sửa bill: dòng đã lưu và dòng có mã combo giữ giá", mien, {0, 1, 2, 5})
	db.ap_gia_diem(sua, None, gia, mien)
	la("sửa bill: chỉ dòng thêm mới (kể cả mang nhãn combo tự gửi, dòng gốc giả) về giá điểm", [x["rate"] for x in sua], [40000, 45000, 1, 70000, 70000, 40000])


@ca("v631 Codex PR #532 vòng 5: sửa bill nháp sau khi quản lý đổi giá NVH: hai ly trà đã lưu giữ 70.000 (tổng thu ngân xác nhận 140.000 vẫn đúng); ly thêm mới theo giá mới 80.000")
def _sua_giu_gia():
	gia = {"TRA": 80000}
	cu = {"D1": {"item_code": "TRA", "qty": 2, "rate": 70000}}
	sua = [{"item_code": "TRA", "qty": 2, "rate": 70000, "dong_goc": "D1"}, {"item_code": "TRA", "qty": 1, "rate": 70000}]
	mien = db.dong_giu_gia_sua(sua, cu)
	n = db.ap_gia_diem(sua, None, gia, mien)
	la("một dòng (dòng thêm mới) đổi", n, 1)
	la("giá", [x["rate"] for x in sua], [70000, 80000])
	# Codex PR #532 vòng 6: dòng gốc D1 là ly TRA; gửi D1 kèm mã CAKE giá 1 đồng
	# là món thay thế, KHÔNG được giữ giá, phải về giá điểm của CAKE.
	thay = [{"item_code": "CAKE", "qty": 1, "rate": 1, "dong_goc": "D1"}, {"item_code": " TRA ", "qty": 2, "rate": 70000, "dong_goc": "D1"},
		{"item_code": "", "qty": 1, "rate": 1, "dong_goc": "D1"}]
	m_thay = db.dong_giu_gia_sua(thay, cu)
	la("món thay thế và mã rỗng không được giữ giá; cùng mã (lệch khoảng trắng) vẫn giữ", m_thay, {1})
	db.ap_gia_diem(thay, None, {"TRA": 80000, "CAKE": 90000}, m_thay)
	la("món thay thế về giá điểm", [x["rate"] for x in thay], [90000, 70000, 1])
	la("chỉ sửa ghi chú (gửi lại đủ dòng cũ): không đổi gì", db.ap_gia_diem([{"item_code": "TRA", "qty": 2, "rate": 70000, "dong_goc": "D1"}], None, gia,
		db.dong_giu_gia_sua([{"item_code": "TRA", "dong_goc": "D1"}], cu)), 0)


@ca("v631 Codex PR #532 vòng 7: dòng combo lấy giá thành phần từ cấu hình combo trên máy chủ; gửi mã combo thật kèm giá 1 đồng không còn lọt; combo không khai giá cho món thì tính như món thường")
def _gia_combo():
	dong = [{"item_code": "TEA", "gia_goc": 45000, "nhom": ""}, {"item_code": "CAKE", "gia_goc": 0, "nhom": "Bánh"}]
	la("giá thành phần", [db.gia_dong_combo(dong, "TEA"), db.gia_dong_combo(dong, " TEA "), db.gia_dong_combo(dong, "CAKE"), db.gia_dong_combo(dong, "X")], [45000, 45000, 0, 0])
	r = {"item_code": "TEA", "qty": 1, "rate": 1, "combo_ma": "CB-1"}
	la("ca Codex: TEA giá 1 đồng kèm mã combo thật", (db.dat_gia_dong_combo(r, dong), r["rate"], r["combo_ma"]), (1, 45000, "CB-1"))
	dung("vẫn được miễn giá điểm như dòng combo", 0 in db.dong_combo_tao([r]))
	dung("giá đúng thì không tính lệch", db.dat_gia_dong_combo({"item_code": "TEA", "rate": 45000, "combo_ma": "CB-1"}, dong) == 0)
	c = {"item_code": "CAKE", "qty": 1, "rate": 1, "combo_ma": "CB-1"}
	la("combo không khai giá: bỏ dấu combo", (db.dat_gia_dong_combo(c, dong), c["combo_ma"]), (0, ""))
	la("rồi tính như món thường theo giá điểm", (db.dong_combo_tao([c]), db.ap_gia_diem([c], None, {"CAKE": 90000}, db.dong_combo_tao([c])), c["rate"]), (set(), 1, 90000))


@ca("v631 lưu Bảng giá: đọc từng ô đã đổi, ô trống là xoá giá riêng; mã lạ hay giá sai báo rõ món nào")
def _thay_doi():
	hop = {"A", "B", "C"}
	la("đọc", db.chuan_thay_doi('[{"ma":"A","gia":"70.000"},{"ma":"B","gia":""},{"ma":" ","gia":"1"}]', hop), [("A", 70000), ("B", None)])
	la("một món sửa hai lần: lấy lần sau", db.chuan_thay_doi([{"ma": "A", "gia": 1000}, {"ma": "A", "gia": 2000}], hop), [("A", 2000)])
	dung("mã lạ", "Không có món X" in _loi(lambda: db.chuan_thay_doi([{"ma": "X", "gia": 1}], hop)))
	dung("giá sai nói món", _loi(lambda: db.chuan_thay_doi([{"ma": "C", "gia": "abc"}], hop)).startswith("C:"))
	la("vết đổi giá", [db.cau_vet_gia("NVHTN", 95000, 70000), db.cau_vet_gia("NVHTN", 0, 70000), db.cau_vet_gia("NVHTN", 70000, None)],
		["Giá riêng NVHTN: 95.000 -> 70.000", "Giá riêng NVHTN: giá chung -> 70.000", "Giá riêng NVHTN: 70.000 -> giá chung"])


@ca("v631 Nạp Excel: tìm cột theo TÊN (chèn cột, đổi thứ tự vẫn đọc đúng), ô trống là giá chung, thiếu cột hay giá sai báo đúng dòng")
def _excel():
	dau = ["Mã món", "Tên món", "Nhóm món", "Giá chung", "Giá riêng NVHTN"]
	la("tệp tải từ màn", db.doc_bang_excel([dau, ["A", "Trà", "Nước", 95000, 70000], ["B", "Bánh", "Bánh", 30000, None], [None, "", "", None, None]]),
		[{"ma": "A", "gia": 70000}, {"ma": "B", "gia": None}])
	la("chèn cột, đổi thứ tự", db.doc_bang_excel([["Ghi chú", "Giá riêng NVHTN", "Mã món"], ["x", "80.000", "C"]]), [{"ma": "C", "gia": 80000}])
	dung("thiếu cột", "Mã món" in _loi(lambda: db.doc_bang_excel([["Tên", "Giá"], ["A", 1]])))
	dung("giá sai báo dòng", "Dòng 3 (B)" in _loi(lambda: db.doc_bang_excel([dau, ["A", "", "", 1, 1000], ["B", "", "", 1, "abc"]])))
	dung("tệp trống", _loi(lambda: db.doc_bang_excel([])) != "")


@ca("v631 lưu điểm bán: điểm nhận đơn online không bật được giá riêng (máy chủ chỉ tính lại giá bill quầy)")
def _kiem():
	ds = [db._chuan(x) for x in db.MAC_DINH]
	ds[0]["bang_gia"] = "Giá riêng SALES"
	dung("chặn online", "nhận đơn online" in _loi(lambda: db._kiem(ds)))
	ds[0]["bang_gia"] = ""
	ds[2]["bang_gia"] = "Giá riêng NVHTN"
	la("điểm quầy bật được", _loi(lambda: db._kiem(ds)), "")


@ca("v631 Codex PR #532 vòng 3: món KHÔNG có giá riêng phải đúng giá chung danh mục (giá riêng vừa bị bỏ, bảng giá điểm vừa tắt); combo, phí giao, món chưa có giá chung không đụng")
def _gia_chung():
	gia_chung = {"TRA": 95000, "BANH": 30000, "DVBH00001": 1000, "KOMB": 50000, "NVH1": 80000}
	# Quản lý vừa bỏ giá riêng 70.000 của TRA; giỏ cũ còn 70.000.
	items = [{"item_code": "TRA", "rate": 70000}, {"item_code": "BANH", "rate": 30000}, {"item_code": "DVBH00001", "rate": 15000},
		{"item_code": "KOMB", "rate": 40000, "combo_ma": "CB-1"}, {"item_code": "MOI", "rate": 12000}, {"item_code": "NVH1", "rate": 1}]
	rows = [{"item_code": x["item_code"], "rate": x["rate"]} for x in items]
	gia = {"NVH1": 60000}
	mien = db.dong_combo_tao(items)
	n = db.ap_gia_chung(items, rows, gia, mien, gia_chung, ("DVBH00001",))
	la("một dòng lệch giá chung", n, 1)
	la("giỏ và hoá đơn về giá chung; phí giao, combo, món chưa có giá chung, món có giá điểm giữ nguyên",
		([x["rate"] for x in items], [x["rate"] for x in rows]), ([95000, 30000, 15000, 40000, 12000, 1],) * 2)
	tat = [{"item_code": "TRA", "rate": 70000}]
	la("bảng giá điểm vừa tắt (gia rỗng): vẫn về giá chung", (db.ap_gia_chung(tat, None, {}, set(), gia_chung), tat[0]["rate"]), (1, 95000))
	la("giỏ đúng giá: không đổi gì", db.ap_gia_chung([{"item_code": "BANH", "rate": 30000}], None, {}, set(), gia_chung), 0)


@ca("v631: giá món tặng của khuyến mãi và giá gốc thành phần combo không lấy nhầm bảng giá riêng của điểm (Codex PR #532 vòng 4)")
def _gia_tang():
	import types
	import unittest.mock as um

	from vagabond import khuyen_mai as km
	from vagabond.vagabond.doctype.vagabond_combo import vagabond_combo as vc

	hoi = []

	def get_value(dt, flt_, field, **kw):
		hoi.append((dt, flt_))
		return 95000

	with um.patch.object(km.frappe, "db", types.SimpleNamespace(get_value=get_value), create=True):
		la("giá món tặng", km._gia_ban("TRA"), 95000)
		la("giá gốc combo", vc.gia_ban_mon("TRA"), 95000)
	la("cả hai câu đọc loại bảng giá riêng", [h[1].get("price_list") for h in hoi], [["not like", db.TIEN_TO_BANG_GIA + "%"]] * 2)
	la("điều kiện dùng chung", db.loc_bo_bang_rieng(), ["not like", "Giá riêng %"])


@ca("v631 Codex PR #532: câu máy chủ báo giá vừa đổi khớp đúng câu màn quầy dò, và hai đường lưu bill quầy đều gửi cờ gia_theo_diem")
def _cau_gia_doi():
	cau = db.cau_gia_vua_doi(2)
	dung("câu bắt đầu bằng mốc", cau.startswith(db.GIA_VUA_DOI) and "2 món" in cau)
	pos = _doc("public", "js", "bep", "09-tinh-tien-quay.js")
	dung("màn quầy dò đúng mốc", "cau.indexOf('%s')" % db.GIA_VUA_DOI in pos)
	for tep in ("09-tinh-tien-quay.js", "10-bill-quay.js"):
		src = _doc("public", "js", "bep", tep)
		la("%s: mỗi lần gọi tao_don_tay gửi cờ" % tep, src.count("gia_theo_diem: 1"), src.count("'vagabond.ban_hang.tao_don_tay'"))
	b10 = _doc("public", "js", "bep", "10-bill-quay.js")
	la("màn sửa bill gửi cờ một lần", b10.count("goi.gia_theo_diem = 1;"), 1)
	dung("màn sửa bill bắt câu giá vừa đổi trước nhánh OTP", 0 < b10.index("if (await posSuaGiaVuaDoi(e, d.vgb_quay))") < b10.index("if (loi.indexOf('OTP') < 0)"))


def _ham(src, ten):
	cay = ast.parse(src)
	return next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)


def _dong(ham, mau):
	return [n.lineno for n in ast.walk(ham) if isinstance(n, ast.stmt) and mau in ast.unparse(n).split("\n")[0]]


@ca("v631 thứ tự trong máy chủ: lưu bill đặt giá điểm SAU khi chốt quầy và TRƯỚC khi tính khuyến mãi; sửa bill đặt giá TRƯỚC khi xét OTP")
def _thu_tu_may_chu():
	src = _doc("ban_hang.py")
	tao = _ham(src, "tao_don_tay")
	ap = _dong(tao, "doi_gia = doi_combo + diem_ban.ap_gia_diem(items, rows, gia_diem_tao, mien_tao)")
	# Codex PR #532 vòng 7: giá dòng combo đặt theo cấu hình combo của máy chủ
	# TRONG vòng dựng dòng, trước khi dựng dòng hoá đơn, và tính vào số lệch.
	cb_goi = _dong(tao, "doi_combo += _gia_combo_may_chu(r, ma)")
	la("một chỗ đặt giá combo khi lưu bill", len(cb_goi), 1)
	# v638: dựng dòng hoá đơn gom về MỘT hàm ban_hang._dung_dong_mon (màn quầy,
	# màn sửa bill, nhận đơn gọi món tại bàn), kể cả phép kiểm thành phần combo.
	dung("đặt giá combo trước khi dựng dòng hoá đơn", cb_goi[0] < _dong(tao, "rows.append(_dung_dong_mon(r))")[0] < ap[0])
	la("một chỗ đặt giá khi lưu bill", len(ap), 1)
	dung("sau khi chốt quầy", _dong(tao, "quay = _quay_cua_nguon(nguon, quay)")[0] < ap[0])
	dung("trước khi tính khuyến mãi", ap[0] < _dong(tao, "km_kq = _km.tinh_co_khoa(")[0])
	dung("sau vòng kiểm thành phần combo", _dong(tao, "rows.append(_dung_dong_mon(r))")[0] < ap[0])
	dung("vòng dựng dòng kiểm thành phần combo", len(_dong(_ham(src, "_dung_dong_mon"), "if ma not in [x.item_code for x in cb.dong]:")) == 1)
	chan = _dong(tao, "if doi_gia and cint(gia_theo_diem):")
	chung = _dong(tao, "doi_gia += diem_ban.ap_gia_chung(items, rows, gia_diem_tao, mien_tao, gia_chung, (_pg0.MA_PHI_GIAO,))")
	la("đối chiếu giá chung một chỗ", len(chung), 1)
	dung("giá chung đối chiếu sau giá điểm, trước khi chặn", ap[0] < chung[0] < chan[0])
	cay = ast.unparse(tao)
	dung("giá chung chỉ đối chiếu khi màn quầy gửi cờ", "if cint(gia_theo_diem):\n" in cay and cay.index("if cint(gia_theo_diem):") < cay.index("diem_ban.ap_gia_chung("))
	la("chặn khi màn quầy gửi giá cũ", len(chan), 1)
	dung("chặn ngay sau khi đặt giá, trước khuyến mãi", ap[0] < chan[0] < _dong(tao, "km_kq = _km.tinh_co_khoa(")[0])
	dung("tham số mặc định tắt cho màn cũ", any(a.arg == "gia_theo_diem" for a in tao.args.args))
	sua = _ham(src, "pos_sua_don")
	ap2 = _dong(sua, "doi_sua += diem_ban.ap_gia_diem(items, None, gia_diem_sua, mien_sua)")
	cb2 = _dong(sua, "doi_sua = sum((_gia_combo_may_chu(r, (r.get('item_code') or '').strip()) for r in items))")
	la("sửa bill: đặt giá combo theo máy chủ một chỗ, trước bước giữ giá", (len(cb2), cb2[0] < ap2[0]), (1, True))
	la("dòng giữ giá khi sửa bill tính từ dòng gốc trên máy chủ", len(_dong(sua, "mien_sua = diem_ban.dong_giu_gia_sua(items, dong_cu)")), 1)
	chan2 = _dong(sua, "frappe.throw(diem_ban.cau_gia_vua_doi(doi_sua), title='Giá vừa đổi')")
	la("sửa bill: chặn món thêm mới mang giá cũ", len(chan2), 1)
	neu = _dong(sua, "if doi_sua:")
	la("sửa bill: chặn đúng khi có dòng lệch giá", len(neu), 1)
	dung("điều kiện chặn đứng ngay trên câu chặn", neu[0] + 1 == chan2[0])
	dung("chặn sau khi đặt giá, trước khi xét OTP", ap2[0] < chan2[0] < _dong(sua, "can_otp, vi_sao = quyen_quay.can_otp(si, items, giam_gia)")[0])
	dung("sửa bill: tham số mặc định tắt cho màn cũ", any(a.arg == "gia_theo_diem" for a in sua.args.args))
	la("giá điểm khi sửa bill đọc một lần từ quầy của bill", len(_dong(sua, "gia_diem_sua = diem_ban.gia_rieng_cua_quay(si.get('vgb_quay'))")), 1)
	# Codex PR #532 vòng 3: món lẻ thêm mới trùng thành phần combo được kiểm theo CÙNG bảng giá điểm.
	la("kiểm dòng combo dùng giá điểm", len(_dong(sua, "rows.append(giu_dong_sua(si, r, d, gia_diem_sua))")), 1)
	la("một chỗ đặt giá khi sửa bill", len(ap2), 1)
	dung("trước khi xét OTP", ap2[0] < _dong(sua, "can_otp, vi_sao = quyen_quay.can_otp(si, items, giam_gia)")[0])
	cfg = _ham(src, "cau_hinh_ban_hang")
	dung("màn quầy nhận điểm của tài khoản và giá riêng", "diem_cua_toi" in ast.unparse(cfg) and "'gia_rieng': diem_ban.gia_rieng(" in ast.unparse(cfg))


@ca("v631 Codex PR #532: Bảng giá theo điểm trả ảnh món từ danh mục (món chưa có ảnh trả rỗng để màn hiện ô giữ chỗ)")
def _bang_gia_anh():
	import sys
	import types
	import unittest.mock as um

	fr = db.frappe
	hoi = []

	def get_all(dt, **kw):
		hoi.append((dt, kw.get("fields")))
		if dt == "Item Price":
			# BANH có một dòng giá NVH đã khoá hạn (bỏ giá riêng): màn phải hiện giá chung.
			return [{"item_code": "TRA", "price_list_rate": 70000},
				{"item_code": "BANH", "price_list_rate": 50000, "valid_from": "1999-12-01", "valid_upto": "2000-01-01"}]
		return [{"name": "TRA", "item_name": "Trà", "item_group": "Nước", "standard_rate": 95000, "image": "/files/tra.jpg"},
			{"name": "BANH", "item_name": "Bánh", "item_group": "Bánh", "standard_rate": 30000, "image": None}]

	nvh = db._chuan(dict(db.MAC_DINH[2], bang_gia="Giá riêng NVHTN"))
	with um.patch.dict(sys.modules, {"vagabond.ban_hang": types.SimpleNamespace(_kiem_quyen=lambda: None)}), \
			um.patch.object(db, "_diem_co_bang", lambda ma: nvh), um.patch.object(db, "_sua_gia_duoc", lambda: True), \
			um.patch.object(fr, "get_all", get_all, create=True), \
			um.patch.object(fr, "db", types.SimpleNamespace(sql=lambda *a, **k: []), create=True):
		kq = db.bang_gia_diem("NVHTN")
	la("ảnh từng món", [(m["ma"], m["anh"], m["gia_diem"]) for m in kq["mon"]], [("TRA", "/files/tra.jpg", 70000), ("BANH", "", 0)])
	dung("đọc cột ảnh của Item", "image" in [f for dt, f in hoi if dt == "Item"][0])


@ca("v632 Codex PR #532: bỏ giá riêng hay dòng giá thừa thì KHOÁ HẠN tới hôm qua, không xoá dòng giá nào (QT-20); đặt lại giá thì thêm dòng mới")
def _bo_gia_khong_xoa():
	import sys
	import types
	import unittest.mock as um

	hn = "2026-11-03"
	cu = {"name": "IP-1", "item_code": "TRA", "price_list_rate": 70000, "valid_from": "2026-10-01", "valid_upto": None}
	la("bỏ giá riêng: khoá hạn, không xoá", db.ke_hoach_gia([cu], None, hn),
		(70000, None, [{"name": "IP-1", "valid_upto": "2026-11-02"}], False))
	moi = dict(cu, name="IP-2", valid_from=hn)
	la("dòng khai hôm nay rồi bỏ hôm nay: lùi ngày bắt đầu", db.ke_hoach_gia([moi], "", hn)[2],
		[{"name": "IP-2", "valid_upto": "2026-11-02", "valid_from": "2026-11-02"}])
	het = dict(cu, valid_upto="2026-11-02")
	la("dòng đã khoá hạn không còn là giá điểm", db.gia_dang_ap([het], hn), {})
	la("đặt lại giá sau khi đã bỏ: thêm dòng mới, dòng cũ giữ nguyên", db.ke_hoach_gia([het], 80000, hn), (0, None, [], True))
	thua = dict(cu, name="IP-0", valid_from="2026-09-01", modified="2026-09-01")
	gc, sua, khoa, them = db.ke_hoach_gia([thua, cu], 80000, hn)
	la("hai dòng cùng hiệu lực: sửa dòng mới nhất, khoá hạn dòng thừa", (gc, sua, [k["name"] for k in khoa], them), (70000, ("IP-1", 80000), ["IP-0"], False))
	la("giá không đổi thì không làm gì", db.ke_hoach_gia([cu], 70000, hn), (70000, None, [], False))

	# Đúng chuỗi thao tác của quản lý: màn Bảng giá xoá trắng ô giá NVH của Trà rồi bấm Lưu.
	fr = db.frappe
	so = {"IP-1": dict(cu)}
	goi = []

	class Db(types.SimpleNamespace):
		def set_value(self, dt, ten, k, v=None):
			goi.append(("set_value", ten, k if isinstance(k, dict) else {k: v}))
			so[ten].update(k if isinstance(k, dict) else {k: v})

		def commit(self):
			pass

	def get_all(dt, filters=None, **kw):
		if dt == "Item":
			return ["TRA", "BANH"]
		return [dict(r) for r in so.values() if r["item_code"] == (filters or {}).get("item_code", r["item_code"])]

	def get_doc(d):
		def insert(**k):
			goi.append(("insert", d.get("item_code"), d.get("price_list_rate")))
			so["IP-%d" % (len(so) + 1)] = dict(d, name="IP-%d" % (len(so) + 1))
		return types.SimpleNamespace(insert=insert)

	nvh = db._chuan(dict(db.MAC_DINH[2], bang_gia="Giá riêng NVHTN"))
	with um.patch.dict(sys.modules, {"vagabond.ban_hang": types.SimpleNamespace(_kiem_quyen=lambda: None)}), \
			um.patch.object(db, "_diem_co_bang", lambda ma: nvh), um.patch.object(db, "_sua_gia_duoc", lambda: True), \
			um.patch.object(db, "_bao_dam_bang_gia", lambda b: None), um.patch.object(db, "_ghi_vet_gia", lambda *a: None), \
			um.patch.object(db, "_hom_nay", lambda: hn), \
			um.patch.object(fr, "get_all", get_all, create=True), um.patch.object(fr, "get_doc", get_doc, create=True), \
			um.patch.object(fr, "delete_doc", lambda *a, **k: goi.append(("delete_doc",) + a), create=True), \
			um.patch.object(fr, "db", Db(), create=True):
		kq = db.luu_gia("NVHTN", '[{"ma":"TRA","gia":""}]')
		la("lưu: 1 món đổi giá", kq, {"so": 1})
		la("không gọi xoá dòng giá nào", [g for g in goi if g[0] == "delete_doc"], [])
		la("dòng giá cũ còn nguyên giá, chỉ khoá hạn", (so["IP-1"]["price_list_rate"], so["IP-1"]["valid_upto"]), (70000, "2026-11-02"))
		la("Trà về giá chung", db.gia_dang_ap(list(so.values()), hn), {})
		db.luu_gia("NVHTN", '[{"ma":"TRA","gia":"80000"}]')
		la("đặt lại giá: thêm dòng mới, dòng cũ vẫn còn", (len(so), db.gia_dang_ap(list(so.values()), hn)), (2, {"TRA": 80000}))
		la("vẫn không xoá dòng nào", [g for g in goi if g[0] == "delete_doc"], [])
	# Quầy đọc giá điểm qua gia_rieng: dòng đã khoá hạn không còn là giá NVH.
	so2 = [het, dict(cu, name="IP-9", item_code="BANH", price_list_rate=30000)]
	with um.patch.object(db, "theo_ma", lambda ma: nvh), um.patch.object(db, "_hom_nay", lambda: hn), \
			um.patch.object(fr, "get_all", lambda dt, **kw: [dict(r) for r in so2], create=True):
		la("quầy: món đã bỏ giá riêng về giá chung, món khác giữ giá NVH", db.gia_rieng("NVHTN"), {"BANH": 30000})
	cay = ast.parse(_doc("diem_ban.py"))
	goi_ham = [ast.unparse(x.func) for x in ast.walk(cay) if isinstance(x, ast.Call)]
	la("diem_ban không còn lời gọi xoá nào", [g for g in goi_ham if "delete" in g], [])
	la("một chỗ đọc dòng giá của bảng giá điểm", sum(1 for x in ast.walk(cay) if isinstance(x, ast.Call)
		and ast.unparse(x.func) == "frappe.get_all" and x.args and getattr(x.args[0], "value", None) == "Item Price"), 1)


@ca("v631 Tạo mặt hàng: ô giá riêng NVH lưu vào bảng giá của điểm sau khi mở mã; gõ sai, điểm giá chung, loại không bán thì chặn TRƯỚC khi mở mã")
def _tao_mon():
	import sys
	import types
	import unittest.mock as um

	# Cùng cách thu_v524: Frappe giả không có frappe.model.naming.
	if "vagabond.danh_muc" not in sys.modules and "frappe.model.naming" not in sys.modules:
		sys.modules["frappe.model.naming"] = types.SimpleNamespace(getseries=lambda *a: "00001")
	from vagabond import danh_muc as dm

	dat, tao = [], []
	nvh = db._chuan(dict(db.MAC_DINH[2], bang_gia="Giá riêng NVHTN"))
	tcv = db._chuan(db.MAC_DINH[1])

	class Doc(types.SimpleNamespace):
		def set(self, k, v):
			setattr(self, k, v)

		def insert(self):
			self.name = self.item_code
			tao.append(self.name)

	fr = dm.frappe
	vas = [
		um.patch.object(dm, "_kiem_quyen", lambda: None), um.patch.object(dm, "_duoc_tao", lambda: True),
		um.patch.object(dm, "_ma_moi", lambda tt: tt + "0001"), um.patch.object(dm, "_dvt_quen", lambda n: "Ly"),
		um.patch.object(dm, "_co_truong", lambda *a: False),
		um.patch.object(fr.db, "exists", lambda *a, **k: True, create=True),
		um.patch.object(fr.db, "get_value", lambda *a, **k: 0, create=True),
		um.patch.object(fr.db, "get_default", lambda *a, **k: "", create=True),
		um.patch.object(fr.db, "commit", lambda *a, **k: None, create=True),
		um.patch.object(fr, "new_doc", lambda dt: Doc(flags=types.SimpleNamespace()), create=True),
		um.patch.object(db, "theo_ma", lambda ma: {"NVHTN": nvh, "TCV": tcv}.get(str(ma).upper())),
		um.patch.object(db, "dat_gia_diem", lambda d, mon, gia: dat.append((d["ma"], mon, gia)) or True),
	]
	for v in vas:
		v.start()
	try:
		kq = dm.tao(nhom="Nước", loai="thanh_pham", ten="Trà Hoa Lài", gia_ban="95000", tien_to="TRA", bo_qua_trung=1,
			gia_diem='{"NVHTN": "70.000", "TCV": ""}')
		la("mở mã rồi lưu giá NVH", (tao, dat, kq["gia_diem"]), (["TRA0001"], [("NVHTN", "TRA0001", 70000)], {"NVHTN": 70000}))
		for gd, mo in (('{"NVHTN": "bảy chục"}', "không phải số"), ('{"TCV": "70000"}', "đang bán giá chung")):
			del tao[:], dat[:]
			loi = _loi(lambda: dm.tao(nhom="Nước", loai="thanh_pham", ten="Trà Hoa Lài", tien_to="TRA", bo_qua_trung=1, gia_diem=gd))
			dung("%s: %s" % (mo, loi), mo in loi)
			la("chặn trước khi mở mã", (tao, dat), ([], []))
		loi = _loi(lambda: dm.tao(nhom="Bột", loai="nvl", ten="Bột mì số 13", tien_to="BOT", bo_qua_trung=1, gia_diem='{"NVHTN": 1000}'))
		dung("loại không bán: " + loi, "không bán" in loi and not tao)
	finally:
		for v in reversed(vas):
			v.stop()
