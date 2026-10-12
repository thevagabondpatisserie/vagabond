#!/usr/bin/env python3
"""Đóng dấu mã băm cho mô đun và CSS của web bản Vue.

Site trả /assets với cache immutable (#310): tệp đổi nội dung mà URL không
đổi thì khách cũ không bao giờ thấy bản mới. Trang cũ ghi tay ?v=<băm> cho
từng thẻ link/script. Web bản Vue có nhiều mô đun ES nạp lẫn nhau bằng
`import './x.js'`, chỗ đó không gắn được ?v=, nên dùng IMPORT MAP: trang
khai bảng ánh xạ từng URL mô đun sang URL có ?v=<băm>, trình duyệt tự đổi.

Cách dùng:
    python3 cong_cu/ma_bam_web_vue.py          ghi lại bảng và ?v= trong các trang
    python3 cong_cu/ma_bam_web_vue.py --kiem   chỉ kiểm, lệch thì mã trả về 1

Ca kiểm thu_web_vue.py gọi --kiem, nên quên chạy là CI đỏ.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
THU_MUC = GOC / 'vagabond/public/web_vue'
TIEN_TO = '/assets/vagabond/web_vue/'
TRANG = [GOC / 'vagabond/www/web_moi/banh.html']
DAU, CUOI = '<!-- vue-map:dau -->', '<!-- vue-map:cuoi -->'


def bam(p):
	return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def bang_anh_xa():
	ra = {}
	for p in sorted(THU_MUC.rglob('*.js')):
		duong = TIEN_TO + p.relative_to(THU_MUC).as_posix()
		ra[duong] = duong + '?v=' + bam(p)
	return ra


def khoi_map():
	noi = json.dumps({'imports': bang_anh_xa()}, ensure_ascii=False, indent=1)
	return DAU + '\n<script type="importmap">\n' + noi + '\n</script>\n' + CUOI


def dong_dau(s):
	s = re.sub(re.escape(DAU) + r'.*?' + re.escape(CUOI), lambda m: khoi_map(), s, flags=re.S)

	def thay(m):
		duong = m.group(1)
		p = THU_MUC / duong[len(TIEN_TO):]
		return duong + '?v=' + bam(p) if p.exists() else m.group(0)
	return re.sub(r'(' + re.escape(TIEN_TO) + r'[A-Za-z0-9_./-]+\.(?:css|js))\?v=[0-9a-f]+', thay, s)


def main():
	kiem = '--kiem' in sys.argv
	lech = []
	for trang in TRANG:
		cu = trang.read_text()
		moi = dong_dau(cu)
		if cu != moi:
			lech.append(str(trang.relative_to(GOC)))
			if not kiem:
				trang.write_text(moi)
	if kiem and lech:
		print('Mã băm web Vue lệch, chạy python3 cong_cu/ma_bam_web_vue.py:', ', '.join(lech))
		return 1
	print('Đã đóng dấu' if not kiem else 'Mã băm web Vue khớp', len(TRANG), 'trang')
	return 0


if __name__ == '__main__':
	sys.exit(main())
