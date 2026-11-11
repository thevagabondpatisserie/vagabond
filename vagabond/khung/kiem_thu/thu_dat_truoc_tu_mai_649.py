# -*- coding: utf-8 -*-
"""v649 web đặt bánh (Loan Anh báo 11/11/2026, anh Việt chọn tách đơn): bánh đặt
trước nhận từ ngày mai, bánh nhận trong ngày lấy ở tab Có sẵn hôm nay.

1. Trang chạy thật trong node (hanh_vi/dat_truoc_tu_mai_649.mjs): lịch tab Đặt
   bánh trước bắt đầu từ Ngày mai, giỏ không trộn hai loại, giỏ cũ trộn thì
   không gửi.
2. Máy chủ (ton_don_web.kiem THẬT, Frappe giả): đơn nhận hôm nay có bánh đặt
   trước mà Kiểm bánh hôm nay không có dòng thì từ chối; chưa có bảng Kiểm bánh
   hôm nay thì nhận như cũ (F21-4).
"""
import subprocess
from datetime import date
from pathlib import Path
from types import SimpleNamespace as D
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import ton_don_web as ton  # noqa: E402

GOC = Path(__file__).parents[3]
EPI = "BAWC00019"
CANDLE = "BAWC00139"


def _nguon(dong_kb, co_kb=True):
	"""Kiểm bánh hôm nay và bảng BTP giả, đúng hình dạng ton_don_web đọc."""
	return D(db=D(exists=lambda *a: co_kb),
		get_doc=lambda *a: D(dong=[D(**x) for x in dong_kb]),
		get_single=lambda *a: D(dong=[D(ma_hang=EPI, ten_banh="Bánh Ổ Epi 12cm", so_decor=9),
			D(ma_hang=CANDLE, ten_banh="CANDLE 12cm", so_decor=2)]))


def _kiem(hang, nguon, ngay="2026-11-11"):
	with patch.object(ton, "hom_nay", lambda: date(2026, 11, 11)), patch.object(ton, "frappe", nguon):
		return ton.kiem(hang, ngay)


@ca("v649 web tab Đặt bánh trước từ Ngày mai, tách đơn: ca hành vi chạy thật trong node đều đạt")
def _node():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/dat_truoc_tu_mai_649.mjs")],
		capture_output=True, text=True, timeout=120)
	dung("chạy được: " + (r.stdout[-1500:] + r.stderr[-600:]), r.returncode == 0)
	dung("đủ 7 ca", "7 dat, 0 hong" in r.stdout)


@ca("v649 máy chủ: đơn nhận hôm nay có bánh đặt trước không có trong Kiểm bánh hôm nay thì từ chối, câu nói rõ nhận từ ngày mai")
def _may_chu():
	kb = [{"ma_hang": CANDLE, "ten_banh": "CANDLE 12cm", "co_the_ban": 3}]
	r = _kiem([{"variation_id": EPI, "quantity": 1}], _nguon(kb))
	la("một câu", len(r), 1)
	dung("nói rõ", "Bánh Ổ Epi 12cm là bánh đặt trước, nhận từ ngày mai" in r[0] and "Có sẵn hôm nay" in r[0])
	la("bánh có trong Kiểm bánh hôm nay, đủ số: nhận", _kiem([{"variation_id": CANDLE, "quantity": 2}], _nguon(kb)), [])
	dung("bánh có trong Kiểm bánh hôm nay, quá số: vẫn chặn như cũ",
		"còn 3 cái" in _kiem([{"variation_id": CANDLE, "quantity": 4}], _nguon(kb))[0])
	la("món không phải bánh đặt trước (nến, phụ kiện): không đụng",
		_kiem([{"variation_id": "PKNEN01", "quantity": 5}], _nguon(kb)), [])


@ca("v649 máy chủ: chưa có bảng Kiểm bánh hôm nay là chưa biết tồn, nhận như cũ (F21-4)")
def _chua_co_kb():
	la("không chặn", _kiem([{"variation_id": EPI, "quantity": 1}], _nguon([], co_kb=False)), [])


