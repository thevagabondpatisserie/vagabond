"""v653: điền sẵn ô Hộp thư hoá đơn nhà cung cấp (hoadon@) khi đang trống.

Không đụng mật khẩu (anh Việt tự dán). Chạy lại không đổi gì."""

MAC_DINH = {"hd_thu_dia_chi": "hoadon@thevagabondpatisserie.com", "hd_thu_may_chu": "pro10.emailserver.vn",
	"hd_thu_cong": 993, "hd_thu_bat": 1}


def can_dien(hien):
	"""THUẦN: ô trống nhận mặc định."""
	return {k: v for k, v in MAC_DINH.items() if not str((hien or {}).get(k) or "").strip()}


def execute():
	import frappe

	hien = {k: frappe.db.get_single_value("Vagabond Settings", k) for k in MAC_DINH}
	# Ô Bật mới thêm đọc ra None: lần đầu nhận 1. Ai đã tắt (0) thì giữ.
	for k, v in can_dien(hien).items():
		if k == "hd_thu_bat" and hien.get(k) is not None:
			continue
		frappe.db.set_single_value("Vagabond Settings", k, v)
