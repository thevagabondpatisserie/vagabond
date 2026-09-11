"""Giữ phạm vi1ML=1Gram và không che lỗi công thức khi đổi nhãn."""
from vagabond.gram_bom_252 import bang_doi, MA_NGUYEN_LIEU
from vagabond.khung.kiem_thu.nen import ca, la, dung


@ca('#252 Gram: đúng14 mã, đổi nhãn không đổi định mức và tiền')
def _pham_vi():
    la('đúng14 mã duy nhất', len(set(MA_NGUYEN_LIEU)), 14)
    for ma in MA_NGUYEN_LIEU:
        dong = dict(item_code=ma, uom='ML', conversion_factor=1, qty=330,
                    stock_qty=330, rate=27, amount=8910)
        cu = dict(dong)
        la('chỉ nhãn', bang_doi(dong, True), {'uom': 'Gram'})
        la('không sửa dữ liệu đầu vào', dong, cu)
        dong['uom'] = 'Gram'
        la('chạy lại sạch', bang_doi(dong, True), {})
    la('không đổi mã khác', bang_doi(dict(item_code='NVLT00325', uom='ML')), {})


@ca('#252 Gram: hai dòng Lescure330 và266 Gram giữ nguyên số')
def _lescure():
    for qty in (330, 266):
        la('Gram đã đúng không đổi', bang_doi(dict(item_code='NVLT00002', uom='Gram',
            conversion_factor=1, qty=qty, stock_qty=qty), True), {})


@ca('#252 Gram: không hợp thức hóa hệ số hoặc lượng kho sai')
def _chan():
    goc = dict(item_code='NVLT00002', uom='ML', conversion_factor=1, qty=330, stock_qty=330)
    for doi in ({'conversion_factor': 1000}, {'conversion_factor': 0},
                {'conversion_factor': float('nan')}, {'conversion_factor': float('inf')},
                {'stock_qty': 330000}, {'stock_qty': None}, {'qty': -330},
                {'qty': float('inf')}, {'uom': 'Lít'}):
        try:
            bang_doi(dict(goc, **doi), True)
        except ValueError:
            continue
        dung('phải chặn ' + str(doi), False)
