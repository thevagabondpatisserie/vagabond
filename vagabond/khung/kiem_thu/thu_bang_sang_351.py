# -*- coding: utf-8 -*-
"""#351 đợt 1: màn Việc hôm nay (Bảng sáng) và thẻ Nhận định trên BC08.

Anh Việt 21/09/2026: mỗi sáng không biết giao việc gì cho các bộ phận. Máy
đọc số bán ba tuần, lô sắp hết hạn và bảng kiểm bánh ngày mai, nháp sẵn nhận
định; quản lý bấm Giao việc (thành Task thật) hoặc Bỏ qua (có lý do, có ngày
nhắc lại).

Các ca ở đây chốt ĐÚNG những cái bẫy Codex nêu ở issue #351:
  - từ 1 lên 2 không được gọi là tăng 100%: ngưỡng mẫu, ngưỡng tuyệt đối;
  - "giảm hai tuần liền" cần ba cửa sổ và hai lần so sánh;
  - không trừ đơn đặt hai lần ở luật thiếu thành phẩm;
  - lô chỉ tính số còn tại đúng kho, quá hạn tách khỏi cận hạn;
  - bấm Giao hai lần hay hai người cùng bấm chỉ ra MỘT việc;
  - giao không được thì báo lỗi, không báo thành công giả;
  - lọc theo vai ở máy chủ, marketing không nhận số lô của kho.
Phần chạy trên trình duyệt kiểm ở hanh_vi/bang_sang_351.js.
"""

import datetime
import io
import json
import os
import sys
import types
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import phan_tich as pt
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = datetime.date


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("#351: món bán là bánh và đồ uống, bỏ phụ kiện và dịch vụ; ba cửa sổ bảy ngày")
def _mon_va_cua_so():
	la("bánh nướng", pt.la_mon_ban("BANU00021"), True)
	la("đồ uống", pt.la_mon_ban("nutr00007"), True)
	la("dĩa giấy là phụ kiện", pt.la_mon_ban("BAPK00020"), False)
	la("phí giao là dịch vụ", pt.la_mon_ban("DVBH00001"), False)
	la("nguyên liệu", pt.la_mon_ban("NVLT00104"), False)
	la("hộp Trung thu là hàng mùa", (pt.la_mon_ban("BASS00038"), pt.la_mua_vu("BASS00038")), (True, True))
	cs = pt.cua_so_tuan("2026-09-20")
	la("ba cửa sổ liền nhau", cs, [
		(D(2026, 8, 31), D(2026, 9, 6)), (D(2026, 9, 7), D(2026, 9, 13)), (D(2026, 9, 14), D(2026, 9, 20))])
	la("ngày rơi vào tuần gần", pt.tuan_cua("2026-09-14", cs), 2)
	la("ngày ngoài ba tuần", pt.tuan_cua("2026-08-30", cs), None)


def _hd():
	return {
		"A": {"posting_date": "2026-09-15", "nguon": "GrabFood", "diem": "TCV"},
		"B": {"posting_date": "2026-09-09", "nguon": "Tại chỗ", "diem": "TCV"},
		"C": {"posting_date": "2026-09-16", "nguon": "Sales Online", "diem": "SALES"},
		"R": {"posting_date": "2026-09-17", "nguon": "Tại chỗ", "diem": "TCV"},
	}


@ca("#351: gom bán theo tuần là lượng RÒNG, tách nguồn, bỏ phụ kiện, lọc đơn không quầy")
def _gom():
	cs = pt.cua_so_tuan("2026-09-20")
	dong = [
		{"parent": "A", "item_code": "BANU1", "item_name": "Croissant", "qty": 10},
		{"parent": "B", "item_code": "BANU1", "item_name": "Croissant", "qty": 4},
		{"parent": "C", "item_code": "BANU1", "item_name": "Croissant", "qty": 6},
		{"parent": "R", "item_code": "BANU1", "item_name": "Croissant", "qty": -2},
		{"parent": "A", "item_code": "BAPK00020", "item_name": "Dĩa", "qty": 50},
		{"parent": "X", "item_code": "BANU1", "item_name": "Croissant", "qty": 99},
	]
	b = pt.gom_ban(dong, _hd(), cs)
	la("không có phụ kiện", sorted(b), ["BANU1"])
	la("tuần giữa 4, tuần gần 10+6-2", b["BANU1"]["q"], [0.0, 4.0, 14.0])
	la("tách theo nguồn tuần gần", b["BANU1"]["nguon"][2], {"GrabFood": 10.0, "Sales Online": 6.0, "Tại chỗ": -2.0})
	q = pt.gom_ban(dong, _hd(), cs, chi_quay=True)
	la("chỉ quầy thì bỏ đơn Sales Online", q["BANU1"]["q"], [0.0, 4.0, 8.0])


@ca("#351: luật tăng cần đủ mẫu, đủ chênh tuyệt đối, đủ phần trăm, nằm top; gốc 0 là món mới")
def _tang():
	n = pt.NGUONG
	la("20 lên 28: +8, +40%", pt.xet_tang([0, 20, 28], 1, n), "tang")
	la("20 lên 27: chỉ +7", pt.xet_tang([0, 20, 27], 1, n), None)
	la("30 lên 38: +8 nhưng chỉ 26%", pt.xet_tang([0, 30, 38], 1, n), None)
	la("1 lên 2 không phải xu hướng", pt.xet_tang([0, 1, 2], 1, n), None)
	la("ngoài top 20 thì thôi", pt.xet_tang([0, 20, 28], 21, n), None)
	la("hai tuần trước chưa bán, tuần này 12: món mới", pt.xet_tang([0, 0, 12], 50, n), "moi")
	la("món mới mà mới 11 cái thì chưa", pt.xet_tang([0, 0, 11], 1, n), None)
	la("tuần giữa 0 mà tuần cũ có bán thì không gọi là mới", pt.xet_tang([5, 0, 20], 1, n), None)


@ca("#351: luật giảm cần HAI lần giảm liền nhau và giảm đủ 30% và 8 cái so với tuần cũ")
def _giam():
	n = pt.NGUONG
	la("40 → 31 → 22", pt.xet_giam([40, 31, 22], n), True)
	la("40 → 31 → 33 không liền", pt.xet_giam([40, 31, 33], n), False)
	la("40 → 45 → 22 lần đầu tăng", pt.xet_giam([40, 45, 22], n), False)
	la("12 → 11 → 10 giảm quá ít", pt.xet_giam([12, 11, 10], n), False)
	la("30 → 25 → 22 chỉ 26%", pt.xet_giam([30, 25, 22], n), False)
	la("tuần gốc dưới mẫu", pt.xet_giam([11, 5, 1], n), False)


@ca("#351: nhận định xu hướng ghi rõ số, kênh kéo tăng giảm, và bỏ hàng mùa khỏi luật giảm")
def _xu_huong():
	ban = {
		"BANU14": {"ten": "Croissant Tiramisu", "q": [60.0, 70.0, 105.0],
			"nguon": [{}, {"Tại chỗ": 40, "GrabFood": 30}, {"Tại chỗ": 42, "GrabFood": 63}]},
		"BAEN51": {"ten": "Slice Tiramisu", "q": [40.0, 31.0, 22.0],
			"nguon": [{"ShopeeFood": 20, "Tại chỗ": 20}, {}, {"ShopeeFood": 2, "Tại chỗ": 20}]},
		"BASS38": {"ten": "Hộp Moongarden", "q": [400.0, 300.0, 50.0], "nguon": [{}, {}, {}]},
	}
	nd = {x["luat"] + "|" + x["doi"]["ma"]: x for x in pt.nhan_dinh_xu_huong(ban, {"BANU14": "/a.jpg"}, ["a", "b", "c"])}
	dung("có món tăng", "mon_tang|BANU14" in nd)
	x = nd["mon_tang|BANU14"]
	la("câu có số", x["cau"], "Tuần qua bán 105, tuần trước 70 (tăng 35, +50%). Phần tăng chủ yếu đến từ GrabFood.")
	la("khoá theo món, phạm vi cả tiệm", x["khoa"], "mon_tang|BANU14|tat_ca")
	la("ảnh món", x["doi"]["anh"], "/a.jpg")
	la("chuỗi ba tuần cho cột", x["so_lieu"]["chuoi"], [60, 70, 105])
	y = nd["mon_giam|BAEN51"]
	dung("giảm có chữ cần kiểm tra, không kết luận chất lượng", "Kiểm tra trước khi kết luận" in y["goi_y"] and "chất lượng" not in y["goi_y"])
	dung("chỉ ra kênh giảm", y["cau"].endswith("Phần giảm chủ yếu ở ShopeeFood."))
	la("hàng mùa không vào luật giảm", [k for k in nd if k.endswith("BASS38")], [])
	la("mức và bộ phận của luật giảm", (y["muc"], y["bo_phan"]), ("vua", ["marketing", "bep"]))


