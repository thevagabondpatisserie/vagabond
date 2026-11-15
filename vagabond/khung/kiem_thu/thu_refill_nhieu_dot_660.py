# -*- coding: utf-8 -*-
"""v660 Refill: một bánh có NHIỀU đợt, đợt cũ không bị đè.

Loan Anh và bếp báo 15/11/2026: mỗi bánh chỉ ghi được một lịch refill. Đợt 1
20 bánh nhận đơn 14/11 tới 20/11, thêm đợt 2 15 bánh 21/11 tới 27/11 thì đợt 1
bị ghi đè, không còn số để theo dõi từng đợt. Anh Việt chọn (15/11): quản lý
nhiều đợt độc lập trên một bánh, hai đợt của cùng bánh KHÔNG được trùng ngày.

Các ca chạy THẬT btp.luu_refill, btp.bang_btp, refill.tinh (tới dem_va_id),
giu_ton_web.kiem_va_giu_refill, kiem_banh._dat_truoc_theo_decor, bản vá v660
và nhịp chốt đợt đã qua, trên các bàn giả của thu_refill_646.
"""

import json
import unittest.mock as um
from types import SimpleNamespace as NS

from vagabond import refill as rf
from vagabond.khung.kiem_thu import thu_refill_646 as t646
from vagabond.khung.kiem_thu.btp_gia import BangBTP
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la, nem

D8 = t646.D8
MA = "BAWC00068"
HN = D8(2026, 11, 14)


def _hai_dot(so1=20, so2=15):
	return json.dumps([{"id": "d1", "so": so1, "tu": "2026-11-14", "den": "2026-11-20"},
		{"id": "d2", "so": so2, "tu": "2026-11-21", "den": "2026-11-27"}])


def _roman(dot=None, **kw):
	r = dict(t646.ROMAN, so_refill=0, refill_tu=None, refill_den=None, refill_dot=dot if dot is not None else _hai_dot())
	r.update(kw)
	return r


@ca("v660 phép thuần lưu đợt: đúng ví dụ Loan Anh thêm đợt 2 mà đợt 1 còn nguyên; trùng ngày bị chặn kèm câu chỉ cách làm; sửa và bỏ đúng một đợt")
def _luu_dot():
	ds, _, d1 = rf.luu_dot([], "", "20", "2026-11-14", "2026-11-20", HN, id_moi="d1")
	ds, truoc, d2 = rf.luu_dot(ds, "", "15", "2026-11-21", "2026-11-27", HN, id_moi="d2")
	la("hai đợt cùng tồn tại", sorted((x["id"], x["so"]) for x in ds), [("d1", 20), ("d2", 15)])
	la("thêm thì không có đợt trước", truoc, None)
	for tu, den in (("2026-11-18", "2026-11-24"), ("2026-11-20", "2026-11-20"), ("2026-11-27", "2026-11-30"), ("2026-11-15", "2026-11-28")):
		nem("trùng ngày %s tới %s bị chặn" % (tu, den), lambda: rf.luu_dot(ds, "", "5", tu, den, HN, id_moi="x"), rf.LoiRefill)
	try:
		rf.luu_dot(ds, "", "5", "2026-11-18", "2026-11-24", HN, id_moi="x")
	except rf.LoiRefill as e:
		dung("câu báo nêu đợt đang có và cách làm", "14/11 tới 20/11" in str(e) and "sửa số của chính đợt đó" in str(e))
	ds3, _, _ = rf.luu_dot(ds, "", "5", "2026-11-28", "2026-11-30", HN, id_moi="d3")
	la("đợt kề ngay sau thì được", len(ds3), 3)
	# Sửa số đợt 1 đang chạy (ngày có bánh 14/11 là hôm nay hoặc đã qua): không đụng đợt 2.
	ds4, truoc, sau = rf.luu_dot(ds, "d1", "25", "2026-11-14", "2026-11-20", D8(2026, 11, 16))
	la("sửa đúng đợt 1", (truoc["so"], sau["so"], [x["so"] for x in ds4 if x["id"] == "d2"]), (20, 25, [15]))
	nem("kéo dài đợt 1 chạm đợt 2 bị chặn", lambda: rf.luu_dot(ds, "d1", "20", "2026-11-14", "2026-11-22", HN), rf.LoiRefill)
	ds5, truoc, sau = rf.luu_dot(ds, "d1", "0", "", "", HN)
	la("số 0 bỏ đúng đợt 1, đợt 2 còn", ([x["id"] for x in ds5], sau), (["d2"], None))
	nem("đợt lạ", lambda: rf.luu_dot(ds, "khong-co", "5", "2026-11-14", "", HN), rf.LoiRefill)
	nem("đợt đã qua ngày không sửa được", lambda: rf.luu_dot(ds, "d1", "30", "2026-11-14", "2026-11-20", D8(2026, 11, 21)), rf.LoiRefill)
	# Đợt đã qua ngày không chặn đợt mới cùng khoảng (đã hết nhận đơn).
	ds6, _, _ = rf.luu_dot([x for x in ds if x["id"] == "d1"], "", "9", "2026-11-22", "2026-11-25", D8(2026, 11, 22), id_moi="d9")
	la("thêm đợt sau khi đợt cũ hết hạn", len(ds6), 2)


