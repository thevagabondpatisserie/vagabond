"""v666 Hoá đơn điều chỉnh của nhà cung cấp trên màn Đối chiếu mua.

Ca thật (anh Việt 17/11/2026): Gourmet Partner, hoá đơn gốc C26TGP số 33387
ngày 01/10 (20 KG bơ x 460.000 = 9.200.000 đ, sai giá), hoá đơn điều chỉnh
giảm số 39339 ngày 13/11 (-20 KG x 60.000 = -1.200.000 đ), phiếu nhập
PNK-2026-00803 nhận 2 Thùng x 4.000.000 = 8.000.000 đ. Màn Đối chiếu coi tờ
điều chỉnh như một lần nhập hàng âm (báo lệch đơn vị, lệch -9,2 triệu), tờ gốc
thì lệch 1,2 triệu, Thu mua không nối được tờ nào.

Ca kiểm chạy CHÍNH hàm xử lý (hd_dieu_chinh.thong_tin, doi_chieu_mua.so_sanh,
noi_phieu, chuan_bi_ghi_so) với DB giả ở biên.
"""

from contextlib import ExitStack
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import buoc_hoa_don_mua as bh
from vagabond import doi_chieu_mua as dc
from vagabond import hd_dieu_chinh as hdc
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

MST = "0315194856"

# M-Invoice: gốc, điều chỉnh, và mấy tờ dễ nhầm.
MI = {
	"MI-GOC": dict(name="MI-GOC", so_hd="00033387", ky_hieu="C26TGP", mst_doi_tac=MST, trang_thai="Gốc",
		hd_goc="", tong_tien=9936000, tien_truoc_thue=9200000),
	"MI-DC": dict(name="MI-DC", so_hd="39339", ky_hieu="C26TGP", mst_doi_tac=MST, trang_thai="Điều chỉnh",
		hd_goc="KH C26TGP - So 33387 - Ngay 2026-09-30", tong_tien=-1296000, tien_truoc_thue=-1200000),
	# Cùng MST, số đuôi 33387 nhưng là số khác (133387): LIKE bắt được, phải loại.
	"MI-133387": dict(name="MI-133387", so_hd="133387", ky_hieu="C26TGP", mst_doi_tac=MST, trang_thai="Gốc",
		hd_goc=""),
	# Cùng số 33387 nhưng ký hiệu khác: không phải gốc.
	"MI-KHAC-KH": dict(name="MI-KHAC-KH", so_hd="33387", ky_hieu="C25ABC", mst_doi_tac=MST, trang_thai="Gốc",
		hd_goc=""),
	# Nhà cung cấp khác cùng số 33387.
	"MI-NCC-KHAC": dict(name="MI-NCC-KHAC", so_hd="33387", ky_hieu="C26TGP", mst_doi_tac="0300000000",
		trang_thai="Gốc", hd_goc=""),
}

PI = {
	"HDM-GOC": dict(name="HDM-GOC", custom_minvoice_id="MI-GOC", custom_trang_thai_hddt="Gốc", supplier="GOURMET",
		total=9200000, grand_total=9936000, docstatus=0, vgb_huy=0, bill_no="33387", posting_date="2026-10-01",
		outstanding_amount=9936000),
	"HDM-DC": dict(name="HDM-DC", custom_minvoice_id="MI-DC", custom_trang_thai_hddt="Điều chỉnh", supplier="GOURMET",
		total=-1200000, grand_total=-1296000, docstatus=0, vgb_huy=0, bill_no="39339", posting_date="2026-11-13",
		outstanding_amount=-1296000),
	"HDM-133387": dict(name="HDM-133387", custom_minvoice_id="MI-133387", supplier="GOURMET", total=1, docstatus=1,
		vgb_huy=0, bill_no="133387"),
}


def _khop_like(v, mau):
	mau = str(mau)
	if mau.startswith("%") and mau.endswith("%"):
		return mau.strip("%") in str(v or "")
	if mau.startswith("%"):
		return str(v or "").endswith(mau[1:])
	if mau.endswith("%"):
		return str(v or "").startswith(mau[:-1])
	return str(v or "") == mau


def _loc(ds, filters):
	ra = []
	for r in ds:
		ok = True
		for k, v in (filters or {}).items():
			if isinstance(v, (list, tuple)):
				op, gt = v[0], v[1]
				if op == "like":
					ok = ok and _khop_like(r.get(k), gt)
				elif op == "<":
					ok = ok and r.get(k) is not None and r.get(k) < gt
				elif op == "in":
					ok = ok and r.get(k) in gt
			else:
				ok = ok and r.get(k) == v
		if ok:
			ra.append(dict(r))
	return ra


def _fr(mi=None, pi=None, doc=None):
	mi = deepcopy(mi or MI)
	for r in mi.values():
		r.setdefault("loai", "Đầu vào")
	pi = deepcopy(pi or PI)

	def get_value(dt, ten, f=None, as_dict=False, **k):
		kho = mi if dt == hdc.DT_HD else pi if dt == hdc.PI else {}
		if isinstance(ten, dict):
			ds = _loc(list(kho.values()), ten)
			r = ds[0] if ds else None
		else:
			r = kho.get(ten)
		if not r:
			return None
		if isinstance(f, (list, tuple)):
			return dict(r) if as_dict else [r.get(x) for x in f]
		return r.get(f)

	def get_all(dt, filters=None, fields=None, **k):
		kho = mi if dt == hdc.DT_HD else pi if dt == hdc.PI else {}
		ds = _loc(list(kho.values()), filters)
		for r in ds:
			for f in fields or []:
				r.setdefault(f, None)
		return ds

	def throw(m, *a, **k):
		raise ValueError(m)

	return SimpleNamespace(
		db=SimpleNamespace(get_value=get_value, exists=lambda *a, **k: True),
		get_all=get_all, throw=throw,
		get_doc=lambda dt, ten: doc[ten])


