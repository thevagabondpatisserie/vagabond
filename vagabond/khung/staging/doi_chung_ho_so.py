"""Đối chứng server cùng process CI, không phải latency trình duyệt/site thật.

Chỉ thay factory đọc tên trong bộ nhớ process CLI riêng. Hai đường gọi cùng
hàm danh_sach; dữ liệu đầu ra phải trùng toàn bộ. Cache tên được làm nóng
trước đo, thứ tự cũ/mới đảo theo cặp. Không có cửa HTTP hoặc ghi chứng từ.
"""
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
from .van_don_ci import khoa


def chay():
    import frappe
    from vagabond import ho_so_tt as hs
    khoa()
    frappe.set_user('Administrator')
    root = Path(os.environ['VGB_ARTIFACTS'])
    fixture = json.loads((root / 'tai-ho-so.json').read_text())
    factory = hs._bo_doi_ten_trong_luot
    resolver = hs._ten_nguoi
    output = []
    try:
        # Cache nóng như lần tải tiếp theo; không xoá cache của process gateway.
        warm = hs.danh_sach(tu_khoa=fixture['tu_khoa'])
        assert sorted(r['name'] for r in warm['rows']) == sorted(fixture['ten'])
        for pair in range(12):
            results = {}
            for variant in (('cu', 'moi') if pair % 2 == 0 else ('moi', 'cu')):
                # Trước tối ưu mỗi dòng gọi _ten_nguoi trực tiếp, không memo
                # theo request. Cùng resolver giữ nguyên fallback User/Employee.
                hs._bo_doi_ten_trong_luot = (lambda: hs._ten_nguoi) if variant == 'cu' else factory
                start = perf_counter()
                result = hs.danh_sach(tu_khoa=fixture['tu_khoa'])
                ms = (perf_counter() - start) * 1000
                encoded = json.dumps(result, sort_keys=True, default=str, ensure_ascii=False)
                results[variant] = encoded
                rows = result['rows']
                assert sorted(r['name'] for r in rows) == sorted(fixture['ten'])
                for r in rows:
                    expected = fixture['nguoi_tao'][r['name']]
                    assert r['nguoi_tao'] == expected['user'] and r['nguoi_tao_ten'] == expected['name']
                    assert r['tong_tien'] == 6000 and r['trang_thai'] == 'Nhap'
                output.append({'pair': pair, 'variant': variant, 'ms': ms,
                    'rows': len(rows),
                    'result_sha256': hashlib.sha256(encoded.encode()).hexdigest()})
            assert results['cu'] == results['moi'], 'Đối chứng trả dữ liệu khác nhau'
    finally:
        hs._bo_doi_ten_trong_luot = factory
        hs._ten_nguoi = resolver
    (root / 'doi-chung-ho-so.json').write_text(json.dumps({
        'github_event_sha': os.environ.get('GITHUB_SHA'),
        'source_sha256': hashlib.sha256(Path(hs.__file__).read_bytes()).hexdigest(),
        'baseline_reference': '5aefb3e22e748556eaca3f756bb496282cb4d108',
        'metric': 'server danh_sach with warm name cache; not HTTP/UI latency',
        'results': output}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        chay()
    finally:
        frappe.destroy()
