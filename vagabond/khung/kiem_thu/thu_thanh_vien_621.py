# -*- coding: utf-8 -*-
"""v621: trang thành viên mới và quà chào mừng tại quầy (anh Việt 30/10/2026).

Anh chốt: quà giảm 20.000đ, bắt buộc xác minh số qua Zalo, mã dùng ngay trên
hoá đơn đang tính; không dùng trong ngày thì còn 7 ngày; khách cũ cũng được,
mỗi số một lần.

Mỗi ca chốt một đường lỗi có thật:
  - hai lượt bấm "Nhận quà" ra hai mã, hay đổi khách vẫn nhận lại quà;
  - thu ngân chọn thẳng chương trình (không mã) để đi vòng mã một lần
    (Codex PR #503);
  - mã quà áp cho hoá đơn của khách khác, hay hoá đơn không gắn người nhận
    nên không tích điểm (Codex PR #503);
  - ô khách gõ (ngày sinh, email, ảnh) là đầu vào không tin được;
  - lượt tính nhóm đêm của CRM ghi đè phần khách tự khai.
Phần chạm hệ chạy trên lớp Frappe giả, vá đúng lời gọi hàm thật dùng.
"""

import ast
import base64
import datetime as dt
import json
import sys
import types
import unittest.mock as um
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
# Bản giả không có frappe.rate_limiter; site thật có. Không ghi đè bản thật.
_rl = types.ModuleType("frappe.rate_limiter")
_rl.rate_limit = lambda *a, **k: (lambda f: f)
sys.modules.setdefault("frappe.rate_limiter", _rl)

from vagabond import thanh_vien as tv  # noqa: E402
from vagabond import khuyen_mai as km  # noqa: E402
from vagabond.khung.kiem_thu.thu_su_co_290 import nap  # noqa: E402

GOC = Path(__file__).resolve().parents[2]
D8 = dt.date
HN = D8(2026, 10, 30)
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


# ------------------------------------------------------------------ thuần

@ca("v621 thành viên: ô tên, ngày sinh, email, món hay chọn chịu mọi cách gõ hợp lý; chặn ngày không có thật")
def _thuan():
	la("tên gộp khoảng trắng", tv.chuan_ten("  Lan   Anh "), ("Lan Anh", ""))
	la("tên trống", tv.chuan_ten(" "), ("", "thieu_ten"))
	la("tên toàn số", tv.chuan_ten("0901486556")[1], "ten_khong_dung")
	la("tên quá dài", tv.chuan_ten("a" * 61)[1], "ten_khong_dung")
	la("tên máy tự đặt không điền sẵn", (tv.ten_that("Khách 3412"), tv.ten_that("Khách Lan")), ("", "Khách Lan"))
	la("ngày sinh đủ", tv.chuan_sinh_nhat("14", "11", "1990", HN), (D8(1990, 11, 14), ""))
	la("ngày sinh gõ số 0 đầu và khoảng trắng", tv.chuan_sinh_nhat(" 05", "03 ", "", HN), (D8(tv.NAM_AN, 3, 5), ""))
	la("không năm vẫn nhận 29/02", tv.chuan_sinh_nhat("29", "2", None, HN), (D8(tv.NAM_AN, 2, 29), ""))
	la("29/02 năm thường là sai", tv.chuan_sinh_nhat("29", "2", "1990", HN)[1], "ngay_sinh_khong_dung")
	la("31/04 sai", tv.chuan_sinh_nhat("31", "4", "", HN)[1], "ngay_sinh_khong_dung")
	la("năm tương lai sai", tv.chuan_sinh_nhat("1", "1", "2030", HN)[1], "ngay_sinh_khong_dung")
	la("năm chữ sai", tv.chuan_sinh_nhat("1", "1", "abc", HN)[1], "ngay_sinh_khong_dung")
	la("thiếu tháng", tv.chuan_sinh_nhat("1", "", "", HN)[1], "ngay_sinh_thieu")
	la("để trống cả ba là không khai", tv.chuan_sinh_nhat("", "", "", HN), (None, ""))
	la("hiện ngày có năm", tv.hien_sinh_nhat(D8(1990, 11, 14)), {"ngay": 14, "thang": 11, "nam": 1990})
	la("năm ẩn không hiện", tv.hien_sinh_nhat(D8(tv.NAM_AN, 3, 5)), {"ngay": 5, "thang": 3, "nam": ""})
	la("hiện từ chuỗi", tv.hien_sinh_nhat("1990-11-14"), {"ngay": 14, "thang": 11, "nam": 1990})
	la("email chữ hoa", tv.chuan_email(" Lan@Gmail.COM "), ("lan@gmail.com", ""))
	la("email trống được", tv.chuan_email(""), ("", ""))
	la("email sai", tv.chuan_email("lan@gmail")[1], "email_khong_dung")
	la("món hay chọn: bỏ mã lạ, không trùng, đúng thứ tự màn",
		tv.chuan_so_thich(["tart", "croissant", "tart", "<script>"]), ["croissant", "tart"])
	la("món hay chọn từ chuỗi JSON", tv.chuan_so_thich('["do_uong"]'), ["do_uong"])


