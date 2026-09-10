"""#252 vòng 10/09/2026: LARAFARM HĐ 3019, 2900 và PNK-2026-00027; tham chiếu
phiếu thu chi.

Ba lỗi chị Dung và Uyên báo cùng ngày, ba nguyên nhân gốc:

  1. Màn so sánh cộng nguyên lượng ĐÃ NHẬN của phiếu, còn bước ghi sổ trừ
     phần hoá đơn khác đã lấy. Hai chỗ đọc hai con số: màn báo "Khớp 0 đ",
     ghi sổ bị chặn "chỉ còn 1000 đơn vị kho". Nay một nguồn lượng cho cả
     ba bước (so sánh, nối, ghi sổ), và dấu nối cũ mất hiệu lực thì tự gỡ.
  2. Nút "Gắn mã hàng" nằm trong nhánh "lệch đơn vị" nên dòng chưa có mã mà
     không lệch đơn vị thì không có nút nào. Nay hiện độc lập, kèm gợi ý
     món trên phiếu cùng số lượng và giá.
  3. Bỏ bắt buộc Số séc/tham chiếu đặt tay trên Desk, mất. Nay mã nguồn
     giữ, mỗi lần Migrate khai lại.

Chạy chính hàm xử lý với DB giả ở biên, như thu_mua_hddt_227.py.
"""

import os
from contextlib import ExitStack
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import doi_chieu_mua as dc, tham_chieu_tien as tc
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_mua_hddt_227 import To, _dong

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(duong):
	with open(os.path.join(GOC, duong), encoding="utf-8") as f:
		return f.read()


# Hai phieu dau LARAFARM: P0 nhan 5 Hop (2.500 g) + 2 Hop mam xoi, P1 nhan
# 1 Hop dau. Hop = 500 Gram.
def _phieu_dau():
	return {
		"P0": [
			dict(name="R0", item_code="DAU", item_name="Trái dâu tươi Đà Lạt", qty=5, rate=135000,
				amount=675000, uom="Hộp", stock_uom="Gram", conversion_factor=500, stock_qty=2500),
			dict(name="R1", item_code="MXD", item_name="Blackberry", qty=2, rate=160000,
				amount=320000, uom="Hộp", stock_uom="Gram", conversion_factor=500, stock_qty=1000),
		],
		"P1": [
			dict(name="R2", item_code="DAU", item_name="Trái dâu tươi Đà Lạt", qty=1, rate=135000,
				amount=135000, uom="Hộp", stock_uom="Gram", conversion_factor=500, stock_qty=500),
		],
	}


def _dong_dau(sl, ten="ROW", **them):
	return _dong(sl, 135000, name=ten, item_code="DAU", item_name="Trái dâu tươi Đà Lạt",
		uom="Hộp", stock_uom="Gram", conversion_factor=500, **them)


def _gia_lap(phieu, da_dung=None, dong_hd=None, giu_gia=0, vuot=True):
	"""`da_dung`: dòng hoá đơn ĐÃ GHI SỔ của tờ khác đang chiếm phiếu."""
	bo = ExitStack()
	bo.enter_context(patch.object(dc, "_dong_pnk", lambda p: deepcopy(phieu[p])))
	bo.enter_context(patch.object(dc, "_vuot_lech_gia_duoc", lambda: vuot))
	bo.enter_context(patch.object(dc, "_ghi_chu_lech_gia", lambda *a: None))
	bo.enter_context(patch.object(dc, "_khong_qua_kho", lambda *a: False))
	bo.enter_context(patch.object(dc, "_kiem_quyen", lambda: None))
	if dong_hd is not None:
		bo.enter_context(patch.object(dc, "_dong_hd", lambda n: deepcopy(dong_hd)))

	def get_value(dt, n, o=None, as_dict=False, **k):
		if dt == "Purchase Receipt":
			return "NCC"
		if dt == "Purchase Invoice":
			return {"name": n, "supplier": "NCC", "total": 1130000, "docstatus": 0}
		return None

	def throw(msg, *a, **k):
		raise ValueError(msg)

	bo.enter_context(patch.object(dc, "frappe", SimpleNamespace(
		get_all=lambda *a, **k: da_dung or [],
		parse_json=lambda s: __import__("json").loads(s),
		throw=throw,
		db=SimpleNamespace(get_single_value=lambda *a: giu_gia, get_value=get_value))))
	return bo


