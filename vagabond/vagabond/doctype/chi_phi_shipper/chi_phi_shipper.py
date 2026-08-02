"""Chi phi cua shipper: do xang, bao tri xe... shipper tu khai kem anh
hoa don (vd Petrolimex). Thu mua (Uyen) hoac ke toan (Dung) duyet roi
hoan ung; hoan ung xong ke toan tu lap Phieu chi ben Payment Entry.

Anh hoa don la CHUNG TU nen giu lai, khong nam trong dot don dep anh
giao hang 30 ngay.
"""

import frappe
from frappe.model.document import Document


class ChiPhiShipper(Document):
	def validate(self):
		if (self.so_tien or 0) <= 0:
			frappe.throw("Số tiền phải lớn hơn 0.")
		if self.trang_thai == "Từ chối" and not (self.ghi_chu_duyet or "").strip():
			frappe.throw("Từ chối thì ghi lý do để shipper biết đường bổ sung.")
