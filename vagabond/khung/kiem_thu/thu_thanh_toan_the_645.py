"""v645 (anh Việt 08/11/2026): đơn web khách trả thẻ OnePay về Pancake thành Tiền mặt.

Đọc trên site thật: đơn web DW-2611-06247, 06259, 06271 (Pancake 97077, 97098,
97113) đều trả thẻ OnePay đủ, máy đã ghi lên Pancake ("da_ghi"). Lịch sử đơn
Pancake: lệnh ghi prepaid của khoá API làm cash 0 thành đúng số đó, nên đơn
mang hình thức Tiền mặt. Hoá đơn đồng bộ HDB-26-11-01090, HDB-26-11-01108 ghi
"Tiền mặt" do máy đoán: phép đoán từ ô cash ra Tiền mặt nên không còn hỏi
bản ghi đơn web (chỉ hỏi khi phép đoán rỗng).

Đơn khách trả bằng link thanh toán của chính Pancake (96844, 97059) thì lịch
sử ghi charged_by_onepay CÙNG prepaid, cash giữ 0.

Ca ở đây chạy hàm THẬT (thanh_toan_web_thuan, thanh_toan_web.ghi_pancake,
ban_hang._upsert_hoa_don nạp từ mã nguồn), chỉ thay tầng Frappe và mạng.
"""
import json
import re
import sys
import types
import unicodedata
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import thanh_toan_web as tw
from vagabond import thanh_toan_web_thuan as ttt
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_xhd_dong_bo_khong_de_595 import _nap, _to


class _Tra:
	def __init__(self, ma, j):
		self.status_code, self._j, self.text = ma, j, json.dumps(j)

	def json(self):
		return self._j


class D(dict):
	__getattr__ = dict.get


def _ghi(doc_lan, cach="OnePay", so=671000, ds=None):
	"""Một lượt ghi_pancake thật: đọc, PUT, đọc lại. doc_lan là các lần đọc."""
	from vagabond import lib

	vet = []
	lan = iter(doc_lan)
	req = types.SimpleNamespace(get=lambda *a, **k: vet.append("get") or _Tra(200, {"data": next(lan)}),
		put=lambda *a, **k: vet.append(("put", k.get("json"))) or _Tra(200, {}))
	d = D(name="DW-2611-06259", pancake_id="97098", vgb_tt_cach=cach, vgb_tt_da_thu=so,
		vgb_tt_ma_gd=json.dumps(ds if ds is not None else [{"gd": "DW261106259-1", "so": so, "loai": "the"}]))
	with patch.object(tw, "requests", req), patch.object(lib, "cfg_o", lambda o: ""), \
			patch.object(tw, "_pancake_khoa", lambda: (D(pancake_shop_id="67355"), "k")):
		r = tw.ghi_pancake(d)
	return r, vet


@ca("v645 tái hiện 97098: thẻ OnePay trước đây chỉ ghi prepaid; nay ghi charged_by_onepay kèm prepaid như link thanh toán của Pancake")
def _():
	la("thân thẻ", ttt.than_pancake("OnePay", 671000, {"prepaid": 0, "cash": 0}),
		{"charged_by_onepay": 671000, "prepaid": 671000})
	la("không bao giờ hạ prepaid đang có", ttt.than_pancake("OnePay", 671000, {"prepaid": 800000, "cash": 800000}),
		{"charged_by_onepay": 671000, "prepaid": 800000})
	la("đã ghi đúng (prepaid đủ, không nằm ở Tiền mặt): thôi", ttt.than_pancake("OnePay", 671000, {"prepaid": 671000, "cash": 0}), None)
	la("chuyển khoản giữ nguyên ô transfer_money", ttt.than_pancake("Chuyển khoản", 671000, {}), {"transfer_money": 671000})
	la("số hỏng thì thôi", ttt.than_pancake("OnePay", "x", {}), None)


@ca("v645 ghi Pancake thẻ: đọc lại soát prepaid (ô thẻ không đọc được); Pancake vẫn xếp vào Tiền mặt thì báo Sales đổi tay, COD vẫn đúng")
def _():
	r, vet = _ghi([{"prepaid": 0, "cash": 0}, {"prepaid": 671000, "cash": 0}])
	la("Pancake nhận ô thẻ", (r, vet), ("da_ghi", ["get", ("put", {"charged_by_onepay": 671000, "prepaid": 671000}), "get"]))
	r, _vet = _ghi([{"prepaid": 0, "cash": 0}, {"prepaid": 671000, "cash": 671000}])
	la("Pancake vẫn xếp vào Tiền mặt", r, "tien_mat")
	r, _vet = _ghi([{"prepaid": 0, "cash": 0}, {"prepaid": 0, "cash": 0}])
	la("Pancake bỏ qua lệnh: lỗi, Sales ghi tay", r, "loi")
	tieu, dong = ttt.tin_da_tra("DW-2611-06259", "97098", "OnePay", False, "tien_mat")
	dung("tin Sales nói đổi sang OnePay trên Pancake", any("đổi hình thức thanh toán" in x and "OnePay" in x for x in dong))
	from vagabond import kenh_zalo as kz

	_sach, bo = kz.bo_dong_tien("\n".join([tieu] + dong))
	la("tin không mang số tiền (luật v613)", bo, 0)


