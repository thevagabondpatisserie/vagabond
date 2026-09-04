# -*- coding: utf-8 -*-
"""Bước xử lý của một tờ hoá đơn mua, hiện ngay trên màn danh sách.

VÌ SAO CÓ TỆP NÀY (anh Việt hỏi 04/09/2026)
-------------------------------------------
Anh ghi sổ một tờ xong, ra màn danh sách vẫn chỉ thấy chữ "Quá hạn", và
anh nói thêm là cái trạng thái đó "cũng ít xài nữa".

Đếm thật trên hệ ngày 04/09/2026 giải thích cả hai vế:

  * 63 tờ đã ghi sổ thì 62 tờ có hạn trả TRÙNG ĐÚNG ngày hạch toán, vì
    525 nhà cung cấp không ai được khai điều khoản thanh toán. Hạn trả
    bằng ngày lập nên tờ vừa ghi sổ xong là quá hạn ngay lập tức. 51 tờ
    mang chữ "Quá hạn". Nó không còn là trạng thái nữa, nó là hằng số.
    Một cột lúc nào cũng đỏ thì người ta thôi nhìn nó, đúng như anh nói.

  * 3.170 tờ còn nháp thì tất cả đều hiện đúng một chữ "Nháp", trong khi
    chúng đang ở ba tình cảnh rất khác nhau: 2.487 tờ còn dòng chưa gắn
    mã hàng, 508 tờ đã đủ mã nhưng chưa nối phiếu nhập, và chỉ 5 tờ là
    sạch, chờ kế toán ghi sổ. Ba việc của ba người khác nhau mà đội chung
    một cái nhãn.

Nên tệp này KHÔNG đi đổi tên "Quá hạn" thành "Đã ghi sổ" cho xong. Nó
tính ra tờ đang đứng ở BƯỚC nào của dây chuyền, để nhìn cột trạng thái là
biết tờ đó đang chờ ai làm gì.

NGUYÊN TẮC: CHỈ NÓI ĐIỀU CÒN ĐÚNG
---------------------------------
Ô này được tính lại mỗi lần lưu tờ, nên với tờ còn nháp nó luôn tươi.
Tờ đã ghi sổ thì không lưu lại nữa, nên ô này KHÔNG được dùng để nói
những chuyện còn thay đổi sau khi ghi sổ - trả tiền, phân bổ chi phí.
Mấy chuyện đó màn danh sách đọc thẳng từ số dư công nợ, hoặc để dành cho
báo cáo đối chiếu. Một ô nói sai còn hại hơn không có ô nào.
"""

import frappe
from frappe.utils import cint

PI = "Purchase Invoice"
TRUONG = "vgb_buoc"

# Tên bước. Giữ nguyên chuỗi này khi sửa: màn danh sách và bộ lọc đã lưu
# của kế toán đều neo vào đúng mấy chữ ở đây.
B_THIEU_MA = "Thiếu mã hàng"
B_LECH_HDDT = "Lệch hoá đơn điện tử"
B_CHUA_NOI = "Chờ nối phiếu nhập"
B_CHO_GHI_SO = "Chờ ghi sổ"

DS_BUOC = [B_THIEU_MA, B_LECH_HDDT, B_CHUA_NOI, B_CHO_GHI_SO]

TRUONG_MOI = {
	PI: [
		{
			"fieldname": TRUONG,
			"label": "Bước xử lý",
			"fieldtype": "Select",
			"options": "\n" + "\n".join(DS_BUOC),
			"read_only": 1,
			"in_standard_filter": 1,
			"description": (
				"Tờ này đang chờ ai làm gì. Máy tự tính mỗi lần lưu, không "
				"gõ tay. Chỉ có nghĩa với tờ còn nháp."
			),
		},
	],
}


# ------------------------------------------------------------ phép thuần


