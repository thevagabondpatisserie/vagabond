"""v633: khách trả phiếu đề nghị thanh toán bằng thẻ OnePay, chạy trên ERPNext thật.

Đi ĐÚNG các cửa: trang khách đọc phiếu bằng khoá riêng, `tao_gd` tạo giao dịch
cho số còn phải trả, OnePay gọi `ipn` với PHIÊN KHÁCH (Guest) và chữ ký HMAC.
Đọc lại phiếu thu: phương thức OnePay, đúng tài khoản, ĐÃ GHI SỔ (hook UNC thật
nhận biên nhận OnePay đính kèm), hoá đơn hết nợ, phiếu "Đã thu đủ". Gọi IPN lần
hai không lập thêm phiếu thu; chữ ký giả không ghi gì. Khoá dùng ở đây là giá
trị bịa trong điểm lưu, không phải khoá thật của tiệm.
"""
import random
from unittest.mock import patch

import frappe
from frappe.utils import flt
from frappe.utils.password import set_encrypted_password

from vagabond import onepay as op
from vagabond import thu_tien as tt
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _khach, _hd, _phieu

KHOA = "0123456789ABCDEF0123456789ABCDEF"
VS = "Vagabond Settings"


def _bat_onepay():
	frappe.db.set_single_value(VS, {"onepay_bat": 1, "onepay_cong": " mtf.onepay.vn/paygate/vpcpay.op ",
		"onepay_merchant": "KIEMTHU633"})
	set_encrypted_password(VS, VS, "ABCD1234", "onepay_access_code")
	set_encrypted_password(VS, VS, KHOA, "onepay_hash_code")
	frappe.clear_document_cache(VS, VS)


def _pt_onepay(cty, acc):
	if frappe.db.exists("Mode of Payment", op.PT):
		mp = frappe.get_doc("Mode of Payment", op.PT)
		mp.accounts = [r for r in mp.accounts if r.company != cty]
	else:
		mp = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": op.PT, "type": "Bank", "enabled": 1})
	mp.append("accounts", {"company": cty, "default_account": acc})
	mp.flags.ignore_permissions = True
	if mp.is_new():
		mp.insert(ignore_permissions=True)
		_DA_TAO.append((mp.doctype, mp.name))
	else:
		mp.save(ignore_permissions=True)
	la("phương thức OnePay về đúng tài khoản", tt.tk_tien_thu(cty, op.PT)[0], acc)


def _ket_qua(ma, tien, ma_kq="0", khoa=KHOA):
	ts = {"vpc_MerchTxnRef": ma, "vpc_Amount": op.so_tien_vpc(tien), "vpc_TxnResponseCode": ma_kq,
		"vpc_TransactionNo": "KT633" + frappe.generate_hash(length=6), "vpc_Card": "VC", "vpc_Merchant": "KIEMTHU633",
		"vpc_Command": "pay", "vpc_Locale": "vn"}
	ts["vpc_SecureHash"] = op.ky(ts, khoa)
	return ts


def _goi_ipn(ts):
	truoc = frappe.session.user
	try:
		frappe.set_user("Guest")
		return op.ipn(**ts).get_data(as_text=True)
	finally:
		frappe.set_user(truoc)


def _pe_cua(ds_si, docstatus):
	ten = sorted({r.parent for r in frappe.get_all("Payment Entry Reference", filters={
		"reference_doctype": "Sales Invoice", "reference_name": ["in", [s.name for s in ds_si]],
		"parenttype": "Payment Entry", "docstatus": docstatus}, fields=["parent"], limit_page_length=0)})
	for t in ten:
		_DA_TAO.append(("Payment Entry", t))
	return ten


