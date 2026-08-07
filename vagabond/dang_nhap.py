"""Dang nhap cho khach tren trang dat banh: so dien thoai + ma OTP qua Zalo ZNS.

Vi sao khong dung email va mat khau (chot voi anh Viet 06/08/2026):
danh sach 50.000 khach xuat tu iPOS CRM chi co DUNG 22 email. So dien thoai
thi 100% khach co, iPOS khoa theo so dien thoai, don Pancake cung khoa theo so
dien thoai. Lay so dien thoai lam khoa thi ghep duoc lich su ngay tu ngay dau,
khach khong phai khai lai gi.

Vi sao ZNS chu khong phai SMS: ZNS gui duoc toi moi so, khach KHONG can quan
tam OA, gia khoang 300d mot tin da gui thanh cong, re hon SMS brandname.

Bao mat:
- Ma OTP KHONG luu dang chu, chi luu bam sha256 kem muoi cua site.
- Ma song 5 phut, sai 5 lan la khoa ma do.
- Moi so dien thoai toi da 5 ma moi 30 phut; endpoint co rate_limit theo IP.
- Phien khach la mot chuoi ngau nhien 48 byte, luu ban bam, song 30 ngay.
  KHONG tao User trong Frappe cho tung khach - 50.000 User se lam nang he
  thong va lam ro ret danh sach nguoi dung that.
"""

import hashlib
import json
import re
import secrets
from datetime import timedelta

import frappe
import requests
from frappe.rate_limiter import rate_limit
from frappe.utils import add_days, now_datetime

from vagabond import zalo
from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

OTP_SONG_PHUT = 5
OTP_SAI_TOI_DA = 5
OTP_MOI_30_PHUT = 5
PHIEN_SONG_NGAY = 30


def _so(s):
	return "".join(ch for ch in str(s or "") if ch.isdigit())


def _chuan_sdt(sdt):
	"""Ve dang 84xxxxxxxxx de khop voi iPOS va Zalo.

	Khach go 0901486556, 84901486556 hay +84 901 486 556 deu ra mot ket qua.
	"""
	s = _so(sdt)
	if s.startswith("84") and len(s) >= 11:
		return s
	if s.startswith("0") and len(s) >= 9:
		return "84" + s[1:]
	if len(s) == 9:
		return "84" + s
	return s


def _sdt_noi_dia(sdt84):
	"""84901486556 -> 0901486556, dang Pancake va iPOS dang luu."""
	s = _so(sdt84)
	return "0" + s[2:] if s.startswith("84") else s


def _bam(chuoi):
	"""Bam kem muoi rieng cua site, de lo bang cung khong doi nguoc ra ma."""
	muoi = frappe.local.conf.get("encryption_key") or frappe.local.site
	return hashlib.sha256(("vgb:" + str(muoi) + ":" + str(chuoi)).encode()).hexdigest()


# ---------------------------------------------------------------- Zalo ZNS


def _gui_zns(c, sdt84, ma):
	"""Gui ma xac thuc. Ham gui chung nam o vagabond/zalo.py."""
	return zalo.gui_tin(
		c,
		sdt84,
		(c.get("zns_template_otp") or "").strip(),
		{"otp": ma},
		dau_vet="vgb-otp-%s" % sdt84,
	)


# ---------------------------------------------------------------- OTP


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=12, seconds=600)
def gui_ma(sdt=None):
	"""Sinh ma 6 so, gui qua ZNS. Khong bao gio tra ma ve trinh duyet."""
	s = _chuan_sdt(sdt)
	if not re.match(r"^84\d{9}$", s):
		return {"ok": 0, "ly_do": "so_dien_thoai_khong_dung"}

	tu = now_datetime() - timedelta(minutes=30)
	da_gui = frappe.db.count("Vagabond OTP", {"sdt": s, "creation": [">", tu]})
	if da_gui >= OTP_MOI_30_PHUT:
		return {"ok": 0, "ly_do": "gui_qua_nhieu"}

	ma = "".join(secrets.choice("0123456789") for _ in range(6))
	doc = frappe.new_doc("Vagabond OTP")
	doc.sdt = s
	doc.ma_bam = _bam(ma)
	doc.het_han = now_datetime() + timedelta(minutes=OTP_SONG_PHUT)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	c = cfg()
	xong, loi = _gui_zns(c, s, ma)
	if not xong:
		return {"ok": 0, "ly_do": "khong_gui_duoc", "chi_tiet": loi}
	return {"ok": 1, "song_giay": OTP_SONG_PHUT * 60}


