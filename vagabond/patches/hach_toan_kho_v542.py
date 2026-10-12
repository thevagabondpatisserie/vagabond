"""v542: hạch toán kho theo sơ đồ của Khải, bật từ 01/10/2026.

Anh Việt chốt 30/09/2026 (xem đầu tệp vagabond/hach_toan_kho.py):
- Dựng ô "Bán trừ kho", "Chưa trừ kho" trên hoá đơn bán và hai ô ngày bật
  trên Vagabond Settings.
- Site thật: đặt cả hai ngày bật là 01/10/2026 nếu đang trống. Bench thử và
  site khác KHÔNG tự bật: ca kiểm tự đặt ngày trong điểm lưu của nó.
- Gỡ 154 khỏi các kho Dở dang và bỏ loại Tồn kho của 154, để phiếu Sản xuất
  ghi được Có 154 và kế toán kết chuyển tay Nợ 154 / Có 621. Chỉ làm khi mọi
  kho đang trỏ vào 154 đều không còn tồn; còn tồn thì để nguyên và ghi Error
  Log, phiếu Sản xuất khi đó giữ luồng cũ (không chặn sản xuất).

Không sửa chứng từ nào đã ghi. Không bọc try toàn tệp: lỗi phải làm hỏng migrate.
"""

CTY_THAT = "CÔNG TY TNHH PATISSERIE VAGABOND"


def execute():
	import frappe
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from vagabond import hach_toan_kho as hk

	create_custom_fields(hk.TRUONG_MOI, update=True)
	frappe.db.updatedb("Sales Invoice")

	if frappe.db.exists("Company", CTY_THAT):
		for o in (hk.O_BAN_TU, hk.O_SX_TU):
			if not frappe.db.get_single_value("Vagabond Settings", o):
				frappe.db.set_single_value("Vagabond Settings", o, hk.NGAY_CAT)
		_go_154(frappe, CTY_THAT)
	frappe.db.commit()


def _go_154(frappe, cty):
	ds = frappe.get_all("Account", filters={"company": cty, "account_number": "154", "is_group": 0},
		fields=["name", "account_type"])
	if len(ds) != 1:
		return
	tk = ds[0].name
	kho_ds = frappe.get_all("Warehouse", filters={"account": tk}, pluck="name")
	con_ton = [k for k in kho_ds if frappe.db.sql(
		"select 1 from `tabBin` where warehouse=%s and (actual_qty != 0 or stock_value != 0) limit 1", k)]
	if con_ton:
		frappe.log_error("Kho còn tồn đang trỏ vào 154: %s. Chưa đổi loại tài khoản 154; phiếu Sản xuất "
			"giữ luồng cũ cho tới khi kế toán xử lý." % ", ".join(con_ton), "v542: chưa gỡ 154")
		return
	for k in kho_ds:
		frappe.db.set_value("Warehouse", k, "account", None, update_modified=False)
	if ds[0].account_type == "Stock":
		frappe.db.set_value("Account", tk, "account_type", "", update_modified=False)
	frappe.clear_cache()
