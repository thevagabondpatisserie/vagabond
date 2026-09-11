"""Tổng hợp số đo đủ lượt, giữ mức tải/khổ/cache riêng, không suy ra site nhanh hơn.

Năm lượt chỉ đủ mô tả min/trung vị/max, không dùng để hứa p95 cho production.
Số ms bao gồm thao tác driver và đối chiếu, phải so cùng driver/core/fixture.
"""
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


CA = {
    'van-don': ('so_don', (100, 500), ('mo_ms', 'tim_ms')),
    'kiem-banh': ('so_dong', (50, 200), ('mo_ms',)),
    'ho-so': ('so_ho_so', (1, 300), ('ms',)),
}


def tong_hop(goc):
    sha = json.loads((goc / 'sha.json').read_text())
    for app in ('vagabond', 'frappe', 'erpnext'):
        s = sha.get(app, '')
        if len(s) != 40 or any(c not in '0123456789abcdef' for c in s):
            raise ValueError('Thiếu SHA hợp lệ: ' + app)
    nguon = [json.loads(s) for s in (goc / 'pancake-http.jsonl').read_text().splitlines()]
    if not nguon or any(r.get('ngoai_hop_dong') for r in nguon):
        raise ValueError('Nguồn có lời gọi ngoài hợp đồng hoặc thiếu bằng chứng.')
    ra = []
    for man, (truong, tai, cot) in CA.items():
        rows = json.loads((goc / ('do-' + man + '.json')).read_text())
        if len(rows) != 20 or any(r.get('dat') is not True for r in rows):
            raise ValueError('Thiếu lượt hoặc có lỗi: ' + man)
        da_co = set()
        nhom = defaultdict(list)
        for r in rows:
            k = (r.get('rong'), r.get(truong), r.get('lan'))
            if k[0] not in (390, 1280) or k[1] not in tai or type(k[2]) is not int or k[2] not in range(5) or k in da_co:
                raise ValueError('Trùng/sai khổ, tải hoặc lượt: ' + man)
            da_co.add(k)
            for c in cot:
                v = r.get(c)
                if type(v) not in (float, int) or not math.isfinite(v) or v < 0:
                    raise ValueError('Thời gian không hợp lệ: ' + man + '/' + c)
            nguon = None
            if man == 'kiem-banh':
                nguon = r.get('so_goi_nguon')
                if type(nguon) is not int or nguon < 0:
                    raise ValueError('Thiếu số lần nguồn: ' + man)
            nhom[(k[0], k[1], nguon)].append(r)
        for (rong, so, nguon), ds in sorted(nhom.items()):
            ra.append({'man': man, 'rong': rong, 'tai': so, 'so_goi_nguon': nguon,
                'so_luot': len(ds), 'ms': {c: {
                    'min': min(r[c] for r in ds),
                    'trung_vi': statistics.median(r[c] for r in ds),
                    'max': max(r[c] for r in ds)} for c in cot}})
    return {'sha': sha, 'pham_vi': 'Tải tổng hợp, gồm driver/đối chiếu; chưa là nghiệm thu hiệu năng site',
            'nhom': ra}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Cần thư mục artifact làm đối số duy nhất.')
    goc = Path(sys.argv[1])
    ket = tong_hop(goc)
    (goc / 'tong-hop-do.json').write_text(json.dumps(ket, ensure_ascii=False, indent=2))
    print(json.dumps(ket, ensure_ascii=False))
