"""Phiếu tính giá thử cho món R&D chưa bán (anh Việt 16/10/2026).

Chỉ để định giá: không tạo Item, không tạo BOM, không đụng kho hay sổ.
Giá vốn tính ở vagabond.gia_von_tam (tinh_thu, luu_thu).
"""

from frappe.model.document import Document


class VagabondGiaThu(Document):
	pass
