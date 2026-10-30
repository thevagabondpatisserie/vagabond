# -*- coding: utf-8 -*-
"""v622: phân hệ Tuyển dụng (anh Việt 30/10/2026).

Sáu điều anh chốt và ca nào giữ điều đó:
  1. Làm trong app, không HRMS: doctype riêng, cửa ngõ riêng (_cua_ngo_quyen).
  2. Mọi quản lý bộ phận xem và chốt: danh sách vai hai bên trùng nhau, mọi
     cửa ngõ nội bộ chặn người không có vai (_quyen).
  4. Ứng viên bắt buộc tích đồng ý lưu hồ sơ (_dong_y, _ung_tuyen).
  5. Làm thử có trả công (_cong_thu).
  6. Bật tắt vị trí trên app là web đổi theo (_web_dong_bo, _bien_tap_chan).
Cộng thêm: hồ sơ quá 24 giờ chưa gọi được nhắc (_nhac), hết hạn lưu thì xoá
thông tin cá nhân của người không được nhận (_xoa_het_han).

Các ca chạy hàm THẬT trên lớp Frappe giả có một "site" trong bộ nhớ; không
gọi thêm hàm nội bộ nào ngoài chuỗi máy chạy (điều 15).
"""

import copy
import datetime as dt
import json
import os
import re
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import tuyen_dung as td  # noqa: E402
from vagabond import noi_dung_web as nw  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HOM_NAY = "2026-08-15"
BAY_GIO = dt.datetime(2026, 8, 15, 9, 0, 0)


def _doc_tep(*p):
	with open(os.path.join(GOI, *p), encoding="utf-8") as f:
		return f.read()


def _vt(**k):
	v = {"name": "VTT-0001", "tieu_de": "Thu ngân ca tối", "bo_phan": "Thu ngân - TV", "ten_bo_phan": "Thu ngân",
		"noi_lam": "The Vagabond District 1", "hinh_thuc": "Bán thời gian", "so_can": 2, "dang_tuyen": 1,
		"ket_thuc": "", "noi_dung": "Tính tiền, đóng gói bánh.", "yeu_cau": "Nhanh nhẹn\nLàm được ca tối",
		"muc_luong": "25.000 đ/giờ", "tieu_chi": "", "cong_lam_thu": 100000, "gio_lam_thu": 4}
	v.update(k)
	return v


def _hs(**k):
	h = {"vi_tri": "VTT-0001", "ho_ten": "Nguyễn Văn An", "sdt": "0909 123 456", "email": "",
		"ca_ranh": ["Tối", "Sáng", "Lạ"], "dong_y": 1}
	h.update(k)
	return h


# ------------------------------------------------------------ site giả

class _Loi(Exception):
	pass


class _Doc(dict):
	"""Bản ghi giả: thuộc tính là khoá, có insert, save, append như Document."""

	def __init__(self, site, d):
		super().__init__(d)
		object.__setattr__(self, "_site", site)
		object.__setattr__(self, "flags", types.SimpleNamespace())

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def as_dict(self):
		return dict(self)

	def update(self, d=None, **k):
		dict.update(self, d or {}, **k)

	def append(self, bang, dong):
		self.setdefault(bang, []).append(dict(dong))

	def insert(self, ignore_permissions=False):
		s = self._site
		dt_ = self["doctype"]
		if dt_ == td.UV and self.get("bam_lan_gui"):
			if any(r.get("bam_lan_gui") == self["bam_lan_gui"] for r in s.bang(dt_)):
				raise _fr.DuplicateEntryError("trùng")
		if not self.get("name"):
			s.dem += 1
			self["name"] = ("UV-26-08-%04d" if dt_ == td.UV else "VTT-%04d") % s.dem
		if dt_ == td.UV and self.get("vi_tri"):
			self["ten_vi_tri"] = (s.lay(td.VT, self["vi_tri"]) or {}).get("tieu_de")
		self.setdefault("creation", BAY_GIO)
		s.bang(dt_).append(self)
		s.ghi.append(("insert", dt_, self["name"]))
		if dt_ == td.UV:
			s.hook_moi.append(self["name"])
		return self

	def save(self, ignore_permissions=False):
		self._site.ghi.append(("save", self["doctype"], self["name"]))
		return self


class _Site:
	def __init__(self, vt=None, uv=None):
		self.du = {td.VT: [], td.UV: []}
		self.dem = 0
		self.ghi = []
		self.hook_moi = []
		self.set_value = []
		for v in vt or []:
			self.du[td.VT].append(_Doc(self, dict(v, doctype=td.VT)))
		for u in uv or []:
			self.du[td.UV].append(_Doc(self, dict(u, doctype=td.UV)))

	def bang(self, d):
		return self.du.setdefault(d, [])

	def lay(self, d, ten):
		for r in self.bang(d):
			if r.get("name") == ten:
				return r
		return None

	def get_doc(self, a, b=None, **k):
		if isinstance(a, dict):
			return _Doc(self, dict(a))
		r = self.lay(a, b)
		if r is None:
			raise _Loi("%s %s không có" % (a, b))
		return r

	def get_value(self, d, loc, truong=None, as_dict=False, **k):
		if isinstance(loc, dict):
			ds = [r for r in self.bang(d) if all(r.get(x) == y for x, y in loc.items())]
		else:
			ds = [r for r in self.bang(d) if r.get("name") == loc]
		if not ds:
			return None
		r = ds[0]
		if isinstance(truong, (list, tuple)):
			o = types.SimpleNamespace(**{t: r.get(t) for t in truong}) if as_dict else [r.get(t) for t in truong]
			if as_dict:
				o = _fr._dict({t: r.get(t) for t in truong})
			return o
		return r.get(truong)

	def get_all(self, d, filters=None, fields=None, **k):
		ra = []
		for r in self.bang(d):
			ok = True
			for x, y in (filters or {}).items():
				v = r.get(x)
				if isinstance(y, list):
					op, gt = y
					if op == "<=" and not (v is not None and v <= gt):
						ok = False
					if op == "<" and not (v is not None and str(v) < str(gt)):
						ok = False
					if op == "!=" and v == gt:
						ok = False
					if op == "in" and v not in gt:
						ok = False
				elif (v or 0) != y and v != y:
					ok = False
			if ok:
				ra.append(_fr._dict({f: r.get(f) for f in (fields or r.keys())}))
		return ra

	def vao(self, vai=("System Manager",)):
		"""Các bản vá để tuyen_dung chạy trên site này."""
		db = types.SimpleNamespace(
			get_value=self.get_value, exists=lambda d, n=None: bool(n) if d == "Department" else bool(self.lay(d, n)),
			savepoint=lambda *a, **k: None, rollback=lambda *a, **k: None, count=lambda d, f=None: len(self.get_all(d, f)),
			set_value=lambda d, n, v, **k: self.set_value.append((d, n, v)), sql=lambda *a, **k: self.ghi.append(("sql",) + a),
			delete=lambda d, f=None: self.ghi.append(("xoa_lich_su", d, f)),
		)
		return [
			um.patch.object(td.frappe, "db", db),
			um.patch.object(td.frappe, "get_doc", self.get_doc),
			um.patch.object(td.frappe, "get_all", self.get_all),
			um.patch.object(td.frappe, "get_roles", lambda *a, **k: list(vai)),
			um.patch.object(td.frappe, "generate_hash", lambda length=10: "h" * length, create=True),
			um.patch.object(td.frappe, "local", types.SimpleNamespace(message_log=[], form_dict={})),
			um.patch.object(td.frappe, "session", types.SimpleNamespace(user="de@vagabond")),
			um.patch.object(td.frappe.utils, "get_fullname", lambda u: "Lê Hoàng Dễ", create=True),
			um.patch.object(td, "_ten_bo_phan", lambda bp: str(bp or "").replace(" - TV", "")),
			um.patch.object(td, "_noi_lam_mau", lambda: ["The Vagabond District 1", "Xưởng sản xuất Tân Bình"]),
		]


