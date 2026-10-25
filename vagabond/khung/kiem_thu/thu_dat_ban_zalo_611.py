# -*- coding: utf-8 -*-
"""v611: màn Thông tin đặt bàn, tin Zalo thay thư nội bộ, chặn email hoá đơn sai.

Anh Việt 25/10/2026 duyệt:
  - bill Pancake 95914 (HDB-26-10-04205) nằm nháp ba ngày vì email nhận hoá đơn
    "_quynhntm@ocb.com.vn": chặn ngay lúc nhập, và khi m-invoice chê thông tin
    người mua thì báo Zalo nhóm Bán hàng & Sales;
  - Tài nhận YCDC-2026-00059 thì ERPNext ném câu dịch máy "Tỷ giá định giá ...
    là bắt buộc" vì Kho tổng 307 chưa có BTP: thay bằng câu dễ hiểu, báo Zalo Kho;
  - bốn tin mới: nhận hàng thiếu tồn, tiền chưa gắn chứng từ, YCDC treo, đặt bàn
    còn 3 giờ chưa xác nhận; tin YCSX cho bếp thay thư Notification;
  - màn Thông tin đặt bàn: Xác nhận (email khách theo mẫu đã duyệt + Zalo), Huỷ có
    lý do, Khách đã đến.

Các ca chạy hàm THẬT trên lớp Frappe giả, kênh Zalo giả ghi lại lời gọi; không
gọi thêm hàm nào ngoài chuỗi máy chạy (điều 15).
"""

import ast
import datetime as dt
import io
import os
import re
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test" + (a[0] if a else "")
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import dat_ban as db  # noqa: E402
from vagabond import dat_ban_thu as dbt  # noqa: E402
from vagabond import hoa_don_vat as hdv  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import tin_ban_hang as tbh  # noqa: E402
from vagabond import tin_kho as tk  # noqa: E402
from vagabond.patches import v611_tat_thu_noi_bo as p611  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v

	def as_dict(self):
		return dict(self)


def _zalo(chet=False):
	goi = []

	def ghi(loai, chu_de, tieu_de, dong=None, **kw):
		goi.append(D(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=list(dong or [])))
		return ["ZL-1"]
	return types.SimpleNamespace(bao=ghi, bao_hoac_ghi_loi=ghi, cat_dong=kz.cat_dong, chet_giao_dich=lambda e: chet), goi


# Câu lỗi thật đọc trong Error Log site ngày 25/10/2026 (bill 95914).
LOI_95914 = ("Đơn HDB-26-10-04205 chưa ghi sổ: Chưa tạo được hoá đơn Chờ ký trên m-invoice cho đơn này. "
	"Chi tiết: ['HDB-26-10-04205: Mã chưa rõ 9999 [_quynhntm@ocb.com.vn] địa chỉ email không hợp lệ "
	"Nội dung: {\"ok\": false}']")


# ------------------------------------------------------------ email hoá đơn

@ca("v611 email hoá đơn: chặn đúng ca 95914 và lỗi gõ thường gặp, không chặn email thật")
def _email():
	sai = ["_quynhntm@ocb.com.vn", "quynhntm.@ocb.com.vn", "a..b@ocb.com.vn", "ten @congty.com", "ten@congty",
		"ten@congty.c", "ten@@congty.com", "ten@.congty.com", "a@b.vn; c_@d.com"]
	for e in sai:
		dung("chặn %r" % e, bool(hdv.loi_email_hd(e)))
	dung("câu báo nêu đúng địa chỉ sai", '"_quynhntm@ocb.com.vn"' in hdv.loi_email_hd("_quynhntm@ocb.com.vn"))
	dung("câu báo không dấu gạch dài", not re.search("[\u2013\u2014]", hdv.loi_email_hd("_a@b.com")))
	dung_ = ["quynhntm@ocb.com.vn", "ke.toan_01@cong-ty.com.vn", "A.B+hd@Gmail.com", "x@y.io",
		"a@b.vn; c@d.com", "a@b.vn, c@d.com", "", None, "  "]
	for e in dung_:
		la("cho qua %r" % e, hdv.loi_email_hd(e), "")


