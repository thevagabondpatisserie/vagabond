# -*- coding: utf-8 -*-
"""v648: bill sàn (GrabFood, ShopeeFood, Xanh SM) bị báo "Lệch tiền" sai.

Đo trên site 11/11/2026, dòng đối soát từ 01/10: 860 dòng sàn "Lệch tiền" thì
chỉ 4 dòng lệch thật. Bill sàn ghi theo ba cách, phép so cũ chỉ biết cách đầu:
  - giá menu không giảm (cũ);
  - ghi khuyến mại lên bill: Grab HDB-26-11-01815 tổng 385.000, sau giảm 339.500,
    báo cáo 339.500 + giảm 45.500;
  - ghi thực nhận: Xanh SM HDB-26-11-01810 tổng 650.000, sau giảm 502.860 = thực
    nhận; ShopeeFood HDB-26-11-01792 sau giảm 139.161 = thực nhận.
Một hàm so tiền (khop.cung_tien) cho mọi chỗ; số liệu dưới là số thật.
"""
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import doi_soat_khop as K
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _d(ma, tien_hang, giam, thuc_nhan, ngay="2026-11-09"):
	return dict(loai="ban", ngay=ngay, ma_tham_chieu=ma, tien_hang=tien_hang, giam_gia=giam, thuc_nhan=thuc_nhan)


def _u(name, ma, tien, goc, ngay="2026-11-09"):
	return dict(name=name, ngay=ngay, tien=tien, tien_goc=goc, ma=[ma], tien_to="")


GRAB = (_d("GF-727", 339500, 45500, 289524), _u("HDB-26-11-01815", "GF-727", 339500, 385000))
XSM = (_d("8253", 578000, 72000, 502860), _u("HDB-26-11-01810", "XSM-8253", 502860, 650000))
SPF = (_d("09116-667172500", 163200, 76800, 139161), _u("HDB-26-11-01792", "2500", 139161, 250000))


@ca("v648 cung_tien: ba cách bill sàn ghi tiền đều là cùng tiền (số thật trên site); lệch thật vẫn lệch")
def _():
	la("Grab ghi khuyến mại (trước giảm = gộp)", K.cung_tien("grab", *GRAB), True)
	la("Xanh SM ghi thực nhận", K.cung_tien("greensm", *XSM), True)
	la("ShopeeFood ghi thực nhận (tổng trước giảm chênh 10.000)", K.cung_tien("shopee", *SPF), True)
	la("Grab: chỉ tổng trước giảm khớp (54 dòng như vậy trên site)", K.cung_tien("grab", GRAB[0], dict(GRAB[1], tien=330000)), True)
	la("Grab: tổng trước giảm khác, sau giảm = tiền hàng", K.cung_tien("grab", GRAB[0], dict(GRAB[1], tien_goc=400000)), True)
	la("bill menu không giảm (cách cũ)", K.cung_tien("grab", _d("GF-1", 63000, 52000, 90000), _u("SI-1", "GF-1", 115000, 115000)), True)
	la("lệch thật", K.cung_tien("grab", _d("GF-2", 100000, 0, 80000), _u("SI-2", "GF-2", 90000, 90000)), False)
	la("cổng thẻ chỉ so số quẹt, không so thực nhận", K.cung_tien("payoo", _d("6118", 100000, 0, 98000), _u("SI-3", "6118", 98000, 98000)), False)
	la("bill 0 đồng không khớp thực nhận 0", K.cung_tien("grab", _d("GF-3", 50000, 0, 0), _u("SI-4", "GF-3", 0, 0)), False)
	la("thiếu tổng trước giảm (dòng thanh toán tách) vẫn so được", K.cung_tien("grab", GRAB[0], dict(GRAB[1], tien_goc=None)), True)