@ca("v621 ảnh đại diện: chỉ nhận JPEG thật dưới trần; PNG, base64 hỏng, ảnh quá lớn đều bị chặn")
def _anh():
	url = "data:image/jpeg;base64," + base64.b64encode(JPEG).decode()
	la("JPEG nhận", tv.doc_anh(url), (JPEG, ""))
	png = "data:image/jpeg;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 20).decode()
	la("PNG khai là JPEG vẫn chặn (đọc byte đầu)", tv.doc_anh(png)[1], "anh_khong_dung")
	la("kiểu khác", tv.doc_anh("data:image/png;base64,AAAA")[1], "anh_khong_dung")
	la("base64 hỏng", tv.doc_anh("data:image/jpeg;base64,@@@")[1], "anh_khong_dung")
	to = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff" + b"\x00" * (tv.ANH_TOI_DA + 10)).decode()
	la("quá trần", tv.doc_anh(to)[1], "anh_qua_lon")
	la("rỗng", tv.doc_anh(None)[1], "anh_khong_dung")


@ca("v621 hồ sơ: đếm mục đã khai; quà cần đủ tên, ngày sinh, đồng ý nhận tin Zalo")
def _muc():
	la("trống", tv.muc_ho_so({}), {"du": 0, "tong": 5, "thieu_qua": ["ten", "sinh_nhat", "dong_y"]})
	la("đủ ba mục quà", tv.muc_ho_so({"ten": "Lan", "sinh_nhat": D8(1990, 1, 1), "dong_y": 1}),
		{"du": 3, "tong": 5, "thieu_qua": []})
	la("đủ cả năm", tv.muc_ho_so({"ten": "Lan", "sinh_nhat": 1, "dong_y": 1, "anh": "x", "so_thich": ["tart"]})["du"], 5)
	la("voucher dùng được", tv.trang_thai_voucher(D(trang_thai="Chua dung", han_dung=D8(2026, 11, 6)), HN), "dung_duoc")
	la("hết hạn", tv.trang_thai_voucher(D(trang_thai="Chua dung", han_dung="2026-10-29"), HN), "het_han")
	la("hạn hôm nay vẫn dùng", tv.trang_thai_voucher(D(trang_thai="Chua dung", han_dung=HN), HN), "dung_duoc")
	la("đã dùng", tv.trang_thai_voucher(D(trang_thai="Da dung"), HN), "da_dung")
	la("đã huỷ", tv.trang_thai_voucher(D(trang_thai="Da huy"), HN), "da_huy")


