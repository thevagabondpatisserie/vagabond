"""#206: Work Order/Stock Entry thật, kho thật, SLE/GL thật.

Chỉ tạo mã thử ngẫu nhiên, chạy trong savepoint của nen.py, không commit.
Chưa thể chứng minh lô thay thế bằng ca không theo lô: nghiệm thu ISC/Bacardi
vẫn là gate riêng trong tai_lieu/issue-206-san-xuat.md.
"""
import uuid
import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry, get_consumed_qty
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as nhap_kho
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la, so_cai_cua
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _bom_thu
from vagabond.san_xuat_desktop import TRUONG_KHO


def _nen():
	cty = cong_ty()
	kho = frappe.get_all('Warehouse', filters={'company': cty, 'is_group': 0, 'disabled': 0}, pluck='name', limit_page_length=2)
	if len(kho) != 2:
		raise AssertionError('Cần hai kho lá đang hoạt động để kiểm khác kho.')
	tag = uuid.uuid4().hex[:10]
	nvl = _mon_thu('KT206-NVL-' + tag)
	tp = _mon_thu('KT206-TP-' + tag)
	it = frappe.get_doc('Item', tp)
	it.set(TRUONG_KHO, kho[0]); it.save()
	bom = _bom_thu(tp, nvl, cty)
	return cty, kho, nvl, tp, bom


def _lenh(cty, kho, tp, bom, nguon=None):
	wo = frappe.get_doc({'doctype': 'Work Order', 'company': cty, 'production_item': tp,
		'bom_no': bom.name, 'qty': 2, 'source_warehouse': nguon,
		'fg_warehouse': kho[1], 'wip_warehouse': kho[0], 'skip_transfer': 1,
		'use_multi_level_bom': 1})
	wo.insert()
	nen._DA_TAO.append(('Work Order', wo.name))
	wo.reload()
	return wo


@ca('206 thật: mặc định món, kho chọn tay, kho dòng, lệnh cũ không bị thay')
def _kho():
	cty, kho, nvl, tp, bom = _nen()
	wo = _lenh(cty, kho, tp, bom)
	la('kho từ món', wo.source_warehouse, kho[0])
	la('kho dòng đã lưu', wo.required_items[0].source_warehouse, kho[0])
	tay = _lenh(cty, kho, tp, bom, kho[1])
	la('kho chọn tay thắng', tay.source_warehouse, kho[1])
	tay.required_items[0].source_warehouse = kho[0]
	tay.save(); tay.reload()
	la('giữ kho dòng có chủ ý', tay.required_items[0].source_warehouse, kho[0])
	it = frappe.get_doc('Item', tp)
	it.set(TRUONG_KHO, kho[1]); it.save()
	wo.save(); wo.reload()
	la('không hồi tố mặc định', wo.source_warehouse, kho[0])


@ca('206 thật: hoàn tất từng phần trừ đúng kho SLE, consumed_qty và GL cân')
def _ghi_so():
	cty, kho, nvl, tp, bom = _nen()
	for k in kho:
		phieu = nhap_kho(item_code=nvl, qty=10, company=cty, to_warehouse=k, rate=1000, do_not_save=True)
		phieu.insert(); nen._DA_TAO.append(('Stock Entry', phieu.name)); phieu.submit()
	wo = _lenh(cty, kho, tp, bom, kho[1])
	wo.submit()
	for lan in range(2):
		doc = frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=1))
		doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name)); doc.submit()
		sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type':'Stock Entry', 'voucher_no':doc.name, 'is_cancelled':0}, fields=['item_code','warehouse','actual_qty','stock_value_difference'])
		nl = [d for d in sle if d.item_code == nvl]
		la('một dòng nguyên liệu', len(nl), 1)
		la('trừ đúng kho chọn', nl[0].warehouse, kho[1])
		la('số trừ mỗi lần', float(nl[0].actual_qty), -1)
		la('consumed cộng dồn', get_consumed_qty(wo.name,nvl), lan+1)
		gl = so_cai_cua(doc)
		# Cùng tài khoản tồn và không thêm chi phí có thể không phát sinh GL.
		# Chỉ chấp nhận rỗng khi biến động giá trị kho ròng bằng 0.
		if not gl:
			la('không GL thì giá trị kho ròng không đổi', round(sum(float(d.stock_value_difference) for d in sle), 2), 0)
		la('GL nợ có cân', sum(float(d.debit) for d in gl), sum(float(d.credit) for d in gl))
	wo.reload()
	la('hoàn tất đủ hai phần', float(wo.produced_qty), 2)
	la('đóng lệnh', wo.status, 'Completed')
