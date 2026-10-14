"""Hai tiến trình gọi cửa đặt đơn thật trên bench dùng một lần, cấm outbound."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from datetime import date
from unittest.mock import patch
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung
import frappe

NGAY = '2037-10-14'


def _con(ma, nonce, thu_muc):
    _mo()
    try:
        from vagabond import giu_ton_web as g, ton_don_web as t
        from vagabond.khung.kiem_that.thu_don_web_367 import _goi, _don, _Tra
        folder=Path(thu_muc); ham=g.kiem_va_giu
        def doi(*a,**kw):
            (folder/(nonce+'.ready')).touch()
            han=time.monotonic()+40
            while not (folder/'go').exists():
                if time.monotonic()>han:raise TimeoutError('Hàng rào đặt bánh')
                time.sleep(.02)
            return ham(*a,**kw)
        don=_don(ma);don.update(nonce=nonce,ngay_nhan=NGAY+'T13:00:00')
        with patch.object(g,'hom_nay',lambda:date.fromisoformat(NGAY)),patch.object(t,'hom_nay',lambda:date.fromisoformat(NGAY)),patch.object(g,'kiem_va_giu',doi):
            kq,vet=_goi(don,lambda:_Tra(200,{'success':True,'data':{'id':nonce}}))
        frappe.db.commit()
        (folder/(nonce+'.json')).write_text(json.dumps({'kq':kq,'post':len(vet),'pid':os.getpid()}))
    finally:_dong()


def chay():
    folder=Path(os.environ['VGB_ARTIFACTS'])/('giu-ton-476-'+str(os.getpid()));folder.mkdir()
    ps=[];kq={}
    try:
        _mo()
        try:
            from vagabond.khung.kiem_that.thu_don_web_367 import _mot_mon
            ma=_mot_mon().item_code
            _dung(not frappe.db.exists('Kiem Banh Ngay','KB-'+NGAY),'Không ghi đè bảng có sẵn')
            b=frappe.new_doc('Kiem Banh Ngay');b.ngay=NGAY
            b.append('dong',{'ma_hang':ma,'ten_banh':'Bánh cuối kiểm 476','ton_d2':1})
            b.insert(ignore_permissions=True)
            frappe.db.set_single_value('Vagabond Settings','pancake_shop_id','67355')
            nonce=[frappe.generate_hash(length=24) for _ in range(2)]
            frappe.db.commit()
        finally:_dong()
        for n in nonce:
            ps.append(subprocess.Popen([sys.executable,'-m','vagabond.khung.bench_thu.giu_ton_web_476','--con',ma,n,str(folder)]))
        han=time.monotonic()+60
        while not all((folder/(n+'.ready')).exists() for n in nonce):
            _dung(all(p.poll() is None for p in ps),'Tiến trình lỗi trước kiểm tồn cuối')
            if time.monotonic()>han:raise TimeoutError('Chưa đủ hai tiến trình')
            time.sleep(.02)
        (folder/'go').touch()
        for p in ps:_dung(p.wait(timeout=90)==0,'Tiến trình kết thúc bình thường')
        ket=[json.loads((folder/(n+'.json')).read_text()) for n in nonce]
        _dung(len({r['pid'] for r in ket})==2,'Hai tiến trình riêng')
        _dung(sum(bool(r['kq'].get('ok')) for r in ket)==1,'Chỉ một khách được nhận')
        _dung(sum(r['post'] for r in ket)==1,'Pancake chỉ nhận một lệnh tạo')
        thua=next(r for r in ket if not r['kq'].get('ok'))
        _dung(thua['kq'].get('ly_do')=='het_hang','Bên sau nhận câu hết hàng, không lỗi DB')
        _mo()
        try:
            ds=frappe.get_all('Vagabond Don Web',filters={'ngay_nhan':NGAY+' 13:00:00'},fields=['name','snapshot','trang_thai'])
            _dung(len(ds)==1 and 'giu_ton_web' in ds[0].snapshot,'Một đơn và chỗ giữ commit cùng nhau')
            from vagabond import giu_ton_web as g, ton_don_web as t
            from vagabond.khung.kiem_that.thu_don_web_367 import _goi, _don, _Tra
            # Huỷ đúng đơn thử vừa tạo, rồi kiểm từ chối và timeout qua cửa thật.
            d=frappe.get_doc('Vagabond Don Web',ds[0].name)
            with patch.object(g,'hom_nay',lambda:date.fromisoformat(NGAY)):
                g.khoa()
                g.da_dem('2037-10-15',[d.pancake_id])
                g.da_dem(NGAY,[])
                d.reload();giu=json.loads(d.snapshot)['giu_ton_web']
                _dung(giu['da_dem'] and giu['ngay_nguon']=='2037-10-15','Dời ngày theo ID, đồng bộ ngày cũ không trừ hai lần')
            d.trang_thai='Da huy';d.save(ignore_permissions=True);frappe.db.commit()
            def goi(tra):
                don=_don(ma);don.update(nonce=frappe.generate_hash(length=24),ngay_nhan=NGAY+'T13:00:00')
                return _goi(don,tra)
            def timeout():raise TimeoutError('Mất phản hồi thử')
            with patch.object(g,'hom_nay',lambda:date.fromisoformat(NGAY)),patch.object(t,'hom_nay',lambda:date.fromisoformat(NGAY)):
                r,vet=goi(lambda:_Tra(400,{'success':False,'message':'Từ chối thử'}))
                _dung(not r.get('ok') and len(vet)==1,'Từ chối đã tới Pancake')
                r,vet=goi(timeout)
                _dung(r.get('ok') and len(vet)==1,'Đã nhả phần của đơn bị từ chối; timeout vẫn nhận chờ')
                r,vet=goi(lambda:_Tra(200,{'success':True,'data':{'id':'khong-duoc-goi'}}))
                _dung(r.get('ly_do')=='het_hang' and not vet,'Timeout phải giữ chỗ tới khi rõ kết quả')
            kq={'dat':True,'ket':ket,'don':ds[0].name,'tu_choi_nha':True,'timeout_giu':True,'doi_ngay_theo_id':True}
        finally:_dong()
    except Exception:
        kq['loi']=traceback.format_exc();raise
    finally:
        for p in ps:
            if p.poll() is None:p.kill();p.wait()
        (Path(os.environ['VGB_ARTIFACTS'])/'giu-ton-web-476.json').write_text(json.dumps(kq,ensure_ascii=False,indent=2))
        print(json.dumps(kq,ensure_ascii=False),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--con':_con(*sys.argv[2:])
    else:chay()
