"""Một lượt ứng tuyển (v622). Không xoá cứng; hết hạn lưu thì máy xoá thông tin cá nhân."""
import frappe
from frappe.model.document import Document


class VagabondUngVien(Document):
	def validate(self):
		# Mọi đường tạo hồ sơ (app, web, Desk, API) đều qua đây: bắt đồng ý lưu và
		# đặt hạn lưu, để nhịp xoá theo hạn luôn chọn được hồ sơ (Codex #518).
		from vagabond.tuyen_dung import kiem_luu_tru
		loi, them = kiem_luu_tru({k: self.get(k) for k in ("dong_y", "dong_y_luc", "han_luu", "da_an_danh")},
			frappe.utils.now_datetime())
		if loi:
			frappe.throw(loi)
		for k, v in them.items():
			self.set(k, v)
