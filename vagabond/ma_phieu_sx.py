# -*- coding: utf-8 -*-
"""Mã phiếu kế hoạch sản xuất và lệnh sản xuất, đọc ra thấy ngay tháng năm.

Anh Việt 30/08/2026: "đổi tiền tố mã của phiếu kế hoạch sản xuất thay vì là
MFG- thì đổi thành KHSX-26-08-0001 để thấy rõ tháng năm. Cả lệnh sản xuất
cũng nên là LSX-26-08-0001, rồi đánh số lại theo từng tháng."

Vì sao chuỗi có dấu chấm
------------------------
Frappe đọc `.YY.` và `.MM.` trong chuỗi đặt tên là "điền hai chữ số năm" và
"hai chữ số tháng", còn `.####` là bộ đếm bốn chữ số. Nên
`LSX-.YY.-.MM.-.####` cho ra `LSX-26-08-0001`.

Bộ đếm ĐẾM RIÊNG THEO TIỀN TỐ ĐÃ ĐIỀN, tức bảng `tabSeries` giữ một dòng
tên `LSX-26-08-` và một dòng khác tên `LSX-26-09-`. Nên sang tháng là số tự
quay về 0001, không cần ai đặt lại tay. Đó chính là câu "đánh số lại theo
từng tháng".

Phiếu CŨ giữ nguyên mã cũ
-------------------------
Đổi chuỗi đặt tên chỉ đổi mã của phiếu SINH RA TỪ ĐÂY VỀ SAU. Toàn bộ lệnh
đang mang mã `MFG-WO-2026-00xxx` và phiếu `MFG-PP-2026-00001` vẫn giữ tên
cũ. Đổi tên một chứng từ đã ghi sổ là sửa dữ liệu quá khứ: bút toán kho, mẻ
hàng, phiếu yêu cầu đều trỏ về tên đó. Luật của tiệm là không tự sửa dữ
liệu cũ, nên máy KHÔNG đổi tên phiếu cũ, chỉ báo lại số phiếu cũ còn mang
mã kiểu cũ.

Vì sao chuỗi cũ vẫn nằm trong danh sách chọn
--------------------------------------------
Ô `naming_series` là ô Select. Phiếu cũ đang giữ giá trị `MFG-WO-.YYYY.-`.
Bỏ giá trị đó khỏi danh sách thì mở phiếu cũ trên Desk là Frappe báo giá
trị không hợp lệ, sửa một ô bất kỳ cũng không lưu được. Nên chuỗi mới được
đặt lên ĐẦU và làm mặc định, chuỗi cũ vẫn còn ở dưới.
"""

# ------------------------------------------------------------ phần thuần

import re

# Doctype -> tien to moi. Chi hai cai nay, dung them cho vui.
TIEN_TO = {
	"Production Plan": "KHSX",
	"Work Order": "LSX",
}


def chuoi_ma(tien_to):
	"""Chuỗi đặt tên của Frappe cho một tiền tố: KHSX -> KHSX-.YY.-.MM.-.####

	Viết thành hàm riêng chứ không rải chuỗi khắp nơi, vì sai một dấu chấm
	là Frappe hiểu thành chữ thường: `.YY-` (thiếu dấu chấm đóng) cho ra mã
	có đúng chữ "YY" nằm trong tên phiếu, mà tên phiếu thì không sửa lại
	được.
	"""
	tien_to = (tien_to or "").strip().upper()
	if not tien_to:
		return ""
	return "%s-.YY.-.MM.-.####" % tien_to


def gop_chuoi(moi, cu):
	"""Danh sách chuỗi đặt tên: chuỗi mới lên đầu, chuỗi cũ giữ nguyên ở dưới.

	Giữ chuỗi cũ vì phiếu cũ đang mang giá trị đó trong ô Select; xem phần
	đầu tệp. Không nhân bản nếu chuỗi mới đã có sẵn trong danh sách.
	"""
	cu_dong = [d.strip() for d in (cu or "").replace("\r", "").split("\n")]
	cu_dong = [d for d in cu_dong if d]
	ra = [moi] if moi else []
	for d in cu_dong:
		if d not in ra:
			ra.append(d)
	return "\n".join(ra)


