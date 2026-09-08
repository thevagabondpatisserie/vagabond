"""Khải phải chọn tay ở Desktop, còn Bếp không có các bước chọn đó (#206).

Chỉ đổi metadata mặc định/hiển thị, không UPDATE Work Order/Stock Entry cũ.
Tài khoản621 được cấu hình trên Company bằng Desk theo comment5583472911;
không hardcode tài khoản một công ty vào patch dùng cho mọi site.
"""
import json
import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	# Dùng item_name có sẵn của lõi, không tạo cột tên sản phẩm thứ hai.
	meta = frappe.get_meta('Work Order', cached=False)
	thu_tu = [d.fieldname for d in meta.fields if d.fieldname != 'item_name']
	thu_tu.insert(thu_tu.index('production_item') + 1, 'item_name')
	for truong, thuoc_tinh, gia_tri, loai in [
		(None, 'field_order', json.dumps(thu_tu), 'Text'),
		('item_name', 'hidden', 0, 'Check'),
		('item_name', 'label', 'Tên sản phẩm', 'Data'),
		('item_name', 'read_only', 1, 'Check'),
		('item_name', 'fetch_if_empty', 0, 'Check'),
		('skip_transfer', 'default', '1', 'Text'),
	]:
		make_property_setter('Work Order', truong, thuoc_tinh, gia_tri, loai,
			for_doctype=truong is None)
	# Select phải chứa giá trị mà JS/server gán; giữ mọi chuỗi đang có.
	o = frappe.get_meta('Stock Entry', cached=False).get_field('naming_series')
	chuoi = (o.options or '').split('\n')
	if 'PSX-.YYYY.-' not in chuoi:
		chuoi.append('PSX-.YYYY.-')
		make_property_setter('Stock Entry', 'naming_series', 'options', '\n'.join(chuoi), 'Text')
	for dt in ['Work Order', 'Stock Entry']:
		frappe.clear_cache(doctype=dt)
