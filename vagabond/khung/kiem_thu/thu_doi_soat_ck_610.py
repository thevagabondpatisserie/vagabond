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


def _chay_gan(vai, ma_gd, chu_he=None):
	"""Chạy THẬT pos_gan_tien cho bill TCVEHQHG. Trả (bill, lỗi)."""
	from vagabond import doi_soat_ck as d
	from vagabond import ma_bill

	si = _Si(name="HDB-26-10-04707", docstatus=0, grand_total=1875000, vgb_quay="TCV",
		vgb_ma_tham_chieu="TCVEHQHG", vgb_ghi_chu_doi_soat="", flags=types.SimpleNamespace())
	sao_ke = {
		"BT-CTY": dict(name="BT-CTY", deposit=1875000, reference_number="FT26296028012585",
			date="2026-10-23", docstatus=0, description=MO_TA_CTY.replace(" FT26296028012585", ""),
			unallocated_amount=1875000),
		"BT-TCV": dict(name="BT-TCV", deposit=1875000, reference_number="FT26296000000001",
			date="2026-10-23", docstatus=0, description=MO_TA_TCV.replace(" FT26296000000001", ""),
			unallocated_amount=1875000),
	}
	db = types.SimpleNamespace(
		get_value=lambda dt, ten, cot, as_dict=False: _Si(sao_ke[ten]) if ten in sao_ke else None,
		set_value=lambda *a, **k: None, commit=lambda: None)

	def _throw(m, *a, **k):
		raise _Loi(m)

	fr = types.SimpleNamespace(
		get_doc=lambda dt, ten: si, db=db, throw=_throw, get_roles=lambda: vai,
		get_all=lambda *a, **k: [], session=types.SimpleNamespace(user="de@x"),
		utils=types.SimpleNamespace(get_fullname=lambda u: "Dễ"),
		log_error=lambda *a, **k: None, get_traceback=lambda: "")
	tk = types.SimpleNamespace(CN_DIEM="@diem:", tk_cho=lambda n, diem: {"rieng": 1, "stk": "VQRQALEAF2999"})
	g = {
		"frappe": fr, "re": re, "tai_khoan": tk,
		"_kiem_quyen_ban": lambda: None,
		"_diem_cua_bill": lambda s: "TCV",
		"_gd_da_co_chu": lambda gds: {},
		"RE_MA_NGAN_HANG": re.compile(r"[A-Z0-9]{6,40}"),
		"RE_MA_BILL": ma_bill.RE_MA,
		"cint": lambda v: int(v or 0), "flt": lambda v: float(v or 0),
		"fmt_money": lambda v: "{:,.0f}".format(float(v)).replace(",", "."),
		"SAI_SO_DO_TIEN": 1.0,
	}
	_nap("_gd_co_chu_toan_he", g)
	gan = _nap("pos_gan_tien", g)
	dss = types.ModuleType("vagabond.doi_soat_sepay")
	dss.chu_cua_giao_dich = lambda ds, bo_qua_hoa_don=None: dict(chu_he or {})
	import vagabond
	loi = None
	with patch.dict(sys.modules, {"vagabond.doi_soat_sepay": dss}), \
			patch.object(vagabond, "doi_soat_sepay", dss, create=True), \
			patch.object(d, "bang_dau_he", lambda: d.bang_dau(CAU_HINH, TEN)):
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
