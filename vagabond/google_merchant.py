"""Đưa bánh nổi bật và bánh theo mùa lên Google (v672, anh Việt duyệt 18/11/2026).

Google Merchant Center đọc tệp /google-merchant.xml theo lịch (nguồn dữ liệu
"tìm nạp theo lịch"), bánh hiện miễn phí trên Google Tìm kiếm, Google Mua sắm,
Google Maps và Google Business Profile của tiệm. Mỗi bánh có trang riêng
/mon/<mã hàng> do máy chủ dựng sẵn (Google đọc giá và tình trạng còn hàng trên
trang đích, trang /banh là ứng dụng một trang nên Google không đọc chắc được).

Chỉ đưa hai nhóm (anh Việt: "đồng bộ những sản phẩm nào highlight, seasonal
thôi để tăng nhận diện"):
  - Đặc biệt tuần này: các món của đợt khách đang thấy trên trang /banh.
  - Theo mùa: hàng của mùa vụ đang chạy (mua_vu.hang_theo_mua).

MỘT NGUỒN: tệp cho Google và trang /mon/<mã> cùng gọi `mon_dua_google()`, nên
giá và tình trạng trên hai nơi không bao giờ lệch nhau (Google gỡ sản phẩm khi
giá trên trang đích khác giá trong tệp).

Phần dựng XML, dựng trang và gộp danh sách là THUẦN để kiểm không cần site.
"""
import json
from urllib.parse import quote
from xml.sax.saxutils import escape

GOC = "https://thevagabondpatisserie.com"
THUONG_HIEU = "The Vagabond Pâtisserie"
# Mã danh mục sản phẩm Google: Food, Beverages & Tobacco > Food Items > Bakery.
DANH_MUC_GG = "1876"
ANH_NEN = "/assets/vagabond/web_order/anh-bia.png"
NGUON_DAC_BIET, NGUON_MUA = "dac_biet", "theo_mua"
TEN_NGUON = {NGUON_DAC_BIET: "Đặc biệt tuần này", NGUON_MUA: "Theo mùa"}
CON, HET, DAT_TRUOC = "in_stock", "out_of_stock", "preorder"
CHU_CON = {CON: "Đang nhận đặt", HET: "Đã hết đợt này", DAT_TRUOC: "Sắp mở đặt"}
TRAN_TEN, TRAN_MO_TA = 150, 5000
KHOA_DEM = "vgb_google_merchant"
SONG_DEM_GIAY = 600
MUI_GIO = "+07:00"


# ------------------------------------------------------------------ THUẦN

def anh_tuyet_doi(u, goc=GOC):
	"""THUẦN: đường dẫn ảnh đầy đủ https, hoặc "" khi không dùng được cho Google
	(rỗng, ảnh riêng tư, ảnh nền thương hiệu thay cho ảnh bánh)."""
	u = str(u or "").strip()
	if not u or u.startswith("/private") or "/private/files/" in u or u.split("?")[0].endswith(ANH_NEN):
		return ""
	if u.startswith("//"):
		u = "https:" + u
	elif u.startswith("/"):
		u = goc.rstrip("/") + u
	return u if u.startswith("https://") else ""


def mo_ta_mac_dinh(ten):
	return "%s, bánh của %s, 9 Trần Cao Vân, Quận 1, TP. Hồ Chí Minh. Đặt online, giao tận nơi hoặc nhận tại tiệm." % (ten, THUONG_HIEU)


def gop_mon(nhom, goc=GOC):
	"""THUẦN: gộp các nhóm bánh thành danh sách đưa Google.

	nhom: các danh sách [{"ma", "ten", "mo_ta", "anh", "gia", "con", "tu_luc", "nguon"}],
	nhóm đứng trước thắng khi trùng mã. Bỏ bánh không có giá, không có ảnh thật
	(Google từ chối ảnh nền), không có tên."""
	ra, da = [], set()
	for ds in nhom or []:
		for m in ds or []:
			m = m or {}
			ma = str(m.get("ma") or "").strip()
			ten = " ".join(str(m.get("ten") or "").split())[:TRAN_TEN]
			try:
				gia = int(float(m.get("gia") or 0))
			except (TypeError, ValueError):
				gia = 0
			anh = anh_tuyet_doi(m.get("anh"), goc)
			if not ma or ma in da or not ten or gia <= 0 or not anh:
				continue
			con = m.get("con") if m.get("con") in CHU_CON else CON
			tu_luc = str(m.get("tu_luc") or "")[:16]
			if con == DAT_TRUOC and not tu_luc:
				con = HET
			da.add(ma)
			ra.append({"ma": ma, "ten": ten, "mo_ta": (str(m.get("mo_ta") or "").strip() or mo_ta_mac_dinh(ten))[:TRAN_MO_TA],
				"anh": anh, "gia": gia, "con": con, "tu_luc": tu_luc if con == DAT_TRUOC else "",
				"nguon": m.get("nguon") or NGUON_MUA})
	return ra


