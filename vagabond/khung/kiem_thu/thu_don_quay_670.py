# -*- coding: utf-8 -*-
"""v670 đơn giao của quầy (Minh Vũ 17/11/2026, anh Việt đồng ý gom vào PR #585).

Ca chốt:
  - Combo cho đơn giao: luật bán xét kênh WEBORDER (anh Việt 17/11: một chữ cho
    kênh này ở mọi chỗ cài đặt; don_quay.nguon_combo), một nguồn cho bảng món lúc
    đặt (goi_mon_ban.bang_mon kênh Giao), trang khách (kiem_kho) và phiếu quầy rã
    combo (cờ vgb_nguon_luat); đơn bàn giữ hai nguồn Tại chỗ, QR tại bàn.
  - Mã đơn WO-YYMMDD-5 số và O2O-YYMMDD-5 số, số chạy theo tháng (ma_don); mã
    chuyển khoản, trả thẻ của đơn WO đi đúng đường đơn web như DW.
  - Trang khách gộp combo hai kênh thành một danh sách mang cờ tai_ban, giao và số
    bộ riêng của kênh Giao (gop_combo_kenh).
"""

import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("v670 gộp combo hai kênh: cờ tai_ban, giao và con_giao đúng; combo chỉ bán Giao đứng sau; không trùng mã")
def _():
	from vagabond import kiem_kho

	ra = kiem_kho.gop_combo_kenh([{"ma": "KMCB1", "con": 5}, {"ma": "KMCB2", "con": 3}], [{"ma": "KMCB1", "con": 2}, {"ma": "KMCB9", "con": 4}])
	la("cờ", [(c["ma"], co) for c, co in ra], [("KMCB1", {"tai_ban": 1, "giao": 1, "con_giao": 2}),
		("KMCB2", {"tai_ban": 1, "giao": 0}), ("KMCB9", {"tai_ban": 0, "giao": 1, "con_giao": 4})])
	la("giữ số bộ Tại bàn", [c["con"] for c, _co in ra], [5, 3, 4])
	la("rỗng", kiem_kho.gop_combo_kenh([], []), [])


def _combo_gia(goi_mon_ban, cho_nguon):
	"""Bộ giả biên Frappe cho doc_combo_ban: hai combo cố định, luật bán theo nguồn."""
	from vagabond import combo_mon, khuyen_mai

	hoi = []

	def ly_do(cb, ma, quay="", nguon=""):
		hoi.append((ma, nguon))
		return "" if nguon in cho_nguon.get(ma, ()) else "không bán nguồn %s" % nguon
	cb = {"ten": "Combo", "dong": [{"item_code": "NU1", "ten_mon": "Trà", "so_luong": 1, "gia_goc": 50000}], "mo_ta": "", "anh": ""}
	vao = [um.patch.object(goi_mon_ban.frappe, "get_all", lambda *a, **k: [{"name": "CB-1", "ma_hang": "KMCB1"}, {"name": "CB-2", "ma_hang": "KMCB2"}], create=True),
		um.patch.object(khuyen_mai, "_doc_combo", lambda ten: dict(cb, ten=ten)),
		um.patch.object(khuyen_mai, "_tiet_kiem_bo", lambda c, goc: 5000),
		um.patch.object(combo_mon, "ly_do_khong_ban", ly_do)]
	return vao, hoi


@ca("v670 luật bán combo theo nguồn: đơn bàn xét Tại chỗ và QR tại bàn; đơn giao xét đúng nguồn phiếu giao, combo không cho nguồn đó thì không bày")
def _():
	from contextlib import ExitStack

	from vagabond import goi_mon_ban

	cho = {"KMCB1": ("Tại chỗ", "QR tại bàn", "WEBORDER"), "KMCB2": ("Tại chỗ", "QR tại bàn")}
	vao, hoi = _combo_gia(goi_mon_ban, cho)
	with ExitStack() as bo:
		for v in vao:
			bo.enter_context(v)
		ban = goi_mon_ban.doc_combo_ban("TCV")
		dau = len(hoi)
		giao = goi_mon_ban.doc_combo_ban("TCV", ("WEBORDER",))
	la("đơn bàn: cả hai combo", [c["ma"] for c in ban], ["KMCB1", "KMCB2"])
	la("đơn bàn xét hai nguồn bàn", sorted({n for _m, n in hoi[:dau]}), ["QR tại bàn", "Tại chỗ"])
	la("đơn giao: chỉ combo mở kênh WEBORDER", [c["ma"] for c in giao], ["KMCB1"])
	la("đơn giao chỉ xét kênh WEBORDER", sorted({n for _m, n in hoi[dau:]}), ["WEBORDER"])
	la("giá bộ = gốc trừ phần giảm", giao[0]["gia"], 45000)


