"""v542 chạy thật trong điểm lưu: sản xuất qua 621/154, bán trừ kho 632.

Không xuất HĐĐT. Lỗi lõi là ca đỏ. Ngày bật đặt bằng hôm nay trong điểm
lưu của ca (patch chỉ tự bật trên site thật).
"""
import json

import frappe
from frappe.utils import today

from vagabond import diem_ban
from vagabond import hach_toan_kho as hk
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _bom_thu, _nhom_hang, _uom, _lo_thu


def _luu(d):
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append((d.doctype, d.name))
	return d


def _tk(ct, so, ten, root, loai=None):
	ds = frappe.get_all("Account", filters={"company": ct, "account_number": so, "is_group": 0, "disabled": 0}, pluck="name")
	if ds:
		if loai is not None and root == "Asset":
			frappe.db.set_value("Account", ds[0], "account_type", loai)
		return ds[0]
	cha = frappe.db.get_value("Account", {"company": ct, "root_type": root, "is_group": 1}, "name")
	return _luu(frappe.get_doc(dict(doctype="Account", account_name=ten + " KT542", account_number=so,
		company=ct, parent_account=cha, is_group=0, account_type=loai or "", account_currency="VND"))).name


def _nen(tien_to_kho="KT542-"):
	ct = cong_ty()
	for truong, gia_tri in (("enable_serial_and_batch_no_for_item", 1), ("use_serial_batch_fields", 1), ("allow_negative_stock", 0)):
		frappe.db.set_single_value("Stock Settings", truong, gia_tri)
	frappe.clear_document_cache("Stock Settings")
	tk621 = _tk(ct, "621", "Chi phí NVL trực tiếp", "Expense")
	tk154 = _tk(ct, "154", "Chi phí SXKD dở dang", "Asset", "")
	tk632 = _tk(ct, "632", "Giá vốn hàng bán", "Expense", "Cost of Goods Sold")
	tk_kho = frappe.db.get_value("Account", {"company": ct, "account_type": "Stock", "is_group": 0, "disabled": 0}, "name")
	kho = _luu(frappe.get_doc(dict(doctype="Warehouse", warehouse_name=tien_to_kho + frappe.generate_hash(length=9),
		company=ct, account=tk_kho))).name
	for o in (hk.O_BAN_TU, hk.O_SX_TU):
		frappe.db.set_single_value("Vagabond Settings", o, today())
	cfg = diem_ban.ds()
	for d in cfg:
		if not d["quay"]:
			d["kho_tang"] = kho
	frappe.db.set_single_value("Vagabond Settings", diem_ban.TRUONG, json.dumps(cfg, ensure_ascii=False))
	return ct, kho, tk621, tk154, tk632


def _tat():
	"""Trả hai ngày bật về trống và dọn cache Settings.

	Bench CI 30/09 (e8124fb): get_single_value đọc qua cache, rollback điểm
	lưu không dọn cache, nên ngày bật của ca này rò sang 36 ca sau (#243,
	#225...) và làm phiếu Sản xuất của chúng đi luồng 621/154 trên bench
	không có tài khoản 621. Mỗi ca v542 phải tắt lại trong finally.
	"""
	for o in (hk.O_BAN_TU, hk.O_SX_TU):
		frappe.db.set_single_value("Vagabond Settings", o, None)
		# Như kế toán xoá ô ngày trên Desk: không còn giá trị trong Singles.
		frappe.db.sql("delete from `tabSingles` where doctype=%s and field=%s", ("Vagabond Settings", o))
	la("đã tắt ngày bán", hk._moc(hk.O_BAN_TU), None)
	la("đã tắt ngày sản xuất", hk._moc(hk.O_SX_TU), None)
	frappe.clear_document_cache("Vagabond Settings")
	frappe.clear_cache(doctype="Vagabond Settings")


def _bat(o, ngay=None):
	frappe.db.set_single_value("Vagabond Settings", o, ngay or today())
	frappe.clear_document_cache("Vagabond Settings")
	frappe.clear_cache(doctype="Vagabond Settings")


