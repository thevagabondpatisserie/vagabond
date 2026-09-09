"""Yêu cầu khách giữ lịch và lịch sử xử lý, không xóa vĩnh viễn."""
from frappe.model.document import Document
from vagabond.dat_ban import kiem_phieu

class VagabondDatBan(Document):
    def validate(self):
        kiem_phieu(self)
