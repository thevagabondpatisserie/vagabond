"""#227: tái hiện Nam An, chiết khấu 5561 và 2.400 trứng chia ba phiếu.

Chạy chính hàm xử lý với DB giả ở biên. Tầng này không thay cho ca
insert/submit và GL thật trong kiem_that/thu_mua_hddt_227.py.
"""

from contextlib import ExitStack
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import minvoice_chung_tu as mc, dung_lai_hddt as dl, doi_chieu_mua as dc, mua_dich_vu as dv
from vagabond.khung.kiem_thu.nen import ca, dung, la


class To(SimpleNamespace):
	def __getattr__(self, ten):
		return None
	def get(self, ten, mac_dinh=None):
		return getattr(self, ten, mac_dinh)
	def set(self, ten, so):
		setattr(self, ten, so)
		if ten == "items":
			for i, d in enumerate(so, 1):
				d.idx = i
	def append(self, ten, du):
		d = To(**du)
		getattr(self, ten).append(d)
		d.idx = len(getattr(self, ten))
		return d
	def as_dict(self):
		return dict(self.__dict__)


def _dong(sl=2400, gia=2300, **them):
	d = dict(name="ROW", item_code="EGG", item_name="Trứng gà tươi", ten_hang_ncc="Trứng gà tươi",
		qty=sl, rate=gia, amount=sl * gia, uom="PCS", stock_uom="PCS", conversion_factor=1, idx=1)
	d.update(them)
	return To(**d)


def _phieu():
	return {"P" + str(i): [dict(name="R" + str(i), item_code="EGG", qty=800, rate=2275,
		uom="PCS", stock_uom="PCS", conversion_factor=1)] for i in range(3)}


def _gia_lap(phieu, da_dung=None, giu_gia=0, vuot=True):
	bo = ExitStack()
	bo.enter_context(patch.object(dc, "_dong_pnk", lambda p: deepcopy(phieu[p])))
	bo.enter_context(patch.object(dc, "_vuot_lech_gia_duoc", lambda: vuot))
	bo.enter_context(patch.object(dc, "_ghi_chu_lech_gia", lambda *a: None))
	bo.enter_context(patch.object(dc, "_khong_qua_kho", lambda *a: False))
	bo.enter_context(patch.object(dc, "frappe", SimpleNamespace(get_all=lambda *a, **k: da_dung or [],
		db=SimpleNamespace(get_single_value=lambda *a: giu_gia))))
	return bo


@ca("#227: Thanh An 2.400 PCS nối ba phiếu, giữ giá 5.520.000 và bấm lại không đúp")
def _ba_phieu():
	t = To(name="PI", items=[_dong()])
	with _gia_lap(_phieu(), giu_gia=1):
		ra = dc._noi(t, ["P0", "P1", "P2", "P2"], True)
		la("nối đủ ba dòng", ra["da_noi"], 3)
		la("không báo thiếu giả", ra["loi"], [])
		la("đủ ba pr_detail", {d.pr_detail for d in t.items}, {"R0", "R1", "R2"})
		la("không lấy giá phiếu nhập", sum(d.qty * d.rate for d in t.items), 5520000)
		la("đủ lượng", sum(d.qty for d in t.items), 2400)
		la("bấm lại không nối thêm", dc._noi(t, ["P0", "P1", "P2"], True)["da_noi"], 0)
		la("không nhân số dòng", len(t.items), 3)


@ca("#227: trừ lượng PI khác đã dùng và dòng đã nối trên cùng phiếu")
def _luong_con():
	for da_dung, dong in (([To(pr_detail="R0", qty=400, conversion_factor=1)], [_dong()]),
		([], [_dong(400, purchase_receipt="P0", pr_detail="R0"), _dong()])):
		t = To(name="PI", items=dong)
		with _gia_lap(_phieu(), da_dung):
			ra = dc._noi(t, ["P0", "P1", "P2"], True)
			la("không nối vượt", ra["da_noi"], 0)
			dung("báo đúng chỉ còn 2000", "2000" in ra["loi"][0])


