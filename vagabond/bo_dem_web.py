"""Bộ đệm ngắn cho hàm trang khách gọi theo nhịp (v693, 26/11/2026).

Sự cố 25/11/2026: site chạm trần thời gian máy chủ của gói Frappe Cloud
(14.400 giây mỗi ngày) và trả trang "Daily usage limit reached" cho tới 07:00
sáng 26/11. Hai hàm khách gọi mỗi phút trên MỌI trang đặt bánh đang mở chiếm
gần 8.600 giây trong ngày: kiem_kho.con_tren_quay_web (12.205 lượt, 6.024 giây)
và kiem_banh.co_the_ban_hom_nay (12.202 lượt, 2.521 giây). Kết quả của hai hàm
giống nhau cho mọi khách (không tham số, không theo phiên), nên mỗi nhịp chỉ
cần tính một lần cho cả site.

Chỉ đệm khi đang phục vụ một request web. Gọi trong việc nền, ca bench hay
hàm nội bộ không có request thì luôn tính lại, để số đọc ngay sau khi ghi là
số mới.
"""

import frappe

GIAY_DEM = 30


def khoa_dem(ten, ngay):
	"""THUẦN. Khoá Redis của một hàm trong một ngày (đổi ngày là khoá mới)."""
	return "vgb_bo_dem_web:%s:%s" % (ten, ngay)


def qua_bo_dem(ten, tinh, giay=GIAY_DEM):
	"""Trả kết quả tinh() đã đệm tối đa `giay` giây cho request web.

	Redis lỗi thì vẫn tính và trả bình thường: bộ đệm hỏng không được làm
	trang khách hỏng."""
	if getattr(frappe.local, "request", None) is None:
		return tinh()
	from frappe.utils import nowdate

	khoa = khoa_dem(ten, nowdate())
	try:
		co = frappe.cache().get_value(khoa)
	except Exception:
		co = None
	if co is not None:
		return co
	ra = tinh()
	try:
		frappe.cache().set_value(khoa, ra, expires_in_sec=giay)
	except Exception:
		pass
	return ra
