"""v670 (PR #577 dựng lại trên main 669): gieo Sổ chủ đề cho Kho bản thảo và tích tin "Giám đốc duyệt hoặc trả lại bài
đăng" cho nhóm Zalo của Marketing.

Chủ đề: mười hai sổ Evernote anh Việt dùng (bai_dang.CHU_DE_GIEO), mỗi chủ đề có sẵn bốn
câu chân bài mẫu. Chỉ gieo khi bảng chủ đề còn trống, nên Marketing sửa, thêm chủ đề rồi
thì chạy lại không đổi gì.

Tin: nhóm đã tích tin "Bài đăng chờ Marketing duyệt" được tích thêm mkt_bai_gd_duyet.
Nhóm để trống Tin nhận đang nhận mọi tin, không đổi. Chạy lại không đổi gì.
"""

MOI = "mkt_bai_gd_duyet"
MOC = "mkt_bai_cho_duyet"


def _tach(chuoi):
	return [m.strip() for m in str(chuoi or "").replace(";", ",").split(",") if m.strip()]


def tin_them(tin_nhan):
	"""THUẦN: chuỗi Tin nhận mới của một nhóm, None nếu không đổi."""
	cu = _tach(tin_nhan)
	if not cu or MOC not in cu or MOI in cu:
		return None
	return ", ".join(cu + [MOI])


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
	if frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		rows = frappe.get_all("Vagabond Kenh Zalo",
			filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
			fields=["name", "tin_nhan"], order_by="idx asc", limit_page_length=0)
		for r in rows:
			moi = tin_them(r.get("tin_nhan"))
			if moi:
				frappe.db.set_value("Vagabond Kenh Zalo", r["name"], "tin_nhan", moi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
