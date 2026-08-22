"""Tao don that ben Pancake POS tu trang dat banh.

Cho khach vang lai goi, nen KHONG duoc tin bat ky con so nao trinh duyet
gui len. Phi giao tinh lai o may chu; so luong, so dien thoai, ma hang
deu duoc lam sach truoc khi gui di.

Dinh dang cac truong theo tai lieu docs.pancake.biz/pos/api/ va da bat
bang cach ban don thu that:
  - tags               : mang SO, khong phai mang object
  - estimate_delivery_date : ISO datetime, khong phai dd/mm/yyyy
  - account            : ma nguon don dang SO. Gui order_sources_name
                         thi Pancake bo qua lang le, khong bao loi
  - received_at_shop   : true khi khach tu lay tai cua hang
"""

import json
import re

import frappe
import requests
from frappe.rate_limiter import rate_limit

from vagabond.giao_hang import phi_giao
from vagabond.lib import PANCAKE, TIMEOUT, cache_get, cache_set, cfg, key

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


_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _uuid_tu_ma(c, k, ma):
	"""Doi ma hang nguoi doc duoc (BAWC00139) thanh variation_id UUID.

	Trang dat banh dung ma in tren tem cho de doi chieu, nhung Pancake chi
	nhan UUID. Gui ma thang vao tao don thi Pancake tra "Server internal
	error" - da dinh that ngay 31/07, khach bam gui la hong ca don.
	"""
	ma = str(ma or "").strip()
	if _UUID.match(ma.lower()):
		return ma
	ck = "vgb:vid:" + ma
	hit = cache_get(ck)
	if hit:
		return hit
	try:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
	except Exception:
		frappe.log_error(title="Vagabond: khong tra duoc ma hang", message=frappe.get_traceback())
		return None
	if r.status_code != 200:
		return None
	for v in (r.json() or {}).get("data") or []:
		if str(v.get("display_id") or "").strip().lower() == ma.lower():
			vid = v.get("id")
			if vid:
				cache_set(ck, vid, 86400)
				return vid
	return None


def _lam_sach_the(tags):
	"""Pancake chi nhan mang so. Gui object thi the khong duoc gan."""
	ra = []
	for t in (tags or [])[:10]:
		if isinstance(t, dict):
			t = t.get("id")
		try:
			n = int(t)
		except (TypeError, ValueError):
			continue
		if n not in ra:
			ra.append(n)
	return ra


def _ngay_iso(v):
	"""Doi ngay nhan ve ISO datetime.

	Nhan san ISO thi giu nguyen. Nhan dd/mm/yyyy thi doi, vi ban portal cu
	gui kieu do va Pancake im lang bo qua.
	"""
	v = str(v or "").strip()
	if not v:
		return None
	m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", v)
	if m:
		d, thg, nam = m.groups()
		return "%s-%02d-%02dT00:00:00" % (nam, int(thg), int(d))
	return v


def _hoa_don_pancake(hd):
	"""Goi thong tin hoa don theo dung dinh dang invoice_info_list cua Pancake."""
	mst = _so(hd.get("tax_code"))
	if not mst:
		return None
	dia_chi = (hd.get("address") or "").strip()
	return [
		{
			"invoice_type": "company",
			"is_requested": True,
			"invoice_detail": {
				"company_tax_id": mst,
				"company_name": (hd.get("name") or "").strip(),
				"company_address": dia_chi,
				"company_email": (hd.get("email") or "").strip(),
			},
		}
	]


