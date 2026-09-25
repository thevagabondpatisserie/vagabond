# -*- coding: utf-8 -*-
"""v528: khoản trả tiện ích qua app ngân hàng không mang mã APP (anh Việt 25/09/2026).

Ca thật trên site: hồ sơ APP.26.09.100 (Cấp nước Bến Thành, 1.144.382 đ, chi
TK công ty MB) trả bằng tính năng thanh toán hoá đơn của app MB. Sao kê về
ACC-BTN-2026-06151 ngày 22/09 với nội dung "WATER BT WATER 1032865688
e0Vh5pp20ek.BP1", không có chữ APP nào. Nút Dò SePay báo "Ngân hàng đã chi
0 / 1.144.382 đ. Chưa thấy giao dịch nào mang mã APP.26.09.100", còn ô tìm
của màn khớp tay chỉ so chữ nên gõ số tiền không ra dòng nào.

Ba phần sửa, ca kiểm theo từng phần:
  A. Dò SePay đưa dòng đúng tiền, đúng tài khoản, chưa ai dùng để người bấm
     Khớp. Máy KHÔNG tự gán theo số tiền.
  B. Nhớ MẪU ĐẦU DÒNG sao kê theo nhà cung cấp ("WATER BT WATER"), không nhớ
     dãy số vì dãy số đổi mỗi lần trả (APP.26.09.101 cùng ngày mang
     1032865615). Lần sau: mẫu + đúng tiền + đúng tài khoản + chỉ một dòng
     chưa ai dùng thì máy tự khớp.
  C. Ô tìm nhận số tiền.

Ca kiểm chạy hàm THẬT với frappe giả tôn trọng bộ lọc (điều 17a), và màn
THẬT nạp vào node. Không gọi thêm hàm nào ngoài chuỗi thao tác (điều 15).
"""

import json
import unittest.mock
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_tra_truoc_528 import KHUNG_JS, _node


class _D(dict):
	"""Như frappe._dict: đọc và GHI thuộc tính đều vào khoá."""
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


APP = "APP.26.09.100"
NCC = "CAP-NUOC-BT"
TIEN = 1144382.0
MO_TA_BT = "WATER BT WATER 1032865688 e0Vh5pp20ek.BP1 "
MO_TA_TH = "WATER TH WATER 1032865615 faILoefoMwM.BP1 "


# ------------------------------------------------------------------ thuần


@ca("v528 tiện ích: bóc mẫu đầu dòng đúng trên nội dung sao kê thật, bỏ lệnh chuyển tay")
def _mau():
	from vagabond.khop_sao_ke import mau_sao_ke
	for mo_ta, mau in ((MO_TA_BT, "WATER BT WATER"), (MO_TA_TH, "WATER TH WATER"),
			("EVN-HCM ELECTRIC bvoL7t5kJkS", "EVN-HCM ELECTRIC"), ("PAYOO WATER gZejDwFh5QU", "PAYOO WATER"),
			("VAGABOND APP.26.09.102 THANH TOAN TONG CONG TY", ""), ("MBCT VAGABOND TT DH 0630 KAMEREO", ""),
			("Thanh toan QR-090926-10:32:59", ""), ("2221", ""), ("KH TT TAI CH 303", ""),
			("VGB SEP00049382 APP2609097 SEPAY", ""), ("", ""), (None, "")):
		la(repr(mo_ta), mau_sao_ke(mo_ta), mau)


@ca("v528 tiện ích: khớp mẫu trọn chữ ở đầu dòng, mẫu dài thắng; ô nhớ đọc mỗi dòng một mẫu")
def _khop_mau():
	from vagabond.khop_sao_ke import doc_ds_mau, khop_mau
	la("khớp", khop_mau(MO_TA_BT, ["WATER BT WATER"]), "WATER BT WATER")
	la("khác nhà nước", khop_mau(MO_TA_TH, ["WATER BT WATER"]), "")
	la("không khớp nửa chữ", khop_mau("WATER BTX 1", ["WATER BT"]), "")
	la("không khớp giữa dòng", khop_mau("PAYOO WATER BT WATER x", ["WATER BT WATER"]), "")
	la("mẫu dài thắng", khop_mau(MO_TA_BT, ["WATER BT", "WATER BT WATER"]), "WATER BT WATER")
	la("đọc ô nhớ", doc_ds_mau(" water bt  water\n\nEVN-HCM ELECTRIC\nWATER BT WATER"), ["WATER BT WATER", "EVN-HCM ELECTRIC"])