@ca("v611 email hoá đơn: hai cửa nhập (Sales sửa bill, khách tự điền) đều chặn trước khi lưu")
def _email_cua():
	src = io.open(os.path.join(GOI, "ban_hang.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	for ten, truoc in (("luu_xhd", "sach_dia_chi_xhd"), ("xhd_khach_luu", "sach_dia_chi_xhd")):
		h = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten][0]
		than = ast.get_source_segment(src, h)
		i, j = than.find("loi_email_hd("), than.find(truoc)
		dung("%s gọi loi_email_hd trước khi lưu" % ten, 0 < i < j)


# ------------------------------------------------ tin thông tin hoá đơn sai

@ca("v611 hoá đơn sai: đọc đúng phần m-invoice chê, lỗi khác không báo Sales")
def _chi_tiet():
	ct = tbh.chi_tiet_hd_sai(LOI_95914)
	la("chi tiết ca 95914", ct, "[_quynhntm@ocb.com.vn] địa chỉ email không hợp lệ")
	la("lỗi mạng m-invoice không báo", tbh.chi_tiet_hd_sai(
		"Chưa tạo được hoá đơn Chờ ký trên m-invoice. Chi tiết: ['HDB-1: ReadTimeout']"), "")
	la("lỗi không phải m-invoice không báo", tbh.chi_tiet_hd_sai("Không đủ tồn kho cho BTP"), "")
	la("rỗng", tbh.chi_tiet_hd_sai(None), "")


@ca("v611 hoá đơn sai: báo nhóm Bán hàng đúng mã, một đơn một tin mỗi ngày, có đơn và cách sửa")
def _bao_hd_sai():
	gia, goi = _zalo()
	si = D(name="HDB-26-10-04205", custom_pancake_display_id="95914", grand_total=1240000,
		vgb_xhd_ten="NGÂN HÀNG TMCP PHƯƠNG ĐÔNG", vgb_xhd_mst="0300852005")
	with um.patch.object(tbh, "kenh_zalo", gia), um.patch.object(tbh, "nowdate", lambda: "2026-10-25"):
		tbh.bao_thong_tin_hd_sai(si, LOI_95914)
		tbh.bao_thong_tin_hd_sai(si, "Chưa tạo được hoá đơn Chờ ký trên m-invoice. Chi tiết: ['x: timeout']")
	la("đúng một tin (lỗi mạng im)", [(g.ma_tin, g.loai, g.khoa) for g in goi],
		[("bh_thong_tin_hd_sai", "canh_bao", "hd-sai:HDB-26-10-04205:2026-10-25")])
	chu = "\n".join(goi[0].dong)
	for x in ("95914", "1.240.000 đ", "0300852005", "địa chỉ email không hợp lệ", "Thông tin xuất hoá đơn"):
		dung("tin có %r" % x, x in chu)


@ca("v611 hoá đơn sai: cửa ghi sổ gọi báo SAU khi đã lùi giao dịch hỏng, rồi commit để tin còn lại")
def _hd_sai_cho_goi():
	src = io.open(os.path.join(GOI, "ban_hang.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	h = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_ghi_so_mot_don"][0]
	than = ast.get_source_segment(src, h)
	i, j, k = than.find("frappe.db.rollback()"), than.find("bao_thong_tin_hd_sai("), than.find("frappe.db.commit()", than.find("bao_thong_tin_hd_sai("))
	dung("rollback trước, báo sau, commit sau báo", 0 < i < j < k)


# --------------------------------------------------------- tiền chưa gắn

@ca("v611 tiền chưa gắn: chỉ khoản vào tài khoản chính, chưa ai giữ, chưa thuộc đơn Pancake có bill; lớn trước")
def _tien():
	gds = [
		{"ten": "BT-1", "tien": 1875000, "ngay": "2026-10-23", "mo_ta": "Nam transfers money quickly", "tk_cty": True},
		{"ten": "BT-2", "tien": 245000, "ngay": "2026-10-23", "mo_ta": "QALEAF2999 TCV", "tk_cty": False},
		{"ten": "BT-3", "tien": 500000, "ngay": "2026-10-22", "mo_ta": "CONG TY ABC", "tk_cty": True},
		{"ten": "BT-4", "tien": 900000, "ngay": "2026-10-22", "mo_ta": "S1234O95914T chuyen khoan", "tk_cty": True},
		{"ten": "BT-5", "tien": 3000000, "ngay": "2026-10-21", "mo_ta": "KHACH SI", "tk_cty": True},
	]
	ds = tbh.loc_tien_chua_gan(gds, {"BT-3": "phiếu công nợ CN-1"}, {"95914"})
	la("còn BT-5 rồi BT-1", [g["ten"] for g in ds], ["BT-5", "BT-1"])
	d = tbh.dong_tien_chua_gan(ds)
	la("dòng ngày, tiền, nội dung", d[1], "23/10: 1.875.000 đ, Nam transfers money quickly")
	la("cắt ở tối đa", tbh.dong_tien_chua_gan(ds * 6, toi_da=10)[-1], "+2 khoản khác")


# ------------------------------------------------ YCSX, YCDC, nhận thiếu tồn

ITEMS = [D(item_code="BTPN00001", item_name="BTP Sauce Cherry", qty=2, uom="Kg", stock_uom="Kg")]


@ca("v611 YCSX: tin bếp có phiếu, bộ phận, ngày cần, món; cần trong ngày thì GẤP; loại khác im")
def _ycsx():
	gia, goi = _zalo()
	mr = D(name="MAT-MR-1", material_request_type="Manufacture", custom_bep_nhan="Bếp Baker",
		bo_phan_yeu_cau="Bar TCV", nguoi_yeu_cau="Tài", schedule_date="2026-08-15",
		set_warehouse="Kho TCV - TV", items=ITEMS)
	with um.patch.object(tk, "kenh_zalo", gia):
		tk.khi_co_yeu_cau_sx(mr)
		tk.khi_co_yeu_cau_sx(D(mr, material_request_type="Material Transfer"))
		tk.khi_co_yeu_cau_chuyen(mr)
	la("một tin bếp", [(g.ma_tin, g.loai, g.khoa) for g in goi], [("bep_ycsx_moi", "viec", "ycsx:MAT-MR-1")])
	dung("GẤP vì cần hôm nay", goi[0].tieu_de.startswith("GẤP: "))
	dung("có ai gửi, ngày cần, kho giao", "Bar TCV, Tài, cần ngày 15/08" in goi[0].dong[0] and "Kho TCV" in goi[0].dong[0])
	dung("có món", "BTP Sauce Cherry: 2 Kg" in goi[0].dong)
	t, _ = tk.soan_ycsx(D(mr, schedule_date="2026-08-20"), [], "2026-08-15")
	dung("chưa tới ngày thì không GẤP", not t.startswith("GẤP"))


@ca("v611 YCSX ngày mai: cộng món cùng mã theo bếp, đếm phiếu, bếp trống gom riêng")
def _ycsx_mai():
	g = tk.gom_ycsx_theo_bep([
		{"bep": "Bếp Baker", "ma": "A", "ten": "Croissant", "sl": 20, "dvt": "Cái", "phieu": "MR-1"},
		{"bep": "Bếp Baker", "ma": "A", "ten": "Croissant", "sl": 10, "dvt": "Cái", "phieu": "MR-2"},
		{"bep": "Bếp Baker", "ma": "B", "ten": "Tart", "sl": 5, "dvt": "Cái", "phieu": "MR-2"},
		{"bep": "", "ma": "C", "ten": "Cookie", "sl": 3, "dvt": "Hộp", "phieu": "MR-3"},
	])
	la("hai bếp", sorted(g), ["Bếp Baker", "Chưa chọn bếp"])
	la("cộng cùng món, lớn trước", [(x["ten"], x["sl"], x["so_phieu"]) for x in g["Bếp Baker"]],
		[("Croissant", 30.0, 2), ("Tart", 5.0, 1)])


@ca("v611 YCDC: tin yêu cầu mới đúng mã; nhắc treo chỉ phiếu từ 2 ngày, chưa xong, cũ trước")
def _ycdc():
	gia, goi = _zalo()
	mr = D(name="YCDC-2026-00059", material_request_type="Material Transfer", set_from_warehouse="Kho tổng 307 - TV",
		set_warehouse="Kho TCV - TV", nguoi_yeu_cau="Tài", schedule_date="2026-08-16", items=ITEMS)
	with um.patch.object(tk, "kenh_zalo", gia):
		tk.khi_co_yeu_cau_chuyen(mr)
		tk.khi_co_yeu_cau_sx(mr)
	la("một tin kho", [(g.ma_tin, g.khoa) for g in goi], [("kho_ycdc_moi", "ycdc:YCDC-2026-00059")])
	dung("kho đi, kho đến gọn", "Kho tổng 307 sang Kho TCV" in goi[0].dong[0])
	rows = [
		{"name": "Y1", "status": "Pending", "transaction_date": "2026-08-13", "so_mon": 2},
		{"name": "Y2", "status": "Partially Ordered", "transaction_date": "2026-08-10", "so_mon": 1},
		{"name": "Y3", "status": "Pending", "transaction_date": "2026-08-14", "so_mon": 1},
		{"name": "Y4", "status": "Transferred", "transaction_date": "2026-08-01", "so_mon": 1},
		{"name": "Y5", "status": "Stopped", "transaction_date": "2026-08-01", "so_mon": 1},
	]
	ds = tk.gom_ycdc_treo(rows, "2026-08-15")
	la("Y2 (5 ngày) rồi Y1 (2 ngày)", [(r["name"], r["tre"]) for r in ds], [("Y2", 5), ("Y1", 2)])
	dung("dòng nêu số ngày và số món", "(5 ngày), 1 món" in tk.dong_ycdc_treo(ds)[0])


@ca("v611 nhận thiếu tồn: ca Tài (kho xuất 0) và ca có hàng chưa có giá nhập đều ra; đủ hàng thì im")
def _thieu_ton():
	items = [{"ma": "BTPN00001", "ten": "BTP Sauce Cherry", "can": 2, "dvt": "Kg", "kho": "Kho tổng 307 - TV"},
		{"ma": "BTPN00014", "ten": "BTP Mứt dâu", "can": 1, "dvt": "Kg", "kho": "Kho tổng 307 - TV"},
		{"ma": "SUA", "ten": "Sữa tươi", "can": 3, "dvt": "Lít", "kho": "Kho tổng 307 - TV"}]
	ton = {("BTPN00014", "Kho tổng 307 - TV"): 5, ("SUA", "Kho tổng 307 - TV"): 10}
	gia = {("SUA", "Kho tổng 307 - TV"): 30000}
	t = tk.gom_thieu_ton(items, ton, gia)
	la("hai món", [(x["ten"], x["ghi"]) for x in t], [("BTP Sauce Cherry", "kho đang có 0"),
		("BTP Mứt dâu", "có hàng nhưng máy chưa có giá nhập, báo kế toán")])
	la("đủ hàng có giá thì im", tk.gom_thieu_ton(items[2:], ton, gia), [])
	c = tk.cau_thieu_ton("Kho tổng 307 - TV", t)
	dung("câu dễ hiểu nêu kho, món, việc cần làm", c.startswith("Kho tổng 307 chưa đủ hàng") and "BTP Sauce Cherry: 2 Kg" in c
		and "ghi nhận sản xuất hoặc nhập kho" in c and "Tỷ giá" not in c)
	gia_z, goi = _zalo()
	with um.patch.object(tk, "kenh_zalo", gia_z), um.patch.object(tk, "_ten_nguoi", lambda u: "Tài"), \
			um.patch.object(tk, "nowdate", lambda: "2026-10-25"):
		tk.bao_nhan_thieu_ton("YCDC-2026-00059", "Kho tổng 307 - TV", "Kho TCV - TV", t)
	la("tin cảnh báo Kho", [(g.ma_tin, g.loai, g.khoa) for g in goi],
		[("kho_nhan_thieu_ton", "canh_bao", "thieu-ton:YCDC-2026-00059:Kho tổng 307 - TV:2026-10-25")])
	dung("tin không nói tiền", not any(re.search(r"\d đ\b", x) for x in goi[0].dong))


class _LoiDinhGia(sys.modules["frappe"].ValidationError):
	"""Đứng thay NegativeStockError: lớp con của ValidationError như Frappe thật."""


def _throw_that(msg, exc=None, title=None, **k):
	"""Như frappe.throw thật: tôn trọng exc= (bản giả chung của nen.py bỏ qua nó)."""
	raise (exc or sys.modules["frappe"].ValidationError)(msg)


def _nhan(thieu, loi=None, loi_chen=None):
	"""Chạy THẬT lan_nhan.nhan_theo_phieu, ghi sổ hỏng như ca Tài."""
	from vagabond import lan_nhan as ln
	nhat = []
	doc = D(items=[], flags=D())
	doc.append = lambda k, v: doc["items"].append(D(v))
	def chen():
		nhat.append("insert")
		if loi_chen:
			raise loi_chen
	doc.insert = chen

	def submit():
		raise loi or _LoiDinhGia("Tỷ giá định giá cho Mặt hàng BTPN00001 là bắt buộc")
	doc.submit = submit
	fr = sys.modules["frappe"]
	db_gia = types.SimpleNamespace(savepoint=lambda d: nhat.append("savepoint:" + d),
		rollback=lambda save_point=None: nhat.append("rollback:%s" % save_point),
		commit=lambda: nhat.append("commit"), get_value=lambda *a, **k: "TV")
	bao = []
	ps = [um.patch.object(fr, "new_doc", lambda dt: doc, create=True), um.patch.object(fr, "db", db_gia),
		um.patch.object(ln, "_da_co", lambda *a, **k: None),
		# Codex #498 (4371298484): ghi lại LÚC NÀO đọc tồn. Đọc trước khi lùi
		# điểm lưu là đọc Bin của giao dịch dở (bench CI: kho 30 ra "đang có 0").
		um.patch.object(tk, "kiem_thieu_ton", lambda d: nhat.append("doc_ton") or thieu),
		um.patch.object(fr, "throw", _throw_that),
		um.patch.object(tk, "bao_nhan_thieu_ton", lambda *a: bao.append(a))]
	for p in ps:
		p.start()
	try:
		ln.nhan_theo_phieu(ma_lan_nhan="a" * 32, phieu="YCDC-2026-00059", kho_xuat="Kho tổng 307 - TV",
			kho_nhan="Kho TCV - TV", dong='[{"item_code": "BTPN00001", "qty": 2}]', cong_ty="TV")
		return nhat, bao, None
	except Exception as e:
		return nhat, bao, e
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v611 nhận thiếu tồn: lùi về điểm lưu, báo Zalo, commit tin, rồi nói câu dễ hiểu; lỗi khác giữ nguyên")
def _nhan_thieu():
	t = [{"ten": "BTP Sauce Cherry", "sl": 2, "dvt": "Kg", "ghi": "kho đang có 0"}]
	nhat, bao, e = _nhan(t)
	la("thứ tự: chèn, lùi điểm lưu, RỒI mới đọc tồn, commit", [x for x in nhat if x != "savepoint:vgb_lan_nhan_chen"],
		["insert", "rollback:vgb_lan_nhan_chen", "doc_ton", "commit"])
	la("báo đúng phiếu và kho", [a[:3] for a in bao], [("YCDC-2026-00059", "Kho tổng 307 - TV", "Kho TCV - TV")])
	dung("người bấm thấy câu dễ hiểu, không thấy câu dịch máy", e is not None and "chưa đủ hàng" in str(e) and "Tỷ giá" not in str(e))
	dung("giữ đúng lớp lỗi gốc để màn Nhận hàng xử lý như cũ", type(e) is _LoiDinhGia)
	nhat, bao, e = _nhan([])
	dung("kho đủ hàng thì lỗi gốc đi nguyên", isinstance(e, _LoiDinhGia))
	la("không báo, không commit", (bao, "commit" in nhat), ([], False))
	# Codex #498 vòng 2, bench CI 58b0ccb (ca Tài dựng trên ERPNext thật): câu
	# "Valuation Rate ... is required" ném ngay ở INSERT, chưa tới submit.
	nhat, bao, e = _nhan(t, loi_chen=_LoiDinhGia("Valuation Rate for the Item X, is required to do accounting entries"))
	dung("lỗi ở insert cũng ra câu dễ hiểu", e is not None and "chưa đủ hàng" in str(e) and "Valuation" not in str(e))
	la("insert hỏng: lùi điểm lưu, đọc tồn, commit tin", [x for x in nhat if x != "savepoint:vgb_lan_nhan_chen"],
		["insert", "rollback:vgb_lan_nhan_chen", "doc_ton", "commit"])
	la("insert hỏng: báo Zalo", len(bao), 1)
	# Câu đã dễ hiểu của app (lo_hang) không bị thay, không lùi, không báo.
	cau_lo = 'Kho "Kho tổng 307" không đủ BTP để trừ: còn thiếu 70 Kg.'
	nhat, bao, e = _nhan(t, loi_chen=_LoiDinhGia(cau_lo))
	la("câu lo_hang đi nguyên", str(e), cau_lo)
	la("không đọc tồn, không báo, không commit", ("doc_ton" in nhat, bao, "commit" in nhat), (False, [], False))
	la("lỗi lõi nhận diện đúng", [tk.la_loi_ton_loi(x) for x in (_LoiDinhGia("Tỷ giá định giá cho Mặt hàng X là bắt buộc"),
		type("NegativeStockError", (Exception,), {})("x"), _LoiDinhGia("20 units of X needed in Kho A on 25-10-2026 to complete this transaction."),
		_LoiDinhGia(cau_lo), RuntimeError("Deadlock found"))], [True, True, True, False, False])


# ------------------------------------------------------------- đặt bàn

HOM = dt.datetime(2026, 10, 25, 15, 0)
DB = D(name="DB-1", ten="Nguyễn Minh Anh", sdt="0909123456", co_so="TCV", ten_co_so="District 1", ngay="2026-10-25",
	gio="18:30", so_khach=4, tre_em=1, dip="Sinh nhật", khu_vuc="Bàn sofa thấp", email="minhanh@gmail.com",
	banh_kem_theo="1 Entremet Pistachio 16cm", trang_thai="Chờ xác nhận")


@ca("v611 đặt bàn thuần: khoảng ngày bốn chip, giờ hẹn, nhắc trong 3 giờ, quá giờ, số chờ")
def _thuan_dat_ban():
	h = dt.date(2026, 10, 25)
	la("bốn khoảng", [db.khoang_ngay(k, h) for k in db.KHOANG], [(h, h), (dt.date(2026, 10, 26),) * 2,
		(h, dt.date(2026, 10, 31)), (dt.date(2026, 10, 11), dt.date(2026, 10, 24))])
	la("ngày ngắn", db.ngay_ngan("2026-10-25"), "CN 25/10")
	rows = [DB, D(DB, name="DB-2", gio="19:00"), D(DB, name="DB-3", gio="14:59"), D(DB, name="DB-4", trang_thai="Đã xác nhận", gio="16:00"),
		D(DB, name="DB-5", gio="16:00")]
	la("nhắc: chờ xác nhận, trong 3 giờ tới, chưa qua giờ", [r.name for r in db.can_nhac(rows, HOM)], ["DB-5"])
	la("đúng 3 giờ vẫn nhắc", [r.name for r in db.can_nhac([D(DB, gio="18:00")], HOM)], ["DB-1"])
	dung("quá giờ", db.qua_gio(D(DB, gio="15:00"), HOM) and not db.qua_gio(DB, HOM))
	la("số chờ bỏ phiếu quá giờ", db.dem_cho(rows, HOM), 3)
	la("câu email", [db.cau_thu(1, "a@b.com", "15:00 25/10"), db.cau_thu(0, "a@b.com", "x"), db.cau_thu(1, "", "x")],
		["đã gửi email cho khách lúc 15:00 25/10", "không gửi email (quản lý tắt)", "khách không để email, nhớ gọi báo khách"])


@ca("v611 đặt bàn tin Zalo: xác nhận có ngày giờ, cơ sở, tên, SĐT, số khách, khu vực, dịp, bánh, người xác nhận và email")
def _tin_dat_ban():
	t, d = db.soan_tin_xac_nhan(DB, "Lê Hoàng Dễ", "đã gửi email cho khách lúc 15:00 25/10")
	la("tiêu đề", t, "Đặt bàn đã xác nhận")
	chu = "\n".join(d)
	for x in ("CN 25/10 lúc 18:30", "District 1", "Nguyễn Minh Anh", "0909123456", "4 khách (1 trẻ em)", "Bàn sofa thấp",
			"Sinh nhật", "Entremet", "Xác nhận bởi Lê Hoàng Dễ", "đã gửi email"):
		dung("có %r" % x, x in chu)
	t, d = db.soan_tin_huy(DB, "Hết chỗ khung giờ này", "Lê Hoàng Dễ", "không gửi email (quản lý tắt)")
	la("huỷ có lý do và người huỷ", (t, d[2:]), ("Đặt bàn đã huỷ", ["Lý do: Hết chỗ khung giờ này",
		"Huỷ bởi Lê Hoàng Dễ · không gửi email (quản lý tắt)"]))


@ca("v611 thư khách: mẫu đã duyệt có tên, ngày giờ, chi nhánh, lời nhắn; huỷ có lý do và nút chọn giờ khác")
def _thu():
	d = D(DB, ten_co_so="The Vagabond District 1", dia_chi="9 Trần Cao Vân")
	h = dbt.thu_xac_nhan(d, "Tiệm chuẩn bị nến cho anh chị")
	for x in ("Bàn của anh chị đã được giữ", "Nguyễn Minh Anh", "Chủ Nhật, 25/10/2026", "18:30", "The Vagabond District 1",
			"Tiệm chuẩn bị nến cho anh chị", "Xem đường đến tiệm"):
		dung("thư xác nhận có %r" % x, x in h)
	h = dbt.thu_huy(d, "Hết chỗ khung giờ này")
	for x in ("Tiệm chưa giữ được bàn lần này", "Hết chỗ khung giờ này", "Chọn giờ khác", dbt.WEB_DAT_BAN):
		dung("thư huỷ có %r" % x, x in h)
	dung("tên khách được thoát HTML", "&lt;b&gt;" in dbt.thu_xac_nhan(D(d, ten="<b>x</b>")))
	la("tiêu đề", dbt.tieu_de_thu("xac_nhan", d), "Xác nhận đặt bàn 25/10 lúc 18:30 · The Vagabond Pâtisserie")


class _Phieu(D):
	pass


def _xu_ly(ham, vai=("VGB - Quản lý cửa hàng",), phieu=None, gio=HOM, loi_thu=None, **ts):
	"""Chạy THẬT một nút của màn đặt bàn trên phiếu giả. Trả (kết quả hoặc lỗi, phiếu, thư, zalo)."""
	p = _Phieu(phieu or DB)
	luu, thu = [], []
	p.save = lambda: luu.append(dict(p))
	p.db_set = lambda k, v, **kw: p.__setitem__(k, v)
	p.flags = D()
	gia, goi = _zalo()
	fr = sys.modules["frappe"]
	ps = [um.patch.object(fr, "get_roles", lambda *a: list(vai), create=True),
		um.patch.object(fr, "get_doc", lambda *a, **k: p, create=True),
		um.patch.object(fr, "sendmail", lambda **k: (_ for _ in ()).throw(loi_thu) if loi_thu else thu.append(k), create=True),
		um.patch.object(fr, "session", D(user="de@vagabond.vn"), create=True),
		um.patch.object(fr.utils, "get_fullname", lambda u: "Lê Hoàng Dễ", create=True),
		um.patch.object(fr.utils, "now_datetime", lambda: gio, create=True),
		um.patch.object(db, "_co_so", lambda d: ("District 1", "The Vagabond District 1", "9 Trần Cao Vân")),
		um.patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}),
		um.patch("vagabond.thu_khung.goc_anh", lambda: "", create=True),
		um.patch("vagabond.thu_khung._cac_quay", lambda: [], create=True)]
	import vagabond
	ps.append(um.patch.object(vagabond, "kenh_zalo", gia, create=True))
	for x in ps:
		x.start()
	try:
		kq = ham(name="DB-1", **ts)
	except Exception as e:
		kq = e
	finally:
		for x in reversed(ps):
			x.stop()
	return kq, p, luu, thu, goi


