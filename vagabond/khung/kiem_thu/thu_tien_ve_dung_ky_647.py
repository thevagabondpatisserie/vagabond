# -*- coding: utf-8 -*-
"""v647 (10/11/2026): đối soát tiền về ShopeeFood báo "Lệch tiền về" sai.

Bot Zalo 08:33 báo ShopeeFood ngày 09/11 "báo chuyển 1.613.010, ngân hàng nhận
2.771.246". Thật ra không lệch: 2.771.246 là tiền của báo cáo 08/11 (nội dung
"ShopeeFood thanh toan tu dong 08 11 2026"), về ngày 09/11; tiền của 09/11 về
trưa 10/11. Hai lỗi:
  1. khop_ngan_hang lấy giao dịch "gần số nhất" trong cửa sổ ngày, kể cả tiền
     của kỳ khác, rồi báo lệch.
  2. _tien_ve chỉ chạy lúc đọc báo cáo, tiền về muộn thì nguồn kẹt "Chưa thấy".

Các ca dưới chạy THẬT doi_soat_khop.khop_ngan_hang, doi_soat_vendor._tien_ve,
doi_soat_vendor.do_lai_tien_ve và doi_soat_thu._bao_lech; chỉ thay tầng chạm
hệ (frappe.get_all, get_doc, db) bằng kho trong bộ nhớ.
"""
import datetime
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import doi_soat_khop as K
from vagabond.khung.kiem_thu.nen import ca, dung, la

ND = "SHOPEEPAY CHUYEN TIEN 10665291 ShopeeFood thanh toan tu dong %s 2026 10665291"
KY_09 = ("2026-11-09", "2026-11-09")


def _gd(name, tien, mo_ta, ngay="2026-11-09"):
	return dict(name=name, ngay=ngay, tien=tien, mo_ta=mo_ta)


# ------------------------------------------------------------ phần thuần

@ca("v647 tách ngày kỳ trong nội dung ShopeeFood; nguồn khác, ngày sai, thiếu ngày trả None")
def _():
	la("nội dung thật", K.ngay_ky_noi_dung("shopeefood", ND % "08 11"), "2026-11-08")
	la("ngày một chữ số", K.ngay_ky_noi_dung("shopeefood", "ShopeeFood thanh toan tu dong 6 11 2026"), "2026-11-06")
	la("chữ hoa, dấu chấm", K.ngay_ky_noi_dung("shopeefood", "SHOPEEFOOD THANH TOAN TU DONG 06.11.2026"), "2026-11-06")
	la("không có ngày", K.ngay_ky_noi_dung("shopeefood", "SHOPEEPAY ShopeeFood thanh toan tu dong"), None)
	la("ngày không có thật", K.ngay_ky_noi_dung("shopeefood", "ShopeeFood thanh toan tu dong 31 02 2026"), None)
	la("Grab chưa khai mẫu ngày", K.ngay_ky_noi_dung("grabfood", "Grab TT 118203316 08 11 2026"), None)
	la("rỗng", K.ngay_ky_noi_dung("shopeefood", None), None)


@ca("v647 chuỗi thật 08:33 ngày 10/11: báo cáo 09/11, cửa sổ chỉ có tiền của 08/11 thì là CHỜ, không phải lệch")
def _():
	gd = [_gd("ACC-BTN-2026-10173", 2771246, ND % "08 11")]
	# Trước sửa (không biết kỳ, lấy giao dịch gần số nhất): đúng triệu chứng site thật.
	la("cách cũ ra Lệch tiền về", K.khop_ngan_hang("shopeefood", 1613010, "2026-11-08", "2026-11-15", gd)[:2],
		("Lệch tiền về", ["ACC-BTN-2026-10173"]))
	tt, ds, ghi = K.khop_ngan_hang("shopeefood", 1613010, "2026-11-08", "2026-11-15", gd, ky=KY_09)
	la("sau sửa", (tt, ds), ("Chưa thấy tiền về", []))
	dung("ghi chú nói đang chờ đúng ngày 09/11", "09/11" in ghi and "1.613.010" in ghi)


