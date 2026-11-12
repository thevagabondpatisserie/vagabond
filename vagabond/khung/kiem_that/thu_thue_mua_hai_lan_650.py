"""v650 (Uyên báo 12/11/2026, DMH-2026-00970): đơn mua thuế bị tính HAI lần.

Mẫu thuế từng món của site (GTGT 8% - TV) khai cả 1331 lẫn 33311, Cài đặt kế
toán bật "tự thêm thuế từ mẫu thuế của món". ERPNext thật thêm hai dòng thuế
vào đơn mua: 620.000 đ ra thuế 99.200 đ thay vì 49.600 đ. Ca dựng đúng như site,
chạy insert và submit thật trong savepoint; tái hiện bằng cách tắt hook mới.
"""

from unittest.mock import patch

import frappe
from frappe.utils import flt, getdate, today

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


# Codex #553 vòng 2: hook gắn cả Purchase Invoice và Purchase Receipt, hai chứng
# từ sinh sổ cái. Ca dưới ghi sổ thật rồi đọc lại GL Entry và Stock Ledger Entry
# (AGENTS.md: thay đổi chạm sổ cái phải có ca tích hợp đọc lại sổ).


def _tk_thue():
	cty = nen.cong_ty()
	vao = frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "name": ["like", "1331 -%"]}, "name")
	ra = frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "name": ["like", "33311 -%"]}, "name")
	dung("cần tài khoản 1331 và 33311", bool(vao and ra))
	return cty, vao, ra


def _mon_hai_tk(cty, vao, ra, ton_kho):
	"""Món có mẫu thuế 8% khai cả 1331 lẫn 33311, như mẫu GTGT 8% - TV của site."""
	duoi = frappe.generate_hash(length=10)
	mau = _luu(frappe.get_doc({"doctype": "Item Tax Template", "title": "Thử 650 sổ " + duoi, "company": cty,
		"taxes": [{"tax_type": vao, "tax_rate": 8}, {"tax_type": ra, "tax_rate": 8}]}))
	return _luu(frappe.get_doc({"doctype": "Item", "item_code": "THU650S" + duoi, "item_name": "Hũ sốt thử 650 sổ",
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 1 if ton_kho else 0, "has_batch_no": 0, "has_serial_no": 0, "is_purchase_item": 1,
		"valuation_rate": 310, "taxes": [{"item_tax_template": mau.name}]})).name


def _hoa_don(cty, mon):
	hd = frappe.new_doc("Purchase Invoice")
	hd.company, hd.supplier = cty, nen.mot_nha_cung_cap()
	hd.currency, hd.conversion_rate = "VND", 1
	hd.posting_date = hd.bill_date = hd.due_date = today()
	hd.bill_no = "kiem-650-" + frappe.generate_hash(length=12)
	hd.update_stock = 0
	hd.ignore_pricing_rule = 1
	hd.cost_center = frappe.db.get_value("Company", cty, "cost_center")
	hd.append("items", {"item_code": mon, "qty": 2000, "rate": 310})
	return _luu(hd)


def _no_co(gl, tk):
	return (round(sum(flt(g.debit) for g in gl if g.account == tk)), round(sum(flt(g.credit) for g in gl if g.account == tk)))


