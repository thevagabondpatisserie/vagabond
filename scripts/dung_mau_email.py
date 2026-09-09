#!/usr/bin/env python3
"""Dựng toàn bộ mẫu email để bắt lại lỗi Outlook mobile tràn ngang (#249).

Chỉ xuất HTML/ảnh local, không gửi email. Có thể so với mã nguồn cũ bằng
--nguon /tmp/thu_khung_truoc_249.py. Chạy từ bất kỳ thư mục nào.
"""
import argparse
import base64
import importlib.util
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GOC))
from vagabond import thu_khung as tk


def dung(thu, dich):
    dich.mkdir(parents=True, exist_ok=True)
    mau = {ma: thu.dung_thu_mau(ma)[1] for ma, _, _ in thu.MAU_THU}
    dai = 'MA' + '0123456789' * 15
    than = (thu.cap([('Địa chỉ email người phụ trách', dai + '@thevagabondpatisserie.com')])
            + thu.bang([('Hoá đơn', 'left'), ('Số tiền', 'right')], [[dai, '123.456.789.012 đ']], tong=('Tổng thanh toán', '123.456.789.012 đ'))
            + thu.o_kem(dai) + thu.o_canh_bao(dai) + thu.doan(dai))
    mau['chu_dai'] = thu.khung_thuan(dai, than, nut_html=thu.nut('https://example.com', dai))
    for ma, html in mau.items():
        for anh in ('dau.png', 'lot-xanh.png', 'lot-kem.png'):
            # Chỉ preview: nhúng ảnh để kiểm offline, không đổi URL email thật.
            du_lieu = base64.b64encode((GOC / 'vagabond/public/images/thu' / anh).read_bytes()).decode()
            html = html.replace('/assets/vagabond/images/thu/' + anh, 'data:image/png;base64,' + du_lieu)
        (dich / (ma + '.html')).write_text('<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="margin:0">' + html + '</body></html>', encoding='utf-8')
    print('%d mẫu: %s' % (len(mau), dich))


if __name__ == '__main__':
    bo_doc = argparse.ArgumentParser(description=__doc__)
    bo_doc.add_argument('dich', type=Path)
    bo_doc.add_argument('--nguon', type=Path)
    args = bo_doc.parse_args()
    if args.nguon:
        spec = importlib.util.spec_from_file_location('thu_cu', args.nguon)
        tk = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tk)
    dung(tk, args.dich)
