# -*- coding: utf-8 -*-
"""v670 Bài đăng (anh Việt 17/11/2026, dựng lại PR #577 trên main 669).

Ca chốt:
  - dải chip trạng thái đầu màn: máy chủ đếm số bài cho TỪNG chip lọc của Danh sách
    bằng một hàm thuần (dem_trang_thai), cùng khoá với chip, bài đã huỷ không vào
    "Mọi bài";
  - "chưa hẹn giờ" chỉ một điều kiện cho cả số đếm, chip Danh sách và Kho bản thảo
    (Nháp, Chờ duyệt, chưa có giờ hẹn), không còn chỗ tự tính kiểu khác.
"""

import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import bai_dang as x  # noqa: E402


@ca("v670 đếm theo chip: mỗi trạng thái một số, Mọi bài trừ bài đã huỷ, Chưa hẹn giờ lấy số riêng; dòng trống bỏ qua")
def _dem():
	d = x.dem_trang_thai([(x.TT_NHAP, 2), (x.TT_CHO, 1), (x.TT_HEN, 3), (x.TT_TAY, 1), (x.TT_XONG, 4), (x.TT_HUY, 5), (None, 9)], 2)
	la("từng chip", [d.get(k) for k in ("", "chua_gio", x.TT_CHO, x.TT_TAY, x.TT_HEN, x.TT_XONG, x.TT_NHAP)], [11, 2, 1, 1, 3, 4, 2])
	la("không dữ liệu", x.dem_trang_thai([], 0), {"": 0, "chua_gio": 0})


@ca("v670 Việc đầu màn trả số theo chip bằng MỘT câu đếm nhóm theo trạng thái")
def _viec():
	cau = []

	def sql(q, gt=None, as_dict=False):
		cau.append(q)
		if "group by trang_thai" in q:
			return [(x.TT_NHAP, 2), (x.TT_CHO, 1)]
		return [[0]]
	with um.patch.object(x.frappe.db, "sql", sql, create=True), \
			um.patch.object(x.frappe.db, "count", lambda dt, f=None: 2 if f and "hen_luc" in f else 1, create=True):
		v = x._viec()
	la("số theo chip", (v["dem"][""], v["dem"]["chua_gio"], v["dem"][x.TT_CHO]), (3, 2, 1))
	la("một câu nhóm", sum(1 for q in cau if "group by trang_thai" in q), 1)


@ca("v670 Chưa hẹn giờ một điều kiện: chip Danh sách đọc đúng bài Nháp, Chờ duyệt chưa có giờ hẹn như số đếm và Kho bản thảo; không còn chỗ tự tính kiểu khác")
def _chua_gio():
	cau = []

	def sql(q, gt=None, as_dict=False):
		cau.append((q, gt))
		return []
	with um.patch.object(x.frappe.db, "sql", sql, create=True):
		x._doc_bai(khong_gio=True, gioi_han=200)
	q, gt = cau[0]
	dung("lọc Nháp, Chờ duyệt chưa có giờ hẹn", "b.trang_thai in %s and b.hen_luc is null" in q and x.TT_SUA_DUOC in gt)
	dung("không còn điều kiện duyet_luc cũ", "duyet_luc is null" not in q)
	import inspect
	nguon = inspect.getsource(x)
	dung("số đếm dùng cùng điều kiện", '{"trang_thai": ["in", TT_SUA_DUOC], "hen_luc": ["is", "not set"]}' in nguon)
	dung("Kho bản thảo dùng cùng điều kiện", '["b.trang_thai in %s", "b.hen_luc is null"], [TT_SUA_DUOC]' in nguon)
	la("không còn chỗ lọc chưa hẹn giờ kiểu khác", nguon.count("hen_luc is null and b.duyet_luc is null"), 0)
