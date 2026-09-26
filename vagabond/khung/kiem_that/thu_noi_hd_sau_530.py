"""v530: ca TÍCH HỢP nối hoá đơn đến sau ở mức hồ sơ, sổ cái THẬT.

Codex #373 vòng 1: đường này ghi sổ một Journal Entry đụng sổ cái và sổ công
nợ, nên phải có ca chạy thật trên site: ERPNext có nhận bút toán Nợ 331 tham
chiếu tờ / Có tài khoản chi phí không, công nợ tờ có về 0 không, gỡ có huỷ
được bút toán và trả công nợ tờ về như cũ không, và sửa tay bảng tờ nối có bị
chặn không. Mọi thứ lùi về điểm lưu (nen.py).

Dựng giống hồ sơ thật: hồ sơ chi từ TK công ty đã thanh toán, bút toán chi Nợ
chi phí / Có ngân hàng mang vgb_ho_so_tt, tờ hoá đơn mua cùng NCC ĐÃ ghi sổ.
"""
import json

import frappe
from frappe.utils import today

from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _luu, _phieu

TIEN = 100000


def _tk_ngan_hang(cty):
	return frappe.db.get_value("Account", {"company": cty, "is_group": 0, "disabled": 0, "account_type": "Bank"}, "name")


def _dung():
	"""(tờ đã ghi sổ, tên hồ sơ, tài khoản chi phí, bút toán chi) hoặc None."""
	cty = nen.cong_ty()
	hd = khong_nem("dựng tờ", lambda: _luu(_phieu([("Cước thử v530", 1, TIEN)])))
	if not hd:
		return None
	khong_nem("ghi sổ tờ", lambda: hd.submit())
	hd.reload()
	if hd.docstatus != 1:
		return None
	tk_cp = next((d.expense_account for d in hd.items if d.expense_account), None)
	ngan_hang = _tk_ngan_hang(cty)
	dung("có tài khoản chi phí và ngân hàng", bool(tk_cp and ngan_hang))
	if not (tk_cp and ngan_hang):
		return None
	p = frappe.new_doc("Vagabond Ho So TT")
	p.name = p.ma = "KT530-" + frappe.generate_hash(length=8)
	p.loai = "TK cong ty"
	p.trang_thai = "Da thanh toan"
	p.ngay = p.ngay_thanh_toan = today()
	p.nha_cung_cap = hd.supplier
	p.loai_cp_thue = "Chi phi khong hop le"
	p.tong_tien = hd.grand_total
	p.db_insert()
	d = frappe.new_doc("Vagabond Ho So TT Dong")
	d.parent, d.parenttype, d.parentfield, d.idx = p.name, "Vagabond Ho So TT", "dong", 1
	d.noi_dung, d.so_tien, d.cho_hoa_don, d.tk_no, d.tk_co = "Cước thử", hd.grand_total, 1, tk_cp, ngan_hang
	d.db_insert()
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Bank Entry"
	je.company = cty
	je.posting_date = je.cheque_date = today()
	je.cheque_no = p.name
	ttcp = frappe.db.get_value("Company", cty, "cost_center")
	je.append("accounts", {"account": tk_cp, "debit_in_account_currency": hd.grand_total, "cost_center": ttcp})
	je.append("accounts", {"account": ngan_hang, "credit_in_account_currency": hd.grand_total, "cost_center": ttcp})
	je.vgb_ho_so_tt = p.name
	je.flags.ignore_permissions = True
	if not khong_nem("bút toán chi của hồ sơ", lambda: (je.insert(ignore_permissions=True), je.submit())):
		return None
	nen._DA_TAO.append(("Journal Entry", je.name))
	return hd, p.name, tk_cp, je.name


