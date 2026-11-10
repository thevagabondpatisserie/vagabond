# -*- coding: utf-8 -*-
"""v638: khách gọi món tại bàn qua mã QR (anh Việt duyệt 04/11/2026).

Ca chạm hệ chạy HÀM THẬT của goi_mon_ban, kiem_kho, ban_hang (mo_ban, goi,
trang_thai, dem_cho, nhan, tu_choi, quet_het_han, con_tren_quay_web, bảng kiểm
kho), chỉ thay tầng Frappe bằng một kho giả có khoá hàng thật (threading) để
chứng minh hai thu ngân bấm nhận cùng lúc chỉ ra MỘT phiếu. Phần trình duyệt
nạp thật trong node: hanh_vi/goi_mon_ban_638.mjs (trang khách Vue),
hanh_vi/goi_mon_quay_638.js (màn quầy, màn In QR), hanh_vi/kiem_kho_nuoc_638.js
(mục Đồ uống trên bảng kiểm kho).
"""

import ast
import contextlib
import datetime
import json
import re
import subprocess
import sys
import threading
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"
if not hasattr(_fr.utils, "get_url_to_form"):
	_fr.utils.get_url_to_form = lambda dt, ten: "https://vagabond.test/app/%s/%s" % (dt, ten)
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

import vagabond as _goi  # noqa: E402
from vagabond import diem_ban, kenh_zalo, kiem_kho, tat_ban_web  # noqa: E402
from vagabond import goi_mon_ban as g  # noqa: E402

GOC = Path(__file__).resolve().parents[3]


def _nap_bh():
	"""Các hàm THẬT của ban_hang.py nạp riêng vào một mô đun thay (ban_hang kéo
	requests ở đầu tệp nên bộ kiểm tầng khung không import cả mô đun, CI tay
	không không có requests). goi_mon_ban nạp ban_hang trong thân hàm; _co_bh() đặt mô đun này vào đúng chỗ đó trong lúc chạy ca."""
	from vagabond import luat_thanh_toan, pt_thanh_toan

	cay = ast.parse((GOC / "vagabond/ban_hang.py").read_text())
	m = types.ModuleType("vagabond.ban_hang")
	gl = m.__dict__
	gl.update(frappe=_fr, flt=_fr.utils.flt, cint=_fr.utils.cint, re=re, json=json,
		luat_thanh_toan=luat_thanh_toan, pt_thanh_toan=pt_thanh_toan)
	hang = ("QUYEN_BAN_HANG_THAT", "QUYEN_BAN_VA_KE_TOAN", "NGUON_CU", "DAU_COMBO", "DAU_GC_MON")
	ham = ("mo_ta_dong", "_dung_dong_mon", "doc_tuy_chon", "_pt_cho_nguon", "_pt_cho_nguon_kem_co", "_kiem_quyen_ban")
	for n in cay.body:
		if isinstance(n, ast.Assign) and len(n.targets) == 1 and getattr(n.targets[0], "id", "") in hang:
			exec(compile(ast.Module(body=[n], type_ignores=[]), "ban_hang.py", "exec"), gl)
		elif isinstance(n, ast.FunctionDef) and n.name in ham:
			n.decorator_list = []
			exec(compile(ast.Module(body=[n], type_ignores=[]), "ban_hang.py", "exec"), gl)
	for k in hang + ham:
		assert k in gl, "ban_hang.py không còn " + k

	def chua_gia(**kw):
		raise AssertionError("ca kiểm phải thay tao_don_tay")
	m.tao_don_tay = chua_gia
	m._nguon_don = lambda: []
	return m


BH = _nap_bh()


@contextlib.contextmanager
def _co_bh():
	# Gói `vagabond` đọc lúc chạy ca, không phải lúc nạp tệp: trong bộ chạy đủ
	# một ca kiểm khác có thể đã thay đối tượng gói trong sys.modules.
	goi_hien = sys.modules.get("vagabond", _goi)
	with patch.dict(sys.modules, {"vagabond.ban_hang": BH}), patch.object(goi_hien, "ban_hang", BH, create=True):
		yield
KHOA = "bi-mat-site-kiem-thu-638"
BAY = datetime.datetime(2026, 11, 4, 10, 0, 0)
TRA = {"item_code": "NUTR00021", "item_name": "Trà Hoa Lài", "image": "/files/tra.jpg", "standard_rate": 45000,
	"item_group": "Trà", "disabled": 0, "is_sales_item": 1, "has_variants": 0}
CF = {"item_code": "NUCF00003", "item_name": "Cà phê sữa", "image": "", "standard_rate": 40000,
	"item_group": "Cà phê", "disabled": 0, "is_sales_item": 1, "has_variants": 0}
TC = [{"nhom": "Đá", "lua_chon": ["Ít đá", "Không đá"], "nhom_mon": ["Trà", "Cà phê"]},
	{"nhom": "Đường", "lua_chon": ["50% đường", "Không đường"], "nhom_mon": []},
	{"nhom": "Size", "lua_chon": ["L"], "nhom_mon": ["Matcha"]}]
BANH = [{"ma": "BAWC00115", "ten": "Mousse Chanh Dây", "con": 2, "gia_chung": 95000, "nhom": "Bánh lạnh", "anh_goc": ""}]


# ------------------------------------------------------------------ phần thuần

@ca("v638 chữ ký QR: đúng điểm đúng bàn thì nhận; đổi bàn, đổi điểm, sai khoá, khoá site khác, khoá sai dạng đều từ chối")
def _ky():
	k = g.khoa_ban(KHOA, "TCV", 5)
	dung("16 hex", re.fullmatch(r"[0-9a-f]{16}", k))
	dung("đúng", g.dung_khoa(KHOA, "TCV", 5, k))
	dung("số bàn gõ chuỗi vẫn đúng", g.dung_khoa(KHOA, "tcv", " 05 ", k))
	dung("đổi sang bàn 6 với khoá bàn 5", not g.dung_khoa(KHOA, "TCV", 6, k))
	dung("đổi điểm", not g.dung_khoa(KHOA, "NVHTN", 5, k))
	dung("khoá site khác", not g.dung_khoa("khac", "TCV", 5, k))
	dung("khoá sai một ký tự", not g.dung_khoa(KHOA, "TCV", 5, k[:-1] + ("0" if k[-1] != "0" else "1")))
	for x in ("", None, k.upper(), k + "0", "<script>", 12345):
		dung("khoá dạng lạ %r" % (x,), not g.dung_khoa(KHOA, "TCV", 5, x))
	for b in (0, 100, "-1", "5a", None, ""):
		dung("bàn %r không hợp lệ" % (b,), not g.dung_khoa(KHOA, "TCV", b, k))
	nem("site chưa có khoá", lambda: g.khoa_ban("", "TCV", 5), ValueError)
	la("đường QR", g.duong_qr("tcv", "5", k), "/banh?diem=TCV&ban=5&k=%s#/in-store" % k)
	# v647: tên bàn là chuỗi (bàn theo khu A1, B1); bàn số giữ chuỗi "5" nên
	# khoá và link QR bàn số in trước v647 không đổi (thu_qr_ban_khu_647).
	la("khoảng bàn, gõ ngược vẫn đúng", g.ds_ban(5, 2), ["2", "3", "4", "5"])
	la("bàn sai", g.ds_ban(0, 5), [])
	la("trần một lần in", len(g.ds_ban(1, 99)), g.TO_QR_TOI_DA)


@ca("v638 nhóm nước MỘT nguồn: JS màn quầy (lưới đỡ) trùng goi_mon_ban.NHOM_NUOC; cấu hình bán hàng gửi danh sách xuống")
def _nhom_nuoc():
	s = (GOC / "vagabond/public/js/bep/10-bill-quay.js").read_text()
	m = re.search(r"var POS_NHOM_NUOC = (\[[^\]]*\]);", s)
	la("JS trùng máy chủ", json.loads(m.group(1).replace("'", '"')), list(g.NHOM_NUOC))
	src = (GOC / "vagabond/ban_hang.py").read_text()
	dung("cau_hinh_ban_hang gửi nhom_nuoc từ goi_mon_ban", '"nhom_nuoc": list(_goi_mon_ban().NHOM_NUOC)' in src)
	dung("topping không phải món nước", not g.la_do_uong("Topping cho món nước"))


@ca("v638 đồ uống của điểm: đúng năm nhóm nước, bỏ topping, món ngừng, không phải hàng bán, mẫu biến thể, không giá; giá điểm thắng giá chung")
def _loc():
	rows = [TRA, CF,
		dict(TRA, item_code="TOP1", item_group="Topping cho món nước"),
		dict(TRA, item_code="NGUNG", disabled=1),
		dict(TRA, item_code="KHONGBAN", is_sales_item=0),
		dict(TRA, item_code="MAU", has_variants=1),
		dict(TRA, item_code="KHONGGIA", standard_rate=0),
		dict(TRA, item_code="KEM", item_group="Ice Cream - Kem", item_name="Kem vani", standard_rate=30000)]
	ds = g.loc_do_uong(rows, {"NUTR00021": 50000, "KHONGGIA": 20000}, {"NUCF00003": {"tat": 1, "den_ngay": "2026-11-04"}})
	la("mã, xếp theo thứ tự nhóm nước", [x["ma"] for x in ds], ["NUTR00021", "KHONGGIA", "NUCF00003", "KEM"])
	la("giá điểm", [x["gia"] for x in ds], [50000, 20000, 40000, 30000])
	la("cờ bán web", [x["ban_web"] for x in ds], [1, 1, 0, 1])


@contextlib.contextmanager
def _item(rows, gia_diem=None):
	def get_all(dt, **k):
		if dt == "Item":
			loc = k.get("filters") or {}
			nhom = (loc.get("item_group") or ["in", None])[1]
			ma = (loc.get("item_code") or ["in", None])[1]
			return [_fr._dict(r) for r in rows if (nhom is None or r.get("item_group") in nhom) and (ma is None or r["item_code"] in ma)]
		return []
	with patch.object(_fr, "get_all", side_effect=get_all), patch.object(diem_ban, "gia_rieng", return_value=dict(gia_diem or {})):
		yield


@ca("v638 tắt đồ uống trên bảng kiểm kho: tắt tới hết hôm nay (dùng tat_ban_web), sáng mai tự bật; cửa tắt chỉ nhận đồ uống")
def _tat_hom_nay():
	tat = dict(CF, **{tat_ban_web.TRUONG: "2026-11-04"})
	with _item([TRA, tat]):
		hom_nay = kiem_kho._do_uong_bang("TCV", datetime.date(2026, 11, 4))
		mai = kiem_kho._do_uong_bang("TCV", datetime.date(2026, 11, 5))
	la("hôm nay cà phê tắt", [(x["ma_hang"], x["ban_web"]) for x in hom_nay], [("NUTR00021", 1), ("NUCF00003", 0)])
	la("sáng mai tự bật", [x["ban_web"] for x in mai], [1, 1])
	ghi = []
	with patch.object(kiem_kho, "_chan_neu_khong_duoc_sua"), patch.object(kiem_kho, "_kiem_diem"), \
			patch.object(_fr.db, "get_value", side_effect=lambda dt, ma, f=None, **k: {"NUCF00003": "Cà phê", "BAWC00115": "Bánh lạnh"}.get(ma)), \
			patch.object(tat_ban_web, "ghi", side_effect=lambda *a: ghi.append(a) or {"tat": a[1]}):
		kiem_kho.ban_web_do_uong("TCV", "NUCF00003", 0, "2026-11-04")
		kiem_kho.ban_web_do_uong("TCV", "NUCF00003", 1, None)
		nem("mã bánh không qua cửa đồ uống", lambda: kiem_kho.ban_web_do_uong("TCV", "BAWC00115", 0), _fr.ValidationError)
	la("tắt tới hết ngày đang xem, bật thì xoá ô", ghi, [("NUCF00003", 1, "2026-11-04"), ("NUCF00003", 0, None)])