@ca("#227: phân bổ nhiều phiếu vẫn giữ cửa đơn vị và quyền giá")
def _gia_dvt():
	t = To(name="PI", items=[_dong()])
	with _gia_lap(_phieu(), giu_gia=1, vuot=False):
		la("không vượt quyền giá", dc._noi(t, list(_phieu()), True)["da_noi"], 0)
	phieu = _phieu()
	for ds in phieu.values():
		ds[0]["conversion_factor"] = 1000
	t = To(name="PI", items=[_dong()])
	with _gia_lap(phieu):
		la("không đoán hệ số", dc._noi(t, list(phieu), True)["da_noi"], 0)


@ca("#227: tchat 3 và nhãn chiết khấu không thành mã hàng; tchat 4 không có tiền")
def _phan_loai():
	for d in ({"tchat": 3, "ten": "Giảm theo hợp đồng"}, {"ten": "Chiết khấu thương mại"}, {"ten": "Chiết khấu"}):
		la("không vào bảng hàng", mc.dong_hang_hoa([d]), [])
	la("không bỏ món chỉ vì có chữ giảm", len(mc.dong_hang_hoa([{"ten": "Bánh giảm đường"}])), 1)
	la("ghi chú không vào bảng hàng", mc.dong_hang_hoa([{"tchat": 4, "thtien": 100}]), [])
	for so in (28935, -28935):
		la("trừ đúng một lần cả khi nguồn ghi âm", dv.gom_dong_theo_tinh_chat([
			{"thtien": 578700}, {"tchat": 3, "thtien": so}]), 549765)


def _goc():
	return {"so_hd": "5561", "ky_hieu": "C26TYY", "tong_tien": 593746,
		"tien_thue": 43981, "tien_truoc_thue": 549765, "chi_tiet": [
			{"ten": "Rong biển", "sluong": 5, "dgia": 69444, "thtien": 347220},
			{"ten": "Nước mắm", "sluong": 5, "dgia": 46296, "thtien": 231480},
			{"ten": "Chiết khấu", "tchat": 3, "sluong": 1, "dgia": 28935, "thtien": 28935}]}


def _thue(tien):
	return To(account_head="1331 - CTY", tax_amount=tien, rate=0)


@ca("#227: dựng lại 5561 bỏ dòng giảm giả, sửa giảm 57.870 về 28.935")
def _dung_chiet_khau():
	t = To(name="PI", supplier="NCC", company="CTY", cost_center="CC", items=[], taxes=[_thue(43981)])
	with patch.object(mc, "_tra_ma_hang", lambda *a: (None, "Nos", 1)), patch.object(dl, "_do_chinh_xac", lambda: (2, 2, 3)):
		dl._dung_dong_tai_cho(t, _goc())
		la("chỉ hai dòng hàng", len(t.items), 2)
		la("giảm một lần", t.discount_amount, 28935)
		la("tổng đúng", sum(d.qty * d.rate for d in t.items) - t.discount_amount + sum(d.tax_amount for d in t.taxes), 593746)
		dl._dung_dong_tai_cho(t, _goc())
		la("lưu lại không nhân chiết khấu", t.discount_amount, 28935)


@ca("#227: Nam An tiền hàng đã khớp vẫn xoá thuế cộng thêm, cả save và submit")
def _nam_an():
	g = dict(tong_tien=319800, tien_thue=15229, tien_truoc_thue=304571, chi_tiet=[])
	for trang_thai, hanh_dong in ((0, "save"), (1, "submit")):
		t = To(name="PI", docstatus=trang_thai, _action=hanh_dong, custom_minvoice_id="M",
			items=[_dong(2, 152286, item_tax_template="TAX8")], taxes=[_thue(15229), _thue(24365.76)])
		with patch.object(dl, "_goc", lambda *a: g), patch.object(dl, "hoc_ma_hang", lambda *a: 0):
			dl.dong_bo_luc_luu(t)
		la("chỉ thuế gốc", sum(d.tax_amount for d in t.taxes), 15229)
		la("mẫu thuế không nạp lại", t.items[0].item_tax_template, "")
		la("giá không bị pricing rule đổi", t.ignore_pricing_rule, 1)


