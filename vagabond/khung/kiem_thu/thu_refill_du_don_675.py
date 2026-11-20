# -*- coding: utf-8 -*-
"""v675 (Sales báo 19/11/2026, giám đốc chốt "Đợt đủ đơn thì bán Đủ decor";
v677: nguồn đó nay là BTP sẵn, anh Việt chọn hướng A 20/11/2026):
đợt refill đã nhận đủ đơn (Còn nhận refill bằng 0) không còn giữ các ngày của nó.
Các ngày đó bánh bán theo luật bánh đặt trước thường: ngày mai theo cột Có thể bán
của phiếu Kiểm bánh ngày mai (v671), ngày xa hơn thì nhắc chọn ngày của đợt còn nhận.

Ca gốc trên site 19/11/2026: Tira-Missing-U 12cm có đợt 1 (5 bánh, giao 17/11 tới
23/11) đã nhận đủ 5 đơn và đợt 2 (10 bánh, 24/11 tới 30/11). Thẻ web bỏ đợt 1 nên
hiện số của bánh thường, còn lúc gửi đơn máy chủ vẫn tính ngày 20/11 theo đợt 1
nên báo "chỉ còn 0 cái". Hai nguồn số lệch nhau.

Các ca chạy hàm THẬT (ton_don_web.kiem, giu_ton_web.kiem_va_giu,
giu_ton_web.kiem_va_giu_refill, kiem_banh._dat_truoc_theo_decor, refill.tinh) với
tầng Frappe và Pancake giả.
"""
import datetime as dt
import json
import unittest.mock as um
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, gia_lap, la

gia_lap()

from vagabond import refill as rf  # noqa: E402
from vagabond.khung.kiem_thu import thu_refill_646 as t646  # noqa: E402

D8 = dt.date
NAY = D8(2026, 11, 19)
MA = "BAWC00077"
TEN = "Bánh Ổ Tira-Missing-U 3.0, size 12cm"
DOT = [{"id": "d1", "so": 5, "tu": "2026-11-17", "den": "2026-11-23", "da_dat": None},
	{"id": "d2", "so": 10, "tu": "2026-11-24", "den": "2026-11-30", "da_dat": None}]
TIRA = {"ma_hang": MA, "ten_banh": TEN, "hinh": "", "so_btp": 6, "so_decor": 6, "decor_da_lam": 9,
	"so_refill": 0, "refill_tu": None, "refill_den": None, "refill_dot": json.dumps(DOT)}
# Năm đơn Pancake trong đợt 1 (giờ UTC, 03:00 UTC là 10:00 giờ Việt Nam).
DON_DU = [t646._don(MA, "2026-11-%02dT03:00:00" % d, 1) for d in (17, 18, 20, 22, 22)]
KB_MAI = {"KB-2026-11-20": [{"ma_hang": MA, "ten_banh": TEN, "co_the_ban": 2, "da_dat": 1}]}


def _tinh(don, loi=False):
	goc = rf.tinh

	def t(hom_nay=None, moi=False, dong=None):
		def dtl(hn=None, moi=False, tu=None):
			if loi:
				raise Exception("Pancake 429")
			return rf.dem_theo_ngay(don, t646._ngay_vn), rf.id_da_dem(don)
		import frappe
		with um.patch.object(rf, "dem_va_id", dtl), um.patch.object(frappe, "log_error", lambda *a, **k: None, create=True), \
				um.patch.object(frappe, "cache", lambda: t646._BoNho(), create=True):
			return goc(NAY, moi, dong)
	return t


def _kiem(sl, ngay, don=DON_DU, kb=KB_MAI, loi=False):
	from vagabond import ton_don_web

	kho = t646.Kho([TIRA], kb)
	return t646._chay(kho, lambda: ton_don_web.kiem([{"variation_id": MA, "quantity": sl}], ngay), _tinh(don, loi), nay=NAY)


