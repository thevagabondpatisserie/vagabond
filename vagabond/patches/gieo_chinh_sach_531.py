"""v531: gieo lại bản nháp ba trang chính sách của #367.

Lúc deploy v529 (27/09/2026) patch don_web_367 gieo hỏng: gieo_chinh_sach
dựng bản ghi bằng get_doc(dict) nên is_new() trả False và save() nổ
DoesNotExistError. Site vẫn lên (patch nuốt lỗi, ghi Error Log). v531 sửa
gieo_chinh_sach, patch này chạy lại đúng bước gieo. Chỉ điền chỗ còn trống,
trang nào đã có trong nháp thì giữ nguyên, trang công khai vẫn 404 cho tới
khi marketing bật hiện và xuất bản.
"""

import frappe


def execute():
	try:
		from vagabond import noi_dung_web

		noi_dung_web.gieo_tu_tep()
	except Exception:
		frappe.log_error(title="v531: chua gieo lai duoc nhap chinh sach", message=frappe.get_traceback())