@ca("v670 một nguồn: bảng món kênh Giao gọi luật combo với kênh WEBORDER (nguon_combo); phiếu quầy cũng mang chữ WEBORDER; kênh Tại bàn giữ mặc định")
def _():
	from vagabond import bien_tap_menu, diem_ban, don_quay, goi_mon_ban, kiem_kho

	d = {"ma": "TCV", "nguon": ["Tại chỗ", "Mang về"]}
	la("kênh combo đơn giao", don_quay.nguon_combo(d), ("WEBORDER",))
	la("phiếu quầy và mã ưu đãi cùng một chữ", (don_quay.NGUON_BILL, don_quay.KENH_MA, don_quay.KENH), ("WEBORDER",) * 3)
	goi = []
	menu = {"nhom": [], "an": [], "giao": [], "tuy_chon": [], "topping": {}, "mon": {}}
	with um.patch.object(goi_mon_ban, "do_uong_cua_diem", return_value=[]), \
			um.patch.object(goi_mon_ban, "topping_cua_diem", return_value=[]), \
			um.patch.object(bien_tap_menu, "menu_hien_hanh", return_value=menu), \
			um.patch.object(goi_mon_ban, "_da_nhan_cua", return_value=[]), \
			um.patch.object(goi_mon_ban, "_cho_cua", return_value=[]), \
			um.patch.object(goi_mon_ban, "_phieu_tam_mo", return_value=set()), \
			um.patch.object(diem_ban, "gia_rieng", return_value={}), \
			um.patch.object(goi_mon_ban, "doc_combo_ban", side_effect=lambda ma, nguon=None: goi.append(nguon) or []), \
			um.patch.object(kiem_kho, "banh_tren_quay", return_value=[]), \
			um.patch.object(don_quay, "giu_cua_diem", return_value={}):
		goi_mon_ban.bang_mon(d)
		goi_mon_ban.bang_mon(d, kenh=bien_tap_menu.KENH_GIAO)
	la("Tại bàn mặc định, Giao theo kênh WEBORDER", goi, [None, ("WEBORDER",)])
	dung("hai nguồn bàn vẫn là mặc định", goi_mon_ban.NGUON_TAO and goi_mon_ban.NGUON_QR)


@ca("v670 tin mới tới nhóm đã chọn lọc Tin nhận: nhóm đang nhận mã mốc được tích thêm mã mới; nhóm nhận tất cả, nhóm chưa nhận mốc, chạy lại không đổi")
def _():
	import sys

	with um.patch.object(sys.modules["frappe.utils"], "get_url", lambda p="": "https://site" + p, create=True):
		from vagabond import kenh_zalo as kz

	f = kz.tin_them_theo_moc
	la("nhóm cửa hàng", f("hd_ket_ghi_so, bh_goi_mon_tai_ban, bh_dat_ban", "bh_weborder_moi", "bh_goi_mon_tai_ban"),
		"hd_ket_ghi_so, bh_goi_mon_tai_ban, bh_dat_ban, bh_weborder_moi")
	la("không đổi", (f("", "bh_weborder_moi", "bh_goi_mon_tai_ban"), f("hd_ket_ghi_so", "bh_weborder_moi", "bh_goi_mon_tai_ban"),
		f("bh_goi_mon_tai_ban; bh_weborder_moi", "bh_weborder_moi", "bh_goi_mon_tai_ban")), (None, None, None))
	for moi, moc in kz.TIN_MOC.items():
		dung("mã mới và mốc có trong TIN: %s, %s" % (moi, moc), moi in kz.TIN and moc in kz.TIN)
	la("tin đơn giao đi theo tin gọi món tại bàn", kz.TIN_MOC.get("bh_weborder_moi"), "bh_goi_mon_tai_ban")
	ghi = []
	rows = [{"name": "N1", "tin_nhan": "bh_goi_mon_tai_ban, bh_dat_ban"}, {"name": "N2", "tin_nhan": "hd_ket_ghi_so"},
		{"name": "N3", "tin_nhan": ""}, {"name": "N4", "tin_nhan": "mkt_bai_cho_duyet, bh_goi_mon_tai_ban"}]
	with um.patch.object(kz.frappe.db, "has_column", lambda *a: True, create=True), \
			um.patch.object(kz.frappe, "get_all", lambda *a, **k: [dict(r) for r in rows], create=True), \
			um.patch.object(kz.frappe.db, "set_value", lambda dt, ten, f, v, **k: ghi.append((ten, v)), create=True), \
			um.patch.object(kz.frappe, "clear_cache", lambda **k: None, create=True):
		so = kz.tich_theo_moc(("mkt_bai_gd_duyet", "bh_weborder_moi"))
	la("chỉ nhóm nhận mốc đổi, một lần ghi mỗi nhóm", ghi, [("N1", "bh_goi_mon_tai_ban, bh_dat_ban, bh_weborder_moi"),
		("N4", "mkt_bai_cho_duyet, bh_goi_mon_tai_ban, mkt_bai_gd_duyet, bh_weborder_moi")])
	la("số nhóm đổi", so, 2)
	from vagabond.patches import v670_so_chu_de_bai as p

	dung("bản vá v670 tích tin đơn giao", "bh_weborder_moi" in p.TIN_MOI)


