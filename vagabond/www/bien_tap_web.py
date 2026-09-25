"""Dashboard marketing chỉ mở cho người có quyền soạn nội dung (#245).

#367 mục 8: khách chưa đăng nhập thì chuyển sang /login rồi quay lại đây;
đã đăng nhập mà thiếu vai Marketing thì hiện trang báo quyền có nút Đăng
xuất, không ném lỗi giữa lúc dựng trang nữa. Trang phụ thuộc phiên nên tắt
đệm ở CẢ hai tầng: `no_cache` của mô đun và `frappe.local.no_cache` của
lượt tải, để phiên này không bao giờ thấy trang dựng cho phiên khác.
"""
import frappe
from frappe.utils import get_fullname

from vagabond.noi_dung_web import DUONG_BANG, quyet_vao_bang

no_cache = 1


def get_context(context):
    frappe.local.no_cache = 1
    context.no_cache = 1
    frappe.local.response_headers.update({"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"})
    nguoi = frappe.session.user
    ket_qua = quyet_vao_bang(nguoi, frappe.get_roles(nguoi) if nguoi != "Guest" else [])
    if ket_qua == "dang_nhap":
        frappe.local.flags.redirect_location = "/login?redirect-to=" + DUONG_BANG
        raise frappe.Redirect
    context.khong_quyen = 1 if ket_qua == "khong_quyen" else 0
    context.ten_nguoi = frappe.utils.escape_html(get_fullname(nguoi) or nguoi)
    context.csrf_token = frappe.sessions.get_csrf_token()
