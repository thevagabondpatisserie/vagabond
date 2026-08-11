"""Phan he hop dong ban hang: catering, event, teabreak, banh thiet ke, B2B.

Man hinh o app /bep goi cac endpoint nay. Mot hop dong gom nhieu hoa don
(Sales Invoice) gan qua truong custom_hop_dong; tien do thu tien tinh tu
grand_total va outstanding_amount cua cac hoa don da submit.
"""

import frappe
from frappe.utils import flt

QUYEN = {"System Manager", "Sales User", "Sales Manager", "Accounts User", "Bộ phận đặt hàng"}


def _quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Không có quyền xem hợp đồng")


def _tong(name):
	"""Tong hop hoa don cua mot hop dong."""
	r = frappe.db.sql(
		"""select count(name), coalesce(sum(grand_total), 0), coalesce(sum(outstanding_amount), 0)
		from `tabSales Invoice` where custom_hop_dong = %s and docstatus = 1""",
		name,
	)[0]
	so_nhap = frappe.db.count(
		"Sales Invoice", {"custom_hop_dong": name, "docstatus": 0, "vgb_huy": 0}
	)
	da_xuat = flt(r[1])
	con_no = flt(r[2])
	return {
		"so_hd_chot": r[0],
		"so_hd_nhap": so_nhap,
		"da_xuat": da_xuat,
		"da_thu": da_xuat - con_no,
		"con_no": con_no,
	}


@frappe.whitelist()
def danh_sach(trang_thai=None):
	_quyen()
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	ds = frappe.get_all(
		"Hop Dong Ban Hang",
		filters=loc,
		fields=["name", "ten", "so_hop_dong", "loai", "trang_thai", "khach_hang", "ngay_su_kien", "gia_tri"],
		order_by="modified desc",
		limit_page_length=200,
	)
	for hd in ds:
		hd.update(_tong(hd["name"]))
	return ds


@frappe.whitelist()
def chi_tiet(name):
	_quyen()
	doc = frappe.get_doc("Hop Dong Ban Hang", name)
	hoa_don = frappe.get_all(
		"Sales Invoice",
		filters={"custom_hop_dong": name, "docstatus": ["<", 2], "vgb_huy": 0},
		fields=["name", "posting_date", "grand_total", "outstanding_amount", "docstatus", "customer_name"],
		order_by="posting_date desc",
		limit_page_length=100,
	)
	kq = {
		"hop_dong": {
			"name": doc.name,
			"ten": doc.ten,
			"so_hop_dong": doc.so_hop_dong,
			"loai": doc.loai,
			"trang_thai": doc.trang_thai,
			"khach_hang": doc.khach_hang,
			"ngay_ky": str(doc.ngay_ky or ""),
			"ngay_su_kien": str(doc.ngay_su_kien or ""),
			"gia_tri": flt(doc.gia_tri),
			"mo_ta": doc.mo_ta or "",
			"ghi_chu": doc.ghi_chu or "",
		},
		"hoa_don": hoa_don,
	}
	kq.update(_tong(name))
	return kq


@frappe.whitelist()
def tao(ten, so_hop_dong=None, loai=None, khach_hang=None, ngay_ky=None, ngay_su_kien=None, gia_tri=0, mo_ta=None, ghi_chu=None):
	_quyen()
	doc = frappe.get_doc(
		{
			"doctype": "Hop Dong Ban Hang",
			"ten": ten,
			"so_hop_dong": so_hop_dong,
			"loai": loai or "Event - Catering",
			"khach_hang": khach_hang or None,
			"ngay_ky": ngay_ky or None,
			"ngay_su_kien": ngay_su_kien or None,
			"gia_tri": flt(gia_tri),
			"mo_ta": mo_ta,
			"ghi_chu": ghi_chu,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def doi_trang_thai(name, trang_thai):
	_quyen()
	hop_le = {"Nháp", "Đang thực hiện", "Hoàn tất", "Đã thanh lý", "Huỷ"}
	if trang_thai not in hop_le:
		frappe.throw("Trạng thái không hợp lệ")
	frappe.db.set_value("Hop Dong Ban Hang", name, "trang_thai", trang_thai)
	return trang_thai


@frappe.whitelist()
def gan_hoa_don(hop_dong, si_name, go=0):
	"""Gan (hoac go) mot hoa don vao hop dong. Dung db_set de gan duoc ca
	hoa don da submit (custom field, khong dung cham vao so lieu)."""
	_quyen()
	if not frappe.db.exists("Sales Invoice", si_name):
		frappe.throw("Không có hoá đơn %s" % si_name)
	frappe.db.set_value("Sales Invoice", si_name, "custom_hop_dong", None if int(go or 0) else hop_dong)
	return si_name


@frappe.whitelist()
def hoa_don_chua_gan(khach_hang=None):
	"""Hoa don 90 ngay gan nhat chua gan hop dong, de tick gan."""
	_quyen()
	loc = {
		"custom_hop_dong": ["in", ["", None]],
		"docstatus": ["<", 2],
		# Hoa don da huy thi khong gan vao hop dong duoc: gan roi la so tien
		# hop dong sai ma khong ai nhin ra.
		"vgb_huy": 0,
		"posting_date": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -90)],
	}
	if khach_hang:
		loc["customer"] = khach_hang
	return frappe.get_all(
		"Sales Invoice",
		filters=loc,
		fields=["name", "posting_date", "customer_name", "grand_total", "docstatus"],
		order_by="posting_date desc",
		limit_page_length=60,
	)
