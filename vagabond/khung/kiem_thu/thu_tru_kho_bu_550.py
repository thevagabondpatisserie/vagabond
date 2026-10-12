# -*- coding: utf-8 -*-
"""v550: trừ kho từng món và trừ bù khi hàng về (anh Việt chốt 01/10/2026).

Ca thật lấy từ District 1 ngày 01/10/2026: HDB-26-10-00033 bán 10:10, phiếu
điều chuyển PDC-2026-00329 từ NVHTN nhập 14:09, ghi sổ 18:40, nên v542 đánh
dấu cả tờ "Chưa trừ kho". HDB-26-10-00021 có Biscotti còn 12 cái mà vẫn không
trừ vì một món khác thiếu.

Tầng này chạy THẬT các hàm của tru_kho_bu (tru_bu, _lap_cac_phieu, các hook)
và ban_truoc_ghi_so của hach_toan_kho, thay phần chạm cơ sở dữ liệu bằng bản
giả ghi lại từng lời gọi. Sổ cái, sổ kho, lô và quyền trên site nằm ở bench:
vagabond/khung/kiem_that/thu_tru_kho_bu_550.py.
"""
import io
import os
import subprocess
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import tru_kho_bu as tb
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
KHO = "Kho D1 - TV"


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v

	def set(self, k, v):
		self[k] = v


def _doc(p):
	return io.open(os.path.join(GOC, p), encoding="utf-8").read()


# ------------------------------------------------------------ phần thuần

@ca("v550 chip trạng thái kho: một khoá cho mọi màn, còn thiếu xét trước đã trừ bù")
def _tt():
	tt = tb.trang_thai_kho
	la("nháp không có chip", tt({"docstatus": 0, "vgb_tru_kho_ban": 1, "update_stock": 1}), "")
	la("đã trừ kho ngay lúc ghi sổ", tt({"docstatus": 1, "vgb_tru_kho_ban": 1, "update_stock": 1}), "da_tru")
	la("tờ chỉ có đồ uống (không trừ kho, không thiếu)", tt({"docstatus": 1, "vgb_tru_kho_ban": 1, "update_stock": 0}), "")
	la("chưa trừ", tt({"docstatus": 1, "vgb_tru_kho_ban": 1, "vgb_chua_tru_kho": 1}), "chua_tru")
	la("đã trừ một phần", tt({"docstatus": 1, "vgb_chua_tru_kho": 1, "vgb_tru_bu": "Một phần"}), "mot_phan")
	la("gỡ tay vẫn là chưa trừ", tt({"docstatus": 1, "vgb_chua_tru_kho": 1, "vgb_tru_bu": "Gỡ tay"}), "chua_tru")
	la("đã trừ bù đủ", tt({"docstatus": 1, "vgb_chua_tru_kho": 0, "vgb_tru_bu": "Đủ"}), "da_tru_bu")
	la("tờ huỷ không có chip", tt({"docstatus": 2, "vgb_chua_tru_kho": 1}), "")
	# Đột biến M2 (xét Đủ trước) chỉ lộ ở tổ hợp này: còn thiếu là phải hiện
	# chưa trừ, kể cả khi ô Trừ bù còn giữ chữ Đủ của lượt cũ.
	la("còn thiếu thì không bao giờ hiện đã trừ bù", tt({"docstatus": 1, "vgb_chua_tru_kho": 1, "vgb_tru_bu": "Đủ"}), "chua_tru")
	la("tờ hoá đơn trộn phiếu giao (F6) vẫn hiện chưa trừ", tt({"docstatus": 1, "vgb_tru_kho_ban": 0, "vgb_chua_tru_kho": 1}), "chua_tru")
	ds = tb.gan_trang_thai([{"docstatus": 1, "vgb_chua_tru_kho": 1}, {"docstatus": 1, "vgb_tru_bu": "Đủ"}])
	la("gắn khoá cho danh sách", [r["tt_kho"] for r in ds], ["chua_tru", "da_tru_bu"])


