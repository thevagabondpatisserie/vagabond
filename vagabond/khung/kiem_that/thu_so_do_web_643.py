"""v643: trên Frappe thật, /sitemap.xml phải đi qua luật định tuyến về trang
của tiệm (vgb-sitemap.xml), không còn là sơ đồ mặc định ghi địa chỉ nội bộ."""
import frappe

from vagabond.khung.kiem_that.nen import ca, dung, la


@ca("643 /sitemap.xml đi về sơ đồ của tiệm")
def _so_do():
	from frappe.website.path_resolver import resolve_path

	la("luật định tuyến", resolve_path("sitemap.xml"), "vgb-sitemap.xml")
	from vagabond.www import vgb_sitemap

	ctx = frappe._dict()
	vgb_sitemap.get_context(ctx)
	dung("có trang đặt bánh trên tên miền chính", "https://thevagabondpatisserie.com/banh" in ctx.so_do)
	dung("không địa chỉ nội bộ", "frappe.cloud" not in ctx.so_do)
