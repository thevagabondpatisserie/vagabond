"""#227: một người mua, một đơn; chặn email lạc ở cửa ra M-Invoice.

Kịch bản trên site từng lấy kết quả tìm Pancake đầu tiên và gắn email
vào cả hoá đơn người tiêu dùng. Hàm thuần dùng chung cho Python và script
để dữ liệu cũ chưa phát hành cũng được kiểm ở cửa cuối.
"""

import copy
import re
import unicodedata

from vagabond import hoa_don_vat


def chuoi(gia_tri):
	return str(gia_tri or "").strip()


def ten_mac_dinh(ten):
	t = unicodedata.normalize("NFD", chuoi(ten).lower())
	t = "".join(c for c in t if unicodedata.category(c) != "Mn").replace("đ", "d")
	return t in ("", "ban cho nguoi tieu dung", "nguoi mua khong lay hoa don", "khach le")


def la_hang_tang(si):
	return chuoi(si.get("vgb_pt_thanh_toan")) == "Hàng tặng" or bool(si.get("vgb_phieu_qua"))


def da_gui(si):
	return bool(si.get("vgb_hddt_cho_doi_chieu")) or any(chuoi(si.get(o)) for o in (
		"custom_hddt_so", "custom_hddt_id", "custom_minvoice_id",
	)) or chuoi(si.get("custom_hddt_trang_thai")) in ("Chờ ký", "Đã ký", "Đã phát hành")


def nguoi_mua(si):
	"""Không bổ sung email từ danh mục khách hoặc kết quả tìm kiếm khác đơn."""
	ten = chuoi(si.get("vgb_xhd_ten"))
	mst = chuoi(si.get("vgb_xhd_mst"))
	if mst:
		so = re.sub(r"[\s-]", "", mst)
		if not so.isascii() or not so.isdigit() or len(so) not in (10, 12, 13):
			raise ValueError("Mã số thuế chưa đúng định dạng. Xác nhận lại mã số thuế người mua trước khi xuất.")
		mst = so[:10] + "-" + so[10:] if len(so) == 13 else so
	if ten_mac_dinh(ten):
		if mst:
			raise ValueError("Có mã số thuế nhưng chưa có tên người mua. Mở khối Hoá đơn điện tử để sửa tên trước khi xuất.")
		return {"inv_buyerDisplayName": "Bán cho người tiêu dùng", "inv_buyerLegalName": "",
			"inv_buyerTaxCode": "", "inv_buyerAddressLine": "", "inv_buyerEmail": ""}
	if mst and hoa_don_vat.thieu_ten_rieng(ten):
		raise ValueError(hoa_don_vat.LOI_TEN_CUT)
	mail = chuoi(si.get("vgb_xhd_email"))
	if mail and not re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", mail):
		raise ValueError("Email nhận hoá đơn chưa hợp lệ. Mở khối Hoá đơn điện tử, xác nhận lại đúng email người mua.")
	return {"inv_buyerDisplayName": "" if mst else ten, "inv_buyerLegalName": ten if mst else "",
		"inv_buyerTaxCode": mst, "inv_buyerAddressLine": hoa_don_vat.sach_dia_chi_xhd(si.get("vgb_xhd_dia_chi")),
		"inv_buyerEmail": mail}


def chuan_goi(si, goi):
	"""Giữ phép tính giá/thuế của đường gọi, chốt người mua và ghi chú cuối."""
	ra = copy.deepcopy(goi)
	if len(ra.get("data") or []) != 1:
		raise ValueError("Mỗi lần xuất phải chỉ có một hoá đơn để kiểm đúng người mua.")
	dd = ra["data"][0]
	dd.update(nguoi_mua(si))
	# Hai cửa dùng chung mã SI, tránh đơn quầy trống mã hoặc mã Pancake trùng.
	dd["key_api"] = si.get("name")
	if la_hang_tang(si):
		if chuoi(si.get("vgb_pt_thanh_toan")) == "Hàng tặng" and si.get("vgb_tang_duyet") != "Đã duyệt":
			raise ValueError("Đơn hàng tặng chưa được Giám đốc duyệt, chưa xuất hoá đơn điện tử được.")
		for nhom in dd.get("details") or []:
			for dong in nhom.get("data") or []:
				ten = chuoi(dong.get("inv_itemName"))
				if "không thu tiền" not in ten.lower():
					dong["inv_itemName"] = ten + " (Hàng biếu tặng không thu tiền)"
		# Giữ tổng giá tính thuế, nói rõ khách không phải trả ngay trên tờ VAT.
		dd["inv_paymentMethodName"] = "Hàng tặng không thu tiền"
	return ra


