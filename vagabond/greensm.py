"""GreenSM Express: báo phí giao, gọi xe, thử kết nối.

Thân yêu cầu theo tài liệu công khai của GreenSM (đọc 26/10/2026):
https://developer.greensm.com/vn/docs/express/estimates
https://developer.greensm.com/vn/docs/express/book-a-delivery
https://developer.greensm.com/vn/docs/express/get-available-services

Hôm 21/10 sandbox trả 400 "missing required fields" vì khi đó chưa có tài
liệu và mình gửi `pickup`/`dropoff` số ít. Đúng là `pickups`/`dropoffs` (mảng)
cho danh sách dịch vụ, và `service_ids` + `points` cho báo giá.

Ba điều phải nhớ:
1. `order_time` gửi lúc báo giá phải gửi Y HỆT lúc tạo đơn, và `fee_id` có
   hạn. Nên giá báo cho nhân viên được giữ lại phía máy chủ (theo vận đơn)
   rồi tạo đơn từ chính bản đó, không nhận lại số tiền từ trình duyệt.
2. Sandbox là dữ liệu giả: mọi địa chỉ ra cùng một giá. Không bao giờ được
   đưa giá sandbox cho khách trên web, và không được gọi xe sandbox cho một
   vận đơn thật (vận đơn sẽ báo "Đang giao" mà không có tài xế nào).
3. Mã dịch vụ cố định theo từng đối tác, sandbox và thật khác nhau, nên đọc
   từ /list-available-services rồi nhớ một ngày, không viết cứng.

Phần THUẦN (dựng thân, đọc phản hồi, chọn dịch vụ) không chạm Frappe để kiểm
được không cần site; phần gọi mạng nằm cuối tệp.
"""

import json
import re

import frappe

BASE_THU = "https://api-sandbox.vn.gsm-api.net/v1/sandbox/express"
BASE_THAT = "https://api-partner.vn.gsm-api.net/v1/express"
TOKEN_THU = "https://api-sandbox.vn.gsm-api.net/v1/sandbox/token"
TOKEN_THAT = "https://api-partner.vn.gsm-api.net/v1/public/token"

# Bánh của tiệm: một hộp bánh kem dưới 5 kg, hộp 25x20x20 cm vừa cỡ SMALL của
# xe máy (SMALL 1-5 kg, MEDIUM 6-15 kg, LARGE 16-30 kg theo tài liệu).
KHOI_LUONG_KG = 2
CO_HOP = "SMALL"
LOAI_HANG = ["food"]

# partner_pay: tài xế không thu cước của người gửi hay người nhận, GreenSM
# đối soát với tiệm cuối kỳ (giống tài khoản trả sau của Ahamove).
THANH_TOAN = "partner_pay"

# Mã add-on thu hộ (COD) theo bảng "Mapping Addon Service": 4 là tài xế ứng
# tiền cho người gửi rồi thu lại của người nhận. Thu hộ do máy tự gắn theo
# tiền thu hộ của vận đơn, nên không hiện cho nhân viên tick.
ADDON_COD = 4
CHU_ADDON_AN = ("cod", "thu hộ", "thu ho")


def so_quoc_te(sdt):
	"""Số điện thoại về dạng +84xxxxxxxxx mà GreenSM đòi. Không đọc được thì ''."""
	so = re.sub(r"[^\d+]", "", str(sdt or ""))
	if so.startswith("+"):
		return so if len(so) >= 10 else ""
	if so.startswith("84") and len(so) >= 11:
		return "+" + so
	if so.startswith("0") and len(so) >= 10:
		return "+84" + so[1:]
	return ""


def diem(loai, lat, lng, ten, sdt, dia_chi, ngan="", ghi_chu="", hang=False):
	"""Một điểm trên lộ trình. `hang=True` cho điểm lấy: kèm cân nặng, cỡ hộp."""
	d = {
		"type": loai,
		"latitude": float(lat),
		"longitude": float(lng),
		"name": (ten or "The Vagabond")[:256],
		"phone_number": so_quoc_te(sdt),
		"short_address": (ngan or dia_chi or "")[:512],
		"address": (dia_chi or "")[:512],
	}
	if ghi_chu:
		d["address_note"] = str(ghi_chu)[:512]
	if hang:
		d["package_weight"] = KHOI_LUONG_KG
		d["package_size"] = CO_HOP
		d["package_types"] = list(LOAI_HANG)
	return d


