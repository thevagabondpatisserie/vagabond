# -*- coding: utf-8 -*-
"""Hàng rào đơn vị cho đơn mua hàng và phiếu nhập kho.

VÌ SAO CÓ TỆP NÀY, ngày 27/08/2026
--------------------------------------------------------------------
Rà 43 mẩu lệnh chỉ sống trên Desk thì thấy mẩu "Gợi ý giá mua" ghi
thẳng cả GIÁ lẫn ĐƠN VỊ vào dòng đơn mua. Mẩu đó nằm trong cơ sở dữ
liệu, git không quản, không có ca kiểm nào soi, và app không nhìn thấy
nó. Nó ghi đơn vị gì thì dòng mang đơn vị đó, kể cả đơn vị mà danh mục
Món chưa bao giờ khai.

Số liệu thật cùng ngày, 5 đơn mua đang mở:

    DMH-2026-00127  1 "Box" hệ số 1, món chỉ khai Gram/Kg/Lon
    DMH-2026-00145  18 "Hộp" hệ số 500, món khai Hộp với hệ số khác
    DMH-2026-00126  2 "Kg" hệ số 1000, món CHỈ khai Gram
    DMH-2026-00067  1 "Kg" hệ số 1000, món CHỈ khai Gram
    DMH-2026-00204  4 "Kg" hệ số 1000, món CHỈ khai Gram

Cái "1 Box hệ số 1" là loại nguy hiểm nhất: một thùng hàng vào kho
thành một gram. Y hệt vụ 24,63 Kg bơ thành 24,63 Gram bên hoá đơn.

CÁCH CHỮA
--------------------------------------------------------------------
Không đi sửa mẩu lệnh trên Desk. Đặt hàng rào ở tầng dưới, ngay lúc
lưu chứng từ. Như vậy:

  - Mẩu lệnh cũ ghi sai bao nhiêu cũng không lọt.
  - Nút bên app và nút bên Desk chịu chung một luật.
  - Những đường mình CHƯA BIẾT cũng bị chặn luôn.

Đây đúng là cách v328 đã dùng cho số lượng đã duyệt, nay áp cho đơn vị.

Phần thuần nằm trên vạch, phần chạm Frappe nằm dưới, để bộ kiểm chạy
được trên máy CI tay không.
"""

from vagabond import dvt_mua

# Ba kết luận của phép soi một dòng.
DVT_OK = "ok"                  # đơn vị kho, hoặc món đã khai đúng hệ số
DVT_CHUA_KHAI = "chua_khai"    # món chưa khai đơn vị này
DVT_SAI_HE_SO = "sai_he_so"    # món có khai nhưng hệ số trên dòng khác


def soi_dong(dvt_dong, he_so_dong, dvt_kho, he_so_mon_khai):
	"""Dòng này mang đơn vị hợp lệ không. THUẦN.

	`he_so_mon_khai` là hệ số món khai cho đơn vị đó, hoặc None nếu món
	chưa khai. Truyền None chứ đừng truyền 0: 0 và "chưa khai" là hai
	chuyện khác nhau, gộp lại là mất thông tin.

	Đơn vị trùng đơn vị kho thì luôn hợp lệ, không cần khai gì thêm - đó
	là mặc định của ERPNext.
	"""
	if dvt_mua.cung_don_vi(dvt_dong, dvt_kho):
		return DVT_OK
	if he_so_mon_khai is None:
		return DVT_CHUA_KHAI
	if abs(dvt_mua.he_so(he_so_mon_khai) - dvt_mua.he_so(he_so_dong)) > 1e-9:
		return DVT_SAI_HE_SO
	return DVT_OK


