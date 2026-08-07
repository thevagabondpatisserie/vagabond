"""Yeu cau thanh toan: sales chot duoc don roi moi gui link cho khach.

Anh Viet 07/08/2026 bac phuong an bat khach chuyen khoan ngay khi dat: phi
giao nhieu khi chi la so uoc luong, chua ke phu thu hang de vo; khach xa qua
15km thi khong giao duoc. Khach chuyen tien xong ma khong giao duoc thi phai
hoan tien, mat thoi gio hon.

Luong dung la:
  khach dat -> sales xem co giao duoc khong -> BAM MOT NUT
  -> he thong gui tin Zalo ZNS kem link trang QR -> khach quet, chuyen khoan

MA QR LAY TU PANCAKE, KHONG TU SINH. Ly do do that ngay 07/08: MB cap cho
moi don MOT SO TAI KHOAN AO khac nhau (don 91429 ra VQRQALAFY2856, don 91432
ra VQRQALAFZ3966). Chinh nho vay MB bao co la Pancake tu khop dung don nao da
tra. Tu sinh QR vao tai khoan that thi mat het phan doi soat tu dong do.

Endpoint Pancake dung (khong co trong tai lieu, do lai tu giao dien POS):
  POST {PANCAKE}/shops/{shop}/orders/payment_qr?api_key=...
  {"provider":"mbbank","display_id":91429,"account_id":1290000210,"bin":"970422"}
  -> {"success":true,"account_number":"VQRQALAGD7534","qr_text":"0002010102123857..."}

qr_text la chuoi EMVCo chuan VietQR, trong do co san so tien va noi dung
chuyen khoan do Pancake quyet dinh.

Luu y: MOI LAN goi la Pancake cap mot so tai khoan ao MOI. Nen chi goi mot
lan cho moi don, cat lai, so tien doi moi goi lai.
"""

import json
import re
import secrets

import frappe
import requests
from frappe.utils import now_datetime

from vagabond import whatsapp, zalo
from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

VIETQR_ANH = "https://img.vietqr.io/image"


def _so(s):
	return "".join(ch for ch in str(s or "") if ch.isdigit())


def _sdt84(sdt):
	s = _so(sdt)
	if s.startswith("84") and len(s) >= 11:
		return s
	if s.startswith("0") and len(s) >= 9:
		return "84" + s[1:]
	if len(s) == 9:
		return "84" + s
	return s


def _vnd(n):
	return "{:,.0f}".format(int(n or 0)).replace(",", ".")


def _tlv(chuoi):
	"""Tach chuoi EMVCo thanh tu dien tag -> gia tri."""
	ra, i = {}, 0
	x = str(chuoi or "")
	while i + 4 <= len(x):
		tag = x[i : i + 2]
		try:
			dai = int(x[i + 2 : i + 4])
		except ValueError:
			break
		ra[tag] = x[i + 4 : i + 4 + dai]
		i += 4 + dai
	return ra


def _doc_qr(qr_text):
	"""Boc so tien, noi dung, ma BIN va so tai khoan ao ra khoi chuoi VietQR."""
	g = _tlv(qr_text)
	t38 = _tlv(g.get("38", ""))
	t62 = _tlv(g.get("62", ""))
	# Tag 38 truong 01 la "0006<BIN>0113<so tai khoan>", lai la TLV long nhau.
	nh = _tlv(t38.get("01", ""))
	try:
		tien = int(g.get("54") or 0)
	except ValueError:
		tien = 0
	return {
		"bin": nh.get("00", ""),
		"stk": nh.get("01", ""),
		"so_tien": tien,
		"noi_dung": t62.get("08", ""),
	}


def _don_pancake(c, k, ma_don):
	r = requests.get(
		"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
		params={"api_key": k, "search": str(ma_don), "page_size": 5, "page_number": 1},
		timeout=TIMEOUT,
	)
	for o in (r.json() or {}).get("data") or []:
		if str(o.get("id")) == str(ma_don) or str(o.get("system_id")) == str(ma_don):
			return o
	return None


def _minh_tinh(o):
	"""So tien minh tu tinh, chi de doi chieu voi so Pancake dua ra."""
	tong = int(o.get("total_price") or 0)
	phi = int(o.get("partner_fee") or 0) or int(o.get("shipping_fee") or 0)
	da = int(o.get("prepaid") or 0)
	return max(0, tong + phi - da), tong, phi, da


