# -*- coding: utf-8 -*-
"""v671 (Sales góp ý 18/11/2026, giám đốc chốt): tab Đặt bánh trước của web
nhận NGÀY MAI, số theo cột Bán được (Có thể bán) của phiếu Kiểm bánh ngày mai,
cùng cách với tab Có sẵn hôm nay. Trước v671 tab theo ô Đủ decor của bảng BTP,
nhận 3 ngày tới, lịch cho chọn tới 2 tuần.

Các ca chạy hàm THẬT (con_dat_truoc_mai, _dat_truoc_theo_decor, dong_bo_tu_dong,
_dong_bo_mot_lan, chan_dat_truoc_ngay_xa), chỉ thay tầng Frappe bằng bản giả.
Phần trang khách nằm ở hanh_vi/dat_truoc_tu_mai_649.mjs (ca 8, 9) và
hanh_vi/web_vue_banh.mjs (refill).
"""
import datetime
import types
from unittest.mock import patch

import frappe

from vagabond import kiem_banh as kb
from vagabond import ton_don_web as ton
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la
from vagabond.khung.kiem_thu.thu_cot_huy_kiem_banh import BangGia, CuaGia, _tao_dong
from vagabond.khung.kiem_thu.thu_len_web_606 import NGAY, _chay, _dong

D = types.SimpleNamespace


@ca("v671 phép thuần con_dat_truoc_mai: cột Có thể bán của phiếu ngày mai; bỏ bánh sỉ, số không dương, ngày mai thuộc mẻ refill; cộng dòng trùng mã")
def _thuan():
	dong = [D(ma_hang="A", co_the_ban=3), D(ma_hang="A", co_the_ban=1), D(ma_hang="BAWS001", co_the_ban=5),
		D(ma_hang="B", co_the_ban=0), D(ma_hang="C", co_the_ban=-2), D(ma_hang="R", co_the_ban=4), D(ma_hang=None, co_the_ban=9),
		D(ma_hang="E", co_the_ban=None)]
	la("chỉ còn A", kb.con_dat_truoc_mai(dong, lambda ma: ma == "R"), {"A": 4})
	la("không có hàm refill: R vẫn tính", kb.con_dat_truoc_mai(dong), {"A": 4, "R": 4})
	la("phiếu rỗng", kb.con_dat_truoc_mai(None), {})


@ca("v671 tab Đặt bánh trước: ngày mai đọc phiếu NGÀY MAI (không phải hôm nay); v675 Đủ decor chỉ cho ngày kia và ngày thứ ba")
def _phieu_mai():
	nay = [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=7, hinh="")]
	mai = [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=2, hinh="")]
	decor = [_dong(ma_hang="BAWC00089", ten_banh="Very Berry", so_decor=9, hinh="", so_refill=0, refill_tu=None, refill_den=None)]
	kq = _chay(kb._dat_truoc_theo_decor, kiem_hom_nay=nay, decor=decor, kiem_mai=mai)
	la("ngày mai theo phiếu (2), ngày kia theo Đủ decor (9)", [(s["ma"], s["con"], s["con_mai"], s["con_xa"]) for g in kq["nhom"] for s in g["sizes"]],
		[("BAWC00089", 2, 2, 9)])
	kq = _chay(kb._dat_truoc_theo_decor, kiem_hom_nay=nay, decor=decor)
	la("chưa có phiếu ngày mai: ngày mai 0 (tủ hôm nay 7 không tính), ngày kia theo Đủ decor 9",
		[(s["con_mai"], s["con_xa"]) for g in kq["nhom"] for s in g["sizes"]], [(0, 9)])
	kq = _chay(kb._dat_truoc_theo_decor, kiem_mai=[_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=0, hinh="")], decor=decor)
	la("phiếu ngày mai hết (0): ngày mai 0, ngày kia vẫn theo Đủ decor", [(s["con_mai"], s["con_xa"]) for g in kq["nhom"] for s in g["sizes"]], [(0, 9)])
	kq = _chay(kb._dat_truoc_theo_decor, kiem_mai=[_dong(ma_hang="BAWC00089", ten_banh="Very Berry", co_the_ban=0, hinh="")],
		decor=[_dong(ma_hang="BAWC00089", ten_banh="Very Berry", so_decor=0, hinh="", so_refill=0, refill_tu=None, refill_den=None)])
	la("phiếu ngày mai hết và không có Đủ decor: không lên", kq["nhom"], [])


