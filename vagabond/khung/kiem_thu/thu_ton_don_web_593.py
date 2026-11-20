"""F21: gọi cửa tạo đơn thật, chỉ giả IO; tồn đổi lúc gửi và nonce cũ."""
from datetime import date
from types import SimpleNamespace as D
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, dung, la, gia_lap

gia_lap()
from vagabond import ton_don_web as ton
from vagabond.khung.kiem_thu.thu_don_web_367 import _moi_truong_tao_don, _don, _Tra


def nguon(sl=1, decor=2, da_dat=0, co=True, btp=None):
    # v677: ngày kia và ngày thứ ba theo BTP sẵn; mặc định BTP sẵn bằng Đủ decor.
    return D(db=D(exists=lambda *a: co),
             get_doc=lambda *a: D(dong=[D(ma_hang='BAWC00139', ten_banh='CANDLE 12cm', co_the_ban=sl, da_dat=da_dat)]),
             get_single=lambda *a: D(dong=[D(ma_hang='BAWC00139', ten_banh='CANDLE 12cm', so_decor=decor,
                                             so_btp=decor if btp is None else btp)]))


def gui(sl=1, ngay='2026-10-13T13:00:00', **kw):
    vet, ham = _moi_truong_tao_don(lambda v: _Tra(200, {'data': {'id': '1'}}), **kw)
    d = _don(ngay_nhan=ngay, items=[{'variation_id': 'BAWC00139', 'quantity': sl}])
    return vet, ham, d


@ca('F21-1 đủ tồn thật tại lúc gửi thì tạo đơn')
def _():
    vet, ham, d = gui()
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon()):
        la('nhận', ham(d)['ok'], 1)
    dung('đã gọi Pancake', 'post' in vet.su)


@ca('F21-2/3 tồn giảm từ 1 về0 hoặc gửi vượt số còn: không ghi đơn, câu đúng')
def _():
    for con, xin in [(0,1),(1,2)]:
        vet, ham, d = gui(xin)
        with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(con)):
            r = ham(d)
        la('từ chối', r['ok'], 0)
        la('giao thức', r['ly_do'], 'het_hang')
        dung('nói món và số còn', 'CANDLE 12cm' in r['nhac'][0] and 'còn %s cái' % con in r['nhac'][0])
        dung('không sinh đơn hoặc gọi Pancake', 'ghi' not in vet.su and 'post' not in vet.su)


@ca('F21-4 thiếu phiếu không suy thành0; v675 sau 3 ngày tới không nhận bánh đặt trước')
def _():
    # v671, v675 (Sales 18 và 19/11/2026, giám đốc chốt): bánh đặt trước nhận tới ngày thứ ba.
    # Trước v671 đơn 17/10 (ngoài ba ngày decor) được nhận không giới hạn.
    vet, ham, d = gui(2, '2026-10-17T13:00:00')
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(0)):
        r = ham(d)
    la('ngày xa không nhận', (r['ok'], r['ly_do']), (0, 'het_hang'))
    dung('nhắc nhận trong 3 ngày tới', 'nhận trong 3 ngày tới' in r['nhac'][0] and 'CANDLE 12cm' in r['nhac'][0])
    dung('không gửi Pancake', 'post' not in vet.su)
    vet, ham, d = gui(2, '2026-10-13T13:00:00')
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(0, co=False)):
        la('chưa có phiếu hôm nay thì giữ nhận', ham(d)['ok'], 1)
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(0)):
        la('mã không trong nguồn', ton.kiem([{'variation_id':'BTPKHAC','quantity':20}], '2026-10-13'), [])
        la('mã không phải bánh đặt trước, ngày xa vẫn nhận', ton.kiem([{'variation_id':'BTPKHAC','quantity':20}], '2026-10-20'), [])


@ca('v671 ngày mai theo Có thể bán của phiếu NGÀY MAI, không theo Đủ decor; v677 ngày kia và ngày thứ ba theo BTP sẵn (Đủ decor 0 không chặn)')
def _():
    fr = nguon(1, decor=0, da_dat=0, btp=9)
    hoi = []
    goc = fr.get_doc
    fr.get_doc = lambda dt, ten: hoi.append(ten) or goc(dt, ten)
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', fr):
        r = ton.kiem([{'variation_id':'BAWC00139','quantity':2}], '2026-10-14')
        dung('chỉ còn 1 theo Có thể bán (BTP sẵn 9 không tính cho ngày mai)', 'còn 1 cái' in r[0])
        la('đọc đúng phiếu ngày mai', hoi[-1], 'KB-2026-10-14')
        la('đủ số thì nhận', ton.kiem([{'variation_id':'BAWC00139','quantity':1}], '2026-10-14'), [])
        for ng in ('2026-10-15', '2026-10-16'):
            la('ngày %s theo BTP sẵn 9: nhận' % ng, ton.kiem([{'variation_id':'BAWC00139','quantity':9}], ng), [])
            dung('ngày %s đặt 10: còn 9' % ng, 'còn 9 cái' in ton.kiem([{'variation_id':'BAWC00139','quantity':10}], ng)[0])
    # v677: Đủ decor 9 mà BTP sẵn chỉ 2 thì ngày kia còn 2 (Đủ decor không còn là nguồn).
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(1, decor=9, btp=2)):
        dung('Đủ decor 9, BTP sẵn 2: ngày kia còn 2', 'còn 2 cái' in ton.kiem([{'variation_id':'BAWC00139','quantity':3}], '2026-10-15')[0])
    # Có thể bán âm (bán lố) vẫn là hết, không phải không giới hạn.
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(-2)):
        dung('số âm là hết', 'còn 0 cái' in ton.kiem([{'variation_id':'BAWC00139','quantity':1}], '2026-10-14')[0])


