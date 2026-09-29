# -*- coding: utf-8 -*-
"""v540: chọn lô theo NGÀY GHI SỔ của phiếu, không theo tồn hôm nay.

Ca thật 29/09/2026: Khải làm phiếu sản xuất PSX-2026-00116 ghi lùi ngày
31/08/2026 23:59 (khoá sổ tháng 8). Máy chọn lô LO-260914-000105 cho sữa tươi
NVLT00013 vì HÔM NAY lô đó còn 9.026 ML, nhưng lô đó sinh ngày 14/09, vào
31/08 chưa có. ERPNext kiểm tồn lô tại ngày ghi sổ nên chặn "negative stock
of quantity -2893.182". Đọc trên site: ngày 31/08 kho Baker có 88.000 ML sữa
ở bảy lô khác, và lô KKK2600009 có 4.000 ML ngày 31/08 nhưng chỉ còn 2.414,812
ML hôm nay.

Số lô và số lượng dưới đây là số thật đọc trên site 29/09/2026.
"""

import datetime
import sys
import unittest.mock
from types import SimpleNamespace as NS

from vagabond import lo_hang as lh
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

KHO = "Baker - Nguyên liệu - TV"
MA = "NVLT00013"
# Tồn từng lô, đọc bằng get_batch_qty trên site.
HOM_NAY = {"LO-260914-000105": 9026.497, "LO-260915-000128": 36000, "KKK2600009-NVLT00013": 2414.812,
	"KKK2600007-NVLT00013": 24000, "NVLT00013-002": 12000, "NVLT00013-001": 12000}
NGAY_31_08 = {"KKK2600009-NVLT00013": 4000, "KKK2600007-NVLT00013": 24000,
	"NVLT00013-002": 12000, "NVLT00013-001": 12000}
HAN = {"LO-260914-000105": "2026-12-31", "LO-260915-000128": "2026-12-31",
	"KKK2600009-NVLT00013": "2027-01-30", "KKK2600007-NVLT00013": "2027-01-30",
	"NVLT00013-002": "2027-01-31", "NVLT00013-001": "2027-01-31"}


@ca("v540 tồn khả dụng cho phiếu ghi lùi ngày: chỉ lô có hàng vào ngày đó, và không quá tồn hôm nay")
def _thuan():
	kha = lh.ton_kha_dung(NGAY_31_08, HOM_NAY)
	dung("lô sinh 14/09 không dùng được cho phiếu 31/08", "LO-260914-000105" not in kha)
	dung("lô sinh 15/09 cũng không", "LO-260915-000128" not in kha)
	la("lô KKK2600009: lấy số nhỏ hơn (còn 2.414,812 hôm nay dù 31/08 có 4.000)", kha["KKK2600009-NVLT00013"], 2414.812)
	la("lô 31/08 đã hết hôm nay thì bỏ", lh.ton_kha_dung({"X": 100}, {}), {})
	la("rỗng", lh.ton_kha_dung(None, HOM_NAY), {})


class _Doc(dict):
	__getattr__ = dict.get


def _doc_ngay(chu):
	return datetime.datetime.strptime(str(chu)[:19], "%Y-%m-%d %H:%M:%S")


def _gia_lap_tai(cho_31_08=True):
	"""Thay đúng phần đọc sổ, giữ nguyên _ton_tung_lo thật để kiểm phép bọc."""
	hoi = []

	def tai(ma, kho, ke_ca_qua_han=False, luc=None):
		hoi.append(luc)
		return dict(NGAY_31_08 if luc else HOM_NAY)
	return tai, hoi


@ca("v540 luc_cua_phieu: phiếu ghi lùi ngày trả thời điểm ghi sổ, phiếu hôm nay/tương lai trả None")
def _luc():
	# frappe.utils.get_datetime của bản giả luôn trả một ngày cố định, nên dùng
	# phép đọc ngày thật của Python cho đúng hành vi Frappe.
	with unittest.mock.patch.object(lh, "now_datetime", lambda: datetime.datetime(2026, 9, 29, 18, 55)), \
			unittest.mock.patch.object(lh, "get_datetime", _doc_ngay):
		la("ghi lùi 31/08", lh.luc_cua_phieu(_Doc(posting_date="2026-08-31", posting_time="23:59:00")),
			{"posting_date": "2026-08-31", "posting_time": "23:59:00"})
		la("ghi sau giờ hiện tại", lh.luc_cua_phieu(_Doc(posting_date="2026-09-29", posting_time="23:00:00")), None)
		la("không có ngày", lh.luc_cua_phieu(_Doc()), None)


@ca("v540 _ton_tung_lo: phiếu ghi lùi thì đọc sổ HAI lần (tại ngày ghi và hôm nay) rồi lấy số nhỏ; phiếu hôm nay đọc một lần")
def _boc():
	tai, hoi = _gia_lap_tai()
	with unittest.mock.patch.object(lh, "_ton_tung_lo_tai", tai):
		la("hôm nay", lh._ton_tung_lo(MA, KHO), HOM_NAY)
		la("hỏi một lần", hoi, [None])
		hoi.clear()
		luc = {"posting_date": "2026-08-31", "posting_time": "23:59:00"}
		kq = lh._ton_tung_lo(MA, KHO, luc=luc)
	dung("hỏi cả tại ngày ghi và hôm nay", hoi == [None, luc])
	dung("không còn lô sinh sau ngày ghi", "LO-260914-000105" not in kq)


