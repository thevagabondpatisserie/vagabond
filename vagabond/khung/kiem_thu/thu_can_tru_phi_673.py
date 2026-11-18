# -*- coding: utf-8 -*-
"""v673 (chị Dung 18/11/2026): hoá đơn phí của đối tác treo nợ phải trả.

Ảnh Công nợ phải trả: ba hoá đơn CÔNG TY TNHH GRAB (52.689.983, 46.864.129,
44.071.417) nằm bước "Kiểm khoản đã trả", trễ 6 tới 66 ngày, dù tiệm không
chuyển đồng nào: Grab đã giữ phí khi chuyển tiền bán. Nút Cấn trừ công nợ chỉ
có lối khoản đã chi và "đã trả trước khi lên ERP" (Có 11211), cả hai sai bản chất.

Các ca chạy THẬT can_tru_phi (phần thuần, de_xuat, lap, kiem_phieu_doi_soat)
và can_tru_san (kiem_phieu, thu_bu, kiem_but_toan); chỉ thay tầng chạm hệ.
"""
from contextlib import ExitStack
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import can_tru_phi as P
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


# ------------------------------------------------------------ phần thuần

@ca("v673 nhận ra đối tác và loại phí theo tên nhà cung cấp, nội dung hoá đơn (ba mẫu hoá đơn thật)")
def _():
	la("Grab hoa hồng", P.doan_doi_tac("CÔNG TY TNHH GRAB", "Phí dịch vụ"), "grab")
	la("Grab quảng cáo", P.doan_doi_tac("CÔNG TY TNHH GRAB VIỆT NAM", ""), "grab")
	la("OnePay", P.doan_doi_tac("CÔNG TY CỔ PHẦN THƯƠNG MẠI VÀ DỊCH VỤ TRỰC TUYẾN ONEPAY", ""), "onepay")
	la("Xanh SM", P.doan_doi_tac("CÔNG TY CỔ PHẦN XANH SM", ""), "greensm")
	la("không rõ", P.doan_doi_tac("Công ty In Printeco", "Tem nhãn"), None)
	la("quảng cáo là phí kỳ", P.doan_loai("Phí dịch vụ quảng cáo 1.0 tháng 10/2026_5-C4E1NPWGG2WZFA"), "ky")
	la("phí xử lý giao dịch là theo đơn", P.doan_loai("Phí xử lý giao dịch và phí thanh toán theo HĐ số 212626"), "don")


@ca("v673 kỳ phí: 'từ ngày ... đến ngày' của OnePay, 'tháng 10/2026' của Grab, không ghi thì tháng trước ngày hoá đơn")
def _():
	la("OnePay", P.doan_ky("Phí xử lý giao dịch và phí thanh toán theo HĐ số 212626/HCM/ECOM từ ngày 01/10/2026 đến ngày 31/10/2026",
		"2026-11-07"), ("2026-10-01", "2026-10-31", "ghi trên hoá đơn"))
	la("Grab quảng cáo", P.doan_ky("Phí dịch vụ quảng cáo 1.0 tháng 10/2026_5-C4E1NPWGG2WZFA", "2026-11-03"),
		("2026-10-01", "2026-10-31", "ghi trên hoá đơn"))
	la("hoa hồng Grab xuất 06/10", P.doan_ky("Phí dịch vụ", "2026-10-06"), ("2026-09-01", "2026-09-30", "tháng trước ngày hoá đơn"))
	la("tháng 1 lùi về tháng 12 năm trước", P.doan_ky("", "2026-01-05")[:2], ("2025-12-01", "2025-12-31"))
	la("ngày sai không nhận", P.doan_ky("từ ngày 31/02/2026 đến ngày 31/03/2026", "2026-04-02")[2], "tháng trước ngày hoá đơn")
	la("chip tháng", [x["ten"] for x in P.cac_thang("2026-11-07", 3)], ["Tháng 11/2026", "Tháng 10/2026", "Tháng 09/2026"])


