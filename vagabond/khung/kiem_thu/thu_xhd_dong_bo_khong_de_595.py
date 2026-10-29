# -*- coding: utf-8 -*-
"""v595: nhịp đồng bộ Pancake không được đè người mua sales đã nhập tay.

Loan Anh báo 15/10/2026, tờ HDB-26-10-02615 (đơn Pancake #95605). Lịch sử
Version trên site:
  - Sales lưu "Không có MST Việt Nam": tên COCO INVESTMENTS PTE. LTD, địa chỉ
    Singapore, email, mã số thuế trống.
  - 22:32 nhịp đồng bộ đổi tên thành "Bán cho người tiêu dùng".
  - 23:00 tên đã là mặc định nên nhịp sau xoá luôn địa chỉ và email.
  - 23:07 hoá đơn 19621 xuất cho người tiêu dùng.

Gốc lỗi: điều kiện cũ đọc lại người mua "chừng nào còn thiếu mã số thuế", mà
người mua không MST thì vĩnh viễn thiếu. Bản sửa của #456 (v588) chỉ chốt màn
Sales và tờ gửi m-invoice, chưa có ca nào chạy nhịp đồng bộ trên một tờ đã có
tên không MST, nên lỗi lọt.

Các ca ở đây chạy ĐÚNG hàm `_upsert_hoa_don` và `_thong_tin_xhd` nạp từ mã
nguồn thật, chỉ thay phần chạm site (frappe, tra cứu MST). Không gọi thêm hàm
nào ngoài chuỗi của nhịp đồng bộ (điều 15).
"""

import ast
import re
import sys
import unicodedata
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la

TEN_NAP = (
	"XHD_MAC_DINH", "RE_MOC_MST", "RE_MOI_SO", "TU_KHOA_XHD", "RE_EMAIL", "MIEN_CUA_MINH",
	"_text_don", "_bo_dau", "_chuan_mst", "_so_hop_le", "_tach_mst", "_tach_email",
	"_thong_tin_xhd", "TRUONG_XHD", "nguoi_mua_con_trong", "gop_nguoi_mua_dong_bo",
	"_upsert_hoa_don",
	# v619: _upsert_hoa_don gọi giu_ten_dong khi thêm lại bảng món.
	"giu_ten_dong",
)
MAC_DINH = "Bán cho người tiêu dùng"


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


def _nap(g, nguon=None):
	"""Nạp đúng các hằng và hàm cần dùng từ ban_hang.py vào g."""
	nguon = nguon if nguon is not None else (Path(__file__).resolve().parents[2] / "ban_hang.py").read_text(encoding="utf-8")
	cay = ast.parse(nguon)
	chon = []
	for n in cay.body:
		if isinstance(n, ast.FunctionDef) and n.name in TEN_NAP:
			n.decorator_list = []
			chon.append(n)
		elif isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in TEN_NAP for t in n.targets):
			chon.append(n)
	exec(compile(ast.Module(body=chon, type_ignores=[]), "ban_hang.py", "exec"), g)
	return g


def _to(**kw):
	d = D(name="HDB-26-10-02615", docstatus=0, customer="KH", vgb_pt_thanh_toan="Chuyển khoản", vgb_pt_do_may=1,
		vgb_xhd_ten="", vgb_xhd_mst="", vgb_xhd_dia_chi="", vgb_xhd_email="", flags=D())
	d.update(kw)
	d["save"] = lambda *a, **k: None
	d["set"] = lambda k, v: d.__setitem__(k, v)
	d["append"] = lambda *a, **k: None
	return d


