"""Chung tu MUA DICH VU: lay so theo DAU hoa don dien tu, khong cong dong chi tiet.

Vi sao co mo dun nay
--------------------
Hoa don cuoc van chuyen GSM so 57194 ngay 31/07/2026 keo ve 929 dong chi
tiet, moi dong la mot chuyen xe. Cong 929 dong lai ra 26.609.274 trong khi
dau hoa don ghi tien truoc thue 22.068.519. Lech 4.540.755.

Truy ra thi khong phai loi lam tron. Trong phan chi tiet cua m-invoice moi
dong co truong `tchat` (tinh chat):

    tchat = 1   hang hoa, dich vu binh thuong        824 dong  18.474.089
    tchat = 5   dong phi, van tinh tien              104 dong   5.864.815
    tchat = 3   CHIET KHAU THUONG MAI                  1 dong   2.270.370
    tchat = 4   ghi chu, dien giai, khong tinh tien

May dang be nguyen moi dong thanh dong hang duong, khong doc `tchat`. Dong
chiet khau le ra phai TRU thi lai duoc CONG, nen sai so dung bang HAI LAN
dong chiet khau: 2 x 2.270.370 = 4.540.740, cong 15d lam tron tung dong cua
chinh m-invoice, ra dung 4.540.755.

Cach chua tan goc
-----------------
Voi hoa don dich vu thi so ke toan phai lay tu DAU hoa don dien tu
(`tien_truoc_thue`, `tien_thue`, `tong_tien`), khong lay tu tong cong phan
chi tiet. Dau hoa don la con so DA KY va DA GUI co quan thue; phan chi tiet
chi la dien giai, va ban than m-invoice lam tron tung dong nen cong lai gan
nhu luon lech vai dong.

Lay theo dau hoa don thi tong tren ERP luon khop tuyet doi voi hoa don dien
tu, va khong phu thuoc vao viec may hieu dung hay sai tinh chat tung dong.

Chi tiet 929 chuyen khong mat: no van nam nguyen trong `MInvoice Invoice`,
tra luc nao cung co. No chi khong duoc chay vao so nua.

Anh Viet chot 18/08/2026.
"""

import frappe
from frappe.utils import cint, flt

PI = "Purchase Invoice"

LOAI_HANG = "Mua hàng"
LOAI_DICH_VU = "Mua dịch vụ"

# Lech bao nhieu dong thi coi la khac nhau. Mot dong: hoa don dien tu tinh
# tron den dong nen khong bao gio duoc phep lech qua the.
NGUONG_LECH = 1.0

# Tinh chat dong trong chi tiet m-invoice.
TC_CHIET_KHAU = "3"
TC_GHI_CHU = "4"


TRUONG_MOI = {
	PI: [
		{
			"fieldname": "vgb_loai_chung_tu",
			"label": "Loại chứng từ",
			"fieldtype": "Select",
			"options": "%s\n%s" % (LOAI_HANG, LOAI_DICH_VU),
			"default": LOAI_HANG,
			"insert_after": "supplier",
			"in_standard_filter": 1,
			"description": (
				"Mua hàng: giữ lưới mặt hàng chi tiết như cũ. "
				"Mua dịch vụ: gom thành một dòng, số tiền lấy thẳng từ đầu hoá đơn "
				"điện tử nên luôn khớp tuyệt đối, không còn sai số làm tròn."
			),
		},
		{
			"fieldname": "vgb_tk_chi_phi",
			"label": "Tài khoản chi phí",
			"fieldtype": "Link",
			"options": "Account",
			"insert_after": "vgb_loai_chung_tu",
			"depends_on": "eval:doc.vgb_loai_chung_tu=='%s'" % LOAI_DICH_VU,
			"description": (
				"Tài khoản ghi Nợ cho khoản dịch vụ này, ví dụ 6417 cho cước giao hàng "
				"bán, 6277 cho dịch vụ mua ngoài của bếp. Để trống thì máy giữ tài khoản "
				"đang có trên dòng, mà mặc định của hệ là 632 nên thường sai."
			),
		},
	]
}


# ------------------------------------------------------------ phep THUAN
#
# Bon ham duoi day khong cham vao Frappe, nen kiem thu duoc khong can site.


def so_theo_dau_hoa_don(dau):
	"""Doc ba con so tien tu DAU hoa don dien tu. THUAN.

	Tra ve (truoc_thue, thue, tong).

	Hoa don cua HO KINH DOANH khong co thue nen m-invoice de trong o
	`tien_truoc_thue`. Quet 1.500 hoa don gan nhat thay 5 cai nhu vay (Abby
	E33, Trai cay nhap khau, Nguyen Van Tien, Nha van hoa Thanh Nien). Lay
	nguyen o trong do la ghi so 0 dong. Nhom nay lay tong tien lam goc.
	"""
	dau = dau or {}
	tong = flt(dau.get("tong_tien"))
	thue = flt(dau.get("tien_thue"))
	truoc = flt(dau.get("tien_truoc_thue"))
	if not truoc and tong:
		truoc = tong - thue
	if not tong:
		tong = truoc + thue
	return truoc, thue, tong


def gom_dong_theo_tinh_chat(chi_tiet):
	"""Cong phan chi tiet cho DUNG DAU. THUAN.

	Dong chiet khau thuong mai (tchat 3) phai tru ra, dong ghi chu dien giai
	(tchat 4) khong tinh tien. Moi thu con lai cong vao.

	Dung de doi chieu va de vet lai luong mua hang thuong, chu luong mua dich
	vu thi khong dung den phan chi tiet nua.
	"""
	tong = 0.0
	for d in chi_tiet or []:
		tc = str(d.get("tchat"))
		if tc == TC_GHI_CHU:
			continue
		tien = flt(d.get("thtien"))
		tong += -tien if tc == TC_CHIET_KHAU else tien
	return tong