@ca("v649 phép thuần chan_dat_truoc_hom_nay")
def _thuan():
	ten = {EPI: "Bánh Ổ Epi 12cm"}
	la("có dòng thì không nhắc", ton.chan_dat_truoc_hom_nay([{"variation_id": EPI}], {EPI}, ten), [])
	la("không dòng thì nhắc", len(ton.chan_dat_truoc_hom_nay([{"variation_id": EPI}], set(), ten)), 1)
	la("không phải bánh BTP", ton.chan_dat_truoc_hom_nay([{"variation_id": "X"}], set(), ten), [])
	la("hàng rỗng", ton.chan_dat_truoc_hom_nay(None, set(), ten), [])


def _nguon_decor(decor, lam=0):
	"""Bảng BTP sau khi bếp làm: Đủ decor còn `decor` (có thể âm), đã trừ `lam`."""
	return D(db=D(exists=lambda dt, ten: False),
		get_doc=lambda *a: D(dong=[]),
		get_single=lambda *a: D(dong=[D(ma_hang=EPI, ten_banh="Bánh Ổ Epi 12cm", so_decor=decor, decor_da_lam=lam,
			so_refill=0, refill_tu=None, refill_den=None)]))


@ca("v649 Codex #552 vòng 4: bếp làm hết Đủ decor (về 0 hay âm) thì máy chủ vẫn chặn đơn ngày mai, không coi là dòng giữ chỗ")
def _het_decor():
	h = [{"variation_id": EPI, "quantity": 1}]
	dung("decor 1, bếp làm 1, còn 0: chặn", "còn 0 cái" in "".join(_kiem(h, _nguon_decor(0, 1), "2026-11-12")))
	dung("decor 1, bếp làm 2, còn -1: chặn", "còn 0 cái" in "".join(_kiem(h, _nguon_decor(-1, 2), "2026-11-12")))
	la("dòng giữ chỗ thật (bếp chưa nhập decor): nhận như cũ", _kiem(h, _nguon_decor(0, 0), "2026-11-12"), [])
	la("bếp nhập 0 rồi làm (gốc vẫn 0): giữ chỗ như cũ", _kiem(h, _nguon_decor(-2, 2), "2026-11-12"), [])
	la("còn decor: nhận", _kiem(h, _nguon_decor(3, 1), "2026-11-12"), [])


@ca("v649 Codex #552 vòng 4: lượt giữ tồn cuối cùng (giu_ton_web) cũng chặn khi bếp làm hết Đủ decor, và đọc cột phần đã trừ")
def _giu_het_decor():
	from vagabond import giu_ton_web as g

	def moi(decor, lam):
		vet = []

		def sql(q, args=None, **kw):
			vet.append(q)
			if "tabSingles" in q:
				return [("pancake_shop_id",)]
			if "tabKiem Banh Dong" in q:
				return []
			if "tabBTP Banh O Dong" in q:
				return [D(ma_hang=EPI, ten_banh="Bánh Ổ Epi 12cm", so_decor=decor, decor_da_lam=lam,
					so_refill=0, refill_tu=None, refill_den=None)]
			if "tabVagabond Don Web" in q:
				return []
			raise AssertionError(q)
		return D(db=D(sql=sql)), vet

	h = [{"variation_id": EPI, "quantity": 1}]
	for decor, lam, chan in ((0, 1, True), (-1, 2, True), (0, 0, False), (2, 1, False)):
		f, vet = moi(decor, lam)
		with patch.object(g, "frappe", f), patch.object(g, "hom_nay", lambda: date(2026, 11, 11)):
			nhac, giu = g.kiem_va_giu(h, "2026-11-12")
		la("decor %s, đã trừ %s: chặn" % (decor, lam), bool(nhac), chan)
	dung("câu SQL đọc cột decor_da_lam", any("decor_da_lam" in q for q in vet if "tabBTP Banh O Dong" in q))