def _xin_qr(c, k, ma_don):
	"""Xin Pancake cap ma QR cho mot don. Tra (du_lieu, loi)."""
	tk = str(c.get("pancake_qr_account_id") or "").strip()
	if not tk:
		return None, "Chưa điền Account ID tài khoản nhận tiền của Pancake trong Vagabond Settings"
	than = {
		"provider": (c.get("pancake_qr_provider") or "mbbank").strip(),
		"display_id": int(_so(ma_don) or 0),
		"account_id": int(tk),
		"bin": (c.get("ngan_hang_bin") or "970422").strip(),
	}
	try:
		r = requests.post(
			"%s/shops/%s/orders/payment_qr" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k},
			json=than,
			timeout=TIMEOUT,
		)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: xin QR Pancake loi mang", message=frappe.get_traceback())
		return None, "Không gọi được Pancake"
	if not j.get("success") or not j.get("qr_text"):
		frappe.log_error(title="Vagabond: Pancake khong cap QR", message=json.dumps(j)[:1000])
		return None, j.get("message") or "Pancake không cấp được mã QR"
	return j, ""


def _link(c, ma_bam):
	goc = (c.get("trang_thanh_toan") or "").strip().rstrip("/")
	if not goc:
		goc = "https://order.thevagabondpatisserie.com/tt"
	return "%s?m=%s" % (goc, ma_bam)


@frappe.whitelist()
def tao_va_gui(ma_don, kenh="zalo", sdt=None):
	"""Sales bam nut: xin QR tu Pancake roi gui cho khach.

	kenh: "zalo" (mac dinh), "whatsapp", hoac "ca_hai".
	"""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")

	o = _don_pancake(c, k, ma_don)
	if not o:
		frappe.throw("Không tìm thấy đơn %s bên Pancake" % ma_don)

	minh_tinh, tong, phi, da = _minh_tinh(o)
	sdt_don = (o.get("shipping_address") or {}).get("phone_number") or o.get("bill_phone_number")
	s84 = _sdt84(sdt or sdt_don)
	if not re.match(r"^84\d{9}$", s84):
		frappe.throw("Đơn %s không có số điện thoại hợp lệ để gửi" % ma_don)
	ten_khach = (o.get("shipping_address") or {}).get("full_name") or o.get("bill_full_name") or ""

	# Moi lan goi Pancake la mot so tai khoan ao moi, nen dung lai ban cu neu
	# van con hieu luc va so tien khong doi.
	cu = frappe.get_all(
		"Vagabond Yeu Cau TT",
		filters={"ma_don": str(ma_don), "tinh_trang": "Cho thanh toan"},
		fields=["name", "so_tien"],
		order_by="creation desc",
		limit_page_length=1,
	)
	doc = None
	if cu:
		doc = frappe.get_doc("Vagabond Yeu Cau TT", cu[0]["name"])
		if not doc.qr_text:
			doc = None

	if doc is None:
		j, loi = _xin_qr(c, k, ma_don)
		if not j:
			frappe.throw(loi)
		q = _doc_qr(j.get("qr_text"))
		for x in cu:
			frappe.db.set_value("Vagabond Yeu Cau TT", x["name"], "tinh_trang", "Da huy")
		doc = frappe.new_doc("Vagabond Yeu Cau TT")
		doc.ma_don = str(ma_don)
		doc.ma_bam = secrets.token_urlsafe(16)
		doc.sdt = s84
		doc.ten_khach = ten_khach
		doc.so_tien = q["so_tien"]
		doc.tien_hang = tong
		doc.phi_giao = phi
		doc.da_tra = da
		doc.noi_dung_ck = q["noi_dung"]
		doc.stk_ao = j.get("account_number") or q["stk"]
		doc.qr_text = j.get("qr_text")
		doc.tinh_trang = "Cho thanh toan"
		doc.insert(ignore_permissions=True)
		frappe.db.commit()

	link = _link(c, doc.ma_bam)
	ket = {}

	if kenh in ("zalo", "ca_hai"):
		xong, loi = zalo.gui_tin(
			c,
			s84,
			(c.get("zns_template_thanh_toan") or "").strip(),
			{
				"ma_don": str(ma_don),
				"so_tien": _vnd(doc.so_tien),
				"link": link,
				"ten_khach": ten_khach,
			},
			dau_vet="vgb-tt-%s" % ma_don,
		)
		ket["zalo"] = {"ok": 1 if xong else 0, "loi": loi}

	if kenh in ("whatsapp", "ca_hai"):
		xong, loi = whatsapp.gui_mau(
			c,
			s84,
			(c.get("wa_template_thanh_toan") or "").strip(),
			[str(ma_don), _vnd(doc.so_tien) + " d", link],
		)
		ket["whatsapp"] = {"ok": 1 if xong else 0, "loi": loi}

	if any(v.get("ok") for v in ket.values()):
		doc.db_set("gui_luc", now_datetime())
		frappe.db.commit()

	return {
		"ok": 1 if any(v.get("ok") for v in ket.values()) else 0,
		"link": link,
		"so_tien": int(doc.so_tien or 0),
		"noi_dung_ck": doc.noi_dung_ck,
		"stk_ao": doc.stk_ao,
		# Pancake tu quyet so tien. Neu lech voi cach minh tinh thi bao ra cho
		# sales biet chu khong im lang - co don Pancake chi thu tien hang, chua
		# gom phi giao.
		"minh_tinh": minh_tinh,
		"lech": minh_tinh - int(doc.so_tien or 0),
		"kenh": ket,
	}


