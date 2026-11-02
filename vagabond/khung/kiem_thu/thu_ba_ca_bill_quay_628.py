# -*- coding: utf-8 -*-
"""v628: ba ca bill quầy Dễ báo ngày 02/11/2026.

TH1 (NVH, 01/11): khách quét mã QR NVHCXVC4, app tải lại trước khi bill được
lưu. Bill lập lại NVHDQ6FJ không gắn được khoản 40.000 vì máy coi mã
NVHCXVC4 là "của một bill khác" dù không bill nào mang mã đó.

TH3 (D1, 02/11): bill SOL3D4A9 (HDB-26-11-00292) bấm nhầm điểm Sales Online,
nhận 1.130.000 rồi bị huỷ. Bill lập lại TCVURLV8 (HDB-26-11-00295) không gắn
được vì bill đã huỷ vẫn giữ khoản tiền.

TH2 (NVH, 01/11): bill 405.000 bớt giá còn 290.000 sau khi khách chuyển đủ,
phần thừa phải chuyển lại khách. Ca dưới chốt phép tính phần thừa.

Mọi ca chạy THẬT các hàm của ban_hang (nạp bằng ast, không import ban_hang vì
nó kéo theo requests) trên Frappe giả, không dò chuỗi mã nguồn.
"""

import ast
import datetime
import io
import os
import re
import sys
import types
from unittest import mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la

QUAY = ["VGB - Nhân viên bán hàng"]
QLCH = ["VGB - Nhân viên bán hàng", "VGB - Quản lý cửa hàng"]

# Dấu tài khoản ảo như trên site (xem thu_doi_soat_ck_610).
CAU_HINH = {
	"mac_dinh": {"bank": "MB", "stk": "VQRQ00033k5p6", "ten": "PATISSERIE VAGABOND COMPANY LIMITED"},
	"theo_nguon": [
		{"nguon": "@diem:SALES", "bank": "MB", "stk": "VQRQALEAI2626", "dung": 1},
		{"nguon": "@diem:NVHTN", "bank": "MB", "stk": "VQRQALEAI0938", "dung": 1},
		{"nguon": "@diem:TCV", "bank": "MB", "stk": "VQRQALEAF2999", "dung": 1},
	],
}
TEN = {"TCV": "Trần Cao Vân", "NVHTN": "NVHTN", "SALES": "Sales Online"}

# Hai dòng sao kê dựng theo đúng hai ca đọc trên site.
SAO_KE = {
	"BT-SOL": dict(name="BT-SOL", deposit=1130000, reference_number="FT26306111111111",
		date="2026-11-02", docstatus=0, unallocated_amount=1130000,
		creation="2026-11-02 10:50:00", description="QALEAI2626 VAGABOND SOL3D4A9 Ma GD ACSP/ AB000001"),
	"BT-NVH": dict(name="BT-NVH", deposit=40000, reference_number="FT26305222222222",
		date="2026-11-01", docstatus=0, unallocated_amount=40000,
		creation="2026-11-01 11:55:00", description="QALEAI0938 VAGABOND NVHCXVC4 Ma GD ACSP/ CD000002"),
}


def _bill(name, ma, quay, **k):
	r = dict(name=name, docstatus=0, vgb_huy=0, grand_total=0, vgb_quay=quay,
		vgb_ma_tham_chieu=ma, custom_pancake_display_id=ma, vgb_ghi_chu_doi_soat="",
		vgb_huy_luc=None, vgb_huy_ly_do=None)
	r.update(k)
	return r


def _bill_cu_th3(**k):
	"""HDB-26-11-00292: đã huỷ lúc 11:05 với lý do Gia Bảo ghi trên site."""
	r = _bill("HDB-26-11-00292", "SOL3D4A9", "", grand_total=1130000, vgb_huy=1,
		vgb_huy_luc="2026-11-02 11:05:12", vgb_huy_ly_do="OUT NHẦM NGUỒN CỦA SALE Ạ")
	r.update(k)
	return r


