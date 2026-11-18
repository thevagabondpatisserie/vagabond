# -*- coding: utf-8 -*-
"""v673 (chị Dung 18/11/2026): nguồn "Trùng số tiền, kế toán chọn" kẹt bước 4.

Màn Đối soát nhà cung cấp ghi GrabFood 16/11 (5.503.254 đ) "Cần chọn tiền về":
sao kê có hơn một khoản có thể là tiền của đợt, máy không tự chọn, nhưng app
không có nút nào để kế toán chọn. Nguồn nằm vàng mãi, nút Xác nhận không mở.

Các ca chạy THẬT doi_soat_khop (phần thuần) và doi_soat_vendor._tien_ve,
chon_tien_ve, bo_chon_tien_ve, ung_vien_tien_ve; chỉ thay tầng chạm hệ bằng kho
trong bộ nhớ (du_lieu của nguồn được lưu thật, để lựa chọn sống qua lượt dò lại).
"""
import datetime
import json
from contextlib import ExitStack, contextmanager
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import doi_soat_khop as K
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GRAB = "GRAB TT DOANH THU THE VAGABOND PATISSERIE %s"


def _g(name, tien, mo_ta="", ngay="2026-11-17"):
	return dict(name=name, ngay=ngay, tien=tien, mo_ta=mo_ta)


# ------------------------------------------------------------ phần thuần

@ca("v673 ứng viên chọn tay: đúng các giao dịch cùng số máy đã nêu, không rộng hơn luật máy")
def _():
	gd = [_g("BT-1", 5503254, GRAB % "NVHTN"), _g("BT-2", 5503254, GRAB % "NVHTN"),
		_g("BT-3", 4000000, GRAB % "NVHTN"), _g("BT-4", 5503254, "NOP TIEN MAT")]
	tt = K.khop_ngan_hang("grabfood", 5503254, "2026-11-15", "2026-11-22", gd)[0]
	la("máy không tự chọn", tt, "Cần chọn tiền về")
	la("chỉ hai khoản cùng số đúng mẫu Grab", [g["name"] for g in K.ung_vien_chon(
		"grabfood", 5503254, "2026-11-15", "2026-11-22", gd)], ["BT-1", "BT-2"])
	la("khoản nguồn khác đã giữ bị loại", [g["name"] for g in K.ung_vien_chon(
		"grabfood", 5503254, "2026-11-15", "2026-11-22", gd, da_dung={"BT-1"})], ["BT-2"])
	la("ngoài cửa sổ ngày bị loại", K.ung_vien_chon("grabfood", 5503254, "2026-11-18", "2026-11-22", gd), [])


@ca("v673 không có khoản cùng số: được chọn khoản đúng mẫu đối tác để báo lệch; nguồn không mẫu (Shinhan) thì không")
def _():
	gd = [_g("BT-1", 5400000, GRAB % "NVHTN"), _g("BT-2", 5300000, GRAB % "NVHTN"), _g("BT-9", 999, "KHAC")]
	la("Grab: hai khoản đúng mẫu", [g["name"] for g in K.ung_vien_chon(
		"grabfood", 5503254, "2026-11-15", "2026-11-22", gd)], ["BT-1", "BT-2"])
	la("Shinhan không mẫu nội dung, khác số: không có gì để chọn",
		K.ung_vien_chon("shinhan_ngay", 5503254, "2026-11-15", "2026-11-22", gd), [])
	la("Shinhan cùng số thì chọn được", [g["name"] for g in K.ung_vien_chon(
		"shinhan_ngay", 999, "2026-11-15", "2026-11-22", gd)], ["BT-9"])


@ca("v673 kết quả chọn: cùng số là Đã thấy, khác số là Lệch có số chênh; còn hợp lệ theo đủ luật ứng viên")
def _():
	la("cùng số", K.ket_qua_chon(100, _g("BT-1", 100))[0], "Đã thấy tiền về")
	tt, ghi = K.ket_qua_chon(100, _g("BT-1", 90))
	la("khác số", tt, "Lệch tiền về")
	dung("ghi số chênh", "-10" in ghi and "BT-1" in ghi)
	gd = [_g("BT-1", 100, GRAB % "A")]
	dung("còn hợp lệ", K.con_hop_le("grabfood", "BT-1", "2026-11-15", "2026-11-22", gd))
	la("nguồn khác vừa giữ", K.con_hop_le("grabfood", "BT-1", "2026-11-15", "2026-11-22", gd, {"BT-1"}), None)
	la("giao dịch không còn trên sao kê", K.con_hop_le("grabfood", "BT-1", "2026-11-15", "2026-11-22", []), None)


# ------------------------------------------------------------ phần chạm hệ

def _ngay(d, n):
	return str(datetime.date.fromisoformat(str(d)[:10]) + datetime.timedelta(days=n))


