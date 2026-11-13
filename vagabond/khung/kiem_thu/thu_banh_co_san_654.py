# -*- coding: utf-8 -*-
"""v654 tin "Bánh có sẵn hôm nay" chỉ gửi khi số bán được đổi (anh Việt 13/11/2026).

Sự cố trên site 13/11: 13 tin từ 08:02 tới 11:03, nhiều cặp giống hệt. Lần gửi
trước chỉ nằm trong bộ nhớ đệm, mất là gửi lại. Ca chốt:
  - nhiều lượt cùng dữ liệu, kể cả khi bộ nhớ đệm bị xoá giữa chừng: không gửi thêm;
  - thêm bánh, một bánh hết, đổi số: đúng một tin;
  - một loại giảm 1, loại khác tăng 1 (tổng không đổi): vẫn gửi;
  - giờ, thứ tự hiện, ảnh vẽ lại không làm đổi dấu;
  - hai lượt chạy chồng: lượt sau nhường (khoá có tên), và nếu lọt thì sổ tin
    chỉ nhận một dòng (khoá chống trùng theo tin đứng trước);
  - Zalo chậm trả lời (dòng "Chưa rõ"): nhịp sau không gửi lại;
  - tin đầu ngày: bảng chưa có bánh bán được thì im; đã báo có bánh mà hết sạch
    thì báo một tin.
"""

import datetime as dt
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

fr = gia_lap()
if not hasattr(fr.utils, "get_url"):
	fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import anh_bang  # noqa: E402
from vagabond import tin_banh_co_san as t  # noqa: E402


def _dong(*cap):
	return [dict(ma_hang=m, ten_banh=ten, hinh="https://anh/%s.jpg" % m, co_the_ban=so) for m, ten, so in cap]


class Bo(object):
	def __init__(self):
		self.d = {}

	def get_value(self, k):
		return self.d.get(k)

	def set_value(self, k, v, expires_in_sec=None):
		self.d[k] = v


class So(object):
	"""Sổ tin giả: mỗi lần bao() là một dòng, khoá trùng thì không thêm (như
	DuplicateEntryError của bảng thật). Có khoá có tên giống MariaDB."""

	def __init__(self):
		self.dong = []
		self.khoa_ten = set()
		self.ban_khoa = False

	def bao(self, *a, **k):
		if any(x["khoa"] == k.get("khoa") for x in self.dong):
			return []
		self.dong.append({"khoa": k.get("khoa"), "dau": k.get("dau") or "", "creation": self.bay, "chu": a[3],
			"anh": k.get("anh"), "ma_tin": k.get("ma_tin"), "trang_thai": "Chờ gửi"})
		return ["ZL-%d" % len(self.dong)]

	def sql(self, q, v=None, *a, **k):
		if "get_lock" in q:
			if self.ban_khoa or v[0] in self.khoa_ten:
				return [(0,)]
			self.khoa_ten.add(v[0])
			return [(1,)]
		if "release_lock" in q:
			self.khoa_ten.discard(v[0])
			return [(1,)]
		return []


def _chay(bay, dong, so, bo, anh="https://anh/luoi.png"):
	from vagabond import kenh_zalo

	so.bay = bay

	def get_all(dt_, *a, **k):
		if dt_ == "Vagabond Tin Kenh":
			r = [x for x in so.dong if x["ma_tin"] == k["filters"]["ma_tin"] and str(x["creation"]) >= k["filters"]["creation"][1]]
			r.sort(key=lambda x: x["creation"], reverse=True)
			return [dict(dau=x["dau"], creation=x["creation"]) for x in r[:1]]
		return [dict(x) for x in dong]

	vs = [um.patch.object(fr.db, "exists", lambda *a, **k: True), um.patch.object(fr, "get_all", get_all),
		um.patch.object(fr.db, "sql", so.sql), um.patch.object(fr, "cache", lambda: bo, create=True),
		um.patch("frappe.utils.now_datetime", lambda: bay), um.patch("frappe.utils.nowdate", lambda: str(bay.date())),
		um.patch("frappe.utils.get_datetime", lambda v: v if isinstance(v, dt.datetime) else dt.datetime.fromisoformat(str(v)), create=True),
		um.patch.object(anh_bang, "anh_luoi", lambda *a, **k: anh),
		um.patch.object(kenh_zalo, "bao_hoac_ghi_loi", so.bao)]
	for v in vs:
		v.start()
	try:
		return t.quet()
	finally:
		for v in reversed(vs):
			v.stop()


def h(gio, phut):
	return dt.datetime(2026, 11, 13, gio, phut)


# Bảng thật 13/11 lúc 08:32 (rút gọn 4 dòng): số không đổi suốt một giờ.
SANG = _dong(("BAWC00086", "Very Berry 12cm", 5), ("BAWC00087", "Very Berry 16cm", 5),
	("BAWC00020", "Epi 16cm", 3), ("BAWC00019", "Epi 12cm", 1), ("BAWC00055", "Hannari 16cm", 0))


@ca("v654 cùng dữ liệu chạy nhiều lượt, bộ nhớ đệm bị xoá giữa chừng: chỉ MỘT tin (sự cố 13/11)")
def _khong_lap():
	so, bo = So(), Bo()
	_chay(h(8, 32), SANG, so, bo)
	la("tin đầu ngày", len(so.dong), 1)
	for gio, phut in ((8, 37), (8, 48), (9, 2), (9, 20), (9, 32), (10, 3)):
		bo.d.clear()  # đúng điều đã xảy ra trên site: bộ nhớ đệm mất dấu
		_chay(h(gio, phut), SANG, so, bo)
	la("bảy lượt, số không đổi: vẫn một tin", len(so.dong), 1)
	dung("dòng tin mang dấu trạng thái", bool(so.dong[0]["dau"]))


