# -*- coding: utf-8 -*-
"""v618: hoá đơn An Phú C26MYY số 8345 đồng bộ ra một dòng 1 đồng không mã hàng.

Anh Việt báo 28/10/2026: chứng từ HDM-26-10-00298 có dòng thứ ba "Chênh lệch
làm tròn theo hoá đơn điện tử" 1 đồng vào tài khoản 632, không mã hàng, nên
tờ kẹt ở bước "Thiếu mã hàng".

SỐ LIỆU LẤY TỪ SITE THẬT (đọc, không sửa)
-----------------------------------------
Bản gốc `MInvoice Invoice` d59cf189-4e9a-4a5f-9c38-156e2120df36:

    tong_tien 387.001, tien_thue 0, tien_truoc_thue 0
    dòng 1 "BƯỞI VÀNG" Kg, sluong 7,7, dgia 45.065, thtien 347.001
    dòng 2 "Phí ship giao và nhận hàng" chuyến, 1 x 40.000

Chứng từ: dòng 1 qty 7,7, rate 45.065, amount 347.000; dòng 2 40.000;
dòng 3 không mã hàng 1 đồng, tài khoản 632. Tổng 387.001.

NGUYÊN NHÂN
-----------
7,7 x 45.065 = 347.000,5. Người bán làm tròn nửa đồng LÊN (347.001), ERPNext
làm tròn nửa đồng về số CHẴN (347.000). Phép nắn cả tờ thấy thiếu 1 đồng và
thêm dòng bù. Nay đơn giá dòng chịu theo thành tiền của hoá đơn.

Các ca dưới đây chạy hàm thật. Bản Frappe giả làm tròn nửa đồng về số chẵn
y như site (đã đối chiếu: 347.000,5 ra 347.000 ở cả hai).
"""

import inspect
import json
from unittest.mock import patch

from vagabond import dung_lai_hddt as dl
from vagabond import minvoice_chung_tu as mc
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_lech_mot_dong_502 import (
	TO_1144, _chay_dung_moi, _phieu_vnd, _so_le_that)

DONG_8345 = [
	{"idhdon": "d59cf189-4e9a-4a5f-9c38-156e2120df36", "dgia": 45065,
		"dvtinh": "Kg", "mhhdvu": "BV01", "sluong": 7.7, "stckhau": 0, "stt": 1,
		"tchat": 1, "ten": "BƯỞI VÀNG", "thtien": 347001},
	{"idhdon": "d59cf189-4e9a-4a5f-9c38-156e2120df36", "dgia": 40000,
		"dvtinh": "chuyến", "mhhdvu": "PSGVNH01", "sluong": 1, "stckhau": 0,
		"stt": 2, "tchat": 1, "ten": "Phí ship giao và nhận hàng", "thtien": 40000},
]

TO_8345 = {
	"name": "d59cf189-4e9a-4a5f-9c38-156e2120df36",
	"so_hd": "8345",
	"ky_hieu": "C26MYY",
	"ngay_lap": "2026-10-20",
	"tong_tien": 387001,
	"tien_thue": 0,
	"tien_truoc_thue": 0,
	"mst_doi_tac": "075191002965",
	"nguoi_mua_ban": "HỘ KINH DOANH TRÁI CÂY NHẬP KHẨU AN PHÚ",
	"chi_tiet": json.dumps(DONG_8345, ensure_ascii=False),
}

GIA_NAN = 45065.064935065
TEN_BU = "Chênh lệch làm tròn theo hoá đơn điện tử"


def _dp():
	return _so_le_that(TO_8345)


def _tien(d):
	dp_gia, dp_tien, dp_sl = _dp()
	return mc.tien_dong_may_ghi(d.get("qty"), d.get("rate"), dp_gia, dp_tien, dp_sl)


# ------------------------------------------------------------- tái hiện


