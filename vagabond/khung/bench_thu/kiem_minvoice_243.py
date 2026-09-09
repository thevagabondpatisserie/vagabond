"""#243: hai cửa phát hành phải thật sự gửi hai SI độc lập tới HTTP giả.

Chỉ bench riêng. Chạy trọn Python và Server Script execute_method/safe_exec,
không thay helper tính tiền. Khóa mọi HTTP requests còn lại và hoàn nguyên
DB/callback bằng khung cách ly. Kịch bản nạp Pancake cũng thực thi thật.
"""
import json
from unittest.mock import patch

import frappe
import requests
from frappe.integrations import utils as tich_hop
from frappe.utils.password import set_encrypted_password
from vagabond import ban_hang, minvoice_kich_ban as kich_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon
from vagabond.thue_vnd import doc_dong


def _bang(nhan, duoc, mong):
    if duoc != mong:
        raise AssertionError('%s: %r != %r' % (nhan, duoc, mong))


def _hoa_don():
    ct, tk, mau = _nen()
    ma = 'KT243-' + frappe.generate_hash(length=12)
    hd = frappe.get_doc(dict(doctype='Sales Invoice', company=ct, currency='VND', conversion_rate=1,
        customer=frappe.db.get_value('Customer', {'disabled':0,'is_internal_customer':0}, 'name'),
        custom_nguon='Pancake', custom_pancake_display_id=ma, custom_pancake_id=ma,
        vgb_pt_thanh_toan='Chuyển khoản', taxes_and_charges=mau.name,
        apply_discount_on='Grand Total', discount_amount=777,
        items=[dict(item_code=_mon(tk,8),qty=1,rate=150000),
               dict(item_code=_mon(tk,10),qty=1,rate=70000)]))
    hd.flags.ignore_permissions = True
    hd.insert(ignore_permissions=True)
    nen._DA_TAO.append((hd.doctype, hd.name))
    hd.submit()
    hd.reload()
    _bang('gross sau giảm', hd.grand_total, 219223)
    return hd


def _cau_hinh():
    for dt, vals in (
        ('Vagabond Settings', dict(minvoice_host='https://minvoice.invalid', minvoice_username='kiem',
          minvoice_series='1C26TAA', pancake_shop_id='kiem243', tu_xuat_hddt=0)),
        ('MInvoice Phat Hanh Settings', dict(api2_base='https://minvoice.invalid', api2_username='kiem',
          ky_hieu='1C26TAA', thue_suat=8, ma_hang_gop='', nguon='Pancake'))):
        for k,v in vals.items():
            frappe.db.set_single_value(dt,k,v)
        frappe.clear_document_cache(dt,dt)
    for dt, field in (('Vagabond Settings','minvoice_password'),
                      ('Vagabond Settings','pancake_api_key'),
                      ('MInvoice Phat Hanh Settings','api2_password')):
        set_encrypted_password(dt,dt,'mat-khau-gia',field)
    # Lưu Single theo cửa Document như cấu hình ở Desk, rồi đọc lại cả
    # trường thường và mật khẩu. Không đợi script nuốt mất lỗi nền.
    st = frappe.get_doc('MInvoice Phat Hanh Settings')
    st.api2_base = 'https://minvoice.invalid'
    st.api2_username = 'kiem'
    st.api2_password = 'mat-khau-gia'
    st.save(ignore_permissions=True)
    st = frappe.get_doc('MInvoice Phat Hanh Settings')
    _bang('base phát hành đọc lại', st.api2_base, 'https://minvoice.invalid')
    _bang('user phát hành đọc lại', st.api2_username, 'kiem')
    _bang('mật khẩu giả đọc lại', bool(st.get_password('api2_password', raise_exception=False)), True)
    for ten, loai, _cu, _sua in kich_ban.BO:
        ma = frappe.db.get_value('Server Script',ten,'script')
        _bang('script đã migrate '+loai, ma, kich_ban.ban_moi(loai))


def _doi_chieu(hd, goi):
    hd.reload()
    dd = goi['data'][0]
    ds = [d for nhom in dd['details'] for d in nhom['data']]
    da_luu = doc_dong(hd)
    _bang('số dòng',len(ds),len(hd.items))
    for i,(gui,luu,it) in enumerate(zip(ds,da_luu,hd.items),1):
        _bang('mã dòng %s'%i,gui['inv_itemCode'],it.item_code)
        _bang('qty dòng %s'%i,gui['inv_quantity'],it.qty)
        for khoa, cot in (('net','inv_TotalAmountWithoutVat'),('vat','inv_vatAmount'),('gross','inv_TotalAmount')):
            _bang('%s dòng %s'%(khoa,i),gui[cot],luu[khoa])
        _bang('thuế suất dòng %s'%i,gui['ma_thue'],luu['rate'])
    for cot,gia in (('inv_TotalAmountWithoutVat',hd.net_total),
                    ('inv_vatAmount',hd.total_taxes_and_charges),('inv_TotalAmount',hd.grand_total)):
        _bang(cot,dd[cot],gia)
    _bang('khóa theo SI',dd['key_api'],hd.name)
    return dict(phieu=hd.name, net=hd.net_total, vat=hd.total_taxes_and_charges,
                gross=hd.grand_total, dong=da_luu)


