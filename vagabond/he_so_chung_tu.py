"""Kiểm quy đổi tại Document, không tự sửa số lượng hoặc tiền chứng từ.

Danh mục dùng cho dòng mới. Chứng từ nguồn đã ghi sổ và phiếu trả giữ
quy cách có căn cứ lịch sử; không lấy một mã dòng tuỳ ý để bỏ qua luật.

Core ERPNext de59166 controllers/accounts_controller.py
set_missing_item_details chỉ bổ sung conversion_factor khi ô còn trống;
giá trị sai nhưng có sẵn như 1 vẫn tồn tại. buying_controller.py:730
set_qty_as_per_stock_uom lấy stock_qty = qty * conversion_factor;
selling_controller.py:281 có cùng phép đổi. Vì vậy guard chạy validate
sau core chuẩn hoá và before_submit, không chỉ ở UI chọn Món.
"""
import math
import frappe


NGUON = {
    'Purchase Invoice': [('Purchase Receipt', 'purchase_receipt', 'pr_detail'),
                         ('Purchase Order', 'purchase_order', 'po_detail')],
    'Purchase Receipt': [('Purchase Order', 'purchase_order', 'purchase_order_item')],
    'Sales Invoice': [('Delivery Note', 'delivery_note', 'dn_detail'),
                      ('Sales Order', 'sales_order', 'so_detail')],
    'Delivery Note': [('Sales Order', 'against_sales_order', 'so_detail')],
}


def _so(gia_tri):
    try:
        so = float(gia_tri)
        return so if math.isfinite(so) and so > 0 else None
    except (TypeError, ValueError, OverflowError):
        return None


def _loi(doc, dong, noi_dung):
    frappe.throw('Dòng %s, món %s trên %s: %s. Kiểm đơn vị và bảng quy đổi của Món rồi lưu lại; '
                 'không đổi số lượng hoặc đơn giá để bù hệ số.'
                 % (dong.idx, dong.item_code, doc.name or doc.doctype, noi_dung),
                 title='Sai hệ số quy đổi')


def _doc_nguon(loai, ten, doc, dong, khoa):
    # Table names only come from NGUON or the current supported DocType.
    if khoa:
        dong_khoa = frappe.db.sql('select docstatus from `tab' + loai + '` where name=%s for update', ten)
        if not dong_khoa or dong_khoa[0][0] != 1:
            _loi(doc, dong, 'chứng từ nguồn không còn được ghi sổ')
    nguon = frappe.get_doc(loai, ten)
    if nguon.docstatus != 1 or nguon.company != doc.company:
        _loi(doc, dong, 'chứng từ nguồn phải đã ghi sổ và cùng công ty')
    for ben in ('supplier', 'customer'):
        if doc.get(ben) and nguon.get(ben) != doc.get(ben):
            _loi(doc, dong, 'chứng từ nguồn không cùng nhà cung cấp hoặc khách hàng')
    return nguon


