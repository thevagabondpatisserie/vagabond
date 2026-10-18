# -*- coding: utf-8 -*-
"""v602 chạy THẬT (Codex #488 vòng 2): lượt ghi sổ riêng của MỘT đơn.

Lượt riêng `ban_hang.ghi_so_mot_don_nen` đi tới `_ghi_so_mot_don`, tức là
submit Sales Invoice thật và sinh GL thật. AGENTS.md mục kiểm tích hợp bắt
buộc những đường như vậy có ca dựng chứng từ thật, ghi sổ thật, đọc lại sổ cái.

Ca dựng đúng chuỗi của hàng đợi: một bill quầy nháp, rồi gọi ĐÚNG hàm mà
`_xep_ghi_so` xếp lên hàng đợi, với đúng tham số. Không gọi thêm hàm nào
khác ngoài chuỗi đó. Chỉ chặn cửa phát hành HĐĐT (cho_xuat=False và cửa
xuất bị thay bằng hàm ném lỗi): bộ kiểm tích hợp không được gửi m-invoice.
Quầy dùng mã riêng KT602 để không lẫn bill thật.
"""

from unittest.mock import patch

import frappe
from frappe.utils import add_days, flt, today

from vagabond import ban_hang, hddt_bu
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_hang_tang_227 import _gl, _hoa_don

QUAY = "KT602"


def _bill_quay():
	hd = _hoa_don(False)
	hd.vgb_quay = QUAY
	hd.custom_nguon = "Tại chỗ"
	hd.vgb_pt_thanh_toan = "Tiền mặt"
	hd.save(ignore_permissions=True)
	hd.reload()
	return hd


def _cho_khoa():
	return flt(frappe.db.sql("SELECT @@SESSION.innodb_lock_wait_timeout")[0][0])


def _goi(ten, ngay):
	"""Gọi lượt riêng như hàng đợi gọi; giữ và trả lại trần chờ khoá của phiên."""
	cu = _cho_khoa()
	try:
		with patch.object(ban_hang, "_tu_xuat_hddt", side_effect=AssertionError("Ca kiểm không phát hành HĐĐT")):
			ket = ban_hang.ghi_so_mot_don_nen(ten, str(ngay), cho_xuat=False, nguon="kiem-that")
		trong = _cho_khoa()
	finally:
		frappe.db.sql("SET SESSION innodb_lock_wait_timeout = %s" % int(cu))
	return ket, trong


@ca("v602 thật: lượt riêng ghi sổ một bill quầy, GL cân, đặt trần chờ khoá dòng, nhả khoá đơn")
def _ghi_mot_don():
	hd = _bill_quay()
	la("trước: còn nháp", hd.docstatus, 0)
	ket, trong = _goi(hd.name, hd.posting_date)
	la("lượt riêng báo ghi sổ xong, không phát hành", ket, (1, 0, ""))
	hd.reload()
	la("đã ghi sổ thật", hd.docstatus, 1)
	so = _gl(hd)
	dung("có sổ cái thật", bool(so))
	la("sổ cái cân", round(sum(flt(d.debit) - flt(d.credit) for d in so), 2), 0)
	dung("có dòng phải thu của khách", any(d.party_type == "Customer" for d in so))
	la("trần chờ khoá dòng trong lượt", trong, hddt_bu.GIAY_CHO_KHOA_DONG)
	khoa = ban_hang._khoa_dong_bo(cho=1, im_lang=True)
	dung("khoá đơn Sales đã được nhả", khoa is not None)
	if khoa is not None:
		ban_hang._mo_khoa_dong_bo(khoa)


@ca("v602 thật: lượt tới muộn bỏ đơn đã ghi sổ và đơn đã kéo sang ngày khác, không sinh thêm sổ cái")
def _luot_muon():
	hd = _bill_quay()
	ket, _ = _goi(hd.name, add_days(hd.posting_date, -1))
	la("đơn đã đổi ngày: bỏ", ket, (0, 0, ""))
	hd.reload()
	la("vẫn nháp", hd.docstatus, 0)
	la("không có sổ cái", len(_gl(hd)), 0)
	_goi(hd.name, hd.posting_date)
	so = len(_gl(hd))
	ket, _ = _goi(hd.name, hd.posting_date)
	la("đơn đã ghi sổ: bỏ", ket, (0, 0, ""))
	la("không thêm dòng sổ cái", len(_gl(hd)), so)


@ca("v602 thật: lượt chờ hỏi được hàng đợi thật và đọc trạng thái đơn thật")
def _hoi_hang_doi():
	hd = _bill_quay()
	# Mã chưa từng xếp: hỏi được hàng đợi thì phải là False, không phải None.
	la("hỏi được hàng đợi", ban_hang._job_dang_chay("KT602-chua-xep-" + frappe.generate_hash(length=8)), False)
	la("đọc trạng thái nháp", ban_hang._trang_thai_lo([hd.name]), {hd.name: 0})
	_goi(hd.name, hd.posting_date)
	la("đọc trạng thái đã ghi sổ", ban_hang._trang_thai_lo([hd.name]), {hd.name: 1})
	la("đếm theo sổ", hddt_bu.ket_qua_lo([hd.name], ban_hang._trang_thai_lo([hd.name])), (1, []))
	la("hôm nay là ngày của bill", str(hd.posting_date), today())
