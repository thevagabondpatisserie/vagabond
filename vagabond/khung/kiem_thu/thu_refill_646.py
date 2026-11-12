# -*- coding: utf-8 -*-
"""v646 Refill (bếp báo 09/11/2026 sau vụ Roman De La Rose 18 đặt xa ngày, anh Việt
duyệt 09/11): bếp nhập mẻ refill (số bánh, có bánh từ ngày, nhận đơn tới ngày) trên
bảng kiểm bánh; đơn giao trong khoảng refill trừ vào refill chứ không trừ Đủ decor;
web tab Đặt trước hiện bánh refill kèm khoảng ngày và máy chủ chặn đặt quá số.

Mỗi ca chốt một đường lỗi có thật:
  - đơn đặt xa ngày (ngoài cửa sổ 3 ngày) không ai thấy trên bảng kiểm bánh;
  - web nhận đơn xa ngày không kiểm gì (trước: ngày quá 3 ngày tới là cho qua);
  - đơn của ngày refill vẫn ăn vào Đủ decor (trừ hai lần, decor báo hết oan);
  - Pancake lỗi mà coi là 0 đơn (mở bán refill nhận lố);
  - ô số trống bị coi là 0, ngày nhận tới vô hạn, sales sửa được số của bếp.
Phần chạm hệ chạy trên lớp Frappe giả, vá đúng lời gọi hàm thật dùng.
"""

import datetime as dt
import json
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import refill as rf  # noqa: E402

D8 = dt.date
HN = D8(2026, 11, 10)  # Thứ Ba 10/11, như ảnh đề xuất anh duyệt


def _don(ma, ngay_giao_utc, sl, tt=1):
	"""Đơn Pancake đúng hình dạng API: estimate_delivery_date là giờ UTC không múi."""
	return {"status": tt, "estimate_delivery_date": ngay_giao_utc,
		"items": [{"quantity": sl, "variation_info": {"display_id": ma, "name": "Roman De La Rose 18"}}]}


def _ngay_vn(s):
	from vagabond.ngay_pancake import ngay_tu_iso

	return ngay_tu_iso(s)


# Đơn Roman 18 như ảnh: giao 14/11 bốn cái (một đơn đặt 17:00 UTC 13/11 = 00:00 VN 14/11),
# 15/11 hai cái, 20/11 một cái, 11/11 một cái (trong cửa sổ 3 ngày), một đơn huỷ.
DON = [_don("BAWC00068", "2026-11-13T17:00:00", 3), _don("BAWC00068", "2026-11-14T03:00:00", 1),
	_don("BAWC00068", "2026-11-15T02:00:00", 2), _don("BAWC00068", "2026-11-20T04:00:00", 1),
	_don("BAWC00068", "2026-11-11T02:00:00", 1), _don("BAWC00068", "2026-11-16T02:00:00", 5, tt=6)]


# ------------------------------------------------------------ phần thuần

@ca("v646 refill nhập: ô số trống thì báo (không coi là 0), 0 là bỏ, ngày nhận tới mặc định có bánh + 6, trần 13 ngày, ngày đã qua bị chặn")
def _chuan():
	nem("số trống", lambda: rf.chuan_refill("", "2026-11-14", "", HN), rf.LoiRefill)
	la("0 là bỏ refill", rf.chuan_refill("0", "", "", HN), (0, None, None))
	la("mặc định nhận tới +6", rf.chuan_refill("20", "2026-11-14", "", HN), (20, D8(2026, 11, 14), D8(2026, 11, 20)))
	la("gõ kiểu 1.000 vẫn đọc", rf.chuan_refill("1.000", "2026-11-14", "2026-11-14", HN)[0], 1000)
	nem("ngày có bánh đã qua", lambda: rf.chuan_refill("5", "2026-11-09", "", HN), rf.LoiRefill)
	nem("thiếu ngày có bánh", lambda: rf.chuan_refill("5", "", "", HN), rf.LoiRefill)
	nem("nhận tới trước có bánh", lambda: rf.chuan_refill("5", "2026-11-14", "2026-11-13", HN), rf.LoiRefill)
	nem("nhận tới quá 13 ngày", lambda: rf.chuan_refill("5", "2026-11-14", "2026-11-28", HN), rf.LoiRefill)
	la("đúng 13 ngày được", rf.chuan_refill("5", "2026-11-14", "2026-11-27", HN)[2], D8(2026, 11, 27))
	nem("có bánh xa quá 30 ngày", lambda: rf.chuan_refill("5", "2026-12-11", "", HN), rf.LoiRefill)
	nem("số âm", lambda: rf.chuan_refill("-2", "2026-11-14", "", HN), rf.LoiRefill)
	nem("chữ", lambda: rf.chuan_refill("hai mươi", "2026-11-14", "", HN), rf.LoiRefill)


