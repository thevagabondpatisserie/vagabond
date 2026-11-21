# -*- coding: utf-8 -*-
"""v680: mã chứng từ chung MÃ-yymmdd-nnnnnn từ 01/12/2026 (anh Việt 21/11/2026).

Số liên tục theo tiền tố, sáu chữ số, không đánh lại mỗi ngày. Trước
01/12/2026 không đổi gì. Phiếu cũ giữ mã cũ.
"""

import frappe

from vagabond import ma_chung_tu as mct
from vagabond import ma_phieu_sx as mps
from vagabond.khung.kiem_thu.nen import ca, dung, la


class _Doc(object):
	def __init__(self, doctype, naming_series=None, name=None):
		self.doctype = doctype
		self.naming_series = naming_series
		self.name = name

	def get(self, k, md=None):
		return getattr(self, k, md)


def _chay(doc, ngay="2026-12-01", so=(1, 2, 3, 4, 5, 6), co_san=()):
	"""Chạy hook với ba cửa chạm hệ giả: ngày, bộ đếm, bảng đã có mã nào."""
	dem = {}
	day = list(so)
	goc = (mct._hom_nay, mct.cap_so, getattr(frappe.db, "exists", None), frappe.log_error)
	loi = []

	def cap(tt):
		dem[tt] = dem.get(tt, 0) + 1
		return day.pop(0)

	mct._hom_nay = lambda: ngay
	mct.cap_so = cap
	frappe.db.exists = lambda dt, f=None: (f or {}).get("name") in co_san if isinstance(f, dict) else False
	frappe.log_error = lambda *a, **k: loi.append(a)
	try:
		mct.dat_ten(doc)
	finally:
		mct._hom_nay, mct.cap_so, ex, frappe.log_error = goc
		if ex is None:
			del frappe.db.exists
		else:
			frappe.db.exists = ex
	return doc.name, dem, loi


@ca("mã chung v680: khuôn TIỀN TỐ-yymmdd-sáu số, qua 999999 thì dài ra")
def _():
	la("hoá đơn bán đầu tiên", mct.ma("HDB", "2026-12-01", 1), "HDB-261201-000001")
	la("năm-tháng-ngày", mct.yymmdd("2027-01-09"), "270109")
	la("số lớn", mct.ma("PXD", "2026-12-31", 1234567), "PXD-261231-1234567")
	for rac in (0, -1, None, "abc"):
		try:
			mct.duoi(rac)
			dung("số rác %r phải ném lỗi" % (rac,), False)
		except (ValueError, TypeError):
			pass


@ca("mã chung v680: mốc 01/12/2026, ngày 30/11 vẫn kiểu cũ")
def _():
	la("30/11", mct.da_ap("2026-11-30"), False)
	la("01/12", mct.da_ap("2026-12-01"), True)
	la("năm sau", mct.da_ap("2027-03-04"), True)


@ca("mã chung v680: tiền tố lấy từ chuỗi naming_series, bỏ chuỗi gốc ERPNext")
def _():
	for chuoi, tt in (
		("HDB-.YY.-.MM.-.#####", "HDB"), ("PXD-.YYYY.-", "PXD"), ("PCV-.#####", "PCV"),
		("APP-.YY.-.MM.-.###", "APP"), ("KK-.YY.-.#####", "KK"), ("YCSX-.YYYY.-", "YCSX"),
		("ACC-SINV-.YYYY.-", ""), ("MAT-STE-.YYYY.-", ""), ("", ""), (None, ""),
		("SAL-ORD-.YYYY.-", ""), ("hdb-.YY.-", "HDB"),
	):
		la("chuỗi %r" % (chuoi,), mct.tien_to_tu_chuoi(chuoi), tt)


@ca("mã chung v680: trước 01/12/2026 hook không đụng, Frappe đặt như cũ")
def _():
	ten, dem, _ = _chay(_Doc("Sales Invoice", "HDB-.YY.-.MM.-.#####"), ngay="2026-11-30")
	la("chưa đặt tên", ten, None)
	la("không tốn số", dem, {})


@ca("mã chung v680: từ 01/12/2026 hoá đơn bán ra HDB-yymmdd-sáu số, số nối tiếp qua ngày")
def _():
	ten, dem, _ = _chay(_Doc("Sales Invoice", "HDB-.YY.-.MM.-.#####"), so=(41,))
	la("ngày đầu", ten, "HDB-261201-000041")
	la("đếm theo tiền tố", dem, {"HDB": 1})
	ten, _, _ = _chay(_Doc("Sales Invoice", "HDB-.YY.-.MM.-.#####"), ngay="2026-12-02", so=(42,))
	la("sang ngày số không về 1", ten, "HDB-261202-000042")


