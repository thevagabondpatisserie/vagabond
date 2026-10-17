"""Phiếu tính giá thử cho món R&D chưa bán (anh Việt 16/10/2026).

Chỉ để định giá: không tạo Item, không tạo BOM, không đụng kho hay sổ.
Giá vốn tính ở vagabond.gia_von_tam (tinh_thu, luu_thu).

Codex #486 P2: lưu thẳng trên Desk cũng phải tính lại giá vốn và giá đề xuất,
nên validate() đi qua đúng một chỗ là gia_von_tam.kiem_khi_luu: phiếu đã bỏ
không sửa được, bỏ phiếu giữ nguyên ảnh chụp giá, còn lại tính lại (v2).
"""

from frappe.model.document import Document


class VagabondGiaThu(Document):
	def validate(self):
		from vagabond.gia_von_tam import kiem_khi_luu
		kiem_khi_luu(self)

	def on_trash(self):
		# QT-20, Codex #486 v4: không xoá cứng phiếu thử, kể cả System Manager.
		import frappe
		frappe.throw("Không xoá phiếu tính giá thử. Bấm Bỏ phiếu trên app: phiếu ẩn khỏi danh sách, vẫn giữ để tra lại.")