def buoc_cua_to(dong, lech_hddt=0):
	"""Tờ đang ở bước nào. THUẦN, không chạm Frappe.

	`dong` là danh sách từ điển, mỗi dòng có `item_code`, `purchase_receipt`
	và `qua_kho`. `lech_hddt` là tờ có lệch tổng với hoá đơn điện tử không.

	Thứ tự xét là thứ tự người phải làm, và nó có lý do:

	  1. Thiếu mã hàng chặn TẤT CẢ các bước sau. Chưa biết là món gì thì
	     không tra được phiếu nhập, không tính được giá vốn. Đây cũng là
	     nhóm đông nhất nên để đầu.
	  2. Lệch hoá đơn điện tử xét trước bước nối phiếu, vì nối phiếu trên
	     một tờ đang lệch số là nối vào một con số sai.
	  3. Còn dòng hàng thật chưa có phiếu nhập thì chờ thu mua nối.
	  4. Hết cả ba thì tờ sạch, chờ kế toán ghi sổ.

	Dòng KHÔNG qua kho (phí ship, dịch vụ) không bao giờ tính là thiếu
	phiếu nhập - đó chính là cái bẫy đã làm kẹt Uyên suốt tháng 8.
	"""
	ds = list(dong or [])
	if any(not str((d or {}).get("item_code") or "").strip() for d in ds):
		return B_THIEU_MA
	if cint(lech_hddt):
		return B_LECH_HDDT
	for d in ds:
		if not cint((d or {}).get("qua_kho")):
			continue
		if not str((d or {}).get("purchase_receipt") or "").strip():
			return B_CHUA_NOI
	return B_CHO_GHI_SO


def mau_cua_buoc(buoc):
	"""Màu của một bước trên màn danh sách. THUẦN.

	Đỏ dành cho việc đang CHẶN dây chuyền, cam cho việc đang chờ người
	khác, xanh cho tờ đã sẵn sàng. Không dùng đỏ cho mọi thứ, vì đỏ khắp
	nơi thì đỏ không còn nghĩa gì - đúng bài học của chữ "Quá hạn".
	"""
	return {
		B_THIEU_MA: "red",
		B_LECH_HDDT: "red",
		B_CHUA_NOI: "orange",
		B_CHO_GHI_SO: "blue",
	}.get(str(buoc or "").strip(), "gray")


def han_tra_that(ngay_hach_toan, han_tra):
	"""Tờ này có hạn trả THẬT không, hay hạn bằng luôn ngày lập. THUẦN.

	Hạn trả bằng ngày hạch toán nghĩa là chưa ai khai điều khoản thanh
	toán cho nhà cung cấp, chứ không phải chủ nợ đòi tiền ngay trong ngày.
	Gọi tờ đó là "quá hạn" là vu oan cho cả 525 nhà cung cấp.
	"""
	a = str(ngay_hach_toan or "").strip()
	b = str(han_tra or "").strip()
	if not a or not b:
		return 0
	return 1 if b > a else 0


# ------------------------------------------------------------ chạm Frappe


def _qua_kho(ma):
	"""Món này có quản kho không. Không có mã thì coi như không."""
	ma = str(ma or "").strip()
	if not ma:
		return 0
	try:
		return 1 if cint(frappe.db.get_value("Item", ma, "is_stock_item")) else 0
	except Exception:
		return 0


def _lech_hddt(doc):
	"""Tờ có lệch tổng so với bản hoá đơn điện tử gốc không."""
	try:
		from vagabond import dung_lai_hddt, mua_dich_vu

		g = dung_lai_hddt._goc(doc.get("custom_minvoice_id"))
		if not g:
			return 0
		muc_tieu = dung_lai_hddt.muc_tieu_truoc_thue(g)
		if not muc_tieu:
			return 0
		hien = dung_lai_hddt._tong_dong_hien_tai(doc)
		return 1 if mua_dich_vu.lech_qua_nguong(hien, muc_tieu, dung_lai_hddt.NGUONG) else 0
	except Exception:
		return 0


def dat_buoc(doc, method=None):
	"""Hook validate: ghi lại tờ này đang ở bước nào.

	Mọi lỗi ở đây chỉ ghi nhật ký. Một ô hiển thị hỏng KHÔNG bao giờ được
	làm rớt việc lưu chứng từ - bài học hook đặt trên "*" ngày 16/08.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		dong = []
		for d in doc.get("items") or []:
			ma = str(d.get("item_code") or "").strip()
			dong.append({
				"item_code": ma,
				"purchase_receipt": d.get("purchase_receipt"),
				"qua_kho": _qua_kho(ma),
			})
		doc.set(TRUONG, buoc_cua_to(dong, _lech_hddt(doc)))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "buoc_hoa_don_mua: dat buoc")
