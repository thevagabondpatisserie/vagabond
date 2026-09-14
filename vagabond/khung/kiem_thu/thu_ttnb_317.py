"""#317: biên mua vặt và đường duyệt đúng theo loại nghiệp vụ."""
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import de_nghi_chi as dc


def phieu(tien=500000, **kw):
	p = dict(loai_nghiep_vu='Chi phí', cac_khoan=[dict(so_tien=tien)], _so_tep_phieu=1)
	p.update(kw)
	return p


@ca('#317 trần mua vặt dưới bằng trên, không tin tổng máy khách')
def _nguong():
	for t in (499999, 500000):
		la('trong trần', dc.ly_do_chan_vat(phieu(t)), None)
	dung('trên trần', '500.000' in dc.ly_do_chan_vat(phieu(500001)))
	dung('không hạ tổng giả', dc.ly_do_chan_vat(phieu(500001, tong_tien=1)))


@ca('#317 một hoá đơn một phiếu và đúng một biên nhận')
def _chung_tu():
	p=phieu(10, cac_khoan=[dict(so_tien=10,so_hoa_don='A'),dict(so_tien=10,so_hoa_don='B')])
	dung('hai số', 'tách phiếu' in dc.ly_do_chan_vat(p))
	p['cac_khoan'][1]['so_hoa_don']=''
	dung('một có một không', dc.ly_do_chan_vat(p))
	for n in (0,):
		dung('thiếu biên nhận', dc.ly_do_chan_vat(phieu(_so_tep_phieu=n)))
	la('hai ảnh cùng biên nhận được nhận', dc.ly_do_chan_vat(phieu(_so_tep_phieu=2)), None)


@ca('#317 tạm ứng và hoàn ứng chỉ miễn trần khi đã xác minh YCPS')
def _ung():
	dung('thiếu YCPS', dc.ly_do_chan_vat(phieu(600000,loai_nghiep_vu='Tạm ứng')))
	la('đã xác minh', dc.ly_do_chan_vat(phieu(600000,loai_nghiep_vu='Tạm ứng',_ycps_hop_le=True)),None)
	dung('tự gõ mã không đủ',dc.ly_do_chan_vat(phieu(600000,loai_nghiep_vu='Hoàn ứng',yeu_cau_phat_sinh='YCPS-X')))
	la('kế thừa đã xác minh',dc.ly_do_chan_vat(phieu(600000,loai_nghiep_vu='Hoàn ứng',_ycps_ke_thua=True)),None)


@ca('#317 chỉ tạm ứng lớn qua giám đốc, chi phí và hoàn ứng về kế toán')
def _duyet_theo_loai():
	la('tạm ứng lớn qua giám đốc', dc.buoc_ke_tiep(2000000, dc.NV_TAM_UNG), dc.TT_CHO_GIAM_DOC)
	la('chi phí lớn về kế toán', dc.buoc_ke_tiep(2000000, dc.NV_CHI_PHI), dc.TT_CHO_KE_TOAN)
	la('hoàn ứng lớn về kế toán', dc.buoc_ke_tiep(2000000, dc.NV_HOAN_UNG), dc.TT_CHO_KE_TOAN)


@ca('#317 uỷ nhiệm chi chỉ bắt buộc khi trả nhà cung cấp bằng chuyển khoản')
def _uy_nhiem_chi():
	src = open(dc.__file__, encoding='utf-8').read()
	i = src.index('\ndef duyet(')
	j = src.index('\ndef huy(', i)
	than = src[i:j]
	dung('chặn đúng hình thức nhà cung cấp', 'doc.get("hinh_thuc") or "") == HT_NCC' in than)
	dung('chặn đúng chuyển khoản', 'doc.get("phuong_thuc") or "") == PT_CHUYEN_KHOAN' in than)


@ca('#317 màn chi tiết có nút quay về danh sách và nhãn kế toán duyệt và chi')
def _giao_dien_duyet():
	import os
	js = open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'public/js/bep/16-mua-hang.js'), encoding='utf-8').read()
	dung('có nút quay lại', 'id="ttnbVeDanhSach"' in js and 'go(scrTTNB, true)' in js)
	dung('có nhãn duyệt và chi', "'Duyệt và chi'" in js)
	dung('đã ẩn gộp chuyển', 'id="ttnbGop"' not in js and 'vagabond.ttnb_lo.gop' not in js)


