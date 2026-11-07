# -*- coding: utf-8 -*-
"""v643: khách tự chọn ưu đãi trên trang gọi món tại bàn (anh Việt duyệt mẫu
07/11/2026, chốt "Máy tự trừ ngay").

Ca chạm hệ chạy HÀM THẬT của uu_dai_ban (ds, chon, bo, bo_quay, tinh_lai,
truoc_chot, sau_chot), goi_mon_ban.the_bill, quyen_quay.them_giam_gia và
ban_hang.pos_chot (nạp riêng bằng ast vì ban_hang kéo requests), chỉ thay tầng
Frappe bằng một hoá đơn giả tự tính grand_total khi lưu như ERPNext. Phép tính
khuyến mãi thay bằng một chương trình giả "giảm 10% hoá đơn từ 150.000 đ" để
ca không phụ thuộc bảng CTKM; ca _tinh_goi chốt riêng uu_dai_ban gọi đúng
khuyen_mai.tinh với đúng tham số. Bench: kiem_that/thu_uu_dai_ban_643.py.
"""

import ast
import contextlib
import json
import re
import sys
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import goi_mon_ban, quyen_quay  # noqa: E402
from vagabond import uu_dai_ban as u  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
SDT = "0909123412"
KHACH = "CUST-0001"
DIEM = {"ma": "TCV", "quay": "TCV", "ten": "The Vagabond District 1"}


class HoaDon(_fr._dict):
	"""Sales Invoice nháp giả: lưu thì tính lại grand_total như ERPNext
	(tổng dòng trừ discount_amount, không âm)."""

	def __init__(self, **k):
		super().__init__(**k)
		self["items"] = [_fr._dict(x) for x in k.get("items") or []]
		self["flags"] = _fr._dict()
		self.luu = 0
		self.ghi_chu = []
		self.tinh()

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def tinh(self):
		t = sum(float(x.qty) * float(x.rate) for x in self["items"])
		self["total"] = t
		self["grand_total"] = max(0.0, t - float(self.get("discount_amount") or 0))

	def append(self, f, d):
		self[f].append(_fr._dict(d))

	def save(self, *a, **k):
		self.tinh()
		self.luu += 1
		# Bench #546: ghi lại người đang đăng nhập lúc lưu (khách là Guest).
		ss = getattr(_fr, "session", None)
		self["luu_boi"] = getattr(ss, "user", None)
		if self.get("nhat_ky") is not None:
			self["nhat_ky"].append("luu")

	def add_comment(self, loai, chu):
		self.ghi_chu.append(chu)


def _hd(**k):
	d = dict(name="ACC-SINV-0001", docstatus=0, vgb_tam_tinh=1, vgb_huy=0, vgb_quay="TCV", vgb_so_ban="5",
		custom_nguon=goi_mon_ban.NGUON_QR, discount_amount=0, vgb_giam_diem=0, vgb_giam_ud=0, vgb_ud_ban="",
		items=[{"item_code": "NUTR00021", "qty": 2, "rate": 45000}, {"item_code": "BAWC00115", "qty": 1, "rate": 95000}])
	d.update(k)
	return HoaDon(**d)


def km_gia(items, ctkm=None, ma=None, khach=None, **k):
	"""Khuyến mãi giả: VC-8K2Q và CTKM-10 giảm 10% hoá đơn từ 150.000 đ.
	Khách có hạng thì kèm thêm dòng ưu đãi hạng 5% (phải bị bỏ qua)."""
	tong = sum(float(d["qty"]) * float(d["rate"]) for d in items)
	ap, bo = [], []
	ten = "Giảm 10% hoá đơn"
	# VC-KHAC là mã hợp lệ của KHÁCH KHÁC: khuyến mãi giả vẫn áp, chỉ cửa
	# "mã phải nằm trong Ví quà của chính số đăng nhập" chặn được.
	if ma in ("VC-8K2Q", "VC-KHAC") or "CTKM-10" in (ctkm or []):
		if tong >= 150000:
			ap.append({"loai": "ctkm", "ma": "CTKM-10", "ten": ten, "giam": round(tong * 0.1), "voucher": ma or ""})
		else:
			bo.append({"ten": ten, "ly_do": "hoá đơn chưa đủ 150.000 đ"})
	# Codex PR #546 vòng 1: VC-OTP là mã trong Ví quà của chương trình CẦN OTP
	# quản lý (can_otp=1). tinh chỉ báo cờ can_otp, không tự chặn.
	if ma == "VC-OTP":
		ap.append({"loai": "ctkm", "ma": "CTKM-OTP", "ten": "Giảm sâu cần quản lý", "giam": round(tong * 0.3), "voucher": ma, "can_otp": 1})
	if khach:
		ap.append({"loai": "hang", "ma": "Voyager", "ten": "Ưu đãi hạng Voyager", "giam": round(tong * 0.05)})
	return {"tong_hd": tong, "tong_giam": sum(a["giam"] for a in ap), "ap": ap, "bo": bo, "voucher": ma or "",
		"can_otp": 1 if any(a.get("can_otp") for a in ap) else 0}


