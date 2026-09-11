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
        ra.append(dict(item_code=d['item_code'], qty=float(sl), rate=float(phan[i] / sl),
            vgb_combo_tien=float(phan[i]), vgb_combo_luong=float(sl)))
    return ra


import frappe
from frappe.utils import cint

TRUONG_MOI = {'Sales Invoice Item': [
    dict(fieldname='vgb_combo_tien', label='Thành tiền combo', fieldtype='Currency', precision='0', read_only=1, no_copy=0),
    dict(fieldname='vgb_combo_luong', label='Lượng combo đã chia', fieldtype='Float', read_only=1, no_copy=0),
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
    _kiem_tien_da_chia(doc)
    if not any(str(d.item_code or '').upper().startswith('KMCB') for d in doc.items):
        return
    if doc.get('custom_hddt_so') or doc.docstatus == 1:
        frappe.throw('Hoá đơn đã phát hành/ghi sổ còn mã combo. Báo kế toán xử lý chứng từ, không tự rã lại.')
    dong = []
    for d in doc.items:
        if not str(d.item_code or '').upper().startswith('KMCB'):
            dong.append(d)
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


def _kiem_tien_da_chia(doc):
    """Chỉ dùng thành tiền máy chủ đã chia và lưu; không nhận số tự gửi lên.

    Dòng rã cố định giữ nguyên lượng. Đổi số bộ bằng cách chọn lại combo,
    tránh một món bị đổi lượng riêng nhưng còn giữ tiền của cả cấu hình cũ.
    """
    if doc.name:
        cu = frappe.get_all('Sales Invoice Item', filters={'parent': doc.name,
            'vgb_combo_luong': ['!=', 0]}, fields=['name', 'vgb_combo_ma'])
        kiem_nhom(cu, doc.items)
    for d in doc.items:
        if not d.get('vgb_combo_luong'):
            continue
        cu = frappe.db.get_value('Sales Invoice Item', d.name,
            ['parent', 'item_code', 'qty', 'rate', 'vgb_combo_ma', 'vgb_combo_ten', 'vgb_combo_tien', 'vgb_combo_luong'], as_dict=True) if d.name else None
        if not cu or cu.parent != doc.name or cu.item_code != d.item_code or any(
                (d.get(k) or '') != (cu.get(k) or '') for k in ('vgb_combo_ma','vgb_combo_ten')) or any(
                Decimal(str(d.get(k) or 0)) != Decimal(str(cu.get(k) or 0))
                for k in ('qty', 'rate', 'vgb_combo_tien', 'vgb_combo_luong')):
            frappe.throw('Dòng combo đã chia tiền không được sửa riêng lượng/thành tiền. Xóa bộ này rồi chọn lại combo với số bộ cần bán.')


def kiem_nhom(cu, moi):
    """Một mã combo trên bill phải được giữ đủ hoặc xóa hết thành phần."""
    theo_ten = {d.get('name'): d for d in moi if d.get('name')}
    nhom = {}
    for d in cu:
        nhom.setdefault(d.get('vgb_combo_ma'), []).append(d.get('name'))
        if d.get('name') in theo_ten and not theo_ten[d.get('name')].get('vgb_combo_luong'):
            frappe.throw('Không được bỏ dấu combo khỏi món đã chia tiền. Xóa toàn bộ combo rồi chọn lại.')
    for ten in nhom.values():
        con = sum(x in theo_ten for x in ten)
        if con and con != len(ten):
            frappe.throw('Không được xóa riêng món trong combo. Xóa toàn bộ món cùng mã combo rồi chọn lại.')


def dat_thanh_tien(doc):
    """Core tính lại amount từ rate đã làm tròn; phục hồi tiền dòng sau cửa đó.

    ERPNext de591661, taxes_and_totals.calculate_item_values. ThueVnd gọi
    sau super(), trước phân VAT/chiết khấu/GL; rate chỉ phục vụ hiển thị.
    """
    for d in doc.items:
        if d.get('vgb_combo_luong'):
            if Decimal(str(d.qty)) != Decimal(str(d.vgb_combo_luong)):
                frappe.throw('Lượng món combo đã thay đổi. Chọn lại combo để chia tiền đúng.')
            d.amount = d.base_amount = d.net_amount = d.base_net_amount = float(d.vgb_combo_tien)



def giu_dong_sua(si, gui, dong):
    """Màn sửa bill gửi tên dòng; tiền combo lấy từ chứng từ gốc trên máy chủ."""
    cu = next((x for x in si.items if x.name == gui.get('dong_goc')), None)
    if gui.get('dong_goc') and not cu:
        frappe.throw('Dòng bill gốc không còn tồn tại. Tải lại bill rồi sửa tiếp.')
    if not cu and any(x.item_code == dong['item_code'] and x.get('vgb_combo_luong') for x in si.items):
        frappe.throw('Món thuộc combo thiếu dòng gốc. Lưu việc xóa toàn bộ combo trước khi thêm lại món lẻ.')
    if not cu or not cu.get('vgb_combo_luong'):
        return dong
    if cu.item_code != dong['item_code'] or any(
            Decimal(str(cu.get(k))) != Decimal(str(dong[k])) for k in ('qty', 'rate')):
        frappe.throw('Dòng combo đã chia tiền không sửa riêng lượng/giá. Xóa bộ này rồi chọn lại combo.')
    ra = cu.as_dict()
    ra.update(dong)
    # Nhãn combo cũng là nguồn máy chủ, không mất khi màn cũ bỏ trường combo.
    if not gui.get('combo'):
        ra['description'] = cu.description
    return ra
