"""Đơn khách gọi món tại bàn qua mã QR (v638). Xem vagabond/goi_mon_ban.py.

Bản ghi chờ, chưa phải hoá đơn: quầy nhận thì món vào phiếu tạm tính của bàn.
Không xoá vĩnh viễn (QT-20): đơn từ chối, hết hạn vẫn nằm lại để tra.
"""
from frappe.model.document import Document


class VagabondGoiMonBan(Document):
	pass
