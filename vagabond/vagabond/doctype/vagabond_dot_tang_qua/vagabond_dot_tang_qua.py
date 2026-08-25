# -*- coding: utf-8 -*-
"""Dot tang qua: mot mua qua mot ban ghi.

KHONG cat so lieu tong hop o day. Tong so hop, so khach da tang deu tinh
lai tu cac phieu con luc mo man, theo QT-19 may chu chot so. Cat san thi
moi lan sua mot phieu lai phai nho cong tru vao dot, quen mot lan la con
so sai vinh vien ma khong ai biet.
"""

import frappe
from frappe.model.document import Document


class VagabondDotTangQua(Document):
	def validate(self):
		if not self.nguoi_tao:
			self.nguoi_tao = frappe.session.user
		if self.tu_ngay and self.den_ngay and str(self.den_ngay) < str(self.tu_ngay):
			frappe.throw(
				"Ngày kết thúc đợt đang trước ngày bắt đầu. Nhờ anh chị xem "
				"lại hai ô Từ ngày và Đến ngày."
			)