class Kho:
	"""Nguồn đối soát (có du_lieu thật) và giao dịch ngân hàng giả."""

	def __init__(self, nguon, gd, vai=("Accounts User",)):
		self.nguon = {n["name"]: dict(n) for n in nguon}
		self.gd = list(gd)
		self.vai = set(vai)
		self.khoa = []
		self.kiem_xn = []
		self.khi_khoa = None

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
		d.as_dict = lambda: dict(n)
		return d

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		if dt == "Bank Transaction":
			tu, den = filters["date"][1]
			return [NS(name=g[0], date=g[1], deposit=g[2], description=g[3], reference_number="")
				for g in self.gd if str(tu) <= g[1] <= str(den)]
		if pluck == "giao_dich_ngan_hang":
			return [n.get("giao_dich_ngan_hang") for x, n in self.nguon.items()
				if x != filters["name"][1] and n.get("giao_dich_ngan_hang")]
		return []

	def ghi_them(self, name, **k):
		d = json.loads(self.nguon[name].get("du_lieu") or "{}")
		d.update(k)
		self.nguon[name]["du_lieu"] = json.dumps(d, ensure_ascii=False)

	@contextmanager
	def _khoa(self, *a, **k):
		self.khoa.append("vao")
		if self.khi_khoa:
			self.khi_khoa()
		try:
			yield
		finally:
			self.khoa.append("ra")

	def chay(self, ham, *a, **kw):
		from vagabond import doi_soat_thu as T
		from vagabond import doi_soat_vendor as V
		with ExitStack() as st:
			p = lambda o, t, v: st.enter_context(patch.object(o, t, v, create=True))
			p(V.frappe, "get_all", self.get_all)
			p(V.frappe, "get_doc", lambda dt, name: self._doc(name))
			p(V.frappe, "get_meta", lambda dt: NS(has_field=lambda f: False))
			p(V.frappe, "get_roles", lambda *x: list(self.vai))
			p(V.frappe, "PermissionError", type("PermissionError", (Exception,), {}))
			p(V.frappe.utils, "add_days", _ngay)
			p(V.frappe.db, "count", lambda dt, f=None: 0)
			p(V.frappe.db, "get_value", lambda dt, name, f, **k: self.nguon[name][f])
			p(V, "_ghi_them", self.ghi_them)
			p(V, "khoa_doi_chieu", self._khoa)
			p(V, "_chan_cong_ty", lambda c: None)
			p(V, "chi_tiet", lambda name: dict(trang_thai_tien=self.nguon[name]["trang_thai_tien"]))
			p(T, "kiem_xac_nhan", lambda name: self.kiem_xn.append(name))
			p(T, "la_giam_doc", lambda: "Giám đốc" in self.vai)
			return ham(*a, **kw)


def _nguon(name="DSN-GRAB-1611", thuc_nhan=5503254, tt="Cần chọn tiền về", **k):
	n = dict(name=name, mau="grabfood", nhom="Tiền bán", trang_thai="Đã nhận", tu_ngay="2026-11-16",
		den_ngay="2026-11-16", ngay_tien_ve="2026-11-17", thuc_nhan=thuc_nhan, trang_thai_tien=tt,
		giao_dich_ngan_hang="", company="CT", tai_khoan="", du_lieu="{}")
	n.update(k)
	return n


GD = [("BT-1", "2026-11-17", 5503254, GRAB % "NVHTN"), ("BT-2", "2026-11-17", 5503254, GRAB % "NVHTN")]


@ca("v673 trước sửa: nguồn trùng số tiền nằm Cần chọn tiền về sau mỗi lượt dò, không có đường nào ra")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon()], GD)
	k.chay(lambda: V._tien_ve(k._doc("DSN-GRAB-1611")))
	la("vẫn chờ", k.nguon["DSN-GRAB-1611"]["trang_thai_tien"], "Cần chọn tiền về")
	la("không giữ giao dịch", k.nguon["DSN-GRAB-1611"]["giao_dich_ngan_hang"], "")


@ca("v673 kế toán chọn BT-2: nguồn Đã thấy tiền về, giữ đúng BT-2, gỡ xác nhận cũ nếu đổi; lấy khoá trước khi đọc")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon()], GD)
	ds = k.chay(V.ung_vien_tien_ve, name="DSN-GRAB-1611")
	la("hai ứng viên cùng số", [(g["name"], g["cung_so"]) for g in ds["ds"]], [("BT-1", True), ("BT-2", True)])
	k.chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd="BT-2")
	n = k.nguon["DSN-GRAB-1611"]
	la("đã thấy", n["trang_thai_tien"], "Đã thấy tiền về")
	la("giữ BT-2", n["giao_dich_ngan_hang"], "BT-2")
	la("lưu người chọn", json.loads(n["du_lieu"])["tien_ve_chon"]["gd"], "BT-2")
	la("kiểm lại xác nhận", k.kiem_xn, ["DSN-GRAB-1611"])
	la("trong khoá", k.khoa, ["vao", "ra"])


