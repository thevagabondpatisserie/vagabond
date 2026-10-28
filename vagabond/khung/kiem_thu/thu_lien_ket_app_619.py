# -*- coding: utf-8 -*-
"""v619: đường mở trong tin Zalo đi vào APP, không vào bản desktop.

Anh Việt 28/10/2026 gửi ảnh nhóm "VGB VH Đặt hàng & Nhận hàng": tin "Đã chuyển hàng
giữa kho" ghi "Mở: https://vagabond.s.frappe.cloud/app/stock-entry/PDC-2026-00602",
bấm trên điện thoại ra màn Desk. Anh chốt: link trong thông báo Zalo phải là link app
hết. Cửa ghi tin (kenh_zalo._ghi_hop_thu) đổi mọi đường Desk qua lien_ket_app.

Ca chuỗi chạy ĐÚNG đường máy chạy: tin_kho._bao_da_chuyen (hook ghi sổ phiếu điều
chuyển) -> kenh_zalo.bao -> _ghi_hop_thu -> dòng sổ tin. Chỉ thay tầng Frappe (sổ tin
giả, nhóm giả) và địa chỉ app trong Cài đặt.
"""
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")

from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import lien_ket_app as lk  # noqa: E402
from vagabond import tin_kho as tk  # noqa: E402

APP = "https://app.thevagabondpatisserie.com"
SITE = ("vagabond.s.frappe.cloud", "erp.thevagabondpatisserie.com", "app.thevagabondpatisserie.com")
ANH = "https://vagabond.s.frappe.cloud/app/stock-entry/PDC-2026-00602"


def doi(x):
	return lk.doi_link(x, APP, SITE)


@ca("v619 link app: đúng link trong ảnh anh Việt thành màn Hàng chuyển về kho tôi mở thẳng phiếu")
def _anh():
	la("PDC trong ảnh", doi(ANH), APP + "/hang-chuyen-ve-kho-toi?mo=PDC-2026-00602")
	la("đường Desk trên tên miền erp", doi("https://erp.thevagabondpatisserie.com/app/stock-entry/PDC-2026-00603"),
		APP + "/hang-chuyen-ve-kho-toi?mo=PDC-2026-00603")
	la("đường Desk tương đối", doi("/app/stock-entry/PDC-1"), APP + "/hang-chuyen-ve-kho-toi?mo=PDC-1")
	la("/desk cũng là Desk", doi("https://vagabond.s.frappe.cloud/desk/stock-entry/PDC-1"), APP + "/hang-chuyen-ve-kho-toi?mo=PDC-1")


@ca("v619 link app: từng loại chứng từ ra đúng màn app, loại chưa có màn về trang chủ app")
def _bang():
	mau = [
		("/app/stock-entry/PSX-2026-00001", "/san-xuat"),
		("/app/stock-entry/PNT-2026-00001", "/nhap-kho"),
		("/app/stock-entry/PXD-2026-00001", "/phan-he-xuat-kho"),
		("/app/material-request/YCSX-2026-00001", "/lap-ke-hoach-san-xuat"),
		("/app/material-request/YCMH-2026-00001", "/duyet-yeu-cau"),
		("/app/material-request/YCDC-2026-00001", "/xuat-dieu-chuyen"),
		("/app/material-request?material_request_type=Manufacture", "/lap-ke-hoach-san-xuat"),
		("/app/material-request?material_request_type=Material%20Transfer", "/xuat-dieu-chuyen"),
		("/app/material-request/new", "/duyet-yeu-cau"),
		("/app/purchase-order/PO-1", "/don-mua-hang"),
		("/app/purchase-order?status=To%20Receive%20and%20Bill", "/don-mua-hang"),
		("/app/purchase-receipt?status=To%20Bill", "/nhap-kho"),
		("/app/purchase-invoice/PI-1", "/hoa-don-mua"),
		("/app/delivery-note/DN-1", "/xuat-ban-si"),
		("/app/phieu-kiem-ke/KK-1", "/kiem-ke"),
		("/app/stock-reconciliation/SR-1", "/kiem-ke"),
		("/app/batch", "/ton-kho"),
		("/app/query-report/Stock Balance", "/ton-kho"),
		("/app/query-report/Stock%20Balance", "/ton-kho"),
		("/app/query-report/General Ledger", "/bao-cao"),
		("/app/work-order?status=In%20Process", "/san-xuat"),
		("/app/sales-invoice/HDB-26-10-02615", "/hoa-don-ban"),
		("/app/payment-entry/APP-26-10-001", "/thanh-toan"),
		("/app/vagabond-don-web/DW-1", "/doanh-so"),
		("/app/vagabond-dang-ky-tiec/T-1", "/don-tiec"),
		("/app/vagabond-dat-ban/DB-1", "/thong-tin-dat-ban"),
		("/app/vagabond-kiem-kho-diem/KKD-1", "/kiem-banh"),
		("/app/loai-chua-co-man/X-1", "/bep"),
		("/app", "/bep"),
	]
	la("đủ bảng", [(d, doi(d)) for d, _ in mau], [(d, APP + m) for d, m in mau])


