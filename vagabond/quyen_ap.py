# -*- coding: utf-8 -*-
"""Quyen doc chung tu goc cho ba vai duyet chi.

VI SAO CO TEP NAY
-----------------
Ngay 21/08/2026 chi Dung mo phieu APP-26-08-534 de kiem tra, man hinh nem
ra dung cau nay:

    Nguoi dung dung.ngo1587@gmail.com khong co quyen truy cap doctype qua
    quyen vai tro cho tai lieu Don mua hang

Chi ay la ke toan truong, giu vai `AP Kiem soat (FIN)`, ma lai bi chan o
mot don mua hang chi ay chi can NHIN.

Goc re nam trong ERPNext chu khong nam trong ma cua minh. Doc thang ma
nguon `erpnext/accounts/doctype/payment_entry/payment_entry.py` ban
version-16:

    def set_missing_ref_details(self, ...):      # goi tu validate()
        for d in self.get("references"):
            if d.allocated_amount:
                ref_details = get_reference_details(d.reference_doctype, ...)

    @frappe.whitelist()
    def get_reference_details(reference_doctype, reference_name, ...):
        frappe.has_permission(reference_doctype, "read", reference_name, throw=True)

Nghia la: MOI LAN luu mot Payment Entry co dong tham chieu, ERPNext doc lai
chung tu goc va bat buoc nguoi dang luu phai co quyen DOC chung tu goc do.
Khong phai luc mo man hinh, ma luc LUU. Nen loi khong lo ra khi xem, no chi
lo ra dung luc bam nut duyet - cho kho chiu nhat.

Truoc v265 dieu nay khong ai gap, vi phieu chi cua app deu tham chieu
Purchase Invoice, ma ba vai AP deu co `Accounts User`. Tu v265 luong
"Tao phieu thanh toan truoc cho NCC" neo vao PURCHASE ORDER - va khong vai
AP nao co quyen doc Purchase Order. Ca ba buoc duyet deu luu phieu, nen ca
ba vai deu dung tuong.

VI SAO PHAI NAM TRONG GIT CHU KHONG PHAI BAM TAY TREN DESK
----------------------------------------------------------
Ngay 21/08/2026 luc 19:09 da co nguoi mo Quan ly quyen vai tro va cap
`read` Purchase Order cho `AP Kiem soat (FIN)`. Cap dung, nhung no chi
nam trong co so du lieu - giong het Server Script sua thang tren Desk:
git khong quan, khong co lich su, ai lo reset quyen mot cai la mat sach
ma khong ai hay. Va no moi cuu duoc mot vai; hai vai con lai van ho.

Tep nay khai lai dieu do bang ma nguon, chay lai duoc khong gioi han lan.

VI SAO CHI DUNG VAO PURCHASE ORDER
----------------------------------
Them mot dong Custom DocPerm vao doctype nao la DONG BANG quyen cua
doctype do: tu do tro di ERPNext nang cap quyen chuan thi site khong nhan
nua, vi Custom DocPerm de len tren. Purchase Order thi da co Custom DocPerm
tu 19:09 hom nay roi nen khong mat them gi. Purchase Invoice thi CHUA co,
va ba vai AP von da doc duoc qua `Accounts User`, nen dung dung vao.

DUNG DUNG frappe.db.set_value HAY INSERT TAY
--------------------------------------------
`frappe.permissions.add_permission` va `update_permission_property` deu goi
`setup_custom_perms` truoc, va ham do chep TOAN BO cac dong quyen chuan
sang Custom DocPerm. Chen tay mot dong Custom DocPerm vao doctype chua co
dong nao thi ke tu giay do doctype ay CHI con dung mot dong do, moi vai
khac mat sach quyen. Luon di qua hai ham cua Frappe.
"""

import frappe

