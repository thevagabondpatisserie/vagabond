"""HTTP/HTTPS thật trên site CI dùng một lần; không gửi OTP hoặc nối ngoài."""
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import socket
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import frappe
import requests


def _noi():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Chỉ chạy trên GitHub Actions.')
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    if not all(frappe.conf.get(k) for k in ('vagabond_bench_thu','mute_emails','disable_scheduler')):
        raise RuntimeError('Thiếu khóa bench riêng hoặc khóa gửi ngoài.')
    frappe.set_user('Administrator')


def _phuc_vu(cong):
    _noi()
    frappe.destroy()
    from vagabond.khung.staging.phuc_vu_ci import chan_mang
    chan_mang()
    from vagabond import dat_ban
    goc = dat_ban.chuan_hoa
    hen = threading.Barrier(2, timeout=10)
    khoa = threading.Lock()
    so_lan = [0]

    def cung_luc(du_lieu, *args, **kwargs):
        ra = goc(du_lieu, *args, **kwargs)
        if ra.get('ten') == 'Khach HTTP245':
            with khoa:
                so_lan[0] += 1
                doi = so_lan[0] <= 4  # 2 request x 2 cửa: gui và kiem_phieu.
            if doi:
                # Hai request đều qua phép đọc khóa trước khi insert.
                # Đồng bộ thời điểm thôi, không thay DB/validation/kết quả.
                hen.wait()
        return ra

    dat_ban.chuan_hoa = cung_luc
    from frappe.app import application
    from werkzeug.serving import make_server

    def ung_dung(environ, start_response):
        environ['HTTP_X_FRAPPE_SITE_NAME'] = 'bench-ci.localhost'
        return application(environ, start_response)

    # HTTPS thật để cookie Secure đi qua cookie jar bình thường.
    may = make_server('127.0.0.1', cong, ung_dung, threaded=True, ssl_context='adhoc')
    may.serve_forever()


