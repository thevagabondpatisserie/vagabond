"""#261: rã mã hàng thật, bảo toàn giá và không đoán thành phần."""
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch
from types import SimpleNamespace
from vagabond import combo_mon as cb
from vagabond.khung.kiem_thu.nen import ca, la, dung, nem, Doi


@ca('#261 chia combo 3 bánh không mất đồng, nhiều bộ và món trùng')
def _chia():
    ds = [dict(item_code='BAWS1', so_luong=3, gia_goc=50000)]
    for n in (1, 2, 7):
        r = cb.chia_gia(ds, n, 140000)
        la('đúng số bánh', r[0]['qty'], 3*n)
        la('đúng tiền', round(r[0]['qty']*r[0]['rate']), 140000*n)
    le = cb.chia_gia([dict(item_code='BAWS'+str(i),so_luong=1,gia_goc=1) for i in range(6)],1,3)
    la('không sinh giá âm khi chia nhiều dòng',sum(x['rate'] for x in le),3)
    dung('mọi giá không âm', all(x['rate'] >= 0 for x in le))
    ds.append(dict(item_code='BAWS1', so_luong=1, gia_goc=20000))
    r = cb.chia_gia(ds, 2, 100001)
    la('hai dòng cùng món vẫn đủ số lượng', sum(x['qty'] for x in r), 8)
    la('không mất đồng', sum(round(x['qty']*x['rate']) for x in r), 200002)


@ca('#261 chặn số bộ trống, âm, lẻ, không hữu hạn và cấu hình hỏng')
def _so():
    for n in ('', 0, -1, 1.5, 'abc', 'NaN', 'Infinity'):
        try:
            cb.chia_gia([dict(item_code='BAWS1', so_luong=3, gia_goc=50000)], n, 140000)
        except ValueError:
            continue
        dung('phải chặn '+str(n), False)


@ca('#261 máy chủ dùng cấu hình, không đoán từ tên mã KMCB')
def _ra():
    cau = dict(ten='Ba bánh', dong=[dict(item_code='BAWS1', so_luong=3, gia_goc=50000)], kieu='Gia tron goi',gia_combo=140000)
    with patch.object(cb,'doc_cau_hinh',return_value=cau), patch.object(cb.frappe.db,'get_value',return_value='Bánh'):
        r=cb.ra_dong('KMCB00002',2,'NVHTN','GrabFood')
    la('số lượng dùng đếm kho',r[0]['qty'],6)
    dung('có mã và tên', 'KMCB00002 - Ba bánh' in r[0]['description'])


@ca('#261 thành tiền là số chốt, rate làm tròn không còn làm mất đồng')
def _thanh_tien():
    r = cb.chia_gia([dict(item_code='M1',so_luong=3,gia_goc=45000),
        dict(item_code='M2',so_luong=1,gia_goc=60000)],1,155000)
    la('phân đồng dư',[d['vgb_combo_tien'] for d in r],[107308,47692])
    la('đủ tiền',sum(d['vgb_combo_tien'] for d in r),155000)


@ca('#261 xóa thành phần, bỏ dấu combo và bỏ dòng gốc đều bị chặn')
def _nhom():
    cu = [Doi(name='A', item_code='M1', vgb_combo_ma='CB1', vgb_combo_luong=3),
        Doi(name='B', item_code='M2', vgb_combo_ma='CB1', vgb_combo_luong=1)]
    nem('xóa một món', lambda: cb.kiem_nhom(cu, cu[:1]))
    nem('bỏ dấu combo', lambda: cb.kiem_nhom(cu, [dict(cu[0],vgb_combo_luong=0),cu[1]]))
    cb.kiem_nhom(cu, cu)
    cb.kiem_nhom(cu, [])
    si = SimpleNamespace(items=cu)
    nem('bỏ dòng gốc giữ giá', lambda: cb.giu_dong_sua(si, {}, dict(item_code='M1',qty=3,rate=35769)))
    nem('giả dòng gốc', lambda: cb.giu_dong_sua(si, {'dong_goc':'X'}, dict(item_code='M1',qty=3,rate=35769)))
    la('món lẻ mới vẫn thêm', cb.giu_dong_sua(si, {}, dict(item_code='M3',qty=1,rate=10000))['rate'],10000)


@ca('#261 cửa lưu gọi kiểm đủ nhóm từ các dòng đã lưu trong DB')
def _cua_nhom():
    ds=[Doi(name='A',parent='SI1',item_code='M1',qty=3,rate=35769,vgb_combo_ma='CB1',
        vgb_combo_ten='Combo',vgb_combo_luong=3,vgb_combo_tien=107308),
        Doi(name='B',parent='SI1',item_code='M2',qty=1,rate=47692,vgb_combo_ma='CB1',
        vgb_combo_ten='Combo',vgb_combo_luong=1,vgb_combo_tien=47692)]
    doc=SimpleNamespace(name='SI1',items=ds[:1],get=lambda k:None,is_new=lambda:False)
    with patch.object(cb.frappe,'get_all',return_value=ds), \
            patch.object(cb.frappe.db,'get_value',return_value=ds[0]):
        nem('cửa lưu phải chặn mất dòng B',lambda:cb._kiem_tien_da_chia(doc),cb.frappe.ValidationError)


@ca('#261 cửa cấu hình chặn combo tắt, lồng, chọn nhóm và ưu đãi giới hạn')
def _cau_hinh_cam():
    from vagabond import khuyen_mai as km
    goc = dict(bat=1,dong=[dict(item_code='M1',so_luong=3,gia_goc=50000)])
    for doi in ({'bat':0},{'dong':[{'item_code':'KMCB1'}]},
            {'dong':[{'item_code':'M1','nhom':'Chọn bánh'}]},
            {'can_otp':1},{'gioi_han_bill':1},{'lan_moi_ngay':1}):
        with patch.object(cb.frappe.db,'get_value',return_value='CB1'), \
                patch.object(km,'_doc_combo',return_value=dict(goc,**doi)), \
                patch.object(km,'_hop_thoi_gian',return_value=(True,'')), \
                patch.object(km,'_hop_kenh',return_value=(True,'')):
            nem('chặn '+str(doi),lambda:cb.doc_cau_hinh('KMCB1'),cb.frappe.ValidationError)


@ca('#261 trả combo đảo số tiền VND và chiết khấu, không mở dòng âm trên phiếu bán')
def _tra_tien():
    from vagabond.thue_vnd import tinh_dong, tinh_dong_tra
    for giam in (0,5000,165000):
        ban=tinh_dong([10000,107308,47692],[8,8,8],True,giam)
        tra=tinh_dong_tra([-10000,-107308,-47692],[8,8,8],True,-giam)
        la('đảo đúng net/VAT/gross',tra,[dict(d,net=-d['net'],vat=-d['vat'],gross=-d['gross']) for d in ban])
    nem('phiếu bán vẫn cấm âm',lambda:tinh_dong([-1],[8],True),ValueError)
    nem('phiếu trả cấm dòng dương',lambda:tinh_dong_tra([1],[8],True),ValueError)
