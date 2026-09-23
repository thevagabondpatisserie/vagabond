# -*- coding: utf-8 -*-
"""Tim don vi tinh trong o chon, khop ca ten luu lan ten da dich.

VI SAO TEP NAY TON TAI (ca that 23/09/2026)
-------------------------------------------
Uyen mo mot Mon, mo bang quy doi don vi, go "Box" thi o chon KHONG ra gi,
chi con moi loi moi "Tao Don vi tinh moi". Trong khi danh muc CO san don vi
ten "Box", dang bat, tao tu 16/07/2026.

Do lai tren site that thi ra: doctype UOM co co `translated_doctype = 1`,
nen o chon cua Frappe khop theo TEN DA DICH chu khong theo ten luu. Site
nay da nap 24.4k dong dich tieng Viet tu 22/07/2026, trong do Box dich la
"Hop", Nos dich la "So", Set dich la "Bo". Vay nen:

  go "Box" -> rong          go "Hop" -> ra ca "Hop" lan "Box"
  go "Nos" -> rong          go "So"  -> ra ca "So"  lan "Nos"
  go "Set" -> rong          go "Bo"  -> ra ca "Bo"  lan "Set"

Cac don vi tu tao bang tieng Viet khong co ban dich nen tim binh thuong,
vi vay loi nay chi dinh dung ba don vi tieng Anh, va rat kho doan ra.

Hau qua that: nhan vien tuong danh muc chua co nen bam "Tao Don vi tinh
moi", the la danh muc sinh trung. Ngay 23/09/2026 danh muc dang co ca
"Hop", "Hop 16", "Hop 24" lan "Box".

CACH CHUA: dang ky standard_queries cho UOM (xem hooks.py). O chon tu nay
khop CA ba: ten luu, o `uom_name`, va ten da dich. Ten da dich khac ten
luu thi bay kem lam mo ta, de nguoi go tieng Viet van nhan ra don vi mang
ten tieng Anh va KHONG tao them ban trung.
"""

# ------------------------------------------------------------ phan thuan


def chuan(s):
	"""Chuoi de so khop: bo khoang trang thua, ve chu thuong. THUAN."""
	return " ".join(str(s if s is not None else "").strip().lower().split())


def khop(cac_ten, txt):
	"""Diem khop cua mot don vi voi chuoi nguoi go. THUAN.

	Tra None neu khong khop. 0 la khop tu dau chuoi, 1 la khop giua chuoi.
	Go rong thi moi don vi deu khop, diem 0, de o chon van bay ca danh muc.
	"""
	k = chuan(txt)
	cac = [chuan(x) for x in cac_ten if chuan(x)]
	if not k:
		return 0
	if any(x.startswith(k) for x in cac):
		return 0
	if any(k in x for x in cac):
		return 1
	return None


def mo_ta_hien(ten, dich):
	"""Mo ta bay canh don vi trong o chon. THUAN.

	Ten da dich khac ten luu thi tra "Box (Hop)", con khong thi rong.

	PHAI giu ten luu tieng Anh trong mo ta (v522, su co 23/09/2026). Voi
	doctype co translated_doctype = 1 nhu UOM, search_widget cua Frappe goi
	ham standard_queries voi txt RONG, lay het danh muc, roi TU LOC LAI tung
	dong bang filter_translated: dich tung o qua _() va giu dong nao co o
	chua chu nguoi go. Box dich thanh "Hop", nen neu dong chi co ["Box",
	"Hop"] thi go "box" bi loc sach. Chuoi "Box (Hop)" khong co ban dich nen
	qua _() van nguyen, va giu duoc Box khi go "box".
	"""
	t, d = str(ten or "").strip(), str(dich or "").strip()
	if not chuan(d) or chuan(d) == chuan(t):
		return ""
	return "%s (%s)" % (t, d)


