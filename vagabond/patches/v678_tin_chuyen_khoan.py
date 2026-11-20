"""v678: nhóm Zalo đang nhận tin "Khách gọi món tại bàn qua QR" được tích thêm tin
"Bàn đã chuyển khoản, bill tự chốt" (bh_ban_da_chuyen_khoan); nhóm đang nhận tin
hộp thư đối soát lỗi được tích thêm tin tệp đối soát đọc lỗi (ht_ds_tep_loi). Một nguồn:
kenh_zalo.TIN_MOC, tich_theo_moc. Nhóm để trống Tin nhận đang nhận mọi tin, không đổi.
Chạy lại không đổi gì."""
import frappe

TIN_MOI = ("bh_ban_da_chuyen_khoan", "ht_ds_tep_loi")


def execute():
	try:
		from vagabond import kenh_zalo

		kenh_zalo.tich_theo_moc(TIN_MOI)
		frappe.db.commit()
	except Exception:
		# Bản vá hỏng không được chặn cả lần migrate.
		frappe.log_error(frappe.get_traceback(), "patches: v678 tích tin bàn đã chuyển khoản")
