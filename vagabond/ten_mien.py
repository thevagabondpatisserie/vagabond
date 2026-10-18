"""Định tuyến theo TÊN MIỀN: mỗi subdomain một việc.

Anh Việt chốt 23/08/2026:

  app.thevagabondpatisserie.com    chỉ app nghiệp vụ
  erp.thevagabondpatisserie.com    chỉ Desk của ERPNext
  order.thevagabondpatisserie.com  chỉ trang khách đặt bánh

VÌ SAO PHẢI LÀM Ở ĐÂY CHỨ KHÔNG ĐỔI Website Settings
----------------------------------------------------
`Website Settings.home_page` là thiết lập TOÀN SITE, không tách theo tên
miền được. Cả tiệm chỉ có một site Frappe, nên đặt home_page thành `bep` là
khách vào tên miền nào cũng ra app nội bộ.

BA ĐIỀU CẨN THẬN, ĐỌC TRƯỚC KHI SỬA TỆP NÀY
--------------------------------------------
1. CHỈ ba tên miền dưới đây bị áp luật. Tên miền lạ, tên miền mặc định của
   Frappe Cloud (`*.frappe.cloud`), localhost, đều đi đường cũ không đụng
   tới. Đây là chốt an toàn quan trọng nhất: đặt luật rộng rồi chặn nhầm là
   KHOÁ CỬA CHÍNH MÌNH, không vào Desk mà sửa lại được nữa.

2. Chặn ở đây là CHUYỂN HƯỚNG, không phải trả lỗi. Người vào nhầm cửa thì
   đưa họ sang đúng cửa, đừng ném 403 vào mặt.

3. TUYỆT ĐỐI không chặn `/api`, `/assets`, `/files`, `/private`. App gọi API
   và tải tài nguyên tĩnh qua chính tên miền của nó; chặn là app trắng màn.
   Danh sách này đã làm hỏng một lần ở nơi khác, đừng rút gọn nó.
"""

MIEN_APP = "app.thevagabondpatisserie.com"
MIEN_DESK = "erp.thevagabondpatisserie.com"
MIEN_KHACH = "order.thevagabondpatisserie.com"
# Sẵn sàng nhận apex/www; chỉ đổi link phát ra sau khi DNS và SSL được kiểm.
MIEN_CHINH = "thevagabondpatisserie.com"
CAC_MIEN_KHACH = (MIEN_KHACH, MIEN_CHINH, "www." + MIEN_CHINH)

# Trang chu cua tung mien.
NHA = {
	MIEN_APP: "/bep",
	MIEN_DESK: "/app",
	MIEN_KHACH: "/banh",
	MIEN_CHINH: "/banh",
	"www." + MIEN_CHINH: "/banh",
}

# Duong dan KHONG BAO GIO bi dinh vao, du o mien nao. Xem dieu 3 o tren.
CHUA_RA = (
	"/api/", "/assets/", "/files/", "/private/", "/socket.io/",
	"/.well-known/", "/robots.txt", "/favicon.ico", "/sitemap.xml",
	"/manifest.json", "/sw.js", "/login", "/update-password",
)

# Duong dan cua tung mien. Vao dung mien nay thi cho qua.
# Mien app: app nghiep vu va cac man con cua no.
DAU_APP = ("/bep", "/btp", "/kiem-banh", "/kho-moi", "/kho-v2", "/in-tem", "/cuon-ma")
# Mien khach: trang dat banh va thanh toan don.
# #367: them ba trang chinh sach. "/banh" da gom ca trang bien nhan
# /banh/xong/<token>.
DAU_KHACH = ("/dat-ban", "/thanh-vien", "/banh", "/tt", "/xhd", "/ong-trang", "/suc-khoe", "/sop-san-xuat",
	"/chinh-sach-bao-mat", "/dieu-khoan", "/giao-hang-doi-tra",
	"/web_moi/banh", "/web_moi/chinh-sach-bao-mat", "/web_moi/dieu-khoan", "/web_moi/giao-hang-doi-tra")
# Mien Desk: khong khai o day, xem `_la_desk`.

# DUONG DI QUA MOI MIEN, khong bao gio bi da (them 03/09/2026).
#
# /xhd la trang khach quet QR cuoi bill giay de dien thong tin xuat hoa don.
# Cai QR do IN LEN GIAY dia chi cua trinh duyet thu ngan luc in, tuc la
# app.thevagabondpatisserie.com. Tu 23/08 luat tren coi /xhd la trang KHACH
# nen mien app da no ve /bep: khach quet xong thay man dang nhap app noi bo.
#
# Vi sao "luc duoc luc khong": luat nay chay trong luc DUNG trang, ma Frappe
# giu trang web da dung trong bo nho dem cho khach vang lai. Trang dang nam
# trong dem thi luat khong chay va khach vao duoc; moi lan deploy xoa dem
# la khach dau tien lai bi da. Hai tuan qua deploy hon muoi lan mot ngay.
#
# Sua hai tang: ma QR in dia chi mien khach co dinh (xem `link_khach`), VA
# /xhd di qua moi mien de nhung to bill da in truoc hom nay van quet duoc.
DUONG_CHUNG = ("/xhd",)


