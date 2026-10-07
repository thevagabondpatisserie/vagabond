# -*- coding: utf-8 -*-
"""Ca kiem v583: doi bo phan tung nguoi ngay tren app.

Anh Viet 07/10/2026: chi Le Thi Linh la bep truong Pastry ma he thong ghi bo
phan Bep Baker, nen app chi cho chi thay phieu cua Baker. Tren app khong co
cho nao sua bo phan, phai vao Desk.

Cac ca goi THANG ham that (nguoi_dung.dat_bo_phan, chi_tiet) voi mot lop
Frappe gia, khong do chuoi ma nguon. Rieng danh sach bep ben JS va ben may
chu phai trung nhau thi chi chot duoc bang doc ma nguon.
"""

import io
import os
import re
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

# Department that tren site ngay 07/10/2026 (rut gon), ca nhom va ca dong da tat.
DEP = [
	{"name": "All Departments", "is_group": 1, "disabled": 0},
	{"name": "Bếp Baker - TV", "is_group": 0, "disabled": 0},
	{"name": "Bếp Pastry - TV", "is_group": 0, "disabled": 0},
	{"name": "Kế toán - TV", "is_group": 0, "disabled": 0},
	{"name": "Marketing - TV", "is_group": 0, "disabled": 0},
	{"name": "Accounts - TV", "is_group": 0, "disabled": 1},
	{"name": "Pha chế - TV", "is_group": 0, "disabled": 0},
]


class _Meta(object):
	def __init__(self, truong):
		self.truong = set(truong)

	def has_field(self, f):
		return f in self.truong


