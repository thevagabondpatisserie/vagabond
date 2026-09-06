# -*- coding: utf-8 -*-
"""Mã phiếu kế hoạch sản xuất và lệnh sản xuất, đọc ra thấy ngay ngày tháng.

Anh Việt 30/08/2026: "đổi tiền tố mã của phiếu kế hoạch sản xuất thay vì là
MFG- thì đổi thành KHSX-26-08-0001 để thấy rõ tháng năm. Cả lệnh sản xuất
cũng nên là LSX-26-08-0001, rồi đánh số lại theo từng tháng."

Khải 06/09/2026 (#206) muốn lệnh sản xuất chi tiết hơn: LSX-ddmmyy-xxxxxx,
sáu số đánh lại từ đầu khi sang ngày. Anh Việt chốt cùng ngày: phần ngày là
NGÀY TẠO LỆNH theo múi giờ site, không phải ngày dự kiến sản xuất. Lệnh tạo
06/09/2026 mang mã LSX-060926-000001 và GIỮ mã đó dù hoàn tất ngày 07/09.
Phiếu sinh ra lúc hoàn tất là Stock Entry (Manufacture) và Batch, hai cái đó
có mã riêng của chúng, tệp này không đụng tới.

Kế hoạch sản xuất (KHSX) GIỮ NGUYÊN kiểu theo tháng: issue không yêu cầu đổi,
và đổi chung một hàm cho cả hai doctype là cách dễ nhất để vô tình đổi cả
KHSX. Nên mỗi doctype có chuỗi riêng, xem `chuoi_cua`.

Vì sao chuỗi có dấu chấm
------------------------
Frappe đọc `.DD.`, `.MM.`, `.YY.` trong chuỗi đặt tên là "điền hai chữ số
ngày / tháng / năm", còn `.####` hay `.######` là bộ đếm bốn hay sáu chữ số.
Nên `KHSX-.YY.-.MM.-.####` cho ra `KHSX-26-09-0001`, và
`LSX-.DD.MM.YY.-.######` cho ra `LSX-060926-000001`. Ngày lấy từ đồng hồ
máy chủ theo múi giờ site, không lấy đồng hồ trình duyệt.

Bộ đếm ĐẾM RIÊNG THEO TIỀN TỐ ĐÃ ĐIỀN, tức bảng `tabSeries` giữ một dòng
tên `KHSX-26-08-`, một dòng `KHSX-26-09-`, và với lệnh sản xuất là một dòng
cho MỖI NGÀY như `LSX-060926-`. Nên sang tháng (KHSX) hay sang ngày (LSX) là
số tự quay về 1, không cần ai đặt lại tay, và hai người tạo cùng lúc vẫn không
trùng vì Frappe khoá dòng đếm khi cấp số.

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

# Doctype nào đánh số theo NGÀY. Còn lại theo tháng. Chỉ Work Order, theo
# đúng quyết định 06/09/2026; KHSX không nằm đây.
THEO_NGAY = ("Work Order",)


def chuoi_ma_ngay(tien_to):
	"""Chuỗi đặt tên theo ngày: LSX -> LSX-.DD.MM.YY.-.######

	Ba mã ngày tháng năm đứng liền nhau không có dấu gạch, vì Khải vẽ
	`LSX-ddmmyy-xxxxxx`. Frappe tách chuỗi theo dấu chấm nên `.DD.MM.YY.`
	vẫn là ba phần riêng, không cần dấu chấm kép.
	"""
	tien_to = (tien_to or "").strip().upper()
	if not tien_to:
		return ""
	return "%s-.DD.MM.YY.-.######" % tien_to


def chuoi_cua(doctype):
	"""Chuỗi đặt tên đúng cho MỘT doctype. Nguồn duy nhất, `_dat_mot` gọi đây.

	Work Order theo ngày, Production Plan theo tháng. Doctype lạ trả rỗng.
	"""
	tt = TIEN_TO.get(doctype)
	if not tt:
		return ""
	return chuoi_ma_ngay(tt) if doctype in THEO_NGAY else chuoi_ma(tt)


def chuoi_ma(tien_to):
	"""Chuỗi đặt tên theo tháng cho một tiền tố: KHSX -> KHSX-.YY.-.MM.-.####

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


def la_ma_theo_ngay(ten, tien_to):
	"""Mã này theo kiểu ngày chưa: LSX-060926-000001 đúng, LSX-26-09-0001 chưa.

	Sáu chữ số ngày tháng năm liền nhau, gạch, rồi bộ đếm. Chỉ so tiền tố là
	không đủ, cùng lý do với `la_ma_kieu_moi`.
	"""
	ten = (ten or "").strip().upper()
	tien_to = (tien_to or "").strip().upper()
	if not ten or not tien_to:
		return False
	return bool(re.match(r"^%s-\d{6}-\d+$" % re.escape(tien_to), ten))


def ngay_tao_trong_ma(ten, tien_to):
	"""Đọc ngày tạo từ mã kiểu ngày: LSX-060926-000001 -> "2026-09-06". THUẦN.

	Mã không theo kiểu ngày, hoặc sáu số không phải một ngày có thật
	(LSX-320926-...), trả về "" chứ không đoán. Dùng để màn hình hiện
	"tạo ngày 06/09" mà không phải hỏi máy chủ thêm một lượt.
	"""
	if not la_ma_theo_ngay(ten, tien_to):
		return ""
	so = ten.strip().upper().split("-")[1]
	dd, mm, yy = int(so[0:2]), int(so[2:4]), int(so[4:6])
	import datetime
	try:
		return datetime.date(2000 + yy, mm, dd).isoformat()
	except ValueError:
		return ""


def la_ma_kieu_moi(ten, tien_to):
	"""Mã này đã theo kiểu mới chưa. Kiểu mới có HAI dạng, cả hai đều tính:
	theo tháng `LSX-26-08-0001` (30/08 tới 06/09/2026) và theo ngày
	`LSX-060926-000001` (từ 06/09/2026). `LSX-2026-00113` là kiểu cũ.

	Chỉ so tiền tố là KHÔNG đủ. Lệnh sản xuất trước đây đã mang chuỗi
	`LSX-.YYYY.-`, tức mã cũ `LSX-2026-00113` cũng bắt đầu bằng "LSX-" y
	như mã mới. Đếm kiểu đó thì `soat_ma_cu` báo không còn mã cũ nào trong
	khi thực tế còn 48 lệnh. Nên soi đúng hình dạng.
	"""
	ten = (ten or "").strip().upper()
	tien_to = (tien_to or "").strip().upper()
	if not ten or not tien_to:
		return False
	if la_ma_theo_ngay(ten, tien_to):
		return True
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

	moi = chuoi_cua(dt)
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
