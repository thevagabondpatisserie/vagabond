# -*- coding: utf-8 -*-
"""v653 Nhật ký BTP (sự cố Tira 18cm BAWC00079, Loan Anh báo 12/11/2026).

BTP sẵn và Đủ decor cùng từ 1 lên 2, bếp nói không nhập. Bảng BTP không có
lịch sử, mọi cửa lưu ghi lại CẢ BẢNG Single, nên không truy được ai đổi.

Ca chốt:
  - MỌI cửa ghi bảng BTP (luu_btp, luu_decor, luu_refill, them_ma_btp,
    xoa_ma_btp, gieo_tu_kiem_banh, tru_vo_theo_sx qua kiem_banh.luu_o, bản vá
    v649) đều ghi nhật ký, và không cửa nào lưu cả bảng Single (chạy từng hàm
    thật trên bảng giả, không dò chuỗi);
  - cửa sửa một ô khoá đúng dòng (for update) TRƯỚC khi đọc số trước, chỉ
    UPDATE dòng đó: số máy vừa trừ ở dòng khác không bị ghi đè;
  - Tira: Linh nhập 2 thì nhật ký 1 -> 2, "Linh 22:27 · nhập tay"; Hân sửa
    Bếp làm thì máy trừ, nhật ký nêu bảng Kiểm bánh nguồn và tên Hân;
  - ô Bếp làm ghi ai sửa ở tầng doctype; máy lưu (không đổi Bếp làm) và
    payload giả không đè được vết;
  - lich_su_btp: khách lạ không đọc được, mười dòng mới nhất, nhãn tiếng Việt;
  - màn /kiem-banh chạy THẬT trong node (hanh_vi/nhat_ky_btp_653.js).
"""

import contextlib
import os
import subprocess
import unittest.mock as um

import frappe

from vagabond import btp, kiem_banh
from vagabond.khung.kiem_thu.btp_gia import BangBTP
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_cot_huy_kiem_banh import CuaGia, DongGia, _tao_dong
from vagabond.khung.kiem_thu.thu_tru_vo_btp_649 import BangLuu

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TIRA = "BAWC00079"
KHAC = "BAWC00019"


def _kho(sx=0):
	nay = BangLuu(ngay="2026-08-15", dong=[_tao_dong(ma_hang=TIRA, sx=sx)])
	nay.trong_csdl = Doi(dong=[DongGia(dict(d)) for d in nay.dong])
	cua = CuaGia(**{"KB-2026-08-15": nay})
	cua.btp = Doi(dong=[
		DongGia(ma_hang=TIRA, ten_banh="Bánh Ổ Tira-Missing-U 3.0, 18cm", hinh="", so_btp=1, so_decor=1, decor_da_lam=0,
			so_refill=0, refill_tu=None, refill_den=None),
		DongGia(ma_hang=KHAC, ten_banh="Bánh Ổ Epi 12cm", hinh="", so_btp=5, so_decor=5, decor_da_lam=0,
			so_refill=0, refill_tu=None, refill_den=None)], cap_nhat_luc=None)

	def cam(*a, **k):
		raise AssertionError("không cửa nào được lưu cả bảng BTP Single (v653)")
	cua.btp.save = cam
	return nay, cua


def _so(cua, ma):
	d = [x for x in cua.btp.dong if x["ma_hang"] == ma][0]
	return (d["so_btp"], d["so_decor"])


def _ten(nguoi):
	return {"lethilinh051996@gmail.com": "Linh", "ngochan41096@gmail.com": "Hân"}.get(nguoi)


@contextlib.contextmanager
def _vao(*them):
	"""Quyền bếp, tên người thật trong User, bang_btp không vẽ lại (và vá thêm)."""
	with contextlib.ExitStack() as st:
		for x in [um.patch.object(btp, "_duoc_sua_btp", lambda: True), um.patch.object(btp, "bang_btp", lambda: "ok"),
				um.patch.object(frappe.db, "get_value", lambda dt_, ten=None, f=None, *a, **k: _ten(ten) if dt_ == "User" else None)] + list(them):
			st.enter_context(x)
		yield


