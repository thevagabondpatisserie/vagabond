"""v656 Phiếu Đề xuất công thức (anh Việt 13/11/2026). Mọi việc lưu đi qua
vagabond/de_xuat_cong_thuc.py (màn Danh mục công thức); form Desk chỉ để xem."""

import frappe
from frappe.model.document import Document


class VagabondDeXuatCongThuc(Document):
	def validate(self):
		# Sửa thẳng trên Desk hay qua API là đi vòng qua kiểm vai và kiểm trạng
		# thái của màn. Chỉ de_xuat_cong_thuc.py được lưu.
		if not self.flags.get("vgb_de_xuat_ct"):
			frappe.throw("Chỉ sửa trên màn Danh mục công thức của app. Form này chỉ để xem.", frappe.PermissionError)

	def on_trash(self):
		if not frappe.flags.get("vgb_xoa_de_xuat_ct"):
			frappe.throw("Phiếu đề xuất không xoá được; bấm Huỷ phiếu trên app.", frappe.PermissionError)
