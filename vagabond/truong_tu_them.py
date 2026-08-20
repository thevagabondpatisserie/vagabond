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
	from vagabond import (
		ban_hang, bao_gia, chung_tu_tien, diem_otp, duyet_ycmh, hoan_tien,
		mua_dich_vu, noi_bo, sepay,
	)

	_dung_nhom(duyet_ycmh.TRUONG_MOI, "duyet_ycmh")
	_dung_nhom(ban_hang.TRUONG_MOI, "ban_hang")
	_dung_nhom(diem_otp.TRUONG_MOI, "diem_otp")
	_dung_nhom(noi_bo.TRUONG_MOI, "noi_bo")
	_dung_nhom(hoan_tien.TRUONG_MOI, "hoan_tien")
	_dung_nhom(chung_tu_tien.TRUONG_MOI, "chung_tu_tien")
	_dung_nhom(bao_gia.TRUONG_MOI, "bao_gia")
	_dung_nhom(bao_gia.TRUONG_CAI_DAT, "bao_gia_cai_dat")
	_dung_nhom(bao_gia.TRUONG_MAU, "bao_gia_mau_in")
	_dung_nhom(mua_dich_vu.TRUONG_MOI, "mua_dich_vu")
	_dung_nhom(sepay.TRUONG_MOI, "sepay")
	# M-Invoice: cau hinh keo PDF ban the hien (them 20/08/2026).
	from vagabond import minvoice_tep

	_dung_nhom(minvoice_tep.TRUONG_MOI, "minvoice_tep")
	# Kho Hang Huy: dung lai moi lan Migrate, lap lai duoc.
	try:
		hoan_tien.dung_kho_huy()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: kho hang huy")
	try:
		from vagabond import hop_thu

		hop_thu.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: hop thu")
	# Cot trang thai gui email: CHEN THEM lua chon "Dang cho gui" vao truong
	# cu, khong khai lai ca truong. Xem tai lieu trong trang_thai_thu.dung.
	try:
		from vagabond import trang_thai_thu

		trang_thai_thu.dung()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "truong_tu_them: trang thai thu")
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
