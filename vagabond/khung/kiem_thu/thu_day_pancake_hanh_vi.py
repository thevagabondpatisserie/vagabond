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
        return [Doi(**rows[args[0]])] if args[0] in rows else []
    def commit():
        calls.append('commit'); saved.clear(); saved.update(copy.deepcopy(rows))
    def get_doc(dt,name=None):
        if isinstance(dt,dict):
            def insert(**kw):
                rows[kw['set_name']]={**dt,'name':kw['set_name']}
                return Doi(**rows[kw['set_name']])
            return NS(insert=insert)
        return item if dt=='Item' else Doi(**rows[name])
    db=NS(get_value=get_value,set_value=set_value,sql=sql,commit=commit,
          get_single_value=lambda *a:None)
    f=NS(db=db,get_doc=get_doc,session=NS(user='tester'),as_json=json.dumps,
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
    la('nhận chưa phải đã tạo',_nhan(g)['trang_thai'],'chua_ro')
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
