#!/usr/bin/env python3
"""Soạn thông báo sau deploy theo mẫu chung, chỉ xuất tệp để xem/duyệt.

Chạy từ repo: python3 .agents/skills/vagabond-email-phat-hanh/scripts/soan_thu.py
noi_dung.json thu.html. JSON gồm tieu_de, mo_dau, cac_y (danh sách chuỗi),
site (URL HTTPS đã xác minh), ket (tuỳ chọn). Không đọc người nhận hoặc gửi thư.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path.cwd()))
from vagabond import thu_khung as tk


def soan(du_lieu):
    """Chỉ nhận văn bản; thoát HTML trước khi đưa vào mẫu branding."""
    site = du_lieu['site'].rstrip('/')
    dia_chi = urlsplit(site)
    if dia_chi.scheme != 'https' or not dia_chi.netloc or dia_chi.username or dia_chi.password or dia_chi.query or dia_chi.fragment or dia_chi.path:
        raise ValueError('site phải là địa chỉ gốc HTTPS, không có đường dẫn hoặc thông tin đăng nhập.')
    tieu_de, mo_dau = du_lieu['tieu_de'], du_lieu['mo_dau']
    cac_y = du_lieu['cac_y']
    if not isinstance(cac_y, list) or not 1 <= len(cac_y) <= 5 or not all(isinstance(y, str) and y.strip() for y in cac_y):
        raise ValueError('Cần từ 1 tới 5 ý bằng văn bản.')
    ket = du_lieu.get('ket', '')
    than = tk.doan(tk.h(mo_dau)) + ''.join(tk.o_kem(tk.h(y), goc_anh=site) for y in cac_y)
    if ket:
        than += tk.doan(tk.h(ket))
    html = tk.khung_thuan(tieu_de, than, nut_html=tk.nut(site + '/bep', 'Mở app', goc_anh=site), chan='nhan_vien', nhan='Cập nhật hệ thống', goc_anh=site)
    chu = '\n\n'.join([tieu_de, mo_dau, *('- ' + y for y in cac_y), ket, 'Mở app: ' + site + '/bep', tk.HO_TRO_APP])
    return html, chu


if __name__ == '__main__':
    bo_doc = argparse.ArgumentParser(description=__doc__)
    bo_doc.add_argument('noi_dung', type=Path)
    bo_doc.add_argument('html', type=Path)
    args = bo_doc.parse_args()
    html, chu = soan(json.loads(args.noi_dung.read_text(encoding='utf-8')))
    args.html.write_text(html, encoding='utf-8')
    args.html.with_suffix('.txt').write_text(chu, encoding='utf-8')
