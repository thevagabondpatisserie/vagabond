# -*- coding: utf-8 -*-
"""v645 (anh Việt 08/11/2026): giảm 50.000 đ cho đơn web đầu tiên của một số.

Ba điều anh chốt: số CHƯA TỪNG có đơn web (đơn đã huỷ không tính); không cộng
với mã hay chương trình khác, máy giữ cái giảm nhiều hơn; tiền bánh từ
300.000 đ. Số phải xác thực bằng mã Zalo (phiên Thành viên) và trùng số trên
đơn.

Các ca chạy hàm THẬT: phép thuần của don_dau_web; xem_uu_dai và tao_don nạp từ
mã nguồn don_hang.py trong đúng môi trường các ca #367 dùng, chỉ thay phần đọc
site (đã có đơn web chưa, số của phiên) và mạng.
"""

import contextlib
import json
import re
import types
from types import SimpleNamespace as NS

from vagabond import don_dau_web as dd
from vagabond import don_web
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_don_web_367 import DIEM_KHONG, _Tra, _dau_gia, _don, _km_gia, _moi_truong_tao_don
from vagabond.khung.kiem_thu.thu_su_co_290 import nap

SO = "0931224334"   # số của _don() trong bộ #367
SO84 = "84931224334"


# ------------------------------------------------------------------ phép thuần

@ca("v645 chin_so và bien_the: 0931..., 84931..., +84 931 ... là một số; số lạ thì rỗng")
def _():
	la("ba cách viết một số", {dd.chin_so(x) for x in (SO, SO84, "+84 931 224 334", "931224334")}, {"931224334"})
	la("số cố định 8 chữ hay số dài thì không đọc", (dd.chin_so("38123456"), dd.chin_so("0931224334999"), dd.chin_so(None)), ("", "", ""))
	la("ba biến thể dò ô điện thoại của đơn web", dd.bien_the("+84 931 224 334"), ["0931224334", "84931224334", "931224334"])
	la("số lạ không dò gì", dd.bien_the("abc"), [])


@ca("v645 trang_thai: đã có đơn web thì không hiện; chưa mở Zalo thì không hiện; dưới 300.000 nói còn thiếu; đúng 300.000 là đủ; phiên khác số thì phải xác thực")
def _():
	t = dd.trang_thai
	la("số hỏng", t("12", False, "", 500000, True), dd.KHONG)
	la("đã có đơn web", t(SO, True, SO84, 500000, True), dd.KHONG)
	la("chưa cấu hình gửi mã Zalo", t(SO, False, SO84, 500000, False), dd.CHUA_MO)
	la("299.999 chưa đủ", t(SO, False, SO84, 299999, True), dd.CHUA_DU_TIEN)
	la("đúng 300.000 là đủ, đã xác thực", t(SO, False, SO84, 300000, True), dd.DU)
	la("chưa đăng nhập", t(SO, False, "", 500000, True), dd.CAN_XAC_THUC)
	la("phiên của số khác: không cho giảm theo số trên đơn", t(SO, False, "84901234567", 500000, True), dd.CAN_XAC_THUC)


@ca("v645 tron: không cộng, giữ cái lớn hơn; bằng nhau giữ mã; mã sai giữ nguyên để báo lỗi mã")
def _():
	def ma(g, ly_do=""):
		return {"tong_giam": g, "ap": [{"ma": "SN", "ten": "Giảm SN", "giam": g}] if g else [], "ly_do": ly_do, "kq": {"x": 1}}

	uu, bo = dd.tron(ma(30000), dd.CAN_XAC_THUC, True)
	la("chưa xác thực thì giữ mã", (uu["tong_giam"], bo, uu.get("don_dau")), (30000, False, None))
	uu, bo = dd.tron(ma(30000), dd.DU, True)
	la("mã 30.000 thua 50.000: dùng ưu đãi đơn đầu, cờ bỏ mã", (uu["tong_giam"], bo, uu["don_dau"], uu["ma"], uu["kq"]), (50000, True, 1, "", None))
	la("dòng ưu đãi mang tên dễ đọc, không mã", uu["ap"], [{"ma": "", "ten": dd.TEN, "giam": 50000, "dien_giai": "", "don_dau": 1}])
	uu, bo = dd.tron(ma(50000), dd.DU, True)
	la("bằng nhau giữ mã khách gõ (không tốn lần đầu)", (uu["tong_giam"], bo, uu.get("don_dau")), (50000, False, None))
	uu, bo = dd.tron(ma(90000), dd.DU, True)
	la("mã 90.000 thắng", (uu["tong_giam"], bo, uu.get("don_dau")), (90000, False, None))
	uu, bo = dd.tron(ma(0, ly_do="Mã hết hạn."), dd.DU, True)
	la("mã sai: giữ lỗi mã", (uu["ly_do"], uu.get("don_dau")), ("Mã hết hạn.", None))
	uu, bo = dd.tron(ma(20000), dd.DU, False)
	la("chương trình tự áp 20.000 (không gõ mã): dùng đơn đầu, không có mã để bỏ", (uu["tong_giam"], bo), (50000, False))
	uu, bo = dd.tron(None, dd.DU, False)
	la("không có ưu đãi nào", uu["tong_giam"], 50000)


