# -*- coding: utf-8 -*-
"""v650 (anh Việt cho phép 12/11/2026): bản vá dọn dòng 33311 tự thêm trên chứng từ
mua CŨ (patches/v650_bo_thue_ra_cu.py). Chạy THẬT tinh_bo_thue, kiem_sau_bo, sua_mot
và execute trên cơ sở dữ liệu giả; ca ERPNext thật ở kiem_that/thu_thue_mua_hai_lan_650."""
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import thue_don_mua as tdm  # noqa: E402
from vagabond.patches import v650_bo_thue_ra_cu as vb  # noqa: E402

VAO = "1331 - Thuế GTGT được khấu trừ của hàng hóa, dịch vụ - TV"
RA = "33311 - Thuế GTGT đầu ra - TV"


def _d(name, tk, thue, tong, add="Add"):
	return {"name": name, "account_head": tk, "charge_type": "On Net Total", "rate": 0, "tax_amount": thue,
		"base_tax_amount": thue, "total": tong, "base_total": tong, "add_deduct_tax": add}


def _cha(**k):
	c = {"net_total": 620000.0, "grand_total": 719200.0, "base_grand_total": 719200.0, "total_taxes_and_charges": 99200.0,
		"base_total_taxes_and_charges": 99200.0, "taxes_and_charges_added": 99200.0, "base_taxes_and_charges_added": 99200.0,
		"rounded_total": 719200.0, "base_rounded_total": 719200.0, "disable_rounded_total": 0, "advance_paid": 0.0,
		"currency": "VND", "company": "TV"}
	c.update(k)
	return c


@ca("v650 thuần tinh_bo_thue (ca DMH-2026-00970): chỉ trừ dòng 33311, giữ thuế 1331 như đã ghi, tổng và cộng dồn từng dòng đúng")
def _():
	dong = [_d("t1", VAO, 49600.0, 669600.0), _d("t2", RA, 49600.0, 719200.0)]
	moi, dm = tdm.tinh_bo_thue(_cha(), dong, [1])
	la("tổng, thuế, cộng thêm, làm tròn", (moi["grand_total"], moi["base_grand_total"], moi["total_taxes_and_charges"],
		moi["taxes_and_charges_added"], moi["rounded_total"], moi["rounding_adjustment"]), (669600.0, 669600.0, 49600.0, 49600.0, 669600, 0.0))
	la("dòng giữ lại", dm, [{"name": "t1", "idx": 1, "total": 669600.0, "base_total": 669600.0}])
	# 33311 đứng trước dòng khác: cộng dồn của dòng sau phải trừ phần bỏ.
	dong = [_d("t1", RA, 100.0, 1100.0), _d("t2", VAO, 80.0, 1180.0)]
	moi, dm = tdm.tinh_bo_thue(_cha(grand_total=1180.0, base_grand_total=1180.0, rounded_total=1180.0, base_rounded_total=1180.0,
		total_taxes_and_charges=180.0, base_total_taxes_and_charges=180.0, taxes_and_charges_added=180.0,
		base_taxes_and_charges_added=180.0), dong, [0])
	la("dòng sau: cộng dồn trừ phần bỏ, đánh lại số thứ tự", dm, [{"name": "t2", "idx": 1, "total": 1080.0, "base_total": 1080.0}])
	# Thuế lẻ (ca DMH-2026-00719, 6,24 đ): làm tròn tổng theo tiền tệ.
	moi, _ = tdm.tinh_bo_thue(_cha(grand_total=115092.48, base_grand_total=115092.48, rounded_total=115092.0, base_rounded_total=115092.0),
		[_d("t1", VAO, 15086.24, 115086.24), _d("t2", RA, 6.24, 115092.48)], [1])
	la("thuế lẻ: tổng 115.086,24, làm tròn 115.086", (moi["grand_total"], moi["rounded_total"], moi["rounding_adjustment"]), (115086.24, 115086, -0.24))
	moi, _ = tdm.tinh_bo_thue(_cha(disable_rounded_total=1, rounded_total=0.0), [_d("t1", VAO, 49600.0, 669600.0), _d("t2", RA, 49600.0, 719200.0)], [1])
	dung("tắt làm tròn: không đặt tổng làm tròn", "rounded_total" not in moi)