@ca("v638 tab Tại quầy: đồ uống chỉ ở quầy có món, trong khoá riêng do_uong; khoá mon (tab cũ, editor đọc) không có đồ uống; giá theo bảng giá điểm")
def _tren_quay():
	diem = [dict(ma="TCV", ten="The Vagabond District 1", ten_ngan="District 1", dia_chi="9 TCV", quay="TCV"),
		dict(ma="NVHTN", ten="Nhà Văn Hóa Thanh Niên", ten_ngan="NVHTN", dia_chi="21 PNT", quay="NVHTN")]
	nuoc = {"TCV": g.loc_do_uong([TRA, CF], {}, {"NUCF00003": {"tat": 1}}), "NVHTN": []}
	lib = sys.modules.get("vagabond.lib")
	with patch.object(kiem_kho, "_diem_co_quay", return_value=diem), \
			patch.object(kiem_kho, "banh_tren_quay", side_effect=lambda ma, ngay=None: BANH if ma == "TCV" else []), \
			patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: nuoc[ma]), \
			patch.object(g, "doc_tuy_chon", return_value=TC), \
			patch.object(diem_ban, "gia_rieng", side_effect=lambda ma: {"BAWC00115": 99000} if ma == "TCV" else {}), \
			patch.object(lib, "cfg", return_value=_fr._dict(pancake_shop_id="")), patch.object(lib, "key", return_value=""):
		ra = kiem_kho.con_tren_quay_web()
	q = {x["ma"]: x for x in ra["quay"]}
	la("TCV bánh trong mon", [m["ma"] for m in q["TCV"]["mon"]], ["BAWC00115"])
	la("giá bánh theo điểm", q["TCV"]["mon"][0]["gia"], 99000)
	la("TCV đồ uống đang bật", [m["ma"] for m in q["TCV"]["do_uong"]], ["NUTR00021"])
	la("nhóm hiển thị", q["TCV"]["do_uong"][0]["nhom"], "Đồ uống")
	la("lựa chọn đá đường của trà, không có Size Matcha", [n["nhom"] for n in q["TCV"]["do_uong"][0]["tc"]], ["Đá", "Đường"])
	dung("đồ uống không có số còn", "con" not in q["TCV"]["do_uong"][0])
	la("NVHTN không có đồ uống", q["NVHTN"]["do_uong"], [])
	dung("không đồ uống nào lọt vào mon", not any(m["ma"].startswith("NU") for x in ra["quay"] for m in x["mon"]))


def _bang():
	return {
		"NUTR00021": {"ten": "Trà Hoa Lài", "gia": 45000, "loai": "nuoc", "nhom_goc": "Trà", "tc": g.tuy_chon_cho("Trà", TC)},
		"BAWC00115": {"ten": "Mousse Chanh Dây", "gia": 95000, "loai": "banh", "con": 2, "nhom_goc": "Bánh lạnh"},
	}


@ca("v638 giỏ: giá máy chủ (giá giả trình duyệt bỏ qua), gộp cùng lựa chọn, chặn quá số bánh, món tắt, lựa chọn lạ, số lượng lạ")
def _gio():
	dong, tam = g.chuan_gio([
		{"ma": "NUTR00021", "sl": 1, "tc": {"Đá": "Ít đá"}, "gia": 1},
		{"ma": "NUTR00021", "sl": 2, "tc": {"Đá": "Ít đá"}},
		{"ma": "NUTR00021", "sl": 1, "tc": {}},
		{"ma": "BAWC00115", "sl": 2, "gia": 0}], _bang())
	la("dòng", [(d["ma"], d["sl"], d["tc"], d["gia"]) for d in dong],
		[("NUTR00021", 3, ["Ít đá"], 45000), ("NUTR00021", 1, [], 45000), ("BAWC00115", 2, [], 95000)])
	la("tạm tính máy chủ", tam, 4 * 45000 + 2 * 95000)
	for gio, cau in (
		([{"ma": "BAWC00115", "sl": 3}], "chỉ còn 2"),
		([{"ma": "BAWC00115", "sl": 1}, {"ma": "BAWC00115", "sl": 2}], "chỉ còn 2"),
		([{"ma": "NUCF00003", "sl": 1}], "ngừng bán"),
		([{"ma": "NUTR00021", "sl": 1, "tc": {"Đá": "Nhiều đá"}}], "không có"),
		([{"ma": "NUTR00021", "sl": 1, "tc": {"Size": "L"}}], "không có"),
		([{"ma": "NUTR00021", "sl": 0}], "từ 1 tới"),
		([{"ma": "NUTR00021", "sl": 21}], "từ 1 tới"),
		([], "chưa có món"), ("khong-phai-json", "không đọc được")):
		try:
			g.chuan_gio(gio, _bang())
			la("phải chặn %r" % (gio,), "không chặn", cau)
		except ValueError as e:
			dung("câu chặn %r có '%s' (được: %s)" % (gio, cau, e), cau in str(e))
	b = _bang()
	b["BAWC00115"]["con"] = 0
	try:
		g.chuan_gio([{"ma": "BAWC00115", "sl": 1}], b)
	except ValueError as e:
		dung("hết trên tủ nói bỏ ra khỏi giỏ", "vừa hết" in str(e))


# ------------------------------------------------------------ kho giả có khoá

class Kho:
	"""Bảng Vagabond Goi Mon Ban giả: ghi, đọc, khoá hàng `for update` giữ tới
	commit/rollback của ĐÚNG luồng gọi (như InnoDB), cột nonce duy nhất."""

	def __init__(self):
		self.dong = {}
		# v639: bảng Vagabond Goi Nhan Vien giả (lời bấm chuông).
		self.tg = {}
		self.so_tg = 0
		# Phiếu Sales Invoice giả cho câu hỏi "phiếu tạm tính còn mở không".
		self.phieu = {}
		self.khoa = {}
		self.khoa_ten = {}
		self.goi_khoa = []
		self.cua = threading.local()
		self.so = 0
		self.mu = threading.Lock()

	def _giu(self):
		if not hasattr(self.cua, "giu"):
			self.cua.giu = []
		return self.cua.giu

	def nha(self):
		for k in self._giu():
			self.khoa[k].release()
		self.cua.giu = []

	def _bang(self, dt):
		return self.dong if dt == g.DT else (self.tg if dt == g.DT_TG else (self.phieu if dt == "Sales Invoice" else None))

	def get_value(self, dt, ten, truong=None, as_dict=False, **k):
		bang = self._bang(dt)
		if bang is None:
			return None
		if isinstance(ten, dict):
			r = next((r for r in bang.values() if all(r.get(a) == b for a, b in ten.items())), None)
		else:
			r = bang.get(ten)
		if not r:
			return None
		if isinstance(truong, (list, tuple)):
			d = _fr._dict({f: r.get(f) for f in truong})
			return d if as_dict else [r.get(f) for f in truong]
		return r.get(truong or "name")

	def set_value(self, dt, ten, truong, gt=None, **k):
		bang = self._bang(dt)
		if bang is None or ten not in bang:
			return
		bang[ten].update(truong if isinstance(truong, dict) else {truong: gt})

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		ra = []
		for r in (self._bang(dt) or {}).values():
			ok = True
			for a, b in (filters or {}).items():
				if isinstance(b, list) and b[0] == "<=":
					ok = ok and r.get(a) <= b[1]
				elif isinstance(b, list) and b[0] == ">=":
					ok = ok and r.get(a) >= b[1]
				elif isinstance(b, list) and b[0] == "in":
					ok = ok and r.get(a) in b[1]
				elif isinstance(b, list) and b[0] == "!=":
					ok = ok and r.get(a) != b[1]
				else:
					ok = ok and r.get(a) == b
			if ok:
				ra.append(r[pluck] if pluck else _fr._dict(r))
		return ra

	def sql(self, cau, ts=None, as_dict=False, **k):
		# Khoá tên MariaDB (get_lock/release_lock): giữ theo LUỒNG như theo kết nối.
		if "get_lock(" in cau:
			with self.mu:
				kt = self.khoa_ten.setdefault(ts[0], threading.Lock())
			ok = kt.acquire(timeout=float(ts[1]))
			self.goi_khoa.append(("lay", ts[0], ok, threading.get_ident()))
			return [[1 if ok else 0]]
		if "release_lock(" in cau:
			kt = self.khoa_ten.get(ts[0])
			if kt and kt.locked():
				kt.release()
			self.goi_khoa.append(("nha", ts[0], threading.get_ident()))
			return [[1]]
		if cau.lstrip().lower().startswith("update") and "set trang_thai" in cau:
			# update ... set trang_thai = moi where name = x and trang_thai = cu
			moi, ten, cu = ts
			r = (self.tg if g.DT_TG in cau else self.dong).get(ten)
			if r and r.get("trang_thai") == cu:
				r["trang_thai"] = moi
			return []
		if "for update" in cau:
			ma = ts[0]
			if ma not in self.khoa:
				self.khoa[ma] = threading.Lock()
			if ma not in self._giu():
				self.khoa[ma].acquire()
				self._giu().append(ma)
			r = self.dong.get(ma)
			return [_fr._dict(r)] if r else []
		return []

	def them(self, d):
		bang = self.tg if d.get("doctype") == g.DT_TG else self.dong
		with self.mu:
			if any(r.get("nonce") == d.get("nonce") for r in bang.values()):
				raise Exception("DuplicateEntryError nonce")
			if bang is self.tg:
				self.so_tg += 1
				ten = "GNV-261105-%04d" % self.so_tg
			else:
				self.so += 1
				ten = "TQ-261104-%04d" % self.so
		d = dict(d, name=ten)
		bang[ten] = d
		return ten


class Doc(_fr._dict):
	def __init__(self, kho, d):
		super().__init__(d)
		self._kho = kho

	def insert(self, **k):
		self["name"] = self._kho.them({x: y for x, y in self.items() if x != "_kho"})
		return self

	def as_dict(self):
		return {x: y for x, y in self.items() if x != "_kho"}


@contextlib.contextmanager
def _he(kho, bay=BAY, mo=True, gt=None):
	"""Dựng tầng Frappe giả quanh các hàm thật của goi_mon_ban."""
	tin = []
	cu_db = (_fr.db.get_value, _fr.db.set_value, _fr.db.sql, _fr.db.commit, _fr.db.rollback)
	_fr.db.get_value, _fr.db.set_value, _fr.db.sql = kho.get_value, kho.set_value, kho.sql
	_fr.db.commit = lambda *a, **k: (kho.goi_khoa.append(("commit", threading.get_ident())), kho.nha())
	_fr.db.rollback = lambda *a, **k: kho.nha()
	# `from vagabond import gioi_thieu` đọc THUỘC TÍNH của gói trước sys.modules: khi mô
	# đun thật đã được nạp (ca thu_gioi_thieu_638 chạy trước) phải thay cả hai chỗ.
	import vagabond as _goi
	mod_gt = sys.modules.pop("vagabond.gioi_thieu", None)
	thuoc_tinh_gt = _goi.__dict__.pop("gioi_thieu", None)
	if gt is not None:
		sys.modules["vagabond.gioi_thieu"] = gt
		_goi.gioi_thieu = gt
	try:
		with _co_bh(), patch.object(_fr, "get_all", side_effect=kho.get_all), \
				patch.object(_fr, "get_doc", side_effect=lambda d, *a, **k: Doc(kho, d) if isinstance(d, dict) else None), \
				patch.object(g, "_bi_mat", return_value=KHOA), patch.object(g, "now_datetime", side_effect=lambda: bay[0] if isinstance(bay, list) else bay), \
				patch.object(diem_ban, "cfg_o", return_value=""), \
				patch.object(g, "_gio_mo_cua", side_effect=lambda d, b: {"dang_mo": mo, "gio": "7:00 - 22:00"}), \
				patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: g.loc_do_uong([TRA], {}, {})), \
				patch.object(g, "doc_tuy_chon", return_value=TC), \
				patch.object(kiem_kho, "banh_tren_quay", side_effect=lambda ma, ngay=None: [dict(x) for x in BANH] if ma == "TCV" else []), \
				patch.object(diem_ban, "gia_rieng", return_value={}), \
				patch.object(kenh_zalo, "bao", side_effect=lambda *a, **k: tin.append((a, k))), \
				patch("vagabond.lien_ket_app.goc_app", return_value="https://app.vagabond.test"):
			yield tin
	finally:
		_fr.db.get_value, _fr.db.set_value, _fr.db.sql, _fr.db.commit, _fr.db.rollback = cu_db
		sys.modules.pop("vagabond.gioi_thieu", None)
		_goi.__dict__.pop("gioi_thieu", None)
		if mod_gt is not None:
			sys.modules["vagabond.gioi_thieu"] = mod_gt
		if thuoc_tinh_gt is not None:
			_goi.gioi_thieu = thuoc_tinh_gt


def _k(ban=5, diem="TCV"):
	return g.khoa_ban(KHOA, diem, ban)


def _gui(nonce="N" * 32, ban=5, mon=None, **kw):
	return g.goi(diem=kw.pop("diem", "TCV"), ban=ban, k=kw.pop("k", _k(ban)), nonce=nonce,
		mon=json.dumps(mon if mon is not None else [{"ma": "NUTR00021", "sl": 2, "tc": {"Đá": "Ít đá"}, "gia": 1}]), **kw)


@ca("v638 mở link: đúng thì trả điểm, bàn, mở cửa; sai khoá, đổi bàn, điểm không có quầy thì ok 0 (trang ở chế độ xem)")
def _mo_ban():
	kho = Kho()
	with _he(kho):
		r = g.mo_ban("TCV", "5", _k())
		la("link đúng", (r["ok"], r["diem"], r["ten"], r["ban"], r["mo_cua"]), (1, "TCV", "District 1", "5", 1))
		la("đổi bàn", g.mo_ban("TCV", "6", _k(5)), {"ok": 0})
		la("điểm Sales Online không có quầy", g.mo_ban("SALES", "5", g.khoa_ban(KHOA, "SALES", 5)), {"ok": 0})
		la("khoá rỗng", g.mo_ban("TCV", "5", ""), {"ok": 0})
	with _he(kho, mo=False):
		la("ngoài giờ: link vẫn đúng nhưng chỉ xem", g.mo_ban("TCV", "5", _k())["mo_cua"], 0)


