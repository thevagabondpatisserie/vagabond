# -*- coding: utf-8 -*-
"""v630: bánh sỉ trên web cho quán, khách sạn, nhà hàng (anh Việt chốt 02/11/2026).

Các ca chạy phép THẬT của banh_si.py, ung_truoc_don.py, cong_no.py trên Frappe
giả của nen.py. Chốt những điều tiền và quyền:
  1. giá là giá RIÊNG của khách, đọc ở MỘT hàm, chỉ từ bảng giá riêng; món
     không có giá riêng thì khách không thấy, không đặt được; giá trình duyệt
     gửi bị bỏ qua;
  2. ngày giao sớm nhất = ngày đặt + 3;
  3. công nợ (hạn +15, không cấn ứng trước) và trả trước (cấn ĐÚNG phiếu thu
     đã ghi sổ của đơn) rẽ đúng nhánh ở bước giao hàng;
  4. phiên Guest: hàm khách không đi qua cổng quyền nhân viên, hàm nhân viên
     chặn Guest, bếp không thấy tiền;
  5. đăng ký kiểm ở cửa nhập; "đặt lại như đơn trước" lấy giá hôm nay.
Ca hành vi node của trang Vue và hai màn app chạy ở cuối tệp.
"""

import ast
import contextlib
import json
import re
import subprocess
import sys
import types
from datetime import date
from pathlib import Path
from unittest import mock

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import banh_si as bs  # noqa: E402
from vagabond import ung_truoc_don as utd  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
HOM = "2026-11-02"


def _ip(ma, gia, tu="2026-10-01", den=None, sua="2026-10-01 10:00:00", ten="IP-1"):
	return _fr._dict(name=ten, item_code=ma, price_list_rate=gia, valid_from=tu, valid_upto=den, modified=sua, uom="Cái")


BANG = {"BANU00001": {"gia": 28000, "ten": "Croissant bơ"}, "BANU00002": {"gia": 32000, "ten": "Pain au chocolat"}}


# ------------------------------------------------------------ giá riêng

@ca("v630 bánh sỉ giá riêng: dòng đang áp hôm nay, dòng bắt đầu muộn nhất thắng, dòng hết hạn, chưa tới, giá 0 bị bỏ")
def _chon_gia():
	rows = [_ip("A", 30000, "2026-10-01", ten="A1"), _ip("A", 31000, "2026-10-20", ten="A2"),
		_ip("B", 50000, "2026-10-01", "2026-11-01", ten="B1"), _ip("C", 40000, "2026-11-03", ten="C1"),
		_ip("D", 0, "2026-10-01", ten="D1"), _ip("E", 20000, "2026-11-02", "2026-11-02", ten="E1")]
	ra = bs.chon_gia(rows, HOM)
	la("món đang áp", sorted(ra), ["A", "E"])
	la("bắt đầu muộn nhất thắng", ra["A"].name, "A2")
	la("cùng ngày bắt đầu thì dòng sửa sau thắng", bs.chon_gia([_ip("A", 1, sua="2026-10-01 09:00", ten="X"),
		_ip("A", 2, sua="2026-10-02 09:00", ten="Y")], HOM)["A"].name, "Y")


@ca("v630 bánh sỉ giá riêng: MỘT hàm gia_cua_khach chỉ đọc bảng giá riêng của đúng khách, món ngừng bán bị bỏ")
def _gia_cua_khach():
	hoi = []

	def get_all(dt, filters=None, **k):
		hoi.append((dt, dict(filters or {})))
		if dt == "Item Price":
			return [_ip("BANU00001", 28000, ten="P1"), _ip("BANU00009", 15000, ten="P9"), _ip("BANU00002", 32000, ten="P2")]
		if dt == "Item":
			ten = (filters or {}).get("name", ["in", []])[1]
			return [_fr._dict(name=m, item_name="Bánh " + m, image="/files/%s.jpg" % m, stock_uom="Cái", item_group="Bánh mì")
				for m in ten if m != "BANU00009"]
		return []
	with mock.patch.object(_fr, "get_all", get_all):
		ra = bs.gia_cua_khach("SI00012", HOM)
	ip = [f for dt, f in hoi if dt == "Item Price"][0]
	la("đọc đúng bảng giá riêng", ip.get("price_list"), bs.BANG_GIA)
	la("đọc đúng khách", ip.get("customer"), "SI00012")
	dung("bảng giá riêng không phải bảng giá bán mặc định", bs.BANG_GIA not in ("Standard Selling", "Bán tại tiệm"))
	it = [f for dt, f in hoi if dt == "Item"][0]
	la("chỉ món đang bán, không biến thể", (it.get("disabled"), it.get("is_sales_item"), it.get("has_variants")), (0, 1, 0))
	la("món ngừng bán không hiện", sorted(ra), ["BANU00001", "BANU00002"])
	la("giá đúng", (ra["BANU00001"]["gia"], ra["BANU00002"]["gia"]), (28000.0, 32000.0))
	with mock.patch.object(_fr, "get_all", lambda dt, **k: []):
		la("khách chưa có giá riêng thì không có món nào", bs.gia_cua_khach("SI00099", HOM), {})
	la("không có khách thì rỗng", bs.gia_cua_khach("", HOM), {})


@ca("v630 bánh sỉ giá riêng: không mô đun nào khác đọc bảng giá riêng; trang khách, lập đơn, màn Sales đều đi qua gia_cua_khach")
def _mot_nguon_gia():
	s = (GOC / "vagabond/banh_si.py").read_text(encoding="utf-8")
	cay = ast.parse(s)
	ham = {f.name: ast.unparse(f) for f in cay.body if isinstance(f, ast.FunctionDef)}
	for t in ("toi", "dat", "bang_gia"):
		dung(t + " đọc giá qua gia_cua_khach", "gia_cua_khach(" in ham[t])
	la("chỉ _dong_gia đọc Item Price của bảng riêng", sorted(t for t, m in ham.items() if "'Item Price', filters" in m), ["_dong_gia"])
	for p in (GOC / "vagabond").glob("*.py"):
		if p.name in ("banh_si.py",):
			continue
		dung(p.name + " không chạm bảng giá riêng", "Giá sỉ theo khách" not in p.read_text(encoding="utf-8") and "BANG_GIA_SI" not in p.read_text(encoding="utf-8"))


@ca("v630 bánh sỉ giá Sales gõ: số nguyên dương có trần, gõ kiểu 28.000 hay 28000đ đều nhận, chữ hay 0 bị chặn")
def _chuan_gia():
	la("có chấm", bs.chuan_gia("28.000"), 28000)
	la("có đ", bs.chuan_gia("28000đ"), 28000)
	la("số", bs.chuan_gia(32000), 32000)
	for x in ("0", "-5", "abc", "", None, "99999999999", str(bs.GIA_TOI_DA + 1)):
		nem("giá %r" % (x,), lambda x=x: bs.chuan_gia(x), ValueError)


# ------------------------------------------------------------ đơn

