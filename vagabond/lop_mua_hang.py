"""Hai lớp thay thế cho Phiếu nhập kho và Hoá đơn mua, khai ở hooks.

Chỉ làm đúng một việc: sau khi ERPNext dựng xong các dòng sổ cái, gắn mã
nhà cung cấp vào những dòng rơi vào tài khoản hàng về chưa có hoá đơn. Lý
do và các đường đã loại bỏ nằm ở đầu vagabond/ke_toan_mua.py, đọc ở đó.

Tệp này tách riêng khỏi ke_toan_mua.py vì nó import erpnext. Máy chạy CI
của GitHub không có erpnext, mà bộ kiểm thử tầng khung phải chạy được ở đó,
nên mọi phép có thể kiểm thử đều nằm bên ke_toan_mua.py, tệp này chỉ còn
phần nối dây.

Ghi đè `get_gl_entries` chứ không ghi đè `make_gl_entries`: hàm dựng sổ trả
về danh sách để mình sửa, hàm kia đã ghi thẳng xuống cơ sở dữ liệu. Và bọc
try/except quanh phần của mình: gắn được đối tác thì tốt, không gắn được
cũng tuyệt đối không được làm rớt việc ghi sổ của cả tiệm.
"""

import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.stock.doctype.purchase_receipt.purchase_receipt import PurchaseReceipt

from vagabond import ke_toan_mua


def _gan(doc, cac_dong):
	try:
		tk = doc.get("stock_received_but_not_billed") or ke_toan_mua.tk_cho_hien_tai(
			doc.company)
		return ke_toan_mua.gan_doi_tac(cac_dong, tk, doc.get("supplier"))
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"vagabond: gan doi tac vao dong hang chua hoa don")
		return cac_dong


class PhieuNhapKho(PurchaseReceipt):
	"""Giữ nguyên mọi thứ của ERPNext, chỉ thêm đối tác vào dòng chờ hoá đơn."""

	def get_gl_entries(self, *a, **k):
		return _gan(self, super().get_gl_entries(*a, **k))


class HoaDonMua(PurchaseInvoice):
	"""Như trên, cho đường hoá đơn mua.

	Dòng Nợ tài khoản chờ của hoá đơn cũng phải có đối tác, nếu không thì
	sổ chi tiết công nợ chỉ thấy một nửa cặp bút toán: phiếu nhập ghi Có có
	tên nhà cung cấp, hoá đơn ghi Nợ lại trống tên.
	"""

	def get_gl_entries(self, *a, **k):
		return _gan(self, super().get_gl_entries(*a, **k))
