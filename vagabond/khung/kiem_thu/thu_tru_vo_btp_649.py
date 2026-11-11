# -*- coding: utf-8 -*-
"""v649: trừ BTP sẵn và Đủ decor NGAY khi bếp nhập ô Bếp làm (Loan Anh đề xuất,
anh Việt chọn phương án A 11/11/2026), chốt sổ thôi trừ theo số bán.

Mỗi ca chốt một đường lỗi có thật:
  - nhập Bếp làm mà BTP sẵn, Đủ decor đứng yên tới cuối ngày (đề xuất của Loan Anh);
  - sửa bớt Bếp làm mà vỏ không được cộng lại (trừ mất vỏ thật);
  - bếp đếm lại tủ rồi nhập lại BTP sẵn, máy trừ lại cả bánh làm trước lần đếm;
  - Còn nhận 3 ngày trừ trùng đơn hôm nay đã có bánh bếp làm xong;
  - bếp làm nhiều hơn số đếm, màn hiện số âm.

Ca chạy qua đúng cửa `kiem_banh.luu_o` mà màn Kiểm bánh gọi, lớp doctype
KiemBanhNgay THẬT (validate rồi on_update như Frappe), và `btp.bang_btp` THẬT.
Chỉ giả bảng lưu và câu SQL cộng dồn trên bảng BTP.
"""

import contextlib
import copy
import unittest.mock as um

import frappe

from vagabond import btp, kiem_banh
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la
from vagabond.khung.kiem_thu.thu_cot_huy_kiem_banh import BangGia, CuaGia, DongGia, _tao_dong

EPI = "BAWC00019"  # Bánh Ổ Epi 12cm, dòng trong ảnh Loan Anh gửi 11/11/2026


class BangLuu(BangGia):
	"""Như Frappe: lưu thì validate, ghi, rồi on_update; bản trước lưu là bản
	đang nằm trong CSDL (get_doc_before_save)."""

	def __init__(self, *a, **k):
		super().__init__(*a, **k)
		self.trong_csdl = None

	def _ban_truoc(self):
		return self.trong_csdl

	def save(self, *a, **k):
		self.validate()
		self.on_update()
		self.so_lan_luu += 1
		self.trong_csdl = Doi(dong=copy.deepcopy([dict(d) for d in self.dong]))


def _kho(so_btp=10, so_decor=9, sx=0, ma=EPI, ngay="2026-08-15", **dong):
	"""Bảng Kiểm bánh ngày cố định của bộ kiểm (15/08) và bảng BTP một dòng."""
	nay = BangLuu(ngay=ngay, dong=[_tao_dong(ma_hang=ma, sx=sx, **dong)])
	nay.trong_csdl = Doi(dong=copy.deepcopy([dict(d) for d in nay.dong]))
	cua = CuaGia(**{"KB-" + ngay: nay})
	# Dòng BTP ghi thuộc tính vào khoá dict như dòng Frappe (luu_decor gán d.so_decor).
	cua.btp = Doi(dong=[DongGia(ma_hang=ma, ten_banh="Bánh Ổ Epi, size 12cm", hinh="", so_btp=so_btp, so_decor=so_decor, decor_da_lam=0,
		so_refill=0, refill_tu=None, refill_den=None)], cap_nhat_luc=None)
	return nay, cua


@contextlib.contextmanager
def _chay(cua):
	"""Câu UPDATE cộng dồn của btp.tru_vo_theo_sx chạy trên bảng BTP giả."""
	vet = []

	def sql(cau, gt=None, *a, **k):
		vet.append(gt)
		if cau.lstrip().lower().startswith("select ma_hang from `tabbtp banh o dong`"):
			can = set(gt["ma"] if isinstance(gt, dict) else gt)
			return [(d["ma_hang"],) for d in cua.btp.dong if d["ma_hang"] in can]
		if "update `tabBTP Banh O Dong`" in cau:
			for d in cua.btp.dong:
				if d.ma_hang == gt["ma"]:
					d["so_btp"] = (d["so_btp"] or 0) - gt["n"]
					d["so_decor"] = (d["so_decor"] or 0) - gt["n"]
					if "decor_da_lam = ifnull(decor_da_lam, 0) + %(n)s" in cau:
						d["decor_da_lam"] = (d.get("decor_da_lam") or 0) + gt["n"]
		return []

	with cua, um.patch.object(frappe.db, "sql", sql, create=True), \
			um.patch.object(frappe.db, "set_single_value", lambda *a, **k: vet.append(("moc", a[1])), create=True), \
			um.patch.object(frappe.db, "commit", lambda *a, **k: None, create=True):
		yield vet