@ca("v528 tiện ích: ô tìm nhận số tiền mọi kiểu gõ, chữ vẫn tìm như cũ")
def _tu_khoa():
	from vagabond.khop_sao_ke import khop_tu_khoa
	d = {"name": "ACC-BTN-2026-06151", "mo_ta": MO_TA_BT + " FT26265054275377", "tien": TIEN}
	for tk in ("1.144.382", "1,144,382", "1144382", "1.144.382 đ", "1144382d", "water bt", "FT2626505", "06151", ""):
		dung("tìm " + repr(tk), khop_tu_khoa(tk, d))
	for tk in ("1.144.383", "114", "nước"):
		dung("không ra " + repr(tk), not khop_tu_khoa(tk, d))


@ca("v528 tiện ích: gợi ý xếp mẫu đã nhớ trước, rồi ngày gần ngày lập")
def _xep():
	from vagabond.khop_sao_ke import xep_goi_y
	ds = [{"name": "A", "date": "2026-09-30", "da_nho": 0}, {"name": "B", "date": "2026-09-23", "da_nho": 0},
		{"name": "C", "date": "2026-08-20", "da_nho": 1}, {"name": "D", "date": "", "da_nho": 0}]
	la("thứ tự", [r["name"] for r in xep_goi_y(ds, "2026-09-22")], ["C", "B", "A", "D"])


# ------------------------------------------------------- máy chủ, hàm thật

def _bt(name, date, mo_ta, tien=TIEN, tk="MB-CTY", ref="FT26265054275377"):
	return _D(name=name, date=date, description=mo_ta, reference_number=ref, withdrawal=tien,
		deposit=0, bank_account=tk, docstatus=1, flags=_D())


class _San:
	"""frappe giả cho doi_chieu_app. Bộ lọc được TÔN TRỌNG, không trả bừa."""

	def __init__(self, bts, mau=None, dung_roi=(), ma_gd="", ncc=NCC):
		self.bts = {b.name: b for b in bts}
		self.mau = dict(mau or {})
		self.dung_roi = set(dung_roi)
		self.nhat_ky = []
		self.doc = _D(name=APP, ngay="2026-09-22", nha_cung_cap=ncc, ten_ncc="Cấp nước Bến Thành",
			ma_giao_dich=ma_gd, trang_thai="Da duyet")
		self.doc.save = lambda **k: None
		self.doc.add_comment = lambda loai, noi: self.nhat_ky.append((APP, noi))
		import frappe as _fr
		from vagabond import doi_chieu_app as dca
		self.dca = dca
		self.f = NS(get_all=self.get_all, get_doc=self.get_doc, get_meta=lambda dt: NS(has_field=lambda o: o == dca.O_MAU),
			throw=_fr.throw, QueryDeadlockError=type("QDE", (Exception,), {}),
			db=NS(get_value=self.get_value, exists=lambda dt, ten: ten in self.bts, set_value=self.set_value))

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		filters = filters or {}
		if dt == "Bank Account":
			ra = [_D(name="MB-CTY")]
		elif dt == "Bank Transaction":
			ra = list(self.bts.values())
			if "bank_account" in filters:
				ra = [b for b in ra if b.bank_account in filters["bank_account"][1]]
			if "withdrawal" in filters:
				ra = [b for b in ra if abs(b.withdrawal - filters["withdrawal"]) < 0.001]
			if "date" in filters:
				ra = [b for b in ra if b.date >= filters["date"][1]]
			if "reference_number" in filters:
				ra = [b for b in ra if b.reference_number == filters["reference_number"]]
			ra.sort(key=lambda b: (b.date, b.name), reverse=True)
		elif dt == "Supplier":
			tk = filters[self.dca.O_MAU][1].strip("%")
			ra = [_D(name=n, **{self.dca.O_MAU: m}) for n, m in self.mau.items()
				if tk in (m or "") and n != filters["name"][1]]
		else:
			raise AssertionError("get_all lạ: " + dt)
		return [r.name for r in ra] if pluck else ra

	def get_doc(self, dt, ten=None, for_update=False):
		if dt == "Bank Transaction":
			return self.bts[ten]
		if dt == "Supplier":
			return NS(add_comment=lambda loai, noi: self.nhat_ky.append((ten, noi)))
		raise AssertionError("get_doc lạ: " + dt)

	def get_value(self, dt, ten, o, for_update=False, **k):
		if dt == "Supplier":
			return ten if o == "name" else self.mau.get(ten)
		if dt == "Bank Transaction":
			return ten
		raise AssertionError("get_value lạ: " + dt)

	def set_value(self, dt, ten, o, gt, **k):
		assert dt == "Supplier" and o == self.dca.O_MAU
		self.mau[ten] = gt

	def chay(self, ham):
		dca = self.dca
		kiem = lambda g, doc, nguon: ("Giao dịch đã được APP.26.09.050 sử dụng." if g.name in self.dung_roi else "")
		with unittest.mock.patch.object(dca, "frappe", self.f), \
				unittest.mock.patch.object(dca, "_nguon", lambda doc: ("VGB", "1121 - MB", TIEN)), \
				unittest.mock.patch.object(dca, "_kiem", kiem), \
				unittest.mock.patch.object(dca, "_ho_so", lambda name, khoa=False: self.doc), \
				unittest.mock.patch.object(dca, "nowdate", lambda: "2026-09-25"):
			try:
				return ham(dca)
			except Exception as e:
				return {"loi": str(e)}


