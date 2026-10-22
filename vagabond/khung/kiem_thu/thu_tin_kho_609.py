# -*- coding: utf-8 -*-
"""v609: tin Zalo cho kho, thu mua, sản xuất và đơn web mới (anh Việt duyệt mẫu 22/10/2026).

Ba lớp ca:
  1. Phép THUẦN soạn chữ: tên hàng có đủ, cắt ở 5 món, không tiền ở tin kho.
  2. Hàm hook và hàm lịch chạy THẬT trên lớp Frappe giả, kênh Zalo giả ghi lại
     lời gọi: đúng mã tin, đúng loại, đúng khoá chống trùng, không bao giờ ném
     lỗi ra chứng từ (trừ lỗi chết giao dịch).
  3. AST: hooks.py đã nối đủ, các chỗ gọi tay (nhận điều chuyển, kiểm kê ghi sổ,
     đơn web) có thật, màn Nhận hàng giương cờ trước khi insert.
"""

import ast
import datetime
import os
import re
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import HOM_NAY, ca, dung, gia_lap, la, nem

gia_lap()
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")

from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import tin_kho as tk  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.dirname(GOI)


class D(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def _doc(**k):
	d = D(k)
	d.flags = D()
	return d


def _zalo(chet=False, nem_loi=None):
	goi = []

	def ghi(loai, chu_de, tieu_de, dong=None, **kw):
		if nem_loi:
			raise nem_loi
		goi.append(D(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=list(dong or [])))
		return ["ZL-1"]
	gia = types.SimpleNamespace(bao=ghi, bao_hoac_ghi_loi=ghi, cat_dong=kz.cat_dong, chet_giao_dich=lambda e: chet)
	return gia, goi


def _chay(ham, chet=False, nem_loi=None, cho_loi=False, **patch):
	"""Chạy hàm thật với kênh Zalo giả. Hook nuốt lỗi và ghi Error Log, nên mặc định
	một Error Log cũng là hỏng: ca "im" phải im vì đúng luật, không phải vì gãy."""
	gia, goi = _zalo(chet, nem_loi)
	fr = sys.modules["frappe"]
	loi = []
	patch.setdefault("log_error", lambda *a, **k: loi.append(a))
	ps = [um.patch.object(tk, "kenh_zalo", gia)] + [um.patch.object(fr, k, v, create=True) for k, v in patch.items()]
	for p in ps:
		p.start()
	try:
		ham()
	finally:
		for p in reversed(ps):
			p.stop()
	if not cho_loi:
		la("không có Error Log", loi, [])
	return goi


def _loi_ghi(ham, **k):
	"""Như _chay nhưng trả thêm danh sách Error Log đã ghi."""
	loi = []
	goi = _chay(ham, cho_loi=True, log_error=lambda *a, **kw: loi.append(a), **k)
	return goi, loi


TIEN = re.compile(r"\d đ(?![\wÀ-ỹ])")


def _khong_tien(goi):
	for g in goi:
		if g["ma_tin"].startswith(("kho_", "bep_")):
			dung("%s không có tiền" % g["ma_tin"], not any(TIEN.search(d) for d in g["dong"]))


ITEMS = [D(item_code="BOT-01", item_name="Bột mì số 13", qty=25, uom="Kg", purchase_order_item="POI-1", batch_no="LO-1"),
	D(item_code="BO-02", item_name="Bơ lạt Anchor", qty=4, uom="Thùng", purchase_order_item="POI-2", batch_no="")]
NHIEU = [D(item_code="M%d" % i, item_name="Món %d" % i, qty=i + 1, uom="Cái") for i in range(7)]


@ca("v609 thuần: tên kho bỏ đuôi, số và tiền kiểu Việt, dòng hàng cắt ở 5 món rồi +N món khác")
def _thuan():
	la("tên kho", [tk.ten_kho("Kho D1 - TV"), tk.ten_kho("Baker - Nguyên liệu - TVD"), tk.ten_kho("")], ["Kho D1", "Baker - Nguyên liệu", ""])
	la("số", [tk.so(12), tk.so(1250), tk.so(0.5), tk.so(2.25)], ["12", "1.250", "0,5", "2,25"])
	la("tiền", [tk.tien(1234567), tk.tien(0)], ["1.234.567 đ", "0 đ"])
	d = tk.dong_hang(tk.hang_tu_items(NHIEU))
	la("năm dòng rồi +2", (len(d), d[0], d[-1]), (6, "Món 0: 1 Cái", "+2 món khác"))
	la("đuôi dòng", tk.dong_hang([{"ten": "Bơ", "sl": 2, "dvt": "Kg", "ghi": "hạn 20/10"}]), ["Bơ: 2 Kg (hạn 20/10)"])
	la("bỏ dòng không tên", tk.dong_hang([{"ten": " ", "sl": 1, "dvt": "x"}]), [])
	la("lệch đơn", [tk.cau_lech_don({}, 2), tk.cau_lech_don({}, -1), tk.cau_lech_don({}, 0), tk.cau_lech_don({}, None)],
		["còn thiếu 2 theo đơn", "dư 1 so với đơn", "đủ theo đơn", ""])
	la("ngày, giờ", (tk.ngay_vn("2026-10-23"), tk.gio_vn(datetime.datetime(2026, 10, 22, 7, 5)), tk.ngay_vn(None)), ("23/10", "07:05 22/10", ""))


@ca("v609 thuần: phân loại phiếu kho đúng từng ô, phục vụ bán và huỷ mềm thì im")
def _phan_loai():
	la("ma trận", [
		tk.phan_loai_phieu_kho("Material Transfer", "", 0), tk.phan_loai_phieu_kho("Material Issue", "", 0, "Hỏng"),
		tk.phan_loai_phieu_kho("Material Issue", "phuc_vu_ban", 0), tk.phan_loai_phieu_kho("Material Issue", "marketing", 0),
		tk.phan_loai_phieu_kho("Manufacture", "", 0), tk.phan_loai_phieu_kho("Material Receipt", "", 0),
		tk.phan_loai_phieu_kho("Material Transfer", "", 1),
	], ["chuyen", "huy", "", "noi_bo", "san_xuat", "", ""])
	# Codex #495 vòng 4: Material Issue trống mục đích mà KHÔNG có lý do huỷ (trừ kho bù, tiệc, dọn dữ liệu) thì không phải xuất huỷ.
	la("không lý do huỷ thì im", [tk.phan_loai_phieu_kho("Material Issue", "", 0), tk.phan_loai_phieu_kho("Material Issue", "", 0, "  "), tk.phan_loai_phieu_kho("Material Issue", None, 0, None)], ["", "", ""])
	la("tên mục đích", (tk.ten_muc_dich("marketing"), tk.ten_muc_dich("la_ma")), ("Marketing chụp ảnh, quay phim", "la_ma"))


@ca("v609 phiếu nhập: nháp thì nhắc kho đếm, màn Nhận hàng giương cờ thì im; ghi sổ thì báo đã nhập kèm lệch đơn và hạn lô")
def _phieu_nhap():
	pr = _doc(name="PNK-1", docstatus=0, supplier_name="Cty ABC", set_warehouse="Kho D1 - TV", items=ITEMS)
	goi = _chay(lambda: tk.khi_lap_phieu_nhap(pr))
	la("một tin chờ kiểm", [(g.ma_tin, g.loai, g.khoa) for g in goi], [("kho_nhap_cho_kiem", "viec", "pnk-cho:PNK-1")])
	dung("có tên hàng và kho gọn", "Bột mì số 13: 25 Kg" in goi[0].dong and "Kho D1" in goi[0].dong[0] and "- TV" not in goi[0].dong[0])
	_khong_tien(goi)
	pr.flags.vgb_nhap_ngay = True
	la("giương cờ thì im", _chay(lambda: tk.khi_lap_phieu_nhap(pr)), [])
	pr.flags = D()
	# Codex #495 vòng 4: phiếu trả hàng nhà cung cấp (is_return) không báo nhập ở cả hai móc.
	la("trả hàng NCC: nháp im", _chay(lambda: tk.khi_lap_phieu_nhap(D(pr, is_return=1))), [])
	la("trả hàng NCC: ghi sổ im", _chay(lambda: tk.khi_ghi_so_phieu_nhap(D(pr, is_return=1, docstatus=1))), [])
	pr.docstatus = 1
	la("đã ghi sổ thì after_insert im", _chay(lambda: tk.khi_lap_phieu_nhap(pr)), [])

	def gv(dt, name, fields=None, as_dict=False, **k):
		if dt == "Purchase Order Item":
			return {"POI-1": D(qty=30, received_qty=25), "POI-2": D(qty=4, received_qty=4)}.get(name)
		if dt == "Batch":
			return "2026-10-30" if name == "LO-1" else None
	db = types.SimpleNamespace(get_value=gv)
	goi = _chay(lambda: tk.khi_ghi_so_phieu_nhap(pr), db=db)
	la("một tin đã nhập", [(g.ma_tin, g.loai, g.khoa) for g in goi], [("kho_da_nhap", "thong_bao", "pnk-xong:PNK-1")])
	la("dòng hàng kèm lệch và hạn", goi[0].dong[1:], ["Bột mì số 13: 25 Kg (còn thiếu 5 theo đơn, hạn 30/10)", "Bơ lạt Anchor: 4 Thùng (đủ theo đơn)"])
	_khong_tien(goi)


@ca("v609 phiếu kho ghi sổ: chuyển, huỷ (kho và kế toán), nội bộ, sản xuất; phục vụ bán và huỷ mềm thì im")
def _phieu_kho():
	nen = dict(name="PXK-1", docstatus=1, from_warehouse="Kho D1 - TV", to_warehouse="Kho TC - TV", vgb_huy=0,
		total_outgoing_value=850000, vgb_ly_do_huy="Hỏng do mất điện", items=ITEMS)
	se = _doc(purpose="Material Transfer", vgb_muc_dich_xuat="", **nen)
	goi = _chay(lambda: tk.khi_ghi_so_phieu_kho(se))
	la("chuyển", [(g.ma_tin, g.khoa) for g in goi], [("kho_da_chuyen", "dc-xong:PXK-1")])
	dung("kho đi sang kho đến", "Kho D1 sang Kho TC" in goi[0].dong[0])
	_khong_tien(goi)
	se = _doc(purpose="Material Issue", vgb_muc_dich_xuat="", **nen)
	goi = _chay(lambda: tk.khi_ghi_so_phieu_kho(se))
	la("huỷ: kho rồi kế toán", [g.ma_tin for g in goi], ["kho_da_huy", "kt_xuat_huy_gia_von"])
	dung("kho thấy lý do, không thấy tiền", "Hỏng do mất điện" in goi[0].dong[0] and not TIEN.search(" ".join(goi[0].dong)))
	dung("kế toán thấy giá vốn", "850.000 đ" in goi[1].dong[0])
	la("huỷ: khoá khác nhau", [g.khoa for g in goi], ["xh-xong:PXK-1", "xh-gv:PXK-1"])
	se = _doc(purpose="Material Issue", vgb_muc_dich_xuat="phuc_vu_ban", **nen)
	la("phục vụ bán im", _chay(lambda: tk.khi_ghi_so_phieu_kho(se)), [])
	se = _doc(purpose="Material Issue", vgb_muc_dich_xuat="rnd", **nen)
	goi = _chay(lambda: tk.khi_ghi_so_phieu_kho(se))
	la("nội bộ", [g.ma_tin for g in goi], ["kho_xuat_noi_bo"])
	dung("mục đích có dấu, không lộ mã", "rnd" not in goi[0].dong[0] and "mục đích: " in goi[0].dong[0])
	sx = [D(item_code="BOT-01", item_name="Bột mì số 13", qty=5, uom="Kg", is_finished_item=0),
		D(item_code="BANH-1", item_name="Bánh mì vỏ giòn", qty=40, uom="Cái", is_finished_item=1)]
	se = _doc(purpose="Manufacture", vgb_muc_dich_xuat="", work_order="LSX-9", **dict(nen, items=sx))
	goi = _chay(lambda: tk.khi_ghi_so_phieu_kho(se))
	la("sản xuất", [(g.ma_tin, g.chu_de) for g in goi], [("bep_lenh_sx_xuat_nvl", "san_xuat")])
	la("thành phẩm riêng, nguyên liệu riêng", goi[0].dong, ["Phiếu PXK-1, lệnh LSX-9", "Thành phẩm: Bánh mì vỏ giòn 40 Cái", "Bột mì số 13: 5 Kg"])
	se = _doc(purpose="Material Issue", vgb_muc_dich_xuat="", **dict(nen, vgb_huy=1))
	la("huỷ mềm im", _chay(lambda: tk.khi_ghi_so_phieu_kho(se)), [])
	# Codex #495 vòng 4: phiếu trừ kho bù của hoá đơn (Material Issue, không lý do huỷ) không phải xuất huỷ.
	se = _doc(purpose="Material Issue", vgb_muc_dich_xuat="", vgb_hd_tru_bu="HD-1", **dict(nen, vgb_ly_do_huy=""))
	la("trừ kho bù: ghi sổ im", _chay(lambda: tk.khi_ghi_so_phieu_kho(se)), [])
	la("trừ kho bù: nháp im", _chay(lambda: tk.khi_lap_phieu_kho(D(se, docstatus=0))), [])
	# Nháp: chỉ xuất huỷ mới nhắc ghi sổ.
	se = _doc(purpose="Material Issue", vgb_muc_dich_xuat="", **dict(nen, docstatus=0))
	la("nháp huỷ nhắc ghi sổ", [(g.ma_tin, g.loai) for g in _chay(lambda: tk.khi_lap_phieu_kho(se))], [("kho_huy_cho_ghi_so", "viec")])
	se = _doc(purpose="Material Transfer", vgb_muc_dich_xuat="", **dict(nen, docstatus=0))
	la("nháp chuyển im", _chay(lambda: tk.khi_lap_phieu_kho(se)), [])


@ca("v609 nhận điều chuyển: đủ là thông báo kê số nhận, thiếu là cảnh báo kê dòng lệch")
def _nhan_chuyen():
	from vagabond.nhan_dieu_chuyen import DU, THIEU
	se = _doc(name="PXK-2", from_warehouse="Kho D1 - TV", to_warehouse="Kho TC - TV")
	cd = [{"ma": "BOT-01", "ten": "Bột mì số 13", "giao": 10, "nhan": 10}, {"ma": "BO-02", "ten": "Bơ lạt", "giao": 4, "nhan": 3}]
	goi = _chay(lambda: tk.bao_da_nhan_chuyen(se, THIEU, cd))
	la("thiếu là cảnh báo", [(g.ma_tin, g.loai, g.khoa) for g in goi], [("kho_da_nhan_chuyen", "canh_bao", "dc-nhan:PXK-2")])
	la("chỉ dòng lệch", goi[0].dong[1:], ["Bơ lạt: 3 (giao 4, nhận 3)"])
	goi = _chay(lambda: tk.bao_da_nhan_chuyen(se, DU, cd))
	la("đủ là thông báo", [(g.ma_tin, g.loai) for g in goi], [("kho_da_nhan_chuyen", "thong_bao")])
	la("kê số nhận", goi[0].dong[1:], ["Bột mì số 13: 10", "Bơ lạt: 3"])
	_khong_tien(goi)


@ca("v609 kiểm kê: Chờ duyệt mới nhắc (một lần mỗi phiếu); ghi sổ báo kho dòng lệch và kế toán giá trị chênh lệch")
def _kiem_ke():
	items = [D(item_name="Bột mì số 13", dvt="Kg", so_luong=24, lech=-1), D(item_name="Bơ lạt", dvt="Thùng", so_luong=4, lech=0)]
	pk = _doc(name="KK-1", trang_thai="Đang kiểm", kho="Kho D1 - TV", nguoi_kiem="Dễ", ngay_kiem="2026-10-22", items=items)
	la("đang kiểm im", _chay(lambda: tk.khi_doi_phieu_kiem_ke(pk)), [])
	pk.trang_thai = "Chờ duyệt"
	goi = _chay(lambda: tk.khi_doi_phieu_kiem_ke(pk))
	la("chờ duyệt", [(g.ma_tin, g.loai, g.khoa) for g in goi], [("kho_kiem_ke_cho_duyet", "viec", "kk-cho-duyet:KK-1")])
	la("chỉ dòng lệch", goi[0].dong[1:], ["Bột mì số 13: 24 Kg (lệch -1)"])
	dung("đầu tin nêu 1 dòng lệch", "1 dòng lệch" in goi[0].dong[0])
	db = types.SimpleNamespace(get_value=lambda dt, n, f=None, **k: -45000 if dt == "Stock Reconciliation" else None)
	goi = _chay(lambda: (tk.bao_kiem_ke_da_ghi_so(pk, "SR-1"), tk.bao_ke_toan_kiem_ke_lech(pk, "SR-1")), db=db)
	la("hai tin", [(g.ma_tin, g.khoa) for g in goi], [("kho_kiem_ke_da_ghi_so", "kk-ghi-so:KK-1"), ("kt_kiem_ke_lech", "kk-gt:KK-1")])
	dung("kế toán thấy giá trị", "-45.000 đ" in goi[1].dong[0])
	_khong_tien(goi)
	goi = _chay(lambda: (tk.bao_kiem_ke_da_ghi_so(pk, None), tk.bao_ke_toan_kiem_ke_lech(pk, None)), db=db)
	la("tồn khớp: kho một tin, kế toán im", [g.ma_tin for g in goi], ["kho_kiem_ke_da_ghi_so"])
	dung("nói tồn khớp", "tồn khớp" in goi[0].dong[0])


@ca("v609 thu mua: yêu cầu mua một tin mỗi phiếu (after_insert và on_submit cùng khoá), đơn mua có tiền và hẹn về; giao sỉ kê hàng")
def _thu_mua():
	mr = _doc(name="YCMH-1", docstatus=0, material_request_type="Purchase", bo_phan_yeu_cau="Bếp", schedule_date="2026-10-25", items=ITEMS)
	goi = _chay(lambda: (tk.khi_co_yeu_cau_mua(mr), tk.khi_co_yeu_cau_mua(D(mr, docstatus=1))))
	la("hai lần gọi, cùng khoá", [(g.ma_tin, g.khoa) for g in goi], [("tm_yeu_cau_mua", "ycm:YCMH-1")] * 2)
	dung("đầu tin có bộ phận và ngày cần", "bộ phận Bếp" in goi[0].dong[0] and "cần ngày 25/10" in goi[0].dong[0])
	la("chuyển kho nội bộ không báo thu mua", _chay(lambda: tk.khi_co_yeu_cau_mua(D(mr, material_request_type="Material Transfer"))), [])
	po = _doc(name="DMH-1", supplier_name="Cty ABC", schedule_date="2026-10-28", grand_total=12500000, vgb_huy=0, items=ITEMS)
	goi = _chay(lambda: tk.khi_ghi_so_don_mua(po))
	la("đơn mua", [(g.ma_tin, g.loai, g.khoa) for g in goi], [("tm_don_mua_moi", "thong_bao", "dmh:DMH-1")])
	la("hẹn về và tổng", (goi[0].dong[1], goi[0].dong[-1]), ("Hẹn về 28/10", "Tổng 12.500.000 đ"))
	la("huỷ mềm im", _chay(lambda: tk.khi_ghi_so_don_mua(D(po, vgb_huy=1))), [])
	dn = _doc(name="GH-1", customer_name="Khách sỉ A", set_warehouse="Kho TC - TV", vgb_nguoi_nhan="Anh Ba", items=ITEMS)
	goi = _chay(lambda: tk.khi_ghi_so_giao_si(dn))
	la("giao sỉ", [(g.ma_tin, g.khoa) for g in goi], [("kho_giao_si", "dn-xong:GH-1")])
	dung("khách, kho, người nhận", "Khách sỉ A" in goi[0].dong[0] and "Kho TC" in goi[0].dong[0] and "Anh Ba" in goi[0].dong[0])
	_khong_tien(goi)


@ca("v609 lịch: trễ hẹn và chưa hoá đơn gom một tin mỗi ngày; chuyển chưa nhận một tin mỗi phiếu; lô hết hạn và tồn thấp một tin mỗi kho")
def _lich():
	hom = str(HOM_NAY)

	def ga(dt, **k):
		return {
			"Purchase Order": [D(name="DMH-2", supplier_name="Cty B", schedule_date="2026-08-10", grand_total=3000000, per_received=40)],
			"Purchase Receipt": [D(name="PNK-7", supplier_name="Cty C", posting_date="2026-08-01", grand_total=900000)],
			"Stock Entry": [D(name="PXK-5", from_warehouse="Kho D1 - TV", to_warehouse="Kho TC - TV", modified=datetime.datetime(2026, 8, 15, 5, 0)),
				D(name="PXK-6", from_warehouse="Kho D1 - TV", to_warehouse="Kho D2 - TV", modified=datetime.datetime(2026, 8, 14, 20, 0))],
			"Batch": [D(name="LO-1", item="BOT-01", item_name="Bột mì số 13", stock_uom="Kg", expiry_date="2026-08-16"),
				D(name="LO-2", item="TRUNG", item_name="Trứng gà", stock_uom="Quả", expiry_date="2026-08-14"),
				D(name="LO-3", item="BO-02", item_name="Bơ lạt", stock_uom="Kg", expiry_date="2026-09-30")],
			"Item Reorder": [D(parent="BOT-01", warehouse="Kho D1 - TV", warehouse_reorder_level=50),
				D(parent="BO-02", warehouse="Kho D1 - TV", warehouse_reorder_level=5), D(parent="BO-02", warehouse="Kho TC - TV", warehouse_reorder_level=2)],
			"Item": [D(name="BOT-01", item_name="Bột mì số 13", stock_uom="Kg"), D(name="BO-02", item_name="Bơ lạt", stock_uom="Kg")],
			"Bin": [D(item_code="BOT-01", warehouse="Kho D1 - TV", actual_qty=20), D(item_code="BO-02", warehouse="Kho D1 - TV", actual_qty=6),
				D(item_code="BO-02", warehouse="Kho TC - TV", actual_qty=0)],
		}.get(dt, [])
	goi = _chay(tk.nhac_don_mua_tre_hen, get_all=ga)
	la("trễ hẹn", [(g.ma_tin, g.khoa, g.nguon) for g in goi], [("tm_don_mua_tre_hen", "dmh-tre:%s" % hom, "Purchase Order")])
	dung("dòng có tiền và phần trăm", "40%" in goi[0].dong[0] and "3.000.000 đ" in goi[0].dong[0])
	bl_hd = []
	goi = _chay(tk.nhac_hang_ve_chua_hoa_don, get_all=lambda dt, **k: (bl_hd.append(k.get("filters")), ga(dt))[1])
	la("chưa hoá đơn", [(g.ma_tin, g.khoa) for g in goi], [("tm_hang_ve_chua_hoa_don", "pnk-chua-hd:%s" % hom)])
	la("loại phiếu trả hàng NCC (Codex #495 vòng 4)", bl_hd[0].get("is_return"), 0)
	bo_loc, bo_loc_k = [], []
	goi = _chay(tk.nhac_chuyen_chua_nhan, get_all=lambda dt, **k: (bo_loc.append(k.get("filters")), bo_loc_k.append(k), ga(dt))[2])
	la("chuyển chưa nhận: mỗi phiếu một khoá", [(g.ma_tin, g.loai, g.khoa) for g in goi],
		[("kho_chuyen_chua_nhan", "viec", "chua-nhan:PXK-5"), ("kho_chuyen_chua_nhan", "viec", "chua-nhan:PXK-6")])
	dung("chỉ kho nhận phải làm", "Kho TC mở Hàng chuyển về kho tôi" in goi[0].dong[1])
	dung("giờ ghi sổ lấy từ mốc ghi sổ", "ghi sổ lúc 05:00 15/08" in goi[0].dong[0])
	# Codex #495 P2: mốc là lúc ghi sổ (modified), không phải lúc tạo nháp (creation).
	bay_gio = datetime.datetime(2026, 8, 15, 9, 0)
	tu, den = tk.cua_so_chua_nhan(bay_gio)
	la("cửa sổ 2 tới 48 giờ", (tu, den), (datetime.datetime(2026, 8, 13, 9, 0), datetime.datetime(2026, 8, 15, 7, 0)))
	dung("lọc theo modified, không creation", bo_loc[0]["modified"] == ["between", (tu, den)] and "creation" not in bo_loc[0])
	# Nháp lập 60 giờ trước, ghi sổ 3 giờ trước: theo creation thì rơi ngoài cửa sổ (không bao giờ nhắc), theo mốc ghi sổ thì nhắc.
	tao = datetime.datetime(2026, 8, 12, 21, 0); ghi_so = datetime.datetime(2026, 8, 15, 6, 0)
	la("theo creation: KHÔNG nhắc", tu <= tao <= den, False)
	la("theo mốc ghi sổ: nhắc", tu <= ghi_so <= den, True)
	dung("lịch chuyển chưa nhận đọc hết, không giới hạn số dòng (Codex #495 vòng 2)", "limit" not in bo_loc_k[0] and bo_loc_k[0].get("limit_page_length") == 0)
	# Codex #495 P1: _ton_lo_theo_kho chạy THẬT qua get_batch_qty giả; lô hết hạn hôm qua
	# chỉ có dòng khi for_stock_levels=True (đúng hành vi ERPNext v16).
	ton = {"LO-1": [{"warehouse": "Kho D1 - TV", "qty": 12}, {"warehouse": "Kho TC - TV", "qty": 3}],
		"LO-2": [{"warehouse": "Kho D1 - TV", "qty": 30}], "LO-3": [{"warehouse": "Kho D1 - TV", "qty": 9}, {"warehouse": "Kho D2 - TV", "qty": 0}]}
	han = {"LO-1": "2026-08-16", "LO-2": "2026-08-14", "LO-3": "2026-09-30"}
	goi_gbq = []

	def get_batch_qty(batch_no=None, warehouse=None, item_code=None, for_stock_levels=False, **k):
		goi_gbq.append((batch_no, for_stock_levels))
		if han[batch_no] < str(HOM_NAY) and not for_stock_levels:
			return []
		return list(ton.get(batch_no, []))
	bm = types.ModuleType("erpnext.stock.doctype.batch.batch"); bm.get_batch_qty = get_batch_qty
	with um.patch.dict(sys.modules, {"erpnext": types.ModuleType("erpnext"), "erpnext.stock": types.ModuleType("erpnext.stock"),
			"erpnext.stock.doctype": types.ModuleType("erpnext.stock.doctype"), "erpnext.stock.doctype.batch": types.ModuleType("erpnext.stock.doctype.batch"),
			"erpnext.stock.doctype.batch.batch": bm}):
		goi = _chay(tk.nhac_lo_sap_het_han, get_all=ga)
	la("gọi get_batch_qty với cờ kể cả lô quá hạn", sorted(goi_gbq), [("LO-1", True), ("LO-2", True), ("LO-3", True)])
	la("lô hết hạn: một tin mỗi kho", [(g.ma_tin, g.khoa) for g in goi],
		[("kho_lo_sap_het_han", "lo-het-han:Kho D1 - TV:%s" % hom), ("kho_lo_sap_het_han", "lo-het-han:Kho TC - TV:%s" % hom)])
	la("kho D1: quá hạn trước, bỏ lô còn xa", goi[0].dong[1:3], ["Trứng gà: 30 Quả (đã quá hạn 14/08)", "Bột mì số 13: 12 Kg (hết hạn 16/08)"])
	goi = _chay(tk.nhac_ton_duoi_muc, get_all=ga)
	la("tồn thấp: một tin mỗi kho", [(g.ma_tin, g.khoa) for g in goi],
		[("kho_ton_duoi_muc", "ton-thap:Kho D1 - TV:%s" % hom), ("kho_ton_duoi_muc", "ton-thap:Kho TC - TV:%s" % hom)])
	la("chỉ món dưới mức", (goi[0].dong[1:2], goi[1].dong[1:2]), (["Bột mì số 13: 20 Kg (mức tối thiểu 50)"], ["Bơ lạt: 0 Kg (mức tối thiểu 2)"]))
	_khong_tien(goi)
	la("không có gì thì im", _chay(lambda: (tk.nhac_don_mua_tre_hen(), tk.nhac_lo_sap_het_han(), tk.nhac_ton_duoi_muc(), tk.nhac_chuyen_chua_nhan()),
		get_all=lambda dt, **k: []), [])


@ca("v609 tồn lô theo kho: ERPNext trả rỗng thì cộng thẳng sổ gói lô và sổ kho; tồn âm hay 0 bị bỏ; lỗi cả hai đường thì rỗng và ghi Error Log")
def _ton_lo():
	la("gom thuần", tk.gom_ton_theo_kho([{"warehouse": "A", "qty": 2}, {"warehouse": "A", "qty": 3}, {"warehouse": "B", "qty": 0}, {"warehouse": "C", "qty": -1}, {"qty": 9}]), {"A": 5})
	fr = sys.modules["frappe"]
	bm = types.ModuleType("erpnext.stock.doctype.batch.batch"); bm.get_batch_qty = lambda **k: []
	sql_goi = []

	def sql(q, a=None, as_dict=False, **k):
		q1 = " ".join(q.split())
		sql_goi.append(q1)
		return [{"warehouse": "Kho D1 - TV", "qty": 4}] if "Serial and Batch Entry" in q else [{"warehouse": "Kho D1 - TV", "qty": 1}, {"warehouse": "Kho TC - TV", "qty": 2}]
	mods = {"erpnext": types.ModuleType("erpnext"), "erpnext.stock": types.ModuleType("erpnext.stock"), "erpnext.stock.doctype": types.ModuleType("erpnext.stock.doctype"),
		"erpnext.stock.doctype.batch": types.ModuleType("erpnext.stock.doctype.batch"), "erpnext.stock.doctype.batch.batch": bm}
	with um.patch.dict(sys.modules, mods), um.patch.object(fr, "db", types.SimpleNamespace(sql=sql, get_value=lambda *a, **k: None)):
		la("cộng gói lô và sổ kho theo kho", tk._ton_lo_theo_kho("LO-9", "BOT-01"), {"Kho D1 - TV": 5, "Kho TC - TV": 2})
	la("đọc đủ hai bảng", len(sql_goi), 2)
	# Codex #495 vòng 3: gói lô phải nối qua sổ kho còn hiệu lực (Pick List ghi sổ gói mà không vào sổ kho);
	# dòng sổ kho kiểu cũ loại dòng đã trỏ gói để không đếm hai lần.
	dung("gói lô nối qua Stock Ledger Entry, không qua bảng gói", "join `tabStock Ledger Entry` s on s.serial_and_batch_bundle = e.parent" in sql_goi[0]
		and "s.is_cancelled = 0" in sql_goi[0] and "Serial and Batch Bundle" not in sql_goi[0])
	dung("sổ kho kiểu cũ loại dòng có gói", "ifnull(serial_and_batch_bundle, '') = ''" in sql_goi[1] and "is_cancelled = 0" in sql_goi[1])
	bm.get_batch_qty = lambda **k: [{"warehouse": "Kho D1 - TV", "qty": 7}]
	with um.patch.dict(sys.modules, mods), um.patch.object(fr, "db", types.SimpleNamespace(sql=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("không được gọi")))):
		la("ERPNext có dòng thì không đụng sổ", tk._ton_lo_theo_kho("LO-9", "BOT-01"), {"Kho D1 - TV": 7})
	bm.get_batch_qty = lambda **k: (_ for _ in ()).throw(RuntimeError("hỏng"))
	loi = []
	with um.patch.dict(sys.modules, mods), um.patch.object(fr, "db", types.SimpleNamespace(sql=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("hỏng sql")))), \
			um.patch.object(fr, "log_error", lambda *a, **k: loi.append(a)):
		la("hỏng cả hai thì rỗng", tk._ton_lo_theo_kho("LO-9", "BOT-01"), {})
	la("và ghi Error Log", len(loi), 1)