@ca("v540 đọc sổ tại ngày ghi: truyền posting_date/time cho get_batch_qty, và đường dự phòng lọc sổ kho tới đúng thời điểm đó")
def _doc_so():
	goi = []
	loc = []

	def gbq(**kw):
		goi.append(kw)
		return []  # rỗng để đi xuống đường dự phòng

	def get_all(dt, filters=None, **k):
		loc.append((dt, dict(filters or {})))
		return []
	core = NS(get_reserved_batches_for_pos=lambda a: {}, get_reserved_batches_for_sre=lambda a: {})
	with unittest.mock.patch.dict(sys.modules, {"erpnext.stock.doctype.batch.batch": NS(get_batch_qty=gbq),
			"erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle": core}), \
			unittest.mock.patch.object(lh.frappe, "get_all", get_all, create=True), \
			unittest.mock.patch.object(lh.frappe, "_dict", dict, create=True):
		lh._ton_tung_lo_tai(MA, KHO, luc={"posting_date": "2026-08-31", "posting_time": "23:59:00"})
	la("get_batch_qty nhận ngày ghi", (goi[0].get("posting_date"), goi[0].get("posting_time")), ("2026-08-31", "23:59:00"))
	so = [f for dt, f in loc if dt == "Stock Ledger Entry"]
	la("sổ kho lọc tới thời điểm ghi", so[0].get("posting_datetime"), ["<=", "2026-08-31 23:59:00"])


def _phieu(lo=None, qty=2893.182):
	from vagabond.khung.kiem_thu.thu_nhan_nvl_chon_lo import Dong, Phieu

	class P(Phieu):
		def get(self, k, mac_dinh=None):
			return getattr(self, k, mac_dinh)
	p = P("Manufacture", [Dong(item_code=MA, s_warehouse=KHO, qty=qty, conversion_factor=1, uom="ML",
		stock_uom="ML", name="d3", batch_no=lo, serial_and_batch_bundle=None)])
	p.posting_date, p.posting_time = "2026-08-31", "23:59:00"
	return p


def _chay(ham, p):
	"""Chạy THẬT gan_lo / _bo_sung_lo_tay; chỉ thay phần đọc sổ và vài cửa hồ sơ."""
	tai, _ = _gia_lap_tai()
	cua = [(lh, "_ton_tung_lo_tai", tai), (lh, "_theo_lo", lambda ma: 1),
		(lh, "_bo_lo_khong_dung", lambda ton, *a: dict(ton)),
		(lh, "_xep_het_han_truoc", lambda ton: sorted((ton or {}).items(), key=lambda kv: HAN.get(kv[0], "9"))),
		(lh, "_cac_ma_thay_the", lambda ma: []), (lh, "_kho_khac_con", lambda *a: []),
		(lh, "_ten_hang", lambda *a: MA), (lh, "_lo_trong_goi", lambda ten: {}),
		(lh, "now_datetime", lambda: datetime.datetime(2026, 9, 29, 18, 55)), (lh, "get_datetime", _doc_ngay),
		(lh.frappe, "get_cached_value", lambda *a, **k: 0),
		(lh.frappe.db, "get_value", lambda *a, **k: MA)]
	from contextlib import ExitStack
	with ExitStack() as st:
		for obj, ten, h in cua:
			st.enter_context(unittest.mock.patch.object(obj, ten, h, create=True))
		ham(p)
	return [(d.get("batch_no"), round(d.get("qty"), 3)) for d in p.items]


@ca("v540 ca thật PSX-2026-00116: dòng sữa CHƯA có lô, phiếu ghi 31/08 thì máy chọn lô có hàng ngày 31/08, không chọn LO-260914-000105")
def _gan_lo_moi():
	ra = _chay(lh.gan_lo, _phieu())
	dung("không có lô sinh 14/09", all(lo != "LO-260914-000105" for lo, _ in ra))
	la("FEFO trong các lô hợp lệ: KKK2600009 lấy đủ phần còn lại hôm nay rồi sang KKK2600007",
		ra, [("KKK2600009-NVLT00013", 2414.812), ("KKK2600007-NVLT00013", 478.37)])
	la("đủ số", round(sum(q for _, q in ra), 3), 2893.182)


@ca("v540 ca thật PSX-2026-00116: dòng sữa ĐÃ gắn LO-260914-000105 (máy gắn từ trước), lưu lại thì máy bù sang lô hợp lệ thay vì để ERPNext chặn âm")
def _bu_lo_da_gan():
	p = _phieu(lo="LO-260914-000105")
	ra = _chay(lh._bo_sung_lo_tay, p)
	la("chuyển hết sang lô có hàng ngày 31/08", ra,
		[("KKK2600009-NVLT00013", 2414.812), ("KKK2600007-NVLT00013", 478.37)])
	dung("ghi lời nhắc vào phiếu", "Đã bù phần thiếu" in (getattr(p, "remarks", "") or ""))


@ca("v540 phiếu ghi 31/08 xin nhiều hơn tồn khả dụng ngày đó: chặn với lời thiếu hàng, không cấp lô sinh sau")
def _thieu_that():
	nem("thiếu thật thì chặn", lambda: _chay(lh.gan_lo, _phieu(qty=60000)), lh.frappe.ValidationError)
