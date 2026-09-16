"""#247: bắt lỗi mã ở tham chiếu, tiền tố và mã lặp trong cùng dòng."""
from unittest.mock import patch
from types import SimpleNamespace

import frappe
from vagabond import ho_so_tt as hs, doi_chieu_app as dc, coc_app
from vagabond.khung.kiem_thu.nen import ca, la, dung


@ca("#247 mã APP trong tham chiếu, dấu phân cách, lặp mã chỉ cộng một lần")
def _ma():
	g = {"name": "BT-1", "description": "APP2609015 APP.26.09.015", "reference_number": "APP2609015", "withdrawal": 100, "date": "2026-09-09"}
	with patch.object(frappe.db, "sql", return_value=[g]):
		r = hs._sepay_theo_ma_app(["APP.26.09.015"])
		la("đúng một dòng 100", r["APP.26.09.015"]["chi"], 100)
		la("giữ khóa bản ghi", r["APP.26.09.015"]["ma_gd"], "BT-1")
		g["description"] = "Thanh toan internet"
		la("chỉ có mã trong tham chiếu vẫn thấy", hs._sepay_theo_ma_app(["APP.26.09.015"])["APP.26.09.015"]["so_gd"], 1)
		g["reference_number"] = "APP26090150"
		la("không ăn tiền tố của mã dài hơn", hs._sepay_theo_ma_app(["APP.26.09.015"]), {})


@ca("#247 một sao kê không đúng chiều, tiền, tài khoản hoặc chủ phải bị từ chối")
def _chan():
	g = SimpleNamespace(name="BT", docstatus=1, deposit=0, withdrawal=100, bank_account="BA", currency="VND", payment_entries=[])
	d = SimpleNamespace(name="APP")
	ba = {"company": "CT", "account": "112", "is_company_account": 1, "disabled": 0}
	with patch.object(frappe.db, "get_value", return_value=ba), patch.object(dc, "_chu_khac", return_value=""):
		la("đủ điều kiện", dc._kiem(g, d, ("CT", "112", 100)), "")
		for truong, gia_tri in (("docstatus", 0), ("deposit", 100), ("withdrawal", 99), ("currency", "USD")):
			cu = getattr(g, truong)
			setattr(g, truong, gia_tri)
			dung("chặn " + truong, bool(dc._kiem(g, d, ("CT", "112", 100))))
			setattr(g, truong, cu)
		dung("khác công ty", bool(dc._kiem(g, d, ("CT-KHAC", "112", 100))))
		dung("khác nguồn chi", bool(dc._kiem(g, d, ("CT", "112-KHAC", 100))))
	with patch.object(frappe.db, "get_value", return_value=ba), patch.object(dc, "_chu_khac", return_value="APP-KHAC"):
		dung("đã có chủ", "APP-KHAC" in dc._kiem(g, d, ("CT", "112", 100)))


@ca("#247 đối chiếu cọc bỏ giới hạn 50 và dùng lại một lần đọc mỗi NCC")
def _doi_chieu_coc_khong_cat_50():
	class Rec:
		def __init__(self):
			self.payments = [SimpleNamespace(reference_type="Payment Entry",
				reference_name="PE-1", amount=3000000,
				as_dict=lambda: {"reference_type": "Payment Entry", "reference_name": "PE-1", "amount": 3000000})]
			self.invoices = []
		def get_unreconciled_entries(self):
			la("bỏ giới hạn hóa đơn trước khi đọc", self.invoice_limit, 0)
			la("bỏ giới hạn phiếu tiền trước khi đọc", self.payment_limit, 0)
	rec = Rec()
	pe = SimpleNamespace(company="CT", party="NCC", paid_to="331", name="PE-1")
	bo_nho = {}
	with patch.object(frappe, "new_doc", return_value=rec, create=True) as tao:
		_, tien = coc_app._doi_chieu(pe, bo_nho)
		coc_app._doi_chieu(pe, bo_nho)
	la("chỉ dựng bộ đối chiếu một lần", tao.call_count, 1)
	la("đọc đúng tiền cọc", tien[0]["amount"], 3000000)


@ca("#328 APP whitelist chung vẫn dùng kiểm nguồn và số tiền của APP")
def _app_danh_sach_chung():
	from vagabond import doi_soat_sepay as dss
	from contextlib import ExitStack
	doc = frappe._dict(name='APP-TEST',ma_giao_dich='')
	ds = [dict(name='DUNG',bank_account='BA',withdrawal=100,tien=100,date='2026-09-16',description=''),
		dict(name='SAI-NGUON',bank_account='CN',withdrawal=100,tien=100,date='2026-09-16',description=''),
		dict(name='SAI-TIEN',bank_account='BA',withdrawal=90,tien=90,date='2026-09-16',description='')]
	with ExitStack() as st:
		st.enter_context(patch.object(dc,'_ho_so',return_value=doc))
		st.enter_context(patch.object(dc,'_nguon',return_value=('CT','112',100)))
		st.enter_context(patch.object(frappe,'get_all',return_value=['BA']))
		st.enter_context(patch.object(frappe,'get_doc',return_value='DOC-GD'))
		kiem=st.enter_context(patch.object(dc,'_kiem',return_value=''))
		st.enter_context(patch.object(dss,'nhan_tai_khoan',return_value=({},[{'ma':'BA'},{'ma':'CN'}],[])))
		st.enter_context(patch.object(dss,'dong_sao_ke',return_value=ds))
		kq=dss.ung_vien('app',doc.name)
		la('không giấu nguồn/tiền sai',len(kq['rows']),3)
		la('duy nhất dòng hợp lệ',[r['name'] for r in kq['rows'] if r['dung_duoc']],['DUNG'])
		la('kiểm đầy đủ dòng hợp lệ',kiem.call_count,1)
		la('Document thật truyền vào kiểm',kiem.call_args.args,('DOC-GD',doc,('CT','112',100)))
