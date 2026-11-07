"""v643: trên Frappe thật, /sitemap.xml phải đi qua luật định tuyến về trang
của tiệm (vgb-sitemap.xml), không còn là sơ đồ mặc định ghi địa chỉ nội bộ.

Bench #546 (07/11/2026): Frappe chỉ áp luật định tuyến (website_route_rules)
khi có request web (evaluate_dynamic_routes đọc frappe.local.request.environ).
Bench chạy từ dòng lệnh không có request nên resolve_path trả nguyên
"sitemap.xml" và ca đỏ dù luật đúng. Ca dựng một request GET /sitemap.xml
thật (cùng cách thu_phieu_thu_unc_534) rồi gọi đúng lối phục vụ trang của
Frappe, đọc nội dung trả về."""
import frappe

from vagabond.khung.kiem_that.nen import ca, dung, la


@ca("643 /sitemap.xml đi về sơ đồ của tiệm")
def _so_do():
	from frappe.website.path_resolver import resolve_path
	from frappe.website.serve import get_response
	from werkzeug.test import EnvironBuilder
	from werkzeug.wrappers import Request

	co_request_cu = hasattr(frappe.local, "request")
	request_cu = getattr(frappe.local, "request", None)
	form_cu = frappe.form_dict
	try:
		frappe.local.request = Request(EnvironBuilder(path="/sitemap.xml", method="GET").get_environ())
		frappe.local.form_dict = frappe._dict()
		la("luật định tuyến", resolve_path("sitemap.xml"), "vgb-sitemap.xml")
		r = get_response("sitemap.xml")
		chu = r.get_data(as_text=True) if hasattr(r, "get_data") else str(r.data, "utf-8")
		la("trả 200", r.status_code, 200)
		dung("có trang đặt bánh trên tên miền chính", "https://thevagabondpatisserie.com/banh" in chu)
		dung("không địa chỉ nội bộ", "frappe.cloud" not in chu)
		dung("không trang nhân viên", "/kho-v2" not in chu and "/kiem-banh" not in chu)
	finally:
		# Bench CLI không có request: gán None vẫn làm hasattr đúng (bài học 534).
		if co_request_cu:
			frappe.local.request = request_cu
		else:
			del frappe.local.request
		frappe.local.form_dict = form_cu
	from vagabond.www import vgb_sitemap

	ctx = frappe._dict()
	vgb_sitemap.get_context(ctx)
	dung("bộ điều khiển dựng đúng sơ đồ", "https://thevagabondpatisserie.com/banh" in ctx.so_do and "frappe.cloud" not in ctx.so_do)
