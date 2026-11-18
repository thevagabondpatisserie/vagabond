"""v674 Bảng kê chi phí trả trước (242). Mỗi chứng từ ghi Nợ 242 là một khoản.
Dòng do vagabond/chi_phi_242.py dựng từ sổ cái; kế toán khai cách phân bổ trên app
(màn Bảng kê 242) hoặc ngay trên form này. Hai đường dùng chung một bộ kiểm."""

import frappe
from frappe.model.document import Document


class VagabondKhoan242(Document):
	def validate(self):
		if self.flags.get("vgb_bang_ke"):
			return
		from vagabond import chi_phi_242 as C

		if self.trang_thai == C.TT_HUY and self.has_value_changed("so_ky"):
			frappe.throw("Chứng từ gốc của khoản này đã huỷ nên không khai được nữa.")
		if self.so_ky or self.ky_bat_dau:
			nhac = C.kiem_khai(self.so_ky, self.nguyen_gia, self.da_phan_bo_truoc, self.ky_bat_dau)
			if nhac:
				frappe.throw(" ".join(nhac))
		if self.bo_phan:
			C._kiem_cost_center(self.company, self.bo_phan)
		if self.tk_chi_phi:
			C._kiem_tk_chi_phi(self.company, self.tk_chi_phi)
		da = C.da_phan_bo_theo_khoan([self.name]).get(self.name, 0) if not self.is_new() else 0
		if C.BN.lam_tron_dong(self.da_phan_bo_truoc) + da > C.BN.lam_tron_dong(self.nguyen_gia):
			frappe.throw("Đã phân bổ trước cộng số đã phân bổ trên sổ vượt nguyên giá.")
		self.khai_boi = frappe.session.user
		self.khai_luc = frappe.utils.now_datetime()

	def on_trash(self):
		frappe.throw("Khoản trong Bảng kê 242 không xoá được. Khoản không phân bổ thì chọn Không phân bổ trên app.", frappe.PermissionError)
