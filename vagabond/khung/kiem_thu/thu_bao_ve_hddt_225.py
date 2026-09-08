"""#225: cửa Document giữ HĐĐT, phép đối chiếu không giấu số dư lẻ."""
import sys
from types import SimpleNamespace
from unittest.mock import patch
from vagabond.bao_ve_hddt import co_dau_hddt, chan_huy
from vagabond.doi_chieu_tang_cu import sau_thay_pkt
from vagabond.khung.kiem_thu.nen import ca, la


@ca("#225: số/ID/trạng thái CQT và chờ đối chiếu đều chặn, phiếu chưa phát hành vẫn huỷ được")
def _dau():
	for o, v in [("custom_hddt_so", "12165"), ("custom_hddt_id", "id"),
		("custom_minvoice_id", "id"), ("custom_hddt_trang_thai", "CQT chấp nhận"),
		("custom_hddt_trang_thai", "Chờ ký"), ("vgb_hddt_cho_doi_chieu", 1)]:
		la(o, co_dau_hddt({o: v}), True)
	la("chưa gửi", co_dau_hddt({"vgb_hddt_cho_doi_chieu": 0}), False)


@ca("#225: payload xoá dấu HĐĐT vẫn bị chặn theo DB trước cancel")
def _db():
	class Phieu(dict):
		doctype = "Sales Invoice"
		name = "SI225"
	class Loi(Exception):
		pass
	def nem(*a, **k):
		raise Loi()
	gia = SimpleNamespace(db=SimpleNamespace(get_value=lambda *a, **k: {"custom_hddt_so": "12165"}), throw=nem)
	with patch.dict(sys.modules, {"frappe": gia}):
		try:
			chan_huy(Phieu())
		except Loi:
			pass
		else:
			raise AssertionError("đã huỷ tờ có số trong DB")
		gia.db.get_value = lambda *a, **k: {}
		chan_huy(Phieu())


@ca("#225: ba dòng PKT làm tròn vẫn còn5111 0,14 và6428 0,01, không được báo doanh thu bằng0")
def _le():
	gl = [{"account_number": tk, "debit": no, "credit": co} for tk, no, co in [
		("131", "10420000", 0), ("5111", 0, "9648148.14"),
		("33311", 0, "771851.85"), ("6428", 0, "0.01")]]
	moi = [{"account_number": tk, "debit": no, "credit": co} for tk, no, co in [
		("5111", 9648148, 0), ("64182", 771852, 0), ("131", 0, 10420000)]]
	la("số dư thực", sau_thay_pkt(gl, moi), {"5111": "-0.14", "33311": "-771851.85",
		"64182": "771852", "6428": "-0.01"})
	try:
		sau_thay_pkt([{"account_number": "131", "debit": "NaN"}], [])
	except ValueError:
		pass
	else:
		raise AssertionError("không được nhận số lỗi")


@ca("#225: thêm cửa bảo vệ không được ghi đè hook chống trùng Pancake")
def _hook():
	import ast
	from pathlib import Path
	tree = ast.parse((Path(__file__).resolve().parents[2] / "hooks.py").read_text())
	for node in ast.walk(tree):
		if isinstance(node, ast.Dict):
			keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
			la("không key hook trùng", len(keys), len(set(keys)))


@ca("#225: không xoá dấu qua save trước rồi cancel ở request sau")
def _xoa_dau():
	from vagabond.bao_ve_hddt import chan_huy_mem
	class Phieu(dict):
		doctype = "Sales Invoice"
		name = "SI225"
	class Loi(Exception):
		pass
	def nem(*a, **k):
		raise Loi()
	gia = SimpleNamespace(db=SimpleNamespace(get_value=lambda *a, **k: {"custom_hddt_so": "12165"}), throw=nem)
	with patch.dict(sys.modules, {"frappe": gia, "frappe.utils": SimpleNamespace(cint=lambda v: int(v or 0))}):
		try:
			chan_huy_mem(Phieu())
		except Loi:
			pass
		else:
			raise AssertionError("đã xoá dấu trước khi huỷ")
		chan_huy_mem(Phieu(custom_hddt_so="12165"))


@ca("#225: sáu dòng gồm chênh lệch được duyệt đưa doanh thu và6428 về0, VAT khớp771852")
def _sau_le():
	from vagabond.doi_chieu_tang_cu import dong_pkt_sua
	gl = [{"account_number": tk, "debit": no, "credit": co} for tk, no, co in [
		("131", "10420000", 0), ("5111", 0, "9648148.14"),
		("33311", 0, "771851.85"), ("6428", 0, "0.01")]]
	moi = [{"account_number": tk, "debit": no, "credit": co} for tk, no, co in dong_pkt_sua()]
	la("chỉ cònVAT", sau_thay_pkt(gl, moi), {"33311": "-771852.00", "64182": "771852"})
