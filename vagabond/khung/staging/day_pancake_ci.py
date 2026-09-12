"""#210: chứng minh dấu gửi qua tiến trình chết và hai worker thật trên DB CI.

Chỉ bench dùng một lần. Fixture được commit cố ý để tiến trình khác đọc;
không gọi Pancake thật, không dùng khung rollback của kiểm trên site thật.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import patch
import frappe


def _khoa():
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('Chỉ chạy trên GitHub Actions.')
    frappe.init(site='bench-ci.localhost',sites_path='.')
    frappe.connect()
    if not frappe.conf.get('vagabond_bench_thu'):
        raise RuntimeError('Thiếu khoá bench thử, không chạy trên site thật.')
    frappe.set_user('Administrator')


def _goi(pc, ma):
    with patch.object(pc,'cfg',lambda:frappe._dict(pancake_shop_id='THU210')),patch.object(pc,'key',lambda *a:'fake'),patch.object(frappe,'enqueue') as enq:
        kq=pc.tao_tren_pancake(ma)
        assert kq['trang_thai'] in ('dang_cho','chua_ro')
        if enq.called: assert enq.call_args.kwargs['enqueue_after_commit'] is True
    frappe.db.commit()
    return pc._ten_luot('THU210',ma)


def worker(ten, che_do, tep):
    from vagabond import pancake_sp as pc
    def post(*a,**kw):
        # Ghi bằng chứng HTTP stub đã nhận, rồi mô phỏng mất cả tiến trình.
        with open(tep,'a') as f:
            f.write(ten+'\n');f.flush();os.fsync(f.fileno())
        if che_do=='chet':os._exit(23)
        if che_do=='doi_soat':
            han=time.monotonic()+20
            while not Path(str(tep)+'.tha').exists():
                if time.monotonic()>han:raise RuntimeError('Không có đối chứng mở lại trong lúc POST')
                time.sleep(0.05)
        time.sleep(0.2)
        return frappe._dict(status_code=201,json=lambda:{'success':True})
    with patch.object(pc,'cfg',lambda:frappe._dict(pancake_shop_id='THU210')),patch.object(pc,'key',lambda *a:'fake'),patch.object(pc,'tim_het_tren_pancake',lambda *a:([],True)),patch.object(pc.requests,'post',post):
        pc.chay_luot_day(ten)
        frappe.db.commit()


def chay():
    from vagabond import pancake_sp as pc
    goc=Path(os.environ['VGB_ARTIFACTS']);goc.mkdir(exist_ok=True)
    tep=goc/'pancake-post-stub.log'
    if tep.exists():raise RuntimeError('Cần bench CI mới, không chạy đè bằng chứng.')
    names=['THU210-CHET','THU210-HAI-JOB','THU210-HAI-REQUEST']
    for ma in names:
        if frappe.db.exists('Item',ma):raise RuntimeError('Fixture đã tồn tại.')
        frappe.get_doc(dict(doctype='Item',item_code=ma,item_name='Món kiểm210',item_group='All Item Groups',stock_uom='Nos',is_stock_item=0,is_sales_item=1,standard_rate=15000)).insert(ignore_permissions=True)
    ids=[_goi(pc,ma) for ma in names[:2]]
    base=[sys.executable,'-m','vagabond.khung.staging.day_pancake_ci']
    ps=[subprocess.Popen(base+['request',names[2]]) for _ in range(2)]
    for p in ps: assert p.wait(timeout=90)==0
    frappe.db.rollback()
    assert frappe.db.count(pc.DT_DAY,{'ma':names[2]})==1,'Hai request tạo hai dấu'
    p=subprocess.run(base+['worker',ids[0],'chet',str(tep)],timeout=90)
    assert p.returncode==23, 'Chưa chạm HTTP stub trước khi chết'
    frappe.db.rollback()
    assert frappe.db.get_value(pc.DT_DAY,ids[0],'trang_thai')=='dang_gui','Dấu gửi chưa bền sau tiến trình chết'
    assert _goi(pc,names[0])==ids[0]
    subprocess.run(base+['worker',ids[0],'binh_thuong',str(tep)],check=True,timeout=90)
    with patch.object(pc,'cfg',lambda:frappe._dict(pancake_shop_id='THU210')),patch.object(pc,'key',lambda *a:'fake'),patch.object(pc,'tim_het_tren_pancake',lambda *a:([],True)):
        assert pc.trang_thai_tren_pancake(names[0])['trang_thai']=='chua_ro'
    assert tep.read_text().splitlines().count(ids[0])==1,'POST lặp sau crash'
    ps=[subprocess.Popen(base+['worker',ids[1],'binh_thuong',str(tep)]) for _ in range(2)]
    for p in ps: assert p.wait(timeout=90)==0
    frappe.db.rollback()
    assert frappe.db.get_value(pc.DT_DAY,ids[1],'trang_thai')=='da_tao'
    assert tep.read_text().splitlines().count(ids[1])==1,'Hai worker tạo trùng'
    # Pha2: stub giữ kết nối mở, request/đối soát phải NOWAIT, không mở dấu.
    ten3=pc._ten_luot('THU210',names[2])
    p=subprocess.Popen(base+['worker',ten3,'doi_soat',str(tep)])
    try:
        han=time.monotonic()+20
        while ten3 not in tep.read_text().splitlines():
            if time.monotonic()>han:raise RuntimeError('Worker chưa tới POST')
            time.sleep(0.05)
        assert _goi(pc,names[2])==ten3
        try:
            pc.doi_soat_luot(ten3,'Ca CI chen ngang worker','Bằng chứng giả lập chỉ dùng cho CI',1)
        except frappe.ValidationError as e:
            assert 'Lượt gửi đang chạy' in str(e)
        else:raise AssertionError('Đã mở lại trong lúc worker đang POST')
        frappe.db.rollback()
    finally:
        Path(str(tep)+'.tha').touch()
        assert p.wait(timeout=30)==0
    frappe.db.rollback()
    assert frappe.db.get_value(pc.DT_DAY,ten3,'trang_thai')=='da_tao'
    assert tep.read_text().splitlines().count(ten3)==1
    pc.doi_soat_luot(ids[0], 'Ca CI: phía nhận stub đã dọn mã', 'Xác nhận giả lập HTTP stub: không còn yêu cầu cũ', 1)
    frappe.db.commit()
    assert frappe.db.get_value(pc.DT_DAY,ids[0],'trang_thai')=='loi'
    assert len(json.loads(frappe.db.get_value(pc.DT_DAY,ids[0],'lich_su_doi_soat')))==1
    (goc/'pancake-durable.json').write_text(json.dumps({'dat':True,'crash_post':1,'concurrent_post':1,'fixture':names,'ngoai_he_thong':'HTTP stub, không gửi Pancake thật'}))
    print('PASS #210: commit bền qua crash, hai worker chỉ POST một lần; không gọi Pancake thật.')


if __name__=='__main__':
    _khoa()
    try:
        if len(sys.argv)>1 and sys.argv[1]=='request':
            from vagabond import pancake_sp as pc
            _goi(pc,sys.argv[2])
        elif len(sys.argv)>1:worker(*sys.argv[2:])
        else:chay()
    finally:frappe.destroy()