@ca("v647 tiền đúng kỳ về sau: khớp, gắn đúng giao dịch ghi ngày 09/11")
def _():
	gd = [_gd("ACC-BTN-2026-10173", 2771246, ND % "08 11"),
		_gd("ACC-BTN-2026-10232", 1613010, ND % "09 11", ngay="2026-11-10")]
	la("đã thấy", K.khop_ngan_hang("shopeefood", 1613010, "2026-11-08", "2026-11-15", gd, ky=KY_09)[:2],
		("Đã thấy tiền về", ["ACC-BTN-2026-10232"]))


@ca("v647 lệch thật vẫn báo: giao dịch đúng kỳ mà khác số thì Lệch tiền về, gợi ý đúng giao dịch đó")
def _():
	gd = [_gd("BT-08", 2771246, ND % "08 11"), _gd("BT-09", 1600000, ND % "09 11", ngay="2026-11-10")]
	tt, ds, ghi = K.khop_ngan_hang("shopeefood", 1613010, "2026-11-08", "2026-11-15", gd, ky=KY_09)
	la("lệch đúng kỳ", (tt, ds), ("Lệch tiền về", ["BT-09"]))
	dung("ghi chú có độ lệch", "13.010" in ghi)


@ca("v647 giao dịch của kỳ khác TRÙNG số tiền vẫn không được nhận")
def _():
	gd = [_gd("BT-08", 1613010, ND % "08 11")]
	la("không nhận", K.khop_ngan_hang("shopeefood", 1613010, "2026-11-08", "2026-11-15", gd, ky=KY_09)[:2],
		("Chưa thấy tiền về", []))
	la("đúng kỳ 08/11 thì nhận", K.khop_ngan_hang("shopeefood", 1613010, "2026-11-07", "2026-11-14", gd,
		ky=("2026-11-08", "2026-11-08"))[:2], ("Đã thấy tiền về", ["BT-08"]))
	la("báo cáo nhiều ngày gồm 08/11 thì nhận", K.khop_ngan_hang("shopeefood", 1613010, "2026-11-07", "2026-11-14", gd,
		ky=("2026-11-06", "2026-11-08"))[:2], ("Đã thấy tiền về", ["BT-08"]))


@ca("v647 nguồn không ghi ngày: Lệch chỉ khi đúng MỘT ứng viên, nhiều ứng viên thì Cần chọn tiền về")
def _():
	mot = [_gd("BT-1", 668000, "Grab TT 118203316 Tran Cao Van")]
	la("một ứng viên khác số: lệch", K.khop_ngan_hang("grabfood", 668915, "2026-11-08", "2026-11-15", mot,
		ky=KY_09)[:2], ("Lệch tiền về", ["BT-1"]))
	hai = mot + [_gd("BT-2", 900000, "Grab TT 118203316 Tran Cao Van")]
	tt, ds, ghi = K.khop_ngan_hang("grabfood", 668915, "2026-11-08", "2026-11-15", hai, ky=KY_09)
	la("hai ứng viên: cần chọn, không gắn", (tt, ds), ("Cần chọn tiền về", []))
	dung("ghi chú nêu cả hai", "BT-1" in ghi and "BT-2" in ghi)
	la("không có ứng viên", K.khop_ngan_hang("grabfood", 668915, "2026-11-08", "2026-11-15", [], ky=KY_09)[0],
		"Chưa thấy tiền về")


@ca("v647 ShopeeFood có giao dịch không ghi ngày lẫn giao dịch kỳ khác: kỳ khác bị loại, còn một thì mới là lệch")
def _():
	gd = [_gd("BT-08", 2771246, ND % "08 11"), _gd("BT-X", 1600000, "SHOPEEPAY ShopeeFood thanh toan tu dong")]
	la("chỉ còn giao dịch không ghi ngày", K.khop_ngan_hang("shopeefood", 1613010, "2026-11-08", "2026-11-15", gd,
		ky=KY_09)[:2], ("Lệch tiền về", ["BT-X"]))


# ------------------------------------------------------------ phần chạm hệ, kho trong bộ nhớ

def _ngay(d, n):
	return str(datetime.date.fromisoformat(str(d)[:10]) + datetime.timedelta(days=n))


