"""v630: bánh thiết kế riêng, trọn vòng đời trên sổ cái thật (Codex finding 3).

Đi ĐÚNG các cửa của app, không dựng chứng từ bằng tay:
  1. `thiet_ke_rieng._lap_phieu_dat`: Sales Order đã ghi sổ, một dòng BAEV00001,
     giá đã gồm VAT do máy chủ tính, mẫu thuế "đã gồm trong giá".
  2. Một dòng sao kê THẬT mang mã đơn, rồi `khop_mot`: phiếu thu cọc nháp trỏ
     phiếu đặt, chiếm dòng sao kê; chạy lại không lập đôi.
  3. `ghi_so_phieu` (kế toán đính giấy báo Có): ERPNext chạy đủ hook ghi sổ,
     kể cả bốn hàng rào dat_banh và chặn thiếu đính kèm.
  4. `thu_tien_mat` ở quầy TCV, `giao_banh`: hoá đơn từ phiếu đặt, cấn ĐÚNG
     hai phiếu thu, không vơ khoản ứng trước khác của khách.
Đọc lại sổ cái, Payment Ledger, Chốt ca. Chạy trong điểm lưu của nen.py,
commit bị khoá, không gửi gì ra ngoài.
"""

import hashlib
from unittest.mock import patch

import frappe
from frappe.utils import add_days, flt, now_datetime, today

from vagabond import thiet_ke_rieng as tkr
from vagabond.khung.kiem_that.nen import _DA_TAO, _mot, ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen as _nen_thue
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi

PNG = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
	"+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
ANH = '[{"ten": "giay-bao-co-630.png", "noi_dung": "%s"}]' % PNG


def _mon():
	if frappe.db.exists("Item", tkr.MA_MON):
		return tkr.MA_MON
	d = frappe.get_doc(dict(doctype="Item", item_code=tkr.MA_MON, item_name="Bánh thiết kế riêng",
		item_group=frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
		stock_uom=frappe.db.get_value("UOM", {}, "name"), is_stock_item=0, is_sales_item=1))
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


def _tien_mat(cty):
	tien = _mot("Account", {"company": cty, "account_type": "Cash", "is_group": 0, "disabled": 0})
	if not frappe.db.get_value("Mode of Payment Account", {"parent": "Tiền mặt", "company": cty}, "default_account"):
		if not frappe.db.exists("Mode of Payment", "Tiền mặt"):
			m = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Tiền mặt", "type": "Cash"})
			m.insert(ignore_permissions=True)
			_DA_TAO.append((m.doctype, m.name))
		m = frappe.get_doc("Mode of Payment", "Tiền mặt")
		m.append("accounts", {"company": cty, "default_account": tien})
		m.save(ignore_permissions=True)
	if not frappe.db.exists("Mode of Payment", tkr.PT_CK):
		m = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": tkr.PT_CK, "type": "Bank"})
		m.insert(ignore_permissions=True)
		_DA_TAO.append((m.doctype, m.name))
	return tien


def _loi_tao_khach():
	"""Khách mới tạo hỏng thì nhap_khach nuốt lỗi vào Error Log: đọc ra để ca
	kiểm đỏ nói được nguyên nhân thật (bench #531 chỉ thấy câu chung chung)."""
	r = frappe.get_all("Error Log", filters={"method": "nhap_khach: gan khach cho don"}, fields=["error"],
		order_by="creation desc", limit_page_length=1)
	return (r[0].error or "")[-1500:] if r else "(không có Error Log)"


def _sao_ke(ba, tien, noi_dung):
	from vagabond import sepay
	sepay.them_tai_khoan(frappe.db.get_value("Bank Account", ba, "bank_account_no"), ba)
	ref = "FTKT630" + frappe.generate_hash(length=10)
	g = frappe.get_doc({"doctype": "Bank Transaction", "date": today(), "bank_account": ba,
		"deposit": tien, "withdrawal": 0, "currency": "VND", "description": noi_dung,
		"reference_number": ref, "transaction_id": ref})
	g.insert(ignore_permissions=True)
	_DA_TAO.append((g.doctype, g.name))
	g.submit()
	return g


