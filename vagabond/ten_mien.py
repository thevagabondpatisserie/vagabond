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

# Trang chu cua tung mien.
NHA = {
	MIEN_APP: "/bep",
	MIEN_DESK: "/app",
	MIEN_KHACH: "/banh",
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
DAU_KHACH = ("/banh", "/tt", "/xhd", "/ong-trang", "/suc-khoe", "/sop-san-xuat")
# Mien Desk: khong khai o day, xem `_la_desk`.


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

	la_app = _thuoc(d, DAU_APP) or _thuoc(d, tuple("/" + s for s in duong_app or ()))
	la_khach = _thuoc(d, DAU_KHACH)
	la_desk = _la_desk(d)

	if m == MIEN_APP:
		return "" if la_app else (NHA[m] if (la_desk or la_khach) else "")
	if m == MIEN_DESK:
		return "" if la_desk else (NHA[m] if (la_app or la_khach) else "")
	if m == MIEN_KHACH:
		return "" if la_khach else (NHA[m] if (la_app or la_desk) else "")
	return ""


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
