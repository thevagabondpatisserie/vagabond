"""#247: bắt lỗi mã ở tham chiếu, tiền tố và mã lặp trong cùng dòng."""
from unittest.mock import patch
from types import SimpleNamespace

import frappe
from vagabond import ho_so_tt as hs, doi_chieu_app as dc
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