@ca("v618: tái hiện An Phú 8345, giá in trên hoá đơn máy ghi 347.000 thay vì 347.001")
def _tai_hien():
	dp_gia, dp_tien, dp_sl = _dp()
	la("số lẻ máy dùng cho tờ này", (dp_gia, dp_tien, dp_sl), (9, 0, 9))
	la("tích đúng là 347.000,5", 7.7 * 45065, 347000.5)
	la("máy làm tròn về số chẵn", mc.tien_dong_may_ghi(7.7, 45065, dp_gia, dp_tien, dp_sl), 347000.0)
	x = mc.dong_tu_hoa_don(DONG_8345[0], 1)
	la("đọc dòng giữ giá in", x["gia"], 45065)
	viec, so_tien = mc.can_theo_truoc_thue(
		mc.tien_dong_may_ghi(x["sl"], x["gia"], dp_gia, dp_tien, dp_sl) + 40000,
		mc.muc_tieu_truoc_thue(TO_8345))
	la("không nắn dòng thì cả tờ thiếu một đồng", (viec, so_tien), ("phi", 1.0))


# ------------------------------------------------------------ phép thuần


@ca("v618: đơn giá nắn theo thành tiền, máy ghi đúng 347.001")
def _nan_gia():
	dp_gia, dp_tien, dp_sl = _dp()
	gia = mc.gia_cho_dung_thanh_tien(7.7, 45065, 347001, dp_gia, dp_tien, dp_sl)
	la("đơn giá mới", gia, GIA_NAN)
	la("máy ghi đúng thành tiền", mc.tien_dong_may_ghi(7.7, gia, dp_gia, dp_tien, dp_sl), 347001.0)
	dung("đổi chưa tới nửa đồng một ký", abs(gia - 45065) <= mc.NAN_GIA_TOI_DA)
	x = mc.dong_may_ghi(DONG_8345[0], 1, dp_gia, dp_tien, dp_sl)
	la("dòng đọc ra đã nắn", x["gia"], GIA_NAN)
	la("dòng ship đúng số thì giữ nguyên", mc.dong_may_ghi(DONG_8345[1], 1, dp_gia, dp_tien, dp_sl)["gia"], 40000)


@ca("v618: không nắn khi lệch không phải làm tròn")
def _khong_nan_bua():
	dp = _dp()
	la("lệch 9 đồng giữ giá in", mc.gia_cho_dung_thanh_tien(7.7, 45065, 347010, *dp), 45065)
	# 100 x 1.000 mà hoá đơn ghi 100.010: đổi giá chỉ 0,1 đồng là khớp, nhưng
	# lệch 10 đồng thì không phải làm tròn, không được giấu vào đơn giá.
	la("lệch 10 đồng dù đổi giá ít vẫn giữ giá in", mc.gia_cho_dung_thanh_tien(100, 1000, 100010, *dp), 1000)
	# 7 x 14,28 = 99,96, hoá đơn 100: giá mới cắt hai số lẻ là 14,29 ra
	# 100,03, vẫn không đúng, nên giữ giá in cho phép nắn cả tờ lo.
	la("giá mới không ra đúng thành tiền thì giữ giá in", mc.gia_cho_dung_thanh_tien(7, 14.28, 100, 2, 2, 3), 14.28)
	# 0,5 x 1.001 = 500,5, máy ghi 500, hoá đơn 501: muốn khớp phải đổi đơn
	# giá 1 đồng một đơn vị, quá nửa đồng nên để phép nắn cả tờ lo.
	la("đổi quá nửa đồng một đơn vị giữ giá in", mc.gia_cho_dung_thanh_tien(0.5, 1001, 501, *dp), 1001)
	# Tờ không có quy ước riêng (đơn giá 2 số lẻ): 410.000 / 260 cắt còn
	# 1.576,92, vẫn ra 409.999, nên không đổi gì.
	la("số lẻ không chứa nổi thì giữ giá in", mc.gia_cho_dung_thanh_tien(260, 1576.92, 410000, 2, 0, 3), 1576.92)
	la("không có thành tiền thì giữ", mc.gia_cho_dung_thanh_tien(7.7, 45065, None, *dp), 45065)
	la("thành tiền không phải số thì giữ", mc.gia_cho_dung_thanh_tien(7.7, 45065, "abc", *dp), 45065)
	la("đơn giá trống thì giữ", mc.gia_cho_dung_thanh_tien(7.7, 0, 347001, *dp), 0)


