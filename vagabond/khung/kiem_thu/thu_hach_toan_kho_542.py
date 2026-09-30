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


class _Dong(dict):
	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v


class _Meta:
	def has_field(self, f):
		return True


class _Tho(dict):
	"""Tờ hoá đơn nháp mới, đủ cho ban_chuan_bi (không chạm DB)."""
	docstatus = 0
	meta = _Meta()

	def __init__(self, **kw):
		super().__init__(**kw)
		self.flags = {}

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		if k == "flags":
			dict.__setattr__(self, k, v)
		else:
			self[k] = v

	def is_new(self):
		return True


def _chay_chuan_bi(hd, ton=(), bo=(), kho="Kho Sales Online - TV", loi_cau_hinh=None):
	import unittest.mock as m
	def cau_hinh(k, c):
		if loi_cau_hinh:
			raise Exception(loi_cau_hinh)
		return "632 - GV - TV"
	with m.patch.object(hk, "_moc", lambda o: "2026-10-01"), \
			m.patch.object(hk, "_la_tang", lambda d: False), \
			m.patch.object(hk, "_ghi_so_lien_tuc", lambda c: True), \
			m.patch.object(hk, "_la_bo", lambda ma: ma in bo), \
			m.patch.object(hk, "_kho_diem_ban", lambda d: kho), \
			m.patch.object(hk, "_kiem_cau_hinh", cau_hinh), \
			m.patch.object(hk.frappe, "get_cached_value", lambda dt, ma, o: ma in ton, create=True), \
			m.patch.object(hk.frappe, "clear_last_message", lambda: None, create=True):
		hk.ban_chuan_bi(hd)
	return hd


@ca("v542 Codex #395 F3: hoá đơn chỉ có bộ sản phẩm vẫn bật trừ kho theo thành phần")
def _bo_san_pham():
	hd = _chay_chuan_bi(_Tho(posting_date="2026-10-01", company="C",
		items=[_Dong(item_code="BO-01", warehouse=None)]), ton=(), bo=("BO-01",))
	la("bật trừ kho", hd.update_stock, 1)
	la("dòng bộ nhận kho điểm bán", hd["items"][0].warehouse, "Kho Sales Online - TV")
	la("dòng bộ nhận 632", hd["items"][0].expense_account, "632 - GV - TV")
	hd2 = _chay_chuan_bi(_Tho(posting_date="2026-10-01", company="C",
		items=[_Dong(item_code="PHI-SHIP")]), ton=(), bo=())
	la("chỉ dịch vụ thì không trừ kho", hd2.update_stock, 0)


@ca("v542 Codex #395 F4: nháp lỡ đánh dấu Chưa trừ kho vì cấu hình, sửa cấu hình rồi lưu lại thì trừ kho")
def _tinh_lai_nhap():
	hd = _chay_chuan_bi(_Tho(posting_date="2026-10-01", company="C",
		items=[_Dong(item_code="BANU00015")]), ton=("BANU00015",), loi_cau_hinh="Kho chưa gắn tài khoản")
	la("lần đầu lỗi cấu hình: đánh dấu", hd.vgb_chua_tru_kho, 1)
	la("lần đầu không trừ", hd.update_stock, 0)
	_chay_chuan_bi(hd, ton=("BANU00015",))
	la("lưu lại sau khi sửa: bỏ dấu", hd.vgb_chua_tru_kho, 0)
	la("lưu lại sau khi sửa: trừ kho", hd.update_stock, 1)
	dung("xoá lý do cũ", not hd.vgb_ly_do_chua_tru_kho)


@ca("v542 lượt ghi sổ lại sau lỗi lõi giữ dấu Chưa trừ kho, không tính lại")
def _giu_khi_lui():
	hd = _Tho(posting_date="2026-10-01", company="C", items=[_Dong(item_code="BANU00015")],
		vgb_chua_tru_kho=1, update_stock=1)
	hd.flags = {"vgb_lui_tru_kho": True}
	_chay_chuan_bi(hd, ton=("BANU00015",))
	la("giữ dấu", hd.vgb_chua_tru_kho, 1)
	la("không trừ kho", hd.update_stock, 0)


