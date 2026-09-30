# -*- coding: utf-8 -*-
"""v545 chạy THẬT: mã còn tồn ở lô cũ, tắt lô, rồi kiểm kê, xuất, nhập.

Ca thật 30/09/2026: Khải ghi sổ kiểm kê, Bánh Chocolatine Mini máy 20 đếm 0,
ERPNext báo "Vui lòng thêm Gói Số seri và Lô". Anh Việt chốt tắt lô cho mọi
mã. Điều cần chứng minh là sau khi tắt bằng `tat_lo.tat_lo` (ghi thẳng cờ,
vì form Item không cho bỏ tick khi đã có phát sinh), ERPNext vẫn nhận chứng
từ KHÔNG lô cho mã đang còn tồn nằm trong các lô cũ, số tồn và giá đúng.

Ca dựng đúng chuỗi của khách: hàng nhập vào hai lô, tắt lô, rồi phiếu điều
chỉnh tồn không lô. Không gọi thêm hàm nào ngoài chuỗi đó.
"""

import frappe
from frappe.utils import add_days, flt, nowdate

from vagabond import tat_lo
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_lo_theo_ngay_540 import _lo, _mon_lo, _nhap_lo
from vagabond.khung.kiem_that.thu_kho_dich_512 import _kho_bep
from vagabond import kho_san_xuat as ksx


def _dung(ma):
	cty = cong_ty()
	bep = "baker" if "baker" in ksx.BEP else "pastry"
	kho = _kho_bep(cty, bep, ksx.NGUYEN_LIEU)
	m = _mon_lo(ma)
	a = _lo("KT545-A-" + ma, m, add_days(nowdate(), 30))
	b = _lo("KT545-B-" + ma, m, add_days(nowdate(), 60))
	khong_nem("nhập lô A", lambda: _nhap_lo(m, kho, 12, a, add_days(nowdate(), -5), cty, 2000))
	khong_nem("nhập lô B", lambda: _nhap_lo(m, kho, 8, b, add_days(nowdate(), -2), cty, 3000))
	return cty, kho, m


def _ton(ma, kho):
	return flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty"))


def _tk_lech(cty):
	return frappe.db.get_value("Company", cty, ["stock_adjustment_account", "cost_center"])


def _kiem_ke(cty, kho, ma, so, gia):
	tk, cc = _tk_lech(cty)
	sr = frappe.new_doc("Stock Reconciliation")
	sr.company = cty
	sr.purpose = "Stock Reconciliation"
	sr.expense_account = tk
	sr.cost_center = cc
	sr.append("items", {"item_code": ma, "warehouse": kho, "qty": so, "valuation_rate": gia})
	sr.flags.ignore_permissions = True
	sr.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Reconciliation", sr.name))
	sr.submit()
	return sr


def _phieu(cty, kho, ma, so, loai, gia=None):
	tk, cc = _tk_lech(cty)
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = loai
	se.stock_entry_type = loai
	dong = {"item_code": ma, "qty": so, "expense_account": tk, "cost_center": cc}
	if loai == "Material Issue":
		dong["s_warehouse"] = kho
	else:
		dong.update(t_warehouse=kho, basic_rate=gia)
	se.append("items", dong)
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()
	return se


def _sle(ten, ma):
	return frappe.get_all("Stock Ledger Entry", filters={"voucher_no": ten, "item_code": ma, "is_cancelled": 0},
		fields=["actual_qty", "qty_after_transaction", "valuation_rate", "stock_value", "serial_and_batch_bundle"])


@ca("v545 that: tắt lô rồi kiểm kê về 0 cho mã còn 20 ở hai lô cũ (như Chocolatine Mini của Khải): ghi sổ được, tồn về 0")
def _kiem_ve_0():
	cty, kho, ma = _dung("NVLT-KT545A")
	la("trước khi tắt: tồn 20 ở hai lô", _ton(ma, kho), 20.0)
	la("tắt đúng mã", tat_lo.tat_lo([ma]), [ma])
	la("cờ lô đã tắt", frappe.db.get_value("Item", ma, ["has_batch_no", "has_expiry_date", "create_new_batch"]), (0, 0, 0))
	sr = khong_nem("kiểm kê về 0 không lô", lambda: _kiem_ke(cty, kho, ma, 0, 2400))
	if not sr:
		return
	la("tồn sau kiểm kê", _ton(ma, kho), 0.0)
	s = _sle(sr.name, ma)
	dung("có dòng sổ kho", len(s) >= 1)
	dung("không gắn gói lô", all(not x.serial_and_batch_bundle for x in s))


@ca("v545 that: tắt lô rồi đếm 15 trên 20, xuất 5, nhập 4 đều không lô: ghi sổ được, tồn 14, giá bình quân khác 0")
def _dem_xuat_nhap():
	cty, kho, ma = _dung("NVLT-KT545B")
	tat_lo.tat_lo([ma])
	sr = khong_nem("kiểm kê còn 15", lambda: _kiem_ke(cty, kho, ma, 15, 2400))
	if not sr:
		return
	la("tồn sau kiểm kê", _ton(ma, kho), 15.0)
	se = khong_nem("xuất 5 không lô", lambda: _phieu(cty, kho, ma, 5, "Material Issue"))
	if not se:
		return
	la("tồn sau xuất", _ton(ma, kho), 10.0)
	s = _sle(se.name, ma)
	dung("giá xuất khác 0", s and flt(s[0].valuation_rate) > 0)
	nh = khong_nem("nhập 4 không lô", lambda: _phieu(cty, kho, ma, 4, "Material Receipt", 3000))
	if not nh:
		return
	la("tồn sau nhập", _ton(ma, kho), 14.0)
	gia = flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "valuation_rate"))
	dung("giá bình quân nằm giữa 2400 và 3000", 2400 - 0.01 <= gia <= 3000 + 0.01)
	gt = flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "stock_value"))
	dung("giá trị tồn = tồn x giá", abs(gt - 14 * gia) < 1)


@ca("v545 that: tắt lô chỉ ghi ba cờ, lô và gói lô cũ còn nguyên")
def _khong_xoa_lo():
	cty, kho, ma = _dung("NVLT-KT545C")
	truoc = frappe.db.count("Batch", {"item": ma})
	tat_lo.tat_lo([ma])
	la("số lô không đổi", frappe.db.count("Batch", {"item": ma}), truoc)
	la("tồn không đổi", _ton(ma, kho), 20.0)
