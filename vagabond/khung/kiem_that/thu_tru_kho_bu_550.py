"""v550 chạy thật trong điểm lưu: trừ kho từng món và trừ bù khi hàng về.

Dựng lại đúng chuỗi ở District 1 ngày 01/10/2026: hoá đơn bán khi kho điểm
bán chưa có hàng, ghi sổ, rồi phiếu nhập về kho đó. Không gọi thêm hàm nào
ngoài chuỗi của người dùng và của máy (quy tắc 15): việc nền trừ bù được gọi
đúng như hàng đợi sẽ gọi, sau khi đã kiểm phiếu nhập có xếp việc đó.
"""
from unittest.mock import patch

import frappe
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

from vagabond import tru_kho_bu as tb
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_hach_toan_kho_542 import _gl, _hoa_don, _luu, _nen, _sach, _so
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu


def _nhap(ct, kho, ma, sl):
	ph = make_stock_entry(item_code=ma, qty=sl, company=ct, to_warehouse=kho, rate=20000, do_not_save=True)
	_luu(ph)
	ph.submit()
	return ph


def _bu(hd):
	return frappe.get_all("Stock Entry", filters={"vgb_hd_tru_bu": hd, "docstatus": 1},
		fields=["name", "purpose"])


def _ton(ma, kho):
	return frappe.db.get_value("Bin", {"item_code": ma, "warehouse": kho}, "actual_qty") or 0


def _sle_bu(ten):
	return frappe.get_all("Stock Ledger Entry", filters={"voucher_type": "Stock Entry", "voucher_no": ten,
		"is_cancelled": 0}, fields=["item_code", "warehouse", "actual_qty", "stock_value_difference"])


@ca("v550 bán lúc kho chưa có hàng, hàng điều chuyển về sau: phiếu nhập xếp việc, việc nền trừ bù đủ, Nợ 632")
@_sach
def _hang_ve():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	tp = _mon_thu("KT550-TP-" + frappe.generate_hash(length=8))
	hd = _hoa_don(ct, tp, 2)
	hd.submit()
	hd.reload()
	la("vẫn ghi sổ doanh thu", hd.docstatus, 1)
	la("đánh dấu chưa trừ kho", hd.vgb_chua_tru_kho, 1)
	la("chưa có phiếu bù", _bu(hd.name), [])
	la("ô Trừ bù trống", hd.vgb_tru_bu or "", "")
	viec, sau_commit = [], []
	with patch.object(frappe, "enqueue", lambda *a, **k: viec.append((a, k))), \
			patch.object(frappe.db.after_commit, "add", lambda fn: sau_commit.append(fn)):
		_nhap(ct, kho, tp, 5)
		la("trong lúc ghi phiếu nhập chưa chạm hàng đợi", [x for x in viec if x[0] and x[0][0] == "vagabond.tru_kho_bu.tru_bu_kho"], [])
		# Ca kiểm không commit (điểm lưu), nên chạy tay đúng các việc phiếu nhập
		# đã đăng ký cho lúc sau commit, như Frappe sẽ chạy.
		for fn in sau_commit:
			fn()
	viec = [(a, k) for a, k in viec if a and a[0] == "vagabond.tru_kho_bu.tru_bu_kho"]
	la("phiếu nhập xếp đúng một việc trừ bù", [k.get("kho") for a, k in viec], [kho])
	# Hàng đợi chạy đúng lời gọi vừa xếp.
	a, k = viec[0]
	tb.tru_bu_kho(kho=k["kho"])
	hd.reload()
	bu = _bu(hd.name)
	la("một phiếu bù", len(bu), 1)
	la("là phiếu xuất dùng", bu[0].purpose, "Material Issue")
	sle = _sle_bu(bu[0].name)
	la("xuất 2 từ kho điểm bán", [(d.warehouse, d.actual_qty) for d in sle], [(kho, -2)])
	gia = -sum(d.stock_value_difference for d in sle)
	dung("giá vốn dương", gia > 0)
	la("Nợ 632 đúng giá vốn", _so(_gl("Stock Entry", bu[0].name), tk632), round(gia, 2))
	la("hết chưa trừ kho", hd.vgb_chua_tru_kho, 0)
	la("ô Trừ bù", hd.vgb_tru_bu, "Đủ")
	la("tồn còn 3", _ton(tp, kho), 3)
	la("chip", tb.trang_thai_kho(hd.as_dict()), "da_tru_bu")


