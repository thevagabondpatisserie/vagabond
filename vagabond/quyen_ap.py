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


def can_cap():
	"""Danh sach (doctype, vai, quyen) ma he PHAI co. Phep thuan, khong cham Frappe."""
	ra = []
	for dt in CHUNG_TU_GOC:
		for vai in VAI_DUYET:
			for q in QUYEN:
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
	for dt, vai, q in can_cap():
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
