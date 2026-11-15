# -*- coding: utf-8 -*-
"""v660 Kiểm bánh: bảng đã chốt giữ nguyên số lúc chốt, bán sau chốt ghi riêng
và máy tự trừ tiếp vào tồn đã chuyển sang ngày mai.

Loan Anh báo 15/11/2026: hôm qua (14/11) Epi 12cm bán hết, đã chốt sổ, nhưng
bảng hôm nay vẫn mang tồn 1 của hôm qua, và không mở lại được bảng hôm qua để
tra. Đọc site: chốt 20:25 chuyển 1 cái; sau đó nhịp đồng bộ vẫn viết lại bảng
14/11 tới 23:56 (Đã đặt, Phát sinh về 0). Anh Việt chọn (15/11): bánh bán sau
giờ chốt thì máy TỰ TRỪ vào tồn hôm sau.

Mọi ca chạy THẬT cap_nhat_don_khac, _dong_bo_mot_lan, chot_ngay, bang, dong_bo
qua bàn giả CuaGia (kế thừa lớp doctype thật).
"""

import frappe

from vagabond import kiem_banh
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la
from vagabond.khung.kiem_thu.thu_cot_huy_kiem_banh import BangGia, CuaGia, _tao_dong

MAY, TAY = kiem_banh.NGUON_MAY, kiem_banh.NGUON_TAY
EPI = "BAWC00019"


def _hai_bang(mai_dong=None, **nay):
	"""Bảng 14/11 CHƯA chốt (tồn 13/11: 1, bếp làm 2) và bảng 15/11."""
	d = dict(ma_hang=EPI, ten_banh="Bánh Ổ Epi, size 12cm", ton_d1=1, nsx_d1="2026-11-13", sx=2)
	d.update(nay)
	hom = BangGia(ngay="2026-11-14", dong=[_tao_dong(**d)])
	mai = BangGia(ngay="2026-11-15", dong=mai_dong or [])
	cua = CuaGia(**{"KB-2026-11-14": hom, "KB-2026-11-15": mai})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	return cua, hom, mai


def _khac(cua, dem):
	"""Chạy THẬT cap_nhat_don_khac với số bán kênh khác đếm lúc này là `dem`."""
	cu = kiem_banh._dem_don_khac
	kiem_banh._dem_don_khac = lambda ngay, theo_doi=None: (dict(dem), {})
	try:
		with cua:
			return kiem_banh.cap_nhat_don_khac("2026-11-14")
	finally:
		kiem_banh._dem_don_khac = cu


def _ton(mai):
	m = [d for d in mai.dong if d.ma_hang == EPI][0]
	return int(m.ton_cu or 0) + int(m.ton_d2 or 0) + int(m.ton_d1 or 0), m


@ca("v660 phép thuần: chuyen_ton trừ lô cũ trước và lùi một bậc tuổi; so_sau_chot không âm")
def _thuan():
	d = dict(ton_cu=1, ton_d2=1, ton_d1=1, nsx_d1="2026-11-13", sx=2)
	la("bán 0: cũ hơn 2, hai ngày 1, hôm qua 2", [x[1] for x in kiem_banh.chuyen_ton(d, "2026-11-14", 0)], [2, 1, 2])
	la("bán 3: ăn hết ba lô cũ", [x[1] for x in kiem_banh.chuyen_ton(d, "2026-11-14", 3)], [0, 0, 2])
	la("bán 4: ăn sang bếp làm", [x[1] for x in kiem_banh.chuyen_ton(d, "2026-11-14", 4)], [0, 0, 1])
	la("bán quá tồn: về 0, không âm", [x[1] for x in kiem_banh.chuyen_ton(d, "2026-11-14", 9)], [0, 0, 0])
	la("bán thêm 1 sau chốt", kiem_banh.so_sau_chot(3, 2), 1)
	la("đếm tụt dưới số lúc chốt thì 0", kiem_banh.so_sau_chot(0, 2), 0)


