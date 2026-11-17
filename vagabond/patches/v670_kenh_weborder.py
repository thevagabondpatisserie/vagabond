"""v670 (anh Việt 17/11/2026): một chữ WEBORDER cho kênh khách đặt giao qua tab Tại quầy
trên web, ở mọi chỗ cài đặt. Ô Kênh của chương trình khuyến mãi và combo đang ghi "Web
giao" (nguồn phiếu cũ của kênh này) đổi thành WEBORDER, bỏ dòng trùng. Chỉ đổi cấu
hình, không đụng hoá đơn hay chứng từ đã lập. Chạy lại không đổi gì.
"""

CU = "Web giao"
MOI = "WEBORDER"
BANG = ("Vagabond CTKM", "Vagabond Combo")


def kenh_moi(kenh):
	"""THUẦN: ô Kênh mới, None nếu không đổi. Giữ thứ tự, bỏ dòng trùng."""
	dong = [x.strip() for x in str(kenh or "").split("\n") if x.strip()]
	if CU not in dong:
		return None
	ra = []
	for x in dong:
		x = MOI if x == CU else x
		if x not in ra:
			ra.append(x)
	return "\n".join(ra)


def execute():
	import frappe

	for dt in BANG:
		if not frappe.db.table_exists(dt) or not frappe.db.has_column(dt, "kenh"):
			continue
		for r in frappe.get_all(dt, filters={"kenh": ["like", "%" + CU + "%"]}, fields=["name", "kenh"], limit_page_length=0):
			moi = kenh_moi(r.get("kenh"))
			if moi is not None:
				frappe.db.set_value(dt, r["name"], "kenh", moi, update_modified=False)
	frappe.db.commit()
