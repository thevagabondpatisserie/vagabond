"""Ca kiểm TÍCH HỢP cho luồng hoàn tiền đơn Pancake đã huỷ.

Ca kiểm phép thuần đã chốt phần tính toán. Còn một câu mà chỉ tầng này trả
lời được: **ERPNext có chấp thuận cặp phiếu thu và phiếu chi không gán hoá
đơn nào không.** Đúng loại câu hỏi mà vụ 3311 ngày 21/08/2026 đã bỏ sót.

Mọi ca ở đây dựng chứng từ thật rồi lùi về điểm lưu, xem nen.py.
"""

import frappe

from vagabond import don_huy
from vagabond.khung.kiem_that.nen import (
	ca, cong_ty, dung, khong_nem, la,
)


@ca("don huy: site phai co ma khach dung chung va tai khoan ngan hang")
def _du_du_lieu_nen():
	# Thiếu một trong hai là cả luồng chết ngay ở câu lệnh đầu, và người
	# dùng chỉ thấy một câu lỗi khó hiểu giữa chừng.
	khach = khong_nem("tìm mã Khách lẻ Online", don_huy._khach_le_online)
	dung("có mã khách dùng chung", bool(khach))
	tk = khong_nem("đọc tài khoản ngân hàng công ty",
		lambda: don_huy._tk_ngan_hang(cong_ty()))
	dung("có tài khoản kế toán của ngân hàng", bool(tk))
	if tk:
		loai = frappe.get_cached_value("Account", tk, "account_type")
		la("tài khoản ngân hàng đúng loại", loai, "Bank")


@ca("don huy: ERPNext CHAP THUAN cap phieu thu va phieu chi khong gan hoa don")
def _cap_phieu_ghi_so_duoc():
	# Đây là ca quan trọng nhất của tệp này. Khoản tiền của đơn đã huỷ không
	# gắn với hoá đơn nào, nên hai phiếu này không có dòng tham chiếu. Nếu
	# ERPNext từ chối thì cả luồng hoàn tiền vô nghĩa, và phải biết điều đó
	# ở đây chứ không phải lúc Sales bấm nút.
	cty = cong_ty()
	khach = don_huy._khach_le_online()
	tk = don_huy._tk_ngan_hang(cty)
	tien = 705000.0
	mo_ta = don_huy.dien_giai_don("92252", "MD92252", "Ms.Nhu Duyen")

	thu = khong_nem("lập phiếu thu", lambda: don_huy._phieu(
		"Receive", khach, cty, tk, tien, "Ca kiem tich hop: " + mo_ta,
		don_huy.noi_dung_chuyen_khoan("92252", "MD92252"), None))
	if not thu:
		return
	la("phiếu thu để NHÁP", int(thu.docstatus), 0)
	la("phiếu thu đúng khách", thu.party, khach)
	# Không gán vào hoá đơn nào: khoản này chưa từng là doanh thu.
	la("phiếu thu không có dòng tham chiếu", len(thu.get("references") or []), 0)

	chi = khong_nem("lập phiếu chi", lambda: don_huy._phieu(
		"Pay", khach, cty, tk, tien, "Ca kiem tich hop tra lai: " + mo_ta,
		don_huy.noi_dung_chuyen_khoan("92252", "MD92252"), None))
	if not chi:
		return
	la("phiếu chi để NHÁP", int(chi.docstatus), 0)
	la("hai phiếu cùng số tiền", float(chi.paid_amount), float(thu.paid_amount))

	# Ghi sổ THẬT cả hai để ERPNext chạy trọn chuỗi validation. Đây là chỗ
	# vụ 3311 đáng lẽ phải bị bắt: chỉ dựng doc trong bộ nhớ thì không bao
	# giờ biết hệ lõi có nhận hay không.
	khong_nem("ghi sổ phiếu thu", thu.submit)
	khong_nem("ghi sổ phiếu chi", chi.submit)
	la("phiếu thu đã ghi sổ", int(thu.docstatus), 1)
	la("phiếu chi đã ghi sổ", int(chi.docstatus), 1)

	# Hai chân cân nhau thì số dư của khách không đổi. Đó là điều chị Dung
	# cần: trả lại một khoản giữ hộ, không đẻ ra công nợ.
	gl = frappe.get_all("GL Entry", filters={
		"voucher_no": ["in", [thu.name, chi.name]], "is_cancelled": 0,
	}, fields=["account", "party", "debit", "credit"])
	dung("có sinh bút toán", len(gl) >= 4)
	tk_131 = [g for g in gl if g.party == khach]
	dung("dòng công nợ có đối tác", len(tk_131) >= 2)
	lech = sum(float(g.credit or 0) - float(g.debit or 0) for g in tk_131)
	la("hai chân cân nhau, số dư khách không đổi", round(lech, 2), 0.0)
