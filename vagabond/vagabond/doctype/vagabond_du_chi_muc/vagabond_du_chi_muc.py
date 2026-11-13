"""v654 Lịch dự chi (anh Việt 13/11/2026). Mọi việc lưu đi qua vagabond/lich_du_chi.py
(màn Dự chi công nợ); form Desk chỉ để xem."""

import frappe
from frappe.model.document import Document


class VagabondDuChiMuc(Document):
	def validate(self):
		# Cùng nếp Vagabond Dot Chi (Codex #560): sửa thẳng trên Desk hay qua API
		# đi vòng qua kiểm vai và kiểm số của màn. Chỉ lich_du_chi.py được lưu.
		if not self.flags.get("vgb_du_chi"):
			frappe.throw(
				"Chỉ sửa trên màn Dự chi công nợ của app. Form này chỉ để xem.",
				frappe.PermissionError,
			)

	def on_trash(self):
		# Chỉ nút Xoá dự chi nháp của app (lich_du_chi.xoa_muc) được xoá, và chỉ khi còn nháp.
		if getattr(frappe.flags, "vgb_xoa_du_chi", None) != self.name:
			frappe.throw("Chỉ xoá được bằng nút Xoá dự chi nháp trên màn Dự chi công nợ.", frappe.PermissionError)