@ca("v671 nhịp 5 phút đếm cả phiếu ngày mai khi bếp đã mở; chưa có phiếu thì không tự tạo; lỗi ngày mai không làm hỏng ngày hôm nay")
def _nhip():
	goi, loi = [], []
	co = {"KB-%s" % (NGAY + datetime.timedelta(days=1))}
	with patch.object(kb, "dong_bo", lambda ngay=None: goi.append(ngay)), patch.object(kb, "getdate", lambda *a: NGAY), \
			patch.object(frappe.db, "exists", lambda dt, ten: ten in co, create=True), \
			patch.object(frappe, "log_error", lambda *a, **k: loi.append(k.get("title")), create=True):
		kb.dong_bo_tu_dong()
		la("hôm nay rồi ngày mai", goi, [None, NGAY + datetime.timedelta(days=1)])
		co.clear(); goi.clear()
		kb.dong_bo_tu_dong()
		la("chưa có phiếu ngày mai: chỉ hôm nay", goi, [None])

	def hong(ngay=None):
		goi.append(ngay)
		if ngay:
			raise RuntimeError("Pancake 429")
	co.add("KB-%s" % (NGAY + datetime.timedelta(days=1))); goi.clear()
	with patch.object(kb, "dong_bo", hong), patch.object(kb, "getdate", lambda *a: NGAY), \
			patch.object(frappe.db, "exists", lambda dt, ten: ten in co, create=True), \
			patch.object(frappe, "log_error", lambda *a, **k: loi.append(k.get("title")), create=True), \
			patch.object(frappe, "get_traceback", lambda: "tb", create=True):
		kb.dong_bo_tu_dong()
	la("hôm nay vẫn chạy trước", goi[0], None)
	dung("lỗi ngày mai ghi riêng", "Vagabond: dong bo kiem banh ngay mai loi" in loi)