@ca("v660 đúng ca Epi 12cm 14/11: chốt còn 1 chuyển sang 15/11, sau chốt quầy bán nốt thì tồn 15/11 tự về 0, bảng 14/11 giữ nguyên số lúc chốt")
def _epi():
	cua, hom, mai = _hai_bang(don_khac=2)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	la("lúc chốt chuyển 1", _ton(mai)[0], 1)
	kq = _khac(cua, {EPI: 3})
	d = hom.dong[0]
	la("cột Kênh khác lúc chốt giữ 2", d.don_khac, 2)
	la("bán sau chốt ghi riêng 1", d.sau_chot_khac, 1)
	la("Bán được của 14/11 về 0 (web, quầy không bán lố)", d.co_the_ban, 0)
	tong, m = _ton(mai)
	la("tồn 15/11 tự về 0", tong, 0)
	la("ô vẫn là Tự chuyển", m.nguon_ton_d1, MAY)
	la("trả về có báo đã chốt và số mã đổi", (kq.get("da_chot"), kq.get("sau_chot")), (1, 1))
	with cua:
		b = kiem_banh.bang("2026-11-14")
	la("màn nhận cột Bán sau chốt", b["dong"][0]["ban_sau_chot"], 1)


@ca("v660 chạy lại: đếm lại cùng số ba lần không trừ thêm; đơn sau chốt bị huỷ thì tồn trả về đúng số lúc chốt, không vượt")
def _chay_lai():
	cua, hom, mai = _hai_bang(don_khac=2)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	for _ in range(3):
		_khac(cua, {EPI: 3})
	la("ba lần vẫn 0, không âm, không trừ dồn", _ton(mai)[0], 0)
	_khac(cua, {EPI: 2})
	la("huỷ đơn sau chốt: tồn về lại 1", _ton(mai)[0], 1)
	_khac(cua, {EPI: 0})
	la("số đếm tụt dưới lúc chốt: vẫn 1, không cộng thêm tồn", _ton(mai)[0], 1)
	la("các cột lúc chốt không đổi", (hom.dong[0].don_khac, hom.dong[0].sau_chot_khac), (2, 0))


@ca("v660 ô tồn hôm sau người đã đếm tay thì máy không đụng, chỉ ghi số máy bên cạnh; ngày mai đã chốt thì thôi")
def _dem_tay():
	cua, hom, mai = _hai_bang(don_khac=2)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
		kiem_banh.luu_o("2026-11-15", EPI, "ton_d1", 1)
	_khac(cua, {EPI: 3})
	tong, m = _ton(mai)
	la("số người đếm giữ nguyên 1", (m.ton_d1, m.nguon_ton_d1), (1, TAY))
	la("số máy bên cạnh là 0", m.may_chuyen_ton_d1, 0)
	cua2, hom2, mai2 = _hai_bang(don_khac=2)
	with cua2:
		kiem_banh.chot_ngay("2026-11-14")
	mai2.tinh_trang = "Da chot"
	_khac(cua2, {EPI: 3})
	la("ngày mai đã chốt: không sửa", _ton(mai2)[0], 1)
	la("bán sau chốt vẫn được ghi ở bảng hôm qua", hom2.dong[0].sau_chot_khac, 1)


