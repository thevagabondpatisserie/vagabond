"""Ban hang: doanh so ngay tu Pancake thanh Hoa don ban hang (Sales Invoice).

Chot voi anh Viet 01/08/2026:
- MOI don Pancake giao THANH CONG trong ngay (status 3 da nhan, 16 da thu tien,
  loc theo ngay giao estimate_delivery_date) thanh MOT Sales Invoice nhap.
- GIAI DOAN 1 KHONG cap nhat kho (update_stock = 0), chi ghi doanh thu.
- Loan Anh ra soat tren man "Doanh so ngay" cua app /bep roi bam Chot,
  may submit ca loat.
- Don co yeu cau hoa don cong ty (Vagabond Hoa Don) day sang m-invoice
  o che do CHO KY (InvoiceApi78/Save), ke toan ky tay giai doan dau.

Chong trung: SI mang custom_pancake_id (id noi bo cua Pancake). Dong bo
chay lai bao nhieu lan cung chi co mot hoa don cho mot don.
"""

import json
import re

import frappe
import requests
from frappe.utils import flt, getdate, now_datetime, nowdate

from vagabond.kiem_banh import _keo_don, _khoang_unix
from vagabond.lib import TIMEOUT, cache_get, cache_set, cfg, key

# Trang thai Pancake tinh vao doanh so: 3 da nhan, 16 da thu tien.
TT_DOANH_SO = {3, 16}

KHACH_LE = "Khách lẻ Online"
# DVBH00001 la item "Phí Dịch Vụ Vận Chuyển" co san ben Next (bo ma chuan).
MA_PHI_GIAO = "DVBH00001"

QUYEN_BAN_HANG = {"System Manager", "Sales User", "Sales Manager", "Bộ phận đặt hàng"}


def _kiem_quyen():
	if not QUYEN_BAN_HANG & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền ghi nhận doanh số.")


def _cong_ty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _khach_le():
	"""Khach le online dung chung. Ten that cua khach nam o remarks tung hoa don."""
	if frappe.db.exists("Customer", KHACH_LE):
		return KHACH_LE
	nhom = (
		frappe.db.get_single_value("Selling Settings", "customer_group")
		or frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	)
	vung = frappe.db.get_single_value("Selling Settings", "territory") or frappe.db.get_value(
		"Territory", {"is_group": 0}, "name"
	)
	kh = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": KHACH_LE,
			"customer_type": "Individual",
			"customer_group": nhom,
			"territory": vung,
		}
	)
	kh.insert(ignore_permissions=True)
	return kh.name


def _item_phi_giao():
	"""Item dich vu phi giao hang thu cua khach - khong ton kho."""
	if frappe.db.exists("Item", MA_PHI_GIAO):
		return MA_PHI_GIAO
	nhom = None
	for ung_vien in ("Dịch vụ", "Services"):
		if frappe.db.exists("Item Group", ung_vien):
			nhom = ung_vien
			break
	if not nhom:
		nhom = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	it = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": MA_PHI_GIAO,
			"item_name": "Phí giao hàng",
			"item_group": nhom,
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_sales_item": 1,
			"is_purchase_item": 0,
		}
	)
	it.insert(ignore_permissions=True)
	return it.name


def _dong_hang(o):
	"""Dich items cua don Pancake sang dong hoa don. Tra (rows, thieu_ma)."""
	rows, thieu = [], []
	for it in o.get("items") or []:
		vi = it.get("variation_info") or {}
		ma = str(vi.get("display_id") or "").strip()
		sl = flt(it.get("quantity") or 0)
		if not sl:
			continue
		if ma and not frappe.db.exists("Item", ma):
			# Pancake tu sinh hau to size cho mau ma (vd BAWC00115S16CM,
			# BAWC00127MINI12CM); thu bo hau to de khop ma goc ben Next.
			goc = re.sub(r"(MINI|[SML])\d{1,2}CM$", "", ma, flags=re.IGNORECASE)
			if goc != ma and frappe.db.exists("Item", goc):
				ma = goc
		if not ma or not frappe.db.exists("Item", ma):
			# Nhieu san pham Pancake bi dat ma "1"/"2": thu khop dung ten mon
			# voi item_name ben Next (khong phan biet hoa thuong).
			ten = (vi.get("name") or it.get("product_name") or "").strip()
			ma_theo_ten = frappe.db.get_value("Item", {"item_name": ten}, "name") if ten else None
			if ma_theo_ten:
				ma = ma_theo_ten
			else:
				thieu.append("%s (%s)" % (ma or "(trống)", ten or "?"))
				continue
		gia = flt(vi.get("retail_price") or 0)
		giam = flt(it.get("discount_each_product") or 0)
		rows.append(
			{
				"item_code": ma,
				"qty": sl,
				"rate": max(gia - giam, 0),
			}
		)
	phi_giao = flt(o.get("shipping_fee") or 0)
	if phi_giao > 0:
		rows.append({"item_code": _item_phi_giao(), "qty": 1, "rate": phi_giao})
	return rows, thieu