def duong_mon(ma, goc=GOC):
	return goc.rstrip("/") + "/mon/" + quote(str(ma), safe="")


def luc_gg(luc):
	"""THUẦN: "YYYY-MM-DDTHH:MM" giờ Việt Nam thành dạng ISO 8601 có múi giờ."""
	luc = str(luc or "")[:16]
	return luc + MUI_GIO if len(luc) == 16 else ""


def xml_tep(ds, goc=GOC):
	"""THUẦN: tệp RSS 2.0 có không gian tên g: theo đặc tả dữ liệu sản phẩm của Google."""
	e = lambda s: escape(str(s if s is not None else ""))
	dong = ['<?xml version="1.0" encoding="UTF-8"?>',
		'<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">', "<channel>",
		"<title>%s</title>" % e(THUONG_HIEU), "<link>%s</link>" % e(goc.rstrip("/") + "/banh"),
		"<description>%s</description>" % e("Bánh đặc biệt tuần này và bánh theo mùa của " + THUONG_HIEU)]
	for m in ds or []:
		dong.append("<item>")
		dong.append("<g:id>%s</g:id>" % e(m["ma"]))
		dong.append("<title>%s</title>" % e(m["ten"]))
		dong.append("<description>%s</description>" % e(m["mo_ta"]))
		dong.append("<link>%s</link>" % e(duong_mon(m["ma"], goc)))
		dong.append("<g:image_link>%s</g:image_link>" % e(m["anh"]))
		dong.append("<g:availability>%s</g:availability>" % e(m["con"]))
		if m["con"] == DAT_TRUOC:
			dong.append("<g:availability_date>%s</g:availability_date>" % e(luc_gg(m["tu_luc"])))
		dong.append("<g:price>%d VND</g:price>" % m["gia"])
		dong.append("<g:brand>%s</g:brand>" % e(THUONG_HIEU))
		dong.append("<g:condition>new</g:condition>")
		dong.append("<g:identifier_exists>no</g:identifier_exists>")
		dong.append("<g:google_product_category>%s</g:google_product_category>" % DANH_MUC_GG)
		dong.append("<g:custom_label_0>%s</g:custom_label_0>" % e(m["nguon"]))
		dong.append("</item>")
	dong += ["</channel>", "</rss>"]
	return "\n".join(dong) + "\n"


def con_theo_suat(con_dot, toi_da, da_dat):
	"""THUẦN: tình trạng một bánh của đợt Đặc biệt. Đợt đang mở mà bánh đã hết suất
	(số tối đa trừ số đã đặt còn 0) thì hết, đúng như trang đặt bánh khoá món đó (Codex
	#587). Để trống số tối đa là không giới hạn."""
	if con_dot != CON or not str(toi_da or "").strip():
		return con_dot
	try:
		return CON if int(toi_da) - int(da_dat or 0) > 0 else HET
	except (TypeError, ValueError):
		return con_dot


def chu_gia(gia):
	return "{:,}".format(int(gia)).replace(",", ".") + " ₫"


def json_ld(m, goc=GOC):
	"""THUẦN: dữ liệu có cấu trúc Product cho trang /mon/<mã> (Google đối chiếu với tệp)."""
	offer = {"@type": "Offer", "price": str(m["gia"]), "priceCurrency": "VND",
		"availability": "https://schema.org/" + {CON: "InStock", HET: "OutOfStock", DAT_TRUOC: "PreOrder"}[m["con"]],
		"url": duong_mon(m["ma"], goc), "itemCondition": "https://schema.org/NewCondition"}
	if m["con"] == DAT_TRUOC and m.get("tu_luc"):
		offer["availabilityStarts"] = luc_gg(m["tu_luc"])
	d = {"@context": "https://schema.org", "@type": "Product", "sku": m["ma"], "name": m["ten"],
		"description": m["mo_ta"], "image": [m["anh"]], "brand": {"@type": "Brand", "name": THUONG_HIEU},
		"offers": offer}
	# Chặn "</script>" trong chữ Marketing gõ làm gãy thẻ script.
	return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


def chu_tinh_trang(m):
	if m["con"] == DAT_TRUOC and m.get("tu_luc"):
		t = m["tu_luc"]
		return "Mở đặt từ %s:%s ngày %s/%s" % (t[11:13], t[14:16], t[8:10], t[5:7])
	return CHU_CON[m["con"]]


def tim(ds, ma):
	ma = str(ma or "").strip()
	return next((m for m in ds or [] if m["ma"] == ma), None)