@ca("v621 tiến độ hạng: một phép cho màn Chi tiết khách và trang thành viên; không còn chỗ nào tự tính")
def _tien_do():
	ham = nap("khach_hang.py", "tien_do_hang", dict(flt=lambda v: float(v or 0)))
	bang = [{"name": "VOYAGER", "chi_tieu_tu": 10000000}, {"name": "EXPLORER", "chi_tieu_tu": 0},
		{"name": "VAGABONDER", "chi_tieu_tu": 20000000}]
	la("giữa hai hạng", ham(bang, 13580000), {"dat": "VOYAGER", "tiep": "VAGABONDER", "con_thieu": 6420000.0, "ty_le": 0.679})
	la("chưa mua", ham(bang, 0), {"dat": "EXPLORER", "tiep": "VOYAGER", "con_thieu": 10000000.0, "ty_le": 0.0})
	la("hạng cao nhất", ham(bang, 25000000), {"dat": "VAGABONDER", "tiep": "", "con_thieu": 0, "ty_le": 1.0})
	la("đúng mốc là lên", ham(bang, 20000000)["dat"], "VAGABONDER")
	# Chốt một nguồn: thân ho_so không còn vòng so chi_tieu_tu tự viết.
	cay = ast.parse((GOC / "khach_hang.py").read_text())
	hs = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "ho_so")
	goi = {getattr(n.func, "id", "") for n in ast.walk(hs) if isinstance(n, ast.Call)}
	dung("ho_so gọi tien_do_hang", "tien_do_hang" in goi)
	so_sanh = [n for n in ast.walk(hs) if isinstance(n, ast.Compare) and "chi_tieu_tu" in ast.unparse(n)]
	la("ho_so không tự so chi_tieu_tu", len(so_sanh), 0)
	dung("trang thành viên dùng chung", "khach_hang.tien_do_hang(" in (GOC / "thanh_vien.py").read_text())


# ------------------------------------------------------------------ quầy

def _tinh(ctkm, ma=None, khach=None, sdt="", voucher=None, hang=None):
	"""Chạy THẬT khuyen_mai.tinh trên dữ liệu giả."""
	voucher = voucher or {}
	hang = hang or {}

	class Fr:
		db = types.SimpleNamespace(
			get_value=lambda dt_, ten=None, truong=None, as_dict=False, **k: (
				D(voucher[ten]) if dt_ == "Vagabond Voucher" and ten in voucher else
				hang.get(ten) if dt_ == "Customer" and truong == "vgb_hang" else
				D(name="VOYAGER", ten_hang="VOYAGER", giam_gia=10, bat=1) if dt_ == "Vagabond Hang Khach" and ten == "VOYAGER" else None),
			exists=lambda dt_, ten=None: (dt_ == "Vagabond CTKM" and ten in ctkm) or (dt_ == "Vagabond Voucher" and ten in voucher),
		)
		get_all = staticmethod(lambda *a, **k: [])

		@staticmethod
		def throw(m, *a, **k):
			raise Exception(m)
	with um.patch.object(km, "frappe", Fr), um.patch.object(km, "_doc_ctkm", lambda m: dict(ctkm[m], name=m)), \
			um.patch.object(km, "_hop_thoi_gian", lambda *a, **k: (True, "")), \
			um.patch.object(km, "_hop_kenh", lambda *a, **k: (True, "")), \
			um.patch.object(km, "_hop_han_muc", lambda *a, **k: (True, "")):
		return km.tinh([{"item_code": "BANH", "qty": 1, "rate": 300000}], ctkm=[c for c in ctkm if not ma],
			ma=ma, quay="TCV", nguon="Tại chỗ", khach=khach, sdt=sdt)


QUA = {km.CTKM_QUA: dict(ten="Quà chào mừng thành viên", cach_thuc="Giam tong hoa don", bat=1, cong_don=1,
	kieu_giam="So tien", gia_tri=20000, pham_vi="Ca hoa don", doi_tuong="Moi khach", cach_ma="Ma dung mot lan")}
VC = {"QK7M2P": dict(ctkm=km.CTKM_QUA, trang_thai="Chua dung", han_dung=None, danh_cho="KL0412", sdt="0909123412")}


@ca("PR503 Codex: chương trình phát mã dùng một lần KHÔNG áp khi chỉ gửi tên chương trình (không mã), kể cả quà chào mừng")
def _ctkm_khong_ma():
	# Tái hiện trên 455adcd: gửi ctkm=[QUA-CHAO-MUNG] không kèm mã thì máy
	# vẫn giảm 20.000đ, bỏ qua mã một lần, OTP và luật một số một lần.
	kq = _tinh(QUA)
	la("không giảm", kq["tong_giam"], 0)
	dung("nói rõ phải nhập mã", any("chỉ áp khi nhập mã dùng một lần" in b["ly_do"] for b in kq["bo"]))
	# Chương trình Không cần mã vẫn áp như cũ.
	kq = _tinh({"KM-THU": dict(QUA[km.CTKM_QUA], ten="Thu", cach_ma="Khong can ma")})
	la("chương trình không cần mã vẫn áp", kq["tong_giam"], 20000)


