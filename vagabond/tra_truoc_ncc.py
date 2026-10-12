"""v551: chi từ TK công ty cho khoản "hoá đơn đến sau" = TRẢ TRƯỚC nhà cung cấp.

Chị Dung 01/10/2026 (anh Việt duyệt): hồ sơ Adecco APP.26.09.009 ghi Nợ chi
phí / Có 1121 lúc chi, rồi khi hoá đơn về lại lập bút toán tay Nợ 331 / Có
chi phí để "bù trừ". Số cuối đúng nhưng sai đường: chi phí phát sinh hai
chiều (gồm cả VAT), lệch kỳ, và dùng phiếu kế toán cho việc của phân hệ
thanh toán. Quy trình đúng:

  Hoá đơn về:   Nợ chi phí + 1331 / Có 331 (tờ hoá đơn mua tự ghi)
  Chi tiền:     Nợ 331 NCC / Có 1121       (phiếu chi Payment Entry)
  => 331 hết nợ, chi phí chỉ đi theo tờ hoá đơn.

Nên từ v551, khoản chờ hoá đơn của hồ sơ Chi từ TK công ty (có nhà cung cấp)
ghi bằng MỘT phiếu chi trả trước cho nhà cung cấp, chưa phân bổ. Hoá đơn về:
- tờ đã ghi sổ thì lúc nối, máy phân bổ phiếu chi vào tờ (đối chiếu thanh
  toán lõi ERPNext), không lập bút toán bù trừ;
- tờ còn nháp thì nối làm căn cứ, ghi sổ tờ bình thường, máy tự phân bổ
  ngay lúc ghi sổ.
Hồ sơ đã chi theo cách cũ (chi phí ngay) giữ nguyên đường bù trừ cũ: không
sửa dữ liệu quá khứ (anh Việt chốt 13/08/2026).
"""
# ------------------------------------------------------------------ THUẦN


def _tien(v):
	try:
		return round(float(v or 0), 2)
	except (TypeError, ValueError):
		return 0.0


def _so(v):
	try:
		return int(v or 0)
	except (TypeError, ValueError):
		return 0


def la_dong_tra_truoc(dong, ncc, tk_ngan_hang=""):
	"""Khoản này của hồ sơ Chi từ TK công ty ghi thành trả trước NCC không.

	dong: {"cho_hoa_don", "so_tien", "tk_co", "tk_no_cong_no"}. Chỉ khi: đánh
	dấu hoá đơn đến sau, hồ sơ có nhà cung cấp, số tiền dương, và tiền ra từ
	đúng tài khoản ngân hàng của hồ sơ (tk_co trống hoặc trùng). Khoản ghi Có
	tài khoản khác (bù trừ nội bộ, quỹ) giữ đường bút toán cũ. THUẦN."""
	dong = dong or {}
	if not _so(dong.get("cho_hoa_don")) or not (ncc or "").strip():
		return False
	if _tien(dong.get("so_tien")) <= 0:
		return False
	tk_co = (dong.get("tk_co") or "").strip()
	return not tk_co or tk_co == (tk_ngan_hang or "").strip()


def tach_dong(dong, ncc, tk_ngan_hang="", da_chi=False):
	"""(tổng trả trước, [chỉ số khoản trả trước], [chỉ số khoản còn lại]). THUẦN.

	Một nguồn cho cả lúc sinh chứng từ và lúc đối chiếu bộ chứng từ (điều 18):
	hai nơi tự tính riêng là lệch ngay khi một bên đổi luật.

	Đã chi rồi thì KHÔNG suy lại từ cờ chờ hoá đơn (cờ đó còn bật/tắt được
	sau khi chi, và hồ sơ chi trước v551 không có phiếu trả trước nào): chỉ
	khoản mang dấu tra_truoc (máy đặt lúc ghi nhận thanh toán) là trả trước."""
	da_dau = any(_so((d or {}).get("tra_truoc")) for d in (dong or []))
	tt, i_tt, i_khac = 0.0, [], []
	for i, d in enumerate(dong or []):
		if _tien((d or {}).get("so_tien")) <= 0:
			continue
		if da_dau or da_chi:
			la = bool(_so(d.get("tra_truoc")))
		else:
			la = la_dong_tra_truoc(d, ncc, tk_ngan_hang)
		if la:
			tt += _tien(d.get("so_tien"))
			i_tt.append(i)
		else:
			i_khac.append(i)
	return round(tt, 2), i_tt, i_khac