def _da_lay(pr_detail, sl, hd="HDM-KHAC"):
	return To(parent=hd, pr_detail=pr_detail, qty=sl, uom="Hộp", conversion_factor=500)


@ca("#252: màn so sánh đọc lượng CÒN LẠI của phiếu, không phải lượng đã nhận")
def _con_lai():
	# HĐ 3019: 1 Hop + 5 Hop dau, 2 Hop mam xoi. Mot to khac da ghi so lay
	# 3 Hop dau cua P0.
	dong = [
		dict(name="A", idx=1, item_code="DAU", item_name="Trái dâu tươi Đà Lạt", qty=1, rate=135000,
			amount=135000, uom="Hộp", stock_uom="Gram", conversion_factor=500, description="", purchase_receipt="", pr_detail=""),
		dict(name="B", idx=2, item_code="MXD", item_name="Blackberry", qty=2, rate=160000,
			amount=320000, uom="Hộp", stock_uom="Gram", conversion_factor=500, description="", purchase_receipt="", pr_detail=""),
		dict(name="C", idx=3, item_code="DAU", item_name="Trái dâu tươi Đà Lạt", qty=5, rate=135000,
			amount=675000, uom="Hộp", stock_uom="Gram", conversion_factor=500, description="", purchase_receipt="", pr_detail=""),
	]
	with _gia_lap(_phieu_dau(), [_da_lay("R0", 3, "HDM-26-08-00050")], dong):
		s = dc.so_sanh("PI", ["P0", "P1"])
	d = {r["idx"]: r for r in s["dong"]}
	la("dâu còn 3 Hộp cho tờ này (2 của P0 + 1 của P1)", d[1]["sl_pnk"], 3.0)
	la("vẫn nói đã nhận 6", d[1]["sl_pnk_nhan"], 6.0)
	la("nêu tên hoá đơn đã lấy", d[1]["da_dung_hd"], ["HDM-26-08-00050"])
	la("lệch tính theo món: 6 Hộp trên hoá đơn so với 3 Hộp còn", d[3]["lech_sl"], 1500.0)
	la("hai dòng cùng món cùng một số lệch", d[1]["lech_sl"], d[3]["lech_sl"])
	la("mâm xôi chưa ai lấy nên còn nguyên", d[2]["sl_pnk"], 2.0)
	# Tien phieu con lai: 3 Hop dau 405.000 + 2 Hop mam xoi 320.000.
	la("tiền phiếu nhập còn lại", s["tien_pnk"], 725000.0)
	la("không còn báo khớp giả", s["khop"], 0)
	la("tên hoá đơn đã lấy ở tổng", s["hd_da_dung"], ["HDM-26-08-00050"])


@ca("#252: dấu nối cũ mất hiệu lực thì màn báo rõ và không khớp")
def _noi_cu_man():
	dong = [
		dict(name="C", idx=1, item_code="DAU", item_name="Trái dâu tươi Đà Lạt", qty=5, rate=135000,
			amount=675000, uom="Hộp", stock_uom="Gram", conversion_factor=500, description="",
			purchase_receipt="P0", pr_detail="R0"),
	]
	with _gia_lap(_phieu_dau(), [_da_lay("R0", 3, "HDM-26-08-00050")], dong):
		s = dc.so_sanh("PI", ["P0"])
	la("dòng bị đánh dấu nối cũ", s["dong"][0]["noi_cu"], 1)
	la("đếm ở tổng", s["so_noi_cu"], 1)
	la("không khớp", s["khop"], 0)
	# Chua ai lay thi dau noi van hieu luc.
	with _gia_lap(_phieu_dau(), [], dong):
		s = dc.so_sanh("PI", ["P0"])
	la("chưa ai lấy thì không phải nối cũ", s["dong"][0]["noi_cu"], 0)