@ca("v660 đọc đợt: ô refill_dot là một nguồn; dòng chưa nâng đọc ba ô cũ thành một đợt; ô đã có chữ thì KHÔNG đọc ba ô cũ; đợt hết hạn rời danh sách đang nhận và vào Đợt đã xong")
def _doc():
	la("dòng cũ ba ô", [(x["id"], x["so"]) for x in rf.doc_dot(Doi(t646.ROMAN))], [("cu", 20)])
	la("ô mới '[]' thắng ba ô cũ", rf.doc_dot(Doi(dict(t646.ROMAN, refill_dot="[]"))), [])
	la("ô mới hỏng định dạng: không có đợt, không đọc lén ba ô cũ", rf.doc_dot(Doi(dict(t646.ROMAN, refill_dot="{hong"))), [])
	h = rf.hieu_luc_tu_dong([Doi(_roman())], HN)
	la("hai đợt xếp theo ngày", [(x["id"], x["tu"]) for x in h[MA]], [("d1", D8(2026, 11, 14)), ("d2", D8(2026, 11, 21))])
	h = rf.hieu_luc_tu_dong([Doi(_roman())], D8(2026, 11, 21))
	la("21/11: đợt 1 hết hạn, còn đợt 2", [x["id"] for x in h[MA]], ["d2"])
	q = rf.da_qua_tu_dong([Doi(_roman())], D8(2026, 11, 21))
	la("đợt 1 vào Đợt đã xong", [(x["id"], x["ma_hang"], x["so"]) for x in q], [("d1", MA, 20)])
	la("quá 60 ngày thì thôi", rf.da_qua_tu_dong([Doi(_roman())], D8(2027, 2, 1)), [])
	la("ngày thuộc đợt nào", [(rf.dot_cua(h0, MA, g) or {}).get("id") for h0 in [rf.hieu_luc_tu_dong([Doi(_roman())], HN)]
		for g in ("2026-11-13", "2026-11-14", "2026-11-20", "2026-11-21", "2026-11-27", "2026-11-28")], [None, "d1", "d1", "d2", "d2", None])


@ca("v660 số còn TỪNG ĐỢT: đợt 1 làm 20 nhận 7 còn 13, đợt 2 làm 15 nhận 3 còn 12; đơn của đợt này không ăn vào đợt kia; đếm từ ngày đầu đợt sớm nhất")
def _con_tung_dot():
	don = [dict(t646._don(MA, "2026-11-15T03:00:00", 7), id="P-1"), dict(t646._don(MA, "2026-11-22T03:00:00", 3), id="P-2")]
	kq, hoi = t646._dem_that(don, D8(2026, 11, 16), [_roman()])
	la("hai đợt, hai số còn", [(x["id"], x["so"], x["da_dat"], x["con"]) for x in kq["refill"][MA]], [("d1", 20, 7, 13), ("d2", 15, 3, 12)])
	la("đếm từ ngày đầu đợt 1", hoi, [D8(2026, 11, 14)])
	la("số còn theo ngày nhận", [rf.con_theo_ngay(kq, g).get(MA) for g in ("2026-11-20", "2026-11-21", "2026-12-01")], [13, 12, None])


