# -*- coding: utf-8 -*-
"""#351: Giao việc từ màn Việc hôm nay chạy THẬT trên Task, ToDo, DocShare.

Tầng khung thay Frappe bằng đồ giả nên không bao giờ biết ERPNext có nhận
Task mang các trường vgb_goi_y_* không, ToDo có tự chép người nhận vào ô
Assigned To không, và Task chuyển Completed có tự đóng ToDo không (hàm
`unassign_todo` trong erpnext/projects/doctype/task/task.py). Ba điều đó là
lý do chọn Task lõi thay vì doctype riêng, nên phải kiểm trên site thật.

Mọi thứ nằm trong điểm lưu của khung, chạy xong biến mất.
"""

import frappe
from frappe.utils import add_days, nowdate

from vagabond import phan_tich as pt
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la

NGUOI = "kt351@vagabond.test"


def _nguoi():
	"""Tài khoản nhận việc kiểm thử. Phải là System User THẬT: Frappe tự hạ
	User không có vai vào bàn làm việc xuống Website User khi lưu, dù gửi
	user_type System User (bench CI 0a8754e: giao bị loi_nguoi_nhan chặn đúng
	luật). Nên gắn vai Projects User, như nhân viên thật được giao việc."""
	if not frappe.db.exists("User", NGUOI):
		u = frappe.get_doc({
			"doctype": "User", "email": NGUOI, "first_name": "Kiểm thử 351",
			"send_welcome_email": 0, "user_type": "System User",
			"roles": [{"role": "Projects User"}],
		})
		u.flags.ignore_permissions = True
		u.insert(ignore_permissions=True)
		nen._DA_TAO.append(("User", u.name))
	la("tài khoản kiểm thử là nội bộ", frappe.db.get_value("User", NGUOI, "user_type"), "System User")
	return NGUOI


def _dat_bang():
	"""Một bảng sáng giả của hôm nay trong bộ nhớ đệm, trả về hàm dọn."""
	cu = frappe.cache().get_value(pt.KHOA_DEM)
	nd = pt.nhan_dinh_lo([
		{"lo": "LO-KT351", "ma": "NVLT-KT351", "ten": "Bơ thử", "kho": "Kho KT351 - VK", "han": add_days(nowdate(), -3), "sl": 5},
	], nowdate())
	frappe.cache().set_value(pt.KHOA_DEM, {
		"den_ngay": str(add_days(nowdate(), -1)), "chot_luc": "2026-09-21 07:00:00",
		"nhan_dinh": nd, "chat_luong": [], "nhan_tuan": [],
	})

	def don():
		if cu is None:
			frappe.cache().delete_value(pt.KHOA_DEM)
		else:
			frappe.cache().set_value(pt.KHOA_DEM, cu)
	return nd[0]["khoa"], don


