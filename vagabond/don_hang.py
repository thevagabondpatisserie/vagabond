"""Tao don that ben Pancake tu trang dat banh.

Cho khach vang lai goi, nen KHONG duoc tin bat ky con so nao trinh duyet
gui len. Phi giao tinh lai o may chu; so luong, so dien thoai, ma hang
deu duoc lam sach truoc khi gui di.
"""

import json

import frappe
import requests
from frappe.rate_limiter import rate_limit

from vagabond.giao_hang import phi_giao
from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

MAX_DONG = 30
MAX_SL = 20


def _so(s):
	return "".join(ch for ch in str(s or "") if ch.isdigit())


def _lam_sach_hang(items):
	"""Bo dong rac, gop dong trung ma, chan so luong vo ly."""
	gom = {}
	for it in (items or [])[:MAX_DONG]:
		ma = str((it or {}).get("variation_id") or "").strip()
		try:
			sl = int((it or {}).get("quantity") or 0)
		except (TypeError, ValueError):
			continue
		if not ma or sl < 1:
			continue
		gom[ma] = min(gom.get(ma, 0) + sl, MAX_SL)
	return [{"variation_id": ma, "quantity": sl} for ma, sl in gom.items()]


def _luu_hoa_don(ma_don, hd):
	"""Pancake khong co cho ghi thong tin hoa don, nen giu ben minh.

	Truoc day sales ghi tay vao ghi chu roi cuoi ngay go lai sang Fabi,
	de sai chinh ta ten cong ty va mat so.
	"""
	try:
		doc = frappe.new_doc("Vagabond Hoa Don")
		doc.ma_don = ma_don
		doc.ma_so_thue = _so(hd.get("tax_code"))
		doc.ten_cong_ty = (hd.get("name") or "").strip()
		doc.dia_chi = (hd.get("address") or "").strip()
		doc.email = (hd.get("email") or "").strip()
		doc.tinh_trang = "Chua xuat"
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		# Don da tao roi thi khong duoc lam hong ca don chi vi cho nay.
		frappe.log_error(frappe.get_traceback(), "Vagabond: khong luu duoc hoa don")


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=10, seconds=60)
def tao_don(don=None):
	"""Nhan don tu trang dat banh, tao don that ben Pancake."""
	if isinstance(don, str):
		try:
			don = json.loads(don)
		except ValueError:
			return {"ok": 0, "ly_do": "du_lieu_khong_doc_duoc"}
	if not isinstance(don, dict):
		return {"ok": 0, "ly_do": "thieu_du_lieu"}

	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		return {"ok": 0, "ly_do": "chua_dien_khoa_pancake"}

	hang = _lam_sach_hang(don.get("items"))
	if not hang:
		return {"ok": 0, "ly_do": "gio_hang_rong"}

	ten = (don.get("ho_ten") or "").strip()
	dien_thoai = _so(don.get("dien_thoai"))
	if not ten or len(dien_thoai) < 9:
		return {"ok": 0, "ly_do": "thieu_ten_hoac_so_dien_thoai"}

	tu_lay = bool(don.get("tu_lay"))
	dia_chi = (don.get("dia_chi") or "").strip()
	if not tu_lay and len(dia_chi) < 8:
		return {"ok": 0, "ly_do": "thieu_dia_chi_giao"}

	# Phi giao TINH LAI o day. Con so tu trinh duyet gui len chi de hien
	# cho khach xem, khong duoc dung lam so tien that.
	phi = 0
	bao_phi = None
	if not tu_lay:
		bao_phi = phi_giao(addr=dia_chi, lat=don.get("lat"), lng=don.get("lng"))
		if bao_phi.get("ok"):
			phi = int(bao_phi.get("total_fee") or 0)

	nguoi_nhan = (don.get("nguoi_nhan") or {}) if isinstance(don.get("nguoi_nhan"), dict) else {}
	body = {
		"bill_full_name": ten,
		"bill_phone_number": dien_thoai,
		"bill_email": (don.get("email") or "").strip(),
		"shipping_address": {
			"full_name": (nguoi_nhan.get("ho_ten") or ten).strip(),
			"phone_number": _so(nguoi_nhan.get("dien_thoai")) or dien_thoai,
			"full_address": dia_chi,
		},
		"items": hang,
		"note_print": (don.get("note_print") or "").strip(),
		"note": (don.get("note") or "").strip(),
		"partner_fee": phi,
		"status": 0,
		"order_sources_name": "Website",
	}
	if don.get("ngay_nhan"):
		body["estimate_delivery_date"] = don["ngay_nhan"]
	if isinstance(don.get("tags"), list) and don["tags"]:
		body["tags"] = don["tags"][:5]

	try:
		r = requests.post(
			"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k},
			json=body,
			timeout=TIMEOUT,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Pancake khong tao duoc don")
		return {"ok": 0, "ly_do": "pancake_loi"}

	if r.status_code not in (200, 201):
		frappe.log_error(r.text[:1000], "Vagabond: Pancake tu choi don")
		return {"ok": 0, "ly_do": "pancake_tu_choi"}

	try:
		j = r.json() or {}
	except ValueError:
		frappe.log_error(r.text[:1000], "Vagabond: Pancake tra ve khong phai JSON")
		return {"ok": 0, "ly_do": "pancake_tra_ve_la"}

	# Pancake tung doi ten truong ma don giua cac ban, nen do lan luot.
	data = j.get("data") if isinstance(j.get("data"), dict) else j
	ma_don = data.get("id") or data.get("order_id") or data.get("system_id")
	if not ma_don:
		frappe.log_error(json.dumps(j)[:1000], "Vagabond: Pancake khong tra ve ma don")
		return {"ok": 0, "ly_do": "khong_ro_ma_don"}

	hd = don.get("hoa_don")
	if isinstance(hd, dict) and _so(hd.get("tax_code")):
		_luu_hoa_don(str(ma_don), hd)

	return {
		"ok": 1,
		"ma_don": str(ma_don),
		"phi_giao": phi,
		"ly_do_phi": None if phi else (bao_phi or {}).get("ly_do"),
	}