@ca("v650 thuần kiem_sau_bo: chỉ đạt khi tổng giảm đúng phần 33311, tiền hàng và thuế 1331 giữ nguyên, ứng trước không vượt tổng mới")
def _():
	t = {"net_total": 620000, "grand_total": 719200, "thue_giu": 49600, "advance_paid": 0}
	la("đạt", tdm.kiem_sau_bo(t, dict(t, grand_total=669600), 49600), [])
	la("lệch 1 đồng làm tròn vẫn đạt", tdm.kiem_sau_bo(t, dict(t, grand_total=669601), 49600), [])
	la("tiền hàng đổi", tdm.kiem_sau_bo(t, dict(t, grand_total=669600, net_total=600000), 49600), ["tiền hàng đổi"])
	la("thuế 1331 đổi", tdm.kiem_sau_bo(t, dict(t, grand_total=670600, thue_giu=50600), 49600),
		["thuế đầu vào đổi", "tổng không giảm đúng phần thuế bỏ"])
	la("ứng trước vượt", tdm.kiem_sau_bo(dict(t, advance_paid=700000), dict(t, grand_total=669600, advance_paid=700000), 49600),
		["đã ứng trước nhiều hơn tổng mới"])


class _Meta:
	def __init__(self, co):
		self.co = co

	def has_field(self, k):
		return k in self.co

	def get_field(self, k):
		return k if k in self.co else None


class _Db:
	def __init__(self, cha, dong):
		self.cha, self.dong, self.ghi, self.xoa = cha, dong, [], []

	def get_value(self, dt, ten, cot, as_dict=False):
		self.cot = cot
		return {k: self.cha.get(k) for k in cot}

	def set_value(self, dt, ten, gia_tri, update_modified=True):
		self.ghi.append((dt, ten, gia_tri, update_modified))

	def delete(self, dt, loc):
		self.xoa.append((dt, loc))


def _chay(cha, dong, co=None, lich=None):
	co = co or set(_cha()) | {"in_words", "base_in_words", "rounding_adjustment", "base_rounding_adjustment", "payment_schedule"}
	lich = lich if lich is not None else [{"name": "ps1", "invoice_portion": 100.0, "payment_amount": cha["grand_total"],
		"paid_amount": 0.0, "base_paid_amount": 0.0, "discounted_amount": 0.0}]
	db, ghi_chu = _Db(cha, dong), []

	class _Doc(dict):
		def insert(self, **k):
			ghi_chu.append(self["content"])

	with patch.object(vb.frappe, "db", db, create=True), \
			patch.object(vb.frappe, "get_meta", lambda dt: _Meta(co), create=True), \
			patch.object(vb.frappe, "get_all", lambda dt, **k: [dict(r) for r in (dong if dt == "Purchase Taxes and Charges" else lich)],
				create=True), \
			patch.object(vb.frappe, "get_doc", lambda d: _Doc(d), create=True), \
			patch.object(vb.frappe, "get_cached_value", lambda *a: "VND", create=True), \
			patch("frappe.utils.round_based_on_smallest_currency_fraction", lambda x, c, p=0: round(x), create=True), \
			patch("frappe.utils.money_in_words", lambda so, tien: "chữ %d" % so, create=True):
		kq = vb.sua_mot("Purchase Order", "DMH-1")
	return kq, db, ghi_chu


