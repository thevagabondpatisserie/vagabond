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


# ------------------------------------------------ v537: xuất Excel mọi báo cáo

@ca("v537 xuất Excel: chỉ bật export cho vai kế toán ĐÃ đọc được doctype gốc của báo cáo, không cấp read, không lặp doctype")
def _():
	doc = {("Purchase Invoice", "Accounts User"), ("Purchase Invoice", "Accounts Manager"),
		("Purchase Invoice", "AP Kiểm soát (FIN)"), ("GL Entry", "Accounts User"), ("Sales Invoice", "Accounts Manager")}
	xuat = {("GL Entry", "Accounts User")}
	kh = quyen_ap.ke_hoach_xuat_excel(["Purchase Invoice", "Purchase Invoice", "GL Entry", "Sales Invoice", "", None, "Stock Ledger Entry"],
		lambda dt, vai: (dt, vai) in doc, lambda dt, vai: (dt, vai) in xuat)
	la("kế hoạch", kh, [("Purchase Invoice", "Accounts User"), ("Purchase Invoice", "Accounts Manager"),
		("Purchase Invoice", "AP Kiểm soát (FIN)"), ("Sales Invoice", "Accounts Manager")])
	dung("không đụng doctype vai chưa đọc được", not any(dt == "Stock Ledger Entry" for dt, _ in kh))
	la("ba vai kế toán, có chị Dung (AP Kiểm soát FIN)", sorted(quyen_ap.VAI_XUAT_EXCEL),
		["AP Kiểm soát (FIN)", "Accounts Manager", "Accounts User"])


@ca("v537 xuất Excel: patch đọc bảng Report trên site, cấp qua hai hàm của Frappe, chỉ bật ô export, hỏng thì làm hỏng migrate")
def _():
	import sys
	import unittest.mock
	from types import SimpleNamespace as NS
	from vagabond.khung.kiem_thu.nen import nem
	goi_ = []
	quyen = {("Purchase Invoice", "Accounts User"): {"read": 1, "export": 0},
		("Purchase Invoice", "Accounts Manager"): {"read": 1, "export": 1},
		("Sales Invoice", "Accounts User"): {"read": 1, "export": 0}}

	def _doc_duoc(dt, vai):
		return bool(quyen.get((dt, vai), {}).get("read"))

	def _thieu(dt, vai, q):
		return not quyen.get((dt, vai), {}).get(q)

	def throw(m):
		raise ValueError(m)
	f = NS(get_all=lambda dt, **k: ["Purchase Invoice", "Purchase Invoice", "Sales Invoice", "Report Khong Co", None],
		db=NS(exists=lambda dt, n=None: n != "Report Khong Co"),
		clear_cache=lambda: goi_.append("cache"), throw=throw)
	perms = NS(add_permission=lambda dt, vai, lv: goi_.append(("add", dt, vai)),
		update_permission_property=lambda dt, vai, lv, q, v: (goi_.append(("set", dt, vai, q, v)), quyen[(dt, vai)].__setitem__(q, v)))
	with unittest.mock.patch.object(quyen_ap, "frappe", f), unittest.mock.patch.object(quyen_ap, "_thieu", _thieu), \
			unittest.mock.patch.object(quyen_ap, "_doc_duoc", _doc_duoc), \
			unittest.mock.patch.object(quyen_ap, "_xuat_duoc", lambda dt, vai: not _thieu(dt, vai, "export")), \
			unittest.mock.patch.dict(sys.modules, {"frappe.permissions": perms}):
		kq = quyen_ap.cap_xuat_excel_v537()
	la("cấp đúng hai dòng đang thiếu", kq["them"], ["Purchase Invoice · Accounts User", "Sales Invoice · Accounts User"])
	la("đi qua add_permission rồi chỉ bật export", [g for g in goi_ if g != "cache"],
		[("add", "Purchase Invoice", "Accounts User"), ("set", "Purchase Invoice", "Accounts User", "export", 1),
		("add", "Sales Invoice", "Accounts User"), ("set", "Sales Invoice", "Accounts User", "export", 1)])
	dung("xoá cache sau khi cấp", "cache" in goi_)
	# Cấp không ăn thì ném, để migrate đỏ chứ không báo xong giả.
	perms.update_permission_property = lambda *a: None
	quyen[("Purchase Invoice", "Accounts User")]["export"] = 0
	with unittest.mock.patch.object(quyen_ap, "frappe", f), unittest.mock.patch.object(quyen_ap, "_thieu", _thieu), \
			unittest.mock.patch.object(quyen_ap, "_doc_duoc", _doc_duoc), \
			unittest.mock.patch.object(quyen_ap, "_xuat_duoc", lambda dt, vai: not _thieu(dt, vai, "export")), \
			unittest.mock.patch.dict(sys.modules, {"frappe.permissions": perms}):
		nem("cấp không ăn thì ném", quyen_ap.cap_xuat_excel_v537, ValueError)
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	p = io.open(os.path.join(goi, "patches", "xuat_excel_v537.py"), encoding="utf-8").read()
	dung("patch gọi đúng hàm, không bọc try", "cap_xuat_excel_v537()" in p and "except" not in p)
	dong = io.open(os.path.join(goi, "patches.txt"), encoding="utf-8").read().splitlines()
	dung("patches.txt có dòng v537 trước dòng đồng bộ cấu trúc",
		dong.index("vagabond.patches.xuat_excel_v537") < dong.index("vagabond.patches.dong_bo_cau_truc #v537"))


# ------------------------------------------------ Codex #385: hai finding P2 trên mã v537

