# -*- coding: utf-8 -*-
"""v648 (anh Việt chọn cách 1, 11/11/2026): hoàn tất lệnh mà kho nguyên liệu
của bếp thiếu thì máy lập và ghi sổ luôn phiếu điều chuyển từ Kho tổng 307 sang
kho bếp đúng phần thiếu, ngay trước phiếu hoàn tất, cùng một yêu cầu.

Ca ở đây chốt phép tính thuần (tinh_lay_bu) và chuỗi của hoan_tat_phieu trên
kho giả: chỉ hỏi thì không ghi gì; đồng ý thì phiếu điều chuyển ghi TRƯỚC phiếu
hoàn tất; không có cờ thì như cũ. Ca ERPNext thật ở kiem_that/thu_tu_lam_cap_duoi_648.
"""
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import kho_san_xuat as ksx
from vagabond.khung.kiem_thu.nen import ca, dung, la

BEP = "Pastry - Nguyên liệu - TV"
BEP2 = "Baker - Nguyên liệu - TV"
TONG = ksx.KHO_GOC


def _d(ma, can, kho=BEP, ten=None):
	return dict(ma=ma, ten=ten or ma, dvt="Gram", kho=kho, can=can)


@ca("v648 lấy bù từ Kho tổng 307: chỉ lấy phần thiếu; kho tổng thiếu thì lấy phần có, báo phần còn thiếu; đủ thì không lấy")
def _():
	lay, con = ksx.tinh_lay_bu([_d("BOT", 100)], {("BOT", BEP): 30}, {"BOT": 500})
	la("lấy đúng 70", [(x["ma"], x["sl"], x["kho_bep_con"], x["kho_tong_con"]) for x in lay], [("BOT", 70.0, 30.0, 500.0)])
	la("không còn thiếu", con, [])
	lay, con = ksx.tinh_lay_bu([_d("BOT", 100)], {("BOT", BEP): 30}, {"BOT": 20})
	la("kho tổng còn 20: lấy 20", [x["sl"] for x in lay], [20.0])
	la("còn thiếu 50", [(x["ma"], x["thieu"]) for x in con], [("BOT", 50.0)])
	lay, con = ksx.tinh_lay_bu([_d("BOT", 100)], {("BOT", BEP): 100}, {"BOT": 500})
	la("đủ thì không lấy", (lay, con), ([], []))
	lay, con = ksx.tinh_lay_bu([_d("BOT", 100)], {}, {})
	la("kho tổng hết: không lấy, báo thiếu đủ 100", (lay, [x["thieu"] for x in con]), ([], [100.0]))


@ca("v648 lấy bù: gộp dòng cùng mã; hai kho bếp chia tồn kho tổng một lần; dòng xuất từ chính Kho tổng bỏ qua; gram lẻ làm tròn lên")
def _():
	lay, con = ksx.tinh_lay_bu([_d("BOT", 40), _d("BOT", 60)], {("BOT", BEP): 30}, {"BOT": 500})
	la("gộp 40 + 60, thiếu 70", [x["sl"] for x in lay], [70.0])
	lay, con = ksx.tinh_lay_bu([_d("BOT", 100), _d("BOT", 100, kho=BEP2)], {}, {"BOT": 150})
	la("hai bếp: 100 rồi 50", [(x["kho"], x["sl"]) for x in lay], [(BEP, 100.0), (BEP2, 50.0)])
	la("bếp sau còn thiếu 50", [(x["kho"], x["thieu"]) for x in con], [(BEP2, 50.0)])
	lay, con = ksx.tinh_lay_bu([_d("BOT", 100, kho=TONG)], {}, {"BOT": 0})
	la("lệnh xuất thẳng từ Kho tổng: không tự chuyển sang chính nó", (lay, con), ([], []))
	lay, con = ksx.tinh_lay_bu([_d("BOT", 10.0004)], {}, {"BOT": 50})
	la("10,0004 g lấy 10,001 để ghi sổ không hụt", [x["sl"] for x in lay], [10.001])


