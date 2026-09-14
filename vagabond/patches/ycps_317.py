"""#317: tên và số YCPS cho phiếu mới, không đổi tên phiếu đã có."""
import frappe


def execute():
	if not frappe.db.exists("DocType", "RnD Purchase Request"):
		return
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter
	for prop in ("options", "default"):
		make_property_setter("RnD Purchase Request", "naming_series", prop,
			"YCPS-.YY.-.MM.-.####", "Text" if prop == "options" else "Data")
	frappe.clear_cache(doctype="RnD Purchase Request")
