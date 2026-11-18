"""v674 Khoá một bút toán nháp do máy lập theo tháng (vagabond/but_toan_nhap.py).
Tên bản ghi chính là khoá loại:công ty:tháng, nên mỗi tháng chỉ một bản nháp hiệu lực."""

import frappe
from frappe.model.document import Document


class VagabondButToanTuLap(Document):
	def validate(self):
		if not self.flags.get("vgb_tu_lap"):
			frappe.throw("Bản ghi này do hệ thống quản lý. Thao tác trên màn Bảng kê 242 hoặc Đối soát chi phí Meta của app.", frappe.PermissionError)

	def on_trash(self):
		frappe.throw("Không xoá được bản ghi khoá bút toán tháng.", frappe.PermissionError)
