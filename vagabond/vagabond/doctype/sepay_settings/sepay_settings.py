import frappe
from frappe.model.document import Document


class SePaySettings(Document):
	def validate(self):
		"""Chặn JSON hỏng hoặc một số trỏ vào nhiều túi tiền trước khi lưu."""
		import json
		from vagabond.sepay import _chuan_hoa_ban_do, kiem_map_tai_khoan

		try:
			ban_do = json.loads(self.account_map or "{}")
		except Exception:
			frappe.throw("Bản đồ tài khoản SePay phải là một JSON hợp lệ.")
		if not isinstance(ban_do, dict):
			frappe.throw("Bản đồ tài khoản SePay phải có dạng số tài khoản và Bank Account.")
		_x, xung_dot = _chuan_hoa_ban_do(ban_do)
		if xung_dot:
			frappe.throw(
				"Bản đồ SePay có cùng một số tài khoản trỏ vào nhiều Bank Account. "
				"Máy chưa lưu thay đổi. Hãy đối chiếu và chỉ giữ một dòng đúng."
			)

		# Không để Desk bỏ qua kiểm số, tài khoản ngưng dùng hoặc túi tiền cá nhân.
		for so, tk in ban_do.items():
			kiem_map_tai_khoan(so, tk)
