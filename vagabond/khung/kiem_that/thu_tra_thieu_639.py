"""v639 (Codex PR #542 vòng 2): kho nhận xác nhận nhận THIẾU thì máy tự lập phiếu
điều chuyển trả phần thiếu về kho đi, chạy THẬT qua insert() và submit().

Tầng khung chỉ kiểm bằng chứng từ giả nên không biết ERPNext có chấp thuận
phiếu trả (kho, tài khoản chi phí, sổ kho hai bên) hay không. Ca này dựng hai
kho lá tạm trong điểm lưu, nhập hàng vào kho đi, lập phiếu điều chuyển thật,
rồi gọi đúng cửa `nhan_dieu_chuyen.xac_nhan` như app quầy gọi.

Ba ca:
1. Nhận 9/10: phiếu trả ghi sổ thật, Stock Ledger Entry kho nhận -1 và kho đi
   +1, phiếu gốc nối sang phiếu trả, đánh dấu đã xử lý, lời khai Nhận thiếu.
2. Kho nhận đã bán mất phần đó (tồn 0): lõi hoặc hàng rào chặn, KHÔNG có
   phiếu trả ghi sổ, lời khai vẫn Nhận thiếu, việc vẫn treo (chưa xử lý), màn
   nhận được câu lỗi. Lưu ý: khung này tắt rollback thật (điểm lưu), nên ca
   chỉ chốt được "không có phiếu trả đã ghi sổ và phiếu gốc không nối", không
   chốt được bản nháp đã bị rollback dọn.
3. Vừa thiếu A vừa thừa B: phiếu trả chỉ có dòng A, việc KHÔNG đóng (phần thừa
   thủ kho vẫn phải đối chiếu).

Không gửi Zalo thật: cờ vagabond_kiem_that làm kenh_zalo.bao im lặng.
"""
from unittest.mock import patch

import frappe
from frappe.utils import flt

from vagabond import nhan_dieu_chuyen as ndc
from vagabond import xuat_kho
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu


def _luu(d):
	d.flags.ignore_permissions = True
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append((d.doctype, d.name))
	return d


def _kho(ct, nhan):
	tk_kho = frappe.db.get_value("Account", {"company": ct, "account_type": "Stock", "is_group": 0, "disabled": 0}, "name")
	return _luu(frappe.get_doc(dict(doctype="Warehouse", warehouse_name="KT639-%s-%s" % (nhan, frappe.generate_hash(length=6)),
		company=ct, account=tk_kho))).name


def _nhap(ct, ma, kho, so):
	from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
	ph = make_stock_entry(item_code=ma, qty=so, company=ct, to_warehouse=kho, rate=5000, do_not_save=True)
	_luu(ph)
	ph.submit()
	return ph


def _chuyen(ct, dong, kho_di, kho_nhan):
	"""Phiếu điều chuyển THẬT kho đi -> kho nhận, cùng khuôn xuat_kho.luu_dieu_chuyen."""
	se = xuat_kho._phieu_moi("chuyen", ct)
	se.from_warehouse = kho_di
	se.to_warehouse = kho_nhan
	tk = xuat_kho._tk_chi_phi(ct)
	for ma, so in dong:
		se.append("items", {"item_code": ma, "qty": so, "s_warehouse": kho_di, "t_warehouse": kho_nhan, "expense_account": tk})
	_luu(se)
	se.submit()
	return se


def _sle(ten_phieu, ma):
	r = frappe.get_all("Stock Ledger Entry", filters={"voucher_no": ten_phieu, "item_code": ma, "is_cancelled": 0},
		fields=["warehouse", "actual_qty"])
	return sorted((x["warehouse"], flt(x["actual_qty"])) for x in r)