def _giu(sl, ngay, don=DON_DU, ctb=2, loi=False):
	"""Chạy THẬT kiem_va_giu rồi kiem_va_giu_refill như cửa tạo đơn (don_hang)."""
	from vagabond import giu_ton_web as g

	def sql(q, ts=None, as_dict=False, **kw):
		if "tabSingles" in q:
			return [("pancake_shop_id",)]
		if "tabKiem Banh Dong" in q:
			return [NS(ma_hang=MA, ten_banh=TEN, co_the_ban=ctb, da_dat=1, phat_sinh=0, cho_chot=0, sx=3, huy=0,
				don_khac=0, giu_cho=0)] if ts and ts[0] == "KB-2026-11-20" else []
		if "tabBTP Banh O Dong" in q:
			return [NS(**TIRA)]
		if "tabVagabond Don Web" in q:
			return []
		raise AssertionError(q)
	h = [{"variation_id": MA, "quantity": sl}]
	with um.patch.object(g, "hom_nay", lambda: NAY), um.patch.object(g, "frappe", NS(db=NS(sql=sql))), \
			um.patch.object(rf, "tinh", _tinh(don, loi)):
		return g.kiem_va_giu(h, ngay), g.kiem_va_giu_refill(h, ngay)


@ca("v675 phép thuần bo_dot_du_don: bỏ đợt đã nhận đủ đơn (còn 0 hay âm); đợt chưa đếm được giữ nguyên; Pancake lỗi giữ mọi đợt")
def _thuan():
	hl = rf.hieu_luc_tu_dong([Doi(TIRA)], NAY)
	so = {"refill": {MA: [dict(DOT[0], con=0), dict(DOT[1], con=10)]}, "loi": ""}
	la("đợt 1 đủ đơn bị bỏ", [r["id"] for r in rf.bo_dot_du_don(hl, so)[MA]], ["d2"])
	so = {"refill": {MA: [dict(DOT[0], con=-1), dict(DOT[1], con=0)]}, "loi": ""}
	la("mọi đợt đủ đơn: mã không còn đợt nào", rf.bo_dot_du_don(hl, so), {})
	so = {"refill": {MA: [dict(DOT[0], con=None), dict(DOT[1], con=3)]}, "loi": ""}
	la("đợt chưa đếm được (None) giữ nguyên", [r["id"] for r in rf.bo_dot_du_don(hl, so)[MA]], ["d1", "d2"])
	la("Pancake lỗi: giữ mọi đợt như cũ", rf.bo_dot_du_don(hl, {"refill": {}, "loi": "Chưa đếm được"}), hl)
	la("không có kết quả đếm: giữ mọi đợt", rf.bo_dot_du_don(hl, None), hl)


@ca("v675 ca gốc 19/11: đợt 1 của 12cm đã đủ 5 đơn, khách đặt 1 bánh nhận 20/11 (ngày mai) thì nhận theo phiếu ngày mai (Có thể bán 2), không báo còn 0")
def _ca_goc():
	la("ngày mai, đặt 1: nhận", _kiem(1, "2026-11-20"), [])
	dung("ngày mai, đặt 3: chặn theo phiếu ngày mai (còn 2)", "chỉ còn 2 cái" in "".join(_kiem(3, "2026-11-20")))
	(n, giu), (n_rf, giu_rf) = _giu(1, "2026-11-20")
	la("cửa tạo đơn: giữ theo phiếu ngày mai, không giữ suất mẻ", (n, giu["dong"] if giu else None, n_rf, giu_rf),
		([], {MA: 1}, [], None))
	(n, giu), _ = _giu(1, "2026-11-20", ctb=0)
	dung("phiếu ngày mai hết: cửa tạo đơn chặn", bool(n) and "chỉ còn 0 cái" in n[0])


@ca("v675, v677 đợt 1 đủ đơn: ngày kia 21/11 bán theo BTP sẵn (6, trừ đơn chưa làm và phần vượt đợt); ngày 23/11 (sau 3 ngày tới) nhắc chọn ngày của đợt 2")
def _ngay_xa():
	la("21/11 đặt 1: nhận theo BTP sẵn", _kiem(1, "2026-11-21"), [])
	dung("21/11 đặt 7: còn 6", "chỉ còn 6 cái" in "".join(_kiem(7, "2026-11-21")))
	vuot = DON_DU + [t646._don(MA, "2026-11-23T03:00:00", 1)]
	dung("đợt 1 nhận vượt 1 đơn: phần vượt trừ vào BTP sẵn (còn 5)", "chỉ còn 5 cái" in "".join(_kiem(7, "2026-11-21", don=vuot)))
	(n, giu), (n_rf, giu_rf) = _giu(1, "2026-11-21")
	la("cửa tạo đơn 21/11: giữ theo BTP sẵn, không giữ suất mẻ", (n, giu and giu["dong"], n_rf, giu_rf), ([], {MA: 1}, [], None))
	(n, _g), _ = _giu(7, "2026-11-21")
	dung("cửa tạo đơn 21/11 đặt 7: chặn (còn 6)", bool(n) and "chỉ còn 6 cái" in n[0])
	r = _kiem(1, "2026-11-23")
	dung("23/11 sau 3 ngày tới: nhắc đúng khoảng đợt 2, không nhắc đợt đã đủ", len(r) == 1 and "từ 24/11 tới 30/11" in r[0] and "17/11" not in r[0])
	_, (n_rf, _g) = _giu(1, "2026-11-23")
	dung("cửa tạo đơn chặn 23/11 thuộc đợt đã đủ", bool(n_rf))
	la("đợt 2 còn nhận: đặt 2 ngày 25/11 nhận", _kiem(2, "2026-11-25"), [])


