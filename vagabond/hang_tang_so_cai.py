"""#227: hàng tặng không phải doanh thu rồi cấn công nợ theo giá bán.

Anh Việt chốt 07/09/2026: xuất kho tại hoá đơn khi kho sản xuất sẵn sàng.
Hiện app dùng update_stock=0 và Kiểm bánh riêng; ghi VAT, để chờ giá vốn.
Dấu trên phiếu phân biệt cách ghi mới với hoá đơn cũ khi huỷ hoặc repost.
"""

# phần thuần
import math


def chia_thue(tong, dong, thue_suat):
	"""Cùng phép chia gross theo dòng với script M-Invoice đã chụp từ site."""
	tong, ts = float(tong or 0), float(thue_suat)
	gia = [float(d.get("amount") or 0) for d in dong]
	if not all(math.isfinite(x) for x in [tong, ts] + gia):
		raise ValueError("Số tiền không hợp lệ. Kiểm lại giá trên đơn tặng.")
	if tong <= 0 or tong != int(tong) or ts not in (0, 5, 8, 10) or not gia or min(gia) <= 0:
		raise ValueError("Đơn tặng cần giá dương bằng VND và thuế suất 0, 5, 8 hoặc 10%. Kiểm lại đơn và cấu hình M-Invoice.")
	con = int(tong)
	ra = []
	for i, g in enumerate(gia):
		sau = con if i == len(gia) - 1 else int(round(g * tong / sum(gia)))
		con -= sau
		truoc = round(sau / (1 + ts / 100))
		ra.append((truoc, sau - truoc, sau))
	return ra


def kiem_thue_gui(si, goi):
	"""Không để đổi cấu hình thuế sau ghi sổ làm VAT trên tờ khác sổ cái."""
	if not si.get("vgb_tang_so_cai"):
		return
	chia = chia_thue(si.get("grand_total"), si.get("items"), si.get("vgb_tang_thue_suat"))
	dong = [d for nhom in goi.get("details") or [] for d in nhom.get("data") or []]
	if (len(dong) != len(chia) or any(
		(float(d.get("inv_TotalAmountWithoutVat") or 0), float(d.get("inv_vatAmount") or 0), float(d.get("inv_TotalAmount") or 0)) != c
		or float(d.get("ma_thue", -1)) != float(si.get("vgb_tang_thue_suat"))
		for d, c in zip(dong, chia))
		or float(goi.get("inv_vatAmount") or 0) != float(si.get("vgb_tang_tien_thue"))
		or float(goi.get("inv_TotalAmount") or 0) != float(si.get("grand_total"))
		or float(goi.get("inv_TotalAmountWithoutVat") or 0) != sum(c[0] for c in chia)):
		raise ValueError("VAT gửi đi khác số đã ghi sổ của đơn tặng. Kế toán đối chiếu cấu hình thuế và từng dòng trước khi phát hành; không tự gửi lại.")


import frappe
from frappe.utils import cint, flt

TRUONG_MOI = {"Sales Invoice": [
	{"fieldname": ten, "label": nhan, "fieldtype": loai, "read_only": 1,
	 "no_copy": 1, "insert_after": "vgb_tang_duyet", **them}
	for ten, nhan, loai, them in (
		("vgb_tang_so_cai", "Hàng tặng ghi riêng VAT và giá vốn", "Check", {}),
		("vgb_tang_cho_gia_von", "Hàng tặng chờ giá vốn", "Check", {}),
		("vgb_tang_thue_suat", "Thuế suất hàng tặng khi ghi sổ", "Float", {}),
		("vgb_tang_tien_thue", "VAT hàng tặng khi ghi sổ", "Currency", {"options": "currency"}),
		("vgb_tang_tk_vat", "Chi phí VAT hàng tặng", "Link", {"options": "Account"}),
		("vgb_tang_tk_thue", "Thuế đầu ra hàng tặng", "Link", {"options": "Account"}),
	)
]}


def tai_khoan(cong_ty, so, goc):
	"""Không đoán tên hay tạo tài khoản. GLEntry kiểm công ty, tiền tệ, nhóm."""
	ds = frappe.get_all("Account", filters={"company": cong_ty, "account_number": so,
		"is_group": 0, "disabled": 0}, fields=["name", "root_type", "account_type", "account_currency"], limit=2)
	if (len(ds) != 1 or ds[0].root_type != goc or ds[0].account_currency != "VND"
		or ds[0].account_type in ("Receivable", "Payable")):
		frappe.throw("Kế toán kiểm tài khoản %s của %s: cần đúng một tài khoản chi tiết còn dùng, nhóm %s, tiền tệ VND." % (so, cong_ty, goc))
	return ds[0].name


