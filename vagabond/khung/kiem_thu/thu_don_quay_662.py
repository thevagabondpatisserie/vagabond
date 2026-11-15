# -*- coding: utf-8 -*-
"""v662 tách hai kênh bán ở quầy và đơn giao của quầy (anh Việt chốt 15/11/2026).

Ca chốt:
  - Biên tập menu: mỗi món, mỗi bánh hai tick. Món mới chưa tick: Tại bàn bật,
    Giao tắt. Menu lưu giữ "giao" và "an" của bánh trên tủ; mã lạ bị bỏ.
  - Trang khách đọc đúng kênh: Tại bàn bỏ món tắt Tại bàn, Giao chỉ món tick Giao.
  - Bảng món gọi được (goi_mon_ban.bang_mon) theo kênh, và trừ bánh mà đơn giao
    của quầy đang giữ ở MỌI kênh (một nguồn don_quay.giu_cua_diem).
  - Ô Miễn phí giao đơn giao của quầy người điền tay: mọi cách điền hợp lý; để
    trống là 500.000 đ, gõ 0 là tắt.
  - Trả trước bắt buộc: tiền mặt về chuyển khoản.
  - Trạng thái ở quầy chỉ đi đúng chiều: bấm hai lần, màn cũ bấm muộn đều dừng.
  - Đơn chưa trả chỉ giữ món 30 phút.
  - Khung bốn mã ưu đãi gieo ở trạng thái TẮT, mức 0, kênh WEBORDER; mã kênh
    WEBORDER không áp cho đơn đặt bánh Website và ngược lại vẫn áp được.
  - Thu online xong (thanh_toan_web.sau_thu) đơn giao của quầy không ghi Pancake,
    không báo Sales: vào quầy.
"""

import datetime as dt
import json
import os
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _btm():
	from vagabond import bien_tap_menu

	return bien_tap_menu


def _dq():
	from vagabond import don_quay

	return don_quay


@ca("v662 Biên tập menu: món mới chưa tick là Tại bàn bật, Giao tắt; menu giữ tick Giao và tắt Tại bàn của cả bánh trên tủ, bỏ mã lạ")
def _():
	b = _btm()
	m = b.chuan_menu({"nhom": [], "an": ["BK1", "NU1", "LA"], "giao": ["BK2", "NU1", "LA", "NU1"]}, {"NU1", "NU2"}, set(), {"BK1", "BK2"})
	la("an", m["an"], ["BK1", "NU1"])
	la("giao", m["giao"], ["BK2", "NU1"])
	la("món mới NU2: tại bàn bật", b.ban_o_kenh(m, "NU2", b.KENH_TAI_BAN), True)
	la("món mới NU2: giao tắt", b.ban_o_kenh(m, "NU2", b.KENH_GIAO), False)
	la("BK1 tắt tại bàn", b.ban_o_kenh(m, "BK1", b.KENH_TAI_BAN), False)
	la("BK2 bật giao", b.ban_o_kenh(m, "BK2", b.KENH_GIAO), True)
	la("menu chưa xuất bản (None): tại bàn bật", b.ban_o_kenh(None, "X", b.KENH_TAI_BAN), True)
	la("menu chưa xuất bản (None): giao tắt", b.ban_o_kenh(None, "X", b.KENH_GIAO), False)
	la("menu mặc định có giao rỗng", b.menu_mac_dinh([], [], [])["giao"], [])
	la("giao không phải danh sách thì bỏ", b.chuan_menu({"nhom": [], "giao": "NU1"}, {"NU1"}, set())["giao"], [])


@ca("v662 Biên tập menu: thay đổi đọc được nói bật tắt bán Tại bàn, bán Giao")
def _():
	b = _btm()
	ten = {"NU1": "Trà Lài", "BK1": "Mille-feuille"}
	cu = {"nhom": [], "an": [], "giao": ["BK1"]}
	moi = {"nhom": [], "an": ["NU1"], "giao": ["NU1"]}
	la("câu", b.khac_nhau(cu, moi, ten), ["Trà Lài: tắt bán Tại bàn", "Trà Lài: bật bán Giao", "Mille-feuille: tắt bán Giao"])


@ca("v662 trang khách: Tại bàn bỏ món đã tắt Tại bàn; Giao chỉ món tick Giao, kể cả món ẩn ở Tại bàn; nhóm không còn món thì không hiện")
def _():
	b = _btm()
	menu = {"nhom": [{"ma": "banh", "ten": "Bánh", "loai": "banh", "hien": 1},
		{"ma": "n-tra", "ten": "Trà", "loai": "nuoc", "hien": 1, "goc": "Trà", "mon": ["NU1", "NU2"]}],
		"an": ["NU1"], "giao": ["NU1"], "tuy_chon": [], "topping": {}, "mon": {}}
	uong = [{"ma": "NU1", "ten": "A", "nhom_goc": "Trà"}, {"ma": "NU2", "ten": "B", "nhom_goc": "Trà"}]
	la("tại bàn", [x["ma"] for x in b.ap_menu(menu, uong, b.KENH_TAI_BAN)[1]], ["NU2"])
	la("giao", [x["ma"] for x in b.ap_menu(menu, uong, b.KENH_GIAO)[1]], ["NU1"])
	la("cả hai kênh (trang khách tự lọc)", [x["ma"] for x in b.ap_menu(menu, uong, b.KENH_MOI)[1]], ["NU1", "NU2"])
	la("mặc định vẫn là Tại bàn", [x["ma"] for x in b.ap_menu(menu, uong)[1]], ["NU2"])


