"""Hop dong ban hang: catering, event, teabreak, banh thiet ke, B2B.

Nguyen tac chot voi anh Viet 02/08/2026: KHONG sinh Item moi cho tung hop
dong. Dong hoa don dung Item dich vu chung (BAEV, DVBH, DVTI...) va sua
Mo ta dong theo dung cau chu hop dong; doanh thu, cong no theo doi qua
truong custom_hop_dong tren Sales Invoice / Sales Order.
"""

import frappe
from frappe.model.document import Document


class HopDongBanHang(Document):
	def validate(self):
		if self.so_hop_dong:
			self.so_hop_dong = self.so_hop_dong.strip()
