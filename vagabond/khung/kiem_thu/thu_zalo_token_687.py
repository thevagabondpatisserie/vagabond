# -*- coding: utf-8 -*-
"""v687 (23/11/2026): làm mới token Zalo OA có khoá, nghỉ sau khi bị từ chối.

Sự cố: từ 04:48 sáng 22/11/2026 Zalo trả -14014 "Invalid refresh token", mọi
tin Zalo ngừng hơn một ngày. Lúc 09:48 ngày 23/11 một đợt việc nền gọi
token() 13 lần trong 4 giây; mỗi lần đều tự xin Zalo làm mới bằng cùng một
refresh token, và mỗi lần hỏng đều ghi một Error Log (148 dòng một giờ).

Bộ này dựng một "Zalo giả" làm đúng luật Zalo: mỗi lần làm mới cấp refresh
token mới và HUỶ mã cũ; mã đã huỷ thì trả -14014. Kho Cài đặt giả giữ ba ô
token. Khoá GET_LOCK giả cho một lượt vào một lúc, như MariaDB.

Mỗi ca chốt một đường có thật:
  - một đợt 13 lượt gọi khi token hết hạn chỉ làm mới đúng MỘT lần;
  - lượt chờ khoá đọc lại Cài đặt, dùng token lượt trước vừa ghi;
  - Zalo từ chối thì nghỉ: các lượt sau không gọi Zalo, không ghi Error Log;
  - người dán refresh token mới thì máy thử ngay, không chờ hết giờ nghỉ;
  - refresh token mới được ghi TRƯỚC access token;
  - không chiếm được khoá thì báo bận, không gọi Zalo;
  - khoá luôn được nhả, kể cả khi lỗi.
Dữ liệu giả hoàn toàn, không có mã thật.
"""

import datetime as dt
import sys
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import zalo  # noqa: E402

BAY_GIO = dt.datetime(2026, 11, 23, 9, 48, 33)


class ZaloGia:
	"""Luật Zalo: mỗi refresh token dùng được MỘT lần; dùng xong là huỷ."""

	def __init__(self, ma_dau):
		self.con_song = {ma_dau}
		self.dem = 0
		self.so_cap = 0

	def goi(self, app_id, bi_mat, refresh):
		self.dem += 1
		if refresh not in self.con_song:
			return {"error": -14014, "error_name": "Invalid refresh token."}
		self.con_song.discard(refresh)
		self.so_cap += 1
		moi = "rt-gia-%d" % self.so_cap
		self.con_song.add(moi)
		return {"access_token": "at-gia-%d" % self.so_cap, "refresh_token": moi, "expires_in": "90000"}


class CaiDatGia(dict):
	def get_password(self, field, raise_exception=False):
		return self.get(field)


class Kho:
	"""Cài đặt giả, khoá giả, bộ nhớ đệm giả và nhật ký các lần ghi."""

	def __init__(self, refresh, het_han=None, access="at-cu"):
		self.o = {"zalo_app_id": "1000000000000000001", "zalo_app_secret": "bi-mat-gia",
			"zalo_refresh_token": refresh, "zalo_access_token": access, "zalo_token_het_han": het_han}
		self.giu_khoa = False
		self.cho_khoa = True
		self.so_mo = 0
		self.dem = {}
		self.thu_tu_ghi = []
		self.loi_log = []

	def doc(self):
		return CaiDatGia(self.o)

	def khoa(self):
		if not self.cho_khoa or self.giu_khoa:
			return False
		self.giu_khoa = True
		return True

	def mo(self):
		self.giu_khoa = False
		self.so_mo += 1

	def ghi(self, tok, refresh_moi, het_han):
		if refresh_moi:
			self.thu_tu_ghi.append("refresh")
			self.o["zalo_refresh_token"] = refresh_moi
		self.thu_tu_ghi.append("access")
		self.o["zalo_access_token"] = tok
		self.o["zalo_token_het_han"] = het_han


