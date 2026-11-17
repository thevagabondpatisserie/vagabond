from frappe.model.document import Document


class VagabondMonDiKem(Document):
	def validate(self):
		from vagabond import goi_y_mua

		goi_y_mua.kiem_dong(self)
