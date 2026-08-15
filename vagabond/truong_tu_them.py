"""Cac truong tu them do MA NGUON khai, dung lai sau moi lan deploy.

Vi sao co file nay
------------------
Toan bo truong tu them cua he tu truoc toi nay deu bam tay tren Desk. Hai
cai gia phai tra: site thu va site that lech nhau ma khong ai biet, va doc
ma nguon khong bao gio hieu duoc vi sao co truong do.

Tu 15/08/2026 truong moi khai o day. Ham dung() chay trong after_migrate
nen moi lan deploy la Frappe tu dung lai; khai lai lan hai khong sao vi
create_custom_fields la thao tac lap lai duoc.

KHONG dua cac truong cu vao day. Chung dang chay that, khai lai chi de ra
rui ro ghi de nham. File nay chi giu truong sinh ra tu hom nay tro di.
"""

import frappe


def dung():
	"""Dung moi truong tu them do ma nguon khai. Goi tu after_migrate."""
	from vagabond import ban_hang, duyet_ycmh

	_dung_nhom(duyet_ycmh.TRUONG_MOI, "duyet_ycmh")
	_dung_nhom(ban_hang.TRUONG_MOI, "ban_hang")
	try:
		duyet_ycmh._them_trang_thai_tu_choi()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: trang thai tu choi")


def _dung_nhom(khai, ten_nhom):
	"""Dung mot nhom truong. Hong nhom nay khong duoc keo do ca lan deploy."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	try:
		create_custom_fields(khai, update=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: %s" % ten_nhom)