PT_KENH = (
	("cash", "Tiền mặt", "tiền mặt"),
	("transfer_money", "Chuyển khoản", "chuyển khoản"),
	("charged_by_onepay", "OnePay", "OnePay"),
	("charged_by_card", "", "cà thẻ (chọn máy Payoo/Shinhan)"),
	("charged_by_momo", "", "Momo"),
	("charged_by_vnpay", "", "VNPay"),
	("charged_by_qrpay", "", "QR Pay"),
)


def _vnd(so):
	return "{:,.0f}".format(so).replace(",", ".")


def _doan_thanh_toan(o):
	"""Doan phuong thuc thanh toan tu cac o tien cua don Pancake.

	Tra (pt, ghi_chu). pt rong = chua ro, sales chon tay o man doanh thu
	truoc khi ghi so. Ca the (charged_by_card) khong phan biet duoc may
	Payoo hay ShinhanBank nen khong tu dien - so tien van vao ghi chu de
	ke toan doi soat (anh Viet chot 02/08).
	"""
	thay = []
	pt_ro = []
	mo_ho = 0
	for truong, ten_pt, nhan in PT_KENH:
		try:
			so = float(o.get(truong) or 0)
		except (TypeError, ValueError):
			so = 0
		if so <= 0:
			continue
		thay.append("%s %s" % (nhan, _vnd(so)))
		if ten_pt:
			if ten_pt not in pt_ro:
				pt_ro.append(ten_pt)
		else:
			mo_ho += 1
	try:
		tra_truoc = float(o.get("prepaid") or 0)
	except (TypeError, ValueError):
		tra_truoc = 0
	if tra_truoc > 0 and not thay:
		thay.append("trả trước %s (chưa rõ kênh)" % _vnd(tra_truoc))
	pt = pt_ro[0] if (len(pt_ro) == 1 and not mo_ho) else ""
	ghi = ("Pancake: " + " + ".join(thay)) if thay else ""
	return pt, ghi


def _upsert_hoa_don(o, ngay, cong_ty, khach):
	"""Mot don Pancake = mot Sales Invoice nhap. Tra (trang_thai, ghi_chu)."""
	pid = str(o.get("id") or "")
	did = str(o.get("display_id") or o.get("id") or "")
	cu = frappe.db.get_value(
		"Sales Invoice", {"custom_pancake_id": pid}, ["name", "docstatus"], as_dict=True
	)
	if cu and cu.docstatus == 1:
		return "da_chot", cu.name
	if cu and cu.docstatus == 2:
		return "da_huy_si", cu.name

	rows, thieu = _dong_hang(o)
	if thieu:
		return "thieu_ma", "Đơn %s thiếu mã: %s" % (did, ", ".join(sorted(set(thieu))))
	if not rows:
		return "rong", did

	ten_khach = (o.get("bill_full_name") or "").strip()
	sdt = (o.get("bill_phone_number") or "").strip()
	giam_don = flt(o.get("total_discount") or o.get("discount") or 0)

	if cu:
		si = frappe.get_doc("Sales Invoice", cu.name)
		si.items = []
	else:
		si = frappe.new_doc("Sales Invoice")

	si.update(
		{
			"company": cong_ty,
			"customer": khach,
			"posting_date": str(ngay),
			"set_posting_time": 1,
			"due_date": str(ngay),
			"update_stock": 0,
			"custom_pancake_id": pid,
			"custom_pancake_display_id": did,
			"custom_nguon": "Pancake",
			"apply_discount_on": "Grand Total",
			"discount_amount": giam_don,
			"remarks": "Pancake #%s - %s%s" % (did, ten_khach or "Khách lẻ", " - " + sdt if sdt else ""),
		}
	)
	pt_tt, ghi_tt = _doan_thanh_toan(o)
	if pt_tt and frappe.db.exists("Mode of Payment", pt_tt):
		si.vgb_pt_thanh_toan = pt_tt
	if ghi_tt:
		si.vgb_ghi_chu_doi_soat = ghi_tt
	for r in rows:
		si.append("items", r)
	si.flags.ignore_permissions = True
	si.save()
	return ("tao_moi" if not cu else "cap_nhat"), si.name