G_BT = _bt("ACC-BTN-2026-06151", "2026-09-22", MO_TA_BT)
G_TH = _bt("ACC-BTN-2026-06150", "2026-09-22", MO_TA_TH, tien=2022368.0)


@ca("v528 tiện ích (hàm thật): chưa nhớ mẫu thì máy không tự khớp; nhớ rồi thì khớp đúng dòng Bến Thành và ghi cờ theo mẫu")
def _chon_mau():
	s = _San([G_BT, G_TH])
	la("chưa nhớ: không tự khớp (đúng như ca thật)", s.chay(lambda d: d.chon(s.doc)), None)
	s = _San([G_BT, G_TH], mau={NCC: "WATER BT WATER"})
	g = s.chay(lambda d: d.chon(s.doc))
	la("nhớ rồi: khớp 06151", getattr(g, "name", g), "ACC-BTN-2026-06151")
	la("cờ theo mẫu", g.flags.get("theo_mau"), True)
	s = _San([G_BT, G_TH], mau={NCC: "WATER TH WATER"})
	la("mẫu của Tân Hoà không kéo dòng Bến Thành", s.chay(lambda d: d.chon(s.doc)), None)


@ca("v528 tiện ích (hàm thật): mẫu khớp hai dòng dùng được thì không đoán; một dòng đã có chủ thì lấy dòng còn lại; ngoài khoảng ngày thì thôi")
def _chon_mo_ho():
	hai = _bt("ACC-BTN-2026-06999", "2026-09-23", "WATER BT WATER 1032869999 xYz.BP1", ref="FT2")
	s = _San([G_BT, hai], mau={NCC: "WATER BT WATER"})
	la("hai dòng: không tự khớp, không ném lỗi", s.chay(lambda d: d.chon(s.doc)), None)
	s = _San([G_BT, hai], mau={NCC: "WATER BT WATER"}, dung_roi={"ACC-BTN-2026-06999"})
	la("một dòng đã có chủ: lấy dòng kia", getattr(s.chay(lambda d: d.chon(s.doc)), "name", None), "ACC-BTN-2026-06151")
	cu = _bt("ACC-BTN-2026-00001", "2026-07-01", MO_TA_BT)
	s = _San([cu], mau={NCC: "WATER BT WATER"})
	la("trước ngày lập quá 45 ngày: không", s.chay(lambda d: d.chon(s.doc)), None)
	co_ma = _bt("ACC-BTN-2026-07000", "2026-09-23", "VAGABOND APP.26.09.100 THANH TOAN NUOC", ref="FT3")
	s = _San([G_BT, co_ma], mau={NCC: "WATER BT WATER"})
	g = s.chay(lambda d: d.chon(s.doc))
	la("dòng mang mã APP vẫn thắng, không phải theo mẫu", (getattr(g, "name", g), g.flags.get("theo_mau")), ("ACC-BTN-2026-07000", False))


