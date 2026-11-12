"""Đợt dự chi công nợ nhà cung cấp, trả ngày 10 và 20 (issue #555).

Mọi việc đổi trạng thái đi qua vagabond/du_chi.py; form Desk chỉ để xem."""

import frappe
from frappe.model.document import Document


class VagabondDotChi(Document):
	def validate(self):
		# Codex #560: Thu mua có quyền ghi doctype này nên sửa thẳng trên Desk
		# hay qua API (đổi trạng thái sang Đã duyệt, sửa số trả sau khi duyệt)
		# sẽ đi vòng qua hai cấp duyệt. Chỉ du_chi.py (soạn, lưu, gửi, duyệt)
		# được lưu, và du_chi.py tự kiểm vai, bước, người duyệt.
		if not self.flags.get("vgb_du_chi"):
			frappe.throw(
				"Đợt dự chi chỉ sửa trên màn Dự chi công nợ (soạn, lưu, gửi duyệt, duyệt). "
				"Form này chỉ để xem.",
				frappe.PermissionError,
			)
