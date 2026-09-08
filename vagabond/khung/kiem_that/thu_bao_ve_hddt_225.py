"""#225: SI mới thử có dấu CQT không bị cancel hoặc huỷ mềm; không gọi M-Invoice."""
import frappe
from vagabond.khung.kiem_that.nen import ca, la
from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don, _gl


@ca("#225: SI đã ghi sổ có dấu CQT giả lập, cancel thật bị chặn trước đảo GL")
def _chan():
	hd = _hoa_don()
	hd.submit()
	# Chỉ dấu giả trên SI mới trong runner savepoint; không phát hành thử.
	frappe.db.set_value("Sales Invoice", hd.name, {
		"custom_hddt_so": "THU225", "custom_hddt_trang_thai": "CQT chấp nhận"})
	hd.reload()
	truoc = _gl(hd)
	# Payload cố xoá số và trạng thái vẫn phải đọc được dấu trong DB.
	hd.custom_hddt_so = ""
	hd.custom_hddt_trang_thai = ""
	try:
		hd.cancel()
	except frappe.ValidationError as loi:
		if "Không huỷ chứng từ gốc" not in str(loi):
			raise
	else:
		raise AssertionError("Đã huỷ SI còn dấu CQT")
	hd.reload()
	la("SI còn ghi sổ", hd.docstatus, 1)
	la("số HĐĐT giữ nguyên", hd.custom_hddt_so, "THU225")
	la("không đảo GL", _gl(hd), truoc)


@ca("#225: huỷ mềm SI nháp có dấu HĐĐT bị chặn trước db.set_value")
def _mem():
	from vagabond.chung_tu import danh_dau_huy
	hd = _hoa_don(False)
	frappe.db.set_value("Sales Invoice", hd.name, "custom_minvoice_id", "THU225")
	try:
		danh_dau_huy(hd, "Ca thử225")
	except frappe.ValidationError as loi:
		if "Không huỷ chứng từ gốc" not in str(loi):
			raise
	else:
		raise AssertionError("Đã huỷ mềm SI có ID")
	hd.reload()
	la("không bị đánh dấu huỷ", bool(hd.get("vgb_huy")), False)


def _cap_cu():
	"""Dựng SI/GL kiểu cũ bằng factory, không đọc hay sửa mã00710/00012 thật."""
	from unittest.mock import patch
	from vagabond.khung.kiem_that import nen
	hd = _hoa_don(False)
	hd.items[0].rate = 10420000
	hd.save()
	tk = {}
	for so_tk in ("131", "5111", "64181", "64182", "33311", "6428"):
		tk[so_tk] = frappe.db.get_value("Account", {"company": hd.company,
			"account_number": so_tk, "is_group": 0, "disabled": 0}, "name")
		if not tk[so_tk]:
			frappe.throw("Fixture225 cần tài khoản%s" % so_tk)
	hd.debit_to = tk["131"]
	def gl_cu(self, inventory_account_map=None):
		ds = []
		for ma, no, co in (("131",10420000,0),("5111",0,9648148.14),
			("33311",0,771851.85),("6428",0,0.01)):
			d = {"account": tk[ma], "debit": no, "credit": co,
				"debit_in_account_currency": no, "credit_in_account_currency": co,
				"debit_in_transaction_currency": no, "credit_in_transaction_currency": co,
				"cost_center": self.cost_center}
			if ma == "131":
				d.update(party_type="Customer", party=self.customer,
					against_voucher_type="Sales Invoice", against_voucher=self.name)
			ds.append(self.get_gl_dict(d, "VND"))
		return ds
	# Chỉ factory GL lịch sử; việc ghi GL/PLE và tất cả thao tác sửa dùng lõi thật.
	with patch.object(type(hd), "get_gl_entries", gl_cu):
		hd.submit()
	je = frappe.new_doc("Journal Entry")
	je.company, je.posting_date = hd.company, hd.posting_date
	je.voucher_type = "Journal Entry"
	je.append("accounts", {"account": tk["64181"], "debit_in_account_currency": 10420000,
		"cost_center": hd.cost_center})
	je.append("accounts", {"account": tk["131"], "credit_in_account_currency": 10420000,
		"party_type": "Customer", "party": hd.customer,
		"reference_type": "Sales Invoice", "reference_name": hd.name})
	je.insert()
	nen._DA_TAO.append((je.doctype, je.name))
	je.submit()
	u = frappe.new_doc("Unreconcile Payment")
	u.company, u.voucher_type, u.voucher_no = hd.company, "Journal Entry", je.name
	u.add_references()
	u.insert()
	nen._DA_TAO.append((u.doctype, u.name))
	u.submit()
	frappe.db.set_value("Sales Invoice", hd.name, {"vgb_but_toan_tang": je.name,
		"vgb_pt_thanh_toan": "Hàng tặng", "vgb_tang_so_cai": 0,
		"custom_hddt_so": "THU225", "custom_hddt_trang_thai": "CQT chấp nhận"})
	return hd.name, je.name, u.name


@ca("#225: thay PKT thật sau Unreconcile, GL đúng số lẻ, SI/CQT giữ nguyên, PLE tất toán")
def _thay_that():
	from vagabond import doi_chieu_tang_cu as sua
	from vagabond.khung.kiem_that import nen
	hd, je, ur = _cap_cu()
	anh = sua._ban_xem(hd, je)
	kq = sua._thay(hd, je, "THU225", anh["ma_xac_nhan"])
	nen._DA_TAO.append(("Journal Entry", kq["pkt_moi"]))
	la("Unreconcile vẫn giữ lịch sử", frappe.db.get_value("Unreconcile Payment", ur, "docstatus"), 1)
	la("PKT cũ huỷ", frappe.db.get_value("Journal Entry", je, "docstatus"), 2)
	la("HDB nối mới", frappe.db.get_value("Sales Invoice", hd, "vgb_but_toan_tang"), kq["pkt_moi"])
	la("đúng một PKT năm dòng", len(frappe.get_doc("Journal Entry", kq["pkt_moi"]).accounts), 5)
	la("amended_from", frappe.db.get_value("Journal Entry", kq["pkt_moi"], "amended_from"), je)
	la("hết nợ", kq["con_no"], 0)
	try:
		sua._thay(hd, je, "THU225", anh["ma_xac_nhan"])
	except frappe.ValidationError as loi:
		if "không còn ghi sổ" not in str(loi):
			raise
	else:
		raise AssertionError("Retry không được sinh bù")


@ca("#225: lỗi sau huỷ PKT phải rollback cả Link, PKT, GL và công nợ")
def _rollback():
	from unittest.mock import patch
	from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry
	from vagabond import doi_chieu_tang_cu as sua
	hd, je, ur = _cap_cu()
	anh = sua._ban_xem(hd, je)
	def hong(*a, **k):
		raise RuntimeError("THU225 lỗi sau cancel")
	with patch.object(JournalEntry, "insert", hong):
		try:
			sua._thay(hd, je, "THU225", anh["ma_xac_nhan"])
		except RuntimeError as loi:
			if "THU225" not in str(loi):
				raise
		else:
			raise AssertionError("Fixture phải tới lỗi sau cancel")
	la("ảnh dữ liệu giữ nguyên", sua._ban_xem(hd, je), anh)
	la("Unreconcile giữ nguyên", frappe.db.get_value("Unreconcile Payment", ur, "docstatus"), 1)
