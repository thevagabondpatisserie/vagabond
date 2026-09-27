"""Trang khách có CSRF cho cả nhân viên đang đăng nhập, không cache phiên."""
import frappe
no_cache = 1

def get_context(context):
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
