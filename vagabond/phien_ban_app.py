# -*- coding: utf-8 -*-
"""v657: số bản app đang có trên máy chủ, để máy đang mở app biết mà tải lại.

Vì sao có tệp này (Dễ báo 14/11/2026, ảnh phiếu tạm tính HDB-26-11-02668 in
13:11): mã QR chuyển khoản in ra chỉ còn một góc, đúng lỗi v655 đã sửa và đã
deploy lúc 01:43 cùng ngày. Dựng lại đúng phiếu đó bằng mã trước v655 thì ra
y hệt ảnh; bằng mã hiện tại thì ra đủ ô. Máy quầy để trang app mở từ hôm
trước nên vẫn chạy bản cũ: app nạp mã một lần lúc mở trang và không có cách
nào biết máy chủ đã có bản mới. Mọi bản sửa đều không tới quầy cho tới khi ai
đó tự tải lại trang.

Trang app hỏi số bản ở đây vài phút một lần (73-ban-moi.js). Số đọc thẳng từ
tệp nguồn của app đang cài trên máy chủ, cùng cách đọc với chốt chặn hạ số
APPVER (trang.so_appver), nên không có chỗ thứ hai phải nhớ tăng số.
"""

import os

import frappe

# Tệp nguồn mang dòng `var APPVER = '...'` của app /bep.
TEP_APPVER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
	"public", "js", "bep", "12-van-don.js")

_DEM = {"luc": None, "so": -1}


def doc_so(duong=TEP_APPVER):
	"""Số APPVER trong tệp nguồn, -1 khi không đọc được. Nhớ theo giờ sửa tệp."""
	from vagabond.trang import so_appver
	try:
		luc = os.path.getmtime(duong)
	except OSError:
		return -1
	if _DEM["luc"] != (duong, luc):
		with open(duong, encoding="utf-8") as f:
			_DEM["so"] = so_appver(f.read())
		_DEM["luc"] = (duong, luc)
	return _DEM["so"]


@frappe.whitelist()
def hien_tai():
	"""Số bản app trên máy chủ. Chỉ người đã đăng nhập gọi được."""
	return {"appver": doc_so()}
