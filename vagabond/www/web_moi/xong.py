"""Biên nhận Vue song song, dùng dữ liệu tối thiểu của backend cũ."""
import frappe
from vagabond import don_web, trang_khach, noi_dung_web, web_vue
from vagabond.www.banh.xong import TIEU_DE
no_cache = 1
sitemap = 0


def get_context(context):
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.local.no_cache = 1
    frappe.local.response_headers.update(TIEU_DE)
    token = str(frappe.form_dict.get('token') or '')
    d = {'loai': 'bien_nhan', 'khong_token': 1}
    if token:
        bn = don_web.bien_nhan_theo_token(token)
        if not bn:
            raise frappe.PageDoesNotExistError
        d = dict(bn, loai='bien_nhan', pixel_id=don_web.pixel_id())
    d['nhan'] = (noi_dung_web.cong_khai().get('nhan') or {})
    lh = don_web.lien_he()
    d['lien_he'] = web_vue.nut_lien_he_bien_nhan(lh, d['nhan'])
    context.du_lieu = trang_khach.json_trong_script(d)
    context.chan_trang = trang_khach.chan_trang_html(don_web.PHAP_NHAN, lh, web_vue.chinh_sach_vue(noi_dung_web.chinh_sach_dang_hien()))
    return context
