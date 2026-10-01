"""v551: hồ sơ Chi từ TK công ty, khoản hoá đơn đến sau, trên sổ cái THẬT.

Chị Dung 01/10/2026 (ca Adecco APP.26.09.009): lúc chi phải là Nợ 331 NCC /
Có ngân hàng (phiếu chi), hoá đơn về tự ghi Nợ chi phí + 1331 / Có 331, rồi
331 hết nợ. Không ghi chi phí lúc chi, không bút toán tay bù trừ.

Ca chạy đúng chuỗi thao tác thật: hồ sơ Đã duyệt có sao kê, bấm ghi nhận đã
thanh toán, rồi nối tờ (đã ghi sổ, hoặc còn nháp rồi ghi sổ), rồi gỡ. Không
gọi thêm hàm "cho chắc" giữa các bước (bài học #205). Mọi chứng từ lùi về
điểm lưu của nen.py.
"""
import json

import frappe
from frappe.utils import flt, today

from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_that.nen import _DA_TAO, _mot, ca, cong_ty, dung, khong_nem, la, so_cai_cua
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import (
	_giao_dich_ngan_hang, _hoa_don_mua, _mon_dich_vu, _tk_ngan_hang, _unc_gia,
)


def _hoa_don_nhap(tien, ncc):
	"""Tờ hoá đơn mua DỊCH VỤ còn NHÁP (hoá đơn điện tử vừa kéo về)."""
	hd = frappe.new_doc("Purchase Invoice")
	hd.company = cong_ty()
	hd.supplier = ncc
	hd.posting_date = hd.bill_date = today()
	hd.set_posting_time = 1
	hd.bill_no = "KT551-%s" % frappe.generate_hash(length=6)
	hd.append("items", {"item_code": _mon_dich_vu(), "qty": 1, "rate": tien})
	hd.flags.ignore_permissions = True
	hd.insert(ignore_permissions=True)
	_DA_TAO.append((hd.doctype, hd.name))
	return hd


def _ho_so(ncc, dong):
	"""Hồ sơ Chi từ TK công ty Đã duyệt, có UNC và sao kê đúng tổng."""
	cty = cong_ty()
	h = frappe.new_doc("Vagabond Ho So TT")
	h.ma = hs._sinh_ma()
	h.loai, h.ngay, h.trang_thai, h.da_tam_ung = "TK cong ty", today(), "Da duyet", 0
	h.nha_cung_cap = ncc
	h.tk_chi = _tk_ngan_hang(cty)
	h.loai_cp_thue = "Chi phi khong hop le"
	for d in dong:
		h.append("dong", d)
	h.flags.ignore_permissions = True
	h.insert(ignore_permissions=True)
	_DA_TAO.append((h.doctype, h.name))
	_unc_gia(h)
	_giao_dich_ngan_hang(h.name, sum(flt(d["so_tien"]) for d in dong), cty)
	return h


def _ghi_nhan(h):
	kq = khong_nem("ghi nhận đã thanh toán", lambda: hs.danh_dau_da_tra(h.name, gui_thu=0)) or {}
	for t in (kq.get("but_toan") or "").split(", "):
		if t:
			_DA_TAO.append(("Payment Entry" if frappe.db.exists("Payment Entry", t) else "Journal Entry", t))
	return kq


def _gl(dt, ten):
	return so_cai_cua(frappe.get_doc(dt, ten))