@ca("v528 tiện ích (hàm thật): gợi ý chỉ dòng đúng tiền, đúng tài khoản, chưa ai dùng, trong khoảng ngày; kèm mẫu bóc được")
def _goi_y():
	dung_roi = _bt("ACC-BTN-2026-06200", "2026-09-24", "WATER BT WATER 1 a.BP1", ref="FT4")
	cu = _bt("ACC-BTN-2026-00002", "2026-06-01", MO_TA_BT, ref="FT5")
	tk_khac = _bt("ACC-BTN-2026-06300", "2026-09-22", MO_TA_BT, tk="OCB", ref="FT6")
	s = _San([G_BT, G_TH, dung_roi, cu, tk_khac], dung_roi={"ACC-BTN-2026-06200"})
	ds = s.chay(lambda d: d.goi_y_khong_ma(s.doc))
	la("chỉ 06151", [r["name"] for r in ds], ["ACC-BTN-2026-06151"])
	la("mẫu, chưa nhớ, nội dung", (ds[0]["mau"], ds[0]["da_nho"], ds[0]["mo_ta"]),
		("WATER BT WATER", 0, MO_TA_BT.strip()))
	xa = _bt("ACC-BTN-2026-05000", "2026-08-20", "WATER BT WATER 9 q.BP1", ref="FT7")
	gan = _bt("ACC-BTN-2026-06152", "2026-09-22", "PAYOO WATER abc", ref="FT8")
	s = _San([xa, gan], mau={NCC: "WATER BT WATER"})
	la("mẫu đã nhớ lên trước dù xa ngày hơn", [r["name"] for r in s.chay(lambda d: d.goi_y_khong_ma(s.doc))],
		["ACC-BTN-2026-05000", "ACC-BTN-2026-06152"])


@ca("v528 tiện ích (hàm thật): gán tay dòng không mang mã thì đề nghị nhớ mẫu; các ca không nên nhớ thì không đề nghị")
def _de_nghi():
	s = _San([G_BT], ma_gd="")
	kq = s.chay(lambda d: d.gan(APP, "ACC-BTN-2026-06151"))
	la("gán xong có đề nghị", kq.get("nho_mau"), {"mau": "WATER BT WATER", "ncc": NCC, "ten_ncc": "Cấp nước Bến Thành"})
	dung("vẫn ghi nhật ký gán tay", any("Đối chiếu tay" in n for _, n in s.nhat_ky))
	for mo_ta, kw, g in (
			# Mã APP nằm ở ô tham chiếu, nội dung vẫn bóc được mẫu: chỉ lớp
			# "có mã thì không đề nghị" chặn được ca này (đột biến M7, điều 17c:
			# nội dung "VAGABOND APP..." thì lớp chữ chung đã chặn thay).
			("dòng có mã APP", {}, _bt("X1", "2026-09-22", MO_TA_BT, ref="APP.26.09.100")),
			("đã nhớ rồi", {"mau": {NCC: "WATER BT WATER"}}, G_BT),
			("NCC khác giữ mẫu", {"mau": {"CAP-NUOC-KHAC": "WATER BT WATER"}}, G_BT),
			("hồ sơ không có NCC", {"ncc": None}, G_BT),
			("lệnh chuyển tay", {}, _bt("X2", "2026-09-22", "MBCT VAGABOND TT NUOC D2/1"))):
		s = _San([g], **kw)
		la(mo_ta + ": không đề nghị", s.chay(lambda d: d.de_nghi_nho_mau(s.doc, g)), None)


