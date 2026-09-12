"""Lịch đặt bàn do quản lý chốt, không tự bật giờ giả khi migrate."""
import re
import frappe
from frappe.model.document import Document
from vagabond import diem_ban

class VagabondCauHinhDatBan(Document):
    def validate(self):
        if not self.bat:
            return
        d = diem_ban.theo_ma(self.co_so)
        if not d or not d.get('bat') or not d.get('quay'):
            frappe.throw('Chọn cơ sở có quầy đang hoạt động.')
        gio = str(self.khung_gio or '').split()
        if not gio or len(gio) > 48 or any(not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', g) for g in gio):
            frappe.throw('Nhập từ 1 đến 48 khung giờ, mỗi dòng HH:MM.')
        if not 1 <= int(self.toi_da_khach or 0) <= 30 or not 1 <= int(self.toi_da_ngay or 0) <= 90:
            frappe.throw('Số khách tối đa từ 1 đến 30, số ngày nhận trước từ 1 đến 90.')