if not hasattr(_fr, "DuplicateEntryError"):
	class DuplicateEntryError(Exception):
		pass
	_fr.DuplicateEntryError = DuplicateEntryError
if not hasattr(_fr, "PermissionError"):
	class PermissionError_(Exception):
		pass
	_fr.PermissionError = PermissionError_


def _chay(site, ham, vai=("System Manager",)):
	ps = site.vao(vai)
	for p in ps:
		p.start()
	try:
		return ham()
	finally:
		for p in reversed(ps):
			p.stop()


def _loi(ham):
	try:
		ham()
	except Exception as e:
		return str(e)
	return ""


# ------------------------------------------------------------ phép thuần

@ca("v622 form ứng tuyển: chuẩn hoá đúng, số điện thoại, ca rảnh theo thứ tự, nguồn lạ về mặc định")
def _chuan():
	d = td.chuan_ho_so(_hs(sdt="+84 909.123.456", nguon="Lạ", lien_ket_cv="https://drive.google.com/x"), ["VTT-0001"])
	la("số điện thoại về dạng 0xxxxxxxxx", d["sdt"], "0909123456")
	la("ca rảnh theo đúng thứ tự, bỏ giá trị lạ", d["ca_ranh"], "Sáng, Tối")
	la("nguồn lạ về Web Vagabond", d["nguon"], "Web Vagabond")
	la("CV https giữ nguyên", d["lien_ket_cv"], "https://drive.google.com/x")
	la("đồng ý ghi 1", d["dong_y"], 1)
	for sai, cau in (
		(_hs(vi_tri="VTT-0009"), "ngừng nhận hồ sơ"),
		(_hs(sdt="0123"), "số điện thoại di động"),
		(_hs(ho_ten=" "), "họ tên"),
		(_hs(email="an@"), "email"),
		(_hs(lien_ket_cv="javascript:alert(1)"), "https://"),
		(_hs(kinh_nghiem="x" * 1501), "1.500"),
	):
		dung("chặn: %s" % cau, cau in _loi(lambda: td.chuan_ho_so(sai, ["VTT-0001"])))
	dung("chuỗi quá dài báo được", "quá dài" in _loi(lambda: td.chuan_ho_so("{" + "x" * 9000, ["VTT-0001"])))
	dung("không có dấu gạch dài trong câu báo", not re.search("[–—]", _loi(lambda: td.chuan_ho_so(_hs(sdt="1"), ["VTT-0001"]))))


@ca("v622 bắt buộc tích đồng ý lưu hồ sơ (anh Việt 30/10/2026)")
def _dong_y():
	for gt in (0, "", None, "0", False, "false"):
		dung("chưa tích (%r) thì chặn" % (gt,), "Tích ô đồng ý" in _loi(lambda: td.chuan_ho_so(_hs(dong_y=gt), ["VTT-0001"])))
	dung("câu đồng ý nói rõ mục đích và hạn lưu", "tuyển dụng" in td.CAU_DONG_Y and "%d tháng" % td.THANG_LUU in td.CAU_DONG_Y)
	la("hạn lưu cộng đúng 12 tháng", td.han_luu(dt.datetime(2026, 10, 30, 8, 0)), dt.date(2027, 10, 30))
	la("ngày 31 lùi về cuối tháng ngắn", td.han_luu(dt.date(2026, 1, 31), 1), dt.date(2026, 2, 28))


@ca("v622 thẻ web: tắt hoặc qua hạn thì không hiện; nút mở form /ung-tuyen; lương lên dòng đầu")
def _the_web():
	la("đang tuyển thì có thẻ", bool(td.the_web(_vt(), HOM_NAY)), True)
	la("tắt thì không hiện", td.the_web(_vt(dang_tuyen=0), HOM_NAY), None)
	la("qua hạn thì không hiện", td.the_web(_vt(ket_thuc="2026-08-14"), HOM_NAY), None)
	la("đúng hạn hôm nay vẫn hiện", bool(td.the_web(_vt(ket_thuc=HOM_NAY), HOM_NAY)), True)
	t = td.the_web(_vt(), HOM_NAY)
	la("liên kết form", t["lien_ket"], "/ung-tuyen?vt=VTT-0001")
	la("loại khối tuyển dụng, nguồn erp", (t["loai"], t["nguon"], t["hien"]), ("tuyen_dung", "erp", True))
	la("lương lên đầu danh sách", t["yeu_cau"].split("\n"), ["Mức lương: 25.000 đ/giờ", "Nhanh nhẹn", "Làm được ca tối"])
	la("không còn email (không mở thư nữa)", t["email"], "")
	la("trạng thái cho biên tập", [td.trang_thai_web(_vt(), HOM_NAY), td.trang_thai_web(_vt(dang_tuyen=0), HOM_NAY),
		td.trang_thai_web(_vt(ket_thuc="2026-01-01"), HOM_NAY)],
		["Khách đang thấy", "Đang tắt trên app, khách không thấy", "Đã hết hạn nhận hồ sơ, khách không thấy"])


