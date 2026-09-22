"""Ba lỗi anh Việt báo 22/09/2026, gộp vào v518.

1. HT-2026-02900: hoàn 90.000 cho đơn HDB-26-09-03237 (tổng hàng 570.000,
   chiết khấu tổng 135.000, khách trả 435.000). Tiền đã ra, đã khớp sao kê,
   nhưng tờ trả hàng không sinh được: "Số tiền CK bổ sung (-135.000) không
   thể vượt tổng trước CK (-117.930,96)".
2. APP-26-09-799: đính uỷ nhiệm chi trên app rồi bấm xác nhận vẫn báo
   "Chưa đính uỷ nhiệm chi" (màn gửi [null] lên máy chủ, xem
   hanh_vi/unc_app_518.js).
3. Cùng phiếu đó: ngân hàng đã chi 5.580.000 với nội dung
   "MBCT VAGABOND TT HD 1840 APP 26 09 799 PHUC AN" mà máy báo 0 đ, vì chữ
   số 0 của "1840" đứng sát chữ A của mã sau khi gọt khoảng trắng.
"""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khop_sao_ke import co_ma
from vagabond.hoan_tien import ty_le_ha_gia

GOC = Path(__file__).resolve().parents[2]
MA_HT = (GOC / "hoan_tien.py").read_text()


@ca("APP-26-09-799: nội dung chuyển khoản có số đứng sát trước mã APP vẫn khớp")
def _app_sat_so():
	mo = "MBCT VAGABOND TT HD 1840 APP 26 09 799 PHUC AN D26VB73Q/886002"
	dung("dòng sao kê thật khớp mã phiếu", co_ma(mo, "APP-26-09-799"))
	dung("mã hoá đơn bán mở đầu bằng chữ cũng vậy", co_ma("HOAN 12HDB-26-09-03237", "HDB-26-09-03237"))
	# Phía cuối mã là chữ số thì vẫn chặn: APP26080 không được dính vào APP2608027.
	dung("mã ngắn không dính vào mã dài hơn", not co_ma("TT APP 26 08 027", "APP-26-08-0"))
	# Mã mở đầu bằng chữ số (đơn Pancake 5 số) vẫn chặn hai đầu như cũ.
	dung("mã số không dính vào số dài hơn", not co_ma("CK 192252 KHACH", "92252"))
	dung("mã số đứng riêng vẫn khớp", co_ma("CK 92252 KHACH", "92252"))


@ca("HT-2026-02900: hoàn một phần trên đơn có chiết khấu tổng, tỷ lệ tính trên tổng trước chiết khấu")
def _ty_le():
	ty, bo = ty_le_ha_gia(90000, 435000 + 135000, 435000)
	la("tỷ lệ 90.000 trên 570.000", ty, 90000 / 570000)
	la("bỏ chiết khấu tổng", bo, True)
	la("hoàn đủ đơn thì chép nguyên", ty_le_ha_gia(435000, 570000, 435000), (1.0, False))
	la("đơn không chiết khấu: như cũ", ty_le_ha_gia(50000, 200000, 200000), (0.25, True))


class _Dong(SimpleNamespace):
	def get(self, k, m=None):
		return getattr(self, k, m)