@ca("#252: nối lại tự gỡ dấu cũ và chia theo lượng còn thật, nêu tên hoá đơn đã lấy")
def _go_va_chia():
	# P0 con 2 Hop (1.000 g) sau khi to khac lay 3; P1 co 1 Hop. Dong 5 Hop
	# dang noi cu vao R0.
	t = To(name="PI", items=[_dong_dau(5, purchase_receipt="P0", pr_detail="R0")])
	with _gia_lap(_phieu_dau(), [_da_lay("R0", 3, "HDM-26-08-00050")]):
		ra = dc._noi(t, ["P0", "P1"], True)
	la("gỡ đúng một dấu nối cũ", len(ra["da_go_noi_cu"]), 1)
	dung("câu gỡ nêu tên hoá đơn đã lấy", "HDM-26-08-00050" in ra["da_go_noi_cu"][0])
	la("không nối vượt: 5 Hộp mà chỉ còn 3", ra["da_noi"], 0)
	dung("dòng không còn giữ dấu cũ", not t.items[0].get("pr_detail"))
	dung("câu báo nêu đã nhận và ai lấy", "đã nhận 3000" in ra["loi"][0] and "HDM-26-08-00050" in ra["loi"][0])
	# Du luong thi chia: 2 Hop tu R0 + 3 Hop tu mot phieu khac.
	phieu = _phieu_dau()
	phieu["P1"][0].update(qty=3, amount=405000, stock_qty=1500)
	t = To(name="PI", items=[_dong_dau(5, purchase_receipt="P0", pr_detail="R0")])
	with _gia_lap(phieu, [_da_lay("R0", 3, "HDM-26-08-00050")]):
		ra = dc._noi(t, ["P0", "P1"], True)
	la("gỡ rồi chia đủ", ra["da_noi"], 2)
	la("đúng hai dòng phiếu", {d.pr_detail for d in t.items}, {"R0", "R2"})
	la("đủ 5 Hộp", sum(d.qty for d in t.items), 5)
	la("giữ tiền hoá đơn", sum(d.qty * d.rate for d in t.items), 675000)
	la("bấm lại không đổi gì", dc._noi(t, ["P0", "P1"], True)["da_noi"], 0)


@ca("#252: dấu nối còn hiệu lực thì KHÔNG bị gỡ")
def _khong_go_oan():
	t = To(name="PI", items=[_dong_dau(2, purchase_receipt="P0", pr_detail="R0")])
	with _gia_lap(_phieu_dau(), [_da_lay("R0", 3, "HDM-26-08-00050")]):
		ra = dc._noi(t, ["P0"], True)
	la("không gỡ", ra["da_go_noi_cu"], [])
	la("giữ dấu nối", t.items[0].pr_detail, "R0")


@ca("#252: danh sách đánh dấu tờ nháp giữ dấu nối đã mất hiệu lực")
def _danh_sach_noi_cu():
	dong_theo_hd = {
		"HD-A": [To(item_code="DAU", purchase_receipt="P0", pr_detail="R0", qty=5, uom="Hộp", conversion_factor=500)],
		"HD-B": [To(item_code="DAU", purchase_receipt="P0", pr_detail="R0", qty=2, uom="Hộp", conversion_factor=500)],
		"HD-C": [To(item_code="MXD", purchase_receipt="", pr_detail="", qty=1, uom="Hộp", conversion_factor=500)],
	}

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Purchase Receipt Item":
			return [dict(name="R0", item_code="DAU", qty=5, uom="Hộp", conversion_factor=500, stock_uom="Gram")]
		return [_da_lay("R0", 3, "HDM-26-08-00050")]

	with patch.object(dc, "frappe", SimpleNamespace(get_all=get_all)), \
		patch.object(dc, "dong_hieu_luc", lambda rows, **kw: [dict(r) for r in rows]):
		la("chỉ tờ đòi 5 Hộp bị đánh dấu", dc.hd_noi_cu(dong_theo_hd), {"HD-A"})
	with patch.object(dc, "frappe", SimpleNamespace(get_all=get_all)):
		la("không có dấu nối thì không truy vấn", dc.hd_noi_cu({"HD-C": dong_theo_hd["HD-C"]}), set())


