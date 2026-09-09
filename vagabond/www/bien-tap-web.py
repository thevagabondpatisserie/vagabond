"""Dashboard marketing chỉ mở cho người có quyền soạn nội dung (#245)."""
import frappe
from vagabond.noi_dung_web import kiem_quyen

no_cache = 1


def get_context(context):
    kiem_quyen()
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