@ca("v618: tờ âm nắn theo trị tuyệt đối, dấu nằm ở ô số lượng")
def _to_am():
	dp = _dp()
	it = dict(DONG_8345[0], sluong=-7.7, thtien=-347001)
	x = mc.dong_may_ghi(it, -1, *dp)
	la("số lượng âm", x["sl"], -7.7)
	la("đơn giá dương đã nắn", x["gia"], GIA_NAN)
	la("máy ghi đúng -347.001", mc.tien_dong_may_ghi(x["sl"], x["gia"], *dp), -347001.0)
	# Nguồn ghi thành tiền dương trên tờ âm: chiều dòng do `nan_dau_dong`
	# quyết (theo thành tiền), phép nắn chỉ chịu theo chiều đó, không lật dấu.
	x2 = mc.dong_may_ghi(dict(it, thtien=347001), -1, *dp)
	x2_goc = mc.dong_tu_hoa_don(dict(it, thtien=347001), -1)
	la("không đổi chiều dòng", x2["sl"], x2_goc["sl"])
	la("trị tuyệt đối đúng 347.001", abs(mc.tien_dong_may_ghi(x2["sl"], x2["gia"], *dp)), 347001.0)


# ------------------------------------------- đường dựng mới, chạy thật


@ca("v618: dung_hoa_don_mua trên tờ 8345 ra hai dòng, không còn dòng bù không mã")
def _dung_moi():
	t = _chay_dung_moi(dict(TO_8345))
	la("hai dòng như hoá đơn", len(t.items), 2)
	dung("không có dòng bù", all(d.item_name != TEN_BU for d in t.items))
	la("đơn giá bưởi đã nắn", t.items[0].rate, GIA_NAN)
	la("giá bảng ghim theo đơn giá dòng", t.items[0].price_list_rate, GIA_NAN)
	la("tiền bưởi đúng hoá đơn", t.items[0].amount, 347001.0)
	la("không đặt giảm giá", t.discount_amount, 0)
	la("tổng đúng 387.001", t.grand_total, 387001.0)


@ca("v618: dự kiến tổng khi dựng lại tờ 8345 ra đúng 387.001")
def _du_kien():
	la("tổng dự kiến", dl.du_kien_tong(_phieu_vnd(), TO_8345), 387001.0)


# ----------------------------------------------- đường dựng lại, chạy thật


class Dong(dict):
	def __getattr__(s, k):
		return s.get(k)

	def __setattr__(s, k, v):
		s[k] = v


class To:
	"""Phiếu nháp giả, chỉ đủ ô mà đường dựng lại đọc."""

	def __init__(s, items):
		s._items = items
		s.supplier = "HỘ KINH DOANH TRÁI CÂY NHẬP KHẨU AN PHÚ"
		s.apply_discount_on = ""
		s.discount_amount = 0
		s.additional_discount_percentage = 0
		s.is_return = 0

	def get(s, k, m=None):
		if k == "items":
			return s._items
		return getattr(s, k, m)

	def set(s, k, v):
		if k == "items":
			s._items = list(v)

	def append(s, k, v):
		if k == "items":
			s._items.append(Dong(v))


def _to_tren_site():
	"""Đúng ba dòng đang nằm trên HDM-26-10-00298 lúc 28/10/2026."""
	return To([
		Dong(item_code="NVLT00358", ten_hang_ncc="BƯỞI VÀNG", uom="Kg",
			conversion_factor=1000, qty=7.7, rate=45065, price_list_rate=45065,
			expense_account="3311 - Phải trả người bán, hàng về chưa có hoá đơn - TV",
			purchase_receipt="PNK-2026-00756", pr_detail="0mu0fgr6al"),
		Dong(item_code="DVTI00003", ten_hang_ncc="Phí ship giao và nhận hàng",
			uom="chuyến", conversion_factor=1, qty=1, rate=40000, price_list_rate=40000,
			expense_account="Chi phí thu mua chờ phân bổ vào giá trị hàng - TV"),
		Dong(item_code=None, ten_hang_ncc=TEN_BU, item_name=TEN_BU, uom="Nos",
			conversion_factor=1, qty=1, rate=1, price_list_rate=1,
			expense_account="632 - Giá vốn hàng bán - TV"),
	])


