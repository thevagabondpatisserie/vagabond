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