@ca("v673 số được bù không quá dư hoá đơn phí, không quá phần phí đối soát chưa bù cho hoá đơn khác")
def _():
	la("hoá đơn lớn hơn đối soát", P.can_bu(1332076, 1300000, 0), 1300000)
	la("đối soát lớn hơn hoá đơn", P.can_bu(1332076, 1400000, 0), 1332076)
	la("đã bù cho hoá đơn khác", P.can_bu(1332076, 1400000, 1000000), 400000)
	la("không âm", P.can_bu(100, 50, 80), 0)
	la("phí ròng theo hoá đơn, hoàn phí trừ đúng hoá đơn", P.gop_phi([dict(sales_invoice="SI1", phi=100),
		dict(sales_invoice="SI1", phi=-30), dict(sales_invoice="", phi=49139)]), ({"SI1": 70}, [49139]))


@ca("v673 đặt phí: hoá đơn còn dư 131 thì trừ vào chính nó; đã thu qua hình thức thanh toán thì vào tài khoản chờ")
def _():
	si = [dict(si="SI1", phi=25000, du=210000, tk=None), dict(si="SI2", phi=20000, du=0, tk="1131 Grab")]
	kq = P.phan_bo(si, [], 45000, "1131 Grab")
	la("131 đúng hoá đơn", kq["ban"], [dict(si="SI1", so_tien=25000)])
	la("tài khoản chờ của hình thức", [(x["tai_khoan"], x["so_tien"]) for x in kq["tk"]], [("1131 Grab", 20000)])
	la("đủ", (kq["da_dat"], kq["thieu"]), (45000, 0))


@ca("v673 phí quảng cáo không gắn đơn: trừ vào hoá đơn khác của kỳ còn dư 131, rồi mới tài khoản chờ của đối tác")
def _():
	si = [dict(si="SI1", phi=10000, du=50000, tk=None), dict(si="SI2", phi=0, du=30000, tk=None)]
	kq = P.phan_bo(si, [49139], 59139, "1131 Grab")
	la("131", kq["ban"], [dict(si="SI1", so_tien=50000), dict(si="SI2", so_tien=9139)])
	la("không cần tài khoản", kq["tk"], [])
	kq = P.phan_bo([dict(si="SI1", phi=0, du=0, tk=None)], [49139], 49139, "1131 Grab")
	la("hết dư 131 thì vào tài khoản chờ đối tác", [(x["tai_khoan"], x["so_tien"]) for x in kq["tk"]], [("1131 Grab", 49139)])


@ca("v673 không biết phí nằm đâu (hết dư 131, hình thức chưa khai tài khoản chờ): báo thiếu đúng số, không đoán")
def _():
	kq = P.phan_bo([dict(si="SI1", phi=30000, du=10000, tk=None)], [5000], 35000, None)
	la("đặt được 10.000 vào 131", kq["ban"], [dict(si="SI1", so_tien=10000)])
	la("thiếu 25.000", kq["thieu"], 25000)
	la("không có dòng tài khoản đoán", kq["tk"], [])


@ca("v673 đặt đủ số được bù thì dừng: hoá đơn phí nhỏ hơn phí đối soát không bù quá hoá đơn")
def _():
	si = [dict(si="SI%d" % i, phi=1000, du=5000, tk=None) for i in range(5)]
	kq = P.phan_bo(si, [], 2500, None)
	la("đúng 2.500", sum(x["so_tien"] for x in kq["ban"]), 2500)
	la("theo thứ tự ngày", [x["si"] for x in kq["ban"]], ["SI0", "SI1", "SI2"])
	la("không thiếu", kq["thieu"], 0)
	la("can_bu 0 thì không đặt gì", P.phan_bo(si, [5], 0, "TK"), dict(ban=[], tk=[], da_dat=0, thieu=0, nguon={"si": {}, "khong": 0}))


@ca("v673 bảng kê căn cứ có đủ dòng đối soát, mở được bằng Excel (BOM UTF-8)")
def _():
	s = P.bang_ke_csv([dict(nguon="DSN-1", ngay="2026-10-03", loai="ban", ma_don="GF-1", sales_invoice="SI1", phi=25025)])
	dung("BOM", s.startswith("﻿"))
	dung("dòng", "DSN-1,2026-10-03,ban,GF-1,SI1,25025" in s)


# ------------------------------------------------------------ phần chạm hệ

class Doc(dict):
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v

	def set(self, k, v):
		self[k] = [Doc(x) for x in v]

	def is_new(self):
		return not self.get("name")


