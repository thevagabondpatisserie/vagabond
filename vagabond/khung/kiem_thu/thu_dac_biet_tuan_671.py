# -*- coding: utf-8 -*-
"""v671 (Minh Vũ 18/11/2026): món của đợt "Đặc biệt tuần này" lên tab theo ĐỢT.

Ca thật trên site: đợt cuối tuần 28 · 29/11 có Hũ Stollen (chưa có trên tủ, bếp
chưa điền Đủ decor), trang khách báo "Món của tuần này đang được cập nhật". Cách
lách là nhờ bếp điền Đủ decor, nhưng món lại lọt sang tab Đặt bánh trước và ô
decor bị dùng sai mục đích.

Ca dưới chạy THẬT:
  - phép thuần dac_biet_tuan.nhom_cua_dot, bo_mon_dot;
  - kiem_banh._mon_dac_biet với bảng giả (thẻ Bánh, Item, tắt bán web);
  - don_hang.tao_don THẬT trên môi trường giả của bộ ca #367: món của đợt không
    đem đi kiểm hay giữ tồn tủ, Đủ decor, refill (cả lần kiểm sớm lẫn lần kiểm
    dưới khoá), bánh thường trong cùng đơn vẫn bị kiểm như cũ.
Phần trang khách kiểm bằng node: hanh_vi/dac_biet_tuan_671.mjs.
"""
import os
import subprocess
import unittest.mock as um

from vagabond import dac_biet_tuan as dbt
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STOLLEN = "bánh stollen cookie, hũ 200 gr"


def _dot(mon):
	return {"id": "dbt-28", "mon_dt": mon}


def _the(khoa, tt="Đang hiện", anhs=("/files/a.jpg",), ma=("M1",), ten=None):
	return {"khoa": khoa, "ten": ten or khoa.title(), "trang_thai": tt, "anhs": list(anhs), "mo_ta": ["Dòng một", "Dòng hai"],
		"tang": ["Bơ"], "ma": list(ma)}


@ca("v671 món của đợt theo ĐỢT: thẻ Đang hiện hay Chờ ảnh đều lên; Đã ẩn không lên; không mã nào bán được (thiếu giá, ngừng dùng, tắt bán web) không lên")
def _nhom():
	dot = _dot([{"khoa": "a", "anh": ""}, {"khoa": "b", "anh": ""}, {"khoa": "c", "anh": ""}, {"khoa": "d", "anh": ""}, {"khoa": "e", "anh": ""}])
	the = [_the("a", ma=("A1",)), _the("b", tt="Chờ ảnh", ma=("B1",)), _the("c", tt="Đã ẩn", ma=("C1",)), _the("d", ma=("D1",))]
	gia = {"A1": {"cm": 16, "gia": 650000}, "B1": {"cm": 0, "gia": 180000}, "C1": {"cm": 12, "gia": 1}}
	ra = dbt.nhom_cua_dot(dot, the, gia)
	la("lên a và b theo thứ tự đợt; c Đã ẩn, d không mã bán được, e không có thẻ: bỏ", [g["ten"] for g in ra], ["A", "B"])
	la("khuôn một nhóm", ra[0], {"ten": "A", "anh": "/files/a.jpg", "anhs": ["/files/a.jpg"], "mo_ta": "Dòng một Dòng hai",
		"tang": ["Bơ"], "tu_web": 1, "sizes": [{"ma": "A1", "cm": 16, "gia": 650000}]})
	la("không có đợt", [dbt.nhom_cua_dot(None, the, gia), dbt.nhom_cua_dot(_dot([]), the, gia)], [[], []])


@ca("v671 món của đợt: thẻ chưa có ảnh mà đợt có Ảnh đứng thì lên bằng ảnh đợt; không ảnh nào thì không lên; size xếp nhỏ tới lớn, size không cỡ đứng cuối")
def _anh_size():
	the = [_the("a", tt="Chờ ảnh", anhs=(), ma=("A20", "A12", "A0"))]
	gia = {"A20": {"cm": 20, "gia": 9}, "A12": {"cm": 12, "gia": 5}, "A0": {"cm": 0, "gia": 1}}
	ra = dbt.nhom_cua_dot(_dot([{"khoa": "a", "anh": "/files/dung.jpg"}]), the, gia)
	la("ảnh đứng của đợt", (ra[0]["anh"], ra[0]["anhs"]), ("/files/dung.jpg", ["/files/dung.jpg"]))
	la("size nhỏ tới lớn, không cỡ cuối", [z["ma"] for z in ra[0]["sizes"]], ["A12", "A20", "A0"])
	la("không ảnh nào: không lên", dbt.nhom_cua_dot(_dot([{"khoa": "a", "anh": ""}]), the, gia), [])


