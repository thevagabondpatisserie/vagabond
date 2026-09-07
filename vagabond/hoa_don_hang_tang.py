"""#227: chỉ hoá đơn tặng mới ghi VAT, không sinh 511/131 theo giá thị trường.

ERPNext de59166: SalesInvoice.make_gl_entries gọi get_gl_entries rồi dùng
general_ledger.make_gl_entries/make_reverse_gl_entries. Giữ nguyên hai
đường ghi/đảo chuẩn, chỉ thay bản đồ sổ cái cho phiếu có dấu mới.
"""

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import flt


class HoaDonHangTang(SalesInvoice):
	def get_gl_entries(self, inventory_account_map=None):
		if not self.get("vgb_tang_so_cai"):
			return super().get_gl_entries(inventory_account_map)
		# accounts/party.py validate_account_party_type: party chỉ được gắn
		# vào Receivable/Payable/Equity. Hai dòng này KHÔNG mang Customer.
		tien = flt(self.vgb_tang_tien_thue)
		dong = []
		if tien:
			for tk, no, co in ((self.vgb_tang_tk_vat, tien, 0), (self.vgb_tang_tk_thue, 0, tien)):
				dong.append(self.get_gl_dict({"account": tk, "debit": no, "credit": co,
					"debit_in_account_currency": no, "credit_in_account_currency": co,
					"debit_in_transaction_currency": no, "credit_in_transaction_currency": co,
					"cost_center": self.cost_center, "remarks": "VAT hàng tặng không thu tiền"}, "VND"))
		self.set_transaction_currency_and_rate_in_gl_map(dong)
		return dong