@ca("v673 lựa chọn sống qua lượt dò lại mỗi giờ; nguồn khác không lấy được giao dịch đã chọn")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon(), _nguon("DSN-GRAB-KHAC", tt="Cần chọn tiền về")], GD)
	k.chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd="BT-1")
	k.chay(lambda: V._tien_ve(k._doc("DSN-GRAB-1611")))
	la("dò lại giữ lựa chọn", (k.nguon["DSN-GRAB-1611"]["trang_thai_tien"], k.nguon["DSN-GRAB-1611"]["giao_dich_ngan_hang"]),
		("Đã thấy tiền về", "BT-1"))
	k.chay(lambda: V._tien_ve(k._doc("DSN-GRAB-KHAC")))
	la("nguồn kia còn đúng một ứng viên BT-2 thì máy tự nhận", k.nguon["DSN-GRAB-KHAC"]["giao_dich_ngan_hang"], "BT-2")
	nem("nguồn kia không chọn được BT-1", lambda: k.chay(V.chon_tien_ve, name="DSN-GRAB-KHAC", gd="BT-1"))


@ca("v673 chọn khoản khác số: Lệch tiền về có số chênh, vẫn giữ giao dịch; bỏ lựa chọn thì về như máy")
def _():
	from vagabond import doi_soat_vendor as V
	gd = [("BT-1", "2026-11-17", 5400000, GRAB % "NVHTN"), ("BT-2", "2026-11-17", 5300000, GRAB % "NVHTN")]
	k = Kho([_nguon()], gd)
	k.chay(lambda: V._tien_ve(k._doc("DSN-GRAB-1611")))
	la("máy: Cần chọn", k.nguon["DSN-GRAB-1611"]["trang_thai_tien"], "Cần chọn tiền về")
	k.chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd="BT-1")
	n = k.nguon["DSN-GRAB-1611"]
	la("lệch", (n["trang_thai_tien"], n["giao_dich_ngan_hang"]), ("Lệch tiền về", "BT-1"))
	la("số lệch cho tin", json.loads(n["du_lieu"])["lech_tien"], dict(gd="BT-1", nhan=5400000, bao=5503254))
	k.chay(V.bo_chon_tien_ve, name="DSN-GRAB-1611")
	la("bỏ chọn", (n["trang_thai_tien"], n["giao_dich_ngan_hang"]), ("Cần chọn tiền về", ""))
	nem("bỏ lần hai báo lỗi", lambda: k.chay(V.bo_chon_tien_ve, name="DSN-GRAB-1611"))


@ca("v673 giao dịch đã chọn bị nguồn khác giữ (hay huỷ khỏi sao kê): lượt dò bỏ lựa chọn, ghi lý do, không giữ chung")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon()], GD)
	k.chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd="BT-1")
	k.gd = GD[1:]
	k.chay(lambda: V._tien_ve(k._doc("DSN-GRAB-1611")))
	n = k.nguon["DSN-GRAB-1611"]
	la("máy nhận khoản còn lại", (n["trang_thai_tien"], n["giao_dich_ngan_hang"]), ("Đã thấy tiền về", "BT-2"))
	d = json.loads(n["du_lieu"])
	la("lựa chọn cũ bị bỏ", d["tien_ve_chon"], None)
	dung("ghi lý do", "BT-1" in d["tien_ve"] and "không còn dùng được" in d["tien_ve"])


@ca("v673 đọc SAU khoá: lượt khác giữ giao dịch đúng lúc kế toán bấm thì báo lỗi, không ghi")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon(), _nguon("DSN-KHAC", tt="Đã thấy tiền về")], GD)
	k.khi_khoa = lambda: k.nguon["DSN-KHAC"].update(giao_dich_ngan_hang="BT-2")
	nem("chặn", lambda: k.chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd="BT-2"))
	la("không ghi lựa chọn", json.loads(k.nguon["DSN-GRAB-1611"]["du_lieu"]).get("tien_ve_chon"), None)
	la("không giữ", k.nguon["DSN-GRAB-1611"]["giao_dich_ngan_hang"], "")


@ca("v673 chỉ kế toán (hoặc giám đốc) chọn được; nguồn đã thấy tiền về và chưa chọn thì không mở chọn")
def _():
	from vagabond import doi_soat_vendor as V
	k = Kho([_nguon()], GD, vai=("Sales User",))
	with patch.object(V, "_chan", lambda ghi=False: None):
		nem("vai khác bị chặn", lambda: k.chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd="BT-1"))
	k2 = Kho([_nguon(tt="Đã thấy tiền về", giao_dich_ngan_hang="BT-9")], GD)
	nem("nguồn đã thấy không mở", lambda: k2.chay(V.ung_vien_tien_ve, name="DSN-GRAB-1611"))
	nem("giao dịch rỗng", lambda: Kho([_nguon()], GD).chay(V.chon_tien_ve, name="DSN-GRAB-1611", gd=""))
