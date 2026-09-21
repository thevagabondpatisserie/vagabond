# -*- coding: utf-8 -*-
"""v515: them tai khoan nhan tien cua nha cung cap NGAY TAI CHO.

Uyen bao 21/09/2026: o man Thanh toan truoc cho NCC, man chi bao "chua co so
tai khoan" ma khong co loi nhap; anh Viet chup them form Desk, the "Tai
khoan ngan hang" cung khong co nut them. Cua sua o v509 chi nam trong app,
muc Danh muc > Nha cung cap, khong ai tim ra.

Ca kiem o day chot phan may chu va dang ky. Hanh vi bam tren man Thanh toan
truoc chay that o hanh_vi/stk_tai_cho_515.js (DOM gia).
"""

import io
import os
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import ncc, tra_truoc
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("v515: duoc_sua_tk là nguồn duy nhất cho cổng chặn và cho nút trên màn")
def _quyen():
	la("thu mua sửa được", ncc.duoc_sua_tk(["Purchase User"]), True)
	la("AP Giám đốc sửa được", ncc.duoc_sua_tk(["AP Giám đốc"]), True)
	la("kho thì không", ncc.duoc_sua_tk(["Stock User"]), False)
	la("rỗng thì không", ncc.duoc_sua_tk(None), False)
	with patch.object(ncc.frappe, "get_roles", lambda *a: ["Stock User"]):
		try:
			ncc._kiem("thử")
			bi_chan = False
		except Exception:
			bi_chan = True
	dung("_kiem chặn đúng người duoc_sua_tk trả False", bi_chan)


class _Don(SimpleNamespace):
	def get(self, k, d=None):
		return getattr(self, k, d)


def _chi_tiet(vai, tk):
	don = _Don(name="DMH-1", docstatus=1, supplier="NCC-DL", grand_total=1620000, advance_paid=0,
		per_billed=0, transaction_date="2026-09-16", status="To Receive and Bill", currency="VND")
	with patch.object(tra_truoc.frappe.db, "exists", lambda *a, **k: True), \
		patch.object(tra_truoc.frappe, "get_doc", lambda *a, **k: don), \
		patch.object(tra_truoc.frappe.db, "get_value", lambda *a, **k: {"supplier_name": "Duy Lợi", "tax_id": "0315917706"}), \
		patch.object(tra_truoc.frappe, "get_roles", lambda *a: vai), \
		patch.object(tra_truoc.frappe, "session", SimpleNamespace(user="uyen@vgb")), \
		patch.object(tra_truoc, "_dia_chi_ncc", lambda ma: ""), \
		patch.object(ncc, "_tai_khoan", lambda ma: tk):
		return tra_truoc.chi_tiet_don("DMH-1")


@ca("v515: chi_tiet_don báo sua_tk theo vai; kế toán không có vai NCC thì 0")
def _co_co():
	rong = {"ten": "", "chu_tk": "", "so_tk": "", "ngan_hang": ""}
	la("thu mua: bật nút", _chi_tiet(["Purchase User"], rong)["ncc"]["sua_tk"], 1)
	# AP Officer lập được phiếu trả trước (QUYEN_LAP) nhưng không sửa được hồ
	# sơ NCC (QUYEN_NCC): bày nút cho họ là bấm vào ăn lỗi quyền.
	la("chỉ AP Officer: không bật nút", _chi_tiet(["AP Officer"], rong)["ncc"]["sua_tk"], 0)
	la("chưa có tài khoản thì tai_khoan rỗng", _chi_tiet(["Purchase User"], rong)["ncc"]["tai_khoan"], {})


@ca("v515: màn trả trước đọc tài khoản MẶC ĐỊNH qua ncc._tai_khoan, cùng nguồn với phiếu chi")
def _cung_nguon():
	tk = {"ten": "TK-MOI", "chu_tk": "DUY LOI", "so_tk": "0999", "ngan_hang": "MB"}
	# Trước v515 hàm tự đọc Bank Account, lấy dòng đầu không theo mặc định:
	# sửa tài khoản đã có phiếu trỏ tới thì máy giữ bản cũ, tạo bản mới làm
	# mặc định, màn này có thể hiện số CŨ trong khi phiếu lập ra gắn số MỚI.
	def _cam(*a, **k):
		raise AssertionError("không được tự đọc Bank Account nữa")
	with patch.object(ncc, "_tai_khoan", lambda ma: tk), patch.object(tra_truoc.frappe, "get_all", _cam):
		la("đúng số mặc định", tra_truoc._tk_ncc("NCC-DL"), {"so_tk": "0999", "ngan_hang": "MB", "chu_tk": "DUY LOI"})


@ca("v515: form Desk Nhà cung cấp có nút thêm/sửa tài khoản, ghi qua cùng một cổng")
def _desk():
	h = _doc("vagabond", "hooks.py")
	dung("hooks gắn supplier.js cho Supplier", '"Supplier": "public/js/supplier.js"' in h)
	j = _doc("vagabond", "public", "js", "supplier.js")
	dung("đọc qua ncc.tai_khoan", "vagabond.ncc.tai_khoan" in j)
	dung("ghi qua ncc.luu_tai_khoan, không tự tạo Bank Account",
		"vagabond.ncc.luu_tai_khoan" in j and "frappe.new_doc" not in j and "frappe.db.insert" not in j)
	dung("chỉ bày nút khi được sửa", "if (!tk.sua) return;" in j)
	with patch.object(ncc.frappe.db, "exists", lambda *a, **k: True), \
		patch.object(ncc.frappe, "has_permission", create=True, new=lambda *a, **k: True), \
		patch.object(ncc.frappe, "get_roles", lambda *a: ["Stock User"]), \
		patch.object(ncc, "_tai_khoan", lambda ma: {"ten": "", "chu_tk": "", "so_tk": "", "ngan_hang": ""}):
		la("kho xem được nhưng sua=0", ncc.tai_khoan("NCC-DL")["sua"], 0)
	with patch.object(ncc.frappe.db, "exists", lambda *a, **k: True), \
		patch.object(ncc.frappe, "has_permission", create=True, new=lambda *a, **k: False):
		try:
			ncc.tai_khoan("NCC-DL")
			bi_chan = False
		except Exception:
			bi_chan = True
	dung("không có quyền đọc NCC thì chặn", bi_chan)


@ca("v515: đăng ký đủ: cửa ngõ, ca hành vi trong cổng, APPVER, patch")
def _dang_ky():
	c = _doc("vagabond", "khung", "kiem_thu", "thu_cua_ngo.py")
	dung("tai_khoan trong cửa ngõ ncc.py", '"tai_khoan"' in c.split('"ncc.py"')[1].split("\n")[0])
	sh = _doc("kiem_truoc_deploy.sh")
	dung("ca hành vi nằm trong cổng", "hanh_vi/stk_tai_cho_515.js" in sh)
	v = _doc("vagabond", "public", "js", "bep", "12-van-don.js")
	dung("APPVER 515", "var APPVER = '515';" in v)
	dung("patch #v515", "#v515" in _doc("vagabond", "patches.txt"))
