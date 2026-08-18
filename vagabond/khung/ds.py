"""Ham dung danh sach chuan (A2) - tang noi voi Frappe.

Day la file DUY NHAT trong thu muc khung duoc goi frappe. Hai file kia
(hop_dong.py va tinh.py) phai chay duoc ngoai Frappe de bo kiem thu A6 op
vao. Cong viec cua file nay dung ba viec, khong lam gi hon:

    1. Kiem quyen - MOT cong, khong phai 10 ham _kiem_quyen roi rac
    2. Dich bo loc da khai thanh dieu kien SQL roi doc du lieu
    3. Giao du lieu cho tang thuan, roi tra ve dung hop dong

Moi phep tinh dung toi tien deu nam ben tinh.py. Neu mai nay co ai muon
them mot phep cong vao day thi cau tra loi la khong: dat no ben kia, roi
goi qua.

Tieu chuan so 10 - khong pha cai dang chay
------------------------------------------
20 ham ds_* cu van con nguyen, van chay, van duoc app goi. Man nao chuyen
sang khung thi them mot duong moi ben canh duong cu, chay song song, doi
chieu tung con so, khi nao khop het thi moi go duong cu. Khong doi ca 14
man trong mot lan deploy.
"""

import json

import frappe
from frappe.utils import add_days, getdate, nowdate

from vagabond.khung import tinh
from vagabond.khung.hop_dong import GIOI_HAN_DONG  # noqa: F401  (de mo dun khac lay)

# Danh ba man da chuyen sang khung. Chi la bang tra ten - khung khong biet
# nghiep vu, khai bao that nam trong chinh mo dun nghiep vu.
#
# Danh sach nay se dai dan. Duyet dot dau 15/08/2026: chi hai man mau.
NGUON_BANG = {
	"PO": ("vagabond.mua_hang", "BANG_PO"),
	"HDM": ("vagabond.ke_toan", "BANG_HOA_DON_MUA"),
	# Phan he Danh muc (anh Viet 18/08/2026). Muoi sau man, khong mot dong
	# JavaScript nao - dung cai loi hua cua tang khung hom 15/08.
	"DMSP": ("vagabond.danh_muc_nen", "BANG_SP"),
	"DMNSP": ("vagabond.danh_muc_nen", "BANG_NHOM_SP"),
	"DMDVT": ("vagabond.danh_muc_nen", "BANG_DVT"),
	"DMQD": ("vagabond.danh_muc_nen", "BANG_QUY_DOI"),
	"DMKHO": ("vagabond.danh_muc_nen", "BANG_KHO"),
	"DMBOM": ("vagabond.danh_muc_nen", "BANG_BOM"),
	"DMNCC": ("vagabond.danh_muc_nen", "BANG_NCC"),
	"DMNNCC": ("vagabond.danh_muc_nen", "BANG_NHOM_NCC"),
	"DMGIA": ("vagabond.danh_muc_nen", "BANG_GIA_MUA"),
	"DMKH": ("vagabond.danh_muc_nen", "BANG_KHACH"),
	"DMNKH": ("vagabond.danh_muc_nen", "BANG_NHOM_KHACH"),
	"DMPT": ("vagabond.danh_muc_nen", "BANG_PT_THANH_TOAN"),
	"DMNH": ("vagabond.danh_muc_nen", "BANG_NGAN_HANG"),
	"DMTK": ("vagabond.danh_muc_nen", "BANG_TAI_KHOAN"),
	"DMTHUE": ("vagabond.danh_muc_nen", "BANG_THUE"),
	"DMTHUEM": ("vagabond.danh_muc_nen", "BANG_THUE_MUA"),
}


def lay_bang(ma):
	"""Tra ve khai bao cua mot man. Nem loi tieng Viet neu khong co."""
	ma = (ma or "").strip().upper()
	nguon = NGUON_BANG.get(ma)
	if not nguon:
		frappe.throw("Không có màn danh sách mã %s." % (ma or "(trống)"))
	mo_dun = frappe.get_module(nguon[0])
	b = getattr(mo_dun, nguon[1], None)
	if not b:
		frappe.throw("Màn %s khai báo thiếu." % ma)
	return b


