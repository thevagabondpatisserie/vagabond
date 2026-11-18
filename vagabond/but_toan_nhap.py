# -*- coding: utf-8 -*-
"""v674: bút toán NHÁP do máy lập theo tháng, kế toán xem rồi mới ghi sổ.

Vì sao có tệp này
--------------------------------------------------------------------
Anh Việt 18/11/2026 giao hai việc cùng một khuôn: phân bổ chi phí trả trước
(242) hằng tháng và chi phí quảng cáo Meta theo sao kê thẻ. Cả hai đều là "mỗi
công ty, mỗi tháng, máy lập MỘT bút toán nháp, kế toán kiểm rồi ghi sổ". Anh
dặn thêm: "bên cạnh việc máy đề xuất hạch toán thì phải có đường làm thủ công".

Nên khuôn chung giữ đúng ba luật, viết một lần ở đây cho cả hai nơi dùng:

1. Một công ty, một tháng, một loại: chỉ MỘT bút toán nháp đang hiệu lực. Bản
   ghi "Vagabond But Toan Tu Lap" mang tên chính là khoá (loại:công ty:tháng),
   nên hai người bấm cùng lúc thì một bên vấp khoá chính; sau đó cả hai đọc
   bản ghi bằng SELECT FOR UPDATE rồi mới quyết (H8 loại 1: đọc sau khoá).
2. Máy không bao giờ ghi đè tay người. Lúc lập, máy cất dấu các dòng nó viết
   (dau_ban_may). Lần lập sau, bút toán nháp còn đúng dấu đó thì máy cập nhật
   tại chỗ; khác dấu nghĩa là kế toán đã sửa tay, máy dừng và nói rõ hai lựa
   chọn: ghi sổ bản đã sửa, hoặc bỏ bản nháp rồi lập lại.
3. Máy không tự ghi sổ. Ghi sổ là thao tác của kế toán (QUYEN_GHI), qua màn của
   từng việc hoặc màn Hạch toán tay, đường nào cũng được.

Đường thủ công không đi qua đây: kế toán tự lập bút toán ở Hạch toán tay hoặc
trên Desk. Mỗi nơi dùng (chi_phi_242, chi_phi_meta) tự nhận ra bút toán tay đó
để không lập trùng.
"""

import hashlib
import json
from datetime import date, timedelta

DT = "Vagabond But Toan Tu Lap"
LOAI_242 = "Phân bổ 242"
LOAI_META = "Chi phí Meta"
MA_LOAI = {LOAI_242: "PB242", LOAI_META: "META"}

TT_CHUA = "Chưa lập"
TT_NHAP = "Nháp chờ ghi sổ"
TT_SUA_TAY = "Nháp đã sửa tay"
TT_GHI = "Đã ghi sổ"
TT_BO = "Đã bỏ nháp"

QUYEN_XEM = {
	"System Manager", "Accounts Manager", "Accounts User",
	"AP Kiểm soát (FIN)", "AP Giám đốc", "Vagabond Bao cao",
}
QUYEN_LAP = {"System Manager", "Accounts Manager", "Accounts User", "AP Kiểm soát (FIN)"}
QUYEN_GHI = {"System Manager", "Accounts Manager", "AP Kiểm soát (FIN)"}


# ------------------------------------------------------------- phần thuần


def ten_ban_ghi(loai, viet_tat, ky):
	"""Tên bản ghi khoá. THUẦN. ky dạng YYYY-MM."""
	return "%s:%s:%s" % (MA_LOAI[loai], viet_tat, ky)


def ky_hop_le(ky):
	"""ky là chuỗi YYYY-MM có thật. THUẦN. Trả (năm, tháng) hoặc None."""
	s = str(ky or "").strip()
	if len(s) != 7 or s[4] != "-":
		return None
	try:
		y, m = int(s[:4]), int(s[5:])
	except ValueError:
		return None
	if y < 2000 or y > 2100 or m < 1 or m > 12:
		return None
	return y, m


