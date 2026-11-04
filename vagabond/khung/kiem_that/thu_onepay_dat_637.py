"""v637: khách trả thẻ OnePay cho đơn đặt trước, chạy trên ERPNext thật.

Đi ĐÚNG các cửa: phiếu đặt thiết kế riêng lập bằng `thiet_ke_rieng._lap_phieu_dat`,
trang khách đọc đơn bằng khoá riêng, `tao_gd` (phiên khách) tạo giao dịch cho
số còn phải thu, OnePay gọi `ipn` với PHIÊN KHÁCH và chữ ký HMAC. Đọc lại phiếu
thu: phương thức OnePay, đúng tài khoản, ĐÃ GHI SỔ (hook UNC thật nhận biên
nhận đính kèm, bốn hàng rào dat_banh), quầy không két nên két TCV không thấy;
IPN lặp không lập thêm; giao bánh cấn đúng phiếu thu thẻ. Khoá dùng ở đây là giá
trị bịa trong điểm lưu, không phải khoá thật của tiệm.
"""
import hashlib

import frappe
from frappe.utils import add_days, flt, now_datetime, today

from vagabond import onepay as op
from vagabond import thiet_ke_rieng as tkr
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen as _nen_thue
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_onepay_633 import KHOA, _bat_onepay, _goi_ipn, _ket_qua, _pt_onepay
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_thiet_ke_rieng_630 import _loi_tao_khach, _mon, _tien_mat


@ca("v637 OnePay đơn đặt trước: khách trả thẻ qua QR màn quầy, IPN phiên khách ghi sổ phiếu thu OnePay của đúng phiếu đặt, quầy không két, gọi lại không lập thêm, giao bánh cấn đúng phiếu thẻ")
def _vong_doi():
	cty, _tk_thue, _mau = _nen_thue()
	_mon()
	_tien_mat(cty)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	acc = frappe.db.get_value("Bank Account", ba, "account")
	_pt_onepay(cty, acc)
	_bat_onepay()
	dung("cấu hình đọc được và đủ", op.dung_duoc())
	from vagabond import noi_dung_web as nw
	tp = nw.chuan_tkr(nw.TKR_MAU)
	diem = [{"id": "tcv", "n": "The Vagabond District 1", "a": "9 Trần Cao Vân"}]
	sdt = "0909%06d" % (int(hashlib.sha1(frappe.generate_hash().encode()).hexdigest(), 16) % 10 ** 6)
	don = tkr.chuan_don({"tac_pham": tp["id"], "kich_co": "M", "trang_tri": ["Hoa lan trắng"],
		"ngay": str(add_days(today(), 10)), "ten": "Khách kiểm 637", "sdt": sdt, "diem_nhan": "tcv", "tong": 1}, tp, today(), diem)
	so = khong_nem("lập phiếu đặt", lambda: tkr._lap_phieu_dat(don, "kt637" + frappe.generate_hash(length=20)))
	if not so:
		dung("lỗi tạo khách (Error Log): " + _loi_tao_khach(), False)
		return
	_DA_TAO.append(("Sales Order", so.name))
	so.reload()
	ma = so.vgb_tkr_ma
	tong = flt(so.rounded_total) or flt(so.grand_total)

	k = op.khoa_phieu(ma)
	la("khoá sai thì không thấy đơn", op.thong_tin_trang(ma, "0" * 16), None)
	la("trang khách thấy đúng số còn phải thu", (op.thong_tin_trang(ma, k) or {}).get("con"), tong)
	truoc = frappe.session.user
	try:
		frappe.set_user("Guest")
		url = op.tao_gd(ma, k)["url"]
	finally:
		frappe.set_user(truoc)
	dung("chuyển sang cổng OnePay", url.startswith("https://mtf.onepay.vn/paygate/vpcpay.op?"))
	nk = op.doc_nhat_ky(frappe.db.get_value("Sales Order", so.name, "vgb_onepay_gd"))
	la("một giao dịch chờ trên phiếu đặt, đúng số", [(g["trang_thai"], flt(g["so_tien"])) for g in nk], [("cho", tong)])
	gd = nk[0]["ma"]

	la("chữ ký giả: từ chối", _goi_ipn(_ket_qua(gd, tong, khoa="FFFF" + KHOA[4:])), op.DAP_IPN_SAI)
	la("chữ ký giả không lập phiếu thu", frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name}, pluck="name"), [])

	bat_dau = now_datetime()
	la("IPN thành công: xác nhận", _goi_ipn(_ket_qua(gd, tong)), op.DAP_IPN_OK)
	da = frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name, "docstatus": 1}, pluck="name")
	for t in da:
		_DA_TAO.append(("Payment Entry", t))
	la("một phiếu thu ĐÃ GHI SỔ", len(da), 1)
	la("không có phiếu nháp", frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name, "docstatus": 0}, pluck="name"), [])
	if not da:
		return
	pe = frappe.get_doc("Payment Entry", da[0])
	la("các ô phiếu thu", (pe.mode_of_payment, pe.paid_to, pe.vgb_quay, flt(pe.paid_amount), pe.reference_no),
		(op.PT, acc, tkr.quay_chuyen_khoan(tkr._ds_diem()), tong, "onepay:" + gd))
	dung("có biên nhận OnePay đính kèm", frappe.db.count("File", {"attached_to_doctype": "Payment Entry",
		"attached_to_name": pe.name, "file_name": ["like", "onepay-%"]}) >= 1)
	from vagabond import dat_banh
	dung("két TCV không thấy tiền thẻ", "OnePay" not in dat_banh.thu_ung_truoc("TCV", bat_dau, now_datetime()))
	la("đơn đã thu đủ", tkr.tom_tat(so.name)["trang_thai"], "du_tien")
	la("nhật ký đã ghi", op.doc_nhat_ky(frappe.db.get_value("Sales Order", so.name, "vgb_onepay_gd"))[0]["trang_thai"], "da_ghi")

	# Codex #538: đọc lại SỔ CÁI của phiếu thu (AGENTS: ca kiểm hạch toán phải đọc GL).
	def _gl():
		return sorted((r.account, flt(r.debit), flt(r.credit), r.party or "") for r in frappe.get_all("GL Entry",
			filters={"voucher_type": "Payment Entry", "voucher_no": ["in", da], "is_cancelled": 0},
			fields=["account", "debit", "credit", "party"], limit_page_length=0))
	gl = _gl()
	la("sổ cái: Nợ tài khoản OnePay, Có phải thu khách, đúng số", gl,
		sorted([(acc, tong, 0.0, ""), (pe.paid_from, 0.0, tong, so.customer)]))
	la("sổ cái cân", round(sum(x[1] for x in gl) - sum(x[2] for x in gl)), 0)

	la("OnePay gọi lại: vẫn xác nhận", _goi_ipn(_ket_qua(gd, tong)), op.DAP_IPN_OK)
	la("không lập thêm", frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name, "docstatus": ["<", 2]}, pluck="name"), da)
	la("sổ cái không ghi thêm sau IPN lặp", _gl(), gl)
	la("trang khách báo đã trả đủ", op.thong_tin_trang(ma, k)["con"], 0.0)

	kq = khong_nem("giao bánh và xuất hoá đơn", lambda: tkr.giao_banh(so.name, "TCV"))
	if not kq:
		return
	_DA_TAO.append(("Sales Invoice", kq["hoa_don"]))
	si = frappe.get_doc("Sales Invoice", kq["hoa_don"])
	la("cấn đúng phiếu thẻ, hết nợ", (sorted(a.reference_name for a in si.advances), flt(si.outstanding_amount)), (da, 0.0))


