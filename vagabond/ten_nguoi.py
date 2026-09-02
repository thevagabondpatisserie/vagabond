# -*- coding: utf-8 -*-
"""MỘT cách duy nhất đổi mã tài khoản thành tên người, cho cả hệ.

Anh Việt chốt 02/09/2026, sau khi mở màn Duyệt đơn hàng tặng và thấy ô
"Người duyệt" ghi `thevagabond.marketing@gmai...` bị cắt cụt giữa chừng:

    "Tất cả các chỗ hiện tên người thao tác phải là hiện tên chứ không
    hiện email (trong cả app, erp desktop, email gửi đi,...) phải sửa ở
    backend để làm mặc định về sau."

BA LỚP, và phải đủ cả ba mới thành mặc định thật
--------------------------------------------------------------------
1. Lớp này: `ten()` và `nhieu()` đổi mã tài khoản thành họ tên. Mọi mô đun
   trả dữ liệu ra màn hình đều gọi qua đây chứ không tự `get_value` nữa.
   Trước 02/09 có tới bốn bản `_ten_nguoi` chép qua chép lại ở bốn tệp,
   mỗi bản xử lý trường hợp thiếu tên một kiểu.

2. `gan()` bơm thêm ô `<tên trường>_ten` bên cạnh ô cũ. CỐ Ý không ghi đè
   ô cũ: mã tài khoản vẫn là thứ dùng để so sánh quyền, để lọc, để tra
   ngược. Ghi đè là mất khoá.

3. `dung()` bật cờ hiện tên trên doctype User, để MỌI ô Link trỏ tới User
   trong toàn bộ ERPNext bản máy tính đều hiện họ tên thay vì địa chỉ thư.
   Đây là phần "mặc định về sau": ô mới ai đó thêm sau này cũng tự đúng,
   không phải nhớ.

Ai cũng có thể chưa có họ tên (tài khoản mới lập, tài khoản máy). Khi đó
trả về phần trước dấu @ chứ KHÔNG trả về cả địa chỉ thư: hiện nửa địa chỉ
còn đọc được, hiện cả địa chỉ thì tràn ô và bị cắt cụt như ảnh anh Việt gửi.
"""

import frappe

# Tài khoản máy, không phải người. Hiện đúng như vậy để người đọc biết đây
# là việc hệ thống tự làm chứ không phải ai đó bấm.
MAY = {
	"Administrator": "Hệ thống",
	"Guest": "Khách vãng lai",
}

_NHO_KHOA = "vgb_ten_nguoi"
_NHO_GIAY = 3600


def _tho(ma):
	"""Phương án cuối: phần trước dấu @, viết hoa chữ đầu."""
	ma = str(ma or "").strip()
	if not ma:
		return ""
	dau = ma.split("@")[0].strip()
	return dau or ma


def ten(ma):
	"""Họ tên của một tài khoản. Không có thì trả phần trước dấu @."""
	ma = str(ma or "").strip()
	if not ma:
		return ""
	if ma in MAY:
		return MAY[ma]
	try:
		nho = frappe.cache().hget(_NHO_KHOA, ma)
	except Exception:
		nho = None
	if nho:
		return nho
	try:
		ht = frappe.db.get_value("User", ma, "full_name")
	except Exception:
		ht = None
	ht = (ht or "").strip()
	# Frappe dat full_name bang chinh dia chi thu khi tai khoan chua khai
	# ho ten. Coi nhu chua co.
	if ht.lower() == ma.lower():
		ht = ""
	if not ht:
		# Ho so nhan su thuong co ten day du hon tai khoan. Anh Viet khoanh
		# do man Ho so thanh toan ngay 13/08/2026 cung vi ly do nay.
		try:
			nv = frappe.db.get_value("Employee", {"user_id": ma}, "employee_name")
		except Exception:
			nv = None
		ht = (nv or "").strip()
	ra = ht or _tho(ma)
	try:
		frappe.cache().hset(_NHO_KHOA, ma, ra)
	except Exception:
		pass
	return ra


def nhieu(ds):
	"""Đổi cả một danh sách trong MỘT lượt đọc, trả về bảng mã -> tên.

	Danh sách phiếu có hai trăm dòng thì gọi `ten()` hai trăm lần là hai
	trăm lượt đọc cơ sở dữ liệu. Hàm này gom lại còn một.
	"""
	can = []
	ra = {}
	for m in ds or []:
		m = str(m or "").strip()
		if not m or m in ra:
			continue
		if m in MAY:
			ra[m] = MAY[m]
			continue
		try:
			nho = frappe.cache().hget(_NHO_KHOA, m)
		except Exception:
			nho = None
		if nho:
			ra[m] = nho
		else:
			can.append(m)
	if can:
		try:
			for r in frappe.get_all(
				"User", filters={"name": ["in", can]},
				fields=["name", "full_name"], limit_page_length=0,
				ignore_permissions=True,
			):
				t = (r.get("full_name") or "").strip() or _tho(r["name"])
				ra[r["name"]] = t
				try:
					frappe.cache().hset(_NHO_KHOA, r["name"], t)
				except Exception:
					pass
		except Exception:
			pass
		for m in can:
			ra.setdefault(m, _tho(m))
	return ra


def gan(d, *o):
	"""Bơm thêm `<ô>_ten` vào một bản ghi, giữ nguyên ô mã.

	Nhận cả dict lẫn danh sách dict, nên dùng được cho một phiếu hay cho
	cả một trang danh sách.
	"""
	if d is None:
		return d
	ds = d if isinstance(d, (list, tuple)) else [d]
	ma = []
	for r in ds:
		if not isinstance(r, dict):
			continue
		for k in o:
			v = r.get(k)
			if v:
				ma.append(v)
	bang = nhieu(ma)
	for r in ds:
		if not isinstance(r, dict):
			continue
		for k in o:
			v = r.get(k)
			r[k + "_ten"] = bang.get(v) or _tho(v) if v else ""
	return d


def quen(ma=None):
	"""Xoá phần nhớ. Gọi khi ai đó đổi họ tên."""
	try:
		if ma:
			frappe.cache().hdel(_NHO_KHOA, str(ma))
		else:
			frappe.cache().delete_key(_NHO_KHOA)
	except Exception:
		pass


def dung():
	"""Bật cờ hiện tên cho mọi ô Link trỏ tới User trong bản máy tính.

	Frappe mặc định hiện KHOÁ của bản ghi được trỏ tới, mà khoá của User
	chính là địa chỉ thư. Bật `show_title_field_in_link` thì nó hiện ô
	tiêu đề, tức là họ tên, ở mọi ô Link trong toàn hệ. Một dòng, và mọi
	ô thêm sau này cũng tự đúng.

	Lặp lại được không giới hạn lần.
	"""
	from frappe.custom.doctype.property_setter.property_setter import (
		make_property_setter,
	)

	try:
		make_property_setter(
			"User", None, "show_title_field_in_link", 1, "Check",
			for_doctype=True, validate_fields_for_doctype=False,
		)
		# O tieu de cua User la full_name. Khai lai cho chac, vi neu o nay
		# trong thi co tren khong co tac dung gi.
		make_property_setter(
			"User", None, "title_field", "full_name", "Data",
			for_doctype=True, validate_fields_for_doctype=False,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ten_nguoi: bat hien ten o o Link")