def _phieu():
	return {
		"doctype": "Stock Entry", "purpose": "Manufacture", "work_order": "WO-1", "company": "Vagabond",
		"fg_completed_qty": 2,
		"items": [
			{"item_code": "BOT", "item_name": "Bột mì", "s_warehouse": BEP, "qty": 0.1, "conversion_factor": 1000,
				"stock_uom": "Gram", "uom": "Kg"},
			{"item_code": "BO", "item_name": "Bơ", "s_warehouse": BEP, "qty": 50, "transfer_qty": 50, "stock_uom": "Gram"},
			{"item_code": "TP", "item_name": "Bánh", "t_warehouse": "Pastry - Thành phẩm - TV", "qty": 2, "is_finished_item": 1},
		],
	}


class _Co(dict):
	"""Giống frappe._dict thật: gán thuộc tính là gán khoá (doc.flags)."""
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


class _He:
	"""Kho giả: ghi lại thứ tự lập, ghi sổ phiếu và các ô ghi thẳng."""

	def __init__(self, ton):
		self.ton, self.nhat, self.set = ton, [], []

	def get_all(self, dt, filters=None, fields=None, **k):
		assert dt == "Bin", dt
		ma, kho = filters["item_code"][1], filters["warehouse"][1]
		return [NS(item_code=m, warehouse=w, actual_qty=q) for (m, w), q in self.ton.items() if m in ma and w in kho]

	def _doc(self, goc):
		he = self
		d = NS(**goc)
		d.flags = _Co()

		def append(f, row):
			d.__dict__.setdefault(f, []).append(row)

		def insert():
			d.name = "PDC-1" if d.purpose == "Material Transfer" else "SE-1"
			he.nhat.append(("insert", d.purpose, d.name))

		def submit():
			he.nhat.append(("submit", d.purpose, d.name, dict(d.flags)))
		d.append, d.insert, d.submit, d.get = append, insert, submit, (lambda k, m=None: getattr(d, k, m))
		return d

	def chay(self, **kw):
		from vagabond.khung.kiem_thu import nen  # noqa: F401
		db = NS(set_value=lambda dt, ten, ghi, update_modified=True: self.set.append((dt, ten, ghi)))
		with patch.object(ksx.frappe, "get_roles", lambda *a: ["Manufacturing User"], create=True), \
				patch.object(ksx, "_don_phieu_nhap_mo_coi", lambda ten: []), \
				patch.object(ksx.frappe, "get_all", self.get_all, create=True), \
				patch.object(ksx.frappe, "get_doc", lambda goc: self._doc(dict(goc)), create=True), \
				patch.object(ksx.frappe, "new_doc", lambda dt: self._doc({"doctype": dt}), create=True), \
				patch.object(ksx.frappe, "get_meta", lambda dt: NS(has_field=lambda f: True), create=True), \
				patch.object(ksx.frappe, "db", db, create=True):
			return ksx.hoan_tat_phieu(_phieu(), q=2, can=2, **kw)


@ca("v648 hoàn tất lấy bù, đúng chuỗi app: chỉ hỏi thì KHÔNG ghi gì; đồng ý thì phiếu điều chuyển Kho tổng 307 ghi sổ TRƯỚC phiếu hoàn tất")
def _():
	ton = {("BOT", BEP): 30, ("BO", BEP): 50, ("BOT", TONG): 1000}
	he = _He(ton)
	kq = he.chay(hoi_lay_bu=1)
	la("chỉ hỏi: liệt kê đúng 70 g bột (100 g theo Kg x 1000)", [(x["ma"], x["sl"]) for x in kq["hoi_lay_bu"]], [("BOT", 70.0)])
	la("chỉ hỏi: không lập, không ghi phiếu nào", he.nhat, [])

	he = _He(ton)
	kq = he.chay(lay_bu=1, lay_toi_da='{"BOT": 70}')
	la("thứ tự: điều chuyển rồi mới hoàn tất",
		[(x[0], x[1]) for x in he.nhat],
		[("insert", "Material Transfer"), ("submit", "Material Transfer"), ("insert", "Manufacture"), ("submit", "Manufacture")])
	la("cờ cho tin Zalo kho: bếp lấy cho lệnh WO-1", he.nhat[1][3].get("bep_lay_bu"), "WO-1")
	la("trả số phiếu điều chuyển", kq["phieu_bu"], "PDC-1")
	ghi = he.set[0][2]
	la("ghi bếp đã nhận đủ để không bị nhắc chưa nhận", (ghi["vgb_nhan_tt"], ghi["vgb_nhan_boi"]), ("Đã nhận đủ", ksx.frappe.session.user))


