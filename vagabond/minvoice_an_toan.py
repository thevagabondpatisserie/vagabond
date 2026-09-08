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
		from vagabond.hang_tang_so_cai import kiem_thue_gui
		kiem_thue_gui(si, dd)
	return ra


# ---------------------------------------------------------------- phân loại phản hồi Save
#
# Bằng chứng thật đã ghi trong project doc (m-invoice-xuat-hoa-don-tu-dong,
# ma-so-thue-chi-nhanh-va-tu-ghi-so-23h30):
#   - tạo được:  {"code": "00", "ok": true, "data": {"inv_invoiceAuth_id": ...}}
#   - từ chối:   code "296" "Create invoice fail" (12/08/2026, MST thiếu gạch ngang);
#                gọi lại cùng dữ liệu vẫn 296, không có tờ nào sinh ra bên M-Invoice.
# Chưa có bảng mã lỗi đầy đủ của M-Invoice trong tay, nên chỉ mã đã thấy thật
# mới được coi là "chắc chắn chưa tạo". Mọi mã khác, phản hồi thiếu dữ liệu,
# phản hồi nói trùng/đã tồn tại, hay timeout đều GIỮ cờ đối chiếu.
MA_TAO = "00"
MA_TU_CHOI_RO = {"296"}
DAU_HIEU_TRUNG = ("tồn tại", "ton tai", "trùng", "trung", "exist", "duplicate", "đã có", "da co")


def phan_loai_phan_hoi_thuan(phan_hoi, loi=None):
	"""Một nguồn duy nhất cho Python và Server Script.

	Trả {"loai": "tao" | "tu_choi" | "khong_ro", "cau": ..., "id": ...}.
	  tao      : có mã 00 và có inv_invoiceAuth_id, ghi ID và gỡ cờ.
	  tu_choi  : M-Invoice từ chối bằng mã đã biết, không kèm ID và không nói
	             trùng. Gỡ cờ để kế toán sửa rồi gửi lại.
	  khong_ro : mọi trường hợp còn lại. Giữ cờ, kế toán đối chiếu theo mã phiếu.
	"""
	if loi is not None:
		return {"loai": "khong_ro", "cau": "Không rõ kết quả gửi (" + chuoi(loi)[:150] + ")", "id": ""}
	if not isinstance(phan_hoi, dict):
		return {"loai": "khong_ro", "cau": "Phản hồi không đọc được: " + chuoi(phan_hoi)[:150], "id": ""}
	ma = chuoi(phan_hoi.get("code"))
	du_lieu = phan_hoi.get("data")
	ma_hd = chuoi(du_lieu.get("inv_invoiceAuth_id")) if isinstance(du_lieu, dict) else ""
	thong_diep = chuoi(phan_hoi.get("message"))
	if ma == MA_TAO and ma_hd:
		return {"loai": "tao", "cau": "Đã tạo hoá đơn " + ma_hd, "id": ma_hd}
	if ma_hd:
		return {"loai": "khong_ro", "cau": "Mã " + ma + " nhưng có ID " + ma_hd + ", giữ đối chiếu", "id": ma_hd}
	if ma == MA_TAO:
		return {"loai": "khong_ro", "cau": "Mã 00 nhưng thiếu dữ liệu hoá đơn, giữ đối chiếu", "id": ""}
	tom = (ma + " " + thong_diep).strip()[:150]
	if any(d in thong_diep.lower() for d in DAU_HIEU_TRUNG):
		return {"loai": "khong_ro", "cau": "M-Invoice báo trùng/đã tồn tại: " + tom, "id": ""}
	if ma in MA_TU_CHOI_RO and phan_hoi.get("ok") is not True:
		return {"loai": "tu_choi", "cau": "M-Invoice từ chối: " + tom, "id": ""}
	if not ma:
		return {"loai": "khong_ro", "cau": "Phản hồi không có mã: " + chuoi(phan_hoi)[:150], "id": ""}
	return {"loai": "khong_ro", "cau": "Mã chưa rõ " + tom + ", giữ đối chiếu", "id": ""}


import frappe


@frappe.whitelist()
def phan_loai_phan_hoi(phan_hoi=None, loi=None):
	"""Cửa cho Server Script gọi cùng quy tắc; thuần, không ghi gì."""
	if isinstance(phan_hoi, str):
		import json
		try:
			phan_hoi = json.loads(phan_hoi)
		except Exception:
			pass
	return phan_loai_phan_hoi_thuan(phan_hoi, loi)


def go_co_sau_tu_choi(phieu, cau):
	"""Từ chối rõ: gỡ cờ và ghi vết, rồi COMMIT ngay.

	Bên gọi sẽ frappe.throw để báo kế toán; throw làm Frappe rollback cả
	request, nên nếu không commit ở đây thì việc gỡ cờ bị cuốn theo và
	phiếu kẹt lại như chưa sửa gì. Cờ đã được commit lúc giữ chỗ (kiem_goi),
	nên gỡ cũng phải commit thì DB đọc lại sau request mới đúng.
	"""
	if frappe.flags.vagabond_kiem_that:
		frappe.throw("Bộ kiểm tích hợp không được gỡ cờ HĐĐT thật.")
	si = frappe.get_doc("Sales Invoice", phieu, for_update=True)
	if any(chuoi(si.get(o)) for o in ("custom_minvoice_id", "custom_hddt_id", "custom_hddt_so")):
		frappe.db.commit()
		return
	si.add_comment("Comment", "M-Invoice từ chối lần gửi HĐĐT, mở lại để kế toán sửa và gửi lại: " + chuoi(cau)[:300])
	frappe.db.set_value("Sales Invoice", phieu, "vgb_hddt_cho_doi_chieu", 0, update_modified=False)
	frappe.db.commit()

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