class _Site(object):
	"""User va Department gia. Ghi lai MOI lan ghi de ca kiem soi."""

	def __init__(self, vai_toi=("Quản lý người dùng",)):
		self.user = {
			"lethilinh051996@gmail.com": {
				"name": "lethilinh051996@gmail.com", "full_name": "Lê Thị Linh",
				"custom_phong_ban": "Bếp Baker - TV", "custom_bo_phan": None,
			},
		}
		self.vai_toi = set(vai_toi)
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
		if dt != "Department":
			return []
		ra = [r for r in DEP if all(r.get(f) == v for f, v in (filters or {}).items())]
		return [r[pluck] for r in ra] if pluck else ra

	def vao(self):
		fr = sys.modules["frappe"]
		db = types.SimpleNamespace(get_value=self.get_value, set_value=self.set_value)

		def _save(*a, **k):
			self.luu_doc += 1

		return [
			um.patch.object(fr, "db", db),
			um.patch.object(fr, "get_all", self.get_all),
			um.patch.object(fr, "get_roles", lambda *a: list(self.vai_toi), create=True),
			um.patch.object(fr, "get_meta", lambda dt: _Meta(
				["disabled"] if dt == "Department" else ["custom_phong_ban", "custom_bo_phan"]), create=True),
			um.patch.object(fr, "get_doc", lambda *a, **k: types.SimpleNamespace(save=_save, insert=lambda **kk: None)),
			um.patch.object(fr.session, "user", "de@vgb"),
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


# ------------------------------------------------------------ phep thuan

@ca("v583 bo phan: ten ngan bo duoi viet tat, bep nao thay phieu bep nao")
def _thuan():
	# Codex #450 vong 2: goi THANG tep thuan, khong qua lop Frappe gia.
	from vagabond import bo_phan_nguoi as bp
	la("pastry", bp.ten_ngan_bo_phan("Bếp Pastry - TV"), "Bếp Pastry")
	la("khong duoi", bp.ten_ngan_bo_phan("Bếp Pastry"), "Bếp Pastry")
	la("gach trong ten giu nguyen", bp.ten_ngan_bo_phan("Bếp Lab - R&D"), "Bếp Lab - R&D")
	la("bep pastry", bp.bep_cua_bo_phan("Bếp Pastry - TV"), "Bếp Pastry")
	la("bep baker", bp.bep_cua_bo_phan("Bếp Baker - TV"), "Bếp Baker")
	la("lab cu", bp.bep_cua_bo_phan("Bếp Lab - R&D"), "Bếp Lab")
	la("sonneto", bp.bep_cua_bo_phan("Sonneto Lab - TV"), "Bếp Lab")
	la("ke toan khong phai bep", bp.bep_cua_bo_phan("Kế toán - TV"), "")
	dung("mo ta bep noi ro thay phieu", "Bếp Pastry" in bp.mo_ta_bo_phan("Bếp Pastry - TV"))
	la("mo ta khoi", bp.mo_ta_bo_phan("Marketing - TV", {"Marketing": "Khối kinh doanh"}.get), "Khối kinh doanh.")
	la("khong biet khoi", bp.mo_ta_bo_phan("Pha chế - TV"), "Phiếu do người này tạo sẽ ghi bộ phận này.")
	# Ben nguoi_dung ghep cay bo phan that vao cung phep do.
	la("nguoi_dung dung cung phep thuan", nd.ten_ngan_bo_phan, bp.ten_ngan_bo_phan)
	la("mo ta khoi qua cay that", nd.mo_ta_bo_phan("Marketing - TV"), "Khối kinh doanh.")


@ca("v583 bo phan: lua chon co ten co dau va dong giai thich, xep theo cay bo phan")
def _lua_chon():
	from vagabond import bo_phan_nguoi as bp
	ds = bp.cac_bo_phan_chon(["Marketing - TV", "Bếp Pastry - TV", "Pha chế - TV", "Bếp Baker - TV"],
		["Bếp Baker", "Bếp Pastry", "Marketing"])
	la("thu tu theo cay, la ngoai cay xep cuoi", [x["nhan"] for x in ds],
		["Bếp Baker", "Bếp Pastry", "Marketing", "Pha chế"])
	la("khoa la ten day du de luu", ds[1]["k"], "Bếp Pastry - TV")
	dung("moi lua chon co dong giai thich", all(x["mo_ta"] for x in ds))
	dung("khong hien duoi viet tat ra man", not any(" - TV" in x["nhan"] for x in ds))
	la("qua nguoi_dung theo cay that", [x["nhan"] for x in nd.cac_bo_phan_chon(["Marketing - TV", "Bếp Pastry - TV",
		"Pha chế - TV", "Bếp Baker - TV"])], ["Bếp Baker", "Bếp Pastry", "Marketing", "Pha chế"])


@ca("Codex #450 vong 2: phep thuan bo phan nam o tep khong import Frappe")
def _tach_thuan():
	import ast
	with io.open(os.path.join(GOI_TEP, "bo_phan_nguoi.py"), encoding="utf-8") as f:
		cay = ast.parse(f.read())
	nhap = set()
	for n in ast.walk(cay):
		if isinstance(n, ast.Import):
			nhap.update(a.name.split(".")[0] for a in n.names)
		elif isinstance(n, ast.ImportFrom):
			nhap.add((n.module or "").split(".")[0])
	la("chi import thu vien chuan", sorted(nhap), ["re"])
	with io.open(os.path.join(GOI_TEP, "nguoi_dung.py"), encoding="utf-8") as f:
		src = f.read()
	for ten in ("def ten_ngan_bo_phan", "def bep_cua_bo_phan", "_BEP_THAY_PHIEU = ("):
		dung("nguoi_dung khong con ban rieng: " + ten, ten not in src)


# ------------------------------------------------------- ham that, site gia

@ca("v583 bo phan: doi Linh sang Bep Pastry ghi thang o User, khong luu ca tai lieu")
def _doi_linh():
	# Truoc v583 khong co cua nay: tren app khong co cach nao doi bo phan.
	site = _Site()
	kq = _chay(site, lambda: nd.dat_bo_phan("lethilinh051996@gmail.com", "Bếp Pastry - TV"))
	la("o chinh", site.user["lethilinh051996@gmail.com"]["custom_phong_ban"], "Bếp Pastry - TV")
	la("o du lieu cu theo ten ngan", site.user["lethilinh051996@gmail.com"]["custom_bo_phan"], "Bếp Pastry")
	la("khong luu ca tai lieu User (bay bo vai mau)", site.luu_doc, 0)
	dung("khong doi moc sua", all(g[4] is False for g in site.ghi))
	dung("cau bao noi thay phieu Pastry", "Bếp Pastry" in kq["loi_nhan"] and "Lê Thị Linh" in kq["loi_nhan"])


@ca("v583 bo phan: chi nguoi quan ly nguoi dung moi doi duoc")
def _quyen():
	site = _Site(vai_toi=("Bếp phó",))
	try:
		_chay(site, lambda: nd.dat_bo_phan("lethilinh051996@gmail.com", "Bếp Pastry - TV"))
		dung("phai bi chan", False)
	except Exception as e:
		dung("cau bao quyen", "không có quyền" in str(e))
	la("khong ghi gi", site.ghi, [])


@ca("v583 bo phan: bo phan khong co that, la nhom, dang tat hay trong deu bi tu choi")
def _bo_phan_sai():
	for bp in ("Bếp Ma - TV", "All Departments", "Accounts - TV", "", None):
		site = _Site()
		try:
			_chay(site, lambda: nd.dat_bo_phan("lethilinh051996@gmail.com", bp))
			dung("phai tu choi %r" % bp, False)
		except Exception as e:
			dung("cau bao chi duong %r" % bp, "Chọn một bộ phận" in str(e))
		la("khong ghi %r" % bp, site.ghi, [])


@ca("v583 bo phan: ho so nguoi dung tra bo phan hien tai va danh sach chon duoc")
def _chi_tiet():
	site = _Site()
	with um.patch.object(nd, "_vai_cua", lambda e: {"Bếp phó"}), \
			um.patch.object(nd, "_vai_co_that", lambda: {"Bếp phó"}), \
			um.patch.object(nd, "_goi_da_luu", lambda e: None):
		d = _chay(site, lambda: nd.chi_tiet("lethilinh051996@gmail.com"))
	la("bo phan", d["bo_phan"], "Bếp Baker - TV")
	la("ten ngan", d["bo_phan_ten"], "Bếp Baker")
	la("bep", d["bo_phan_bep"], "Bếp Baker")
	la("chon duoc: bo nhom va dong tat", [x["k"] for x in d["bo_phan_chon_duoc"]],
		# Theo thu tu khoi cua cay bo phan: kinh doanh truoc ho tro.
		["Bếp Baker - TV", "Bếp Pastry - TV", "Marketing - TV", "Kế toán - TV", "Pha chế - TV"])


@ca("v583 bo phan: bo vai cua chi Linh sau khi sua la goi Quan ly san xuat")
def _goi_linh():
	vai = {"Bếp phó", "Bộ phận đặt hàng", "Kiểm kê viên", "Manufacturing User",
		"Manufacturing Manager", "Mua hàng R&D"}
	cg = nd.doan_cac_goi(vai, set(nd.VAI_QUAN_LY) | vai)
	la("goi nang nhat", cg[0]["k"] if cg else None, "bepql")


@ca("v583 bo phan: danh sach bep ben app trung ben may chu")
def _bep_hai_ben():
	with io.open(os.path.join(GOI_TEP, "public", "js", "bep", "01-khung-app.js"), encoding="utf-8") as f:
		js = f.read()
	m = re.search(r"var BEPS = \[([^\]]*)\]", js)
	ben_js = set(re.findall(r"'([^']+)'", m.group(1)))
	ben_py = {b for _, b in nd._BEP_THAY_PHIEU}
	la("cung tap bep", sorted(ben_js), sorted(ben_py))
