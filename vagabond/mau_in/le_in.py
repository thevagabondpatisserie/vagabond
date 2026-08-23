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