@ca("v609 đơn web mới: tên viết tắt, không số điện thoại, giờ nhận, món cắt ở 5, bốn trạng thái phí (phí chưa rõ KHÔNG thành Tổng 0)")
def _don_web():
	from vagabond.don_web import quyet_phi_giao
	mon = [{"ma": "m%d" % i, "ten": "Bánh %d" % i, "sl": 2, "gia": 100000} for i in range(6)]
	# Codex #495 P2: Ahamove không báo được -> quyet_phi_giao trả phi_khach None.
	chua_ro = quyet_phi_giao(1200000, 2000000, False, None)
	la("tiền đề: phí chưa rõ", (chua_ro["phi_khach"], chua_ro["trang_thai"]), (None, "chua_ro"))
	goi = _chay(lambda: tk.bao_don_web_moi("DW-1", "Nguyễn Văn An", "2026-10-25T13:00", False, "", "12 Lê Lợi, Q1", mon, 1200000, chua_ro, "PK-77"))
	la("một tin", [(g.ma_tin, g.loai, g.chu_de, g.khoa) for g in goi], [("bh_don_web_moi", "thong_bao", "don_web", "don-web-moi:DW-1")])
	d = goi[0].dong
	la("đầu tin", d[0], "Khách N. V. An, nhận Chủ nhật, 25/10 13h - 15h")
	la("giao", d[1], "Giao: 12 Lê Lợi, Q1")
	la("món cắt ở 5", (d[2], d[7]), ("Bánh 0 x2", "+1 món khác"))
	la("phí chưa rõ: không có chữ Tổng, nói Sales báo phí", d[8], "Tiền bánh 1.200.000 đ, phí giao CHƯA RÕ (Ahamove không báo được), Sales báo phí khi gọi khách")
	la("mã Pancake", d[9:], ["Đã vào Pancake, mã PK-77"])
	dung("không lộ họ tên đầy đủ", not any("Nguyễn Văn An" in x for x in d))
	# Bốn trạng thái phí, chạy đúng hàm quyet_phi_giao thật.
	mp = quyet_phi_giao(1200000, 1000000, False, None)
	cx = quyet_phi_giao(500000, 1000000, False, {"ok": 1, "total_fee": 35000})
	tl = quyet_phi_giao(500000, 1000000, True, None)
	la("miễn phí giao", tk.dong_tien_don_web(1200000, mp), "Tổng 1.200.000 đ, miễn phí giao")
	la("có báo giá: tổng gồm phí", tk.dong_tien_don_web(500000, cx), "Tổng 535.000 đ (gồm phí giao 35.000 đ)")
	la("tự lấy", tk.dong_tien_don_web(500000, tl), "Tổng 500.000 đ, tự lấy")
	goi = _chay(lambda: tk.bao_don_web_moi("DW-2", "An", "", True, "The Vagabond Thảo Điền", "", mon[:1], 100000, tl, ""))
	la("tự lấy, chưa rõ giờ", goi[0].dong[:2], ["Khách An, chưa rõ giờ nhận", "Tự lấy tại The Vagabond Thảo Điền"])


