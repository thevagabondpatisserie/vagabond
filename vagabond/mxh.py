# -*- coding: utf-8 -*-
"""v664 Tự đăng bài lên Facebook, Instagram, Threads (anh Việt 16/11/2026).

Vì sao có tệp này
-----------------
v662 cho Marketing soạn, duyệt bài trong app nhưng mọi kênh vẫn đăng tay. Ngày
16/11 anh Việt báo "đang không có đăng được gì" và giao nối Meta để hệ thống tự
đăng đúng giờ hẹn.

Cách nối (không ai phải nhập mật khẩu vào app, Claude không nhập token):
  - Facebook và Instagram: token của Người dùng hệ thống (System User) "Vagabond
    ERP" trong doanh nghiệp TVB, đã được gán Trang và tài khoản Instagram, tích
    quyền đăng bài. Token này không hết hạn. Quản trị hệ thống dán vào Cài đặt lõi
    và API, mục Đăng bài mạng xã hội. Từ token, hệ thống tự tìm Trang và tài khoản
    Instagram doanh nghiệp nối với Trang.
  - Threads: token người dùng Threads (sống 60 ngày) tạo ở bảng điều khiển ứng dụng
    Meta, mục Threads, Trình tạo mã người dùng. Hệ thống tự gia hạn mỗi tuần.
  - Zalo OA vẫn đăng tay.

Đăng một kênh là một chuỗi gọi Meta. Bước cuối (công bố) mà mất mạng thì KHÔNG
biết bài đã lên hay chưa: báo "chưa rõ" (LoiDang.ro = False) để người kiểm trên
kênh trước khi đăng lại, không tự đăng lại (tránh đăng hai lần).

Phần THUẦN đứng trước vạch, phần chạm hệ đứng sau.
"""

import json
import time

GRAPH = "https://graph.facebook.com/v21.0"
THREADS = "https://graph.threads.net/v1.0"
THREADS_GOC = "https://graph.threads.net"
TIMEOUT = 60
CHO_XU_LY_GIAY = 90
NHIP_HOI_GIAY = 3
SONG_CACHE_GIAY = 600
KHOA_CACHE = "vgb_mxh_ket_noi"
GIA_HAN_SAU_NGAY = 6

# Mã lỗi Graph hay gặp -> việc cần làm. Nguồn: tài liệu lỗi Graph API (190 token
# hỏng, 10 và 200 thiếu quyền, 368 bị chặn tạm, 4, 17, 32, 613 quá nhịp gọi).
LOI_TOKEN = (190, 102, 463, 467)
LOI_QUYEN = (10, 200, 283, 299)
LOI_NHIP = (4, 17, 32, 613, 80001, 80002)


class LoiDang(Exception):
	"""Đăng một kênh không được. ro=False: bước công bố đã gửi đi mà mất mạng, không
	biết bài đã lên chưa."""

	def __init__(self, chu, ro=True):
		Exception.__init__(self, chu)
		self.chu = chu
		self.ro = ro


def loi_de_hieu(ten_kenh, tra):
	"""THUẦN: câu lỗi tiếng Việt nói việc cần làm, từ phần error Meta trả về."""
	loi = (tra or {}).get("error") if isinstance(tra, dict) else None
	if not isinstance(loi, dict):
		return "%s chưa nhận bài. Thử lại sau ít phút, vẫn lỗi thì đăng tay." % ten_kenh
	ma = loi.get("code")
	try:
		ma = int(ma)
	except (TypeError, ValueError):
		ma = None
	if ma in LOI_TOKEN:
		return "Token %s hết hạn hoặc bị thu hồi. Quản trị hệ thống tạo token mới ở Cài đặt lõi và API, mục Đăng bài mạng xã hội." % ten_kenh
	if ma in LOI_QUYEN:
		return "Token %s thiếu quyền đăng bài. Quản trị hệ thống tạo lại token, tích đủ quyền đăng bài." % ten_kenh
	if ma == 368:
		return "%s đang tạm chặn đăng bài từ hệ thống. Đăng tay bài này, vài giờ sau thử lại." % ten_kenh
	if ma in LOI_NHIP:
		return "%s đang giới hạn số lần gọi. Chờ khoảng 15 phút rồi bấm Thử lại." % ten_kenh
	tin = str(loi.get("error_user_msg") or loi.get("message") or "").strip()
	return ("%s từ chối bài: %s" % (ten_kenh, tin[:200])) if tin else ("%s chưa nhận bài. Thử lại sau ít phút, vẫn lỗi thì đăng tay." % ten_kenh)


