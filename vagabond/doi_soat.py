"""Doi soat ma san pham giua Pancake va ERPNext.

Bo ma tren Next la BO CHUAN (anh Viet chot 01/08/2026): moi noi khac
(Pancake, Grab...) phai chinh theo Next. Cac ham o day chi DOC de liet ke
cho lech, khong tu sua gi ben Pancake.
"""

import csv
import io
import re

import frappe
import requests

from frappe.utils import flt

from vagabond.lib import PANCAKE, TIMEOUT, cfg, key

QUYEN = {"System Manager", "Sales Manager", "Sales User", "Bộ phận đặt hàng"}

HAU_TO_SIZE = re.compile(r"(MINI|[SML])\d{1,2}CM$", re.IGNORECASE)


def _quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Không có quyền đối soát mã")


@frappe.whitelist()
def keo_san_pham_pancake():
	"""Keo toan bo mau ma (variations) tu danh muc Pancake."""
	_quyen()
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chưa cấu hình Pancake trong Vagabond Settings")
	ds, page = [], 1
	while page <= 60:
		r = requests.get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "page_number": page, "page_size": 100},
			timeout=TIMEOUT,
		)
		data = (r.json() or {}).get("data") or []
		if not data:
			break
		for v in data:
			sp = v.get("product") or {}
			anh = v.get("images") or sp.get("images") or []
			ds.append(
				{
					"ma": str(v.get("display_id") or "").strip(),
					"ten": (v.get("name") or "").strip() or (sp.get("name") or "").strip(),
					"ten_sp": (sp.get("name") or "").strip(),
					"gia": v.get("retail_price") or 0,
					"anh": anh[0] if anh else "",
				}
			)
		if len(data) < 100:
			break
		page += 1
	return ds


@frappe.whitelist()
def keo_anh_san_pham(ghi_de=0, gioi_han=400):
	"""Keo anh mau ma tu Pancake ve gan vao Item.image.

	Man Chon mon cua app hien icon banh thay vi anh that vi hau het Item
	khong co anh (02/08: chi 13 tren 456 ma hang ban co anh). Lenh nay keo
	anh san ben Pancake ve, chay lai bao nhieu lan cung khong tao anh trung
	vi da co anh thi bo qua (tru khi ghi_de = 1).
	"""
	_quyen()
	ghi_de = int(ghi_de or 0)
	gioi_han = int(gioi_han or 400)
	ds = keo_san_pham_pancake()

	# Ban do ma -> url anh. Ma co hau to size Pancake tu sinh thi lay ma goc.
	anh_theo_ma = {}
	for v in ds:
		url = (v.get("anh") or "").strip()
		ma = (v.get("ma") or "").strip()
		if not url or not ma:
			continue
		anh_theo_ma.setdefault(ma, url)
		goc = HAU_TO_SIZE.sub("", ma).strip()
		if goc and goc != ma:
			anh_theo_ma.setdefault(goc, url)

	loc = {"is_sales_item": 1}
	if not ghi_de:
		loc["image"] = ["in", ["", None]]
	can = frappe.db.get_all("Item", filters=loc, fields=["name", "item_name"], limit_page_length=0)

	kq = {"da_gan": 0, "khong_co_anh": [], "loi": [], "tong_can": len(can)}
	for it in can:
		if kq["da_gan"] >= gioi_han:
			break
		url = anh_theo_ma.get(it.name)
		if not url:
			kq["khong_co_anh"].append(it.name)
			continue
		try:
			r = requests.get(url, timeout=TIMEOUT)
			r.raise_for_status()
			duoi = "png" if "png" in (r.headers.get("Content-Type") or "") else "jpg"
			tep = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": "sp-%s.%s" % (it.name.lower(), duoi),
					"content": r.content,
					"is_private": 0,
					"attached_to_doctype": "Item",
					"attached_to_name": it.name,
				}
			)
			tep.flags.ignore_permissions = True
			tep.insert(ignore_permissions=True)
			frappe.db.set_value("Item", it.name, "image", tep.file_url)
			kq["da_gan"] += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "doi_soat: keo anh %s" % it.name)
			kq["loi"].append(it.name)
	frappe.db.commit()
	kq["con_thieu"] = len(kq["khong_co_anh"])
	kq["khong_co_anh"] = kq["khong_co_anh"][:200]
	return kq


