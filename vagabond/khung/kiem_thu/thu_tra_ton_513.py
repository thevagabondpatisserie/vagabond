# -*- coding: utf-8 -*-
"""v513: man Tra ton kho co phan loai, chip loc, canh bao lo, anh mon (anh Viet 20/09/2026).

Phan thuan cua vagabond/tra_ton.py kiem o day; phan chay tren trinh duyet
kiem bang hanh_vi/tra_ton_513.js (DOM gia). Ca cuoi chot man ton dung cua
may chu, khong con doc Bin tu trinh duyet.
"""

import io
import os
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import tra_ton as tt
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("v513: loai hang theo tien to ma")
def _loai():
	la("bao bì", tt.loai_cua_ma("BPKG00001"), "bao_bi")
	la("công cụ", tt.loai_cua_ma("ccdc00012"), "ccdc")
	la("văn phòng phẩm gom vào công cụ", tt.loai_cua_ma("VVPP00003"), "ccdc")
	la("nguyên liệu", tt.loai_cua_ma("NVLT00156"), "nguyen_lieu")
	la("bán thành phẩm", tt.loai_cua_ma("NBTP00029"), "btp")
	la("thành phẩm", tt.loai_cua_ma("BAWC00046"), "thanh_pham")
	la("không rõ", tt.loai_cua_ma("DVBH00001"), "khac")
	la("rỗng", tt.loai_cua_ma(None), "khac")


@ca("v513: trang thai lo va dem lo can han, qua han, chi dem lo con hang")
def _lo():
	la("quá hạn", tt.trang_thai_lo("2026-09-19", "2026-09-20"), "qua_han")
	la("hôm nay hết hạn là cận hạn", tt.trang_thai_lo("2026-09-20", "2026-09-20"), "can_han")
	la("7 ngày là cận hạn", tt.trang_thai_lo("2026-09-27", "2026-09-20"), "can_han")
	la("8 ngày thì chưa", tt.trang_thai_lo("2026-09-28", "2026-09-20"), "")
	la("không HSD thì không cảnh báo", tt.trang_thai_lo(None, "2026-09-20"), "")
	d = tt.dem_lo({
		"A": [("2026-09-19", 5), ("2026-09-22", 3), ("2026-12-01", 10), ("2026-09-18", 0)],
		"B": [(None, 4)],
	}, "2026-09-20")
	la("A: 1 quá hạn, 1 cận hạn, lô hết hàng không đếm", d["A"], {"can_han": 1, "qua_han": 1})
	la("B: không HSD", d["B"], {"can_han": 0, "qua_han": 0})


def _rows():
	return [
		{"ma": "BPKG00001", "ten": "Túi", "ton": 100, "loai": "bao_bi", "can_han": 0, "qua_han": 0},
		{"ma": "NVLT00007", "ten": "Bơ lạt", "ton": 12, "loai": "nguyen_lieu", "can_han": 2, "qua_han": 0},
		{"ma": "CCDC00012", "ten": "Khay", "ton": -3, "loai": "ccdc", "can_han": 0, "qua_han": 0},
		{"ma": "BAWC00046", "ten": "Bánh Avoca", "ton": 4, "loai": "thanh_pham", "can_han": 0, "qua_han": 1},
	]


@ca("v513: loc theo chip va o tim, sap xep, dem chip, cau tom tat")
def _loc():
	r = _rows()
	la("tất cả", len(tt.loc(r)), 4)
	la("chip loại", [x["ma"] for x in tt.loc(r, "bao_bi")], ["BPKG00001"])
	la("chip cận hạn gồm cả quá hạn", [x["ma"] for x in tt.loc(r, "can_han")], ["NVLT00007", "BAWC00046"])
	la("chip âm", [x["ma"] for x in tt.loc(r, "am")], ["CCDC00012"])
	la("tìm theo tên không dấu hoa", [x["ma"] for x in tt.loc(r, "", "bơ")], ["NVLT00007"])
	la("tìm theo mã", [x["ma"] for x in tt.loc(r, "", "ccdc")], ["CCDC00012"])
	la("chip + tìm", tt.loc(r, "bao_bi", "bơ"), [])
	la("sắp A-Z", [x["ma"] for x in tt.sap_xep(r, "ten")], ["BAWC00046", "NVLT00007", "CCDC00012", "BPKG00001"])
	la("tồn nhiều trước", [x["ma"] for x in tt.sap_xep(r, "nhieu")][:2], ["BPKG00001", "NVLT00007"])
	la("tồn ít trước", [x["ma"] for x in tt.sap_xep(r, "it")][0], "CCDC00012")
	la("sắp lạ thì về A-Z", [x["ma"] for x in tt.sap_xep(r, "xyz")][0], "BAWC00046")
	d = tt.dem_chip(r)
	la("đếm", (d[""], d["bao_bi"], d["nguyen_lieu"], d["ccdc"], d["thanh_pham"], d["btp"], d["khac"], d["can_han"], d["am"]), (4, 1, 1, 1, 1, 0, 0, 2, 1))
	la("tóm tắt không giá trị", tt.cau_tom_tat(r), "4 mã có tồn · ⏰ 2 mã có lô cận hạn hoặc quá hạn · ⚠ 1 mã tồn âm")
	la("tóm tắt có giá trị", tt.cau_tom_tat(r[:1], 1234567), "1 mã có tồn · giá trị 1.234.567 đ")