@ca("v550 kế hoạch trừ: không bao giờ trừ quá tồn, tồn âm coi như 0, món đủ thì không còn thiếu")
def _ke_hoach():
	can = {("A", KHO): 2, ("B", KHO): 1, ("C", KHO): 3}
	thieu = tb.con_thieu(can, {("C", KHO): 3})
	la("C đã trừ đủ, chỉ còn A và B", thieu, {("A", KHO): 2.0, ("B", KHO): 1.0})
	lay = tb.ke_hoach(thieu, {("A", KHO): 12, ("B", KHO): -4})
	la("A lấy 2, B tồn âm không lấy", lay, {("A", KHO): 2.0})
	la("tồn ít hơn cần thì lấy bằng tồn", tb.ke_hoach({("A", KHO): 5}, {("A", KHO): 1.5}), {("A", KHO): 1.5})
	la("sai số nhỏ không sinh dòng", tb.con_thieu({("A", KHO): 1}, {("A", KHO): 0.9999999}), {})


@ca("v550 ô Trừ bù kho: chưa có phiếu thì trống, còn thiếu là Một phần, hết thiếu là Đủ")
def _gia_tri():
	la("chưa phiếu", tb.gia_tri_bu(False, {("A", KHO): 1}), "")
	la("một phần", tb.gia_tri_bu(True, {("A", KHO): 1}), "Một phần")
	la("đủ", tb.gia_tri_bu(True, {}), "Đủ")


@ca("v550 nhãn món và nhãn tờ trên màn Hoá đơn chưa trừ kho")
def _nhan():
	la("đã trừ", tb.nhan_dong(2, 2, 0), "da_tru")
	la("đủ để trừ", tb.nhan_dong(2, 0, 2), "du")
	la("một phần", tb.nhan_dong(2, 0, 1), "mot_phan")
	la("kho chưa có", tb.nhan_dong(2, 0, 0), "het")
	la("tồn âm là chưa có", tb.nhan_dong(1, 0, -3), "het")
	la("tờ kho đủ", tb.nhan_hoa_don(["da_tru", "du"]), "kho_du")
	la("tờ kho đủ một phần", tb.nhan_hoa_don(["het", "du"]), "kho_mot_phan")
	la("tờ kho chưa có", tb.nhan_hoa_don(["da_tru", "het"]), "kho_het")
	la("tờ không còn thiếu", tb.nhan_hoa_don(["da_tru"]), "")


@ca("v550 chip chặng: Gỡ tay và Kho ... chỉ đếm tờ còn chờ, Đã trừ bù không lẫn vào Chưa trừ kho")
def _chang():
	ds = [{"tt_kho": "chua_tru", "kho_nay": "kho_du"}, {"tt_kho": "mot_phan", "kho_nay": "kho_het"},
		{"tt_kho": "chua_tru", "kho_nay": "kho_het", "vgb_tru_bu": "Gỡ tay"}, {"tt_kho": "da_tru_bu", "vgb_tru_bu": "Đủ"}]
	la("đếm", tb.dem_chang(ds), {"": 4, "cho": 3, "kho_du": 1, "kho_mot_phan": 0, "kho_het": 2,
		"mot_phan": 1, "go_tay": 1, "da_tru_bu": 1})
	la("khoá lạ không khớp gì", [tb.thuoc_chang(o, "xyz") for o in ds], [False] * 4)
	la("mọi chip chặng có nhãn và biểu tượng", all(len(x) == 3 and x[1] and x[2] for x in tb.CHANG), True)


@ca("v550 hàng về kho: chỉ kho điểm bán mới xếp việc trừ bù, đọc cả t_warehouse và warehouse")
def _kho_cham():
	diem = {KHO, "Kho Sales Online - TV"}
	la("phiếu điều chuyển vào D1", tb.kho_bi_cham([{"s_warehouse": "Kho NVHTN - TV", "t_warehouse": KHO}], diem), [KHO])
	la("phiếu kiểm kê", tb.kho_bi_cham([{"warehouse": "Kho Sales Online - TV"}], diem), ["Kho Sales Online - TV"])
	la("kho bếp không xếp việc", tb.kho_bi_cham([{"t_warehouse": "Baker - Thành phẩm - TV"}], diem), [])
	la("xuất đi khỏi D1 không xếp việc", tb.kho_bi_cham([{"s_warehouse": KHO}], diem), [])


