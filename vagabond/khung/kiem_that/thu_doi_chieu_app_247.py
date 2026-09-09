"""#247: thao tác APP tạo PE/JE rồi đối chiếu bằng lõi ERPNext thật.

Chứng từ thử có nguồn riêng, hoàn nguyên bởi nen; không gửi ra ngoài.
"""
import frappe
from frappe.utils import today
from unittest.mock import patch
from vagabond import ho_so_tt as hs, doi_chieu_app as dc
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO, cong_ty, _mot, mot_nha_cung_cap
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua, _ho_so_ncc, _unc_gia, _giao_dich_ngan_hang, _tk_ngan_hang


def _nen(tien=12345, tay=False):
	hd = _hoa_don_mua(tien)
	h = _ho_so_ncc([hd])
	_unc_gia(h)
	g = _giao_dich_ngan_hang(h.name, tien, cong_ty())
	if tay:
		g.description = "Thanh toan internet khong ghi duoc ma APP"
		g.save(ignore_permissions=True)
	return h, g


def _ghi(h, g):
	kq = hs.danh_dau_da_tra(h.name, gui_thu=0)
	bo = hs._but_toan_cua_ho_so(h.name)
	_DA_TAO.extend((b["doctype"], b["name"]) for b in bo)
	g.reload()
	la("đã đối chiếu lõi", g.status, "Reconciled")
	la("không còn tiền chưa phân bổ", float(g.unallocated_amount), 0.0)
	la("đủ liên kết", len(g.payment_entries), len(bo))
	for b in bo:
		la("clearance_date lấy từ sao kê", str(frappe.db.get_value(b["doctype"], b["name"], "clearance_date")), str(g.date))
		gl = frappe.get_all("GL Entry", filters={"voucher_type": b["doctype"], "voucher_no": b["name"], "is_cancelled": 0}, fields=["debit", "credit"])
		dung("có GL thật", bool(gl))
		la("GL cân", sum(float(r.debit)-float(r.credit) for r in gl), 0.0)
	return kq


@ca("#247 tự dò mã trong tham chiếu, ghi PE và retry không thêm liên kết")
def _tu_dong():
	h, g = _nen()
	g.description, g.reference_number = "CK", h.name.replace(".", "")
	g.save(ignore_permissions=True)
	_ghi(h, g)
	kq = hs.danh_dau_da_tra(h.name, gui_thu=0)
	la("retry được nhận diện", kq["da_lam_roi"], 1)
	g.reload()
	la("vẫn một liên kết", len(g.payment_entries), 1)


@ca("#247 chọn tay trước thanh toán và đối chiếu lại sau thanh toán là idempotent")
def _tay():
	h, g = _nen(tay=True)
	r = dc.danh_sach(h.name)
	dung("list có giao dịch không mang APP", any(x["ma"] == g.name for x in r["rows"]))
	dc.gan(h.name, g.name)
	la("chọn chưa ghi sổ", frappe.db.get_value(h.doctype, h.name, "trang_thai"), "Da duyet")
	_ghi(h, g)
	dc.gan(h.name, g.name)
	g.reload()
	la("chỉ một liên kết", len(g.payment_entries), 1)


@ca("#247 chi tiện ích bằng JE dùng cùng Bank Transaction Payments lõi")
def _je():
	cty = cong_ty()
	h = frappe.new_doc("Vagabond Ho So TT")
	h.ma = hs._sinh_ma()
	h.loai, h.ngay, h.trang_thai, h.da_tam_ung = "TK cong ty", today(), "Da duyet", 0
	h.nha_cung_cap = mot_nha_cung_cap()
	h.tk_chi = _tk_ngan_hang(cty)
	h.loai_cp_thue = "Chi phi hop le"
	h.append("dong", {"noi_dung": "Internet thử #247", "so_tien": 12345,
		"tk_no": _mot("Account", {"company": cty, "is_group": 0, "root_type": "Expense", "disabled": 0})})
	h.insert(ignore_permissions=True)
	_DA_TAO.append((h.doctype, h.name))
	_unc_gia(h)
	g = _giao_dich_ngan_hang("KHONG-MA", 12345, cty)
	dc.gan(h.name, g.name)
	_ghi(h, g)
	la("nối JE", g.payment_entries[0].payment_document, "Journal Entry")


@ca("#247 giao dịch đã chọn không cho APP khác hoặc Desk chiếm lại")
def _trung():
	h, g = _nen(tay=True)
	h2 = _ho_so_ncc([_hoa_don_mua(12345)])
	dc.gan(h.name, g.name)
	for lam in (lambda: dc.gan(h2.name, g.name), lambda: _luu_tay(h2, g.name)):
		try:
			lam()
		except frappe.ValidationError as e:
			dung("nêu chủ cũ", h.name in str(e))
		else:
			dung("phải chặn giao dịch trùng", False)
	la("APP thứ hai chưa có giao dịch", frappe.db.get_value(h2.doctype, h2.name, "ma_giao_dich") or "", "")


def _luu_tay(h, ma):
	h.ma_giao_dich = ma
	h.save(ignore_permissions=True)


@ca("#247 lỗi đối chiếu sau submit phải hoàn nguyên PE, GL và trạng thái")
def _loi():
	h, g = _nen()
	frappe.db.savepoint("app247_loi")
	try:
		with patch.object(dc, "noi_but_toan", side_effect=frappe.ValidationError("Lỗi đối chiếu thử")):
			hs.danh_dau_da_tra(h.name, gui_thu=0)
	except frappe.ValidationError:
		# Mô phỏng rollback của POST bị lỗi; không tự dọn chứng từ để xanh.
		frappe.db.rollback(save_point="app247_loi")
	else:
		dung("phải ném lỗi", False)
	la("không PE sót", hs._but_toan_cua_ho_so(h.name), [])
	la("giữ Đã duyệt", frappe.db.get_value(h.doctype, h.name, "trang_thai"), "Da duyet")
	g.reload()
	la("không liên kết dở", len(g.payment_entries), 0)


@ca("#247 chuyển giữa hai tài khoản: tiền vào không triệt tiêu tiền ra cùng mã APP")
def _hai_chieu():
	h, g = _nen(7000599)
	vao = frappe.new_doc("Bank Transaction")
	vao.date, vao.bank_account = today(), g.bank_account
	vao.deposit, vao.withdrawal = 7000599, 0
	vao.description = g.description
	vao.reference_number = "THU-247-" + frappe.generate_hash(length=6)
	vao.insert(ignore_permissions=True)
	_DA_TAO.append((vao.doctype, vao.name))
	vao.submit()
	la("bộ dò không bù trừ chiều vào", hs._sepay_theo_ma_app([h.name])[h.name]["chi"], 7000599.0)
	la("cửa APP nhận đủ tiền ra", hs.kiem_sepay(h.name)["rows"][0]["da_chi"], 7000599.0)
	_ghi(h, g)
	vao.reload()
	la("dòng tiền vào không bị chiếm", len(vao.payment_entries), 0)
