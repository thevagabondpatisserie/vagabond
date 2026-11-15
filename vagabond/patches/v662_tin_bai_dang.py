"""v662: tích hai tin Bài đăng mạng xã hội cho nhóm Zalo của Marketing.

Bài đăng mạng xã hội (bai_dang.py, anh Việt 15/11/2026) nhắn nhóm Marketing hai
tin: bài chờ Marketing duyệt (mkt_bai_cho_duyet) và đến giờ đăng tay
(mkt_bai_dang_den_gio). Nhóm đã tích tin Marketing ("Bánh mới chờ ảnh trên web"
hay "Báo cáo ưu đãi Zalo") được tích thêm hai tin này. Nhóm để trống Tin nhận
đang nhận mọi tin, không đổi. Chạy lại không đổi gì (lũy đẳng).
"""

MOI = ("mkt_bai_cho_duyet", "mkt_bai_dang_den_gio")
MOC = ("mkt_banh_cho_anh", "mkt_bao_cao_uu_dai")


def _tach(chuoi):
	return [m.strip() for m in str(chuoi or "").replace(";", ",").split(",") if m.strip()]


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm, None nếu không đổi."""
	cu = _tach(tin_nhan)
	if not cu or not any(m in cu for m in MOC):
		return None
	moi = list(cu) + [m for m in MOI if m not in cu]
	return ", ".join(moi) if moi != cu else None


def execute():
	import frappe
	from vagabond import kenh_zalo

	la = sorted(set(MOI) - set(kenh_zalo.TIN))
	if la:
		raise Exception("v662_tin_bai_dang: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
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
