"""v571 (#437): Sales lập phiếu thu, khớp tay một giao dịch trả gộp nhiều hoá đơn.

Codex #437 vòng 3: ca tầng khung thay Payment Entry bằng đồ giả nên không
chứng minh được ERPNext chấp thuận phiếu do Sales lập (validation, quyền, sổ
cái). Các ca dưới dựng hoá đơn, giao dịch ngân hàng THẬT trong điểm lưu, gọi
đúng cửa màn Công nợ gọi BẰNG MỘT TÀI KHOẢN CHỈ CÓ VAI SALES, rồi đọc lại
phiếu thu, dư nợ, sổ cái.

Ca thật gốc: Loan Anh (Sales Manager) khớp tay DNTT-26-10-00002 của chị
Hồng; Error Log 04/10/2026 ghi PermissionError từ
payment_entry.get_account_details.
"""
from unittest.mock import patch

import frappe
from frappe.utils import flt, nowdate, add_days

from vagabond import thu_tien as tt
from vagabond import cong_no as cn
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon, _app
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_phieu_thu_unc_534 import _Tep, _gl


def _sales():
	"""Tài khoản thử CHỈ có vai Sales, như Loan Anh: không quyền Payment Entry."""
	u = frappe.get_doc({"doctype": "User",
		"email": "kt571-sales-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm Sales 571", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Sales Manager"}, {"role": "Sales User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u.name


def _hd_no(tk_thue, cty, tien):
	si = _app(cty, [dict(item_code=_mon(tk_thue), qty=1, rate=tien)])
	si.vgb_tam_tinh = 0
	# Bench #437 lần 1: đơn GrabFood không nhận phương thức "Công nợ"
	# (ban_hang.kiem_truoc_khi_luu). Khớp tay chỉ cần tờ đã ghi sổ còn nợ,
	# nên giữ đúng phương thức của nguồn như ca #534.
	si.vgb_pt_thanh_toan = "GrabFood"
	si.vgb_ma_tham_chieu = "KT571-" + frappe.generate_hash(length=8)
	si.save(ignore_permissions=True)
	si.submit(); si.reload()
	return si


def _gd(ba, tien):
	ref = "FTKT571" + frappe.generate_hash(length=10)
	g = frappe.get_doc({"doctype": "Bank Transaction", "date": nowdate(), "bank_account": ba,
		"deposit": tien, "withdrawal": 0, "currency": "VND", "description": "KT571 chuyen gop",
		"reference_number": ref, "transaction_id": ref})
	g.insert(ignore_permissions=True); _DA_TAO.append((g.doctype, g.name))
	g.submit()
	return g


def _phieu(ds_si):
	d = frappe.new_doc("Vagabond Cong No")
	d.ma_phieu = "DNTT-KT571-" + frappe.generate_hash(length=6)
	d.khach = ds_si[0].customer
	d.ten_khach = ds_si[0].customer_name
	d.ngay_tao = nowdate()
	d.han_qr = add_days(nowdate(), 7)
	d.trang_thai = "Cho thu"
	for s in ds_si:
		d.append("dong", {"hoa_don": s.name, "ngay": s.posting_date, "so_tien": flt(s.grand_total)})
	d.insert(ignore_permissions=True); _DA_TAO.append((d.doctype, d.name))
	return d


def _khop_bang(ai, phieu, tien, ma):
	truoc = frappe.session.user
	try:
		frappe.set_user(ai)
		with patch.object(cn, "_gui_thu_da_nhan", lambda d: None):
			kq = cn.khop_tay(phieu, tien, ma, "KT571")
		sau = frappe.session.user
	finally:
		frappe.set_user(truoc)
	return kq, sau


def _pe_moi(kq):
	pe = frappe.get_doc("Payment Entry", kq["pe"])
	_DA_TAO.append((pe.doctype, pe.name))
	return pe


@ca("#437 Sales khớp tay một giao dịch gộp hai hoá đơn: MỘT phiếu thu nháp thật, đúng phân bổ, đúng người lập, trả lại người gọi")
def _sales_khop_gop():
	cty, tk, _mau = _nen()
	a = _hd_no(tk, cty, 4750000)
	b = _hd_no(tk, cty, 2850000)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	g = _gd(ba, flt(a.grand_total) + flt(b.grand_total))
	p = _phieu([a, b])
	ai = _sales()
	dung("tài khoản thử KHÔNG có quyền đọc Payment Entry",
		not frappe.has_permission("Payment Entry", "read", user=ai))
	kq, sau = _khop_bang(ai, p.name, flt(g.deposit), g.reference_number)
	la("trả lại đúng người gọi sau khi lập", sau, ai)
	dung("có phiếu thu", bool(kq.get("pe")))
	pe = _pe_moi(kq)
	la("phiếu còn nháp (ghi sổ cần UNC)", pe.docstatus, 0)
	la("người lập là Sales, không phải Administrator", pe.owner, ai)
	la("mang mã giao dịch", pe.reference_no, g.reference_number)
	la("về đúng tài khoản giao dịch", pe.paid_to, frappe.db.get_value("Bank Account", ba, "account"))
	la("phân bổ đủ hai tờ", sorted((r.reference_name, flt(r.allocated_amount)) for r in pe.references),
		sorted([(a.name, flt(a.grand_total)), (b.name, flt(b.grand_total))]))
	la("phiếu đòi nợ đã thu đủ", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Da thu du")
	ds = [x for x in tt.phieu_thu_nhap(cac_si=[a.name, b.name]) if x["pe"] == pe.name]
	la("màn Tiền đã về xác minh được", ds and ds[0]["da_xac_minh"], 1)
	la("không còn hoá đơn thiếu phiếu thu", cn._hd_chua_co_phieu_thu([a.name, b.name]), set())


@ca("#437 kế toán đính UNC rồi ghi sổ phiếu gộp: GL đúng, hai tờ hết nợ, giao dịch nối đúng phiếu")
def _ghi_so_gop():
	cty, tk, _mau = _nen()
	a = _hd_no(tk, cty, 4750000)
	b = _hd_no(tk, cty, 2850000)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	tong = flt(a.grand_total) + flt(b.grand_total)
	g = _gd(ba, tong)
	p = _phieu([a, b])
	kq, _sau = _khop_bang(_sales(), p.name, tong, g.reference_number)
	pe = _pe_moi(kq)
	with _Tep() as t:
		r = tt.ghi_so_phieu_thu(pe.name, unc=[t.file_url])
		la("ghi sổ được", r.get("ok"), 1)
		pe.reload(); a.reload(); b.reload(); g.reload()
		la("phiếu vào sổ", pe.docstatus, 1)
		la("GL: nợ ngân hàng đủ tổng, có phải thu đủ tổng",
			sorted((x["account"], round(x["debit"]), round(x["credit"])) for x in _gl_tong(pe)),
			sorted([(pe.paid_to, round(tong), 0), (a.debit_to, 0, round(tong))]))
		la("tờ 1 hết nợ", flt(a.outstanding_amount), 0.0)
		la("tờ 2 hết nợ", flt(b.outstanding_amount), 0.0)
		la("giao dịch nối đúng phiếu", [x.payment_entry for x in g.payment_entries], [pe.name])


def _gl_tong(pe):
	gom = {}
	for acc, _pt, no, co in _gl(pe):
		x = gom.setdefault(acc, {"account": acc, "debit": 0.0, "credit": 0.0})
		x["debit"] += no; x["credit"] += co
	return list(gom.values())


@ca("#437 vòng 3: khách trả góp, tờ đã có phiếu nháp một phần vẫn được chia phần còn lại")
def _tra_gop():
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	cty, tk, _mau = _nen()
	a = _hd_no(tk, cty, 4750000)
	b = _hd_no(tk, cty, 2850000)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	tk_gl = frappe.db.get_value("Bank Account", ba, "account")
	g1 = _gd(ba, 2000000)
	pe1 = get_payment_entry("Sales Invoice", a.name, party_amount=2000000, bank_account=tk_gl)
	pe1.reference_no = g1.reference_number; pe1.reference_date = nowdate()
	pe1.insert(ignore_permissions=True); _DA_TAO.append((pe1.doctype, pe1.name))
	con = flt(a.grand_total) - 2000000 + flt(b.grand_total)
	g2 = _gd(ba, con)
	p = _phieu([a, b])
	kq, _sau = _khop_bang(_sales(), p.name, con, g2.reference_number)
	pe = _pe_moi(kq)
	la("chia cả phần còn lại của tờ 1 và cả tờ 2",
		sorted((r.reference_name, round(flt(r.allocated_amount))) for r in pe.references),
		sorted([(a.name, round(flt(a.grand_total) - 2000000)), (b.name, round(flt(b.grand_total)))]))
	la("không bơ vơ đồng nào", round(flt(pe.paid_amount)), round(con))
	# Codex #437 vòng 4: đã thu cộng dồn cả phần nháp 2tr có từ trước.
	la("phiếu đòi nợ đã thu đủ", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Da thu du")
	la("đã thu cộng dồn", round(flt(frappe.db.get_value("Vagabond Cong No", p.name, "da_thu"))),
		round(flt(a.grand_total) + flt(b.grand_total)))


@ca("#437 Sales ghi thu tiền mặt cho hoá đơn: phiếu thu GHI SỔ thật, GL hai dòng, hết nợ, người lập là Sales")
def _sales_tien_mat():
	cty, tk, _mau = _nen()
	si = _hd_no(tk, cty, 1000000)
	quy = frappe.db.get_value("Account", {"company": cty, "account_type": "Cash", "is_group": 0, "disabled": 0}, "name")
	dung("có tài khoản tiền mặt", bool(quy))
	mp = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "KT571 TM " + frappe.generate_hash(length=6),
		"type": "Cash", "enabled": 1, "accounts": [{"company": cty, "default_account": quy}]})
	mp.insert(ignore_permissions=True); _DA_TAO.append((mp.doctype, mp.name))
	ai = _sales()
	truoc = frappe.session.user
	try:
		frappe.set_user(ai)
		ds = tt.ghi_thu_tien(si.name, [{"pt": mp.name, "so_tien": flt(si.grand_total)}], nguon="kt571")
		sau = frappe.session.user
	finally:
		frappe.set_user(truoc)
	la("trả lại người gọi", sau, ai)
	la("một phiếu thu", len(ds), 1)
	pe = frappe.get_doc("Payment Entry", ds[0]); _DA_TAO.append((pe.doctype, pe.name))
	si.reload()
	la("đã ghi sổ", pe.docstatus, 1)
	la("người lập là Sales", pe.owner, ai)
	la("GL hai dòng đúng", sorted((acc, round(no), round(co)) for acc, _p, no, co in _gl(pe)),
		sorted([(quy, round(flt(si.grand_total)), 0), (si.debit_to, 0, round(flt(si.grand_total)))]))
	la("hoá đơn hết nợ", flt(si.outstanding_amount), 0.0)
