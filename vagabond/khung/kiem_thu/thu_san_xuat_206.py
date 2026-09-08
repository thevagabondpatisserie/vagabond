"""#206: chạy hàm thật với kho giả; không thay cho kiểm Frappe/SLE."""
from unittest.mock import patch
from types import SimpleNamespace
import ast
import json
from pathlib import Path

from vagabond import san_xuat_desktop as sx, kho_san_xuat as ks
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


@ca('206 mặc định Desk: patch giữ trường riêng, tên cạnh mã, skip mới và chạy lại không đổi')
def _mac_dinh_desk():
	duong = Path(__file__).resolve().parents[2] / 'patches' / 'mac_dinh_san_xuat_206.py'
	cay = ast.parse(duong.read_text())
	cay.body = [d for d in cay.body if isinstance(d, ast.FunctionDef)]
	truong = ['item', 'production_item', 'custom_rieng', 'qty', 'item_name', 'skip_transfer']
	ghi = {}
	def dat(dt, f, p, v, t, **kw):
		if p == 'field_order': dung('field_order thuộc DocType', kw.get('for_doctype'))
		ghi[(dt, f, p)] = v
		if p == 'field_order': truong[:] = json.loads(v)
	def meta(dt, **kw):
		return SimpleNamespace(fields=[SimpleNamespace(fieldname=x) for x in truong],
			get_field=lambda f: SimpleNamespace(options=ghi.get(('Stock Entry','naming_series','options'), 'CU-.YYYY.-')))
	pham_vi = {'json': json, 'frappe': SimpleNamespace(get_meta=meta, clear_cache=lambda **kw: None), 'make_property_setter': dat}
	exec(compile(cay, str(duong), 'exec'), pham_vi)
	pham_vi['execute']()
	la('tên cạnh mã', truong[truong.index('production_item')+1], 'item_name')
	dung('giữ trường riêng', 'custom_rieng' in truong)
	la('mặc định bỏ qua', ghi[('Work Order','skip_transfer','default')], '1')
	la('không cho nhập tên riêng', ghi[('Work Order','item_name','read_only')], 1)
	dung('giữ mẫu cũ', 'CU-.YYYY.-' in ghi[('Stock Entry','naming_series','options')])
	cu = dict(ghi); pham_vi['execute'](); la('lặp không đổi', ghi, cu)


class Doc(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	def is_new(self):
		return self.get('moi', True)


@ca("206 kho đã chọn và dòng khác kho không bị suy lại theo bếp")
def _():
	doc = Doc(source_warehouse='Pastry', required_items=[
		Doc(item_code='Rum', source_warehouse='Pastry'),
		Doc(item_code='Bao bi', source_warehouse='Kho rieng'),
		Doc(item_code='Bot', source_warehouse='')])
	ks.gan_kho_nguon(doc)
	la('giữ lựa chọn từng dòng', [d.source_warehouse for d in doc.required_items], ['Pastry', 'Kho rieng', 'Pastry'])


@ca("206 mặc định món chỉ điền lệnh mới chưa chọn kho")
def _():
	with patch.object(sx, 'kho_tren_mon', return_value='Pastry'), patch.object(sx, 'kiem_kho') as kiem:
		doc = Doc(production_item='Banh', company='TV', skip_transfer=1)
		sx.dien_kho_mon(doc)
		la('nguồn', doc.source_warehouse, 'Pastry')
		kiem.assert_called_once_with('Pastry', 'TV')
		for gia in [Doc(moi=False), Doc(source_warehouse='Chon tay')]:
			cu = dict(gia)
			sx.dien_kho_mon(gia)
			la('không đổi', dict(gia), cu)


@ca("206 cấu hình kho lỗi phải ném, không rơi về kho khác")
def _():
	with patch.object(sx, 'kho_tren_mon', return_value='Kho tat'), patch.object(sx, 'kiem_kho', side_effect=ValueError('Kho tat')):
		nem('chặn kho sai', lambda: sx.dien_kho_mon(Doc(production_item='Banh')), ValueError)


@ca("206 thông tin LSX tính hao hụt, WIP và cảnh báo kho dòng")
def _():
	d = Doc(qty=10, produced_qty=6, process_loss_qty=1, skip_transfer=1,
		source_warehouse='Pastry', required_items=[Doc(item_code='Rum', source_warehouse='Baker')])
	r = sx.thong_tin_lenh(d)
	la('còn', r['con_lai'], 3)
	la('khác kho', r['so_khac_kho'], 1)
	la('không qua WIP', r['qua_wip'], False)
	d.from_wip_warehouse = 1
	la('từ WIP', sx.thong_tin_lenh(d)['qua_wip'], True)
	d.process_loss_qty = 20
	la('không âm', sx.thong_tin_lenh(d)['con_lai'], 0)


@ca("206 đọc chi tiết bắt buộc quyền trên lệnh")
def _():
	class Cam(Doc):
		def check_permission(self, loai):
			raise PermissionError(loai)
	with patch.object(sx, 'frappe', SimpleNamespace(get_doc=lambda *a: Cam())):
		nem('không lộ chi tiết', lambda: sx.chi_tiet('WO-CAM'), PermissionError)


@ca("206 thay nguyên liệu giữ original_item để ERPNext cộng consumed_qty")
def _():
	from contextlib import ExitStack
	from vagabond import lo_hang as lh
	class Dong(Doc):
		def as_dict(self): return dict(self)
	d = Dong(item_code='Rum goc', s_warehouse='Pastry', qty=2, uom='ML', stock_uom='ML', conversion_factor=1)
	# items là thuộc tính Frappe, không phải dict.items của Python.
	class P:
		docstatus = 0
		purpose = 'Manufacture'
		items = [d]
		def set(self,k,v): setattr(self,k,v)
		def append(self,k,v): getattr(self,k).append(v)
	doc = P()
	with ExitStack() as st:
		for ten, ham in {
			'_dong_can_lo': lambda x: True,
			'phan_da_chon_tay': lambda *a, **k: {},
			'_tui_lo': lambda bo, ma, kho, **k: {'con': [('LO-ISC',10)] if ma == 'ISC' else []},
			'_cac_ma_thay_the': lambda ma: ['ISC'],
			'_boc': lambda d, **k: dict(d),
		}.items(): st.enter_context(patch.object(lh, ten, ham))
		st.enter_context(patch.object(lh.frappe, 'get_cached_value', return_value='ML', create=True))
		lh.gan_lo(doc)
	la('một dòng thay', len(doc.items), 1)
	la('mã dùng', doc.items[0].get('item_code'), 'ISC')
	la('liên kết mã gốc', doc.items[0].get('original_item'), 'Rum goc')
	la('không đổi kho', doc.items[0].get('s_warehouse'), 'Pastry')
	la('lô thực dùng', doc.items[0].get('batch_no'), 'LO-ISC')


@ca('206 thiếu Bacardi nhưng ISC ở kho khác thì chỉ đúng đường, không nói hết toàn hệ')
def _():
	from vagabond.lo_hang import cau_thieu_lo
	c = cau_thieu_lo('Bacardi', 'BACARDI', 'Baker', 20, 'ML', [], [('ISC', 'Pastry', 200)])
	for chu in ['ISC', 'Pastry', '200', 'chuyển nguyên liệu', 'chưa xác nhận lô']:
		dung(chu, chu in c)
	dung('không khẳng định hết hệ', 'Cả hệ không còn' not in c)