@ca("v630 thiết kế riêng: phiếu đặt giá máy chủ, cọc chuyển khoản chiếm sao kê, kế toán ghi sổ, tiền mặt tại quầy, giao bánh cấn đúng hai phiếu, sổ cái và két đúng")
def _vong_doi():
	cty, _tk_thue, _mau = _nen_thue()
	_mon()
	_tien_mat(cty)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	from vagabond import noi_dung_web as nw
	tp = nw.chuan_tkr(nw.TKR_MAU)
	diem = [{"id": "tcv", "n": "The Vagabond District 1", "a": "9 Trần Cao Vân"}]
	sdt = "09%08d" % (int(hashlib.sha1(frappe.generate_hash().encode()).hexdigest(), 16) % 10 ** 8)
	don = tkr.chuan_don({"tac_pham": tp["id"], "kich_co": "M", "trang_tri": ["Hoa lan trắng"],
		"ngay": str(add_days(today(), 10)), "ten": "Khách kiểm 630", "sdt": sdt, "diem_nhan": "tcv", "tong": 1}, tp, today(), diem)
	la("giá máy chủ", (don["tong"], don["coc"]), (7560000, 3780000))
	so = khong_nem("lập phiếu đặt", lambda: tkr._lap_phieu_dat(don, "kt630" + frappe.generate_hash(length=20)))
	if not so:
		dung("lỗi tạo khách (Error Log): " + _loi_tao_khach(), False)
		return
	_DA_TAO.append(("Sales Order", so.name))
	so.reload()
	la("phiếu đặt đã ghi sổ, đúng giá gồm VAT", (so.docstatus, flt(so.rounded_total) or flt(so.grand_total), so.items[0].item_code, flt(so.items[0].rate)),
		(1, 7560000.0, tkr.MA_MON, 7560000.0))
	dung("thuế đã gồm trong giá", all(t.included_in_print_rate for t in so.taxes))
	dung("bảng kê trên dòng", "Croquembouche" in (so.items[0].description or ""))

	# Một khoản ứng trước KHÁC của cùng khách (tiền chuyển dư cũ): hoá đơn ngày giao không được vơ.
	khac = frappe.get_doc({"doctype": "Payment Entry", "payment_type": "Receive", "company": cty, "party_type": "Customer",
		"party": so.customer, "paid_amount": 500000, "received_amount": 500000, "posting_date": today(),
		"paid_to": _mot("Account", {"company": cty, "account_type": "Cash", "is_group": 0, "disabled": 0}),
		"reference_no": "KT630-KHAC", "reference_date": today()})
	khac.setup_party_account_field()
	khac.set_missing_values()
	khac.insert(ignore_permissions=True)
	_DA_TAO.append((khac.doctype, khac.name))
	khac.submit()

	g = _sao_ke(ba, 3780000, "MBVCB.%s coc banh" % so.vgb_tkr_ma)
	la("lập một phiếu cọc", khong_nem("khớp sao kê", lambda: tkr.khop_mot(so.name)), 1)
	la("chạy lại không lập đôi", khong_nem("khớp lại", lambda: tkr.khop_mot(so.name)), 0)
	coc = frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name, "docstatus": 0}, pluck="name")
	la("một phiếu nháp", len(coc), 1)
	if not coc:
		return
	pe = frappe.get_doc("Payment Entry", coc[0])
	_DA_TAO.append((pe.doctype, pe.name))
	la("ô phiếu cọc", (pe.vgb_gd_tkr, pe.vgb_quay, pe.mode_of_payment, flt(pe.paid_amount), pe.bank_account),
		(g.name, tkr.quay_chuyen_khoan(tkr._ds_diem()), tkr.PT_CK, 3780000.0, ba))
	from vagabond import doi_soat_sepay as dss
	dung("dòng sao kê đã có chủ trong sổ chung", g.name in dss.chu_cua_giao_dich([g.name]))
	la("trạng thái đã cọc", tkr.tom_tat(so.name)["trang_thai"], "da_coc")

	# Giao khi phiếu cọc còn nháp: chặn.
	try:
		tkr.giao_banh(so.name, "TCV")
	except frappe.ValidationError as e:
		dung("chặn giao khi còn phải thu", "còn phải thu" in str(e))
	else:
		dung("phải chặn giao khi còn phải thu", False)

	khong_nem("kế toán ghi sổ phiếu cọc", lambda: tkr.ghi_so_phieu(so.name, pe.name, ANH))
	pe.reload()
	la("phiếu cọc đã ghi sổ", pe.docstatus, 1)
	bat_dau = now_datetime()
	tm = khong_nem("thu tiền mặt tại TCV", lambda: tkr.thu_tien_mat(so.name, "TCV"))
	if not tm:
		return
	_DA_TAO.append(("Payment Entry", tm["phieu"]))
	p2 = frappe.get_doc("Payment Entry", tm["phieu"])
	la("phiếu tiền mặt", (p2.docstatus, p2.vgb_quay, p2.mode_of_payment, flt(p2.paid_amount), p2.vgb_phieu_dat), (1, "TCV", "Tiền mặt", 3780000.0, so.name))
	from vagabond import dat_banh
	la("két TCV nhận đúng tiền mặt", dat_banh.thu_ung_truoc("TCV", bat_dau, now_datetime()).get("Tiền mặt"), 3780000.0)
	dung("két TCV không có chuyển khoản của cọc", "Chuyển khoản" not in dat_banh.thu_ung_truoc("TCV", bat_dau, now_datetime()))
	try:
		tkr.thu_tien_mat(so.name, "TCV")
	except frappe.ValidationError as e:
		dung("thu đủ thì chặn thu thêm", "đã thu đủ" in str(e))
	else:
		dung("phải chặn thu thêm", False)

	kq = khong_nem("giao bánh và xuất hoá đơn", lambda: tkr.giao_banh(so.name, "TCV"))
	if not kq:
		return
	_DA_TAO.append(("Sales Invoice", kq["hoa_don"]))
	si = frappe.get_doc("Sales Invoice", kq["hoa_don"])
	la("hoá đơn ngày giao", (si.docstatus, str(si.posting_date), si.vgb_pt_thanh_toan, si.vgb_quay, si.custom_pancake_id),
		(1, today(), "Trả trước", "TCV", "TKR-" + so.vgb_tkr_ma))
	la("tổng hoá đơn bằng tổng phiếu đặt", flt(si.rounded_total) or flt(si.grand_total), 7560000.0)
	la("cấn đủ, không còn nợ", (flt(si.total_advance), flt(si.outstanding_amount)), (7560000.0, 0.0))
	la("chỉ cấn hai phiếu của đơn", sorted(a.reference_name for a in si.advances), sorted([pe.name, p2.name]))
	ple = frappe.get_all("Payment Ledger Entry", filters={"against_voucher_no": si.name, "delinked": 0}, fields=["amount"])
	la("sổ công nợ hoá đơn về 0", round(sum(flt(p.amount) for p in ple)), 0)
	khac.reload()
	la("khoản ứng trước khác của khách vẫn nguyên", flt(khac.unallocated_amount), 500000.0)
	dung("dòng hoá đơn trỏ phiếu đặt", all(d.sales_order == so.name for d in si.items))
	la("trạng thái đã giao", tkr.tom_tat(so.name)["trang_thai"], "da_giao")
	try:
		tkr.giao_banh(so.name, "TCV")
	except frappe.ValidationError as e:
		dung("chặn hoá đơn thứ hai", "đã giao" in str(e))
	else:
		dung("phải chặn hoá đơn thứ hai", False)


