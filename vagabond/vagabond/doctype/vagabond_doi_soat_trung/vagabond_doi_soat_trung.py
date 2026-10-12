"""#420 v583 đối soát vendor: sự kiện một báo cáo có nhưng đã nhận ở nguồn khác. Máy ghi, người chỉ xem; không xoá tay."""
import frappe
from frappe.model.document import Document


class VagabondDoiSoatTrung(Document):
	def validate(self):
		# Cùng luật với dòng đối soát (Codex #446 F1): chỉ cửa máy chủ được ghi.
		if not self.flags.ignore_permissions:
			frappe.throw("Dữ liệu đối soát do máy đọc từ tệp vendor; không sửa tay. Tải lại tệp hoặc bấm Đối chiếu lại.")

	def on_trash(self):
		frappe.throw("Giữ nguồn đối soát để tra cứu; không xoá.")
