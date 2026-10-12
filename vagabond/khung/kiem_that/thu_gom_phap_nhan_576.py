"""v576 (Codex #443): một giao dịch khách chuyển gộp cho HAI pháp nhân, chạy thật.

Ca thật gốc: Loan Anh gom Công ty TNHH Oshima's và anh Vũ Oshima vào một phiếu
đề nghị thanh toán. Khách chuyển một lần. Máy lập mỗi khách một phiếu thu
nháp cùng giao dịch, chung mã nhóm; kế toán đính UNC và ghi sổ lần lượt từng
phiếu, giao dịch ngân hàng nối cả hai.

Codex #443 vòng 3 đòi ca tích hợp: tầng khung thay Payment Entry và Bank
Transaction bằng đồ giả nên không chứng minh được ERPNext nhận cả hai lần
ghi sổ, sổ cái và trạng thái giao dịch đúng. Các ca dưới dựng hoá đơn, khách,
giao dịch THẬT trong điểm lưu của nen.py, gọi đúng cửa màn Công nợ, rồi đọc
lại phiếu thu, dư nợ, sổ cái, dòng nối giao dịch.
"""
from unittest.mock import patch

import frappe
from frappe.utils import flt

from vagabond import ban_hang
from vagabond import cong_no as cn
from vagabond import thu_tien as tt
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_phieu_thu_unc_534 import _Tep, _gl
from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd, _sales


def _khach(ten):
	c = frappe.get_doc({"doctype": "Customer", "customer_name": "KT576 %s %s" % (ten, frappe.generate_hash(length=6)),
		"customer_type": "Company",
		"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
		"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name")})
	c.insert(ignore_permissions=True); _DA_TAO.append((c.doctype, c.name))
	return c.name


def _hd(tk, cty, tien, kh):
	"""Hoá đơn ghi sổ còn nợ của khách `kh`, đi đúng tao_don_tay như ca #571."""
	from vagabond import diem_ban
	cac_diem = diem_ban.diem_cua_nguon("GrabFood")
	quay = next((ma for ma in cac_diem if not diem_ban.theo_ma(ma)["quay"]), cac_diem[0])
	with patch.object(ban_hang, "_cong_ty", return_value=cty), patch.object(ban_hang, "_khach_le", return_value=kh):
		ra = ban_hang.tao_don_tay(nguon="GrabFood", quay=quay, ma_don="KT576-" + frappe.generate_hash(length=10),
			items=[dict(item_code=_mon(tk), qty=1, rate=tien)], tam_tinh=1)
	_DA_TAO.append(("Sales Invoice", ra["name"]))
	si = frappe.get_doc("Sales Invoice", ra["name"])
	si.vgb_tam_tinh = 0
	si.vgb_pt_thanh_toan = "GrabFood"
	si.vgb_ma_tham_chieu = "KT576-" + frappe.generate_hash(length=8)
	si.save(ignore_permissions=True)
	si.submit(); si.reload()
	dung("hoá đơn đúng khách", si.customer == kh)
	return si


def _phieu(ds_si, khach_dung_ten):
	d = frappe.new_doc("Vagabond Cong No")
	d.ma_phieu = "DNTT-KT576-" + frappe.generate_hash(length=6)
	d.khach = khach_dung_ten
	d.ten_khach = khach_dung_ten
	d.ngay_tao = frappe.utils.nowdate()
	d.han_qr = frappe.utils.add_days(frappe.utils.nowdate(), 7)
	d.trang_thai = "Cho thu"
	for s in ds_si:
		d.append("dong", {"hoa_don": s.name, "khach": s.customer, "ngay": s.posting_date, "so_tien": flt(s.grand_total)})
	d.insert(ignore_permissions=True); _DA_TAO.append((d.doctype, d.name))
	return d


def _du_lieu():
	cty, tk, _mau = _nen()
	osh, vu = _khach("Oshima"), _khach("Vu")
	a = _hd(tk, cty, 4540000, osh)
	b = _hd(tk, cty, 5000000, vu)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	g = _gd(ba, flt(a.grand_total) + flt(b.grand_total))
	p = _phieu([a, b], vu)
	ai = _sales()
	truoc = frappe.session.user
	try:
		frappe.set_user(ai)
		with patch.object(cn, "_gui_thu_da_nhan", lambda d: None):
			kq = cn.khop_tay(p.name, flt(g.deposit), g.reference_number, "KT576")
	finally:
		frappe.set_user(truoc)
	cac = [frappe.get_doc("Payment Entry", t) for t in kq["pe"].split(", ")]
	for pe in cac:
		_DA_TAO.append((pe.doctype, pe.name))
	return a, b, g, p, cac


