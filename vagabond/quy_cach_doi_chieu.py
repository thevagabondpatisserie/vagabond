"""Căn cứ đối chiếu cho phiếu nhập đã được kiểm kê sửa quy cách.

PNK-2026-00158 ghi 18 hộp thành 9.000 g. PKK-2026-00005 đã bù đủ
9.000 g, giữ nguyên giá trị; sửa tiếp PR sẽ tính kho hai lần. Vì vậy chỉ
đổi cơ sở đối chiếu, có bản xác nhận được ghi sổ và trỏ đúng dòng kiểm kê.
Không lấy quy cách hiện tại của Item để tự sửa lịch sử.

Core purchase_invoice.py validate_with_previous_doc so item/uom với PR;
update_billing_status_in_pr dùng qty thương mại để tính tiền. Khi bật
set_landed_cost_based_on_purchase_invoice_rate vẫn repost PR dù PI không
update_stock. Ca tích hợp phải kiểm cả hai cấu hình, không suy từ cờ PI.
"""

import frappe
from frappe.utils import flt, get_datetime

LOAI = "Vagabond Quy Cach Doi Chieu"


@frappe.whitelist()
def goi_y_dong(phieu_nhap, phieu_kiem_ke):
	"""Chọn hai phiếu bằng Link; máy xác định dòng, không nhập mã con tay."""
	frappe.only_for("System Manager")
	pr = frappe.get_doc("Purchase Receipt", phieu_nhap)
	sr = frappe.get_doc("Stock Reconciliation", phieu_kiem_ke)
	pr.check_permission("read")
	sr.check_permission("read")
	return _dong_tu_hai_phieu(pr, sr)


def _dong_tu_hai_phieu(pr, sr):
	if len(sr.items) != 1:
		frappe.throw("Chọn phiếu kiểm kê riêng một dòng cho lần điều chỉnh quy cách này.")
	s = sr.items[0]
	ds = [r for r in pr.items if r.item_code == s.item_code and r.warehouse == s.warehouse
		and r.batch_no and r.batch_no == s.batch_no]
	if len(ds) != 1 or flt(ds[0].qty) <= 0:
		frappe.throw("Hai phiếu chưa xác định được duy nhất một dòng cùng món, kho và lô. Kiểm lại phiếu được chọn.")
	r = ds[0]
	return {"dong_nhap": r.name, "dong_kiem_ke": s.name,
		"he_so_cu": flt(r.conversion_factor),
		"he_so_moi": flt(r.conversion_factor) + (flt(s.qty) - flt(s.current_qty)) / flt(r.qty)}


def dien_dong(doc):
	if not doc.phieu_nhap or not doc.phieu_kiem_ke:
		return
	goi_y = _dong_tu_hai_phieu(frappe.get_doc("Purchase Receipt", doc.phieu_nhap),
		frappe.get_doc("Stock Reconciliation", doc.phieu_kiem_ke))
	# API thiếu mã dòng cũng dùng đúng lựa chọn như Desk. Không âm thầm
	# ghi đè tham chiếu/hệ số sai mà client gửi: validate vẫn phải bắt lỗi.
	for ten, gia_tri in goi_y.items():
		if not doc.get(ten):
			doc.set(ten, gia_tri)


