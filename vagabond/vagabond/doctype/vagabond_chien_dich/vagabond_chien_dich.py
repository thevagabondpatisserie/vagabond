"""Chiến dịch chăm sóc khách. Đã chốt danh sách thì không sửa trên Desk (vagabond.crm)."""
from frappe.model.document import Document


class VagabondChienDich(Document):
	def validate(self):
		from vagabond.crm import kiem_sua_chien_dich

		kiem_sua_chien_dich(self)
