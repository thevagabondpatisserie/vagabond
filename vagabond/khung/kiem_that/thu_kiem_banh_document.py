"""Giữ số nhập và dấu vết khi Frappe insert/save bảng kiểm bánh thật.

Bàn giả không mô phỏng đầy đủ lúc Frappe gán tên cho child. Các ca này dùng
Document thật trong điểm lưu của khung; không xoá bản có sẵn để lấy chỗ.
"""

import json
import secrets

import frappe
from frappe.utils import add_days, today

from vagabond import kiem_banh
from vagabond.khung.kiem_that.nen import _DA_TAO, _mot, ca, dung, la


def _bang_moi():
	ngay = str(add_days(today(), 10000 + secrets.randbelow(20000)))
	if frappe.db.exists("Kiem Banh Ngay", "KB-" + ngay):
		frappe.throw("Ngày fixture đã có dữ liệu. Giữ nguyên và chạy lại với ngày khác.")
	ma = _mot("Item", {"disabled": 0})
	if not ma:
		frappe.throw("Site thử cần một Item đang bật.")
	b = frappe.new_doc("Kiem Banh Ngay")
	b.ngay = ngay
	return b, ma


@ca("kiem banh Document: insert parent moi va them child moi giu so nhap va audit")
def _():
	b, ma = _bang_moi()
	b.append("dong", {"ma_hang": ma, "ton_d2": 2})
	b.insert(ignore_permissions=True)
	_DA_TAO.append((b.doctype, b.name))
	b.reload()
	la("số nhập parent mới", b.dong[0].ton_d2, 2)
	la("nguồn tay sau insert thật", b.dong[0].nguon_ton_d2, kiem_banh.NGUON_TAY)
	dung("audit sau insert", bool(json.loads(b.dong[0].kiem_dem_ghi)["ton_d2"]["ai"]))
	b.append("dong", {"ma_hang": ma, "ton_d1": 3})
	b.save(ignore_permissions=True)
	b.reload()
	la("child mới ở parent cũ", b.dong[1].nguon_ton_d1, kiem_banh.NGUON_TAY)


@ca("kiem banh Document: xac nhan 0 co audit va go child bang payload bi chan")
def _():
	b, ma = _bang_moi()
	b.append("dong", {"ma_hang": ma, "ton_d1": 0, "nguon_ton_d1": kiem_banh.NGUON_TAY})
	b.insert(ignore_permissions=True)
	_DA_TAO.append((b.doctype, b.name))
	b.reload()
	la("xác nhận 0", b.dong[0].nguon_ton_d1, kiem_banh.NGUON_TAY)
	dung("có audit 0", bool(json.loads(b.dong[0].kiem_dem_ghi)["ton_d1"]["luc"]))
	b.set("dong", [])
	try:
		b.save(ignore_permissions=True)
	except frappe.ValidationError as e:
		dung("chặn đúng lý do giữ dòng", "Giữ dòng để đối chiếu" in str(e))
	else:
		dung("không được xoá child đã đếm 0", False)
	b.reload()
	la("DB còn dòng", len(b.dong), 1)
