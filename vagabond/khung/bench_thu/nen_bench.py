"""Dựng dữ liệu nền TỐI THIỂU cho một bench thử trống, để chạy được
`vagabond.khung.kiem_that.cua.chay` và các kịch bản giao dịch thật.

CHỈ chạy trên bench thử. Tuyệt đối không chạy trên site thật: nó tạo
Company, tài khoản, doctype site-only và custom field theo bản mô phỏng
của site. Có khoá: chỉ chạy khi site_config có `vagabond_bench_thu: 1`.

Vì sao tệp này nằm trong repo (08/09/2026, review Codex PR #228): các
phiên trước dựng bằng tệp tạm rồi máy làm việc bị lùi, mất hết, người sau
không tái hiện được "11 ca đỏ do thiếu fixture" là thiếu cái gì. Đây là
danh sách fixture đã dựng, ai chạy lại cũng ra cùng nền.

Chạy:
    bench --site <site-thu> execute vagabond.khung.bench_thu.nen_bench.dung
"""

import frappe
from frappe.utils import today

CTY = "Vagabond Kiem"
ABBR = "VK"


def _khoa():
	if not frappe.conf.get("vagabond_bench_thu"):
		frappe.throw("nen_bench chỉ chạy trên bench thử có vagabond_bench_thu=1 trong site_config.json.")


def _doctype(ten, module, fields, **them):
	if frappe.db.exists("DocType", ten):
		return
	d = frappe.get_doc(dict({"doctype": "DocType", "name": ten, "module": module, "custom": 1,
		"fields": fields, "permissions": [{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}]}, **them))
	d.insert(ignore_permissions=True)


def _truong(dt, ds):
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	create_custom_fields({dt: ds}, update=True)


def _tai_khoan(so, ten, cha, loai=None, root=None):
	name = "%s - %s - %s" % (so, ten, ABBR)
	if frappe.db.exists("Account", name):
		return name
	cha_name = frappe.db.get_value("Account", {"company": CTY, "is_group": 1, "account_name": cha}, "name")
	if not cha_name:
		cha_name = frappe.db.get_value("Account", {"company": CTY, "is_group": 1, "root_type": root}, "name")
	doc = frappe.get_doc({"doctype": "Account", "account_name": ten, "account_number": so, "company": CTY,
		"parent_account": cha_name, "is_group": 0, "account_type": loai, "account_currency": "VND"})
	doc.insert(ignore_permissions=True)
	return doc.name


