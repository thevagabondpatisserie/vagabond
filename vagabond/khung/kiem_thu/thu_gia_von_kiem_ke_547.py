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


@ca("v547 Codex #401 F1: dòng đã tra được giá hiện tại mà gõ 0 là chủ ý định giá lại, không điền")
def _giu_0_chu_y():
	dung("giá hiện tại 400, gõ 0: giữ", not gv.can_dien(10, 0, 0, 400))
	dung("chưa tra giá hiện tại (dòng nạp một lượt như phiếu Kiên): điền", gv.can_dien(10, 0, 0, 0))
	dung("giá hiện tại 400 nhưng ô giá trống: vẫn điền", gv.can_dien(10, None, 0, 400))


@ca("v547 Codex #401 F2: mốc thời gian phiếu để chặn giá tương lai")
def _moc():
	la("đủ ngày giờ", gv.moc("2026-09-25", "08:30:00"), "2026-09-25 08:30:00")
	la("giờ thiếu giây", gv.moc("2026-09-25", "08:30"), "2026-09-25 08:30:00")
	la("thiếu giờ thì cuối ngày", gv.moc("2026-09-25"), "2026-09-25 23:59:59")
	la("thiếu ngày thì không chặn", gv.moc(None), None)


@ca("v547 Codex #401 vòng 3: sổ kho đọc lỗi thì NÉM lỗi, không coi như kho chưa có giá")
def _so_kho_loi_thi_nem():
	import sys
	import types

	cu = {k: sys.modules.get(k) for k in ("erpnext", "erpnext.stock", "erpnext.stock.utils")}
	gia = types.ModuleType("erpnext.stock.utils")

	def _hong(*a, **k):
		raise RuntimeError("sổ kho đọc lỗi")

	gia.get_stock_balance = _hong
	sys.modules["erpnext"] = types.ModuleType("erpnext")
	sys.modules["erpnext.stock"] = types.ModuleType("erpnext.stock")
	sys.modules["erpnext.stock.utils"] = gia
	try:
		try:
			gv._gia_so_kho("M", "Kho D1", "2026-09-30", "08:00:00")
			nem = False
		except RuntimeError:
			nem = True
		dung("lỗi sổ kho nổi lên, không thành giá 0", nem)
		gia.get_stock_balance = lambda *a, **k: (5, 400)
		la("đọc được thì trả giá", gv._gia_so_kho("M", "Kho D1", "2026-09-30", "08:00:00"), 400.0)
	finally:
		for k, v in cu.items():
			if v is None:
				sys.modules.pop(k, None)
			else:
				sys.modules[k] = v