@ca("v550 trừ từng món ngay lúc ghi sổ: món có hàng trừ ngay, món chưa có chờ; tờ là Một phần")
@_sach
def _tung_mon():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	co = _mon_thu("KT550-CO-" + frappe.generate_hash(length=8))
	chua = _mon_thu("KT550-CH-" + frappe.generate_hash(length=8))
	_nhap(ct, kho, co, 12)
	hd = _hoa_don(ct, co, 2, dong=[(co, 2), (chua, 1)])
	with patch.object(frappe, "enqueue", lambda *a, **k: None):
		hd.submit()
	hd.reload()
	la("hoá đơn không tự trừ kho (thiếu một món)", hd.update_stock, 0)
	la("vẫn chưa trừ kho", hd.vgb_chua_tru_kho, 1)
	la("ô Trừ bù", hd.vgb_tru_bu, "Một phần")
	bu = _bu(hd.name)
	la("một phiếu bù", len(bu), 1)
	la("phiếu chỉ có món có hàng", [(d.item_code, d.actual_qty) for d in _sle_bu(bu[0].name)], [(co, -2)])
	dung("lý do nêu món chờ", chua in (hd.vgb_ly_do_chua_tru_kho or ""))
	la("tồn món có hàng còn 10", _ton(co, kho), 10)
	# Hàng về cho món còn lại: trừ nốt, không trừ lại món đã trừ.
	with patch.object(frappe, "enqueue", lambda *a, **k: None):
		_nhap(ct, kho, chua, 1)
	tb.tru_bu_kho(kho=kho)
	hd.reload()
	la("hai phiếu bù", len(_bu(hd.name)), 2)
	la("món có hàng không bị trừ hai lần", _ton(co, kho), 10)
	la("món về rồi đã trừ", _ton(chua, kho), 0)
	la("đủ", (hd.vgb_chua_tru_kho, hd.vgb_tru_bu), (0, "Đủ"))


@ca("v550 huỷ hoá đơn đã trừ bù: phiếu bù huỷ theo, hàng trở lại kho")
@_sach
def _huy_hd():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	tp = _mon_thu("KT550-HU-" + frappe.generate_hash(length=8))
	hd = _hoa_don(ct, tp, 2)
	hd.submit()
	with patch.object(frappe, "enqueue", lambda *a, **k: None):
		_nhap(ct, kho, tp, 5)
	tb.tru_bu_kho(kho=kho)
	hd.reload()
	ten = _bu(hd.name)[0].name
	hd.cancel()
	la("phiếu bù đã huỷ", frappe.db.get_value("Stock Entry", ten, "docstatus"), 2)
	la("hàng về lại kho", _ton(tp, kho), 5)


@ca("v550 kế toán huỷ tay phiếu bù: hoá đơn về Chưa trừ kho, Gỡ tay; nhịp tự động không trừ lại, bấm tay thì trừ")
@_sach
def _go_tay():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	tp = _mon_thu("KT550-GT-" + frappe.generate_hash(length=8))
	hd = _hoa_don(ct, tp, 1)
	hd.submit()
	with patch.object(frappe, "enqueue", lambda *a, **k: None):
		_nhap(ct, kho, tp, 3)
	tb.tru_bu_kho(kho=kho)
	ten = _bu(hd.name)[0].name
	se = frappe.get_doc("Stock Entry", ten)
	se.cancel()
	hd.reload()
	la("về chưa trừ kho", hd.vgb_chua_tru_kho, 1)
	la("gỡ tay", hd.vgb_tru_bu, "Gỡ tay")
	tb.tru_bu_kho(kho=kho)
	la("nhịp tự động không lập lại", _bu(hd.name), [])
	r = tb.tru_bu(hd.name, nguon="kiem that", tay=True)
	la("bấm tay lập phiếu", len(r.get("phieu") or []), 1)
	hd.reload()
	la("đủ", (hd.vgb_chua_tru_kho, hd.vgb_tru_bu), (0, "Đủ"))


@ca("v550 ghi sổ cuối ngày giờ bán sớm, tồn lúc đó đã bị xuất đi: không trừ theo giờ bán, không lỗi lõi")
@_sach
def _gio_som():
	from frappe.utils import add_days, today
	from vagabond.khung.kiem_that.thu_hach_toan_kho_542 import _bat
	from vagabond import hach_toan_kho as hk
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	hom_qua = add_days(today(), -1)
	_bat(hk.O_BAN_TU, hom_qua)
	tp = _mon_thu("KT550-GS-" + frappe.generate_hash(length=8))
	with patch.object(frappe, "enqueue", lambda *a, **k: None):
		ph = make_stock_entry(item_code=tp, qty=2, company=ct, to_warehouse=kho, rate=20000, do_not_save=True)
		ph.set_posting_time = 1
		ph.posting_date, ph.posting_time = hom_qua, "08:00:00"
		_luu(ph)
		ph.submit()
		ra = make_stock_entry(item_code=tp, qty=2, company=ct, from_warehouse=kho, rate=20000, do_not_save=True)
		ra.set_posting_time = 1
		ra.posting_date, ra.posting_time = hom_qua, "12:00:00"
		_luu(ra)
		ra.submit()
	hd = _hoa_don(ct, tp, 1)
	hd.set_posting_time = 1
	hd.posting_date, hd.posting_time, hd.due_date = hom_qua, "10:00:00", hom_qua
	hd.save()
	lui = []
	goc = hk.co_the_lui
	with patch.object(hk, "co_the_lui", lambda d, loi: lui.append(str(loi)) or goc(d, loi)):
		hd.submit()
	hd.reload()
	la("ghi sổ", hd.docstatus, 1)
	la("không trừ theo giờ bán", hd.update_stock, 0)
	la("chưa trừ kho", hd.vgb_chua_tru_kho, 1)
	# Trước v550: tồn lúc 10:00 còn 2 nên hoá đơn trừ kho, lõi báo âm kho về
	# sau (phiếu xuất 12:00), rồi phải lùi ghi sổ lần hai. Nay không cần lùi.
	la("không phải lùi vì lỗi lõi", lui, [])
	la("tồn không âm", _ton(tp, kho), 0)


