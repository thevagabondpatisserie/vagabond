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
	ba = _tk_ngan_hang(cty)
	tk_gl = frappe.db.get_value('Bank Account', ba, 'account')
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

	def __init__(self, gan_vao=None):
		self.gan_vao = gan_vao
		self.tep = None

	def __enter__(self):
		d = dict(doctype='File', file_name='KT534-unc-khach.txt', is_private=1,
			content='UNC khach gui KT534 ' + frappe.generate_hash(length=16))
		if self.gan_vao:
			d.update(attached_to_doctype='Payment Entry', attached_to_name=self.gan_vao)
		self.tep = frappe.get_doc(d)
		self.tep.insert(ignore_permissions=True); _DA_TAO.append((self.tep.doctype, self.tep.name))
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


@ca('#380 v534 giao dịch đã nối chứng từ khác thì chặn, không ghi tiền hai lần')
def _da_noi():
	si, g, pe = _du_lieu()
	# Giao dịch đã bị ai đó phân bổ một phần: phiếu thu không còn khớp.
	frappe.db.set_value('Bank Transaction', g.name, {'allocated_amount': 1, 'unallocated_amount': float(TIEN) - 1},
		update_modified=False)
	with _Tep(gan_vao=pe.name):
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
	with _Tep(gan_vao=pe.name):
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
