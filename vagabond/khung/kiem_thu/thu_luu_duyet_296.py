"""#296: gọi cửa lưu thật và kiểm việc gọi cửa chung, không chỉ tìm chuỗi."""
from types import SimpleNamespace as NS
from datetime import date
from vagabond.khung.kiem_thu.nen import ca, la, dung
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap


def nem(cau, **kw):
    raise ValueError(cau)


def don():
    d = D(name='SI296', docstatus=0, custom_nguon='Tại chỗ', vgb_quay='TCV',
          vgb_pt_thanh_toan='Tiền mặt', vgb_ma_tham_chieu='', vgb_xhd_ten='',
          grand_total=100000, flags=D())
    object.__setattr__(d, 'items', [])
    return d


def nen(d, vet):
    d.save = lambda: vet.append('save')
    d.submit = lambda: vet.append('submit')
    return dict(frappe=NS(throw=nem, db=NS(commit=lambda: vet.append('commit'))),
        _kiem_quyen=lambda: None, _kiem_quyen_doc_luu_don=lambda: None, _pos_lay=lambda n:d, _nan_pt_theo_nguon=lambda s:s.vgb_pt_thanh_toan,
        _chuan_ma_tham_chieu=lambda p,m:m, _kiem_trung_ma=lambda *a,**k:None,
        _soat_sepay=lambda *a:None, XHD_MAC_DINH='Bán cho người tiêu dùng',
        flt=lambda x:float(x or 0), _tien=lambda x:str(x), KHACH_LE='LE')


@ca('#296 lưu gọi cùng điều kiện với ghi sổ, chỉ lưu nháp')
def luu():
    for pt in ('Tiền mặt', '', 'Công nợ'):
        d=don();d.vgb_pt_thanh_toan=pt;d.customer='LE';vet=[];g=nen(d,vet)
        nap('ban_hang.py','_chuan_bi_ghi_so',g)
        fn=nap('ban_hang.py','pos_luu_don',g)
        if pt=='Tiền mặt':
            la('vẫn nháp',fn(d.name)['docstatus'],0)
            la('không submit',vet,['save','commit'])
        else:
            try:fn(d.name)
            except ValueError: pass
            else:dung('cửa chung phải chặn '+pt,False)
            la('không ghi dở',vet,[])


@ca('#296 quầy lưu và ghi sổ cùng chặn SePay thiếu tiền hoặc giao dịch có chủ')
def sepay():
    for ten in ('pos_luu_don','pos_ghi_so'):
        for loi in ('thiếu tiền','có chủ','đủ'):
            d=don();d.vgb_pt_thanh_toan='Chuyển khoản';vet=[];g=nen(d,vet)
            g['_kiem_quyen_ghi_so']=lambda:None
            g['_sepay_cho_bill']=lambda s:dict(nhan=0 if loi=='thiếu tiền' else 100000,gd=['GD296'])
            def chiem(s, gd):
                la('đúng giao dịch',gd,['GD296'])
                if loi=='có chủ':nem('Giao dịch đã có chủ')
                vet.append('chiem')
            g['_chiem_gd_bill']=chiem
            nap('ban_hang.py','_chuan_bi_ghi_so',g)
            fn=nap('ban_hang.py',ten,g)
            try:fn(d.name)
            except ValueError:dung('chỉ nhánh không đủ bị chặn',loi!='đủ')
            else:dung('phải chặn tiền thiếu/trùng',loi=='đủ')
            la('không lưu hoặc submit khi bị chặn',vet,
                ['chiem','save' if ten=='pos_luu_don' else 'submit','commit'] if loi=='đủ' else [])


@ca('#296 quyền ghi sổ tay kiểm trước khi đọc chứng từ')
def quyen():
    for vai in ('Guest','Sales User','Sales Manager','Accounts User','Accounts Manager','System Manager'):
        vet=[];g=nen(don(),vet);g['frappe'].get_roles=lambda:[vai]
        g['QUYEN_BAN_HANG']={'System Manager','Sales User','Sales Manager','Bộ phận đặt hàng'}
        nap('ban_hang.py','_kiem_quyen',g)
        nap('ban_hang.py','_kiem_quyen_ghi_so',g)
        def doc(n):vet.append('doc');return don()
        g['_pos_lay']=doc;g['_chuan_bi_ghi_so']=lambda s:nem('đã qua quyền')
        try:nap('ban_hang.py','pos_ghi_so',g)('SI296')
        except ValueError:pass
        la('chặn trước đọc bill',vet,['doc'] if vai in ('Accounts User','Accounts Manager','System Manager') else [])


@ca('#296 cửa đổi ngày giữ tờ đã gửi hoặc chưa rõ, không sửa lịch thanh toán')
def ngay():
    for co in ('custom_minvoice_id','custom_hddt_id','custom_hddt_so','vgb_hddt_cho_doi_chieu'):
        d=don();d[co]='DA-GUI';d.posting_date='2026-09-11';vet=[];g=nen(d,vet)
        g.update(getdate=date.fromisoformat,nowdate=lambda:'2026-09-13')
        nap('ban_hang.py','_kiem_ngay_ban_nhap',g)
        try:nap('ban_hang.py','_doi_ngay_ban_nhap',g)(d,'2026-09-13','thử','duyệt')
        except ValueError:pass
        else:dung('phải chặn dấu '+co,False)
        la('không save',vet,[]);la('giữ ngày',d.posting_date,'2026-09-11')