@ca("v530 tờ đã ghi sổ nối vào hồ sơ TK công ty: bút toán bù trừ thật Nợ 331 tham chiếu tờ, Có chi phí; công nợ tờ về 0")
def _noi_that():
	from vagabond import ho_so_bo_sung as bo
	x = _dung()
	if not x:
		return
	hd, ho_so, tk_cp, _chi = x
	kq = khong_nem("nối", lambda: bo.noi_nhieu(ho_so, json.dumps([hd.name]))) or {}
	dung("có bút toán bù trừ", bool(kq.get("but_toan")))
	if not kq.get("but_toan"):
		return
	ten = kq["but_toan"][0]
	je = frappe.get_doc("Journal Entry", ten)
	la("ghi sổ, mang ô bù trừ, không mang ô bút toán chi", (je.docstatus, je.vgb_bu_tru_ho_so, je.get("vgb_ho_so_tt") or None), (1, ho_so, None))
	gl = nen.so_cai_cua(je)
	la("Nợ 331 đúng NCC", sum(g.debit for g in gl if g.account == hd.credit_to and g.party == hd.supplier), TIEN)
	la("Có tài khoản chi phí", sum(g.credit for g in gl if g.account == tk_cp), TIEN)
	la("công nợ tờ về 0", float(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 0.0)
	p = frappe.get_doc("Vagabond Ho So TT", ho_so)
	la("dòng nối trỏ đúng bút toán", [(r.hoa_don, r.but_toan) for r in p.hd_sau], [(hd.name, ten)])
	la("hợp lệ tính thuế", p.loai_cp_thue, "Chi phi hop le")


@ca("v530 gỡ tờ đã bù trừ trên site thật: bút toán huỷ được, công nợ tờ trở lại, bảng tờ nối trống")
def _go_that():
	from vagabond import ho_so_bo_sung as bo
	x = _dung()
	if not x:
		return
	hd, ho_so, _tk, _chi = x
	kq = khong_nem("nối", lambda: bo.noi_nhieu(ho_so, json.dumps([hd.name]))) or {}
	if not kq.get("but_toan"):
		dung("nối được trước khi gỡ", False)
		return
	g = khong_nem("gỡ", lambda: bo.go_noi(ho_so, hd.name)) or {}
	la("huỷ đúng bút toán", g.get("huy_but_toan"), kq["but_toan"][0])
	la("bút toán đã huỷ", frappe.db.get_value("Journal Entry", kq["but_toan"][0], "docstatus"), 2)
	la("công nợ tờ trở lại", float(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), float(TIEN))
	la("bảng tờ nối trống", len(frappe.get_doc("Vagabond Ho So TT", ho_so).hd_sau), 0)


@ca("v530 sửa tay bảng tờ nối trên Desk (không qua nút) thì dừng, bút toán còn nguyên")
def _sua_tay_that():
	from vagabond import ho_so_bo_sung as bo
	x = _dung()
	if not x:
		return
	hd, ho_so, _tk, _chi = x
	kq = khong_nem("nối", lambda: bo.noi_nhieu(ho_so, json.dumps([hd.name]))) or {}
	if not kq.get("but_toan"):
		dung("nối được trước khi sửa", False)
		return
	p = frappe.get_doc("Vagabond Ho So TT", ho_so)
	p.hd_sau = []
	try:
		p.save(ignore_permissions=True)
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("chặn, chỉ nối gỡ bằng nút", "bằng nút" in loi)
	la("bút toán còn ghi sổ", frappe.db.get_value("Journal Entry", kq["but_toan"][0], "docstatus"), 1)


@ca("v530 Codex #373 v2: huỷ thẳng bút toán bù trừ trên Desk bị chặn, công nợ tờ vẫn 0")
def _huy_thang_that():
	from vagabond import ho_so_bo_sung as bo
	x = _dung()
	if not x:
		return
	hd, ho_so, _tk, _chi = x
	kq = khong_nem("nối", lambda: bo.noi_nhieu(ho_so, json.dumps([hd.name]))) or {}
	if not kq.get("but_toan"):
		dung("nối được trước khi huỷ", False)
		return
	je = frappe.get_doc("Journal Entry", kq["but_toan"][0])
	try:
		je.cancel()
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("chặn, chỉ đường nút Gỡ", ho_so in loi)
	la("bút toán còn ghi sổ", frappe.db.get_value("Journal Entry", je.name, "docstatus"), 1)
	la("công nợ tờ vẫn 0", float(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 0.0)
