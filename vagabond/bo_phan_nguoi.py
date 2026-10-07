# -*- coding: utf-8 -*-
"""Bo phan cua tung nguoi dung: cac phep THUAN (khong cham Frappe).

Anh Viet 07/10/2026: chi Le Thi Linh la bep truong Pastry ma he thong ghi bo
phan Bep Baker, nen app chi cho chi thay phieu cua Baker, va tren app khong co
cho nao sua bo phan. Bo phan cua mot nguoi nam o o `custom_phong_ban` (lien
ket Department) tren User; app doc o do de biet nguoi nay thuoc bep nao
(myKitchen trong 01-khung-app.js) va de giao viec theo bo phan.

Codex #450 (vong 2 phan bo phan): cac phep thuan phai dung TRUOC ranh gioi
Frappe de ca kiem tang khung goi duoc ma khong dung lop Frappe gia. Tep nay
khong import frappe; cay bo phan (thu tu, khoi) do ben goi truyen vao.
"""

import re

# Bep nao thi thay phieu yeu cau san xuat cua bep do. Khop voi BEPS va
# myKitchen trong 01-khung-app.js (ca kiem chot hai ben trung nhau).
BEP_THAY_PHIEU = (
	("Bếp Pastry", "Bếp Pastry"),
	("Bếp Baker", "Bếp Baker"),
	("Bếp Lab", "Bếp Lab"),
	("Sonneto Lab", "Bếp Lab"),
	("Lab", "Bếp Lab"),
)


def ten_ngan_bo_phan(ten):
	"""Bo duoi viet tat cong ty: "Bếp Pastry - TV" thanh "Bếp Pastry"."""
	ten = str(ten or "").strip()
	i = ten.rfind(" - ")
	# Duoi viet tat cong ty chi gom chu in hoa va so ("TV"). "Bếp Lab - R&D"
	# la ten that cua bo phan cu, khong duoc cat.
	if i > 0 and re.fullmatch(r"[A-Z0-9]{1,10}", ten[i + 3:]):
		return ten[:i]
	return ten


def bep_cua_bo_phan(ten):
	"""Bo phan nay thay phieu san xuat cua bep nao. "" la khong phai bep."""
	ngan = ten_ngan_bo_phan(ten)
	for dau, bep in BEP_THAY_PHIEU:
		if ngan.startswith(dau):
			return bep
	return ""


def mo_ta_bo_phan(ten, nhom_cua=None):
	"""Mot dong giai thich chon bo phan nay thi sao. nhom_cua(ten ngan) tra
	ten khoi trong cay bo phan (hoac None)."""
	bep = bep_cua_bo_phan(ten)
	if bep:
		return "Thấy và nhận phiếu yêu cầu sản xuất gửi %s." % bep
	nhom = nhom_cua(ten_ngan_bo_phan(ten)) if nhom_cua else None
	return nhom + "." if nhom else "Phiếu do người này tạo sẽ ghi bộ phận này."


def cac_bo_phan_chon(ds, thu_tu=(), nhom_cua=None):
	"""Lua chon cho hop doi bo phan, xep theo thu tu cay bo phan.

	ds: danh sach ten Department (da loc nhom va da tat). thu_tu: ten ngan
	cac bo phan la theo dung thu tu cay. Tra ve [{k, nhan, mo_ta}], k la ten
	day du dung de luu.
	"""
	thu_tu = list(thu_tu or [])

	def hang(ten):
		ngan = ten_ngan_bo_phan(ten)
		return (thu_tu.index(ngan) if ngan in thu_tu else len(thu_tu), ngan)

	return [{"k": ten, "nhan": ten_ngan_bo_phan(ten), "mo_ta": mo_ta_bo_phan(ten, nhom_cua)}
		for ten in sorted({str(x) for x in ds or [] if x}, key=hang)]
