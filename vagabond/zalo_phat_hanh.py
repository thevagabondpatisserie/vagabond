# -*- coding: utf-8 -*-
"""v585: bản tin phát hành vào nhóm Zalo.

Anh Việt 07/10/2026: đã cài nhóm Zalo nhận loại tin Phát hành mà không thấy
tin nào. Nguyên nhân: bản tin phát hành chỉ có đường Telegram (bot GitHub đọc
comment [ĐÃ DEPLOY]); trong app không chỗ nào gọi kenh_zalo.bao("phat_hanh").

Cách làm: dùng ĐÚNG nguồn của Telegram để hai kênh không lệch nhau. Mỗi 15
phút site đọc comment mới trên GitHub (repo công khai, không cần khoá), lấy
khối `telegram-release` do chủ repo đăng sau khi đã kiểm site thật, rồi gọi
kenh_zalo.bao. Luật đọc khối giống hệt .github/telegram/thong_bao.py.

Chỉ báo bản đang chạy trên site (số cuối của patches.txt): comment cũ của các
bản trước không bao giờ bị bắn lại, kể cả lần đầu bật. Chống trùng bằng khoá
"phat_hanh:<sha>" của kenh_zalo (mỗi nhóm một lần).
"""

import json
import re
from datetime import datetime, timedelta, timezone

import frappe

REPO = "thevagabondpatisserie/vagabond"
API = "https://api.github.com/repos/%s/issues/comments" % REPO
LUI_NGAY = 3
TIMEOUT = 10


# ------------------------------------------------------------------ THUẦN

def ban_phat_hanh(c, chu=REPO.split("/")[0]):
	"""THUẦN: khối telegram-release hợp lệ của một comment, hoặc None.
	Cùng luật với .github/telegram/thong_bao.py: chủ repo, dòng đầu đúng
	[ĐÃ DEPLOY], đúng một khối, đủ bốn khoá, đã kiểm site thật."""
	body = (c or {}).get("body") or ""
	dong = body.splitlines()
	if ((c.get("user") or {}).get("login") != chu or c.get("author_association") != "OWNER"
			or not dong or dong[0].strip() != "[ĐÃ DEPLOY]"):
		return None
	khoi = re.findall(r"<!-- telegram-release\s*([\s\S]*?)-->", body)
	if len(khoi) != 1 or len(khoi[0]) > 3000:
		return None
	try:
		x = json.loads(khoi[0])
	except (ValueError, TypeError):
		return None
	if not isinstance(x, dict) or set(x) != {"version", "sha", "features", "live_verified"}:
		return None
	if (x["live_verified"] is not True or not isinstance(x["version"], str)
			or not re.fullmatch(r"v[1-9][0-9]{0,7}", x["version"])
			or not isinstance(x["sha"], str) or not re.fullmatch(r"[0-9a-f]{40}", x["sha"])):
		return None
	f = x["features"]
	if (not isinstance(f, list) or not 1 <= len(f) <= 5
			or any(not isinstance(d, str) or not d.strip() or len(d) > 220
				or any(ord(ch) < 32 for ch in d) for d in f)):
		return None
	return x


def so_ban(patches):
	"""THUẦN: số phiên bản lớn nhất ghi trong patches.txt (dấu #vNNN), 0 nếu không có."""
	so = [int(m) for m in re.findall(r"#v(\d+)\s*$", patches or "", re.M)]
	return max(so) if so else 0


def chon_ban(cac_comment, ban_site):
	"""THUẦN: các bản tin của ĐÚNG bản đang chạy trên site, mỗi sha một bản
	(comment sửa sau cùng thắng). Bản trước hay bản chưa lên site thì bỏ."""
	ra = {}
	for c in sorted(cac_comment or [], key=lambda c: c.get("updated_at") or ""):
		x = ban_phat_hanh(c)
		if x and int(x["version"][1:]) == ban_site:
			ra[x["sha"]] = x
	return list(ra.values())