@ca("v662 ô Miễn phí giao đơn giao của quầy: trống là 500.000, 0 là tắt, nhận 500.000, 500k, 0,5tr, 1tr, chữ lạ không tắt oan")
def _():
	c = _dq().chuan_nguong
	for v, mong in ((None, 500000), ("", 500000), ("   ", 500000), ("0", 0), (0, 0), ("500000", 500000),
			("500.000", 500000), ("500,000", 500000), ("500k", 500000), ("500 nghìn", 500000), ("0,5tr", 500000),
			("1tr", 1000000), ("1 triệu", 1000000), ("300.000đ", 300000), ("abc", 500000), (450000.0, 450000)):
		la("%r" % (v,), c(v), mong)


@ca("v662 đơn giao trả trước: tiền mặt và giá trị lạ về chuyển khoản; thẻ giữ nguyên")
def _():
	c = _dq().chuan_pt
	la("ba cách", [c(x) for x in ("bank", "card", "atm", "cash", "", None, "BANK")], ["bank", "card", "atm", "bank", "bank", "bank", "bank"])


@ca("v662 trạng thái ở quầy chỉ đi đúng chiều (H8 loại 4): xác nhận hai lần, từ chối đơn đã xác nhận, gọi xe khi chưa xác nhận đều không được")
def _():
	d = _dq()
	la("tiền về", d.chuyen_duoc(d.TT_CHO_TRA, "tien_ve"), d.TT_CHO_XN)
	la("tiền về lần hai", d.chuyen_duoc(d.TT_CHO_XN, "tien_ve"), None)
	la("xác nhận", d.chuyen_duoc(d.TT_CHO_XN, "xac_nhan"), d.TT_XN)
	la("xác nhận lần hai", d.chuyen_duoc(d.TT_XN, "xac_nhan"), None)
	la("từ chối đơn đã xác nhận", d.chuyen_duoc(d.TT_XN, "tu_choi"), None)
	la("từ chối đơn đã từ chối", d.chuyen_duoc(d.TT_TU_CHOI, "tu_choi"), None)
	la("gọi xe khi chưa xác nhận", d.chuyen_duoc(d.TT_CHO_XN, "goi_xe"), None)
	la("gọi xe lần hai", d.chuyen_duoc(d.TT_GOI_XE, "goi_xe"), None)
	la("giao xong sau gọi xe", d.chuyen_duoc(d.TT_GOI_XE, "xong"), d.TT_XONG)
	la("đã giao rồi không quay lại", d.chuyen_duoc(d.TT_XONG, "xac_nhan"), None)
	dung("câu màn cũ", "đã được xác nhận" in d.cau_khong_chuyen("DW-1", d.TT_XN))
	la("hẹn hợp lệ", [d.chuan_hen(x) for x in (10, "15", 20)], [10, 15, 20])
	for x in (5, 0, None, "x", 30):
		try:
			d.chuan_hen(x)
			dung("hẹn %r phải bị chặn" % (x,), False)
		except ValueError:
			pass
	la("lý do lạ", d.chuan_ly_do("bất kỳ"), "")


@ca("v662 giữ món trên tủ: đơn chưa trả giữ 30 phút; chờ xác nhận, đang làm, đã gọi xe giữ; đã giao, từ chối nhả; combo tách thành phần, nước không tính")
def _():
	d = _dq()
	bay = dt.datetime(2026, 11, 15, 10, 0)
	la("chưa trả 29 phút", d.con_giu(d.TT_CHO_TRA, bay - dt.timedelta(minutes=29), bay), True)
	la("chưa trả 31 phút", d.con_giu(d.TT_CHO_TRA, bay - dt.timedelta(minutes=31), bay), False)
	la("chờ xác nhận lâu vẫn giữ", d.con_giu(d.TT_CHO_XN, bay - dt.timedelta(hours=5), bay), True)
	la("đã giao nhả", d.con_giu(d.TT_XONG, bay, bay), False)
	la("từ chối nhả", d.con_giu(d.TT_TU_CHOI, bay, bay), False)
	snaps = [{"weborder": {"dong": [{"ma": "BK1", "loai": "banh", "sl": 2}, {"ma": "NU1", "loai": "nuoc", "sl": 3},
		{"ma": "CB1", "loai": "combo", "sl": 2, "thanh_phan": [{"ma": "BK1", "sl": 1}, {"ma": "NU1", "sl": 1}]}]}},
		{"weborder": {"dong": [{"ma": "BK2", "loai": "banh", "sl": 1}]}}, {}]
	la("số giữ", d.sl_giu(snaps), {"BK1": 4, "NU1": 2, "BK2": 1})


