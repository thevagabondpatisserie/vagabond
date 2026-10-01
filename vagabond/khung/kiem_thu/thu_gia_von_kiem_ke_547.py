# -*- coding: utf-8 -*-
"""v547: giá vốn phiếu kiểm kê, phần thuần. Ca chạy thật ở
kiem_that/gia_von_kiem_ke_547.py (phiếu Desk nạp giá 0 như phiếu của Kiên)."""

from vagabond import gia_von_kiem_ke as gv
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("v547: dòng có số lượng mà giá trống hoặc 0 thì phải điền; giá 0 cố ý (cho phép định giá 0) thì giữ")
def _can_dien():
	dung("giá 0 như phiếu Kiên", gv.can_dien(5000, 0))
	dung("giá trống", gv.can_dien(5, None))
	dung("giá chuỗi rỗng", gv.can_dien(5, ""))
	dung("đã có giá thì giữ", not gv.can_dien(5, 400))
	dung("đếm 0 thì không cần giá", not gv.can_dien(0, 0))
	dung("cho phép định giá 0 thì giữ", not gv.can_dien(5, 0, 1))


@ca("v547: chọn giá theo thứ tự sổ kho đúng kho, kho khác, giá mua, giá chung; lấy cái đầu tiên lớn hơn 0")
def _chon_gia():
	la("sổ kho đúng kho đứng trước", gv.chon_gia([("so_kho", 400), ("kho_khac", 380), ("gia_mua", 410)]), (400.0, "so_kho"))
	la("kho chưa có giá thì lấy kho khác", gv.chon_gia([("so_kho", 0), ("kho_khac", 6755), ("gia_mua", 0)]), (6755.0, "kho_khac"))
	la("chưa từng có trong kho thì lấy giá mua", gv.chon_gia([("so_kho", 0), ("kho_khac", 0), ("gia_mua", 1500), ("gia_ma", 900)]), (1500.0, "gia_mua"))
	la("chỉ còn giá chung của mã", gv.chon_gia([("so_kho", None), ("kho_khac", 0), ("gia_mua", 0), ("gia_ma", 900)]), (900.0, "gia_ma"))
	la("không có gì thì để trống cho ERPNext chặn", gv.chon_gia([("so_kho", 0), ("kho_khac", 0), ("gia_mua", None), ("gia_ma", 0)]), (None, None))
	la("thứ tự nguồn cố định", gv.NGUON, ("so_kho", "kho_khac", "gia_mua", "gia_ma"))