@ca("v609 an toàn: kênh Zalo lỗi thì hook im và ghi Error Log, lỗi chết giao dịch thì ném tiếp cho chứng từ dừng")
def _an_toan():
	pr = _doc(name="PNK-9", docstatus=0, supplier_name="X", set_warehouse="K", items=ITEMS)
	goi, log = _loi_ghi(lambda: tk.khi_lap_phieu_nhap(pr), nem_loi=RuntimeError("mạng"))
	la("lỗi thường nuốt", goi, [])
	la("ghi Error Log", len(log), 1)
	nem("lỗi chết giao dịch ném tiếp", lambda: _chay(lambda: tk.khi_lap_phieu_nhap(pr), chet=True, nem_loi=RuntimeError("deadlock")), RuntimeError)
	# Hàm điều phối Stock Entry cũng không nuốt lỗi chết giao dịch.
	se = _doc(name="PXK-9", docstatus=1, purpose="Material Transfer", vgb_muc_dich_xuat="", vgb_huy=0, from_warehouse="A", to_warehouse="B", items=ITEMS)
	nem("điều phối ném tiếp", lambda: _chay(lambda: tk.khi_ghi_so_phieu_kho(se), chet=True, nem_loi=RuntimeError("deadlock")), RuntimeError)


def _ham(cay, ten):
	return next(n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten)