# --------------------------------------------------------------- cong quyen

def _cong_quyen(b):
	"""MOT cong quyen cho moi man danh sach (tieu chuan so 6).

	Truoc day 10 mo dun moi mo dun tu viet mot ham _kiem_quyen rieng. Doi
	chinh sach quyen phai sua 10 cho va chac chan sot mot cho. Nay vai tro
	khai ngay trong bang, con cho kiem chi con mot.
	"""
	if not b["quyen"] & set(frappe.get_roles()):
		frappe.throw(b["loi_quyen"])


# ---------------------------------------------------------------- doc loc

def _ds_gia_tri(v):
	"""Doc mot tham so nhieu gia tri: JSON list, hoac chuoi ngan cach dau phay.

	App gui xuong khi thi mang JSON khi thi chuoi, tuy man. Nhan ca hai chu
	khong bat app phai dong nhat - do la viec cua khung, khong phai cua man.
	"""
	if v is None or v == "":
		return []
	if isinstance(v, (list, tuple, set)):
		return [str(x).strip() for x in v if str(x).strip()]
	s = str(v).strip()
	if s.startswith("["):
		try:
			return [str(x).strip() for x in json.loads(s) if str(x).strip()]
		except (ValueError, TypeError):
			pass
	return [x.strip() for x in s.split(",") if x.strip()]


def khoang_ngay(tham, mac_dinh=30):
	"""Khoang ngay dang xem. Uu tien tu/den, khong co thi lui theo so ngay.

	so_ngay = 0 nghia la lay het, ke toan tra chung tu cu can duong nay.
	Tra ve (tu, den) hoac (None, None) khi lay het.
	"""
	tu, den = tham.get("tu"), tham.get("den")
	if tu and den:
		t, d = getdate(tu), getdate(den)
		return (t, d) if t <= d else (d, t)
	sn = tham.get("so_ngay")
	sn = int(sn) if str(sn or "").strip() not in ("", "None") else int(mac_dinh)
	if sn <= 0:
		return None, None
	return getdate(add_days(nowdate(), -sn)), getdate(nowdate())


def _dieu_kien(b, tham):
	"""Dich cac bo loc da khai thanh dieu kien SQL.

	Loc chay o MAY CHU (tieu chuan so 7). Chi rieng tim_chu la loc tren tap
	da doc ve, vi no do chu vao nhieu truong cung luc va co ca truong dan
	xuat - nhung tap do da bi cac dieu kien SQL khac thu nho lai roi.
	"""
	dk = dict(b["dieu_kien"])
	khoa_tim = []
	tu_ngay = den_ngay = None
	dang = {}
	for f in b["loc"]:
		k, kieu = f["k"], f["kieu"]
		if kieu == "tim_chu":
			gt = tinh.chu(tham.get(k))
			if gt:
				dang[k] = gt
			khoa_tim = list(f["tim"])
			continue
		if kieu == "ngay":
			tu_ngay, den_ngay = khoang_ngay(tham, f.get("mac_dinh", 30))
			if tu_ngay and den_ngay and not f.get("tay"):
				dk[f["truong"]] = ["between", [str(tu_ngay), str(den_ngay)]]
			dang[k] = {"tu": str(tu_ngay or ""), "den": str(den_ngay or "")}
			continue
		if kieu == "chon_mot":
			gt = tinh.chu(tham.get(k))
			if gt and not f.get("tay"):
				dk[f["truong"]] = gt
			if gt:
				dang[k] = gt
			continue
		if kieu == "chon_nhieu":
			gt = _ds_gia_tri(tham.get(k))
			if gt and not f.get("tay"):
				dk[f["truong"]] = ["in", gt]
			if gt:
				dang[k] = gt
			continue
		if kieu == "khoang_so":
			a, z = tham.get(k + "_tu"), tham.get(k + "_den")
			if str(a or "").strip() != "":
				dk[f["truong"]] = [">=", tinh.so(a)]
			if str(z or "").strip() != "":
				# Hai dieu kien tren cung mot truong: Frappe nhan dang list
				# cac cap, nen gop lai thanh mot bieu thuc between.
				a2 = tinh.so(a) if str(a or "").strip() != "" else None
				dk[f["truong"]] = (
					["between", [a2, tinh.so(z)]] if a2 is not None else ["<=", tinh.so(z)]
				)
			if str(a or "").strip() != "" or str(z or "").strip() != "":
				dang[k] = {"tu": a, "den": z}
			continue
		if kieu == "co":
			if tinh.co(tham.get(k)):
				dk.update(f.get("dk") or {})
				dang[k] = 1
			continue
	return dk, khoa_tim, dang, tu_ngay, den_ngay


