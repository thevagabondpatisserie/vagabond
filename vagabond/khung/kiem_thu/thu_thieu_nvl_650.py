# -*- coding: utf-8 -*-
"""v650 (anh Việt 12/11/2026, LSX-121126-000604): hoàn tất lệnh mà kho bếp thiếu
nguyên liệu thì câu báo phải là việc cần làm, không phải câu dịch máy của ERPNext
"Cần 0.361 đơn vị Món ... để hoàn tất giao dịch này".

Chạy THẬT hoan_tat_phieu trên kho giả của bộ v648 (thu_lay_bu_kho_tong_648):
phiếu hoàn tất ném lỗi thiếu tồn lúc submit như ERPNext. Máy phải lùi điểm
lưu TRƯỚC rồi mới đọc tồn (bài học Codex #498), giữ đúng lớp lỗi gốc.
"""
import sys
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")

from vagabond import kho_san_xuat as ksx  # noqa: E402
from vagabond import tin_kho  # noqa: E402
from vagabond.khung.kiem_thu.thu_lay_bu_kho_tong_648 import BEP, _He  # noqa: E402


class NegativeStockError(ksx.frappe.ValidationError):
	"""Đứng thay lớp lỗi thiếu tồn của ERPNext (lớp con của ValidationError)."""


class _Dong(dict):
	__getattr__ = dict.get


CAU_MAY = "Cần 0.361 đơn vị Món NVLT00318: Cacao Mass 100%, Crea tại Kho Pastry - Nguyên liệu - TV để hoàn tất giao dịch này."


def _chay(loi, ton=None):
	"""Ghi phiếu hoàn tất WO-1 (cần 100 g bột, 50 g bơ); submit phiếu Manufacture ném `loi`."""
	he = _He(ton if ton is not None else {("BOT", BEP): 30, ("BO", BEP): 50})
	goc = he._doc
	vet = []

	def _doc(g):
		d = goc(g)
		# Dòng phiếu thật là Document (đọc thuộc tính lẫn .get); make_stock_entry
		# của ERPNext điền sẵn transfer_qty theo đơn vị kho (0,1 Kg x 1000 = 100 g).
		d.items = [_Dong(x, transfer_qty=x.get("transfer_qty") or x.get("qty", 0) * (x.get("conversion_factor") or 1))
			for x in (getattr(d, "items", None) or [])]
		if d.purpose == "Manufacture":
			def submit():
				vet.append("submit")
				raise loi
			d.submit = submit
		return d

	def _throw(msg, *a, exc=None, title=None, **k):
		raise (exc or ksx.frappe.ValidationError)(msg)

	doc_ton = he.get_all

	def get_all(dt, filters=None, fields=None, **k):
		vet.append("đọc tồn sau " + (he.diem[-1][0] if he.diem else "không"))
		# Bin thật có cả giá vốn; kho giả v648 chỉ có tồn.
		return [_Dong(item_code=b.item_code, warehouse=b.warehouse, actual_qty=b.actual_qty, valuation_rate=1)
			for b in doc_ton(dt, filters=filters, fields=fields, **k)]

	he._doc = _doc
	he.get_all = get_all
	with patch.object(ksx.frappe, "throw", _throw), \
			patch.object(tin_kho.frappe, "get_all", get_all, create=True), \
			patch.object(ksx.frappe, "local", ksx.frappe.local):
		try:
			he.chay()
		except Exception as e:  # noqa: BLE001
			return e, he, vet
	return None, he, vet


@ca("v650 hoàn tất thiếu nguyên liệu (đúng câu ERPNext dịch máy): báo kho nào thiếu món gì, việc phải làm; giữ lớp lỗi gốc; lùi điểm lưu TRƯỚC khi đọc tồn")
def _():
	e, he, vet = _chay(NegativeStockError(CAU_MAY))
	la("lớp lỗi gốc", type(e).__name__, "NegativeStockError")
	cau = str(e)
	dung("không còn câu dịch máy", "để hoàn tất giao dịch này" not in cau)
	dung("nói lệnh", "Chưa hoàn tất được lệnh WO-1" in cau)
	dung("nói kho, không đuôi công ty", "kho Pastry - Nguyên liệu chưa đủ nguyên liệu" in cau)
	dung("nói món, số cần, kho đang có", "Bột mì cần 100 Gram (kho đang có 30)" in cau)
	dung("món đủ không kể", "Bơ" not in cau)
	dung("việc phải làm", "Xin chuyển nguyên liệu" in cau and "bấm Hoàn tất lại" in cau)
	la("điểm lưu đặt rồi lùi", he.diem, [("diem", ksx.DIEM_HOAN_TAT), ("lui", ksx.DIEM_HOAN_TAT)])
	la("đọc tồn SAU khi lùi", vet[-1], "đọc tồn sau lui")


@ca("v650 lỗi khác (không phải thiếu tồn) đi nguyên, không lùi điểm lưu; lỗi chết giao dịch không đụng điểm lưu")
def _():
	e, he, vet = _chay(ksx.frappe.ValidationError("Lệnh đã đóng"))
	la("đi nguyên", str(e), "Lệnh đã đóng")
	la("không lùi", he.diem, [("diem", ksx.DIEM_HOAN_TAT)])
	Chet = type("OperationalError", (Exception,), {})
	e, he, vet = _chay(Chet(1213, "Deadlock found when trying to get lock"))
	la("đi nguyên lớp", type(e).__name__, "OperationalError")
	la("không lùi", he.diem, [("diem", ksx.DIEM_HOAN_TAT)])


@ca("v650 tin_kho nhận ra câu thiếu tồn tiếng Việt dịch máy kể cả khi lớp lỗi không mang tên NegativeStockError")
def _():
	dung("câu dịch máy", tin_kho.la_loi_ton_loi(ksx.frappe.ValidationError(CAU_MAY)))
	dung("câu khác thì không", not tin_kho.la_loi_ton_loi(ksx.frappe.ValidationError("Lệnh đã đóng")))


@ca("v650 thuần cau_thieu_nvl: gọn tối đa 4 món rồi +N món khác")
def _():
	ds = [{"ten": "M%d" % i, "sl": i, "dvt": "Kg", "ghi": "kho đang có 0"} for i in range(1, 7)]
	cau = ksx.cau_thieu_nvl("LSX-1", ds, "Baker - Nguyên liệu - TV")
	dung("kho gọn", "kho Baker - Nguyên liệu chưa đủ" in cau)
	dung("4 món rồi +2", "M4 cần 4 Kg" in cau and "M5" not in cau and "+2 món khác" in cau)


@ca("v650 app: hoàn thành cả nhóm chạy bộ kiểm hành vi node (kiểm nguyên liệu trước khi ghi)")
def _():
	import os
	import subprocess

	goc = os.path.dirname(os.path.abspath(__file__))
	r = subprocess.run(["node", os.path.join(goc, "hanh_vi", "nhom_kiem_nvl_650.js")], capture_output=True, text=True)
	la("node: 8 đạt, 0 hỏng", (r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]), (0, "8 dat, 0 hong"))
