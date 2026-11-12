"""Nhật ký BTP (v653, sự cố Tira 18cm 12/11/2026): mỗi lần đổi số trên bảng
BTP bánh ổ một dòng. Chỉ vagabond/btp.py ghi; không ai sửa hay xoá được."""

import frappe
from frappe.model.document import Document


class NhatKyBTP(Document):
	def validate(self):
		if not self.is_new():
			frappe.throw("Nhật ký BTP chỉ máy ghi, không sửa được.")

	def on_trash(self):
		frappe.throw("Nhật ký BTP không xoá được.")