@ca("v662 một nguồn bánh đang giữ: bảng món gọi được trừ bánh đơn giao của quầy đang giữ ở cả kênh Tại bàn lẫn Giao; bánh chưa tick kênh không gọi được")
def _():
	import unittest.mock as um

	from vagabond import bien_tap_menu, diem_ban, don_quay, goi_mon_ban, kiem_kho

	menu = {"nhom": [{"ma": "banh", "ten": "Bánh", "loai": "banh", "hien": 1}], "an": ["BK2"], "giao": ["BK1"],
		"tuy_chon": [], "topping": {}, "mon": {}}
	tu = [{"ma": "BK1", "ten": "Mousse", "con": 5, "gia_chung": 95000, "nhom": "Bánh lạnh"},
		{"ma": "BK2", "ten": "Mille-feuille", "con": 3, "gia_chung": 85000, "nhom": "Bánh lạnh"}]
	with um.patch.object(goi_mon_ban, "do_uong_cua_diem", return_value=[]), \
			um.patch.object(goi_mon_ban, "topping_cua_diem", return_value=[]), \
			um.patch.object(bien_tap_menu, "menu_hien_hanh", return_value=menu), \
			um.patch.object(goi_mon_ban, "_da_nhan_cua", return_value=[]), \
			um.patch.object(goi_mon_ban, "_cho_cua", return_value=[]), \
			um.patch.object(goi_mon_ban, "_phieu_tam_mo", return_value=set()), \
			um.patch.object(diem_ban, "gia_rieng", return_value={}), \
			um.patch.object(goi_mon_ban, "doc_combo_ban", return_value=[]), \
			um.patch.object(kiem_kho, "banh_tren_quay", return_value=tu), \
			um.patch.object(don_quay, "giu_cua_diem", return_value={"BK1": 2}):
		tb = goi_mon_ban.bang_mon({"ma": "TCV"})
		gi = goi_mon_ban.bang_mon({"ma": "TCV"}, kenh=bien_tap_menu.KENH_GIAO)
	la("Tại bàn: BK2 tắt Tại bàn không gọi được, BK1 còn 5 trừ 2 đang giữ", {k: v["con"] for k, v in tb.items()}, {"BK1": 3})
	la("Giao: chỉ BK1, cũng trừ 2 đang giữ", {k: v["con"] for k, v in gi.items()}, {"BK1": 3})


@ca("v662 khung bốn mã đơn giao: luôn TẮT, mức 0, kênh WEBORDER và nguồn phiếu Web giao; tên tiếng Việt có dấu, không gạch dài")
def _():
	d = _dq()
	la("bốn mã", [x["ma_ctkm"] for x in d.KHUNG_MA], ["WEB-DON-DAU", "WEB-THE-GRAB", "WEB-DON-HAI", "WEB-GIO-VANG"])
	for x in d.KHUNG_MA:
		r = d.dong_khung_ma(x)
		la(x["ma_ctkm"] + " tắt, mức 0", (r["bat"], r["gia_tri"]), (0, 0))
		la(x["ma_ctkm"] + " kênh", r["kenh"].split("\n"), ["WEBORDER", "Web giao"])
		dung(x["ma_ctkm"] + " tên có dấu", any(ord(c) > 127 for c in r["ten"]))
		dung(x["ma_ctkm"] + " không gạch dài", not any(c in r["ten"] + r.get("web_mo_ta", "") for c in (chr(0x2013), chr(0x2014))))
	gv = [x for x in d.KHUNG_MA if x["ma_ctkm"] == "WEB-GIO-VANG"][0]
	la("giờ vắng", (gv["gio_tu"], gv["gio_den"]), ("14:00:00", "17:00:00"))
	la("ví quà 14 ngày", [x.get("vi_han_ngay") for x in d.KHUNG_MA if x.get("vi_phat")], [14])


@ca("v662 kênh mã ưu đãi: mã kênh WEBORDER chỉ áp đơn giao của quầy; mã không giới hạn kênh áp cả hai; mã Website không áp WEBORDER")
def _():
	from vagabond import khuyen_mai as km

	ma_web = {"cach_thuc": "Giam tong hoa don", "kenh": "WEBORDER\nWeb giao"}
	la("WEBORDER trên Website", bool(km.ly_do_khong_web(ma_web)), True)
	la("WEBORDER trên WEBORDER", km.ly_do_khong_web(ma_web, km.NGUON_WEBORDER), "")
	la("mọi kênh", (km.ly_do_khong_web({"cach_thuc": "Giam tong hoa don"}), km.ly_do_khong_web({"cach_thuc": "Giam tong hoa don"}, "WEBORDER")), ("", ""))
	la("Website trên WEBORDER", bool(km.ly_do_khong_web({"cach_thuc": "Giam tong hoa don", "kenh": "Website"}, "WEBORDER")), True)
	dung("câu nói đúng kênh", "đặt giao tại quầy" in km.ly_do_khong_web(ma_web) or "Website" in km.ly_do_khong_web(ma_web))


@ca("v662 thu online xong: đơn giao của quầy đi don_quay.sau_thu, không ghi Pancake, không báo Sales; đơn đặt bánh vẫn đi như cũ")
def _():
	import types
	import unittest.mock as um

	from vagabond import don_quay, thanh_toan_web as tw
	from vagabond import thanh_toan_web_thuan as ttt

	def doc(kenh):
		return types.SimpleNamespace(vgb_tt_trang_thai=ttt.TT_DA_THU, vgb_tt_bao_luc=None, get=lambda k, d=None: kenh if k == "vgb_kenh" else d)

	for kenh, vao_quay, ghi in (("WEBORDER", 1, 0), ("", 0, 1)):
		with um.patch.object(tw, "_doc", return_value=doc(kenh)), \
				um.patch.object(don_quay, "sau_thu") as sq, \
				um.patch.object(tw, "ghi_pancake", side_effect=RuntimeError("dừng sau khi gọi")) as gp:
			tw.sau_thu("DW-2026-00001")
		la("kênh %r: vào quầy, ghi Pancake" % kenh, (sq.call_count, gp.call_count), (vao_quay, ghi))
	dung("đọc được ô kênh", "vgb_kenh" in tw.F_DOC)


