# -*- coding: utf-8 -*-
"""v693 (26/11/2026): site chạm trần thời gian máy chủ gói Frappe Cloud ngày
25/11 (trang "Daily usage limit reached" tới 07:00 sáng 26/11). Hai hàm trang
khách gọi mỗi phút trên mọi trình duyệt đang mở được đệm 30 giây cho cả site.
Ca chạy hàm thật của bo_dem_web với Frappe giả: có request thì lượt sau dùng
bản đệm, không có request (việc nền, bench) thì luôn tính lại, Redis lỗi thì
trang vẫn có số."""

import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la


class _Redis:
	def __init__(self, hong=False):
		self.kho, self.hong, self.ghi = {}, hong, []

	def get_value(self, k):
		if self.hong:
			raise ConnectionError("redis")
		return self.kho.get(k)

	def set_value(self, k, v, expires_in_sec=None):
		if self.hong:
			raise ConnectionError("redis")
		self.ghi.append((k, expires_in_sec))
		self.kho[k] = v


def _moi(bd, redis, co_request, ngay="2026-11-26"):
	fr = types.SimpleNamespace(local=types.SimpleNamespace(), cache=lambda: redis)
	if co_request:
		fr.local.request = object()
	return [um.patch.object(bd, "frappe", fr), um.patch("frappe.utils.nowdate", lambda: ngay, create=True)]


def _chay(bd, redis, co_request, so_lan, ngay="2026-11-26"):
	dem = []

	def tinh():
		dem.append(1)
		return {"lan": len(dem)}
	vs = _moi(bd, redis, co_request, ngay)
	for v in vs:
		v.start()
	try:
		ra = [bd.qua_bo_dem("co_the_ban_hom_nay", tinh) for _ in range(so_lan)]
	finally:
		for v in vs:
			v.stop()
	return ra, len(dem)


@ca("v693 bộ đệm trang khách: request web tính một lần rồi dùng bản đệm 30 giây")
def _co_request():
	from vagabond import bo_dem_web as bd
	r = _Redis()
	ra, n = _chay(bd, r, True, 5)
	la("tính đúng một lần cho năm lượt", n, 1)
	la("năm lượt cùng một kết quả", ra, [{"lan": 1}] * 5)
	la("ghi đệm 30 giây đúng khoá ngày", r.ghi, [("vgb_bo_dem_web:co_the_ban_hom_nay:2026-11-26", 30)])
	ra2, n2 = _chay(bd, r, True, 1, ngay="2026-11-27")
	la("sang ngày mới tính lại", (n2, ra2), (1, [{"lan": 1}]))


@ca("v693 bộ đệm trang khách: việc nền, bench (không có request) luôn tính lại")
def _khong_request():
	from vagabond import bo_dem_web as bd
	r = _Redis()
	ra, n = _chay(bd, r, False, 3)
	la("ba lượt tính ba lần", n, 3)
	la("không ghi đệm", r.ghi, [])
	la("số mới nhất", ra[-1], {"lan": 3})


@ca("v693 bộ đệm trang khách: Redis lỗi thì vẫn tính và trả số, không làm hỏng trang")
def _redis_loi():
	from vagabond import bo_dem_web as bd
	ra, n = _chay(bd, _Redis(hong=True), True, 2)
	la("vẫn có số mỗi lượt", ra, [{"lan": 1}, {"lan": 2}])


@ca("v693 hai hàm trang khách đi qua bộ đệm, phần tính giữ nguyên")
def _hai_ham():
	from vagabond import bo_dem_web as bd, kiem_banh as kb, kiem_kho as kk
	goi = []

	def gia(ten, tinh, giay=30):
		goi.append((ten, tinh, giay))
		return {"tu_dem": ten}
	with um.patch.object(bd, "qua_bo_dem", gia):
		la("có sẵn hôm nay", kb.co_the_ban_hom_nay(), {"tu_dem": "co_the_ban_hom_nay"})
		la("tại quầy", kk.con_tren_quay_web(), {"tu_dem": "con_tren_quay_web"})
	la("đúng hàm tính", [(t, f.__name__) for t, f, _ in goi],
		[("co_the_ban_hom_nay", "_co_the_ban_hom_nay_tinh"), ("con_tren_quay_web", "_con_tren_quay_web_tinh")])
	dung("khoá thuần đổi theo ngày", bd.khoa_dem("x", "2026-11-26") != bd.khoa_dem("x", "2026-11-27"))
