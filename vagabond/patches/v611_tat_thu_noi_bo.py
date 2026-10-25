"""v611: tắt thư báo nội bộ còn sót, tích sẵn tin Zalo mới cho nhóm đã nhận tin đặt bàn.

Anh Việt 25/10/2026: "Em tắt luôn tính năng gửi email YCSX qua mail nhé. Anh
muốn tắt hết việc gửi mail để tránh rác mail và thực ra nhân viên cũng không đọc
mail bao giờ." Thư cho KHÁCH và NHÀ CUNG CẤP (hoá đơn, báo giá, hợp đồng, xác
nhận đặt bàn, đơn mua, đặt lại mật khẩu) giữ nguyên; bản vá này chỉ tắt thư báo
nhân viên.

Đọc trên site thật 25/10/2026 (Email Queue từ 23/10), các nguồn thư nội bộ còn
chạy đều là cấu hình trong cơ sở dữ liệu, không nằm trong fixtures:
  - Notification kênh Email: báo bếp khi có YCSX, báo thủ kho khi có YCDC, báo
    Purchasing khi có YCMH, thư nhận hàng của Material Request, thư năm tài chính.
  - Auto Email Report hạn dùng sắp hết (hai bản, gửi hằng tuần).
Thay vào đó là tin Zalo bep_ycsx_moi, bep_ycsx_huy, bep_ycsx_ngay_mai,
kho_ycdc_moi, kho_ycdc_treo, tm_yeu_cau_mua (đã có từ v604); anh tích cho nhóm.

Bản vá chỉ ĐỔI CỜ BẬT (enabled = 0), không xoá: muốn bật lại thì mở bản ghi trên
Desk tích lại. "Phiếu sản xuất - chuông trong app" là chuông trong app (System
Notification), không phải thư, nên giữ. Chạy lại không đổi gì thêm (lũy đẳng).

Tin Zalo: nhóm nào đã tích tin đặt bàn mới (bh_dat_ban) thì tích thêm ba tin
đặt bàn của v611; nhóm Bán hàng & Sales tích thêm tin thông tin xuất hoá đơn sai
(anh Việt chọn nhóm này 25/10/2026). Nhóm để trống Tin nhận đang nhận mọi tin,
không cần tích. Không bỏ mã nào anh đã tích.
"""

import unicodedata

THONG_BAO_TAT = (
	"Phiếu sản xuất - báo bếp",
	"Chuyển hàng nội bộ - báo Thủ kho",
	"Đặt mua hàng mới - báo Purchasing",
	"Material Request Receipt Notification",
	"Notification for new fiscal year",
)
BAO_CAO_TAT = ("HSD sắp hết hạn", "HSD sắp hết hạn-1")
TIN_DAT_BAN = ("bh_dat_ban_xac_nhan", "bh_dat_ban_huy", "bh_dat_ban_sap_toi")
TIN_SALES = ("bh_thong_tin_hd_sai",)


def _khong_dau(s):
	s = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
	return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def _tach(chuoi):
	return [m.strip() for m in str(chuoi or "").replace(";", ",").split(",") if m.strip()]


def thong_bao_can_tat(ds):
	"""THUẦN: tên các Notification kênh Email trong danh sách tắt mà còn đang bật."""
	return [r["name"] for r in ds or [] if r.get("name") in THONG_BAO_TAT
		and int(r.get("enabled") or 0) and str(r.get("channel") or "Email") == "Email"]


def tin_them(ten_nhom, tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới cho một nhóm, None nếu không đổi.

	Ô trống nghĩa là nhóm đang nhận mọi tin nên để nguyên. Giữ đúng thứ tự mã cũ,
	chỉ nối mã mới vào cuối, không lặp mã."""
	cu = _tach(tin_nhan)
	if not cu:
		return None
	moi = list(cu)
	if "bh_dat_ban" in cu:
		moi += [m for m in TIN_DAT_BAN if m not in moi]
	t = _khong_dau(ten_nhom)
	if "sales" in t or "ban hang" in t:
		moi += [m for m in TIN_SALES if m not in moi]
	return ", ".join(moi) if moi != cu else None


def execute():
	import frappe
	from vagabond import kenh_zalo

	la = sorted(set(TIN_DAT_BAN + TIN_SALES) - set(kenh_zalo.TIN))
	if la:
		raise Exception("v611_tat_thu_noi_bo: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))

	ds = frappe.get_all("Notification", filters={"name": ["in", list(THONG_BAO_TAT)]},
		fields=["name", "enabled", "channel"], limit_page_length=0)
	for ten in thong_bao_can_tat(ds):
		frappe.db.set_value("Notification", ten, "enabled", 0, update_modified=False)
	if frappe.db.exists("DocType", "Auto Email Report"):
		for ten in frappe.get_all("Auto Email Report", filters={"name": ["in", list(BAO_CAO_TAT)], "enabled": 1},
				pluck="name"):
			frappe.db.set_value("Auto Email Report", ten, "enabled", 0, update_modified=False)

	if frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		rows = frappe.get_all("Vagabond Kenh Zalo",
			filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
			fields=["name", "ten_nhom", "tin_nhan"], order_by="idx asc", limit_page_length=0)
		for r in rows:
			moi = tin_them(r.get("ten_nhom"), r.get("tin_nhan"))
			if moi:
				# Ghi thẳng ô con như v604: không qua save() của Cài đặt.
				frappe.db.set_value("Vagabond Kenh Zalo", r["name"], "tin_nhan", moi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Notification")
	frappe.clear_cache(doctype="Vagabond Settings")