@ca("#252: câu chặn ghi sổ nêu tên hoá đơn đã lấy và chỉ đường ra")
def _cau_chan():
	c = dc.cau_chan_vuot_luong("PNK-2026-00043", 2500, 1500, 2500, ["HDM-26-08-00050"])
	dung("nêu phiếu", "PNK-2026-00043" in c)
	dung("nêu đã nhận 2500", "đã nhận 2500" in c)
	dung("nêu ai lấy", "HDM-26-08-00050 đã ghi sổ lấy 1500" in c)
	dung("nêu còn 1000", "chỉ còn 1000" in c)
	dung("chỉ đường: nối lại", "Nối phiếu" in c)
	dung("không có hoá đơn tên thì vẫn có câu", "khác" in dc.cau_chan_vuot_luong("P", 1, 1, 1, []))


@ca("#252: dòng không có trong phiếu được gợi ý món cùng số lượng, cùng giá")
def _goi_y_phieu():
	# Hoa don ghi "Dau Nhat size 49" chua co ma, phieu co "Trai dau tuoi Da
	# Lat" 5 Hop x 135.000 khong ai nhac toi.
	dong = [
		dict(name="A", idx=1, item_code="", item_name="Dâu Nhật size 49 hộp 500g", qty=5, rate=135000,
			amount=675000, uom="Hộp", stock_uom="", conversion_factor=1, description="", purchase_receipt="", pr_detail=""),
		dict(name="B", idx=2, item_code="MXD", item_name="Blackberry", qty=2, rate=160000,
			amount=320000, uom="Hộp", stock_uom="Gram", conversion_factor=500, description="", purchase_receipt="", pr_detail=""),
	]
	with _gia_lap(_phieu_dau(), [], dong):
		s = dc.so_sanh("PI", ["P0"])
	r = s["dong"][0]
	la("không có trong phiếu", r["co_phieu"], 0)
	la("gợi ý đúng món dâu", [g["item_code"] for g in r["goi_y_phieu"]], ["DAU"])
	la("dòng có phiếu thì không gợi ý", s["dong"][1].get("goi_y_phieu"), None)
	# Phieu bi lay het thi khong con la "thua".
	with _gia_lap(_phieu_dau(), [_da_lay("R0", 5, "HDM-X")], dong):
		s = dc.so_sanh("PI", ["P0"])
	la("dòng phiếu đã bị lấy hết không còn thừa, không gợi ý", s["dong"][0]["goi_y_phieu"], [])
	la("thừa rỗng", [t["item_code"] for t in s["thua"]], [])


@ca("#252: đổi mã hàng trên dòng đã có mã: chỉ khi chưa nối, có ghi vết")
def _doi_ma():
	ma = _doc("vagabond/doi_chieu_mua.py")
	dung("có tham số đổi", "def gan_ma_hang(name, dong, item_code, nho=1, doi=0):" in ma)
	dung("không đổi dòng đã nối", "Bỏ nối trước khi đổi mã hàng" in ma)
	dung("ghi vết vào tờ", "Đổi mã hàng dòng %d từ %s sang %s" in ma)
	dung("đổi ghi nhớ theo", "(ma_cu and cint(doi))" in ma)


