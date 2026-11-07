"""/sitemap.xml của tiệm (luật định tuyến trong hooks.py trỏ về đây), thay bản
mặc định của Frappe ghi địa chỉ nội bộ và trang nhân viên. Xem so_do_web.py."""
import frappe
from frappe.utils import nowdate

from vagabond import so_do_web

no_cache = 1
base_template_path = "www/vgb-sitemap.xml"


def get_context(context):
	context.no_cache = 1
	context.so_do = so_do_web.xml_so_do(nowdate())
