# -*- coding: utf-8 -*-
"""Ô "Số séc/tham chiếu" và "Ngày séc/tham chiếu" trên phiếu thu chi.

VÌ SAO CÓ TỆP NÀY (issue #252, 10/09/2026)
--------------------------------------------------------------------
ERPNext bắt buộc hai ô đó khi một vế của phiếu là tài khoản ngân hàng.
Ngày 07/08/2026 đã bỏ bắt buộc cho chị Dung, nhưng bỏ bằng Property
Setter và Server Script sửa thẳng trên Desk, tức nằm trong cơ sở dữ liệu,
không nằm trong mã nguồn. Đến 10/09 chị Dung lập uỷ nhiệm chi trả nhà
cung cấp thì lại bị chặn "Số séc/tham chiếu is required": thứ đặt tay
trên Desk không có gì giữ, mất lúc nào không ai hay, và mất rồi không
có lịch sử để biết.

Nay đưa cả hai việc vào mã nguồn:
  1. `dung()` khai lại Property Setter mỗi lần Migrate, lặp lại được.
  2. `dien_khi_trong` là hook validate: trống thì tự điền, để đối chiếu
     ngân hàng không bị trống dữ liệu. Có sẵn mã FT thật của ngân hàng
     (phiếu thu SePay tự lập) thì giữ nguyên, không đè.

Không đụng phiếu đã ghi sổ, không đụng số tiền, không đụng tài khoản.
"""

import frappe
from frappe.utils import getdate

from vagabond.chung_tu_tien import cham_ngan_hang

LOAI = "Payment Entry"
CAC_O = ("reference_no", "reference_date")


# ------------------------------------------------------------ phep THUAN


def so_tham_chieu_mac_dinh(ngay):
	"""Số tham chiếu khi người lập không có số nào: CK-ngày hạch toán. THUẦN.

	Cùng dạng với Server Script ngày 07/08/2026 đã dùng, để phiếu cũ và
	phiếu mới nhìn giống nhau trên sổ.
	"""
	d = getdate(ngay) if ngay else None
	return "CK-%s" % d.strftime("%Y%m%d") if d else "CK"


def can_dien(paid_from, paid_to, reference_no, reference_date,
		paid_from_account_type=None, paid_to_account_type=None):
	"""Phiếu này có cần máy điền tham chiếu không, và điền ô nào. THUẦN.

	Chỉ điền khi có vế ngân hàng (đúng lúc ERPNext đòi), và chỉ ô nào
	đang trống. Phiếu tiền mặt không đụng.
	"""
	# Core danh dau bat buoc theo account_type, trong khi nghiep vu Vagabond
	# nhan tai khoan ngan hang theo so 112. Xet ca hai de mot tai khoan khai
	# nham type Bank (tung co o 1411) cung khong bi core chan truoc hook.
	if not (cham_ngan_hang(paid_from, paid_to)
			or paid_from_account_type == "Bank" or paid_to_account_type == "Bank"):
		return []
	ra = []
	if not str(reference_no or "").strip():
		ra.append("reference_no")
	if not reference_date:
		ra.append("reference_date")
	return ra


# ------------------------------------------------------------------ hook


def dien_khi_trong(doc, method=None):
	"""Hook validate của Payment Entry: trống thì điền, có rồi thì giữ."""
	o = can_dien(doc.get("paid_from"), doc.get("paid_to"),
		doc.get("reference_no"), doc.get("reference_date"),
		doc.get("paid_from_account_type"), doc.get("paid_to_account_type"))
	if "reference_date" in o:
		doc.reference_date = doc.get("posting_date") or getdate()
	if "reference_no" in o:
		doc.reference_no = so_tham_chieu_mac_dinh(doc.get("posting_date"))


# ---------------------------------------------------------------- migrate


def dung():
	"""Bỏ bắt buộc hai ô tham chiếu, bằng Property Setter do mã nguồn giữ.

	Gọi từ patches/dong_bo_cau_truc.py mỗi lần Migrate. Lặp lại được:
	make_property_setter ghi đè đúng một bản ghi theo (doctype, field,
	property). Ai lỡ xoá trên Desk thì lần deploy sau tự có lại.

	ERPNext đặt bắt buộc ở `mandatory_depends_on` (khi có vế Bank) chứ
	không phải `reqd`, nên phải xoá cả hai; xoá mỗi reqd là vẫn bị chặn.
	"""
	from frappe.custom.doctype.property_setter.property_setter import (
		make_property_setter,
	)

	ra = []
	for o in CAC_O:
		try:
			make_property_setter(LOAI, o, "reqd", 0, "Check", validate_fields_for_doctype=False)
			make_property_setter(LOAI, o, "mandatory_depends_on", "", "Code",
				validate_fields_for_doctype=False)
			ra.append(o)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tham_chieu_tien: bo bat buoc %s" % o)
	if ra:
		frappe.clear_cache(doctype=LOAI)
	return {"da_dat": ra}