@ca('#296 giao diện lưu và duyệt hiện đúng kết quả, lỗi, huỷ')
def giao_dien():
    import subprocess
    from pathlib import Path
    p=Path(__file__).parent/'hanh_vi'/'luu_duyet_296.cjs'
    kq=subprocess.run(['node',str(p)],capture_output=True,text=True,timeout=20)
    la('hành vi node: '+kq.stdout+kq.stderr,kq.returncode,0)


@ca('#298 R5 ngày không đổi hoặc tờ bị chặn không tiêu OTP')
def otp():
    for trang in ('cùng ngày','đã ghi','chờ đối chiếu','đổi'):
        d=don();vet=[];g=nen(d,vet)
        d.posting_date='2026-09-13' if trang=='cùng ngày' else '2026-09-11'
        if trang=='đã ghi':d.docstatus=1
        if trang=='chờ đối chiếu':d.vgb_hddt_cho_doi_chieu=1
        g['frappe'].get_doc=lambda *a:d;g['frappe'].get_roles=lambda:['Accounts User']
        g.update(getdate=date.fromisoformat,nowdate=lambda:'2026-09-13',QUYEN_SUA_NGAY={'Accounts User'},
            _otp_kiem=lambda *a:vet.append('otp'),_ghi_vet=lambda *a:None)
        for ten in ('_kiem_ngay_ban_nhap','_doi_ngay_ban_nhap','doi_ngay_hoa_don'):nap('ban_hang.py',ten,g)
        try:g['doi_ngay_hoa_don'](d.name,otp='mã thử')
        except ValueError:dung('chỉ chặn tờ không được đổi',trang in ('đã ghi','chờ đối chiếu'))
        la('OTP chỉ khi đổi',vet,['otp','save','commit'] if trang=='đổi' else [])


@ca('#298 R2 chỉ nhả giao dịch của nháp huỷ mềm, giữ chủ của tờ đã ghi sổ')
def nha_giao_dich():
    for tt,huy in ((0,0),(0,1),(1,1)):
        d=D(name='CU',docstatus=tt,vgb_huy=huy,vgb_gd_sepay='GD296')
        g=dict(frappe=NS(get_all=lambda *a,**k:[d]),nap_so=lambda:None,_SO={},
            HD_BAN={'doctype':'Sales Invoice','truong':'vgb_gd_sepay','ten_man':'hoá đơn bán'},cint=lambda x:int(x or 0))
        ket=nap('doi_soat_sepay.py','chu_cua_giao_dich',g)(['GD296'])
        la('chủ đang hiệu lực',ket,{} if (tt,huy)==(0,1) else {'GD296':'hoá đơn bán CU'})


@ca('#298 kế toán đi qua các bước đọc/lưu trước ghi sổ, Guest bị chặn')
def quyen_truoc_ghi_so():
    from unittest.mock import patch
    import sys
    from pathlib import Path
    nguon=(Path(__file__).resolve().parents[2]/'ban_hang.py').read_text()
    for vai in ('Guest','Sales User','Sales Manager','Accounts User','Accounts Manager','System Manager'):
        for ten in ('bang_doanh_so','cau_hinh_ban_hang','tim_don','don_treo','luu_xhd','luu_thanh_toan','luu_khach_no','doi_ngay_hoa_don'):
            vet=[]
            def doc(*a,**kw):vet.append('qua_quyen');raise ValueError('Dừng sau quyền')
            g=dict(frappe=NS(get_roles=lambda:[vai],throw=nem,get_doc=doc,db=NS(get_value=doc)),QUYEN_BAN_HANG={'System Manager','Sales User','Sales Manager','Bộ phận đặt hàng'},QUYEN_SUA_NGAY={'System Manager','Sales Manager','Accounts User','Accounts Manager'},getdate=doc,pt_thanh_toan=NS(bang_tham_chieu=doc),chuan_tim=doc,_quet_don_treo=doc)
            nap('ban_hang.py','_kiem_quyen',g)
            if 'def _kiem_quyen_doc_luu_don(' in nguon:nap('ban_hang.py','_kiem_quyen_doc_luu_don',g)
            try:
                with patch.dict(sys.modules,{'vagabond.minvoice_an_toan':NS(da_gui=lambda d:False)}):
                    nap('ban_hang.py',ten,g)('SI298') if ten!='cau_hinh_ban_hang' else nap('ban_hang.py',ten,g)()
            except ValueError:pass
            mong=vai!='Guest' and not (ten=='doi_ngay_hoa_don' and vai=='Sales User')
            la(ten+' / '+vai,vet,['qua_quyen'] if mong else [])