@ca("v638 gọi món: k sai, ngoài giờ, món tắt, quá số bánh đều không ghi; giá giả bỏ qua; một nonce bấm hai lần ra một đơn; quá 3 đơn chờ một bàn thì chặn")
def _goi():
	kho = Kho()
	with _he(kho, mo=False):
		la("ngoài giờ", (_gui()["ok"], len(kho.dong)), (0, 0))
	with _he(kho) as tin:
		la("k sai", (_gui(k="0" * 16)["ok"], len(kho.dong)), (0, 0))
		la("k của bàn khác", (_gui(k=_k(6))["ok"], len(kho.dong)), (0, 0))
		r = _gui(mon=[{"ma": "NUCF00003", "sl": 1}])
		dung("món không bán (cà phê đang tắt)", r["ok"] == 0 and "ngừng bán" in r["cau"] and r.get("tai_lai"))
		r = _gui(mon=[{"ma": "BAWC00115", "sl": 3}])
		dung("quá số bánh trên tủ", r["ok"] == 0 and "chỉ còn 2" in r["cau"])
		la("chưa ghi gì", len(kho.dong), 0)
		r = _gui(ten="Lan", sdt_gioi_thieu="0909 123 456", ghi_chu="ít ngọt")
		la("ghi một đơn", (r["ok"], len(kho.dong)), (1, 1))
		d = kho.dong[r["ma"]]
		la("giá máy chủ, không theo giá 1 đồng", (d["tam_tinh"], json.loads(d["mon"])[0]["gia"]), (90000, 45000))
		la("số giới thiệu chỉ chữ số", d["sdt_gioi_thieu"], "0909123456")
		la("token khách băm", d["token_bam"], g.bam(r["token"]))
		r2 = _gui(ten="Lan")
		la("bấm hai lần cùng nonce: cùng đơn, không thêm bản ghi", (r2["ma"], r2.get("lap_lai"), len(kho.dong)), (r["ma"], 1, 1))
		la("tin Zalo đúng một lần, đúng mã tin", [k["ma_tin"] for a, k in tin], ["bh_goi_mon_tai_ban"])
		a, k = tin[0]
		dung("tin không có số tiền (luật bộ phận Bán hàng)", not any(kenh_zalo.MAU_TIEN.search(x) for x in [a[2]] + list(a[3])))
		dung("tin nêu bàn, điểm, món, link app", "Bàn 5" in a[2] and "District 1" in a[2] and any("Trà Hoa Lài x2 (Ít đá)" in x for x in a[3])
			and "https://app.vagabond.test/ban-tai-quay" in a[3][-1])
		la("hỏi lại trước khi gửi", (k["kiem"], kenh_zalo.DIEU_KIEN["goi_mon_cho"]), ("goi_mon_cho", "vagabond.goi_mon_ban.con_cho_nhan"))
		_gui(nonce="B" * 32)
		_gui(nonce="C" * 32)
		r = _gui(nonce="D" * 32)
		dung("đơn thứ tư khi bàn còn 3 đơn chờ", r["ok"] == 0 and "đang có 3 đơn chờ" in r["cau"])
		la("vẫn 3 đơn", len(kho.dong), 3)
		la("bàn khác vẫn gọi được", _gui(nonce="E" * 32, ban=7)["ok"], 1)
		r = _gui(nonce="F" * 32, ban=8, mon=[{"ma": "BAWC00115", "sl": 1}, {"ma": "NUTR00021", "sl": 1}])
		la("bánh còn 2: một bàn gọi 1", r["ok"], 1)
		r = _gui(nonce="G" * 32, ban=9, mon=[{"ma": "BAWC00115", "sl": 2}])
		dung("đơn chờ đã giữ 1 bánh: bàn khác gọi 2 thì chặn", r["ok"] == 0 and "chỉ còn 1" in r["cau"])
		la("mã lần gửi khác bàn không trả đơn bàn khác", _gui(nonce="F" * 32, ban=10)["ok"], 0)


@ca("v638 nonce chạy song song: hai lượt cùng mã lần gửi, lượt sau vấp cột duy nhất thì trả đúng đơn của lượt trước")
def _nonce_dua():
	kho = Kho()
	with _he(kho):
		goc = kho.get_value

		def tre(dt, ten, *a, **k):
			# Lần tra đầu của lượt sau không thấy (lượt trước chưa ghi), như hai
			# yêu cầu chạy song song.
			if isinstance(ten, dict) and ten.get("nonce") == "Z" * 32 and not getattr(tre, "da", 0):
				tre.da = 1
				return None
			return goc(dt, ten, *a, **k)
		r1 = _gui(nonce="Z" * 32)
		_fr.db.get_value = tre
		r2 = _gui(nonce="Z" * 32)
	la("một đơn", (len(kho.dong), r2["ma"], r2.get("lap_lai")), (1, r1["ma"], 1))


@ca("Codex PR #541 vòng 2: hai bàn gọi cùng lúc (mã lần gửi khác nhau), cùng đọc bảng món trước khi đơn kia ghi: chỉ MỘT bàn lấy được 2 bánh cuối; khoá theo điểm luôn được nhả")
def _hai_ban_dua():
	kho = Kho()
	cho = threading.Barrier(2)
	that = g.bang_mon

	def doc_roi_doi(*a, **k):
		r = that(*a, **k)
		# Đúng chuỗi Codex: hai luồng cùng dừng ngay sau khi đọc bảng món. Có khoá
		# theo điểm thì luồng sau không tới được đây khi luồng trước chưa xong, rào hết giờ.
		try:
			cho.wait(timeout=1.5)
		except threading.BrokenBarrierError:
			pass
		return r
	kq = {}
	with _he(kho), patch.object(g, "bang_mon", side_effect=doc_roi_doi):
		def chay(ban, nonce):
			kq[ban] = _gui(nonce=nonce, ban=ban, mon=[{"ma": "BAWC00115", "sl": 2}])
		ts = [threading.Thread(target=chay, args=(5, "P" * 32)), threading.Thread(target=chay, args=(9, "Q" * 32))]
		for x in ts:
			x.start()
		for x in ts:
			x.join(20)
	ok = sorted(b for b, r in kq.items() if r.get("ok"))
	la("đúng một bàn gọi được", len(ok), 1)
	la("tổng bánh đang giữ không vượt số trên tủ", sum(g.sl_dang_cho([r.get("mon") for r in kho.dong.values()]).values()), 2)
	thua = [r for b, r in kq.items() if not r.get("ok")]
	dung("bàn kia nghe câu hết bánh", len(thua) == 1 and "vừa hết" in thua[0]["cau"])
	lay = [x for x in kho.goi_khoa if x[0] == "lay"]
	nha = [x for x in kho.goi_khoa if x[0] == "nha"]
	la("khoá đúng tên theo điểm, lấy bao nhiêu nhả bấy nhiêu", ({x[1] for x in lay}, len(lay), len(nha)), ({"vgb_goi_mon_ban:TCV"}, 2, 2))
	dung("khoá không còn bị giữ", not any(k.locked() for k in kho.khoa_ten.values()))
	# Đơn được ghi phải COMMIT trước khi nhả khoá, không thì luồng sau đọc tồn
	# lúc đơn trước chưa hiện ra với nó (kho giả không mô phỏng cô lập giao dịch).
	thu_tu = {}
	for x in kho.goi_khoa:
		if x[0] in ("commit", "nha"):
			thu_tu.setdefault(x[-1], []).append(x[0])
	dung("mỗi lượt gọi được: commit rồi mới nhả khoá", sum(1 for v in thu_tu.values() if "commit" in v and v.index("commit") < v.index("nha")) == 1)
	# Khoá đang bị giữ quá lâu: không ghi đơn, câu mời gọi lại, không nhả khoá của người khác.
	kho2 = Kho()
	kho2.khoa_ten["vgb_goi_mon_ban:TCV"] = threading.Lock()
	kho2.khoa_ten["vgb_goi_mon_ban:TCV"].acquire()
	with _he(kho2), patch.object(g, "_lay_khoa", side_effect=lambda ten, giay=10: bool(kho2.sql("select get_lock(%s, %s)", (ten, 0.05))[0][0])):
		r = _gui(nonce="R" * 32)
	dung("chờ khoá quá hạn: không ghi, mời gọi lại", r["ok"] == 0 and "lại sau vài giây" in r["cau"] and not kho2.dong)


@ca("Codex PR #541 vòng 7: bàn khác gọi món đúng lúc quầy đang lập phiếu cho đơn vừa nhận (Đã nhận, chưa có phiếu): bánh của đơn đó vẫn được giữ")
def _goi_luc_dang_lap_phieu():
	kho = Kho()
	with _he(kho):
		r = _gui(ban=5, mon=[{"ma": "BAWC00115", "sl": 2}])
	kq = {}
	that = g._vao_phieu_tam

	def xen_goi(rr):
		# Đúng chuỗi Codex: một lượt goi() của bàn 9 chạy ngay đầu _vao_phieu_tam().
		with _he(kho):
			kq["ban9"] = _gui(nonce="U" * 32, ban=9, mon=[{"ma": "BAWC00115", "sl": 2}])
		return that(rr)
	with _quay(kho) as (tao, si), patch.object(g, "_vao_phieu_tam", side_effect=xen_goi), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho.set_value(dt, *a, **k) if dt == g.DT else None):
		g.nhan(r["ma"])
	dung("bàn 9 không lấy được 2 bánh bàn 5 đang nhận", kq["ban9"]["ok"] == 0 and "vừa hết" in kq["ban9"]["cau"])
	la("phép thuần: đã nhận, chưa có phiếu, hôm nay thì giữ", g.mon_dang_giu([], [{"mon": "m", "hoa_don": None, "nhan_luc": BAY}], set(), BAY.date()), ["m"])
	la("phép thuần: đã nhận, chưa có phiếu, hôm trước thì thôi", g.mon_dang_giu([], [{"mon": "m", "hoa_don": "", "nhan_luc": "2026-11-03 21:00:00"}], set(), BAY.date()), [])


class SI(_fr._dict):
	def __init__(self, ten, items=None):
		super().__init__(name=ten, docstatus=0, vgb_tam_tinh=1, vgb_huy=0, items=list(items or []), vgb_ghi_chu="")
		self.flags = types.SimpleNamespace()
		self.luu = 0

	def __setattr__(self, k, v):
		# Như Document thật: gán thuộc tính là gán ô.
		if k in ("flags", "luu"):
			object.__setattr__(self, k, v)
		else:
			self[k] = v

	def append(self, bang, d):
		self[bang].append(d)

	def save(self, **k):
		self.luu += 1


def _gt_mo_dun(goi=None):
	m = types.ModuleType("vagabond.gioi_thieu")
	# v638 gộp: máy chủ hỏi tên qua ten_theo_sdt, KHÔNG qua cửa khách kiem (cửa đó có
	# giới hạn lượt theo IP của khách đang gọi món). Giữ kiem để bắt nếu ai gọi lại nó.
	m.ten_theo_sdt = lambda sdt: "Chị Dễ" if sdt == "0909123456" else ""
	m.kiem = lambda sdt=None: (_ for _ in ()).throw(AssertionError("không được gọi cửa khách kiem từ máy chủ"))
	m.gan_cho_hoa_don = lambda si, sdt, kenh: (goi if goi is not None else []).append((si.name, sdt, kenh))
	return m


@contextlib.contextmanager
def _quay(kho, phieu_co="", gt=None):
	tao, si = [], {}

	def get_doc(dt, ten=None, *a, **k):
		if isinstance(dt, dict):
			return Doc(kho, dt)
		if dt == "Sales Invoice":
			si.setdefault(ten, SI(ten, [{"item_code": "BAWC00115", "qty": 1, "rate": 95000}]))
			return si[ten]
		return None

	def tao_don_tay(**kw):
		tao.append(kw)
		return {"name": "ACC-SINV-NEW%d" % len(tao), "grand_total": 0}
	with _he(kho, gt=gt), patch.object(_fr, "get_doc", side_effect=get_doc), \
			patch.object(BH, "_kiem_quyen_ban"), patch.object(BH, "tao_don_tay", side_effect=tao_don_tay), \
			patch.object(g, "_phieu_tam_cua_ban", return_value=phieu_co), \
			patch.object(_fr.db, "get_value", side_effect=lambda dt, ten, f=None, **k: (
				kho.get_value(dt, ten, f, **k) if dt == g.DT else ({"NUTR00021": "Trà Hoa Lài"}.get(ten) if dt == "Item" else "TCVABCDE"))):
		yield tao, si