@frappe.whitelist()
def dong_bo_doanh_so(ngay=None):
	"""Keo don Pancake giao thanh cong cua mot ngay ve thanh SI nhap."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k:
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")

	dau, cuoi = _khoang_unix(ngay)
	dons = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
	dons = [o for o in dons if o.get("status") in TT_DOANH_SO]

	cong_ty = _cong_ty()
	khach = _khach_le()
	kq = {"tao_moi": 0, "cap_nhat": 0, "da_chot": 0, "loi": []}
	for o in dons:
		try:
			tt, ghi_chu = _upsert_hoa_don(o, ngay, cong_ty, khach)
			if tt in ("tao_moi", "cap_nhat", "da_chot"):
				kq[tt] += 1
			elif tt == "thieu_ma":
				kq["loi"].append(ghi_chu)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang: don %s" % o.get("display_id"))
			kq["loi"].append("Đơn %s lỗi khi tạo, xem Error Log." % o.get("display_id"))
	frappe.db.commit()
	cache_set("bh_loi_%s" % ngay, json.dumps(kq["loi"]), 6 * 3600)
	cache_set("bh_luc_%s" % ngay, str(now_datetime())[:16], 6 * 3600)
	kq["so_don_pancake"] = len(dons)
	return kq


@frappe.whitelist()
def bang_doanh_so(ngay=None):
	"""Du lieu cho man 'Doanh so ngay' cua app /bep."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	sis = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay, "custom_pancake_id": ["!=", ""]},
		fields=[
			"name",
			"docstatus",
			"grand_total",
			"remarks",
			"custom_pancake_display_id",
			"custom_hddt_trang_thai",
			"custom_hddt_so",
			"custom_nguon",
			"vgb_pt_thanh_toan",
		],
		order_by="custom_pancake_display_id",
	)
	loi = json.loads(cache_get("bh_loi_%s" % ngay) or "[]")
	hd_cty = {
		r.ma_don: r
		for r in frappe.db.get_all(
			"Vagabond Hoa Don",
			fields=["ma_don", "ten_cong_ty", "tinh_trang"],
			filters={"ma_don": ["in", [s.custom_pancake_display_id for s in sis] or [""]]},
		)
	}
	for s in sis:
		s["can_hddt"] = 1 if s.custom_pancake_display_id in hd_cty else 0
	return {
		"ngay": str(ngay),
		"dong_bo_luc": cache_get("bh_luc_%s" % ngay) or "",
		"rows": sis,
		"loi": loi,
		"tong_nhap": sum(s.grand_total for s in sis if s.docstatus == 0),
		"tong_chot": sum(s.grand_total for s in sis if s.docstatus == 1),
	}


@frappe.whitelist()
def chot_doanh_so(ngay=None):
	"""Submit ca loat SI nhap cua ngay. Loan Anh bam sau khi ra soat."""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	ds = frappe.db.get_all(
		"Sales Invoice",
		filters={"posting_date": ngay, "custom_pancake_id": ["!=", ""], "docstatus": 0},
		pluck="name",
	)
	xong, loi = 0, []
	for ten in ds:
		try:
			si = frappe.get_doc("Sales Invoice", ten)
			si.flags.ignore_permissions = True
			si.submit()
			xong += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ban_hang chot: %s" % ten)
			loi.append(ten)
	frappe.db.commit()
	return {"da_chot": xong, "loi": loi}


