"""Cấu hình một kịch bản tin Zalo tự động (v621). Logic ở vagabond/zalo_kich_ban.py."""
from frappe.model.document import Document


class VagabondKichBanZalo(Document):
	def validate(self):
		# Lưu trên Desk theo đúng luật màn app: đổi mã mẫu thì xoá kết quả kiểm
		# cũ, bật thì ghi lúc bật.
		from vagabond.zalo_kich_ban import truoc_luu_form

		truoc_luu_form(self)