@ca("v648 chiều xuôi: dòng Grab GF-727 nối HDB-26-11-01815 là Đã nối (trước v648: Lệch tiền); lượt nối theo tiền dùng cùng hàm")
def _():
	kq = K.khop_hoa_don("grab", [GRAB[0]], [GRAB[1]])
	la("theo mã", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Đã nối", "HDB-26-11-01815"))
	d = dict(SPF[0], ma_tham_chieu="")
	kq = K.khop_hoa_don("shopee", [d], [dict(SPF[1], ma=[""])])
	la("theo tiền (không mã)", kq[0]["trang_thai"], "Nối theo tiền")
	la("xác nhận còn đúng", K.xac_nhan_con_dung("greensm", dict(XSM[0], sales_invoice="HDB-26-11-01810"), [XSM[1]]), True)


@ca("v648 màn Bill chưa khớp đối tác: dòng còn ghi Lệch tiền theo phép so cũ mà cùng tiền thì là Khớp, kèm lời nhắc Đối chiếu lại; lệch thật ghi cả số trước giảm")
def _():
	phu = {("grab", "2026-11-09", "*")}
	b1 = dict(name="HDB-26-11-01815", kieu="grab", ngay="2026-11-09", tien=339500, tien_goc=385000, ma=["GF-727"], diem="TCV")
	b2 = dict(name="SI-X", kieu="grab", ngay="2026-11-09", tien=90000, tien_goc=120000, ma=["GF-9"], diem="TCV")
	noi = {("HDB-26-11-01815", "grab"): dict(trang_thai_khop="Lệch tiền", tien=385000, ma="GF-727", vendor="GrabFood",
			tien_hang=339500, giam_gia=45500, thuc_nhan=289524),
		("SI-X", "grab"): dict(trang_thai_khop="Lệch tiền", tien=150000, ma="GF-9", vendor="GrabFood",
			tien_hang=150000, giam_gia=0, thuc_nhan=120000)}
	kq = {x["name"]: x for x in K.doi_chieu_bill([b1, b2], noi, phu, (), "2026-11-15")}
	la("bill khớp theo cách so mới", kq["HDB-26-11-01815"]["trang_thai"], "Khớp")
	dung("nhắc bấm Đối chiếu lại", "Đối chiếu lại" in kq["HDB-26-11-01815"]["ghi_chu"])
	la("lệch thật", kq["SI-X"]["trang_thai"], "Lệch tiền")
	dung("ghi cả số trước giảm", "trước giảm 120.000" in kq["SI-X"]["ghi_chu"] and "150.000" in kq["SI-X"]["ghi_chu"])


@ca("v648 _ung_vien_hd đưa tổng trước giảm của bill (s.total) cho mọi ứng viên hoá đơn")
def _():
	from vagabond import doi_soat_vendor as V
	hoi = []

	def sql(q, tham=None, as_dict=False):
		hoi.append(q)
		return [NS(name="HDB-26-11-01815", ngay="2026-11-09", grand_total=339500, rounded_total=339500, total=385000,
			vgb_ma_tham_chieu="GF-727", vgb_quay="TCV", get=lambda k, m=None: {"vgb_ma_tham_chieu": "GF-727", "vgb_quay": "TCV"}.get(k, m))]
	with patch.object(V.frappe, "get_meta", lambda dt: NS(has_field=lambda f: True), create=True), \
			patch.object(V.frappe.db, "sql", sql, create=True), \
			patch.object(V.frappe.db, "table_exists", lambda t: False, create=True), \
			patch.object(V, "_ma_dong_tt", lambda name: []):
		uv = V._ung_vien_hd("grab", "2026-11-09", "2026-11-09", "CT")
	dung("câu hỏi có s.total", all("s.total" in q for q in hoi))
	la("ứng viên mang tien_goc", [(u["name"], u["tien"], u.get("tien_goc")) for u in uv][:1], [("HDB-26-11-01815", 339500, 385000)])


# ------------------------------------------------------------ Codex PR #551 (231aeef5bd)

class KhoSan:
	"""Kho trong bộ nhớ cho đúng chuỗi Codex #551: chiều xuôi THẬT (khop_hoa_don)
	nối dòng ShopeeFood, rồi chiều ngược THẬT (du_lieu_bill). Truy vấn giả CHỈ trả
	các trường được hỏi (fields), như frappe.get_all: câu truy vấn quên trường nào
	thì dòng thiếu trường đó, không được kho giả che đi."""

	def __init__(self, dong_bao_cao, bill):
		self.bill = bill
		uv = [dict(name=n, ngay="2026-11-09", tien=t, tien_goc=g, ma=[m], tien_to="") for n, t, g, m in bill]
		kq = K.khop_hoa_don("shopee", dong_bao_cao, uv)
		self.dong = [dict(d, nguon="DSN-SPF-0911", sales_invoice=kq[i]["hoa_don"] or None, trang_thai_khop=kq[i]["trang_thai"],
			vendor="ShopeeFood", diem_ban="") for i, d in enumerate(dong_bao_cao)]

	def get_all(self, dt, filters=None, fields=None, **k):
		f = filters or {}
		if dt == "Vagabond Doi Soat Dong":
			if "sales_invoice" in f:
				ra = [d for d in self.dong if d["sales_invoice"] in f["sales_invoice"][1] and d["trang_thai_khop"] in f["trang_thai_khop"][1]]
			elif f.get("trang_thai_khop") == ["in", ["Nhiều chứng từ"]]:
				ra = [d for d in self.dong if d["trang_thai_khop"] == "Nhiều chứng từ" and d["nguon"] in f["nguon"][1]]
			else:
				ra = []
		elif dt == "Vagabond Doi Soat Nguon":
			ra = [dict(name="DSN-SPF-0911", mau="shopeefood", tu_ngay="2026-11-09", den_ngay="2026-11-09",
				tai_khoan="SPF", duong_vao="Từ thư", company="CT")] if "shopeefood" in f["mau"][1] else []
		elif dt == "Vagabond Doi Soat Trung":
			ra = []
		else:
			raise AssertionError(dt)
		return [NS(**{t: d[t] for t in fields if t in d}) for d in ra]

	def chay(self, ham):
		import datetime

		from vagabond import diem_ban
		from vagabond import doi_soat_vendor as V
		cong = lambda d, n: str(datetime.date.fromisoformat(str(d)[:10]) + datetime.timedelta(days=n))
		uv = lambda kieu, tu, den, ct: [dict(name=n, ngay="2026-11-09", tien=t, tien_goc=g, ma=[m], quay="Q1")
			for n, t, g, m in self.bill] if kieu == "shopee" else []
		with patch.object(V, "_ung_vien_hd", uv), \
				patch.object(V, "_kieu_nguon", lambda ten: "shopee"), \
				patch.object(V, "diem_doi_tac", lambda: {}), \
				patch.object(V.frappe, "get_all", self.get_all, create=True), \
				patch.object(V.frappe.utils, "add_days", cong, create=True), \
				patch.object(diem_ban, "ma_theo_quay", lambda q: "TCV"):
			return ham()


@ca("Codex #551: hai bill ShopeeFood chỉ khớp dòng báo cáo theo THỰC NHẬN: chiều xuôi Nhiều chứng từ, chiều ngược hai bill Chờ kế toán chọn (trước sửa: Không có trên báo cáo)")
def _():
	from vagabond import doi_soat_vendor as V
	# Đúng số Codex dùng: bill 139.161 (tổng 250.000), báo cáo 163.200 + 76.800, thực nhận 139.161.
	dong = [dict(SPF[0], ma_tham_chieu="", ngay="2026-11-09")]
	k = KhoSan(dong, [("HDB-S1", 139161, 250000, ""), ("HDB-S2", 139161, 250000, ""), ("HDB-S3", 99000, 99000, "")])
	la("chiều xuôi thật: dòng có nhiều chứng từ", [d["trang_thai_khop"] for d in k.dong], ["Nhiều chứng từ"])
	kq = {x["name"]: x["trang_thai"] for x in k.chay(lambda: V.du_lieu_bill("2026-11-09", "2026-11-09", ["CT"], "2026-11-15"))}
	la("hai bill chờ chọn, bill khác tiền không có", kq, {"HDB-S1": "Chờ kế toán chọn", "HDB-S2": "Chờ kế toán chọn",
		"HDB-S3": "Không có trên báo cáo"})


@ca("Codex #551: một nguồn cho ba con số tiền của dòng đối tác; thiếu trường là lỗi, không âm thầm thành 0")
def _():
	import re

	from vagabond import doi_soat_vendor as V
	la("đủ ba trường", V._tien_dong(dict(tien_hang=163200, giam_gia=76800, thuc_nhan=139161)),
		dict(tien_hang=163200, giam_gia=76800, thuc_nhan=139161))
	la("bản ghi dạng thuộc tính", V._tien_dong(NS(tien_hang=None, giam_gia=0, thuc_nhan=5)), dict(tien_hang=0, giam_gia=0, thuc_nhan=5))
	try:
		V._tien_dong(NS(tien_hang=1, giam_gia=0))
		loi = None
	except AttributeError as e:
		loi = e
	dung("thiếu thực nhận thì báo lỗi", loi is not None)
	import inspect
	src = inspect.getsource(V)
	# Chốt một nguồn: không chỗ nào còn tự đọc tiền hàng của một dòng đối tác (r., d.) ngoài _tien_dong.
	la("không còn chỗ nào tự dựng tiền của dòng đối tác", re.findall(r"tien_hang=int\((?:r|d)\.", src), [])


@ca("v648 tin Zalo 08:30 bill không khớp: bill sàn còn ghi Lệch tiền theo cách so cũ KHÔNG còn bị nhắc; lệch thật ghi cả số báo cáo đối tác")
def _():
	import sys

	import vagabond
	from vagabond import diem_ban
	from vagabond import doi_soat_thu as T
	from vagabond import doi_soat_vendor as V
	# Đúng chuỗi của tin 08:30: kết luận THẬT của màn Bill chưa khớp (doi_chieu_bill) rồi bao_bill_lech.
	b1 = dict(name="HDB-26-11-01815", kieu="grab", ngay="2026-11-09", tien=339500, tien_goc=385000, ma=["GF-727"], diem="TCV")
	b2 = dict(name="SI-X", kieu="grab", ngay="2026-11-09", tien=90000, tien_goc=120000, ma=["GF-9"], diem="TCV")
	noi = {("HDB-26-11-01815", "grab"): dict(trang_thai_khop="Lệch tiền", tien=385000, ma="GF-727", vendor="GrabFood",
			tien_hang=339500, giam_gia=45500, thuc_nhan=289524),
		("SI-X", "grab"): dict(trang_thai_khop="Lệch tiền", tien=150000, ma="GF-9", vendor="GrabFood",
			tien_hang=150000, giam_gia=0, thuc_nhan=120000)}
	ds = K.doi_chieu_bill([b1, b2], noi, {("grab", "2026-11-09", "*")}, (), "2026-11-15")
	gui = []
	gia = NS(bao_hoac_ghi_loi=lambda loai, cd, t, d, **k: gui.append((k["khoa"], t, d)))
	gia_f = NS(utils=NS(add_days=lambda d, n: "2026-11-%02d" % (int(d[8:]) + n)), get_all=lambda *a, **k: ["CT"],
		defaults=NS(get_global_default=lambda k: "CT"))
	with patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), patch.object(vagabond, "kenh_zalo", gia, create=True), \
			patch.object(T, "_frappe", lambda: gia_f), patch.object(T, "_link", lambda: "/bep/doi-soat"), \
			patch.object(V, "_cong_ty_demo", lambda: ""), patch.object(V, "du_lieu_bill", lambda tu, den, ct, hom: ds), \
			patch.object(diem_ban, "ten_diem", lambda: {"TCV": "Trần Cao Vân"}):
		T.bao_bill_lech("2026-11-15")
	la("một tin cho GrabFood ngày 09/11", [g[0] for g in gui], ["ds_bill:grab:2026-11-09"])
	t, d = gui[0][1], gui[0][2]
	la("tiêu đề chỉ đếm bill lệch thật", t, "1 bill GrabFood ngày 09/11 không khớp báo cáo đối tác")
	dung("bill cùng tiền theo cách so mới không bị nhắc", not any("HDB-26-11-01815" in x for x in d))
	dung("dòng lệch thật ghi số bill và số báo cáo", any("SI-X" in x and "lệch tiền" in x and "báo cáo ghi 150.000" in x for x in d))
