# -*- coding: utf-8 -*-
"""Ca kiểm TÍCH HỢP cho mã chứng từ chung MÃ-yymmdd-nnnnnn (v680, PR #601).

Tầng khung đã chốt phần thuần và hook với frappe giả. Tầng này chứng minh
trên Frappe và ERPNext THẬT ba điều bộ giả không thấy:

1. Hook `autoname` của app thật sự được Frappe gọi cho một doctype ERPNext đặt
   tên bằng naming_series (Material Request) và cho một doctype của app đặt
   tên bằng chuỗi format (Vagabond Moc So Du), và tên hook đặt là tên được giữ.
2. Dòng đếm `VGBMA-<tiền tố>` trong tabSeries tăng đúng một mỗi lần, hai phiếu
   nối tiếp mang hai số liền nhau.
3. Trước mốc 01/12/2026 không phiếu nào đổi tên.

Ngày được thay bằng 01/12/2026 trong ca (`ma_chung_tu._hom_nay`). Bench không
có Property Setter và Server Script của site, nên chuỗi mặc định của Material
Request là chuỗi gốc ERPNext; ca thay phép đọc tiền tố để chuỗi đó ra YCDC.
Mọi phiếu, dòng đếm lùi lại sau ca theo điểm lưu của `nen.py`.
"""

import frappe
from frappe.utils import nowdate

from vagabond import ma_chung_tu as mct
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la, mot_kho
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _uom


def _dong(tt):
	d = frappe.db.sql("select `current` from `tabSeries` where `name`=%s", (mct.khoa(tt),))
	return int(d[0][0]) if d else None


class _Ngay(object):
	"""Thay ngày và phép đọc tiền tố trong ca, trả lại khi xong."""

	def __init__(self, ngay, tien_to=None):
		self.ngay, self.tien_to = ngay, tien_to

	def __enter__(self):
		self.goc = (mct._hom_nay, mct.tien_to_tu_chuoi)
		mct._hom_nay = lambda: self.ngay
		if self.tien_to:
			goc_tt = self.goc[1]
			mct.tien_to_tu_chuoi = lambda c: self.tien_to if str(c or "").startswith("MAT-MR-") else goc_tt(c)
		return self

	def __exit__(self, *a):
		mct._hom_nay, mct.tien_to_tu_chuoi = self.goc


def _yeu_cau():
	cty = cong_ty()
	kho = mot_kho(cty)
	ma = _mon_thu("KT-MCT-679")
	mr = frappe.new_doc("Material Request")
	mr.company = cty
	mr.material_request_type = "Purchase"
	mr.schedule_date = nowdate()
	mr.append("items", {"item_code": ma, "qty": 1, "schedule_date": nowdate(),
		"warehouse": kho, "uom": _uom(), "conversion_factor": 1})
	mr.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Material Request", mr.name))
	return mr


def _moc():
	d = frappe.get_doc({"doctype": "Vagabond Moc So Du", "nguon": "KT-679", "ngay_chot": nowdate()})
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Vagabond Moc So Du", d.name))
	return d


@ca("ma chung tu 680: tu 01/12/2026 phieu ERPNext mang YCDC-261201-nnnnnn, so noi tiep dong dem")
def _erpnext():
	with _Ngay("2026-12-01", "YCDC"):
		truoc = _dong("YCDC") or 0
		a = khong_nem("insert yêu cầu 1", _yeu_cau)
		b = khong_nem("insert yêu cầu 2", _yeu_cau)
	if not (a and b):
		return
	dung("mã mới: " + a.name, mct.la_ma_moi(a.name, "YCDC"))
	la("phần ngày", a.name.split("-")[1], "261201")
	la("số nối tiếp dòng đếm", int(a.name.split("-")[-1]), truoc + 1)
	la("phiếu sau hơn đúng một", int(b.name.split("-")[-1]), truoc + 2)
	la("dòng đếm tăng đúng hai", _dong("YCDC"), truoc + 2)
	la("có thật trong sổ", frappe.db.exists("Material Request", a.name), a.name)


@ca("ma chung tu 680: phieu cua app (chuoi format) mang MSD-261201-nnnnnn")
def _app():
	with _Ngay("2026-12-01"):
		truoc = _dong("MSD") or 0
		d = khong_nem("insert mốc số dư", _moc)
	if not d:
		return
	la("tên", d.name, mct.ma("MSD", "2026-12-01", truoc + 1))


@ca("ma chung tu 680: truoc 01/12/2026 khong phieu nao doi ten, khong ton so")
def _truoc_moc():
	with _Ngay("2026-11-30", "YCDC"):
		truoc = _dong("YCDC")
		mr = khong_nem("insert yêu cầu", _yeu_cau)
		d = khong_nem("insert mốc số dư", _moc)
	if not (mr and d):
		return
	dung("yêu cầu giữ chuỗi cũ: " + mr.name, not mct.la_ma_moi(mr.name))
	dung("mốc giữ chuỗi cũ: " + d.name, not mct.la_ma_moi(d.name))
	la("dòng đếm không đổi", _dong("YCDC"), truoc)
