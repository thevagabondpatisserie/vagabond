"""Hai man danh sach hoa don cho ke toan (anh Viet 12/08/2026).

Hoa don ban ra va hoa don mua vao, moi man mot bang kem chip loc. Truoc
day ke toan phai mo Desk, loc bang bo loc chuan cua ERPNext roi tu doc ma
trang thai tieng Anh; nay len app, trang thai goi bang tieng Viet theo
viec con phai lam.

Khac voi phan he Bao cao: bao cao la SO TONG de nhin xu huong, con hai man
nay la DANH SACH TUNG TO de doi chieu va xu ly.
"""

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

QUYEN_KT = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"Sales Manager",
	"Vagabond Bao cao",
}


def _kiem_quyen():
	if not QUYEN_KT & set(frappe.get_roles()):
		frappe.throw("Danh sách hoá đơn chỉ mở cho kế toán và quản lý.")


def _khoang(so_ngay, tu=None, den=None):
	if tu and den:
		t, d = getdate(tu), getdate(den)
		return (t, d) if t <= d else (d, t)
	so_ngay = int(so_ngay or 30)
	return getdate(add_days(nowdate(), -so_ngay)), getdate(nowdate())


# --------------------------------------------------------- hoa don ban ra

NHOM_BAN = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "nhap", "ten": "Chưa ghi sổ", "ic": "📝"},
	{"k": "chua_hddt", "ten": "Chưa xuất hoá đơn điện tử", "ic": "⚠️"},
	{"k": "cho_ky", "ten": "Chờ ký", "ic": "✍️"},
	{"k": "da_ky", "ten": "Đã ký", "ic": "✅"},
	{"k": "cqt", "ten": "CQT chấp nhận", "ic": "🏛️"},
	{"k": "con_thu", "ten": "Còn phải thu", "ic": "📒"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "✖️"},
]


def _nhom_ban(r):
	if r.get("docstatus") == 2:
		return "huy"
	if r.get("docstatus") == 0:
		return "nhap"
	tt = (r.get("custom_hddt_trang_thai") or "").strip()
	if not (r.get("custom_hddt_so") or "").strip():
		return "chua_hddt"
	if "chấp nhận" in tt.lower():
		return "cqt"
	if tt.lower().startswith("đã ký"):
		return "da_ky"
	if tt:
		return "cho_ky"
	return "cho_ky"


@frappe.whitelist()
def ds_hoa_don_ban(so_ngay=30, tu=None, den=None, quay=None, tu_khoa=""):
	_kiem_quyen()
	t, d = _khoang(so_ngay, tu, den)
	ds = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": ["<", 3], "posting_date": ["between", [str(t), str(d)]]},
		fields=[
			"name", "posting_date", "customer", "customer_name", "grand_total",
			"outstanding_amount", "docstatus", "custom_hddt_so",
			"custom_hddt_trang_thai", "custom_nguon", "vgb_quay",
			"vgb_pt_thanh_toan", "custom_pancake_display_id", "vgb_tam_tinh",
			"vgb_khach_no",
		],
		order_by="posting_date desc, name desc",
		limit_page_length=0,
	)
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		if r.get("vgb_tam_tinh"):
			continue
		diem = (r.vgb_quay or "").strip().upper() or "SALES"
		if quay and diem != str(quay).strip().upper():
			continue
		o = dict(r)
		o["diem"] = diem
		o["nhom"] = _nhom_ban(r)
		o["khach"] = r.vgb_khach_no or r.customer_name or r.customer
		if q and q not in (
			(r.name or "") + " " + (o["khach"] or "") + " "
			+ (r.custom_hddt_so or "") + " " + (r.custom_pancake_display_id or "")
		).lower():
			continue
		ra.append(o)

	dem = {}
	for o in ra:
		dem[o["nhom"]] = dem.get(o["nhom"], 0) + 1
	dem[""] = len(ra)
	dem["con_thu"] = len([o for o in ra if o["docstatus"] == 1 and flt(o["outstanding_amount"]) > 0])
	return {
		"hd": ra,
		"dem": dem,
		"nhom": NHOM_BAN,
		"tu": str(t),
		"den": str(d),
		"tong": sum(flt(o["grand_total"]) for o in ra if o["docstatus"] == 1),
		"con_thu": sum(flt(o["outstanding_amount"]) for o in ra if o["docstatus"] == 1),
	}


# -------------------------------------------------------- hoa don mua vao

NHOM_MUA = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "nhap", "ten": "Chưa ghi sổ", "ic": "📝"},
	{"k": "qua_han", "ten": "Quá hạn trả", "ic": "🔴"},
	{"k": "con_no", "ten": "Còn nợ", "ic": "📒"},
	{"k": "da_tra", "ten": "Đã trả xong", "ic": "✅"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "✖️"},
]


def _nhom_mua(r, hom_nay):
	if r.get("docstatus") == 2:
		return "huy"
	if r.get("docstatus") == 0:
		return "nhap"
	if flt(r.get("outstanding_amount")) <= 0:
		return "da_tra"
	if r.get("due_date") and getdate(r["due_date"]) < hom_nay:
		return "qua_han"
	return "con_no"


@frappe.whitelist()
def ds_hoa_don_mua(so_ngay=60, tu=None, den=None, ncc=None, tu_khoa=""):
	_kiem_quyen()
	t, d = _khoang(so_ngay, tu, den)
	loc = {"docstatus": ["<", 3], "posting_date": ["between", [str(t), str(d)]]}
	if ncc:
		loc["supplier"] = ncc
	ds = frappe.get_all(
		"Purchase Invoice",
		filters=loc,
		fields=[
			"name", "posting_date", "supplier", "supplier_name", "grand_total",
			"outstanding_amount", "docstatus", "due_date", "bill_no", "bill_date",
			"status", "total_qty",
		],
		order_by="posting_date desc, name desc",
		limit_page_length=0,
	)
	hom_nay = getdate(nowdate())
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		o = dict(r)
		o["nhom"] = _nhom_mua(r, hom_nay)
		o["tre_ngay"] = (
			(hom_nay - getdate(r.due_date)).days
			if r.due_date and getdate(r.due_date) < hom_nay and flt(r.outstanding_amount) > 0
			else 0
		)
		if q and q not in (
			(r.name or "") + " " + (r.supplier_name or "") + " " + (r.bill_no or "")
		).lower():
			continue
		ra.append(o)

	dem = {}
	for o in ra:
		dem[o["nhom"]] = dem.get(o["nhom"], 0) + 1
	dem[""] = len(ra)
	return {
		"hd": ra,
		"dem": dem,
		"nhom": NHOM_MUA,
		"tu": str(t),
		"den": str(d),
		"tong": sum(flt(o["grand_total"]) for o in ra if o["docstatus"] == 1),
		"con_no": sum(flt(o["outstanding_amount"]) for o in ra if o["docstatus"] == 1),
	}