def hop_cat(rong, cao, khung):
	"""THUẦN: hộp cắt giữa ảnh (trái, trên, phải, dưới) để ảnh đúng khung "R:C"."""
	try:
		r, c = int(rong), int(cao)
		p = str(khung).split(":")
		ty = float(p[0]) / float(p[1])
	except (TypeError, ValueError, IndexError, ZeroDivisionError):
		return None
	if r <= 0 or c <= 0 or ty <= 0:
		return None
	if r / float(c) > ty:
		moi = int(round(c * ty))
		trai = (r - moi) // 2
		return (trai, 0, trai + moi, c)
	moi = int(round(r / ty))
	tren = (c - moi) // 2
	return (0, tren, r, tren + moi)


def chon_trang(ds, ma_cau_hinh=""):
	"""THUẦN: Trang để đăng trong danh sách Trang token nhìn thấy. Có mã cấu hình thì
	đúng mã đó; không thì chỉ nhận khi token thấy đúng một Trang."""
	ds = [t for t in (ds or []) if isinstance(t, dict) and t.get("id")]
	ma = "".join(ch for ch in str(ma_cau_hinh or "") if ch.isdigit())
	if ma:
		for t in ds:
			if str(t.get("id")) == ma:
				return t, ""
		return None, "Token không thấy Trang có mã %s. Kiểm ô Mã Trang Facebook hoặc gán Trang cho người dùng hệ thống." % ma
	if len(ds) == 1:
		return ds[0], ""
	if not ds:
		return None, "Token chưa được gán Trang Facebook nào. Gán Trang cho người dùng hệ thống Vagabond ERP rồi tạo lại token."
	return None, "Token thấy %d Trang. Điền Mã Trang Facebook ở Cài đặt lõi và API để chọn đúng Trang của tiệm." % len(ds)


def chu_cho_kenh(chu, tran):
	"""THUẦN: chữ gửi đi, bỏ khoảng trắng thừa hai đầu, không vượt trần (bảng Kiểm đã
	chặn lúc duyệt; đây là lưới cuối)."""
	chu = str(chu or "").strip()
	return chu[:tran] if tran and len(chu) > tran else chu


# ------------------------------------------------------------ phần chạm hệ

import frappe  # noqa: E402

try:
	import requests  # noqa: E402
except ImportError:  # CI tay không
	requests = None


def _cfg():
	return frappe.get_doc("Vagabond Settings")


def _khoa(c, o):
	from vagabond.lib import key
	try:
		return key(c, o)
	except Exception:
		return ""


