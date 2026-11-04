# -*- coding: utf-8 -*-
"""v638: mã giới thiệu và hoa hồng giới thiệu (anh Việt duyệt 04/11/2026).

Phần thuần gọi thẳng. Phần chạm hệ chạy HÀM THẬT của gioi_thieu.py (kiem,
gan_cho_don_web, gan_cho_hoa_don, truoc_khi_luu, khi_ghi_so, khi_huy,
doi_nguoi, dua_vao_kpi, toan_tiem), don_web.tao_ban_ghi, don_web.cau_hinh_web
và kpi.day_chi, chỉ thay tầng Frappe bằng một cơ sở dữ liệu giả trong bộ nhớ
(bảng, Singles, Comment) ghi lại lời gọi. Màn app nạp thật trong node ở
hanh_vi/hoa_hong_gioi_thieu_638.js; ô web ở hanh_vi/thanh_toan_web_638.mjs.
"""

import ast
import contextlib
import datetime
import json
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import gioi_thieu as gt  # noqa: E402

GOC = Path(__file__).resolve().parents[3]


# ------------------------------------------------------------ CSDL giả

def _khop(r, loc):
	for k, v in (loc or {}).items():
		x = r.get(k)
		if isinstance(v, (list, tuple)) and len(v) == 2 and isinstance(v[0], str):
			op, gtri = v
			if op == "in":
				if x not in gtri:
					return False
			elif op == "is":
				if (gtri == "set") != bool(x):
					return False
			elif op == "between":
				if not (str(gtri[0]) <= str(x)[:10] <= str(gtri[1])):
					return False
			elif op == "!=":
				if x == gtri:
					return False
			else:
				raise AssertionError("bộ lọc chưa hỗ trợ " + op)
		elif x != v:
			return False
	return True


class Doc(dict):
	"""Một chứng từ giả đủ dùng cho gioi_thieu.py."""

	def __init__(self, db=None, doctype=None, **k):
		super().__init__(**k)
		self.__dict__["db"] = db
		self.__dict__["doctype"] = doctype
		self.__dict__["flags"] = _fr.flags.__class__()
		self.__dict__["_truoc"] = None

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def set(self, k, v):
		self[k] = v

	def is_new(self):
		return not self.get("name") or self.get("__islocal")

	def get_doc_before_save(self):
		return self.__dict__["_truoc"]

	def db_set(self, k, v=None, update_modified=True):
		gtri = k if isinstance(k, dict) else {k: v}
		self.update(gtri)
		self.__dict__["db"].set_value(self.__dict__["doctype"], self["name"], gtri)

	def reload(self):
		self.update(self.__dict__["db"].bang[self.__dict__["doctype"]][self["name"]])

	def update(self, d=None, **k):
		dict.update(self, d or {}, **k)

	def insert(self, ignore_permissions=False):
		db = self.__dict__["db"]
		if not self.get("name"):
			db.so += 1
			self["name"] = "%s-%03d" % (self.__dict__["doctype"][:3].upper(), db.so)
		db.bang.setdefault(self.__dict__["doctype"], {})[self["name"]] = dict(self)
		return self

	def as_dict(self):
		return dict(self)

	def save(self, ignore_permissions=False):
		self.__dict__["db"].bang.setdefault(self.__dict__["doctype"], {})[self["name"]] = dict(self)
		return self


class DB:
	def __init__(self):
		self.bang = {}
		self.singles = {}
		self.so = 0
		self.ghi = []
		self.vet = []
		self.commit_so = 0

	# frappe.db
	def get_value(self, dt, ten, truong=None, as_dict=False, **k):
		rows = self.bang.get(dt, {})
		if isinstance(ten, dict):
			r = next((r for r in rows.values() if _khop(r, ten)), None)
		else:
			r = rows.get(ten)
		if r is None:
			return None
		if isinstance(truong, (list, tuple)):
			d = {f: r.get(f) for f in truong}
			return _D(d) if as_dict else tuple(d.values())
		return r.get(truong or "name")

	def set_value(self, dt, ten, k, v=None, update_modified=True):
		gtri = k if isinstance(k, dict) else {k: v}
		self.ghi.append((dt, ten, dict(gtri)))
		self.bang.setdefault(dt, {}).setdefault(ten, {"name": ten}).update(gtri)

	def exists(self, dt, ten=None):
		rows = self.bang.get(dt, {})
		if isinstance(ten, dict):
			return next((r["name"] for r in rows.values() if _khop(r, ten)), None)
		return ten if ten in rows else None

	def sql(self, q, p=None, **k):
		if "tabSingles" in q:
			v = self.singles.get(p[0])
			return [(v,)] if v is not None else []
		return []

	def set_single_value(self, dt, k, v):
		self.singles[k] = v

	def commit(self, *a, **k):
		self.commit_so += 1

	def rollback(self, *a, **k):
		pass

	# frappe.get_all
	def get_all(self, dt, filters=None, fields=None, **k):
		ra = []
		for r in self.bang.get(dt, {}).values():
			if _khop(r, filters):
				ra.append(_D({f: r.get(f) for f in (fields or ["name"])}))
		return ra

	def get_doc(self, dt, ten=None, **k):
		if isinstance(dt, dict):
			d = Doc(self, dt.get("doctype"), **{k: v for k, v in dt.items() if k != "doctype"})
			if dt.get("doctype") == "Comment":
				self.vet.append(dt)
			return d
		r = self.bang[dt][ten]
		d = Doc(self, dt, **r)
		d.__dict__["_truoc"] = Doc(self, dt, **r)
		return d

	def new_doc(self, dt):
		return Doc(self, dt, __islocal=1)


class _D(dict):
	__getattr__ = dict.get


@contextlib.contextmanager
def moi_truong(db, vai=("Sales User",), toi="thungan@x"):
	ns = types.SimpleNamespace(
		get_value=db.get_value, set_value=db.set_value, exists=db.exists, sql=db.sql,
		set_single_value=db.set_single_value, commit=db.commit, rollback=db.rollback, get_all=db.get_all)
	with patch.object(_fr, "db", ns), patch.object(_fr, "get_all", db.get_all), \
			patch.object(_fr, "get_doc", db.get_doc), patch.object(_fr, "new_doc", db.new_doc, create=True), \
			patch.object(_fr, "get_roles", lambda *a, **k: list(vai)), \
			patch.object(_fr, "session", types.SimpleNamespace(user=toi)), \
			patch.object(_fr, "log_error", lambda *a, **k: db.ghi.append(("LOI", k.get("title") or (a[0] if a else ""), {}))):
		yield db