def loi_chua_khai(idx, ma_mon, ten_mon, dvt, dvt_kho, da_khai):
	"""Câu tiếng Việt cho ca món chưa khai đơn vị. THUẦN."""
	cau = (
		'Dòng %d, món %s "%s": đơn vị "%s" chưa được khai trong bảng quy đổi '
		"của món, nên hệ thống không biết một %s bằng bao nhiêu %s."
		% (idx, ma_mon, ten_mon or ma_mon, dvt, dvt, dvt_kho)
	)
	if da_khai:
		cau += " Món này đang khai: %s." % ", ".join(da_khai)
	else:
		cau += " Món này chưa khai đơn vị nào ngoài đơn vị kho."
	cau += (
		" Mở danh mục Món, thêm đơn vị đó vào bảng quy đổi rồi quay lại. "
		"Đừng sửa tay số lượng cho khớp, vì như vậy tồn kho sẽ sai."
	)
	return cau


def loi_sai_he_so(idx, ma_mon, ten_mon, dvt, he_so_dong, he_so_khai, dvt_kho):
	"""Câu tiếng Việt cho ca hệ số trên dòng khác hệ số món khai. THUẦN."""
	return (
		'Dòng %d, món %s "%s": dòng ghi 1 %s bằng %g %s, nhưng danh mục Món '
		"khai 1 %s bằng %g %s. Hai con số phải bằng nhau. Sửa lại hệ số trên "
		"dòng, hoặc sửa bảng quy đổi của món nếu quy cách nhà cung cấp đã đổi."
		% (
			idx, ma_mon, ten_mon or ma_mon, dvt,
			dvt_mua.he_so(he_so_dong), dvt_kho,
			dvt, dvt_mua.he_so(he_so_khai), dvt_kho,
		)
	)


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import flt


def _he_so_khai(item_code, dvt):
	"""Hệ số món khai cho đơn vị đó, None nếu chưa khai.

	Trả None chứ không trả 0 - xem ghi chú ở `soi_dong`.
	"""
	if not (item_code and dvt):
		return None
	v = frappe.db.get_value(
		"UOM Conversion Detail", {"parent": item_code, "uom": dvt}, "conversion_factor"
	)
	return None if v is None else flt(v)


def _cac_dvt_da_khai(item_code):
	return [
		r[0]
		for r in frappe.db.get_all(
			"UOM Conversion Detail",
			filters={"parent": item_code},
			fields=["uom"],
			as_list=True,
			limit_page_length=0,
		)
	]


def chan_don_vi_la(doc, method=None):
	"""Chặn lưu khi có dòng mang đơn vị món chưa khai, hoặc sai hệ số.

	Gắn cho cả Đơn mua hàng lẫn Phiếu nhập kho: hai chứng từ này đều có
	nút trên Desk tự điền đơn vị, và cả hai đều chảy tiếp vào kho.

	Gom hết lỗi rồi báo MỘT LẦN, đừng báo từng dòng một. Người nhập mà
	phải sửa rồi bấm lại năm lần thì lần thứ ba là họ đi tìm đường vòng.
	"""
	loi = []
	for r in doc.get("items") or []:
		ma = r.get("item_code")
		if not ma:
			continue
		dvt = r.get("uom")
		dvt_kho = r.get("stock_uom") or frappe.db.get_value("Item", ma, "stock_uom")
		if not (dvt and dvt_kho):
			continue
		khai = _he_so_khai(ma, dvt)
		ket = soi_dong(dvt, r.get("conversion_factor"), dvt_kho, khai)
		if ket == DVT_OK:
			continue
		if ket == DVT_CHUA_KHAI:
			loi.append(loi_chua_khai(
				r.idx, ma, r.get("item_name"), dvt, dvt_kho, _cac_dvt_da_khai(ma)
			))
		else:
			loi.append(loi_sai_he_so(
				r.idx, ma, r.get("item_name"), dvt,
				r.get("conversion_factor"), khai, dvt_kho,
			))
	if loi:
		frappe.throw(
			"Đơn vị tính chưa khớp danh mục Món:<br><br>" + "<br><br>".join(loi),
			title="Sai đơn vị tính",
		)
