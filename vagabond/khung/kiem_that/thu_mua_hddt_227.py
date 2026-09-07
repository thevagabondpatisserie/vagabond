"""#227: PI thật qua save/submit, thuế gốc, chiết khấu và nhiều lần nhận.

Chỉ tạo chứng từ mới trong savepoint của nen; không gọi nhà cung cấp
HĐĐT, không đụng ba hoá đơn thật người dùng báo. Thiếu danh mục là ca đỏ.
"""

import frappe
from frappe.utils import flt, today

from vagabond import doi_chieu_mua, mua_dich_vu
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la


def _luu(doc):
	doc.insert(ignore_permissions=True)
	nen._DA_TAO.append((doc.doctype, doc.name))
	return doc


def _nguon(dong, thue, tong):
	return _luu(frappe.get_doc({
		"doctype": "MInvoice Invoice", "ma_hd_id": "kiem-227-" + frappe.generate_hash(length=20),
		"loai": "Đầu vào", "ky_hieu": "KIEM227", "so_hd": "227",
		"ngay_lap": today(), "nguoi_mua_ban": "Kiểm thử trong điểm lưu #227",
		"tien_truoc_thue": tong - thue, "tien_thue": thue, "tong_tien": tong,
		"chi_tiet": frappe.as_json(dong),
	}))


def _phieu(dong, mon=None, ncc=None):
	cty = nen.cong_ty()
	mon = mon or nen._mot("Item", {"disabled": 0, "is_stock_item": 0,
		"is_purchase_item": 1, "is_fixed_asset": 0})
	ncc = ncc or nen.mot_nha_cung_cap()
	tk = frappe.db.get_value("Account", {"company": cty, "is_group": 0,
		"disabled": 0, "name": ["like", "1331 -%"]}, "name")
	if not mon or not ncc or not tk:
		frappe.throw("Ca #227 cần món mua không qua kho, NCC và tài khoản 1331 hợp lệ.")
	hd = frappe.new_doc("Purchase Invoice")
	hd.company = cty
	hd.supplier = ncc
	hd.currency = "VND"
	hd.conversion_rate = 1
	hd.posting_date = today()
	hd.bill_date = today()
	hd.bill_no = "kiem-227-" + frappe.generate_hash(length=12)
	hd.due_date = today()
	hd.update_stock = 0
	hd.ignore_pricing_rule = 1
	hd.cost_center = frappe.db.get_value("Company", cty, "cost_center")
	hd.flags.ignore_permissions = True
	for ten, sl, gia in dong:
		hd.append("items", {"item_code": mon, "item_name": ten,
			"ten_hang_ncc": ten, "qty": sl, "rate": gia})
	hd.set("taxes", [])
	hd.append("taxes", {"charge_type": "Actual", "account_head": tk,
		"description": "VAT thử #227", "tax_amount": 0, "category": "Total",
		"add_deduct_tax": "Add", "cost_center": hd.cost_center})
	return hd


def _ghi_so(hd, tong, thue):
	hd.submit()
	hd.reload()
	la("đã ghi sổ thật", hd.docstatus, 1)
	dung("tổng khớp trong ngưỡng làm tròn 1 đồng", abs(flt(hd.grand_total) - tong) <= 1)
	la("thuế đúng nguồn", sum(flt(t.tax_amount) for t in hd.taxes), thue)
	gl = nen.so_cai_cua(hd)
	dung("có GL thật", bool(gl))
	dung("GL cân", abs(sum(flt(d.debit) - flt(d.credit) for d in gl)) < 0.01)
	la("VAT đầu vào lên sổ đúng", sum(flt(d.debit) - flt(d.credit)
		for d in gl if d.account == hd.taxes[0].account_head), thue)
	la("không nhập kho lần hai", frappe.db.count("Stock Ledger Entry",
		{"voucher_type": hd.doctype, "voucher_no": hd.name}), 0)


@ca("#227: Nam An save và submit không cộng mẫu thuế lần hai vào GL")
def _nam_an():
	g = _nguon([{"ten": "Món thử Nam An", "sluong": 2, "dgia": 152286,
		"thtien": 304571}], 15229, 319800)
	hd = _phieu([("Món thử Nam An", 2, 152286)])
	_luu(hd)
	hd.custom_minvoice_id = g.name
	for buoc in ("save", "submit"):
		hd.append("taxes", {"charge_type": "On Net Total", "account_head": hd.taxes[0].account_head,
			"description": "Mẫu thừa 8%", "rate": 8, "category": "Total", "add_deduct_tax": "Add"})
		if buoc == "save":
			hd.save()
			la("save chỉ còn thuế gốc", len(hd.taxes), 1)
		else:
			_ghi_so(hd, 319800, 15229)