@ca("v646 đếm đơn tương lai theo NGÀY GIAO GIỜ VIỆT NAM, bỏ đơn huỷ, cộng giữ chỗ phiếu đặt; đặt xa ngày là sau cửa sổ 3 ngày")
def _dem():
	tn = rf.dem_theo_ngay(DON, _ngay_vn, {"2026-11-15": {"BAWC00068": 1}})["BAWC00068"]
	la("theo ngày", tn, {"2026-11-14": 4, "2026-11-15": 3, "2026-11-20": 1, "2026-11-11": 1})
	la("đã đặt trong khoảng 14 tới 20", rf.da_dat_trong(tn, "2026-11-14", "2026-11-20"), 8)
	tong, ds = rf.dat_xa(tn, HN)
	la("đặt xa ngày: bỏ 11/11 (trong 3 ngày tới)", (tong, ds), (8, [("2026-11-14", 4), ("2026-11-15", 3), ("2026-11-20", 1)]))
	la("mô tả", rf.mo_ta({"tu": "2026-11-14", "den": "2026-11-20"}), "có từ T7 14/11, nhận tới 20/11")
	dung("hết hạn khi qua ngày nhận tới", not rf.con_hieu_luc(20, "2026-11-01", "2026-11-09", HN))
	dung("còn hiệu lực đúng ngày nhận tới", rf.con_hieu_luc(20, "2026-11-01", "2026-11-10", HN))


@ca("v646 kiểm đơn web có refill: trong khoảng mà quá số thì nhắc; ngoài khoảng, không còn decor thì nhắc chọn ngày; còn decor thì để decor lo")
def _kiem_don():
	r = {"BAWC00068": {"so": 20, "tu": D8(2026, 11, 14), "den": D8(2026, 11, 20), "ten": "Roman De La Rose 18"}}
	h = lambda n: [{"variation_id": "BAWC00068", "quantity": n}]
	la("còn đủ", rf.kiem_don(h(2), "2026-11-15", r, {"BAWC00068": 12}), [])
	la("quá số", rf.kiem_don(h(13), "2026-11-15", r, {"BAWC00068": 12}),
		["Roman De La Rose 18 ngày 15/11/2026 chỉ còn 12 cái, quý khách đang chọn 13 cái."])
	la("ngoài khoảng", rf.kiem_don(h(1), "2026-11-25", r, {"BAWC00068": 12}),
		["Roman De La Rose 18 nhận giao từ 14/11 tới 20/11, quý khách chọn ngày nhận trong khoảng này."])
	la("ngoài khoảng mà còn decor 3 ngày tới", rf.kiem_don(h(1), "2026-11-12", r, {"BAWC00068": 12}, {"BAWC00068": 3}), [])
	la("mã không refill không đụng", rf.kiem_don([{"variation_id": "X", "quantity": 99}], "2026-11-15", r, {}), [])


# ------------------------------------------------------------ chạm hệ

from vagabond.khung.kiem_thu.btp_gia import BangBTP  # noqa: E402


class Kho:
	"""Bảng BTP và phiếu kiểm bánh ngày giả, đủ cho btp, kiem_banh, ton_don_web."""

	def __init__(self, dong, kb=None):
		self.btp = Doi(dong=[Doi(x) for x in dong], cap_nhat_luc=None, luu=0)
		self.btp.save = lambda **k: setattr(self, "da_luu", True)
		self.btp.append = lambda f, v: self.btp.dong.append(Doi(v)) or self.btp.dong[-1]
		self.kb = kb or {}
		self.da_luu = False

	def get_single(self, ten):
		return self.btp

	def exists(self, dt_, ten):
		return ten in self.kb

	def get_doc(self, dt_, ten=None):
		return Doi(tinh_trang="Dang ban", dong=[Doi(x) for x in self.kb[ten]])