class Kho:
	"""Nguồn đối soát và giao dịch ngân hàng giả, đủ cho _tien_ve và do_lai_tien_ve."""

	def __init__(self, nguon, gd):
		self.nguon = {n["name"]: dict(n) for n in nguon}
		self.gd = list(gd)
		self.loc_ds = None
		self.tin = []
		self.loi = []

	def _doc(self, name):
		n = self.nguon[name]
		d = NS(**n)

		def db_set(k, v=None, **kw):
			cap = k if isinstance(k, dict) else {k: v}
			n.update(cap)
			for a, b in cap.items():
				setattr(d, a, b)
		d.db_set = db_set
		d.get = lambda k, mac=None: n.get(k, mac)
		return d

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		if dt == "Bank Transaction":
			tu, den = filters["date"][1]
			return [NS(name=g[0], date=g[1], deposit=g[2], description=g[3], reference_number="")
				for g in self.gd if str(tu) <= g[1] <= str(den)]
		if pluck == "giao_dich_ngan_hang":
			return [n.get("giao_dich_ngan_hang") for x, n in self.nguon.items()
				if x != filters["name"][1] and n.get("giao_dich_ngan_hang")]
		self.loc_ds = filters
		cho = filters["trang_thai_tien"][1]
		moc = filters["den_ngay"][1]
		return [NS(name=x, duong_vao=n.get("duong_vao"), get=lambda k, n=n: n.get(k)) for x, n in self.nguon.items()
			if n["trang_thai_tien"] in cho and n["den_ngay"] >= moc and n["nhom"] == filters["nhom"]
			and n["trang_thai"] == filters["trang_thai"]]

	def chay(self, ham, *a):
		from vagabond import doi_soat_thu as T
		from vagabond import doi_soat_vendor as V
		with ExitStack() as st:
			st.enter_context(patch.object(V.frappe, "get_all", self.get_all, create=True))
			st.enter_context(patch.object(V.frappe, "get_doc", lambda dt, name: self._doc(name), create=True))
			st.enter_context(patch.object(V.frappe, "get_meta", lambda dt: NS(has_field=lambda f: False), create=True))
			st.enter_context(patch.object(V.frappe, "log_error", lambda *a, **k: self.loi.append(a), create=True))
			st.enter_context(patch.object(V.frappe, "get_traceback", lambda *a: "tb", create=True))
			st.enter_context(patch.object(V.frappe.utils, "add_days", _ngay, create=True))
			st.enter_context(patch.object(V.frappe.utils, "nowdate", lambda: "2026-11-10", create=True))
			st.enter_context(patch.object(V.frappe.db, "count", lambda dt, f=None: 0, create=True))
			st.enter_context(patch.object(V.frappe.db, "get_value",
				lambda dt, name, f, **k: self.nguon[name][f], create=True))
			st.enter_context(patch.object(V, "_ghi_them", lambda name, **k: self.nguon[name].update(_ghi=k)))
			st.enter_context(patch.object(T, "bao_lech_tien", lambda name, cu: self.tin.append(
				(name, cu, self.nguon[name]["trang_thai_tien"]))))
			return ham(*a)


def _nguon(name, ngay, thuc_nhan, tt, **k):
	n = dict(name=name, mau="shopeefood", nhom="Tiền bán", trang_thai="Đã nhận", tu_ngay=ngay, den_ngay=ngay,
		ngay_tien_ve=_ngay(ngay, 1), thuc_nhan=thuc_nhan, trang_thai_tien=tt, giao_dich_ngan_hang="", company="CT",
		duong_vao="")
	n.update(k)
	return n


