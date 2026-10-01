# -*- coding: utf-8 -*-
"""v547 chạy THẬT: phiếu kiểm kê lập trên Desk có cột giá vốn 0.

Ca thật 01/10/2026: Kiên nạp nhiều dòng một lượt vào phiếu kiểm kê Kho tổng
307, cột giá vốn 0 cả loạt dù sổ kho có giá. ERPNext coi giá 0 là định giá
lại về 0. Tờ đó còn mở từ trước v545 nên các dòng còn dính ô lô.

Ca dựng đúng chuỗi của khách: dòng ghi sẵn giá 0, insert rồi submit. Không gọi
hook hay hàm nào khác ngoài insert/submit.
"""

import frappe
from frappe.utils import flt

from vagabond import kho_san_xuat as ksx
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_kho_dich_512 import _kho_bep, _mon
from vagabond.khung.kiem_that.tat_lo_545 import _phieu, _ton


def _kho(cty):
	return _kho_bep(cty, "baker" if "baker" in ksx.BEP else "pastry", ksx.NGUYEN_LIEU)


def _phieu_kk(cty, kho, dong, gui=True, ngay=None, gio=None, dau_ky=False):
	tk = frappe.db.get_value("Company", cty, "stock_adjustment_account")
	sr = frappe.new_doc("Stock Reconciliation")
	sr.company = cty
	sr.purpose = "Opening Stock" if dau_ky else "Stock Reconciliation"
	if dau_ky:
		from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import get_difference_account
		tk = get_difference_account(sr.purpose, cty)
	sr.expense_account = tk
	sr.set_warehouse = kho
	if ngay:
		sr.set_posting_time = 1
		sr.posting_date = ngay
		sr.posting_time = gio or "08:00:00"
	for d in dong:
		r = {"warehouse": kho}
		r.update(d)
		sr.append("items", r)
	sr.flags.ignore_permissions = True
	sr.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Reconciliation", sr.name))
	if gui:
		sr.submit()
	return sr


@ca("v547 that: phiếu Desk ghi giá 0 cho mã có giá sổ kho 400 (như phiếu Kiên): lưu, ghi sổ được, giá lấy 400, giá trị tồn không về 0")
def _gia_0_lay_so_kho():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547A")
	khong_nem("nhập 100 giá 400", lambda: _phieu(cty, kho, ma, 100, "Material Receipt", 400))
	sr = khong_nem("kiểm kê 90 với giá 0", lambda: _phieu_kk(cty, kho, [{"item_code": ma, "qty": 90, "valuation_rate": 0}]))
	if not sr:
		return
	la("giá trên dòng", flt(sr.items[0].valuation_rate), 400.0)
	la("tồn sau ghi sổ", _ton(ma, kho), 90.0)
	gt = flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "stock_value"))
	dung("giá trị tồn 90 x 400, không về 0", abs(gt - 36000) < 1)


@ca("v547 vòng 4: giá Item hiện tại không được áp vào phiếu lùi ngày hoặc cùng ngày; nhập giá xác minh vẫn được")
def _gia_mua():
	from frappe.utils import add_days, nowdate
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547B")
	frappe.db.set_value("Item", ma, {"last_purchase_rate": 1500, "valuation_rate": 900})
	for ngay in (add_days(nowdate(), -5), nowdate()):
		for gia in (0, None):
			loi = None
			try:
				_phieu_kk(cty, kho, [{"item_code": ma, "qty": 3, "valuation_rate": gia}], ngay=ngay)
			except frappe.ValidationError as e:
				loi = str(e)
			dung("chặn trước fallback core, báo đúng món", bool(loi and ma in loi and "chưa có giá vốn" in loi))
	la("chưa ghi tồn", _ton(ma, kho), 0.0)
	dung("không sinh phiếu nháp dở", not frappe.db.exists("Stock Reconciliation Item", {"item_code": ma}))
	sr = khong_nem("giá nhập tay đã xác minh", lambda: _phieu_kk(cty, kho, [{"item_code": ma, "qty": 3, "valuation_rate": 700}], dau_ky=True))
	if sr:
		la("giữ giá nhập tay", flt(sr.items[0].valuation_rate), 700.0)
		la("giá trị tồn theo giá nhập tay", flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "stock_value")), 2100.0)


@ca("v547 that: dòng còn dính ô lô từ trước v545 trên mã đã tắt lô: lưu và ghi sổ được")
def _o_lo_cu():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547C")
	khong_nem("nhập 10 giá 2000", lambda: _phieu(cty, kho, ma, 10, "Material Receipt", 2000))
	sr = khong_nem("kiểm kê 8, dòng use_serial_batch_fields=1",
		lambda: _phieu_kk(cty, kho, [{"item_code": ma, "qty": 8, "valuation_rate": 0, "use_serial_batch_fields": 1}]))
	if not sr:
		return
	la("tồn sau ghi sổ", _ton(ma, kho), 8.0)
	la("đã gỡ cờ lô trên dòng", int(sr.items[0].use_serial_batch_fields or 0), 0)