class _Loi(Exception):
	pass


class _Si(dict):
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def save(self):
		self["_da_luu"] = 1


def _loc(ban_ghi, loc):
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


def _nap(ten, g):
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	cay = ast.parse(io.open(os.path.join(goc, "ban_hang.py"), encoding="utf-8").read())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)
	ham.decorator_list = []
	exec(compile(ast.Module(body=[ham], type_ignores=[]), "ban_hang.py", "exec"), g)
	return g[ten]


def _the_gioi(vai, hd, hoan=(), bay_gio="2026-11-02 12:00:00", gd_cua_bill=None):
	"""Dựng Frappe giả và nạp THẬT các hàm gắn tiền của ban_hang.

	hd           mọi hoá đơn trong hệ (dict); set_value ghi thẳng vào đây
	hoan         phiếu hoàn tiền [{hoa_don, trang_thai}]
	gd_cua_bill  {tên bill: [tên dòng]} cho _sepay_cho_bill giả (pos_chuyen_tien)
	Trả dict hàm đã nạp.
	"""
	from vagabond import doi_soat_ck as d
	from vagabond import ma_bill

	hd = [h for h in hd]
	theo_ten = {h["name"]: h for h in hd}
	bg = datetime.datetime.fromisoformat(bay_gio)

	def _get_doc(dt, ten):
		r = theo_ten[ten]
		if not isinstance(r, _Si):
			r = _Si(r)
			r.flags = types.SimpleNamespace()
			theo_ten[ten] = r
			hd[[x["name"] for x in hd].index(ten)] = r
		return r

	def _set_value(dt, ten, a, b=None, **k):
		if dt != "Sales Invoice":
			return
		r = theo_ten[ten]
		r.update(a if isinstance(a, dict) else {a: b})

	def _get_value(dt, ten, cot, as_dict=False):
		if dt == "Bank Transaction":
			return _Si(SAO_KE[ten]) if ten in SAO_KE else None
		if dt == "Sales Invoice":
			return theo_ten[ten].get(cot) if isinstance(cot, str) else _Si(theo_ten[ten])
		return None

	def _get_all(dt, filters=None, fields=None, **k):
		if dt == "Sales Invoice":
			return _loc(hd, filters or {})
		if dt == "Vagabond Hoan Tien":
			return _loc(list(hoan), filters or {})
		if dt == "Bank Transaction":
			return _loc(list(SAO_KE.values()), filters or {})
		return []

	def _throw(m, *a, **k):
		raise _Loi(m)

	fr = types.SimpleNamespace(
		get_doc=_get_doc, throw=_throw, get_roles=lambda: vai, get_all=_get_all,
		db=types.SimpleNamespace(get_value=_get_value, set_value=_set_value, commit=lambda: None),
		session=types.SimpleNamespace(user="giabao@x"),
		utils=types.SimpleNamespace(get_fullname=lambda u: "Gia Bảo"),
		log_error=lambda *a, **k: None, get_traceback=lambda: "")

	def _phut(v):
		if not v:
			return None
		t = datetime.datetime.fromisoformat(str(v)[:19])
		return t.hour * 60 + t.minute + t.second / 60.0

	def _sepay_cho_bill(si):
		ds = list((gd_cua_bill or {}).get(si.get("name")) or [])
		return {"nhan": sum(SAO_KE[x]["deposit"] for x in ds), "gd": ds}

	g = {
		"frappe": fr, "re": re,
		"tai_khoan": types.SimpleNamespace(CN_DIEM="@diem:", tk_cho=lambda n, diem: {"rieng": 1}),
		"_kiem_quyen_ban": lambda: None,
		"_diem_cua_bill": lambda s: s.get("vgb_quay") or "SALES",
		"RE_MA_NGAN_HANG": re.compile(r"[A-Z0-9]{6,40}"),
		"RE_MA_BILL": ma_bill.RE_MA,
		"cint": lambda v: int(v or 0), "flt": lambda v: float(v or 0),
		"fmt_money": lambda v: "{:,.0f}".format(float(v)).replace(",", "."),
		"SAI_SO_DO_TIEN": 1.0,
		"getdate": lambda v: datetime.date.fromisoformat(str(v)[:10]),
		"now_datetime": lambda: bg,
		"nowdate": lambda: bay_gio[:10],
		"_phut_trong_ngay": _phut,
		"_sepay_cho_bill": _sepay_cho_bill,
	}
	for ten in ("_bill_nha", "_gd_qua_han", "_gd_da_co_chu", "_ma_cua_bill", "_chu_ma_bill",
			"_gd_co_chu_toan_he", "_gan_tien_vao", "pos_gan_tien", "_gd_cua_bill",
			"pos_chuyen_tien", "tien_da_sang_bill_khac"):
		_nap(ten, g)
	g["_hd"] = theo_ten
	g["_vo"] = (d, fr)
	return g