@ca("v542 thiếu tài khoản 621/154: phiếu Sản xuất vẫn lưu được theo luồng cũ, không chặn")
def _sx_thieu_tk():
	import sys
	import types
	import unittest.mock as m
	loi_cls = getattr(hk.frappe, "ValidationError", None) or type("ValidationError", (Exception,), {})
	def tk(c, so, goc):
		raise loi_cls("Kế toán kiểm tài khoản %s" % so)
	nhac = []
	phieu = _Tho(purpose="Manufacture", posting_date="2026-10-02", company="C",
		items=[_Dong(s_warehouse="Baker - Nguyên liệu - TV", expense_account="cu")])
	erp = types.ModuleType("erpnext")
	erp.is_perpetual_inventory_enabled = lambda c: True
	with m.patch.dict(sys.modules, {"erpnext": erp}), \
			m.patch.object(hk, "_moc", lambda o: "2026-10-01"), \
			m.patch.object(hk, "_tk", tk), \
			m.patch.object(hk.frappe, "ValidationError", loi_cls, create=True), \
			m.patch.object(hk.frappe, "clear_last_message", lambda: None, create=True), \
			m.patch.object(hk.frappe, "msgprint", lambda *a, **k: nhac.append(a), create=True):
		hk.sx_gan_tai_khoan(phieu)
	la("giữ tài khoản cũ", phieu["items"][0].expense_account, "cu")
	la("có nhắc kế toán", len(nhac), 1)


@ca("v542 hoá đơn người lập tự bật Cập nhật kho, tự chọn kho và lô: máy không đè")
def _tu_bat():
	hd = _chay_chuan_bi(_Tho(posting_date="2026-10-01", company="C", update_stock=1,
		items=[_Dong(item_code="BANU00015", warehouse="Kho riêng - TV", batch_no="LO-1", expense_account="cu")]),
		ton=("BANU00015",), kho="")
	la("vẫn trừ kho", hd.update_stock, 1)
	la("giữ kho người chọn", hd["items"][0].warehouse, "Kho riêng - TV")
	la("giữ lô", hd["items"][0].batch_no, "LO-1")
	la("không đánh dấu", hd.vgb_chua_tru_kho, None)


@ca("v542 Codex #395 F6: tờ trộn dòng Phiếu giao hàng với dòng thêm tay thì đánh dấu Chưa trừ kho, không lọt im lặng")
def _tron_phieu_giao():
	hd = _chay_chuan_bi(_Tho(posting_date="2026-10-01", company="C", items=[
		_Dong(item_code="BANU00015", delivery_note="PGH-1", dn_detail="x"),
		_Dong(item_code="BANU00016")]), ton=("BANU00015", "BANU00016"))
	la("không trừ kho cả tờ", hd.update_stock, None)
	la("đánh dấu", hd.vgb_chua_tru_kho, 1)
	dung("lý do nói dòng thêm tay", "thêm tay" in (hd.vgb_ly_do_chua_tru_kho or ""))
	hd2 = _chay_chuan_bi(_Tho(posting_date="2026-10-01", company="C", items=[
		_Dong(item_code="BANU00015", delivery_note="PGH-1", dn_detail="x")]), ton=("BANU00015",))
	dung("tờ chỉ có dòng phiếu giao: không đánh dấu", not hd2.vgb_chua_tru_kho)


