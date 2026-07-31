import frappe
from frappe.model.document import Document


class VagabondSettings(Document):
	def validate(self):
		if self.phu_thu and self.phu_thu < 0:
			frappe.throw("Phu thu khong duoc am")
		if not (self.kitchen_lat and self.kitchen_lng):
			frappe.throw("Phai co toa do bep thi moi hoi duoc phi giao")
