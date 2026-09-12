"""#266: gọi hai nhịp thật, tách ghi sổ và phát hành khi còn nợ ngày cũ."""
import ast
from html import escape
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS
from vagabond.khung.kiem_thu.nen import ca, la, dung
SRC = Path(__file__).resolve().parents[2] / 'ban_hang.py'

class D(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


@ca('#266 hook production chịu cờ hoãn, trả cờ và vẫn xuất khi được phép')
def hook_sau_ghi_so():
	from vagabond import minvoice_sau_ghi_so as sau
	from vagabond.minvoice_kich_ban import bam
	la('snapshot khớp production', bam(sau.ban_goc()), sau.BAM_GOC)
	for cho_xuat in (False, True):
		gui = []
		st = D(nguon='Pancake', enabled=1, tu_xuat_khi_ghi_so=1)
		f = NS(form_dict={}, response={'message': {'tao_ok': 1}},
			utils=NS(cint=lambda x: int(x or 0), flt=float, today=lambda: '2026-09-12', date_diff=lambda *a: 0),
			db=NS(commit=lambda: None, get_value=lambda *a: 'ID-GIA'))
		f.get_doc = lambda dt, ten=None: st if dt == 'MInvoice Phat Hanh Settings' else NS(execute_method=lambda: gui.append('hook'))
		si = D(name='SI-THU', custom_nguon='Pancake', posting_date='2026-09-12', grand_total=80000, flags=D())
		si.submit = lambda: exec(compile(sau.ban_moi(), 'hook-production', 'exec'), {'frappe': f, 'doc': si})
		g = dict(frappe=f, _chuan_bi_ghi_so=lambda *a: None, _tu_xuat_hddt=lambda *a: (True, ''))
		la('kết quả ghi sổ', nap('_ghi_so_mot_don', g)(si, cho_xuat=cho_xuat), (1, int(cho_xuat), ''))
		la('hook chỉ gọi khi cho phép', gui, ['hook'] if cho_xuat else [])
		la('trả lại cờ nội bộ', si.flags.get('vgb_hoan_phat_hanh'), None)

def nap(name, g):
	fn = next((n for n in ast.parse(SRC.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == name))
	exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SRC), 'exec'), g)
	return g[name]


@ca('#266 đếm đúng nguồn quầy, giữ nợ chưa rõ và tổng tiền cùng tập')
def dem_no_doc_lap():
	from vagabond import hddt_cho_xuat as pure
	rows = [D(name='DUNG', custom_nguon='Pancake', vgb_quay=''),
		D(name='NVHTN', custom_nguon='Pancake', vgb_quay='NVHTN'),
		D(name='NGUON-KHAC', custom_nguon='Khác', vgb_quay=''),
		D(name='DA-CO', custom_nguon='Pancake', vgb_quay='', custom_hddt_id='ID'),
		D(name='CHUA-RO', custom_nguon='Pancake', vgb_quay='', vgb_hddt_cho_doi_chieu=1)]
	def doc(dt, **kw):
		la('không trần mặc định', kw['limit_page_length'], 0)
		if 'custom_nguon' in kw['fields']:
			la('lọc ngày và trạng thái', kw['filters'], {'posting_date':'2026-09-12', 'docstatus':1,
				'grand_total':['>',0], 'vgb_huy':['!=',1], 'vgb_tam_tinh':['!=',1]})
			return rows
		la('tiền đúng cùng tập tờ', kw['filters'], {'name':['in',['DUNG','CHUA-RO']]})
		return [D(grand_total=80000), D(grand_total=20000)]
	f = NS(db=NS(get_all=doc))
	h = NS(_cai_dat_minvoice=lambda: (None, ['Pancake'], ['@']),
		thuoc_diem_dang_xuat=pure.thuoc_diem_dang_xuat, da_co_hddt=pure.da_co_hddt)
	g = dict(frappe=f, hddt_cho_xuat=h, getdate=lambda x:x, flt=float)
	la('không bỏ tờ cần đối soát, không cộng quầy khác', nap('_dem_hddt_sot',g)('2026-09-12'), (2,100000))