@ca("v622 web: bật tắt trên app là trang khách đổi theo, khối tuyển dụng gõ tay cũ không ra web")
def _web_dong_bo():
	cu = {"id": "cu-1", "loai": "tuyen_dung", "hien": True, "tieu_de": "Gõ tay cũ", "email": "a@b.vn"}
	uu = {"id": "uu-1", "loai": "uu_dai", "hien": True, "tieu_de": "Ưu đãi"}
	k1 = {"id": "k1", "loai": "cau_chuyen"}
	nd = {"khoi": [k1, cu, uu], "nhan": {}}
	for dang, mong in ((1, ["k1", "erp-td-VTT-0001", "erp-uu"]), (0, ["k1", "erp-uu"])):
		site = _Site(vt=[_vt(dang_tuyen=dang)])
		with um.patch.object(nw, "_ban_cong_khai", lambda khoa=False: copy.deepcopy(nd)), \
				um.patch.object(nw, "_the_uu_dai_erp", lambda: [{"id": "erp-uu", "loai": "uu_dai"}]), \
				um.patch.object(nw, "nhan_day_du", lambda r: {}), um.patch.object(nw, "thong_tin_day_du", lambda r: {}), \
				um.patch.object(nw, "diem_nhan", lambda r: {}), um.patch.object(nw, "_dem_ve", lambda r: {}), \
				um.patch.dict(sys.modules, {"vagabond.don_web": types.SimpleNamespace(lien_he=lambda: {})}):
			ra = _chay(site, nw.cong_khai)
		la("đang tuyển=%d: trang khách có đúng các khối" % dang, [k["id"] for k in ra["khoi"]], mong)
	la("thay khối giữ chỗ khối cũ", [k["id"] for k in nw.thay_khoi_erp([k1, cu, uu], [{"id": "x"}], "tuyen_dung")], ["k1", "x", "uu-1"])
	la("ưu đãi vẫn qua hàm cũ", [k["id"] for k in nw.thay_uu_dai_erp([k1, cu, uu], [{"id": "y"}])], ["k1", "cu-1", "y"])
	la("lưu cả bản giữ khối tuyển dụng đã lưu", [k["id"] for k in nw.giu_khoi_da_luu([k1], [k1, cu], "tuyen_dung")], ["k1", "cu-1"])


@ca("v622 trình biên tập web: không lưu được vị trí tuyển dụng gõ tay, lưu cả bản không đổi được khối này")
def _bien_tap_chan():
	ps = [um.patch.object(nw, "kiem_quyen", lambda: None)]
	for p in ps:
		p.start()
	try:
		loi = _loi(lambda: nw.luu_muc(json.dumps({"id": "x", "loai": "tuyen_dung", "tieu_de": "Phụ bếp"})))
	finally:
		for p in ps:
			p.stop()
	dung("luu_muc chặn tuyển dụng, chỉ đường tới app", "Nhân sự, Tuyển dụng" in loi)
	js = _doc_tep("public", "web_order", "bien-tap-moi.js")
	dung("thẻ Tuyển dụng của trình biên tập chỉ xem, đọc từ máy chủ", "if (loai === 'tuyen_dung') return dsTuyenDungErp();" in js
		and "B.tuyen_dung_erp" in js)


@ca("v622 chuyển trạng thái: đã nhận việc không quay lại; hẹn phải có giờ; dừng phải có lý do")
def _chuyen():
	la("mới -> đã liên hệ được", td.kiem_chuyen(td.MOI, td.LIEN_HE), "")
	la("lùi về đã liên hệ được", td.kiem_chuyen(td.HEN_PV, td.LIEN_HE), "")
	dung("đã nhận việc không quay lại", "đã nhận việc" in td.kiem_chuyen(td.NHAN_VIEC, td.LIEN_HE))
	dung("hẹn phỏng vấn thiếu giờ", "phỏng vấn" in td.kiem_chuyen(td.LIEN_HE, td.HEN_PV))
	dung("làm thử thiếu giờ", "làm thử" in td.kiem_chuyen(td.LIEN_HE, td.LAM_THU))
	la("hẹn có giờ thì được", td.kiem_chuyen(td.LIEN_HE, td.HEN_PV, "2026-08-16 14:00"), "")
	dung("dừng thiếu lý do", "lý do" in td.kiem_chuyen(td.MOI, td.DUNG, ly_do=" "))
	dung("trạng thái lạ", "danh sách" in td.kiem_chuyen(td.MOI, "Xoá"))


@ca("v622 phiếu chấm: đủ tiêu chí của vị trí, điểm 1 đến 4, kết luận trong danh sách")
def _phieu():
	tc = td.tieu_chi_cua({"tieu_chi": "Thái độ\n- Nhanh nhẹn\n\nThái độ"})
	la("tiêu chí theo dòng, bỏ trùng và gạch đầu dòng", tc, ["Thái độ", "Nhanh nhẹn"])
	la("trống thì dùng bộ mặc định", td.tieu_chi_cua({}), list(td.TIEU_CHI_MAC_DINH))
	la("chuẩn hoá đủ", td.chuan_phieu_cham(tc, json.dumps({"Thái độ": 4, "Nhanh nhẹn": "3"}), "Nên nhận", "Phỏng vấn"),
		{"Thái độ": 4, "Nhanh nhẹn": 3})
	dung("thiếu một tiêu chí", "Nhanh nhẹn" in _loi(lambda: td.chuan_phieu_cham(tc, {"Thái độ": 4}, "Nên nhận", "Phỏng vấn")))
	dung("điểm 5 bị chặn", "1 đến 4" in _loi(lambda: td.chuan_phieu_cham(tc, {"Thái độ": 5, "Nhanh nhẹn": 3}, "Nên nhận", "Phỏng vấn")))
	dung("kết luận lạ", "Kết luận" not in td.KET_LUAN and "kết luận" in _loi(lambda: td.chuan_phieu_cham(tc, {"Thái độ": 4, "Nhanh nhẹn": 3}, "Ok", "Phỏng vấn")))
	la("điểm trung bình", td.diem_tb({"a": 4, "b": 3, "c": "x"}), 3.5)


@ca("v622 vị trí: tên, hình thức, hạn, số; tiêu chí trống thì để máy dùng mặc định")
def _vi_tri():
	d = td.chuan_vi_tri({"tieu_de": "Phụ bếp Pastry", "hinh_thuc": "Toàn thời gian", "cong_lam_thu": "120.000",
		"gio_lam_thu": "4,5", "dang_tuyen": True, "ket_thuc": "2026-09-30"})
	la("tiền công bỏ dấu chấm nghìn", d["cong_lam_thu"], 120000)
	la("giờ dấu phẩy", d["gio_lam_thu"], 4.5)
	la("đang tuyển", d["dang_tuyen"], 1)
	la("tiêu chí trống", d["tieu_chi"], "")
	for sai, cau in (({"tieu_de": "ab"}, "tên vị trí"), ({"tieu_de": "Phụ bếp", "hinh_thuc": "Part"}, "hình thức"),
		({"tieu_de": "Phụ bếp", "ket_thuc": "30/09"}, "Hạn"), ({"tieu_de": "Phụ bếp", "so_can": 0}, "1 đến 50")):
		dung("chặn %s" % cau, cau in _loi(lambda: td.chuan_vi_tri(sai)))


