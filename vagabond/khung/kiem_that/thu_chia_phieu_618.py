# -*- coding: utf-8 -*-
"""v618 chạy THẬT (Codex #512): một dòng hoá đơn đơn giá lẻ nối hai phiếu nhập.

Ca tầng khung `thu_nan_gia_dong_618._chia_hai_phieu` chạy `_noi` với bộ giả.
Ca này đi đúng đường của máy trên ERPNext thật: hai Purchase Receipt thật,
`doi_chieu_mua._noi`, lưu lặp, reload, ghi sổ, sổ cái.

SỐ LIỆU: 13 đơn vị x 1.001,5 = 13.019,5. Người bán làm tròn lên 13.020. Chia 2
+ 11 thì hai dòng con 2.003 + 11.016,5. Site làm tròn nửa đồng về số chẵn nên
dòng thứ hai ra 11.016, cộng 13.019, hụt một đồng so với hoá đơn. Bản sửa chia
tiền trước: 2.003 + 11.017, đơn giá dòng thứ hai 1.001,545454545.

Bench làm tròn kiểu khác (nửa đồng lên) thì hai dòng con tự cộng đúng 13.020 và
nhánh chia tiền không cần chạy; ca vẫn chốt tổng, chỉ bỏ ý "hai đơn giá khác
nhau". Ý đó có điều kiện theo đúng cách làm tròn của chính site đang chạy.
"""

from frappe.utils import flt

from vagabond import doi_chieu_mua
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_mua_hddt_227 import _ghi_so, _luu, _nguon, _phieu


@ca("v618 Codex #512: PI 13 x 1.001,5 nối hai PR 2 + 11, lưu lặp, ghi sổ, GL đúng 13.020")
def _chia_hai_pr():
	p1 = nen.phieu_nhap_ao(2, 1001.5)
	p2 = nen.phieu_nhap_ao(11, 1001.5)
	d = p1.items[0]
	la("hai phiếu cùng mã hàng", p2.items[0].item_code, d.item_code)
	g = _nguon([{"ten": "Hàng chia thử 618", "sluong": 13, "dgia": 1001.5,
		"thtien": 13020, "dvtinh": d.uom}], 0, 13020)
	hd = _phieu([("Hàng chia thử 618", 13, 1001.5)], d.item_code, p1.supplier)
	hd.items[0].uom = d.uom
	hd.items[0].conversion_factor = d.conversion_factor
	hd.items[0].warehouse = d.warehouse
	hd.custom_minvoice_id = g.name
	_luu(hd)
	la("trước khi nối: một dòng đúng 13.020", flt(hd.items[0].amount), 13020)
	nua_ve_chan = flt(0.5, 0) == 0
	kq = doi_chieu_mua._noi(hd, [p1.name, p2.name], True)
	la("nối đủ hai phiếu", kq["da_noi"], 2)
	la("không lỗi", kq["loi"], [])
	for lan in range(2):
		hd.save(ignore_permissions=True)
		hd.reload()
		la("lần lưu %d: hai dòng con 2 và 11" % (lan + 1), sorted(flt(x.qty) for x in hd.items), [2, 11])
		la("lần lưu %d: tổng dòng con đúng hoá đơn" % (lan + 1), sum(flt(x.amount) for x in hd.items), 13020)
		la("lần lưu %d: tiền hàng đúng" % (lan + 1), flt(hd.net_total), 13020)
		la("lần lưu %d: đủ liên kết" % (lan + 1), {x.pr_detail for x in hd.items},
			{p1.items[0].name, p2.items[0].name})
	if nua_ve_chan:
		dung("site làm tròn về chẵn: hai dòng con mang hai đơn giá", len({flt(x.rate) for x in hd.items}) == 2)
		dung("đơn giá lệch giá in dưới nửa đồng", all(abs(flt(x.rate) - 1001.5) <= 0.5 for x in hd.items))
	hd.flags.ignore_permissions = True
	_ghi_so(hd, 13020, 0)
	la("ghi sổ giữ tổng tuyệt đối", flt(hd.grand_total), 13020)
	gl = nen.so_cai_cua(hd)
	la("phải trả đúng 13.020", round(sum(x.credit - x.debit for x in gl if x.account == hd.credit_to), 2), 13020)
	for p in (p1, p2):
		p.reload()
		dung("PR %s đã nhận tiền hoá đơn" % p.name, flt(p.items[0].billed_amt) > 0)
	dung("không còn dòng không mã hàng", all(x.item_code for x in hd.items))