def chia_phan_bo(phieu, can, ncc):
	"""Lấy từ các phiếu trả trước còn dư để phân bổ `can` đ cho tờ của `ncc`.

	phieu: [{"name", "party", "con"}] theo thứ tự cũ trước. Chỉ phiếu cùng
	nhà cung cấp với tờ (ERPNext không phân bổ chéo đối tượng). Trả
	(tổng lấy, [(phiếu, tiền)]). THUẦN."""
	con_can = max(_tien(can), 0.0)
	ra = []
	for p in phieu or []:
		if con_can <= 0.004:
			break
		if (p.get("party") or "") != (ncc or ""):
			continue
		lay = min(max(_tien(p.get("con")), 0.0), con_can)
		if lay > 0.004:
			ra.append((p["name"], round(lay, 2)))
			con_can -= lay
	return round(sum(t for _p, t in ra), 2), ra


def loi_bo_tra_truoc(ke, pe, do=2):
	"""So một phiếu chi trả trước với kế hoạch. Trả danh sách lỗi. THUẦN.

	ke: {"tien", "supplier", "nguon_chi"}. pe: dòng đọc từ
	_but_toan_cua_ho_so (có "tham_chieu"). Sau khi đã phân bổ vào tờ hoá đơn
	thì phiếu có thêm dòng tham chiếu tờ mua: hợp lệ, miễn tổng phân bổ cộng
	phần chưa phân bổ đúng bằng số đã chi."""
	loi = []
	ten = pe.get("name")
	if (pe.get("payment_type") or "") != "Pay":
		loi.append("%s không phải phiếu chi" % ten)
	if (pe.get("party_type") or "") != "Supplier" or pe.get("party") != ke.get("supplier"):
		loi.append("%s không trả đúng nhà cung cấp %s của hồ sơ" % (ten, ke.get("supplier")))
	if pe.get("paid_from") != ke.get("nguon_chi"):
		loi.append("%s chi từ %s, hồ sơ chi từ %s" % (ten, pe.get("paid_from"), ke.get("nguon_chi")))
	if any(pe.get(t) != "VND" for t in ("paid_from_account_currency", "paid_to_account_currency")) or any(
			_tien(pe.get(t)) != 1 for t in ("source_exchange_rate", "target_exchange_rate")):
		loi.append("%s chưa khớp tiền tệ VND và tỷ giá 1" % ten)
	if round(_tien(pe.get("paid_amount")), do) != round(_tien(ke.get("tien")), do):
		loi.append("%s chi %s đ, phần trả trước của hồ sơ là %s đ" % (ten, pe.get("paid_amount"), ke.get("tien")))
	pb = 0.0
	for r in pe.get("tham_chieu") or []:
		if r.get("reference_doctype") != "Purchase Invoice":
			loi.append("%s trỏ tới %s %s, không phải hoá đơn mua" % (ten, r.get("reference_doctype"), r.get("reference_name")))
		pb += _tien(r.get("allocated_amount"))
	if round(pb + _tien(pe.get("unallocated_amount")), do) != round(_tien(pe.get("paid_amount")), do):
		loi.append("%s: đã phân bổ %s đ cộng chưa phân bổ %s đ không bằng số đã chi"
			% (ten, round(pb, 2), pe.get("unallocated_amount")))
	return loi


# --------------------------------------------------------------- CHẠM HỆ
import frappe  # noqa: E402
from frappe.utils import flt  # noqa: E402


def tk_ngan_hang(doc):
	return frappe.db.get_value("Bank Account", doc.get("tk_chi"), "account") if doc.get("tk_chi") else ""


TT_CHUA_CHI = ("Nhap", "Cho ke toan", "Cho giam doc", "Da duyet")


def dong_dict(doc):
	return [{"cho_hoa_don": d.get("cho_hoa_don"), "so_tien": d.get("so_tien"), "tk_co": d.get("tk_co"),
		"tra_truoc": d.get("tra_truoc")} for d in (doc.get("dong") or [])]


