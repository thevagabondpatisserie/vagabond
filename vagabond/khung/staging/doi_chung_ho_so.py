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
    goc = Path(os.environ['VGB_ARTIFACTS'])
    du_lieu = json.loads((goc / 'tai-ho-so.json').read_text())
    tao_bo_doi = hs._bo_doi_ten_trong_luot
    doi_ten = hs._ten_nguoi
    dau_ra = []
    try:
        # Cache nóng như lần tải tiếp theo; không xoá cache của process gateway.
        da_nap = hs.danh_sach(tu_khoa=du_lieu['tu_khoa'])
        assert sorted(dong['name'] for dong in da_nap['rows']) == sorted(du_lieu['ten'])
        for cap in range(12):
            cac_ket_qua = {}
            for bien_the in (('cu', 'moi') if cap % 2 == 0 else ('moi', 'cu')):
                # Trước tối ưu mỗi dòng gọi _ten_nguoi trực tiếp, không memo
                # theo request. Cùng resolver giữ nguyên fallback User/Employee.
                hs._bo_doi_ten_trong_luot = (lambda: hs._ten_nguoi) if bien_the == 'cu' else tao_bo_doi
                bat_dau = perf_counter()
                ket_qua = hs.danh_sach(tu_khoa=du_lieu['tu_khoa'])
                mili_giay = (perf_counter() - bat_dau) * 1000
                ma_hoa = json.dumps(ket_qua, sort_keys=True, default=str, ensure_ascii=False)
                cac_ket_qua[bien_the] = ma_hoa
                cac_dong = ket_qua['rows']
                assert sorted(dong['name'] for dong in cac_dong) == sorted(du_lieu['ten'])
                for dong in cac_dong:
                    mong_doi = du_lieu['nguoi_tao'][dong['name']]
                    assert dong['nguoi_tao'] == mong_doi['user'] and dong['nguoi_tao_ten'] == mong_doi['name']
                    assert dong['tong_tien'] == 6000 and dong['trang_thai'] == 'Nhap'
                dau_ra.append({'pair': cap, 'variant': bien_the, 'ms': mili_giay,
                    'rows': len(cac_dong),
                    'result_sha256': hashlib.sha256(ma_hoa.encode()).hexdigest()})
            assert cac_ket_qua['cu'] == cac_ket_qua['moi'], 'Đối chứng trả dữ liệu khác nhau'
    finally:
        hs._bo_doi_ten_trong_luot = tao_bo_doi
        hs._ten_nguoi = doi_ten
    (goc / 'doi-chung-ho-so.json').write_text(json.dumps({
        'github_event_sha': os.environ.get('GITHUB_SHA'),
        'source_sha256': hashlib.sha256(Path(hs.__file__).read_bytes()).hexdigest(),
        'baseline_reference': '5aefb3e22e748556eaca3f756bb496282cb4d108',
        'metric': 'server danh_sach with warm name cache; not HTTP/UI latency',
        'results': dau_ra}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import frappe
    frappe.init(site='bench-ci.localhost', sites_path=str(Path.cwd()))
    frappe.connect()
    try:
        chay()
    finally:
        frappe.destroy()
