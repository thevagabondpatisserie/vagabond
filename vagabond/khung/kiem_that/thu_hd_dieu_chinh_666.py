"""v666: hoá đơn ĐIỀU CHỈNH giảm của nhà cung cấp ghi sổ trên sổ THẬT.

Ca thật (anh Việt 17/11/2026): Gourmet Partner hoá đơn gốc 33387 sai giá bơ
(2 Thùng thành 9.200.000 đ), hoá đơn điều chỉnh giảm 39339 (-1.200.000 đ),
phiếu nhập PNK-2026-00803 nhận 8.000.000 đ. Bản giả ở tầng khung không biết
ERPNext có nhận tờ âm gắn tờ gốc (return_against) không, có kiểm lượng trả
theo đơn vị kho không, và sổ cái ra sao. Ca này dựng đúng chuỗi trên một
phiếu nhập ảo rồi gọi CHÍNH cửa ghi sổ của màn Đối chiếu.

Mọi chứng từ lùi về điểm lưu (nen.py); không gọi nhà cung cấp HĐĐT.
"""

import frappe
from frappe.utils import flt, today

from vagabond import doi_chieu_mua, hd_dieu_chinh
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _luu, _phieu

TEN = "Bơ thử v666"
GOC, DIEU_CHINH, PNK = 9200000, -1200000, 8000000


def _mi(so, trang_thai, mst, chi_tiet, tong, hd_goc=""):
	return _luu(frappe.get_doc({
		"doctype": "MInvoice Invoice", "ma_hd_id": "kiem-666-" + frappe.generate_hash(length=20),
		"loai": "Đầu vào", "ky_hieu": "C26KTH", "so_hd": so, "ngay_lap": today(),
		"nguoi_mua_ban": "Kiểm thử trong điểm lưu v666", "mst_doi_tac": mst,
		"tien_truoc_thue": tong, "tien_thue": 0, "tong_tien": tong, "trang_thai": trang_thai,
		"hd_goc": hd_goc, "chi_tiet": frappe.as_json(chi_tiet),
	}))


def _dung(ghi_so_goc=True):
	"""(phiếu nhập, tờ gốc, tờ điều chỉnh) hoặc None."""
	p = khong_nem("phiếu nhập 2 x 4.000.000", lambda: nen.phieu_nhap_ao(2, PNK / 2))
	if not p:
		return None
	d = p.items[0]
	so = int(frappe.generate_hash(length=8), 16)
	mst = "03" + str(so % 10 ** 8).zfill(8)
	so_goc = str(30000 + so % 60000)
	g_goc = _mi(so_goc, "Gốc", mst, [{"ten": TEN, "sluong": 2, "dgia": GOC / 2, "thtien": GOC, "dvtinh": d.uom}], GOC)
	goc = _phieu([(TEN, 2, GOC / 2)], d.item_code, p.supplier)
	goc.items[0].update({"uom": d.uom, "conversion_factor": d.conversion_factor, "warehouse": d.warehouse,
		"purchase_receipt": p.name, "pr_detail": d.name})
	goc.custom_minvoice_id = g_goc.name
	goc.custom_trang_thai_hddt = "Gốc"
	if not khong_nem("lưu tờ gốc", lambda: _luu(goc)):
		return None
	if ghi_so_goc:
		khong_nem("ghi sổ tờ gốc (giá hoá đơn cao hơn phiếu nhập)", lambda: goc.submit())
		goc.reload()
		la("tờ gốc đã ghi sổ", goc.docstatus, 1)
	g_dc = _mi(str(int(so_goc) + 1), "Điều chỉnh", mst,
		[{"ten": TEN, "sluong": -2, "dgia": DIEU_CHINH / 2, "thtien": DIEU_CHINH, "dvtinh": d.uom}], DIEU_CHINH,
		hd_goc="KH C26KTH - So %s - Ngay %s" % (so_goc, today()))
	dc = _phieu([(TEN, -2, -DIEU_CHINH / 2)], d.item_code, p.supplier)
	dc.is_return = 1
	dc.items[0].update({"uom": d.uom, "conversion_factor": d.conversion_factor, "warehouse": d.warehouse})
	dc.custom_minvoice_id = g_dc.name
	dc.custom_trang_thai_hddt = "Điều chỉnh"
	if not khong_nem("lưu tờ điều chỉnh", lambda: _luu(dc)):
		return None
	dc.reload()
	return p, goc, dc


