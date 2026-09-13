# -*- coding: utf-8 -*-
"""#206: lô và hạn dùng chỉ cảnh báo, không đổi dữ liệu Batch.

Stock Entry và phiếu mua/bán có cập nhật kho dùng phương thức riêng của
controller, không thay StockController chung. Giữ kiểm serial thuộc lô,
kiểm tồn, kho, mã, gói và sổ cái của ERPNext de591661. Lô hết hạn hoặc
disabled vẫn có dấu vết trên chứng từ. Không còn công tắc bật chặn HSD.
"""

# ------------------------------------------------------------ phần thuần

# Bốn luồng sản xuất của core và ba phiếu kho liên quan (#206).
# StockController.validate_serialized_batch còn chặn Material Receipt;
# Material Issue/Transfer cần cùng dấu vết cảnh báo, giữ kiểm serial/lô tắt.
PHIEU_BI_CHAN = (
	"Material Transfer for Manufacture",
	"Manufacture",
	"Repack",
	"Send to Subcontractor",
	"Material Receipt",
	"Material Issue",
	"Material Transfer",
)

DAU_CAU = "Phiếu dùng lô quá hạn:"

def ngay_goc(x):
	"""Đưa ngày về dạng so sánh được: chuỗi YYYY-MM-DD. THUẦN."""
	if not x:
		return ""
	return str(x)[:10]


def qua_han(han, ngay):
	"""Lô có hạn `han` đã quá ngày `ngay` chưa. THUẦN.

	Không ghi hạn thì KHÔNG tính là quá hạn, y như ERPNext.
	"""
	h, n = ngay_goc(han), ngay_goc(ngay)
	if not h or not n:
		return False
	return n > h


def chi_lo_qua_han(cac_lo, han_cua, ngay, bo_qua=None):
	"""Lọc lấy các lô ĐÃ quá hạn. THUẦN.

	`cac_lo` là {tên lô: tồn}, `han_cua` là {tên lô: hạn dùng}. `bo_qua` là
	các lô đã tính ở vòng trước, không lấy lại.
	"""
	ra = {}
	for ten, so in (cac_lo or {}).items():
		if bo_qua and ten in bo_qua:
			continue
		if qua_han((han_cua or {}).get(ten), ngay):
			ra[ten] = so
	return ra


def cau_ghi_chu(cac_lo):
	"""Câu ghi vào ô Ghi chú của phiếu. THUẦN.

	`cac_lo` là [(mã hàng, tên lô, hạn dùng, số dòng tuỳ chọn)].
	"""
	if not cac_lo:
		return ""
	phan = "; ".join(
		("Dòng %s: " % x[3] if len(x) > 3 and x[3] else "")
		+ "%s lô %s hạn %s" % (x[0], x[1], ngay_goc(x[2])) for x in cac_lo
	)
	return "%s %s. Kiểm tra chất lượng thực tế trước khi sử dụng." % (DAU_CAU, phan)


def them_ghi_chu(cu, moi):
	"""Nối câu mới vào ghi chú cũ, không nối hai lần. THUẦN."""
	cu = (cu or "").strip()
	moi = (moi or "").strip()
	if not moi:
		return cu
	if not cu:
		return moi
	if moi in cu:
		return cu
	# Lưu lần hai thì thay câu cũ của mình chứ không xếp chồng.
	dong = [d for d in cu.splitlines() if not d.strip().startswith((DAU_CAU, "Đã xuất lô quá hạn:", "Cảnh báo lô quá hạn:"))]
	dong.append(moi)
	return "\n".join(d for d in dong if d.strip())


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, getdate, today

_DA_THAY = False


def _ho_so_lo(ten):
	ho = frappe.db.get_value("Batch", ten, ["disabled", "expiry_date"], as_dict=True)
	if not ho:
		frappe.throw("Không đọc được lô %s. Kiểm tra lại lô đã chọn." % ten)
	return ho


