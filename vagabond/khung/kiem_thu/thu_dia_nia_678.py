# -*- coding: utf-8 -*-
"""v678: dĩa, nĩa tặng kèm chọn một lần cho cả đơn ở trang Thông tin đơn hàng
(anh Việt 20/11/2026, chọn phương án A: chỉ nhập ở giỏ, dùng món có sẵn
BAPK00020 Dĩa giấy bã mía, BAPK00018 Nĩa gỗ, không theo dõi tồn kho).

Phần trang khách nằm ở hanh_vi/web_vue_banh.mjs và cong_cu/kiem_web_vue_dom.cjs.
Ở đây: máy chủ nhận dòng giá 0, kẹp số, không nhận đơn chỉ có dĩa, nĩa, và
chia giảm giá sang Pancake không làm rơi phần lẻ hay chia cho 0. don_hang kéo
requests ở đầu tệp nên ca nạp hàm thật từ mã nguồn (như ca #367), không import cả mô-đun.
"""

import ast
import json
import re
import sys
import types
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la
from vagabond.khung.kiem_thu.thu_su_co_290 import nap

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

GOC = Path(__file__).resolve().parents[3]


def _hang_so(ten):
	"""Đọc hằng số literal ở cấp mô-đun don_hang.py mà không import (don_hang kéo requests)."""
	cay = ast.parse((GOC / "vagabond/don_hang.py").read_text(encoding="utf-8"))
	for n in cay.body:
		if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == ten for t in n.targets):
			return ast.literal_eval(n.value)
	raise KeyError(ten)


def _don_hang():
	"""Hàm THẬT nạp từ don_hang.py (không import cả mô-đun), như ca #367."""
	from vagabond import don_web
	g = dict(json=json, re=re, don_web=don_web, MAX_DONG=_hang_so("MAX_DONG"), MAX_SL=_hang_so("MAX_SL"))
	for ten in ("_so", "_lam_sach_hang", "_gan_giam_pancake", "tao_don", "xem_uu_dai"):
		nap("don_hang.py", ten, g)
	return types.SimpleNamespace(**g)


@ca("v678 dĩa, nĩa tặng: mã và trần số lượng ở máy chủ trùng trang khách (một nguồn hai phía)")
def _mot_nguon():
	dh = _don_hang()
	js = (GOC / "vagabond/public/web_vue/kho/thuan.js").read_text(encoding="utf-8")
	m = re.search(r"export const MA_DIA_TANG = '(\w+)', MA_NIA_TANG = '(\w+)', DC_TOI_DA = (\d+);", js)
	dung("trang khách khai mã", bool(m))
	la("cùng mã, cùng thứ tự dĩa rồi nĩa", (m.group(1), m.group(2)), dh._lam_sach_hang.__defaults__[0])
	la("trần trang khách bằng trần máy chủ", int(m.group(3)), dh.MAX_SL)


@ca("v678 dĩa, nĩa tặng (hàm thật _lam_sach_hang): đơn chỉ có dĩa, nĩa là đơn rỗng; có bánh thì giữ nguyên thứ tự, kẹp theo trần chung")
def _lam_sach():
	dh = _don_hang()
	h = [{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAPK00020", "quantity": 99},
		{"variation_id": "BAPK00018", "quantity": 2}]
	la("kẹp, giữ thứ tự", dh._lam_sach_hang(h), [{"variation_id": "BAWC00139", "quantity": 1},
		{"variation_id": "BAPK00020", "quantity": dh.MAX_SL}, {"variation_id": "BAPK00018", "quantity": 2}])
	la("chỉ dĩa, nĩa: rỗng", dh._lam_sach_hang(h[1:]), [])
	la("rỗng vẫn rỗng", dh._lam_sach_hang([]), [])
	la("không có dĩa, nĩa: như cũ", dh._lam_sach_hang(h[:1]), h[:1])


@ca("v678 dĩa, nĩa tặng (hàm thật don_hang.tao_don, xem_uu_dai): gọi thẳng với đơn chỉ có dĩa, nĩa thì báo giỏ rỗng, không tính ưu đãi")
def _cua_tao_don():
	dh = _don_hang()
	don = {"nonce": "a" * 32, "dong_y": True, "items": [{"variation_id": "BAPK00020", "quantity": 3},
		{"variation_id": "BAPK00018", "quantity": 3}], "ho_ten": "Khách", "dien_thoai": "0901234567", "tu_lay": True}
	la("tạo đơn: giỏ rỗng", dh.tao_don(dict(don)), {"ok": 0, "ly_do": "gio_hang_rong"})
	la("xem ưu đãi: không giảm", dh.xem_uu_dai(dict(don)), {"ok": 1, "giam": 0, "ap": []})


@ca("v678 chia giảm giá sang Pancake khi đơn có dòng giá 0 (dĩa, nĩa tặng đứng cuối): đủ từng đồng, dòng 0 đ không nhận giảm, không chia cho 0")
def _chia_giam():
	dh = _don_hang()
	gia = {"BAWC00139": 650000, "BAPK00002": 17000, "BAPK00020": 0, "BAPK00018": 0}
	for ten, goc, giam in (
		("bánh rồi hai dòng 0 đ", [("BAWC00139", 1), ("BAPK00020", 4), ("BAPK00018", 4)], 65001),
		("bánh, thiệp, hai dòng 0 đ", [("BAWC00139", 2), ("BAPK00002", 3), ("BAPK00020", 2), ("BAPK00018", 1)], 100003),
		("dòng 0 đ ở giữa", [("BAWC00139", 1), ("BAPK00020", 1), ("BAPK00002", 1)], 6667),
		("không giảm", [("BAWC00139", 1), ("BAPK00020", 1)], 0),
	):
		hang_goc = [{"variation_id": m, "quantity": q} for m, q in goc]
		hang = [dict(x) for x in hang_goc]
		try:
			ra = dh._gan_giam_pancake(hang, hang_goc, gia, giam)
		except ZeroDivisionError:
			dung(ten + ": không chia cho 0", False)
			continue
		la(ten + ": tổng giảm đủ từng đồng", sum(int(x["discount_each_product"]) * int(x["quantity"]) for x in ra), giam)
		la(ten + ": dòng 0 đ không nhận giảm", [x["discount_each_product"] for x in ra if gia[x["variation_id"]] == 0],
			[0] * len([x for x in ra if gia[x["variation_id"]] == 0]))
		la(ten + ": đủ số lượng từng mã", {m: sum(x["quantity"] for x in ra if x["variation_id"] == m) for m, _q in goc}, dict(goc))
