# -*- coding: utf-8 -*-
"""v655 (anh Việt chọn phương án B, 13/11/2026): bỏ việc máy tự lấy bù từ Kho
tổng 307 khi hoàn tất lệnh (v648 cách 1). Uyên thu mua báo năm phiếu
PDC-2026-00744 tới 00748 trừ Kho tổng từng 14,245 ml, 22,792 ml Rượu Rhum vàng
trong khi kho giao nguyên chai, nên tồn ERP lệch tồn thật, lẻ số không đếm được.

Từ nay: kho bếp thiếu thì báo thiếu, bếp gửi phiếu xin (xin_kho_tong) đúng phần
thiếu làm tròn lên số nguyên; kho tổng giao bao nhiêu ghi bấy nhiêu ở màn Lập
phiếu điều chuyển (phần vượt số xin thành dòng không nối phiếu), ghi sổ xong
hàng nằm ngay ở kho bếp.

Ca ở đây chốt phép thuần và chuỗi của hoan_tat_phieu, xin_kho_tong trên kho giả.
"""
import json
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import kho_san_xuat as ksx
from vagabond import lo_hang, xuat_kho
from vagabond.khung.kiem_thu.nen import ca, dung, la

BEP = "Pastry - Nguyên liệu - TV"
BEP2 = "Baker - Nguyên liệu - TV"
TONG = ksx.KHO_GOC


def _d(ma, can, kho=BEP, ten=None, **k):
	return dict(ma=ma, ten=ten or ma, dvt="ML", kho=kho, can=can, **k)


@ca("v655 số xin kho tổng: làm tròn LÊN số nguyên của đơn vị tồn kho, tối thiểu 1; không thiếu thì 0")
def _():
	la("14,245 ml xin 15", ksx.so_xin(14.245), 15)
	la("22,792 ml xin 23", ksx.so_xin(22.792), 23)
	la("đúng số nguyên giữ nguyên", ksx.so_xin(700), 700)
	la("0,2 g xin 1", ksx.so_xin(0.2), 1)
	la("không thiếu", (ksx.so_xin(0), ksx.so_xin(-3), ksx.so_xin(0.0001)), (0, 0, 0))


@ca("v655 tinh_xin_kho_tong: thiếu = cần trừ tồn kho bếp; gộp cùng mã cùng kho; hai kho bếp tách riêng; bỏ dòng xuất từ Kho tổng; đủ thì không xin")
def _():
	ra = ksx.tinh_xin_kho_tong([_d("RHUM", 14.245)], {})
	la("Rhum thiếu 14,245 xin 15", [(x["ma"], x["kho"], x["thieu"], x["xin"]) for x in ra], [("RHUM", BEP, 14.245, 15)])
	ra = ksx.tinh_xin_kho_tong([_d("BOT", 40), _d("BOT", 60)], {("BOT", BEP): 30.5})
	la("gộp 40 + 60 trừ 30,5 còn 69,5 xin 70", [(x["can"], x["co"], x["thieu"], x["xin"]) for x in ra], [(100.0, 30.5, 69.5, 70)])
	ra = ksx.tinh_xin_kho_tong([_d("BOT", 10), _d("BOT", 10, kho=BEP2)], {("BOT", BEP): 10})
	la("hai bếp: Pastry đủ, Baker xin 10", [(x["kho"], x["xin"]) for x in ra], [(BEP2, 10)])
	la("dòng xuất thẳng từ Kho tổng: không tự xin chính nó", ksx.tinh_xin_kho_tong([_d("BOT", 10, kho=TONG)], {}), [])
	la("đủ thì không xin", ksx.tinh_xin_kho_tong([_d("BOT", 10)], {("BOT", BEP): 10}), [])
	la("số âm của app bị chặn", ksx.tinh_xin_kho_tong([_d("BOT", -5)], {}), [])


