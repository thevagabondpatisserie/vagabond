"""v666 Sổ chủ đề của Kho bản thảo (anh Việt 17/11/2026, phương án A như sổ Evernote).
Mọi việc tạo, sửa đi qua vagabond/bai_dang.py (màn Bài đăng mạng xã hội); form Desk chỉ để xem."""

import frappe
from frappe.model.document import Document


class VagabondChuDeBai(Document):
	def validate(self):
		if not self.flags.get("vgb_bai_dang"):
			frappe.throw("Chỉ sửa chủ đề trên màn Bài đăng mạng xã hội của app. Form này chỉ để xem.", frappe.PermissionError)

	def on_trash(self):
		if not frappe.flags.get("vgb_xoa_bai_dang"):
			frappe.throw("Chủ đề không xoá được trên Desk.", frappe.PermissionError)
