# -*- coding: utf-8 -*-
"""v547: giá vốn phiếu kiểm kê, MỘT luật chung cho app và Desk.

Ca thật 30/09-01/10/2026:
- Kiên lập phiếu kiểm kê Kho tổng 307 trên Desk, nạp nhiều dòng một lượt.
  Cột giá vốn ra 0 cả loạt dù sổ kho có giá (bơ 400 đ/g, Feuille 315 đ/g).
  ERPNext v16 coi giá 0 ghi sẵn là "định giá lại về 0" và không tự tra
  (stock_reconciliation.py: "an explicitly set zero rate is a real
  revaluation"), chỉ tự tra khi ô để TRỐNG.
- Màn Ghi sổ kiểm kê trên app lấy Item.valuation_rate (ô chung của mã,
  thường 0) thay vì giá sổ kho của đúng kho, nên phiếu Kho D1 của Dễ đòi
  điền tay 15 giá dù Kho D1 có giá cho phần lớn các món đó.

Luật chung (gia_von): dòng có số lượng mà giá vốn trống hoặc 0 thì lấy, theo
thứ tự, cái đầu tiên lớn hơn 0:
  1. giá bình quân trên sổ kho của ĐÚNG kho, tại ngày giờ phiếu;
  2. giá sổ kho gần nhất của mã ở kho khác cùng công ty, không sau mốc phiếu.
Không dùng giá hiện tại trên Item vì không có lịch sử tại mốc phiếu.
Không có giá thì yêu cầu kế toán nhập giá vốn đã xác minh cho dòng đó. Dòng bật "Cho phép định giá bằng 0" thì giữ nguyên.

App gọi goi_y_gia (cùng luật) để điền sẵn, Desk đi qua hook trước khi lưu.
"""

import frappe
from frappe.utils import flt

NGUON = ("so_kho", "kho_khac")


def can_dien(qty, gia, cho_phep_0=0, gia_hien_tai=None):
	"""THUẦN: dòng có số lượng, giá trống hoặc 0, không chủ ý định giá 0.

	Codex #401 F1: dòng đã tra được giá hiện tại (> 0) mà người dùng gõ 0 là
	CHỦ Ý định giá lại về 0, giữ nguyên để ERPNext tự xử (không bật "Cho phép
	định giá bằng 0" thì ERPNext chặn khi ghi sổ). Chỉ điền khi dòng chưa từng
	được tra giá, như các dòng nạp một lượt trên phiếu của Kiên."""
	try:
		if int(cho_phep_0 or 0):
			return False
	except (TypeError, ValueError):
		pass
	if flt(gia_hien_tai) > 0 and gia not in (None, ""):
		return False
	return flt(qty) > 0 and (gia in (None, "") or flt(gia) <= 0)


def chon_gia(cac_gia):
	"""THUẦN: cac_gia là [(nguồn, giá)] theo thứ tự ưu tiên. Trả (giá, nguồn)
	của cái đầu tiên > 0, không có thì (None, None)."""
	for nguon, gia in cac_gia or []:
		if flt(gia) > 0:
			return flt(gia), nguon
	return None, None


def _gia_so_kho(ma, kho, ngay=None, gio=None):
	"""Giá bình quân sổ kho đúng kho tại mốc phiếu.

	Codex #401 vòng 3: KHÔNG nuốt lỗi. Sổ kho đọc không được (lỗi CSDL, lỗi
	ERPNext) khác hẳn kho chưa có giá; nuốt lỗi thành 0 thì gia_von rơi sang
	kho khác hay giá chung của mã và ghi sổ sai giá mà không ai biết. Để lỗi
	nổi lên: Desk không lưu được phiếu, app báo và chặn ghi sổ."""
	from erpnext.stock.utils import get_stock_balance

	kq = get_stock_balance(ma, kho, ngay, gio, with_valuation_rate=True)
	return flt(kq[1]) if isinstance(kq, (list, tuple)) and len(kq) > 1 else 0


def moc(ngay=None, gio=None):
	"""THUẦN: mốc thời gian 'YYYY-MM-DD HH:MM:SS' của phiếu, thiếu giờ thì cuối ngày."""
	if not ngay:
		return None
	g = str(gio or "23:59:59")
	if len(g) == 5:
		g += ":00"
	return "%s %s" % (str(ngay)[:10], g[:8])


