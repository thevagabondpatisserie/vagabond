"""Đăng ký bánh sỉ của quán: giữ nguyên chữ khách gửi, Sales chỉ duyệt hoặc từ chối (v630)."""
from frappe.model.document import Document


class VagabondDangKySi(Document):
	def validate(self):
		from vagabond.banh_si import kiem_phieu_dang_ky

		kiem_phieu_dang_ky(self)