@ca("v653 THUẦN: chữ ngắn dưới số (nhập tay, máy trừ theo Bếp làm, cộng lại, bản vá)")
def _nhan():
	la("nhập tay hôm nay chỉ giờ", btp.nhan_doi({"ten_nguoi": "Linh", "luc": "2026-11-12 22:27:55", "ly_do": "nhap_tay"}, "2026-11-12"),
		"Linh 22:27 · nhập tay")
	la("ngày khác kèm ngày", btp.nhan_doi({"ten_nguoi": "Linh", "luc": "2026-11-12 22:27:55", "ly_do": "nhap_tay"}, "2026-11-13"),
		"Linh 12/11 22:27 · nhập tay")
	la("máy trừ theo Bếp làm", btp.nhan_doi({"ten_nguoi": "Hân", "luc": "2026-11-13 21:05", "ly_do": "tru_bep_lam", "nguon": "KB-2026-11-13"}),
		"Máy trừ · Bếp làm 13/11 (Hân)")
	la("sửa bớt Bếp làm", btp.nhan_doi({"ten_nguoi": "Hân", "luc": "2026-11-13 21:05", "ly_do": "cong_lai_bep_lam", "nguon": "KB-2026-11-13"}),
		"Máy cộng lại · Bếp làm 13/11 (Hân)")
	la("rỗng", btp.nhan_doi(None), "")
	la("chênh", (btp.chenh_so("1", 2), btp.chenh_so(None, None), btp.chenh_so("2026-11-14", "")), (1, 0, None))


@ca("v653 Tira: Linh nhập BTP sẵn 2, Đủ decor 2 thì nhật ký ghi 1 -> 2, tên Linh, nhập tay; khoá dòng trước khi đọc số")
def _tira():
	nay, cua = _kho()
	with cua, BangBTP(cua.btp.dong, nguoi="lethilinh051996@gmail.com") as b, _vao():
		btp.luu_btp(TIRA, 2)
		btp.luu_decor(TIRA, "2")
		btp.luu_decor(TIRA, 2)
	la("số mới", _so(cua, TIRA), (2, 2))
	la("bánh khác không đụng", _so(cua, KHAC), (5, 5))
	nk = [(x["truong"], x["truoc"], x["sau"], x["ly_do"], x["ten_nguoi"], x["nguoi"]) for x in b.nhat_ky]
	la("hai dòng nhật ký (lần lưu lại cùng số không ghi)", nk, [
		("so_btp", "1", "2", "nhap_tay", "Linh", "lethilinh051996@gmail.com"),
		("so_decor", "1", "2", "nhap_tay", "Linh", "lethilinh051996@gmail.com")])
	cau = [q for q, g in b.cau]
	i_khoa = next(i for i, q in enumerate(cau) if "for update" in q)
	i_ghi = next(i for i, q in enumerate(cau) if q.lower().startswith("update `tabbtp banh o dong`"))
	dung("khoá dòng trước khi ghi", i_khoa < i_ghi)
	dung("UPDATE chỉ theo tên dòng của mã", all("where name = %(ten)s" in q for q in cau if q.lower().startswith("update `tabbtp banh o dong` set `")))
	dung("đổi mốc BTP bếp cập nhật", "cap_nhat_luc" in b.moc)


@ca("v653 Hân sửa Bếp làm: máy trừ hai ô, nhật ký ghi bảng Kiểm bánh nguồn và người đang lưu; sửa bớt ghi cộng lại")
def _bep_lam():
	nay, cua = _kho()
	with cua, BangBTP(cua.btp.dong, nguoi="ngochan41096@gmail.com") as b, \
			um.patch.object(frappe.db, "get_value", lambda dt_, ten=None, *a, **k: _ten(ten) if dt_ == "User" else None):
		kiem_banh.luu_o("2026-08-15", TIRA, "sx", 1)
		kiem_banh.luu_o("2026-08-15", TIRA, "sx", 0)
	la("trừ rồi cộng lại", _so(cua, TIRA), (1, 1))
	nk = [(x["truong"], x["truoc"], x["sau"], x["ly_do"], x["nguon"], x["ten_nguoi"]) for x in b.nhat_ky]
	la("bốn dòng", nk, [
		("so_btp", "1", "0", "tru_bep_lam", "KB-2026-08-15", "Hân"), ("so_decor", "1", "0", "tru_bep_lam", "KB-2026-08-15", "Hân"),
		("so_btp", "0", "1", "cong_lai_bep_lam", "KB-2026-08-15", "Hân"), ("so_decor", "0", "1", "cong_lai_bep_lam", "KB-2026-08-15", "Hân")])
	dung("đọc số trước dưới khoá", any(q.startswith("select ma_hang, so_btp, so_decor, ten_banh") and q.endswith("for update") for q, g in b.cau))