@ca("PR503 Codex: mã quà gắn người nhận vào hoá đơn chưa chọn khách (tích điểm, ưu đãi hạng đúng người); khách khác hay số khác thì từ chối")
def _nguoi_nhan():
	# Tái hiện trên 455adcd: hoá đơn không chọn khách áp mã quà thì vẫn là
	# khách lẻ, không ưu đãi hạng, không tích điểm cho người vừa xác minh.
	kq = _tinh(QUA, ma="QK7M2P", voucher=VC, hang={"KL0412": "VOYAGER"})
	la("giảm quà và ưu đãi hạng của người nhận", sorted((a["loai"], a["giam"]) for a in kq["ap"]),
		[("ctkm", 20000), ("hang", 28000)])
	try:
		_tinh(QUA, ma="QK7M2P", voucher=VC, khach="KL9999")
		dung("khách khác phải bị từ chối", False)
	except Exception as e:
		dung("câu nói của khách khác", "của khách khác" in str(e))
	try:
		_tinh(QUA, ma="QK7M2P", voucher=VC, sdt="0911000000")
		dung("số khác phải bị từ chối", False)
	except Exception as e:
		dung("câu nói số khác", "số điện thoại khác" in str(e))
	la("đúng khách thì nhận", _tinh(QUA, ma="QK7M2P", voucher=VC, khach="KL0412")["tong_giam"] >= 20000, True)
	la("đúng số (dạng 84) thì nhận", _tinh(QUA, ma="QK7M2P", voucher=VC, sdt="84909123412")["tong_giam"], 20000)
	# Voucher tin Zalo (không ràng buộc) dùng cho khách khác vẫn được như trước.
	km2 = {"KM-SN": dict(QUA[km.CTKM_QUA], ten="Sinh nhật")}
	vc2 = {"SN1234": dict(VC["QK7M2P"], ctkm="KM-SN")}
	la("voucher thường cho khách khác vẫn được", _tinh(km2, ma="SN1234", voucher=vc2, khach="KL9999")["tong_giam"], 20000)
	la("thuần: không gắn ai thì giữ khách", km.kiem_nguoi_nhan({}, "KL1", ""), ("KL1", ""))
	la("thuần: gắn người nhận khi chưa có khách", km.kiem_nguoi_nhan({"danh_cho": "KL2"}, "", ""), ("KL2", ""))


@ca("PR503 Codex: lưu hoá đơn quầy gắn người nhận của mã khi thu ngân chưa chọn khách, TRƯỚC khi tính khuyến mãi")
def _tao_don_tay():
	# Không nạp ban_hang (kéo requests). Đọc cây hàm: gán khach_ma từ mã phải
	# đứng trước dòng khach_km và chỉ khi chưa có khách nợ, khách chọn.
	cay = ast.parse((GOC / "ban_hang.py").read_text())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "tao_don_tay")
	gan = [n for n in ast.walk(ham) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "khach_ma" for t in n.targets)]
	km_ = [n for n in ast.walk(ham) if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "khach_km" for t in n.targets)]
	la("một chỗ gán khach_ma", len(gan), 1)
	dung("gán từ khach_cua_ma", "khach_cua_ma(ma_voucher)" in ast.unparse(gan[0]))
	dung("trước khach_km", gan[0].lineno < km_[0].lineno)
	cha = next(n for n in ast.walk(ham) if isinstance(n, ast.If) and gan[0] in n.body)
	dk = ast.unparse(cha.test)
	dung("chỉ khi chưa chọn khách", "not (khach_no or '').strip()" in dk and "not (khach_ma or '').strip()" in dk)


# ------------------------------------------------------------------ máy chủ trang

