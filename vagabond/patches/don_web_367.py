"""#367: gieo cấu hình mặc định và bản nháp ba trang chính sách. Chạy MỘT lần.

Hai việc, đều CHỈ ĐIỀN chỗ còn trống, không bao giờ đè lên thứ đã có:

1. Ô mới của Vagabond Settings. Frappe không tự điền giá trị mặc định cho ô
   mới của doctype đơn (Single): `get_single_value` trả None khi bảng
   Singles chưa có dòng. Mà anh Việt chốt "ô trống hoặc 0 là tắt miễn phí
   giao", nên nếu không gieo thì ngay sau deploy miễn phí giao đang TẮT,
   trái với mức 1.000.000 đã chốt. Gieo khi chưa có dòng nào, để sau này
   anh xoá trống thì máy hiểu đúng là tắt.
2. Bản nháp ba trang chính sách anh Việt đã duyệt ngày 25/09/2026 (nguyên
   văn trong vagabond/du_lieu/chinh_sach/). Chỉ vào BẢN NHÁP, trang công khai
   vẫn 404 cho tới khi marketing điền các chỗ trong ngoặc vuông, bật hiện
   và bấm Xuất bản.
"""

import io
import os

import frappe

MAC_DINH_SETTINGS = {
	"mien_phi_giao_tu": 1000000,
	"web_dien_thoai": "0931 224 334",
	"web_messenger": "https://m.me/thevagabond.saigon",
	"web_instagram": "https://instagram.com/thevagabond.patisserie",
	"web_tiktok": "https://www.tiktok.com/@thevagabond.patisserie",
}


def _chua_co_dong(ten):
	return not frappe.db.sql(
		"select 1 from `tabSingles` where doctype=%s and field=%s limit 1", ("Vagabond Settings", ten))


def execute():
	# Patch hong KHONG duoc chan ca lan migrate (cung luat voi
	# dong_bo_cau_truc): ghi Error Log de nguoi sau gieo tay, site van len.
	try:
		for ten, gia_tri in MAC_DINH_SETTINGS.items():
			if _chua_co_dong(ten):
				frappe.db.set_single_value("Vagabond Settings", ten, gia_tri)
	except Exception:
		frappe.log_error(title="#367: chua gieo duoc cau hinh trang dat banh", message=frappe.get_traceback())

	try:
		from vagabond import noi_dung_web

		thu_muc = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "du_lieu", "chinh_sach")
		nhap = {}
		for khoa in noi_dung_web.CHINH_SACH:
			with io.open(os.path.join(thu_muc, khoa + ".md"), encoding="utf-8") as f:
				nhap[khoa] = f.read().strip() + "\n"
		noi_dung_web.gieo_chinh_sach(nhap)
	except Exception:
		frappe.log_error(title="#367: chua gieo duoc nhap chinh sach", message=frappe.get_traceback())
