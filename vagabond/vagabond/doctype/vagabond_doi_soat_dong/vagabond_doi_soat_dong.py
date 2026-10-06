"""#420 v579: #420 v579 đối soát vendor: một sự kiện trong báo cáo vendor (đơn, phí, chuyến, giao dịch thẻ). Máy ghi, người chỉ xem; không xoá (QT-20)."""
import frappe
from frappe.model.document import Document


class VagabondDoiSoatDong(Document):
	def on_trash(self):
		frappe.throw("Giữ nguồn đối soát để tra cứu; không xoá.")
