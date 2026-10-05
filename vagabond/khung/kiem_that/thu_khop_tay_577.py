"""v577: khớp tay KHÔNG gắn giao dịch, huỷ phiếu bị kẹt, SePay lập phiếu nháp. Chạy thật.

Ca thật gốc (Loan Anh 05/10/2026, phiếu DNTT-26-10-00004 của Ms.Dung, 17 hoá
đơn 8.450.000 đ): khách Kiệt Tác chuyển 9.550.000 đ, hộp Khớp tay lọc đúng số
tiền nên không hiện giao dịch đó. Loan Anh chọn "Không thấy giao dịch", gõ
8.450.000 đ. Máy lập 17 phiếu thu ngân hàng rồi ghi sổ thẳng; hook
chung_tu_tien.chan_thieu_dinh_kem chặn cả 17 vì không có Uỷ nhiệm chi đính
kèm; lỗi bị nuốt, phiếu đòi nợ vẫn thành "Đã thu đủ", 17 phiếu nháp hỏng ở
lại (Error Log site thật 16:03 05/10/2026, APP-26-10-134 tới 150).

Tầng khung thay Payment Entry và hook bằng đồ giả, nên không chứng minh được
ERPNext và hook UNC thật nhận phiếu thu do lối mới lập. Các ca dưới dựng hoá
đơn, khách, giao dịch, tệp THẬT trong điểm lưu của nen.py, gọi đúng cửa màn
Công nợ, rồi đọc lại phiếu thu, tệp đính kèm, dư nợ.
"""
import json
from unittest.mock import patch

import frappe
from frappe.utils import flt

from vagabond import cong_no as cn
from vagabond import thu_tien as tt
from vagabond import tep_dinh_kem
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_phieu_thu_unc_534 import _Tep
from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd, _sales
from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _khach, _hd, _phieu


def _ke_toan():
	"""Tài khoản thử vai kế toán (Accounts User) kèm Sales, như chị Dung."""
	u = frappe.get_doc({"doctype": "User",
		"email": "kt577-ketoan-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm Kế toán 577", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Accounts User"}, {"role": "Sales User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u.name


def _chuyen_khoan(cty, ba):
	"""Khai tài khoản cho hình thức "Chuyển khoản" của công ty thử, về đúng ngân hàng ba."""
	acc = frappe.db.get_value("Bank Account", ba, "account")
	if frappe.db.exists("Mode of Payment", "Chuyển khoản"):
		mp = frappe.get_doc("Mode of Payment", "Chuyển khoản")
		mp.accounts = [r for r in mp.accounts if r.company != cty]
	else:
		mp = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Chuyển khoản", "type": "Bank",
			"enabled": 1})
	mp.append("accounts", {"company": cty, "default_account": acc})
	mp.flags.ignore_permissions = True
	if mp.is_new():
		mp.insert(ignore_permissions=True)
		_DA_TAO.append((mp.doctype, mp.name))
	else:
		mp.save(ignore_permissions=True)
	la("hình thức chuyển khoản về đúng ngân hàng", tt.tk_tien_thu(cty, "Chuyển khoản")[0], acc)
	return acc


def _nen_577(so_hd=2, tien=500000):
	cty, tk, _mau = _nen()
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	acc = _chuyen_khoan(cty, ba)
	kh = _khach("Dung")
	ds = [_hd(tk, cty, tien, kh) for _i in range(so_hd)]
	p = _phieu(ds, kh)
	return cty, ba, acc, ds, p


def _goi_bang(ai, ham):
	truoc = frappe.session.user
	try:
		frappe.set_user(ai)
		with patch.object(cn, "_gui_thu_da_nhan", lambda d, **k: (False, "kiem that")):
			return ham()
	finally:
		frappe.set_user(truoc)


def _pe_cua(ds_si, docstatus):
	ten = sorted({r.parent for r in frappe.get_all("Payment Entry Reference", filters={
		"reference_doctype": "Sales Invoice", "reference_name": ["in", [s.name for s in ds_si]],
		"parenttype": "Payment Entry", "docstatus": docstatus}, fields=["parent"], limit_page_length=0)})
	for t in ten:
		_DA_TAO.append(("Payment Entry", t))
	return ten


