# -*- coding: utf-8 -*-
"""Ba vai duyet phieu chi phai doc duoc chung tu goc ma phieu tro toi.

Anh Viet 21/08/2026: chi Dung mo phieu APP-26-08-534 de kiem tra thi man
hinh bao "khong co quyen truy cap doctype qua quyen vai tro cho tai lieu
Don mua hang". Chi ay la ke toan truong.

Goc re: ERPNext `set_missing_ref_details` goi `get_reference_details`, ma
ham do mo dau bang `frappe.has_permission(reference_doctype, "read", ...,
throw=True)`. Phep kiem chay luc LUU phieu chu khong phai luc mo man hinh,
nen no chi lo ra dung luc bam nut duyet.

Tu v265 luong tra truoc neo vao Purchase Order, va ca ba buoc cua luong
duyet deu luu phieu, nen ca ba vai deu can quyen doc.
"""

import io
import os

from vagabond import ho_so_tt as hs
from vagabond import quyen_ap
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _js(ten):
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


def _src():
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	return io.open(os.path.join(goi, "quyen_ap.py"), encoding="utf-8").read()


@ca("quyền AP: ba vai trong quyen_ap trùng từng ký tự với bảng PAYFLOW bên JS")
def _():
	js = _js("04-tao-phieu.js")
	khuc = js.split("var PAYFLOW = [")[1].split("];")[0]
	vai_js = set()
	for manh in khuc.split("role: '")[1:]:
		vai_js.add(manh.split("'")[0])
	dung("bảng PAYFLOW đọc ra được ba vai", len(vai_js) == 3)
	la("ba vai khớp nhau", sorted(quyen_ap.VAI_DUYET), sorted(vai_js))


@ca("quyền AP: không bỏ sót vai nào của luồng duyệt")
def _():
	for vai in ("AP Officer", "AP Kiểm soát (FIN)", "AP Giám đốc"):
		dung("có %s" % vai, vai in quyen_ap.VAI_DUYET)


@ca("quyền AP: cấp read và print trên Purchase Order cho cả ba vai")
def _():
	can = quyen_ap.can_cap()
	la("đủ 3 vai x 2 quyền", len(can), 6)
	for vai in quyen_ap.VAI_DUYET:
		dung("%s có read" % vai, ("Purchase Order", vai, "read") in can)
		dung("%s có print" % vai, ("Purchase Order", vai, "print") in can)


@ca("quyền AP: read phải đứng trước print, vì print mà thiếu read là quyền không hợp lệ")
def _():
	la("thứ tự quyền", list(quyen_ap.QUYEN), ["read", "print"])


@ca("quyền AP: chỉ đụng vào Purchase Order, không lan sang doctype khác")
def _():
	# Purchase Invoice da co san quyen qua Accounts User, va no CHUA co dong
	# Custom DocPerm nao. Them vao la dong bang quyen cua no khoi moi ban
	# nang cap ERPNext ve sau. Muon them thi phai sua ca ca kiem nay.
	la("đúng một doctype", list(quyen_ap.CHUNG_TU_GOC), ["Purchase Order"])
	dung("không đụng Purchase Invoice", "Purchase Invoice" not in quyen_ap.CHUNG_TU_GOC)


@ca("quyền AP: đi qua add_permission và update_permission_property của Frappe")
def _():
	src = _src()
	dung("gọi add_permission", "add_permission(dt, vai, 0)" in src)
	dung("gọi update_permission_property", "update_permission_property(dt, vai, 0, q, 1)" in src)


@ca("quyền AP: KHÔNG chèn tay dòng Custom DocPerm")
def _():
	src = _src()
	dung("không frappe.new_doc Custom DocPerm", 'new_doc("Custom DocPerm"' not in src)
	dung("không frappe.get_doc dựng Custom DocPerm", '"doctype": "Custom DocPerm"' not in src)
	dung("không insert Custom DocPerm", '"Custom DocPerm"' in src and ".insert(" not in src)


@ca("quyền AP: chạy lại được, lần thứ hai không đổi gì")
def _():
	src = _src()
	dung("có phép kiểm thiếu trước khi cấp", "def _thieu(" in src)
	dung("bỏ qua khi đã đủ", "if not _thieu(dt, vai, q):" in src)
	dung("bỏ qua doctype không có trên hệ", 'frappe.db.exists("DocType", dt)' in src)
	dung("bỏ qua vai không có trên hệ", 'frappe.db.exists("Role", vai)' in src)


@ca("quyền AP: hỏng một dòng không được chặn cả lần migrate")
def _():
	src = _src()
	dung("bọc try trong vòng lặp", "except Exception:" in src)
	dung("ghi bản ghi lỗi", "frappe.log_error(" in src)


@ca("quyền AP: patch có gọi và không chặn migrate khi hỏng")
def _():
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	p = io.open(
		os.path.join(goi, "patches", "dong_bo_cau_truc.py"), encoding="utf-8").read()
	dung("patch có nạp quyen_ap", "from vagabond import quyen_ap" in p)
	dung("patch có gọi dung()", "quyen_ap.dung()" in p)
	khuc = p.split("from vagabond import quyen_ap")[1]
	dung("có bọc except", "except Exception:" in khuc)


@ca("quyền AP: tệp phải giải thích vì sao, không chỉ nêu cách")
def _():
	src = _src()
	dung("nêu tên hàm của ERPNext", "get_reference_details" in src)
	dung("nói rõ phép kiểm chạy lúc lưu", "LUU" in src)
	dung("giải thích cái giá của Custom DocPerm", "DONG BANG" in src)


@ca("khôi phục: đặt lại quyền Phiếu thu/chi cho hai vai kế toán chuẩn")
def _():
	"""Bảng quyền đóng băng đã lấy mất sạch quyền của hai vai kế toán.

	Trên Payment Entry có ba dòng Custom DocPerm tạo 23/07/2026. Frappe vứt
	bỏ toàn bộ bảng quyền chuẩn khi có dòng tuỳ biến, nên từ hôm đó
	`Accounts User` và `Accounts Manager` trắng quyền. Anh Khải giữ cả hai
	vai đó mà không mở nổi một phiếu thu chi nào.
	"""
	can = quyen_ap.can_khoi_phuc()
	dt = "Payment Entry"
	for vai in ("Accounts Manager", "Accounts User"):
		for q in ("read", "write", "create", "submit", "cancel", "print"):
			dung("%s có %s" % (vai, q), (dt, vai, q) in can)
	# Đây là ĐẶT LẠI chứ không phải nới quyền: không được lén thêm vai nào
	# khác vào bảng khôi phục.
	vai_co = {v for _d, v, _q in can}
	la("chỉ đúng hai vai kế toán", sorted(vai_co), ["Accounts Manager", "Accounts User"])
	dt_co = {d for d, _v, _q in can}
	la("chỉ đụng Payment Entry", sorted(dt_co), ["Payment Entry"])


@ca("khôi phục: dung() phải chạy CẢ hai bảng, không bỏ sót bảng nào")
def _():
	import inspect

	src = inspect.getsource(quyen_ap.dung)
	dung("có gọi can_cap", "can_cap()" in src)
	dung("có gọi can_khoi_phuc", "can_khoi_phuc()" in src)
	# Vẫn phải đi qua hai hàm của Frappe. Chèn tay một dòng Custom DocPerm
	# vào doctype chưa có dòng nào chính là cái đẻ ra sự cố này.
	dung("đi qua add_permission", "add_permission(" in src)
	dung("đi qua update_permission_property", "update_permission_property(" in src)