VI = [{"ma": "VC-8K2Q", "uu_dai": "Giảm 10% hoá đơn", "han": "30/11", "dieu_kien": "đơn từ 150.000 đ", "trang_thai": "dung_duoc"}]
VI_OTP = VI + [{"ma": "VC-OTP", "uu_dai": "Giảm 30% hoá đơn", "han": "30/11", "dieu_kien": "", "trang_thai": "dung_duoc"}]
CTKM = [_fr._dict(name="CTKM-10", ten="Giảm 10% tại bàn", cach_ma="Khong can ma", cach_thuc="Giam tong hoa don", can_otp=0, kenh="", quay="", web_mo_ta=""),
	_fr._dict(name="CTKM-GRAB", ten="Grab giảm 20%", cach_ma="Khong can ma", cach_thuc="Giam tong hoa don", can_otp=0, kenh="GrabFood", quay="", web_mo_ta=""),
	_fr._dict(name="CTKM-OTP", ten="Giảm sâu cần quản lý", cach_ma="Khong can ma", cach_thuc="Giam tong hoa don", can_otp=1, kenh="", quay="", web_mo_ta=""),
	_fr._dict(name="CTKM-TANG", ten="Tặng bánh", cach_ma="Khong can ma", cach_thuc="Tang mon", can_otp=0, kenh="", quay="", web_mo_ta=""),
	_fr._dict(name="CTKM-MA", ten="Mã cố định", cach_ma="Ma co dinh", cach_thuc="Giam tong hoa don", can_otp=0, kenh="", quay="", web_mo_ta="")]


@contextlib.contextmanager
def _ban(si, sdt=SDT, khach=KHACH, link=True):
	"""Bàn 5 ở TCV, link đúng hay sai, phiên Thành viên của sdt (None là chưa
	đăng nhập), hoá đơn tạm tính si (None là bàn chưa có hoá đơn)."""
	from vagabond import khuyen_mai

	with patch.object(goi_mon_ban, "_kiem_link", return_value=(DIEM, 5) if link else (None, None)), \
			patch.object(u, "_phien", return_value=(sdt, khach) if sdt else (None, None)), \
			patch.object(u, "_hoa_don_ban", side_effect=lambda d, n, khoa=False: si), \
			patch.object(u, "_vi", side_effect=lambda kh: list(VI) if kh == KHACH else []), \
			patch.object(_fr, "get_all", side_effect=lambda dt, **k: list(CTKM) if dt == u.DT_CTKM else []), \
			patch.object(khuyen_mai, "tinh", side_effect=km_gia), \
			patch.object(khuyen_mai, "tinh_co_khoa", side_effect=km_gia), \
			patch.object(_fr.local, "response_headers", {}, create=True), \
			patch.object(_fr, "session", _fr._dict(user="Guest"), create=True), \
			patch.object(_fr, "set_user", lambda nd: setattr(_fr.session, "user", nd), create=True):
		yield


# ------------------------------------------------------------------ thuần

@ca("v643 ưu đãi tại bàn thuần: số giảm chỉ của ưu đãi khách chọn (bỏ ưu đãi hạng), lý do khi không áp, che số, đọc JSON hỏng")
def _thuan():
	kq = km_gia([{"qty": 1, "rate": 185000}], ma="VC-8K2Q", khach=KHACH)
	la("bỏ phần hạng 5%", u.giam_tu_kq(kq), (18500.0, ""))
	la("không đủ điều kiện, lý do của ưu đãi chính", u.giam_tu_kq(km_gia([{"qty": 1, "rate": 90000}], ma="VC-8K2Q", khach=KHACH)),
		(0, "hoá đơn chưa đủ 150.000 đ"))
	la("chỉ còn lý do của hạng thì nói chung", u.giam_tu_kq({"ap": [], "bo": [{"ten": "Ưu đãi hạng Voyager", "ly_do": "x"}]}), (0, "không đủ điều kiện"))
	la("cắt về tổng hoá đơn", u.giam_tu_kq({"tong_hd": 50000, "ap": [{"loai": "ctkm", "giam": 80000}]}), (50000.0, ""))
	la("che số", [u.che_sdt(x) for x in ("0909123412", "+84 909 123 412", "12", None)], ["0909 *** 412", "0909 *** 412", "", ""])
	la("JSON hỏng hay thiếu mã thì như chưa chọn", [u.doc_ud(x) for x in ("{", "[]", '{"loai":"ma"}', '{"loai":"x","ma":"A"}', None)], [{}] * 5)
	la("chuẩn mã ví", u.chuan_chon("ma", " vc-8k2q "), ("ma", "VC-8K2Q"))
	for x in (("ma", "<b>"), ("ma", "A"), ("hang", "Voyager"), ("ctkm", ""), (None, None)):
		la("mã lạ %r" % (x,), u.chuan_chon(*x), (None, None))
	la("kẹp không âm, chừa phần giảm khác", [u.kep_giam(50000, 185000, 150000), u.kep_giam(-5, 100, 0), u.kep_giam(20, 100, 0)], [35000.0, 0.0, 20.0])
	la("tổng dòng lấy tiền combo đã chia", u.tong_dong([{"qty": 3, "rate": 33333.33, "vgb_combo_tien": 100000, "vgb_combo_luong": 3}, {"qty": 2, "rate": 10}]), 100020.0)
	la("thẻ khách thấy", u.the_ud(json.dumps({"loai": "ma", "ma": "VC-8K2Q", "ten": "Giảm 10%", "giam": 18500.4, "sdt": SDT, "khach": KHACH})),
		{"ten": "Giảm 10%", "giam": 18500, "ly_do": "", "sdt": "0909 *** 412"})
	from vagabond import khuyen_mai
	ds = u.loc_ctkm(CTKM, goi_mon_ban.NGUON_QR, "TCV", khuyen_mai._hop_kenh, khuyen_mai.CACH_THUC_WEB)
	la("chỉ chương trình không mã, không OTP quản lý, giảm tiền, mở cho bàn", [x.name for x in ds], ["CTKM-10"])


