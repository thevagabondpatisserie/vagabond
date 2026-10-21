# -*- coding: utf-8 -*-
"""Ca kiem v607: doi kho phu trach tung nguoi ngay tren app (De 21/10/2026).

De bao: nhan vien vao "Hang chuyen ve kho toi" thi may bao "chua khai Kho phu
trach... Bao anh Viet khai giup o man Quan ly nguoi dung", ma man do KHONG co
cho nao khai, chi sua duoc tren Desk. Nay co nut "Doi kho phu trach" tren ho
so nguoi dung, va cau bao chi dung duong.

Cac ca goi THANG ham that (nguoi_dung.dat_kho_phu_trach, chi_tiet) voi mot lop
Frappe gia, nhu thu_bo_phan_583.
"""

import io
import os
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

for _ten in ("frappe.core", "frappe.core.doctype", "frappe.core.doctype.user",
		"frappe.core.doctype.user.user"):
	if _ten not in sys.modules:
		sys.modules[_ten] = types.ModuleType(_ten)
if not hasattr(sys.modules["frappe.core.doctype.user.user"], "User"):
	sys.modules["frappe.core.doctype.user.user"].User = type("User", (object,), {})
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import nguoi_dung as nd  # noqa: E402

GOI_TEP = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KHO = [
	{"name": "Tất cả kho - TV", "is_group": 1, "disabled": 0},
	{"name": "Kho Hàng Hoá - TV", "is_group": 0, "disabled": 0},
	{"name": "Kho Cửa Hàng TCV - TV", "is_group": 0, "disabled": 0},
	{"name": "Kho Cũ - TV", "is_group": 0, "disabled": 1},
]
EMAIL = "de@vagabond.vn"


class _Meta(object):
	def __init__(self, truong):
		self.truong = set(truong)

	def has_field(self, f):
		return f in self.truong


class _Site(object):
	def __init__(self, vai_toi=("Quản lý người dùng",), co_o=True, kho_dang=""):
		self.user = {EMAIL: {"name": EMAIL, "full_name": "Dễ", "custom_kho_phu_trach": kho_dang}}
		self.vai_toi = set(vai_toi)
		self.co_o = co_o
		self.ghi = []
		self.luu_doc = 0

	def get_value(self, dt, ten, truong, as_dict=False, **k):
		if dt != "User" or ten not in self.user:
			return None
		r = self.user[ten]
		if isinstance(truong, (list, tuple)):
			d = {f: r.get(f) for f in truong}
			return types.SimpleNamespace(**d, get=d.get) if as_dict else [r.get(f) for f in truong]
		return r.get(truong)

	def set_value(self, dt, ten, truong, gt, update_modified=True):
		self.ghi.append((dt, ten, truong, gt, update_modified))
		self.user[ten][truong] = gt

	def get_all(self, dt, filters=None, pluck=None, **k):
		if dt != "Warehouse":
			return []
		ra = [r for r in KHO if all(r.get(f) == v for f, v in (filters or {}).items())]
		return [r[pluck] for r in ra] if pluck else ra

	def vao(self):
		fr = sys.modules["frappe"]
		db = types.SimpleNamespace(get_value=self.get_value, set_value=self.set_value)

		def _save(*a, **k):
			self.luu_doc += 1

		truong = ["custom_kho_phu_trach"] if self.co_o else []
		return [
			um.patch.object(fr, "db", db),
			um.patch.object(fr, "get_all", self.get_all),
			um.patch.object(fr, "get_roles", lambda *a: list(self.vai_toi), create=True),
			um.patch.object(fr, "get_meta", lambda dt: _Meta(truong), create=True),
			um.patch.object(fr, "get_doc", lambda *a, **k: types.SimpleNamespace(save=_save, insert=lambda **kk: None)),
			um.patch.object(fr.session, "user", "quanly@vgb"),
		]


def _chay(site, ham):
	ps = site.vao()
	for p in ps:
		p.start()
	try:
		return ham()
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v607 kho phu trach: phep thuan tach chuoi, ten ngan, lua chon")
def _thuan():
	la("tach dau phay, bo trung va khoang trang", nd.tach_kho(" Kho A - TV , Kho B - TV,Kho A - TV,, "), ["Kho A - TV", "Kho B - TV"])
	la("rong", nd.tach_kho(None), [])
	la("ten ngan bo duoi TV", nd.ten_ngan_kho("Kho Hàng Hoá - TV"), "Kho Hàng Hoá")
	la("ten ngan bo duoi TVD", nd.ten_ngan_kho("Kho Hàng Hoá - TVD"), "Kho Hàng Hoá")
	la("khong duoi giu nguyen", nd.ten_ngan_kho("Kho Lab"), "Kho Lab")
	ds = nd.cac_kho_chon(["Kho Hàng Hoá - TV"])
	la("khoa la ten day du, nhan khong duoi, co giai thich", (ds[0]["k"], ds[0]["nhan"], bool(ds[0]["mo_ta"])),
		("Kho Hàng Hoá - TV", "Kho Hàng Hoá", True))