@ca("v550 quyền: quản lý cửa hàng và kế toán được trừ bù, thu ngân chỉ xem, bếp không xem")
def _quyen():
	dung("QLCH trừ bù", tb.duoc(["VGB - Quản lý cửa hàng"], tb.QUYEN_TRU))
	dung("kế toán trừ bù", tb.duoc(["Accounts User"], tb.QUYEN_TRU))
	dung("giám đốc trừ bù", tb.duoc(["Giám đốc"], tb.QUYEN_TRU))
	dung("thu ngân không trừ bù", not tb.duoc(["Sales User"], tb.QUYEN_TRU))
	dung("thu ngân xem được", tb.duoc(["Sales User"], tb.QUYEN_XEM))
	dung("bếp không xem", not tb.duoc(["Bếp trưởng", "Stock User"], tb.QUYEN_XEM))
	dung("trừ bù là tập con của xem", tb.QUYEN_TRU <= tb.QUYEN_XEM)


# ------------------------------------------------- tru_bu chạy thật, DB giả

class Hop:
	"""Sổ giả: tồn từng (mã, kho), phiếu bù đã lập, ô đã ghi lên hoá đơn."""

	def __init__(self, can, ton, da=None, si=None, hong_mon=None, hong_het=None):
		self.can, self.ton, self.da = dict(can), dict(ton), dict(da or {})
		self.si = D(name="HDB-26-10-00033", docstatus=1, vgb_tru_kho_ban=1, vgb_chua_tru_kho=1,
			vgb_tru_bu="", company="CÔNG TY TNHH PATISSERIE VAGABOND")
		self.si.update(si or {})
		self.phieu, self.ghi, self.lui, self.diem_luu, self.khoa = [], [], [], [], []
		self.hong_mon, self.hong_het = set(hong_mon or ()), hong_het

	def lap_phieu(self, si, kho, tk632, lay, nguon):
		if self.hong_het:
			raise self.hong_het
		if any(k[0] in self.hong_mon for k in lay):
			raise tb.frappe.ValidationError("Lô của %s đã tắt" % ",".join(k[0] for k in lay))
		ten = "PXD-%d" % (len(self.phieu) + 1)
		self.phieu.append((ten, dict(lay)))
		for k, v in lay.items():
			self.da[k] = self.da.get(k, 0) + v
			self.ton[k] = self.ton.get(k, 0) - v
		return ten

	def chay(self, **kw):
		f = tb.frappe
		db = NS(savepoint=lambda m: self.diem_luu.append(m), rollback=lambda save_point=None: self.lui.append(save_point),
			sql=lambda q, a=None, **k: self.khoa.append(a) or [], set_value=lambda *a, **k: self.ghi.append(("db", a)))
		with patch.object(f, "db", db), \
				patch.object(f, "get_doc", lambda dt, ten: self.si), \
				patch.object(f, "generate_hash", lambda length=10: "x" * length, create=True), \
				patch.object(f, "clear_last_message", lambda: None, create=True), \
				patch.object(tb, "_kho_diem_ban", lambda si: KHO), \
				patch.object(tb, "can_cua", lambda si, kho: dict(self.can)), \
				patch.object(tb, "da_tru_cua", lambda ten: dict(self.da)), \
				patch.object(tb, "_ton", lambda cap, khoa=False: {k: self.ton.get(k, 0) for k in cap}), \
				patch.object(tb, "_lap_phieu", self.lap_phieu), \
				patch.object(tb, "_ghi_hd", lambda si, gt: (self.ghi.append(("hd", dict(gt))), si.update(gt))), \
				patch.object(tb, "now_datetime", lambda: "2026-10-01 14:20:00"), \
				patch("vagabond.hach_toan_kho._kiem_cau_hinh", lambda kho, ct: "632 - Giá vốn hàng bán - TV"):
			return tb.tru_bu(self.si.name, **kw)


