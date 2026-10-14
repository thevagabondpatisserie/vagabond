"""Đơn đặt bánh từ website (#367). Logic nằm ở vagabond/don_web.py."""
from frappe.model.document import Document

from vagabond.don_web import kiem_ban_ghi, sau_khi_luu


class VagabondDonWeb(Document):
	def validate(self):
		from vagabond.giu_ton_web import bao_ve
		bao_ve(self)
		kiem_ban_ghi(self)

	def on_update(self):
		sau_khi_luu(self)
