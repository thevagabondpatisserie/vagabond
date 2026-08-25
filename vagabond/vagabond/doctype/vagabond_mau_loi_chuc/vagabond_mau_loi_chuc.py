# -*- coding: utf-8 -*-
"""Mau loi chuc co bien.

Chan bien la ngay luc SOAN mau chu khong luc in: nguoi soan go {ten} thay
vi {ten_khach} thi ca dot qua in ra thiep con nguyen dau ngoac nhon, ma
thiep thi da gui khach roi.
"""

from frappe.model.document import Document

from vagabond.tang_qua import _kiem_mau


class VagabondMauLoiChuc(Document):
	def validate(self):
		_kiem_mau(self)
