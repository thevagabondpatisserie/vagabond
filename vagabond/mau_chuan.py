# -*- coding: utf-8 -*-
"""Khuôn chuẩn cho MỌI bản in hồ sơ thanh toán trên APP.

Vì sao có tệp này
-----------------
Anh Việt 22/08/2026, khi giao việc siết hồ sơ hoàn ứng:

  "Bốc thiết kế Song ngữ và Block chữ ký này làm chuẩn chung (Standard
  Template) để áp dụng cho tất cả các loại hồ sơ thanh toán khác trên APP
  sau này."

Trước tệp này mỗi bản in tự dựng dải logo, tự đặt cỡ chữ, tự vẽ ô chữ ký.
Hệ quả đã thấy: tờ đề nghị thanh toán và mẫu in chứng từ thanh toán để cạnh
nhau trông như hai công ty khác nhau, và sửa quy ước trình bày một lần thì
phải đi sửa từng tệp một, sót chỗ nào thì chỗ đó lệch mãi.

Nay mọi bản in gọi vào đây. Đổi cách trình bày thì đổi ở một chỗ.

Quy ước song ngữ, anh Việt chốt 22/08/2026
------------------------------------------
Tiếng Anh KHÔNG nằm cùng dòng với tiếng Việt và KHÔNG ngăn bằng gạch chéo.
Tiếng Anh xuống dòng riêng ngay dưới, luôn in nghiêng, cỡ chữ nhỏ hơn, màu
nhạt hơn. Dấu hai chấm chỉ đặt ở dòng tiếng Việt.

Vì sao: bản in này gửi cho cả kế toán Việt và đối tác nước ngoài. Gạch chéo
làm hai thứ tiếng dính vào nhau thành một khối khó đọc cho cả hai bên, mà
tiếng Việt là tiếng chính thì phải nổi hơn.

Phông chữ
---------
Từ 31/08/2026 xâu phông KHÔNG còn viết tay ở đây nữa mà lấy thẳng từ
`vagabond/phong_chu.py`, nơi duy nhất khai phông của cả ứng dụng. Trước đó
xâu này bị chép tay ở BỐN tệp khác nhau, và tệp thứ năm là `nop_quy.py` thì
lại khai `Times New Roman` - phông máy chủ không có - nên tờ Biên bản bàn
giao tiền mặt in ra vỡ hết dấu tiếng Việt.

Điều không đổi: phông có đủ dấu tiếng Việt phải đứng TRƯỚC Arial. Đặt Arial
lên đầu là ra bản in mất dấu, đã gặp một lần.
"""

import frappe

from vagabond.phong_chu import NGAN_XEP as PHONG

# Xâu phông cho THƯ ĐIỆN TỬ. Khác hẳn phông bản in, và khác có chủ ý.
#
# Thư hiện trên máy NGƯỜI NHẬN, không đi qua wkhtmltopdf, nên không dính
# chuyện máy chủ thiếu phông. Ngược lại, nhét một cái tên phông máy người ta
# không có vào thư là hộp thư nào cũng tự chọn một phông khác, mỗi nơi một
# kiểu. Arial thì máy nào cũng có.
#
# Khai ở đây thay vì gõ tay trong từng tệp, để bộ ca kiểm phông phân biệt
# được đâu là bản in đâu là thư, và bắt đúng chỗ sai.
PHONG_THU = "Arial,Helvetica,sans-serif"
VIEN = "1px solid #c9c4bd"

CONG_TY = {
	"ten": "CÔNG TY TNHH PATISSERIE VAGABOND",
	"ten_en": "VAGABOND PATISSERIE CO., LTD",
	"mst": "0318561568",
	"dia_chi": "9 Trần Cao Vân, Phường Sài Gòn, TP.HCM",
	"web": "www.thevagabondpatisserie.com",
	"logo": "/files/vagabond_logo_print.png",
}


def sn(vi, en, co_vi=None, co_en=None, mau_en="#666"):
	"""Một nhãn song ngữ: tiếng Việt trên, tiếng Anh nghiêng ở dòng dưới.

	Dùng cho nhãn cột, nhãn trường, tiêu đề. KHÔNG dùng gạch chéo, không ghép
	hai thứ tiếng vào một dòng - xem phần quy ước ở đầu tệp.
	"""
	h = frappe.utils.escape_html
	ra = '<span style="font-size:%s">%s</span>' % (co_vi or "inherit", h(vi))
	if en:
		ra += (
			'<span style="display:block;font-style:italic;font-weight:normal;'
			'font-size:%s;color:%s;line-height:1.3">%s</span>'
			% (co_en or "0.86em", mau_en, h(en))
		)
	return ra


def dai_logo():
	"""Dải đầu trang: logo bên trái, khối thông tin công ty bên phải."""
	c = CONG_TY
	return (
		'<table style="width:100%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;width:45%;vertical-align:middle">'
		'<img src="' + c["logo"] + '" width="150" height="62" '
		'style="width:150px !important;height:62px !important;object-fit:contain">'
		"</td>"
		'<td style="border:none;text-align:right;vertical-align:middle;font-size:9.5px;'
		'color:#444;line-height:1.5">'
		'<b style="font-size:10.5px;color:#1c1a17">' + c["ten"] + "</b>"
		'<div style="font-style:italic;font-size:9px;color:#777">' + c["ten_en"] + "</div>"
		"MST / Tax code: " + c["mst"] + "<br>"
		+ c["dia_chi"] + "<br>" + c["web"] +
		"</td></tr></table>"
	)


