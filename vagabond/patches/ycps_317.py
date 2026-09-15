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
			from vagabond.giao_viec import go_giao
			go_giao("Vagabond De Nghi Chi", ten)
			frappe.get_doc("Vagabond De Nghi Chi", ten).add_comment("Info",
				"Chưa giao được việc cho kế toán. Phiếu vẫn ở Chờ kế toán; quản trị cần kiểm vai và giao lại việc.")
			frappe.log_error(title="YCPS317: cần giao lại việc", message="Phiếu %s đã chuyển Chờ kế toán nhưng chưa có người nhận việc." % ten)
	if not frappe.db.exists("DocType", "RnD Purchase Request"):
		return
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter
	truong = frappe.get_meta("RnD Purchase Request").get_field("naming_series")
	if not truong:
		return
	moi = "YCPS-.YY.-.MM.-.####"
	cu = [x.strip() for x in (truong.options or "").splitlines() if x.strip()]
	if moi not in cu:
		cu.append(moi)
	make_property_setter("RnD Purchase Request", "naming_series", "options", "\n".join(cu), "Text")
	make_property_setter("RnD Purchase Request", "naming_series", "default", moi, "Data")
	frappe.clear_cache(doctype="RnD Purchase Request")
