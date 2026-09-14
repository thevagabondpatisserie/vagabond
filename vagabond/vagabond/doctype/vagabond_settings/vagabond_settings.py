import frappe
from frappe.model.document import Document


class VagabondSettings(Document):
	def validate(self):
		if self.phu_thu and self.phu_thu < 0:
			frappe.throw("Phu thu khong duoc am")
		if not (self.kitchen_lat and self.kitchen_lng):
			frappe.throw("Phai co toa do bep thi moi hoi duoc phi giao")
		# #307: hai ô tài khoản tồn kho BTP phải là tài khoản kho hợp lệ.
		from vagabond.tai_khoan_btp import kiem_o_cau_hinh
		kiem_o_cau_hinh(self)

	def on_update(self):
		from vagabond.tai_khoan_btp import khi_luu_cau_hinh
		khi_luu_cau_hinh(self)