def _sach(ham):
	import functools

	@functools.wraps(ham)
	def boc():
		try:
			return ham()
		finally:
			_tat()
	return boc


def _gl(dt, ten):
	return frappe.get_all("GL Entry", filters={"voucher_type": dt, "voucher_no": ten, "is_cancelled": 0},
		fields=["account", "debit", "credit", "cost_center"])


def _so(gl, tk):
	return round(sum(d.debit - d.credit for d in gl if d.account == tk), 2)


def _san_xuat(ct, kho, sl_nvl=10, sl_tp=5, ghi_so=True):
	from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
	nvl = _mon_thu("KT542-NVL-" + frappe.generate_hash(length=8))
	tp = _mon_thu("KT542-TP-" + frappe.generate_hash(length=8))
	ph = make_stock_entry(item_code=nvl, qty=sl_nvl, company=ct, to_warehouse=kho, rate=12000, do_not_save=True)
	_luu(ph)
	ph.submit()
	bom = _bom_thu(tp, nvl, ct)
	wo = _luu(frappe.get_doc(dict(doctype="Work Order", company=ct, production_item=tp, bom_no=bom.name,
		qty=sl_tp, skip_transfer=1, source_warehouse=kho, wip_warehouse=kho, fg_warehouse=kho)))
	wo.submit()
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry as lam
	sx = frappe.get_doc(lam(wo.name, "Manufacture", qty=sl_tp))
	_luu(sx)
	if ghi_so:
		sx.submit()
	return nvl, tp, sx


@ca("v542 sản xuất thật: Nợ 621 / Có kho nguyên liệu, Nợ kho thành phẩm / Có 154, cân sổ")
@_sach
def _sx_that():
	ct, kho, tk621, tk154, tk632 = _nen()
	nvl, tp, sx = _san_xuat(ct, kho)
	sx.reload()
	gl = _gl("Stock Entry", sx.name)
	gia_nvl = sum(d.amount for d in sx.items if not d.t_warehouse)
	gia_tp = sum(d.amount for d in sx.items if d.is_finished_item)
	dung("giá nguyên liệu dương", gia_nvl > 0)
	la("621 Nợ đúng giá nguyên liệu", _so(gl, tk621), round(gia_nvl, 2))
	la("154 Có đúng giá thành phẩm", _so(gl, tk154), round(-gia_tp, 2))
	la("sổ cân", round(sum(d.debit - d.credit for d in gl), 2), 0)
	dung("không còn tài khoản chênh lệch cũ", all(d.account in (tk621, tk154) or frappe.db.get_value(
		"Account", d.account, "account_type") == "Stock" for d in gl))
	sx.cancel()
	la("huỷ đảo 621", _so(_gl("Stock Entry", sx.name), tk621), 0)


@ca("v542 sản xuất trước ngày bật giữ luồng cũ (không 621)")
@_sach
def _sx_truoc_moc():
	ct, kho, tk621, tk154, tk632 = _nen()
	frappe.db.set_single_value("Vagabond Settings", hk.O_SX_TU, "2099-01-01")
	nvl, tp, sx = _san_xuat(ct, kho)
	la("không chạm 621", _so(_gl("Stock Entry", sx.name), tk621), 0)


def _hoa_don(ct, tp, sl, dong=None):
	from vagabond.hang_tang_so_cai import tai_khoan
	khach = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name")
	hd = frappe.new_doc("Sales Invoice")
	hd.update(dict(company=ct, customer=khach, posting_date=today(), due_date=today(), currency="VND",
		conversion_rate=1, ignore_pricing_rule=1))
	hd.set("taxes", [])
	hd.taxes_and_charges = None
	hd.append("taxes", {"charge_type": "On Net Total", "account_head": tai_khoan(ct, "33311", "Liability"),
		"rate": 8, "description": "VAT ca kiểm v542", "included_in_print_rate": 1})
	for ma, so in (dong or [(tp, sl)]):
		hd.append("items", {"item_code": ma, "qty": so, "rate": 108000})
	hd.flags.ignore_permissions = True
	_luu(hd)
	hd.reload()
	hd.flags.ignore_permissions = True
	return hd