def _he_so_nguon(doc, dong, khoa):
    if doc.get('is_return') and doc.get('return_against'):
        nguon = _doc_nguon(doc.doctype, doc.return_against, doc, dong, khoa)
        if nguon.get('is_return'):
            _loi(doc, dong, 'phiếu trả phải tham chiếu chứng từ gốc không phải phiếu trả')
        cac_dong = [r for r in nguon.items if r.item_code == dong.item_code]
        if not cac_dong:
            _loi(doc, dong, 'món không có trên chứng từ trả lại')
        ds = [r for r in cac_dong if r.uom == dong.uom]
        # Core cho phép trả bằng đơn vị khác và kiểm hạn mức stock_qty.
        # Chỉ giữ hệ số lịch sử khi cùng UOM; đơn vị khác dùng master.
        if not ds:
            return None, False
        hs = {_so(r.conversion_factor) for r in ds}
        if len(hs) != 1 or None in hs:
            _loi(doc, dong, 'không xác định được duy nhất quy cách của món trên chứng từ trả lại')
        return hs.pop(), True
    for loai, truong_phieu, truong_dong in NGUON.get(doc.doctype, []):
        ten, ma = dong.get(truong_phieu), dong.get(truong_dong)
        if not ten and not ma:
            continue
        if not ten or not ma:
            _loi(doc, dong, 'thiếu cặp phiếu nguồn và dòng nguồn')
        nguon = _doc_nguon(loai, ten, doc, dong, khoa)
        r = next((r for r in nguon.items if r.name == ma), None)
        if not r or r.item_code != dong.item_code:
            _loi(doc, dong, 'dòng nguồn không thuộc phiếu đã chọn hoặc khác món/đơn vị')
        da_duyet = False
        if loai == 'Purchase Receipt':
            from vagabond.quy_cach_doi_chieu import dong_hieu_luc
            r = dong_hieu_luc([r.as_dict()], khoa=khoa)[0]
            da_duyet = bool(r.get('can_cu_quy_cach'))
        he_so = _so(r.conversion_factor)
        if he_so is None:
            _loi(doc, dong, 'hệ số trên chứng từ nguồn không hợp lệ')
        if not da_duyet:
            kho = frappe.db.get_value('Item', dong.item_code, 'stock_uom')
            if r.uom == kho:
                cac = {1.0}
            else:
                ds = frappe.db.sql('select conversion_factor from `tabUOM Conversion Detail` '
                    'where parent=%s and parenttype=%s and uom=%s' + (' for update' if khoa else ''),
                    (dong.item_code, 'Item', r.uom))
                cac = {_so(x[0]) for x in ds}
            if len(cac) != 1 or None in cac or abs(he_so - next(iter(cac))) > 0.000001:
                _loi(doc, dong, 'quy cách chứng từ nguồn khác danh mục hiện tại; cần xác nhận căn cứ lịch sử '
                     'hoặc hiệu chỉnh quy cách trước khi lập chứng từ mới')
        if r.uom != dong.uom:
            if da_duyet:
                _loi(doc, dong, 'căn cứ hiệu chỉnh quy cách yêu cầu cùng đơn vị mua với phiếu nhập')
            # Không so hệ số Hộp với Gram. Nguồn vẫn phải đúng dòng/món;
            # core kiểm lượng đã nhận bằng stock_qty khi đổi đơn vị.
            return None, False
        return he_so, da_duyet
    return None, False