@ca("v622 con số đầu màn: chưa gọi, quá 24 giờ, hẹn hôm nay, công chưa trả")
def _tom_tat():
	rows = [
		{"trang_thai": td.MOI, "creation": "2026-08-14 08:00:00"},
		{"trang_thai": td.MOI, "creation": "2026-08-15 08:00:00"},
		{"trang_thai": td.HEN_PV, "lich_hen": "2026-08-15 14:00:00"},
		{"trang_thai": td.LAM_THU, "lich_hen": "2026-08-16 08:00:00", "tien_cong_thu": 100000, "da_tra_cong": 0},
		{"trang_thai": td.DE_NGHI, "tien_cong_thu": 100000, "da_tra_cong": 1},
	]
	la("tóm tắt", td.tom_tat(rows, HOM_NAY, BAY_GIO), {"moi": 2, "qua_han": 1, "hen_hom_nay": 1, "cong_chua_tra": 1})
	la("đúng 24 giờ là quá hạn", td.qua_han_goi({"trang_thai": td.MOI, "creation": "2026-08-14 09:00:00"}, BAY_GIO), True)
	la("23 giờ chưa", td.qua_han_goi({"trang_thai": td.MOI, "creation": "2026-08-14 10:00:00"}, BAY_GIO), False)
	la("đã liên hệ thì không tính", td.qua_han_goi({"trang_thai": td.LIEN_HE, "creation": "2026-08-01 10:00:00"}, BAY_GIO), False)


# ------------------------------------------------------------ cửa ngõ thật

@ca("v622 nộp hồ sơ: tạo hồ sơ Mới nhận, có hạn lưu; gửi lại cùng mã không tạo hồ sơ thứ hai; ô bẫy im lặng")
def _ung_tuyen():
	site = _Site(vt=[_vt(), _vt(name="VTT-0002", dang_tuyen=0)])
	ma = "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
	kq = _chay(site, lambda: td.ung_tuyen(json.dumps(_hs()), ma))
	hs = site.bang(td.UV)
	la("một hồ sơ", len(hs), 1)
	la("trạng thái, đồng ý, hạn lưu", (hs[0]["trang_thai"], hs[0]["dong_y"], hs[0]["han_luu"]), (td.MOI, 1, "2027-08-15"))
	la("mã trả về là tên hồ sơ", kq["ma"], hs[0]["name"])
	la("gửi lại cùng mã, cùng nội dung: trả mã cũ", _chay(site, lambda: td.ung_tuyen(json.dumps(_hs()), ma))["ma"], hs[0]["name"])
	la("vẫn một hồ sơ", len(site.bang(td.UV)), 1)
	dung("cùng mã khác nội dung: báo", "đã được nhận" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(_hs(ho_ten="Người khác")), ma))))
	ma2 = "2b4e28ba-2fa1-11d2-883f-0016d3cca427"
	dung("vị trí đang tắt: không nhận", "ngừng nhận" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(_hs(vi_tri="VTT-0002")), ma2))))
	dung("chưa tích đồng ý: không nhận", "đồng ý" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(_hs(dong_y=0)), ma2))))
	la("ô bẫy có chữ: trả OK nhưng không ghi", _chay(site, lambda: td.ung_tuyen(json.dumps(_hs(web="spam")), ma2)), {"ok": 1, "ma": "OK"})
	la("vẫn một hồ sơ sau ba lần bị chặn", len(site.bang(td.UV)), 1)
	dung("mã lần gửi sai dạng", "Tải lại trang" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(_hs()), "abc"))))
	m = _doc_tep("tuyen_dung.py")
	dung("cửa nộp có giới hạn tần suất", re.search(r"@frappe\.whitelist\(methods=\[\"POST\"\], allow_guest=True\)\n@rate_limit\(limit=5, seconds=600\)\ndef ung_tuyen\(", m))


@ca("v622 quyền: mọi cửa ngõ nội bộ chặn người không phải quản lý bộ phận; hai bên cùng một danh sách vai")
def _quyen():
	site = _Site(vt=[_vt()], uv=[dict(_hs(), name="UV-1", sdt="0909123456", trang_thai=td.MOI, da_an_danh=0)])
	goi = [lambda: td.tong_quan(), lambda: td.luu_vi_tri(json.dumps({"tieu_de": "Phụ bếp"})),
		lambda: td.bat_tat_vi_tri("VTT-0001", 0), lambda: td.them_ho_so(json.dumps(_hs())),
		lambda: td.cap_nhat("UV-1", td.LIEN_HE), lambda: td.cham("UV-1", "Phỏng vấn", "{}", "Nên nhận"),
		lambda: td.ghi_cong_thu("UV-1", 4, 100000), lambda: td.ghi_lien_he("UV-1", "Gọi", "Nghe máy")]
	for i, g in enumerate(goi):
		dung("cửa %d chặn nhân viên quầy" % i, "chỉ mở cho quản lý" in _loi(lambda: _chay(site, g, vai=("Sales User",))))
	la("đếm trên ô trang chủ trả 0 cho người không có quyền", _chay(site, td.dem_cho_goi, vai=("Sales User",)), {"so": 0})
	la("không ghi gì khi bị chặn", [x for x in site.ghi if x[0] != "sql"], [])
	js = _doc_tep("public", "js", "bep", "60-tuyen-dung.js")
	ds_js = re.search(r"var QUYEN_TUYENDUNG = \[([^\]]*)\]", js).group(1)
	la("danh sách vai app trùng máy chủ", re.findall(r"'([^']+)'", ds_js), list(td.QUYEN_TUYEN_DUNG))
	from vagabond.vai_cua_hang import BANG_VAI
	la("vai VGB - Tuyển dụng được dựng sau migrate", [m["vai"] for m in BANG_VAI if m["vai"] == td.VAI_TUYEN_DUNG], [td.VAI_TUYEN_DUNG])
	for ten in ("vagabond_vi_tri_tuyen", "vagabond_ung_vien"):
		j = json.loads(_doc_tep("vagabond", "doctype", ten, ten + ".json"))
		vai_json = {p["role"] for p in j["permissions"]}
		la("%s: quyền Desk nằm trong danh sách vai tuyển dụng" % ten, sorted(vai_json - set(td.QUYEN_TUYEN_DUNG)), [])