@ca("v551 ca Adecco: chi khoản hoá đơn đến sau ra phiếu chi Nợ 331 / Có ngân hàng, không chạm chi phí")
def _chi_tra_truoc():
	hd = khong_nem("tờ đã ghi sổ 100.000", lambda: _hoa_don_mua(100000))
	if not hd:
		return
	h = khong_nem("hồ sơ chờ hoá đơn, không chọn tài khoản Nợ", lambda: _ho_so(hd.supplier, [
		{"noi_dung": "Dịch vụ nhân sự T08", "so_tien": 100000, "cho_hoa_don": 1}]))
	if not h:
		return
	kq = _ghi_nhan(h)
	pe = kq.get("but_toan") or ""
	dung("sinh đúng một phiếu chi", bool(pe) and "," not in pe and bool(frappe.db.exists("Payment Entry", pe)))
	if not frappe.db.exists("Payment Entry", pe):
		return
	la("bộ chứng từ đủ", (kq.get("bo_chung_tu") or {}).get("du"), 1)
	p = frappe.get_doc("Payment Entry", pe)
	la("phiếu chi trả trước NCC, chưa phân bổ",
		(p.payment_type, p.party_type, p.party, flt(p.paid_amount), flt(p.unallocated_amount), len(p.references)),
		("Pay", "Supplier", hd.supplier, 100000.0, 100000.0, 0))
	gl = _gl("Payment Entry", pe)
	tk_nh = frappe.db.get_value("Bank Account", h.tk_chi, "account")
	la("Nợ 331 đúng NCC", sum(flt(g["debit"]) for g in gl if g["account"] == hd.credit_to and g.get("party") == hd.supplier), 100000.0)
	la("Có ngân hàng", sum(flt(g["credit"]) for g in gl if g["account"] == tk_nh), 100000.0)
	la("không dòng chi phí nào", sorted({g["account"] for g in gl}), sorted({hd.credit_to, tk_nh}))
	la("khoản mang dấu đã chi trả trước", [r.tra_truoc for r in frappe.get_doc("Vagabond Ho So TT", h.name).dong], [1])
	la("sao kê đã nối phiếu chi", frappe.db.count("Bank Transaction Payments", {"payment_entry": pe}), 1)
	kq2 = khong_nem("bấm lại", lambda: hs.danh_dau_da_tra(h.name, gui_thu=0)) or {}
	la("bấm lại không sinh thêm", (kq2.get("da_lam_roi"), kq2.get("but_toan")), (1, pe))