class Kho:
	"""Hoá đơn, tài khoản, dòng đối soát và phiếu cấn trừ trong bộ nhớ."""

	def __init__(self):
		self.pi = Doc(name="PI-GRAB-10", docstatus=1, is_return=0, currency="VND", company="CT", supplier="NC000056",
			supplier_name="CÔNG TY TNHH GRAB", outstanding_amount=44071417, posting_date="2026-10-06",
			bill_date="2026-10-06", bill_no="798888", credit_to="331 - CT", remarks="", items=[Doc(item_name="Phí dịch vụ", description="")])
		self.si = {}
		self.dong = []
		self.phieu = {}
		self.tk = {"331 - CT": "Payable", "131 - CT": "Receivable", "1131 - CT": "Temporary", "1121 - CT": "Bank"}
		self.pt_tk = {"GrabFood": "1131 - CT"}
		self.sql = []
		self.vai = {"Accounts User"}

	def them_si(self, ten, du, pt="GrabFood", debit="131 - CT", ngay="2026-09-10"):
		self.si[ten] = Doc(name=ten, company="CT", docstatus=1, outstanding_amount=du, debit_to=debit,
			vgb_pt_thanh_toan=pt, posting_date=ngay, customer="KH-GRAB")

	def db_sql(self, q, a=None, as_dict=False):
		self.sql.append(q)
		if "Vagabond Doi Soat Dong" in q:
			loai = a["loai"]
			return [Doc(x) for x in self.dong if x["loai"] in loai and a["tu"] <= x["ngay"] <= a["den"]]
		if "Vagabond Can Tru Ban" in q:
			# Đúng điều kiện câu thật: phiếu khác còn hiệu lực, chưa có bút toán.
			giu = {}
			for x in self.phieu.values():
				if x.docstatus >= 2 or x.get("but_toan") or x.name == a["tru"]:
					continue
				for b in x.get("ban") or []:
					if b.hoa_don in a["si"]:
						giu[b.hoa_don] = giu.get(b.hoa_don, 0) + b.so_tien
			return [Doc(hoa_don=k, so=v) for k, v in giu.items()]
		return []

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		if dt == "Sales Invoice":
			return [self.si[n] for n in filters["name"][1] if n in self.si]
		if dt == "Vagabond Can Tru San":
			ra = []
			for x in self.phieu.values():
				if "name" in filters and isinstance(filters["name"], list) and filters["name"][0] == "!=" and x.name == filters["name"][1]:
					continue
				if "name" in filters and filters["name"][0] == "in" and x.name not in filters["name"][1]:
					continue
				if filters.get("doi_soat") and (x.docstatus >= 2 or x.san != filters.get("san", x.san)
						or x.loai_phi != filters.get("loai_phi", x.loai_phi)):
					continue
				ra.append(x)
			return ra
		if dt == "Vagabond Can Tru Phi":
			return [x.name for x in self.phieu.values() if any(p.hoa_don == filters["hoa_don"] for p in x.phi)]
		return []

	def get_value(self, dt, name, f=None, as_dict=False, **k):
		if dt == "Account":
			if isinstance(f, list):
				return Doc(account_type=self.tk.get(name), is_group=0, disabled=0, company="CT", account_currency="VND")
			return self.tk.get(name)
		return None

	def chay(self, ham, *a, **kw):
		from vagabond import thu_tien
		with ExitStack() as st:
			p = lambda o, t, v: st.enter_context(patch.object(o, t, v, create=True))
			p(P.frappe, "get_roles", lambda *x: list(self.vai))
			p(P.frappe, "PermissionError", type("PermissionError", (Exception,), {}))
			p(P.frappe.db, "sql", self.db_sql)
			p(P.frappe.db, "get_value", self.get_value)
			p(P.frappe, "get_all", self.get_all)
			p(P.frappe, "get_doc", lambda dt, name=None: self.pi if dt == "Purchase Invoice" else self.phieu[name])
			p(P, "_chan_cty", lambda c: None)
			p(P, "_nhan_tk", lambda t: t)
			p(thu_tien, "tk_tien_thu", lambda ct, pt: (self.pt_tk.get(pt), None))
			return ham(*a, **kw)