def tach(doc):
	return tach_dong(dong_dict(doc), doc.get("nha_cung_cap"), tk_ngan_hang(doc),
		da_chi=(doc.get("trang_thai") or "") not in TT_CHUA_CHI)


def tao_phieu(doc, tien, ngay, phuong_thuc):
	"""Phiếu chi trả trước NCC (Payment Entry Pay, chưa phân bổ): Nợ 331 / Có
	ngân hàng. Không commit: cùng giao dịch với lần ghi nhận hồ sơ."""
	from vagabond.chung_tu_tien import dat_dien_giai
	from vagabond.ho_so_tt import _cong_ty_chung_tu
	from vagabond.tra_tien_app import chep_unc, loi_khong_ro_tk, tk_tien_chi
	from vagabond import ncc as _ncc
	cty = _cong_ty_chung_tu()
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.company = cty
	pe.posting_date = ngay
	pe.party_type = "Supplier"
	pe.party = doc.nha_cung_cap
	pe.party_bank_account = _ncc.tk_mac_dinh(doc.nha_cung_cap) or None
	pe.paid_amount = flt(tien)
	pe.received_amount = flt(tien)
	pe.reference_no = doc.get("ma_giao_dich") or doc.name
	pe.reference_date = ngay
	pe.vgb_ho_so_tt = doc.name
	dat_dien_giai(pe, "Trả trước nhà cung cấp %s theo hồ sơ %s, hoá đơn về sau. Số tiền %s đ. "
		"Khi hoá đơn về, máy phân bổ phiếu này vào tờ hoá đơn mua.%s" % (
			doc.get("ten_ncc") or doc.nha_cung_cap, doc.name, "{:,.0f}".format(flt(tien)),
			(" Ghi chú: %s" % doc.ghi_chu) if doc.get("ghi_chu") else ""))
	if phuong_thuc and frappe.db.exists("Mode of Payment", phuong_thuc):
		pe.mode_of_payment = phuong_thuc
	tk_nh, ba = tk_tien_chi(cty, phuong_thuc, doc.get("tk_chi"))
	if not tk_nh:
		frappe.throw(loi_khong_ro_tk(cty))
	pe.paid_from = tk_nh
	if ba:
		pe.bank_account = ba
	pe.setup_party_account_field()
	pe.set_missing_values()
	if not flt(pe.source_exchange_rate):
		pe.source_exchange_rate = 1
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)
	chep_unc(doc.name, "Payment Entry", pe.name)
	pe.submit()
	return pe.name


def phieu_con(ho_so, khoa=False):
	"""Phiếu chi trả trước của hồ sơ, kèm phần còn chưa phân bổ, cũ trước."""
	ds = frappe.db.sql(
		"""select name, party, unallocated_amount as con, paid_amount from `tabPayment Entry`
		where vgb_ho_so_tt = %s and docstatus = 1 and payment_type = 'Pay' and party_type = 'Supplier'
		order by posting_date, name""" + (" for update" if khoa else ""), (ho_so,), as_dict=True)
	return [dict(r) for r in ds]


def co_tra_truoc(ho_so, khoa=False):
	"""Hồ sơ này đã chi theo đường trả trước (v551) chưa."""
	return bool(phieu_con(ho_so, khoa=khoa))


