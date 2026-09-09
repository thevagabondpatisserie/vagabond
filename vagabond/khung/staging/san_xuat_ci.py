"""Fixture hoàn tất lệnh thật qua app; chưa thay ca tạo lệnh từ BOM trên UI."""
import json
import os
from pathlib import Path
from vagabond.khung.staging.van_don_ci import khoa


def tao():
    import frappe
    khoa()
    frappe.set_user('Administrator')
    if frappe.db.get_single_value('System Settings', 'time_zone') != 'Asia/Ho_Chi_Minh':
        raise RuntimeError('Ca lech gio can site Asia/Ho_Chi_Minh va browser UTC.')
    goc = Path(os.environ['VGB_ARTIFACTS'])
    nhan = json.loads((goc / 'nhan-hang-fixture.json').read_text())
    cty = nhan['cong_ty']
    nvl, tp = 'THU257-SX-NVL', 'THU257-SX-BANH'
    for ma, lo in ((nvl, 0), (tp, 1)):
        if frappe.db.exists('Item', ma):
            raise RuntimeError('Fixture sản xuất cũ còn lại, cần bench mới.')
        frappe.get_doc({'doctype': 'Item', 'item_code': ma, 'item_name': ma,
            'item_group': 'All Item Groups', 'stock_uom': 'Nos', 'is_stock_item': 1,
            'include_item_in_manufacturing': 1, 'has_batch_no': lo,
            'create_new_batch': lo, 'has_expiry_date': lo, 'shelf_life_in_days': 10 if lo else 0,
            'valuation_rate': 1000}).insert(ignore_permissions=True)
    se = frappe.get_doc({'doctype': 'Stock Entry', 'company': cty,
        'stock_entry_type': 'Material Receipt', 'purpose': 'Material Receipt',
        'items': [{'item_code': nvl, 'qty': 10, 't_warehouse': nhan['kho_xuat'],
            'basic_rate': 1000, 'cost_center': frappe.db.get_value('Company', cty, 'cost_center')}]})
    se.insert(ignore_permissions=True)
    se.submit()
    bom = frappe.get_doc({'doctype': 'BOM', 'company': cty, 'item': tp, 'quantity': 1,
        'is_active': 1, 'is_default': 1, 'rm_cost_as_per': 'Valuation Rate',
        'items': [{'item_code': nvl, 'qty': 1, 'uom': 'Nos', 'rate': 1000}]})
    bom.insert(ignore_permissions=True)
    bom.submit()
    wo = frappe.get_doc({'doctype': 'Work Order', 'company': cty, 'production_item': tp,
        'bom_no': bom.name, 'qty': 2, 'source_warehouse': nhan['kho_xuat'],
        'fg_warehouse': nhan['kho_nhan'], 'wip_warehouse': nhan['kho_xuat'],
        'skip_transfer': 1, 'use_multi_level_bom': 1})
    wo.insert(ignore_permissions=True)
    wo.submit()
    frappe.db.commit()
    f = {'lenh': wo.name, 'bom': bom.name, 'nvl': nvl, 'banh': tp, 'nhap_nvl': se.name,
        'kho_xuat': nhan['kho_xuat'], 'kho_nhan': nhan['kho_nhan']}
    (goc / 'san-xuat-fixture.json').write_text(json.dumps(f))


