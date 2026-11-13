"""v654 Codex #561 vòng 3: Tiền khả dụng của Lịch dự chi đọc SỔ CÁI THẬT.

Tầng khung thay GL Entry và Bank Account bằng đồ giả. Tầng này hỏi điều đồ
giả không trả lời được: chứng từ THẬT do ERPNext ghi sổ (Payment Entry trả
nhà cung cấp, Journal Entry chi thẳng từ tài khoản công ty) có làm
`lich_du_chi.so_du_kha_dung` trừ đúng số, đúng tài khoản, đúng mốc giờ đọc
số dư, và bỏ đúng bút toán đã huỷ không.

Số dư SePay và giờ đọc là đồ giả có chủ đích (không gọi mạng); mọi thứ còn
lại là chứng từ thật, insert rồi submit, nằm trong điểm lưu của nen.py.
"""

import unittest.mock as um

import frappe
from frappe.utils import now_datetime, today

from vagabond import lich_du_chi, tai_chinh
from vagabond.khung.kiem_that.nen import _DA_TAO, _mot, ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua, _tk_ngan_hang

SO_DU = 100000000


def _so_du(ba, luc):
	# Dòng tài khoản ngân hàng đúng như mục Tài chính trả về khi lấy thẳng số SePay báo.
	dong = [{"nguon": "nh:kiem", "loai": tai_chinh.LOAI_NH, "ten": "Kiểm 654", "tam_ung": 0, "bank_account": ba,
		"dong_bo": 0, "so_bao": float(SO_DU), "so_du": float(SO_DU)}]
	with um.patch.object(tai_chinh, "_tinh_tien", lambda: {"dong": dong}), \
			um.patch.object(tai_chinh, "_sepay_luc_bao", lambda: luc):
		return lich_du_chi.so_du_kha_dung()


def _phieu_chi_ncc(hd, ba, tk_gl, tien):
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type, pe.company = "Pay", hd.company
	pe.posting_date = today()
	pe.party_type, pe.party = "Supplier", hd.supplier
	pe.paid_amount = pe.received_amount = tien
	pe.reference_no, pe.reference_date = "KIEMTHAT-654-" + frappe.generate_hash(length=6), today()
	pe.paid_from = tk_gl
	pe.bank_account = ba
	pe.append("references", {"reference_doctype": "Purchase Invoice", "reference_name": hd.name,
		"total_amount": tien, "outstanding_amount": tien, "allocated_amount": tien})
	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.insert(ignore_permissions=True)
	_DA_TAO.append(("Payment Entry", pe.name))
	# Phiếu chi qua ngân hàng bắt buộc có Uỷ nhiệm chi đính kèm (chung_tu_tien): kèm một
	# UNC thử, nội dung riêng để không trùng tệp của ca khác.
	tep = frappe.get_doc({"doctype": "File", "file_name": "kt654-unc-%s.txt" % pe.name, "is_private": 1,
		"content": "UNC thu bench 654 " + frappe.generate_hash(length=16),
		"attached_to_doctype": "Payment Entry", "attached_to_name": pe.name})
	tep.insert(ignore_permissions=True)
	_DA_TAO.append((tep.doctype, tep.name))
	pe.submit()
	return pe


def _chi_tk_cong_ty(cty, tk_gl, tien):
	tk_cp = _mot("Account", {"company": cty, "root_type": "Expense", "is_group": 0, "disabled": 0})
	cc = frappe.db.get_value("Company", cty, "cost_center")
	je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Bank Entry", "company": cty, "posting_date": today(),
		"cheque_no": "KIEMTHAT-654", "cheque_date": today(), "user_remark": "Kiểm Lịch dự chi v654",
		"accounts": [{"account": tk_cp, "debit_in_account_currency": tien, "cost_center": cc},
			{"account": tk_gl, "credit_in_account_currency": tien, "cost_center": cc}]})
	je.insert(ignore_permissions=True)
	_DA_TAO.append(("Journal Entry", je.name))
	je.submit()
	return je


