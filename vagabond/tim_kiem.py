# -*- coding: utf-8 -*-
"""MOT NGUON cho moi o tim trong app (anh Viet 07/10/2026).

Anh Viet: "phai sua o backend cho moi o tim kiem trong app, go co dau, khong
dau, dau phay, cham, ma,... go kieu nao cung phai ra cai mon ay".

Ca that 06/10/2026: De go "chocolatine mini" trong Phieu yeu cau san xuat thi
khong ra "Bánh Chocolatine, Mini size" (BANU00050), trong khi man Ton kho van
ra. Ly do: hau het o tim gui NGUYEN CUM chu vao phep `like '%...%'` cua co so
du lieu, nen dau phay giua ten, thu tu tu, hay dau cach thua deu lam hut.

Do tren site that (06/10/2026) ve phep `like` cua MariaDB (utf8mb4 _ci):
  - KHONG phan biet hoa thuong va dau thanh: "banh chocolatine" ra
    "Bánh Chocolatine", "BÁNH" ra "Bánh".
  - NHUNG coi "d" va "đ" la hai chu khac nhau: "duong" khong ra "Đường đen".
  - Dau phay, dau cham, dau gach la ky tu that, go khac la hut.

Nen moi o tim di qua DUNG mot phep o day:
  1. Chuan hoa chu go: bo dau, đ thanh d, bo moi ky tu khong phai chu hoac so,
     tach thanh tung TU.
  2. Moi tu deu phai co mat o mot trong cac cot tim (AND giua cac tu, OR giua
     cac cot), khong can dung thu tu, khong can dung dau cau.
  3. Tu nao co chu "d" thi thu ca "đ" o vi tri do, vi co so du lieu khong tu
     coi hai chu la mot.
  4. Tu NGAN (mot hai ky tu) phai dung DAU mot tieng, khong duoc nam giua
     long tu khac. Neu khong thi go "banh o" ra ca "Croissant" vi chu "o" nam
     trong do, va o tim khong loc gi (bai hoc cua xuat_kho._co_tu, 2026).
     Tu tu ba ky tu tro len thi khop o bat ky dau, de go "wc000" van ra.

Phep THUAN (chuan, cac_tu, khop, cac_mau, sql) khong cham Frappe, kiem thu
khong can site. Ban JS cung quy tac la vgbChuan / vgbKhop trong 00-nen.js;
ca kiem chot hai ben cho cung ket qua tren cung bo mau.
"""

import re
import unicodedata

import frappe

# Go dai qua thi chi lay chung nay tu dau, de cau lenh khong phinh vo han.
SO_TU_TOI_DA = 8
# Moi tu toi da chung nay bien the d/đ (2 mu so chu d, cat o 4 chu d).
SO_MAU_TOI_DA = 16

_KHONG_CHU_SO = re.compile(r"[^a-z0-9]+")
# Tu ngan hon muc nay phai dung dau mot tieng (xem diem 4 o dau tep).
TU_NGAN = 3
# Ky tu co the dung ngay truoc mot tieng trong ten goc chua chuan hoa.
_TRUOC_TIENG = (" ", "(", "-", ",", "/", ".", "+")
_TEN_COT = re.compile(r"^[a-z_][a-z0-9_]*$")
_TEN_DT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _\-]*$")
# Dau ngan cach bo di khi so ban "dinh lien" o may chu (Codex #450, vong 1):
# go "chocolatinemini" phai ra "Bánh Chocolatine, Mini size" giong may khach.
# Ky tu nao khong co trong danh sach van la ky tu that o buoc hoi co so du lieu
# (it gap trong ten mon); buoc so lai bang `khop` van coi no la dau ngan cach.
_NGAN_CACH = (" ", ",", ".", "-", "/", "(", ")", "_", "+", "&", ":", ";", "'", "\"",
	"\t", "\n", "–", "—")
# Moi luot hoi ung vien doc toi da chung nay dong (Codex #450, vong 1): khong
# quet ca bang chi vi mot chu ngan.
GIOI_HAN_DOC = 5000
# Kieu o duoc phep lam cot tim tu man hinh (xem `tim`).
KIEU_O_TIM = {"Data", "Link", "Dynamic Link", "Select", "Small Text", "Text", "Read Only", "Phone"}


# ------------------------------------------------------------ phep thuan


