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
], 'Sales Invoice': [dict(fieldname='vgb_combo_hoan_tien',label='Tiền hoàn bill có combo',
    fieldtype='Currency',precision='0',read_only=1,no_copy=1)]}


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
    if doc.get('is_return'):
        chuan_bi_tra(doc)
    elif doc.is_new() and not doc.get('amended_from'):
        try:
            _sao_chep(doc)
        except ValueError as e:
            frappe.throw(str(e))
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
        x = doc.append('items', d)
        x.idx = len(doc.items)


def _kiem_tien_da_chia(doc):
    """Chỉ dùng thành tiền máy chủ đã chia và lưu; không nhận số tự gửi lên.

    Dòng rã cố định giữ nguyên lượng. Đổi số bộ bằng cách chọn lại combo,
    tránh một món bị đổi lượng riêng nhưng còn giữ tiền của cả cấu hình cũ.
    """
    if doc.get('is_return'):
        return  # chuan_bi_tra lấy tiền từ sales_invoice_item của phiếu gốc.
    if doc.is_new() and doc.get('amended_from'):
        _kiem_sua_doi(doc)
        return
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


def _sao_chep(doc):
    """Duplicate là lần bán mới: kiểm đủ bộ và tính lại bằng cấu hình hiện tại."""
    nhom = {}
    for d in doc.items:
        if d.get('vgb_combo_luong') or d.get('vgb_combo_ma'):
            nhom.setdefault(d.get('vgb_combo_ma'), []).append(d)
    if not nhom:
        return
    cac_bo = {}
    for ma, ds in nhom.items():
        if not str(ma or '').upper().startswith('KMCB'):
            frappe.throw('Bản sao thiếu mã combo gốc. Xóa nhóm món và chọn lại mã bộ.')
        if len({d.get('warehouse') for d in ds}) > 1:
            frappe.throw('Combo trong bản sao đang lấy nhiều kho. Chọn lại mã bộ và kho trước khi lưu.')
        cau = doc_cau_hinh(ma,doc.get('vgb_quay'),doc.get('custom_nguon'))
        goc, moi = {}, {}
        for d in cau['dong']:
            goc[d['item_code']] = goc.get(d['item_code'],Decimal(0)) + so_duong(d['so_luong'],'Lượng cấu hình')
        for d in ds:
            moi[d.item_code] = moi.get(d.item_code,Decimal(0)) + so_duong(d.qty,'Lượng món')
        ti_le = {moi[k]/goc[k] for k in moi if k in goc}
        if set(moi) != set(goc) or len(ti_le) != 1:
            frappe.throw('Bản sao thiếu thành phần combo. Xóa toàn bộ combo và chọn lại mã bộ.')
        bo = ti_le.pop()
        if bo != bo.to_integral_value():
            frappe.throw('Bản sao không đủ số bộ combo. Chọn lại mã bộ.')
        cac_bo[ma] = dict(item_code=ma,qty=float(bo),rate=0,warehouse=ds[0].get('warehouse'))
    dong = []
    for d in doc.items:
        if d.get('vgb_combo_luong') or d.get('vgb_combo_ma'):
            if d.get('vgb_combo_ma') in cac_bo:
                dong.append(cac_bo.pop(d.get('vgb_combo_ma')))
        else:
            dong.append(d)
    doc.set('items',[])
    for d in dong:
        x = doc.append('items',d)
        x.idx = len(doc.items)


def _kiem_sua_doi(doc):
    cu = frappe.get_doc('Sales Invoice',doc.amended_from)
    if cu.docstatus != 2 or cu.company != doc.company or cu.currency != doc.currency:
        frappe.throw('Chứng từ sửa đổi combo phải nối đúng hóa đơn gốc đã hủy.')
    con = list(cu.items)
    giu = []
    truong = ('item_code','qty','rate','vgb_combo_ma','vgb_combo_ten','vgb_combo_tien','vgb_combo_luong')
    for d in doc.items:
        if not d.get('vgb_combo_luong'):
            continue
        goc = next((x for x in con if all(x.get(k)==d.get(k) for k in truong)),None)
        if not goc:
            frappe.throw('Dòng combo sửa đổi không khớp hóa đơn gốc. Xóa toàn bộ combo rồi chọn lại.')
        con.remove(goc)
        giu.append(goc)
    kiem_nhom([x for x in cu.items if x.get('vgb_combo_luong')],giu)