def _ton(ma, kho):
	return flt(frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty"))


def _goc(ten):
	return frappe.db.get_value("Stock Entry", ten,
		["vgb_nhan_tt", "vgb_nhan_da_xu_ly", "vgb_phieu_tra_thieu"], as_dict=True)


def _phieu_tra_cua(goc):
	return frappe.get_all("Stock Entry", filters={"vgb_tra_thieu_cua": goc}, fields=["name", "docstatus", "purpose", "from_warehouse", "to_warehouse"])


def _nen():
	frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 0)
	frappe.clear_document_cache("Stock Settings")
	ct = cong_ty()
	kho_di, kho_nhan = _kho(ct, "di"), _kho(ct, "nhan")
	a = _mon_thu("KT639-A-" + frappe.generate_hash(length=8))
	b = _mon_thu("KT639-B-" + frappe.generate_hash(length=8))
	return ct, kho_di, kho_nhan, a, b


def _xac_nhan(kho_nhan, phieu, dong):
	import json
	with patch.object(xuat_kho, "_duoc_xuat", lambda: True), \
			patch.object(xuat_kho, "_kho_phu_trach", lambda *a, **k: [kho_nhan]):
		return ndc.xac_nhan(phieu, json.dumps(dong), "ca kiểm 639")


def _don():
	frappe.clear_document_cache("Stock Settings")


@ca("v639 nhận thiếu thật: phiếu trả ghi sổ, sổ kho nhận -1 và kho đi +1, phiếu gốc nối sang phiếu trả và đóng việc")
def _tra_that():
	ct, kho_di, kho_nhan, a, _ = _nen()
	try:
		_nhap(ct, a, kho_di, 10)
		goc = khong_nem("điều chuyển 10 A", lambda: _chuyen(ct, [(a, 10)], kho_di, kho_nhan))
		if not goc:
			return
		la("trước xác nhận: kho nhận 10, kho đi 0", (_ton(a, kho_nhan), _ton(a, kho_di)), (10.0, 0.0))
		r = khong_nem("xác nhận nhận 9/10", lambda: _xac_nhan(kho_nhan, goc.name, [{"ma": a, "nhan": 9}]))
		if not r:
			return
		la("trả lời cho màn: Nhận thiếu, có phiếu trả, không lỗi", (r["trang_thai"], bool(r["phieu_tra"]), r["loi_tra"], r["con_thua"]), ("Nhận thiếu", True, "", ""))
		tra = _phieu_tra_cua(goc.name)
		la("đúng một phiếu trả đã ghi sổ, điều chuyển từ kho nhận về kho đi",
			[(x["docstatus"], x["purpose"], x["from_warehouse"], x["to_warehouse"]) for x in tra],
			[(1, "Material Transfer", kho_nhan, kho_di)])
		if tra:
			nen._DA_TAO.append(("Stock Entry", tra[0]["name"]))
			la("tên phiếu trả khớp trả lời", tra[0]["name"], r["phieu_tra"])
			la("sổ kho của phiếu trả: kho nhận -1, kho đi +1", _sle(tra[0]["name"], a), sorted([(kho_nhan, -1.0), (kho_di, 1.0)]))
		la("tồn sau: kho nhận 9, kho đi 1", (_ton(a, kho_nhan), _ton(a, kho_di)), (9.0, 1.0))
		g = _goc(goc.name)
		la("phiếu gốc: lời khai Nhận thiếu, nối phiếu trả, đã xử lý", (g.vgb_nhan_tt, int(g.vgb_nhan_da_xu_ly or 0), g.vgb_phieu_tra_thieu), ("Nhận thiếu", 1, r["phieu_tra"]))
		la("số nhận ghi trên dòng phiếu gốc", flt(frappe.db.get_value("Stock Entry Detail", {"parent": goc.name, "item_code": a}, "vgb_sl_nhan")), 9.0)
	finally:
		_don()


