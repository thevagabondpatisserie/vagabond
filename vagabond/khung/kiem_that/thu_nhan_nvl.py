# -*- coding: utf-8 -*-
"""Ca kiểm TÍCH HỢP cho luồng nhận nguyên liệu theo phiếu yêu cầu (#206, PR #222).

Câu hỏi chỉ tầng này trả lời được
---------------------------------
`lo_hang.gan_lo` đắp lại các dòng của một Stock Entry Material Transfer ở
`before_validate`, giữa `insert` và `submit`. Bộ kiểm tầng khung đã chốt
phép chia lô, nhưng chưa ai hỏi ERPNext: nó có NHẬN các dòng đã tách không,
sổ kho sau ghi sổ có đúng từng lô không, và số "đã chuyển" trên phiếu yêu
cầu có nhảy không. Codex nêu đúng chỗ này trên PR #222 (06/09/2026). Vụ 3311
ngày 21/08/2026 chính là kiểu lỗi mà chỉ `submit()` thật mới lộ.

Cộng thêm lỗi Codex tái hiện bằng giả lập: dòng người chọn lô bằng gói
Serial and Batch Bundle không được trừ khỏi túi, nên lô A tồn 60, gói lấy
40, dòng máy xin 30 vẫn được cấp trọn 30 từ lô A. Ở đây dựng đúng cảnh đó
với gói THẬT của ERPNext rồi ghi sổ, và đọc lại tồn từng lô.

Mọi ca chạy trong điểm lưu của `nen.py`: mã hàng, kho, lô, phiếu nhập, phiếu
yêu cầu, phiếu chuyển, sổ kho, gói lô đều lùi lại hết sau ca.

VỀ "HAI YÊU CẦU ĐỒNG THỜI": một phiên Frappe có MỘT kết nối, nên ở đây chỉ
kiểm được lần gửi LẠI (nối tiếp): phiếu thứ hai cho cùng dòng yêu cầu đã
chuyển đủ phải bị ERPNext chặn ở `update_completed_qty` (erpnext/stock/
doctype/material_request/material_request.py, "cannot be greater than
requested quantity"). Hai kết nối cùng lúc KHÔNG chứng minh được ở đây và
được nói rõ trong tên ca.
"""

import frappe
from frappe.utils import add_days, nowdate, nowtime

from vagabond import lo_hang
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import (
	ca, cong_ty, dung, khong_nem, la, mot_kho,
)


# ------------------------------------------------------------ dựng dữ liệu


def _uom():
	for t in ("Gram", "Nos", "Cái", "Unit"):
		if frappe.db.exists("UOM", t):
			return t
	return frappe.db.get_value("UOM", {}, "name")


def _nhom_hang():
	for t in ("Nguyên vật liệu", "All Item Groups"):
		if frappe.db.exists("Item Group", t):
			return t
	return frappe.db.get_value("Item Group", {"is_group": 0}, "name")


def _mon_theo_lo(ma):
	if frappe.db.exists("Item", ma):
		return ma
	it = frappe.new_doc("Item")
	it.item_code = ma
	it.item_name = "Ca kiem tich hop %s" % ma
	it.item_group = _nhom_hang()
	it.stock_uom = _uom()
	it.is_stock_item = 1
	it.has_batch_no = 1
	# Lo do ca kiem tu tao voi so ro rang, khong de ERPNext tu de lo moi.
	it.create_new_batch = 0
	it.valuation_rate = 1
	it.flags.ignore_permissions = True
	it.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Item", it.name))
	return it.name


def _lo(ma, ten, han):
	if frappe.db.exists("Batch", ten):
		return ten
	b = frappe.new_doc("Batch")
	b.item = ma
	b.batch_id = ten
	b.expiry_date = han
	b.flags.ignore_permissions = True
	b.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Batch", b.name))
	return b.name


def _kho_nhan(cty):
	"""Một kho lá thứ hai để làm kho nhận, tạo trong điểm lưu."""
	goc = frappe.db.get_value("Warehouse", {"company": cty, "is_group": 1}, "name", order_by="lft asc")
	ten = "Kiem That Nhan"
	tat = frappe.db.get_value("Company", cty, "abbr")
	day_du = "%s - %s" % (ten, tat)
	if frappe.db.exists("Warehouse", day_du):
		return day_du
	k = frappe.new_doc("Warehouse")
	k.warehouse_name = ten
	k.company = cty
	k.parent_warehouse = goc
	k.flags.ignore_permissions = True
	k.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Warehouse", k.name))
	return k.name


