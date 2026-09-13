"""#243: giữ chuyển loại, marker lịch sử và chặn xuất tay tại máy chủ."""
from types import SimpleNamespace
from unittest.mock import patch
from vagabond import hang_tang_kho as kho, diem_ban, hang_tang_so_cai
from vagabond.khung.kiem_thu.nen import ca, la, dung


class To(dict):
    __getattr__=dict.get
    __setattr__=dict.__setitem__
    def is_new(self): return bool(self.get('moi'))


def _hd(**them):
    d=To(doctype='Sales Invoice',name='HD',docstatus=0,moi=1,company='CT',vgb_pt_thanh_toan='Hàng tặng',
        meta=SimpleNamespace(has_field=lambda x:True))
    d.update(them)
    object.__setattr__(d,'items',[To(item_code='BANH',idx=1,qty=1,stock_qty=1,warehouse='KHO-NVL')])
    return d


def _f(cu=0):
    def nem(s): raise ValueError(s)
    def gt(dt,ten,o):
        if dt=='Item': return 1 if o=='is_stock_item' else 0
        if dt=='Account': return '64181' if ten=='64181' else '632'
        return 'CC'
    return SimpleNamespace(throw=nem,get_cached_value=gt,
        db=SimpleNamespace(get_single_value=lambda *a:1,exists=lambda *a:False,get_value=lambda *a,**k:To(docstatus=0,vgb_tang_kho_moi=cu)))


def _chuan(d,cu=0):
    with patch.object(kho,'frappe',_f(cu)), patch.object(kho,'kiem_kho'), \
         patch.object(diem_ban,'ma_theo_quay',return_value='SALES'), \
         patch.object(diem_ban,'theo_ma',return_value={'kho_tang':'KHO-TP'}), \
         patch.object(hang_tang_so_cai,'tai_khoan',return_value='64181'):
        kho.chuan_bi(d)


@ca('#243 kho: SI mới dùng kho điểm bán và 64181, không kho mặc định nguyên liệu')
def _moi():
    d=_hd();_chuan(d)
    la('marker mới',d.vgb_tang_kho_moi,1)
    la('xuất kho',d.update_stock,1)
    la('đúng kho',d.items[0].warehouse,'KHO-TP')
    la('đúng giá vốn tặng',d.items[0].expense_account,'64181')


@ca('#243 kho: không nhận marker giả trên SI nháp cũ')
def _cu():
    d=_hd(moi=0,vgb_tang_kho_moi=1,update_stock=0);_chuan(d,0)
    la('dùng dấu DB',d.vgb_tang_kho_moi,0)
    la('không tự xuất phiếu cũ',d.update_stock,0)


@ca('#243 kho: đổi tặng sang bán thường gỡ cờ kho và tài khoản tặng')
def _doi():
    d=_hd();_chuan(d)
    d.moi=0;d.vgb_pt_thanh_toan='Tiền mặt';_chuan(d,1)
    la('không xuất thêm',d.update_stock,0)
    la('gỡ 64181',d.items[0].expense_account,None)
    la('gỡ dấu kho',d.vgb_tang_kho,None)
    d.vgb_pt_thanh_toan='Hàng tặng';_chuan(d,1)
    la('đổi lại kiểm kho lại',d.update_stock,1)


@ca('#243 kho: đã chọn lô không được tự chuyển sang kho khác')
def _lo():
    d=_hd();d.items[0].batch_no='LO'
    try: _chuan(d)
    except ValueError as e: dung('chỉ rõ chọn lại lô','chọn lại lô' in str(e))
    else: dung('phải chặn',False)


@ca('#243 kho: phiếu xuất 64181 thiếu nguồn hoặc nguồn SI tự xuất đều chặn')
def _trung():
    for ten in (None,'HD'):
        d=_hd(vgb_hoa_don_tang=ten)
        d.items[0].expense_account='64181';d.items[0].s_warehouse='KHO-TP'
        f=_f();f.get_doc=lambda *a:To(company='CT',vgb_tang_kho_moi=1)
        with patch.object(kho,'frappe',f):
            try: kho.chan_xuat_tay(d)
            except ValueError: pass
            else: dung('phải chặn '+str(ten),False)


@ca('#243 kho: bán hay tặng dùng tài khoản tồn kho thực tế, không ép tiền tố 155')
def _tk_kho():
    for so,dat in [('152',True),('1551',True),('155',True),('156',True)]:
        f=_f()
        f.get_cached_doc=lambda dt,ten: (To(company='CT',is_group=0,disabled=0,account='TK') if dt=='Warehouse'
            else To(company='CT',is_group=0,disabled=0,root_type='Asset',account_type='Stock',account_currency='VND',account_number=so))
        with patch.object(kho,'frappe',f):
            try: kho.kiem_kho('KHO','CT')
            except ValueError: la('chặn đúng tài khoản '+so,dat,False)
            else: la('chấp nhận đúng tài khoản '+so,dat,True)