@ca("mã chung v680: phiếu kho và phiếu yêu cầu lấy tiền tố Server Script đã chọn")
def _():
	la("xuất dùng", _chay(_Doc("Stock Entry", "PXD-.YYYY.-"))[0], "PXD-261201-000001")
	la("điều chuyển", _chay(_Doc("Stock Entry", "PDC-.YYYY.-"))[0], "PDC-261201-000001")
	la("yêu cầu sản xuất", _chay(_Doc("Material Request", "YCSX-.YYYY.-"))[0], "YCSX-261201-000001")
	la("kiểm kê app", _chay(_Doc("Phieu Kiem Ke", "KK-.YY.-.#####"))[0], "KK-261201-000001")


@ca("mã chung v680: phiếu của app dùng tiền tố cố định")
def _():
	la("phiếu quỹ", _chay(_Doc("Vagabond Phieu Quy"))[0], "PQ-261201-000001")
	la("vận đơn", _chay(_Doc("Van Don"))[0], "VD-261201-000001")
	la("hoàn tiền", _chay(_Doc("Vagabond Hoan Tien"))[0], "HT-261201-000001")


@ca("mã chung v680: đã có tên (bản sửa đổi, nhập dữ liệu) thì không đụng")
def _():
	ten, dem, _ = _chay(_Doc("Sales Invoice", "HDB-.YY.-.MM.-.#####", name="HDB-26-11-03963-1"))
	la("giữ tên bản sửa", ten, "HDB-26-11-03963-1")
	la("không tốn số", dem, {})


@ca("mã chung v680: doctype ngoài danh sách và chuỗi gốc ERPNext thì không đụng")
def _():
	la("Customer", _chay(_Doc("Customer", "KL-"))[0], None)
	la("Work Order đi hook riêng", _chay(_Doc("Work Order", "LSX-.YY.-.MM.-.####"))[0], None)
	la("đơn web giữ DW", _chay(_Doc("Vagabond Don Web"))[0], None)
	la("chuỗi ERPNext gốc", _chay(_Doc("Sales Invoice", "ACC-SINV-.YYYY.-"))[0], None)


@ca("mã chung v680: mã vừa cấp đã có người mang thì lấy số kế tiếp")
def _():
	ten, _, _ = _chay(_Doc("Sales Invoice", "HDB-.YY.-"), so=(7, 8), co_san=("HDB-261201-000007",))
	la("nhảy số", ten, "HDB-261201-000008")


@ca("mã chung v680: cấp số hỏng thì ghi lỗi và để Frappe đặt như cũ, quầy không đứng")
def _():
	d = _Doc("Sales Invoice", "HDB-.YY.-")
	ten, _, loi = _chay(d, so=())
	la("trả tên rỗng cho Frappe", ten, None)
	la("có ghi lỗi", len(loi), 1)


@ca("mã chung v680: hồ sơ APP và phiếu chi APP chung MỘT dòng đếm")
def _():
	la("phiếu chi", mct.tien_to_cua(_Doc("Payment Entry", "APP-.YY.-.MM.-.###")), "APP")
	la("cùng khoá", mct.khoa("APP"), "VGBMA-APP")
	from vagabond import ho_so_tt

	goc = mct.cap_ma
	goi = []
	mct.cap_ma = lambda tt, dt, ngay=None, truong="name": goi.append((tt, dt, str(ngay), truong)) or "APP-261201-000077"
	try:
		la("hồ sơ từ mốc", ho_so_tt._sinh_ma("2026-12-01"), "APP-261201-000077")
	finally:
		mct.cap_ma = goc
	la("cấp theo tiền tố APP, dò trùng ở ô mã", goi, [("APP", "Vagabond Ho So TT", "2026-12-01", "ma")])


@ca("mã chung v680: danh sách doctype MỘT nguồn, hooks nối autoname cho đủ và không mất hook cũ")
def _():
	from vagabond import hooks

	for dt in tuple(mct.DT_THEO_CHUOI) + tuple(mct.DT_TIEN_TO):
		h = hooks.doc_events.get(dt, {}).get("autoname")
		h = [h] if isinstance(h, str) else list(h or [])
		la("%s có hook" % dt, h.count("vagabond.ma_chung_tu.dat_ten"), 1)
	la("lệnh sản xuất giữ hook riêng", hooks.doc_events["Work Order"]["autoname"], "vagabond.ma_phieu_sx.dat_ten_lenh")
	dung("dựng dòng đếm sau migrate", "vagabond.ma_chung_tu.dung" in hooks.after_migrate)
	dung("không gắn vào doctype ngoài danh sách", "autoname" not in hooks.doc_events.get("Vagabond Don Web", {}))