def _vá(kho, nay=HN):
	import frappe
	from vagabond import btp, kiem_banh, ton_don_web

	ds = [um.patch.object(frappe, "get_single", kho.get_single, create=True),
		um.patch.object(frappe.db, "exists", kho.exists, create=True),
		um.patch.object(frappe, "get_doc", kho.get_doc, create=True), um.patch.object(btp, "getdate", lambda *a: nay),
		um.patch.object(kiem_banh, "getdate", lambda *a: nay), um.patch.object(ton_don_web, "hom_nay", lambda: nay)]
	return ds


def _chay(kho, ham, tinh=None, nay=HN):
	import contextlib

	from frappe.utils import getdate as _gd  # noqa: F401
	with contextlib.ExitStack() as st:
		for p in _vá(kho, nay):
			st.enter_context(p)
		st.enter_context(um.patch("frappe.utils.getdate", lambda *a: nay))
		if tinh is not None:
			st.enter_context(um.patch.object(rf, "tinh", tinh))
		return ham()


ROMAN = {"ma_hang": "BAWC00068", "ten_banh": "Roman De La Rose 18", "hinh": "", "so_btp": 0, "so_decor": 0,
	"so_refill": 20, "refill_tu": D8(2026, 11, 14), "refill_den": D8(2026, 11, 20)}
KANKIN = {"ma_hang": "BAWC00123", "ten_banh": "Kankin 16", "hinh": "", "so_btp": 6, "so_decor": 5,
	"so_refill": 0, "refill_tu": None, "refill_den": None}


def _tinh_that(don=DON, loi=False):
	"""Chạy refill.tinh THẬT với đơn Pancake giả (hoặc Pancake lỗi)."""
	goc = rf.tinh

	def t(hom_nay=None, moi=False, dong=None):
		def dtl(hn=None, moi=False, tu=None):
			if loi:
				raise Exception("Pancake 429")
			return rf.dem_theo_ngay(don, _ngay_vn), rf.id_da_dem(don)
		import frappe
		with um.patch.object(rf, "dem_va_id", dtl), um.patch.object(frappe, "log_error", lambda *a, **k: None, create=True):
			return goc(HN, moi, dong)
	return t


@ca("v646 bảng BTP: ô Refill, Còn nhận refill = 20 trừ 7 đơn trong khoảng, Đặt xa ngày theo ngày; Pancake lỗi thì '?' chứ không phải 0")
def _bang_btp():
	from vagabond import btp

	kho = Kho([ROMAN, KANKIN])
	m = _chay(kho, btp.bang_btp, _tinh_that())
	r = [d for d in m["dong"] if d["ma_hang"] == "BAWC00068"][0]["refill"]
	la("refill Roman", (r["so"], r["tu"], r["den"], r["da_dat"], r["con"]), (20, "2026-11-14", "2026-11-20", 7, 13))
	la("đặt xa ngày", m["dat_xa"]["BAWC00068"]["tong"], 7)
	la("lịch refill", [(x["ma_hang"], x["tu"]) for x in m["lich_refill"]], [("BAWC00068", "2026-11-14")])
	la("Kankin không refill", [d for d in m["dong"] if d["ma_hang"] == "BAWC00123"][0]["refill"], None)
	m = _chay(Kho([ROMAN]), btp.bang_btp, _tinh_that(loi=True))
	r = m["dong"][0]["refill"]
	la("Pancake lỗi: chưa đếm, không phải 0", (r["da_dat"], r["con"]), (None, None))
	dung("có câu báo", "Chưa đếm được" in m["refill_loi"])