def _chay(g, ten_ham, *a, **k):
	"""Gọi một hàm đã nạp trong vỏ Frappe giả. Trả (kết quả, lỗi)."""
	import vagabond

	d, fr = g["_vo"]
	dss = types.ModuleType("vagabond.doi_soat_sepay")
	dss.chu_cua_giao_dich = lambda ds, bo_qua_hoa_don=None: {}
	with um.patch.dict(sys.modules, {"vagabond.doi_soat_sepay": dss}), \
			um.patch.object(vagabond, "doi_soat_sepay", dss, create=True), \
			um.patch.object(d, "bang_dau_he", lambda: d.bang_dau(CAU_HINH, TEN)):
		try:
			return g[ten_ham](*a, **k), None
		except _Loi as e:
			return None, str(e)


# ---------------------------------------------------------------- phép THUẦN


@ca("v628 ba ca: bill nháp đã huỷ mềm nhả tiền; có phiếu hoàn hoặc đã ghi sổ thì vẫn giữ")
def _thuan_nha():
	from vagabond import doi_soat_ck as d

	rows = [
		{"name": "A", "docstatus": 0, "vgb_huy": 1},
		{"name": "B", "docstatus": 0, "vgb_huy": 1},
		{"name": "C", "docstatus": 1, "vgb_huy": 1},
		{"name": "D", "docstatus": 0, "vgb_huy": 0},
	]
	la("chỉ A nhả", d.bill_huy_nha(rows, {"B"}), {"A"})
	cau = d.cau_bill_nha("SOL3D4A9", "HDB-26-11-00292", "2026-11-02 11:05:12", "OUT NHẦM NGUỒN CỦA SALE Ạ")
	la("câu giải thích", cau,
		"Bill SOL3D4A9 (HDB-26-11-00292) đã huỷ lúc 11:05 ngày 02/11 (lý do: OUT NHẦM NGUỒN CỦA SALE Ạ), chưa hoàn tiền cho khách.")


@ca("v628 ba ca: mã mồ côi quá 15 phút mới coi là tiền chưa thuộc ai; thiếu giờ thì không đoán")
def _thuan_qua_han():
	from vagabond import doi_soat_ck as d

	la("đúng 15 phút", d.qua_han_mo_coi("2026-11-01", 715, "2026-11-01", 730), True)
	la("mới 10 phút", d.qua_han_mo_coi("2026-11-01", 715, "2026-11-01", 725), False)
	la("hôm trước", d.qua_han_mo_coi("2026-10-31", 1430, "2026-11-01", 1), True)
	la("thiếu giờ", d.qua_han_mo_coi("2026-11-01", None, "2026-11-01", 730), False)
	la("thiếu ngày", d.qua_han_mo_coi("", 1, "2026-11-01", 730), False)