@frappe.whitelist(allow_guest=True)
def xem(m=None):
	"""Trang thanh toan cua khach doc o day."""
	if not m:
		return {"ok": 0, "ly_do": "thieu_ma"}
	ds = frappe.get_all(
		"Vagabond Yeu Cau TT",
		filters={"ma_bam": m},
		fields=[
			"name",
			"ma_don",
			"ten_khach",
			"so_tien",
			"tien_hang",
			"phi_giao",
			"da_tra",
			"noi_dung_ck",
			"stk_ao",
			"qr_text",
			"tinh_trang",
		],
		limit_page_length=1,
	)
	if not ds:
		return {"ok": 0, "ly_do": "khong_thay"}
	d = ds[0]
	c = cfg()
	q = _doc_qr(d.get("qr_text") or "")
	from urllib.parse import quote

	anh = ""
	stk = d.get("stk_ao") or q.get("stk") or ""
	binh = q.get("bin") or (c.get("ngan_hang_bin") or "").strip()
	if stk and binh:
		anh = "%s/%s-%s-compact2.png?amount=%s&addInfo=%s&accountName=%s" % (
			VIETQR_ANH,
			binh,
			stk,
			int(d.get("so_tien") or 0),
			quote(d.get("noi_dung_ck") or ""),
			quote((c.get("ngan_hang_ten") or "").strip()),
		)
	return {
		"ok": 1,
		"ma_don": d["ma_don"],
		"ten_khach": d["ten_khach"],
		"so_tien": int(d["so_tien"] or 0),
		"tien_hang": int(d["tien_hang"] or 0),
		"phi_giao": int(d["phi_giao"] or 0),
		"da_tra": int(d["da_tra"] or 0),
		"noi_dung_ck": d["noi_dung_ck"],
		"tinh_trang": d["tinh_trang"],
		"ngan_hang": {
			"ten": (c.get("ngan_hang_hien_thi") or "").strip(),
			"stk": stk,
			"chu_tk": (c.get("ngan_hang_ten") or "").strip(),
		},
		"qr": anh,
	}


@frappe.whitelist()
def danh_dau_da_tra(ma_don=None, ghi_chu=None):
	"""Ke toan xac nhan da nhan tien.

	Thuong thi khong phai bam tay: MB bao co ve Pancake theo so tai khoan ao,
	Pancake tu danh dau don da tra. Ham nay de danh cho truong hop khach tra
	kieu khac hoac Pancake khong nhan duoc.
	"""
	ds = frappe.get_all(
		"Vagabond Yeu Cau TT",
		filters={"ma_don": str(ma_don or ""), "tinh_trang": "Cho thanh toan"},
		pluck="name",
	)
	if not ds:
		frappe.throw("Không có yêu cầu thanh toán nào đang chờ cho đơn %s" % ma_don)
	for n in ds:
		d = frappe.get_doc("Vagabond Yeu Cau TT", n)
		d.tinh_trang = "Da thanh toan"
		d.tra_luc = now_datetime()
		d.ghi_chu = ghi_chu
		d.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "so_yeu_cau": len(ds)}


@frappe.whitelist()
def ds_cho_thu(gioi_han=100):
	"""Danh sach yeu cau dang cho khach chuyen, cho man hinh ke toan."""
	return frappe.get_all(
		"Vagabond Yeu Cau TT",
		filters={"tinh_trang": "Cho thanh toan"},
		fields=[
			"name",
			"ma_don",
			"ten_khach",
			"sdt",
			"so_tien",
			"noi_dung_ck",
			"stk_ao",
			"gui_luc",
			"creation",
		],
		order_by="creation desc",
		limit_page_length=int(gioi_han or 100),
	)