# --------------------------------------------------------- CHẠM HỆ THỐNG

def _noi_dung_ma():
	"""{mã: {"ten", "mo_ta"}} Marketing đã sửa ở mục Trang từng bánh của biên tập web."""
	try:
		from vagabond import noi_dung_web
		return (noi_dung_web._ban_cong_khai() or {}).get("san_pham") or {}
	except Exception:
		return {}


def _ap_noi_dung(m, nd):
	x = nd.get(m["ma"]) or {}
	if str(x.get("ten") or "").strip():
		m["ten"] = str(x["ten"]).strip()
	if str(x.get("mo_ta") or "").strip():
		m["mo_ta"] = str(x["mo_ta"]).strip()
	return m


def _dac_biet():
	"""Các size của từng món trong đợt Đặc biệt tuần này khách đang thấy."""
	import frappe

	from vagabond import banh_web, dac_biet_tuan as dbt
	from vagabond.kiem_banh import _tach_ten_size

	dot = dbt.dot_cong_khai()
	if not dot:
		return []
	tt = dbt.trang_thai(dot, dbt.luc_vn())
	con = {"mo": CON, "chua_mo": DAT_TRUOC}.get(tt, HET)
	khoa = [m["khoa"] for m in dot.get("mon_dt") or []]
	the = {x.khoa: x for x in frappe.get_all(banh_web.DT, filters={"khoa": ["in", khoa]},
		fields=["khoa", "ten", "trang_thai", "anh", "mo_ta", "ma_hang"], limit_page_length=0, ignore_permissions=True)} if khoa else {}
	# Số đã đặt từng bánh: cùng hàm trang đặt bánh dùng để khoá món hết suất (MỘT nguồn).
	dat = dbt.da_dat(dot, dbt.ma_theo_khoa(dot)) if con == CON else {}
	ma_all = [ma for x in the.values() for ma in banh_web.tach_dong(x.ma_hang)]
	it = {x.item_code: x for x in frappe.get_all("Item", filters={"item_code": ["in", ma_all]},
		fields=["item_code", "item_name", "standard_rate", "disabled", "is_sales_item"], limit_page_length=0,
		ignore_permissions=True)} if ma_all else {}
	ra = []
	for m in dot.get("mon_dt") or []:
		x = the.get(m["khoa"])
		if not x or not banh_web.hien_duoc(x):
			continue
		anh = (banh_web.doc_anh(x.anh) or [{}])[0].get("url") or m.get("anh")
		con_mon = con_theo_suat(con, m.get("toi_da"), dat.get(m["khoa"]))
		for ma in banh_web.tach_dong(x.ma_hang):
			i = it.get(ma)
			if not i or i.disabled or not i.is_sales_item:
				continue
			cm = _tach_ten_size(i.item_name)[1]
			ra.append({"ma": ma, "ten": ("%s %dcm" % (x.ten, cm)) if cm else x.ten, "mo_ta": m.get("mo_ta") or x.mo_ta or "",
				"anh": m.get("anh") or anh, "gia": i.standard_rate, "con": con_mon,
				"tu_luc": dot.get("mo_don") if con == DAT_TRUOC else "", "nguon": NGUON_DAC_BIET})
	return ra


def _theo_mua():
	from vagabond.mua_vu import hang_theo_mua

	return [{"ma": m.get("ma"), "ten": m.get("ten"), "mo_ta": m.get("ruot") or "", "anh": m.get("anh"),
		"gia": m.get("gia"), "con": HET if m.get("het") else CON, "nguon": NGUON_MUA}
		for m in (hang_theo_mua() or {}).get("mon") or []]


def mon_dua_google(lam_moi=False):
	"""MỘT NGUỒN cho tệp /google-merchant.xml và trang /mon/<mã>. Nhớ 10 phút vì
	hàng theo mùa đọc danh mục Pancake. Một nhóm lỗi không làm mất nhóm kia."""
	import frappe

	if not lam_moi:
		try:
			c = frappe.cache().get_value(KHOA_DEM)
			if c is not None:
				return c
		except Exception:
			pass
	nhom = []
	for ham, ten in ((_dac_biet, "Đặc biệt tuần này"), (_theo_mua, "Theo mùa")):
		try:
			nhom.append(ham())
		except Exception:
			frappe.log_error(title="Google Merchant: không đọc được nhóm %s" % ten, message=frappe.get_traceback())
			nhom.append([])
	nd = _noi_dung_ma()
	ra = gop_mon([[_ap_noi_dung(dict(m), nd) for m in ds] for ds in nhom])
	try:
		frappe.cache().set_value(KHOA_DEM, ra, expires_in_sec=SONG_DEM_GIAY)
	except Exception:
		pass
	return ra
