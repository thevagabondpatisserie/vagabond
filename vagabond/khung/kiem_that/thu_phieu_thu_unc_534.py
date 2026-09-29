"""v534 (#380): ghi sổ phiếu thu kèm uỷ nhiệm chi khách gửi, trên sổ cái thật.

Codex #381 F3: đổi điều kiện ghi sổ Payment Entry là chạm thẳng sổ cái, ca
thuần không chạy validation của ERPNext, không chứng minh được phiếu thu vào
sổ thật, không bắt được ghi tiền hai lần. Các ca dưới dựng SI, Bank
Transaction, Payment Entry nháp THẬT trong điểm lưu, gọi đúng cửa mà màn
Công nợ gọi, rồi đọc lại GL, dư nợ hoá đơn và giao dịch ngân hàng.
"""
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.utils import today

from vagabond import thu_tien as tt
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon, _app
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi

TIEN = 1000000


def _du_lieu():
	"""SI đã ghi sổ còn nợ đủ, giao dịch ngân hàng tiền vào, phiếu thu nháp."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	cty, tk, _mau = _nen()
	si = _app(cty, [dict(item_code=_mon(tk), qty=1, rate=TIEN)])
	si.vgb_tam_tinh = 0
	si.vgb_pt_thanh_toan = 'GrabFood'
	si.vgb_ma_tham_chieu = 'KT534-' + frappe.generate_hash(length=8)
	si.save(ignore_permissions=True)
	si.submit(); si.reload()
	# Tài khoản sổ cái số hiệu 112 như site thật: hai hook ghi sổ (tệp đính
	# kèm chung và UNC khách gửi) chỉ soi tài khoản ngân hàng theo số hiệu,
	# tài khoản Bank mặc định của bench không mang 112 nên sẽ lọt hook.
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	tk_gl = frappe.db.get_value('Bank Account', ba, 'account')
	dung('tài khoản thử là 112', str(tk_gl).startswith('112'))
	ref = 'FTKT534' + frappe.generate_hash(length=10)
	g = frappe.get_doc({
		'doctype': 'Bank Transaction', 'date': today(), 'bank_account': ba,
		'deposit': si.grand_total, 'withdrawal': 0, 'currency': 'VND',
		'description': 'KT534 khach chuyen', 'reference_number': ref, 'transaction_id': ref,
	})
	g.insert(ignore_permissions=True); _DA_TAO.append((g.doctype, g.name))
	g.submit()
	pe = get_payment_entry('Sales Invoice', si.name, party_amount=si.grand_total, bank_account=tk_gl)
	pe.reference_no = ref
	pe.reference_date = today()
	pe.insert(ignore_permissions=True); _DA_TAO.append((pe.doctype, pe.name))
	la('phiếu thu nháp về đúng tài khoản giao dịch', pe.paid_to, tk_gl)
	return si, g, pe


class _Tep:
	"""Tệp UNC thử; dọn cả bản ghi lẫn tệp trên đĩa dù ca có ném lỗi.

	Savepoint không chạy after_rollback của File (Frappe f33ac3f), cùng
	cách dọn với ca #265.
	"""

	def __init__(self, gan_vao=None, vao_o=False):
		self.gan_vao = gan_vao
		# vao_o: ghi luôn tệp vào ô UNC khách gửi của phiếu, như người dùng
		# đã đính đúng chỗ từ trước. Không bật thì tệp chỉ gắn vào phiếu,
		# như một ảnh bất kỳ ở mục khác (Codex #382).
		self.vao_o = vao_o
		self.tep = None

	def __enter__(self):
		d = dict(doctype='File', file_name='KT534-unc-khach.txt', is_private=1,
			content='UNC khach gui KT534 ' + frappe.generate_hash(length=16))
		if self.gan_vao:
			d.update(attached_to_doctype='Payment Entry', attached_to_name=self.gan_vao)
		self.tep = frappe.get_doc(d)
		self.tep.insert(ignore_permissions=True); _DA_TAO.append((self.tep.doctype, self.tep.name))
		if self.gan_vao and self.vao_o:
			from vagabond import tep_dinh_kem
			frappe.db.set_value('Payment Entry', self.gan_vao, 'vgb_thu_unc',
				tep_dinh_kem.ghi_ds([self.tep.file_url]), update_modified=False)
		return self.tep

	def __exit__(self, *a):
		t = self.tep
		if t and t.name and frappe.db.exists('File', t.name):
			duong = Path(t.get_full_path())
			t.delete(ignore_permissions=True)
			dung('tệp UNC thử đã dọn trên đĩa', not duong.exists())
		elif t is not None and t.flags.new_file:
			t.on_rollback()
		return False


def _gl(pe):
	return sorted(
		(x.account, x.party_type or '', float(x.debit), float(x.credit))
		for x in frappe.get_all('GL Entry', filters={'voucher_type': 'Payment Entry', 'voucher_no': pe.name, 'is_cancelled': 0},
			fields=['account', 'party_type', 'debit', 'credit']))


@ca('#380 v534 phiếu thu nháp khớp giao dịch: xác minh ra đúng, tách khỏi nợ')
def _xac_minh():
	si, g, pe = _du_lieu()
	ds = [p for p in tt.phieu_thu_nhap(cac_si=[si.name]) if p['pe'] == pe.name]
	la('đọc ra đúng một phiếu', len(ds), 1)
	la('đã xác minh', ds[0]['da_xac_minh'], 1)
	la('đúng giao dịch', ds[0]['gd'], g.name)
	la('phân bổ đúng hoá đơn', ds[0]['hd'], [(si.name, float(si.grand_total))])


@ca('#380 v534 đính UNC khách gửi rồi ghi sổ: GL hai dòng, hết nợ, giao dịch nối đúng phiếu, bấm lại không ghi hai lần')
def _ghi_so():
	si, g, pe = _du_lieu()
	with _Tep() as t:
		kq = tt.ghi_so_phieu_thu(pe.name, unc=[t.file_url])
		la('ghi sổ được', kq.get('ok'), 1)
		pe.reload(); si.reload(); g.reload()
		la('phiếu vào sổ', pe.docstatus, 1)
		la('tệp gắn vào phiếu', frappe.db.get_value('File', t.name, 'attached_to_name'), pe.name)
		dung('ô UNC khách gửi ghi đúng tệp', t.file_url in (pe.get('vgb_thu_unc') or ''))
		la('GL đúng hai dòng', _gl(pe), sorted([(pe.paid_to, '', float(TIEN), 0.0), (si.debit_to, 'Customer', 0.0, float(TIEN))]))
		la('hoá đơn hết nợ', float(si.outstanding_amount), 0.0)
		la('giao dịch nối đúng phiếu', [r.payment_entry for r in g.payment_entries], [pe.name])
		la('giao dịch hết tiền chưa phân bổ', float(g.unallocated_amount), 0.0)
		kq2 = tt.ghi_so_phieu_thu(pe.name)
		la('bấm lại trả đã làm rồi', kq2.get('da_lam_roi'), 1)
		la('vẫn chỉ hai dòng GL', len(_gl(pe)), 2)


@ca('#380 v534 thiếu UNC khách gửi thì không ghi sổ, phiếu giữ nháp')
def _thieu_unc():
	si, g, pe = _du_lieu()
	try:
		tt.ghi_so_phieu_thu(pe.name)
	except frappe.ValidationError as e:
		dung('câu nói thiếu uỷ nhiệm chi', 'uỷ nhiệm chi' in str(e))
	else:
		dung('phải chặn khi thiếu UNC', False)
	pe.reload(); si.reload()
	la('phiếu còn nháp', pe.docstatus, 0)
	la('không GL', _gl(pe), [])
	la('hoá đơn còn nợ', float(si.outstanding_amount), float(TIEN))


@ca('#380 v534 Codex #382: ảnh bất kỳ gắn vào phiếu mà ô UNC khách gửi trống thì KHÔNG ghi sổ')
def _tep_khac_muc():
	si, g, pe = _du_lieu()
	with _Tep(gan_vao=pe.name):
		la('ô UNC trống', frappe.db.get_value('Payment Entry', pe.name, 'vgb_thu_unc') or '', '')
		ds = [p for p in tt.phieu_thu_nhap(cac_si=[si.name]) if p['pe'] == pe.name]
		la('màn Tiền đã về không đếm tệp mục khác', ds[0]['so_tep'], 0)
		try:
			tt.ghi_so_phieu_thu(pe.name)
		except frappe.ValidationError as e:
			dung('câu nói thiếu uỷ nhiệm chi', 'uỷ nhiệm chi' in str(e))
		else:
			dung('phải chặn khi ô UNC trống', False)
		pe.reload(); si.reload()
		la('phiếu còn nháp', pe.docstatus, 0)
		la('không GL', _gl(pe), [])
		la('hoá đơn còn nợ', float(si.outstanding_amount), float(TIEN))


@ca('#380 v534 Codex #382 vòng 2: một giao dịch có hai phiếu nháp cho hai hoá đơn thì chỉ một hoá đơn sang Tiền đã về')
def _mot_gd_hai_hd():
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	si, g, pe = _du_lieu()
	cty, tk, _mau = _nen()
	si2 = _app(cty, [dict(item_code=_mon(tk), qty=1, rate=TIEN)])
	si2.vgb_tam_tinh = 0
	si2.vgb_pt_thanh_toan = 'GrabFood'
	si2.vgb_ma_tham_chieu = 'KT534B-' + frappe.generate_hash(length=8)
	si2.save(ignore_permissions=True)
	si2.submit(); si2.reload()
	pe2 = get_payment_entry('Sales Invoice', si2.name, party_amount=si2.grand_total, bank_account=pe.paid_to)
	pe2.reference_no = pe.reference_no
	pe2.reference_date = today()
	pe2.insert(ignore_permissions=True); _DA_TAO.append((pe2.doctype, pe2.name))
	ds = [p for p in tt.phieu_thu_nhap(cac_si=[si.name, si2.name]) if p['pe'] in (pe.name, pe2.name)]
	la('đọc ra hai phiếu', len(ds), 2)
	la('chỉ một phiếu được tính là đã xác minh', sum(p['da_xac_minh'] for p in ds), 1)
	g2 = tt.gom_tien_da_ve(ds)
	tach = [x for x in (si.name, si2.name) if x in g2 and tt.tach_tien_da_ve(float(TIEN), g2[x]['phan_bo'], 1)]
	la('một lần tiền về chỉ tách một hoá đơn', len(tach), 1)
	# Đọc riêng từng hoá đơn vẫn ra cùng một phiếu thắng.
	rieng = [p for c in (si.name, si2.name) for p in tt.phieu_thu_nhap(cac_si=[c]) if p['da_xac_minh']]
	la('đọc từng hoá đơn vẫn chỉ một phiếu thắng', len(rieng), 1)


@ca('#380 v534 Codex #382 vòng 3: phiếu thu có mã giao dịch mà không gắn hoá đơn thì không vào Tiền đã về, không thắng phiếu công nợ')
def _khong_hd():
	si, g, pe = _du_lieu()
	le = frappe.copy_doc(pe)
	le.references = []
	le.reference_no = pe.reference_no
	le.paid_amount = le.received_amount = float(TIEN) * 2
	le.insert(ignore_permissions=True); _DA_TAO.append((le.doctype, le.name))
	ds = tt.phieu_thu_nhap()
	dung('phiếu không gắn hoá đơn không hiện', all(p['pe'] != le.name for p in ds))
	cua_si = [p for p in tt.phieu_thu_nhap(cac_si=[si.name]) if p['pe'] == pe.name]
	la('phiếu công nợ thật vẫn đã xác minh dù phiếu lẻ lớn hơn', cua_si[0]['da_xac_minh'], 1)


@ca('#380 v534 anh Việt 29/09: ghi sổ thẳng trên Desk cũng phải có tệp trong ô UNC khách gửi')
def _desk():
	si, g, pe = _du_lieu()
	with _Tep(gan_vao=pe.name) as t:
		# Đường Desk: tệp bất kỳ bằng nút kẹp giấy, bấm Ghi sổ (submit thẳng).
		try:
			pe.reload(); pe.submit()
		except frappe.ValidationError as e:
			dung('câu nói thiếu uỷ nhiệm chi khách gửi', 'uỷ nhiệm chi' in str(e) and 'khách gửi' in str(e))
		else:
			dung('Desk phải bị chặn khi ô UNC khách gửi trống', False)
		pe.reload()
		la('phiếu còn nháp', pe.docstatus, 0)
		la('không GL', _gl(pe), [])
		# Đính đúng ô trên Desk rồi lưu: tệp gộp vào ô danh sách, ghi sổ được.
		pe.vgb_thu_unc_tep = t.file_url
		pe.save(ignore_permissions=True); pe.reload()
		dung('tệp Desk gộp vào ô UNC khách gửi', t.file_url in (pe.get('vgb_thu_unc') or ''))
		pe.submit(); pe.reload()
		la('ghi sổ được sau khi đính đúng ô', pe.docstatus, 1)
		la('GL hai dòng', len(_gl(pe)), 2)


@ca('#380 v534 Codex #382 vòng 4: phiếu thu không thuộc màn công nợ thì nút đính UNC từ chối, không gắn tệp')
def _ngoai_tap():
	si, g, pe = _du_lieu()
	le = frappe.copy_doc(pe)
	le.references = []
	le.insert(ignore_permissions=True); _DA_TAO.append((le.doctype, le.name))
	with _Tep() as t:
		try:
			tt.ghi_so_phieu_thu(le.name, unc=[t.file_url])
		except frappe.ValidationError as e:
			dung('câu nói không phải phiếu thu công nợ', 'không phải phiếu thu' in str(e))
		else:
			dung('phải từ chối phiếu ngoài tập', False)
		la('tệp không bị gắn vào phiếu', frappe.db.get_value('File', t.name, 'attached_to_name') or '', '')
		la('ô UNC của phiếu vẫn trống', frappe.db.get_value('Payment Entry', le.name, 'vgb_thu_unc') or '', '')


@ca('#380 v534 giao dịch đã nối chứng từ khác thì chặn, không ghi tiền hai lần')
def _da_noi():
	si, g, pe = _du_lieu()
	# Giao dịch đã bị ai đó phân bổ một phần: phiếu thu không còn khớp.
	frappe.db.set_value('Bank Transaction', g.name, {'allocated_amount': 1, 'unallocated_amount': float(TIEN) - 1},
		update_modified=False)
	with _Tep(gan_vao=pe.name, vao_o=True):
		try:
			tt.ghi_so_phieu_thu(pe.name)
		except frappe.ValidationError as e:
			dung('câu nói giao dịch đã nối', 'đã nối' in str(e) or 'chưa phân bổ' in str(e))
		else:
			dung('phải chặn giao dịch đã nối', False)
		pe.reload()
		la('phiếu còn nháp', pe.docstatus, 0)
		la('không GL', _gl(pe), [])


@ca('#380 v534 hỏng sau khi phiếu đã submit: lùi sạch cả lượt, thử lại được')
def _hong_giua():
	from erpnext.accounts.doctype.bank_transaction.bank_transaction import BankTransaction

	si, g, pe = _du_lieu()
	with _Tep(gan_vao=pe.name, vao_o=True):
		def hong(self, *a, **k):
			raise ValueError('KT534 hỏng khi nối giao dịch')
		with patch.object(BankTransaction, 'add_payment_entries', hong):
			try:
				tt.ghi_so_phieu_thu(pe.name)
			except ValueError:
				pass
			else:
				dung('phải ném lỗi khi nối hỏng', False)
		pe.reload(); si.reload(); g.reload()
		la('phiếu lùi về nháp', pe.docstatus, 0)
		la('không còn GL dở', _gl(pe), [])
		la('hoá đơn còn nguyên nợ', float(si.outstanding_amount), float(TIEN))
		la('giao dịch chưa nối', len(g.payment_entries or []), 0)
		kq = tt.ghi_so_phieu_thu(pe.name)
		la('thử lại ghi sổ được', kq.get('ok'), 1)
		pe.reload()
		la('một lần vào sổ', (pe.docstatus, len(_gl(pe))), (1, 2))


@ca('#380 v534 chẩn đoán ghi sổ chỉ đọc: báo đúng lỗi thiếu tệp nếu có, không đổi phiếu, không sinh GL')
def _chan_doan():
	si, g, pe = _du_lieu()
	kq = tt.chan_doan_ghi_so(pe.name)
	pe.reload()
	la('phiếu còn nháp', pe.docstatus, 0)
	la('không GL', _gl(pe), [])
	dung('trả về có khoá qua hoặc loi', 'qua' in kq and 'loi' in kq)