def _o(cua):
	d = cua.btp.dong[0]
	return (d["so_btp"], d["so_decor"])


@ca("v649 thuần: chênh Bếp làm theo từng mã (tăng, bớt, mã mới, gộp dòng trùng mã, bỏ mã rỗng)")
def _thuan():
	la("tăng 1", btp.chenh_sx([{"ma_hang": EPI, "sx": 0}], [{"ma_hang": EPI, "sx": 1}]), {EPI: 1})
	la("bớt 2", btp.chenh_sx([{"ma_hang": EPI, "sx": 3}], [{"ma_hang": EPI, "sx": 1}]), {EPI: -2})
	la("không đổi thì rỗng", btp.chenh_sx([{"ma_hang": EPI, "sx": 2}], [{"ma_hang": EPI, "sx": 2}]), {})
	la("bản mới chưa có trong CSDL", btp.chenh_sx([], [{"ma_hang": EPI, "sx": 4}]), {EPI: 4})
	la("ô trống là 0", btp.chenh_sx([{"ma_hang": EPI, "sx": None}], [{"ma_hang": EPI, "sx": ""}]), {})
	la("gộp hai dòng cùng mã", btp.chenh_sx([], [{"ma_hang": EPI, "sx": 1}, {"ma_hang": EPI, "sx": 2}]), {EPI: 3})
	la("bỏ mã rỗng", btp.chenh_sx([], [{"ma_hang": "", "sx": 5}]), {})
	g = lambda don, sx: btp.don_con_giu_vo({"da_dat": don, "sx": sx})
	la("giữ đơn trừ bánh đã làm", (g(2, 1), g(2, 5), g(0, 3)), (1, 0, 0))


@ca("v649 Loan Anh: nhập Bếp làm 1 thì BTP sẵn 10 thành 9, Đủ decor 9 thành 8 NGAY, không chờ chốt sổ")
def _tru_ngay():
	nay, cua = _kho()
	with _chay(cua) as vet:
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
	la("BTP sẵn, Đủ decor", _o(cua), (9, 8))
	dung("đổi mốc sửa của bảng BTP", ("moc", "cap_nhat_luc") in vet)


@ca("v649 sửa Bếp làm: tăng thì trừ thêm, sửa bớt thì cộng lại đúng phần bớt, về 0 là trả đủ")
def _sua():
	nay, cua = _kho()
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 3)
		la("làm 3", _o(cua), (7, 6))
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
		la("sửa về 1", _o(cua), (9, 8))
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 0)
		la("sửa về 0", _o(cua), (10, 9))
		kiem_banh.luu_o("2026-08-15", EPI, "huy", 2)
		la("huỷ không đụng vỏ", _o(cua), (10, 9))


@ca("v649 bếp đếm lại tủ rồi nhập lại BTP sẵn: số đếm là gốc mới, chỉ bánh làm SAU lần đếm mới trừ tiếp")
def _dem_lai():
	nay, cua = _kho()
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
		la("sau lần làm đầu", _o(cua), (9, 8))
		# Bếp đếm tủ thấy 9 vỏ, 8 đủ decor và nhập lại (đường luu_btp, luu_decor ghi thẳng số).
		cua.btp.dong[0].update(so_btp=9, so_decor=8)
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 3)
	la("chỉ trừ 2 bánh làm sau lần đếm", _o(cua), (7, 6))


@ca("v649 chốt sổ sau khi bếp làm: không trừ vỏ lần hai theo số bán")
def _chot():
	nay, cua = _kho(ton_d1=1, da_dat=1, phat_sinh=1)
	mai = BangLuu(ngay="2026-08-16")
	cua.bang["KB-2026-08-16"] = mai
	cua.btp.save = lambda *a, **k: None
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
		kiem_banh.chot_ngay("2026-08-15")
	la("vỏ chỉ trừ một lần (bếp làm 1)", _o(cua), (9, 8))
	la("hôm nay đã khoá", nay.tinh_trang, "Da chot")