def _nhap(ma, kho, cac_lo, cty):
	"""Phiếu nhập kho (Material Receipt) có lô rõ ràng, ghi sổ thật."""
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Material Receipt"
	se.stock_entry_type = "Material Receipt"
	se.set_posting_time = 1
	se.posting_date = nowdate()
	se.posting_time = nowtime()
	for lo, so in cac_lo:
		se.append("items", {
			"item_code": ma, "qty": so, "t_warehouse": kho, "batch_no": lo,
			"use_serial_batch_fields": 1, "basic_rate": 1, "allow_zero_valuation_rate": 1,
		})
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	se.submit()
	return se


def _yeu_cau(ma, tu_kho, den_kho, so, cty):
	mr = frappe.new_doc("Material Request")
	mr.company = cty
	mr.material_request_type = "Material Transfer"
	mr.schedule_date = nowdate()
	mr.set_from_warehouse = tu_kho
	mr.set_warehouse = den_kho
	mr.append("items", {
		"item_code": ma, "qty": so, "schedule_date": nowdate(),
		"warehouse": den_kho, "from_warehouse": tu_kho, "uom": _uom(), "conversion_factor": 1,
	})
	mr.flags.ignore_permissions = True
	mr.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Material Request", mr.name))
	mr.submit()
	return mr


def _goi_xuat(ma, kho, cac_lo, cty):
	"""Một gói Serial and Batch Bundle XUẤT, để nháp, đúng đường Desk tạo.

	erpnext/stock/serial_batch_bundle.py `SerialBatchCreation`: truyền
	`batches` thì nó ghi đúng các lô đó, không tự chọn.
	"""
	from erpnext.stock.serial_batch_bundle import SerialBatchCreation

	tong = sum(float(s) for s in cac_lo.values())
	sb = SerialBatchCreation({
		"item_code": ma, "warehouse": kho, "company": cty,
		"type_of_transaction": "Outward", "voucher_type": "Stock Entry",
		"qty": tong, "batches": dict(cac_lo), "do_not_submit": 1,
		"posting_date": nowdate(), "posting_time": nowtime(),
	})
	doc = sb.make_serial_and_batch_bundle()
	nen._DA_TAO.append(("Serial and Batch Bundle", doc.name))
	return doc


def _chuyen(ma, tu_kho, den_kho, dong, cty):
	"""Phiếu chuyển kho như app gửi: insert rồi submit tách hai bước."""
	se = frappe.new_doc("Stock Entry")
	se.company = cty
	se.purpose = "Material Transfer"
	se.stock_entry_type = "Material Transfer"
	se.set_posting_time = 1
	se.posting_date = nowdate()
	se.posting_time = nowtime()
	se.from_warehouse = tu_kho
	se.to_warehouse = den_kho
	for d in dong:
		x = {"item_code": ma, "s_warehouse": tu_kho, "t_warehouse": den_kho, "uom": _uom(), "conversion_factor": 1}
		x.update(d)
		se.append("items", x)
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Stock Entry", se.name))
	return se


def _ton_lo(lo, kho):
	from erpnext.stock.doctype.batch.batch import get_batch_qty

	return float(get_batch_qty(batch_no=lo, warehouse=kho) or 0)


def _ton_kho(ma, kho):
	return float(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty") or 0)


def _bat_serial_batch_neu_chua():
	"""Bật "Activate Serial / Batch No for Item" trong Stock Settings nếu
	site chưa bật. THIẾT LẬP TOÀN CỤC, không phải mặc định tắt vô lý: một
	site Vagabond thật (quản lý lô dày đặc) luôn bật cờ này, nhưng site
	trống dựng cho kiểm thử tích hợp thì Stock Settings còn nguyên mặc định
	của ERPNext (tắt). Thiếu nó thì cả `_nhap` lẫn `_goi_xuat` đều bị chặn
	ngay từ ERPNext với câu "Please check the 'Activate Serial and Batch No
	for Item' checkbox in the Stock Settings...", trước khi chạm gì đến
	`lo_hang`. Đặt ở ĐÂY, bên trong điểm lưu của ca kiểm, nên tự lùi lại sau
	mỗi ca, không đọng lại trên site thật.
	"""
	if not frappe.db.get_single_value("Stock Settings", "enable_serial_and_batch_no_for_item"):
		frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)