@ca("v646 đơn giao trong khoảng refill KHÔNG trừ Đủ decor (Còn nhận 3 ngày, Còn nhận mai); ngoài khoảng vẫn trừ như cũ")
def _decor():
	from vagabond import btp

	ro = dict(ROMAN, so_btp=10, so_decor=6, refill_tu=D8(2026, 11, 11), refill_den=D8(2026, 11, 17))
	kb = {"KB-2026-11-10": [{"ma_hang": "BAWC00068", "da_dat": 1, "phat_sinh": 0, "cho_chot": 0}],
		"KB-2026-11-11": [{"ma_hang": "BAWC00068", "da_dat": 4, "phat_sinh": 0, "cho_chot": 0}],
		"KB-2026-11-12": [{"ma_hang": "BAWC00068", "da_dat": 2, "phat_sinh": 0, "cho_chot": 0}]}
	m = _chay(Kho([ro], kb), btp.bang_btp, _tinh_that(don=[]))
	d = m["dong"][0]
	la("còn nhận 3 ngày chỉ trừ đơn 10/11", d["con_nhan"], 9)
	la("còn nhận mai không trừ đơn 11/11 (thuộc refill)", d["giao_mai"], 6)
	m = _chay(Kho([dict(ro, so_refill=0)], kb), btp.bang_btp, _tinh_that(don=[]))
	la("không refill: trừ đủ như cũ", (m["dong"][0]["con_nhan"], m["dong"][0]["giao_mai"]), (3, 2))


def du_lieu_web(loi=False, kankin=None, kb=None):
	"""Tab Đặt bánh trước dựng bằng kiem_banh._dat_truoc_theo_decor THẬT (ca node dùng lại)."""
	import frappe
	from vagabond import kiem_banh, tat_ban_web

	kho = Kho([ROMAN, kankin or KANKIN], kb or {"KB-2026-11-11": [{"ma_hang": "BAWC00123", "da_dat": 2}]})
	item = [{"item_code": "BAWC00068", "item_name": "Bánh Ổ Roman de la Rose, size 18cm", "image": "", "standard_rate": 1060000, "disabled": 0,
		"is_sales_item": 1}, {"item_code": "BAWC00123", "item_name": "Bánh Ổ Kankin, size 16cm", "image": "", "standard_rate": 910000,
		"disabled": 0, "is_sales_item": 1}]
	with um.patch.object(frappe, "get_all", lambda *a, **k: [Doi(x) for x in item], create=True), \
			um.patch.object(tat_ban_web, "bang", lambda *a, **k: {}), \
			um.patch.object(kiem_banh, "_anh_noi_dung_web", lambda ds: ds):
		return _chay(kho, kiem_banh._dat_truoc_theo_decor, _tinh_that(loi=loi))


@ca("v646 web tab Đặt trước: bánh chỉ có refill lên kèm khoảng ngày và số còn; Pancake lỗi thì ẩn refill (không nhận lố); decor không đổi")
def _web():
	m = du_lieu_web()
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("Roman: còn 13, khoảng 14 tới 20, chỉ refill", (s["BAWC00068"]["con"], s["BAWC00068"]["refill"]),
		(13, {"tu": "2026-11-14", "den": "2026-11-20", "con": 13, "chi_refill": 1}))
	la("Kankin decor 5 trừ 2 đơn", (s["BAWC00123"]["con"], "refill" in s["BAWC00123"]), (3, False))
	m = du_lieu_web(loi=True)
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	dung("Pancake lỗi: Roman không lên", "BAWC00068" not in s)
	dung("Kankin vẫn lên", "BAWC00123" in s)


@ca("v646 cửa nhận đơn web: ngày xa (trước: không kiểm) nay kiểm theo refill; quá số chặn; ngoài khoảng chặn; Pancake lỗi thì báo Sales, không chặn")
def _cua_nhan():
	import frappe
	from vagabond import ton_don_web

	h = lambda n: [{"variation_id": "BAWC00068", "quantity": n}]
	bao = []
	with um.patch.object(ton_don_web, "bao_loi", lambda ng: bao.append(ng)), um.patch.object(frappe, "log_error", lambda *a, **k: None, create=True):
		k = lambda hang, ngay, loi=False: _chay(Kho([ROMAN]), lambda: ton_don_web.kiem(hang, ngay), _tinh_that(loi=loi))
		la("còn đủ", k(h(2), "2026-11-15"), [])
		la("quá số (13 còn, chọn 14)", k(h(14), "2026-11-15"),
			["Roman De La Rose 18 ngày 15/11/2026 chỉ còn 13 cái, quý khách đang chọn 14 cái."])
		la("ngày 25/11 ngoài khoảng (trước bản này: cho qua)", k(h(1), "2026-11-25"),
			["Roman De La Rose 18 nhận giao từ 14/11 tới 20/11, quý khách chọn ngày nhận trong khoảng này."])
		la("Pancake lỗi: không chặn", k(h(30), "2026-11-15", loi=True), [])
		la("và báo Sales", bao, [D8(2026, 11, 15)])
		la("bánh không refill, ngày xa: như cũ", k([{"variation_id": "BAWC00123", "quantity": 9}], "2026-11-25"), [])