A, B = ("BACF00001", KHO), ("BANU00032", KHO)


@ca("v550 HDB-26-10-00021: Biscotti còn hàng thì trừ ngay, Tart chưa có thì chờ; tờ là Một phần")
def _mot_phan():
	h = Hop({A: 2, B: 1}, {A: 12, B: 0})
	r = h.chay(nguon="máy: lúc ghi sổ hoá đơn")
	la("ok", r["ok"], 1)
	la("lập một phiếu chỉ cho Biscotti", h.phieu, [("PXD-1", {A: 2.0})])
	la("còn thiếu Tart", r["con_thieu"], {"BANU00032|" + KHO: 1.0})
	la("ô Trừ bù", h.si.vgb_tru_bu, "Một phần")
	la("vẫn Chưa trừ kho", h.si.vgb_chua_tru_kho, 1)
	dung("lý do nêu món chờ", "BANU00032" in (h.si.vgb_ly_do_chua_tru_kho or "") and "Còn chờ hàng về" in h.si.vgb_ly_do_chua_tru_kho)
	la("khoá hoá đơn trước khi tính", h.khoa[0], (h.si.name,))
	la("không lùi điểm lưu", h.lui, [])


@ca("v550 HDB-26-10-00033: hàng điều chuyển về rồi thì lượt sau trừ nốt, tờ thành Đã trừ bù")
def _ve_hang():
	h = Hop({A: 2, B: 1}, {A: 10, B: 5}, da={A: 2}, si={"vgb_tru_bu": "Một phần"})
	r = h.chay(nguon="máy: hàng về kho")
	la("chỉ trừ món còn thiếu", h.phieu, [("PXD-1", {B: 1.0})])
	la("không còn thiếu", r["con_thieu"], {})
	la("hết Chưa trừ kho", h.si.vgb_chua_tru_kho, 0)
	la("ô Trừ bù", h.si.vgb_tru_bu, "Đủ")
	la("chip màn hình", tb.trang_thai_kho(h.si), "da_tru_bu")
	la("tồn D1 không âm", h.ton[B], 4.0)


@ca("v550 kho vẫn chưa có gì: không lập phiếu, ô Trừ bù giữ nguyên, tờ vẫn chờ")
def _chua_co():
	h = Hop({B: 1}, {B: 0})
	r = h.chay()
	la("không phiếu", h.phieu, [])
	la("ok", r["ok"], 1)
	la("ô Trừ bù vẫn trống", h.si.vgb_tru_bu, "")
	la("vẫn chưa trừ", h.si.vgb_chua_tru_kho, 1)


@ca("v550 một món hỏng lô không kéo món khác: thử từng món, món tốt vẫn trừ")
def _tung_mon():
	h = Hop({A: 2, B: 1}, {A: 12, B: 5}, hong_mon={"BANU00032"})
	r = h.chay()
	la("trừ được Biscotti bằng phiếu riêng", h.phieu, [("PXD-1", {A: 2.0})])
	la("Tart còn thiếu", r["con_thieu"], {"BANU00032|" + KHO: 1.0})
	dung("lý do có lỗi lô của Tart", "Lô của BANU00032 đã tắt" in (h.si.vgb_ly_do_chua_tru_kho or ""))
	la("đã lùi đúng hai lần thử hỏng (cả nhóm, rồi riêng Tart)", len(h.lui), 2)


@ca("v550 phiếu bù bị gỡ tay: nhịp tự động bỏ qua, người bấm Trừ bù thì trừ lại")
def _go_tay():
	h = Hop({B: 1}, {B: 3}, si={"vgb_tru_bu": "Gỡ tay"})
	r = h.chay(nguon="máy: nhịp mỗi giờ")
	dung("bỏ qua", "gỡ tay" in (r.get("bo_qua") or ""))
	la("không phiếu", h.phieu, [])
	r = h.chay(nguon="ketoan@vagabond.vn", tay=True)
	la("bấm tay thì lập phiếu", [p[0] for p in h.phieu], ["PXD-1"])
	la("ô Trừ bù", h.si.vgb_tru_bu, "Đủ")


