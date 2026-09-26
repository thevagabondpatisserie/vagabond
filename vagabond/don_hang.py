"""Tao don that ben Pancake POS tu trang dat banh.

Cho khach vang lai goi, nen KHONG duoc tin bat ky con so nao trinh duyet
gui len. Phi giao tinh lai o may chu; so luong, so dien thoai, ma hang
deu duoc lam sach truoc khi gui di.

TU #367 (25/09/2026): moi lan gui la MOT ban ghi `Vagabond Don Web` ghi va
commit TRUOC khi goi Pancake. Pancake mat phan hoi thi ban ghi sang Cho doi
soat, khach van sang trang bien nhan, va tac vu 5 phut tu di tim don. Xem
dau tep vagabond/don_web.py.

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

from vagabond import don_web
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


def _gia_va_ten(cac_ma):
	"""Gia ban va ten mon theo ho so mon ERP. Khach vang lai goi nen dung
	get_all (khong soi quyen), chi doc ba cot."""
	if not cac_ma:
		return {}, {}
	ds = frappe.get_all(
		"Item",
		filters={"item_code": ["in", list(cac_ma)]},
		fields=["item_code", "item_name", "standard_rate"],
		limit_page_length=0,
	)
	return (
		{x["item_code"]: x.get("standard_rate") or 0 for x in ds},
		{x["item_code"]: x.get("item_name") or x["item_code"] for x in ds},
	)


def _ip_va_trinh_duyet():
	try:
		req = frappe.local.request
		return getattr(frappe.local, "request_ip", None), str(req.headers.get("User-Agent") or "")[:400]
	except Exception:
		return None, ""


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def tao_don(don=None):
	"""Nhan don tu trang dat banh: ghi ban ghi don web, roi tao don ben Pancake."""
	if isinstance(don, str):
		try:
			don = json.loads(don)
		except ValueError:
			return {"ok": 0, "ly_do": "du_lieu_khong_doc_duoc"}
	if not isinstance(don, dict):
		return {"ok": 0, "ly_do": "thieu_du_lieu"}

	# Trang cu con mo trong trinh duyet tu truoc dot #367 khong gui nonce va o
	# dong y. Nhan don khong co hai thu do la mat chong trung va mat bang
	# chung dong y, nen bao khach tai lai trang chu khong doan.
	nonce = str(don.get("nonce") or "")
	if not don_web.nonce_hop_le(nonce):
		return {"ok": 0, "ly_do": "can_tai_lai_trang"}
	if don.get("dong_y") is not True:
		return {"ok": 0, "ly_do": "chua_dong_y_chinh_sach"}

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

	ngay = _ngay_iso(don.get("ngay_nhan"))

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
			ngay=ngay,
		)
		if nhac:
			return {"ok": 0, "ly_do": "het_hang_mua_vu", "nhac": nhac}
	except Exception:
		# Hong phep kiem KHONG duoc chan don thuong. Ghi log roi di tiep: chan
		# nham ca tiem vi mot loi phu la cai gia dat hon nhieu so voi mot don
		# mua vu lot qua, ma don do van con chot chan o before_submit ben trong.
		frappe.log_error(frappe.get_traceback(), "don_hang: kiem han muc mua vu")

	# Tien banh TINH LAI o day theo gia ho so mon (QT-19). Con so trinh duyet
	# hien cho khach khong duoc dung de quyet mien phi giao.
	hang_goc = [dict(h) for h in hang]
	gia, ten_mon = _gia_va_ten([h["variation_id"] for h in hang_goc])
	tien_banh, _thieu_gia = don_web.tinh_tien_banh(hang_goc, gia)

	# Phi giao TINH LAI o day. Con so tu trinh duyet gui len chi de hien
	# cho khach xem, khong duoc dung lam so tien that.
	# Truyen luon moc gio khach chon, vi gia Ahamove doi theo gio.
	# Don tu lay thi khong goi Ahamove.
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
	phi = don_web.quyet_phi_giao(tien_banh, don_web.nguong_mien_phi(), tu_lay, bao_phi)

	# Doi ma hang sang UUID truoc khi gui. Thieu mot ma la dung lai bao ngay,
	# con hon de Pancake tu choi ca don voi loi chung chung. Lam TRUOC khi ghi
	# ban ghi: loi o day la chac chan chua co don nao.
	for h in hang:
		vid = _uuid_tu_ma(c, k, h["variation_id"])
		if not vid:
			return {"ok": 0, "ly_do": "khong_tim_thay_ma_hang", "ma": h["variation_id"]}
		h["variation_id"] = vid

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
		#
		# #367: truoc day ca hai o cung nhan mot con so. Nay tach that: don
		# duoc mien phi giao thi khach tra 0 nhung tiem van tra Ahamove.
		"partner_fee": int(phi.get("phi_ahamove") or 0),
		"shipping_fee": int(phi.get("phi_khach") or 0),
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

	thanh_toan = don.get("thanh_toan") if don.get("thanh_toan") in ("bank", "card") else "bank"
	snapshot = {
		"mon": [
			{"ma": h["variation_id"], "ten": ten_mon.get(h["variation_id"]) or h["variation_id"],
			 "sl": int(h["quantity"]), "gia": int(float(gia.get(h["variation_id"]) or 0))}
			for h in hang_goc
		],
		"nguoi_dat": {"ho_ten": ten, "dien_thoai": dien_thoai, "email": (don.get("email") or "").strip()},
		"nguoi_nhan": {"ho_ten": (nguoi_nhan.get("ho_ten") or "").strip(),
			"dien_thoai": _so(nguoi_nhan.get("dien_thoai"))} if nguoi_nhan else None,
		"tu_lay": tu_lay,
		"dia_chi": dia_chi,
		"diem_lay_ten": (don.get("diem_lay_ten") or "").strip()[:80] if tu_lay else "",
		"ngay_nhan": ngay,
		"ghi_chu": body["note"],
		"ghi_chu_in": body["note_print"],
		"the": the,
		"hoa_don": {
			"tax_code": _so(hd.get("tax_code")), "name": (hd.get("name") or "").strip(),
			"address": (hd.get("address") or "").strip(), "email": (hd.get("email") or "").strip(),
		} if hd_pancake else None,
		"thanh_toan": thanh_toan,
		"phi": phi,
		"thieu_gia": _thieu_gia,
	}

	ip, ua = _ip_va_trinh_duyet()
	khoa = don_web.khoa_chong_trung(dien_thoai, hang_goc, ngay, nonce)

	# GHI BAN GHI TRUOC, COMMIT, roi moi goi Pancake. Khoa tep bao quanh phep
	# tim trung va phep ghi, de hai lan bam cung luc khong cung lot qua.
	with don_web.khoa_ghi(khoa):
		trung = don_web.tim_trung(khoa)
		if trung:
			return don_web.phan_hoi(trung, nonce, trung=True)
		ban_ghi = don_web.tao_ban_ghi(nonce, {
			"ho_ten": ten,
			"dien_thoai": dien_thoai,
			"ngay_nhan": (ngay or "").replace("T", " ") or None,
			"tu_lay": 1 if tu_lay else 0,
			"thanh_toan": thanh_toan,
			"tien_banh": tien_banh,
			"phi_khach": phi.get("phi_khach") or 0,
			"phi_ahamove": phi.get("phi_ahamove") or 0,
			"tiem_chiu_phi": phi.get("tiem_chiu") or 0,
			"mien_phi_giao": 1 if phi.get("mien_phi") else 0,
			"trang_thai_phi": phi.get("trang_thai"),
			"khoa_chong_trung": khoa,
			"fbp": str(don.get("fbp") or "")[:250] if don_web.fb_hop_le(don.get("fbp")) else "",
			"fbc": str(don.get("fbc") or "")[:250] if don_web.fb_hop_le(don.get("fbc")) else "",
			"trinh_duyet": ua,
			"snapshot": json.dumps(snapshot, ensure_ascii=False),
		})
		frappe.db.commit()

	# KHONG tu gui lai: Pancake khong co co che chong trung cong khai nao de
	# dua vao, gui lai sau mot lan mat phan hoi la nguy co hai don.
	ma_http, du_lieu, loi_mang = 0, None, False
	try:
		r = requests.post(
			"%s/shops/%s/orders" % (PANCAKE, shop_id),
			params={"api_key": k},
			json=body,
			timeout=TIMEOUT,
		)
		ma_http = r.status_code
		try:
			du_lieu = r.json()
		except ValueError:
			du_lieu = None
		if ma_http not in (200, 201):
			frappe.log_error(title="Vagabond: Pancake tu choi don", message="%s HTTP %s: %s" % (ban_ghi.name, ma_http, (r.text or "")[:800]))
	except Exception:
		loi_mang = True
		frappe.log_error(title="Vagabond: Pancake khong tao duoc don", message=frappe.get_traceback())

	kq = don_web.phan_loai_pancake(ma_http, du_lieu, loi_mang)
	don_web.cap_nhat_sau_pancake(ban_ghi, kq)
	frappe.db.commit()

	if kq["ket_qua"] == "tu_choi":
		return {"ok": 0, "ly_do": kq["ly_do"]}

	don_web.xep_capi(ban_ghi.name, "GuiDon", ip=ip, ua=ua)
	return don_web.phan_hoi(ban_ghi, nonce)
