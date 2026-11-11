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


# v650 (Uyên báo 12/11/2026, DMH-2026-00970): mẫu thuế từng món (GTGT 8% - TV)
# khai CẢ tài khoản thuế đầu vào 1331 lẫn đầu ra 33311, mỗi tài khoản 8%. Cài đặt
# kế toán bật "tự thêm thuế từ mẫu thuế của món" nên ERPNext thêm HAI dòng thuế
# vào đơn mua, tiền thuế bị tính hai lần (620.000 đ ra 99.200 đ thay vì 49.600 đ).
# Trên chứng từ MUA, dòng 33311 do máy tự thêm là sai: bỏ đi rồi tính lại tổng.
# Dòng 33311 người dùng tự gõ thuế suất thì giữ nguyên.
TK_THUE_VAO = "1331"
TK_THUE_RA = "33311"


def dong_thue_ra_tu_them(taxes):
	"""THUẦN: chỉ số các dòng thuế đầu ra (33311) mà máy tự thêm vào chứng từ mua.

	Máy tự thêm theo mẫu thuế của món thì dòng có loại "On Net Total" và thuế
	suất 0 (thuế suất lấy theo từng món). Chỉ bỏ khi chứng từ đã có dòng thuế
	đầu vào 1331, để không mất thuế của đơn chỉ khai 33311 (không có ca nào hợp lệ
	nhưng không đoán thay người dùng)."""
	def doc(r, k):
		return r.get(k) if hasattr(r, "get") else getattr(r, k, None)

	ds = list(taxes or [])
	co_vao = any(str(doc(r, "account_head") or "").startswith(TK_THUE_VAO + " ") or str(doc(r, "account_head") or "") == TK_THUE_VAO
		for r in ds)
	if not co_vao:
		return []
	return [i for i, r in enumerate(ds)
		if str(doc(r, "account_head") or "").startswith(TK_THUE_RA)
		and (doc(r, "charge_type") or "") == "On Net Total"
		and abs(float(doc(r, "rate") or 0)) < 1e-9]


def bo_thue_ra_chung_tu_mua(doc, method=None):
	"""Hook validate của Đơn mua, Phiếu nhập kho, Hoá đơn mua, Báo giá NCC."""
	if doc.get("docstatus") == 2:
		return
	bo = dong_thue_ra_tu_them(doc.get("taxes"))
	if not bo:
		return
	giu = [r for i, r in enumerate(doc.get("taxes") or []) if i not in bo]
	for i, r in enumerate(giu, 1):
		r.idx = i
	doc.set("taxes", giu)
	doc.calculate_taxes_and_totals()


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
