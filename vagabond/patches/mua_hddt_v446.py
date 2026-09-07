"""#227: current read lượng đã lập hoá đơn không quét các dòng PI nháp."""


def execute():
	import frappe

	frappe.db.add_index("Purchase Invoice Item", ["pr_detail", "docstatus"],
		index_name="vgb_pr_docstatus_227")