@ca('#317 gọi cửa duyệt thật: hoàn ứng một tệp đạt, UNC nhà cung cấp vẫn chặn')
def _duyet_cua_that():
	from unittest.mock import patch
	from types import SimpleNamespace
	class Phieu(dict):
		__getattr__ = dict.get
		__setattr__ = dict.__setitem__
		def save(self, **kw):
			self['da_luu'] = True
	for hinh, chan in ((dc.HT_NCC, True), ('Hoàn tiền nhân viên', False)):
		d = Phieu(name='TTNB-THU', trang_thai=dc.TT_CHO_DUYET, nguoi_tao='nguoi-lap',
			loai_nghiep_vu=dc.NV_HOAN_UNG, hinh_thuc=hinh, phuong_thuc=dc.PT_CHUYEN_KHOAN,
			cac_khoan=[{'so_tien': 2000000}])
		def bao(cau):
			raise ValueError(cau)
		with patch.object(dc.frappe, 'get_doc', return_value=d), \
			patch.object(dc.frappe, 'session', SimpleNamespace(user='ke-toan')), \
			patch.object(dc.frappe, 'throw', side_effect=bao), \
			patch.object(dc, '_vai', return_value=dc.VAI_GIAM_DOC), \
			patch.object(dc, '_so_tep', return_value=1), \
			patch.object(dc, '_bao_buoc_ke_tiep'):
			loi = ''
			try:
				dc.duyet(d.name)
			except ValueError as e:
				loi = str(e)
			if chan:
				dung('thiếu UNC không lưu', 'uỷ nhiệm chi' in loi and not d.get('da_luu'))
			else:
				la('không bắt UNC của nhân viên', loi, '')
				la('đã lưu đúng bàn kế toán', d.trang_thai, dc.TT_CHO_KE_TOAN)
				dung('cửa duyệt đã lưu', d.get('da_luu'))


@ca('#317 người mua hàng chọn Người lập thì truy vấn thật áp đúng bộ lọc')
def _nguoi_lap_mua_hang():
	from unittest.mock import patch
	from copy import deepcopy
	goi = []
	def doc(dt, **kw):
		goi.append(deepcopy(kw))
		return []
	import sys
	from types import SimpleNamespace
	with patch.dict(sys.modules, {'vagabond.ban_hang': SimpleNamespace(_kiem_quyen=lambda: None)}), patch.object(dc, '_vai', return_value=dc.VAI_DUYET), \
		patch.object(dc.frappe, 'get_all', side_effect=doc):
		kq = dc.ds_man(so_ngay=0, nguoi_lap='nguoi-duoc-chon')
		la('vai mua hàng thấy nút', kq['duoc_duyet'], 1)
		ds = next(k for k in goi if 'ten_khoan_chi' in k.get('fields', []))
		la('máy chủ lọc người đã chọn', ds['filters'].get('nguoi_tao'), 'nguoi-duoc-chon')


@ca('#317 lịch sử trả tên người lập và quá hạn, không báo hoàn ứng phải qua giám đốc')
def _lich_su_dau_vet():
	from unittest.mock import patch
	from types import SimpleNamespace
	def doc(dt, **kw):
		if dt == 'User': return [SimpleNamespace(name='nguoi-thu', full_name='Người thử')]
		if dt == dc.DT: return [dict(name='PHIEU-THU', nguoi_tao='nguoi-thu', trang_thai=dc.TT_CHO_KE_TOAN,
			ngay_can_tt='2026-09-01', tong_tien=3000000, loai_nghiep_vu=dc.NV_HOAN_UNG)]
		return []
	with patch.object(dc, '_vai', return_value=dc.VAI_DUYET), \
		patch.object(dc.frappe, 'get_all', side_effect=doc), patch.object(dc, 'nowdate', return_value='2026-09-14'):
		r = dc.danh_sach()['ds'][0]
		la('tên thật trong payload lịch sử', r['ten_nguoi_tao'], 'Người thử')
		dung('hiện quá hạn', r['qua_han'])
		la('hoàn ứng không qua giám đốc', r['can_giam_doc'], 0)