NV = {
	"ngan@x": {"name": "ngan@x", "full_name": "Nguyễn Thị Ngân", "first_name": "Ngân", "mobile_no": "+84 909 123 456",
		"enabled": 1, "user_type": "System User"},
	"lan@x": {"name": "lan@x", "full_name": "Trần Lan", "first_name": "Lan", "mobile_no": "0912.000.111",
		"enabled": 1, "user_type": "System User"},
	"khoa@x": {"name": "khoa@x", "full_name": "Lê Khoá", "mobile_no": "0933444555", "enabled": 0, "user_type": "System User"},
	"web@x": {"name": "web@x", "full_name": "Khách Web", "mobile_no": "0944555666", "enabled": 1, "user_type": "Website User"},
	"a@x": {"name": "a@x", "full_name": "Phạm A", "mobile_no": "0977888999", "enabled": 1, "user_type": "System User"},
	"b@x": {"name": "b@x", "full_name": "Võ B", "mobile_no": "+84977888999", "enabled": 1, "user_type": "System User"},
}


def _db(bat=1, pt_web=2, pt_tai_ban=2):
	db = DB()
	db.bang["User"] = {k: dict(v) for k, v in NV.items()}
	if bat is not None:
		db.singles[gt.O_BAT] = bat
	if pt_web is not None:
		db.singles[gt.O_PT_WEB] = pt_web
	if pt_tai_ban is not None:
		db.singles[gt.O_PT_TAI_BAN] = pt_tai_ban
	return db


def _hd(db, ten, **k):
	r = {"name": ten, "docstatus": 0, "is_return": 0, "posting_date": "2026-11-03", "vgb_huy": 0,
		"discount_amount": 0, "customer": "Khách lẻ", "items": []}
	r.update(k)
	db.bang.setdefault(gt.DT_HD, {})[ten] = r
	for i, d in enumerate(r["items"]):
		db.bang.setdefault("Sales Invoice Item", {})["%s-%d" % (ten, i)] = dict(d, parent=ten, parenttype=gt.DT_HD, name="%s-%d" % (ten, i))
	return db.get_doc(gt.DT_HD, ten)


MON = [{"item_code": "BANH01", "amount": 600000}, {"item_code": "BANH02", "amount": 400000},
	{"item_code": "DVBH00001", "amount": 36000}]


# ------------------------------------------------------------------ phần thuần

@ca("v638 chuẩn hoá số điện thoại: +84, 84, 0084, số 0 đầu, khoảng trắng, dấu chấm, gạch ra cùng một dạng; số ngắn ra rỗng")
def _chuan_sdt():
	for v in ("+84 909 123 456", "84909123456", "0084909123456", "0909.123.456", "0909-123-456", "909123456", " 0909123456 "):
		la("chuẩn " + v, gt.chuan_sdt(v), "0909123456")
	for v in ("", None, "12345", "abc", "0909"):
		la("ngắn hoặc rỗng " + repr(v), gt.chuan_sdt(v), "")


@ca("v638 tìm nhân viên theo số: đúng người đang làm; tài khoản khoá, không phải System User, Administrator, hai người trùng số thì không nhận")
def _chon_nv():
	ds = list(NV.values()) + [{"name": "Administrator", "mobile_no": "0955000111", "enabled": 1, "user_type": "System User"}]
	la("đúng người dù lưu +84", gt.chon_nhan_vien("0909 123 456", ds)["name"], "ngan@x")
	la("đúng người lưu dấu chấm", gt.chon_nhan_vien("+84912000111", ds)["name"], "lan@x")
	la("tài khoản khoá", gt.chon_nhan_vien("0933444555", ds), None)
	la("không phải System User", gt.chon_nhan_vien("0944555666", ds), None)
	la("Administrator", gt.chon_nhan_vien("0955000111", ds), None)
	la("hai người cùng số", gt.chon_nhan_vien("0977888999", ds), None)
	la("số lạ", gt.chon_nhan_vien("0900000000", ds), None)
	la("số rỗng không khớp người không có số", gt.chon_nhan_vien("", ds + [{"name": "x@x", "mobile_no": "", "enabled": 1, "user_type": "System User"}]), None)
	la("tên gọi chữ cuối", [gt.ten_goi("Nguyễn Thị Ngân"), gt.ten_goi("", "Lan Anh"), gt.ten_goi("")], ["Ngân", "Anh", ""])


@ca("v638 tiền tính hoa hồng: bỏ dòng phí giao DVBH00001 (cả viết thường), trừ giảm cả đơn, không âm; hoa hồng làm tròn đồng")
def _tien():
	la("bỏ phí giao, trừ ưu đãi", gt.tien_tinh(MON, 100000), 900000)
	la("phí giao viết thường", gt.tien_tinh([{"item_code": "dvbh00001", "amount": 50000}, {"item_code": "X", "amount": 1000}]), 1000)
	la("ưu đãi lớn hơn tiền hàng", gt.tien_tinh(MON, 5000000), 0)
	la("2% của 900.000", gt.hoa_hong(900000, 2), 18000)
	la("1,5% làm tròn", gt.hoa_hong(333333, 1.5), 5000)
	la("% kẹp 0..100", (gt.chuan_pt(150), gt.chuan_pt(-5), gt.chuan_pt(None), gt.chuan_pt("abc")), (100.0, 0.0, 2.0, 2.0))
	la("mã phí giao một nguồn với phi_giao.py", gt.MA_PHI_GIAO, __import__("vagabond.phi_giao", fromlist=["x"]).MA_PHI_GIAO)
	from vagabond import kpi
	dung("bộ vai xem phủ đủ phân hệ KPI", kpi.VAI_XEM <= gt.VAI_XEM)
	from vagabond import vai_cua_hang
	la("vai quản lý cửa hàng đúng tên vai thật trên site", gt.VAI_QLCH, vai_cua_hang.VAI_QLCH)
	dung("quản lý cửa hàng (vai thật) xem được toàn tiệm và đổi được người", gt.VAI_QLCH in gt.VAI_XEM and gt.VAI_QLCH in gt.VAI_DOI)
	dung("thu ngân không đổi được người giới thiệu", not ({"Sales User", "Accounts User", "Kế toán"} & gt.VAI_DOI))


@ca("v638 tự giới thiệu: khách đặt bằng chính số nhân viên (viết kiểu khác) thì không tính; nhân viên đặt bằng số khác vẫn tính")
def _tu_gt():
	dung("cùng số khác cách viết", gt.tu_gioi_thieu("+84 909 123 456", ["0909.123.456"]))
	dung("số khác", not gt.tu_gioi_thieu("0909123456", ["0912000111", None, ""]))
	dung("nhân viên không có số", not gt.tu_gioi_thieu("", ["0909123456"]))