def chay():
    from vagabond import dat_ban, dang_nhap, diem_ban
    from frappe.utils import add_days, now_datetime, nowdate
    _noi()
    ma = str(uuid.uuid4())
    ten_phieu = hashlib.sha256(ma.encode()).hexdigest()
    sdt, sdt_sai = '84900000245', '84900000246'
    cau_hinh = frappe.get_single(dat_ban.CAU_HINH)
    cu = {k:cau_hinh.get(k) for k in ('bat','co_so','khung_gio','toi_da_khach','toi_da_ngay')}
    co_so = next(d['ma'] for d in diem_ban.ds(chi_bat=True) if d.get('quay'))
    cau_hinh.update(dict(bat=1,co_so=co_so,khung_gio='14:00',toi_da_khach=8,toi_da_ngay=30))
    cau_hinh.save(ignore_permissions=True)
    for so in (sdt,sdt_sai):
        frappe.get_doc(dict(doctype='Vagabond OTP',sdt=so,ma_bam=dang_nhap._bam('123456'),
            het_han=add_days(now_datetime(),1),da_dung=0,so_lan_sai=0)).insert(ignore_permissions=True)
    kh = frappe.get_doc(dict(doctype='Customer',customer_name='Khach HTTP245',customer_type='Individual',
        customer_group=frappe.db.get_value('Customer Group',{'is_group':0},'name'),
        territory='All Territories',mobile_no='0900000245')).insert(ignore_permissions=True)
    frappe.get_doc(dict(doctype='Vagabond So Diem',khach=kh.name,ngay=now_datetime(),
        loai='So du dau ky',diem=25000)).insert(ignore_permissions=True)
    nd = dict(ten='Khach HTTP245',sdt='0900000245',co_so=co_so,
        ngay=add_days(nowdate(),2),gio='14:00',so_khach=2,ghi_chu='Ghi chu goc HTTP')
    frappe.db.commit()
    frappe.destroy()
    with socket.socket() as o:
        o.bind(('127.0.0.1',0))
        cong = o.getsockname()[1]
    may = multiprocessing.get_context('spawn').Process(target=_phuc_vu,args=(cong,),daemon=True)
    may.start()
    goc = 'https://127.0.0.1:%s/api/method/' % cong
    ket = []
    requests.packages.urllib3.disable_warnings()

    def dat(ten, dieu):
        if not dieu:
            raise AssertionError(ten)
        ket.append(ten)

    def goi(khach, ham, noi_dung=None):
        return khach.request('POST' if noi_dung is not None else 'GET',goc+ham,
            json=noi_dung,verify=False,timeout=20)

    def hai_luot(ham, noi_dung):
        hen = threading.Barrier(2,timeout=10)
        def mot(_):
            khach = requests.Session()
            hen.wait()
            return khach, goi(khach,ham,noi_dung)
        with ThreadPoolExecutor(max_workers=2) as bo:
            return list(bo.map(mot,range(2)))

    try:
        for _ in range(80):
            if not may.is_alive():
                raise RuntimeError('Server HTTPS thử đã dừng.')
            try:
                if requests.get(goc+'ping',verify=False,timeout=1).status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.2)
        else:
            raise RuntimeError('Server HTTPS thử chưa sẵn sàng.')
        cac = hai_luot('vagabond.thanh_vien.xac_thuc',dict(sdt=sdt,ma='123456'))
        dat('Hai POST OTP nhận phản hồi HTTP',all(r.status_code==200 for _,r in cac))
        dat('Một OTP chỉ mở một phiên',sum(r.json()['message']['ok'] for _,r in cac)==1)
        khach, tra = next((k,r) for k,r in cac if r.json()['message']['ok'])
        cookie = tra.headers.get('Set-Cookie','').lower()
        dat('Cookie có HttpOnly Secure SameSite Strict',all(x in cookie for x in ('vgb_thanh_vien=','httponly','secure','samesite=strict')))
        dat('API xác thực không trả token vào JS','token' not in tra.json()['message'])
        toi = goi(khach,'vagabond.thanh_vien.toi')
        dat('Cookie jar HTTPS đọc đúng hồ sơ và điểm',toi.json()['message']['diem']==25000 and toi.json()['message']['sdt']=='0900000245')
        dat('Hồ sơ HTTP không cache','no-store' in toi.headers.get('Cache-Control',''))
        la = goi(requests.Session(),'vagabond.thanh_vien.toi')
        dat('Không cookie không đọc được hồ sơ',la.json()['message']['ok']==0)
        ra = goi(khach,'vagabond.thanh_vien.thoat',{})
        dat('Đăng xuất HTTP thành công',ra.status_code==200 and ra.json()['message']['ok']==1)
        dat('Sau đăng xuất cookie không đọc được hồ sơ',goi(khach,'vagabond.thanh_vien.toi').json()['message']['ok']==0)
        sai = hai_luot('vagabond.thanh_vien.xac_thuc',dict(sdt=sdt_sai,ma='000000'))
        dat('Hai mã sai đều bị từ chối',all(r.status_code==200 and not r.json()['message']['ok'] for _,r in sai))
        _noi()
        dat('Hai lần sai không ghi đè bộ đếm',frappe.db.get_value('Vagabond OTP',{'sdt':sdt_sai},'so_lan_sai')==2)
        frappe.destroy()
        cac = hai_luot('vagabond.dat_ban.gui',dict(du_lieu=nd,ma_lan_gui=ma))
        dat('Hai request đặt bàn cùng khóa đều nhận kết quả',all(r.status_code==200 and r.json()['message']['ok']==1 for _,r in cac))
        dat('Retry thành công không kèm hộp lỗi trùng tên',all(not r.json().get('_server_messages') for _,r in cac))
        dat('Hai request nhận cùng mã',len({r.json()['message']['ma'] for _,r in cac})==1)
        _noi()
        dat('DB chỉ có một yêu cầu đặt bàn',frappe.db.count(dat_ban.DOCTYPE,{'name':ten_phieu})==1)
        dat('Ghi chú HTTP giữ đúng sau reload',frappe.get_doc(dat_ban.DOCTYPE,ten_phieu).ghi_chu==nd['ghi_chu'])
        frappe.db.set_single_value(dat_ban.CAU_HINH,'bat',0)
        frappe.db.commit(); frappe.destroy()
        lai = goi(requests.Session(),'vagabond.dat_ban.gui',dict(du_lieu=nd,ma_lan_gui=ma))
        dat('Retry sau tắt lịch vẫn tìm thấy yêu cầu',lai.status_code==200 and lai.json()['message']['ok']==1)
        doi = goi(requests.Session(),'vagabond.dat_ban.gui',dict(du_lieu=dict(nd,so_khach=3),ma_lan_gui=ma))
        dat('Cùng khóa khác nội dung bị từ chối',doi.status_code>=400)
        return dict(dat=len(ket),ket_qua=ket)
    finally:
        may.terminate(); may.join(timeout=5)
        _noi()
        cau_hinh = frappe.get_single(dat_ban.CAU_HINH)
        cau_hinh.update(cu); cau_hinh.save(ignore_permissions=True)
        frappe.db.commit(); frappe.destroy()


if __name__ == '__main__':
    ra = chay()
    Path(os.environ['VGB_ARTIFACTS'],'web-http-245.json').write_text(json.dumps(ra,ensure_ascii=False,indent=2))
    print(json.dumps(ra,ensure_ascii=False))
