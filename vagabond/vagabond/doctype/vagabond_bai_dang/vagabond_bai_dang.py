"""v662 Bài đăng mạng xã hội (anh Việt 15/11/2026). Mọi việc lưu đi qua
vagabond/bai_dang.py (màn Bài đăng mạng xã hội trên app); form Desk chỉ để xem.

Các vai soạn bài có quyền ghi trên doctype vì tải ảnh lên (upload_file gắn vào
bài) cần quyền ghi bài đó; validate dưới đây vẫn chặn mọi lần lưu không đi qua
bai_dang.py."""

import frappe
from frappe.model.document import Document


class VagabondBaiDang(Document):
	def validate(self):
		# Sửa thẳng trên Desk hay qua API là đi vòng qua kiểm vai, kiểm trạng thái
		# và đếm lần lưu của màn. Chỉ bai_dang.py được lưu.
		if not self.flags.get("vgb_bai_dang"):
			frappe.throw("Chỉ sửa trên màn Bài đăng mạng xã hội của app. Form này chỉ để xem.", frappe.PermissionError)
		# v672: thương hiệu theo chủ đề, bỏ kênh thương hiệu không có (mọi đường ghi).
		from vagabond.bai_dang import dong_bo_hieu
		dong_bo_hieu(self)

	def on_trash(self):
		if not frappe.flags.get("vgb_xoa_bai_dang"):
			frappe.throw("Bài đăng không xoá được; bấm Huỷ bài trên app.", frappe.PermissionError)