@ca("v611 nút Xác nhận: đổi trạng thái, ghi vết, gửi đúng một thư mẫu, báo Zalo bh_dat_ban_xac_nhan")
def _xac_nhan():
	kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, loi_nhan="Tiệm chuẩn bị nến", gui_email=1)
	la("trạng thái", (kq.get("trang_thai") if isinstance(kq, dict) else repr(kq), p.trang_thai), ("Đã xác nhận", "Đã xác nhận"))
	la("lưu một lần", len(luu), 1)
	dung("vết có người và lời nhắn", "Xác nhận bởi Lê Hoàng Dễ. Lời nhắn: Tiệm chuẩn bị nến" in p.xu_ly)
	la("người xử lý", p.xu_ly_boi, "Lê Hoàng Dễ")
	la("một thư tới khách", [t["recipients"] for t in thu], [["minhanh@gmail.com"]])
	dung("thư theo mẫu, gắn phiếu", "Bàn của anh chị đã được giữ" in thu[0]["message"] and thu[0]["reference_name"] == "DB-1")
	la("một tin Zalo", [(g.ma_tin, g.khoa) for g in goi], [("bh_dat_ban_xac_nhan", "dat-ban-xac_nhan:DB-1")])
	dung("tin nêu đã gửi email", "đã gửi email cho khách" in goi[0].dong[-1])