@ca("v607 kho phu trach: doi cho De hai kho, ghi thang o User cach nhau dau phay, khong luu ca tai lieu")
def _doi():
	site = _Site()
	kq = _chay(site, lambda: nd.dat_kho_phu_trach(EMAIL, '["Kho Hàng Hoá - TV", "Kho Cửa Hàng TCV - TV"]'))
	la("o tren User", site.user[EMAIL]["custom_kho_phu_trach"], "Kho Hàng Hoá - TV, Kho Cửa Hàng TCV - TV")
	la("khong luu ca tai lieu User (bay bo vai mau)", site.luu_doc, 0)
	dung("khong doi moc sua", all(g[4] is False for g in site.ghi))
	dung("cau bao ten kho khong duoi", "Kho Hàng Hoá, Kho Cửa Hàng TCV" in kq["loi_nhan"] and " - TV" not in kq["loi_nhan"])
	# Chuoi cach dau phay (nhu go tay) cung nhan.
	site = _Site()
	_chay(site, lambda: nd.dat_kho_phu_trach(EMAIL, "Kho Hàng Hoá - TV"))
	la("mot kho", site.user[EMAIL]["custom_kho_phu_trach"], "Kho Hàng Hoá - TV")
	# Bo het.
	site = _Site(kho_dang="Kho Hàng Hoá - TV")
	kq = _chay(site, lambda: nd.dat_kho_phu_trach(EMAIL, "[]"))
	la("bo het thi o rong", site.user[EMAIL]["custom_kho_phu_trach"], "")
	dung("cau bao noi khong kho nao", "không kho nào" in kq["loi_nhan"])


@ca("v607 kho phu trach: kho khong co that, la nhom hay dang tat bi tu choi, khong ghi")
def _sai():
	for kho in ("Kho Ma - TV", "Tất cả kho - TV", "Kho Cũ - TV", "Kho Hàng Hoá - TV, Kho Ma - TV"):
		site = _Site()
		try:
			_chay(site, lambda: nd.dat_kho_phu_trach(EMAIL, kho))
			dung("phai tu choi %r" % kho, False)
		except Exception as e:
			dung("cau bao chi duong %r: %s" % (kho, e), "Chọn kho trong danh sách" in str(e))
		la("khong ghi %r" % kho, site.ghi, [])


@ca("v607 kho phu trach: chi nguoi quan ly nguoi dung moi doi duoc; site chua co o thi bao")
def _quyen():
	site = _Site(vai_toi=("Stock User",))
	try:
		_chay(site, lambda: nd.dat_kho_phu_trach(EMAIL, "Kho Hàng Hoá - TV"))
		dung("phai bi chan", False)
	except Exception as e:
		dung("cau bao quyen", "không có quyền" in str(e))
	la("khong ghi gi", site.ghi, [])
	site = _Site(co_o=False)
	try:
		_chay(site, lambda: nd.dat_kho_phu_trach(EMAIL, "Kho Hàng Hoá - TV"))
		dung("phai bao thieu o", False)
	except Exception as e:
		dung("cau bao thieu o", "chưa có ô Kho phụ trách" in str(e))


@ca("v607 kho phu trach: ho so nguoi dung tra kho dang khai va danh sach kho chon duoc")
def _chi_tiet():
	site = _Site(kho_dang="Kho Hàng Hoá - TV")
	with um.patch.object(nd, "_vai_cua", lambda e: {"Stock User"}), \
			um.patch.object(nd, "_vai_co_that", lambda: {"Stock User"}), \
			um.patch.object(nd, "_goi_da_luu", lambda e: None), \
			um.patch.object(nd, "_co_o_bo_phan", lambda: False):
		d = _chay(site, lambda: nd.chi_tiet(EMAIL))
	la("kho dang khai", d["kho_phu_trach"], ["Kho Hàng Hoá - TV"])
	la("chon duoc: kho that, khong nhom, khong tat", [x["k"] for x in d["kho_chon_duoc"]], ["Kho Hàng Hoá - TV", "Kho Cửa Hàng TCV - TV"])
	# Site chua co o thi khong moi doi (khong ve nut).
	site = _Site(co_o=False)
	with um.patch.object(nd, "_vai_cua", lambda e: set()), um.patch.object(nd, "_vai_co_that", lambda: set()), \
			um.patch.object(nd, "_goi_da_luu", lambda e: None), um.patch.object(nd, "_co_o_bo_phan", lambda: False):
		d = _chay(site, lambda: nd.chi_tiet(EMAIL))
	la("khong co o thi khong chon duoc", d["kho_chon_duoc"], [])


@ca("v607 kho phu trach: cau bao chua khai kho chi dung nut tren app, khong con bao anh Viet")
def _cau_bao():
	from vagabond import xuat_kho
	dung("chi duong toi nut Doi kho phu trach", "Đổi kho phụ trách" in xuat_kho.CHI_DUONG_KHO)
	for tep in ("xuat_kho.py", "nhan_dieu_chuyen.py"):
		with io.open(os.path.join(GOI_TEP, tep), encoding="utf-8") as f:
			src = f.read()
		dung("%s khong con bao anh Viet khai giup" % tep, "Báo anh Việt khai giúp" not in src and "báo anh Việt khai thêm" not in src)
	# Man nguoi dung co nut, goi dung cua, va ten kho ngan cung phep voi may chu.
	with io.open(os.path.join(GOI_TEP, "public", "js", "bep", "20-danh-muc-quyen.js"), encoding="utf-8") as f:
		js = f.read()
	dung("co nut Doi kho phu trach", 'id="qndDoiKho"' in js and "Đổi kho phụ trách" in js)
	dung("goi dat_kho_phu_trach", "vagabond.nguoi_dung.dat_kho_phu_trach" in js)
	dung("hien dong Kho phu trach", "o('Kho phụ trách'" in js)