def gom_trang(lay, co=100, toi_da=10):
	"""THUẦN: gom mọi trang comment, cùng cách GitHub.trang() của bộ gửi
	Telegram. lay(so_trang) trả một danh sách. Dừng khi trang thiếu; quá
	toi_da trang mà vẫn còn thì ném lỗi chứ không lặng lẽ bỏ phần sau.
	Codex #452: chỉ đọc một trang 100 dòng thì biên nhận bị đẩy sang trang 2
	sẽ mất hẳn dù GitHub trả thành công."""
	ket = []
	for so in range(1, toi_da + 1):
		nhom = lay(so)
		if not isinstance(nhom, list):
			raise ValueError("GitHub trả dữ liệu không phải danh sách ở trang %d" % so)
		ket.extend(nhom)
		if len(nhom) < co:
			return ket
	if lay(toi_da + 1):
		raise ValueError("Quá %d comment mới trong %d ngày, chưa đọc hết được." % (co * toi_da, LUI_NGAY))
	return ket


# v643 (còn tồn v604): GitHub cho máy lạ 60 lượt đọc mỗi giờ theo IP, mà IP
# của Frappe Cloud dùng chung nhiều site. Error Log ngày 01/11 có 10 dòng
# "rate limit exceeded" chỉ trong 4 giờ, 07/11 thêm "Read timed out". Đó là
# lỗi TẠM của phía GitHub, nhịp sau tự hết: nghỉ tới giờ GitHub hẹn, chỉ ghi
# Error Log khi lỗi tạm kéo dài quá GIO_BAO_LOI giờ (mỗi ngày một dòng). Bản
# tin của bản đang chạy đã đọc được rồi thì thôi gọi GitHub tới bản sau.
GIO_BAO_LOI = 12
NGHI_TOI_THIEU, NGHI_TOI_DA = 300, 3600


def loi_tam(e):
	"""THUẦN: lỗi mạng hay giới hạn lượt của GitHub, tự hết, không phải hỏng."""
	ten = type(e).__name__
	if ten in ("Timeout", "ReadTimeout", "ConnectTimeout", "ConnectionError"):
		return True
	r = getattr(e, "response", None)
	ma = getattr(r, "status_code", None)
	if ma == 429 or (isinstance(ma, int) and ma >= 500):
		return True
	return ma == 403 and "rate limit" in str(e).lower()


def giay_nghi(headers, bay_gio):
	"""THUẦN: số giây nghỉ trước khi gọi lại GitHub theo X-RateLimit-Reset (giờ
	unix) hoặc Retry-After, kẹp trong [NGHI_TOI_THIEU, NGHI_TOI_DA]."""
	h = {str(k).lower(): v for k, v in (headers or {}).items()}
	try:
		if h.get("retry-after"):
			s = float(h["retry-after"])
		elif h.get("x-ratelimit-reset"):
			s = float(h["x-ratelimit-reset"]) - float(bay_gio)
		else:
			s = NGHI_TOI_THIEU
	except (TypeError, ValueError):
		s = NGHI_TOI_THIEU
	return int(min(max(s, NGHI_TOI_THIEU), NGHI_TOI_DA))


def nen_ghi_loi(loi_tu, bay_gio, gio=GIO_BAO_LOI):
	"""THUẦN: lỗi tạm đã kéo dài đủ lâu để báo kỹ thuật chưa."""
	return float(bay_gio) - float(loi_tu) >= gio * 3600


# --------------------------------------------------------------- CHẠM HỆ

def _ban_site():
	"""Số bản đang chạy. Không đọc được thì NÉM LỖI để quet() ghi Error Log
	(Codex #452: trả 0 lặng lẽ thì kênh tắt mãi mà không ai biết)."""
	with open(frappe.get_app_path("vagabond", "patches.txt"), encoding="utf-8") as f:
		so = so_ban(f.read())
	if not so:
		raise ValueError("patches.txt không có dấu #vNNN nào")
	return so