@ca("v655 Codex #562 P1 tinh_xin_kho_tong: bỏ qua số thiếu app gửi kèm; thiếu = cần - tồn kho bếp - hàng thay thế máy chủ tính")
def _():
	ra = ksx.tinh_xin_kho_tong([_d("BOT", 100, thieu=20)], {("BOT", BEP): 10})
	la("app nói thiếu 20 lúc xem, tồn nay còn 10: xin 90", [x["xin"] for x in ra], [90])
	la("tồn nay đủ 100: không xin", ksx.tinh_xin_kho_tong([_d("BOT", 100, thieu=20)], {("BOT", BEP): 100}), [])
	ra = ksx.tinh_xin_kho_tong([_d("BOT", 100)], {("BOT", BEP): 30}, {("BOT", BEP): 50})
	la("hàng thay thế bù 50: xin 20", [(x["thay"], x["thieu"], x["xin"]) for x in ra], [(50.0, 20.0, 20)])
	la("dòng hỏi hàng thay: thiếu theo tồn lúc gửi", ksx.dong_bu_thay([_d("BOT", 40), _d("BOT", 60), _d("CA", 5)], {("BOT", BEP): 30, ("CA", BEP): 9}),
		[dict(ma="BOT", kho=BEP, can=100.0, thieu=70.0), dict(ma="CA", kho=BEP, can=5.0, thieu=0.0)])


@ca("v655 tru_phieu_dang_cho: bấm hai lần hay hai lệnh cùng thiếu một món không sinh hai phiếu cho cùng phần thiếu")
def _():
	xin = ksx.tinh_xin_kho_tong([_d("RHUM", 23), _d("BOT", 70)], {})
	con, da = ksx.tru_phieu_dang_cho(xin, {("RHUM", BEP): 23})
	la("Rhum đã có phiếu chờ đủ 23: không xin", [x["ma"] for x in da], ["RHUM"])
	la("Bột vẫn xin 70", [(x["ma"], x["xin"]) for x in con], [("BOT", 70)])
	con, da = ksx.tru_phieu_dang_cho(xin, {("RHUM", BEP): 10})
	la("phiếu chờ 10: chỉ xin thêm 13", [(x["ma"], x["xin"]) for x in con if x["ma"] == "RHUM"], [("RHUM", 13)])
	con, da = ksx.tru_phieu_dang_cho(xin, {("RHUM", BEP2): 50})
	la("phiếu chờ của bếp khác không tính", [(x["ma"], x["xin"]) for x in con if x["ma"] == "RHUM"], [("RHUM", 23)])


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
		self.ton, self.nhat, self.set, self.diem = ton, [], [], []

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

		def insert(**k):
			d.name = {"Material Transfer": "PDC-1", "Material Request": "YCDC-1"}.get(
				getattr(d, "purpose", None) or d.doctype, "SE-1")
			he.nhat.append(("insert", getattr(d, "purpose", None) or d.doctype, d.name))

		def submit():
			he.nhat.append(("submit", getattr(d, "purpose", None) or d.doctype, d.name, dict(d.flags)))
		d.append, d.insert, d.submit, d.get = append, insert, submit, (lambda k, m=None: getattr(d, k, m))
		return d

	def chay(self, **kw):
		db = NS(set_value=lambda dt, ten, ghi, update_modified=True: self.set.append((dt, ten, ghi)),
			savepoint=lambda ten: self.diem.append(("diem", ten)), rollback=lambda save_point=None: self.diem.append(("lui", save_point)))
		with patch.object(ksx.frappe, "get_roles", lambda *a: ["Manufacturing User"], create=True), \
				patch.object(ksx, "_don_phieu_nhap_mo_coi", lambda ten: []), \
				patch.object(ksx.frappe, "get_all", self.get_all, create=True), \
				patch.object(ksx.frappe, "get_doc", lambda goc: self._doc(dict(goc)), create=True), \
				patch.object(ksx.frappe, "new_doc", lambda dt: self._doc({"doctype": dt}), create=True), \
				patch.object(ksx.frappe, "get_meta", lambda dt: NS(has_field=lambda f: True), create=True), \
				patch.object(ksx.frappe, "db", db, create=True):
			return ksx.hoan_tat_phieu(_phieu(), q=2, can=2, **kw)


