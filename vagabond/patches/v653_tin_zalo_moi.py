"""v653: tích sẵn hai tin Zalo mới cho đúng nhóm.

Nhóm đã tích ô Tin nhận chỉ nhận đúng các tin đã tích, nên tin mới phải được tích
thì mới tới (cùng cách v619_tin_hao_hut):
  - nhóm đang nhận tin đơn web mới (bh_don_web_moi, nhóm Sales) tích thêm "Bánh có
    sẵn hôm nay, kèm ảnh bánh" (bh_banh_co_san), anh Việt 12/11/2026 23:23;
  - nhóm đang nhận tin gom yêu cầu mua (tm_gom_mua, nhóm Thu mua) tích thêm "Dự chi
    công nợ đợt 10 và 20 đã soạn" (tm_du_chi).
Không nhắm theo tên nhóm. Nhóm để trống Tin nhận đang nhận mọi tin. Không bỏ mã
nào đã tích, giữ thứ tự, chạy lại không đổi gì.
"""

THEO_MOC = (
	("bh_don_web_moi", "bh_banh_co_san"),
	("tm_gom_mua", "tm_du_chi"),
)


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm, None nếu không đổi."""
	from vagabond.patches.v619_tin_hao_hut import _tach

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
		raise Exception("v653_tin_zalo_moi: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
	if not frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		return
	rows = frappe.get_all("Vagabond Kenh Zalo",
		filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
		fields=["name", "tin_nhan"], order_by="idx asc", limit_page_length=0)
	for r in rows:
		moi = tin_them(r.get("tin_nhan"))
		if moi:
			frappe.db.set_value("Vagabond Kenh Zalo", r["name"], "tin_nhan", moi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