def _luu_hoa_don(ma_don, hd):
	"""Ban doi chieu cho ke toan, giu ben ERPNext.

	Van giu du Pancake da nhan invoice_info_list, vi ke toan can loc va danh
	dau da xuat hay chua - Pancake khong co cho danh dau viec do.
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
		frappe.log_error(title="Vagabond: khong luu duoc hoa don", message=frappe.get_traceback())


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

	# CHOT CHAN HAN MUC MUA VU (them 21/08/2026 cung dot dua hang mua vu len web).
	#
	# Trinh duyet da khoa nut o nhung mon het hang, nhung ai cung goi thang
	# endpoint nay duoc, va giua luc khach mo trang voi luc khach bam dat co the
	# da co nguoi khac mua mat. Hang mua vu la hang co han muc cung: ban lo mot
	# hop la mot loi hua khong giu duoc, khong phai mot dong so am tren bang.
	#
	# Goi thang kiem_han_muc chu khong goi kiem_truoc_khi_ban, vi ham kia co
	# _kiem_quyen() danh cho nhan vien, con day la khach vang lai.
	try:
		from vagabond import mua_vu

		nhac = mua_vu.kiem_han_muc(
			[{"item_code": h["variation_id"], "qty": h.get("quantity") or 0} for h in hang],
			ngay=_ngay_iso(don.get("ngay_nhan")),
		)
		if nhac:
			return {"ok": 0, "ly_do": "het_hang_mua_vu", "nhac": nhac}
	except Exception:
		# Hong phep kiem KHONG duoc chan don thuong. Ghi log roi di tiep: chan
		# nham ca tiem vi mot loi phu la cai gia dat hon nhieu so voi mot don
		# mua vu lot qua, ma don do van con chot chan o before_submit ben trong.
		frappe.log_error(frappe.get_traceback(), "don_hang: kiem han muc mua vu")

	# Doi ma hang sang UUID truoc khi gui. Thieu mot ma la dung lai bao ngay,
	# con hon de Pancake tu choi ca don voi loi chung chung.
	for h in hang:
		vid = _uuid_tu_ma(c, k, h["variation_id"])
		if not vid:
			return {"ok": 0, "ly_do": "khong_tim_thay_ma_hang", "ma": h["variation_id"]}
		h["variation_id"] = vid

	ten = (don.get("ho_ten") or "").strip()
	dien_thoai = _so(don.get("dien_thoai"))
	if not ten or len(dien_thoai) < 9:
		return {"ok": 0, "ly_do": "thieu_ten_hoac_so_dien_thoai"}

	tu_lay = bool(don.get("tu_lay"))
	dia_chi = (don.get("dia_chi") or "").strip()
	if not tu_lay and len(dia_chi) < 8:
		return {"ok": 0, "ly_do": "thieu_dia_chi_giao"}

	ngay = _ngay_iso(don.get("ngay_nhan"))

	# Phi giao TINH LAI o day. Con so tu trinh duyet gui len chi de hien
	# cho khach xem, khong duoc dung lam so tien that.
	# Truyen luon moc gio khach chon, vi gia Ahamove doi theo gio.
	# Don tu lay thi khong goi Ahamove.
	phi = 0
	bao_phi = None
	if not tu_lay:
		bao_phi = phi_giao(
			addr=dia_chi, lat=don.get("lat"), lng=don.get("lng"), luc_giao=ngay
		)
		# Ngoai vung giao thi KHONG tao don. Chan o trinh duyet roi van phai
		# chan lai o day, vi ai cung goi thang endpoint duoc.
		if bao_phi.get("ly_do") == "ngoai_vung_giao":
			return {
				"ok": 0,
				"ly_do": "ngoai_vung_giao",
				"khoang_cach": bao_phi.get("khoang_cach"),
				"ban_kinh": bao_phi.get("ban_kinh"),
			}
		if bao_phi.get("ok"):
			phi = int(bao_phi.get("total_fee") or 0)

	nguoi_nhan = (don.get("nguoi_nhan") or {}) if isinstance(don.get("nguoi_nhan"), dict) else {}
	shop_id = c.pancake_shop_id

	body = {
		"shop_id": int(shop_id),
		"bill_full_name": ten,
		"bill_phone_number": dien_thoai,
		"bill_email": (don.get("email") or "").strip(),
		"shipping_address": {
			"full_name": (nguoi_nhan.get("ho_ten") or ten).strip(),
			"phone_number": _so(nguoi_nhan.get("dien_thoai")) or dien_thoai,
			# Pancake BO QUA full_address khi tao don - phai gui "address".
			# Don #91428 ngay 06/08/2026 la vet that: khach chon dia chi tu so,
			# phi giao tinh ra 26.000d (tuc dia chi co that), nhung don ve POS
			# co full_address rong tron, sales khong biet giao di dau. Do lai
			# bang PUT chi mot truong "address" thi Pancake tu tach ra duong,
			# phuong, tinh va tu dung lai full_address.
			"address": dia_chi,
			"full_address": dia_chi,
		},
		"items": hang,
		"note_print": (don.get("note_print") or "").strip(),
		"note": (don.get("note") or "").strip(),
		# partner_fee = tien tiem TRA cho ben giao (chi phi cua tiem).
		# shipping_fee = tien tiem THU cua khach. Phai gui ca hai, neu chi gui
		# partner_fee thi Pancake tinh cod = tien hang, ma QR chi thu tien banh,
		# thieu dung phan phi giao (don thu #91429 ngay 06/08/2026: QR ra
		# 680.000d trong khi phai thu 706.000d). Da kiem 07/08/2026: gui kem
		# shipping_fee thi Pancake tu cong cod = total_price + shipping_fee va
		# ma QR ra dung so.
		"partner_fee": phi,
		"shipping_fee": phi,
		"received_at_shop": tu_lay,
		"status": 0,
	}

	nguon = str(c.pancake_order_source_id or "").strip()
	if nguon:
		try:
			body["account"] = int(nguon)
		except ValueError:
			body["account_name"] = nguon

	if ngay:
		body["estimate_delivery_date"] = ngay

	the = _lam_sach_the(don.get("tags"))
	if the:
		body["tags"] = the

	hd = don.get("hoa_don") if isinstance(don.get("hoa_don"), dict) else None
	hd_pancake = _hoa_don_pancake(hd) if hd else None
	if hd_pancake:
		body["invoice_info_list"] = hd_pancake

	try:
		r = requests.post(
			"%s/shops/%s/orders" % (PANCAKE, shop_id),
			params={"api_key": k},
			json=body,
			timeout=TIMEOUT,
		)
	except Exception:
		frappe.log_error(title="Vagabond: Pancake khong tao duoc don", message=frappe.get_traceback())
		return {"ok": 0, "ly_do": "pancake_loi"}

	if r.status_code not in (200, 201):
		frappe.log_error(title="Vagabond: Pancake tu choi don", message=r.text[:1000])
		return {"ok": 0, "ly_do": "pancake_tu_choi"}

	try:
		j = r.json() or {}
	except ValueError:
		frappe.log_error(title="Vagabond: Pancake tra ve khong phai JSON", message=r.text[:1000])
		return {"ok": 0, "ly_do": "pancake_tra_ve_la"}

	# Pancake tung doi ten truong ma don giua cac ban, nen do lan luot.
	# Luu y: API tao don tra ve display_id duoi cai ten "id".
	data = j.get("data") if isinstance(j.get("data"), dict) else j
	ma_don = data.get("id") or data.get("order_id") or data.get("system_id")
	if not ma_don:
		frappe.log_error(title="Vagabond: Pancake khong tra ve ma don", message=json.dumps(j)[:1000])
		return {"ok": 0, "ly_do": "khong_ro_ma_don"}

	if hd and _so(hd.get("tax_code")):
		_luu_hoa_don(str(ma_don), hd)

	return {
		"ok": 1,
		"ma_don": str(ma_don),
		"phi_giao": phi,
		"ly_do_phi": None if phi else (bao_phi or {}).get("ly_do"),
		"da_gui_hoa_don": bool(hd_pancake),
	}