def loc_don_vi(hang, txt, gioi_han=0):
	"""Chon cac don vi khop, xep khop-dau-chuoi len truoc. THUAN.

	`hang` la cac bo (ten_luu, ten_o, ten_da_dich). Tra list cac cap
	[ten_luu, mo_ta], mo_ta la "ten_luu (ten_da_dich)" khi ban dich khac ten
	luu, con khong thi rong (xem mo_ta_hien). Khong bao gio tra ban trung ten.
	"""
	ra, da_co = [], set()
	for bo in hang or []:
		ten = (list(bo) + ["", "", ""])[0]
		o = (list(bo) + ["", "", ""])[1]
		dich = (list(bo) + ["", "", ""])[2]
		if not str(ten or "").strip() or ten in da_co:
			continue
		diem = khop([ten, o, dich], txt)
		if diem is None:
			continue
		da_co.add(ten)
		mo = mo_ta_hien(ten, dich)
		ra.append((diem, chuan(ten), ten, mo))
	ra.sort(key=lambda x: (x[0], x[1]))
	cat = int(gioi_han or 0)
	dan = [[x[2], x[3]] for x in ra]
	return dan[:cat] if cat > 0 else dan


# ------------------------------------------------------- phan cham he

import frappe  # noqa: E402
from frappe.utils import cint  # noqa: E402


def _loc(filters):
	"""Loc nguoi goi dua vao, cong them dieu kien don vi con dung.

	Giu nguyen loc cua nguoi goi: cac man ERPNext co man chi cho chon don vi
	nguyen (must_be_whole_number), bo di la mo them thu ho khong ai xin.
	"""
	ra = {}
	if isinstance(filters, dict):
		ra.update(filters)
	elif isinstance(filters, (list, tuple)):
		for d in filters:
			if isinstance(d, (list, tuple)) and len(d) >= 3:
				ra[d[-3]] = [d[-2], d[-1]] if d[-2] not in ("=", "==") else d[-1]
	ra.setdefault("enabled", 1)
	return ra


# PHAI CO @frappe.whitelist() (v521, su co 23/09/2026). Frappe goi ham
# standard_queries qua search_widget, va truoc khi goi no chay
# `is_whitelisted(frappe.get_attr(query))`. Thieu decorator nay thi Frappe
# tra trang "Invalid Method" 404 cho MOI lan tim trong o chon UOM, ke ca go
# "Gram". Ban v520 lot dung loi nay: bo kiem goi thang ham nen khong thay,
# chi lo ra khi len site that. Thu tu decorator theo dung mau cua ERPNext.
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def tim_uom(doctype, txt, searchfield, start, page_len, filters, **kwargs):
	"""standard_queries cho UOM. Khop ca ten luu lan ten da dich.

	search_widget con truyen them as_dict, reference_doctype,
	ignore_user_permissions, link_fieldname; nhan vao **kwargs de khong vo.

	Danh muc don vi cua tiem chi vai tram dong nen doc het roi loc trong
	Python la du nhanh, va nho vay phep loc nam gon trong mot ham THUAN
	kiem thu duoc khong can site.
	"""
	# PHAI la get_list, KHONG duoc la get_all (Codex #360 vong 1). get_all
	# cua Frappe gan cung `ignore_permissions = True` truoc khi goi get_list,
	# nen truyen ignore_permissions=False vao get_all la vo tac dung. Ham nay
	# la standard_queries cho MOI o chon UOM trong he, bo qua quyen o day la
	# mo cho nguoi khong co quyen doc UOM xem het danh muc.
	ds = frappe.get_list(
		"UOM", filters=_loc(filters), fields=["name", "uom_name"],
		limit_page_length=0,
	)
	hang = [(d.get("name"), d.get("uom_name"), frappe._(d.get("name") or "")) for d in ds]
	dan = loc_don_vi(hang, txt)
	tu = cint(start)
	lay = cint(page_len) or 20
	return [list(x) for x in dan[tu:tu + lay]]