def _dong_bo(cua, giao, tao=()):
	"""Chạy THẬT _dong_bo_mot_lan với đơn Pancake giả: giao = đơn giao ngày
	14/11, tao = mã các đơn tạo trong ngày."""
	from vagabond import giu_ton_web, pancake_nhip

	don = {"estimate_delivery_date": list(giao), "inserted_at": [o for o in giao if o["id"] in set(tao)]}
	cu = {
		"keo": kiem_banh._keo_don, "cfg": kiem_banh.cfg, "key": kiem_banh.key, "khac": kiem_banh._dem_don_khac,
		"khoa": giu_ton_web.khoa, "da_dem": giu_ton_web.da_dem, "hn": giu_ton_web.hom_nay,
		"ok": pancake_nhip.ghi_ok, "nghi": kiem_banh._con_nghi, "val": frappe.db.get_value,
		"set": getattr(frappe.db, "set_value", None), "commit": frappe.db.commit,
	}
	kiem_banh._keo_don = lambda c, k, kieu, dau, cuoi: don[kieu]
	kiem_banh.cfg = lambda: Doi({"pancake_shop_id": "1"})
	kiem_banh.key = lambda c, t: "k"
	kiem_banh._dem_don_khac = lambda ngay, theo_doi=None: ({EPI: cua.bang["KB-2026-11-14"].dong[0].don_khac or 0}, {})
	giu_ton_web.khoa = lambda: None
	giu_ton_web.da_dem = lambda ngay, ids: None
	giu_ton_web.hom_nay = lambda: "2026-11-14"
	pancake_nhip.ghi_ok = lambda: None
	kiem_banh._con_nghi = lambda ngay: 0
	frappe.db.get_value = lambda *a, **k: None
	frappe.db.set_value = lambda *a, **k: None
	frappe.db.commit = lambda: None
	try:
		with cua:
			return kiem_banh._dong_bo_mot_lan("2026-11-14")
	finally:
		kiem_banh._keo_don, kiem_banh.cfg, kiem_banh.key, kiem_banh._dem_don_khac = cu["keo"], cu["cfg"], cu["key"], cu["khac"]
		giu_ton_web.khoa, giu_ton_web.da_dem, giu_ton_web.hom_nay = cu["khoa"], cu["da_dem"], cu["hn"]
		pancake_nhip.ghi_ok, kiem_banh._con_nghi = cu["ok"], cu["nghi"]
		frappe.db.get_value, frappe.db.commit = cu["val"], cu["commit"]
		if cu["set"] is not None:
			frappe.db.set_value = cu["set"]


def _don(i, sl, tt=1):
	return {"id": i, "status": tt, "bill_full_name": "Khách %s" % i,
		"items": [{"quantity": sl, "variation_info": {"display_id": EPI, "name": "Epi 12"}}]}


@ca("v660 nhịp đồng bộ Pancake trên bảng ĐÃ CHỐT: không viết lại Đã đặt, Phát sinh (kể cả khi Pancake trả 0 đơn); đơn mới sau chốt vào Bán sau chốt và trừ tồn hôm sau")
def _dong_bo_da_chot():
	cua, hom, mai = _hai_bang(da_dat=1, phat_sinh=1)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	la("chốt: có 3, bán 2, chuyển 1", _ton(mai)[0], 1)
	# Đúng hiện tượng 14/11: sau chốt Pancake trả về không còn đơn nào của mã.
	_dong_bo(cua, [])
	d = hom.dong[0]
	la("Đã đặt, Phát sinh giữ số lúc chốt", (d.da_dat, d.phat_sinh), (1, 1))
	la("không có bán sau chốt, tồn hôm sau giữ 1", (int(d.get("sau_chot_pc") or 0), _ton(mai)[0]), (0, 1))
	# 21:00 khách đặt thêm 1 cái giao ngay trong ngày.
	_dong_bo(cua, [_don("a", 1), _don("b", 1), _don("c", 1)], tao=["b", "c"])
	la("cột lúc chốt vẫn nguyên", (d.da_dat, d.phat_sinh), (1, 1))
	la("bán sau chốt 1, Bán được về 0", (d.sau_chot_pc, d.co_the_ban), (1, 0))
	la("tồn 15/11 về 0", _ton(mai)[0], 0)


@ca("v660 đơn Mới (chờ chốt) lúc chốt, sau giờ chốt được xác nhận: rời cột Chờ chốt sang Bán sau chốt, Bán được không bị trừ hai lần")
def _cho_chot():
	cua, hom, mai = _hai_bang(da_dat=1, cho_chot=1)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	d = hom.dong[0]
	la("lúc chốt: có 3, đặt 1, chờ 1, bán được 1; chuyển 2", (d.co_the_ban, _ton(mai)[0]), (1, 2))
	_dong_bo(cua, [_don("a", 1), _don("m", 1)])
	la("chờ chốt về 0, bán sau chốt 1, Bán được vẫn 1", (d.cho_chot, d.sau_chot_pc, d.co_the_ban), (0, 1, 1))
	la("tồn hôm sau còn 1", _ton(mai)[0], 1)


