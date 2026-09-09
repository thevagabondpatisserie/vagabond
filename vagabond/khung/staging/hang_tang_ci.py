"""Đơn tặng thử dùng bánh từ ca sản xuất. Chỉ kiểm ghi sổ, chưa phát hành HĐĐT."""
import json
import os
from pathlib import Path
from vagabond.khung.staging.van_don_ci import khoa


def tao():
    import frappe
    from vagabond import diem_ban
    khoa()
    frappe.set_user('Administrator')
    goc = Path(os.environ['VGB_ARTIFACTS'])
    nhan = json.loads((goc / 'nhan-hang-fixture.json').read_text())
    sx = json.loads((goc / 'san-xuat-fixture.json').read_text())
    ct = nhan['cong_ty']
    tk = {}
    for so, loai in (('64181', 'Expense'), ('64182', 'Expense'), ('33311', 'Liability')):
        if frappe.db.exists('Account', {'company': ct, 'account_number': so}):
            raise RuntimeError('Tài khoản fixture đã tồn tại, cần bench mới.')
        cha = frappe.db.get_value('Account', {'company': ct, 'root_type': loai, 'is_group': 1}, 'name')
        a = frappe.get_doc({'doctype': 'Account', 'account_name': 'THU257 ' + so,
            'account_number': so, 'company': ct, 'parent_account': cha,
            'account_currency': 'VND', 'is_group': 0})
        a.insert(ignore_permissions=True)
        tk[so] = a.name
    cfg = diem_ban.ds()
    sales = next(d for d in cfg if not d['quay'])
    sales['kho_tang'] = sx['kho_nhan']
    c = frappe.get_doc('Vagabond Settings')
    c.set(diem_ban.TRUONG, json.dumps(cfg, ensure_ascii=False))
    c.tk_chi_phi_qua_tang = tk['64181']
    # Cấu hình thật của site thử, không mock _tu_xuat_hddt/submit.
    # Ca này không được báo là đã kiểm đường phát hành M-Invoice.
    c.tu_xuat_hddt = 0
    c.save(ignore_permissions=True)
    kh = frappe.get_doc({'doctype': 'Customer', 'customer_name': 'THU257 Hang tang',
        'customer_type': 'Individual', 'customer_group': 'All Customer Groups',
        'territory': 'All Territories'})
    kh.insert(ignore_permissions=True)
    mau = frappe.get_doc({'doctype': 'Sales Taxes and Charges Template',
        'title': 'THU257 VAT8', 'company': ct, 'taxes': [{
            'charge_type': 'On Net Total', 'account_head': tk['33311'],
            'description': 'VAT8 da gom gia', 'rate': 8, 'included_in_print_rate': 1}]})
    mau.insert(ignore_permissions=True)
    hd = frappe.get_doc({'doctype': 'Sales Invoice', 'company': ct, 'customer': kh.name,
        'currency': 'VND', 'conversion_rate': 1, 'taxes_and_charges': mau.name,
        'custom_pancake_id': 'THU257-TANG', 'custom_pancake_display_id': 'THU257-TANG',
        'custom_nguon': 'Tại chỗ', 'vgb_quay': '',
        'vgb_pt_thanh_toan': 'Hàng tặng', 'vgb_tang_loai': 'marketing',
        'vgb_tang_ly_do': 'Banh thu CI tu lenh san xuat, khong giao that',
        'items': [{'item_code': sx['banh'], 'qty': 2, 'rate': 1080}]})
    hd.insert(ignore_permissions=True)
    frappe.db.commit()
    (goc / 'hang-tang-fixture.json').write_text(json.dumps({
        'hoa_don': hd.name, 'banh': sx['banh'], 'kho': sx['kho_nhan'], 'tk': tk}))


def kiem():
    import frappe
    khoa()
    goc = Path(os.environ['VGB_ARTIFACTS'])
    f = json.loads((goc / 'hang-tang-fixture.json').read_text())
    hd = frappe.get_doc('Sales Invoice', f['hoa_don'])
    assert hd.docstatus == 1 and hd.vgb_tang_duyet == 'Đã duyệt', 'Chưa duyệt/ghi sổ'
    assert hd.update_stock == 1 and hd.vgb_tang_kho == f['kho'], 'Sai kho tặng'
    assert float(hd.outstanding_amount) == 0, 'Đơn tặng không được còn nợ'
    assert float(hd.grand_total) == 2160, 'Tổng đơn thử phải2160'
    assert not hd.custom_hddt_so, 'Ca này không phát hành HĐĐT'
    sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type': 'Sales Invoice',
        'voucher_no': hd.name, 'is_cancelled': 0},
        fields=['item_code', 'warehouse', 'actual_qty', 'stock_value_difference'], limit_page_length=0)
    assert len(sle) == 1, 'Phải đúng một dòng xuất'
    r = sle[0]
    assert (r.item_code, r.warehouse, float(r.actual_qty), float(r.stock_value_difference)) == (
        f['banh'], f['kho'], -2, -2000), 'Kho/giá vốn không khớp mẻ sản xuất'
    gl = frappe.get_all('GL Entry', filters={'voucher_type': 'Sales Invoice',
        'voucher_no': hd.name, 'is_cancelled': 0},
        fields=['account', 'debit', 'credit', 'party_type'], limit_page_length=0)
    from erpnext.stock import get_warehouse_account_map
    kho_tk = get_warehouse_account_map(hd.company)[f['kho']].account
    dung = {f['tk']['64181']: 2000, f['tk']['64182']: 160,
            f['tk']['33311']: -160, kho_tk: -2000}
    thuc = {}
    for d in gl:
        assert not d.party_type, 'Không được sinh công nợ khách'
        thuc[d.account] = thuc.get(d.account, 0) + float(d.debit) - float(d.credit)
    assert {k: round(v, 2) for k, v in thuc.items() if round(v, 2)} == dung, 'GL phải đúng giá vốn và VAT'
    assert float(frappe.db.get_value('Bin', {'item_code': f['banh'], 'warehouse': f['kho']}, 'actual_qty') or 0) == 0, 'Bánh phải xuất hết2'
    (goc / 'hang-tang-db.json').write_text(json.dumps({'dat': True, 'hoa_don': hd.name,
        'gia_von': 2000, 'vat': 160, 'con_no': 0}))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        kiem()
    finally:
        frappe.destroy()