# ------------------------------------------------------------------ chạm site

@ca("v645 da_dat_web: dò đủ ba cách viết số, bỏ đơn đã huỷ; số hỏng không chạm site")
def _():
	import frappe
	goi = []
	cu = getattr(frappe, "db", None)
	frappe.db = NS(exists=lambda dt, f: (goi.append((dt, f)), True)[1])
	try:
		co = dd.da_dat_web("+84 931 224 334")
		khong = dd.da_dat_web("12")
	finally:
		frappe.db = cu
	la("có đơn", (co, khong), (True, False))
	la("một lần đọc, đúng bảng và bộ lọc", goi, [("Vagabond Don Web", {
		"dien_thoai": ["in", ["0931224334", "84931224334", "931224334"]], "trang_thai": ["!=", "Da huy"]})])


@ca("v645 sdt_phien: đọc phiên Thành viên; lỗi đọc thì coi như chưa đăng nhập (không bao giờ giảm oan) và ghi Error Log")
def _():
	import sys
	import frappe
	log = []
	cu_tv = sys.modules.get("vagabond.thanh_vien")
	cu_log, cu_tb = getattr(frappe, "log_error", None), getattr(frappe, "get_traceback", None)
	frappe.log_error = lambda *a, **k: log.append(k.get("title"))
	frappe.get_traceback = lambda: ""
	import vagabond
	cu_attr = getattr(vagabond, "thanh_vien", None)
	try:
		gia = types.ModuleType("vagabond.thanh_vien")
		gia._so_phien = lambda: SO84
		sys.modules["vagabond.thanh_vien"] = gia
		vagabond.thanh_vien = gia
		dung_so = dd.sdt_phien()

		def hong():
			raise RuntimeError("cookie hỏng")
		gia._so_phien = hong
		loi = dd.sdt_phien()
	finally:
		if cu_tv is not None:
			sys.modules["vagabond.thanh_vien"] = cu_tv
		else:
			sys.modules.pop("vagabond.thanh_vien", None)
		if cu_attr is not None:
			vagabond.thanh_vien = cu_attr
		frappe.log_error, frappe.get_traceback = cu_log, cu_tb
	la("số phiên", dung_so, SO84)
	la("lỗi thì rỗng, có Error Log", (loi, len(log)), ("", 1))


@ca("v645 xet: số hỏng trả Không mà không đọc site; số tốt ghép đủ bốn nguồn")
def _():
	vet = []
	cu = (dd.da_dat_web, dd.sdt_phien, dd.otp_mo)
	dd.da_dat_web = lambda s: (vet.append("da_dat"), False)[1]
	dd.sdt_phien = lambda: (vet.append("phien"), SO84)[1]
	dd.otp_mo = lambda: (vet.append("otp"), True)[1]
	try:
		hong = dd.xet("12", 500000)
		vet_hong = list(vet)
		tot = dd.xet(SO, 500000)
	finally:
		dd.da_dat_web, dd.sdt_phien, dd.otp_mo = cu
	la("số hỏng: không đọc site", (hong, vet_hong), (dd.KHONG, []))
	la("số tốt, đã xác thực", tot, dd.DU)


# ------------------------------------------------------------------ xem_uu_dai

def _xem(ap_giam=0, ly_do="", dau=None, xet_loi=False):
	"""xem_uu_dai THẬT nạp từ don_hang.py, giá 450.000 mỗi dòng."""
	log = []
	dau = dau or _dau_gia()
	if xet_loi:
		def hong(*a):
			raise RuntimeError("site hỏng")
		dau.xet = hong
	km = _km_gia(giam=ap_giam, ly_do=ly_do)
	g = dict(
		json=json, re=re, don_web=don_web, don_dau_web=dau, khuyen_mai=km,
		frappe=NS(log_error=lambda *a, **k: log.append(k.get("title")), get_traceback=lambda: ""),
		_gia_va_ten=lambda ds: ({m: 450000 for m in ds}, {m: "Bánh " + m for m in ds}),
		MAX_DONG=30, MAX_SL=20,
	)
	for ten in ("_so", "_lam_sach_hang", "_ngay_iso", "_uu_dai_don", "_don_dau", "_diem_don", "_diem_hien"):
		nap("don_hang.py", ten, g)
	# v652: điểm thành viên web; ca đơn đầu không dùng điểm.
	g["TEN_DIEM"] = "Điểm thành viên"
	g["diem_web"] = DIEM_KHONG
	return nap("don_hang.py", "xem_uu_dai", g), dau, km, log


