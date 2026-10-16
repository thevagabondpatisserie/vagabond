"""Trang đặt bánh bản Vue (chạy thử song song, anh Việt chốt 11/10/2026).

Như các trang khách khác: có mã CSRF cho nhân viên đang đăng nhập (thiếu là
Frappe chặn 400 khi gửi đơn), không cache phiên. Tên tệp bằng gạch dưới vì
Frappe tìm mô đun theo luật gạch dưới (bài học v529).
"""
import frappe
from vagabond.web_vue import seo_banh

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.seo = seo_banh()
	context.csrf_token = frappe.sessions.get_csrf_token()