def lech_qua_nguong(a, b, nguong=NGUONG_LECH):
	"""Hai con so nay co coi la khac nhau khong. THUAN."""
	return abs(flt(a) - flt(b)) > flt(nguong)


def da_gom_roi(so_dong, tien_dong_dau, truoc_thue):
	"""Phieu da gom thanh mot dong dung so chua. THUAN.

	Co ham nay de luu lai lan hai khong gom lai lan nua: gom lai la ghi de
	chinh cai vua gom, va neu ke toan da tach dong theo tai khoan thi mat.
	"""
	if cint(so_dong) != 1:
		return False
	return not lech_qua_nguong(tien_dong_dau, truoc_thue)


def dong_dich_vu(ten_ncc, so_hd, truoc_thue, tk_chi_phi=None, trung_tam=None):
	"""Dung mot dong hang gom cho hoa don dich vu. THUAN."""
	mo_ta = "Dịch vụ mua ngoài theo hoá đơn %s" % (so_hd or "")
	if ten_ncc:
		mo_ta = "%s, %s" % (mo_ta.rstrip(", "), ten_ncc)
	dong = {
		"item_name": (mo_ta[:140] or "Dịch vụ mua ngoài"),
		"description": mo_ta,
		"qty": 1,
		"uom": "Nos",
		"stock_uom": "Nos",
		"conversion_factor": 1,
		"rate": flt(truoc_thue),
		"amount": flt(truoc_thue),
	}
	if tk_chi_phi:
		dong["expense_account"] = tk_chi_phi
	if trung_tam:
		dong["cost_center"] = trung_tam
	return dong


# ------------------------------------------------------------ cham vao he


def _dau_hoa_don(ma_minvoice):
	"""Doc dau hoa don dien tu. Khong co thi tra ve None."""
	if not ma_minvoice:
		return None
	if not frappe.db.exists("MInvoice Invoice", ma_minvoice):
		return None
	return frappe.db.get_value(
		"MInvoice Invoice",
		ma_minvoice,
		["so_hd", "tien_truoc_thue", "tien_thue", "tong_tien"],
		as_dict=True,
	)


def _trung_tam_mac_dinh(doc):
	"""Trung tam chi phi de dat len dong. Thieu la ERPNext chan ghi so."""
	for d in doc.get("items") or []:
		if d.get("cost_center"):
			return d.get("cost_center")
	if doc.get("cost_center"):
		return doc.get("cost_center")
	return frappe.db.get_value("Company", doc.get("company"), "cost_center")


def _tk_chi_phi_dang_dung(doc):
	"""Tai khoan chi phi dang co tren dong dau, dung khi ke toan chua chon."""
	for d in doc.get("items") or []:
		if d.get("expense_account"):
			return d.get("expense_account")
	return None


def truoc_khi_luu(doc, method=None):
	"""Gom hoa don dich vu thanh mot dong. Goi tu before_validate."""
	if (doc.get("vgb_loai_chung_tu") or LOAI_HANG) != LOAI_DICH_VU:
		return
	dau = _dau_hoa_don(doc.get("custom_minvoice_id"))
	if not dau:
		return
	truoc_thue, _thue, _tong = so_theo_dau_hoa_don(dau)
	if truoc_thue <= 0:
		return

	dong_hien = doc.get("items") or []
	tien_dau = flt(dong_hien[0].get("amount")) if dong_hien else 0
	if da_gom_roi(len(dong_hien), tien_dau, truoc_thue):
		return

	tk = doc.get("vgb_tk_chi_phi") or _tk_chi_phi_dang_dung(doc)
	tt = _trung_tam_mac_dinh(doc)
	dong = dong_dich_vu(
		doc.get("supplier_name") or doc.get("supplier"),
		dau.get("so_hd") or doc.get("bill_no"),
		truoc_thue,
		tk,
		tt,
	)
	doc.set("items", [])
	doc.append("items", dong)


def chan_lech_tong(doc, method=None):
	"""Khong cho ghi so khi tong tien lech voi hoa don dien tu.

	Truoc day cho nay chi CANH BAO do tren man. Canh bao thi bam qua duoc,
	nen phieu sai van vao so duoc. Hoa don dien tu la con so da gui co quan
	thue, lech mot dong cung la sai.
	"""
	dau = _dau_hoa_don(doc.get("custom_minvoice_id"))
	if not dau:
		return
	_truoc, _thue, tong = so_theo_dau_hoa_don(dau)
	if not tong:
		return
	if lech_qua_nguong(doc.get("base_grand_total"), tong):
		frappe.throw(
			"Tổng tiền phiếu %s đ không khớp hoá đơn điện tử %s đ (lệch %s đ). "
			"Hoá đơn điện tử là con số đã gửi cơ quan thuế, không được ghi sổ khi lệch. "
			"Nếu là hoá đơn dịch vụ nhiều dòng chi tiết, đổi Loại chứng từ sang "
			'"%s" rồi lưu lại, máy sẽ lấy đúng số ở đầu hoá đơn.'
			% (
				flt(doc.get("base_grand_total")),
				flt(tong),
				flt(doc.get("base_grand_total")) - flt(tong),
				LOAI_DICH_VU,
			)
		)
