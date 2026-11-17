"""v667 Tiền nộp thừa trả qua OnePay (Loan Anh 17/11/2026).

Ca thật: đơn Pancake 97790 (HDB-26-11-03188, 770.000 đ). Khách trả OnePay
1.650.000 đ ngày 14/11 ở đơn cũ 97615 (2 bánh); huỷ 1 bánh thì bánh còn lại
sang số đơn mới 97790. Bảng kê OnePay có dòng S67355O97615T100622 1.650.000 đ,
đang "Không thấy chứng từ". Nút "Chuyển lại tiền dư" chỉ đếm SePay nên báo dư
0 đ. Anh Việt chốt: tiền OnePay chỉ tính theo bảng kê đã về, nối theo số đơn;
đơn bị đổi số thì Sales chọn đơn cũ, máy kiểm đúng khách và chưa dùng.

Ca chạy CHÍNH các hàm của hoan_tien với DB giả ở biên; màn Sales chạy thật
trong node (hanh_vi/tien_du_onepay_667.js).
"""

import json
import os
import subprocess
import sys
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import hoan_tien as ht
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

SI_NAME = "HDB-26-11-03188"
DONG = [
	# Dòng thật của bảng kê (đọc trên site 17/11/2026).
	dict(name="85j5koug8o", ma_tham_chieu="S67355O97615T100622", tien_hang=1650000, sales_invoice="", ngay="2026-11-14"),
	# Đơn khác số đuôi giống (197615) và đơn khác hẳn: không được tính.
	dict(name="d2", ma_tham_chieu="S67355O197615T090000", tien_hang=500000, sales_invoice="", ngay="2026-11-14"),
	# Dòng cùng đơn cũ nhưng kế toán đã nối vào hoá đơn KHÁC: tiền của hoá đơn đó.
	dict(name="d3", ma_tham_chieu="S67355O97615T100700", tien_hang=100000, sales_invoice="HDB-KHAC", ngay="2026-11-14"),
]


def _si(**doi):
	d = dict(name=SI_NAME, docstatus=1, vgb_huy=0, grand_total=770000, customer="Khách lẻ Online",
		custom_pancake_display_id="97790", remarks="Pancake #97790 - Ms.Hảo - 0916220439",
		posting_date="2026-11-17", vgb_pt_thanh_toan="OnePay", custom_hddt_so="")
	d.update(doi)
	return SimpleNamespace(get=lambda k, m=None: d.get(k, m), **d)


@ca("v667 số đơn người gõ: chỉ chữ số, bỏ #, bỏ số 0 đầu; chữ lạ thì rỗng")
def _so_don():
	la("số", ht.so_don_hop_le(" #97615 "), "97615")
	la("số 0 đầu", ht.so_don_hop_le("097615"), "97615")
	la("chữ", ht.so_don_hop_le("S67355O97615T1"), "")
	la("trống", ht.so_don_hop_le(""), "")


@ca("v667 cùng khách: so 9 số cuối, thiếu một bên thì không nhận")
def _cung_khach():
	dung("0916 và +84916", ht.cung_khach("0916220439", "+84 916 220 439"))
	dung("khác số", not ht.cung_khach("0916220439", "0916220438"))
	dung("thiếu số", not ht.cung_khach("", "0916220439"))


@ca("v667 tiền OnePay của đơn 97790 chọn đơn cũ 97615: 1.650.000; không lấy đơn 197615, không lấy dòng đã nối hoá đơn khác")
def _tien_onepay():
	tong, ma = ht.tien_onepay_cua_don(["97790", "97615"], DONG, SI_NAME)
	la("tổng", tong, 1650000)
	la("mã", ma, ["S67355O97615T100622"])
	tong, _m = ht.tien_onepay_cua_don(["97790"], DONG, SI_NAME)
	la("chưa chọn đơn cũ: 0", tong, 0)
	la("dòng đã nối chính hoá đơn này thì tính dù mã khác",
		ht.tien_onepay_cua_don(["97790"], [dict(DONG[2], sales_invoice=SI_NAME)], SI_NAME)[0], 100000)
	la("phần dư", ht.tran_tien_du(1650000, 770000)[:2], (True, 880000))


class _D(dict):
	__getattr__ = dict.get