@ca("v619 link app: đường app đổi về tên miền app; đường khách, đường ngoài, đường đã đúng thì để nguyên")
def _giu():
	la("màn app trên tên miền mặc định", doi("https://vagabond.s.frappe.cloud/doanh-so"), APP + "/doanh-so")
	la("giữ tham số", doi("https://vagabond.s.frappe.cloud/bep?vd=VD-2026-00001"), APP + "/bep?vd=VD-2026-00001")
	la("đường tương đối của app", doi("/bep"), APP + "/bep")
	la("đã đúng thì y nguyên", doi(APP + "/hang-chuyen-ve-kho-toi?mo=PDC-1"), APP + "/hang-chuyen-ve-kho-toi?mo=PDC-1")
	la("đổi hai lần vẫn vậy", doi(doi(ANH)), doi(ANH))
	for x in ("https://order.thevagabondpatisserie.com/banh/xong/abc", "https://zalo.me/g/abc", "https://maps.google.com/?q=1",
			"", None, "mailto:a@b.c"):
		la("để nguyên %r" % (x,), doi(x), x)


@ca("v619 link app: đổi cả đường nằm giữa nội dung tin, giữ dấu câu cuối câu")
def _trong_chu():
	chu = ("Trạng thái: Chờ xác nhận. Mở phiếu: https://vagabond.s.frappe.cloud/app/vagabond-dang-ky-tiec/T-9.\n"
		"Xem thêm /app/stock-entry/PDC-7, và https://order.thevagabondpatisserie.com/banh")
	la("đổi đúng chỗ", lk.doi_trong_chu(chu, APP, SITE),
		"Trạng thái: Chờ xác nhận. Mở phiếu: " + APP + "/don-tiec.\n"
		"Xem thêm " + APP + "/hang-chuyen-ve-kho-toi?mo=PDC-7, và https://order.thevagabondpatisserie.com/banh")
	la("chữ không có đường", lk.doi_trong_chu("Bánh 1/2 kg, giá 10/11", APP, SITE), "Bánh 1/2 kg, giá 10/11")
	dung("không còn /app/ nào", "/app/" not in lk.doi_trong_chu(chu, APP, SITE))


@ca("v619 link app: tên máy của site gồm tên miền mặc định, erp, app; địa chỉ app lấy từ Cài đặt")
def _may():
	with um.patch.object(lk, "goc_app", lambda: "https://app.mien-moi.vn"), \
			um.patch.object(sys.modules["frappe"].utils, "get_url", lambda *a, **k: "https://vagabond.s.frappe.cloud"):
		may = lk.may_cua_site()
	dung("đủ ba tên máy và tên miền app mới", {"vagabond.s.frappe.cloud", "erp.thevagabondpatisserie.com",
		"app.thevagabondpatisserie.com", "app.mien-moi.vn"} <= may)
	with um.patch.object(lk, "goc_app", lambda: (_ for _ in ()).throw(RuntimeError("chưa đọc được Cài đặt"))):
		la("lỗi đọc Cài đặt thì tin giữ nguyên, không chặn gửi", lk.doi_tin("Mở: " + ANH), "Mở: " + ANH)


def _chay_chuoi(ham, doc, ma_tin):
	ghi = []

	class Tin(dict):
		def insert(self, **k):
			ghi.append(dict(self))
	fr = types.SimpleNamespace(
		generate_hash=lambda length=8: "h" * length, flags=types.SimpleNamespace(vagabond_kiem_that=False),
		db=types.SimpleNamespace(savepoint=lambda *a: None, rollback=lambda **k: None,
			after_commit=types.SimpleNamespace(add=lambda f: None)),
		get_doc=lambda d: Tin(d), log_error=lambda *a, **k: None, DuplicateEntryError=KeyError,
		utils=types.SimpleNamespace(get_url=lambda *a, **k: "https://vagabond.s.frappe.cloud" + (a[0] if a else "")))
	nhom = [{"ten_nhom": "VGB VH Đặt hàng & Nhận hàng", "chat_id": "c1", "bat": 1, "tin_nhan": ma_tin}]
	with um.patch.object(kz, "frappe", fr), um.patch.object(tk, "frappe", fr), \
			um.patch.object(kz, "_bat", lambda: 1), um.patch.object(kz, "_cac_nhom", lambda: nhom), \
			um.patch.object(lk, "goc_app", lambda: APP), \
			um.patch.object(lk, "may_cua_site", lambda: set(SITE)):
		ham(doc)
	return ghi


