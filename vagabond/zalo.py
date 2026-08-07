"""Gui tin Zalo ZNS qua Zalo OA.

Tach rieng khoi dang_nhap.py vi tu 06/08/2026 co hai cho dung: ma dang nhap
cho khach, va tin yeu cau thanh toan sau khi sales chot duoc don.

ZNS gui duoc toi moi so dien thoai, khach KHONG can quan tam OA - do chinh la
ly do chon kenh nay thay cho cach goi dien roi xin ket ban Zalo.
"""

import json

import frappe
import requests
from frappe.utils import now_datetime

from vagabond.lib import TIMEOUT, key

ZALO_OA = "https://business.openapi.zalo.me"
ZALO_OAUTH = "https://oauth.zaloapp.com/v4/oa/access_token"


def token(c):
	"""Access token cua OA, tu lam moi bang refresh token khi het han.

	Zalo cap access token song 1 tieng, refresh token song 3 thang. Moi lan lam
	moi Zalo tra ve refresh token MOI va huy cai cu, nen bat buoc ghi de lai
	vao cau hinh - quen ghi la lan sau het duong lam moi.
	"""
	from datetime import timedelta

	tok = key(c, "zalo_access_token")
	han = c.get("zalo_token_het_han")
	if tok and han and now_datetime() < han:
		return tok

	app_id = (c.get("zalo_app_id") or "").strip()
	bi_mat = key(c, "zalo_app_secret")
	refresh = key(c, "zalo_refresh_token")
	if not (app_id and bi_mat and refresh):
		frappe.throw("Chưa điền App ID, App Secret hoặc Refresh Token của Zalo OA trong Vagabond Settings")

	r = requests.post(
		ZALO_OAUTH,
		headers={"secret_key": bi_mat, "Content-Type": "application/x-www-form-urlencoded"},
		data={"app_id": app_id, "refresh_token": refresh, "grant_type": "refresh_token"},
		timeout=TIMEOUT,
	)
	j = r.json() if r.content else {}
	tok = j.get("access_token")
	if not tok:
		frappe.log_error(title="Vagabond: Zalo khong cap token", message=json.dumps(j)[:1000])
		frappe.throw("Zalo không cấp được token, nhờ anh chị kiểm tra lại cấu hình Zalo OA")

	doc = frappe.get_doc("Vagabond Settings")
	doc.zalo_access_token = tok
	if j.get("refresh_token"):
		doc.zalo_refresh_token = j["refresh_token"]
	try:
		song = int(j.get("expires_in") or 3600)
	except (TypeError, ValueError):
		song = 3600
	doc.zalo_token_het_han = now_datetime() + timedelta(seconds=max(300, song - 300))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return tok


def gui_tin(c, sdt84, template_id, du_lieu, dau_vet=None):
	"""Gui mot tin ZNS. Tra ve (thanh_cong, loi).

	KHONG nem loi ra ngoai khi Zalo tu choi - cho ben goi tu quyet dinh, vi co
	cho chi can bao "khong gui duoc" chu khong duoc lam hong ca nghiep vu.
	"""
	if not template_id:
		return False, "Chưa khai mã mẫu ZNS trong Vagabond Settings"
	try:
		tok = token(c)
	except Exception as e:
		return False, str(e)
	try:
		r = requests.post(
			"%s/message/template" % ZALO_OA,
			headers={"access_token": tok, "Content-Type": "application/json"},
			json={
				"phone": sdt84,
				"template_id": template_id,
				"template_data": du_lieu,
				"tracking_id": dau_vet or ("vgb-%s" % sdt84),
			},
			timeout=TIMEOUT,
		)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: ZNS loi mang", message=frappe.get_traceback())
		return False, "Không gọi được Zalo"
	if j.get("error") not in (0, None):
		frappe.log_error(title="Vagabond: ZNS khong gui duoc", message=json.dumps(j)[:1000])
		return False, j.get("message") or "Zalo từ chối tin"
	return True, ""
