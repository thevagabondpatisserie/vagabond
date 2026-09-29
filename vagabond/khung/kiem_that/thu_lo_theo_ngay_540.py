# -*- coding: utf-8 -*-
"""v540 chạy THẬT qua insert() và submit(): phiếu sản xuất ghi lùi ngày.

Codex #388 F2: ca kiểm tầng khung chỉ giả phần đọc sổ, chưa chứng minh ERPNext
chấp nhận phiếu Manufacture ghi lùi ngày với lô máy chọn, và sổ kho ghi đúng
lô, đúng giá. Ca này dựng lại đúng hình dạng ca thật PSX-2026-00116 (29/09/2026):

- Lô CŨ nhập từ 20 ngày trước, hạn dùng xa.
- Lô MỚI nhập 2 ngày trước, hạn dùng GẦN hơn, nên theo FEFO lô mới đứng trước.
- Phiếu sản xuất ghi ngày 10 ngày trước.

Hành vi cũ chọn lô MỚI (tồn hôm nay, hạn gần) cho một phiếu ghi lúc lô mới
chưa có, ERPNext chặn âm lô và giá xuất ra 0. Hành vi đúng: chọn lô CŨ, ghi
sổ được, sổ kho trừ lô cũ với đơn giá bằng giá nhập.
"""

import frappe
from frappe.utils import add_days, flt, nowdate

from vagabond import kho_san_xuat as ksx
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_kho_dich_512 import _kho_bep, _mon
from vagabond.khung.kiem_that.thu_ma_cap_so import _uom

MA = "NVLT-KT540"
TP = "BAWC-KT540"


def _mon_lo(ma):
	if frappe.db.exists("Item", ma):
		frappe.db.set_value("Item", ma, "has_batch_no", 1)
		return ma
	it = frappe.new_doc("Item")
	it.item_code = ma
	it.item_name = "Ca kiem 540 %s" % ma
	it.item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	it.stock_uom = _uom()
	it.is_stock_item = 1
	it.has_batch_no = 1
	it.has_expiry_date = 1
	it.shelf_life_in_days = 365
	it.flags.ignore_permissions = True
	it.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Item", it.name))
	return it.name


def _lo(ten, ma, han):
	if frappe.db.exists("Batch", ten):
		return ten
	b = frappe.new_doc("Batch")
	b.batch_id = ten
	b.item = ma
	b.expiry_date = han
	b.flags.ignore_permissions = True
	b.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Batch", b.name))
	return b.name


def _nhap_lo(ma, kho, so, lo, ngay, cty, gia):
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Material Receipt"
	se.stock_entry_type = "Material Receipt"
	se.set_posting_time = 1
	se.posting_date = ngay
	se.posting_time = "08:00:00"
	se.append("items", {"item_code": ma, "qty": so, "t_warehouse": kho, "basic_rate": gia,
		"batch_no": lo, "use_serial_batch_fields": 1})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()


def _dung():
	cty = cong_ty()
	kho = _kho_bep(cty, "baker", ksx.NGUYEN_LIEU) if "baker" in ksx.BEP else _kho_bep(cty, "pastry", ksx.NGUYEN_LIEU)
	kho_tp = _kho_bep(cty, "baker", ksx.THANH_PHAM) if "baker" in ksx.BEP else _kho_bep(cty, "pastry", ksx.THANH_PHAM)
	ma = _mon_lo(MA)
	tp = _mon(TP)
	cu = _lo("KT540-CU", ma, add_days(nowdate(), 300))
	moi = _lo("KT540-MOI", ma, add_days(nowdate(), 60))
	khong_nem("nhập lô cũ 20 ngày trước", lambda: _nhap_lo(ma, kho, 10, cu, add_days(nowdate(), -20), cty, 1000))
	khong_nem("nhập lô mới 2 ngày trước", lambda: _nhap_lo(ma, kho, 10, moi, add_days(nowdate(), -2), cty, 3000))
	return cty, kho, kho_tp, ma, tp, cu, moi


def _san_xuat(cty, kho, kho_tp, ma, tp, lo=None, set_posting_time=1, ngay=None):
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Manufacture"
	se.stock_entry_type = "Manufacture"
	se.set_posting_time = set_posting_time
	se.posting_date = ngay or add_days(nowdate(), -10)
	se.posting_time = "23:59:00"
	se.from_warehouse = kho
	se.to_warehouse = kho_tp
	dong = {"item_code": ma, "qty": 4, "s_warehouse": kho}
	if lo:
		dong.update(batch_no=lo, use_serial_batch_fields=1)
	se.append("items", dong)
	se.append("items", {"item_code": tp, "qty": 1, "t_warehouse": kho_tp, "is_finished_item": 1})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()
	return se


def _sle(ten, ma):
	r = frappe.get_all("Stock Ledger Entry", filters={"voucher_no": ten, "item_code": ma, "is_cancelled": 0},
		fields=["actual_qty", "valuation_rate", "serial_and_batch_bundle", "batch_no", "posting_date"])
	ra = []
	for x in r:
		lo = x.get("batch_no")
		if not lo and x.get("serial_and_batch_bundle"):
			lo = ",".join(sorted({e.batch_no for e in frappe.get_all("Serial and Batch Entry",
				filters={"parent": x["serial_and_batch_bundle"]}, fields=["batch_no"])}))
		ra.append((lo, flt(x["actual_qty"]), flt(x["valuation_rate"]), str(x["posting_date"])))
	return ra


