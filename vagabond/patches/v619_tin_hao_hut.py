"""v619: tích sẵn tin "Dữ liệu để tính hao hụt" cho nhóm kế toán.

Anh Việt 28/10/2026 duyệt tin tuần cho nhóm kế toán. Nhóm đã tích ô Tin nhận chỉ
nhận đúng các tin đã tích, nên tin mới phải được tích thì mới tới. Đọc site
28/10/2026: chỉ nhóm "VGB • BP • Kế toán" tích tin kiểm kê lệch (kt_kiem_ke_lech),
là tin cùng mảng của kế toán giá thành. Bản vá tích thêm tin mới cho đúng các nhóm
đã nhận tin đó; không nhắm theo tên nhóm vì anh đang đặt lại tên nhóm Zalo.

Nhóm để trống Tin nhận đang nhận mọi tin, không cần tích. Không bỏ mã nào anh đã
tích, giữ thứ tự cũ, chạy lại không đổi gì (lũy đẳng).
"""

MA_MOI = "kt_du_lieu_hao_hut"
MA_MOC = "kt_kiem_ke_lech"


def _tach(chuoi):
	return [m.strip() for m in str(chuoi or "").replace(";", ",").split(",") if m.strip()]


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm, None nếu không đổi."""
	cu = _tach(tin_nhan)
	if not cu or MA_MOC not in cu or MA_MOI in cu:
		return None
	return ", ".join(cu + [MA_MOI])


def execute():
	import frappe
	from vagabond import kenh_zalo

	if MA_MOI not in kenh_zalo.TIN:
		raise Exception("v619_tin_hao_hut: mã tin %s không có trong kenh_zalo.TIN" % MA_MOI)
	if not frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		return
	rows = frappe.get_all("Vagabond Kenh Zalo",
		filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
		fields=["name", "tin_nhan"], order_by="idx asc", limit_page_length=0)
	for r in rows:
		moi = tin_them(r.get("tin_nhan"))
		if moi:
			# Ghi thẳng ô con như v604, v611: không qua save() của Cài đặt.
			frappe.db.set_value("Vagabond Kenh Zalo", r["name"], "tin_nhan", moi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
