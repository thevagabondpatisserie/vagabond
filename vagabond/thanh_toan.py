"""Yeu cau thanh toan: sales chot duoc don roi moi gui link cho khach.

Anh Viet 07/08/2026 bac phuong an bat khach chuyen khoan ngay khi dat: phi
giao nhieu khi chi la so uoc luong, chua ke phu thu hang de vo; khach xa qua
15km thi khong giao duoc. Khach chuyen tien xong ma khong giao duoc thi phai
hoan tien, mat thoi gio hon.

Nen luong dung la:
  khach dat  ->  sales xem co giao duoc khong  ->  BAM MOT NUT
  -> he thong gui tin Zalo ZNS kem link trang QR  ->  khach quet, chuyen khoan

Cai bo duoc so voi truoc la doan goi dien roi xin ket ban Zalo de gui link.
ZNS gui thang toi so dien thoai, khach khong can quan tam OA.

So tien tren yeu cau LAY LUC BAM NUT, nghia la da gom phi giao that ma sales
da chot - khong con la so uoc luong tren web nua.
"""

import json
import re
import secrets

import frappe
import requests
from frappe.utils import now_datetime

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key
from vagabond import whatsapp, zalo

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


def _con_phai_tra(o):
	"""Tong tien khach con phai chuyen.

	Pancake de tien hang o total_price, phi giao shop thu o partner_fee, tien
	khach da tra o prepaid. Khong tin mot truong duy nhat vi Pancake doi ten
	truong giua cac ban - do lan luot roi lay cai co that.
	"""
	tong = int(o.get("total_price") or 0)
	phi = int(o.get("partner_fee") or 0) or int(o.get("shipping_fee") or 0)
	da = int(o.get("prepaid") or 0)
	return max(0, tong + phi - da), tong, phi, da


def _ma_noi_dung(ma_don):
	"""Noi dung chuyen khoan. Chi chu va so - dau tieng Viet lam ngan hang cat."""
	return "VGB" + re.sub(r"[^0-9A-Za-z]", "", str(ma_don))


def _qr(c, so_tien, noi_dung):
	bin_nh = (c.get("ngan_hang_bin") or "").strip()
	stk = (c.get("ngan_hang_stk") or "").strip()
	ten = (c.get("ngan_hang_ten") or "").strip()
	if not (bin_nh and stk):
		return ""
	from urllib.parse import quote

	return "%s/%s-%s-compact2.png?amount=%s&addInfo=%s&accountName=%s" % (
		VIETQR_ANH,
		bin_nh,
		stk,
		int(so_tien or 0),
		quote(noi_dung),
		quote(ten),
	)


def _link(c, ma_bam):
	goc = (c.get("trang_thanh_toan") or "").strip().rstrip("/")
	if not goc:
		goc = "https://order.thevagabondpatisserie.com/tt"
	return "%s?m=%s" % (goc, ma_bam)


@frappe.whitelist()
def tao_va_gui(ma_don, kenh="zalo", sdt=None):
	"""Sales bam nut: tao yeu cau thanh toan cho mot don Pancake roi gui cho khach.

	kenh: "zalo" (mac dinh), "whatsapp", hoac "ca_hai".
	sdt:  de trong thi lay so tren don.
	"""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings")

	o = _don_pancake(c, k, ma_don)
	if not o:
		frappe.throw("Không tìm thấy đơn %s bên Pancake" % ma_don)

	con, tong, phi, da = _con_phai_tra(o)
	if con <= 0:
		frappe.throw("Đơn %s không còn khoản nào phải thu" % ma_don)

	sdt_don = (o.get("shipping_address") or {}).get("phone_number") or o.get("bill_phone_number")
	s84 = _sdt84(sdt or sdt_don)
	if not re.match(r"^84\d{9}$", s84):
		frappe.throw("Đơn %s không có số điện thoại hợp lệ để gửi" % ma_don)

	ten_khach = (o.get("shipping_address") or {}).get("full_name") or o.get("bill_full_name") or ""
	noi_dung = _ma_noi_dung(ma_don)

	# Mot don chi giu MOT yeu cau con hieu luc, bam hai lan khong sinh hai link.
	cu = frappe.get_all(
		"Vagabond Yeu Cau TT",
		filters={"ma_don": str(ma_don), "tinh_trang": "Cho thanh toan"},
		fields=["name", "ma_bam", "so_tien"],
		limit_page_length=1,
	)
	if cu and int(cu[0]["so_tien"] or 0) == con:
		doc = frappe.get_doc("Vagabond Yeu Cau TT", cu[0]["name"])
	else:
		for x in cu:
			frappe.db.set_value("Vagabond Yeu Cau TT", x["name"], "tinh_trang", "Da huy")
		doc = frappe.new_doc("Vagabond Yeu Cau TT")
		doc.ma_don = str(ma_don)
		doc.ma_bam = secrets.token_urlsafe(16)
		doc.sdt = s84
		doc.ten_khach = ten_khach
		doc.so_tien = con
		doc.tien_hang = tong
		doc.phi_giao = phi
		doc.da_tra = da
		doc.noi_dung_ck = noi_dung
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
				"so_tien": _vnd(con),
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
			[str(ma_don), _vnd(con) + " d", link],
		)
		ket["whatsapp"] = {"ok": 1 if xong else 0, "loi": loi}

	gui_duoc = any(v.get("ok") for v in ket.values())
	if gui_duoc:
		doc.db_set("gui_luc", now_datetime())
		frappe.db.commit()

	return {
		"ok": 1 if gui_duoc else 0,
		"link": link,
		"so_tien": con,
		"noi_dung_ck": noi_dung,
		"kenh": ket,
	}


@frappe.whitelist(allow_guest=True)
def xem(m=None):
	"""Trang thanh toan cua khach doc o day. Khong tra bat ky thong tin nao thua."""
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
			"tinh_trang",
		],
		limit_page_length=1,
	)
	if not ds:
		return {"ok": 0, "ly_do": "khong_thay"}
	d = ds[0]
	c = cfg()
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
			"stk": (c.get("ngan_hang_stk") or "").strip(),
			"chu_tk": (c.get("ngan_hang_ten") or "").strip(),
		},
		"qr": _qr(c, d["so_tien"], d["noi_dung_ck"]),
	}


@frappe.whitelist()
def danh_dau_da_tra(ma_don=None, ghi_chu=None):
	"""Ke toan xac nhan da nhan tien. Tam thoi lam tay, sau noi SePay vao day."""
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
		fields=["name", "ma_don", "ten_khach", "sdt", "so_tien", "noi_dung_ck", "gui_luc", "creation"],
		order_by="creation desc",
		limit_page_length=int(gioi_han or 100),
	)
