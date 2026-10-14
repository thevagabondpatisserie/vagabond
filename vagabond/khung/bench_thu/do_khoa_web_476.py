"""Đo cập nhật đơn web khác trong lúc tao_don giữ khóa, bench dùng một lần."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from datetime import date
from unittest.mock import patch
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung
from vagabond.khung.bench_thu.do_khoa_476 import cho

NGAY = '2038-10-15'


def con(vai, thu_muc):
    folder=Path(thu_muc);cfg=json.loads((folder/'cfg.json').read_text())
    _mo();ket={'vai':vai}
    try:
        from vagabond import giu_ton_web as g, ton_don_web as t, don_web as dw
        from vagabond.khung.kiem_that.thu_don_web_367 import _goi, _don, _Tra
        if vai=='A':
            ham=g._don
            def giu(*a,**kw):
                ds=ham(*a,**kw)
                (folder/'A.locked').touch();cho(folder,'A.go')
                return ds
            d=dict(_don(cfg['ma']),nonce=cfg['nonce'],ngay_nhan=NGAY+'T13:00:00')
            with patch.object(g,'hom_nay',lambda:date.fromisoformat(NGAY)),patch.object(t,'hom_nay',lambda:date.fromisoformat(NGAY)),patch.object(g,'_don',giu):
                kq,_=_goi(d,lambda:_Tra(400,{'success':False,'message':'Từ chối thử, nhả giữ'}))
            _dung(not kq.get('ok'),'Pancake giả từ chối đơn đo')
        else:
            # Đây là hook phía máy chủ nhận kết quả hóa đơn của đơn Pancake.
            # Tắt riêng hàng đợi quảng cáo, không thay câu UPDATE đang đo.
            co=frappe.flags.vagabond_kiem_that
            with patch.object(dw,'xep_capi'),patch.object(dw,'_noi_uu_dai_hoa_don'):
                frappe.flags.vagabond_kiem_that=False
                try:
                    (folder/'B.start').touch();t0=time.monotonic()
                    dw.khi_ghi_so_hoa_don(frappe._dict(name='SINV-PROBE-476',custom_pancake_id=cfg['pancake'],grand_total=100))
                    ket['thao_tac_giay']=time.monotonic()-t0
                finally:frappe.flags.vagabond_kiem_that=co
            _dung(frappe.db.get_value(dw.DOCTYPE,cfg['don'],'trang_thai')=='Da ghi so','Hook cập nhật đơn khác thật')
        ket['dat']=True
    except Exception:
        ket.update(dat=False,loi=traceback.format_exc())
    finally:
        _dong();(folder/(vai+'.json')).write_text(json.dumps(ket,ensure_ascii=False,indent=2))


def chay():
    folder=Path(os.environ['VGB_ARTIFACTS'])/'do-khoa-web-476';folder.mkdir()
    ps=[];ket={}
    try:
        _mo()
        try:
            from vagabond.khung.kiem_that.thu_don_web_367 import _mot_mon,_goi,_don,_Tra
            ma=_mot_mon().item_code;pancake='PROBE476'+frappe.generate_hash(length=12)
            d=dict(_don(ma),nonce=frappe.generate_hash(length=24),ngay_nhan='2030-01-01T13:00:00')
            kq,_=_goi(d,lambda:_Tra(200,{'success':True,'data':{'id':pancake}}))
            _dung(kq.get('ok'),'Tạo đơn web đối chứng')
            cfg=dict(ma=ma,don=kq['ma_yeu_cau'],pancake=pancake,nonce=frappe.generate_hash(length=24))
            frappe.db.set_single_value('Vagabond Settings','pancake_shop_id','67355')
            frappe.db.commit()
        finally:_dong()
        (folder/'cfg.json').write_text(json.dumps(cfg))
        def mo(v):
            ps.append(subprocess.Popen([sys.executable,'-m',__spec__.name,'--con',v,str(folder)]))
        mo('A');cho(folder,'A.locked');mo('B');cho(folder,'B.start')
        time.sleep(2);(folder/'A.go').touch()
        for p in ps:p.wait(timeout=60)
        ket={v:json.loads((folder/(v+'.json')).read_text()) for v in ('A','B')}
        _dung(all(r['dat'] for r in ket.values()),str(ket))
        _dung(ket['B']['thao_tac_giay']<1.5,'Đơn khác không phải chờ giữ tồn')
        print('DO KHOA WEB: '+json.dumps(ket,ensure_ascii=False),flush=True)
    finally:
        for p in ps:
            if p.poll() is None:p.kill();p.wait()
        (Path(os.environ['VGB_ARTIFACTS'])/'do-khoa-web-476.json').write_text(json.dumps(ket,ensure_ascii=False,indent=2))


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--con':con(*sys.argv[2:])
    else:chay()
