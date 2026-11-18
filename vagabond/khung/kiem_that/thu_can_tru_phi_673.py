"""v673 ca TÍCH HỢP (Codex #589, gộp vào #590): cấn trừ hoá đơn phí đối tác theo đối soát.

Tầng khung chốt phép đặt phí bằng bản giả. Tầng này hỏi điều bản giả không trả lời:
Frappe có THẬT SỰ lưu được phiếu chỉ có dòng tài khoản chờ (bảng Hoá đơn bán rỗng),
ERPNext ghi sổ đúng Nợ 331 / Có 131 / Có tài khoản chờ, công nợ hai bên về đúng số,
sửa tay phân bổ trên phiếu bị chặn ở lưu thật, và huỷ phiếu thì bút toán đảo, công
nợ hồi lại. Mọi thứ lùi về điểm lưu (nen.py); tệp bảng kê căn cứ dọn trên đĩa.
Chỉ thay phép tra tài khoản khai cho hình thức thanh toán (cấu hình), không thay sổ.
"""
from contextlib import contextmanager
from unittest.mock import patch

import frappe
from frappe.utils import flt, get_first_day, today

from vagabond import can_tru_phi as P
from vagabond import thu_tien
from vagabond.khung.kiem_that.he_so_252 import _luu
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _app, _mon, _nen
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua

DT = "payoo"
PT = P.DOI_TAC[DT][3]


def _tk_cho(ct):
	cha = frappe.db.get_value("Account", {"company": ct, "root_type": "Asset", "is_group": 1}, "name", order_by="lft desc")
	dung("có nhóm tài sản", bool(cha))
	return _luu(frappe.get_doc(dict(doctype="Account", company=ct, account_name="KT673 Chờ tiền về Payoo " + frappe.generate_hash(length=6),
		parent_account=cha, account_currency="VND", is_group=0))).name


@contextmanager
def _cau_hinh(tk):
	goc = thu_tien.tk_tien_thu
	with patch.object(thu_tien, "tk_tien_thu", lambda ct, pt: (tk, None) if pt == PT else goc(ct, pt)):
		yield


def _ncc():
	ncc = frappe.get_doc(dict(doctype="Supplier", supplier_name="NCC phí Payoo kiểm 673 " + frappe.generate_hash(length=8),
		supplier_group=frappe.db.get_value("Supplier Group", {"is_group": 0}, "name"), supplier_type="Company", tax_id="KIEM673"))
	return _luu(ncc).name


def _nguon_dong(ct, dong):
	n = _luu(frappe.get_doc(dict(doctype="Vagabond Doi Soat Nguon", company=ct, nhom="Tiền bán", vendor=P.DOI_TAC[DT][1],
		tu_ngay=str(get_first_day(today())), den_ngay=today(), trang_thai="Đã nhận", kenh_nhan="Tải tay",
		xac_nhan_luc=frappe.utils.now_datetime())))
	for loai, phi, si in dong:
		_luu(frappe.get_doc(dict(doctype="Vagabond Doi Soat Dong", nguon=n.name, company=ct, nhom="Tiền bán",
			vendor=P.DOI_TAC[DT][1], khoa="KT673-" + frappe.generate_hash(length=12), ngay=today(), loai=loai,
			ma_don="KT673-" + frappe.generate_hash(length=6), phi=phi, sales_invoice=si or None)))


def _si(ct):
	tk = _nen()[1]
	si = _app(ct, [dict(item_code=_mon(tk), qty=1, rate=1000000)])
	si.vgb_tam_tinh = 0
	si.vgb_pt_thanh_toan = PT
	si.save(ignore_permissions=True)
	si.submit()
	si.reload()
	frappe.db.set_value("Sales Invoice", si.name, "custom_hddt_so", "KIEM-673")
	return si


def _gl(je):
	return sorted((x.account, x.party or "", flt(x.debit), flt(x.credit)) for x in frappe.get_all("GL Entry",
		filters={"voucher_type": "Journal Entry", "voucher_no": je, "is_cancelled": 0}, fields=["account", "party", "debit", "credit"]))


def _don_tep(phieu):
	for f in frappe.get_all("File", filters={"file_url": phieu.can_cu}, pluck="name"):
		frappe.delete_doc("File", f, ignore_permissions=True, force=True)