def _dong(ngay, phi, si="", loai="ban", nguon="DSN-1", xn="2026-10-02"):
	return dict(name="D%s%s" % (ngay, si), nguon=nguon, ngay=ngay, loai=loai, ma_don="", phi=phi,
		sales_invoice=si, xac_nhan_luc=xn)


@ca("v673 đề xuất thật cho hoá đơn hoa hồng Grab 06/10: kỳ tháng 9, phí từ đối soát, 131 và tài khoản chờ, định khoản")
def _():
	k = Kho()
	k.them_si("SI1", 30000000)
	k.them_si("SI2", 0, pt="GrabFood")
	k.dong = [_dong("2026-09-10", 30000000, "SI1"), _dong("2026-09-11", 14071417, "SI2"), _dong("2026-10-01", 999, "SI9")]
	kq = k.chay(P.de_xuat, hoa_don="PI-GRAB-10")
	la("đối tác, loại, kỳ", (kq["doi_tac"], kq["loai"], kq["ky"]["tu"], kq["ky"]["den"]), ("grab", "don", "2026-09-01", "2026-09-30"))
	la("phí theo đối soát", kq["tong_doi_soat"], 44071417)
	la("bù đủ hoá đơn", (kq["can_bu"], kq["lech"]), (44071417, 0))
	dung("lập được", kq["lap_duoc"])
	la("định khoản", [(d["ve"], d["tk"], d["so"]) for d in kq["dinh_khoan"]],
		[("Nợ", "331 - CT", 44071417), ("Có", "131 - CT", 30000000), ("Có", "1131 - CT", 14071417)])


@ca("v673 không lập khi phí không đặt được; hình thức ghi thẳng ngân hàng không được coi là tài khoản chờ")
def _():
	k = Kho()
	k.pt_tk = {"GrabFood": "1121 - CT"}
	k.them_si("SI1", 0)
	k.dong = [_dong("2026-09-10", 44071417, "SI1")]
	kq = k.chay(P.de_xuat, hoa_don="PI-GRAB-10")
	dung("không lập", not kq["lap_duoc"])
	dung("nói rõ số và cách gỡ", "44.071.417" in kq["ly_do"] and "GrabFood" in kq["ly_do"])
	la("không có định khoản", kq["dinh_khoan"], [])
	nem("lap chặn", lambda: k.chay(P.lap, hoa_don="PI-GRAB-10"))


@ca("v673 không có dòng đối soát trong kỳ: nói rõ, không lập; vai không phải kế toán bị chặn")
def _():
	k = Kho()
	kq = k.chay(P.de_xuat, hoa_don="PI-GRAB-10")
	dung("lý do", "Chưa có dòng đối soát" in kq["ly_do"])
	k.vai = {"Purchase User"}
	nem("thu mua không lập", lambda: k.chay(P.de_xuat, hoa_don="PI-GRAB-10"))


@ca("v673 phí đã bù cho hoá đơn phí khác cùng kỳ không bù lần hai")
def _():
	k = Kho()
	k.them_si("SI1", 50000000)
	k.dong = [_dong("2026-09-10", 44071417, "SI1")]
	k.phieu["CTSAN-1"] = Doc(name="CTSAN-1", docstatus=1, doi_soat=1, san="GrabFood", loai_phi="Phí theo đơn",
		tong_bu=44000000, phi=[Doc(hoa_don="PI-KHAC")])
	kq = k.chay(P.de_xuat, hoa_don="PI-GRAB-10")
	la("chỉ còn 71.417", (kq["da_bu_truoc"], kq["can_bu"]), (44000000, 71417))