def truoc_khi_ghi_so(doc, method=None):
	"""Document.run_before_save_methods chạy before_submit trước db_update.

	Không nhận dấu/các số tiền do client gửi. Cách ghi cũ không bị đổi bởi
	việc migrate; chỉ lần ghi sổ mới đi qua đây sau cửa duyệt hiện có.
	"""
	from vagabond.minvoice_an_toan import la_hang_tang
	for o in TRUONG_MOI["Sales Invoice"]:
		doc.set(o["fieldname"], None if o["fieldtype"] == "Link" else 0)
	if not la_hang_tang(doc):
		return
	if (doc.currency != "VND" or frappe.get_cached_value("Company", doc.company, "default_currency") != "VND"
		or flt(doc.conversion_rate) != 1):
		frappe.throw("Luồng hàng tặng này dùng VND. Kế toán kiểm tiền tệ trước khi ghi sổ.")
	if any(doc.get(o) for o in ("is_return", "is_debit_note", "is_pos", "is_internal_customer",
		"advances", "payments", "paid_amount", "write_off_amount", "redeem_loyalty_points", "vgb_huy")):
		frappe.throw("Đơn tặng không thu tiền không được kèm thu tiền, ứng trước hoặc trả hàng. Kế toán tách chứng từ phù hợp trước khi ghi sổ.")
	if doc.get("is_opening") == "Yes" or any(d.get("enable_deferred_revenue") for d in doc.items):
		frappe.throw("Đơn tặng không dùng mở sổ hoặc doanh thu chờ phân bổ. Kế toán tách chứng từ phù hợp trước khi ghi sổ.")
	if any(d.get("pt") != "Hàng tặng" and flt(d.get("so_tien")) for d in doc.get("vgb_thanh_toan_nhieu") or []):
		frappe.throw("Đơn tặng đang có dòng thu tiền. Sửa lại phương thức thanh toán trước khi ghi sổ.")
	if any(d.get("delivery_note") or d.get("is_fixed_asset") for d in doc.items):
		frappe.throw("Đơn tặng có phiếu giao hàng hoặc tài sản. Kế toán đối chiếu xuất kho trước khi ghi sổ để tránh ghi hai lần.")
	# Giá trên đơn hiện là gross; không cộng VAT lần thứ hai theo bảng thuế SI.
	ts = frappe.get_single("MInvoice Phat Hanh Settings").get("thue_suat")
	ts = flt(ts or 8)
	try:
		chia = chia_thue(doc.grand_total, doc.items, ts)
	except ValueError as loi:
		frappe.throw(str(loi))
	doc.cost_center = doc.cost_center or frappe.get_cached_value("Company", doc.company, "cost_center")
	if not doc.cost_center:
		frappe.throw("Kế toán chọn trung tâm chi phí trên đơn tặng hoặc đặt mặc định cho công ty trước khi ghi sổ.")
	doc.vgb_tang_tk_vat = tai_khoan(doc.company, "64182", "Expense")
	doc.vgb_tang_tk_thue = tai_khoan(doc.company, "33311", "Liability")
	doc.vgb_tang_thue_suat = ts
	doc.vgb_tang_tien_thue = sum(d[1] for d in chia)
	doc.vgb_tang_so_cai = 1
	doc.vgb_tang_cho_gia_von = 1
	# Chưa triển khai kho sản xuất: không tự bật xuất kho hoặc đoán giá vốn.
	# Cửa này dừng cả ghi sổ, nên không có phiếu ghi nửa VAT, nửa kho.
	if cint(doc.update_stock):
		frappe.throw("Kho sản xuất cho hàng tặng chưa được triển khai. Giữ đơn nháp để kế toán kiểm kho; luồng app hiện ghi VAT và chờ giá vốn, không cập nhật kho.")
	doc.outstanding_amount = 0
	# validate đã đặt Unpaid trước before_submit; tính lại bằng core sau khi gỡ nợ.
	doc.set_status()
	doc.dont_create_loyalty_points = 1