@ca("#351: thiếu thành phẩm dùng số CÓ THỂ BÁN của kiểm bánh và bán TẠI QUẦY, không trừ đơn đặt hai lần")
def _thieu():
	ban_quay = {
		"BAWC55": {"ten": "Mille Crepe", "q": [0, 0, 42.0]},    # 6 cái/ngày tại quầy
		"BAWC10": {"ten": "Ổ ít bán", "q": [0, 0, 7.0]},        # 1 cái/ngày: dưới ngưỡng
		"BAWC20": {"ten": "Ổ đủ", "q": [0, 0, 21.0]},           # 3 cái/ngày
	}
	kb = [
		{"ma_hang": "BAWC55", "ten_banh": "Mille Crepe", "hinh": "/m.jpg", "co_the_ban": 2, "da_dat": 1, "sx": 3},
		{"ma_hang": "BAWC10", "co_the_ban": -4, "da_dat": 5, "sx": 0},
		{"ma_hang": "BAWC20", "co_the_ban": 2, "da_dat": 0, "sx": 2},
		{"ma_hang": "BAWC99", "co_the_ban": 0, "da_dat": 9, "sx": 0},
	]
	nd = pt.nhan_dinh_thieu(kb, ban_quay, D(2026, 9, 22))
	la("chỉ món bán quầy đủ nhiều và thiếu ít nhất 2", [x["doi"]["ma"] for x in nd], ["BAWC55"])
	x = nd[0]
	la("thiếu 6 - 2 = 4", x["so_lieu"]["thieu"], 4)
	la("câu nêu đủ số", x["cau"], "Tại quầy bán trung bình 6 cái/ngày. Bảng kiểm bánh ngày 22/09 còn có thể bán 2 (đã trừ 1 đơn đặt, đã tính bếp đã lên 3).")
	la("khoá theo món và ngày", x["khoa"], "thieu_thanh_pham|BAWC55|2026-09-22")
	am = pt.nhan_dinh_thieu([{"ma_hang": "BAWC55", "co_the_ban": -3, "da_dat": 8, "sx": 5}], ban_quay, D(2026, 9, 22))
	dung("âm thì nói màn Gợi ý YCSX đã tính, không cộng lại phần âm", "đang âm 3 (màn Gợi ý YCSX đã tính phần này)" in am[0]["cau"])
	la("âm thì thiếu cho quầy là cả mức bán một ngày, không phải 6 + 3", am[0]["so_lieu"]["thieu"], 6)


@ca("#351: lô gộp theo kho, quá hạn tách cận hạn, chỉ tính lô còn hàng, ranh giới 7 ngày")
def _lo():
	lo = [
		{"lo": "L1", "ma": "NVLT00104", "ten": "Bơ", "kho": "Kho tổng 307 - TV", "han": "2024-01-21", "sl": 2000},
		{"lo": "L2", "ma": "NVLT00005", "ten": "Kem", "kho": "Kho tổng 307 - TV", "han": "2026-09-19", "sl": 3},
		{"lo": "L3", "ma": "NVLT00006", "ten": "Sữa", "kho": "Kho tổng 307 - TV", "han": "2026-09-27", "sl": 5},
		{"lo": "L4", "ma": "NVLT00007", "ten": "Trứng", "kho": "Kho tổng 307 - TV", "han": "2026-09-28", "sl": 5},
		{"lo": "L5", "ma": "NVLT00008", "ten": "Bột", "kho": "Pastry - Nguyên liệu - TV", "han": "2026-09-01", "sl": 0},
		{"lo": "L6", "ma": "NVLT00009", "ten": "Đường", "kho": "Pastry - Nguyên liệu - TV", "han": None, "sl": 9},
	]
	nd = pt.nhan_dinh_lo(lo, "2026-09-20")
	la("một kho quá hạn, một kho cận hạn", [x["khoa"] for x in nd], ["lo_can_han|Kho tổng 307 - TV|", "lo_qua_han|Kho tổng 307 - TV|"])
	q = [x for x in nd if x["luat"] == "lo_qua_han"][0]
	la("hai lô quá hạn", q["so_lieu"]["so_lo"], 2)
	la("tiêu đề ngắn tên kho", q["tieu_de"], "2 lô quá hạn ở Kho tổng 307")
	dung("quá hạn không gợi ý dùng hay bán", "cách ly" in q["goi_y"] and "không dùng, không bán" in q["goi_y"] and "không tự sửa" in q["goi_y"])
	c = [x for x in nd if x["luat"] == "lo_can_han"][0]
	la("27/09 là cận hạn, 28/09 thì chưa", [l["lo"] for l in c["so_lieu"]["lo"]], ["L3"])
	la("mức", (q["muc"], c["muc"]), ("cao", "vua"))


@ca("#351: xếp mức cao trước; lọc theo vai ở máy chủ, đếm đúng phạm vi")
def _vai():
	ds = pt.xep([
		{"khoa": "a", "muc": "vua", "diem": 5, "bo_phan": ["marketing"]},
		{"khoa": "b", "muc": "cao", "diem": 1, "bo_phan": ["kho"]},
		{"khoa": "c", "muc": "vua", "diem": 9, "bo_phan": ["marketing", "bep"]},
		{"khoa": "d", "muc": "thap", "diem": 99, "bo_phan": ["marketing"]},
	])
	la("thứ tự", [x["khoa"] for x in ds], ["b", "c", "a", "d"])
	la("marketing không thấy lô của kho", len(pt.loc_theo_vai(ds, ["Marketing"])), 3)
	la("kho chỉ thấy việc kho", [x["khoa"] for x in pt.loc_theo_vai(ds, ["Stock Manager"])], ["b"])
	la("bếp trưởng thấy việc có bếp", [x["khoa"] for x in pt.loc_theo_vai(ds, ["Bếp trưởng"])], ["c"])
	la("giám đốc thấy hết", len(pt.loc_theo_vai(ds, ["AP Giám đốc"])), 4)
	la("nhân viên thường không thấy gì", pt.loc_theo_vai(ds, ["Sales User"]), [])
	dung("quyền mở màn gồm vai giám đốc và vai xem", {"Giám đốc", "Marketing", "Stock Manager"} <= pt.QUYEN_BANG_SANG)
	dung("Sales User không mở được màn", "Sales User" not in pt.QUYEN_BANG_SANG)


@ca("#351: nhận định ẩn khi đang giao, đang bỏ qua, hoặc vừa xong trong số ngày của luật")
def _chia():
	nd = [
		{"khoa": "mon_tang|A|tat_ca", "luat": "mon_tang"},
		{"khoa": "mon_tang|B|tat_ca", "luat": "mon_tang"},
		{"khoa": "lo_qua_han|K|", "luat": "lo_qua_han"},
		{"khoa": "mon_giam|C|tat_ca", "luat": "mon_giam"},
		{"khoa": "mon_giam|E|tat_ca", "luat": "mon_giam"},
	]
	viec = [
		{"khoa": "mon_tang|A|tat_ca", "status": "Overdue"},
		{"khoa": "mon_tang|B|tat_ca", "status": "Completed", "completed_on": "2026-09-15"},
		{"khoa": "lo_qua_han|K|", "status": "Completed", "completed_on": "2026-09-19"},
		{"khoa": "mon_giam|C|tat_ca", "status": "Cancelled", "nhac_lai": "2026-09-22"},
		{"khoa": "mon_giam|E|tat_ca", "status": "Cancelled", "nhac_lai": "2026-09-20"},
	]
	con = [x["khoa"] for x in pt.chia_theo_viec(nd, viec, "2026-09-20")]
	la("A đang giao ẩn; B xong 5 ngày trước vẫn ẩn (7 ngày); lô xong hôm qua hiện lại; C còn bỏ qua; E tới ngày nhắc", con,
		["lo_qua_han|K|", "mon_giam|E|tat_ca"])
	la("lô quá hạn bỏ qua tối đa 3 ngày", pt.so_ngay_bo_qua("lo_qua_han", 14), 3)
	la("món giảm bỏ qua được 14", pt.so_ngay_bo_qua("mon_giam", 14), 14)
	la("ít nhất một ngày", pt.so_ngay_bo_qua("mon_tang", 0), 1)


