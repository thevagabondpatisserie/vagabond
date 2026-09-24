"""v524/v525: ca TÍCH HỢP cho tick "Đi 242" và chặn tắt món còn ánh xạ.

v525: anh Việt bỏ nhóm "CCDC dùng ngay" và tiền tố CCDN của v524, thay bằng ô
tick trên mã món. Mã CCDC cũ chưa có sổ kho được tick sẵn.

Tầng khung đã chốt phần quyết định bằng dữ liệu giả. Câu chỉ tầng này trả
lời được: ERPNext có THẬT SỰ nhận món nhóm này là món không quản kho, hoá đơn
mua dựng từ hoá đơn điện tử có đi 242 không cần phiếu nhập kho, sổ cái có
ghi Nợ 242 đúng số tiền và không sinh sổ kho không.

Ca thật: quạt Midea FS40-24EVN 650.000 Uyên mua cho nhân viên (Điện Máy
Xanh). Mọi thứ lùi về điểm lưu, xem nen.py.
"""
import frappe

from vagabond import ccdc_dung_ngay as C
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la
from vagabond.khung.kiem_that.he_so_252 import _luu
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon, _phieu


def _tk_242():
	ct = nen.cong_ty()
	tk = frappe.db.get_value("Account", {"company": ct, "account_number": C.SO_TK,
		"is_group": 0, "disabled": 0}, "name")
	if tk:
		return tk
	# Bench CI dựng từ sơ đồ tài khoản chuẩn có thể không có số 242. Dựng
	# trong điểm lưu, lùi cùng mọi thứ khác. Site thật đã có sẵn.
	cha = frappe.db.get_value("Account", {"company": ct, "root_type": "Asset", "is_group": 1}, "name")
	dung("có nhóm tài khoản tài sản", bool(cha))
	return _luu(frappe.get_doc(dict(doctype="Account", company=ct, account_name="KT524 Chi phí chờ phân bổ",
		account_number=C.SO_TK, parent_account=cha, account_currency="VND", is_group=0))).name


def _nhom_ccdc():
	"""Nhóm Công cụ Dụng cụ như site thật. Bench CI dựng mới thì chưa có: dựng
	trong điểm lưu, lùi cùng mọi thứ khác."""
	ten = C.NHOM_CCDC[0]
	if not frappe.db.exists("Item Group", ten):
		goc = frappe.db.get_value("Item Group", {"is_group": 1}, "name", order_by="lft asc")
		_luu(frappe.get_doc(dict(doctype="Item Group", item_group_name=ten, parent_item_group=goc, is_group=0)))
	return ten


def _mon_cu(nhom, tick=0):
	it = frappe.new_doc("Item")
	it.item_code = "KT525-" + frappe.generate_hash(length=9)
	it.item_name = "Quạt đứng ca kiểm v525"
	# Mã cũ: tạo ở nhóm khác (không tick sẵn), quản kho, rồi mới chuyển nhóm.
	it.item_group = frappe.db.get_value("Item Group", {"is_group": 0, "name": ["!=", nhom]}, "name")
	it.stock_uom = frappe.db.get_value("UOM", {}, "name")
	it.is_stock_item = 1
	it.is_purchase_item = 1
	_luu(it)
	frappe.db.set_value("Item", it.name, "item_group", nhom)
	return frappe.get_doc("Item", it.name)


