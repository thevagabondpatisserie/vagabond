# -*- coding: utf-8 -*-
"""Ma khach hang sinh theo nhom (anh Viet 12/08/2026).

Truoc day khoa chinh cua khach hang chinh la TEN khach: mot ban ghi ten
"CONG TY TNHH THUONG MAI DICH VU VA XAY DUNG FALCONS" thi ma cua no cung
la nguyen cai ten do. Ba cai gia phai tra:

  1. Hai khach trung ten la ERPNext tu them "-1" vao duoi, khong ai doc ra
     duoc dau la ai.
  2. Sua mot ky tu trong ten khach la doi khoa chinh, keo theo phai sua het
     moi hoa don da tro toi.
  3. Sap import gan 50.000 khach tu Fabi. Ten khach la truong nguoi ta go
     tay, chac chan co trung, co khoang trang thua, co viet hoa viet thuong
     lan lon - dung no lam khoa la nhan lay het mo hon do lam khoa.

Nay moi khach moi mang mot ma ngan theo NHOM: KL cho khach le, SI cho khach
si, DN cho khach doanh nghiep, SA cho san giao do an, NB cho noi bo. Nhin
ma la biet ngay khach thuoc dien nao ma khong phai mo ra xem.

Khach CU giu nguyen ma cu. Doi ma cua 1.545 khach dang chay la doi khoa
chinh cua tung nguoi, keo theo moi hoa don, phieu giao hang, cong no da
tro toi ho - viec do phai lam rieng, co xem truoc, khong nhet vao mot ban
deploy.
"""

import re

import frappe
from frappe.model.naming import getseries
from frappe.utils import cint

# Chuan hoa so dien thoai nay o vagabond/lib.py, dung chung ca he: bon mo
# dun tung tu viet mot ham roi hieu khac nhau, nen cung mot nguoi vao he
# hai lan thanh hai khach.
from vagabond.lib import sdt_so as _so

# Nhan dien nhom theo TEN nhom chu khong liet ke cung tung nhom mot: ke
# toan hay them nhom moi ("Khach si B2B" truoc do la "Khach si"), liet ke
# cung thi nhom moi rot het xuong ma mac dinh ma khong ai biet.
# Xet theo THU TU trong danh sach, khop cai dau tien thi dung lai.
TIEN_TO = [
	(("sỉ", "si b2b", "wholesale", "b2b"), "SI"),
	(("doanh nghiệp", "quà tặng", "corporate", "company"), "DN"),
	(("sàn", "giao đồ ăn", "platform"), "SA"),
	(("nội bộ", "nhân viên", "internal"), "NB"),
	(("lẻ", "retail", "individual"), "KL"),
]
MAC_DINH = "KH"
SO_CHU_SO = 6

# Ma da dung khuon roi thi khong dat lai. De khi khoi phuc du lieu hoac
# import lai mot khach cu, ma cua ho khong bi doi thanh mot ma khac.
MAU_MA = re.compile(r"^(?:%s|%s)\d{%d}$" % ("|".join(t for _, t in TIEN_TO), MAC_DINH, SO_CHU_SO))


def tien_to(nhom):
	"""Tien to ma theo ten nhom khach."""
	n = (nhom or "").strip().lower()
	for tu_khoa, ma in TIEN_TO:
		for t in tu_khoa:
			if t in n:
				return ma
	return MAC_DINH


def ma_moi(nhom):
	"""Mot ma moi chua ai dung. getseries dem trong bang tabSeries nen
	khong dung frappe.db.count: dem ban ghi vua cham vua dung nhau khi hai
	nguoi cung tao khach mot luc, va import 50.000 dong thi de trung."""
	tt = tien_to(nhom)
	return "%s%s" % (tt, getseries(tt, SO_CHU_SO))


def dat_ma(doc, method=None):
	"""Hook autoname cua Customer.

	Chay SAU autoname cua ERPNext nen ghi de duoc cai ten ERPNext vua dat.
	"""
	try:
		if getattr(doc, "doctype", None) != "Customer":
			return
		ten = (doc.name or "").strip()
		# Da la ma dung khuon thi giu nguyen: import lai khach cu khong bi
		# cap ma moi, va chay lai mot phieu hong khong sinh rac.
		if ten and MAU_MA.match(ten):
			return
		doc.name = ma_moi(doc.get("customer_group"))
	except Exception:
		# Dat ma hong thi de ERPNext dung ten nhu cu, con hon chan dung viec
		# tao khach giua gio ban hang.
		frappe.log_error(frappe.get_traceback(), "ma_khach: dat ma loi")


# ------------------------------------------------------- ra trung so dien thoai
#
# Import 50.000 khach tu Fabi vao mot he da co 1.545 khach thi chac chan
# co nguoi nam ca hai ben. Hai ban ghi cho mot nguoi nghia la chi tieu bi
# chia doi, hang xet sai, diem tich ra hai so du.
#
# KHONG chan tu dong luc them khach: chan giua chung mot lan import 50.000
# dong la hong ca me du lieu ma khong biet dung o dong nao. Ra sau, xem
# truoc, gop tay.


@frappe.whitelist()
def ra_trung_sdt(so_dong=200):
	"""Cac so dien thoai dang gan cho tu hai khach tro len."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	rows = frappe.get_all(
		"Customer",
		filters={"disabled": 0},
		fields=["name", "customer_name", "customer_group", "mobile_no", "vgb_hang", "creation"],
		limit_page_length=0,
	)
	theo_so = {}
	for r in rows:
		s = _so(r.get("mobile_no"))
		if len(s) < 8:
			continue
		theo_so.setdefault(s, []).append(r)

	ra = []
	for s, ds in theo_so.items():
		if len(ds) < 2:
			continue
		ds.sort(key=lambda x: str(x.get("creation") or ""))
		ra.append(
			{
				"sdt": s,
				"so_ban_ghi": len(ds),
				"khach": [
					{
						"ma": x["name"],
						"ten": x.get("customer_name") or x["name"],
						"nhom": x.get("customer_group") or "",
						"hang": x.get("vgb_hang") or "",
					}
					for x in ds
				],
			}
		)
	ra.sort(key=lambda x: -x["so_ban_ghi"])
	return {
		"trung": ra[: max(1, min(2000, cint(so_dong) or 200))],
		"tong": len(ra),
		"tong_ban_ghi_thua": sum(x["so_ban_ghi"] - 1 for x in ra),
	}