@ca("#227: ghim lại giá không nhân 2400 lên từng dòng đã chia phiếu")
def _ghim_chia():
	t = To(items=[_dong(800, 2275, purchase_receipt="P" + str(i)) for i in range(3)])
	g = {"chi_tiet": [{"ten": "Trứng gà tươi", "sluong": 2400, "dgia": 2300, "dvtinh": "PCS"}]}
	with patch.object(mc, "don_vi_theo_ma", lambda *a: ("PCS", 1)):
		dl.ghim_lai_theo_goc(t, g)
	la("giữ tổng lượng", sum(d.qty for d in t.items), 2400)
	la("giữ tổng tiền HĐĐT", sum(d.qty * d.rate for d in t.items), 5520000)


@ca("#227: tính chất nguồn rõ có ưu tiên hơn nhãn và hệ số ưu tiên hơn tên đơn vị")
def _khong_doan():
	la("ghi chú không bị đổi thành chiết khấu", mc.tinh_chat_dong({"tchat": 4, "ten": "Chiết khấu"}), "4")
	la("hàng rõ không bị đoán theo tên", mc.tinh_chat_dong({"tchat": 1, "ten": "Chiết khấu thương mại"}), "1")
	la("dịch vụ bỏ ghi chú", dv.gom_dong_theo_tinh_chat([
		{"thtien": 1000}, {"tchat": 4, "ten": "Chiết khấu", "thtien": 100}]), 1000)
	dung("cùng PCS khác hệ số vẫn lệch", dc.dvt_mua.lech_don_vi("PCS", 1, "PCS", 1000))


@ca("#227: submit khoá PR, current read hoá đơn đã ghi và chặn vượt lượng dù giá thấp")
def _hai_nhap():
	goi = []
	def sql(cau, gia_tri, **kw):
		goi.append(cau)
		if "tabPurchase Receipt Item" in cau:
			return [To(name="R0", parent="P0", qty=800, conversion_factor=1)]
		return [To(pr_detail="R0", qty=800, conversion_factor=1)]
	def nem(cau):
		raise ValueError(cau)
	t = To(name="PI2", items=[_dong(800, 1, pr_detail="R0", purchase_receipt="P0")])
	with patch.object(dc, "frappe", SimpleNamespace(db=SimpleNamespace(sql=sql), throw=nem)):
		try:
			dc.chan_vuot_luong_da_nhan(t)
		except ValueError as loi:
			dung("báo hoá đơn khác dùng rồi", "Có hoá đơn khác" in str(loi))
		else:
			dung("phải chặn", False)
	la("khoá và đọc trong cùng giao dịch", len(goi), 2)
	dung("không dùng snapshot cũ", all("for update" in s for s in goi))
	dung("loại trừ chính phiếu đang submit", "d.parent != %(hd)s" in goi[1])


@ca("#227: 2400 Quả bằng 2400 PCS khi danh mục trứng khai cả hai hệ số 1")
def _trung_qua_pcs():
	t = To(name="PI", items=[_dong(uom="Quả")])
	with _gia_lap(_phieu(), giu_gia=1):
		dc.frappe.db.get_value = lambda dt, loc, cot: 1 if loc["uom"] == "PCS" else None
		ra = dc._noi(t, list(_phieu()), True)
		la("không báo lệch tên giả", ra["loi"], [])
		la("đủ ba phiếu", ra["da_noi"], 3)
		la("tổng lượng kho", sum(d.qty * d.conversion_factor for d in t.items), 2400)
		la("không đổi tiền", sum(d.qty * d.rate for d in t.items), 5520000)
		la("tên theo phiếu", {d.uom for d in t.items}, {"PCS"})


