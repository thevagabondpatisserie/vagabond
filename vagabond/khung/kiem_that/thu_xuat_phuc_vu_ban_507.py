# -*- coding: utf-8 -*-
"""v507: Xuat kho phuc vu ban hang chay THAT qua insert() va submit().

Codex bat tren PR #341: man nay de ra Material Issue cham thang vao GL Entry
va Stock Ledger Entry, ma bo kiem tang khung thay Frappe bang phieu gia nen
khong bao gio biet ERPNext co CHAP THUAN cai minh vua dien khong. AGENTS.md
muc 6 bat buoc tang nay cho moi thay doi cham so kho.

Chay tren site that qua `vagabond.khung.kiem_that.cua.chay`. Moi ca nam
trong diem luu cua khung, chung tu ao bien mat sau khi chay.

Ba ca:

1. Duong chinh: nhap 100 vao kho thu, quay khai ton_so SAI (90) va con_lai
   80, luu, ke toan ghi so. Phai xuat dung 20 theo ton THAT chu khong phai
   10, SLE ghi -20, Bin con 80, GL co dong No vao tai khoan 6412.
2. Banh thanh pham deo nhan "Bao bi" gui len thi may tu choi.
3. Cua `bo_phieu` tu choi phieu cua man khac.
"""

import frappe
from frappe.utils import flt, nowdate, nowtime

from vagabond import bo_phan, xuat_kho
from vagabond import xuat_phuc_vu_ban as xp
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_ma_cap_so import _uom


def _nhom(ten):
	"""Nhom mon theo dung TEN ma man nay phan loai.

	Site that co san "Bao bì", "Bánh lạnh". Bench CI (Bench tich hop SHA)
	la site trang, khong co nhom nao cua tiem: lan chay dau 17/09/2026 ca
	3 ca deu do vi "site thieu nhom mon". Nen thieu thi DUNG nhom la trong
	diem luu, ten phai dung tung chu vi `xp.trong_pham_vi` va
	`xp.NGOAI_PHAM_VI` doi chieu theo ten.
	"""
	if frappe.db.exists("Item Group", ten):
		return ten
	cha = "All Item Groups"
	if not frappe.db.exists("Item Group", cha):
		cha = frappe.db.get_value("Item Group", {"is_group": 1}, "name")
	g = frappe.new_doc("Item Group")
	g.item_group_name = ten
	g.parent_item_group = cha
	g.is_group = 0
	g.flags.ignore_permissions = True
	g.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Item Group", g.name))
	if g.name != ten:
		nen._LOI.append("dựng nhóm %r nhưng site đặt tên %r" % (ten, g.name))
		return None
	return ten


def _mon(ma, nhom):
	if frappe.db.exists("Item", ma):
		return ma
	it = frappe.new_doc("Item")
	it.item_code = ma
	it.item_name = "Ca kiem tich hop %s" % ma
	it.item_group = nhom
	it.stock_uom = _uom()
	it.is_stock_item = 1
	it.flags.ignore_permissions = True
	it.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Item", it.name))
	return it.name


def _kho(cty):
	"""Kho la rieng cho ca kiem, khong dung kho that cua diem ban."""
	goc = frappe.db.get_value("Warehouse", {"company": cty, "is_group": 1}, "name", order_by="lft asc")
	tat = frappe.db.get_value("Company", cty, "abbr")
	day_du = "Kiem That D1 - %s" % tat
	if frappe.db.exists("Warehouse", day_du):
		return day_du
	k = frappe.new_doc("Warehouse")
	k.warehouse_name = "Kiem That D1"
	k.company = cty
	k.parent_warehouse = goc
	k.flags.ignore_permissions = True
	k.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Warehouse", k.name))
	return k.name


def _nhap(ma, kho, so, cty, gia=1000):
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Material Receipt"
	se.stock_entry_type = "Material Receipt"
	se.set_posting_time = 1
	se.posting_date = nowdate()
	se.posting_time = nowtime()
	se.append("items", {"item_code": ma, "qty": so, "t_warehouse": kho, "basic_rate": gia})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()
	return se


def _ton(ma, kho):
	return flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty"))


def _bo_phan_that():
	for t in bo_phan.cac_la():
		if bo_phan.la_bo_phan_hop_le(t):
			return t
	return ""


