"""Ahamove: hoi phi giao.

Khoa Ahamove nam o day. Token la JWT co han nen duoc nho lai,
dung xin moi lan khach go dia chi.
"""

import json

import frappe
import requests
from frappe.rate_limiter import rate_limit

from vagabond.dia_chi import geocode
from vagabond.lib import TIMEOUT, cache_get, cache_set, cfg, key


def _token(c):
	ck = "vgb:aha:token"
	hit = cache_get(ck)
	if hit:
		return hit
	r = requests.post(
		(c.ahamove_base or "").rstrip("/") + "/v3/accounts/token",
		json={"mobile": c.ahamove_mobile, "api_key": key(c, "ahamove_api_key")},
		timeout=TIMEOUT,
	)
	r.raise_for_status()
	tok = (r.json() or {}).get("token")
	if not tok:
		frappe.throw("Ahamove khong tra ve token")
	cache_set(ck, tok, 3000)
	return tok


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=40, seconds=60)
def phi_giao(addr=None, lat=None, lng=None):
	"""Phi giao tham khao = phi Ahamove + phu thu cua tiem.

	Truyen san lat/lng thi khong ton mot luot goi Goong.
	Khong lay duoc thi tra ve ok=0 kem ly do.
	TUYET DOI khong doan mot con so: con so sai lam mat uy tin hon la khong co so.
	"""
	c = cfg()
	if not key(c, "ahamove_api_key") or not c.ahamove_base or not c.ahamove_mobile:
		return {"ok": 0, "ly_do": "chua_dien_khoa_ahamove"}

	if lat and lng:
		diem = {"lat": float(lat), "lng": float(lng), "dia_chi": addr or ""}
	elif addr:
		diem = geocode(c, addr.strip())
		if not diem:
			return {"ok": 0, "ly_do": "khong_tim_thay_dia_chi"}
	else:
		frappe.throw("Thieu dia chi")

	ck = "vgb:fee:%s,%s" % (round(diem["lat"], 5), round(diem["lng"], 5))
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)

	reqs = []
	if c.dung_dich_vu_de_vo:
		reqs.append({"_id": c.ma_dich_vu + "-FRAGILE"})

	diem_bep = {
		"lat": c.kitchen_lat,
		"lng": c.kitchen_lng,
		"address": c.kitchen_address,
		"name": "Bep Vagabond",
		"mobile": c.ahamove_mobile,
	}
	diem_khach = {
		"lat": diem["lat"],
		"lng": diem["lng"],
		"address": diem.get("dia_chi") or "",
		"name": "Khach",
		"mobile": c.ahamove_mobile,
	}
	body = {
		"order_time": 0,
		"path": [diem_bep, diem_khach],
		"services": [{"_id": c.ma_dich_vu, "requests": reqs}],
		"payment_method": "BALANCE",
	}
	try:
		r = requests.post(
			(c.ahamove_base or "").rstrip("/") + "/v3/orders/estimates",
			json=body,
			headers={"Authorization": "Bearer " + _token(c)},
			timeout=TIMEOUT,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Ahamove khong goi duoc")
		return {"ok": 0, "ly_do": "ahamove_loi"}

	if r.status_code != 200:
		frappe.log_error(r.text[:500], "Vagabond: Ahamove tu choi")
		return {"ok": 0, "ly_do": "ahamove_loi"}

	arr = r.json() or []
	data = (arr[0] or {}).get("data") if arr else None
	if not data or not data.get("total_fee"):
		return {"ok": 0, "ly_do": "ahamove_khong_bao_gia"}

	goc = int(data["total_fee"])
	phu = int(c.phu_thu or 0)
	out = {
		"ok": 1,
		"phi_goc": goc,
		"phu_thu": phu,
		"total_fee": goc + phu,
		"distance": data.get("distance"),
		"dia_chi": diem.get("dia_chi"),
	}
	cache_set(ck, json.dumps(out), 600)
	return out
