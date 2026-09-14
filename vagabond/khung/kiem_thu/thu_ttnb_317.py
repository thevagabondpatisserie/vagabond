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
	for n in (0,2):
		dung('số tệp không đúng', dc.ly_do_chan_vat(phieu(_so_tep_phieu=n)))


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
