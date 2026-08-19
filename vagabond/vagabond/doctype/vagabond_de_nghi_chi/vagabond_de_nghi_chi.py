# -*- coding: utf-8 -*-
"""Lớp doctype cho Đề nghị chi nội bộ.

Luật nghiệp vụ nằm hết ở `vagabond/de_nghi_chi.py` để kiểm thử được không
cần site. Ở đây chỉ nối vào vòng đời của Frappe.
"""

from frappe.model.document import Document


class VagabondDeNghiChi(Document):
	pass