@ca("v611 nút Xác nhận: tắt email thì không thư; khách không email thì không thư và tin nhắc gọi")
def _xac_nhan_khong_thu():
	kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, gui_email=0)
	la("tắt email", (len(thu), p.thu_khach), (0, "không gửi email (quản lý tắt)"))
	kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, phieu=D(DB, email=""), gui_email=1)
	la("khách không email", (len(thu), p.thu_khach), (0, "khách không để email, nhớ gọi báo khách"))
	dung("tin Zalo nhắc gọi", "nhớ gọi báo khách" in goi[0].dong[-1])


@ca("v611 nút Xác nhận: quá giờ hẹn, sai trạng thái, sai quyền đều bị chặn ở máy chủ, không thư không tin")
def _xac_nhan_chan():
	for mo, kw in (("quá giờ", dict(gio=dt.datetime(2026, 10, 25, 18, 30))),
			("đã huỷ", dict(phieu=D(DB, trang_thai="Đã hủy"))),
			("thu ngân", dict(vai=("VGB - Nhân viên bán hàng",)))):
		kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, gui_email=1, **kw)
		dung("%s: bị chặn" % mo, isinstance(kq, Exception))
		la("%s: không lưu, không thư, không tin" % mo, (len(luu), len(thu), len(goi)), (0, 0, 0))
	kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, phieu=D(DB, trang_thai="Đã xác nhận"), gui_email=1)
	la("bấm lại khi đã xác nhận: báo đã có, không gửi lại", (kq.get("da_co"), len(thu), len(goi)), (1, 0, 0))


