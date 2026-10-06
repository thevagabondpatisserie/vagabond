"""#420 v579 đối soát vendor: một sự kiện trong báo cáo vendor (đơn, phí, chuyến, giao dịch thẻ). Máy ghi, người chỉ xem; không xoá (QT-20)."""
import frappe
from frappe.model.document import Document


class VagabondDoiSoatDong(Document):
	def validate(self):
		# Codex #446 F1: chỉ cửa máy chủ đối soát (ghi với ignore_permissions)
		# được tạo hay sửa. Lưu từ Desk hay REST thì chặn, kể cả quản trị,
		# vì số tiền và trạng thái nối phải đúng là số máy đọc từ tệp.
		if not self.flags.ignore_permissions:
			frappe.throw("Dữ liệu đối soát do máy đọc từ tệp vendor; không sửa tay. Tải lại tệp hoặc bấm Đối chiếu lại.")

	def on_trash(self):
		frappe.throw("Giữ nguồn đối soát để tra cứu; không xoá.")