def _gia(si, phieu=(), si_cua_don_cu=None, sdt_pancake="0916220439", sql=None):
	"""Biên Frappe giả cho xem_tien_du / tao_tien_du / _kiem_don_cu."""
	ghi = {"sql": [], "insert": [], "lock": []}
	bo = ExitStack()

	def throw(m, *a, **k):
		raise ValueError(m)

	def db_sql(q, args=None, as_dict=False):
		ghi["sql"].append(q)
		if "get_lock" in q:
			ghi["lock"].append(("get", args[0]))
			return [[1]]
		if "release_lock" in q:
			ghi["lock"].append(("release", args[0]))
			return [[1]]
		if "don_tra_tien=" in q:
			return [_D(p) for p in phieu if p.get("don_tra_tien") == args[0] and p["trang_thai"] != "Da huy"]
		if "where hoa_don=" in q:
			return [_D(p) for p in phieu if p.get("hoa_don") == args[0] and p["trang_thai"] != "Da huy"]
		return []

	def get_value(dt, f=None, fields=None, as_dict=False, **k):
		if dt == ht.SI and isinstance(f, dict):
			return si_cua_don_cu
		if dt == ht.DT and isinstance(f, dict):
			for p in phieu:
				if p.get("hoa_don") == f.get("hoa_don") and p["trang_thai"] != "Da huy":
					return _D(p)
			return None
		return None

	class _Doc(SimpleNamespace):
		def insert(self, **k):
			self.name = "HT-2026-01000"
			ghi["insert"].append(self.__dict__)

	fr = SimpleNamespace(
		throw=throw, get_doc=lambda a, b=None: si if not isinstance(a, dict) else _Doc(flags=SimpleNamespace(), **a),
		get_meta=lambda dt: SimpleNamespace(has_field=lambda f: True), session=SimpleNamespace(user="loananh@x"),
		log_error=lambda *a, **k: None, get_traceback=lambda: "",
		db=SimpleNamespace(sql=sql or db_sql, get_value=get_value, commit=lambda: None, exists=lambda *a: True),
	)
	bo.enter_context(patch.object(ht, "frappe", fr))
	# Máy CI không có requests: không nạp ban_hang thật, đặt mô đun giả ở chỗ
	# hoan_tien nạp _kiem_quyen_ban.
	bo.enter_context(patch.dict(sys.modules, {"vagabond.ban_hang": SimpleNamespace(_kiem_quyen_ban=lambda: None)}))
	bo.enter_context(patch.object(ht, "_tien_da_nhan", lambda s: 0.0))
	bo.enter_context(patch.object(ht, "_dong_onepay", lambda cac_so, n: [dict(d) for d in DONG]))
	bo.enter_context(patch.object(ht, "goi_y_don_cu", lambda s, toi_da=5: [{"so": "97615", "tien": 1650000.0, "ngay": "2026-11-14"}]))
	bo.enter_context(patch.object(ht, "_khach_tren_don", lambda n, kh=None: {"ten": "Ms.Hảo", "sdt": "0916220439"}))
	bo.enter_context(patch.object(ht, "_sdt_don_pancake", lambda so: sdt_pancake))
	bo.enter_context(patch.object(ht, "_bao_ke_toan", lambda h, s: (1, [])))
	return bo, ghi


@ca("v667 xem tiền dư đơn 97790: chưa chọn đơn cũ thì dư 0 và mời chọn đơn 97615; chọn rồi thì dư 880.000")
def _xem():
	si = _si()
	bo, _g = _gia(si)
	with bo:
		t = ht.xem_tien_du(SI_NAME)
		la("chưa dư", t["duoc"], 0)
		la("mời chọn đơn cũ", t["cho_chon_don_cu"], 1)
		la("gợi ý 97615", [g["so"] for g in t["goi_y_don_cu"]], ["97615"])
		t = ht.xem_tien_du(SI_NAME, don_cu="97615")
	la("dư", (t["duoc"], t["tran"], t["da_nhan"], t["onepay"], t["don_cu"]), (1, 880000, 1650000, 1650000, "97615"))
	la("đã chọn thì không mời nữa", t["cho_chon_don_cu"], 0)


@ca("v667 đơn cũ sai: khác khách, là chính đơn này, còn hoá đơn riêng, đã dùng cho phiếu khác thì từ chối và nói rõ")
def _don_cu_sai():
	si = _si()
	for nhan, kw, don, chu in (
		("khác số điện thoại", dict(sdt_pancake="0909000000"), "97615", "không cùng số điện thoại"),
		("chính đơn này", {}, "97790", "chính hoá đơn này"),
		("còn hoá đơn riêng", dict(si_cua_don_cu="HDB-26-11-02000"), "97615", "HDB-26-11-02000"),
		("đã dùng", dict(phieu=[dict(name="HT-9", hoa_don="HDB-X", don_tra_tien="97615", trang_thai="Cho chi")]),
			"97615", "HT-9"),
		("chữ", {}, "abc", "chỉ gồm chữ số"),
	):
		bo, _g = _gia(si, **kw)
		with bo:
			try:
				ht.xem_tien_du(SI_NAME, don_cu=don)
				loi = "KHONG NEM"
			except ValueError as e:
				loi = str(e)
		dung(nhan + ": " + loi, chu in loi)


