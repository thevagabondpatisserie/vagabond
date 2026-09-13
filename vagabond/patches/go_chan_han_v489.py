"""Bỏ công tắc HSD đã hết hiệu lực; không sửa Batch/chứng từ cũ."""
import frappe


def execute():
    ten = "Vagabond Settings-chan_lo_het_han"
    if frappe.db.exists("Custom Field", ten):
        frappe.delete_doc("Custom Field", ten, ignore_permissions=True)
    sec = "Vagabond Settings-sec_kho_lo"
    if frappe.db.exists("Custom Field", sec):
        frappe.delete_doc("Custom Field", sec, ignore_permissions=True)
    frappe.db.delete("Singles", {"doctype": "Vagabond Settings", "field": "chan_lo_het_han"})
    frappe.clear_cache(doctype="Vagabond Settings")
