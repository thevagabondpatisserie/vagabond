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
	ten, ten_da_xoa = [], []
	if frappe.db.count('Version', {'creation': ['<', dd._moc(180)]}):
		raise AssertionError('Bench đã có Version cũ ngoài mẫu; cần nền sạch trước ca xóa.')
	try:
		for i in range(4):
			d = frappe.get_doc(dict(doctype='Version', ref_doctype='ToDo', docname=ma, data='{}'))
			d.insert(ignore_permissions=True)
			ten.append(d.name)
			frappe.db.set_value('Version', d.name, 'creation', add_days(nowdate(), -181 if i < 3 else -1), update_modified=False)
		for loai in ['Sales Invoice', '']:
			d = frappe.get_doc(dict(doctype='Version', ref_doctype=loai or 'ToDo', docname=ma, data='{}'))
			d.insert(ignore_permissions=True)
			ten.append(d.name)
			frappe.db.set_value('Version', d.name, {'creation': add_days(nowdate(), -181), 'ref_doctype': loai}, update_modified=False)
		if frappe.db.count('Deleted Document', {'creation': ['<', dd._moc(180)]}):
			raise AssertionError('Bench đã có Deleted Document cũ ngoài mẫu.')
		for loai, ngay in [('ToDo', -181), ('Sales Invoice', -181), ('', -181), ('ToDo', -1)]:
			d = frappe.get_doc(dict(doctype='Deleted Document', deleted_doctype=loai, deleted_name=ma, data='{}'))
			d.insert(ignore_permissions=True)
			ten_da_xoa.append(d.name)
			frappe.db.set_value('Deleted Document', d.name, 'creation', add_days(nowdate(), ngay), update_modified=False)
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
		if frappe.db.count('Version', {'name':['in',ten]}) != 6:
			raise AssertionError('DELETE chưa được rollback khi đọc số lỗi')
		if dd.don_mot_bang('Version', lo=2) != 3:
			raise AssertionError('ROW_COUNT/commit thật không đếm đúng ba dòng cũ')
		if not frappe.db.exists('Version', ten[3]):
			raise AssertionError('Dòng mới bị xóa nhầm')
		if dd.don_mot_bang('Version', lo=2) != 0:
			raise AssertionError('Lượt hai không rỗng')
		if not all(frappe.db.exists('Version', n) for n in ten[4:]):
			raise AssertionError('Mất lịch sử chứng từ bảo vệ hoặc loại chưa xác định')
		if dd.don_mot_bang('Deleted Document', lo=2) != 1:
			raise AssertionError('Không giới hạn xóa payload đúng phạm vi')
		if not all(frappe.db.exists('Deleted Document', n) for n in ten_da_xoa[1:]):
			raise AssertionError('Mất payload bảo vệ/chưa xác định/mới')
		if dd.gon_tep('KT284_khong_co_bang'):
			raise AssertionError('OPTIMIZE bảng không có bị nhận nhầm là thành công')
		if not dd.gon_tep('tabVersion'):
			raise AssertionError('OPTIMIZE bảng thật không xác nhận thành công')
		if not frappe.db.exists('Version', ten[3]):
			raise AssertionError('Dòng mới mất sau OPTIMIZE')
		print('PASS #284: GET/POST; rollback/ROW_COUNT; giữ lịch sử và payload chứng từ; OPTIMIZE OK/lỗi trên MariaDB thật.', flush=True)
	finally:
		frappe.db.rollback()
		if ten:
			frappe.db.delete('Version', {'name':['in',ten]})
		if ten_da_xoa:
			frappe.db.delete('Deleted Document', {'name':['in',ten_da_xoa]})
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
