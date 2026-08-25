# -*- coding: utf-8 -*-
"""Cat quy cach dong goi ra khoi TEN mon.

Viec anh Viet duyet 25/08/2026
------------------------------
Ngay 04/08/2026 Fuji doi tu 1 tui 1 kg sang 2 tui 500 gram. San pham khong
doi, chi bao bi doi, nhung ten mon "Bot tra xanh, Matcha MK4, Tui 1 kg, Fuji"
thanh SAI ngay lap tuc. Anh Viet chot hom do: quy cach song o bang quy doi
don vi, khong song trong ten mon.

Ngay 05/08 ra 1.428 ma, de xuat doi ten cho hang tram ma. Ngay 25/08 anh Viet
duyet: "248 ma cat quy cach anh cung duyet luon, em tien hanh doi ten nhe."

LUAT CAT
========
Ten mon tach theo dau phay. Doan nao SAU doan dau tien ma co dang
"<danh tu bao bi> <so> <don vi>" thi cat. Vi du "Bao 25 kg", "Tui 100 cai",
"Hop 550 gr", "Khoi 2,5kg", "Thung 2000 cai".

Doan DAU TIEN khong bao gio cat: do la ten goc cua mon.

Dau phay thap phan duoc gom lai truoc khi tach: "Can 3,5 kg" bi dau phay cat
lam hai thi doan sau bat dau bang chu so, dan nguoc vao doan truoc.

NHOM HANG BAN RA KHONG DUNG TOI
===============================
Ben ban ra thi con so CHINH LA san pham: banh 110 gram khac banh 150 gram,
hop 8 cai khac set 4 cai. Cat so o do la lam hong ten mon. Nen toan bo nhom
banh, nuoc, tra, ca phe, matcha, qua, combo, dich vu bi loai ra khoi phep
nay. Luat nay anh Viet chot 05/08/2026.

BA MUC AN TOAN
==============
Cat ten la BO thong tin quy cach ra khoi ten, nen truoc khi cat phai chac
thong tin do da nam trong bang quy doi don vi cua mat hang:

    A  don vi da co trong bang quy doi VA he so khop voi so trong ten
    B  don vi co nhung he so lech
    C  chua co don vi do trong bang quy doi

Chi muc A moi cat mac dinh. Muc B va C phai nap hoac sua bang quy doi truoc,
neu cat luon thi mat han thong tin. Muon cat het thi goi voi `ca_ba_muc=1`.

Ca that muc B da bat duoc: NVLT00350 "Bot Lion Custard, Lon 3,5 kg" co dong
quy doi ghi 1 Lon = 35.000 gram, sai gap muoi lan.

KHONG DOI MA HANG
=================
Chi doi TEN. Ma hang la dinh danh, nam tren tem da in, trong hoa don, trong
Pancake va Fabi. Cam tuyet doi doi ma cu, quy tac da dong bang 05/08/2026.
"""

import re

# ---------------------------------------------------------------- phep thuan

DANH_TU_BAO_BI = (
	"Túi", "Bao", "Hộp", "Chai", "Lọ", "Hũ", "Khối", "Thùng", "Gói", "Bình",
	"Can", "Xô", "Khay", "Vỉ", "Cuộn", "Lon", "Bịch", "Keo", "Thanh", "Cây",
	"Set", "Combo", "Pack", "Tuýp", "Ống",
)

DON_VI = (
	"kg", "g", "gr", "gram", "grams", "ml", "l", "lít", "lit", "cc", "cái",
	"chiếc", "viên", "quả", "tép", "lá", "hộp", "túi", "bịch", "gói", "pcs",
	"cm", "mm", "m", "oz", "tờ",
)

_SO = r"\d+(?:[.,]\d+)?"
_DOAN = re.compile(
	r"^\s*(?:%s)\s*%s\s*(?:%s)?\s*(?:x\s*%s\s*(?:%s)?)?\s*$"
	% ("|".join(DANH_TU_BAO_BI), _SO, "|".join(DON_VI), _SO, "|".join(DON_VI)),
	re.IGNORECASE,
)

