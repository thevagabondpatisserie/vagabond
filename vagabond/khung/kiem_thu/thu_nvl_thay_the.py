# -*- coding: utf-8 -*-
"""Bảng Nguyên liệu thay thế: cột tên, cột đếm công thức, chip cảnh báo.

Khải đề nghị 28/08/2026: bảng chỉ hiện mã, không hiện tên. Anh Việt giao
thêm: dựng luôn các cột và chip lọc hữu ích nhất để Khải ít nhầm nhất.

Các ca dưới đây bám vào bốn điều đo được trên site hôm đó, vì mỗi điều là
một kiểu nhầm thật chứ không phải giả định:

* Năm trong bảy mã đang khai có tồn 0.
* Ba mã chưa có giá vốn, tức chưa từng nhập lô nào.
* Giá vốn giữa các mã chênh nhau từ vài phần trăm tới hơn ba mươi.
* Một mã nằm trong 128 dòng công thức.
"""

import io
import os

from vagabond import nvl_thay_the as n
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _py(ten):
	goc = os.path.dirname(os.path.abspath(n.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


def _mon(**kw):
	"""Một món sạch sẽ: có hàng, có giá, cùng đơn vị, cho phép thay."""
	d = {"uom": "Gram", "tat": 0, "cho_thay": 1, "gia": 230.0, "ton": 100000.0}
	d.update(kw)
	return d


# --------------------------------------------------------- lệch giá vốn


@ca("lệch giá vốn tính theo phần trăm so với món gốc")
def _():
	# Bơ Avonmore 230 thay bằng bơ Anchor 252, đúng hai mã thật trên site.
	l = n.lech_gia_phan_tram(230, 252)
	la("tăng gần 10 phần trăm", round(l, 1), 9.6)
	la("giảm thì ra số âm", round(n.lech_gia_phan_tram(252, 230), 1), -8.7)


@ca("một bên chưa có giá thì KHÔNG so, chứ không nói lệch 100 phần trăm")
def _():
	la("món thay thế chưa có giá", n.lech_gia_phan_tram(230, 0), None)
	la("món gốc chưa có giá", n.lech_gia_phan_tram(0, 230), None)


@ca("câu chênh giá viết cho người đọc")
def _():
	la("tăng", n.chu_lech_gia(230, 252), "+9.6%")
	la("chưa có giá", n.chu_lech_gia(230, 0), "Chưa có giá")
	la("ngang giá", n.chu_lech_gia(230, 230), "Ngang giá")
	la("gốc chưa có giá", n.chu_lech_gia(0, 230), "Chưa so được")


@ca("câu tồn kho nói Hết hàng chứ không nói số 0 trơ trọi")
def _():
	la("hết", n.chu_ton(0, "Gram"), "Hết hàng")
	la("âm cũng là hết", n.chu_ton(-5, "Gram"), "Hết hàng")
	la("còn hàng", n.chu_ton(102982, "Gram"), "102,982 Gram")


# ------------------------------------------------------------- soát cặp


@ca("cặp sạch thì không có cảnh báo nào")
def _():
	la("sạch", n.soat_cap(_mon(), _mon(), so_bom=5), [])
	la("mức", n.muc_cua([]), n.MUC_DUNG_DUOC)


@ca("lệch đơn vị là lỗi CHẶN, vì thay vào là sai số lượng")
def _():
	ds = n.soat_cap(_mon(uom="Gram"), _mon(uom="Kg"), so_bom=5)
	dung("phải bắt lệch đơn vị", "lech_don_vi" in ds)
	la("mức phải là chặn", n.muc_cua(ds), n.MUC_CHAN)


@ca("món thay thế đã tắt trong danh mục cũng là lỗi chặn")
def _():
	ds = n.soat_cap(_mon(), _mon(tat=1), so_bom=5)
	dung("phải bắt món tắt", "mon_tat" in ds)
	la("mức", n.muc_cua(ds), n.MUC_CHAN)


@ca("món gốc chưa bật cho phép thay thì khai xong cũng nằm im")
def _():
	# Ô allow_alternative_item nằm trên món GỐC. Chưa bật thì ERPNext không
	# đề nghị hàng thay thế lúc phát lệnh sản xuất.
	ds = n.soat_cap(_mon(cho_thay=0), _mon(), so_bom=5)
	dung("phải bắt", "goc_khong_cho_thay" in ds)
	la("mức", n.muc_cua(ds), n.MUC_CHAN)


@ca("không biết cờ cho phép thay thì THÔI KHÔNG KIỂM, không báo bừa")
def _():
	ds = n.soat_cap(_mon(cho_thay=None), _mon(), so_bom=5)
	la("không được báo", "goc_khong_cho_thay" in ds, False)


@ca("món thay thế hết hàng là Cần xem, không phải chặn")
def _():
	# Khai trước, mua sau là chuyện bình thường. Chặn ở đây là cấm người ta
	# chuẩn bị.
	ds = n.soat_cap(_mon(), _mon(ton=0), so_bom=5)
	dung("phải bắt hết hàng", "het_hang" in ds)
	la("mức", n.muc_cua(ds), n.MUC_CAN_XEM)


@ca("món thay thế chưa có giá thì cảnh báo, vì thay vào là giá vốn tụt")
def _():
	ds = n.soat_cap(_mon(), _mon(gia=0), so_bom=5)
	dung("phải bắt", "chua_co_gia" in ds)
	# Chưa có giá thì không so được, nên KHÔNG được báo thêm lệch giá.
	la("không báo kèm lệch giá", "lech_gia" in ds, False)


@ca("chênh giá vốn quá ngưỡng thì nói ra")
def _():
	ds = n.soat_cap(_mon(gia=120), _mon(gia=165), so_bom=5)
	dung("kem 120 thay bang kem 165 la lech 37 phan tram", "lech_gia" in ds)
	ds2 = n.soat_cap(_mon(gia=230), _mon(gia=235), so_bom=5)
	la("chênh 2 phần trăm thì im", "lech_gia" in ds2, False)


@ca("món gốc chưa nằm trong công thức nào thì nhắc")
def _():
	ds = n.soat_cap(_mon(), _mon(), so_bom=0)
	dung("phải nhắc", "chua_dung_bom" in ds)


@ca("thiếu nhiều thứ thì kể HẾT, và mức lấy cái nặng nhất")
def _():
	ds = n.soat_cap(_mon(uom="Gram"), _mon(uom="Kg", ton=0, gia=0), so_bom=0)
	for m in ("lech_don_vi", "het_hang", "chua_co_gia", "chua_dung_bom"):
		dung("phải kể %s" % m, m in ds)
	la("mức nặng nhất thắng", n.muc_cua(ds), n.MUC_CHAN)


@ca("thứ tự kể cảnh báo cố định, không đổi theo thứ tự phát hiện")
def _():
	# Hai lần chạy trên cùng dữ liệu phải ra cùng một chuỗi, không thì ô
	# tóm tắt nhấp nháy mỗi lần quét lại mà nội dung không đổi.
	a = n.soat_cap(_mon(uom="Gram"), _mon(uom="Kg", ton=0), so_bom=0)
	b = n.soat_cap(_mon(uom="Gram"), _mon(uom="Kg", ton=0), so_bom=0)
	la("hai lần như một", a, b)
	la("theo đúng bảng CANH_BAO", a, [m for m in n.CANH_BAO if m in set(a)])


@ca("mọi mã cảnh báo đều có câu tiếng Việt và một mức hợp lệ")
def _():
	for m, (chu, muc) in n.CANH_BAO.items():
		dung("mã %s phải có câu" % m, chu)
		dung("mã %s phải có mức hợp lệ" % m, muc in n.MUC)


@ca("câu tóm tắt và câu chi tiết không bỏ sót cảnh báo nào")
def _():
	ds = n.soat_cap(_mon(uom="Gram"), _mon(uom="Kg", ton=0, gia=0), so_bom=0)
	tom = n.cau_tom_tat(ds)
	chi = n.cau_chi_tiet(ds)
	la("tóm tắt phải có đủ %d phần" % len(ds), tom.count(",") + 1, len(ds))
	la("chi tiết mỗi cảnh báo một dòng", len(chi.splitlines()), len(ds))


@ca("cặp sạch thì câu nói rõ là dùng được, không để trống")
def _():
	dung("tóm tắt", n.cau_tom_tat([]))
	dung("chi tiết", n.cau_chi_tiet([]))


# ------------------------------------------------- nối vào hệ đúng chỗ


@ca("hook chỉ TRỢ GIÚP, không được chặn ai lưu cặp thay thế")
def _():
	m = _py("nvl_thay_the.py")
	# Bảng này là ô gợi ý. Ném lỗi ở đây là chặn Khải khai nguyên liệu.
	la("không được có frappe.throw trong hook khi luu", "def khi_luu" in m, True)
	doan = m.split("def khi_luu")[1].split("\ndef ")[0]
	la("khong duoc nem loi", "frappe.throw" in doan, False)
	dung("phải bọc lỗi và ghi Error Log", "log_error" in doan)


@ca("hook và nhịp đêm đều đã nối vào hooks.py")
def _():
	m = _py("hooks.py")
	dung("hook luc luu", "vagabond.nvl_thay_the.khi_luu" in m)
	dung("nhip dem", "vagabond.nvl_thay_the.quet_tu_dong" in m)


@ca("trường tự thêm khai trong mã nguồn, không bấm tay trên Desk")
def _():
	m = _py("truong_tu_them.py")
	dung("phai dung nhom nvl_thay_the", "nvl_thay_the.TRUONG_MOI" in m)


@ca("mọi trường đều là ô máy điền, người không gõ tay được")
def _():
	for o in n.TRUONG_MOI["Item Alternative"]:
		if o["fieldtype"] in ("Section Break", "Column Break"):
			continue
		dung("ô %s phải chỉ đọc" % o["fieldname"], o.get("read_only"))
		dung("ô %s không được chép sang bản ghi khác" % o["fieldname"], o.get("no_copy"))


@ca("có đủ cột tên, cột đếm công thức, và chip lọc trên danh sách")
def _():
	o = dict((x["fieldname"], x) for x in n.TRUONG_MOI["Item Alternative"])
	# Đúng hai thứ Khải xin: tên cạnh mã món, và tên cạnh mã món thay thế.
	dung("ten mon hien tren danh sach", o["vgb_ten_mon"].get("in_list_view"))
	dung("ten mon thay the hien tren danh sach", o["vgb_ten_thay_the"].get("in_list_view"))
	dung("ten mon dat ngay sau ma mon", o["vgb_ten_mon"]["insert_after"] == "item_code")
	dung("ten thay the dat ngay sau ma thay the",
		o["vgb_ten_thay_the"]["insert_after"] == "alternative_item_code")
	dung("co cot dem cong thuc", "vgb_so_bom" in o)
	# Ba chip lọc trên thanh bộ lọc của Desk.
	for f in ("vgb_muc", "vgb_het_hang", "vgb_lech_don_vi"):
		dung("%s phai la chip loc" % f, o[f].get("in_standard_filter"))


@ca("không dùng Client Script, toàn bộ nằm trong mã nguồn")
def _():
	# 43 Client Script trong cơ sở dữ liệu là nguồn của mọi vụ lệch app và
	# Desk, ghi trong tài liệu rà soát 27/08. Không thêm cái thứ 44.
	#
	# Soi bằng cây cú pháp chứ không tìm chuỗi trong tệp: tệp này có nhắc
	# tên "Client Script" trong phần ghi chú đầu tệp để nói VÌ SAO không
	# dùng nó, tìm chuỗi thô sẽ bắt nhầm chính câu giải thích đó.
	import ast

	cay = ast.parse(_py("nvl_thay_the.py"))
	tai_lieu = set()
	for nut in ast.walk(cay):
		if isinstance(nut, (ast.Module, ast.FunctionDef, ast.ClassDef)):
			d = ast.get_docstring(nut, clean=False)
			if d:
				tai_lieu.add(d)
	for nut in ast.walk(cay):
		if not isinstance(nut, ast.Constant) or not isinstance(nut.value, str):
			continue
		if nut.value in tai_lieu:
			continue
		for t in ("Client Script", "listview_settings"):
			la("khong duoc dung %s trong ma" % t, t in nut.value, False)


@ca("nhịp đêm ghi thẳng, không save để khỏi đội version và bắn thông báo")
def _():
	m = _py("nvl_thay_the.py")
	doan = m.split("def quet_lai")[1].split("\ndef ")[0]
	dung("phai dung db.set_value", "frappe.db.set_value" in doan)
	dung("phai giu nguyen ngay sua", "update_modified=False" in doan)
	la("khong duoc goi save", ".save(" in doan, False)


@ca("chỉ đếm công thức đã ghi sổ và còn hoạt động")
def _():
	m = _py("nvl_thay_the.py")
	doan = m.split("def _dem_bom")[1].split("\ndef ")[0]
	# Đếm cả bản nháp và bản cũ thì con số phồng lên, Khải nhìn tưởng sửa
	# một cặp là chạm hàng trăm công thức trong khi phần lớn đã nghỉ.
	dung("phai loc docstatus 1", '"docstatus": 1' in doan)
	dung("phai loc is_active", '"is_active": 1' in doan)