# Ba vai trong luong duyet phieu chi. Phai trung TUNG KY TU voi bang PAYFLOW
# trong `public/js/bep/04-tao-phieu.js`; co ca kiem doi chieu hai ben.
VAI_DUYET = (
	"AP Officer",
	"AP Kiểm soát (FIN)",
	"AP Giám đốc",
)

# Chung tu goc ma dong `references` cua phieu chi tro toi VA hien chua vai
# AP nao doc duoc. Doc phan "VI SAO CHI DUNG VAO PURCHASE ORDER" o tren
# truoc khi them ten vao day.
CHUNG_TU_GOC = ("Purchase Order",)

# `read`  ERPNext bat buoc co, neu khong thi khong luu duoc phieu.
# `print` de to don mua hang co mat trong bo ho so xuat ra cho giam doc ky;
#         thieu no thi `frappe.get_print` lang le bo to do ra khoi bo.
QUYEN = ("read", "print")


# v526 (anh Việt chọn 24/09/2026): kế toán FIN sửa được tài khoản trên hoá
# đơn mua ĐÃ ghi sổ. Ca thật: chị Dung ghi hoá đơn xăng HDM-26-09-00335 vào
# 632, vào Desk đổi 632 thành 6417 thì bị chặn "Không có quyền cho Repost sổ
# kế toán". ERPNext v16 đổi tài khoản trên tờ đã ghi sổ bằng cách lập một
# phiếu Repost Accounting Ledger, mà bảng quyền chuẩn của phiếu đó chỉ có
# System Manager. Chỉ mở cho đúng một vai AP Kiểm soát (FIN), không mở cho cả
# Accounts User. Đọc đoạn "VI SAO CHI DUNG VAO PURCHASE ORDER" ở đầu tệp: thêm
# dòng quyền là đóng băng bảng quyền chuẩn của doctype đó; Repost Accounting
# Ledger chuẩn chỉ có một dòng System Manager, được chép sang nguyên vẹn.
CAP_THEM = (
	(
		"Repost Accounting Ledger",
		("AP Kiểm soát (FIN)",),
		("read", "write", "create", "submit"),
	),
)


def can_cap():
	"""Danh sach (doctype, vai, quyen) ma he PHAI co. Phep thuan, khong cham Frappe."""
	ra = []
	for dt in CHUNG_TU_GOC:
		for vai in VAI_DUYET:
			for q in QUYEN:
				ra.append((dt, vai, q))
	return ra


def can_cap_them():
	"""Danh sach (doctype, vai, quyen) cua CAP_THEM. Phep thuan."""
	ra = []
	for dt, cac_vai, cac_quyen in CAP_THEM:
		for vai in cac_vai:
			for q in cac_quyen:
				ra.append((dt, vai, q))
	return ra


def cap_repost_v526():
	"""Patch v526: cấp quyền Repost cho kế toán FIN. KHÔNG nuốt lỗi: thiếu
	quyền sau khi cấp là làm hỏng migrate, để deploy không báo xong giả."""
	from frappe.permissions import add_permission, update_permission_property

	them = []
	for dt, cac_vai, cac_quyen in CAP_THEM:
		if not frappe.db.exists("DocType", dt):
			frappe.throw("Không có doctype %s trên site, chưa cấp quyền được." % dt)
		for vai in cac_vai:
			if not frappe.db.exists("Role", vai):
				frappe.throw("Không có vai %s trên site, chưa cấp quyền %s được." % (vai, dt))
			for q in cac_quyen:
				if not _thieu(dt, vai, q):
					continue
				add_permission(dt, vai, 0)
				update_permission_property(dt, vai, 0, q, 1)
				them.append("%s · %s · %s" % (dt, vai, q))
			con = [q for q in cac_quyen if _thieu(dt, vai, q)]
			if con:
				frappe.throw("Cấp quyền %s cho %s chưa đủ: thiếu %s." % (dt, vai, ", ".join(con)))
	frappe.clear_cache()
	return {"them": them}