@ca("v618: dựng lại tờ 8345 đang có dòng bù thì bỏ dòng bù, giữ mã hàng, đúng 387.001")
def _dung_lai():
	doc = _to_tren_site()
	with patch.object(mc, "_tra_ma_hang", lambda x, mst, ncc: (None, None, 1)), \
			patch.object(mc, "don_vi_theo_ma", lambda ma, dvt, mst, ten: (
				("Kg", 1000) if ma == "NVLT00358" else ("chuyến", 1))), \
			patch.object(dl, "_do_chinh_xac", lambda doc=None, g=None: _dp()), \
			patch.object(dl, "_dung_thue_tai_cho", lambda doc, g: None), \
			patch.object(mc, "bo_mau_thue_mat_hang", lambda doc: None):
		dl._dung_dong_tai_cho(doc, dict(TO_8345))
	ds = doc.get("items")
	la("còn hai dòng", len(ds), 2)
	la("giữ mã bưởi người đã gắn", ds[0].get("item_code"), "NVLT00358")
	la("giữ mã ship", ds[1].get("item_code"), "DVTI00003")
	dung("không còn dòng không mã hàng", all(d.get("item_code") for d in ds))
	la("đơn giá bưởi đã nắn", ds[0].get("rate"), GIA_NAN)
	la("tiền hàng đúng 387.001", sum(_tien(d) for d in ds), 387001.0)
	la("không giảm giá", doc.discount_amount, 0)


@ca("v618: ghim lại theo bản gốc kéo về đơn giá ĐÃ NẮN, không kéo về 45.065")
def _ghim_lai():
	doc = _to_tren_site()
	doc._items = doc._items[:2]
	with patch.object(dl, "_do_chinh_xac", lambda doc=None, g=None: _dp()), \
			patch.object(mc, "don_vi_theo_ma", lambda ma, dvt, mst, ten: ("chuyến", 1)):
		da = dl.ghim_lai_theo_goc(doc, dict(TO_8345))
	la("kéo đúng một dòng", da, 1)
	la("đơn giá bưởi", doc.get("items")[0].rate, GIA_NAN)
	la("giá bảng theo đơn giá", doc.get("items")[0].price_list_rate, GIA_NAN)
	la("tiền hàng đúng 387.001", sum(_tien(d) for d in doc.get("items")), 387001.0)
	# Lượt lưu sau không đổi gì nữa: không lật qua lật lại giữa hai đơn giá.
	with patch.object(dl, "_do_chinh_xac", lambda doc=None, g=None: _dp()), \
			patch.object(mc, "don_vi_theo_ma", lambda ma, dvt, mst, ten: ("chuyến", 1)):
		la("lượt sau không kéo nữa", dl.ghim_lai_theo_goc(doc, dict(TO_8345)), 0)


@ca("v618: ALOIN 1144 cũng vào thẳng đơn giá, đường dựng lại không còn dòng bù")
def _aloin_dung_lai():
	doc = To([Dong(item_code=None, ten_hang_ncc="In ấn", uom="Cái", conversion_factor=1,
		qty=260, rate=1576.92, expense_account="642")])
	with patch.object(mc, "_tra_ma_hang", lambda x, mst, ncc: (None, None, 1)), \
			patch.object(dl, "_do_chinh_xac", lambda doc=None, g=None: _so_le_that(TO_1144)), \
			patch.object(dl, "_dung_thue_tai_cho", lambda doc, g: None), \
			patch.object(mc, "bo_mau_thue_mat_hang", lambda doc: None):
		dl._dung_dong_tai_cho(doc, dict(TO_1144))
	ds = doc.get("items")
	la("một dòng", len(ds), 1)
	la("đơn giá nắn", ds[0].get("rate"), 1576.923076923)
	dp_gia, dp_tien, dp_sl = _so_le_that(TO_1144)
	la("đúng 410.000", mc.tien_dong_may_ghi(ds[0].qty, ds[0].rate, dp_gia, dp_tien, dp_sl), 410000.0)


