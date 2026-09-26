"""Trang biên nhận /banh/xong/<token> sau khi khách gửi đơn (#367).

Ai cầm đường dẫn là mở được, nên trang chỉ hiện dữ liệu tối thiểu: mã yêu
cầu, tên viết tắt, món, tiền, giờ nhận, cách thanh toán. Không số điện thoại,
không địa chỉ, không email.

Ba lớp giữ token khỏi lọt ra ngoài:
  - Cache-Control no-store và no_cache: không trình duyệt, proxy hay bộ nhớ
    đệm trang của Frappe nào giữ lại bản của khách này cho khách khác. Mọi
    token đều đi vào CÙNG một đường trang "banh/xong", nên chỉ cần một lần
    bị đệm là khách sau thấy biên nhận của khách trước.
  - Referrer-Policy no-referrer: bấm sang Zalo, Messenger không mang theo
    đường dẫn có token.
  - Trình duyệt thay đường dẫn về /banh/xong trước khi nạp Pixel, nên
    PageView gửi Meta không có token (xem bien-nhan.js).
Token sai hay không tồn tại thì trả 404 thật.
"""

import frappe

from vagabond import don_web, noi_dung_web, trang_khach

no_cache = 1
sitemap = 0

TIEU_DE = {
	"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
	"Referrer-Policy": "no-referrer",
	"X-Robots-Tag": "noindex, nofollow",
}


def get_context(context):
	frappe.local.no_cache = 1
	context.no_cache = 1
	frappe.local.response_headers.update(TIEU_DE)
	token = str(frappe.form_dict.get("token") or "")
	lien_he = don_web.lien_he()
	context.chan_trang = trang_khach.chan_trang_html(
		don_web.PHAP_NHAN, lien_he, noi_dung_web.chinh_sach_dang_hien())
	if not token:
		# /banh/xong khong token: khach vua tai lai trang sau khi trinh duyet
		# da go token khoi duong dan. Trang tu doc lai ban tom tat trong bo nho
		# phien cua chinh tab do (bien-nhan.js); tab khac thi bao tim tin nhan.
		context.than = ""
		context.du_lieu = trang_khach.json_trong_script({"khong_token": 1})
		return context
	bn = don_web.bien_nhan_theo_token(token)
	if not bn:
		raise frappe.PageDoesNotExistError
	context.than = trang_khach.bien_nhan_html(bn["bien_nhan"], lien_he)
	context.du_lieu = trang_khach.json_trong_script({
		"pixel_id": don_web.pixel_id(),
		"su_kien": bn["su_kien"],
		"than": context.than,
	})
	return context