@ca("v622 cập nhật: liên hệ lần đầu được ghi, hẹn lưu đúng giờ, dừng có lý do, rời Dừng thì bỏ lý do")
def _cap_nhat():
	uv = dict(_hs(), name="UV-1", sdt="0909123456", trang_thai=td.MOI, da_an_danh=0, nhat_ky="")
	site = _Site(vt=[_vt()], uv=[uv])
	_chay(site, lambda: td.cap_nhat("UV-1", td.HEN_PV, lich_hen="2026-08-16T14:30"))
	r = site.lay(td.UV, "UV-1")
	la("hẹn lưu đủ giây", r["lich_hen"], "2026-08-16 14:30:00")
	la("liên hệ lần đầu ghi lúc chuyển khỏi Mới nhận", r["lien_he_luc"], BAY_GIO)
	dung("nhật ký có người và giờ hẹn", "Lê Hoàng Dễ" in r["nhat_ky"] and "14:30 16/08" in r["nhat_ky"])
	dung("giờ hẹn sai dạng báo rõ", "không hợp lệ" in _loi(lambda: _chay(site, lambda: td.cap_nhat("UV-1", td.HEN_PV, lich_hen="16/08 14h"))))
	_chay(site, lambda: td.cap_nhat("UV-1", td.DUNG, ly_do="Ứng viên rút"))
	la("lý do dừng", r["ly_do_dung"], "Ứng viên rút")
	_chay(site, lambda: td.cap_nhat("UV-1", td.LIEN_HE))
	la("rời Dừng thì bỏ lý do", r["ly_do_dung"], "")
	la("liên hệ lần đầu không bị ghi đè", r["lien_he_luc"], BAY_GIO)


@ca("v622 chấm: thêm một dòng theo tiêu chí của vị trí, không dựng lại bảng; nhận xét giữ")
def _cham():
	uv = dict(_hs(), name="UV-1", sdt="0909123456", trang_thai=td.HEN_PV, da_an_danh=0, danh_gia=[{"vong": "Phỏng vấn", "diem_tb": 3}])
	site = _Site(vt=[_vt(tieu_chi="Thái độ\nNhanh nhẹn")], uv=[uv])
	cu = site.lay(td.UV, "UV-1")["danh_gia"][0]
	kq = _chay(site, lambda: td.cham("UV-1", "Làm thử", json.dumps({"Thái độ": 4, "Nhanh nhẹn": 3}), "Nên nhận", "Làm sạch bàn nhanh"))
	r = site.lay(td.UV, "UV-1")
	la("hai dòng chấm", len(r["danh_gia"]), 2)
	dung("dòng cũ giữ nguyên đối tượng (không dựng lại bảng)", r["danh_gia"][0] is cu)
	la("dòng mới", (r["danh_gia"][1]["vong"], r["danh_gia"][1]["diem_tb"], r["danh_gia"][1]["ket_luan"], r["danh_gia"][1]["nguoi"]),
		("Làm thử", 3.5, "Nên nhận", "Lê Hoàng Dễ"))
	la("điểm trả về", kq["diem_tb"], 3.5)
	dung("thiếu tiêu chí của vị trí thì chặn", "Nhanh nhẹn" in _loi(lambda: _chay(site, lambda: td.cham("UV-1", "Làm thử", json.dumps({"Thái độ": 4}), "Nên nhận"))))


@ca("v622 công làm thử có trả công: ghi giờ, tiền; đánh dấu đã trả kèm người và giờ; không trả hai lần")
def _cong_thu():
	uv = dict(_hs(), name="UV-1", sdt="0909123456", trang_thai=td.LAM_THU, da_an_danh=0)
	site = _Site(vt=[_vt()], uv=[uv])
	dung("tiền 0 bị chặn", "lớn hơn 0" in _loi(lambda: _chay(site, lambda: td.ghi_cong_thu("UV-1", 4, 0))))
	_chay(site, lambda: td.ghi_cong_thu("UV-1", "4", "100.000", 0))
	r = site.lay(td.UV, "UV-1")
	la("ghi công, chưa trả", (r["gio_lam_thu"], r["tien_cong_thu"], r.get("da_tra_cong")), (4.0, 100000, None))
	_chay(site, lambda: td.ghi_cong_thu("UV-1", "4", "100000", 1))
	la("đã trả, có người và giờ", (r["da_tra_cong"], r["tra_cong_boi"], r["tra_cong_luc"]), (1, "Lê Hoàng Dễ", BAY_GIO))
	dung("không ghi trả lần hai", "đã ghi là đã trả" in _loi(lambda: _chay(site, lambda: td.ghi_cong_thu("UV-1", 4, 100000, 1))))


@ca("v622 thêm hồ sơ tay: vẫn bắt xác nhận ứng viên đồng ý, câu báo nói việc của quản lý")
def _them_tay():
	site = _Site(vt=[_vt(dang_tuyen=0)])
	loi = _loi(lambda: _chay(site, lambda: td.them_ho_so(json.dumps(_hs(dong_y=0, nguon="TopCV")))))
	dung("câu báo cho quản lý", "Hỏi ứng viên đã đồng ý" in loi)
	kq = _chay(site, lambda: td.them_ho_so(json.dumps(_hs(nguon="TopCV"))))
	r = site.lay(td.UV, kq["name"])
	la("thêm được vào vị trí đang tắt (hồ sơ cũ từ TopCV)", (r["vi_tri"], r["nguon"], r["trang_thai"]), ("VTT-0001", "TopCV", td.MOI))
	dung("nhật ký ghi thêm tay", "Thêm hồ sơ tay, nguồn TopCV" in r["nhat_ky"])


@ca("v622 bật tắt vị trí: lưu đúng, trả câu trạng thái web")
def _bat_tat():
	site = _Site(vt=[_vt()])
	kq = _chay(site, lambda: td.bat_tat_vi_tri("VTT-0001", "0"))
	la("tắt", (site.lay(td.VT, "VTT-0001")["dang_tuyen"], kq["trang_thai_web"]), (0, "Đang tắt trên app, khách không thấy"))
	kq = _chay(site, lambda: td.bat_tat_vi_tri("VTT-0001", 1))
	la("bật", kq["trang_thai_web"], "Khách đang thấy")