@ca("v540 that: phiếu sản xuất ghi lùi 10 ngày, dòng chưa có lô: máy chọn lô có hàng ngày đó, ghi sổ được, giá khác 0")
def _chua_co_lo():
	cty, kho, kho_tp, ma, tp, cu, moi = _dung()
	se = khong_nem("ghi sổ phiếu ghi lùi", lambda: _san_xuat(cty, kho, kho_tp, ma, tp))
	if not se:
		return
	s = _sle(se.name, ma)
	la("một dòng sổ trừ nguyên liệu", len(s), 1)
	if s:
		la("trừ lô cũ, không phải lô sinh sau ngày ghi", s[0][0], cu)
		la("trừ 4", s[0][1], -4.0)
		dung("đơn giá xuất là giá lô cũ, không phải 0", abs(s[0][2] - 1000) < 0.01)
		la("sổ ghi đúng ngày lùi", s[0][3], str(add_days(nowdate(), -10)))


def _nhap_da_luu_lo_sai(cty, kho, kho_tp, ma, tp, moi):
	"""Nháp ĐÃ LƯU mang lô sinh sau ngày ghi, đúng như PSX-2026-00116 lưu
	trước v540. Lưu nháp qua insert() sẽ chạy gan_lo và chữa lô ngay, nên
	sau đó đặt lại lô sai thẳng vào bảng dòng để có đúng trạng thái cũ."""
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Manufacture"
	se.stock_entry_type = "Manufacture"
	se.set_posting_time = 1
	se.posting_date = add_days(nowdate(), -10)
	se.posting_time = "23:59:00"
	se.from_warehouse = kho
	se.to_warehouse = kho_tp
	se.append("items", {"item_code": ma, "qty": 4, "s_warehouse": kho, "batch_no": moi, "use_serial_batch_fields": 1})
	se.append("items", {"item_code": tp, "qty": 1, "t_warehouse": kho_tp, "is_finished_item": 1})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	dong_nvl = [d for d in se.items if d.item_code == ma]
	for d in dong_nvl[1:]:
		frappe.db.delete("Stock Entry Detail", d.name)
	frappe.db.set_value("Stock Entry Detail", dong_nvl[0].name,
		{"batch_no": moi, "qty": 4, "transfer_qty": 4, "use_serial_batch_fields": 1, "serial_and_batch_bundle": None},
		update_modified=False)
	return se.name


@ca("v540 that Codex #390: nháp ĐÃ LƯU mang lô sinh sau ngày ghi (như PSX-2026-00116), bấm Gửi thẳng không lưu lại: máy bù sang lô hợp lệ, ghi sổ được")
def _da_gan_lo_sai():
	# Bản đầu của ca này gọi insert() với lô sai rồi submit(). insert() chạy
	# gan_lo ở docstatus 0 nên lô đã được chữa TRƯỚC lượt Gửi, ca xanh mà
	# đường Gửi thẳng (docstatus=1 trước before_validate) chưa hề được kiểm.
	# Giữ đúng chuỗi của khách: nháp đã lưu sẵn, mở ra, bấm Gửi.
	cty, kho, kho_tp, ma, tp, cu, moi = _dung()
	ten = _nhap_da_luu_lo_sai(cty, kho, kho_tp, ma, tp, moi)
	nhap = frappe.get_doc("Stock Entry", ten)
	la("nháp đang mang lô sai", [d.batch_no for d in nhap.items if d.item_code == ma], [moi])

	def gui():
		nhap.flags.ignore_permissions = True
		nhap.submit()
		return nhap
	se = khong_nem("Gửi thẳng nháp đã lưu", gui)
	if not se:
		return
	s = _sle(se.name, ma)
	la("trừ lô cũ", [x[0] for x in s], [cu])
	dung("giá khác 0", all(x[2] > 0 for x in s))


@ca("v540 that Codex F1: nháp mang ngày cũ nhưng không bật sửa ngày giờ thì ghi theo hôm nay và vẫn chọn lô FEFO của hôm nay")
def _khong_bat_co():
	cty, kho, kho_tp, ma, tp, cu, moi = _dung()
	se = khong_nem("ghi sổ", lambda: _san_xuat(cty, kho, kho_tp, ma, tp, set_posting_time=0))
	if not se:
		return
	s = _sle(se.name, ma)
	la("ghi ngày hôm nay", [x[3] for x in s], [str(nowdate())])
	la("FEFO hôm nay: lô mới hạn gần đứng trước", [x[0] for x in s], [moi])


def _xuat_lo(ma, kho, so, lo, ngay, cty):
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Material Issue"
	se.stock_entry_type = "Material Issue"
	se.set_posting_time = 1
	se.posting_date = ngay
	se.posting_time = "09:00:00"
	se.append("items", {"item_code": ma, "qty": so, "s_warehouse": kho, "batch_no": lo, "use_serial_batch_fields": 1})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()


@ca("v540 that Codex #388: lô về 0 SAU ngày ghi rồi được nhập lại thì không được dùng cho phiếu ghi lùi; máy báo thiếu hàng rõ ràng, không để ERPNext báo âm")
def _xuong_0_giua_chung():
	cty, kho, kho_tp, ma, tp, cu, moi = _dung()
	khong_nem("xuất hết lô cũ 5 ngày trước", lambda: _xuat_lo(ma, kho, 10, cu, add_days(nowdate(), -5), cty))
	khong_nem("nhập lại lô cũ hôm qua", lambda: _nhap_lo(ma, kho, 10, cu, add_days(nowdate(), -1), cty, 1000))
	try:
		_san_xuat(cty, kho, kho_tp, ma, tp)
		dung("phải chặn vì ngày ghi không có lô nào dùng được", False)
	except frappe.ValidationError as e:
		cau = nen.cau_loi(e)
		dung("câu chặn là câu thiếu hàng của app, không phải âm lô của ERPNext: %s" % cau[:120],
			"negative" not in cau.lower())
