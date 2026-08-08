"""Tien ich dung chung: doc cau hinh, doc khoa, nho ket qua."""

import frappe

GOONG = "https://rsapi.goong.io"
VIETQR = "https://api.vietqr.io/v2/business"
PANCAKE = "https://pos.pages.fm/api/v1"
TIMEOUT = 12


def cfg():
	return frappe.get_cached_doc("Vagabond Settings")


def key(doc, field):
	"""Doc truong Password ra dang chu."""
	val = doc.get_password(field, raise_exception=False)
	return (val or "").strip()


def cache_get(k):
	return frappe.cache().get_value(k)


def cache_set(k, val, ttl):
	frappe.cache().set_value(k, val, expires_in_sec=ttl)


# ---------------------------------------------------------------------------
# Anh xem truoc (og:image) tach theo ten mien.
#
# Ca hai ten mien order.* va app.* deu tro vao cung mot site, va khach chua
# dang nhap mo "/" thi Frappe deu tra ve trang dat banh. Nghia la mac dinh hai
# ten mien dung chung mot anh xem truoc, ma anh do lai ghi "ORDER.THEVAGABOND
# PATISSERIE.COM" - gui link app cho nhan vien trong Lark, Zalo thi nhin nham.
#
# Hook update_website_context chay cho moi trang web, doc ten mien tu request
# roi doi bo the og khi ten mien bat dau bang "app.". Trang order giu nguyen.
# ---------------------------------------------------------------------------

OG_APP_ANH = "/files/og-vagabond-app.jpg"
OG_APP_TITLE = "The Vagabond Pâtisserie"
OG_APP_MOTA = "Ứng dụng vận hành nội bộ: bếp, kho, vận đơn, mua hàng."


def og_theo_ten_mien(context=None):
	"""Doi anh xem truoc khi mo bang ten mien app.*"""
	if context is None:
		return context
	try:
		host = (frappe.local.request.host or "").split(":")[0].lower()
	except Exception:
		return context
	if not host.startswith("app."):
		return context

	anh = "https://" + host + OG_APP_ANH
	tags = context.get("metatags") or {}
	tags["og:image"] = anh
	tags["og:image:width"] = "1200"
	tags["og:image:height"] = "630"
	tags["twitter:image"] = anh
	tags["twitter:card"] = "summary_large_image"
	tags["og:title"] = OG_APP_TITLE
	tags["title"] = OG_APP_TITLE
	tags["og:description"] = OG_APP_MOTA
	tags["description"] = OG_APP_MOTA
	context["metatags"] = tags
	context["meta_image"] = anh
	context["meta_title"] = OG_APP_TITLE
	context["meta_description"] = OG_APP_MOTA
	return context
