# -*- coding: utf-8 -*-
"""v542: hạch toán kho theo sơ đồ Khải (anh Việt chốt 30/09/2026).

Số liệu ca lấy từ phiếu thật PSX-2026-00117 (1 bánh Plain Croissant, nguyên
liệu kho Baker - Nguyên liệu, thành phẩm Baker - Thành phẩm) đọc trên site
30/09/2026. Phần chạy thật (sổ cái, sổ kho, ghi sổ lại khi thiếu hàng) nằm ở
bench: vagabond/khung/kiem_that/thu_hach_toan_kho_542.py.
"""

import datetime

from vagabond import hach_toan_kho as hk
from vagabond.khung.kiem_thu.nen import ca, dung, la

TT = {"Bếp Baker": "Bếp Baker - TV", "Bếp Pastry": "Bếp Pastry - TV", "Sonneto Lab": "Sonneto Lab - TV"}


def _tt(kho):
	return TT.get(hk.ten_tt_chi_phi_bep(kho))


@ca("v542 ngày áp dụng: từ 01/10 mới áp, mốc trống là tắt")
def _moc():
	dung("30/09 chưa áp", not hk.ap_dung("2026-09-30", hk.NGAY_CAT))
	dung("01/10 áp", hk.ap_dung("2026-10-01", hk.NGAY_CAT))
	dung("nhận kiểu date", hk.ap_dung(datetime.date(2026, 10, 2), "2026-10-01"))
	dung("mốc trống là tắt", not hk.ap_dung("2026-10-05", None))
	dung("mốc rỗng là tắt", not hk.ap_dung("2026-10-05", ""))


@ca("v542 trung tâm chi phí theo kho bếp")
def _tt_bep():
	la("Baker nguyên liệu", _tt("Baker - Nguyên liệu - TV"), "Bếp Baker - TV")
	la("Baker thành phẩm", _tt("Baker - Thành phẩm - TV"), "Bếp Baker - TV")
	la("Pastry", _tt("Pastry - Nguyên liệu - TV"), "Bếp Pastry - TV")
	la("Lab", _tt("Kho Lab - TV"), "Sonneto Lab - TV")
	la("kho tổng không phải bếp", _tt("Kho tổng 307 - TV"), None)
	la("kho điểm bán không phải bếp", _tt("Kho D1 - TV"), None)


@ca("v542 phiếu Sản xuất PSX-2026-00117: nguyên liệu 621, thành phẩm 154, trung tâm Bếp Baker")
def _sx():
	dong = [
		{"item_code": "NVLT00013", "s_warehouse": "Baker - Nguyên liệu - TV", "t_warehouse": None,
			"expense_account": "6328 - Chênh lệch tồn kho - TV", "cost_center": "Main - TV"},
		{"item_code": "NVLT00021", "s_warehouse": "Baker - Nguyên liệu - TV", "t_warehouse": None,
			"expense_account": "6328 - Chênh lệch tồn kho - TV", "cost_center": "Main - TV"},
		{"item_code": "BANU00015", "s_warehouse": None, "t_warehouse": "Baker - Thành phẩm - TV",
			"is_finished_item": 1, "expense_account": "6328 - Chênh lệch tồn kho - TV", "cost_center": "Main - TV"},
	]
	la("đặt 3 dòng", hk.gan_tai_khoan_sx(dong, "621 - X - TV", "154 - Y - TV", _tt), 3)
	la("nguyên liệu 1 vào 621", dong[0]["expense_account"], "621 - X - TV")
	la("nguyên liệu 2 vào 621", dong[1]["expense_account"], "621 - X - TV")
	la("thành phẩm vào 154", dong[2]["expense_account"], "154 - Y - TV")
	dung("không còn dòng nào 6328", all("6328" not in d["expense_account"] for d in dong))
	dung("mọi dòng trung tâm Bếp Baker", all(d["cost_center"] == "Bếp Baker - TV" for d in dong))


@ca("v542 thành phẩm nhập kho không nhận ra bếp thì theo bếp của nguyên liệu; phế phẩm cũng vào 154")
def _sx_kho_la():
	dong = [
		{"s_warehouse": "Pastry - Nguyên liệu - TV", "t_warehouse": None},
		{"s_warehouse": None, "t_warehouse": "Kho Sales Online - TV", "is_finished_item": 1},
		{"s_warehouse": None, "t_warehouse": "Pastry - Nguyên liệu - TV", "is_scrap_item": 1},
	]
	hk.gan_tai_khoan_sx(dong, "621", "154", _tt)
	la("thành phẩm theo bếp nguyên liệu", dong[1]["cost_center"], "Bếp Pastry - TV")
	la("phế phẩm vào 154", dong[2]["expense_account"], "154")


@ca("v542 dòng không rõ vai trò (chuyển kho trong phiếu) thì để nguyên")
def _sx_khong_ro():
	dong = [{"s_warehouse": "Baker - Nguyên liệu - TV", "t_warehouse": "Baker - Thành phẩm - TV",
		"expense_account": "cu", "cost_center": "Main - TV"}]
	la("không đặt dòng nào", hk.gan_tai_khoan_sx(dong, "621", "154", _tt), 0)
	la("giữ tài khoản cũ", dong[0]["expense_account"], "cu")


