"""v644: ảnh, mô tả và tầng hương vị của bánh trên web quản ở MỘT nơi.

Vì sao có tệp này
-----------------
Anh Việt 07/11/2026 gửi hai ảnh chụp trang bánh trên điện thoại. Very Berry
hiện 4 ảnh giống hệt nhau: bánh có 3 size, mỗi size được tải cùng một tấm ảnh
vào hồ sơ món ERP (3 tệp khác tên), cộng thêm bản của chính tấm đó trên
Pancake; `anh_web.chon_anh` gom ảnh của từng size rồi chỉ loại trùng theo
đường dẫn. Ảnh và mô tả web ghép từ ba nơi (hồ sơ món, Pancake, chữ riêng
từng mã trong trình biên tập) nên không ai biết sửa ở đâu thì khách thấy.

Luồng anh duyệt cùng ngày (mẫu mau-anh-banh-web.jpg):
  ERP tạo mã -> Đồng bộ Pancake -> nút "Đưa lên web" (tệp này, dua_len_web)
  -> Marketing thêm ảnh, mô tả, tầng hương vị ở trình biên tập web, thẻ Bánh
  -> bật "Hiện trên web" thì khách mới thấy.
Hai điều chỉnh em đề xuất, anh đồng ý: bộ ảnh gắn theo BÁNH (mọi size dùng
chung, khoá là tên bánh không size, đúng khoá web đang gom size), và chống
trùng theo NỘI DUNG ảnh (băm hình dHash), không theo tên tệp.
Anh chọn: bánh chưa có ảnh thì ẨN với khách tới khi Marketing bật; mô tả và
tầng hương vị chuyển hẳn sang đây (Pancake không còn đổi chữ trên web).

ERP vẫn là nguồn của mã, size, giá, tồn, bật tắt bán web; tệp này chỉ quyết
bánh nào khách được thấy và khách thấy ảnh, chữ gì.

Chưa có bản ghi nào (trước lần gieo đầu sau deploy) thì web chạy đúng đường
cũ, không ẩn bánh nào (so_ghi trả None). Lần gieo chép bộ ảnh đang hiện của
từng bánh, gộp ảnh giống nhau, nên không bánh nào mất ảnh hay biến mất.

Phép THUẦN ở trên, phần chạm Frappe ở dưới.
"""

import json
import re
import unicodedata

import frappe

from vagabond.anh_web import ANH_NEN, SO_ANH_TOI_DA, anh_cong_khai

DT = "Vagabond Banh Web"
CHO_ANH, DANG_HIEN, DA_AN = "Chờ ảnh", "Đang hiện", "Đã ẩn"
TRANG_THAI = (CHO_ANH, DANG_HIEN, DA_AN)
# Hai ảnh lệch không quá chừng này bit trên 64 bit dHash là cùng một tấm (khác
# cỡ, khác nén JPG/WebP như bản Pancake của Very Berry).
NGUONG_GIONG = 6
SO_TANG_TOI_DA = 12
CAU_CAN_ANH = "Thêm ít nhất một ảnh trước khi bật Hiện trên web."


# ------------------------------------------------------------------ THUẦN

def khoa_banh(ten):
	"""THUẦN: khoá của một bánh = tên không size, viết thường, gọn khoảng trắng.
	Cùng cách web gom size (kiem_banh: goc.lower())."""
	t = unicodedata.normalize("NFC", str(ten or ""))
	return " ".join(t.lower().split())[:140]


def tach_dong(s, toi_da=None):
	"""THUẦN: các dòng có chữ của một ô nhiều dòng."""
	ds = [d.strip() for d in str(s or "").replace("\r", "").split("\n") if d.strip()]
	return ds[:toi_da] if toi_da else ds


def doc_anh(s):
	"""THUẦN: danh sách ảnh lưu trong bản ghi ([{url, bam}]), rỗng khi hỏng."""
	if isinstance(s, (list, tuple)):
		ds = s
	else:
		try:
			ds = json.loads(s or "[]")
		except (TypeError, ValueError):
			return []
	ra = []
	for x in ds if isinstance(ds, list) else []:
		if isinstance(x, str):
			x = {"url": x}
		if not isinstance(x, dict):
			continue
		u = anh_cong_khai(x.get("url"))
		if u:
			ra.append({"url": u, "bam": str(x.get("bam") or "")})
	return ra