@ca("v638 Cài đặt: % ngoài 0 tới 100 thì chặn lưu với câu nói rõ ô nào; 0 và 100 hợp lệ")
def _cai_dat():
	for v in (0, 100, 2, "", None):
		gt.kiem_cai_dat(Doc(None, "Vagabond Settings", **{gt.O_PT_WEB: v, gt.O_PT_TAI_BAN: 2}))
	nem("101%", lambda: gt.kiem_cai_dat(Doc(None, "x", **{gt.O_PT_WEB: 101})), _fr.ValidationError)
	nem("-1%", lambda: gt.kiem_cai_dat(Doc(None, "x", **{gt.O_PT_TAI_BAN: -1})), _fr.ValidationError)
	try:
		gt.kiem_cai_dat(Doc(None, "x", **{gt.O_PT_TAI_BAN: 120}))
	except _fr.ValidationError as e:
		dung("câu nêu đúng ô", "tại bàn" in str(e) and "120" in str(e))


@ca("v638 mặc định: chưa lưu thì công tắc bật, 2%, 2%; gieo_mac_dinh chỉ ghi ô chưa có, không đè 0% hay công tắc tắt người đã chọn")
def _mac_dinh():
	db = _db(bat=None, pt_web=None, pt_tai_ban=None)
	with moi_truong(db):
		la("chưa lưu", (gt.bat(), gt.pt_cho("web"), gt.pt_cho("tai_ban")), (True, 2.0, 2.0))
		gt.gieo_mac_dinh()
		la("đã gieo", db.singles, {gt.O_BAT: 1, gt.O_PT_WEB: 2.0, gt.O_PT_TAI_BAN: 2.0})
	db = _db(bat="0", pt_web="0", pt_tai_ban="3.5")
	with moi_truong(db):
		gt.gieo_mac_dinh()
		la("không đè lựa chọn", (gt.bat(), gt.pt_cho("web"), gt.pt_cho("tai_ban")), (False, 0.0, 3.5))


@ca("v638 trạng thái và dòng màn: ghi sổ lấy số đã chốt (không tính lại theo % mới), nháp là tạm tính, huỷ hay hoàn tiền là 0")
def _dong():
	r = {"name": "SI-1", "docstatus": 1, gt.O_PT: 5, gt.O_HH: 18000, "discount_amount": 100000, gt.O_NGUOI: "ngan@x",
		gt.O_LOAI: "web", "custom_pancake_display_id": "91428", "posting_date": "2026-11-03"}
	d = gt.dong_hoa_don(r, MON)
	la("ghi sổ: số đã chốt", (d["tt"], d["tien_hang"], d["hoa_hong"], d["hien"]), ("ghi_so", 900000, 18000, "Đơn #91428"))
	la("nháp: tạm tính theo % của đơn", gt.dong_hoa_don(dict(r, docstatus=0), MON)["hoa_hong"], 45000)
	la("huỷ", [gt.dong_hoa_don(dict(r, docstatus=2), MON)["hoa_hong"], gt.dong_hoa_don(dict(r, docstatus=0, vgb_huy=1), MON)["tt"]], [0, "huy"])
	la("hoàn tiền", (gt.dong_hoa_don(r, MON, True)["tt"], gt.dong_hoa_don(r, MON, True)["hoa_hong"]), ("hoan", 0))
	dw = gt.dong_don_web({"name": "DW-1", "trang_thai": "Da nhan", gt.O_DW_PT: 2, "ngay_nhan": "2026-11-05 10:00"}, 500000)
	la("đơn web chờ", (dw["tt"], dw["hoa_hong"], dw["ngay"], dw["loai"]), ("cho", 10000, "2026-11-05", "web"))
	la("đơn web huỷ", gt.dong_don_web({"trang_thai": "Da huy", gt.O_DW_PT: 2}, 500000)["hoa_hong"], 0)
	rows = [dict(d, nguoi="ngan@x"), dict(gt.dong_hoa_don(dict(r, docstatus=0), MON), nguoi="ngan@x"),
		dict(gt.dong_hoa_don(r, MON, True), nguoi="lan@x"), dict(d, nguoi="lan@x", hoa_hong=30000)]
	la("tạm tính tháng", gt.tong_hop(rows), {"ghi_so": {"so_don": 2, "tien_hang": 1800000, "hoa_hong": 48000},
		"cho": {"so_don": 1, "tien_hang": 900000, "hoa_hong": 45000}, "huy": {"so_don": 1, "tien_hang": 0, "hoa_hong": 0}})
	la("bảng nhân viên", [(o["nguoi"], o["so_don"], o["hoa_hong"], o["so_cho"], o["hoa_hong_cho"]) for o in gt.theo_nhan_vien(rows)],
		[("lan@x", 1, 30000, 0, 0), ("ngan@x", 1, 18000, 1, 45000)])
	la("kỳ tháng", [str(x) for x in gt.ky_thang("2026-12", datetime.date(2026, 11, 4))], ["2026-12", "2026-12-01", "2026-12-31"])
	la("kỳ sai dạng về tháng này", gt.ky_thang("abc", datetime.date(2026, 11, 4))[0], "2026-11")


@ca("v638 kế hoạch đưa vào phiếu KPI: ghi ĐÈ tổng tháng, áp lần hai ra toàn 'giữ'; phiếu đã chốt để nguyên; người về 0 thì ghi 0")
def _ke_hoach():
	rows = [{"tt": "ghi_so", "nguoi": "ngan@x", "ma": "SI-1", "hoa_hong": 18000},
		{"tt": "ghi_so", "nguoi": "ngan@x", "ma": "SI-2", "hoa_hong": 2000},
		{"tt": "cho", "nguoi": "ngan@x", "ma": "SI-3", "hoa_hong": 9000},
		{"tt": "ghi_so", "nguoi": "lan@x", "ma": "SI-4", "hoa_hong": 5000}]
	phieu = {"ngan@x": {"name": "KPI-1", "hh": 0}, "a@x": {"name": "KPI-9", "hh": 7000},
		"b@x": {"name": "KPI-8", "hh": 3000, "dong_bang": 1}}
	v = {x["nguoi"]: x for x in gt.ke_hoach_kpi(rows, phieu)}
	la("việc", {k: (x["viec"], x["so"]) for k, x in v.items()},
		{"ngan@x": ("cap_nhat", 20000), "lan@x": ("tao", 5000), "a@x": ("cap_nhat", 0), "b@x": ("da_chot", 0)})
	la("đơn ghi kèm", v["ngan@x"]["don"], [["SI-1", 18000], ["SI-2", 2000]])
	# Áp kết quả rồi chạy lại: không còn việc ghi nào.
	for k, x in v.items():
		if x["viec"] in ("cap_nhat", "tao"):
			phieu.setdefault(k, {"name": "KPI-new"})["hh"] = x["so"]
	la("lần hai", sorted(x["viec"] for x in gt.ke_hoach_kpi(rows, phieu)), ["da_chot", "giu", "giu"])