@ca("v650 thật (Codex #553 vòng 2): hoá đơn mua món có mẫu 1331 và 33311 ghi sổ: thuế 49.600, phải trả 669.600, sổ cái không có 33311")
def _():
	cty, vao, ra = _tk_thue()
	mon = _mon_hai_tk(cty, vao, ra, ton_kho=False)
	cu = frappe.db.get_single_value("Accounts Settings", "add_taxes_from_item_tax_template")
	frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", 1)
	try:
		with patch("vagabond.thue_don_mua.bo_thue_ra_chung_tu_mua", lambda doc, method=None: None):
			hd = _hoa_don(cty, mon)
			hd.flags.ignore_permissions = True
			nen.khong_nem("tái hiện: ghi sổ hoá đơn khi chưa có hook", hd.submit)
		hd.reload()
		gl = nen.so_cai_cua(hd)
		la("tái hiện trên ERPNext thật: thuế 99.200, 33311 bị ghi Nợ 49.600",
			(round(flt(hd.total_taxes_and_charges)), _no_co(gl, ra)), (99200, (49600, 0)))

		hd = _hoa_don(cty, mon)
		hd.reload()
		la("có hook: một dòng 1331, thuế 49.600, tổng 669.600",
			([r.account_head for r in hd.taxes], round(flt(hd.total_taxes_and_charges)), round(flt(hd.grand_total))),
			([vao], 49600, 669600))
		hd.flags.ignore_permissions = True
		nen.khong_nem("ghi sổ hoá đơn có hook", hd.submit)
		hd.reload()
		gl = nen.so_cai_cua(hd)
		dung("có GL thật", bool(gl))
		la("1331 Nợ 49.600", _no_co(gl, vao), (49600, 0))
		la("không dòng sổ cái nào trên 33311", [g.account for g in gl if g.account == ra], [])
		la("phải trả nhà cung cấp Có 669.600",
			round(sum(flt(g.credit) - flt(g.debit) for g in gl if g.party_type == "Supplier")), 669600)
		la("sổ cân", round(sum(flt(g.debit) for g in gl)), round(sum(flt(g.credit) for g in gl)))
	finally:
		frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", cu)


@ca("v650 thật (Codex #553 vòng 2): phiếu nhập hàng món có mẫu 1331 và 33311 ghi sổ: thuế 49.600, giá trị kho 620.000, sổ cái không có 33311")
def _():
	cty, vao, ra = _tk_thue()
	mon = _mon_hai_tk(cty, vao, ra, ton_kho=True)
	kho = nen.mot_kho(cty)
	dung("cần một kho lá", bool(kho))
	cu = frappe.db.get_single_value("Accounts Settings", "add_taxes_from_item_tax_template")
	frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", 1)
	try:
		pn = frappe.new_doc("Purchase Receipt")
		pn.company, pn.supplier = cty, nen.mot_nha_cung_cap()
		pn.currency, pn.conversion_rate = "VND", 1
		pn.posting_date = today()
		pn.ignore_pricing_rule = 1
		pn.append("items", {"item_code": mon, "qty": 2000, "rate": 310, "warehouse": kho})
		_luu(pn)
		pn.reload()
		la("một dòng 1331, thuế 49.600, tổng 669.600",
			([r.account_head for r in pn.taxes], round(flt(pn.total_taxes_and_charges)), round(flt(pn.grand_total))),
			([vao], 49600, 669600))
		pn.flags.ignore_permissions = True
		nen.khong_nem("ghi sổ phiếu nhập", pn.submit)
		pn.reload()
		la("đã ghi sổ", pn.docstatus, 1)
		sle = frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Purchase Receipt", "voucher_no": pn.name,
			"is_cancelled": 0}, fields=["actual_qty", "stock_value_difference"])
		la("sổ kho: nhập 2000, giá trị 620.000 (thuế không vào giá vốn)",
			(sum(flt(x.actual_qty) for x in sle), round(sum(flt(x.stock_value_difference) for x in sle))), (2000, 620000))
		gl = nen.so_cai_cua(pn)
		la("không dòng sổ cái nào trên 33311", [g.account for g in gl if g.account == ra], [])
		la("sổ cân", round(sum(flt(g.debit) for g in gl)), round(sum(flt(g.credit) for g in gl)))
	finally:
		frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", cu)


# v650 (anh Việt cho phép 12/11/2026): bản vá dọn chứng từ CŨ đã ghi sổ trước hook.


def _thue_iwtd(doc):
	return sorted((d.tax_row, round(flt(d.amount))) for d in frappe.get_all("Item Wise Tax Detail",
		filters={"parenttype": doc.doctype, "parent": doc.name}, fields=["tax_row", "amount"]))


