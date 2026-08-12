# -*- coding: utf-8 -*-
"""So diem tich luy cua khach.

Ghi tung but mot chu khong giu moi mot con so du: diem la tien cua khach,
mat mot cuc ma khong biet no di dau thi khong ai giai trinh duoc. So du
tren Customer chi la ban tong hop, luc nao lech thi tinh lai tu so nay.
"""

import frappe
from frappe.model.document import Document


class VagabondSoDiem(Document):
	def validate(self):
		if not self.nguoi:
			self.nguoi = frappe.session.user
		if not self.ngay:
			self.ngay = frappe.utils.now_datetime()