@ca("v551 nối tờ đã ghi sổ: máy phân bổ phiếu chi vào tờ, công nợ 331 về 0, không có bút toán bù trừ; gỡ thì trở lại")
def _noi_va_go():
	from vagabond import ho_so_bo_sung as bo
	hd = khong_nem("tờ đã ghi sổ 100.000", lambda: _hoa_don_mua(100000))
	if not hd:
		return
	h = khong_nem("hồ sơ", lambda: _ho_so(hd.supplier, [{"noi_dung": "DV", "so_tien": 100000, "cho_hoa_don": 1}]))
	if not h:
		return
	pe = _ghi_nhan(h).get("but_toan") or ""
	if not frappe.db.exists("Payment Entry", pe):
		dung("có phiếu chi trước khi nối", False)
		return
	so_bt = frappe.db.count("Journal Entry", {"vgb_bu_tru_ho_so": h.name})
	kq = khong_nem("nối tờ", lambda: bo.noi_nhieu(h.name, json.dumps([hd.name]))) or {}
	la("trả đúng phiếu chi đã phân bổ", kq.get("but_toan"), [pe])
	la("không lập bút toán bù trừ", frappe.db.count("Journal Entry", {"vgb_bu_tru_ho_so": h.name}), so_bt)
	la("công nợ tờ về 0", flt(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 0.0)
	la("phiếu chi hết phần chưa phân bổ", flt(frappe.db.get_value("Payment Entry", pe, "unallocated_amount")), 0.0)
	la("phiếu chi trỏ tờ", [(r.reference_doctype, r.reference_name, flt(r.allocated_amount))
		for r in frappe.get_doc("Payment Entry", pe).references], [("Purchase Invoice", hd.name, 100000.0)])
	p = frappe.get_doc("Vagabond Ho So TT", h.name)
	la("dòng nối trỏ phiếu chi", [(r.hoa_don, r.but_toan, flt(r.bu_tru)) for r in p.hd_sau], [(hd.name, pe, 100000.0)])
	ke = hs._ke_hoach_duyet(p)
	la("bộ chứng từ vẫn đủ sau phân bổ", hs._kiem_bo_chung_tu(ke, hs._but_toan_cua_ho_so(h.name), hs._do_chinh_xac())["du"], 1)
	g = khong_nem("gỡ", lambda: bo.go_noi(h.name, hd.name)) or {}
	dung("gỡ bằng Unreconcile Payment", bool(g.get("go_phan_bo")))
	if g.get("go_phan_bo"):
		_DA_TAO.append(("Unreconcile Payment", g["go_phan_bo"]))
	la("không huỷ phiếu chi", frappe.db.get_value("Payment Entry", pe, "docstatus"), 1)
	la("công nợ tờ trở lại", flt(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 100000.0)
	la("phiếu chi trở lại trả trước", flt(frappe.db.get_value("Payment Entry", pe, "unallocated_amount")), 100000.0)
	la("bảng tờ nối trống", len(frappe.get_doc("Vagabond Ho So TT", h.name).hd_sau), 0)


@ca("v551 tờ còn nháp: nối làm căn cứ, ghi sổ tờ được và máy tự phân bổ phiếu chi lúc ghi sổ")
def _to_nhap():
	from vagabond import ho_so_bo_sung as bo
	from vagabond.khung.kiem_that.nen import mot_nha_cung_cap
	ncc = mot_nha_cung_cap()
	hd = khong_nem("tờ nháp 100.000", lambda: _hoa_don_nhap(100000, ncc))
	if not hd:
		return
	h = khong_nem("hồ sơ", lambda: _ho_so(ncc, [{"noi_dung": "DV", "so_tien": 100000, "cho_hoa_don": 1}]))
	if not h:
		return
	pe = _ghi_nhan(h).get("but_toan") or ""
	if not frappe.db.exists("Payment Entry", pe):
		dung("có phiếu chi trước khi nối", False)
		return
	khong_nem("nối tờ nháp", lambda: bo.noi_nhieu(h.name, json.dumps([hd.name])))
	la("chưa phân bổ khi tờ còn nháp", flt(frappe.db.get_value("Payment Entry", pe, "unallocated_amount")), 100000.0)
	t = frappe.get_doc("Purchase Invoice", hd.name)
	t.flags.ignore_permissions = True
	dung("tờ đã nối ghi sổ được (chi phí chưa vào sổ qua hồ sơ)", bool(khong_nem("ghi sổ tờ", t.submit)))
	la("công nợ tờ về 0 ngay lúc ghi sổ", flt(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 0.0)
	la("phiếu chi đã phân bổ hết", flt(frappe.db.get_value("Payment Entry", pe, "unallocated_amount")), 0.0)
	p = frappe.get_doc("Vagabond Ho So TT", h.name)
	la("dòng nối cập nhật", [(r.hoa_don, r.da_ghi_so, r.but_toan, flt(r.bu_tru)) for r in p.hd_sau],
		[(hd.name, 1, pe, 100000.0)])


@ca("v551 hồ sơ lẫn khoản: phần chờ hoá đơn ra phiếu chi, phần không hoá đơn giữ bút toán chi phí")
def _lan():
	cty = cong_ty()
	from vagabond.khung.kiem_that.nen import mot_nha_cung_cap
	tk_cp = _mot("Account", {"company": cty, "is_group": 0, "root_type": "Expense", "disabled": 0})
	if not tk_cp:
		dung("có tài khoản chi phí", False)
		return
	h = khong_nem("hồ sơ lẫn", lambda: _ho_so(mot_nha_cung_cap(), [
		{"noi_dung": "Chờ hoá đơn", "so_tien": 70000, "cho_hoa_don": 1},
		{"noi_dung": "Phí không hoá đơn", "so_tien": 30000, "cho_hoa_don": 0, "tk_no": tk_cp}]))
	if not h:
		return
	kq = _ghi_nhan(h)
	ten = [t for t in (kq.get("but_toan") or "").split(", ") if t]
	la("một phiếu chi và một bút toán", sorted("PE" if frappe.db.exists("Payment Entry", t) else "JE" for t in ten), ["JE", "PE"])
	la("bộ chứng từ đủ", (kq.get("bo_chung_tu") or {}).get("du"), 1)
	for t in ten:
		if frappe.db.exists("Payment Entry", t):
			la("phiếu chi 70.000", flt(frappe.db.get_value("Payment Entry", t, "paid_amount")), 70000.0)
		else:
			gl = _gl("Journal Entry", t)
			la("bút toán Nợ chi phí 30.000", sum(flt(g["debit"]) for g in gl if g["account"] == tk_cp), 30000.0)