@ca("v673 thật (Codex #589): phiếu hỗn hợp Nợ 331 / Có 131 / Có tài khoản chờ: lập, sửa tay bị chặn, xác nhận ghi sổ đúng, huỷ đảo và hồi công nợ")
def _hon_hop():
	ct = _nen()[0]
	tk = _tk_cho(ct)
	si = _si(ct)
	g = int(flt(si.outstanding_amount))
	_nguon_dong(ct, [("ban", 200000, si.name), ("ban", g, None)])
	pi = _hoa_don_mua(g + 200000, _ncc())
	tu, den = str(get_first_day(today())), today()
	phieu = None
	try:
		with _cau_hinh(tk):
			dx = P.de_xuat(hoa_don=pi.name, doi_tac=DT, loai="don", tu=tu, den=den)
			dung("đề xuất lập được: %s" % dx.get("ly_do"), dx.get("lap_duoc"))
			kq = P.lap(hoa_don=pi.name, doi_tac=DT, loai="don", tu=tu, den=den)
			phieu = frappe.get_doc(P.DT, kq["name"])
			_DA_TAO.append((phieu.doctype, phieu.name))
			la("phiếu: Có SI đúng dư 131", [(x.hoa_don, flt(x.so_tien)) for x in phieu.ban], [(si.name, float(g))])
			la("phiếu: Có tài khoản chờ phần còn lại", [(x.tai_khoan, flt(x.so_tien)) for x in phieu.tk], [(tk, 200000.0)])
			dung("ghi nguồn phí", bool(phieu.nguon_phi))
			# Desk sửa tay phân bổ: dời 1 đồng từ tài khoản sang hoá đơn bán.
			sua = frappe.get_doc(P.DT, phieu.name)
			sua.ban[0].so_tien = g + 1
			sua.tk[0].so_tien = 199999
			try:
				sua.save(ignore_permissions=True)
				dung("sửa tay phân bổ phải bị chặn", False)
			except frappe.ValidationError as e:
				dung("chặn vì khác cách tính theo đối soát", "khác cách tính" in str(e))
			kq = P.xac_nhan(phieu.name)
			la("đã cấn trừ", kq["trang_thai"], "Đã cấn trừ")
			_DA_TAO.append(("Journal Entry", kq["but_toan"]))
			la("sổ cái ba dòng", _gl(kq["but_toan"]), sorted([(pi.credit_to, pi.supplier, float(g + 200000), 0.0),
				(si.debit_to, si.customer, 0.0, float(g)), (tk, "", 0.0, 200000.0)]))
			pi.reload(); si.reload()
			la("331 hết nợ", flt(pi.outstanding_amount), 0.0)
			la("131 hết dư", flt(si.outstanding_amount), 0.0)
			phieu = frappe.get_doc(P.DT, phieu.name)
			phieu.cancel()
			pi.reload(); si.reload()
			la("huỷ: bút toán đảo", frappe.db.get_value("Journal Entry", kq["but_toan"], "docstatus"), 2)
			la("huỷ: 331 hồi lại", flt(pi.outstanding_amount), float(g + 200000))
			la("huỷ: 131 hồi lại", flt(si.outstanding_amount), float(g))
	finally:
		if phieu:
			_don_tep(phieu)


@ca("v673 thật (Codex #589): phí quảng cáo không còn hoá đơn bán nào: phiếu CHỈ có tài khoản chờ lưu được, ghi sổ Nợ 331 / Có tài khoản chờ, huỷ hoàn nguyên")
def _chi_tk():
	ct = _nen()[0]
	tk = _tk_cho(ct)
	_nguon_dong(ct, [("phi_ky", 300000, None)])
	pi = _hoa_don_mua(300000, _ncc())
	tu, den = str(get_first_day(today())), today()
	phieu = None
	try:
		with _cau_hinh(tk):
			kq = P.lap(hoa_don=pi.name, doi_tac=DT, loai="ky", tu=tu, den=den)
			phieu = frappe.get_doc(P.DT, kq["name"])
			_DA_TAO.append((phieu.doctype, phieu.name))
			la("không dòng hoá đơn bán", len(phieu.ban), 0)
			la("một dòng tài khoản chờ", [(x.tai_khoan, flt(x.so_tien)) for x in phieu.tk], [(tk, 300000.0)])
			kq = P.xac_nhan(phieu.name)
			la("đã cấn trừ", kq["trang_thai"], "Đã cấn trừ")
			_DA_TAO.append(("Journal Entry", kq["but_toan"]))
			la("sổ cái", _gl(kq["but_toan"]), sorted([(pi.credit_to, pi.supplier, 300000.0, 0.0), (tk, "", 0.0, 300000.0)]))
			pi.reload()
			la("331 hết nợ", flt(pi.outstanding_amount), 0.0)
			phieu = frappe.get_doc(P.DT, phieu.name)
			phieu.cancel()
			pi.reload()
			la("huỷ: 331 hồi lại", flt(pi.outstanding_amount), 300000.0)
	finally:
		if phieu:
			_don_tep(phieu)