class QueryDeadlockError(Exception):
	"""Cùng tên lớp với frappe.QueryDeadlockError: loi_csdl nhận theo tên lớp."""


@ca("v611 nút Xác nhận: gửi thư gặp lỗi chết giao dịch thì lỗi đi lên, KHÔNG nhắn Zalo, KHÔNG báo xong (Codex #498 4371394665)")
def _xac_nhan_chet_giao_dich():
	kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, gui_email=1, loi_thu=QueryDeadlockError("Deadlock found when trying to get lock"))
	dung("lỗi đi lên cho người bấm: " + repr(kq), isinstance(kq, QueryDeadlockError))
	la("không nhắn Zalo đã xác nhận", len(goi), 0)
	dung("không ghi câu email dự phòng", p.thu_khach != "CHƯA gửi được email, gọi báo khách")
	kq, p, luu, thu, goi = _xu_ly(db.xac_nhan, gui_email=1, loi_thu=RuntimeError("SMTP 421"))
	la("lỗi thư thường: vẫn xác nhận, ghi câu dự phòng, vẫn nhắn Zalo", (kq.get("trang_thai") if isinstance(kq, dict) else repr(kq),
		p.thu_khach, len(goi)), ("Đã xác nhận", "CHƯA gửi được email, gọi báo khách", 1))


