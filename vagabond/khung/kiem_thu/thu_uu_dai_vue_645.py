# -*- coding: utf-8 -*-
"""v645: mục Ưu đãi trên web Vue dàn lại theo kiểu Tuyển dụng (anh Việt 08/11/2026).

Chạy ca hành vi node (Vue thật, thẻ ERP dựng bằng khuyen_mai.the_web thật) và
chốt mọi tệp ?v= của trang web khớp nội dung sau khi sửa giao diện.
"""

import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@ca("v645 web Vue Ưu đãi: thẻ ảnh gọn, trang chi tiết bốn ô, chép mã, nút đặt bánh đúng luật, ca node đều đạt")
def _vue():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/uu_dai_vue_645.mjs"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= 10)


@ca("v645 web Vue: mã băm ?v= của trang khớp nội dung tệp (vượt cache immutable)")
def _ma_bam():
	r = subprocess.run(["python3", "-B", "cong_cu/ma_bam_web_vue.py", "--kiem"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-800:] + r.stderr[-800:], r.returncode, 0)