@ca("v646 lưu refill: chỉ bếp; ô trống báo; lưu đủ ba ô; 0 thì xoá ngày; đang có refill thì không xoá mã khỏi bảng BTP")
def _luu():
	import frappe
	from vagabond import btp

	kho = Kho([dict(KANKIN)])
	with um.patch.object(btp, "_duoc_sua_btp", lambda: False):
		nem("sales không sửa", lambda: _chay(kho, lambda: btp.luu_refill("BAWC00123", "5", "2026-11-14", "")), Exception)
	with um.patch.object(btp, "_duoc_sua_btp", lambda: True), um.patch.object(btp, "bang_btp", lambda: "ok"), \
			um.patch.object(frappe.db, "commit", lambda: None, create=True):
		nem("ô trống", lambda: _chay(kho, lambda: btp.luu_refill("BAWC00123", "", "2026-11-14", "")), Exception)
		# v653: lưu đúng một dòng (khoá, UPDATE, nhật ký), không lưu cả bảng.
		with BangBTP(kho.btp.dong) as b:
			_chay(kho, lambda: btp.luu_refill("BAWC00123", "12", "2026-11-16", ""))
			d = kho.btp.dong[0]
			la("đã lưu", (d.so_refill, d.refill_tu, d.refill_den, kho.da_luu), (12, D8(2026, 11, 16), D8(2026, 11, 22), False))
			la("nhật ký ba ô refill", sorted(x["truong"] for x in b.nhat_ky), ["refill_den", "refill_tu", "so_refill"])
			nem("có refill thì không xoá mã", lambda: _chay(kho, lambda: btp.xoa_ma_btp("BAWC00123")), Exception)
			_chay(kho, lambda: btp.luu_refill("BAWC00123", "0", "", ""))
			la("0 thì bỏ", (d.so_refill, d.refill_tu, d.refill_den), (0, None, None))


@ca("v646 một phép cho 'ngày này thuộc refill của mã': bốn chỗ trừ decor đều gọi refill.ngay_cua_refill")
def _mot_nguon():
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	for tep, so in (("btp.py", 2), ("kiem_banh.py", 1), ("ton_don_web.py", 1), ("giu_ton_web.py", 2)):
		n = io.open(os.path.join(goc, tep), encoding="utf-8").read().count("refill.ngay_cua_refill(")
		dung("%s gọi đủ %d lần (được %d)" % (tep, so, n), n >= so)
	j = json.load(io.open(os.path.join(goc, "vagabond", "doctype", "btp_banh_o_dong", "btp_banh_o_dong.json"), encoding="utf-8"))
	la("ba ô mới trên bảng BTP", [f["fieldname"] for f in j["fields"]][-3:], ["so_refill", "refill_tu", "refill_den"])


@ca("v646 web tab Đặt trước: bánh có cả decor lẫn refill thì đơn ngày nằm trong refill không trừ decor (Kankin decor 5, đơn 11/11 thuộc refill)")
def _web_ca_hai():
	ka = dict(KANKIN, so_refill=10, refill_tu=D8(2026, 11, 11), refill_den=D8(2026, 11, 17))
	m = du_lieu_web(kankin=ka)
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("decor nguyên 5 (đơn 11/11 trừ vào refill)", s["BAWC00123"]["con"], 5)
	la("refill của Kankin còn nhận cả khi còn decor", s["BAWC00123"]["refill"]["chi_refill"], 0)