@ca("v650 thật: bản vá chứng từ cũ trên đơn mua ĐÃ GHI SỔ cộng VAT hai lần: còn 49.600, tổng 669.600, chi tiết thuế chỉ còn dòng 1331, có ghi chú")
def _():
	from vagabond.patches import v650_bo_thue_ra_cu as vb

	cty, vao, ra = _tk_thue()
	mon = _mon_hai_tk(cty, vao, ra, ton_kho=False)
	cu = frappe.db.get_single_value("Accounts Settings", "add_taxes_from_item_tax_template")
	frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", 1)
	try:
		with patch("vagabond.thue_don_mua.bo_thue_ra_chung_tu_mua", lambda doc, method=None: None):
			po = _don(mon)
			po.flags.ignore_permissions = True
			nen.khong_nem("ghi sổ đơn mua cũ khi chưa có hook", po.submit)
		po.reload()
		la("dựng đúng ca cũ: thuế 99.200, tổng 719.200", (round(flt(po.total_taxes_and_charges)), round(flt(po.grand_total))), (99200, 719200))
		dung("chứng từ nằm trong danh sách bản vá", po.name in vb.cac_chung_tu("Purchase Order"))
		kq = nen.khong_nem("chạy bản vá trên đơn mua", lambda: vb.sua_mot("Purchase Order", po.name))
		dung("bản vá đạt", bool(kq) and not kq.get("loi"))
		po.reload()
		la("sau bản vá: một dòng 1331, thuế 49.600, tổng 669.600, vẫn đã ghi sổ",
			([r.account_head for r in po.taxes], round(flt(po.total_taxes_and_charges)), round(flt(po.grand_total)), po.docstatus),
			([vao], 49600, 669600, 1))
		la("chi tiết thuế từng món chỉ còn dòng 1331", [t for t, _ in _thue_iwtd(po)], [po.taxes[0].name])
		la("lịch thanh toán theo tổng mới (Codex #553)",
			[(round(flt(r.payment_amount)), round(flt(r.outstanding))) for r in po.payment_schedule] or [(669600, 669600)],
			[(669600, 669600)] * max(1, len(po.payment_schedule)))
		dung("có ghi chú trên chứng từ", bool(frappe.db.exists("Comment", {"reference_doctype": "Purchase Order",
			"reference_name": po.name, "content": ["like", "%33311%"]})))
		la("chạy lần nữa không còn gì để bỏ", vb.sua_mot("Purchase Order", po.name), None)
	finally:
		frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", cu)


@ca("v650 thật: bản vá trên phiếu nhập ĐÃ GHI SỔ: tổng về 669.600, sổ kho và sổ cái giữ nguyên")
def _():
	from vagabond.patches import v650_bo_thue_ra_cu as vb

	cty, vao, ra = _tk_thue()
	mon = _mon_hai_tk(cty, vao, ra, ton_kho=True)
	kho = nen.mot_kho(cty)
	cu = frappe.db.get_single_value("Accounts Settings", "add_taxes_from_item_tax_template")
	frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", 1)
	try:
		with patch("vagabond.thue_don_mua.bo_thue_ra_chung_tu_mua", lambda doc, method=None: None):
			pn = frappe.new_doc("Purchase Receipt")
			pn.company, pn.supplier = cty, nen.mot_nha_cung_cap()
			pn.currency, pn.conversion_rate = "VND", 1
			pn.posting_date = today()
			pn.ignore_pricing_rule = 1
			pn.append("items", {"item_code": mon, "qty": 2000, "rate": 310, "warehouse": kho})
			_luu(pn)
			pn.flags.ignore_permissions = True
			nen.khong_nem("ghi sổ phiếu nhập cũ khi chưa có hook", pn.submit)
		pn.reload()
		la("dựng đúng ca cũ: tổng 719.200", round(flt(pn.grand_total)), 719200)

		def so():
			sle = frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Purchase Receipt", "voucher_no": pn.name,
				"is_cancelled": 0}, fields=["actual_qty", "stock_value_difference"])
			gl = nen.so_cai_cua(pn)
			return (sorted((flt(x.actual_qty), round(flt(x.stock_value_difference))) for x in sle),
				sorted((g.account, round(flt(g.debit)), round(flt(g.credit))) for g in gl))

		truoc = so()
		kq = nen.khong_nem("chạy bản vá trên phiếu nhập", lambda: vb.sua_mot("Purchase Receipt", pn.name))
		dung("bản vá đạt", bool(kq) and not kq.get("loi"))
		pn.reload()
		la("sau bản vá: một dòng 1331, tổng 669.600", ([r.account_head for r in pn.taxes], round(flt(pn.grand_total))), ([vao], 669600))
		la("sổ kho và sổ cái giữ nguyên", so(), truoc)
	finally:
		frappe.db.set_single_value("Accounts Settings", "add_taxes_from_item_tax_template", cu)
