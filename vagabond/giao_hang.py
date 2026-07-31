"""Ahamove: hoi phi giao, va chan don ngoai vung giao.

Khoa Ahamove nam o day. Token la JWT co han nen duoc nho lai,
dung xin moi lan khach go dia chi.

Hai dieu quan trong da hoc duoc bang cach do that:

1. Phi Ahamove DOI THEO GIO. Cung mot dia chi 11,48 km, hoi luc 15h ra
   76.000, hoi luc 17h20 ra 123.000 - chenh 62%. Nen phai truyen order_time
   la luc khach muon nhan banh, khong duoc de 0 (giao ngay).

2. Banh kem chi giao trong ban kinh gioi han, tinh theo duong chim bay tu
   BEP hoac tu CUA HANG - cho nao gan khach hon thi lay banh o do.
   Xa hon thi tra loi thang la khong giao toi, moi khach tu den lay.
"""

import json
import math
import time
from datetime import datetime, timedelta

import frappe
import requests
from frappe.rate_limiter import rate_limit

from vagabond.dia_chi import geocode
from vagabond.lib import TIMEOUT, cache_get, cache_set, cfg, key

BAN_KINH_MAC_DINH = 12.0

# Ahamove chi bao gia dat truoc trong vong 7 ngay. Do that ngay 31/07:
# +7 ngay van bao gia, +8 ngay tra loi tu choi. Trang dat banh cho chon
# 14 ngay, nen phai co duong lui cho nhung ngay xa hon.
GIOI_HAN_DAT_TRUOC = 7 * 86400


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


def _chim_bay(lat1, lng1, lat2, lng2):
	"""Khoang cach duong chim bay, km. Dung de chan don xa truoc khi goi Ahamove."""
	R = 6371.0
	p1, p2 = math.radians(lat1), math.radians(lat2)
	dp = math.radians(lat2 - lat1)
	dl = math.radians(lng2 - lng1)
	a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
	return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _cac_diem_lay(c):
	"""Danh sach diem co the lay banh. Bep luon co, cua hang co neu da dien toa do."""
	ds = []
	if c.kitchen_lat and c.kitchen_lng:
		ds.append({
			"ten": "Bep Vagabond",
			"lat": float(c.kitchen_lat), "lng": float(c.kitchen_lng),
			"dia_chi": c.kitchen_address or "",
		})
	if c.store_lat and c.store_lng:
		ds.append({
			"ten": "Cua hang Sai Gon",
			"lat": float(c.store_lat), "lng": float(c.store_lng),
			"dia_chi": c.store_address or "",
		})
	return ds


