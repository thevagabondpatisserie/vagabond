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
	g = _giao_dich_ngan_hang(h.name, tien, cong_ty(),
		noi_dung="Thanh toan internet khong ghi duoc ma APP" if tay else None)
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
	h, g = _nen(tay=True)
	g.reference_number = h.name.replace(".", "")
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
	return h, g


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


@ca("#247 một APP nhiều nhà cung cấp đối chiếu đủ các PE vào cùng sao kê")
def _nhieu_pe():
	hd = _hoa_don_mua(10000)
	ncc = frappe.copy_doc(frappe.get_doc("Supplier", hd.supplier))
	ncc.supplier_name = "NCC kiểm #247 " + frappe.generate_hash(length=8)
	ncc.insert(ignore_permissions=True)
	_DA_TAO.append((ncc.doctype, ncc.name))
	hd2 = _hoa_don_mua(2345, ncc.name)
	h = _ho_so_ncc([hd, hd2])
	_unc_gia(h)
	g = _giao_dich_ngan_hang(h.name, 12345, cong_ty())
	_ghi(h, g)
	la("hai nhà cung cấp tạo hai PE", len(g.payment_entries), 2)


def _bi_chan(lam, chu):
	try:
		lam()
	except frappe.ValidationError as e:
		dung("câu lỗi chỉ rõ cách xử lý", chu in str(e))
	else:
		dung("phải chặn thao tác", False)


@ca("#247 huỷ PE giải phóng sao kê qua nút app, giữ vết và cho hồ sơ khác dùng")
def _huy_bo():
	h, g = _nen(22222)
	_ghi(h, g)
	_bi_chan(lambda: dc.bo(h.name), "Sao kê còn liên kết")
	h.reload()
	_bi_chan(lambda: _luu_tay(h, ""), "Sao kê còn liên kết")
	bo = hs._but_toan_cua_ho_so(h.name)
	frappe.get_doc(bo[0]["doctype"], bo[0]["name"]).cancel()
	g.reload()
	la("lõi tự gỡ", len(g.payment_entries), 0)
	la("lõi hoàn tiền chưa phân bổ", float(g.unallocated_amount), 22222.0)
	dc.bo(h.name)
	dc.bo(h.name)
	la("bỏ giữ mã", frappe.db.get_value(h.doctype, h.name, "ma_giao_dich") or "", "")
	dung("giữ dấu vết mã cũ", bool(frappe.get_all("Comment", filters={"reference_doctype": h.doctype,
		"reference_name": h.name, "content": ["like", "%" + g.name + "%"]}, pluck="name")))
	h2 = _ho_so_ncc([_hoa_don_mua(22222)])
	dc.gan(h2.name, g.name)
	la("APP khác lấy lại được", frappe.db.get_value(h2.doctype, h2.name, "ma_giao_dich"), g.name)


@ca("#247 unreconcile lõi còn PE sống thì không bỏ giữ mã, đối chiếu lại không ghi đôi")
def _go_loi():
	from erpnext.accounts.doctype.bank_transaction.bank_transaction import unreconcile_transaction
	h, g = _nen()
	_ghi(h, g)
	bo = hs._but_toan_cua_ho_so(h.name)
	unreconcile_transaction(g.name)
	g.reload()
	la("lõi gỡ đối chiếu", len(g.payment_entries), 0)
	_bi_chan(lambda: dc.bo(h.name), "Hồ sơ còn bút toán")
	dc.gan(h.name, g.name)
	g.reload()
	la("nối lại đủ", len(g.payment_entries), len(bo))
	la("không sinh bút toán mới", hs._but_toan_cua_ho_so(h.name), bo)


@ca("#247 lọc đúng khoản phải chuyển ở máy chủ dù client gửi số cũ")
def _loc_tien():
	h, g = _nen()
	r = dc.danh_sach(h.name, so_tien=1)
	dung("vẫn thấy dòng đúng", any(x["ma"] == g.name for x in r["rows"]))


@ca("#247 tranh chấp trả câu tiếng Việt và vẫn ném lỗi để POST rollback")
def _loi_khoa():
	with patch.object(dc, "_ho_so", side_effect=frappe.QueryDeadlockError("Deadlock found")):
		_bi_chan(lambda: dc.gan("APP-THU", "BT-THU"), "Tải lại hồ sơ")
		_bi_chan(lambda: dc.bo("APP-THU"), "Tải lại hồ sơ")


@ca("#247 huỷ JE giải phóng sao kê và cho hồ sơ khác chọn lại")
def _huy_je():
	h, g = _je()
	frappe.get_doc("Journal Entry", g.payment_entries[0].payment_entry).cancel()
	dc.bo(h.name)
	h2 = _ho_so_ncc([_hoa_don_mua(12345)])
	dc.gan(h2.name, g.name)
	la("sao kê JE dùng lại được", frappe.db.get_value(h2.doctype, h2.name, "ma_giao_dich"), g.name)


@ca("#247 người không có FIN bị chặn ở đọc, gán và bỏ đối chiếu")
def _quyen():
	cu = frappe.session.user
	try:
		frappe.set_user("Guest")
		for ham in (lambda: dc.danh_sach("APP-THU"), lambda: dc.gan("APP-THU", "BT-THU"), lambda: dc.bo("APP-THU")):
			_bi_chan(ham, "không có quyền")
	finally:
		frappe.set_user(cu)


@ca("#247 thiếu Bank Account thì fixture dựng bản ghi thật trong điểm lưu")
def _thieu_ngan_hang():
	from vagabond.khung.kiem_that import thu_ho_so_tt_v445 as thu
	goc = thu._mot
	with patch.object(thu, "_mot", side_effect=lambda dt, loc: None if dt == "Bank Account" else goc(dt, loc)):
		ba = thu._tk_ngan_hang(cong_ty())
	doc = frappe.get_doc("Bank Account", ba)
	la("đúng công ty", doc.company, cong_ty())
	dung("có tài khoản GL", bool(doc.account))
	dung("được theo dõi để hoàn nguyên", (doc.doctype, doc.name) in _DA_TAO)