@ca("v638 nhận đơn: bàn có phiếu tạm tính hôm nay thì THÊM món vào đó (đúng mô tả đá đường); chưa có thì lập qua tao_don_tay, nguồn QR tại bàn; gọi hook giới thiệu")
def _nhan():
	kho = Kho()
	goi_gt = []
	with _he(kho, gt=_gt_mo_dun()):
		r = _gui(sdt_gioi_thieu="0909123456", ghi_chu="ít ngọt")
	la("tên người giới thiệu lấy lúc gọi", kho.dong[r["ma"]]["ten_gioi_thieu"], "Chị Dễ")
	with _quay(kho, phieu_co="ACC-SINV-CO", gt=_gt_mo_dun(goi_gt)) as (tao, si), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho.set_value(dt, *a, **k) if dt == g.DT else None):
		kq = g.nhan(r["ma"])
	la("thêm vào phiếu có sẵn, không lập mới", (kq["hoa_don"], kq["them_vao"], tao), ("ACC-SINV-CO", 1, []))
	dong = si["ACC-SINV-CO"]["items"]
	la("phiếu có thêm dòng trà", [(x["item_code"], x["qty"], x["rate"]) for x in dong],
		[("BAWC00115", 1, 95000), ("NUTR00021", 2.0, 45000.0)])
	la("mô tả mang lựa chọn như màn quầy", dong[-1]["description"], "Trà Hoa Lài\n[Ít đá]")
	dung("ghi chú bàn vào ghi chú phiếu", "Bàn 5 gọi qua QR: ít ngọt" in si["ACC-SINV-CO"]["vgb_ghi_chu"])
	la("bản ghi đã nhận, trỏ phiếu", (kho.dong[r["ma"]]["trang_thai"], kho.dong[r["ma"]]["hoa_don"]), ("Đã nhận", "ACC-SINV-CO"))
	la("hook giới thiệu", goi_gt, [("ACC-SINV-CO", "0909123456", "tai_ban")])
	la("phiếu pha chế cho posInPhieuMon", (kq["phieu"]["so_ban"], kq["phieu"]["mon"][0]["tc"], kq["phieu"]["mon"][0]["nhom"]), ("5", ["Ít đá"], "Trà"))

	kho2 = Kho()
	with _he(kho2):
		r = _gui(ban=9, ten="An")
	nguon = []
	with _quay(kho2) as (tao, si), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho2.set_value(dt, *a, **k) if dt == g.DT else nguon.append((dt,) + a)):
		kq = g.nhan(r["ma"])
	la("lập mới một phiếu", len(tao), 1)
	t = tao[0]
	la("đúng đường tao_don_tay tạm tính", (t["nguon"], t["quay"], t["tam_tinh"], t["so_ban"], t["ten_khach"]), ("Tại chỗ", "TCV", 1, "9", "An"))
	la("dòng giỏ", t["items"], [{"item_code": "NUTR00021", "qty": 2, "rate": 45000.0, "tuy_chon": "Ít đá"}])
	dung("mã bill theo tiền tố điểm", re.fullmatch(r"TCV[ACDEFGHJKLMNPQRSTUVWXY3456789]{5}", t["ma_don"]))
	la("đổi nguồn thành QR tại bàn", nguon, [("Sales Invoice", kq["hoa_don"], "custom_nguon", "QR tại bàn")])
	la("không có module giới thiệu thì vẫn nhận", kho2.dong[r["ma"]]["trang_thai"], "Đã nhận")
	la("nhận lại lần hai: chặn", _bat_loi(lambda: _qua(kho2, lambda: g.nhan(r["ma"]))), True)


def _bat_loi(f):
	try:
		f()
		return False
	except _fr.ValidationError:
		return True


def _qua(kho, f):
	with _quay(kho):
		return f()


@ca("Codex PR #541: quầy NHẬN đơn rồi bánh vẫn giữ cho bàn đó tới khi phiếu tạm tính chốt; chốt rồi thì thôi giữ, không trừ hai lần")
def _giu_sau_nhan():
	kho = Kho()
	with _he(kho):
		# Đúng chuỗi Codex: tủ có 2 bánh, bàn 5 gọi hết 2.
		r = _gui(ban=5, mon=[{"ma": "BAWC00115", "sl": 2}])
		la("bàn 5 gọi 2 bánh", r["ok"], 1)
	with _quay(kho) as (tao, si), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho.set_value(dt, *a, **k) if dt == g.DT else None):
		kq = g.nhan(r["ma"])
	# tao_don_tay giả không ghi bảng: phiếu tạm tính vừa lập là nháp, còn mở.
	kho.phieu[kq["hoa_don"]] = {"name": kq["hoa_don"], "docstatus": 0, "vgb_tam_tinh": 1, "vgb_huy": 0}
	with _he(kho):
		r2 = _gui(nonce="H" * 32, ban=9, mon=[{"ma": "BAWC00115", "sl": 1}])
		dung("đã nhận, phiếu chưa chốt: bàn 9 không gọi được bánh đó", r2["ok"] == 0 and "vừa hết" in r2["cau"])
		la("bảng món: còn 0", g.bang_mon(g._diem("TCV"))["BAWC00115"]["con"], 0)
	# Thu ngân chốt phiếu (thành bill bán): bảng kiểm kho tính 2 cái đã bán, máy thôi giữ.
	kho.phieu[kq["hoa_don"]]["vgb_tam_tinh"] = 0
	ban_roi = [dict(x, con=0) for x in BANH]
	with _he(kho), patch.object(kiem_kho, "banh_tren_quay", side_effect=lambda ma, ngay=None: [dict(x) for x in ban_roi]):
		la("chốt rồi: không trừ hai lần (0, không phải -2)", g.bang_mon(g._diem("TCV"))["BAWC00115"]["con"], 0)
	kho.phieu[kq["hoa_don"]].update(vgb_tam_tinh=1, vgb_huy=1)
	with _he(kho):
		la("phiếu tạm tính bị huỷ: thả bánh", g.bang_mon(g._diem("TCV"))["BAWC00115"]["con"], 2)
	la("phép thuần: đơn nhận hôm trước không giữ", g.mon_dang_giu([], [{"mon": "[]", "hoa_don": "A", "nhan_luc": "2026-11-03 21:00:00"}],
		{"A"}, BAY.date()), [])
	la("phép thuần: đơn nhận hôm nay, phiếu mở thì giữ", g.mon_dang_giu(["x"], [{"mon": "y", "hoa_don": "A", "nhan_luc": BAY},
		{"mon": "z", "hoa_don": "B", "nhan_luc": BAY}], {"A"}, BAY.date()), ["x", "y"])


@ca("v638 hai thu ngân bấm Nhận cùng lúc: khoá hàng, chỉ MỘT phiếu được lập, lượt sau báo đã nhận")
def _hai_thu_ngan():
	kho = Kho()
	with _he(kho):
		r = _gui()
	cho = threading.Barrier(2)
	kq, loi = [], []
	with _quay(kho) as (tao, si):
		cu = BH.tao_don_tay

		def cham(**kw):
			# Giữ lượt đầu lâu trong lúc lập phiếu để lượt sau chắc chắn đã tới.
			import time
			time.sleep(0.15)
			return cu(**kw)
		with patch.object(BH, "tao_don_tay", side_effect=cham):
			def chay():
				cho.wait()
				try:
					kq.append(g.nhan(r["ma"]))
				except _fr.ValidationError as e:
					loi.append(str(e))
				finally:
					kho.nha()
			ts = [threading.Thread(target=chay) for _ in range(2)]
			[x.start() for x in ts]
			[x.join(5) for x in ts]
	la("một lượt nhận được, một lượt bị chặn", (len(kq), len(loi)), (1, 1))
	la("chỉ một phiếu tạm tính", len(tao), 1)
	dung("câu báo đã có người nhận", loi and "đã được nhận" in loi[0])


@ca("Codex PR #541 vòng 3: hai đơn KHÁC nhau của cùng một bàn được hai thu ngân nhận cùng lúc, bàn chưa có phiếu: chỉ MỘT phiếu tạm tính, đơn sau thêm vào phiếu đó; khoá theo bàn luôn nhả")
def _hai_don_mot_ban():
	kho = Kho()
	with _he(kho):
		r1 = _gui(nonce="S" * 32, ban=5)
		r2 = _gui(nonce="T" * 32, ban=5, mon=[{"ma": "BAWC00115", "sl": 1}])
	cho = threading.Barrier(2)
	kq, loi = [], []
	with _quay(kho) as (tao, si):
		def tim(diem, ban, ngay):
			# Đúng chuỗi Codex: hai luồng dừng ở bước tìm phiếu. Có khoá theo bàn thì
			# luồng sau chưa tới được đây, rào hết giờ; nó tìm lại sau khi luồng trước lập xong.
			try:
				cho.wait(timeout=1.5)
			except threading.BrokenBarrierError:
				pass
			return tao and "ACC-SINV-NEW%d" % len(tao) or ""
		with patch.object(g, "_phieu_tam_cua_ban", side_effect=tim), \
				patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho.set_value(dt, *a, **k) if dt == g.DT else None):
			def chay(ma):
				try:
					kq.append(g.nhan(ma))
				except _fr.ValidationError as e:
					loi.append(str(e))
				finally:
					kho.nha()
			ts = [threading.Thread(target=chay, args=(m,)) for m in (r1["ma"], r2["ma"])]
			[x.start() for x in ts]
			[x.join(20) for x in ts]
	la("hai đơn đều nhận được", (len(kq), loi), (2, []))
	la("chỉ một phiếu tạm tính được lập", len(tao), 1)
	la("hai đơn trỏ cùng một phiếu", {kho.dong[r1["ma"]]["hoa_don"], kho.dong[r2["ma"]]["hoa_don"]}, {"ACC-SINV-NEW1"})
	la("một lần thêm vào phiếu có sẵn", sorted(x["them_vao"] for x in kq), [0, 1])
	lay = [x for x in kho.goi_khoa if x[0] == "lay" and x[1].startswith("vgb_phieu_ban:")]
	nha = [x for x in kho.goi_khoa if x[0] == "nha" and x[1].startswith("vgb_phieu_ban:")]
	la("khoá đúng tên theo bàn, lấy bao nhiêu nhả bấy nhiêu", ({x[1] for x in lay}, len(lay), len(nha)), ({"vgb_phieu_ban:TCV:5"}, 2, 2))
	dung("khoá không còn bị giữ", not any(k.locked() for k in kho.khoa_ten.values()))


@ca("v638 từ chối: bắt lý do, không lập phiếu; khách thấy Từ chối kèm lý do; token sai không đọc được gì")
def _tu_choi():
	kho = Kho()
	with _he(kho):
		r = _gui()
	with _quay(kho) as (tao, si), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho.set_value(dt, *a, **k)):
		la("thiếu lý do", _bat_loi(lambda: g.tu_choi(r["ma"], "")), True)
		g.tu_choi(r["ma"], "Hết món")
		la("không lập phiếu", (tao, si), ([], {}))
		la("nhận sau khi từ chối: chặn", _bat_loi(lambda: g.nhan(r["ma"])), True)
	with _he(kho):
		tt = g.trang_thai(r["ma"], r["token"])
		la("khách thấy", (tt["ok"], tt["trang_thai"], tt["ly_do"]), (1, "Từ chối", "Hết món"))
		la("token sai", g.trang_thai(r["ma"], "0" * 32), {"ok": 0})
		la("token sai dạng", g.trang_thai(r["ma"], "<x>"), {"ok": 0})
		dung("không lộ số điện thoại, tên khách, mã hoá đơn", not ({"sdt_gioi_thieu", "ten_goi", "hoa_don", "token_bam"} & set(tt)))


@ca("v638 hết hạn sau 10 phút: khách thấy Hết hạn ngay, quầy không còn thấy, nhận thì báo hết hạn; lịch 5 phút ghi sổ trạng thái")
def _het_han():
	kho = Kho()
	gio = [BAY]
	with _he(kho, bay=gio):
		r = _gui()
		r2 = _gui(nonce="Q" * 32, ban=6)
		gio[0] = BAY + datetime.timedelta(minutes=9, seconds=59)
		la("9 phút 59 giây vẫn chờ", g.trang_thai(r["ma"], r["token"])["trang_thai"], "Chờ nhận")
		with patch.object(BH, "_kiem_quyen_ban"):
			la("quầy thấy 2 đơn", g.dem_cho("TCV")["so"], 2)
		gio[0] = BAY + datetime.timedelta(minutes=10)
		la("đủ 10 phút: khách thấy Hết hạn", g.trang_thai(r["ma"], r["token"])["trang_thai"], "Hết hạn")
		with patch.object(BH, "_kiem_quyen_ban"):
			la("quầy không còn thấy", g.dem_cho("TCV")["so"], 0)
		la("lịch 5 phút chuyển cả hai", g.quet_het_han(), 2)
		la("sổ ghi Hết hạn", sorted(x["trang_thai"] for x in kho.dong.values()), ["Hết hạn", "Hết hạn"])
		la("không còn chờ thì tin Zalo bỏ", g.con_cho_nhan(r2["ma"]), False)
	kho2 = Kho()
	gio2 = [BAY]
	with _he(kho2, bay=gio2):
		r = _gui()
	gio2[0] = BAY + datetime.timedelta(minutes=11)
	with _quay(kho2) as (tao, si), patch.object(g, "now_datetime", return_value=gio2[0]), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho2.set_value(dt, *a, **k)):
		la("nhận đơn quá hạn: chặn", _bat_loi(lambda: g.nhan(r["ma"])), True)
		la("không lập phiếu", tao, [])
	la("bản ghi chuyển Hết hạn", kho2.dong[r["ma"]]["trang_thai"], "Hết hạn")