class Moi:
	"""Lớp giả cho nhan_qua / luu_ho_so: voucher, hồ sơ CRM, Customer, khoá."""

	def __init__(self, ho_so=None, khach=None, vc=None, km_qua=None, nhan_vien=False, so="84909123412"):
		self.hs = ho_so if ho_so is not None else {"KL0412": D(ten_goi="Lan Anh", dy_zalo="Đồng ý", qua_chao_mung="")}
		self.kh = khach if khach is not None else D(name="KL0412", customer_name="Nguyễn Lan Anh", vgb_sinh_nhat=D8(1990, 11, 14))
		self.vc = vc if vc is not None else {}
		self.km = km_qua if km_qua is not None else D(name=km.CTKM_QUA, ten="Quà chào mừng thành viên", cach_ma="Ma dung mot lan",
			bat=1, kieu_giam="So tien", gia_tri=20000, hd_toi_thieu=0)
		self.nv, self.so = nhan_vien, so
		self.vet, self.ma = [], iter(["QK7M2P", "QB3N8R"])
		self.dong_y = []

	def get_value(self, dt_, ten=None, cot=None, as_dict=False, **k):
		if dt_ == "Vagabond Voucher":
			v = self.vc.get(ten)
			return D({c: v.get(c) for c in cot}) if v and isinstance(cot, list) else (v or {}).get(cot) if v else None
		if dt_ == tv.DT_HO_SO:
			h = self.hs.get(ten)
			if not h:
				return None if not as_dict else {}
			return D({c: h.get(c) for c in cot}) if isinstance(cot, list) else h.get(cot)
		return None

	def get_all(self, dt_, filters=None, fields=None, order_by=None, limit_page_length=None, **k):
		if dt_ == "Vagabond Voucher":
			ra = [D(v, ma=m) for m, v in self.vc.items() if all(v.get(c) == x for c, x in (filters or {}).items())]
			return ra[:limit_page_length] if limit_page_length else ra
		return []

	def sql(self, q, *a, **k):
		self.vet.append(("sql", q.strip()[:40]))
		return []

	def set_value(self, dt_, ten, v, *a, **k):
		self.vet.append(("set", dt_))
		if dt_ == tv.DT_HO_SO:
			self.hs.setdefault(ten, D()).update(v if isinstance(v, dict) else {v: a[0]})
		if dt_ == "Customer":
			self.kh[v] = a[0]

	def get_doc(self, d, *a, **k):
		moi = self

		class Doc(D):
			def insert(self, **kk):
				moi.vet.append(("insert", self.get("doctype")))
				if self.get("doctype") == "Vagabond Voucher":
					moi.vc[self["ma"]] = D(self)
				return self
		return Doc(d)

	def chay(self, ham, *a, **k):
		fr = tv.frappe
		from vagabond import crm

		def ho_so(khach, tao=False):
			if tao:
				self.hs.setdefault(khach, D(dy_zalo="Chưa hỏi"))
			return self.hs.get(khach)

		def ghi_dy(khach, dat, noi, cau_hoi="", nguoi=None, **kk):
			self.dong_y.append((khach, dat, noi, nguoi))
			self.hs[khach]["dy_zalo"] = dat["Zalo"]
		with um.patch.object(tv, "_so_phien", lambda: self.so), um.patch.object(tv, "_hom_nay", lambda: HN), \
				um.patch.object(tv, "_ctkm_qua", lambda: self.km), \
				um.patch.object(tv, "_dn", lambda: types.SimpleNamespace(_sdt_noi_dia=lambda s: "0" + s[-9:])), \
				um.patch.object(tv, "_khach_cua_so", lambda so: ((self.kh or None), "")), \
				um.patch.object(tv, "_khong_cache", lambda: None), \
				um.patch.object(km, "_la_sdt_nhan_vien", lambda s: self.nv), \
				um.patch.object(km, "_sinh_ma_moi", lambda n: [next(self.ma)]), \
				um.patch.object(crm, "_ho_so", ho_so), um.patch.object(crm, "ghi_dong_y_noi", ghi_dy), \
				um.patch.object(fr.db, "get_value", self.get_value), um.patch.object(fr.db, "sql", self.sql), \
				um.patch.object(fr.db, "set_value", self.set_value), um.patch.object(fr, "get_all", self.get_all), \
				um.patch.object(fr, "get_doc", self.get_doc):
			return ham(*a, **k)