def ngay_cuoi_thang(ky):
	"""Ngày cuối tháng của ky. THUẦN."""
	y, m = ky_hop_le(ky)
	dau_sau = date(y + (m == 12), m % 12 + 1, 1)
	return dau_sau - timedelta(days=1)


def ngay_dau_thang(ky):
	y, m = ky_hop_le(ky)
	return date(y, m, 1)


def ky_cua(ngay):
	"""Tháng của một ngày (date hoặc chuỗi ISO). THUẦN."""
	s = str(ngay or "")[:10]
	return s[:7] if len(s) >= 7 else ""


def cong_thang(ky, n):
	"""ky cộng n tháng (n âm được). THUẦN."""
	y, m = ky_hop_le(ky)
	t = y * 12 + (m - 1) + int(n)
	return "%04d-%02d" % (t // 12, t % 12 + 1)


def so_thang_giua(tu, den):
	"""Số tháng từ ky tu tới ky den (den - tu). THUẦN."""
	y1, m1 = ky_hop_le(tu)
	y2, m2 = ky_hop_le(den)
	return (y2 * 12 + m2) - (y1 * 12 + m1)


def lam_tron_dong(x):
	"""Tiền VND nguyên đồng, làm tròn nửa lên. THUẦN."""
	x = float(x or 0)
	return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def dau_ban(dong):
	"""Dấu nhận dạng các dòng bút toán, không phụ thuộc thứ tự. THUẦN.

	dong: list dict có account, cost_center, debit, credit, khoan. So bằng tiền
	đã làm tròn đồng để 1.000.000 và 1000000.0 cùng một dấu.
	"""
	gon = sorted(
		(
			str(d.get("account") or ""),
			str(d.get("cost_center") or ""),
			lam_tron_dong(d.get("debit")),
			lam_tron_dong(d.get("credit")),
			str(d.get("khoan") or ""),
		)
		for d in (dong or [])
	)
	return hashlib.sha1(json.dumps(gon, ensure_ascii=False).encode("utf-8")).hexdigest()


def kiem_can(dong):
	"""Bút toán cân và mọi dòng một bên. THUẦN. Trả câu lỗi hoặc ''."""
	if not dong or len(dong) < 2:
		return "Bút toán phải có ít nhất hai dòng."
	no = sum(lam_tron_dong(d.get("debit")) for d in dong)
	co = sum(lam_tron_dong(d.get("credit")) for d in dong)
	if no != co:
		return "Bút toán chưa cân: Nợ %s đ, Có %s đ." % ("{:,}".format(no).replace(",", "."), "{:,}".format(co).replace(",", "."))
	for d in dong:
		a, b = lam_tron_dong(d.get("debit")), lam_tron_dong(d.get("credit"))
		if a < 0 or b < 0 or (a and b) or not (a or b):
			return "Mỗi dòng bút toán phải có đúng một bên Nợ hoặc Có, số dương."
	return ""


def trang_thai_ban_ghi(je, dau_may):
	"""Trạng thái của bản ghi theo bút toán đang nối. THUẦN.

	je: None hoặc dict {docstatus, vgb_huy, dau}; dau là dấu các dòng hiện tại.
	"""
	if not je:
		return TT_CHUA
	if int(je.get("vgb_huy") or 0):
		return TT_BO
	ds = int(je.get("docstatus") or 0)
	if ds == 1:
		return TT_GHI
	if ds == 2:
		return TT_BO
	if dau_may and je.get("dau") and je.get("dau") != dau_may:
		return TT_SUA_TAY
	return TT_NHAP


def viec_khi_lap(trang_thai):
	"""Bấm Lập bút toán thì làm gì với bút toán đang nối. THUẦN.

	"moi": lập tờ mới; "cap_nhat": sửa tại chỗ tờ nháp máy lập chưa ai đụng;
	"dung": tờ nháp đã bị sửa tay, máy không đụng, báo người quyết.
	"""
	if trang_thai in (TT_CHUA, TT_BO, TT_GHI):
		return "moi"
	if trang_thai == TT_NHAP:
		return "cap_nhat"
	return "dung"


# ------------------------------------------------ phần chạm Frappe

import frappe  # noqa: E402
from frappe.utils import cint, flt, getdate, now_datetime, nowdate  # noqa: E402


def kiem_quyen(quyen, viec):
	if not (set(frappe.get_roles()) & set(quyen)):
		frappe.throw("Bạn chưa có quyền %s. Nhờ Kế toán trưởng hoặc giám đốc." % viec, frappe.PermissionError)


def co_quyen(quyen):
	return bool(set(frappe.get_roles()) & set(quyen))


def dong_cua_je(je):
	"""Các dòng hiện tại của một Journal Entry, đúng khuôn dau_ban."""
	return [
		{
			"account": r.account,
			"cost_center": r.cost_center or "",
			"debit": flt(r.debit_in_account_currency),
			"credit": flt(r.credit_in_account_currency),
			"khoan": r.get("vgb_khoan_242") or "",
		}
		for r in je.get("accounts") or []
	]


def _thong_tin_je(ten):
	if not ten or not frappe.db.exists("Journal Entry", ten):
		return None
	je = frappe.get_doc("Journal Entry", ten)
	return {"docstatus": je.docstatus, "vgb_huy": cint(je.get("vgb_huy")), "dau": dau_ban(dong_cua_je(je)), "doc": je}


def doc_ban_ghi(loai, cty, ky):
	"""Đọc bản ghi khoá (không khoá) cho màn xem. None nếu chưa có."""
	viet_tat = frappe.db.get_value("Company", cty, "abbr") or cty
	ten = ten_ban_ghi(loai, viet_tat, ky)
	if not frappe.db.exists(DT, ten):
		return None
	return frappe.get_doc(DT, ten)


def tinh_trang(ban_ghi):
	"""Trạng thái hiện hành của một bản ghi (đọc lại bút toán thật)."""
	if not ban_ghi:
		return TT_CHUA, None
	tt = _thong_tin_je(ban_ghi.get("journal_entry"))
	return trang_thai_ban_ghi(tt, ban_ghi.get("dau_ban_may")), tt


def khoa_ban_ghi(loai, cty, ky):
	"""Lấy bản ghi khoá, dựng nếu chưa có, rồi SELECT FOR UPDATE.

	Hai người bấm cùng lúc: một bên chèn được, bên kia vấp khoá chính và đi
	tiếp xuống câu khoá dòng, chờ bên kia xong rồi mới đọc. Mọi quyết định
	sau đó đọc từ bản ghi đã khoá (H8 loại 1)."""
	viet_tat = frappe.db.get_value("Company", cty, "abbr") or cty
	ten = ten_ban_ghi(loai, viet_tat, ky)
	if not frappe.db.exists(DT, ten):
		try:
			frappe.db.savepoint("vgb_tu_lap")
			d = frappe.new_doc(DT)
			d.khoa = ten
			d.loai = loai
			d.company = cty
			d.ky = ky
			d.flags.ignore_permissions = True
			d.flags.vgb_tu_lap = True
			d.insert(ignore_permissions=True)
		except Exception:
			frappe.db.rollback(save_point="vgb_tu_lap")
			if not frappe.db.exists(DT, ten):
				raise
	frappe.db.sql("select name from `tabVagabond But Toan Tu Lap` where name=%s for update", ten)
	return frappe.get_doc(DT, ten)


def chan_khoa_so(ngay):
	"""Ngày hạch toán nằm trong vùng đã khoá sổ thì báo rõ cách gỡ."""
	from vagabond import chung_tu

	moc = chung_tu.ngay_khoa()
	if moc and getdate(ngay) <= getdate(moc):
		frappe.throw(
			"Sổ đã khoá đến %s nên không lập bút toán ngày %s được. Kế toán trưởng mở khoá ở "
			"Cài đặt, mục Khoá sổ, rồi bấm lại." % (getdate(moc).strftime("%d/%m/%Y"), getdate(ngay).strftime("%d/%m/%Y"))
		)


def lap_hoac_cap_nhat(loai, cty, ky, dong, dien_giai, ban_ke=None, tu_lap=None):
	"""Lập (hoặc cập nhật tại chỗ) bút toán nháp của tháng. Trả dict kết quả.

	dong: [{account, cost_center, debit, credit, khoan, user_remark}].
	ban_ke: dữ liệu bản kê (JSON được) cất vào bản ghi để đối chiếu sau.
	Gọi trong cùng giao dịch với phép đọc số liệu; không commit ở đây."""
	loi = kiem_can(dong)
	if loi:
		frappe.throw(loi)
	ngay = ngay_cuoi_thang(ky)
	chan_khoa_so(ngay)
	bg = khoa_ban_ghi(loai, cty, ky)
	tt, info = tinh_trang(bg)
	viec = viec_khi_lap(tt)
	if viec == "dung":
		frappe.throw(
			"Bút toán nháp %s của tháng này đã được sửa tay nên hệ thống không ghi đè. Kế toán chọn: "
			"ghi sổ bản đã sửa, hoặc bấm Bỏ bản nháp rồi Lập lại." % bg.journal_entry
		)
	if viec == "cap_nhat":
		je = info["doc"]
		je.set("accounts", [])
	else:
		je = frappe.new_doc("Journal Entry")
		je.voucher_type = "Journal Entry"
		je.company = cty
	je.posting_date = ngay
	je.user_remark = dien_giai
	je.vgb_tu_lap = tu_lap or ten_ban_ghi(loai, frappe.db.get_value("Company", cty, "abbr") or cty, ky)
	for d in dong:
		hang = {
			"account": d["account"],
			"debit_in_account_currency": lam_tron_dong(d.get("debit")),
			"credit_in_account_currency": lam_tron_dong(d.get("credit")),
			"user_remark": (d.get("user_remark") or "")[:140] or None,
		}
		if d.get("cost_center"):
			hang["cost_center"] = d["cost_center"]
		if d.get("khoan"):
			hang["vgb_khoan_242"] = d["khoan"]
		je.append("accounts", hang)
	je.flags.ignore_permissions = True
	if je.is_new():
		je.insert(ignore_permissions=True)
	else:
		je.save(ignore_permissions=True)
	bg.journal_entry = je.name
	bg.dau_ban_may = dau_ban(dong_cua_je(je))
	# Không truyền bản kê thì GIỮ bản kê cũ (Codex #590): bản kê của Meta là lịch sử các
	# tờ đã lập, xoá về rỗng làm tờ bổ sung lấy lại giao dịch đã ghi sổ.
	if ban_ke is not None:
		bg.ban_ke = json.dumps(ban_ke, ensure_ascii=False, default=str)
	bg.lap_boi = frappe.session.user
	bg.lap_luc = now_datetime()
	bg.flags.ignore_permissions = True
	bg.flags.vgb_tu_lap = True
	bg.save(ignore_permissions=True)
	return {"ok": 1, "journal_entry": je.name, "trang_thai": TT_NHAP, "cap_nhat": 1 if viec == "cap_nhat" else 0}


def bo_nhap(loai, cty, ky, ly_do=None):
	"""Bỏ bút toán nháp đang nối (đánh dấu huỷ mềm, không xoá: QT-20)."""
	from vagabond import chung_tu

	bg = khoa_ban_ghi(loai, cty, ky)
	tt, info = tinh_trang(bg)
	if tt not in (TT_NHAP, TT_SUA_TAY):
		frappe.throw("Tháng này không có bút toán nháp nào để bỏ.")
	chung_tu.danh_dau_huy(info["doc"], ly_do or "Kế toán bỏ bản nháp để lập lại")
	return {"ok": 1, "da_bo": info["doc"].name}


# Phép đọc lại số hiện tại của từng loại (cty, ky, bản ghi) -> câu phần đã đổi, "" là còn đúng.
KIEM_CU = {
	LOAI_242: "vagabond.chi_phi_242.kiem_cu_thang",
	LOAI_META: "vagabond.chi_phi_meta.kiem_cu_thang",
}


def _ban_ghi_cua_je(ten):
	"""Bản ghi tháng đang nối với bút toán này (khoá dòng), None nếu không có."""
	n = frappe.db.get_value(DT, {"journal_entry": ten}, "name")
	if not n:
		return None
	frappe.db.sql("select name from `tabVagabond But Toan Tu Lap` where name=%s for update", n)
	return frappe.get_doc(DT, n)


def kiem_je_tu_lap(doc, method=None):
	"""Hook Journal Entry before_submit (Codex #590 vòng 2): bút toán nháp máy lập
	chỉ ghi sổ được khi còn khớp số hiện tại, ở MỌI đường ghi (màn tháng, Hạch toán
	tay, Desk). Quyết định, khai báo, sao kê đổi sau khi lập thì nháp đã cũ; ghi sổ
	nó là ghi số sai hoặc ghi trùng. Bút toán không do máy lập thì không đụng."""
	if not doc.get("vgb_tu_lap") or not doc.name:
		return
	bg = _ban_ghi_cua_je(doc.name)
	if not bg or bg.get("loai") not in KIEM_CU:
		return
	import importlib

	mo, ham = KIEM_CU[bg.loai].rsplit(".", 1)
	doi = getattr(importlib.import_module(mo), ham)(bg.company, bg.ky, bg)
	if doi:
		tt, _i = tinh_trang(bg)
		frappe.throw("Bản nháp %s đã cũ so với số hiện tại: %s. %s" % (doc.name, doi,
			"Bản nháp đã được sửa tay nên bấm Bỏ bản nháp rồi Lập lại." if tt == TT_SUA_TAY
			else "Bấm Lập lại (Cập nhật bản nháp) ở màn của tháng rồi ghi sổ."))


def ghi_so(loai, cty, ky):
	"""Kế toán ghi sổ bút toán nháp của tháng. Kiểm nháp cũ nằm ở hook trước ghi
	sổ (kiem_je_tu_lap) để mọi đường ghi đều qua cùng một chỗ."""
	kiem_quyen(QUYEN_GHI, "ghi sổ bút toán")
	bg = khoa_ban_ghi(loai, cty, ky)
	tt, info = tinh_trang(bg)
	if tt not in (TT_NHAP, TT_SUA_TAY):
		frappe.throw("Tháng này không có bút toán nháp nào chờ ghi sổ.")
	je = info["doc"]
	chan_khoa_so(je.posting_date)
	je.flags.ignore_permissions = True
	je.submit()
	bg.ghi_so_boi = frappe.session.user
	bg.ghi_so_luc = now_datetime()
	bg.flags.ignore_permissions = True
	bg.flags.vgb_tu_lap = True
	bg.save(ignore_permissions=True)
	return {"ok": 1, "journal_entry": je.name, "trang_thai": TT_GHI}


def la_thang_tuong_lai(ky):
	return ky > ky_cua(nowdate())


TRUONG_MOI = {
	"Journal Entry": [
		{
			"fieldname": "vgb_tu_lap",
			"label": "Máy lập theo tháng",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "user_remark",
			"description": "Khoá của bút toán nháp do hệ thống lập theo tháng (phân bổ 242, chi phí Meta). "
				"Bút toán kế toán tự lập thì để trống.",
		}
	],
	"Journal Entry Account": [
		{
			"fieldname": "vgb_khoan_242",
			"label": "Khoản chi phí trả trước (242)",
			"fieldtype": "Link",
			"options": "Vagabond Khoan 242",
			"insert_after": "cost_center",
			"allow_on_submit": 1,
			"description": "Dòng Có 242 khi phân bổ: chọn đúng khoản trong Bảng kê 242 để hệ thống tính số đã phân bổ.",
		}
	],
}