def _gan_dieu_kien(ban, khoa=False):
	"""Kiểm chứng từ gốc mỗi lần dùng, kể cả khi dữ liệu bị sửa ngoài form."""
	trang_thai = []
	if khoa:
		# Khoá đầu chứng từ ngăn huỷ căn cứ giữa kiểm và ghi hoá đơn. Đọc
		# current read, không tin docstatus từ snapshot trước lúc chờ khoá.
		for bang, ten in (("Purchase Receipt", ban.phieu_nhap), ("Stock Reconciliation", ban.phieu_kiem_ke)):
			trang_thai.extend(frappe.db.sql("select docstatus from `tab" + bang + "` where name=%s for update", ten))
		if len(trang_thai) != 2 or any(x[0] != 1 for x in trang_thai):
			frappe.throw("Phiếu nhập hoặc kiểm kê đã đổi trạng thái. Tải lại đối chiếu trước khi ghi sổ.")
	pr = frappe.get_doc("Purchase Receipt", ban.phieu_nhap)
	sr = frappe.get_doc("Stock Reconciliation", ban.phieu_kiem_ke)
	r = next((x for x in pr.items if x.name == ban.dong_nhap), None)
	s = next((x for x in sr.items if x.name == ban.dong_kiem_ke), None)
	if pr.docstatus != 1 or sr.docstatus != 1 or not r or not s:
		frappe.throw("Căn cứ quy cách cần đúng dòng của phiếu nhập và phiếu kiểm kê đã ghi sổ.")
	if pr.company != sr.company or r.item_code != s.item_code or r.warehouse != s.warehouse:
		frappe.throw("Phiếu kiểm kê phải cùng công ty, món và kho với dòng nhập cần sửa quy cách.")
	if not r.batch_no or r.batch_no != s.batch_no:
		frappe.throw("Căn cứ quy cách hiện chỉ nhận điều chỉnh có cùng lô rõ ràng trên hai phiếu.")
	ngay_nhap = get_datetime(str(pr.posting_date) + " " + str(pr.posting_time or "00:00:00"))
	ngay_kiem = get_datetime(str(sr.posting_date) + " " + str(sr.posting_time or "00:00:00"))
	if len(sr.items) != 1 or ngay_kiem <= ngay_nhap or pr.is_return or r.get("is_fixed_asset"):
		frappe.throw("Cần phiếu kiểm kê riêng cho dòng nhập này, sau ngày nhập, không phải phiếu trả hàng.")
	cu, moi = flt(ban.he_so_cu), flt(ban.he_so_moi)
	if cu <= 0 or moi <= cu or abs(cu - flt(r.conversion_factor)) > 0.000001:
		frappe.throw("Hệ số cũ phải khớp phiếu nhập; căn cứ này chỉ xử lý lượng nhập bị ghi thiếu.")
	chenh = flt(r.qty) * (moi - cu)
	if abs(flt(s.current_qty) - flt(r.stock_qty)) > 0.0001:
		frappe.throw("Cần kiểm kê riêng đúng lượng của lô nhập gốc, chưa gộp với lần nhập khác.")
	if abs(flt(s.qty) - flt(s.current_qty) - chenh) > 0.0001:
		frappe.throw("Lượng kiểm kê bù không khớp chênh lệch quy cách của dòng nhập.")
	if abs(flt(sr.difference_amount)) > 0.01 or abs(
		flt(s.qty) * flt(s.valuation_rate) - flt(s.current_qty) * flt(s.current_valuation_rate)
	) > 0.01:
		frappe.throw("Căn cứ này chỉ nhận kiểm kê sửa lượng mà giữ nguyên giá trị kho.")
	return r


def kiem_ban_xac_nhan(doc):
	if not (doc.ly_do or "").strip():
		frappe.throw("Ghi lý do và căn cứ người có thẩm quyền duyệt điều chỉnh quy cách.")
	frappe.db.sql("select name from `tabPurchase Receipt Item` where name=%s for update", doc.dong_nhap)
	_gan_dieu_kien(doc, khoa=True)
	if frappe.db.sql("select name from `tabPurchase Invoice Item` where pr_detail=%s and docstatus=1 for update", doc.dong_nhap):
		frappe.throw("Dòng nhập đã có hoá đơn ghi sổ. Cần kế toán đối chiếu phần đã dùng trước khi xác nhận quy cách.")