def _bon_nguon():
	"""Đúng bảng bốn nguồn ShopeeFood trên site thật ngày 10/11/2026."""
	return [_nguon("DSN-2611-06355", "2026-11-06", 3889408, "Lệch tiền về"),
		_nguon("DSN-2611-06504", "2026-11-07", 2904839, "Lệch tiền về"),
		_nguon("DSN-2611-06587", "2026-11-08", 2771246, "Chưa thấy tiền về"),
		_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Lệch tiền về")]


GD_THAT = [("ACC-BTN-2026-10176", "2026-11-09", 3889408, ND % "06 11"),
	("ACC-BTN-2026-10175", "2026-11-09", 2904839, ND % "07 11"),
	("ACC-BTN-2026-10173", "2026-11-09", 2771246, ND % "08 11")]
GD_10_11 = ("ACC-BTN-2026-10232", "2026-11-10", 1613010, ND % "09 11")


@ca("v647 _tien_ve thật đưa kỳ của nguồn xuống: báo cáo 09/11 với tiền của 08/11 ra Chưa thấy, không giữ giao dịch")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Lệch tiền về")], GD_THAT[2:])
	k.chay(lambda: V._tien_ve(k._doc("DSN-2611-06683")))
	n = k.nguon["DSN-2611-06683"]
	la("trạng thái", (n["trang_thai_tien"], n["giao_dich_ngan_hang"]), ("Chưa thấy tiền về", ""))
	la("không còn số lệch để gửi tin", n["_ghi"].get("lech_tien"), None)


@ca("v647 dò lại mỗi giờ: bốn nguồn ShopeeFood trên site tự đúng lại, gắn đúng ACC-BTN, không gửi tin")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho(_bon_nguon(), GD_THAT)
	kq = k.chay(V.do_lai_tien_ve)
	tt = {x: (n["trang_thai_tien"], n["giao_dich_ngan_hang"]) for x, n in k.nguon.items()}
	la("lượt 1 (08:33, tiền 09/11 chưa về)", tt, {
		"DSN-2611-06355": ("Đã thấy tiền về", "ACC-BTN-2026-10176"),
		"DSN-2611-06504": ("Đã thấy tiền về", "ACC-BTN-2026-10175"),
		"DSN-2611-06587": ("Đã thấy tiền về", "ACC-BTN-2026-10173"),
		"DSN-2611-06683": ("Chưa thấy tiền về", "")})
	la("đếm", kq, {"so_nguon": 4, "doi": 4})
	k.gd.append(GD_10_11)
	kq = k.chay(V.do_lai_tien_ve)
	la("lượt 2 (sau 12:03 ngày 10/11)", (k.nguon["DSN-2611-06683"]["trang_thai_tien"],
		k.nguon["DSN-2611-06683"]["giao_dich_ngan_hang"]), ("Đã thấy tiền về", "ACC-BTN-2026-10232"))
	la("lượt 2 chỉ dò nguồn còn chờ", kq, {"so_nguon": 1, "doi": 1})
	la("không nguồn nào thành Lệch, không có tin lệch", [t for t in k.tin if t[2] == "Lệch tiền về"], [])
	la("không lỗi", k.loi, [])


@ca("v647 dò lại: tiền đúng kỳ về mà khác số thì thành Lệch tiền về và đi qua cửa báo lệch đúng một lần")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Chưa thấy tiền về")],
		[("BT-09", "2026-11-10", 1600000, ND % "09 11")])
	k.chay(V.do_lai_tien_ve)
	la("lệch thật", k.nguon["DSN-2611-06683"]["trang_thai_tien"], "Lệch tiền về")
	la("gọi báo lệch một lần", k.tin, [("DSN-2611-06683", "Chưa thấy tiền về", "Lệch tiền về")])
	la("số cho tin là số thật", k.nguon["DSN-2611-06683"]["_ghi"]["lech_tien"], {"gd": "BT-09", "nhan": 1600000, "bao": 1613010})
	k.chay(V.do_lai_tien_ve)
	la("lượt sau không đổi thì không gọi lại", len(k.tin), 1)


@ca("v647 dò lại chỉ lấy nguồn Tiền bán đã nhận, còn chờ tiền, 14 ngày gần đây; bỏ nguồn giám đốc từ chối")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon("CU", "2026-10-20", 1613010, "Chưa thấy tiền về"),
		_nguon("TU-CHOI", "2026-11-09", 1613010, "Chưa thấy tiền về", duong_vao="Từ chối"),
		_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Chưa thấy tiền về")], [GD_10_11])
	kq = k.chay(V.do_lai_tien_ve)
	la("bộ lọc", (k.loc_ds["nhom"], k.loc_ds["trang_thai"], sorted(k.loc_ds["trang_thai_tien"][1]), k.loc_ds["den_ngay"]),
		("Tiền bán", "Đã nhận", sorted(K.CHO_TIEN_VE), [">=", "2026-10-27"]))
	la("nguồn cũ hơn 14 ngày không đụng", k.nguon["CU"]["trang_thai_tien"], "Chưa thấy tiền về")
	la("nguồn từ chối không đụng", k.nguon["TU-CHOI"]["trang_thai_tien"], "Chưa thấy tiền về")
	la("nguồn trong hạn khớp", k.nguon["DSN-2611-06683"]["giao_dich_ngan_hang"], "ACC-BTN-2026-10232")
	la("đếm", kq, {"so_nguon": 2, "doi": 1})


