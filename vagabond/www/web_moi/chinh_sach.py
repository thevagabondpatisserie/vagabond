"""Chính sách Vue: chỉ đọc nội dung đã xuất bản bằng cửa hiện có."""
import frappe
from vagabond import noi_dung_web, trang_khach, don_web, web_vue
no_cache = 1


def get_context(context):
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.local.no_cache = 1
    duong = str(getattr(getattr(frappe.local, 'request', None), 'path', '') or getattr(frappe.local, 'path', ''))
    khoa = noi_dung_web.khoa_tu_duong(duong.removeprefix('/web_moi'))
    context.trang_chu = web_vue.trang_chu_dat_banh(duong)
    ngon = 'en' if frappe.form_dict.get('ngon_ngu') == 'en' else 'vn'
    d = noi_dung_web.trang_chinh_sach(khoa, ngon) if khoa else None
    if not d:
        raise frappe.PageDoesNotExistError
    context.doi_ngon_ngu = web_vue.doi_ngon_ngu_html(duong, d['ngon_ngu'], d['co_en'], noi_dung_web.nhan_cong_khai())
    context.tieu_de = trang_khach._e(d['ten'])
    context.du_lieu = trang_khach.json_trong_script({'loai':'chinh_sach', 'ten':d['ten'], 'mo':d.get('mo',''), 'cay':web_vue.cay_chinh_sach(d['html'])})
    context.chan_trang = trang_khach.chan_trang_html(don_web.PHAP_NHAN, don_web.lien_he(), web_vue.chinh_sach_vue(noi_dung_web.chinh_sach_dang_hien()))
    return context