@ca("#252: bo_noi chỉ xoá dấu nối trên tờ nháp, không đụng tiền")
def _bo_noi():
	ma = _doc("vagabond/doi_chieu_mua.py")
	i = ma.index("def bo_noi(")
	j = ma.index("@frappe.whitelist()", i)
	than = ma[i:j]
	dung("chặn tờ đã ghi sổ", "docstatus != 0" in than)
	dung("xoá đúng hai ô", "d.purchase_receipt = None" in than and "d.pr_detail = None" in than)
	dung("không sửa số lượng", "d.qty =" not in than)
	dung("không sửa đơn giá", "d.rate =" not in than)
	dung("có mở ra màn hình", "'vagabond.doi_chieu_mua.bo_noi'" in _doc("vagabond/public/js/bep/18-doi-chieu-may-in.js"))


@ca("#252: nút Gắn mã hàng hiện độc lập với nhánh lệch đơn vị")
def _nut_gan_ma():
	js = _doc("vagabond/public/js/bep/18-doi-chieu-may-in.js")
	dung("khối chưa gắn mã đứng riêng", "if (!r.item_code) {" in js)
	dung("nút gắn đứng riêng", "if (!r.item_code && kq.lam_duoc && !r.da_noi) {" in js)
	# Nut phai nam TRUOC khoi "if (lechDvt)", tuc khong con lồng trong đó.
	dung("nút đứng trước nhánh lệch đơn vị",
		js.index("Gắn mã hàng cho dòng này") < js.index("if (lechDvt) {"))
	dung("có gợi ý từ phiếu", "data-dcmgoiy" in js)
	dung("hiện lượng còn lại", "Phiếu nhập còn " in js)
	dung("chip nối cũ", "noi_cu" in js)


@ca("#252: tham chiếu phiếu thu chi: điền khi trống, giữ khi có, chỉ vế ngân hàng")
def _tham_chieu():
	la("số mặc định theo ngày hạch toán", tc.so_tham_chieu_mac_dinh("2026-09-10"), "CK-20260910")
	la("ngân hàng, trống cả hai", tc.can_dien("11211 - MB", "331 - NCC", "", None), ["reference_no", "reference_date"])
	la("ngân hàng, có số FT thì giữ", tc.can_dien("131", "11211 - MB", "FT26233503", "2026-09-10"), [])
	la("tiền mặt không đụng", tc.can_dien("1111 - Quỹ", "331", "", None), [])
	la("type Bank khai nhầm vẫn không bị core chặn", tc.can_dien(
		"1411 - Tạm ứng", "331", "", None, "Bank", "Payable"),
		["reference_no", "reference_date"])
	t = To(paid_from="11211 - MB", paid_to="331 - NCC", posting_date="2026-09-10", reference_no="", reference_date=None)
	tc.dien_khi_trong(t)
	la("điền số", t.reference_no, "CK-20260910")
	la("điền ngày bằng ngày hạch toán", str(t.reference_date), "2026-09-10")
	t = To(paid_from="11211 - MB", paid_to="331", posting_date="2026-09-10", reference_no="FT1", reference_date="2026-09-09")
	tc.dien_khi_trong(t)
	la("không đè số thật của ngân hàng", t.reference_no, "FT1")
	la("không đè ngày thật", t.reference_date, "2026-09-09")