def _o_ghi_chu(doc):
	return "vgb_dien_giai" if getattr(doc, "doctype", None) == "Delivery Note" else "remarks"


def _ghi_vet(doc, cac_lo):
	truong = _o_ghi_chu(doc)
	setattr(doc, truong, them_ghi_chu(getattr(doc, truong, ""), cau_ghi_chu(cac_lo)))


def _kiem_lo_va_ghi_vet(doc):
	"""Soi cả ô lô tay và gói v16, kể cả gói vừa sinh sau validate_batch.

	Không đổi Batch.expiry_date, không đổi purpose, không bắt rồi nuốt lỗi
	của lõi. Hỏng việc đọc gói thì phải dừng, không xuất mất dấu vết.
	"""
	cac_lo = []
	lo_tat = []
	for dong in doc.get("items") or []:
		lo = {getattr(dong, "batch_no", None)}
		goi = getattr(dong, "serial_and_batch_bundle", None)
		if goi:
			lo.update(frappe.get_all("Serial and Batch Entry",
				filters={"parent": goi, "parenttype": "Serial and Batch Bundle"},
				pluck="batch_no"))
		for ten in sorted(x for x in lo if x):
			ho = _ho_so_lo(ten)
			if cint(ho.get("disabled")):
				lo_tat.append("%s lô %s" % (dong.item_code, ten))
			han = ho.get("expiry_date")
			if han and doc.posting_date and getdate(doc.posting_date) > getdate(han):
				cac_lo.append((dong.item_code, ten, han, getattr(dong, "idx", None)))
	if cac_lo:
		_ghi_vet(doc, cac_lo)
	if lo_tat:
		truong = _o_ghi_chu(doc)
		cu = getattr(doc, truong, "") or ""
		cu = "\n".join(x for x in cu.splitlines() if not x.startswith("Phiếu dùng lô đã tắt:"))
		setattr(doc, truong, (cu + "\nPhiếu dùng lô đã tắt: " + "; ".join(sorted(set(lo_tat)))
			+ ". Kiểm tra chất lượng thực tế trước khi sử dụng.").strip())


def _trong_pham_vi(doc):
	loai = getattr(doc, "doctype", None)
	if loai in ("Purchase Receipt", "Delivery Note"):
		return True
	if loai in ("Purchase Invoice", "Sales Invoice"):
		return bool(cint(getattr(doc, "update_stock", 0)))
	return getattr(doc, "purpose", None) in PHIEU_BI_CHAN


def mo_chot_mua_ban(doc, method=None):
	"""Chỉ thay phương thức controller thực tế của bốn DocType được duyệt.

	Dùng type(doc) để giữ lớp Sales Invoice hiện hữu của ứng dụng; không
	thay lớp StockController hoặc ghi đè override_doctype_class.
	"""
	if getattr(doc, "doctype", None) not in ("Purchase Receipt", "Purchase Invoice", "Delivery Note", "Sales Invoice"):
		return
	lop = type(doc)
	goc = lop.validate_serialized_batch
	if not getattr(goc, "_vagabond", False):
		lop.validate_serialized_batch = _thay_kiem_serial(goc)


def _thay_kiem_serial(goc):
	"""ERPNext v16.28.0 controllers/stock_controller.py:321-357.

	Bản gốc kiểm serial.batch_no rồi kiểm expiry_date < posting_date với
	qty > 0 và docstatus < 2. Chỉ bỏ điều kiện hạn cho các phiếu kho đã liệt kê,
	giữ nguyên toàn bộ phép kiểm serial và lô tắt.
	"""
	def validate_serialized_batch(self):
		if not _trong_pham_vi(self) or cint(getattr(self, "docstatus", 0)) == 2:
			return goc(self)
		from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
		for dong in self.get("items") or []:
			if getattr(dong, "serial_no", None) and getattr(dong, "batch_no", None):
				for so in frappe.get_all("Serial No", fields=["batch_no", "name", "warehouse"],
						filters={"name": ("in", get_serial_nos(dong.serial_no))}):
					if so.warehouse and so.batch_no != dong.batch_no:
						frappe.throw(frappe._("Row #{0}: Serial No {1} does not belong to Batch {2}")
							.format(dong.idx, so.name, dong.batch_no))
		_kiem_lo_va_ghi_vet(self)
	validate_serialized_batch._vagabond = True
	return validate_serialized_batch