@ca("v670 mã đơn WO-YYMMDD-5 số và O2O-YYMMDD-5 số: bộ đếm theo tháng (khoá TIỀN TỐ-YYMM-), ngày trong mã để đọc; đúng ví dụ anh Việt duyệt")
def _():
	import datetime as dt

	from vagabond import ma_don

	luc = dt.datetime(2026, 11, 17, 21, 5)
	la("ví dụ WO", ma_don.ten_ma(ma_don.TIEN_TO_WO, luc, 23), "WO-261117-00023")
	la("ví dụ O2O", ma_don.ten_ma(ma_don.TIEN_TO_O2O, luc, 5), "O2O-261117-00005")
	la("bộ đếm theo tháng, không theo ngày", (ma_don.khoa_dem("WO", luc), ma_don.khoa_dem("WO", dt.datetime(2026, 11, 30))),
		("WO-2611-", "WO-2611-"))
	la("sang tháng mới khoá mới", ma_don.khoa_dem("WO", dt.datetime(2026, 12, 1)), "WO-2612-")
	la("cuối năm", ma_don.khoa_dem("O2O", dt.datetime(2026, 12, 31, 23, 59)), "O2O-2612-")
	dem = []
	import sys
	import types

	with um.patch.dict(sys.modules, {"frappe.model.naming": types.SimpleNamespace(getseries=lambda khoa, so: dem.append((khoa, so)) or "00007")}):
		la("đặt tên lấy số của tháng", ma_don.dat_ten("WO", luc), "WO-261117-00007")
	la("hỏi đúng khoá và 5 chữ số", dem, [("WO-2611-", 5)])


@ca("v670 bản ghi đặt tên: đơn kênh WEBORDER mang mã WO, đơn đặt bánh web giữ DW (để trống cho doctype), đơn gọi món tại bàn mang mã O2O")
def _():
	import sys
	import types

	from vagabond import ma_don

	goi = []
	with um.patch.object(ma_don, "dat_ten", lambda tt, luc=None: goi.append(tt) or tt + "-261117-00001"):
		lop = {}
		for mod, ten in (("vagabond.vagabond.doctype.vagabond_don_web.vagabond_don_web", "VagabondDonWeb"),
				("vagabond.vagabond.doctype.vagabond_goi_mon_ban.vagabond_goi_mon_ban", "VagabondGoiMonBan")):
			gia = {"vagabond.don_web": types.SimpleNamespace(kiem_ban_ghi=None, sau_khi_luu=None)} if "don_web" in mod else {}
			with um.patch.dict(sys.modules, gia):
				m = __import__(mod, fromlist=[ten])
			lop[ten] = getattr(m, ten)

		class _D(dict):
			name = None

			def get(self, k, d=None):
				return dict.get(self, k, d)
		wo, dw, o2o = _D(vgb_kenh="WEBORDER"), _D(vgb_kenh=""), _D()
		lop["VagabondDonWeb"].autoname(wo)
		lop["VagabondDonWeb"].autoname(dw)
		lop["VagabondGoiMonBan"].autoname(o2o)
	la("tên", (wo.name, dw.name, o2o.name), ("WO-261117-00001", None, "O2O-261117-00001"))
	la("tiền tố đã hỏi", goi, ["WO", "O2O"])