@ca("v637 Codex #538: khách đang trả thẻ thì đơn bị huỷ; OnePay báo thành công sau: không lập phiếu thu, nhật ký ghi phải hoàn toàn bộ, sổ cái không có bút toán")
def _huy_giua_chung():
	cty, _tk_thue, _mau = _nen_thue()
	_mon()
	_tien_mat(cty)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	_pt_onepay(cty, frappe.db.get_value("Bank Account", ba, "account"))
	_bat_onepay()
	from vagabond import noi_dung_web as nw
	tp = nw.chuan_tkr(nw.TKR_MAU)
	diem = [{"id": "tcv", "n": "The Vagabond District 1", "a": "9 Trần Cao Vân"}]
	sdt = "0909%06d" % (int(hashlib.sha1(frappe.generate_hash().encode()).hexdigest(), 16) % 10 ** 6)
	don = tkr.chuan_don({"tac_pham": tp["id"], "kich_co": "M", "trang_tri": ["Hoa lan trắng"],
		"ngay": str(add_days(today(), 10)), "ten": "Khách kiểm 637 huỷ", "sdt": sdt, "diem_nhan": "tcv", "tong": 1}, tp, today(), diem)
	so = khong_nem("lập phiếu đặt", lambda: tkr._lap_phieu_dat(don, "kt637h" + frappe.generate_hash(length=20)))
	if not so:
		dung("lỗi tạo khách (Error Log): " + _loi_tao_khach(), False)
		return
	_DA_TAO.append(("Sales Order", so.name))
	so.reload()
	ma = so.vgb_tkr_ma
	tong = flt(so.rounded_total) or flt(so.grand_total)
	truoc = frappe.session.user
	try:
		frappe.set_user("Guest")
		op.tao_gd(ma, op.khoa_phieu(ma))
	finally:
		frappe.set_user(truoc)
	gd = op.doc_nhat_ky(frappe.db.get_value("Sales Order", so.name, "vgb_onepay_gd"))[0]["ma"]
	khong_nem("huỷ đơn khi khách đang trả thẻ", lambda: tkr.huy(so.name, "khách đổi ý"))
	la("đơn đã huỷ", frappe.db.get_value("Sales Order", so.name, "docstatus"), 2)
	la("IPN thành công sau khi huỷ: vẫn xác nhận", _goi_ipn(_ket_qua(gd, tong)), op.DAP_IPN_OK)
	la("không lập phiếu thu", frappe.get_all("Payment Entry", filters={"vgb_phieu_dat": so.name}, pluck="name"), [])
	g = op.doc_nhat_ky(frappe.db.get_value("Sales Order", so.name, "vgb_onepay_gd"))[0]
	la("nhật ký: đã nhận, phải hoàn toàn bộ", (g["trang_thai"], flt(g["so_ghi"]), flt(g["du"])), ("da_ghi", 0.0, tong))
