"""#317: biên mua vặt và chia lô theo đúng người nhận."""
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import de_nghi_chi as dc
from vagabond.ttnb_lo import chia_lo


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


@ca('#317 ba phiếu hai tài khoản tạo hai lô, retry không đổi mã')
def _lo():
	ds=[dict(name=str(i),ngan_hang='MB',so_tk='1' if i<3 else '2',ten_tk='A',tong_tien=100) for i in (1,2,3)]
	lo=chia_lo(ds)
	la('hai người nhận',len(lo),2)
	la('tổng bảo toàn',sum(x['tong_tien'] for x in lo),300)
	la('đổi thứ tự vẫn cùng lô',lo,chia_lo(list(reversed(ds))))
	dung('mã lô để đối soát',all(x['ma_lo'] in x['noi_dung'] for x in lo))
