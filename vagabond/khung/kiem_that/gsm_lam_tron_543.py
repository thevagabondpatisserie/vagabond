# -*- coding: utf-8 -*-
"""v543 chạy THẬT: tờ nhiều dòng có chiết khấu dựng ra đúng tổng hoá đơn.

Ca thật GSM C26TBB/77683 (30/09/2026): 889 dòng cước, một dòng chiết khấu
thương mại 1.489.862, thuế 1.788.923, tổng 24.150.459. Trước v543 máy dựng
ra 24.150.438 rồi "Không nhận". Ca này đi đúng đường của máy:
`dung_hoa_don_mua` -> insert -> hook độ lẻ -> ERPNext chia chiết khấu, chỉ
giả chỗ tra nhà cung cấp và mã hàng (dòng cước không gắn Món nào).
"""

from unittest.mock import patch

import frappe

from vagabond import minvoice_chung_tu as mv
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon


def _dong():
	gia = [23325, 56574, 18000, 31234, 42111, 27000, 19873, 24560, 36789]
	tien = [gia[(i * 7) % len(gia)] for i in range(889)]
	tien[-1] += 23851398 - sum(tien)
	raw = [dict(ten="Cước chuyến thử 543 số %d" % i, sluong=1, dgia=t, thtien=t,
		dvtinh="Chuyến", tchat=1, stckhau=0) for i, t in enumerate(tien)]
	raw.append(dict(ten="Chiết khấu thương mại/ khuyến mại", sluong=1, dgia=1489862,
		thtien=1489862, tchat=3, stckhau=0))
	return raw


@ca("v543 that: 889 dòng cước + chiết khấu như GSM 77683 dựng ra đúng 24.150.459, không 'Không nhận'")
def _gsm_77683():
	goc = _nguon(_dong(), 1788923, 24150459)
	ncc = nen.mot_nha_cung_cap()
	with patch.object(mv, "_tim_ncc", return_value=(ncc, "")), \
			patch.object(mv, "_tra_ma_hang", return_value=(None, None, 1)):
		ma = mv.dung_hoa_don_mua(goc.as_dict())
	nen._DA_TAO.append(("Purchase Invoice", ma))
	hd = frappe.get_doc("Purchase Invoice", ma)
	la("chiết khấu cả tờ", hd.discount_amount, 1489862)
	la("tiền hàng sau giảm", hd.net_total, 22361536)
	la("tổng đúng hoá đơn điện tử", hd.grand_total, 24150459)
	hd.save(ignore_permissions=True)
	hd.reload()
	la("lưu lại lần hai vẫn đúng", hd.grand_total, 24150459)
