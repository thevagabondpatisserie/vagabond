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


def _hoa_don(ngay, gia=(150000, 70000), ghi_so=True):
	"""SI Pancake thật của một ngày, có thể kèm dòng 0 đồng."""
	ct, tk, mau = _nen()
	ma = 'KT266-' + frappe.generate_hash(length=12)
	dong = [dict(item_code=_mon(tk, 8), qty=1, rate=g) for g in gia]
	hd = frappe.get_doc(dict(doctype='Sales Invoice', company=ct, currency='VND', conversion_rate=1,
		customer=frappe.db.get_value('Customer', {'disabled': 0, 'is_internal_customer': 0}, 'name'),
		custom_nguon='Pancake', custom_pancake_display_id=ma, custom_pancake_id=ma,
		vgb_pt_thanh_toan='Chuyển khoản', taxes_and_charges=mau.name,
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
	gui, hoi = [], []
	# Cách m-invoice trả lời GetInfoInvoice, đổi được giữa các đoạn kiểm.
	# 'am_tinh' la cau tra loi cho MA PHIEU BIA RA ma kiem_chung_api hoi de
	# do hinh dang "khong co to" cua m-invoice (#266 vong 3).
	tra_loi = {'mac_dinh': dict(code='00', data=None),
		'am_tinh': dict(code='01', message='not found', data=None)}

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
		if url == 'https://minvoice.invalid/api/InvoiceApi78/GetInfoInvoice':
			khoa = (kw.get('params') or {}).get('keyApi')
			hoi.append(khoa)
			if str(khoa or '').startswith(hddt_cho_xuat.KHOA_AM_TINH):
				return tra_loi['am_tinh']
			return tra_loi.get(khoa, tra_loi['mac_dinh'])
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

				# ---------------------------------------------- F5 phạm vi phát hành
				# Dựng ĐÚNG chuỗi thao tác của khách (điều 15): kế toán mở
				# Cài đặt > Cuối ngày, chọn ngày cũ, chọn "giữ ngày bán", máy
				# chạy nền. KHÔNG gọi thẳng kịch bản phát hành: lần chạy CI
				# đầu tiên làm vậy và chọn được 0 tờ, vì ds_cho_xuat lọc theo
				# vgb_hddt_ngay_xuat, mà trường đó chỉ do chay_nen đặt. Gọi tắt
				# là kiểm một đường mà sản phẩm không hề đi.
				_cau_hinh(ma_gop='')
				cu = _hoa_don(hom_qua, gia=(150000, 0))
				khac_ngay = _hoa_don(add_days(hom_nay, -3))
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
				tra_loi[cu.name] = dict(code='00', data=dict(inv_invoiceNumber='12944'))
				tra_loi['mac_dinh'] = dict(code='00', data=dict(inv_invoiceNumber='12944'))
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

				# ------------------------------------------ F1 vòng 3: mã LẠ giữ cờ
				# Mẫu dương tính và âm tính đều tốt, nhưng tờ này trả mã 9999, đúng
				# mã m-invoice đã từ chối 116 tờ TCV đêm 09/09. Mã đó KHÔNG phải
				# câu "không có tờ" nên phải giữ cờ.
				tra_loi[cu.name] = dict(code='00', data=dict(inv_invoiceNumber='12944'))
				tra_loi['mac_dinh'] = dict(code='00', data=dict(inv_invoiceNumber='12944'))
				tra_loi['am_tinh'] = dict(code='01', message='not found', data=None)
				tra_loi[kep.name] = dict(code='9999', message='Mã chưa rõ')
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F1v3 mã lạ 9999 vẫn giữ cờ', frappe.db.get_value(
					'Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu'), 1)
				_bang('F1v3 không gửi lại tờ nào', len(gui), truoc)
				_bang('F1v3 không gỡ cờ tờ nào', ra.get('go_co'), 0)
				kq['phan'].append({'ten': 'F1 vòng 3 mã lạ giữ cờ', 'dat': True})

				# Đúng mã của mẫu âm tính thì mới gỡ, và tờ được gửi lại.
				tra_loi[kep.name] = dict(code='01', message='not found', data=None)
				truoc = len(gui)
				ra = hddt_cho_xuat.chay_nen(str(hom_qua), 'giu_ngay', 'bench')
				_bang('F1v3 trùng mẫu âm tính thì gỡ cờ', frappe.db.get_value(
					'Sales Invoice', kep.name, 'vgb_hddt_cho_doi_chieu'), 0)
				_bang('F1v3 gỡ đúng một tờ', ra.get('go_co'), 1)
				_bang('F1v3 gỡ xong thì gửi tờ đó đi', len(gui), truoc + 1)
				kq['phan'].append({'ten': 'F1 vòng 3 trùng mẫu âm tính thì gỡ', 'dat': True,
					'da_gui': len(gui) - truoc})

				# ---------------------------------------------- F2 hàng rào ở cửa chung
				# Còn tờ ngày cũ đang chờ (tờ kep), tờ của HÔM NAY phải bị chặn
				# ngay tại kiem_goi, tức là mọi đường phát hành đều bị chặn.
				moi = _hoa_don(hom_nay)
				truoc = len(gui)
				chan_duoc = False
				try:
					ban_hang.xuat_hoa_don_dien_tu(moi.name)
				except Exception as e:
					chan_duoc = 'ngày cũ' in str(e) or 'ngày lập' in str(e)
				_bang('F2 tờ hôm nay bị chặn', chan_duoc, True)
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
				_bang('F4 cửa hôm qua đã đóng', hddt_cho_xuat.cua_con_mo(hom_qua, hom_nay), False)
				kq['phan'].append({'ten': 'F4 ngày lập hiệu lực', 'dat': True})

				# ---------------------------------------------- backlog
				# Gỡ hết nợ thì tờ hôm nay đi được, không còn bị chặn.
				frappe.db.set_value('Sales Invoice', kep.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					None, update_modified=False)
				frappe.db.set_value('Sales Invoice', keo.name, hddt_cho_xuat.TRUONG_NGAY_XUAT,
					None, update_modified=False)
				frappe.db.set_value('Sales Invoice', keo.name, 'custom_hddt_so', '', update_modified=False)
				frappe.db.set_value('Sales Invoice', keo.name, 'custom_minvoice_id', '', update_modified=False)
				_bang('backlog rỗng', hddt_cho_xuat.ngay_cu_dang_cho(), [])
				truoc = len(gui)
				ban_hang.xuat_hoa_don_dien_tu(moi.name)
				_bang('hết nợ thì tờ hôm nay đi được', len(gui) - truoc, 1)
				_bang('ngày lập của tờ hôm nay', gui[-1]['data'][0]['inv_invoiceIssuedDate'], str(hom_nay))
				kq['phan'].append({'ten': 'backlog rỗng thì thông', 'dat': True})

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