def giong(b1, b2, nguong=NGUONG_GIONG):
	"""THUẦN: hai mã băm hình (16 ký tự hex) là cùng một tấm ảnh."""
	try:
		return bin(int(b1, 16) ^ int(b2, 16)).count("1") <= nguong
	except (TypeError, ValueError):
		return False


def tim_giong(bam, ds):
	"""THUẦN: ảnh trong ds giống tấm có mã băm `bam`, hoặc None."""
	if not bam:
		return None
	return next((x for x in ds if x.get("bam") and giong(bam, x["bam"])), None)


def gop_trung(ds):
	"""THUẦN: bỏ ảnh trùng đường dẫn hoặc giống nội dung, giữ tấm đứng trước,
	tối đa SO_ANH_TOI_DA tấm."""
	ra = []
	for x in doc_anh(ds):
		if any(y["url"] == x["url"] for y in ra) or tim_giong(x["bam"], ra):
			continue
		ra.append(x)
	return ra[:SO_ANH_TOI_DA]


def kiem_luu(trang_thai, anh):
	"""THUẦN: trạng thái hợp lệ cho bộ ảnh này, hoặc ném ValueError có câu cho người dùng."""
	if trang_thai not in TRANG_THAI:
		raise ValueError("Trạng thái không hợp lệ. Tải lại thẻ Bánh.")
	if trang_thai == DANG_HIEN and not doc_anh(anh):
		raise ValueError(CAU_CAN_ANH)
	return trang_thai


def hien_duoc(ban_ghi):
	"""THUẦN: khách được thấy bánh này: Đang hiện và có ít nhất một ảnh."""
	return bool(ban_ghi) and ban_ghi.get("trang_thai") == DANG_HIEN and bool(doc_anh(ban_ghi.get("anh")))


def ap_nhom(ds_nhom, so_ghi):
	"""THUẦN: trả các nhóm bánh khách được thấy, đã mang ảnh, mô tả, tầng hương
	vị của bản ghi web. Nhóm chưa có bản ghi, Chờ ảnh, Đã ẩn hay không ảnh bị
	bỏ (anh Việt 07/11/2026: ẩn tới khi Marketing bật). Khoá riêng _anh_erp,
	_anh_dong của từng size luôn bị gỡ trước khi trả cho khách."""
	ra = []
	for g in ds_nhom or []:
		for s in g.get("sizes") or []:
			s.pop("_anh_erp", None)
			s.pop("_anh_dong", None)
		bg = (so_ghi or {}).get(khoa_banh(g.get("ten")))
		if not hien_duoc(bg):
			continue
		anhs = [x["url"] for x in doc_anh(bg.get("anh"))][:SO_ANH_TOI_DA]
		dong = tach_dong(bg.get("mo_ta"))
		g["anh"], g["anhs"] = anhs[0], anhs
		g["mo_ta"] = " ".join(dong)
		g["tang"] = tach_dong(bg.get("tang"), SO_TANG_TOI_DA)
		g["tu_web"] = 1
		ra.append(g)
	return ra


def chu_nhac(ds_ten):
	"""THUẦN: dòng tin nhắc Marketing các bánh còn Chờ ảnh."""
	ds = [str(t) for t in ds_ten if str(t or "").strip()]
	if not ds:
		return []
	dau = ds[:8]
	return ["Bánh chờ ảnh: " + ", ".join(dau) + (" và %d bánh khác" % (len(ds) - 8) if len(ds) > 8 else "") + ".",
		"Mở trình biên tập web, thẻ Bánh: thêm ảnh rồi bật Hiện trên web. Khách chưa thấy các bánh này."]


# --------------------------------------------------------------- băm hình

