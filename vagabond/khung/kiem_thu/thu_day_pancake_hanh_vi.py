"""#210: gọi cửa thật với DB/HTTP giả, chốt thứ tự commit và không POST lại."""
import ast
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
from vagabond import pancake_ket_qua as kq
from vagabond.khung.kiem_thu.nen import ca, la, dung, Doi

SRC = Path(__file__).resolve().parents[2] / 'pancake_sp.py'

def _canh():
    rows={}; saved={}; calls=[]; jobs=[]
    item=Doi(name='KT210',item_code='KT210',item_name='Món thử',disabled=0,is_sales_item=1,standard_rate=15000,image='')
    def get_value(dt,name,fields,**kw):
        return Doi(**rows[name]) if name in rows else None
    def set_value(dt,name,key,value=None):
        rows[name].update(key if isinstance(key,dict) else {key:value})
    def sql(query,args,**kw):
        calls.append('lock')
        if query.startswith('update '):
            tt,bao,vet,ten,ma_lan=args
            if rows[ten]['ma_lan']==ma_lan and rows[ten]['trang_thai']=='dang_gui':
                rows[ten].update(trang_thai=tt,thong_bao=bao,vet_gui=vet)
            return []
        return [Doi(**rows[args[0]])] if args[0] in rows else []
    def commit():
        calls.append('commit'); saved.clear(); saved.update(copy.deepcopy(rows))
    def get_doc(dt,name=None):
        if isinstance(dt,dict):
            def insert(**kw):
                rows[kw['set_name']]={'vet_gui':None,'thong_bao':None,'lich_su_doi_soat':None,**dt,'name':kw['set_name']}
                return Doi(**rows[kw['set_name']])
            return NS(insert=insert)
        return item if dt=='Item' else Doi(**rows[name])
    db=NS(get_value=get_value,set_value=set_value,sql=sql,commit=commit,
          get_single_value=lambda *a:None)
    f=NS(clear_document_cache=lambda *a:calls.append(("clear_cache",a)),db=db,get_doc=get_doc,session=NS(user='tester'),as_json=json.dumps,
         utils=NS(now_datetime=lambda:'2026-09-12 12:00:00'),QueryTimeoutError=TimeoutError,log_error=lambda **kw:calls.append(kw),
         has_permission=lambda *a:True,whitelist=lambda **kw:lambda f:f,
         enqueue=lambda *a,**kw:jobs.append(kw),throw=lambda msg:(_ for _ in ()).throw(ValueError(msg)))
    http=NS(post=lambda *a,**kw:None)
    tree=ast.parse(SRC.read_text())
    tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]
    g={'frappe':f,'requests':http,'kq':kq,'cint':int,'flt':lambda x:float(x or 0),
       'get_url':str,'cfg':lambda:Doi(pancake_shop_id='S'),'key':lambda *a:'fake',
       'PANCAKE':'https://example.invalid','TIMEOUT':1}
    exec(compile(tree,str(SRC),'exec'),g)
    g['tim_het_tren_pancake']=lambda *a:([],True)
    return g,f,http,rows,saved,calls,jobs

def _nhan(g):
    dm=NS(_kiem_quyen=lambda:None,_duoc_tao=lambda:True)
    with patch.dict(sys.modules,{'vagabond.danh_muc':dm}):
        return g['tao_tren_pancake']('KT210')

@ca('#210 nhận yêu cầu không POST và job chỉ enqueue sau commit')
def _nhan_khong_gui():
    g,f,http,rows,saved,calls,jobs=_canh()
    http.post=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('POST trong request'))
    la('nhận chưa phải đã tạo',_nhan(g)['trang_thai'],'dang_cho')
    la('chỉ một dấu',len(rows),1)
    dung('sau commit',jobs[0]['enqueue_after_commit'])
    la('không commit giao dịch người gọi',calls,['lock'])
    _nhan(g)
    la('bấm lặp không nhân dấu',len(rows),1)

@ca('#210 timeout sau POST rồi rollback/reload/tìm rỗng vẫn không POST lại')
def _timeout_ben():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);f.db.commit()
    count=[]
    def post(*a,**kw):
        dung('đã lưu bền dấu gửi',next(iter(saved.values()))['trang_thai']=='dang_gui')
        count.append(1);raise TimeoutError('mất phản hồi')
    http.post=post;ten=next(iter(rows))
    g['chay_luot_day'](ten)
    la('kết quả chưa rõ',rows[ten]['trang_thai'],'chua_ro')
    rows.clear();rows.update(copy.deepcopy(saved))
    _nhan(g);g['chay_luot_day'](ten)
    la('GET rỗng không giải phóng dấu',g['trang_thai_tren_pancake']('KT210')['trang_thai'],'chua_ro')
    la('chỉ POST một lần',len(count),1)

@ca('#210 job lặp trong lúc POST không có lượt gửi thứ hai')
def _job_lap():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows));count=[]
    def post(*a,**kw):
        count.append(1);g['chay_luot_day'](ten)
        return NS(status_code=201,json=lambda:{'success':True})
    http.post=post;g['chay_luot_day'](ten);g['chay_luot_day'](ten)
    la('một POST',len(count),1);la('đã tạo',rows[ten]['trang_thai'],'da_tao')