@ca("v628 ba ca: chủ đọc từ nội dung: mã bill đã huỷ nhả kèm câu, mã mồ côi chờ 15 phút; cửa cũ giữ luật cũ")
def _thuan_noi_dung():
	from vagabond import doi_soat_ck as d
	from vagabond import ma_bill

	gds = [{"ten": "G1", "mo_ta": "CK SOL3D4A9"}, {"ten": "G2", "mo_ta": "CK NVHCXVC4"},
		{"ten": "G3", "mo_ta": "CK NVHAAAAA"}]
	gc = {}
	ra = d.chu_theo_noi_dung(gds, ["TCVURLV8"], ma_bill.RE_MA, {},
		{"SOL3D4A9": {"cau": "Bill SOL3D4A9 đã huỷ", "bill": "HDB-26-11-00292"}}, {"G2"}, gc)
	la("G1 nhả", "G1" in ra, False)
	la("G1 có câu và bill cũ", gc.get("G1"), {"cau": "Bill SOL3D4A9 đã huỷ", "bill": "HDB-26-11-00292"})
	la("G2 quá hạn nhả", "G2" in ra, False)
	dung("G2 nói bill mất trước khi lưu", "bill bị mất trước khi lưu" in gc.get("G2", {}).get("cau", ""))
	dung("G3 chưa quá hạn vẫn giữ, nói chờ 15 phút", "15 phút" in ra.get("G3", ""))
	cu = d.chu_theo_noi_dung(gds, ["TCVURLV8"], ma_bill.RE_MA, {})
	la("cửa cũ (tin báo, quỹ) không nhả gì", sorted(cu), ["G1", "G2", "G3"])
	la("câu cửa cũ giữ nguyên", cu["G1"], "bill mang mã SOL3D4A9")


@ca("v628 ba ca: bảng Dò tiền hiện câu giải thích trên khoản được nhả, không hiện trên khoản đã có chủ")
def _thuan_bang():
	from vagabond import doi_soat_ck as d

	gds = [{"ten": "G1", "tien": 1130000, "gio": "10:50", "mo_ta": "QALEAI2626 SOL3D4A9"},
		{"ten": "G2", "tien": 1130000, "gio": "10:51", "mo_ta": "QALEAI2626 X"}]
	gc = {"G1": {"cau": "Bill SOL3D4A9 đã huỷ"}, "G2": {"cau": "không được hiện"}}
	kq = d.dung_bang_do_tien(gds, d.bang_dau(CAU_HINH, TEN), "@diem:SALES", 1, 1130000,
		{"G2": "bill khác"}, QUAY, "diem", lambda a, b: abs(a - b) <= 1, gc)
	theo = {r["ten"]: r for r in kq["gd"]}
	la("G1 có câu", theo["G1"]["ghi_chu"], "Bill SOL3D4A9 đã huỷ")
	la("G1 khớp tiền lên đầu", (kq["gd"][0]["ten"], theo["G1"]["khop"]), ("G1", 1))
	la("G2 có chủ thì không câu", theo["G2"]["ghi_chu"], "")


# ------------------------------------------------------------ chạy thật TH3


@ca("v628 TH3 chạy thật: quản lý gắn khoản của bill đã huỷ SOL3D4A9 cho bill lập lại TCVURLV8, vết ghi cả hai bill")
def _th3_quan_ly():
	moi = _bill("HDB-26-11-00295", "TCVURLV8", "TCV", grand_total=1130000)
	g = _the_gioi(QLCH, [_bill_cu_th3(), moi])
	kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00295", "BT-SOL")
	la("không lỗi", loi, None)
	si = g["_hd"]["HDB-26-11-00295"]
	la("bill mới giữ số tham chiếu", si.get("vgb_ma_tham_chieu"), "FT26306111111111")
	dung("ghi chú bill mới nói bill cũ đã huỷ", "SOL3D4A9 (HDB-26-11-00292) đã huỷ" in si.get("vgb_ghi_chu_doi_soat", ""))
	cu = g["_hd"]["HDB-26-11-00292"].get("vgb_ghi_chu_doi_soat", "")
	dung("bill cũ ghi khoản đã chuyển sang bill nào", "đã chuyển sang bill TCVURLV8 (HDB-26-11-00295)" in cu)
	dung("bill cũ ghi người gắn", "Gia Bảo" in cu)
	la("trả về bill cũ", kq.get("tu_bill"), "HDB-26-11-00292")