def chuan(s):
	"""Chu ve dang so sanh: thuong, bo dau, đ thanh d, chi con chu va so."""
	s = unicodedata.normalize("NFD", str(s if s is not None else ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	s = s.replace("đ", "d").replace("Đ", "D").lower()
	return " ".join(_KHONG_CHU_SO.sub(" ", s).split())


def cac_tu(q):
	"""Tach chu go thanh danh sach tu, bo trung, giu thu tu, toi da 8 tu."""
	ra = []
	for t in chuan(q).split():
		if t not in ra:
			ra.append(t)
	return ra[:SO_TU_TOI_DA]


def khop(chu, q):
	"""Chu `chu` co khop o tim `q` khong. Moi tu go ra deu phai co mat.

	`chu` co the la mot chuoi hoac danh sach chuoi (ten, ma, ma vach...).
	Go rong thi luon khop.
	"""
	tu = cac_tu(q)
	if not tu:
		return True
	if isinstance(chu, (list, tuple)):
		chu = " ".join(str(x) for x in chu if x is not None)
	k = chuan(chu)
	# Them ban dinh lien (bo dau cach) de go "chocolatinemini" van ra.
	k2 = k.replace(" ", "")
	mot_tu = len(tu) == 1
	return all(_co_tu(k, k2, t, mot_tu) for t in tu)


def _co_tu(k, k2, t, mot_tu=False):
	"""Mot tu co mat trong chu da chuan hoa khong.

	Tu tu 3 ky tu: o bat ky dau (ca ban dinh lien).
	Tu ngan (1-2 ky tu):
	  - go MOT tu (dang go do): dau mot tieng la du, "ch" ra "Chocolatine";
	  - go NHIEU tu: tu ngan co chu cai phai la NGUYEN mot tieng. Go "water bt"
	    khong duoc ra moi giao dich ma ACC-BTN..., go "banh o" khong ra
	    "Bánh Ống". Tu ngan toan so van khop dau tieng: "12" ra "12cm".
	"""
	if len(t) >= TU_NGAN:
		return (t in k) or (t in k2)
	duoi = "" if (mot_tu or t.isdigit()) else r"(?![a-z0-9])"
	return re.search(r"(?<![a-z0-9])" + re.escape(t) + duoi, k) is not None


def cac_mau(tu):
	"""Cac mau `like` cho mot tu, gom ca bien the đ o moi vi tri chu d.

	Tu ngan (duoi 3 ky tu) chi khop o DAU mot tieng: dau chuoi, hoac ngay sau
	dau cach hay dau cau.
	"""
	tu = str(tu or "")
	vi_tri = [i for i, c in enumerate(tu) if c == "d"][:4]
	ra = []
	for bit in range(1 << len(vi_tri)):
		cs = list(tu)
		for j, p in enumerate(vi_tri):
			if bit & (1 << j):
				cs[p] = "đ"
		v = "".join(cs)
		if len(tu) >= TU_NGAN:
			mau = ["%" + v + "%"]
		else:
			mau = [v + "%"] + ["%" + p + v + "%" for p in _TRUOC_TIENG]
		for m in mau:
			if m not in ra:
				ra.append(m)
		if bit + 1 >= SO_MAU_TOI_DA:
			break
	return ra


def sql(q, cot, ten="tk"):
	"""Dieu kien SQL cho o tim. Tra ve (chuoi, tham_so).

	`cot` la danh sach bieu thuc cot do MA NGUON viet (vd "i.item_name"),
	khong bao gio lay tu man hinh. Go rong thi tra ("", {}) de ben goi bo
	qua dieu kien.
	"""
	tu = cac_tu(q)
	if not tu or not cot:
		return "", {}
	tham = {}
	nhom = []
	for i, t in enumerate(tu):
		hoac = []
		dai = len(t) >= TU_NGAN
		for j, m in enumerate(cac_mau(t)):
			k = "%s%d_%d" % (ten, i, j)
			tham[k] = m
			for c in cot:
				# Tu dai so tren ban da bo dau ngan cach, nen go dinh lien
				# "chocolatinemini" van ra "Chocolatine, Mini". Tu ngan giu
				# nguyen cot de con biet dau tieng.
				hoac.append("%s like %%(%s)s" % (_gon(c, ten) if dai else c, k))
		if dai:
			tham.update(_tham_ngan(ten))
		nhom.append("(" + " or ".join(hoac) + ")")
	return "(" + " and ".join(nhom) + ")", tham


def _gon(bieu_thuc, ten):
	"""Bieu thuc SQL bo moi dau ngan cach khoi mot cot (tham so co ten)."""
	e = bieu_thuc
	for i in range(len(_NGAN_CACH)):
		e = "replace(%s, %%(%s_n%d)s, '')" % (e, ten, i)
	return e


def _tham_ngan(ten):
	return {"%s_n%d" % (ten, i): s for i, s in enumerate(_NGAN_CACH)}


def sql_ung_vien(doctype, truong, cot, mau, trong=None, gioi_han=GIOI_HAN_DOC, ten="tg"):
	"""Cau doc ung vien cho MOT tu dai: cot da bo dau ngan cach `like` mau.

	`doctype`, `truong`, `cot` phai la ten that (soat dang o day, khong bao gio
	noi chuoi go vao cau lenh). Tra ve (chuoi, tham_so).
	"""
	if not _TEN_DT.match(str(doctype or "")):
		raise ValueError("doctype khong hop le: %r" % (doctype,))
	for c in list(truong) + list(cot):
		if not _TEN_COT.match(str(c or "")):
			raise ValueError("cot khong hop le: %r" % (c,))
	tham = _tham_ngan(ten)
	hoac = []
	for j, m in enumerate(mau):
		k = "%s_m%d" % (ten, j)
		tham[k] = m
		for c in cot:
			hoac.append("%s like %%(%s)s" % (_gon("`%s`" % c, ten), k))
	dk = "(" + " or ".join(hoac) + ")"
	if trong is not None:
		tham[ten + "_trong"] = tuple(trong)
		dk += " and `name` in %%(%s_trong)s" % ten
	return ("select %s from `tab%s` where %s limit %d" % (
		", ".join("`%s`" % c for c in truong), doctype, dk, int(gioi_han)), tham)


def cot_hop_le(cot, co_that):
	"""Loc danh sach cot: chi giu ten cot dung dang va co that tren doctype."""
	ra = []
	for c in cot or []:
		c = str(c or "").strip()
		if _TEN_COT.match(c) and c in co_that and c not in ra:
			ra.append(c)
	return ra


# ------------------------------------------------------------ cham Frappe


def ten_khop(doctype, q, cot, gioi_han=2000):
	"""Ten cac ban ghi khop o tim. None neu khong go gi (de ben goi bo loc).

	Hai buoc:
	  1. Moi TU mot luot frappe.get_all voi or_filters tren cac cot (va moi
	     bien the d/đ), lay GIAO cac luot. Tu dai nhat hoi truoc, cac luot sau
	     chi hoi trong tap da khop. Buoc nay rong tay (tu ngan chi can dung
	     dau mot tieng).
	  2. So lai tung dong bang `khop` (cung luat voi may khach) tren chinh cac
	     cot da doc, de ket qua dung y het ban JS: tu ngan phai nguyen tieng khi
	     go nhieu tu, va moi tu deu phai co mat.

	Doc KHONG soat quyen (giong mot cau SQL): ben goi phai dua ket qua qua
	frappe.get_list / get_all cung bo loc quyen cua minh, khong tra thang
	danh sach nay ra man hinh.
	"""
	tu = cac_tu(q)
	if not tu or not cot:
		return None
	con, gia_tri = None, {}
	truong = ["name"] + [c for c in cot if c != "name"]
	for t in sorted(tu, key=len, reverse=True):
		# Tap da khop con nho thi hoi trong tap do cho nhe; lon qua thi hoi ca
		# bang roi giao trong Python, tranh cau "in" dai vai chuc nghin ma.
		trong = sorted(con) if con is not None and len(con) <= 3000 else None
		if len(t) >= TU_NGAN:
			# Tu dai: so tren cot da bo dau ngan cach (go dinh lien van ra).
			# get_all khong nhan bieu thuc tren cot nen di cau SQL soat dang.
			cau, tham = sql_ung_vien(doctype, truong, cot, cac_mau(t), trong)
			ds = frappe.db.sql(cau, tham, as_dict=True)
		else:
			hoac = [[c, "like", m] for m in cac_mau(t) for c in cot]
			loc = {"name": ["in", trong]} if trong is not None else None
			ds = frappe.get_all(doctype, filters=loc, or_filters=hoac, fields=truong,
				limit_page_length=GIOI_HAN_DOC)
		for r in ds:
			gia_tri.setdefault(r["name"], [r.get(c) for c in truong])
		ten = {r["name"] for r in ds}
		con = ten if con is None else con & ten
		if not con:
			break
	ra = sorted(m for m in (con or []) if khop(gia_tri.get(m) or [m], q))
	if doctype == "Item":
		# Go ma vach (in tren tem, quet khong duoc thi go tay) cung phai ra mon.
		gon = "".join(tu)
		if len(gon) >= 4:
			for m in frappe.get_all("Item Barcode", filters={"barcode": ["like", "%" + gon + "%"]},
					pluck="parent", limit_page_length=50):
				if m not in ra:
					ra.append(m)
	return ra[: int(gioi_han or 2000)]


def loc_ten(doctype, q, cot, gioi_han=2000):
	"""Mot bo loc ["name", "in", [...]] de ghep vao `filters` cua get_all.

	Thay cho kieu cu `or_filters={cot: ["like", "%" + q + "%"]}`. Go rong thi
	tra None, ben goi khong them gi.
	"""
	ds = ten_khop(doctype, q, cot, gioi_han)
	if ds is None:
		return None
	return ["name", "in", ds or ["\x00khong-co"]]


def them_loc(filters, doctype, q, cot, gioi_han=2000):
	"""Ghep bo loc tim vao `filters` (dict hoac list). Tra ve filters moi."""
	f = loc_ten(doctype, q, cot, gioi_han)
	if f is None:
		return filters
	if not filters:
		return [f]
	if isinstance(filters, dict):
		ra = [[k] + (list(v) if isinstance(v, (list, tuple)) else ["=", v]) for k, v in filters.items()]
	else:
		ra = list(filters)
	ra.append(f)
	return ra


def _cot_tim_mac_dinh(meta):
	"""Cot tim khi man hinh khong noi: ten, cac o tieu de va o tim nhanh."""
	cot = ["name"]
	for c in [meta.title_field] + [x.strip() for x in (meta.search_fields or "").split(",")]:
		if c and c not in cot:
			cot.append(c)
	return cot


def _tham_so(v, mac_dinh=None):
	import json

	if v is None or v == "":
		return mac_dinh
	if isinstance(v, str):
		try:
			return json.loads(v)
		except ValueError:
			return [x.strip() for x in v.split(",") if x.strip()]
	return v


@frappe.whitelist()
def tim(doctype, tu_khoa="", cot=None, fields=None, filters=None, gioi_han=100, order_by=None):
	"""Ban thay cho getList(..., or_filters like) cua app. Co soat quyen doc.

	Doctype, cot, fields do man hinh gui len nen:
	  - quyen doc do frappe.get_list soat (giong getList cu);
	  - cot tim chi nhan ten cot CO THAT tren doctype, khong lot SQL vao duoc.
	"""
	# Soat quyen doc TRUOC buoc hoi ung vien (Codex #450, vong 1): buoc do
	# khong soat quyen, nguoi khong duoc doc doctype thi dung o day.
	if not frappe.has_permission(doctype, "read"):
		frappe.throw("Bạn không có quyền xem %s." % doctype, frappe.PermissionError)
	meta = frappe.get_meta(doctype)
	# Chi cho tim tren o CHU thuong, quyen cap 0. Khong cho do tren o mat khau
	# hay o quyen cao: buoc doc ten khop khong soat quyen, do tren o do la mo
	# mot duong doan gia tri qua so dong tra ve.
	co_that = {"name"} | {
		d.fieldname for d in meta.fields
		if d.fieldtype in KIEU_O_TIM and not int(d.permlevel or 0)
	}
	cot = cot_hop_le(_tham_so(cot, None) or _cot_tim_mac_dinh(meta), co_that)
	loc = them_loc(_tham_so(filters, None), doctype, tu_khoa, cot, gioi_han=5000)
	return frappe.get_list(
		doctype,
		filters=loc,
		fields=_tham_so(fields, ["name"]),
		order_by=order_by or None,
		limit_page_length=min(int(gioi_han or 100), 1000),
	)