def la_ma_kieu_moi(ten, tien_to):
	"""Mã này đã theo kiểu mới chưa: LSX-26-08-0001 đúng, LSX-2026-00113 chưa.

	Chỉ so tiền tố là KHÔNG đủ. Lệnh sản xuất trước đây đã mang chuỗi
	`LSX-.YYYY.-`, tức mã cũ `LSX-2026-00113` cũng bắt đầu bằng "LSX-" y
	như mã mới. Đếm kiểu đó thì `soat_ma_cu` báo không còn mã cũ nào trong
	khi thực tế còn 48 lệnh. Nên soi đúng hình dạng: tiền tố, hai chữ số
	năm, hai chữ số tháng, rồi mới tới bộ đếm.
	"""
	ten = (ten or "").strip().upper()
	tien_to = (tien_to or "").strip().upper()
	if not ten or not tien_to:
		return False
	return bool(re.match(r"^%s-\d{2}-\d{2}-\d+$" % re.escape(tien_to), ten))


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint


def dung():
	"""Đặt chuỗi đặt tên mới cho hai doctype. Gọi từ after_migrate.

	Lặp lại được không giới hạn lần: `make_property_setter` ghi đè đúng một
	bản ghi, chạy lần thứ mười cũng ra cùng kết quả.
	"""
	ra = {}
	for dt, tt in TIEN_TO.items():
		try:
			ra[dt] = _dat_mot(dt, tt)
		except Exception:
			# Hong o day KHONG duoc chan ca lan migrate: site khong len duoc
			# phien ban moi thi ca tiem dung, ma loi that chi la ma phieu
			# van mang tien to cu.
			frappe.log_error(frappe.get_traceback(), "ma_phieu_sx: %s" % dt)
			ra[dt] = "loi"
	return ra


def _dat_mot(dt, tien_to):
	"""Đặt chuỗi mới cho MỘT doctype. Trả về chữ mô tả việc đã làm."""
	from frappe.custom.doctype.property_setter.property_setter import (
		make_property_setter,
	)

	if not frappe.db.exists("DocType", dt):
		return "khong co doctype"

	meta = frappe.get_meta(dt)
	o = meta.get_field("naming_series")
	if not o:
		# Doctype nay khong dat ten bang naming_series thi doi chuoi la vo
		# nghia. Bao ra chu khong am tham lam gi ca.
		return "khong co o naming_series"

	dat_ten = (meta.autoname or "").strip().lower()
	if not dat_ten.startswith("naming_series"):
		# ERPNext co the doi cach dat ten giua cac ban. Ghi chuoi vao mot o
		# khong ai doc toi thi ma van ra kieu cu ma minh lai tuong da xong.
		return "autoname khong theo naming_series (%s)" % (meta.autoname or "")

	moi = chuoi_ma(tien_to)
	cu = o.options or ""
	gop = gop_chuoi(moi, cu)
	if gop != cu:
		make_property_setter(dt, "naming_series", "options", gop, "Text",
			validate_fields_for_doctype=False)
	if (o.default or "") != moi:
		make_property_setter(dt, "naming_series", "default", moi, "Text",
			validate_fields_for_doctype=False)
	frappe.clear_cache(doctype=dt)
	return "da dat %s" % moi


@frappe.whitelist()
def soat_ma_cu():
	"""Đếm xem còn bao nhiêu phiếu mang mã kiểu cũ, để anh Việt biết mà đọc.

	KHÔNG đổi tên phiếu nào. Đổi tên chứng từ đã ghi sổ là sửa dữ liệu quá
	khứ; việc của hàm này chỉ là đếm và kể ra vài mã đầu tiên.
	"""
	if not set(frappe.get_roles()) & {"System Manager", "Manufacturing Manager",
			"Giám đốc", "AP Giám đốc"}:
		frappe.throw("Bạn chưa được cấp quyền xem mục này.")
	ra = []
	for dt, tt in TIEN_TO.items():
		if not frappe.db.exists("DocType", dt):
			continue
		ds = frappe.get_all(dt, fields=["name"], limit_page_length=0)
		cu = [d["name"] for d in ds if not la_ma_kieu_moi(d["name"], tt)]
		ra.append({"doctype": dt, "tien_to": tt, "tong": len(ds),
			"con_ma_cu": len(cu), "vai_ma": sorted(cu)[:5]})
	return ra
