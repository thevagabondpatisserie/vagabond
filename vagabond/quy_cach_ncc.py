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
        frappe.throw('Món %s chưa khai duy nhất đơn vị %s trong bảng quy đổi. Khai đúng quy cách trước khi chọn ánh xạ.'
                     % (item_code, uom))
    try:
        hs = float(ds[0].conversion_factor)
    except (TypeError, ValueError, OverflowError):
        hs = 0
    if not math.isfinite(hs) or hs <= 0:
        frappe.throw('Món %s có hệ số không hợp lệ cho đơn vị %s. Hệ số phải hữu hạn và lớn hơn 0.' % (item_code, uom))


def kiem(doc, method=None):
    doc.supplier_mst = (doc.get('supplier_mst') or '').strip().split('-')[0]
    uom = (doc.get(TRUONG) or '').strip()
    if not uom:
        return
    if not doc.get('item_code'):
        frappe.throw('Chọn Món trước khi chọn Đơn vị đã đối chiếu của nhà cung cấp.')
    if not (doc.get('supplier_mst') or '').strip() or not (doc.get('ten_ncc') or '').strip():
        frappe.throw('Ánh xạ quy cách cần MST nhà cung cấp và tên hàng nguyên văn trên hoá đơn.')
    _kiem_uom(doc.item_code, uom)


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
    ds = frappe.get_all(LOAI, filters={'ten_ncc': ten},
        or_filters=[['supplier_mst', '=', mst], ['supplier_mst', 'like', mst+'-%']],
        fields=['name', 'supplier_mst', 'ten_ncc', 'item_code', TRUONG], limit_page_length=0)
    # Collation MariaDB có thể coi khác dấu/hoa thường là giống nhau.
    # Quy cách chỉ áp dụng đúng tên NCC đã đối chiếu, không gần giống.
    ds = [d for d in ds if (d.supplier_mst or '').strip().split('-')[0] == mst and (d.ten_ncc or '').strip() == ten]
    da_chon = [d for d in ds if (d.get(TRUONG) or '').strip()]
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
