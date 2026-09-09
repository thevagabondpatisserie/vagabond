"""#257: báo cáo UOM phải phát hiện lệch thật mà không tự đoán quy đổi."""
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.staging.ra_uom import ra


@ca('#257 UOM: quả và pcs chỉ báo lệch khi có quy ước theo món đã duyệt')
def _():
    mon = [dict(item_code='TRUNG-THU', stock_uom='pcs', uoms=[dict(uom='pcs', conversion_factor=1)])]
    la('khong doan tu ten', ra(mon, {})['so_phat_hien'], 0)
    kq = ra(mon, {'TRUNG-THU': 'Quả'})
    la('bao dung lech', kq['phat_hien'][0]['loai'], 'lech_quy_uoc')
    la('khong sua nguon', mon[0]['stock_uom'], 'pcs')


@ca('#257 UOM: bắt hệ số không hữu hạn, bằng 0 và đơn vị gốc khác 1')
def _():
    for he in ['NaN', 'Infinity', 0, -1, None, 'khong phai so']:
        kq = ra([dict(item_code='THU', stock_uom='Gram', uoms=[dict(uom='Gram', conversion_factor=he)])], {})
        dung('he so sai bi bao', any(r['loai'] == 'he_so_khong_hop_le' for r in kq['phat_hien']))
    kq = ra([dict(item_code='THU', stock_uom='Gram', uoms=[dict(uom='Gram', conversion_factor=1000)])], {})
    la('goc bang mot', kq['phat_hien'][0]['loai'], 'he_so_goc_khac_mot')


@ca('#257 UOM: không bỏ sót quy đổi mua bán và bản xuất thiếu món')
def _():
    kq = ra([dict(item_code='THU', stock_uom='Quả', purchase_uom='Thùng', sales_uom='Gói', uoms=[])], {'THIEU': 'Gram'})
    la('du ba phat hien', kq['so_phat_hien'], 3)
    kq = ra([dict(item_code='THU', stock_uom='Quả', purchase_uom='Thùng', uoms=[dict(uom='Thùng', conversion_factor=30)])], {})
    la('he so ro rang dat', kq['so_phat_hien'], 0)
