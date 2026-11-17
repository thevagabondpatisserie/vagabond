"""Mã đơn của hai kênh bán ở quầy (v670, anh Việt chốt 17/11/2026).

- WEBORDER, khách đặt giao qua tab Tại quầy trên web: WO-YYMMDD-5 số.
- O2O, khách gọi món tại bàn qua mã QR: O2O-YYMMDD-5 số (anh Việt chọn O2O cho
  khỏi nhìn nhầm với WO).

Ngày trong mã để dễ đọc; số 5 chữ số chạy tiếp cả tháng, sang tháng mới quay
về 00001 (bộ đếm theo khoá TIỀN TỐ-YYMM-). Đơn cũ giữ mã cũ (DW-YYMM-5 số, TQ-
YYMMDD-4 số), không đổi tên.
"""

TIEN_TO_WO = "WO"
TIEN_TO_O2O = "O2O"
SO_CHU_SO = 5


def khoa_dem(tien_to, luc):
	"""Khoá bộ đếm theo tháng, ví dụ "WO-2611-". THUẦN."""
	return "%s-%s-" % (tien_to, luc.strftime("%y%m"))


def ten_ma(tien_to, luc, so):
	"""Tên đơn, ví dụ WO-261117-00023. THUẦN."""
	return "%s-%s-%0*d" % (tien_to, luc.strftime("%y%m%d"), SO_CHU_SO, int(so))


def dat_ten(tien_to, luc=None):
	"""Lấy số kế tiếp của tháng (bảng Series của Frappe, khoá trong giao dịch
	lưu bản ghi) và dựng tên đơn."""
	from frappe.model.naming import getseries
	from frappe.utils import now_datetime

	luc = luc or now_datetime()
	return ten_ma(tien_to, luc, int(getseries(khoa_dem(tien_to, luc), SO_CHU_SO)))
