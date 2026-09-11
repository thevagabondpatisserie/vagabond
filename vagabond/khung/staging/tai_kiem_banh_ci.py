"""Tải tổng hợp 50/200 dòng kiểm bánh, giữ validation và nguồn đếm thật.

Chạy sau ca nghiệp vụ, ngày mai/ngày kia đúng chip trên app. Không sao chép
bánh/đơn khách thật, không chốt ngày, không sinh sổ kho hoặc gọi Pancake.
"""
import json
import os
from pathlib import Path
from .van_don_ci import khoa


def tao():
    import frappe
    from frappe.utils import add_days, nowdate
    khoa()
    frappe.set_user('Administrator')
    ket = []
    for buoc, so in enumerate((50, 200), 1):
        ngay = str(add_days(nowdate(), buoc))
        if frappe.db.exists('Kiem Banh Ngay', {'ngay': ngay}):
            raise RuntimeError('Ngày đo Kiểm bánh đã có dữ liệu; cần nền riêng.')
        d = frappe.get_doc({'doctype': 'Kiem Banh Ngay', 'ngay': ngay})
        for i in range(so):
            d.append('dong', {'ma_hang': 'BAWSDO257%03d' % i,
                'ten_banh': 'Bánh thử kiểm đếm %03d' % i,
                'ton_cu': 1, 'ton_d2': 2, 'ton_d1': 3, 'sx': 10, 'huy': 1})
        d.insert()
        d.reload()
        assert len(d.dong) == so
        assert all(r.co_the_ban == 15 and r.kiem_dem_ghi for r in d.dong)
        ket.append({'ngay': ngay, 'so_dong': so, 'ma': [r.ma_hang for r in d.dong],
                    'co_the_ban': 15})
    frappe.db.commit()
    (Path(os.environ['VGB_ARTIFACTS']) / 'tai-kiem-banh.json').write_text(json.dumps(ket))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        tao()
    finally:
        frappe.destroy()