@ca("#227: dựng lại tờ âm không tạo đơn giá âm rồi che bằng chiết khấu")
def _dung_to_am():
	for muc_tieu, giam, so_dong in ((-200, 0, 1), (-180, -20, 1), (-220, 0, 2)):
		g = dict(tong_tien=muc_tieu, tien_thue=0, tien_truoc_thue=muc_tieu,
			chi_tiet=[dict(ten="Món trả", sluong=-2, dgia=-100, thtien=-200)])
		t = To(name="PI", supplier="NCC", items=[], taxes=[_thue(0)])
		with patch.object(mc, "_tra_ma_hang", lambda *a: (None, "Nos", 1)), patch.object(dl, "_do_chinh_xac", lambda: (2, 2, 3)):
			la("dự kiến theo đúng dấu", dl.du_kien_tong(t, g), muc_tieu)
			for _ in range(2):
				dl._dung_dong_tai_cho(t, g)
				la("là trả lại", t.is_return, 1)
				la("không bù giả", len(t.items), so_dong)
				la("giảm theo chiều tờ", t.discount_amount, giam)
				la("giá hàng dương", t.items[0].rate, 100)
				la("lượng hàng âm", t.items[0].qty, -2)
				la("đúng tiền", sum(d.qty * d.rate for d in t.items) - t.discount_amount, muc_tieu)
				dung("mọi đơn giá không âm", all(d.rate >= 0 for d in t.items))
		t.items[0].qty = 2
		t.items[0].rate = -100
		dl.ghim_lai_theo_goc(t, g)
		la("ghim lượng đúng", t.items[0].qty, -2)
		la("ghim giá đúng", t.items[0].rate, 100)


@ca("#227: chiết khấu trên tờ trả giảm trị tuyệt đối, không tăng tiền trả")
def _giam_to_am():
	for so in (-20, 20):
		la("âm 200 giảm 20 còn âm 180", dv.gom_dong_theo_tinh_chat([
			{"thtien": -200}, {"tchat": 3, "thtien": so}], -1), -180)


@ca("#227: tổng tờ âm khớp không cho phép bỏ qua dấu lượng và giá")
def _tong_khop_dau_sai():
	g = dict(tong_tien=-200, tien_thue=0, tien_truoc_thue=-200,
		chi_tiet=[dict(ten="Món trả", sluong=-2, dgia=-100, thtien=-200)])
	for sl, gia, giam in ((2, -100, 0), (-2, -100, 400)):
		t = To(name="PI", supplier="NCC", docstatus=0, custom_minvoice_id="M", discount_amount=giam,
			items=[_dong(sl, gia, item_code=None, item_name="Món trả", ten_hang_ncc="Món trả")], taxes=[_thue(0)])
		with patch.object(dl, "_goc", lambda *a: g), patch.object(dl, "hoc_ma_hang", lambda *a: 0), patch.object(mc, "_tra_ma_hang", lambda *a: (None, "Nos", 1)), patch.object(dl, "_do_chinh_xac", lambda: (2, 2, 3)):
			dl.dong_bo_luc_luu(t)
		la("lượng âm", t.items[0].qty, -2)
		la("giá dương", t.items[0].rate, 100)
		la("không giảm giả", t.discount_amount, 0)
		la("trả lại", t.is_return, 1)


@ca("#227: tên trùng khiến ghim bỏ qua vẫn phải dựng đúng dấu trước tổng khớp")
def _am_trung_ten():
	g = dict(tong_tien=-200, tien_thue=0, tien_truoc_thue=-200,
		chi_tiet=[dict(ten="Món trả", sluong=-1, dgia=100, thtien=-100) for _ in range(2)])
	t = To(name="PI", supplier="NCC", docstatus=0, custom_minvoice_id="M", discount_amount=0,
		items=[_dong(1, -100, item_code=None, item_name="Món trả", ten_hang_ncc="Món trả") for _ in range(2)], taxes=[_thue(0)])
	with patch.object(dl, "_goc", lambda *a: g), patch.object(dl, "hoc_ma_hang", lambda *a: 0), patch.object(mc, "_tra_ma_hang", lambda *a: (None, "Nos", 1)), patch.object(dl, "_do_chinh_xac", lambda: (2, 2, 3)):
		for _ in range(2):
			dl.dong_bo_luc_luu(t)
			la("hai dòng đúng dấu", [(d.qty, d.rate) for d in t.items], [(-1, 100), (-1, 100)])
			la("không giảm giả", t.discount_amount, 0)