@ca("v646 giữ tồn web: ngày nhận trong khoảng refill thì không giữ theo Đủ decor; đơn ngày refill không trừ decor của ngày khác")
def _giu_ton():
	from types import SimpleNamespace as NS

	from vagabond import giu_ton_web as g

	def moi(refill_tu, dd=2):
		def sql(q, args=None, **kw):
			if "tabSingles" in q:
				return [("pancake_shop_id",)]
			if "tabKiem Banh Dong" in q:
				return [NS(ma_hang="A", ten_banh="Bánh A", co_the_ban=0, da_dat=dd)]
			if "tabBTP Banh O Dong" in q:
				return [NS(ma_hang="A", ten_banh="Bánh A", so_decor=3, so_refill=10 if refill_tu else 0,
					refill_tu=refill_tu, refill_den=(refill_tu + dt.timedelta(days=6)) if refill_tu else None)]
			if "tabVagabond Don Web" in q:
				return []
			raise AssertionError(q)
		return NS(db=NS(sql=sql))
	h = [{"variation_id": "A", "quantity": 1}]
	nay = D8(2026, 10, 14)
	with um.patch.object(g, "hom_nay", lambda: nay):
		with um.patch.object(g, "frappe", moi(None)):
			la("không refill: decor 3 trừ 3 ngày x 2 đơn = hết", bool(g.kiem_va_giu(h, "2026-10-16")[0]), True)
		with um.patch.object(g, "frappe", moi(D8(2026, 10, 15))):
			la("ngày 16/10 thuộc refill: không giữ theo decor", g.kiem_va_giu(h, "2026-10-16"), ([], None))
		with um.patch.object(g, "frappe", moi(D8(2026, 10, 16))):
			n, giu = g.kiem_va_giu(h, "2026-10-15")
			la("15/10 ngoài refill: decor 3 chỉ trừ đơn 15/10 (2), còn 1, nhận", (n, giu["dong"]), ([], {"A": 1}))


# ------------------------------------------------- Codex 549 vòng 1eefda8 (Refill)


class _BoNho:
	def __init__(self):
		self.d = {}

	def get_value(self, k, *a, **kw):
		return self.d.get(k)

	def set_value(self, k, v, *a, **kw):
		self.d[k] = v


def _dem_that(don, nay, dong, quay=()):
	"""Chạy refill.tinh THẬT tới tận dem_va_id: Pancake giả trả đơn theo NGÀY GIAO VN
	trong khoảng [đầu, cuối) mà máy hỏi, ghi lại ngày đầu đã hỏi."""
	import frappe
	from vagabond import dat_banh, kiem_banh, lib

	hoi = []

	def keo(c, k, truong, dau, cuoi):
		hoi.append(dau)
		return [o for o in don if dau <= rf.ngay(_ngay_vn(o["estimate_delivery_date"])) < cuoi]
	bn = _BoNho()
	with um.patch.object(kiem_banh, "_khoang_unix", lambda d: (d, d + dt.timedelta(days=1)), create=True), \
			um.patch.object(kiem_banh, "_keo_don", keo, create=True), \
			um.patch.object(dat_banh, "dong_tieu_thu", lambda tu, den: [x for x in quay if tu <= rf.ngay(x["delivery_date"]) < den], create=True), \
			um.patch.object(lib, "cfg", lambda: {}, create=True), um.patch.object(lib, "key", lambda c, n: "k", create=True), \
			um.patch.object(frappe, "cache", lambda: bn, create=True), \
			um.patch.object(frappe, "log_error", lambda *a, **k: None, create=True):
		return rf.tinh(nay, moi=True, dong=[Doi(x) for x in dong]), hoi


@ca("v646 Codex 549 (1eefda8) refill: đếm đơn từ NGÀY ĐẦU MẺ, không từ hôm nay (mẻ 20, ngày 14 đặt đủ 20: ngày 15 phải còn 0, trước bản sửa còn 20)")
def _dem_tu_dau_me():
	ro = dict(ROMAN, so_refill=20)
	don = [dict(_don("BAWC00068", "2026-11-14T03:00:00", 20), id="P-1")]
	kq, hoi = _dem_that(don, D8(2026, 11, 14), [ro])
	la("ngày 14: còn 0", kq["refill"]["BAWC00068"]["con"], 0)
	kq, hoi = _dem_that(don, D8(2026, 11, 15), [ro])
	la("ngày 15: vẫn còn 0 (trước: 20)", kq["refill"]["BAWC00068"]["con"], 0)
	la("Pancake được hỏi từ ngày đầu mẻ 14/11", hoi, [D8(2026, 11, 14)])
	la("mã đơn đã đếm đi kèm cùng lần kéo", kq["ids"], ["P-1"])
	la("thuần: ngày bắt đầu là ngày đầu mẻ sớm nhất", rf.ngay_bat_dau_dem({"A": {"tu": D8(2026, 11, 12)}, "B": {"tu": D8(2026, 11, 16)}},
		D8(2026, 11, 15)), D8(2026, 11, 12))
	la("thuần: mẻ chưa tới thì từ hôm nay", rf.ngay_bat_dau_dem({"A": {"tu": D8(2026, 11, 20)}}, D8(2026, 11, 15)), D8(2026, 11, 15))