@ca("v577 gốc lỗi Ms.Dung: phiếu thu ngân hàng ghi sổ thẳng KHÔNG UNC thì hook thật chặn")
def _goc():
	cty, ba, acc, ds, p = _nen_577(so_hd=1)
	try:
		tt.ghi_thu_tien(ds[0].name, [{"pt": "Chuyển khoản", "so_tien": flt(ds[0].grand_total)}], nguon="kt577-goc")
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("hook UNC chặn ghi sổ: " + loi[:120], "Uỷ nhiệm chi" in loi)


@ca("v577 kế toán khớp tay không giao dịch, đính UNC: mỗi hoá đơn một phiếu thu ĐÃ GHI SỔ có tệp, hoá đơn hết nợ")
def _ke_toan_khong_gd():
	cty, ba, acc, ds, p = _nen_577(so_hd=2)
	kt = _ke_toan()
	tong = sum(flt(s.grand_total) for s in ds)
	truoc = frappe.session.user
	frappe.set_user(kt)
	try:
		with _Tep() as t:
			la("tệp do chính kế toán tải lên", t.owner, kt)
			with patch.object(cn, "_gui_thu_da_nhan", lambda d, **k: (False, "kiem that")):
				kq = cn.khop_tay(p.name, tong, "", "KT577", ma_lan="kt577a", unc=json.dumps([t.file_url]))
			frappe.set_user(truoc)
			da = _pe_cua(ds, 1)
			la("hai phiếu thu đã vào sổ", len(da), 2)
			for ten in da:
				pe = frappe.get_doc("Payment Entry", ten)
				la("về đúng ngân hàng %s" % ten, pe.paid_to, acc)
				la("ô UNC ghi đúng tệp %s" % ten, tep_dinh_kem.doc_ds(pe.vgb_thu_unc), [t.file_url])
				dung("có tệp đính kèm thật %s" % ten, frappe.db.count("File", {"attached_to_doctype": "Payment Entry",
					"attached_to_name": ten, "file_url": t.file_url}) == 1)
			la("không còn phiếu nháp nào", _pe_cua(ds, 0), [])
			for s in ds:
				s.reload()
				la("hoá đơn %s hết nợ" % s.name, flt(s.outstanding_amount), 0.0)
			la("phiếu đòi nợ đã thu đủ", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Da thu du")
			la("không còn hoá đơn thiếu phiếu thu", cn._hd_chua_co_phieu_thu([s.name for s in ds]), set())
			la("câu báo không có lỗi", kq.get("loi"), [])
			# Dọn bản chép dòng File trước khi _Tep xoá tệp gốc (tệp trên đĩa
			# chỉ mất khi không còn dòng nào trỏ tới).
			for f in frappe.get_all("File", filters={"file_url": t.file_url, "name": ["!=", t.name]}, pluck="name"):
				frappe.delete_doc("File", f, ignore_permissions=True)
	finally:
		frappe.set_user(truoc)


@ca("v577 Sales chọn không giao dịch thì bị chặn, phiếu không đổi, không có phiếu thu nào")
def _sales_khong_gd():
	cty, ba, acc, ds, p = _nen_577(so_hd=1)
	ai = _sales()
	try:
		_goi_bang(ai, lambda: cn.khop_tay(p.name, flt(ds[0].grand_total), "", "KT577", ma_lan="kt577b"))
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("báo chỉ kế toán làm được: " + loi[:100], "chỉ kế toán" in loi)
	la("phiếu vẫn chờ thu", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Cho thu")
	la("không phiếu thu nào", _pe_cua(ds, 0) + _pe_cua(ds, 1), [])


@ca("v577 kế toán không đính UNC thì bị chặn trước mọi thay đổi")
def _ke_toan_thieu_unc():
	cty, ba, acc, ds, p = _nen_577(so_hd=1)
	kt = _ke_toan()
	try:
		_goi_bang(kt, lambda: cn.khop_tay(p.name, flt(ds[0].grand_total), "", "KT577", ma_lan="kt577c"))
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("báo phải đính UNC: " + loi[:100], "uỷ nhiệm chi" in loi)
	la("phiếu vẫn chờ thu", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Cho thu")
	la("không phiếu thu nào", _pe_cua(ds, 0) + _pe_cua(ds, 1), [])


def _nhap_hong(si, p):
	"""Dựng lại đúng phiếu nháp hỏng lối cũ để lại: khoá THU:<hoá đơn>:phieu:<tên>:tay:..."""
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Receive"
	pe.company = si.company
	pe.party_type = "Customer"
	pe.party = si.customer
	pe.paid_amount = pe.received_amount = flt(si.outstanding_amount)
	pe.reference_no = tt.khoa_chong_trung(si.name, "phieu:%s:tay:kt577|Chuyển khoản" % p.name)
	pe.reference_date = frappe.utils.nowdate()
	pe.paid_to = tt.tk_tien_thu(si.company, "Chuyển khoản")[0]
	pe.append("references", {"reference_doctype": "Sales Invoice", "reference_name": si.name,
		"total_amount": flt(si.grand_total), "outstanding_amount": flt(si.outstanding_amount),
		"allocated_amount": flt(si.outstanding_amount), "due_date": si.due_date})
	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.insert(ignore_permissions=True)
	_DA_TAO.append((pe.doctype, pe.name))
	return pe.name


@ca("v577 phiếu kẹt kiểu Ms.Dung (đã thu đủ, không giao dịch, nháp hỏng giữ nợ): Sales huỷ được, nháp hỏng được GỠ khỏi hoá đơn, không xoá")
def _huy_ket():
	cty, ba, acc, ds, p = _nen_577(so_hd=2)
	nhap = [_nhap_hong(s, p) for s in ds]
	frappe.db.set_value("Vagabond Cong No", p.name, {"trang_thai": "Da thu du", "da_thu": p.tong_tien})
	la("trước khi huỷ: phần nợ bị nháp hỏng phủ hết",
		sorted(tt.phan_bo_nhap_theo_hd([s.name for s in ds]).items()),
		sorted((s.name, flt(s.outstanding_amount)) for s in ds))
	xem = _goi_bang(_sales(), lambda: cn.xem_phieu(p.name))
	la("màn biết huỷ được", xem.get("huy_duoc"), 1)
	la("màn biết số nháp hỏng", xem.get("so_nhap_hong"), 2)
	kq = _goi_bang(_sales(), lambda: cn.huy_phieu(p.name, "KT577"))
	la("gỡ đúng hai nháp hỏng", sorted(kq.get("da_go_nhap")), sorted(nhap))
	for t in nhap:
		pe = frappe.get_doc("Payment Entry", t)
		# Codex #444 vòng 2 (QT-20): giữ phiếu để tra, chỉ gỡ khỏi hoá đơn.
		la("nháp %s vẫn còn, vẫn nháp" % t, pe.docstatus, 0)
		la("nháp %s hết dòng hoá đơn" % t, len(pe.references), 0)
		dung("nháp %s đổi khoá GO: và ghi vết phiếu đòi nợ" % t,
			(pe.reference_no or "").startswith("GO:THU:") and (p.ma_phieu in (pe.remarks or "")))
	la("phiếu đã huỷ", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Huy")
	# Codex #444 vòng 3: phiếu đã gỡ không ghi sổ được trên Desk, kể cả có tệp.
	pe = frappe.get_doc("Payment Entry", nhap[0])
	try:
		pe.flags.ignore_permissions = True
		pe.submit()
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("ghi sổ phiếu đã gỡ bị chặn: " + loi[:100], "đã bị gỡ" in loi)
	la("vẫn nháp", frappe.db.get_value("Payment Entry", nhap[0], "docstatus"), 0)
	pe = frappe.get_doc("Payment Entry", nhap[0])
	pe.reference_no = "THU:lay-lai"
	try:
		pe.save(ignore_permissions=True)
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("đổi khoá về như cũ bị chặn: " + loi[:100], "không đổi số tham chiếu" in loi)
	la("hoá đơn hết bị nháp giữ", tt.phan_bo_nhap_theo_hd([s.name for s in ds]), {})


@ca("v577 phiếu đã thu đủ có gạch giao dịch thì KHÔNG huỷ được")
def _huy_co_gd():
	cty, ba, acc, ds, p = _nen_577(so_hd=1)
	frappe.db.set_value("Vagabond Cong No", p.name, {"trang_thai": "Da thu du", "ma_gd": "FT-KT577"})
	try:
		_goi_bang(_sales(), lambda: cn.huy_phieu(p.name, "KT577"))
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("báo không huỷ được: " + loi[:80], "không huỷ được" in loi)
	la("phiếu giữ nguyên", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Da thu du")


@ca("v577 hộp Khớp tay thấy giao dịch LỚN hơn phiếu (ca Kiệt Tác 9,55tr cho phiếu 8,45tr), chọn thì máy báo dư bao nhiêu")
def _gd_lon_hon():
	cty, ba, acc, ds, p = _nen_577(so_hd=2)
	tong = sum(flt(s.grand_total) for s in ds)
	g = _gd(ba, tong + 1100000)
	kq = _goi_bang(_sales(), lambda: cn.tim_giao_dich_thu(so_ngay=5, so_tien=tong, chua_noi=1))
	ma = [r["ma"] for r in kq["rows"]]
	dung("giao dịch lớn hơn có trong danh sách", g.reference_number in ma)
	try:
		_goi_bang(_sales(), lambda: cn.khop_tay(p.name, tong, g.reference_number, "KT577", ma_lan="kt577d"))
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	dung("báo đúng phần dư 1.100.000: " + loi[:160], "dư 1.100.000 đ" in loi)
	la("phiếu không đổi", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Cho thu")
	la("không phiếu thu nào", _pe_cua(ds, 0), [])


@ca("v577 SePay tự khớp lập phiếu thu NHÁP theo đúng giao dịch, không ghi sổ thẳng, không để nháp hỏng")
def _sepay_nhap():
	cty, ba, acc, ds, p = _nen_577(so_hd=2)
	tong = sum(flt(s.grand_total) for s in ds)
	g = _gd(ba, tong)
	with patch.object(cn, "_sepay_cn", lambda ma: {"nhan": tong, "so_gd": 1, "gd": [g.name]}), \
			patch.object(cn, "_giu_gd", lambda d, ds_gd: "\n".join(ds_gd)):
		_goi_bang(_sales(), lambda: cn.kiem_sepay(p.name))
	la("phiếu đòi nợ đã thu đủ", frappe.db.get_value("Vagabond Cong No", p.name, "trang_thai"), "Da thu du")
	nhap = _pe_cua(ds, 0)
	la("một phiếu thu nháp", len(nhap), 1)
	la("mang đúng mã giao dịch", frappe.db.get_value("Payment Entry", nhap[0], "reference_no"), g.reference_number)
	la("không phiếu nào ghi sổ thẳng", _pe_cua(ds, 1), [])
	xm = {x["pe"]: x["da_xac_minh"] for x in tt.phieu_thu_nhap(cac_si=[s.name for s in ds])}
	la("Tiền đã về xác minh được", xm.get(nhap[0]), 1)
	la("không còn hoá đơn thiếu phiếu thu", cn._hd_chua_co_phieu_thu([s.name for s in ds]), set())
	# Codex #444 F1: tiền đã về nhưng phiếu thu còn nháp: màn không được báo sạch.
	la("màn biết còn 2 hoá đơn chờ ghi sổ", _goi_bang(_sales(), lambda: cn.xem_phieu(p.name)).get("cho_ghi_so"), 2)


@ca("v577 Codex #444 vòng 4: Thư báo gửi tay bị chặn khi phiếu thu còn nháp; kế toán ghi sổ THẲNG trên Desk thì hook on_submit xếp thư")
def _desk_gui_thu():
	cty, ba, acc, ds, p = _nen_577(so_hd=1)
	tong = sum(flt(s.grand_total) for s in ds)
	g = _gd(ba, tong)
	with patch.object(cn, "_sepay_cn", lambda ma: {"nhan": tong, "so_gd": 1, "gd": [g.name]}), \
			patch.object(cn, "_giu_gd", lambda d, ds_gd: "\n".join(ds_gd)):
		_goi_bang(_sales(), lambda: cn.kiem_sepay(p.name))
	nhap = _pe_cua(ds, 0)
	la("một phiếu thu nháp", len(nhap), 1)
	# Nút Thư báo: cửa gửi tay thật, không thay _gui_thu_da_nhan.
	truoc = frappe.session.user
	frappe.set_user(_sales())
	try:
		cn.gui_thu_da_nhan(p.name)
		loi = ""
	except frappe.ValidationError as e:
		loi = str(e)
	finally:
		frappe.set_user(truoc)
	dung("gửi tay bị chặn khi sổ còn nợ: " + loi[:160], "chưa hết nợ" in loi)
	la("chưa đánh dấu đã gửi", frappe.db.get_value("Vagabond Cong No", p.name, "email_da_gui") or 0, 0)
	# Đường Desk: đính tệp qua ô UNC rồi bấm Submit, không qua ghi_so_phieu_thu.
	gui = []
	pe = frappe.get_doc("Payment Entry", nhap[0])
	with _Tep(gan_vao=pe.name, o="vgb_thu_unc_tep") as t:
		pe.vgb_thu_unc_tep = t.file_url
		pe.save(ignore_permissions=True); pe.reload()
		cu = len(frappe.db.after_commit._functions)
		with patch.object(cn, "_gui_thu_da_nhan", lambda d, **k: gui.append((d.name, k.get("xep_hang"))) or (True, "kt")):
			pe.submit()
		pe.reload()
		la("phiếu thu vào sổ từ Desk", pe.docstatus, 1)
		ds[0].reload()
		la("hoá đơn hết nợ", flt(ds[0].outstanding_amount), 0.0)
		# Codex #444 vòng 6: trong giao dịch ghi sổ KHÔNG gửi gì, chỉ đăng ký
		# việc chạy sau commit; việc đó xếp việc nền gui_thu_nen.
		la("trong lúc ghi sổ chưa gửi", gui, [])
		cua_minh = [f for f in list(frappe.db.after_commit._functions)[cu:] if getattr(f, "func", None) is tt.xep_gui_thu]
		la("hook đăng ký đúng một việc sau commit", len(cua_minh), 1)
		xep = []
		with patch.object(frappe, "enqueue", lambda ham, **k: xep.append((ham, k))):
			cua_minh[0]()
		la("sau commit xếp việc nền đúng hoá đơn", xep,
			[("vagabond.cong_no.gui_thu_nen", {"queue": "short", "cac_hd": [ds[0].name]})])
		with patch.object(cn, "_gui_thu_da_nhan", lambda d, **k: gui.append((d.name, k.get("xep_hang"))) or (True, "kt")):
			la("việc nền gửi đúng phiếu đòi nợ", frappe.get_attr(xep[0][0])(**{"cac_hd": xep[0][1]["cac_hd"]}), [p.name])
		la("thư xếp hàng", gui, [(p.name, True)])
		for f in cua_minh:
			frappe.db.after_commit._functions.remove(f)


@ca("v577 Codex #444 vòng 5: SePay gặp giao dịch LỚN hơn phiếu (khách trả gộp): phiếu không kẹt, Sales huỷ được, giao dịch được nhả")
def _sepay_lon_hon_huy():
	from vagabond import doi_soat_sepay as dss
	cty, ba, acc, ds, p = _nen_577(so_hd=1)
	tong = sum(flt(s.grand_total) for s in ds)
	g = _gd(ba, tong + 1100000)
	with patch.object(cn, "_sepay_cn", lambda ma: {"nhan": tong + 1100000, "so_gd": 1, "gd": [g.name]}), \
			patch.object(cn, "_giu_gd", lambda d, ds_gd: "\n".join(ds_gd)):
		kq = _goi_bang(_sales(), lambda: cn.kiem_sepay(p.name))
	dung("báo lý do lập hỏng: %s" % kq.get("loi_lap"), any("1.100.000" in x for x in kq.get("loi_lap") or []))
	la("không phiếu thu nào", _pe_cua(ds, 0) + _pe_cua(ds, 1), [])
	la("phiếu ghi nhận giao dịch", frappe.db.get_value("Vagabond Cong No", p.name, ["trang_thai", "ma_gd"]),
		("Da thu du", g.name))
	la("giao dịch chưa có phiếu thu", cn._gd_da_dung(g.name), [])
	la("màn cho huỷ", _goi_bang(_sales(), lambda: cn.xem_phieu(p.name)).get("huy_duoc"), 1)
	_goi_bang(_sales(), lambda: cn.huy_phieu(p.name, "Kiet Tac tra gop"))
	la("đã huỷ, mã giao dịch còn để tra", frappe.db.get_value("Vagabond Cong No", p.name, ["trang_thai", "ma_gd"]),
		("Huy", g.name))
	dung("giao dịch không còn thuộc phiếu đòi nợ nào",
		not any("Cong No" in v or p.name in v for v in dss.chu_cua_giao_dich([g.name]).values()))
