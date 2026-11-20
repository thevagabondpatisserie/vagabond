# -*- coding: utf-8 -*-
"""PR 0 việc "Nghệ sĩ công nghệ": công cụ thống kê màn và kiểu hiển thị.

cong_cu/thong_ke_ui_nghe_si.py lập danh mục màn làm MẪU SỐ cho "đạt 100%"
của các PR đổi giao diện. Danh mục sót màn thì một màn chưa chuyển vẫn lọt
qua cổng, nên bộ ca này chốt ba điều:

  1. các phép đọc mã (tách hàm, định tuyến, emoji, khoảng lẻ) đúng trên mẫu nhỏ;
  2. bảng nhóm đọc bằng biểu thức chính quy TRÙNG bảng thật do node chạy ra
     (thu_gom_nhom_565 đã nói vì sao biểu thức chính quy dễ sai chỗ này);
  3. trên mã thật: mọi hàm màn đều có trong danh mục, mọi nhóm trang chủ đều
     có PR nhận. Thêm nhóm mới mà quên xếp PR thì đỏ ngay.

Toàn phép thuần, không Frappe, không requests. Không so tệp docs đã ghi:
SHA danh mục ghi trong từng báo cáo PR mới là thứ chốt bản nào đang dùng.
"""

import importlib.util
import os
import re
from collections import OrderedDict

from vagabond.khung.kiem_thu import thu_gom_nhom_565
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _cong_cu():
	duong = os.path.join(GOC, "cong_cu", "thong_ke_ui_nghe_si.py")
	spec = importlib.util.spec_from_file_location("thong_ke_ui_nghe_si", duong)
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


MAU = OrderedDict([
	("01-a.js", "function go(f) { }\nfunction vgbGo(k) {\n  if (k === 'A') return go(scrA);\n  if (k === 'B') { x = 1; return go(scrB); }\n  if (k === 'N') { location.href = '/ngoai'; return; }\n}\n"),
	("02-b.js", "async function scrA() {\n  frame('Màn A', '<div class=\"card\" style=\"padding:10px 16px;font-size:12px;color:#c2361f\">📌</div>', { footer: 'x' });\n  var r = await api('x');\n  go(scrCon);\n}\nfunction scrB() { frame(ten, '<input id=\"a\">'); hoiCo('a', 'b'); }\nfunction scrCon() { frame('Con', ''); }\nfunction scrLac() { frame('Lạc', ''); }\n"),
])


@ca("thống kê UI: tách hàm cột 0, giữ đúng phần và dòng")
def _():
	m = _cong_cu()
	ham = m.tach_ham(MAU)
	la("số hàm", sorted(ham), ["go", "scrA", "scrB", "scrCon", "scrLac", "vgbGo"])
	la("phần của scrA", ham["scrA"]["tep"], "02-b.js")
	la("dòng của scrB", ham["scrB"]["dong"], 6)


@ca("thống kê UI: đọc vgbGo ra khoá và màn, khoá mở trang ngoài thì không có màn")
def _():
	m = _cong_cu()
	t = m.doc_dinh_tuyen(m.tach_ham(MAU)["vgbGo"]["than"])
	la("khoá A", t["A"], ["scrA"])
	la("khoá B", t["B"], ["scrB"])
	la("khoá N", t["N"], [])


@ca("thống kê UI: màn con theo nhóm của màn mẹ, màn không ai mở thì chưa xếp")
def _():
	m = _cong_cu()
	ham = m.tach_ham(MAU)
	tuyen = m.doc_dinh_tuyen(ham["vgbGo"]["than"])
	canh, tong_dai = m.do_thi(ham)
	kq = m.xep_nhom(ham, [("X", "Nhóm X", ["A"]), ("Y", "Nhóm Y", ["B"])], tuyen, canh, tong_dai)
	la("scrA", kq.get("scrA"), "X")
	la("scrCon theo mẹ", kq.get("scrCon"), "X")
	la("scrB", kq.get("scrB"), "Y")
	la("scrLac", kq.get("scrLac"), None)


