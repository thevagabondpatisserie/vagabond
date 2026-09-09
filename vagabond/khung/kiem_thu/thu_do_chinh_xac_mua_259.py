"""Chốt precision nguồn nguyên/lẻ, phạm vi riêng MInvoice VND và hai cửa core."""
from decimal import Decimal, ROUND_HALF_UP
from vagabond.do_chinh_xac_mua import quy_uoc, so_le_tien
from vagabond.khung.kiem_thu.nen import ca, la, dung


@ca('#259 precision thuần: tiền nguồn nguyên làm tròn sau nhân, không cắt đơn giá')
def _11595():
    g = dict(tien_truoc_thue=925926, tien_thue=74074, tong_tien=1000000,
        chi_tiet=[dict(thtien=925926, dgia=925.9259, sluong=1000)])
    q = quy_uoc(dict(doctype='Purchase Invoice', currency='VND'), g)
    la('đơn giá9, tiền0, lượng9', q, dict(gia=9, tien=0, sl=9))
    gia = Decimal('925.9259')
    la('bản cũ tái hiện lệch4đ', gia.quantize(Decimal('.01'))*1000 + 74074, Decimal(1000004))
    la('bản mới nhân rồi làm tròn tiền', (gia*1000).quantize(Decimal(1), rounding=ROUND_HALF_UP)+74074, Decimal(1000000))


@ca('#259 precision thuần: giữ tiền nguồn có lẻ, tờ âm và không áp tờ khác')
def _pham_vi():
    la('nguồn lẻ giữ2', so_le_tien(dict(tong_tien='1080.03', chi_tiet=[dict(thtien='1000.0300')])), 2)
    la('âm vẫn nguyên', so_le_tien(dict(tong_tien=-1000000, chi_tiet=[])), 0)
    for doc, g in ((dict(doctype='Purchase Invoice', currency='USD'), {'tong_tien': 1}),
                   (dict(doctype='Sales Invoice', currency='VND'), {'tong_tien': 1}),
                   (dict(doctype='Purchase Invoice', currency='VND'), None)):
        la('ngoài phạm vi', quy_uoc(doc, g), None)
    for v in ('NaN', 'Infinity', 'abc', '0.0000000001'):
        try:
            so_le_tien(dict(tong_tien=v))
        except ValueError:
            continue
        dung('không nhận tiền nguồn sai ' + v, False)
