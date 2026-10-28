"""v614: xếp hàng lượt tính nhóm khách đầu tiên ngay lúc deploy.

Phân hệ Khách hàng (CRM) đọc nhóm từ bảng Vagabond Ho So CRM, bảng này do
lượt đêm 02:30 dựng. Không có bản vá này thì từ lúc deploy tới 02:30 hôm sau
màn Nhóm khách trống trơn. Bản vá chỉ XẾP HÀNG một lượt nền (hàng long), không
chạy tại chỗ để Migrate không phải chờ 45.000 khách. Chạy lại không sao: lượt
tính là lũy đẳng và job_id chống xếp trùng.
"""

import frappe


def execute():
	try:
		from vagabond import crm

		crm.tinh_nhom_lan_dau()
	except Exception:
		# Xếp hàng hỏng không được chặn Migrate: lượt 02:30 vẫn tự dựng bảng.
		frappe.log_error(frappe.get_traceback(), "patches: v614 tính nhóm khách lần đầu")