def _tao_phien(sdt84):
	tok = secrets.token_urlsafe(48)
	doc = frappe.new_doc("Vagabond Phien Khach")
	doc.sdt = sdt84
	doc.token_bam = _bam(tok)
	doc.het_han = add_days(now_datetime(), PHIEN_SONG_NGAY)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return tok


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=600)
def xac_thuc(sdt=None, ma=None):
	s = _chuan_sdt(sdt)
	ma = _so(ma)
	if not (re.match(r"^84\d{9}$", s) and len(ma) == 6):
		return {"ok": 0, "ly_do": "thieu_du_lieu"}

	ds = frappe.get_all(
		"Vagabond OTP",
		filters={"sdt": s, "da_dung": 0, "het_han": [">", now_datetime()]},
		fields=["name", "ma_bam", "so_lan_sai"],
		order_by="creation desc",
		limit_page_length=1,
	)
	if not ds:
		return {"ok": 0, "ly_do": "ma_het_han"}
	o = ds[0]
	if (o.get("so_lan_sai") or 0) >= OTP_SAI_TOI_DA:
		return {"ok": 0, "ly_do": "sai_qua_nhieu"}
	if o["ma_bam"] != _bam(ma):
		frappe.db.set_value("Vagabond OTP", o["name"], "so_lan_sai", (o.get("so_lan_sai") or 0) + 1)
		frappe.db.commit()
		return {"ok": 0, "ly_do": "ma_khong_dung"}

	frappe.db.set_value("Vagabond OTP", o["name"], "da_dung", 1)
	frappe.db.commit()
	return {"ok": 1, "token": _tao_phien(s), "sdt": _sdt_noi_dia(s)}


def _phien(token):
	"""Tra so dien thoai cua phien con han, khong thi tra None."""
	if not token:
		return None
	ds = frappe.get_all(
		"Vagabond Phien Khach",
		filters={"token_bam": _bam(token), "het_han": [">", now_datetime()]},
		fields=["name", "sdt"],
		limit_page_length=1,
	)
	return ds[0]["sdt"] if ds else None


@frappe.whitelist(allow_guest=True)
def thoat(token=None):
	if not token:
		return {"ok": 1}
	for d in frappe.get_all("Vagabond Phien Khach", filters={"token_bam": _bam(token)}, pluck="name"):
		frappe.delete_doc("Vagabond Phien Khach", d, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"ok": 1}


# ---------------------------------------------------------------- Cong khach


def _don_pancake(c, k, sdt_noi_dia, gioi_han=30):
	"""Lich su don cua mot so dien thoai, doc thang tu Pancake."""
	try:
		r = requests.get(
			"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": sdt_noi_dia, "page_size": gioi_han, "page_number": 1},
			timeout=TIMEOUT,
		)
		ds = (r.json() or {}).get("data") or []
	except Exception:
		frappe.log_error(title="Vagabond: khong doc duoc don cua khach", message=frappe.get_traceback())
		return []

	ra = []
	for o in ds:
		# Pancake tim theo chuoi nen co the tra ve don cua so khac gan giong.
		sdt_don = _so((o.get("shipping_address") or {}).get("phone_number")) or _so(o.get("bill_phone_number"))
		if _chuan_sdt(sdt_don) != _chuan_sdt(sdt_noi_dia):
			continue
		mon = []
		for it in o.get("items") or []:
			v = it.get("variation_info") or {}
			mon.append(
				{
					"ma": v.get("display_id") or "",
					"ten": v.get("name") or "",
					"sl": it.get("quantity") or 0,
				}
			)
		ra.append(
			{
				"ma_don": str(o.get("id") or o.get("system_id") or ""),
				"luc_tao": o.get("inserted_at") or "",
				"ngay_giao": o.get("estimate_delivery_date") or "",
				"trang_thai": o.get("status_name") or "",
				"tong": int(o.get("total_price") or 0),
				"dia_chi": (o.get("shipping_address") or {}).get("full_address") or "",
				"mon": mon,
			}
		)
	return ra


@frappe.whitelist(allow_guest=True)
def toi(token=None):
	"""Cong khach: ho ten, diem, lich su don. Chi tra khi phien con han."""
	sdt = _phien(token)
	if not sdt:
		return {"ok": 0, "ly_do": "chua_dang_nhap"}
	noi_dia = _sdt_noi_dia(sdt)

	kh = frappe.db.get_value(
		"Customer",
		{"mobile_no": noi_dia},
		["name", "customer_name", "loyalty_program"],
		as_dict=True,
	)
	diem = 0
	if kh:
		diem = (
			frappe.db.sql(
				"""select sum(loyalty_points) from `tabLoyalty Point Entry`
				where customer = %s and (expiry_date is null or expiry_date >= curdate())""",
				kh["name"],
			)[0][0]
			or 0
		)

	c = cfg()
	k = key(c, "pancake_api_key")
	don = _don_pancake(c, k, noi_dia) if (k and c.pancake_shop_id) else []
	return {
		"ok": 1,
		"sdt": noi_dia,
		"ten": (kh or {}).get("customer_name") or "",
		"khach": (kh or {}).get("name") or "",
		"diem": int(diem),
		"don": don,
	}


def don_dep_phien():
	"""3h sang moi ngay: xoa ma OTP het han va phien khach het han.

	Bang OTP moi ngay se phinh ra rat nhanh (moi lan bam gui la mot ban ghi),
	giu lai khong de lam gi vi ma da bam roi.
	"""
	moc = now_datetime()
	for dt in ("Vagabond OTP", "Vagabond Phien Khach"):
		for ten in frappe.get_all(dt, filters={"het_han": ["<", moc]}, pluck="name", limit_page_length=5000):
			frappe.delete_doc(dt, ten, ignore_permissions=True, force=True, delete_permanently=True)
	frappe.db.commit()
