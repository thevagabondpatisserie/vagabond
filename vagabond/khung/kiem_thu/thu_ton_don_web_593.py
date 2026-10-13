"""F21: gọi cửa tạo đơn thật, chỉ giả IO; tồn đổi lúc gửi và nonce cũ."""
from datetime import date
from types import SimpleNamespace as D
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, dung, la, gia_lap

gia_lap()
from vagabond import ton_don_web as ton
from vagabond.khung.kiem_thu.thu_don_web_367 import _moi_truong_tao_don, _don, _Tra


def nguon(sl=1, decor=2, da_dat=0, co=True):
    return D(db=D(exists=lambda *a: co),
             get_doc=lambda *a: D(dong=[D(ma_hang='BAWC00139', ten_banh='CANDLE 12cm', co_the_ban=sl, da_dat=da_dat)]),
             get_single=lambda *a: D(dong=[D(ma_hang='BAWC00139', ten_banh='CANDLE 12cm', so_decor=decor)]))


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


@ca('F21-4 đặt xa ngày không dùng tồn hôm nay; thiếu dòng/phiếu không suy thành0')
def _():
    for ngay, fr in [('2026-10-17T13:00:00', nguon(0)), ('2026-10-13T13:00:00', nguon(0,co=False))]:
        vet, ham, d = gui(2,ngay)
        with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', fr):
            la('giữ nhận', ham(d)['ok'], 1)
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(0)):
        la('mã không trong nguồn', ton.kiem([{'variation_id':'BTPKHAC','quantity':20}], '2026-10-13'), [])


@ca('F21 decor ba ngày tới trừ tổng đã đặt, vẫn thấy dòng đã về0; không cộng nguồn hôm nay')
def _():
    with patch.object(ton, 'hom_nay', lambda: date(2026,10,13)), patch.object(ton, 'frappe', nguon(99,decor=4,da_dat=1)):
        for ng in ('2026-10-14','2026-10-15','2026-10-16'):
            r=ton.kiem([{'variation_id':'BAWC00139','quantity':2}],ng)
            dung('chỉ còn1 cho '+ng, 'còn 1 cái' in r[0])
        la('ngoài ba ngày',ton.kiem([{'variation_id':'BAWC00139','quantity':20}], '2026-10-17'), [])


@ca('F21-5 lỗi đọc tồn vẫn tạo đơn, ghi log và báo Sales')
def _():
    vet, ham, d = gui()
    with patch.object(ton, 'kiem', side_effect=RuntimeError('IO')), patch.object(ton, 'bao_loi') as bao:
        la('nhận', ham(d)['ok'], 1)
        dung('đã yêu cầu cảnh báo', bao.called)
    from vagabond import gui_thu, lib
    fr=D(log_error=lambda *a,**k: vet.su.append('log'), get_traceback=lambda: 'IO')
    with patch.object(ton,'frappe',fr), patch.object(lib,'cfg_o',lambda k: 'https://sales.invalid' if k == 'webhook_don_web' else ''), patch.object(gui_thu,'ban_webhook',lambda cau,**k: vet.su.append(('sales',cau,k['url'])) or True):
        ton.bao_loi('2026-10-13')
    dung('log thật được gọi', 'log' in vet.su)
    dung('đúng kênh đơn web', any(isinstance(x,tuple) and x[0]=='sales' and x[2]=='https://sales.invalid' and '2026-10-13' in x[1] for x in vet.su))


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
    from vagabond import gui_thu, lib
    vet, ham, d = gui()
    fr=D(log_error=lambda *a,**k: vet.su.append('log'), get_traceback=lambda: 'IO')
    with patch.object(ton, 'kiem', side_effect=RuntimeError('IO')), patch.object(ton,'frappe',fr), patch.object(lib,'cfg_o',lambda k: 'https://sales.invalid'), patch.object(gui_thu,'ban_webhook',side_effect=RuntimeError('Lark')):
        la('nhận dù Sales lỗi',ham(d)['ok'],1)
        dung('ghi lỗi đọc và gửi',vet.su.count('log') >= 2)


@ca('F21 lỗi bên trong nguồn mùa vụ cũng báo Sales, giữ nhận')
def _():
    from vagabond import mua_vu
    with patch.object(mua_vu,'mua_dang_chay',lambda ngay: ['MUA']), patch.object(mua_vu,'_doc_mua',side_effect=RuntimeError('IO')):
        da_bao=[]
        la('không chặn',mua_vu.kiem_han_muc([{'item_code':'X','qty':1}], ngay='2026-10-13', khi_loi=lambda:da_bao.append(1)),[])
        la('cảnh báo',da_bao,[1])
