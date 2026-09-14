"""#317: tên và số YCPS cho phiếu mới, không đổi tên phiếu đã có."""
import frappe


def execute():
	# Phiếu đang chờ giám đốc chưa chi tiền nên được chuyển an toàn sang đúng
	# bàn kế toán. Giữ nguyên phiếu đã chi, đã huỷ và mã phiếu lịch sử.
	for ten in frappe.get_all("Vagabond De Nghi Chi", filters={
		"trang_thai": "Cho giam doc",
		"loai_nghiep_vu": ["in", ["Chi phí", "Hoàn ứng"]],
	}, pluck="name", limit_page_length=0):
		ghi = "Tự chuyển từ Chờ giám đốc sang Chờ kế toán theo quy trình #317 ngày 14/09/2026."
		frappe.db.set_value("Vagabond De Nghi Chi", ten, "trang_thai", "Cho ke toan")
		frappe.get_doc("Vagabond De Nghi Chi", ten).add_comment("Info", ghi)
		# Cùng cơ chế giao việc với duyệt thường, nhưng không bắn chuông khi migrate.
		from vagabond.giao_viec import giao_vai
		from vagabond.de_nghi_chi import VAI_BUOC, TT_CHO_KE_TOAN
		kq = giao_vai("Vagabond De Nghi Chi", ten, sorted(VAI_BUOC[TT_CHO_KE_TOAN]), ghi, bao=0)
		if not kq.get("giao"):
			frappe.throw("Chưa giao được phiếu %s cho kế toán. Kiểm người giữ vai kế toán rồi chạy lại migrate." % ten)
	if not frappe.db.exists("DocType", "RnD Purchase Request"):
		return
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter
	for prop in ("options", "default"):
		make_property_setter("RnD Purchase Request", "naming_series", prop,
			"YCPS-.YY.-.MM.-.####", "Text" if prop == "options" else "Data")
	frappe.clear_cache(doctype="RnD Purchase Request")