@ca("v654 thêm bánh, một bánh hết, đổi số: mỗi thay đổi đúng một tin; giảm 1 tăng 1 tổng không đổi vẫn gửi")
def _doi():
	so, bo = So(), Bo()
	_chay(h(9, 0), SANG, so, bo)
	them = SANG + _dong(("BAWC00143", "Monsoon 12cm", 2))
	_chay(h(9, 15), them, so, bo)
	_chay(h(9, 20), them, so, bo)
	la("thêm một loại: một tin", len(so.dong), 2)
	het = [dict(x, co_the_ban=0) if x["ma_hang"] == "BAWC00019" else x for x in them]
	_chay(h(9, 30), het, so, bo)
	_chay(h(9, 35), het, so, bo)
	la("một loại hết: một tin", len(so.dong), 3)
	doi = [dict(x, co_the_ban=4) if x["ma_hang"] == "BAWC00086" else dict(x, co_the_ban=6) if x["ma_hang"] == "BAWC00087" else x for x in het]
	tong = lambda d: sum(max(0, x["co_the_ban"]) for x in d)  # noqa: E731
	la("tổng hai lần bằng nhau", tong(doi), tong(het))
	_chay(h(9, 45), doi, so, bo)
	la("12cm giảm 1, 16cm tăng 1: vẫn gửi", len(so.dong), 4)
	_chay(h(10, 0), het, so, bo)
	la("quay lại đúng trạng thái 9:30 vẫn gửi", len(so.dong), 5)


@ca("v654 giờ cập nhật, thứ tự hiện, ảnh vẽ lại không làm đổi dấu nên không gửi")
def _khong_doi_dau():
	so, bo = So(), Bo()
	_chay(h(9, 0), SANG, so, bo)
	_chay(h(9, 20), list(reversed(SANG)), so, bo, anh="https://anh/luoi-ve-lai.png")
	_chay(h(9, 40), [dict(x, ten_banh=x["ten_banh"].upper(), hinh="https://anh/moi.jpg") for x in SANG], so, bo)
	la("đảo thứ tự, vẽ lại ảnh, đổi tên hiển thị: vẫn một tin", len(so.dong), 1)


@ca("v654 hai lượt chạy chồng: lượt sau nhường khoá; nếu lọt thì sổ tin chỉ nhận một dòng")
def _chong():
	so, bo = So(), Bo()
	so.khoa_ten.add(t.KHOA_CHAY)  # lượt khác đang giữ khoá
	la("lượt sau nhường", _chay(h(9, 0), SANG, so, bo), None)
	la("không gửi", len(so.dong), 0)
	so.khoa_ten.clear()
	_chay(h(9, 0), SANG, so, bo)
	# Hai lượt cùng đọc thấy "chưa có tin hôm nay" rồi cùng ghi: cùng khoá.
	k1 = t.khoa_tin("2026-11-13", t.dau_van_tay(t.danh_sach(SANG)), None)
	la("khoá của lượt kia trùng khoá dòng đã ghi", k1, so.dong[0]["khoa"])
	la("ghi lần hai bị sổ tin từ chối", so.bao("ban_tin", "ban_hang", "x", [], khoa=k1, ma_tin=t.MA_TIN, dau="x"), [])
	la("vẫn một dòng", len(so.dong), 1)


@ca("v654 Zalo chậm trả lời (dòng Chưa rõ): nhịp sau không gửi lại cùng nội dung")
def _cham():
	so, bo = So(), Bo()
	_chay(h(9, 0), SANG, so, bo)
	so.dong[0]["trang_thai"] = "Chưa rõ"
	bo.d.clear()
	_chay(h(9, 20), SANG, so, bo)
	la("không gửi lại", len(so.dong), 1)


@ca("v654 tin đầu ngày: bảng chưa có bánh thì im; đã báo có bánh mà hết sạch thì báo một tin; ngoài giờ im")
def _dau_ngay():
	so, bo = So(), Bo()
	trong = [dict(x, co_the_ban=0) for x in SANG]
	_chay(h(8, 5), trong, so, bo)
	_chay(h(8, 30), trong, so, bo)
	la("chưa có bánh bán được: không tin", len(so.dong), 0)
	_chay(h(7, 50), SANG, so, bo)
	la("trước giờ mở cửa: không tin", len(so.dong), 0)
	_chay(h(8, 45), SANG, so, bo)
	la("có bánh: tin đầu ngày", len(so.dong), 1)
	_chay(h(20, 0), trong, so, bo)
	_chay(h(20, 30), trong, so, bo)
	la("hết sạch: đúng một tin", len(so.dong), 2)
	dung("tin hết mời đặt trước", "đặt trước" in " ".join(so.dong[-1]["chu"]))
	la("hết sạch không vẽ ảnh", so.dong[-1]["anh"], None)


@ca("v654 THUẦN can_gui: đúng lý do cho từng nhánh")
def _can_gui():
	b = h(9, 30)
	la("đầu ngày bảng trống", t.can_gui("x", 0, None, b), (False, "đầu ngày, bảng chưa có bánh bán được"))
	la("đầu ngày có bánh", t.can_gui("x", 3, None, b), (True, "tin đầu ngày"))
	la("không đổi", t.can_gui("x", 3, "x", b, h(8, 0)), (False, "số bán được không đổi"))
	la("đổi mà mới 10 phút", t.can_gui("y", 3, "x", b, h(9, 20))[0], False)
	la("đổi đủ 15 phút", t.can_gui("y", 3, "x", b, h(9, 15)), (True, "số bán được đổi"))
	la("dòng cũ chưa có dấu: gửi một lần để có dấu", t.can_gui("y", 3, "", b, h(9, 0))[0], True)
