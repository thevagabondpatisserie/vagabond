"""Fixture vận đơn ghi thật chỉ ở CI dùng một lần; không có API whitelisted."""
import json
import os
from pathlib import Path


def khoa():
    import frappe
    if os.environ.get('GITHUB_ACTIONS') != 'true' or frappe.local.site != 'bench-ci.localhost':
        raise RuntimeError('Chỉ dùng bench CI riêng.')
    if not all(frappe.conf.get(k) for k in ('vagabond_bench_thu', 'mute_emails', 'disable_scheduler')):
        raise RuntimeError('Thiếu khoá site thử.')


def tao():
    import frappe
    from frappe.utils import add_days, nowdate
    khoa()
    frappe.set_user('Administrator')
    if frappe.db.exists('Van Don', {'pancake_id': 'THU257-93405'}):
        raise RuntimeError('Fixture cũ còn lại; phải dùng bench mới, không âm thầm xoá.')
    c = frappe.get_doc('Vagabond Settings')
    c.pancake_shop_id = 'THU257'
    c.pancake_api_key = 'THU257'
    c.save(ignore_permissions=True)
    cu = str(add_days(nowdate(), 3650))
    moi = str(add_days(cu, 2))
    d = frappe.get_doc({'doctype': 'Van Don', 'ngay_giao': cu,
        'pancake_id': 'THU257-93405', 'ma_don': 'THU257-93405',
        'trang_thai': 'Chờ giao', 'kenh': 'Shipper nội bộ',
        'khach': 'Khách thử staging257', 'dia_chi': 'Địa chỉ thử phải giữ', 'tien_thu_ho': 123})
    d.append('mon', {'ma_hang': 'THU-A', 'ten': 'Bánh thử A', 'so_luong': 2})
    d.append('mon', {'ma_hang': 'THU-B', 'ten': 'Bánh thử B', 'so_luong': 1})
    d.insert(ignore_permissions=True)
    frappe.db.commit()
    ra = {'ten': d.name, 'ngay_cu': cu, 'ngay_moi': moi, 'don': {
        'id': d.pancake_id, 'display_id': d.ma_don, 'status': 1,
        'estimate_delivery_date': moi + 'T08:00:00+07:00',
        'items': [{'variation_info': {'display_id': 'THU-A', 'name': 'Bánh thử A',
                                     'retail_price': 100}, 'quantity': 1}]}}
    (Path(os.environ['VGB_ARTIFACTS']) / 'van-don-fixture.json').write_text(json.dumps(ra))
    return ra


def kiem():
    import frappe
    khoa()
    goc = Path(os.environ['VGB_ARTIFACTS'])
    f = json.loads((goc / 'van-don-fixture.json').read_text())
    d = frappe.get_doc('Van Don', f['ten'])
    assert str(d.ngay_giao) == f['ngay_moi'], 'DB chưa đổi ngày'
    assert [(r.ma_hang, r.so_luong) for r in d.mon] == [('THU-A', 1)], 'DB chưa thay bảng món'
    assert d.dia_chi == 'Địa chỉ thử phải giữ', 'Mất địa chỉ'
    assert frappe.db.count('Van Don', {'pancake_id': f['don']['id']}) == 1, 'Trùng vận đơn'
    assert not frappe.db.count('Van Don', {'name': d.name, 'ngay_giao': f['ngay_cu']}), 'Còn ở ngày cũ'
    log = [json.loads(s) for s in (goc / 'pancake-http.jsonl').read_text().splitlines()]
    duong = '/api/v1/shops/THU257/orders'
    assert log == [
        {'duong': duong, 'so_don': 0},
        {'duong': duong + '/' + f['don']['id'], 'so_don': 1},
        {'duong': duong, 'so_don': 1}], 'Chưa đi đúng danh sách rỗng -> GET ID -> đồng bộ lại ngày mới'
    (goc / 'van-don-db.json').write_text(json.dumps({'dat': True, 'ten': d.name,
        'ngay': str(d.ngay_giao), 'mon': [(r.ma_hang, r.so_luong) for r in d.mon]}))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        kiem()
    finally:
        frappe.destroy()