@ca("v660 xem lại ngày cũ: dong_bo cho ngày đã qua chỉ đọc bảng, không kéo Pancake; hôm nay vẫn đồng bộ như cũ")
def _ngay_cu_chi_doc():
	goi = []
	cu = (kiem_banh._dong_bo_thu_lai, kiem_banh.bang, kiem_banh.getdate)
	kiem_banh._dong_bo_thu_lai = lambda ngay=None, chot=False: goi.append(("keo", str(ngay))) or {"keo": 1}
	kiem_banh.bang = lambda ngay=None: goi.append(("doc", str(ngay))) or {"doc": 1}
	import datetime
	that = cu[2]
	kiem_banh.getdate = lambda v=None: that(v) if v else datetime.date(2026, 11, 15)
	try:
		la("hôm qua: chỉ đọc", kiem_banh.dong_bo("2026-11-14"), {"doc": 1})
		la("hôm nay: kéo Pancake", kiem_banh.dong_bo("2026-11-15"), {"keo": 1})
		la("ngày mai: kéo Pancake", kiem_banh.dong_bo("2026-11-16"), {"keo": 1})
		la("không truyền ngày: kéo Pancake", kiem_banh.dong_bo(), {"keo": 1})
	finally:
		kiem_banh._dong_bo_thu_lai, kiem_banh.bang, kiem_banh.getdate = cu
	la("thứ tự gọi", goi, [("doc", "2026-11-14"), ("keo", "2026-11-15"), ("keo", "2026-11-16"), ("keo", "None")])


@ca("v660 tự chữa: lượt trước ghi được số bán sau chốt nhưng chưa sửa được tồn hôm sau (bảng hôm sau đang có người lưu) thì lượt sau, dù số không đổi, vẫn sửa; lượt không đổi gì thì không lưu lại bảng hôm sau")
def _tu_chua():
	cua, hom, mai = _hai_bang(don_khac=2)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	luu = []
	goc = mai.save

	def save(*a, **k):
		luu.append(1)
		if len(luu) == 1:
			raise frappe.ValidationError("bảng hôm sau đang có người lưu")
		return goc(*a, **k)
	mai.save = save
	try:
		_khac(cua, {EPI: 3})
		dung("lượt đầu phải nổ ra ngoài", False)
	except frappe.ValidationError:
		pass
	la("số bán sau chốt đã ghi ở bảng hôm qua", hom.dong[0].sau_chot_khac, 1)
	mai.dong[0].may_chuyen_ton_d1 = 1
	mai.dong[0].ton_d1 = 1
	_khac(cua, {EPI: 3})
	la("lượt sau số không đổi vẫn sửa tồn hôm sau về 0", _ton(mai)[0], 0)
	n = len(luu)
	_khac(cua, {EPI: 3})
	la("lượt thứ ba không còn gì đổi: không lưu lại bảng hôm sau", len(luu), n)


@ca("v660 hai bill sau chốt bấm cùng lúc: cap_nhat_don_khac giữ khoá bảng ngày đó TRƯỚC, rồi mới đếm bill và đọc lại bảng (đếm trước khoá thì lượt sau ghi đè số của lượt trước)")
def _khoa_truoc_khi_dem():
	cua, hom, mai = _hai_bang(don_khac=2)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	thu_tu = []
	cu_dem, cu_sql, cu_get = kiem_banh._dem_don_khac, frappe.db.sql, frappe.get_doc

	def dem(ngay, theo_doi=None):
		thu_tu.append("dem")
		return ({EPI: 3}, {})

	def sql(q, *a, **k):
		if "for update" in str(q) and "tabKiem Banh Ngay" in str(q):
			thu_tu.append("khoa")
			return [["KB-2026-11-14"]]
		return cu_sql(q, *a, **k)

	def get_doc(*a, **k):
		if a[:2] == ("Kiem Banh Ngay", "KB-2026-11-14"):
			thu_tu.append("doc")
		return cu_get(*a, **k)
	with cua:
		kiem_banh._dem_don_khac = dem
		goc_sql, goc_get = frappe.db.sql, frappe.get_doc
		cu_sql, cu_get = goc_sql, goc_get
		frappe.db.sql, frappe.get_doc = sql, get_doc
		try:
			kiem_banh.cap_nhat_don_khac("2026-11-14")
		finally:
			kiem_banh._dem_don_khac = cu_dem
			frappe.db.sql, frappe.get_doc = goc_sql, goc_get
	dung("có giữ khoá bảng", "khoa" in thu_tu)
	sau = thu_tu[thu_tu.index("khoa") + 1:]
	dung("đếm bill SAU khoá", "dem" in sau)
	dung("đọc lại bảng SAU khoá", "doc" in sau)
	la("số bán sau chốt ghi đúng", hom.dong[0].sau_chot_khac, 1)


