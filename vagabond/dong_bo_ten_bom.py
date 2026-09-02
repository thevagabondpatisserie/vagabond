# -*- coding: utf-8 -*-
"""Đồng bộ TÊN món lưu sẵn trong công thức với tên trong danh mục Hàng hoá.

Vì sao có tệp này
-----------------
ERPNext chép tên món vào dòng công thức lúc thêm dòng và KHÔNG bao giờ chép
lại. Đổi tên một món bên danh mục thì mọi công thức cũ vẫn giữ tên cũ mãi
mãi. Ngày 02/09/2026 anh Việt chụp màn Kế hoạch sản xuất hiện "Nước, ml" cho
món đã đổi tên thành "Nước, gram" từ lâu.

Bản v388 đã chữa phần HIỂN THỊ: mọi màn đọc tên thẳng từ danh mục, nên nhìn
đâu cũng ra tên đúng. Tệp này chữa nốt phần DỮ LIỆU cho những mã anh Việt
chỉ đích danh, để bản thân tờ công thức đọc ra cũng đúng.

Vì sao KHÔNG đồng bộ tất
------------------------
Đo trên site ngày 02/09/2026: 1.650 trên 2.384 dòng công thức đang giữ tên
cũ, thuộc 103 mã. Phần lớn là dư âm của lần cắt quy cách khỏi tên món hồi
v310, ví dụ "Bơ lạt Avonmore, Unsalted Butter, Khối 2,5kg, Ireland" nay còn
"Bơ lạt Avonmore, Unsalted Butter, Ireland".

Sửa một lượt 1.650 dòng là chạm vào 103 mã mà anh Việt chưa xem qua, trong
đó có cả những cái tên còn ghi quy cách đóng gói mà bếp có thể đang dùng để
nhận dạng. Nên tệp này chỉ đồng bộ những mã CÓ TÊN TRONG DANH SÁCH dưới đây.
Muốn thêm mã thì anh Việt gật đầu rồi thêm vào danh sách, không tự quét cả
bảng.

Hàm `soat()` chỉ ĐỌC, liệt kê hết mọi chỗ lệch để anh Việt xem rồi quyết.

Chỉ chạm đúng một ô
-------------------
Chỉ ghi ô TÊN. Không chạm số lượng, không chạm đơn vị, không chạm hệ số quy
đổi, không chạm công thức cha. Tên là ô để người đọc, không đi vào phép tính
nào cả, nên sửa nó không làm lệch một con số.
"""

import frappe

DT = "BOM Item"
DT_NO = "BOM Explosion Item"

# Mã được phép đồng bộ tên. Anh Việt chốt 02/09/2026: *"Vậy em cứ giữ nguyên
# Nước, gram. Rồi thay vào các công thức cho nó đồng bộ đơn vị gram."*
#
# NVLT00231 là nước máy: danh mục ghi "Nước, gram", đơn vị Gram, không quản
# tồn. 43 dòng công thức còn giữ tên cũ "Nước, ml". Đơn vị trong các dòng đó
# VỐN ĐÃ là Gram, chỉ mỗi cái tên là cũ.
MA_DONG_BO = ("NVLT00231",)


# ----------------------------------------------------------- phần THUẦN

def can_doi(ten_dong, ten_danh_muc):
	"""Dòng này có cần đổi tên không. THUẦN.

	Tên danh mục rỗng thì KHÔNG đổi: thà giữ tên cũ còn hơn xoá trắng ô tên
	của một dòng công thức.
	"""
	moi = str(ten_danh_muc or "").strip()
	if not moi:
		return False
	return str(ten_dong or "").strip() != moi


# ------------------------------------------------------ phần chạm Frappe

def _ten_danh_muc(cac_ma):
	ra = {}
	cac_ma = sorted({str(m).strip() for m in (cac_ma or []) if str(m).strip()})
	for i in range(0, len(cac_ma), 100):
		for d in frappe.get_all("Item", filters={"name": ["in", cac_ma[i:i + 100]]},
			fields=["name", "item_name"], limit_page_length=0):
			ra[d["name"]] = d.get("item_name") or ""
	return ra


def _dong_cua(bang, cac_ma):
	try:
		return frappe.get_all(bang, filters={"item_code": ["in", list(cac_ma)]},
			fields=["name", "item_code", "item_name"], limit_page_length=0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dong_bo_ten_bom: doc %s" % bang)
		return []


def dong_bo(cac_ma=None):
	"""Ghi lại ô tên cho các mã trong danh sách. Chạy lại nhiều lần không sao.

	Trả về {bảng: số dòng đã đổi}. Lần chạy thứ hai trả về 0 vì không còn
	dòng nào lệch.
	"""
	cac_ma = tuple(cac_ma or MA_DONG_BO)
	if not cac_ma:
		return {}
	ten = _ten_danh_muc(cac_ma)
	ra = {}
	for bang in (DT, DT_NO):
		dem = 0
		for d in _dong_cua(bang, cac_ma):
			moi = ten.get(d["item_code"], "")
			if not can_doi(d.get("item_name"), moi):
				continue
			# CHỈ ô tên. `update_modified=False` để không đụng dấu thời gian
			# của tờ công thức: đây không phải một lần ai đó sửa công thức.
			frappe.db.set_value(bang, d["name"], "item_name", moi,
				update_modified=False)
			dem += 1
		ra[bang] = dem
	return ra


def dung():
	"""Gọi trong after_migrate. Hỏng thì ghi nhật ký, không chặn migrate."""
	try:
		ra = dong_bo()
		if any(ra.values()):
			frappe.logger().info("dong_bo_ten_bom: %s" % ra)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dong_bo_ten_bom: dung")


@frappe.whitelist()
def soat():
	"""LIỆT KÊ mọi chỗ tên trong công thức lệch với danh mục. Chỉ đọc.

	Không sửa gì. Dùng để anh Việt xem rồi quyết mã nào cho đồng bộ, đúng
	điều anh chốt 13/08/2026: phát hiện sai sót thì liệt kê ra, không tự sửa.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	dong = frappe.get_all(DT, fields=["item_code", "item_name"], limit_page_length=0)
	ten = _ten_danh_muc([d["item_code"] for d in dong])
	gom = {}
	for d in dong:
		moi = ten.get(d["item_code"], "")
		if not can_doi(d.get("item_name"), moi):
			continue
		k = d["item_code"]
		o = gom.setdefault(k, {
			"ma_hang": k, "ten_danh_muc": moi,
			"ten_trong_cong_thuc": d.get("item_name") or "", "so_dong": 0,
			"da_dong_bo": 1 if k in MA_DONG_BO else 0,
		})
		o["so_dong"] += 1
	ra = sorted(gom.values(), key=lambda o: (-o["so_dong"], o["ma_hang"]))
	return {
		"tong_dong": len(dong),
		"so_dong_lech": sum(o["so_dong"] for o in ra),
		"so_ma_lech": len(ra),
		"chi_tiet": ra,
	}