def _goi(phuong_thuc, url, tok, data=None, files=None, params=None, cong_bo=False, ten_kenh="Meta"):
	"""Một lần gọi Meta. Trả dict khi thành công; ném LoiDang khi không.
	cong_bo=True: đây là bước công bố, mất mạng giữa chừng thì không biết đã lên chưa."""
	if frappe.flags.get("vagabond_kiem_that"):
		raise LoiDang("Đang chạy kiểm thử: không đăng thật lên %s." % ten_kenh)
	if requests is None:
		raise LoiDang("Máy chủ thiếu thư viện gọi mạng, báo quản trị hệ thống.")
	p = dict(params or {})
	p["access_token"] = tok
	try:
		r = requests.request(phuong_thuc, url, params=p, data=data, files=files, timeout=TIMEOUT)
	except Exception:
		from vagabond.lib import giau_khoa
		frappe.log_error(title="Bài đăng: lỗi mạng khi gọi %s" % ten_kenh, message=giau_khoa(frappe.get_traceback()))
		if cong_bo:
			raise LoiDang("Mất kết nối lúc công bố bài lên %s, chưa rõ bài đã lên chưa. Mở %s kiểm: đã có bài thì bấm Đã đăng, chưa có thì bấm Thử lại." % (ten_kenh, ten_kenh), ro=False)
		raise LoiDang("Chưa gọi được %s (mất kết nối). Bấm Thử lại sau ít phút." % ten_kenh)
	try:
		tra = r.json() if r.content else {}
	except ValueError:
		tra = {}
	if r.status_code >= 400 or (isinstance(tra, dict) and tra.get("error")):
		raise LoiDang(loi_de_hieu(ten_kenh, tra))
	return tra if isinstance(tra, dict) else {}


def _thu_goi(*a, **k):
	"""Gọi phụ (đọc link, tên): lỗi thì trả {} chứ không làm hỏng bài đã lên."""
	try:
		return _goi(*a, **k)
	except LoiDang:
		return {}


# ---------- kết nối

def _trang_cua_token(tok, ma_cau_hinh):
	"""Trang để đăng và token Trang. Token người dùng hệ thống: đọc /me/accounts. Token
	Trang dán thẳng: /me chính là Trang."""
	tra = _thu_goi("GET", GRAPH + "/me/accounts", tok, params={"fields": "id,name,access_token,instagram_business_account{id,username}", "limit": 100},
		ten_kenh="Facebook")
	ds = tra.get("data") or []
	if not ds:
		# Token Trang dán thẳng: /me là Trang. Nút User không có trường
		# instagram_business_account nên Meta báo lỗi, _thu_goi trả rỗng.
		me = _thu_goi("GET", GRAPH + "/me", tok, params={"fields": "id,name,instagram_business_account{id,username}"}, ten_kenh="Facebook")
		if me.get("id"):
			ds = [dict(me, access_token=tok)]
		elif not tra:
			# Cả hai lần đều lỗi: gọi lại lần đầu để có câu lỗi thật (token hỏng, thiếu quyền).
			_goi("GET", GRAPH + "/me/accounts", tok, params={"fields": "id"}, ten_kenh="Facebook")
	t, loi = chon_trang(ds, ma_cau_hinh)
	if not t:
		raise LoiDang(loi)
	return {"id": str(t["id"]), "ten": t.get("name") or "", "token": t.get("access_token") or tok,
		"ig": t.get("instagram_business_account") or None}


def trang_thai(lam_moi=False):
	"""Kết nối từng kênh cho màn (không chứa token). Đọc Meta tối đa 10 phút một lần."""
	if not lam_moi:
		try:
			c = frappe.cache().get_value(KHOA_CACHE)
			if c:
				return c
		except Exception:
			pass
	c = _cfg()
	ra = {"fb": {"ok": 0, "chu": "Chưa nối. Bài lên Facebook phải đăng tay."},
		"ig": {"ok": 0, "chu": "Chưa nối. Bài lên Instagram phải đăng tay."},
		"th": {"ok": 0, "chu": "Chưa nối. Bài lên Threads phải đăng tay."},
		"zl": {"ok": 0, "chu": "Zalo OA đăng tay."}}
	tok = _khoa(c, "mxh_token")
	if tok:
		try:
			t = _trang_cua_token(tok, c.get("mxh_page_id"))
			ra["fb"] = {"ok": 1, "chu": "Tự đăng lên Trang %s" % t["ten"]}
			if t.get("ig"):
				ra["ig"] = {"ok": 1, "chu": "Tự đăng lên @%s" % (t["ig"].get("username") or t["ig"].get("id"))}
			else:
				ra["ig"] = {"ok": 0, "chu": "Trang chưa nối tài khoản Instagram doanh nghiệp. Bài lên Instagram phải đăng tay."}
		except LoiDang as e:
			ra["fb"] = {"ok": 0, "chu": e.chu, "loi": 1}
			ra["ig"] = {"ok": 0, "chu": "Chưa nối được vì token Facebook lỗi.", "loi": 1}
	th = _khoa(c, "th_token")
	if th:
		try:
			me = _goi("GET", THREADS + "/me", th, params={"fields": "id,username"}, ten_kenh="Threads")
			het = str(c.get("th_het_han") or "")[:10]
			ra["th"] = {"ok": 1, "chu": "Tự đăng lên @%s%s" % (me.get("username") or me.get("id"),
				(" · token dùng tới %s/%s/%s" % (het[8:10], het[5:7], het[:4])) if het else "")}
		except LoiDang as e:
			ra["th"] = {"ok": 0, "chu": e.chu, "loi": 1}
	try:
		frappe.cache().set_value(KHOA_CACHE, ra, expires_in_sec=SONG_CACHE_GIAY)
	except Exception:
		pass
	return ra