@ca("v662 thẻ đơn và tin cho quầy: đủ món, cách nhận, số đã trả; tin nói khách đã trả và việc cần làm")
def _():
	d = _dq()
	snap = {"dia_chi": "12 Lê Lợi", "phi": {"phi_khach": 22000}, "uu_dai": {"giam": 10000},
		"weborder": {"dong": [{"ten": "Mousse", "sl": 2, "tc_chu": "", "tp": []}, {"ten": "Trà", "sl": 1, "tc_chu": "Ít đá", "tp": [{"ten": "Thạch"}]}]}}
	r = {"name": "DW-2026-00009", "vgb_tt_quay": d.TT_CHO_XN, "creation": "2026-11-15 10:05:00", "ho_ten": "Lan", "dien_thoai": "0909",
		"tu_lay": 0, "tien_banh": 235000, "vgb_tt_da_thu": 247000, "vgb_tt_cach": "Chuyển khoản"}
	t = d.the_don(r, snap)
	la("thẻ", [t["ma"], t["tt"], t["dia_chi"], [m["ten"] for m in t["mon"]], t["mon"][1]["tp"], t["phi"], t["giam"], t["da_thu"]],
		["DW-2026-00009", d.TT_CHO_XN, "12 Lê Lợi", ["Mousse", "Trà"], ["Thạch"], 22000, 10000, 247000])
	tieu, dong = d.soan_tin_moi(r["name"], "District 1", r, snap, "https://x/ban-tai-quay")
	dung("tiêu đề", tieu.startswith("Đơn giao mới DW-2026-00009"))
	dung("đã trả", any("đã trả online" in x for x in dong))
	dung("giao tới", any(x.startswith("Giao tới: 12 Lê Lợi") for x in dong))


@ca("v662 trang khách Vue (node, Vue thật): tab Tại quầy không QR là đơn giao, chỉ món tick Giao, đặt gửi đúng dữ liệu, bấm hai lần gửi một đơn, giá cũ không đè giá mới")
def _():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/web_giao_662.mjs"], cwd=GOC, capture_output=True, text=True, timeout=120)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)


@ca("v662 trụ Zalo, Grab nổi: tự thu khi đè nút chính hoặc thanh nút dưới đáy, không đè thì hiện (node)")
def _():
	js = ("import('./vagabond/public/web_vue/banh/noi-dung.js').then(m => {"
		"const t = {top: 500, bottom: 620, left: 330, right: 390};"
		"const r = [m.kenhNoiNenThu(t, [{top: 600, bottom: 660, left: 0, right: 390}]),"
		"m.kenhNoiNenThu(t, [{top: 619, bottom: 660, left: 0, right: 390}]),"
		"m.kenhNoiNenThu(t, [{top: 100, bottom: 160, left: 0, right: 390}]),"
		"m.kenhNoiNenThu(t, []), m.kenhNoiNenThu(null, [{top: 0, bottom: 1, left: 0, right: 1}]), m.KENH_NOI_DUNG_MS];"
		"console.log(JSON.stringify(r)); })")
	r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=GOC, capture_output=True, text=True, timeout=60)
	la("đè, chạm mép, không đè, rỗng, chưa đo, nhịp dừng", r.stdout.strip(), "[true,false,false,false,false,600]")


# ------------------------------------------------------- Codex #573 (review 95b6a14a3)

class _Vet:
	"""Ghi lại thứ tự các việc chạm cơ sở dữ liệu trong một lượt."""

	def __init__(self):
		self.su = []


def _moi_truong_tao_don(vet, tinh, km=None, tao_ten="DW-2611-00001"):
	"""Dựng tao_don với các lớp chạm hệ thay bằng bản giả ghi vết. `tinh` là
	danh sách kết quả _tinh lần lượt (lần sau cùng dùng lại)."""
	import types
	import unittest.mock as um

	import frappe

	from vagabond import don_quay, don_web, goi_mon_ban, khuyen_mai, onepay

	lan = {"i": 0}

	def _tinh(raw, chi_xem=False):
		i = min(lan["i"], len(tinh) - 1)
		lan["i"] += 1
		kq = dict(tinh[i])
		return kq, None

	km = km or {}
	ps = [
		um.patch.object(don_web, "nonce_hop_le", return_value=True),
		um.patch.object(don_web, "khoa_chong_trung", return_value="KHOA"),
		um.patch.object(don_web, "tim_trung", return_value=None),
		um.patch.object(don_web, "tao_ban_ghi", side_effect=lambda n, d: (vet.su.append(("ghi", d.get("vgb_kenh"))), types.SimpleNamespace(name=tao_ten))[1]),
		um.patch.object(don_web, "phan_hoi", side_effect=lambda b, n, trung=False: {"ok": 1, "ma_yeu_cau": b.name}),
		um.patch.object(don_quay, "_diem_giao", return_value={"ma": "TCV", "ten": "Cửa hàng Sài Gòn", "dia_chi": "1 Đồng Khởi"}),
		um.patch.object(goi_mon_ban, "_gio_mo_cua", return_value=True),
		um.patch.object(don_quay, "_khoa", side_effect=lambda t, g=10: vet.su.append(("khoa", t)) or True),
		um.patch.object(don_quay, "_nha", side_effect=lambda t: vet.su.append(("nha", t))),
		um.patch.object(don_quay, "_tinh", side_effect=_tinh),
		um.patch.object(onepay, "dung_duoc", return_value=False),
		um.patch.object(frappe.db, "commit", side_effect=lambda *a, **k: vet.su.append("commit")),
		um.patch.object(frappe.db, "rollback", side_effect=lambda *a, **k: vet.su.append("rollback")),
		um.patch.object(frappe.db, "set_value", side_effect=lambda *a, **k: vet.su.append(("set", a[1] if len(a) > 1 else None))),
		um.patch.object(khuyen_mai, "khoa_ctkm", side_effect=lambda ds: vet.su.append(("khoa_ctkm", list(ds)))),
		um.patch.object(khuyen_mai, "ma_dung_mot_lan", side_effect=km.get("mot_lan", lambda m: False)),
		um.patch.object(khuyen_mai, "giu_ma_mot_lan", side_effect=km.get("giu_ma", lambda m, gc: vet.su.append(("giu_ma", m, gc)) or True)),
		um.patch.object(khuyen_mai, "giu_luot_web", side_effect=km.get("giu_luot", lambda kq, **k: vet.su.append(("giu_luot", k.get("ghi_chu"), k.get("sdt"))))),
	]
	return ps