@ca("v660 kiểm đơn web: ngày nhận thuộc đợt 2 thì so với số còn của đợt 2 (đợt 1 đã hết không chặn); ngày ngoài mọi đợt thì nhắc đủ hai khoảng")
def _kiem_don():
	h = rf.hieu_luc_tu_dong([Doi(_roman())], HN)
	hang = [{"variation_id": MA, "quantity": 2}]
	la("đợt 1 hết, đặt ngày 22/11 thuộc đợt 2 còn 12: nhận", rf.kiem_don(hang, "2026-11-22", h, {MA: 12}), [])
	la("đợt 2 chỉ còn 1: nhắc", rf.kiem_don(hang, "2026-11-22", h, {MA: 1}),
		["Roman De La Rose 18 ngày 22/11/2026 chỉ còn 1 cái, quý khách đang chọn 2 cái."])
	la("ngày 30/11 ngoài mọi đợt: nhắc đủ hai khoảng", rf.kiem_don(hang, "2026-11-30", h, {}),
		["Roman De La Rose 18 nhận giao từ 14/11 tới 20/11 hoặc từ 21/11 tới 27/11, quý khách chọn ngày nhận trong khoảng này."])


def _giu(dong_web, con, hang, ngay, ids=()):
	"""Chạy THẬT giu_ton_web.kiem_va_giu_refill với bảng BTP hai đợt."""
	from vagabond import giu_ton_web as g

	hoi = []

	def sql(q, ts=None, as_dict=False):
		if "tabSingles" in q:
			return [("pancake_shop_id",)]
		if "tabBTP Banh O Dong" in q:
			dung("câu đọc bảng BTP có cột refill_dot", "refill_dot" in q)
			return [NS(**_roman())]
		if "tabVagabond Don Web" in q:
			hoi.append(ts)
			return [dict(d, snapshot=json.dumps(d["snapshot"])) for d in dong_web]
		raise AssertionError(q)

	def tinh(n, moi=False, dong=None):
		return {"refill": {MA: [{"con": con[0], "tu": "2026-11-14", "den": "2026-11-20"},
			{"con": con[1], "tu": "2026-11-21", "den": "2026-11-27"}]}, "ids": list(ids), "loi": ""}
	with um.patch.object(g, "hom_nay", lambda: D8(2026, 11, 12)), um.patch.object(g, "frappe", NS(db=NS(sql=sql))), \
			um.patch.object(rf, "tinh", tinh):
		return g.kiem_va_giu_refill(hang, ngay), hoi


@ca("v660 giữ suất đơn web theo ĐÚNG ĐỢT: suất đơn web đang giữ của đợt 1 không ăn vào đợt 2; hai khách cùng lấy suất cuối của đợt 2 thì người sau bị chặn")
def _giu_suat():
	from vagabond import giu_ton_web as g

	h = [{"variation_id": MA, "quantity": 1}]
	giu_d1 = {"name": "W-1", "pancake_id": None, "snapshot": {g.O_RF: {"dong": {MA: 5}, "ngay": "2026-11-16"}}}
	(n, giu), hoi = _giu([giu_d1], (0, 1), h, "2026-11-23")
	la("đợt 2 còn 1, đơn web giữ 5 suất của đợt 1: vẫn nhận", (n, giu), ([], {"dong": {MA: 1}, "ngay": "2026-11-23"}))
	la("chỉ hỏi đơn web trong khoảng của đợt 2", hoi, [("2026-11-21", "2026-11-27")])
	giu_d2 = {"name": "W-2", "pancake_id": None, "snapshot": {g.O_RF: giu}}
	(n, _), _ = _giu([giu_d1, giu_d2], (0, 1), h, "2026-11-24")
	la("khách sau cùng đợt 2: bị chặn", n, ["Roman De La Rose 18 ngày 24/11/2026 chỉ còn 0 cái, quý khách đang chọn 1 cái."])
	(n, giu), _ = _giu([], (3, 3), h, "2026-11-30")
	la("ngày ngoài mọi đợt: không giữ suất refill", (n, giu), ([], None))


