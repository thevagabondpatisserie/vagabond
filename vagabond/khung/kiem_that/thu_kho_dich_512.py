# -*- coding: utf-8 -*-
"""v512: kho dich theo chang chay THAT qua insert() va submit() (Codex PR #349).

Hook `kho_san_xuat.gan_kho_thanh_pham` doi t_warehouse cua dong thanh pham
truoc khi ERPNext ghi so kho. Tang khung chi kiem phep thuan va do chuoi, nen
khong biet ERPNext co chap thuan kho da doi, hay mot buoc sau do doi lai.
Ca nay dung hai kho bep that (hoac dung tam trong diem luu tren bench CI),
lap phieu Manufacture voi kho dich SAI, ghi so, roi doc Stock Ledger Entry.

Hai ca:
1. Thanh pham (tien to BAWC) khai t_warehouse = <Bep> - Nguyen lieu: sau ghi
   so, SLE cua dong thanh pham phai o <Bep> - Thanh pham.
2. Ban thanh pham (tien to NBTP, khong co BOM => so cap) khai t_warehouse =
   <Bep> - Thanh pham: SLE phai o <Bep> - Nguyen lieu.
"""

import frappe
from frappe.utils import flt, nowdate, nowtime

from vagabond import kho_san_xuat as ksx
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_ma_cap_so import _uom


def _hau_to(cty):
	return " - " + (frappe.db.get_value("Company", cty, "abbr") or "")


def _kho_bep(cty, bep, chang):
	"""Kho la cua bep o mot chang. Site trang thi dung tam trong diem luu."""
	ten = ksx.ten_kho_cua(bep, chang, _hau_to(cty))
	if frappe.db.exists("Warehouse", ten):
		return ten
	cha_ten = ksx.BEP[bep]["kho_nhom"].rsplit(" - ", 1)[0]
	cha = cha_ten + _hau_to(cty)
	if not frappe.db.exists("Warehouse", cha):
		goc = frappe.db.get_value("Warehouse", {"company": cty, "is_group": 1}, "name", order_by="lft asc")
		g = frappe.new_doc("Warehouse")
		g.warehouse_name = cha_ten
		g.company = cty
		g.parent_warehouse = goc
		g.is_group = 1
		g.flags.ignore_permissions = True
		g.insert(ignore_permissions=True)
		nen._DA_TAO.append(("Warehouse", g.name))
		cha = g.name
	k = frappe.new_doc("Warehouse")
	k.warehouse_name = ksx.TEN_KHO[chang] % ksx.BEP[bep]["ten"]
	k.company = cty
	k.parent_warehouse = cha
	k.flags.ignore_permissions = True
	k.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Warehouse", k.name))
	if k.name != ten:
		nen._LOI.append("dựng kho %r nhưng site đặt tên %r" % (ten, k.name))
	return k.name


def _nhom():
	for t in ("Nguyên vật liệu", "All Item Groups"):
		if frappe.db.exists("Item Group", t):
			return t
	return frappe.db.get_value("Item Group", {"is_group": 0}, "name")


def _mon(ma):
	if frappe.db.exists("Item", ma):
		return ma
	it = frappe.new_doc("Item")
	it.item_code = ma
	it.item_name = "Ca kiem 512 %s" % ma
	it.item_group = _nhom()
	it.stock_uom = _uom()
	it.is_stock_item = 1
	it.flags.ignore_permissions = True
	it.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Item", it.name))
	return it.name


def _nhap(ma, kho, so, cty):
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Material Receipt"
	se.stock_entry_type = "Material Receipt"
	se.set_posting_time = 1
	se.posting_date = nowdate()
	se.posting_time = nowtime()
	se.append("items", {"item_code": ma, "qty": so, "t_warehouse": kho, "basic_rate": 1000})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()


def _san_xuat(cty, nvl, kho_nvl, tp, kho_khai):
	"""Phieu Manufacture khong qua lenh: 1 dong nguyen lieu, 1 dong thanh pham."""
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Manufacture"
	se.stock_entry_type = "Manufacture"
	se.set_posting_time = 1
	se.posting_date = nowdate()
	se.posting_time = nowtime()
	se.from_warehouse = kho_nvl
	se.to_warehouse = kho_khai
	se.append("items", {"item_code": nvl, "qty": 2, "s_warehouse": kho_nvl})
	se.append("items", {"item_code": tp, "qty": 1, "t_warehouse": kho_khai, "is_finished_item": 1, "basic_rate": 2000})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()
	return se