@ca("#351: thẻ Nhận định BC08 so với kỳ trước, bỏ phụ kiện, giữ hai món mỗi chiều, đếm phần còn lại")
def _the_bc08():
	nay = [
		{"ma_mon": "BAPK00020", "mon": "Dĩa", "sl": 717}, {"ma_mon": "BANU1", "mon": "A", "sl": 60},
		{"ma_mon": "BANU2", "mon": "B", "sl": 50}, {"ma_mon": "BANU3", "mon": "C", "sl": 45},
		{"ma_mon": "BAEN1", "mon": "D", "sl": 10}, {"ma_mon": "BAEN2", "mon": "E", "sl": 5},
		{"ma_mon": "BANU9", "mon": "Mới", "sl": 30}, {"ma_mon": "BASS1", "mon": "Hộp", "sl": 1},
	]
	truoc = [
		{"ma_mon": "BAPK00020", "sl": 100}, {"ma_mon": "BANU1", "sl": 30}, {"ma_mon": "BANU2", "sl": 30},
		{"ma_mon": "BANU3", "sl": 30}, {"ma_mon": "BAEN1", "sl": 30}, {"ma_mon": "BAEN2", "sl": 20},
		{"ma_mon": "BASS1", "sl": 400},
	]
	t = pt.nhan_dinh_bao_cao_mon(nay, truoc, "Tuần 07/09 - 13/09/2026")
	la("hai món tăng mạnh nhất", [x["ma"] for x in t["tang"]], ["BANU1", "BANU2"])
	la("đếm đủ ba món tăng", t["so_tang"], 3)
	la("hai món giảm, hàng mùa không tính", [x["ma"] for x in t["giam"]], ["BAEN1", "BAEN2"])
	la("một món mới", t["moi"], 1)
	la("phần trăm", (t["tang"][0]["pt"], t["giam"][0]["pt"]), (100, -67))
	la("không có gì thì không có thẻ", pt.nhan_dinh_bao_cao_mon([{"ma_mon": "BANU1", "sl": 5}], [{"ma_mon": "BANU1", "sl": 4}], "x"), None)


@ca("#351: lớp độ tin cậy số liệu nói thẳng khi số chưa đủ hay chưa mới")
def _chat_luong():
	bg = datetime.datetime(2026, 9, 21, 7, 0, 0)
	c = pt.chat_luong(
		{"cu": 10, "giua": 300, "gan": 320, "nhap": (100, 320)},
		{"TCV": 40},
		[{"ma": "TCV", "ten": "District 1", "tb_ngay": 40}, {"ma": "NVHTN", "ten": "NVHTN", "tb_ngay": 20}, {"ma": "X", "ten": "Đóng", "tb_ngay": 0}],
		{"co_so": 1, "dong_bo_luc": "2026-09-21 02:10:00"}, D(2026, 9, 22), bg)
	ma = [x["ma"] for x in c]
	la("thiếu lịch sử, thiếu hoá đơn NVHTN, nhiều nháp, Pancake cũ", ma, ["lich_su", "thieu_hd_NVHTN", "nhap", "pancake"])
	dung("câu nháp có số", "100 trên 320 đơn" in c[2]["cau"])
	c2 = pt.chat_luong({"cu": 300, "nhap": (0, 300)}, {"TCV": 40}, [{"ma": "TCV", "ten": "D1", "tb_ngay": 40}], {"co_so": 0}, D(2026, 9, 22), bg)
	la("chưa có bảng kiểm bánh", [x["ma"] for x in c2], ["kiem_banh"])


# ------------------------------------------------------------ phần chạm hệ

class Gia:
	"""Frappe giả đủ cho giao, bỏ qua, cập nhật việc. Giữ trạng thái thật."""

	def __init__(self, vai=("AP Giám đốc",), user="viet@vgb", bang=True):
		self.vai = list(vai)
		self.task = {}
		self.todo = []
		self.share = []
		self.khoa = []
		self.bao = []
		self.bang = {"den_ngay": "2026-09-19", "chot_luc": "2026-09-20 07:00:00", "nhan_dinh": [
			pt._nd("mon_tang", "BANU14", "tat_ca", "Croissant đang lên", "Tuần qua bán 105.", "Đẩy story.", {"loai": "mon", "ma": "BANU14", "ten": "C", "anh": ""}, {}),
			pt._nd("lo_qua_han", "Kho tổng 307 - TV", "", "2 lô quá hạn", "…", "Cách ly.", {"loai": "kho", "ma": "Kho tổng 307 - TV", "ten": "Kho", "anh": ""}, {}),
		]} if bang else None
		fr = self
		self.session = NS(user=user)
		self.flags = NS()
		self.utils = NS(escape_html=lambda s: s)

		class Loi(Exception):
			pass
		self.Loi = Loi

		def get_value(dt, name, f=None, **k):
			if dt == "User":
				u = {"enabled": 0 if name == "tat@vgb" else 1, "user_type": "Website User" if name == "khach@vgb" else "System User"}
				if isinstance(f, (list, tuple)):
					return u
				return u.get(f, "Tên " + name) if name != "tat@vgb" else 0
			return None

		def exists(dt, f=None):
			if dt == "ToDo":
				return any(t for t in fr.todo if all(t.get(a) == b for a, b in f.items()))
			if dt == "Task":
				return f in fr.task
			return None

		def sql(q, a=()):
			fr.khoa.append((q.split("(")[0], a[0]))
			return [[1]]

		self.db = NS(get_value=get_value, exists=exists, sql=sql, set_value=lambda dt, n, f, v: fr.task[n].__setitem__(f, v),
			commit=lambda: fr.khoa.append(("commit", None)))
		self.cache = lambda: NS(get_value=lambda k: fr.bang, set_value=lambda *a, **k: None)

	def get_roles(self, *a):
		return self.vai

	def throw(self, m, **k):
		raise self.Loi(m)

	def log_error(self, *a, **k):
		pass

	def get_traceback(self):
		return ""

	def get_all(self, dt, filters=None, fields=None, **k):
		if dt == "Task":
			ra = []
			for t in self.task.values():
				ok = True
				for f, v in (filters or {}).items():
					if isinstance(v, list) and v[0] == "in":
						ok = ok and t.get(f) in v[1]
					elif isinstance(v, list):
						continue
					else:
						ok = ok and t.get(f) == v
				if ok:
					ra.append(dict(t))
			return ra
		if dt == "ToDo":
			return [dict(t) for t in self.todo if all(t.get(a) == b for a, b in (filters or {}).items())]
		return []

	def get_doc(self, d, name=None):
		fr = self
		if isinstance(d, str):
			if d == "ToDo":
				td = [x for x in fr.todo if x.get("name") == name][0]

				class TD(dict):
					def __setattr__(s, k, v):
						if k == "flags":
							object.__setattr__(s, k, v)
						else:
							s[k] = v

					def save(s, ignore_permissions=False):
						td.update(s)
				o = TD(td)
				o.flags = NS()
				return o
			return _TaskGia(fr, fr.task[name])

		class Moi(dict):
			def insert(s, ignore_permissions=False):
				dung("ghi bằng quyền hệ thống", ignore_permissions)
				if s["doctype"] == "Task":
					s["name"] = "TASK-%d" % (len(fr.task) + 1)
					s.setdefault("owner", fr.session.user)
					fr.task[s["name"]] = s
				else:
					s["name"] = "TD-%d" % (len(fr.todo) + 1)
					fr.todo.append(dict(s))
				return s

			@property
			def name(s):
				return s["name"]

			@property
			def priority(s):
				return s.get("priority")
		return Moi(d)


def _gv(fr):
	"""db.get_value giả cho Task: một trường trả giá trị, danh sách trả dict."""
	def gv(dt, n, f=None, as_dict=False, **k):
		d = fr.task[n]
		if isinstance(f, (list, tuple)):
			return {x: d.get(x) for x in f}
		return d.get(f)
	return gv


def _luu(doc):
	"""Chạy hai hook Task đúng thứ tự Frappe: before_validate rồi validate."""
	pt.kiem_nguoi_sua_task(doc)
	pt.kiem_task(doc)


class _DocGia(dict):
	def get(s, k, d=None):
		return dict.get(s, k, d)

	def is_new(s):
		return False

	def __getattr__(s, k):
		return s.get(k)

	def __setattr__(s, k, v):
		s[k] = v


class _TaskGia:
	def __init__(self, fr, d):
		self.__dict__["_fr"] = fr
		self.__dict__["_d"] = d
		self.__dict__["flags"] = NS()

	def __getattr__(self, k):
		return self._d.get(k)

	def __setattr__(self, k, v):
		self._d[k] = v

	def get(self, k):
		return self._d.get(k)

	def as_dict(self):
		return dict(self._d)

	def save(self):
		dung("lưu Task bằng quyền hệ thống", self.flags.ignore_permissions)


def _chay(fr, ham, *a, **k):
	chia_se = types.ModuleType("frappe.share")
	chia_se.add_docshare = lambda dt, name, user=None, read=1, write=0, flags=None, **kw: fr.share.append((name, user, write, (flags or {}).get("ignore_share_permission")))
	tb = NS(gui=lambda *x, **y: fr.bao.append(x))
	with patch.object(pt, "frappe", fr), patch.object(pt, "nowdate", lambda: "2026-09-20"), \
			patch.dict(sys.modules, {"frappe.share": chia_se}), \
			patch("vagabond.thong_bao.gui", tb.gui, create=True):
		return ham(*a, **k)