def _bang(cua, kb):
	from vagabond.khung.kiem_thu import thu_refill_646 as rf

	kho = rf.Kho([dict(d) for d in cua.btp.dong], kb)
	return rf._chay(kho, btp.bang_btp, rf._tinh_that(don=[]))["dong"][0]


@ca("v649 ví dụ trong ảnh duyệt: Bánh Ổ Epi 12cm, đơn hôm nay 2, bếp làm 1: BTP 9, decor 8, Còn nhận mai 8, Còn nhận 3 ngày 8")
def _vi_du():
	from vagabond.khung.kiem_thu.thu_refill_646 import HN

	nay, cua = _kho(ton_d1=1, da_dat=1, phat_sinh=1)
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
	kb = {"KB-%s" % HN: [{"ma_hang": EPI, "da_dat": 1, "phat_sinh": 1, "cho_chot": 0, "sx": 1}]}
	d = _bang(cua, kb)
	la("bốn ô", (d["so_btp"], d["so_decor"], d["giao_mai"], d["con_nhan"]), (9, 8, 8, 8))
	# Trước v649 (chưa trừ lúc làm, giữ đủ 2 đơn): Còn nhận 3 ngày cũng là 8. Không trừ trùng.
	kb[next(iter(kb))][0]["sx"] = 0
	cua.btp.dong[0].update(so_btp=10, so_decor=9)
	la("bản cũ để so", _bang(cua, kb)["con_nhan"], 8)


@ca("v649 bếp làm nhiều hơn số đã đếm: màn hiện 0 chứ không hiện số âm, Còn nhận vẫn báo thiếu")
def _am():
	from vagabond.khung.kiem_thu.thu_refill_646 import HN

	nay, cua = _kho(so_btp=1, so_decor=1)
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 3)
	la("số lưu giữ phần âm để sửa bớt cộng lại đúng", _o(cua), (-2, -2))
	d = _bang(cua, {"KB-%s" % HN: [{"ma_hang": EPI, "da_dat": 0, "phat_sinh": 0, "cho_chot": 0, "sx": 3}]})
	la("màn hiện 0", (d["so_btp"], d["so_decor"]), (0, 0))
	dung("Còn nhận 3 ngày âm (báo thiếu)", d["con_nhan"] < 0)


@ca("v649 Codex #552 vòng 4: ghi phần Đủ decor đã trừ theo Bếp làm (cộng, sửa bớt thì bớt); bếp nhập lại Đủ decor thì về 0 (gốc mới)")
def _da_lam():
	nay, cua = _kho(so_decor=1)
	cua.btp.save = lambda *a, **k: None
	with _chay(cua), um.patch.object(btp, "_duoc_sua_btp", lambda: True), \
			um.patch.object(btp, "bang_btp", lambda: None):
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 2)
		la("đã trừ 2, decor còn -1", (cua.btp.dong[0]["decor_da_lam"], cua.btp.dong[0]["so_decor"]), (2, -1))
		kiem_banh.luu_o("2026-08-15", EPI, "sx", 1)
		la("sửa về 1", (cua.btp.dong[0]["decor_da_lam"], cua.btp.dong[0]["so_decor"]), (1, 0))
		btp.luu_decor(EPI, 4)
	la("bếp nhập lại 4: gốc mới", (cua.btp.dong[0].get("decor_da_lam"), cua.btp.dong[0].get("so_decor")), (0, 4))


@ca("v649 nhập Bếp làm cho bánh không có trong bảng BTP: không ghi gì vào bảng BTP, không đổi giờ 'BTP bếp cập nhật'")
def _ngoai_bang():
	nay, cua = _kho(ma="BAWS00777")
	cua.btp.dong[0]["ma_hang"] = EPI
	with _chay(cua) as vet:
		kiem_banh.luu_o("2026-08-15", "BAWS00777", "sx", 4)
	la("bảng BTP giữ nguyên", _o(cua), (10, 9))
	dung("không đổi giờ cập nhật bảng BTP", ("moc", "cap_nhat_luc") not in vet)
	la("không câu UPDATE nào", [g for g in vet if isinstance(g, dict) and "n" in g], [])