@ca("v655 hoàn tất lệnh KHÔNG còn lấy bù Kho tổng 307: app cũ gửi cờ lấy bù thì bỏ qua, không đọc kho, không lập phiếu điều chuyển")
def _():
	for kw in ({}, {"hoi_lay_bu": 1}, {"lay_bu": 1, "lay_toi_da": '{"BOT": 70}'}):
		he = _He({})
		he.get_all = lambda *a, **k: (_ for _ in ()).throw(AssertionError("không được đọc kho"))
		kq = he.chay(**kw)
		la("chỉ phiếu hoàn tất (%s)" % (sorted(kw) or "không cờ"), [x[1] for x in he.nhat], ["Manufacture", "Manufacture"])
		dung("không hỏi lấy bù", "hoi_lay_bu" not in kq and "phieu_bu" not in kq)
		la("không ghi ô nhận nào", he.set, [])


@ca("v655 câu thiếu nguyên liệu khi hoàn tất chỉ đúng việc mới: bấm Gửi phiếu xin kho tổng rồi Hoàn tất lại")
def _():
	cau = ksx.cau_thieu_nvl("WO-1", [{"ten": "Rượu Rhum vàng, ISC", "sl": 22.792, "dvt": "ML", "ghi": "kho đang có 0"}], BEP)
	dung("việc phải làm mới", "Gửi phiếu xin kho tổng" in cau and "Hoàn tất lại" in cau)
	dung("không còn trỏ màn Kế hoạch", "Xin chuyển nguyên liệu" not in cau)


class _Xin:
	"""Hệ giả cho xin_kho_tong: khoá có tên, tồn Bin, phiếu đang chờ, lập phiếu."""

	def __init__(self, ton, cho=(), khoa=1, kho_ok=True, thay=None, lo=()):
		# cho: (mã, kho, số xin, số đã giao[, ngày lập]); thay: {mã: [mã thay]}; lo: mã theo lô.
		self.ton, self.cho, self.khoa, self.kho_ok = ton, list(cho), khoa, kho_ok
		self.thay, self.lo = thay or {}, set(lo)
		self.cau, self.phieu, self.commit = [], [], 0
		self.truoc_doc = None

	def sql(self, q, args=None, as_dict=False):
		self.cau.append(q.split()[0] + " " + q.split()[1])
		if "get_lock" in q:
			if self.khoa and self.truoc_doc:
				self.truoc_doc(self)
			return [[self.khoa]]
		if "release_lock" in q:
			return [[1]]
		if "Material Request Item" in q:
			assert "for update" in q, "đọc phiếu chờ phải khoá"
			hom_nay = "2026-11-13"
			ra = []
			for r in self.cho:
				m, w, s, o = r[:4]
				ngay = r[4] if len(r) > 4 else hom_nay
				if "transaction_date >=" in q and ngay < str((args or {}).get("tu")):
					continue
				ra.append(NS(item_code=m, warehouse=w, stock_qty=s, ordered_qty=o))
			return ra
		raise AssertionError(q)

	def chay(self, dong, **kw):
		he = self
		nhat = []

		def new_doc(dt):
			d = NS(doctype=dt, items=[], flags=_Co())
			d.append = lambda f, row: d.items.append(row)

			def insert(**k):
				d.name = "YCDC-%d" % (len(he.phieu) + 1)
				nhat.append(("insert", d.name))

			def submit():
				nhat.append(("submit", d.name))
				he.phieu.append(d)
			d.insert, d.submit = insert, submit
			return d
		db = NS(sql=self.sql, commit=lambda: setattr(self, "commit", self.commit + 1),
			exists=lambda dt, ten: self.kho_ok,
			get_value=lambda dt, f, cot: self.ton.get((f["item_code"], f["warehouse"]), 0))
		bins = lambda dt, filters=None, **k: [NS(item_code=m, warehouse=w, actual_qty=q) for (m, w), q in self.ton.items()]
		with patch.object(ksx.frappe, "get_roles", lambda *a: ["Manufacturing User"], create=True), \
				patch.object(ksx.frappe, "db", db, create=True), \
				patch.object(ksx.frappe, "get_all", bins, create=True), \
				patch.object(ksx.frappe, "get_cached_value", lambda dt, ma, f, as_dict=False: {"item_name": "Tên " + ma, "stock_uom": "ML"}, create=True), \
				patch.object(ksx.frappe, "new_doc", new_doc, create=True), \
				patch.object(ksx.frappe, "get_meta", lambda dt: NS(has_field=lambda f: False), create=True), \
				patch.object(lo_hang, "_theo_lo", lambda ma: 1 if ma in he.lo else 0), \
				patch.object(lo_hang, "_cac_ma_thay_the", lambda ma: list(he.thay.get(ma) or [])), \
				patch("frappe.utils.nowdate", lambda: "2026-11-13", create=True):
			kq = ksx.xin_kho_tong(json.dumps(dong), **kw)
		return kq, nhat