def chuan_bi_tra(doc):
    """ERPNext de591661 mapper nối sales_invoice_item nhưng validate_returned_items
    vẫn cho bỏ trống link và dò item_code. Combo phải yêu cầu link nguồn rõ ràng.
    Tiền trả theo lượng giữ đồng dư; bồi hoàn tiền dùng số tiền đã duyệt riêng.
    """
    if doc.get('amended_from'):
        cu = frappe.db.get_value('Sales Invoice',doc.amended_from,
            ['docstatus','company','currency','return_against','vgb_combo_hoan_tien'],
            as_dict=True,for_update=True)
        if cu and not cu.vgb_combo_hoan_tien and doc.get('vgb_combo_hoan_tien'):
            frappe.throw('Phiếu gốc trả theo lượng, sửa đổi không được đổi sang bồi hoàn theo tiền.')
        if cu and cu.vgb_combo_hoan_tien:
            if (cu.docstatus != 2 or cu.company != doc.company or cu.currency != doc.currency
                    or cu.return_against != doc.get('return_against')):
                frappe.throw('Sửa đổi phiếu hoàn phải giữ đúng bill gốc của phiếu đã hủy.')
            if doc.get('vgb_combo_hoan_tien') and Decimal(str(doc.vgb_combo_hoan_tien)) != Decimal(str(cu.vgb_combo_hoan_tien)):
                frappe.throw('Sửa đổi phiếu hoàn phải giữ số tiền đã duyệt; đổi tiền cần lập yêu cầu mới.')
            # Desk Amend giữ no_copy; API thiếu trường vẫn lấy tiền từ nguồn đã hủy.
            doc.vgb_combo_hoan_tien = cu.vgb_combo_hoan_tien
    if not doc.get('return_against'):
        if any(d.get('vgb_combo_luong') for d in doc.items):
            frappe.throw('Trả combo phải chọn hóa đơn gốc.')
        return
    goc = frappe.db.get_value('Sales Invoice',doc.return_against,
        ['name','company','currency','docstatus'],as_dict=True,for_update=True)
    ds = frappe.get_all('Sales Invoice Item',filters={'parent':doc.return_against},
        fields=['name','item_code','qty','vgb_combo_ma','vgb_combo_ten','vgb_combo_tien','vgb_combo_luong'])
    theo_ten = {d.name:d for d in ds}
    ma_combo = {d.item_code for d in ds if d.vgb_combo_luong}
    if not doc.is_new():
        cu_tien = frappe.db.get_value('Sales Invoice',doc.name,'vgb_combo_hoan_tien')
        if cu_tien and Decimal(str(doc.get('vgb_combo_hoan_tien') or 0)) != Decimal(str(cu_tien)):
            frappe.throw('Không đổi hoặc bỏ số tiền hoàn đã lưu để chuyển sang hoàn theo lượng.')
    if doc.get('vgb_combo_hoan_tien'):
        return _hoan_theo_tien(doc,goc,theo_ten)
    da_dung = set()
    for d in doc.items:
        cu = theo_ten.get(d.get('sales_invoice_item'))
        if not cu and d.item_code in ma_combo:
            frappe.throw('Trả món combo phải chọn đúng dòng từ hóa đơn gốc, không nhập món rời.')
        if not cu or not cu.vgb_combo_luong:
            if d.get('vgb_combo_luong'):
                frappe.throw('Dòng trả combo không nối đúng món trên hóa đơn gốc.')
            continue
        if (not goc or goc.docstatus != 1 or goc.company != doc.company or goc.currency != doc.currency
                or cu.item_code != d.item_code or cu.name in da_dung):
            frappe.throw('Dòng trả combo không nối đúng hóa đơn gốc hoặc bị gửi trùng.')
        da_dung.add(cu.name)
        luong = -Decimal(str(d.qty))
        truoc = frappe.db.sql('''select coalesce(sum(-d.qty),0), coalesce(sum(-d.vgb_combo_tien),0)
            from `tabSales Invoice Item` d join `tabSales Invoice` h on h.name=d.parent
            where h.docstatus=1 and h.is_return=1 and h.return_against=%s
            and d.sales_invoice_item=%s and h.name!=%s for update''',(doc.return_against,cu.name,doc.name or ''))[0]
        da_tra, tien_tra = (Decimal(str(x)) for x in truoc)
        if luong <= 0 or da_tra+luong > Decimal(str(cu.qty)):
            frappe.throw('Lượng trả combo phải dương và không vượt lượng còn được trả.')
        tien = (Decimal(str(cu.vgb_combo_tien))*(da_tra+luong)/Decimal(str(cu.qty))).quantize(Decimal('1'),rounding=ROUND_HALF_UP)-tien_tra
        d.vgb_combo_luong = float(-luong)
        d.vgb_combo_tien = float(-tien)
        d.vgb_combo_ma, d.vgb_combo_ten = cu.vgb_combo_ma, cu.vgb_combo_ten