def _sach(duong):
	d = "/" + str(duong or "").lstrip("/")
	return d.rstrip("/") or "/"


def _mien(host):
	return str(host or "").split(":")[0].strip().lower()


def _la_desk(d):
	"""Đường của Desk ERPNext."""
	return d == "/app" or d.startswith("/app/") or d.startswith("/desk")


def _thuoc(d, dau):
	return any(d == x or d.startswith(x + "/") for x in dau)


def dich_chuyen_huong(host, duong, duong_app=()):
	"""Tên miền này vào đường này thì nên đá sang đâu. "" là cho đi tiếp.

	Hàm THUẦN, không chạm Frappe, nên kiểm thử được không cần site.

	`duong_app`: các slug màn hình của app Bếp (vagabond.duong_app.DUONG),
	truyền vào chứ không import để hàm đứng một mình kiểm thử được.
	"""
	m = _mien(host)
	if m not in NHA:
		return ""
	d = _sach(duong)

	# Duong dung chung, khong bao gio dinh vao.
	if d == "/" :
		return NHA[m] if NHA[m] != "/" else ""
	for x in CHUA_RA:
		if d == x.rstrip("/") or d.startswith(x):
			return ""

	if _thuoc(d, DUONG_CHUNG):
		return ""

	la_app = _thuoc(d, DAU_APP) or _thuoc(d, tuple("/" + s for s in duong_app or ()))
	la_khach = _thuoc(d, DAU_KHACH)
	la_desk = _la_desk(d)

	if m == MIEN_APP:
		return "" if la_app else (NHA[m] if (la_desk or la_khach) else "")
	if m == MIEN_DESK:
		return "" if la_desk else (NHA[m] if (la_app or la_khach) else "")
	if m in CAC_MIEN_KHACH:
		return "" if la_khach else (NHA[m] if (la_app or la_desk) else "")
	return ""


def link_khach(duong):
	"""Địa chỉ TUYỆT ĐỐI trên miền khách cho một đường. Hàm THUẦN.

	Dùng cho mọi thứ in ra giấy hay gửi cho khách: QR xuất hoá đơn, link
	thanh toán. In địa chỉ theo trình duyệt của thu ngân là in cái miền
	app.*, mà miền đó là miền nội bộ, khách vào là bị đá.
	"""
	d = _sach(duong)
	return "https://%s%s" % (MIEN_KHACH, d if d != "/" else "")


def ap_luat():
	"""Gọi từ hook `update_website_context`, mỗi lượt tải trang web một lần.

	KHÔNG dùng cho `/api` và `/assets`: hook này chỉ chạy ở tầng trang web,
	còn API đi đường khác của Frappe. Dù vậy `CHUA_RA` vẫn giữ nguyên để
	nếu mai này ai đó gọi hàm này từ chỗ rộng hơn thì vẫn an toàn.

	Nuốt mọi lỗi: định tuyến hỏng thì cùng lắm là vào nhầm cửa, còn ném lỗi
	ở đây là TRẮNG MÀN mọi trang của site.
	"""
	import frappe

	try:
		req = getattr(frappe.local, "request", None)
		if not req:
			return
		from vagabond.duong_app import DUONG

		dich = dich_chuyen_huong(req.host, req.path, tuple(DUONG))
		if dich and _sach(dich) != _sach(req.path):
			frappe.local.flags.redirect_location = dich
			raise frappe.Redirect
	except Exception:
		if frappe.local.flags.get("redirect_location"):
			raise
		return


# ------------------------------------------------------------------ v605
# Anh Việt 18/10/2026: đưa trang đặt bánh lên tên miền chính
# thevagabondpatisserie.com (thay web WordPress cũ), order. và www. chuyển
# vĩnh viễn (301) về tên miền chính, mọi đường dẫn WordPress cũ đã có trên
# Google chuyển 301 về trang đặt bánh để giữ thứ hạng.
#
# VÌ SAO CHẠY Ở before_request CHỨ KHÔNG Ở `ap_luat`: `ap_luat` chạy lúc DỰNG
# trang, mà Frappe giữ trang đã dựng trong bộ nhớ đệm cho khách vãng lai (xem
# ghi chú DUONG_CHUNG ở trên). Chuyển hướng tên miền phải chạy ở MỌI lượt, nên
# đặt ở before_request, chạy trước cả bộ đệm trang.
#
# Ba chốt an toàn, giữ nguyên khi sửa:
# 1. Chỉ chạy khi công tắc "Dùng tên miền chính" trong Cài đặt đang bật. Bật
#    sau khi DNS và SSL của tên miền chính đã kiểm; tắt là order. hết chuyển
#    hướng ngay, không cần deploy.
# 2. Chỉ GET và HEAD. POST (gửi đơn, webhook) đi thẳng, chuyển hướng POST là
#    mất dữ liệu khách.
# 3. Không đụng CHUA_RA (/api, /assets, /files...): app và đối tác gọi qua
#    chính tên miền order., chặn là trắng màn và rớt webhook.