@ca("v633 OnePay: khách trả thẻ qua trang /tra-the, IPN phiên khách ghi sổ phiếu thu OnePay có biên nhận, hoá đơn hết nợ, gọi lại không ghi hai lần, chữ ký giả không ghi")
def _vong_doi():
	cty, tk, _mau = _nen()
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	acc = frappe.db.get_value("Bank Account", ba, "account")
	_pt_onepay(cty, acc)
	_bat_onepay()
	dung("cấu hình đọc được và đủ", op.dung_duoc())
	kh = _khach("OnePay")
	ds = [_hd(tk, cty, 400000, kh) for _i in range(2)]
	ma_phieu = "DNTT-99-12-%05d" % random.randint(0, 99999)
	p = _phieu(ds, kh, ma_phieu=ma_phieu)
	tong = sum(flt(s.grand_total) for s in ds)

	k = op.khoa_phieu(ma_phieu)
	ma_ngan = ma_phieu.replace("-", "")
	la("khoá sai thì không thấy phiếu", op.thong_tin_trang(ma_ngan, "0" * 16), None)
	tt_trang = op.thong_tin_trang(ma_ngan, k)
	la("trang khách thấy đúng số còn phải trả", (tt_trang or {}).get("con"), tong)

	with patch.object(tt, "xep_gui_thu", lambda *a, **kw: None):
		truoc = frappe.session.user
		try:
			frappe.set_user("Guest")
			url = op.tao_gd(ma_ngan, k)["url"]
		finally:
			frappe.set_user(truoc)
		dung("chuyển sang cổng OnePay đã chuẩn hoá", url.startswith("https://mtf.onepay.vn/paygate/vpcpay.op?"))
		nk = op.doc_nhat_ky(frappe.db.get_value("Vagabond Cong No", p.name, "onepay_gd"))
		la("một giao dịch chờ, đúng số tiền", [(g["trang_thai"], flt(g["so_tien"])) for g in nk], [("cho", tong)])
		ma = nk[0]["ma"]

		la("chữ ký giả: OnePay nhận câu từ chối", _goi_ipn(_ket_qua(ma, tong, khoa="FFFF" + KHOA[4:])), op.DAP_IPN_SAI)
		la("chữ ký giả không lập phiếu thu", _pe_cua(ds, 1) + _pe_cua(ds, 0), [])

		la("IPN thành công: xác nhận đúng câu OnePay đòi", _goi_ipn(_ket_qua(ma, tong)), op.DAP_IPN_OK)
		da = _pe_cua(ds, 1)
		la("mỗi hoá đơn một phiếu thu ĐÃ GHI SỔ", len(da), 2)
		la("không còn phiếu nháp", _pe_cua(ds, 0), [])
		for ten in da:
			pe = frappe.get_doc("Payment Entry", ten)
			la("phương thức %s" % ten, pe.mode_of_payment, op.PT)
			la("về đúng tài khoản %s" % ten, pe.paid_to, acc)
			dung("có biên nhận OnePay đính kèm %s" % ten, frappe.db.count("File", {"attached_to_doctype": "Payment Entry",
				"attached_to_name": ten, "file_name": ["like", "onepay-%"]}) >= 1)
		for s in ds:
			s.reload()
			la("hoá đơn %s hết nợ" % s.name, flt(s.outstanding_amount), 0.0)
		d = frappe.get_doc("Vagabond Cong No", p.name)
		la("phiếu đã thu đủ", (d.trang_thai, flt(d.da_thu)), ("Da thu du", tong))
		la("nhật ký ghi đã ghi", op.doc_nhat_ky(d.onepay_gd)[0]["trang_thai"], "da_ghi")

		la("OnePay gọi lại cùng giao dịch: vẫn xác nhận", _goi_ipn(_ket_qua(ma, tong)), op.DAP_IPN_OK)
		la("không lập thêm phiếu thu", _pe_cua(ds, 1), da)
		la("trang khách báo đã trả đủ", op.thong_tin_trang(ma_ngan, k)["con"], 0.0)


