"""Web bản Vue (anh Việt chốt 11/10/2026): chốt những thứ dễ quên khi dựng lại
web khách bằng Vue mà vẫn chạy song song với trang cũ.

- Ca hành vi kho trang đặt bánh chạy THẬT bằng node (hanh_vi/web_vue_banh.mjs).
- Mã băm ?v= và import map khớp nội dung tệp (cache immutable #310).
- Chữ marketing không bao giờ thành HTML: không v-html, không innerHTML.
- Mọi khoá chữ dùng trong web Vue đều có trong sổ nhãn, chữ mặc định trùng
  sổ nhãn, để trình biên tập sửa được và trang chưa tải nhãn vẫn đúng câu.
- Trang www mới đặt mô đun Python bằng gạch dưới (bài học v529).
Không cần Frappe, không cần mạng.
"""
import ast
import json
import re
import subprocess
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]
VUE = GOC / 'vagabond/public/web_vue'


def _nguon():
	return [p for p in sorted(VUE.rglob('*.js')) if '/lib/' not in p.as_posix()]


def _so_nhan():
	cay = ast.parse((GOC / 'vagabond/noi_dung_web.py').read_text())
	nhan = {}
	for n in cay.body:
		if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'NHAN' for x in n.targets):
			nhan = ast.literal_eval(n.value)
	nhan.update(json.loads((GOC / 'vagabond/public/web_order/chu-mac-dinh.json').read_text()))
	return nhan


@ca('Web Vue: ca hành vi kho trang đặt bánh chạy thật bằng node đều đạt')
def _hanh_vi():
	r = subprocess.run(['node', 'vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs'], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	dung('đủ số ca', re.search(r'(\d+) ca dat, 0 ca hong', r.stdout) and int(re.search(r'(\d+) ca dat', r.stdout).group(1)) >= 16)


@ca('Web Vue: mã băm ?v= và import map khớp nội dung tệp')
def _ma_bam():
	r = subprocess.run(['python3', 'cong_cu/ma_bam_web_vue.py', '--kiem'], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout + r.stderr, r.returncode, 0)
	trang = (GOC / 'vagabond/www/web_moi/banh.html').read_text()
	for p in VUE.rglob('*.js'):
		dung('import map có ' + p.name, '/assets/vagabond/web_vue/' + p.relative_to(VUE).as_posix() + '?v=' in trang)
	dung('không còn ?v=0', '?v=0"' not in trang)


@ca('Web Vue: chữ người soạn không thành HTML (không v-html, không innerHTML)')
def _khong_html():
	for p in _nguon():
		# Bỏ chú thích: lời giải thích "không dùng v-html" không phải là dùng.
		s = re.sub(r'/\*.*?\*/', '', p.read_text(), flags=re.S)
		s = re.sub(r'(?m)^\s*//.*$', '', s)
		for mau in ('v-html', 'innerHTML', 'outerHTML', 'insertAdjacentHTML', 'document.write'):
			dung(p.name + ' không dùng ' + mau, mau not in s)


@ca('Web Vue: mọi khoá chữ có trong sổ nhãn, chữ mặc định trùng sổ nhãn')
def _khoa_chu():
	nhan = _so_nhan()
	so = 0
	for p in _nguon():
		s = p.read_text()
		for k, d in re.findall(r"\bt\(\s*'([a-z0-9_]+)'\s*,\s*'((?:[^'\\]|\\.)*)'", s):
			so += 1
			dung(p.name + ' có khoá ' + k, k in nhan)
			chu = d.replace('\\\\n', '\n').replace('\\n', '\n').replace("\\'", "'")
			la(p.name + ' mặc định ' + k, chu, nhan[k]['mac_dinh'])
	dung('dò được khoá', so > 150)


@ca('Web Vue: trang www mới có mô đun gạch dưới, có CSRF và không cache')
def _trang_www():
	thu = GOC / 'vagabond/www/web_moi'
	dung('có __init__', (thu / '__init__.py').exists())
	for html in thu.glob('*.html'):
		py = thu / (html.stem.replace('-', '_') + '.py')
		dung(html.name + ' có ' + py.name, py.exists())
		s = py.read_text()
		dung(py.name + ' đặt csrf', 'context.csrf_token' in s and 'no_cache = 1' in s)
		dung(html.name + ' có thẻ csrf', '<meta name="csrf-token" content="{{ csrf_token }}">' in html.read_text())


@ca('Codex #462: link #/banh/<bánh> chưa thấy bánh thì CHỈ về trang chủ khi đã hỏi tồn xong (dò chuỗi vì app.js cần DOM; hành vi đã kiểm bằng Chromium, xem PR #462)')
def _link_banh_cho_ton():
	s = (VUE / 'banh/app.js').read_text()
	la('lối về trang chủ khi không thấy bánh có điều kiện tonDaThu', s.count("if (!c) { if (S.tonDaThu) nav('#/', true); return; }"), 1)
	dung('không còn lối về trang chủ vô điều kiện', "if (!c) { nav('#/', true); return; }" not in s)
	dung('nạp tồn xong thì mở lại đường dẫn bánh', 'kho.napTon().then(apDuongDanNeuBanh)' in s)


@ca('Web Vue: node CI tay không chạy được mô đun ES (package.json type module)')
def _kieu_mo_dun():
	d = json.loads((VUE / 'package.json').read_text())
	la('type', d.get('type'), 'module')
	dung('Vue có giấy phép MIT ở đầu tệp', '@license MIT' in (VUE / 'lib/vue.esm-browser.prod.js').read_text()[:200])