def _goi_trong(ham, ten):
	return [n for n in ast.walk(ham) if isinstance(n, ast.Call) and ast.unparse(n.func).endswith(ten)]


@ca("v609 nối dây: hooks.py đủ 9 móc và 5 lịch, Nhận hàng giương cờ trước insert, ba chỗ gọi tay có thật và đứng đúng chỗ")
def _noi_day():
	src = open(os.path.join(GOI, "hooks.py"), encoding="utf-8").read()
	for dt, sk, ham in (("Material Request", "after_insert", "khi_co_yeu_cau_mua"), ("Material Request", "on_submit", "khi_co_yeu_cau_mua"),
			("Purchase Order", "on_submit", "khi_ghi_so_don_mua"), ("Purchase Receipt", "after_insert", "khi_lap_phieu_nhap"),
			("Purchase Receipt", "on_submit", "khi_ghi_so_phieu_nhap"), ("Stock Entry", "after_insert", "khi_lap_phieu_kho"),
			("Stock Entry", "on_submit", "khi_ghi_so_phieu_kho"), ("Delivery Note", "on_submit", "khi_ghi_so_giao_si"),
			("Phieu Kiem Ke", "on_update", "khi_doi_phieu_kiem_ke")):
		dung("móc %s %s" % (dt, sk), '("%s", "%s", "vagabond.tin_kho.%s")' % (dt, sk, ham) in src)
	for lich, ham in (("0 7 * * *", "nhac_lo_sap_het_han"), ("0 7 * * *", "nhac_ton_duoi_muc"), ("0 8 * * *", "nhac_don_mua_tre_hen"),
			("25 8 * * *", "nhac_hang_ve_chua_hoa_don")):
		dung("lịch %s" % ham, 'setdefault("%s", []).append("vagabond.tin_kho.%s")' % (lich, ham) in src)
	dung("mỗi giờ chuyển chưa nhận", 'setdefault("hourly", []).append("vagabond.tin_kho.nhac_chuyen_chua_nhan")' in src)
	# Nạp hooks.py thật để chắc các dòng nối không làm hỏng cấu trúc.
	g = {"__file__": os.path.join(GOI, "hooks.py")}
	exec(compile(src, "hooks.py", "exec"), g)
	la("Stock Entry on_submit: tin kho đứng cuối, sau trừ kho bù", g["doc_events"]["Stock Entry"]["on_submit"][-2:],
		["vagabond.tru_kho_bu.khi_nhap_kho", "vagabond.tin_kho.khi_ghi_so_phieu_kho"])
	la("Phieu Kiem Ke on_update giữ giao việc", g["doc_events"]["Phieu Kiem Ke"]["on_update"],
		["vagabond.giao_viec.khi_sinh_phieu", "vagabond.tin_kho.khi_doi_phieu_kiem_ke"])
	la("Purchase Order on_submit", g["doc_events"]["Purchase Order"]["on_submit"], ["vagabond.tin_kho.khi_ghi_so_don_mua"])
	# Nhận hàng: cờ đặt TRƯỚC insert.
	nh = _ham(ast.parse(open(os.path.join(GOI, "nhan_hang.py"), encoding="utf-8").read()), "tao_phieu")
	dong = [n.lineno for n in ast.walk(nh) if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "pr.flags.vgb_nhap_ngay"]
	ins = [n.lineno for n in ast.walk(nh) if isinstance(n, ast.Call) and ast.unparse(n.func) == "pr.insert"]
	dung("cờ vgb_nhap_ngay đặt trước pr.insert", len(dong) == 1 and len(ins) == 1 and dong[0] < ins[0])
	# Ba chỗ gọi tay.
	xn = _ham(ast.parse(open(os.path.join(GOI, "nhan_dieu_chuyen.py"), encoding="utf-8").read()), "xac_nhan")
	la("xac_nhan gọi bao_da_nhan_chuyen một lần", len(_goi_trong(xn, "bao_da_nhan_chuyen")), 1)
	gs = _ham(ast.parse(open(os.path.join(GOI, "kiem_ke.py"), encoding="utf-8").read()), "ghi_so")
	la("ghi_so gọi hai tin", (len(_goi_trong(gs, "bao_kiem_ke_da_ghi_so")), len(_goi_trong(gs, "bao_ke_toan_kiem_ke_lech"))), (1, 1))
	td = _ham(ast.parse(open(os.path.join(GOI, "don_hang.py"), encoding="utf-8").read()), "tao_don")
	goi = _goi_trong(td, "bao_don_web_moi")
	la("tao_don gọi bao_don_web_moi một lần", len(goi), 1)
	dung("truyền nguyên phi, không ép phí chưa rõ thành 0 (Codex #495)", ast.unparse(goi[0].args[8]) == "phi" and "or 0" not in ast.unparse(goi[0]))
	# Lời gọi nằm trong nhánh da_nhan: tìm If bao quanh.
	bao_quanh = [n for n in ast.walk(td) if isinstance(n, ast.If) and any(c is goi[0] for c in ast.walk(n)) and "da_nhan" in ast.unparse(n.test)]
	dung("chỉ khi Pancake đã nhận", len(bao_quanh) >= 1)
