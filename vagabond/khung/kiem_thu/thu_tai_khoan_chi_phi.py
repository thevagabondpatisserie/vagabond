"""#206: thiếu tài khoản phí không được lọt qua một cửa lưu khác."""
import sys
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import tai_khoan_chi_phi as tk
from vagabond.khung.kiem_thu.nen import ca, dung, la


class Phieu(dict):
	__getattr__ = dict.get


def _phieu(dt='Stock Entry', **dong):
	return Phieu(doctype=dt, docstatus=0, company='TV', purpose='Manufacture',
		work_order='LSX-THU', items=[{'item_code': 'Banh', 't_warehouse': 'Kho'}],
		**{tk.BANG_PHI[dt]: [dict({'idx': 2, 'amount': 100, 'description': 'Bao bì'}, **dong)]})


@contextmanager
def _gia(tai_khoan=None, lien_tuc=1):
	def nem(cau, **kw):
		raise ValueError(cau)
	with patch.dict(sys.modules, {'erpnext': SimpleNamespace(is_perpetual_inventory_enabled=lambda c: lien_tuc)}), patch.object(
		tk, 'frappe', SimpleNamespace(throw=nem, db=SimpleNamespace(get_value=lambda *a, **k: tai_khoan))):
		yield


def _loi(p, *chu):
	try:
		tk.kiem(p)
	except ValueError as e:
		for c in chu:
			dung(c, c in str(e))
	else:
		dung('phải chặn', False)


@ca('206 tài khoản: bốn nghiệp vụ đều chỉ đúng dòng phí bị bỏ trống')
def _():
	with _gia():
		for dt in tk.BANG_PHI:
			_loi(_phieu(dt), 'Dòng 2', 'Bao bì', 'chưa chọn tài khoản', 'chọn tài khoản')
		_loi(_phieu(), 'default_operating_cost_account', 'LSX-THU', 'cấu hình')


@ca('206 tài khoản: chặn mã mất, khác công ty, tài khoản tổng hợp và đã tắt')
def _():
	for du_lieu, cau in [(None, 'không tồn tại'), ({'company': 'KHAC'}, 'thuộc công ty khác'),
		({'company': 'TV', 'is_group': 1}, 'tổng hợp'), ({'company': 'TV', 'disabled': 1}, 'ngừng sử dụng')]:
		with _gia(du_lieu):
			_loi(_phieu(expense_account='TK-SAI'), 'TK-SAI', cau)


@ca('206 tài khoản: giữ nguyên tài khoản đã chọn, không suy 621 hay theo phiếu cũ')
def _():
	with _gia({'company': 'TV', 'is_group': 0, 'disabled': 0}):
		for dt in tk.BANG_PHI:
			p = _phieu(dt, expense_account='TK-HOP-LE')
			cu = repr(p)
			tk.kiem(p, 'before_validate'); tk.kiem(p, 'before_submit')
			la('không sửa chứng từ', repr(p), cu)


@ca('206 tài khoản: chi phí âm, phí triệt tiêu và base_amount vẫn phải kiểm từng dòng')
def _():
	with _gia():
		for dong in [{'amount': -100}, {'amount': 0, 'base_amount': 100}]:
			_loi(_phieu(**dong), 'chưa chọn tài khoản')
		p = _phieu(); p['additional_costs'].append({'amount': -100, 'description': 'Giảm phí'})
		_loi(p, 'Bao bì', 'Giảm phí')


@ca('206 tài khoản: không ép công ty không dùng sổ kho liên tục hoặc chi phí bằng không')
def _():
	with _gia(lien_tuc=0):
		for dt in tk.BANG_PHI: tk.kiem(_phieu(dt))
	with _gia():
		for dt in tk.BANG_PHI: tk.kiem(_phieu(dt, amount=0))
		p = _phieu(); p['items'] = [{'item_code': 'Banh', 's_warehouse': 'Kho'}]
		tk.kiem(p)
		p = _phieu(); p['docstatus'] = 2; tk.kiem(p)


@ca('206 tài khoản: nội dung dòng phí là dữ liệu, không được chèn HTML vào lỗi')
def _():
	with _gia():
		_loi(_phieu(description='<script>'), '&lt;script&gt;')


@ca('206 tài khoản: các cửa Document kiểm trước validate và trước submit')
def _():
	from vagabond.hooks import doc_events
	for dt in tk.BANG_PHI:
		for su_kien in ['before_validate', 'before_submit']:
			loi_goi = doc_events[dt][su_kien]
			if isinstance(loi_goi, str): loi_goi = [loi_goi]
			dung(dt + su_kien, 'vagabond.tai_khoan_chi_phi.kiem' in loi_goi)
