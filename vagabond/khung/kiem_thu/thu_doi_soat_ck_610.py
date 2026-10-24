# -*- coding: utf-8 -*-
"""v610: đối soát tay tiền chuyển khoản vào thẳng tài khoản chính công ty.

Ca gốc (anh Việt 24/10/2026, Dễ báo): bill TCVEHQHG, HDB-26-10-04707, ngày
23/10, 1.875.000 đ. Khách chuyển thẳng vào MB 31561568. SePay có ghi dòng
ACC-BTN-2026-08831 lúc 13:27, nội dung không mang dấu tài khoản ảo nào, nên
nút Dò tiền (chỉ soi tài khoản ảo của điểm) không bao giờ hiện dòng đó.

Mọi ca dưới đây chạy THẬT các phép của doi_soat_ck với đúng nội dung sao kê
đọc trên site, không dò chuỗi mã nguồn, trừ ca chốt hai bản danh sách vai.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _dsck():
	from vagabond import doi_soat_ck
	return doi_soat_ck


# Cấu hình tài khoản như trên site (bốn tài khoản ảo mở 12/08/2026).
CAU_HINH = {
	"mac_dinh": {"bank": "MB", "stk": "VQRQ00033k5p6", "ten": "PATISSERIE VAGABOND COMPANY LIMITED"},
	"theo_nguon": [
		{"nguon": "Khách sỉ", "bank": "MB", "stk": "VQRQALEAL8702", "dung": 1},
		{"nguon": "@diem:SALES", "bank": "MB", "stk": "VQRQALEAI2626", "dung": 1},
		{"nguon": "@diem:NVHTN", "bank": "MB", "stk": "VQRQALEAI0938", "dung": 1},
		{"nguon": "@diem:TCV", "bank": "MB", "stk": "VQRQALEAF2999", "dung": 1},
		{"nguon": "@phieu_cong_no", "bank": "MB", "stk": "VQRQALEAL8702", "dung": 1},
		# Tài khoản thường: không để dấu trong nội dung, không vào bảng dấu.
		{"nguon": "Shopee", "bank": "MB", "stk": "31561568", "dung": 1},
	],
}
TEN = {"TCV": "Trần Cao Vân", "NVHTN": "NVHTN", "SALES": "Sales Online"}

# Nội dung thật của dòng ACC-BTN-2026-08831 (đã ghép ô tham chiếu).
MO_TA_CTY = "Nam transfers money quickly via Zalo FT26296252050942 k2AIB6G1/268370 FT26296028012585"
MO_TA_TCV = "QALEAF2999 VAGABOND TCV QR 30210 Ma GD ACSP/ AB123456 FT26296000000001"
MO_TA_NVH = "QALEAI0938 VAGABOND NVH QR 11111 Ma GD ACSP/ CD654321 FT26296000000002"

# Một ngày sao kê mẫu: hai khoản 1.875.000 (một vào thẳng tài khoản chính,
# một vào điểm NVHTN), một khoản của TCV lệch tiền, một khoản tài khoản
# chính đã có chủ.
GDS = [
	{"ten": "BT-CTY", "tien": 1875000, "gio": "13:27", "mo_ta": MO_TA_CTY},
	{"ten": "BT-TCV", "tien": 245000, "gio": "13:40", "mo_ta": MO_TA_TCV},
	{"ten": "BT-NVH", "tien": 1875000, "gio": "13:30", "mo_ta": MO_TA_NVH},
	{"ten": "BT-CTY2", "tien": 1875000, "gio": "09:00", "mo_ta": "CONG TY ABC TRA NO HD 1234 FT26296000000003"},
]
QUAY = ["VGB - Nhân viên bán hàng"]
QLCH = ["VGB - Nhân viên bán hàng", "VGB - Quản lý cửa hàng"]
KE_TOAN = ["Accounts User"]


def _cung(a, b):
	return abs(float(a) - float(b)) <= 1


def _bang():
	d = _dsck()
	return d.bang_dau(CAU_HINH, TEN)


@ca("v610 bảng dấu: chỉ tài khoản ảo, nhãn đọc được, nguồn cụ thể thắng mặc định")
def _bang_dau():
	d = _dsck()
	b = _bang()
	dau = [x["dau"] for x in b]
	dung("có dấu điểm TCV (cắt VQR)", "QALEAF2999" in dau)
	dung("tài khoản thường 31561568 không vào bảng", "31561568" not in dau)
	la("dấu trùng (khách sỉ và phiếu đòi nợ) chỉ một dòng", dau.count("QALEAL8702"), 1)
	la("mặc định đứng cuối", b[-1]["khoa"], "@mac_dinh")
	nhan = {x["khoa"]: x["nhan"] for x in b}
	la("nhãn điểm dùng tên ngắn", nhan["@diem:TCV"], "Điểm Trần Cao Vân")
	la("dấu tài khoản thường rỗng", d.dau_tk("31561568"), "")


@ca("v610 ca TCVEHQHG: khoản vào thẳng tài khoản chính được nhận ra là tài khoản chính")
def _thuoc_tk():
	d = _dsck()
	la("dòng ACC-BTN-2026-08831", d.thuoc_tk(MO_TA_CTY, _bang()), ("", d.NHAN_CTY))
	la("dòng mang dấu TCV", d.thuoc_tk(MO_TA_TCV, _bang())[0], "@diem:TCV")
	la("dòng mang dấu NVHTN", d.thuoc_tk(MO_TA_NVH, _bang())[0], "@diem:NVHTN")


@ca("v610 chip tài khoản: điểm, tài khoản chính, tất cả; điểm chưa có tài khoản riêng giữ nếp cũ")
def _loc():
	d = _dsck()
	gds = [dict(g) for g in GDS]
	for g in gds:
		g["khoa_tk"], g["nhan_tk"] = d.thuoc_tk(g["mo_ta"], _bang())
	ten = lambda ds: sorted(g["ten"] for g in ds)
	la("chip điểm TCV", ten(d.loc_theo_nguon(gds, "diem", "@diem:TCV", 1)), ["BT-TCV"])
	la("chip tài khoản chính", ten(d.loc_theo_nguon(gds, "cty", "@diem:TCV", 1)), ["BT-CTY", "BT-CTY2"])
	la("chip tất cả", len(d.loc_theo_nguon(gds, "tat_ca", "@diem:TCV", 1)), 4)
	la("điểm chưa có tài khoản riêng: chip điểm hiện cả sao kê như trước",
		len(d.loc_theo_nguon(gds, "diem", "@diem:TCV", 0)), 4)
	la("chip lạ quay về chip điểm", ten(d.loc_theo_nguon(gds, "xyz", "@diem:TCV", 1)), ["BT-TCV"])


@ca("v610 quyền gắn: khoản ngoài tài khoản điểm chỉ quản lý cửa hàng và kế toán")
def _quyen():
	d = _dsck()
	la("thu ngân gắn khoản của điểm mình", d.duoc_gan("@diem:TCV", "@diem:TCV", 1, QUAY), True)
	la("thu ngân KHÔNG gắn khoản tài khoản chính", d.duoc_gan("", "@diem:TCV", 1, QUAY), False)
	la("thu ngân KHÔNG gắn khoản điểm khác", d.duoc_gan("@diem:NVHTN", "@diem:TCV", 1, QUAY), False)
	la("quản lý cửa hàng gắn khoản tài khoản chính", d.duoc_gan("", "@diem:TCV", 1, QLCH), True)
	la("kế toán gắn khoản tài khoản chính", d.duoc_gan("", "@diem:TCV", 1, KE_TOAN), True)
	la("điểm chưa có tài khoản riêng: giữ nếp cũ", d.duoc_gan("", "@diem:TCV", 0, QUAY), True)


@ca("v610 bảng dò tiền ca TCVEHQHG: điểm không có khoản đúng tiền thì mở thẳng chip tài khoản chính")
def _bang_do():
	d = _dsck()
	co_chu = {"BT-CTY2": "phiếu công nợ CN-0001"}
	kq = d.dung_bang_do_tien(GDS, _bang(), "@diem:TCV", 1, 1875000, co_chu, QLCH, "", _cung)
	la("máy tự mở chip tài khoản chính", kq["nguon"], "cty")
	la("đếm khoản đúng tiền theo chip", kq["so_khop_nguon"], {"diem": 0, "cty": 1, "tat_ca": 2})
	la("đếm dòng theo chip", kq["so_dong_nguon"], {"diem": 1, "cty": 2, "tat_ca": 4})
	la("khoản của bill đứng đầu", kq["gd"][0]["ten"], "BT-CTY")
	la("khoản đó đúng tiền", kq["gd"][0]["khop"], 1)
	la("quản lý được gắn", kq["gd"][0]["duoc_gan"], 1)
	la("khoản đã có chủ đứng cuối, không tính là khớp", (kq["gd"][-1]["ten"], kq["gd"][-1]["khop"]), ("BT-CTY2", 0))
	la("nói rõ ai đang giữ", kq["gd"][-1]["cua_bill"], "phiếu công nợ CN-0001")
	la("nhãn tài khoản", kq["gd"][0]["tk_nhan"], d.NHAN_CTY)
	q = d.dung_bang_do_tien(GDS, _bang(), "@diem:TCV", 1, 1875000, co_chu, QUAY, "cty", _cung)
	la("thu ngân thấy nhưng không được gắn", q["gd"][0]["duoc_gan"], 0)
	la("thu ngân không có cờ gắn ngoài", q["gan_ngoai"], 0)
	t = d.dung_bang_do_tien(GDS, _bang(), "@diem:TCV", 1, 245000, {}, QUAY, "", _cung)
	la("điểm có khoản đúng tiền thì giữ chip điểm như cũ", t["nguon"], "diem")
	la("người đã bấm chip thì giữ chip đó", d.dung_bang_do_tien(GDS, _bang(), "@diem:TCV", 1, 1875000, {}, QLCH, "tat_ca", _cung)["nguon"], "tat_ca")


@ca("v610 chủ đọc từ nội dung: mã bill khác, đã khớp Đối chiếu ngân hàng")
def _chu_noi_dung():
	d = _dsck()
	from vagabond import ma_bill
	gds = [
		{"ten": "A", "mo_ta": "CK TCVACDEF cam on"},
		{"ten": "B", "mo_ta": "CK TCVEHQHG"},
		{"ten": "C", "mo_ta": MO_TA_CTY, "da_phan_bo": 1875000},
		{"ten": "D", "mo_ta": MO_TA_CTY, "da_phan_bo": 0},
	]
	kq = d.chu_theo_noi_dung(gds, "TCVEHQHG", ma_bill.RE_MA)
	la("mã bill khác", kq.get("A"), "bill mang mã TCVACDEF")
	la("mã của chính bill đang xem không chặn", kq.get("B"), None)
	la("đã khớp chứng từ ngân hàng", kq.get("C"), "chứng từ trong Đối chiếu ngân hàng")
	la("dòng tự do", kq.get("D"), None)


@ca("v610 trạng thái tiền của bill chuyển khoản")
def _trang_thai():
	d = _dsck()
	la("đủ", d.trang_thai_tien(1875000, 1875000), d.TT_DU)
	la("lệch một đồng vẫn đủ", d.trang_thai_tien(1874999.5, 1875000), d.TT_DU)
	la("thiếu", d.trang_thai_tien(1000000, 1875000), d.TT_THIEU)
	la("chưa", d.trang_thai_tien(0, 1875000), d.TT_CHUA)


@ca("v610 danh sách vai màn Đối soát chuyển khoản: JS và máy chủ trùng từng chữ")
def _vai_trung():
	d = _dsck()
	goc = os.path.dirname(os.path.dirname(os.path.abspath(d.__file__)))
	js = io.open(os.path.join(goc, "vagabond", "public", "js", "bep", "56-doi-soat-ck.js"), encoding="utf-8").read()
	m = re.search(r"var QUYEN_DSCK = \[([^\]]*)\]", js)
	dung("có danh sách QUYEN_DSCK", bool(m))
	ds = re.findall(r"'([^']+)'", m.group(1)) if m else []
	la("trùng QUYEN_GAN_NGOAI", sorted(ds), sorted(d.QUYEN_GAN_NGOAI))


# ------------------------------------------------- cửa ghi pos_gan_tien chạy thật
#
# Không import ban_hang (kéo requests, CI tay không không có). Nạp riêng hai hàm
# THẬT pos_gan_tien và _gd_co_chu_toan_he bằng cây cú pháp, cùng cách
# thu_tang_tra_truoc_607, rồi cho chạy trên một Frappe giả tối thiểu.

import ast
import sys
import types
from unittest.mock import patch


def _nap(ten, g):
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	cay = ast.parse(io.open(os.path.join(goc, "ban_hang.py"), encoding="utf-8").read())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)
	ham.decorator_list = []
	exec(compile(ast.Module(body=[ham], type_ignores=[]), "ban_hang.py", "exec"), g)
	return g[ten]


class _Loi(Exception):
	pass


class _Si(dict):
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def save(self):
		self["_da_luu"] = 1


def _loc_gia(ban_ghi, loc):
	"""Bộ lọc frappe.get_all tối thiểu cho Frappe giả: =, !=, in, <."""
	def hop(r, k, v):
		x = r.get(k)
		if isinstance(v, (list, tuple)) and len(v) == 2 and v[0] in ("in", "!=", "<", "is"):
			op, gt = v
			if op == "in":
				return x in gt
			if op == "!=":
				return x != gt
			if op == "<":
				return (x or 0) < gt
			return bool(x) if gt == "set" else not x
		return x == v
	ds = loc.items() if isinstance(loc, dict) else [(f[0], [f[1], f[2]]) for f in loc]
	return [_Si(r) for r in ban_ghi if all(hop(r, k, v) for k, v in ds)]


def _chay_gan(vai, ma_gd, chu_he=None, si_them=None, sao_ke_them=None, hd_khac=None, cong_no=None):
	"""Chạy THẬT pos_gan_tien cho bill TCVEHQHG. Trả (bill, lỗi).

	si_them      ô thay trên bill (ví dụ bill đã gắn một lần: mã tham chiếu là số ngân hàng)
	sao_ke_them  {tên dòng: ô thay} trên dòng sao kê
	hd_khac      các hoá đơn khác trong hệ (cho phép hỏi chủ theo mã tham chiếu và mã bill)
	cong_no      các phiếu công nợ trong hệ. Có thì chạy THẬT doi_soat_sepay.chu_cua_giao_dich
	             với sổ chỉ có luồng công nợ và bộ lọc DB giả (Codex #497 v2 4367048767)
	"""
	from vagabond import doi_soat_ck as d
	from vagabond import ma_bill

	si = _Si(name="HDB-26-10-04707", docstatus=0, grand_total=1875000, vgb_quay="TCV",
		vgb_ma_tham_chieu="TCVEHQHG", custom_pancake_display_id="TCVEHQHG",
		vgb_ghi_chu_doi_soat="", flags=types.SimpleNamespace())
	si.update(si_them or {})
	sao_ke = {
		"BT-CTY": dict(name="BT-CTY", deposit=1875000, reference_number="FT26296028012585",
			date="2026-10-23", docstatus=0, description=MO_TA_CTY.replace(" FT26296028012585", ""),
			unallocated_amount=1875000),
		"BT-TCV": dict(name="BT-TCV", deposit=1875000, reference_number="FT26296000000001",
			date="2026-10-23", docstatus=0, description=MO_TA_TCV.replace(" FT26296000000001", ""),
			unallocated_amount=1875000),
	}
	for ten_gd, them in (sao_ke_them or {}).items():
		sao_ke[ten_gd].update(them)
	hd = [dict(si, docstatus=si.docstatus, vgb_huy=0)] + [dict(r) for r in (hd_khac or [])]
	db = types.SimpleNamespace(
		get_value=lambda dt, ten, cot, as_dict=False: _Si(sao_ke[ten]) if ten in sao_ke else None,
		set_value=lambda *a, **k: None, commit=lambda: None)

	def _throw(m, *a, **k):
		raise _Loi(m)

	fr = types.SimpleNamespace(
		get_doc=lambda dt, ten: si, db=db, throw=_throw, get_roles=lambda: vai,
		get_all=lambda dt, filters=None, fields=None, **k: _loc_gia(hd, filters or {}) if dt == "Sales Invoice" else [],
		session=types.SimpleNamespace(user="de@x"),
		utils=types.SimpleNamespace(get_fullname=lambda u: "Dễ"),
		log_error=lambda *a, **k: None, get_traceback=lambda: "")
	tk = types.SimpleNamespace(CN_DIEM="@diem:", tk_cho=lambda n, diem: {"rieng": 1, "stk": "VQRQALEAF2999"})
	g = {
		"frappe": fr, "re": re, "tai_khoan": tk,
		"_kiem_quyen_ban": lambda: None,
		"_diem_cua_bill": lambda s: "TCV",
		"RE_MA_NGAN_HANG": re.compile(r"[A-Z0-9]{6,40}"),
		"RE_MA_BILL": ma_bill.RE_MA,
		"cint": lambda v: int(v or 0), "flt": lambda v: float(v or 0),
		"fmt_money": lambda v: "{:,.0f}".format(float(v)).replace(",", "."),
		"SAI_SO_DO_TIEN": 1.0,
	}
	_nap("_gd_da_co_chu", g)
	_nap("_ma_cua_bill", g)
	_nap("_chu_ma_bill", g)
	_nap("_gd_co_chu_toan_he", g)
	gan = _nap("pos_gan_tien", g)
	import vagabond
	loi = None
	if cong_no is not None:
		import contextlib

		import frappe
		from vagabond import bo_sao_ke_db as bs
		from vagabond import doi_soat_sepay as that

		so = {"cong_no": {"doctype": "Vagabond Cong No", "truong_gd": "ma_gd",
			"ten_man": "phiếu công nợ", "loc_chiem": {"trang_thai": ["!=", "Huy"]}}}
		bang = {"Vagabond Cong No": cong_no, "Sales Invoice": hd}

		def _get_all(dt, filters=None, fields=None, **k):
			return _loc_gia(bang.get(dt, []), filters or {})

		boc = contextlib.ExitStack()
		for x in (patch.object(that, "_SO", so), patch.object(that, "nap_so", lambda: None),
				patch.object(bs, "_cac_bo", lambda ma: []), patch.object(frappe, "get_all", _get_all, create=True),
				patch.object(frappe, "log_error", lambda *a, **k: None, create=True)):
			boc.enter_context(x)
	else:
		dss = types.ModuleType("vagabond.doi_soat_sepay")
		dss.chu_cua_giao_dich = lambda ds, bo_qua_hoa_don=None: dict(chu_he or {})
		boc = __import__("contextlib").ExitStack()
		boc.enter_context(patch.dict(sys.modules, {"vagabond.doi_soat_sepay": dss}))
		boc.enter_context(patch.object(vagabond, "doi_soat_sepay", dss, create=True))
	with boc, patch.object(d, "bang_dau_he", lambda: d.bang_dau(CAU_HINH, TEN)):
		try:
			gan("HDB-26-10-04707", ma_gd)
		except _Loi as e:
			loi = str(e)
	return si, loi


@ca("v610 cửa ghi: thu ngân gắn khoản tài khoản chính bị chặn ở máy chủ, bill không đổi")
def _gan_thu_ngan():
	si, loi = _chay_gan(QUAY, "BT-CTY")
	dung("có lỗi chặn", bool(loi) and "Chỉ Quản lý cửa hàng hoặc Kế toán" in loi)
	dung("câu nói rõ tiền vào đâu", "vào thẳng tài khoản chính công ty" in (loi or ""))
	la("bill không lưu", si.get("_da_luu"), None)
	la("mã tham chiếu giữ nguyên", si.vgb_ma_tham_chieu, "TCVEHQHG")


@ca("v610 cửa ghi: quản lý cửa hàng gắn được, ghi số tham chiếu và tên người gắn")
def _gan_quan_ly():
	si, loi = _chay_gan(QLCH, "BT-CTY")
	la("không lỗi", loi, None)
	la("bill đã lưu", si.get("_da_luu"), 1)
	la("số tham chiếu ngân hàng", si.vgb_ma_tham_chieu, "FT26296028012585")
	dung("vết ghi tên người và tài khoản: " + si.vgb_ghi_chu_doi_soat,
		si.vgb_ghi_chu_doi_soat.startswith("Quản lý dò tay (Dễ, vào thẳng tài khoản chính công ty): gắn khoản 1.875.000 đ"))


@ca("v610 cửa ghi: khoản đã có chủ ở luồng khác thì quản lý cũng không gắn được")
def _gan_co_chu():
	si, loi = _chay_gan(QLCH, "BT-CTY", {"BT-CTY": "phiếu công nợ CN-0001"})
	dung("chặn và nói ai giữ", bool(loi) and "đã thuộc về phiếu công nợ CN-0001" in loi)
	la("bill không lưu", si.get("_da_luu"), None)


@ca("v610 cửa ghi: thu ngân vẫn gắn khoản vào tài khoản của điểm mình như trước")
def _gan_diem():
	si, loi = _chay_gan(QUAY, "BT-TCV")
	la("không lỗi", loi, None)
	dung("vết thu ngân như cũ", si.vgb_ghi_chu_doi_soat.startswith("Thu ngân dò tay: gắn khoản 1.875.000 đ"))


# ------------------------------------------------- vòng 2: ba finding Codex trên d6777aa


@ca("v610 v2 Codex 4366436285: bill đã giữ số tham chiếu nhưng dòng còn chủ khác thì vẫn bị chặn")
def _f1_chu_khac():
	# Dựng đúng chuỗi Codex mô tả: bill đang xem ĐÃ giữ số tham chiếu của dòng
	# (gắn trước đó), đồng thời dòng đã thuộc phiếu công nợ và đã phân bổ trong
	# Đối chiếu ngân hàng. Trên d6777aa hàm hỏi chủ trả {} nên cửa gắn cho qua.
	si, loi = _chay_gan(QLCH, "BT-CTY", chu_he={"BT-CTY": "phiếu công nợ CN-0001"},
		si_them={"vgb_ma_tham_chieu": "FT26296028012585"},
		sao_ke_them={"BT-CTY": {"unallocated_amount": 0}})
	dung("bị chặn và nói ai giữ: %r" % loi, bool(loi) and "phiếu công nợ CN-0001" in loi)
	la("bill không lưu", si.get("_da_luu"), None)
	si2, loi2 = _chay_gan(QLCH, "BT-CTY", si_them={"vgb_ma_tham_chieu": "FT26296028012585"},
		sao_ke_them={"BT-CTY": {"unallocated_amount": 0}})
	dung("chỉ còn chủ Đối chiếu ngân hàng cũng bị chặn: %r" % loi2,
		bool(loi2) and "Đối chiếu ngân hàng" in loi2)


@ca("v610 v2 Codex 4366436291: gắn lại dòng mang mã của chính bill sau khi mã tham chiếu đã đổi")
def _f3_ma_cua_chinh_bill():
	# Lần gắn đầu thay vgb_ma_tham_chieu bằng số ngân hàng; mã bill gốc còn ở
	# custom_pancake_display_id. Thử lại (mất phản hồi) phải qua.
	mo_ta = "TCVEHQHG chuyen tien banh"
	si, loi = _chay_gan(QLCH, "BT-CTY", si_them={"vgb_ma_tham_chieu": "FT26296028012585"},
		sao_ke_them={"BT-CTY": {"description": mo_ta}})
	la("không lỗi", loi, None)
	la("bill đã lưu", si.get("_da_luu"), 1)
	# Mã của MỘT BILL KHÁC trong nội dung thì vẫn chặn.
	si2, loi2 = _chay_gan(QLCH, "BT-CTY", sao_ke_them={"BT-CTY": {"description": "TCVACDEF chuyen tien"}},
		hd_khac=[{"name": "HDB-26-10-04700", "docstatus": 0, "vgb_huy": 0,
			"vgb_ma_tham_chieu": "TCVACDEF", "custom_pancake_display_id": "TCVACDEF"}])
	dung("mã bill khác bị chặn: %r" % loi2, bool(loi2) and "HDB-26-10-04700" in loi2)
	# Mã không còn bill nào mang (đã bị thay) mà không phải của bill này: vẫn chặn, không đoán.
	si3, loi3 = _chay_gan(QLCH, "BT-CTY", sao_ke_them={"BT-CTY": {"description": "TCVACDEF chuyen tien"}})
	dung("mã lạ vẫn chặn: %r" % loi3, bool(loi3) and "TCVACDEF" in loi3)


# ------------------------------------------------- vòng 3: finding Codex trên ad1816d


@ca("v610 v3 Codex 4367048767: phiếu công nợ cũ giữ NHIỀU giao dịch trong một ô vẫn là chủ")
def _f4_cong_no_nhieu_ma():
	# Chạy THẬT doi_soat_sepay.chu_cua_giao_dich. Phiếu công nợ ghi cộng dồn
	# (cong_no.py: gom_gd) nên ô ma_gd là "BT-X\nBT-CTY". Lọc "in" nguyên ô
	# thì không khớp và cửa gắn cho quản lý nhận khoản đã trả công nợ.
	cn = [{"name": "CN-OLD", "trang_thai": "Da thu du", "ma_gd": "BT-X\nBT-CTY"}]
	si, loi = _chay_gan(QLCH, "BT-CTY", cong_no=cn)
	dung("tên dòng nằm giữa danh sách: chặn và nói ai giữ: %r" % loi,
		bool(loi) and "phiếu công nợ CN-OLD" in loi)
	la("bill không lưu", si.get("_da_luu"), None)
	# Phiếu cũ lưu SỐ THAM CHIẾU ngân hàng thay vì tên dòng (lịch sử).
	cn2 = [{"name": "CN-REF", "trang_thai": "Thu thieu", "ma_gd": "FT26296028012585\nBT-X"}]
	si2, loi2 = _chay_gan(QLCH, "BT-CTY", cong_no=cn2)
	dung("số tham chiếu lịch sử cũng chặn: %r" % loi2, bool(loi2) and "phiếu công nợ CN-REF" in loi2)
	la("bill không lưu", si2.get("_da_luu"), None)
	# Phiếu đã huỷ thì nhả dòng (loc_chiem của luồng), không chặn nhầm.
	cn3 = [{"name": "CN-HUY", "trang_thai": "Huy", "ma_gd": "BT-X\nBT-CTY"}]
	si3, loi3 = _chay_gan(QLCH, "BT-CTY", cong_no=cn3)
	la("phiếu huỷ không giữ tiền", loi3, None)
	la("bill đã lưu", si3.get("_da_luu"), 1)
	# Một ô một mã như cũ vẫn chặn.
	cn4 = [{"name": "CN-1", "trang_thai": "Cho thu", "ma_gd": "BT-CTY"}]
	si4, loi4 = _chay_gan(QLCH, "BT-CTY", cong_no=cn4)
	dung("một mã vẫn chặn: %r" % loi4, bool(loi4) and "phiếu công nợ CN-1" in loi4)
