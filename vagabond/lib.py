"""Tien ich dung chung: doc cau hinh, doc khoa, nho ket qua."""

import re

import frappe

GOONG = "https://rsapi.goong.io"
VIETQR = "https://api.vietqr.io/v2/business"
PANCAKE = "https://pos.pages.fm/api/v1"
TIMEOUT = 12


def cfg():
	return frappe.get_cached_doc("Vagabond Settings")


def cfg_o(ten):
	"""Doc MOT o Cai dat, di thang xuong bang Singles.

	Vi sao khong doc qua cfg(): duong do di qua danh sach truong cua doctype,
	con phep GHI (`frappe.db.set_single_value`) thi khong. O nao chua duoc
	dung thi ghi van vao, doc lai luon rong, va man Cai dat bao "da luu" xong
	quay lai thay trang - khong mot dong loi nao.

	Anh Viet 03/09/2026 gap dung canh do voi tai khoan nhan tien cua Tran Cao
	Van, lan thu hai trong ba tuan. Ra soat thi con bon o nua cung canh: mau
	in quay, danh sach may in, can tem, nhip Pancake.

	Doc thang thi cau hinh cu nam san duoi bang Singles tro lai duoc ngay,
	khong phai khai lai. Con o thi van phai dung - xem `o_cai_dat.py` va ca
	kiem `thu_o_cai_dat.py`.
	"""
	try:
		return frappe.db.get_single_value("Vagabond Settings", ten) or ""
	except Exception:
		try:
			return cfg().get(ten) or ""
		except Exception:
			return ""


def key(doc, field):
	"""Doc truong Password ra dang chu."""
	val = doc.get_password(field, raise_exception=False)
	return (val or "").strip()


# Khoa API cua Pancake, Goong, SePay deu di trong DUONG DAN chu khong phai
# trong dau thu. Nen moi thong diep loi cua thu vien mang deu cong nguyen ca
# duong dan, ke ca khoa.
#
# Ngay 26/08/2026 Sales chup man hinh Kiem banh gui len: khoa API Pancake
# cua tiem nam chan giua man hinh, chu do, ai dung canh cung doc duoc. Ham
# nay quet moi chuoi TRUOC khi no co co hoi di ra man hinh hay vao nhat ky.
_MAU_KHOA = re.compile(r"(?i)(api_key|access_token|token|key)=[^&\s\"']+")


def giau_khoa(chuoi):
	"""Bo khoa API ra khoi mot thong diep truoc khi cho ai do doc no."""
	return _MAU_KHOA.sub(r"\1=***", str(chuoi or ""))


# ---------------------------------------------------------------------------
# So dien thoai - MOT cach chuan hoa duy nhat cho ca he (anh Viet 12/08/2026).
#
# Truoc day moi mo dun tu viet mot ham: ma_khach._so tra 9 chu so bo so 0,
# don_hang._so chi loc chu so, nhap_khach.sdt_chuan tra 0xxxxxxxxx, con Zalo
# thi can 84xxxxxxxxx. Bon cach hieu khac nhau cho cung mot so nghia la tra
# cuu khong khop nhau: cung mot nguoi vao he hai lan thanh hai khach.
#
# Nay mot noi. Dang CAT TRONG CO SO DU LIEU luon la 0xxxxxxxxx; dang gui di
# thi doi ngay luc gui.

# Dau so di dong Viet Nam that su dang phat hanh, hai chu so sau so 0.
#
# Phai liet ke tung dau so chu khong chi kiem "bat dau bang 3 5 7 8 9":
# trong tep Fabi co so 0300136435, dau so 030 khong ton tai o Viet Nam (day
# la ma so thue bi go nham vao o so dien thoai). Kiem lo tay thi de ra mot
# khach ma ca doi khong nhan duoc tin nhan nao.
DAU_SO = frozenset(
	"32 33 34 35 36 37 38 39 52 55 56 58 59 70 76 77 78 79 "
	"81 82 83 84 85 86 87 88 89 90 91 92 93 94 96 97 98 99".split()
)


def _chin_so(s):
	"""Chin chu so cuoi cua mot so di dong, hoac rong neu khong doc duoc.

	Nhan moi kieu nguoi ta go vao: 0901557462, 84901557462, +84 901 557 462,
	901557462, "0901.557.462", "0901 557 462 (Mr Nam)".
	"""
	x = "".join(ch for ch in str(s or "") if ch.isdigit())
	# Chi cat ma quoc gia khi phan con lai du dai. "0084..." va cac so bat
	# dau bang 84 nhung ngan thi khong phai ma vung.
	if x.startswith("0084"):
		x = x[4:]
	elif x.startswith("84") and len(x) > 10:
		x = x[2:]
	x = x.lstrip("0")
	return x if len(x) == 9 and x[:2] in DAU_SO else ""


def sdt(s):
	"""So di dong ve dang 0xxxxxxxxx. Doc khong ra thi tra RONG.

	Tra rong chu KHONG doan bua: mot so sai mot chu so la ca doi khach do
	khong nhan duoc tin nhan nao, ma khong ai biet vi sao.
	"""
	x = _chin_so(s)
	return "0" + x if x else ""


def sdt84(s):
	"""Dang 84xxxxxxxxx - Zalo ZNS va vai cong khac doi dang nay."""
	x = _chin_so(s)
	return "84" + x if x else ""


def sdt_so(s):
	"""Chin chu so tran, khong co so 0 dau - dung de so sanh va tra cuu."""
	return _chin_so(s)


def cache_get(k):
	return frappe.cache().get_value(k)


def cache_set(k, val, ttl):
	frappe.cache().set_value(k, val, expires_in_sec=ttl)


# ---------------------------------------------------------------------------
# Anh xem truoc (og:image) tach theo ten mien.
#
# Ca hai ten mien order.* va app.* deu tro vao cung mot site, va khach chua
# dang nhap mo "/" thi Frappe deu tra ve trang dat banh. Nghia la mac dinh hai
# ten mien dung chung mot anh xem truoc, ma anh do lai ghi "ORDER.THEVAGABOND
# PATISSERIE.COM" - gui link app cho nhan vien trong Lark, Zalo thi nhin nham.
#
# Hook update_website_context chay cho moi trang web, doc ten mien tu request
# roi doi bo the og khi ten mien bat dau bang "app.". Trang order giu nguyen.
# ---------------------------------------------------------------------------

OG_APP_ANH = "/files/og-vagabond-app.jpg"
OG_APP_TITLE = "The Vagabond Pâtisserie"
OG_APP_MOTA = "Ứng dụng vận hành nội bộ: bếp, kho, vận đơn, mua hàng."


def og_theo_ten_mien(context=None):
	"""Doi anh xem truoc khi mo bang ten mien app.*"""
	if context is None:
		return context
	try:
		host = (frappe.local.request.host or "").split(":")[0].lower()
	except Exception:
		return context
	if not host.startswith("app."):
		return context

	anh = "https://" + host + OG_APP_ANH
	tags = context.get("metatags") or {}
	tags["og:image"] = anh
	tags["og:image:width"] = "1200"
	tags["og:image:height"] = "630"
	tags["twitter:image"] = anh
	tags["twitter:card"] = "summary_large_image"
	tags["og:title"] = OG_APP_TITLE
	tags["title"] = OG_APP_TITLE
	tags["og:description"] = OG_APP_MOTA
	tags["description"] = OG_APP_MOTA
	context["metatags"] = tags
	context["meta_image"] = anh
	context["meta_title"] = OG_APP_TITLE
	context["meta_description"] = OG_APP_MOTA
	return context