@ca("v660 cửa lưu thật btp.luu_refill: thêm đợt 2 không đè đợt 1; trùng ngày bị chặn; sửa và bỏ đúng đợt; nhật ký ghi từng đợt; bảng trả danh sách đợt và lịch refill đủ hai dòng")
def _cua_luu():
	import frappe
	from vagabond import btp

	kho = t646.Kho([dict(t646.KANKIN)])
	luu = lambda *a, **k: t646._chay(kho, lambda: btp.luu_refill("BAWC00123", *a, **k), nay=HN)
	dem = iter(range(1, 99))
	with um.patch.object(btp, "_duoc_sua_btp", lambda: True), um.patch.object(btp, "bang_btp", lambda: "ok"), \
			um.patch.object(frappe.db, "commit", lambda: None, create=True), BangBTP(kho.btp.dong) as b, \
			um.patch.object(frappe, "generate_hash", lambda length=8: "dot%d" % next(dem), create=True):
		luu("20", "2026-11-14", "2026-11-20")
		luu("15", "2026-11-21", "2026-11-27")
		d = kho.btp.dong[0]
		ds = sorted(rf.doc_dot(d), key=lambda x: x["tu"])
		la("hai đợt cùng nằm trên dòng", [(x["so"], x["tu"], x["den"]) for x in ds],
			[(20, D8(2026, 11, 14), D8(2026, 11, 20)), (15, D8(2026, 11, 21), D8(2026, 11, 27))])
		dung("hai mã đợt khác nhau", ds[0]["id"] != ds[1]["id"] and ds[0]["id"] and ds[1]["id"])
		nem("trùng ngày bị chặn ở cửa lưu", lambda: luu("5", "2026-11-19", "2026-11-23"), Exception)
		la("bị chặn thì không đổi gì", len(rf.doc_dot(d)), 2)
		luu("22", "2026-11-14", "2026-11-20", dot=ds[0]["id"])
		luu("0", "", "", dot=ds[1]["id"])
		la("sửa đợt 1 lên 22, bỏ đợt 2", [(x["id"], x["so"]) for x in rf.doc_dot(d)], [(ds[0]["id"], 22)])
		la("nhật ký từng lần", [(x["truong"], x["truoc"], x["sau"]) for x in b.nhat_ky], [
			("refill_dot", "", "20 bánh 14/11 tới 20/11"), ("refill_dot", "", "15 bánh 21/11 tới 27/11"),
			("refill_dot", "20 bánh 14/11 tới 20/11", "22 bánh 14/11 tới 20/11"), ("refill_dot", "15 bánh 21/11 tới 27/11", "")])
	with um.patch.object(btp, "_duoc_sua_btp", lambda: False):
		nem("không phải bếp thì không lưu", lambda: luu("5", "2026-11-28", ""), Exception)
	kho2 = t646.Kho([_roman()])
	m = t646._chay(kho2, btp.bang_btp, t646._tinh_that(), nay=D8(2026, 11, 21))
	la("Đợt đã xong có đợt 1, chưa chốt số thì để trống", [(x["ma_hang"], x["so"], x["tu"], x["den"], x["da_dat"], x["con"]) for x in m["dot_xong"]],
		[(MA, 20, "2026-11-14", "2026-11-20", None, None)])
	m = t646._chay(t646.Kho([_roman()]), btp.bang_btp, t646._tinh_that(), nay=HN)
	la("lịch refill đủ hai dòng của một bánh", [(x["ma_hang"], x["tu"]) for x in m["lich_refill"]], [(MA, "2026-11-14"), (MA, "2026-11-21")])


@ca("v660 web tab Đặt trước: bánh có hai đợt lên kèm danh sách khoảng ngày và số còn từng đợt; đợt hết suất không lên")
def _web():
	cu = t646.ROMAN
	t646.ROMAN = _roman()
	try:
		m = t646.du_lieu_web()
	finally:
		t646.ROMAN = cu
	s = {x["ma"]: x for g in m["nhom"] for x in g["sizes"]}
	r = s[MA]["refill"]
	la("hai khoảng", r["ds"], [{"tu": "2026-11-14", "den": "2026-11-20", "con": 13}, {"tu": "2026-11-21", "den": "2026-11-27", "con": 15}])
	la("khoảng đầu giữ cho trang bản cũ", (r["tu"], r["den"], r["con"], r["chi_refill"]), ("2026-11-14", "2026-11-20", 13, 1))