@ca("v647 dò lại giữ luật cũ: giao dịch nguồn khác đã giữ không dùng lại, có lý do kế toán tự chọn thì không tự nhận")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon("GIU", "2026-11-09", 1613010, "Đã thấy tiền về", giao_dich_ngan_hang="ACC-BTN-2026-10232"),
		_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Chưa thấy tiền về")], [GD_10_11])
	k.chay(V.do_lai_tien_ve)
	la("đã dùng thì không nhận", k.nguon["DSN-2611-06683"]["trang_thai_tien"], "Chưa thấy tiền về")
	k = Kho([_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Chưa thấy tiền về")], [GD_10_11])
	with patch.object(K, "ly_do_khong_tu_nhan", lambda *a: "có dòng đã được thay bằng bản sửa của vendor"):
		k.chay(V.do_lai_tien_ve)
	la("lý do tay: cần chọn, không giữ", (k.nguon["DSN-2611-06683"]["trang_thai_tien"],
		k.nguon["DSN-2611-06683"]["giao_dich_ngan_hang"]), ("Cần chọn tiền về", ""))


@ca("v647 dò lại: một nguồn lỗi không chặn nguồn sau, lỗi vào Error Log")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon("A-LOI", "2026-11-08", 1, "Chưa thấy tiền về"),
		_nguon("DSN-2611-06683", "2026-11-09", 1613010, "Chưa thấy tiền về")], [GD_10_11])
	that = V._tien_ve

	def hong(n):
		if n.name == "A-LOI":
			raise RuntimeError("x")
		return that(n)
	with patch.object(V, "_tien_ve", hong):
		k.chay(V.do_lai_tien_ve)
	la("nguồn sau vẫn khớp", k.nguon["DSN-2611-06683"]["trang_thai_tien"], "Đã thấy tiền về")
	la("ghi một lỗi", len(k.loi), 1)


@ca("v647 lượt mỗi giờ quet_moi_gio có chạy dò lại tiền về")
def _():
	from vagabond import doi_soat_vendor as V
	viec = []
	with patch.object(V, "quet_email", lambda n: viec.append("thu")), \
			patch.object(V, "do_lai_tien_ve", lambda: viec.append("tien")), \
			patch.object(V.frappe, "set_user", lambda u: None, create=True):
		V.quet_moi_gio()
	la("thứ tự", viec, ["thu", "tien"])


# ------------------------------------------------------------ tin Zalo

def _chay_bao(n, d, cu):
	import sys
	import vagabond
	from vagabond import doi_soat_thu as T
	gui = []
	gia = NS(bao_hoac_ghi_loi=lambda *a, **k: gui.append(k.get("khoa")))
	with patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), patch.object(vagabond, "kenh_zalo", gia, create=True), \
			patch.object(T, "_link", lambda: "/app/doi-soat"):
		T._bao_lech(n, d, cu, {"nguong_lech": 1000})
	return gui


@ca("v647 tin Lệch tiền về: chỉ khi chuyển sang lệch thật, khoá theo nguồn, không tin đính chính khi đã khớp")
def _():
	from vagabond import doi_soat_thu as T
	from vagabond.khung.kiem_thu.nen import Doi
	n = Doi(name="DSN-1", vendor="ShopeeFood", mau="shopeefood", tu_ngay="2026-11-09", den_ngay="2026-11-09",
		trang_thai_tien="Lệch tiền về")
	d = {"lech_tien": {"gd": "BT-09", "nhan": 1600000, "bao": 1613010}}
	la("chuyển sang lệch: một tin, khoá theo nguồn", _chay_bao(n, d, "Chưa thấy tiền về"), [T.khoa_lech("DSN-1")])
	la("khoá không mang số tiền", T.khoa_lech("DSN-1"), "ds_lech:DSN-1")
	la("đã lệch từ trước: không gửi lại", _chay_bao(n, d, "Lệch tiền về"), [])
	n.trang_thai_tien = "Đã thấy tiền về"
	la("đổi sang đã thấy: không gửi tin đính chính", _chay_bao(n, d, "Lệch tiền về"), [])
	n.trang_thai_tien = "Chưa thấy tiền về"
	la("chưa thấy: không gửi", _chay_bao(n, {}, "Lệch tiền về"), [])


