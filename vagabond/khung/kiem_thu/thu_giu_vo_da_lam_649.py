# -*- coding: utf-8 -*-
"""v649 Codex #552 vòng 7: đơn đã có bánh bếp làm xong không giữ vỏ BTP lần nữa,
ở MỌI ngày và MỌI chỗ tính, và bánh làm xong đã bị kênh khác, giữ chỗ, huỷ lấy
mất thì đơn vẫn phải giữ vỏ.

Từ v649 bếp nhập Bếp làm là trừ BTP sẵn, Đủ decor ngay, cả khi nhập trên bảng
Kiểm bánh của ngày mai (chip ngày tới trên màn Kiểm bánh). Hai đường lỗi Codex
tìm, đều tái hiện được trước khi sửa:
  1. Bếp làm trước 3 bánh cho 3 đơn ngày mai: vỏ trừ 3 rồi đơn ngày mai vẫn giữ
     3 vỏ nữa (Còn nhận 3 ngày 4 thay vì 7, Giao ngày mai 3 thay vì 6; web tab
     Đặt bánh trước và cửa nhận đơn ngày mai báo còn 3 thay vì 6).
  2. Hôm nay bếp làm 3, kênh khác bán cả 3, còn 2 đơn Pancake: máy coi 2 đơn đã
     có bánh nên thôi giữ vỏ (Còn nhận 7 thay vì 5).

Mọi chỗ gọi đúng một phép btp.don_con_giu_vo. Ca chạy hàm THẬT (bang_btp,
_dat_truoc_theo_decor, ton_don_web.kiem, giu_ton_web.kiem_va_giu) trên dữ liệu
giả, không gọi thêm hàm nào "cho chắc".
"""
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace as D
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import btp  # noqa: E402
from vagabond.khung.kiem_thu import thu_refill_646 as rf  # noqa: E402

GOC = Path(__file__).parents[3]
KANKIN = "BAWC00123"  # Kankin 16 trong bộ kiểm refill; hôm nay của bộ đó là 10/11/2026
MAI = "KB-2026-11-11"
NAY = "KB-2026-11-10"
# Sáng BTP sẵn 10, Đủ decor 9; bếp làm trước 3 bánh cho ngày mai nên máy đã trừ còn 7/6.
SAU_LAM = dict(rf.KANKIN, so_btp=7, so_decor=6, decor_da_lam=3)


COT = ("da_dat", "phat_sinh", "cho_chot", "sx", "huy", "don_khac", "giu_cho")


def _du_cot(kb):
	"""Dòng Kiểm bánh đủ cột như Frappe trả (ô trống là 0)."""
	return {t: [dict({c: 0 for c in COT}, **x) for x in ds] for t, ds in kb.items()}


def _bang(kb, dong=SAU_LAM):
	m = rf._chay(rf.Kho([dong], _du_cot(kb)), btp.bang_btp, rf._tinh_that(don=[]))
	d = m["dong"][0]
	return d["dang_giu"], d["con_nhan"], d["giao_mai"]


@ca("v649 thuần don_con_giu_vo: đơn có bánh làm xong thôi giữ vỏ; bánh làm xong bị kênh khác, giữ chỗ, huỷ, đơn khác lấy trước thì đơn vẫn giữ")
def _thuan():
	g = btp.don_con_giu_vo
	la("chưa làm: giữ đủ", g({"da_dat": 2, "phat_sinh": 1}), 3)
	la("làm 1 cho 3 đơn: giữ 2", g({"da_dat": 3, "sx": 1}), 2)
	la("làm dư: giữ 0", g({"da_dat": 2, "sx": 5}), 0)
	la("kênh khác bán hết bánh làm: giữ đủ 2", g({"da_dat": 2, "sx": 3, "don_khac": 3}), 2)
	la("giữ chỗ và huỷ cũng lấy bánh làm", g({"da_dat": 2, "sx": 3, "giu_cho": 1, "huy": 1}), 1)
	la("huỷ âm (đính chính) không thành bánh thêm", g({"da_dat": 2, "sx": 1, "huy": -3}), 1)
	la("chỉ tính đơn đặt: phát sinh, chờ chốt lấy bánh làm trước", g({"da_dat": 2, "phat_sinh": 1, "cho_chot": 1, "sx": 3}, ("da_dat",)), 1)
	la("đơn âm giữ nguyên như cũ", g({"da_dat": -1, "sx": 2}), -1)
	la("đọc được dòng Frappe kiểu thuộc tính", g(D(da_dat=3, sx=1, phat_sinh=None)), 2)


@ca("v649 Codex #552 vòng 7 (btp.py:106): bếp làm trước 3 bánh trên bảng ngày mai cho 3 đơn ngày mai: không giữ vỏ lần hai (Còn nhận 7, Giao ngày mai 6)")
def _ngay_mai():
	la("bảng BTP", _bang({MAI: [{"ma_hang": KANKIN, "da_dat": 3, "sx": 3}]}), (0, 7, 6))
	la("chưa làm thì giữ đủ 3 như cũ", _bang({MAI: [{"ma_hang": KANKIN, "da_dat": 3}]}, dict(rf.KANKIN, so_btp=10, so_decor=9)), (3, 7, 6))
	la("ngày kia cũng vậy", _bang({"KB-2026-11-12": [{"ma_hang": KANKIN, "da_dat": 2, "sx": 2}]}), (0, 7, 6))


