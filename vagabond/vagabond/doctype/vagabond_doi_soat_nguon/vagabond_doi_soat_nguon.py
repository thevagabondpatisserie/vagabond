"""#420 v579: #420 v579 đối soát vendor: một tệp báo cáo nhận vào. Máy ghi, người chỉ xem; không xoá (QT-20)."""
import frappe
from frappe.model.document import Document


class VagabondDoiSoatNguon(Document):
	def on_trash(self):
		frappe.throw("Giữ nguồn đối soát để tra cứu; không xoá.")