@ca("v655 xin_kho_tong đúng chuỗi app: máy chủ tự đọc tồn, xin số nguyên đúng phần thiếu, mỗi kho bếp MỘT phiếu từ Kho tổng 307, gửi luôn để Zalo báo kho")
def _():
	he = _Xin({("RHUM", BEP2): 0, ("BOT", BEP2): 30, ("BOT", BEP): 0})
	kq, nhat = he.chay([{"ma": "RHUM", "kho": BEP2, "can": 22.792}, {"ma": "BOT", "kho": BEP2, "can": 100},
		{"ma": "BOT", "kho": BEP, "can": 5}], ten_lenh="LSX-1")
	la("hai kho bếp hai phiếu, lập rồi gửi", nhat, [("insert", "YCDC-1"), ("submit", "YCDC-1"), ("insert", "YCDC-2"), ("submit", "YCDC-2")])
	p = {x.set_warehouse: x for x in he.phieu}
	la("phiếu Baker: từ Kho tổng, Rhum 23, Bột 70", (p[BEP2].set_from_warehouse, p[BEP2].material_request_type,
		[(i["item_code"], i["qty"], i["from_warehouse"], i["warehouse"]) for i in p[BEP2].items]),
		(TONG, "Material Transfer", [("RHUM", 23, TONG, BEP2), ("BOT", 70, TONG, BEP2)]))
	la("phiếu Pastry: Bột 5", [(i["item_code"], i["qty"]) for i in p[BEP].items], [("BOT", 5)])
	dung("câu báo nói số phiếu và việc làm tiếp", "YCDC-1" in kq["ghi_chu"] and "Hoàn tất lại" in kq["ghi_chu"])
	la("khoá trước khi đọc, nhả sau", [he.cau[0], he.cau[-1]], ["select get_lock(%s,", "select release_lock(%s)"])


@ca("v655 xin_kho_tong: đã có phiếu xin đang chờ đủ số thì không lập phiếu mới; kho bếp đã đủ thì không xin; kho không phải kho bếp thì chặn")
def _():
	he = _Xin({}, cho=[("RHUM", BEP2, 23, 0)])
	kq, nhat = he.chay([{"ma": "RHUM", "kho": BEP2, "can": 22.792}])
	la("không lập phiếu", (nhat, kq["ok"]), ([], 0))
	dung("báo đã có phiếu chờ", "đang chờ kho giao" in kq["ghi_chu"])
	he = _Xin({("RHUM", BEP2): 30})
	kq, nhat = he.chay([{"ma": "RHUM", "kho": BEP2, "can": 22.792}])
	la("đủ: không lập", (nhat, kq["ok"]), ([], 0))
	he = _Xin({}, kho_ok=True)
	try:
		he.chay([{"ma": "RHUM", "kho": "Kho D1 - TV", "can": 5}])
		dung("phải chặn kho không phải kho bếp", False)
	except Exception as e:
		dung("chặn kho cửa hàng", "không phải kho bếp" in str(e))
	he = _Xin({}, khoa=0)
	try:
		he.chay([{"ma": "RHUM", "kho": BEP2, "can": 5}])
		dung("không lấy được khoá thì phải dừng", False)
	except Exception as e:
		dung("báo đang có người gửi", "Đang có người gửi" in str(e))