def _kq(tien=95000, giam=0, phi=22000, tu_lay=False, ap=None, ma=""):
	return {"ok": 1, "diem": {"ma": "TCV", "ten": "Cửa hàng Sài Gòn"}, "dong": [{"ma": "BK1", "ten": "Mousse", "sl": 1, "gia": tien, "loai": "banh"}],
		"tien_hang": tien, "giam": giam, "uu": {"tong_giam": giam, "ap": ap or [], "kq": {"ap": [dict(a, loai="ctkm") for a in ap or []]}},
		"phi": None if tu_lay else phi, "phi_day_du": {"phi_khach": 0 if tu_lay else phi, "trang_thai": "chinh_xac"},
		"trang_thai_phi": "chinh_xac", "nguong": 500000, "tu_lay": tu_lay, "dia_chi": "" if tu_lay else "12 Lê Lợi, Quận 1",
		"sdt": "0909123456", "ma": ma, "loi_ma": ""}


def _don_gui(**k):
	d = {"nonce": "n" * 32, "dong_y": True, "ho_ten": "Lan", "dien_thoai": "0909123456", "diem": "TCV",
		"mon": [{"ma": "BK1", "sl": 1}], "tien_hang_da_xem": 95000, "giam_da_xem": 0, "phi_da_xem": 22000, "thanh_toan": "bank"}
	d.update(k)
	return json.dumps(d)


def _chay(ps, ham):
	import contextlib

	with contextlib.ExitStack() as st:
		for p in ps:
			st.enter_context(p)
		return ham()


@ca("Codex #573 (H8 loại 3): giá món đổi giữa lúc xem giá và lúc Đặt thì KHÔNG tạo đơn, trả tổng mới (gia_doi); số khớp thì tạo")
def _():
	d = _dq()
	vet = _Vet()
	kq = _chay(_moi_truong_tao_don(vet, [_kq(tien=120000)]), lambda: d.tao_don(_don_gui()))
	la("đổi giá món", (kq.get("ok"), kq.get("ly_do"), kq.get("tien_hang")), (0, "gia_doi", 120000))
	dung("không ghi đơn", not any(x[0] == "ghi" for x in vet.su if isinstance(x, tuple)))
	vet = _Vet()
	kq = _chay(_moi_truong_tao_don(vet, [_kq()]), lambda: d.tao_don(_don_gui()))
	la("số khớp: tạo đơn", (kq.get("ok"), kq.get("ma_yeu_cau")), (1, "DW-2611-00001"))
	# Bảng chốt so_da_doi: thiếu số đã xem là đổi; tự lấy không xét phí.
	la("thiếu tiền món đã xem", d.so_da_doi(_kq(), {"giam_da_xem": 0, "phi_da_xem": 22000}), True)
	la("tự lấy không xét phí", d.so_da_doi(_kq(tu_lay=True), {"tien_hang_da_xem": "95000", "giam_da_xem": 0, "phi_da_xem": None}), False)
	la("giảm đổi", d.so_da_doi(_kq(giam=10000), {"tien_hang_da_xem": 95000, "giam_da_xem": 0, "phi_da_xem": 22000}), True)
	la("phí đổi", d.so_da_doi(_kq(phi=30000), {"tien_hang_da_xem": 95000, "giam_da_xem": 0, "phi_da_xem": 22000}), True)


@ca("Codex #573 (H8 loại 1, 4): đơn có ưu đãi giữ lượt và mã dùng một lần CÙNG giao dịch ghi đơn, sau khi khoá chương trình và tính lại; mã vừa bị đơn khác giữ thì rollback, không ghi đơn")
def _():
	d = _dq()
	ap = [{"ma": "WEB-DON-DAU", "ten": "Đơn giao đầu tiên", "giam": 20000}]
	vet = _Vet()
	kq = _chay(_moi_truong_tao_don(vet, [_kq(giam=20000, ap=ap, ma="GIAOLANDAU")]),
		lambda: d.tao_don(_don_gui(giam_da_xem=20000, ma_uu_dai="GIAOLANDAU")))
	la("tạo đơn", kq.get("ok"), 1)
	su = [x for x in vet.su if x != "commit" or True]
	i_khoa = su.index(("khoa_ctkm", ["WEB-DON-DAU"]))
	dung("commit ngay trước khi khoá chương trình (bỏ ảnh chụp đọc cũ)", su[i_khoa - 1] == "commit")
	i_ghi = [k for k, x in enumerate(su) if isinstance(x, tuple) and x[0] == "ghi"][0]
	i_luot = su.index(("giu_luot", "Đơn web DW-2611-00001", "0909123456"))
	dung("khoá chương trình trước khi ghi đơn, ghi lượt sau khi có mã đơn", i_khoa < i_ghi < i_luot)
	dung("commit sau khi ghi lượt (cùng giao dịch với đơn)", "commit" in su[i_luot:])
	# Mã dùng một lần vừa bị đơn khác giữ.
	vet = _Vet()
	kq = _chay(_moi_truong_tao_don(vet, [_kq(giam=20000, ap=ap, ma="THE01")],
		km={"mot_lan": lambda m: True, "giu_ma": lambda m, gc: False}),
		lambda: d.tao_don(_don_gui(giam_da_xem=20000, ma_uu_dai="THE01")))
	la("chặn", (kq.get("ok"), kq.get("cau")), (0, "Mã THE01 vừa được dùng cho một đơn khác."))
	i_rb = vet.su.index("rollback")
	dung("rollback trước mọi commit sau khi ghi", "commit" not in vet.su[[k for k, x in enumerate(vet.su) if isinstance(x, tuple) and x[0] == "ghi"][0]:i_rb])
	# Tính lại dưới khoá ra chương trình khác (đơn khác vừa lấy lượt cuối): dừng.
	vet = _Vet()
	kq = _chay(_moi_truong_tao_don(vet, [_kq(giam=20000, ap=ap), _kq()]), lambda: d.tao_don(_don_gui(giam_da_xem=20000)))
	la("ưu đãi vừa đổi", (kq.get("ok"), kq.get("ly_do"), kq.get("giam")), (0, "gia_doi", 0))
	dung("không ghi đơn", not any(isinstance(x, tuple) and x[0] == "ghi" for x in vet.su))