@ca("v673 lập phiếu: khoá hoá đơn phí TRƯỚC khi tính; phiếu đúng khuôn #262 (nháp, đã kiểm, một hoá đơn phí)")
def _():
	k = Kho()
	k.them_si("SI1", 50000000)
	k.dong = [_dong("2026-09-10", 44071417, "SI1")]
	tao = {}

	def new_doc(dt):
		d = Doc(doctype=dt, docstatus=0)
		d.insert = lambda: (tao.setdefault("ins", d), d.update(name="CTSAN-9", tong_bu=44071417))
		return d

	def file_doc(x):
		return NS(insert=lambda **kk: NS(name="F1", file_url="/private/files/bang-ke.csv"))
	with patch.object(P.frappe, "new_doc", new_doc, create=True), \
			patch.object(P.frappe.utils, "nowdate", lambda: "2026-11-18", create=True), \
			patch.object(P.frappe.utils, "getdate", lambda v: v, create=True), \
			patch.object(P.frappe.db, "set_value", lambda *a, **kk: None, create=True):
		get_doc = lambda dt, name=None: (file_doc(dt) if isinstance(dt, dict) else (k.pi if dt == "Purchase Invoice" else k.phieu[name]))
		with patch.object(P.frappe, "get_doc", get_doc, create=True):
			import contextlib
			with contextlib.ExitStack() as st:
				st.enter_context(patch.object(P.frappe, "get_roles", lambda *x: ["Accounts User"], create=True))
				st.enter_context(patch.object(P.frappe.db, "sql", k.db_sql, create=True))
				st.enter_context(patch.object(P.frappe.db, "get_value", k.get_value, create=True))
				st.enter_context(patch.object(P.frappe, "get_all", k.get_all, create=True))
				st.enter_context(patch.object(P, "_chan_cty", lambda c: None))
				from vagabond import thu_tien
				st.enter_context(patch.object(thu_tien, "tk_tien_thu", lambda ct, pt: (k.pt_tk.get(pt), None)))
				P.lap(hoa_don="PI-GRAB-10")
	la("câu đầu tiên là khoá hoá đơn phí", "for update" in k.sql[0] and "Purchase Invoice" in k.sql[0], True)
	d = tao["ins"]
	la("khuôn phiếu", (d.doi_soat, d.xac_nhan, d.san, d.loai_phi, d.ngay_bu, d.diem_ban), (1, 1, "GrabFood", "Phí theo đơn", "2026-11-18", ""))
	la("một hoá đơn phí", [(x.hoa_don, x.so_tien) for x in d.phi], [("PI-GRAB-10", 44071417)])
	la("bù vào SI1", [(x.hoa_don, x.so_tien) for x in d.ban], [("SI1", 44071417)])
	la("căn cứ là bảng kê", d.can_cu, "/private/files/bang-ke.csv")


@ca("v673 kỳ chưa hết thì không lập (đối soát của kỳ chưa đủ)")
def _():
	k = Kho()
	k.them_si("SI1", 50000000)
	k.dong = [_dong("2026-11-10", 100, "SI1")]
	with patch.object(P.frappe.utils, "nowdate", lambda: "2026-11-18", create=True), \
			patch.object(P.frappe.utils, "getdate", lambda v: v, create=True):
		try:
			k.chay(P.lap, hoa_don="PI-GRAB-10", doi_tac="grab", loai="don", tu="2026-11-01", den="2026-11-30")
			dung("phải chặn", False)
		except Exception as e:
			dung("chặn vì kỳ chưa hết, không phải lỗi khác", "chưa hết" in str(e))


def _phieu(**kk):
	d = Doc(name="CTSAN-9", company="CT", nha_cung_cap="NC000056", san="GrabFood", loai_phi="Phí theo đơn", doi_soat=1, tu_ngay="2026-09-01",
		den_ngay="2026-09-30", tong_bu=44071417, phi=[Doc(hoa_don="PI-GRAB-10", so_tien=44071417)],
		ban=[Doc(hoa_don="SI1", so_tien=30000000)], tk=[Doc(tai_khoan="1131 - CT", so_tien=14071417)])
	d.update(kk)
	return d


@ca("v673 kiểm phiếu ở mọi đường ghi (Desk sửa tay): hoá đơn bán ngoài đối soát, tài khoản lạ, bù vượt phí đều bị chặn")
def _():
	k = Kho()
	k.them_si("SI1", 30000000)
	k.them_si("SI2", 0)
	k.dong = [_dong("2026-09-10", 30000000, "SI1"), _dong("2026-09-11", 14071417, "SI2")]
	with patch.object(P.frappe.utils, "getdate", lambda v: v, create=True):
		d = _phieu()
		k.chay(P.kiem_phieu_doi_soat, d)
		la("ghi tổng đối soát", d.tong_doi_soat, 44071417)
		nem("hoá đơn bán ngoài đối soát", lambda: k.chay(P.kiem_phieu_doi_soat, _phieu(ban=[Doc(hoa_don="SI-LA", so_tien=30000000)])))
		nem("tài khoản ngân hàng", lambda: k.chay(P.kiem_phieu_doi_soat, _phieu(tk=[Doc(tai_khoan="1121 - CT", so_tien=14071417)])))
		nem("bù vượt phí đối tác đã giữ", lambda: k.chay(P.kiem_phieu_doi_soat, _phieu(tong_bu=44071418)))
		nem("hai hoá đơn phí", lambda: k.chay(P.kiem_phieu_doi_soat, _phieu(phi=[Doc(hoa_don="A", so_tien=1), Doc(hoa_don="B", so_tien=1)])))
		nem("đối tác lạ", lambda: k.chay(P.kiem_phieu_doi_soat, _phieu(san="BeFood")))


