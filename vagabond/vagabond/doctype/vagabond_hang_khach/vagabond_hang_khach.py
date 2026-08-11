"""Hang khach hang: EXPLORER, VOYAGER, VAGABONDER xet theo chi tieu;
FAMILY va AMBASSADOR quan ly gan tay.

Muc chi tieu va phan tram giam de o day chu khong nhet trong ma, de anh
Viet tu sua khi chot con so ma khong phai doi deploy (11/08/2026).
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class VagabondHangKhach(Document):
	def validate(self):
		self.ten_hang = (self.ten_hang or "").strip().upper()
		if flt(self.giam_gia) < 0 or flt(self.giam_gia) > 100:
			frappe.throw("Phần trăm giảm phải nằm trong khoảng 0 đến 100.")