@ca("v622 tin Zalo: hồ sơ mới báo một lần; quá 24 giờ nhắc mỗi hồ sơ một lần; mã tin có trong danh mục")
def _nhac():
	goi = []
	zalo = types.SimpleNamespace(
		bao=lambda loai, chu_de, tieu_de, dong=None, **kw: goi.append(dict(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=dong)),
		bao_hoac_ghi_loi=lambda loai, chu_de, tieu_de, dong=None, **kw: goi.append(dict(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=dong)))
	cu = dict(_hs(ca_ranh="Tối, Cuối tuần"), name="UV-1", sdt="0909123456", ten_vi_tri="Thu ngân ca tối", trang_thai=td.MOI, da_an_danh=0,
		creation=dt.datetime(2026, 8, 14, 8, 0))
	moi = dict(cu, name="UV-2", creation=dt.datetime(2026, 8, 15, 8, 0))
	goi_roi = dict(cu, name="UV-3", trang_thai=td.LIEN_HE)
	site = _Site(uv=[cu, moi, goi_roi])
	with um.patch.dict(sys.modules, {"vagabond.kenh_zalo": zalo}), um.patch.object(td.frappe.utils, "now_datetime", lambda: BAY_GIO):
		import vagabond
		with um.patch.object(vagabond, "kenh_zalo", zalo, create=True):
			_chay(site, td.nhac_qua_han)
			la("chỉ hồ sơ quá 24 giờ còn Mới nhận", [g["nguon"] for g in goi], ["UV-1"])
			la("khoá riêng từng hồ sơ, đúng mã tin", (goi[0]["khoa"], goi[0]["ma_tin"], goi[0]["kiem"]),
				("ung-vien-qua-han:UV-1", "ns_ung_vien_qua_han", "ung_vien_moi"))
			del goi[:]
			d = site.lay(td.UV, "UV-2")
			_chay(site, lambda: td.bao_moi(d))
	la("tin hồ sơ mới", (goi[0]["ma_tin"], goi[0]["chu_de"], goi[0]["khoa"]), ("ns_ung_vien_moi", "tuyen_dung", "ung-vien:UV-2"))
	dung("tin có tên, số, vị trí", "Nguyễn Văn An · 0909123456" in goi[0]["dong"][0] and "Thu ngân ca tối" in goi[0]["dong"][1])
	dung("tin có ca rảnh", "Ca rảnh: Tối, Cuối tuần" in goi[0]["dong"][2])
	for ma in ("ns_ung_vien_moi", "ns_ung_vien_qua_han"):
		dung("%s có trong danh mục tin Zalo" % ma, ma in kz.TIN and kz.TIN[ma][0] == "Nhân sự" and kz.TIN[ma][4] == "tuyen_dung")
	la("điều kiện hỏi lại trỏ đúng hàm", kz.DIEU_KIEN["ung_vien_moi"], "vagabond.tuyen_dung.con_moi_nhan")
	dung("chủ đề tuyển dụng có thật", "tuyen_dung" in kz.CHU_DE and kz.TEN_CHU_DE["tuyen_dung"] == "Tuyển dụng")


@ca("v622 hết hạn lưu: xoá thông tin cá nhân người không được nhận, giữ dòng; người đã nhận việc không đụng")
def _xoa_het_han():
	ds = [dict(_hs(), name="UV-1", trang_thai=td.DUNG, han_luu="2026-08-14", da_an_danh=0),
		dict(_hs(), name="UV-2", trang_thai=td.NHAN_VIEC, han_luu="2026-08-14", da_an_danh=0),
		dict(_hs(), name="UV-3", trang_thai=td.MOI, han_luu="2026-08-15", da_an_danh=0)]
	site = _Site(uv=ds)
	_chay(site, td.xoa_het_han)
	la("chỉ UV-1 bị xoá thông tin", [x[1] for x in site.set_value], ["UV-1"])
	v = site.set_value[0][2]
	la("xoá tên, số, email, CV, nhận xét; đánh dấu", (v["sdt"], v["email"], v["lien_ket_cv"], v["da_an_danh"]), ("", "", "", 1))
	dung("không giữ họ tên thật", "An" not in v["ho_ten"])
	dung("nhận xét trong phiếu chấm cũng xoá", any("Vagabond Ung Vien Danh Gia" in str(x) for x in site.ghi if x[0] == "sql"))
	dung("không xoá cứng dòng nào", not any(x[0] == "delete" for x in site.ghi))
	# Hai lớp giữ người đã nhận việc: câu lọc của nhịp đêm và phép can_xoa. Đột
	# biến bỏ một lớp không làm ca trên đỏ (lớp kia đỡ), nên chốt riêng phép thuần.
	la("phép thuần: người đã nhận việc không bao giờ tới hạn xoá",
		td.can_xoa({"trang_thai": td.NHAN_VIEC, "han_luu": "2026-01-01", "da_an_danh": 0}, HOM_NAY), False)
	la("phép thuần: đã xoá rồi thì không xoá lại", td.can_xoa({"trang_thai": td.DUNG, "han_luu": "2026-01-01", "da_an_danh": 1}, HOM_NAY), False)
	la("phép thuần: chưa tới hạn", td.can_xoa({"trang_thai": td.DUNG, "han_luu": HOM_NAY, "da_an_danh": 0}, HOM_NAY), False)


@ca("v622 doctype: mọi ô máy chủ đọc ghi đều có trong JSON; mã lần gửi là duy nhất; đổi bố cục có mốc modified")
def _doctype():
	vt = json.loads(_doc_tep("vagabond", "doctype", "vagabond_vi_tri_tuyen", "vagabond_vi_tri_tuyen.json"))
	uv = json.loads(_doc_tep("vagabond", "doctype", "vagabond_ung_vien", "vagabond_ung_vien.json"))
	dg = json.loads(_doc_tep("vagabond", "doctype", "vagabond_ung_vien_danh_gia", "vagabond_ung_vien_danh_gia.json"))
	o_vt, o_uv, o_dg = ({f["fieldname"] for f in j["fields"]} | {"name", "modified", "creation"} for j in (vt, uv, dg))
	la("ô vị trí", sorted(set(td.TRUONG_VT) - o_vt), [])
	la("ô hồ sơ", sorted(set(td.TRUONG_UV) - o_uv), [])
	la("ô xoá theo hạn", sorted(set(td.an_danh({})) - o_uv), [])
	la("ô phiếu chấm", sorted({"vong", "nguoi", "luc", "diem", "diem_tb", "ket_luan", "nhan_xet"} - o_dg), [])
	la("mã lần gửi duy nhất", [f.get("unique") for f in uv["fields"] if f["fieldname"] == "bam_lan_gui"], [1])
	# Bài học v620: ô Data chỉ chứa 140 ký tự; mã cho gõ dài hơn là Frappe ném lỗi
	# độ dài (417, không vào Error Log) và hồ sơ mất. Đưa giá trị dài nhất mã nhận
	# qua chuẩn hoá thật rồi so với sức chứa của đúng kiểu ô trong JSON.
	kieu = {f["fieldname"]: f["fieldtype"] for f in uv["fields"]}
	dai = td.chuan_ho_so(_hs(ho_ten="A" * 120, email="a" * 120 + "@gmail.com", khu_vuc="K" * 120,
		lien_ket_cv="https://" + "c" * 492, nguoi_gioi_thieu="N" * 120, ca_ranh=list(td.CA_RANH)), ["VTT-0001"])
	for o, v in dai.items():
		if kieu.get(o) == "Data":
			dung("ô %s (Data, 140) chứa được %d ký tự mã nhận" % (o, len(str(v))), len(str(v)) <= 140)
	la("CV dài 500 nằm ở ô Small Text", kieu["lien_ket_cv"], "Small Text")
	kieu_vt = {f["fieldname"]: f["fieldtype"] for f in vt["fields"]}
	dai_vt = td.chuan_vi_tri({"tieu_de": "T" * 140, "noi_lam": "N" * 140, "muc_luong": "L" * 140})
	for o, v in dai_vt.items():
		if kieu_vt.get(o) == "Data":
			dung("vị trí: ô %s chứa được %d ký tự" % (o, len(str(v))), len(str(v)) <= 140)
	la("trạng thái trên JSON khớp máy chủ", [f["options"].split("\n") for f in uv["fields"] if f["fieldname"] == "trang_thai"][0], list(td.TRANG_THAI))
	la("nguồn trên JSON khớp máy chủ", [f["options"].split("\n") for f in uv["fields"] if f["fieldname"] == "nguon"][0], list(td.NGUON))
	la("hình thức khớp", [f["options"].split("\n") for f in vt["fields"] if f["fieldname"] == "hinh_thuc"][0], list(td.HINH_THUC))
	la("bảng con là bảng con", (dg.get("istable"), [f["options"] for f in uv["fields"] if f["fieldname"] == "danh_gia"]),
		(1, ["Vagabond Ung Vien Danh Gia"]))
	for j in (vt, uv, dg):
		la("%s: thứ tự ô đủ" % j["name"], j["field_order"], [f["fieldname"] for f in j["fields"]])
		dung("%s: có mốc modified" % j["name"], str(j.get("modified", "")) >= "2026-10-30")