@ca("v653 MỌI cửa ghi bảng BTP đều ghi nhật ký và không cửa nào lưu cả bảng Single (chạy từng cửa thật)")
def _moi_cua():
	from vagabond.patches import v649_tru_vo_btp_dang_lam as p

	cua_ghi = {}

	def chay(ten, ham, nguoi="lethilinh051996@gmail.com"):
		nay, cua = _kho()
		cua.bang["KB-2026-08-16"] = BangLuu(ngay="2026-08-16", dong=[_tao_dong(ma_hang="BAWC00123", ten_banh="Kankin")])
		with cua, BangBTP(cua.btp.dong, nguoi=nguoi) as b, _vao(
				um.patch.object(btp, "_co_that", lambda *a: True), um.patch.object(btp, "_tra_anh_ten", lambda *a: ("Tên", "")),
				um.patch.object(btp, "cfg", lambda: {}), um.patch.object(btp, "key", lambda *a: "k"),
				um.patch.object(btp, "getdate", lambda *a: __import__("datetime").date(2026, 8, 15)),
				um.patch.object(frappe, "cache", lambda: Doi(delete_value=lambda *a: None), create=True),
				um.patch.object(frappe, "get_all", lambda *a, **k: [{"name": "KB-2026-08-15", "ngay": "2026-08-15", "tinh_trang": "Dang ban"}], create=True),
				um.patch.object(p, "can_tru", lambda bang, hn: (["KB-2026-08-15"], []))):
			ham(cua)
		cua_ghi[ten] = len(b.nhat_ky)

	chay("luu_btp", lambda c: btp.luu_btp(TIRA, 3))
	chay("luu_decor", lambda c: btp.luu_decor(TIRA, 3))
	chay("luu_refill", lambda c: btp.luu_refill(TIRA, "5", "2026-08-16", ""))
	chay("luu_btp mã mới", lambda c: btp.luu_btp("BAWC00555", 2))
	chay("them_ma_btp", lambda c: btp.them_ma_btp("BAWC00556"))
	chay("xoa_ma_btp", lambda c: (c.btp.dong[0].update(so_btp=0, so_decor=0), btp.xoa_ma_btp(TIRA)))
	chay("gieo_tu_kiem_banh", lambda c: btp.gieo_tu_kiem_banh())
	chay("tru_vo_theo_sx (Kiểm bánh)", lambda c: kiem_banh.luu_o("2026-08-15", TIRA, "sx", 1))
	chay("bản vá v649", lambda c: (c.bang["KB-2026-08-15"].dong[0].update(sx=1), p.execute()))
	la("mọi cửa đều có nhật ký", sorted(k for k, n in cua_ghi.items() if n == 0), [])
	dung("đủ chín cửa", len(cua_ghi) == 9)


@ca("v653 xoá mã còn số bị chặn và không ghi gì; mã không có trên bảng thì Bếp làm không ghi nhật ký")
def _chan():
	nay, cua = _kho()
	with cua, BangBTP(cua.btp.dong) as b, _vao():
		nem("còn số BTP thì không gỡ mã", lambda: btp.xoa_ma_btp(TIRA))
	la("không nhật ký", b.nhat_ky, [])
	nay, cua = _kho()
	nay.dong.append(_tao_dong(ma_hang="BAWS00777"))
	nay.trong_csdl.dong.append(DongGia(dict(nay.dong[-1])))
	with cua, BangBTP(cua.btp.dong) as b:
		kiem_banh.luu_o("2026-08-15", "BAWS00777", "sx", 2)
	la("bánh ngoài bảng BTP: không nhật ký", b.nhat_ky, [])


@ca("v653 ô Bếp làm ghi ai sửa; máy lưu không đổi Bếp làm hay payload giả không đè vết; màn hiện tên đầy đủ, không email")
def _sx_nguoi():
	nay, cua = _kho()
	with cua, BangBTP(cua.btp.dong, nguoi="ngochan41096@gmail.com"):
		kiem_banh.luu_o("2026-08-15", TIRA, "sx", 2)
	d = nay.dong[0]
	la("ghi Hân", d.get("sx_nguoi"), "ngochan41096@gmail.com")
	luc = d.get("sx_luc")
	dung("có giờ", bool(luc))
	with cua, BangBTP(cua.btp.dong, nguoi="Administrator"):
		d["sx_nguoi"] = "ke.gia@x.vn"
		kiem_banh.luu_o("2026-08-15", TIRA, "huy", 1)
	la("máy lưu ô khác, payload giả: vết giữ Hân", (d.get("sx_nguoi"), d.get("sx_luc")), ("ngochan41096@gmail.com", luc))
	la("chữ dưới ô Bếp làm", kiem_banh.ai_sua_sx(d, {"ngochan41096@gmail.com": "Hân"}), "Hân 09:00")
	la("chưa có tên trong User thì không lộ cả email", kiem_banh.ai_sua_sx(d, {}), "ngochan41096 09:00")
	la("chưa ai sửa", kiem_banh.ai_sua_sx({"sx_nguoi": None}), "")