@ca("v650 bản vá chứng từ cũ (DMH-2026-00970): 719.200 ra 669.600, chỉ xoá dòng 33311 và chi tiết thuế của dòng đó, không đổi mốc sửa, có ghi chú")
def _():
	dong = [_d("t1", VAO, 49600.0, 669600.0), _d("t2", RA, 49600.0, 719200.0)]
	kq, db, gc = _chay(_cha(), dong)
	la("trước và sau", (kq["truoc"]["grand_total"], kq["sau"]["grand_total"]), (719200.0, 669600.0))
	cha = db.ghi[0]
	la("ghi chứng từ: tổng, bằng chữ, không đổi mốc sửa", (cha[2]["grand_total"], cha[2]["rounded_total"], cha[2]["in_words"], cha[3]),
		(669600.0, 669600, "chữ 669600", False))
	la("ghi dòng 1331", db.ghi[1], ("Purchase Taxes and Charges", "t1", {"idx": 1, "total": 669600.0, "base_total": 669600.0}, False))
	la("xoá đúng dòng 33311 và chi tiết thuế của nó", db.xoa, [("Purchase Taxes and Charges", {"name": ["in", ["t2"]]}),
		("Item Wise Tax Detail", {"parenttype": "Purchase Order", "parent": "DMH-1", "tax_row": ["in", ["t2"]]})])
	dung("ghi chú có số trước và sau", "99.200 → 49.600" in gc[0] and "719.200 → 669.600" in gc[0])


@ca("v650 bản vá: tổng cũ lệch tiền hàng cộng thuế hoặc ứng trước vượt thì KHÔNG ghi gì; không có 1331 thì không đụng; chỉ đọc cột chứng từ có")
def _():
	dong = [_d("t1", VAO, 49600.0, 669600.0), _d("t2", RA, 49600.0, 719200.0)]
	kq, db, gc = _chay(_cha(grand_total=700000.0), dong)
	la("tổng cũ lệch: bỏ qua", kq, {"ten": "DMH-1", "loi": ["tổng cũ không bằng tiền hàng cộng thuế"]})
	la("không ghi, không xoá, không ghi chú", (db.ghi, db.xoa, gc), ([], [], []))
	kq, db, gc = _chay(_cha(advance_paid=700000.0), dong)
	la("ứng trước vượt tổng mới: bỏ qua", kq["loi"], ["đã ứng trước nhiều hơn tổng mới"])
	la("không ghi", (db.ghi, db.xoa), ([], []))
	kq, db, gc = _chay(_cha(), [_d("t2", RA, 49600.0, 669600.0)])
	la("không có 1331: không đụng", (kq, db.ghi, db.xoa), (None, [], []))
	co = set(_cha()) - {"advance_paid"}
	kq, db, gc = _chay(_cha(), dong, co=co)
	dung("phiếu nhập không có cột ứng trước: không đọc cột đó, vẫn sửa", "advance_paid" not in db.cot and kq.get("sau"))
	dung("không ghi cột chứng từ không có", "rounding_adjustment" not in db.ghi[0][2])


@ca("v650 bản vá execute: chỉ đơn mua, phiếu nhập, báo giá (không hoá đơn mua); chứng từ không đạt ghi Error Log, chứng từ khác vẫn sửa")
def _():
	hoi, log = [], []
	ds = {"Purchase Order": ["A", "B"], "Purchase Receipt": ["C"], "Supplier Quotation": []}

	def sua(dt, ten):
		if ten == "B":
			return {"ten": "B", "loi": ["tiền hàng đổi"]}
		return {"ten": ten, "truoc": {}, "sau": {}}

	with patch.object(vb, "cac_chung_tu", lambda dt: hoi.append(dt) or ds[dt]), patch.object(vb, "sua_mot", sua), \
			patch.object(vb.frappe, "log_error", lambda chu, tieu: log.append((tieu, chu)), create=True):
		kq = vb.execute()
	la("loại chứng từ", hoi, ["Purchase Order", "Purchase Receipt", "Supplier Quotation"])
	la("đã sửa", kq["da_sua"], {"Purchase Order": 1, "Purchase Receipt": 1})
	la("bỏ qua ghi log", log, [(vb.TIEU_DE_LOG, "Purchase Order B: tiền hàng đổi")])
	dung("không đụng hoá đơn mua", "Purchase Invoice" not in vb.LOAI)


