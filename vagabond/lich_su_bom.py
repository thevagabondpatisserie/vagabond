"""Ghi trực tiếp BOM và dấu vết trong cùng giao dịch, không tự commit."""
import frappe
from html import escape


def dat_bom(doctype, name, fieldname, value=None, *, nguon, **kwargs):
	assert doctype == "BOM"
	doi = fieldname if isinstance(fieldname, dict) else {fieldname: value}
	cu = frappe.db.get_value("BOM", name, list(doi), as_dict=True) or {}
	kq = frappe.db.set_value("BOM", name, fieldname, value, **kwargs)
	cau = ["%s: %s thành %s" % (k, cu.get(k), v) for k, v in doi.items() if cu.get(k) != v]
	if cau:
		# Không nuốt lỗi: nếu không ghi được dấu vết, request phải rollback.
		frappe.get_doc("BOM", name).add_comment("Comment", escape(
			"%s. Người sửa: %s. %s" % (nguon, frappe.session.user, "; ".join(cau))))
	return kq