def kenh_noi(lam_moi=False):
	"""Tập mã kênh đang tự đăng được."""
	return set(k for k, v in trang_thai(lam_moi).items() if v.get("ok"))


def xoa_cache():
	try:
		frappe.cache().delete_value(KHOA_CACHE)
	except Exception:
		pass


# ---------- ảnh

def _noi_dung_anh(url):
	ten = frappe.db.get_value("File", {"file_url": url}, "name")
	if not ten:
		raise LoiDang("Không đọc được ảnh %s. Tải lại ảnh vào bài." % url)
	return frappe.get_doc("File", ten).get_content()


def anh_jpeg(url, khung=None):
	"""Ảnh của bài thành JPEG; có khung thì cắt giữa đúng khung (như màn xem trước ghi
	"Ảnh cắt tự động"). Instagram chỉ nhận JPEG."""
	import io
	from PIL import Image
	goc = _noi_dung_anh(url)
	with Image.open(io.BytesIO(goc)) as im:
		im = im.convert("RGB")
		if khung:
			hop = hop_cat(im.size[0], im.size[1], khung)
			if hop:
				im = im.crop(hop)
		ra = io.BytesIO()
		im.save(ra, "JPEG", quality=92)
		return ra.getvalue()


def url_cong_khai(ma_bai, noi_dung):
	"""Instagram và Threads tự tải ảnh về từ một đường dẫn công khai. Lưu bản JPEG
	thành tệp công khai, tên ngẫu nhiên, gắn vào bài."""
	import secrets
	from frappe.utils import get_url
	f = frappe.get_doc({"doctype": "File", "file_name": "bd-%s.jpg" % secrets.token_hex(12), "is_private": 0,
		"attached_to_doctype": "Vagabond Bai Dang", "attached_to_name": ma_bai, "content": noi_dung})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	return get_url(f.file_url)


# ---------- đăng từng kênh. anh: [{"url", "khung", "cat"}] như bai_dang.anh_cho_kenh.

def _link(url_goc, ma, truong, tok, ten_kenh):
	return (_thu_goi("GET", "%s/%s" % (url_goc, ma), tok, params={"fields": truong}, ten_kenh=ten_kenh).get(truong) or "")


