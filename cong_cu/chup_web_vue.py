#!/usr/bin/env python3
"""Chụp các cảnh đặt bánh bằng fixture, tuyệt đối không đọc dữ liệu khách thật.

Workflow chụp viewport thật, giữ nguyên fixed/sticky để phát hiện nút che tổng.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


CANH = ('trang-chu', 'chi-tiet-banh', 'gio-uu-dai', 'gio-giao-hang',
        'gio-tu-lay', 'loi-tai-du-lieu', 'in-store')


def cho_may_chu(cong):
	for _ in range(80):
		try:
			urlopen(f'http://127.0.0.1:{cong}/banh', timeout=.2).read(1)
			return
		except Exception:
			time.sleep(.1)
	raise RuntimeError('Máy chủ fixture không mở được')


def ban_nhap(kieu='ship', ma=''):
	return json.dumps({'luc': int(time.time() * 1000), 'gio': [{
		'k': 'CANDLE', 'img': '', 'id': 'BAWC00139', 'cm': 12,
		'price': 650000, 'nguon': 'today', 'qty': 1, 'wish': '',
		'adds': [], 'dung_cu': {'nia': 0, 'dia': 0}}],
		'ngay': None, 'slot': 6, 'daChonNgay': False, 'daChonGio': False,
		'truong': {'f-ma': ma, 'f-phone': '0900000000', 'f-name': 'Khách fixture', 'f-addr': '12 Nguyễn Huệ, Quận 1'},
		'co': {'mode': kieu, 'pickupId': 'bep-tan-son-hoa', 'pay': 'bank',
			'other': False, 'gift': False, 'vat': False, 'quan': 'Q1', 'nonce': ''}}, ensure_ascii=False)


def mo(page, goc_url, duong, canh):
	page.unroute_all()
	page.route('**/*', lambda r: r.continue_() if r.request.url.startswith(goc_url) else r.abort())
	if canh == 'loi-tai-du-lieu':
		page.route('**/api/method/vagabond.kiem_banh.co_the_ban_hom_nay*',
			lambda route: route.fulfill(status=500, content_type='application/json', body='{"message":{}}'))
		page.route('**/api/method/vagabond.kiem_kho.con_tren_quay_web*',
			lambda route: route.fulfill(status=500, content_type='application/json', body='{"message":{}}'))
	if canh.startswith('gio-'):
		kieu = 'pick' if canh == 'gio-tu-lay' else 'ship'
		ma = 'GIAM10' if canh == 'gio-uu-dai' else ''
		page.add_init_script('sessionStorage.setItem("vgb-gio-v1", ' + json.dumps(ban_nhap(kieu, ma)) + ');')
		duong += '#/gio-hang'
	page.goto(goc_url + duong, wait_until='networkidle')
	page.wait_for_timeout(350)
	page.evaluate("() => document.getAnimations().forEach(a => {a.pause(); a.currentTime=0;})")
	if canh == 'chi-tiet-banh':
		page.evaluate("location.hash='#/banh/candle'")
		page.wait_for_timeout(250)
	elif canh.startswith('gio-'):
		kieu = 'pick' if canh == 'gio-tu-lay' else 'ship'
		ma = 'GIAM10' if canh == 'gio-uu-dai' else ''
		if canh == 'gio-giao-hang':
			page.locator('#f-addr').fill('12 Nguyễn Huệ')
			page.locator('#addrGoiY button').first.click()
			page.wait_for_function("document.querySelector('#sum').innerText.includes('42.000')")
		if ma:
			page.locator('#btnMa').click()
			page.wait_for_timeout(500)
		page.locator('#checkout').wait_for(state='visible')
		page.locator('#sum').scroll_into_view_if_needed()
		page.evaluate("() => { const e=document.querySelector('#checkout'); e.scrollTop=e.scrollHeight; }")

	elif canh in ('in-store', 'loi-tai-du-lieu'):
		page.evaluate("location.hash='#/in-store'")
		page.wait_for_timeout(450)


def chay(goc, dich, cong):
	dich.mkdir(parents=True, exist_ok=True)
	env = dict(os.environ, VGB_GOC=str(goc))
	may_chu = subprocess.Popen([sys.executable, str(Path(__file__).with_name('xem_thu_web_vue.py')), str(cong)],
		env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
	try:
		cho_may_chu(cong)
		with sync_playwright() as p:
			browser = p.chromium.launch()
			for rong in (390, 1440):
				context = browser.new_context(viewport={'width': rong, 'height': 844 if rong == 390 else 1000}, device_scale_factor=1, timezone_id='Asia/Ho_Chi_Minh')
				for duong, ten_ban in (('/banh', 'banh'), ('/web_moi/banh', 'web-moi-banh')):
					for canh in CANH:
						page = context.new_page()
						mo(page, f'http://127.0.0.1:{cong}', duong, canh)
						page.screenshot(path=dich / f'{ten_ban}-{canh}-{rong}.png', full_page=False, animations='disabled')
						page.close()
				context.close()
			browser.close()
	finally:
		may_chu.terminate()
		may_chu.wait(timeout=5)


if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument('--goc', type=Path, default=Path(__file__).resolve().parents[1])
	ap.add_argument('--dich', type=Path, required=True)
	ap.add_argument('--cong', type=int, default=8790)
	a = ap.parse_args()
	chay(a.goc.resolve(), a.dich.resolve(), a.cong)