@ca("v576 Sales khớp tay một giao dịch cho hai pháp nhân: HAI phiếu thu nháp thật, đúng khách, chung nhóm, đều xác minh được")
def _khop():
	a, b, g, p, cac = _du_lieu()
	la("hai phiếu", len(cac), 2)
	la("đúng khách và hoá đơn", sorted((pe.party, tuple(r.reference_name for r in pe.references)) for pe in cac),
		sorted([(a.customer, (a.name,)), (b.customer, (b.name,))]))
	la("còn nháp", [pe.docstatus for pe in cac], [0, 0])
	la("cùng giao dịch", {pe.reference_no for pe in cac}, {g.reference_number})
	dung("chung một mã nhóm máy ghi", len({pe.vgb_nhom_gd for pe in cac}) == 1 and bool(cac[0].vgb_nhom_gd))
	la("phiếu đòi nợ đã thu đủ", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Da thu du")
	ds = {x["pe"]: x["da_xac_minh"] for x in tt.phieu_thu_nhap(cac_si=[a.name, b.name])}
	la("Tiền đã về xác minh cả hai", sorted(ds.items()), sorted((pe.name, 1) for pe in cac))


@ca("v576 kế toán ghi sổ lần lượt hai phiếu cùng nhóm: GL đúng từng phiếu, hai hoá đơn hết nợ, giao dịch nối cả hai")
def _ghi_so():
	a, b, g, p, cac = _du_lieu()
	for i, pe in enumerate(cac):
		with _Tep() as t:
			r = tt.ghi_so_phieu_thu(pe.name, unc=[t.file_url])
			la("ghi sổ phiếu %d" % (i + 1), r.get("ok"), 1)
		pe.reload()
		la("phiếu %d vào sổ" % (i + 1), pe.docstatus, 1)
		la("GL phiếu %d" % (i + 1), sorted((x[0], round(x[2]), round(x[3])) for x in _gl(pe)),
			sorted([(pe.paid_to, round(flt(pe.paid_amount)), 0), (pe.paid_from, 0, round(flt(pe.paid_amount)))]))
		if i == 0:
			# Sau phiếu đầu, phiếu còn lại của nhóm vẫn xác minh được (Codex #443 vòng 3).
			con = {x["pe"]: x["da_xac_minh"] for x in tt.phieu_thu_nhap(cac_si=[a.name, b.name])}
			la("phiếu còn lại vẫn ở Tiền đã về", con.get(cac[1].name), 1)
	a.reload(); b.reload(); g.reload()
	la("hoá đơn Oshima hết nợ", flt(a.outstanding_amount), 0.0)
	la("hoá đơn anh Vũ hết nợ", flt(b.outstanding_amount), 0.0)
	la("giao dịch nối cả hai", sorted(x.payment_entry for x in g.payment_entries), sorted(pe.name for pe in cac))
	la("giao dịch hết tiền chưa phân bổ", round(flt(g.unallocated_amount)), 0)


@ca("v576 phiếu tự chế chép mã nhóm qua API thì bị bỏ ô nhóm, không nối được vào giao dịch đã nối")
def _gia_mao():
	a, b, g, p, cac = _du_lieu()
	with _Tep() as t:
		la("ghi sổ phiếu đầu", tt.ghi_so_phieu_thu(cac[0].name, unc=[t.file_url]).get("ok"), 1)
	gia = frappe.copy_doc(cac[1])
	gia.vgb_nhom_gd = cac[0].vgb_nhom_gd
	gia.flags.ignore_permissions = True
	gia.insert(ignore_permissions=True); _DA_TAO.append((gia.doctype, gia.name))
	la("ô nhóm bị bỏ lúc lưu", frappe.db.get_value("Payment Entry", gia.name, "vgb_nhom_gd"), None)
	with _Tep() as t:
		# Có tệp UNC thì cửa ghi sổ trả câu lỗi thay vì ném (để giữ tệp vừa đính).
		try:
			r = tt.ghi_so_phieu_thu(gia.name, unc=[t.file_url])
		except frappe.ValidationError:
			r = {"ok": 0}
		la("không ghi sổ được phiếu tự chế", r.get("ok"), 0)
	la("phiếu tự chế vẫn nháp", frappe.db.get_value("Payment Entry", gia.name, "docstatus"), 0)