# ------------------------------------------------------------ một nguồn


@ca("v618: mọi đường tính tiền dòng đi qua dong_may_ghi, không đường nào lấy giá in")
def _mot_nguon():
	# Dò chuỗi chỉ để chốt một sự VẮNG MẶT; hành vi đã có các ca chạy thật ở trên.
	for ham in (mc.dung_hoa_don_mua, dl._dung_dong_tai_cho, dl.ghim_lai_theo_goc, dl.du_kien_tong):
		than = inspect.getsource(ham)
		dung("%s dùng dong_may_ghi" % ham.__name__, "dong_may_ghi(" in than)
		dung("%s không tự đọc dòng bằng dong_tu_hoa_don" % ham.__name__,
			"dong_tu_hoa_don(it" not in than)


# ------------------------------- Codex #512: một dòng chia qua nhiều phiếu nhập


def _to_noi():
	from vagabond.khung.kiem_thu.thu_mua_hddt_227 import To

	d = To(name="ROW", item_code="NVLT00358", item_name="Trái bưởi tươi, Kg",
		ten_hang_ncc="BƯỞI VÀNG", qty=7.7, rate=GIA_NAN, price_list_rate=GIA_NAN,
		amount=347001, uom="Kg", stock_uom="Gram", conversion_factor=1000, idx=1)
	return To(name="HDM-26-10-00298", doctype="Purchase Invoice", currency="VND",
		custom_minvoice_id=TO_8345["name"], items=[d])


def _hai_phieu():
	return {"P" + str(i): [dict(name="R" + str(i), item_code="NVLT00358", qty=3.85,
		rate=45065, uom="Kg", stock_uom="Gram", conversion_factor=1000)] for i in range(2)}


def _noi_hai_phieu(t):
	from vagabond import doi_chieu_mua as dc
	from vagabond.khung.kiem_thu.thu_mua_hddt_227 import _gia_lap

	with _gia_lap(_hai_phieu(), giu_gia=1), \
			patch.object(dl, "_goc", lambda ma: dict(TO_8345) if ma == TO_8345["name"] else None):
		return dc._noi(t, ["P0", "P1"], True)


@ca("v618 Codex #512: 7,7 kg chia hai phiếu 3,85 kg vẫn cộng đúng 347.001")
def _chia_hai_phieu():
	# Tái hiện đúng chuỗi Codex: trước bản sửa mỗi dòng con giữ 45.065,064935065
	# và máy ghi 173.501 mỗi dòng, cộng 347.002.
	la("trước bản sửa: một dòng con ra 173.501", mc.tien_dong_may_ghi(3.85, GIA_NAN, *_dp()), 173501.0)
	t = _to_noi()
	ra = _noi_hai_phieu(t)
	la("nối đủ hai dòng", ra["da_noi"], 2)
	la("không báo lỗi", ra["loi"], [])
	la("hai dòng con", [d.qty for d in t.items], [3.85, 3.85])
	la("tổng máy ghi đúng 347.001", sum(_tien(d) for d in t.items), 347001.0)
	dung("mỗi dòng con lệch giá in chưa tới nửa đồng",
		all(abs(d.rate - 45065) <= mc.NAN_GIA_TOI_DA for d in t.items))
	dung("giá bảng theo đơn giá dòng", all(d.price_list_rate == d.rate for d in t.items))
	# Lượt lưu sau (hook ghim lại theo gốc) không kéo cả nhóm về một giá.
	with patch.object(dl, "_do_chinh_xac", lambda doc=None, g=None: _dp()):
		la("ghim lại không đổi dòng nào", dl.ghim_lai_theo_goc(t, dict(TO_8345)), 0)
	la("vẫn đúng 347.001 sau ghim", sum(_tien(d) for d in t.items), 347001.0)


