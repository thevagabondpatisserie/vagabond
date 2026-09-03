# -*- coding: utf-8 -*-
"""Cho bếp xuất được lô đã quá hạn ghi trên hệ, và để lại vết.

Vì sao có tệp này
-----------------
Chiều 03/09/2026 Khải ghi phiếu làm Bánh Ổ Mille Crepe Avocado thì bị chặn
ở mấy dòng nguyên liệu "hết date". Đo trên site thấy ba lớp chặn chồng lên
nhau, mà lớp nào cũng đủ để bếp đứng im:

1. ERPNext KHÔNG cho bảng chọn lô nhìn thấy lô quá hạn. Hàm
   `get_auto_batch_nos` lọc `expiry_date >= today` trừ khi gọi kèm cờ
   `for_stock_levels`. Nên `lo_hang._ton_tung_lo` hỏi tồn từng lô là nhận
   về rỗng, dù kho thật còn hàng.
2. Đường dự phòng của `lo_hang` cộng sổ kho theo cột `batch_no` của Stock
   Ledger Entry. ERPNext v16 để cột đó TRỐNG, số lô nằm trong gói Serial
   and Batch Bundle. Đo ngày 03/09: NVLT00037 còn 3.000 gram ở Kho tổng
   307, sổ kho có đúng một dòng và cột batch_no của nó là NULL. Nghĩa là
   đường dự phòng chưa bao giờ đỡ được gì.
3. Cả hai lớp trên qua được thì tới `StockEntry.validate_batch` của
   ERPNext (stock_entry.py:4182): với phiếu Manufacture, Repack, Material
   Transfer for Manufacture và Send to Subcontractor, hễ lô quá hạn là ném
   "Batch {0} of Item {1} has expired." và không ai ghi được phiếu.

Hệ quả cộng lại: 171 lô đang quá hạn, 106 lô trong đó còn ghi số dư. Hàng
nằm trong kho mà máy vừa không thấy vừa không cho lấy, câu lỗi bếp nhận
được lại là "thiếu hàng trong kho".

Chốt của anh Việt 03/09/2026: tắt chốt chặn để bếp xuất được. Tắt chứ
không phải xoá: ô "Chặn xuất lô quá hạn" nằm trong Vagabond Settings, tích
vào là ERPNext chặn lại như cũ. Mặc định (ô trống) là KHÔNG chặn.

Cái gì vẫn giữ nguyên
---------------------
- Lô bị TẮT (disabled) vẫn chặn cứng. Tắt một lô là quyết định của người,
  máy không được cãi.
- Chỉ ưu tiên hạ xuống chứ không đảo: `lo_hang` vẫn lấy lô còn hạn trước,
  hết lô còn hạn mới tới mã thay thế, hết mã thay thế mới tới lô quá hạn.
  Máy không tự ý dồn hàng quá hạn vào bánh khi trong kho còn hàng tốt.
- Mỗi phiếu có dùng lô quá hạn đều bị ghi một câu vào ô Ghi chú, nêu rõ mã
  nào lô nào hạn ngày nào. Không có chuyện xuất lặng lẽ.

Vá bằng cách thay hàm, KHÔNG bằng override_doctype_class
--------------------------------------------------------
Đọc `hooks.py` để thấy vì sao: ngày 21/08/2026 hai lớp thay Purchase
Receipt và Purchase Invoice đã làm CẢ TIỆM không nhập kho được. Ở đây chỉ
thay đúng MỘT hàm `validate_batch`, thay lúc hook before_validate của Stock
Entry chạy, tức là ngay trước khi ERPNext gọi hàm đó trong cùng một lần
lưu. Thay lại lần hai không đổi gì (có cờ đánh dấu). Hỏng ở bước thay thì
ghi nhật ký rồi để ERPNext chạy y như cũ, chứ không kéo đổ phiếu.
"""

# ------------------------------------------------------------ phần thuần

# Bốn loại phiếu mà ERPNext chặn lô quá hạn. Chép đúng từ
# erpnext/stock/doctype/stock_entry/stock_entry.py:4183.
PHIEU_BI_CHAN = (
	"Material Transfer for Manufacture",
	"Manufacture",
	"Repack",
	"Send to Subcontractor",
)

DAU_CAU = "Đã xuất lô quá hạn:"

