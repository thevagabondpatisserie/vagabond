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


@ca('#471 chính sách Vue dựng text node, chỉ link an toàn; chữ có ngoặc Vue không được thực thi')
def _cay_chinh_sach():
	from vagabond.web_vue import cay_chinh_sach
	x = cay_chinh_sach('<p>{{alert(1)}} <a href="javascript:alert(1)" onclick="x()">x</a><strong>Đúng</strong></p>')
	la('text giữ nguyên', x[0]['con'][0], '{{alert(1)}} ')
	la('link bẩn bỏ thuộc tính', x[0]['con'][1]['props'], {})
	la('thẻ định dạng giữ', x[0]['con'][2]['tag'], 'strong')


@ca('#471 SEO đọc nhãn Editor công khai, không lấy nháp, URL canonical cố định')
def _seo():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap
	from vagabond import trang_khach
	import types
	g = {'trang_khach': trang_khach, 'noi_dung_web': types.SimpleNamespace(cong_khai=lambda: {
		'nhan': {'dat_banh_e7c59d5a1': 'Tiêu đề đã xuất bản'},
		'khoi': [{'hien': False, 'anh': '/files/nhap.png', 'tieu_de': 'Nháp'},
			{'hien': True, 'anh': '/files/bia.png', 'tieu_de': 'Bánh', 'noi_dung': 'Mô tả'}]})}
	seo = nap('web_vue.py', 'seo_banh', g)()
	la('nội dung', (seo['title'], seo['description']), ('Tiêu đề đã xuất bản', 'Mô tả'))
	la('ảnh tuyệt đối', seo['image'], 'https://order.thevagabondpatisserie.com/files/bia.png')
	la('canonical', seo['url'], 'https://order.thevagabondpatisserie.com/banh')


@ca('#471 biên nhận Vue token sai trả404, không token không đọc đơn; giữ header riêng tư')
def _bien_nhan_context():
	import types
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach
	from vagabond.www.banh.xong import TIEU_DE
	goi = []
	fr = D(local=D(response_headers={}), sessions=D(get_csrf_token=lambda: 'csrf'),
		form_dict={}, PageDoesNotExistError=ValueError)
	dw = D(PHAP_NHAN={}, lien_he=lambda: {}, pixel_id=lambda: '123',
		bien_nhan_theo_token=lambda tok: goi.append(tok))
	g = {'frappe': fr, 'don_web': dw, 'trang_khach': D(_lien_ket_an_toan=trang_khach._lien_ket_an_toan, json_trong_script=trang_khach.json_trong_script,
		chan_trang_html=lambda *a: ''), 'noi_dung_web': D(chinh_sach_dang_hien=lambda: [], cong_khai=lambda: {}), 'TIEU_DE': TIEU_DE,
		'web_vue': __import__('vagabond.web_vue', fromlist=['x'])}
	fn = nap('www/web_moi/xong.py', 'get_context', g)
	c = fn(D()); la('không token không đọc', goi, [])
	dung('không token', 'khong_token' in c.du_lieu)
	la('referrer', fr.local.response_headers['Referrer-Policy'], 'no-referrer')
	fr.form_dict = {'token': 'sai'}
	try:
		fn(D()); dung('phải404', False)
	except ValueError:
		pass

@ca('#471 đo cửa tồn hiện tại: thường nhận yêu cầu, mùa vụ chặn hạn mức, lỗi kiểm vẫn nhận')
def _do_chinh_sach_ton():
	import sys, types, vagabond
	from vagabond.khung.kiem_thu import thu_don_web_367 as t
	cu = sys.modules.get('vagabond.mua_vu')
	cu_thuoc = getattr(vagabond, 'mua_vu', None)
	try:
		for ten, fn, ok, post in (
			('không hạn mức', lambda *a, **k: [], 1, 1),
			('hết mùa vụ', lambda *a, **k: ['hết'], 0, 0),
			('lỗi phép kiểm', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('fixture')), 1, 1)):
			m = types.SimpleNamespace(kiem_han_muc=fn)
			sys.modules['vagabond.mua_vu'] = m; vagabond.mua_vu = m
			vet, goi = t._moi_truong_tao_don(lambda v: t._Tra(200, {'data': {'id': 'thu'}}))
			la(ten, goi(t._don())['ok'], ok)
			la(ten + ' POST', vet.su.count('post'), post)
	finally:
		if cu is None: sys.modules.pop('vagabond.mua_vu', None)
		else: sys.modules['vagabond.mua_vu'] = cu
		if cu_thuoc is None: delattr(vagabond, 'mua_vu')
		else: vagabond.mua_vu = cu_thuoc

