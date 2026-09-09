"""Quy ước riêng14 nguyên liệu: anh Việt duyệt ngày09/09/2026, 1ML=1Gram.

Không phải bảng mật độ và không phải quy đổi UOM toàn hệ thống. Giữ ML
là đơn vị kho để không diễn giải lại SLE cũ. ERPNext v16.28.0,
manufacturing/doctype/bom/bom.py:update_stock_qty nhân qty với hệ số;
get_bom_items_as_dict và bảng khai triển dùng stock_qty. Vì vậy chỉ đổi
nhãn ML sang Gram khi hệ số1, lượng kho và tiền công thức giữ nguyên.
"""

import math

MA_NGUYEN_LIEU = (
    'NVLT00002', 'NVLT00013', 'NVLT00149', 'NVLT00150', 'NVLT00151',
    'NVLT00153', 'NVLT00154', 'NVLT00158', 'NVLT00174', 'NVLT00175',
    'NVLT00192', 'NVLT00245', 'NVLT00305', 'NVLT00329',
)
CAN_CU = 'Quy ước #252 ngày09/09/2026: anh Việt duyệt riêng14 mã, 1 ML = 1 Gram.'


def bang_doi(dong, kiem_luong_kho=False):
    """Kế hoạch thuần; không hợp thức hoá một hệ số sai đã có trên BOM."""
    if dong.get('item_code') not in MA_NGUYEN_LIEU:
        return {}
    if dong.get('uom') not in ('ML', 'Gram'):
        raise ValueError('Định mức của mã đã duyệt phải dùng Gram; cần đối chiếu dòng đang dùng %s'
                         % dong.get('uom'))
    try:
        hs = float(dong.get('conversion_factor'))
        qty = float(dong.get('qty'))
        if not math.isfinite(hs) or hs != 1 or not math.isfinite(qty) or qty <= 0:
            raise ValueError()
        if kiem_luong_kho:
            kho = float(dong.get('stock_qty'))
            if not math.isfinite(kho) or not math.isclose(kho, qty, rel_tol=0, abs_tol=0.000001):
                raise ValueError()
    except (TypeError, ValueError, OverflowError):
        raise ValueError('Chưa thể đổi nhãn sang Gram: cần kiểm hệ số1 và lượng kho của dòng BOM') from None
    return {'uom': 'Gram'} if dong.get('uom') == 'ML' else {}


# phần cần Frappe
def kiem_mon(doc, method=None):
    import frappe
    if doc.name not in MA_NGUYEN_LIEU and doc.get('item_code') not in MA_NGUYEN_LIEU:
        return
    gram = [d for d in doc.get('uoms') or [] if d.uom == 'Gram']
    if doc.stock_uom != 'ML' or len(gram) != 1 or gram[0].conversion_factor != 1:
        frappe.throw('Món %s thuộc quy ước #252: giữ kho ML và khai duy nhất Gram với hệ số1. '
                     'Cần đối chiếu quy ước đã duyệt trước khi đổi.' % doc.item_code)


def truoc_khi_luu(doc, method=None):
    import frappe
    if doc.docstatus == 2 or getattr(doc, '_action', None) == 'update_after_submit':
        return
    for dong in doc.get('items') or []:
        try:
            doi = bang_doi(dong)
        except ValueError as e:
            frappe.throw('Dòng %s, món %s trên %s: %s.' %
                         (dong.idx, dong.item_code, doc.name or 'BOM', e))
        if doi:
            dong.update(doi)


def ap_dung():
    """Migration một giao dịch, lập và kiểm toàn bộ kế hoạch trước khi ghi.

    BOM đã ghi sổ không cho sửa uom qua save. Đây là hiệu chỉnh nhãn được
    duyệt, không đổi công thức: db.set_value chỉ ghi uom, giữ nguyên tất cả
    trường số và bảng khai triển, thêm Comment để lưu căn cứ từng BOM.
    Không commit ở đây; lỗi bất kỳ để Frappe rollback cả patch.
    """
    import frappe
    ds_mon = []
    for ma in MA_NGUYEN_LIEU:
        if not frappe.db.exists('Item', ma):
            continue
        frappe.db.sql('select name from `tabItem` where name=%s for update', ma)
        mon = frappe.get_doc('Item', ma)
        if mon.stock_uom != 'ML':
            frappe.throw('Quy ước #252: %s không còn quản kho bằng ML; cần đối chiếu trước khi migrate.' % ma)
        gram = [d for d in mon.uoms if d.uom == 'Gram']
        if len(gram) > 1 or (gram and gram[0].conversion_factor != 1):
            frappe.throw('Quy ước #252: %s đã có quy đổi Gram khác1 hoặc trùng; cần đối chiếu trước khi migrate.' % ma)
        if not gram:
            ds_mon.append(mon)
    ds_dong = frappe.db.sql('''select d.name, d.parent, d.item_code, d.uom,
        d.conversion_factor, d.qty, d.stock_qty, d.stock_uom
        from `tabBOM Item` d inner join `tabBOM` b on b.name=d.parent
        where d.item_code in %(ma)s and b.docstatus < 2
        order by b.name, d.idx for update''', {'ma': MA_NGUYEN_LIEU}, as_dict=True)
    doi_dong = []
    for dong in ds_dong:
        if dong.stock_uom != 'ML':
            frappe.throw('Quy ước #252: đơn vị kho trên %s, dòng %s khác ML.' % (dong.parent, dong.name))
        try:
            doi = bang_doi(dong, kiem_luong_kho=True)
        except ValueError as e:
            frappe.throw('%s, dòng %s: %s.' % (dong.parent, dong.name, e))
        if doi:
            doi_dong.append((dong, doi))
    if ds_mon and not frappe.db.exists('UOM', 'Gram'):
        frappe.get_doc(dict(doctype='UOM', uom_name='Gram', must_be_whole_number=0)).insert(ignore_permissions=True)
    for mon in ds_mon:
        mon.append('uoms', dict(uom='Gram', conversion_factor=1))
        mon.save(ignore_permissions=True)
        mon.reload()
        kiem_mon(mon)
        mon.add_comment('Comment', CAN_CU + ' Bổ sung Gram=1ML; giữ đơn vị kho và các quy cách mua.')
        frappe.clear_document_cache('Item', mon.name)
    cac_bom = set()
    for dong, doi in doi_dong:
        frappe.db.set_value('BOM Item', dong.name, doi, update_modified=False)
        cac_bom.add(dong.parent)
    for ma in sorted(cac_bom):
        bom = frappe.get_doc('BOM', ma)
        bom.add_comment('Comment', CAN_CU + ' Đổi nhãn dòng nguyên liệu từ ML sang Gram; giữ số lượng, hệ số1, lượng kho, tiền và bảng khai triển.')
        frappe.clear_document_cache('BOM', ma)
    return {'mon_bo_sung': len(ds_mon), 'dong_bom': len(doi_dong), 'bom': len(cac_bom)}