# ================================================================== THUẦN

@ca("v666 đọc chuỗi hoá đơn gốc M-Invoice: ký hiệu và số, bỏ số 0 đầu; chuỗi lạ thì không đoán")
def _doc_goc():
	la("chuỗi M-Invoice", hdc.doc_hd_goc("KH C26TGP - So 33387 - Ngay 2026-09-30"), {"ky_hieu": "C26TGP", "so": 33387})
	la("số có 0 đầu, có mẫu số", hdc.doc_hd_goc("KH 1C26TGP - So 00033387"), {"ky_hieu": "C26TGP", "so": 33387})
	la("Số có dấu", hdc.doc_hd_goc("KH C26TGP - Số 33387"), {"ky_hieu": "C26TGP", "so": 33387})
	la("cùng một nguồn với đối soát bán ra", hdc._ds.tach_goc("KH C26TGP - So 33387"), ("C26TGP", "33387"))
	la("chữ thường", hdc.doc_hd_goc("kh c26tgp - so 7"), {"ky_hieu": "C26TGP", "so": 7})
	la("trống", hdc.doc_hd_goc(""), None)
	la("không có số", hdc.doc_hd_goc("KH C26TGP"), None)
	la("số 0", hdc.doc_hd_goc("KH C26TGP - So 0"), None)


@ca("v666 tờ điều chỉnh: trạng thái Điều chỉnh và đọc được hoá đơn gốc; tờ thay thế, tờ gốc không phải")
def _la_dc():
	dung("điều chỉnh", hdc.la_to_dieu_chinh("Điều chỉnh", "KH C26TGP - So 33387"))
	dung("thay thế không phải", not hdc.la_to_dieu_chinh("Thay thế", "KH C26TGP - So 33387"))
	dung("gốc không phải", not hdc.la_to_dieu_chinh("Gốc", ""))
	dung("điều chỉnh mà không ghi gốc thì không đoán", not hdc.la_to_dieu_chinh("Điều chỉnh", ""))


@ca("v666 chọn tờ gốc: đúng số (không nhận 133387), ký hiệu khớp (bỏ mẫu số), không nhận chính tờ điều chỉnh, trùng hai tờ thì không đoán")
def _chon_goc():
	goc = {"ky_hieu": "C26TGP", "so": 33387}
	ung = [MI["MI-133387"], MI["MI-KHAC-KH"], dict(MI["MI-GOC"], ky_hieu="1C26TGP")]
	la("chọn đúng tờ gốc", hdc.chon_goc(goc, ung)["name"], "MI-GOC")
	la("tờ điều chỉnh khác cùng số không phải gốc",
		hdc.chon_goc(goc, [dict(MI["MI-DC"], so_hd="33387")]), None)
	la("hai tờ gốc trùng thì không đoán", hdc.chon_goc(goc, [MI["MI-GOC"], dict(MI["MI-GOC"], name="MI-GOC-2")]), None)


@ca("v666 tiền sau điều chỉnh: 9.200.000 + (-1.200.000) = 8.000.000; tờ điều chỉnh đã huỷ không tính")
def _tien_sau():
	la("ca Gourmet", hdc.tien_sau_dieu_chinh(9200000, [{"total": -1200000}]), 8000000.0)
	la("hai tờ, một đã huỷ", hdc.tien_sau_dieu_chinh(9200000, [{"total": -1200000}, {"total": -500000, "huy": 1}]), 8000000.0)
	la("điều chỉnh tăng", hdc.tien_sau_dieu_chinh(1000, [{"total": 200}]), 1200.0)


@ca("v666 ghi sổ tờ điều chỉnh chỉ khi tờ gốc đã ghi sổ; tờ gốc huỷ, chưa tìm thấy thì nói rõ")
def _ly_do():
	dung("chưa có gốc", "Chưa tìm thấy" in hdc.ly_do_chua_ghi_so(None))
	dung("gốc còn nháp", "Ghi sổ tờ gốc HDM-GOC trước" in hdc.ly_do_chua_ghi_so({"name": "HDM-GOC", "docstatus": 0}))
	dung("gốc huỷ", "đã huỷ" in hdc.ly_do_chua_ghi_so({"name": "HDM-GOC", "docstatus": 1, "huy": 1}))
	la("gốc đã ghi sổ", hdc.ly_do_chua_ghi_so({"name": "HDM-GOC", "docstatus": 1, "huy": 0}), None)