@ca("v537 sửa #385: quyền hiệu lực đọc Custom DocPerm nếu doctype đã có dòng tuỳ biến, ngược lại đọc DocPerm chuẩn")
def _():
	tb = [{"role": "Accounts User", "permlevel": 0, "if_owner": 0, "read": 1, "export": 0}]
	chuan = [{"role": "Accounts User", "permlevel": 0, "if_owner": 0, "read": 1, "export": 1},
		{"role": "Accounts Manager", "permlevel": 1, "if_owner": 0, "read": 1, "export": 1},
		{"role": "Stock User", "permlevel": 0, "if_owner": 1, "read": 1, "export": 1}]
	f = quyen_ap.co_quyen_hieu_luc
	dung("chưa có dòng tuỳ biến: bảng chuẩn cho export là đã xuất được", f([], chuan, "Accounts User", "export"))
	dung("đã có dòng tuỳ biến: bảng chuẩn hết hiệu lực", not f(tb, chuan, "Accounts User", "export"))
	dung("đọc được theo dòng tuỳ biến", f(tb, chuan, "Accounts User", "read"))
	dung("dòng permlevel 1 không tính", not f([], chuan, "Accounts Manager", "export"))
	dung("dòng chỉ-chủ-sở-hữu không tính", not f([], chuan, "Stock User", "export"))
	dung("vai không có dòng", not f([], chuan, "AP Kiểm soát (FIN)", "read"))


@ca("v537 sửa #385 (P2 thứ nhất): doctype mà bảng quyền CHUẨN đã cho export thì patch không gọi add_permission, không đóng băng bảng chuẩn")
def _():
	# Chạy thật cap_xuat_excel_v537 với _doc_duoc/_xuat_duoc thật, chỉ giả
	# bảng DocPerm/Custom DocPerm trong bộ nhớ. Tái hiện trên 393374be:
	# Sales Invoice chưa có dòng tuỳ biến, bảng chuẩn cho Accounts User
	# read+export, bản cũ vẫn gọi add_permission (đóng băng bảng chuẩn).
	import sys
	import unittest.mock
	from types import SimpleNamespace as NS
	bang = {"DocPerm": {
		"Sales Invoice": [{"role": v, "permlevel": 0, "if_owner": 0, "read": 1, "export": 1}
			for v in quyen_ap.VAI_XUAT_EXCEL],
		"Purchase Invoice": [{"role": v, "permlevel": 0, "if_owner": 0, "read": 1, "export": 0}
			for v in quyen_ap.VAI_XUAT_EXCEL]},
		"Custom DocPerm": {}}
	goi_ = []

	def get_all(dt, filters=None, fields=None, pluck=None, **k):
		if dt == "Report":
			return ["Sales Invoice", "Purchase Invoice"]
		return [dict(r) for r in bang[dt].get(filters["parent"], [])]

	def add_permission(dt, vai, lv):
		goi_.append(("add", dt, vai))
		if not bang["Custom DocPerm"].get(dt):
			bang["Custom DocPerm"][dt] = [dict(r) for r in bang["DocPerm"][dt]]

	def update_permission_property(dt, vai, lv, q, v):
		goi_.append(("set", dt, vai, q))
		for r in bang["Custom DocPerm"][dt]:
			if r["role"] == vai and not r["permlevel"]:
				r[q] = v

	def _thieu(dt, vai, q):
		return not quyen_ap.co_quyen_hieu_luc(bang["Custom DocPerm"].get(dt), [], vai, q)

	def throw(m):
		raise ValueError(m)
	f = NS(get_all=get_all, db=NS(exists=lambda dt, n=None: True), clear_cache=lambda: None, throw=throw)
	perms = NS(add_permission=add_permission, update_permission_property=update_permission_property)
	with unittest.mock.patch.object(quyen_ap, "frappe", f), unittest.mock.patch.object(quyen_ap, "_thieu", _thieu), \
			unittest.mock.patch.dict(sys.modules, {"frappe.permissions": perms}):
		kq = quyen_ap.cap_xuat_excel_v537()
		kq2 = quyen_ap.cap_xuat_excel_v537()
	dung("không đụng Sales Invoice", not any(g[1] == "Sales Invoice" for g in goi_))
	dung("Sales Invoice vẫn chưa có dòng tuỳ biến", "Sales Invoice" not in bang["Custom DocPerm"])
	la("chỉ cấp Purchase Invoice cho ba vai", sorted(kq["them"]),
		sorted("Purchase Invoice · %s" % v for v in quyen_ap.VAI_XUAT_EXCEL))
	la("chạy lần hai không thêm gì", kq2["them"], [])


@ca("v537 sửa #385 (P2 thứ hai): đồng bộ cấu trúc MỖI lần migrate gọi lại cấp xuất Excel, lỗi ở đó không chặn migrate")
def _():
	import unittest.mock
	from vagabond.patches import dong_bo_cau_truc as dbct
	goi_ = []

	def hong():
		goi_.append(1)
		raise RuntimeError("gia lap cap hong")
	m = unittest.mock.MagicMock()
	with unittest.mock.patch.object(quyen_ap, "cap_xuat_excel_v537", hong), \
			unittest.mock.patch.object(dbct, "frappe", m):
		loi = None
		try:
			dbct.execute()
		except Exception as e:  # noqa: BLE001
			loi = e
	la("được gọi đúng một lần mỗi lượt đồng bộ", len(goi_), 1)
	dung("lỗi không chặn migrate", loi is None)
	dung("lỗi ghi Error Log", any("quyen xuat Excel" in str(c) for c in m.log_error.call_args_list))
