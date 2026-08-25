# -*- coding: utf-8 -*-
"""Danh muc phan loai khach VIP.

Danh muc SONG chu khong phai hang so trong ma nguon: "Cigar & Bar" moi xuat
hien o mua Trung thu 2026, tuc la con de tiep. Viet cung vao mot o Select
la moi mua lai phai deploy mot lan.
"""

import frappe
from frappe.model.document import Document


class VagabondNhomKhachVIP(Document):
	def validate(self):
		# Xung ho la chu se in len thiep gui khach VIP. De trong hoac de
		# dinh khoang trang thua thi ca dot qua in ra sai.
		self.xung_ho = (self.xung_ho or "").strip()
		if not self.xung_ho:
			frappe.throw(
				"Nhóm khách nào cũng phải có cách xưng hô, vì đó là chữ sẽ in "
				"lên thiệp. Nhờ anh chị điền ô Xưng hô, ví dụ Nghệ sỹ hoặc Hoa Hậu."
			)
