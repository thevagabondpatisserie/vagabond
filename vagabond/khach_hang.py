# -*- coding: utf-8 -*-
"""Danh sach khach hang de tra cuu: phan theo DANG khach (si hay le) va
HANG khach (anh Viet 11/08/2026).

Hang xet theo chi tieu: EXPLORER thap nhat, roi VOYAGER, roi VAGABONDER.
Hai hang gan tay: FAMILY giam 20% cho so dien thoai nhan vien, AMBASSADOR
giam vinh vien 10%.

Muc chi tieu tung hang nam trong doctype "Vagabond Hang Khach" chu khong
nhet trong ma - anh Viet chot con so luc nao thi sua o do, khong phai doi
deploy.
"""

import frappe
from frappe.utils import add_months, flt, getdate, nowdate

from vagabond.ban_hang import _kiem_quyen

# Nhom khach ben ERPNext nao duoc coi la khach SI. Nhan dien theo TEN nhom
# chu khong liet ke cung, vi ke toan hay them nhom moi (hien co "Khach si
# B2B", truoc do la "Khach si"). Con lai la khach le.
def _la_si(nhom):
	n = (nhom or "").strip().lower()
	return ("sỉ" in n) or ("si b2b" in n) or ("wholesale" in n) or ("b2b" in n)


def _nhom_si():
	"""Danh sach ten nhom khach duoc coi la si, doc that tu danh muc."""
	try:
		ds = frappe.get_all("Customer Group", fields=["name"], limit_page_length=0)
	except Exception:
		return []
	return [r["name"] for r in ds if _la_si(r["name"])]


@frappe.whitelist()
def ds_hang():
	"""Bang hang khach dang cau hinh, xep tu thap len cao."""
	_kiem_quyen()
	try:
		ds = frappe.get_all(
			"Vagabond Hang Khach",
			filters={"bat": 1},
			fields=["name", "ten_hang", "thu_tu", "loai", "giam_gia", "chi_tieu_tu", "so_thang_xet", "mo_ta"],
			order_by="thu_tu asc",
			limit_page_length=0,
		)
	except Exception:
		return {"hang": []}
	return {"hang": ds}


def _chi_tieu(ds_khach, so_thang=12):
	"""Tong tien da mua cua tung khach trong ky xet."""
	if not ds_khach:
		return {}
	tu = add_months(getdate(nowdate()), -abs(int(so_thang or 12)))
	rows = frappe.get_all(
		"Sales Invoice",
		filters={
			"docstatus": 1,
			"customer": ["in", ds_khach],
			"posting_date": [">=", str(tu)],
		},
		fields=["customer", "grand_total", "posting_date"],
		limit_page_length=0,
	)
	ra = {}
	for r in rows:
		o = ra.setdefault(r.customer, {"tien": 0.0, "so_don": 0, "gan_nhat": None})
		o["tien"] += flt(r.grand_total)
		o["so_don"] += 1
		if not o["gan_nhat"] or str(r.posting_date) > o["gan_nhat"]:
			o["gan_nhat"] = str(r.posting_date)
	return ra


