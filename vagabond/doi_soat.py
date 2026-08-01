"""Doi soat ma san pham giua Pancake va ERPNext.

Bo ma tren Next la BO CHUAN (anh Viet chot 01/08/2026): moi noi khac
(Pancake, Grab...) phai chinh theo Next. Cac ham o day chi DOC de liet ke
cho lech, khong tu sua gi ben Pancake.
"""

import re

import frappe
import requests

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