@ca("v666 bước xử lý: tờ điều chỉnh là Chờ ghi sổ, không phải Chờ nối phiếu nhập")
def _buoc():
	dong = [{"item_code": "NVLT00021", "purchase_receipt": "", "qua_kho": 1}]
	la("tờ thường còn dòng hàng chưa nối", bh.buoc_cua_to(dong), bh.B_CHUA_NOI)
	la("tờ điều chỉnh", bh.buoc_cua_to(dong, 0, 1), bh.B_CHO_GHI_SO)
	la("điều chỉnh mà thiếu mã vẫn báo thiếu mã", bh.buoc_cua_to([{"item_code": "", "qua_kho": 1}], 0, 1), bh.B_THIEU_MA)


# ================================================================== CHẠM HỆ (DB giả)

@ca("v666 tờ điều chỉnh HDM-DC tìm đúng tờ gốc HDM-GOC qua M-Invoice, tiền sau điều chỉnh 8.000.000, chưa ghi sổ được vì gốc còn nháp")
def _thong_tin_dc():
	with patch.object(hdc, "_frappe", lambda: _fr()):
		t = hdc.thong_tin("HDM-DC")
	la("là tờ điều chỉnh", t.get("la_dieu_chinh"), 1)
	la("số gốc", t.get("so_goc"), "C26TGP/33387")
	la("tờ gốc", (t.get("goc") or {}).get("name"), "HDM-GOC")
	la("tiền sau điều chỉnh", t.get("tien_sau"), 8000000.0)
	dung("chưa ghi sổ được: gốc còn nháp", "Ghi sổ tờ gốc HDM-GOC trước" in (t.get("loi") or ""))


@ca("v666 tờ gốc HDM-GOC thấy tờ điều chỉnh của nó, không lẫn tờ của NCC khác hay số 133387")
def _thong_tin_goc():
	mi = deepcopy(MI)
	# Tờ điều chỉnh của NCC khác trỏ cùng số 33387 và một tờ điều chỉnh số 133387.
	mi["MI-DC-NCC-KHAC"] = dict(name="MI-DC-NCC-KHAC", so_hd="5", ky_hieu="C26TGP", mst_doi_tac="0300000000",
		trang_thai="Điều chỉnh", hd_goc="KH C26TGP - So 33387")
	mi["MI-DC-133387"] = dict(name="MI-DC-133387", so_hd="6", ky_hieu="C26TGP", mst_doi_tac=MST,
		trang_thai="Điều chỉnh", hd_goc="KH C26TGP - So 133387")
	pi = deepcopy(PI)
	pi["HDM-DC-NCC-KHAC"] = dict(name="HDM-DC-NCC-KHAC", custom_minvoice_id="MI-DC-NCC-KHAC", total=-1, docstatus=0, vgb_huy=0)
	pi["HDM-DC-133387"] = dict(name="HDM-DC-133387", custom_minvoice_id="MI-DC-133387", total=-2, docstatus=0, vgb_huy=0)
	with patch.object(hdc, "_frappe", lambda: _fr(mi, pi)):
		t = hdc.thong_tin("HDM-GOC")
	la("đúng một tờ điều chỉnh", [x["name"] for x in t.get("cac_to") or []], ["HDM-DC"])
	la("tiền điều chỉnh", t.get("tien_dieu_chinh"), -1200000.0)
	la("tiền sau", t.get("tien_sau"), 8000000.0)
	with patch.object(hdc, "_frappe", lambda: _fr()):
		la("tờ không dính điều chỉnh", hdc.thong_tin("HDM-133387"), {})


@ca("v666 tờ điều chỉnh của tờ gốc ĐÃ HUỶ (vgb_huy) thì không tìm ra tờ gốc, không ghi sổ vào tờ đã huỷ")
def _goc_huy():
	pi = deepcopy(PI)
	pi["HDM-GOC"]["vgb_huy"] = 1
	with patch.object(hdc, "_frappe", lambda: _fr(None, pi)):
		t = hdc.thong_tin("HDM-DC")
	la("không có gốc", t.get("goc"), None)
	dung("báo chưa tìm thấy", "Chưa tìm thấy" in (t.get("loi") or ""))


def _doc_dc(docstatus=0):
	return SimpleNamespace(name="HDM-DC", docstatus=docstatus, is_return=1, supplier="GOURMET", return_against=None,
		items=[SimpleNamespace(idx=1, get=lambda k, d=None: "")], flags=SimpleNamespace())


@ca("v666 chuẩn bị ghi sổ: gốc còn nháp thì chặn; gốc đã ghi sổ thì tờ âm gắn return_against = tờ gốc")
def _chuan_bi():
	d = _doc_dc()
	with patch.object(hdc, "_frappe", lambda: _fr(doc={"HDM-DC": d})):
		nem("gốc còn nháp", lambda: hdc.chuan_bi_ghi_so("HDM-DC"), ValueError)
	la("chưa gắn gì", d.return_against, None)
	pi = deepcopy(PI)
	pi["HDM-GOC"]["docstatus"] = 1
	d = _doc_dc()
	with patch.object(hdc, "_frappe", lambda: _fr(None, pi, {"HDM-DC": d})):
		ra = hdc.chuan_bi_ghi_so("HDM-DC")
	la("gắn tờ gốc", ra.return_against, "HDM-GOC")
	# Dòng đang nối phiếu nhập thì không ghi sổ điều chỉnh.
	d = _doc_dc()
	d.items = [SimpleNamespace(idx=1, get=lambda k, dd=None: "PNK-1" if k == "purchase_receipt" else "")]
	with patch.object(hdc, "_frappe", lambda: _fr(None, pi, {"HDM-DC": d})):
		nem("dòng nối phiếu", lambda: hdc.chuan_bi_ghi_so("HDM-DC"), ValueError)
	with patch.object(hdc, "_frappe", lambda: _fr(None, pi, {"HDM-GOC": _doc_dc()})):
		nem("tờ thường không phải điều chỉnh", lambda: hdc.chuan_bi_ghi_so("HDM-GOC"), ValueError)