@ca("v507: chot kho diem ban chay that, xuat theo ton THAT, SLE va GL dung")
def _duong_chinh():
	cty = cong_ty()
	nhom = _nhom("Bao bì")
	if not nhom:
		return
	kho = _kho(cty)
	ma = _mon("KT-XPV-BAOBI", nhom)
	khong_nem("nhập 100 vào kho thử", lambda: _nhap(ma, kho, 100, cty))
	la("tồn thật 100", _ton(ma, kho), 100.0)

	# Quay khai ton_so SAI (90) va con_lai 80. Ton that la 100 nen so da dung
	# phai la 20. Day dung la finding cua Codex tren PR #341.
	r = khong_nem("lưu phiếu", lambda: xp.luu(
		kho=kho, bo_phan_chiu=_bo_phan_that(), ghi_chu="ca kiem 507",
		dong=[{"ma": ma, "nhom": "Bao bì", "ton_so": 90, "con_lai": 80}],
	))
	if not r:
		return
	nen._DA_TAO.append(("Stock Entry", r["name"]))
	doc = frappe.get_doc("Stock Entry", r["name"])
	la("20/09: lưu là ghi sổ ngay", doc.docstatus, 1)
	la("mang mã của màn này", doc.get("vgb_muc_dich_xuat"), xuat_kho.MA_PHUC_VU_BAN)
	la("một dòng", len(doc.items), 1)
	la("xuất 20 theo tồn thật, không phải 10 theo tồn app gửi", flt(doc.items[0].qty), 20.0)
	# Site that co 6412. Bench CI la site trang, cay tai khoan mac dinh cua
	# ERPNext khong co 6412, luc do ham phai TUT ve tai khoan Xuat huy dang
	# dung chu khong nem loi (docstring _tk_theo_nhom). Kiem dung nhanh minh
	# dang dung, khong bia mot ben cho xanh.
	tk = str(doc.items[0].expense_account or "")
	co_6412 = bool(frappe.db.exists("Account", {"company": cty, "account_number": "6412", "is_group": 0}))
	if co_6412:
		dung("tài khoản chi phí là 6412", tk.startswith("6412"))
	else:
		la("site không có 6412 thì tụt về tài khoản Xuất huỷ", tk, xuat_kho._tk_chi_phi(cty))
	la("tồn còn 80 ngay sau khi lưu", _ton(ma, kho), 80.0)

	# App cu bam Ghi so lan nua thi phai tra ok, khong nem, khong tru them.
	kq2 = khong_nem("bấm Ghi sổ lần nữa", lambda: xp.ghi_so(r["name"]))
	la("trả đã ghi", (kq2 or {}).get("da_ghi"), 1)
	la("tồn vẫn 80", _ton(ma, kho), 80.0)

	sle = frappe.get_all("Stock Ledger Entry",
		filters={"voucher_no": r["name"], "is_cancelled": 0},
		fields=["item_code", "warehouse", "actual_qty"])
	la("đúng một dòng sổ kho", len(sle), 1)
	if sle:
		la("sổ kho ghi -20", flt(sle[0]["actual_qty"]), -20.0)
		la("đúng kho", sle[0]["warehouse"], kho)

	gl = frappe.get_all("GL Entry",
		filters={"voucher_no": r["name"], "is_cancelled": 0},
		fields=["account", "debit", "credit"])
	dung("có bút toán", len(gl) >= 2)
	no_6412 = [g for g in gl if g["account"] == tk and flt(g["debit"]) > 0]
	dung("có đúng một dòng Nợ vào tài khoản chi phí của dòng hàng", len(no_6412) == 1)
	if no_6412:
		la("giá trị Nợ = 20 x giá nhập", flt(no_6412[0]["debit"]), 20000.0)

	ct = xp.chi_tiet(r["name"])
	la("chi_tiet nói ai ghi sổ", bool(ct.get("nguoi_ghi_so")), True)
	la("chi_tiet nói lúc ghi sổ", bool(ct.get("luc_ghi_so")), True)
	la("nhãn dòng là chi phí bán hàng", ct["dong"][0]["nhan"], xp.NHAN_CHI_PHI)


@ca("v507: banh thanh pham deo nhan Bao bi gui len thi may tu choi")
def _banh_gia_bao_bi():
	cty = cong_ty()
	nhom_banh = _nhom("Bánh lạnh")
	if not nhom_banh:
		return
	kho = _kho(cty)
	ma = _mon("KT-XPV-BANH", nhom_banh)
	khong_nem("nhập 10 bánh vào kho thử", lambda: _nhap(ma, kho, 10, cty))
	loi = ""
	try:
		xp.luu(kho=kho, bo_phan_chiu=_bo_phan_that(), ghi_chu="",
			dong=[{"ma": ma, "nhom": "Bao bì", "ton_so": 10, "con_lai": 5}])
	except Exception as e:
		loi = nen.cau_loi(e)
	dung("từ chối", bool(loi))
	dung("nói rõ đi đường hoá đơn bán", "hoá đơn bán" in loi)
	la("không dựng phiếu nào", frappe.db.count("Stock Entry",
		{"vgb_muc_dich_xuat": xuat_kho.MA_PHUC_VU_BAN, "from_warehouse": kho, "docstatus": 0}), 0)
	la("tồn bánh còn nguyên", _ton(ma, kho), 10.0)


@ca("v507: bo_phieu tu choi phieu cua man khac")
def _bo_phieu_man_khac():
	cty = cong_ty()
	nhom = _nhom("Bao bì")
	if not nhom:
		return
	kho = _kho(cty)
	ma = _mon("KT-XPV-BAOBI", nhom)
	khong_nem("nhập 5", lambda: _nhap(ma, kho, 5, cty))
	# Mot phieu xuat dung noi bo NHAP, cua man khac.
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = xuat_kho.LOAI["huy"]
	se.stock_entry_type = xuat_kho.LOAI["huy"]
	se.from_warehouse = kho
	se.vgb_muc_dich_xuat = "marketing"
	se.append("items", {"item_code": ma, "qty": 1, "s_warehouse": kho})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	loi = ""
	try:
		xp.bo_phieu(se.name, "thử")
	except Exception as e:
		loi = nen.cau_loi(e)
	dung("từ chối phiếu của màn khác", "không phải phiếu xuất kho phục vụ bán hàng" in loi)
	frappe.clear_document_cache("Stock Entry", se.name)
	la("phiếu kia còn nguyên, chưa bị đánh dấu bỏ",
		int(frappe.db.get_value("Stock Entry", se.name, "vgb_huy") or 0), 0)