@ca("v671 đồng bộ phiếu NGÀY MAI đánh dấu đã đếm MỌI đơn giao ngày đó (cả đơn Mới), vì Có thể bán trừ cả Chờ chốt; trước v671 chỉ đơn đã chốt")
def _da_dem_mai():
	from vagabond import giu_ton_web, pancake_nhip

	mai = BangGia(ngay="2026-11-15", dong=[_tao_dong(ma_hang="BAWC00019", ten_banh="Bánh Ổ Epi, size 12cm", sx=3)])
	cua = CuaGia(**{"KB-2026-11-15": mai})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	moi = {"id": "P-MOI", "status": 0, "items": [{"variation_info": {"display_id": "BAWC00019"}, "quantity": 1}]}
	chot = {"id": "P-CHOT", "status": 1, "items": [{"variation_info": {"display_id": "BAWC00019"}, "quantity": 1}]}
	don = {"estimate_delivery_date": [moi, chot], "inserted_at": []}
	dem = []
	cu = {k: getattr(kb, k) for k in ("_keo_don", "cfg", "key", "_dem_don_khac", "_con_nghi")}
	cu_g = (giu_ton_web.khoa, giu_ton_web.da_dem, giu_ton_web.hom_nay, pancake_nhip.ghi_ok)
	cu_db = (frappe.db.get_value, getattr(frappe.db, "set_value", None), frappe.db.commit)
	kb._keo_don = lambda c, k, kieu, dau, cuoi: don[kieu]
	kb.cfg = lambda: Doi({"pancake_shop_id": "1"})
	kb.key = lambda c, t: "k"
	kb._dem_don_khac = lambda ngay, theo_doi=None: ({}, {})
	kb._con_nghi = lambda ngay: 0
	giu_ton_web.khoa = lambda: None
	giu_ton_web.da_dem = lambda ngay, ids: dem.append((str(ngay), sorted(ids)))
	giu_ton_web.hom_nay = lambda: datetime.date(2026, 11, 14)
	pancake_nhip.ghi_ok = lambda: None
	frappe.db.get_value = lambda *a, **k: None
	frappe.db.set_value = lambda *a, **k: None
	frappe.db.commit = lambda: None
	try:
		with cua, patch.object(kb, "_ghi_giu_cho", lambda doc, ngay: None), patch.object(frappe, "cache", lambda: Doi({"get_value": lambda k: 1, "set_value": lambda *a, **k: None}), create=True):
			kb._dong_bo_mot_lan("2026-11-15")
	finally:
		for k, v in cu.items():
			setattr(kb, k, v)
		giu_ton_web.khoa, giu_ton_web.da_dem, giu_ton_web.hom_nay, pancake_nhip.ghi_ok = cu_g
		frappe.db.get_value, frappe.db.commit = cu_db[0], cu_db[2]
		if cu_db[1] is not None:
			frappe.db.set_value = cu_db[1]
	la("đánh dấu cả đơn Mới và đơn đã chốt", dem, [("2026-11-15", ["P-CHOT", "P-MOI"])])
	d = mai.dong[0]
	la("Chờ chốt và Đã đặt của ngày mai", (d.cho_chot, d.da_dat), (1, 1))


@ca("v671 phép thuần chan_dat_truoc_ngay_xa: bánh đặt trước chọn ngày xa hơn ngày mai thì nhắc; món khác không đụng")
def _ngay_xa():
	ten = {"BAWC00019": "Bánh Ổ Epi 12cm"}
	r = ton.chan_dat_truoc_ngay_xa([{"variation_id": "BAWC00019", "quantity": 1}, {"variation_id": "PKNEN", "quantity": 2}], ten, datetime.date(2026, 11, 20))
	la("một câu", len(r), 1)
	dung("nói rõ 3 ngày tới và ngày khách chọn (v675)", "nhận trong 3 ngày tới" in r[0] and "20/11/2026" in r[0] and "Bánh Ổ Epi 12cm" in r[0])
	la("hàng rỗng", ton.chan_dat_truoc_ngay_xa(None, ten, datetime.date(2026, 11, 20)), [])


@ca("v671 bánh có mẻ refill, ngày mai NGOÀI mẻ: đơn ngày mai theo Có thể bán của phiếu ngày mai; phiếu không còn thì nhắc chọn ngày trong mẻ")
def _refill_ngoai_me():
	from vagabond.khung.kiem_thu import thu_refill_646 as rf

	ka = dict(rf.KANKIN, so_decor=9, so_refill=10, refill_tu=datetime.date(2026, 11, 13), refill_den=datetime.date(2026, 11, 19))

	def kiem(sl, ctb):
		kho = rf.Kho([ka], {"KB-2026-11-11": [{"ma_hang": "BAWC00123", "ten_banh": "Kankin 16", "co_the_ban": ctb}]})
		return rf._chay(kho, lambda: ton.kiem([{"variation_id": "BAWC00123", "quantity": sl}], "2026-11-11"), rf._tinh_that(don=[]))
	la("phiếu ngày mai còn 3, đặt 2: nhận", kiem(2, 3), [])
	dung("đặt 4: còn 3 (Đủ decor 9 không tính)", "còn 3 cái" in "".join(kiem(4, 3)))
	r = kiem(1, 0)
	dung("phiếu hết: nhắc chọn ngày trong mẻ", len(r) == 1 and "từ 13/11 tới 19/11" in r[0])
