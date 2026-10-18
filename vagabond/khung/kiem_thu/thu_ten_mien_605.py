"""v605 (anh Việt 18/10/2026): trang đặt bánh lên tên miền chính, sửa phông tên
bánh có dấu, favicon và dữ liệu cho Google.

- Tên miền: thevagabondpatisserie.com mở trang đặt bánh; order. và www. chuyển
  301 về tên miền chính; đường dẫn WordPress cũ chuyển 301 về /banh. Chỉ khi
  công tắc "Dùng tên miền chính" bật, chỉ GET/HEAD, không đụng /api, /assets...
- LadyRuby: tên có dấu ("Bánh LADYRUBY") bị đổi sang phông hệ thống, lệch với
  các bánh khác. Bỏ luật đó ở cả trang Vue và trang cũ.
- SEO: mô tả, ảnh xem trước lấy từ khối Editor đầu tiên nên ra "Mở các kênh đặt
  hàng" kèm logo Grab. Nay dùng mô tả và ảnh của tiệm, kèm JSON-LD, favicon.

Ca hook before_request gọi hàm THẬT, chỉ thay tầng Frappe và werkzeug bằng bản
giả (máy CI không có werkzeug).
"""
import json
import sys
import types
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
CHINH = "thevagabondpatisserie.com"


def _c(host, duong, pt="GET", hoi="", bat=1):
	from vagabond.ten_mien import chuyen_ten_mien
	return chuyen_ten_mien(host, duong, pt, hoi, bat)


@ca("v605 công tắc tắt: không tên miền nào bị chuyển, order. chạy như trước")
def _tat():
	for h in ("order." + CHINH, CHINH, "www." + CHINH):
		for d in ("/", "/banh", "/shop/"):
			la("tắt %s%s" % (h, d), _c(h, d, bat=0), None)


@ca("v605 order. và www. chuyển 301 về tên miền chính, giữ đường và chuỗi hỏi")
def _order_www():
	la("order /banh", _c("order." + CHINH, "/banh"), ("https://%s/banh" % CHINH, 301))
	la("order giữ utm", _c("order." + CHINH, "/banh", hoi="utm_source=fb&x=1"),
		("https://%s/banh?utm_source=fb&x=1" % CHINH, 301))
	la("order biên nhận", _c("ORDER.%s:443" % CHINH, "/banh/xong/ABC"), ("https://%s/banh/xong/ABC" % CHINH, 301))
	la("order trang chủ", _c("order." + CHINH, "/"), ("https://%s/" % CHINH, 301))
	la("www", _c("www." + CHINH, "/gioi-thieu/"), ("https://%s/gioi-thieu/" % CHINH, 301))
	la("HEAD cũng chuyển", _c("order." + CHINH, "/banh", "HEAD"), ("https://%s/banh" % CHINH, 301))


@ca("v605 chốt an toàn: POST, /api, /assets, /files và tên miền nội bộ không bao giờ bị chuyển")
def _an_toan():
	for d in ("/api/method/vagabond.don_web.tao", "/assets/vagabond/x.js", "/files/a.png", "/private/files/b.pdf",
			"/socket.io/x", "/.well-known/acme-challenge/t", "/backups/x"):
		la("order " + d, _c("order." + CHINH, d), None)
		la("chính " + d, _c(CHINH, d), None)
	la("POST gửi đơn", _c("order." + CHINH, "/banh", "POST"), None)
	la("PUT", _c(CHINH, "/shop/", "PUT"), None)
	for h in ("app." + CHINH, "erp." + CHINH, "vagabond.s.frappe.cloud", "erpnext-qwy-acq.s.frappe.cloud", "localhost:8000", ""):
		for d in ("/", "/shop", "/banh", "/app"):
			la("mien noi bo %s%s" % (h, d), _c(h, d), None)


@ca("v605 tên miền chính: / về /banh (302, giữ utm); đường WordPress cũ 301 về /banh; trang khách đi thẳng")
def _chinh():
	la("trang chủ", _c(CHINH, "/"), ("/banh", 302))
	la("trang chủ giữ utm", _c(CHINH, "/", hoi="utm_campaign=t10"), ("/banh?utm_campaign=t10", 302))
	for d in ("/shop/", "/products/", "/product/very-berry/", "/en/", "/en/product/roman-de-la-rose/",
			"/gioi-thieu/", "/lien-he/", "/tin-tuc", "/2026mooncake/", "/product-category/whole-cake-vi/",
			"/the-vagabond-nhung-nguoi-lam-banh-lang-thang-tim-cai-dep-3/", "/wp-content/uploads/2026/04/a.png",
			"/wp-login.php", "/cart/", "/checkout/", "/my-account/", "/category/news/", "/author/tvp-editor/", "/SHOP/"):
		la("WP " + d, _c(CHINH, d), ("/banh", 301))
	for d in ("/banh", "/banh/xong/T", "/dat-ban", "/thanh-vien", "/xhd", "/tt/x", "/chinh-sach-bao-mat",
			"/login", "/robots.txt", "/sitemap.xml", "/favicon.ico", "/endless", "/enx", "/productx"):
		la("đi thẳng " + d, _c(CHINH, d), None)