def _giu_rf(dong_web, so_con, ids, hang, ngay, nay=D8(2026, 11, 12), loi=""):
	"""Chạy THẬT giu_ton_web.kiem_va_giu_refill với CSDL giả; ghi lại câu SQL và khoảng ngày hỏi đơn web."""
	import json as _j
	from types import SimpleNamespace as NS

	from vagabond import giu_ton_web as g

	hoi = []

	def sql(q, ts=None, as_dict=False):
		if "tabSingles" in q:
			return [("pancake_shop_id",)]
		if "tabBTP Banh O Dong" in q:
			return [NS(**ROMAN)]
		if "tabVagabond Don Web" in q:
			hoi.append((q, ts))
			return [dict(d, snapshot=_j.dumps(d["snapshot"])) for d in dong_web]
		raise AssertionError(q)

	def tinh(n, moi=False, dong=None):
		return {"refill": {"BAWC00068": {"con": so_con}}, "ids": ids, "loi": loi}
	with um.patch.object(g, "hom_nay", lambda: nay), um.patch.object(g, "frappe", NS(db=NS(sql=sql))), \
			um.patch.object(rf, "tinh", tinh):
		return g.kiem_va_giu_refill(hang, ngay), hoi


@ca("v646 Codex 549 (1eefda8) refill: hai khách cùng lấy suất cuối thì người sau bị chặn trong transaction tạo đơn (trước: cả hai qua)")
def _giu_suat_refill():
	from vagabond import giu_ton_web as g

	h = lambda n: [{"variation_id": "BAWC00068", "quantity": n}]
	(n, giu), hoi = _giu_rf([], 1, ["P-1"], h(1), "2026-11-15")
	la("khách A: còn 1, nhận, ghi suất", (n, giu), ([], {"dong": {"BAWC00068": 1}, "ngay": "2026-11-15"}))
	dung("đơn web tìm theo cột có chỉ mục, có khoá", "force index (vgb_ngay_nguon_ton)" in hoi[0][0] and "for update" in hoi[0][0])
	la("trong đúng khoảng mẻ", hoi[0][1], ("2026-11-14", "2026-11-20"))
	don_a = {"name": "W-A", "pancake_id": None, "snapshot": {g.O_RF: giu}}
	(n, giu2), _ = _giu_rf([don_a], 1, ["P-1"], h(1), "2026-11-16")
	la("khách B cùng lúc (A chưa lên Pancake): bị chặn", n, ["Roman De La Rose 18 ngày 16/11/2026 chỉ còn 0 cái, quý khách đang chọn 1 cái."])
	don_a["pancake_id"] = "P-9"
	(n, _), _ = _giu_rf([don_a], 1, ["P-1"], h(1), "2026-11-16")
	dung("A đã lên Pancake nhưng lần đếm chưa có A: vẫn trừ", bool(n))
	(n, _), _ = _giu_rf([don_a], 0, ["P-1", "P-9"], h(1), "2026-11-16")
	dung("lần đếm đã có A: Pancake trừ rồi, không trừ hai lần (còn 0 là do Pancake)", bool(n))
	(n, _), _ = _giu_rf([don_a], 1, ["P-1", "P-9"], h(1), "2026-11-16")
	la("lần đếm có A và còn 1: nhận", n, [])
	(n, giu), _ = _giu_rf([], 0, [], h(1), "2026-11-25")
	la("ngoài khoảng mẻ: không giữ refill (cửa ngoài đã nhắc chọn ngày)", (n, giu), ([], None))
	(n, giu), _ = _giu_rf([don_a], 0, [], h(1), "2026-11-15", loi="Chưa đếm được")
	la("chưa đếm được Pancake: không chặn nhưng vẫn ghi suất", (n, giu), ([], {"dong": {"BAWC00068": 1}, "ngay": "2026-11-15"}))
	la("đơn chỉ giữ refill có ngày trên cột chỉ mục", g.ngay_nguon({g.O_RF: {"dong": {"A": 1}, "ngay": "2026-11-15"}}, "2026-11-15 10:00"), "2026-11-15")
	la("đơn giữ decor vẫn theo ngày decor", g.ngay_nguon({g.O: {"dong": {"A": 1}, "ngay_nguon": "2026-11-13"}}, "2026-11-13"), "2026-11-13")


