"""v670 ca TÍCH HỢP: combo trong đơn giao của quầy (WEBORDER) qua phiếu tạm tính thật.

Tầng khung chốt luật nguồn và cờ kênh bằng bản giả. Tầng này hỏi điều bản giả không
trả lời: phiếu tạm tính quầy lập khi xác nhận đơn giao (ban_hang.tao_don_tay với
tam_tinh=1 và cờ giữ giá dòng vgb_gia_chot, đúng đường don_quay._xac_nhan_trong_khoa)
có rã dòng combo KMCB thành món thật mà GIỮ ĐÚNG tổng khách đã trả không. Lệch tổng
thì quầy không xác nhận được đơn (don_quay chặn), nên ca này chốt tổng.
Mọi thứ lùi về điểm lưu, xem nen.py.
"""

from unittest.mock import patch

import frappe

from vagabond import ban_hang, diem_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _mon, _nen


@ca("v670 thật: phiếu tạm tính đơn giao có combo (giữ giá dòng) rã thành món, tổng đúng giá combo khách đã trả")
def _combo_giao():
	ct, tk, _ = _nen()
	mon = _mon(tk)
	cha = frappe.copy_doc(frappe.get_doc("Item", mon))
	cha.item_code = "KMCB-KIEM670-" + frappe.generate_hash(length=8)
	cha.item_name = "Combo kiểm đơn giao"
	cha.insert(ignore_permissions=True)
	nen._DA_TAO.append((cha.doctype, cha.name))
	cb = frappe.get_doc(dict(doctype="Vagabond Combo", ten="Combo kiểm đơn giao", ma_hang=cha.name, bat=1,
		kieu="Gia tron goi", gia_combo=89000, dong=[dict(item_code=mon, so_luong=2, gia_goc=50000)]))
	cb.insert(ignore_permissions=True)
	nen._DA_TAO.append((cb.doctype, cb.name))
	kh = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name")
	cac_diem = diem_ban.diem_cua_nguon("GrabFood")
	quay = cac_diem[0] if cac_diem else ""

	def lap():
		frappe.flags.vgb_gia_chot = True
		try:
			with patch.object(ban_hang, "_cong_ty", return_value=ct), patch.object(ban_hang, "_khach_le", return_value=kh):
				return ban_hang.tao_don_tay(nguon="GrabFood", quay=quay, ma_don="KT670-" + frappe.generate_hash(length=8),
					items=[dict(item_code=cha.name, qty=1, rate=89000)], tam_tinh=1)
		finally:
			frappe.flags.vgb_gia_chot = False
	ra = khong_nem("lập phiếu tạm tính", lap) or {}
	if not ra.get("name"):
		return
	nen._DA_TAO.append(("Sales Invoice", ra["name"]))
	hd = frappe.get_doc("Sales Invoice", ra["name"])
	la("rã thành món thật", [(d.item_code, d.qty) for d in hd.items if d.item_code == mon], [(mon, 2)])
	la("không còn dòng mã combo", [d.item_code for d in hd.items if d.item_code == cha.name], [])
	la("tổng đúng giá combo khách đã trả", int(round(hd.grand_total)), 89000)


@ca("v670 thật: phiếu mang nguồn WEBORDER thanh toán đúng như Mang về; đơn kênh WEBORDER đặt tên WO-YYMMDD-5 số, đơn đặt bánh web vẫn DW, đơn gọi món tại bàn O2O, số liền nhau")
def _ten_va_nguon():
	import re

	from frappe.model.naming import set_new_name

	la("phương thức như Mang về", ban_hang._pt_cho_nguon("WEBORDER"), ban_hang._pt_cho_nguon("Mang về"))
	ten = []
	for kenh in ("WEBORDER", "WEBORDER", ""):
		d = frappe.new_doc("Vagabond Don Web")
		d.vgb_kenh = kenh
		khong_nem("đặt tên đơn web", lambda: set_new_name(d))
		ten.append(d.name or "")
	dung("hai đơn WEBORDER mang mã WO: " + ", ".join(ten), all(re.fullmatch(r"WO-[0-9]{6}-[0-9]{5}", x) for x in ten[:2]))
	la("số liền nhau", int(ten[1][-5:]) - int(ten[0][-5:]), 1)
	dung("đơn đặt bánh web vẫn DW: " + ten[2], ten[2].startswith("DW-"))
	g = frappe.new_doc("Vagabond Goi Mon Ban")
	khong_nem("đặt tên đơn gọi món", lambda: set_new_name(g))
	dung("đơn gọi món tại bàn mang mã O2O: " + str(g.name), bool(re.fullmatch(r"O2O-[0-9]{6}-[0-9]{5}", g.name or "")))


@ca("v670 thật: dòng phiếu đặt ERPNext không có cột billed_qty; số đã xuất hoá đơn đọc từ hoá đơn ĐÃ GHI SỔ lập từ phiếu (đặt 5, hoá đơn 2 ghi sổ, hoá đơn 1 còn nháp: 2); đọc giữ chỗ và đếm refill chạy không lỗi")
def _da_xuat_hd():
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
	from frappe.utils import add_days, getdate, today

	from vagabond import dat_banh

	dung("bảng dòng phiếu đặt không có cột billed_qty (app không được đọc cột này)",
		"billed_qty" not in frappe.db.get_table_columns("Sales Order Item"))
	ct, tk, _ = _nen()
	mon = _mon(tk)
	kh = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name")
	ngay = add_days(today(), 3)
	so = frappe.get_doc(dict(doctype="Sales Order", company=ct, customer=kh, transaction_date=today(), delivery_date=ngay,
		items=[dict(item_code=mon, qty=5, rate=10000, delivery_date=ngay)]))

	def lap_so():
		so.insert(ignore_permissions=True)
		nen._DA_TAO.append((so.doctype, so.name))
		so.submit()
		return so.name
	if not khong_nem("lập phiếu đặt", lap_so):
		return

	def lap_hd(sl, ghi_so):
		hd = make_sales_invoice(so.name)
		hd.items = [d for d in hd.items if d.so_detail == so.items[0].name]
		hd.items[0].qty = sl
		hd.insert(ignore_permissions=True)
		nen._DA_TAO.append((hd.doctype, hd.name))
		if ghi_so:
			hd.submit()
		return hd.name
	if not khong_nem("hoá đơn 2 cái ghi sổ", lambda: lap_hd(2, True)):
		return
	khong_nem("hoá đơn 1 cái để nháp", lambda: lap_hd(1, False))

	ten = so.items[0].name
	la("hàm đọc một nguồn", dat_banh.doc_da_xuat_hd([ten]), {ten: 2.0})
	dong = khong_nem("đọc dòng giữ chỗ", lambda: dat_banh.dong_phieu_dat(ngay)) or []
	la("dòng giữ chỗ mang số đã xuất hoá đơn", [d["da_xuat_hd"] for d in dong if d.get("name") == ten], [2.0])
	tt = khong_nem("đọc dòng refill", lambda: dat_banh.dong_tieu_thu(ngay, add_days(ngay, 1))) or []
	la("dòng refill mang số đã xuất hoá đơn", [d["da_xuat_hd"] for d in tt if d.get("name") == ten], [2.0])
	dung("đếm giữ chỗ chạy không lỗi", khong_nem("đếm giữ chỗ", lambda: dat_banh.dem_giu_cho(getdate(ngay)) or "rỗng") is not None)