@frappe.whitelist()
def ds_khach(tu_khoa="", dang="", hang=""):
	"""Danh sach khach hang de tra cuu, kem chi tieu va hang.

	Chi tieu tinh trong 12 thang gan nhat theo hoa don DA GHI SO - don con
	o ban nhap chua phai la tien that.
	"""
	_kiem_quyen()
	q = (tu_khoa or "").strip()
	# Loc phai chay o MAY CHU truoc khi cat bot, khong thi khach si nam
	# cuoi bang chu cai se bien mat: co 1545 khach ma chi tai 500 cai dau
	# thi 5 khach si B2B khong bao gio hien ra (bat duoc 11/08/2026).
	loc = {"disabled": 0}
	nhom_si = _nhom_si()
	if dang == "si":
		if not nhom_si:
			return {"khach": [], "tong_tien": 0, "so_si": 0, "so_le": 0, "tong_so": 0}
		loc["customer_group"] = ["in", nhom_si]
	elif dang == "le" and nhom_si:
		loc["customer_group"] = ["not in", nhom_si]
	if hang == "_chua":
		loc["vgb_hang"] = ["in", ["", None]]
	elif hang:
		loc["vgb_hang"] = hang
	doi = {
		"doctype": "Customer",
		"filters": loc,
		"fields": [
			"name", "customer_name", "customer_group", "tax_id",
			"mobile_no", "territory", "creation",
		],
		"order_by": "customer_name asc",
		"limit_page_length": 400,
	}
	if q:
		doi["or_filters"] = {
			"name": ["like", "%" + q + "%"],
			"customer_name": ["like", "%" + q + "%"],
			"tax_id": ["like", "%" + q + "%"],
			"mobile_no": ["like", "%" + q + "%"],
		}
	try:
		tong_so = frappe.db.count("Customer", loc)
	except Exception:
		tong_so = 0
	ds = frappe.get_all(**doi)

	# Truong hang nam o Custom Field tren Customer. Doc rieng de neu chua
	# tao field thi man hinh van chay, chi la chua ai co hang.
	hang_map = {}
	try:
		for r in frappe.get_all(
			"Customer",
			filters={"name": ["in", [x["name"] for x in ds]]},
			fields=["name", "vgb_hang"],
			limit_page_length=0,
		):
			if r.get("vgb_hang"):
				hang_map[r["name"]] = r["vgb_hang"]
	except Exception:
		hang_map = {}

	ct = _chi_tieu([r["name"] for r in ds])
	bang_hang = {h["name"]: h for h in (ds_hang().get("hang") or [])}

	ra = []
	for r in ds:
		o = ct.get(r["name"]) or {}
		h = hang_map.get(r["name"]) or ""
		hd = bang_hang.get(h) or {}
		ra.append(
			{
				"ma": r["name"],
				"ten": r.get("customer_name") or r["name"],
				"nhom": r.get("customer_group") or "",
				"si": 1 if _la_si(r.get("customer_group")) else 0,
				"mst": r.get("tax_id") or "",
				"dt": r.get("mobile_no") or "",
				"hang": h,
				"giam": flt(hd.get("giam_gia")),
				"tien": flt(o.get("tien")),
				"so_don": int(o.get("so_don") or 0),
				"gan_nhat": o.get("gan_nhat") or "",
			}
		)

	# Khach chi nhieu nhat len dau - do la khach can cham nhat.
	ra.sort(key=lambda x: -x["tien"])
	try:
		so_si = frappe.db.count("Customer", {"disabled": 0, "customer_group": ["in", nhom_si]}) if nhom_si else 0
		so_tat = frappe.db.count("Customer", {"disabled": 0})
	except Exception:
		so_si, so_tat = 0, len(ra)
	return {
		"khach": ra,
		"tong_tien": sum(x["tien"] for x in ra),
		"so_si": so_si,
		"so_le": max(0, so_tat - so_si),
		"tong_so": tong_so,
		"da_tai": len(ra),
	}


@frappe.whitelist()
def dat_hang(khach=None, hang=None):
	"""Gan hang cho mot khach. Hang gan tay (FAMILY, AMBASSADOR) chi quan
	ly moi dat duoc, nen di qua ham nay chu khong sua thang tren Desk."""
	_kiem_quyen()
	khach = (khach or "").strip()
	hang = (hang or "").strip().upper()
	if not khach or not frappe.db.exists("Customer", khach):
		frappe.throw("Không có khách hàng %s." % (khach or "(trống)"))
	if hang and not frappe.db.exists("Vagabond Hang Khach", hang):
		frappe.throw("Không có hạng %s trong danh mục." % hang)
	frappe.db.set_value("Customer", khach, "vgb_hang", hang or None)
	frappe.db.commit()
	return {"khach": khach, "hang": hang}


@frappe.whitelist()
def goi_y_hang(khach=None):
	"""Hang ma khach DANG DUOC HUONG theo chi tieu, de quan ly doi chieu
	voi hang dang gan. Khong tu doi hang - doi hang la viec cua nguoi."""
	_kiem_quyen()
	khach = (khach or "").strip()
	if not khach:
		return {}
	bang = [
		h for h in (ds_hang().get("hang") or [])
		if (h.get("loai") or "Theo chi tieu") == "Theo chi tieu"
	]
	if not bang:
		return {"hang": "", "tien": 0}
	so_thang = max([int(h.get("so_thang_xet") or 12) for h in bang] or [12])
	ct = _chi_tieu([khach], so_thang).get(khach) or {}
	tien = flt(ct.get("tien"))
	dat = ""
	for h in sorted(bang, key=lambda x: flt(x.get("chi_tieu_tu"))):
		if tien >= flt(h.get("chi_tieu_tu")):
			dat = h["name"]
	return {"hang": dat, "tien": tien, "so_thang": so_thang}
