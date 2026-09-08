"""#225: đối chiếu trước khi sửa PKT hàng tặng cũ, không huỷ HĐĐT.

Chị Dung đã chốt một PKT năm dòng gồm số lẻ0,14/0,15/0,01. Không làm
tròn sổ cũ hoặc huỷ kèm SI để tháo liên kết. Bản xem chỉ đọc; hàm thay
đòi mã xác nhận ảnh hiện tại và kiểm lại GL/PLE, không hỏi duyệt lại số lẻ.
"""
from decimal import Decimal


def so(v):
	n = Decimal(str(v if v is not None else 0))
	if not n.is_finite():
		raise ValueError("Số tiền không hữu hạn")
	return n


def sau_thay_pkt(gl_hd, dong_moi):
	"""Nợ dương, Có âm; đây là SI cộng PKT MỚI sau khi PKT cũ đã đảo đủ.

	Không gộp theo tên tài khoản đoán từ tiền tố, không ép về đồng làm mất
	chênh lệch cần chị Dung quyết. Nhóm theo đúng mã số danh mục được đọc.
	"""
	ra = {}
	for d in list(gl_hd) + list(dong_moi):
		tk = d["account_number"]
		if not tk:
			raise ValueError("Tài khoản chưa có mã số, kế toán đối chiếu danh mục")
		ra[tk] = ra.get(tk, Decimal(0)) + so(d.get("debit")) - so(d.get("credit"))
	return {tk: str(n) for tk, n in sorted(ra.items()) if n}


