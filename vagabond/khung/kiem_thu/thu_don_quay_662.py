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