# ==================================================================
# KHOI PHUC quyen bi bang quyen dong bang lam mat
# ==================================================================
#
# Anh Viet phat hien 23/08/2026: chi Loan Anh khong lap duoc phieu, va khi
# dao ra thi lo mot chuyen lon hon nhieu.
#
# Tren Payment Entry hien co ba dong Custom DocPerm (ba vai AP), tao
# 23/07/2026. Doc thang ma nguon Frappe version-16,
# `frappe/model/meta.py`:
#
#     def set_custom_permissions(self):
#         """Reset `permissions` with Custom DocPerm if exists"""
#         ...
#         if custom_perms:
#             self.permissions = [Document(d) for d in custom_perms]
#
# He co MOT dong Custom DocPerm la Frappe VUT BO toan bo bang quyen chuan
# va chi dung may dong tuy bien. Nghia la tu 23/07 den nay, `Accounts User`
# va `Accounts Manager` TRANG QUYEN tren Phieu thu/chi.
#
# Nguoi chiu tran that: khai.lam193@gmail.com giu ca hai vai ke toan nhung
# khong giu vai AP nao, nen khong mo noi mot phieu thu chi nao. Chi Dung
# thoat vi tinh co co them vai AP Kiem soat (FIN).
#
# Bang duoi day KHONG PHAI la noi quyen. No chep lai DUNG bang quyen chuan
# cua ERPNext cho hai vai do, tuc dat lai nhung gi bang dong bang da lam
# mat. Da doi chieu tung o voi bang DocPerm chuan tren site truoc khi viet.
KHOI_PHUC = (
	(
		"Payment Entry",
		("Accounts Manager", "Accounts User"),
		("read", "write", "create", "delete", "submit", "cancel", "amend",
		 "report", "export", "import", "share", "print", "email"),
	),
)


def can_khoi_phuc():
	"""Danh sach (doctype, vai, quyen) phai dat lai. Phep thuan."""
	ra = []
	for dt, cac_vai, cac_quyen in KHOI_PHUC:
		for vai in cac_vai:
			for q in cac_quyen:
				ra.append((dt, vai, q))
	return ra


def _thieu(dt, vai, q):
	"""Dong Custom DocPerm cua (dt, vai) o muc 0 co bat quyen `q` chua."""
	ten = frappe.db.get_value(
		"Custom DocPerm", {"parent": dt, "role": vai, "permlevel": 0, "if_owner": 0}
	)
	if not ten:
		return True
	return not frappe.db.get_value("Custom DocPerm", ten, q)


def dung():
	"""Cap du quyen cho ba vai AP. Chay lai duoc, lan thu hai khong doi gi."""
	from frappe.permissions import add_permission, update_permission_property

	them = []
	# Cap moi cho ba vai AP, VA dat lai nhung gi bang dong bang da lam mat.
	# Cung mot vong vi cung mot phep: di qua hai ham cua Frappe, bo qua dong
	# da du, chay lai duoc khong gioi han lan.
	for dt, vai, q in list(can_cap()) + list(can_khoi_phuc()) + list(can_cap_them()):
		if not frappe.db.exists("DocType", dt):
			continue
		if not frappe.db.exists("Role", vai):
			continue
		if not _thieu(dt, vai, q):
			continue
		try:
			# `add_permission` tu bo qua neu dong da co, nen goi truoc luon
			# cho chac: no lo phan chep cac dong quyen chuan sang Custom
			# DocPerm neu doctype chua co dong nao.
			add_permission(dt, vai, 0)
			update_permission_property(dt, vai, 0, q, 1)
			them.append("%s · %s · %s" % (dt, vai, q))
		except Exception:
			frappe.log_error(
				frappe.get_traceback(), "quyen_ap: cap %s %s %s" % (dt, vai, q)
			)
	if them:
		frappe.clear_cache()
	return {"them": them}


