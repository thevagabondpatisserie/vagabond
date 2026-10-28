# -*- coding: utf-8 -*-
"""v619: nhịp đồng bộ Pancake giữ tên dòng món cũ khi dựng lại bảng món.

Đo trên site 28/10/2026: 111 trên 111 lần nhịp đồng bộ dựng lại bảng món của
hoá đơn nháp có nội dung món y hệt, nhưng dòng mới mang tên mới nên lịch sử
sửa chụp lại cả bảng cũ lẫn mới. Lịch sử hoá đơn bán phình hơn 1 GB thô.

Ca chuỗi ở đây chạy ĐÚNG hàm `_upsert_hoa_don` nạp từ mã nguồn thật (cùng cách
nạp với ca v595), chỉ thay phần chạm site. Không gọi giu_ten_dong riêng trong
ca chuỗi: ca phải thấy đúng cái nhịp đồng bộ đưa vào hoá đơn. Bench chạy lại
chuỗi này trên ERPNext thật và đọc lịch sử thật (kiem_that/thu_dong_mon_619).
"""

import ast
from pathlib import Path
from types import SimpleNamespace

from vagabond.khung.kiem_thu import thu_xhd_dong_bo_khong_de_595 as h595
from vagabond.khung.kiem_thu.nen import ca, la


def _nap_giu_ten_dong():
	# Nạp từ mã nguồn thay vì import ban_hang: đầu tệp đó kéo thư viện mạng,
	# máy chạy CI không có (giả lập CI tay không).
	cay = ast.parse((Path(__file__).resolve().parents[2] / "ban_hang.py").read_text(encoding="utf-8"))
	ham = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "giu_ten_dong"]
	g = {}
	exec(compile(ast.Module(body=ham, type_ignores=[]), "ban_hang.py", "exec"), g)
	return g["giu_ten_dong"]


ban_hang = SimpleNamespace(giu_ten_dong=_nap_giu_ten_dong())


@ca("v619 giữ tên dòng: dòng mới cùng vị trí mang tên dòng cũ, dòng thừa lấy tên mới")
def _():
	moi = [{"item_code": "A", "qty": 1}, {"item_code": "B", "qty": 2}, {"item_code": "C", "qty": 3}]
	goc = [dict(r) for r in moi]
	la("đủ tên cũ", [r.get("name") for r in ban_hang.giu_ten_dong(moi, ["r1", "r2", "r3"])], ["r1", "r2", "r3"])
	la("thêm món: dòng thừa không tên", [r.get("name") for r in ban_hang.giu_ten_dong(moi, ["r1", "r2"])], ["r1", "r2", None])
	la("bớt món: chỉ dùng tên đầu", [r.get("name") for r in ban_hang.giu_ten_dong(moi[:1], ["r1", "r2"])], ["r1"])
	la("hoá đơn mới không có tên cũ", ban_hang.giu_ten_dong(moi, []), moi)
	la("tên rỗng bị bỏ qua", [r.get("name") for r in ban_hang.giu_ten_dong(moi[:2], [None, "", "r9"])], ["r9", None])
	la("dòng đã có tên để nguyên", ban_hang.giu_ten_dong([{"name": "x", "qty": 1}], ["r1"]), [{"name": "x", "qty": 1}])
	la("không sửa dữ liệu đầu vào", moi, goc)
	la("nội dung món giữ nguyên", [{k: v for k, v in r.items() if k != "name"} for r in ban_hang.giu_ten_dong(moi, ["r1"])], goc)


def _chay(cu, dong):
	"""Một nhịp _upsert_hoa_don thật trên tờ nháp có sẵn các dòng món `cu`."""
	d = h595._to(items=[h595.D(name=n, item_code="CU") for n in cu])
	them = []
	d["append"] = lambda bang, r: them.append((bang, dict(r)))
	goc = h595._nap

	def nap(g2, nguon=None):
		goc(g2, nguon)
		g2["_dong_hang"] = lambda *a: ([dict(r) for r in dong], [])
		return g2

	h595._nap = nap
	try:
		h595._dong_bo(d, {"id": "PK1", "display_id": "1", "note": ""})
	finally:
		h595._nap = goc
	return [r for bang, r in them if bang == "items"], d


@ca("v619 nhịp đồng bộ thật: dựng lại bảng món dùng lại tên dòng cũ theo vị trí")
def _():
	dong = [{"item_code": "BANH", "qty": 1, "rate": 100}, {"item_code": "KEM", "qty": 2, "rate": 50}]
	them, d = _chay(["SII-1", "SII-2"], dong)
	la("dòng mới mang tên dòng cũ", [r.get("name") for r in them], ["SII-1", "SII-2"])
	la("nội dung lấy từ đơn Pancake", [(r["item_code"], r["qty"]) for r in them], [("BANH", 1), ("KEM", 2)])
	la("bảng cũ đã được xoá trước khi thêm", d["items"], [])
	them, _ = _chay(["SII-1"], dong)
	la("thêm món: dòng thừa lấy tên mới", [r.get("name") for r in them], ["SII-1", None])
	them, _ = _chay(["SII-1", "SII-2", "SII-3"], dong[:1])
	la("bớt món: chỉ dòng đầu giữ tên", [r.get("name") for r in them], ["SII-1"])