@ca("v621 nhận quà: đủ hồ sơ thì cấp MỘT mã gắn đúng người nhận, hạn 7 ngày; bấm lại trả đúng mã cũ, không cấp mã thứ hai")
def _nhan_qua():
	m = Moi()
	kq = m.chay(tv.nhan_qua, quay="tcv")
	la("cấp mã", (kq["ok"], kq["ma"], kq["cu"], kq["han"], kq["uu_dai"]), (1, "QK7M2P", 0, "06/11/2026", "Giảm 20.000đ"))
	v = m.vc["QK7M2P"]
	la("mã gắn đúng người nhận", (v["danh_cho"], v["ctkm"], v["trang_thai"], str(v["han_dung"]), v["sdt"], v["quay"]),
		("KL0412", km.CTKM_QUA, "Chua dung", "2026-11-06", "0909123412", "TCV"))
	la("ghi lên hồ sơ", m.hs["KL0412"]["qua_chao_mung"], "QK7M2P")
	i_khoa = m.vet.index(("sql", "select name from `tabVagabond Ho So CRM`"))
	i_chen = m.vet.index(("insert", "Vagabond Voucher"))
	dung("khoá dòng hồ sơ trước khi cấp", i_khoa < i_chen)
	kq2 = m.chay(tv.nhan_qua, quay="TCV")
	la("bấm lại: đúng mã cũ", (kq2["ma"], kq2["cu"]), ("QK7M2P", 1))
	la("vẫn một mã", len(m.vc), 1)


@ca("v621 nhận quà: một số một lần, kể cả mã đã dùng, đã huỷ, hay cấp cho hồ sơ khách khác cùng số")
def _mot_lan():
	for tt, mong in (("Da dung", "da_dung"), ("Da huy", "da_huy")):
		m = Moi(vc={"QOLD12": D(ctkm=km.CTKM_QUA, danh_cho="KL0412", trang_thai=tt, han_dung=D8(2026, 10, 20), sdt="0909123412")})
		m.hs["KL0412"]["qua_chao_mung"] = ""
		kq = m.chay(tv.nhan_qua)
		la("%s: trả mã cũ, không cấp mới" % tt, (kq["ma"], kq["cu"], kq["trang_thai"], len(m.vc)), ("QOLD12", 1, mong, 1))
	m = Moi(vc={"QKHAC1": D(ctkm=km.CTKM_QUA, danh_cho="KL0001", trang_thai="Chua dung", han_dung=D8(2026, 11, 2), sdt="0909123412")})
	kq = m.chay(tv.nhan_qua)
	la("cùng số, hồ sơ khác: không cấp mới", (kq["ma"], len(m.vc)), ("QKHAC1", 1))


@ca("v621 nhận quà: thiếu tên, ngày sinh hay đồng ý Zalo thì không cấp; nhân viên, chương trình tắt, chưa đăng nhập cũng không")
def _khong_cap():
	m = Moi(ho_so={"KL0412": D(ten_goi="Lan Anh", dy_zalo="Chưa hỏi")})
	la("chưa đồng ý", (m.chay(tv.nhan_qua)["ly_do"], m.chay(tv.nhan_qua)["thieu"]), ("ho_so_thieu", ["dong_y"]))
	m = Moi(khach=D(name="KL0412", customer_name="Lan", vgb_sinh_nhat=None))
	la("chưa ngày sinh", m.chay(tv.nhan_qua)["thieu"], ["sinh_nhat"])
	m = Moi(ho_so={"KL0412": D(ten_goi="", dy_zalo="Đồng ý")})
	la("chưa tên gọi", m.chay(tv.nhan_qua)["thieu"], ["ten"])
	la("không cấp mã nào", len(m.vc), 0)
	la("nhân viên", Moi(nhan_vien=True).chay(tv.nhan_qua)["ly_do"], "nhan_vien")
	la("chương trình tắt", Moi(km_qua=D(name=km.CTKM_QUA, ten="Q", cach_ma="Ma dung mot lan", bat=0)).chay(tv.nhan_qua)["ly_do"],
		"qua_chua_mo")
	la("chưa có chương trình", Moi(km_qua={}).chay(tv.nhan_qua)["ly_do"], "qua_chua_mo")
	la("chưa đăng nhập", Moi(so=None).chay(tv.nhan_qua)["ly_do"], "chua_dang_nhap")