@ca("v542 Codex #395 F5: _save quyết định lùi trước khi reload, lượt lùi giữ cờ bán trừ kho")
def _lui_truoc_reload():
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	s = open(os.path.join(goc, "hoa_don_hang_tang.py"), encoding="utf-8").read()
	i = s.index("def _save(")
	than = s[i:s.index("\n\tdef ", i + 10)]
	dung("co_the_lui gọi trước rollback", than.index("lui = co_the_lui(self, loi)") < than.index("frappe.db.rollback(save_point=moc)"))
	dung("co_the_lui gọi trước reload", than.index("lui = co_the_lui(self, loi)") < than.index("self.reload()"))
	dung("lượt lùi đặt lại cờ bán trừ kho", "self.vgb_tru_kho_ban = 1" in than)


@ca("v542 Codex #397: tắt 621/154 chỉ trả dòng máy đã gắn, về đúng giá trị trước khi gắn; dòng kế toán tự chọn 621 giữ nguyên")
def _tra_tk_cu():
	cu = lambda d: {"expense_account": "CL - X", "cost_center": "Chính - X"}
	moi = {"621 - X", "154 - X"}
	nl = _Dong(expense_account="Trước - X", cost_center="TT trước - X", s_warehouse="Baker - NL - TV")
	tp = _Dong(expense_account="", cost_center="", t_warehouse="Baker - TP - TV", is_finished_item=1)
	tay = _Dong(expense_account="621 - X", cost_center="Bếp Pastry - X")
	hk.gan_tai_khoan_sx([nl, tp], "621 - X", "154 - X", lambda k: "Bếp Baker - X")
	la("máy gắn dấu dòng nguyên liệu", nl.get(hk.O_MAY_GAN), 1)
	la("nhớ tài khoản trước", nl.get(hk.O_TK_TRUOC), "Trước - X")
	la("nhớ trung tâm trước", nl.get(hk.O_TT_TRUOC), "TT trước - X")
	la("đã gắn 621", nl.expense_account, "621 - X")
	hk.gan_tai_khoan_sx([nl], "621 - X", "154 - X", lambda k: "Bếp Baker - X")
	la("lưu lại lần hai không ghi đè giá trị trước", nl.get(hk.O_TK_TRUOC), "Trước - X")
	dem = hk.tra_tai_khoan_cu([nl, tp, tay], moi, cu)
	la("trả 2 dòng máy gắn", dem, 2)
	la("nguyên liệu về tài khoản trước khi gắn", nl.expense_account, "Trước - X")
	la("nguyên liệu về trung tâm trước khi gắn", nl.cost_center, "TT trước - X")
	la("thành phẩm trống giá trị trước thì lấy cách lõi tự điền", tp.expense_account, "CL - X")
	la("thành phẩm về trung tâm lõi", tp.cost_center, "Chính - X")
	la("bỏ dấu sau khi trả", nl.get(hk.O_MAY_GAN), 0)
	la("621 kế toán tự chọn giữ nguyên", tay.expense_account, "621 - X")
	la("trung tâm kế toán tự chọn giữ nguyên", tay.cost_center, "Bếp Pastry - X")
	tp2 = _Dong(expense_account="154 - X", cost_center="Bếp Baker - X", vgb_tk_may_gan=1, vgb_tk_truoc="", vgb_tt_truoc="")
	la("không tra được thì để nguyên", hk.tra_tai_khoan_cu([tp2], moi, lambda d: None), 0)
	la("giữ 154 khi không có tài khoản cũ", tp2.expense_account, "154 - X")