@ca("v673 bút toán cấn trừ có dòng tài khoản chờ: thu_bu thêm đúng vế Có, kiem_but_toan nhận đúng khuôn, sửa tay bị chặn")
def _():
	from vagabond import can_tru_san as C
	d = _phieu(docstatus=1, xac_nhan=1, but_toan=None, ngay_bu="2026-11-18", diem_ban="", mst="0312650437")
	pi = Doc(doctype="Purchase Invoice", name="PI-GRAB-10", docstatus=1, posting_date="2026-10-06", supplier="NC000056",
		credit_to="331 - CT", outstanding_amount=44071417, bill_no="798888", bill_date="2026-10-06", company="CT")
	si = Doc(doctype="Sales Invoice", name="SI1", docstatus=1, posting_date="2026-09-10", customer="KH-GRAB",
		debit_to="131 - CT", custom_hddt_so="123", outstanding_amount=30000000, company="CT")
	nguon = [(pi, d.phi[0], "credit_to"), (si, d.ban[0], "debit_to")]
	tao = {}

	class JE(Doc):
		def append(self, k, v):
			self.setdefault(k, []).append(Doc(v))

		def insert(self, **kk):
			tao["je"] = self
			self.name = "JE-1"

		def submit(self):
			pass
	with patch.object(C.frappe.db, "sql", lambda *a, **kk: [], create=True), \
			patch.object(C.frappe, "get_doc", lambda dt, name=None: d, create=True), \
			patch.object(C.frappe, "get_all", lambda *a, **kk: [], create=True), \
			patch.object(C.frappe, "new_doc", lambda dt: JE(), create=True), \
			patch.object(C, "_doc_nguon", lambda dd, khoa=True: nguon), \
			patch.object(C, "_doi_trang_thai", lambda dd, tt, ly_do="", but_toan=None: tao.update(tt=tt)):
		C.thu_bu("CTSAN-9")
		je = tao["je"]
		la("ba dòng", [(x.account, x.debit_in_account_currency, x.credit_in_account_currency, x.get("party") or "")
			for x in je.accounts], [("331 - CT", 44071417.0, 0, "NC000056"), ("131 - CT", 0, 30000000.0, "KH-GRAB"),
			("1131 - CT", 0, 14071417.0, "")])
		la("đã cấn trừ", tao["tt"], "Đã cấn trừ")
		d.but_toan = None
		with patch.object(C.frappe, "flags", NS(get=lambda k: "CTSAN-9"), create=True):
			je.vgb_can_tru_san, je.company, je.posting_date = "CTSAN-9", "CT", "2026-11-18"
			with patch.object(C, "getdate", lambda v: v):
				C.kiem_but_toan(je)
				je.accounts[2].account = "1121 - CT"
				nem("sửa tay vế Có bị chặn", lambda: C.kiem_but_toan(je))


