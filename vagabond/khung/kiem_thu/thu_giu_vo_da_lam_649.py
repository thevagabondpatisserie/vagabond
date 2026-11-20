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

v671: web không còn theo Đủ decor (xem ba ca v671 bên dưới); phần bảng BTP giữ nguyên.
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
	# v677: ô Còn nhận mai cũ bỏ; số thứ ba là ô Web nhận ngày kia (BTP sẵn).
	return d["dang_giu"], d["con_nhan"], d["web"][1][1]


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


@ca("v649 Codex #552 vòng 7 (btp.py:106): bếp làm trước 3 bánh trên bảng ngày mai cho 3 đơn ngày mai: không giữ vỏ lần hai (Còn nhận 7, v677 web ngày kia 7)")
def _ngay_mai():
	la("bảng BTP", _bang({MAI: [{"ma_hang": KANKIN, "da_dat": 3, "sx": 3}]}), (0, 7, 7))
	la("chưa làm thì giữ đủ 3 như cũ", _bang({MAI: [{"ma_hang": KANKIN, "da_dat": 3}]}, dict(rf.KANKIN, so_btp=10, so_decor=9)), (3, 7, 7))
	la("ngày kia cũng vậy", _bang({"KB-2026-11-12": [{"ma_hang": KANKIN, "da_dat": 2, "sx": 2}]}), (0, 7, 7))


@ca("v649 Codex #552 vòng 7 (btp.py:181): ngày mai bếp làm 3, kênh khác bán cả 3, còn 2 đơn Pancake: vẫn giữ 2 vỏ (Còn nhận 5, không phải 7)")
def _kenh_khac():
	# v677: đơn hôm nay bán theo tủ, không trừ vỏ; ca đặt vào phiếu ngày mai.
	la("bảng BTP", _bang({MAI: [{"ma_hang": KANKIN, "sx": 3, "don_khac": 3, "da_dat": 2}]}), (2, 5, 5))
	la("kênh khác chỉ lấy 1: 2 đơn đã có bánh", _bang({MAI: [{"ma_hang": KANKIN, "sx": 3, "don_khac": 1, "da_dat": 2}]}), (0, 7, 7))
	la("v677: đơn hôm nay không trừ vào số ngày kia", _bang({NAY: [{"ma_hang": KANKIN, "sx": 0, "da_dat": 2}]}), (0, 7, 7))


# v671 (Sales góp ý 18/11/2026, giám đốc chốt): web tab Đặt bánh trước, cửa nhận
# đơn và lượt giữ tồn ngày mai lấy cột Có thể bán của phiếu Kiểm bánh NGÀY MAI.
# Cột đó máy tính ở KiemBanhNgay.validate (tồn chuyển + Bếp làm - đơn), nên bánh
# bếp làm trước cho đơn ngày mai tự không bị trừ hai lần; Đủ decor không còn tính.
# Ba ca dưới thay ba ca v649 cũ theo Đủ decor.


@ca("v671 tab Đặt bánh trước trên web: số ngày mai là Có thể bán của phiếu ngày mai; v677 ngày kia theo BTP sẵn, Đủ decor không tính")
def _tab_dat_truoc():
	m = rf.du_lieu_web(kankin=SAU_LAM, kb=_du_cot({MAI: [{"ma_hang": KANKIN, "da_dat": 3, "sx": 3, "co_the_ban": 4}]}))
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("Có thể bán 4 (Đủ decor 6 không tính)", s[KANKIN]["con"], 4)
	m = rf.du_lieu_web(kankin=dict(rf.KANKIN, so_btp=9, so_decor=0), kb=_du_cot({MAI: [{"ma_hang": KANKIN, "da_dat": 3, "co_the_ban": 0}]}))
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("Có thể bán 0: ngày mai 0, ngày kia theo BTP sẵn 9 trừ 3 đơn ngày mai (Đủ decor 0 không chặn)", (s[KANKIN]["con_mai"], s[KANKIN]["con_xa"]), (0, 6))


def _ton_don(kb_mai, decor=6, lam=3):
	from vagabond import ton_don_web as ton

	nguon = D(db=D(exists=lambda dt, ten: ten == MAI),
		get_doc=lambda dt, ten: D(dong=[D(**x) for x in _du_cot({MAI: kb_mai})[MAI]]),
		get_single=lambda *a: D(dong=[D(ma_hang=KANKIN, ten_banh="Kankin 16", so_decor=decor, decor_da_lam=lam,
			so_refill=0, refill_tu=None, refill_den=None)]))
	with patch.object(ton, "hom_nay", lambda: date(2026, 11, 10)), patch.object(ton, "frappe", nguon):
		return ton.kiem([{"variation_id": KANKIN, "quantity": 6}], "2026-11-11")


@ca("v671 cửa nhận đơn web ngày mai: theo Có thể bán của phiếu ngày mai, Đủ decor không tính")
def _cua_nhan():
	la("Có thể bán 6, đặt 6: nhận", _ton_don([{"ma_hang": KANKIN, "ten_banh": "Kankin 16", "da_dat": 3, "sx": 3, "co_the_ban": 6}], decor=0), [])
	dung("Có thể bán 3, đặt 6: chặn dù Đủ decor 9",
		"còn 3 cái" in "".join(_ton_don([{"ma_hang": KANKIN, "ten_banh": "Kankin 16", "da_dat": 3, "co_the_ban": 3}], decor=9)))


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


@ca("v671 lượt giữ tồn cuối cùng (giu_ton_web) ngày mai: theo Có thể bán của phiếu ngày mai, khoá dòng phiếu")
def _giu_ton_web():
	nhac, vet = _giu_ton([{"ma_hang": KANKIN, "ten_banh": "Kankin 16", "co_the_ban": 6, "da_dat": 3, "sx": 3}], decor=0)
	la("nhận", nhac, [])
	nhac, vet = _giu_ton([{"ma_hang": KANKIN, "ten_banh": "Kankin 16", "co_the_ban": 3, "da_dat": 3}], decor=9)
	dung("Có thể bán 3 thì chặn dù Đủ decor 9", "còn 3 cái" in "".join(nhac))
	cau = [q for q in vet if "tabKiem Banh Dong" in q][0]
	dung("đọc dòng phiếu dưới khoá", "co_the_ban" in cau and "for update" in cau)


@ca("v649 một nguồn: không còn chỗ nào tự trừ đơn đặt vào Đủ decor, BTP sẵn mà không qua btp.don_con_giu_vo")
def _mot_nguon():
	for tep in ("btp.py", "ton_don_web.py", "giu_ton_web.py", "kiem_banh.py"):
		ma = (GOC / "vagabond" / tep).read_text(encoding="utf-8")
		tu_tinh = re.findall(r"\+\s*int\(d\.da_dat or 0\)|\+ \(d\.da_dat or 0\)", ma)
		la("%s không tự cộng da_dat" % tep, tu_tinh, [])
	dung("không còn giu_hom_nay", "def giu_hom_nay" not in (GOC / "vagabond" / "btp.py").read_text(encoding="utf-8"))
