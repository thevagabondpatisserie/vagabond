# -*- coding: utf-8 -*-
"""Sửa giá và nhận dư ở bước nhập kho, có để lại dấu vết.

Uyên đề xuất 26/08/2026, anh Việt duyệt
------------------------------------------------------------------------
Hai việc thật ngày nào cũng gặp mà hệ thống đang chặn:

  1. Đặt hàng theo bảng giá, giao tới mới biết bên bán đang khuyến mãi,
     hoặc có hàng tặng kèm. Giá thực nhận khác giá đặt.
  2. Mua thịt heo 3 kg, họ giao 3,02 kg. Cân thịt không cắt ra đúng số.

ERPNext chặn cả hai bằng hai thiết lập:

  * `maintain_same_rate` mức "Stop": đơn giá phiếu nhập phải bằng hệt đơn
    giá đơn mua hàng.
  * `over_delivery_receipt_allowance` bằng 0: nhận nhiều hơn số đặt dù chỉ
    một phần trăm cũng bị chặn.

VÌ SAO NỚI HAI CÁI ĐÓ KHÔNG PHẢI LÀ BỎ KIỂM SOÁT
------------------------------------------------------------------------
`maintain_same_rate` chỉ bắt ba tờ của mình khớp nhau: đơn mua, phiếu
nhập, hoá đơn. Nó KHÔNG kiểm tra tờ nào trong ba tờ đó có đúng với thứ nhà
cung cấp thật sự đòi hay không. Mà cái đáng lo là cái sau.

Hàng rào thật đã có sẵn và mạnh hơn hẳn: `mua_dich_vu.chan_lech_tong`
không cho ghi sổ khi tổng tiền phiếu lệch với BẢN HOÁ ĐƠN ĐIỆN TỬ nhà cung
cấp đã gửi cơ quan thuế. Gõ nhầm giá thì tổng lệch, và tờ đó không vào
được sổ cái. Đó mới là kiểm soát đúng chỗ.

Nên chỗ này nới ra, còn tiền vẫn được canh ở cửa ghi sổ. Đổi lại, mọi lần
giá lúc nhận khác giá lúc đặt đều được ghi lại vào chính phiếu nhập, để
cuối tháng kế toán dò được vì sao giá vốn nhảy.

Ngưỡng nhận dư 10 phần trăm: đủ cho cân đong (3 kg thành 3,02 kg là 0,7
phần trăm) và cho khuyến mãi mua mười tặng một. Quá mười phần trăm vẫn bị
chặn, vì lúc đó nhiều khả năng là gõ nhầm số chứ không phải cân lệch.
"""

import frappe
from frappe.utils import cint, flt

# Nhận dư tới bao nhiêu phần trăm thì không chặn.
NGUONG_NHAN_DU = 10.0

# Lệch dưới mức này coi như không đổi giá, khỏi ghi chú cho rối.
NGUONG_GIA = 0.5


# ----------------------------------------------------------------- thuần


def gia_da_doi(gia_nhan, gia_dat, nguong=NGUONG_GIA):
	"""Giá lúc nhận có khác giá lúc đặt không. THUẦN."""
	if gia_dat is None or gia_nhan is None:
		return False
	return abs(flt(gia_nhan) - flt(gia_dat)) > flt(nguong)


def phan_tram_du(sl_nhan, sl_dat):
	"""Nhận dư bao nhiêu phần trăm so với số đặt. THUẦN. Âm là nhận thiếu."""
	dat = flt(sl_dat)
	if dat <= 0:
		return 0.0
	return (flt(sl_nhan) - dat) / dat * 100.0


def cau_ghi_vet(idx, ten_mon, gia_dat, gia_nhan, sl_dat, sl_nhan):
	"""Một dòng ghi vào phiếu nhập, nói rõ đổi cái gì. THUẦN."""
	phan = []
	if gia_da_doi(gia_nhan, gia_dat):
		huong = "giảm" if flt(gia_nhan) < flt(gia_dat) else "tăng"
		phan.append("đơn giá %s từ %s xuống %s" % (huong, _so(gia_dat), _so(gia_nhan))
			if huong == "giảm"
			else "đơn giá tăng từ %s lên %s" % (_so(gia_dat), _so(gia_nhan)))
	du = phan_tram_du(sl_nhan, sl_dat)
	if abs(du) > 0.01:
		phan.append("nhận %s %g so với đặt %g" % ("dư" if du > 0 else "thiếu", flt(sl_nhan), flt(sl_dat)))
	if not phan:
		return ""
	return "Dòng %d %s: %s." % (idx, ten_mon, ", ".join(phan))


def _so(x):
	try:
		n = int(round(float(x or 0)))
	except (TypeError, ValueError):
		return "0"
	dau = "-" if n < 0 else ""
	s = str(abs(n))
	cum = []
	while s:
		cum.insert(0, s[-3:])
		s = s[:-3]
	return dau + ".".join(cum)


# ------------------------------------------------------- phan can Frappe


def ghi_vet(doc, method=None):
	"""Hook `validate` trên Phiếu nhập kho: ghi lại giá và số lượng đã đổi.

	Chỉ GHI CHÚ, không chặn ai. Người nhận hàng cứ nhập theo thực tế, còn
	kế toán có cái để dò.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		can = []
		for d in doc.get("items") or []:
			ma_dong = (d.get("purchase_order_item") or "").strip()
			if not ma_dong:
				continue
			dat = frappe.db.get_value(
				"Purchase Order Item", ma_dong, ["rate", "qty"], as_dict=True
			)
			if not dat:
				continue
			cau = cau_ghi_vet(
				d.idx, d.get("item_name") or d.get("item_code") or "",
				dat.get("rate"), d.get("rate"), dat.get("qty"), d.get("qty"),
			)
			if cau:
				can.append(cau)
		if not can:
			return
		cu = (doc.get("remarks") or "").strip()
		# Ghi đè phần cũ của chính mình chứ không nối thêm mãi: sửa đi sửa
		# lại một phiếu là ô ghi chú dài ra vô tận.
		giu = [d for d in cu.split("\n") if not d.startswith("Dòng ") or "so với đặt" not in d and "đơn giá" not in d]
		doc.remarks = "\n".join([d for d in giu if d.strip()] + can).strip()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gia_khi_nhan: ghi vet")
