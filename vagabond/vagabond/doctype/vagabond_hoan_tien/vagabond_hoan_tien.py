"""Yeu cau hoan tien cho khach. Mot don tra hang = mot ban ghi o day."""

import frappe
from frappe.model.document import Document


class VagabondHoanTien(Document):
	def validate(self):
		if (self.ly_do or "") == "Khac" and not (self.dien_giai or "").strip():
			frappe.throw(
				"Lý do \"Khác\" thì phải ghi rõ vì sao hoàn, để sau này còn thống kê được. "
				"Gõ vào ô Diễn giải thêm giúp em."
			)