@ca("v643 dat_giam: phần ưu đãi tách riêng, giữ giảm tay và giảm điểm, gọi nhiều lần không cộng dồn, không kéo bill dưới 0")
def _dat_giam():
	si = _hd(discount_amount=30000, vgb_giam_diem=10000)
	la("đặt lần đầu", u.dat_giam(si, 18500), 18500.0)
	la("discount = phần khác + phần ưu đãi", (si.discount_amount, si.vgb_giam_ud, si.apply_discount_on), (48500.0, 18500.0, "Grand Total"))
	u.dat_giam(si, 18500)
	u.dat_giam(si, 20000)
	la("gọi lại không cộng dồn", (si.discount_amount, si.vgb_giam_ud), (50000.0, 20000.0))
	u.dat_giam(si, 0)
	la("bỏ thì về đúng phần khác", (si.discount_amount, si.vgb_giam_ud), (30000.0, 0.0))
	la("không quá tổng còn lại", u.dat_giam(si, 999999), 155000.0)
	si.append("items", {"item_code": "NUTR00021", "qty": 1, "rate": 45000})
	la("vừa thêm món chưa lưu: tổng tính từ dòng", u.dat_giam(si, 999999), 200000.0)


# ------------------------------------------------------------- chạm hệ

@ca("v643 danh sách ưu đãi: chưa đăng nhập thì mời đăng nhập; đã đăng nhập thì Ví quà trước, chương trình sau, số giảm theo hoá đơn của bàn")
def _ds():
	with _ban(None, link=False):
		la("link sai", u.ds("TCV", 5, "x").get("ok"), 0)
	with _ban(_hd(), sdt=None):
		la("chưa đăng nhập", u.ds("TCV", 5, "k"), {"ok": 1, "dang_nhap": 0})
	with _ban(_hd()):
		r = u.ds("TCV", 5, "k")
	la("đăng nhập, có hoá đơn, che số", (r["dang_nhap"], r["co_hoa_don"], r["sdt"], r["chon"]), (1, 1, "0909 *** 412", None))
	la("ví trước, chương trình sau, Grab/OTP/tặng món/mã cố định không hiện", [(x["nhom"], x["ma"], x["giam"], x["dung_duoc"]) for x in r["ds"]],
		[("vi", "VC-8K2Q", 18500, 1), ("ctkm", "CTKM-10", 18500, 1)])
	la("dòng phụ của mã ví", r["ds"][0]["phu"], "Mã VC-8K2Q · hạn 30/11 · đơn từ 150.000 đ")
	with _ban(_hd(items=[{"item_code": "NUTR00021", "qty": 1, "rate": 45000}])):
		r = u.ds("TCV", 5, "k")
	la("hoá đơn nhỏ: mờ kèm lý do", [(x["giam"], x["dung_duoc"], x["ly_do"]) for x in r["ds"]], [(0, 0, "hoá đơn chưa đủ 150.000 đ")] * 2)
	with _ban(None):
		r = u.ds("TCV", 5, "k")
	la("bàn chưa có hoá đơn: chưa có số giảm", (r["co_hoa_don"], [x["giam"] for x in r["ds"]]), (0, [None, None]))