@ca("#351: Giao tạo MỘT Task, ToDo và chia sẻ cho từng người; bấm lại ra đúng việc cũ")
def _giao():
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	k = "mon_tang|BANU14|tat_ca"
	r = _chay(fr, pt.giao, k, json.dumps(["mkt@vgb", "vu@vgb"]), "2026-09-23", "đăng tối nay")
	la("một việc", (r["ok"], r["name"], r["so_nguoi"]), (1, "TASK-1", 2))
	t = fr.task["TASK-1"]
	la("khoá và luật trên Task", (t["vgb_goi_y_khoa"], t["vgb_goi_y_luat"], t["vgb_goi_y_bo_phan"]), (k, "mon_tang", "marketing"))
	la("hạn 18 giờ ngày chọn", t["exp_end_date"], "2026-09-23 18:00:00")
	dung("ghi chú người giao vào mô tả", "Ghi chú của người giao: đăng tối nay" in t["description"])
	la("hai ToDo", sorted(x["allocated_to"] for x in fr.todo), ["mkt@vgb", "vu@vgb"])
	la("chia sẻ cho hai người nhận và người giao, bỏ qua kiểm quyền chia sẻ",
		sorted(fr.share), sorted([("TASK-1", "mkt@vgb", 1, True), ("TASK-1", "vu@vgb", 1, True), ("TASK-1", "loan@vgb", 1, True)]))
	la("chuông cho hai người", len(fr.bao), 2)
	dung("có khoá tên cơ sở dữ liệu, commit rồi mới nhả khoá", [q for q, _ in fr.khoa] == ["select get_lock", "commit", "select release_lock"])
	r2 = _chay(fr, pt.giao, k, ["mkt@vgb"], "2026-09-23")
	la("bấm lại: đúng việc cũ, không Task mới", (r2.get("da_co"), r2["name"], len(fr.task)), (1, "TASK-1", 1))
	la("không thêm ToDo", len(fr.todo), 2)


@ca("#351: Giao chặn khi không chọn người, tài khoản tắt, hạn trong quá khứ, hay nhận định không thuộc bộ phận mình")
def _giao_chan():
	k = "mon_tang|BANU14|tat_ca"
	fr = Gia()
	nem("không chọn ai", lambda: _chay(fr, pt.giao, k, "[]"), fr.Loi)
	nem("tài khoản tắt", lambda: _chay(fr, pt.giao, k, ["tat@vgb"]), fr.Loi)
	nem("hạn hôm qua", lambda: _chay(fr, pt.giao, k, ["a@vgb"], "2026-09-19"), fr.Loi)
	fr2 = Gia(vai=("Stock Manager",))
	nem("kho không giao được nhận định marketing", lambda: _chay(fr2, pt.giao, k, ["a@vgb"]), fr2.Loi)
	fr3 = Gia(vai=("Sales User",))
	nem("nhân viên không mở được", lambda: _chay(fr3, pt.giao, k, ["a@vgb"]), fr3.Loi)
	fr4 = Gia(bang=False)
	try:
		_chay(fr4, pt.giao, k, ["a@vgb"])
		dung("bảng chưa dựng phải báo", False)
	except fr4.Loi as e:
		dung("bảng chưa dựng: câu nói đang dựng, bấm Tải lại", "đang dựng lại" in str(e) and "Tải lại" in str(e))
	la("không Task nào sinh ra trong các ca chặn", sum(len(f.task) for f in (fr, fr2, fr3, fr4)), 0)


@ca("#351: Giao mà không gắn được người thì BÁO LỖI, không báo thành công giả")
def _giao_hong():
	fr = Gia()
	with patch.object(pt, "_gan_nguoi", lambda *a: 0):
		nem("gắn 0 người", lambda: _chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["a@vgb"]), fr.Loi)
	s = _doc("vagabond", "phan_tich.py")
	dung("không đi qua assign_to.add hay giao_viec.giao (kiểm quyền người giao)", "assign_to import" not in s and "giao_viec.giao(" not in s)


@ca("#351: Bỏ qua bắt buộc lý do trong danh sách, kẹp số ngày theo luật, không bỏ qua việc đang giao")
def _bo_qua():
	fr = Gia()
	nem("lý do lạ", lambda: _chay(fr, pt.bo_qua, "lo_qua_han|Kho tổng 307 - TV|", "chan", 3), fr.Loi)
	r = _chay(fr, pt.bo_qua, "lo_qua_han|Kho tổng 307 - TV|", "so_sai", 14)
	la("lô quá hạn kẹp còn 3 ngày", (r["so_ngay"], r["nhac_lai"]), (3, "2026-09-23"))
	t = fr.task[r["name"]]
	la("lưu thành Task đã huỷ kèm lý do", (t["status"], t["vgb_goi_y_bo_qua_ly_do"]), ("Cancelled", "so_sai"))
	_chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["a@vgb"])
	nem("đã giao thì không bỏ qua", lambda: _chay(fr, pt.bo_qua, "mon_tang|BANU14|tat_ca", "khac", 3), fr.Loi)


@ca("#351: Báo xong bắt buộc ghi kết quả; người ngoài không mở được việc")
def _cap_nhat():
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	r = _chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["mkt@vgb"])
	fr.session.user = "mkt@vgb"
	fr.vai = ["Sales User"]
	nem("xong mà không ghi kết quả", lambda: _chay(fr, pt.cap_nhat_viec, r["name"], "xong", "ok"), fr.Loi)
	_chay(fr, pt.cap_nhat_viec, r["name"], "dang_lam")
	la("đang làm", fr.task[r["name"]]["status"], "Working")
	_chay(fr, pt.cap_nhat_viec, r["name"], "xong", "Đã đăng 2 story")
	t = fr.task[r["name"]]
	la("xong có người, ngày, kết quả", (t["status"], t["completed_by"], t["completed_on"], t["vgb_goi_y_ket_qua"]),
		("Completed", "mkt@vgb", "2026-09-20", "Đã đăng 2 story"))
	nem("xong rồi không sửa nữa", lambda: _chay(fr, pt.cap_nhat_viec, r["name"], "dang_lam"), fr.Loi)
	fr.session.user = "la@vgb"
	nem("người ngoài không có ToDo, không phụ trách bộ phận", lambda: _chay(fr, pt.viec, r["name"]), fr.Loi)


@ca("#351: Việc cần làm có loại 'Việc được giao', lọc theo ToDo đích danh, kể cả giám đốc")
def _viec_can_lam():
	from vagabond import viec_can_lam as vcl

	dung("ai cũng thấy loại đích danh", vcl.thay_duoc("goi_y", {"Sales User"}) and vcl.thay_duoc("goi_y", {"AP Giám đốc"}))
	dung("giám đốc vẫn bị siết các loại khác", not vcl.thay_duoc("xuat_kho", {"AP Giám đốc"}))
	fr = Gia()
	fr.todo = [{"allocated_to": "b@vgb", "status": "Open", "reference_type": "Task", "reference_name": "TASK-9"}]
	fr.task = {"TASK-9": {"name": "TASK-9", "subject": "Croissant đang lên", "exp_end_date": "2026-09-19 18:00:00",
		"vgb_goi_y_khoa": "k", "status": "Open"}, "TASK-8": {"name": "TASK-8", "vgb_goi_y_khoa": "k2", "status": "Open"}}
	ra = _chay(fr, pt.viec_can_lam_cua, "b@vgb")
	la("chỉ việc của mình, quá hạn thì trễ hẹn", [(x["ma"], x["tt"], x["loai"]) for x in ra], [("TASK-9", "tre_hen", "goi_y")])
	s = _doc("vagabond", "viec_can_lam.py")
	dung("nguồn goi_y nằm trong danh sách gom", '("goi_y", lambda: _viec_goi_y(nguoi))' in s)


@ca("#351: đăng ký đủ: cửa ngõ, nhịp 7 giờ, trường Task, đường dẫn, quyền nền, thẻ BC08, ca hành vi trong cổng")
def _dang_ky():
	from vagabond.khung.kiem_thu import thu_cua_ngo
	from vagabond import duong_app

	la("cửa ngõ", sorted(thu_cua_ngo.CUA_NGO.get("phan_tich.py") or []),
		["bang_sang", "bo_qua", "bo_qua_viec", "cap_nhat_viec", "dem_trang_chu", "giao", "hien_lai", "nguoi_de_giao", "tinh_lai", "viec"])
	dung("nhịp 7 giờ", '"0 7 * * *": ["vagabond.phan_tich.dung_bang_sang_tu_dong"]' in _doc("vagabond", "hooks.py"))
	dung("trường Task được dựng lúc migrate", "_dung_nhom(phan_tich.TRUONG_MOI" in _doc("vagabond", "truong_tu_them.py"))
	dung("lối vào Desk dựng lúc migrate", "phan_tich.dung_sidebar()" in _doc("vagabond", "truong_tu_them.py"))
	m = pt.muc_sidebar()
	la("sidebar: một nhóm, một lối mở màn app, một danh sách Task đã lọc", [(x["type"], x.get("link_type")) for x in m],
		[("Section Break", None), ("Link", "URL"), ("Link", "DocType")])
	la("lối mở màn đúng đường app", m[1]["url"], "/viec-hom-nay")
	ten = [f["fieldname"] for f in pt.TRUONG_MOI["Task"]]
	dung("đủ trường khoá, căn cứ, kết quả, bỏ qua", {"vgb_goi_y_khoa", "vgb_goi_y_so_lieu", "vgb_goi_y_ket_qua", "vgb_goi_y_bo_qua_ly_do", "vgb_goi_y_nhac_lai"} <= set(ten))
	la("đường /viec-hom-nay", duong_app.DUONG.get("viec-hom-nay"), "BCSANG")
	dung("quyền nền báo cho app", '"bang_sang": bool(vai & QUYEN_BANG_SANG)' in _doc("vagabond", "nhan_su.py"))
	dung("BC08 gắn thẻ nhận định", 'if b["ma"] == "BC08":' in _doc("vagabond", "bao_cao.py") and '"nhan_dinh": nhan_dinh,' in _doc("vagabond", "bao_cao.py"))
	dung("ca hành vi nằm trong cổng", "hanh_vi/bang_sang_351.js" in _doc("kiem_truoc_deploy.sh"))
	s = _doc("vagabond", "phan_tich.py")
	dung("không gọi mô hình ngôn ngữ ở đợt 1", "tro_ly" not in s and "anthropic" not in s.lower() and "openai" not in s.lower())