@ca("#351: Giao tạo Task thật có trường căn cứ, ToDo mở, chia sẻ, ô Assigned To; bấm lại không sinh việc thứ hai")
def _giao_that():
	dung("Task có trường khoá nhận định (đã dựng lúc migrate)", frappe.get_meta("Task").has_field("vgb_goi_y_khoa"))
	ai = _nguoi()
	khoa, don = _dat_bang()
	try:
		r = khong_nem("giao", lambda: pt.giao(khoa, [ai], str(nowdate()), "kiểm thử"))
		if not r:
			return
		t = frappe.get_doc("Task", r["name"])
		la("khoá và luật", (t.vgb_goi_y_khoa, t.vgb_goi_y_luat, t.status), (khoa, "lo_qua_han", "Open"))
		la("ưu tiên cao", t.priority, "High")
		todo = frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": t.name, "status": "Open"}, pluck="allocated_to")
		la("một ToDo mở cho người nhận", todo, [ai])
		dung("ô Assigned To có người nhận", ai in (frappe.db.get_value("Task", t.name, "_assign") or ""))
		dung("người nhận được chia sẻ Task", frappe.db.exists("DocShare", {"share_doctype": "Task", "share_name": t.name, "user": ai}))
		r2 = khong_nem("giao lần hai", lambda: pt.giao(khoa, [ai], str(nowdate())))
		la("bấm lại ra đúng việc cũ", (r2 or {}).get("name"), t.name)
		la("vẫn một Task cho khoá này", frappe.db.count("Task", {"vgb_goi_y_khoa": khoa}), 1)

		frappe.set_user(ai)
		try:
			khong_nem("người nhận báo xong", lambda: pt.cap_nhat_viec(t.name, "xong", "Đã cách ly lô và báo quản lý kho"))
		finally:
			frappe.set_user("Administrator")
		t.reload()
		la("Task xong có người và kết quả", (t.status, t.completed_by, t.vgb_goi_y_ket_qua), ("Completed", ai, "Đã cách ly lô và báo quản lý kho"))
		la("ERPNext tự đóng ToDo khi Task xong", frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": t.name, "status": "Open"}), [])
	finally:
		don()


@ca("#351: Bỏ qua lưu Task đã huỷ kèm lý do và ngày nhắc lại; nhận định ẩn tới ngày đó")
def _bo_qua_that():
	khoa, don = _dat_bang()
	try:
		r = khong_nem("bỏ qua", lambda: pt.bo_qua(khoa, "so_sai", 14))
		if not r:
			return
		la("lô quá hạn kẹp 3 ngày", r["so_ngay"], 3)
		t = frappe.get_doc("Task", r["name"])
		la("Task huỷ kèm lý do", (t.status, t.vgb_goi_y_bo_qua_ly_do), ("Cancelled", "so_sai"))
		kq = khong_nem("đọc bảng", lambda: pt.bang_sang("can_giao"))
		dung("nhận định không còn trong Cần giao", kq and all(x["khoa"] != khoa for x in kq["ds"]))
		kq2 = khong_nem("đọc tab Bỏ qua", lambda: pt.bang_sang("bo_qua"))
		dung("nằm ở tab Bỏ qua", kq2 and any(x["name"] == t.name for x in kq2["ds"]))
	finally:
		don()


@ca("#353 F1: trên Desk, Task bảng sáng chuyển Completed mà thiếu kết quả bị chặn; có kết quả thì qua")
def _desk_thieu_ket_qua():
	khoa, don = _dat_bang()
	try:
		r = khong_nem("giao", lambda: pt.giao(khoa, [_nguoi()], str(nowdate())))
		if not r:
			return
		t = frappe.get_doc("Task", r["name"])
		t.status = "Completed"
		bi_chan = False
		try:
			t.save(ignore_permissions=True)
		except frappe.ValidationError:
			bi_chan = True
		dung("lưu Completed không kết quả bị chặn", bi_chan)
		la("Task vẫn mở", frappe.db.get_value("Task", t.name, "status"), "Open")
		t = frappe.get_doc("Task", r["name"])
		t.status = "Completed"
		t.vgb_goi_y_ket_qua = "Đã kiểm lô trên Desk"
		khong_nem("lưu có kết quả", lambda: t.save(ignore_permissions=True))
		la("Task xong kèm người đánh dấu", (frappe.db.get_value("Task", t.name, "status"), bool(t.completed_by)), ("Completed", True))
	finally:
		don()


@ca("#356 T1: huỷ Task bảng sáng qua API tài liệu không vượt trần bỏ qua; đã huỷ thì không đẩy ngày nhắc ra xa")
def _tran_bo_qua_that():
	khoa, don = _dat_bang()
	try:
		r = khong_nem("giao", lambda: pt.giao(khoa, [_nguoi()], str(nowdate())))
		if not r:
			return
		t = frappe.get_doc("Task", r["name"])
		t.status = "Cancelled"
		t.vgb_goi_y_bo_qua_ly_do = "so_sai"
		t.vgb_goi_y_nhac_lai = str(add_days(nowdate(), 365))
		bi_chan = False
		try:
			t.save(ignore_permissions=True)
		except frappe.ValidationError:
			bi_chan = True
		dung("lô quá hạn bỏ qua một năm bị chặn", bi_chan)
		la("Task vẫn mở", frappe.db.get_value("Task", t.name, "status"), "Open")
		t = frappe.get_doc("Task", r["name"])
		t.status = "Cancelled"
		t.vgb_goi_y_bo_qua_ly_do = "so_sai"
		t.vgb_goi_y_nhac_lai = str(add_days(nowdate(), 3))
		khong_nem("bỏ qua đúng 3 ngày", lambda: t.save(ignore_permissions=True))
		la("đã huỷ", frappe.db.get_value("Task", t.name, "status"), "Cancelled")
		# Codex #356 (196f394): huỷ qua tài liệu cũng phải đóng ToDo của người nhận.
		la("huỷ qua tài liệu đóng ToDo", frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": t.name, "status": "Open"}), [])
		# Đường của Codex: sửa tiếp Task đã huỷ bằng tài khoản thường.
		frappe.set_user(_nguoi())
		try:
			t = frappe.get_doc("Task", r["name"])
			t.vgb_goi_y_nhac_lai = str(add_days(nowdate(), 365))
			bi_chan = False
			try:
				t.save(ignore_permissions=True)
			except frappe.ValidationError:
				bi_chan = True
			dung("đẩy ngày nhắc của việc đã huỷ bị chặn", bi_chan)
		finally:
			frappe.set_user("Administrator")
		la("ngày nhắc giữ nguyên", str(frappe.db.get_value("Task", r["name"], "vgb_goi_y_nhac_lai")), str(add_days(nowdate(), 3)))
	finally:
		don()


@ca("#356 T2: người có quyền tạo Task không tạo được Task mang khoá bảng sáng")
def _task_gia_that():
	khoa, don = _dat_bang()
	frappe.set_user(_nguoi())
	try:
		bi_chan = False
		try:
			# ignore_permissions: chỉ để hook chặn, không nhờ quyền doctype chặn hộ.
			frappe.get_doc({"doctype": "Task", "subject": "Giả", "status": "Open", "vgb_goi_y_khoa": khoa}).insert(ignore_permissions=True)
		except frappe.ValidationError:
			bi_chan = True
		dung("tạo Task giả bị chặn", bi_chan)
	finally:
		frappe.set_user("Administrator")
		don()
	la("không có Task nào cho khoá", frappe.db.count("Task", {"vgb_goi_y_khoa": khoa}), 0)
