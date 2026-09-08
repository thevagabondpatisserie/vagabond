"""#237: đồng bộ theo ID, không suy huỷ từ vắng mặt hay lỗi HTTP."""
from types import SimpleNamespace as NS
from unittest.mock import patch
from copy import deepcopy
from vagabond import van_don as vd
from vagabond.khung.kiem_thu.nen import ca, la, dung


def don(pid='1', **kw):
    return dict(id=pid, status=1, estimate_delivery_date='2026-09-10T08:00:00+07:00', items=[], **kw)


def lay(ds, ids, tra, ngay='2026-09-08', cache=None, cu_ids=None, hom_nay='2026-09-08', tre=None, het_han=None):
    loi, goi, filters, thong_ke = [], [], [], {}
    dong_ho = [0.0]
    cache = cache if cache is not None else {}
    def get(url, **kw):
        pid = url.rsplit('/', 1)[-1]
        goi.append(pid)
        doi = (tre or {}).get(pid, 0)
        dong_ho[0] += min(doi, kw['timeout'])
        if doi > kw['timeout']: raise TimeoutError('Lỗi mạng thử')
        x = tra[pid]
        if isinstance(x, Exception):
            raise x
        return NS(status_code=x[0], json=lambda: x[1])
    def dat_cache(k,v,t):
        cache[k]=v
        if het_han is not None: het_han[k]=t
    def danh_sach(*a, **kw):
        filters.append(kw['filters'])
        return [NS(pancake_id=i) for i in ((cu_ids or []) if isinstance(kw['filters']['ngay_giao'],list) else ids)]
    with patch.object(vd.frappe, 'get_all', danh_sach), patch.object(vd, '_mang', lambda: NS(get=get)), \
        patch.object(vd, 'nowdate', lambda:hom_nay), patch.object(vd.time,'monotonic',lambda:dong_ho[0]), patch.object(vd, 'cache_get', lambda k:cache.get(k)), \
        patch.object(vd, 'cache_set', dat_cache):
        ra=vd._bo_sung_don_da_co(ds, ngay, NS(pancake_shop_id='THU'), 'SECRET', loi, thong_ke)
    return ra, loi, goi, filters, thong_ke


@ca('#237: đơn dời ngày và huỷ vắng truy vấn cũ vẫn được đọc đúng ID')
def _roi_khoi_ngay():
    huy=don('2');huy['status']=6;huy.pop('items');huy.pop('estimate_delivery_date')
    ra,loi,goi,loc,_=lay([], ['1','2'], {'1':(200,{'data':don()}),'2':(200,{'data':huy})})
    la('đọc hai ID',goi,['1','2']);la('không lỗi',loi,[])
    la('giữ ngày mới',ra[0]['estimate_delivery_date'],'2026-09-10T08:00:00+07:00')
    la('giữ huỷ',ra[1]['status'],6)
    la('ưu tiên đúng ngày',loc[0]['ngay_giao'],'2026-09-08')
    la('quá hạn riêng',loc[1]['ngay_giao'],['<','2026-09-08'])


@ca('#237: 404, timeout, sai ID hoặc thiếu items không xoá dữ liệu và không chặn đơn khác')
def _loi_doc():
    for x in ((404,{}),RuntimeError('url?api_key=SECRET'),(200,{'data':don('SAI')}),
              (200,{'data':{'id':'1','status':1,'estimate_delivery_date':'2026-09-10'}})):
        ra,loi,_,_,_=lay([don('2')],['1'],{'1':x})
        la('vẫn trả đơn lành',[d['id'] for d in ra],['2'])
        la('có một lỗi',len(loi),1);dung('không lộ key','SECRET' not in str(loi))


@ca('#237: ID trùng không tạo hai đơn, hai bản khác nhau phải báo lỗi')
def _trung():
    ra,loi,_,_,_=lay([don(),don()],[],{})
    la('một đơn',len(ra),1);la('không lỗi',loi,[])
    khac=don();khac['status']=6
    ra,loi,_,_,_=lay([don(),khac],[],{})
    la('không tự chọn bản',ra,[]);la('có cảnh báo',len(loi),1)


@ca('#237: đối chiếu bổ sung có giới hạn và đi tiếp qua ID lỗi, không đói đơn cuối')
def _tiep_tuc():
    ids=['%02d'%i for i in range(25)]; cache={}
    tra={i:(404,{}) for i in ids}
    a=lay([],ids,tra,cache=cache);b=lay([],ids,tra,cache=cache)
    la('mỗi lượt tối đa20',len(a[2]),20)
    dung('lượt sau đi tiếp hết phần cuối',set(ids).issubset(set(a[2]+b[2])))
    la('chưa tới lượt không thành lỗi',len(a[1]),20)
    la('báo riêng còn chưa kiểm',a[4]['ngay']['chua_kiem'],5)


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


