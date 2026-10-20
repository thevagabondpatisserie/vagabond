"""v607 (Codex #493 P2): số dư khách trả trước trên sổ cái thật.

Dựng phiếu nạp THẬT qua đúng cửa của app (`tao_phieu_nap`, `ghi_so_phieu_nap`):
một Payment Entry tiền mặt và một Journal Entry Giám đốc thu hộ. Rồi ghi sổ
hoá đơn bán trả bằng số dư, để chính ERPNext chạy `set`/`validate` bảng
advances và `update_against_document_in_jv`. Đọc lại sổ cái, Payment Ledger,
outstanding, rồi huỷ một hoá đơn xem số dư có trả lại không.

Chạy trong điểm lưu của nen.py, commit bị khoá, không gửi gì ra ngoài.
"""

import frappe
from frappe.utils import flt, today

from vagabond import tra_truoc_khach as tk
from vagabond.khung.kiem_that.nen import _DA_TAO, _mot, ca, cong_ty, dung, khong_nem, la, mot_kho

# PNG 1x1 hợp lệ, đủ để tệp đính kèm qua được kiểm của File.
PNG = ("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
	"+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
ANH = '[{"ten": "ck-607.png", "noi_dung": "%s"}]' % PNG


def _nen():
	cty = cong_ty()
	tien = _mot("Account", {"company": cty, "account_type": "Cash", "is_group": 0, "disabled": 0})
	mon = _mot("Item", {"is_sales_item": 1, "is_stock_item": 0, "disabled": 0, "is_fixed_asset": 0})
	if not (tien and mon):
		frappe.throw("Cần một tài khoản tiền mặt và một món bán không theo tồn để dựng ca v607.")
	# Tiền mặt phải có tài khoản cho công ty thì tk_tien_thu mới trả ra được.
	if not frappe.db.get_value("Mode of Payment Account", {"parent": "Tiền mặt", "company": cty}, "default_account"):
		if not frappe.db.exists("Mode of Payment", "Tiền mặt"):
			m = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Tiền mặt", "type": "Cash"})
			m.insert(ignore_permissions=True)
			_DA_TAO.append((m.doctype, m.name))
		m = frappe.get_doc("Mode of Payment", "Tiền mặt")
		m.append("accounts", {"company": cty, "default_account": tien})
		m.save(ignore_permissions=True)
	if not frappe.db.exists("Mode of Payment", tk.PT_SO_DU):
		m = frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": tk.PT_SO_DU, "type": "General"})
		m.insert(ignore_permissions=True)
		_DA_TAO.append((m.doctype, m.name))
	frappe.db.set_single_value("Vagabond Settings", "tk_gd_thu_ho", tien)
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	kh = frappe.get_doc({
		"doctype": "Customer", "customer_name": "Khách trả trước 607 " + frappe.generate_hash(length=6),
		"customer_type": "Individual",
		"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
		"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
	})
	kh.insert(ignore_permissions=True)
	_DA_TAO.append((kh.doctype, kh.name))
	return cty, tien, mon, kh.name


def _don(cty, mon, khach, tien_don, dong=None):
	hd = frappe.new_doc("Sales Invoice")
	hd.company = cty
	hd.customer = khach
	hd.posting_date = today()
	hd.due_date = today()
	hd.currency = "VND"
	hd.conversion_rate = 1
	hd.update_stock = 0
	hd.ignore_pricing_rule = 1
	hd.set("taxes", [])
	hd.taxes_and_charges = None
	# Bench không có mẫu thuế mặc định; khai VAT đã gồm trong giá tường minh như
	# fixture #227 để tổng đơn đúng bằng giá món, không phụ thuộc cấu hình site.
	from vagabond.hang_tang_so_cai import tai_khoan
	hd.append("taxes", {"charge_type": "On Net Total", "account_head": tai_khoan(cty, "33311", "Liability"),
		"rate": 8, "description": "VAT ca kiểm 607", "included_in_print_rate": 1})
	hd.append("items", {"item_code": mon, "qty": 1, "rate": tien_don, "warehouse": mot_kho(cty)})
	# Như app: có bảng tách thì ô chính là dòng lớn nhất (ap_dung, thanh_toan_nhieu.luu).
	hd.vgb_pt_thanh_toan = max(dong, key=lambda d: d["so_tien"])["pt"] if dong else tk.PT_SO_DU
	for d in (dong or []):
		hd.append("vgb_thanh_toan_nhieu", d)
	hd.flags.ignore_permissions = True
	hd.insert(ignore_permissions=True)
	_DA_TAO.append((hd.doctype, hd.name))
	return hd


def _ma_lan():
	return "kiem-607-" + frappe.generate_hash(length=20).lower()


def _nap(khach, so_tien, nguon, quay="", ma_lan=None):
	ma_lan = ma_lan or _ma_lan()
	kq = tk.tao_phieu_nap(khach, so_tien, nguon, anh=ANH if nguon != "tien_mat" else "", quay=quay, ma_lan=ma_lan)
	_DA_TAO.append((kq["doctype"], kq["name"]))
	# Codex #493 vòng 3: gửi lại cùng mã lần (mất phản hồi) trả đúng phiếu cũ.
	lai = tk.tao_phieu_nap(khach, so_tien, nguon, anh=ANH if nguon != "tien_mat" else "", quay=quay, ma_lan=ma_lan)
	la("%s gửi lại cùng mã lần trả đúng phiếu cũ" % nguon, (lai["name"], lai.get("trung")), (kq["name"], 1))
	la("%s chỉ một phiếu cho mã lần" % nguon,
		frappe.db.count(kq["doctype"], {tk.O_MA_LAN: ma_lan, "docstatus": ["<", 2]}), 1)
	tk.ghi_so_phieu_nap(kq["doctype"], kq["name"])
	return frappe.get_doc(kq["doctype"], kq["name"])


@ca("v607 số dư trả trước: nạp PE và JE thật, hai đơn trừ dần, sổ cái và số dư đúng, huỷ trả lại")
def _tru_dan():
	cty, tien, mon, khach = _nen()
	pe = khong_nem("nạp tiền mặt tại quầy", lambda: _nap(khach, 500000, "tien_mat", "TCV"))
	je = khong_nem("nạp qua Giám đốc thu hộ", lambda: _nap(khach, 400000, "gd_thu_ho"))
	if not (pe and je):
		return
	la("phiếu thu mang cờ, chưa gắn hoá đơn", (pe.docstatus, pe.get(tk.CO), flt(pe.unallocated_amount)), (1, 1, 500000.0))
	la("phiếu thu đúng quầy", pe.get("vgb_quay"), "TCV")
	dung("phiếu GĐ thu hộ có ảnh", frappe.db.count("File", {"attached_to_doctype": "Journal Entry", "attached_to_name": je.name}) >= 1)
	gl_je = frappe.get_all("GL Entry", filters={"voucher_type": "Journal Entry", "voucher_no": je.name, "is_cancelled": 0},
		fields=["account", "party_type", "party", "debit", "credit"])
	la("JE Nợ tài khoản GĐ thu hộ", sum(flt(g.debit) for g in gl_je if g.account == tien), 400000.0)
	la("JE Có phải thu đúng khách", sum(flt(g.credit) for g in gl_je if g.party == khach), 400000.0)
	s = tk.so_du_khach(khach)
	la("số dư sau nạp", (s["da_nap"], s["con_chua_can"], s["kha_dung"]), (900000.0, 900000.0, 900000.0))

	hd1 = khong_nem("lưu đơn 1 trả bằng số dư", lambda: _don(cty, mon, khach, 300000))
	if not hd1:
		return
	la("giữ chỗ khi đơn còn nháp", tk.so_du_khach(khach)["giu_cho"], 300000.0)
	if khong_nem("ghi sổ đơn 1", lambda: hd1.submit()) is None and hd1.docstatus != 1:
		return
	hd1.reload()
	la("đơn 1 cấn đủ", (flt(hd1.total_advance), flt(hd1.outstanding_amount)), (300000.0, 0.0))
	dung("đơn 1 chỉ cấn phiếu mang cờ", all(a.reference_name in (pe.name, je.name) for a in hd1.advances))
	ple = frappe.get_all("Payment Ledger Entry", filters={"against_voucher_no": hd1.name, "delinked": 0},
		fields=["voucher_no", "amount"])
	la("sổ công nợ đơn 1 về 0", round(sum(flt(p.amount) for p in ple)), 0)

	# Thiếu số dư thì không lưu được.
	try:
		_don(cty, mon, khach, 700000)
	except frappe.ValidationError as e:
		dung("chặn đơn vượt số dư", "chỉ còn" in str(e))
	else:
		dung("phải chặn đơn vượt số dư", False)

	hd2 = khong_nem("lưu đơn 2 tách số dư và tiền mặt", lambda: _don(cty, mon, khach, 700000, [
		{"pt": tk.PT_SO_DU, "so_tien": 600000}, {"pt": "Tiền mặt", "so_tien": 100000}]))
	if not hd2:
		return
	if khong_nem("ghi sổ đơn 2", lambda: hd2.submit()) is None and hd2.docstatus != 1:
		return
	hd2.reload()
	la("đơn 2 cấn đúng phần số dư", flt(hd2.total_advance), 600000.0)
	la("hết số dư", tk.so_du_khach(khach)["con_chua_can"], 0.0)
	cha = frappe.get_all("Payment Entry Reference", filters={"reference_name": hd2.name, "docstatus": 1}, pluck="parent")
	la("không sinh phiếu thu cho phần số dư",
		frappe.db.count("Payment Entry", {"name": ["in", cha or ["-"]], "mode_of_payment": tk.PT_SO_DU}), 0)

	# Huỷ đơn 1: ERPNext gỡ cấn, số dư trả lại.
	hd1.reload()
	hd1.flags.ignore_permissions = True
	if khong_nem("huỷ đơn 1", lambda: hd1.cancel()) is None and hd1.docstatus != 2:
		return
	la("số dư trả lại sau huỷ", tk.so_du_khach(khach)["con_chua_can"], 300000.0)

	# Codex #493 vòng 3: đơn đã tách số dư, người dùng chọn Tiền mặt cho cả
	# đơn rồi lưu (như Bill quầy pos_chot) thì bảng tách bị bỏ, không tự quay lại.
	hd3 = khong_nem("lưu đơn 3 tách số dư", lambda: _don(cty, mon, khach, 400000, [
		{"pt": tk.PT_SO_DU, "so_tien": 300000}, {"pt": "Tiền mặt", "so_tien": 100000}]))
	if not hd3:
		return
	hd3.reload()
	la("đơn 3 phương thức chính là dòng lớn nhất", hd3.vgb_pt_thanh_toan, tk.PT_SO_DU)
	tk.chon_pt_ca_don(hd3, "Tiền mặt")
	hd3.flags.ignore_permissions = True
	if khong_nem("đổi đơn 3 sang Tiền mặt", lambda: hd3.save(ignore_permissions=True)) is None:
		return
	hd3.reload()
	la("đơn 3 giữ Tiền mặt người chọn", hd3.vgb_pt_thanh_toan, "Tiền mặt")
	la("đơn 3 bỏ bảng tách", len(hd3.get("vgb_thanh_toan_nhieu") or []), 0)
	la("đơn 3 không còn giữ chỗ số dư", tk.so_du_khach(khach)["giu_cho"], 0.0)

	# Codex #493 vòng 4: số dư là phần NHỎ (ô chính đã là Tiền mặt), người dùng
	# chọn Tiền mặt cho cả đơn qua cửa chọn phương thức thì vẫn bỏ dòng số dư.
	hd4 = khong_nem("lưu đơn 4 tách số dư phần nhỏ", lambda: _don(cty, mon, khach, 400000, [
		{"pt": tk.PT_SO_DU, "so_tien": 100000}, {"pt": "Tiền mặt", "so_tien": 300000}]))
	if not hd4:
		return
	hd4.reload()
	la("đơn 4 ô chính đã là Tiền mặt", hd4.vgb_pt_thanh_toan, "Tiền mặt")
	tk.chon_pt_ca_don(hd4, "Tiền mặt")
	hd4.flags.ignore_permissions = True
	if khong_nem("chọn Tiền mặt cho cả đơn 4", lambda: hd4.save(ignore_permissions=True)) is None:
		return
	hd4.reload()
	la("đơn 4 bỏ bảng tách", len(hd4.get("vgb_thanh_toan_nhieu") or []), 0)
	la("đơn 4 không giữ chỗ số dư", tk.so_du_khach(khach)["giu_cho"], 0.0)
