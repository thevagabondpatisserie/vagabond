# -*- coding: utf-8 -*-
"""v655 (anh Việt 13/11/2026): Đối soát nhà cung cấp.

1. OnePay nối theo SỐ ĐƠN Pancake trong mã giao dịch S<shop>O<đơn>T<giờ>,
   khoảng ngày nới 45 ngày; nối theo tiền chỉ còn cho dòng không tách được số
   đơn, và không bao giờ đưa hoá đơn của đơn KHÁC (ca thật: đơn 97533 và 97553
   cùng 905.237 đ, máy gợi ý nhầm HDB-26-11-02409 của 97553 cho 97533).
2. Lượt mỗi giờ đối chiếu lại các nguồn Tiền bán còn dòng chưa nối trong 30
   ngày, cùng khoá đối soát, đọc lại nguồn SAU khoá; bản vá một lần từ 01/10.
3. Chữ "Đã khép" đổi thành "Đã hoàn tất", app cũ gửi khoá cũ vẫn lọc đúng.
"""
from contextlib import ExitStack, nullcontext
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import doi_soat_khop as K
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _d(ma, tien, ngay="2026-11-12"):
	return dict(loai="ban", ngay=ngay, ma_tham_chieu=ma, tien_hang=tien, giam_gia=0, thuc_nhan=tien)


def _uv(name, so_don, tien, ngay="2026-11-12", ma_khac=""):
	return dict(name=name, ngay=ngay, tien=tien, ma=[ma_khac] + ([so_don] if so_don else []), so_don=so_don, tien_to="")


@ca("v655 THUẦN so_don_onepay: tách số đơn Pancake giữa chữ O và T; chữ thường, khoảng trắng; mã khác dạng thì rỗng")
def _():
	la("mã thật", K.so_don_onepay("S67355O97528T113544"), "97528")
	la("chữ thường, khoảng trắng", K.so_don_onepay(" s67355 o97533 t090102 "), "97533")
	la("không theo dạng", [K.so_don_onepay(x) for x in ("PL_1", "", None, "S67355O97528", "SO12T1", "S1O000T1", "PVS1447922")],
		["", "", "", "", "", "", ""])


@ca("v655 THUẦN so_don_pancake: một nguồn cho số đơn của hoá đơn; ưu tiên ô số đơn, không có thì đọc ghi chú Pancake #")
def _():
	la("ô số đơn", K.so_don_pancake("97528", "Pancake #11111 - X"), "97528")
	la("ghi chú", K.so_don_pancake("", "Pancake #97528 - Mr.Phong - 0903788998"), "97528")
	la("ghi chú viết thường, có cách", K.so_don_pancake(None, "pancake # 97553 - A"), "97553")
	la("không có", [K.so_don_pancake("", "Mang về #TEST-1 - Khách"), K.so_don_pancake(None, None)], ["", ""])