@ca("v645 xem_uu_dai: đủ điều kiện thì giỏ hiện giảm 50.000 và thẻ Đã áp; mã nhỏ hơn bị thay, báo bỏ mã")
def _():
	xem, dau, km, _log = _xem(ap_giam=30000, dau=_dau_gia(trang_thai=dd.DU))
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": SO, "ma_uu_dai": "sn10"})
	la("giảm 50.000, một dòng tên dễ đọc", (r["ok"], r["giam"], r["ap"]), (1, 50000, [{"ten": dd.TEN, "giam": 50000}]))
	la("phần thẻ cho trang", r["don_dau"], {"trang_thai": dd.DU, "giam": 50000, "toi_thieu": 300000, "can_otp": 1, "hien": 1, "ap_dung": 1, "bo_ma": 1})
	la("xét theo số trên đơn và tiền bánh máy chủ tính", dau.vet.xet, [("0931224334", 450000)])


@ca("v645 xem_uu_dai: chưa xác thực thì vẫn giữ mã, thẻ mời xác thực; mã sai vẫn báo lỗi mã kèm thẻ")
def _():
	xem, _d, _k, _l = _xem(ap_giam=30000, dau=_dau_gia(trang_thai=dd.CAN_XAC_THUC))
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": SO, "ma_uu_dai": "SN10"})
	la("giữ mã 30.000", (r["giam"], r["don_dau"]["trang_thai"], r["don_dau"]["ap_dung"]), (30000, dd.CAN_XAC_THUC, 0))
	xem, _d, _k, _l = _xem(ly_do="Mã SN10: chương trình đã hết hạn.", dau=_dau_gia(trang_thai=dd.DU))
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": SO, "ma_uu_dai": "SN10"})
	la("mã sai: lỗi mã, không lặng lẽ thay bằng đơn đầu", (r["ok"], r["ly_do"], r["giam"], r["don_dau"]["ap_dung"]), (0, "ma_uu_dai", 0, 0))


@ca("v645 xem_uu_dai: đọc site hỏng thì không có ưu đãi, giỏ vẫn hiện bình thường, ghi Error Log")
def _():
	xem, _d, _k, log = _xem(ap_giam=0, xet_loi=True)
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": SO})
	la("không giảm, thẻ ẩn", (r["ok"], r["giam"], r["don_dau"]["trang_thai"]), (1, 0, dd.KHONG))
	la("một Error Log", len(log), 1)


# ------------------------------------------------------------------ tao_don

def _tao(dau, km=None, don=None, pancake=None):
	vet, tao_don = _moi_truong_tao_don(pancake or (lambda v: _Tra(200, {"data": {"id": "91500"}})), km=km, dau=dau)
	r = tao_don(_don(**(don or {})))
	return r, vet


@ca("v645 tao_don: đủ điều kiện, không mã: Pancake nhận giảm 50.000, ảnh chụp ghi ưu đãi đơn đầu; khoá theo số, xét lại SAU commit và TRƯỚC khi ghi; không giữ lượt nào")
def _():
	dau = _dau_gia(trang_thai=dd.DU)
	r, vet = _tao(dau, don={"giam_da_xem": 50000})
	la("đơn thành", r.get("ok"), 1)
	sn = json.loads(vet.truong["snapshot"])
	la("ảnh chụp ưu đãi", sn["uu_dai"], {"ma": "", "giam": 50000, "ap": [{"ma": "", "ten": dd.TEN, "giam": 50000, "dien_giai": "", "don_dau": 1}], "don_dau": 1})
	la("Pancake nhận đủ 50.000 giảm trên các dòng", sum(x.get("discount_each_product", 0) * x["quantity"] for x in vet.body["items"]), 50000)
	la("khoá đúng số, xét lại một lần", (dau.vet.khoa, dau.vet.da_dat), (["0931224334"], ["0931224334"]))
	su = [x for x in vet.su if isinstance(x, str)]
	dung("commit trước lúc xét lại và trước khi ghi bản ghi", su.index("commit") < su.index("ghi"))
	la("không giữ mã, không giữ lượt chương trình", (vet.km.vet.giu, vet.km.vet.ghi, vet.km.vet.khoa), ([], [], []))