# O tat chot chan, khai bang ma nguon nen site thu va site that giong nhau.
# De TRONG la KHONG chan, dung chot 03/09/2026. Tich vao thi ERPNext chan
# lai y nhu cu.
TRUONG_MOI = {
	"Vagabond Settings": [
		{
			"fieldname": "sec_kho_lo", "label": "Kho theo lô",
			"fieldtype": "Section Break", "insert_after": "tro_ly_luot_thang",
		},
		{
			"fieldname": "chan_lo_het_han", "label": "Chặn xuất lô quá hạn",
			"fieldtype": "Check", "insert_after": "sec_kho_lo", "default": "0",
			"description": (
				"Để trống: bếp xuất được lô đã quá hạn ghi trên hệ, và mỗi phiếu "
				"như vậy bị ghi một câu vào ô Ghi chú nêu rõ mã nào lô nào hạn "
				"ngày nào. Tích vào: ERPNext chặn lại như cũ, phiếu sản xuất có "
				"lô quá hạn sẽ không lưu được. Lô bị TẮT thì luôn chặn, không "
				"liên quan tới ô này."
			),
		},
	]
}


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

	`cac_lo` là [(mã hàng, tên lô, hạn dùng)].
	"""
	if not cac_lo:
		return ""
	phan = "; ".join(
		"%s lô %s hạn %s" % (ma, lo, ngay_goc(han)) for ma, lo, han in cac_lo
	)
	return "%s %s. Ô chặn hạn dùng trong Vagabond Settings đang tắt." % (DAU_CAU, phan)


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
	dong = [d for d in cu.splitlines() if not d.strip().startswith(DAU_CAU)]
	dong.append(moi)
	return "\n".join(d for d in dong if d.strip())


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, getdate, today

_DA_THAY = False


def dang_chan():
	"""Có đang bật chốt chặn lô quá hạn không. MẶC ĐỊNH LÀ KHÔNG.

	Ô trống (chưa ai đụng tới) nghĩa là không chặn, đúng chốt 03/09/2026.
	Muốn chặn lại thì tích ô trong Vagabond Settings.
	"""
	try:
		return cint(frappe.db.get_single_value("Vagabond Settings", "chan_lo_het_han"))
	except Exception:
		return 0


def _ho_so_lo(ten):
	try:
		return frappe.db.get_value(
			"Batch", ten, ["disabled", "expiry_date"], as_dict=True
		) or {}
	except Exception:
		return {}


def _ghi_vet(doc, cac_lo):
	try:
		cau = cau_ghi_chu(cac_lo)
		doc.remarks = them_ghi_chu(getattr(doc, "remarks", ""), cau)
	except Exception:
		pass


def _thay_the(goc):
	"""Hàm validate_batch mới. Giữ chặn lô TẮT, chỉ bỏ chặn lô quá hạn."""

	def validate_batch(self):
		if dang_chan():
			return goc(self)
		if getattr(self, "purpose", None) not in PHIEU_BI_CHAN:
			return None
		cac_lo = []
		for dong in self.get("items") or []:
			if not dong.batch_no:
				continue
			ho = _ho_so_lo(dong.batch_no)
			if cint(ho.get("disabled")):
				frappe.throw(
					"Lô %s của mã %s đang bị TẮT nên không xuất được. "
					"Ai tắt lô thì người đó mở lại." % (dong.batch_no, dong.item_code)
				)
			han = ho.get("expiry_date")
			if han and getdate(self.posting_date) > getdate(han):
				cac_lo.append((dong.item_code, dong.batch_no, han))
		if cac_lo:
			_ghi_vet(self, cac_lo)
		return None

	validate_batch._vagabond = True
	return validate_batch


def mo_chot(doc=None, method=None):
	"""Thay hàm validate_batch của ERPNext. Gọi ở before_validate Stock Entry.

	Lặp lại được: lần thứ hai thấy cờ là đi ra ngay.
	"""
	global _DA_THAY
	if _DA_THAY:
		return
	try:
		from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

		goc = getattr(StockEntry, "validate_batch", None)
		if goc is None:
			_DA_THAY = True
			return
		if getattr(goc, "_vagabond", False):
			_DA_THAY = True
			return
		StockEntry.validate_batch = _thay_the(goc)
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