@ca('#266 hai nhịp còn nợ ngày cũ vẫn ghi sổ và báo hoãn riêng')
def hai_nhip():
	for name in ['tu_ghi_so_cuoi_ngay', 'xuat_rai_trong_ngay']:
		ghi = []
		bao = []
		moc = []
		si = D(name='SI-THU', docstatus=0, vgb_quay='TCV', vgb_huy=0, vgb_tam_tinh=0)
		f = NS(set_user=lambda *a: None, log_error=lambda *a, **kw: None, get_doc=lambda *a: si, db=NS(get_all=lambda *a, **kw: [] if 'custom_pancake_id' in kw.get('filters', {}) else [si] if kw.get('fields') else ['SI-THU'], commit=lambda : None, set_single_value=lambda *a: moc.append(a)))

		def goi(si, sepay=None, cho_xuat=True):
			ghi.append(cho_xuat)
			return (1, 0, '')
		g = dict(frappe=f, cfg=lambda : D(tu_ghi_so_bat=1, tu_ghi_so_gio='23:00', tu_ghi_so_quay='TCV'), cint=lambda x: int(x or 0), nowdate=lambda : '2026-09-12', now_datetime=lambda : datetime(2026, 9, 12, 23, 10), _gio_hop_le=lambda x: x, hddt_cho_xuat=NS(xuat_ngay_cu_truoc=lambda : False), _dong_bo_doanh_so=lambda *a: None, pancake_nhip=NS(ghi_ok=lambda : None), _khoa_dong_bo=lambda **kw: object(), _mo_khoa_dong_bo=lambda *a: None, _sepay_theo_don=lambda *a: None, ghi_so_dieu_kien=NS(ly_do=lambda *a, **kw: 'san_sang'), _ghi_so_mot_don=goi, _quay_tu_ghi_so=lambda : ['TCV'], _khach_le=lambda : 'Khách lẻ', _bao_hoan_phat_hanh=lambda *a: bao.append(a), hddt_bu=NS(duoc_rai=lambda *a: True, moc_bill_du_gio=lambda *a: '2026-09-12 19:00:00', rai_bo_qua=lambda *a: False))
		fn = nap(name, g)
		if name == 'tu_ghi_so_cuoi_ngay':
			fn(bo_qua_gio=True, tren_hang_doi=True)
		else:
			fn()
		la(name + ' ghi một tờ, hoãn xuất', ghi, [False])
		la(name + ' báo cả khi tờ cũ chỉ nháp', bao, [('2026-09-12', 1, [], 'cuoi-ngay' if name == 'tu_ghi_so_cuoi_ngay' else 'xuat-rai')])
		if name == 'tu_ghi_so_cuoi_ngay':
			la('ghi sổ xong đánh dấu trước khi hoãn', moc, [('Vagabond Settings', 'tu_ghi_so_lan_cuoi', '2026-09-12')])

@ca('#266 hoãn phát hành vẫn submit và commit, không gọi cửa xuất')
def ghi_so():
	calls = []
	si = D(name='SI-THU', flags=D(), submit=lambda : calls.append('submit'))
	f = NS(db=NS(commit=lambda : calls.append('commit')))
	g = dict(frappe=f, _chuan_bi_ghi_so=lambda *a: None, _tu_xuat_hddt=lambda *a: calls.append('HTTP'))
	la('đã ghi sổ nhưng chưa xuất', nap('_ghi_so_mot_don', g)(si, cho_xuat=False), (1, 0, ''))
	la('thứ tự và không HTTP', calls, ['submit', 'commit'])

