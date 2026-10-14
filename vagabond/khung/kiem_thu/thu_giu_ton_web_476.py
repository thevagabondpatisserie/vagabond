"""Giữ tồn cuối giao dịch, dùng hàm thật và giả I/O."""
import json
from datetime import date
from types import SimpleNamespace as D
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, la, dung, gia_lap

gia_lap()
from vagabond import giu_ton_web as g


def doc(so=1, dem=False, ngay='2026-10-14'):
    return D(name='DW',ngay_nhan=ngay,pancake_id='123',snapshot=json.dumps({g.O:{'dong':{'A':so},'da_dem':dem}}))


def moi(don=(), ton=1, decor=0, dd=0):
    vet=[]
    def sql(q,args=None,**kw):
        vet.append(q)
        if 'tabSingles' in q:return [('pancake_shop_id',)]
        if 'tabKiem Banh Dong' in q:return [D(ma_hang='A',ten_banh='Bánh A',co_the_ban=ton,da_dat=dd)]
        if 'tabBTP Banh O Dong' in q:return [D(ma_hang='A',ten_banh='Bánh A',so_decor=decor)]
        if 'tabVagabond Don Web' in q:return don
        raise AssertionError(q)
    return D(db=D(sql=sql)),vet


@ca('#476 giữ tồn: hai dòng cùng mã phải cộng trước khi kiểm')
def _():
    thieu,dong=g.tinh([{'variation_id':'A','quantity':1}]*2,{'A':(1,'Bánh')},{})
    la('thiếu',thieu,[('Bánh',1,2)]);la('giữ cộng',dong,{'A':2})


@ca('#476 giữ tồn: chiếc cuối đã giữ thì lượt sau không nhận; current read dưới khoá')
def _():
    f,vet=moi([doc()])
    with patch.object(g,'frappe',f),patch.object(g,'hom_nay',lambda:date(2026,10,14)):
        nhac,giu=g.kiem_va_giu([{'variation_id':'A','quantity':1}],'2026-10-14')
    dung('hết bánh',bool(nhac) and 'còn 0' in nhac[0])
    dung('mọi lượt đọc khoá',all('for update' in q for q in vet))
    dung('khoá chung trước đọc tồn','tabSingles' in vet[0])


@ca('#476 giữ tồn: đơn đã tính trong KB không bị trừ lần hai')
def _():
    f,_=moi([doc(dem=True)],ton=1)
    with patch.object(g,'frappe',f),patch.object(g,'hom_nay',lambda:date(2026,10,14)):
        nhac,giu=g.kiem_va_giu([{'variation_id':'A','quantity':1}],'2026-10-14')
    la('không trừ hai lần',nhac,[]);la('giữ mới',giu['dong'],{'A':1})


@ca('#476 giữ tồn: decor0 nhận làm theo đơn; decor dùng chung ba ngày')
def _():
    for decor,thieu in ((0,False),(1,True),(2,False)):
        f,_=moi([doc(ngay='2026-10-15')],decor=decor)
        with patch.object(g,'frappe',f),patch.object(g,'hom_nay',lambda:date(2026,10,14)):
            nhac,giu=g.kiem_va_giu([{'variation_id':'A','quantity':1}],'2026-10-16')
        la('thiếu theo nguồn',bool(nhac),thieu)
        if decor==0:la('không giữ nguồn không biết',giu,None)


@ca('#476 giữ tồn: không ngày hoặc ngoài ba ngày không khoá và không cảnh báo giả')
def _():
    with patch.object(g,'frappe',D()),patch.object(g,'hom_nay',lambda:date(2026,10,14)):
        for ngay in ('',None,'2026-10-18'):
            la('không áp',g.kiem_va_giu([{'variation_id':'A','quantity':1}],ngay),([],None))


@ca('#476 giữ tồn: đồng bộ chỉ đánh dấu đúng đơn được tính, không đụng đơn cũ')
def _():
    d=doc();luu=[]
    f,_=moi([d]);f.db.set_value=lambda *a,**kw:luu.append(a)
    with patch.object(g,'frappe',f):
        g.da_dem('2026-10-14',['123'])
    la('một cập nhật',len(luu),1);la('đã tính',json.loads(luu[0][2]['snapshot'])[g.O]['da_dem'],True)


@ca('#476 giữ tồn: lưu đơn đọc cũ không ghi đè dấu KB vừa tính')
def _():
    d=doc();d.is_new=lambda:False
    f=D(db=D(get_value=lambda *a,**kw:doc(dem=True).snapshot))
    with patch.object(g,'frappe',f):g.bao_ve(d)
    la('giữ dấu mới',json.loads(d.snapshot)[g.O]['da_dem'],True)


