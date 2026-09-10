"""#261: rã mã hàng thật, bảo toàn giá và không đoán thành phần."""
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch
from vagabond import combo_mon as cb
from vagabond.khung.kiem_thu.nen import ca, la, dung


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
