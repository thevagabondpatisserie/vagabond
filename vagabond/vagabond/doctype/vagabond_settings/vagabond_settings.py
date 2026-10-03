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
		# v559 Codex #417: mỗi nhóm Zalo một dòng, không trùng tên, không trùng mã
		# chat; Loại tin và Chủ đề chỉ nhận mã trong danh mục.
		from vagabond.kenh_zalo import kiem_bang_nhom
		loi = kiem_bang_nhom([r.as_dict() for r in (self.get("zalo_nhom") or [])])
		if loi:
			frappe.throw(loi)

	def on_update(self):
		from vagabond.tai_khoan_btp import khi_luu_cau_hinh
		khi_luu_cau_hinh(self)
