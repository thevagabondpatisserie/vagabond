"""#290: tái hiện đơn nháp giữ cả ngày, bill quầy và gửi duyệt lại."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
from vagabond.khung.kiem_thu.nen import ca, la, dung

class D(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__

def nap(tep, ten, g):
    cay=ast.parse((Path(__file__).resolve().parents[2]/tep).read_text())
    ham=next(n for n in cay.body if isinstance(n,ast.FunctionDef) and n.name==ten)
    ham.decorator_list=[]
    exec(compile(ast.Module(body=[ham],type_ignores=[]),tep,'exec'),g)
    return g[ten]

@ca('#290 A1 nháp cũ không giữ cửa, tờ đã ghi sổ vẫn giữ kể cả chờ đối chiếu')
def no_cu():
    for ghi_so in (False,True):
        def sql(q,*a,**k):
            return [D(posting_date='2026-09-11')] if ghi_so or 'docstatus in (0, 1)' in q else []
        g=dict(frappe=NS(db=NS(sql=sql)),nowdate=lambda:'2026-09-12',_loc_diem_dang_xuat=lambda r:[x.posting_date for x in r],KhongDocDuocNo=RuntimeError)
        la('tập bảo vệ',nap('hddt_cho_xuat.py','ngay_cu_can_bao_ve',g)(),['2026-09-11'] if ghi_so else [])

@ca('#290 A2 nút ghi sổ lấy cả bill TCV ngày chọn, không lấy tạm tính')
def quay_cu():
    loc=[]
    def doc(dt,**kw):
        loc.append(kw['filters']); return []
    f=NS(db=NS(get_all=doc,commit=lambda:None))
    g=dict(frappe=f,_kiem_quyen=lambda:None,getdate=lambda x:x,nowdate=lambda:'2026-09-12',cfg=lambda:D(pancake_shop_id='SHOP',tu_ghi_so_quay='TCV'),_sepay_theo_don=lambda *a:{})
    nap('ban_hang.py','chot_doanh_so',g)('2026-09-11')
    la('giữ ngày chọn',loc[0]['posting_date'],'2026-09-11')
    la('Sales có nguồn Pancake',loc[0]['custom_pancake_id'],['!=',''])
    la('TCV theo cấu hình',loc[1]['vgb_quay'],['in',['TCV']])
    la('không lấy trả hàng',loc[0]['is_return'],0)
    la('loại tạm tính',loc[0].get('vgb_tam_tinh'),0)

@ca('#290 A3 cửa ghi sổ lưu rã combo trước submit và không lưu lại món thường')
def combo():
    for ma in ('KMCB00004','BAWS1'):
        vet=[]
        d=D(name='SI',custom_pancake_display_id='',vgb_ma_tham_chieu='',vgb_xhd_ten='',items=[D(item_code=ma)],flags=D())
        object.__setattr__(d,'items',[D(item_code=ma)])
        d.save=lambda:vet.append('save')
        def ghi():
            dung('combo đã lưu trước submit',ma!='KMCB00004' or vet==['save']);vet.append('submit')
        d.submit=ghi
        g=dict(frappe=NS(db=NS(commit=lambda:None)),_nan_pt_theo_nguon=lambda d:'Tiền mặt',_soat_sepay=lambda *a:None,_chuan_ma_tham_chieu=lambda *a:'',_kiem_trung_ma=lambda *a,**k:None,XHD_MAC_DINH='Khách lẻ',_tu_xuat_hddt=lambda *a:(False,''))
        g['_chuan_bi_ghi_so']=nap('ban_hang.py','_chuan_bi_ghi_so',g)
        nap('ban_hang.py','_ghi_so_mot_don',g)(d,cho_xuat=False)
        la('thứ tự',vet,['save','submit'] if ma.startswith('KMCB') else ['submit'])

@ca('#290 B2 khai lại đơn từ chối quay về chờ duyệt, không giữ ý kiến cũ')
def gui_lai():
    d=D(docstatus=0,vgb_tang_duyet='Từ chối',vgb_tang_y_kien='Thiếu lý do',vgb_tang_nguoi_duyet='GD',vgb_tang_luc_duyet='Hôm qua',vgb_tang_dau_van='cu',flags=D())
    d.save=lambda:None
    g=dict(frappe=NS(get_doc=lambda *a:d,db=NS(commit=lambda:None)),_quyen=lambda:None,SI='Sales Invoice',cint=lambda x:int(x or 0),chuoi=lambda x:str(x or '').strip(),NHAN_LOAI={'marketing':'Marketing'},TT_TU_CHOI='Từ chối',TT_CHO='Chờ duyệt',_anh_cua_to=lambda *a:[],thieu_gi=lambda *a,**kw:[],THIEU={})
    nap('hang_tang.py','luu_thong_tin',g)('SI',loai='marketing',ly_do='Tặng sự kiện của tiệm')
    la('chờ duyệt',d.vgb_tang_duyet,'Chờ duyệt')
    dung('xóa dấu cũ',not any(d.get(k) for k in ('vgb_tang_y_kien','vgb_tang_nguoi_duyet','vgb_tang_luc_duyet','vgb_tang_dau_van')))

@ca('#290 D1 đơn treo chỉ lấy trước hôm nay, không lấy đơn đang phục vụ')
def treo():
    loc=[]
    def doc(dt,**kw):loc.append(kw['filters']);return []
    g=dict(frappe=NS(db=NS(get_all=doc)),getdate=lambda x:x,add_days=lambda d,n:'2026-09-11' if n==-1 else '2026-08-29',nowdate=lambda:'2026-09-12')
    nap('ban_hang.py','_quet_don_treo',g)()
    la('chặn trên ngày hôm qua',loc[0]['posting_date'],['between',['2026-08-29','2026-09-11']])

@ca('#290 B1 đồng bộ lại giữ lý do, loại, dấu duyệt người đã nhập')
def dong_bo_giu_tang():
    d=D(name='SI',docstatus=0,customer='KH',vgb_pt_thanh_toan='Hàng tặng',vgb_pt_do_may=1,vgb_xhd_ten='Tên đã nhập',vgb_xhd_mst='MST',vgb_xhd_email='a@b.invalid',vgb_tang_loai='marketing',vgb_tang_ly_do='Tặng sự kiện tiệm',vgb_tang_duyet='Đã duyệt',vgb_tang_nguoi_duyet='GD',flags=D())
    d.save=lambda:None;d.set=lambda k,v:d.__setitem__(k,v);d.append=lambda *a:None
    def doc(dt,loc,*a,**kw):return None if loc.get('docstatus')==2 else D(name='SI',docstatus=0)
    f=NS(db=NS(get_value=doc,exists=lambda *a:True),get_doc=lambda *a:d)
    g=dict(frappe=f,flt=lambda x:float(x or 0),cint=lambda x:int(x or 0),_dong_hang=lambda *a:([{'item_code':'BANH','qty':1,'rate':100}],[]),_lech_pancake=lambda *a:0,giu_khach_cua_don=lambda *a:True,_giam_tu_diem=lambda *a:0,_doan_thanh_toan=lambda *a:('Tiền mặt',''),_dien_dong_thanh_toan=lambda *a:None,nghi_cong_no=lambda *a:0,XHD_MAC_DINH='Khách lẻ')
    truoc=[d.get(k) for k in ('vgb_tang_loai','vgb_tang_ly_do','vgb_tang_duyet','vgb_tang_nguoi_duyet','vgb_pt_thanh_toan')]
    import sys
    from unittest.mock import patch
    with patch.dict(sys.modules,{'vagabond.khach_hang':NS(la_khach_gop=lambda x:False)}):
        nap('ban_hang.py','_upsert_hoa_don',g)({'id':'PK','display_id':'123','vgb_tang_ly_do':''},'2026-09-11','CT','KH')
    la('nguồn không đè người', [d.get(k) for k in ('vgb_tang_loai','vgb_tang_ly_do','vgb_tang_duyet','vgb_tang_nguoi_duyet','vgb_pt_thanh_toan')],truoc)

@ca('#290 B4 tắt kho gỡ xuất tự động cho nháp, không sửa dấu tờ đã ghi sổ')
def tat_kho():
    from unittest.mock import patch
    from vagabond import hang_tang_kho as kho
    from vagabond.khung.kiem_thu.thu_kho_tang_243 import _hd,_f
    for trang in (0,1):
        d=_hd(moi=0,vgb_tang_kho_moi=1,update_stock=1,vgb_tang_kho='KHO')
        f=_f(1);f.db.get_single_value=lambda *a:0
        f.db.get_value=lambda *a,**k:D(docstatus=trang,vgb_tang_kho_moi=1)
        with patch.object(kho,'frappe',f):kho.chuan_bi(d)
        la('dấu lịch sử hoặc tắt kho',d.vgb_tang_kho_moi,trang)
        la('không sửa update_stock của tờ đã chốt',d.update_stock,trang)

@ca('#290 B1 hook không lấy bảng máy đè Hàng tặng, bảng tay phải được kiểm lại')
def bang_may():
    from vagabond import thanh_toan_nhieu as ttn
    for may in (1,0):
        d=D(vgb_pt_thanh_toan='Hàng tặng')
        d[ttn.BANG]=[D(pt='Tiền mặt',so_tien=100,do_may=may)]
        d.set=lambda k,v:d.__setitem__(k,v)
        if may:
            ttn.dat_pt_chinh(d)
            la('gỡ bảng máy',d[ttn.BANG],[])
            la('giữ quà',d.vgb_pt_thanh_toan,'Hàng tặng')
        else:
            try: ttn.dat_pt_chinh(d)
            except Exception as e: dung('nhắc kiểm dòng tay','dòng thanh toán' in str(e))
            else: dung('phải chặn để không xóa tiền nhập tay',False)

@ca('#290 A2 chốt ngày bỏ quà chờ/từ chối, chỉ submit tờ đã duyệt')
def bo_qua_qua():
    from vagabond import ghi_so_dieu_kien
    ds={}
    da_ghi=[]
    for trang in ('Chờ duyệt','Từ chối','Đã duyệt'):
        d=D(name=trang,docstatus=0,custom_pancake_display_id=trang,vgb_pt_thanh_toan='Hàng tặng',vgb_tang_duyet=trang,flags=D())
        d.submit=lambda t=trang:da_ghi.append(t)
        ds[trang]=d
    def doc(dt,**kw): return list(ds) if kw['pluck']=='name' else []
    f=NS(db=NS(get_all=doc,commit=lambda:None),get_doc=lambda dt,n:ds[n])
    g=dict(frappe=f,_kiem_quyen=lambda:None,getdate=lambda x:x,nowdate=lambda:'2026-09-12',cfg=lambda:D(pancake_shop_id='SHOP',tu_ghi_so_quay=''),_sepay_theo_don=lambda *a:{},ghi_so_dieu_kien=ghi_so_dieu_kien,_chuan_bi_ghi_so=lambda *a:None,_tu_xuat_hddt=lambda *a:(False,''))
    r=nap('ban_hang.py','chot_doanh_so',g)('2026-09-11')
    la('chỉ tờ duyệt',da_ghi,['Đã duyệt']);la('không báo lỗi giả',r['loi'],[])