@ca('#471 Pixel và CAPI cùng event_id máy chủ, không bắn Purchase từ biên nhận')
def _pixel_capi_chung_id():
	import subprocess
	from vagabond import don_web
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	b = {'name':'DW-FIXTURE','trang_thai':'Da nhan','tien_banh':650000,
		'event_id_gui_don':'uuid-fixture-server','snapshot':json.dumps({'mon':[{'ma':'BANH','sl':1,'gia':650000}]})}
	g = dict(frappe=D(get_all=lambda *a, **k:[b]), DOCTYPE='Vagabond Don Web',
		token_hop_le=lambda tok:True, bam=don_web.bam, json=json, tom_tat_bien_nhan=don_web.tom_tat_bien_nhan)
	du = nap('don_web.py','bien_nhan_theo_token',g)('token-fixture')
	ev = du['su_kien']
	capi = don_web.goi_su_kien('GuiDon', ev['event_id'], 1, ev['gia_tri'], ev['ma_mon'])
	du['pixel_id']='123'
	code = """
import {bienNhan} from './vagabond/public/web_vue/trang/app.js';
const events=[], storage=new Map();
const win={location:{pathname:'/web_moi/banh/xong/TOKEN'},history:{replaceState(a,b,p){win.location.pathname=p;}},
 sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},fbq:(...x)=>events.push(x)};
const d=JSON.parse(process.argv[1]); bienNhan(d,win); bienNhan(d,win);
console.log(JSON.stringify(events.filter(x=>x[0]==='trackCustom'||x[1]==='Purchase')));
"""
	r = subprocess.run(['node','--input-type=module','-e',code,json.dumps(du)],cwd=str(GOC),text=True,capture_output=True)
	la('node',r.returncode,0)
	x = json.loads(r.stdout)
	la('một GuiDon',len(x),1)
	la('tên',x[0][1],capi['event_name'])
	la('id',x[0][3]['eventID'],capi['event_id'])
	for k in ('value','currency','content_ids','content_type'):
		la(k,x[0][2][k],capi['custom_data'][k])

@ca('#471 cả ba route chính sách chỉ đọc bản công khai, ẩn trả404, giữ đổi ngôn ngữ')
def _ba_chinh_sach():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach, noi_dung_web, web_vue
	for duong in ('chinh-sach-bao-mat','dieu-khoan','giao-hang-doi-tra'):
		fr = D(local=D(request=D(path='/web_moi/'+duong)),form_dict={'ngon_ngu':'en'},
			sessions=D(get_csrf_token=lambda:'csrf'),PageDoesNotExistError=ValueError)
		vet=[]
		nd = D(khoa_tu_duong=noi_dung_web.khoa_tu_duong, chinh_sach_dang_hien=lambda:[],
			trang_chinh_sach=lambda k,n:(vet.append((k,n)) or {'ten':'Chính sách','html':'<p>Published</p>','ngon_ngu':'en','co_en':True}))
		g=dict(frappe=fr,noi_dung_web=nd,web_vue=web_vue,don_web=D(PHAP_NHAN={},lien_he=lambda:{}),
			trang_khach=D(_e=trang_khach._e,json_trong_script=trang_khach.json_trong_script,chan_trang_html=lambda *a:''))
		fn=nap('www/web_moi/chinh_sach.py','get_context',g)
		c=fn(D()); la('ngôn ngữ',vet[0][1],'en'); dung('link quay lại Vue', '/web_moi/'+duong in c.doi_ngon_ngu)
		dung('nội dung công khai','Published' in c.du_lieu)
		nd.trang_chinh_sach=lambda *a:None
		try: fn(D()); dung('ẩn phải404',False)
		except ValueError: pass
