"""Ghi nhận thanh toán hồ sơ TT trên chứng từ THẬT (v445, Codex #225 R1, R2, R6).

Tầng khung đã chốt thứ tự commit, khoá, retry bằng Frappe giả lập. Tầng
này hỏi câu mà tầng khung không trả lời được: ERPNext version-16 có CHẤP
THUẬN bút toán mà `_tao_but_toan` dựng ra không, và khi công nợ đã đổi thì
hệ có thật sự dừng chứ không sinh khoản ứng trước.

Giới hạn nói thẳng: khung `nen.py` khoá tay lái giao dịch (mọi `commit()`
bị bỏ qua) nên tầng này KHÔNG chứng minh được "một commit duy nhất" của R1;
điều đó chỉ chốt được ở tầng khung, và bằng hai kết nối DB thật trên bench
kiểm thử riêng. Ca R1 hai request đồng thời chưa có ở đây.

Mọi chứng từ dựng ra đều biến mất khi ca kết thúc (điểm lưu của nen.py).
"""

import json

import frappe
from frappe.utils import today

from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_that.nen import (
	_DA_TAO, _mot, ca, cong_ty, dung, khong_nem, la, mot_nha_cung_cap, so_cai_cua,
)


# ------------------------------------------------------------------- dựng


def _mon_dich_vu():
	return _mot("Item", {"is_stock_item": 0, "disabled": 0, "is_purchase_item": 1,
		"is_fixed_asset": 0})


def _tk_ngan_hang(cty):
	return _mot("Bank Account", {"is_company_account": 1, "company": cty})


def _hoa_don_mua(tien, ncc=None):
	"""Một hoá đơn mua DỊCH VỤ đã ghi sổ, còn nợ đúng `tien`."""
	cty = cong_ty()
	ncc = ncc or mot_nha_cung_cap()
	mon = _mon_dich_vu()
	for nhan, gt in (("nhà cung cấp", ncc), ("mã hàng dịch vụ mua được", mon)):
		if not gt:
			frappe.throw("Site này chưa có %s để dựng hoá đơn thử." % nhan)
	hd = frappe.new_doc("Purchase Invoice")
	hd.company = cty
	hd.supplier = ncc
	hd.posting_date = today()
	hd.set_posting_time = 1
	hd.bill_no = "KIEMTHAT-%s" % frappe.generate_hash(length=6)
	hd.bill_date = today()
	hd.append("items", {"item_code": mon, "qty": 1, "rate": tien})
	hd.flags.ignore_permissions = True
	hd.insert(ignore_permissions=True)
	_DA_TAO.append((hd.doctype, hd.name))
	hd.submit()
	return hd


def _unc_gia(ho_so):
	"""Một tệp UNC giả đính lên hồ sơ, để hàng rào UNC thật vẫn chạy."""
	f = frappe.get_doc({
		"doctype": "File", "file_name": "UNC-kiem-that.txt",
		"content": "UNC gia lap cho ca kiem tich hop", "is_private": 1,
		"attached_to_doctype": "Vagabond Ho So TT", "attached_to_name": ho_so.name,
	})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	_DA_TAO.append(("File", f.name))
	frappe.db.set_value("Vagabond Ho So TT", ho_so.name, "unc_tep", f.name, update_modified=False)
	ho_so.unc_tep = f.name
	return f


def _ho_so_ncc(hoa_dons):
	"""Hồ sơ NCC Đã duyệt, mỗi hoá đơn một dòng trả ĐỦ nợ."""
	h = frappe.new_doc("Vagabond Ho So TT")
	h.loai = "NCC"
	h.ngay = today()
	h.nha_cung_cap = hoa_dons[0].supplier
	h.ten_ncc = hoa_dons[0].supplier_name
	h.trang_thai = "Da duyet"
	h.da_tam_ung = 0
	for hd in hoa_dons:
		h.append("dong", {"hoa_don": hd.name, "so_hd_ncc": hd.bill_no, "tong_hd": hd.grand_total,
			"con_no": hd.outstanding_amount, "so_tien": hd.outstanding_amount})
	h.flags.ignore_permissions = True
	h.insert(ignore_permissions=True)
	_DA_TAO.append((h.doctype, h.name))
	_chot_ke_thu(h)
	return h