@ca("v550 lỗi bất ngờ khi trừ bù: không ném ra ngoài, lùi điểm lưu, ghi lý do, mở lại cờ chống lặp")
def _khong_nem():
	h = Hop({B: 1}, {B: 3}, hong_het=RuntimeError("mất kết nối"))
	r = h.chay()
	la("ok 0", r["ok"], 0)
	dung("câu lỗi", "mất kết nối" in r["loi"])
	la("lùi đúng điểm lưu ngoài cùng", h.lui[-1], h.diem_luu[0])
	dung("ghi lý do lên hoá đơn", any(x[0] == "db" and "Trừ bù chưa được" in str(x[1]) for x in h.ghi))
	la("cờ chống lặp đã mở lại", bool(tb.frappe.flags.get("vgb_dang_tru_bu")), False)


@ca("v550 tờ đã đủ hoặc không qua luồng bán trừ kho: không làm gì")
def _bo_qua():
	for si in ({"vgb_chua_tru_kho": 0}, {"vgb_tru_kho_ban": 0}, {"docstatus": 2}):
		h = Hop({B: 1}, {B: 3}, si=si)
		r = h.chay()
		dung("bỏ qua %s" % si, bool(r.get("bo_qua")))
		la("không phiếu %s" % si, h.phieu, [])


@ca("v550 đang trừ bù trong cùng lượt (phiếu bù gọi hook nhập kho): không chạy lồng")
def _long():
	h = Hop({B: 1}, {B: 3})
	tb.frappe.flags.vgb_dang_tru_bu = True
	try:
		r = h.chay()
	finally:
		tb.frappe.flags.vgb_dang_tru_bu = False
	la("không chạy", r["ok"], 0)
	la("không phiếu", h.phieu, [])


# ------------------------------------------------------------ hook

@ca("v550 phiếu nhập vào kho điểm bán: xếp việc SAU commit (không chạm hàng đợi trong phiếu), gộp theo kho; phiếu bù của máy không xếp")
def _hook_nhap():
	goi, sau_commit = [], []
	f = tb.frappe
	db = NS(after_commit=NS(add=lambda fn: sau_commit.append(fn)))
	with patch.object(f, "enqueue", lambda *a, **k: goi.append((a, k)), create=True), \
			patch.object(f, "db", db), \
			patch.object(f, "scrub", lambda s: s.lower().replace(" ", "_"), create=True), \
			patch.object(tb, "tat_ca_kho_diem", lambda: {KHO}):
		tb.khi_nhap_kho(D(items=[D(t_warehouse=KHO), D(t_warehouse=KHO)]))
		tb.khi_nhap_kho(D(vgb_hd_tru_bu="HDB-1", items=[D(t_warehouse=KHO)]))
		tb.khi_nhap_kho(D(items=[D(t_warehouse="Baker - Thành phẩm - TV")]))
		la("chưa chạm hàng đợi trước commit", goi, [])
		la("một việc chờ commit cho D1", len(sau_commit), 1)
		for fn in sau_commit:
			fn()
	la("một việc cho D1", len(goi), 1)
	a, k = goi[0]
	la("đúng hàm", a[0], "vagabond.tru_kho_bu.tru_bu_kho")
	la("đúng kho", k["kho"], KHO)
	la("gộp trùng", k.get("deduplicate"), True)


