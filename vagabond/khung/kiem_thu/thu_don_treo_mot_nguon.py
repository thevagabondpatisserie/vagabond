# -*- coding: utf-8 -*-
"""Ô "Đơn còn treo" trên Trang chủ và màn Đơn còn treo đếm cùng một bộ lọc.

Codex kiểm v685 (UI15, loại 3 và 6): ô ở phân hệ Bán hàng hiện 11 nhưng màn
Đơn còn treo (14 ngày, Tất cả) chỉ có 3. Ô tự dựng bộ lọc ở trình duyệt: từ
ngày 14 ngày trước tính theo giờ UTC tới hết hôm nay (cả đơn tương lai), còn
màn lấy ngày của site, từ 14 ngày trước tới HÔM QUA.

Các ca nạp đúng hàm thật từ ban_hang.py (_loc_don_treo, dem_don_treo,
_quet_don_treo), chỉ thay cơ sở dữ liệu bằng một bảng giả có đơn hôm nay,
hôm qua, đúng biên 14 ngày, ngoài biên và ngày tương lai, rồi chốt: con số
máy chủ trả cho ô đúng bằng số dòng màn danh sách nhận. Dữ liệu đều giả.
"""

import ast
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, la

GOC = Path(__file__).resolve().parents[2]
SRC = GOC / "ban_hang.py"


class D(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def _ngay(x):
	return x if isinstance(x, date) else date.fromisoformat(str(x))


def _add_days(d, n):
	return str(_ngay(d) + timedelta(days=int(n)))


def _khop(r, loc):
	"""Áp bộ lọc kiểu frappe lên một dòng giả (đủ cho các phép bộ lọc này dùng)."""
	for k, v in loc.items():
		gt = r.get(k)
		if isinstance(v, list):
			op, arg = v[0], v[1]
			if op == "between":
				if not (_ngay(arg[0]) <= _ngay(gt) <= _ngay(arg[1])):
					return False
			elif op == "!=":
				if (gt or "") == arg:
					return False
			elif op == "in":
				if gt not in arg:
					return False
			elif op == ">=":
				if not (_ngay(gt) >= _ngay(arg)):
					return False
			else:
				raise AssertionError("phép lọc chưa hỗ trợ: %s" % op)
		elif gt != v:
			return False
	return True


def _bang(hom_nay):
	"""Bảng Sales Invoice giả quanh ngày hom_nay."""
	h = _ngay(hom_nay)

	def don(ten, lui, **k):
		d = D(name=ten, posting_date=str(h - timedelta(days=lui)), custom_pancake_id="P-" + ten, docstatus=0,
			vgb_quay="", vgb_huy=0, vgb_tam_tinh=0, grand_total=100000, custom_pancake_display_id=ten)
		d.update(k)
		return d

	return [
		don("HOM-NAY", 0),
		don("TUONG-LAI", -2),
		don("HOM-QUA", 1),
		don("BIEN-14", 14),
		don("NGOAI-15", 15),
		don("GIUA", 6),
		don("DA-GHI-SO", 3, docstatus=1),
		don("TAM-TINH", 3, vgb_tam_tinh=1),
		don("DA-HUY", 3, vgb_huy=1),
		don("CO-QUAY", 3, vgb_quay="D1"),
		don("KHONG-PANCAKE", 3, custom_pancake_id=""),
	]


def _moi_truong(hom_nay, bang, ghi):
	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=None):
		ghi.append(("get_all", dt, filters))
		return [D(r) for r in bang if _khop(r, filters)]

	def count(dt, filters=None):
		ghi.append(("count", dt, filters))
		return sum(1 for r in bang if _khop(r, filters))

	g = {
		"frappe": NS(db=NS(get_all=get_all, count=count), whitelist=lambda *a, **k: (lambda f: f),
			log_error=lambda *a, **k: None, get_traceback=lambda: ""),
		"nowdate": lambda: str(hom_nay),
		"add_days": _add_days,
		"getdate": _ngay,
		"int": int,
		"flt": lambda x: float(x or 0),
		"_kiem_quyen_doc_luu_don": lambda: None,
		"_sepay_theo_don": lambda *a: {},
		"cfg": lambda: NS(pancake_shop_id="X"),
		"_gan_can_ck": lambda ds: None,
		"_ly_do_treo": lambda r, sepay: "chua_pt",
		"LY_DO_TREO": {"chua_pt": "Chưa có phương thức"},
	}
	cay = ast.parse(SRC.read_text(encoding="utf-8"))
	for ten in ("_loc_don_treo", "dem_don_treo", "_quet_don_treo"):
		fn = next((n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten), None)
		if fn is None:
			raise AssertionError("ban_hang.py thiếu hàm %s" % ten)
		fn.decorator_list = []
		exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SRC), "exec"), g)
	return g


@ca("UI15: số trên ô Đơn còn treo bằng đúng số dòng màn danh sách, cùng bộ lọc")
def _mot_nguon():
	ghi = []
	g = _moi_truong("2026-11-23", _bang("2026-11-23"), ghi)
	so = g["dem_don_treo"](14)["so"]
	ds = g["_quet_don_treo"](14)
	la("ô và màn cùng số", so, len(ds))
	la("đúng những đơn trong khoảng", sorted(r.name for r in ds), ["BIEN-14", "GIUA", "HOM-QUA"])
	loc = [x[2] for x in ghi]
	la("hai lời đọc dùng đúng một bộ lọc", loc[0], loc[1])


@ca("UI15 biên ngày: hôm nay, tương lai, ngoài 14 ngày không vào; đúng 14 ngày trước và hôm qua vào")
def _bien():
	for hom_nay in ("2026-11-23", "2026-03-01", "2028-03-01", "2027-01-01"):
		bang = _bang(hom_nay)
		g = _moi_truong(hom_nay, bang, [])
		ten = sorted(r.name for r in g["_quet_don_treo"](14))
		la("khoảng ngày quanh " + hom_nay, ten, ["BIEN-14", "GIUA", "HOM-QUA"])
		la("số trên ô quanh " + hom_nay, g["dem_don_treo"](14)["so"], 3)
	g = _moi_truong("2026-11-23", _bang("2026-11-23"), [])
	la("đổi kỳ 7 ngày: chỉ còn trong 7 ngày", sorted(r.name for r in g["_quet_don_treo"](7)), ["GIUA", "HOM-QUA"])
	la("đếm kỳ 7 ngày", g["dem_don_treo"](7)["so"], 2)


@ca("UI15 dựng lại số cũ: bộ lọc cũ của trình duyệt đếm dư đơn hôm nay và tương lai")
def _so_cu():
	"""Ghi lại vì sao ô từng lệch: cùng bảng giả, bộ lọc cũ (ngày >= mốc) ra 5,
	màn ra 3. Ca này giữ để không ai đưa bộ lọc ở trình duyệt quay lại."""
	bang = _bang("2026-11-23")
	cu = {"posting_date": [">=", "2026-11-09"], "docstatus": 0, "custom_pancake_id": ["!=", ""],
		"vgb_quay": ["in", ["", None]], "vgb_huy": 0, "vgb_tam_tinh": 0}
	la("bộ lọc cũ đếm cả hôm nay và tương lai", sum(1 for r in bang if _khop(r, cu)), 5)
	g = _moi_truong("2026-11-23", bang, [])
	la("máy chủ đếm đúng như màn", g["dem_don_treo"](14)["so"], 3)
	# Trang chủ gọi dem_don_treo và hiện đúng con số: chạy thật trong
	# hanh_vi/trang_chu_nhanh_pr_b.js (ca "ô Đơn còn treo lấy số máy chủ").