@ca("v639 nhận thiếu nhưng kho nhận đã bán mất phần đó: không có phiếu trả ghi sổ, lời khai vẫn ghi, việc vẫn treo, màn nhận câu lỗi")
def _tra_hong():
	ct, kho_di, kho_nhan, a, _ = _nen()
	try:
		_nhap(ct, a, kho_di, 10)
		goc = khong_nem("điều chuyển 10 A", lambda: _chuyen(ct, [(a, 10)], kho_di, kho_nhan))
		if not goc:
			return
		# Kho nhận bán hết 10 trước khi bấm xác nhận: xuất huỷ 10 khỏi kho nhận.
		se = xuat_kho._phieu_moi("huy", ct)
		se.from_warehouse = kho_nhan
		se.append("items", {"item_code": a, "qty": 10, "s_warehouse": kho_nhan, "expense_account": xuat_kho._tk_chi_phi(ct)})
		khong_nem("xuất hết kho nhận", lambda: (_luu(se), se.submit()))
		la("kho nhận còn 0", _ton(a, kho_nhan), 0.0)
		r = khong_nem("xác nhận nhận 7/10 khi kho nhận trống", lambda: _xac_nhan(kho_nhan, goc.name, [{"ma": a, "nhan": 7}]))
		if not r:
			return
		dung("không có phiếu trả, có câu lỗi cho màn", r["phieu_tra"] == "" and bool(r["loi_tra"]))
		la("không phiếu trả nào ghi sổ nối về phiếu gốc", [x for x in _phieu_tra_cua(goc.name) if x["docstatus"] == 1], [])
		g = _goc(goc.name)
		la("phiếu gốc: lời khai Nhận thiếu, KHÔNG nối, việc vẫn treo", (g.vgb_nhan_tt, int(g.vgb_nhan_da_xu_ly or 0), g.vgb_phieu_tra_thieu or ""), ("Nhận thiếu", 0, ""))
		la("tồn không đổi: kho nhận 0, kho đi 0", (_ton(a, kho_nhan), _ton(a, kho_di)), (0.0, 0.0))
	finally:
		_don()


@ca("v639 vừa thiếu A vừa thừa B: phiếu trả chỉ có dòng A, việc không đóng vì phần thừa còn chờ thủ kho")
def _thieu_a_thua_b():
	ct, kho_di, kho_nhan, a, b = _nen()
	try:
		_nhap(ct, a, kho_di, 10)
		_nhap(ct, b, kho_di, 5)
		goc = khong_nem("điều chuyển 10 A, 5 B", lambda: _chuyen(ct, [(a, 10), (b, 5)], kho_di, kho_nhan))
		if not goc:
			return
		r = khong_nem("xác nhận 8 A, 6 B", lambda: _xac_nhan(kho_nhan, goc.name, [{"ma": a, "nhan": 8}, {"ma": b, "nhan": 6}]))
		if not r:
			return
		dung("có phiếu trả, báo còn thừa B", bool(r["phieu_tra"]) and r["loi_tra"] == "" and b in r["con_thua"] and "thừa 1" in r["con_thua"])
		tra = _phieu_tra_cua(goc.name)
		la("một phiếu trả đã ghi sổ", [x["docstatus"] for x in tra], [1])
		if tra:
			nen._DA_TAO.append(("Stock Entry", tra[0]["name"]))
			la("phiếu trả chỉ có A, 2 cái", _sle(tra[0]["name"], a), sorted([(kho_nhan, -2.0), (kho_di, 2.0)]))
			la("không có dòng B", _sle(tra[0]["name"], b), [])
		g = _goc(goc.name)
		la("phiếu gốc nối phiếu trả nhưng việc KHÔNG đóng", (g.vgb_nhan_tt, int(g.vgb_nhan_da_xu_ly or 0), g.vgb_phieu_tra_thieu), ("Nhận thiếu", 0, r["phieu_tra"]))
		dung("phiếu còn trong danh sách chờ thủ kho", goc.name in frappe.get_all("Stock Entry",
			filters={"vgb_nhan_tt": ndc.THIEU, "vgb_nhan_da_xu_ly": 0, "docstatus": 1}, pluck="name"))
	finally:
		_don()