@ca("v622 móc và lịch: hồ sơ mới báo Zalo, nhắc mỗi giờ, xoá theo hạn 03:40; trang /ung-tuyen mở trên miền khách")
def _moc():
	import importlib
	h = importlib.import_module("vagabond.hooks")
	la("hook tạo hồ sơ", h.doc_events["Vagabond Ung Vien"]["after_insert"], "vagabond.tuyen_dung.bao_moi")
	dung("nhắc mỗi giờ", "vagabond.tuyen_dung.nhac_qua_han" in h.scheduler_events["hourly"])
	dung("xoá 03:40", "vagabond.tuyen_dung.xoa_het_han" in h.scheduler_events["cron"]["40 3 * * *"])
	for ham in ("bao_moi", "nhac_qua_han", "xoa_het_han", "con_moi_nhan"):
		dung("hàm %s có thật" % ham, callable(getattr(td, ham, None)))
	from vagabond.ten_mien import dich_chuyen_huong, MIEN_KHACH, MIEN_APP
	la("/ung-tuyen mở trên miền khách", dich_chuyen_huong(MIEN_KHACH, "/ung-tuyen"), "")
	dung("/ung-tuyen không mở trên miền app nội bộ", dich_chuyen_huong(MIEN_APP, "/ung-tuyen") != "")
	from vagabond import duong_app
	la("màn app có đường riêng", duong_app.bang_duong().get("tuyen-dung"), "TD")


# ------------------------------------------------------------ liên hệ ứng viên (30/10/2026)

@ca("v622 liên hệ ứng viên (phép thuần): kênh, kết quả gọi, chuyển trạng thái, mẫu tin đủ chỗ trống")
def _lien_he_thuan():
	la("gọi thiếu kết quả", td.kiem_lien_he("Gọi"), "Chọn kết quả cuộc gọi.")
	dung("kênh lạ", "Gọi, Zalo hoặc SMS" in td.kiem_lien_he("Email"))
	dung("mẫu lạ", "Mẫu tin" in td.kiem_lien_he("Zalo", mau="khong_co"))
	la("hợp lệ", [td.kiem_lien_he("Gọi", "Sai số"), td.kiem_lien_he("Zalo", mau="hen_pv"), td.kiem_lien_he("SMS")], ["", "", ""])
	la("gọi không nghe hoặc sai số: giữ Mới nhận", [td.sau_lien_he(td.MOI, "Gọi", "Không nghe máy"), td.sau_lien_he(td.MOI, "Gọi", "Sai số")], [td.MOI, td.MOI])
	la("nghe máy, hẹn gọi lại, nhắn tin: sang Đã liên hệ", [td.sau_lien_he(td.MOI, "Gọi", "Nghe máy"),
		td.sau_lien_he(td.MOI, "Gọi", "Hẹn gọi lại"), td.sau_lien_he(td.MOI, "Zalo"), td.sau_lien_he(td.MOI, "SMS")], [td.LIEN_HE] * 4)
	la("không kéo lùi hồ sơ đã ở vòng sau", [td.sau_lien_he(td.HEN_PV, "Zalo"), td.sau_lien_he(td.NHAN_VIEC, "Gọi", "Nghe máy")], [td.HEN_PV, td.NHAN_VIEC])
	la("dòng nhật ký", [td.cau_lien_he("Gọi", "Không nghe máy"), td.cau_lien_he("Zalo", mau="hen_pv"), td.cau_lien_he("SMS")],
		["Gọi: Không nghe máy", "Nhắn Zalo mẫu Hẹn phỏng vấn", "Nhắn SMS"])
	for m in td.MAU_TIN:
		dung("mẫu %s chỉ dùng chỗ trống app điền được" % m[0], set(re.findall(r"\{(\w+)\}", m[3])) <= set(td.CHO_TRONG))
		dung("mẫu %s có tên, giải thích, không gạch dài" % m[0], m[1] and m[2] and not re.search("[\u2013\u2014]", m[1] + m[2] + m[3]))
	la("mỗi trạng thái có mẫu gợi ý đúng mã", sorted(td.MAU_THEO_TRANG_THAI), sorted(td.TRANG_THAI))
	dung("mẫu gợi ý có thật", set(td.MAU_THEO_TRANG_THAI.values()) <= {m[0] for m in td.MAU_TIN})
	dung("mỗi kết quả gọi có dòng giải thích", all(p for _k, p in td.KET_QUA_GOI))
	app = td.mau_tin_app()
	la("gói gửi app", (len(app["mau_tin"]), [k["k"] for k in app["ket_qua_goi"]], app["hotline"]),
		(len(td.MAU_TIN), [k for k, _p in td.KET_QUA_GOI], td.HOTLINE))
	cu = {"trang_thai": td.MOI, "creation": "2026-08-14 08:00:00"}
	la("đã có người gọi thì không còn nhắc chưa ai gọi", [td.qua_han_goi(cu, BAY_GIO), td.qua_han_goi(dict(cu, lien_he_luc="2026-08-14 09:00:00"), BAY_GIO)], [True, False])
	la("ô Chưa gọi không đếm hồ sơ đã gọi", td.tom_tat([cu, dict(cu, lien_he_luc="2026-08-14 09:00:00")], HOM_NAY, BAY_GIO)["moi"], 1)