@ca("v550 huỷ tay phiếu bù: hoá đơn về Chưa trừ kho, gắn Gỡ tay; huỷ theo hoá đơn thì không đụng")
def _hook_huy():
	si = D(name="HDB-1", docstatus=1, vgb_chua_tru_kho=0, vgb_tru_bu="Đủ")
	ghi = []
	with patch.object(tb.frappe, "get_doc", lambda dt, ten: si), \
			patch.object(tb, "_kho_diem_ban", lambda s: KHO), \
			patch.object(tb, "can_cua", lambda s, k: {B: 1}), \
			patch.object(tb, "da_tru_cua", lambda t: {}), \
			patch.object(tb, "now_datetime", lambda: "2026-10-01 15:00:00"), \
			patch.object(tb, "_ghi_hd", lambda s, gt: (ghi.append(gt), s.update(gt))):
		tb.frappe.flags.vgb_huy_theo_hd = "HDB-1"
		tb.khi_huy_phieu(D(name="PXD-1", vgb_hd_tru_bu="HDB-1"))
		la("huỷ theo hoá đơn: không ghi", ghi, [])
		tb.frappe.flags.vgb_huy_theo_hd = None
		tb.khi_huy_phieu(D(name="PXD-1", vgb_hd_tru_bu="HDB-1"))
	la("về chưa trừ", si.vgb_chua_tru_kho, 1)
	la("gỡ tay", si.vgb_tru_bu, "Gỡ tay")
	dung("lý do nêu phiếu bị huỷ", "PXD-1" in si.vgb_ly_do_chua_tru_kho)


@ca("v550 hook nối CUỐI chuỗi sẵn có, không thay hook cũ; ô mới dựng sau ô v542")
def _dang_ky():
	sys.modules.setdefault("frappe", tb.frappe)
	ns = {}
	exec(compile(_doc("vagabond/hooks.py"), "hooks.py", "exec"), ns)
	de = ns["doc_events"]
	la("ghi sổ hoá đơn: chạy cuối", de["Sales Invoice"]["on_submit"][-1], "vagabond.tru_kho_bu.khi_ghi_so_hd")
	dung("vẫn giữ hook don_web", "vagabond.don_web.khi_ghi_so_hoa_don" in de["Sales Invoice"]["on_submit"])
	la("huỷ hoá đơn: chạy cuối", de["Sales Invoice"]["on_cancel"][-1], "vagabond.tru_kho_bu.khi_huy_hd")
	dung("huỷ phiếu kho giữ hook vận đơn", de["Stock Entry"]["on_cancel"][0] == "vagabond.van_don.dong_van_don_khi_huy_phieu")
	for dt in ("Stock Entry", "Stock Reconciliation", "Purchase Receipt"):
		dung("%s ghi sổ xếp trừ bù" % dt, "vagabond.tru_kho_bu.khi_nhap_kho" in de[dt]["on_submit"])
	dung("nhịp mỗi giờ", "vagabond.tru_kho_bu.quet_moi_gio" in ns["scheduler_events"]["hourly"])
	tt = _doc("vagabond/truong_tu_them.py")
	dung("ô mới dựng sau nhóm hach_toan_kho",
		tt.index('_dung_nhom(hach_toan_kho.TRUONG_MOI') < tt.index('_dung_nhom(tru_kho_bu.TRUONG_MOI'))
	o = {x["fieldname"]: x for x in tb.TRUONG_MOI["Sales Invoice"]}
	la("ô Trừ bù kho chèn sau Lý do chưa trừ kho", o["vgb_tru_bu"]["insert_after"], "vgb_ly_do_chua_tru_kho")
	la("giá trị ô Trừ bù", o["vgb_tru_bu"]["options"].split("\n"), ["", "Một phần", "Đủ", "Gỡ tay"])
	la("ô liên kết trên phiếu kho", tb.TRUONG_MOI["Stock Entry"][0]["options"], "Sales Invoice")