# ------------------------------------------------ Codex #353 vòng 1 (SHA 9fca02e)

@ca("#353 F1: Task bảng sáng chuyển Xong mà thiếu kết quả thì chặn ở tầng chứng từ (cả đường Desk)")
def _f1_ket_qua():
	la("thiếu kết quả", bool(pt.soat_ket_qua("Completed", "Open", "")), True)
	la("kết quả quá ngắn", bool(pt.soat_ket_qua("Completed", "Working", "ok")), True)
	la("có kết quả", pt.soat_ket_qua("Completed", "Open", "Đã đăng 2 story"), None)
	# Codex #353 vòng 2 (G5): trước đây ca này mong None, tức việc đã xong thì
	# được xoá trắng kết quả. Đó chính là lỗi; đừng sửa ca về như cũ.
	la("đã xong từ trước mà xoá trắng kết quả thì vẫn chặn", bool(pt.soat_ket_qua("Completed", "Completed", "")), True)
	la("chưa xong thì không soát", pt.soat_ket_qua("Working", "Open", ""), None)

	class DocGia(dict):
		def get(s, k, d=None):
			return dict.get(s, k, d)

		def is_new(s):
			return False

		def __getattr__(s, k):
			return s.get(k)

		def __setattr__(s, k, v):
			s[k] = v
	fr = Gia(user="mkt@vgb")
	fr.task["TASK-7"] = {"vgb_goi_y_khoa": "k", "name": "TASK-7", "status": "Open"}
	fr.db.get_value = _gv(fr)
	fr.todo.append({"reference_type": "Task", "reference_name": "TASK-7", "allocated_to": "mkt@vgb", "status": "Open"})
	d = DocGia(name="TASK-7", status="Completed", vgb_goi_y_khoa="k")
	nem("Desk đánh dấu xong mà trống kết quả", lambda: _chay(fr, pt.kiem_task, d), fr.Loi)
	d2 = DocGia(name="TASK-7", status="Completed", vgb_goi_y_khoa="k", vgb_goi_y_ket_qua="Đã cách ly lô")
	_chay(fr, pt.kiem_task, d2)
	la("có kết quả thì qua, tự ghi người và ngày xong", (d2.completed_by, d2.completed_on), ("mkt@vgb", "2026-09-20"))
	fr.task["TASK-8"] = {"name": "TASK-8", "status": "Open"}
	d3 = DocGia(name="TASK-8", status="Completed")
	_chay(fr, pt.kiem_task, d3)
	dung("Task không phải của bảng sáng thì bỏ qua", d3.completed_by is None)
	# Codex #356: Task bảng sáng mà ô khoá gửi lên bị xoá trắng vẫn bị soát
	# (nhận diện theo giá trị đã lưu), không lọt như Task thường.
	nem("xoá trắng ô khoá rồi đánh dấu xong không kết quả", lambda: _chay(fr, pt.kiem_task, DocGia(name="TASK-7", status="Completed")), fr.Loi)
	dung("hook đăng ký trên Task: before_validate soát người, validate soát kết quả",
		'"Task": {"before_validate": "vagabond.phan_tich.kiem_nguoi_sua_task", "validate": "vagabond.phan_tich.kiem_task"}' in _doc("vagabond", "hooks.py"))


@ca("#353 F2: người nhận cũ (ToDo đã đóng) không đổi được trạng thái, vẫn xem được")
def _f2_todo_dong():
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	r = _chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["cu@vgb"])
	for t in fr.todo:
		t["status"] = "Closed"
	fr.session.user = "cu@vgb"
	fr.vai = ["Sales User"]
	nem("người nhận cũ báo xong", lambda: _chay(fr, pt.cap_nhat_viec, r["name"], "xong", "Đã đăng 2 story"), fr.Loi)
	la("Task vẫn mở", fr.task[r["name"]]["status"], "Open")
	with patch.object(pt, "frappe", fr):
		la("vẫn xem được", pt._quyen_viec(_TaskGia(fr, fr.task[r["name"]])), "nhan")


@ca("#353 F3: việc còn mở đọc riêng, không bị lọc theo tuổi hay trần dòng")
def _f3_viec_mo():
	goi = []

	def get_all(dt, filters=None, limit_page_length=None, **k):
		goi.append((dict(filters), limit_page_length))
		return []
	with patch.object(pt, "frappe", NS(get_all=get_all)), patch.object(pt, "nowdate", lambda: "2026-09-21"):
		pt._viec_bang_sang()
	mo = [f for f, _ in goi if f.get("status") == ["in", list(pt.TASK_MO)]]
	la("có một truy vấn việc mở", len(mo), 1)
	dung("việc mở không lọc modified", "modified" not in mo[0])
	la("việc mở không giới hạn dòng", [l for f, l in goi if f.get("status") == ["in", list(pt.TASK_MO)]], [0])
	dung("lịch sử mới có hạn ngày", any("modified" in f for f, _ in goi if f.get("status") == ["in", ["Completed", "Cancelled"]]))


@ca("#353 F4: bảng kiểm bánh có mà chưa đồng bộ lần nào thì báo, không coi là số mới")
def _f4_chua_dong_bo():
	c = pt.chat_luong({"cu": 300, "nhap": (0, 300)}, {}, [], {"co_so": 1, "dong_bo_luc": ""},
		D(2026, 9, 22), datetime.datetime(2026, 9, 21, 7))
	la("có cảnh báo", [x["ma"] for x in c], ["pancake"])
	dung("câu nói chưa đồng bộ lần nào", "chưa đồng bộ đơn Pancake lần nào" in c[0]["cau"])


# ------------------------------------------------ Codex #353 vòng 2 (SHA b2d66e6)

@ca("#353 G1: lô đã tắt (disabled) mà còn hàng vẫn vào nhắc quá hạn")
def _g1_lo_tat():
	loc = []

	def get_all(dt, filters=None, **k):
		if dt == "Item":
			return [{"name": "NVLT1", "stock_uom": "Gram"}]
		loc.append(dict(filters or {}))
		return [{"name": "LO-TAT", "item": "NVLT1", "item_name": "Bơ", "expiry_date": "2026-09-01"}]
	tra_ton = types.ModuleType("vagabond.tra_ton")
	tra_ton._so_lo = lambda f: {("LO-TAT", "Kho tổng 307 - TV"): 4}
	fr = NS(get_all=get_all)
	with patch.object(pt, "frappe", fr), patch.dict(sys.modules, {"vagabond.tra_ton": tra_ton}):
		import vagabond
		with patch.object(vagabond, "tra_ton", tra_ton, create=True):
			ra = pt._lo_sap_het(datetime.date(2026, 9, 20))
	dung("không lọc disabled", "disabled" not in loc[0])
	la("lô tắt còn 4 vẫn ra, kèm đơn vị tồn kho", [(x["lo"], x["sl"], x["dvt"]) for x in ra], [("LO-TAT", 4.0, "Gram")])


