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
