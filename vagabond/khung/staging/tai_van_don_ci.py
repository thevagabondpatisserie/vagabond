"""Tải tổng hợp 100/500 vận đơn để đo màn, không sao chép đơn của khách.

Chạy sau năm ca nghiệp vụ để giữ bằng chứng đồng bộ độc lập. Đây là hai
mức tải thử, chưa nhận là phân bố thực tế của site. Không tạo pancake_id,
không ghi sổ kho/kế toán hoặc gọi nguồn bên ngoài.
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
    goc = Path(os.environ['VGB_ARTIFACTS'])
    sx = json.loads((goc / 'san-xuat-fixture.json').read_text())
    bang = []
    for buoc, so in enumerate((100, 500)):
        ngay = str(add_days(nowdate(), 3700 + buoc))
        if frappe.db.count('Van Don', {'ngay_giao': ngay}):
            raise RuntimeError('Ngày đo đã có dữ liệu; cần bench mới.')
        ds = []
        for i in range(so):
            ma = 'DO257-%s-%04d' % (so, i)
            d = frappe.get_doc({'doctype': 'Van Don', 'ngay_giao': ngay,
                'ma_don': ma, 'trang_thai': 'Chờ giao', 'kenh': 'Shipper nội bộ',
                'khach': 'Khách thử ' + ma, 'dia_chi': 'Địa chỉ tổng hợp ' + str(i),
                'tien_thu_ho': 100000 + i * 1000, 'thu_tu': i})
            for j in range(3):
                d.append('mon', {'ma_hang': sx['banh'], 'ten': 'Bánh thử %s' % j,
                    'so_luong': j + 1})
            d.insert()
            ds.append(d.name)
        # Commit một lần: lỗi giữa chừng không để ngày đo nửa bộ.
        frappe.db.commit()
        if frappe.db.count('Van Don', {'ngay_giao': ngay}) != so:
            raise RuntimeError('Số vận đơn sau dựng khác tải đã chọn.')
        if frappe.db.count('Van Don Mon', {'parent': ['in', ds]}) != so * 3:
            raise RuntimeError('Số dòng món không đủ.')
        bang.append({'ngay': ngay, 'so_don': so, 'so_mon': so * 3,
            'ten': ds, 'tim_ma': 'DO257-%s-%04d' % (so, so - 1)})
    (goc / 'tai-van-don.json').write_text(json.dumps(bang))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        tao()
    finally:
        frappe.destroy()