class _Tra(SimpleNamespace):
	def get(self, k, m=None):
		return getattr(self, k, m)

	def set(self, k, v):
		setattr(self, k, v)

	def run_method(self, ten, *a, **k):
		"""Như ERPNext tính lại tiền: thuế gồm trong giá hay cộng thêm, chiết
		khấu đặt trên Tổng sau thuế hay Tổng trước thuế, mỗi kiểu một số."""
		if ten != "calculate_taxes_and_totals":
			return None
		r = float(getattr(self, "thue_suat", 0) or 0) / 100.0
		tong = sum(d.qty * d.rate for d in self.items)
		self.tong_hang = tong
		if getattr(self, "thue_trong_gia", 1):
			net0, grand0 = tong / (1 + r), tong
		else:
			net0, grand0 = tong, tong * (1 + r)
		ck = float(self.discount_amount or 0)
		if getattr(self, "apply_discount_on", "Grand Total") == "Grand Total":
			self.grand_total = grand0 - ck
		else:
			self.grand_total = (net0 - ck) * (1 + r)
		return None

	def insert(self, **k):
		# Đúng phép ERPNext làm ở validate: chiết khấu tổng không vượt tổng trước chiết khấu.
		self.run_method("calculate_taxes_and_totals")
		tong = self.tong_hang
		if abs(self.discount_amount or 0) > abs(tong) + 0.005:
			raise ValueError("Số tiền CK bổ sung (%s) không thể vượt tổng trước CK (%.2f)" % (self.discount_amount, tong))

	def submit(self):
		pass


def _chay(tien, tren="Grand Total", thue=8, trong_gia=1, ck=135000, grand=435000):
	# Mặc định: đơn HDB-26-09-03237 đúng số liệu trên site 22/09/2026.
	si = _Dong(name="HDB-26-09-03237", grand_total=grand, total=570000, discount_amount=ck, items=[
		_Dong(qty=18, rate=25000), _Dong(qty=2, rate=20000), _Dong(qty=1, rate=20000), _Dong(qty=1, rate=60000)])
	tra = _Tra(items=[_Dong(qty=-d.qty, rate=d.rate, price_list_rate=d.rate, discount_amount=0, discount_percentage=0)
		for d in si.items], discount_amount=-ck, additional_discount_percentage=0,
		apply_discount_on=tren, thue_suat=thue, thue_trong_gia=trong_gia,
		meta=SimpleNamespace(has_field=lambda o: False), flags=SimpleNamespace())
	sys.modules["erpnext.accounts.doctype.sales_invoice.sales_invoice"] = SimpleNamespace(make_sales_return=lambda n: tra)
	ham = [n for n in ast.parse(MA_HT).body if isinstance(n, ast.FunctionDef)
		and n.name in ("_lap_hoa_don_tra", "ty_le_ha_gia", "_nan_dung_tien")]
	from frappe.utils import flt
	env = dict(flt=flt, nowdate=lambda: "2026-09-22", frappe=SimpleNamespace(throw=_nem))
	exec(compile(ast.Module(body=ham, type_ignores=[]), "hoan_tien.py", "exec"), env)
	return env["_lap_hoa_don_tra"](si, "Kho Hàng Hủy - TV", "Khác", "HT-2026-02900", tien)


def _nem(m, *a, **k):
	raise ValueError(m)


@ca("HT-2026-02900: tờ trả hàng hoàn 90.000 sinh được và ra đúng 90.000")
def _tra_mot_phan():
	tra = _chay(90000)
	la("không còn chiết khấu tổng", tra.discount_amount, 0)
	la("tổng tờ trả đúng số tiền hoàn", round(abs(tra.grand_total), 2), 90000.0)


@ca("Codex #358: chiết khấu đặt trên Tổng trước thuế, thuế cộng thêm: tờ trả vẫn ra đúng tiền hoàn")
def _tra_ck_net():
	tra = _chay(90000, tren="Net Total", thue=8, trong_gia=0)
	la("không còn chiết khấu tổng", tra.discount_amount, 0)
	la("tổng tờ trả đúng số tiền hoàn", round(abs(tra.grand_total), 2), 90000.0)
	tra2 = _chay(200000, tren="Net Total", thue=10, trong_gia=0, ck=50000, grand=520000)
	la("kiểu khác cũng đúng", round(abs(tra2.grand_total), 2), 200000.0)


@ca("HT: hoàn đủ đơn có chiết khấu tổng vẫn chép nguyên chiết khấu như đơn gốc")
def _tra_du():
	tra = _chay(435000)
	la("giữ chiết khấu", tra.discount_amount, -135000)
	la("giữ nguyên đơn giá", round(sum(d.qty * d.rate for d in tra.items), 2), -570000.0)
