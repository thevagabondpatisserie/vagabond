"""Khai kho nguồn trên món; chỉ schema, không sửa Item/WO đang có.

Patch này không nuốt lỗi: app đọc field ngay sau deploy nên thiếu cột phải
làm migrate thất bại rõ ràng. Chạy lại an toàn với update=True.
"""
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from vagabond.san_xuat_desktop import TRUONG_MOI, TRUONG_KHO


def execute():
	create_custom_fields(TRUONG_MOI, update=True)
	frappe.clear_cache(doctype='Item')
	if not frappe.db.has_column('Item', TRUONG_KHO):
		frappe.throw('Chưa tạo được ô Kho nguyên liệu mặc định khi sản xuất. Dừng cập nhật.')