@ca("v675 đợt 1 còn suất thì vẫn theo đợt như cũ; Pancake lỗi thì không chặn và không tự chuyển sang phiếu ngày mai")
def _con_suat():
	bon = DON_DU[:4]
	la("đợt 1 còn 1: đặt 1 ngày 20/11 nhận theo đợt", _kiem(1, "2026-11-20", don=bon), [])
	dung("đặt 2: chặn theo đợt (còn 1), không theo phiếu 2", "chỉ còn 1 cái" in "".join(_kiem(2, "2026-11-20", don=bon)))
	(n, giu), (n_rf, giu_rf) = _giu(1, "2026-11-20", don=bon)
	la("cửa tạo đơn: giữ suất mẻ, không giữ theo phiếu", (n, giu, n_rf, giu_rf and giu_rf["dong"]), ([], None, [], {MA: 1}))
	from vagabond import ton_don_web
	import frappe
	with um.patch.object(ton_don_web, "bao_loi", lambda ng: None), um.patch.object(frappe, "log_error", lambda *a, **k: None, create=True):
		la("Pancake lỗi: không chặn", _kiem(9, "2026-11-20", loi=True), [])


def du_lieu_web():
	"""Tab Đặt bánh trước của ca gốc dựng bằng kiem_banh._dat_truoc_theo_decor THẬT (ca node dùng lại)."""
	import frappe
	from vagabond import kiem_banh, tat_ban_web

	item = [{"item_code": MA, "item_name": TEN, "image": "", "standard_rate": 560000, "disabled": 0, "is_sales_item": 1}]
	kho = t646.Kho([TIRA], KB_MAI)
	with um.patch.object(frappe, "get_all", lambda *a, **k: [Doi(x) for x in item], create=True), \
			um.patch.object(tat_ban_web, "bang", lambda *a, **k: {}), \
			um.patch.object(kiem_banh, "_anh_noi_dung_web", lambda ds: ds):
		return t646._chay(kho, kiem_banh._dat_truoc_theo_decor, _tinh(DON_DU), nay=NAY)


@ca("v675 thẻ web tab Đặt bánh trước: đợt 1 đủ đơn thì số ngày mai là Có thể bán của phiếu (2), kèm đợt 2 để chọn từ 24/11; cùng nguồn với cửa nhận đơn")
def _the_web():
	m = du_lieu_web()
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	la("ngày mai theo phiếu (2), ngày kia theo BTP sẵn (6), đợt 2 để chọn ngày sau",
		(s[MA]["con"], s[MA]["con_mai"], s[MA]["con_xa"], s[MA]["refill"]["chi_refill"], [(d["tu"], d["con"]) for d in s[MA]["refill"]["ds"]]),
		(2, 2, 6, 0, [("2026-11-24", 10)]))


@ca("v675 (Codex #588): bếp CHƯA mở phiếu ngày mai, bánh có mẻ 14/11 tới 20/11, khách đặt nhận ngày mai 11/11: nhắc chọn ngày trong mẻ (trước bản sửa: nổ lỗi, đơn lọt qua)")
def _chua_co_phieu():
	from vagabond import ton_don_web

	kho = t646.Kho([t646.ROMAN], {})
	r = t646._chay(kho, lambda: ton_don_web.kiem([{"variation_id": "BAWC00068", "quantity": 1}], "2026-11-11"), t646._tinh_that(don=[]))
	la("nhắc chọn ngày trong mẻ", r, ["Roman De La Rose 18 nhận giao từ 14/11 tới 20/11, quý khách chọn ngày nhận trong khoảng này."])