def phan_bo(pe_name, hoa_don, tien):
	"""Phân bổ `tien` của phiếu chi trả trước vào tờ hoá đơn mua, qua bộ đối
	chiếu thanh toán lõi (cùng đường cấn cọc v548, coc_app.can_coc)."""
	from vagabond.coc_app import _doi_chieu
	pe = frappe.get_doc("Payment Entry", pe_name)
	hd = frappe.get_doc("Purchase Invoice", hoa_don)
	if hd.supplier != pe.party or hd.company != pe.company or hd.credit_to != pe.paid_to:
		frappe.throw("Hoá đơn %s không cùng nhà cung cấp, công ty hoặc tài khoản công nợ với phiếu chi %s."
			% (hoa_don, pe_name), title="Chưa phân bổ được")
	rec, payments = _doi_chieu(pe)
	con = sum(flt(p.get("amount")) for p in payments)
	if flt(tien, 2) > flt(con, 2) + 0.004:
		frappe.throw("Phiếu chi %s chỉ còn %s đ chưa phân bổ, không đủ %s đ cho hoá đơn %s."
			% (pe_name, "{:,.0f}".format(con), "{:,.0f}".format(flt(tien)), hoa_don), title="Chưa phân bổ được")
	match = [i.as_dict() for i in rec.invoices
		if i.invoice_type == "Purchase Invoice" and i.invoice_number == hoa_don]
	if len(match) != 1:
		frappe.throw("Không tìm được công nợ còn lại của hoá đơn %s để phân bổ." % hoa_don, title="Chưa phân bổ được")
	if flt(tien, 2) > flt(match[0].get("outstanding_amount"), 2) + 0.004:
		frappe.throw("Hoá đơn %s chỉ còn nợ %s đ." % (hoa_don, "{:,.0f}".format(flt(match[0].get("outstanding_amount")))),
			title="Chưa phân bổ được")
	match[0]["outstanding_amount"] = flt(tien, 2)
	rec.allocate_entries({"payments": payments, "invoices": match})
	cu = frappe.flags.mute_messages
	frappe.flags.mute_messages = True
	try:
		rec.reconcile()
	finally:
		frappe.flags.mute_messages = cu
	return flt(tien, 2)


def go_phan_bo(pe_name, hoa_don):
	"""Gỡ phần phân bổ của phiếu chi vào đúng một tờ (Unreconcile Payment lõi,
	giữ lịch sử). Phiếu chi trở lại phần trả trước chưa phân bổ."""
	pe = frappe.get_doc("Payment Entry", pe_name)
	u = frappe.new_doc("Unreconcile Payment")
	u.company, u.voucher_type, u.voucher_no = pe.company, "Payment Entry", pe.name
	u.add_references()
	giu = [r for r in u.allocations if r.reference_doctype == "Purchase Invoice" and r.reference_name == hoa_don]
	if not giu:
		return None
	u.set("allocations", giu)
	u.flags.ignore_permissions = True
	u.insert(ignore_permissions=True)
	u.submit()
	return u.name


def khi_ghi_so_hd(doc, method=None):
	"""on_submit Hoá đơn mua: tờ đang nối làm hoá đơn đến sau của hồ sơ đã
	chi theo đường trả trước thì tự phân bổ phiếu chi vào tờ, kế toán không
	phải làm thêm bước nào."""
	from vagabond.ho_so_bo_sung import ho_so_dang_giu
	ho_so = ho_so_dang_giu(doc.name, khoa=True, chi_tkct=True)
	if not ho_so:
		return
	phieu = phieu_con(ho_so, khoa=True)
	if not phieu:
		return
	can = flt(frappe.db.get_value("Purchase Invoice", doc.name, "outstanding_amount"))
	_tong, chia = chia_phan_bo(phieu, can, doc.supplier)
	da = []
	for pe, tien in chia:
		phan_bo(pe, doc.name, tien)
		da.append((pe, tien))
	tong = round(sum(t for _p, t in da), 2)
	for r in frappe.get_all("Vagabond Ho So TT HD Sau", filters={"parent": ho_so, "hoa_don": doc.name},
			fields=["name"], limit_page_length=0):
		frappe.db.set_value("Vagabond Ho So TT HD Sau", r.name, {
			"da_ghi_so": 1, "bu_tru": tong, "phieu_chi": da[0][0] if da else ""}, update_modified=False)
	con_no = can - tong
	frappe.get_doc("Vagabond Ho So TT", ho_so).add_comment("Comment", (
		"Hoá đơn %s (số %s) đã ghi sổ: máy phân bổ %s đ từ phiếu chi trả trước %s vào tờ này."
		% (doc.name, doc.get("bill_no") or "", "{:,.0f}".format(tong), ", ".join(p for p, _t in da)))
		+ (" Tờ còn nợ %s đ vì phần trả trước của hồ sơ không đủ." % "{:,.0f}".format(con_no) if con_no > 0.5 else ""))