def _xem(hoa_don, pkt):
	"""Chỉ đọc bằng bench execute; không mở API và không trả lệnh tự submit.

	JournalEntry.validate_reference_doc kiểm Customer/debit_to và tổng phân
	bổ của dòng Có131. Tên HDB trong user_remark không tạo liên kết công nợ.
	Frappe.check_no_back_links_exist còn kiểm Link SI; Unreconcile được
	core JournalEntry.on_cancel giữ làm lịch sử; không dùng ignore_links hoặc huỷ dây chuyền để vượt qua.
	"""
	import frappe
	from vagabond.minvoice_an_toan import la_hang_tang
	if not ({"System Manager", "Accounts Manager", "Accounts User"} & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán hoặc quản trị được đối chiếu bút toán hàng tặng.", frappe.PermissionError)
	hd = frappe.get_doc("Sales Invoice", hoa_don)
	je = frappe.get_doc("Journal Entry", pkt)
	hd.check_permission("read")
	je.check_permission("read")
	if (hd.docstatus != 1 or je.docstatus != 1 or not la_hang_tang(hd)
		or hd.company != je.company or hd.currency != "VND"
		or hd.get("vgb_tang_so_cai") or hd.get("vgb_but_toan_tang") != je.name):
		frappe.throw("Cặp phiếu không còn đúng luồng hàng tặng cũ đã ghi sổ. Đọc lại trước khi lập phương án.")
	def doc_gl(dt, ten):
		return frappe.get_all("GL Entry", filters={"voucher_type": dt, "voucher_no": ten,
			"is_cancelled": 0}, fields=["account", "debit", "credit", "party_type", "party",
			"against_voucher_type", "against_voucher"], order_by="name asc", limit_page_length=0)
	gl_hd, gl_pkt = doc_gl("Sales Invoice", hd.name), doc_gl("Journal Entry", je.name)
	if not gl_hd or not gl_pkt:
		frappe.throw("Thiếu sổ cái đang hiệu lực; không suy chứng từ đã được sửa.")
	for d in gl_hd + gl_pkt:
		d["account_number"] = frappe.db.get_value("Account", d["account"], "account_number")
	moi = [{"account_number": tk, "debit": no, "credit": co}
		for tk, no, co in dong_pkt_sua()]
	for d in moi:
		if d["account_number"] == "131":
			d.update(party_type="Customer", party=hd.customer,
				reference_type="Sales Invoice", reference_name=hd.name)

	# Đây là chốt cho đúng cặp 00710/00012, tuyệt đối không nhân số này cho 4 tờ khác.
	if so(hd.grand_total) != so(10420000):
		frappe.throw("Phương án số tiền chỉ được chốt cho HDB-26-09-00710 / PKT-2026-00012.")
	ple = frappe.get_all("Payment Ledger Entry", filters={"company": hd.company,
		"delinked": 0}, or_filters={"voucher_no": ["in", [hd.name, je.name]],
		"against_voucher_no": ["in", [hd.name, je.name]]}, fields=[
		"voucher_type", "voucher_no", "against_voucher_type", "against_voucher_no",
		"account", "party_type", "party", "amount", "amount_in_account_currency"], order_by="name asc", limit_page_length=0)
	return {
		"chi_doc": True, "hoa_don": hd.name, "pkt_cu": je.name,
		"modified": {hd.name: str(hd.modified), je.name: str(je.modified)},
		"so_hddt": hd.get("custom_hddt_so"), "con_no": hd.outstanding_amount,
		"gl_hoa_don": gl_hd, "gl_pkt": gl_pkt, "payment_ledger": ple,
		"tham_chieu_pkt": [{"account": d.account, "reference_type": d.reference_type,
			"reference_name": d.reference_name} for d in je.accounts],
		"pkt_moi_chi_dung_chot": moi,
		"so_du_sau_khi_dao_du_pkt_cu_va_ghi_pkt_moi": sau_thay_pkt(gl_hd, moi),
		"dong_kho": frappe.db.count("Stock Ledger Entry", {"voucher_type": "Sales Invoice",
			"voucher_no": hd.name, "is_cancelled": 0}),
		"chua_duoc_tu_ghi": [
			"Chưa đảo PKT cũ; không ghi thêm PKT mới khi chưa xử lý đủ phiếu cũ và Payment Ledger.",
			"Năm dòng gồm số lẻ đã được chị Dung chốt; giữ nguyên SI đã phát hành, chỉ thay PKT.",
			"Kiểm liên kết SI và Unreconcile Payment trước huỷ; không huỷ kèm SI hoặc bỏ kiểm liên kết.",
			"Không đổi ngày/hạn, tạo giá vốn hoặc tự sửa bốn hoá đơn còn lại.",
		],
	}


def dong_pkt_sua():
	"""Chị Dung chốt một PKT năm dòng, gộp số lẻ vào cùng dòng5111.

	Tổng Nợ/Có10420000,15. Gộp với SI: chỉ còn Nợ64182/Có33311 771852.
	Không đổi precision toàn hệ để tránh nuốt các khoản0,01/0,15 này.
	"""
	return [
		("5111", "9648148.14", "0"), ("64182", "771852", "0"),
		("6428", "0.01", "0"), ("131", "0", "10420000"), ("33311", "0", "0.15"),
	]


def _ban_xem(hoa_don, pkt):
	"""Chụp lại dữ liệu và mã xác nhận; chưa có thao tác ghi nào."""
	import hashlib
	import json
	ra = _xem(hoa_don, pkt)
	ra["phuong_an_da_chot"] = "Chị Dung: một PKT năm dòng, gộp số lẻ; tổng10420000,15"
	ra["ma_xac_nhan"] = hashlib.sha256(json.dumps(ra, sort_keys=True, default=str,
		ensure_ascii=False).encode()).hexdigest()
	return ra


def _thay(hoa_don, pkt, so_hddt, ma_xac_nhan):
	"""Chỉ cho Claude chạy sau review/bench; năm dòng đã được chị Dung chốt; không có whitelist.

	Không commit. Caller quản lý giao dịch; mọi lỗi rollback về savepoint.
	Core de59166 JournalEntry.on_cancel giữ Unreconcile Payment trong danh
	sách ignore_linked_doctypes. Không huỷ chứng từ đó, không tự thêm bypass.
	Frappe Document gọi on_cancel trước kiểm backlink nên chỉ phải tháo Link
	SI do Vagabond tạo; giữ vết qua amended_from, user_remark và Comment.
	"""
	import frappe
	from frappe.utils import nowdate

	if not isinstance(ma_xac_nhan, str) or len(ma_xac_nhan) != 64:
		frappe.throw("Chạy ban_xem rồi dùng đúng mã xác nhận của bản kế toán đã duyệt.")
	if not ({"System Manager", "Accounts Manager"} & set(frappe.get_roles())):
		frappe.throw("Chỉ quản trị hoặc kế toán trưởng được thay PKT cũ.", frappe.PermissionError)
	moc = "sua_tang_225"
	frappe.db.savepoint(moc)
	try:
		hd = frappe.get_doc("Sales Invoice", hoa_don, for_update=True)
		cu = frappe.get_doc("Journal Entry", pkt, for_update=True)
		hd.check_permission("write")
		cu.check_permission("cancel")
		# Retry dừng, không sinh bù hoặc tin một phiếu cùng tổng là cùng bộ.
		if cu.docstatus != 1:
			frappe.throw("PKT cũ không còn ghi sổ. Kiểm phiếu thay thế và công nợ; không chạy lại hoặc sinh bù.")
		anh = _ban_xem(hoa_don, pkt)
		if anh["ma_xac_nhan"] != ma_xac_nhan:
			frappe.throw("Dữ liệu đã đổi từ bản xem trước. Chạy ban_xem và đối chiếu lại, chưa sửa phiếu.")
		if hd.get("custom_hddt_so") != so_hddt or so(hd.outstanding_amount) != so(10420000):
			frappe.throw("Số HĐĐT hoặc công nợ đã khác bằng chứng được duyệt.")
		ky_vong = {"131": "10420000", "5111": "-9648148.14", "33311": "-771851.85", "6428": "-0.01"}
		def bang(ds):
			return {k: so(v) for k, v in sau_thay_pkt(ds, []).items()}
		if bang(anh["gl_hoa_don"]) != {k: so(v) for k, v in ky_vong.items()}:
			frappe.throw("GL hoá đơn khác bản được duyệt, không áp số cố định.")
		if bang(anh["gl_pkt"]) != {"64181": so(10420000), "131": so(-10420000)}:
			frappe.throw("GL PKT khác bản được duyệt.")
		if len(cu.accounts) != 2 or any(d.reference_type or d.reference_name for d in cu.accounts):
			frappe.throw("PKT đã có phân bổ khác hoặc không còn đúng hai dòng, phải đối chiếu lại.")
		for d in cu.accounts:
			if d.account == hd.debit_to and (d.party_type != "Customer" or d.party != hd.customer):
				frappe.throw("Khách trên PKT không khớp hoá đơn.")
		if anh["dong_kho"]:
			frappe.throw("Hoá đơn đã có sổ kho, cần đối chiếu giá vốn riêng trước khi sửa.")
		ple = anh["payment_ledger"]
		if any((d.voucher_type, d.voucher_no, d.against_voucher_type, d.against_voucher_no)
			not in (("Sales Invoice", hd.name, "Sales Invoice", hd.name),
				("Journal Entry", cu.name, "Journal Entry", cu.name))
			or d.account != hd.debit_to or d.party_type != "Customer" or d.party != hd.customer
			for d in ple):
			frappe.throw("Có phân bổ khác ngoài hai khoản chưa đối trừ; không tự gỡ phân bổ.")
		for ten, tien in ((hd.name, 10420000), (cu.name, -10420000)):
			if sum((so(d.amount_in_account_currency) for d in ple if d.voucher_no == ten), so(0)) != so(tien):
				frappe.throw("Payment Ledger không còn đúng hai khoản chưa đối trừ đã duyệt.")
		moi = frappe.new_doc("Journal Entry")
		moi.company = hd.company
		# Ngày xử lý hiện tại; core giữ nguyên kiểm kỳ/khoá sổ.
		moi.posting_date = nowdate()
		moi.voucher_type = "Journal Entry"
		moi.amended_from = cu.name
		moi.user_remark = "#225 thay %s cho %s, giữ HĐĐT12165. VAT64182; một PKT năm dòng đã được chị Dung duyệt." % (cu.name, hd.name)
		for tk, no, co in dong_pkt_sua():
			ds = frappe.get_all("Account", filters={"company": hd.company, "account_number": tk,
				"is_group": 0, "disabled": 0}, fields=["name", "account_currency"], limit=2)
			if len(ds) != 1 or ds[0].account_currency != "VND":
				frappe.throw("Cần đúng một tài khoản%s VND của công ty." % tk)
			dong = {"account": ds[0].name, "debit_in_account_currency": float(no),
				"credit_in_account_currency": float(co), "exchange_rate": 1,
				"cost_center": hd.cost_center or frappe.get_cached_value("Company", hd.company, "cost_center")}
			if tk == "131":
				if ds[0].name != hd.debit_to:
					frappe.throw("Tài khoản131 không khớp debit_to của hoá đơn.")
				dong.update(party_type="Customer", party=hd.customer,
					reference_type="Sales Invoice", reference_name=hd.name)
			moi.append("accounts", dong)
		moi.check_permission("create")
		moi.check_permission("submit")
		# Một giao dịch: gỡ đúng Link nội bộ, core huỷ PKT, lập phiếu thay thế,
		# nối lại. Không đụng mã/số/trạng thái/tiền của SI hoặc Unreconcile.
		hd.db_set("vgb_but_toan_tang", None)
		cu.cancel()
		moi.insert()
		moi.submit()
		hd.db_set("vgb_but_toan_tang", moi.name)
		hd.reload()
		if so(hd.outstanding_amount) != 0 or hd.docstatus != 1 or hd.get("custom_hddt_so") != so_hddt:
			frappe.throw("Sau thay PKT công nợ/chứng từ gốc chưa đúng, quay lại toàn bộ.")
		def so_cai(dt, ten):
			ds = frappe.get_all("GL Entry", filters={"voucher_type": dt, "voucher_no": ten,
				"is_cancelled": 0}, fields=["account", "debit", "credit"], limit_page_length=0)
			for d in ds:
				d["account_number"] = frappe.db.get_value("Account", d.account, "account_number")
			return ds
		gl_moi = so_cai("Journal Entry", moi.name)
		ky_vong_moi = [{"account_number": tk, "debit": no, "credit": co} for tk, no, co in dong_pkt_sua()]
		if bang(gl_moi) != bang(ky_vong_moi) or bang(so_cai("Journal Entry", cu.name)):
			frappe.throw("GL thực của PKT mới/cũ không đúng, có thể do làm tròn số lẻ. Quay lại toàn bộ.")
		gl_hd = so_cai("Sales Invoice", hd.name)
		if bang(gl_hd) != {k: so(v) for k, v in ky_vong.items()} or bang(gl_hd + gl_moi) != {"64182": so(771852), "33311": so(-771852)}:
			frappe.throw("Sổ cái sau sửa chưa khớp VAT đã duyệt, quay lại toàn bộ.")
		hd.add_comment("Comment", "#225: thay %s bằng %s; Có131 trỏ đúng HDB. Giữ HĐĐT12165. Một PKT năm dòng đã được chị Dung duyệt." % (cu.name, moi.name))
		return {"hoa_don": hd.name, "pkt_cu": cu.name, "pkt_moi": moi.name,
			"con_no": hd.outstanding_amount, "chua_commit": True}
	except Exception:
		frappe.db.rollback(save_point=moc)
		raise


def xem():
	return _xem("HDB-26-09-00710", "PKT-2026-00012")


def ban_xem():
	return _ban_xem("HDB-26-09-00710", "PKT-2026-00012")


def thay(ma_xac_nhan):
	return _thay("HDB-26-09-00710", "PKT-2026-00012", "12165", ma_xac_nhan)


def kiem_nam_to():
	"""Đọc riêng năm tờ đã được Claude xác định, không nhân phương án00710."""
	import frappe
	if not ({"System Manager", "Accounts Manager", "Accounts User"} & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán hoặc quản trị được đối chiếu.", frappe.PermissionError)
	ra = []
	for ten in ("HDB-26-09-00171", "HDB-26-09-00710", "HDB-26-09-00372",
		"HDB-26-09-00170", "HDB-26-09-00504"):
		hd = frappe.get_doc("Sales Invoice", ten)
		hd.check_permission("read")
		pkt = hd.get("vgb_but_toan_tang")
		d = {"hoa_don": ten, "ngay": str(hd.posting_date), "trang_thai": hd.docstatus,
			"tong": hd.grand_total, "con_no": hd.outstanding_amount,
			"so_hddt": hd.get("custom_hddt_so"), "pkt": pkt,
			"luong_moi": hd.get("vgb_tang_so_cai"), "update_stock": hd.update_stock}
		d["gl"] = []
		for dt, ma in (("Sales Invoice", ten), ("Journal Entry", pkt)):
			if not ma:
				continue
			frappe.get_doc(dt, ma).check_permission("read")
			d["gl"].extend(frappe.get_all("GL Entry", filters={"voucher_type": dt,
				"voucher_no": ma, "is_cancelled": 0}, fields=["voucher_type", "voucher_no",
				"account", "debit", "credit", "party_type", "party"], order_by="name asc", limit_page_length=0))
		d["dong_kho"] = frappe.db.count("Stock Ledger Entry", {"voucher_type": "Sales Invoice", "voucher_no": ten, "is_cancelled": 0})
		ra.append(d)
	return ra
