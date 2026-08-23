"""Lề trang và khung CSS dùng chung cho MỌI bản in của tiệm.

Anh Việt 23/08/2026: *"Tất cả các bản in hiện tại đang bị tràn lề (sát mép
giấy) gây mất chữ và thiếu thẩm mỹ."*

VÌ SAO PHẢI CÓ MỘT CHỖ DUY NHẤT
-------------------------------
Trước đây mỗi nơi tự khai lề của mình: `xuat_ho_so` khai 12mm trong chuỗi
HTML của nó, mỗi bản ghi Print Format khai bốn ô margin riêng, mẫu báo giá
lại khai kiểu khác. Ba luật cho cùng một việc thì sớm muộn lệch nhau, và
lệch ở bản in thì chỉ phát hiện được sau khi giấy đã ra khỏi máy.

VÌ SAO 15mm
-----------
Máy in văn phòng thường không in được sát hơn 5mm mỗi mép, máy in nhiệt còn
tệ hơn. 15mm cho vùng in 180x267mm trên khổ A4, thừa chỗ cho đóng ghim mép
trái mà không phải xoay giấy.

VÌ SAO CÓ THÊM PADDING TRONG KHUNG
----------------------------------
wkhtmltopdf tính @page margin theo cách riêng và có bản còn bỏ qua hẳn khi
gặp thẻ chạy ngang trang. Đệm thêm vài mm bên trong khung là hàng rào thứ
hai: mất một hàng rào thì vẫn còn một hàng rào, chữ không bao giờ chạm mép.
"""

import re

# Le giay, dung cho ca @page lan bon o margin cua ban ghi Print Format.
LE_MM = 15

# Vung in that con lai tren A4 doc sau khi tru le hai ben.
RONG_TRONG_MM = 210 - LE_MM * 2      # 180
CAO_TRONG_MM = 297 - LE_MM * 2       # 267


def css_trang(le_mm=LE_MM):
	"""Khối <style> chuẩn cho một tờ in A4 dọc. THUẦN, không chạm Frappe.

	Đặt ở ĐẦU tài liệu in. Ai cần lề khác thì truyền le_mm, đừng chép khối
	này ra chỗ khác rồi sửa - chép ra là bắt đầu có hai luật.
	"""
	return (
		"<style>"
		"@page{size:A4 portrait;margin:%dmm}"
		"html,body{margin:0;padding:0}"
		# Hang rao thu hai: dem trong khung, phong khi wkhtmltopdf bo qua @page.
		".vgb-in{padding:0 2mm;box-sizing:border-box}"
		# Bang dai duoc phep tran sang trang sau, nhung mot HANG thi khong -
		# cat doi mot hang la doc mat mot dong so.
		"table{page-break-inside:auto}tr{page-break-inside:avoid}"
		"img{max-width:100%%}"
		"</style>" % le_mm
	)


# Kho giay duoc phep ap le chung. Ban in khac kho (tem 62x45mm) KHONG duoc
# dinh vao, xem duoc_ap_le_chung().
KHO_A4_A5 = ("a4", "a5")

# Tu khoa trong TEN ban in hoac ten doctype de loai tru thang. Hang rao thu
# nhat, de doc, de kiem.
TU_KHOA_LOAI_TRU = ("tem",)

_RE_PAGE_SIZE = re.compile(r"@page[^{]*\{[^}]*\bsize\s*:\s*([^;}]+)", re.I)


def kho_giay_trong_mau(html):
	"""Doc kho giay ma chinh mau in tu khai trong @page. "" neu khong khai."""
	m = _RE_PAGE_SIZE.search(html or "")
	return " ".join(m.group(1).split()).lower() if m else ""


def duoc_ap_le_chung(ten, doctype="", html=""):
	"""Ban in nay co duoc ap le chung 15mm khong.

	Anh Viet 23/08/2026: *"Le Global 15mm nay chi ap dung cho cac Print
	Format kho A4 hoac A5. Tuyet doi loai tru cac Doctype hoac Print Format
	co ten chua chu Tem."*

	VI SAO CAN HAM NAY. Ban v281 quet theo `name like "Vagabond%"` nen dinh
	ca ba mau tem kho 62x45mm. Lan do khong gay hong vi duong in tem that di
	qua /printview, ma /printview khong nhet bon o margin cua ban ghi vao
	trang. Nhung do la MAY, khong phai thiet ke: he ai sinh PDF tem tu may
	chu la tem bi an 15mm moi canh, mat sach noi dung.

	Hai hang rao, phai qua CA HAI:
	  1. Ten ban in va ten doctype khong chua tu khoa loai tru.
	  2. Neu chinh mau tu khai @page size thi kho do phai la A4 hoac A5.
	     Mau khong khai gi thi coi nhu kho mac dinh, cho qua.
	"""
	goi = ("%s %s" % (ten or "", doctype or "")).lower()
	for tu in TU_KHOA_LOAI_TRU:
		if tu in goi:
			return False
	kho = kho_giay_trong_mau(html)
	if not kho:
		return True
	return kho.split()[0] in KHO_A4_A5
