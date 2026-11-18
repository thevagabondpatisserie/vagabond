"""/sitemap.xml của tiệm (luật định tuyến trong hooks.py trỏ về đây), thay bản
mặc định của Frappe ghi địa chỉ nội bộ và trang nhân viên. Xem so_do_web.py."""
import frappe
from frappe.utils import nowdate

from vagabond import so_do_web

no_cache = 1
base_template_path = "www/vgb-sitemap.xml"


def get_context(context):
	context.no_cache = 1
	# v672: thêm trang /mon/<mã> của bánh đang lên Google, lấy từ đúng nguồn của
	# tệp /google-merchant.xml. Đọc nguồn hỏng thì vẫn trả các trang khách cố định.
	try:
		from vagabond import google_merchant
		mon = so_do_web.trang_mon(google_merchant.mon_dua_google())
	except Exception:
		frappe.log_error(title="Sơ đồ trang: không đọc được danh sách bánh cho Google", message=frappe.get_traceback())
		mon = ()
	context.so_do = so_do_web.xml_so_do(nowdate(), trang=so_do_web.TRANG_CONG_KHAI + mon)