@ca("v550 website không đọc tồn ERP: trừ bù không làm web trừ hàng lần hai")
def _web():
	# Phép dò chuỗi CHỐT một điều không chạy được ở tầng này (quy tắc 16):
	# hai nguồn số của web không đụng sổ kho ERP. Nếu một ngày ai cho web đọc
	# Bin hay Stock Ledger thì phiếu bù sẽ trừ web thêm lần nữa, phải xét lại.
	for tep in ("vagabond/kiem_kho.py", "vagabond/kiem_banh.py"):
		s = _doc(tep)
		for tu in ("tabBin", "Stock Ledger Entry", "get_stock_balance", "actual_qty", "vgb_tru_bu"):
			dung("%s không đọc %s" % (tep, tu), tu not in s)


# ----------------------------------- ban_truoc_ghi_so chạy thật, tồn giả

@ca("v550 ghi sổ cuối ngày: tồn lúc bán còn mà hiện giờ đã hết thì không trừ theo giờ bán")
def _min_ton():
	from vagabond import hach_toan_kho as hk
	bo = []

	class Lo:
		@staticmethod
		def get_stock_balance(ma, kho, ngay=None, gio=None):
			return 2 if ngay else 0

	doc = D(vgb_tru_kho_ban=1, update_stock=1, posting_date="2026-10-01", posting_time="10:10:00",
		items=[D(item_code="BANU00062", warehouse=KHO, stock_qty=1)], packed_items=[])
	from vagabond import hang_tang_kho
	chia = []
	db = NS(sql=lambda *a, **k: [], savepoint=lambda m: None, rollback=lambda save_point=None: None)
	with patch.dict(sys.modules, {"erpnext": NS(), "erpnext.stock": NS(), "erpnext.stock.utils": Lo,
			"vagabond.minvoice_an_toan": NS(la_hang_tang=lambda d: False)}), \
			patch.object(hk.frappe, "get_cached_value", lambda *a: 1, create=True), \
			patch.object(hk.frappe, "db", db), \
			patch.object(hk.frappe, "generate_hash", lambda length=10: "x" * length, create=True), \
			patch.object(hang_tang_kho, "chia_lo_xuat", lambda d, nhom: chia.append(nhom)), \
			patch.object(hk, "_bo_tru_kho", lambda d, ly_do: bo.append(ly_do)):
		hk.ban_truoc_ghi_so(doc)
	la("không đi tiếp sang chia lô xuất", chia, [])
	la("đánh dấu thiếu một lần", len(bo), 1)
	dung("lý do nêu món, còn 0", "BANU00062" in bo[0] and "còn 0" in bo[0])


@ca("v550 hành vi màn hình chạy thật trong node (chip, chip lọc, Trừ bù, Excel, khối Kho)")
def _node():
	p = os.path.join(GOC, "vagabond/khung/kiem_thu/hanh_vi/tru_kho_bu_550.js")
	kq = subprocess.run(["node", p], capture_output=True, text=True, timeout=60)
	la("hành vi node: " + kq.stdout + kq.stderr, kq.returncode, 0)
	dung("cổng chạy tru_kho_bu_550.js", "node vagabond/khung/kiem_thu/hanh_vi/tru_kho_bu_550.js" in _doc("kiem_truoc_deploy.sh"))


# ------------------------------------------- vòng 3: Codex review 3c93e55

def _ds_gia(rows):
	"""get_all giả tôn trọng limit_page_length như Frappe thật."""
	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=20, **k):
		n = limit_page_length if limit_page_length else len(rows)
		return [D(r) for r in rows[:n]]
	return get_all


@ca("v550 F1 (Codex 3c93e55): 300 tờ Gỡ tay hay kho khác đứng đầu không chặn tờ thứ 301 đủ điều kiện")
def _f1_tran():
	rows = [{"name": "G%03d" % i, "vgb_quay": "TCV", "vgb_tru_bu": "Gỡ tay"} for i in range(300)]
	rows += [{"name": "K%03d" % i, "vgb_quay": "NVHTN", "vgb_tru_bu": ""} for i in range(50)]
	rows.append({"name": "T301", "vgb_quay": "TCV", "vgb_tru_bu": ""})
	kho = {"TCV": KHO, "NVHTN": "Kho NVHTN - TV"}
	with patch.object(tb.frappe, "get_all", _ds_gia(rows)), \
			patch.object(tb, "_kho_diem_ban", lambda r: kho[r.vgb_quay]), \
			patch("vagabond.hach_toan_kho._moc", lambda o: "2026-10-01"):
		dung("nhịp toàn hệ thống tới được T301", "T301" in tb._hd_cho(None))
		la("hàng về D1 tới được T301", tb._hd_cho(KHO), ["T301"])
		dung("nút cả điểm (kể cả Gỡ tay) vẫn tới T301", "T301" in tb._hd_cho(KHO, tu_dong=False))


