# -*- coding: utf-8 -*-
"""v627: Tài chính đọc được số dư SePay trên site thật.

Anh Việt 01/11/2026 hỏi vì sao màn Tiền hiện có báo "Chưa đọc được SePay"
trong khi Shinhan đã nối SePay. Nguyên nhân: tai_chinh._sepay_so_bao gọi
frappe.make_get_request, hàm chỉ có trong System Console và Server Script.
Mọi ca v626 đều thay _sepay_so_bao bằng bản giả nên hàm thật chưa chạy lần
nào trong kiểm thử (ca che lỗi). Ca dưới chạy HÀM THẬT, frappe giả không có
make_get_request giống frappe thật; chỉ frappe.integrations.utils có.
"""

import json
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]

from vagabond import tai_chinh as tc  # noqa: E402

TRA_SEPAY = {"status": 200, "bankaccounts": [
	{"account_number": "700037279585", "bank_short_name": "ShinhanBank", "accumulated": "242995597.00"},
	{"account_number": "31561568", "bank_short_name": "MBBank", "accumulated": "0.00"},
]}


class _Dem:
	def __init__(self):
		self.d, self.han = {}, {}

	def get_value(self, k):
		return self.d.get(k)

	def set_value(self, k, v, expires_in_sec=None):
		self.d[k], self.han[k] = v, expires_in_sec


def _chay(tra, dem=None, token="tk-thu"):
	goi = []

	def get(url, headers=None, **k):
		goi.append((url, dict(headers or {})))
		if isinstance(tra, Exception):
			raise tra
		return tra
	iu = types.ModuleType("frappe.integrations.utils")
	iu.make_get_request = get
	tich = types.ModuleType("frappe.integrations")
	tich.utils = iu
	dem = dem or _Dem()
	stg = types.SimpleNamespace(get_password=lambda f, raise_exception=False: token if f == "api_token" else "")
	ps = [um.patch.dict(sys.modules, {"frappe.integrations": tich, "frappe.integrations.utils": iu}),
		um.patch.object(_fr, "cache", lambda: dem, create=True),
		um.patch.object(_fr, "get_doc", lambda *a, **k: stg, create=True),
		um.patch.object(_fr, "log_error", lambda *a, **k: None, create=True),
		um.patch.object(_fr, "get_traceback", lambda *a, **k: "", create=True)]
	if hasattr(_fr, "make_get_request"):
		ps.append(um.patch.object(_fr, "make_get_request", None))
	for p in ps:
		p.start()
	try:
		if hasattr(_fr, "make_get_request") and _fr.make_get_request is None:
			delattr(_fr, "make_get_request")
		return tc._sepay_so_bao(), goi, dem
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v627 đọc số dư SePay bằng hàm THẬT (frappe như site thật, không có make_get_request): Shinhan ra 242.995.597 (trước: rỗng, màn báo Chưa đọc được)")
def _doc_that():
	dung("frappe giả không có make_get_request như site thật", not hasattr(_fr, "make_get_request"))
	kq, goi, dem = _chay(TRA_SEPAY)
	la("số dư theo số tài khoản", kq, {"700037279585": 242995597.0, "31561568": 0.0})
	la("gọi đúng một lần, đúng địa chỉ, có khoá", [(u, h.get("Authorization")) for u, h in goi],
		[("https://my.sepay.vn/userapi/bankaccounts/list", "Bearer tk-thu")])
	# v654 Codex #561: kèm khoá giờ đọc của đúng bản số dư đó, cùng hạn 1 phút.
	la("lưu đệm tối đa 1 phút (số dư và giờ đọc)", sorted(dem.han.items()), [("vgb_tc_sepay_so_du", 60), ("vgb_tc_sepay_so_du_luc", 60)])
	# v654 Codex #561 vòng 3: giờ đọc giữ đủ phần lẻ giây, đọc lại đúng nguyên giá trị.
	import datetime as _dt
	luc = _dt.datetime(2026, 11, 13, 9, 30, 0, 250000)
	with um.patch.object(tc, "now_datetime", lambda: luc):
		_kq, _goi, dem2 = _chay(TRA_SEPAY)
	la("giờ đọc đủ phần lẻ giây", dem2.d.get("vgb_tc_sepay_so_du_luc"), "2026-11-13 09:30:00.250000")
	with um.patch.object(_fr, "cache", lambda: dem2, create=True):
		la("đọc lại giờ đọc nguyên giá trị", tc._sepay_luc_bao(), "2026-11-13 09:30:00.250000")
	kq2, goi2, _ = _chay(TRA_SEPAY, dem=dem)
	la("lần mở sau trong 1 phút dùng đệm, không gọi lại", (kq2, len(goi2)), (kq, 0))


@ca("v627 SePay lỗi mạng hoặc trả rỗng: không lưu đệm, lần mở sau đọc lại; chưa có khoá thì không gọi")
def _doc_loi():
	kq, goi, dem = _chay(RuntimeError("Hết thời gian chờ"))
	la("lỗi mạng: rỗng, không lưu đệm", (kq, dem.d), ({}, {}))
	kq, goi, dem = _chay({"status": 200, "bankaccounts": []})
	la("trả rỗng: không lưu đệm", (kq, dem.d), ({}, {}))
	kq, goi, dem = _chay(TRA_SEPAY, token="")
	la("chưa có khoá: không gọi SePay", (kq, len(goi)), ({}, 0))
