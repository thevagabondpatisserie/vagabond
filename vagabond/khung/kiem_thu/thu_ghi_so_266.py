"""#266: gọi hai nhịp thật, tách ghi sổ và phát hành khi còn nợ ngày cũ."""
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS
from vagabond.khung.kiem_thu.nen import ca, la, dung
SRC=Path(__file__).resolve().parents[2]/'ban_hang.py'
class D(dict):
    __getattr__=dict.get

def nap(name,g):
    fn=next(n for n in ast.parse(SRC.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SRC),'exec'),g)
    return g[name]

@ca('#266 hai nhịp còn nợ ngày cũ vẫn ghi sổ và báo hoãn riêng')
def hai_nhip():
    for name in ['tu_ghi_so_cuoi_ngay','xuat_rai_trong_ngay']:
        ghi=[];bao=[]
        si=D(name='SI-THU',docstatus=0,vgb_quay='TCV',vgb_huy=0,vgb_tam_tinh=0)
        f=NS(set_user=lambda *a:None,log_error=lambda *a,**kw:None,
            get_doc=lambda *a:si,db=NS(get_all=lambda *a,**kw:[] if 'custom_pancake_id' in kw.get('filters',{}) else ([si] if kw.get('fields') else ['SI-THU']),commit=lambda:None))
        def goi(si,sepay=None,cho_xuat=True):ghi.append(cho_xuat);return 1,0,''
        g=dict(frappe=f,cfg=lambda:D(tu_ghi_so_bat=1,tu_ghi_so_gio='23:00',tu_ghi_so_quay='TCV'),
            cint=lambda x:int(x or 0),nowdate=lambda:'2026-09-12',now_datetime=lambda:datetime(2026,9,12,23,10),
            _gio_hop_le=lambda x:x,hddt_cho_xuat=NS(xuat_ngay_cu_truoc=lambda:False),
            _dong_bo_doanh_so=lambda *a:None,pancake_nhip=NS(ghi_ok=lambda:None),
            _khoa_dong_bo=lambda **kw:object(),_mo_khoa_dong_bo=lambda *a:None,
            _sepay_theo_don=lambda *a:None,ghi_so_dieu_kien=NS(ly_do=lambda *a,**kw:'san_sang'),
            _ghi_so_mot_don=goi,_quay_tu_ghi_so=lambda:['TCV'],_khach_le=lambda:'Khách lẻ',
            _bao_hoan_phat_hanh=lambda *a:bao.append(a),
            hddt_bu=NS(duoc_rai=lambda *a:True,moc_bill_du_gio=lambda *a:'2026-09-12 19:00:00',rai_bo_qua=lambda *a:False))
        fn=nap(name,g)
        if name=='tu_ghi_so_cuoi_ngay':fn(bo_qua_gio=True,tren_hang_doi=True)
        else:fn()
        la(name+' ghi một tờ, hoãn xuất',ghi,[False])
        la(name+' báo cả khi tờ cũ chỉ nháp',bao,[('2026-09-12',1,0)])

@ca('#266 hoãn phát hành vẫn submit và commit, không gọi cửa xuất')
def ghi_so():
    calls=[];si=D(name='SI-THU',flags=NS(),submit=lambda:calls.append('submit'))
    f=NS(db=NS(commit=lambda:calls.append('commit')))
    g=dict(frappe=f,_chuan_bi_ghi_so=lambda *a:None,_tu_xuat_hddt=lambda *a:calls.append('HTTP'))
    la('đã ghi sổ nhưng chưa xuất',nap('_ghi_so_mot_don',g)(si,cho_xuat=False),(1,0,''))
    la('thứ tự và không HTTP',calls,['submit','commit'])

@ca('#266 cảnh báo riêng có nhật ký và xếp thư, không phụ thuộc đếm đã submit')
def canh_bao():
    calls=[];mail=[];co_thu=[]
    f=NS(db=NS(set_single_value=lambda *a:calls.append(a),commit=lambda:None,exists=lambda *a:bool(co_thu)),
         utils=NS(escape_html=lambda x:x),log_error=lambda **kw:None,
         sendmail=lambda **kw:mail.append(kw))
    fn=nap('_bao_hoan_phat_hanh',dict(frappe=f,_nguoi_nhan_don_treo=lambda:['ci@example.invalid']))
    fn('2026-09-12',1,0)
    la('có thư xếp hàng',len(mail),1)
    dung('có lời cảnh báo trên Cài đặt','CẢNH BÁO' in calls[0][2])
    co_thu.append(1);fn('2026-09-12',0,0)
    la('không xếp lại thư đã có',len(mail),1)
    la('nhật ký vẫn mới',len(calls),2)


@ca('#266 công cụ đặt phiên bản giữ nguyên lịch sử patch và không nhân dòng')
def lich_su_patch():
    import importlib.util
    import tempfile
    from unittest.mock import patch
    duong=SRC.parents[1]/'dat_phien_ban.py'
    spec=importlib.util.spec_from_file_location('dat_ver_thu',duong);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'patches.txt';cu='[post_model_sync]\nvagabond.patches.dong_bo_cau_truc #v480\nkhac.patch\n';p.write_text(cu)
        with patch.object(m,'TEP_PATCH',str(p)):
            dung('thêm được',m.dat_patch('482'))
            la('giữ nguyên mọi dòng',p.read_text(),cu+'vagabond.patches.dong_bo_cau_truc #v482\n')
            la('không nhân dòng',m.dat_patch('482'),False)
