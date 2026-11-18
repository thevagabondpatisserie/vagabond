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
  - Zalo OA (v666, anh Việt 17/11/2026 "làm luôn cái Zalo OA"): đăng thành Bài viết
    trên trang OA bằng Article API (openapi.zalo.me/v2.0/article). Dùng chung App ID,
    App Secret, Refresh Token của mục Zalo OA đã có, không dán thêm mã. Ứng dụng Zalo
    phải được Zalo duyệt nhóm "Quản lý bài viết" (Zalo for Developers, Article API,
    Nộp xét duyệt); chưa duyệt thì Zalo trả lỗi -212 và kênh hiện "chưa nối".
  - Sonneto (v672, anh Việt 18/11/2026 "kết nối với các kênh của Sonneto để đăng, quản
    lý từ 1 nơi thôi"): Trang Facebook, Instagram, Threads của Sonneto. Bài thuộc chủ đề
    mang thương hiệu Sonneto đi kênh Sonneto. Token Facebook riêng của doanh nghiệp
    Sonneto, hoặc để trống và dùng token Vagabond nếu Trang Sonneto đã được chia cho
    người dùng hệ thống Vagabond ERP; khi dùng chung token thì BẮT BUỘC có Mã Trang
    Sonneto, không bao giờ tự chọn Trang (kẻo bài Sonneto lên Trang Vagabond).
    Sonneto chưa có Zalo OA.

Threads (v672, anh Việt 18/11): bài quá 500 ký tự tự tách thành chuỗi bài nối tiếp
(phần sau trả lời phần trước, như app Threads tự làm khi đăng tay). Cần quyền
threads_manage_replies trên token Threads. Phần đầu lên rồi mà phần sau hỏng thì kênh
vẫn là Đã đăng (không đăng lại phần đầu), kèm ghi chú phần nào chưa lên để đăng tay.

Đăng một kênh là một chuỗi gọi Meta. Bước cuối (công bố) mà mất mạng thì KHÔNG
biết bài đã lên hay chưa: báo "chưa rõ" (LoiDang.ro = False) để người kiểm trên
kênh trước khi đăng lại, không tự đăng lại (tránh đăng hai lần).

Phần THUẦN đứng trước vạch, phần chạm hệ đứng sau.
"""

import json
import re
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
ZALO_BAI = "https://openapi.zalo.me/v2.0/article"
# Trần của Zalo cho Bài viết thường (tài liệu Article API): tiêu đề 150, tác giả 50,
# mô tả 300 ký tự. Ảnh mỗi tấm tối đa 1 MB.
ZL_TRAN_TIEU_DE = 150
ZL_TRAN_MO_TA = 300
ZL_TAC_GIA = "The Vagabond Pâtisserie"
ZL_ANH_TOI_DA_BYTE = 1000 * 1000
# Lỗi Zalo hay gặp -> việc cần làm. -212: ứng dụng chưa được duyệt API này.
# -216, -124, -14010: token hỏng hay hết hạn.
ZL_LOI_CHUA_DUYET = (-212,)
ZL_LOI_TOKEN = (-216, -124, -14010, -220)

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


# v672 Thương hiệu: mỗi thương hiệu một bộ ô Cài đặt. tok_chung: ô token dùng thay khi
# ô token riêng trống (khi đó phải có mã Trang).
HIEU_VGB = "vagabond"
HIEU_SO = "sonneto"
HIEU = {
	HIEU_VGB: {"ten": "The Vagabond", "tok": "mxh_token", "trang": "mxh_page_id", "th": "th_token",
		"th_het": "th_het_han", "th_luc": "th_gia_han_luc", "zl": True, "tok_chung": ""},
	HIEU_SO: {"ten": "Sonneto", "tok": "so_mxh_token", "trang": "so_page_id", "th": "so_th_token",
		"th_het": "so_th_het_han", "th_luc": "so_th_gia_han_luc", "zl": False, "tok_chung": "mxh_token"},
}

# Threads: trần một bài 500 ký tự (tài liệu Meta). Đếm theo đơn vị UTF-16 cho an toàn
# với biểu tượng cảm xúc; chừa chỗ cho số thứ tự "2/3" ở cuối mỗi phần.
TH_TRAN_PHAN = 500
TH_TOI_DA_PHAN = 10
TH_CHUA_SO = 8


def chuan_hieu(h):
	"""THUẦN: mã thương hiệu từ giá trị lưu ("Sonneto", "sonneto", "", None)."""
	return HIEU_SO if str(h or "").strip().lower().startswith("sonneto") else HIEU_VGB


def nguon_fb(hieu, tok_rieng, tok_chung, ma_trang, ma_trang_vgb=""):
	"""THUẦN: (token, mã Trang, câu lỗi) để đăng Facebook, Instagram của thương hiệu.

	Vagabond: token của mình, mã Trang có thì chọn đúng Trang đó. Sonneto: token riêng
	nếu có; trống thì mượn token Vagabond nhưng BẮT BUỘC có Mã Trang Sonneto, và Mã Trang
	Sonneto không được trùng Mã Trang Vagabond."""
	ma = "".join(ch for ch in str(ma_trang or "") if ch.isdigit())
	ma_v = "".join(ch for ch in str(ma_trang_vgb or "") if ch.isdigit())
	if chuan_hieu(hieu) == HIEU_VGB:
		if not tok_rieng:
			return None, ma, "Chưa có token Facebook, Instagram ở Cài đặt lõi và API. Đăng tay bài này."
		return tok_rieng, ma, ""
	if ma and ma == ma_v:
		return None, ma, "Mã Trang Facebook Sonneto đang trùng Mã Trang The Vagabond. Sửa ô Mã Trang Facebook Sonneto ở Cài đặt lõi và API."
	if tok_rieng:
		return tok_rieng, ma, ""
	if not tok_chung:
		return None, ma, "Chưa nối kênh Sonneto. Quản trị hệ thống điền mục Đăng bài kênh Sonneto ở Cài đặt lõi và API."
	if not ma:
		return None, ma, "Chưa điền Mã Trang Facebook Sonneto ở Cài đặt lõi và API, nên hệ thống chưa biết Trang nào là của Sonneto."
	return tok_chung, ma, ""


def dai_th(s):
	"""THUẦN: độ dài theo cách đếm an toàn của Threads (biểu tượng cảm xúc tính 2)."""
	return len(str(s or "").encode("utf-16-le")) // 2


def _diem_cat(s, han):
	"""Vị trí cắt trong s để phần đầu dài không quá han: ưu tiên chỗ hết đoạn, rồi xuống
	dòng, rồi hết câu, rồi khoảng trắng. Không cắt quá sớm (dưới 40% han)."""
	dau = 0
	n = 0
	for i, ch in enumerate(s):
		n += 2 if ord(ch) > 0xFFFF else 1
		if n > han:
			break
		dau = i + 1
	khuc = s[:dau]
	san = int(han * 0.4)
	for mau in ("\n\n", "\n"):
		i = khuc.rfind(mau)
		if i >= san:
			return i + len(mau)
	tot = -1
	for m in re.finditer(r"[.!?…:;](?=\s)", khuc):
		tot = m.end()
	if tot >= san:
		return tot
	i = khuc.rfind(" ")
	if i >= san:
		return i + 1
	return dau or 1


def tach_threads(chu, tran=TH_TRAN_PHAN):
	"""THUẦN: chia chữ Threads thành các bài nối tiếp, mỗi bài không quá `tran` ký tự.
	Chữ vừa một bài thì giữ nguyên. Nhiều bài thì cắt ở chỗ hết đoạn, xuống dòng hoặc hết
	câu, mỗi phần có số thứ tự "1/3" ở cuối. Ghép các phần (bỏ số) ra lại đúng chữ."""
	chu = str(chu or "").strip()
	if not chu:
		return []
	if dai_th(chu) <= tran:
		return [chu]
	han = tran - TH_CHUA_SO
	phan, con = [], chu
	while con:
		if dai_th(con) <= han:
			phan.append(con)
			break
		cat = _diem_cat(con, han)
		dau = con[:cat].rstrip()
		if dau:
			phan.append(dau)
		con = con[cat:].lstrip()
	n = len(phan)
	return ["%s\n\n%d/%d" % (p, i + 1, n) for i, p in enumerate(phan)]


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


def loi_zalo_de_hieu(tra):
	"""Câu lỗi Zalo -> việc cần làm. THUẦN."""
	tra = tra if isinstance(tra, dict) else {}
	try:
		ma = int(tra.get("error") or 0)
	except (TypeError, ValueError):
		ma = 0
	goc = str(tra.get("message") or "").strip()
	if ma in ZL_LOI_CHUA_DUYET:
		return ("Zalo chưa duyệt quyền đăng bài viết cho ứng dụng. Quản trị hệ thống vào Zalo for Developers, "
			"mục Article API, bấm Nộp xét duyệt; trong lúc chờ thì đăng tay.")
	if ma in ZL_LOI_TOKEN:
		return "Mã kết nối Zalo OA đã hết hạn hoặc bị thu hồi. Báo quản trị hệ thống cấp lại quyền cho ứng dụng Zalo."
	return "Zalo OA từ chối bài (mã %s%s). Sửa theo câu báo rồi Thử lại, hoặc đăng tay." % (ma, (": " + goc[:200]) if goc else "")


def than_bai_zalo(tieu_de, chu, urls, tac_gia=ZL_TAC_GIA):
	"""Thân yêu cầu tạo Bài viết thường trên Zalo OA. THUẦN.

	Ảnh đầu làm ảnh bìa; chữ chia đoạn theo dòng trống; ảnh đặt sau chữ theo thứ tự
	của bài. Mô tả là đoạn đầu, gọn trong 300 ký tự (Zalo hiện ở thẻ bài)."""
	urls = [u for u in (urls or []) if u]
	if not urls:
		raise LoiDang("Bài viết Zalo OA cần ít nhất một ảnh làm ảnh bìa.")
	td = " ".join(str(tieu_de or "").split())
	if not td:
		raise LoiDang("Bài viết Zalo OA chưa có tiêu đề. Viết tiêu đề cho kênh Zalo OA rồi Thử lại.")
	chu = str(chu or "").replace("\r\n", "\n").strip()
	doan = [d.strip() for d in chu.split("\n\n") if d.strip()]
	mo_ta = " ".join((doan[0] if doan else td).split())
	if len(mo_ta) > ZL_TRAN_MO_TA:
		mo_ta = mo_ta[:ZL_TRAN_MO_TA - 1].rstrip() + "…"
	than = [{"type": "text", "content": d} for d in doan]
	than += [{"type": "image", "url": u} for u in urls]
	return {"type": "normal", "title": td[:ZL_TRAN_TIEU_DE], "author": str(tac_gia or "")[:50],
		"cover": {"cover_type": "photo", "photo_url": urls[0], "status": "show"},
		"description": mo_ta, "body": than, "status": "show", "comment": "show"}


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


def _khoa_cache(hieu):
	return KHOA_CACHE if chuan_hieu(hieu) == HIEU_VGB else KHOA_CACHE + ":" + chuan_hieu(hieu)


def _trang_hieu(c, hieu):
	"""Trang Facebook (kèm Instagram) của thương hiệu. Lỗi thì ném LoiDang."""
	h = HIEU[chuan_hieu(hieu)]
	tok, ma, loi = nguon_fb(hieu, _khoa(c, h["tok"]), _khoa(c, h["tok_chung"]) if h["tok_chung"] else "",
		c.get(h["trang"]), c.get("mxh_page_id"))
	if not tok:
		raise LoiDang(loi)
	return _trang_cua_token(tok, ma)


def trang_thai(lam_moi=False, hieu=HIEU_VGB):
	"""Kết nối từng kênh của một thương hiệu cho màn (không chứa token). Đọc Meta tối đa
	10 phút một lần."""
	hieu = chuan_hieu(hieu)
	h = HIEU[hieu]
	if not lam_moi:
		try:
			c = frappe.cache().get_value(_khoa_cache(hieu))
			if c:
				return c
		except Exception:
			pass
	c = _cfg()
	ra = {"fb": {"ok": 0, "chu": "Chưa nối. Bài lên Facebook phải đăng tay."},
		"ig": {"ok": 0, "chu": "Chưa nối. Bài lên Instagram phải đăng tay."},
		"th": {"ok": 0, "chu": "Chưa nối. Bài lên Threads phải đăng tay."},
		"zl": {"ok": 0, "chu": "Chưa nối Zalo OA. Bài lên Zalo OA phải đăng tay." if h["zl"] else "Sonneto chưa có Zalo OA."}}
	co_fb = _khoa(c, h["tok"]) or (h["tok_chung"] and (c.get(h["trang"]) or "").strip())
	if co_fb:
		try:
			t = _trang_hieu(c, hieu)
			ra["fb"] = {"ok": 1, "chu": "Tự đăng lên Trang %s" % t["ten"]}
			if t.get("ig"):
				ra["ig"] = {"ok": 1, "chu": "Tự đăng lên @%s" % (t["ig"].get("username") or t["ig"].get("id"))}
			else:
				ra["ig"] = {"ok": 0, "chu": "Trang chưa nối tài khoản Instagram doanh nghiệp. Bài lên Instagram phải đăng tay."}
		except LoiDang as e:
			ra["fb"] = {"ok": 0, "chu": e.chu, "loi": 1}
			ra["ig"] = {"ok": 0, "chu": "Chưa nối được vì token Facebook lỗi.", "loi": 1}
	th = _khoa(c, h["th"])
	if th:
		try:
			me = _goi("GET", THREADS + "/me", th, params={"fields": "id,username"}, ten_kenh="Threads")
			het = str(c.get(h["th_het"]) or "")[:10]
			ra["th"] = {"ok": 1, "chu": "Tự đăng lên @%s%s" % (me.get("username") or me.get("id"),
				(" · token dùng tới %s/%s/%s" % (het[8:10], het[5:7], het[:4])) if het else "")}
		except LoiDang as e:
			ra["th"] = {"ok": 0, "chu": e.chu, "loi": 1}
	if h["zl"] and _zl_co_cau_hinh(c):
		try:
			_goi_zl("GET", "getslice", _zl_token(c), params={"offset": 0, "limit": 1, "type": "normal"})
			ra["zl"] = {"ok": 1, "chu": "Tự đăng Bài viết lên trang Zalo OA"}
		except LoiDang as e:
			ra["zl"] = {"ok": 0, "chu": e.chu, "loi": 1}
	try:
		frappe.cache().set_value(_khoa_cache(hieu), ra, expires_in_sec=SONG_CACHE_GIAY)
	except Exception:
		pass
	return ra


def kenh_noi(lam_moi=False, hieu=HIEU_VGB):
	"""Tập mã kênh đang tự đăng được của thương hiệu."""
	return set(k for k, v in trang_thai(lam_moi, hieu).items() if v.get("ok"))


def xoa_cache():
	for h in HIEU:
		try:
			frappe.cache().delete_value(_khoa_cache(h))
		except Exception:
			pass


# ---------- ảnh

def _noi_dung_anh(url):
	ten = frappe.db.get_value("File", {"file_url": url}, "name")
	if not ten:
		raise LoiDang("Không đọc được ảnh %s. Tải lại ảnh vào bài." % url)
	return frappe.get_doc("File", ten).get_content()


def anh_jpeg(url, khung=None, tran_byte=None):
	"""Ảnh của bài thành JPEG; có khung thì cắt giữa đúng khung (như màn xem trước ghi
	"Ảnh cắt tự động"). Instagram chỉ nhận JPEG."""
	import io
	from PIL import Image, ImageOps
	goc = _noi_dung_anh(url)
	with Image.open(io.BytesIO(goc)) as im:
		# Ảnh điện thoại ghi hướng xoay trong EXIF: xoay đúng chiều TRƯỚC khi cắt, như
		# màn xem trước (trình duyệt tự xoay theo EXIF). Bỏ bước này thì ảnh lên kênh bị
		# nằm ngang và vùng cắt lệch (Codex #576).
		im = ImageOps.exif_transpose(im).convert("RGB")
		if khung:
			hop = hop_cat(im.size[0], im.size[1], khung)
			if hop:
				im = im.crop(hop)
		ra = io.BytesIO()
		im.save(ra, "JPEG", quality=92)
		# Zalo OA nhận ảnh tối đa 1 MB: thu nhỏ dần tới khi lọt trần.
		while tran_byte and ra.tell() > tran_byte and min(im.size) > 320:
			im = im.resize((int(im.size[0] * .8), int(im.size[1] * .8)), Image.LANCZOS)
			ra = io.BytesIO()
			im.save(ra, "JPEG", quality=85)
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
	"""Đăng Threads. Chữ quá 500 ký tự thành chuỗi bài nối tiếp: phần đầu mang ảnh, mỗi
	phần sau trả lời phần ngay trước. Trả (mã bài đầu, link bài đầu, ghi chú). Ghi chú
	khác rỗng khi phần đầu đã lên mà có phần sau chưa lên (không ném lỗi, kẻo bị đăng lại
	phần đầu)."""
	ten = "Threads"
	tao = lambda d: _goi("POST", THREADS + "/me/threads", tok, data=d, ten_kenh=ten).get("id")
	url = lambda a: url_cong_khai(ma_bai, anh_jpeg(a["url"], a["khung"] if a.get("cat") else None))
	phan = tach_threads(chu) or [""]
	dau = phan[0]
	if not anh:
		c = tao({"media_type": "TEXT", "text": dau})
	elif len(anh) == 1:
		c = tao({"media_type": "IMAGE", "image_url": url(anh[0]), "text": dau})
	else:
		con = [tao({"media_type": "IMAGE", "image_url": url(a), "is_carousel_item": "true"}) for a in anh]
		for m in con:
			_cho_xong(THREADS, m, tok, "status", "FINISHED", ("ERROR", "EXPIRED"), ten)
		c = tao({"media_type": "CAROUSEL", "children": ",".join(con), "text": dau})
	_cho_xong(THREADS, c, tok, "status", "FINISHED", ("ERROR", "EXPIRED"), ten)
	r = _goi("POST", THREADS + "/me/threads_publish", tok, data={"creation_id": c}, cong_bo=True, ten_kenh=ten)
	ma = str(r.get("id") or "")
	link = _link(THREADS, ma, "permalink", tok, ten) if ma else ""
	truoc, ghi = ma, ""
	for i, p in enumerate(phan[1:], 2):
		try:
			c2 = tao({"media_type": "TEXT", "text": p, "reply_to_id": truoc})
			_cho_xong(THREADS, c2, tok, "status", "FINISHED", ("ERROR", "EXPIRED"), ten)
			r2 = _goi("POST", THREADS + "/me/threads_publish", tok, data={"creation_id": c2}, cong_bo=True, ten_kenh=ten)
			truoc = str(r2.get("id") or "") or truoc
		except LoiDang as e:
			ghi = ("Phần 1 đã lên Threads nhưng phần %d/%d chưa %s (%s). Mở Threads, đăng tay tiếp từ phần %d"
				" bằng cách trả lời bài vừa lên.") % (i, len(phan), "rõ đã lên chưa" if not e.ro else "lên", e.chu, i)
			if "thiếu quyền" in e.chu:
				ghi += " Token Threads cần quyền threads_manage_replies để tự đăng bài nối tiếp."
			break
	return ma, link, ghi


def _zl_co_cau_hinh(c):
	return bool((c.get("zalo_app_id") or "").strip() and _khoa(c, "zalo_app_secret") and _khoa(c, "zalo_refresh_token"))


def _zl_token(c):
	"""Mã truy cập OA (tự làm mới bằng refresh token, dùng chung với tin ZNS và OA)."""
	from vagabond import zalo
	if frappe.flags.get("vagabond_kiem_that"):
		raise LoiDang("Đang chạy kiểm thử: không đăng thật lên Zalo OA.")
	try:
		return zalo.token(c)
	except Exception as e:
		frappe.log_error(title="Bài đăng: Zalo không cấp mã", message=frappe.get_traceback())
		raise LoiDang("Chưa lấy được mã kết nối Zalo OA (%s). Báo quản trị hệ thống kiểm mục Zalo OA trong Cài đặt." % str(e)[:150])


def _goi_zl(phuong_thuc, duong, tok, than=None, params=None, cong_bo=False):
	"""Một lần gọi Article API của Zalo. Trả dict khi thành công; ném LoiDang khi không."""
	ten = "Zalo OA"
	if frappe.flags.get("vagabond_kiem_that"):
		raise LoiDang("Đang chạy kiểm thử: không đăng thật lên Zalo OA.")
	if requests is None:
		raise LoiDang("Máy chủ thiếu thư viện gọi mạng, báo quản trị hệ thống.")
	try:
		r = requests.request(phuong_thuc, "%s/%s" % (ZALO_BAI, duong), params=params, timeout=TIMEOUT,
			headers={"access_token": tok, "Content-Type": "application/json"},
			data=json.dumps(than, ensure_ascii=False).encode("utf-8") if than is not None else None)
	except Exception:
		from vagabond.lib import giau_khoa
		frappe.log_error(title="Bài đăng: lỗi mạng khi gọi Zalo OA", message=giau_khoa(frappe.get_traceback()))
		if cong_bo:
			raise LoiDang("Mất kết nối lúc công bố bài lên %s, chưa rõ bài đã lên chưa. Mở trang Zalo OA kiểm: đã có bài thì bấm Đã đăng, chưa có thì bấm Thử lại." % ten, ro=False)
		raise LoiDang("Chưa gọi được %s (mất kết nối). Bấm Thử lại sau ít phút." % ten)
	try:
		tra = r.json() if r.content else {}
	except ValueError:
		tra = {}
	tra = tra if isinstance(tra, dict) else {}
	if r.status_code >= 400 or tra.get("error"):
		raise LoiDang(loi_zalo_de_hieu(tra))
	return tra


def dang_zl(ma_bai, tieu_de, chu, anh):
	"""Tạo Bài viết trên trang Zalo OA. Zalo trả mã tiến trình, hỏi lại tới khi có mã bài."""
	c = _cfg()
	if not _zl_co_cau_hinh(c):
		raise LoiDang("Chưa nối Zalo OA (thiếu App ID, App Secret hoặc Refresh Token ở mục Zalo OA). Đăng tay bài này.")
	tok = _zl_token(c)
	urls = [url_cong_khai(ma_bai, anh_jpeg(a["url"], a["khung"] if a.get("cat") else None, ZL_ANH_TOI_DA_BYTE)) for a in (anh or [])]
	than = than_bai_zalo(tieu_de, chu, urls)
	tao = _goi_zl("POST", "create", tok, than=than, cong_bo=True)
	tien_trinh = str(((tao.get("data") or {}).get("token")) or "")
	if not tien_trinh:
		raise LoiDang("Zalo OA đã nhận bài nhưng không trả mã tiến trình, chưa rõ bài đã lên chưa. Mở trang Zalo OA kiểm trước khi đăng lại.", ro=False)
	het = time.time() + CHO_XU_LY_GIAY
	while True:
		try:
			v = _goi_zl("POST", "verify", tok, than={"token": tien_trinh})
		except LoiDang as e:
			raise LoiDang("Zalo OA đã nhận bài nhưng chưa xác nhận (%s). Mở trang Zalo OA kiểm trước khi đăng lại." % e.chu, ro=False)
		ma = str(((v.get("data") or {}).get("id")) or "")
		if ma:
			return ma, ""
		if time.time() > het:
			raise LoiDang("Zalo OA xử lý bài quá lâu, chưa rõ bài đã lên chưa. Mở trang Zalo OA kiểm trước khi đăng lại.", ro=False)
		time.sleep(NHIP_HOI_GIAY)


def dang(kenh, ma_bai, chu, anh, story=False, tieu_de="", hieu=HIEU_VGB):
	"""Đăng một kênh của một thương hiệu. Trả (mã bài trên kênh, link) hoặc (mã, link,
	ghi chú) với Threads nhiều phần. Lỗi thì ném LoiDang."""
	c = _cfg()
	h = HIEU[chuan_hieu(hieu)]
	if kenh in ("fb", "ig"):
		trang = _trang_hieu(c, hieu)
		if kenh == "fb":
			return dang_fb(trang, chu, anh, story)
		return dang_ig(ma_bai, trang, chu, anh, story)
	if kenh == "th":
		tok = _khoa(c, h["th"])
		if not tok:
			raise LoiDang("Chưa có token Threads%s ở Cài đặt lõi và API. Đăng tay bài này." % ("" if h["zl"] else " " + h["ten"]))
		return dang_th(ma_bai, tok, chu, anh)
	if kenh == "zl" and not story and h["zl"]:
		return dang_zl(ma_bai, tieu_de, chu, anh)
	raise LoiDang("Kênh này đăng tay.")


def gia_han_threads():
	"""Nhịp mỗi ngày: token Threads (mỗi thương hiệu một token) sống 60 ngày, gia hạn khi
	đã quá 6 ngày từ lần trước (Meta chỉ cho gia hạn token đã quá 24 giờ). Lỗi thì ghi
	Error Log, hôm sau thử lại; một thương hiệu lỗi không chặn thương hiệu kia."""
	for hieu in HIEU:
		_gia_han_mot(hieu)


def _gia_han_mot(hieu):
	h = HIEU[hieu]
	try:
		from datetime import timedelta
		from frappe.utils import now_datetime, get_datetime
		from frappe.utils.password import set_encrypted_password
		c = _cfg()
		tok = _khoa(c, h["th"])
		if not tok:
			return
		luc = c.get(h["th_luc"])
		if luc and get_datetime(luc) > now_datetime() - timedelta(days=GIA_HAN_SAU_NGAY):
			return
		tra = _goi("GET", THREADS_GOC + "/refresh_access_token", tok, params={"grant_type": "th_refresh_token"}, ten_kenh="Threads")
		moi = tra.get("access_token")
		if not moi:
			return
		set_encrypted_password("Vagabond Settings", "Vagabond Settings", moi, h["th"])
		bay_gio = now_datetime()
		frappe.db.set_single_value("Vagabond Settings", h["th_luc"], bay_gio)
		try:
			giay = int(tra.get("expires_in") or 0)
		except (TypeError, ValueError):
			giay = 0
		if giay:
			frappe.db.set_single_value("Vagabond Settings", h["th_het"], (bay_gio + timedelta(seconds=giay)).strftime("%Y-%m-%d"))
		frappe.db.commit()
		xoa_cache()
	except LoiDang as e:
		frappe.log_error(title="Bài đăng: chưa gia hạn được token Threads %s" % h["ten"], message=e.chu)
	except Exception:
		from vagabond.lib import giau_khoa
		frappe.log_error(title="Bài đăng: chưa gia hạn được token Threads %s" % h["ten"], message=giau_khoa(frappe.get_traceback()))
