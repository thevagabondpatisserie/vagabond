"""v674 (anh Việt 18/11/2026): gieo một lần ô "Đọc lại bao nhiêu ngày gần nhất" của
phần đọc chi phí quảng cáo Meta là 3 ngày, CHỈ khi ô còn trống. Ô đã có số, kể cả
0 (chỉ đọc hôm qua), thì giữ nguyên. Công tắc đọc vẫn tắt: giám đốc tự dán mã
truy cập và bật trong Cài đặt. Chạy lại không đổi gì.
"""

MAC_DINH = 3


def gia_tri_gieo(hien_tai):
	"""THUẦN: số cần gieo, None nếu giữ nguyên. 0 là giá trị người dùng đã chọn."""
	if hien_tai is None or str(hien_tai).strip() == "":
		return MAC_DINH
	return None


def execute():
	import frappe

	hien = frappe.db.get_value("Singles", {"doctype": "Vagabond Settings", "field": "meta_ads_doc_lai"}, "value")
	moi = gia_tri_gieo(hien)
	if moi is not None:
		frappe.db.set_single_value("Vagabond Settings", "meta_ads_doc_lai", moi)
		frappe.db.commit()