@ca('#210 commit dấu gửi lỗi thì tuyệt đối không gọi HTTP')
def _commit_hong():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g)
    f.db.commit=lambda:(_ for _ in ()).throw(OSError('db'))
    http.post=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('đã POST'))
    try:g['chay_luot_day'](next(iter(rows)))
    except OSError:pass
    else:dung('phải thất bại',False)

@ca('#210 HTTP lỗi hoặc JSON hỏng sau POST luôn giữ chưa rõ')
def _phan_hoi_hong():
    for response in [NS(status_code=502,json=lambda:{'success':False}),
                     NS(status_code=200,json=lambda:[]),
                     NS(status_code=201,json=lambda:(_ for _ in ()).throw(ValueError('json')))]:
        g,f,http,rows,saved,calls,jobs=_canh();_nhan(g)
        http.post=lambda *a,**kw:response
        g['chay_luot_day'](next(iter(rows)))
        la('không cho gửi lại',next(iter(rows.values()))['trang_thai'],'chua_ro')

@ca('#210 tìm trùng hoặc quét dở không gửi POST')
def _quet_chan():
    for data,du in [([{},{}],True),([],False)]:
        g,f,http,rows,saved,calls,jobs=_canh();_nhan(g)
        g['tim_het_tren_pancake']=lambda *a:(data,du)
        http.post=lambda *a,**kw:(_ for _ in ()).throw(AssertionError('đã POST'))
        g['chay_luot_day'](next(iter(rows)))
        la('kết quả',next(iter(rows.values()))['trang_thai'],'xung_dot' if du else 'loi')

@ca('#210 giá âm và vô hạn không qua được xác nhận giá0')
def _gia_xau():
    for gia in [-1,float('nan'),float('inf'),'hong']:
        la('chặn kể cả xác nhận',kq.gia_dung_de_day(gia,True)[0],False)


@ca('#210 giao diện: kiểm lại và xác nhận giá0 chạy đúng cửa')
def _nut_that():
    import subprocess
    script=Path(__file__).parent/'hanh_vi'/'day_pancake.js'
    r=subprocess.run(['node',str(script)],capture_output=True,text=True,timeout=30)
    la(r.stdout+r.stderr,r.returncode,0)


@ca('#210 dữ liệu hỏng trước HTTP không khóa thành chưa rõ')
def _du_lieu_hong():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows))
    rows[ten]['du_lieu']='{'
    count=[];http.post=lambda *a,**kw:count.append(1)
    g['chay_luot_day'](ten)
    la('không POST',count,[])
    la('được lập yêu cầu lại',rows[ten]['trang_thai'],'loi')

@ca('#210 kiểm lại có bằng chứng thì lưu kết quả, mất mã không báo xanh')
def _doi_soat():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows))
    rows[ten]['trang_thai']='chua_ro'
    g['tim_het_tren_pancake']=lambda *a:([{'display_id':'KT210'}],True)
    la('đã đối soát',g['trang_thai_tren_pancake']('KT210')['trang_thai'],'da_co')
    la('lần sau nhớ kết quả',_nhan(g)['trang_thai'],'da_co')
    g['tim_het_tren_pancake']=lambda *a:([],True)
    la('mất mã không báo xanh',g['trang_thai_tren_pancake']('KT210')['ok'],0)
    la('không tự mở tạo lại',rows[ten]['trang_thai'],'da_co')


@ca('#210 mở lại cần quyền và bằng chứng, có lịch sử và vô hiệu worker cũ')
def _mo_lai():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows))
    f.get_roles=lambda:['Purchase User']
    try:g['doi_soat_luot'](ten,'Lý do đủ dài','Bằng chứng đủ dài',1)
    except ValueError:pass
    else:dung('phải chặn quyền',False)
    f.get_roles=lambda:['System Manager'];f.utils=NS(now_datetime=lambda:'2026-09-12 12:00:00')
    rows[ten].update(trang_thai='chua_ro',lich_su_doi_soat='[]')
    old=rows[ten]['ma_lan']
    try:g['doi_soat_luot'](ten,'Lý do đủ dài','',1)
    except ValueError:pass
    else:dung('phải có bằng chứng',False)
    g['doi_soat_luot'](ten,'Pancake xác minh chưa tạo','Yêu cầu hỗ trợ PC-210 xác nhận xong',1)
    la('mở lại',rows[ten]['trang_thai'],'loi')
    dung('đổi mã lần',rows[ten]['ma_lan']!=old)
    la('ghi người',json.loads(rows[ten]['lich_su_doi_soat'])[0]['nguoi'],'tester')

@ca('#210 worker cũ bị mở lại giữa hai khóa không được POST')
def _fence():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows))
    old_commit=f.db.commit
    def commit():
        old_commit();rows[ten]['ma_lan']='một lần khác'
    f.db.commit=commit;count=[];http.post=lambda *a,**kw:count.append(1)
    g['chay_luot_day'](ten)
    la('worker cũ không gửi',count,[])