import frappe

TRUONG_MOI = {"Sales Invoice": [{
	"fieldname": "vgb_hddt_cho_doi_chieu", "label": "HĐĐT cần đối chiếu kết quả gửi",
	"fieldtype": "Check", "read_only": 1, "no_copy": 1,
	"insert_after": "custom_hddt_trang_thai",
	"description": "Lần gửi chưa có kết quả chắc chắn. Kế toán kiểm M-Invoice theo mã phiếu trước khi cho gửi lại.",
}]}


@frappe.whitelist()
def kiem_goi(phieu, goi, giu_cho=0):
	"""Kiểm payload; khi gửi thật lưu dấu trước HTTP để timeout không gửi đúp.

	Frappe database/database.py: commit nhả khoá giao dịch. Bởi vậy giữ
	FOR UPDATE tới khi dấu chờ đã lưu; lượt thứ hai đọc lại sẽ gặp dấu này.
	Chế độ thử không lưu dấu, bộ kiểm tích hợp không được dùng gửi thật.
	"""
	from vagabond.ban_hang import _kiem_quyen
	_kiem_quyen()
	giu_cho = int(giu_cho or 0)
	if giu_cho and frappe.flags.vagabond_kiem_that:
		frappe.throw("Bộ kiểm tích hợp không được phát hành HĐĐT ra ngoài.")
	si = frappe.get_doc("Sales Invoice", phieu, for_update=True)
	si.check_permission("read")
	if si.docstatus != 1 or si.get("vgb_huy") or si.get("vgb_tam_tinh"):
		frappe.throw("Đơn chưa ghi sổ hoặc đã huỷ/tạm tính, không xuất hoá đơn điện tử.")
	from vagabond import noi_bo
	noi_bo.chan_hoa_don_dien_tu(si)
	if da_gui(si):
		frappe.throw("Đơn đã gửi hoặc đang chờ đối chiếu kết quả gửi. Kế toán kiểm M-Invoice theo mã phiếu trước khi làm tiếp.")
	try:
		ra = chuan_goi(si, frappe.parse_json(goi) if isinstance(goi, str) else goi)
	except ValueError as loi:
		frappe.throw(str(loi))
	if giu_cho:
		frappe.db.set_value("Sales Invoice", phieu, "vgb_hddt_cho_doi_chieu", 1, update_modified=False)
		frappe.db.commit()
	return ra


@frappe.whitelist()
def mo_lai(phieu, ly_do, da_doi_chieu=0):
	"""Kế toán xác nhận không có bản trên M-Invoice rồi mới mở lại, có vết."""
	if not set(frappe.get_roles()) & {"System Manager", "Accounts Manager", "Giám đốc", "AP Giám đốc"}:
		frappe.throw("Chỉ Giám đốc hoặc kế toán trưởng được mở lại lần gửi HĐĐT sau đối chiếu.")
	if int(da_doi_chieu or 0) != 1 or len(chuoi(ly_do)) < 15:
		frappe.throw("Kiểm M-Invoice theo mã phiếu, xác nhận chưa có hoá đơn và ghi rõ kết quả đối chiếu (ít nhất 15 ký tự).")
	si = frappe.get_doc("Sales Invoice", phieu, for_update=True)
	if not si.get("vgb_hddt_cho_doi_chieu"):
		return {"ok": 1}
	if any(si.get(o) for o in ("custom_minvoice_id", "custom_hddt_id", "custom_hddt_so")):
		frappe.throw("Phiếu đã có mã hoá đơn M-Invoice, không được mở lại để gửi lần nữa.")
	si.add_comment("Comment", "Mở lại gửi HĐĐT sau đối chiếu không có hoá đơn trên M-Invoice: " + chuoi(ly_do))
	frappe.db.set_value("Sales Invoice", phieu, "vgb_hddt_cho_doi_chieu", 0, update_modified=False)
	return {"ok": 1}