@ca("v660 bản vá nâng cấp: dòng còn số ở ba ô cũ thành đợt đầu trong ô mới, ba ô cũ về trống; dòng đã nâng và dòng không có refill không đổi; chạy lại không đổi thêm")
def _ban_va():
	import frappe
	from vagabond.patches import v660_refill_nhieu_dot as bv

	dong = [Doi(name="a", so_refill=20, refill_tu=D8(2026, 11, 14), refill_den=D8(2026, 11, 20), refill_dot=None),
		Doi(name="b", so_refill=0, refill_tu=None, refill_den=None, refill_dot=None),
		Doi(name="c", so_refill=0, refill_tu=None, refill_den=None, refill_dot=_hai_dot())]
	ghi = []

	def sql(q, ts=None, as_dict=False):
		if q.strip().lower().startswith("select"):
			return [d for d in dong if int(d.so_refill or 0) > 0 and not (d.refill_dot or "")]
		ghi.append(ts)
		d = [x for x in dong if x.name == ts[1]][0]
		d.refill_dot, d.so_refill, d.refill_tu, d.refill_den = ts[0], 0, None, None
		return []
	with um.patch.object(frappe.db, "sql", sql, create=True), um.patch.object(frappe.db, "has_column", lambda *a: True, create=True), \
			um.patch.object(frappe, "generate_hash", lambda length=8: "moi12345", create=True):
		bv.execute()
		bv.execute()
	la("chỉ nâng dòng a, một lần", [x[1] for x in ghi], ["a"])
	la("dòng a thành một đợt giữ đúng số và ngày", [(x["id"], x["so"], x["tu"], x["den"]) for x in rf.doc_dot(dong[0])],
		[("moi12345", 20, D8(2026, 11, 14), D8(2026, 11, 20))])
	la("ba ô cũ về trống", (dong[0].so_refill, dong[0].refill_tu), (0, None))
	la("dòng c giữ nguyên hai đợt", len(rf.doc_dot(dong[2])), 2)


@ca("v660 nhịp chốt đợt đã qua: ghi số đã nhận đúng một lần cho đợt vừa hết hạn, không đụng đợt đang chạy; Pancake lỗi thì không ghi số đoán; quá 60 ngày thì gỡ")
def _chot_dot():
	import frappe

	dong = [Doi(name="a", ma_hang=MA, ten_banh="Roman", so_refill=0, refill_tu=None, refill_den=None, refill_dot=_hai_dot())]
	don = {MA: {"2026-11-15": 7, "2026-11-22": 3}}

	def chay(nay, loi=False):
		def sql(q, ts=None, as_dict=False):
			ql = " ".join(q.split()).lower()
			if ql.startswith("select name, ma_hang, ten_banh"):
				return [d for d in dong if d.refill_dot]
			if ql.startswith("select name, ma_hang, refill_dot"):
				dung("khoá dòng trước khi ghi", "for update" in ql)
				return [d for d in dong if d.name == ts]
			if ql.startswith("update"):
				[d for d in dong if d.name == ts[1]][0].refill_dot = ts[0]
				return []
			raise AssertionError(q)

		def dem(hn, moi=False, tu=None):
			if loi:
				raise RuntimeError("Pancake 500")
			hoi.append(tu)
			return don, []
		with um.patch.object(frappe.db, "sql", sql, create=True), um.patch.object(frappe.db, "commit", lambda: None, create=True), \
				um.patch.object(rf, "dem_va_id", dem):
			return rf.chot_dot_da_qua(nay)
	hoi = []
	la("đợt chưa hết hạn: không làm gì, không gọi Pancake", (chay(D8(2026, 11, 20)), hoi), (0, []))
	nem("Pancake lỗi: ném ra, không ghi số", lambda: chay(D8(2026, 11, 21), loi=True), RuntimeError)
	la("vẫn chưa có số", [x.get("da_dat") for x in rf.doc_dot(dong[0])], [None, None])
	la("21/11: chốt đợt 1", chay(D8(2026, 11, 21)), 1)
	la("đợt 1 đã nhận 7, đợt 2 đang chạy chưa ghi", [(x["id"], x.get("da_dat")) for x in rf.doc_dot(dong[0])], [("d1", 7), ("d2", None)])
	la("đếm từ ngày đầu đợt cần chốt", hoi, [D8(2026, 11, 14)])
	la("chạy lại: không đếm lại, không đổi", (chay(D8(2026, 11, 21)), len(hoi)), (0, 1))
	q = rf.da_qua_tu_dong(dong, D8(2026, 11, 22))
	la("Đợt đã xong có số đã nhận", [(x["id"], x["so"], x["da_dat"]) for x in q], [("d1", 20, 7)])
	don[MA]["2026-11-15"] = 99
	chay(D8(2027, 1, 25))
	la("quá 60 ngày: gỡ đợt 1, giữ đợt 2 (đã chốt 3)", [(x["id"], x.get("da_dat")) for x in rf.doc_dot(dong[0])], [("d2", 3)])