def _canh():
	"""Dựng cảnh chung: lô A 60 (hết hạn sớm), lô B 100, phiếu yêu cầu 30."""
	_bat_serial_batch_neu_chua()
	cty = cong_ty()
	tu_kho = mot_kho(cty)
	den_kho = _kho_nhan(cty)
	dung("có kho xuất", bool(tu_kho))
	dung("có kho nhận khác kho xuất", bool(den_kho) and den_kho != tu_kho)
	ma = _mon_theo_lo("KTTH-NVL-CHON-LO")
	lo_a = _lo(ma, "KTTH-LO-A", add_days(nowdate(), 10))
	lo_b = _lo(ma, "KTTH-LO-B", add_days(nowdate(), 30))
	khong_nem("nhập kho lô A 60 và lô B 100", lambda: _nhap(ma, tu_kho, [(lo_a, 60), (lo_b, 100)], cty))
	la("tồn lô A sau nhập", _ton_lo(lo_a, tu_kho), 60.0)
	la("tồn lô B sau nhập", _ton_lo(lo_b, tu_kho), 100.0)
	mr = khong_nem("lập phiếu yêu cầu chuyển 30", lambda: _yeu_cau(ma, tu_kho, den_kho, 30, cty))
	return cty, tu_kho, den_kho, ma, lo_a, lo_b, mr


# ------------------------------------------------------------ các ca


@ca("nhan nvl: chuyen kho theo phieu yeu cau, may chon lo, ERPNext ghi so duoc va so da chuyen tren MR nhay")
def _chuyen_binh_thuong():
	cty, tu_kho, den_kho, ma, lo_a, lo_b, mr = _canh()
	if not mr:
		return
	se = khong_nem("insert phiếu chuyển 30 không kèm lô", lambda: _chuyen(ma, tu_kho, den_kho, [
		{"qty": 30, "material_request": mr.name, "material_request_item": mr.items[0].name},
	], cty))
	if not se:
		return
	# gan_lo chay o before_validate cua insert: dong 30 phai da mang lo A (het han som hon).
	la("sau insert có đúng một dòng", len(se.items), 1)
	la("máy chọn lô hết hạn sớm trước", se.items[0].batch_no, lo_a)
	la("dòng vẫn trỏ về phiếu yêu cầu", se.items[0].material_request, mr.name)
	la("dòng vẫn trỏ về dòng yêu cầu", se.items[0].material_request_item, mr.items[0].name)
	khong_nem("submit phiếu chuyển", se.submit)
	la("phiếu đã ghi sổ", int(frappe.db.get_value("Stock Entry", se.name, "docstatus") or 0), 1)
	la("lô A còn 30 ở kho xuất", _ton_lo(lo_a, tu_kho), 30.0)
	la("lô A có 30 ở kho nhận", _ton_lo(lo_a, den_kho), 30.0)
	la("lô B nguyên 100", _ton_lo(lo_b, tu_kho), 100.0)
	sle = frappe.get_all("Stock Ledger Entry", filters={"voucher_no": se.name, "is_cancelled": 0},
		fields=["warehouse", "actual_qty"])
	la("sổ kho: một dòng trừ kho xuất 30", sum(float(x.actual_qty) for x in sle if x.warehouse == tu_kho), -30.0)
	la("sổ kho: một dòng cộng kho nhận 30", sum(float(x.actual_qty) for x in sle if x.warehouse == den_kho), 30.0)
	mr.reload()
	la("số đã chuyển trên dòng yêu cầu", float(mr.items[0].ordered_qty or 0), 30.0)
	la("phiếu yêu cầu chuyển đủ 100%", float(mr.per_ordered or 0), 100.0)


