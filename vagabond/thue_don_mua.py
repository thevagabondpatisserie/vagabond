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


def kiem_sau_bo(truoc, sau, thue_bo):
	"""THUẦN: chứng từ cũ sau khi bỏ dòng 33311 tự thêm có thay đổi ĐÚNG phần đó không.

	truoc, sau: {net_total, grand_total, thue_giu, advance_paid}; thue_giu là tổng
	thuế các dòng còn giữ. Chỉ được giảm tổng đúng bằng phần thuế bỏ (lệch tối đa
	1 đồng làm tròn); tiền hàng và thuế 1331 giữ nguyên; tiền đã ứng trước không
	được vượt tổng mới. Trả danh sách lý do, rỗng là đạt."""
	def f(d, k):
		return float((d or {}).get(k) or 0)

	loi = []
	if abs(f(truoc, "net_total") - f(sau, "net_total")) > 0.01:
		loi.append("tiền hàng đổi")
	if abs(f(truoc, "thue_giu") - f(sau, "thue_giu")) > 0.01:
		loi.append("thuế đầu vào đổi")
	if abs(f(truoc, "grand_total") - float(thue_bo or 0) - f(sau, "grand_total")) > 1:
		loi.append("tổng không giảm đúng phần thuế bỏ")
	if f(sau, "advance_paid") > f(sau, "grand_total") + 0.01:
		loi.append("đã ứng trước nhiều hơn tổng mới")
	return loi


TRUONG_TIEN = ("grand_total", "total_taxes_and_charges", "taxes_and_charges_added")


def tinh_bo_thue(cha, dong, bo, lam_tron=None):
	"""THUẦN: số mới của chứng từ CŨ khi bỏ các dòng thuế `bo`, chỉ bằng phép trừ.

	Không tính lại theo mẫu thuế hiện tại (mẫu có thể đã đổi từ ngày lập chứng từ,
	tính lại sẽ đổi luôn thuế 1331 đã ghi). cha: các trường tiền của chứng từ (cả
	base_*), rounded_total, disable_rounded_total. dong: các dòng thuế theo thứ tự
	{name, tax_amount, base_tax_amount, total, base_total, add_deduct_tax}.
	Trả (cha_moi, dong_moi) với dong_moi = [{name, idx, total, base_total}] của
	các dòng giữ lại. lam_tron(x) làm tròn tổng theo tiền tệ."""
	lam_tron = lam_tron or (lambda x: round(x))

	def f(d, k):
		return float(d.get(k) or 0)

	def dau(r):
		return -1.0 if (r.get("add_deduct_tax") or "Add") == "Deduct" else 1.0

	tru, tru_base, dong_moi = 0.0, 0.0, []
	for i, r in enumerate(dong):
		if i in bo:
			tru += dau(r) * f(r, "tax_amount")
			tru_base += dau(r) * f(r, "base_tax_amount")
			continue
		dong_moi.append({"name": r.get("name"), "idx": len(dong_moi) + 1,
			"total": round(f(r, "total") - tru, 6), "base_total": round(f(r, "base_total") - tru_base, 6)})
	them = sum(f(dong[i], "tax_amount") for i in bo if dau(dong[i]) > 0)
	them_base = sum(f(dong[i], "base_tax_amount") for i in bo if dau(dong[i]) > 0)
	moi = {}
	for k, d, db in (("grand_total", tru, tru_base), ("total_taxes_and_charges", tru, tru_base),
			("taxes_and_charges_added", them, them_base)):
		moi[k] = round(f(cha, k) - d, 6)
		moi["base_" + k] = round(f(cha, "base_" + k) - db, 6)
	if not int(cha.get("disable_rounded_total") or 0) and f(cha, "rounded_total"):
		for p in ("", "base_"):
			moi[p + "rounded_total"] = lam_tron(moi[p + "grand_total"])
			moi[p + "rounding_adjustment"] = round(moi[p + "rounded_total"] - moi[p + "grand_total"], 6)
	return moi, dong_moi


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