@ca("Codex #553: chứng từ cũ có giảm giá trên tổng (10%) thì trừ số thuế SAU giảm: 647.280 ra 602.640, khớp dòng 1331 còn lại")
def _():
	dong = [dict(_d("t1", VAO, 49600.0, 602640.0), tax_amount_after_discount_amount=44640.0, base_tax_amount_after_discount_amount=44640.0),
		dict(_d("t2", RA, 49600.0, 647280.0), tax_amount_after_discount_amount=44640.0, base_tax_amount_after_discount_amount=44640.0)]
	cha = _cha(net_total=558000.0, grand_total=647280.0, base_grand_total=647280.0, total_taxes_and_charges=89280.0,
		base_total_taxes_and_charges=89280.0, taxes_and_charges_added=89280.0, base_taxes_and_charges_added=89280.0,
		rounded_total=647280.0, base_rounded_total=647280.0)
	kq, db, gc = _chay(cha, dong)
	moi = db.ghi[0][2]
	la("tổng, thuế theo số sau giảm", (moi["grand_total"], moi["total_taxes_and_charges"], moi["taxes_and_charges_added"]),
		(602640.0, 44640.0, 44640.0))
	la("tổng mới bằng cộng dồn dòng 1331 còn lại", moi["grand_total"], db.ghi[1][2]["total"])
	dung("ghi chú theo số sau giảm", "89.280 → 44.640" in gc[0])


@ca("Codex #553: lịch thanh toán đơn mua theo tổng mới (719.200 ra 669.600), chia theo tỷ lệ kỳ, giữ phần đã trả; đã trả vượt hoặc lịch không đủ 100% thì không ghi gì")
def _():
	dong = [_d("t1", VAO, 49600.0, 669600.0), _d("t2", RA, 49600.0, 719200.0)]
	kq, db, gc = _chay(_cha(), dong)
	ps = [g for g in db.ghi if g[0] == "Payment Schedule"]
	la("một kỳ 100%", ps, [("Payment Schedule", "ps1", {"payment_amount": 669600.0, "outstanding": 669600.0,
		"base_payment_amount": 669600.0, "base_outstanding": 669600.0}, False)])
	hai = [{"name": "a", "invoice_portion": 30.0, "paid_amount": 215760.0, "base_paid_amount": 215760.0, "discounted_amount": 0.0},
		{"name": "b", "invoice_portion": 70.0, "paid_amount": 0.0, "base_paid_amount": 0.0, "discounted_amount": 0.0}]
	hai[0]["paid_amount"] = hai[0]["base_paid_amount"] = 100000.0
	kq, db, gc = _chay(_cha(), dong, lich=hai)
	ps = {g[1]: g[2] for g in db.ghi if g[0] == "Payment Schedule"}
	la("hai kỳ: chia 30/70, giữ phần đã trả", (ps["a"]["payment_amount"], ps["a"]["outstanding"], ps["b"]["payment_amount"], ps["b"]["outstanding"]),
		(200880.0, 100880.0, 468720.0, 468720.0))
	hai[0]["paid_amount"] = hai[0]["base_paid_amount"] = 215760.0
	kq, db, gc = _chay(_cha(), dong, lich=hai)
	la("đã trả kỳ 1 vượt số mới: bỏ qua, không ghi gì", (kq["loi"], db.ghi, db.xoa), (["kỳ 1 đã trả nhiều hơn số mới"], [], []))
	kq, db, gc = _chay(_cha(), dong, lich=[{"name": "a", "invoice_portion": 60.0, "paid_amount": 0.0}])
	la("lịch không đủ 100%: bỏ qua", (kq["loi"], db.ghi), (["lịch trả không đủ 100%"], []))
	kq, db, gc = _chay(_cha(), dong, co=set(_cha()) - {"advance_paid"}, lich=[])
	dung("phiếu nhập không có lịch trả: vẫn sửa", kq.get("sau") and not [g for g in db.ghi if g[0] == "Payment Schedule"])