def _len_ban(cua, bang_csdl):
	"""Chạy bản vá lên v649 trên bảng Kiểm bánh giả: get_all đọc các bảng đang có."""
	from vagabond.patches import v649_tru_vo_btp_dang_lam as p

	ds = [{"name": t, "ngay": b.ngay, "tinh_trang": getattr(b, "tinh_trang", None)} for t, b in bang_csdl.items()]
	with _chay(cua), um.patch.object(frappe, "get_all", lambda *a, **k: [dict(x) for x in ds], create=True):
		p.execute()


@ca("v649 Codex #552 vòng 6: bếp đã nhập Bếp làm 3 dưới bản cũ (bảng chưa chốt), lên v649 thì bản vá trừ đúng 3 một lần; lưu, chốt sau đó không trừ thêm")
def _len_ban_dang_lam():
	nay, cua = _kho(sx=3, ton_d1=1, da_dat=3)
	cua.btp.save = lambda *a, **k: None
	mai = BangLuu(ngay="2026-08-16")
	cua.bang["KB-2026-08-16"] = mai
	# Đường lỗi khi chưa có bản vá: lưu ô khác rồi chốt, vỏ đứng yên 10/9 dù đã làm 3.
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "huy", 0)
	la("chưa có bản vá: bản cũ để lại vỏ chưa trừ", _o(cua), (10, 9))
	_len_ban(cua, {"KB-2026-08-15": nay})
	la("bản vá trừ phần làm dưới bản cũ", _o(cua), (7, 6))
	la("phần Đủ decor đã trừ", cua.btp.dong[0]["decor_da_lam"], 3)
	with _chay(cua):
		kiem_banh.luu_o("2026-08-15", EPI, "huy", 1)
		kiem_banh.chot_ngay("2026-08-15")
	la("lưu, chốt sau đó không trừ thêm", _o(cua), (7, 6))


@ca("v649 bản vá lên bản: chỉ trừ bảng chưa chốt của hôm nay, hôm qua; bảng đã chốt và bảng bỏ quên cũ không đụng")
def _len_ban_chon():
	import datetime

	from vagabond.patches import v649_tru_vo_btp_dang_lam as p

	hn = datetime.date(2026, 8, 15)
	ds = [
		{"name": "KB-2026-08-15", "ngay": hn, "tinh_trang": "Dang ban"},
		{"name": "KB-2026-08-14", "ngay": hn - datetime.timedelta(days=1), "tinh_trang": None},
		{"name": "KB-2026-08-13", "ngay": hn - datetime.timedelta(days=2), "tinh_trang": "Dang ban"},
		{"name": "KB-2026-08-12", "ngay": hn - datetime.timedelta(days=3), "tinh_trang": "Da chot"},
		{"name": "KB-2026-08-16", "ngay": hn + datetime.timedelta(days=1), "tinh_trang": ""},
	]
	la("chọn bảng", p.can_tru(ds, hn), (["KB-2026-08-14", "KB-2026-08-15", "KB-2026-08-16"], ["KB-2026-08-13"]))
	nay, cua = _kho(sx=2)
	nay.tinh_trang = "Da chot"
	_len_ban(cua, {"KB-2026-08-15": nay})
	la("bảng đã chốt: bản cũ đã trừ lúc chốt, không trừ lại", _o(cua), (10, 9))


@ca("v649 bản vá lên bản nằm SAU đồng bộ cấu trúc v649 trong patches.txt (cần cột phần Đủ decor đã trừ)")
def _len_ban_thu_tu():
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	sau = io.open(os.path.join(goc, "patches.txt"), encoding="utf-8").read().split("[post_model_sync]")[1].split()
	dung("có trong post_model_sync", "vagabond.patches.v649_tru_vo_btp_dang_lam" in sau)
	dung("sau đồng bộ cấu trúc v649", sau.index("vagabond.patches.v649_tru_vo_btp_dang_lam") > sau.index("#v649"))