def _item_theo_ma(ma):
	"""Item khop ma, co lop bo hau to size Pancake/Fabi tu sinh."""
	ma = (ma or "").strip().upper()
	if not ma:
		return ""
	if frappe.db.exists("Item", ma):
		return ma
	goc = HAU_TO_SIZE.sub("", ma).strip()
	if goc and goc != ma and frappe.db.exists("Item", goc):
		return goc
	return ""


def _gan_anh_url(ma, url):
	"""Tai anh tu url ve, tao File cong khai roi gan vao Item.image."""
	r = requests.get(url, timeout=TIMEOUT)
	r.raise_for_status()
	kieu = (r.headers.get("Content-Type") or "").lower()
	duoi = "png" if "png" in kieu else ("webp" if "webp" in kieu else "jpg")
	tep = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": "sp-%s.%s" % (ma.lower(), duoi),
			"content": r.content,
			"is_private": 0,
			"attached_to_doctype": "Item",
			"attached_to_name": ma,
		}
	)
	tep.flags.ignore_permissions = True
	tep.insert(ignore_permissions=True)
	frappe.db.set_value("Item", ma, "image", tep.file_url)
	return tep.file_url


@frappe.whitelist()
def nap_anh_mo_ta_tu_file(file_url, ghi_de_anh=0, ghi_de_mo_ta=0, gioi_han=500):
	"""Nap anh + mo ta mon tu file CSV da upload len Next.

	File CSV ba cot: ma, anh, mo_ta. Dung cho ban xuat menu cua Fabi
	(cot Hinh anh tro ve CDN image.foodbook.vn, cot Mo ta la thanh phan banh).
	Fabi phu anh day hon Pancake nhieu nen day la nguon chinh de bu anh mon
	(anh Viet gui file 02/08/2026).

	Chay lai bao nhieu lan cung duoc: ma nao da co anh (hay da co mo ta) thi
	bo qua, tru khi bat ghi_de tuong ung.
	"""
	_quyen()
	ghi_de_anh = int(ghi_de_anh or 0)
	ghi_de_mo_ta = int(ghi_de_mo_ta or 0)
	gioi_han = int(gioi_han or 500)

	tep = frappe.get_doc("File", {"file_url": file_url})
	noi_dung = tep.get_content()
	if isinstance(noi_dung, bytes):
		noi_dung = noi_dung.decode("utf-8-sig")
	doc = csv.DictReader(io.StringIO(noi_dung))

	kq = {"anh": 0, "mo_ta": 0, "khong_co_ma": [], "loi": [], "xet": 0}
	for dong in doc:
		if kq["anh"] >= gioi_han:
			break
		kq["xet"] += 1
		ma = _item_theo_ma(dong.get("ma"))
		if not ma:
			kq["khong_co_ma"].append((dong.get("ma") or "").strip())
			continue
		hien = frappe.db.get_value("Item", ma, ["image", "description"], as_dict=True) or {}
		url = (dong.get("anh") or "").strip()
		if url.startswith("http") and (ghi_de_anh or not (hien.get("image") or "").strip()):
			try:
				_gan_anh_url(ma, url)
				kq["anh"] += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), "doi_soat: nap anh %s" % ma)
				kq["loi"].append(ma)
		mo_ta = (dong.get("mo_ta") or "").strip()
		cu = re.sub(r"<[^>]+>", "", hien.get("description") or "").strip()
		# ERPNext tu dien description bang chinh ten mon - do khong tinh la co.
		if mo_ta and (ghi_de_mo_ta or not cu or cu == ma or cu.lower() == (frappe.db.get_value("Item", ma, "item_name") or "").lower()):
			frappe.db.set_value("Item", ma, "description", mo_ta)
			kq["mo_ta"] += 1
	frappe.db.commit()
	kq["so_ma_khong_thay"] = len(kq["khong_co_ma"])
	kq["khong_co_ma"] = kq["khong_co_ma"][:150]
	return kq


