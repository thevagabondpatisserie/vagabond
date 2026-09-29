"""v536: sổ hoá đơn điện tử bán ra đối chiếu được với Fast.

Hai việc, đều CHỈ ĐIỀN Ô MỚI trên bản ghi cũ, không đổi số, ngày, tên, tiền,
trạng thái của bất kỳ tờ hay đơn nào (anh Việt duyệt 29/09/2026: điền ô mới
thì được, sửa dữ liệu đã ghi sổ thì không):

1. Ô Mã khách kế toán trên hoá đơn bán: dựng ô ngay trong patch (after_migrate
   chạy SAU patches, dựng ở đó thì lúc này chưa có cột) rồi điền hàng loạt
   theo dữ liệu sẵn có. Tờ chưa điền được (khách có MST mà chưa có mã) sẽ
   được điền ở lượt nạp danh mục Fast.
2. Ô Đơn ERP trên tờ m-invoice đầu ra đang trống: nối theo mã m-invoice ghi
   trên đơn, không có thì theo ký hiệu và số, không có nữa thì theo ô
   "Hoá đơn thay thế" kế toán ghi tay trên đơn gốc. Chỉ nối khi tìm ra đúng
   MỘT đơn đã ghi sổ; tờ nhiều ứng viên để trống cho kế toán nối tay.

Không bọc try (Codex #364 v2): lỗi phải làm hỏng migrate.
"""


def execute():
	import frappe
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from vagabond import ma_ke_toan
	from vagabond.doi_soat_hddt_ra import DT_TO, kh, so, tach_ghi_thay_the, ghi_don_erp_cua_to
	from vagabond.minvoice_chung_tu import LOAI_RA

	create_custom_fields(ma_ke_toan.TRUONG_MOI, update=True)
	frappe.db.updatedb("Sales Invoice")
	da_dien = ma_ke_toan.dien_ma_hang_loat()

	# Bench mới: MInvoice Invoice là doctype khai trên site, và ô Đơn ERP do
	# after_migrate dựng (chạy SAU patch). Thiếu một trong hai thì chưa có gì
	# để nối, lượt migrate sau sẽ nối tiếp qua nhịp kéo hoá đơn.
	if not frappe.db.exists("DocType", DT_TO) or not frappe.db.has_column(DT_TO, "vgb_don_erp"):
		frappe.db.commit()
		return
	# "is not set" thành ifnull(cột, '') = '': bắt cả NULL lẫn chuỗi rỗng.
	# ["in", ["", None]] chỉ bắt chuỗi rỗng, tờ cũ NULL bị bỏ sót (Codex #383 F3).
	to_ds = frappe.get_all(DT_TO, filters={"loai": LOAI_RA, "vgb_don_erp": ["is", "not set"]},
		fields=["name", "ky_hieu", "so_hd"], limit_page_length=0)
	if not to_ds:
		frappe.db.commit()
		return
	# Ba bảng tra, mỗi bảng dựng một lần từ đơn đã ghi sổ.
	theo_ma, theo_so, theo_thay = {}, {}, {}
	for r in frappe.get_all("Sales Invoice", filters={"docstatus": 1},
			or_filters=[["custom_minvoice_id", "is", "set"], ["custom_hddt_id", "is", "set"]],
			fields=["name", "custom_minvoice_id", "custom_hddt_id"], limit_page_length=0):
		for o in ("custom_minvoice_id", "custom_hddt_id"):
			m = str(r.get(o) or "").strip()
			if m:
				theo_ma.setdefault(m, set()).add(r["name"])
	for r in frappe.get_all("Sales Invoice", filters={"docstatus": 1, "custom_hddt_so": ["is", "set"]},
			fields=["name", "custom_hddt_so", "custom_hddt_ky_hieu"], limit_page_length=0):
		n = so(r.get("custom_hddt_so"))
		if n:
			theo_so.setdefault((kh(r.get("custom_hddt_ky_hieu")), n), set()).add(r["name"])
	for r in (frappe.get_all("Sales Invoice", filters={"docstatus": 1, "custom_hddt_thay_the": ["is", "set"]},
			fields=["name", "custom_hddt_thay_the"], limit_page_length=0)
			if frappe.db.has_column("Sales Invoice", "custom_hddt_thay_the") else []):
		cap = tach_ghi_thay_the(r.get("custom_hddt_thay_the"))
		if cap:
			theo_thay.setdefault(cap, set()).add(r["name"])

	noi = 0
	for t in to_ds:
		k, n = kh(t.get("ky_hieu")), so(t.get("so_hd"))
		ung = theo_ma.get(t["name"]) or theo_so.get((k, n)) or theo_thay.get((k, n)) or set()
		if len(ung) != 1:
			continue
		if ghi_don_erp_cua_to(t["name"], next(iter(ung)), "Máy nối lúc lên v536 theo dữ liệu đã có trên đơn."):
			noi += 1
	frappe.db.commit()
	frappe.logger("vagabond").info("v536: dien ma khach %s to; noi %s/%s to dau ra vao don" % (da_dien, noi, len(to_ds)))
