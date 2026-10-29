"""v619: tích sẵn hai tin dữ liệu hao hụt cho đúng nhóm Zalo.

Anh Việt 28/10/2026 duyệt tin tuần cho nhóm kế toán và chọn gửi thêm tin việc cần
làm cho từng bếp. Nhóm đã tích ô Tin nhận chỉ nhận đúng các tin đã tích, nên tin
mới phải được tích thì mới tới. Đọc site 28/10/2026:
  - chỉ nhóm "VGB • BP • Kế toán" tích tin kiểm kê lệch (kt_kiem_ke_lech), là tin
    cùng mảng của kế toán giá thành: tích thêm kt_du_lieu_hao_hut;
  - chỉ nhóm "VGB • VH • Sản xuất & Tồn kho" tích tin lệnh sản xuất quá ngày
    (bep_lenh_chua_xong): tích thêm bep_du_lieu_hao_hut.
Không nhắm theo tên nhóm vì anh đang đặt lại tên nhóm Zalo.

Nhóm để trống Tin nhận đang nhận mọi tin, không cần tích. Không bỏ mã nào anh đã
tích, giữ thứ tự cũ, chạy lại không đổi gì (lũy đẳng).
"""

# Mã mốc (nhóm đã tích) -> mã mới tích thêm.
THEO_MOC = (
	("kt_kiem_ke_lech", "kt_du_lieu_hao_hut"),
	("bep_lenh_chua_xong", "bep_du_lieu_hao_hut"),
)


def _tach(chuoi):
	return [m.strip() for m in str(chuoi or "").replace(";", ",").split(",") if m.strip()]


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm, None nếu không đổi."""
	cu = _tach(tin_nhan)
	if not cu:
		return None
	moi = list(cu)
	for moc, ma in THEO_MOC:
		if moc in cu and ma not in moi:
			moi.append(ma)
	return ", ".join(moi) if moi != cu else None


def execute():
	import frappe
	from vagabond import kenh_zalo

	la = sorted({ma for _, ma in THEO_MOC} - set(kenh_zalo.TIN))
	if la:
		raise Exception("v619_tin_hao_hut: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
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
