#!/usr/bin/env python3
"""Rà mọi nút trên các trang khách bằng Chromium thật, ở 390 px và 1440 px.

v598 (16/10/2026): nút "Gửi yêu cầu đặt bánh" bị co thành viên tròn khi có
dòng báo lỗi, vì dòng báo nằm chung hàng flex với nút. Công cụ này tìm đúng
kiểu lỗi đó ở MỌI nút, không chỉ nút gửi:

  - nút hẹp hơn bề rộng chữ của chính nó (bị flex ép co);
  - vùng bấm dưới 44 px (AGENTS.md điều 13);
  - chữ tràn khỏi nút;
  - trang cuộn ngang.

Mỗi trang chụp hai lần: bình thường, và sau khi nhét một câu báo lỗi dài vào
mọi ô thông báo ([role=status], [aria-live], các ô *Hint, .thong-bao) để giả
lập lúc trang báo lỗi. Đây là phép thử chịu tải bố cục, không phải chuỗi thao
tác của khách; chuỗi thao tác thật nằm ở ca kiểm riêng.

Chỉ dùng fixture localhost (cong_cu/xem_thu_web_vue.py), chặn mọi mạng ngoài,
không đọc dữ liệu khách thật. Trả mã 1 nếu có vi phạm.

    python3 cong_cu/ra_nut_web.py [--anh /tmp/anh-nut] [--json /tmp/ra-nut.json]
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chup_web_vue import ban_nhap, cho_may_chu  # noqa: E402

GOC = Path(__file__).resolve().parents[1]

LOI_DAI = ("Chưa gửi được đơn. Hệ thống bán hàng của chúng tôi từ chối đơn này. Quý khách "
	"nhắn qua Messenger, hoặc bấm gửi lại sau ít phút.")

# Trang dựng bằng Jinja ở máy chủ: dựng tạm bằng jinja2, giá trị trống thành
# chữ mẫu để có độ dài thật.
TRANG_WWW = {
	'/dat-ban': ('vagabond/www/dat-ban.html', ['#dat-ban']),
	'/thanh-vien': ('vagabond/www/thanh-vien.html', ['#dang-nhap', '#ho-so', '#xac-thuc']),
	'/chinh-sach-bao-mat': ('vagabond/www/chinh-sach.html', []),
	'/banh/xong/thu': ('vagabond/www/banh/xong.html', []),
}

CAU_HINH_DAT_BAN = {'bat': 1, 'ten_co_so': 'Cửa hàng Sài Gòn', 'dia_chi': '9 Trần Cao Vân, P. Sài Gòn', 'hom_nay': '2026-10-17',
	'toi_da_khach': 20, 'dip': ['Sinh nhật', 'Kỷ niệm', 'Gặp gỡ công việc'], 'khu_vuc': ['Trong nhà', 'Ngoài trời', 'Bàn ghế cao'],
	'khung_gio': ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00']}

JS_DO = r"""(nguong) => {
  const ra = [];
  const hien = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const ten = e => (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).slice(0,2).join('.') : '') + ' "' + (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\s+/g,' ').slice(0,40) + '"';
  const ds = [...document.querySelectorAll('button, a.btn, a.tab, nav a, [role=button], input[type=submit]')].filter(hien);
  for (const e of ds) {
    const r = e.getBoundingClientRect();
    // Nút nằm khuất ngoài khung đang xem theo chiều ngang (băng cuộn ngang có chủ ý) thì bỏ qua đo co.
    const chu = (e.innerText || '').trim();
    if (chu && e.parentElement) {
      // Bị ép co: cho nút rộng bằng hàng chứa nó thì chữ nằm gọn (thấp hơn hẳn),
      // còn hiện tại nút hẹp và cao vọt vì chữ phải xuống dòng từng chữ một.
      // Đo tại chỗ để giữ nguyên ngữ cảnh CSS, đo xong trả lại kiểu cũ.
      const cha = e.parentElement.getBoundingClientRect().width;
      const cu = e.getAttribute('style');
      e.style.setProperty('flex', 'none', 'important'); e.style.setProperty('width', cha + 'px', 'important');
      e.style.setProperty('max-width', 'none', 'important'); e.style.setProperty('align-self', 'flex-start', 'important');
      e.style.setProperty('height', 'auto', 'important');
      const cao_rong = e.getBoundingClientRect().height;
      if (cu === null) e.removeAttribute('style'); else e.setAttribute('style', cu);
      if (r.height > cao_rong * 1.5 + 2 && r.width < cha * 0.6)
        ra.push({loai: 'nut_bi_ep', nut: ten(e), rong: Math.round(r.width), cao: Math.round(r.height), cao_khi_du_rong: Math.round(cao_rong)});
    }
    if (e.scrollWidth > e.clientWidth + 2 && getComputedStyle(e).overflowX !== 'auto') ra.push({loai: 'chu_tran', nut: ten(e)});
    const nho = Math.min(r.width, r.height);
    if (nho < nguong - 0.5 && !e.closest('[data-cho-phep-nho]')) ra.push({loai: 'vung_bam_nho', nut: ten(e), rong: Math.round(r.width), cao: Math.round(r.height)});
  }
  const tt = document.getElementById('trang-thai');
  if (tt && tt.classList.contains('loi')) { const r = tt.getBoundingClientRect();
    if (r.bottom < 0 || r.top > innerHeight) ra.push({loai: 'bao_loi_ngoai_khung_nhin', top: Math.round(r.top), cao_khung: innerHeight}); }
  const cuon = document.documentElement.scrollWidth - document.documentElement.clientWidth;
  if (cuon > 1) ra.push({loai: 'trang_cuon_ngang', du: cuon});
  return {so_nut: ds.length, loi: ra};
}"""

JS_BAO_LOI = r"""(loi) => {
  const o = new Set([...document.querySelectorAll('[role=status], [aria-live], [id$=Hint], [id$=hint], .thong-bao, #sendHint')]);
  o.forEach(e => { e.hidden = false; e.innerHTML = '<b>' + loi.split('.')[0] + '.</b> ' + loi.split('.').slice(1).join('.'); });
  return o.size;
}"""


def dung_www(tep, hien):
	from jinja2 import ChainableUndefined, Environment
	moi = Environment(undefined=ChainableUndefined, autoescape=False)
	s = (GOC / tep).read_text()
	mau = {'csrf_token': 'thu', 'tieu_de': 'Chính sách bảo mật', 'than': '<h1>Chính sách bảo mật thông tin</h1>' + '<p>Nội dung mẫu.</p>' * 6,
		'doi_ngon_ngu': '<a href="#">English</a>', 'chan_trang': '', 'du_lieu': '{}',
		'nhan': {'dat_ban_nhan': 'ĐẶT BÀN', 'dat_ban_tieu_de': 'Đặt bàn tại Vagabond', 'dat_ban_mo_ta': 'Chọn chi nhánh, ngày và giờ.',
			'dat_ban_dong': 'Tạm ngưng nhận đặt bàn.', 'dat_ban_nut': 'Gửi yêu cầu đặt bàn', 'dat_ban_ho_tro': 'Cần hỗ trợ?'}}
	html = moi.from_string(s).render(**mau)
	for sel in hien:
		html = html.replace('id="%s" ' % sel[1:], 'id="%s" data-ra-hien ' % sel[1:])
	return html


def mo_canh(page, url, canh):
	page.unroute_all()
	page.route('**/*', lambda r: r.continue_() if r.request.url.startswith(url) else r.abort())
	if canh.startswith('www:'):
		duong, _, buoc = canh[4:].partition('#')
		tep, hien = TRANG_WWW[duong]
		html = dung_www(tep, hien)
		page.route(url + duong, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=html))
		page.route('**/api/method/vagabond.dat_ban.cau_hinh*', lambda r: r.fulfill(status=200, content_type='application/json',
			body=json.dumps({'message': CAU_HINH_DAT_BAN}, ensure_ascii=False)))
		page.goto(url + duong, wait_until='networkidle')
		page.wait_for_timeout(300)
		if buoc == 'loi':
			# Khách điền tên, số rồi bấm Gửi ở cuối trang mà quên chọn giờ: dòng báo phải lọt vào khung nhìn.
			page.locator('#ten').fill('Khách fixture')
			page.locator('#sdt').fill('0900000000')
			page.locator('#gui').scroll_into_view_if_needed()
			page.locator('#gui').click()
			page.wait_for_timeout(900)
		else:
			page.evaluate("() => document.querySelectorAll('[data-ra-hien]').forEach(e => e.hidden = false)")
		return
	ban, con = canh.split(':', 1)
	duong = '/web_moi/banh' if ban == 'vue' else '/banh'
	if con == 'gui-loi':
		page.route('**/api/method/vagabond.don_hang.tao_don*', lambda r: r.fulfill(status=200, content_type='application/json',
			body=json.dumps({'message': {'ok': 0, 'ly_do': 'pancake_tu_choi'}})))
	if con.startswith('gio') or con == 'gui-loi':
		page.add_init_script('sessionStorage.setItem("vgb-gio-v1", ' + json.dumps(ban_nhap('pick' if con in ('gio-tu-lay', 'gui-loi') else 'ship')) + ');')
		duong += '#/gio-hang'
	page.goto(url + duong, wait_until='networkidle')
	page.wait_for_timeout(350)
	if con == 'chi-tiet':
		page.evaluate("location.hash='#/banh/candle'")
		page.wait_for_timeout(300)
	elif con == 'in-store':
		page.evaluate("location.hash='#/in-store'")
		page.wait_for_timeout(400)
	elif con == 'gui-loi':
		# Đúng chuỗi khách gặp ngày 16/10: chọn ngày, giờ, đồng ý, bấm gửi; máy chủ trả "chưa gửi được".
		# Chọn theo vị trí, không theo chữ ngày: CI chạy ngày nào cũng có ngày thứ ba và một khung giờ còn mở.
		page.locator('#c-days button').nth(2).click()
		page.locator('#c-slots button:not([disabled])').first.click()
		page.locator('#c-dongy').scroll_into_view_if_needed()
		page.locator('#c-dongy').click()
		page.locator('#btnSend').click()
		page.wait_for_function("document.querySelector('#sendHint').innerText.length > 10")
	elif con == 'huong-size':
		page.evaluate("location.hash='#/banh/candle'")
		page.wait_for_timeout(300)
		if page.locator('#s-huongsize').count():
			page.locator('#s-huongsize').click()
			page.wait_for_timeout(200)


CANH = ['cu:trang-chu', 'cu:chi-tiet', 'cu:huong-size', 'cu:in-store', 'cu:gio-giao', 'cu:gio-tu-lay', 'cu:gui-loi',
	'vue:trang-chu', 'vue:chi-tiet', 'vue:huong-size', 'vue:gio-giao', 'vue:gui-loi',
	'www:/dat-ban', 'www:/dat-ban#loi', 'www:/thanh-vien', 'www:/chinh-sach-bao-mat', 'www:/banh/xong/thu']


def chay(cong, anh, nguong=44, chi=None):
	env = dict(os.environ, VGB_GOC=str(GOC))
	may = subprocess.Popen([sys.executable, str(GOC / 'cong_cu/xem_thu_web_vue.py'), str(cong)], env=env,
		stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
	ket = []
	try:
		cho_may_chu(cong)
		url = 'http://127.0.0.1:%d' % cong
		with sync_playwright() as p:
			trinh = p.chromium.launch()
			for rong in (390, 1440):
				ctx = trinh.new_context(viewport={'width': rong, 'height': 844 if rong == 390 else 1000}, timezone_id='Asia/Ho_Chi_Minh')
				for canh in [c for c in CANH if not chi or any(c.startswith(x) for x in chi)]:
					for co_loi in (False, True):
						page = ctx.new_page()
						try:
							mo_canh(page, url, canh)
							so_o = page.evaluate(JS_BAO_LOI, LOI_DAI) if co_loi else 0
							page.wait_for_timeout(100)
							kq = page.evaluate(JS_DO, nguong)
							ten = '%s-%s-%d' % (canh.replace(':', '_').replace('/', '_'), 'baoloi' if co_loi else 'thuong', rong)
							if anh:
								page.screenshot(path=str(Path(anh) / (ten + '.png')), full_page=True)
							ket.append({'canh': canh, 'rong': rong, 'bao_loi': co_loi, 'o_bao': so_o, **kq})
						except Exception as e:
							ket.append({'canh': canh, 'rong': rong, 'bao_loi': co_loi, 'so_nut': 0, 'loi': [{'loai': 'khong_mo_duoc', 'chi_tiet': str(e)[:200]}]})
						finally:
							page.close()
				ctx.close()
			trinh.close()
	finally:
		may.terminate()
		may.wait(timeout=5)
	return ket


if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument('--cong', type=int, default=8796)
	ap.add_argument('--anh', default='')
	ap.add_argument('--json', default='')
	ap.add_argument('--canh', action='append', help='chỉ chạy cảnh bắt đầu như vậy, ví dụ --canh vue:')
	a = ap.parse_args()
	if a.anh:
		Path(a.anh).mkdir(parents=True, exist_ok=True)
	ket = chay(a.cong, a.anh, chi=a.canh)
	tong = 0
	for k in ket:
		for l in k['loi']:
			tong += 1
			print('%-26s %4d %-6s %s' % (k['canh'], k['rong'], 'baoloi' if k['bao_loi'] else '', json.dumps(l, ensure_ascii=False)))
	print('Tổng: %d con, %d nút đã đo, %d vi phạm.' % (len(ket), sum(k['so_nut'] for k in ket), tong))
	if a.json:
		Path(a.json).write_text(json.dumps(ket, ensure_ascii=False, indent=1))
	sys.exit(1 if tong else 0)