@ca("v667 lập phiếu nộp thừa 880.000 từ đơn cũ: khoá hoá đơn và khoá đơn cũ TRƯỚC khi đọc, ghi số đơn cũ lên phiếu, nhả khoá")
def _tao():
	si = _si()
	bo, g = _gia(si)
	with bo:
		kq = ht.tao_tien_du(SI_NAME, ly_do="Khac", dien_giai="Khách huỷ 1 bánh", so_tien=880000, ten_tk="NGUYEN THI HAO",
			so_tk="0123456789", ngan_hang="MB", don_cu="97615")
	la("số tiền", kq["so_tien"], 880000)
	p = g["insert"][0]
	la("phiếu nộp thừa ghi đơn cũ", (p["loai_hoan"], p["don_tra_tien"], p["so_tien"]), (ht.LOAI_TIEN_DU, "97615", 880000))
	dung("diễn giải nói rõ", "đơn Pancake 97615" in p["dien_giai"])
	la("khoá rồi nhả đúng đơn cũ", g["lock"], [("get", "vgb_tien_du_don:97615"), ("release", "vgb_tien_du_don:97615")])
	thu_tu = [i for i, q in enumerate(g["sql"]) if "for update" in q or "get_lock" in q]
	dung("khoá hoá đơn là câu đầu tiên", "tabSales Invoice" in g["sql"][0] and "for update" in g["sql"][0])
	dung("đọc phiếu cũ và đơn cũ bằng câu đọc khoá", len(thu_tu) >= 4)


@ca("v667 bấm lập hai lần: lần sau đọc khoá thấy phiếu của lần trước và dừng, không ghi phiếu thứ hai")
def _hai_lan():
	si = _si()
	bo, g = _gia(si, phieu=[dict(name="HT-2026-01000", hoa_don=SI_NAME, don_tra_tien="97615", trang_thai="Cho chi")])
	with bo:
		nem("lần hai", lambda: ht.tao_tien_du(SI_NAME, ly_do="Khac", dien_giai="x", so_tien=880000, ten_tk="A",
			so_tk="1", ngan_hang="MB", don_cu="97615"), ValueError)
	la("không ghi phiếu", g["insert"], [])
	la("vẫn nhả khoá", g["lock"][-1], ("release", "vgb_tien_du_don:97615"))


@ca("v667 phiếu nộp thừa không có đơn cũ (chuyển khoản dư) đi đường cũ: không khoá đơn cũ, không ghi ô đơn cũ")
def _khong_don_cu():
	si = _si(vgb_pt_thanh_toan="Chuyển khoản")
	bo, g = _gia(si)
	with bo, patch.object(ht, "_tien_da_nhan", lambda s: 820000.0):
		ht.tao_tien_du(SI_NAME, ly_do="Khac", dien_giai="Ship", so_tien=50000, ten_tk="A", so_tk="1", ngan_hang="MB")
	la("không khoá đơn cũ", g["lock"], [])
	la("ô đơn cũ trống", g["insert"][0]["don_tra_tien"], None)


@ca("v667 màn kế toán: thấy OnePay đã về theo bảng kê và phần nộp thừa máy tính, cùng hàm với lúc Sales lập")
def _ke_toan():
	import inspect
	than = inspect.getsource(ht.chi_tiet)
	dung("đọc OnePay theo đơn cũ ghi trên phiếu", '_onepay_da_ve(si, d.get("don_tra_tien")' in than)
	dung("phần nộp thừa cùng một hàm", "_tien_da_nhan_tien_du(si" in than and "tran_tien_du(" in than)


@ca("v667 ô 'Đơn Pancake khách đã trả tiền' khai trong mã nguồn, có neo, chỉ đọc")
def _truong():
	o = [f for f in ht.TRUONG_MOI[ht.DT] if f["fieldname"] == "don_tra_tien"]
	la("một ô", len(o), 1)
	la("neo và chỉ đọc", (o[0]["insert_after"], o[0]["read_only"]), ("diem_ban", 1))


@ca("v667 chạy thật màn Sales trong node: chạm đơn cũ gợi ý, gõ tay, đơn không OnePay, đơn dư sẵn")
def _man():
	js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hanh_vi", "tien_du_onepay_667.js")
	r = subprocess.run(["node", js], capture_output=True, text=True, timeout=60)
	try:
		kq = json.loads((r.stdout or "").strip().splitlines()[-1])
	except Exception:
		kq = {"dat": 0, "hong": 1, "loi": [(r.stderr or r.stdout)[:500]]}
	la("hỏng", kq["loi"], [])
	la("đạt đủ", kq["dat"], 4)
