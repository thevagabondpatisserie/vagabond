"""#284: DELETE/ROW_COUNT/rollback thật trên bench GitHub dùng một lần.

Không đăng ký vào bộ savepoint: hàm sản phẩm có commit thật. Khóa ba điều
kiện môi trường trước khi tạo dữ liệu, không dùng script này trên production.
"""
import os
from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.utils import add_days, nowdate
from vagabond import don_dep_db as dd


def chay():
	if (os.environ.get('GITHUB_ACTIONS') != 'true' or frappe.local.site != 'bench-ci.localhost'
		or not frappe.conf.get('vagabond_bench_thu')):
		raise RuntimeError('Chỉ kiểm dọn dữ liệu trên bench GitHub dùng một lần.')
	frappe.set_user('Administrator')
	from frappe.handler import is_valid_http_method
	with patch.object(frappe.local, 'request', SimpleNamespace(method='GET'), create=True):
		try:
			is_valid_http_method(dd.don_dep_ngay_bay_gio)
		except frappe.PermissionError:
			pass
		else:
			raise AssertionError('GET vẫn mở cửa xóa dữ liệu')
	with patch.object(frappe.local, 'request', SimpleNamespace(method='POST'), create=True):
		is_valid_http_method(dd.don_dep_ngay_bay_gio)
	ma = 'KT284-' + frappe.generate_hash(length=12)
	ten = []
	if frappe.db.count('Version', {'creation': ['<', dd._moc(180)]}):
		raise AssertionError('Bench đã có Version cũ ngoài mẫu; cần nền sạch trước ca xóa.')
	try:
		for i in range(4):
			d = frappe.get_doc(dict(doctype='Version', ref_doctype='ToDo', docname=ma, data='{}'))
			d.insert(ignore_permissions=True)
			ten.append(d.name)
			frappe.db.set_value('Version', d.name, 'creation', add_days(nowdate(), -181 if i < 3 else -1), update_modified=False)
		frappe.db.commit()
		sql_goc = frappe.db.sql
		def hong(cau, *a, **kw):
			if str(cau).lower().startswith('select row_count'):
				raise RuntimeError('KT284 lỗi đọc số sau DELETE')
			return sql_goc(cau, *a, **kw)
		with patch.object(frappe.db, 'sql', hong):
			try:
				dd.don_mot_bang('Version', lo=2)
			except RuntimeError as e:
				if 'KT284' not in str(e):
					raise
			else:
				raise AssertionError('Lỗi số đếm bị nuốt thành thành công')
		if frappe.db.count('Version', {'name':['in',ten]}) != 4:
			raise AssertionError('DELETE chưa được rollback khi đọc số lỗi')
		if dd.don_mot_bang('Version', lo=2) != 3:
			raise AssertionError('ROW_COUNT/commit thật không đếm đúng ba dòng cũ')
		if not frappe.db.exists('Version', ten[-1]):
			raise AssertionError('Dòng mới bị xóa nhầm')
		if dd.don_mot_bang('Version', lo=2) != 0:
			raise AssertionError('Lượt hai không rỗng')
		print('PASS #284: GET bị chặn, POST được phép; rollback/ROW_COUNT/giữ dòng mới trên MariaDB thật.', flush=True)
	finally:
		frappe.db.rollback()
		if ten:
			frappe.db.delete('Version', {'name':['in',ten]})
			frappe.db.commit()


if __name__ == '__main__':
	if os.environ.get('GITHUB_ACTIONS') != 'true':
		raise RuntimeError('Không chạy ngoài GitHub Actions.')
	frappe.init(site='bench-ci.localhost', sites_path='.')
	frappe.connect()
	try:
		chay()
	finally:
		frappe.db.rollback()
		frappe.destroy()
