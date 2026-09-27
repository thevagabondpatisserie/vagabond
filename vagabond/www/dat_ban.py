"""Trang khách có CSRF cho cả nhân viên đang đăng nhập, không cache phiên."""
import frappe
from vagabond import noi_dung_web
no_cache = 1

def get_context(context):
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    # v532: chữ trên trang do marketing sửa ở /bien-tap-web, đã xuất bản.
    # Frappe không autoescape www, nên mẫu phải dùng |e cho từng nhãn.
    context.nhan = noi_dung_web.nhan_cong_khai()