@ca("v649 Codex #552 vòng 7 (btp.py:181): hôm nay bếp làm 3, kênh khác bán cả 3, còn 2 đơn Pancake: vẫn giữ 2 vỏ (Còn nhận 5, không phải 7)")
def _kenh_khac():
	la("bảng BTP", _bang({NAY: [{"ma_hang": KANKIN, "sx": 3, "don_khac": 3, "da_dat": 2}]}), (2, 5, 6))
	la("kênh khác chỉ lấy 1: 2 đơn đã có bánh", _bang({NAY: [{"ma_hang": KANKIN, "sx": 3, "don_khac": 1, "da_dat": 2}]}), (0, 7, 6))


@ca("v649 Codex #552 vòng 7: tab Đặt bánh trước trên web hiện đúng số còn nhận khi bếp đã làm trước bánh cho đơn ngày mai")
def _tab_dat_truoc():
	m = rf.du_lieu_web(kankin=SAU_LAM, kb=_du_cot({MAI: [{"ma_hang": KANKIN, "da_dat": 3, "sx": 3}]}))
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("Đủ decor 6, 3 đơn đã có bánh: còn 6", s[KANKIN]["con"], 6)
	m = rf.du_lieu_web(kankin=dict(rf.KANKIN, so_decor=9), kb=_du_cot({MAI: [{"ma_hang": KANKIN, "da_dat": 3}]}))
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("chưa làm: 9 trừ 3 đơn như cũ", s[KANKIN]["con"], 6)


def _ton_don(kb_mai, decor=6, lam=3):
	from vagabond import ton_don_web as ton

	nguon = D(db=D(exists=lambda dt, ten: ten == MAI),
		get_doc=lambda dt, ten: D(dong=[D(**x) for x in _du_cot({MAI: kb_mai})[MAI]]),
		get_single=lambda *a: D(dong=[D(ma_hang=KANKIN, ten_banh="Kankin 16", so_decor=decor, decor_da_lam=lam,
			so_refill=0, refill_tu=None, refill_den=None)]))
	with patch.object(ton, "hom_nay", lambda: date(2026, 11, 10)), patch.object(ton, "frappe", nguon):
		return ton.kiem([{"variation_id": KANKIN, "quantity": 6}], "2026-11-11")


@ca("v649 Codex #552 vòng 7: cửa nhận đơn web ngày mai nhận 6 bánh khi Đủ decor còn 6 và 3 đơn ngày mai đã có bánh bếp làm")
def _cua_nhan():
	la("nhận", _ton_don([{"ma_hang": KANKIN, "da_dat": 3, "sx": 3}]), [])
	dung("chưa làm: Đủ decor 6 trừ 3 đơn còn 3, đặt 6 thì chặn",
		"còn 3 cái" in "".join(_ton_don([{"ma_hang": KANKIN, "da_dat": 3}])))


def _giu_ton(kb_mai, decor=6, lam=3):
	from vagabond import giu_ton_web as g
	vet = []

	def sql(q, args=None, **kw):
		vet.append(q)
		if "tabSingles" in q:
			return [("pancake_shop_id",)]
		if "tabKiem Banh Dong" in q:
			return [D(**x) for x in _du_cot({MAI: kb_mai})[MAI]] if args and args[0] == MAI else []
		if "tabBTP Banh O Dong" in q:
			return [D(ma_hang=KANKIN, ten_banh="Kankin 16", so_decor=decor, decor_da_lam=lam,
				so_refill=0, refill_tu=None, refill_den=None)]
		if "tabVagabond Don Web" in q:
			return []
		raise AssertionError(q)

	with patch.object(g, "frappe", D(db=D(sql=sql))), patch.object(g, "hom_nay", lambda: date(2026, 11, 10)):
		nhac, giu = g.kiem_va_giu([{"variation_id": KANKIN, "quantity": 6}], "2026-11-11")
	return nhac, vet


@ca("v649 Codex #552 vòng 7: lượt giữ tồn cuối cùng (giu_ton_web) cũng không giữ vỏ lần hai cho đơn ngày mai đã có bánh, và đọc đủ cột")
def _giu_ton_web():
	nhac, vet = _giu_ton([{"ma_hang": KANKIN, "ten_banh": "Kankin 16", "co_the_ban": 0, "da_dat": 3, "sx": 3}])
	la("nhận", nhac, [])
	nhac, vet = _giu_ton([{"ma_hang": KANKIN, "ten_banh": "Kankin 16", "co_the_ban": 0, "da_dat": 3}])
	dung("chưa làm thì chặn", "còn 3 cái" in "".join(nhac))
	cau = [q for q in vet if "tabKiem Banh Dong" in q][0]
	dung("câu SQL đọc đủ cột phép giữ vỏ cần", all(c in cau for c in ("sx", "huy", "don_khac", "giu_cho", "phat_sinh", "cho_chot")))


@ca("v649 một nguồn: không còn chỗ nào tự trừ đơn đặt vào Đủ decor, BTP sẵn mà không qua btp.don_con_giu_vo")
def _mot_nguon():
	for tep in ("btp.py", "ton_don_web.py", "giu_ton_web.py", "kiem_banh.py"):
		ma = (GOC / "vagabond" / tep).read_text(encoding="utf-8")
		tu_tinh = re.findall(r"\+\s*int\(d\.da_dat or 0\)|\+ \(d\.da_dat or 0\)", ma)
		la("%s không tự cộng da_dat" % tep, tu_tinh, [])
	dung("không còn giu_hom_nay", "def giu_hom_nay" not in (GOC / "vagabond" / "btp.py").read_text(encoding="utf-8"))