@ca("v673 kiem_phieu: phiếu từ đối soát không cần điểm bán, khách; tổng phí bằng 131 cộng tài khoản; phiếu tay vẫn như cũ")
def _():
	from vagabond import can_tru_san as C
	goi = []
	with patch.object(C.frappe.db, "get_value", lambda dt, n, f=None, **kk: "VND" if dt == "Company" else "0312650437", create=True), \
			patch.object(C, "_doc_nguon", lambda dd, khoa=True: []), \
			patch.object(C, "getdate", lambda v: v), \
			patch.object(P, "kiem_phieu_doi_soat", lambda dd: goi.append(dd.name)):
		d = _phieu(ngay_bu="2026-11-18", diem_ban="", khach_hang=None, tham_chieu="DS", amended_from=None, docstatus=0)
		C.kiem_phieu(d)
		la("tổng bù", d.tong_bu, 44071417.0)
		la("gọi kiểm đối soát", goi, ["CTSAN-9"])
		nem("lệch tổng", lambda: C.kiem_phieu(_phieu(ngay_bu="2026-11-18", tham_chieu="DS", amended_from=None, docstatus=0,
			tk=[Doc(tai_khoan="1131 - CT", so_tien=1)])))
		tay = _phieu(doi_soat=0, ngay_bu="2026-11-18", tham_chieu="DS", amended_from=None, docstatus=0, diem_ban="SALES",
			khach_hang="KH", ban=[Doc(hoa_don="SI1", so_tien=44071417)], tk=[Doc(tai_khoan="1131 - CT", so_tien=1)],
			tong_bu=0)
		with patch("vagabond.diem_ban.theo_ma", lambda m: True, create=True):
			nem("phiếu tay không dùng dòng tài khoản", lambda: C.kiem_phieu(tay))
		la("tay không gọi kiểm đối soát", goi, ["CTSAN-9"])
	dung("Decimal", isinstance(C.tong_tk([Doc(tai_khoan="A", so_tien=1)]), Decimal))


# ------------------------------------------------------------ Codex #589 vòng 1 (gộp vào #590)

def _kho_hai_si(du1=1000, du2=1000):
	k = Kho()
	k.pi.update(outstanding_amount=100, name="PI-GRAB-11")
	k.them_si("SI1", du1, ngay="2026-09-10")
	k.them_si("SI2", du2, ngay="2026-09-11")
	k.dong = [_dong("2026-09-10", 100, "SI1"), _dong("2026-09-11", 100, "SI2")]
	return k


def _phieu_cu(k, docstatus, but_toan, ban, nguon):
	k.phieu["CTSAN-1"] = Doc(name="CTSAN-1", docstatus=docstatus, doi_soat=1, san="GrabFood", loai_phi="Phí theo đơn",
		tu_ngay="2026-09-01", den_ngay="2026-09-30", tong_bu=sum(x[1] for x in ban), but_toan=but_toan,
		phi=[Doc(hoa_don="PI-GRAB-10", so_tien=sum(x[1] for x in ban))], ban=[Doc(hoa_don=a, so_tien=b) for a, b in ban],
		tk=[], nguon_phi=nguon)


@ca("Codex #589: hai hoá đơn phí cùng kỳ: phiếu thứ hai bù vào SI2, không bù lại SI1 (phiếu đầu đã ghi sổ hoặc còn nháp giữ phần dư)")
def _():
	import json as _j
	for ten, ds, bt, du1 in (("đã ghi sổ", 1, "JE-1", 900), ("còn nháp", 0, None, 1000), ("chờ đối soát", 1, None, 1000)):
		k = _kho_hai_si(du1=du1)
		_phieu_cu(k, ds, bt, [("SI1", 100)], _j.dumps({"si": {"SI1": 100}, "khong": 0}))
		kq = k.chay(P.de_xuat, hoa_don="PI-GRAB-11", doi_tac="grab", loai="don", tu="2026-09-01", den="2026-09-30")
		la("phiếu đầu %s: phiếu hai Có SI2" % ten, [(d["ve"], d["so"]) for d in kq.get("dinh_khoan") or []], [("Nợ", 100), ("Có", 100)])
		t = k.chay(P._tinh, k.pi, "grab", "don", "2026-09-01", "2026-09-30")
		la("phiếu đầu %s: đúng hoá đơn SI2" % ten, t["pb"]["ban"], [dict(si="SI2", so_tien=100)])


@ca("Codex #589: phiếu nháp giữ dư 131 của một hoá đơn bán: phiếu khác không dùng lại phần dư đó")
def _():
	import json as _j
	k = _kho_hai_si(du1=100, du2=0)
	k.dong = [_dong("2026-09-10", 100, "SI1"), _dong("2026-09-11", 100, "SI2")]
	k.pt_tk = {"GrabFood": None}
	_phieu_cu(k, 0, None, [("SI1", 100)], _j.dumps({"si": {"SI1": 100}, "khong": 0}))
	t = k.chay(P._tinh, k.pi, "grab", "don", "2026-09-01", "2026-09-30")
	la("SI1 đã bị phiếu nháp giữ hết, SI2 hết dư: báo thiếu, không Có SI1 lần hai", (t["pb"]["ban"], t["pb"]["thieu"]), ([], 100))


