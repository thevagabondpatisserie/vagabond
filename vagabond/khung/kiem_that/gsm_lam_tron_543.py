# -*- coding: utf-8 -*-
"""v543 chạy THẬT: tờ nhiều dòng có chiết khấu dựng ra đúng tổng hoá đơn.

Ca thật GSM C26TBB/77683 (30/09/2026): 889 dòng cước, một dòng chiết khấu
thương mại 1.489.862, thuế 1.788.923, tổng 24.150.459. Trước v543 máy dựng
ra 24.150.438 rồi "Không nhận". Ca này đi đúng đường của máy:
`dung_hoa_don_mua` -> insert -> hook độ lẻ -> ERPNext chia chiết khấu, chỉ
giả chỗ tra nhà cung cấp và mã hàng (gắn một Món không qua kho, như ca #259).

Codex #396: phải đi tới ghi sổ và sổ cái, vì net_amount/base_net_amount là
số ERPNext dùng để hạch toán chi phí. Lưu nháp đúng tổng chưa chứng minh ghi
sổ không bị chặn hay sổ cái không lệch.
"""

from unittest.mock import patch

import frappe

from vagabond import minvoice_chung_tu as mv
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon
from vagabond.khung.kiem_that.do_chinh_xac_mua_259 import _mon


def _dong():
	# Mọi dòng dương như tờ thật; dòng cuối là phần còn lại 23.144. Bản đầu
	# cộng bù vào dòng cuối nên nó âm và ERPNext chặn ghi sổ (Bench #396).
	gia = [23325, 36574, 18000, 31234, 23959, 27000, 19873, 24560, 36789]
	tien = [gia[(i * 7) % len(gia)] for i in range(888)]
	tien.append(23851398 - sum(tien))
	raw = [dict(ten="Cước chuyến thử 543 số %d" % i, sluong=1, dgia=t, thtien=t,
		dvtinh="Gram", tchat=1, stckhau=0) for i, t in enumerate(tien)]
	raw.append(dict(ten="Chiết khấu thương mại/ khuyến mại", sluong=1, dgia=1489862,
		thtien=1489862, tchat=3, stckhau=0))
	return raw


@ca("v543 that: 889 dòng cước + chiết khấu như GSM 77683 dựng ra đúng 24.150.459, không 'Không nhận'")
def _gsm_77683():
	goc = _nguon(_dong(), 1788923, 24150459)
	ncc = nen.mot_nha_cung_cap()
	mon = _mon()
	with patch.object(mv, "_tim_ncc", return_value=(ncc, "")), \
			patch.object(mv, "_tra_ma_hang", return_value=(mon.name, "Gram", 1)):
		ma = mv.dung_hoa_don_mua(goc.as_dict())
	nen._DA_TAO.append(("Purchase Invoice", ma))
	hd = frappe.get_doc("Purchase Invoice", ma)
	la("chiết khấu cả tờ", hd.discount_amount, 1489862)
	la("tiền hàng sau giảm", hd.net_total, 22361536)
	la("tổng đúng hoá đơn điện tử", hd.grand_total, 24150459)
	hd.save(ignore_permissions=True)
	hd.reload()
	la("lưu lại lần hai vẫn đúng", hd.grand_total, 24150459)
	hd.flags.ignore_permissions = True
	hd.submit()
	hd.reload()
	la("ghi sổ được, giữ tổng", (hd.docstatus, hd.grand_total), (1, 24150459))
	gl = nen.so_cai_cua(hd)
	dung("có sổ cái", bool(gl))
	la("sổ cái cân", round(sum(d.debit - d.credit for d in gl), 2), 0)
	tk_cp = hd.items[0].expense_account
	la("chi phí đúng tiền hàng sau giảm", round(sum(d.debit - d.credit for d in gl if d.account == tk_cp), 2), 22361536)
	la("thuế đầu vào đúng hoá đơn", round(sum(d.debit - d.credit for d in gl if d.account == hd.taxes[0].account_head), 2), 1788923)
	la("phải trả đúng tổng hoá đơn", round(sum(d.credit - d.debit for d in gl if d.account == hd.credit_to), 2), 24150459)
	hd.cancel()
	gl = frappe.get_all("GL Entry", filters={"voucher_type": hd.doctype, "voucher_no": hd.name},
		fields=["account", "debit", "credit"])
	for tk in {d.account for d in gl}:
		la("huỷ đảo đủ " + tk, round(sum(d.debit - d.credit for d in gl if d.account == tk), 2), 0)
