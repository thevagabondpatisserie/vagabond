"""Van don giao banh: sales phan don, shipper bao ket qua kem anh.

Anh giao thanh cong luu private, cron xoa sau 30 ngay cho nhe he thong
(vagabond.van_don.don_dep_anh_giao). Khi shipper bam "Da giao", trang thai
day nguoc sang Pancake (status 3 da nhan) neu don co pancake_id.
"""

import frappe
from frappe.model.document import Document


class VanDon(Document):
	def validate(self):
		if self.trang_thai == "Không giao được" and not (self.ly_do_loi or "").strip():
			frappe.throw("Không giao được thì ghi rõ lý do giúp bếp và sales xử lý tiếp.")
