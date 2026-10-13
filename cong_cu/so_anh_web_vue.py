#!/usr/bin/env python3
"""So pixel ảnh fixture và xuất bảng Markdown cho comment PR."""
import argparse
from pathlib import Path

from PIL import Image, ImageChops


def ti_le(a, b):
	x, y = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
	if x.size != y.size:
		return 100.0
	d = ImageChops.difference(x, y).convert('L')
	# Sai khác rất nhỏ của nền trời động không nên biến thành cảnh đổi.
	return 100 * sum(1 for p in d.getdata() if p > 18) / (x.width * x.height)


if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument('main', type=Path)
	ap.add_argument('head', type=Path)
	ap.add_argument('--dich', type=Path, required=True)
	a = ap.parse_args()
	dong = ['| Trang | Cảnh | 390 px | 1440 px |', '|---|---|---:|---:|']
	for tep in sorted(a.head.glob('*-390.png')):
		goc = tep.name[:-8]
		phan = []
		for rong in (390, 1440):
			p = ti_le(a.main / f'{goc}-{rong}.png', a.head / f'{goc}-{rong}.png')
			phan.append(('Đổi' if p >= .05 else 'Không đổi') + f' ({p:.3f}%)')
		trang, canh = goc.split('-', 1)
		if goc.startswith('web-moi-banh-'):
			trang, canh = '/web_moi/banh', goc[len('web-moi-banh-'):]
		else:
			trang, canh = '/banh', goc[len('banh-'):]
		dong.append(f'| {trang} | {canh} | {phan[0]} | {phan[1]} |')
	a.dich.write_text('\n'.join(dong) + '\n')
