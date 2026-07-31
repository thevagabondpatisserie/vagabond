"""Yeu cau xuat hoa don doanh nghiep di kem mot don hang.

Pancake khong co cho ghi ma so thue va email nhan hoa don, nen giu ben nay.
"""

import frappe
from frappe.model.document import Document


class VagabondHoaDon(Document):
	def validate(self):
		self.ma_so_thue = "".join(ch for ch in (self.ma_so_thue or "") if ch.isdigit())
		if len(self.ma_so_thue) not in (10, 13):
			frappe.throw("Ma so thue phai 10 hoac 13 so")
