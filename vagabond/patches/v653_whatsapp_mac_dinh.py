"""v653: điền sẵn các ô WhatsApp đường phụ trong Vagabond Settings.

Chỉ điền ô đang trống; ô Phone Number ID đang là số điện thoại thì thay bằng mã
Meta cấp (anh Việt chọn A 12/11/2026). Không đụng token, PIN, App Secret,
Verify token: các ô bí mật anh Việt tự dán. Logic ở whatsapp.can_dien (thuần,
có ca kiểm)."""


def execute():
	import frappe

	from vagabond import whatsapp

	ds = list(whatsapp.MAC_DINH)
	hien = {k: frappe.db.get_single_value("Vagabond Settings", k) for k in ds}
	for k, v in whatsapp.can_dien(hien).items():
		frappe.db.set_single_value("Vagabond Settings", k, v)