@ca("v655 Codex #562 P1 xin_kho_tong: tồn kho bếp đổi giữa lúc xem hộp và lúc bấm Gửi: máy chủ xin theo tồn LÚC GỬI, không theo số app gửi kèm")
def _():
	# Lúc xem: cần 100, tồn 80, app (bản cũ trong bộ đệm) gửi kèm thiếu 20.
	he = _Xin({("BOT", BEP): 80})
	he.truoc_doc = lambda h: h.ton.update({("BOT", BEP): 10})  # đơn khác vừa dùng 70
	kq, nhat = he.chay([{"ma": "BOT", "kho": BEP, "can": 100, "thieu": 20}])
	la("tồn còn 10: xin 90, không xin 20", [(i["item_code"], i["qty"]) for i in he.phieu[0].items], [("BOT", 90)])
	he = _Xin({("BOT", BEP): 80})
	he.truoc_doc = lambda h: h.ton.update({("BOT", BEP): 100})  # kho vừa giao thêm
	kq, nhat = he.chay([{"ma": "BOT", "kho": BEP, "can": 100, "thieu": 20}])
	la("tồn đã đủ: không lập phiếu", (nhat, kq["ok"]), ([], 0))


@ca("v655 Codex #562 P1 xin_kho_tong: hàng thay thế đã khai cùng kho bù trước, máy chủ tự tính lúc gửi; hàng thay cũng là nguyên liệu nhóm dùng thì trừ phần đó trước")
def _():
	he = _Xin({("CACAO", BEP): 0.1, ("CACAO70", BEP): 0.2}, thay={"CACAO": ["CACAO70"]})
	kq, nhat = he.chay([{"ma": "CACAO", "kho": BEP, "can": 0.5}])
	la("thiếu 0,4, hàng thay bù 0,2: xin 1 (làm tròn lên của 0,2)", [(i["item_code"], i["qty"]) for i in he.phieu[0].items], [("CACAO", 1)])
	dung("dòng xin ghi phần hàng thay", kq["xin"][0]["thay"] == 0.2 and kq["xin"][0]["thieu"] == 0.2)
	he = _Xin({("BOT", BEP): 30, ("BOT2", BEP): 50}, thay={"BOT": ["BOT2"]})
	kq, nhat = he.chay([{"ma": "BOT", "kho": BEP, "can": 100}, {"ma": "BOT2", "kho": BEP, "can": 50}])
	la("Bột 2 nhóm dùng hết 50: không bù được, xin đủ 70", [(i["item_code"], i["qty"]) for i in he.phieu[0].items], [("BOT", 70)])
	he = _Xin({("BOT", BEP): 30, ("BOT2", BEP): 200}, thay={"BOT": ["BOT2"]})
	kq, nhat = he.chay([{"ma": "BOT", "kho": BEP, "can": 100}])
	la("hàng thay đủ: không lập phiếu", (nhat, kq["ok"]), ([], 0))