def dong_bo_doanh_so_tu_dong():
	"""Cron: tu keo doanh so hom nay, sales chi viec ra soat cuoi ngay."""
	try:
		frappe.set_user("Administrator")
		dong_bo_doanh_so(nowdate())
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ban_hang cron")


@frappe.whitelist()
def chot_mot_don(si_name, pt=None):
	"""Submit mot don le, sales ra soat xong don nao chot don do."""
	_kiem_quyen()
	si = frappe.get_doc("Sales Invoice", si_name)
	if not si.custom_pancake_id:
		frappe.throw("Phiếu này không phải doanh thu sales.")
	if si.docstatus != 0:
		frappe.throw("Đơn này đã chốt rồi.")
	if pt:
		if not frappe.db.exists("Mode of Payment", pt):
			frappe.throw("Không có phương thức thanh toán %s" % pt)
		si.vgb_pt_thanh_toan = pt
	si.flags.ignore_permissions = True
	si.submit()
	frappe.db.commit()
	return {"ok": 1, "name": si.name}


@frappe.whitelist()
def tao_don_tay(ngay=None, nguon="Grab", ma_don="", ten_khach="", dien_thoai="", items=None, giam_gia=0, phi_ship=0):
	"""Nhap tay doanh thu tu kenh khong co API (Grab Merchant, Be, GreenSM...).

	Grab co muc Giam gia (chiet khau san) nen nhan giam_gia rieng,
	tru vao Grand Total giong giam gia don Pancake.
	"""
	_kiem_quyen()
	ngay = getdate(ngay or nowdate())
	if isinstance(items, str):
		items = json.loads(items or "[]")
	rows = []
	for r in items or []:
		ma = (r.get("item_code") or "").strip()
		if not ma or not frappe.db.exists("Item", ma):
			frappe.throw("Không có mã hàng %s trong hệ thống." % (ma or "(trống)"))
		sl = flt(r.get("qty") or 0)
		if sl <= 0:
			frappe.throw("Số lượng của %s phải lớn hơn 0." % ma)
		rows.append({"item_code": ma, "qty": sl, "rate": flt(r.get("rate") or 0)})
	if not rows:
		frappe.throw("Đơn chưa có món nào.")
	if flt(phi_ship) > 0:
		rows.append({"item_code": _item_phi_giao(), "qty": 1, "rate": flt(phi_ship)})
	nguon = (nguon or "Khác").strip()
	ma_don = (ma_don or "").strip()
	pid = "%s-%s" % (nguon.upper().replace(" ", ""), ma_don or frappe.generate_hash(length=8))
	if frappe.db.exists("Sales Invoice", {"custom_pancake_id": pid}):
		frappe.throw("Mã đơn %s của %s đã nhập rồi, không nhập trùng." % (ma_don, nguon))
	si = frappe.new_doc("Sales Invoice")
	si.update(
		{
			"company": _cong_ty(),
			"customer": _khach_le(),
			"posting_date": str(ngay),
			"set_posting_time": 1,
			"due_date": str(ngay),
			"update_stock": 0,
			"custom_pancake_id": pid,
			"custom_pancake_display_id": ma_don,
			"custom_nguon": nguon,
			"apply_discount_on": "Grand Total",
			"discount_amount": flt(giam_gia),
			"remarks": "%s #%s - %s%s"
			% (nguon, ma_don or "?", (ten_khach or "Khách lẻ").strip(), " - " + dien_thoai.strip() if (dien_thoai or "").strip() else ""),
		}
	)
	for r in rows:
		si.append("items", r)
	si.flags.ignore_permissions = True
	si.save()
	frappe.db.commit()
	return {"name": si.name, "grand_total": si.grand_total}


# ---------------------------------------------------------------- m-invoice

