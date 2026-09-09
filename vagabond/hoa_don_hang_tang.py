"""#227: chỉ hoá đơn tặng mới ghi VAT, không sinh 511/131 theo giá thị trường.

ERPNext de59166: SalesInvoice.make_gl_entries gọi get_gl_entries rồi dùng
general_ledger.make_gl_entries/make_reverse_gl_entries. Giữ nguyên hai
đường ghi/đảo chuẩn, chỉ thay bản đồ sổ cái cho phiếu có dấu mới.
"""

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from erpnext.controllers.stock_controller import StockController
import frappe
from frappe.utils import flt


class HoaDonHangTang(SalesInvoice):
	def insert(self, *args, **kwargs):
		# Document.insert cũng chạy on_submit nếu client gửi docstatus=1.
		# Buộc tạo nháp trước để mọi đường ghi sổ đi qua điểm lưu bên dưới.
		if self.docstatus == 1:
			frappe.throw('Lưu hoá đơn nháp trước rồi ghi sổ. Không tạo thẳng hoá đơn đã ghi sổ.')
		return super().insert(*args, **kwargs)

	def _save(self, *args, **kwargs):
		# Document._save ghi parent trước on_submit; caller có thể bắt lỗi
		# rồi commit các đơn khác. Điểm lưu giữ SI/SLE/GL cùng thành bại.
		if self.docstatus != 1 or self.is_new():
			return super()._save(*args, **kwargs)
		cu = frappe.db.get_value('Sales Invoice', self.name, 'docstatus', for_update=True)
		if cu != 0:
			return super()._save(*args, **kwargs)
		moc = 'si_' + frappe.generate_hash(length=12)
		frappe.db.savepoint(moc)
		# Database.rollback(save_point=...) không dọn CallbackManager.
		# Không để job/chuông của lần submit hỏng chạy khi caller commit sau.
		hang_doi = [(getattr(frappe.db, k), getattr(frappe.db, k)._functions.copy())
			for k in ('before_commit', 'after_commit')]
		frappe.db._disable_transaction_control += 1
		try:
			return super()._save(*args, **kwargs)
		except Exception:
			frappe.db.rollback(save_point=moc)
			for bo, cu in hang_doi:
				bo._functions = cu
			self.reload()
			raise
		finally:
			frappe.db._disable_transaction_control -= 1

	def set_missing_values(self, for_validate=False):
		from vagabond.hang_tang_kho import kiem_lo_da_chon
		kiem_lo_da_chon(self)
		ket_qua = super().set_missing_values(for_validate=for_validate)
		from vagabond.hang_tang_kho import chuan_bi
		chuan_bi(self)
		return ket_qua

	def set_taxes_and_charges(self):
		from vagabond.hoa_don_thue_vnd import nap_mau_thue
		nap_mau_thue(self)
		return super().set_taxes_and_charges()

	def calculate_taxes_and_totals(self):
		from vagabond.hoa_don_thue_vnd import ap_dung, tinh
		if ap_dung(self):
			return tinh(self)
		if self.get("docstatus") == 0 or getattr(self, "_action", None) == "submit":
			self.vgb_thue_vnd = 0
		return super().calculate_taxes_and_totals()

	def get_gl_entries(self, inventory_account_map=None):
		if not self.get("vgb_tang_so_cai"):
			return super().get_gl_entries(inventory_account_map)
		# accounts/party.py validate_account_party_type: party chỉ được gắn
		# vào Receivable/Payable/Equity. Hai dòng này KHÔNG mang Customer.
		tien = flt(self.vgb_tang_tien_thue)
		dong = []
		if self.get('vgb_tang_kho_moi') and self.update_stock:
			# Chính hàm core mà SalesInvoice.make_item_gl_entries dùng cho
			# phần kho. Lấy theo SLE thực tế, không dùng giá bán làm giá vốn.
			dong = StockController.get_gl_entries(self, inventory_account_map)
		if tien:
			for tk, no, co in ((self.vgb_tang_tk_vat, tien, 0), (self.vgb_tang_tk_thue, 0, tien)):
				dong.append(self.get_gl_dict({"account": tk, "debit": no, "credit": co,
					"debit_in_account_currency": no, "credit_in_account_currency": co,
					"debit_in_transaction_currency": no, "credit_in_transaction_currency": co,
					"cost_center": self.cost_center, "remarks": "VAT hàng tặng không thu tiền"}, "VND"))
		self.set_transaction_currency_and_rate_in_gl_map(dong)
		return dong