@ca("v528 tiện ích (hàm thật): nhớ mẫu ghi đúng NCC, giữ mẫu cũ, có nhật ký; mẫu gõ tay, mẫu trùng NCC khác, hồ sơ chưa gán đều chặn")
def _nho():
	s = _San([G_BT], mau={NCC: "EVN-HCM ELECTRIC"}, ma_gd="ACC-BTN-2026-06151")
	kq = s.chay(lambda d: d.nho_mau(APP, "water bt  water"))
	la("trả ok", kq.get("ok"), 1)
	la("ô nhớ giữ mẫu cũ, thêm mẫu mới", s.mau[NCC], "EVN-HCM ELECTRIC\nWATER BT WATER")
	la("nhật ký hai phía", sorted(t for t, _ in s.nhat_ky), [APP, NCC])
	for mo_ta, kw, mau, chu in (
			("mẫu gõ tay", {}, "THANH TOAN", "không khớp"),
			("NCC khác giữ", {"mau": {"CAP-NUOC-TH": "WATER BT WATER"}}, "WATER BT WATER", "CAP-NUOC-TH"),
			("chưa gán giao dịch", {"ma_gd": ""}, "WATER BT WATER", "chưa gán")):
		s = _San([G_BT], **dict({"ma_gd": "ACC-BTN-2026-06151"}, **kw))
		cu = dict(s.mau)
		kq = s.chay(lambda d: d.nho_mau(APP, mau))
		dung(mo_ta + ": chặn có lời", chu in kq.get("loi", ""))
		la(mo_ta + ": không ghi", s.mau, cu)


@ca("v528 tiện ích (hàm thật): ô tìm màn khớp tay gõ 1.144.382 ra đúng dòng Bến Thành (trước đó 0 dòng)")
def _tim_that():
	from vagabond import doi_soat_sepay as dss
	gds = [dict(name=b.name, date=b.date, description=b.description, reference_number=b.reference_number,
		bank_account="MB-CTY", mo_ta="%s %s" % (b.description, b.reference_number), tien=b.withdrawal)
		for b in (G_BT, G_TH)]
	with unittest.mock.patch.object(dss, "dong_sao_ke", lambda *a, **k: [dict(g) for g in gds]), \
			unittest.mock.patch.object(dss, "nhan_tai_khoan", lambda: ({}, [{"ma": "MB-CTY"}], None)), \
			unittest.mock.patch.object(dss, "ly_do_tai_khoan_sepay", lambda *a: ""), \
			unittest.mock.patch("frappe.utils.nowdate", lambda: "2026-09-25", create=True), \
			unittest.mock.patch("frappe.utils.add_days", lambda d, n: d, create=True):
		for tk, mong in (("1.144.382", ["ACC-BTN-2026-06151"]), ("2022368", ["ACC-BTN-2026-06150"]),
				("water bt", ["ACC-BTN-2026-06151"]), ("1.144.383", [])):
			kq = dss.danh_sach_chon(dss.RA, APP, TIEN, 120, tk)
			la("tìm " + tk, [r["name"] for r in kq["rows"]], mong)


@ca("v528 tiện ích (hàm thật): Dò SePay một hồ sơ chưa khớp thì kèm gợi ý; dò cả loạt thì không gọi gợi ý")
def _kiem_sepay():
	import frappe
	from vagabond import ho_so_tt as hs
	goi = []
	dong = {"name": APP, "tong_tien": TIEN, "con_lai": TIEN, "trang_thai": "Da duyet"}
	with unittest.mock.patch.object(frappe.db, "get_value", lambda *a, **k: dict(dong), create=True), \
			unittest.mock.patch.object(frappe, "get_all", lambda *a, **k: [dict(dong)], create=True), \
			unittest.mock.patch.object(frappe, "get_doc", lambda *a, **k: _D(name=APP), create=True), \
			unittest.mock.patch.object(hs, "_kiem", lambda *a, **k: None), \
			unittest.mock.patch("vagabond.doi_chieu_app.chon", return_value=None), \
			unittest.mock.patch("vagabond.doi_chieu_app.goi_y_khong_ma", lambda doc: goi.append(doc.name) or [{"name": "ACC-BTN-2026-06151"}]):
		r = hs.kiem_sepay(APP)["rows"][0]
		la("một hồ sơ: có gợi ý", (r["so_gd"], r["goi_y"]), (0, [{"name": "ACC-BTN-2026-06151"}]))
		r = hs.kiem_sepay()["rows"][0]
		la("cả loạt: không gợi ý", (r["goi_y"], goi), ([], [APP]))
		dong["trang_thai"] = "Da thanh toan"
		la("hồ sơ đã trả: không gợi ý", hs.kiem_sepay(APP)["rows"][0]["goi_y"], [])


# ------------------------------------------------------------- màn thật


GOI_Y = {"name": "ACC-BTN-2026-06151", "date": "2026-09-22", "mo_ta": MO_TA_BT.strip(), "tham_chieu": "FT26265054275377",
	"tien": TIEN, "mau": "WATER BT WATER", "da_nho": 0}