def _chot_ke_thu(h):
	"""Fixture đã duyệt chốt kế hoạch trước khi sinh bút toán; không sửa hồ sơ cũ."""
	ke = hs._dung_ke_hoach_chi(h, "Chuyển khoản")
	loi = hs._loi_ke_hoach_chi(ke)
	if loi:
		frappe.throw("Fixture chưa đủ dữ liệu VND: " + loi)
	h.ke_hoach_chi = json.dumps(ke, ensure_ascii=False, sort_keys=True)
	h.flags.vgb_chot_ke_hoach_chi = True
	try:
		h.save(ignore_permissions=True)
	finally:
		h.flags.vgb_chot_ke_hoach_chi = False


def _giao_dich_ngan_hang(ma_ho_so, tien, cty):
	"""Dòng sao kê SePay giả: chi `tien`, nội dung mang mã hồ sơ."""
	ba = _tk_ngan_hang(cty)
	if not ba:
		frappe.throw("Site này chưa có tài khoản ngân hàng công ty để dựng sao kê thử.")
	g = frappe.new_doc("Bank Transaction")
	g.date = today()
	g.bank_account = ba
	g.withdrawal = tien
	g.deposit = 0
	g.description = "CK %s KIEM THAT" % ma_ho_so.replace(".", "")
	g.reference_number = "FT-KIEMTHAT-%s" % frappe.generate_hash(length=5)
	g.flags.ignore_permissions = True
	g.insert(ignore_permissions=True)
	_DA_TAO.append((g.doctype, g.name))
	return g


def _pe_cua(ho_so):
	return frappe.get_all("Payment Entry", filters={"vgb_ho_so_tt": ho_so, "docstatus": 1},
		fields=["name", "paid_amount", "unallocated_amount", "total_allocated_amount"])


# ------------------------------------------------------------------ các ca