def _sle_kho(ten_phieu, ma):
	r = frappe.get_all("Stock Ledger Entry",
		filters={"voucher_no": ten_phieu, "item_code": ma, "is_cancelled": 0},
		fields=["warehouse", "actual_qty"])
	return [(x["warehouse"], flt(x["actual_qty"])) for x in r]


def _chay(ma_tp, kho_khai_chang, kho_dung_chang, nhan):
	cty = cong_ty()
	kho_nl = _kho_bep(cty, "pastry", ksx.NGUYEN_LIEU)
	kho_tp = _kho_bep(cty, "pastry", ksx.THANH_PHAM)
	kho_khai = kho_nl if kho_khai_chang == ksx.NGUYEN_LIEU else kho_tp
	kho_dung = kho_nl if kho_dung_chang == ksx.NGUYEN_LIEU else kho_tp
	nvl = _mon("NVLT-KT512")
	tp = _mon(ma_tp)
	khong_nem("nhập nguyên liệu", lambda: _nhap(nvl, kho_nl, 5, cty))
	se = khong_nem("phiếu sản xuất khai kho SAI", lambda: _san_xuat(cty, nvl, kho_nl, tp, kho_khai))
	if not se:
		return
	frappe.clear_document_cache("Stock Entry", se.name)
	doc = frappe.get_doc("Stock Entry", se.name)
	la("%s: đã ghi sổ" % nhan, doc.docstatus, 1)
	dong_tp = [d for d in doc.items if d.item_code == tp]
	la("%s: dòng thành phẩm còn" % nhan, len(dong_tp), 1)
	if dong_tp:
		la("%s: t_warehouse đã đổi về kho đúng" % nhan, dong_tp[0].t_warehouse, kho_dung)
	sle = _sle_kho(se.name, tp)
	la("%s: đúng một dòng sổ kho cho thành phẩm" % nhan, len(sle), 1)
	if sle:
		la("%s: SLE ở kho đúng theo chặng" % nhan, sle[0][0], kho_dung)
		la("%s: SLE +1" % nhan, sle[0][1], 1.0)
	la("%s: kho khai sai không có sổ" % nhan, [s for s in sle if s[0] == kho_khai and kho_khai != kho_dung], [])


@ca("v512 that: thanh pham khai kho Nguyen lieu -> SLE o kho Thanh pham")
def _tp_vao_nl():
	_chay("BAWC-KT512", ksx.NGUYEN_LIEU, ksx.THANH_PHAM, "TP")


@ca("v512 that: ban thanh pham khai kho Thanh pham -> SLE o kho Nguyen lieu")
def _btp_vao_tp():
	_chay("NBTP-KT512", ksx.THANH_PHAM, ksx.NGUYEN_LIEU, "BTP")


@ca("v512 that Codex I1: nhap tay nguyen lieu vao kho Thanh pham bi chan, vao kho Nguyen lieu thi qua")
def _i1_nvl_vao_tp():
	cty = cong_ty()
	kho_nl = _kho_bep(cty, "pastry", ksx.NGUYEN_LIEU)
	kho_tp = _kho_bep(cty, "pastry", ksx.THANH_PHAM)
	nvl = _mon("NVLT-KT512")
	try:
		_nhap(nvl, kho_tp, 1, cty)
		dung("nguyên liệu vào kho Thành phẩm phải bị chặn", False)
	except frappe.ValidationError as e:
		dung("câu chặn nói rõ kho đúng", kho_nl in str(e) and nvl in str(e))
	except Exception as e:
		dung("chặn bằng ValidationError, không phải lỗi khác: %r" % e, False)
	la("không có sổ kho ở kho Thành phẩm", frappe.get_all("Stock Ledger Entry",
		filters={"item_code": nvl, "warehouse": kho_tp, "is_cancelled": 0}, pluck="name"), [])
	khong_nem("vào kho Nguyên liệu thì ghi được", lambda: _nhap(nvl, kho_nl, 1, cty))
