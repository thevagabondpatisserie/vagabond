"""v646: tích tin "Tin Zalo cho khách đang dừng vì lệch mẫu" cho nhóm Marketing.

Minh Vũ báo 09/11/2026: gửi thử tin cảm ơn bị Zalo từ chối (-1124, ô tiền sai định
dạng); trong ngày 20 khách không nhận được tin mà không ai được báo. Từ v646 lỗi dữ
liệu lệch mẫu dừng lượt, để tin chờ và báo Marketing (mã tin mkt_zalo_mau_loi).

Nhóm đã tích "Báo cáo ưu đãi Zalo" (nhóm Marketing, v645) được tích thêm tin này.
Nhóm để trống Tin nhận đang nhận mọi tin. Chạy lại không đổi gì (lũy đẳng).
"""

THEO_MOC = (("mkt_bao_cao_uu_dai", "mkt_zalo_mau_loi"),)


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
		raise Exception("v646_tin_zalo_mau_loi: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
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