@frappe.whitelist()
def nap_gia_ban_tu_file(file_url, bang_gia=None, ghi_de=1):
	"""Nap gia ban tu file CSV hai cot: ma, gia.

	Anh Viet chot 02/08/2026: LAY GIA BEN FABI LAM CHUAN cho bo ma tren Next.
	Ham nay ghi vao ca hai cho:
	- Item.standard_rate (gia niem yet tren ho so hang)
	- Item Price cua bang gia ban mac dinh (Standard Selling), tao moi neu chua co

	Chay lai bao nhieu lan cung duoc. ghi_de = 0 thi chi dien cho ma chua co gia.
	"""
	_quyen()
	ghi_de = int(ghi_de or 0)
	bang_gia = (bang_gia or "").strip() or frappe.db.get_single_value(
		"Selling Settings", "selling_price_list"
	) or "Standard Selling"
	if not frappe.db.exists("Price List", bang_gia):
		frappe.throw("Không có bảng giá %s." % bang_gia)
	tien_te = frappe.db.get_value("Price List", bang_gia, "currency") or "VND"

	tep = frappe.get_doc("File", {"file_url": file_url})
	noi_dung = tep.get_content()
	if isinstance(noi_dung, bytes):
		noi_dung = noi_dung.decode("utf-8-sig")

	kq = {"sua_ho_so": 0, "sua_bang_gia": 0, "tao_bang_gia": 0, "khong_co_ma": [], "xet": 0}
	for dong in csv.DictReader(io.StringIO(noi_dung)):
		kq["xet"] += 1
		ma = _item_theo_ma(dong.get("ma"))
		if not ma:
			kq["khong_co_ma"].append((dong.get("ma") or "").strip())
			continue
		try:
			gia = float(dong.get("gia") or 0)
		except ValueError:
			continue
		if gia <= 0:
			continue

		cu = flt(frappe.db.get_value("Item", ma, "standard_rate"))
		if ghi_de or not cu:
			if cu != gia:
				frappe.db.set_value("Item", ma, "standard_rate", gia)
				kq["sua_ho_so"] += 1

		ten_gia = frappe.db.get_value(
			"Item Price", {"item_code": ma, "price_list": bang_gia}, "name"
		)
		if ten_gia:
			if ghi_de and flt(frappe.db.get_value("Item Price", ten_gia, "price_list_rate")) != gia:
				frappe.db.set_value("Item Price", ten_gia, "price_list_rate", gia)
				kq["sua_bang_gia"] += 1
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": ma,
					"price_list": bang_gia,
					"price_list_rate": gia,
					"currency": tien_te,
					"selling": 1,
				}
			)
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)
			kq["tao_bang_gia"] += 1
	frappe.db.commit()
	kq["so_ma_khong_thay"] = len(kq["khong_co_ma"])
	kq["khong_co_ma"] = kq["khong_co_ma"][:150]
	kq["bang_gia"] = bang_gia
	return kq


@frappe.whitelist()
def doi_soat_ma():
	"""So tung mau ma Pancake voi Item ben Next.

	Phan loai: thieu_ma (ma rong hoac "1"), khong_co_next (ma khong ton tai
	ben Next, ke ca sau khi bo hau to size), khac_ten (trung ma nhung ten
	hai ben khac nhau), con lai la khop.
	"""
	_quyen()
	sp = keo_san_pham_pancake()
	kq = {
		"tong_pancake": len(sp),
		"khop": 0,
		"thieu_ma": [],
		"khong_co_next": [],
		"khac_ten": [],
	}
	for v in sp:
		ma = v["ma"]
		if not ma or ma == "1":
			kq["thieu_ma"].append(v)
			continue
		ten_next = frappe.db.get_value("Item", ma, "item_name")
		if ten_next is None:
			goc = HAU_TO_SIZE.sub("", ma)
			if goc != ma:
				ten_next = frappe.db.get_value("Item", goc, "item_name")
				if ten_next is not None:
					v["ghi_chu"] = "Hậu tố size, mã gốc %s" % goc
		if ten_next is None:
			kq["khong_co_next"].append(v)
		elif (v["ten"] or "").strip().lower() != (ten_next or "").strip().lower():
			v["ten_next"] = ten_next
			kq["khac_ten"].append(v)
		else:
			kq["khop"] += 1
	return kq