@ca("v647 bao_lech_tien (lượt dò lại gọi) đọc nguồn rồi đi đúng _bao_lech: lệch thật gửi một tin, đã thấy thì im")
def _():
	import json
	import sys
	import vagabond
	from vagabond import doi_soat_thu as T
	from vagabond.khung.kiem_thu.nen import Doi
	gui, loi = [], []
	n = Doi(name="DSN-1", vendor="ShopeeFood", mau="shopeefood", nhom="Tiền bán", tu_ngay="2026-11-09",
		den_ngay="2026-11-09", thuc_nhan=1613010, trang_thai_tien="Lệch tiền về", company="CT",
		du_lieu=json.dumps({"lech_tien": {"gd": "BT-09", "nhan": 1600000, "bao": 1613010}}))
	gia_f = NS(db=NS(get_value=lambda dt, name, f, as_dict=False: n), log_error=lambda *a, **k: loi.append(k))
	gia = NS(bao_hoac_ghi_loi=lambda *a, **k: gui.append(k.get("khoa")))
	with patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), patch.object(vagabond, "kenh_zalo", gia, create=True), \
			patch.object(T, "_frappe", lambda: gia_f), patch.object(T, "_link", lambda: "/app/doi-soat"), \
			patch.object(T, "cau_hinh", lambda: {"nguong_lech": 1000}):
		T.bao_lech_tien("DSN-1", "Chưa thấy tiền về")
		n["trang_thai_tien"] = "Đã thấy tiền về"
		T.bao_lech_tien("DSN-1", "Lệch tiền về")
	la("một tin", gui, ["ds_lech:DSN-1"])
	la("không lỗi", loi, [])


# ------------------------------------------------------------ v647 mở rộng: Payoo, OnePay, GrabFood
# Anh Việt 10/11/2026: áp cùng nguyên lý "chỉ so với tiền đúng kỳ" cho mọi nguồn.
# Nội dung chuyển khoản lấy nguyên văn từ sao kê MB thật (chú thích MAU_TIEN_VE) và
# đặc tả nguồn docs/doi-soat-vendor/schema/dac-ta-10-nguon.md.

PAYOO = "Payoo TT TD ngay %s.VAGABOND TONG"
ONEPAY = "PVS%s OnePay tam ung VAGABOND QT 17h %s den 17h %s"
VIETQR = "PVS%s OnePay tam ung VAGABOND VIETQR 0h %s den 23h59 %s"


@ca("v647 dấu kỳ trong nội dung: Payoo nhiều ngày, một ngày, qua năm; OnePay QT, VietQR, bị cắt; mã PVS; cửa hàng Grab")
def _():
	la("Payoo cuối tuần", K.khoang_ky_noi_dung("payoo_the", PAYOO % "02.10 04.10.2026"), ("2026-10-02", "2026-10-04"))
	la("Payoo một ngày", K.khoang_ky_noi_dung("payoo_qr", "PAYOO TT TD NGAY 05.10.2026.VAGABOND TONG"),
		("2026-10-05", "2026-10-05"))
	la("Payoo qua năm", K.khoang_ky_noi_dung("payoo_the", PAYOO % "30.12 02.01.2027"), ("2026-12-30", "2027-01-02"))
	la("Payoo ngày sai", K.khoang_ky_noi_dung("payoo_the", PAYOO % "31.02.2026"), None)
	la("OnePay QT", K.khoang_ky_noi_dung("onepay_ngay", ONEPAY % ("1365757", "28 07 26", "29 07 26")),
		("2026-07-28", "2026-07-29"))
	la("OnePay VietQR cuối tuần", K.khoang_ky_noi_dung("onepay_ngay", VIETQR % ("1", "10 07 26", "12 07 26")),
		("2026-07-10", "2026-07-12"))
	la("OnePay bị cắt sau 'den'", K.khoang_ky_noi_dung("onepay_ngay", "PVS1365757 OnePay tam ung VAGABOND QT 17h 28 07 26 den 17"),
		("2026-07-28", "2026-08-01"))
	la("mã PVS", K.ma_chuyen_noi_dung("pvs1365757 onepay tam ung"), "PVS1365757")
	la("không mã", K.ma_chuyen_noi_dung("OnePay tam ung"), "")
	la("Grab TCV", K.cua_hang_noi_dung("Grab TT 118203316 Tran Cao Van"), "5-C4E1NPWGG2WZFA")
	la("Grab NVT", K.cua_hang_noi_dung("GRAB TT 118203317 THE VAGABOND DELIVERY KITCHEN"), "5-C4E1NPWGMGBGNX")
	la("Grab không tên", K.cua_hang_noi_dung("Grab TT 118203316"), "")
	la("Xanh SM chưa có dấu", K.khoang_ky_noi_dung("greensm_ngon", "XANH SM 08 11 2026"), None)


