"""v552: mã thay thế cho nguyên liệu KHÔNG theo lô, chạy thật trên ERPNext.

Ca thật 02/10/2026: Lescure (NVLT00002) hết ở kho Baker, Pauls (NVLT00329)
còn 87.915 ml cùng kho, cặp thay thế đã khai, bấm Hoàn tất vẫn bị chặn.
Các ca dưới đi ĐÚNG chuỗi của bếp: lệnh thật, make_stock_entry Manufacture
của ERPNext, rồi `kho_san_xuat.hoan_tat_phieu` (đúng hàm nút Hoàn tất gọi),
không gọi thêm hàm nào khác.

Chỉ tạo mã thử ngẫu nhiên, chạy trong savepoint của nen.py, không commit.
"""
import uuid

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import get_consumed_qty, make_stock_entry
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as nhap_kho

from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la
from vagabond.khung.kiem_that.thu_ma_cap_so import _bom_thu, _mon_thu
from vagabond.khung.kiem_that.thu_san_xuat_206 import _lenh
from vagabond.kho_san_xuat import hoan_tat_phieu
from vagabond.san_xuat_desktop import TRUONG_KHO


def _nen(cho_thay=1, khai=True):
	cty = cong_ty()
	kho = frappe.get_all("Warehouse", filters={"company": cty, "is_group": 0, "disabled": 0},
		pluck="name", limit_page_length=2)
	if len(kho) != 2:
		raise AssertionError("Cần hai kho lá đang hoạt động.")
	tag = uuid.uuid4().hex[:10]
	goc = _mon_thu("KT552-GOC-" + tag)
	thay = _mon_thu("KT552-THAY-" + tag)
	tp = _mon_thu("KT552-TP-" + tag)
	frappe.db.set_value("Item", goc, "allow_alternative_item", 1)
	if khai:
		ia = frappe.get_doc({"doctype": "Item Alternative", "item_code": goc,
			"alternative_item_code": thay, "two_way": 1})
		ia.flags.ignore_permissions = True
		ia.insert(ignore_permissions=True)
		nen._DA_TAO.append(("Item Alternative", ia.name))
	frappe.db.set_value("Item", goc, "allow_alternative_item", cho_thay)
	frappe.clear_document_cache("Item", goc)
	frappe.clear_cache(doctype="Item")
	it = frappe.get_doc("Item", tp)
	it.set(TRUONG_KHO, kho[0])
	it.save()
	bom = _bom_thu(tp, goc, cty)
	return cty, kho, goc, thay, tp, bom


def _nhap(ma, so, cty, kho):
	if so <= 0:
		return
	p = nhap_kho(item_code=ma, qty=so, company=cty, to_warehouse=kho, rate=1000, do_not_save=True)
	p.insert()
	nen._DA_TAO.append(("Stock Entry", p.name))
	p.submit()


def _ton(ma, kho):
	return float(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty") or 0)


def _bam_hoan_tat(wo, q):
	"""Đúng chuỗi của nút Hoàn tất: make_stock_entry rồi hoan_tat_phieu."""
	kq = hoan_tat_phieu(make_stock_entry(wo.name, "Manufacture", qty=q), q=q, can=q)
	nen._DA_TAO.append(("Stock Entry", kq["name"]))
	return frappe.get_doc("Stock Entry", kq["name"])


def _dong_nl(se):
	return sorted((d.item_code, d.original_item or "", float(d.qty)) for d in se.items if d.s_warehouse)


@ca("v552 thật: gốc hết, mã thay còn cùng kho -> Hoàn tất ghi sổ được, trừ mã thay, lệnh tính đã dùng mã gốc")
def _het_goc():
	cty, kho, goc, thay, tp, bom = _nen()
	_nhap(thay, 10, cty, kho[0])
	wo = _lenh(cty, kho, tp, bom, kho[0])
	wo.submit()
	se = _bam_hoan_tat(wo, 2)
	la("phiếu đã ghi sổ", se.docstatus, 1)
	la("một dòng nguyên liệu là mã thay, mang mã gốc", _dong_nl(se), [(thay, goc, 2.0)])
	la("tồn mã thay giảm đúng 2", _ton(thay, kho[0]), 8.0)
	la("lệnh tính đã dùng nguyên liệu gốc", float(get_consumed_qty(wo.name, goc)), 2.0)
	wo.reload()
	la("lệnh hoàn tất", wo.status, "Completed")


@ca("v552 thật: gốc còn một phần -> trừ hết gốc trước, phần thiếu lấy mã thay")
def _mot_phan():
	cty, kho, goc, thay, tp, bom = _nen()
	_nhap(goc, 1, cty, kho[0])
	_nhap(thay, 10, cty, kho[0])
	wo = _lenh(cty, kho, tp, bom, kho[0])
	wo.submit()
	se = _bam_hoan_tat(wo, 2)
	la("hai dòng", _dong_nl(se), sorted([(goc, "", 1.0), (thay, goc, 1.0)]))
	la("gốc về 0", _ton(goc, kho[0]), 0.0)
	la("thay còn 9", _ton(thay, kho[0]), 9.0)
	la("lệnh tính đã dùng 2 nguyên liệu gốc", float(get_consumed_qty(wo.name, goc)), 2.0)


@ca("v552 thật: món gốc TẮT cho phép thay thì không đổi mã, vẫn bị chặn thiếu hàng, mã thay không bị trừ")
def _khong_cho_thay():
	cty, kho, goc, thay, tp, bom = _nen(cho_thay=0)
	_nhap(thay, 10, cty, kho[0])
	wo = _lenh(cty, kho, tp, bom, kho[0])
	wo.submit()
	co_chan = False
	try:
		_bam_hoan_tat(wo, 2)
	except Exception:
		co_chan = True
	dung("bị chặn thiếu hàng", co_chan)
	la("mã thay không bị trừ", _ton(thay, kho[0]), 10.0)


@ca("v552 thật: mã thay cũng không đủ -> chặn bằng câu đọc được, không trừ gì")
def _thay_thieu():
	cty, kho, goc, thay, tp, bom = _nen()
	_nhap(thay, 1, cty, kho[0])
	wo = _lenh(cty, kho, tp, bom, kho[0])
	wo.submit()
	cau = ""
	try:
		_bam_hoan_tat(wo, 2)
	except Exception as e:
		cau = str(e)
	dung("bị chặn", bool(cau))
	dung("câu nói không đủ và còn thiếu", "không đủ" in cau and "thiếu" in cau)
	la("mã thay không bị trừ", _ton(thay, kho[0]), 1.0)