# ------------------------------------------------------------ phần chạm hệ

@ca("v638 cửa kiem (khách vãng lai): chỉ trả ok và TÊN GỌI, không lộ số, email, họ tên; không thấy thì ok 0; công tắc tắt thì tat 1; POST và giới hạn lượt")
def _kiem():
	db = _db()
	with moi_truong(db):
		kq = gt.kiem("0909 123 456")
		la("chỉ hai khoá", kq, {"ok": 1, "ten": "Ngân"})
		s = json.dumps(kq, ensure_ascii=False)
		dung("không lộ gì thêm", not re.search(r"0909|123456|@|Nguyễn", s))
		la("không thấy", gt.kiem("0900000000"), {"ok": 0})
		la("trùng số", gt.kiem("0977888999"), {"ok": 0})
		la("tài khoản khoá", gt.kiem("0933444555"), {"ok": 0})
	with moi_truong(_db(bat=0)):
		la("công tắc tắt", gt.kiem("0909123456"), {"ok": 0, "tat": 1})
	la("chỉ nhận POST", getattr(gt.kiem, "__vgb_methods__", None), ["POST"])
	cay = ast.parse((GOC / "vagabond/gioi_thieu.py").read_text())
	f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "kiem")
	trang = [ast.unparse(d) for d in f.decorator_list]
	la("decorator: cửa khách POST và trần 20 lượt/10 phút", trang,
		["frappe.whitelist(allow_guest=True, methods=['POST'])", "rate_limit(limit=20, seconds=600)"])


@ca("v638 tên gọi cho máy chủ (gọi món tại bàn): đúng người ra tên gọi, không thấy hay công tắc tắt ra rỗng, không qua cửa khách giới hạn lượt")
def _ten_theo_sdt():
	with moi_truong(_db()):
		la("đúng người", gt.ten_theo_sdt("0909 123 456"), "Ngân")
		la("không thấy", gt.ten_theo_sdt("0900000000"), "")
	with moi_truong(_db(bat=0)):
		la("công tắc tắt", gt.ten_theo_sdt("0909123456"), "")
	cay = ast.parse((GOC / "vagabond/goi_mon_ban.py").read_text())
	f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_ten_gioi_thieu")
	dung("gọi món tại bàn không gọi cửa khách kiem", "gioi_thieu.kiem" not in ast.unparse(f))


@ca("v638 đơn web: tao_ban_ghi gắn người giới thiệu và % chốt lúc đặt từ ảnh chụp; tự giới thiệu, công tắc tắt, số lạ thì không gắn; lỗi không chặn đơn")
def _don_web():
	from vagabond import don_web

	def tao(db, sdt_gt, sdt_khach="0901234567"):
		snap = {"gioi_thieu_sdt": sdt_gt, "nguoi_dat": {"dien_thoai": sdt_khach}}
		with moi_truong(db), patch.object(don_web, "_khoa_bi_mat", lambda: "k" * 32):
			return don_web.tao_ban_ghi("n" * 32, {"dien_thoai": sdt_khach, "snapshot": json.dumps(snap)})

	db = _db(pt_web=3)
	b = tao(db, "0909123456")
	luu = db.bang[gt.DT_DW][b.name]
	la("đã gắn và lưu cùng lúc insert", (luu.get(gt.O_DW_NGUOI), luu.get(gt.O_DW_PT)), ("ngan@x", 3.0))
	la("tự giới thiệu", db.bang[gt.DT_DW][tao(db, "0909123456", "+84909123456").name].get(gt.O_DW_NGUOI), None)
	la("số lạ", db.bang[gt.DT_DW][tao(db, "0900000000").name].get(gt.O_DW_NGUOI), None)
	db2 = _db(bat=0)
	b2 = tao(db2, "0909123456")
	la("công tắc tắt", db2.bang[gt.DT_DW][b2.name].get(gt.O_DW_NGUOI), None)
	with patch.object(gt, "tim_nhan_vien", lambda s: 1 / 0):
		db3 = _db()
		b3 = tao(db3, "0909123456")
	dung("lỗi trong phép gắn: đơn vẫn lưu, có Error Log", b3.name in db3.bang[gt.DT_DW] and any(x[0] == "LOI" for x in db3.ghi))
	# % chốt lúc đặt: đổi Cài đặt sau đó, hoá đơn ghi sổ vẫn dùng 3%.
	db.singles[gt.O_PT_WEB] = 10
	with moi_truong(db):
		si = _hd(db, "SI-W", items=MON, discount_amount=100000, custom_pancake_display_id="91428", docstatus=1)
		db.bang[gt.DT_DW][b.name]["pancake_display_id"] = "91428"
		gt.khi_ghi_so(si)
	r = db.bang[gt.DT_HD]["SI-W"]
	la("hoá đơn chép người, loại, % lúc đặt; tính trên 900.000", (r.get(gt.O_NGUOI), r.get(gt.O_LOAI), r.get(gt.O_PT), r.get(gt.O_HH)),
		("ngan@x", "web", 3.0, 27000))


@ca("v638 cấu hình web công khai mang cờ gioi_thieu theo công tắc (để trang đặt bánh ẩn ô Mã giới thiệu)")
def _cau_hinh_web():
	from vagabond import don_web, noi_dung_web, onepay
	for bat, can in ((1, 1), (0, 0), (None, 1)):
		with moi_truong(_db(bat=bat)), patch.object(onepay, "dung_duoc", lambda: False), \
				patch.object(noi_dung_web, "chinh_sach_dang_hien", lambda: []), \
				patch.object(don_web, "nguong_mien_phi", lambda: 0), patch.object(don_web, "lien_he", lambda: {}), \
				patch.object(don_web, "pixel_id", lambda: ""):
			la("công tắc " + repr(bat), don_web.cau_hinh_web()["gioi_thieu"], can)
	la("ô người giới thiệu trên Don Web không sửa tay được", {"vgb_nguoi_gioi_thieu", "vgb_pt_gioi_thieu"} <= set(don_web.KHONG_DOI), True)


