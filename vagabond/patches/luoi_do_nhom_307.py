"""#307: lưới đỡ tài khoản tồn kho theo nhóm món. Idempotent, không đè khai tay.

Lõi ERPNext de591661 khi bật tài khoản theo món tìm ba nấc món, nhóm,
nhãn hiệu rồi CHẶN chứng từ, không quay về kho (xem đầu luoi_do_nhom.py).
Patch gán Item Group Default cho từng nhóm lá đang có món theo tồn, theo
nhóm gốc của cây. Tên nhóm và tài khoản đọc từ site lúc chạy; bảng dự
kiến đã dán lên PR #316 bằng `vagabond.luoi_do_nhom.xem_bang` trước khi
phát hành. Không bật cờ Company, không đụng chứng từ.
"""
import frappe

from vagabond import luoi_do_nhom


def execute():
	for m in luoi_do_nhom.bo_theo_ton_chua_phat_sinh():
		print("luoi_do_nhom_307: %s: %s" % (m["name"],
			"giữ theo tồn vì đã có SLE, Khải cần xử lý" if m["co_sle"] else "đã bỏ theo tồn"))
	kq = luoi_do_nhom.ap_dung()
	print("luoi_do_nhom_307: %s" % kq["dem"])
	for r in kq["bang"]:
		if r["hanh_dong"] != luoi_do_nhom.GAN:
			print("  %s: %s (%s)" % (r["nhom"], r["hanh_dong"], r["ly_do"]))
	frappe.clear_cache(doctype="Item")
