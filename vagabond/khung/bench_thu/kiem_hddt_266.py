"""#266 vòng 2: chạy thật qua Server Script với HTTP giả, cho năm finding của Codex.

Bộ kiểm tầng khung là phép thuần, không chứng minh được thứ tự và phạm vi
trên một site thật. Bench này dựng SI thật, gọi CHÍNH kịch bản M-Invoice trên
site (execute_method), chỉ thay lời gọi HTTP cuối cùng, và chốt:

  F1  gỡ cờ đối chiếu: m-invoice trả lỗi dạng dict thì tờ PHẢI giữ cờ và
      KHÔNG được gửi lại; không đối chứng được API thì không gỡ tờ nào.
  F2  hàng rào nằm ở cửa chung: tờ của HÔM NAY bị chặn khi còn hoá đơn ngày
      cũ đang chờ, kể cả khi đi bằng đường chốt đơn tay.
  F3  đồng thời: lượt khác đang giữ khoá phát hành thì hàng rào trả về CÒN NỢ
      và nhịp gọi nó phải dừng, không được ghi sổ tờ nào của hôm nay.
  F4  cửa mở hay đóng đọc theo ngày lập hiệu lực, không phải ngày sổ.
  F5  phạm vi: chỉ tờ đúng ngày và đúng điểm bán mới được gửi; số lượng 1 chỉ
      được chấp nhận cho mã khai trong ma_hang_gop.

Chỉ chạy trên bench dùng một lần (vagabond_bench_thu=1). Không gọi mạng thật,
không chạm dữ liệu sản xuất.
"""
import json
from unittest.mock import patch

import frappe
import requests
from frappe.integrations import utils as tich_hop
from frappe.utils import add_days, nowdate
from frappe.utils.password import set_encrypted_password

from vagabond import ban_hang, hddt_cho_xuat, minvoice_an_toan, minvoice_kich_ban as kich_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon


def so_(v):
	return float(v or 0)


def _bang(nhan, duoc, mong):
	if duoc != mong:
		raise AssertionError('%s: %r != %r' % (nhan, duoc, mong))


def _cau_hinh(ma_gop=''):
	for dt, vals in (
		('Vagabond Settings', dict(minvoice_host='https://minvoice.invalid', minvoice_username='kiem',
			minvoice_series='1C26TAA', pancake_shop_id='kiem266', tu_xuat_hddt=0, vgb_hddt_quay='@')),
		('MInvoice Phat Hanh Settings', dict(api2_base='https://minvoice.invalid', api2_username='kiem',
			ky_hieu='1C26TAA', thue_suat=8, ma_hang_gop=ma_gop, nguon='Pancake', enabled=1,
			tu_ky_hang_loat=0))):
		for k, v in vals.items():
			frappe.db.set_single_value(dt, k, v)
		frappe.clear_document_cache(dt, dt)
	for dt, field in (('Vagabond Settings', 'minvoice_password'),
			('Vagabond Settings', 'pancake_api_key'),
			('MInvoice Phat Hanh Settings', 'api2_password')):
		set_encrypted_password(dt, dt, 'mat-khau-gia', field)
	# Luu Single qua cua Document nhu cau hinh o Desk roi DOC LAI. Bench 243 da
	# ghi ro rang chi set_single_value la khong du, va lan chay CI dau tien cua
	# bench nay chon duoc 0 to chinh vi bo buoc nay.
	st = frappe.get_doc('MInvoice Phat Hanh Settings')
	st.api2_base = 'https://minvoice.invalid'
	st.api2_username = 'kiem'
	st.api2_password = 'mat-khau-gia'
	st.nguon = 'Pancake'
	st.enabled = 1
	st.ma_hang_gop = ma_gop
	st.save(ignore_permissions=True)
	st = frappe.get_doc('MInvoice Phat Hanh Settings')
	_bang('base phat hanh doc lai', st.api2_base, 'https://minvoice.invalid')
	_bang('nguon doc lai', st.nguon, 'Pancake')
	_bang('cong tac phat hanh bat', int(st.get('enabled') or 0), 1)


def _hoa_don(ngay, gia=(150000, 70000), ghi_so=True, chiet_khau=0, sl=None):
	"""SI Pancake thật của một ngày, có thể kèm dòng 0 đồng.

	chiet_khau: chiết khấu trên Grand Total, dùng để dựng ca THÀNH TIỀN DÒNG
	còn tiền mà gross sau chia lại về 0 (contract amount > 0 của #266 vòng 5).
	"""
	ct, tk, mau = _nen()
	ma = 'KT266-' + frappe.generate_hash(length=12)
	sl = sl or [1] * len(gia)
	dong = [dict(item_code=_mon(tk, 8), qty=q, rate=g) for g, q in zip(gia, sl)]
	hd = frappe.get_doc(dict(doctype='Sales Invoice', company=ct, currency='VND', conversion_rate=1,
		customer=frappe.db.get_value('Customer', {'disabled': 0, 'is_internal_customer': 0}, 'name'),
		custom_nguon='Pancake', custom_pancake_display_id=ma, custom_pancake_id=ma,
		vgb_pt_thanh_toan='Chuyển khoản', taxes_and_charges=mau.name,
		apply_discount_on='Grand Total', discount_amount=chiet_khau,
		set_posting_time=1, posting_date=ngay, items=dong))
	hd.flags.ignore_permissions = True
	hd.insert(ignore_permissions=True)
	nen._DA_TAO.append((hd.doctype, hd.name))
	if ghi_so:
		hd.submit()
		hd.reload()
	return hd