@ca("v671 dòng đơn đem đi kiểm tồn: bỏ mọi size của món đợt, giữ bánh thường; không có đợt thì giữ nguyên")
def _bo_mon():
	hang = [{"variation_id": "C12", "quantity": 1}, {"variation_id": "KHAC", "quantity": 2}, {"variation_id": "C16", "quantity": 1}]
	la("bỏ món đợt", dbt.bo_mon_dot(hang, {"candle": {"C12", "C16"}}), [{"variation_id": "KHAC", "quantity": 2}])
	la("không đợt", dbt.bo_mon_dot(hang, {}), hang)
	la("rỗng", dbt.bo_mon_dot(None, {"candle": {"C12"}}), [])


@ca("v671 máy chủ trả món của đợt (kiem_banh._mon_dac_biet): đọc thẻ Bánh của đợt, chỉ mã bán được trên web (giá, đang dùng, hàng bán, không tắt bán web, không BAWS); đọc hỏng thì rỗng, không làm hỏng hai tab kia")
def _may_chu():
	from types import SimpleNamespace as NS

	from vagabond import banh_web, kiem_banh

	dot = {"id": "dbt-28", "mon_dt": [{"khoa": STOLLEN, "anh": ""}]}
	the = [NS(khoa=STOLLEN, ten="Bánh Stollen Cookie, Hũ 200 gr", trang_thai="Chờ ảnh",
		anh='[{"url": "/files/stollen.jpg", "bam": ""}]', mo_ta="Bánh quy", tang="", ma_hang="BACF00051\nBACF00052\nBAWS00001")]
	item = [{"item_code": "BACF00051", "item_name": "Bánh Stollen Cookie, Hũ 200 gr", "standard_rate": 180000, "disabled": 0, "is_sales_item": 1},
		{"item_code": "BACF00052", "item_name": "Bánh Stollen Cookie, Hũ 400 gr", "standard_rate": 0, "disabled": 0, "is_sales_item": 1}]
	hoi = []

	def get_all(dt, filters=None, fields=None, **k):
		hoi.append((dt, filters))
		return the if dt == banh_web.DT else [dict(x) for x in item if x["item_code"] in filters["item_code"][1]]
	with um.patch.object(dbt, "dot_cong_khai", lambda: dot), um.patch.object(kiem_banh.frappe, "get_all", get_all, create=True), \
			um.patch.object(kiem_banh.tat_ban_web, "bang", lambda ma, ngay: {}), \
			um.patch.object(kiem_banh, "getdate", lambda *a: "2026-11-18"):
		ra = kiem_banh._mon_dac_biet()
	la("một nhóm Hũ Stollen, chỉ mã có giá", [(g["ten"], [z["ma"] for z in g["sizes"]], g["anh"]) for g in ra],
		[("Bánh Stollen Cookie, Hũ 200 gr", ["BACF00051"], "/files/stollen.jpg")])
	dung("không hỏi Item mã bánh sỉ BAWS", all("BAWS00001" not in (f or {}).get("item_code", ["", []])[1] for dt, f in hoi if dt == "Item"))
	with um.patch.object(dbt, "dot_cong_khai", lambda: dot), um.patch.object(kiem_banh.tat_ban_web, "bang", lambda ma, ngay: {"BACF00051": {"tat": 1}}), \
			um.patch.object(kiem_banh.frappe, "get_all", get_all, create=True), um.patch.object(kiem_banh, "getdate", lambda *a: "2026-11-18"):
		la("tắt bán web: không lên", kiem_banh._mon_dac_biet(), [])
	ghi = []

	def hong():
		raise RuntimeError("mất kết nối")
	with um.patch.object(dbt, "dot_cong_khai", hong), um.patch.object(kiem_banh.frappe, "log_error", lambda *a, **k: ghi.append(a), create=True), \
			um.patch.object(kiem_banh.frappe, "get_traceback", lambda *a: "tb", create=True):
		la("đọc hỏng: rỗng", kiem_banh._mon_dac_biet(), [])
	la("có ghi Error Log", len(ghi), 1)


def _tao_ghi_ton(hang, ngay="2026-11-21T10:00:00"):
	"""Chạy tao_don THẬT (khuôn ca v667), ghi lại các dòng đem đi kiểm và giữ tồn."""
	from vagabond import giu_ton_web, ton_don_web
	from vagabond.khung.kiem_thu import thu_dac_biet_tuan_667 as t667

	vet = {"kiem": [], "giu": [], "rf": []}

	def kiem(h, n):
		vet["kiem"].append(sorted(x["variation_id"] for x in h))
		return []

	def giu(h, n):
		vet["giu"].append(sorted(x["variation_id"] for x in h))
		return [], None

	def giu_rf(h, n):
		vet["rf"].append(sorted(x["variation_id"] for x in h))
		return [], None
	d = dbt.chuan_dot(t667._dot(mon_dt=[{"khoa": "candle", "toi_da": "30"}]))
	with um.patch.object(ton_don_web, "kiem", kiem), um.patch.object(giu_ton_web, "kiem_va_giu", giu, create=True), \
			um.patch.object(giu_ton_web, "kiem_va_giu_refill", giu_rf, create=True):
		r, _vet, _thu = t667._tao(d, "2026-11-17T10:00", ngay, hang=hang)
	return r, vet