def _raw(**k):
	d = {"ngay": "2026-11-05", "dong": [{"ma": "BANU00001", "sl": 30}, {"ma": "BANU00002", "sl": 20}], "ghi_chu": "Giao trước 7 giờ"}
	d.update(k)
	return d


@ca("v630 bánh sỉ đơn: giá và tổng trình duyệt gửi bị bỏ qua, giá lấy từ bảng giá riêng máy chủ, cùng món cộng dồn")
def _gia_may_chu():
	don = bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": 30, "gia": 1, "tien": 1}, {"ma": "BANU00002", "sl": "20", "gia": 0},
		{"ma": "BANU00001", "sl": 10}], tong=5, gia=5), BANG, HOM)
	la("dòng", [(d["ma"], d["sl"], d["gia"], d["tien"]) for d in don["dong"]],
		[("BANU00001", 40, 28000.0, 1120000.0), ("BANU00002", 20, 32000.0, 640000.0)])
	la("tổng máy chủ", don["tong"], 1760000.0)
	la("số lượng 0 bỏ qua", bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": 0}, {"ma": "BANU00002", "sl": 1}]), BANG, HOM)["tong"], 32000.0)


@ca("v630 bánh sỉ đơn: món không có giá riêng của khách (mã lạ gửi thẳng) bị chặn; đơn rỗng, số âm, quá trần, số lẻ bị chặn")
def _mon_an():
	nem("mã lạ", lambda: bs.chuan_don(_raw(dong=[{"ma": "BANU00099", "sl": 5}]), BANG, HOM), ValueError)
	nem("mã của bảng giá khác", lambda: bs.chuan_don(_raw(), {"BANU00001": BANG["BANU00001"]}, HOM), ValueError)
	nem("rỗng", lambda: bs.chuan_don(_raw(dong=[]), BANG, HOM), ValueError)
	nem("toàn số 0", lambda: bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": 0}]), BANG, HOM), ValueError)
	nem("âm", lambda: bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": -3}]), BANG, HOM), ValueError)
	nem("số lẻ", lambda: bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": "2.5"}]), BANG, HOM), ValueError)
	nem("quá trần", lambda: bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": bs.SL_TOI_DA + 1}]), BANG, HOM), ValueError)
	nem("cộng dồn quá trần", lambda: bs.chuan_don(_raw(dong=[{"ma": "BANU00001", "sl": bs.SL_TOI_DA}, {"ma": "BANU00001", "sl": 1}]), BANG, HOM), ValueError)
	nem("ghi chú quá dài", lambda: bs.chuan_don(_raw(ghi_chu="x" * 501), BANG, HOM), ValueError)


@ca("v630 bánh sỉ ngày giao: sớm nhất ngày đặt + 3 (giờ Việt Nam), xa nhất 60 ngày sau đó, sai dạng bị chặn")
def _ngay():
	la("sớm nhất", bs.ngay_som_nhat(HOM), date(2026, 11, 5))
	nem("đặt + 2 bị chặn", lambda: bs.chuan_don(_raw(ngay="2026-11-04"), BANG, HOM), ValueError)
	la("đặt + 3 nhận", bs.chuan_don(_raw(ngay="2026-11-05"), BANG, HOM)["ngay"], "2026-11-05")
	la("qua tháng", str(bs.ngay_som_nhat("2026-11-29")), "2026-12-02")
	nem("quá 60 ngày", lambda: bs.chuan_don(_raw(ngay="2027-01-05"), BANG, HOM), ValueError)
	nem("sai dạng", lambda: bs.chuan_don(_raw(ngay="05/11/2026"), BANG, HOM), ValueError)
	nem("thiếu ngày", lambda: bs.chuan_don(_raw(ngay=""), BANG, HOM), ValueError)


@ca("v630 bánh sỉ đặt lại như đơn trước: chép số lượng, món đã thôi bán bị bỏ và đếm, không mang giá cũ")
def _dat_lai():
	cu = [{"ma": "BANU00001", "sl": 30, "gia": 25000}, {"ma": "BANU00007", "sl": 10, "gia": 9000}, {"ma": "BANU00002", "sl": 0}]
	con, bo = bs.dat_lai(cu, BANG)
	la("còn đặt được", con, [{"ma": "BANU00001", "sl": 30}])
	la("thôi bán", bo, ["BANU00007"])
	dung("không mang giá", all("gia" not in d for d in con))
	don = bs.chuan_don({"ngay": "2026-11-05", "dong": con}, BANG, HOM)
	la("gửi lại thì giá hôm nay", don["dong"][0]["gia"], 28000.0)


@ca("v630 bánh sỉ mã đơn BSI + yymm + 4 số theo tháng; mẫu mã không dính mã TKR, DNTT")
def _ma():
	la("đầu tháng", bs.ma_tiep_theo("", HOM), "BSI26110001")
	la("kế tiếp", bs.ma_tiep_theo("BSI26110041", HOM), "BSI26110042")
	la("sang tháng", bs.ma_tiep_theo("BSI26101234", HOM), "BSI26110001")
	dung("không khớp TKR", not bs.RE_MA.fullmatch("TKR26110001"))
	dung("không khớp DNTT", not bs.RE_MA.findall("DNTT261100001"))


# ------------------------------------------------------------ công nợ và trả trước

@ca("v630 bánh sỉ cách trả: bật trả cuối kỳ là Công nợ hạn +15, tắt là Trả trước; trạng thái và chặn giao đúng nhánh")
def _nhanh():
	la("cuối kỳ", bs.cach_tra(1), "Công nợ")
	la("trả trước", bs.cach_tra(0), "Trả trước")
	la("hạn nợ", bs.han_no("2026-11-05"), date(2026, 11, 20))
	la("hạn nợ qua tháng", bs.han_no("2026-11-25"), date(2026, 12, 10))
	tong = 1760000
	la("công nợ chưa có đồng nào vẫn chờ giao", bs.xet_trang_thai(False, tong, [], False, False)[0], "cho_giao")
	la("trả trước chưa tiền", bs.xet_trang_thai(True, tong, [], False, False)[0], "cho_tt")
	la("trả trước tiền về nháp", bs.xet_trang_thai(True, tong, [{"so_tien": tong, "docstatus": 0}], False, False)[0], "cho_giao")
	la("đã giao", bs.xet_trang_thai(True, tong, [{"so_tien": tong, "docstatus": 1}], True, False)[0], "da_giao")
	la("đã huỷ", bs.xet_trang_thai(False, tong, [], False, True)[0], "da_huy")
	la("công nợ giao được ngay", bs.loi_giao(False, 0, []), "")
	dung("trả trước còn thiếu thì chặn", "còn phải thu" in bs.loi_giao(True, 50000, []))
	dung("trả trước phiếu nháp thì chặn", "PE-1" in bs.loi_giao(True, 0, [{"name": "PE-1", "docstatus": 0}]))
	la("trả trước đã ghi sổ thì giao", bs.loi_giao(True, 0, [{"name": "PE-1", "docstatus": 1}]), "")


@ca("v630 bánh sỉ trả trước: lần chuyển đầu phải đủ cả đơn, chuyển thiếu, dư, hai mã để người xem; dòng đã có chủ bỏ qua")
def _chon_gd():
	ma, tong = "BSI26110001", 1760000
	g = lambda ten, tien, mo: {"name": ten, "tien": tien, "mo_ta": mo, "date": "2026-11-03"}
	n, x = utd.chon_giao_dich([g("A", tong, "MBVCB " + ma)], ma, bs.RE_MA, {}, tong, tong, 0, "số tiền đơn")
	la("đủ thì nhận", [(y["gd"]["name"], y["so_tien"]) for y in n], [("A", float(tong))])
	n, x = utd.chon_giao_dich([g("B", 800000, ma)], ma, bs.RE_MA, {}, tong, tong, 0, "số tiền đơn")
	la("thiếu thì xem lại", ([y["gd"]["name"] for y in n], [y["gd"] for y in x]), ([], ["B"]))
	dung("câu nói số tiền đơn", "số tiền đơn" in x[0]["ly_do"])
	n, x = utd.chon_giao_dich([g("C", 2000000, ma)], ma, bs.RE_MA, {}, tong, tong, 0, "số tiền đơn")
	la("dư thì xem lại", [y["gd"] for y in x], ["C"])
	n, x = utd.chon_giao_dich([g("D", tong, ma + " BSI26110002")], ma, bs.RE_MA, {}, tong, tong, 0, "số tiền đơn")
	la("hai mã", [y["gd"] for y in x], ["D"])
	n, x = utd.chon_giao_dich([g("E", tong, ma)], ma, bs.RE_MA, {"E": "phiếu công nợ DNTT-1"}, tong, tong, 0, "số tiền đơn")
	la("có chủ thì bỏ", (n, x), ([], []))
	n, x = utd.chon_giao_dich([g("F", tong, "TKR26110001")], ma, bs.RE_MA, {}, tong, tong, 0, "số tiền đơn")
	la("mã đơn khác luồng không khớp", (n, x), ([], []))


class _Lap(object):
	"""Frappe giả cho ung_truoc_don.khop qua banh_si.khop_don."""

	def __init__(self, gds, tt="Trả trước"):
		self.gds, self.tt, self.chu, self.phieu, self.lap, self.tin = gds, tt, {}, [], [], []

	def sql(self, q, a=None, as_dict=False):
		if "from `tabSales Order`" in q:
			return [_fr._dict(name="SO-1", docstatus=1, status="To Deliver and Bill", vgb_si_ma="BSI26110001", vgb_tkr_coc=0,
				customer="SI00012", grand_total=1760000, rounded_total=1760000, per_billed=0)]
		if "from `tabBank Transaction`" in q:
			return [_fr._dict(g) for g in self.gds]
		return []

	def get_value(self, dt, ten, f=None, **k):
		if dt == "Bank Account":
			return "1121 - MB"
		if f == "vgb_si_tt":
			return self.tt
		return "{}"

	def get_all(self, dt, filters=None, **k):
		return [_fr._dict(p) for p in self.phieu] if dt == "Payment Entry" else []

	def get_doc(self, d):
		lap = self

		class Doc(_fr._dict):
			def setup_party_account_field(self):
				pass

			def set_missing_values(self):
				pass

			def insert(self, **k):
				self.name = "PE-%d" % (len(lap.lap) + 1)
				lap.lap.append(dict(self))
				lap.phieu.append({"name": self.name, "docstatus": 0, "paid_amount": self.paid_amount,
					"received_amount": self.received_amount, "vgb_gd_tkr": self.vgb_gd_tkr})
				lap.chu[self.vgb_gd_tkr] = "phiếu thu " + self.name
		doc = Doc(d)
		doc.flags = _fr._dict()
		return doc


def _chay_khop(l):
	from vagabond import doi_soat_sepay as dss
	from vagabond import thu_tien
	ps = [mock.patch.object(_fr.db, "sql", l.sql), mock.patch.object(_fr, "get_all", l.get_all),
		mock.patch.object(_fr, "get_doc", l.get_doc), mock.patch.object(_fr.db, "get_value", l.get_value),
		mock.patch.object(_fr.db, "exists", lambda *a, **k: True),
		mock.patch.object(dss, "chu_cua_giao_dich", lambda ds, **k: {g: c for g, c in l.chu.items() if g in ds}),
		mock.patch.object(dss, "tai_khoan_duoc_khop", lambda: {"BA-MB"}),
		mock.patch.object(thu_tien, "nang_quyen_lap_phieu", contextlib.nullcontext),
		mock.patch.object(bs, "_ds_diem", lambda: [{"ma": "SALES", "quay": "", "bat": 1}, {"ma": "TCV", "quay": "TCV", "bat": 1}]),
		mock.patch.object(bs, "_cong_ty", lambda: "Vagabond"),
		mock.patch.object(bs, "_bao_da_tt", lambda *a, **k: l.tin.append("da_tt"))]
	for p in ps:
		p.start()
	try:
		return bs.khop_don("SO-1")
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v630 bánh sỉ khop_don chạy thật (bộ máy chung): MỘT phiếu thu nháp trỏ phiếu đặt, quầy SALES, chiếm đúng dòng; chạy lại không lập đôi; đơn công nợ không khớp")
def _khop_don():
	g = {"name": "BT-9", "date": "2026-11-03", "deposit": 1760000, "withdrawal": 0, "description": "BSI26110001 chuyen tien",
		"reference_number": "FT26307", "bank_account": "BA-MB", "transaction_id": "x"}
	l = _Lap([g])
	la("lần đầu lập một phiếu", _chay_khop(l), 1)
	p = l.lap[0]
	la("phiếu đúng ô", (p["vgb_gd_tkr"], p["vgb_quay"], p["vgb_phieu_dat"], p["paid_amount"], p["mode_of_payment"]),
		("BT-9", "SALES", "SO-1", 1760000.0, "Chuyển khoản"))
	la("qua bốn hàng rào dat_banh", utd.loi_phieu(p), None)
	la("chạy lại không lập thêm", _chay_khop(l), 0)
	la("báo Sales và bếp một lần", l.tin, ["da_tt"])
	l2 = _Lap([dict(g, deposit=900000)])
	la("chuyển thiếu không lập", _chay_khop(l2), 0)
	l3 = _Lap([g], tt="Công nợ")
	la("đơn công nợ không đi khớp tiền", _chay_khop(l3), 0)


class _Doc(_fr._dict):
	def __init__(self, *a, **k):
		super().__init__(*a, **k)
		self.flags = _fr._dict()
		self.items = self.get("items") or []

	def set(self, k, v):
		self[k] = v

	def append(self, k, v):
		self.setdefault(k, []).append(v)

	def run_method(self, *a):
		pass

	def insert(self, **k):
		self.name = self.get("name") or ("DN-1" if self.doctype == "Delivery Note" else "SI-1")

	def submit(self):
		self.docstatus = 1


def _chay_giao(tra_truoc, phieu):
	"""giao_hang chạy thật trên Frappe giả: ghi lại phiếu giao, hoá đơn và lời gọi cấn ứng trước."""
	vet = {"cap": None, "ton": None}
	t = {"name": "SO-1", "ma": "BSI26110001", "trang_thai": "cho_giao", "nhan": "Chờ giao", "khach": "Café Lá Me",
		"tra_truoc": 1 if tra_truoc else 0, "con_lai": 0.0, "phieu": phieu, "ghi_chu": "",
		"dong": [{"ma": "BANU00001", "sl": 30}, {"ma": "BAEV00009", "sl": 2}], "hoa_don": ""}
	dn = _Doc(doctype="Delivery Note", items=[_fr._dict(warehouse="Kho cũ"), _fr._dict(warehouse="Kho cũ")])
	si = _Doc(doctype="Sales Invoice", payment_terms_template="KY-30", payment_schedule=[1], advances=[1], allocate_advances_automatically=1)
	sel = types.ModuleType("erpnext.selling.doctype.sales_order.sales_order")
	sel.make_delivery_note = lambda name: dn
	dnm = types.ModuleType("erpnext.stock.doctype.delivery_note.delivery_note")
	dnm.make_sales_invoice = lambda name: si
	mods = {"erpnext": types.ModuleType("erpnext"), "erpnext.selling": types.ModuleType("x"), "erpnext.selling.doctype": types.ModuleType("x"),
		"erpnext.selling.doctype.sales_order": types.ModuleType("x"), "erpnext.selling.doctype.sales_order.sales_order": sel,
		"erpnext.stock": types.ModuleType("x"), "erpnext.stock.doctype": types.ModuleType("x"),
		"erpnext.stock.doctype.delivery_note": types.ModuleType("x"), "erpnext.stock.doctype.delivery_note.delivery_note": dnm}
	from vagabond import thu_tien, xuat_kho

	def cap(s, ds):
		vet["cap"] = list(ds)
		s.allocate_advances_automatically = 0
		s.advances = [{"reference_name": x} for x in ds]
		return s

	def gv(dt, ten, f=None, **k):
		if dt == "Item" and f == "is_stock_item":
			return 1 if ten == "BANU00001" else 0
		return None
	ps = [mock.patch.dict(sys.modules, mods), mock.patch.object(bs, "tom_tat", lambda n, khoa=False: dict(t)),
		mock.patch.object(bs, "_khoa_don", lambda n: None), mock.patch.object(bs, "_phieu_giao_cua", lambda n: ()),
		mock.patch.object(bs, "_cong_ty", lambda: "Vagabond"), mock.patch.object(bs, "_hom_nay", lambda: "2026-11-05"),
		mock.patch.object(bs, "_quay", lambda: "SALES"), mock.patch.object(bs, "_kiem_quyen_giao", lambda: None),
		mock.patch.object(bs, "_nguoi_mua", lambda k: {"vgb_xhd_ten": "CÔNG TY LÁ ME", "vgb_xhd_mst": "0312345678"}),
		mock.patch.object(xuat_kho, "_kho_that", lambda ct: [_fr._dict(name="Kho Sỉ - VGB", warehouse_name="Kho Sỉ")]),
		mock.patch.object(xuat_kho, "_chan_qua_ton", lambda kho, ds: vet.__setitem__("ton", (kho, ds))),
		mock.patch.object(thu_tien, "nang_quyen_lap_phieu", lambda: contextlib.nullcontext("sales@vgb")),
		mock.patch.object(thu_tien, "_giu_chu", lambda d, g: None),
		mock.patch.object(utd, "cap_ung_truoc", cap),
		mock.patch.object(_fr, "get_doc", lambda dt, n=None: _fr._dict(name="SO-1", customer="SI00012")),
		mock.patch.object(_fr.db, "get_value", gv),
		mock.patch.object(_fr, "generate_hash", lambda length=8: "a" * length, create=True)]
	for p in ps:
		p.start()
	try:
		kq = bs.giao_hang("SO-1", "Kho Sỉ - VGB", " chị  Lan ")
	finally:
		for p in reversed(ps):
			p.stop()
	return kq, dn, si, vet


@ca("v630 bánh sỉ giao_hang chạy thật, khách công nợ: phiếu giao từ phiếu đặt ở kho chọn, hoá đơn từ phiếu giao, Công nợ hạn +15, không cấn ứng trước nào")
def _giao_cong_no():
	kq, dn, si, vet = _chay_giao(False, [])
	la("kiểm tồn chỉ hàng có tồn", vet["ton"], ("Kho Sỉ - VGB", [{"ma": "BANU00001", "sl": 30}]))
	la("phiếu giao đúng kho mọi dòng", (dn.set_warehouse, [d.warehouse for d in dn.items], dn.docstatus), ("Kho Sỉ - VGB", ["Kho Sỉ - VGB"] * 2, 1))
	la("người nhận gọn", dn.vgb_nguoi_nhan, "chị Lan")
	la("hoá đơn công nợ", (si.vgb_pt_thanh_toan, str(si.due_date), si.posting_date, si.update_stock, si.docstatus),
		("Công nợ", "2026-11-20", "2026-11-05", 0, 1))
	la("một đơn một hoá đơn", (si.custom_pancake_id, si.vgb_quay, si.custom_nguon), ("BSI-BSI26110001", "SALES", "Khách sỉ"))
	la("bỏ mẫu điều khoản, lịch trả máy dựng lại theo hạn", (si.payment_terms_template, si.payment_schedule), (None, []))
	la("không tự cấn, không ứng trước", (si.allocate_advances_automatically, si.advances, vet["cap"]), (0, [], None))
	la("người mua theo MST", si.vgb_xhd_mst, "0312345678")
	la("trả về", (kq["phieu_giao"], kq["hoa_don"]), ("DN-1", "SI-1"))


@ca("v630 bánh sỉ giao_hang chạy thật, khách trả trước: Trả trước, hạn hôm nay, cấn ĐÚNG phiếu đã ghi sổ của đơn (bỏ phiếu nháp)")
def _giao_tra_truoc():
	kq, dn, si, vet = _chay_giao(True, [{"name": "PE-1", "docstatus": 1}, {"name": "PE-2", "docstatus": 1}])
	la("hoá đơn trả trước", (si.vgb_pt_thanh_toan, str(si.due_date)), ("Trả trước", "2026-11-05"))
	la("cấn đúng phiếu đã ghi sổ", vet["cap"], ["PE-1", "PE-2"])
	la("tắt tự cấn", si.allocate_advances_automatically, 0)
	# Đột biến M6 lần đầu lọt: loi_giao đã chặn giao khi còn phiếu nháp, nên ca
	# trên không bao giờ đưa phiếu nháp tới bước cấn. Gỡ lớp đó (H5 c) để chứng
	# minh bước cấn TỰ lọc phiếu nháp, không dựa vào lớp chặn phía trước.
	with mock.patch.object(bs, "loi_giao", lambda *a: ""):
		kq, dn, si, vet = _chay_giao(True, [{"name": "PE-1", "docstatus": 1}, {"name": "PE-N", "docstatus": 0}])
	la("bỏ lớp chặn trước: vẫn chỉ cấn phiếu đã ghi sổ", vet["cap"], ["PE-1"])


@ca("v630 bánh sỉ giao_hang: đơn trả trước còn phiếu nháp hoặc còn thiếu tiền, đơn đã giao, kho lạ đều bị chặn trước khi lập gì")
def _giao_chan():
	t0 = {"name": "SO-1", "ma": "BSI26110001", "trang_thai": "cho_giao", "nhan": "Chờ giao", "khach": "K", "tra_truoc": 1,
		"con_lai": 0.0, "phieu": [{"name": "PE-1", "docstatus": 0}], "dong": [], "ghi_chu": "", "hoa_don": ""}
	from vagabond import xuat_kho
	lap = []
	for ten, t, kho in (("phiếu nháp", t0, "Kho Sỉ - VGB"), ("thiếu tiền", dict(t0, con_lai=5000.0, phieu=[]), "Kho Sỉ - VGB"),
			("đã giao", dict(t0, trang_thai="da_giao", hoa_don="SI-9"), "Kho Sỉ - VGB"),
			("kho lạ", dict(t0, tra_truoc=0, phieu=[]), "Kho Bếp")):
		with mock.patch.object(bs, "tom_tat", lambda n, t=t, khoa=False: dict(t)), mock.patch.object(bs, "_khoa_don", lambda n: None), \
				mock.patch.object(bs, "_kiem_quyen_giao", lambda: None), mock.patch.object(bs, "_phieu_giao_cua", lambda n: ()), \
				mock.patch.object(bs, "_cong_ty", lambda: "Vagabond"), \
				mock.patch.object(xuat_kho, "_kho_that", lambda ct: [_fr._dict(name="Kho Sỉ - VGB")]), \
				mock.patch.object(_fr, "get_doc", lambda *a, **k: lap.append(1)):
			nem(ten, lambda kho=kho: bs.giao_hang("SO-1", kho))
	la("không lập phiếu giao nào", lap, [])


@ca("v630 bánh sỉ hoá đơn ngày giao: chỉ miễn phép so nguồn khi phiếu đặt mang ĐÚNG mã BSI; Desk gõ tay mã BSI vẫn bị so")
def _mien_so():
	ok = bs.la_hoa_don_si_web
	dung("đúng", ok("Công nợ", "BSI-BSI26110001", ["SO-1", "SO-1"], {"SO-1": "BSI26110001"}))
	dung("trả trước", ok("Trả trước", "BSI-BSI26110001", ["SO-1"], {"SO-1": "BSI26110001"}))
	dung("phiếu đặt không phải đơn sỉ", not ok("Công nợ", "BSI-BSI26110001", ["SO-1"], {"SO-1": None}))
	dung("phiếu đặt mã khác", not ok("Công nợ", "BSI-BSI26110001", ["SO-1"], {"SO-1": "BSI26110002"}))
	dung("một dòng gõ tay", not ok("Công nợ", "BSI-BSI26110001", ["SO-1", None], {"SO-1": "BSI26110001"}))
	dung("phương thức khác", not ok("Chuyển khoản", "BSI-BSI26110001", ["SO-1"], {"SO-1": "BSI26110001"}))
	dung("mã đơn không phải BSI", not ok("Công nợ", "TKR-TKR26110001", ["SO-1"], {"SO-1": "TKR26110001"}))
	s = (GOC / "vagabond/ban_hang.py").read_text(encoding="utf-8")
	i = s.find("def kiem_truoc_khi_luu(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("hook gọi phép miễn trước phép so nguồn", 0 < than.find("mien_so_nguon(doc)") < than.find("hop_le = _pt_cho_nguon(nguon)"))


@ca("v630 bánh sỉ công nợ trên trang khách: tổng gồm tờ chưa gom và phiếu đòi nợ còn mở, hạn gần nhất, đếm quá hạn")
def _tom_tat_no():
	hd = [{"name": "SI-1", "ngay": "2026-10-26", "tien": 2064960}, {"name": "SI-2", "ngay": "2026-10-29", "tien": 2064960}]
	phieu = [{"ma_phieu": "DNTT-26-10-00007", "con_thieu": 1000000, "hoa_don": ["SI-0"]}]
	han = {"SI-1": "2026-11-10", "SI-2": "2026-11-13", "SI-0": "2026-10-30"}
	n = bs.tom_tat_no(hd, phieu, han, "2026-11-02")
	la("tổng", n["tong"], 2064960 * 2 + 1000000.0)
	la("hạn gần nhất", n["han_gan"], "2026-10-30")
	la("quá hạn", n["so_qua_han"], 1)
	la("thứ tự hạn", [d["hoa_don"] for d in n["dong"]], ["SI-0", "SI-1", "SI-2"])
	la("rỗng", bs.tom_tat_no([], [], {}, "2026-11-02")["tong"], 0)


@ca("v630 bánh sỉ cong_no.no_cua_khach chạy thật với vai Guest: đúng một khách, không đi qua cổng quyền nhân viên")
def _no_guest():
	from vagabond import cong_no
	from vagabond import thu_tien as tt
	rows = [_fr._dict(name="SI-1", customer="SI00012", customer_name="Lá Me", posting_date="2026-10-26", grand_total=2000000,
			outstanding_amount=2000000, vgb_pt_thanh_toan="Công nợ", custom_nguon="Khách sỉ", vgb_quay="SALES",
			vgb_ma_tham_chieu="BSI26100001", vgb_khach_no=None),
		_fr._dict(name="SI-7", customer="KL0001", customer_name="Khác", posting_date="2026-10-27", grand_total=500000,
			outstanding_amount=500000, vgb_pt_thanh_toan="Công nợ", custom_nguon="", vgb_quay="", vgb_ma_tham_chieu="",
			vgb_khach_no="SI00099")]
	hoi = []

	def get_all(dt, filters=None, **k):
		hoi.append((dt, k.get("or_filters")))
		if dt == "Sales Invoice" and (filters or {}).get("vgb_pt_thanh_toan") == "Công nợ":
			return [_fr._dict(r) for r in rows]
		if dt == "Sales Invoice":
			return [_fr._dict(name="SI-1", due_date="2026-11-10")]
		return []
	with mock.patch.object(_fr, "get_roles", lambda *a: ["Guest"]), mock.patch.object(_fr, "get_all", get_all), \
			mock.patch.object(tt, "si_co_dong_cong_no", lambda: set()), mock.patch.object(tt, "bang_dong_cua", lambda ds: {}), \
			mock.patch.object(cong_no, "_hd_da_gom", lambda: set()), mock.patch.object(cong_no, "_tien_da_ve_theo_hd", lambda ds: {}), \
			mock.patch.object(_fr.db, "sql", lambda *a, **k: []):
		n = cong_no.no_cua_khach("SI00012")
		nem("cửa nhân viên vẫn chặn Guest", lambda: cong_no.ds_khach_no())
	la("chỉ tờ của khách", [h["name"] for h in n["hd"]], ["SI-1"])
	la("số còn đòi", n["hd"][0]["tien"], 2000000.0)
	la("hạn", n["han"], {"SI-1": "2026-11-10"})
	la("lọc khách ở truy vấn", hoi[0][1], {"customer": "SI00012", "vgb_khach_no": "SI00012"})


# ------------------------------------------------------------ phiên, quyền

def _ham_whitelist():
	cay = ast.parse((GOC / "vagabond/banh_si.py").read_text(encoding="utf-8"))
	ra = {}
	for f in cay.body:
		if isinstance(f, ast.FunctionDef):
			trang = [ast.unparse(d) for d in f.decorator_list]
			if any("whitelist" in d for d in trang):
				ra[f.name] = (f, trang)
	return cay, ra


@ca("v630 bánh sỉ: không hàm nào trong banh_si.py khai trùng tên (hàm thuần bị cửa whitelist cùng tên đè lặng lẽ)")
def _trung_ten():
	cay = ast.parse((GOC / "vagabond/banh_si.py").read_text(encoding="utf-8"))
	ten = [f.name for f in cay.body if isinstance(f, ast.FunctionDef)]
	la("tên trùng", sorted({t for t in ten if ten.count(t) > 1}), [])


@ca("v630 bánh sỉ cửa ngõ: hàm khách có trần lượt, ghi chỉ POST, không gọi cổng quyền nhân viên; hàm màn app kiểm vai đầu tiên")
def _cua_ngo():
	cay, ds = _ham_whitelist()
	khach = {t for t, (f, tr) in ds.items() if any("allow_guest=True" in d for d in tr)}
	# Codex #531 f4: thêm qr_don (mở lại QR đơn trả trước của chính khách phiên).
	la("mười hàm khách", sorted(khach), sorted(["san_sang", "gui_ma", "xac_thuc", "thoat", "toi", "dat", "trang_thai_don", "qr_no",
		"qr_don", "dang_ky"]))
	ham = {f.name: f for f in cay.body if isinstance(f, ast.FunctionDef)}
	for t, (f, tr) in ds.items():
		if t in khach:
			dung(t + " có rate_limit", any(d.startswith("rate_limit") for d in tr))
			if t not in ("san_sang", "toi"):
				dung(t + " chỉ POST", any("methods=['POST']" in d for d in tr))
			# Hàm khách và mọi hàm cùng tệp nó gọi không có cổng quyền nhân viên.
			goi = {n.func.id for n in ast.walk(f) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
			for g in goi | {t}:
				if g in ham:
					than = ast.unparse(ham[g])
					dung("%s (gọi từ %s) không cổng nhân viên" % (g, t), "_kiem_quyen" not in than and "get_roles" not in than)
		else:
			than = [x for x in f.body if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant) and isinstance(x.value.value, str))]
			dung(t + " kiểm vai đầu tiên", re.match(r"_kiem_quyen_(sales|giao|xem)\(\)", ast.unparse(than[0])))


@ca("v630 bánh sỉ phiên Guest: hàm dùng chung mô đun khác mà trang khách gọi (cong_no, ung_truoc_don) không có cổng quyền nhân viên")
def _guest_mo_dun_khac():
	tep = {"cong_no.py": ["no_cua_khach", "qr_no_cua_khach", "bang_khach_no", "lap_phieu_doi_no", "_phieu_mo_cua",
		"tinh_con_doi"],
		"ung_truoc_don.py": ["khop", "ds_phieu", "phieu_cua", "gd_mang_ma", "con_phai_thu"]}
	for t, ds in tep.items():
		cay = ast.parse((GOC / "vagabond" / t).read_text(encoding="utf-8"))
		ham = {f.name: f for f in cay.body if isinstance(f, ast.FunctionDef)}
		for d in ds:
			dung("%s %s có thật" % (t, d), d in ham)
			than = ast.unparse(ham[d]) if d in ham else ""
			dung("%s %s không cổng quyền" % (t, d), "_kiem_quyen" not in than and "get_roles" not in than)
			dung("%s %s không whitelist" % (t, d), not any("whitelist" in ast.unparse(x) for x in (ham[d].decorator_list if d in ham else [])))


@ca("v630 bánh sỉ quyền chạy thật: Guest bị chặn ở mọi hàm màn app; Sales không ghi sổ phiếu thu; bếp xem đơn không thấy tiền")
def _quyen_that():
	_, ds = _ham_whitelist()
	nv = {"ds_dang_ky": {}, "tim_khach": {}, "duyet": {"name": "x"}, "tu_choi": {"name": "x", "ly_do": "khong hop"}, "ds_khach": {},
		"luu_khach": {"khach": "x"}, "bang_gia": {"khach": "x"}, "tim_mon": {}, "luu_gia": {"khach": "x", "ma": "y", "gia": 1},
		"bo_gia": {"khach": "x", "ma": "y"}, "ds_don": {}, "xem_don": {"name": "x"}, "kiem_tien_ve": {"name": "x"},
		"ghi_so_phieu": {"name": "x", "phieu": "y"}, "giao_hang": {"name": "x", "kho": "y"}, "huy_don": {"name": "x", "ly_do": "khach doi y"}}
	la("đủ hàm màn app", sorted(nv), sorted(t for t, (f, tr) in ds.items() if not any("allow_guest=True" in d for d in tr)))
	cham = []
	with mock.patch.object(_fr, "get_roles", lambda *a: ["Guest"]), mock.patch.object(_fr.db, "sql", lambda *a, **k: cham.append(a) or []), \
			mock.patch.object(_fr, "get_doc", lambda *a, **k: cham.append(a)), mock.patch.object(_fr, "get_all", lambda *a, **k: cham.append(a) or []):
		for t, a in nv.items():
			nem("Guest gọi " + t, lambda t=t, a=a: getattr(bs, t)(**a))
	la("chặn trước khi chạm dữ liệu", cham, [])
	with mock.patch.object(_fr, "get_roles", lambda *a: ["Sales User"]), mock.patch.object(bs, "_khoa_don", lambda n: cham.append(n)):
		nem("Sales ghi sổ phiếu thu", lambda: bs.ghi_so_phieu("SO-1", "PE-1"))
	la("chặn trước khi khoá đơn", cham, [])
	t = {"name": "SO-1", "tong": 100.0, "chua_vat": 93.0, "vat": 7.0, "con_lai": 0.0, "phieu": [{"name": "PE-1"}],
		"dong": [{"ma": "A", "sl": 3, "gia": 30.0, "tien": 90.0}], "tra_truoc": 1, "trang_thai": "cho_giao"}
	with mock.patch.object(_fr, "get_roles", lambda *a: ["Manufacturing User"]), mock.patch.object(bs, "tom_tat", lambda n, khoa=False: json.loads(json.dumps(t))):
		r = bs.xem_don("SO-1")
	la("bếp không thấy tiền", (r["tong"], r["vat"], r["con_lai"], r["phieu"], r["dong"][0]["gia"], r["dong"][0]["tien"]), (None, None, None, [], None, None))
	la("bếp vẫn thấy món và số lượng", (r["dong"][0]["ma"], r["dong"][0]["sl"]), ("A", 3))
	with mock.patch.object(_fr, "get_roles", lambda *a: ["Stock User"]):
		dung("kho thấy tiền để giao", bs._co_tien())


def _otp_than():
	gui, cookie = [], []
	dn = types.SimpleNamespace(gui_ma=lambda s: gui.append(s) or {"ok": 1, "song_giay": 300},
		xac_thuc=lambda s, m: {"ok": 1, "token": "tok"} if m == "123456" else {"ok": 0, "ly_do": "ma_khong_dung"},
		PHIEN_SONG_NGAY=30)
	from vagabond import lib
	ps = [mock.patch.object(bs, "_dn", lambda: dn), mock.patch.object(lib, "cfg", lambda: {"zns_template_otp": "123"}),
		mock.patch.object(_fr, "local", types.SimpleNamespace(cookie_manager=types.SimpleNamespace(
			set_cookie=lambda k, v, **kw: cookie.append((k, v, kw.get("httponly"), kw.get("samesite")))), response_headers={}))]
	for p in ps:
		p.start()
	try:
		with mock.patch.object(_fr, "get_all", lambda dt, **k: []):
			la("số lạ", bs.gui_ma("0909 123 456"), {"ok": 0, "ly_do": "chua_mo_si"})
			la("số lạ xác thực", bs.xac_thuc("0909123456", "123456"), {"ok": 0, "ly_do": "chua_mo_si"})
		la("không gửi ZNS cho số lạ", gui, [])
		with mock.patch.object(_fr, "get_all", lambda dt, filters=None, **k: [_fr._dict(name="SI00012", vgb_si_cuoi_ky=1)]
				if (filters or {}).get("vgb_si_sdt") == "0909123456" and (filters or {}).get("vgb_si_web") == 1 else []):
			la("số đã mở", bs.gui_ma("+84 909 123 456")["ok"], 1)
			la("sai mã", bs.xac_thuc("0909123456", "000000")["ok"], 0)
			la("chưa đặt cookie khi sai", cookie, [])
			la("đúng mã", bs.xac_thuc("0909123456", "123456"), {"ok": 1})
		la("cookie riêng, HttpOnly, Strict", cookie, [("vgb_khach_si", "tok", True, "Strict")])
		dung("không dùng cookie thành viên", bs.COOKIE != "vgb_thanh_vien")
		with mock.patch.object(_fr, "get_all", lambda dt, **k: [_fr._dict(name="A"), _fr._dict(name="B")]):
			la("hai khách cùng số thì không đoán", bs.gui_ma("0909123456")["ly_do"], "can_doi_chieu")
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v630 bánh sỉ OTP chạy thật: số lạ không gửi ZNS, cookie riêng chỉ đặt sau mã đúng, hai khách cùng số không đoán")
def _otp_that():
	_otp_than()


@ca("v630 bánh sỉ đặt chạy thật: khách lấy từ phiên (không từ trình duyệt), giá gửi lên bị bỏ, chưa đăng nhập bị chặn, mã lần gửi sai dạng bị chặn")
def _dat_that():
	goi = {}

	def lap(kh, don, lan):
		goi["kh"], goi["don"], goi["lan"] = kh.name, don, lan
		return _fr._dict(name="SO-9", vgb_si_ma="BSI26110009", vgb_si_tt="Công nợ")
	kh = _fr._dict(name="SI00012", customer_name="Café Lá Me", vgb_si_cuoi_ky=1)
	ps = [mock.patch.object(bs, "_khach_phien", lambda: (kh, "")), mock.patch.object(bs, "_hom_nay", lambda: HOM),
		mock.patch.object(bs, "gia_cua_khach", lambda k, n=None: dict(BANG) if k == "SI00012" else {}),
		mock.patch.object(bs, "_da_gui", lambda k, lan, dau, khoa=False: None), mock.patch.object(bs, "_lap_don", lap),
		mock.patch.object(bs, "_bao_don_moi", lambda *a: goi.setdefault("bao", a[2])), mock.patch.object(bs, "_ket_qua", lambda ten: {"ok": 1, "ma": ten})]
	for p in ps:
		p.start()
	try:
		raw = dict(_raw(), khach="SI00099", dong=[{"ma": "BANU00001", "sl": 30, "gia": 1}])
		kq = bs.dat(json.dumps(raw), "123e4567-e89b-42d3-a456-426614174000")
	finally:
		for p in reversed(ps):
			p.stop()
	la("trả đơn", kq, {"ok": 1, "ma": "SO-9"})
	la("khách của phiên", goi["kh"], "SI00012")
	la("giá máy chủ", (goi["don"]["dong"][0]["gia"], goi["don"]["tong"]), (28000.0, 840000.0))
	la("công nợ không chờ tiền", goi["bao"], False)
	with mock.patch.object(bs, "_khach_phien", lambda: (None, "chua_dang_nhap")):
		nem("chưa đăng nhập", lambda: bs.dat(json.dumps(_raw()), "123e4567-e89b-42d3-a456-426614174000"))
	nem("mã lần gửi sai dạng", lambda: bs.dat("{}", "abc"))


@ca("v630 bánh sỉ trang_thai_don: chỉ đơn CỦA khách phiên này, mã sai dạng hay không đăng nhập bị chặn")
def _trang_thai_don():
	hoi = []
	with mock.patch.object(bs, "_khach_phien", lambda: (_fr._dict(name="SI00012"), "")), \
			mock.patch.object(_fr.db, "get_value", lambda dt, f=None, *a, **k: hoi.append(f) or None):
		nem("đơn không thuộc khách", lambda: bs.trang_thai_don("BSI26110001"))
	la("lọc theo khách phiên", hoi[0].get("customer"), "SI00012")
	with mock.patch.object(bs, "_khach_phien", lambda: (None, "chua_dang_nhap")):
		nem("chưa đăng nhập", lambda: bs.trang_thai_don("BSI26110001"))
	with mock.patch.object(bs, "_khach_phien", lambda: (_fr._dict(name="SI00012"), "")):
		nem("mã sai dạng", lambda: bs.trang_thai_don("TKR26110001"))


# ------------------------------------------------------------ đăng ký

@ca("v630 bánh sỉ đăng ký: chuẩn hoá tên, số, MST; loại hình và lượng chỉ trong danh sách; thiếu hay sai bị chặn bằng câu tiếng Việt")
def _dang_ky():
	dk = bs.chuan_dang_ky({"ten_quan": "  Café   Lá Me ", "sdt": "+84 909 123 456", "mst": "0312.345.678", "loai_hinh": "cafe", "luong": "50_200"})
	la("sạch", (dk["ten_quan"], dk["sdt"], dk["mst"], dk["loai_hinh"], dk["luong_tuan"]), ("Café Lá Me", "0909123456", "0312345678", "Quán cà phê", "50 - 200 cái"))
	la("MST chi nhánh", bs.chuan_mst("0312345678-001"), "0312345678-001")
	la("MST chi nhánh liền", bs.chuan_mst("0312345678001"), "0312345678-001")
	la("MST 12 số", bs.chuan_mst("079123456789"), "079123456789")
	la("MST trống", bs.chuan_mst(""), "")
	ok = {"ten_quan": "Lá Me", "sdt": "0909123456", "loai_hinh": "cafe", "luong": "duoi_50"}
	for ten, sai in (("thiếu tên", {"ten_quan": " "}), ("số bàn", {"sdt": "0283 822 9999"}), ("MST 9 số", {"mst": "031234567"}),
			("loại lạ", {"loai_hinh": "bar"}), ("lượng lạ", {"luong": "1000"}), ("ghi chú dài", {"ghi_chu": "x" * 501})):
		nem(ten, lambda sai=sai: bs.chuan_dang_ky(dict(ok, **sai)), ValueError)
	nem("không phải dict", lambda: bs.chuan_dang_ky([]), ValueError)


@ca("v630 bánh sỉ phiếu đăng ký: chỉ nhận từ web, Sales không sửa chữ khách gửi, không đổi trạng thái đã chốt")
def _phieu_dk():
	class D(_fr._dict):
		def is_new(self):
			return self.get("_moi", False)

		def get_doc_before_save(self):
			return self.get("_cu")
	nem("tạo tay", lambda: bs.kiem_phieu_dang_ky(D(_moi=True, flags=_fr._dict())))
	bs.kiem_phieu_dang_ky(D(_moi=True, flags=_fr._dict(dang_ky_web=True)))
	cu = _fr._dict(ten_quan="Lá Me", sdt="0909123456", trang_thai="Chờ duyệt")
	nem("sửa tên khách gửi", lambda: bs.kiem_phieu_dang_ky(D(_cu=cu, ten_quan="Lá Me 2", sdt="0909123456", trang_thai="Chờ duyệt")))
	bs.kiem_phieu_dang_ky(D(_cu=cu, ten_quan="Lá Me", sdt="0909123456", trang_thai="Đã duyệt"))
	nem("đã duyệt quay lại chờ", lambda: bs.kiem_phieu_dang_ky(D(_cu=dict(cu, trang_thai="Đã duyệt"), ten_quan="Lá Me", sdt="0909123456", trang_thai="Chờ duyệt")))
	nem("trạng thái lạ", lambda: bs.kiem_phieu_dang_ky(D(_cu=cu, ten_quan="Lá Me", sdt="0909123456", trang_thai="Xoá")))


@ca("v630 bánh sỉ gợi ý giá: giá khách đã trả gần nhất theo mã gốc, mã sỉ BAWS gộp qua Anh Xa Ma Si, món đã có giá không gợi ý lại")
def _goi_y():
	ls = [{"item_code": "BAWS00001", "rate": 30000, "ngay": "2026-10-01", "hoa_don": "HD-1"},
		{"item_code": "BAWS00001", "rate": 31000, "ngay": "2026-10-20", "hoa_don": "HD-5"},
		{"item_code": "BANU00002", "rate": 32000, "ngay": "2026-10-10", "hoa_don": "HD-3"},
		{"item_code": "BANU00003", "rate": 15000, "ngay": "2026-10-11", "hoa_don": "HD-4"},
		{"item_code": "BANU00004", "rate": 0, "ngay": "2026-10-12", "hoa_don": "HD-6"}]
	g = bs.goi_y_gia(ls, {"BAWS00001": "BANU00001"}, {"BANU00003"})
	la("mã và giá", [(x["ma"], x["gia"], x["tu_ma"]) for x in g], [("BANU00001", 31000.0, "BAWS00001"), ("BANU00002", 32000.0, "")])


# ------------------------------------------------------------ tin, JS

@ca("v630 bánh sỉ tin Zalo: đăng ký và đơn không mang số tiền; đơn dài thu về 'và N món nữa'")
def _tin():
	don = {"ma": "BSI26110001", "khach": "Lá Me", "ngay": "2026-11-05", "ghi_chu": "",
		"dong": [{"ten": "Bánh %d" % i, "sl": 5, "gia": 28000, "tien": 140000} for i in range(35)]}
	for loai in ("moi_no", "moi_tt", "da_tt", "bep"):
		c = bs.tin_don(don, loai)
		dung(loai + " không có tiền", "28000" not in c and "140000" not in c and not re.search(r"[0-9] ?(đ|đồng|VND)\b", c))
		dung(loai + " thu gọn", "và 5 món nữa" in c)
	dk = bs.tin_dang_ky({"ten_quan": "Lá Me", "sdt": "0909123456", "loai_hinh": "Quán cà phê", "luong_tuan": "Dưới 50 cái", "mst": ""})
	dung("đăng ký có số Zalo", "0909123456" in dk)
	for c in (dk, bs.tin_don(don, "bep")):
		dung("không gạch dài", not re.search("[–—]", c))


@ca("v630 bánh sỉ quyền: hai danh sách vai bên JS (64-banh-si.js) trùng tuyệt đối máy chủ")
def _quyen_js():
	s = (GOC / "vagabond/public/js/bep/64-banh-si.js").read_text(encoding="utf-8")

	def doc(ten):
		m = re.search(r"var %s = \[(.*?)\];" % ten, s, re.S)
		return tuple(re.findall(r"'([^']+)'", m.group(1))) if m else None
	la("Sales", doc("QUYEN_BSI_SALES"), bs.QUYEN_SALES_SI)
	la("xem", doc("QUYEN_BSI_XEM"), bs.QUYEN_XEM_SI)
	dung("không ô xổ danh sách", "<select" not in s)


def _node(tep, can):
	r = subprocess.run(["node", tep], cwd=GOC, capture_output=True, text=True, timeout=120)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= can)


@ca("v630 trang /banh-si chạy Vue thật: đăng ký không hiện giá, đăng nhập, đặt, đặt lại, QR, công nợ (hanh_vi/banh_si_630.mjs)")
def _vue():
	_node("vagabond/khung/kiem_thu/hanh_vi/banh_si_630.mjs", 12)


@ca("v630 màn Đơn sỉ web và Khách sỉ web nạp thật phần 63: giao hàng, kiểm tiền, ghi sổ, huỷ, duyệt, giá riêng (hanh_vi/banh_si_app_630.js)")
def _app():
	_node("vagabond/khung/kiem_thu/hanh_vi/banh_si_app_630.js", 10)