@ca("v655 Codex #562 P2 xin_kho_tong: phiếu xin lập từ 10/11 kho chưa giao vẫn được trừ ngày 13/11, bấm lại không sinh phiếu thứ hai")
def _():
	he = _Xin({}, cho=[("BOT", BEP, 100, 0, "2026-11-10")])
	kq, nhat = he.chay([{"ma": "BOT", "kho": BEP, "can": 100}])
	la("không lập phiếu mới", (nhat, kq["ok"]), ([], 0))
	dung("báo đã có phiếu chờ", "đang chờ kho giao" in kq["ghi_chu"])
	he = _Xin({}, cho=[("BOT", BEP, 100, 60, "2026-10-01")])
	kq, nhat = he.chay([{"ma": "BOT", "kho": BEP, "can": 100}])
	la("phiếu cũ đã giao 60, còn chờ 40: chỉ xin thêm 60", [(i["item_code"], i["qty"]) for i in he.phieu[0].items], [("BOT", 60)])


@ca("v655 kho tổng giao theo phiếu xin: phần trong số xin nối đúng dòng phiếu, phần vượt (nguyên chai) thành dòng riêng không nối")
def _():
	yc = [{"ten": "mri-1", "ma": "RHUM", "con": 23}, {"ten": "mri-2", "ma": "BOT", "con": 70}]
	ra = xuat_kho.chia_theo_yeu_cau([{"ma": "RHUM", "sl": 700}, {"ma": "BOT", "sl": 50}], yc)
	la("Rhum 23 nối, 677 không nối; Bột giao thiếu 50 nối hết",
		[(x["ma"], x["sl"], x["mr_item"]) for x in ra], [("RHUM", 23, "mri-1"), ("RHUM", 677, ""), ("BOT", 50, "mri-2")])
	ra = xuat_kho.chia_theo_yeu_cau([{"ma": "MOI", "sl": 3}], yc)
	la("món ngoài phiếu: không nối", [(x["ma"], x["sl"], x["mr_item"]) for x in ra], [("MOI", 3, "")])
	ra = xuat_kho.chia_theo_yeu_cau([{"ma": "RHUM", "sl": 10}, {"ma": "RHUM", "sl": 20}], yc)
	la("hai dòng cùng mã: chia dần phần còn chờ", [(x["sl"], x["mr_item"]) for x in ra], [(10, "mri-1"), (13, "mri-1"), (7, "")])
	la("không theo phiếu: mọi dòng không nối", [x["mr_item"] for x in xuat_kho.chia_theo_yeu_cau([{"ma": "A", "sl": 1}], [])], [""])


@ca("v655 chọn phiếu yêu cầu ở Xuất điều chuyển: dòng hiện TỒN THẬT của kho xuất (trước hiện số xin ở chỗ chữ tồn), số điền sẵn vẫn là số còn chờ")
def _():
	mr = NS(name="YCDC-1", set_from_warehouse=TONG, set_warehouse=BEP2, items=[
		NS(item_code="RHUM", item_name="Rượu Rhum vàng", uom="ML", qty=23, ordered_qty=0, warehouse=BEP2),
		NS(item_code="BOT", item_name="Bột", uom="Gram", qty=70, ordered_qty=70, warehouse=BEP2)])
	loc = []

	def get_all(dt, filters=None, **k):
		loc.append((dt, filters))
		return [NS(item_code="RHUM", actual_qty=1400)]
	with patch.object(xuat_kho.frappe, "get_roles", lambda *a: ["Stock User", "Stock Manager"], create=True), \
			patch.object(xuat_kho.frappe, "get_doc", lambda dt, ten: mr, create=True), \
			patch.object(xuat_kho.frappe, "get_all", get_all, create=True):
		ra = xuat_kho.dong_cua_yeu_cau("YCDC-1")
	la("dòng còn chờ, tồn thật", [(d["ma"], d["sl"], d["ton"]) for d in ra["dong"]], [("RHUM", 23.0, 1400.0)])
	la("đọc tồn ở kho xuất", loc[0][1]["warehouse"], TONG)
	src = open(xuat_kho.__file__.replace("xuat_kho.py", "public/js/bep/03-kho-chung-tu.js"), encoding="utf-8").read()
	dung("app dùng tồn thật", "ton: d.ton != null ? d.ton : d.sl" in src)