def dong_hieu_luc(cac_dong, khoa=False):
	"""Trả bản sao dùng cho đối chiếu; tuyệt đối không ghi vào dòng PR."""
	# Đã đọc ERPNext v16.28.0, SHA de591661b9ba0bd3f62ac25b99b5c85c723515f6.
	# erpnext/accounts/doctype/purchase_invoice/purchase_invoice.py,
	# PurchaseInvoice.validate_with_previous_doc, cấu hình Purchase Receipt Item:
	# "ref_dn_field": "pr_detail",
	# "compare_fields": [["project", "="], ["item_code", "="], ["uom", "="]],
	# "is_child_table": True
	# Core không so conversion_factor ở đây. Chỉ bản sao có căn cứ được đổi
	# hệ số; PI vẫn phải giữ item/uom và qua toàn bộ validate chuẩn của core.
	# Cũng trong tệp trên, update_billing_status_in_pr lấy:
	# adjust_incoming_rate = frappe.db.get_single_value(
	#     "Buying Settings", "set_landed_cost_based_on_purchase_invoice_rate")
	# rồi truyền vào update_billing_percentage, không kiểm self.update_stock.
	# erpnext/stock/doctype/purchase_receipt/purchase_receipt.py,
	# update_billing_percentage có đúng nhánh:
	# if adjust_incoming_rate:
	#     adjust_incoming_rate_for_pr(pr_doc)
	# adjust_incoming_rate_for_pr gọi doc.update_valuation_rate(
	# reset_outgoing_rate=False), item.db_update(), và
	# doc.repost_future_sle_and_gle(force=True).
	# Vì vậy PI không cập nhật kho vẫn có thể repost PR: ca tích hợp phải
	# kiểm cả cờ 0/1, cả tiêu hao sau kiểm kê và huỷ PI, giữ nguyên SLE/GL.
	ra = [frappe._dict(dict(x)) for x in cac_dong]
	if not ra:
		return ra
	cac_ban = frappe.db.sql("""select name, phieu_nhap, dong_nhap, phieu_kiem_ke,
		dong_kiem_ke, he_so_cu, he_so_moi from `tabVagabond Quy Cach Doi Chieu`
		where docstatus=1 and dong_nhap in %(ten)s order by dong_nhap"""
		+ (" for update" if khoa else ""), {"ten": [r.name for r in ra]}, as_dict=True)
	ban_theo_dong = {b.dong_nhap: b for b in cac_ban}
	for r in ra:
		b = ban_theo_dong.get(r.name)
		if b:
			_gan_dieu_kien(b, khoa=khoa)
			r.he_so_goc = r.conversion_factor
			r.conversion_factor = b.he_so_moi
			r.stock_qty = flt(r.qty) * flt(b.he_so_moi)
			r.can_cu_quy_cach = b.name
	return ra


def luong_da_ghi(dong_hd, dong_nhap):
	"""Cùng Hộp phải chiếm cùng hạn mức, kể cả nháp cũ còn hệ số 500."""
	if dong_nhap.get("can_cu_quy_cach"):
		if dong_hd.get("uom") != dong_nhap.get("uom"):
			frappe.throw("Hoá đơn dùng căn cứ quy cách phải cùng đơn vị mua với phiếu nhập.")
		return flt(dong_hd.get("qty")) * flt(dong_nhap.get("conversion_factor"))
	return flt(dong_hd.get("qty")) * (flt(dong_hd.get("conversion_factor")) or 1)


@frappe.whitelist()
def thong_tin_phieu(phieu_nhap):
	"""Hiện căn cứ đã kiểm trên phiếu gốc, không thay số liệu lịch sử."""
	pr = frappe.get_doc("Purchase Receipt", phieu_nhap)
	pr.check_permission("read")
	if pr.docstatus != 1:
		return []
	return [{"item_code": r.item_code, "uom": r.uom, "stock_uom": r.stock_uom,
		"he_so_goc": r.he_so_goc, "he_so_hieu_luc": r.conversion_factor,
		"can_cu": r.can_cu_quy_cach}
		for r in dong_hieu_luc([d.as_dict() for d in pr.items]) if r.get("can_cu_quy_cach")]