@ca("v643 khách chọn ưu đãi: máy trừ NGAY vào hoá đơn tạm tính, đổi ưu đãi không cộng dồn, số khác không chen, mã không trong ví bị chặn")
def _chon():
	si = _hd(discount_amount=10000)
	with _ban(si):
		r = u.chon("TCV", 5, "k", "ma", "vc-8k2q")
	la("áp ngay", (r["ok"], r["chon"]["giam"], r["tong"]), (1, 18500, 185000 - 10000 - 18500))
	la("đã lưu và giữ giảm tay", (si.luu, si.discount_amount, si.vgb_giam_ud), (1, 28500.0, 18500.0))
	# Bench #546 (07/11/2026): lưu bằng phiên Guest thì ERPNext ném PermissionError
	# ở get_party_account. Bước lưu phải chạy bằng quyền hệ thống rồi trả lại Guest.
	la("lưu bằng quyền hệ thống", si.luu_boi, "Administrator")
	ud = json.loads(si.vgb_ud_ban)
	la("lưu lựa chọn", (ud["loai"], ud["ma"], ud["sdt"], ud["khach"], ud["giam"]), ("ma", "VC-8K2Q", SDT, KHACH, 18500))
	with _ban(si):
		r = u.chon("TCV", 5, "k", "ctkm", "CTKM-10")
	la("đổi sang chương trình: thay, không cộng", (r["ok"], si.discount_amount, si.vgb_giam_ud, json.loads(si.vgb_ud_ban)["loai"]), (1, 28500.0, 18500.0, "ctkm"))
	with _ban(si, sdt="0912000111", khach="CUST-0002"):
		r = u.chon("TCV", 5, "k", "ctkm", "CTKM-10")
		r2 = u.bo("TCV", 5, "k")
	la("số khác cùng bàn không chen", (r["ok"], "0909 *** 412" in r["cau"]), (0, True))
	la("số khác không bỏ được", r2["ok"], 0)
	la("hoá đơn không đổi", (si.discount_amount, si.luu), (28500.0, 2))
	si2 = _hd()
	with _ban(si2):
		la("mã hợp lệ nhưng của khách khác (không trong ví)", u.chon("TCV", 5, "k", "ma", "VC-KHAC")["ok"], 0)
		la("chương trình cần OTP quản lý không chọn được", u.chon("TCV", 5, "k", "ctkm", "CTKM-OTP")["ok"], 0)
		la("chương trình kênh khác", u.chon("TCV", 5, "k", "ctkm", "CTKM-GRAB")["ok"], 0)
	la("không lưu gì", (si2.luu, si2.discount_amount), (0, 0))
	with _ban(_hd(items=[{"item_code": "NUTR00021", "qty": 1, "rate": 45000}])):
		r = u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	la("chưa đủ điều kiện thì nói lý do", (r["ok"], "150.000" in r["cau"]), (0, True))
	with _ban(None):
		la("bàn chưa có hoá đơn", u.chon("TCV", 5, "k", "ma", "VC-8K2Q")["ok"], 0)
	with _ban(si, sdt=None):
		la("chưa đăng nhập", u.chon("TCV", 5, "k", "ma", "VC-8K2Q").get("dang_nhap"), 0)
	with _ban(si):
		r = u.bo("TCV", 5, "k")
	la("chính số đó bỏ: về phần giảm tay", (r["ok"], si.discount_amount, si.vgb_giam_ud, si.vgb_ud_ban, r["tong"]), (1, 10000.0, 0.0, "", 175000))
	la("bỏ cũng lưu bằng quyền hệ thống", si.luu_boi, "Administrator")
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
		la("xong trả lại đúng Guest", _fr.session.user, "Guest")

		def hong(*a, **k):
			raise ValueError("ERPNext hỏng")
		si.save = hong
		try:
			u.bo("TCV", 5, "k")
		except ValueError:
			pass
		la("lưu hỏng vẫn trả lại Guest", _fr.session.user, "Guest")


@ca("v643 bàn gọi thêm món: ưu đãi đã chọn tính lại trên giỏ mới; chưa đủ điều kiện thì giữ lựa chọn giảm 0, đủ lại thì tự áp")
def _tinh_lai():
	si = _hd(items=[{"item_code": "BAWC00115", "qty": 2, "rate": 95000}])
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
		la("ban đầu", si.vgb_giam_ud, 19000.0)
		si.append("items", {"item_code": "NUTR00021", "qty": 2, "rate": 45000})
		u.tinh_lai(si)
		si.save()
	la("gọi thêm: 10% của 280.000", (si.vgb_giam_ud, si.grand_total), (28000.0, 252000.0))
	with _ban(si):
		si["items"] = [_fr._dict(item_code="NUTR00021", qty=2, rate=45000)]
		u.tinh_lai(si)
		si.save()
	ud = json.loads(si.vgb_ud_ban)
	la("quầy bớt món dưới mức: giảm 0, giữ lựa chọn, có lý do", (si.vgb_giam_ud, si.grand_total, ud["ma"], ud["ly_do"]), (0.0, 90000.0, "VC-8K2Q", "hoá đơn chưa đủ 150.000 đ"))
	la("trang khách thấy lý do", goi_mon_ban.the_bill(si.name, si.grand_total, si.vgb_ud_ban)["ud"]["ly_do"], "hoá đơn chưa đủ 150.000 đ")
	with _ban(si):
		si.append("items", {"item_code": "BAWC00115", "qty": 1, "rate": 95000})
		u.tinh_lai(si)
	la("đủ lại thì tự áp", si.vgb_giam_ud, 18500.0)