def _so_du(tk, *docs):
	return round(sum(flt(g.debit) - flt(g.credit) for doc in docs for g in nen.so_cai_cua(doc)
		if g.account == tk), 2)


@ca("v666 ghi sổ tờ điều chỉnh giảm vào tờ gốc trên sổ thật: phiếu nợ gắn tờ gốc, công nợ tờ gốc giảm 1,2 triệu, không đụng kho")
def _ghi_so_that():
	x = _dung()
	if not x:
		return
	p, goc, dc = x
	t = khong_nem("tìm tờ gốc", lambda: hd_dieu_chinh.thong_tin(dc.name)) or {}
	la("nhận là tờ điều chỉnh", t.get("la_dieu_chinh"), 1)
	la("tìm đúng tờ gốc qua M-Invoice", (t.get("goc") or {}).get("name"), goc.name)
	la("chưa có lý do chặn", t.get("loi"), None)
	kq = khong_nem("ghi sổ điều chỉnh", lambda: doi_chieu_mua.ghi_so_dieu_chinh(dc.name)) or {}
	la("báo đã ghi sổ", kq.get("da_ghi_so"), 1)
	dc.reload()
	la("tờ điều chỉnh đã ghi sổ", dc.docstatus, 1)
	la("là phiếu nợ trả lại", dc.is_return, 1)
	la("gắn đúng tờ gốc", dc.return_against, goc.name)
	la("không ghi kho", frappe.db.count("Stock Ledger Entry", {"voucher_type": dc.doctype, "voucher_no": dc.name}), 0)
	gl = nen.so_cai_cua(dc)
	dung("có sổ cái và cân", bool(gl) and abs(sum(flt(g.debit) - flt(g.credit) for g in gl)) < 0.01)
	la("phải trả NCC giảm đúng 1,2 triệu", round(sum(flt(g.debit) - flt(g.credit) for g in gl
		if g.account == dc.credit_to and g.party == dc.supplier), 2), float(-DIEU_CHINH))
	la("công nợ tờ gốc còn 8.000.000",
		flt(frappe.db.get_value("Purchase Invoice", goc.name, "outstanding_amount")), float(PNK))
	cty = nen.cong_ty()
	srbnb = frappe.get_cached_value("Company", cty, "stock_received_but_not_billed")
	theo_hd = frappe.db.get_single_value("Buying Settings", "set_landed_cost_based_on_purchase_invoice_rate")
	if srbnb and not theo_hd:
		la("hàng về chưa có hoá đơn của phiếu nhập về 0 sau ba chứng từ", _so_du(srbnb, p, goc, dc), 0.0)
	else:
		dung("Buying Settings đang tính giá kho theo hoá đơn: ca này chưa xét tài khoản hàng về", not theo_hd)


@ca("v666 bấm ghi sổ điều chỉnh lần hai thì từ chối, không ghi phiếu nợ thứ hai")
def _hai_lan_that():
	x = _dung()
	if not x:
		return
	_p, goc, dc = x
	khong_nem("ghi sổ lần một", lambda: doi_chieu_mua.ghi_so_dieu_chinh(dc.name))
	try:
		doi_chieu_mua.ghi_so_dieu_chinh(dc.name)
		loi = ""
	except frappe.ValidationError as e:
		loi = nen.cau_loi(e)
	dung("lần hai bị chặn", "nháp" in loi)
	la("tờ gốc chỉ có một phiếu nợ", frappe.db.count("Purchase Invoice",
		{"return_against": goc.name, "docstatus": 1}), 1)
	la("công nợ tờ gốc vẫn 8.000.000",
		flt(frappe.db.get_value("Purchase Invoice", goc.name, "outstanding_amount")), float(PNK))


@ca("v666 tờ gốc còn nháp thì ghi sổ điều chỉnh bị chặn, nói rõ phải ghi sổ tờ gốc trước")
def _goc_nhap_that():
	x = _dung(ghi_so_goc=False)
	if not x:
		return
	_p, goc, dc = x
	try:
		doi_chieu_mua.ghi_so_dieu_chinh(dc.name)
		loi = ""
	except frappe.ValidationError as e:
		loi = nen.cau_loi(e)
	dung("chặn và chỉ đường", goc.name in loi and "trước" in loi)
	la("tờ điều chỉnh vẫn nháp", frappe.db.get_value("Purchase Invoice", dc.name, "docstatus"), 0)
