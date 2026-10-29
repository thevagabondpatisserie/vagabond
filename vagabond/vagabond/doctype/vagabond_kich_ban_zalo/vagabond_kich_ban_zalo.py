"""Cấu hình một kịch bản tin Zalo tự động (v621). Logic ở vagabond/zalo_kich_ban.py."""
from frappe.model.document import Document


class VagabondKichBanZalo(Document):
	def validate(self):
		# Sửa mã mẫu trên Desk: xoá trạng thái duyệt và tham số của mẫu cũ.
		from vagabond.zalo_kich_ban import doi_mau_tren_form

		doi_mau_tren_form(self)