@ca("v648 hoàn tất lấy bù: đủ nguyên liệu thì không lập phiếu; không có cờ thì đi đường cũ, không đọc kho")
def _():
	he = _He({("BOT", BEP): 100, ("BO", BEP): 50})
	kq = he.chay(lay_bu=1, lay_toi_da="{}")
	la("đủ: chỉ phiếu hoàn tất", [x[1] for x in he.nhat], ["Manufacture", "Manufacture"])
	la("không có phiếu bù", kq["phieu_bu"], "")

	he = _He({})
	he.get_all = lambda *a, **k: (_ for _ in ()).throw(AssertionError("không được đọc kho khi không có cờ"))
	kq = he.chay()
	la("đường cũ", [x[1] for x in he.nhat], ["Manufacture", "Manufacture"])
	dung("không có ô hỏi", "hoi_lay_bu" not in kq)


@ca("v648 Codex #551 vòng 8: số đã duyệt là trần của lượt ghi; cộng theo mã; thiếu số duyệt thì không ghi; chịu chuỗi JSON")
def _():
	lay = [dict(ma="BOT", sl=40.0), dict(ma="BOT", sl=30.0), dict(ma="BO", sl=5.0)]
	dung("đủ trần", ksx.trong_han_lay(lay, {"BOT": 70, "BO": 5}))
	dung("cộng theo mã: 70 vượt 60", not ksx.trong_han_lay(lay, {"BOT": 60, "BO": 5}))
	dung("thiếu mã trong trần", not ksx.trong_han_lay(lay, {"BOT": 70}))
	dung("không có số duyệt thì không ghi", not ksx.trong_han_lay(lay, None) and not ksx.trong_han_lay(lay, {}) and not ksx.trong_han_lay(lay, ""))
	dung("chuỗi JSON như app gửi", ksx.trong_han_lay(lay, '{"BOT": 70, "BO": 5}'))
	dung("chuỗi hỏng thì không ghi", not ksx.trong_han_lay(lay, "{BOT"))
	dung("làm tròn 3 chữ số không chặn nhầm", ksx.trong_han_lay([dict(ma="BOT", sl=10.001)], {"BOT": 10.001}))


@ca("v648 Codex #551 vòng 8: kho bếp bị dùng bớt giữa lượt hỏi và lượt ghi thì máy chủ KHÔNG lấy quá số bếp đã duyệt, chỉ hỏi lại")
def _():
	# Lượt hỏi: bếp còn 30 g, thiếu 70 g; bếp duyệt 70. Trước lượt ghi, đơn
	# khác dùng hết 30 g: phần thiếu tính lại là 100 g.
	he = _He({("BOT", BEP): 0, ("BO", BEP): 50, ("BOT", TONG): 1000})
	kq = he.chay(lay_bu=1, lay_toi_da='{"BOT": 70}')
	la("hỏi lại đúng 100", [(x["ma"], x["sl"]) for x in kq["hoi_lay_bu"]], [("BOT", 100.0)])
	la("không lập, không ghi phiếu nào", he.nhat, [])
	he = _He({("BOT", BEP): 0, ("BO", BEP): 50, ("BOT", TONG): 1000})
	kq = he.chay(lay_bu=1)
	la("lượt ghi không mang số duyệt: không ghi", (he.nhat, [x["sl"] for x in kq["hoi_lay_bu"]]), ([], [100.0]))
	he = _He({("BOT", BEP): 0, ("BO", BEP): 50, ("BOT", TONG): 1000})
	kq = he.chay(lay_bu=1, lay_toi_da='{"BOT": 100}')
	la("bếp duyệt lại 100 thì lấy 100", [(x["ma"], x["sl"]) for x in kq["da_lay"]], [("BOT", 100.0)])
