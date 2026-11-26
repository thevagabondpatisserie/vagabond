"""Bộ đệm ngắn cho hàm trang khách gọi theo nhịp (v693, 26/11/2026).

Sự cố 25/11/2026: site chạm trần thời gian máy chủ của gói Frappe Cloud
(14.400 giây mỗi ngày) và trả trang "Daily usage limit reached" tới 07:00
sáng 26/11. Hai hàm khách gọi mỗi phút trên MỌI trang đặt bánh đang mở chiếm
gần 8.600 giây trong ngày: kiem_kho.con_tren_quay_web (12.205 lượt, 6.024 giây)
và kiem_banh.co_the_ban_hom_nay (12.202 lượt, 2.521 giây).

Hai hàm không nhận tham số, không đọc phiên, khách hay trình duyệt nào cũng
nhận cùng một kết quả (mọi điểm bán nằm chung trong một kết quả). Nên mỗi
nhịp chỉ cần tính một lần cho cả site. Bộ đệm CHỈ dùng cho số hiển thị; tạo
đơn kiểm tồn, giá bằng hàm riêng (ton_don_web, giu_ton_web, don_hang) không
đi qua đây.

Cách đệm:
- bản còn tươi (dưới GIAY_DEM) thì trả ngay;
- bản đã cũ: request nào giữ được khoá thì tính lại, các request khác trả
  bản cũ trong lúc chờ, không để cả loạt cùng tính một lúc;
- chưa có bản nào (đầu ngày) mà khoá đang bị giữ: chờ tối đa CHO_LANH giây
  đọc bản vừa tính, hết giờ thì tự tính;
- Redis lỗi: tính trực tiếp như khi chưa có bộ đệm;
- gọi trong việc nền, ca bench, hàm nội bộ không có request: luôn tính lại.
"""

import time

import frappe

GIAY_DEM = 30      # tuổi tối đa của bản trả ngay
GIAY_GIU = 300     # Redis giữ bản cũ để phục vụ trong lúc một request tính lại
GIAY_KHOA = 15     # khoá tính lại tự nhả nếu request giữ khoá chết giữa chừng
CHO_LANH = 2.0     # chờ tối đa khi chưa có bản nào và request khác đang tính
BUOC_CHO = 0.1


def khoa_dem(ten, ngay):
	"""THUẦN. Khoá Redis của một hàm trong một ngày (đổi ngày là khoá mới)."""
	return "vgb_bo_dem_web:%s:%s" % (ten, ngay)


def _doc(c, khoa):
	try:
		# expires=True: đọc thẳng Redis, không dùng bản nhớ tạm trong request
		# (bản nhớ tạm giữ cả None, vòng chờ sẽ không bao giờ thấy bản mới).
		goi = c.get_value(khoa, expires=True)
	except Exception:
		return None, False
	if isinstance(goi, dict) and "luc" in goi and "gt" in goi:
		return goi, True
	return None, True


def _ghi(c, khoa, gt, luc):
	try:
		c.set_value(khoa, {"luc": luc, "gt": gt}, expires_in_sec=GIAY_GIU)
	except Exception:
		pass


def _giu_khoa(c, khoa):
	"""True khi request này được quyền tính lại. Redis lỗi thì cho tính."""
	try:
		return bool(c.set(c.make_key(khoa + ":dang_tinh"), 1, nx=True, ex=GIAY_KHOA))
	except Exception:
		return True


def _tha_khoa(c, khoa):
	try:
		c.delete(c.make_key(khoa + ":dang_tinh"))
	except Exception:
		pass


def qua_bo_dem(ten, tinh, giay=GIAY_DEM, bay=None, ngu=None):
	"""Trả kết quả tinh() đã đệm cho request web. bay, ngu: đồng hồ và hàm
	ngủ, chỉ ca kiểm truyền vào."""
	if getattr(frappe.local, "request", None) is None:
		return tinh()
	bay = bay or time.time
	ngu = ngu or time.sleep
	from frappe.utils import nowdate

	khoa = khoa_dem(ten, nowdate())
	try:
		c = frappe.cache()
	except Exception:
		return tinh()
	goi, redis_song = _doc(c, khoa)
	if not redis_song:
		return tinh()
	if goi and bay() - goi["luc"] < giay:
		return goi["gt"]
	if _giu_khoa(c, khoa):
		try:
			# Codex #622: giữa lúc đọc bản cũ và lúc giành khoá, request khác có thể
			# vừa tính xong, ghi bản mới và nhả khoá. Đọc lại SAU khoá; còn tươi thì
			# dùng luôn, không tính lần nữa.
			moi, _ = _doc(c, khoa)
			if moi and bay() - moi["luc"] < giay:
				return moi["gt"]
			ra = tinh()
			_ghi(c, khoa, ra, bay())
			return ra
		finally:
			_tha_khoa(c, khoa)
	if goi:
		return goi["gt"]
	da_cho = 0.0
	while da_cho < CHO_LANH:
		ngu(BUOC_CHO)
		da_cho += BUOC_CHO
		goi, _ = _doc(c, khoa)
		if goi:
			return goi["gt"]
	return tinh()