@ca("Codex #573: cùng số điện thoại đặt đơn thứ hai thì KHÔNG dùng lại được mã Đơn giao đầu tiên (lượt đơn đầu đã ghi theo số)")
def _():
	d = _dq()
	luot = {}

	def tinh_theo_luot(raw, chi_xem=False):
		# Bộ tính giả theo đúng luật lan_moi_khach = 1: số đã có lượt thì báo lý do.
		sdt = json.loads(raw)["dien_thoai"] if isinstance(raw, str) else raw["dien_thoai"]
		if luot.get(sdt):
			return None, "Mã GIAOLANDAU: số điện thoại này đã dùng hết 1 lượt."
		return _kq(giam=20000, ap=[{"ma": "WEB-DON-DAU", "ten": "Đơn đầu", "giam": 20000}], ma="GIAOLANDAU"), None

	def giu_luot(kq, **k):
		luot[k.get("sdt")] = luot.get(k.get("sdt"), 0) + 1

	import unittest.mock as um

	vet = _Vet()
	ps = _moi_truong_tao_don(vet, [_kq()], km={"giu_luot": giu_luot})
	from vagabond import don_quay

	ps.append(um.patch.object(don_quay, "_tinh", side_effect=tinh_theo_luot))
	gui = _don_gui(giam_da_xem=20000, ma_uu_dai="GIAOLANDAU")
	k1 = _chay(ps, lambda: d.tao_don(gui))
	ps = _moi_truong_tao_don(vet, [_kq()], km={"giu_luot": giu_luot}, tao_ten="DW-2611-00002")
	ps.append(um.patch.object(don_quay, "_tinh", side_effect=tinh_theo_luot))
	k2 = _chay(ps, lambda: d.tao_don(_don_gui(giam_da_xem=20000, ma_uu_dai="GIAOLANDAU", nonce="m" * 32)))
	la("đơn đầu được giảm", k1.get("ok"), 1)
	la("đơn thứ hai bị chặn", (k2.get("ok"), k2.get("cau")), (0, "Mã GIAOLANDAU: số điện thoại này đã dùng hết 1 lượt."))


def _moi_truong_quay(vet, r, tao=None):
	import unittest.mock as um

	import frappe

	import sys
	import types

	import vagabond
	from vagabond import don_quay, goi_mon_ban, khuyen_mai

	# ban_hang kéo requests ở đầu tệp: bộ kiểm tầng khung không nạp nó, thay bằng mô đun giả.
	ban_hang = types.ModuleType("vagabond.ban_hang")
	co = {}

	def tao_don_tay(**k):
		co["gia_chot"] = bool(frappe.flags.get("vgb_gia_chot"))
		co["items"] = k.get("items")
		vet.su.append("tao_bill")
		return (tao or (lambda k: {"name": "BILL-1", "grand_total": 107000}))(k)

	return co, [
		um.patch.object(don_quay, "_kiem_quyen", return_value=None),
		um.patch.object(don_quay, "_khoa", side_effect=lambda t, g=10: vet.su.append(("khoa", t)) or True),
		um.patch.object(don_quay, "_nha", side_effect=lambda t: vet.su.append(("nha", t))),
		um.patch.object(don_quay, "_doc_khoa", side_effect=lambda ma: dict(r)),
		um.patch.object(don_quay, "_diem_giao", return_value={"ma": "TCV", "ten": "Cửa hàng Sài Gòn", "nguon": ["Mang về - Sài Gòn"]}),
		um.patch.object(goi_mon_ban, "ma_bill_moi", return_value="TCV-001"),
		um.patch.dict(sys.modules, {"vagabond.ban_hang": ban_hang}),
		um.patch.object(vagabond, "ban_hang", ban_hang, create=True),
		um.patch.object(ban_hang, "tao_don_tay", side_effect=tao_don_tay, create=True),
		um.patch.object(khuyen_mai, "gan_hoa_don_web", side_effect=lambda gc, si: vet.su.append(("gan", gc, si))),
		um.patch.object(khuyen_mai, "tra_luot_web", side_effect=lambda gc: vet.su.append(("tra", gc))),
		um.patch.object(frappe, "delete_doc", side_effect=lambda dt, ten, **k: vet.su.append(("xoa", ten)), create=True),
		um.patch.object(frappe.db, "commit", side_effect=lambda *a, **k: vet.su.append("commit")),
		um.patch.object(frappe.db, "set_value", side_effect=lambda *a, **k: vet.su.append(("set", a[0], a[1], a[2] if len(a) > 2 else None))),
	]