@ca("v655 ca thật 13/11: đơn 97533 và 97553 cùng 905.237 đ: mỗi dòng nối ĐÚNG hoá đơn của đơn mình, không nối theo tiền chéo")
def _():
	dong = [_d("S67355O97533T101010", 905237), _d("S67355O97553T111111", 905237)]
	uv = [_uv("HDB-26-11-02409", "97553", 905237)]
	kq = K.khop_hoa_don("onepay", dong, uv)
	la("97533 chưa có hoá đơn: không lấy hoá đơn của 97553", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Không thấy chứng từ", ""))
	dung("ghi chú nói đơn nào", "#97533" in kq[0]["ghi_chu"])
	la("97553 nối đúng theo số đơn", (kq[1]["trang_thai"], kq[1]["hoa_don"]), ("Đã nối", "HDB-26-11-02409"))


@ca("v655 OnePay số đơn khớp mà khác tiền là Lệch tiền; khớp số đơn trong 45 ngày (đơn trả trước nhận sau); quá 45 ngày thì không")
def _():
	kq = K.khop_hoa_don("onepay", [_d("S67355O97492T080000", 500000)], [_uv("SI-1", "97492", 450000, ngay="2026-11-14")])
	la("lệch tiền", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Lệch tiền", "SI-1"))
	kq = K.khop_hoa_don("onepay", [_d("S67355O97492T080000", 500000, ngay="2026-10-01")], [_uv("SI-1", "97492", 500000, ngay="2026-11-14")])
	la("44 ngày sau vẫn nối", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Đã nối", "SI-1"))
	kq = K.khop_hoa_don("onepay", [_d("S67355O97492T080000", 500000, ngay="2026-09-01")], [_uv("SI-1", "97492", 500000, ngay="2026-11-14")])
	la("quá 45 ngày thì không", kq[0]["trang_thai"], "Không thấy chứng từ")
	la("cửa sổ đọc ứng viên OnePay", (K.cua_so_ngay("onepay"), K.cua_so_ngay("payoo"), K.cua_so_ngay("grab")), (45, 1, 0))


@ca("v655 OnePay nối theo tiền chỉ cho dòng KHÔNG có số đơn; dòng có số đơn chỉ được nối theo tiền vào hoá đơn không mang số đơn nào (nhập tay)")
def _():
	kq = K.khop_hoa_don("onepay", [_d("PL_1", 300000)], [_uv("SI-1", "97000", 300000)])
	la("mã không số đơn: nối theo tiền như cũ", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Nối theo tiền", "SI-1"))
	kq = K.khop_hoa_don("onepay", [_d("S1O97600T1", 300000)], [_uv("SI-TAY", "", 300000)])
	la("hoá đơn nhập tay không số đơn: gợi ý theo tiền", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Nối theo tiền", "SI-TAY"))
	kq = K.khop_hoa_don("onepay", [_d("S1O97600T1", 300000)], [_uv("SI-X", "97601", 300000)])
	la("hoá đơn của đơn khác: không", kq[0]["trang_thai"], "Không thấy chứng từ")
	# la_ung_vien (màn Bill chưa khớp) dùng đúng hai luật trên.
	la("la_ung_vien cùng luật", (K.la_ung_vien("onepay", _d("S1O97600T1", 300000), _uv("SI-X", "97601", 300000)),
		K.la_ung_vien("onepay", _d("S1O97600T1", 300000, ngay="2026-10-10"), _uv("SI-Y", "97600", 1, ngay="2026-11-12"))), (False, True))


@ca("v655 nối theo mã OnePay vẫn một đối một: hai dòng cùng số đơn (khách trả hai lần) chỉ một dòng lấy hoá đơn")
def _():
	kq = K.khop_hoa_don("onepay", [_d("S1O97700T1", 200000), _d("S1O97700T2", 200000)], [_uv("SI-1", "97700", 200000)])
	la("một dòng nối, dòng kia không lấy lại", sorted(r["hoa_don"] for r in kq.values()), ["", "SI-1"])


@ca("v655 các nguồn khác không đổi: Grab, Shopee, Payoo vẫn nối theo tiền như trước (luật mã riêng chỉ cho OnePay)")
def _():
	for kieu, ma in (("shopee", "2607170001066529"), ("payoo", "6118")):
		kq = K.khop_hoa_don(kieu, [_d(ma, 100000, ngay="2026-07-17")], [dict(name="SI-1", ngay="2026-07-17", tien=100000, ma=["123"], so_don="999")])
		la(kieu, kq[0]["trang_thai"], "Nối theo tiền")


# ------------------------------------------------------------ phần chạm hệ

@ca("v655 _gan_so_don_pancake: ứng viên OnePay (cả bill một kênh và chân OnePay của bill nhiều kênh) mang số đơn; đọc theo lô 500, đủ hơn 500 hoá đơn")
def _():
	from vagabond import doi_soat_vendor as V
	ra = [dict(name="SI-%d" % i, ma=[""]) for i in range(1203)] + [dict(name="SI-5", ma=["REF"])]
	goi = []

	def get_all(dt, filters=None, fields=None, limit_page_length=None, **k):
		goi.append(len(filters["name"][1]))
		assert limit_page_length == 0
		return [NS(name=n, remarks="Pancake #%s - A" % (90000 + int(n[3:])), get=lambda f, n=n: {"remarks": "Pancake #%s - A" % (90000 + int(n[3:]))}.get(f))
			for n in filters["name"][1]]
	with patch.object(V.frappe, "get_all", get_all, create=True):
		V._gan_so_don_pancake(ra, NS(has_field=lambda f: False))
	la("đọc ba lô", goi, [500, 500, 203])
	la("mọi ứng viên có số đơn", sum(1 for u in ra if u["so_don"]), 1204)
	la("chân OnePay của bill nhiều kênh cũng có", [(u["so_don"], u["ma"]) for u in ra if u["name"] == "SI-5" and "REF" in u["ma"]], [("90005", ["REF", "90005"])])
	la("số đơn vào danh sách mã", ra[7]["ma"], ["", "90007"])


class KhoNoiLai:
	"""Nguồn đối soát giả cho doi_chieu_lai_dong: ghi thứ tự lấy khoá, đọc, đối chiếu."""

	def __init__(self, nguon):
		self.nguon = {n["name"]: dict(n) for n in nguon}
		self.nhat = []
		self.loc = None
		self.sua_khi_cho_khoa = {}

	def get_all(self, dt, filters=None, fields=None, limit_page_length=None, **k):
		self.loc = filters
		assert limit_page_length == 0, "phải đọc đủ"
		return [NS(name=x, **{f: n.get(f) for f in fields if f != "name"}, get=lambda f, n=n: n.get(f))
			for x, n in self.nguon.items() if n["nhom"] == "Tiền bán" and n["trang_thai"] == "Đã nhận"
			and n["so_chua_noi"] > 0 and n["den_ngay"] >= filters["den_ngay"][1]]

	def get_value(self, dt, name, f, as_dict=False, **k):
		n = self.nguon[name]
		self.nhat.append(("doc", name))
		if as_dict:
			return NS(**{x: n.get(x) for x in f})
		return n.get(f)

	def khoa(self, *a, **k):
		self.nhat.append(("khoa",))
		# Một lượt khác vừa đối chiếu xong nguồn này trong lúc chờ khoá.
		for name, cap in self.sua_khi_cho_khoa.items():
			self.nguon[name].update(cap)
		self.sua_khi_cho_khoa = {}
		return nullcontext()

	def doi_chieu(self, name):
		self.nhat.append(("doi_chieu", name))
		self.nguon[name]["so_chua_noi"] = 0

	def chay(self, **kw):
		from vagabond import doi_soat_vendor as V

		def add_days(d, n):
			import datetime
			return str(datetime.date.fromisoformat(str(d)[:10]) + datetime.timedelta(days=n))
		with ExitStack() as st:
			st.enter_context(patch.object(V.frappe, "get_all", self.get_all, create=True))
			st.enter_context(patch.object(V.frappe.db, "get_value", self.get_value, create=True))
			st.enter_context(patch.object(V.frappe.utils, "add_days", add_days, create=True))
			st.enter_context(patch.object(V.frappe.utils, "nowdate", lambda: "2026-11-13", create=True))
			st.enter_context(patch.object(V.frappe, "log_error", lambda *a, **k: self.nhat.append(("loi",)), create=True))
			st.enter_context(patch.object(V.frappe, "get_traceback", lambda *a: "", create=True))
			st.enter_context(patch.object(V, "khoa_doi_chieu", self.khoa))
			st.enter_context(patch.object(V, "_doi_chieu", self.doi_chieu))
			return V.doi_chieu_lai_dong(**kw)


def _n(name, den, chua, **k):
	return dict(dict(name=name, nhom="Tiền bán", trang_thai="Đã nhận", so_chua_noi=chua, den_ngay=den, duong_vao=""), **k)


@ca("v655 mỗi giờ đối chiếu lại nguồn Tiền bán còn dòng chưa nối trong 30 ngày: lấy khoá rồi mới đọc lại nguồn; bỏ nguồn từ chối và nguồn đã nối đủ")
def _():
	k = KhoNoiLai([_n("DSN-OP-1", "2026-11-12", 17), _n("DSN-OP-2", "2026-11-01", 3), _n("DSN-CU", "2026-10-10", 5),
		_n("DSN-TC", "2026-11-11", 4, duong_vao="Từ chối"), _n("DSN-DU", "2026-11-12", 0)])
	k.sua_khi_cho_khoa = {"DSN-OP-2": {"so_chua_noi": 0}}
	kq = k.chay()
	la("mốc 30 ngày", k.loc["den_ngay"], [">=", "2026-10-14"])
	la("thứ tự: khoá, đọc lại, đối chiếu; nguồn vừa được lượt khác nối đủ thì bỏ",
		[x for x in k.nhat if x[0] != "loi"], [("khoa",), ("doc", "DSN-OP-1"), ("doi_chieu", "DSN-OP-1"), ("doc", "DSN-OP-1"),
			("khoa",), ("doc", "DSN-OP-2")])
	la("đếm", kq, dict(so_nguon=2, doi=1))


@ca("v655 bản vá một lần đối chiếu lại từ 01/10/2026 (quá mốc 30 ngày), chạy nền sau migrate, không tạo chứng từ")
def _():
	k = KhoNoiLai([_n("DSN-2611-06762", "2026-11-05", 8), _n("DSN-2610-00100", "2026-10-02", 2), _n("DSN-2609", "2026-09-30", 1)])
	kq = k.chay(tu_ngay="2026-10-01", toi_da=1000)
	la("hai nguồn từ 01/10", sorted(x[1] for x in k.nhat if x[0] == "doi_chieu"), ["DSN-2610-00100", "DSN-2611-06762"])
	la("đếm", kq["so_nguon"], 2)
	from vagabond.patches import v655_doi_chieu_lai_tien_ban as P
	xep = []
	with patch.object(P, "__builtins__", P.__builtins__):
		import frappe
		with patch.object(frappe.db, "table_exists", lambda dt: True, create=True), \
				patch.object(frappe, "enqueue", lambda m, **kw: xep.append((m, kw)), create=True):
			P.execute()
	la("xếp hàng nền đúng hàm, đúng mốc", [(m, kw.get("tu_ngay"), kw.get("enqueue_after_commit")) for m, kw in xep],
		[("vagabond.doi_soat_vendor.doi_chieu_lai_dong", "2026-10-01", True)])


@ca("v655 THUẦN chon_nguon_noi_lai: mới nhất trước, trần số nguồn mỗi lượt")
def _():
	from vagabond import doi_soat_vendor as V
	ds = [dict(name="A", den_ngay="2026-11-01", so_chua_noi=1), dict(name="B", den_ngay="2026-11-12", so_chua_noi=2),
		dict(name="C", den_ngay="2026-11-05", so_chua_noi=0), dict(name="D", den_ngay="2026-11-10", so_chua_noi=3, duong_vao="Từ chối")]
	la("thứ tự và trần", [r["name"] for r in V.chon_nguon_noi_lai(ds, 1)], ["B"])
	la("đủ", [r["name"] for r in V.chon_nguon_noi_lai(ds, 60)], ["B", "A"])
	dung("lượt mỗi giờ gọi đối chiếu lại dòng", "doi_chieu_lai_dong()" in open(V.__file__, encoding="utf-8").read().split("def quet_moi_gio")[1].split("\ndef ")[0])


@ca("v655 chữ Đã khép đổi thành Đã hoàn tất: lọc nhận cả khoá mới lẫn khoá cũ của app trong bộ nhớ máy; số đếm có cả hai khoá")
def _():
	from vagabond import doi_soat_vendor as V
	la("khoá mới", V.loc_trang_thai("Đã hoàn tất"), {"xac_nhan_luc": ["is", "set"]})
	la("khoá cũ", V.loc_trang_thai("Đã khép"), {"xac_nhan_luc": ["is", "set"]})
	from vagabond import doi_soat_thu as T
	src = open(T.__file__, encoding="utf-8").read()
	dung("bước cuối hiện Đã hoàn tất", 'ghi = "Đã hoàn tất" if hien == 7' in src)
	dem, _ = V.dem_nguon([dict(nhom="Tiền bán", vendor="OnePay", xac_nhan_luc="2026-11-13 09:00"), dict(nhom="Tiền bán", vendor="OnePay")])
	la("số đếm hai khoá", (dem.get("Đã hoàn tất"), dem.get("Đã khép")), (1, 1))