def _thay_the(goc):
	"""Hàm validate_batch mới. Chỉ ghi cảnh báo lô tắt/quá hạn."""

	def validate_batch(self):
		if getattr(self, "purpose", None) not in PHIEU_BI_CHAN:
			return goc(self)
		_kiem_lo_va_ghi_vet(self)
		return None

	validate_batch._vagabond = True
	return validate_batch


def mo_chot(doc=None, method=None):
	"""Thay hai phép kiểm lô của StockEntry ở before_validate.

	Lặp lại được: lần thứ hai thấy cờ là đi ra ngay.
	"""
	global _DA_THAY
	if _DA_THAY:
		return
	try:
		from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

		goc = StockEntry.validate_batch
		serial = StockEntry.validate_serialized_batch
		if not getattr(goc, "_vagabond", False):
			StockEntry.validate_batch = _thay_the(goc)
		if not getattr(serial, "_vagabond", False):
			StockEntry.validate_serialized_batch = _thay_kiem_serial(serial)
		_DA_THAY = True
	except Exception:
		# Thay không được thì để ERPNext chạy như cũ, đừng chặn ai lưu phiếu.
		try:
			frappe.log_error(frappe.get_traceback(), "lo_het_han: thay validate_batch")
		except Exception:
			pass


def han_cua(ten_lo):
	"""Hạn dùng của từng lô. {tên lô: hạn}. Lô không ghi hạn vẫn có mặt."""
	ra = {}
	if not ten_lo:
		return ra
	try:
		for b in frappe.get_all(
			"Batch",
			filters={"name": ["in", list(ten_lo)]},
			fields=["name", "expiry_date"],
			limit_page_length=0,
		):
			ra[b["name"]] = b.get("expiry_date")
	except Exception:
		return {}
	return ra


def hom_nay():
	try:
		return today()
	except Exception:
		return ""


def mo_han_lo(doc, method=None):
	"""HSD là dữ liệu ghi nhận, không bắt buộc/tự suy từ shelf life (#206).

	Chỉ thay phép đặt hạn trên Batch. Không đổi hạn lô đã lưu hay các kiểm
	item/serial/batch quantity khác của Batch.validate.
	"""
	lop = type(doc)
	if getattr(lop.set_expiry_date, '_vagabond', False):
		return
	def giu_han_da_nhap(self):
		# Giữ nguyên hạn của lô đã lưu; API nhận mua chủ động để trống khi
		# chưa biết ngày trên nhãn. Lô mới ở các cửa khác giữ tính shelf life.
		if not self.expiry_date and self.is_new() and not self.flags.get("vgb_hsd_thuc_te"):
			from frappe.utils import add_days
			co_han, so_ngay = frappe.db.get_value("Item", self.item, ["has_expiry_date", "shelf_life_in_days"])
			if co_han and so_ngay:
				if (not self.manufacturing_date and self.reference_doctype in
						["Stock Entry", "Purchase Receipt", "Purchase Invoice"] and self.reference_name):
					self.manufacturing_date = frappe.db.get_value(self.reference_doctype, self.reference_name, "posting_date")
				if self.manufacturing_date:
					self.expiry_date = add_days(self.manufacturing_date, so_ngay)
		if not self.expiry_date:
			frappe.msgprint('Lô %s chưa có hạn sử dụng. Kiểm tra nhãn hàng khi sử dụng.' % (self.name or self.item),
				title='Kiểm tra hạn dùng', indicator='orange')
	giu_han_da_nhap._vagabond = True
	lop.set_expiry_date = giu_han_da_nhap
