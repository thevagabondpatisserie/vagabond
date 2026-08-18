# -*- coding: utf-8 -*-
"""Mot noi duy nhat khai ai duoc vao phan he nao.

Anh Viet 18/08/2026: "cac nut tinh nang cua luong Mua hang dang de chung
chung khien toan bo nhan vien deu nhin thay".

Doc lai quyen tren he thi thay dung, va thay ro cho ro: vai "Bo phan dat
hang" nam trong MOI bo quyen cua luong mua (QUYEN_MUA, QUYEN_DUYET, bang gia
mua), ma vai do thi gan nhu ai cung co - Hieu baker, Han bep pho, Uyen Duyen
sales, De, Kien thu kho deu co. Vai do sinh ra de LAP YEU CAU MUA, mot viec
ai cung phai lam duoc; no khong nen keo theo quyen xem gia mua va cong no.

Nen tach hai chuyen ra:

  - "Bo phan dat hang" giu nguyen: lap yeu cau mua nguyen vat lieu.
  - Phan he THU MUA (duyet yeu cau, don mua, cong no phai tra, danh muc nha
    cung cap, bang gia mua) khoa lai cho thu mua, ke toan va giam doc.

Vi sao khong dung thang Purchase Manager / Purchase User cua ERPNext: hai
vai do la vai ky thuat, anh Viet goi bo phan la "Thu mua" va "Giam doc". Ten
vai nen trung voi cach nguoi that goi nhau, khong thi den luc phan quyen
khong ai biet minh dang tick cai gi. Hai vai ERPNext van giu trong danh sach
de khong ai dang lam viec bi mat quyen giua chung.

Anh Viet chot 18/08/2026: ke toan VAN thay phan he Thu mua, vi cong no phai
tra va hoa don mua vao la viec hang ngay cua ho.
"""

import frappe

ROLE_THU_MUA = "Thu mua"
ROLE_GIAM_DOC = "Giám đốc"

# Ai duoc vao phan he Thu mua. Ap chung cho: duyet yeu cau mua, don mua
# hang, cong no phai tra, danh muc nha cung cap, khai gia mua.
QUYEN_THU_MUA = {
	"System Manager",
	ROLE_THU_MUA,
	ROLE_GIAM_DOC,
	# Hai vai ERPNext dang dung that, giu de khong ai bi mat quyen giua chung.
	"Purchase Manager",
	"Purchase User",
	# Ke toan: cong no phai tra va hoa don mua vao la viec hang ngay.
	"Accounts Manager",
	"Accounts User",
}


def duoc_thu_mua(nguoi=None):
	"""Nguoi nay co duoc vao phan he Thu mua khong. Dung o ca man lan may chu."""
	return bool(QUYEN_THU_MUA & set(frappe.get_roles(nguoi)))


def chan_neu_khong_thu_mua(viec="vào phân hệ Thu mua"):
	"""Nem loi theo QT-24: noi ro phai lam gi tiep."""
	if not duoc_thu_mua():
		frappe.throw(
			"Tài khoản của bạn không có quyền %s. Phân hệ này chỉ mở cho Thu mua, "
			"Kế toán và Giám đốc. Cần dùng thì báo anh Việt cấp thêm chức vụ "
			"Thu mua trong màn Quản lý người dùng." % viec
		)