def dang_fb(trang, chu, anh, story=False):
	pid, tok, ten = trang["id"], trang["token"], "Facebook"
	if story:
		if not anh:
			raise LoiDang("Story Facebook cần một ảnh.")
		ph = _goi("POST", "%s/%s/photos" % (GRAPH, pid), tok, data={"published": "false"},
			files={"source": ("story.jpg", anh_jpeg(anh[0]["url"], "9:16"), "image/jpeg")}, ten_kenh=ten)
		r = _goi("POST", "%s/%s/photo_stories" % (GRAPH, pid), tok, data={"photo_id": ph.get("id")}, cong_bo=True, ten_kenh=ten)
		return str(r.get("post_id") or ph.get("id") or ""), ""
	if not anh:
		r = _goi("POST", "%s/%s/feed" % (GRAPH, pid), tok, data={"message": chu}, cong_bo=True, ten_kenh=ten)
		ma = str(r.get("id") or "")
	elif len(anh) == 1:
		r = _goi("POST", "%s/%s/photos" % (GRAPH, pid), tok, data={"message": chu},
			files={"source": ("anh.jpg", anh_jpeg(anh[0]["url"]), "image/jpeg")}, cong_bo=True, ten_kenh=ten)
		ma = str(r.get("post_id") or r.get("id") or "")
	else:
		ids = []
		for a in anh:
			ph = _goi("POST", "%s/%s/photos" % (GRAPH, pid), tok, data={"published": "false"},
				files={"source": ("anh.jpg", anh_jpeg(a["url"]), "image/jpeg")}, ten_kenh=ten)
			ids.append({"media_fbid": ph.get("id")})
		r = _goi("POST", "%s/%s/feed" % (GRAPH, pid), tok, data={"message": chu, "attached_media": json.dumps(ids)}, cong_bo=True, ten_kenh=ten)
		ma = str(r.get("id") or "")
	return ma, _link(GRAPH, ma, "permalink_url", tok, ten) if ma else ""


def _cho_xong(url_goc, ma, tok, truong, xong, hong, ten_kenh):
	"""Instagram, Threads xử lý ảnh xong mới cho công bố. Hỏi lại tới khi xong."""
	het = time.time() + CHO_XU_LY_GIAY
	while True:
		tra = _goi("GET", "%s/%s" % (url_goc, ma), tok, params={"fields": truong}, ten_kenh=ten_kenh)
		tt = str(tra.get(truong) or "").upper()
		if tt == xong:
			return
		if tt in hong:
			raise LoiDang("%s không xử lý được ảnh của bài. Kiểm ảnh (JPEG, đúng khung) rồi Thử lại, hoặc đăng tay." % ten_kenh)
		if time.time() > het:
			raise LoiDang("%s xử lý ảnh quá lâu nên chưa công bố. Bấm Thử lại sau ít phút." % ten_kenh)
		time.sleep(NHIP_HOI_GIAY)


def dang_ig(ma_bai, trang, chu, anh, story=False):
	ig = (trang.get("ig") or {}).get("id")
	tok, ten = trang["token"], "Instagram"
	if not ig:
		raise LoiDang("Trang chưa nối tài khoản Instagram doanh nghiệp, đăng tay bài này.")
	if not anh:
		raise LoiDang("Instagram cần ít nhất một ảnh.")
	tao = lambda d: _goi("POST", "%s/%s/media" % (GRAPH, ig), tok, data=d, ten_kenh=ten).get("id")
	url = lambda a, khung: url_cong_khai(ma_bai, anh_jpeg(a["url"], khung))
	if story:
		c = tao({"media_type": "STORIES", "image_url": url(anh[0], "9:16")})
	elif len(anh) == 1:
		c = tao({"image_url": url(anh[0], anh[0]["khung"] if anh[0].get("cat") else None), "caption": chu})
	else:
		con = []
		for a in anh:
			m = tao({"image_url": url(a, a["khung"] if a.get("cat") else None), "is_carousel_item": "true"})
			_cho_xong(GRAPH, m, tok, "status_code", "FINISHED", ("ERROR", "EXPIRED"), ten)
			con.append(m)
		c = tao({"media_type": "CAROUSEL", "children": ",".join(con), "caption": chu})
	_cho_xong(GRAPH, c, tok, "status_code", "FINISHED", ("ERROR", "EXPIRED"), ten)
	r = _goi("POST", "%s/%s/media_publish" % (GRAPH, ig), tok, data={"creation_id": c}, cong_bo=True, ten_kenh=ten)
	ma = str(r.get("id") or "")
	return ma, _link(GRAPH, ma, "permalink", tok, ten) if ma and not story else ""


