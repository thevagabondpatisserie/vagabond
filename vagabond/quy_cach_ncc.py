"""Quy cách NCC đã đối chiếu: chọn UOM của Item, không ghi hệ số riêng.

Một tên NCC có thể là Chai 1L trong khi UOM Chai mặc định nay là 500ml.
Lựa chọn theo đúng MST và tên dòng gốc tránh sửa quy cách lịch sử hoặc
đoán từ chuỗi tên. Chỉ người quản lý ánh xạ khai lựa chọn này.
"""
import math
import frappe

LOAI = 'MInvoice NCC Map'
TRUONG = 'vgb_uom'


def dung():
    if not frappe.db.exists('DocType', LOAI):
        return
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields({LOAI: [dict(fieldname=TRUONG, fieldtype='Link', options='UOM',
        label='Đơn vị đã đối chiếu', insert_after='item_code',
        description='Chọn đúng quy cách nhà cung cấp ghi. Hệ số lấy từ bảng quy đổi của Món.') ]}, update=True)


def _kiem_uom(item_code, uom):
    mon = frappe.db.get_value('Item', item_code, ['stock_uom', 'disabled'], as_dict=True)
    if not mon or mon.disabled:
        frappe.throw('Ánh xạ quy cách cần Món có thật và còn dùng. Kiểm lại mã Món đã chọn.')
    if not frappe.db.exists('UOM', uom):
        frappe.throw('Đơn vị đã đối chiếu %s không tồn tại. Chọn lại đơn vị của Món %s.' % (uom, item_code))
    if uom == mon.stock_uom:
        return
    ds = frappe.get_all('UOM Conversion Detail', filters={
        'parent': item_code, 'parenttype': 'Item', 'uom': uom}, fields=['conversion_factor'])
    if len(ds) != 1:
        # v523 (Uyên, Kahlua 23/09/2026): đổi Món của ánh xạ sang mã khác mà
        # đơn vị cũ không có trên mã mới thì câu cũ chỉ nói "chưa khai", người
        # đọc không biết phải đổi luôn ô đơn vị. Nói rõ và bày đơn vị đang có.
        co = [stock_uom for stock_uom in [mon.stock_uom] if stock_uom] + [
            r.uom for r in frappe.get_all('UOM Conversion Detail', filters={
                'parent': item_code, 'parenttype': 'Item'}, fields=['uom'])
            if r.uom and r.uom != mon.stock_uom]
        frappe.throw('Món %s không có đơn vị "%s" (đơn vị này có thể thuộc món cũ của ánh xạ). '
                     'Chọn lại ô Đơn vị đã đối chiếu bằng một trong các đơn vị của món này: %s.'
                     % (item_code, uom, ', '.join(co) or '(chưa khai đơn vị nào)'))
    try:
        hs = float(ds[0].conversion_factor)
    except (TypeError, ValueError, OverflowError):
        hs = 0
    if not math.isfinite(hs) or hs <= 0:
        frappe.throw('Món %s có hệ số không hợp lệ cho đơn vị %s. Hệ số phải hữu hạn và lớn hơn 0.' % (item_code, uom))


def _vua_chon_mon(doc):
    """Ánh xạ mới, hoặc vừa đổi ô Món. Ánh xạ cũ trỏ món ĐÃ tắt từ trước mà
    được lưu lại vì ô khác (máy học đổi món sẽ đổi luôn ô này) thì không
    chặn ở đây: v523 đã cho mọi lối đọc bỏ qua nó."""
    moi = getattr(doc, 'is_new', None)
    if callable(moi) and moi():
        return True
    doi = getattr(doc, 'has_value_changed', None)
    return bool(callable(doi) and doi('item_code'))


def kiem(doc, method=None):
    doc.supplier_mst = (doc.get('supplier_mst') or '').strip().split('-')[0]
    ma = (doc.get('item_code') or '').strip()
    # v524 (anh Việt 24/09/2026): trước đây chỉ chặn món tắt khi ô Đơn vị đã
    # đối chiếu có điền, để trống ô đó là lưu được ánh xạ trỏ món đã tắt.
    if ma and _vua_chon_mon(doc) and _mon_tat(ma):
        frappe.throw('Món %s đã tắt (ngừng dùng), không ánh xạ vào được. '
                     'Chọn mã đang dùng thay cho món này.' % ma)
    uom = (doc.get(TRUONG) or '').strip()
    if not uom:
        return
    if not doc.get('item_code'):
        frappe.throw('Chọn Món trước khi chọn Đơn vị đã đối chiếu của nhà cung cấp.')
    if not (doc.get('supplier_mst') or '').strip() or not (doc.get('ten_ncc') or '').strip():
        frappe.throw('Ánh xạ quy cách cần MST nhà cung cấp và tên hàng nguyên văn trên hoá đơn.')
    _kiem_uom(doc.item_code, uom)


def _anh_xa(mst, truong, gia_tri):
    mst = (mst or '').strip().split('-')[0]
    gia_tri = (gia_tri or '').strip()
    if not mst or not gia_tri:
        return []
    fields = ['name', 'supplier_mst', truong, 'item_code']
    if frappe.get_meta(LOAI).has_field(TRUONG):
        fields.append(TRUONG)
    ds = frappe.get_all(LOAI, filters={truong: gia_tri},
        or_filters=[['supplier_mst', '=', mst], ['supplier_mst', 'like', mst+'-%']],
        fields=fields, limit_page_length=0)
    return [d for d in ds if (d.supplier_mst or '').strip().split('-')[0] == mst
            and (d.get(truong) or '').strip() == gia_tri]