@ca("#252: bỏ bắt buộc tham chiếu do mã nguồn giữ, chạy mỗi lần Migrate")
def _property_setter():
	goi = []

	def make(dt, o, thuoc_tinh, gia_tri, kieu, **k):
		goi.append((dt, o, thuoc_tinh, gia_tri))

	mod = SimpleNamespace(make_property_setter=make)
	import sys
	with patch.dict(sys.modules, {"frappe.custom.doctype.property_setter.property_setter": mod}), \
		patch.object(tc, "frappe", SimpleNamespace(clear_cache=lambda **k: None, log_error=lambda *a: None)):
		kq = tc.dung()
	la("đặt cho cả hai ô", kq["da_dat"], ["reference_no", "reference_date"])
	dung("xoá cả mandatory_depends_on, không chỉ reqd",
		("Payment Entry", "reference_no", "mandatory_depends_on", "") in goi
		and ("Payment Entry", "reference_no", "reqd", 0) in goi
		and ("Payment Entry", "reference_date", "mandatory_depends_on", "") in goi)
	dung("gọi từ patch migrate", "tham_chieu_tien.dung()" in _doc("vagabond/patches/dong_bo_cau_truc.py"))
	h = _doc("vagabond/hooks.py")
	dung("hook validate đã gắn", '"vagabond.tham_chieu_tien.dien_khi_trong"' in h)
	dung("gắn đúng doctype", h.index('"Payment Entry": {') < h.index('"vagabond.tham_chieu_tien.dien_khi_trong"'))
	dung("Desk có hook riêng chạy trước kiểm bắt buộc của trình duyệt",
		'"Payment Entry": "public/js/payment_entry.js"' in h)


# ---------------------------------------------------------- chay that man hinh

def _ve_man(xem, so_sanh):
	"""Chạy thật 18-doi-chieu-may-in.js trong node với API giả, trả HTML đã vẽ."""
	import json
	import subprocess

	js = os.path.join(GOC, "vagabond", "khung", "kiem_thu", "gia_lap_dcm.js")
	r = subprocess.run(["node", js, json.dumps(xem), json.dumps(so_sanh)],
		capture_output=True, text=True, timeout=60)
	if r.returncode != 0:
		raise AssertionError("giả lập màn lỗi: " + (r.stderr or "").strip()[:600])
	return json.loads(r.stdout)


def _xem_mau(**doi):
	x = {
		"hd": {"name": "HDM-1", "supplier_name": "LARAFARM", "posting_date": "2026-08-07",
			"grand_total": 1035000, "docstatus": 0, "update_stock": 0, "bill_no": "3019"},
		"hddt": None, "dong": [], "da_noi": 0, "phieu_da_noi": [], "nhom": "cho_doi_chieu", "noi_cu": 0,
		"goi_y": [{"name": "PNK-27", "ngay": "2026-08-07", "tien": 1035000, "tong": 1035000,
			"da_hoa_don": 0, "so_mon": 3, "so_mon_trung": 1, "dong": []}],
		"lam_duoc": 1, "ghi_so_duoc": 0, "nguong_lech": 1000,
	}
	x.update(doi)
	return x


def _dong_man(**doi):
	d = {"idx": 1, "item_code": "", "item_name": "Dâu Nhật size 49 hộp 500g", "sl_hd": 5, "gia_hd": 135000,
		"tien_hd": 675000, "sl_pnk": 0, "sl_pnk_nhan": 0, "da_dung_hd": [], "noi_cu": 0, "gia_pnk": 0,
		"dvt_hd": "Hộp", "dvt_pnk": "", "dvt_kho": "", "dvt_ncc": "", "ton_hd": 5, "ton_pnk": 0,
		"gia_kho_hd": 135000, "gia_kho_pnk": 0, "lech_dvt": 0, "khac_ten_dvt": 0, "co_phieu": 0,
		"hs_pnk": 0, "lech_sl": 5, "lech_gia": 0, "da_noi": "", "goi_y_phieu": []}
	d.update(doi)
	return d


def _so_sanh_mau(dong, **doi):
	s = {"dong": dong, "thua": [], "tien_hd": 1035000, "tien_pnk": 1035000, "lech_tien": 0, "khop": 0,
		"so_lech_dvt": 0, "so_khac_ten_dvt": 0, "so_noi_cu": 0, "hd_da_dung": [],
		"vuot_lech_gia_duoc": 1, "nguong_lech": 1000}
	s.update(doi)
	return s