def _dong_bo_pt(d, don, doan, web):
	"""Một nhịp _upsert_hoa_don thật với phép đoán từ ô tiền Pancake và bản ghi đơn web."""
	def gv(dt, loc, *a, **k):
		return None if loc.get("docstatus") == 2 else D(name=d.name, docstatus=0)
	f = NS(db=NS(get_value=gv, exists=lambda *a, **k: True), get_doc=lambda *a, **k: d,
		get_all=lambda *a, **k: [], log_error=lambda *a, **k: None, throw=lambda m: (_ for _ in ()).throw(Exception(m)))
	goi = []
	g = dict(frappe=f, re=re, unicodedata=unicodedata, flt=lambda x: float(x or 0), cint=lambda x: int(x or 0),
		hoa_don_vat=NS(sach_dia_chi_xhd=lambda s: (s or "").strip(), thieu_ten_rieng=lambda t: False),
		_dong_hang=lambda *a: ([{"item_code": "BANH", "qty": 1, "rate": 100}], []), _lech_pancake=lambda *a: 0,
		giu_khach_cua_don=lambda *a: True, _giam_tu_diem=lambda *a: 0, _giam_rieng=lambda *a: 0,
		_doan_thanh_toan=lambda *a: doan, _dien_dong_thanh_toan=lambda *a: None, nghi_cong_no=lambda *a: 0,
		_pt_don_web=lambda *a: goi.append(a) or web)
	g["_yeu_cau_xhd_dung_don"] = lambda ma: None
	_nap(g)
	with patch.dict(sys.modules, {"vagabond.khach_hang": NS(la_khach_gop=lambda x: False), "vagabond.api": NS(tra_mst=lambda m: {})}):
		g["_upsert_hoa_don"](don, "2026-11-06", "CT", "KH")
	return d, goi


DON = {"id": "97098", "display_id": "97098", "note": ""}


@ca("v645 tái hiện HDB-26-11-01090: Pancake ghi Tiền mặt nhưng đơn web đã thu đủ thẻ OnePay thì hoá đơn đồng bộ mang OnePay và mã giao dịch")
def _():
	d, goi = _dong_bo_pt(_to(name="HDB-26-11-01090", vgb_pt_thanh_toan="", vgb_pt_do_may=0, vgb_ma_tham_chieu=""), DON,
		("Tiền mặt", "Pancake: tiền mặt 671.000"), ("OnePay", "DW261106259-1"))
	la("phương thức, mã tham chiếu", (d.vgb_pt_thanh_toan, d.vgb_pt_do_may, d.vgb_ma_tham_chieu), ("OnePay", 1, "DW261106259-1"))
	dung("ghi chú đối soát nói web đã thu thẻ", str(d.get("vgb_ghi_chu_doi_soat") or "").startswith("Web đã thu online qua OnePay."))
	la("hỏi bản ghi đơn web đúng mã đơn", goi, [("97098", "97098")])
	# Lần đồng bộ sau trên tờ máy đã điền Tiền mặt (tờ nháp bị lỗi cũ) cũng sửa về OnePay.
	d2, _ = _dong_bo_pt(_to(vgb_pt_thanh_toan="Tiền mặt", vgb_pt_do_may=1, vgb_ma_tham_chieu=""), DON,
		("Tiền mặt", "Pancake: tiền mặt 671.000"), ("OnePay", "DW261106259-1"))
	la("tờ máy điền Tiền mặt về OnePay", d2.vgb_pt_thanh_toan, "OnePay")


@ca("v645: không phải đơn web trả online thì vẫn theo phép đoán; Sales đã chọn tay thì máy không đè")
def _():
	d, _ = _dong_bo_pt(_to(vgb_pt_thanh_toan="", vgb_pt_do_may=0), DON, ("Tiền mặt", "Pancake: tiền mặt 671.000"), ("", ""))
	la("đơn thường: Tiền mặt", d.vgb_pt_thanh_toan, "Tiền mặt")
	d, _ = _dong_bo_pt(_to(vgb_pt_thanh_toan="Chuyển khoản", vgb_pt_do_may=0), DON, ("Tiền mặt", ""), ("OnePay", "DW-1"))
	la("Sales chọn tay giữ nguyên", d.vgb_pt_thanh_toan, "Chuyển khoản")
	d, _ = _dong_bo_pt(_to(vgb_pt_thanh_toan="Hàng tặng", vgb_pt_do_may=1), DON, ("Tiền mặt", ""), ("OnePay", "DW-1"))
	la("Hàng tặng giữ nguyên", d.vgb_pt_thanh_toan, "Hàng tặng")