@ca("v622 ghi liên hệ: gọi không nghe giữ Mới nhận nhưng hết nhắc; nhắn Zalo chuyển Đã liên hệ; nhật ký đúng người")
def _ghi_lien_he():
	uv = dict(_hs(), name="UV-1", sdt="0909123456", trang_thai=td.MOI, da_an_danh=0, nhat_ky="")
	site = _Site(vt=[_vt()], uv=[uv])
	kq = _chay(site, lambda: td.ghi_lien_he("UV-1", "Gọi", "Không nghe máy"))
	r = site.lay(td.UV, "UV-1")
	la("giữ Mới nhận, ghi lần liên hệ đầu", (kq["trang_thai"], r["trang_thai"], r["lien_he_luc"]), (td.MOI, td.MOI, BAY_GIO))
	dung("nhật ký có người và kết quả", "Lê Hoàng Dễ: Gọi: Không nghe máy" in r["nhat_ky"])
	_chay(site, lambda: td.ghi_lien_he("UV-1", "Zalo", "", "hen_pv"))
	la("nhắn Zalo thì sang Đã liên hệ", r["trang_thai"], td.LIEN_HE)
	dung("nhật ký ghi mẫu và chuyển trạng thái", "Nhắn Zalo mẫu Hẹn phỏng vấn, Mới nhận -> Đã liên hệ" in r["nhat_ky"])
	la("lần liên hệ đầu không bị ghi đè", r["lien_he_luc"], BAY_GIO)
	dung("kênh lạ bị chặn", "Gọi, Zalo hoặc SMS" in _loi(lambda: _chay(site, lambda: td.ghi_lien_he("UV-1", "Email"))))
	dung("gọi thiếu kết quả bị chặn", "kết quả cuộc gọi" in _loi(lambda: _chay(site, lambda: td.ghi_lien_he("UV-1", "Gọi"))))
	r["da_an_danh"] = 1
	dung("hồ sơ đã xoá thông tin thì không liên hệ", "hạn lưu" in _loi(lambda: _chay(site, lambda: td.ghi_lien_he("UV-1", "SMS"))))


# ------------------------------------------------------------ Codex rà #518 (25615f076e), 31/10/2026

@ca("v622 Codex #518: hồ sơ tạo qua Desk hay API cũng phải có đồng ý lưu và hạn lưu (controller validate)")
def _codex_dong_y_desk():
	from vagabond.vagabond.doctype.vagabond_ung_vien.vagabond_ung_vien import VagabondUngVien

	class _D(VagabondUngVien, dict):
		def set(self, k, v):
			self[k] = v

	with um.patch.object(td.frappe.utils, "now_datetime", lambda: BAY_GIO):
		d = _D(ho_ten="An", sdt="0909123456", dong_y=0)
		dung("Desk không tích đồng ý: chặn, chỉ đường sang app", "Nhân sự, Tuyển dụng, Thêm hồ sơ" in _loi(d.validate))
		d = _D(ho_ten="An", dong_y=1)
		d.validate()
		la("có đồng ý mà thiếu hạn: máy đặt lúc đồng ý và hạn 12 tháng", (d["dong_y_luc"], d["han_luu"]), (BAY_GIO, "2027-08-15"))
		d = _D(dong_y=1, dong_y_luc="2026-01-31 10:00:00", han_luu="2026-05-01")
		d.validate()
		la("đã có hạn thì giữ nguyên", d["han_luu"], "2026-05-01")
		d = _D(dong_y=1, dong_y_luc="2026-01-31 10:00:00")
		d.validate()
		la("hạn tính từ lúc đồng ý ghi sẵn", d["han_luu"], "2027-01-31")
		d = _D(dong_y=0, da_an_danh=1)
		d.validate()
		la("hồ sơ đã xoá thông tin thì không bắt lại", dict(d), {"dong_y": 0, "da_an_danh": 1})


@ca("v622 Codex #518: xoá theo hạn bỏ cả lý do dừng gõ tay và lịch sử sửa; lưu lịch sử sửa đã tắt")
def _codex_an_danh_du():
	la("an_danh xoá lý do dừng", td.an_danh({})["ly_do_dung"], "")
	ds = [dict(_hs(), name="UV-1", trang_thai=td.DUNG, ly_do_dung="Nhà ở Thủ Đức, đang mang thai", han_luu="2026-08-14", da_an_danh=0),
		dict(_hs(), name="UV-2", trang_thai=td.DUNG, han_luu="2026-09-30", da_an_danh=0)]
	site = _Site(uv=ds)
	_chay(site, td.xoa_het_han)
	la("chỉ UV-1 tới hạn, lý do dừng xoá", [(x[1], x[2]["ly_do_dung"]) for x in site.set_value], [("UV-1", "")])
	la("bỏ lịch sử sửa của đúng hồ sơ đó", [x[1:] for x in site.ghi if x[0] == "xoa_lich_su"], [("Version", {"ref_doctype": td.UV, "docname": "UV-1"})])
	j = json.loads(_doc_tep("vagabond", "doctype", "vagabond_ung_vien", "vagabond_ung_vien.json"))
	la("hồ sơ ứng viên không lưu lịch sử sửa (nhật ký trên hồ sơ thay thế)", j.get("track_changes"), 0)


@ca("v622 Codex #518: quản lý chốt Đã nhận việc ngay sau khi nhịp đêm chọn lô thì không bị xoá")
def _codex_khoa_doc_lai():
	site = _Site(uv=[dict(_hs(), name="UV-1", trang_thai=td.DUNG, han_luu="2026-08-14", da_an_danh=0)])
	goc = site.get_all

	def chon_lo_roi_chot(d, filters=None, fields=None, **k):
		ra = goc(d, filters, fields, **k)
		site.lay(td.UV, "UV-1")["trang_thai"] = td.NHAN_VIEC
		return ra
	site.get_all = chon_lo_roi_chot
	_chay(site, td.xoa_het_han)
	la("không ghi đè người vừa được nhận", site.set_value, [])
	la("không bỏ nhận xét, lịch sử", [x[0] for x in site.ghi if x[0] in ("sql", "xoa_lich_su")], [])
	dung("đọc lại có khoá dòng", "for_update=True" in _doc_tep("tuyen_dung.py").split("def xoa_het_han")[1].split("def ")[0])