@ca("v611 nút Huỷ: bắt buộc lý do; có lý do thì thư huỷ kèm lý do và tin bh_dat_ban_huy")
def _huy():
	kq, p, luu, thu, goi = _xu_ly(db.huy, ly_do="  ", gui_email=1)
	dung("thiếu lý do bị chặn", isinstance(kq, Exception) and not luu and not thu and not goi)
	kq, p, luu, thu, goi = _xu_ly(db.huy, ly_do="Hết  chỗ khung giờ này", gui_email=1)
	la("trạng thái và lý do gọn khoảng trắng", (p.trang_thai, p.ly_do_huy), ("Đã hủy", "Hết chỗ khung giờ này"))
	dung("thư huỷ có lý do", len(thu) == 1 and "Hết chỗ khung giờ này" in thu[0]["message"])
	la("tin huỷ", [(g.ma_tin, g.dong[2]) for g in goi], [("bh_dat_ban_huy", "Lý do: Hết chỗ khung giờ này")])


@ca("v611 nút Khách đã đến: chỉ từ Đã xác nhận, không thư, không tin")
def _da_den():
	kq, p, luu, thu, goi = _xu_ly(db.da_den)
	dung("chờ xác nhận thì chưa ghi đến được", isinstance(kq, Exception) and not luu)
	kq, p, luu, thu, goi = _xu_ly(db.da_den, phieu=D(DB, trang_thai="Đã xác nhận"))
	la("ghi đến, im lặng", (p.trang_thai, len(thu), len(goi)), ("Đã đến", 0, 0))