def _mon_tat(item_code):
    return bool(item_code and frappe.db.get_value('Item', item_code, 'disabled'))


def cau_chan_tat(ma, ds, toi_da=5):
    """Câu chặn tắt món còn ánh xạ. Phần thuần, kiểm không cần site."""
    dong = []
    for d in (ds or [])[:toi_da]:
        dong.append('- %s (MST %s)' % ((d.get('ten_ncc') or d.get('ma_ncc') or d.get('name') or '').strip(),
                                        (d.get('supplier_mst') or '').strip() or '?'))
    con = len(ds or []) - len(dong)
    if con > 0:
        dong.append('- và %d ánh xạ khác' % con)
    return ('Chưa tắt được món %s: còn %d ánh xạ hoá đơn mua đang trỏ vào món này, '
            'tắt thì các hoá đơn sau của nhà cung cấp sẽ không gợi ý được món.<br>%s<br>'
            'Mở Ánh xạ mặt hàng NCC (MInvoice NCC Map), đổi Món của từng dòng trên sang mã thay thế '
            '(đổi luôn ô Đơn vị đã đối chiếu), hoặc xoá dòng nếu nhà cung cấp không còn bán món đó, '
            'rồi tắt lại.' % (ma, len(ds or []), '<br>'.join(dong)))


def chan_tat_mon(doc, method=None):
    """Hook validate Item (v524): không cho tắt món còn ánh xạ trỏ vào.

    Ca thật Kahlua: ánh xạ lập 07/09 khi NVLT00325 còn dùng, 15/09 món bị tắt
    mà không ai biết còn ánh xạ, từ đó hoá đơn Con Rồng kẹt. Chặn ở lúc TẮT
    là chặn đúng chỗ sinh ra ánh xạ chết."""
    if not doc.get('disabled'):
        return
    moi = getattr(doc, 'is_new', None)
    if callable(moi) and moi():
        return
    if not doc.has_value_changed('disabled'):
        return
    if not frappe.db.exists('DocType', LOAI):
        return
    ds = frappe.get_all(LOAI, filters={'item_code': doc.name},
                        fields=['name', 'supplier_mst', 'ten_ncc', 'ma_ncc'], limit_page_length=0)
    if ds:
        frappe.throw(cau_chan_tat(doc.name, ds), title='Món còn ánh xạ hoá đơn mua')


def tim_mon(mst, ma_ncc, ten_ncc):
    """Tra mã và quy cách cùng đọc được ánh xạ chi nhánh lịch sử.

    Ánh xạ trỏ vào Món ĐÃ TẮT không còn là gợi ý (v523, Kahlua NVLT00325):
    món tắt thì không ai được nhập vào nữa, gợi ý nó là đẩy người dùng vào
    đúng chỗ bị chặn."""
    for truong, gia_tri in [('ma_ncc', ma_ncc), ('ten_ncc', (ten_ncc or '')[:140])]:
        ds = _anh_xa(mst, truong, gia_tri)
        cac = {d.item_code for d in ds if d.item_code and not _mon_tat(d.item_code)}
        if len(cac) > 1:
            frappe.throw('Ánh xạ NCC %s, hàng %s đang chọn nhiều Món. Đối chiếu lại ánh xạ trước khi tạo hoá đơn.'
                         % (mst, gia_tri))
        if cac:
            return cac.pop()
    return None


def lay(item_code, mst, ten_ncc):
    """Chỉ dùng đúng bộ MST + tên NCC; không suy từ tên gần giống."""
    # Cùng khoá MST gốc mà hoc_ma_hang và _mst_cua_to lưu cho chi nhánh.
    mst, ten = (mst or '').strip().split('-')[0], (ten_ncc or '').strip()[:140]
    if not item_code or not mst or not ten:
        return None
    if not frappe.db.exists('DocType', LOAI) or not frappe.get_meta(LOAI).has_field(TRUONG):
        return None
    # Đọc cả ánh xạ chi nhánh đã lưu trước guard; không âm thầm bỏ lựa
    # chọn cũ hoặc ghi đè khi có nhiều ánh xạ cùng MST gốc.
    ds = _anh_xa(mst, 'ten_ncc', ten)
    # Collation MariaDB có thể coi khác dấu/hoa thường là giống nhau.
    # Quy cách chỉ áp dụng đúng tên NCC đã đối chiếu, không gần giống.
    # Bỏ ánh xạ trỏ Món ĐÃ TẮT trước khi đếm (v523, Codex #363 vòng 3): lịch
    # sử chi nhánh có thể giữ một ánh xạ chết cạnh ánh xạ sống, đếm chung là
    # báo "nhiều ánh xạ" và chặn đúng hoá đơn đang làm. Món tắt thì không ai
    # nhập vào được nữa, quy cách của nó không còn là một lựa chọn.
    da_chon = [d for d in ds if (d.get(TRUONG) or '').strip() and not _mon_tat(d.item_code)]
    if not da_chon:
        return None
    if len(da_chon) != 1:
        frappe.throw('Có nhiều ánh xạ quy cách cho NCC %s, hàng "%s". Giữ một lựa chọn rõ ràng trước khi tạo hoá đơn.'
                     % (mst, ten))
    d = da_chon[0]
    if d.item_code != item_code:
        frappe.throw('Ánh xạ quy cách NCC của "%s" đang chọn Món %s, khác Món %s trên dòng. '
                     'Đối chiếu lại ánh xạ, không dùng quy cách của món khác.' % (ten, d.item_code, item_code))
    uom = d.get(TRUONG).strip()
    _kiem_uom(item_code, uom)
    return uom