def _hoan_theo_tien(doc,goc,theo_ten):
    """Bồi hoàn theo tiền khác trả theo lượng: chia gross sau giảm giá của SI."""
    from vagabond.thue_vnd import doc_dong, phan_bo
    if (not goc or goc.docstatus != 1 or goc.company != doc.company or goc.currency != doc.currency
            or not any(d.vgb_combo_luong for d in theo_ten.values())):
        frappe.throw('Hoàn tiền combo phải nối đúng hóa đơn bán đã ghi sổ.')
    nguon = frappe.get_doc('Sales Invoice',goc.name)
    tien = Decimal(str(doc.vgb_combo_hoan_tien))
    if not tien.is_finite() or tien <= 0 or tien != tien.to_integral_value() or tien > Decimal(str(nguon.grand_total)):
        frappe.throw('Tiền hoàn combo phải là số nguyên đồng, lớn hơn0 và không vượt tiền bill gốc.')
    if not doc.is_new():
        da_luu = frappe.db.get_value('Sales Invoice',doc.name,'vgb_combo_hoan_tien')
        if tien != Decimal(str(da_luu or 0)):
            frappe.throw('Tiền hoàn combo đã lưu không được đổi. Kế toán xử lý phiếu cũ rồi lập lại yêu cầu đúng.')
    if (not nguon.get('vgb_thue_vnd') or len(nguon.taxes)!=1
            or not nguon.taxes[0].included_in_print_rate):
        frappe.throw('Hoàn tiền combo cần bill VND có giá đã gồm VAT. Kế toán kiểm bill gốc trước khi hoàn.')
    if frappe.db.get_value('Sales Invoice',{'return_against':goc.name,'is_return':1,'docstatus':1,
            'name':['!=',doc.name or '']},'name',for_update=True):
        frappe.throw('Bill đã có phiếu trả. Kế toán đối chiếu phiếu cũ trước khi bồi hoàn thêm.')
    lien_ket = [d.get('sales_invoice_item') for d in doc.items]
    if len(lien_ket)!=len(theo_ten) or set(lien_ket)!=set(theo_ten):
        frappe.throw('Bồi hoàn theo tiền phải giữ đủ dòng hóa đơn gốc; trả riêng món thì dùng phiếu trả theo lượng.')
    try:
        gross = {d.name:x['gross'] for d,x in zip(nguon.items,doc_dong(nguon))}
        chia = phan_bo([gross[k] for k in lien_ket],int(tien))
    except ValueError as e:
        frappe.throw(str(e))
    for d,so in zip(doc.items,chia):
        cu = theo_ten[d.sales_invoice_item]
        if d.item_code != cu.item_code or Decimal(str(d.qty)) != -Decimal(str(cu.qty)):
            frappe.throw('Bồi hoàn theo tiền giữ nguyên lượng trên hóa đơn gốc, không đồng thời trả riêng món.')
        d.vgb_combo_luong = float(d.qty)
        d.vgb_combo_tien = -so
        d.vgb_combo_ma, d.vgb_combo_ten = cu.vgb_combo_ma,cu.vgb_combo_ten
        d.rate = d.price_list_rate = float(Decimal(so)/Decimal(str(cu.qty)))
        d.discount_amount = d.discount_percentage = 0
    # Giá mỗi dòng đã là tiền hoàn sau giảm giá; không trừ chiết khấu lần hai.
    doc.apply_discount_on = 'Grand Total'
    doc.discount_amount = doc.additional_discount_percentage = 0


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
        gia_le = frappe.db.get_value('Item',dong['item_code'],'standard_rate')
        if not gia_le or Decimal(str(dong['rate'])) != Decimal(str(gia_le)):
            frappe.throw('Món thuộc combo thiếu dòng gốc. Món lẻ thêm mới phải dùng giá bán trong danh mục.')
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