@ca("#353 G2: phần tính hỏng thì bảng BÁO, không im lặng như kho sạch")
def _g2_hong():
	la("không hỏng thì không báo", pt.canh_bao_hong([]), [])
	c = pt.canh_bao_hong(["lo", "lo", "kiem_banh"])
	la("một dòng, mã loi_tinh", (len(c), c[0]["ma"]), (1, "loi_tinh"))
	dung("nêu đúng phần hỏng, không lặp", c[0]["cau"].count("lô quá hạn") == 1 and "kiểm bánh" in c[0]["cau"])
	# Chạy thật dung_bang_sang với phần lô nổ: bảng cất vào đệm phải có cảnh báo.
	cat = {}
	bc = types.ModuleType("vagabond.bao_cao")
	bc._diem = lambda r: "Q1"
	bc._dong_hang = lambda hd: []
	bc._diem_ban = lambda: []
	kb = types.ModuleType("vagabond.kiem_banh")
	kb.bang = lambda ngay: {"co_so": 1, "dong_bo_luc": "2026-09-20 06:50:00", "dong": []}

	def no(*a, **k):
		raise RuntimeError("mat ket noi")
	fr = NS(log_error=lambda *a, **k: None, get_traceback=lambda: "",
		cache=lambda: NS(set_value=lambda k, v, **kw: cat.__setitem__("bang", v)))
	import vagabond
	with patch.object(pt, "frappe", fr), patch.dict(sys.modules, {"vagabond.bao_cao": bc, "vagabond.kiem_banh": kb}), \
			patch.object(vagabond, "bao_cao", bc, create=True), patch.object(vagabond, "kiem_banh", kb, create=True), \
			patch.object(pt, "_hom_nay", lambda: datetime.date(2026, 9, 20)), \
			patch.object(pt, "_hoa_don_ba_tuan", lambda cs: []), patch.object(pt, "_anh_mon", lambda ds: {}), \
			patch.object(pt, "_lo_sap_het", no), \
			patch.object(pt, "now_datetime", lambda: datetime.datetime(2026, 9, 20, 7, 0, 0)):
		pt.dung_bang_sang()
	ma = [x["ma"] for x in cat["bang"]["chat_luong"]]
	dung("bảng cất vào đệm có cảnh báo phần lô", "loi_tinh" in ma and "lô quá hạn" in cat["bang"]["chat_luong"][0]["cau"])


@ca("#353 G3: giao/bỏ qua ghi hẳn (commit) TRƯỚC khi nhả khoá tên")
def _g3_khoa():
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	_chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["mkt@vgb"])
	buoc = [x[0].strip().split(" ")[-1] if x[0] != "commit" else "commit" for x in fr.khoa]
	la("thứ tự: lấy khoá, commit, nhả khoá", buoc, ["get_lock", "commit", "release_lock"])
	fr2 = Gia(user="viet@vgb")
	_chay(fr2, pt.bo_qua, "lo_qua_han|Kho tổng 307 - TV|", "so_sai", 3)
	buoc2 = [x[0].strip().split(" ")[-1] if x[0] != "commit" else "commit" for x in fr2.khoa]
	la("bỏ qua cũng vậy", buoc2, ["get_lock", "commit", "release_lock"])


@ca("#353 G4: trên Desk, người nhận cũ không đổi được trạng thái/kết quả; người đang nhận và quản lý thì được")
def _g4_desk_nguoi_cu():
	fr = Gia(user="cu@vgb", vai=("Sales User",))
	fr.task["TASK-9"] = {"vgb_goi_y_khoa": "k", "name": "TASK-9", "status": "Open", "vgb_goi_y_ket_qua": "", "vgb_goi_y_bo_phan": "marketing"}
	fr.db.get_value = _gv(fr)
	fr.todo += [
		{"reference_type": "Task", "reference_name": "TASK-9", "allocated_to": "cu@vgb", "status": "Closed"},
		{"reference_type": "Task", "reference_name": "TASK-9", "allocated_to": "moi@vgb", "status": "Open"},
	]
	d = lambda: _DocGia(name="TASK-9", status="Completed", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="marketing", vgb_goi_y_ket_qua="Đã xong việc")
	nem("người nhận cũ lưu Completed trên Desk", lambda: _chay(fr, _luu, d()), fr.Loi)
	fr.session.user = "moi@vgb"
	_chay(fr, _luu, d())
	fr.session.user, fr.vai = "loan@vgb", ["Marketing"]
	_chay(fr, _luu, d())
	fr.session.user, fr.vai = "Administrator", []
	_chay(fr, _luu, d())
	fr.session.user, fr.vai = "cu@vgb", ["Sales User"]
	# Codex #353 vòng 4 (M2): trước đây ca này CHỐT là người nhận cũ sửa ô khác
	# (tiêu đề, mô tả, hạn) thì KHÔNG chặn. Đó chính là lỗ hổng; đừng đổi về.
	sua_mo_ta = _DocGia(name="TASK-9", status="Open", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="marketing", vgb_goi_y_ket_qua="", subject="Đổi tiêu đề")
	nem("người nhận cũ sửa tiêu đề/hạn trên Desk", lambda: _chay(fr, _luu, sua_mo_ta), fr.Loi)
	fr.session.user, fr.vai = "sys@vgb", ["System Manager"]
	_chay(fr, _luu, sua_mo_ta)
	la("hàm thuần: System Manager miễn", pt.can_kiem_nguoi_sua("sys@vgb", {}, "Open", "", ["System Manager"]), False)
	la("hàm thuần: Administrator không xét", pt.can_kiem_nguoi_sua("Administrator", {"status": "Open"}, "Completed", "x"), False)
	la("hàm thuần: đổi kết quả thì xét", pt.can_kiem_nguoi_sua("a@vgb", {"status": "Completed", "vgb_goi_y_ket_qua": "cũ dài"}, "Completed", "mới dài"), True)


@ca("#353 G5: việc đã xong không xoá trắng hay rút ngắn được kết quả (đường Desk)")
def _g5_giu_ket_qua():
	fr = Gia(user="moi@vgb", vai=("Sales User",))
	fr.task["TASK-5"] = {"vgb_goi_y_khoa": "k", "name": "TASK-5", "status": "Completed", "vgb_goi_y_ket_qua": "Đã cách ly lô", "vgb_goi_y_bo_phan": "kho"}
	fr.db.get_value = _gv(fr)
	fr.todo.append({"reference_type": "Task", "reference_name": "TASK-5", "allocated_to": "moi@vgb", "status": "Open"})
	d = _DocGia(name="TASK-5", status="Completed", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="kho", vgb_goi_y_ket_qua="ok")
	nem("rút ngắn kết quả việc đã xong", lambda: _chay(fr, pt.kiem_task, d), fr.Loi)


# ------------------------------------------------ Codex #353 vòng 3 (SHA a279657)

@ca("#353 K1+K2: nhận định lô gửi đủ lô (tới trần) và mỗi lô kèm đơn vị tồn kho")
def _k12_lo():
	lo = [{"lo": "L%02d" % i, "ma": "NVLT1", "ten": "Bơ", "kho": "Kho tổng 307 - TV", "han": "2026-09-01", "sl": 500 + i, "dvt": "Gram"} for i in range(30)]
	x = pt.nhan_dinh_lo(lo, "2026-09-20")[0]
	la("gửi đủ 30 lô (trước đây cắt 12)", len(x["so_lieu"]["lo"]), 30)
	la("so_lo thật", x["so_lieu"]["so_lo"], 30)
	la("mỗi lô có đơn vị", {l["dvt"] for l in x["so_lieu"]["lo"]}, {"Gram"})
	nhieu = [dict(lo[0], lo="X%03d" % i) for i in range(pt.LO_GUI_TOI_DA + 5)]
	y = pt.nhan_dinh_lo(nhieu, "2026-09-20")[0]
	la("vượt trần thì gửi đúng trần, so_lo vẫn thật", (len(y["so_lieu"]["lo"]), y["so_lieu"]["so_lo"]), (pt.LO_GUI_TOI_DA, pt.LO_GUI_TOI_DA + 5))


@ca("#353 K3: Bỏ qua vừa ghi xong thì Giao đang chờ khoá phải thấy và dừng; một nguồn cho bảng và khoá")
def _k3_bo_qua_roi_giao():
	la("thuần: bỏ qua còn hạn", pt.ly_do_an("lo_qua_han", [{"name": "T1", "status": "Cancelled", "nhac_lai": "2026-09-22"}], "2026-09-20"), ("bo_qua", "T1"))
	la("thuần: đang mở thắng bỏ qua cũ", pt.ly_do_an("mon_tang", [{"name": "T0", "status": "Cancelled", "nhac_lai": "2026-09-30"}, {"name": "T2", "status": "Open"}], "2026-09-20"), ("mo", "T2"))
	la("thuần: bỏ qua đã tới ngày nhắc thì không ẩn", pt.ly_do_an("lo_qua_han", [{"name": "T1", "status": "Cancelled", "nhac_lai": "2026-09-20"}], "2026-09-20"), (None, None))
	# Chuỗi thật: A bỏ qua (ghi xong, nhả khoá), rồi B bấm Giao từ CÙNG ảnh bảng cũ.
	fr = Gia(user="viet@vgb")
	k = "lo_qua_han|Kho tổng 307 - TV|"
	r = _chay(fr, pt.bo_qua, k, "so_sai", 3)
	nem("Giao sau khi vừa bỏ qua", lambda: _chay(fr, pt.giao, k, ["kho@vgb"]), fr.Loi)
	la("không sinh Task giao, không ToDo", ([t["status"] for t in fr.task.values()], len(fr.todo)), (["Cancelled"], 0))
	r2 = _chay(fr, pt.bo_qua, k, "so_sai", 3)
	la("bấm Bỏ qua lần hai ra đúng việc cũ", (r2.get("da_co"), r2["name"], len(fr.task)), (1, r["name"], 1))
	dung("chia_theo_viec dùng chung ly_do_an", "ly_do_an(" in _doc("vagabond", "phan_tich.py").split("def chia_theo_viec")[1].split("def ly_do_an")[0])