def _ban_ghi_xn(**k):
	snap = {"weborder": {"dong": [{"ma": "BK1", "ten": "Mousse", "sl": 1, "gia": 95000, "loai": "banh"}]},
		"uu_dai": {"ma": "GIAOLANDAU", "giam": 10000}, "phi": {"phi_khach": 22000}}
	r = {"name": "DW-2611-00001", "vgb_kenh": "WEBORDER", "vgb_diem": "TCV", "vgb_tt_quay": "Chờ quầy xác nhận",
		"tien_banh": 95000, "tu_lay": 0, "ho_ten": "Lan", "dien_thoai": "0909123456", "vgb_tt_da_thu": 107000,
		"vgb_tt_cach": "Chuyển khoản", "snapshot": json.dumps(snap)}
	r.update(k)
	return r


@ca("Codex #573: Xác nhận lập phiếu GIỮ giá khách đã trả (cờ giá chốt), nối lượt ưu đãi với phiếu; tổng phiếu lệch số đã trả thì xoá phiếu nháp, KHÔNG đổi trạng thái")
def _():
	import frappe

	d = _dq()
	vet = _Vet()
	co, ps = _moi_truong_quay(vet, _ban_ghi_xn())
	kq = _chay(ps, lambda: d.xac_nhan("DW-2611-00001", 15))
	la("xác nhận", (kq.get("ok"), kq.get("bill")), (1, "BILL-1"))
	la("cờ giá chốt bật đúng lúc lập phiếu, tắt sau đó", (co["gia_chot"], bool(frappe.flags.get("vgb_gia_chot"))), (True, False))
	la("giá dòng là giá đã chốt", [x["rate"] for x in co["items"]], [95000.0])
	dung("nối lượt với phiếu", ("gan", "Đơn web DW-2611-00001", "BILL-1") in vet.su)
	vet = _Vet()
	co, ps = _moi_truong_quay(vet, _ban_ghi_xn(), tao=lambda k: {"name": "BILL-2", "grand_total": 132000})
	try:
		_chay(ps, lambda: d.xac_nhan("DW-2611-00001", 15))
		dung("phải báo lệch tổng", False)
	except frappe.ValidationError as e:
		dung("câu nói hai con số", "132.000" in str(e) and "107.000" in str(e))
	dung("xoá phiếu nháp lệch", ("xoa", "BILL-2") in vet.su)
	dung("không đổi trạng thái đơn", not any(isinstance(x, tuple) and x[0] == "set" and x[1] == "Vagabond Don Web" for x in vet.su))
	dung("vẫn nhả khoá đơn", ("nha", "vagabond:weborder-don:DW-2611-00001") in vet.su)


@ca("Codex #573 (H8 loại 1): Xác nhận, Từ chối, Đã giao, Gọi xe đều chạy trong khoá phiên theo mã đơn (giữ qua commit của tao_don_tay); Từ chối trả lượt ưu đãi đã giữ")
def _():
	d = _dq()
	vet = _Vet()
	co, ps = _moi_truong_quay(vet, _ban_ghi_xn())
	_chay(ps, lambda: d.xac_nhan("DW-2611-00001", 10))
	k = vet.su.index(("khoa", "vagabond:weborder-don:DW-2611-00001"))
	n = vet.su.index(("nha", "vagabond:weborder-don:DW-2611-00001"))
	dung("lập phiếu và đổi trạng thái nằm giữa khoá và nhả", k < vet.su.index("tao_bill") < n
		and k < [i for i, x in enumerate(vet.su) if isinstance(x, tuple) and x[0] == "set" and x[1] == "Vagabond Don Web"][0] < n)
	vet = _Vet()
	co, ps = _moi_truong_quay(vet, _ban_ghi_xn())
	_chay(ps, lambda: d.tu_choi("DW-2611-00001", "Hết món"))
	dung("từ chối trong khoá", ("khoa", "vagabond:weborder-don:DW-2611-00001") in vet.su)
	dung("trả lượt ưu đãi của đơn", ("tra", "Đơn web DW-2611-00001") in vet.su)
	vet = _Vet()
	co, ps = _moi_truong_quay(vet, _ban_ghi_xn(vgb_tt_quay="Đã xác nhận"))
	_chay(ps, lambda: d.xong("DW-2611-00001"))
	dung("đã giao trong khoá", ("khoa", "vagabond:weborder-don:DW-2611-00001") in vet.su)
	import unittest.mock as um

	from vagabond import don_quay

	vet = _Vet()
	with um.patch.object(don_quay, "_kiem_quyen", return_value=None), \
			um.patch.object(don_quay, "_khoa", side_effect=lambda t, g=10: vet.su.append(("khoa", t)) or True), \
			um.patch.object(don_quay, "_nha", side_effect=lambda t: vet.su.append(("nha", t))), \
			um.patch.object(don_quay, "_goi_xe_trong_khoa", side_effect=lambda ma, g: vet.su.append("goi")):
		d.goi_xe("DW-2611-00001", "F1")
	la("gọi xe trong khoá", vet.su, [("khoa", "vagabond:weborder-don:DW-2611-00001"), "goi", ("nha", "vagabond:weborder-don:DW-2611-00001")])


@ca("Codex #573: lập phiếu tay thường vẫn đặt lại giá theo bảng giá điểm; chỉ khi máy chủ bật cờ giá chốt (đơn giao đã trả) thì giữ giá dòng")
def _():
	import frappe

	from vagabond import diem_ban

	items = [{"item_code": "BK1", "rate": 95000}]
	rows = [{"item_code": "BK1", "rate": 95000}]
	la("không cờ: theo giá điểm", (diem_ban.ap_gia_diem(items, rows, {"BK1": 120000}), rows[0]["rate"]), (1, 120000))
	items = [{"item_code": "BK1", "rate": 95000}]
	rows = [{"item_code": "BK1", "rate": 95000}]
	frappe.flags.vgb_gia_chot = True
	try:
		la("cờ giá chốt: giữ giá đã thu", (diem_ban.ap_gia_diem(items, rows, {"BK1": 120000}), rows[0]["rate"], items[0]["rate"]), (0, 95000, 95000))
	finally:
		frappe.flags.vgb_gia_chot = False