def _nap_pos_chot():
	"""ban_hang.pos_chot THẬT nạp riêng (ban_hang kéo requests ở đầu tệp)."""
	cay = ast.parse((GOC / "vagabond/ban_hang.py").read_text())
	m = types.ModuleType("bh_643")
	gl = m.__dict__
	gl.update(frappe=_fr, flt=_fr.utils.flt, cint=_fr.utils.cint, quyen_quay=quyen_quay)
	for n in cay.body:
		if isinstance(n, ast.FunctionDef) and n.name in ("pos_chot", "_giam_tu_diem", "_giam_rieng"):
			n.decorator_list = []
			exec(compile(ast.Module(body=[n], type_ignores=[]), "ban_hang.py", "exec"), gl)
	gl.update(_kiem_quyen_ban=lambda: None, _nan_pt_tai_cho=lambda si: None, _otp_la_sep=lambda: False, _pos_lay=None,
		_otp_kiem=lambda *a: (_ for _ in ()).throw(AssertionError("không được đòi OTP")))
	return m


@ca("v643 chốt bill: ưu đãi tính lại có khoá, ghi lượt dùng SAU khi lưu (tiêu mã, cách duyệt Zalo, bỏ dòng hạng); số đổi thì lưu số mới và dừng chốt")
def _chot():
	from vagabond import khuyen_mai

	bh = _nap_pos_chot()
	si = _hd()
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	ghi, thu_tu = [], []
	si["nhat_ky"] = thu_tu
	with _ban(si), patch.object(bh, "_pos_lay", return_value=si), \
			patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda kq, ten, **k: (thu_tu.append("ghi"), ghi.append((kq, ten, k)))), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, ten, f, v, **k: si.__setitem__(f, v)), \
			patch.object(_fr.db, "commit", side_effect=lambda: thu_tu.append("commit")), \
			patch.object(quyen_quay, "muc", return_value="duyet"):
		r = bh.pos_chot(si.name)
	la("chốt xong đúng tổng", (r["ok"], r["grand_total"], si.vgb_tam_tinh), (1, 166500.0, 0))
	la("lưu, ghi lượt, rồi mới commit", thu_tu, ["luu", "ghi", "commit"])
	kq, ten, k = ghi[0]
	la("ghi đúng ưu đãi, bỏ dòng hạng", [(a["loai"], a["ma"], a["giam"]) for a in kq["ap"]], [("ctkm", "CTKM-10", 18500)])
	la("voucher tiêu", kq["voucher"], "VC-8K2Q")
	la("khách, số, cách duyệt", (ten, k["khach"], k["sdt"], k["cach_duyet"]), (si.name, KHACH, SDT, u.CACH_DUYET))
	la("đánh dấu đã ghi", json.loads(si.vgb_ud_ban).get("da_ghi"), 1)
	with _ban(si), patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda *a, **k: ghi.append(a)):
		u.sau_chot(si, kq)
		u.tinh_lai(si)
	la("không ghi lần hai", len(ghi), 1)
	nem("đã ghi lượt thì quầy không bỏ được", lambda: _bo_quay(si), _fr.ValidationError)

	si = _hd()
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	with _ban(si), patch.object(bh, "_pos_lay", return_value=si), \
			patch.object(khuyen_mai, "tinh_co_khoa", side_effect=lambda items, **k: km_gia(items + [{"qty": 1, "rate": 15000}], **k)), \
			patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda *a, **k: ghi.append(a)), \
			patch.object(quyen_quay, "muc", return_value="duyet"), \
			patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		nem("số đổi lúc chốt thì dừng", lambda: bh.pos_chot(si.name), u.UuDaiDoi)
	la("số mới đã lưu, bill vẫn tạm tính, chưa ghi lượt", (si.vgb_giam_ud, si.vgb_tam_tinh, len(ghi)), (20000.0, 1, 1))


def _nem_dung_lop(msg, exc=None, **k):
	"""frappe.throw thật ném đúng lớp exc; bản giả chung chỉ ném ValidationError."""
	raise (exc or _fr.ValidationError)(msg)


def _bo_quay(si):
	with patch.object(_fr, "get_doc", return_value=si), patch.dict(sys.modules, {"vagabond.ban_hang": types.SimpleNamespace(_kiem_quyen_ban=lambda: None)}):
		import vagabond
		with patch.object(vagabond, "ban_hang", sys.modules["vagabond.ban_hang"], create=True):
			return u.bo_quay(si.name, "khách đổi ý")


@ca("v643 quầy bỏ ưu đãi khách chọn: về đúng phần giảm khác, ghi lý do vào lịch sử hoá đơn")
def _quay_bo():
	si = _hd(discount_amount=5000)
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	r = _bo_quay(si)
	la("bỏ", (r["ok"], si.discount_amount, si.vgb_giam_ud, si.vgb_ud_ban), (1, 5000.0, 0.0, ""))
	dung("lịch sử có lý do", any("khách đổi ý" in x for x in si.ghi_chu))