@ca("v547 that: mã không có giá ở đâu cả thì vẫn chặn, không ghi sổ với giá 0")
def _khong_co_gia():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547D")
	frappe.db.set_value("Item", ma, {"last_purchase_rate": 0, "valuation_rate": 0})
	loi = None
	try:
		_phieu_kk(cty, kho, [{"item_code": ma, "qty": 2, "valuation_rate": 0}])
	except Exception as e:
		loi = str(e)
	dung("ERPNext chặn vì thiếu giá", bool(loi))
	la("không có tồn giá 0", _ton(ma, kho), 0.0)


@ca("v547 that: app gọi goi_y_gia nhận đúng giá sổ kho của kho đang kiểm")
def _goi_y():
	from vagabond import gia_von_kiem_ke as gv
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547E")
	khong_nem("nhập 5 giá 700", lambda: _phieu(cty, kho, ma, 5, "Material Receipt", 700))
	kq = khong_nem("gọi gợi ý", lambda: gv.goi_y_gia(kho, [ma]))
	if kq is None:
		return
	la("giá gợi ý", flt((kq.get(ma) or {}).get("gia")), 700.0)
	la("nguồn", (kq.get(ma) or {}).get("nguon"), "so_kho")


@ca("v547 that Codex #401 F1: dòng đã có giá hiện tại 400 mà gõ 0 thì không bị điền lại")
def _giu_0_chu_y():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547F")
	khong_nem("nhập 10 giá 400", lambda: _phieu(cty, kho, ma, 10, "Material Receipt", 400))
	sr = khong_nem("lưu nháp giá 0 có giá hiện tại 400",
		lambda: _phieu_kk(cty, kho, [{"item_code": ma, "qty": 9, "valuation_rate": 0, "current_valuation_rate": 400}], gui=False))
	if not sr:
		return
	# Core bench de591661 loại dòng qty không đổi + rate 0 trong remove_items_with_no_change.
	# Đếm 9 thay cho 10 để kiểm được hook giữ ý định giá 0 qua insert thật.
	la("giá vẫn 0, không bị điền", flt(sr.items[0].valuation_rate), 0.0)


@ca("v547 that Codex #401 F1: định giá về 0 có bật cờ cho phép thì ghi sổ được và giá trị tồn về 0")
def _dinh_gia_0_co_co():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547G")
	khong_nem("nhập 10 giá 400", lambda: _phieu(cty, kho, ma, 10, "Material Receipt", 400))
	sr = khong_nem("ghi sổ giá 0 có cờ",
		lambda: _phieu_kk(cty, kho, [{"item_code": ma, "qty": 9, "valuation_rate": 0, "allow_zero_valuation_rate": 1}]))
	if not sr:
		return
	la("giá giữ 0", flt(sr.items[0].valuation_rate), 0.0)
	la("giá trị tồn về 0", flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "stock_value")), 0.0)


@ca("v547 that Codex #401 F2: phiếu ghi lùi 5 ngày không lấy giá kho khác nhập SAU mốc phiếu")
def _khong_lay_gia_tuong_lai():
	from frappe.utils import add_days, nowdate
	from vagabond import gia_von_kiem_ke as gv
	cty = cong_ty()
	kho = _kho(cty)
	kho2 = _kho_bep(cty, "baker" if "baker" in ksx.BEP else "pastry", ksx.THANH_PHAM)
	ma = _mon("NVLT-KT547H")
	frappe.db.set_value("Item", ma, {"last_purchase_rate": 0, "valuation_rate": 0})
	khong_nem("nhập kho khác hôm nay giá 900", lambda: _phieu(cty, kho2, ma, 4, "Material Receipt", 900))
	gia, nguon = gv.gia_von(ma, kho, add_days(nowdate(), -5), "08:00:00")
	la("không có giá trước mốc phiếu", gia, None)
	gia2, nguon2 = gv.gia_von(ma, kho, nowdate(), "23:59:59")
	la("giá kho khác khi phiếu ghi hôm nay", (gia2, nguon2), (900.0, "kho_khac"))


@ca("v547 vòng 4: giá âm bị core từ chối, không bị hook thay bằng giá sổ kho")
def _gia_am():
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon("NVLT-KT547I")
	khong_nem("nhập 10 giá 400", lambda: _phieu(cty, kho, ma, 10, "Material Receipt", 400))
	loi = None
	try:
		_phieu_kk(cty, kho, [{"item_code": ma, "qty": 9, "valuation_rate": -1}])
	except frappe.ValidationError as e:
		loi = str(e)
	dung("core báo giá âm", bool(loi and "Negative Valuation Rate" in loi))
	la("không đổi tồn", _ton(ma, kho), 10.0)
	dung("không để phiếu nháp dở", not frappe.db.exists("Stock Reconciliation Item", {"item_code": ma}))