def kiem(doc, method=None):
    if doc.doctype not in ('Purchase Order', 'Purchase Receipt', 'Purchase Invoice',
                          'Sales Order', 'Delivery Note', 'Sales Invoice', 'POS Invoice', 'Stock Entry',
                          'BOM', 'Material Request', 'Subcontracting Order',
                          'Subcontracting Receipt', 'Subcontracting Inward Order'):
        return
    hanh_dong = getattr(doc, '_action', None)
    if doc.docstatus == 2 or hanh_dong == 'update_after_submit':
        return
    # Không bỏ qua lần submit đầu: Frappe đã đặt docstatus=1 lúc này.
    if doc.docstatus == 1 and hanh_dong != 'submit' and not doc.is_new() and method != 'kiem_nguon_san_xuat':
        if frappe.db.get_value(doc.doctype, doc.name, 'docstatus') == 1:
            return
    khoa = doc.docstatus == 1 or method == 'before_submit'
    if doc.doctype in ('Stock Entry', 'Subcontracting Order', 'Subcontracting Receipt', 'Subcontracting Inward Order'):
        kiem_bom_lenh(doc)
    cac_dong = list(doc.get('items') or [])
    if doc.doctype == 'BOM':
        cac_dong += list(doc.get('secondary_items') or [])
    for dong in cac_dong:
        if not dong.get('item_code'):
            continue
        rows = frappe.db.sql('select stock_uom from `tabItem` where name=%s'
                             + (' for update' if khoa else ''), dong.item_code)
        if not rows or not rows[0][0]:
            _loi(doc, dong, 'Món chưa có đơn vị kho hợp lệ')
        kho = rows[0][0]
        if dong.get('stock_uom') and dong.stock_uom != kho:
            _loi(doc, dong, 'đơn vị kho trên dòng khác danh mục Món (%s)' % kho)
        hs = _so(dong.get('conversion_factor'))
        if hs is None:
            _loi(doc, dong, 'hệ số phải là số hữu hạn lớn hơn 0')
        # Các dòng gia công v16 không có ô UOM mua: qty đã là đơn vị
        # kho. Core vẫn nhân conversion_factor khi sinh SLE nên phải là1.
        if doc.doctype in ('Subcontracting Order', 'Subcontracting Receipt', 'Subcontracting Inward Order'):
            if abs(hs - 1) > 0.000001:
                _loi(doc, dong, 'số lượng gia công đã theo đơn vị kho %s, hệ số phải bằng 1' % kho)
            continue
        if not dong.get('uom'):
            _loi(doc, dong, 'chưa chọn đơn vị tính')
        if (doc.doctype == 'Purchase Invoice' and doc.get('custom_minvoice_id')
                and not doc.get('is_return') and not dong.get('pr_detail') and not dong.get('po_detail')):
            from vagabond.quy_cach_ncc import lay
            mst = frappe.db.get_value('MInvoice Invoice', doc.custom_minvoice_id, 'mst_doi_tac')
            da_chon = lay(dong.item_code, mst, dong.get('ten_hang_ncc'))
            if da_chon and dong.uom != da_chon:
                _loi(doc, dong, 'NCC đã đối chiếu đơn vị %s cho tên hàng này, không dùng đơn vị %s'
                     % (da_chon, dong.uom))
        nguon, da_duyet = _he_so_nguon(doc, dong, khoa)
        if dong.uom == kho:
            dung = 1.0
        else:
            dung = nguon if da_duyet else None
            if dung is None:
                ds = frappe.db.sql('select conversion_factor from `tabUOM Conversion Detail` '
                    'where parent=%s and parenttype=%s and uom=%s' + (' for update' if khoa else ''),
                    (dong.item_code, 'Item', dong.uom))
                cac = {_so(r[0]) for r in ds}
                if len(cac) != 1 or None in cac:
                    _loi(doc, dong, 'Món chưa khai duy nhất hệ số cho đơn vị %s' % dong.uom)
                dung = cac.pop()
                if nguon is not None and abs(nguon - dung) > 0.000001:
                    _loi(doc, dong, 'quy cách chứng từ nguồn khác danh mục hiện tại; cần xác nhận căn cứ lịch sử '
                         'hoặc hiệu chỉnh quy cách trước khi lập chứng từ mới')
        if abs(hs - dung) > 0.000001:
            _loi(doc, dong, '1 %s phải bằng %g %s theo căn cứ quy cách, dòng đang ghi %g'
                 % (dong.uom, dung, kho, hs))
        if khoa and doc.doctype == 'Purchase Invoice' and doc.get('custom_minvoice_id'):
            from vagabond.dvt_mua import dvt_tren_hoa_don, don_vi_chua_khai
            goc = dvt_tren_hoa_don(dong.get('description'))
            if don_vi_chua_khai(goc, dong.uom, hs):
                _loi(doc, dong, 'đơn vị NCC %s chưa được đối chiếu, không ghi sổ dòng tạm quy về đơn vị kho' % goc)


def kiem_bom_lenh(doc, method=None):
    """BOM cũ sai không được biến thành lượng stock-UOM hợp lệ trên phiếu kho."""
    if doc.docstatus == 2 or getattr(doc, '_action', None) == 'update_after_submit':
        return
    ten = doc.get('bom_no')
    if not ten and doc.get('work_order'):
        ten = frappe.db.get_value('Work Order', doc.work_order, 'bom_no')
    gia_cong = doc.doctype in ('Subcontracting Order', 'Subcontracting Receipt', 'Subcontracting Inward Order')
    cho, da_xem = [ten] if ten else [], set()
    if gia_cong:
        cho.extend(d.bom for d in doc.get('items') or [] if d.get('bom'))
    while cho:
        ma = cho.pop()
        if ma in da_xem:
            continue
        da_xem.add(ma)
        bom = frappe.get_doc('BOM', ma)
        kiem(bom, 'kiem_nguon_san_xuat')
        if gia_cong or doc.get('use_multi_level_bom'):
            cho.extend(d.bom_no for d in bom.items if d.get('bom_no'))