@ca("Codex PR #541 vòng 4: lịch hết hạn đọc thấy đơn còn Chờ nhận, đúng lúc đó thu ngân nhận xong: bản ghi giữ Đã nhận và phiếu, khách không thấy Hết hạn, bánh vẫn được giữ")
def _het_han_dua_nhan():
	kho = Kho()
	with _he(kho):
		r = _gui(mon=[{"ma": "BAWC00115", "sl": 2}])
	goc = kho.get_all

	def doc_roi_nhan(dt, filters=None, **k):
		ra = goc(dt, filters=filters, **k)
		if (filters or {}).get("trang_thai") == g.TT_CHO and "luc" in (filters or {}):
			# Đúng chuỗi Codex: nhan() commit Đã nhận ngay sau khi lịch đọc danh sách.
			kho.dong[r["ma"]].update(trang_thai=g.TT_NHAN, hoa_don="SI-1", nhan_luc=BAY)
		return ra
	with _he(kho, bay=BAY + datetime.timedelta(minutes=10, seconds=5)), patch.object(_fr, "get_all", side_effect=doc_roi_nhan):
		g.quet_het_han()
	la("vẫn Đã nhận, vẫn trỏ phiếu", (kho.dong[r["ma"]]["trang_thai"], kho.dong[r["ma"]]["hoa_don"]), (g.TT_NHAN, "SI-1"))
	kho.phieu["SI-1"] = {"name": "SI-1", "docstatus": 0, "vgb_tam_tinh": 1, "vgb_huy": 0}
	with _he(kho, bay=BAY + datetime.timedelta(minutes=10, seconds=5)):
		la("khách thấy Đã nhận", g.trang_thai(r["ma"], r["token"])["trang_thai"], g.TT_NHAN)
		la("bánh vẫn được giữ cho bàn", g.bang_mon(g._diem("TCV"))["BAWC00115"]["con"], 0)
	# Đơn vẫn chờ thật thì lịch vẫn chuyển Hết hạn.
	kho2 = Kho()
	with _he(kho2):
		r2 = _gui()
	with _he(kho2, bay=BAY + datetime.timedelta(minutes=11)):
		g.quet_het_han()
	la("đơn còn chờ thật: Hết hạn", kho2.dong[r2["ma"]]["trang_thai"], g.TT_HET_HAN)


@ca("v638 thẻ quầy: bàn, số món, tạm tính, phút chờ, món kèm đá đường, ghi chú, tên gọi, người giới thiệu")
def _the():
	r = {"name": "TQ-1", "ban": 5, "diem": "TCV", "tam_tinh": 90000, "luc": "2026-11-04 09:53:00", "ghi_chu": "ít ngọt",
		"ten_goi": "Lan", "ten_gioi_thieu": "Chị Dễ", "mon": json.dumps([{"ma": "NUTR00021", "ten": "Trà", "sl": 2, "tc": ["Ít đá"], "gia": 45000}])}
	t = g.the_quay(r, BAY, "District 1")
	la("thẻ", (t["ban"], t["so_mon"], t["tam_tinh"], t["phut"], t["mon"][0]["tc"], t["ghi_chu"], t["ten_goi"], t["gioi_thieu"]),
		("5", 2, 90000, 7, ["Ít đá"], "ít ngọt", "Lan", "Chị Dễ"))
	la("chưa có ảnh: rỗng (màn vẽ ô 🍰)", t["mon"][0]["anh"], "")
	la("có ảnh danh mục: mang theo", g.the_quay(r, BAY, "District 1", {"NUTR00021": "/files/tra.jpg"})["mon"][0]["anh"], "/files/tra.jpg")
	# Codex PR #541 vòng 2: đường thật dem_cho đọc ảnh danh mục (một câu cho mọi món) và đưa lên thẻ.
	kho = Kho()
	with _he(kho):
		_gui()
		doc_item = []
		goc = _fr.get_all

		def get_all(dt, *a, **k):
			if dt == "Item":
				doc_item.append(k.get("filters"))
				return [{"name": "NUTR00021", "image": "/files/tra.jpg"}]
			return goc(dt, *a, **k)
		with patch.object(BH, "_kiem_quyen_ban"), patch.object(_fr, "get_all", side_effect=get_all):
			ds = g.dem_cho("TCV")["ds"]
	la("dem_cho: ảnh món trên thẻ", [(x["ma"], x["anh"]) for x in ds[0]["mon"]], [("NUTR00021", "/files/tra.jpg")])
	la("một câu đọc ảnh cho mọi món", doc_item, [{"name": ["in", ["NUTR00021"]]}])


@ca("v638 giờ mở cửa: đọc thẻ Cửa hàng của điểm (cùng nguồn Đặt bàn); chưa điền thì 7:00 - 22:00")
def _gio_mo():
	from vagabond import noi_dung_web

	d = {"ten": "The Vagabond District 1", "dia_chi": "9 Trần Cao Vân, Quận 1"}
	ch = [{"ten": "Cửa hàng Sài Gòn", "dia_chi": "9 Trần Cao Vân, P. Sài Gòn", "gio_mo_cua": "Thứ 2 - Chủ nhật: 8:00 - 21:00"}]
	with patch.object(noi_dung_web, "_ban_cong_khai", return_value={}), \
			patch.object(noi_dung_web, "thong_tin_day_du", return_value={"cua_hang": ch}):
		la("21:30 đã đóng theo thẻ", g._gio_mo_cua(d, datetime.datetime(2026, 11, 4, 21, 30))["dang_mo"], False)
		la("8:30 mở", g._gio_mo_cua(d, datetime.datetime(2026, 11, 4, 8, 30))["dang_mo"], True)
	with patch.object(noi_dung_web, "_ban_cong_khai", side_effect=Exception("hong")):
		la("đọc hỏng: 21:30 vẫn mở theo khung mặc định", g._gio_mo_cua(d, datetime.datetime(2026, 11, 4, 21, 30))["dang_mo"], True)
		la("23:00 đóng", g._gio_mo_cua(d, datetime.datetime(2026, 11, 4, 23, 0))["dang_mo"], False)