@ca("v638 tại bàn: gan_cho_hoa_don gắn % lúc gọi trên doc chưa lưu và đã lưu; đã có người thì không đè; tự giới thiệu, tắt, số lạ không gắn; không bao giờ ném")
def _tai_ban():
	db = _db(pt_tai_ban=4)
	with moi_truong(db):
		moi = Doc(db, gt.DT_HD, __islocal=1, docstatus=0, customer="Khách lẻ")
		la("doc chưa lưu", gt.gan_cho_hoa_don(moi, "0909123456", "tai_ban"), {"ok": 1, "nguoi": "ngan@x", "ten": "Ngân"})
		la("ô trên doc", (moi[gt.O_NGUOI], moi[gt.O_LOAI], moi[gt.O_PT]), ("ngan@x", "tai_ban", 4.0))
		dung("chưa lưu thì không ghi xuống", not db.ghi)
		si = _hd(db, "SI-T", customer="Khách lẻ")
		la("doc đã lưu", gt.gan_cho_hoa_don(si, "0912000111")["ok"], 1)
		la("đã lưu: ghi xuống luôn", db.bang[gt.DT_HD]["SI-T"][gt.O_NGUOI], "lan@x")
		la("đã có người: không đè", gt.gan_cho_hoa_don("SI-T", "0909123456"), {"ok": 0, "ly_do": "da_co", "nguoi": "lan@x"})
		db.bang["Customer"] = {"KH-1": {"name": "KH-1", "mobile_no": "0909123456"}}
		la("khách là chính nhân viên", gt.gan_cho_hoa_don(Doc(db, gt.DT_HD, __islocal=1, customer="KH-1"), "0909123456")["ly_do"], "tu_gioi_thieu")
		la("sdt khách truyền vào", gt.gan_cho_hoa_don(Doc(db, gt.DT_HD, __islocal=1), "0909123456", sdt_khach="+84909123456")["ly_do"], "tu_gioi_thieu")
		la("số lạ", gt.gan_cho_hoa_don(Doc(db, gt.DT_HD, __islocal=1), "0900000000")["ly_do"], "khong_thay")
		la("hoá đơn đã ghi sổ", gt.gan_cho_hoa_don(Doc(db, gt.DT_HD, __islocal=1, docstatus=1), "0909123456")["ly_do"], "da_ghi_so")
		with patch.object(gt, "tim_nhan_vien", lambda s: 1 / 0):
			la("lỗi: trả loi, không ném", gt.gan_cho_hoa_don(Doc(db, gt.DT_HD, __islocal=1), "0909123456")["ly_do"], "loi")
	with moi_truong(_db(bat=0)) as db0:
		la("công tắc tắt", gt.gan_cho_hoa_don(Doc(db0, gt.DT_HD, __islocal=1), "0909123456")["ly_do"], "tat")