@ca('F21-5 lỗi đọc tồn vẫn tạo đơn, ghi log và báo Sales')
def _():
    vet, ham, d = gui()
    with patch.object(ton, 'kiem', side_effect=RuntimeError('IO')), patch.object(ton, 'bao_loi') as bao:
        la('nhận', ham(d)['ok'], 1)
        dung('đã yêu cầu cảnh báo', bao.called)
    from vagabond import kenh_zalo
    fr=D(log_error=lambda *a,**k: vet.su.append('log'), get_traceback=lambda: 'IO')
    # v597: Zalo thay Lark (anh Việt 16/10/2026).
    with patch.object(ton,'frappe',fr), patch.object(kenh_zalo,'bao',lambda loai,chu_de,tieu_de,dong=None,**k: vet.su.append(('zalo',loai,chu_de,tieu_de,k.get('khoa'))) or ['Z1']):
        ton.bao_loi('2026-10-13')
    dung('log thật được gọi', 'log' in vet.su)
    dung('đúng chủ đề đơn web, loại cảnh báo, khoá theo ngày nhận', any(isinstance(x,tuple) and x[:3]==('zalo','canh_bao','don_web') and '2026-10-13' in x[3] and x[4]=='f21-ton-loi:2026-10-13' for x in vet.su))
    vet.su.clear()
    with patch.object(ton,'frappe',fr), patch.object(kenh_zalo,'bao',lambda *a,**k: []):
        ton.bao_loi('2026-10-13')
    la('chưa có nhóm nhận thì ghi thêm log hành động được', vet.su.count('log'), 2)


@ca('F21-6 nonce đã nhận đứng trước tồn, trả biên nhận cũ dù hết hàng')
def _():
    vet, ham, d=gui(trung=D(name='DW-CU'))
    with patch.object(ton, 'kiem', side_effect=AssertionError('không được gọi')) as kiem:
        r=ham(d)
    la('biên nhận cũ', (r['ok'],r['trung'],r['ma_yeu_cau']), (1,1,'DW-CU'))
    la('không hỏi tồn', kiem.call_count, 0)
    dung('không tạo lại', 'post' not in vet.su and 'ghi' not in vet.su)


@ca('F21 lỗi cả cảnh báo Sales không làm hỏng cửa nhận đơn')
def _():
    from vagabond import kenh_zalo
    vet, ham, d = gui()
    fr=D(log_error=lambda *a,**k: vet.su.append('log'), get_traceback=lambda: 'IO')
    with patch.object(ton, 'kiem', side_effect=RuntimeError('IO')), patch.object(ton,'frappe',fr), patch.object(kenh_zalo,'bao',side_effect=RuntimeError('Zalo')):
        la('nhận dù Sales lỗi',ham(d)['ok'],1)
        dung('ghi lỗi đọc và gửi',vet.su.count('log') >= 2)


@ca('F21 lỗi bên trong nguồn mùa vụ cũng báo Sales, giữ nhận')
def _():
    from vagabond import mua_vu
    with patch.object(mua_vu,'mua_dang_chay',lambda ngay: ['MUA']), patch.object(mua_vu,'_doc_mua',side_effect=RuntimeError('IO')):
        da_bao=[]
        la('không chặn',mua_vu.kiem_han_muc([{'item_code':'X','qty':1}], ngay='2026-10-13', khi_loi=lambda:da_bao.append(1)),[])
        la('cảnh báo',da_bao,[1])


@ca('v671 qua cửa tạo đơn: ngày mai đủ, thiếu, hết theo phiếu ngày mai; chưa có phiếu thì nhận')
def _phieu_mai():
    for co_the_ban, xin, con in [(2,2,None),(0,1,0),(1,2,1)]:
        fr = nguon(co_the_ban, decor=0)
        vet,ham,d=gui(xin,'2026-10-14T13:00:00')
        with patch.object(ton,'hom_nay',lambda:date(2026,10,13)),patch.object(ton,'frappe',fr):
            r=ham(d)
        if con is None:
            la('đủ số thì nhận',r['ok'],1)
            dung('đã gửi Pancake','post' in vet.su)
        else:
            la('chặn hết/thiếu',r['ly_do'],'het_hang')
            dung('đúng số còn','còn %s cái'%con in r['nhac'][0])
            dung('không gửi','post' not in vet.su)
    vet,ham,d=gui(5,'2026-10-14T13:00:00')
    with patch.object(ton,'hom_nay',lambda:date(2026,10,13)),patch.object(ton,'frappe',nguon(0,co=False)):
        la('chưa có phiếu ngày mai là chưa biết tồn, nhận như cũ',ham(d)['ok'],1)


@ca('F21 review: hom_nay thật dùng ngày Sài Gòn lúc 23:30 và 00:30')
def _moc_sai_gon():
    from datetime import datetime,timezone
    for utc,mong in [('2026-10-13T16:30:00+00:00',date(2026,10,13)),('2026-10-13T17:30:00+00:00',date(2026,10,14))]:
        moc=datetime.fromisoformat(utc)
        class DongHo(datetime):
            @classmethod
            def now(cls,tz=None):
                return moc.astimezone(tz) if tz else moc.replace(tzinfo=None)
        with patch.object(ton,'datetime',DongHo):
            la('ngày địa phương',ton.hom_nay(),mong)


@ca('F21 review: thiếu ngày nhận không đọc tồn và không báo Sales giả')
def _khong_ngay():
    for ngay in [None,'','   ']:
        vet,ham,d=gui(1,ngay)
        with patch.object(ton,'frappe',D()),patch.object(ton,'bao_loi') as bao:
            la('giữ nhận đơn',ham(d)['ok'],1)
            la('không cảnh báo giả',bao.call_count,0)