@ca("v643 thu ngân sửa giảm tay trên bill có ưu đãi khách chọn: không coi ưu đãi là giảm tay cần OTP; thêm giảm tay thật vẫn cần")
def _quyen():
	si = _hd(discount_amount=28500, vgb_giam_ud=18500)
	with patch.object(quyen_quay, "muc", return_value="duyet"):
		la("giữ giảm tay 10.000 đ", quyen_quay.them_giam_gia(si, 10000), False)
		la("thêm giảm tay 15.000 đ", quyen_quay.them_giam_gia(si, 15000), True)


@ca("v643 trang bàn: hoá đơn của bàn kèm ưu đãi đã trừ (tên, số giảm, số che); chưa chọn thì không có khoá ud")
def _the_bill():
	ud = json.dumps({"loai": "ma", "ma": "VC-8K2Q", "ten": "Giảm 10% hoá đơn", "giam": 18500, "sdt": SDT})
	b = goi_mon_ban.the_bill("ACC-SINV-0001", 166500, ud)
	la("có ud", (b["tong"], b["ud"]["ten"], b["ud"]["giam"], b["ud"]["sdt"]), (166500, "Giảm 10% hoá đơn", 18500, "0909 *** 412"))
	dung("không lộ mã khách, số đủ", "CUST" not in json.dumps(b) and SDT not in json.dumps(b))
	la("chưa chọn", sorted(goi_mon_ban.the_bill("ACC-SINV-0001", 185000, "").keys()), ["khoa", "tong"])
	la("khoá không đổi khi có ưu đãi", b["khoa"], goi_mon_ban.the_bill("ACC-SINV-0001", 1)["khoa"])


@ca("v643 uu_dai_ban gọi khuyen_mai.tinh đúng tham số: mã ví vào ma, chương trình vào ctkm, quầy, nguồn, khách, số của hoá đơn")
def _tinh_goi():
	from vagabond import khuyen_mai

	goi = []
	si = _hd()
	with patch.object(khuyen_mai, "tinh", side_effect=lambda items, **k: goi.append(("tinh", items, k)) or {}), \
			patch.object(khuyen_mai, "tinh_co_khoa", side_effect=lambda items, **k: goi.append(("khoa", items, k)) or {}):
		u._tinh(si, {"loai": "ma", "ma": "VC-8K2Q", "sdt": SDT, "khach": KHACH})
		u._tinh(si, {"loai": "ctkm", "ma": "CTKM-10", "sdt": SDT, "khach": ""}, co_khoa=True)
	la("mã ví", (goi[0][0], goi[0][2]["ma"], goi[0][2]["ctkm"], goi[0][2]["khach"], goi[0][2]["sdt"]), ("tinh", "VC-8K2Q", [], KHACH, SDT))
	la("chương trình có khoá", (goi[1][0], goi[1][2]["ma"], goi[1][2]["ctkm"], goi[1][2]["khach"]), ("khoa", None, ["CTKM-10"], None))
	la("quầy, nguồn", (goi[0][2]["quay"], goi[0][2]["nguon"]), ("TCV", goi_mon_ban.NGUON_QR))
	la("giỏ", goi[0][1], [{"item_code": "NUTR00021", "qty": 2.0, "rate": 45000.0}, {"item_code": "BAWC00115", "qty": 1.0, "rate": 95000.0}])


@ca("v643 MỘT cửa giảm riêng: bốn chỗ dựng lại discount_amount trong ban_hang đều cộng _giam_rieng, không còn chỗ nào tự cộng _giam_tu_diem")
def _mot_cua():
	cay = ast.parse((GOC / "vagabond/ban_hang.py").read_text())
	goi = {"_giam_rieng": 0, "_giam_tu_diem": 0}
	for f in [n for n in cay.body if isinstance(n, ast.FunctionDef)]:
		for x in ast.walk(f):
			if isinstance(x, ast.Call) and getattr(x.func, "id", "") in goi:
				if f.name == "_giam_rieng" and x.func.id == "_giam_tu_diem":
					continue
				goi[x.func.id] += 1
	la("bốn chỗ qua _giam_rieng, không chỗ nào gọi thẳng _giam_tu_diem", goi, {"_giam_rieng": 4, "_giam_tu_diem": 0})
	bh = _nap_pos_chot()
	la("_giam_rieng cộng điểm và ưu đãi", bh._giam_rieng({"vgb_giam_diem": 10000, "vgb_giam_ud": 18500}), 28500.0)
	la("trước migrate (thiếu cột) vẫn 0", bh._giam_rieng({}), 0.0)
	# Ba cửa xoá mọi khoản giảm (hàng tặng, quà tặng hoá đơn, nội bộ) xoá cả phần ưu đãi.
	for tep in ("hang_tang.py", "qua_tang_hoa_don.py", "noi_bo.py"):
		s = (GOC / "vagabond" / tep).read_text()
		dung("%s xoá vgb_giam_ud" % tep, "vgb_giam_ud" in s and "vgb_ud_ban" in s)