# Nhom hang ban ra: con so trong ten chinh la san pham, khong duoc cat.
NHOM_BAN_RA = re.compile(
	"bánh|nước|đồ uống|thức uống|combo|quà|set|dịch vụ|trà|cà phê|matcha",
	re.IGNORECASE,
)


def la_doan_quy_cach(doan):
	"""Doan nay co phai quy cach dong goi khong. THUAN."""
	return bool(_DOAN.match(doan or ""))


def gom_dau_phay_thap_phan(cac_doan):
	"""Dan lai nhung doan bi dau phay thap phan cat doi. THUAN.

	"Can 3,5 kg" tach theo dau phay ra thanh "Can 3" va "5 kg". Doan sau bat
	dau bang chu so va doan truoc ket thuc bang chu so thi do la mot so bi
	cat doi, dan nguoc lai.
	"""
	ra = []
	for i, x in enumerate(cac_doan):
		if i and ra and re.match(r"^\s*\d", x or "") \
				and re.search(r"\d\s*$", ra[-1] or ""):
			ra[-1] = ra[-1] + "," + x
		else:
			ra.append(x)
	return ra


def cat_quy_cach(ten):
	"""Cat cac doan quy cach khoi ten mon. THUAN.

	Tra ve (ten_moi, danh sach doan da cat). Khong co gi de cat thi tra
	(ten nguyen ven, danh sach rong).
	"""
	goc = str(ten or "")
	doan = gom_dau_phay_thap_phan(goc.split(","))
	if len(doan) < 2:
		return (goc.strip(), [])
	giu, cat = [], []
	for i, x in enumerate(doan):
		if i and la_doan_quy_cach(x):
			cat.append(x.strip())
		else:
			giu.append(x.strip())
	if not cat:
		return (goc.strip(), [])
	moi = ", ".join(y for y in giu if y)
	moi = re.sub(r"\s{2,}", " ", moi).strip().strip(",").strip()
	return (moi, cat)


def duoc_cat_nhom(nhom):
	"""Nhom hang nay co duoc cat ten khong. THUAN."""
	return not NHOM_BAN_RA.search(str(nhom or ""))


def doc_so(doan):
	"""So dau tien trong doan quy cach. THUAN. None neu khong doc duoc."""
	m = re.search(r"(\d+(?:[.,]\d+)?)", doan or "")
	if not m:
		return None
	return float(m.group(1).replace(",", "."))


def doc_danh_tu(doan):
	"""Danh tu bao bi dung dau doan. THUAN."""
	m = re.match(r"^\s*([^\d]+?)\s*\d", doan or "")
	return (m.group(1).strip() if m else str(doan or "").strip())


def quy_ra_don_vi_goc(doan):
	"""Doan quy cach nay bang bao nhieu don vi kho. THUAN. None neu khong ro.

	Chi doi duoc khi doan co ghi don vi do luong. "Tui 100 cai" thi 100 cai
	la bao nhieu gram khong ai biet, tra None.
	"""
	sl = doc_so(doan)
	if sl is None:
		return None
	m = re.search(r"\d+(?:[.,]\d+)?\s*(kg|g|gr|gram|ml|l|lít|lit|cái|chiếc|"
		r"viên|quả|pcs|tờ|gói|hộp|túi)\b", doan or "", re.IGNORECASE)
	if not m:
		return None
	u = m.group(1).lower()
	if u == "kg":
		return sl * 1000.0
	if u in ("g", "gr", "gram"):
		return sl
	if u in ("l", "lít", "lit"):
		return sl * 1000.0
	if u == "ml":
		return sl
	return sl


def muc_an_toan(doan, bang_quy_doi):
	"""Cat doan nay co mat thong tin khong. THUAN.

	`bang_quy_doi` la {ten don vi: he so}. Tra ve "A", "B" hoac "C".
	"""
	dt = doc_danh_tu(doan)
	hs = quy_ra_don_vi_goc(doan)
	kho = {str(k).strip().lower(): v for k, v in (bang_quy_doi or {}).items()}
	if dt.lower() not in kho:
		return "C"
	if hs is None:
		return "B"
	try:
		if abs(float(kho[dt.lower()]) - hs) < 0.001:
			return "A"
	except (TypeError, ValueError):
		return "B"
	return "B"