@ca("v542 Codex #397: nháp Sản xuất lưu lúc bật, kế toán xoá ngày, lưu/ghi sổ lại thì bỏ 621/154")
def _tat_giua_chung():
	import unittest.mock as m
	phieu = _Tho(purpose="Manufacture", posting_date="2026-10-02", company="C", items=[
		_Dong(item_code="NVL", s_warehouse="Baker - Nguyên liệu - TV", expense_account="621 - X", cost_center="Bếp Baker - X",
			vgb_tk_may_gan=1, vgb_tk_truoc="", vgb_tt_truoc=""),
		_Dong(item_code="TP", t_warehouse="Baker - Thành phẩm - TV", is_finished_item=1, expense_account="154 - X",
			vgb_tk_may_gan=1, vgb_tk_truoc="", vgb_tt_truoc="")])
	phieu.get_item_details = lambda args: {"expense_account": "CL - X", "cost_center": "Chính - X"}
	with m.patch.object(hk, "_moc", lambda o: None), \
			m.patch.object(hk, "_tk_moi_cua", lambda c: {"621 - X", "154 - X"}), \
			m.patch.object(hk.frappe, "_dict", dict, create=True):
		hk.sx_gan_tai_khoan(phieu)
	la("nguyên liệu về cũ", phieu["items"][0].expense_account, "CL - X")
	la("thành phẩm về cũ", phieu["items"][1].expense_account, "CL - X")
	la("trung tâm chi phí về cũ", phieu["items"][0].cost_center, "Chính - X")
	phieu["items"][0].update(expense_account="621 - X", vgb_tk_may_gan=1, vgb_tk_truoc="", vgb_tt_truoc="")
	phieu["posting_date"] = "2026-09-29"
	with m.patch.object(hk, "_moc", lambda o: "2026-10-01"), \
			m.patch.object(hk, "_tk_moi_cua", lambda c: {"621 - X", "154 - X"}), \
			m.patch.object(hk.frappe, "_dict", dict, create=True):
		hk.sx_gan_tai_khoan(phieu)
	la("lùi ngày ghi về trước mốc: về cũ", phieu["items"][0].expense_account, "CL - X")
	tay = _Tho(purpose="Manufacture", posting_date="2026-10-02", company="C", items=[
		_Dong(item_code="NVL", s_warehouse="Baker - Nguyên liệu - TV", expense_account="621 - X")])
	tay.get_item_details = lambda args: {"expense_account": "CL - X", "cost_center": "Chính - X"}
	with m.patch.object(hk, "_moc", lambda o: None), \
			m.patch.object(hk, "_tk_moi_cua", lambda c: {"621 - X", "154 - X"}), \
			m.patch.object(hk.frappe, "_dict", dict, create=True):
		hk.sx_gan_tai_khoan(tay)
	la("tắt mà 621 kế toán tự chọn: giữ nguyên", tay["items"][0].expense_account, "621 - X")


@ca("v542 Codex #397: lùi ghi sổ không trừ kho thì gỡ gói lô ở cả dòng hàng lẫn thành phần bộ")
def _bo_ca_goi_thanh_phan():
	hd = _Tho(items=[_Dong(serial_and_batch_bundle="SABB-1")], packed_items=[_Dong(serial_and_batch_bundle="SABB-2")])
	hk._bo_tru_kho(hd, "Lô không đủ")
	la("dòng hàng bỏ gói", hd["items"][0].serial_and_batch_bundle, None)
	la("thành phần bỏ gói", hd["packed_items"][0].serial_and_batch_bundle, None)
	la("không trừ kho", hd.update_stock, 0)


class _Goi:
	tao = []

	def __init__(self, a):
		self.a = a

	def make_serial_and_batch_bundle(self):
		_Goi.tao.append(self.a)
		return _Dong(name="SABB-%d" % len(_Goi.tao))


def _chia(dong, bo_lo, lo_con, nhom):
	import sys
	import types
	import unittest.mock as m
	from vagabond import hang_tang_kho as htk
	_Goi.tao = []
	sbb = types.ModuleType("erpnext.stock.serial_batch_bundle")
	sbb.SerialBatchCreation = _Goi
	bt = types.ModuleType("erpnext.stock.doctype.batch.batch")
	bt.get_available_batches = lambda a: list(lo_con.get((a["item_code"], a["warehouse"]), {}).items())
	def nem(msg, *a, **k):
		raise RuntimeError(msg)
	class _Hd:
		doctype, name, company, posting_date, posting_time = "Sales Invoice", "HD-1", "C", "2026-10-01", "10:00:00"
		items = [x for x in dong if x.doctype != "Packed Item"]
		packed_items = [x for x in dong if x.doctype == "Packed Item"]

		def get(self, k, d=None):
			return getattr(self, k, d)
	hd = _Hd()
	with m.patch.dict(sys.modules, {"erpnext.stock.serial_batch_bundle": sbb, "erpnext.stock.doctype.batch.batch": bt}), \
			m.patch.object(htk.frappe, "get_cached_value", lambda dt, ma, o: ma in bo_lo, create=True), \
			m.patch.object(htk.frappe, "_dict", dict, create=True), \
			m.patch.object(htk.frappe, "throw", nem, create=True):
		htk.chia_lo_xuat(hd, nhom)
	return hd