@ca("mã chung v680: lệnh sản xuất đổi phần ngày sang yymmdd, đọc ngày cả hai kiểu")
def _():
	la("01/12", mps.ma_lenh("2026-12-01", 700), "LSX-261201-000700")
	hn = "2026-12-01"
	la("mã cũ ddmmyy", mps.ngay_tao_trong_ma("LSX-281026-000600", "LSX", hn), "2026-10-28")
	la("mã cũ đầu tiên", mps.ngay_tao_trong_ma("LSX-060926-000057", "LSX", hn), "2026-09-06")
	la("mã mới yymmdd", mps.ngay_tao_trong_ma("LSX-261201-000700", "LSX", hn), "2026-12-01")
	la("mã mới năm sau", mps.ngay_tao_trong_ma("LSX-270315-000900", "LSX", "2027-03-20"), "2027-03-15")
	# 27/10/2026 cũ và 26/10/2027 mới cùng chuỗi 271026: tới khi 26/10/2027 đã qua
	# thì hai cách đọc cùng đúng, không đoán.
	la("trước 26/10/2027 chỉ là mã cũ", mps.ngay_tao_trong_ma("LSX-271026-000900", "LSX", "2027-01-01"), "2026-10-27")
	la("hai cách đọc cùng đúng thì không đoán", mps.ngay_tao_trong_ma("LSX-271026-000900", "LSX", "2027-11-01"), "")
	dung("mã mới vẫn là kiểu mới", mps.la_ma_kieu_moi("LSX-261201-000700", "LSX"))


@ca("mã chung v680: nhận đúng mã mới, không nhận kiểu cũ")
def _():
	dung("HDB mới", mct.la_ma_moi("HDB-261201-000001", "HDB"))
	dung("APP mới, đuôi dài", mct.la_ma_moi("APP-261201-1000000"))
	dung("HDB tháng cũ", not mct.la_ma_moi("HDB-26-11-03963"))
	dung("PXD năm cũ", not mct.la_ma_moi("PXD-2026-03322"))
	dung("ngày không có thật", not mct.la_ma_moi("HDB-261341-000001"))
	dung("sai tiền tố", not mct.la_ma_moi("HDB-261201-000001", "HDM"))


@ca("mã chung v680: các chỗ dò mã trong chữ nhận cả kiểu mới")
def _():
	from vagabond import hoan_tien, khop_sao_ke, tin_ban_hang, trang_thai_thu

	la("mã hoá đơn trong nội dung hoàn tiền",
		hoan_tien.RX_MA_HD.findall("HOAN TIEN HDB-261201-000123 KHACH"), ["HDB-261201-000123"])
	la("mã chứng từ trong thư", trang_thai_thu.MAU_MA.findall("Đơn DMH-261201-000146 gửi NCC, DMH-2026-00133-1"),
		["DMH-261201-000146", "DMH-2026-00133-1"])
	dung("sao kê mang mã APP mới của hồ sơ khác",
		khop_sao_ke.co_ma_app_khac("WATER APP261201000099 TT", "APP-261201-000100"))
	dung("sao kê giữ nguyên gạch của mã APP mới của hồ sơ khác",
		khop_sao_ke.co_ma_app_khac("WATER APP-261201-000099 TT", "APP-261201-000100"))
	dung("sao kê mang đúng mã APP mới của mình",
		not khop_sao_ke.co_ma_app_khac("WATER APP261201000100 TT", "APP-261201-000100"))
	dung("vẫn nhận mã APP cũ", khop_sao_ke.co_ma_app_khac("WATER BT APP.26.09.999", "APP.26.09.100"))
	for ma in ("HDB-261201-000123", "HDB-26-10-04205"):
		loi = ("Chưa tạo được hoá đơn Chờ ký trên m-invoice. Chi tiết: ['%s: Mã chưa rõ 9999 "
			"[a@b] địa chỉ email không hợp lệ Nội dung: x']" % ma)
		la("tin lỗi m-invoice bỏ mã %s ở đầu" % ma, tin_ban_hang.chi_tiet_hd_sai(loi),
			"[a@b] địa chỉ email không hợp lệ")


