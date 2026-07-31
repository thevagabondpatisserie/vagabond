"""Goong: goi y dia chi va doi dia chi thanh toa do.

Khoa Goong nam o day, khong bao gio ra trinh duyet.
Ket qua duoc nho lai de khach go di go lai khong ban ra chuc luot goi.
"""

import json

import frappe
import requests
from frappe.rate_limiter import rate_limit

from vagabond.lib import GOONG, TIMEOUT, cache_get, cache_set, cfg, key


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=60)
def goi_y_dia_chi(q=None):
	"""Goi y dia chi khi khach go.

	BAT BUOC truyen toa do bep lam diem tham chieu. Khong truyen thi Goong
	tra ve dia chi cung ten o Ba Ria, Binh Dinh, Thanh Hoa - khach bam bua
	la don ra sai tinh.
	"""
	q = (q or "").strip()
	if len(q) < 3:
		return {"suggestions": []}

	ck = "vgb:ac:" + q.lower()
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)

	c = cfg()
	k = key(c, "goong_api_key")
	if not k:
		return {"suggestions": [], "ly_do": "chua_dien_khoa_goong"}

	try:
		r = requests.get(
			GOONG + "/Place/AutoComplete",
			params={
				"input": q,
				"location": "%s,%s" % (c.kitchen_lat, c.kitchen_lng),
				"radius": c.suggest_radius_km or 30,
				"api_key": k,
			},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Goong AutoComplete loi")
		return {"suggestions": [], "ly_do": "goong_loi"}

	preds = (r.json() or {}).get("predictions") or []
	out = {
		"suggestions": [
			{"mo_ta": p.get("description"), "place_id": p.get("place_id")} for p in preds[:6]
		]
	}
	cache_set(ck, json.dumps(out), 3600)
	return out


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=60)
def chi_tiet_dia_chi(place_id=None):
	"""Doi place_id thanh toa do."""
	if not place_id:
		frappe.throw("Thieu place_id")

	ck = "vgb:pd:" + place_id[:60]
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)

	c = cfg()
	k = key(c, "goong_api_key")
	if not k:
		return {"dia_chi": None, "lat": None, "lng": None, "ly_do": "chua_dien_khoa_goong"}

	try:
		r = requests.get(
			GOONG + "/Place/Detail",
			params={"place_id": place_id, "api_key": k},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Goong Place Detail loi")
		return {"dia_chi": None, "lat": None, "lng": None, "ly_do": "goong_loi"}

	res = (r.json() or {}).get("result") or {}
	loc = (res.get("geometry") or {}).get("location") or {}
	out = {"dia_chi": res.get("formatted_address"), "lat": loc.get("lat"), "lng": loc.get("lng")}
	cache_set(ck, json.dumps(out), 86400)
	return out


def geocode(c, addr):
	"""Doi dia chi chu thanh toa do. Khong tim thay thi tra None."""
	ck = "vgb:gc:" + addr.lower()[:80]
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)

	k = key(c, "goong_api_key")
	if not k:
		return None

	try:
		r = requests.get(
			GOONG + "/geocode",
			params={"address": addr, "api_key": k},
			timeout=TIMEOUT,
		)
		r.raise_for_status()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Goong geocode loi")
		return None

	res = (r.json() or {}).get("results") or []
	if not res:
		return None
	loc = (res[0].get("geometry") or {}).get("location") or {}
	out = {"dia_chi": res[0].get("formatted_address"), "lat": loc.get("lat"), "lng": loc.get("lng")}
	cache_set(ck, json.dumps(out), 86400)
	return out