@ca("v542 Codex #397: thành phần có lô của bộ sản phẩm được chia lô, gói gắn dòng hàng cha")
def _chia_lo_thanh_phan():
	bo = _Dong(doctype="Sales Invoice Item", idx=1, name="R1", item_code="BO", warehouse="K", stock_qty=1)
	tp = _Dong(doctype="Packed Item", item_code="TP", warehouse="K", qty=2, parent_detail_docname="R1", parent_item="BO")
	hd = _chia([bo, tp], {"TP"}, {("TP", "K"): {"L1": 5}}, {("TP", "K")})
	la("thành phần có gói lô", tp.serial_and_batch_bundle, "SABB-1")
	la("một gói", len(_Goi.tao), 1)
	la("gói gắn dòng hàng cha", _Goi.tao[0]["voucher_detail_no"], "R1")
	la("lượng theo thành phần", _Goi.tao[0]["qty"], 2)
	la("lấy lô L1", _Goi.tao[0]["batches"], {"L1": 2})
	dung("dòng bộ không lô không có gói", not bo.get("serial_and_batch_bundle"))


@ca("v542 Codex #397: thành phần thiếu lô còn dùng thì báo lỗi để lùi, không lọt im lặng")
def _chia_lo_thanh_phan_thieu():
	tp = _Dong(doctype="Packed Item", item_code="TP", warehouse="K", qty=3, parent_detail_docname="R1", parent_item="BO")
	try:
		_chia([_Dong(doctype="Sales Invoice Item", idx=1, name="R1", item_code="BO", warehouse="K", stock_qty=1), tp],
			{"TP"}, {("TP", "K"): {"L1": 1}}, {("TP", "K")})
		dung("phải báo lỗi", False)
	except RuntimeError as e:
		dung("báo thiếu theo lô", "thiếu" in str(e))


@ca("v542 Codex #397: chia lô bọc trong điểm lưu, lỗi thì quay về điểm lưu trước khi lùi")
def _diem_luu_chia_lo():
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	s = open(os.path.join(goc, "hach_toan_kho.py"), encoding="utf-8").read()
	i = s.index("def ban_truoc_ghi_so(")
	than = s[i:s.index("\ndef ", i + 10)]
	dung("có điểm lưu trước chia lô", than.index("frappe.db.savepoint(moc)") < than.index("chia_lo_xuat(doc, set(nhom))"))
	dung("quay về điểm lưu trước khi lùi", than.index("frappe.db.rollback(save_point=moc)") < than.index('_bo_tru_kho(doc, "Lô không đủ'))


@ca("v542 Codex #397: lượng cần của thành phần bộ lấy đúng qty lõi ghi sổ, không nhân lại hệ số quy đổi")
def _nhu_cau_thanh_phan():
	nhom = hk.nhu_cau_kho([_Dong(item_code="A", warehouse="K", stock_qty=3)],
		[_Dong(item_code="TP", warehouse="K", qty=2, conversion_factor=1000), _Dong(item_code="A", warehouse="K", qty=1, conversion_factor=5)])
	la("thành phần cần 2, không phải 2.000", nhom[("TP", "K")], 2)
	la("cộng dồn cùng mã cùng kho", nhom[("A", "K")], 4)