@ca("v638 một chỗ dựng dòng hoá đơn: tao_don_tay, pos_sua_don, nhận đơn tại bàn đều qua ban_hang._dung_dong_mon; mô tả giữ đúng định dạng cũ")
def _mot_cho():
	cay = ast.parse((GOC / "vagabond/ban_hang.py").read_text())
	ham = {n.name: n for n in cay.body if isinstance(n, ast.FunctionDef)}
	for ten in ("tao_don_tay", "pos_sua_don"):
		goi = [n for n in ast.walk(ham[ten]) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_dung_dong_mon"]
		la(ten + " gọi _dung_dong_mon", len(goi), 1)
		ten_dau = [n for n in ast.walk(ham[ten]) if isinstance(n, ast.Name) and n.id in ("DAU_GC_MON", "DAU_COMBO")]
		la(ten + " không tự dựng mô tả", len(ten_dau), 0)
	la("định dạng", BH.mo_ta_dong("Trà", "CB1 - Combo", "Ít đá", "mang ra trước"),
		"Trà\n%s CB1 - Combo\n[Ít đá]\n%s mang ra trước" % (BH.DAU_COMBO, BH.DAU_GC_MON))
	la("không gì thêm thì không mô tả", BH.mo_ta_dong("Trà"), "")
	with patch.object(_fr.db, "get_value", return_value="Trà Hoa Lài"):
		la("dòng", BH._dung_dong_mon({"item_code": "NUTR00021", "qty": 2, "rate": 45000, "tuy_chon": "Ít đá"}),
			{"item_code": "NUTR00021", "qty": 2.0, "rate": 45000.0, "description": "Trà Hoa Lài\n[Ít đá]"})


@ca("v638 nguồn QR tại bàn: phương thức thu tiền đi đúng như Tại chỗ (máy chủ), không thêm nút nguồn trên màn quầy")
def _nguon():
	ds = [{"v": "Tại chỗ", "pt": ["Tiền mặt", "Chuyển khoản"], "rieng": 0}, {"v": "GrabFood", "pt": ["GrabFood"], "rieng": 1}]
	with patch.object(BH, "_nguon_don", return_value=ds):
		la("như Tại chỗ", BH._pt_cho_nguon(g.NGUON_QR), ["Tiền mặt", "Chuyển khoản"])
	dung("không nằm trong nguồn mặc định của điểm", all(g.NGUON_QR not in d["nguon"] for d in diem_ban.MAC_DINH))
	s = (GOC / "vagabond/public/js/bep/08-doanh-so-sales.js").read_text()
	dung("màn bill đọc pt_quay cho nguồn QR (ca hành vi ở goi_mon_quay_638.js)", "c.pt_quay" in s)


@ca("v638 lịch 5 phút và cửa quyền: quet_het_han nằm trong scheduler; In QR chỉ quản lý cửa hàng, Giám đốc; màn quầy cần quyền bán")
def _lich_quyen():
	s = (GOC / "vagabond/hooks.py").read_text()
	dung("cron 5 phút", '.setdefault("*/5 * * * *", []).append("vagabond.goi_mon_ban.quet_het_han")' in s)
	with patch.object(_fr, "get_roles", return_value=["Sales User"]):
		la("Sales không in QR", _bat_loi(g.diem_in_qr), True)
	with patch.object(_fr, "get_roles", return_value=["VGB - Quản lý cửa hàng"]), patch.object(diem_ban, "cfg_o", return_value=""):
		la("QLCH in được, chỉ điểm có quầy", [d["ma"] for d in g.diem_in_qr()], ["TCV", "NVHTN"])
	js = (GOC / "vagabond/public/js/bep/66-goi-mon-tai-ban.js").read_text()
	m = re.search(r"var QUYEN_GMB_QR = (\[[^\]]*\]);", js)
	la("danh sách quyền JS trùng máy chủ", sorted(json.loads(m.group(1).replace("'", '"'))), sorted(g.QUYEN_IN_QR))
	with patch.object(_fr, "get_roles", return_value=["Stock User"]), _co_bh():
		la("không có quyền bán thì không xem đơn chờ", _bat_loi(lambda: g.dem_cho("TCV")), True)


@ca("v638 tờ QR: mỗi bàn một tờ, link ký đúng bàn, mở ra đúng điểm")
def _to_qr():
	ve = []
	with patch.object(_fr, "get_roles", return_value=["Giám đốc"]), patch.object(g, "_bi_mat", return_value=KHOA), \
			patch.object(diem_ban, "cfg_o", return_value=""), \
			patch("vagabond.qr_chuyen_khoan.anh_lien_ket", side_effect=lambda u: ve.append(u) or "data:image/svg+xml;base64,QR"):
		kq = g.to_qr("NVHTN", 3, 1)
	la("ba tờ", [t["ban"] for t in kq["to"]], ["1", "2", "3"])
	la("tên điểm", kq["to"][0]["ten_diem"], "NVHTN")
	for t, u in zip(kq["to"], ve):
		m = re.match(r"https://order\.thevagabondpatisserie\.com/banh\?diem=NVHTN&ban=(\d+)&k=([0-9a-f]{16})#/in-store$", u)
		dung("link tuyệt đối miền khách " + u, m)
		dung("khoá đúng bàn", m and m.group(1) == t["ban"] and g.dung_khoa(KHOA, "NVHTN", t["ban"], m.group(2)))


@ca("v638 doctype mới: đủ trường, trạng thái trùng hằng máy chủ, nonce duy nhất, đặt tên TQ-")
def _doctype():
	d = json.loads((GOC / "vagabond/vagabond/doctype/vagabond_goi_mon_ban/vagabond_goi_mon_ban.json").read_text())
	f = {x["fieldname"]: x for x in d["fields"]}
	for k in ("diem", "ban", "mon", "tam_tinh", "ghi_chu", "ten_goi", "sdt_gioi_thieu", "trang_thai", "luc", "hoa_don", "token_bam", "nonce"):
		dung("có trường " + k, k in f)
	la("trạng thái", tuple(f["trang_thai"]["options"].split("\n")), g.TRANG_THAI)
	la("nonce duy nhất", f["nonce"].get("unique"), 1)
	dung("tên TQ-", d["autoname"].startswith("format:TQ-"))


# ============================== v639 vòng 2 (anh Việt duyệt mẫu 05/11/2026) ==============================

KOM = {"item_code": "NUTR00040", "item_name": "Kombucha Chill , Chai 300ml", "image": "", "standard_rate": 100000,
	"item_group": "Trà", "disabled": 0, "is_sales_item": 1, "has_variants": 0, "description": "<p>Lên men <b>tại tiệm</b></p>"}
TOP = [{"item_code": "TPNC00001", "item_name": "Trân châu ô long", "standard_rate": 10000, "item_group": "Topping cho món nước", "disabled": 0, "is_sales_item": 1, "has_variants": 0},
	{"item_code": "TPNC00002", "item_name": "Thay sữa yến mạch", "standard_rate": 20000, "item_group": "Topping cho món nước", "disabled": 0, "is_sales_item": 1, "has_variants": 0},
	{"item_code": "TPBA00001", "item_name": "Nến số", "standard_rate": 5000, "item_group": "Topping cho món bánh", "disabled": 0, "is_sales_item": 1, "has_variants": 0},
	{"item_code": "TPNC00009", "item_name": "Tắt", "standard_rate": 10000, "item_group": "Topping cho món nước", "disabled": 1, "is_sales_item": 1, "has_variants": 0},
	{"item_code": "TPNC00010", "item_name": "Không giá", "standard_rate": 0, "item_group": "Topping cho món nước", "disabled": 0, "is_sales_item": 1, "has_variants": 0}]


@ca("v639 phép thuần: món đóng sẵn theo tên không hỏi đá đường; mô tả HTML thành một dòng; topping đúng nhóm, có giá; đơn giá dòng kể cả topping")
def _thuan_639():
	for ten in ("Kombucha Chill , Chai 300ml", "Trà Earl Grey, Set trà 2 người, Nóng/Hot", "Nước suối lon 330", "Trà hoa cúc, hũ 100g", "Bánh quy, Hộp 12"):
		dung("đóng sẵn: " + ten, g.khong_pha(ten))
	for ten in ("Trà Sữa Lài Kem Phô Mai, Size M, Đá/Iced", "Cà phê sữa", "Chai Latte", "Hồng trà Thanh Trà", "Trà hoa cúc hộp"):
		dung("pha: " + ten, not g.khong_pha(ten))
	la("đóng sẵn thì không lựa chọn dù nhóm Trà có", g.tuy_chon_mon("Kombucha Chill , Chai 300ml", "Trà", TC), [])
	la("pha thì theo nhóm", [n["nhom"] for n in g.tuy_chon_mon("Trà Lài", "Trà", TC)], ["Đá", "Đường"])
	la("mô tả HTML", g.mo_ta_ngan("<p>Trà lài ủ lạnh,<br>lớp kem &amp; phô mai</p><div>uống lạnh</div>"), "Trà lài ủ lạnh, lớp kem & phô mai uống lạnh")
	la("mô tả rỗng", g.mo_ta_ngan(None), "")
	dai = g.mo_ta_ngan("x" * 50 + " " + "y" * 200)
	dung("cắt ở 200 và thêm ...", dai.endswith("...") and len(dai) <= 204)
	la("topping lọc", g.loc_topping(TOP, {"TPNC00002": 25000}), [{"ma": "TPNC00001", "ten": "Trân châu ô long", "gia": 10000}, {"ma": "TPNC00002", "ten": "Thay sữa yến mạch", "gia": 25000}])
	d = {"ma": "NUTR00021", "ten": "Trà", "sl": 2, "gia": 45000, "tc": ["Ít đá"], "tp": [{"ma": "TPNC00001", "ten": "Trân châu ô long", "gia": 10000}]}
	la("lựa chọn kèm topping để hiện", g.tc_hien(d), ["Ít đá", "+ Trân châu ô long"])
	la("đơn giá dòng", g.gia_dong(d), 55000)
	la("tạm tính", g.tinh_tam([d]), 110000)
	la("dòng hoá đơn: ly rồi topping theo ly, mô tả Kèm", g.dong_hoa_don([d]),
		[{"item_code": "NUTR00021", "qty": 2, "rate": 45000.0, "tuy_chon": "Ít đá, + Trân châu ô long"},
			{"item_code": "TPNC00001", "qty": 2, "rate": 10000.0, "tuy_chon": "Kèm Trà"}])
	la("lý do chuông", [g.chuan_ly_do(x) for x in ("Xin tính tiền", " Xin tính tiền ", "xin tiền", "", None)], ["Xin tính tiền", "Xin tính tiền", "", "", ""])


def _bang2():
	b = _bang()
	b["NUTR00040"] = {"ten": "Kombucha Chill , Chai 300ml", "gia": 100000, "loai": "nuoc", "nhom_goc": "Trà", "tc": [], "khong_pha": 1}
	for t in g.loc_topping(TOP, {}):
		b[t["ma"]] = {"ten": t["ten"], "gia": t["gia"], "loai": "topping", "nhom_goc": g.NHOM_TOPPING}
	return b


@ca("v639 giỏ có topping: giá máy chủ, cùng ly cùng topping gộp, khác topping tách dòng, bỏ trùng; topping gọi riêng, topping cho bánh, cho chai, topping lạ, quá 5 đều chặn")
def _gio_topping():
	dong, tam = g.chuan_gio([
		{"ma": "NUTR00021", "sl": 1, "tc": {"Đá": "Ít đá"}, "tp": ["TPNC00001", "TPNC00001"]},
		{"ma": "NUTR00021", "sl": 2, "tc": {"Đá": "Ít đá"}, "tp": [{"ma": "TPNC00001", "gia": 1}]},
		{"ma": "NUTR00021", "sl": 1, "tc": {"Đá": "Ít đá"}},
		{"ma": "NUTR00040", "sl": 1}], _bang2())
	la("dòng", [(d["ma"], d["sl"], d["tc"], [t["ma"] for t in d["tp"]], g.gia_dong(d)) for d in dong],
		[("NUTR00021", 3, ["Ít đá"], ["TPNC00001"], 55000), ("NUTR00021", 1, ["Ít đá"], [], 45000), ("NUTR00040", 1, [], [], 100000)])
	la("giá topping máy chủ, không theo 1 đồng", dong[0]["tp"], [{"ma": "TPNC00001", "ten": "Trân châu ô long", "gia": 10000}])
	la("tạm tính", tam, 3 * 55000 + 45000 + 100000)
	for gio, cau in (
		([{"ma": "TPNC00001", "sl": 1}], "chọn kèm một ly nước"),
		([{"ma": "BAWC00115", "sl": 1, "tp": ["TPNC00001"]}], "không thêm topping"),
		([{"ma": "NUTR00040", "sl": 1, "tp": ["TPNC00001"]}], "không thêm topping"),
		([{"ma": "NUTR00021", "sl": 1, "tp": ["TPBA00001"]}], "ngừng bán"),
		([{"ma": "NUTR00021", "sl": 1, "tp": ["TPNC00009"]}], "ngừng bán"),
		([{"ma": "NUTR00021", "sl": 1, "tp": "TPNC00001"}], "không đọc được"),
		([{"ma": "NUTR00021", "sl": 1, "tp": ["a", "b", "c", "d", "e", "f"]}], "ngừng bán")):
		try:
			g.chuan_gio(gio, _bang2())
			la("phải chặn %r" % (gio,), "không chặn", cau)
		except ValueError as e:
			dung("câu chặn %r có '%s' (được: %s)" % (gio, cau, e), cau in str(e))
	b = _bang2()
	for i in range(6):
		b["TP%d" % i] = {"ten": "T%d" % i, "gia": 1000, "loai": "topping"}
	try:
		g.chuan_gio([{"ma": "NUTR00021", "sl": 1, "tp": ["TP%d" % i for i in range(6)]}], b)
		dung("quá 5 topping phải chặn", False)
	except ValueError as e:
		dung("câu tối đa 5", "tối đa 5" in str(e))


@ca("v639 bảng món và tab Tại quầy: topping của điểm vào bảng (loai topping) và vào khoá topping của quầy; đồ uống có nhom_goc, mo_ta, khong_pha; chai không có lựa chọn")
def _feed_639():
	diem = [dict(ma="TCV", ten="The Vagabond District 1", ten_ngan="District 1", dia_chi="9 TCV", quay="TCV")]
	nuoc = g.loc_do_uong([TRA, KOM], {}, {})
	for x in nuoc:
		x["mo_ta"] = g.mo_ta_ngan(KOM["description"]) if x["ma"] == "NUTR00040" else ""
		x["khong_pha"] = 1 if g.khong_pha(x["ten"]) else 0
	lib = sys.modules.get("vagabond.lib")
	with patch.object(kiem_kho, "_diem_co_quay", return_value=diem), \
			patch.object(kiem_kho, "banh_tren_quay", side_effect=lambda ma, ngay=None: [dict(x, mo_ta="Chanh dây Đà Lạt") for x in BANH]), \
			patch.object(g, "do_uong_cua_diem", side_effect=lambda ma, ngay=None: nuoc), \
			patch.object(g, "topping_cua_diem", side_effect=lambda ma: g.loc_topping(TOP, {})), \
			patch.object(g, "doc_tuy_chon", return_value=TC), \
			patch.object(diem_ban, "gia_rieng", return_value={}), \
			patch.object(lib, "cfg", return_value=_fr._dict(pancake_shop_id="")), patch.object(lib, "key", return_value=""):
		ra = kiem_kho.con_tren_quay_web()
		bm = g.bang_mon(diem[0])
	q = ra["quay"][0]
	la("bánh có mô tả", q["mon"][0]["mo_ta"], "Chanh dây Đà Lạt")
	la("đồ uống: nhóm gốc, mô tả, đóng sẵn", [(m["ma"], m["nhom_goc"], m["mo_ta"], m["khong_pha"], [n["nhom"] for n in m["tc"]]) for m in q["do_uong"]],
		[("NUTR00040", "Trà", "Lên men tại tiệm", 1, []), ("NUTR00021", "Trà", "", 0, ["Đá", "Đường"])])
	la("topping của quầy", [t["ma"] for t in q["topping"]], ["TPNC00001", "TPNC00002"])
	la("bảng món có topping loai topping, chai không lựa chọn", [(k, v["loai"]) for k, v in bm.items() if k.startswith("TP")] + [bm["NUTR00040"]["tc"], bm["NUTR00040"]["khong_pha"]],
		[("TPNC00001", "topping"), ("TPNC00002", "topping"), [], 1])


@ca("v639 gọi món có topping rồi quầy nhận: đơn lưu topping; phiếu tạm tính có dòng topping theo ly ghi Kèm; phiếu pha chế ghi + topping; tạm tính đủ")
def _nhan_topping():
	kho = Kho()
	with _he(kho), patch.object(g, "topping_cua_diem", side_effect=lambda ma: g.loc_topping(TOP, {})):
		r = _gui(mon=[{"ma": "NUTR00021", "sl": 2, "tc": {"Đá": "Ít đá"}, "tp": ["TPNC00002"]}])
	la("ghi", r["ok"], 1)
	d = kho.dong[r["ma"]]
	la("tạm tính kể cả topping", d["tam_tinh"], 2 * (45000 + 20000))
	la("đơn lưu topping", json.loads(d["mon"])[0]["tp"], [{"ma": "TPNC00002", "ten": "Thay sữa yến mạch", "gia": 20000}])
	with _quay(kho, phieu_co="ACC-SINV-CO") as (tao, si), \
			patch.object(_fr.db, "set_value", side_effect=lambda dt, *a, **k: kho.set_value(dt, *a, **k) if dt == g.DT else None):
		kq = g.nhan(r["ma"])
	dong = si["ACC-SINV-CO"]["items"]
	la("phiếu: ly rồi topping theo ly", [(x["item_code"], x["qty"], x["rate"]) for x in dong[1:]], [("NUTR00021", 2.0, 45000.0), ("TPNC00002", 2.0, 20000.0)])
	la("mô tả ly ghi topping", dong[1]["description"], "Trà Hoa Lài\n[Ít đá, + Thay sữa yến mạch]")
	la("phiếu pha chế ghi + topping", kq["phieu"]["mon"][0]["tc"], ["Ít đá", "+ Thay sữa yến mạch"])
	with _he(kho):
		the = g.the_quay(kho.dong[r["ma"]], BAY, "District 1")
	la("thẻ quầy: lựa chọn kèm topping, giá dòng kể cả topping", (the["mon"][0]["tc"], the["mon"][0]["gia"]), (["Ít đá", "+ Thay sữa yến mạch"], 65000))


def _chuong(nonce="C" * 32, ban=5, ly_do="Xin tính tiền", **kw):
	return g.goi_nhan_vien(diem="TCV", ban=ban, k=kw.pop("k", _k(ban)), ly_do=ly_do, nonce=nonce, **kw)


@ca("v639 chuông gọi nhân viên: k sai, ngoài giờ, lý do lạ không ghi; ghi một lời kèm tin Zalo nhóm quầy (không tiền, có kiểm lại); cùng nonce không ghi thêm; bàn gọi 3 lần trong 10 phút thì chặn")
def _goi_nhan_vien():
	kho = Kho()
	with _he(kho, mo=False):
		la("ngoài giờ", (_chuong()["ok"], len(kho.tg)), (0, 0))
	with _he(kho) as tin:
		la("k sai", (_chuong(k="0" * 16)["ok"], len(kho.tg)), (0, 0))
		r = _chuong(ly_do="xin tiền")
		dung("lý do lạ", r["ok"] == 0 and "chọn một lý do" in r["cau"] and not kho.tg)
		r = _chuong(chi_tiet=" xin thêm ghế em bé " + "x" * 200)
		la("ghi một lời", (r["ok"], len(kho.tg), r["luc"]), (1, 1, "10:00"))
		d = kho.tg[r["ma"]]
		la("bản ghi", (d["diem"], d["ban"], d["ly_do"], d["trang_thai"], len(d["chi_tiet"])), ("TCV", "5", "Xin tính tiền", "Chờ xử lý", 120))
		la("tin Zalo đúng mã", [k["ma_tin"] for a, k in tin], ["bh_khach_can_tro_giup"])
		a, k = tin[0]
		dung("tin nêu bàn, điểm, lý do, chữ khách, link app", "Bàn 5" in a[2] and "District 1" in a[2] and "Xin tính tiền" in a[2]
			and any("xin thêm ghế em bé" in x for x in a[3]) and "https://app.vagabond.test/ban-tai-quay" in a[3][-1])
		dung("không số tiền", not any(kenh_zalo.MAU_TIEN.search(x) for x in [a[2]] + list(a[3])))
		la("hỏi lại trước khi gửi", (k["kiem"], kenh_zalo.DIEU_KIEN["tro_giup_cho"], k["khoa"]), ("tro_giup_cho", "vagabond.goi_mon_ban.con_tro_giup", "tro-giup:" + r["ma"]))
		dung("còn chờ", g.con_tro_giup(r["ma"]))
		r2 = _chuong()
		la("cùng nonce: cùng lời, không thêm", (r2["ma"], r2.get("lap_lai"), len(kho.tg)), (r["ma"], 1, 1))
		_chuong(nonce="D" * 32, ly_do="Việc khác")
		_chuong(nonce="E" * 32, ly_do="Xin thêm nước lọc, đá")
		r = _chuong(nonce="F" * 32)
		dung("lần thứ tư trong 10 phút chặn", r["ok"] == 0 and "vừa gọi 3 lần" in r["cau"])
		la("vẫn 3 lời, bàn khác vẫn gọi được", (len(kho.tg), _chuong(nonce="G" * 32, ban=7)["ok"]), (3, 1))
		la("tin Zalo mỗi lời một tin", len(tin), 4)


@ca("Codex PR #542 vòng 1: hai khách cùng bàn bấm chuông cùng lúc (nonce khác), cùng đếm 2 lời đã có rồi cùng qua: phải khoá theo bàn, chỉ MỘT lời được ghi, khoá luôn nhả")
def _chuong_dua():
	kho = Kho()
	with _he(kho):
		_chuong(nonce="C" * 32)
		_chuong(nonce="D" * 32, ly_do="Việc khác")
	kho.goi_khoa.clear()
	cho = threading.Barrier(2)
	goc = kho.get_all

	def dem_roi_doi(dt, filters=None, **k):
		r = goc(dt, filters=filters, **k)
		if dt == g.DT_TG and filters and "luc" in filters:
			try:
				cho.wait(timeout=1.5)
			except threading.BrokenBarrierError:
				pass
		return r
	kq = {}
	with _he(kho), patch.object(_fr, "get_all", side_effect=dem_roi_doi):
		def chay(nonce):
			kq[nonce] = _chuong(nonce=nonce, ly_do="Xin thêm nước lọc, đá")
		ts = [threading.Thread(target=chay, args=("E" * 32,)), threading.Thread(target=chay, args=("F" * 32,))]
		for x in ts:
			x.start()
		for x in ts:
			x.join(20)
	ok = [n for n, r in kq.items() if r.get("ok")]
	la("đúng một lời qua, bàn vẫn 3 lời", (len(ok), len(kho.tg)), (1, 3))
	thua = [r for r in kq.values() if not r.get("ok")]
	dung("lời kia nghe câu vừa gọi 3 lần", len(thua) == 1 and "vừa gọi 3 lần" in thua[0]["cau"])
	lay = [x for x in kho.goi_khoa if x[0] == "lay" and x[1].startswith("vgb_chuong")]
	nha = [x for x in kho.goi_khoa if x[0] == "nha" and x[1].startswith("vgb_chuong")]
	la("khoá theo bàn, lấy bao nhiêu nhả bấy nhiêu", ({x[1] for x in lay}, len(lay), len(nha)), ({"vgb_chuong:TCV:5"}, 2, 2))
	dung("khoá không còn bị giữ", not any(k.locked() for k in kho.khoa_ten.values()))


@ca("v639 màn quầy nhận lời gọi: dem_cho trả tro_giup (xin tính tiền kèm bill của bàn, lời quá 30 phút ẩn); Đã tới bàn chuyển Đã xong, ghi người bấm; lịch 5 phút chuyển Hết hạn lời quá 30 phút")
def _tro_giup_quay():
	kho = Kho()
	with _he(kho):
		r1 = _chuong(nonce="C" * 32, ly_do="Xin tính tiền")
		r2 = _chuong(nonce="D" * 32, ban=9, ly_do="Việc khác", chi_tiet="xin ghế em bé")
	kho.tg[r2["ma"]]["luc"] = BAY - datetime.timedelta(minutes=31)
	with _he(kho), patch.object(BH, "_kiem_quyen_ban"), patch.object(g, "_phieu_tam_cua_ban", side_effect=lambda diem, ban, ngay: "ACC-SINV-CO" if ban == "5" else ""), \
			patch.object(_fr.db, "get_value", side_effect=lambda dt, ten, f=None, **k: kho.get_value(dt, ten, f, **k) if dt in (g.DT, g.DT_TG)
				else (_fr._dict(custom_pancake_display_id="TCVABCDE", grand_total=335000.0) if dt == "Sales Invoice" else None)):
		kq = g.dem_cho("TCV")
		la("một lời còn hạn, kèm bill", [(x["ma"], x["ban"], x["ly_do"], x["bill"], x["tam_tinh"], x["hoa_don"], x["phut"]) for x in kq["tro_giup"]],
			[(r1["ma"], "5", "Xin tính tiền", "TCVABCDE", 335000, "ACC-SINV-CO", 0)])
		_fr.session.user = "thu.ngan@vagabond.test"
		la("đã tới bàn", g.xong_tro_giup(r1["ma"]), {"ok": 1, "ban": "5"})
		la("bản ghi", (kho.tg[r1["ma"]]["trang_thai"], kho.tg[r1["ma"]]["xong_boi"]), ("Đã xong", "thu.ngan@vagabond.test"))
		la("bấm lần hai", g.xong_tro_giup(r1["ma"]), {"ok": 1, "da_xong": 1})
		dung("tin Zalo hỏi lại: không còn chờ", not g.con_tro_giup(r1["ma"]) and not g.con_tro_giup(r2["ma"]))
		la("không còn lời nào trên màn", g.dem_cho("TCV")["tro_giup"], [])
		g.quet_het_han()
		la("lời quá 30 phút Hết hạn, lời đã xong giữ nguyên", (kho.tg[r2["ma"]]["trang_thai"], kho.tg[r1["ma"]]["trang_thai"]), ("Hết hạn", "Đã xong"))


@ca("v639 doctype lời gọi nhân viên: đủ trường, trạng thái trùng hằng máy chủ, nonce duy nhất, đặt tên GNV-; cửa mới có trong sổ cửa ngõ; tin Zalo có trong danh mục")
def _doctype_tg():
	d = json.loads((GOC / "vagabond/vagabond/doctype/vagabond_goi_nhan_vien/vagabond_goi_nhan_vien.json").read_text())
	f = {x["fieldname"]: x for x in d["fields"]}
	for k in ("diem", "ban", "ly_do", "chi_tiet", "trang_thai", "luc", "xong_luc", "xong_boi", "nonce"):
		dung("có trường " + k, k in f)
	la("trạng thái", tuple(f["trang_thai"]["options"].split("\n")), g.TRANG_THAI_TG)
	la("nonce duy nhất", f["nonce"].get("unique"), 1)
	dung("tên GNV-", d["autoname"].startswith("format:GNV-"))
	la("tên doctype", d["name"], g.DT_TG)
	dung("tin Zalo trong danh mục", "bh_khach_can_tro_giup" in kenh_zalo.TIN and kenh_zalo.TIN["bh_khach_can_tro_giup"][0] == "Bán hàng, cửa hàng")
	s = (GOC / "vagabond/khung/kiem_thu/thu_cua_ngo.py").read_text()
	dung("sổ cửa ngõ có hai cửa mới", '"goi_nhan_vien"' in s and '"xong_tro_giup"' in s)
	js = (GOC / "vagabond/public/web_vue/banh/kho-goi-ban.js").read_text()
	for ly in g.LY_DO_GOI:
		dung("trang khách có đúng câu lý do: " + ly, "'" + ly + "'" in js)


def _node(tep, so_toi_thieu):
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/" + tep], cwd=GOC, capture_output=True, text=True, timeout=90)
	la(tep + "\n" + r.stdout[-2500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung(tep + " đủ số ca", m and int(m.group(1)) >= so_toi_thieu)


@ca("v638 trang khách Vue (node, Vue thật): link có k hiện chế độ gọi món, thêm món, chọn đá đường, giỏ, gọi món gửi đúng dữ liệu, xem trạng thái")
def _vue():
	_node("goi_mon_ban_638.mjs", 14)


@ca("v638 màn quầy và màn In QR (node, mã nguồn thật): dải chờ hiện khi có đơn, nhận đơn gọi đúng cửa và in phiếu, từ chối bắt lý do, in đủ tờ")
def _quay_js():
	# v647: ca In QR cũ chuyển sang hanh_vi/qr_ban_khu_647.js (thu_qr_ban_khu_647), còn 8 ca.
	_node("goi_mon_quay_638.js", 8)


@ca("v638 bảng kiểm kho (node, trang thật): mục Đồ uống đủ món, công tắc Bán trên web gọi đúng cửa, ngày cũ không bấm được")
def _kiem_kho_js():
	_node("kiem_kho_nuoc_638.js", 3)


@ca("v642 đơn của bàn: trang khách nhận giờ gọi từng lượt, đơn giá và tiền từng dòng (kể cả topping) do máy chủ chốt; không lộ tên gọi, số điện thoại")
def _cho_khach_642():
	r = {"name": "TQ-7", "ban": 1, "trang_thai": g.TT_NHAN, "luc": "2026-11-04 09:53:00", "nhan_luc": "2026-11-04 09:55:00",
		"tam_tinh": 155000, "ten_goi": "Lan", "sdt_gioi_thieu": "0901234567",
		"mon": json.dumps([
			{"ma": "NUTR00021", "ten": "Trà Lài (M)", "sl": 2, "tc": ["Ít đá"], "gia": 45000, "tp": [{"ma": "TP1", "ten": "Trân châu", "gia": 10000}]},
			{"ma": "BANH1", "ten": "Canelé", "sl": 1, "gia": 45000}])}
	k = g.cho_khach(r, BAY)
	la("giờ gọi", k["luc"], "09:53")
	la("giờ nhận", k["nhan_luc"], "09:55")
	la("dòng: đơn giá kể cả topping, tiền theo số lượng", [(x["ten"], x["sl"], x["gia"], x["tien"], x["tc"]) for x in k["mon"]],
		[("Trà Lài (M)", 2, 55000, 110000, ["Ít đá", "+ Trân châu"]), ("Canelé", 1, 45000, 45000, [])])
	la("tổng dòng bằng tạm tính máy chủ", sum(x["tien"] for x in k["mon"]), k["tam_tinh"])
	dung("không lộ tên gọi, số giới thiệu", "Lan" not in json.dumps(k, ensure_ascii=False) and "0901234567" not in json.dumps(k))
	la("thiếu giờ gọi: rỗng, không vỡ", g.cho_khach(dict(r, luc=None), BAY)["luc"], "")


COMBO = {"ma": "KMCB00001", "ten": "Trà chiều", "gia": 120000, "goc": 140000, "mo_ta": "Mỗi ngày", "anh": "",
	"dong": [{"ma": "NUTR00021", "ten": "Trà Hoa Lài", "sl": 1}, {"ma": "BAWC00115", "ten": "Mousse Chanh Dây", "sl": 1}]}


@ca("v642 combo trên trang bàn (phép thuần): chỉ bày khi mọi món thành phần gọi được ở điểm; số bộ theo bánh còn trên tủ; giá bộ của máy chủ; thiếu món hay hết bánh thì không bày")
def _combo_thuan():
	ra = g.combo_ban_duoc([COMBO], _bang())
	la("một combo, số bộ theo 2 bánh còn", [(c["ma"], c["gia"], c["goc"], c["con"], c["loai"]) for c in ra], [("KMCB00001", 120000, 140000, 2, "combo")])
	la("thành phần kèm loại và nhóm", [(x["ma"], x["sl"], x["loai"], x["nhom"]) for x in ra[0]["thanh_phan"]],
		[("NUTR00021", 1, "nuoc", "Trà"), ("BAWC00115", 1, "banh", "Bánh lạnh")])
	hai = dict(COMBO, dong=[{"ma": "BAWC00115", "ten": "Mousse", "sl": 2}])
	la("bộ cần 2 bánh, tủ còn 2: 1 bộ", g.combo_ban_duoc([hai], _bang())[0]["con"], 1)
	la("nước đang tắt (không có trong bảng): không bày", g.combo_ban_duoc([dict(COMBO, dong=COMBO["dong"] + [{"ma": "NUCF00003", "sl": 1}])], _bang()), [])
	het = _bang()
	het["BAWC00115"]["con"] = 0
	la("hết bánh: không bày", g.combo_ban_duoc([COMBO], het), [])
	la("giá 0 hay không có món: không bày", g.combo_ban_duoc([dict(COMBO, gia=0), dict(COMBO, dong=[])], _bang()), [])
	la("mô tả món thành phần", [g.mo_ta_thanh_phan({"ten": "Canelé", "sl": 1}), g.mo_ta_thanh_phan({"ten": "Trà", "sl": 2})], ["Canelé", "2 Trà"])


@ca("v642 gọi combo: máy chủ chốt giá bộ, bỏ lựa chọn và chặn topping khách gửi; bánh trong combo cộng chung với bánh gọi lẻ khi so số còn; đơn chờ giữ bánh theo món thành phần; phiếu pha chế tách từng món")
def _combo_gio():
	bang = _bang()
	for c in g.combo_ban_duoc([COMBO], bang):
		bang[c["ma"]] = c
	dong, tam = g.chuan_gio([{"ma": "KMCB00001", "sl": 1, "tc": {"Đá": "Ít đá"}, "gia": 1}], bang)
	la("dòng combo: giá bộ, không lựa chọn", [(d["ma"], d["sl"], d["gia"], d["tc"], d["loai"]) for d in dong], [("KMCB00001", 1, 120000, [], "combo")])
	la("tạm tính theo giá bộ", tam, 120000)
	la("thành phần đi theo đơn", [(x["ma"], x["sl"]) for x in dong[0]["thanh_phan"]], [("NUTR00021", 1), ("BAWC00115", 1)])
	la("khách và quầy thấy món trong combo", g.tc_hien(dong[0]), ["Trà Hoa Lài", "Mousse Chanh Dây"])
	nem("combo không kèm topping", lambda: g.chuan_gio([{"ma": "KMCB00001", "sl": 1, "tp": ["TPNC00001"]}], bang), ValueError)
	try:
		g.chuan_gio([{"ma": "KMCB00001", "sl": 2}, {"ma": "BAWC00115", "sl": 1}], bang)
		raise AssertionError("phải chặn: 2 bộ + 1 lẻ = 3 bánh, tủ còn 2")
	except ValueError as e:
		dung("câu nói số bánh còn: " + str(e), "chỉ còn 2" in str(e))
	la("2 bộ vừa đủ 2 bánh", g.chuan_gio([{"ma": "KMCB00001", "sl": 2}], bang)[1], 240000)
	giu = g.sl_dang_cho([json.dumps(dong), json.dumps([{"ma": "BAWC00115", "sl": 1}])])
	la("đơn chờ giữ bánh theo thành phần, không giữ mã combo", giu, {"NUTR00021": 1, "BAWC00115": 2})
	la("phiếu pha chế: combo tách món, ghi tên combo", [(x["item_code"], x["qty"], x["nhom"], x["gc"]) for x in g.dong_phieu_pha([dict(dong[0], sl=2)])],
		[("NUTR00021", 2, "Trà", "Combo Trà chiều"), ("BAWC00115", 2, "Bánh lạnh", "Combo Trà chiều")])
	la("dòng thường giữ nguyên", g.dong_phieu_pha([{"ma": "NUTR00021", "ten": "Trà", "sl": 1, "tc": ["Ít đá"], "nhom": "Trà"}]),
		[{"item_code": "NUTR00021", "ten": "Trà", "qty": 1, "nhom": "Trà", "tc": ["Ít đá"], "gc": ""}])
	la("dòng hoá đơn: mã combo, giá bộ (hoá đơn tự rã khi lưu)", g.dong_hoa_don(dong)[0]["item_code"], "KMCB00001")


@ca("v642 cửa gọi món thật: combo đọc qua luật bán của hoá đơn cho CẢ HAI nguồn đơn bàn; bàn khác thấy bánh đã giữ cho combo; combo bị luật chặn ở một nguồn thì không gọi được")
def _combo_cua():
	from vagabond import combo_mon

	cb = {"name": "CB-1", "ten": "Trà chiều", "bat": 1, "kieu": "Gia tron goi", "gia_combo": 120000, "mo_ta": "", "anh": "",
		"dong": [{"item_code": "NUTR00021", "ten_mon": "Trà Hoa Lài", "so_luong": 1, "gia_goc": 45000, "nhom": ""},
			{"item_code": "BAWC00115", "ten_mon": "Mousse Chanh Dây", "so_luong": 1, "gia_goc": 95000, "nhom": ""}]}
	nguon_hoi = []

	def luat(c, ma, quay, nguon):
		nguon_hoi.append((ma, quay, nguon))
		return ""
	kho = Kho()
	goc = _fr.get_all

	def get_all(dt, *a, **k):
		if dt == "Vagabond Combo":
			return [{"name": "CB-1", "ma_hang": "KMCB00001"}]
		return kho.get_all(dt, *a, **k)
	with _he(kho), patch.object(_fr, "get_all", side_effect=get_all), patch("vagabond.khuyen_mai._doc_combo", return_value=cb), \
			patch.object(combo_mon, "ly_do_khong_ban", side_effect=luat):
		r = _gui(mon=[{"ma": "KMCB00001", "sl": 1}])
		la("gọi combo được", r["ok"], 1)
		la("luật bán hỏi cả hai nguồn", sorted({x[2] for x in nguon_hoi}), sorted([g.NGUON_TAO, g.NGUON_QR]))
		la("tạm tính giá bộ", kho.dong[r["ma"]]["tam_tinh"], 120000)
		la("bàn khác: bánh còn 1 sau khi combo giữ 1", g.bang_mon(g._diem("TCV"))["BAWC00115"]["con"], 1)
		r2 = _gui(nonce="M" * 32, ban=6, mon=[{"ma": "BAWC00115", "sl": 2}])
		la("bàn khác gọi 2 bánh bị chặn", (r2["ok"], "chỉ còn 1" in r2.get("cau", "")), (0, True))
	with _he(Kho()), patch.object(_fr, "get_all", side_effect=get_all), patch("vagabond.khuyen_mai._doc_combo", return_value=cb), \
			patch.object(combo_mon, "ly_do_khong_ban", side_effect=lambda c, ma, quay, nguon: "chặn" if nguon == g.NGUON_QR else ""):
		r3 = _gui(mon=[{"ma": "KMCB00001", "sl": 1}])
		la("combo bị chặn ở nguồn QR tại bàn: không gọi được", r3["ok"], 0)
	del goc


@ca("v642 Codex #545 vòng 1: trang khách biết lượt đã nhận thuộc bill đã chốt (phiếu tạm tính không còn mở) để không cộng vào bill mới; lượt chưa có phiếu, phiếu còn mở thì chưa trả; không lộ mã hoá đơn")
def _da_tra_642():
	r = {"name": "TQ-8", "ban": 1, "trang_thai": g.TT_NHAN, "luc": "2026-11-04 09:53:00", "nhan_luc": "2026-11-04 09:55:00",
		"tam_tinh": 45000, "mon": json.dumps([{"ma": "NUTR00021", "ten": "Trà", "sl": 1, "gia": 45000}]), "hoa_don": "ACC-SINV-1"}
	la("thuần: cờ đã trả", (g.cho_khach(r, BAY, True)["da_tra"], g.cho_khach(r, BAY)["da_tra"]), (1, 0))
	la("đơn chưa nhận không bao giờ đã trả", g.cho_khach(dict(r, trang_thai=g.TT_CHO), BAY, True)["da_tra"], 0)
	tk = g.token_khach(KHOA, "TQ-8")
	for mo, hd, can in ((set(), "ACC-SINV-1", 1), ({"ACC-SINV-1"}, "ACC-SINV-1", 0), (set(), "", 0)):
		dong = dict(r, hoa_don=hd, token_bam=g.bam(tk))
		with patch.object(g, "_bi_mat", return_value=KHOA), patch.object(_fr.db, "get_value", return_value=_fr._dict(dong)), \
				patch.object(g, "_phieu_tam_mo", return_value=mo):
			kq = g.trang_thai("TQ-8", tk)
		la("phiếu %s, phiếu mở %s: đã trả" % (hd or "(chưa có)", sorted(mo)), kq["da_tra"], can)
		dung("không lộ mã hoá đơn", "ACC-SINV" not in json.dumps(kq))


@ca("v642 Codex #545 vòng 6: trang khách hỏi trạng thái lượt đã nhận thì nhận kèm TỔNG hoá đơn của bàn đang mở (gồm món máy khác gọi, món quầy thêm), khoá hoá đơn là mã băm không lộ tên phiếu; lượt chờ nhận, đã trả thì không kèm; đọc hoá đơn lỗi vẫn trả trạng thái")
def _bill_ban_642():
	r = {"name": "TQ-8", "ban": 1, "trang_thai": g.TT_NHAN, "luc": "2026-11-04 09:53:00", "nhan_luc": "2026-11-04 09:55:00",
		"tam_tinh": 100000, "mon": json.dumps([{"ma": "NUTR00021", "ten": "Trà", "sl": 2, "gia": 50000}]), "hoa_don": "ACC-SINV-1"}
	tk = g.token_khach(KHOA, "TQ-8")
	dong = dict(r, token_bam=g.bam(tk))

	def doc(si=None, loi=False):
		def gv(dt, ten, f=None, **k):
			if dt == g.DT:
				return _fr._dict(dong)
			if loi:
				raise RuntimeError("hỏng đọc")
			return _fr._dict(si or {})
		return gv

	def hoi(mo, gv, dong_moi=None):
		if dong_moi:
			dong.update(dong_moi)
		with patch.object(g, "_bi_mat", return_value=KHOA), patch.object(_fr.db, "get_value", side_effect=gv), \
				patch.object(g, "_phieu_tam_mo", return_value=mo), patch.object(_fr, "log_error"):
			return g.trang_thai("TQ-8", tk)

	kq = hoi({"ACC-SINV-1"}, doc({"grand_total": 140000.0}))
	la("lượt máy này 100.000 đ, hoá đơn của bàn 140.000 đ", (kq["tam_tinh"], (kq.get("bill") or {}).get("tong")), (100000, 140000))
	dung("khoá hoá đơn không lộ tên phiếu", (kq.get("bill") or {}).get("khoa") and "SINV" not in json.dumps(kq))
	la("cùng phiếu thì cùng khoá (hai máy cùng bàn gộp đúng một lần)", g.the_bill("ACC-SINV-1", 1)["khoa"], kq["bill"]["khoa"])
	dung("phiếu khác thì khoá khác", g.the_bill("ACC-SINV-2", 1)["khoa"] != kq["bill"]["khoa"])
	la("đã trả: không kèm hoá đơn", (hoi(set(), doc({"grand_total": 140000.0})).get("bill"), hoi(set(), doc({}))["da_tra"]), (None, 1))
	la("chờ nhận: không kèm", hoi({"ACC-SINV-1"}, doc({"grand_total": 1.0}), {"trang_thai": g.TT_CHO}).get("bill"), None)
	dong.update(trang_thai=g.TT_NHAN)
	kq = hoi({"ACC-SINV-1"}, doc(loi=True))
	# Codex PR #545 vòng 7: đọc lỗi vẫn báo khoá phiếu (tổng rỗng) để trang không cộng trùng lượt này.
	la("đọc hoá đơn lỗi: vẫn trả trạng thái, kèm khoá phiếu, tổng rỗng", (kq["ok"], kq["trang_thai"], kq.get("bill")),
		(1, g.TT_NHAN, {"khoa": g.the_bill("ACC-SINV-1", 1)["khoa"], "tong": None}))
	la("phiếu không đọc ra dòng nào: khoá phiếu, tổng rỗng", hoi({"ACC-SINV-1"}, lambda dt, ten, f=None, **k: _fr._dict(dong) if dt == g.DT else None).get("bill"),
		{"khoa": g.the_bill("ACC-SINV-1", 1)["khoa"], "tong": None})
	la("thuần: tổng làm tròn đồng", g.the_bill("X", "140000.4"), {"khoa": g.the_bill("X", 0)["khoa"], "tong": 140000})
	la("thuần: tổng 0 đ vẫn là số, không rỗng", g.the_bill("X", 0)["tong"], 0)
	la("thuần: tổng lạ là rỗng", [g.the_bill("X", None)["tong"], g.the_bill("X", "abc")["tong"]], [None, None])
