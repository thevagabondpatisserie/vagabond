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


# --------------------------------------------------------------- CHẠM HỆ

def _ban_site():
	try:
		with open(frappe.get_app_path("vagabond", "patches.txt"), encoding="utf-8") as f:
			return so_ban(f.read())
	except Exception:
		return 0


def _doc_comment():
	from frappe.utils import add_days, now_datetime
	import requests

	tu = add_days(now_datetime(), -LUI_NGAY).strftime("%Y-%m-%dT%H:%M:%SZ")
	r = requests.get(API, params={"since": tu, "sort": "updated", "direction": "desc", "per_page": 100},
		headers={"Accept": "application/vnd.github+json"}, timeout=TIMEOUT)
	r.raise_for_status()
	ds = r.json()
	return ds if isinstance(ds, list) else []


def quet():
	"""Nhịp 15 phút. Tắt bot Zalo thì không gọi GitHub. Lỗi mạng chỉ ghi Error
	Log, nhịp sau thử lại; không bao giờ ném ra ngoài."""
	from vagabond import kenh_zalo

	if getattr(frappe.flags, "vagabond_kiem_that", False) or not kenh_zalo._bat():
		return 0
	ban = _ban_site()
	if not ban:
		return 0
	try:
		cac = _doc_comment()
	except Exception:
		frappe.log_error("Chưa đọc được bản tin phát hành trên GitHub.", "zalo_phat_hanh: doc loi")
		return 0
	gui = 0
	for x in chon_ban(cac, ban):
		kenh_zalo.bao("phat_hanh", "phat_hanh", "Vagabond cập nhật %s, đã lên app" % x["version"],
			dong=[d.strip() for d in x["features"]], khoa="phat_hanh:" + x["sha"])
		gui += 1
	if gui:
		frappe.db.commit()
	return gui