@ca("Codex #573 (H8 loại 3): bánh đơn giao trừ ĐÚNG MỘT lần: phiếu đã chốt thì thôi giữ (da_ban đã trừ); phiếu còn tạm tính thì vẫn giữ kể cả đã bấm Đã giao; phiếu huỷ thì theo trạng thái")
def _():
	import unittest.mock as um

	import frappe

	d = _dq()
	bay = dt.datetime(2026, 8, 15, 9, 0)
	la("bảng", [d.giu_theo_bill(d.TT_XN, bay, bay, d.BILL_CHOT), d.giu_theo_bill(d.TT_XONG, bay, bay, d.BILL_TAM),
		d.giu_theo_bill(d.TT_XN, bay, bay, None), d.giu_theo_bill(d.TT_XONG, bay, bay, d.BILL_HUY), d.giu_theo_bill(d.TT_XN, bay, bay, d.BILL_HUY),
		d.giu_theo_bill(d.TT_TU_CHOI, bay, bay, d.BILL_TAM)], [False, True, True, False, True, False])
	la("trạng thái phiếu", [d.tt_bill({"docstatus": 0, "vgb_tam_tinh": 1}), d.tt_bill({"docstatus": 1, "vgb_tam_tinh": 0}),
		d.tt_bill({"docstatus": 0, "vgb_tam_tinh": 0, "vgb_huy": 1}), d.tt_bill({"docstatus": 2}), d.tt_bill(None)],
		[d.BILL_TAM, d.BILL_CHOT, d.BILL_HUY, d.BILL_HUY, None])
	sn = lambda ma, sl: json.dumps({"weborder": {"dong": [{"ma": ma, "loai": "banh", "sl": sl}]}})
	don = [{"name": "D1", "vgb_tt_quay": d.TT_XN, "creation": bay, "snapshot": sn("BK1", 1), "vgb_bill_quay": "B1"},
		{"name": "D2", "vgb_tt_quay": d.TT_XONG, "creation": bay, "snapshot": sn("BK2", 2), "vgb_bill_quay": "B2"},
		{"name": "D3", "vgb_tt_quay": d.TT_CHO_XN, "creation": bay, "snapshot": sn("BK3", 3), "vgb_bill_quay": None},
		{"name": "D4", "vgb_tt_quay": d.TT_XONG, "creation": bay, "snapshot": sn("BK4", 4), "vgb_bill_quay": "B4"}]
	bill = [{"name": "B1", "docstatus": 0, "vgb_tam_tinh": 0, "vgb_huy": 0}, {"name": "B2", "docstatus": 0, "vgb_tam_tinh": 1, "vgb_huy": 0},
		{"name": "B4", "docstatus": 1, "vgb_tam_tinh": 0, "vgb_huy": 0}]
	with um.patch.object(frappe, "get_all", side_effect=lambda dt_, **k: bill if dt_ == "Sales Invoice" else don):
		la("giữ", d.giu_cua_diem("TCV"), {"BK2": 2, "BK3": 3})


@ca("Codex #573 (AGENTS.md 2b.3, 2b.5, 2b.6): màn Đơn giao của quầy chạy thật (node): ba hàng chip có đếm, ô tìm bỏ dấu, thẻ tóm tắt bấm số là lọc, Tổng theo bộ lọc, chip 44 điểm, câu lỗi")
def _():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/don_giao_quay_663.js"], cwd=GOC, capture_output=True, text=True, timeout=120)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)


@ca("Codex #573: khoảng ngày màn Đơn giao của quầy chỉ 24 giờ hoặc 7 ngày; giá trị lạ về 24 giờ")
def _():
	d = _dq()
	la("chuẩn", [d.chuan_ngay_xem(x) for x in (1, "7", 30, None, "abc", 0)], [1, 7, 1, 1, 1, 1])


@ca("Codex #573: việc dọn định kỳ trả lượt ưu đãi cả đơn giao của quầy bị từ chối hoặc khách bỏ không trả quá một ngày (lưới an toàn cho lần trả ngay)")
def _():
	import types

	from vagabond import don_quay
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap

	goi, tra = [], []

	def sql(q, v=None, **k):
		goi.append((" ".join(q.split()), v))
		return [("Đơn web DW-2611-00009",)]

	g = dict(frappe=types.SimpleNamespace(db=types.SimpleNamespace(sql=sql, commit=lambda: None, rollback=lambda: None),
			log_error=lambda *a, **k: None, get_traceback=lambda: ""),
		khuyen_mai=types.SimpleNamespace(tra_luot_web=lambda gc: tra.append(gc)))
	ham = nap("don_hang.py", "_tra_luot_don_huy", g)
	la("trả", (ham(), tra), (1, ["Đơn web DW-2611-00009"]))
	q, v = goi[0]
	dung("vẫn giữ đơn Đã huỷ", "d.trang_thai='Da huy'" in q)
	dung("thêm đơn WEBORDER từ chối hay chưa trả quá một ngày", "vgb_kenh" in q and "interval 1 day" in q)
	la("tham số", v, (don_quay.KENH, don_quay.TT_TU_CHOI, don_quay.TT_CHO_TRA))
