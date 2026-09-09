"""#245: lưu/reload đặt bàn, quyền Guest và hồ sơ theo phiên trên bench riêng.

Không gửi OTP, không gọi Pancake thật. Điểm kiểm giữ dữ liệu trong rollback;
chặn mọi commit của helper phiên cũ trong thời gian dựng fixture.
"""
import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch
import frappe
from vagabond import dat_ban, thanh_vien, dang_nhap


def chay():
    if not frappe.conf.get('vagabond_bench_thu'):
        raise RuntimeError('Chỉ chạy trên bench riêng.')
    nguoi = frappe.session.user
    req = getattr(frappe.local, 'request', None)
    ket = []
    frappe.db.savepoint('web_khach_245')
    def dat(chu, dieu):
        if not dieu: raise AssertionError(chu)
        ket.append(chu)
    def chan(chu, ham):
        try: ham()
        except (frappe.ValidationError, frappe.PermissionError): ket.append(chu); return
        raise AssertionError(chu)
    c = {'bat':True,'co_so':'TCV','khung_gio':['14:00'],'toi_da_khach':8,'toi_da_ngay':30}
    nd = {'ten':'Khách bench #245','sdt':'0912345678','co_so':'TCV','ngay':frappe.utils.add_days(frappe.utils.nowdate(),2),'gio':'14:00','so_khach':2,'ghi_chu':''}
    ma = '24500000-0000-4000-8000-000000000001'
    try:
        frappe.local.request = None
        frappe.set_user('Guest')
        with patch.object(dat_ban, '_cau_hinh', return_value=c):
            r = dat_ban.gui(nd,ma)
            ten = hashlib.sha256(ma.encode()).hexdigest()
            phieu = frappe.get_doc(dat_ban.DOCTYPE, ten)
            dat('Lưu thật trạng thái chờ',phieu.trang_thai=='Chờ xác nhận')
            dat('Guest không có quyền đọc phiếu',not frappe.has_permission(dat_ban.DOCTYPE,'read',doc=phieu))
            dat('Retry trả cùng mã',dat_ban.gui(nd,ma)['ma']==r['ma'])
            chan('Đổi nội dung cùng khóa bị chặn',lambda:dat_ban.gui(dict(nd,so_khach=3),ma))
            with patch.object(dat_ban, '_cau_hinh', return_value=dict(c,bat=False)):
                dat('Retry khi đã tắt lịch vẫn đối soát được',dat_ban.gui(nd,ma)['ok']==1)
            frappe.set_user('Administrator')
            phieu.trang_thai='Đã xác nhận';phieu.save();phieu.reload()
            dat('Nhân viên lưu xác nhận',phieu.trang_thai=='Đã xác nhận')
            phieu.so_khach=7
            chan('Không âm thầm đổi yêu cầu đã xác nhận',phieu.save)
            phieu.reload();phieu.trang_thai='Chờ xác nhận'
            chan('Không chuyển ngược trạng thái',phieu.save)
        nhom = frappe.db.get_value('Customer Group', {'is_group': 0}, 'name')
        if not nhom:
            nhom = frappe.get_doc({'doctype':'Customer Group','customer_group_name':'Khách bench web 245','parent_customer_group':'All Customer Groups','is_group':0}).insert().name
        kh = frappe.get_doc({'doctype':'Customer','customer_name':'Khách bench thành viên 245','customer_type':'Individual','customer_group':nhom,'territory':'All Territories','mobile_no':'0912345678','vgb_diem':999999}).insert()
        frappe.get_doc({'doctype':'Vagabond So Diem','khach':kh.name,'ngay':frappe.utils.now_datetime(),'loai':'So du dau ky','diem':25000}).insert()
        token='bench-only-web245-token'
        frappe.get_doc({'doctype':'Vagabond Phien Khach','sdt':'84912345678','token_bam':dang_nhap._bam(token),'het_han':frappe.utils.add_days(frappe.utils.now_datetime(),1)}).insert()
        frappe.local.request = SimpleNamespace(cookies={thanh_vien.COOKIE:token},method='GET')
        frappe.local.request_ip='127.0.0.245'
        frappe.local.form_dict=frappe._dict(cmd='web245-bench')
        frappe.local.response_headers={}
        frappe.set_user('Guest')
        with patch.object(thanh_vien,'cfg',return_value=frappe._dict(pancake_shop_id='')), patch.object(thanh_vien,'key',return_value=''):
            r=thanh_vien.toi()
            dat('Phiên đúng chỉ đọc khách đã xác thực',r['ok']==1 and r['ten']==kh.customer_name)
            dat('Đọc 25000 từ sổ, bỏ ô tổng hợp 999999',r['diem']==25000)
            dat('Không cache hồ sơ',frappe.local.response_headers['Cache-Control']=='private, no-store')
            frappe.local.request.cookies[thanh_vien.COOKIE]='sai-token'
            dat('Token sai không lộ tên/điểm/đơn',thanh_vien.toi()=={'ok':0,'ly_do':'chua_dang_nhap'})
        return {'dat':len(ket),'ket_qua':ket}
    finally:
        frappe.set_user(nguoi)
        frappe.local.request=req
        frappe.db.rollback(save_point='web_khach_245')