@ca("v671 cửa tạo đơn THẬT: đơn có món của đợt và bánh thường: món đợt không bị kiểm, giữ tồn tủ, Đủ decor, refill (lần kiểm sớm và lần dưới khoá); bánh thường vẫn bị kiểm; đơn ghi được")
def _tao_don():
	r, vet = _tao_ghi_ton([{"variation_id": "BAWC00139", "quantity": 3}, {"variation_id": "BAWC00135", "quantity": 1}])
	la("ghi đơn", r.get("ok"), 1)
	la("lần kiểm sớm chỉ bánh thường", vet["kiem"], [["BAWC00135"]])
	la("giữ tồn dưới khoá chỉ bánh thường", vet["giu"], [["BAWC00135"]])
	la("giữ refill dưới khoá chỉ bánh thường", vet["rf"], [["BAWC00135"]])
	r, vet = _tao_ghi_ton([{"variation_id": "BAWC00135", "quantity": 1}], ngay="2026-11-19T10:00:00")
	la("đơn chỉ bánh thường: kiểm như cũ", (r.get("ok"), vet["kiem"], vet["giu"]), (1, [["BAWC00135"]], [["BAWC00135"]]))


@ca("v671 cửa tạo đơn THẬT: Marketing thêm món vào đợt trong lúc đơn chờ khoá đợt: lần giữ tồn dưới khoá đọc theo đợt mới, món vừa thêm cũng không bị giữ Đủ decor")
def _dot_doi_giua_chung():
	import contextlib

	from vagabond import giu_ton_web, ton_don_web
	from vagabond.khung.kiem_thu import thu_dac_biet_tuan_667 as t667
	from vagabond.khung.kiem_thu import thu_don_web_367 as t367

	vet, tao_don = t367._moi_truong_tao_don(lambda v: t367._Tra(200, {"data": {"id": "91500"}}))
	dau = dbt.chuan_dot(t667._dot(mon_dt=[{"khoa": "candle", "toi_da": "30"}]))
	sau = dbt.chuan_dot(t667._dot(mon_dt=[{"khoa": "candle", "toi_da": "30"}, {"khoa": "phi tử tiếu", "toi_da": "30"}]))
	ma = {"candle": {"BAWC00139"}, "phi tử tiếu": {"BAWC00135"}}
	bay = {"dot": dau}
	giu = []

	@contextlib.contextmanager
	def khoa_suat(d):
		bay["dot"] = sau
		yield
	don = t367._don(ngay_nhan="2026-11-21T10:00:00")
	don["items"] = [{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAWC00135", "quantity": 1}]
	with um.patch.object(dbt, "dot_cong_khai", lambda: bay["dot"]), \
			um.patch.object(dbt, "ma_theo_khoa", lambda d: {m["khoa"]: ma[m["khoa"]] for m in (d or {}).get("mon_dt") or []}), \
			um.patch.object(dbt, "luc_vn", lambda: "2026-11-17T10:00"), um.patch.object(dbt, "khoa_suat", khoa_suat), \
			um.patch.object(dbt, "da_dat", lambda d, mk: {}), um.patch.object(ton_don_web, "kiem", lambda h, n: []), \
			um.patch.object(giu_ton_web, "kiem_va_giu", lambda h, n: (giu.append(sorted(x["variation_id"] for x in h)), ([], None))[1], create=True), \
			um.patch.object(giu_ton_web, "kiem_va_giu_refill", lambda h, n: ([], None), create=True):
		r = tao_don(__import__("json").dumps(don))
	la("ghi đơn", r.get("ok"), 1)
	la("giữ tồn dưới khoá không còn món vừa thêm vào đợt", giu, [[]])


@ca("v671 Đặc biệt tuần này: chạy thật hanh_vi/dac_biet_tuan_671.mjs (món chỉ làm cho đợt lên tab, không lọt sang Đặt trước, size và số theo đợt, giỏ lưu) đều đạt")
def _node():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond/khung/kiem_thu/hanh_vi/dac_biet_tuan_671.mjs")],
		capture_output=True, text=True, timeout=120)
	la("dac_biet_tuan_671.mjs", (r.returncode, (r.stdout or "")[-600:] if r.returncode else ""), (0, ""))
	dung("đủ 5 ca", "5 đạt, 0 hỏng" in r.stdout)





@ca("v671 màn Danh mục sản phẩm, khối Tìm mã cũ: chạy thật hanh_vi/tim_ma_web_671.js (mã chưa có giá nói ngay, không nút Lên web; mọi nút 44 điểm) đều đạt")
def _tim_ma():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond/khung/kiem_thu/hanh_vi/tim_ma_web_671.js")],
		capture_output=True, text=True, timeout=120)
	la("tim_ma_web_671.js", (r.returncode, (r.stdout or "")[-600:] if r.returncode else ""), (0, ""))
	dung("đủ 2 ca", "2 ca đạt, 0 ca hỏng" in r.stdout)
