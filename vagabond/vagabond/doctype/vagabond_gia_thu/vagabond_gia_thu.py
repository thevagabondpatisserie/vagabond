"""Phiếu tính giá thử cho món R&D chưa bán (anh Việt 16/10/2026).

Chỉ để định giá: không tạo Item, không tạo BOM, không đụng kho hay sổ.
Giá vốn tính ở vagabond.gia_von_tam (tinh_thu, luu_thu).

Codex #486 P2: lưu thẳng trên Desk cũng phải tính lại giá vốn và giá đề xuất,
nên validate() gọi đúng một nguồn tính là gia_von_tam.tinh_lai_doc.
"""

from frappe.model.document import Document


class VagabondGiaThu(Document):
	def validate(self):
		from vagabond.gia_von_tam import tinh_lai_doc
		tinh_lai_doc(self)