def than_bao_gia(service_id, order_time, diem_lay, diem_giao, addon_ids=(), cod=0):
	"""Thân /estimate/order. Add-on nằm TRONG service_ids, mỗi cái có apply."""
	addons = [{"id": int(a), "apply": True} for a in addon_ids or () if int(a) != ADDON_COD]
	cod = int(round(float(cod or 0)))
	giao = dict(diem_giao)
	if cod > 0:
		addons.append({"id": ADDON_COD, "remain_cod": cod, "value": 1, "apply": True})
		# Ở điểm giao là MỘT object, không phải mảng (tài liệu nhấn mạnh).
		giao["addons"] = {"collect_cod": cod, "currency_code": "VND"}
	dv = {"id": int(service_id)}
	if addons:
		dv["addons"] = addons
	return {
		"service_ids": [dv],
		"order_time": int(order_time or 0),
		"payment_method": THANH_TOAN,
		"points": [dict(diem_lay), giao],
	}


def doc_bao_gia(phan_hoi, service_id=None):
	"""Đọc phản hồi báo giá. Trả dict gọn, có `loi` khi dịch vụ không báo giá."""
	ds = ((phan_hoi or {}).get("data") or {}).get("service_estimates") or []
	chon = None
	for s in ds:
		if service_id is None or str((s.get("service") or {}).get("id")) == str(service_id):
			chon = s
			break
	if chon is None:
		return {"loi": "GreenSM không trả giá cho loại xe này."}
	if chon.get("fee_unavailable"):
		return {"loi": chon.get("err_msg") or "GreenSM chưa báo giá được cho tuyến này."}
	info = chon.get("estimate_info") or {}
	est = info.get("estimate") or {}
	bd = est.get("fee_breakdown") or {}
	trip = info.get("trip") or {}
	sv = chon.get("service") or {}
	tong = int(est.get("total_fee") or est.get("total_pay") or 0)
	if not tong or not info.get("fee_id"):
		return {"loi": "GreenSM không trả số tiền cho tuyến này."}
	return {
		"tong": tong,
		"fee_id": info.get("fee_id"),
		"het_han": int(info.get("expires_at") or 0),
		"service_id": sv.get("id"),
		"service_type": sv.get("service_type") or "EXPRESS-ONDEMAND",
		"ten_xe": sv.get("display_name") or "",
		"km": float(trip.get("distance_estimate") or 0),
		"phut": int(float(trip.get("duration_estimate") or 0) // 60),
		"phi_them": int(bd.get("addons_fee") or 0),
		"giam": int(bd.get("discount") or 0),
		"tang_gia": bool(info.get("increase_price")),
	}


def than_tao_don(bg, than_gia, ma_noi_bo, gia_tri_hang=0):
	"""Thân /create-order từ CHÍNH bản báo giá đã giữ.

	`than_gia` là thân đã gửi lúc báo giá: lấy lại order_time, điểm và bộ
	add-on y hệt, vì lệch một thứ là GreenSM từ chối fee_id. Add-on ở đây chỉ
	là mảng mã số ở cấp ngoài cùng (`addon_ids`)."""
	dv = (than_gia.get("service_ids") or [{}])[0]
	ma_addon = [int(a["id"]) for a in dv.get("addons") or []]
	diem_ds = [dict(p) for p in than_gia.get("points") or []]
	for p in diem_ds:
		# Tiệm trả cước (partner_pay), đánh dấu ở điểm lấy cho rõ.
		p["is_payment_check_point"] = p.get("type") == "PICK UP"
	d = {
		"order_time": int(than_gia.get("order_time") or 0),
		"service_id": int(bg["service_id"]),
		"service_type": bg.get("service_type") or "EXPRESS-ONDEMAND",
		"fee_id": bg["fee_id"],
		"payment_method": than_gia.get("payment_method") or THANH_TOAN,
		"points": diem_ds,
		"partner_trip_id": str(ma_noi_bo or "")[:32],
	}
	if ma_addon:
		d["addon_ids"] = ma_addon
	gt = int(round(float(gia_tri_hang or 0)))
	if gt > 0:
		d["goods_value"] = gt
	return d


def dich_vu_gon(phan_hoi):
	"""Danh sách loại xe cho màn gọi xe: xe máy trước, add-on thu hộ ẩn đi."""
	ra = []
	for x in (phan_hoi or {}).get("data") or []:
		sv = x.get("service") or {}
		if not sv.get("id") or sv.get("enable") is False:
			continue
		addon = []
		for a in x.get("addons") or []:
			ten = str(a.get("name") or a.get("display_name") or "").strip()
			if not a.get("id") or any(t in ten.lower() for t in CHU_ADDON_AN):
				continue
			addon.append({"id": int(a["id"]), "ten": ten})
		ra.append({
			"id": int(sv["id"]),
			"ten": sv.get("display_name") or str(sv["id"]),
			"xe_may": str(sv.get("travel_mode") or "").lower() == "motorcycle",
			"service_type": sv.get("service_type") or "",
			"addon": addon,
		})
	ra.sort(key=lambda d: 0 if d["xe_may"] else 1)
	return ra


def che_loi(text):
	"""Rút gọn phản hồi lỗi để ghi nhật ký mà không lộ khoá."""
	than = str(text or "")[:500]
	than = re.sub(r'(?i)bearer\s+[^\s,"\'}]+', "Bearer [ĐÃ CHE]", than)
	than = re.sub(r'(?i)(client_secret|access_token|token|authorization)(["\']?\s*[:=]\s*["\']?)[^,"\'}&]+',
		r"\1\2[ĐÃ CHE]", than)
	return than


# ------------------------------------------------------------ phần chạm hệ

def co_khoa(c):
	"""Đủ ba ô GreenSM chưa. Chip "đã khai" ở trang Cài đặt ghim đúng điều kiện này."""
	from vagabond.lib import key

	if not (c.get("greensm_client_id") and key(c, "greensm_client_secret") and c.get("greensm_token_url")):
		return False
	return True


def dang_thu(c):
	return bool(c.get("greensm_sandbox"))


class LoiGsm(Exception):
	pass


def _token(c, lam_moi=False):
	from vagabond.lib import TIMEOUT, cache_get, cache_set, key
	import requests

	thu = dang_thu(c)
	ck = "vgb:gsm:token:" + ("thu" if thu else "that")
	if not lam_moi:
		hit = cache_get(ck)
		if hit:
			return hit
	r = requests.post(
		(c.get("greensm_token_url") or "").strip() or (TOKEN_THU if thu else TOKEN_THAT),
		data={
			"grant_type": "client_credentials",
			"client_id": c.get("greensm_client_id"),
			"client_secret": key(c, "greensm_client_secret"),
			"scope": "sandbox.express.trips" if thu else "express.trips",
		},
		timeout=TIMEOUT,
	)
	if r.status_code != 200:
		raise LoiGsm("GreenSM không cấp token (mã %s): %s" % (r.status_code, che_loi(r.text)))
	d = r.json() or {}
	tok = d.get("access_token")
	if not tok:
		raise LoiGsm("GreenSM không trả access_token, kiểm lại Client ID và Client Secret.")
	# Token sống 3600 giây; nhớ ngắn hơn hai phút để không dùng token sắp hết.
	cache_set(ck, tok, max(60, int(d.get("expires_in") or 3600) - 120))
	return tok


def goi(c, duong_dan, body=None, phuong_thuc="POST"):
	"""Gọi một endpoint Express. Hết hạn token (401) thì xin token mới, thử lại một lần."""
	from vagabond.lib import TIMEOUT
	import requests

	url = (BASE_THU if dang_thu(c) else BASE_THAT) + duong_dan
	for lan in (0, 1):
		dau = {
			"Authorization": "Bearer " + _token(c, lam_moi=bool(lan)),
			"Accept-Language": "vi",
			"Content-Type": "application/json",
		}
		if phuong_thuc == "GET":
			r = requests.get(url, headers=dau, timeout=TIMEOUT)
		else:
			r = requests.post(url, data=json.dumps(body or {}), headers=dau, timeout=TIMEOUT)
		if r.status_code == 401 and not lan:
			continue
		break
	if r.status_code not in (200, 201):
		raise LoiGsm("GreenSM trả mã %s: %s" % (r.status_code, che_loi(r.text)))
	return r.json() or {}


def dich_vu(c, lat, lng):
	"""Loại xe GreenSM mở cho tiệm, nhớ một ngày theo môi trường."""
	from vagabond.lib import cache_get, cache_set

	ck = "vgb:gsm:dichvu:" + ("thu" if dang_thu(c) else "that")
	hit = cache_get(ck)
	if hit:
		return json.loads(hit)
	ds = dich_vu_gon(goi(c, "/list-available-services", {
		"pickups": [{"latitude": float(lat), "longitude": float(lng)}],
		"service_types": ["EXPRESS-ONDEMAND"],
	}))
	if ds:
		cache_set(ck, json.dumps(ds), 86400)
	return ds


def chon_dich_vu(c, lat, lng, service_id=None):
	ds = dich_vu(c, lat, lng)
	if not ds:
		raise LoiGsm("GreenSM chưa mở loại xe nào cho tài khoản của tiệm.")
	if service_id:
		for d in ds:
			if str(d["id"]) == str(service_id):
				return d
		raise LoiGsm("Loại xe %s không còn mở cho tiệm." % service_id)
	return ds[0]


def bao_gia(c, diem_lay, diem_giao, order_time=0, service_id=None, addon_ids=(), cod=0):
	"""Báo giá một tuyến. Trả (bản giá, thân đã gửi)."""
	dv = chon_dich_vu(c, diem_lay["latitude"], diem_lay["longitude"], service_id)
	than = than_bao_gia(dv["id"], order_time, diem_lay, diem_giao, addon_ids, cod)
	bg = doc_bao_gia(goi(c, "/estimate/order", than), dv["id"])
	if bg.get("loi"):
		raise LoiGsm(bg["loi"])
	return bg, than


def phi_cho_web(c, diem_lay, diem_khach, moc):
	"""Cho trang đặt bánh: (data giống Ahamove {total_fee, distance}, lý do lỗi).

	Đang chạy thử thì KHÔNG báo số: giá sandbox là giá giả."""
	if dang_thu(c):
		return None, "greensm_dang_chay_thu"
	lay = diem("PICK UP", diem_lay["lat"], diem_lay["lng"], diem_lay.get("ten"), c.get("ahamove_mobile"),
		diem_lay.get("dia_chi"), hang=True)
	khach = diem("DROP OFF", diem_khach["lat"], diem_khach["lng"], "Khách", c.get("ahamove_mobile"),
		diem_khach.get("dia_chi"))
	try:
		bg, _than = bao_gia(c, lay, khach, moc)
	except Exception as e:
		_ghi_loi_web_mot_lan(che_loi(str(e)))
		return None, "greensm_loi"
	return {"total_fee": bg["tong"], "distance": bg["km"]}, None


def _ghi_loi_web_mot_lan(loi):
	"""Khách gõ địa chỉ liên tục: mỗi ngày chỉ ghi Error Log một lần cho đỡ ngập."""
	from datetime import date

	from vagabond.lib import cache_get, cache_set

	khoa = "vgb:gsm:loi-web:" + date.today().isoformat()
	if cache_get(khoa):
		return
	cache_set(khoa, "1", 86400)
	try:
		frappe.log_error(title="Vagabond: GreenSM không báo phí web", message=loi[:2000])
	except Exception:
		pass


@frappe.whitelist()
def thu_ket_noi():
	"""Chạy đủ chuỗi danh sách xe, báo giá, tạo đơn, xem đơn trên MÔI TRƯỜNG THỬ.

	Dùng cho bước nghiệm thu tích hợp của GreenSM. Chỉ chạy khi đang bật môi
	trường thử, để không bao giờ gọi một chiếc xe thật từ nút thử."""
	from vagabond.lib import cfg

	frappe.only_for("System Manager")
	c = cfg()
	if not co_khoa(c):
		frappe.throw("Chưa khai đủ Client ID, Client Secret và địa chỉ lấy token GreenSM.")
	if not dang_thu(c):
		frappe.throw("Nút thử chỉ chạy ở môi trường thử GreenSM, để không gọi xe thật.")
	if not (c.get("kitchen_lat") and c.get("kitchen_lng")):
		frappe.throw("Chưa khai toạ độ bếp trong mục Bản đồ.")
	buoc = []
	try:
		ds = dich_vu(c, c.kitchen_lat, c.kitchen_lng)
		buoc.append("Danh sách loại xe: %s" % ", ".join("%s (%s)" % (d["ten"], d["id"]) for d in ds))
		lay = diem("PICK UP", c.kitchen_lat, c.kitchen_lng, "The Vagabond", c.get("ahamove_mobile"),
			c.get("kitchen_address"), ghi_chu="Đơn thử kết nối, không giao", hang=True)
		lat2 = float(c.store_lat or c.kitchen_lat) + (0 if c.store_lat else 0.01)
		lng2 = float(c.store_lng or c.kitchen_lng)
		giao = diem("DROP OFF", lat2, lng2, "Khách thử", c.get("ahamove_mobile"),
			c.get("store_address") or c.get("kitchen_address"))
		bg, than = bao_gia(c, lay, giao, 0)
		buoc.append("Báo giá: %s đ, %s km, mã giá %s" % ("{:,}".format(bg["tong"]).replace(",", "."), bg["km"], bg["fee_id"]))
		tao = goi(c, "/create-order", than_tao_don(bg, than, "THU-%s" % frappe.generate_hash(length=8)))
		oid = (tao.get("data") or {}).get("id")
		buoc.append("Tạo đơn: mã %s, trạng thái %s" % (oid, (tao.get("data") or {}).get("status")))
		if oid:
			xem = goi(c, "/orders/" + oid, phuong_thuc="GET")
			buoc.append("Xem đơn: trạng thái %s" % ((xem.get("data") or {}).get("status")))
	except LoiGsm as e:
		buoc.append("DỪNG: %s" % e)
		return {"ok": 0, "buoc": buoc}
	return {"ok": 1, "buoc": buoc}