@ca('#237: giữ tương thích số lượng dạng số hoặc chuỗi số, chặn NaN')
def _so_luong():
    for sl in (2,2.5,'2','2.5','0'):
        o=don();o['items']=[{'quantity':sl,'variation_info':{'display_id':'THU','name':'Bánh'}}]
        la('đọc đúng số',vd._kiem_don_dong_bo(o),o)
    for sl in (None,'','NaN',float('inf'),-1,True):
        o=don();o['items']=[{'quantity':sl,'variation_info':{'name':'Bánh'}}]
        try: vd._kiem_don_dong_bo(o)
        except ValueError: pass
        else: dung('số lỗi phải chặn',False)


@ca('#237/93405: 1325 quá hạn không đứng trước 11 đơn ngày Sales xem')
def _khong_nghen_93405():
    cu=[str(i) for i in range(90000,91325)]
    moi=['93405']+[str(i) for i in range(93406,93416)]
    tra={i:(200,{'data':don(i)}) for i in cu+moi}
    ra,loi,goi,_,tk=lay([],moi,tra,cu_ids=cu)
    la('93405 được đọc đầu tiên',goi[0],'93405')
    la('đủ 11 đơn trong ngày trước',[d for d in goi[:11]],moi)
    la('giữ trần 20 request',len(goi),20)
    la('ngày đã đọc đủ',tk['ngay']['chua_kiem'],0)
    la('phần dư dành cho quá hạn',tk['qua_han']['da_thu'],9)
    la('không coi backlog là lỗi',loi,[])
    la('nguồn ngày mới',next(d for d in ra if d['id']=='93405')['estimate_delivery_date'],'2026-09-10T08:00:00+07:00')


@ca('#237: qua nửa đêm con trỏ quá hạn không quay về đầu')
def _qua_dem():
    cu=[str(i) for i in range(90000,90030)];cache={};het_han={}
    tra={i:(404,{}) for i in cu}
    a=lay([],[],tra,cu_ids=cu,cache=cache,het_han=het_han)
    b=lay([],[],tra,cu_ids=cu,cache=cache,ngay='2026-09-09',hom_nay='2026-09-09')
    la('tiếp sau 20 đơn lỗi của hôm qua',b[2][0],'90020')
    dung('qua ngày vẫn đọc hết các ID',set(cu).issubset(set(a[2]+b[2])))
    la('cursor ngày đầu',a[4]['qua_han']['moc_moi'],'90019')
    la('cursor quá hạn không TTL',het_han['van_don_237_v2:THU:qua_han'],None)


@ca('#237: ngày đông vẫn dành phần lượt cho quá hạn và quay vòng cả hai')
def _hai_hang():
    cu=[str(i) for i in range(90000,90025)]
    moi=[str(i) for i in range(93000,93025)];cache={}
    tra={i:(200,{'data':don(i)}) for i in cu+moi}
    a=lay([],moi,tra,cu_ids=cu,cache=cache)
    la('ngày có 16 lượt',a[4]['ngay']['da_thu'],16)
    la('quá hạn có 4 lượt',a[4]['qua_han']['da_thu'],4)
    b=lay([],moi,tra,cu_ids=cu,cache=cache)
    la('ngày tiếp đúng cursor',b[2][0],'93016')
    la('quá hạn cũng đi tiếp',b[4]['qua_han']['moc_cu'],'90003')
    tra['89999']=(200,{'data':don('89999')})
    gap=set()
    for _ in range(7):gap.update(lay([],moi,tra,cu_ids=['89999']+cu,cache=cache)[2])
    dung('ID nhỏ mới thêm không đói lượt','89999' in gap)


@ca('#237: mạng chậm bên ngày vẫn để quá hạn được thử; timeout không lộ key')
def _mang_cham_hai_hang():
    moi=['93000','93001','93002','93003'];cu=['90000','90001']
    tra={i:(200,{'data':don(i)}) for i in moi+cu}
    ra,loi,goi,_,tk=lay([],moi,tra,cu_ids=cu,tre={i:10 for i in moi+cu})
    la('ngày dừng sau hết 12 giây',tk['ngay']['da_thu'],3)
    la('quá hạn vẫn được thử',tk['qua_han']['da_thu'],1)
    la('lỗi đọc đếm riêng',len(loi),4)
    la('chưa đọc ngày còn một',tk['ngay']['chua_kiem'],1)
    dung('không lộ khoá','SECRET' not in str(loi))


@ca('#237: xem ngày khác chỉ đối chiếu ngày đó, không quay hàng quá hạn')
def _ngay_khac():
    cache={'van_don_237_v2:THU:qua_han':'90015'}
    a=lay([],['93405'],{'93405':(200,{'data':don('93405')})},ngay='2026-09-10',cu_ids=['90000'],cache=cache)
    la('chỉ gọi đơn ngày đang xem',a[2],['93405'])
    la('giữ cursor quá hạn',cache['van_don_237_v2:THU:qua_han'],'90015')