def _gia_kho_khac(ma, kho, ngay=None, gio=None):
	"""Giá sổ kho gần nhất của mã ở KHO KHÁC cùng công ty, KHÔNG muộn hơn mốc
	phiếu (Codex #401 F2: phiếu ghi lùi ngày không được lấy giá tương lai)."""
	cty = frappe.db.get_value("Warehouse", kho, "company") if kho else None
	dk = ["item_code=%(ma)s", "is_cancelled=0", "valuation_rate > 0"]
	gt = {"ma": ma}
	if kho:
		dk.append("warehouse != %(kho)s")
		gt["kho"] = kho
	if cty:
		dk.append("company = %(cty)s")
		gt["cty"] = cty
	m = moc(ngay, gio)
	if m:
		dk.append("posting_datetime <= %(moc)s")
		gt["moc"] = m
	r = frappe.db.sql(
		"select valuation_rate from `tabStock Ledger Entry` where " + " and ".join(dk)
		+ " order by posting_datetime desc, creation desc limit 1", gt)
	return flt(r[0][0]) if r else 0


def gia_von(ma, kho, ngay=None, gio=None):
	"""Giá vốn đề xuất cho một mã ở một kho. Trả (giá, nguồn) hoặc (None, None)."""
	# Item.last_purchase_rate / valuation_rate không có mốc lịch sử hay công ty.
	# Cả phiếu hôm nay cũng có thể ghi trước lần cập nhật giá trong cùng ngày.
	gia = _gia_so_kho(ma, kho, ngay, gio)
	if flt(gia) > 0:
		return flt(gia), "so_kho"
	return chon_gia([("kho_khac", _gia_kho_khac(ma, kho, ngay, gio))])


def dien_gia(doc, method=None):
	"""Hook before_validate Stock Reconciliation (Desk, app, API đều đi qua).

	Hai việc trên từng dòng:
	- Mã không còn quản lý theo lô hay serial (v545) thì gỡ các ô lô cũ còn
	  dính trên dòng, để tờ mở từ trước khi tắt lô vẫn lưu được.
	- Giá vốn trống hoặc 0 thì điền theo gia_von.
	"""
	if doc.docstatus == 2:
		return
	for r in doc.get("items") or []:
		if not r.item_code:
			continue
		co = frappe.db.get_value("Item", r.item_code, ["has_batch_no", "has_serial_no"], as_dict=True) or {}
		if not co.get("has_batch_no") and not co.get("has_serial_no"):
			for f in ("batch_no", "serial_no", "serial_and_batch_bundle", "current_serial_and_batch_bundle"):
				if r.get(f):
					r.set(f, None)
			if r.get("use_serial_batch_fields"):
				r.use_serial_batch_fields = 0
		if can_dien(r.qty, r.valuation_rate, r.get("allow_zero_valuation_rate"), r.get("current_valuation_rate")):
			gia, _nguon = gia_von(r.item_code, r.warehouse or doc.get("set_warehouse"),
				doc.posting_date, doc.posting_time)
			if gia:
				r.valuation_rate = gia
			else:
				# Core ERPNext (bench de591661), validate_data: giá trống còn rơi
				# sang Item Price/Item hiện tại. Chặn trước để Desk không đi vòng.
				frappe.throw("Dòng %s, món %s: chưa có giá vốn trên sổ kho tới %s. "
					"Nhập giá vốn tại thời điểm kiểm kê đã được kế toán xác minh."
					% (r.idx, r.item_code, moc(doc.posting_date, doc.posting_time)))


@frappe.whitelist()
def goi_y_gia(kho, ma, ngay=None, gio=None):
	"""Cho màn Ghi sổ kiểm kê trên app: giá đề xuất theo cùng luật với Desk.

	`ngay`, `gio` phải là đúng ngày giờ app sẽ ghi sổ phiếu (Codex #401 vòng 3:
	chỉ gửi ngày thì mốc thành 23:59:59, phiếu ghi lùi vẫn lấy được giá muộn
	hơn giờ ghi sổ trong cùng ngày).

	Trả {mã: {"gia": giá, "nguon": nguồn}}; mã không có giá thì không có mặt."""
	if not frappe.has_permission("Stock Reconciliation", "create"):
		frappe.throw("Không có quyền lập phiếu kiểm kê.", frappe.PermissionError)
	if isinstance(ma, str):
		ma = frappe.parse_json(ma)
	ra = {}
	for m in (ma or [])[:2000]:
		gia, nguon = gia_von(m, kho, ngay, gio)
		if gia:
			ra[m] = {"gia": gia, "nguon": nguon}
	return ra