@ca("v542 bán đủ hàng: trừ kho điểm bán, Nợ 632 bằng giá vốn sổ kho")
@_sach
def _ban_du():
	ct, kho, tk621, tk154, tk632 = _nen()
	nvl, tp, sx = _san_xuat(ct, kho)
	hd = _hoa_don(ct, tp, 2)
	la("nháp đã bật trừ kho", hd.update_stock, 1)
	la("cờ bán trừ kho", hd.vgb_tru_kho_ban, 1)
	hd.submit()
	hd.reload()
	la("ghi sổ", hd.docstatus, 1)
	la("không đánh dấu thiếu", hd.vgb_chua_tru_kho, 0)
	sle = frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Sales Invoice", "voucher_no": hd.name,
		"is_cancelled": 0}, fields=["warehouse", "actual_qty", "stock_value_difference"])
	la("xuất 2", sum(d.actual_qty for d in sle), -2)
	dung("đúng kho điểm bán", all(d.warehouse == kho for d in sle))
	gia = -sum(d.stock_value_difference for d in sle)
	dung("giá vốn dương", gia > 0)
	la("632 Nợ đúng giá vốn", _so(_gl("Sales Invoice", hd.name), tk632), round(gia, 2))


@ca("v542 bán thiếu hàng: vẫn ghi sổ doanh thu, không trừ kho, đánh dấu Chưa trừ kho kèm lý do")
@_sach
def _ban_thieu():
	ct, kho, tk621, tk154, tk632 = _nen()
	nvl, tp, sx = _san_xuat(ct, kho)
	hd = _hoa_don(ct, tp, 50)
	hd.submit()
	hd.reload()
	la("vẫn ghi sổ", hd.docstatus, 1)
	la("không trừ kho", hd.update_stock, 0)
	la("đánh dấu chưa trừ kho", hd.vgb_chua_tru_kho, 1)
	dung("lý do nêu món thiếu", tp in (hd.vgb_ly_do_chua_tru_kho or ""))
	la("không sổ kho", frappe.db.count("Stock Ledger Entry", {"voucher_type": "Sales Invoice", "voucher_no": hd.name}), 0)
	la("không 632", _so(_gl("Sales Invoice", hd.name), tk632), 0)


@ca("v542 lõi báo lỗi kho lúc ghi sổ: lùi một lần, ghi sổ không trừ kho")
@_sach
def _ban_loi_loi():
	from unittest.mock import patch
	ct, kho, tk621, tk154, tk632 = _nen()
	nvl, tp, sx = _san_xuat(ct, kho)
	hd = _hoa_don(ct, tp, 1)
	lop = type(hd)
	goc = lop.update_stock_ledger
	def hong(self, *a, **kw):
		if self.update_stock:
			raise frappe.ValidationError("KT542 lõi kho giả")
		return goc(self, *a, **kw)
	with patch.object(lop, "update_stock_ledger", hong):
		hd.submit()
	hd.reload()
	la("ghi sổ", hd.docstatus, 1)
	la("không trừ kho", hd.update_stock, 0)
	la("đánh dấu", hd.vgb_chua_tru_kho, 1)
	dung("lý do có lỗi lõi", "KT542" in (hd.vgb_ly_do_chua_tru_kho or ""))


@ca("v542 Codex #395 F5: nháp lưu trước ngày bật, ghi sổ sau khi bật mà lõi lỗi kho: vẫn lùi ghi sổ không trừ kho")
@_sach
def _nhap_cu_loi_loi():
	from unittest.mock import patch
	ct, kho, tk621, tk154, tk632 = _nen()
	nvl, tp, sx = _san_xuat(ct, kho)
	# Bench 7fc4d84: đặt None mà không dọn cache thì ngày cũ còn đọc được,
	# nháp "trước ngày bật" vẫn trừ kho. Tắt và bật đều phải qua dọn cache.
	_tat()
	hd = _hoa_don(ct, tp, 1)
	la("nháp cũ chưa bật trừ kho", hd.update_stock, 0)
	la("nháp cũ chưa có cờ", hd.vgb_tru_kho_ban, 0)
	_bat(hk.O_BAN_TU)
	lop = type(hd)
	goc = lop.update_stock_ledger
	def hong(self, *a, **kw):
		if self.update_stock:
			raise frappe.ValidationError("KT542 F5 lõi kho giả")
		return goc(self, *a, **kw)
	with patch.object(lop, "update_stock_ledger", hong):
		hd.submit()
	hd.reload()
	la("ghi sổ", hd.docstatus, 1)
	la("không trừ kho", hd.update_stock, 0)
	la("đánh dấu", hd.vgb_chua_tru_kho, 1)
	dung("lý do có lỗi lõi", "KT542 F5" in (hd.vgb_ly_do_chua_tru_kho or ""))