@ca("thống kê UI: thành phần, hộp thoại và trạng thái cần kiểm của một màn")
def _():
	m = _cong_cu()
	ham = m.tach_ham(MAU)
	co, hop, rieng = m.thanh_phan(ham["scrA"]["than"])
	dung("scrA có thanh đáy", "thanh đáy" in co)
	dung("scrA có thẻ", "thẻ" in co)
	tt = m.trang_thai(ham["scrA"]["than"], co, hop, rieng)
	dung("scrA phải kiểm đang tải", "đang tải" in tt)
	co, hop, rieng = m.thanh_phan(ham["scrB"]["than"])
	dung("scrB có ô nhập", "ô nhập" in co)
	la("scrB gọi hộp thoại", hop, ["hoiCo"])
	tt = m.trang_thai(ham["scrB"]["than"], co, hop, rieng)
	dung("scrB phải kiểm bàn phím ảo", "bàn phím ảo" in tt)
	dung("scrB phải kiểm hộp thoại mở", "hộp thoại mở" in tt)
	la("tiêu đề động", m.tieu_de(ham["scrB"]["than"]), ["(động)"])


@ca("thống kê UI: đếm emoji, cỡ chữ, khoảng lẻ; chữ tiếng Việt không bị tính là emoji")
def _():
	m = _cong_cu()
	dung("📌 là emoji", m.la_emoji("📌"))
	dung("chữ ế không phải emoji", not m.la_emoji("ế"))
	dung("dấu gạch không phải emoji", not m.la_emoji("-"))
	tung, tong = m.thong_ke_kieu(MAU)
	la("style trong thẻ", tung["02-b.js"]["style"], 1)
	la("emoji", tung["02-b.js"]["emoji"], 1)
	la("khoảng lẻ: 10 lẻ, 16 chẵn", dict(tong["khoang_le"]), {"10": 1})
	la("cỡ chữ", dict(tong["co_chu"]), {"12": 1})
	la("vai của màu", dict(tong["mau_vai"]["#c2361f"]), {"chữ": 1})


@ca("thống kê UI: bảng nhóm đọc bằng biểu thức chính quy trùng bảng thật của node")
def _():
	m = _cong_cu()
	that = thu_gom_nhom_565._bang_nhom()["nhom"]
	doc = m.doc_nhom(thu_gom_nhom_565._ma_js())
	la("số nhóm", len(doc), len(that))
	for (k, ten, khoa), nh in zip(doc, that):
		la("khoá nhóm", k, nh["k"])
		la("tên nhóm " + k, ten, nh["ten"])
		if khoa != ["DM:*"]:
			la("các ô của nhóm " + k, khoa, nh["keys"])


@ca("thống kê UI: trên mã thật, mọi nhóm trang chủ có PR nhận và mọi hàm màn có trong danh mục")
def _():
	m = _cong_cu()
	cac_phan = m.doc_cac_phan()
	dm = m.lap_danh_muc(cac_phan)
	for k, ten, _khoa in dm["nhom"]:
		dung("nhóm %s (%s) phải có PR nhận trong PR_THEO_NHOM" % (k, ten), k in m.PR_THEO_NHOM)
	trong_ma = set()
	for ma in cac_phan.values():
		trong_ma.update(re.findall(r"^(?:async\s+)?function\s+(scr[A-Z]\w*)\s*\(", ma, re.M))
	trong_dm = set(x["ten"] for x in dm["man"])
	la("màn sót khỏi danh mục", sorted(trong_ma - trong_dm), [])
	dung("danh mục có trên 200 màn", len(trong_dm) > 200)
	van_ban = m.viet_danh_muc(dm)
	for ten in sorted(trong_dm):
		dung("bảng in ra phải có dòng của " + ten, ("| %s |" % ten) in van_ban)
	dung("tài liệu sinh ra không có gạch dài", chr(0x2014) not in van_ban and chr(0x2013) not in van_ban)