def chay():
    if not frappe.conf.get('vagabond_bench_thu'):
        raise RuntimeError('Chỉ chạy kiem_minvoice_243 trên bench riêng vagabond_bench_thu=1.')
    form_cu = getattr(frappe.local,'form_dict',None)
    dap_cu = getattr(frappe.local,'response',None)
    gui, nap = [], []

    def chan(*a,**kw):
        raise AssertionError('HTTP ngoài stub bị chặn trong bench #243')

    def post(url,data=None,**kw):
        if url == 'https://minvoice.invalid/api/Account/Login':
            return dict(ok=True,code='00',token='token-gia')
        if url == 'https://minvoice.invalid/api/InvoiceApi78/Save':
            goi = kw.get('json') if 'json' in kw else json.loads(data)
            gui.append(goi)
            return dict(ok=True,code='00',data=dict(inv_invoiceAuth_id='KT243-'+str(len(gui)),inv_invoiceNumber=str(len(gui))))
        return chan()

    class PhanHoi:
        def __init__(self,than): self.than=than
        def json(self): return self.than
        def raise_for_status(self): pass

    def post_python(url,**kw): return PhanHoi(post(url,**kw))

    def get(url,**kw):
        dau='https://pos.pages.fm/api/v1/shops/kiem243/orders/'
        if url.startswith(dau):
            ma=url[len(dau):]
            nap.append(ma)
            return dict(success=True,data=dict(id=ma,display_id=ma,
                note_print='Tên khách: Khách kiểm thử 243'))
        return chan()

    def script(ten,phieu):
        frappe.local.form_dict=frappe._dict(phieu=phieu,che_do='day',khong_commit=1)
        frappe.local.response=frappe._dict(docs=[])
        frappe.get_doc('Server Script',ten).execute_method()
        return dict(frappe.local.response.get('message') or {})

    kq=[]
    try:
        with patch.object(requests.sessions.Session,'request',chan), \
             patch.object(ban_hang.requests,'post',post_python), \
             patch.object(tich_hop,'make_post_request',post), \
             patch.object(tich_hop,'make_get_request',get), nen._cach_ly():
            diem='minvoice243_'+frappe.generate_hash(length=8)
            frappe.db.savepoint(diem)
            try:
                _cau_hinh()
                # Mỗi cửa có SI riêng: ID từ cửa trước không được làm cửa sau bỏ qua.
                for cua in ('tay_python','rai_server_script'):
                    hd=_hoa_don()
                    truoc_gui=len(gui); truoc_nap=len(nap)
                    # Chỉ mở cờ sau khi toàn bộ HTTP đã bị thay bằng stub.
                    # Không sửa guard production để làm cho ca kiểm xanh.
                    frappe.flags.vagabond_kiem_that=False
                    try:
                        if cua=='tay_python':
                            ra=script(kich_ban.TEN_NAP,hd.name)
                            _bang('nạp không lỗi',ra.get('loi') or [],[])
                            hd.reload()
                            _bang('nạp đúng khách',hd.vgb_xhd_ten,'Khách kiểm thử 243')
                            ban_hang.xuat_hoa_don_dien_tu(hd.name)
                        else:
                            ra=script(kich_ban.TEN_PHAT_HANH,hd.name)
                            if ra.get('loi'):
                                raise AssertionError('Server Script phát hành: ' + json.dumps(ra, ensure_ascii=False, default=str))
                            _bang('script tạo 1',ra.get('tao_ok'),1)
                    finally:
                        frappe.flags.vagabond_kiem_that=True
                    _bang('cửa gửi đúng một payload',len(gui)-truoc_gui,1)
                    _bang('nạp đúng SI riêng',nap[truoc_nap:],[hd.custom_pancake_id])
                    dong=_doi_chieu(hd,gui[-1]); dong['cua']=cua
                    _bang('ID ghi xuống DB',bool(hd.get('custom_hddt_id') or hd.get('custom_minvoice_id')),True)
                    _bang('cờ đối chiếu đã gỡ',int(hd.get('vgb_hddt_cho_doi_chieu') or 0),0)
                    kq.append(dong)
                _bang('hai SI độc lập',len({x['phieu'] for x in kq}),2)
            finally:
                frappe.db.rollback(save_point=diem)
        for d in kq:
            _bang('SI thử đã hoàn nguyên',bool(frappe.db.exists('Sales Invoice',d['phieu'])),False)
        return dict(dat=True,cac_cua=kq,so_goi=len(gui),nap_pancake=len(nap),http_that=0)
    finally:
        frappe.local.form_dict=form_cu
        frappe.local.response=dap_cu
