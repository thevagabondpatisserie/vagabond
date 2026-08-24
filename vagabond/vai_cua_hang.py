# -*- coding: utf-8 -*-
"""Vai "Quan ly cua hang": dung tu ma nguon, khong bam tay tren Desk.

Vi sao co tep nay
-----------------
Ngay 24/08/2026 ban Le Hoang De bao khong chinh duoc cau hinh may in. Do
lai thi ho so vai cua ban ay la `VGB - Quan ly cua hang`, gom muoi vai,
nhung khong vai nao nam trong `may_in.QUYEN_SUA`. Ban ay la quan ly cua
hang kiem giam doc van hanh, tuc dung la nguoi phai cam cai man do.

Van de sau hon: he KHONG co mot vai nao mang nghia "quan ly cua hang".
Chi co mot HO SO ten nhu vay. Nen moi lan can mo mot man cho vai tro do,
khong biet phai them vai gi, va nguoi ta lai muon tam mot vai khac cho
xong - vi du lay "Sales Manager" hay "Accounts Manager". Muon nham mot
lan la mo them ca dong cua khong lien quan.

Nen o day dung han mot vai rieng, do MA NGUON khai va MA NGUON dung lai
sau moi lan deploy, giong cach `truong_tu_them.py` lam voi truong tu them.

Ba dieu ham `dung()` phai giu
-----------------------------
1. CHI THEM, khong bao gio bot. Ho so nay co the da duoc ai do them vai
   bang tay tren Desk; xoa di la lay mat quyen cua nguoi dang lam viec.
2. Lam lai duoc nhieu lan. Chay lan hai khong duoc doi gi them.
3. Luu lai cac User bi anh huong. Ham validate cua doctype User dung lai
   bang roles TU HO SO moi lan luu, nen them vai vao ho so xong ma khong
   luu lai User thi phien lam viec cua ho van chua co vai moi. Nguoc lai,
   gan vai THANG len User se bi xoa am tham o lan luu sau - da ghi trong
   claude/erpnext-phan-quyen-role.md.
"""

# ------------------------------------------------------------ phan thuan

# Ten vai. Dat mot cho, moi mo dun khac import tu day, de khong co ban
# sao chuoi nao lech chinh ta ma khong ai thay.
VAI_QLCH = "VGB - Quản lý cửa hàng"

# Ho so duoc nhan vai. Ten ho so trung voi ten vai la co y: nguoi doc
# danh sach vai tren Desk thay ngay ho so nao di voi vai nao.
HO_SO_NHAN = "VGB - Quản lý cửa hàng"

# Vai co san cua ERPNext can them cho ho so quan ly cua hang.
#
# `Stock Manager` mo hai cua dang khoa: ghi so phieu kiem ke
# (kiem_ke.VAI_DUYET) va ghi so phieu xuat huy (xuat_kho.VAI_DUYET). Ca
# hai deu GHI VAO SO CAI, nen day la phan can anh Viet gat dau ro rang.
#
# `Kiem ke vien` de tu chay duoc mot dot kiem ke xoay vong ma khong phai
# nho anh Kien mo phieu ho.
VAI_THEM_SAN = ("Stock Manager", "Kiểm kê viên")


def vai_can_co(dang_co, vai_moi=None, vai_san=None):
	"""Nhung vai con THIEU cua mot ho so. THUAN.

	Tra ve danh sach da sap xep, chi gom vai chua co. Ho so da du thi tra
	ve rong, va do chinh la dieu kien de `dung()` khong dong vao gi ca.
	"""
	dang_co = {str(v or "").strip() for v in (dang_co or []) if str(v or "").strip()}
	can = [vai_moi or VAI_QLCH] + list(vai_san or VAI_THEM_SAN)
	return sorted({v for v in can if v and v not in dang_co})


# ------------------------------------------------------- phan can Frappe

import frappe


def dung():
	"""Dung vai va gan vao ho so. Goi tu after_migrate, lam lai duoc."""
	try:
		_dung_vai()
		them = _gan_vao_ho_so()
		if them:
			_luu_lai_nguoi_dung()
		return them
	except Exception:
		# Khong bao gio duoc lam hong after_migrate: hong o day la ca lan
		# deploy do, ma phan quyen thi sua tay tren Desk van duoc.
		frappe.log_error(frappe.get_traceback(), "vai_cua_hang: dung vai loi")
		return []


def _dung_vai():
	if frappe.db.exists("Role", VAI_QLCH):
		return
	doc = frappe.get_doc({
		"doctype": "Role",
		"role_name": VAI_QLCH,
		"desk_access": 1,
		# Khong phai vai he thong: de nguoi dung gan va go binh thuong.
		"is_custom": 1,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)


def _gan_vao_ho_so():
	"""Them vai con thieu vao ho so. Tra ve danh sach vai vua them."""
	if not frappe.db.exists("Role Profile", HO_SO_NHAN):
		frappe.log_error(
			message="Khong thay ho so vai %s, bo qua." % HO_SO_NHAN,
			title="vai_cua_hang: thieu ho so",
		)
		return []
	ho_so = frappe.get_doc("Role Profile", HO_SO_NHAN)
	dang_co = [r.role for r in (ho_so.get("roles") or [])]
	thieu = vai_can_co(dang_co)
	# Vai chua ton tai trong he thi bo qua, dung de no lam hong ban ghi.
	thieu = [v for v in thieu if frappe.db.exists("Role", v)]
	if not thieu:
		return []
	for v in thieu:
		ho_so.append("roles", {"role": v})
	ho_so.flags.ignore_permissions = True
	ho_so.save(ignore_permissions=True)
	return thieu


def _luu_lai_nguoi_dung():
	"""Luu lai cac User dung ho so nay de vai moi vao phien lam viec.

	Bang roles cua User duoc validate() dung lai TU HO SO, nen chi can
	luu lai la du, khong phai append tay.
	"""
	ds = frappe.get_all(
		"User",
		filters={"role_profile_name": HO_SO_NHAN, "enabled": 1},
		pluck="name",
	)
	for ten in ds:
		try:
			u = frappe.get_doc("User", ten)
			u.flags.ignore_permissions = True
			u.save(ignore_permissions=True)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(), "vai_cua_hang: luu lai %s" % ten
			)
	return ds