@ca('#210 quét trang thật không đọc trang thiếu thành không có')
def _quet_trang():
    g,f,http,rows,saved,calls,jobs=_canh()
    tree=ast.parse(SRC.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='tim_het_tren_pancake')
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(SRC),'exec'),g)
    pages=[]
    def get(*a,**kw):
        page=kw['params']['page_number'];pages.append(page)
        return NS(raise_for_status=lambda:None,json=lambda:{'data':([{'display_id':'OTHER'}]*100 if page==1 else [{'display_id':'KT210'}])})
    http.get=get
    ds,du=g['tim_het_tren_pancake'](g['cfg'](),'fake','KT210')
    la('đọc trang hai',pages,[1,2]);la('đúng mã',len(ds),1);dung('quét đủ',du)
    http.get=lambda *a,**kw:NS(raise_for_status=lambda:None,json=lambda:{})
    la('schema thiếu không phải không có',g['tim_het_tren_pancake'](g['cfg'](),'fake','KT210'),([],False))

@ca('#210 đọc giá ưu tiên bảng bán rồi mới giá mặt hàng')
def _gia_ban():
    g,f,http,rows,saved,calls,jobs=_canh()
    f.db.get_single_value=lambda *a:'Bán'
    f.db.get_value=lambda *a,**kw:22000
    la('lấy bảng bán',g['_gia_niem_yet'](f.get_doc('Item','KT210')),22000)
    f.db.get_value=lambda *a,**kw:None
    la('giá mặt hàng khi không có giá bán',g['_gia_niem_yet'](f.get_doc('Item','KT210')),15000)


@ca('#210 vết lỗi có HTTP và loại lỗi, không lộ khóa trong phản hồi')
def _vet_loi():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g)
    http.post=lambda *a,**kw:NS(status_code=502,text='api_key=SECRET',json=lambda:{'success':False})
    g['chay_luot_day'](next(iter(rows)))
    vet=next(iter(rows.values()))['vet_gui']
    la('HTTP được lưu',json.loads(vet)['http'],502)
    dung('không giữ body/khóa','SECRET' not in str(calls)+vet)
    dung('có nhật ký',any(isinstance(x,dict) and 'message' in x for x in calls))

@ca('#210 không chờ khóa trong request và đọc lại sau GET')
def _khoa_ban():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows));rows[ten]['trang_thai']='dang_gui'
    old=f.db.get_value
    def busy(*a,**kw):
        if kw.get('for_update'):
            la('NOWAIT',kw.get('wait'),False);raise TimeoutError('lock')
        return old(*a,**kw)
    f.db.get_value=busy
    la('bận trả câu chờ',_nhan(g)['trang_thai'],'dang_cho')
    f.db.get_value=old
    def scan(*a):
        rows[ten].update(trang_thai='loi',thong_bao='Chưa quét hết - lần cũ')
        return [],True
    g['tim_het_tren_pancake']=scan
    ket=g['trang_thai_tren_pancake']('KT210')
    la('đọc mới sau GET',ket['trang_thai'],'chua_co')
    dung('bỏ câu lỗi quét cũ','Chưa quét hết' not in ket['thong_bao'])

@ca('#210 worker cũ không ghi đè trạng thái đã đối soát')
def _cas():
    g,f,http,rows,saved,calls,jobs=_canh();_nhan(g);ten=next(iter(rows))
    def post(*a,**kw):
        rows[ten].update(ma_lan='lan-moi',trang_thai='loi')
        return NS(status_code=201,json=lambda:{'success':True})
    http.post=post;g['chay_luot_day'](ten)
    la('giữ trạng thái mới',rows[ten]['trang_thai'],'loi')
    dung('xóa cache cả khi lượt cũ bị chặn',('clear_cache',(g['DT_DAY'],ten)) in calls)


@ca('#210 quyền bán hàng không đủ để ghi kết quả kiểm lại')
def _quyen_kiem():
    from unittest.mock import MagicMock
    dm=SRC.with_name('danh_muc.py')
    fn=next(n for n in ast.parse(dm.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='kiem_ma_tren_pancake')
    fn.decorator_list=[]
    f=MagicMock();f.throw.side_effect=ValueError('Không có quyền')
    g=dict(frappe=f,_kiem_quyen=lambda:None,_duoc_tao=lambda:False)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),str(dm),'exec'),g)
    try:g['kiem_ma_tren_pancake']('KT210')
    except ValueError:pass
    else:dung('phải bị chặn trước GET',False)


@ca('#210 không đọc được giá hoặc giá lẻ đồng thì chưa nhận gửi')
def _gia_khong_doc():
    g,f,http,rows,saved,calls,jobs=_canh()
    f.db.get_single_value=lambda *a:(_ for _ in ()).throw(ValueError('schema'))
    la('lỗi có hành động',_nhan(g)['trang_thai'],'loi')
    la('không enqueue',jobs,[])
    f.db.get_single_value=lambda *a:None
    f.get_doc('Item','KT210').standard_rate=0.5
    la('không cắt thành giá0',_nhan(g)['trang_thai'],'loi')
    la('không enqueue giá lẻ',jobs,[])