# -------------------------------------------------------------------- chay

def dung(b, tham=None, day_du=0):
	"""Doc du lieu roi tra ve dung hop dong. Dung duoc tu Python, khong qua API.

	Tach khoi ham chay() co @whitelist de mo dun khac goi lai duoc, va de
	kiem thu goi duoc ma khong phai gia lap mot request.
	"""
	tham = dict(tham or {})
	_cong_quyen(b)
	dk, khoa_tim, dang, tu_ngay, den_ngay = _dieu_kien(b, tham)

	# limit_page_length=0 la co y: phai doc HET tap khop dieu kien thi dem
	# chip va cong tong moi dung. Cat dong lam o buoc cuoi, trong tinh.py.
	dong = frappe.get_all(
		b["doctype"],
		filters=dk,
		fields=b["truong"],
		order_by=b["sap"],
		limit_page_length=0,
	)
	dong = [dict(r) for r in dong]

	boi_canh = {
		"hom_nay": getdate(nowdate()),
		"tu": tu_ngay,
		"den": den_ngay,
		"tham": tham,
	}
	if b["truoc"]:
		boi_canh.update(b["truoc"](dong, boi_canh) or {})
	if b["them"]:
		for r in dong:
			r.update(b["them"](r, boi_canh) or {})
	if b["xep"]:
		tinh.dat_chip(dong, b["xep"], boi_canh)
	q = ""
	for f in b["loc"]:
		if f["kieu"] == "tim_chu":
			q = tinh.chu(tham.get(f["k"]))
	if q:
		dong = tinh.tim(dong, q, khoa_tim)

	kq = tinh.dung_bang(
		dong,
		b["cot"],
		ds_chip=b["chip"],
		chon=tham.get("chip") or tham.get("nhom") or "",
		tran=b["tran"],
		day_du=tinh.co(day_du),
		tinh_dong=b["tinh_dong"],
		tom_tat_khai=b["tom_tat"],
		tom_tat_theo_chip=b["tom_tat_theo_chip"],
	)
	kq["ma"] = b["ma"]
	kq["ten"] = b["ten"]
	kq["sap"] = b["sap"]
	kq["loc"] = [dict(f, gt=dang.get(f["k"])) for f in b["loc"]]
	kq["tu"] = str(tu_ngay or "")
	kq["den"] = str(den_ngay or "")
	return kq


@frappe.whitelist()
def chay(ma, day_du=0, **tham):
	"""Duong goi duy nhat cho moi man danh sach da chuyen sang khung.

	Them mot man moi tu nay ve sau chi con la khai bao cot va bo loc trong
	mo dun nghiep vu, roi ghi mot dong vao NGUON_BANG. Khong phai viet lai
	loc, dem, cong, cat, cung khong phai viet mot man hinh moi.
	"""
	tham.pop("cmd", None)
	return dung(lay_bang(ma), tham, day_du=day_du)


@frappe.whitelist()
def danh_ba():
	"""Cac man da co trong khung, kem ten - de app dung menu khong phai go tay."""
	ra = []
	for ma in sorted(NGUON_BANG):
		try:
			b = lay_bang(ma)
		except Exception:
			continue
		if b["quyen"] & set(frappe.get_roles()):
			ra.append({"ma": b["ma"], "ten": b["ten"]})
	return ra