@ca("v611 nhắc đặt bàn: đúng mã, mỗi phiếu một khoá, hỏi lại trước khi gửi, nêu thời gian còn lại")
def _nhac():
	gia, goi = _zalo()
	fr = sys.modules["frappe"]
	rows = [D(DB, gio="17:15"), D(DB, name="DB-9", gio="20:00")]
	with um.patch.object(fr, "get_all", lambda *a, **k: [D(r) for r in rows], create=True), \
			um.patch.object(fr.utils, "now_datetime", lambda: HOM, create=True), \
			um.patch.object(db, "_co_so", lambda d: ("District 1", "", "")), \
			um.patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}):
		import vagabond
		with um.patch.object(vagabond, "kenh_zalo", gia, create=True):
			db.nhac_sap_toi()
	la("một tin", [(g.ma_tin, g.khoa, g.kiem, g.nguon) for g in goi], [("bh_dat_ban_sap_toi", "dat-ban-gan:DB-1", "dat_ban_cho", "DB-1")])
	dung("nêu còn 2 giờ 15 phút", "Còn 2 giờ 15 phút" in goi[0].dong[-1])


@ca("v611 đặt bàn: vai được mở màn trùng tuyệt đối giữa app và máy chủ")
def _vai():
	js = io.open(os.path.join(GOI, "public", "js", "bep", "57-dat-ban.js"), encoding="utf-8").read()
	m = re.search(r"var QUYEN_DATBAN = \[([^\]]*)\]", js)
	dung("có danh sách", bool(m))
	la("trùng", sorted(re.findall(r"'([^']+)'", m.group(1))), sorted(db.QUYEN_DAT_BAN))


