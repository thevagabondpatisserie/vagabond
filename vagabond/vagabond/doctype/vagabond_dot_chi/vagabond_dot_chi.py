"""Đợt dự chi công nợ nhà cung cấp, trả ngày 10 và 20 (issue #555).

Mọi việc đổi trạng thái đi qua vagabond/du_chi.py; form Desk chỉ để xem."""

from frappe.model.document import Document


class VagabondDotChi(Document):
	pass
