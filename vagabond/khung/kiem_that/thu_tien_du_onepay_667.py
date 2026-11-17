"""v667 ca TÍCH HỢP: tiền nộp thừa trả qua OnePay ở đơn Pancake cũ.

Tầng khung chốt luật bằng DB giả. Tầng này hỏi điều bản giả không trả lời:
câu lọc "like %O97615T%" của dòng bảng kê có chạy đúng trên MariaDB thật
không, ô "Đơn Pancake khách đã trả tiền" có thật trên phiếu sau migrate
không, câu đọc khoá và khoá tên có chạy không, và phiếu nộp thừa ghi được.

Dựng giống ca Loan Anh (đơn 97790, OnePay 1.650.000 ở đơn cũ 97615) trên
chứng từ ảo; Pancake không gọi thật (số điện thoại đơn cũ đọc qua hàm giả).
Mọi thứ lùi về điểm lưu, xem nen.py.
"""

from unittest.mock import patch

import frappe
from frappe.utils import flt, today

from vagabond import hoan_tien
from vagabond.doi_soat_vendor import DT_DONG
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _mon, _nen

DU = 880000


def _don():
	ct, tk, _ = _nen()
	a = _mon(tk)
	hd = frappe.get_doc(dict(
		doctype="Sales Invoice", company=ct, currency="VND", conversion_rate=1,
		customer=frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name"),
		custom_pancake_display_id="97790", remarks="Pancake #97790 - Ms.Hảo - 0916220439",
		items=[dict(item_code=a, qty=1, rate=770000)],
	))
	hd.insert(ignore_permissions=True)
	nen._DA_TAO.append((hd.doctype, hd.name))
	hd.flags.ignore_permissions = True
	hd.submit()
	hd.reload()
	d = frappe.get_doc(dict(doctype=DT_DONG, company=ct, vendor="OnePay", loai="ban", nhom="ban",
		ngay=today(), ma_tham_chieu="S67355O97615T100622", ma_don="S67355O97615T100622",
		tien_hang=flt(hd.grand_total) + DU, khoa="kiem-667-" + frappe.generate_hash(length=10),
		trang_thai_khop="Không thấy chứng từ"))
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append((d.doctype, d.name))
	return hd


def _gia():
	return patch.multiple(hoan_tien, _sdt_don_pancake=lambda so: "0916220439",
		_don_cua_khach=lambda sdt: ["97615", "97790"],
		_khach_tren_don=lambda n, kh=None: {"ten": "Ms.Hảo", "sdt": "0916220439"},
		_bao_ke_toan=lambda h, s: (0, []))


@ca("v667 thật: đơn 97790 chưa chọn đơn cũ thì mời chọn 97615; chọn rồi thấy dư 880.000 từ bảng kê OnePay")
def _xem_that():
	hd = khong_nem("dựng đơn", _don)
	if not hd:
		return
	with _gia():
		t = khong_nem("xem chưa chọn", lambda: hoan_tien.xem_tien_du(hd.name)) or {}
		la("mời chọn đơn cũ", t.get("cho_chon_don_cu"), 1)
		dung("gợi ý có 97615", "97615" in [g["so"] for g in t.get("goi_y_don_cu") or []])
		t = khong_nem("xem đã chọn", lambda: hoan_tien.xem_tien_du(hd.name, don_cu="97615")) or {}
	la("phần dư", (t.get("duoc"), flt(t.get("tran"))), (1, float(DU)))


def _ngan_hang():
	"""Ngân hàng nhận tiền là ô Link tới Bank; bench trống thì dựng một ngân hàng ảo."""
	ten = frappe.db.get_value("Bank", {}, "name")
	if ten:
		return ten
	b = frappe.get_doc({"doctype": "Bank", "bank_name": "Kiem 667 Bank"})
	b.insert(ignore_permissions=True)
	nen._DA_TAO.append((b.doctype, b.name))
	return b.name


@ca("v667 thật: lập phiếu nộp thừa 880.000 từ đơn cũ, phiếu ghi đơn 97615; lập lần hai, hoá đơn khác lấy lại đơn 97615 đều bị chặn")
def _tao_that():
	hd = khong_nem("dựng đơn", _don)
	nh = khong_nem("ngân hàng", _ngan_hang)
	if not (hd and nh):
		return
	with _gia():
		kq = khong_nem("lập phiếu", lambda: hoan_tien.tao_tien_du(hd.name, ly_do="Khac", dien_giai="Ca kiểm v667",
			so_tien=DU, ten_tk="NGUYEN THI HAO", so_tk="0123456789", ngan_hang=nh, don_cu="97615")) or {}
		if kq.get("ho_so"):
			nen._DA_TAO.append((hoan_tien.DT, kq["ho_so"]))
		la("phiếu ghi đơn cũ", frappe.db.get_value(hoan_tien.DT, kq.get("ho_so"), ["so_tien", "don_tra_tien"]),
			(float(DU), "97615"))
		try:
			hoan_tien.tao_tien_du(hd.name, ly_do="Khac", dien_giai="lần hai", so_tien=DU, ten_tk="A",
				so_tk="1", ngan_hang=nh, don_cu="97615")
			loi = ""
		except frappe.ValidationError as e:
			loi = nen.cau_loi(e)
		dung("lần hai bị chặn", bool(loi))
		la("chỉ một phiếu", frappe.db.count(hoan_tien.DT, {"hoa_don": hd.name, "trang_thai": ["!=", "Da huy"]}), 1)
		hd2 = khong_nem("dựng đơn thứ hai", _don)
		if hd2:
			try:
				hoan_tien.xem_tien_du(hd2.name, don_cu="97615")
				loi = ""
			except frappe.ValidationError as e:
				loi = nen.cau_loi(e)
			dung("đơn cũ đã dùng thì hoá đơn khác không lấy được", kq.get("ho_so", "?") in loi)
	r = frappe.db.sql("select is_free_lock(%s)", ("vgb_tien_du_don:97615",))
	la("đã nhả khoá đơn cũ", r[0][0], 1)