def moc_utc(bay_gio=None, lui_ngay=LUI_NGAY):
	"""THUẦN: mốc `since` gửi GitHub, theo giờ UTC thật (đuôi Z). Codex #452:
	now_datetime() của Frappe là giờ site (Asia/Ho_Chi_Minh, không kèm múi),
	gắn Z vào thì mốc lệch 7 giờ về sau và cửa sổ 3 ngày hụt mất 7 giờ.
	bay_gio phải có múi giờ; bỏ trống thì lấy giờ UTC hiện tại."""
	bay_gio = bay_gio or datetime.now(timezone.utc)
	if bay_gio.tzinfo is None:
		raise ValueError("moc_utc cần thời điểm có múi giờ")
	return (bay_gio.astimezone(timezone.utc) - timedelta(days=lui_ngay)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _moc():
	return moc_utc()


def _doc_comment():
	import requests

	tu = _moc()

	def lay(so):
		r = requests.get(API, params={"since": tu, "sort": "updated", "direction": "desc",
			"per_page": 100, "page": so}, headers={"Accept": "application/vnd.github+json"}, timeout=TIMEOUT)
		r.raise_for_status()
		return r.json()

	return gom_trang(lay)


def quet():
	"""Nhịp 15 phút. Tắt bot Zalo thì không gọi GitHub. Lỗi mạng chỉ ghi Error
	Log, nhịp sau thử lại; không bao giờ ném ra ngoài."""
	from vagabond import kenh_zalo

	if getattr(frappe.flags, "vagabond_kiem_that", False) or not kenh_zalo._bat():
		return 0
	try:
		ban = _ban_site()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "zalo_phat_hanh: khong doc duoc so ban tren site")
		return 0
	import time

	nho = frappe.cache()
	if nho.get_value("zph_xong:%s" % ban):
		return 0
	bay = time.time()
	nghi = nho.get_value("zph_nghi_den")
	try:
		if nghi and float(nghi) > bay:
			return 0
	except (TypeError, ValueError):
		pass
	try:
		cac = _doc_comment()
	except Exception as e:
		if not loi_tam(e):
			frappe.log_error(frappe.get_traceback(), "zalo_phat_hanh: khong doc duoc ban tin tren GitHub")
			return 0
		s = giay_nghi(getattr(getattr(e, "response", None), "headers", None), bay)
		nho.set_value("zph_nghi_den", bay + s, expires_in_sec=s)
		tu = nho.get_value("zph_loi_tu") or bay
		nho.set_value("zph_loi_tu", tu, expires_in_sec=3 * 86400)
		if nen_ghi_loi(tu, bay) and not nho.get_value("zph_da_bao"):
			nho.set_value("zph_da_bao", "1", expires_in_sec=86400)
			frappe.log_error(frappe.get_traceback(), "zalo_phat_hanh: GitHub tu choi hon %d gio" % GIO_BAO_LOI)
		return 0
	nho.set_value("zph_loi_tu", None, expires_in_sec=1)
	gui = 0
	ben = True
	ban_tin = chon_ban(cac, ban)
	for x in ban_tin:
		khoa = "phat_hanh:" + x["sha"]
		ten = kenh_zalo.bao("phat_hanh", "phat_hanh", "Vagabond cập nhật %s, đã lên app" % x["version"],
			dong=[d.strip() for d in x["features"]], khoa=khoa, ma_tin="ht_phat_hanh")
		gui += 1
		# Codex PR #546 vòng 3: bao() nuốt lỗi ghi và trả rỗng khi không nhóm nào
		# nhận. Chỉ coi là xong khi tin đã nằm trong hộp thư (vừa ghi, hoặc đã có
		# sẵn theo khoá chống trùng); không thì nhịp sau đọc GitHub và ghi lại.
		if not ten and not _da_co_tin(khoa):
			ben = False
	if gui:
		frappe.db.commit()
	if ban_tin and ben:
		# Đã có bản tin của bản đang chạy trong hộp thư: thôi gọi GitHub tới bản sau.
		nho.set_value("zph_xong:%s" % ban, "1", expires_in_sec=7 * 86400)
	return gui


def _da_co_tin(khoa):
	"""Tin của sự kiện khoa đã nằm trong hộp thư Zalo của ít nhất một nhóm nhận
	tin phát hành (tên dòng = khoá chống trùng theo mã chat)."""
	from vagabond import kenh_zalo

	ten = [kenh_zalo.khoa_tin(khoa, n.get("chat_id"))
		for n in kenh_zalo.chon_nhom(kenh_zalo._cac_nhom(), "phat_hanh", "phat_hanh", "ht_phat_hanh")]
	return bool(ten) and bool(frappe.db.exists("Vagabond Tin Kenh", {"name": ["in", ten]}))
