"""Mot lo ma voucher xuat ra de gui cho doi tac, brand collab, khach VIP.

Nguoi thao tac dien email cua chinh minh (hoac cua doi tac) va so luong ma
muon nhan; may sinh du so ma 6 ky tu khac nhau roi gui file CSV ve email do.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class VagabondLoVoucher(Document):
	def validate(self):
		if not self.nguoi_tao:
			self.nguoi_tao = frappe.session.user
		if cint(self.so_luong) <= 0:
			frappe.throw("Số lượng mã phải lớn hơn 0.")
		if cint(self.so_luong) > 5000:
			frappe.throw("Một lô tối đa 5.000 mã. Cần nhiều hơn thì xuất thành nhiều lô.")
