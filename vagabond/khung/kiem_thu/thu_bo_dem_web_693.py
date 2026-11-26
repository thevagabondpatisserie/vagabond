# -*- coding: utf-8 -*-
"""v693 (26/11/2026): site chạm trần thời gian máy chủ gói Frappe Cloud ngày
25/11 (trang "Daily usage limit reached" tới 07:00 sáng 26/11). Hai hàm trang
khách gọi mỗi phút trên mọi trình duyệt đang mở được đệm cho cả site.

Ca chạy hàm thật của bo_dem_web với Redis giả mô phỏng đúng cách RedisWrapper
của Frappe v16 (get_value nuốt lỗi kết nối và trả None; set nx, ex; make_key):
- bản tươi trả ngay; bản cũ thì CHỈ một request giữ khoá tính lại, request khác
  trả bản cũ (không cùng tính một lúc);
- đầu ngày chưa có bản nào mà khoá đang bị giữ: chờ đọc bản vừa tính, hết giờ
  chờ thì tự tính;
- Redis mất kết nối: tính trực tiếp, trang vẫn có số;
- không có request (việc nền, bench, tạo đơn gọi nội bộ): luôn tính lại;
- tạo đơn không đi qua bộ đệm; nhịp đọc phía trình duyệt chạy thật bằng node."""

import ast
import subprocess
import types
import unittest.mock as um
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]


class _Redis:
	"""Giống RedisWrapper v16 ở những phép bo_dem_web dùng."""

	def __init__(self, mat=False):
		self.kho, self.mat, self.khoa_giu = {}, mat, set()

	def make_key(self, k):
		return ("db|" + k).encode()

	def get_value(self, k, expires=False):
		if self.mat:
			return None  # v16: ConnectionError bị nuốt, trả None
		return self.kho.get(k)

	def set_value(self, k, v, expires_in_sec=None):
		if not self.mat:
			self.kho[k] = v

	def set(self, ten, v, nx=False, ex=None):
		if self.mat:
			raise ConnectionError("redis")
		if nx and ten in self.khoa_giu:
			return None
		self.khoa_giu.add(ten)
		return True

	def delete(self, ten):
		self.khoa_giu.discard(ten)


class _Moc:
	def __init__(self, t=1000.0):
		self.t, self.ngu_tong = t, 0.0

	def bay(self):
		return self.t

	def ngu(self, s):
		self.ngu_tong += s
		self.t += s


def _goi(bd, redis, moc, tinh, co_request=True, ngay="2026-11-26", ten="co_the_ban_hom_nay"):
	fr = types.SimpleNamespace(local=types.SimpleNamespace(), cache=lambda: redis)
	if co_request:
		fr.local.request = object()
	with um.patch.object(bd, "frappe", fr), um.patch("frappe.utils.nowdate", lambda: ngay, create=True):
		return bd.qua_bo_dem(ten, tinh, bay=moc.bay, ngu=moc.ngu)


def _dem():
	d = []

	def tinh():
		d.append(1)
		return {"lan": len(d)}
	return d, tinh


@ca("v693 bộ đệm: bản tươi trả ngay, quá 30 giây thì một request tính lại")
def _tuoi_va_cu():
	from vagabond import bo_dem_web as bd
	r, m = _Redis(), _Moc()
	d, tinh = _dem()
	la("lượt đầu tính", _goi(bd, r, m, tinh), {"lan": 1})
	m.t += 29.9
	la("dưới 30 giây: bản đệm", _goi(bd, r, m, tinh), {"lan": 1})
	m.t += 0.2
	la("quá 30 giây: tính lại", _goi(bd, r, m, tinh), {"lan": 2})
	la("tính đúng hai lần", len(d), 2)
	la("nhả khoá sau khi tính", r.khoa_giu, set())
	k = bd.khoa_dem("co_the_ban_hom_nay", "2026-11-26")
	la("bản đệm ghi kèm giờ tính", r.kho[k], {"luc": m.t, "gt": {"lan": 2}})


@ca("v693 bộ đệm: bản đã cũ mà request khác đang tính thì trả bản cũ, không cùng tính")
def _khong_cung_tinh():
	from vagabond import bo_dem_web as bd
	r, m = _Redis(), _Moc()
	d, tinh = _dem()
	_goi(bd, r, m, tinh)
	m.t += 31
	r.khoa_giu.add(r.make_key(bd.khoa_dem("co_the_ban_hom_nay", "2026-11-26") + ":dang_tinh"))
	ra = [_goi(bd, r, m, tinh) for _ in range(20)]
	la("20 request đồng thời: không ai tính thêm", len(d), 1)
	la("đều nhận bản cũ", ra, [{"lan": 1}] * 20)


