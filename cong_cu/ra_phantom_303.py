"""#303: đọc cấu hình Mass trước khi sửa, tránh đổi nhầm Powder hoặc BOM cũ.

Nạp tệp trong bench console của quản trị, gọi doc(frappe, [ma_da_xac_nhan]).
Không cài endpoint, không ghi DB, không chọn công thức mặc định thay người dùng.
Kết quả có công thức nội bộ: giữ ở máy, không dán nguyên văn lên repo công khai.
"""


def doc(nguon, cac_ma):
    """Đọc đủ bản công thức và tồn của mã đã chọn; không suy mã từ tên gần giống.

    Mã phải đúng chữ hoa/thường như trên Item; không tự chuẩn hoá mã."""
    if not isinstance(cac_ma, (list, tuple)) or not cac_ma or any(
        not isinstance(ma, str) or not ma.strip() for ma in cac_ma
    ):
        raise ValueError('Cần danh sách mã hàng cụ thể đã xác nhận.')
    cac_ma = sorted(set(ma.strip() for ma in cac_ma))
    mon = nguon.get_all('Item', filters={'name': ['in', cac_ma]},
        fields=['name', 'item_name', 'disabled', 'is_stock_item', 'stock_uom',
                'has_batch_no', 'has_serial_no', 'custom_chang_btp', 'default_bom'], limit_page_length=0)
    thieu = sorted(set(cac_ma) - {d['name'] for d in mon})
    if thieu:
        raise ValueError('Không tìm thấy mã: ' + ', '.join(thieu))
    bom = nguon.get_all('BOM', filters={'item': ['in', cac_ma]},
        fields=['name', 'item', 'docstatus', 'is_active', 'is_default',
                'quantity', 'uom', 'is_phantom_bom', 'custom_chang'], limit_page_length=0)
    ten_bom = [d['name'] for d in bom]
    truong_dong = ['name', 'parent', 'idx', 'item_code', 'qty', 'uom',
                  'stock_qty', 'conversion_factor', 'bom_no', 'do_not_explode',
                  'is_phantom_item']
    thanh_phan = nguon.get_all('BOM Item', filters={'parent': ['in', ten_bom],
        'parenttype': 'BOM'}, fields=truong_dong, limit_page_length=0) if ten_bom else []
    dong_cha = nguon.get_all('BOM Item', filters={'item_code': ['in', cac_ma],
        'parenttype': 'BOM'}, fields=truong_dong, limit_page_length=0)
    la_con = nguon.get_all('BOM Explosion Item', filters={'item_code': ['in', cac_ma],
        'parenttype': 'BOM'}, fields=['parent', 'item_code', 'stock_qty'], limit_page_length=0)
    ten_cha = sorted({d['parent'] for d in dong_cha + la_con})
    cha = nguon.get_all('BOM', filters={'name': ['in', ten_cha]},
        fields=['name', 'item', 'docstatus', 'is_active', 'is_default',
                'quantity', 'uom', 'custom_chang'], limit_page_length=0) if ten_cha else []
    for d in bom + cha:
        d['dang_chay'] = d.get('docstatus') == 1 and d.get('is_active') == 1
    theo_ten = {d['name']: d for d in cha}
    for d in dong_cha + la_con:
        b = theo_ten.get(d['parent'], {})
        d['bom_docstatus'] = b.get('docstatus')
        d['bom_is_active'] = b.get('is_active')
        d['dang_chay'] = b.get('dang_chay', False)
    ton = nguon.get_all('Bin', filters={'item_code': ['in', cac_ma], 'actual_qty': ['!=', 0]},
        fields=['item_code', 'warehouse', 'actual_qty', 'stock_uom'], limit_page_length=0)
    return {'chi_doc': True, 'mon': mon, 'bom': bom, 'thanh_phan': thanh_phan,
            'bom_cha': cha, 'dong_cha': dong_cha, 'la_con_trong_bang_no': la_con,
            'ton_khac_khong': ton,
            'luu_y': 'BOM cũ/ngừng hoạt động được giữ để đối chiếu, không phải đề nghị sửa. '
                      'Không có tồn không chứng minh backflush đúng; phải kiểm Work Order/SLE.'}