@ca('#476 cửa tạo đơn: kiểm lại cuối giao dịch chặn khách thứ hai, không POST Pancake')
def _():
    from vagabond.khung.kiem_thu.thu_ton_don_web_593 import gui
    from vagabond import ton_don_web as ton
    vet,ham,d=gui(1,'2026-10-14T13:00:00')
    f,_=moi([D(name='DW',ngay_nhan='2026-10-14',pancake_id='',snapshot=json.dumps({g.O:{'dong':{'BAWC00139':1},'da_dem':False}}))])
    goc=f.db.sql
    def sql(q,*a,**kw):
        rows=goc(q,*a,**kw)
        if 'tabKiem Banh Dong' in q:
            for row in rows:row.ma_hang='BAWC00139'
        return rows
    f.db.sql=sql
    with patch.object(g,'frappe',f),patch.object(g,'hom_nay',lambda:date(2026,10,14)),patch.object(ton,'kiem',lambda *a:[]):
        kq=ham(d)
    la('thiếu tồn',kq['ly_do'],'het_hang');dung('chưa tạo và gửi','ghi' not in vet.su and 'post' not in vet.su)


@ca('#476 cửa tạo đơn: lỗi đọc chỗ giữ vẫn nhận và báo Sales theo cách B')
def _():
    from vagabond.khung.kiem_thu.thu_ton_don_web_593 import gui
    from vagabond import ton_don_web as ton
    vet,ham,d=gui(1,'2026-10-14T13:00:00')
    with patch.object(g,'kiem_va_giu',side_effect=RuntimeError('DB đọc lỗi')),patch.object(ton,'kiem',lambda *a:[]),patch.object(ton,'bao_loi') as bao:
        la('vẫn nhận',ham(d)['ok'],1);la('báo Sales',bao.call_count,1)
    dung('đã gửi','post' in vet.su)


@ca('#476 dời ngày Pancake: nhận ID ngày mới, đồng bộ ngày cũ không trừ decor hai lần')
def _():
    d=doc(dem=True,ngay='2026-10-15');f,_=moi([d],decor=2)
    def luu(dt,name,fields,**kw):d.snapshot=fields['snapshot']
    f.db.set_value=luu
    with patch.object(g,'frappe',f),patch.object(g,'hom_nay',lambda:date(2026,10,14)):
        g.da_dem('2026-10-16',['123'])
        la('nguồn mới',json.loads(d.snapshot)[g.O].get('ngay_nguon'),'2026-10-16')
        g.da_dem('2026-10-15',[])
        dung('ngày cũ không xóa dấu',json.loads(d.snapshot)[g.O]['da_dem'])
        # KB của ngày mới đã trừ một decor, chỉ còn một. Không trừ giữ nữa.
        f.db.sql=lambda q,*a,**kw: [('pancake_shop_id',)] if 'tabSingles' in q else (
            [D(ma_hang='A',ten_banh='A',so_decor=1)] if 'tabBTP Banh O Dong' in q else (
            [d] if 'tabVagabond Don Web' in q else []))
        nhac,_giu=g.kiem_va_giu([{'variation_id':'A','quantity':1}],'2026-10-17')
        la('vẫn bán được phần còn lại',nhac,[])
        g.da_dem('2026-10-16',[])
        dung('chỉ ngày nguồn mất ID mới nhả dấu',not json.loads(d.snapshot)[g.O]['da_dem'])


@ca('#476 P3 ngày nguồn có chỉ mục, dời ngày đọc thêm đúng ID và gộp không trùng')
def _():
    d=doc();vet=[]
    def sql(q,args,**kw):
        vet.append((q,args));return [d]
    with patch.object(g,'frappe',D(db=D(sql=sql))),patch.object(g,'hom_nay',lambda:date(2026,10,14)):
        la('gộp cùng bản ghi',g._don(['123']),[d])
    la('chỉ hai phạm vi',len(vet),2)
    if len(vet)!=2:return
    dung('ngày dùng chỉ mục','force index (vgb_ngay_nguon_ton)' in vet[0][0])
    dung('ID dùng chỉ mục','force index (pancake_id)' in vet[1][0])
    dung('không LIKE/JSON quét cả bảng',all('like' not in q.lower() and 'json_' not in q.lower() for q,_ in vet))
    la('bốn ngày',vet[0][1],('2026-10-14','2026-10-18'))
    la('ID đúng',vet[1][1],(('123',),))
    la('không có giữ không có ngày',g.ngay_nguon({},'2026-10-14'),None)
    la('ngày giữ ban đầu',g.ngay_nguon({g.O:{'dong':{'A':1}}},'2026-10-14T13:00'),'2026-10-14')
    la('ngày dời thắng ngày gốc',g.ngay_nguon({g.O:{'dong':{'A':1},'ngay_nguon':'2026-10-16'}},'2026-10-14'),'2026-10-16')