def kiem():
    import frappe
    khoa()
    goc = Path(os.environ['VGB_ARTIFACTS'])
    f = json.loads((goc / 'san-xuat-fixture.json').read_text())
    wo = frappe.get_doc('Work Order', f['lenh'])
    assert float(wo.produced_qty) == 2 and wo.status == 'Completed', 'Lệnh chưa hoàn thành2'
    ds = frappe.get_all('Stock Entry', filters={'work_order': wo.name}, fields=['name', 'docstatus'], limit_page_length=0)
    assert len(ds) == 1 and ds[0].docstatus == 1, 'Phải một phiếu sản xuất ghi sổ, không nháp sót'
    from frappe.utils import get_datetime
    nhap = frappe.get_doc('Stock Entry', f['nhap_nvl'])
    xuat = frappe.get_doc('Stock Entry', ds[0].name)
    def thoi_diem(doc):
        return get_datetime(str(doc.posting_date) + ' ' + str(doc.posting_time))
    assert thoi_diem(xuat) >= thoi_diem(nhap), 'Giờ máy khách đã đặt xuất trước nhập'
    sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type': 'Stock Entry',
        'voucher_no': ds[0].name, 'is_cancelled': 0},
        fields=['item_code', 'warehouse', 'actual_qty', 'stock_value_difference', 'serial_and_batch_bundle'], limit_page_length=0)
    assert sorted((d.item_code, d.warehouse, float(d.actual_qty)) for d in sle) == sorted([
        (f['nvl'], f['kho_xuat'], -2.0), (f['banh'], f['kho_nhan'], 2.0)]), 'SLE phải trừ2 nguyên liệu và nhập2 bánh'
    assert abs(sum(float(d.stock_value_difference) for d in sle)) < 0.01, 'Giá trị kho không được tự tăng/giảm'
    for d in sle:
        gia = -2000 if d.item_code == f['nvl'] else 2000
        assert abs(float(d.stock_value_difference) - gia) < 0.01, 'Từng dòng kho phải đúng giá1000 x2'
    gl = frappe.get_all('GL Entry', filters={'voucher_type': 'Stock Entry', 'voucher_no': ds[0].name,
        'is_cancelled': 0}, fields=['account', 'debit', 'credit'], limit_page_length=0)
    assert abs(sum(float(d.debit) - float(d.credit) for d in gl)) < 0.01, 'GL không cân'
    # Core de59166 erpnext/stock/__init__.py: kho có thể lấy tài khoản từ
    # cha hoặc Company. Dùng đúng bộ phân giải, không chỉ đọc Warehouse.account.
    from erpnext.stock import get_warehouse_account_map
    tk = get_warehouse_account_map(wo.company)
    dung_tk, thuc_tk = {}, {}
    for kho, tien in ((f['kho_xuat'], -2000), (f['kho_nhan'], 2000)):
        acc = tk[kho].account
        dung_tk[acc] = dung_tk.get(acc, 0) + tien
    for d in gl:
        assert d.account in dung_tk, 'GL vào tài khoản ngoài hai kho'
        thuc_tk[d.account] = thuc_tk.get(d.account, 0) + float(d.debit) - float(d.credit)
    assert {k: round(v, 2) for k, v in thuc_tk.items() if abs(v) >= 0.01} == {
        k: v for k, v in dung_tk.items() if v}, 'GL không khớp giá trị từng tài khoản kho'
    thanh = next(d for d in sle if d.item_code == f['banh'])
    assert thanh.serial_and_batch_bundle, 'Thành phẩm chưa có gói lô'
    goi = frappe.get_doc('Serial and Batch Bundle', thanh.serial_and_batch_bundle)
    assert goi.docstatus == 1 and goi.voucher_no == ds[0].name and goi.warehouse == f['kho_nhan'], 'Gói lô phải ghi sổ đúng phiếu/kho'
    assert len(goi.entries) == 1 and goi.entries[0].batch_no and float(goi.entries[0].qty) == 2, 'Lô không có đúng2 bánh'
    assert frappe.db.get_value('Batch', goi.entries[0].batch_no, 'item') == f['banh'], 'Lô phải thuộc đúng món bánh'
    for ma, kho, so in ((f['nvl'], f['kho_xuat'], 8), (f['banh'], f['kho_nhan'], 2)):
        assert float(frappe.db.get_value('Bin', {'item_code': ma, 'warehouse': kho}, 'actual_qty') or 0) == so, 'Tồn cuối không khớp'
    (goc / 'san-xuat-db.json').write_text(json.dumps({'dat': True, 'lenh': wo.name,
        'phieu': ds[0].name, 'lo': goi.entries[0].batch_no, 'so_banh': 2}))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        kiem()
    finally:
        frappe.destroy()