@ca("v621 lưu hồ sơ: ghi tên gọi, ngày sinh, món hay chọn; đồng ý Zalo qua sổ đồng ý nơi ghi Web; bỏ tích chỉ ghi Từ chối khi trước đó đã Đồng ý")
def _luu():
	m = Moi(ho_so={"KL0412": D(dy_zalo="Chưa hỏi")})
	kq = m.chay(tv.luu_ho_so, json.dumps({"ten": " Lan  Anh", "ngay": "14", "thang": "11", "nam": "", "email": "",
		"so_thich": ["tart", "lạ"], "dong_y_zalo": True}))
	la("được", kq, {"ok": 1})
	h = m.hs["KL0412"]
	la("hồ sơ", (h["ten_goi"], h["so_thich"], h["email_khach"]), ("Lan Anh", '["tart"]', ""))
	la("ngày sinh không năm", m.kh["vgb_sinh_nhat"], D8(tv.NAM_AN, 11, 14))
	la("đồng ý ghi qua sổ, nơi Web, khách tự bấm", m.dong_y, [("KL0412", {"Zalo": "Đồng ý"}, "Web", "Guest")])
	m.dong_y.clear()
	m.chay(tv.luu_ho_so, {"ten": "Lan Anh", "dong_y_zalo": True})
	la("đã đồng ý, lưu lại không ghi trùng", m.dong_y, [])
	m.chay(tv.luu_ho_so, {"ten": "Lan Anh", "dong_y_zalo": False})
	la("rút đồng ý ghi Từ chối", m.dong_y, [("KL0412", {"Zalo": "Từ chối"}, "Web", "Guest")])
	m2 = Moi(ho_so={"KL0412": D(dy_zalo="Chưa hỏi")})
	m2.chay(tv.luu_ho_so, {"ten": "Lan Anh", "dong_y_zalo": False})
	la("chưa từng đồng ý thì bỏ tích không ghi gì", m2.dong_y, [])
	for dat, ly in (({"ten": ""}, "thieu_ten"), ({"ten": "Lan", "ngay": "31", "thang": "4"}, "ngay_sinh_khong_dung"),
			({"ten": "Lan", "email": "x@y"}, "email_khong_dung"), ({"ten": "Lan", "anh_mau": "../../etc"}, "anh_khong_dung")):
		la("chặn %s" % ly, Moi().chay(tv.luu_ho_so, dat)["ly_do"], ly)
	la("chưa đăng nhập", Moi(so=None).chay(tv.luu_ho_so, {"ten": "Lan"})["ly_do"], "chua_dang_nhap")


@ca("v621 chương trình Quà chào mừng: dựng một lần đúng 20.000đ, mã dùng một lần; đã có thì không ghi đè bản quản lý đã sửa")
def _dung_ctkm():
	chen = []
	fr = tv.frappe

	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
	with um.patch.object(fr.db, "exists", lambda dt_, ten=None: False), um.patch.object(fr, "get_doc", lambda d: Doc(d)):
		la("dựng", tv.dam_bao_ctkm_qua(), True)
	la("đúng chương trình", {k: chen[0][k] for k in ("ma_ctkm", "kieu_giam", "gia_tri", "cach_ma", "doi_tuong", "bat")},
		{"ma_ctkm": km.CTKM_QUA, "kieu_giam": "So tien", "gia_tri": 20000, "cach_ma": "Ma dung mot lan", "doi_tuong": "Moi khach", "bat": 1})
	chen.clear()
	with um.patch.object(fr.db, "exists", lambda dt_, ten=None: True), um.patch.object(fr, "get_doc", lambda d: Doc(d)):
		la("đã có", tv.dam_bao_ctkm_qua(), False)
	la("không ghi gì", chen, [])
	dung("migrate gọi dựng chương trình", "thanh_vien.dam_bao_ctkm_qua()" in (GOC / "patches/dong_bo_cau_truc.py").read_text())


