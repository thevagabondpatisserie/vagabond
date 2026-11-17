# -*- coding: utf-8 -*-
"""v670 đơn giao của quầy (Minh Vũ 17/11/2026, anh Việt đồng ý gom vào PR #585).

Ca chốt:
  - Combo cho đơn giao (WEBORDER): luật bán xét ĐÚNG nguồn phiếu tạm tính quầy
    lập cho đơn giao (don_quay.nguon_combo = _nguon_bill), một nguồn cho bảng món
    lúc đặt (goi_mon_ban.bang_mon kênh Giao) và trang khách (kiem_kho); đơn bàn giữ
    hai nguồn Tại chỗ, QR tại bàn như cũ.
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

	cho = {"KMCB1": ("Tại chỗ", "QR tại bàn", "Mang về"), "KMCB2": ("Tại chỗ", "QR tại bàn")}
	vao, hoi = _combo_gia(goi_mon_ban, cho)
	with ExitStack() as bo:
		for v in vao:
			bo.enter_context(v)
		ban = goi_mon_ban.doc_combo_ban("TCV")
		dau = len(hoi)
		giao = goi_mon_ban.doc_combo_ban("TCV", ("Mang về",))
	la("đơn bàn: cả hai combo", [c["ma"] for c in ban], ["KMCB1", "KMCB2"])
	la("đơn bàn xét hai nguồn bàn", sorted({n for _m, n in hoi[:dau]}), ["QR tại bàn", "Tại chỗ"])
	la("đơn giao: chỉ combo cho nguồn Mang về", [c["ma"] for c in giao], ["KMCB1"])
	la("đơn giao chỉ xét nguồn phiếu giao", sorted({n for _m, n in hoi[dau:]}), ["Mang về"])
	la("giá bộ = gốc trừ phần giảm", giao[0]["gia"], 45000)


@ca("v670 một nguồn: bảng món kênh Giao gọi luật combo với đúng nguồn phiếu quầy lập cho đơn giao (nguon_combo = _nguon_bill); kênh Tại bàn giữ mặc định")
def _():
	from vagabond import bien_tap_menu, diem_ban, don_quay, goi_mon_ban, kiem_kho

	d = {"ma": "TCV", "nguon": ["Tại chỗ", "Mang về"]}
	la("nguồn combo đơn giao", don_quay.nguon_combo(d), (don_quay._nguon_bill(d),))
	la("điểm có Mang về thì là Mang về", don_quay.nguon_combo(d), ("Mang về",))
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
	la("Tại bàn mặc định, Giao theo nguồn phiếu giao", goi, [None, ("Mang về",)])
	dung("hai nguồn bàn vẫn là mặc định", goi_mon_ban.NGUON_TAO and goi_mon_ban.NGUON_QR)


@ca("v670 tin mới tới nhóm đã chọn lọc Tin nhận: nhóm đang nhận mã mốc được tích thêm mã mới; nhóm nhận tất cả, nhóm chưa nhận mốc, chạy lại không đổi")
def _():
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