def chay():
	if not frappe.conf.get('vagabond_bench_thu'):
		raise RuntimeError('Chỉ chạy kiem_hddt_266 trên bench riêng vagabond_bench_thu=1.')
	form_cu = getattr(frappe.local, 'form_dict', None)
	dap_cu = getattr(frappe.local, 'response', None)
	gui, hoi, nap = [], [], []
	# Cách m-invoice trả lời GetInfoInvoice, đổi được giữa các đoạn kiểm.
	# 'am_tinh' la cau tra loi cho MA PHIEU BIA RA ma kiem_chung_api hoi de
	# do hinh dang "khong co to" cua m-invoice (#266 vong 3).
	tra_loi = {'mac_dinh': dict(code='00', data=None),
		'am_tinh': dict(code='29404', message='Get Invoice fail because not found  invoice is not exist.', ok=False)}

	def chan(*a, **kw):
		raise AssertionError('HTTP ngoài stub bị chặn trong bench #266')

	def post(url, data=None, **kw):
		if url == 'https://minvoice.invalid/api/Account/Login':
			return dict(ok=True, code='00', token='token-gia')
		if url == 'https://minvoice.invalid/api/InvoiceApi78/Save':
			goi = kw.get('json') if 'json' in kw else json.loads(data)
			gui.append(goi)
			return dict(ok=True, code='00', data=dict(
				inv_invoiceAuth_id='KT266-' + str(len(gui)), inv_invoiceNumber=str(12943 + len(gui))))
		return chan()

	class PhanHoi:
		def __init__(self, than):
			self.than = than

		def json(self):
			return self.than

		def raise_for_status(self):
			pass

	def post_python(url, **kw):
		return PhanHoi(post(url, **kw))

	def get(url, **kw):
		# Kich ban phat hanh goi kich ban NAP truoc, va nap doc don tu Pancake.
		# Bench 243 co san cua nay; bench nay thieu nen lan chay CI truoc bao
		# "HTTP ngoai stub bi chan" va phat hanh 0/1 to (#266 vong 4).
		dau = 'https://pos.pages.fm/api/v1/shops/kiem266/orders/'
		if url.startswith(dau):
			ma = url[len(dau):]
			nap.append(ma)
			return dict(success=True, data=dict(id=ma, display_id=ma,
				# PHAI co dau: kich ban nap doc chuoi "Ten khach:" co dau tieng
				# Viet. Viet khong dau thi khong tach duoc ten, to khong co ten
				# khach va duong phat hanh bo qua no. Bench 243 dung dang co dau.
				note_print='Tên khách: Khách kiểm thử 266'))
		if url == 'https://minvoice.invalid/api/InvoiceApi78/GetInfoInvoice':
			khoa = (kw.get('params') or {}).get('keyApi')
			hoi.append(khoa)
			if str(khoa or '').startswith(hddt_cho_xuat.KHOA_AM_TINH):
				return tra_loi['am_tinh']
			if khoa in tra_loi:
				return tra_loi[khoa]
			# TRA DUNG SO HOA DON CUA CHINH TO DUOC HOI.
			#
			# Vong CI cho SHA c7a6038 do o day: kiem_chung_api (vong 5) doi
			# dau vet tra ve phai mang dung custom_hddt_so cua TO DOI CHUNG,
			# ma to doi chung la to moi sua gan nhat, khong phai to nao co
			# dinh. Stub tra cung mot so 12944 cho moi to nen cong bi coi la
			# "tra nham to", ca luot khong go co, va ca kiem "khai mau roi
			# thi go duoc" do 1 != 0. Do la fixture sai chu khong phai san
			# pham sai: lop kiem nham to da lam dung viec cua no.
			so_that = frappe.db.get_value('Sales Invoice', khoa, 'custom_hddt_so')
			if so_that:
				return dict(code='00', data=dict(inv_invoiceNumber=str(so_that)))
			return tra_loi['mac_dinh']
		return chan()

	def script(ten, phieu=None, **them):
		frappe.local.form_dict = frappe._dict(phieu=phieu, che_do='day', khong_commit=1, **them)
		frappe.local.response = frappe._dict(docs=[])
		frappe.get_doc('Server Script', ten).execute_method()
		return dict(frappe.local.response.get('message') or {})

	kq = {'phan': []}
	try:
		with patch.object(requests.sessions.Session, 'request', chan), \
				patch.object(ban_hang.requests, 'post', post_python), \
				patch.object(tich_hop, 'make_post_request', post), \
				patch.object(tich_hop, 'make_get_request', get), nen._cach_ly():
			diem = 'hddt266_' + frappe.generate_hash(length=8)
			frappe.db.savepoint(diem)
			try:
				frappe.flags.vagabond_kiem_that = False
				hom_nay = nowdate()
				hom_qua = add_days(hom_nay, -1)

				# ------------------------------ F3 vòng 6: hết hạn không khoá ngày sau
				# Ca này cố ý phát hành một tờ mang ngày hôm nay. Cách ly nó bằng
				# savepoint riêng để mốc số giả không làm đóng cửa kỹ thuật của
				# ca F2 độc lập ở cuối file.
				diem_v6 = 'hddt266_v6_' + frappe.generate_hash(length=6)
				frappe.db.savepoint(diem_v6)
				# Tờ ba ngày trước đã hết hạn ký/gửi. Nó phải bị cửa chung chặn
				# nếu ai cố gửi lùi ngày, nhưng không được khoá tờ hôm qua vẫn
				# còn hạn. Sau đó chính tờ cũ chỉ đi bằng chế độ kéo sang hôm nay.
				_cau_hinh(ma_gop='')
				cu_nhat_ngay = add_days(hom_nay, -3)
				cu_nhat = _hoa_don(cu_nhat_ngay)
				frappe.db.set_value('Sales Invoice', cu_nhat.name,
					hddt_cho_xuat.TRUONG_NGAY_XUAT, cu_nhat_ngay, update_modified=False)
				giua = _hoa_don(hom_qua)
				frappe.db.set_value('Sales Invoice', giua.name,
					hddt_cho_xuat.TRUONG_NGAY_XUAT, hom_qua, update_modified=False)
				# CỬA CHUNG là hàm chan_neu_con_ngay_cu, gọi từ minvoice_an_toan.
				# kiem_goi. Ở đây gọi thẳng cửa đó vì kiem_goi còn đòi payload
				# đã dựng; đoạn F2 bên dưới mới là đường đi đủ từ nút bấm.
				truoc = len(gui)
				chan_qua_han, cau_loi = False, ''
				try:
					hddt_cho_xuat.chan_neu_con_ngay_cu(frappe.get_doc('Sales Invoice', cu_nhat.name))
				except Exception as e:
					cau_loi, chan_qua_han = str(e), 'Cửa pháp lý' in str(e)
				_bang('F3v6 tờ quá hạn bị chặn ở cửa chung', chan_qua_han, True)
				_bang('F3v6 chặn trước khi gửi', len(gui), truoc)
				# Tờ hôm qua không nhường cho nợ đã quá hạn.
				hddt_cho_xuat.chan_neu_con_ngay_cu(frappe.get_doc('Sales Invoice', giua.name))
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				if len(gui) - truoc != 1:
					raise AssertionError('F3v6 hom qua con han ma khong di duoc: %d != 1; %s'
						% (len(gui) - truoc, json.dumps(ra, ensure_ascii=False, default=str)))
				_bang('F3v6 tờ còn hạn giữ đúng ngày hôm qua',
					gui[-1]['data'][0]['inv_invoiceIssuedDate'], str(hom_qua))
				# Tờ quá hạn chỉ được kéo ngày lập sang hôm nay.
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(cu_nhat_ngay), 'keo', 'bench',
					str(hom_nay), str(hom_nay))
				if len(gui) - truoc != 1:
					raise AssertionError('F3v6 to qua han keo sang hom nay khong di duoc: %d != 1; %s'
						% (len(gui) - truoc, json.dumps(ra, ensure_ascii=False, default=str)))
				_bang('F3v6 tờ quá hạn mang ngày lập hôm nay',
					gui[-1]['data'][0]['inv_invoiceIssuedDate'], str(hom_nay))
				kq['phan'].append({'ten': 'F3 vòng 6 quá hạn không khoá ngày sau', 'dat': True,
					'chan_dung_cau': cau_loi[:120]})
				frappe.db.rollback(save_point=diem_v6)
				# Savepoint trên cũng cố ý hoàn tác cấu hình giả của riêng ca F3.
				# Dựng lại công tắc trước khi sang các ca tích hợp độc lập.
				_cau_hinh(ma_gop='')


				# Xác nhận muộn qua API thật + worker, HTTP giả. Cách ly số mới.
				diem_xn = 'hddt266_xn_' + frappe.generate_hash(length=6)
				frappe.db.savepoint(diem_xn)
				ngay_muon = add_days(hom_nay, -2)
				to_muon = _hoa_don(ngay_muon)
				to_khong_chon = _hoa_don(ngay_muon)
				to_sau = _hoa_don(hom_qua)
				truoc = len(gui)
				xem_muon = hddt_cho_xuat.xu_ly_ngay_cu(str(ngay_muon), chay_thu=1)
				with patch('rq.Queue.enqueue_call', side_effect=RuntimeError('bench RQ enqueue_call')):
					ra = hddt_cho_xuat.xu_ly_ngay_cu(str(ngay_muon), chay_thu=0,
						che_do='giu_ngay', xac_nhan_qua_han=1,
						ly_do='Kiểm bench: giữ ngày lập, ký ngày thực tế', pham_vi=xem_muon['pham_vi'], phieu_chon=[to_muon.name])
				_bang('xác nhận muộn API + worker gửi đúng một tờ', len(gui) - truoc, 1)
				_bang('tờ có trong preview nhưng không chọn không được cấp quyền', hddt_cho_xuat._ngay_xac_nhan_qua_han(hom_nay, to_khong_chon.name), ())
				_bang('không gửi tờ bỏ chọn', bool(frappe.db.get_value('Sales Invoice', to_khong_chon.name, 'custom_minvoice_id')), False)
				_bang('xác nhận giữ nguyên ngày lập trong payload',
					gui[-1]['data'][0]['inv_invoiceIssuedDate'], str(ngay_muon))
				_bang('xác nhận không đổi ngày sổ', str(frappe.db.get_value('Sales Invoice', to_muon.name, 'posting_date')), str(ngay_muon))
				_bang('không gửi tờ ngày sau cùng lượt', bool(frappe.db.get_value('Sales Invoice', to_sau.name, 'custom_minvoice_id')), False)
				_bang('xác nhận đọc lại từ DB', tuple(map(str, hddt_cho_xuat._ngay_xac_nhan_qua_han(hom_nay))), (str(ngay_muon),))
				_bang('xác nhận tự hết ngày', hddt_cho_xuat._ngay_xac_nhan_qua_han(add_days(hom_nay, 1)), ())
				# Tờ tạo sau xác nhận cùng ngày không được hưởng quyền của lô cũ.
				to_moi = _hoa_don(ngay_muon)
				chan_moi = False
				try:
					hddt_cho_xuat.chan_neu_con_ngay_cu(frappe.get_doc('Sales Invoice', to_moi.name))
				except Exception as e:
					chan_moi = 'Cửa pháp lý' in str(e)
				_bang('tờ tạo sau xác nhận bị chặn', chan_moi, True)
				truoc = len(gui)
				hddt_cho_xuat.chay_nen(str(ngay_muon), 'giu_ngay', 'bench')
				_bang('chạy lại không gửi thêm', len(gui), truoc)
				kq['phan'].append({'ten': 'Xác nhận quá hạn giữ ngày lập qua API và worker', 'dat': True})
				frappe.db.rollback(save_point=diem_xn)
				_cau_hinh(ma_gop='')

				# ---------------------------------------------- F5 phạm vi phát hành
				# Dựng ĐÚNG chuỗi thao tác của khách (điều 15): kế toán mở
				# Cài đặt > Cuối ngày, chọn ngày cũ, chọn "giữ ngày bán", máy
				# chạy nền. KHÔNG gọi thẳng kịch bản phát hành: lần chạy CI
				# đầu tiên làm vậy và chọn được 0 tờ, vì ds_cho_xuat lọc theo
				# vgb_hddt_ngay_xuat, mà trường đó chỉ do chay_nen đặt. Gọi tắt
				# là kiểm một đường mà sản phẩm không hề đi.
				#
				# TỜ NGÀY KHÁC ĐỂ Ở NGÀY HÔM NAY, không phải một ngày cũ hơn.
				# Từ vòng 5, một ngày cũ hơn đang nợ sẽ CHẶN cả lượt hôm qua,
				# đúng như chuỗi vừa kiểm ngay trên. Để tờ đối chứng ở ngày cũ
				# hơn là ca kiểm tự dựng bế tắc cho chính nó.
				cu = _hoa_don(hom_qua, gia=(150000, 0))
				khac_ngay = _hoa_don(hom_nay)
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				if len(gui) - truoc != 1:
					raise AssertionError('F5 chi phat hanh to dung ngay: %d != 1; ket qua chay_nen = %s'
						% (len(gui) - truoc, json.dumps(ra, ensure_ascii=False, default=str)))
				_bang('F5 payload một tờ', len(gui[-1]['data']), 1)
				dong_gui = [d for nhom in gui[-1]['data'][0]['details'] for d in nhom['data']]
				_bang('F5 bỏ dòng 0 đồng', len(dong_gui), 1)
				_bang('F5 ma_thue là số nguyên', [type(d['ma_thue']) is int for d in dong_gui], [True])
				_bang('F5 ngày lập là ngày bán', gui[-1]['data'][0]['inv_invoiceIssuedDate'], str(hom_qua))
				cu.reload()
				_bang('F5 tờ ngày khác không bị đụng', frappe.db.get_value(
					'Sales Invoice', khac_ngay.name, 'custom_minvoice_id'), None)
				kq['phan'].append({'ten': 'F5 phạm vi phát hành', 'dat': True,
					'da_gui': len(gui) - truoc, 'so_dong': len(dong_gui)})

				# ---------------------------------------------- F1 gỡ cờ với JSON lỗi
				kep = _hoa_don(hom_qua)
				frappe.db.set_value('Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu', 1, update_modified=False)
				frappe.db.set_value('Sales Invoice', kep.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					hom_qua, update_modified=False)
				# m-invoice trả lỗi hệ thống cho chính tờ này, và tờ đối chứng
				# (đã có hoá đơn) thì trả dấu vết đàng hoàng.
				tra_loi[kep.name] = dict(code='500', message='internal error')
				# Khong ep so hoa don co dinh nua: stub tu tra dung
				# custom_hddt_so cua chinh to duoc hoi, dung nhu cong that.
				tra_loi.pop(cu.name, None)
				tra_loi['mac_dinh'] = dict(code='00', data=None)
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F1 không gửi lại tờ đang giữ cờ', len(gui), truoc)
				_bang('F1 cờ đối chiếu còn nguyên', frappe.db.get_value(
					'Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu'), 1)
				_bang('F1 đếm đúng số tờ giữ cờ', ra.get('giu_co'), 1)
				_bang('F1 không gỡ cờ tờ nào', ra.get('go_co'), 0)
				kq['phan'].append({'ten': 'F1 JSON lỗi không gỡ cờ', 'dat': True, 'giu_co': ra.get('giu_co')})

				# Mẫu DƯƠNG TÍNH hỏng (tờ chắc chắn đã có hoá đơn mà m-invoice không
				# trả dấu vết) thì cả lượt không gỡ tờ nào, dù tờ kia trả lời sạch.
				tra_loi[kep.name] = dict(code='01', message='not found', data=None)
				tra_loi[cu.name] = dict(code='00', data=None)
				tra_loi['mac_dinh'] = dict(code='00', data=None)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F1 chưa đối chứng thì giữ cờ', frappe.db.get_value(
					'Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu'), 1)
				kq['phan'].append({'ten': 'F1 không đối chứng được thì không gỡ', 'dat': True})

				# ------------------------------------- F1 vòng 5: chưa khai mẫu, không gỡ
				# Codex bắt đúng ở vòng 5: suy mẫu "không có tờ" bằng cách hỏi
				# một mã bịa ra là SAI VỀ LOGIC. Nay mô đun để MAU_KHONG_CO_TO
				# RỖNG, nghĩa là KHÔNG tờ nào được máy gỡ cờ, kể cả khi cổng
				# trả về câu sạch nhất. Đây là ca chốt điều đó chạy thật.
				# Khong ep so hoa don co dinh nua: stub tu tra dung
				# custom_hddt_so cua chinh to duoc hoi, dung nhu cong that.
				tra_loi.pop(cu.name, None)
				tra_loi['mac_dinh'] = dict(code='00', data=None)
				tra_loi['am_tinh'] = dict(code='01', message='not found', data=None)
				tra_loi[kep.name] = dict(code='01', message='not found', data=None)
				truoc, truoc_hoi = len(gui), len(hoi)
				with patch.object(hddt_cho_xuat, 'MAU_KHONG_CO_TO', ()):
					ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F1v5 chưa khai mẫu thì câu sạch cũng giữ cờ', frappe.db.get_value(
					'Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu'), 1)
				_bang('F1v5 không gỡ cờ tờ nào', ra.get('go_co'), 0)
				_bang('F1v5 không gửi lại tờ nào', len(gui), truoc)
				_bang('F1v5 và nói rõ lý do cho kế toán', any(
					'chưa khai mẫu' in str(x) for x in (ra.get('loi') or [])), True)
				kq['phan'].append({'ten': 'F1 vòng 5 chưa khai mẫu thì không gỡ', 'dat': True,
					'giu_co': ra.get('giu_co')})

				# Ba PHẢN VÍ DỤ của Codex, chạy thật qua chay_nen: kể cả ngày
				# khai được mẫu thật, ba câu này vẫn phải giữ cờ.
				mau_thu = ({'code': '01', 'message': 'not found', 'data': None},)
				for ten_pv, pv in (('A', dict(message='Không đủ quyền')),
						('B', dict(code='9999', message='Mã chưa rõ')),
						('C', dict(code='01', data=dict(reason='Không đủ quyền')))):
					tra_loi[kep.name] = pv
					truoc = len(gui)
					with patch.object(hddt_cho_xuat, 'MAU_KHONG_CO_TO', mau_thu):
						ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
					if frappe.db.get_value('Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu') != 1:
						raise AssertionError('F1v5 phan vi du %s da go co nham: %s'
							% (ten_pv, json.dumps(ra, ensure_ascii=False, default=str)))
					_bang('F1v5 phản ví dụ %s không gửi lại' % ten_pv, len(gui), truoc)
				kq['phan'].append({'ten': 'F1 vòng 5 ba phản ví dụ vẫn giữ cờ', 'dat': True})

				# Replay phản hồi live29404, không vá mẫu product.
				tra_loi['am_tinh'] = dict(code='29404', message='Get Invoice fail because not found  invoice is not exist.', ok=False)
				tra_loi[kep.name] = dict(code='29404', message='Get Invoice fail because not found  invoice is not exist.', ok=False)
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F1v5 khai mẫu rồi thì gỡ được', frappe.db.get_value(
					'Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu'), 0)
				_bang('F1v5 gỡ đúng một tờ', ra.get('go_co'), 1)
				_bang('F1v5 gỡ xong thì gửi tờ đó đi', len(gui), truoc + 1)
				kq['phan'].append({'ten': 'F1 vòng 5 khai mẫu rồi mới gỡ', 'dat': True,
					'da_gui': len(gui) - truoc})

				# Các ca xen kẽ tiếp theo dùng mẫu giả định01 như trước.
				tra_loi["am_tinh"] = dict(code="01", message="not found", data=None)

				# ------------------------------- F5đt vòng 5: hai lượt chạy đồng thời
				# Codex đòi kiểm đồng thời thật. Bản trước gỡ cờ và commit TỪNG
				# TỜ rồi mãi cuối hàm mới lấy khoá, nên suốt đoạn gỡ cờ một lượt
				# khác vẫn chen vào được: lượt này cầm ảnh chụp cũ, ghi cờ về 0
				# và xoá mất dấu giữ chỗ lượt kia vừa đặt.
				#
				# Dựng xen kẽ ĐÚNG điểm nguy hiểm chứ không chạy hai luồng thật:
				# ngay trong lúc lượt A đang hỏi m-invoice về tờ X, lượt B ghi
				# xong hoá đơn cho X. Lượt A phải bỏ qua X, không ghi đè.
				dt = _hoa_don(hom_qua)
				frappe.db.set_value('Sales Invoice', dt.name, {
					'vgb_hddt_cho_doi_chieu': 1,
					hddt_cho_xuat.TRUONG_NGAY_XUAT: hom_qua}, update_modified=False)
				tra_loi[dt.name] = dict(code='01', message='not found', data=None)
				chen = {'so_lan': 0}

				def _luot_b(khoa):
					# Lượt B vừa xuất xong tờ này ngay trong lúc A còn đang hỏi.
					if khoa == dt.name and not chen['so_lan']:
						chen['so_lan'] = 1
						frappe.db.set_value('Sales Invoice', dt.name, {
							'custom_minvoice_id': 'KT266-luot-B',
							'custom_hddt_so': '13001'}, update_modified=False)
						frappe.db.commit()

				get_that = get

				def get_chen(url, **kw):
					if url == 'https://minvoice.invalid/api/InvoiceApi78/GetInfoInvoice':
						_luot_b((kw.get('params') or {}).get('keyApi'))
					return get_that(url, **kw)

				# Chot dung mot duong di: doi chung API coi nhu DAT san, de doan
				# nay kiem DUNG cai can kiem la khe giua luc hoi va luc ghi.
				# Vong CI truoc do o day vi khong chot: san pham lam dung (khong
				# ghi de, khong gui dup) nhung di vao nhanh khac nen cau bao ly
				# do khac han, ma ca kiem lai chot theo cau chu.
				chung_gia = ({'duong': 'bench', 'so_hd': '1', 'khoa_am': 'K'}, 'bench dat san')
				truoc = len(gui)
				with patch.object(tich_hop, 'make_get_request', get_chen), \
						patch.object(hddt_cho_xuat, 'kiem_chung_api', lambda *a, **k: chung_gia), \
						patch.object(hddt_cho_xuat, 'MAU_KHONG_CO_TO', mau_thu):
					ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				kq['loi_f5dt'] = [str(x)[:200] for x in (ra.get('loi') or [])][:6]
				_bang('F5đt lượt B có chen vào thật', chen['so_lan'], 1)
				_bang('F5đt lượt A KHÔNG xoá dấu giữ chỗ của B', frappe.db.get_value(
					'Sales Invoice', dt.name, 'custom_minvoice_id'), 'KT266-luot-B')
				_bang('F5đt cờ đối chiếu không bị ghi đè về 0', frappe.db.get_value(
					'Sales Invoice', dt.name, 'vgb_hddt_cho_doi_chieu'), 1)
				_bang('F5đt không tờ nào bị gửi đúp', len(gui), truoc)
				if not any('lượt khác vừa xuất xong' in str(x) for x in (ra.get('loi') or [])):
					raise AssertionError('F5dt khong noi ro ly do bo qua. Cac cau bao that: %s'
						% json.dumps(kq['loi_f5dt'], ensure_ascii=False))

				# Lượt khác đang GIỮ KHOÁ thì lượt này không đụng tờ nào.
				frappe.db.set_value('Sales Invoice', dt.name, {
					'custom_minvoice_id': '', 'custom_hddt_so': ''}, update_modified=False)
				truoc = len(gui)
				with patch.object(ban_hang, '_khoa_hddt', lambda cho=5: None), \
						patch.object(hddt_cho_xuat, 'MAU_KHONG_CO_TO', mau_thu):
					ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F5đt khoá bận thì không gỡ cờ tờ nào', ra.get('go_co'), 0)
				_bang('F5đt khoá bận thì không kéo tờ nào', ra.get('keo'), 0)
				_bang('F5đt khoá bận thì không gửi tờ nào', len(gui), truoc)
				_bang('F5đt cờ vẫn còn nguyên', frappe.db.get_value(
					'Sales Invoice', dt.name, 'vgb_hddt_cho_doi_chieu'), 1)
				kq['phan'].append({'ten': 'F5đt đồng thời không ghi đè', 'dat': True,
					'lan_chen': chen['so_lan']})
				# Dọn tờ này khỏi đường đi của các đoạn sau.
				frappe.db.set_value('Sales Invoice', dt.name, {
					'vgb_hddt_cho_doi_chieu': 0, 'custom_minvoice_id': 'KT266-don',
					'custom_hddt_so': '13002',
					hddt_cho_xuat.TRUONG_NGAY_XUAT: None}, update_modified=False)

				# ------------------- contract vòng 5: phép lọc dòng phải Y HỆT kịch bản
				# Codex đòi chốt contract amount > 0 giữa hai bên. Kịch bản phát
				# hành bỏ dòng có THÀNH TIỀN DÒNG = 0; thue_vnd.dong_len_hoa_don
				# phải lọc y hệt. Ba ca dưới đây đi qua ĐÚNG kịch bản trên site:
				# đổi phép lọc ở một bên là một trong ba ca đỏ ngay.
				ct_ca = []
				co_gross_0 = False
				# MOI CA MOT TO, VA DON SACH TRUOC KHI TAO.
				#
				# Vong CI truoc do o day ("contract a amount=0: 2 != 1"):
				# _phat_hanh_theo_lo phat hanh MOI to chua co hoa don cua ngay
				# do, nen gui[-1] khong chac la to cua ca dang kiem. Nay phat
				# hanh het phan ton truoc, roi moi tao to cua ca, roi phat hanh
				# lan nua: dung mot payload moi, khong con doan.
				for nhan_ca, tao_hd, so_dong_mong in (
						# a. Dong amount = 0: kich ban bo, ham cung phai bo.
						('a amount=0', lambda: _hoa_don(hom_qua, gia=(150000, 0)), 1),
						# b. amount > 0 nhung gross ve 0 sau chiet khau dau phieu:
						#    kich ban VAN gui, nen ham cung phai giu. Day dung cho
						#    ban loc theo gross lam lech so dong.
						('b gross=0 sau chiết khấu',
							lambda: _hoa_don(hom_qua, gia=(1000000, 1000), chiet_khau=1000999), 2),
						# c. dong thuong nhieu don vi: so luong phai di dung.
						('c nhiều đơn vị', lambda: _hoa_don(hom_qua, gia=(50000, 30000), sl=[3, 2]), 2)):
					ban_hang._phat_hanh_theo_lo(str(hom_qua))
					hd_ca = tao_hd()
					frappe.db.set_value('Sales Invoice', hd_ca.name,
						hddt_cho_xuat.TRUONG_NGAY_XUAT, hom_qua, update_modified=False)
					truoc = len(gui)
					ph = ban_hang._phat_hanh_theo_lo(str(hom_qua))
					if len(gui) - truoc != 1:
						raise AssertionError('contract %s: phai gui dung MOT to, gui %d. %s'
							% (nhan_ca, len(gui) - truoc,
								json.dumps(ph, ensure_ascii=False, default=str)))
					dong_ca = [d for nhom in gui[-1]['data'][0]['details'] for d in nhom['data']]
					_bang('contract %s đúng số dòng' % nhan_ca, len(dong_ca), so_dong_mong)
					gross = [so_(d.get('inv_TotalAmount')) for d in dong_ca]
					if 0 in gross:
						co_gross_0 = True
					ct_ca.append({'ca': nhan_ca, 'so_dong': len(dong_ca), 'gross': gross})
				_bang('contract c giữ đúng số lượng',
					sorted(so_(d['inv_quantity']) for d in dong_ca), [2.0, 3.0])
				# GHI THẬT: ca b chỉ CHẠM tới điểm phân kỳ khi chiết khấu thật
				# sự đẩy một dòng về gross 0. Không chạm tới thì ca vẫn đạt
				# nhưng chứng minh ít hơn, và phải nói ra chứ không gộp vào
				# "CI xanh" (điều 17).
				kq['phan'].append({'ten': 'contract amount > 0 giữa hai bên', 'dat': True,
					'ca': ct_ca, 'cham_diem_phan_ky': co_gross_0})

				# ---------------------------------------------- F2 hàng rào ở cửa chung
				# Dựng LẠI tình huống còn tờ ngày cũ đang chờ. Đoạn F1 vòng 3
				# ngay trên vừa gỡ cờ VÀ phát hành tờ kep, nên tới đây không
				# còn ngày cũ nào nợ nữa; lần chạy CI trước đã đỏ đúng vì thế
				# ("F2 tờ hôm nay bị chặn: False != True"), và hàng rào KHÔNG
				# chặn là hoàn toàn đúng khi không còn gì để nhường. Ca kiểm
				# phải tự dựng đủ điều kiện của mình, đừng thừa hưởng trạng
				# thái của đoạn trước.
				no = _hoa_don(hom_qua)
				frappe.db.set_value('Sales Invoice', no.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					hom_qua, update_modified=False)
				_bang('F2 dựng được nợ ngày cũ', str(hom_qua) in [
					str(x) for x in hddt_cho_xuat.ngay_cu_dang_cho()], True)
				_bang('F2 cửa kỹ thuật của ngày cũ còn mở',
					hddt_cho_xuat.cua_minvoice_con_mo(
						hom_qua, ban_hang._ngay_so_hddt_moi_nhat()), True)
				moi = _hoa_don(hom_nay)
				# xuat_hoa_don_dien_tu con nhieu cua DUNG TRUOC kiem_goi: thieu
				# ten khach la no dung lai ngay, khong bao gio toi hang rao. Lan
				# chay CI truoc do dung vi the ("F2 to hom nay bi chan: False !=
				# True"), va cau bao loi luc do lai la "chua co ten khach". Nay
				# dien du de to di duoc toi CUA CHUNG roi moi kiem hang rao.
				frappe.db.set_value('Sales Invoice', moi.name, {
					'vgb_xhd_ten': 'Khach kiem thu 266',
					'vgb_xhd_dia_chi': 'So 1 duong Thu',
				}, update_modified=False)
				moi.reload()
				truoc = len(gui)
				chan_duoc, cau_loi = False, ''
				try:
					ban_hang.xuat_hoa_don_dien_tu(moi.name)
				except Exception as e:
					cau_loi = str(e)
					chan_duoc = 'ngày cũ' in cau_loi or 'ngày lập' in cau_loi
				if chan_duoc is not True:
					raise AssertionError('F2 to hom nay khong bi hang rao chan. '
						'Cau loi that: %r; ngay cu dang cho = %r'
						% (cau_loi[:400], [str(x) for x in hddt_cho_xuat.ngay_cu_dang_cho()]))
				_bang('F2 không tờ nào của hôm nay được gửi', len(gui), truoc)
				kq['phan'].append({'ten': 'F2 hàng rào ở cửa chung', 'dat': True})

				# ---------------------------------------------- F3 đồng thời
				# Lượt khác đang giữ khoá phát hành: hàng rào phải báo CÒN NỢ.
				with patch.object(ban_hang, '_khoa_hddt', lambda cho=5: None):
					thong = hddt_cho_xuat.xuat_ngay_cu_truoc()
				_bang('F3 khoá bận thì báo còn nợ', thong, False)
				# Và tờ hôm nay vẫn bị chặn ở cửa chung trong lúc đó.
				truoc = len(gui)
				chan_duoc = False
				try:
					with patch.object(ban_hang, '_khoa_hddt', lambda cho=5: None):
						ban_hang.xuat_hoa_don_dien_tu(moi.name)
				except Exception:
					chan_duoc = True
				_bang('F3 vẫn chặn khi khoá bận', chan_duoc, True)
				_bang('F3 không gửi tờ nào', len(gui), truoc)
				kq['phan'].append({'ten': 'F3 đồng thời fail closed', 'dat': True})

				# ---------------------------------------------- F4 ngày lập hiệu lực
				# Tờ mang số lớn nhất có ngày sổ hôm qua nhưng ngày lập hôm nay.
				keo = _hoa_don(hom_qua)
				frappe.db.set_value('Sales Invoice', keo.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					hom_nay, update_modified=False)
				frappe.db.set_value('Sales Invoice', keo.name, 'custom_hddt_so', '99999', update_modified=False)
				frappe.db.set_value('Sales Invoice', keo.name, 'custom_minvoice_id', 'KT266-keo', update_modified=False)
				_bang('F4 đọc đúng ngày lập', str(ban_hang._ngay_so_hddt_moi_nhat()), str(hom_nay))
				# cua_con_mo(ngay, hom_nay, ngay_so_moi_nhat): tham so thu ba la
				# NGAY LAP cua to mang so/ID moi nhat, khong phai ngay so.
				_bang('F4 cửa hôm qua đã đóng',
					hddt_cho_xuat.cua_con_mo(
						hom_qua, hom_nay, ban_hang._ngay_so_hddt_moi_nhat()), False)
				# Thành công có ID nhưng GetInfoInvoice chưa trả số vẫn là một tờ
				# đã tồn tại. Biên phải giữ ngày lập của nó, không chỉ tờ có số.
				frappe.db.set_value('Sales Invoice', keo.name, 'custom_hddt_so', '', update_modified=False)
				_bang('F4 ID chưa có số vẫn giữ biên ngày lập',
					str(ban_hang._ngay_so_hddt_moi_nhat()), str(hom_nay))
				kq['phan'].append({'ten': 'F4 ngày lập hiệu lực', 'dat': True})

				# ---------------------------------------------- backlog
				# CO LAP FIXTURE F4 TRUOC, day la cho hai vong CI da do ma khong
				# hieu vi sao (SHA d849381 va 8fc53c1: "rut can 0 != 1").
				#
				# F4 vua dat to keo mang custom_hddt_so 99999 va ngay lap HOM
				# NAY. To do la to mang so lon nhat, nen _ngay_so_hddt_moi_nhat
				# tra ve hom nay, va cua cua HOM QUA coi nhu da dong. Luc do
				# xuat_ngay_cu_truoc KHONG lam gi la HOAN TOAN DUNG: cua dong
				# roi thi khong con gi de nhuong. Ca kiem do vi fixture cua doan
				# truoc, khong phai vi duong rut can hong.
				# Dung fixture cua doan truoc lam nen cho doan sau la dung cai
				# bay dieu 15. Nay tra to keo ve trang thai chua co hoa don de
				# cua hom qua mo lai, roi moi kiem duong rut can.
				for truong in ('custom_hddt_so', 'custom_minvoice_id'):
					frappe.db.set_value('Sales Invoice', keo.name, truong, '', update_modified=False)
				frappe.db.set_value('Sales Invoice', keo.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					None, update_modified=False)
				_bang('backlog: cua hom qua mo lai sau khi co lap F4',
					hddt_cho_xuat.cua_con_mo(
						hom_qua, hom_nay, ban_hang._ngay_so_hddt_moi_nhat()), True)
				_bang('backlog: van con no ngay cu de rut can',
					str(hom_qua) in [str(x) for x in hddt_cho_xuat.ngay_cu_dang_cho()], True)

				# Gio moi kiem duoc DUONG RUT CAN that: hang rao day ham nay
				# sang hang doi, luot do phai phat hanh het to ngay cu roi to
				# hom nay mai di duoc. Day la duong se chay de cuu 117 to 09/09.
				# DEM TRUOC BAO NHIEU TO DANG CHO, roi doi hoi RUT CAN HET.
				#
				# Vong CI truoc do o day ("rut can: 2 != 1"): sau cac doan
				# tren, ngay hom qua con hon mot to cho, ma ca kiem lai chot
				# cung so 1. Chot cung mot con so la chot vao trang thai thua
				# huong tu doan truoc chu khong phai vao TINH CHAT can kiem.
				# Tinh chat that su la: rut can phai gui HET so to dang cho, va
				# xong thi backlog rong.
				def _con_sot(ngay):
					"""To da ghi so cua NGAY do ma chua co hoa don dien tu.

					Duong rut can di qua _phat_hanh_theo_lo, tuc kich ban chon
					theo NGAY SO, khong phai theo ds_cho_xuat (tap hep hon, con
					doi dau vgb_hddt_ngay_xuat). Vong CI truoc do vi lay so
					mong doi tu ds_cho_xuat roi so voi so that: "2 to, dang cho
					1". Dem bang dung tap ma duong rut can that su dung.
					"""
					r = frappe.db.sql("""select name from `tabSales Invoice`
						where posting_date = %(n)s and docstatus = 1
						  and ifnull(vgb_huy, 0) = 0 and ifnull(vgb_tam_tinh, 0) = 0
						  and grand_total > 0
						  and ifnull(custom_hddt_so, '') = ''
						  and ifnull(custom_minvoice_id, '') = ''
						  and ifnull(custom_hddt_id, '') = ''""", {'n': str(ngay)})
					return [x[0] for x in r]

				# CHOT THEO TINH CHAT, khong chot con so cung:
				# rut can phai lam CAN ngay cu, va moi to gui di deu mang dung
				# ngay ban. Con so bao nhieu to la trang thai thua huong tu cac
				# doan tren, chot vao no la chot nham thu.
				cho_truoc = _con_sot(hom_qua)
				if not cho_truoc:
					raise AssertionError('rut can: khong con to nao sot, ca kiem tu dung bang khong')
				truoc = len(gui)
				het_no = hddt_cho_xuat.xuat_ngay_cu_truoc()
				da_gui = len(gui) - truoc
				if da_gui < 1:
					raise AssertionError('rut can: khong gui to nao du con %d to sot (%r); '
						'ngay cu con lai = %r; ngay so moi nhat = %s'
						% (len(cho_truoc), cho_truoc,
							[str(x) for x in hddt_cho_xuat.ngay_cu_dang_cho()],
							ban_hang._ngay_so_hddt_moi_nhat()))
				con_sau = _con_sot(hom_qua)
				if con_sau:
					raise AssertionError('rut can: van con %d to sot cua ngay cu sau khi rut: %r'
						% (len(con_sau), con_sau))
				_bang('rút cạn xong thì báo hết nợ', het_no, True)
				_bang('rút cạn: mọi tờ ngày cũ mang đúng ngày bán',
					sorted({g['data'][0]['inv_invoiceIssuedDate'] for g in gui[truoc:]}),
					[str(hom_qua)])

				# Don not dau vet cua to kep (da co hoa don tu doan F1 vong 3).
				frappe.db.set_value('Sales Invoice', kep.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					None, update_modified=False)
				con = [str(x) for x in hddt_cho_xuat.ngay_cu_dang_cho()]
				if con:
					raise AssertionError('backlog chua rong sau khi rut can: %r' % con)
				truoc = len(gui)
				ban_hang.xuat_hoa_don_dien_tu(moi.name)
				_bang('hết nợ thì tờ hôm nay đi được', len(gui) - truoc, 1)
				_bang('ngày lập của tờ hôm nay', gui[-1]['data'][0]['inv_invoiceIssuedDate'], str(hom_nay))
				kq['phan'].append({'ten': 'backlog rút cạn rồi mới thông', 'dat': True,
					'da_gui_ngay_cu': da_gui, 'sot_truoc': len(cho_truoc)})

				kq['dat'] = True
			finally:
				frappe.db.rollback(save_point=diem)
	except Exception as e:
		kq['dat'] = False
		kq['loi'] = '%s: %s' % (type(e).__name__, e)
	finally:
		frappe.local.form_dict = form_cu
		frappe.local.response = dap_cu
		frappe.flags.vagabond_kiem_that = True
	kq['so_lan_gui'] = len(gui)
	kq['so_lan_hoi'] = len(hoi)
	return kq


if __name__ == '__main__':
	frappe.init(site='bench-ci.localhost', sites_path='.')
	frappe.connect()
	try:
		ra = chay()
		print(json.dumps(ra, ensure_ascii=False, indent=2, default=str))
	finally:
		frappe.db.rollback()
		frappe.destroy()
	raise SystemExit(0 if ra.get('dat') else 1)