# ------------------------------------------------------- phan can Frappe

import frappe
from frappe.utils import cint


def _quyen():
	quyen = {"System Manager", "Item Manager", "Purchase Manager",
		"Giám đốc", "AP Giám đốc"}
	if not quyen & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý danh mục hoặc giám đốc mới đổi tên hàng loạt được.")


def _bang_quy_doi():
	ra = {}
	for d in frappe.get_all("UOM Conversion Detail",
			filters={"parenttype": "Item"},
			fields=["parent", "uom", "conversion_factor"],
			limit_page_length=0):
		ra.setdefault(d.parent, {})[d.uom] = d.conversion_factor
	return ra


def _ke_hoach(gioi_han=3000):
	qd = _bang_quy_doi()
	ra = []
	for it in frappe.get_all("Item", filters={"disabled": 0},
			fields=["name", "item_name", "item_group"],
			order_by="name asc", limit_page_length=gioi_han):
		if not duoc_cat_nhom(it.item_group):
			continue
		moi, cat = cat_quy_cach(it.item_name)
		if not cat or moi == (it.item_name or "").strip() or not moi:
			continue
		ra.append({
			"ma": it.name, "nhom": it.item_group,
			"cu": it.item_name, "moi": moi, "cat": " + ".join(cat),
			"muc": muc_an_toan(cat[0], qd.get(it.name) or {}),
		})
	return ra


@frappe.whitelist()
def xem_truoc(gioi_han=3000):
	"""Danh sach ma se doi ten, tu gi sang gi. CHI DOC."""
	_quyen()
	ke = _ke_hoach(gioi_han)
	dem = {"A": 0, "B": 0, "C": 0}
	for k in ke:
		dem[k["muc"]] = dem.get(k["muc"], 0) + 1
	return {"so_ma": len(ke), "theo_muc": dem, "danh_sach": ke}


@frappe.whitelist()
def doi_ten(chay_that=0, ca_ba_muc=0, gioi_han=3000):
	"""Doi ten hang loat, cat quy cach dong goi khoi ten mon.

	MAC DINH KHONG GHI GI. Phai truyen `chay_that=1` moi ghi.
	MAC DINH CHI CAT MUC A. Muc B va C phai nap hoac sua bang quy doi truoc,
	muon cat het thi truyen `ca_ba_muc=1`.

	Chi doi truong ten mon. KHONG doi ma hang, khong doi nhom, khong dung
	bang quy doi, khong dung mot chung tu nao da lap: chung tu cu giu ban
	sao ten tai thoi diem lap, dung nhu ke toan can.

	Lap lai duoc: ten da cat roi thi lan sau khong con doan quy cach nao de
	cat nua, danh sach tu rong.
	"""
	_quyen()
	chay_that = cint(chay_that)
	ca_ba_muc = cint(ca_ba_muc)
	ke = _ke_hoach(gioi_han)
	lam = ke if ca_ba_muc else [k for k in ke if k["muc"] == "A"]
	hoan = [k for k in ke if k not in lam]
	if not chay_that:
		return {"se_doi": len(lam), "hoan_lai": len(hoan), "da_ghi": 0,
			"danh_sach": lam, "cho_bang_quy_doi": hoan,
			"ghi_chu": "Chạy thử, chưa ghi gì. Gọi lại với chay_that=1 để ghi thật."}
	da = 0
	for k in lam:
		try:
			frappe.db.set_value("Item", k["ma"], "item_name", k["moi"],
				update_modified=False)
			frappe.clear_document_cache("Item", k["ma"])
			da += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"ten_mon: doi ten %s" % k["ma"])
	frappe.db.commit()
	return {"se_doi": len(lam), "hoan_lai": len(hoan), "da_ghi": da,
		"cho_bang_quy_doi": hoan,
		"ghi_chu": "Đã ghi. Các mã hoãn lại cần nạp hoặc sửa bảng quy đổi trước."}
