"""Trang từng bánh /mon/<mã hàng> (v672): trang đích của bánh đưa lên Google
Merchant Center. Máy chủ dựng sẵn tên, ảnh, giá, tình trạng và dữ liệu có cấu
trúc Product để Google đọc được mà không cần chạy JavaScript.

Chỉ bánh đang có trong tệp /google-merchant.xml mới có trang (cùng một nguồn
google_merchant.mon_dua_google); mã khác trả 404, không lộ hàng nội bộ.
"""
import frappe

from vagabond import don_web, google_merchant as gm, noi_dung_web, trang_khach

no_cache = 1


def get_context(context):
	frappe.local.no_cache = 1
	context.no_cache = 1
	ma = frappe.form_dict.get("ma")
	m = gm.tim(gm.mon_dua_google(), ma)
	if not m:
		raise frappe.PageDoesNotExistError
	e = trang_khach._e
	context.ten = e(m["ten"])
	context.mo_ta = e(m["mo_ta"])
	context.mo_ta_ngan = e(m["mo_ta"][:160])
	context.anh = e(m["anh"])
	context.gia = e(gm.chu_gia(m["gia"]))
	context.tinh_trang = e(gm.chu_tinh_trang(m))
	context.con = m["con"]
	context.nhom = e(gm.TEN_NGUON.get(m["nguon"], ""))
	context.duong = e(gm.duong_mon(m["ma"]))
	context.json_ld = gm.json_ld(m)
	context.chan_trang = trang_khach.chan_trang_html(
		don_web.PHAP_NHAN, don_web.lien_he(), noi_dung_web.chinh_sach_dang_hien())
	return context
