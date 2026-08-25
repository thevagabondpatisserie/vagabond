"""Gui tin WhatsApp Business qua WhatsApp Cloud API cua Meta.

Anh Viet 07/08/2026: "Whatsapp Business co lam duoc khong thi lam them".

Noi thang truoc khi dung: khach Viet gan nhu khong dung WhatsApp, Zalo moi la
kenh chinh. Kenh nay dang de danh cho khach nuoc ngoai va khach o nuoc ngoai
dat banh gui ve. Vi vay he thong LUON gui Zalo truoc, chi gui WhatsApp khi
duoc yeu cau ro hoac khi Zalo tu choi.

Dieu kien de chay duoc, anh chi phai lam ben Meta Business:
1. Co tai khoan WhatsApp Business (WABA) va mot so dien thoai da xac thuc.
2. Lay Phone Number ID cua so do.
3. Tao mot System User token vinh vien co quyen whatsapp_business_messaging.
4. Tao mau tin (message template) loai UTILITY va cho Meta duyet. Mau phai co
   dung 3 tham so trong than tin theo thu tu: ma don, so tien, duong dan.

Ngoai cua so 24 tieng ke tu tin cuoi cua khach, Meta CHI cho gui tin theo mau
da duyet - khong gui duoc tin tu do. Nen bat buoc phai co mau.
"""

import json

import frappe
import requests

from vagabond.lib import TIMEOUT, key

GRAPH = "https://graph.facebook.com/v21.0"


def gui_mau(c, sdt84, ten_mau, tham_so, ngon_ngu=None):
	"""Gui mot tin theo mau da duyet. Tra ve (thanh_cong, loi).

	sdt84 dang 84xxxxxxxxx, khong dau cong - Meta nhan ca hai nhung de mot
	kieu cho khoi lech khi doi chieu.
	"""
	# Cung cai chan nhu ben Zalo, them 25/08/2026. `thanh_toan.py` goi CA HAI
	# duong cho mot tin yeu cau thanh toan, nen chan mot ben ma bo ben kia
	# thi ca kiem tich hop van ban tin that ra dien thoai khach that.
	#
	# Diem luu cua co so du lieu lui lai duoc mot chung tu ao. No khong lui
	# lai duoc mot tin nhan da toi tay nguoi ta.
	if frappe.flags.get("vagabond_kiem_that"):
		return False, "Dang chay kiem thu tich hop nen khong gui WhatsApp"
	phone_id = (c.get("wa_phone_id") or "").strip()
	tok = key(c, "wa_token")
	if not (phone_id and tok):
		return False, "Chưa điền Phone Number ID hoặc token WhatsApp trong Vagabond Settings"
	if not ten_mau:
		return False, "Chưa khai tên mẫu tin WhatsApp trong Vagabond Settings"

	than = {
		"messaging_product": "whatsapp",
		"to": str(sdt84),
		"type": "template",
		"template": {
			"name": ten_mau,
			"language": {"code": (ngon_ngu or c.get("wa_ngon_ngu") or "vi").strip()},
			"components": [
				{
					"type": "body",
					"parameters": [{"type": "text", "text": str(v)} for v in (tham_so or [])],
				}
			],
		},
	}
	try:
		r = requests.post(
			"%s/%s/messages" % (GRAPH, phone_id),
			headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
			json=than,
			timeout=TIMEOUT,
		)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: WhatsApp loi mang", message=frappe.get_traceback())
		return False, "Không gọi được WhatsApp"

	if r.status_code not in (200, 201) or j.get("error"):
		frappe.log_error(title="Vagabond: WhatsApp tu choi tin", message=json.dumps(j)[:1000])
		loi = (j.get("error") or {}).get("message") or "WhatsApp từ chối tin"
		return False, loi
	return True, ""
