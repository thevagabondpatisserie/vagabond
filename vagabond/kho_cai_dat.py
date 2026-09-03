# -*- coding: utf-8 -*-
"""Nguong cua kho: dung sai giao nhan va han dung toi thieu chung.

Anh Viet 03/09/2026 chot dung sai giao thua giao thieu mac dinh 5 phan tram
va "chinh trong Cai dat". Tep nay giu cho de sua, con phep tinh nam ben
`kho_sap.py` de kiem thu duoc khong can site.

Han dung toi thieu thi khai THEO MON tren danh muc (o `Số ngày hạn dùng tối
thiểu khi nhận`), vi bo lat khac hop kem khac nhau. O duoi day chi la muc
chung cho nhung mon chua khai rieng, mac dinh 0 tuc khong soi.
"""

import json

import frappe

from vagabond import kho_sap
from vagabond.lib import cfg_o

TRUONG = "vgb_kho_sap"

QUYEN_SUA = {"System Manager", "Stock Manager", "Accounts Manager"}

# O tren danh muc Mon: so ngay han dung con lai toi thieu khi nhan hang.
TRUONG_MOI = {
	"Item": [
		{
			"fieldname": "vgb_hsd_toi_thieu",
			"label": "Số ngày hạn dùng tối thiểu khi nhận",
			"fieldtype": "Int",
			"insert_after": "shelf_life_in_days",
			"description": (
				"Nhận hàng mà hạn dùng còn ít hơn số ngày này thì máy chặn. "
				"Để 0 là không soi. Ví dụ bơ lạt để 30."
			),
		},
	],
}


def doc():
	"""Nguong dang chay. Khong bao gio nem loi: hong cau hinh thi ve mac dinh."""
	try:
		tho = json.loads((cfg_o(TRUONG) or "").strip() or "{}")
	except Exception:
		tho = {}
	if not isinstance(tho, dict):
		tho = {}
	return {
		"dung_sai_thua": kho_sap.chuan_dung_sai(tho.get("dung_sai_thua")),
		"dung_sai_thieu": kho_sap.chuan_dung_sai(tho.get("dung_sai_thieu")),
		"hsd_toi_thieu_chung": max(0, int(tho.get("hsd_toi_thieu_chung") or 0)),
	}


def hsd_toi_thieu_cua(ma_hang, chung=None):
	"""So ngay han dung toi thieu cua mot mon: khai rieng truoc, roi den chung."""
	if chung is None:
		chung = doc()["hsd_toi_thieu_chung"]
	try:
		rieng = int(frappe.db.get_value("Item", ma_hang, "vgb_hsd_toi_thieu") or 0)
	except Exception:
		rieng = 0
	return rieng if rieng > 0 else int(chung or 0)


def _tran_erpnext():
	"""Muc nhan du ERPNext dang cho phep, doc tu Cai dat kho cua no."""
	try:
		return float(
			frappe.db.get_single_value("Stock Settings", "over_delivery_receipt_allowance") or 0
		)
	except Exception:
		return None


@frappe.whitelist()
def danh_sach():
	"""Cho man Cai dat: nguong dang chay va danh sach ly do chenh lech."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	c = doc()
	c["sua_duoc"] = 1 if QUYEN_SUA & set(frappe.get_roles()) else 0
	c["mac_dinh"] = kho_sap.DUNG_SAI_MAC_DINH
	c["tran"] = kho_sap.DUNG_SAI_TRAN
	c["ly_do_lech"] = kho_sap.LY_DO_LECH
	c["tran_erpnext"] = _tran_erpnext()
	return c


@frappe.whitelist()
def luu(dung_sai_thua=None, dung_sai_thieu=None, hsd_toi_thieu_chung=None):
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý kho hoặc kế toán mới sửa được ngưỡng kho.")
	m = {
		"dung_sai_thua": kho_sap.chuan_dung_sai(dung_sai_thua),
		"dung_sai_thieu": kho_sap.chuan_dung_sai(dung_sai_thieu),
		"hsd_toi_thieu_chung": max(0, int(hsd_toi_thieu_chung or 0)),
	}
	# ERPNext co nguong nhan du cua rieng no trong Cai dat kho. Dat nguong
	# cua minh RONG HON no thi minh cho nhan ma ERPNext van chan, va cau bao
	# hien ra la cau tieng Anh cua ERPNext - nguoi dung khong hieu vi sao vua
	# noi cho lai bao khong. Nen chan ngay tai day.
	tran_erp = _tran_erpnext()
	if tran_erp is not None and m["dung_sai_thua"] > tran_erp + 0.0001:
		frappe.throw(
			"Dung sai nhận dư đang đặt %s phần trăm, rộng hơn mức %s phần trăm "
			"mà ERPNext cho phép, nên đặt xong vẫn không nhận dư được. Nới mức "
			"của ERPNext trong Cài đặt kho trước, hoặc đặt lại số nhỏ hơn."
			% (m["dung_sai_thua"], tran_erp)
		)
	chuoi = json.dumps(m, ensure_ascii=False, indent=1)
	frappe.db.set_single_value("Vagabond Settings", TRUONG, chuoi)
	frappe.db.commit()
	# Ghi xong doc lai, vi ly do da noi dai o `tai_khoan.luu`.
	if (cfg_o(TRUONG) or "").strip() != chuoi.strip():
		frappe.throw(
			"Máy ghi xong nhưng đọc lại không thấy. Báo kỹ thuật trước khi "
			"dùng tiếp, vì ngưỡng đang chạy vẫn là ngưỡng cũ."
		)
	try:
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "Vagabond Settings",
			"reference_name": "Vagabond Settings",
			"content": "Sửa ngưỡng kho: dung sai thừa %s%%, thiếu %s%%, hạn dùng tối thiểu chung %s ngày - %s"
			% (m["dung_sai_thua"], m["dung_sai_thieu"], m["hsd_toi_thieu_chung"], frappe.session.user),
		}).insert(ignore_permissions=True)
	except Exception:
		pass
	return danh_sach()