@ca("v605 canonical theo công tắc: bật là tên miền chính, tắt là order.")
def _mien():
	from vagabond.ten_mien import mien_cong_khai
	la("bật", mien_cong_khai(1), CHINH)
	la("tắt", mien_cong_khai(0), "order." + CHINH)


class _Req:
	def __init__(self, host, path, method="GET", qs=b""):
		self.host, self.path, self.method, self.query_string = host, path, method, qs


def _chay_hook(req, bat=1, doc_loi=False):
	"""Gọi truoc_request THẬT với frappe và werkzeug giả. Trả (ngoại lệ, số lần đọc Cài đặt)."""
	doc = []

	def gsv(dt, f, cache=False):
		doc.append((dt, f, cache))
		if doc_loi:
			raise RuntimeError("chua migrate")
		return bat

	gia = {
		"frappe": types.SimpleNamespace(local=types.SimpleNamespace(request=req),
			db=types.SimpleNamespace(get_single_value=gsv)),
		"werkzeug": types.ModuleType("werkzeug"),
		"werkzeug.exceptions": types.ModuleType("werkzeug.exceptions"),
		"werkzeug.utils": types.ModuleType("werkzeug.utils"),
	}

	class HTTPException(Exception):
		code = None

	gia["werkzeug.exceptions"].HTTPException = HTTPException
	gia["werkzeug.utils"].redirect = lambda dich, ma: ("REDIRECT", dich, ma)
	cu = {k: sys.modules.get(k) for k in gia}
	sys.modules.update(gia)
	try:
		from vagabond import ten_mien
		try:
			ten_mien.truoc_request()
			return None, doc, HTTPException
		except HTTPException as e:
			return e, doc, HTTPException
	finally:
		for k, v in cu.items():
			if v is None:
				sys.modules.pop(k, None)
			else:
				sys.modules[k] = v


@ca("v605 hook before_request: chuyển thật bằng HTTPException 301, đọc Cài đặt có bộ đệm, chỉ đọc ở tên miền khách")
def _hook():
	e, doc, H = _chay_hook(_Req("order." + CHINH, "/banh", qs=b"utm_source=zalo"))
	dung("ném HTTPException để Frappe trả thẳng response", isinstance(e, H))
	la("mã", e.code, 301)
	la("response", e.get_response({}), ("REDIRECT", "https://%s/banh?utm_source=zalo" % CHINH, 301))
	la("đọc đúng công tắc, có cache", doc, [("Vagabond Settings", "web_ten_mien_chinh", True)])

	e, doc, H = _chay_hook(_Req("app." + CHINH, "/bep"))
	la("miền app: không chuyển", e, None)
	la("miền app: không đọc Cài đặt", doc, [])

	e, doc, H = _chay_hook(_Req(CHINH, "/"))
	la("trang chủ 302", (e.code, e.get_response()), (302, ("REDIRECT", "/banh", 302)))

	e, doc, H = _chay_hook(_Req("order." + CHINH, "/banh"), bat=0)
	la("công tắc tắt", e, None)
	e, doc, H = _chay_hook(_Req("order." + CHINH, "/banh"), doc_loi=True)
	la("đọc Cài đặt lỗi: coi như tắt, không trắng màn", e, None)
	e, doc, H = _chay_hook(None)
	la("không có request", e, None)


@ca("v605 hooks khai before_request đúng một lần, trỏ hàm có thật")
def _khai_hook():
	src = (GOC / "hooks.py").read_text()
	la("một dòng khai", src.count("\nbefore_request ="), 1)
	dung("trỏ truoc_request", 'before_request = ["vagabond.ten_mien.truoc_request"]' in src)
	from vagabond import ten_mien
	dung("hàm có thật", callable(getattr(ten_mien, "truoc_request", None)))


@ca("v605 công tắc tên miền chính trong Cài đặt: Check, mặc định tắt, ngay dưới công tắc trang mới, nói cách tắt")
def _cong_tac():
	d = json.loads((GOC / "vagabond/doctype/vagabond_settings/vagabond_settings.json").read_text())
	o = next(x for x in d["fields"] if x["fieldname"] == "web_ten_mien_chinh")
	la("kiểu, mặc định", (o["fieldtype"], o.get("default")), ("Check", "0"))
	dung("nhãn có dấu", o["label"] == "Dùng tên miền chính cho web khách")
	dung("giải thích cách tắt", "không cần deploy" in o["description"] and "Tắt" in o["description"])
	fo = d["field_order"]
	la("ngay dưới web_ban_vue", fo[fo.index("web_ban_vue") + 1], "web_ten_mien_chinh")
	la("field_order khớp", sorted(fo), sorted(x["fieldname"] for x in d["fields"]))
	dung("modified đã đẩy", d["modified"] >= "2026-10-18 23:00")


