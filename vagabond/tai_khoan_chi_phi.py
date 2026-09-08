"""#206: BOM có món không quản kho sinh chi phí nhưng bỏ trống tài khoản.

ERPNext v16.28.0, manufacturing/doctype/bom/bom.py:add_additional_cost:
expense_account = frappe.get_value('Company', company,
'default_operating_cost_account'). Cả chi phí không quản kho và vận hành
đều có thể nhận giá trị trống. StockEntry.get_gl_entries và
SubcontractingReceipt.make_gl_entries dùng thẳng tài khoản của dòng phí;
GL Entry.check_mandatory chỉ báo chung chung 'Account is required'.

Kiểm ở Document cha vì Frappe không chạy doc_events của dòng con khi lưu
cha. Áp dụng cả Desk, API và app cho bốn chứng từ dùng cùng bảng chi phí.
Không đoán tài khoản từ số hiệu 621, dòng hàng, hay phiếu đã ghi sổ khác.
"""

# phần thuần
BANG_PHI = {
	'Stock Entry': 'additional_costs',
	'Subcontracting Order': 'additional_costs',
	'Subcontracting Receipt': 'additional_costs',
	'Landed Cost Voucher': 'taxes',
}


def loi_tai_khoan(tk, cong_ty):
	if not tk:
		return 'không tồn tại'
	if tk.get('company') != cong_ty:
		return 'thuộc công ty khác'
	if tk.get('is_group'):
		return 'là tài khoản tổng hợp'
	if tk.get('disabled'):
		return 'đã ngừng sử dụng'
	return ''


import frappe
from frappe.utils import flt, escape_html


def kiem(doc, method=None):
	"""Chặn trước khi lõi ghi SLE/GL, giữ nguyên mọi tài khoản đã chọn.

	Landed Cost Taxes and Charges.expense_account.mandatory_depends_on:
	chỉ bắt buộc khi is_perpetual_inventory_enabled(parent.company).
	Không áp quy tắc sổ kho liên tục sang công ty không dùng chế độ này.
	"""
	from erpnext import is_perpetual_inventory_enabled
	bang = BANG_PHI.get(doc.doctype)
	if not bang or not doc.get('company') or doc.docstatus == 2:
		return
	if not is_perpetual_inventory_enabled(doc.company):
		return
	# StockEntry.distribute_additional_costs bỏ bảng phí nếu không nhập kho.
	# Không chặn một dòng cũ mà lõi sẽ bỏ khi chuyển sang phiếu xuất thuần.
	if doc.doctype == 'Stock Entry' and not any(
		d.get('item_code') and d.get('t_warehouse') for d in doc.get('items') or []):
		return
	loi = []
	for stt, dong in enumerate(doc.get(bang) or [], 1):
		if not (flt(dong.get('amount')) or flt(dong.get('base_amount'))):
			continue
		tk = dong.get('expense_account')
		ly_do = 'chưa chọn tài khoản' if not tk else loi_tai_khoan(
			frappe.db.get_value('Account', tk,
				['company', 'is_group', 'disabled'], as_dict=True), doc.company)
		if ly_do:
			loi.append('Dòng {0} ({1}): {2}{3}.'.format(
				dong.get('idx') or stt, escape_html(dong.get('description') or 'Chi phí bổ sung'),
				('Tài khoản ' + escape_html(tk) + ' ') if tk else '', ly_do))
	if not loi:
		return
	buoc = 'Mở phiếu, phần Chi phí bổ sung, chọn tài khoản chi phí đang hoạt động của đúng công ty cho từng dòng trên rồi lưu lại.'
	if doc.doctype == 'Landed Cost Voucher':
		buoc = 'Mở phiếu phân bổ chi phí, phần Thuế và phí, chọn tài khoản đang hoạt động của đúng công ty cho từng dòng trên rồi lưu lại.'
	if doc.doctype == 'Stock Entry' and doc.get('work_order') and doc.get('purpose') == 'Manufacture':
		buoc += (' Nếu dòng phí do lệnh sản xuất tự tạo, nhờ kế toán kiểm tra ô '
			'Tài khoản chi phí hoạt động mặc định (default_operating_cost_account) '
			'trên Công ty {0}; chi phí công đoạn có thể có tài khoản riêng. '
			'Sau khi cấu hình, quay lại lệnh {1} và tạo lại phiếu chưa ghi sổ.').format(
				escape_html(doc.company), escape_html(doc.work_order))
	frappe.throw('<br>'.join(loi + [buoc]), title='Cần khai tài khoản chi phí')
