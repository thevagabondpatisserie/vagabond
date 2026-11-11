"""v650 (Uyên báo 12/11/2026, DMH-2026-00970): đơn mua thuế bị tính HAI lần.

Mẫu thuế từng món của site (GTGT 8% - TV) khai cả 1331 lẫn 33311, Cài đặt kế
toán bật "tự thêm thuế từ mẫu thuế của món". ERPNext thật thêm hai dòng thuế
vào đơn mua: 620.000 đ ra thuế 99.200 đ thay vì 49.600 đ. Ca dựng đúng như site,
chạy insert và submit thật trong savepoint; tái hiện bằng cách tắt hook mới.
"""

from unittest.mock import patch

import frappe
from frappe.utils import getdate, today

from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la


def _luu(d):
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append((d.doctype, d.name))
	return d


def _don(mon):
	po = frappe.new_doc("Purchase Order")
	po.company, po.supplier = nen.cong_ty(), nen.mot_nha_cung_cap()
	ngay = getdate(today())
	po.transaction_date = po.schedule_date = ngay
	po.currency, po.conversion_rate = "VND", 1
	po.ignore_pricing_rule = 1
	# Như gom_mua._lap_don: không chọn mẫu thuế đầu phiếu, thuế theo mẫu của món.
	po.append("items", {"item_code": mon, "qty": 2000, "rate": 310, "schedule_date": ngay})
	return _luu(po)


@ca("v650 thật: đơn mua thuế theo mẫu của món (1331 và 33311 cùng 8%) chỉ tính thuế đầu vào một lần, qua insert và submit")
def _():
	cty = nen.cong_ty()
	vao = frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "name": ["like", "1331 -%"]}, "name")
	ra = frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "name": ["like", "33311 -%"]}, "name")
	dung("cần tài khoản 1331 và 33311", bool(vao and ra))
	duoi = frappe.generate_hash(length=10)
	mau = _luu(frappe.get_doc({"doctype": "Item Tax Template", "title": "Thử 650 tám " + duoi, "company": cty,
		"taxes": [{"tax_type": vao, "tax_rate": 8}, {"tax_type": ra, "tax_rate": 8}]}))
	mon = _luu(frappe.get_doc({"doctype": "Item", "item_code": "THU650" + duoi, "item_name": "Hũ sốt thử 650",
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 0, "is_purchase_item": 1, "taxes": [{"item_tax_template": mau.name}]})).name
	cu = frappe.db.get_single_value("Accounts Settings", "add_taxes_from_item_tax_template")
	frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", 1)
	try:
		with patch("vagabond.thue_don_mua.bo_thue_ra_chung_tu_mua", lambda doc, method=None: None):
			po = _don(mon)
		po.reload()
		la("tái hiện trên ERPNext thật: thuế tính hai lần", (po.total_taxes_and_charges, len(po.taxes)), (99200, 2))

		po = _don(mon)
		po.reload()
		la("có hook: thuế 49.600, tổng 669.600", (po.total_taxes_and_charges, po.grand_total), (49600, 669600))
		la("chỉ còn dòng 1331", [r.account_head for r in po.taxes], [vao])
		po.flags.ignore_permissions = True
		po.submit()
		po.reload()
		la("submit thật vẫn 49.600, một dòng", (po.docstatus, po.total_taxes_and_charges, len(po.taxes)), (1, 49600, 1))
	finally:
		frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", cu)


@ca("v650 thật: dòng 33311 người dùng tự khai thuế suất trên chứng từ mua thì giữ nguyên")
def _():
	cty = nen.cong_ty()
	vao = frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "name": ["like", "1331 -%"]}, "name")
	ra = frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "name": ["like", "33311 -%"]}, "name")
	duoi = frappe.generate_hash(length=10)
	mon = _luu(frappe.get_doc({"doctype": "Item", "item_code": "THU650B" + duoi, "item_name": "Món thử 650 B",
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 0, "is_purchase_item": 1})).name
	po = frappe.new_doc("Purchase Order")
	po.company, po.supplier = cty, nen.mot_nha_cung_cap()
	ngay = getdate(today())
	po.transaction_date = po.schedule_date = ngay
	po.currency, po.conversion_rate = "VND", 1
	po.ignore_pricing_rule = 1
	po.append("items", {"item_code": mon, "qty": 1, "rate": 100000, "schedule_date": ngay})
	for tk, ts in ((vao, 8), (ra, 2)):
		po.append("taxes", {"charge_type": "On Net Total", "account_head": tk, "rate": ts, "description": tk,
			"category": "Total", "add_deduct_tax": "Add"})
	_luu(po)
	po.reload()
	la("giữ cả hai dòng tự khai", (len(po.taxes), po.total_taxes_and_charges), (2, 10000))