def _voi_giu(dem):
	"""Thay phép đếm giữ chỗ lúc này bằng `dem` ({mã: số}) trong một khối with."""
	import unittest.mock as um
	return um.patch.object(kiem_banh, "_giu_cho_bay_gio", lambda ngay: (None if dem is None else dict(dem)))


@ca("v660 Codex #569 giữ chỗ nhận sau chốt: 3 bánh, giữ chỗ 1, chốt; khách tới nhận bánh đã giữ thì Bán được còn 2 (không trừ hai lần), tồn hôm sau cũng 2; cột Giữ chỗ lúc chốt giữ nguyên")
def _giu_cho_nhan_sau_chot():
	cua, hom, mai = _hai_bang(sx=2, giu_cho=1)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	d = hom.dong[0]
	la("lúc chốt Bán được 2", d.co_the_ban, 2)
	with _voi_giu({}):
		_khac(cua, {EPI: 1})
	la("bill sau chốt ghi 1", d.sau_chot_khac, 1)
	la("giữ chỗ đã nhận sau chốt 1", d.sau_chot_nha_giu, 1)
	la("cột Giữ chỗ lúc chốt giữ nguyên", d.giu_cho, 1)
	la("Bán được vẫn 2, không trừ hai lần", d.co_the_ban, 2)
	la("tồn hôm sau 2 (3 trừ bánh đã ra khỏi tủ)", _ton(mai)[0], 2)
	with _voi_giu({}):
		_khac(cua, {EPI: 2})
	la("thêm một khách vãng lai mua: Bán được còn 1", d.co_the_ban, 1)
	la("ô bù không vượt số đã giữ", d.sau_chot_nha_giu, 1)


@ca("v660 Codex #569 giữ chỗ: phiếu giữ chỗ bị huỷ sau chốt mà không ai mua thì bảng đã chốt giữ nguyên; huỷ rồi khách khác mua thì chỉ trừ một lần; đọc số giữ chỗ hỏng thì không đụng ô bù")
def _giu_cho_huy_sau_chot():
	cua, hom, mai = _hai_bang(sx=2, giu_cho=1)
	with cua:
		kiem_banh.chot_ngay("2026-11-14")
	d = hom.dong[0]
	with _voi_giu({}):
		_khac(cua, {EPI: 0})
	la("huỷ giữ chỗ, không ai mua: không bù", (d.get("sau_chot_nha_giu") or 0, d.co_the_ban), (0, 2))
	with _voi_giu({}):
		_khac(cua, {EPI: 1})
	la("khách khác mua: bù 1, Bán được vẫn 2", (d.sau_chot_nha_giu, d.co_the_ban), (1, 2))
	with _voi_giu(None):
		_khac(cua, {EPI: 1})
	la("đọc hỏng: giữ ô bù cũ", d.sau_chot_nha_giu, 1)
	with _voi_giu({EPI: 1}):
		_khac(cua, {EPI: 1})
	la("phiếu vẫn còn giữ mà có bill khác: không bù, Bán được 1", (d.sau_chot_nha_giu, d.co_the_ban), (0, 1))
	with _voi_giu(None):
		_khac(cua, {EPI: 1})
	la("đọc hỏng lần nữa: ô bù vẫn 0, không tự coi là đã nhả hết", (d.sau_chot_nha_giu, d.co_the_ban), (0, 1))
	la("phép thuần", [kiem_banh.nha_giu_sau_chot(2, 0, 1), kiem_banh.nha_giu_sau_chot(1, 3, 5), kiem_banh.nha_giu_sau_chot(0, 0, 4),
		kiem_banh.nha_giu_sau_chot(3, 1, 9)], [1, 0, 0, 2])