@ca("v653 bang_btp trả kèm lần đổi gần nhất từng ô; lich_su_btp chặn khách lạ, mười dòng, nhãn tiếng Việt")
def _api():
	nk = [{"ma_hang": TIRA, "truong": "so_btp", "ten_nguoi": "Linh", "luc": "2026-08-15 22:27:55", "ly_do": "nhap_tay", "nguon": ""}]
	with um.patch.object(frappe.db, "sql", lambda q, gt=None, *a, **k: [Doi(x) for x in nk] if "Nhat Ky BTP" in q else []):
		la("lần đổi gần nhất", btp._gan_doi([{"ma_hang": TIRA}], "2026-08-15"), {TIRA: {"so_btp": {"chu": "Linh 22:27 · nhập tay", "luc": "2026-08-15 22:27:55"}}})

	def loi(*a, **k):
		raise Exception("Table 'tabNhat Ky BTP' doesn't exist")
	with um.patch.object(frappe.db, "sql", loi):
		la("chưa migrate thì màn vẫn chạy", btp._gan_doi([{"ma_hang": TIRA}]), {})
	with um.patch.object(frappe.session, "user", "Guest"):
		nem("khách lạ không đọc", lambda: btp.lich_su_btp(TIRA))
	hoi = {}

	def get_all(dt_, filters=None, limit_page_length=None, **k):
		hoi.update(dt=dt_, f=filters, n=limit_page_length)
		return [Doi(truong="so_decor", truoc="1", sau="2", chenh=1, ly_do="nhap_tay", nguon="", ten_nguoi="Linh", luc="2026-08-15 22:27:55")]
	with um.patch.object(frappe, "get_all", get_all):
		r = btp.lich_su_btp(" %s " % TIRA, so="abc")
	la("đọc đúng mã, mười dòng", (hoi["dt"], hoi["f"], hoi["n"]), ("Nhat Ky BTP", {"ma_hang": TIRA}, 10))
	la("nhãn", (r["dong"][0]["o"], r["dong"][0]["ly_do"]), ("Đủ decor", "nhập tay"))


@ca("v653 màn /kiem-banh chạy thật trong node: dòng ai đổi dưới BTP sẵn, Đủ decor, Bếp làm; bấm mở lịch sử")
def _man():
	r = subprocess.run(["node", os.path.join(GOC, "khung", "kiem_thu", "hanh_vi", "nhat_ky_btp_653.js")], capture_output=True, text=True, timeout=120)
	la("nhat_ky_btp_653.js chạy xanh", (r.returncode, (r.stdout + r.stderr)[-400:] if r.returncode else ""), (0, ""))


@ca("v653 doctype Nhật ký BTP: chỉ đọc cho mọi vai, không ai tạo, sửa, xoá tay")
def _doctype():
	import json

	d = json.load(open(os.path.join(GOC, "vagabond", "doctype", "nhat_ky_btp", "nhat_ky_btp.json"), encoding="utf-8"))
	dung("không vai nào được ghi, tạo, xoá", all(not p.get(k) for p in d["permissions"] for k in ("write", "create", "delete")))
	dung("vai bếp đọc được", any(p["role"] == "Bếp phó" and p.get("read") for p in d["permissions"]))
	from vagabond.vagabond.doctype.nhat_ky_btp.nhat_ky_btp import NhatKyBTP

	x = NhatKyBTP.__new__(NhatKyBTP)
	x.is_new = lambda: False
	nem("bản đã có không sửa được", x.validate)
	nem("không xoá được", x.on_trash)
	k = json.load(open(os.path.join(GOC, "vagabond", "doctype", "kiem_banh_dong", "kiem_banh_dong.json"), encoding="utf-8"))
	la("hai ô ai sửa Bếp làm", [f["fieldname"] for f in k["fields"]][-2:], ["sx_nguoi", "sx_luc"])
	dung("đẩy mốc modified", k["modified"] >= "2026-11-13")