@ca("v646 Codex 549 (1eefda8) refill: cửa tạo đơn web gọi giữ suất refill trong cùng transaction và ghi suất vào đơn")
def _cua_tao_don():
	import io
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	src = io.open(os.path.join(goc, "don_hang.py"), encoding="utf-8").read()
	i, j = src.index("giu_ton_web.kiem_va_giu(hang_goc, ngay)"), src.index("giu_ton_web.kiem_va_giu_refill(hang_goc, ngay)")
	dung("giữ refill ngay sau giữ decor, trong cùng savepoint", 0 < j - i < 400)
	dung("ghi suất vào snapshot đơn", "snapshot[giu_ton_web.O_RF] = giu_rf" in src)
	# Dò chuỗi chỉ chốt đường nối; hành vi giữ suất nằm ở ca _giu_suat_refill.


@ca("v646 Codex 549 (1eefda8) refill: lưu lại đơn web bản đọc trước không xoá mất suất refill đã giữ")
def _bao_ve_suat():
	import json as _j
	from types import SimpleNamespace as NS

	from vagabond import giu_ton_web as g

	that = {g.O_RF: {"dong": {"BAWC00068": 1}, "ngay": "2026-11-15"}, "x": 1}
	doc = NS(name="W-A", ngay_nhan="2026-11-15 10:00", snapshot=_j.dumps({"x": 2}), is_new=lambda: False)
	with um.patch.object(g, "frappe", NS(db=NS(get_value=lambda *a, **k: _j.dumps(that)))):
		g.bao_ve(doc)
	moi = _j.loads(doc.snapshot)
	la("suất refill giữ nguyên, phần khác theo bản mới", (moi.get(g.O_RF), moi.get("x")), (that[g.O_RF], 2))
	la("ngày trên cột chỉ mục", getattr(doc, g.O_NGAY), "2026-11-15")


@ca("v646 Codex 549 (58ba797) refill: phiếu đặt tại quầy đã giao xong vẫn ăn vào mẻ (mẻ 20, phiếu quầy 20 giao xong: còn 0, trước bản sửa còn 20)")
def _quay_da_giao():
	ro = dict(ROMAN, so_refill=20)
	q = lambda tt, sl, giao, hd=0, ngay="2026-11-14": {"item_code": "BAWC00068", "delivery_date": ngay, "qty": sl,
		"delivered_qty": giao, "billed_qty": hd, "trang_thai": tt}
	kq, _ = _dem_that([], D8(2026, 11, 14), [ro], [q("To Deliver and Bill", 20, 0)])
	la("phiếu quầy 20 còn chờ giao: còn 0", kq["refill"]["BAWC00068"]["con"], 0)
	kq, _ = _dem_that([], D8(2026, 11, 15), [ro], [q("Completed", 20, 20, 20)])
	la("phiếu quầy 20 đã giao xong: vẫn còn 0 (trước: 20)", kq["refill"]["BAWC00068"]["con"], 0)
	kq, _ = _dem_that([], D8(2026, 11, 15), [ro], [q("Closed", 20, 5)])
	la("phiếu đóng sau khi giao 5: ăn 5, còn 15", kq["refill"]["BAWC00068"]["con"], 15)
	kq, _ = _dem_that([], D8(2026, 11, 15), [ro], [q("Closed", 20, 0, 8)])
	la("phiếu đóng, giao qua hoá đơn 8 (chưa có phiếu giao): ăn 8, còn 12", kq["refill"]["BAWC00068"]["con"], 12)
	kq, _ = _dem_that([], D8(2026, 11, 15), [ro], [q("To Bill", 20, 0, 12)])
	la("đã xuất hoá đơn 12 nhưng phiếu còn mở: ăn đủ 20", kq["refill"]["BAWC00068"]["con"], 0)
	la("thuần: mã không phải bánh ổ bị bỏ", rf.tieu_thu_phieu_dat([dict(q("Completed", 3, 3), item_code="NVL001")], ("BAWC",)), {})