@ca("v654 Codex #561: Tiền khả dụng trừ đúng Payment Entry nhà cung cấp và Journal Entry ghi sổ THẬT sau giờ đọc số dư, bỏ bút toán đã huỷ")
def _so_cai_that():
	cty = cong_ty()
	ba = khong_nem("có tài khoản ngân hàng của công ty", lambda: _tk_ngan_hang(cty))
	if not ba:
		return
	tk_gl = frappe.db.get_value("Bank Account", ba, "account")
	dung("tài khoản ngân hàng có tài khoản sổ cái", bool(tk_gl))
	# Giờ đọc số dư: TRƯỚC mọi chứng từ dưới, đủ phần lẻ giây như tai_chinh lưu.
	luc_doc = str(now_datetime())
	hd = khong_nem("hoá đơn mua thật còn nợ 60.000", lambda: _hoa_don_mua(60000))
	if not hd:
		return
	# Hồ sơ APP nhà cung cấp thường để trống tk_chi: tiền đi ra chỉ thấy ở Payment Entry.
	pe = khong_nem("ERPNext ghi sổ phiếu chi nhà cung cấp 60.000 từ tài khoản ngân hàng", lambda: _phieu_chi_ncc(hd, ba, tk_gl, 60000))
	je = khong_nem("ERPNext ghi sổ bút toán chi thẳng 25.000 từ tài khoản ngân hàng", lambda: _chi_tk_cong_ty(cty, tk_gl, 25000))
	if not (pe and je):
		return
	gl = frappe.get_all("GL Entry", filters={"voucher_no": ["in", [pe.name, je.name]], "account": tk_gl, "is_cancelled": 0},
		fields=["voucher_type", "credit"])
	la("sổ cái ghi có đúng tài khoản ngân hàng", sorted((g.voucher_type, float(g.credit)) for g in gl),
		[("Journal Entry", 25000.0), ("Payment Entry", 60000.0)])
	r = _so_du(ba, luc_doc)
	la("bản số dư đọc trước hai chứng từ: trừ đủ 85.000", (r["chi_sau"], float(r["so_tien"])), (85000.0, float(SO_DU - 85000)))
	sau = str(now_datetime())
	r = _so_du(ba, sau)
	la("bản số dư đọc sau hai chứng từ: đã gồm, không trừ lại", r["chi_sau"], 0.0)
	khong_nem("ERPNext huỷ bút toán chi thẳng", je.cancel)
	r = _so_du(ba, luc_doc)
	la("bút toán đã huỷ không còn bị trừ: chỉ còn 60.000", r["chi_sau"], 60000.0)


@ca("v654 anh Việt 13/11: Lịch dự chi chạy trên ERPNext thật (công nợ cần thu, thói quen trả của khách); Xoá dự chi nháp xoá hẳn, Desk không xoá được")
def _lich_va_xoa():
	from frappe.utils import add_days

	tre = khong_nem("đọc thói quen trả của khách qua Payment Ledger", lich_du_chi._tre_thanh_toan)
	dung("thói quen trả là {khách: [số ngày]}", isinstance(tre, dict))
	hd = khong_nem("đọc công nợ cần thu đúng phép tính màn Công nợ", lich_du_chi._phai_thu_hd)
	dung("công nợ cần thu là danh sách", isinstance(hd, list))
	kq = khong_nem("mở Lịch dự chi", lich_du_chi.lich)
	if kq:
		dung("có ô tiền dự kiến về", "du_kien_ve" in kq)
	ten = khong_nem("lưu một dự chi nháp", lambda: lich_du_chi.luu_muc(ngay=add_days(today(), 2), noi_dung="Kiểm 654 xoá nháp",
		so_tien="1000000", nguoi_nhan="Người nhận kiểm"))
	if not ten:
		return
	ten = ten["name"]
	_DA_TAO.append(("Vagabond Du Chi Muc", ten))
	try:
		frappe.delete_doc("Vagabond Du Chi Muc", ten, ignore_permissions=True)
		dung("xoá thẳng (như trên Desk) phải bị chặn", False)
	except frappe.PermissionError:
		pass
	dung("còn bản ghi sau lần xoá bị chặn", frappe.db.exists("Vagabond Du Chi Muc", ten))
	khong_nem("nút Xoá dự chi nháp", lambda: lich_du_chi.xoa_muc(ten))
	dung("đã xoá hẳn", not frappe.db.exists("Vagabond Du Chi Muc", ten))