def bam_hinh(noi_dung):
	"""dHash 64 bit (16 ký tự hex) của một ảnh, rỗng khi không đọc được."""
	try:
		from io import BytesIO

		from PIL import Image

		with Image.open(BytesIO(noi_dung)) as a:
			x = a.convert("L").resize((9, 8))
			p = list(x.getdata())
		bit = 0
		for h in range(8):
			for c in range(8):
				bit = (bit << 1) | (1 if p[h * 9 + c] > p[h * 9 + c + 1] else 0)
		return "%016x" % bit
	except Exception:
		return ""


def _byte_anh(url):
	"""Đọc byte của một ảnh: tệp công khai của site đọc thẳng trên đĩa, ảnh
	ngoài (Pancake) tải về có giới hạn thời gian và cỡ."""
	u = anh_cong_khai(url)
	if not u:
		return b""
	try:
		if u.startswith("/files/"):
			import os
			from urllib.parse import unquote

			p = frappe.get_site_path("public", "files", unquote(u[len("/files/"):].split("?")[0]))
			if os.path.isfile(p) and os.path.getsize(p) <= 15 * 1024 * 1024:
				with open(p, "rb") as f:
					return f.read()
			return b""
		if u.startswith("https://"):
			import requests

			r = requests.get(u, timeout=8, stream=True)
			if r.status_code != 200:
				return b""
			noi = r.raw.read(15 * 1024 * 1024 + 1, decode_content=True)
			return b"" if len(noi) > 15 * 1024 * 1024 else noi
	except Exception:
		return b""
	return b""


def bam_url(url):
	return bam_hinh(_byte_anh(url))


# --------------------------------------------------------------- CHẠM HỆ

def _bang_co():
	try:
		return bool(frappe.db.table_exists(DT))
	except Exception:
		return False


CO_GIEO = "vagabond_banh_web_da_gieo"


def dang_dung():
	"""Bảng Bánh trên web đã gieo xong lần đầu (Codex PR #547: dấu riêng, không
	lấy "bảng có thẻ" làm dấu vì người bấm Đưa lên web trước khi việc gieo chạy
	đã tạo một thẻ). Chưa xong thì web chạy đường cũ. Không đọc được dấu thì coi
	như ĐANG dùng: thà ẩn bánh còn hơn hiện bánh Marketing đã ẩn."""
	if not _bang_co():
		return False
	try:
		return bool(frappe.db.get_default(CO_GIEO))
	except Exception:
		frappe.log_error(title="Bánh trên web: không đọc được dấu đã gieo", message=frappe.get_traceback())
		return True


