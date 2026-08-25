# -*- coding: utf-8 -*-
"""Mot phieu tang qua cho MOT khach.

Toan bo luat nam trong `vagabond/tang_qua.py` chu khong nam o day: phan
thuan cua tep do chay duoc trong bo kiem thu tang khung ma khong can site,
con lop nay thi khong. Doc dau tep do de biet vi sao thiet ke ba tang va vi
sao co HAI o so dien thoai chu khong phai mot.
"""

from frappe.model.document import Document

from vagabond.tang_qua import truoc_khi_luu


class VagabondTangQuaVIP(Document):
	def validate(self):
		truoc_khi_luu(self)