@ca("v638 ghi sổ tính hoa hồng (tiền hàng sau ưu đãi, bỏ phí giao); tại bàn CỘNG THÊM dù người giới thiệu cũng là người bán; huỷ về 0")
def _ghi_so():
	db = _db()
	with moi_truong(db):
		si = _hd(db, "SI-1", docstatus=1, items=MON, discount_amount=100000, vgb_nguoi_ban="ngan@x",
			**{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2})
		gt.khi_ghi_so(si)
		r = db.bang[gt.DT_HD]["SI-1"]
		la("2% của 900.000", r[gt.O_HH], 18000)
		la("người bán giữ nguyên, không đụng", r["vgb_nguoi_ban"], "ngan@x")
		si = db.get_doc(gt.DT_HD, "SI-1")
		si["docstatus"] = 2
		gt.khi_huy(si)
		la("huỷ về 0, có ghi chú", (db.bang[gt.DT_HD]["SI-1"][gt.O_HH], bool(db.bang[gt.DT_HD]["SI-1"][gt.O_GHI_CHU])), (0, True))
		# Khách đặt bằng chính số nhân viên (khách có hồ sơ): ghi sổ ra 0.
		db.bang["Customer"] = {"KH-NV": {"name": "KH-NV", "mobile_no": "0912 000 111"}}
		si2 = _hd(db, "SI-2", docstatus=1, items=MON, customer="KH-NV", **{gt.O_NGUOI: "lan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2})
		gt.khi_ghi_so(si2)
		la("tự giới thiệu lúc ghi sổ: 0", db.bang[gt.DT_HD]["SI-2"][gt.O_HH], 0)
		# Hoá đơn không có người giới thiệu: không ghi gì.
		n = len(db.ghi)
		gt.khi_ghi_so(_hd(db, "SI-3", docstatus=1, items=MON))
		la("không có người: không ghi", len(db.ghi), n)


@ca("v638 hoàn tiền: tờ trả hàng ghi sổ đưa hoa hồng tờ gốc về 0; huỷ tờ trả hàng thì tính lại tờ gốc")
def _hoan():
	db = _db()
	with moi_truong(db):
		_hd(db, "SI-G", docstatus=1, items=MON, **{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "web", gt.O_PT: 2, gt.O_HH: 19280})
		tra = _hd(db, "SI-R", docstatus=1, is_return=1, return_against="SI-G", items=[])
		gt.khi_ghi_so(tra)
		la("tờ gốc về 0", db.bang[gt.DT_HD]["SI-G"][gt.O_HH], 0)
		db.bang[gt.DT_HD]["SI-R"]["docstatus"] = 2
		gt.khi_huy(db.get_doc(gt.DT_HD, "SI-R"))
		la("huỷ tờ trả hàng: tờ gốc tính lại (1.000.000 x 2%, phí giao không tính)", db.bang[gt.DT_HD]["SI-G"][gt.O_HH], 20000)
		la("tờ trả hàng không mang người", db.bang[gt.DT_HD]["SI-R"].get(gt.O_HH), None)


@ca("v638 thu ngân không đổi được người giới thiệu: lưu hoá đơn với ô bị đổi thì máy trả lại giá trị cũ; cửa của tệp này (cờ máy) và tờ sửa lại thì được")
def _chan_thu_ngan():
	db = _db()
	with moi_truong(db):
		si = _hd(db, "SI-1", **{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2})
		si[gt.O_NGUOI] = "lan@x"
		si[gt.O_PT] = 50
		gt.truoc_khi_luu(si)
		la("trả lại", (si[gt.O_NGUOI], si[gt.O_PT]), ("ngan@x", 2))
		si2 = db.get_doc(gt.DT_HD, "SI-1")
		si2.flags.vgb_gioi_thieu_may = True
		si2[gt.O_NGUOI] = "lan@x"
		gt.truoc_khi_luu(si2)
		la("cờ máy: giữ", si2[gt.O_NGUOI], "lan@x")
		# Chính doc vừa được gan_cho_hoa_don gắn (tại bàn) rồi thu ngân sửa ô:
		# không được có cờ miễn chặn dính lại trên doc đó.
		si3 = _hd(db, "SI-3", customer="Khách lẻ")
		gt.gan_cho_hoa_don(si3, "0909123456")
		si3.__dict__["_truoc"] = db.get_doc(gt.DT_HD, "SI-3")
		si3[gt.O_NGUOI] = "lan@x"
		gt.truoc_khi_luu(si3)
		la("doc vừa gắn rồi bị sửa tay: vẫn trả lại", si3[gt.O_NGUOI], "ngan@x")
		sua = Doc(db, gt.DT_HD, __islocal=1, amended_from="SI-1")
		gt.truoc_khi_luu(sua)
		la("tờ gốc chưa huỷ: tờ sửa lại không mang người", sua.get(gt.O_NGUOI), None)
		db.bang[gt.DT_HD]["SI-1"]["docstatus"] = 2
		sua = Doc(db, gt.DT_HD, __islocal=1, amended_from="SI-1", **{gt.O_PT: 100})
		gt.truoc_khi_luu(sua)
		la("tờ sửa lại mang người và % của tờ gốc đã huỷ (không lấy % gửi lên)", (sua.get(gt.O_NGUOI), sua.get(gt.O_PT)), ("ngan@x", 2))
	from vagabond import hooks
	si_ev = hooks.doc_events["Sales Invoice"]
	dung("hook đúng chỗ", "vagabond.gioi_thieu.truoc_khi_luu" in si_ev["before_validate"]
		and "vagabond.gioi_thieu.khi_ghi_so" in si_ev["on_submit"] and "vagabond.gioi_thieu.khi_huy" in si_ev["on_cancel"])
	dung("không hook trên *", "gioi_thieu" not in json.dumps(hooks.doc_events.get("*", {})))
	la("hook Cài đặt", hooks.doc_events["Vagabond Settings"]["validate"], "vagabond.gioi_thieu.kiem_cai_dat")
	ten = {o["fieldname"]: o for o in gt.TRUONG_MOI[gt.DT_HD]}
	dung("các ô trên hoá đơn chỉ đọc, không chép sang tờ mới", all(o.get("read_only") and o.get("no_copy") for o in ten.values()))


@ca("Codex PR #541: tờ MỚI gửi lên kèm người giới thiệu tự chọn và % 100 (API): máy bỏ hết, ghi sổ ra 0; giá trị máy chủ gắn cho doc chưa lưu thì giữ; tờ trả hàng để trống")
def _to_moi_khong_tin():
	db = _db()
	with moi_truong(db):
		# Đúng chuỗi Codex mô tả: hook nhận doc mới đã mang sẵn các ô, rồi lưu, rồi ghi sổ.
		gui = Doc(db, gt.DT_HD, __islocal=1, docstatus=0, customer="Khách lẻ", items=MON, discount_amount=0,
			**{gt.O_NGUOI: "lan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 100, gt.O_HH: 999999, gt.O_DOI_BOI: "lan@x"})
		gt.truoc_khi_luu(gui)
		la("ô gửi lên bị bỏ", tuple(gui.get(o) for o in (gt.O_NGUOI, gt.O_LOAI, gt.O_PT, gt.O_HH, gt.O_DOI_BOI)),
			(None, None, None, None, None))
		gui.insert()
		for i, d in enumerate(MON):
			db.bang.setdefault("Sales Invoice Item", {})["%s-%d" % (gui["name"], i)] = dict(d, parent=gui["name"], parenttype=gt.DT_HD)
		gui["docstatus"] = 1
		db.bang[gt.DT_HD][gui["name"]]["docstatus"] = 1
		gt.khi_ghi_so(gui)
		la("ghi sổ: không có hoa hồng", db.bang[gt.DT_HD][gui["name"]].get(gt.O_HH) or 0, 0)
		# Máy chủ gắn trên doc chưa lưu (đường gọi món tại bàn) thì lần lưu đầu giữ đúng giá trị máy.
		moi = Doc(db, gt.DT_HD, __islocal=1, docstatus=0, customer="Khách lẻ")
		gt.gan_cho_hoa_don(moi, "0909123456", "tai_ban")
		moi[gt.O_PT] = 100
		gt.truoc_khi_luu(moi)
		la("giá trị máy chủ giữ, % sửa tay bị trả về", (moi[gt.O_NGUOI], moi[gt.O_PT]), ("ngan@x", 2.0))
		# Sổ tin dùng một lần: doc khác (kể cả lưu lại lần nữa) không ăn theo.
		khac = Doc(db, gt.DT_HD, __islocal=1, **{gt.O_NGUOI: "ngan@x", gt.O_PT: 2})
		gt.truoc_khi_luu(khac)
		la("doc khác không được tin", khac.get(gt.O_NGUOI), None)
		tra = Doc(db, gt.DT_HD, __islocal=1, is_return=1, return_against="SI-X", **{gt.O_NGUOI: "ngan@x", gt.O_PT: 2})
		gt.truoc_khi_luu(tra)
		la("tờ trả hàng để trống", (tra.get(gt.O_NGUOI), tra.get(gt.O_PT)), (None, None))
	la("phép thuần: tin máy chủ thắng tờ gốc", gt.don_o_moi({gt.O_NGUOI: "a@x", gt.O_LOAI: "web", gt.O_PT: 3},
		{gt.O_NGUOI: "b@x", gt.O_PT: 9})[gt.O_NGUOI], "a@x")
	la("phép thuần: không nguồn nào thì rỗng", set(gt.don_o_moi(None).values()), {None})


@ca("v638 quản lý đổi người giới thiệu: thu ngân bị chặn; quản lý đổi được, ghi ai đổi lúc nào, có dòng vết; hoá đơn đã ghi sổ tính lại theo người mới")
def _doi():
	db = _db()
	with moi_truong(db, vai=("Sales User", "Accounts User")):
		_hd(db, "SI-1", docstatus=1, items=MON, **{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2, gt.O_HH: 19280})
		nem("thu ngân", lambda: gt.doi_nguoi("SI-1", "lan@x", "nhầm"), _fr.ValidationError)
		la("không đổi", db.bang[gt.DT_HD]["SI-1"][gt.O_NGUOI], "ngan@x")
	# Codex PR #541 vòng 5: tài khoản CHỈ mang vai thật "VGB - Quản lý cửa hàng".
	with moi_truong(db, vai=("VGB - Quản lý cửa hàng",), toi="ql@x"):
		la("thấy chế độ toàn tiệm, có quyền đổi", (gt.cua_toi()["xem_toan_tiem"], gt.toan_tiem()["doi_duoc"]), (1, 1))
		nem("thiếu lý do", lambda: gt.doi_nguoi("SI-1", "lan@x", ""), _fr.ValidationError)
		nem("tài khoản khoá", lambda: gt.doi_nguoi("SI-1", "khoa@x", "x"), _fr.ValidationError)
		kq = gt.doi_nguoi("SI-1", "lan@x", "Khách báo gõ nhầm số")
		r = db.bang[gt.DT_HD]["SI-1"]
		la("đổi", (kq["ok"], r[gt.O_NGUOI], r[gt.O_DOI_BOI], bool(r[gt.O_DOI_LUC])), (1, "lan@x", "ql@x", True))
		la("tính lại", (kq["hoa_hong"], r[gt.O_HH]), (20000, 20000))
		dung("có dòng vết lý do", any("Khách báo gõ nhầm số" in v["content"] and v["reference_name"] == "SI-1" for v in db.vet))
		gt.doi_nguoi("SI-1", "", "Không phải giới thiệu")
		la("gỡ: hoa hồng 0", (db.bang[gt.DT_HD]["SI-1"][gt.O_NGUOI], db.bang[gt.DT_HD]["SI-1"][gt.O_HH]), (None, 0))
		db.bang[gt.DT_DW] = {"DW-1": {"name": "DW-1", "dien_thoai": "0901000000", gt.O_DW_NGUOI: None}}
		gt.doi_nguoi("DW-1", "ngan@x", "Khách gọi điện báo")
		la("đơn web chưa có hoá đơn: gắn và chốt %", (db.bang[gt.DT_DW]["DW-1"][gt.O_DW_NGUOI], db.bang[gt.DT_DW]["DW-1"][gt.O_DW_PT]), ("ngan@x", 2.0))


def _thang(db):
	"""Dữ liệu một tháng: hai người, đơn ghi sổ, nháp, huỷ, hoàn, đơn web chờ và đơn web đã có hoá đơn."""
	_hd(db, "SI-1", docstatus=1, items=MON, discount_amount=100000, **{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "web", gt.O_PT: 2, gt.O_HH: 18000},
		custom_pancake_display_id="91428")
	_hd(db, "SI-2", docstatus=1, items=[{"item_code": "BANH01", "amount": 500000}], **{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2, gt.O_HH: 10000})
	_hd(db, "SI-3", docstatus=0, items=[{"item_code": "BANH01", "amount": 300000}], **{gt.O_NGUOI: "ngan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2})
	_hd(db, "SI-4", docstatus=2, items=MON, **{gt.O_NGUOI: "lan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2, gt.O_HH: 0})
	_hd(db, "SI-5", docstatus=1, items=[{"item_code": "BANH01", "amount": 1000000}], **{gt.O_NGUOI: "lan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2, gt.O_HH: 20000})
	_hd(db, "SI-6", docstatus=1, items=[{"item_code": "BANH01", "amount": 1000000}], **{gt.O_NGUOI: "lan@x", gt.O_LOAI: "tai_ban", gt.O_PT: 2, gt.O_HH: 0})
	_hd(db, "SI-6R", docstatus=1, is_return=1, return_against="SI-6")
	_hd(db, "SI-OLD", docstatus=1, posting_date="2026-10-30", items=MON, **{gt.O_NGUOI: "ngan@x", gt.O_PT: 2, gt.O_HH: 99999})
	db.bang[gt.DT_DW] = {
		"DW-1": {"name": "DW-1", "trang_thai": "Da nhan", "tien_banh": 700000, "snapshot": json.dumps({"uu_dai": {"giam": 200000}}),
			"ngay_nhan": "2026-11-20 09:00:00", gt.O_DW_NGUOI: "ngan@x", gt.O_DW_PT: 2},
		"DW-2": {"name": "DW-2", "trang_thai": "Da nhan", "tien_banh": 900000, "snapshot": "{}", "pancake_display_id": "91428",
			"ngay_nhan": "2026-11-03 09:00:00", gt.O_DW_NGUOI: "ngan@x", gt.O_DW_PT: 2},
		"DW-3": {"name": "DW-3", "trang_thai": "Da huy", "tien_banh": 400000, "snapshot": "{}",
			"ngay_nhan": "2026-11-10 09:00:00", gt.O_DW_NGUOI: "lan@x", gt.O_DW_PT: 2},
	}


@ca("v638 màn của tôi: đúng đơn của mình trong tháng (ghi sổ, nháp tạm tính, đơn web chờ, không lặp đơn web đã có hoá đơn); toàn tiệm: bảng nhân viên đúng số, thu ngân bị chặn")
def _man():
	db = _db()
	_thang(db)
	with moi_truong(db, toi="ngan@x"), patch.object(_fr.utils, "nowdate", lambda: "2026-11-15"), \
			patch.object(gt, "nowdate", lambda: "2026-11-15"):
		kq = gt.cua_toi("2026-11")
		la("đơn của tôi", sorted((r["ma"], r["tt"], r["hoa_hong"]) for r in kq["ds"]),
			[("DW-1", "cho", 10000), ("SI-1", "ghi_so", 18000), ("SI-2", "ghi_so", 10000), ("SI-3", "cho", 6000)])
		la("tạm tính tháng", (kq["tong"]["ghi_so"]["hoa_hong"], kq["tong"]["cho"]["hoa_hong"]), (28000, 16000))
		la("không xem toàn tiệm", kq["xem_toan_tiem"], 0)
		nem("toàn tiệm bị chặn", lambda: gt.toan_tiem("2026-11"), _fr.ValidationError)
	with moi_truong(db, vai=("Giám đốc",), toi="gd@x"), patch.object(gt, "nowdate", lambda: "2026-11-15"):
		kq = gt.toan_tiem("2026-11")
		la("bảng", [(o["nguoi"], o["so_don"], o["tien_hang"], o["hoa_hong"], o["so_cho"]) for o in kq["bang"]],
			[("ngan@x", 2, 1400000, 28000, 2), ("lan@x", 1, 1000000, 20000, 0)])
		la("trạng thái các đơn của Lan", sorted((r["ma"], r["tt"]) for r in kq["ds"] if r["nguoi"] == "lan@x"),
			[("DW-3", "huy"), ("SI-4", "huy"), ("SI-5", "ghi_so"), ("SI-6", "hoan")])
		ten, cot, dong = gt.xuat_ds("2026-11")
		la("Xuất Excel đủ dòng của tháng", len(dong), len(kq["ds"]))
		dung("cột có nhân viên và hoa hồng", {"ten_nguoi", "hoa_hong", "nhan_tt"} <= {c["k"] for c in cot})
	from vagabond.khung import cong_cu_ds
	la("đăng ký xuất Excel", cong_cu_ds.MAN_XUAT["hoa_hong_gioi_thieu"], "vagabond.gioi_thieu.xuat_ds")


@ca("v638 Đưa vào phiếu KPI tháng: bấm hai lần không cộng hai lần; lập phiếu cho người chưa có; phiếu đã chốt để nguyên; thu ngân bị chặn")
def _kpi():
	from vagabond import kpi
	db = _db()
	_thang(db)
	db.bang[gt.DT_KPI] = {
		"KPI-L": {"name": "KPI-L", "ky": "2026-11", "nguoi": "lan@x", "trang_thai": "Cho quan ly", "dong_bang": 0, gt.O_KPI_HH: 0,
			"hoa_hong": 1500000},
		"KPI-A": {"name": "KPI-A", "ky": "2026-11", "nguoi": "a@x", "trang_thai": "Da duyet", "dong_bang": 1, gt.O_KPI_HH: 5000},
	}
	with moi_truong(db, vai=("Sales User",)):
		nem("thu ngân", lambda: gt.dua_vao_kpi("2026-11"), _fr.ValidationError)
	with moi_truong(db, vai=("Giám đốc",), toi="gd@x"), patch.object(gt, "nowdate", lambda: "2026-11-15"), \
			patch.object(kpi, "khoang_ky", lambda ky: (ky, datetime.date(2026, 11, 1), datetime.date(2026, 11, 30))):
		k1 = gt.dua_vao_kpi("2026-11")
		la("lần một", ([x["nguoi"] for x in k1["tao"]], [(x["nguoi"], x["so"]) for x in k1["cap_nhat"]], [x["nguoi"] for x in k1["da_chot"]]),
			(["ngan@x"], [("lan@x", 20000)], ["a@x"]))
		moi = next(r for r in db.bang[gt.DT_KPI].values() if r["nguoi"] == "ngan@x")
		la("phiếu mới: chỉ khoản giới thiệu, chờ quản lý", (moi[gt.O_KPI_HH], moi["hoa_hong"], moi["trang_thai"], moi["bo"]),
			(28000, 0, "Cho quan ly", "gioi_thieu"))
		la("phiếu Lan: hoa hồng doanh số không đụng", (db.bang[gt.DT_KPI]["KPI-L"][gt.O_KPI_HH], db.bang[gt.DT_KPI]["KPI-L"]["hoa_hong"]), (20000, 1500000))
		so_phieu = len(db.bang[gt.DT_KPI])
		k2 = gt.dua_vao_kpi("2026-11")
		la("lần hai: không lập thêm, không đổi số", (len(db.bang[gt.DT_KPI]), k2["tao"], k2["cap_nhat"], sorted(x["nguoi"] for x in k2["giu"])),
			(so_phieu, [], [], ["lan@x", "ngan@x"]))
		la("số trên phiếu sau hai lần", (moi[gt.O_KPI_HH], db.bang[gt.DT_KPI]["KPI-L"][gt.O_KPI_HH], db.bang[gt.DT_KPI]["KPI-A"][gt.O_KPI_HH]),
			(28000, 20000, 5000))
		la("tổng", (k1["tong"], k2["tong"]), (48000, 48000))


@ca("v638 phiếu KPI đẩy chi: hoa hồng giới thiệu là một dòng riêng trong đề nghị chi; phiếu chỉ có khoản giới thiệu vẫn đẩy được")
def _day_chi():
	from vagabond import de_nghi_chi, kpi
	gui = []
	for hh, gtt, can in ((1500000, 20000, [1500000, 20000]), (0, 28000, [28000]), (900000, 0, [900000])):
		db = _db()
		db.bang[kpi.DT] = {"P": {"name": "P", "ky": "2026-11", "nguoi": "ngan@x", "ten_nguoi": "Ngân", "trang_thai": kpi.TT_DUYET,
			"hoa_hong": hh, gt.O_KPI_HH: gtt, "diem_tong": 90, "xep_loai": "Tốt"}}
		with moi_truong(db, vai=("Giám đốc",), toi="gd@x"), patch.object(kpi, "duoc_bam", lambda d: (True, "")), \
				patch.object(de_nghi_chi, "tao", lambda du_lieu, gui_luon=0: gui.append(du_lieu) or {"ma": "DNC-1"}):
			kq = kpi.day_chi("P")
		la("các dòng chi", [k["so_tien"] for k in gui[-1]["cac_khoan"]], can)
		la("phiếu sang đã đẩy chi", (kq["phieu_chi"], db.bang[kpi.DT]["P"]["trang_thai"]), ("DNC-1", kpi.TT_DA_CHI))
	dung("dòng giới thiệu có tên rõ", any("Hoa hồng giới thiệu" in k["noi_dung"] for k in gui[0]["cac_khoan"]))


@ca("v638 ô mới: Cài đặt mục Bán hàng (công tắc, hai % mặc định 2) đủ insert_after, mô tả tiếng Việt; đăng ký trong truong_tu_them; không em dash")
def _o_moi():
	for dt, ds in gt.TRUONG_MOI.items():
		for o in ds:
			dung(dt + " " + o["fieldname"] + " có insert_after", bool(o.get("insert_after")))
	cd = {o["fieldname"]: o for o in gt.TRUONG_MOI["Vagabond Settings"]}
	la("ba ô Cài đặt", (cd[gt.O_BAT]["fieldtype"], cd[gt.O_PT_WEB]["fieldtype"], cd[gt.O_PT_TAI_BAN]["fieldtype"],
		cd[gt.O_PT_WEB]["default"], cd[gt.O_PT_TAI_BAN]["default"]), ("Check", "Percent", "Percent", "2", "2"))
	vs = json.loads((GOC / "vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json").read_text())
	tab = None
	for f in vs["fields"]:
		if f["fieldtype"] == "Tab Break":
			tab = f["fieldname"]
		if f["fieldname"] == cd["vgb_sec_gioi_thieu"]["insert_after"]:
			break
	la("mục mới nằm trong tab Bán hàng & thanh toán", tab, "tab_ban_hang")
	dung("mỗi ô Cài đặt có mô tả", all(o.get("description") for o in cd.values() if o["fieldtype"] not in ("Column Break",)))
	s = (GOC / "vagabond/truong_tu_them.py").read_text()
	dung("đăng ký dựng ô và gieo mặc định", "_dung_nhom(gioi_thieu.TRUONG_MOI" in s and "gioi_thieu.gieo_mac_dinh()" in s)
	for tep in ("vagabond/gioi_thieu.py", "vagabond/public/js/bep/67-hoa-hong-gioi-thieu.js"):
		dung(tep + " không em dash, en dash", not re.search("[\u2013\u2014]", (GOC / tep).read_text()))
		dung(tep + " không ô select", "<select" not in (GOC / tep).read_text())


@ca("v638 màn app Hoa hồng giới thiệu nạp thật trong node: của tôi và toàn tiệm hiện đúng số, đưa vào KPI, đổi người, xuất Excel (node thật)")
def _node():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/hoa_hong_gioi_thieu_638.js"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-2500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= 5)
	s = (GOC / "vagabond/public/js/bep/02-trang-chu.js").read_text()
	dung("có ô trên trang chủ và nhánh mở màn", "'HHGT') + '</div>'" in s and "if (k === 'HHGT') return go(scrHhgt);" in s)
	from vagabond import duong_app
	dung("có đường dẫn riêng", any(m[0] == "HHGT" for m in duong_app.MAN))