DE_NGHI = {"mau": "WATER BT WATER", "ncc": NCC, "ten_ncc": "Cấp nước Bến Thành"}


def _do_sepay(sepay, tra_loi=(True, True), nho=DE_NGHI):
	them = r"""
const hoi = [];
ctx.hoiCo = async function (t, m, ok) { hoi.push([t, m, ok]); return TL.length ? TL.shift() : false; };
(async function () {
  await ctx.scrHoSoTTView('APP.26.09.100');
  const nut = { getAttribute: function () { return 'sepay'; } };
  await khung.nghe({ target: { closest: function (s) { return s === '[data-hsv]' ? nut : null; } } });
  process.stdout.write(JSON.stringify({ api: ghi.api, go: ghi.go.length, bao: ghi.bao, hoi: hoi }));
})().catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
"""
	d = {"ho_so": {"ma": APP, "loai": "TK cong ty", "trang_thai": "Da duyet", "tong_tien": TIEN, "con_lai": TIEN,
		"ten_ncc": "Cấp nước Bến Thành", "ngay": "2026-09-22"}, "quyen": {"fin": 1},
		"dong": [{"noi_dung": "Tiền nước", "so_tien": TIEN, "hoa_don": None, "po": [], "pnk": [], "scan": [], "hddt": []}]}
	tra = ("(m === 'vagabond.ho_so_tt.chi_tiet' ? D : (m === 'vagabond.ho_so_tt.kiem_sepay' ? SK : "
		"(m === 'vagabond.doi_chieu_app.gan' ? { ok: 1, loi_nhan: 'Đã chọn giao dịch.', nho_mau: NHO } : { ok: 1, loi_nhan: 'ok' })))")
	kich = KHUNG_JS.replace("__THEM__", them).replace("TRA(m, a || {})", tra)
	kich = kich.replace("const vm = require('vm');", "const vm = require('vm'); const D = %s; const SK = %s; const NHO = %s; const TL = %s; const VAI = []; const CHON = null; const TDK = [];" % (
		json.dumps(d), json.dumps({"rows": [sepay]}), json.dumps(nho), json.dumps(list(tra_loi))))
	return _node(kich, ["19-ho-so-tt.js"])


def _goi(ra, m):
	return [a for mm, a in ra["api"] if mm == m]


SK_0 = {"ma": APP, "tong_tien": TIEN, "phai_chuyen": TIEN, "da_chi": 0, "so_gd": 0, "du": 0, "theo_mau": 0}


@ca("v528 tiện ích (màn thật): APP.26.09.100 bấm Dò SePay thấy dòng WATER BT, bấm Khớp thì gán đúng dòng, rồi hỏi nhớ mẫu và nhớ đúng mẫu")
def _man_khop():
	ra = _do_sepay(dict(SK_0, goi_y=[GOI_Y]))
	la("hỏi hai lần: khớp rồi nhớ", [h[0] for h in ra["hoi"]], ["Khớp giao dịch này?", "Nhớ mẫu sao kê?"])
	dung("lần hỏi đầu cho thấy nội dung sao kê và số tiền", "WATER BT WATER 1032865688" in ra["hoi"][0][1]
		and "1.144.382" in ra["hoi"][0][1] and "22/09" in ra["hoi"][0][1])
	la("gán đúng dòng", _goi(ra, "vagabond.doi_chieu_app.gan"), [{"name": APP, "ma_giao_dich": "ACC-BTN-2026-06151"}])
	la("nhớ đúng mẫu", _goi(ra, "vagabond.doi_chieu_app.nho_mau"), [{"name": APP, "mau": "WATER BT WATER"}])
	la("mở lại hồ sơ", ra["go"], 1)
	la("không còn bảng báo cũ", ra["bao"], [])