@ca("v693 bộ đệm: đầu ngày chưa có bản nào, khoá đang giữ: chờ đọc bản vừa tính, hết giờ thì tự tính")
def _dau_ngay():
	from vagabond import bo_dem_web as bd
	r, m = _Redis(), _Moc()
	k = bd.khoa_dem("co_the_ban_hom_nay", "2026-11-26")
	r.khoa_giu.add(r.make_key(k + ":dang_tinh"))
	d, tinh = _dem()
	goc_ngu = m.ngu

	def ngu_roi_co_ban(s):
		goc_ngu(s)
		if m.ngu_tong >= 0.3:
			r.kho[k] = {"luc": m.t, "gt": {"tu": "request khac"}}
	m.ngu = ngu_roi_co_ban
	la("đọc được bản request khác vừa tính", _goi(bd, r, m, tinh), {"tu": "request khac"})
	la("không tự tính", len(d), 0)
	r2, m2 = _Redis(), _Moc()
	r2.khoa_giu.add(r2.make_key(k + ":dang_tinh"))
	d2, tinh2 = _dem()
	la("không ai ghi: hết giờ chờ thì tự tính", _goi(bd, r2, m2, tinh2), {"lan": 1})
	dung("chờ không quá trần", abs(m2.ngu_tong - bd.CHO_LANH) < 1e-6)


@ca("v693 bộ đệm: Redis mất kết nối hay hàm cache lỗi thì vẫn tính và trả số")
def _redis_loi():
	from vagabond import bo_dem_web as bd
	r, m = _Redis(mat=True), _Moc()
	d, tinh = _dem()
	la("mỗi lượt tự tính", [_goi(bd, r, m, tinh) for _ in range(3)], [{"lan": 1}, {"lan": 2}, {"lan": 3}])

	def cache_hong():
		raise RuntimeError("cache")
	fr = types.SimpleNamespace(local=types.SimpleNamespace(request=object()), cache=cache_hong)
	with um.patch.object(bd, "frappe", fr), um.patch("frappe.utils.nowdate", lambda: "2026-11-26", create=True):
		la("frappe.cache() lỗi: vẫn có số", bd.qua_bo_dem("x", lambda: {"ok": 1}, bay=m.bay, ngu=m.ngu), {"ok": 1})


@ca("v693 bộ đệm: không có request (việc nền, bench, gọi nội bộ) luôn tính lại; đổi ngày là khoá mới")
def _khong_request_va_ngay():
	from vagabond import bo_dem_web as bd
	r, m = _Redis(), _Moc()
	d, tinh = _dem()
	la("ba lượt tính ba lần", [_goi(bd, r, m, tinh, co_request=False) for _ in range(3)][-1], {"lan": 3})
	la("không ghi đệm", r.kho, {})
	d2, tinh2 = _dem()
	_goi(bd, r, m, tinh2, ngay="2026-11-26")
	la("sang ngày mới tính lại dù chưa quá 30 giây", _goi(bd, r, m, tinh2, ngay="2026-11-27"), {"lan": 2})


@ca("v693 hai hàm trang khách đi qua bộ đệm; chỉ hai hàm này, tạo đơn không đi qua")
def _hai_ham():
	from vagabond import bo_dem_web as bd, kiem_banh as kb, kiem_kho as kk
	goi = []

	def gia(ten, tinh, giay=30, **kw):
		goi.append((ten, tinh.__name__))
		return {"tu_dem": ten}
	with um.patch.object(bd, "qua_bo_dem", gia):
		la("có sẵn hôm nay", kb.co_the_ban_hom_nay(), {"tu_dem": "co_the_ban_hom_nay"})
		la("tại quầy", kk.con_tren_quay_web(), {"tu_dem": "con_tren_quay_web"})
	la("đúng hàm tính", goi, [("co_the_ban_hom_nay", "_co_the_ban_hom_nay_tinh"), ("con_tren_quay_web", "_con_tren_quay_web_tinh")])
	# Đồ thị lời gọi của đường tạo đơn và giữ tồn: không gọi hàm đã đệm.
	dem = {"co_the_ban_hom_nay", "con_tren_quay_web", "qua_bo_dem"}
	for tep in ("don_hang.py", "ton_don_web.py", "giu_ton_web.py", "goi_mon_ban.py"):
		cay = ast.parse((GOC / "vagabond" / tep).read_text(encoding="utf-8"))
		ten = {getattr(n.func, "attr", None) or getattr(n.func, "id", None) for n in ast.walk(cay) if isinstance(n, ast.Call)}
		la("đường tạo đơn %s không đọc số đệm" % tep, sorted(ten & dem), [])
	cho_dung = set()
	for p in (GOC / "vagabond").glob("*.py"):
		if "qua_bo_dem(" in p.read_text(encoding="utf-8") and p.name != "bo_dem_web.py":
			cho_dung.add(p.name)
	la("chỉ hai hàm hiển thị dùng bộ đệm", sorted(cho_dung), ["kiem_banh.py", "kiem_kho.py"])


@ca("v693 nhịp đọc phía trình duyệt (nhip-doc.js) chạy thật bằng node: tab ẩn không đọc, không lượt trùng")
def _nhip_node():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/nhip_doc_693.mjs"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-800:] + r.stderr[-800:], r.returncode, 0)
	dung("đủ số ca", "4 ca dat, 0 ca hong" in r.stdout)
