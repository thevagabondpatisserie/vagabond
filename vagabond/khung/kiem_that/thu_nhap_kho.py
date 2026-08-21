"""Ca kiểm tích hợp đường nhập kho và tài khoản chờ hoá đơn.

Đây là bộ ca kiểm sinh ra từ sự cố 21/08/2026: Kiên không nhập kho được vì
mình đính đối tác vào dòng sổ cái của tài khoản 3311. Mỗi ca ở đây chốt
một mảnh của sự cố đó, và chốt bằng cách để chính ERPNext trả lời chứ
không phải bằng cách đọc lại code của mình.
"""

import frappe

from vagabond import ke_toan_mua
from vagabond.khung.kiem_that.nen import (
	ca, cong_ty, dung, khong_nem, la, phieu_nhap_ao, so_cai_cua,
)


@ca("nhap kho: ghi so duoc mot phieu nhap that, ERPNext khong duoc nem loi")
def _ghi_so_duoc():
	# Ca kiểm quan trọng nhất của cả tầng này. Ngày 21/08/2026 ca này sẽ
	# ĐỎ với đúng câu "Loại đối tác và Đối tác chỉ có thể được đặt cho tài
	# khoản Phải thu / Phải trả", tức là bắt được đúng cái mà bộ kiểm tầng
	# khung không thấy.
	doc = khong_nem("ghi sổ phiếu nhập kho", phieu_nhap_ao)
	if not doc:
		return
	la("trạng thái phiếu", int(doc.docstatus), 1)
	gl = so_cai_cua(doc)
	dung("có sinh bút toán", len(gl) >= 2)
	tong_no = sum(float(d.debit or 0) for d in gl)
	tong_co = sum(float(d.credit or 0) for d in gl)
	la("nợ bằng có", round(tong_no, 2), round(tong_co, 2))


@ca("nhap kho: dong so cai cua tai khoan cho hoa don KHONG duoc co doi tac")
def _tai_khoan_cho_khong_doi_tac():
	doc = khong_nem("ghi sổ phiếu nhập kho", phieu_nhap_ao)
	if not doc:
		return
	tk_cho = ke_toan_mua.tk_cho_hien_tai(doc.company)
	dung("công ty có khai tài khoản chờ hoá đơn", bool(tk_cho))
	dong_cho = [d for d in so_cai_cua(doc) if d.account == tk_cho]
	dung("phiếu nhập có ghi vào tài khoản chờ hoá đơn", len(dong_cho) >= 1)
	for d in dong_cho:
		dung("dòng %s không được có đối tác" % d.account, not d.party)
		dung("dòng %s không được có loại đối tác" % d.account, not d.party_type)


@ca("ke toan mua: loai tai khoan cho tren SITE THAT phai la loai KHONG dinh doi tac")
def _loai_tai_khoan_cho():
	# Chốt luôn ở tầng này chứ không chỉ ở tầng khung: tầng khung đọc hằng
	# trong code, tầng này đọc cấu hình THẬT của site. Ai đó vào Desk đổi
	# loại tài khoản 3311 thành Payable là ca này đỏ ngay, trước khi Payment
	# Ledger Entry kịp làm sai số dư hoá đơn.
	tk = ke_toan_mua.tk_cho_hien_tai(cong_ty())
	dung("có khai tài khoản chờ hoá đơn", bool(tk))
	if not tk:
		return
	loai = frappe.get_cached_value("Account", tk, "account_type")
	la("loại tài khoản chờ", loai, ke_toan_mua.LOAI_TK)
	dung("loại này KHÔNG cho đính đối tác",
		not ke_toan_mua.duoc_gan_doi_tac(loai))


@ca("ke toan mua: khong con lop thay the nao tren Phieu nhap va Hoa don mua")
def _khong_ghi_de_lop():
	# Đọc hooks ĐÃ NẠP trên site chứ không đọc tệp: tệp có thể đúng mà bản
	# đang chạy là bản cũ.
	ghi_de = frappe.get_hooks("override_doctype_class") or {}
	for dt in ("Purchase Receipt", "Purchase Invoice"):
		dung("không ghi đè lớp %s" % dt, dt not in ghi_de)