# Phiếu nhập PNK-2026-00803: 2 Thùng x 4.000.000, Thùng = 10.000 g (2 thùng 5 tấm 2 kg).
def _pnk():
	return {"PNK-803": [dict(name="R803", item_code="NVLT00021", item_name="Bơ tấm Echire", qty=2, rate=4000000,
		amount=8000000, uom="Thùng", stock_uom="Gram", conversion_factor=10000, stock_qty=20000)]}


def _dong_goc(sl=2, dvt="Thùng", hs=10000):
	"""Tờ gốc sau khi Thu mua quy dòng 20 KG về đơn vị phiếu nhập: 2 Thùng x 4.600.000."""
	return [dict(name="A", idx=1, item_code="NVLT00021", item_name="Bơ tấm Echire", qty=sl, rate=9200000 / sl,
		amount=9200000, uom=dvt, stock_uom="Gram", conversion_factor=hs, description="", purchase_receipt="",
		pr_detail="", vgb_mon_may_doan="", vgb_dvt_ncc="KG", ten_hang_ncc="Bơ lạt")]


def _gia_lap_dc(dieu_chinh, total=9200000):
	bo = ExitStack()
	bo.enter_context(patch.object(dc, "_dong_pnk", lambda p: deepcopy(_pnk()[p])))
	bo.enter_context(patch.object(dc, "_dong_hd", lambda n: deepcopy(_dong_goc())))
	bo.enter_context(patch.object(dc, "_vuot_lech_gia_duoc", lambda: True))
	bo.enter_context(patch.object(dc, "_kiem_quyen", lambda: None))
	bo.enter_context(patch.object(dc, "_lam_duoc", lambda: True))
	bo.enter_context(patch.object(dc, "_dieu_chinh", lambda n: deepcopy(dieu_chinh)))

	def get_value(dt, n, o=None, as_dict=False, **k):
		if dt == "Purchase Receipt":
			return "GOURMET"
		if dt == "Purchase Invoice":
			return {"name": n, "supplier": "GOURMET", "total": total, "docstatus": 0}
		return None

	def throw(m, *a, **k):
		raise ValueError(m)

	bo.enter_context(patch.object(dc, "frappe", SimpleNamespace(
		get_all=lambda *a, **k: [], parse_json=lambda s: __import__("json").loads(s), throw=throw,
		get_doc=lambda dt, n: SimpleNamespace(docstatus=0, update_stock=0, supplier="GOURMET"),
		db=SimpleNamespace(get_single_value=lambda *a: 0, get_value=get_value))))
	return bo


@ca("v666 tờ gốc 33387 so với PNK-2026-00803 bằng tiền SAU điều chỉnh: khớp 0 đ; không có điều chỉnh thì lệch 1.200.000")
def _so_sanh_goc():
	with _gia_lap_dc({}):
		s = dc.so_sanh("HDM-GOC", ["PNK-803"])
	la("không điều chỉnh: lệch đúng 1,2 triệu", s["lech_tien"], 1200000.0)
	la("không điều chỉnh: không khớp", s["khop"], 0)
	dc_info = {"cac_to": [{"name": "HDM-DC", "total": -1200000.0, "bill_no": "39339", "huy": 0}],
		"tien_dieu_chinh": -1200000.0, "tien_sau": 8000000.0}
	with _gia_lap_dc(dc_info):
		s = dc.so_sanh("HDM-GOC", ["PNK-803"])
	la("có điều chỉnh: lệch 0", s["lech_tien"], 0.0)
	la("có điều chỉnh: khớp", s["khop"], 1)
	la("trả tiền điều chỉnh cho màn hình", s["tien_dieu_chinh"], -1200000.0)
	la("trả tiền sau điều chỉnh, màn hình không tự cộng", s["tien_hd_sau"], 8000000.0)
	la("nêu tờ điều chỉnh", [t["name"] for t in s["cac_to_dieu_chinh"]], ["HDM-DC"])
	la("cùng đơn vị Thùng: không lệch đơn vị", s["so_lech_dvt"], 0)


@ca("v666 tờ điều chỉnh không đi đường phiếu nhập: so sánh và nối phiếu đều từ chối, nói rõ phải làm gì")
def _dc_khong_noi():
	t = {"la_dieu_chinh": 1, "goc": {"name": "HDM-GOC", "docstatus": 0}, "so_goc": "C26TGP/33387"}
	with _gia_lap_dc(t, total=-1200000):
		la("so sánh nói mở tờ gốc", "Mở tờ gốc" in _loi(lambda: dc.so_sanh("HDM-DC", ["PNK-803"])), True)
		la("nối phiếu nói không nối", "không nối phiếu nhập" in _loi(lambda: dc.noi_phieu("HDM-DC", ["PNK-803"])), True)


def _loi(ham):
	try:
		ham()
	except ValueError as e:
		return str(e)
	return "KHONG NEM"