@ca("v513: ton_kho chay that ham voi frappe gia: phan loai, lo, gia tri chi cho vai kho/ke toan")
def _ton_kho():
	bins = [
		{"item_code": "BPKG00001", "actual_qty": 100, "stock_uom": "Cái", "stock_value": 50000},
		{"item_code": "NVLT00007", "actual_qty": 12, "stock_uom": "Kg", "stock_value": 1200000},
	]
	items = [
		{"name": "BPKG00001", "item_name": "Túi", "item_group": "Bao bì", "image": "/files/tui.jpg", "has_batch_no": 0},
		{"name": "NVLT00007", "item_name": "Bơ lạt", "item_group": "Nguyên liệu", "image": "", "has_batch_no": 1},
	]

	def _get_all(dt, filters=None, fields=None, **k):
		if dt == "Bin":
			return bins
		if dt == "Item":
			return items
		if dt == "Batch":
			la("chỉ hỏi lô của mã có lô", filters["item"][1], ["NVLT00007"])
			return [{"name": "LO-1", "item": "NVLT00007", "expiry_date": "2026-09-22"}, {"name": "LO-2", "item": "NVLT00007", "expiry_date": "2026-12-01"}]
		return []

	def _chay(vai):
		f = NS(get_all=_get_all, get_roles=lambda: vai, throw=lambda m, **k: (_ for _ in ()).throw(ValueError(m)),
			db=NS(exists=lambda *a: True, sql=lambda q, v=None, as_dict=False: [{"batch_no": "LO-1", "sl": 5}, {"batch_no": "LO-2", "sl": 0}]))
		with patch.object(tt, "frappe", f), patch.object(tt, "nowdate", lambda: "2026-09-20"):
			return tt.ton_kho("Kho tổng 307 - TV", "", "", "ten")
	d = _chay(["Sales User"])
	la("hai dòng", d["tong_dong"], 2)
	b = {x["ma"]: x for x in d["ds"]}
	la("loại và ảnh", (b["BPKG00001"]["loai"], b["BPKG00001"]["anh"]), ("bao_bi", "/files/tui.jpg"))
	la("lô cận hạn đếm đúng, lô hết hàng không đếm", (b["NVLT00007"]["can_han"], b["NVLT00007"]["qua_han"]), (1, 0))
	dung("quầy không thấy giá trị", "gia_tri" not in b["BPKG00001"] and d["xem_gia_tri"] == 0 and "giá trị" not in d["tom_tat"])
	d2 = _chay(["Stock Manager"])
	b2 = {x["ma"]: x for x in d2["ds"]}
	la("kho thấy giá trị từng dòng và tổng", (b2["NVLT00007"]["gia_tri"], d2["xem_gia_tri"]), (1200000.0, 1))
	dung("tổng giá trị trong tóm tắt", "1.250.000 đ" in d2["tom_tat"])
	la("chip đếm", (d2["dem"][""], d2["dem"]["can_han"]), (2, 1))


@ca("v513: man Tra ton kho doc qua may chu, cua ngo dang ky, ca hanh vi nam trong cong")
def _man():
	from vagabond.khung.kiem_thu import thu_cua_ngo
	la("cửa ngõ", sorted(thu_cua_ngo.CUA_NGO.get("tra_ton.py") or []), ["chi_tiet_ma", "ton_kho"])
	js = _doc("vagabond", "public", "js", "bep", "05-san-xuat.js")
	doan = js.split("/* ---------- 12. Tra ton kho ---------- */")[1].split("/* ---------- 12b.")[0]
	dung("gọi máy chủ, không đọc Bin từ trình duyệt", "vagabond.tra_ton.ton_kho" in doan and "getList('Bin'" not in doan)
	dung("bấm dòng mở chi tiết", "vagabond.tra_ton.chi_tiet_ma" in doan)
	sh = _doc("kiem_truoc_deploy.sh")
	dung("ca hành vi nằm trong cổng", "hanh_vi/tra_ton_513.js" in sh)
