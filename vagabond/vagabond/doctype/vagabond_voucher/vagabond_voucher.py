"""Mot ma voucher dung mot lan. Ma 6 ky tu, sinh hang loat theo lo."""

import frappe
from frappe.model.document import Document


class VagabondVoucher(Document):
	def autoname(self):
		self.name = (self.ma or "").strip().upper()

	def validate(self):
		self.ma = (self.ma or "").strip().upper()
		if not self.ma:
			frappe.throw("Voucher phải có mã.")