@ca("v621 lượt tính nhóm đêm của CRM KHÔNG ghi đè phần khách tự khai trên trang thành viên")
def _crm_dem():
	cay = ast.parse((GOC / "crm.py").read_text())
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "tinh_nhom_dem")
	cot = next(n for n in ast.walk(ham) if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "cot")
	ds = ast.literal_eval(cot.value)
	for c in tv.COT_TV + ("anh_mau", "qua_luc", "qua_quay"):
		if c == "dy_zalo":
			continue
		dung("lượt đêm không đụng %s" % c, c not in ds)
	js = json.loads((GOC / "vagabond/doctype/vagabond_ho_so_crm/vagabond_ho_so_crm.json").read_text())
	co = {f["fieldname"]: f for f in js["fields"]}
	for c in ("ten_goi", "email_khach", "so_thich", "anh_dai_dien", "anh_mau", "qua_chao_mung", "qua_luc", "qua_quay"):
		dung("hồ sơ CRM có ô %s" % c, c in co and c in js["field_order"])
		dung("ô %s chỉ đọc trên Desk" % c, co.get(c, {}).get("read_only") == 1)
	dung("đẩy mốc modified", js["modified"] >= "2026-10-30")


@ca("v621 khách đăng nhập OTP là Guest: trang thành viên đọc được tiến độ hạng mà KHÔNG cần quyền bán hàng (Codex PR #517 vòng 8)")
def _khach_guest():
	# Chạy THẬT tv._tien_do -> khach_hang (cổng _kiem_quyen_ban thật, vai Guest).
	# Không vá _kiem_quyen_ban: chính nó là thứ làm trang thành viên đổ.
	# CI không có requests mà ban_hang.py nạp cứng ở đầu tệp: chỉ thay bằng bản
	# rỗng khi máy thiếu, và chỉ trong ca này.
	try:
		import requests as rq
	except ImportError:
		rq = types.ModuleType("requests")
	with um.patch.dict(sys.modules, {"requests": rq}):
		_khach_guest_chay()


def _khach_guest_chay():
	from vagabond import khach_hang
	fr = tv.frappe
	bang = [D(name="EXPLORER", ten_hang="Explorer", loai="Theo chi tieu", chi_tieu_tu=0, so_thang_xet=12),
		D(name="VOYAGER", ten_hang="Voyager", loai="Theo chi tieu", chi_tieu_tu=10000000, so_thang_xet=12)]

	def get_all(dt_, **k):
		return [D(h) for h in bang] if dt_ == "Vagabond Hang Khach" else []

	def sql(q, *a, **k):
		return [D(customer="KL0412", tien=4000000, so_don=3, gan_nhat=HN)] if "Sales Invoice" in q else []
	with um.patch.object(fr, "get_roles", lambda *a: ["Guest"]), um.patch.object(fr, "get_all", get_all), \
			um.patch.object(fr.db, "sql", sql), \
			um.patch.object(fr.db, "get_value", lambda dt_, ten=None, cot=None, *a, **k: "Voyager"):
		try:
			kq = tv._tien_do("KL0412")
		except Exception as e:  # noqa: BLE001
			kq = {"loi": str(e)}
		la("Guest đọc được tiến độ", kq, {"da_mua": 4000000.0, "so_thang": 12, "hang_tiep": "Voyager",
			"con_thieu": 6000000.0, "ty_le": 0.4})
		# Màn nhân viên vẫn giữ cổng quyền bán hàng.
		try:
			khach_hang.ds_hang()
			chan = False
		except Exception:
			chan = True
		dung("API bảng hạng cho nhân viên vẫn chặn Guest", chan)
	# Chốt cả lối: trang thành viên (khách là Guest) không gọi hàm nào của mô đun
	# khác mà thân hàm có cổng quyền nhân viên.
	cay = ast.parse((GOC / "thanh_vien.py").read_text())
	goi = {(ast.unparse(n.func.value), n.func.attr) for n in ast.walk(cay)
		if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)}
	# Cả hàm nạp thẳng tên: from vagabond.zalo_kich_ban import ctkm_phat_duoc.
	goi |= {(n.module.split(".")[-1], a.name) for n in ast.walk(cay)
		if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("vagabond.") for a in n.names}
	dung("dò được cả lời gọi nạp thẳng tên", ("zalo_kich_ban", "ctkm_phat_duoc") in goi)
	co_cong = []
	for mo, ham in sorted(goi):
		tep = GOC / (mo + ".py")
		if mo in ("frappe", "tv", "self") or not tep.exists():
			continue
		for n in ast.parse(tep.read_text()).body:
			if isinstance(n, ast.FunctionDef) and n.name == ham and "_kiem_quyen" in ast.unparse(n):
				co_cong.append("%s.%s" % (mo, ham))
	la("không gọi API có cổng quyền nhân viên", co_cong, [])
