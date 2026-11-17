"""Đơn đặt bánh từ website (#367). Logic nằm ở vagabond/don_web.py."""
from frappe.model.document import Document

from vagabond.don_web import kiem_ban_ghi, sau_khi_luu


class VagabondDonWeb(Document):
	def autoname(self):
		"""v670 (anh Việt 17/11/2026): đơn kênh WEBORDER mang mã WO-YYMMDD-5 số
		(vagabond/ma_don.py); đơn đặt bánh trên web giữ mã DW-YYMM-5 số theo doctype."""
		from vagabond import don_quay, ma_don

		if self.get("vgb_kenh") == don_quay.KENH:
			self.name = ma_don.dat_ten(ma_don.TIEN_TO_WO)

	def validate(self):
		from vagabond.giu_ton_web import bao_ve
		bao_ve(self)
		kiem_ban_ghi(self)

	def on_update(self):
		sau_khi_luu(self)