@ca("v675, v677 bánh đặt trước thường: ngày mai theo phiếu, ngày kia và ngày thứ ba theo BTP sẵn trừ đơn chưa làm của ba ngày tới, ngày thứ tư nhắc 3 ngày tới; BTP sẵn 0 thì hết dù Đủ decor còn")
def _thuong():
	from vagabond import ton_don_web

	ka = dict(t646.KANKIN, so_btp=5, so_decor=0, decor_da_lam=0)
	kb = {"KB-2026-11-11": [{"ma_hang": "BAWC00123", "ten_banh": "Kankin 16", "co_the_ban": 1, "da_dat": 1, "sx": 0}],
		"KB-2026-11-12": [{"ma_hang": "BAWC00123", "ten_banh": "Kankin 16", "co_the_ban": 0, "da_dat": 2, "sx": 0}]}

	def k(sl, ngay, kho_kb=kb, dong=ka):
		return t646._chay(t646.Kho([dong], kho_kb), lambda: ton_don_web.kiem([{"variation_id": "BAWC00123", "quantity": sl}], ngay),
			t646._tinh_that(don=[]))
	dung("ngày mai 11/11: theo phiếu (còn 1)", "chỉ còn 1 cái" in "".join(k(2, "2026-11-11")))
	la("ngày kia 12/11: BTP sẵn 5 trừ 3 đơn chưa làm (Đủ decor 0 không chặn), đặt 2 nhận", k(2, "2026-11-12"), [])
	dung("ngày thứ ba 13/11 đặt 3: còn 2", "chỉ còn 2 cái" in "".join(k(3, "2026-11-13")))
	r = k(1, "2026-11-14")
	dung("ngày thứ tư: nhắc nhận trong 3 ngày tới", len(r) == 1 and "nhận trong 3 ngày tới" in r[0])
	dung("BTP sẵn 0 (Đủ decor 9): ngày kia hết", "chỉ còn 0 cái" in "".join(k(1, "2026-11-12", dong=dict(ka, so_btp=0, so_decor=9))))
	la("phép thuần con_btp: bếp đã làm cho đơn thì không trừ vỏ lần hai",
		ton_don_web.con_btp([Doi(ka)], [(D8(2026, 11, 11), [Doi(ma_hang="BAWC00123", da_dat=2, sx=2)])], D8(2026, 11, 10)),
		{"BAWC00123": (5, "Kankin 16")})


@ca("Codex #594 tái hiện (v677 theo BTP sẵn): đợt 5 bánh nhận 6 đơn, Bếp đã làm cả 6 (BTP sẵn đã bị trừ, còn 1): ngày kia còn 1 suất, không trừ phần vượt lần hai; chưa làm bánh nào thì trừ 1; còn 1 đơn chưa làm thì vẫn giữ 1 vỏ")
def _vuot_da_lam():
	from vagabond import ton_don_web as tw

	nay = D8(2026, 11, 19)
	btp = [Doi(ma_hang="BAWC00201", ten_banh="Tira 12", so_btp=1, so_decor=0, decor_da_lam=0)]
	so = {"refill": {"BAWC00201": [{"tu": "2026-11-17", "den": "2026-11-23", "so": 5, "da_dat": 6, "con": -1}]}, "loi": ""}

	def con(phieu, truyen=True):
		dl = tw.da_lam_dot_vuot(so, nay, doc_dong=lambda ng: phieu.get(ng.isoformat())) if truyen else None
		return tw.con_btp(btp, [], nay, {}, so, dl)["BAWC00201"][0]

	dong = lambda dat, sx, **k: [Doi(ma_hang="BAWC00201", da_dat=dat, sx=sx, **k)]
	la("cả 6 đơn đã làm (2 hôm qua, 4 ngày mai): còn 1", con({"2026-11-18": dong(2, 2), "2026-11-20": dong(4, 4)}), 1)
	la("chưa làm bánh nào: trừ 1 phần vượt, còn 0", con({"2026-11-20": dong(6, 0)}), 0)
	la("làm 5, còn 1 đơn chưa có bánh: vẫn giữ 1 vỏ", con({"2026-11-20": dong(6, 5)}), 0)
	la("bánh làm xong bị kênh khác lấy thì không tính cho đơn", con({"2026-11-20": dong(6, 6, don_khac=2)}), 0)
	la("chưa có phiếu nào của đợt: coi như chưa làm", con({}), 0)
	la("nơi gọi không truyền số đã làm: trừ cả phần vượt như trước", con({"2026-11-20": dong(6, 6)}, truyen=False), 0)
	la("mã khác trên cùng phiếu không tính", con({"2026-11-20": [Doi(ma_hang="BAWC00999", da_dat=6, sx=6)]}), 0)
	la("đợt chưa vượt hay Pancake lỗi: không đọc phiếu", (tw.da_lam_dot_vuot({"refill": {"X": [{"tu": "2026-11-17", "den": "2026-11-23", "con": 2}]}}, nay, doc_dong=lambda ng: 1 / 0),
		tw.da_lam_dot_vuot({"loi": "x", "refill": {}}, nay), tw.da_lam_dot_vuot(None, nay)), ({}, {}, {}))


