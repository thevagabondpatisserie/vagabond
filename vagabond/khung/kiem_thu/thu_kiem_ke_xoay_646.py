# -*- coding: utf-8 -*-
"""v646 (bếp Pastry báo 09/11/2026): "Đếm hôm nay" chia 10 món giống hệt nhau
nhiều ngày liền.

Site thật: KK-26-00072 (05/11) tới KK-26-00080 (09/11) của kho Pastry - Nguyên
liệu cùng đúng 10 mã. Bếp đếm và bấm Chốt phiếu mỗi sáng, phiếu sang "Chờ
duyệt" và nằm đó chờ quản lý ghi sổ; lịch xoay vòng chỉ coi "Đã chốt" và "Đã
ghi sổ" là đã đếm, nên sáng hôm sau 10 món vừa cân lại "chưa đếm bao giờ" và
lên đầu danh sách.

Ca chạy CÂU SQL THẬT của kiem_ke trên sqlite (khuôn Kho của
thu_zalo_645_sql), dựng đúng chuỗi thao tác của bếp: sáng 1 máy chia, bếp
đếm, chốt (Chờ duyệt), sáng 2 máy chia lại.
"""

import datetime as dt
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import kiem_ke as kk  # noqa: E402
from vagabond.khung.kiem_thu.thu_zalo_645_sql import Kho  # noqa: E402

KHO = "Pastry - Nguyên liệu - TV"


class KhoKK(Kho):
	BANG = {
		"tabBin": ["item_code", "warehouse", "actual_qty", "stock_value"],
		"tabItem": ["name", "item_name", "item_group", "stock_uom", "disabled"],
		"tabPhieu Kiem Ke": ["name", "kho", "ngay_kiem", "trang_thai"],
		"tabChi Tiet Kiem Ke": ["name", "parent", "item_code", "da_dem"],
	}


def _dung_kho(so_mon=40):
	k = KhoKK()
	for i in range(so_mon):
		ma = "NVL%03d" % i
		k.them("tabItem", name=ma, item_name="Món %d" % i, item_group="Nguyên vật liệu", stock_uom="Gram", disabled=0)
		# giá trị giảm dần: món 0 đắt nhất
		k.them("tabBin", item_code=ma, warehouse=KHO, actual_qty=10, stock_value=1000000 - i * 1000)
	return k


def _lich(k, ngay):
	with um.patch.object(kk.frappe.db, "sql", k.sql), um.patch.object(kk, "nowdate", lambda: ngay), \
			um.patch.object(kk, "getdate", lambda v: dt.date.fromisoformat(str(v)[:10])), \
			um.patch.object(kk, "duoc_duyet", lambda: False):
		return kk.lich_kho(KHO, kk.MOI_NGAY_BEP)


def _bep_dem(k, ten, ngay, ma_ds, trang_thai):
	k.them("tabPhieu Kiem Ke", name=ten, kho=KHO, ngay_kiem=ngay, trang_thai=trang_thai)
	for i, ma in enumerate(ma_ds):
		k.them("tabChi Tiet Kiem Ke", name="%s-%d" % (ten, i), parent=ten, item_code=ma, da_dem=1)


@ca("v646 Đếm hôm nay: bếp đã đếm và chốt (Chờ duyệt, quản lý chưa ghi sổ) thì sáng hôm sau máy chia 10 món KHÁC, không lặp lại")
def _cho_duyet_khong_lap():
	k = _dung_kho()
	sang1 = [d["ma_hang"] for d in _lich(k, "2026-11-05")["dong"]]
	la("sáng 1 chia đủ 10 món", len(sang1), 10)
	_bep_dem(k, "KK-1", "2026-11-05", sang1, "Chờ duyệt")
	sang2 = [d["ma_hang"] for d in _lich(k, "2026-11-06")["dong"]]
	la("sáng 2 vẫn đủ 10 món", len(sang2), 10)
	la("sáng 2 không trùng món nào của sáng 1", sorted(set(sang1) & set(sang2)), [])
	_bep_dem(k, "KK-2", "2026-11-06", sang2, "Chờ duyệt")
	sang3 = [d["ma_hang"] for d in _lich(k, "2026-11-07")["dong"]]
	la("sáng 3 không trùng hai sáng trước", sorted(set(sang3) & (set(sang1) | set(sang2))), [])


@ca("v646 Đếm hôm nay: phiếu bị huỷ hay còn đang đếm dở thì món đó vẫn được chia lại; đã chốt, đã ghi sổ thì không")
def _trang_thai_khac():
	k = _dung_kho()
	sang1 = [d["ma_hang"] for d in _lich(k, "2026-11-05")["dong"]]
	_bep_dem(k, "KK-H", "2026-11-05", sang1[:3], "Đã huỷ")
	_bep_dem(k, "KK-D", "2026-11-05", sang1[3:6], "Đang kiểm")
	_bep_dem(k, "KK-C", "2026-11-05", sang1[6:8], "Đã chốt")
	_bep_dem(k, "KK-G", "2026-11-05", sang1[8:], "Đã ghi sổ")
	sang2 = set(d["ma_hang"] for d in _lich(k, "2026-11-06")["dong"])
	dung("huỷ: chia lại", set(sang1[:3]) <= sang2)
	dung("đang đếm dở: chia lại", set(sang1[3:6]) <= sang2)
	la("đã chốt, đã ghi sổ: không chia lại", sorted(set(sang1[6:]) & sang2), [])


@ca("v646 Đếm hôm nay: món đã đếm (chờ duyệt) quay lại đúng chu kỳ, món đắt (hạng A) sau 7 ngày")
def _quay_lai_dung_chu_ky():
	k = _dung_kho(12)
	sang1 = [d["ma_hang"] for d in _lich(k, "2026-11-01")["dong"]]
	_bep_dem(k, "KK-1", "2026-11-01", sang1, "Chờ duyệt")
	sau6 = set(d["ma_hang"] for d in _lich(k, "2026-11-07")["dong"])
	dung("món 0 (hạng A) chưa tới hạn sau 6 ngày", "NVL000" not in sau6)
	sau7 = set(d["ma_hang"] for d in _lich(k, "2026-11-08")["dong"])
	dung("món 0 (hạng A) tới hạn sau 7 ngày", "NVL000" in sau7)