# ----------------------------------------------------------- bản vá tắt thư

@ca("v611 bản vá: tắt đúng năm Notification thư nội bộ đang bật, giữ chuông trong app")
def _vá_thu():
	ds = [D(name="Phiếu sản xuất - báo bếp", enabled=1, channel="Email"),
		D(name="Phiếu sản xuất - chuông trong app", enabled=1, channel="System Notification"),
		D(name="Chuyển hàng nội bộ - báo Thủ kho", enabled=1, channel="Email"),
		D(name="Đặt mua hàng mới - báo Purchasing", enabled=0, channel="Email"),
		D(name="Thư cho khách", enabled=1, channel="Email"),
		# Tên nằm trong danh sách mà kênh là chuông trong app thì giữ (đột biến M13).
		D(name="Notification for new fiscal year", enabled=1, channel="System Notification")]
	la("chỉ hai cái đang bật trong danh sách", p611.thong_bao_can_tat(ds), ["Phiếu sản xuất - báo bếp", "Chuyển hàng nội bộ - báo Thủ kho"])
	dung("không tắt chuông trong app", "Phiếu sản xuất - chuông trong app" not in p611.THONG_BAO_TAT)


@ca("v611 bản vá: tích thêm tin đặt bàn cho nhóm đã nhận đặt bàn, tin hoá đơn sai cho nhóm Sales; lũy đẳng")
def _vá_tin():
	cu = "bh_don_web_treo, bh_dat_ban, bh_tiec, ht_phat_hanh"
	moi = p611.tin_them("Sales Vagabond - Nhóm Bán hàng", cu)
	la("nối cuối, giữ thứ tự", moi, cu + ", bh_dat_ban_xac_nhan, bh_dat_ban_huy, bh_dat_ban_sap_toi, bh_thong_tin_hd_sai")
	la("chạy lại không đổi", p611.tin_them("Sales Vagabond - Nhóm Bán hàng", moi), None)
	la("nhóm đặt bàn riêng: chỉ tin đặt bàn", p611.tin_them("Đặt bàn D1", "bh_dat_ban"),
		"bh_dat_ban, bh_dat_ban_xac_nhan, bh_dat_ban_huy, bh_dat_ban_sap_toi")
	la("nhóm trống (nhận mọi tin) để nguyên", p611.tin_them("Sales", ""), None)
	la("nhóm kế toán không đụng", p611.tin_them("ERP Văn Phòng - Kế Toán", "hd_trung"), None)
	la("mọi mã có trong danh mục", sorted(set(p611.TIN_DAT_BAN + p611.TIN_SALES) - set(kz.TIN)), [])


@ca("v611 đăng ký: hook Material Request, bốn lịch, dòng bản vá; thư shipper đã gỡ")
def _dang_ky():
	h = io.open(os.path.join(GOI, "hooks.py"), encoding="utf-8").read()
	for x in ('"Material Request", "on_submit", "vagabond.tin_kho.khi_co_yeu_cau_sx"',
			'"Material Request", "on_submit", "vagabond.tin_kho.khi_co_yeu_cau_chuyen"',
			'"Material Request", "on_cancel", "vagabond.tin_kho.khi_huy_yeu_cau_sx"',
			'"*/15 * * * *", []).append("vagabond.dat_ban.nhac_sap_toi")',
			'"30 20 * * *", []).append("vagabond.tin_kho.nhac_ycsx_ngay_mai")',
			'"0 8 * * *", []).append("vagabond.tin_kho.nhac_ycdc_treo")',
			'"0 8 * * *", []).append("vagabond.tin_ban_hang.nhac_tien_chua_gan")'):
		dung("hooks có %s" % x[:60], x in h)
	p = io.open(os.path.join(GOI, "patches.txt"), encoding="utf-8").read().split()
	dung("patches.txt có bản vá tắt thư", "vagabond.patches.v611_tat_thu_noi_bo" in p)
	vd = io.open(os.path.join(GOI, "van_don.py"), encoding="utf-8").read()
	dung("gán shipper không còn gửi thư", "_mail_phan_cong" not in vd and "sendmail" not in vd[vd.find("def gan_shipper("):vd.find("def ds_diem_pickup")])