def _seo(nhan=None, khoi=None, mien=None):
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap
	from vagabond import trang_khach, web_vue
	g = {"trang_khach": trang_khach, "du_lieu_cau_truc": web_vue.du_lieu_cau_truc,
		"SEO_MO_TA": web_vue.SEO_MO_TA, "SEO_ANH": web_vue.SEO_ANH,
		"noi_dung_web": types.SimpleNamespace(cong_khai=lambda: {"nhan": nhan or {}, "khoi": khoi or []})}
	f = nap("web_vue.py", "seo_banh", g)
	return f(mien) if mien else f()


@ca("v605 SEO: không lấy khối Editor 'Mở các kênh đặt hàng' + logo Grab; mô tả, ảnh cố định của tiệm")
def _seo_mac_dinh():
	from vagabond import web_vue
	khoi = [{"hien": True, "anh": "/assets/vagabond/web_order/logo-kenh/grab.png", "tieu_de": "Mở các kênh đặt hàng",
		"noi_dung": "Mở các kênh đặt hàng"}]
	s = _seo(khoi=khoi)
	dung("mô tả không phải câu kênh", "kênh" not in s["description"] and "Trần Cao Vân" in s["description"])
	la("ảnh của tiệm", s["image"], "https://order.%s/assets/vagabond/web_order/og-banh.jpg" % CHINH)
	dung("tệp ảnh có thật", (GOC / "public/web_order/og-banh.jpg").is_file())
	s = _seo(mien=CHINH)
	la("ảnh, canonical theo tên miền chính", (s["image"], s["url"]),
		("https://%s/assets/vagabond/web_order/og-banh.jpg" % CHINH, "https://%s/banh" % CHINH))
	dung("mô tả không quá 300", len(web_vue.SEO_MO_TA) <= 300)


@ca("v605 Codex #491: không đọc nhãn SEO chưa đăng ký (Editor không lưu được thì không hứa sửa được)")
def _khong_nhan_ma():
	src = (GOC / "web_vue.py").read_text()
	for k in ("seo_mo_ta", "seo_anh"):
		dung("web_vue không đọc " + k, "'%s'" % k not in src and '"%s"' % k not in src)


@ca("v605 JSON-LD: Bakery + WebSite, đúng tên miền, không đóng thẻ script sớm")
def _ld():
	from vagabond.web_vue import du_lieu_cau_truc
	x = du_lieu_cau_truc("https://" + CHINH, "https://x/</script><b>")
	dung("không có </ thô", "</" not in x)
	d = json.loads(x)
	la("loại", [k["@type"] for k in d], ["Bakery", "WebSite"])
	la("url", d[0]["url"], "https://%s/" % CHINH)
	la("địa chỉ", d[0]["address"]["streetAddress"], "9 Trần Cao Vân")
	html = (GOC / "www/web_moi/banh.html").read_text()
	dung("chỉ nhúng khi công khai", '{% if cong_khai and seo.ld_json %}<script type="application/ld+json">{{ seo.ld_json }}</script>{% endif %}' in html)


@ca("v605 favicon: /favicon.ico có thật, ba trang Vue khai icon")
def _favicon():
	ico = GOC / "www/favicon.ico"
	dung("có tệp", ico.is_file())
	la("đúng định dạng ico", ico.read_bytes()[:4], b"\x00\x00\x01\x00")
	for t in ("banh", "xong", "chinh-sach"):
		html = (GOC / ("www/web_moi/%s.html" % t)).read_text()
		dung(t + " khai favicon", '<link rel="icon" href="/favicon.ico" sizes="any">' in html)
		dung(t + " khai icon 192", 'href="/assets/vagabond/pwa/icon-192.png"' in html)
		dung(t + " tệp icon có thật", (GOC / "public/pwa/icon-192.png").is_file())


@ca("v605 LadyRuby: tên bánh có dấu không còn bị đổi sang phông hệ thống (trang Vue và trang cũ)")
def _phong():
	for p in ("public/web_vue/banh/banh.css", "trang/banh.html"):
		s = (GOC / p).read_text()
		dung(p + " bỏ luật .c-name.vi", ".c-name.vi" not in s)
	css = (GOC / "public/web_vue/banh/banh.css").read_text()
	dung("tên bánh vẫn Vagabond Sans", ".c-name{font-family:'Vagabond Sans'" in css)
