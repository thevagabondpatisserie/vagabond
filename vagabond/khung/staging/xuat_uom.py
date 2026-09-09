"""Xuất snapshot UOM chỉ đọc bằng CLI trên site đã được phép đọc.

Không whitelisted, không migrate, không đổi quy đổi hoặc tự duyệt đơn vị.
Tệp chỉ chứa mã món, đơn vị và hệ số, không chứa đối tác/chứng từ/khoá API.
"""
import json
from pathlib import Path


def doc(get_all, bat_dau):
    mon, moc, da_gap = [], '', set()
    while True:
        ds = get_all('Item', filters={'name': ['>', moc]},
            fields=['name', 'item_code', 'stock_uom', 'purchase_uom', 'sales_uom'],
            order_by='name asc', limit_page_length=500)
        if not ds:
            break
        ten = [d['name'] for d in ds]
        # Thứ tự tên theo collation DB, không so tiếng Việt bằng thứ tự Python.
        if len(set(ten)) != len(ten) or da_gap.intersection(ten):
            raise RuntimeError('Trang xuất Item lặp lại mã đã đọc.')
        da_gap.update(ten)
        doi = get_all('UOM Conversion Detail', filters={'parent': ['in', ten],
            'parenttype': 'Item', 'parentfield': 'uoms'},
            fields=['parent', 'uom', 'conversion_factor'], limit_page_length=0)
        bang = {t: [] for t in ten}
        for d in doi:
            if d['parent'] not in bang:
                raise RuntimeError('Quy đổi không thuộc trang Item đang xuất.')
            bang[d['parent']].append({'uom': d['uom'], 'conversion_factor': d['conversion_factor']})
        for d in ds:
            mon.append({k: d.get(k) for k in ('item_code', 'stock_uom', 'purchase_uom', 'sales_uom')})
            mon[-1]['uoms'] = bang[d['name']]
        moc = ten[-1]
    # Core có thể ghi đè hệ số Item từ cả cạnh chung hoặc đường trung gian.
    # Giữ toàn bộ bảng để người rà không bỏ sót cạnh ngoài đơn vị đang mua.
    chung = get_all('UOM Conversion Factor', fields=['name', 'from_uom', 'to_uom', 'value'],
        filters={}, order_by='name asc', limit_page_length=0)
    if len({d['name'] for d in chung}) != len(chung):
        raise RuntimeError('Bản xuất lặp dòng quy đổi chung.')
    if get_all('UOM Conversion Factor', filters={'modified': ['>=', bat_dau]},
            fields=['name'], limit_page_length=1):
        raise RuntimeError('Quy đổi chung thay đổi trong lúc xuất; lấy lại snapshot.')
    # Từ chối thay đổi nhìn thấy được trong transaction hiện tại. Cơ chế
    # snapshot còn phụ thuộc isolation của DB; không khẳng định bắt mọi
    # giao dịch đồng thời hoặc raw SQL bỏ modified.
    doi = get_all('Item', filters={'modified': ['>=', bat_dau]},
        fields=['name'], limit_page_length=1)
    if doi:
        raise RuntimeError('Có Item thay đổi trong lúc xuất; lấy lại snapshot khi danh mục ổn định.')
    return {'uom_conversion_factors': chung, 'items': mon, 'quy_uoc_da_duyet': {}, 'chi_doc': True,
            'bat_dau': str(bat_dau), 'so_mon': len(mon)}


def xuat(tep):
    import frappe
    from frappe.utils import now_datetime
    if frappe.session.user != 'Administrator' and 'System Manager' not in frappe.get_roles():
        raise PermissionError('Chỉ quản trị xuất danh mục UOM bằng công cụ này.')
    kq = doc(frappe.get_all, now_datetime())
    # Không ghi đè bằng chứng cũ; người gọi chọn tên tệp mới cho mỗi snapshot.
    with Path(tep).open('x', encoding='utf-8') as f:
        json.dump(kq, f, ensure_ascii=False, indent=2, default=str)
    return {'so_mon': len(kq['items']), 'chi_doc': True}