# ==================================================================
# v537: nut Xuat Excel tren moi man bao cao cho ke toan
# ==================================================================
#
# Anh Viet 29/09/2026: chi Dung mo "Tom tat phai tra" (Accounts Payable
# Summary), menu "..." chi co Sua, In, PDF, khong co Xuat. Doc thang
# frappe/public/js/frappe/views/reports/query_report.js (version-16):
#
#     { label: __("Export"), action: () => this.export_report(),
#       condition: () => frappe.model.can_export(this.report_doc.ref_doctype) }
#
# Nut Xuat chi hien khi vai cua nguoi dung co quyen `export` tren DOCTYPE
# GOC cua bao cao, khong phai tren bao cao. Tren site, bang quyen chuan cua
# Purchase Invoice (ke ca dong DocPerm chuan) de export=0 cho ca Accounts
# User lan Accounts Manager, nen ke toan truong khong xuat noi mot bao cao
# nao ve cong no phai tra.
#
# Cach cap: khong liet ke cung tung doctype (moi ban ERPNext them bao cao la
# lai thieu), ma doc bang Report tren site, gom `ref_doctype` cua MOI bao
# cao con bat, roi cap `export` cho vai ke toan tren nhung doctype ma vai do
# DA doc duoc. Khong cap read moi, khong mo them doctype nao; chi bat mot o
# tren dong quyen von co. Doc lai "VI SAO CHI DUNG VAO PURCHASE ORDER" o dau
# tep: moi doctype duoc cham vao la dong bang bang quyen chuan cua no. Chap
# nhan, vi ke toan phai xuat duoc so ra Excel de doi chieu voi Fast.
VAI_XUAT_EXCEL = ("Accounts User", "Accounts Manager", "AP Kiểm soát (FIN)")


def ke_hoach_xuat_excel(ref_doctypes, doc_duoc, xuat_duoc):
	"""(doctype, vai) can bat export. THUAN.

	ref_doctypes: doctype goc cua cac bao cao (co the trung, co the rong).
	doc_duoc(dt, vai) / xuat_duoc(dt, vai): vai dang doc / dang xuat duoc dt.
	Chi cap khi vai DA doc duoc va CHUA xuat duoc."""
	ra = []
	for dt in sorted({d for d in ref_doctypes or [] if d}):
		for vai in VAI_XUAT_EXCEL:
			if doc_duoc(dt, vai) and not xuat_duoc(dt, vai):
				ra.append((dt, vai))
	return ra


def _doc_duoc(dt, vai):
	"""Vai co dong quyen read o muc 0, o Custom DocPerm hay DocPerm chuan."""
	for bang in ("Custom DocPerm", "DocPerm"):
		if frappe.db.get_value(bang, {"parent": dt, "role": vai, "permlevel": 0, "if_owner": 0, "read": 1}):
			return True
		if bang == "Custom DocPerm" and frappe.db.exists("Custom DocPerm", {"parent": dt}):
			# Da co dong tuy bien thi bang chuan khong con hieu luc.
			return False
	return False


def cap_xuat_excel_v537():
	"""Patch v537. Khong nuot loi o buoc cap: thieu quyen sau khi cap la lam
	hong migrate."""
	from frappe.permissions import add_permission, update_permission_property

	ref = frappe.get_all("Report", filters={"disabled": 0}, pluck="ref_doctype", limit_page_length=0)
	ref = [d for d in ref if d and frappe.db.exists("DocType", d)]
	them = []
	for dt, vai in ke_hoach_xuat_excel(ref, _doc_duoc, lambda dt, vai: not _thieu(dt, vai, "export")):
		if not frappe.db.exists("Role", vai):
			continue
		add_permission(dt, vai, 0)
		update_permission_property(dt, vai, 0, "export", 1)
		if _thieu(dt, vai, "export"):
			frappe.throw("Cấp quyền xuất Excel %s cho %s không ăn." % (dt, vai))
		them.append("%s · %s" % (dt, vai))
	if them:
		frappe.clear_cache()
	return {"them": them}
