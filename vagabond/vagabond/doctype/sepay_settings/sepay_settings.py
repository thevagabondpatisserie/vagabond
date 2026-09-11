import frappe
from frappe.model.document import Document


class SePaySettings(Document):
	def validate(self):
		"""Chặn JSON hỏng hoặc một số trỏ vào nhiều túi tiền trước khi lưu."""
		import json
		from vagabond.sepay import _chuan_hoa_ban_do, kiem_map_tai_khoan
		cu = self.get_doc_before_save()
		if cu and self.account_map == cu.account_map:
			return  # Map cũ hỏng không được chặn lưu token, mốc đồng bộ hoặc lỗi.

		try:
			ban_do = json.loads(self.account_map or "{}")
		except Exception:
			frappe.throw("Bản đồ tài khoản SePay phải là một JSON hợp lệ.")
		if not isinstance(ban_do, dict):
			frappe.throw("Bản đồ tài khoản SePay phải có dạng số tài khoản và Bank Account.")
		moi, xung_dot = _chuan_hoa_ban_do(ban_do)
		if xung_dot:
			frappe.throw(
				"Bản đồ SePay có cùng một số tài khoản trỏ vào nhiều Bank Account. "
				"Máy chưa lưu thay đổi. Hãy đối chiếu và chỉ giữ một dòng đúng."
			)

		try:
			truoc, _ = _chuan_hoa_ban_do(json.loads(cu.account_map or '{}')) if cu else ({},{})
		except (TypeError, ValueError, AttributeError):
			truoc = {}
		# Mọi tuyến mới/đổi đều qua hàng rào; tuyến cũ không chặn việc bảo trì.
		for so, tk in moi.items():
			if truoc.get(so) != tk:
				kiem_map_tai_khoan(so, tk)
