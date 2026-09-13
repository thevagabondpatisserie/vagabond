"""#227: ghi sổ SI thật, chốt không có doanh thu/công nợ và không xuất kho.

Chạy trong savepoint, khoá commit và cấm gửi ra ngoài của nen.py. Không
dùng hoá đơn cũ, không gọi M-Invoice. Thiếu danh mục hoặc core ném lỗi
là ca đỏ, không bỏ qua. Hai tài khoản 64182/33311 phải được kế toán khai.
"""

import frappe
from frappe.utils import today

from vagabond import hang_tang
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import _mot, ca, cong_ty, dung, la, mot_kho


def _hoa_don(tang=True):
	cty = cong_ty()
	mon = _mot("Item", {"is_sales_item": 1, "is_stock_item": 0, "disabled": 0, "is_fixed_asset": 0})
	khach = _mot("Customer", {"disabled": 0, "is_internal_customer": 0, "vgb_hang": ["!=", "OWNER"]})
	if not mon or not khach:
		frappe.throw("Cần món bán và khách hàng để dựng đơn thử #227.")
	hd = frappe.new_doc("Sales Invoice")
	hd.company = cty
	hd.customer = khach
	hd.posting_date = today()
	hd.due_date = today()
	hd.currency = "VND"
	hd.conversion_rate = 1
	hd.update_stock = 0
	hd.ignore_pricing_rule = 1
	hd.set("taxes", [])
	hd.taxes_and_charges = None
	# Fixture legacy khai VAT tường minh; không phụ thuộc cấu hình thuế
	# mặc định của site khi ca chỉ kiểm cơ chế VAT/GL cũ.
	from vagabond.hang_tang_so_cai import tai_khoan
	hd.append('taxes', {'charge_type': 'On Net Total', 'account_head': tai_khoan(cty, '33311', 'Liability'),
		'rate': 8, 'description': 'VAT ca kiểm legacy', 'included_in_print_rate': 1})
	hd.append("items", {"item_code": mon, "qty": 1, "rate": 1900000, "warehouse": mot_kho(cty)})
	if tang:
		hd.vgb_pt_thanh_toan = "Hàng tặng"
		hd.vgb_tang_loai = "marketing"
		hd.vgb_tang_ly_do = "Kiểm tích hợp số VAT hàng tặng #227"
	hd.flags.ignore_permissions = True
	hd.insert(ignore_permissions=True)
	nen._DA_TAO.append((hd.doctype, hd.name))
	# Mô phỏng SI nháp đã có trước patch kho #243; chỉ chạm phiếu thử vừa tạo.
	if hd.meta.has_field("vgb_tang_kho_moi"):
		frappe.db.set_value("Sales Invoice", hd.name, "vgb_tang_kho_moi", 0)
		hd.reload()
	if tang:
		hang_tang.duyet(hd.name, "Ca kiểm trong điểm lưu, không giao quà thật")
		hd.reload()
		hd.flags.ignore_permissions = True
	return hd


def _gl(hd):
	return frappe.get_all("GL Entry", filters={"voucher_type": hd.doctype, "voucher_no": hd.name},
		fields=["account", "debit", "credit", "party_type", "party", "is_cancelled"])


@ca("#227: SI tặng ghi VAT thật, không 511/131/JE/SLE, huỷ đảo đủ VAT")
def _ghi_va_huy():
	hd = _hoa_don()
	# Header rỗng vẫn dùng cost center công ty trước khi dựng GL.
	hd.cost_center = None
	hd.submit()
	hd.reload()
	la("khách không còn nợ", hd.outstanding_amount, 0)
	la("không treo trạng thái chưa trả", hd.status, "Paid")
	la("giá VAT được giữ", hd.grand_total, 1900000)
	la("chờ giá vốn", hd.vgb_tang_cho_gia_von, 1)
	dong = _gl(hd)
	la("hai dòng VAT", len(dong), 2)
	la("đúng hai tài khoản", {d.account for d in dong}, {hd.vgb_tang_tk_vat, hd.vgb_tang_tk_thue})
	la("Nợ VAT", sum(d.debit - d.credit for d in dong if d.account == hd.vgb_tang_tk_vat), hd.vgb_tang_tien_thue)
	la("Có thuế", sum(d.credit - d.debit for d in dong if d.account == hd.vgb_tang_tk_thue), hd.vgb_tang_tien_thue)
	dung("không gắn party vào chi phí", all(not d.party and not d.party_type for d in dong))
	dung("không có JE gạt công nợ", not hd.get("vgb_but_toan_tang"))
	la("không có sổ công nợ", frappe.db.count("Payment Ledger Entry", {"voucher_type": hd.doctype, "voucher_no": hd.name}), 0)
	la("không xuất kho", frappe.db.count("Stock Ledger Entry", {"voucher_type": hd.doctype, "voucher_no": hd.name}), 0)
	# Gọi hai bước core dựng lại GL trong savepoint. Chưa chạy toàn bộ
	# quy trình Repost Accounting Ledger qua doctype quản lý của ERPNext.
	from erpnext.accounts.general_ledger import make_reverse_gl_entries
	make_reverse_gl_entries(voucher_type=hd.doctype, voucher_no=hd.name)
	hd.make_gl_entries(from_repost=True)
	la("repost giữ số VAT", sum(d.debit - d.credit for d in _gl(hd) if d.account == hd.vgb_tang_tk_vat), hd.vgb_tang_tien_thue)
	hd.flags.ignore_permissions = True
	hd.cancel()
	la("đảo đủ nợ/có", sum(d.debit - d.credit for d in _gl(hd)), 0)
	for tk in (hd.vgb_tang_tk_vat, hd.vgb_tang_tk_thue):
		la("số dư sau huỷ bằng 0", sum(d.debit - d.credit for d in _gl(hd) if d.account == tk), 0)


@ca("#227: đơn bán thường vẫn ghi doanh thu và phải thu")
def _don_thuong():
	hd = _hoa_don(False)
	hd.submit()
	hd.reload()
	la("không có dấu hàng tặng", hd.get("vgb_tang_so_cai"), 0)
	dung("vẫn có khoản phải thu", hd.outstanding_amount > 0)
	dung("vẫn có Customer GL", any(d.party_type == "Customer" for d in _gl(hd)))


@ca("#227: chưa có kho sản xuất thì không được xuất kho tặng nửa vời")
def _chan_kho():
	frappe.db.set_single_value("Vagabond Settings", "hang_tang_xuat_kho_that", 1)
	hd = _hoa_don()
	hd.update_stock = 1
	try:
		hd.submit()
	except frappe.ValidationError as loi:
		dung("đúng lý do kho chưa triển khai", "Kho sản xuất cho hàng tặng chưa được triển khai" in str(loi))
	else:
		dung("phải chặn ghi sổ", False)
	la("không có GL", len(_gl(hd)), 0)
