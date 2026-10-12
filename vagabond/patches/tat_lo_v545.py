"""v545: tắt quản lý theo lô cho mọi mã hàng (anh Việt chốt 30/09/2026).

Xem đầu tệp vagabond/tat_lo.py. Chỉ ghi ba cờ trên Item, không sửa chứng từ
nào đã ghi. Không bọc try: lỗi phải làm hỏng migrate.
"""


def execute():
	import frappe
	from vagabond import tat_lo

	cac_ma = tat_lo.tat_lo()
	tat_lo.ghi_note(cac_ma)
	frappe.db.commit()