@ca("v670 đơn WO đi đúng đường thanh toán đơn web như DW: mã chuyển khoản bỏ gạch, đọc ngược, nhận ra trong nội dung, mã giao dịch OnePay; không ăn nhầm mã dài hơn")
def _():
	from vagabond import onepay as op
	from vagabond import thanh_toan_web_thuan as ttt

	la("bỏ gạch", ttt.ma_dw("WO-261117-00023"), "WO26111700023")
	la("đọc ngược WO và DW", (ttt.ten_dw("WO26111700023"), ttt.ten_dw("DW261100123")), ("WO-261117-00023", "DW-2611-00123"))
	la("là mã đơn web", (ttt.la_ma_dw("WO26111700023"), ttt.la_ma_dw("WO2611170002"), ttt.la_ma_dw("WO261117000234")), (True, False, False))
	dung("tên WO hợp lệ", bool(ttt.RE_TEN_DW.match("WO-261117-00023")) and not ttt.RE_TEN_DW.match("WO-2611-00023"))
	la("nội dung khớp đúng đơn", ttt.mo_ta_khop("CK WO26111700023 Lan", "", "WO-261117-00023", ""), True)
	la("không ăn nhầm mã dài hơn", ttt.mo_ta_khop("CK WO261117000231", "", "WO-261117-00023", ""), False)
	la("mã đơn khác trong nội dung", ttt.ma_don_khac("WO26111700023 WO26111700024", "", "WO-261117-00023", ""), ["WO26111700024"])
	la("mã giao dịch OnePay", op.ma_phieu_cua_gd(op.ma_gd("WO26111700023", 2)), "WO26111700023")


@ca("v670 đổi chữ Web giao thành WEBORDER trong ô Kênh của chương trình, combo: giữ thứ tự, bỏ trùng, ô không có Web giao không đổi")
def _():
	from vagabond.patches import v670_kenh_weborder as p

	la("đổi", p.kenh_moi("WEBORDER\nWeb giao"), "WEBORDER")
	la("giữ kênh khác", p.kenh_moi("Tại chỗ\nWeb giao\nMang về"), "Tại chỗ\nWEBORDER\nMang về")
	la("không đổi", (p.kenh_moi(""), p.kenh_moi("WEBORDER"), p.kenh_moi("Mang về")), (None, None, None))


@ca("v670 phiếu đơn giao rã combo xét kênh WEBORDER (cờ máy chủ), phiếu thường xét nguồn của phiếu")
def _():
	import types

	from vagabond import combo_mon

	goi = []

	class _Dong:
		def __init__(self, **kw):
			self.__dict__.update(kw)

		def get(self, k, d=None):
			return self.__dict__.get(k, d)

	class _Phieu(_Dong):
		def is_new(self):
			return True

		def set(self, k, v):
			setattr(self, k, v)

		def append(self, k, v):
			d = _Dong(**v)
			self.items.append(d)
			return d

	def phieu():
		return _Phieu(docstatus=0, custom_nguon="Mang về", vgb_quay="TCV", items=[_Dong(item_code="KMCB0001", qty=1, name=None)], doctype="Sales Invoice")
	with um.patch.object(combo_mon, "ra_dong", lambda ma, sl, quay="", nguon="": goi.append(nguon) or []), \
			um.patch.object(combo_mon, "_kiem_tien_da_chia", lambda doc: None), \
			um.patch.object(combo_mon.frappe, "flags", types.SimpleNamespace(), create=True):
		combo_mon.truoc_khi_luu(phieu())
		combo_mon.frappe.flags.vgb_nguon_luat = "WEBORDER"
		combo_mon.truoc_khi_luu(phieu())
	la("phiếu thường rồi phiếu đơn giao", goi, ["Mang về", "WEBORDER"])