def _dong_bo(d, don, tra_mst=None, portal=None, nguon=None):
	"""Chạy MỘT nhịp `_upsert_hoa_don` thật trên tờ d."""
	def gv(dt, loc, *a, **k):
		return None if loc.get("docstatus") == 2 else D(name=d.name, docstatus=0)
	f = NS(db=NS(get_value=gv, exists=lambda *a, **k: True), get_doc=lambda *a, **k: d,
		get_all=lambda *a, **k: list(portal or []), log_error=lambda *a, **k: None, throw=lambda m: (_ for _ in ()).throw(Exception(m)))
	g = dict(frappe=f, re=re, unicodedata=unicodedata, flt=lambda x: float(x or 0), cint=lambda x: int(x or 0),
		hoa_don_vat=NS(sach_dia_chi_xhd=lambda s: (s or "").strip(), thieu_ten_rieng=lambda t: False),
		_dong_hang=lambda *a: ([{"item_code": "BANH", "qty": 1, "rate": 100}], []), _lech_pancake=lambda *a: 0,
		giu_khach_cua_don=lambda *a: True, _giam_tu_diem=lambda *a: 0, _doan_thanh_toan=lambda *a: ("", ""),
		_dien_dong_thanh_toan=lambda *a: None, nghi_cong_no=lambda *a: 0)
	g["_yeu_cau_xhd_dung_don"] = lambda ma: (portal or [None])[0]
	_nap(g, nguon)
	api = NS(tra_mst=tra_mst or (lambda mst: {}))
	with patch.dict(sys.modules, {"vagabond.khach_hang": NS(la_khach_gop=lambda x: False), "vagabond.api": api}):
		g["_upsert_hoa_don"](don, "2026-10-14", "CT", "KH")
	return {k: d.get(k) for k in ("vgb_xhd_ten", "vgb_xhd_mst", "vgb_xhd_dia_chi", "vgb_xhd_email")}


COCO = dict(vgb_xhd_ten="COCO INVESTMENTS PTE. LTD", vgb_xhd_mst="",
	vgb_xhd_dia_chi="62 BENDEMEER ROAD, #06-00, GMA BUILDING, SINGAPORE 339939",
	vgb_xhd_email="quynhdtn@betrimex.com.vn")
DON = {"id": "PK95605", "display_id": "95605", "note": "Giao 14h, gọi trước khi tới"}


@ca("v595 HDB-26-10-02615: hai nhịp đồng bộ 22:32 và 23:00 không đè tên, địa chỉ, email người mua không MST")
def _():
	d = _to(**COCO)
	_dong_bo(d, DON)
	la("sau nhịp 22:32 giữ nguyên bốn ô", _dong_bo(d, DON), COCO)
	la("sau nhịp 23:00 vẫn giữ nguyên", _dong_bo(d, DON), COCO)


@ca("v595: công đoàn không MST, ghi chú đơn có MST công ty mẹ thì máy KHÔNG đổi người mua")
def _():
	cd = dict(vgb_xhd_ten="CÔNG ĐOÀN CÔNG TY TNHH CÔNG NGHỆ ASUS (VIỆT NAM)", vgb_xhd_mst="",
		vgb_xhd_dia_chi="Toà nhà A, Quận 7, TP HCM", vgb_xhd_email="")
	don = {"id": "PK94989", "display_id": "94989", "note": "Xuất hoá đơn MST 0312345678, mail congdoan@asus.invalid"}
	tra = lambda mst: {"ok": 1, "ten": "CÔNG TY TNHH CÔNG NGHỆ ASUS (VIỆT NAM)", "dia_chi": "Quận 7"}
	kq = _dong_bo(_to(**cd), don, tra_mst=tra)
	la("tên, MST, địa chỉ giữ nguyên",
		(kq["vgb_xhd_ten"], kq["vgb_xhd_mst"], kq["vgb_xhd_dia_chi"]),
		(cd["vgb_xhd_ten"], "", cd["vgb_xhd_dia_chi"]))
	la("chỉ bù email còn trống", kq["vgb_xhd_email"], "congdoan@asus.invalid")


@ca("v595 giữ bài học 91476: tờ đang mặc định, ghi chú có MST về sau thì vẫn điền công ty")
def _():
	don = {"id": "PK91476", "display_id": "91476", "note": "Để in: xuất hoá đơn MST 0311638525 email kt@abc.invalid"}
	tra = lambda mst: {"ok": 1, "ten": "CÔNG TY TNHH ABC", "dia_chi": "12 Lê Lợi, Quận 1"}
	kq = _dong_bo(_to(vgb_xhd_ten=MAC_DINH), don, tra_mst=tra)
	la("điền đủ", kq, {"vgb_xhd_ten": "CÔNG TY TNHH ABC", "vgb_xhd_mst": "0311638525",
		"vgb_xhd_dia_chi": "12 Lê Lợi, Quận 1", "vgb_xhd_email": "kt@abc.invalid"})