@ca('#266 cảnh báo không lọc cột giả, không đè lượt cũ và không che chuông sót')
def canh_bao():
	import sys
	from unittest.mock import patch
	calls = []
	mail = []
	moc = {}
	logs = []
	state = D(tu_ghi_so_nhat_ky='Chuỗi chính đã ghi sổ 140 đơn. CẢNH BÁO khác.')

	def ghi(*a):
		calls.append(a)
		state['tu_ghi_so_nhat_ky'] = a[2]

	def cot_la(*a):
		raise AssertionError('Email Queue không có subject')
	cache = NS(get_value=lambda k: moc.get(k), set_value=lambda k, v, **kw: moc.update({k: v}))
	f = NS(db=NS(set_single_value=ghi, commit=lambda : None, exists=cot_la), cache=lambda : cache, utils=NS(escape_html=escape), get_traceback=lambda : 'lỗi giả lập', log_error=lambda *a, **kw: logs.append((a, kw)), sendmail=lambda **kw: mail.append(kw), set_user=lambda *a: None)
	ns = NS(_khung_thu=lambda *a, **kw: ' '.join(a), _nut_xanh=lambda *a: 'Nút mở app', link_app=lambda : 'https://example.invalid')
	g = dict(giau_khoa=lambda x:x, frappe=f, cfg=lambda : state, _nguoi_nhan_don_treo=lambda : ['ci@example.invalid'])
	with patch.dict(sys.modules, {'vagabond.nhan_su': ns}):
		fn = nap('_bao_hoan_phat_hanh', g)
		fn('2026-09-12', 1, [], 'xuat-rai')
		la('xếp thư dù exists từ chối cột giả', len(mail), 1)
		dung('giữ kết quả chuỗi chính', '140 đơn' in state['tu_ghi_so_nhat_ky'])
		dung('thư có nút', bool(mail) and 'Nút mở app' in mail[0]['message'])
		truoc = state['tu_ghi_so_nhat_ky']
		fn('2026-09-12', 0, [], 'xuat-rai')
		fn('2026-09-12', 0, [], 'xuat-rai')
		la('không đè bằng lượt rỗng', state['tu_ghi_so_nhat_ky'], truoc)
		la('không xếp lại thư', len(mail), 1)
		la('không log lặp', len(logs), 1)
		g.update(nowdate=lambda : '2026-09-12', _dem_hddt_sot=lambda *a: (140, 100000), hddt_bu=NS(cau_canh_bao_sot=lambda *a: 'CẢNH BÁO còn 140 hóa đơn chưa xuất'))
		nap('canh_bao_hddt_sot', g)()
		dung('chuông sót vẫn ghi', 'CẢNH BÁO còn 140' in state['tu_ghi_so_nhat_ky'])
		la('chuông sót vẫn gửi thư riêng', len(mail), 2)
		moc.pop('vgb-hoan-phat-hanh-2026-09-12-xuat-rai-e3b0c44298fc1c14-mail')

		def hong(**kw):
			raise RuntimeError('Hàng đợi không ghi được')
		f.sendmail = hong
		fn('2026-09-12', 0, [], 'xuat-rai')
		la('xếp thư lỗi không ghi mốc thành công', moc.get('vgb-hoan-phat-hanh-2026-09-12-xuat-rai-e3b0c44298fc1c14-mail'), None)
		f.sendmail = lambda **kw: mail.append(kw)
		fn('2026-09-12', 0, [], 'xuat-rai')
		la('nhịp sau vẫn xếp lại được', len(mail), 3)
		fn('2026-09-12', 140, ['Đơn thử thiếu phương thức'], 'cuoi-ngay')
		la('cuối ngày có thư riêng', len(mail), 4)
		dung('log giữ nội dung lỗi', any('Đơn thử thiếu phương thức' in str(x) for x in logs))
		so_log=len(logs)
		fn('2026-09-12', 140, ['Đơn thử thiếu phương thức'], 'cuoi-ngay')
		la('cùng lỗi không log lặp',len(logs),so_log)
		la('cùng lỗi không thư lặp',len(mail),4)

		def hong_cache():
			raise RuntimeError('Redis ngắt')
		f.cache=hong_cache
		fn('2026-09-12', 0, [], 'xuat-rai')
		la('Redis lỗi vẫn xếp thư', len(mail), 5)
		def dem_hong(*a):
			raise RuntimeError('Không đọc được script')
		g['hddt_cho_xuat']=NS(_cai_dat_minvoice=dem_hong)
		g['cint']=lambda x:int(x or 0)
		g['_dem_hddt_sot']=nap('_dem_hddt_sot',g)
		nap('canh_bao_hddt_sot',g)()
		la('đếm lỗi vẫn có thư', len(mail), 6)
		dung('nhật ký không coi lỗi là0', 'không đếm được' in state['tu_ghi_so_nhat_ky'])
		dung('thư nói chưa biết số', 'chưa đếm được' in mail[-1]['subject'])
		dung('đếm hỏng không hướng dẫn chạy ngay', 'Cuối ngày &gt;' not in mail[-1]['message'] and 'Cuối ngày >' not in mail[-1]['message'])
		from vagabond import hddt_bu
		g['hddt_bu']=hddt_bu
		g['hddt_cho_xuat']=NS(_cai_dat_minvoice=lambda: (None, ['Pancake'], ['@']), thuoc_diem_dang_xuat=lambda *a: True, da_co_hddt=lambda *a: False)
		g['getdate']=lambda x:x
		f.db.get_all=lambda *a,**kw: [D(name='SI-%s' % i) for i in range(140)] if 'custom_nguon' in kw['fields'] else (_ for _ in ()).throw(RuntimeError('Tổng tiền lỗi'))
		so_log=len(logs)
		nap('canh_bao_hddt_sot',g)()
		la('tổng tiền lỗi ghi một log',len(logs)-so_log,1)
		dung('giữ số tờ đã đếm', '140' in mail[-1]['subject'] and 'chưa đếm được' not in mail[-1]['subject'])
		dung('nói rõ tiền chưa biết', 'chưa đọc được tổng tiền' in state['tu_ghi_so_nhat_ky'])
		dung('có đường thao tác khi đã đếm', 'Cài đặt &gt; Cuối ngày &gt; Chạy ngay' in mail[-1]['message'])
		dung('không dựng mốc0h chung', 'trước 0h' not in mail[-1]['message'])
		for nhat_ky, hoan in [('HOÃN PHÁT HÀNH 2026-09-12 (cuoi-ngay): còn nợ', True), ('Chuỗi chính đã ghi sổ', False), ('HOÃN PHÁT HÀNH 2026-09-11 (cuoi-ngay): còn nợ', False)]:
			state['tu_ghi_so_nhat_ky'] = nhat_ky
			nap('canh_bao_hddt_sot', g)()
			than = mail[-1]['message']
			la('hướng dẫn theo trạng thái hoãn hôm nay', 'Anh chị mở Cài đặt &gt; Hóa đơn ngày cũ' in than, hoan)
			la('không hoãn dẫn tới chạy ngay', 'Anh chị xử lý ngay trong ca: mở Cài đặt &gt; Cuối ngày' in than, not hoan)
			if hoan:
				dung('đối soát trước chạy ngay', than.index('Cài đặt &gt; Hóa đơn ngày cũ') < than.index('Cài đặt &gt; Cuối ngày'))



@ca('#266 công cụ đặt phiên bản giữ nguyên lịch sử patch và không nhân dòng')
def lich_su_patch():
	import importlib.util
	import tempfile
	from unittest.mock import patch
	duong = SRC.parents[1] / 'dat_phien_ban.py'
	spec = importlib.util.spec_from_file_location('dat_ver_thu', duong)
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	with tempfile.TemporaryDirectory() as d:
		p = Path(d) / 'patches.txt'
		cu = '[post_model_sync]\nvagabond.patches.dong_bo_cau_truc #v480\nkhac.patch\n'
		p.write_text(cu)
		with patch.object(m, 'TEP_PATCH', str(p)):
			dung('thêm được', m.dat_patch('482'))
			la('giữ nguyên mọi dòng', p.read_text(), cu + 'vagabond.patches.dong_bo_cau_truc #v482\n')
			la('không nhân dòng', m.dat_patch('482'), False)
