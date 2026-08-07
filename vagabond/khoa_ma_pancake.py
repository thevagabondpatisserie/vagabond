"""Dat khoa duy nhat cho custom_pancake_id tren Sales Invoice.

Ngay 07/08/2026 don Pancake 91475 bi tao thanh hai hoa don vi nut Dong bo
duoc bam hai lan cach nhau 2,3 giay. Doan kiem "da co hoa don chua" trong ma
khong chan duoc hai yeu cau chay song song. Khoa duy nhat duoi co so du lieu
la cho chan chac chan nhat.

An toan tren MariaDB vi khoa duy nhat cho phep NHIEU dong NULL: hon bon muoi
nghin hoa don khong phai don online deu de trong o nay, chung khong bi coi la
trung nhau. Buoc dau tien la doi het o rong thanh NULL cho chac.
"""

import frappe

TEN_KHOA = "ux_vgb_pancake_id"


def bat_cai_dat():
	"""Bat san hai o cai dat moi.

	Truong Check moi them vao mot Single doctype khong tu mang gia tri mac
	dinh cho ban ghi da co, phai ghi thang.
	"""
	if frappe.db.get_single_value("Vagabond Settings", "tu_xuat_hddt") is None:
		frappe.db.set_single_value("Vagabond Settings", "tu_xuat_hddt", 1)
	if not (frappe.db.get_single_value("Vagabond Settings", "email_canh_bao") or "").strip():
		frappe.db.set_single_value(
			"Vagabond Settings", "email_canh_bao", "thevagabondbakery@gmail.com"
		)


def execute():
	bat_cai_dat()
	frappe.db.sql(
		"update `tabSales Invoice` set custom_pancake_id = null "
		"where custom_pancake_id is not null and trim(custom_pancake_id) = ''"
	)

	da_co = frappe.db.sql(
		"""select 1 from information_schema.statistics
		where table_schema = database() and table_name = 'tabSales Invoice'
		and index_name = %s limit 1""",
		TEN_KHOA,
	)
	if da_co:
		return

	trung = frappe.db.sql(
		"""select custom_pancake_id, count(*) n from `tabSales Invoice`
		where custom_pancake_id is not null group by custom_pancake_id having n > 1""",
		as_dict=True,
	)
	if trung:
		# Con cap trung thi khong dat khoa duoc. Bao ro de nguoi ta go truoc,
		# tuyet doi khong tu xoa hoa don o day.
		frappe.log_error(
			"Chua dat duoc khoa duy nhat vi con don trung: %s"
			% ", ".join("%s (%d hoa don)" % (t.custom_pancake_id, t.n) for t in trung),
			"vagabond: dat khoa ma Pancake",
		)
		return

	try:
		# Phai dung frappe.db.add_unique chu khong goi thang ALTER TABLE:
		# Frappe chan moi cau lenh "gay commit ngam" khi dang trong mot giao
		# dich (ImplicitCommitError, da vap ngay 07/08/2026). Ham nay tu commit
		# truoc roi moi doi cau truc bang.
		frappe.db.add_unique("Sales Invoice", ["custom_pancake_id"], constraint_name=TEN_KHOA)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: dat khoa ma Pancake")