@ca("v595: tờ đang mặc định, khách nhắc hoá đơn mà không ra MST thì để TRỐNG tên cho sales điền")
def _():
	don = {"id": "PK1", "display_id": "1", "note": "Có xuất hoá đơn, mail a@b.invalid"}
	kq = _dong_bo(_to(vgb_xhd_ten=MAC_DINH), don)
	la("tên trống, email nhặt được", (kq["vgb_xhd_ten"], kq["vgb_xhd_email"]), ("", "a@b.invalid"))


@ca("v595: tờ mặc định có email sales gõ, ghi chú không có gì thì không xoá email")
def _():
	kq = _dong_bo(_to(vgb_xhd_ten=MAC_DINH, vgb_xhd_email="khach@le.invalid"), DON)
	la("giữ email", (kq["vgb_xhd_ten"], kq["vgb_xhd_email"]), (MAC_DINH, "khach@le.invalid"))


@ca("v595: tờ trống tên lúc mới về vẫn nhận mặc định như cũ")
def _():
	kq = _dong_bo(_to(), DON)
	la("mặc định", kq["vgb_xhd_ten"], MAC_DINH)


@ca("v595: có tên và MST thì không đụng, chỉ bù email trống")
def _():
	co = dict(vgb_xhd_ten="CÔNG TY TNHH XYZ", vgb_xhd_mst="0300000000", vgb_xhd_dia_chi="HCM", vgb_xhd_email="")
	kq = _dong_bo(_to(**co), {"id": "P", "display_id": "P", "note": "mail x@y.invalid"})
	la("giữ ba ô, bù email", kq, dict(co, vgb_xhd_email="x@y.invalid"))


@ca("v595: bảng luật thuần gop_nguoi_mua_dong_bo")
def _():
	g = _nap(dict(re=re, unicodedata=unicodedata))
	gop, trong = g["gop_nguoi_mua_dong_bo"], g["nguoi_mua_con_trong"]
	la("tên rỗng là trống", trong({"vgb_xhd_ten": " "}), True)
	la("tên mặc định là trống", trong({"vgb_xhd_ten": MAC_DINH}), True)
	la("tên thật không trống", trong({"vgb_xhd_ten": "COCO"}), False)
	moi = {"vgb_xhd_ten": MAC_DINH, "vgb_xhd_mst": "", "vgb_xhd_dia_chi": "", "vgb_xhd_email": ""}
	la("tên thật: kết quả đọc lại bị bỏ qua", gop(dict(COCO), moi=moi), {})
	la("tên thật, email trống: chỉ bù email", gop(dict(COCO, vgb_xhd_email=""), mail="m@n.invalid"), {"vgb_xhd_email": "m@n.invalid"})
	la("tên thật, có email: không bù", gop(dict(COCO), mail="m@n.invalid"), {})
	la("trống: ghi hết, giữ email cũ", gop({"vgb_xhd_ten": "", "vgb_xhd_email": "e@f.invalid"}, moi=moi),
		{"vgb_xhd_ten": MAC_DINH, "vgb_xhd_mst": "", "vgb_xhd_dia_chi": ""})


@ca("v595: nguồn ban_hang.py không còn điều kiện đọc lại 'chừng nào còn thiếu MST'")
def _():
	# Phép dò chuỗi chỉ để chốt KHÔNG còn đường cũ (điều 16); hành vi đã có các ca chạy thật ở trên.
	s = (Path(__file__).resolve().parents[2] / "ban_hang.py").read_text(encoding="utf-8")
	dung("không còn `or not cu_mst`", "or not cu_mst" not in s)
	la("chỉ một chỗ gọi luật gộp trong nhịp đồng bộ", s.count("gop_nguoi_mua_dong_bo(cu_xhd"), 2)