@ca("Codex #534: hoá đơn bị trả bớt ở chỗ khác sau khi khách mở trang thẻ: chỉ ghi số phiếu thu thật, phần dư báo kế toán, phiếu không thành Đã thu đủ")
def _tra_bot_cho_khac():
	cty, tk, _mau = _nen()
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	acc = frappe.db.get_value("Bank Account", ba, "account")
	_pt_onepay(cty, acc)
	_bat_onepay()
	kh = _khach("OnePay2")
	ds = [_hd(tk, cty, 400000, kh) for _i in range(2)]
	ma_phieu = "DNTT-99-12-%05d" % random.randint(0, 99999)
	p = _phieu(ds, kh, ma_phieu=ma_phieu)
	ma_ngan = ma_phieu.replace("-", "")
	k = op.khoa_phieu(ma_phieu)

	def _dinh(pe):
		frappe.get_doc({"doctype": "File", "file_name": "kt534-%s.txt" % pe.name, "content": "Giấy báo Có thử",
			"is_private": 1, "attached_to_doctype": "Payment Entry", "attached_to_name": pe.name}).insert(ignore_permissions=True)

	with patch.object(tt, "xep_gui_thu", lambda *a, **kw: None):
		truoc = frappe.session.user
		try:
			frappe.set_user("Guest")
			op.tao_gd(ma_ngan, k)
		finally:
			frappe.set_user(truoc)
		ma = op.doc_nhat_ky(frappe.db.get_value("Vagabond Cong No", p.name, "onepay_gd"))[0]["ma"]
		# Khách chuyển khoản trả bớt 300.000 cho hoá đơn đầu, kế toán ghi ở chỗ khác.
		ngoai = tt.ghi_thu_tien(ds[0].name, [{"pt": op.PT, "so_tien": 300000}], nguon="kt534-ngoai", dinh=_dinh)
		for t in ngoai:
			_DA_TAO.append(("Payment Entry", t))
		la("IPN thành công 800.000", _goi_ipn(_ket_qua(ma, 800000)), op.DAP_IPN_OK)
		d = frappe.get_doc("Vagabond Cong No", p.name)
		g = op.doc_nhat_ky(d.onepay_gd)[0]
		la("nhật ký ghi đúng số đã ghi sổ và phần dư", (g["trang_thai"], flt(g["so_ghi"]), flt(g["du"])), ("da_ghi", 500000.0, 300000.0))
		ten = [t for t in _pe_cua(ds, 1) if t not in ngoai]
		la("phiếu thu OnePay của giao dịch cộng đúng 500.000",
			sum(flt(frappe.db.get_value("Payment Entry", t, "paid_amount")) for t in ten), 500000.0)
		la("phiếu ghi đã thu đúng số thật", (flt(d.da_thu), d.trang_thai), (500000.0, "Thu thieu"))
		dung("ghi chú phiếu báo phần dư cho kế toán", any("phần dư 300.000 đ" in (c.content or "") for c in
			frappe.get_all("Comment", filters={"reference_doctype": "Vagabond Cong No", "reference_name": p.name},
				fields=["content"], limit_page_length=0)))
		la("gọi lại không đổi số", _goi_ipn(_ket_qua(ma, 800000)), op.DAP_IPN_OK)
		la("vẫn 500.000", flt(frappe.db.get_value("Vagabond Cong No", p.name, "da_thu")), 500000.0)


@ca("Codex #534 vòng 2: mọi hoá đơn đã được trả đủ ở chỗ khác rồi khách mới trả thẻ: IPN xác nhận, không lập phiếu thu OnePay, toàn bộ tiền thẻ báo dư")
def _het_no_cho_khac():
	cty, tk, _mau = _nen()
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	acc = frappe.db.get_value("Bank Account", ba, "account")
	_pt_onepay(cty, acc)
	_bat_onepay()
	kh = _khach("OnePay3")
	ds = [_hd(tk, cty, 400000, kh) for _i in range(2)]
	ma_phieu = "DNTT-99-12-%05d" % random.randint(0, 99999)
	p = _phieu(ds, kh, ma_phieu=ma_phieu)
	ma_ngan = ma_phieu.replace("-", "")

	def _dinh(pe):
		frappe.get_doc({"doctype": "File", "file_name": "kt534b-%s.txt" % pe.name, "content": "Giấy báo Có thử",
			"is_private": 1, "attached_to_doctype": "Payment Entry", "attached_to_name": pe.name}).insert(ignore_permissions=True)

	with patch.object(tt, "xep_gui_thu", lambda *a, **kw: None):
		truoc = frappe.session.user
		try:
			frappe.set_user("Guest")
			op.tao_gd(ma_ngan, op.khoa_phieu(ma_phieu))
		finally:
			frappe.set_user(truoc)
		ma = op.doc_nhat_ky(frappe.db.get_value("Vagabond Cong No", p.name, "onepay_gd"))[0]["ma"]
		ngoai = []
		for s in ds:
			ngoai += tt.ghi_thu_tien(s.name, [{"pt": op.PT, "so_tien": 400000}], nguon="kt534b-ngoai", dinh=_dinh)
		for t in ngoai:
			_DA_TAO.append(("Payment Entry", t))
		la("IPN thành công vẫn được xác nhận", _goi_ipn(_ket_qua(ma, 800000)), op.DAP_IPN_OK)
		la("không lập phiếu thu OnePay nào", [t for t in _pe_cua(ds, 1) if t not in ngoai], [])
		g = op.doc_nhat_ky(frappe.db.get_value("Vagabond Cong No", p.name, "onepay_gd"))[0]
		la("nhật ký: đã ghi 0 đ, dư 800.000", (g["trang_thai"], flt(g["so_ghi"]), flt(g["du"])), ("da_ghi", 0.0, 800000.0))
		dung("ghi chú báo phần dư 800.000 đ", any("phần dư 800.000 đ" in (c.content or "") for c in
			frappe.get_all("Comment", filters={"reference_doctype": "Vagabond Cong No", "reference_name": p.name},
				fields=["content"], limit_page_length=0)))
