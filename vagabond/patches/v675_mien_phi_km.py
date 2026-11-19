"""v675 (Codex #594): gieo 7 km cho ô Miễn phí giao trong bán kính trên site đã
có Cài đặt từ trước. Chỉ ghi khi ô chưa có dòng nào; giá trị đã lưu giữ nguyên."""
import frappe


def execute():
	try:
		from vagabond import mien_phi_km

		mien_phi_km.gieo_mac_dinh()
	except Exception:
		# Bản vá hỏng không được chặn cả lần migrate.
		frappe.log_error(frappe.get_traceback(), "patches: v675 gieo ban kinh mien phi giao")
