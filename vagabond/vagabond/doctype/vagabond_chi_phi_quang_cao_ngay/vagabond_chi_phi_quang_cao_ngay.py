"""v674 Số Meta đã tiêu theo ngày, tài khoản quảng cáo và chiến dịch (chỉ đọc, ads_read).
Do vagabond/quang_cao_meta.py ghi; một dòng một khoá, đọc lại thì ghi thay số cũ."""

import frappe
from frappe.model.document import Document


class VagabondChiPhiQuangCaoNgay(Document):
	def validate(self):
		if not self.flags.get("vgb_meta"):
			frappe.throw("Số chi phí quảng cáo do hệ thống đọc từ Meta, không sửa tay được.", frappe.PermissionError)

	def on_trash(self):
		frappe.throw("Không xoá được số chi phí quảng cáo đã đọc.", frappe.PermissionError)