def _chay(kho, zl, luot=1, bay_gio=BAY_GIO, c=None):
	"""Gọi token() `luot` lần với cùng một bản Cài đặt cũ (như các việc nền đã
	nạp cfg() từ trước). Trả danh sách kết quả hoặc câu lỗi."""
	fr = sys.modules["frappe"]
	cu = c if c is not None else CaiDatGia(dict(kho.o))
	ra = []
	with um.patch.object(zalo, "now_datetime", lambda: bay_gio), \
			um.patch.object(zalo, "_khoa", kho.khoa), um.patch.object(zalo, "_mo_khoa", kho.mo), \
			um.patch.object(zalo, "_doc_moi", kho.doc), um.patch.object(zalo, "_goi_zalo", zl.goi), \
			um.patch.object(zalo, "_ghi_token", kho.ghi), \
			um.patch.object(zalo, "_nghi_doc", lambda: kho.dem.get("nghi")), \
			um.patch.object(zalo, "_nghi_ghi", lambda dau: kho.dem.__setitem__("nghi", {"van_tay": dau})), \
			um.patch.object(zalo, "_nhat_ky", lambda **v: None), \
			um.patch.object(fr, "log_error", lambda *a, **k: kho.loi_log.append(k.get("title"))):
		for _ in range(luot):
			try:
				ra.append(zalo.token(cu))
			except Exception as e:
				ra.append("LOI: %s" % e)
	return ra


HET = dt.datetime(2026, 11, 22, 1, 57, 49)


@ca("Zalo token v687: đợt 13 lượt gọi khi token hết hạn chỉ làm mới MỘT lần, mã còn sống sau đợt")
def _dot_13():
	kho, zl = Kho("rt-dau", HET), ZaloGia("rt-dau")
	ra = _chay(kho, zl, 13)
	la("số lần gọi Zalo", zl.dem, 1)
	la("mọi lượt nhận cùng access token", set(ra), {"at-gia-1"})
	dung("refresh token trong Cài đặt còn sống với Zalo", kho.o["zalo_refresh_token"] in zl.con_song)
	la("không có Error Log", kho.loi_log, [])
	la("khoá nhả đủ 13 lần", (kho.so_mo, kho.giu_khoa), (13, False))
	# Đợt sau, khi token hết hạn lần nữa, vẫn làm mới được (mã không bị huỷ oan).
	ra2 = _chay(kho, zl, 5, bay_gio=BAY_GIO + dt.timedelta(days=2))
	la("đợt sau làm mới được, một lần", (zl.dem, set(ra2)), (2, {"at-gia-2"}))


@ca("Zalo token v687: còn hạn thì không khoá, không gọi Zalo; lượt chờ khoá đọc lại Cài đặt")
def _con_han():
	kho, zl = Kho("rt-dau", BAY_GIO + dt.timedelta(hours=5), access="at-dang-dung"), ZaloGia("rt-dau")
	la("dùng token đang có", _chay(kho, zl, 3), ["at-dang-dung"] * 3)
	la("không gọi Zalo, không khoá", (zl.dem, kho.so_mo), (0, 0))
	# Bản cfg() cũ ghi hết hạn, nhưng Cài đặt trong cơ sở dữ liệu đã có token mới.
	cu = CaiDatGia({"zalo_access_token": "at-cu", "zalo_token_het_han": HET})
	la("đọc lại sau khoá", _chay(kho, zl, 1, c=cu), ["at-dang-dung"])
	la("vẫn không gọi Zalo", zl.dem, 0)


@ca("Zalo token v687: Zalo từ chối thì nghỉ, không gọi lại, không ghi Error Log mỗi tin; dán mã mới thì thử ngay")
def _tu_choi():
	kho, zl = Kho("rt-da-huy", HET), ZaloGia("rt-khac")
	ra = _chay(kho, zl, 13)
	la("gọi Zalo đúng một lần", zl.dem, 1)
	la("một Error Log", kho.loi_log, ["Vagabond: Zalo khong cap token"])
	dung("mọi lượt báo lỗi dễ hiểu", all(x.startswith("LOI: Zalo không cấp được token") for x in ra))
	la("khoá nhả đủ", (kho.so_mo, kho.giu_khoa), (13, False))
	# Người dán refresh token mới (khác vân tay): thử ngay, không chờ hết giờ nghỉ.
	kho.o["zalo_refresh_token"] = "rt-khac"
	la("mã mới dùng được ngay", _chay(kho, zl, 2), ["at-gia-1", "at-gia-1"])
	la("thêm đúng một lần gọi", zl.dem, 2)