@ca("v645 tao_don: khách gõ mã 30.000 mà đủ điều kiện đơn đầu: dùng 50.000, bỏ mã (không giữ mã dùng một lần)")
def _():
	dau = _dau_gia(trang_thai=dd.DU)
	r, vet = _tao(dau, km=_km_gia(giam=30000, mot_lan=True), don={"ma_uu_dai": "SN10", "giam_da_xem": 50000})
	la("đơn thành", r.get("ok"), 1)
	sn = json.loads(vet.truong["snapshot"])
	la("ảnh chụp không mang mã", (sn["uu_dai"]["ma"], sn["uu_dai"]["giam"], sn["uu_dai"]["don_dau"]), ("", 50000, 1))
	la("mã dùng một lần KHÔNG bị giữ", (vet.km.vet.giu, vet.km.vet.ghi), ([], []))


@ca("v645 tao_don: mã 90.000 lớn hơn thì đi đường mã như cũ, không khoá theo số, không xét lại")
def _():
	dau = _dau_gia(trang_thai=dd.DU)
	r, vet = _tao(dau, km=_km_gia(giam=90000), don={"ma_uu_dai": "SN10", "giam_da_xem": 90000})
	la("đơn thành", r.get("ok"), 1)
	sn = json.loads(vet.truong["snapshot"])
	la("ưu đãi là mã", (sn["uu_dai"]["ma"], sn["uu_dai"]["giam"], "don_dau" in sn["uu_dai"]), ("SN10", 90000, False))
	la("không đụng phần đơn đầu", (dau.vet.khoa, dau.vet.da_dat), ([], []))
	dung("giữ lượt như cũ", len(vet.km.vet.ghi) == 1)


@ca("v645 tao_don: hai đơn cùng số gửi cùng lúc: đơn sau xét lại dưới khoá thấy số đã có đơn web thì KHÔNG ghi, KHÔNG gửi Pancake, trả tổng mới (mã cũ của khách) để bấm lại")
def _():
	dau = _dau_gia(trang_thai=dd.DU, da_dat=True)
	r, vet = _tao(dau, km=_km_gia(giam=30000), don={"ma_uu_dai": "SN10", "giam_da_xem": 50000})
	la("báo ưu đãi đổi kèm số của mã", (r.get("ok"), r.get("ly_do"), r["uu"]["giam"]), (0, "uu_dai_doi", 30000))
	dung("không ghi bản ghi, không gọi Pancake", "ghi" not in vet.su and "post" not in vet.su)
	la("không giữ gì", (vet.km.vet.giu, vet.km.vet.ghi), ([], []))


@ca("v645 tao_don: trang còn hiện giảm cũ (khách thấy 0) mà máy chủ nay cho 50.000 thì vẫn bắt xem tổng mới rồi bấm lại")
def _():
	r, vet = _tao(_dau_gia(trang_thai=dd.DU), don={"giam_da_xem": 0})
	la("uu_dai_doi kèm 50.000", (r.get("ly_do"), r["uu"]["giam"]), ("uu_dai_doi", 50000))
	dung("không ghi", "ghi" not in vet.su)


@ca("v645 tao_don: chưa xác thực số (phiên trống hay phiên số khác) thì không giảm, đơn vẫn đi")
def _():
	r, vet = _tao(_dau_gia(trang_thai=dd.CAN_XAC_THUC), don={"giam_da_xem": 0})
	la("đơn thành, không ưu đãi", (r.get("ok"), json.loads(vet.truong["snapshot"])["uu_dai"]), (1, None))


@ca("v645 tao_don: đọc site hỏng khi xét đơn đầu thì không giảm và không chặn đơn")
def _():
	dau = _dau_gia(trang_thai=dd.DU)

	def hong(*a):
		raise RuntimeError("site hỏng")
	dau.xet = hong
	r, vet = _tao(dau, don={"giam_da_xem": 0})
	la("đơn thành, không ưu đãi", (r.get("ok"), json.loads(vet.truong["snapshot"])["uu_dai"]), (1, None))
	dung("có Error Log đúng tên", "Vagabond: ưu đãi đơn đầu tiên trên web" in vet.log)


@ca("v645 tao_don: Pancake từ chối đơn có ưu đãi đơn đầu thì không có lượt nào để trả, không giữ mã nào")
def _():
	dau = _dau_gia(trang_thai=dd.DU)
	r, vet = _tao(dau, don={"giam_da_xem": 50000}, pancake=lambda v: _Tra(422, {"success": False, "message": "sai"}))
	la("từ chối", r.get("ok"), 0)
	la("không trả mã nào (không giữ)", vet.km.vet.tra, [])