@ca("Codex #589: sửa phiếu trên Desk khác phân bổ theo đối soát (Có SI1 200 thay vì mỗi tờ 100) bị chặn; đúng phân bổ thì qua và ghi nguồn phí")
def _():
	import json as _j
	k = _kho_hai_si(du1=1000, du2=1000)
	k.pi.update(outstanding_amount=200)
	with patch.object(P.frappe.utils, "getdate", lambda v: v, create=True):
		sai = _phieu(tong_bu=200, phi=[Doc(hoa_don="PI-GRAB-11", so_tien=200)], ban=[Doc(hoa_don="SI1", so_tien=200)], tk=[])
		nem("Có SI1 toàn bộ bị chặn", lambda: k.chay(P.kiem_phieu_doi_soat, sai))
		dung_pb = _phieu(tong_bu=200, phi=[Doc(hoa_don="PI-GRAB-11", so_tien=200)],
			ban=[Doc(hoa_don="SI1", so_tien=100), Doc(hoa_don="SI2", so_tien=100)], tk=[])
		k.chay(P.kiem_phieu_doi_soat, dung_pb)
		la("ghi nguồn phí từ máy chủ", _j.loads(dung_pb.nguon_phi), {"si": {"SI1": 100, "SI2": 100}, "khong": 0})


@ca("Codex #589: phí quảng cáo không gắn hoá đơn trừ vào hoá đơn bán còn dư của đối tác trong kỳ, không báo thiếu, không chuyển thẳng tài khoản chờ")
def _():
	k = Kho()
	k.pi.update(outstanding_amount=100, name="PI-GRAB-QC", remarks="Phí dịch vụ quảng cáo tháng 09/2026")
	k.them_si("SI1", 1000, ngay="2026-09-10")
	k.dong = [_dong("2026-09-10", 25, "SI1"), _dong("2026-09-30", 100, "", loai="phi_ky")]
	for tk_dt, ten in ((None, "chưa khai tài khoản chờ"), ("1131 - CT", "đã khai tài khoản chờ")):
		k.pt_tk = {"GrabFood": tk_dt}
		t = k.chay(P._tinh, k.pi, "grab", "ky", "2026-09-01", "2026-09-30")
		la("%s: Có SI1 100" % ten, (t["pb"]["ban"], t["pb"]["tk"], t["pb"]["thieu"]), ([dict(si="SI1", so_tien=100)], [], 0))
	with patch.object(P.frappe.utils, "getdate", lambda v: v, create=True):
		d = _phieu(loai_phi="Phí kỳ, quảng cáo", tong_bu=100, phi=[Doc(hoa_don="PI-GRAB-QC", so_tien=100)],
			ban=[Doc(hoa_don="SI1", so_tien=100)], tk=[])
		k.chay(P.kiem_phieu_doi_soat, d)
		la("Desk nhận hoá đơn bán của đối tác cho phí kỳ", d.tong_doi_soat, 100)


@ca("Codex #589: bảng Hoá đơn bán không bắt buộc ở cấp doctype (phiếu chỉ có tài khoản chờ lưu được); phiếu tay vẫn bắt có hoá đơn bán")
def _():
	import json as _j
	import os
	from vagabond import can_tru_san as C
	p = os.path.join(os.path.dirname(P.__file__), "vagabond", "doctype", "vagabond_can_tru_san", "vagabond_can_tru_san.json")
	f = {x["fieldname"]: x for x in _j.load(open(p, encoding="utf-8"))["fields"]}
	la("ban không reqd cứng", (f["ban"].get("reqd", 0), f["ban"].get("mandatory_depends_on")), (0, "eval:!doc.doi_soat"))
	dung("có ô nguồn phí ẩn, chỉ đọc", f.get("nguon_phi", {}).get("hidden") == 1 and f["nguon_phi"].get("read_only") == 1)
	nem("phiếu tay không hoá đơn bán", lambda: C.tong_dong([]))