@ca("Zalo token v687: ghi refresh token mới TRƯỚC access token; Zalo không trả refresh mới thì giữ mã cũ")
def _thu_tu_ghi():
	kho, zl = Kho("rt-dau", HET), ZaloGia("rt-dau")
	_chay(kho, zl, 1)
	la("thứ tự ghi", kho.thu_tu_ghi, ["refresh", "access"])
	la("hạn mới theo expires_in trừ 5 phút", kho.o["zalo_token_het_han"],
		BAY_GIO + dt.timedelta(seconds=90000 - 300))

	class ZaloKhongTraRefresh(ZaloGia):
		def goi(self, *a):
			j = super().goi(*a)
			j.pop("refresh_token", None)
			return j

	kho2, zl2 = Kho("rt-dau", HET), ZaloKhongTraRefresh("rt-dau")
	_chay(kho2, zl2, 1)
	la("giữ refresh token cũ", (kho2.o["zalo_refresh_token"], kho2.thu_tu_ghi), ("rt-dau", ["access"]))


@ca("Zalo token v687: phép ghi thật: refresh token ghi trước access token, rồi hạn, rồi commit, rồi xoá bản đệm")
def _ghi_that():
	import types

	fr = sys.modules["frappe"]
	vet = []
	mk = types.ModuleType("frappe.utils.password")
	mk.set_encrypted_password = lambda dt_, ten, gt, o: vet.append(("mat", o, gt))
	db = types.SimpleNamespace(
		set_single_value=lambda dt_, o, gt: vet.append(("o", o, gt)),
		commit=lambda: vet.append(("commit",)))
	with um.patch.dict(sys.modules, {"frappe.utils.password": mk}), um.patch.object(fr, "db", db), \
			um.patch.object(fr, "clear_cache", lambda **k: vet.append(("xoa_dem", k.get("doctype"))), create=True):
		zalo._ghi_token("at-moi", "rt-moi", HET)
		la("thứ tự ghi", vet, [("mat", "zalo_refresh_token", "rt-moi"), ("mat", "zalo_access_token", "at-moi"),
			("o", "zalo_token_het_han", HET), ("commit",), ("xoa_dem", "Vagabond Settings")])
		del vet[:]
		zalo._ghi_token("at-moi", None, HET)
		dung("không có refresh mới thì không đụng ô refresh", all(x[1] != "zalo_refresh_token" for x in vet if x[0] == "mat"))


@ca("Zalo token v687: không chiếm được khoá thì báo bận, không gọi Zalo")
def _ban():
	kho, zl = Kho("rt-dau", HET), ZaloGia("rt-dau")
	kho.cho_khoa = False
	ra = _chay(kho, zl, 1)
	dung("báo đang làm mới ở lượt khác: %s" % ra, "lượt khác" in ra[0])
	la("không gọi Zalo, không nhả khoá không giữ", (zl.dem, kho.so_mo), (0, 0))


@ca("Zalo token v687: phép thuần còn hạn, đang nghỉ, vân tay")
def _thuan():
	la("còn hạn", [zalo.con_han("a", BAY_GIO + dt.timedelta(seconds=1), BAY_GIO),
		zalo.con_han("a", BAY_GIO, BAY_GIO), zalo.con_han("", BAY_GIO + dt.timedelta(1), BAY_GIO),
		zalo.con_han("a", None, BAY_GIO)], [True, False, False, False])
	v = zalo.van_tay("rt-dau")
	la("vân tay 12 ký tự, không lộ mã", (len(v), "rt-dau" in v), (12, False))
	la("đang nghỉ", [zalo.dang_nghi({"van_tay": v}, v), zalo.dang_nghi({"van_tay": v}, zalo.van_tay("rt-khac")),
		zalo.dang_nghi(None, v), zalo.dang_nghi("rac", v)], [True, False, False, False])
	la("hạn rỗng là chưa có hạn, datetime giữ nguyên", (zalo._han(""), zalo._han(None), zalo._han(HET)), (None, None, HET))