@ca("v628 TH3 chạy thật: bill đã huỷ mà đã lập phiếu hoàn tiền thì vẫn giữ tiền, không gắn được")
def _th3_co_hoan():
	moi = _bill("HDB-26-11-00295", "TCVURLV8", "TCV", grand_total=1130000)
	g = _the_gioi(QLCH, [_bill_cu_th3(), moi], hoan=[{"hoa_don": "HDB-26-11-00292", "trang_thai": "Cho chi"}])
	_kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00295", "BT-SOL")
	dung("bị chặn vì bill cũ giữ", "HDB-26-11-00292" in (loi or ""))
	la("bill mới không đổi", g["_hd"]["HDB-26-11-00295"].get("vgb_ma_tham_chieu"), "TCVURLV8")
	g2 = _the_gioi(QLCH, [_bill_cu_th3(), moi], hoan=[{"hoa_don": "HDB-26-11-00292", "trang_thai": "Da huy"}])
	_kq, loi2 = _chay(g2, "pos_gan_tien", "HDB-26-11-00295", "BT-SOL")
	la("phiếu hoàn đã huỷ thì nhả", loi2, None)


@ca("v628 TH3 chạy thật: bill cũ đã gắn tay số tham chiếu rồi huỷ thì số đó không còn chặn bill mới")
def _th3_tham_chieu():
	cu = _bill_cu_th3(vgb_ma_tham_chieu="FT26306111111111")
	moi = _bill("HDB-26-11-00295", "TCVURLV8", "TCV", grand_total=1130000)
	g = _the_gioi(QLCH, [cu, moi])
	_kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00295", "BT-SOL")
	la("không lỗi", loi, None)
	la("bill mới giữ số tham chiếu", g["_hd"]["HDB-26-11-00295"].get("vgb_ma_tham_chieu"), "FT26306111111111")


@ca("v628 TH3 chạy thật: thu ngân tự gắn khoản tài khoản Sales cho bill D1 vẫn bị chặn; bước lập lại sau huỷ thì chuyển được")
def _th3_thu_ngan():
	moi = _bill("HDB-26-11-00295", "TCVURLV8", "TCV", grand_total=1130000)
	g = _the_gioi(QUAY, [_bill_cu_th3(), moi], gd_cua_bill={"HDB-26-11-00292": ["BT-SOL"]})
	_kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00295", "BT-SOL")
	dung("gắn tay bị chặn theo luật tài khoản", "Chỉ Quản lý cửa hàng hoặc Kế toán" in (loi or ""))
	kq, loi2 = _chay(g, "pos_chuyen_tien", "HDB-26-11-00292", "HDB-26-11-00295")
	la("chuyển được", (loi2, kq and kq.get("chuyen")), (None, 1))
	la("bill mới giữ số tham chiếu", g["_hd"]["HDB-26-11-00295"].get("vgb_ma_tham_chieu"), "FT26306111111111")