@ca("v445 R6: bút toán từ hồ sơ phân bổ ĐỦ, unallocated 0, ERPNext ghi sổ được")
def _r6_phan_bo_du():
	hd = khong_nem("dựng hoá đơn mua dịch vụ 100.000", lambda: _hoa_don_mua(100000))
	if not hd:
		return
	la("hoá đơn còn nợ đúng 100.000", float(hd.outstanding_amount), 100000.0)
	ho = khong_nem("dựng hồ sơ NCC Đã duyệt", lambda: _ho_so_ncc([hd]))
	if not ho:
		return
	khong_nem("đính UNC giả", lambda: _unc_gia(ho))
	ten = khong_nem("ERPNext nhận Payment Entry do _tao_but_toan dựng",
		lambda: hs._tao_but_toan(ho, today(), "Chuyển khoản"))
	if not ten:
		return
	for t in ten.split(", "):
		_DA_TAO.append(("Payment Entry", t))
	pe = _pe_cua(ho.name)
	la("đúng một Payment Entry mang vgb_ho_so_tt", len(pe), 1)
	la("trả đúng 100.000", float(pe[0]["paid_amount"]), 100000.0)
	la("phân bổ hết, không dư", float(pe[0]["unallocated_amount"] or 0), 0.0)
	la("hoá đơn hết nợ", float(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 0.0)
	bo = hs._but_toan_cua_ho_so(ho.name)
	la("phép tra ngược thấy đúng phiếu", [b["name"] for b in bo], [pe[0]["name"]])
	ke = hs._ke_hoach_duyet(ho, "Chuyển khoản")
	la("bộ chứng từ được xem là đủ", hs._kiem_bo_chung_tu(ke, bo, hs._do_chinh_xac())["du"], 1)
	# SO CAI THAT (Codex review #226): dung tai khoan, dung doi tuong, dung
	# chieu. Khong tin o tren phieu, doc GL Entry vua sinh.
	pe_doc = frappe.get_doc("Payment Entry", pe[0]["name"])
	gl = so_cai_cua(pe_doc)
	dung("có dòng sổ cái", len(gl) >= 2)
	co_nh = [g for g in gl if g["account"] == pe_doc.paid_from]
	no_pt = [g for g in gl if g["account"] == pe_doc.paid_to]
	la("Có tài khoản ngân hàng đúng 100.000", sum(float(g["credit"]) for g in co_nh), 100000.0)
	la("Nợ tài khoản phải trả đúng 100.000", sum(float(g["debit"]) for g in no_pt), 100000.0)
	la("dòng phải trả mang đúng nhà cung cấp", sorted({(g["party_type"], g["party"]) for g in no_pt}), [("Supplier", hd.supplier)])
	la("không dòng nào ngoài hai tài khoản đó", sorted({g["account"] for g in gl}), sorted({pe_doc.paid_from, pe_doc.paid_to}))


@ca("v445 R6: nợ giảm sau khi duyệt thì DỪNG, không phiếu, không khoản ứng trước")
def _r6_no_doi():
	hd = khong_nem("dựng hoá đơn 100.000", lambda: _hoa_don_mua(100000))
	if not hd:
		return
	ho_a = khong_nem("hồ sơ A đề nghị trả đủ 100.000", lambda: _ho_so_ncc([hd]))
	if not ho_a:
		return
	khong_nem("UNC cho A", lambda: _unc_gia(ho_a))
	# Mot khoan tra khac chen vao SAU khi A duyet: phieu chi 60.000 dung
	# tay, cung hoa don. Khong dung ho so thu hai vi controller cam hai ho so
	# con hieu luc tro cung mot hoa don, va luat do dung.
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type, pe.company = "Pay", cong_ty()
	pe.posting_date = today()
	pe.party_type, pe.party = "Supplier", hd.supplier
	pe.paid_amount = pe.received_amount = 60000
	pe.reference_no, pe.reference_date = "KIEMTHAT-60", today()
	from vagabond.tra_tien_app import tk_tien_chi
	tk, ba = tk_tien_chi(pe.company, "Chuyển khoản", None)
	if not tk:
		dung("site có tài khoản tiền chi để dựng phiếu 60.000", False)
		return
	pe.paid_from = tk
	if ba:
		pe.bank_account = ba
	pe.append("references", {"reference_doctype": "Purchase Invoice", "reference_name": hd.name,
		"total_amount": 100000, "outstanding_amount": 100000, "allocated_amount": 60000})
	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.flags.ignore_permissions = True
	khong_nem("chèn phiếu chi 60.000", lambda: pe.insert(ignore_permissions=True))
	_DA_TAO.append(("Payment Entry", pe.name))
	from vagabond.tra_tien_app import chep_unc
	chep_unc(ho_a.name, "Payment Entry", pe.name)
	if not khong_nem("ghi sổ phiếu chi 60.000", pe.submit):
		return
	la("hoá đơn chỉ còn nợ 40.000", float(frappe.db.get_value("Purchase Invoice", hd.name, "outstanding_amount")), 40000.0)

	so_pe_truoc = frappe.db.count("Payment Entry")
	cau = ""
	try:
		hs._tao_but_toan(ho_a, today(), "Chuyển khoản")
	except Exception as e:
		cau = str(e)
	dung("máy dừng vì công nợ đã đổi", "chỉ còn nợ" in cau)
	dung("câu nói rõ nợ lúc duyệt và nợ nay", "sau khi duyệt" in cau)
	la("không sinh thêm Payment Entry nào", frappe.db.count("Payment Entry"), so_pe_truoc)
	la("không có phiếu nào mang vgb_ho_so_tt của A", len(_pe_cua(ho_a.name)), 0)
	la("hồ sơ A vẫn Đã duyệt", frappe.db.get_value("Vagabond Ho So TT", ho_a.name, "trang_thai"), "Da duyet")


@ca("v445 R1: Journal Entry của hồ sơ Chi từ TK công ty mang vgb_ho_so_tt và tra ngược được")
def _r1_je_link():
	cty = cong_ty()
	ba = _tk_ngan_hang(cty)
	tk_no = _mot("Account", {"company": cty, "is_group": 0, "root_type": "Expense", "disabled": 0})
	if not (ba and tk_no):
		dung("site có tài khoản ngân hàng và một tài khoản chi phí", False)
		return
	h = frappe.new_doc("Vagabond Ho So TT")
	h.loai, h.ngay, h.trang_thai, h.da_tam_ung = "TK cong ty", today(), "Da duyet", 0
	h.nha_cung_cap = mot_nha_cung_cap()
	h.tk_chi = ba
	h.loai_cp_thue = "Chi phi hop le"
	h.append("dong", {"noi_dung": "Kiểm thử tích hợp v445", "so_tien": 12345, "tk_no": tk_no})
	h.flags.ignore_permissions = True
	if not khong_nem("dựng hồ sơ Chi từ TK công ty", lambda: h.insert(ignore_permissions=True)):
		return
	_DA_TAO.append((h.doctype, h.name))
	_chot_ke_thu(h)
	khong_nem("UNC giả", lambda: _unc_gia(h))
	ten = khong_nem("ERPNext nhận Journal Entry do _tao_but_toan_tkct dựng",
		lambda: hs._tao_but_toan_tkct(h, today(), "Chuyển khoản"))
	if not ten:
		return
	_DA_TAO.append(("Journal Entry", ten))
	la("ô vgb_ho_so_tt trên Journal Entry có thật và trỏ về hồ sơ",
		frappe.db.get_value("Journal Entry", ten, "vgb_ho_so_tt"), h.name)
	bo = hs._but_toan_cua_ho_so(h.name)
	la("tra ngược ra đúng bút toán", [b["name"] for b in bo], [ten])
	ke = hs._ke_hoach_duyet(h, "Chuyển khoản")
	la("đủ bộ", hs._kiem_bo_chung_tu(ke, bo, hs._do_chinh_xac())["du"], 1)
	# SO CAI THAT: No tai khoan chi phi, Co tai khoan ngan hang, dung so.
	je = frappe.get_doc("Journal Entry", ten)
	gl = so_cai_cua(je)
	tk_nh = frappe.db.get_value("Bank Account", ba, "account")
	la("Nợ tài khoản chi phí 12.345", sum(float(g["debit"]) for g in gl if g["account"] == tk_no), 12345.0)
	la("Có tài khoản ngân hàng 12.345", sum(float(g["credit"]) for g in gl if g["account"] == tk_nh), 12345.0)
	la("không dòng nào ngoài hai tài khoản đó", sorted({g["account"] for g in gl}), sorted({tk_no, tk_nh}))
	# Doi chieu tung dong phai bat duoc JE dung tong ma sai tai khoan.
	bo_sai = [dict(bo[0])]
	bo_sai[0]["dong"] = [dict(r, account=(tk_nh if r["account"] == tk_no else r["account"])) for r in bo[0]["dong"]]
	la("JE sai tài khoản Nợ bị coi là không đủ", hs._kiem_bo_chung_tu(ke, bo_sai, hs._do_chinh_xac())["du"], 0)


@ca("v445 R2: đổi thẳng hồ sơ sang Đã thanh toán qua Desk bị controller chặn")
def _r2_controller():
	hd = khong_nem("dựng hoá đơn 50.000", lambda: _hoa_don_mua(50000))
	if not hd:
		return
	ho = khong_nem("dựng hồ sơ", lambda: _ho_so_ncc([hd]))
	if not ho:
		return
	doc = frappe.get_doc("Vagabond Ho So TT", ho.name)
	doc.trang_thai = "Da thanh toan"
	doc.flags.ignore_permissions = True
	cau = ""
	try:
		doc.save(ignore_permissions=True)
	except Exception as e:
		cau = str(e)
	dung("bị chặn với câu hoàn tất phải qua ghi nhận", "Ghi nhận đã thanh toán" in cau)
	la("trạng thái trong sổ vẫn Đã duyệt",
		frappe.db.get_value("Vagabond Ho So TT", ho.name, "trang_thai"), "Da duyet")


@ca("v445 R1+R2: danh_dau_da_tra trọn lượt trên chứng từ thật, bấm lại không sinh thêm")
def _r1_tron_luot():
	hd = khong_nem("dựng hoá đơn 80.000", lambda: _hoa_don_mua(80000))
	if not hd:
		return
	ho = khong_nem("dựng hồ sơ", lambda: _ho_so_ncc([hd]))
	if not ho:
		return
	khong_nem("UNC giả", lambda: _unc_gia(ho))
	khong_nem("sao kê giả 80.000", lambda: _giao_dich_ngan_hang(ho.name, 80000, cong_ty()))
	so_pe_truoc = frappe.db.count("Payment Entry")

	kq = khong_nem("ghi nhận đã thanh toán lượt 1",
		lambda: hs.danh_dau_da_tra(ho.name, ma_giao_dich="FT-KIEMTHAT", gui_thu=0))
	if not kq:
		return
	for t in (kq.get("but_toan") or "").split(", "):
		if t:
			_DA_TAO.append(("Payment Entry", t))
	la("hồ sơ Đã thanh toán", frappe.db.get_value("Vagabond Ho So TT", ho.name, "trang_thai"), "Da thanh toan")
	la("sinh đúng một phiếu", frappe.db.count("Payment Entry") - so_pe_truoc, 1)
	la("bộ chứng từ đủ", kq["bo_chung_tu"]["du"], 1)

	kq2 = khong_nem("bấm lại lượt 2", lambda: hs.danh_dau_da_tra(ho.name, gui_thu=0))
	if not kq2:
		return
	la("báo đã làm rồi", kq2.get("da_lam_roi"), 1)
	la("trả lại đúng phiếu cũ", kq2.get("but_toan"), kq.get("but_toan"))
	la("không sinh thêm phiếu", frappe.db.count("Payment Entry") - so_pe_truoc, 1)

	# B2: huy phieu chi roi bam lai: khong duoc "ok", phai bao chua xac minh.
	pe_ten = kq.get("but_toan")
	pe_doc = frappe.get_doc("Payment Entry", pe_ten)
	pe_doc.flags.ignore_permissions = True
	da_huy = True
	try:
		pe_doc.cancel()
	except Exception as e:
		da_huy = False
		dung("huỷ được phiếu chi để giả tình huống mất bộ chứng từ: " + str(e)[:200], False)
	if da_huy:
		cau = ""
		try:
			hs.danh_dau_da_tra(ho.name, gui_thu=0)
		except Exception as e:
			cau = str(e)
		dung("bấm lại sau khi phiếu bị huỷ thì báo chưa xác minh", "Chưa xác minh" in cau or "không khớp" in cau)
		la("không sinh phiếu mới thay thế", frappe.db.count("Payment Entry") - so_pe_truoc, 1)

	# Duong bo qua but toan da dong, ke ca voi ho so da xong.
	cau = ""
	try:
		hs.danh_dau_da_tra(ho.name, tao_but_toan=0)
	except Exception as e:
		cau = str(e)
	dung("tao_but_toan=0 bị từ chối", "bỏ qua bút toán" in cau)
