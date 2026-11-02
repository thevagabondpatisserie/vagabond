"""v628: tích sẵn các tin Tài chính và tin kiểm kê sáng cho đúng nhóm Zalo.

Anh Việt 02/11/2026 duyệt 5 tin Tài chính và tin kiểm kê sáng cho bếp. Nhóm đã tích
ô Tin nhận chỉ nhận đúng các tin đã tích, nên tin mới phải được tích thì mới tới.
Đọc site 02/11/2026:
  - chỉ nhóm "VGB • BGĐ • Điều hành" tích báo cáo cuối ngày (bgd_bao_cao_ngay):
    tích thêm 4 tin Ban giám đốc và tin tiền ra chưa có chứng từ (mẫu 2 gửi cả
    Ban giám đốc);
  - chỉ nhóm "VGB • BP • Kế toán" tích tin hoá đơn đầu vào (hd_dau_vao): tích thêm
    tin tiền ra chưa có chứng từ, tin két lệch (mẫu 3 gửi cả kế toán), và tin
    tiền vào chưa gắn chứng từ của v611 (chưa nhóm nào tích nên chưa từng tới ai);
  - chỉ nhóm "VGB • VH • Sản xuất & Tồn kho" tích tin dữ liệu sản xuất của bếp
    (bep_du_lieu_hao_hut): tích thêm tin kiểm kê sáng.
Không nhắm theo tên nhóm vì anh đang đặt lại tên nhóm Zalo.

Nhóm để trống Tin nhận đang nhận mọi tin, không cần tích. Không bỏ mã nào anh đã
tích, giữ thứ tự cũ, chạy lại không đổi gì (lũy đẳng).
"""

# Mã mốc (nhóm đã tích) -> mã mới tích thêm.
THEO_MOC = (
	("bgd_bao_cao_ngay", "bgd_tien_cuoi_ngay"),
	("bgd_bao_cao_ngay", "bgd_ket_lech"),
	("bgd_bao_cao_ngay", "bgd_tien_tuan"),
	("bgd_bao_cao_ngay", "bgd_lai_lo_thang"),
	("bgd_bao_cao_ngay", "kt_tien_ra_chua_gan"),
	("hd_dau_vao", "kt_tien_ra_chua_gan"),
	# Tin tiền VÀO chưa gắn (v611, anh duyệt cho kế toán 25/10) chưa nhóm nào tích nên
	# chưa từng tới ai (site 02/11/2026); tích luôn cùng chiều ngược của nó.
	("hd_dau_vao", "kt_tien_chua_gan"),
	("hd_dau_vao", "bgd_ket_lech"),
	("bep_du_lieu_hao_hut", "bep_kiem_ke_sang"),
	# Quỹ tiền mặt công ty: lệch quá 2 triệu tới Ban giám đốc, nộp ngân hàng chưa về tới kế toán.
	("bgd_bao_cao_ngay", "bgd_kiem_quy_lech"),
	("hd_dau_vao", "kt_nop_nh_chua_khop"),
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
		raise Exception("v628_tin_tai_chinh: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
	if not frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		return
	rows = frappe.get_all("Vagabond Kenh Zalo",
		filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
		fields=["name", "tin_nhan"], order_by="idx asc", limit_page_length=0)
	for r in rows:
		moi = tin_them(r.get("tin_nhan"))
		if moi:
			# Ghi thẳng ô con như v604, v611, v619: không qua save() của Cài đặt.
			frappe.db.set_value("Vagabond Kenh Zalo", r["name"], "tin_nhan", moi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