@ca("v643 trường mới: hai trường Sales Invoice có neo insert_after, ưu đãi dựng sau nhóm nội bộ (neo vào vgb_noi_bo)")
def _truong():
	la("neo", [(x["fieldname"], x["insert_after"]) for x in u.TRUONG_MOI["Sales Invoice"]],
		[("vgb_giam_ud", "vgb_noi_bo"), ("vgb_ud_ban", "vgb_giam_ud")])
	s = (GOC / "vagabond/truong_tu_them.py").read_text()
	i, j = s.find('_dung_nhom(noi_bo.TRUONG_MOI'), s.find('_dung_nhom(uu_dai_ban.TRUONG_MOI')
	dung("đăng ký sau noi_bo", 0 < i < j)


@contextlib.contextmanager
def _bh_gia(**ham):
	import vagabond

	m = types.SimpleNamespace(**ham)
	with patch.dict(sys.modules, {"vagabond.ban_hang": m}), patch.object(vagabond, "ban_hang", m, create=True):
		yield m


@ca("v643 quầy nhận lượt gọi thêm vào phiếu có ưu đãi (goi_mon_ban._vao_phieu_tam thật): phần ưu đãi tính lại trên giỏ mới trước khi lưu")
def _vao_phieu():
	si = _hd(items=[{"item_code": "BAWC00115", "qty": 2, "rate": 95000}])
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	la("trước", si.vgb_giam_ud, 19000.0)
	r = {"name": "TQ-9", "diem": "TCV", "ban": 5, "ghi_chu": "", "mon": json.dumps([{"ma": "NUTR00021", "ten": "Trà", "sl": 2, "gia": 45000}])}
	with _ban(si), _bh_gia(_dung_dong_mon=lambda x: dict(x)), patch.object(goi_mon_ban, "_phieu_tam_cua_ban", return_value=si.name), \
			patch.object(_fr, "get_doc", return_value=si):
		kq = goi_mon_ban._vao_phieu_tam(r)
	la("vào phiếu có sẵn", kq, (si.name, 1))
	la("ưu đãi 10% của 280.000, tổng sau giảm", (si.vgb_giam_ud, si.discount_amount, si.grand_total), (28000.0, 28000.0, 252000.0))


@ca("v643 hoá đơn của bàn đọc từ máy chủ (_tong_bill thật): kèm ưu đãi đã chọn; thiếu cột ưu đãi (trước migrate) vẫn trả tổng")
def _tong_bill():
	ud = json.dumps({"loai": "ma", "ma": "VC-8K2Q", "ten": "Giảm 10%", "giam": 18500, "sdt": SDT})

	def gv(dt, ten, f=None, **k):
		if f == "vgb_ud_ban":
			return ud
		return _fr._dict(grand_total=166500)
	with patch.object(_fr.db, "get_value", side_effect=gv):
		b = goi_mon_ban._tong_bill("ACC-SINV-0001")
	la("tổng và ưu đãi", (b["tong"], b["ud"]["giam"]), (166500, 18500))

	def thieu_cot(dt, ten, f=None, **k):
		if f == "vgb_ud_ban":
			raise Exception("Unknown column 'vgb_ud_ban'")
		return _fr._dict(grand_total=185000)
	with patch.object(_fr.db, "get_value", side_effect=thieu_cot):
		b = goi_mon_ban._tong_bill("ACC-SINV-0001")
	la("thiếu cột vẫn có tổng", (b["tong"], "ud" in b), (185000, False))


@ca("Codex PR #546 vòng 1: mã trong Ví quà của chương trình cần OTP quản lý không dùng được tại bàn (danh sách mờ kèm lý do, chọn bị chặn, đã chọn thì lúc chốt và lúc gọi thêm giảm 0)")
def _codex546_otp():
	si = _hd()
	with _ban(si), patch.object(u, "_vi", side_effect=lambda kh: list(VI_OTP)):
		r = u.ds("TCV", 5, "k")
		x = next(y for y in r["ds"] if y["ma"] == "VC-OTP")
		c = u.chon("TCV", 5, "k", "ma", "VC-OTP")
	la("danh sách: không dùng được, có lý do", (x["dung_duoc"], x["giam"], "quản lý" in x["ly_do"]), (0, 0, True))
	la("chọn bị chặn, hoá đơn không đổi", (c["ok"], si.luu, si.discount_amount), (0, 0, 0))
	# Bàn đã mang ưu đãi đó từ trước (dữ liệu cũ): gọi thêm và lúc chốt đều về 0, không ghi lượt.
	si2 = _hd(discount_amount=55500, vgb_giam_ud=55500, vgb_ud_ban=json.dumps({"loai": "ma", "ma": "VC-OTP", "sdt": SDT, "khach": KHACH, "giam": 55500}))
	with _ban(si2):
		u.tinh_lai(si2)
	la("gọi thêm: về 0", si2.vgb_giam_ud, 0.0)
	si3 = _hd(discount_amount=55500, vgb_giam_ud=55500, vgb_ud_ban=json.dumps({"loai": "ma", "ma": "VC-OTP", "sdt": SDT, "khach": KHACH, "giam": 55500}))
	with _ban(si3), patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		nem("lúc chốt dừng, số về 0", lambda: u.truoc_chot(si3), u.UuDaiDoi)
	la("đã lưu số 0", (si3.vgb_giam_ud, si3.discount_amount), (0.0, 0.0))