@ca("v647 Payoo: báo cáo 05/10 không nhận tiền kỳ 02-04/10 dù trùng số; tiền đúng kỳ thì khớp; đúng kỳ khác số thì Lệch")
def _():
	ky = ("2026-10-05", "2026-10-05")
	cu = [_gd("BT-0204", 1847750, PAYOO % "02.10 04.10.2026", ngay="2026-10-05")]
	la("kỳ khác trùng số: chờ", K.khop_ngan_hang("payoo_the", 1847750, "2026-10-04", "2026-10-11", cu, ky=ky)[:2],
		("Chưa thấy tiền về", []))
	moi = cu + [_gd("BT-05", 786800, PAYOO % "05.10.2026", ngay="2026-10-06")]
	la("đúng kỳ", K.khop_ngan_hang("payoo_the", 786800, "2026-10-04", "2026-10-11", moi, ky=ky)[:2],
		("Đã thấy tiền về", ["BT-05"]))
	la("đúng kỳ khác số", K.khop_ngan_hang("payoo_the", 790000, "2026-10-04", "2026-10-11", moi, ky=ky)[:2],
		("Lệch tiền về", ["BT-05"]))
	la("báo cáo cuối tuần nhận tiền cuối tuần", K.khop_ngan_hang("payoo_qr", 1847750, "2026-10-04", "2026-10-11", moi,
		ky=("2026-10-02", "2026-10-04"))[:2], ("Đã thấy tiền về", ["BT-0204"]))


@ca("v647 OnePay: mã PVS của thông báo quyết định; PVS khác không bao giờ là ứng viên; không có mã thì theo khung kỳ lồng nhau")
def _():
	ky = ("2026-07-29", "2026-07-29")
	gd = [_gd("BT-A", 288800, ONEPAY % ("1365757", "28 07 26", "29 07 26"), ngay="2026-07-30"),
		_gd("BT-B", 288800, ONEPAY % ("1365799", "29 07 26", "30 07 26"), ngay="2026-07-31")]
	la("hai đợt trùng số, có mã: chọn đúng đợt", K.khop_ngan_hang("onepay_ngay", 288800, "2026-07-29", "2026-08-05", gd,
		ky=ky, ma_chuyen="PVS1365799")[:2], ("Đã thấy tiền về", ["BT-B"]))
	la("mã khác hẳn: chờ, không lệch", K.khop_ngan_hang("onepay_ngay", 300000, "2026-07-29", "2026-08-05", gd,
		ky=ky, ma_chuyen="PVS1400000")[:2], ("Chưa thấy tiền về", []))
	la("không mã, báo cáo một ngày nằm ở ranh hai kỳ: không tự chọn", K.khop_ngan_hang("onepay_ngay", 288800,
		"2026-07-29", "2026-08-05", gd, ky=ky)[0], "Cần chọn tiền về")
	la("không mã, báo cáo 28-29/07: chỉ kỳ 28-29", K.khop_ngan_hang("onepay_ngay", 288800, "2026-07-27", "2026-08-05",
		gd, ky=("2026-07-28", "2026-07-29"))[:2], ("Đã thấy tiền về", ["BT-A"]))
	vq = [_gd("BT-Q", 729818, VIETQR % ("5257571", "10 07 26", "12 07 26"), ngay="2026-07-13")]
	la("VietQR thứ hai không nhận tiền cuối tuần trước", K.khop_ngan_hang("onepay_ngay", 729818, "2026-07-12",
		"2026-07-19", vq, ky=("2026-07-13", "2026-07-13"))[:2], ("Chưa thấy tiền về", []))


