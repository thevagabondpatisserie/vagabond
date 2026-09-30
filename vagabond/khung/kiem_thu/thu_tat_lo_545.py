# -*- coding: utf-8 -*-
"""v545: tắt lô cho mọi mã. Phần thuần: chọn đúng mã phải tắt.

Ca chạy thật trên ERPNext (mã còn tồn ở lô cũ, tắt lô rồi kiểm kê về 0,
xuất, nhập) nằm ở kiem_that/tat_lo_545.py.
"""

from vagabond import tat_lo
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("v545: mã bật lô phải tắt, mã chỉ còn cờ hạn dùng hay tự sinh lô cũng phải tắt")
def _can_tat():
	dung("bật lô", tat_lo.can_tat({"has_batch_no": 1}))
	dung("chỉ còn cờ hạn dùng", tat_lo.can_tat({"has_batch_no": 0, "has_expiry_date": 1}))
	dung("chỉ còn cờ tự sinh lô", tat_lo.can_tat({"create_new_batch": "1"}))
	dung("mã thường không đụng", not tat_lo.can_tat({"has_batch_no": 0, "has_expiry_date": 0, "create_new_batch": 0}))
	dung("thiếu cờ coi như tắt", not tat_lo.can_tat({}))


@ca("v545: chọn mã giữ thứ tự, bỏ trùng, bỏ dòng không tên")
def _chon_ma():
	ds = [
		{"name": "BANU00050", "has_batch_no": 1},
		{"name": "NVLT001", "has_batch_no": 0},
		{"name": "BANU00050", "has_batch_no": 1},
		{"name": "", "has_batch_no": 1},
		{"name": "NVLT295", "has_batch_no": 1, "has_expiry_date": 1},
	]
	la("danh sách", tat_lo.chon_ma(ds), ["BANU00050", "NVLT295"])
	la("rỗng", tat_lo.chon_ma(None), [])


@ca("v545: tắt đúng ba cờ lô, không đụng hạn dùng theo ngày của mã")
def _ba_co():
	la("ba cờ", tat_lo.TRUONG_LO, ("has_batch_no", "has_expiry_date", "create_new_batch"))
	dung("không đụng shelf_life_in_days", "shelf_life_in_days" not in tat_lo.TRUONG_LO)