@ca("v550 F1: tờ thiếu hàng đứng đầu hàng đợi không làm tờ sau có tồn bị bỏ qua mãi")
def _f1_tien_trien():
	rows = [{"name": "H%03d" % i, "vgb_quay": "TCV", "vgb_tru_bu": ""} for i in range(320)]
	da = []
	with patch.object(tb.frappe, "get_all", _ds_gia(rows)), \
			patch.object(tb.frappe, "db", NS(commit=lambda: None)), \
			patch.object(tb, "_kho_diem_ban", lambda r: KHO), \
			patch.object(tb, "tru_bu", lambda ten, nguon=None: da.append(ten) or {"ok": 1}), \
			patch("vagabond.hach_toan_kho._moc", lambda o: "2026-10-01"):
		tb.tru_bu_kho(KHO)
	dung("lượt quét tới tờ cuối", "H319" in da)
	la("mỗi tờ một lần", len(da), len(set(da)))


@ca("v550 F2 (Codex 3c93e55): hàng đợi lỗi không làm hỏng phiếu nhập kho")
def _f2_hang_doi():
	f = tb.frappe
	sau_commit, nhat_ky = [], []

	def hong(*a, **k):
		raise ConnectionError("redis down")

	db = NS(after_commit=NS(add=lambda fn: sau_commit.append(fn)))
	with patch.object(f, "enqueue", hong, create=True), \
			patch.object(f, "db", db), \
			patch.object(f, "scrub", lambda s: s.lower().replace(" ", "_"), create=True), \
			patch.object(f, "log_error", lambda *a, **k: nhat_ky.append(a)), \
			patch.object(tb, "tat_ca_kho_diem", lambda: {KHO}):
		loi = None
		try:
			tb.khi_nhap_kho(D(items=[D(t_warehouse=KHO)]))
		except Exception as e:  # noqa: BLE001
			loi = e
		la("hook phiếu nhập không ném", loi, None)
		la("đặt việc sau commit", len(sau_commit), 1)
		loi = None
		try:
			for fn in sau_commit:
				fn()
		except Exception as e:  # noqa: BLE001
			loi = e
		la("việc sau commit không ném khi hàng đợi lỗi", loi, None)
		dung("có ghi nhật ký lỗi", len(nhat_ky) >= 1)


@ca("v550 F3 (Codex 3c93e55): tờ đã trừ trực tiếp hiện Đã trừ đúng số, không báo Đủ để trừ")
def _f3_da_tru():
	def sql(q, a=None, **k):
		if "Stock Ledger Entry" in q:
			return [("BANU00062", KHO, 2.0)]
		return []
	with patch.object(tb.frappe, "db", NS(sql=sql)):
		da = tb.da_tru_cua("HDB-2")
	la("đã trừ lấy từ sổ kho của hoá đơn", da, {("BANU00062", KHO): 2.0})
	la("nhãn món", tb.nhan_dong(2, da.get(("BANU00062", KHO)), 5), "da_tru")

	def sql2(q, a=None, **k):
		if "Stock Ledger Entry" in q:
			return [("A", KHO, 1.0)]
		if "Stock Entry Detail" in q:
			return [("A", KHO, 1.0), ("B", KHO, 3.0)]
		return []
	with patch.object(tb.frappe, "db", NS(sql=sql2)):
		la("cộng cả hai nguồn", tb.da_tru_cua("HDB-3"), {("A", KHO): 2.0, ("B", KHO): 3.0})