def _minvoice_login(c):
	host = (c.minvoice_host or "").strip().rstrip("/")
	if not host:
		frappe.throw("Chưa điền host m-invoice trong Vagabond Settings.")
	if not host.startswith("http"):
		host = "https://" + host
	mk = key(c, "minvoice_password")
	r = requests.post(
		host + "/api/Account/Login",
		json={
			"username": (c.minvoice_username or "").strip(),
			"password": mk,
			"ma_dvcs": (c.minvoice_ma_dvcs or "VP").strip(),
		},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	j = r.json() or {}
	if not j.get("ok"):
		frappe.throw("m-invoice từ chối đăng nhập: %s" % j.get("message"))
	return host, j.get("token")


def _tach_thue(gross, ts):
	"""Gia Pancake da gom VAT. Tach nguoc: (chua_thue, tien_thue)."""
	chua = round(gross / (1 + ts / 100.0))
	return chua, round(gross - chua)


@frappe.whitelist()
def xuat_hoa_don_dien_tu(si_name):
	"""Day mot SI sang m-invoice o trang thai CHO KY. Khong ky tu dong."""
	_kiem_quyen()
	si = frappe.get_doc("Sales Invoice", si_name)
	if si.docstatus != 1:
		frappe.throw("Hoá đơn %s chưa chốt, chốt doanh số trước rồi mới xuất HĐĐT." % si_name)
	if si.custom_hddt_so:
		frappe.throw("Hoá đơn %s đã xuất HĐĐT số %s rồi." % (si_name, si.custom_hddt_so))

	hd = frappe.db.get_value(
		"Vagabond Hoa Don",
		{"ma_don": si.custom_pancake_display_id},
		["ma_so_thue", "ten_cong_ty", "dia_chi", "email"],
		as_dict=True,
	)
	c = cfg()
	ts = flt(c.minvoice_ma_thue or 8)
	host, token = _minvoice_login(c)

	dong, t_chua, t_thue = [], 0, 0
	for i, r in enumerate(si.items, 1):
		gross = flt(r.amount)
		chua, thue = _tach_thue(gross, ts)
		t_chua += chua
		t_thue += thue
		dong.append(
			{
				"tchat": 1,
				"stt_rec0": i,
				"inv_itemCode": r.item_code,
				"inv_itemName": r.item_name,
				"inv_unitCode": r.uom or "Cái",
				"inv_quantity": flt(r.qty),
				"inv_unitPrice": round(chua / flt(r.qty)) if r.qty else chua,
				"inv_discountPercentage": 0,
				"inv_discountAmount": 0,
				"inv_TotalAmountWithoutVat": chua,
				"ma_thue": ts,
				"inv_vatAmount": thue,
				"inv_TotalAmount": chua + thue,
			}
		)

	than = {
		"editmode": 1,
		"data": [
			{
				"inv_invoiceSeries": (c.minvoice_series or "").strip(),
				"inv_invoiceIssuedDate": str(si.posting_date),
				"inv_currencyCode": "VND",
				"inv_exchangeRate": 1,
				"inv_buyerDisplayName": (si.remarks or "").split(" - ")[1] if " - " in (si.remarks or "") else "",
				"inv_buyerLegalName": (hd and hd.ten_cong_ty) or "",
				"inv_buyerTaxCode": (hd and hd.ma_so_thue) or "",
				"inv_buyerAddressLine": (hd and hd.dia_chi) or "",
				"inv_buyerEmail": (hd and hd.email) or "",
				"inv_paymentMethodName": "TM/CK",
				"inv_discountAmount": 0,
				"inv_TotalAmountWithoutVat": t_chua,
				"inv_vatAmount": t_thue,
				"inv_TotalAmount": t_chua + t_thue,
				"key_api": si.custom_pancake_display_id or si.name,
				"details": [{"data": dong}],
			}
		],
	}
	r = requests.post(
		host + "/api/InvoiceApi78/Save",
		json=than,
		headers={"Authorization": "Bear " + token},
		timeout=30,
	)
	r.raise_for_status()
	j = r.json() or {}
	if not j.get("ok"):
		frappe.throw("m-invoice báo lỗi: %s" % json.dumps(j.get("message"), ensure_ascii=False))
	d = j.get("data") or {}
	frappe.db.set_value(
		"Sales Invoice",
		si.name,
		{
			"custom_hddt_trang_thai": d.get("tthai") or "Chờ ký",
			"custom_hddt_so": str(d.get("inv_invoiceNumber") or ""),
			"custom_hddt_id": d.get("inv_invoiceAuth_id") or "",
			"custom_hddt_sobaomat": d.get("sobaomat") or "",
		},
	)
	if hd:
		frappe.db.set_value(
			"Vagabond Hoa Don", {"ma_don": si.custom_pancake_display_id}, "tinh_trang", "Đã xuất"
		)
	frappe.db.commit()
	return d