@ca("#252: chạy thật màn: dòng chưa có mã, KHÔNG lệch đơn vị, vẫn có nút Gắn mã hàng")
def _man_nut_gan():
	# Dung ca LARAFARM PNK-2026-00027: lech_dvt = 0 vi khong co dong phieu de so.
	ra = _ve_man(_xem_mau(), _so_sanh_mau([_dong_man(goi_y_phieu=[{"item_code": "DAU", "item_name": "Trái dâu tươi Đà Lạt"}])]))
	dung("có nút gắn mã", 'data-dcmgan="1"' in ra["so_sanh"])
	dung("có câu chưa gắn mã", "chưa gắn mã hàng" in ra["so_sanh"])
	dung("có nút chọn món trên phiếu", 'data-dcmgoiy="1"' in ra["so_sanh"] and "Chọn Trái dâu tươi Đà Lạt" in ra["so_sanh"])
	dung("dòng chưa có mã thì nút là chọn, không phải đổi", 'data-doi="0"' in ra["so_sanh"])
	# Dong da co ma nhung sai: nut doi.
	ra = _ve_man(_xem_mau(), _so_sanh_mau([_dong_man(item_code="KHAC", goi_y_phieu=[{"item_code": "DAU", "item_name": "Dâu"}])]))
	dung("có mã sai thì nút là đổi", 'data-doi="1"' in ra["so_sanh"] and "Đổi sang Dâu" in ra["so_sanh"])
	dung("có mã rồi thì không hiện nút gắn", "data-dcmgan" not in ra["so_sanh"])


@ca("#252: chạy thật màn: lượng còn lại, tên hoá đơn đã lấy, khối nối cũ và nút Bỏ nối")
def _man_noi_cu():
	d = _dong_man(item_code="DAU", item_name="Trái dâu tươi Đà Lạt", co_phieu=1, sl_pnk=3, sl_pnk_nhan=6,
		da_dung_hd=["HDM-26-08-00050"], dvt_pnk="Hộp", dvt_kho="Gram", gia_pnk=135000, noi_cu=1, da_noi="PNK-43",
		lech_sl=1500, ton_pnk=1500, ton_hd=3000)
	ra = _ve_man(_xem_mau(nhom="cho_doi_chieu", noi_cu=1, phieu_da_noi=["PNK-43"]),
		_so_sanh_mau([d], so_noi_cu=1, hd_da_dung=["HDM-26-08-00050"], tien_pnk=725000, lech_tien=405000))
	s = ra["so_sanh"]
	dung("hiện còn 3 Hộp", "Phiếu nhập còn 3 Hộp" in s)
	dung("hiện đã nhận 6", "đã nhận 6" in s)
	dung("hiện tên hoá đơn đã lấy", "HDM-26-08-00050 đã lấy" in s)
	dung("khối nối cũ", "Dấu nối cũ không còn dùng được" in s)
	dung("khối cảnh báo chung", "Phiếu nhập đã bị hoá đơn khác lấy mất lượng" in s)
	dung("nút bỏ nối", 'id="dcmBoNoi"' in s)
	dung("chip nối lại ở đầu tờ", "nối lại" in ra["khung"])
	dung("tiền phiếu ghi là còn lại", "Tiền hàng phiếu nhập còn lại" in s)
	dung("không báo khớp", "✅ Khớp" not in s)
	# Khong noi cu, khong ai lay: khong co khoi canh bao, khong co nut bo noi.
	d2 = _dong_man(item_code="DAU", co_phieu=1, sl_pnk=6, sl_pnk_nhan=6, dvt_pnk="Hộp", gia_pnk=135000, lech_sl=0)
	ra = _ve_man(_xem_mau(), _so_sanh_mau([d2], khop=1))
	dung("không có khối nối cũ khi không cần", "Dấu nối cũ" not in ra["so_sanh"] and "dcmBoNoi" not in ra["so_sanh"])
	dung("không hiện đã nhận khi bằng còn lại", "đã nhận" not in ra["so_sanh"])