@ca("v660 Codex #569 bảng ngày đã qua chỉ xem ở máy chủ: sửa ô, thêm mã, xoá dòng, tắt bán web của ngày cũ đều bị chặn, kể cả bảng QUÊN CHỐT; bảng hôm nay và ngày mai không bị chặn")
def _ngay_cu_chi_xem():
	import unittest.mock as um
	la("phép thuần", [kiem_banh.ngay_da_qua("2026-11-14", "2026-11-15"), kiem_banh.ngay_da_qua("2026-11-15", "2026-11-15"),
		kiem_banh.ngay_da_qua("2026-11-16", "2026-11-15"), kiem_banh.ngay_da_qua(None, "2026-11-15")], [True, False, False, False])
	cua, hom, mai = _hai_bang()
	la("bảng 14/11 đang quên chốt", hom.tinh_trang != "Da chot", True)

	def chan(ten, ham):
		try:
			ham()
		except frappe.ValidationError as e:
			dung(ten + ": câu báo nói bảng đã qua chỉ xem", "chỉ xem" in str(e))
			return
		dung(ten + ": phải bị chặn", False)
	with cua, um.patch.object(kiem_banh, "getdate", lambda v=None: frappe.utils.getdate(v or "2026-11-15")):
		chan("sửa Bếp làm", lambda: kiem_banh.luu_o("2026-11-14", EPI, "sx", 5))
		chan("sửa Huỷ", lambda: kiem_banh.luu_o("2026-11-14", EPI, "huy", 1))
		chan("thêm mã", lambda: kiem_banh.them_dong("2026-11-14", "BAWC00056"))
		chan("xoá dòng", lambda: kiem_banh.xoa_dong("2026-11-14", EPI))
		chan("tắt bán web", lambda: kiem_banh.tat_ban_web_dat(EPI, 1, "2026-11-14"))
		la("bảng cũ không đổi", hom.dong[0].sx, 2)
		kiem_banh.chan_ngay_da_qua("2026-11-15")
		kiem_banh.chan_ngay_da_qua("2026-11-16")


@ca("v660 Codex #569 ba ô Refill cũ: dòng đã có đợt mà ô cũ mang số thì chặn lưu kèm chỉ chỗ sửa; dòng chưa có đợt thì ô cũ vẫn dùng được; ba ô cũ ẩn và chỉ đọc trên Desk")
def _o_refill_cu():
	import json
	import os
	from vagabond.vagabond.doctype.btp_banh_o import btp_banh_o as m

	co = '[{"id": "a", "so": 20, "tu": "2026-11-14", "den": "2026-11-20"}]'
	la("đã có đợt, ô cũ sửa thành 5", m.o_refill_cu_bi_dien([{"ma_hang": EPI, "ten_banh": "Epi", "refill_dot": co, "so_refill": 5}]), ["Epi"])
	la("đã có đợt, ô cũ chỉ có ngày", m.o_refill_cu_bi_dien([{"ma_hang": EPI, "refill_dot": co, "so_refill": 0, "refill_tu": "2026-11-21"}]), [EPI])
	la("đã có đợt, ô cũ sạch", m.o_refill_cu_bi_dien([{"ma_hang": EPI, "refill_dot": co, "so_refill": 0, "refill_tu": None, "refill_den": None}]), [])
	la("chưa có đợt thì ô cũ vẫn là nguồn", m.o_refill_cu_bi_dien([{"ma_hang": EPI, "refill_dot": "", "so_refill": 5, "refill_tu": "2026-11-21"}]), [])
	doc = Doi({"dong": [Doi({"as_dict": lambda: {"ma_hang": EPI, "ten_banh": "Epi", "refill_dot": co, "so_refill": 5}})]})
	doc.get = lambda k, mac=None: getattr(doc, k, mac)
	try:
		m.BTPBanhO.validate(doc)
		dung("phải chặn lưu", False)
	except frappe.ValidationError as e:
		dung("câu báo chỉ chỗ sửa", "Kiểm bánh" in str(e) and "Epi" in str(e))
	p = os.path.join(os.path.dirname(m.__file__), "..", "btp_banh_o_dong", "btp_banh_o_dong.json")
	f = {x["fieldname"]: x for x in json.load(open(p, encoding="utf-8"))["fields"]}
	la("ba ô cũ ẩn và chỉ đọc", [(f[k].get("hidden"), f[k].get("read_only")) for k in ("so_refill", "refill_tu", "refill_den")], [(1, 1)] * 3)