@ca("mã chung v680: báo giá từ mốc theo chuẩn chung, mẫu và bản thương lượng giữ cách cũ")
def _():
	import os

	p = os.path.join(os.path.dirname(mct.__file__), "vagabond", "doctype", "bao_gia_ban_hang", "bao_gia_ban_hang.py")
	src = open(p, encoding="utf-8").read()
	than = src.split("def autoname(self):")[1].split("\n\tdef ")[0]
	i_v = than.find('self.get("goc")')
	i_mau = than.find('self.get("la_mau")')
	i_moi = than.find("_ma_moi()")
	dung("bản thương lượng xét trước", 0 <= i_v < i_moi)
	dung("mẫu xét trước", 0 <= i_mau < i_moi)
	dung("cấp qua ma_chung_tu", 'ma_chung_tu.cap_ma("VGB-PQ", "Bao Gia Ban Hang")' in than)


@ca("mã chung v680: phiếu thu hợp đồng từ mốc theo chuẩn chung")
def _():
	import datetime

	from vagabond import thu_hop_dong as thd

	goc = (mct.cap_ma, thd.getdate)
	goi = []
	mct.cap_ma = lambda tt, dt, ngay=None, truong="name": goi.append((tt, dt)) or "PTHD-261201-000003"
	thd.getdate = lambda *a: datetime.date(2026, 12, 1)
	try:
		la("mã mới", thd._sinh_ma(), "PTHD-261201-000003")
	finally:
		mct.cap_ma, thd.getdate = goc
	la("tiền tố và doctype", goi, [("PTHD", thd.DT)])


@ca("mã chung v680 (Codex #602): nội dung chuyển khoản hồ sơ APP mới qua tới chặn mã APP khác")
def _():
	from types import SimpleNamespace as NS

	from vagabond import ho_so_tt, khop_sao_ke

	def nd(ten):
		return ho_so_tt._noi_dung_ck(NS(name=ten, loai="NCC", dong=[NS(so_hd_ncc="26957", hoa_don=None)],
			ten_nhan="Cong ty A", ten_ncc="", nha_cung_cap=""))

	cua_khac = nd("APP-261201-000099")
	dung("nội dung có mã hồ sơ: " + cua_khac, "APP" in cua_khac and "261201" in cua_khac)
	dung("dòng của hồ sơ khác bị loại khi đối chiếu hồ sơ của mình",
		khop_sao_ke.co_ma_app_khac(cua_khac, "APP-261201-000100"))
	dung("dòng của chính mình không bị loại", not khop_sao_ke.co_ma_app_khac(nd("APP-261201-000100"), "APP-261201-000100"))
	dung("dòng có khoảng trắng do ngân hàng tách",
		khop_sao_ke.co_ma_app_khac("TT APP 261201 000099 CTY A", "APP-261201-000100"))
	dung("dạng cũ có dấu chấm vẫn nhận", khop_sao_ke.co_ma_app_khac(nd("APP.26.11.099"), "APP.26.11.100"))
	dung("dạng cũ có khoảng trắng", khop_sao_ke.co_ma_app_khac("TT APP 26 11 099", "APP.26.11.100"))


@ca("mã chung v680: đọc mã hoá đơn mới trong dòng sao kê dù ngân hàng tách bằng khoảng trắng hay viết liền")
def _():
	from vagabond import hoan_tien

	for mo_ta in ("THE VAGABOND HOAN TIEN HDB-261201-000123", "THE VAGABOND HOAN TIEN HDB 261201 000123",
			"THE VAGABOND HOAN TIEN HDB261201000123"):
		la(mo_ta, hoan_tien.tim_ma_hoa_don(mo_ta), "HDB-261201-000123")
	la("dạng tháng cũ giữ nguyên", hoan_tien.tim_ma_hoa_don("HOAN TIEN HDB-26-11-03963"), "HDB-26-11-03963")
	la("số dài hơn không bị cắt", hoan_tien.tim_ma_hoa_don("HOAN TIEN HDB 261201 1000000"), "HDB-261201-1000000")
	la("không có mã", hoan_tien.tim_ma_hoa_don("HOAN TIEN 261201000123"), "")


@ca("mã chung v680: tin Tiền ra chưa có chứng từ xếp dòng mang mã APP mới vào nhóm trả nhà cung cấp")
def _():
	from vagabond import tien_chua_chung_tu as t

	for mo_ta in ("TT APP-261201-000099 CTY A", "TT APP 261201 000099 CTY A", "TT APP261201000099", "TT APP.26.11.027"):
		nhom = t.nhom_cua(mo_ta, t.NHOM_RA)
		la(mo_ta, nhom, "ncc")
