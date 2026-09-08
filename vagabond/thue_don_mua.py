"""#227: giữ lựa chọn thuế đầu phiếu qua sửa giá và save/submit.

Core accounts_controller.set_missing_item_details giữ Link bằng chuỗi
rỗng (chỉ điền nếu None); taxes_and_totals.validate_item_tax_template bỏ
qua template rỗng, update_item_tax_map lấy thuế đầu phiếu. Không sửa số
thuế tay và không thay cấu hình thuế của Item dùng chung với đơn khác.
"""

import frappe
from frappe.utils import cint


def theo_mau_dau_phieu(doc, method=None):
	if not cint(doc.get("vgb_thue_theo_mau")):
		return
	if not doc.get("taxes_and_charges"):
		frappe.throw("Anh chị chọn mẫu thuế đầu phiếu trước khi áp cho mọi món.")
	if doc.get("shipping_rule"):
		frappe.throw("Đơn có quy tắc phí vận chuyển riêng. Anh chị tắt Dùng mẫu thuế đầu phiếu cho mọi món để giữ đủ thuế và phí.")
	from erpnext.controllers.accounts_controller import get_taxes_and_charges
	mau = frappe.get_doc("Purchase Taxes and Charges Template", doc.get("taxes_and_charges"))
	if mau.company != doc.get("company") or mau.get("disabled"):
		frappe.throw("Mẫu thuế không thuộc công ty hoặc đã ngừng dùng. Anh chị chọn lại mẫu.")
	# API có thể chỉ đổi tên mẫu mà gửi kèm bảng thuế cũ. Máy chủ dựng
	# lại từ mẫu đã chọn để 5% trên tên và 8% trong bảng không cùng tồn tại.
	doc.set("taxes", get_taxes_and_charges("Purchase Taxes and Charges Template", mau.name))
	xoa_thue_rieng(doc)


def xoa_thue_rieng(doc):
	for dong in doc.get("items") or []:
		dong.item_tax_template = ""
		dong.item_tax_rate = "{}"


def dong_bo():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	create_custom_fields({"Purchase Order": [{
		"fieldname": "vgb_thue_theo_mau", "fieldtype": "Check", "default": "0",
		"label": "Dùng mẫu thuế đầu phiếu cho mọi món",
		"insert_after": "taxes_and_charges",
		"description": "Bật: mọi dòng theo mẫu đầu phiếu, kể cả khi sửa giá hoặc thêm món. Tắt: chọn thuế riêng từng món.",
	}]}, update=True)