@ca("v666 màn danh sách nhận tờ điều chỉnh bằng ô trạng thái hoá đơn điện tử trên chính tờ")
def _ds_nhanh():
	dung("điều chỉnh", dc._la_dieu_chinh_nhanh({"custom_trang_thai_hddt": "Điều chỉnh"}))
	dung("gốc", not dc._la_dieu_chinh_nhanh({"custom_trang_thai_hddt": "Gốc"}))
	dung("trống", not dc._la_dieu_chinh_nhanh({}))


@ca("v666 máy không có Frappe (CI) hay đọc M-Invoice hỏng: màn Đối chiếu coi như không dính điều chỉnh, không vỡ")
def _hong_khong_vo():
	with patch.object(dc, "frappe", SimpleNamespace(log_error=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")),
			get_traceback=lambda: "")):
		with patch.object(hdc, "thong_tin", lambda n: (_ for _ in ()).throw(RuntimeError("hong"))):
			la("rỗng", dc._dieu_chinh("HDM-DC"), {})


class _Dong(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


def _sua_dvt(dong, dvt, quy_doi, bang=None):
	"""Chạy đúng hàm nút "Quy về" / "Đổi đơn vị" trên một tờ nháp giả."""
	bang = bang or {"Kg": 1000.0, "Thùng": 10000.0, "Gram": 1.0}
	doc = SimpleNamespace(name="HDM-GOC", docstatus=0, items=[_Dong(dong)], flags=SimpleNamespace(), luu=[])
	doc.save = lambda: doc.luu.append(1)

	def throw(m, *a, **k):
		raise ValueError(m)

	def get_value(dt, f, o=None, **k):
		if dt == "UOM Conversion Detail":
			for ten in bang:
				if ten.lower() == str(f.get("uom")).lower():
					return ten if o == "uom" else bang[ten]
		return None

	with ExitStack() as bo:
		bo.enter_context(patch.object(dc, "_kiem_quyen", lambda: None))
		bo.enter_context(patch.object(dc, "_lam_duoc", lambda: True))
		bo.enter_context(patch.object(dc.dvt_mua, "he_so_cua_mon", lambda m, d: get_value("UOM Conversion Detail", {"uom": d})))
		bo.enter_context(patch.object(dc, "frappe", SimpleNamespace(
			throw=throw, get_doc=lambda dt, n: doc, parse_json=lambda s: __import__("json").loads(s),
			db=SimpleNamespace(get_value=get_value, commit=lambda: None))))
		kq = dc.sua_don_vi("HDM-GOC", ["1"], dvt, quy_doi=quy_doi)
	return kq, doc.items[0]


def _dong_kg():
	# Tờ gốc 33387 đã được đưa về đúng đơn vị NCC: 20 KG x 460.000 = 9.200.000.
	return dict(name="A", idx=1, item_code="NVLT00021", qty=20, rate=460000, price_list_rate=460000, amount=9200000,
		uom="Kg", conversion_factor=1000, purchase_receipt="")


@ca("v666 quy 20 Kg về Thùng theo phiếu nhập: thành 2 Thùng x 4.600.000, thành tiền 9.200.000 giữ nguyên, lượng kho 20.000 g giữ nguyên")
def _quy_doi():
	kq, d = _sua_dvt(_dong_kg(), "Thùng", 1)
	la("đã sửa một dòng", kq["da_sua"], 1)
	la("đơn vị", d.uom, "Thùng")
	la("hệ số", d.conversion_factor, 10000.0)
	la("số lượng quy đổi", d.qty, 2.0)
	la("đơn giá tính lại", d.rate, 4600000.0)
	la("giá niêm yết theo đơn giá mới", d.price_list_rate, 4600000.0)
	la("thành tiền giữ nguyên", d.amount, 9200000)
	la("lượng kho giữ nguyên", d.qty * d.conversion_factor, 20000.0)


@ca("v666 nút Đổi đơn vị cũ (không quy đổi) vẫn giữ số lượng và giá: 20 Kg thành 20 Thùng, đây là cái bẫy nên màn phải dùng Quy về")
def _doi_khong_quy():
	kq, d = _sua_dvt(_dong_kg(), "Thùng", 0)
	la("số lượng giữ", d.qty, 20)
	la("giá giữ", d.rate, 460000)
	la("lượng kho thành 200.000 g", d.qty * d.conversion_factor, 200000.0)


@ca("v666 đưa dòng 20 Thùng (Uyên đổi nhầm) về đơn vị NCC ghi KG: lấy đúng tên Kg trong bảng quy đổi, số lượng và tiền giữ nguyên")
def _ve_dvt_ncc():
	d0 = dict(_dong_kg(), uom="Thùng", conversion_factor=10000)
	kq, d = _sua_dvt(d0, "KG", 0)
	la("tên đơn vị theo bảng quy đổi, không theo chữ NCC", d.uom, "Kg")
	la("hệ số Kg", d.conversion_factor, 1000.0)
	la("số lượng giữ 20", d.qty, 20)
	la("tiền giữ", d.amount, 9200000)


@ca("v666 quy đổi dòng đã nối phiếu nhập thì từ chối, không đổi gì")
def _quy_doi_da_noi():
	nem("đã nối", lambda: _sua_dvt(dict(_dong_kg(), purchase_receipt="PNK-803"), "Thùng", 1), ValueError)


@ca("v666 ghi sổ tờ điều chỉnh giảm (đơn giá 60.000 đ/kg phần chênh) không ghi đè bảng giá nhập của bơ")
def _bang_gia_bo_qua_tra():
	from vagabond import bang_gia_nhap as bg
	ghi = []
	doc = _Dong(name="HDM-DC", is_return=1, posting_date="2026-11-13", bill_no="39339",
		items=[_Dong(item_code="NVLT00021", uom="Kg", conversion_factor=1000, rate=60000, description="")])
	with patch.object(bg, "_ghi_mot_dong", lambda *a: ghi.append(a) or "sua"), \
			patch.object(bg, "ly_do_bo_qua", lambda *a: None):
		kq = bg._chay(doc)
		la("tờ trả: không ghi dòng nào", ghi, [])
		la("ghi rõ lý do bỏ qua", kq["bo_qua"], {"tờ trả lại hoặc điều chỉnh": 1})
		doc.is_return = 0
		bg._chay(doc)
		la("tờ mua thường vẫn ghi bảng giá", len(ghi), 1)


# ---------------------------------------------------------- chạy thật màn hình

def _man(xem, so_sanh=None, bam="", dat=None):
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	import json
	import os
	import subprocess
	js = os.path.join(t252.GOC, "vagabond", "khung", "kiem_thu", "gia_lap_dcm.js")
	r = subprocess.run(["node", js, json.dumps(xem), json.dumps(so_sanh or {}), bam, json.dumps(dat or {})],
		capture_output=True, text=True, timeout=60)
	if r.returncode != 0:
		raise AssertionError("giả lập màn lỗi: " + (r.stderr or "").strip()[:600])
	return json.loads(r.stdout)


def _xem_dc(**doi):
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	dc_info = {"la_dieu_chinh": 1, "so_goc": "C26TGP/33387", "tien": -1200000, "tien_sau": 8000000,
		"goc": {"name": "HDM-26-10-00021", "docstatus": 1, "total": 9200000}}
	dc_info.update(doi.pop("dc", {}))
	return t252._xem_mau(hd={"name": "HDM-26-11-00218", "supplier_name": "GOURMET PARTNER", "posting_date": "2026-11-13",
		"grand_total": -1296000, "docstatus": 0, "update_stock": 0, "bill_no": "39339"},
		nhom="cho_ghi_so", goi_y=[], dieu_chinh=dc_info, **doi)


@ca("v666 chạy thật màn: tờ điều chỉnh hiện thẻ tờ gốc, tiền sau điều chỉnh, nút ghi sổ; không có khối chọn phiếu nhập")
def _man_dc():
	ra = _man(_xem_dc(ghi_so_duoc=1))
	k = ra["khung"]
	dung("nói số hoá đơn gốc", "C26TGP/33387" in k)
	dung("tờ gốc đã ghi sổ", "HDM-26-10-00021 · đã ghi sổ" in k)
	dung("tiền sau điều chỉnh 8.000.000", "8.000.000" in k or "8,000,000" in k)
	dung("nút mở tờ gốc", 'data-dcmgoc="HDM-26-10-00021"' in k)
	dung("không gợi ý phiếu nhập", "PNK-27" not in k and "Chọn phiếu nhập" not in k)
	dung("nút ghi sổ điều chỉnh", 'id="dcmGhiDc"' in ra["footer"])
	ra = _man(_xem_dc(ghi_so_duoc=1), bam="dcmGhiDc")
	la("bấm gọi đúng cửa ghi sổ điều chỉnh với đúng tờ",
		[x["a"] for x in ra["api_args"] if x["m"] == "vagabond.doi_chieu_mua.ghi_so_dieu_chinh"],
		[{"name": "HDM-26-11-00218"}])
	la("ghi sổ xong quay về danh sách", ra["ve_danh_sach"], 1)


@ca("v666 chạy thật màn: tờ gốc còn nháp thì tờ điều chỉnh không có nút ghi sổ, nói rõ ghi sổ tờ gốc trước; thu mua không thấy nút ghi sổ")
def _man_dc_chan():
	ra = _man(_xem_dc(ghi_so_duoc=1, dc={"goc": {"name": "HDM-26-10-00021", "docstatus": 0, "total": 9200000},
		"loi": "Ghi sổ tờ gốc HDM-26-10-00021 trước (nối phiếu nhập rồi ghi sổ), rồi mới ghi sổ tờ điều chỉnh này."}))
	dung("không nút ghi sổ", "dcmGhiDc" not in ra["footer"])
	dung("nói ghi sổ tờ gốc trước", "Ghi sổ tờ gốc HDM-26-10-00021 trước" in ra["khung"])
	dung("tờ gốc còn nháp", "· còn nháp" in ra["khung"])
	ra = _man(_xem_dc(ghi_so_duoc=0))
	dung("thu mua: không nút ghi sổ, có lời nhắn kế toán", "dcmGhiDc" not in ra["footer"] and "Kế toán ghi sổ" in ra["footer"])


def _dong_kg_man(**doi):
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	d = t252._dong_man(item_code="NVLT00021", item_name="Bơ tấm Echire", sl_hd=20, gia_hd=460000, tien_hd=9200000,
		co_phieu=1, sl_pnk=2, sl_pnk_nhan=2, gia_pnk=4000000, dvt_hd="Kg", dvt_pnk="Thùng", dvt_kho="Gram",
		dvt_ncc="KG", ton_hd=20000, ton_pnk=20000, hs_pnk=10000, lech_dvt=1, lech_sl=0, gia_kho_hd=460, gia_kho_pnk=400,
		lech_gia=60, da_noi="")
	d.update(doi)
	return d


@ca("v666 chạy thật màn: 20 Kg so với 2 Thùng cùng 20.000 g thì nút là Quy về 2 Thùng × 4.600.000, không phải đổi tên đơn vị giữ số 20")
def _man_quy_doi():
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	s = t252._so_sanh_mau([_dong_kg_man()], so_lech_dvt=1, tien_hd=9200000, tien_pnk=8000000)
	ra = _man(t252._xem_mau(), s, "", {"dcmPhieu": ["PNK-27"]})
	html = ra["so_sanh"]
	if not html:
		ra = _man(t252._xem_mau(), s)
		html = ra["so_sanh"] or ra["khung"]
	dung("có nút quy đổi", 'data-quydoi="1"' in html)
	dung("nói rõ 2 Thùng", "Quy về 2 Thùng" in html)
	dung("không còn nút đổi tên đơn vị giữ số", "Đổi đơn vị dòng này thành Thùng" not in html)
	s = t252._so_sanh_mau([_dong_kg_man(ton_pnk=40000, sl_pnk=4)], so_lech_dvt=1)
	html = _man(t252._xem_mau(), s)["so_sanh"]
	dung("lượng kho khác nhau: không quy đổi, giữ nút cũ", 'data-quydoi="1"' not in html and "Đổi đơn vị dòng này thành Thùng" in html)


@ca("v666 chạy thật màn: dòng 20 Thùng (đổi nhầm) lệch số lượng với phiếu 2 Thùng thì có nút đưa về đơn vị hoá đơn điện tử KG")
def _man_ve_kg():
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	d = _dong_kg_man(dvt_hd="Thùng", ton_hd=200000, lech_dvt=0, lech_sl=18, gia_kho_hd=46, lech_gia=0)
	html = _man(t252._xem_mau(), t252._so_sanh_mau([d]))["so_sanh"]
	dung("có nút đưa về KG", "Đưa về đơn vị trên hoá đơn điện tử (KG)" in html)
	html = _man(t252._xem_mau(), t252._so_sanh_mau([_dong_kg_man(dvt_hd="KG", ton_hd=20000, lech_dvt=0, lech_sl=0, lech_gia=0)]))["so_sanh"]
	dung("dòng đã đúng đơn vị NCC: không hiện nút", "Đưa về đơn vị trên hoá đơn điện tử" not in html)


@ca("v666 chạy thật màn: bảng so sánh tờ gốc có dòng hoá đơn điều chỉnh và tiền hàng sau điều chỉnh lấy đúng số máy trả, không tự cộng")
def _man_tien_sau():
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	s = t252._so_sanh_mau([_dong_kg_man(dvt_hd="Thùng", sl_hd=2, ton_hd=20000, lech_dvt=0)], tien_hd=9200000,
		tien_pnk=8000000, lech_tien=0, khop=1, tien_dieu_chinh=-1200000, tien_hd_sau=7999999,
		cac_to_dieu_chinh=[{"name": "HDM-DC", "bill_no": "39339", "total": -1200000}])
	html = _man(t252._xem_mau(), s)["so_sanh"]
	dung("nêu tờ điều chỉnh", "HDM-DC (số 39339)" in html)
	dung("tiền sau đúng số máy trả", "7.999.999" in html or "7,999,999" in html)


# ---------------------------------------------------------- Codex #578 vòng 1

@ca("Codex #578: tờ điều chỉnh có dòng dịch vụ thì nút ghi sổ mở màn chọn tài khoản, không gửi thẳng thiếu tài khoản")
def _dc_chi_phi_man():
	dong = [{"ten": "R1", "idx": 1, "ten_hang": "Phí giao hàng điều chỉnh", "tien": -50000, "sua_duoc": 1, "goi_y": "6417 - Chi phí", "tk": ""}]
	ra = _man(_xem_dc(ghi_so_duoc=1, ht_dong=dong), bam="dcmGhiDc")
	dung("đọc dòng hạch toán trước", "vagabond.hach_toan_thang.xem" in ra["api"])
	la("không gửi thẳng ghi sổ điều chỉnh", [x for x in ra["api"] if x == "vagabond.doi_chieu_mua.ghi_so_dieu_chinh"], [])
	dung("mở màn Hạch toán có nút ghi sổ với hạch toán", "dcmHtGhi" in ra["footer"])
	ra = _man(_xem_dc(ghi_so_duoc=1, ht_dong=[dict(dong[0], sua_duoc=0)]), bam="dcmGhiDc")
	la("tờ chỉ có hàng kho: ghi sổ điều chỉnh thẳng", [x["a"] for x in ra["api_args"]
		if x["m"] == "vagabond.doi_chieu_mua.ghi_so_dieu_chinh"], [{"name": "HDM-26-11-00218"}])


@ca("Codex #578: màn Hạch toán ghi sổ tờ điều chỉnh qua ghi_so_thang thì tài khoản đã chọn tới đúng cửa ghi sổ có hạch toán")
def _dc_chi_phi_tk():
	nhan = []
	doc = SimpleNamespace(name="HDM-DC", docstatus=0, items=[], status="Debit Note Issued", get=lambda k, d=None: "HDM-GOC" if k == "return_against" else d)

	def throw(m, *a, **k):
		raise ValueError(m)

	with ExitStack() as bo:
		bo.enter_context(patch.object(dc, "_kiem_quyen", lambda: None))
		bo.enter_context(patch.object(dc, "_ghi_so_duoc", lambda: True))
		bo.enter_context(patch.object(dc, "_dieu_chinh", lambda n: {"la_dieu_chinh": 1}))
		bo.enter_context(patch.object(hdc, "chuan_bi_ghi_so", lambda n: doc))
		bo.enter_context(patch.object(dc, "_ghi_so_co_hach_toan", lambda d, tk: nhan.append((d.name, tk))))
		bo.enter_context(patch.object(dc, "frappe", SimpleNamespace(throw=throw, get_doc=lambda dt, n: doc)))
		kq = dc.ghi_so_thang("HDM-DC", '{"R1": "6417 - Chi phí"}')
	la("tài khoản tới cửa ghi sổ", nhan, [("HDM-DC", '{"R1": "6417 - Chi phí"}')])
	la("báo đã ghi sổ vào tờ gốc", (kq["da_ghi_so"], kq["goc"]), (1, "HDM-GOC"))


@ca("Codex #578: hoá đơn điều chỉnh TĂNG (không phải tờ trả) cũng không ghi đơn giá phần chênh vào bảng giá nhập")
def _bang_gia_dc_tang():
	from vagabond import bang_gia_nhap as bg
	ghi = []
	doc = _Dong(name="HDM-DCT", is_return=0, custom_trang_thai_hddt="Điều chỉnh", posting_date="2026-11-13", bill_no="39340",
		items=[_Dong(item_code="NVLT00021", uom="Kg", conversion_factor=1000, rate=60000, description="")])
	with patch.object(bg, "_ghi_mot_dong", lambda *a: ghi.append(a) or "sua"), patch.object(bg, "ly_do_bo_qua", lambda *a: None):
		bg._chay(doc)
	la("không ghi dòng nào", ghi, [])
	dung("tờ gốc thường vẫn là giá mua", not hdc.la_to_dieu_chinh_doc(_Dong(is_return=0, custom_trang_thai_hddt="Gốc")))


@ca("Codex #578 cùng loại: giá mua gần nhất của nhà cung cấp và của món không lấy từ tờ trả lại hay tờ điều chỉnh")
def _gia_gan_nhat():
	from vagabond import ncc
	cau = []

	class _Db:
		def sql(self, q, *a, **k):
			cau.append(q)
			return []

	with patch.object(hdc, "co_truong", lambda dt, t: True), patch.object(ncc, "frappe", SimpleNamespace(db=_Db())):
		ncc._ncc_tu_lich_su()
	cau_hd = [q for q in cau if "Purchase Invoice Item" in q]
	dung("có câu đọc hoá đơn mua", bool(cau_hd))
	dung("loại tờ trả lại", all("ifnull(pi.is_return, 0) = 0" in q for q in cau_hd))
	dung("loại tờ điều chỉnh", all("custom_trang_thai_hddt, '') != 'Điều chỉnh'" in q for q in cau_hd))
	with patch.object(hdc, "co_truong", lambda dt, t: False):
		dung("site thiếu ô trạng thái: vẫn loại tờ trả, không đọc ô không có", hdc.sql_bo_to_chenh("pi") == " and ifnull(pi.is_return, 0) = 0")


@ca("Codex #578: danh sách tờ điều chỉnh không nối thẳng: 1 và 2 tờ hiện đủ, 5 tờ hiện 2 tờ đầu và 'và 3 tờ nữa' bấm mới mở")
def _ds_gon():
	from vagabond.khung.kiem_thu import thu_doi_chieu_252 as t252
	def cac(n):
		return [{"name": "HDM-DC%d" % i, "bill_no": str(39339 + i), "total": -1000} for i in range(n)]
	for n, co_gon in ((1, False), (2, False), (5, True)):
		s = t252._so_sanh_mau([_dong_kg_man(dvt_hd="Thùng", sl_hd=2, ton_hd=20000, lech_dvt=0)], tien_hd=9200000,
			tien_pnk=8000000, tien_dieu_chinh=-1000 * n, tien_hd_sau=9200000 - 1000 * n, cac_to_dieu_chinh=cac(n))
		html = _man(t252._xem_mau(), s)["so_sanh"]
		la("%d tờ: thu gọn" % n, "tờ nữa</summary>" in html, co_gon)
		dung("%d tờ: tờ đầu hiện" % n, "HDM-DC0 (số 39339)" in html)
		if co_gon:
			dung("đếm đúng phần còn lại", "và 3 tờ nữa" in html)
	ra = _man(t252._xem_mau(dieu_chinh={"cac_to": cac(5), "tien_sau": 9195000}))
	dung("thẻ tờ gốc: đếm số và thu gọn", "5 hoá đơn điều chỉnh" in ra["khung"] and "và 3 tờ nữa" in ra["khung"])
