"""#257: yêu cầu 50, kho chỉ có30; lỗi rồi sửa20 qua màn Nhận hàng.

Chỉ tạo chứng từ tổng hợp trong CI dùng một lần, không dùng dữ liệu thật.
Tên công ty tương thích hằng COMPANY của app; không sửa payload trình duyệt.
"""
import json
import os
from pathlib import Path
from vagabond.khung.staging.van_don_ci import khoa


def tao():
    import frappe
    from frappe.utils import nowdate
    khoa()
    frappe.set_user('Administrator')
    cty = 'CÔNG TY TNHH PATISSERIE VAGABOND'
    if not frappe.db.exists('Company', cty):
        frappe.get_doc({'doctype': 'Company', 'company_name': cty, 'abbr': 'VGT',
            'default_currency': 'VND', 'country': 'Vietnam',
            'chart_of_accounts': 'Standard'}).insert(ignore_permissions=True)
    kho = []
    for ten in ('THU257 Xuat', 'THU257 Nhan'):
        k = frappe.get_doc({'doctype': 'Warehouse', 'warehouse_name': ten, 'company': cty})
        k.insert(ignore_permissions=True)
        kho.append(k.name)
    ma = 'THU257-NHAN-NVL'
    if frappe.db.exists('Item', ma):
        raise RuntimeError('Fixture nhận cũ còn lại, cần bench mới.')
    frappe.get_doc({'doctype': 'Item', 'item_code': ma, 'item_name': 'Nguyên liệu thử257',
        'item_group': 'All Item Groups', 'stock_uom': 'Nos', 'is_stock_item': 1,
        'is_purchase_item': 1, 'valuation_rate': 1000}).insert(ignore_permissions=True)
    cc = frappe.db.get_value('Company', cty, 'cost_center')
    se = frappe.get_doc({'doctype': 'Stock Entry', 'company': cty,
        'stock_entry_type': 'Material Receipt', 'purpose': 'Material Receipt',
        'items': [{'item_code': ma, 'qty': 30, 't_warehouse': kho[0],
                   'basic_rate': 1000, 'cost_center': cc}]})
    se.insert(ignore_permissions=True)
    se.submit()
    mr = frappe.get_doc({'doctype': 'Material Request', 'company': cty,
        'material_request_type': 'Material Transfer', 'schedule_date': nowdate(),
        'set_from_warehouse': kho[0], 'set_warehouse': kho[1],
        'items': [{'item_code': ma, 'qty': 50, 'schedule_date': nowdate(),
            'from_warehouse': kho[0], 'warehouse': kho[1], 'uom': 'Nos', 'conversion_factor': 1}]})
    mr.insert(ignore_permissions=True)
    mr.submit()
    frappe.db.commit()
    kq = {'phieu': mr.name, 'ma': ma, 'kho_xuat': kho[0], 'kho_nhan': kho[1], 'nhap_dau': se.name,
          'cong_ty': cty, 'so_phieu_truoc': frappe.db.count('Stock Entry', {'company': cty})}
    (Path(os.environ['VGB_ARTIFACTS']) / 'nhan-hang-fixture.json').write_text(json.dumps(kq))


def kiem():
    import frappe
    khoa()
    goc = Path(os.environ['VGB_ARTIFACTS'])
    f = json.loads((goc / 'nhan-hang-fixture.json').read_text())
    mr = frappe.get_doc('Material Request', f['phieu'])
    assert float(mr.items[0].ordered_qty) == 20, 'Yêu cầu phải mới nhận20'
    assert frappe.db.count('Stock Entry', {'company': f['cong_ty']}) == f['so_phieu_truoc'] + 1, 'Phải chỉ thêm một phiếu, kể cả nháp không có dòng'
    dong = frappe.get_all('Stock Entry Detail', filters={'item_code': f['ma'],
        'parent': ['!=', f['nhap_dau']]}, fields=['parent', 'qty', 'docstatus', 'material_request'], limit_page_length=0)
    assert len(dong) == 1 and dong[0].docstatus == 1 and float(dong[0].qty) == 20, 'Lần lỗi không được để phiếu nháp/dòng sót'
    assert dong[0].material_request == f['phieu'], 'Mất liên kết yêu cầu'
    sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_no': dong[0].parent,
        'voucher_type': 'Stock Entry', 'is_cancelled': 0},
        fields=['warehouse', 'actual_qty'], limit_page_length=0)
    assert sorted((d.warehouse, float(d.actual_qty)) for d in sle) == sorted([
        (f['kho_xuat'], -20.0), (f['kho_nhan'], 20.0)]), 'SLE phải trừ/cộng đúng20'
    for kho, so in ((f['kho_xuat'], 10), (f['kho_nhan'], 20)):
        assert float(frappe.db.get_value('Bin', {'item_code': f['ma'], 'warehouse': kho}, 'actual_qty') or 0) == so, 'Tồn không khớp'
    (goc / 'nhan-hang-db.json').write_text(json.dumps({'dat': True, 'phieu': dong[0].parent,
        'yeu_cau': mr.name, 'da_nhan': 20, 'ton_xuat': 10, 'ton_nhan': 20}))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        kiem()
    finally:
        frappe.destroy()