@ca("v630 thiết kế riêng: đơn chưa cọc huỷ được; đơn đã có phiếu thu (kể cả nháp) không huỷ được")
def _huy():
	cty, _tk_thue, _mau = _nen_thue()
	_mon()
	from vagabond import noi_dung_web as nw
	tp = nw.chuan_tkr(nw.TKR_MAU)
	diem = [{"id": "tcv", "n": "The Vagabond District 1", "a": "9 Trần Cao Vân"}]
	don = tkr.chuan_don({"tac_pham": tp["id"], "kich_co": "S", "trang_tri": [], "ngay": str(add_days(today(), 9)),
		"ten": "Khách huỷ 630", "sdt": "0912000630", "diem_nhan": "tcv"}, tp, today(), diem)
	so = khong_nem("lập phiếu đặt", lambda: tkr._lap_phieu_dat(don, "kt630h" + frappe.generate_hash(length=20)))
	if not so:
		dung("lỗi tạo khách (Error Log): " + _loi_tao_khach(), False)
		return
	_DA_TAO.append(("Sales Order", so.name))
	khong_nem("huỷ đơn chưa cọc", lambda: tkr.huy(so.name, "Khách đổi ý, kiểm 630"))
	la("phiếu đặt đã huỷ", frappe.db.get_value("Sales Order", so.name, "docstatus"), 2)
	la("trạng thái đã huỷ", tkr.tom_tat(so.name)["trang_thai"], "da_huy")