@ca('#317 patch chuyển bước phải giao lại kế toán, không gửi thông báo migrate')
def _patch_giao_lai():
	import sys
	from unittest.mock import patch, Mock
	from types import SimpleNamespace
	from vagabond.patches import ycps_317
	giao = Mock(return_value={'giao': 1})
	with patch.dict(sys.modules, {'vagabond.giao_viec': SimpleNamespace(giao_vai=giao)}), \
		patch.object(dc.frappe, 'get_all', return_value=['PHIEU-THU']), \
		patch.object(dc.frappe.db, 'get_value', return_value=''), \
		patch.object(dc.frappe.db, 'set_value'), \
		patch.object(dc.frappe.db, 'exists', return_value=False), \
		patch.object(dc.frappe, 'get_doc', return_value=SimpleNamespace(add_comment=Mock())):
		ycps_317.execute()
		la('giao đúng phiếu', giao.call_args.args[:3], (dc.DT, 'PHIEU-THU', sorted(dc.VAI_BUOC[dc.TT_CHO_KE_TOAN])))
		la('không bắn chuông', giao.call_args.kwargs, {'bao': 0})


@ca('#317 chọn YCPS: chỉ mã của người đăng nhập, không nhận người dùng từ client')
def _ycps_cua_toi():
	from unittest.mock import patch
	from types import SimpleNamespace
	with patch.object(dc.frappe, 'session', SimpleNamespace(user='nhan-vien')), \
		patch.object(dc.frappe.db, 'exists', return_value=True), \
		patch.object(dc.frappe, 'get_meta', create=True, return_value=SimpleNamespace(has_field=lambda x: True)), \
		patch.object(dc.frappe, 'get_all', side_effect=[['YCPS-CHIA'], [{'name': 'YCPS-1', 'muc_dich': 'Mua hàng'}]]) as doc:
		la('chỉ trả dữ liệu cần chọn', dc.ycps_cua_toi()['ds'][0]['name'], 'YCPS-1')
		la('không chọn phiếu đã cancel', doc.call_args.kwargs['filters']['docstatus'], ['!=', 2])
		la('lọc owner phía server', doc.call_args.kwargs['or_filters']['owner'], 'nhan-vien')
		la('không lộ toàn bộ phiếu', doc.call_args.kwargs['fields'], ['name', 'muc_dich'])
		la('người yêu cầu đúng user', doc.call_args.kwargs['or_filters']['nguoi_yeu_cau'], 'nhan-vien')
		la('chỉ phiếu được chia sẻ', doc.call_args.kwargs['or_filters']['name'], ['in', ['YCPS-CHIA']])


@ca('#317 ngoại lệ chỉ hoàn ứng cũ, không nới chi phí hoặc tạm ứng mới')
def _ngoai_le_cu():
	la('hoàn ứng cũ có chứng từ', dc.ly_do_chan_vat(phieu(600000, loai_nghiep_vu=dc.NV_HOAN_UNG, _hoan_ung_cu=True)), None)
	dung('chi phí vẫn chặn', dc.ly_do_chan_vat(phieu(600000, _hoan_ung_cu=True)))
	dung('tạm ứng mới vẫn chặn', dc.ly_do_chan_vat(phieu(600000, loai_nghiep_vu=dc.NV_TAM_UNG, _hoan_ung_cu=True)))


@ca('#317 YCPS nguồn huỷ: nhận phiếu thay thế thuộc người lập, không đổi nguồn')
def _ycps_huy_thay_the():
	from unittest.mock import patch
	from types import SimpleNamespace
	class D(dict):
		__getattr__ = dict.get
		__setattr__ = dict.__setitem__
		def is_new(self): return False
	p = D(name='HOAN', nguoi_tao='nhan-vien', trang_thai=dc.TT_CHO_KE_TOAN,
		loai_nghiep_vu=dc.NV_HOAN_UNG, thuoc_tam_ung='UNG', yeu_cau_phat_sinh='YCPS-MOI', cac_khoan=[])
	tu = D(nguoi_tao='nhan-vien', loai_nghiep_vu=dc.NV_TAM_UNG,
		trang_thai=dc.TT_DA_CHI, quy_tac_317=1, yeu_cau_phat_sinh='YCPS-HUY')
	def doc(dt, name, *args, **kw):
		if dt == dc.DT: return tu if name == 'UNG' else D(quy_tac_317=1, trang_thai=dc.TT_CHO_KE_TOAN)
		if dt == 'RnD Purchase Request': return 'Huỷ'
		return None
	with patch.object(dc, '_kem_dm', side_effect=lambda d: dict(d)), \
		patch.object(dc.frappe.db, 'get_value', side_effect=doc), \
		patch.object(dc.frappe.db, 'exists', return_value=True), \
		patch.object(dc.frappe, 'get_doc', side_effect=lambda dt, ma: D(owner='nhan-vien', trang_thai='Huỷ' if ma == 'YCPS-HUY' else 'Đã duyệt')), \
		patch.object(dc.frappe, 'get_all', return_value=[]):
		ra = dc._phieu_kiem_317(p)
		la('phiếu mới hợp lệ', ra['_ycps_hop_le'], True)
		la('chọn phiếu mới giữ nguyên', p.yeu_cau_phat_sinh, 'YCPS-MOI')
		la('không sửa YCPS gốc', tu.yeu_cau_phat_sinh, 'YCPS-HUY')