@ca("#227: 5561 chiết khấu cũ thành hàng được sửa một lần và ghi GL đúng")
def _chiet_khau():
	g = _nguon([
		{"ten": "Món thử rong biển", "sluong": 5, "dgia": 69444, "thtien": 347220},
		{"ten": "Món thử nước mắm", "sluong": 5, "dgia": 46296, "thtien": 231480},
		{"ten": "Chiết khấu", "tchat": 3, "sluong": 1, "dgia": 28935, "thtien": 28935},
	], 43981, 593746)
	hd = _phieu([("Món thử rong biển", 5, 69444), ("Món thử nước mắm", 5, 46296), ("Chiết khấu", 1, 28935)])
	hd.apply_discount_on = "Net Total"
	hd.discount_amount = 57870
	_luu(hd)
	hd.custom_minvoice_id = g.name
	for _ in range(2):
		hd.save()
		la("giữ hai dòng hàng", len(hd.items), 2)
		la("giảm đúng một lần", hd.discount_amount, 28935)
	_ghi_so(hd, 593746, 43981)


@ca("#227: dịch vụ 5561 không trừ chiết khấu cũ lần hai khi submit")
def _dich_vu():
	g = _nguon([{"ten": "Dịch vụ thử", "thtien": 578700},
		{"ten": "Chiết khấu", "tchat": 3, "thtien": 28935}], 43981, 593746)
	hd = _phieu([("Dịch vụ thử", 1, 549765)])
	_luu(hd)
	hd.custom_minvoice_id = g.name
	hd.vgb_loai_chung_tu = mua_dich_vu.LOAI_DICH_VU
	hd.apply_discount_on = "Net Total"
	hd.discount_amount = 57870
	_ghi_so(hd, 593746, 43981)
	la("không còn giảm lần hai", hd.discount_amount, 0)


@ca("#227: PI 2400 nối ba PR, lưu lặp giữ lượng và submit không nhập kho đúp")
def _ba_lan_nhan():
	phieu = [nen.phieu_nhap_ao(800, 2300) for _ in range(3)]
	d = phieu[0].items[0]
	g = _nguon([{"ten": "Trứng thử", "sluong": 2400, "dgia": 2300,
		"thtien": 5520000, "dvtinh": d.uom}], 0, 5520000)
	hd = _phieu([("Trứng thử", 2400, 2300)], d.item_code, phieu[0].supplier)
	hd.items[0].uom = d.uom
	hd.items[0].conversion_factor = d.conversion_factor
	hd.items[0].warehouse = d.warehouse
	hd.custom_minvoice_id = g.name
	_luu(hd)
	kq = doi_chieu_mua._noi(hd, [p.name for p in phieu], True)
	la("nối đủ ba lần nhận", kq["da_noi"], 3)
	la("không lỗi", kq["loi"], [])
	for _ in range(2):
		hd.save()
		la("số lượng không nhân", sum(flt(x.qty) for x in hd.items), 2400)
		la("đủ liên kết", {x.pr_detail for x in hd.items}, {p.items[0].name for p in phieu})
	_ghi_so(hd, 5520000, 0)
	for p in phieu:
		p.reload()
		dung("PR đã nhận tiền hoá đơn", flt(p.items[0].billed_amt) > 0)


@ca("#227: hai PI nháp cùng PR, PI thứ hai giá thấp vẫn bị chặn vượt lượng")
def _hai_nhap():
	p = nen.phieu_nhap_ao(800, 2300)
	d = p.items[0]
	ds = []
	# Hai PI đều được nối khi PR chưa có hoá đơn. Đơn giá thấp làm tổng
	# amount của cả hai vẫn <= tiền PR, nên cửa core theo tiền không đủ.
	for _ in range(2):
		hd = _phieu([("Lượng thử song song", 800, 1000)], d.item_code, p.supplier)
		hd.items[0].update({"uom": d.uom, "conversion_factor": d.conversion_factor,
			"warehouse": d.warehouse, "purchase_receipt": p.name, "pr_detail": d.name})
		_luu(hd)
		ds.append(hd)
	ds[0].submit()
	try:
		ds[1].submit()
	except frappe.ValidationError as loi:
		dung("đúng cửa số lượng, không phải chỉ cửa tiền", "Có hoá đơn khác đã dùng lượng này" in str(loi))
	else:
		dung("phải chặn PI thứ hai", False)
	la("PI thứ hai vẫn nháp trong DB", frappe.db.get_value("Purchase Invoice", ds[1].name, "docstatus"), 0)
	la("PI thứ hai không có GL", len(nen.so_cai_cua(ds[1])), 0)
