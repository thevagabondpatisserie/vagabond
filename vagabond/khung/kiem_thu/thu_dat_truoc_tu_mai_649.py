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
	dung("đủ 6 ca", "6 dat, 0 hong" in r.stdout)


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