def _luc_giao_unix(v):
	"""Doi moc gio khach chon thanh unix giay, theo gio Viet Nam.

	Khong doc duoc, hoac da qua roi, thi tra 0 - Ahamove hieu la giao ngay.
	"""
	if not v:
		return 0
	try:
		s = str(v).strip().replace("Z", "")
		dt = datetime.fromisoformat(s)
	except ValueError:
		return 0
	if dt.tzinfo is None:
		try:
			from zoneinfo import ZoneInfo

			dt = dt.replace(tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
		except Exception:
			return 0
	ts = int(dt.timestamp())
	return ts if ts > int(datetime.now(dt.tzinfo).timestamp()) else 0


def _lui_ve_trong_han(moc):
	"""Keo moc gio qua xa ve ngay xa nhat Ahamove con nhan, GIU NGUYEN GIO.

	Gia doi theo gio trong ngay, nen phai giu dung gio khach chon. Ngay thi
	lui lai - dat truoc 7 ngay hay 14 ngay thi Ahamove van tinh mot gia.
	"""
	han = int(time.time()) + GIOI_HAN_DAT_TRUOC
	if moc <= han:
		return None
	xin = datetime.fromtimestamp(moc)
	cuoi = datetime.fromtimestamp(han)
	lui = xin.replace(year=cuoi.year, month=cuoi.month, day=cuoi.day)
	if lui.timestamp() > han:
		lui -= timedelta(days=1)
	return int(lui.timestamp())


def _hoi_ahamove(c, diem_lay, diem_khach, luc_giao):
	"""Goi Ahamove mot lan. Tra ve (data, loi)."""
	reqs = []
	if c.dung_dich_vu_de_vo:
		reqs.append({"_id": c.ma_dich_vu + "-FRAGILE"})

	body = {
		"order_time": luc_giao,
		"path": [
			{
				"lat": diem_lay["lat"], "lng": diem_lay["lng"],
				"address": diem_lay["dia_chi"], "name": diem_lay["ten"],
				"mobile": c.ahamove_mobile,
			},
			{
				"lat": diem_khach["lat"], "lng": diem_khach["lng"],
				"address": diem_khach.get("dia_chi") or "", "name": "Khach",
				"mobile": c.ahamove_mobile,
			},
		],
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
		return None, "ahamove_loi"

	if r.status_code != 200:
		frappe.log_error(r.text[:500], "Vagabond: Ahamove tu choi")
		return None, "ahamove_loi"

	arr = r.json() or []
	data = (arr[0] or {}).get("data") if arr else None
	if not data or not data.get("total_fee"):
		return None, "ahamove_khong_bao_gia"
	return data, None


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=40, seconds=60)
def phi_giao(addr=None, lat=None, lng=None, luc_giao=None):
	"""Phi giao cho mot dia chi, tai dung khung gio khach chon.

	Truyen san lat/lng thi khong ton mot luot goi Goong.
	`luc_giao` la moc gio khach muon nhan banh, dang ISO. Co no thi phi sat
	thuc te hon nhieu, vi Ahamove tinh gia theo gio.

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

	# CHAN DON XA TRUOC KHI GOI AHAMOVE.
	# Do duong chim bay, dung nghia "ban kinh" tren ban do, va khoi ton mot
	# luot goi cho dia chi chac chan khong giao duoc.
	diem_lay_ds = _cac_diem_lay(c)
	if not diem_lay_ds:
		return {"ok": 0, "ly_do": "chua_dien_toa_do_diem_lay"}

	ban_kinh = float(c.ban_kinh_giao_km or BAN_KINH_MAC_DINH)
	for d in diem_lay_ds:
		d["_km"] = _chim_bay(d["lat"], d["lng"], diem["lat"], diem["lng"])
	diem_lay_ds.sort(key=lambda d: d["_km"])
	gan_nhat = diem_lay_ds[0]

	if gan_nhat["_km"] > ban_kinh:
		return {
			"ok": 0,
			"ly_do": "ngoai_vung_giao",
			"khoang_cach": round(gan_nhat["_km"], 1),
			"ban_kinh": ban_kinh,
			"dia_chi": diem.get("dia_chi"),
		}

	moc = _luc_giao_unix(luc_giao)
	ck = "vgb:fee:%s,%s,%s,%s" % (
		round(diem["lat"], 5), round(diem["lng"], 5), moc // 1800, gan_nhat["ten"]
	)
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)

	data, loi = _hoi_ahamove(c, gan_nhat, diem, moc)
	theo_gio = bool(moc)
	if loi and moc:
		# Duong lui thu nhat: dat qua xa ngay. Hoi lai o ngay xa nhat con
		# nhan duoc nhung dung gio khach chon - ra gia dat truoc, sat hon
		# nhieu so voi gia giao ngay bay gio (co the dang gio cao diem).
		gan = _lui_ve_trong_han(moc)
		if gan:
			data, loi = _hoi_ahamove(c, gan_nhat, diem, gan)
		theo_gio = False
	if loi and moc:
		# Duong lui cuoi: gia giao ngay. Co so con hon khong co so nao,
		# nhung phai noi ro la khong phai gia theo gio khach chon.
		data, loi = _hoi_ahamove(c, gan_nhat, diem, 0)
		theo_gio = False
	if loi:
		return {"ok": 0, "ly_do": loi}

	goc = int(data["total_fee"])
	phu = int(c.phu_thu or 0)
	out = {
		"ok": 1,
		"phi_goc": goc,
		"phu_thu": phu,
		"total_fee": goc + phu,
		"distance": data.get("distance"),
		"dia_chi": diem.get("dia_chi"),
		"diem_lay": gan_nhat["ten"],
		"theo_gio": theo_gio,
	}
	cache_set(ck, json.dumps(out), 600)
	return out
