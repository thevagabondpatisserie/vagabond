# -*- coding: utf-8 -*-
"""v618: thẻ .card khai display:flex phải ghi rõ hướng; nút .btn trong hàng phải có chiều rộng.

Chị Dễ báo 28/10/2026, màn Hoá đơn hôm nay quầy NVHTN: chữ "16 hoá đơn ·
2.458.528 đ" dựng đứng từng ký tự. Lớp `.card` đổi bản chất hai lần:

  * Bootstrap của Frappe đặt `.card{display:flex;flex-direction:column}`. Thẻ
    khai inline `display:flex` mà không ghi hướng thì thành CỘT.
  * v617 đặt `.card{flex-direction:row}` trong 00-nen.js để chữa các thẻ muốn
    hàng ngang. Thẻ nào lâu nay "đúng nhờ cột" thì vỡ: nút `.btn` có
    width:100% và flex:none chiếm trọn hàng, khối chữ bên cạnh co còn 0 điểm.

Một thẻ đúng hay vỡ tuỳ vào dòng CSS nào thắng là bẫy. Luật chốt ở đây: thẻ
khai display:flex thì ghi rõ flex-direction; nút `.btn` khai flex:none thì
ghi rõ chiều rộng. Đây là ca dò chuỗi để chốt một luật viết; hành vi của màn
đã có ca chạy thật ở hanh_vi/ds_hoa_don_618.js và số đo trên site thật ở PR.
"""

import glob
import os
import re

from vagabond.khung.kiem_thu.nen import ca, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOC, "public", "js", "bep")


def _nguon_noi():
	"""Mã các phần bep/, nối các chuỗi JS viết tách dòng ('...' +\\n '...')."""
	ra = {}
	for p in sorted(glob.glob(os.path.join(BEP, "*.js"))):
		with open(p, encoding="utf-8") as f:
			s = f.read()
		ra[os.path.basename(p)] = re.sub(r"'\s*\+\s*\n\s*'", "", s)
	return ra


def the_flex_thieu_huong(ma):
	"""Thẻ .card có style inline display:flex mà không có flex-direction."""
	thieu = []
	# Thuộc tính khác (data-...) có thể nằm giữa class và style.
	for m in re.finditer(r'class="card[^"]*"[^>]*?\sstyle="([^"]*)"', ma):
		st = m.group(1).replace(" ", "")
		if "display:flex" in st and "flex-direction" not in st:
			thieu.append(m.group(1)[:80])
	return thieu


def nut_flex_none_thieu_rong(ma):
	"""Nút .btn khai flex:none (hoặc flex:0 0 auto) mà không ghi width."""
	thieu = []
	for m in re.finditer(r'<button[^>]*class="btn[^"]*"[^>]*>', ma):
		st = re.search(r'style="([^"]*)"', m.group(0))
		st = (st.group(1) if st else "").replace(" ", "")
		if re.search(r"flex:(none|00auto)", st) and "width:" not in st:
			thieu.append(m.group(0)[:100])
	return thieu


@ca("v618: mọi thẻ .card khai display:flex trong bep/ đều ghi rõ flex-direction")
def _the_ghi_huong():
	thieu = {t: x for t, ma in _nguon_noi().items() for x in [the_flex_thieu_huong(ma)] if x}
	la("thẻ thiếu hướng", thieu, {})


@ca("v618: mọi nút .btn khai flex:none trong bep/ đều ghi rõ chiều rộng")
def _nut_co_rong():
	thieu = {t: x for t, ma in _nguon_noi().items() for x in [nut_flex_none_thieu_rong(ma)] if x}
	la("nút thiếu chiều rộng", thieu, {})


@ca("v618: phép soát bắt đúng ba thẻ đã vỡ ở màn Hoá đơn hôm nay")
def _soat_bat_duoc():
	# Đúng nguyên văn ba thẻ trước bản sửa (main 4437e9c6a), viết tách dòng như cũ.
	cu = (
		"'<div class=\"card\" style=\"padding:11px 13px;background:#fff7ed;border:1px solid #fed7aa;' +\n"
		"      'color:#9a3412;font-size:12.5px;line-height:1.55;display:flex;align-items:center;gap:10px\">' +\n"
		"'<div class=\"card\" style=\"padding:12px 14px;display:flex;align-items:center;gap:8px\">' +\n"
		"'<button class=\"btn\" id=\"posDsChotCa\" style=\"margin:0;padding:9px 11px;font-size:13px;flex:none\">'"
	)
	noi = re.sub(r"'\s*\+\s*\n\s*'", "", cu)
	la("hai thẻ thiếu hướng", len(the_flex_thieu_huong(noi)), 2)
	la("một nút thiếu chiều rộng", len(nut_flex_none_thieu_rong(noi)), 1)
	la("có data- giữa class và style vẫn soát", len(the_flex_thieu_huong(
		'<div class="card" data-pdtong="1" style="display:flex;gap:10px">')), 1)
	la("thẻ đã ghi hướng thì qua", the_flex_thieu_huong(
		'class="card" style="display:flex;flex-direction:column"'), [])