@ca("v647 GrabFood: tiền ghi tên cửa hàng khác không là ứng viên; đúng cửa hàng hoặc không ghi tên thì theo luật một ứng viên")
def _():
	tk = "GRABFOOD:5-C4E1NPWGMGBGNX"
	gd = [_gd("BT-TCV", 668915, "Grab TT 118203316 Tran Cao Van")]
	la("tiền của TCV trùng số không vào NVT", K.khop_ngan_hang("grabfood", 668915, "2026-11-08", "2026-11-15", gd,
		tai_khoan=tk)[:2], ("Chưa thấy tiền về", []))
	la("không báo lệch bằng tiền cửa hàng khác", K.khop_ngan_hang("grabfood", 600000, "2026-11-08", "2026-11-15", gd,
		tai_khoan=tk)[:2], ("Chưa thấy tiền về", []))
	gd.append(_gd("BT-NVT", 650000, "GRAB TT 118203317 THE VAGABOND DELIVERY KITCHEN"))
	la("đúng cửa hàng khác số: Lệch", K.khop_ngan_hang("grabfood", 600000, "2026-11-08", "2026-11-15", gd,
		tai_khoan=tk)[:2], ("Lệch tiền về", ["BT-NVT"]))
	la("TCV vẫn nhận tiền TCV", K.khop_ngan_hang("grabfood", 668915, "2026-11-08", "2026-11-15", gd,
		tai_khoan="GRABFOOD:5-C4E1NPWGG2WZFA")[:2], ("Đã thấy tiền về", ["BT-TCV"]))
	la("nội dung không tên cửa hàng: như cũ", K.khop_ngan_hang("grabfood", 500000, "2026-11-08", "2026-11-15",
		[_gd("BT-X", 500000, "Grab TT 118203318")], tai_khoan=tk)[:2], ("Đã thấy tiền về", ["BT-X"]))


@ca("v647 _tien_ve thật: OnePay lấy mã PVS từ dữ liệu nguồn, Grab lấy cửa hàng từ tài khoản nguồn")
def _():
	import json
	from vagabond import doi_soat_vendor as V
	op = _nguon("DSN-OP", "2026-07-29", 288800, "Lệch tiền về", mau="onepay_ngay", ngay_tien_ve="2026-07-30",
		du_lieu=json.dumps({"them": {"ma_chuyen": "PVS1365799", "but_toan": "5321728"}}))
	gd = [("BT-A", "2026-07-30", 288800, ONEPAY % ("1365757", "28 07 26", "29 07 26")),
		("BT-B", "2026-07-31", 288800, ONEPAY % ("1365799", "29 07 26", "30 07 26"))]
	k = Kho([op], gd)
	k.chay(lambda: V._tien_ve(k._doc("DSN-OP")))
	la("OnePay đúng đợt", (k.nguon["DSN-OP"]["trang_thai_tien"], k.nguon["DSN-OP"]["giao_dich_ngan_hang"]),
		("Đã thấy tiền về", "BT-B"))
	gr = _nguon("DSN-GR", "2026-11-08", 600000, "Lệch tiền về", mau="grabfood", tai_khoan="GRABFOOD:5-C4E1NPWGMGBGNX")
	k = Kho([gr], [("BT-TCV", "2026-11-09", 668915, "Grab TT 118203316 Tran Cao Van")])
	k.chay(lambda: V._tien_ve(k._doc("DSN-GR")))
	la("Grab NVT không lệch theo tiền TCV", k.nguon["DSN-GR"]["trang_thai_tien"], "Chưa thấy tiền về")
	la("du_lieu hỏng thì coi như không mã", V._ma_chuyen(NS(du_lieu="{hong")), "")
