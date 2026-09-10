"""#261: mã hàng KMCB từng được lưu như món lẻ nên Kiểm bánh không đếm ruột.

Một cấu hình Vagabond Combo nối đúng một Item; không suy thành phần từ tên.
Rã tại before_validate của SI để Desk/API cũng đi cùng cửa. ERPNext 16.28
SalesInvoice.validate -> set_missing_values/tính thuế chạy SAU before_validate:
chỉ điền mã, lượng và giá, để core tự lấy UOM, thuế, kho của từng món.
"""
# phần thuần
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_DOWN


def so_duong(gia_tri, ten):
    try:
        so = Decimal(str(gia_tri))
        if not so.is_finite() or so <= 0:
            raise ValueError()
        return so
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('%s phải là số lớn hơn 0.' % ten)


def chia_gia(dong, so_bo, gia_bo):
    """Chia giá theo giá lẻ, phân đồng dư theo phần lẻ lớn nhất để không âm."""
    bo = so_duong(so_bo, 'Số bộ')
    if bo != bo.to_integral_value():
        raise ValueError('Số bộ combo phải là số nguyên.')
    gia = so_duong(gia_bo, 'Giá combo')
    if not dong:
        raise ValueError('Combo chưa có món thành phần.')
    trong_so = [so_duong(d.get('so_luong'), 'Số món') * so_duong(d.get('gia_goc'), 'Giá lẻ') for d in dong]
    tong_goc = sum(trong_so)
    tong = (gia * bo).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    chua_tron = [tong * x / tong_goc for x in trong_so]
    phan = [x.quantize(Decimal('1'), rounding=ROUND_DOWN) for x in chua_tron]
    thu_tu = sorted(range(len(dong)), key=lambda i: (-(chua_tron[i]-phan[i]), i))
    for i in thu_tu[:int(tong-sum(phan))]:
        phan[i] += 1
    ra = []
    for i, d in enumerate(dong):
        sl = so_duong(d.get('so_luong'), 'Số món') * bo
        ra.append(dict(item_code=d['item_code'], qty=float(sl), rate=float(phan[i] / sl)))
    return ra


import frappe
from frappe.utils import cint

TRUONG_MOI = {'Sales Invoice Item': [
    dict(fieldname='vgb_combo_ma', label='Mã combo', fieldtype='Data', read_only=1, no_copy=0),
    dict(fieldname='vgb_combo_ten', label='Tên combo', fieldtype='Data', read_only=1, no_copy=0),
]}


def doc_cau_hinh(ma, quay='', nguon=''):
    from vagabond import khuyen_mai as km
    ten = frappe.db.get_value('Vagabond Combo', {'ma_hang': ma}, 'name')
    if not ten:
        frappe.throw('Combo %s chưa khai món thành phần. Mở Khuyến mãi - combo, chọn mã hàng này và khai đủ món trước khi bán.' % ma)
    cb = km._doc_combo(ten)
    if not cint(cb.get('bat')):
        frappe.throw('Combo %s đang tắt. Nhờ quản lý kiểm cấu hình trước khi bán.' % ma)
    for ok, ly_do in (km._hop_thoi_gian(cb), km._hop_kenh(cb, nguon, quay)):
        if not ok:
            frappe.throw('Combo %s: %s.' % (ma, ly_do))
    # Combo có nhóm chọn phải đi qua màn chọn combo và bộ kiểm khuyến mãi.
    if any(d.get('nhom') for d in cb['dong']):
        frappe.throw('Combo %s cần chọn món. Chọn trong nhóm Combo ở màn tính tiền.' % ma)
    if any(str(d.get('item_code', '')).upper().startswith('KMCB') for d in cb['dong']):
        frappe.throw('Combo %s có combo lồng bên trong. Khai trực tiếp từng món để đếm kho đúng.' % ma)
    if cb.get('can_otp') or cb.get('gioi_han_bill') or cb.get('lan_moi_ngay'):
        frappe.throw('Combo %s có giới hạn khuyến mãi. Chọn trong nhóm Combo để kiểm điều kiện.' % ma)
    return cb


def ra_dong(ma, so_bo, quay='', nguon=''):
    from vagabond import khuyen_mai as km
    cb = doc_cau_hinh(ma, quay, nguon)
    goc = sum(float(d['so_luong']) * float(d['gia_goc']) for d in cb['dong'])
    gia = goc - km._tiet_kiem_bo(cb, goc)
    try:
        dong = chia_gia(cb['dong'], so_bo, gia)
    except ValueError as e:
        frappe.throw(str(e))
    for d in dong:
        ten = frappe.db.get_value('Item', d['item_code'], 'item_name') or d['item_code']
        d.update(vgb_combo_ma=ma, vgb_combo_ten=cb['ten'], description='%s\n◈ %s - %s' % (ten, ma, cb['ten']))
    return dong


def truoc_khi_luu(doc, method=None):
    if doc.docstatus == 2:
        return
    if not any(str(d.item_code or '').upper().startswith('KMCB') for d in doc.items):
        return
    if doc.get('custom_hddt_so') or doc.docstatus == 1:
        frappe.throw('Hoá đơn đã phát hành/ghi sổ còn mã combo. Báo kế toán xử lý chứng từ, không tự rã lại.')
    dong = []
    for d in doc.items:
        if not str(d.item_code or '').upper().startswith('KMCB'):
            dong.append(d.as_dict())
            continue
        if doc.get('is_return'):
            frappe.throw('Trả combo: lấy từng món từ hoá đơn gốc, không nhập lại mã combo.')
        for x in ra_dong(d.item_code, d.qty, doc.get('vgb_quay'), doc.get('custom_nguon')):
            # Giữ kho được chọn; tuyệt đối không tạo Stock Entry riêng.
            if d.get('warehouse'):
                x['warehouse'] = d.warehouse
            dong.append(x)
    doc.set('items', [])
    for d in dong:
        doc.append('items', d)
