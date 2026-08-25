"""Ca kiểm TÍCH HỢP cho luồng hoàn tiền đơn Pancake đã huỷ.

Ca kiểm phép thuần đã chốt phần tính toán. Còn một câu mà chỉ tầng này trả
lời được: **ERPNext có chấp thuận cặp phiếu thu và phiếu chi không gán hoá
đơn nào không.** Đúng loại câu hỏi mà vụ 3311 ngày 21/08/2026 đã bỏ sót.

Mọi ca ở đây dựng chứng từ thật rồi lùi về điểm lưu, xem nen.py.
"""

import frappe

from vagabond import don_huy, hoan_tien
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


@ca("don huy: ERPNext nhan cap phieu khong gan hoa don, va hang rao UNC con song")
def _cap_phieu_ghi_so_duoc():
	# Day la ca quan trong nhat cua tep nay. Khoan tien cua don da huy khong
	# gan voi hoa don nao, nen hai phieu nay khong co dong tham chieu. Neu
	# ERPNext tu choi thi ca luong hoan tien vo nghia, va phai biet dieu do
	# o day chu khong phai luc Sales bam nut.
	#
	# SUA 25/08/2026: ca nay HONG suot tu 23/08 voi loi "module
	# 'vagabond.don_huy' has no attribute '_phieu'". Ngay 23/08 hai phieu
	# duoc doi cho sinh: tu `don_huy._phieu` sang
	# `hoan_tien._lap_cap_phieu_huy_don`, vi Sales khong co quyen tren
	# Payment Entry. Ca kiem thi khong ai doi theo.
	#
	# Mot ca kiem tich hop do lien tuc con nguy hon khong co ca kiem nao:
	# nguoi chay quen dan mau do do va thoi doc ket qua.
	cty = cong_ty()
	khach = don_huy._khach_le_online()
	if not khach:
		dung("có mã Khách lẻ Online để chạy ca này", False)
		return

	# Ham that doi mot HO SO co that, vi no dat `pe.vgb_hoan_tien = ho_so.name`
	# va Frappe kiem lien ket do. Dung ho so nhap ngay tai day; diem luu cua
	# `nen.py` se lui het lai khi ca kiem xong.
	ho_so = khong_nem("lập hồ sơ hoàn tiền thử", lambda: _ho_so_thu(khach))
	if not ho_so:
		return

	cap = khong_nem("lập cặp phiếu thu và phiếu chi",
		lambda: hoan_tien._lap_cap_phieu_huy_don(ho_so))
	if not cap:
		return
	thu, chi = cap
	dung("lập được phiếu thu", bool(thu))
	dung("lập được phiếu chi", bool(chi))
	if not (thu and chi):
		return

	la("phiếu thu để NHÁP", int(thu.docstatus), 0)
	la("phiếu chi để NHÁP", int(chi.docstatus), 0)
	la("phiếu thu đúng khách", thu.party, khach)
	# Khong gan vao hoa don nao: khoan nay chua tung la doanh thu.
	la("phiếu thu không có dòng tham chiếu", len(thu.get("references") or []), 0)
	la("phiếu chi không có dòng tham chiếu", len(chi.get("references") or []), 0)
	la("hai phiếu cùng số tiền", float(chi.paid_amount), float(thu.paid_amount))
	la("cả hai trỏ về đúng hồ sơ",
		[thu.get("vgb_hoan_tien"), chi.get("vgb_hoan_tien")],
		[ho_so.name, ho_so.name])

	# ĐẾN ĐÂY LÀ HẾT PHẦN KIỂM ĐƯỢC, VÀ ĐÓ LÀ MỘT TIN TỐT
	# --------------------------------------------------
	# Ban dau ca nay ghi so THAT ca hai phieu, de xem ERPNext co nhan mot
	# cap phieu KHONG co dong tham chieu khong. Cau hoi do da duoc tra loi
	# ngay o tren: ca hai phieu DUNG DUOC va o trang thai nhap, tuc ERPNext
	# chap thuan.
	#
	# Con buoc ghi so thi nay KHONG chay duoc nua, va dung ra la vay: tiem
	# da dung mot luat rieng, phieu di qua tai khoan ngan hang thi bat buoc
	# phai co Uy nhiem chi dinh kem moi ghi so duoc. Luat do dung cho co
	# quan thue, va mot ca kiem KHONG duoc quyen di duong vong qua no.
	#
	# Nen tu 25/08/2026 ca nay chot hai dieu, ca hai deu that:
	#   1. ERPNext nhan cap phieu khong co dong tham chieu  (o tren)
	#   2. Hang rao Uy nhiem chi CON SONG                    (o duoi)
	chan_thu = _nem_gi("ghi sổ phiếu thu khi chưa có UNC", thu.submit)
	chan_chi = _nem_gi("ghi sổ phiếu chi khi chưa có UNC", chi.submit)
	dung("hàng rào UNC chặn phiếu thu", "Uỷ nhiệm chi" in chan_thu)
	dung("hàng rào UNC chặn phiếu chi", "Uỷ nhiệm chi" in chan_chi)
	# Bi chan thi phai con o trang thai nhap, khong duoc nam lung chung.
	la("phiếu thu vẫn ở nháp", int(frappe.db.get_value(
		"Payment Entry", thu.name, "docstatus") or 0), 0)
	la("phiếu chi vẫn ở nháp", int(frappe.db.get_value(
		"Payment Entry", chi.name, "docstatus") or 0), 0)


def _nem_gi(nhan, ham):
	"""Chay mot ham va tra ve CAU LOI no nem. Rong neu no khong nem gi.

	Nguoc voi `khong_nem`: o day loi la ket qua MONG DOI, khong phai su co.
	"""
	try:
		ham()
	except Exception as e:
		return str(e)
	dung(nhan + ": đáng lẽ phải bị chặn mà lại lọt", False)
	return ""


def _ho_so_thu(khach):
	"""Mot ho so hoan tien de NHAP, chi dung trong ca kiem nay."""
	hs = frappe.new_doc("Vagabond Hoan Tien")
	hs.khach = khach
	hs.so_tien = 705000.0
	hs.ly_do = "Khac"
	# Ly do "Khac" thi doctype BAT phai ghi ro vi sao, chinh no chan o
	# validate(). Dien vao day chu khong doi luat: luat do dung, va ca kiem
	# phai chay qua dung con duong ma nguoi that di.
	hs.dien_giai = "Ca kiem tich hop, khong phai ho so that."
	hs.trang_thai = "Cho chi"
	hs.ma_don_pancake = "92252"
	hs.noi_dung_ck = don_huy.noi_dung_chuyen_khoan("92252", "MD92252")
	hs.flags.ignore_permissions = True
	hs.insert(ignore_permissions=True)
	return hs