def dung():
	_khoa()
	# 1. Công ty VND, biểu đồ tài khoản chuẩn.
	if not frappe.db.exists("Company", CTY):
		# Đi qua setup wizard để có đủ Warehouse Type, Item Group, năm tài chính.
		from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
		nam = today()[:4]
		setup_complete({"currency": "VND", "full_name": "Administrator", "company_name": CTY, "company_abbr": ABBR,
			"timezone": "Asia/Ho_Chi_Minh", "country": "Vietnam", "fy_start_date": nam + "-01-01",
			"fy_end_date": nam + "-12-31", "language": "en", "chart_of_accounts": "Standard",
			"email": "admin@example.com", "password": "admin", "setup_demo": 0})
		frappe.db.commit()
	frappe.db.set_single_value("Global Defaults", "default_company", CTY)
	frappe.db.set_single_value("Buying Settings", "maintain_same_rate", 0)
	frappe.db.set_single_value("Buying Settings", "po_required", "No")
	frappe.db.set_single_value("Buying Settings", "pr_required", "No")
	frappe.db.set_single_value("Selling Settings", "cust_master_name", "Customer Name")
	frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 0)
	frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
	frappe.db.set_single_value("Stock Settings", "use_serial_batch_fields", 1)
	# Năm tài chính.
	if not frappe.db.exists("Fiscal Year", {"year_start_date": ["<=", today()], "year_end_date": [">=", today()]}):
		nam = today()[:4]
		frappe.get_doc({"doctype": "Fiscal Year", "year": nam, "year_start_date": nam + "-01-01",
			"year_end_date": nam + "-12-31"}).insert(ignore_permissions=True)
	# 2. Tài khoản cho cả SI/PKT lịch sử và đường VAT mới, chỉ trên bench thử.
	_tai_khoan("131", "Phải thu khách hàng", "Current Assets", "Receivable", "Asset")
	_tai_khoan("5111", "Doanh thu bán hàng", "Income", "Income Account", "Income")
	_tai_khoan("6428", "Chi phí bằng tiền khác", "Expenses", None, "Expense")
	_tai_khoan("1331", "Thuế GTGT được khấu trừ", "Current Assets", "Tax", "Asset")
	_tai_khoan("33311", "Thuế GTGT phải nộp", "Current Liabilities", "Tax", "Liability")
	_tai_khoan("64181", "Chi phí hàng tặng", "Expenses", None, "Expense")
	_tai_khoan("64182", "Thuế GTGT hàng tặng", "Expenses", None, "Expense")
	# 3. Doctype chỉ có trên site.
	_doctype("MInvoice Phat Hanh Settings", "Vagabond", [
		{"fieldname": "api2_base", "fieldtype": "Data", "label": "API base"},
		{"fieldname": "api2_username", "fieldtype": "Data", "label": "API user"},
		{"fieldname": "api2_password", "fieldtype": "Password", "label": "API pass"},
		{"fieldname": "username", "fieldtype": "Data", "label": "User"},
		{"fieldname": "password", "fieldtype": "Password", "label": "Pass"},
		{"fieldname": "ma_dvcs", "fieldtype": "Data", "label": "Ma DVCS"},
		{"fieldname": "thue_suat", "fieldtype": "Float", "label": "Thue suat"},
		{"fieldname": "ky_hieu", "fieldtype": "Data", "label": "Ky hieu"},
		{"fieldname": "buyer_name", "fieldtype": "Data", "label": "Buyer"},
		{"fieldname": "ma_hang_gop", "fieldtype": "Small Text", "label": "Ma hang gop"},
		{"fieldname": "nguon", "fieldtype": "Data", "label": "Nguon"},
		{"fieldname": "hau_to_dia_chi", "fieldtype": "Data", "label": "Hau to"},
		{"fieldname": "last_run", "fieldtype": "Data", "label": "Last run"},
		{"fieldname": "tong_da_day", "fieldtype": "Int", "label": "Tong"},
		{"fieldname": "last_error", "fieldtype": "Small Text", "label": "Last error"},
	], issingle=1)
	frappe.db.set_single_value("MInvoice Phat Hanh Settings", "thue_suat", 8)
	frappe.db.set_single_value("MInvoice Phat Hanh Settings", "ky_hieu", "1C26KIEM")
	frappe.db.set_single_value("MInvoice Phat Hanh Settings", "buyer_name", "Bán cho người tiêu dùng")
	frappe.db.set_single_value("MInvoice Phat Hanh Settings", "nguon", "Pancake")
	_doctype("MInvoice Invoice", "Vagabond", [
		{"fieldname": "ma_hd_id", "fieldtype": "Data", "label": "ID", "unique": 1},
		{"fieldname": "loai", "fieldtype": "Data", "label": "Loai"},
		{"fieldname": "ky_hieu", "fieldtype": "Data", "label": "Ky hieu"},
		{"fieldname": "so_hd", "fieldtype": "Data", "label": "So"},
		{"fieldname": "ngay_lap", "fieldtype": "Date", "label": "Ngay lap"},
		{"fieldname": "nguoi_mua_ban", "fieldtype": "Data", "label": "Doi tac"},
		{"fieldname": "mst_doi_tac", "fieldtype": "Data", "label": "MST"},
		{"fieldname": "tien_truoc_thue", "fieldtype": "Currency", "label": "Truoc thue"},
		{"fieldname": "tien_thue", "fieldtype": "Currency", "label": "Thue"},
		{"fieldname": "tong_tien", "fieldtype": "Currency", "label": "Tong"},
		{"fieldname": "ma_tra_cuu", "fieldtype": "Data", "label": "Ma tra cuu"},
		{"fieldname": "chi_tiet", "fieldtype": "Long Text", "label": "Chi tiet"},
		{"fieldname": "trang_thai", "fieldtype": "Data", "label": "Trang thai"},
		{"fieldname": "ly_do_bo_qua", "fieldtype": "Small Text", "label": "Ly do"},
		{"fieldname": "da_tao_chung_tu", "fieldtype": "Check", "label": "Da tao"},
		{"fieldname": "so_lan_thu", "fieldtype": "Int", "label": "So lan thu"},
		{"fieldname": "sobaomat", "fieldtype": "Data", "label": "So bao mat"},
	], autoname="field:ma_hd_id")
	_doctype("Anh Xa Mat Hang NCC", "Vagabond", [
		{"fieldname": "nha_cung_cap", "fieldtype": "Link", "options": "Supplier", "label": "NCC"},
		{"fieldname": "ten_hang_ncc", "fieldtype": "Data", "label": "Ten hang NCC"},
		{"fieldname": "ma_hang", "fieldtype": "Link", "options": "Item", "label": "Ma hang"},
	])
	_doctype("MInvoice NCC Map", "Vagabond", [
		{"fieldname": "supplier_mst", "fieldtype": "Data", "label": "MST NCC"},
		{"fieldname": "ma_ncc", "fieldtype": "Data", "label": "Ma NCC"},
		{"fieldname": "ten_ncc", "fieldtype": "Data", "label": "Ten NCC"},
		{"fieldname": "item_code", "fieldtype": "Link", "options": "Item", "label": "Item"},
	])
	# 4. Custom field chỉ có trên site (tạo tay trên Desk ngày trước).
	_truong("Sales Invoice", [
		{"fieldname": "vgb_pt_thanh_toan", "fieldtype": "Link", "options": "Mode of Payment", "label": "PT thanh toan", "insert_after": "customer"},
		{"fieldname": "custom_nguon", "fieldtype": "Data", "label": "Nguon", "insert_after": "customer"},
		{"fieldname": "custom_pancake_id", "fieldtype": "Data", "label": "Pancake ID", "insert_after": "customer"},
		{"fieldname": "custom_pancake_display_id", "fieldtype": "Data", "label": "Pancake display", "insert_after": "customer"},
		{"fieldname": "vgb_quay", "fieldtype": "Data", "label": "Quay", "insert_after": "customer"},
		{"fieldname": "vgb_huy", "fieldtype": "Check", "label": "Huy", "insert_after": "customer"},
		{"fieldname": "vgb_tam_tinh", "fieldtype": "Check", "label": "Tam tinh", "insert_after": "customer"},
		{"fieldname": "vgb_xhd_ten", "fieldtype": "Data", "label": "XHD ten", "insert_after": "customer"},
		{"fieldname": "vgb_xhd_mst", "fieldtype": "Data", "label": "XHD mst", "insert_after": "customer"},
		{"fieldname": "vgb_xhd_dia_chi", "fieldtype": "Small Text", "label": "XHD dia chi", "insert_after": "customer"},
		{"fieldname": "vgb_xhd_email", "fieldtype": "Data", "label": "XHD email", "insert_after": "customer"},
		{"fieldname": "custom_hddt_trang_thai", "fieldtype": "Data", "label": "HDDT trang thai", "insert_after": "customer"},
		{"fieldname": "custom_hddt_so", "fieldtype": "Data", "label": "HDDT so", "insert_after": "customer"},
		{"fieldname": "custom_hddt_id", "fieldtype": "Data", "label": "HDDT id", "insert_after": "customer"},
		{"fieldname": "custom_hddt_ky_hieu", "fieldtype": "Data", "label": "HDDT ky hieu", "insert_after": "customer"},
		{"fieldname": "custom_hddt_sobaomat", "fieldtype": "Data", "label": "HDDT sobaomat", "insert_after": "customer"},
		{"fieldname": "custom_minvoice_id", "fieldtype": "Data", "label": "MInvoice id", "insert_after": "customer"},
		{"fieldname": "custom_minvoice_ngay_day", "fieldtype": "Data", "label": "MInvoice ngay day", "insert_after": "customer"},
	])
	_truong("Customer", [{"fieldname": "vgb_hang", "fieldtype": "Data", "label": "Hang", "insert_after": "customer_name"}])
	_truong("Purchase Invoice", [
		{"fieldname": "custom_minvoice_id", "fieldtype": "Data", "label": "MInvoice id", "insert_after": "supplier"},
	])
	_truong("Purchase Invoice Item", [
		{"fieldname": "ten_hang_ncc", "fieldtype": "Data", "label": "Ten hang NCC", "insert_after": "item_name"},
	])
	# 5. Danh mục: kho, món bán, món mua dịch vụ, khách, NCC.
	kho = frappe.db.get_value("Warehouse", {"company": CTY, "is_group": 0}, "name")
	if not kho:
		kho = frappe.get_doc({"doctype": "Warehouse", "warehouse_name": "Kho kiem", "company": CTY}).insert(ignore_permissions=True).name
	if not frappe.db.exists("Item", "BANH-KIEM"):
		frappe.get_doc({"doctype": "Item", "item_code": "BANH-KIEM", "item_name": "Bánh kiểm thử", "item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
			"stock_uom": "Nos", "is_stock_item": 0, "is_sales_item": 1, "is_purchase_item": 0}).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", "DV-KIEM"):
		frappe.get_doc({"doctype": "Item", "item_code": "DV-KIEM", "item_name": "Dịch vụ kiểm thử", "item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
			"stock_uom": "Nos", "is_stock_item": 0, "is_sales_item": 0, "is_purchase_item": 1}).insert(ignore_permissions=True)
	if not frappe.db.exists("Item", "NVL-KIEM"):
		frappe.get_doc({"doctype": "Item", "item_code": "NVL-KIEM", "item_name": "Nguyên liệu kiểm thử", "item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
			"stock_uom": "Nos", "is_stock_item": 1, "is_sales_item": 0, "is_purchase_item": 1, "valuation_rate": 1000}).insert(ignore_permissions=True)
	if not frappe.db.exists("Customer", "Khách kiểm thử"):
		frappe.get_doc({"doctype": "Customer", "customer_name": "Khách kiểm thử", "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
			"territory": "All Territories", "vgb_hang": "MEMBER"}).insert(ignore_permissions=True)
	if not frappe.db.exists("Supplier", "NCC kiểm thử"):
		frappe.get_doc({"doctype": "Supplier", "supplier_name": "NCC kiểm thử", "supplier_group": frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")}).insert(ignore_permissions=True)
	for pt in ("Hàng tặng", "Tiền mặt", "Chuyển khoản"):
		if not frappe.db.exists("Mode of Payment", pt):
			frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": pt}).insert(ignore_permissions=True)
	# 6. Những thứ các bộ kiểm khác cần: khách lẻ dùng chung, tài khoản ngân
	#    hàng, tài khoản kho mặc định cho công ty, index của patch mua_hddt_v446
	#    (install đánh dấu patch đã chạy mà không chạy, nên index không có).
	if not frappe.db.exists("Customer", "Khách lẻ Online"):
		frappe.get_doc({"doctype": "Customer", "customer_name": "Khách lẻ Online", "customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
			"territory": "All Territories"}).insert(ignore_permissions=True)
	if not frappe.db.exists("Account", {"company": CTY, "account_type": "Bank", "is_group": 0}):
		cha = frappe.db.get_value("Account", {"company": CTY, "is_group": 1, "account_name": "Bank Accounts"}, "name")
		frappe.get_doc({"doctype": "Account", "account_name": "Ngân hàng kiểm", "account_number": "1121", "company": CTY,
			"parent_account": cha, "is_group": 0, "account_type": "Bank", "account_currency": "VND"}).insert(ignore_permissions=True)
	kho_tk = frappe.db.get_value("Account", {"company": CTY, "account_type": "Stock", "is_group": 0}, "name")
	if kho_tk:
		frappe.db.set_value("Company", CTY, "default_inventory_account", kho_tk)
		frappe.db.set_value("Company", CTY, "enable_perpetual_inventory", 1)
	if not frappe.db.has_index("tabPurchase Invoice Item", "vgb_pr_docstatus_227"):
		frappe.db.add_index("Purchase Invoice Item", ["pr_detail", "docstatus"], index_name="vgb_pr_docstatus_227")
	# Account loại Bank chưa đủ: đường hoàn tiền và đối chiếu sao kê đọc
	# Bank Account có liên kết về công ty và tài khoản kế toán.
	if not frappe.db.exists("Bank Account", {"company": CTY, "is_company_account": 1}):
		from vagabond.ngan_hang import chuan_hoa_hoac_bao
		ngan_hang = chuan_hoa_hoac_bao("MB")
		frappe.get_doc({"doctype": "Bank Account", "account_name": "Tài khoản kiểm thử",
			"bank": ngan_hang, "company": CTY, "is_company_account": 1,
			"account": frappe.db.get_value("Account", {"company": CTY, "account_type": "Bank", "is_group": 0}, "name"),
			"bank_account_no": "000000000243"}).insert(ignore_permissions=True)
	# Mẫu này có sẵn trên site trước khi app quản lý HTML; dựng bản ghi
	# nền rồi dùng đúng hàm đồng bộ để ca in đi qua get_print của Frappe.
	from vagabond import mau_in
	for ten, (_tep, dt) in mau_in.MAU_IN.items():
		if not frappe.db.exists("Print Format", ten):
			frappe.get_doc({"doctype": "Print Format", "name": ten, "doc_type": dt,
				"standard": "No", "custom_format": 1, "print_format_type": "Jinja",
				"html": "<p>Mẫu nền kiểm thử</p>"}).insert(ignore_permissions=True)
	mau_in.dong_bo()
	if not frappe.db.exists("Purchase Order", {"docstatus": 1}):
		po = frappe.get_doc({"doctype": "Purchase Order", "company": CTY,
			"supplier": "NCC kiểm thử", "schedule_date": today(),
			"items": [{"item_code": "DV-KIEM", "qty": 1, "rate": 100000,
				"schedule_date": today()}]}).insert(ignore_permissions=True)
		po.submit()
	frappe.db.commit()
	return {"cong_ty": CTY, "kho": kho}