@ca("v550 màn Hoá đơn chưa trừ kho đọc đúng từng món: bán, đã trừ, tồn, nhãn; chip chặng đếm đúng")
@_sach
def _man():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	co = _mon_thu("KT550-MC-" + frappe.generate_hash(length=8))
	chua = _mon_thu("KT550-MH-" + frappe.generate_hash(length=8))
	_nhap(ct, kho, co, 12)
	hd = _hoa_don(ct, co, 2, dong=[(co, 2), (chua, 1)])
	with patch.object(frappe, "enqueue", lambda *a, **k: None):
		hd.submit()
	kq = tb.ds_chua_tru_kho(chang="cho")
	o = [x for x in kq["hd"] if x["name"] == hd.name]
	la("có tờ", len(o), 1)
	o = o[0]
	la("chip", o["tt_kho"], "mot_phan")
	la("kho hiện tại", o["kho_nay"], "kho_het")
	mon = {d["ma"]: (d["can"], d["da_tru"], d["ton"], d["nhan"]) for d in o["dong"]}
	la("món có hàng", mon[co], (2, 2, 10, "da_tru"))
	la("món chưa có", mon[chua], (1, 0, 0, "het"))
	dung("đếm chip Đã trừ một phần", kq["dem"]["mot_phan"] >= 1)
	la("có phiếu bù", len(o["phieu"]), 1)


@ca("v550 F2 (Codex 3c93e55): hàng đợi lỗi lúc nhập kho: phiếu nhập vẫn ghi sổ đủ sổ kho, nhịp sau trừ bù đúng một lần")
@_sach
def _hang_doi_loi():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	tp = _mon_thu("KT550-HD-" + frappe.generate_hash(length=8))
	hd = _hoa_don(ct, tp, 2)
	hd.submit()

	def hong(*a, **k):
		raise ConnectionError("KT550 redis down")
	sau_commit = []
	with patch.object(frappe, "enqueue", hong), \
			patch.object(frappe.db.after_commit, "add", lambda fn: sau_commit.append(fn)):
		ph = _nhap(ct, kho, tp, 5)
		loi = None
		try:
			for fn in sau_commit:
				fn()
		except Exception as e:  # noqa: BLE001
			loi = e
	la("việc sau commit không ném", loi, None)
	ph.reload()
	la("phiếu nhập đã ghi sổ", ph.docstatus, 1)
	la("sổ kho phiếu nhập còn nguyên", frappe.db.count("Stock Ledger Entry",
		{"voucher_type": "Stock Entry", "voucher_no": ph.name, "is_cancelled": 0}), 1)
	tb.tru_bu_kho(kho=kho)
	tb.tru_bu_kho(kho=kho)
	la("chỉ một phiếu bù dù quét hai lần", len(_bu(hd.name)), 1)
	la("tồn còn 3", _ton(tp, kho), 3)


@ca("v550 F3 (Codex 3c93e55): khối Kho của tờ đã tự trừ kho hiện Đã trừ đúng số, không báo Đủ để trừ")
@_sach
def _da_tru_truc_tiep():
	ct, kho, tk621, tk154, tk632 = _nen("KT550-")
	tp = _mon_thu("KT550-TT-" + frappe.generate_hash(length=8))
	_nhap(ct, kho, tp, 5)
	hd = _hoa_don(ct, tp, 2)
	hd.submit()
	hd.reload()
	la("tờ tự trừ kho", hd.update_stock, 1)
	o = tb.tt_hoa_don(hd.name)
	la("chip", o["tt_kho"], "da_tru")
	la("món: bán 2, đã trừ 2, nhãn Đã trừ", [(d["can"], d["da_tru"], d["nhan"]) for d in o["dong"]], [(2, 2, "da_tru")])
