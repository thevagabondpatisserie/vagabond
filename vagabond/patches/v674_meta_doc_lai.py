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


def doc_o_tho():
	"""Giá trị thô của ô trong bảng Singles, None nếu chưa có dòng.

	Không dùng frappe.db.get_value("Singles", ...): câu đó tự thêm ORDER BY creation
	mà bảng Singles không có cột creation, migrate thật ném lỗi 1054 và Frappe Cloud
	khôi phục site (deploy 18/11/2026). Không dùng get_single_value vì nó đổi ô rỗng
	thành 0, mất phân biệt "chưa điền" với "đã chọn 0"."""
	import frappe

	r = frappe.db.sql("select value from `tabSingles` where doctype=%s and field=%s",
		("Vagabond Settings", "meta_ads_doc_lai"))
	return r[0][0] if r else None


def execute():
	import frappe

	moi = gia_tri_gieo(doc_o_tho())
	if moi is not None:
		# Không commit ở đây: trình chạy bản vá của Frappe tự commit sau mỗi bản vá.
		frappe.db.set_single_value("Vagabond Settings", "meta_ads_doc_lai", moi)
