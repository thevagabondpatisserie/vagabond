"""Tra khach cu (Pancake) va tra ma so thue (VietQR).

Phi giao o vagabond/giao_hang.py, goi y dia chi o vagabond/dia_chi.py.
"""

import json
import re

import frappe
import requests
from frappe.rate_limiter import rate_limit

from vagabond.lib import PANCAKE, TIMEOUT, VIETQR, cache_get, cache_set, cfg, key


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=20, seconds=60)
def tra_khach(phone=None):
	"""Dia chi cu cua khach theo so dien thoai.

	api_key cua shop tuyet doi khong duoc lo ra trinh duyet, nen phai di qua day.
	Tra ve kem ban da che so nha, portal chi hien ban che cho toi khi khach bam chon.
	"""
	phone = "".join(ch for ch in (phone or "") if ch.isdigit())
	if len(phone) < 9:
		return {"addresses": []}

	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		return {"addresses": [], "ly_do": "chua_dien_khoa_pancake"}

	try:
		r = requests.get(
			"%s/shops/%s/customers" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": phone},
			timeout=TIMEOUT,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Pancake khong goi duoc")
		return {"addresses": [], "ly_do": "pancake_loi"}

	if r.status_code != 200:
		return {"addresses": [], "ly_do": "pancake_tu_choi"}

	# Pancake tim kiem long tay: go so nay co the ra ca khach khac.
	# Chi giu dia chi nao co dung so dien thoai vua go, khong thi tiem lo
	# ten va dia chi cua khach khac cho nguoi la.
	duoi = phone[-9:]
	out = []
	for kh in (r.json() or {}).get("data") or []:
		for a in kh.get("shop_customer_addresses") or []:
			so = "".join(ch for ch in (a.get("phone_number") or "") if ch.isdigit())
			if so[-9:] != duoi:
				continue
			full = a.get("full_address") or ""
			out.append(
				{
					"ho_ten": kh.get("name") or "",
					"dia_chi_che": re.sub(r"^\s*[0-9]+([/\-][0-9A-Za-z]+)*", "***", full),
					"dia_chi": full,
					"phone": a.get("phone_number") or phone,
				}
			)
	return {"addresses": out[:5]}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=60)
def tra_mst(mst=None):
	"""Ten va dia chi cong ty theo ma so thue. VietQR mo cong khai, khong can khoa."""
	# MST chi nhanh 13 so phai giu DAU GACH NGANG (10 so - 3 so) theo Thong
	# tu 86/2024/TT-BTC. VietQR tra code 52 "Ma so thue khong chinh xac" neu
	# gui 13 so lien khong gach - da thu that 12/08/2026 voi 0311638525-027.
	so = "".join(ch for ch in (mst or "") if ch.isdigit())
	if len(so) == 10:
		mst = so
	elif len(so) == 13:
		mst = so[:10] + "-" + so[10:]
	else:
		return {"ok": 0, "ly_do": "ma_so_thue_phai_10_hoac_13_so"}

	ck = "vgb:mst:" + mst
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)

	try:
		r = requests.get("%s/%s" % (VIETQR, mst), timeout=TIMEOUT)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: VietQR khong goi duoc")
		return {"ok": 0, "ly_do": "khong_goi_duoc_cong_thong_tin"}

	j = r.json() if r.status_code == 200 else {}
	if j.get("code") != "00" or not j.get("data"):
		return {"ok": 0, "ly_do": "khong_tim_thay"}

	d = j["data"]
	out = {
		"ok": 1,
		"ma_so_thue": mst,
		"ten": d.get("name"),
		"ten_ngan": d.get("shortName"),
		"dia_chi": d.get("address"),
	}
	cache_set(ck, json.dumps(out), 604800)
	return out