def so_ghi():
	"""{khoá: bản ghi} của mọi bánh, hoặc None khi chưa dùng (bảng chưa có hay
	chưa gieo xong): khi đó web chạy đường cũ, không ẩn bánh nào.

	Codex PR #547: bảng đang dùng mà đọc lỗi thì trả {} (khách không thấy bánh
	nào) chứ không trả None, vì đường cũ bỏ qua mọi quyết định ẩn đã lưu."""
	if not dang_dung():
		return None
	try:
		ds = frappe.get_all(DT, fields=["name", "khoa", "ten", "trang_thai", "anh", "mo_ta", "tang", "ma_hang"],
			limit_page_length=0, ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Bánh trên web: không đọc được bảng", message=frappe.get_traceback())
		return {}
	return {x["khoa"]: x for x in ds or []}


def ap_cho_web(ds_nhom):
	"""Nhóm bánh khách được thấy theo bản ghi web, hoặc None khi chưa dùng."""
	sg = so_ghi()
	if sg is None:
		return None
	return ap_nhom(ds_nhom, sg)


def _ten_khoa_cua_ma(item_code):
	from vagabond.kiem_banh import _tach_ten_size

	x = frappe.db.get_value("Item", item_code, ["item_name", "disabled", "is_sales_item", "standard_rate"], as_dict=True)
	if not x:
		frappe.throw("Không thấy mã %s." % item_code)
	ten = _tach_ten_size(x.item_name or item_code)[0] or (x.item_name or item_code)
	return x, ten, khoa_banh(ten)


def _them_ma(ma_hang, ma):
	ds = tach_dong(ma_hang)
	if ma not in ds:
		ds.append(ma)
	return "\n".join(ds)


def _quyen_dua():
	"""Người được Đồng bộ Pancake (kế toán, thu mua, giám đốc) hoặc Marketing."""
	from vagabond import danh_muc

	if frappe.session.user == "Guest":
		frappe.throw("Cần đăng nhập.", frappe.PermissionError)
	if not (danh_muc._duoc_tao() or {"Marketing", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán, thu mua, giám đốc hoặc Marketing mới đưa bánh lên web được.", frappe.PermissionError)


@frappe.whitelist(methods=["POST"])
def dua_len_web(item_code=None):
	"""Nút "Đưa lên web" ở màn Danh mục sản phẩm (ngay dưới Đồng bộ Pancake).

	Bánh chưa có trên web: tạo thẻ "Chờ ảnh" trong trình biên tập và nhắn
	Zalo nhóm Marketing; khách CHƯA thấy. Bánh đã có (size khác của cùng bánh):
	gắn mã vào đúng thẻ cũ, không tạo thẻ mới."""
	_quyen_dua()
	ma = str(item_code or "").strip()
	if not ma:
		frappe.throw("Thiếu mã hàng.")
	if ma.upper().startswith("BAWS"):
		frappe.throw("Mã bánh sỉ không lên trang đặt bánh lẻ.")
	x, ten, khoa = _ten_khoa_cua_ma(ma)
	if int(x.disabled or 0) or not int(x.is_sales_item or 0):
		frappe.throw("Mã %s đang ngừng dùng hoặc không phải hàng bán, chưa đưa lên web được." % ma)
	if float(x.standard_rate or 0) <= 0:
		frappe.throw("Mã %s chưa có giá bán. Đặt giá ở hồ sơ món rồi đưa lên web." % ma)
	r = frappe.db.sql("select name from `tab%s` where khoa=%%s for update" % DT, (khoa,))
	if r:
		bg = frappe.get_doc(DT, r[0][0])
		bg.ma_hang = _them_ma(bg.ma_hang, ma)
		bg.flags.ignore_permissions = True
		bg.save()
		khach = "khách đang thấy, size mới hiện ngay khi có tồn" if hien_duoc(bg.as_dict()) else "khách chưa thấy, chờ Marketing thêm ảnh và bật"
		return {"khoa": khoa, "ten": bg.ten, "trang_thai": bg.trang_thai, "moi": 0,
			"thong_bao": "%s đã có trên web (%s): %s." % (bg.ten, bg.trang_thai, khach)}
	bg = frappe.get_doc({"doctype": DT, "khoa": khoa, "ten": ten, "trang_thai": CHO_ANH, "ma_hang": ma, "anh": "[]",
		"dua_boi": frappe.session.user, "dua_luc": frappe.utils.now_datetime()})
	bg.insert(ignore_permissions=True)
	_nhac_mot(bg)
	return {"khoa": khoa, "ten": ten, "trang_thai": CHO_ANH, "moi": 1,
		"thong_bao": "Đã tạo thẻ %s trên trình biên tập web và nhắn Marketing thêm ảnh. Khách chưa thấy tới khi Marketing bật Hiện trên web." % ten}


def trang_thai_theo_ma(ds_item):
	"""{mã: trạng thái web của bánh chứa mã} theo tên bánh không size (kể cả size
	chưa gắn vào thẻ). Bảng chưa dùng thì rỗng."""
	from vagabond.kiem_banh import _tach_ten_size

	sg = so_ghi() or {}
	ra = {}
	for x in ds_item or []:
		bg = sg.get(khoa_banh(_tach_ten_size(x.get("item_name") or x.get("name") or "")[0]))
		if bg:
			ra[x.get("name") or x.get("item_code")] = bg["trang_thai"]
	return ra


def _nhac_mot(bg):
	try:
		from vagabond import kenh_zalo

		kenh_zalo.bao("viec", "don_web", "Bánh mới chờ ảnh trên web: %s" % bg.ten, chu_nhac([bg.ten]),
			link="/bien-tap-web", khoa="banh_cho_anh:%s" % bg.khoa, ma_tin="mkt_banh_cho_anh",
			kiem="banh_cho_anh", nguon=bg.name)
	except Exception:
		frappe.log_error(title="Bánh trên web: chưa nhắn được Marketing", message=frappe.get_traceback())


def con_cho_anh(nguon=None):
	"""DIEU_KIEN "banh_cho_anh": còn bánh Chờ ảnh (một bánh cụ thể nếu có nguồn)."""
	f = {"trang_thai": CHO_ANH}
	if nguon:
		f["name"] = nguon
	return bool(frappe.db.count(DT, f))


def nhac_cho_anh():
	"""08:41 mỗi sáng: nhắc Marketing các bánh đã đưa lên web mà còn Chờ ảnh."""
	if not _bang_co():
		return
	ds = frappe.get_all(DT, filters={"trang_thai": CHO_ANH}, fields=["name", "ten"], order_by="dua_luc asc",
		limit_page_length=0, ignore_permissions=True)
	if not ds:
		return
	from vagabond import kenh_zalo

	kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", "%d bánh chờ ảnh trên web" % len(ds), chu_nhac([x.ten for x in ds]),
		link="/bien-tap-web", khoa="banh_cho_anh_ngay:%s" % frappe.utils.nowdate(), ma_tin="mkt_banh_cho_anh",
		kiem="banh_cho_anh")
	frappe.db.sql("update `tab%s` set nhac_luc=%%s where trang_thai=%%s" % DT, (frappe.utils.now_datetime(), CHO_ANH))


# ---------------------------------------------------------- trình biên tập

def _kiem_marketing():
	from vagabond.noi_dung_web import kiem_quyen

	kiem_quyen()


def _the(bg, sizes=None):
	return {"khoa": bg["khoa"], "ten": bg["ten"], "trang_thai": bg["trang_thai"], "anh": doc_anh(bg.get("anh")),
		"mo_ta": bg.get("mo_ta") or "", "tang": bg.get("tang") or "", "ma_hang": tach_dong(bg.get("ma_hang")),
		"sizes": sizes or [], "dua_luc": str(bg.get("dua_luc") or "")}


def _sizes(ds_ma):
	from vagabond.kiem_banh import _tach_ten_size

	if not ds_ma:
		return {}
	it = frappe.get_all("Item", filters={"item_code": ["in", list(ds_ma)]},
		fields=["item_code", "item_name", "standard_rate", "disabled"], limit_page_length=0, ignore_permissions=True)
	ra = {}
	for x in it:
		ra[x.item_code] = {"ma": x.item_code, "cm": _tach_ten_size(x.item_name)[1], "gia": int(x.standard_rate or 0),
			"ngung": int(x.disabled or 0)}
	return ra


@frappe.whitelist()
def ds_bien_tap():
	"""Thẻ Bánh của trình biên tập: mọi bánh đã đưa lên web, Chờ ảnh đứng đầu."""
	_kiem_marketing()
	if not _bang_co():
		return {"banh": [], "dem": {}}
	ds = frappe.get_all(DT, fields=["khoa", "ten", "trang_thai", "anh", "mo_ta", "tang", "ma_hang", "dua_luc"],
		limit_page_length=0, ignore_permissions=True)
	sz = _sizes({m for x in ds for m in tach_dong(x.ma_hang)})
	thu = {CHO_ANH: 0, DANG_HIEN: 1, DA_AN: 2}
	ds.sort(key=lambda x: (thu.get(x.trang_thai, 3), khoa_banh(x.ten)))
	ra = [_the(x, sorted([sz[m] for m in tach_dong(x.ma_hang) if m in sz], key=lambda s: s["cm"] or 999)) for x in ds]
	dem = {t: sum(1 for x in ds if x.trang_thai == t) for t in TRANG_THAI}
	return {"banh": ra, "dem": dem}


def _doc_khoa(khoa):
	r = frappe.db.sql("select name from `tab%s` where khoa=%%s for update" % DT, (str(khoa or ""),))
	if not r:
		frappe.throw("Không thấy bánh này. Tải lại thẻ Bánh.")
	return frappe.get_doc(DT, r[0][0])


@frappe.whitelist(methods=["POST"])
def them_anh(khoa=None, url=None):
	"""Ảnh vừa tải (noi_dung_web.tai_anh) vào bộ ảnh của bánh. Ảnh giống một
	tấm đã có thì không thêm, trả `trung` để màn báo."""
	_kiem_marketing()
	bg = _doc_khoa(khoa)
	ds = doc_anh(bg.anh)
	u = anh_cong_khai(url)
	if not u:
		frappe.throw("Ảnh không hợp lệ. Tải lại ảnh.")
	bam = bam_url(u)
	cu = next((x for x in ds if x["url"] == u), None) or tim_giong(bam, ds)
	if cu:
		return dict(ds_bien_tap(), khoa=khoa, trung=cu["url"])
	if len(ds) >= SO_ANH_TOI_DA:
		frappe.throw("Mỗi bánh tối đa %d ảnh. Bỏ bớt một ảnh, bấm Lưu bánh rồi tải lại." % SO_ANH_TOI_DA)
	ds.append({"url": u, "bam": bam})
	bg.anh = json.dumps(ds, ensure_ascii=False)
	bg.flags.ignore_permissions = True
	bg.save()
	# Codex PR #547: trả đúng ảnh vừa thêm để màn chỉ ghép ảnh đó vào bản đang sửa.
	return dict(ds_bien_tap(), khoa=khoa, trung="", them=u)


@frappe.whitelist(methods=["POST"])
def luu(khoa=None, anh=None, mo_ta="", tang="", trang_thai=None):
	"""Lưu một bánh: thứ tự ảnh (ảnh đầu là ảnh bìa), mô tả, tầng hương vị,
	Hiện trên web. Lưu là khách thấy ngay."""
	_kiem_marketing()
	bg = _doc_khoa(khoa)
	cu = {x["url"]: x for x in doc_anh(bg.anh)}
	moi = []
	for u in doc_anh(json.loads(anh) if isinstance(anh, str) else (anh or [])):
		# Chỉ nhận ảnh đã nằm trong bộ (thêm qua them_anh, có mã băm); đổi thứ tự hay bỏ bớt.
		if u["url"] in cu and u["url"] not in [x["url"] for x in moi]:
			moi.append(cu[u["url"]])
	moi = moi[:SO_ANH_TOI_DA]
	try:
		tt = kiem_luu(trang_thai or bg.trang_thai, moi)
	except ValueError as e:
		frappe.throw(str(e))
	if tt == CHO_ANH and moi:
		tt = DA_AN
	if len(str(mo_ta or "")) > 4000 or len(str(tang or "")) > 4000:
		frappe.throw("Mô tả và tầng hương vị mỗi ô tối đa 4.000 ký tự.")
	bg.anh = json.dumps(moi, ensure_ascii=False)
	bg.mo_ta = str(mo_ta or "").strip()
	bg.tang = "\n".join(tach_dong(tang, SO_TANG_TOI_DA))
	bg.trang_thai = tt if moi else CHO_ANH
	bg.flags.ignore_permissions = True
	bg.save()
	return dict(ds_bien_tap(), khoa=khoa)


def dem_cho_anh():
	try:
		return frappe.db.count(DT, {"trang_thai": CHO_ANH}) if _bang_co() else 0
	except Exception:
		return 0


# ------------------------------------------------------------- gieo lần đầu

def gieo():
	"""after_migrate: chưa có bản ghi nào thì xếp việc gieo chạy nền (cần tải
	ảnh Pancake để băm, không làm chậm migrate). Trong lúc chờ, web chạy đường
	cũ vì so_ghi trả None."""
	try:
		if not _bang_co() or frappe.db.get_default(CO_GIEO):
			return
		frappe.enqueue("vagabond.banh_web.gieo_that", queue="long", timeout=3000, enqueue_after_commit=True,
			job_id="vgb_gieo_banh_web", deduplicate=True)
	except Exception:
		frappe.log_error(title="Bánh trên web: chưa xếp được việc gieo", message=frappe.get_traceback())


def _ma_ung_vien():
	"""Mọi mã bánh ổ lẻ có thể lên web: đang dùng, là hàng bán, có giá, mã BAWC."""
	return frappe.get_all("Item", filters={"item_code": ["like", "BAWC%"], "disabled": 0, "is_sales_item": 1,
		"standard_rate": [">", 0]}, fields=["item_code", "item_name", "image"], limit_page_length=0, ignore_permissions=True)


def _chu_bien_tap():
	"""Chữ riêng từng mã Marketing đã gõ ở mục Nội dung bánh (bản công khai)."""
	try:
		from vagabond.noi_dung_web import _ban_cong_khai

		return (_ban_cong_khai() or {}).get("san_pham") or {}
	except Exception:
		return {}


def nhom_gieo(ds_item, chu_ma):
	"""THUẦN (ngoài _tach_ten_size): gom mã theo bánh như web, kèm chữ riêng."""
	from vagabond.kiem_banh import _tach_ten_size

	nhom, thu_tu = {}, []
	for x in ds_item:
		ten, cm = _tach_ten_size(x.get("item_name") or x["item_code"])
		k = khoa_banh(ten)
		if not k:
			continue
		if k not in nhom:
			nhom[k] = {"ten": ten, "anh": "", "sizes": [], "_chu": {}}
			thu_tu.append(k)
		g = nhom[k]
		g["sizes"].append({"ma": x["item_code"], "cm": cm, "_anh_erp": x.get("image") or "", "_anh_dong": ""})
		c = chu_ma.get(x["item_code"]) or {}
		for t in ("mo_ta", "tang"):
			if not g["_chu"].get(t) and str(c.get(t) or "").strip():
				g["_chu"][t] = str(c[t]).strip()
	return [nhom[k] for k in thu_tu]


def gieo_that():
	"""Chép bộ ảnh và chữ ĐANG hiện của từng bánh vào bảng, gộp ảnh giống nhau.
	Bánh có ảnh: Đang hiện (khách thấy như trước). Không ảnh: Chờ ảnh.

	Codex PR #547: gieo đủ mọi khoá còn thiếu rồi mới đặt dấu đã gieo; thẻ có
	sẵn (người bấm Đưa lên web trước lúc gieo) được giữ, chỉ thẻ còn Chờ ảnh
	chưa có ảnh nào mới nhận bộ ảnh và chữ đang hiện của bánh đó."""
	from vagabond import kiem_banh

	if frappe.db.get_default(CO_GIEO):
		return 0
	ds = nhom_gieo(_ma_ung_vien(), _chu_bien_tap())
	kiem_banh._bo_anh_mo_ta(ds)
	tao = 0
	for g in ds:
		k = khoa_banh(g["ten"])
		anh = gop_trung([{"url": u, "bam": bam_url(u)} for u in (g.get("anhs") or []) if u != ANH_NEN])
		chu = g.get("_chu") or {}
		mo_ta = chu.get("mo_ta") or g.get("mo_ta") or ""
		tang = "\n".join(tach_dong(chu.get("tang") or "\n".join(g.get("tang") or []), SO_TANG_TOI_DA))
		ma = [s["ma"] for s in g["sizes"]]
		ten = frappe.db.get_value(DT, {"khoa": k}, "name")
		if ten:
			bg = frappe.get_doc(DT, ten)
			if bg.trang_thai != CHO_ANH or doc_anh(bg.anh) or not anh:
				continue
			for m in ma:
				bg.ma_hang = _them_ma(bg.ma_hang, m)
			bg.anh = json.dumps(anh, ensure_ascii=False)
			bg.trang_thai = DANG_HIEN
			bg.mo_ta = bg.mo_ta or mo_ta
			bg.tang = bg.tang or tang
			bg.flags.ignore_permissions = True
			bg.save()
			continue
		frappe.get_doc({"doctype": DT, "khoa": k, "ten": g["ten"], "trang_thai": DANG_HIEN if anh else CHO_ANH,
			"ma_hang": "\n".join(ma), "anh": json.dumps(anh, ensure_ascii=False),
			"mo_ta": mo_ta, "tang": tang, "dua_boi": "Gieo lần đầu v644",
			"dua_luc": frappe.utils.now_datetime()}).insert(ignore_permissions=True)
		tao += 1
	frappe.db.set_default(CO_GIEO, "1")
	frappe.db.commit()
	return tao