def _tt_bep(ct, ten="Bếp Baker"):
	abbr = frappe.get_cached_value("Company", ct, "abbr")
	day_du = "%s - %s" % (ten, abbr)
	if frappe.db.exists("Cost Center", day_du):
		return day_du
	goc = frappe.db.get_value("Cost Center", {"company": ct, "is_group": 1, "parent_cost_center": ["in", ["", None]]}, "name") \
		or frappe.db.get_value("Cost Center", {"company": ct, "is_group": 1}, "name")
	return _luu(frappe.get_doc(dict(doctype="Cost Center", cost_center_name=ten, company=ct,
		parent_cost_center=goc, is_group=0))).name


@ca("v542 Codex #397: nháp Sản xuất lưu lúc bật, kế toán xoá ngày rồi ghi sổ: về luồng cũ, không 621/154, không trung tâm bếp")
@_sach
def _sx_tat_giua_chung():
	ct, kho, tk621, tk154, tk632 = _nen("Baker - KT542-")
	tt_bep = _tt_bep(ct)
	nvl, tp, sx = _san_xuat(ct, kho, ghi_so=False)
	sx.reload()
	dung("nháp đã mang 621", any(d.expense_account == tk621 for d in sx.items))
	dung("nháp đã mang 154", any(d.expense_account == tk154 for d in sx.items))
	dung("nháp đã mang trung tâm bếp", any(d.cost_center == tt_bep for d in sx.items))
	_tat()
	sx.reload()
	sx.submit()
	sx.reload()
	dung("dòng không còn 621/154", all(d.expense_account not in (tk621, tk154) for d in sx.items))
	dung("dòng không còn trung tâm bếp", all(d.cost_center != tt_bep for d in sx.items))
	# Bench 8ee08fb: luồng cũ trên bench có thể ra 0 dòng sổ cái (nguyên liệu và
	# thành phẩm cùng một kho, cùng tài khoản kho, lõi gộp Nợ/Có triệt tiêu), nên
	# không đòi "có sổ cái". Chốt ở dòng phiếu (nguồn của sổ cái) và ở sổ cái nếu có.
	gl = _gl("Stock Entry", sx.name)
	la("không 621", _so(gl, tk621), 0)
	la("không 154", _so(gl, tk154), 0)
	dung("sổ cái không mang trung tâm bếp", all(d.cost_center != tt_bep for d in gl))
	la("sổ cân", round(sum(d.debit - d.credit for d in gl), 2), 0)


def _nhap_lo(ct, kho, ma, sl):
	from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
	lo = _lo_thu(ma).name
	ph = make_stock_entry(item_code=ma, qty=sl, company=ct, to_warehouse=kho, rate=20000, do_not_save=True)
	for d in ph.items:
		d.batch_no = lo
		d.use_serial_batch_fields = 1
	_luu(ph)
	ph.submit()
	return lo


def _bo_san_pham(ct, tp, sl=2):
	ma = "KT542-BO-" + frappe.generate_hash(length=8)
	it = frappe.new_doc("Item")
	it.update(dict(item_code=ma, item_name="Ca kiem bo %s" % ma, item_group=_nhom_hang(), stock_uom=_uom(), is_stock_item=0))
	it.flags.ignore_permissions = True
	_luu(it)
	pb = frappe.get_doc(dict(doctype="Product Bundle", new_item_code=ma, items=[{"item_code": tp, "qty": sl}]))
	pb.flags.ignore_permissions = True
	_luu(pb)
	return ma