@ca("v542 hoá đơn bán nào thì trừ kho")
def _dieu_kien_ban():
	thuong = {"posting_date": "2026-10-01"}
	dung("bán thường từ 01/10", hk.du_dieu_kien_ban(thuong, hk.NGAY_CAT, False))
	dung("trước 01/10 không", not hk.du_dieu_kien_ban({"posting_date": "2026-09-30"}, hk.NGAY_CAT, False))
	dung("trả hàng không", not hk.du_dieu_kien_ban({"posting_date": "2026-10-02", "is_return": 1}, hk.NGAY_CAT, False))
	dung("ghi nợ bổ sung không", not hk.du_dieu_kien_ban({"posting_date": "2026-10-02", "is_debit_note": 1}, hk.NGAY_CAT, False))
	dung("hàng tặng đi luồng tặng", not hk.du_dieu_kien_ban(thuong, hk.NGAY_CAT, True))
	dung("tặng luồng kho mới không", not hk.du_dieu_kien_ban({"posting_date": "2026-10-02", "vgb_tang_kho_moi": 1}, hk.NGAY_CAT, False))
	dung("chứng từ đầu kỳ không", not hk.du_dieu_kien_ban({"posting_date": "2026-10-02", "is_opening": "Yes"}, hk.NGAY_CAT, False))
	dung("tắt mốc là không", not hk.du_dieu_kien_ban(thuong, None, False))


@ca("v542 thiếu hàng: liệt kê đúng món thiếu, đủ thì rỗng")
def _thieu():
	can = {("BANU00015", "Kho D1 - TV"): 2, ("BANU00016", "Kho D1 - TV"): 1}
	ton = {("BANU00015", "Kho D1 - TV"): 1.5, ("BANU00016", "Kho D1 - TV"): 1}
	ds = hk.thieu_hang(can, ton)
	la("một món thiếu", len(ds), 1)
	la("đúng món", ds[0][0], "BANU00015")
	dung("lý do có số cần và còn", "cần 2" in hk.ly_do_thieu(ds) and "còn 1.5" in hk.ly_do_thieu(ds))
	la("không có tồn là thiếu", len(hk.thieu_hang({("A", "K"): 1}, {})), 1)
	la("đủ thì rỗng", hk.thieu_hang({("A", "K"): 1}, {("A", "K"): 1}), [])


class _Hd(dict):
	def get(self, k, d=None):
		return dict.get(self, k, d)


class QueryDeadlockError(Exception):
	pass


@ca("v542 lõi báo lỗi khi trừ kho: chỉ ghi sổ lại không trừ kho một lần, lỗi hạ tầng không lùi")
def _lui():
	hd = _Hd(vgb_tru_kho_ban=1, update_stock=1)
	dung("lỗi kho thì lùi", hk.co_the_lui(hd, Exception("negative stock")))
	dung("khoá chết không lùi", not hk.co_the_lui(hd, QueryDeadlockError()))
	dung("đã lùi rồi không lùi lần hai", not hk.co_the_lui(_Hd(vgb_tru_kho_ban=1, update_stock=1, vgb_chua_tru_kho=1), Exception()))
	dung("hoá đơn không trừ kho không lùi", not hk.co_the_lui(_Hd(vgb_tru_kho_ban=1, update_stock=0), Exception()))
	dung("hàng tặng không lùi", not hk.co_the_lui(_Hd(update_stock=1), Exception()))


@ca("v542 móc nối: trừ kho bán chạy trước hang_tang_so_cai, sản xuất ở validate; _save có đường lùi")
def _moc_noi():
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	h = open(os.path.join(goc, "hooks.py"), encoding="utf-8").read()
	dung("có hook bán", "vagabond.hach_toan_kho.ban_truoc_ghi_so" in h)
	dung("chèn trước hang_tang_so_cai", '_ds_bs.index("vagabond.hang_tang_so_cai.truoc_khi_ghi_so")' in h)
	dung("có hook sản xuất", "vagabond.hach_toan_kho.sx_gan_tai_khoan" in h)
	lop = open(os.path.join(goc, "hoa_don_hang_tang.py"), encoding="utf-8").read()
	dung("chuẩn bị bán sau chuẩn bị tặng", lop.index("chuan_bi(self)") < lop.index("ban_chuan_bi(self)"))
	dung("_save gọi co_the_lui", "co_the_lui(self, loi)" in lop)
	p = open(os.path.join(goc, "patches.txt"), encoding="utf-8").read()
	dung("patch v542 có trong patches.txt", "vagabond.patches.hach_toan_kho_v542" in p)


@ca("v542 Codex #395 F1: hoá đơn lập từ Phiếu giao hàng không trừ kho lần hai")
def _phieu_giao():
	hd = {"posting_date": "2026-10-02"}
	dung("dòng có delivery_note thì không trừ", not hk.du_dieu_kien_ban(hd, hk.NGAY_CAT, False,
		[{"item_code": "A", "delivery_note": "PGH-0001", "dn_detail": "x1"}]))
	dung("chỉ có dn_detail cũng không", not hk.du_dieu_kien_ban(hd, hk.NGAY_CAT, False, [{"dn_detail": "x1"}]))
	dung("một dòng giao, một dòng không: không trừ cả tờ", not hk.du_dieu_kien_ban(hd, hk.NGAY_CAT, False,
		[{"item_code": "A"}, {"item_code": "B", "delivery_note": "PGH-0002"}]))
	dung("không phiếu giao thì trừ", hk.du_dieu_kien_ban(hd, hk.NGAY_CAT, False, [{"item_code": "A"}]))


@ca("v542 Codex #395 F2: hoàn tiền toàn bộ hoá đơn đã trừ kho không chuyển kho bán sang kho huỷ lần nữa")
def _hoan_tien():
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	s = open(os.path.join(goc, "hoan_tien.py"), encoding="utf-8").read()
	i = s.index("def _chuyen_kho_huy(")
	than = s[i:s.index("\ndef ", i + 10)]
	dung("thoát sớm khi hoá đơn gốc đã trừ kho", 'if cint(si.get("update_stock")):' in than)
	dung("thoát trước khi dựng dòng chuyển", than.index('if cint(si.get("update_stock")):') < than.index("dong = []"))