# ------------------------------------------------ Codex #353 vòng 4 (SHA ae8e76b)

@ca("#353 M1: người nhận không có vai bán hàng mở được Việc cần làm, chỉ thấy việc giao cho mình")
def _m1_viec_can_lam_khong_ban_hang():
	from vagabond import viec_can_lam as vcl
	bh = types.ModuleType("vagabond.ban_hang")
	bh.QUYEN_BAN_HANG = {"System Manager", "Sales User", "Sales Manager", "Bộ phận đặt hàng"}

	class ChanBH(Exception):
		pass

	def _kq():
		raise ChanBH("chưa được cấp quyền ghi nhận doanh số")
	bh._kiem_quyen = _kq
	goi = []

	def gom(ten, ra):
		def f(*a, **k):
			goi.append(ten)
			return ra
		return f
	fr = NS(session=NS(user="bep@vgb"), get_roles=lambda *a: ["Bếp trưởng", "Stock Manager"], log_error=lambda *a, **k: None, get_traceback=lambda: "",
		get_all=lambda *a, **k: [], db=NS(get_value=lambda *a, **k: None))
	viec = [{"loai": "goi_y", "ma": "TASK-9", "nhom": "Việc được giao", "phu": "Cách ly lô", "ngay": "2026-09-21", "tt": "cho_lam"}]
	import vagabond
	with patch.dict(sys.modules, {"vagabond.ban_hang": bh}), patch.object(vagabond, "ban_hang", bh, create=True), \
			patch.object(vcl, "frappe", fr), patch.object(vcl, "_viec_goi_y", gom("goi_y", viec)), \
			patch.object(vcl, "_viec_xuat_kho", gom("xuat_kho", [{"loai": "xuat_kho", "ma": "X", "tt": "cho_lam"}])), \
			patch.object(vcl, "_viec_san_xuat", gom("san_xuat", [])):
		kq = vcl.danh_sach()
		la("chỉ thấy việc giao cho mình", [x["ma"] for x in kq["ds"]], ["TASK-9"])
		dung("không chạy nguồn phiếu khác", "xuat_kho" not in goi and "san_xuat" not in goi)
		with patch.object(vcl, "_viec_goi_y", gom("goi_y", [])):
			nem("không có việc giao, không vai bán hàng: vẫn chặn như cũ", lambda: vcl.danh_sach(), ChanBH)


@ca("#353 M3: nút Xem thêm lô cao tối thiểu 44 điểm (AGENTS.md mục chạm)")
def _m3_cham():
	s = _doc("vagabond", "public", "js", "bep", "47-bang-sang.js")
	tom = s.split("<summary", 1)[1].split(">", 1)[0]
	dung("summary min-height 44px", "min-height:44px" in tom)


@ca("#353 bench ae8e76b: người nhận THẬT báo xong không bị chặn dù ERPNext đóng ToDo trong Task.validate")
def _thu_tu_hook():
	# Bench CI đỏ trên ae8e76b: soát người đặt ở validate thì ToDo của chính
	# người nhận đã bị ERPNext đóng trước đó, nên họ bị báo "không còn giao
	# cho bạn". Ca này dựng đúng thứ tự: before_validate, bộ điều khiển Task
	# (đóng ToDo khi Completed), rồi validate.
	fr = Gia(user="moi@vgb", vai=("Sales User",))
	fr.task["TASK-3"] = {"vgb_goi_y_khoa": "k", "name": "TASK-3", "status": "Open", "vgb_goi_y_ket_qua": "", "vgb_goi_y_bo_phan": "kho"}
	fr.db.get_value = _gv(fr)
	fr.todo.append({"reference_type": "Task", "reference_name": "TASK-3", "allocated_to": "moi@vgb", "status": "Open"})
	d = _DocGia(name="TASK-3", status="Completed", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="kho", vgb_goi_y_ket_qua="Đã cách ly lô")

	def luu_nhu_frappe(doc):
		pt.kiem_nguoi_sua_task(doc)
		for t in fr.todo:  # ERPNext Task.validate đóng ToDo khi Completed
			if t["reference_name"] == doc["name"] and doc["status"] == "Completed":
				t["status"] = "Closed"
		pt.kiem_task(doc)
	_chay(fr, luu_nhu_frappe, d)
	la("người nhận thật báo xong được", d.completed_by, "moi@vgb")


# ------------------------------------------------ Codex #356 (SHA fed1146)

@ca("#356 N1: người nhận không huỷ Task trên Desk; quản lý huỷ phải có lý do và ngày nhắc")
def _n1_huy():
	la("thuần: người nhận huỷ", bool(pt.soat_huy("Cancelled", "Open", "nhan", "so_sai", "2026-09-25", "2026-09-20")), True)
	la("thuần: quản lý thiếu lý do", bool(pt.soat_huy("Cancelled", "Open", "quan_ly", "", "2026-09-25", "2026-09-20")), True)
	la("thuần: quản lý thiếu ngày nhắc", bool(pt.soat_huy("Cancelled", "Open", "quan_ly", "so_sai", "", "2026-09-20")), True)
	la("thuần: ngày nhắc là hôm nay", bool(pt.soat_huy("Cancelled", "Open", "quan_ly", "so_sai", "2026-09-20", "2026-09-20")), True)
	la("thuần: đủ thì qua", pt.soat_huy("Cancelled", "Open", "quan_ly", "so_sai", "2026-09-23", "2026-09-20"), None)
	la("thuần: đã huỷ từ trước thì không xét lại", pt.soat_huy("Cancelled", "Cancelled", "nhan", "", "", "2026-09-20"), None)
	fr = Gia(user="moi@vgb", vai=("Sales User",))
	fr.task["TASK-4"] = {"vgb_goi_y_khoa": "k", "name": "TASK-4", "status": "Open", "vgb_goi_y_ket_qua": "", "vgb_goi_y_bo_phan": "marketing"}
	fr.db.get_value = _gv(fr)
	fr.todo.append({"reference_type": "Task", "reference_name": "TASK-4", "allocated_to": "moi@vgb", "status": "Open"})
	huy = lambda **k: _DocGia(name="TASK-4", status="Cancelled", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="marketing", **k)
	nem("người nhận đang giữ việc đổi sang Cancelled trên Desk", lambda: _chay(fr, _luu, huy()), fr.Loi)
	fr.session.user, fr.vai = "loan@vgb", ["Marketing"]
	nem("quản lý huỷ không lý do", lambda: _chay(fr, _luu, huy()), fr.Loi)
	_chay(fr, _luu, huy(vgb_goi_y_bo_qua_ly_do="so_sai", vgb_goi_y_nhac_lai="2026-09-23"))


@ca("#356 N2: ô Trễ hạn mở đúng phần việc trễ, không phải cả tab Đã giao")
def _n2_tre():
	fr = Gia(user="viet@vgb")
	fr.task["TASK-1"] = {"name": "TASK-1", "subject": "Trễ", "status": "Open", "exp_end_date": "2026-09-18 18:00:00", "vgb_goi_y_khoa": "k1",
		"vgb_goi_y_luat": "mon_tang", "vgb_goi_y_bo_phan": "marketing", "_assign": "[]", "owner": "viet@vgb"}
	fr.task["TASK-2"] = {"name": "TASK-2", "subject": "Còn hạn", "status": "Open", "exp_end_date": "2026-09-25 18:00:00", "vgb_goi_y_khoa": "k2",
		"vgb_goi_y_luat": "mon_tang", "vgb_goi_y_bo_phan": "marketing", "_assign": "[]", "owner": "viet@vgb"}
	r = _chay(fr, pt.bang_sang, "tre")
	la("tab tre chỉ có việc trễ", (r["tab"], [x["name"] for x in r["ds"]]), ("tre", ["TASK-1"]))
	la("đếm khớp số trên ô", (r["dem"]["tre"], r["so_tre"], r["dem"]["da_giao"]), (1, 1, 2))