MIEN_WWW = "www." + MIEN_CHINH

# Đường dẫn WordPress cũ (đọc từ wp-sitemap.xml ngày 18/10/2026) và đường
# dẫn hệ thống của WordPress. Khớp theo cả đoạn đường: "/en" khớp "/en" và
# "/en/...", không khớp "/endless".
DUONG_WP = (
	"/shop", "/cart", "/checkout", "/my-account", "/thanks-page", "/products", "/product",
	"/product-category", "/category", "/author", "/tag", "/gioi-thieu", "/tin-tuc", "/lien-he",
	"/xin-chao", "/2026mooncake", "/en", "/hello-world", "/sample-page", "/hello-theme-7",
	"/feed", "/comments", "/wp-admin", "/wp-content", "/wp-includes", "/wp-json",
	"/wp-login.php", "/xmlrpc.php", "/index.php", "/wp-sitemap.xml", "/sitemap_index.xml",
)
# Bài viết cũ có số đuôi -2, -3...: khớp theo đầu chuỗi.
DAU_BAI_WP = ("/the-vagabond-nhung-nguoi-lam-banh-lang-thang-tim-cai-dep",)

# Đường không bao giờ chuyển tên miền (giữ cho app, đối tác, máy tìm kiếm).
KHONG_CHUYEN = ("/api/", "/assets/", "/files/", "/private/", "/socket.io/", "/.well-known/", "/backups/")


def chuyen_ten_mien(host, duong, phuong_thuc="GET", chuoi_hoi="", bat=False):
	"""THUẦN: (địa chỉ đích, mã) nếu lượt này phải chuyển, None nếu cho đi tiếp.

	host, duong, chuoi_hoi lấy nguyên từ request (chuoi_hoi không có dấu ?).
	"""
	if not bat:
		return None
	if str(phuong_thuc or "").upper() not in ("GET", "HEAD"):
		return None
	m = _mien(host)
	if m not in (MIEN_KHACH, MIEN_CHINH, MIEN_WWW):
		return None
	goc = "/" + str(duong or "").lstrip("/")
	if any(goc.startswith(x) or goc == x.rstrip("/") for x in KHONG_CHUYEN):
		return None
	hoi = str(chuoi_hoi or "").lstrip("?")
	duoi = goc + ("?" + hoi if hoi else "")

	if m in (MIEN_KHACH, MIEN_WWW):
		return ("https://%s%s" % (MIEN_CHINH, duoi), 301)

	# Tên miền chính.
	d = _sach(goc)
	if d == "/":
		# 302: trang chủ thương hiệu sau này sẽ nằm ở "/", đừng để trình duyệt
		# nhớ vĩnh viễn. Giữ chuỗi hỏi để không mất mã utm của quảng cáo.
		return ("/banh" + ("?" + hoi if hoi else ""), 302)
	thap = d.lower()
	if _thuoc(thap, DUONG_WP) or any(thap.startswith(x) for x in DAU_BAI_WP):
		return ("/banh", 301)
	return None


def mien_cong_khai(bat):
	"""THUẦN: tên miền ghi vào thẻ canonical, og:url của trang khách."""
	return MIEN_CHINH if bat else MIEN_KHACH


def cong_tac_mien_chinh():
	"""Đọc công tắc trong Cài đặt. Lỗi đọc (chưa migrate) coi như tắt."""
	import frappe

	try:
		return int(frappe.db.get_single_value("Vagabond Settings", "web_ten_mien_chinh", cache=True) or 0)
	except Exception:
		return 0



def truoc_request():
	"""Hook before_request. Chỉ đọc Cài đặt khi tên miền thuộc ba tên miền khách.

	Nuốt mọi lỗi trừ chính lệnh chuyển hướng: hỏng ở đây là hỏng MỌI lượt gọi
	của site, kể cả app nội bộ.
	"""
	import frappe
	from werkzeug.exceptions import HTTPException
	from werkzeug.utils import redirect

	try:
		req = getattr(frappe.local, "request", None)
		if not req or _mien(req.host) not in (MIEN_KHACH, MIEN_CHINH, MIEN_WWW):
			return
		qs = req.query_string.decode("utf-8", "ignore") if isinstance(req.query_string, bytes) else str(req.query_string or "")
		kq = chuyen_ten_mien(req.host, req.path, req.method, qs, cong_tac_mien_chinh())
		if not kq:
			return
		dich, ma = kq
	except Exception:
		return

	class ChuyenHuong(HTTPException):
		code = ma

		def get_response(self, environ=None, scope=None):
			return redirect(dich, ma)

	raise ChuyenHuong()
