# -*- coding: utf-8 -*-
"""v543: hoá đơn nhiều dòng có chiết khấu không còn lệch vài chục đồng.

Ca thật 30/09/2026: GSM C26TBB/77683, 889 dòng cước, chiết khấu thương mại
1.489.862, tiền hàng sau giảm 22.361.536, thuế 1.788.923, tổng 24.150.459.
Máy dựng ra 24.150.438, thiếu 21 đồng, hàng rào cuối "Không nhận", tờ nằm lại
ở danh sách "chưa thành phiếu mua" và kế toán tưởng bị đòi Đơn mua hàng.

Đã đo trên site thật (System Console, commit=0, dựng rồi bỏ): cùng 889 dòng,
cùng chiết khấu, KHÔNG gắn nguồn MInvoice thì tổng ra đúng 24.150.459. Chỉ khi
gắn nguồn thì hook `do_chinh_xac_mua.truoc_khi_tinh` hạ độ lẻ net_amount của
dòng về 0 trong khi net_total của tờ vẫn 2, và phép bù làm tròn của ERPNext
lệch nhau từ đó.

Phép chia chiết khấu dưới đây chép đúng
erpnext/controllers/taxes_and_totals.py nhánh version-16, hàm
apply_discount_amount (đối chiếu 30/09/2026). Chép để đo được hai chế độ độ
lẻ mà không cần site; ca chạy thật nằm ở kiem_that/gsm_lam_tron_543.py.
"""

from decimal import Decimal, ROUND_HALF_UP

from vagabond import do_chinh_xac_mua as cx
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _tron(x, so_le):
	return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-so_le), rounding=ROUND_HALF_UP))


def _chia_chiet_khau(tien_dong, chiet_khau, le_dong, le_tong):
	"""apply_discount_amount của ERPNext v16, bỏ phần tiền tệ công ty."""
	tong = sum(tien_dong)
	net_total = 0.0
	ky_vong = 0.0
	rong = []
	for tien in tien_dong:
		chia = chiet_khau * tien / tong
		sau = tien - chia
		ky_vong += sau
		net = _tron(sau, le_dong)
		net_total += net
		bu = _tron(ky_vong - net_total, le_tong)
		if bu:
			net = _tron(net + bu, le_dong)
			net_total += bu
		rong.append(net)
	return sum(rong)


def _dong_giong_gsm():
	"""889 dòng cước nguyên đồng, tổng 23.851.398 như tờ 77683."""
	# Mọi dòng DƯƠNG như tờ thật: 888 dòng theo bảng giá, dòng cuối là phần
	# còn lại (23.144). Bản đầu cộng bù vào dòng cuối nên nó thành âm và
	# ERPNext chặn ghi sổ "rate must be a positive number" (Bench #396).
	gia = [23325, 36574, 18000, 31234, 23959, 27000, 19873, 24560, 36789]
	dong = [gia[(i * 7) % len(gia)] for i in range(888)]
	dong.append(23851398 - sum(dong))
	return dong


QC = {"gia": 9, "tien": 0, "sl": 9}


@ca("v543 độ lẻ: tiền dòng theo nguồn, tiền sau giảm không ít lẻ hơn tổng của tờ")
def _bang():
	b = cx.bang_do_chinh_xac(QC, 2)
	la("thành tiền dòng giữ số nguyên như hoá đơn", (b["amount"], b["base_amount"]), (0, 0))
	la("tiền sau giảm theo độ lẻ tổng", (b["net_amount"], b["base_net_amount"]), (2, 2))
	la("đơn giá 9 lẻ", b["rate"], 9)
	la("số lượng 9 lẻ", b["qty"], 9)
	b = cx.bang_do_chinh_xac({"gia": 9, "tien": 3, "sl": 9}, 2)
	la("nguồn nhiều lẻ hơn tổng thì giữ lẻ nguồn", b["net_amount"], 3)
	dung("đủ mọi trường tiền của bản cũ", set(cx.TIEN) <= set(b))


@ca("v543 ca GSM 77683: 889 dòng chia chiết khấu, độ lẻ cũ lệch hàng chục đồng, độ lẻ mới khớp tuyệt đối")
def _gsm():
	dong = _dong_giong_gsm()
	la("tổng dòng như tờ thật", sum(dong), 23851398)
	muc = 22361536
	cu = _chia_chiet_khau(dong, 1489862, 0, 2)
	moi_bang = cx.bang_do_chinh_xac(QC, 2)
	moi = _chia_chiet_khau(dong, 1489862, moi_bang["net_amount"], 2)
	dung("độ lẻ cũ (dòng 0, tổng 2) tái hiện lệch: %.2f" % (cu - muc), abs(cu - muc) >= 1)
	la("độ lẻ mới khớp tiền sau giảm", round(moi, 2), float(muc))


class _Tt(dict):
	__getattr__ = dict.get


class _Truong(object):
	def __init__(self, ten):
		self.fieldname = ten
		self.fieldtype = "Currency"


class _Phieu(object):
	"""Đủ để chạy thật truoc_khi_tinh: precision() đọc _precision như Frappe."""

	def __init__(self, dong=None, le_mac_dinh=2):
		self.le = le_mac_dinh
		self.items = dong or []
		self.taxes = []
		self.meta = _Tt(fields=[_Truong("net_total"), _Truong("grand_total")])
		self.d = {"doctype": "Purchase Invoice", "currency": "VND", "custom_minvoice_id": "G", "docstatus": 0}

	def get(self, k, mac_dinh=None):
		if k == "items":
			return self.items
		if k == "taxes":
			return self.taxes
		return self.d.get(k, mac_dinh)

	def precision(self, ten, khoa="main"):
		p = getattr(self, "_precision", None) or {}
		return (p.get(khoa) or {}).get(ten, self.le)


@ca("v543 truoc_khi_tinh chạy thật: dòng nhận net_amount theo độ lẻ net_total của tờ, amount theo nguồn")
def _hook():
	import sys
	import types
	from unittest.mock import patch

	dong = [_Phieu(), _Phieu()]
	for d in dong:
		d.d = {}
	to = _Phieu(dong)
	dl = types.SimpleNamespace(_goc=lambda ma: {"tong_tien": 24150459, "tien_thue": 1788923, "chi_tiet": []})
	with patch.dict(sys.modules, {"vagabond.dung_lai_hddt": dl}):
		cx.truoc_khi_tinh(to)
	la("dòng: amount 0 lẻ", dong[0].precision("amount"), 0)
	la("dòng: net_amount 2 lẻ như net_total", dong[0].precision("net_amount"), 2)
	la("cửa items của tờ cũng vậy", (to.precision("amount", "items"), to.precision("net_amount", "items")), (0, 2))
	la("tổng của tờ giữ 2 lẻ", to.precision("net_total"), 2)