@ca("Codex #594 một nguồn: thẻ web, cửa nhận đơn, cửa giữ hàng và bảng Kiểm bánh đều truyền số đã làm của đợt vượt vào con_btp")
def _mot_nguon():
	import inspect
	from vagabond import giu_ton_web, kiem_banh, ton_don_web

	from vagabond import btp
	for ten, ham in (("cửa nhận đơn", ton_don_web._con_btp_web), ("cửa giữ hàng", giu_ton_web.kiem_va_giu), ("thẻ web", kiem_banh._dat_truoc_theo_decor)):
		dung(ten, "da_lam_dot_vuot(" in inspect.getsource(ham))
	# v677: bảng Kiểm bánh (bang_btp) đi qua đúng hàm của cửa nhận đơn.
	dung("bảng Kiểm bánh", "_con_btp_web(" in inspect.getsource(btp.bang_btp) and "so_web_ba_ngay(" in inspect.getsource(btp.bang_btp))
	dung("không còn chỗ nào đọc Đủ decor để tính số web", all("so_decor" not in inspect.getsource(h)
		for h in (ton_don_web.con_btp, ton_don_web.so_web_ba_ngay, ton_don_web.kiem)))



@ca("v677 phép thuần so_web_ba_ngay (ba ô Web nhận của bảng Kiểm bánh): ngày mai theo phiếu, chưa có phiếu là chưa biết; ngày kia, ngày thứ ba theo BTP sẵn; ngày thuộc đợt đang mở theo số còn của đợt, chưa đếm được là chưa biết")
def _so_web():
	from vagabond import ton_don_web as tw

	nay = D8(2026, 11, 19)
	rf = {MA: [{"so": 10, "tu": D8(2026, 11, 22), "den": D8(2026, 11, 28)}]}
	so = {"refill": {MA: [{"tu": "2026-11-22", "den": "2026-11-28", "so": 10, "da_dat": 3, "con": 7}]}, "loi": ""}
	la("phiếu ngày mai, BTP sẵn, đợt", tw.so_web_ba_ngay(MA, nay, {MA: 2}, {MA: 5}, rf, so),
		[(D8(2026, 11, 20), 2, "phieu"), (D8(2026, 11, 21), 5, "btp"), (D8(2026, 11, 22), 7, "refill")])
	la("chưa có phiếu ngày mai: chưa biết, không phải 0", tw.so_web_ba_ngay(MA, nay, None, {MA: 5})[0], (D8(2026, 11, 20), None, "phieu"))
	la("mã không trên phiếu, không trên BTP: 0", [x[1] for x in tw.so_web_ba_ngay("KHAC", nay, {}, {})], [0, 0, 0])
	la("số âm giữ nguyên để bảng báo nhận quá", tw.so_web_ba_ngay(MA, nay, {MA: -1}, {MA: -2})[:2],
		[(D8(2026, 11, 20), -1, "phieu"), (D8(2026, 11, 21), -2, "btp")])
	la("đợt chưa đếm được đơn: ô đợt chưa biết", tw.so_web_ba_ngay(MA, nay, {MA: 2}, {MA: 5}, rf, {"loi": "Pancake 429"})[2],
		(D8(2026, 11, 22), None, "refill"))


@ca("v677 Codex #596: bảng BTP (/btp) ghi ba ô Web nhận theo từng ngày (ngày refill theo đợt); ca hành vi chạy thật trong node đều đạt")
def _btp_web_node():
	import subprocess
	from pathlib import Path

	tep = Path(__file__).parent / "hanh_vi" / "btp_web_677.js"
	r = subprocess.run(["node", str(tep)], capture_output=True, text=True, timeout=120)
	dung("chạy được: " + (r.stdout[-1200:] + r.stderr[-400:]), r.returncode == 0)
	dung("đủ 2 ca", "2 ca dat, 0 ca hong" in r.stdout)
