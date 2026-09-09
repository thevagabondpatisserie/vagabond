"""300 hồ sơ nháp tổng hợp để đo danh sách/tìm kiếm, không tạo thanh toán.

Chỉ đo một lát cắt: hoàn ứng nháp, chưa thay tải hỗn hợp nhiều trạng thái.
Dùng NCC của nền thử đã có, không sao chép danh tính hoặc chứng từ thật.
"""
import json
import os
from pathlib import Path
from .van_don_ci import khoa


def tao():
    import frappe
    from frappe.utils import nowdate
    khoa()
    frappe.set_user('Administrator')
    goc = Path(os.environ['VGB_ARTIFACTS'])
    f = json.loads((goc / 'thanh-toan-fixture.json').read_text())
    h = frappe.get_doc('Vagabond Ho So TT', f['ho_so'])
    if frappe.db.count('Vagabond Ho So TT', {'ma': ['like', 'DO257-HS-%']}):
        raise RuntimeError('Đã có hồ sơ tải thử; cần bench mới.')
    ds = []
    for i in range(300):
        ma = 'DO257-HS-%04d' % i
        d = frappe.get_doc({'doctype': 'Vagabond Ho So TT', 'ma': ma,
            'loai': 'Hoan ung', 'trang_thai': 'Nhap', 'ngay': nowdate(),
            'nha_cung_cap': h.nha_cung_cap, 'ten_ncc': h.ten_ncc,
            'nguoi_tao': 'Administrator', 'ghi_chu': 'Tải thử ' + ma,
            'dong': [{'noi_dung': 'Khoản thử %s' % j, 'so_tien': (j + 1) * 1000,
                      'ngay_hd': nowdate()} for j in range(3)]})
        d.insert()
        d.reload()
        assert d.trang_thai == 'Nhap' and d.tong_tien == 6000 and not d.da_tra
        ds.append(d.name)
    frappe.db.commit()
    assert frappe.db.count('Vagabond Ho So TT', {'name': ['in', ds]}) == 300
    (goc / 'tai-ho-so.json').write_text(json.dumps({'ten': ds, 'so_ho_so': 300,
        'tu_khoa': 'DO257-HS-', 'tong_tien': 1800000, 'tim_ma': ds[-1]}))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        tao()
    finally:
        frappe.destroy()