@ca("v628 TH3 chạy thật: chuyển tiền chỉ từ bill đã huỷ chưa hoàn; nhiều khoản thì trả về để dò tay")
def _th3_chuyen_chan():
	moi = _bill("HDB-26-11-00295", "TCVURLV8", "TCV", grand_total=1130000)
	song = _bill_cu_th3(vgb_huy=0)
	g = _the_gioi(QUAY, [song, moi], gd_cua_bill={"HDB-26-11-00292": ["BT-SOL"]})
	_kq, loi = _chay(g, "pos_chuyen_tien", "HDB-26-11-00292", "HDB-26-11-00295")
	dung("bill chưa huỷ thì chặn", "chưa huỷ" in (loi or ""))
	g2 = _the_gioi(QUAY, [_bill_cu_th3(), moi], gd_cua_bill={"HDB-26-11-00292": ["BT-SOL", "BT-NVH"]})
	kq, loi2 = _chay(g2, "pos_chuyen_tien", "HDB-26-11-00292", "HDB-26-11-00295")
	la("nhiều khoản không chuyển", (loi2, kq.get("chuyen")), (None, 0))
	la("bill mới không đổi", g2["_hd"]["HDB-26-11-00295"].get("vgb_ma_tham_chieu"), "TCVURLV8")
	g3 = _the_gioi(QUAY, [_bill_cu_th3(), moi], gd_cua_bill={"HDB-26-11-00292": ["BT-NVH"]})
	_kq, loi3 = _chay(g3, "pos_chuyen_tien", "HDB-26-11-00292", "HDB-26-11-00295")
	dung("khoản không thuộc bill cũ thì không chuyển tự động", "không thuộc bill đã huỷ" in (loi3 or ""))


@ca("v628 TH3 chạy thật: tiền bill cũ đã sang bill mới thì phiếu hoàn của bill cũ không tính khoản đó nữa")
def _th3_khong_hoan_hai_lan():
	moi = _bill("HDB-26-11-00295", "TCVURLV8", "TCV", grand_total=1130000, vgb_ma_tham_chieu="FT26306111111111")
	g = _the_gioi(QLCH, [_bill_cu_th3(), moi])
	(tong, ds), loi = _chay(g, "tien_da_sang_bill_khac", "HDB-26-11-00292", ["BT-SOL"])
	la("không lỗi", loi, None)
	la("1.130.000 đã sang bill mới", (tong, ds), (1130000.0, ["HDB-26-11-00295"]))
	g2 = _the_gioi(QLCH, [_bill_cu_th3(), _bill("HDB-26-11-00295", "TCVURLV8", "TCV", vgb_huy=1,
		vgb_ma_tham_chieu="FT26306111111111")])
	(tong2, _d), _l = _chay(g2, "tien_da_sang_bill_khac", "HDB-26-11-00292", ["BT-SOL"])
	la("bill mới cũng đã huỷ thì không tính", tong2, 0.0)


# ------------------------------------------------------------ chạy thật TH1


@ca("v628 TH1 chạy thật: khoản mang mã NVHCXVC4 không bill nào lưu, quá 15 phút thì thu ngân NVH gắn được kèm câu")
def _th1_qua_han():
	moi = _bill("HDB-26-11-00050", "NVHDQ6FJ", "NVHTN", grand_total=40000)
	g = _the_gioi(QUAY, [moi], bay_gio="2026-11-01 12:20:00")
	_kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00050", "BT-NVH")
	la("không lỗi", loi, None)
	si = g["_hd"]["HDB-26-11-00050"]
	la("giữ số tham chiếu", si.get("vgb_ma_tham_chieu"), "FT26305222222222")
	dung("ghi chú nói bill mất trước khi lưu", "Chưa có bill nào lưu mã NVHCXVC4" in si.get("vgb_ghi_chu_doi_soat", ""))


@ca("v628 TH1 chạy thật: chưa đủ 15 phút thì vẫn chặn, vì bill đang hiện mã QR có thể sắp lưu")
def _th1_chua_han():
	moi = _bill("HDB-26-11-00050", "NVHDQ6FJ", "NVHTN", grand_total=40000)
	g = _the_gioi(QUAY, [moi], bay_gio="2026-11-01 12:05:00")
	_kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00050", "BT-NVH")
	dung("bị chặn và nói chờ 15 phút", "15 phút" in (loi or ""))
	la("bill không đổi", g["_hd"]["HDB-26-11-00050"].get("vgb_ma_tham_chieu"), "NVHDQ6FJ")