@ca("nhan nvl: goi Serial and Batch Bundle lay 40 cua lo A 60, dong may xin 30 chi con 20 tu A, ghi so khong am lo")
def _goi_bundle_khong_an_trung():
	cty, tu_kho, den_kho, ma, lo_a, lo_b, mr = _canh()
	if not mr:
		return
	goi = khong_nem("dựng gói xuất 40 của lô A", lambda: _goi_xuat(ma, tu_kho, {lo_a: 40}, cty))
	if not goi:
		return
	# Doc goi bang dung ham may chu dang dung trong gan_lo.
	la("_lo_trong_goi đọc ra 40 của lô A", lo_hang._lo_trong_goi(goi.name), {lo_a: 40.0})
	se = khong_nem("insert phiếu chuyển: dòng gói 40 + dòng máy 30", lambda: _chuyen(ma, tu_kho, den_kho, [
		{"qty": 40, "serial_and_batch_bundle": goi.name},
		{"qty": 30, "material_request": mr.name, "material_request_item": mr.items[0].name},
	], cty))
	if not se:
		return
	dong_goi = [d for d in se.items if d.serial_and_batch_bundle]
	dong_may = [d for d in se.items if not d.serial_and_batch_bundle]
	la("dòng gói giữ nguyên", [(float(d.qty), d.serial_and_batch_bundle) for d in dong_goi], [(40.0, goi.name)])
	la("dòng máy tách thành hai lô", sorted((d.batch_no, float(d.qty)) for d in dong_may),
		sorted([(lo_a, 20.0), (lo_b, 10.0)]))
	khong_nem("submit phiếu chuyển có gói", se.submit)
	la("phiếu đã ghi sổ", int(frappe.db.get_value("Stock Entry", se.name, "docstatus") or 0), 1)
	la("lô A ở kho xuất về đúng 0, KHÔNG âm", _ton_lo(lo_a, tu_kho), 0.0)
	la("lô B ở kho xuất còn 90", _ton_lo(lo_b, tu_kho), 90.0)
	la("lô A ở kho nhận 60", _ton_lo(lo_a, den_kho), 60.0)
	la("lô B ở kho nhận 10", _ton_lo(lo_b, den_kho), 10.0)
	la("tồn kho xuất 160 - 70", _ton_kho(ma, tu_kho), 90.0)
	la("tồn kho nhận 70", _ton_kho(ma, den_kho), 70.0)
	mr.reload()
	la("chỉ dòng máy trỏ về MR nên đã chuyển là 30", float(mr.items[0].ordered_qty or 0), 30.0)


@ca("nhan nvl: gui LAI cung dong yeu cau da chuyen du thi ERPNext chan, so kho va MR khong doi (KHONG chung minh duoc hai ket noi cung luc)")
def _gui_lai_bi_chan():
	cty, tu_kho, den_kho, ma, lo_a, lo_b, mr = _canh()
	if not mr:
		return
	se1 = khong_nem("phiếu chuyển lần một", lambda: _chuyen(ma, tu_kho, den_kho, [
		{"qty": 30, "material_request": mr.name, "material_request_item": mr.items[0].name},
	], cty))
	if not se1:
		return
	khong_nem("submit lần một", se1.submit)
	so_sle = frappe.db.count("Stock Ledger Entry", {"is_cancelled": 0})
	se2 = khong_nem("insert phiếu chuyển lần hai (gửi lại)", lambda: _chuyen(ma, tu_kho, den_kho, [
		{"qty": 30, "material_request": mr.name, "material_request_item": mr.items[0].name},
	], cty))
	if not se2:
		return
	loi = ""
	# Điểm lưu RIÊNG ngay trước lần submit CỐ Ý cho hỏng. `Stock Entry.submit()`
	# đã ghi docstatus=1 vào transaction trước khi hook on_submit của ERPNext
	# (update_completed_and_requested_qty) ném lỗi; ngoài vòng đời request
	# HTTP bình thường không có ai tự rollback phần dở dang đó. Không lùi
	# riêng ở đây thì các phép so sánh NGAY BÊN DƯỚI (docstatus, sổ kho, tồn
	# kho) đọc phải trạng thái nửa vời của phiếu vừa nổ, dù bản thân
	# `update_completed_and_requested_qty` đã chặn đúng như mong đợi. Đây là
	# điểm lưu của CA KIỂM (khác DIEM_LUU của nen.py, tự lùi lại ở cuối ca).
	sp = "vagabond_kiem_that_gui_lai"
	frappe.db.savepoint(sp)
	try:
		se2.submit()
	except Exception as e:
		loi = nen.cau_loi(e)
		frappe.db.rollback(save_point=sp)
	dung("lần hai bị chặn, không ghi sổ: " + loi, bool(loi))
	la("phiếu hai không ở trạng thái đã ghi sổ", int(frappe.db.get_value("Stock Entry", se2.name, "docstatus") or 0), 0)
	la("sổ kho không có thêm dòng", frappe.db.count("Stock Ledger Entry", {"is_cancelled": 0}), so_sle)
	mr.reload()
	la("số đã chuyển vẫn 30", float(mr.items[0].ordered_qty or 0), 30.0)
	la("tồn kho xuất vẫn 130", _ton_kho(ma, tu_kho), 130.0)
