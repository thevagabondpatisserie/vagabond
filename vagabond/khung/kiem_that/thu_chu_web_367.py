"""#367: lưu nháp/xuất bản chữ qua Document thật, chỉ trên bench CI riêng."""
import copy
import json

import frappe
from vagabond import noi_dung_web as w
from vagabond.khung.kiem_that.nen import ca, dung, la, _DA_TAO


@ca('367 CMS thật: nháp không lộ, xuất bản đọc lại được, chặn phiên bản cũ')
def _luu_chu():
    # Không sửa bản ghi nội dung trên một site kinh doanh, dù có rollback.
    if frappe.local.site != 'bench-ci.localhost':
        dung('không phải bench CI riêng: không sửa nội dung web', True)
        return
    if not frappe.db.exists(w.DOCTYPE, w.TEN):
        w.gieo_tu_tep()
        _DA_TAO.append((w.DOCTYPE, w.TEN))
    cu = w.doc_bang()
    nd = copy.deepcopy(cu['nhap'])
    nd['nhan'] = {'them_nhanh_mon':'Chọn {ten} cho quý khách'}
    nd['san_pham'] = {'BAWC00139':{'ten':'Tên thử <b>giữ là chữ</b>', 'mo_ta':'Mô tả thử'}}
    r = w.luu(json.dumps(nd), cu['phien_ban'], 'nhap')
    d = frappe.get_doc(w.DOCTYPE, w.TEN)
    la('đọc lại nháp có chữ', json.loads(d.ban_nhap)['san_pham'], nd['san_pham'])
    la('nháp chưa ra công khai', json.loads(d.ban_cong_khai), cu['cong_khai'])
    chan = False
    try:
        w.luu(json.dumps(nd), cu['phien_ban'], 'xuat_ban')
    except frappe.ValidationError:
        chan = True
    dung('chặn phiên bản cũ', chan)
    w.luu(json.dumps(nd), r['phien_ban'], 'xuat_ban')
    d = frappe.get_doc(w.DOCTYPE, w.TEN)
    la('xuất bản giữ nội dung', json.loads(d.ban_cong_khai)['san_pham'], nd['san_pham'])
    la('public nhận nhãn mới', w.cong_khai()['nhan']['them_nhanh_mon'], nd['nhan']['them_nhanh_mon'])
    la('lịch sử giữ bản trước', json.loads(d.lich_su)[0]['noi_dung'], cu['cong_khai'])