@ca("v628 TH1 chạy thật: mã đã có bill đang sống lưu thì không bao giờ nhả, dù quá hạn")
def _th1_co_bill_song():
	moi = _bill("HDB-26-11-00050", "NVHDQ6FJ", "NVHTN", grand_total=40000)
	cu = _bill("HDB-26-11-00049", "NVHCXVC4", "NVHTN", grand_total=40000)
	g = _the_gioi(QUAY, [moi, cu], bay_gio="2026-11-01 18:00:00")
	_kq, loi = _chay(g, "pos_gan_tien", "HDB-26-11-00050", "BT-NVH")
	dung("bị chặn, nói bill đang giữ", "HDB-26-11-00049" in (loi or ""))


def _doc_tien_hoan(g, bill, theo_tc=None):
	"""Chạy THẬT hoan_tien._tien_da_nhan với ban_hang giả mang hàm thật
	tien_da_sang_bill_khac đã nạp trong thế giới `g`."""
	import vagabond
	from vagabond import hoan_tien, ma_bill

	bh = types.ModuleType("vagabond.ban_hang")
	bh._sepay_theo_don = lambda shop, ds: {"SOL3D4A9": {"nhan": 1130000.0, "gd": ["BT-SOL"]}}
	bh.cfg = lambda: types.SimpleNamespace(pancake_shop_id="67355")
	bh.RE_MA_BILL = ma_bill.RE_MA
	bh._sepay_theo_tham_chieu = lambda tc: dict((theo_tc or {}).get(tc) or {})
	bh.tien_da_sang_bill_khac = lambda a, b: _chay(g, "tien_da_sang_bill_khac", a, b)[0]
	with um.patch.dict(sys.modules, {"vagabond.ban_hang": bh}), \
			um.patch.object(vagabond, "ban_hang", bh, create=True):
		return hoan_tien._tien_da_nhan(_Si(bill))


@ca("v628 TH3 chạy thật: phiếu hoàn của bill cũ đọc tiền đã nhận, trừ khoản đã chuyển sang bill mới")
def _th3_hoan_doc_tien():
	cu = _bill_cu_th3()
	truoc = _the_gioi(QLCH, [cu, _bill("HDB-26-11-00295", "TCVURLV8", "TCV")])
	la("chưa chuyển: bill cũ còn 1.130.000", _doc_tien_hoan(truoc, cu), 1130000.0)
	sau = _the_gioi(QLCH, [cu, _bill("HDB-26-11-00295", "TCVURLV8", "TCV", vgb_ma_tham_chieu="FT26306111111111")])
	la("đã chuyển: bill cũ còn 0, không hoàn hai lần", _doc_tien_hoan(sau, cu), 0.0)


@ca("v628 TH2: bill gắn tay bằng số tham chiếu vẫn đọc ra tiền đã nhận, nút Chuyển lại tiền dư tính đúng phần thừa")
def _th2_tham_chieu():
	moi = _bill("HDB-26-11-00149", "NVHWFMLT", "NVHTN", grand_total=290000, vgb_ma_tham_chieu="FT26305333333333")
	g = _the_gioi(QLCH, [moi])
	nhan = _doc_tien_hoan(g, dict(moi, custom_pancake_display_id="NVHWFMLT"),
		{"FT26305333333333": {"nhan": 405000.0, "gd": ["BT-X"]}})
	la("đọc ra 405.000 qua số tham chiếu", nhan, 405000.0)
	from vagabond import hoan_tien

	duoc, tran, _nhac = hoan_tien.tran_tien_du(nhan, 290000)
	la("phần thừa 115.000 chuyển lại được", (bool(duoc), tran), (True, 115000))