@ca("Codex PR #546 vòng 1: phần giảm khác đã gần hết bill, ưu đãi bị kẹp còn 5.000 đ: chốt KHÔNG dừng mãi, ghi lượt theo số thật đã trừ")
def _codex546_kep():
	si = _hd(discount_amount=180000)
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	la("kẹp còn 5.000 đ", si.vgb_giam_ud, 5000.0)
	with _ban(si), patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		try:
			kq = u.truoc_chot(si)
			dung_lai = False
		except u.UuDaiDoi:
			kq, dung_lai = None, True
	la("không dừng chốt", dung_lai, False)
	la("lượt ghi theo số thật đã trừ", [a["giam"] for a in (kq or {}).get("ap") or [] if a.get("loai") != "hang"], [5000])


@ca("Codex PR #546 vòng 2: thu ngân chốt kèm giảm tay mới (180.000 đ về 0): ưu đãi tính theo giảm tay MỚI (18.500 đ, thu 166.500 đ), lượt ghi 18.500 đ, không dừng chốt")
def _codex546_giam_tay_moi():
	from vagabond import khuyen_mai

	bh = _nap_pos_chot()
	si = _hd(discount_amount=180000)
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	la("trước chốt: kẹp 5.000 đ", si.vgb_giam_ud, 5000.0)
	ghi = []
	with _ban(si), patch.object(bh, "_pos_lay", return_value=si), \
			patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda kq, ten, **k: ghi.append(kq)), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, ten, f, v, **k: si.__setitem__(f, v)), \
			patch.object(quyen_quay, "muc", return_value="duyet"), patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		r = bh.pos_chot(si.name, giam_gia=0)
	la("thu 166.500 đ, ưu đãi 18.500 đ", (r["grand_total"], si.vgb_giam_ud, si.discount_amount), (166500.0, 18500.0, 18500.0))
	la("lượt ghi theo 18.500 đ", [a["giam"] for a in ghi[0]["ap"]], [18500])


@ca("Codex PR #546 vòng 2: mã Ví quà bị huỷ, hết hạn, dùng nơi khác lúc chốt (khuyen_mai ném lỗi): lần đầu lưu 0 kèm lý do và dừng báo thu ngân, lần sau chốt được, không ghi lượt")
def _codex546_ma_huy():
	from vagabond import khuyen_mai

	bh = _nap_pos_chot()
	si = _hd()
	with _ban(si):
		u.chon("TCV", 5, "k", "ma", "VC-8K2Q")
	la("trước: 18.500 đ", si.vgb_giam_ud, 18500.0)

	def huy(items, **k):
		raise _fr.ValidationError("Mã VC-8K2Q đã huỷ.")
	ghi = []
	with _ban(si), patch.object(bh, "_pos_lay", return_value=si), patch.object(khuyen_mai, "tinh_co_khoa", side_effect=huy), \
			patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda *a, **k: ghi.append(a)), \
			patch.object(quyen_quay, "muc", return_value="duyet"), patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		nem("lần đầu dừng báo thu ngân", lambda: bh.pos_chot(si.name), u.UuDaiDoi)
		la("đã lưu 0 kèm lý do", (si.vgb_giam_ud, si.discount_amount, "đã huỷ" in json.loads(si.vgb_ud_ban).get("ly_do", "")), (0.0, 0.0, True))
		r = bh.pos_chot(si.name)
	la("lần sau chốt được đủ tiền, không ghi lượt", (r["grand_total"], si.vgb_tam_tinh, ghi), (185000.0, 0, []))
	# Đã ở 0 (chưa đủ điều kiện) mà mã bị huỷ: chốt không dừng, lý do trên bill đổi theo.
	si2 = _hd(vgb_ud_ban=json.dumps({"loai": "ma", "ma": "VC-8K2Q", "sdt": SDT, "khach": KHACH, "giam": 0, "ly_do": "hoá đơn chưa đủ 150.000 đ"}))
	with _ban(si2), patch.object(bh, "_pos_lay", return_value=si2), patch.object(khuyen_mai, "tinh_co_khoa", side_effect=huy), \
			patch.object(quyen_quay, "muc", return_value="duyet"), patch.object(_fr, "throw", side_effect=_nem_dung_lop):
		bh.pos_chot(si2.name)
	la("lý do đổi theo, bill chốt", ("đã huỷ" in json.loads(si2.vgb_ud_ban)["ly_do"], si2.vgb_tam_tinh), (True, 0))
