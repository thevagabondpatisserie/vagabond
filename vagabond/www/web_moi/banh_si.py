"""Trang Bánh sỉ (/banh-si) bản Vue, v630.

Như các trang khách khác: có mã CSRF cho nhân viên đang đăng nhập (thiếu là
Frappe chặn 400 khi gửi), không cache phiên (trang đọc cookie khách sỉ). Tên
tệp gạch dưới vì Frappe tìm mô đun theo luật gạch dưới (bài học v529).
"""
import frappe

no_cache = 1


def get_context(context):
	context.no_cache = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