@ca("v528 tiện ích (màn thật): bấm Thôi thì không gán; không nhớ thì chỉ gán; máy không đề nghị thì không hỏi nhớ")
def _man_thoi():
	ra = _do_sepay(dict(SK_0, goi_y=[GOI_Y]), tra_loi=(False,))
	la("Thôi: không gán, không nhớ", (_goi(ra, "vagabond.doi_chieu_app.gan"), _goi(ra, "vagabond.doi_chieu_app.nho_mau"), ra["go"]), ([], [], 0))
	ra = _do_sepay(dict(SK_0, goi_y=[GOI_Y]), tra_loi=(True, False))
	la("khớp mà không nhớ", (len(_goi(ra, "vagabond.doi_chieu_app.gan")), _goi(ra, "vagabond.doi_chieu_app.nho_mau")), (1, []))
	ra = _do_sepay(dict(SK_0, goi_y=[GOI_Y]), tra_loi=(True,), nho=None)
	la("không có đề nghị: hỏi đúng một lần", [h[0] for h in ra["hoi"]], ["Khớp giao dịch này?"])


@ca("v528 tiện ích (màn thật): nhiều dòng đúng tiền thì mở danh sách chứ không gán; không có dòng nào thì chỉ cách tìm theo số tiền; khớp theo mẫu thì nói rõ")
def _man_khac():
	ra = _do_sepay(dict(SK_0, goi_y=[GOI_Y, dict(GOI_Y, name="ACC-BTN-2026-06999")]), tra_loi=(True,))
	la("nút xem hai dòng", ra["hoi"][0][2], "Xem 2 dòng")
	la("không gán, mở danh sách", (_goi(ra, "vagabond.doi_chieu_app.gan"), ra["go"]), ([], 1))
	ra = _do_sepay(dict(SK_0, goi_y=[]))
	dung("không dòng nào: chỉ cách", len(ra["bao"]) == 1 and "Chưa thấy giao dịch nào mang mã APP.26.09.100" in ra["bao"][0]
		and "tìm theo số tiền" in ra["bao"][0])
	ra = _do_sepay(dict(SK_0, da_chi=TIEN, so_gd=1, ma_gd="ACC-BTN-2026-06151", du=1, theo_mau=1, goi_y=[]))
	dung("khớp theo mẫu: báo đủ và nói theo mẫu", "mẫu sao kê đã nhớ" in ra["bao"][0] and "Đã đủ tiền" in ra["bao"][0])


def _khop_tay(nho=DE_NGHI, tra_loi=(True,)):
	them = r"""
const hoi = []; let o = null;
ctx.hoiCo = async function (t, m, ok) { hoi.push([t, m, ok]); return TL.length ? TL.shift() : false; };
ctx.confirmSheet = async function () { return true; };
ctx.scrKhopSepay = function (x) { o = x; };
ctx.scrHoSoTTView = function () {};
(async function () {
  await ctx.scrTimGiaoDich('APP.26.09.100', 1144382);
  await o.chon('ACC-BTN-2026-06151', 1144382);
  process.stdout.write(JSON.stringify({ loai: o.loai, api: ghi.api, go: ghi.go.length, hoi: hoi }));
})().catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
"""
	tra = "(m === 'vagabond.doi_chieu_app.gan' ? { ok: 1, loi_nhan: 'Đã chọn giao dịch.', nho_mau: NHO } : { ok: 1, loi_nhan: 'ok' })"
	kich = KHUNG_JS.replace("__THEM__", them).replace("TRA(m, a || {})", tra)
	kich = kich.replace("const vm = require('vm');", "const vm = require('vm'); const NHO = %s; const TL = %s; const VAI = []; const CHON = null; const TDK = [];" % (
		json.dumps(nho), json.dumps(list(tra_loi))))
	return _node(kich, ["19-ho-so-tt.js", "21-ke-toan-khac.js"])


@ca("v528 tiện ích (màn thật): khớp tay từ màn tìm sao kê cũng hỏi nhớ mẫu sau khi gán, và nhớ đúng mẫu")
def _man_khop_tay():
	ra = _khop_tay()
	la("màn chọn là loại app", ra["loai"], "app")
	la("gán rồi nhớ", [m for m, a in ra["api"]], ["vagabond.doi_chieu_app.gan", "vagabond.doi_chieu_app.nho_mau"])
	la("nhớ đúng mẫu", ra["api"][1][1], {"name": APP, "mau": "WATER BT WATER"})
	ra = _khop_tay(nho=None)
	la("không đề nghị: chỉ gán, không hỏi", ([m for m, a in ra["api"]], ra["hoi"]), (["vagabond.doi_chieu_app.gan"], []))
