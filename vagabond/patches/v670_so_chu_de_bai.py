"""v670 (PR #577 dựng lại trên main 669): gieo Sổ chủ đề cho Kho bản thảo và tích tin "Giám đốc duyệt hoặc trả lại bài
đăng" cho nhóm Zalo của Marketing.

Chủ đề: mười hai sổ Evernote anh Việt dùng (bai_dang.CHU_DE_GIEO), mỗi chủ đề có sẵn bốn
câu chân bài mẫu. Chỉ gieo khi bảng chủ đề còn trống, nên Marketing sửa, thêm chủ đề rồi
thì chạy lại không đổi gì.

Tin: nhóm đã tích tin "Bài đăng chờ Marketing duyệt" được tích thêm mkt_bai_gd_duyet;
nhóm đã tích "Khách gọi món tại bàn qua QR" được tích thêm bh_weborder_moi (đơn giao của
quầy đã trả tiền, Minh Vũ 17/11). Một nguồn: kenh_zalo.TIN_MOC, tich_theo_moc.
Nhóm để trống Tin nhận đang nhận mọi tin, không đổi. Chạy lại không đổi gì.
"""

MOI = "mkt_bai_gd_duyet"
MOC = "mkt_bai_cho_duyet"
# v670 (Minh Vũ 17/11): tin đơn giao của quầy cho nhóm cửa hàng đang nhận tin gọi món tại bàn.
TIN_MOI = (MOI, "bh_weborder_moi")


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm cho tin giám đốc duyệt, None nếu không đổi."""
	from vagabond import kenh_zalo

	return kenh_zalo.tin_them_theo_moc(tin_nhan, MOI, MOC)


def execute():
	import frappe
	from vagabond import bai_dang, kenh_zalo

	if MOI not in kenh_zalo.TIN:
		raise Exception("v670_so_chu_de_bai: mã tin %s không có trong kenh_zalo.TIN" % MOI)
	if frappe.db.table_exists(bai_dang.DT_CHU_DE) and not frappe.db.count(bai_dang.DT_CHU_DE):
		for i, (bt, ten) in enumerate(bai_dang.CHU_DE_GIEO, 1):
			doc = frappe.get_doc({"doctype": bai_dang.DT_CHU_DE, "ten": ten, "bieu_tuong": bt, "thu_tu": i,
				"cta": "\n".join(bai_dang.CTA_GIEO)})
			doc.flags.vgb_bai_dang = True
			doc.insert(ignore_permissions=True)
	kenh_zalo.tich_theo_moc(TIN_MOI)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
