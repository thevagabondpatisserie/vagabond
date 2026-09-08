"""#237: đồng bộ theo ID, không suy huỷ từ vắng mặt hay lỗi HTTP."""
from types import SimpleNamespace as NS
from unittest.mock import patch
from copy import deepcopy
from vagabond import van_don as vd
from vagabond.khung.kiem_thu.nen import ca, la, dung


def don(pid='1', **kw):
    return dict(id=pid, status=1, estimate_delivery_date='2026-09-10T08:00:00+07:00', items=[], **kw)


def lay(ds, ids, tra, ngay='2026-09-08', cache=None):
    loi, goi, filters = [], [], []
    cache = cache if cache is not None else {}
    def get(url, **kw):
        pid = url.rsplit('/', 1)[-1]
        goi.append(pid)
        x = tra[pid]
        if isinstance(x, Exception):
            raise x
        return NS(status_code=x[0], json=lambda: x[1])
    def danh_sach(*a, **kw):
        filters.append(kw['filters'])
        return [NS(pancake_id=i) for i in ids]
    with patch.object(vd.frappe, 'get_all', danh_sach), patch.object(vd, '_mang', lambda: NS(get=get)), \
        patch.object(vd, 'nowdate', lambda:'2026-09-08'), patch.object(vd, 'cache_get', lambda k:cache.get(k)), \
        patch.object(vd, 'cache_set', lambda k,v,t:cache.update({k:v})):
        ra=vd._bo_sung_don_da_co(ds, ngay, NS(pancake_shop_id='THU'), 'SECRET', loi)
    return ra, loi, goi, filters


@ca('#237: đơn dời ngày và huỷ vắng truy vấn cũ vẫn được đọc đúng ID')
def _roi_khoi_ngay():
    huy=don('2');huy['status']=6;huy.pop('items');huy.pop('estimate_delivery_date')
    ra,loi,goi,loc=lay([], ['1','2'], {'1':(200,{'data':don()}),'2':(200,{'data':huy})})
    la('đọc hai ID',goi,['1','2']);la('không lỗi',loi,[])
    la('giữ ngày mới',ra[0]['estimate_delivery_date'],'2026-09-10T08:00:00+07:00')
    la('giữ huỷ',ra[1]['status'],6)
    la('cron hôm nay soát quá hạn',loc[0]['ngay_giao'],['<=','2026-09-08'])


@ca('#237: 404, timeout, sai ID hoặc thiếu items không xoá dữ liệu và không chặn đơn khác')
def _loi_doc():
    for x in ((404,{}),RuntimeError('url?api_key=SECRET'),(200,{'data':don('SAI')}),
              (200,{'data':{'id':'1','status':1,'estimate_delivery_date':'2026-09-10'}})):
        ra,loi,_,_=lay([don('2')],['1'],{'1':x})
        la('vẫn trả đơn lành',[d['id'] for d in ra],['2'])
        la('có một lỗi',len(loi),1);dung('không lộ key','SECRET' not in str(loi))


@ca('#237: ID trùng không tạo hai đơn, hai bản khác nhau phải báo lỗi')
def _trung():
    ra,loi,_,_=lay([don(),don()],[],{})
    la('một đơn',len(ra),1);la('không lỗi',loi,[])
    khac=don();khac['status']=6
    ra,loi,_,_=lay([don(),khac],[],{})
    la('không tự chọn bản',ra,[]);la('có cảnh báo',len(loi),1)


@ca('#237: đối chiếu bổ sung có giới hạn và đi tiếp qua ID lỗi, không đói đơn cuối')
def _tiep_tuc():
    ids=['%02d'%i for i in range(25)]; cache={}
    tra={i:(404,{}) for i in ids}
    a=lay([],ids,tra,cache=cache);b=lay([],ids,tra,cache=cache)
    la('mỗi lượt tối đa20',len(a[2]),20)
    dung('lượt sau đi tiếp hết phần cuối',set(ids).issubset(set(a[2]+b[2])))
    dung('báo còn chưa kiểm',any('Còn' in d['loi'] for d in a[1]))


@ca('#237: thiếu dữ liệu liên hệ không bị hiểu là khách xoá; rỗng rõ mới cập nhật')
def _thieu_truong():
    moi={k:'MOI' for k in ('khach','dia_chi','ghi_chu','ghi_chu_in','tag_gio','tien_thu_ho')}
    la('giữ trường cũ khi nguồn thiếu',vd._giu_truong_thieu(don(),moi,False),{})
    moi={'khach':'','dia_chi':'','ghi_chu':''}
    vd._giu_truong_thieu({'bill_full_name':'','shipping_address':{'full_address':''},'note':''},moi,False)
    la('rỗng rõ vẫn truyền',moi,{'khach':'','dia_chi':'','ghi_chu':''})


@ca('#237: bảng món rỗng được lưu, không giữ bánh đã bị bỏ hết')
def _rong():
    class Doc:
        def __init__(self): self.mon=[{'ten':'Cũ'}];self.flags=NS();self.saved=0
        def set(self,k,v): setattr(self,k,v)
        def append(self,k,v): getattr(self,k).append(v)
        def save(self,**kw): self.saved+=1
    d=Doc()
    with patch.object(vd.frappe,'get_doc',lambda *a,**kw:d): vd._ghi_mon('THU',[])
    la('xoá đúng bảng con',d.mon,[]);la('save thật được gọi',d.saved,1)


@ca('#237: phí book chặn số sai và người không có quyền trước ghi')
def _phi_sai():
    def nem(c): raise ValueError(c)
    with patch.object(vd.frappe,'throw',nem), patch.object(vd,'_la_sales',lambda:True), \
        patch.object(vd.frappe,'get_doc',side_effect=AssertionError('không được đọc/ghi')):
        for so in ('NaN','inf',-1,0.5,'',None):
            try: vd.luu_phi_book('THU',so)
            except ValueError: pass
            else: dung('phải chặn',False)
    with patch.object(vd.frappe,'throw',nem),patch.object(vd,'_la_sales',lambda:False),patch.object(vd,'_la_ke_toan',lambda:False):
        try: vd.luu_phi_book('THU',100)
        except ValueError: pass
        else: dung('phải chặn quyền',False)


@ca('#237: tên phường theo đúng hai khoá Pancake, district không xoá phường')
def _phuong_thieu():
    for khoa in ('commune_name','commnue_name'):
        moi={'phuong':'Phường mới'}
        vd._giu_truong_thieu({'shipping_address':{khoa:'Phường mới'}},moi,False)
        la('giữ phường nguồn',moi,{'phuong':'Phường mới'})
    la('district không phải phường',vd._giu_truong_thieu({'shipping_address':{'district_name':'Quận'}},{'phuong':''},False),{})


@ca('#237: HTTP200 lỗi/thiếu data không được coi là không có đơn')
def _danh_sach_loi():
    from vagabond import kiem_banh as kb
    for body in ({}, {'success':False,'data':[]}, {'data':None}, {'data':{}}):
        with patch.object(kb,'_mang',lambda:NS(get=lambda *a,**kw:NS(status_code=200,json=lambda:body))):
            try: kb._keo_don(NS(pancake_shop_id='THU'),'KEY','estimate_delivery_date',1,2)
            except kb.LoiPancake: pass
            else: dung('phải báo lỗi',False)
    with patch.object(kb,'_mang',lambda:NS(get=lambda *a,**kw:NS(status_code=200,json=lambda:{'data':[]}))):
        la('rỗng hợp lệ',kb._keo_don(NS(pancake_shop_id='THU'),'KEY','estimate_delivery_date',1,2),[])