@ca("v542 Codex #397: bộ sản phẩm có thành phần theo lô, đủ hàng: trừ kho thành phần theo lô, ghi 632, không đánh dấu")
@_sach
def _bo_thanh_phan_lo():
	ct, kho, tk621, tk154, tk632 = _nen()
	tp = _mon_thu("KT542-TPL-" + frappe.generate_hash(length=8), theo_lo=1)
	lo = _nhap_lo(ct, kho, tp, 5)
	dung("có lô nhập", bool(lo))
	bo = _bo_san_pham(ct, tp, 2)
	hd = _hoa_don(ct, bo, 1)
	la("nháp bật trừ kho", hd.update_stock, 1)
	dung("có dòng thành phần", any(p.item_code == tp for p in hd.packed_items))
	hd.submit()
	hd.reload()
	la("ghi sổ", hd.docstatus, 1)
	la("vẫn trừ kho", hd.update_stock, 1)
	la("không đánh dấu", hd.vgb_chua_tru_kho, 0)
	sle = frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Sales Invoice", "voucher_no": hd.name,
		"item_code": tp, "is_cancelled": 0}, fields=["actual_qty", "serial_and_batch_bundle"])
	la("một dòng sổ kho thành phần", len(sle), 1)
	la("trừ 2", sle[0].actual_qty if sle else None, -2)
	dung("sổ kho có gói lô", bool(sle and sle[0].serial_and_batch_bundle))
	dung("632 có giá vốn", _so(_gl("Sales Invoice", hd.name), tk632) > 0)


@ca("v542 Codex #397: dòng sau thiếu lô còn dùng thì lùi không trừ kho và không để lại gói lô mồ côi của dòng trước")
@_sach
def _khong_goi_mo_coi():
	ct, kho, tk621, tk154, tk632 = _nen()
	a = _mon_thu("KT542-LA-" + frappe.generate_hash(length=8), theo_lo=1)
	b = _mon_thu("KT542-LB-" + frappe.generate_hash(length=8), theo_lo=1)
	_nhap_lo(ct, kho, a, 5)
	lo_b = _nhap_lo(ct, kho, b, 5)
	frappe.db.set_value("Batch", lo_b, "disabled", 1)
	frappe.clear_document_cache("Batch", lo_b)
	hd = _hoa_don(ct, a, 1, dong=[(a, 1), (b, 1)])
	la("nháp bật trừ kho", hd.update_stock, 1)
	hd.submit()
	hd.reload()
	la("ghi sổ", hd.docstatus, 1)
	la("lùi không trừ kho", hd.update_stock, 0)
	la("đánh dấu", hd.vgb_chua_tru_kho, 1)
	la("không còn gói lô gắn hoá đơn", frappe.db.count("Serial and Batch Bundle", {"voucher_no": hd.name}), 0)
	la("không sổ kho", frappe.db.count("Stock Ledger Entry", {"voucher_no": hd.name, "is_cancelled": 0}), 0)


@ca("v542 Codex #397: đang tắt 621/154, kế toán tự chọn 621 cho dòng nguyên liệu: ghi sổ giữ 621")
@_sach
def _sx_tay_621_khi_tat():
	ct, kho, tk621, tk154, tk632 = _nen()
	_tat()
	nvl, tp, sx = _san_xuat(ct, kho, ghi_so=False)
	sx.reload()
	for d in sx.items:
		if d.s_warehouse and not d.t_warehouse:
			d.expense_account = tk621
	sx.save()
	sx.submit()
	sx.reload()
	dung("dòng nguyên liệu giữ 621 kế toán chọn", all(d.expense_account == tk621 for d in sx.items if d.s_warehouse and not d.t_warehouse))
	dung("máy không gắn dấu", not any(d.get(hk.O_MAY_GAN) for d in sx.items))
	gia_nvl = sum(d.amount for d in sx.items if d.s_warehouse and not d.t_warehouse)
	la("621 Nợ đúng giá nguyên liệu", _so(_gl("Stock Entry", sx.name), tk621), round(gia_nvl, 2))
