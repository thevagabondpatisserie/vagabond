"""#206: phí BOM và nhập kho phải ghi đúng tài khoản, thiếu thì không có SLE/GL.

Mọi chứng từ là mã thử trong điểm lưu của nen.py. Chỉ giả lập giá trị đọc
một ô cấu hình khi gọi bộ tạo phiếu lõi, không sửa Công ty trên site.
Insert/submit và SLE/GL đều thật, không thay bằng mock.
"""
import uuid
from unittest.mock import patch

import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as nhap_kho
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la, so_cai_cua
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _uom
from vagabond.khung.kiem_that.thu_san_xuat_206 import _lenh


def _luu(doc):
	doc.insert()
	nen._DA_TAO.append((doc.doctype, doc.name))
	doc.submit()
	return doc


def _nen_phi():
	cty = cong_ty()
	tk = frappe.db.get_value('Account', {'company': cty, 'is_group': 0,
		'disabled': 0, 'root_type': 'Expense', 'account_type': ['not in',
			['Stock', 'Fixed Asset', 'Cost of Goods Sold', 'Stock Received But Not Billed']]}, 'name')
	if not tk: raise AssertionError('Cần tài khoản chi phí lá để kiểm hạch toán.')
	kho = frappe.get_all('Warehouse', filters={'company': cty, 'is_group': 0, 'disabled': 0},
		pluck='name', limit_page_length=2)
	if len(kho) != 2: raise AssertionError('Cần hai kho thử đang hoạt động.')
	tag = uuid.uuid4().hex[:10]
	nvl = _mon_thu('KT206P-NL-' + tag)
	tp = _mon_thu('KT206P-TP-' + tag)
	phi = _mon_thu('KT206P-PHI-' + tag)
	it = frappe.get_doc('Item', phi); it.is_stock_item = 0; it.save()
	_luu(nhap_kho(item_code=nvl, qty=10, company=cty, to_warehouse=kho[0],
		rate=1000, do_not_save=True))
	bom = frappe.get_doc({'doctype': 'BOM', 'item': tp, 'company': cty,
		'quantity': 1, 'is_active': 1, 'is_default': 1, 'rm_cost_as_per': 'Valuation Rate',
		'items': [{'item_code': nvl, 'qty': 1, 'uom': _uom(), 'rate': 1000},
			{'item_code': phi, 'qty': 1, 'uom': _uom(), 'rate': 125}]})
	_luu(bom)
	wo = _lenh(cty, kho, tp, bom, kho[0]); wo.submit()
	return cty, tk, kho, nvl, tp, wo


def _tao_tu_lenh(wo, tk):
	doc_goc = frappe.get_value
	def doc_cau_hinh(dt, ten=None, truong=None, *a, **kw):
		if dt == 'Company' and ten == wo.company and truong == 'default_operating_cost_account':
			return tk
		return doc_goc(dt, ten, truong, *a, **kw)
	with patch.object(frappe, 'get_value', side_effect=doc_cau_hinh):
		return frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=1))


@ca('206 phí thật: BOM không quản kho, mặc định trống bị chặn trước khi lưu phiếu')
def _thieu():
	cty, tk, kho, nvl, tp, wo = _nen_phi()
	doc = _tao_tu_lenh(wo, None)
	dung('lõi sinh dòng phí thiếu tài khoản', any(not d.expense_account and d.amount for d in doc.additional_costs))
	truoc = {dt: frappe.db.count(dt) for dt in ['Stock Entry', 'Stock Ledger Entry', 'GL Entry']}
	try:
		_luu(doc)
		raise AssertionError('Thiếu tài khoản phí phải chặn')
	except frappe.ValidationError as e:
		dung('chỉ đúng ô cấu hình', 'default_operating_cost_account' in str(e))
		dung('có số lệnh và dòng phí', wo.name in str(e) and 'Dòng ' in str(e))
	for dt, so in truoc.items(): la('không tạo ' + dt, frappe.db.count(dt), so)
	wo.reload(); la('chưa tăng sản lượng', float(wo.produced_qty), 0)


@ca('206 phí thật: có mặc định, hoàn tất hai phần ghi chi phí BOM đúng GL và SLE')
def _du():
	cty, tk, kho, nvl, tp, wo = _nen_phi()
	for lan in range(2):
		doc = _tao_tu_lenh(wo, tk)
		la('lõi lấy cấu hình', {d.expense_account for d in doc.additional_costs}, {tk})
		phi = sum(float(d.amount) for d in doc.additional_costs)
		dung('phí không được bằng không', phi > 0)
		_luu(doc)
		gl = so_cai_cua(doc)
		la('ghi Có đúng tài khoản phí', round(sum(float(d.credit)-float(d.debit) for d in gl if d.account == tk), 2), round(phi, 2))
		la('GL cân', round(sum(float(d.debit)-float(d.credit) for d in gl), 2), 0)
		sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_no': doc.name, 'is_cancelled': 0},
			fields=['item_code', 'actual_qty', 'stock_value_difference'])
		la('trừ một nguyên liệu', sum(float(d.actual_qty) for d in sle if d.item_code == nvl), -1)
		la('nhập một thành phẩm', sum(float(d.actual_qty) for d in sle if d.item_code == tp), 1)
		la('giá trị kho tăng đúng phí', round(sum(float(d.stock_value_difference) for d in sle), 2), round(phi, 2))
	wo.reload(); la('hoàn tất hai phần', float(wo.produced_qty), 2)


@ca('206 phí thật: nhập kho trực tiếp giữ tài khoản phí chọn tay và ghi GL')
def _nhap():
	cty, tk, kho, nvl, tp, wo = _nen_phi()
	doc = nhap_kho(item_code=nvl, qty=1, company=cty, to_warehouse=kho[0], rate=1000, do_not_save=True)
	doc.append('additional_costs', {'expense_account': tk, 'description': 'Phí vận chuyển thử', 'amount': 75})
	doc.insert(); nen._DA_TAO.append((doc.doctype, doc.name))
	for cach in ['save', 'submit']:
		doc.additional_costs[0].expense_account = None
		try:
			getattr(doc, cach)()
			raise AssertionError('Xoá tài khoản qua ' + cach + ' phải bị chặn')
		except frappe.ValidationError as e:
			dung('chỉ đúng dòng phí nhập kho', 'Phí vận chuyển thử' in str(e))
		doc.reload()
		la('bản lưu vẫn giữ tài khoản', doc.additional_costs[0].expense_account, tk)
		la('vẫn nháp', doc.docstatus, 0)
		for dt in ['Stock Ledger Entry', 'GL Entry']:
			la('chưa ghi ' + dt, frappe.db.count(dt, {'voucher_no': doc.name}), 0)
	doc.submit()
	doc.reload(); la('giữ chọn tay', doc.additional_costs[0].expense_account, tk)
	gl = so_cai_cua(doc)
	# Tài khoản dòng hàng có thể trùng tk; chốt phí trên dữ liệu đã ghi và
	# giá trị nhập kho, không suy rằng mọi Có của tk đều là chi phí bổ sung.
	la('GL cân', round(sum(float(d.debit)-float(d.credit) for d in gl), 2), 0)
	dung('có bút toán phí', any(d.account == tk and float(d.credit) >= 75 for d in gl))
	sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_no': doc.name, 'is_cancelled': 0}, fields=['stock_value_difference'])
	la('giá nhập gồm phí', round(sum(float(d.stock_value_difference) for d in sle), 2), 1075)
