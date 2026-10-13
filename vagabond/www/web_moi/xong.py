"""Biên nhận Vue song song, dùng dữ liệu tối thiểu của backend cũ."""
import frappe
from vagabond import don_web, trang_khach, noi_dung_web
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
    d['lien_he'] = [{'href': trang_khach._lien_ket_an_toan(lh.get(k)), 'ten': ten}
                    for k, ten in (('zalo', 'Nhắn Zalo'), ('messenger', 'Nhắn Messenger'))
                    if trang_khach._lien_ket_an_toan(lh.get(k))]
    context.du_lieu = trang_khach.json_trong_script(d)
    context.chan_trang = trang_khach.chan_trang_html(don_web.PHAP_NHAN, don_web.lien_he(), noi_dung_web.chinh_sach_dang_hien())
    return context