@ca('#317 YCPS thiếu DocType hoặc phiếu: không nạp controller')
def _ycps_khong_ton_tai():
	from unittest.mock import patch
	for co_dt in (False, True):
		with patch.object(dc.frappe.db, 'exists', side_effect=lambda dt, ma: co_dt if dt == 'DocType' else False), \
			patch.object(dc.frappe, 'get_doc') as nap:
			la('thiếu trả None', dc._doc_ycps_317('YCPS-MAT'), None)
			la('không nạp controller', nap.call_count, 0)


@ca('#317 dấu vết thay YCPS chỉ ghi ở lần kế toán duyệt cuối')
def _dau_vet_mot_lan():
	from unittest.mock import patch, Mock
	from types import SimpleNamespace
	class D(dict):
		__getattr__ = dict.get
		__setattr__ = dict.__setitem__
		def save(self, **kw): pass
	p = D(name='HOAN', nguoi_tao='nhan-vien', trang_thai=dc.TT_CHO_DUYET,
		loai_nghiep_vu=dc.NV_HOAN_UNG, thuoc_tam_ung='UNG', yeu_cau_phat_sinh='YCPS-MOI', cac_khoan=[{'so_tien': 100}])
	p.add_comment = Mock()
	with patch.object(dc.frappe, 'get_doc', return_value=p), \
		patch.object(dc.frappe.db, 'get_value', return_value='YCPS-CU'), \
		patch.object(dc.frappe, 'session', SimpleNamespace(user='ke-toan')), \
		patch.object(dc, '_vai', return_value={'System Manager'}), \
		patch.object(dc, '_phieu_kiem_317', return_value={}), \
		patch.object(dc, '_bao_buoc_ke_tiep'):
		dc.duyet(p.name)
		la('bước mua hàng chưa ghi thay nguồn', p.add_comment.call_count, 0)
		dc.duyet(p.name)
		la('bước kế toán ghi đúng một lần', p.add_comment.call_count, 1)


@ca('#317 đọc trạng thái YCPS không nạp Document')
def _ycps_doc_nhe():
	from unittest.mock import patch
	with patch.object(dc.frappe.db, 'exists', return_value=True), \
		patch.object(dc.frappe.db, 'get_value', return_value={'trang_thai': 'Mới tạo', 'docstatus': 2}) as doc, \
		patch.object(dc.frappe, 'get_doc') as day_du:
		dung('phiếu cancel không hợp lệ', not dc._ycps_hop_le_317(dc._trang_thai_ycps_317('YCPS-1')))
		la('chỉ hai cột cần thiết', doc.call_args.args[2], ['trang_thai', 'docstatus'])
		day_du.assert_not_called()


@ca('#317 patch không ép naming series trên DocType không có trường đó')
def _ycps_khong_co_series():
	from unittest.mock import Mock, patch
	from types import SimpleNamespace
	import sys
	from vagabond.patches import ycps_317
	setter = Mock()
	with patch.object(dc.frappe, 'get_all', return_value=[]), \
		patch.object(dc.frappe.db, 'exists', return_value=True), \
		patch.object(dc.frappe, 'get_meta', create=True, return_value=SimpleNamespace(get_field=lambda x: None)), \
		patch.dict(sys.modules, {'frappe.custom.doctype.property_setter.property_setter': SimpleNamespace(make_property_setter=setter)}):
		ycps_317.execute()
		setter.assert_not_called()