@ca("v618 Codex #512: chia tiền dòng gốc cho các dòng con, không chia được thì giữ giá")
def _chia_thuan():
	dp = _dp()
	ra = mc.gia_cac_dong_chia(7.7, [3.85, 3.85], GIA_NAN, *dp)
	la("tổng hai dòng con", sum(mc.tien_dong_may_ghi(s, g, *dp) for s, g in zip([3.85, 3.85], ra)), 347001.0)
	dp1144 = _so_le_that(TO_1144)
	sl = [100, 100, 60]
	ra = mc.gia_cac_dong_chia(260, sl, 1576.923076923, *dp1144)
	la("ba dòng con ALOIN đúng 410.000", sum(mc.tien_dong_may_ghi(s, g, *dp1144) for s, g in zip(sl, ra)), 410000.0)
	# 2,1 x 1.287 = 2.702,7 ra 2.703; ba dòng con 386,1 + 1.930,5 + 386,1 làm
	# tròn còn 2.702. Phần dư phải vào dòng có phần lẻ lớn nhất (1.930,5); dồn
	# vào dòng đầu thì dòng 0,3 phải đổi giá 3,3 đồng một đơn vị, không nắn nổi.
	sl3 = [0.3, 1.5, 0.3]
	ra = mc.gia_cac_dong_chia(2.1, sl3, 1287.0, 2, 0, 3)
	la("phần dư vào dòng lẻ lớn nhất", ra, [1287.0, 1287.33, 1287.0])
	la("ba dòng cộng đúng 2.703", sum(mc.tien_dong_may_ghi(s, g, 2, 0, 3) for s, g in zip(sl3, ra)), 2703.0)
	la("chia số tròn thì giữ nguyên giá", mc.gia_cac_dong_chia(2400, [800, 800, 800], 2300, *dp), [2300] * 3)
	la("một dòng thì không chia", mc.gia_cac_dong_chia(7.7, [7.7], GIA_NAN, *dp), [GIA_NAN])
	# Đơn giá 2 số lẻ vẫn chia được: 45.065,06 và 45.065,19 ra 173.501 + 173.500.
	ra = mc.gia_cac_dong_chia(7.7, [3.85, 3.85], 45065.06, 2, 0, 3)
	la("đơn giá 2 số lẻ vẫn cộng đúng", sum(mc.tien_dong_may_ghi(3.85, g, 2, 0, 3) for g in ra),
		mc.tien_dong_may_ghi(7.7, 45065.06, 2, 0, 3))
	# 1 x 3 = 3, chia 0,5 + 0,5: mỗi dòng 1,5 làm tròn lên 2, cộng 4. Muốn ra
	# 3 phải hạ một dòng xuống giá 2, quá nửa đồng: giữ giá cho mọi dòng như trước.
	la("không chia đúng được thì giữ giá", mc.gia_cac_dong_chia(1, [0.5, 0.5], 3, 0, 0, 3), [3, 3])
	# Bốn dòng con, đơn giá 1 số lẻ: nắn được hai dòng nhưng hai dòng kia không
	# nắn nổi, tổng vẫn lệch. Chia dở thì không ghi, giữ giá cho cả nhóm.
	la("chia dở không ra đúng tổng thì giữ giá cả nhóm",
		mc.gia_cac_dong_chia(7.0, [2.5, 1.5, 0.5, 2.5], 2351.0, 1, 0, 3), [2351.0] * 4)
	ra = mc.gia_cac_dong_chia(-7.7, [-3.85, -3.85], GIA_NAN, *dp)
	la("tờ âm cũng cộng đúng", sum(mc.tien_dong_may_ghi(s, g, *dp) for s, g in zip([-3.85, -3.85], ra)), -347001.0)
