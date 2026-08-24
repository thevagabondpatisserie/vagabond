# -*- coding: utf-8 -*-
"""Nhat ky cua nhip dong bo Pancake: ghi lai MOI thay doi may tu lam.

Vi sao can
----------
Ngay 19/08/2026 anh Viet hoi vi sao don 91928 nam sai ngay giao. De tra loi
cau do em phai mo ma nguon doc tung dong, vi trong he thong khong co mot dau
vet nao cua nhip dong bo: Error Log chi ghi khi CO LOI, con nhip chay thanh
cong thi im lang tuyet doi.

Tep nay chua cai thieu do. Moi lan nhip dong bo doi mot o cua vet don, no ghi
lai: don nao, o nao, tu gia tri gi sang gia tri gi, luc may gio, nhip nao lam.
Lan sau ai hoi "sao don nay lai the" thi tra ra trong mot phut.

Quy tac cua tep nay
-------------------
1. KHONG BAO GIO nem loi. Nhat ky hong thi viec giao hang van phai chay. Moi
   ham deu boc trong try, that bai thi thoi.
2. Chi ghi khi CO THAY DOI THAT. Ghi ca nhung lan khong doi gi thi mot ngay
   sinh ra hang chuc nghin dong rac, va thu can tim se chim trong do.
3. Viec nao NGUOI phai xem thi danh dau can_nguoi_xem, de man hinh loc ra
   duoc. Vi du: Pancake doi ngay giao cua don shipper dang cam tren duong.
"""

import frappe
from frappe.utils import cint

DT = "Vagabond Nhat Ky Dong Bo"

# So ngay giu nhat ky. Qua han thi don, vi day la vet ky thuat chu khong
# phai chung tu ke toan.
NGAY_GIU = 90


def ghi(nhip, ma_don, doi_tuong, ten_doi_tuong, viec,
        truong="", cu="", moi="", can_nguoi_xem=0, ghi_chu=""):
	"""Ghi mot dong nhat ky. Nuot moi loi.

	nhip            ten nhip, vi du "van_don"
	ma_don          ma don Pancake cho de tra
	doi_tuong       ten doctype bi tac dong, vi du "Van Don"
	ten_doi_tuong   ten ban ghi, vi du "VD-2026-00750"
	viec            mot cum ngan, vi du "doi ngay giao"
	truong          ten o bi doi
	cu, moi         gia tri truoc va sau
	can_nguoi_xem   1 neu con nguoi phai nhin va xu ly
	"""
	try:
		d = frappe.new_doc(DT)
		d.update({
			"nhip": str(nhip or "")[:60],
			"ma_don": str(ma_don or "")[:60],
			"doi_tuong": str(doi_tuong or "")[:60],
			"ten_doi_tuong": str(ten_doi_tuong or "")[:140],
			"viec": str(viec or "")[:140],
			"truong": str(truong or "")[:60],
			"gia_tri_cu": ("" if cu is None else str(cu))[:500],
			"gia_tri_moi": ("" if moi is None else str(moi))[:500],
			"can_nguoi_xem": 1 if cint(can_nguoi_xem) else 0,
			"ghi_chu": str(ghi_chu or "")[:500],
		})
		d.insert(ignore_permissions=True)
		return d.name
	except Exception:
		try:
			frappe.log_error(frappe.get_traceback(), "nhat_ky_dong_bo: khong ghi duoc")
		except Exception:
			pass
		return None


def ghi_nhieu(nhip, ma_don, doi_tuong, ten_doi_tuong, viec, cac_o, can_nguoi_xem=0):
	"""Ghi mot loat o cung doi trong mot luot.

	cac_o la dict {ten_o: (gia_tri_cu, gia_tri_moi)}. Chi ghi cac o that su
	co doi - ben goi da loc roi thi cu truyen thang.
	"""
	ra = []
	for o, (cu, moi) in (cac_o or {}).items():
		n = ghi(nhip, ma_don, doi_tuong, ten_doi_tuong, viec, o, cu, moi, can_nguoi_xem)
		if n:
			ra.append(n)
	return ra


@frappe.whitelist()
def ds(so_dong=100, chi_can_xem=0, ma_don="", nhip=""):
	"""Danh sach nhat ky cho man hinh soi. CHI DOC."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	loc = {}
	if cint(chi_can_xem):
		loc["can_nguoi_xem"] = 1
		loc["da_xem"] = 0
	if (ma_don or "").strip():
		loc["ma_don"] = ["like", "%%%s%%" % ma_don.strip()]
	if (nhip or "").strip():
		loc["nhip"] = nhip.strip()
	return frappe.get_all(
		DT, filters=loc,
		fields=["name", "creation", "nhip", "ma_don", "doi_tuong", "ten_doi_tuong",
		        "viec", "truong", "gia_tri_cu", "gia_tri_moi", "can_nguoi_xem",
		        "da_xem", "ghi_chu"],
		order_by="creation desc",
		limit_page_length=min(int(so_dong or 100), 500),
	)


@frappe.whitelist()
def danh_da_xem(name=None):
	"""Nguoi da xem va xu ly xong mot canh bao."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, name):
		frappe.throw("Không có dòng nhật ký %s. Vui lòng tải lại màn hình." % name)
	frappe.db.set_value(DT, name, "da_xem", 1)
	return {"ok": 1}


@frappe.whitelist()
def so_can_xem():
	"""Dem so canh bao chua ai xem, de gan chip do len the."""
	try:
		return {"so": frappe.db.count(DT, {"can_nguoi_xem": 1, "da_xem": 0})}
	except Exception:
		return {"so": 0}


def don_cu():
	"""Don nhat ky qua han. Scheduler goi mot lan moi ngay."""
	from frappe.utils import add_days, nowdate

	moc = add_days(nowdate(), -NGAY_GIU)
	try:
		frappe.db.sql(
			"delete from `tab%s` where creation < %%s and can_nguoi_xem = 0" % DT,
			(moc,),
		)
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nhat_ky_dong_bo: don cu")
