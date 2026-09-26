"""Ba trang chính sách công khai (#367): /chinh-sach-bao-mat, /dieu-khoan,
/giao-hang-doi-tra. Ba đường cùng về trang này qua website_route_rules; Frappe
không truyền `defaults` của luật vào form_dict nên khoá trang suy từ đường dẫn
yêu cầu (frappe.local.request.path, dự phòng frappe.local.path).

Nội dung là Markdown marketing sửa trong /bien-tap-web. Chưa xuất bản hoặc
chưa bật hiện thì trả 404, không bao giờ lộ bản nháp còn chỗ trong ngoặc
vuông ra cho khách.
"""

import frappe

from vagabond import don_web, noi_dung_web, trang_khach

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	context.no_cache = 1
	req = getattr(frappe.local, "request", None)
	duong = getattr(req, "path", None) if req is not None else None
	if not duong:
		duong = getattr(frappe.local, "path", None) or ""
	khoa = noi_dung_web.khoa_tu_duong(str(duong))
	ngon_ngu = "en" if str(frappe.form_dict.get("ngon_ngu") or "") == "en" else "vn"
	trang = noi_dung_web.trang_chinh_sach(khoa, ngon_ngu) if khoa else None
	if not trang:
		raise frappe.PageDoesNotExistError
	duong = noi_dung_web.CHINH_SACH[khoa]["duong"]
	context.tieu_de = trang_khach._e(trang["ten"])
	context.than = trang["html"]
	context.doi_ngon_ngu = (
		'<a href="%s">Tiếng Việt</a>' % duong if trang["ngon_ngu"] == "en"
		else ('<a href="%s?ngon_ngu=en">English</a>' % duong if trang["co_en"] else "")
	)
	context.chan_trang = trang_khach.chan_trang_html(
		don_web.PHAP_NHAN, don_web.lien_he(), noi_dung_web.chinh_sach_dang_hien())
	return context
