"""v675 trên ERPNext thật: phiếu chi APP đã xác nhận chuyển (có mã dòng sao kê)
được nối vào Đối chiếu ngân hàng của lõi, để dòng tiền ra không còn hiện trong
tin 08:00 "Tiền ra khỏi tài khoản công ty chưa có chứng từ".

Bản giả không thấy được cách lõi cấp tiền khi save() Bank Transaction đã xác
nhận (allocate_payment_entries), nên ca này chạy trên bench.
"""
import unittest.mock as um

import frappe
from frappe.utils import flt

from vagabond import duyet_chi as DC
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _giao_dich_ngan_hang, _hoa_don_mua, _tk_ngan_hang
from vagabond.khung.kiem_that.thu_lich_du_chi_654 import _phieu_chi_ncc


def _dung(tien_pe, tien_bt):
	cty = cong_ty()
	ba = _tk_ngan_hang(cty)
	tk_gl = frappe.db.get_value("Bank Account", ba, "account")
	hd = _hoa_don_mua(tien_pe)
	pe = _phieu_chi_ncc(hd, ba, tk_gl, tien_pe)
	g = _giao_dich_ngan_hang("APP675", tien_bt, cty, "MBCT VAGABOND TT HD NCC KIEM THAT 675")
	frappe.db.set_value("Payment Entry", pe.name, "vgb_chi_ma_gd", g.name, update_modified=False)
	return pe, g


def _dong_noi(g, pe):
	g = frappe.get_doc("Bank Transaction", g.name)
	return g, [r for r in g.payment_entries if r.payment_document == "Payment Entry" and r.payment_entry == pe.name]


@ca("v675 bench: nối phiếu chi vào dòng sao kê thật, dòng hết tiền chưa đối chiếu, bấm lại không nối hai lần")
def _noi_du():
	pe, g = _dung(3456000, 3456000)
	la("nối được", DC.noi_sao_ke(pe.name), "")
	g2, dong = _dong_noi(g, pe)
	la("một dòng đối chiếu", len(dong), 1)
	la("cấp đủ tiền phiếu", flt(dong[0].allocated_amount) if dong else 0, 3456000.0)
	la("dòng sao kê hết phần chưa đối chiếu", flt(g2.unallocated_amount), 0.0)
	dung("phiếu chi có ngày thanh toán bù trừ", bool(frappe.db.get_value("Payment Entry", pe.name, "clearance_date")))
	gl = frappe.db.count("GL Entry", {"voucher_type": "Payment Entry", "voucher_no": pe.name, "is_cancelled": 0})
	la("gọi lại: đã nối thì thôi", DC.noi_sao_ke(pe.name), "")
	la("vẫn một dòng đối chiếu", len(_dong_noi(g, pe)[1]), 1)
	la("bút toán phiếu không đổi", frappe.db.count("GL Entry", {"voucher_type": "Payment Entry", "voucher_no": pe.name, "is_cancelled": 0}), gl)


@ca("v675 bench: dòng sao kê ít tiền hơn phiếu thì không nối dở, trả lý do")
def _noi_thieu():
	pe, g = _dung(5000000, 4000000)
	la("lý do", DC.noi_sao_ke(pe.name), "dòng sao kê không còn đủ tiền chưa đối chiếu")
	g2, dong = _dong_noi(g, pe)
	la("không có dòng đối chiếu", len(dong), 0)
	la("dòng sao kê giữ nguyên", flt(g2.unallocated_amount), 4000000.0)


@ca("v675 bench: lịch 07:40 nối phiếu còn thiếu từ 01/11, ghi lý do một lần cho phiếu không nối được")
def _lich():
	pe_ok, g_ok = _dung(2222000, 2222000)
	pe_sai, _g = _dung(3000000, 1000000)
	with um.patch.object(frappe.db, "rollback", lambda *a, **k: None):
		# Codex #592: chỉ xét phiếu của ca, không đụng phiếu thật khi ca chạy trên site.
		DC.noi_sao_ke_con_thieu([pe_ok.name, pe_sai.name])
		DC.noi_sao_ke_con_thieu([pe_ok.name, pe_sai.name])
	la("phiếu đủ được nối", len(_dong_noi(g_ok, pe_ok)[1]), 1)
	vet = frappe.get_all("Comment", filters={"reference_doctype": "Payment Entry", "reference_name": pe_sai.name,
		"content": ["like", "Chưa nối được dòng sao kê%"]}, pluck="name")
	la("phiếu thiếu: một dòng lý do dù chạy hai lần", len(vet), 1)