def dang_th(ma_bai, tok, chu, anh):
	ten = "Threads"
	tao = lambda d: _goi("POST", THREADS + "/me/threads", tok, data=d, ten_kenh=ten).get("id")
	url = lambda a: url_cong_khai(ma_bai, anh_jpeg(a["url"], a["khung"] if a.get("cat") else None))
	if not anh:
		c = tao({"media_type": "TEXT", "text": chu})
	elif len(anh) == 1:
		c = tao({"media_type": "IMAGE", "image_url": url(anh[0]), "text": chu})
	else:
		con = [tao({"media_type": "IMAGE", "image_url": url(a), "is_carousel_item": "true"}) for a in anh]
		for m in con:
			_cho_xong(THREADS, m, tok, "status", "FINISHED", ("ERROR", "EXPIRED"), ten)
		c = tao({"media_type": "CAROUSEL", "children": ",".join(con), "text": chu})
	_cho_xong(THREADS, c, tok, "status", "FINISHED", ("ERROR", "EXPIRED"), ten)
	r = _goi("POST", THREADS + "/me/threads_publish", tok, data={"creation_id": c}, cong_bo=True, ten_kenh=ten)
	ma = str(r.get("id") or "")
	return ma, _link(THREADS, ma, "permalink", tok, ten) if ma else ""


def dang(kenh, ma_bai, chu, anh, story=False):
	"""Đăng một kênh. Trả (mã bài trên kênh, link). Lỗi thì ném LoiDang."""
	c = _cfg()
	if kenh in ("fb", "ig"):
		tok = _khoa(c, "mxh_token")
		if not tok:
			raise LoiDang("Chưa có token Facebook, Instagram ở Cài đặt lõi và API. Đăng tay bài này.")
		trang = _trang_cua_token(tok, c.get("mxh_page_id"))
		if kenh == "fb":
			return dang_fb(trang, chu, anh, story)
		return dang_ig(ma_bai, trang, chu, anh, story)
	if kenh == "th":
		tok = _khoa(c, "th_token")
		if not tok:
			raise LoiDang("Chưa có token Threads ở Cài đặt lõi và API. Đăng tay bài này.")
		return dang_th(ma_bai, tok, chu, anh)
	raise LoiDang("Kênh này đăng tay.")


def gia_han_threads():
	"""Nhịp mỗi ngày: token Threads sống 60 ngày, gia hạn khi đã quá 6 ngày từ lần trước
	(Meta chỉ cho gia hạn token đã quá 24 giờ). Lỗi thì ghi Error Log, hôm sau thử lại."""
	try:
		from datetime import timedelta
		from frappe.utils import now_datetime, get_datetime
		from frappe.utils.password import set_encrypted_password
		c = _cfg()
		tok = _khoa(c, "th_token")
		if not tok:
			return
		luc = c.get("th_gia_han_luc")
		if luc and get_datetime(luc) > now_datetime() - timedelta(days=GIA_HAN_SAU_NGAY):
			return
		tra = _goi("GET", THREADS_GOC + "/refresh_access_token", tok, params={"grant_type": "th_refresh_token"}, ten_kenh="Threads")
		moi = tra.get("access_token")
		if not moi:
			return
		set_encrypted_password("Vagabond Settings", "Vagabond Settings", moi, "th_token")
		bay_gio = now_datetime()
		frappe.db.set_single_value("Vagabond Settings", "th_gia_han_luc", bay_gio)
		try:
			giay = int(tra.get("expires_in") or 0)
		except (TypeError, ValueError):
			giay = 0
		if giay:
			frappe.db.set_single_value("Vagabond Settings", "th_het_han", (bay_gio + timedelta(seconds=giay)).strftime("%Y-%m-%d"))
		frappe.db.commit()
		xoa_cache()
	except LoiDang as e:
		frappe.log_error(title="Bài đăng: chưa gia hạn được token Threads", message=e.chu)
	except Exception:
		from vagabond.lib import giau_khoa
		frappe.log_error(title="Bài đăng: chưa gia hạn được token Threads", message=giau_khoa(frappe.get_traceback()))
