"""Đăng ký tiệc của khách: giữ nguyên chữ khách gửi, sales chỉ đổi trạng thái."""
from frappe.model.document import Document
from vagabond.tiec_web import kiem_phieu


class VagabondDangKyTiec(Document):
    def validate(self):
        kiem_phieu(self)