class D(dict):
	__getattr__ = dict.get


@ca("v619 chuỗi thật: ghi sổ phiếu điều chuyển PDC -> tin Zalo mở màn app đúng phiếu, không còn link Desk")
def _chuoi_dieu_chuyen():
	doc = D(name="PDC-2026-00602", from_warehouse="Baker - Thành phẩm - TV", to_warehouse="Kho D1 - TV",
		items=[D(item_name="Mini Foccacia Thảo mộc Địa Trung Hải", qty=5, uom="Món")])
	ghi = _chay_chuoi(tk._bao_da_chuyen, doc, "kho_da_chuyen")
	la("ghi một dòng sổ tin", len(ghi), 1)
	t = ghi[0]["noi_dung"]
	dung("mở màn app đúng phiếu: " + t, t.endswith("Mở: " + APP + "/hang-chuyen-ve-kho-toi?mo=PDC-2026-00602"))
	dung("không còn link Desk", "/app/" not in t and "frappe.cloud" not in t)


@ca("v619 chuỗi thật: xuất huỷ và xuất dùng nội bộ (cùng tiền tố PXD) mở đúng màn của từng loại")
def _chuoi_xuat():
	doc = D(name="PXD-2026-00009", from_warehouse="Kho D1 - TV", vgb_ly_do_huy="Hết hạn", vgb_muc_dich_xuat="",
		total_outgoing_value=0, items=[D(item_name="Bánh mì", qty=2, uom="Cái")])
	for ham, ma_tin, man in ((tk._bao_da_huy, "kho_da_huy", "/xuat-huy"),
			(tk._bao_ke_toan_gia_von_huy, "kt_xuat_huy_gia_von", "/xuat-huy"),
			(tk._bao_xuat_noi_bo, "kho_xuat_noi_bo", "/xuat-dung-noi-bo")):
		ghi = _chay_chuoi(ham, doc, ma_tin)
		la("%s ghi một dòng" % ma_tin, len(ghi), 1)
		dung("%s mở %s" % (ma_tin, man), ghi[0]["noi_dung"].endswith("Mở: " + APP + man))


@ca("v619 chuỗi thật: tham số link có dấu cách (báo cáo Stock Balance) đổi nguyên cả đường, không bị cắt ở dấu cách")
def _chuoi_dau_cach():
	from vagabond import tin_ton_sx as ts

	ghi = []

	def ham(_):
		kz.bao("viec", "kho", "Tồn âm", ["Bơ lạt: -2"],
			link=ts._url("/app/query-report/Stock Balance"), khoa="ton-am:1", ma_tin="kho_ton_am")
	with um.patch.object(ts, "frappe", types.SimpleNamespace(utils=types.SimpleNamespace(
			get_url=lambda *a, **k: "https://vagabond.s.frappe.cloud" + (a[0] if a else "")))):
		ghi = _chay_chuoi(ham, None, "kho_ton_am")
	la("ghi một dòng", len(ghi), 1)
	dung("mở màn Tồn kho: " + ghi[0]["noi_dung"], ghi[0]["noi_dung"].endswith("Mở: " + APP + "/ton-kho"))


@ca("v619 cửa ghi tin: đường Desk nằm trong dòng nội dung (tin tiệc, đặt bàn) và trong tin soạn sẵn cũng đổi sang app")
def _cua_ghi_trong_chu():
	def ham(_):
		kz.bao("thong_bao", "dat_ban", "Đăng ký tiệc mới", [
			"Trạng thái: Chờ xác nhận. Mở phiếu: https://vagabond.s.frappe.cloud/app/vagabond-dang-ky-tiec/T-9"],
			khoa="tiec:T-9", ma_tin="bh_tiec")
		kz.bao("ban_tin", "ban_hang", "x", khoa="soan-san:1", ma_tin="bh_tiec",
			noi_dung="Báo cáo ngày\nXem https://erp.thevagabondpatisserie.com/app/sales-invoice/HDB-1.")
	ghi = _chay_chuoi(ham, None, "bh_tiec")
	la("hai dòng", len(ghi), 2)
	dung("dòng nội dung đã đổi: " + ghi[0]["noi_dung"], (APP + "/don-tiec") in ghi[0]["noi_dung"] and "/app/" not in ghi[0]["noi_dung"])
	dung("tin soạn sẵn đã đổi: " + ghi[1]["noi_dung"], ghi[1]["noi_dung"].endswith("Xem " + APP + "/hoa-don-ban.") and "/app/" not in ghi[1]["noi_dung"])