@ca("#356 N4: quản lý bỏ qua việc đã giao bằng nút trên Desk; người nhận không bỏ qua được")
def _n4_bo_qua_viec():
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	r = _chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["mkt@vgb"])
	nem("lý do ngoài danh sách", lambda: _chay(fr, pt.bo_qua_viec, r["name"], "tu_bia", 3), fr.Loi)
	fr.session.user, fr.vai = "mkt@vgb", ["Sales User"]
	nem("người nhận bấm bỏ qua", lambda: _chay(fr, pt.bo_qua_viec, r["name"], "so_sai", 3), fr.Loi)
	fr.session.user, fr.vai = "loan@vgb", ["Marketing"]
	fr.db.get_value = _gv(fr)
	kq = _chay(fr, pt.bo_qua_viec, r["name"], "so_sai", 30)
	t = fr.task[r["name"]]
	la("Task huỷ kèm lý do, ngày kẹp theo luật", (t["status"], t["vgb_goi_y_bo_qua_ly_do"], kq["so_ngay"]),
		("Cancelled", "so_sai", pt.so_ngay_bo_qua("mon_tang", 30)))
	la("ngày nhắc sau hôm nay", pt.soat_huy("Cancelled", "Open", "quan_ly", t["vgb_goi_y_bo_qua_ly_do"], t["vgb_goi_y_nhac_lai"], "2026-09-20"), None)
	fr.task[r["name"]]["status"] = "Open"
	with patch.object(pt, "_ten_nguoi", lambda ds: {}):
		v = _chay(fr, pt.viec, r["name"])
	dung("hooks gắn nút Bỏ qua cho form Task", '"Task": "public/js/task_bang_sang.js"' in _doc("vagabond", "hooks.py"))
	la("viec() trả danh sách lý do từ một nguồn", [x["k"] for x in v["ly_do_bo_qua"]], [k for k, _ in pt.LY_DO_BO_QUA])


@ca("#356 P1+P2: quản lý bộ phận được giao cũng là quản lý; bỏ qua thì đóng hết ToDo")
def _p12():
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	r = _chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["loan@vgb", "mkt@vgb"])
	fr.db.get_value = _gv(fr)
	with patch.object(pt, "frappe", fr):
		q = pt._quyen_viec(_TaskGia(fr, fr.task[r["name"]]), ghi=True)
	la("quản lý marketing vừa được giao vẫn là quan_ly", q, "quan_ly")
	kq = _chay(fr, pt.bo_qua_viec, r["name"], "khong_can", 3)
	la("bỏ qua đóng cả hai ToDo", (kq["dong_todo"], sorted({t["status"] for t in fr.todo})), (2, ["Cancelled"]))


# ------------------------------------------------ Codex #356 (SHA b963578)

@ca("#356 Q1: giao qua API chỉ cho tài khoản nội bộ đang bật")
def _q1_nguoi_nhan():
	la("nội bộ đang bật", pt.loi_nguoi_nhan("a@vgb", {"enabled": 1, "user_type": "System User"}), None)
	dung("Website User bị chặn", "nội bộ" in (pt.loi_nguoi_nhan("k@x", {"enabled": 1, "user_type": "Website User"}) or ""))
	dung("Administrator bị chặn", bool(pt.loi_nguoi_nhan("Administrator", {"enabled": 1, "user_type": "System User"})))
	dung("tắt bị chặn", bool(pt.loi_nguoi_nhan("t@vgb", {"enabled": 0, "user_type": "System User"})))
	dung("không có User bị chặn", bool(pt.loi_nguoi_nhan("z@vgb", None)))
	fr = Gia(user="loan@vgb", vai=("Marketing",))
	nem("giao cho Website User qua API", lambda: _chay(fr, pt.giao, "mon_tang|BANU14|tat_ca", ["khach@vgb"]), fr.Loi)
	la("không Task, không ToDo, không chia sẻ", (len(fr.task), len(fr.todo), len(fr.share)), (0, 0, 0))


@ca("#356 Q2: phần trên `import frappe` nạp và chạy được khi KHÔNG có Frappe")
def _q2_khong_frappe():
	src = _doc("vagabond", "phan_tich.py")
	tren = src.split("\nimport frappe")[0]
	dung("phần thuần không có dòng import frappe", not [l for l in tren.splitlines() if l.startswith(("import frappe", "from frappe"))])

	class Chan:
		def find_module(self, ten, path=None):
			return None

		def find_spec(self, ten, path=None, target=None):
			if ten == "frappe" or ten.startswith("frappe."):
				raise ImportError("gia lap khong co Frappe")
			return None
	cu = {k: v for k, v in sys.modules.items() if k == "frappe" or k.startswith("frappe.") or k == "vagabond.vai_cua_hang"}
	for k in cu:
		del sys.modules[k]
	chan = Chan()
	sys.meta_path.insert(0, chan)
	try:
		ns = {"__name__": "phan_tich_thuan"}
		exec(compile(tren, "phan_tich.py#thuan", "exec"), ns)
	finally:
		sys.meta_path.remove(chan)
		sys.modules.update(cu)
	la("xet_tang chạy", ns["xet_tang"]([10, 20, 40], 1), "tang")
	la("nhan_dinh_lo chạy", len(ns["nhan_dinh_lo"]([{"lo": "L", "ma": "M", "ten": "T", "kho": "K", "han": "2026-09-01", "sl": 2}], "2026-09-20")), 1)
	la("soat_huy chạy", ns["soat_huy"]("Cancelled", "Open", "nhan", "", "", "2026-09-20") is not None, True)
	from vagabond import vai_cua_hang
	la("hằng vai dự phòng trùng bản gốc", (ns["VAI_MARKETING"], ns["VAI_QLCH"]), (vai_cua_hang.VAI_MARKETING, vai_cua_hang.VAI_QLCH))


@ca("#356 Q3: sàn mẫu áp cho tuần/kỳ GỐC")
def _q3_san_goc():
	la("4 lên 12 không phải tăng", pt.xet_tang([0, 4, 12], 1), None)
	la("12 lên 30 là tăng", pt.xet_tang([10, 12, 30], 1), "tang")
	la("món mới vẫn giữ đường riêng", pt.xet_tang([0, 0, 15], 1), "moi")
	kq = pt.nhan_dinh_bao_cao_mon([{"ma_mon": "BANU1", "mon": "A", "sl": 12}], [{"ma_mon": "BANU1", "sl": 4}], "kỳ trước")
	dung("BC08: kỳ gốc 4 không vào danh sách tăng", not kq or not kq.get("tang"))
	kq2 = pt.nhan_dinh_bao_cao_mon([{"ma_mon": "BANU1", "mon": "A", "sl": 30}], [{"ma_mon": "BANU1", "sl": 12}], "kỳ trước")
	dung("BC08: kỳ gốc 12 lên 30 là tăng", bool(kq2) and [x["ma"] for x in kq2.get("tang", [])] == ["BANU1"])


# ------------------------------------------------ Codex #356 (SHA 4eee909)

@ca("#356 R1+R2: không sửa ô căn cứ, không lách luật bằng xoá ô khoá, không mở lại việc đã đóng")
def _r12():
	la("thuần: đổi luật", bool(pt.loi_truong_khoa({"vgb_goi_y_khoa": "k", "vgb_goi_y_luat": "mon_tang"}, {"vgb_goi_y_khoa": "k", "vgb_goi_y_luat": "lo_qua_han"})), True)
	la("thuần: ngày cùng giá trị khác kiểu", pt.loi_truong_khoa({"vgb_goi_y_khoa": "k", "vgb_goi_y_den_ngay": datetime.date(2026, 9, 19)}, {"vgb_goi_y_khoa": "k", "vgb_goi_y_den_ngay": "2026-09-19"}), None)
	la("thuần: mở lại việc xong", bool(pt.loi_mo_lai("Completed", "Open")), True)
	la("thuần: mở lại việc bỏ qua", bool(pt.loi_mo_lai("Cancelled", "Working")), True)
	la("thuần: xong đổi sang huỷ", bool(pt.loi_mo_lai("Completed", "Cancelled")), True)
	la("thuần: mở sang xong", pt.loi_mo_lai("Open", "Completed"), None)
	fr = Gia(user="moi@vgb", vai=("Sales User",))
	fr.task["TASK-6"] = {"name": "TASK-6", "status": "Open", "vgb_goi_y_khoa": "k", "vgb_goi_y_bo_phan": "kho", "vgb_goi_y_luat": "lo_qua_han", "vgb_goi_y_ket_qua": ""}
	fr.db.get_value = _gv(fr)
	fr.todo.append({"reference_type": "Task", "reference_name": "TASK-6", "allocated_to": "moi@vgb", "status": "Open"})
	nem("người nhận xoá trắng ô khoá qua API rồi huỷ", lambda: _chay(fr, _luu, _DocGia(name="TASK-6", status="Cancelled", vgb_goi_y_bo_phan="kho", vgb_goi_y_luat="lo_qua_han")), fr.Loi)
	nem("người nhận đổi bộ phận", lambda: _chay(fr, _luu, _DocGia(name="TASK-6", status="Open", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="marketing", vgb_goi_y_luat="lo_qua_han")), fr.Loi)
	fr.task["TASK-6"]["status"] = "Completed"
	fr.task["TASK-6"]["vgb_goi_y_ket_qua"] = "Đã cách ly lô"
	fr.session.user, fr.vai = "loan@vgb", ["AP Giám đốc"]
	nem("giám đốc mở lại việc đã xong trên Desk", lambda: _chay(fr, _luu, _DocGia(name="TASK-6", status="Open", vgb_goi_y_khoa="k", vgb_goi_y_bo_phan="kho", vgb_goi_y_luat="lo_qua_han", vgb_goi_y_ket_qua="Đã cách ly lô")), fr.Loi)