def tieu_de(vi, en, so=None, ngay=None):
	"""Khối tiêu đề giữa trang, kèm số chứng từ và ngày."""
	h = frappe.utils.escape_html
	ra = (
		'<div style="text-align:center;margin:14px 0 2px">'
		'<div style="font-size:19px;font-weight:bold;letter-spacing:1px">%s</div>'
		'<div style="font-size:11.5px;font-style:italic;color:#666;margin-top:1px">%s</div>'
		% (h(vi), h(en))
	)
	if so or ngay:
		ra += (
			'<div style="font-size:11px;color:#555;margin-top:4px">'
			"Số / No.: <b>%s</b> &nbsp;·&nbsp; Ngày / Date: <b>%s</b></div>"
			% (h(so or ""), h(ngay or ""))
		)
	return ra + "</div>"


# Ba chữ ký chuẩn của mọi hồ sơ thanh toán, đúng thứ tự duyệt trong hệ:
# người lập hồ sơ ký trước, kế toán trưởng kiểm, giám đốc duyệt cuối.
CHU_KY_CHUAN = (
	("NGƯỜI ĐỀ NGHỊ", "Requested by"),
	("KẾ TOÁN TRƯỞNG", "Chief Accountant"),
	("GIÁM ĐỐC", "Director"),
)


def khoi_chu_ky(ten_theo_chuc=None, cot=None):
	"""Block chữ ký tiêu chuẩn ở cuối bản in.

	ten_theo_chuc: {"NGƯỜI ĐỀ NGHỊ": "Nguyễn Văn A", ...} - tên nào chưa có
	thì để trống chỗ đó cho người ta ký tay, KHÔNG bịa tên vào.

	cot: truyền bộ khác nếu một loại hồ sơ cần chức danh khác. Mặc định là
	ba chức danh chuẩn ở trên.
	"""
	h = frappe.utils.escape_html
	cot = cot or CHU_KY_CHUAN
	ten_theo_chuc = ten_theo_chuc or {}
	rong = 100.0 / max(1, len(cot))
	o = []
	for vi, en in cot:
		o.append(
			'<td style="border:none;width:%.2f%%;text-align:center;vertical-align:top">'
			'<div style="font-size:11px;font-weight:bold;letter-spacing:.4px">%s</div>'
			'<div style="font-size:9.5px;font-style:italic;color:#666">%s</div>'
			'<div style="font-size:9px;color:#888;margin-top:2px">Ký, ghi rõ họ tên</div>'
			'<div style="font-size:8.5px;font-style:italic;color:#999">Signature and full name</div>'
			'<div style="height:62px"></div>'
			'<div style="font-size:11px;font-weight:bold">%s</div></td>'
			% (rong, h(vi), h(en), h(ten_theo_chuc.get(vi) or ""))
		)
	return (
		'<table style="width:100%;border:none;border-collapse:collapse;margin-top:26px">'
		"<tr>" + "".join(o) + "</tr></table>"
	)


def o_th(vi, en):
	"""Ô tiêu đề cột của bảng, song ngữ."""
	return (
		'<th style="border:%s;padding:6px 7px;background:#f3f0ec;font-size:10.5px;'
		'font-weight:bold;text-align:center">%s</th>' % (VIEN, sn(vi, en, co_en="9px"))
	)


def khung_trang(noi_dung, tieu_de_tep="", le="12mm"):
	"""Bọc nội dung vào một trang A4 dọc hoàn chỉnh, sẵn sàng đưa qua get_pdf.

	MỌI tờ PDF của ứng dụng phải đi qua đây. Hai việc cửa này làm hộ, và cả
	hai đều là thứ dễ quên khi tự dựng khung:

	  1. Chép bộ phông Vagabond Sans vào thư mục phông của người dùng trên
	     máy chủ. Mỗi lần deploy là một container mới, không chép thì phông
	     biến mất và tờ in vỡ dấu.
	  2. Ép phông cho CẢ tờ bằng `*`, không chỉ đặt trên `body`.

	Hàm chép phông không bao giờ ném lỗi: hỏng thì tờ vẫn in ra được, chỉ là
	xấu phông trở lại như cũ.
	"""
	h = frappe.utils.escape_html
	try:
		from vagabond.phong_chu import bao_dam_phong

		bao_dam_phong()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "mau_chuan: bao dam phong")
	return (
		"<html><head><meta charset='utf-8'><title>%s</title><style>"
		"@page{size:A4 portrait;margin:%s}"
		"*{font-family:%s}"
		"body{margin:0;color:#1c1a17}"
		"table{page-break-inside:auto}tr{page-break-inside:avoid}"
		"img{max-width:100%%}"
		"</style></head><body>%s</body></html>"
		% (h(tieu_de_tep), le, PHONG, noi_dung)
	)


def an_phan_tram(s):
	"""Nhân đôi dấu % để chuỗi HTML này đi qua được một khuôn định dạng %.

	Vì sao cần
	----------
	Mọi hàm trong tệp này trả về HTML có CSS, mà CSS đầy `width:45%`. Ghép
	một chuỗi như thế VÀO GIỮA một khuôn định dạng `%` thì Python đọc `%;`
	thành một lệnh định dạng và nổ "unsupported format character".

	Ngày 22/08/2026 đã dính đúng cái bẫy này: `dai_logo()` ghép thẳng vào
	khuôn của tờ đề nghị, nút Xuất bộ hồ sơ chết, kế toán bấm ra lỗi 500.

	CÁCH ĐÚNG là định dạng trước rồi mới nối chuỗi, hoặc truyền mảnh HTML
	qua `%s`. Hàm này chỉ dành cho chỗ nào bắt buộc phải ghép thẳng.
	"""
	return str(s or "").replace("%", "%%")