@ca("#525 quạt mã CCDC cũ tick Đi 242: hoá đơn mua đi Nợ 242, không phiếu nhập kho, không sổ kho")
def _quat():
	tk = khong_nem("tài khoản 242", _tk_242)
	if not tk:
		return
	nhom = khong_nem("nhóm CCDC", _nhom_ccdc)
	mon = khong_nem("mã CCDC cũ", lambda: _mon_cu(nhom))
	if not mon:
		return
	# Lối patch: tick sẵn mọi mã CCDC chưa có sổ kho.
	kq = khong_nem("patch tick mã cũ", C.tick_ma_cu) or {}
	dung("patch tick mã quạt", mon.name in (kq.get("ma") or []))
	la("chạy lần hai không tick thêm", mon.name in ((C.tick_ma_cu() or {}).get("ma") or []), False)
	mon.reload()
	la("đã tick", int(mon.get(C.O_TICK) or 0), 1)
	la("không quản kho", int(mon.is_stock_item), 0)
	la("cho mua", int(mon.is_purchase_item), 1)
	la("không bán", int(mon.is_sales_item), 0)
	la("mặc định chi phí 242", [(d.company, d.expense_account) for d in mon.item_defaults
		if d.company == nen.cong_ty()], [(nen.cong_ty(), tk)])
	# Lưu lại qua đường thường (hook) không đổi gì.
	khong_nem("lưu lại mã đã tick", lambda: mon.save(ignore_permissions=True))
	mon.reload()
	la("lưu lại vẫn không quản kho và 242", (int(mon.is_stock_item), [d.expense_account for d in mon.item_defaults
		if d.company == nen.cong_ty()]), (0, [tk]))

	goc = _nguon([dict(ten="Quạt đứng Midea FS40-24EVN", sluong=1, dgia=650000, thtien=650000,
		dvtinh=mon.stock_uom, tchat=1)], 0, 650000)
	hd = _phieu([("Quạt đứng Midea FS40-24EVN", 1, 650000)], mon=mon.name)
	_luu(hd)
	hd.custom_minvoice_id = goc.name
	hd.save()
	hd.reload()
	la("dòng hoá đơn đi 242", [d.expense_account for d in hd.items], [tk])
	hd.submit()
	hd.reload()
	la("ghi sổ không cần phiếu nhập kho", int(hd.docstatus), 1)
	gl = nen.so_cai_cua(hd)
	la("Nợ 242 đúng tiền quạt", sum(d.debit - d.credit for d in gl if d.account == tk), 650000)
	la("sổ cái cân", sum(d.debit - d.credit for d in gl), 0)
	la("không sinh sổ kho", frappe.db.count("Stock Ledger Entry",
		{"voucher_type": hd.doctype, "voucher_no": hd.name}), 0)


@ca("#524 ca Kahlua trên dữ liệu thật: tắt món còn ánh xạ bị chặn, ánh xạ mới vào món tắt bị chặn")
def _tat_mon():
	if not frappe.db.exists("DocType", "MInvoice NCC Map"):
		dung("site có bảng ánh xạ NCC để chạy ca này", False)
		return
	mon = frappe.new_doc("Item")
	mon.item_code = "KT524-TAT-" + frappe.generate_hash(length=8)
	mon.item_name = "Rượu ca kiểm v524"
	mon.item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	mon.stock_uom = frappe.db.get_value("UOM", {}, "name")
	mon.is_stock_item = 0
	mon.is_purchase_item = 1
	_luu(mon)
	ax = _luu(frappe.get_doc(dict(doctype="MInvoice NCC Map", supplier_mst="0315777858",
		ten_ncc="Rượu ca kiểm v524 " + frappe.generate_hash(length=6), item_code=mon.name)))
	mon.reload()
	mon.disabled = 1
	try:
		mon.save(ignore_permissions=True)
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("tắt món còn ánh xạ bị chặn", "Chưa tắt được món" in loi)
	la("món vẫn đang dùng", int(frappe.db.get_value("Item", mon.name, "disabled")), 0)

	# Gỡ ánh xạ thì tắt được, và từ đó không lập được ánh xạ mới vào món này.
	frappe.delete_doc("MInvoice NCC Map", ax.name, ignore_permissions=True, force=True)
	mon.reload()
	mon.disabled = 1
	khong_nem("tắt món hết ánh xạ", lambda: mon.save(ignore_permissions=True))
	try:
		_luu(frappe.get_doc(dict(doctype="MInvoice NCC Map", supplier_mst="0315777858",
			ten_ncc="Rượu ca kiểm v524 mới", item_code=mon.name)))
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("ánh xạ mới vào món đã tắt bị chặn", "đã tắt" in loi)
