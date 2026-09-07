# -*- coding: utf-8 -*-
"""Tồn ngày mai có NGUỒN theo từng ô (issue #216, v444).

Bàn giao PR #223 (06/09/2026) đo thật: `chot_ngay` ghi đè cả ba ô tồn ngày
mai khi hôm nay còn hàng, kể cả ô cửa hàng đã đếm tay; còn khi hôm nay về 0
thì bỏ mặc số cũ. Hai nhánh không đối xứng và không ai phân biệt được số nào
là máy chuyển, số nào là tay đếm. Codex chốt luật theo uỷ quyền của anh Việt
(07/09/2026), tệp này khoá từng điều:

  - mỗi ô tồn mang nguồn: Tự chuyển / Đã kiểm đếm / Cần xác nhận (không rõ)
  - đếm ra 0 là số đếm hợp lệ
  - chốt chỉ ghi ô do máy chuyển, kể cả ghi về 0; không đè ô đã đếm, không cộng
  - bày số máy chuyển và chênh lệch bên cạnh; ghi ai đếm, lúc nào
  - dữ liệu cũ không rõ nguồn: giữ nguyên, nhãn Cần xác nhận

Mọi ca chạy THẬT `luu_o`, `chot_ngay`, `bang` qua bàn giả `CuaGia` của
thu_cot_huy_kiem_banh.py (kế thừa thẳng lớp doctype). Bàn giả đã sửa
`DongGia.__setattr__` để không che phép ghi nào nữa.

CHƯA chứng minh được ở đây: hai kết nối đếm và chốt cùng một giây. Frappe
chặn bằng dấu thời gian `modified` (TimestampMismatchError) cho bên lưu sau;
ở đây chỉ kiểm hai THỨ TỰ nối tiếp: đếm rồi chốt, và chốt rồi đếm.
"""

import json

import frappe

from vagabond import kiem_banh
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la
from vagabond.khung.kiem_thu.thu_cot_huy_kiem_banh import (
	BangGia, CuaGia, _doc, _tao_dong,
)

MAY, TAY = kiem_banh.NGUON_MAY, kiem_banh.NGUON_TAY


def _chot(hom_nay, mai=None, lan=1):
	"""Chạy THẬT `chot_ngay` `lan` lần (mỗi lần mở khoá lại hôm nay) rồi trả về
	bảng hôm nay và ngày mai."""
	nay = BangGia(ngay="2026-08-15", dong=hom_nay)
	ngay_mai = BangGia(ngay="2026-08-16", dong=(mai or []))
	cua = CuaGia(**{"KB-2026-08-15": nay, "KB-2026-08-16": ngay_mai})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	with cua:
		for _ in range(lan):
			nay.tinh_trang = "Dang ban"
			kiem_banh.chot_ngay("2026-08-15")
	return nay, ngay_mai


def _dem(bang, ma, o, so):
	"""Chạy THẬT `luu_o` trên một bảng ngày mai đang mở."""
	cua = CuaGia(**{"KB-2026-08-16": bang})
	with cua:
		return kiem_banh.luu_o("2026-08-16", ma, o, so)


def _o(m, o):
	return (m.get(o), m.get("nguon_" + o), m.get("may_chuyen_" + o))


# ------------------------------------------------------------- 1. phần thuần


@ca("ton ngay mai: bang nhan cua tung o (nguon, so) -> nhan va quyen ghi cua may")
def _():
	la("máy chuyển", kiem_banh.trang_thai_o(MAY, 5), "Tự chuyển")
	la("máy chuyển về 0 vẫn là Tự chuyển", kiem_banh.trang_thai_o(MAY, 0), "Tự chuyển")
	la("đếm tay", kiem_banh.trang_thai_o(TAY, 5), "Đã kiểm đếm")
	la("đếm tay ra 0 vẫn là Đã kiểm đếm", kiem_banh.trang_thai_o(TAY, 0), "Đã kiểm đếm")
	la("không rõ nguồn mà có số", kiem_banh.trang_thai_o("", 7), "Cần xác nhận")
	la("không rõ nguồn mà có số (None)", kiem_banh.trang_thai_o(None, 7), "Cần xác nhận")
	la("không rõ nguồn và bằng 0 là ô trống", kiem_banh.trang_thai_o("", 0), "")
	dung("máy ghi được ô Tự chuyển", kiem_banh.may_duoc_ghi(MAY, 9))
	dung("máy ghi được ô trống", kiem_banh.may_duoc_ghi("", 0))
	dung("máy KHÔNG ghi ô đã đếm", not kiem_banh.may_duoc_ghi(TAY, 9))
	dung("máy KHÔNG ghi ô đã đếm ra 0", not kiem_banh.may_duoc_ghi(TAY, 0))
	dung("máy KHÔNG ghi ô chưa rõ nguồn có số", not kiem_banh.may_duoc_ghi("", 7))


# --------------------------------------------- 2. chưa đếm: chuyển dương, về 0


@ca("ton ngay mai: o may chuyen hom truoc, hom nay con hang thi doi sang so moi, nhan Tu chuyen")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, da_dat=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=5, nguon_ton_d2=MAY, may_chuyen_ton_d2=5)
	_nay, mai = _chot([d], mai=[m])
	r = mai.dong[0]
	# 10 làm hôm kia (d1 của hôm nay) trừ 3 còn 7, sang ngày mai lùi thành d2.
	la("ô d2 đổi sang 7", _o(r, "ton_d2"), (7, MAY, 7))
	la("ô cũ hơn về 0, vẫn nguồn máy", _o(r, "ton_cu"), (0, MAY, 0))
	la("ô d1 (hôm nay không làm) là 0", _o(r, "ton_d1"), (0, MAY, 0))


@ca("ton ngay mai: o may chuyen hom truoc, hom nay huy het thi chot ghi VE 0 (khong bo mac so cu nua)")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=3, huy=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=7, nguon_ton_d2=MAY, may_chuyen_ton_d2=7)
	_nay, mai = _chot([d], mai=[m])
	la("số máy cũ bị đưa về 0", _o(mai.dong[0], "ton_d2"), (0, MAY, 0))
	la("NSX cũng xoá", mai.dong[0].get("nsx_d2"), None)


@ca("ton ngay mai: hom nay het sach va ngay mai CHUA co dong thi khong de dong trong")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=3, huy=3)
	_nay, mai = _chot([d])
	la("không thêm dòng", len(mai.dong), 0)


# --------------------------------- 3. đã đếm: dương hay 0 đều giữ nguyên khi chốt


@ca("ton ngay mai: o da dem DUONG thi chot khong de, chi ghi so may ben canh")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, da_dat=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=4, nguon_ton_d2=TAY)
	_nay, mai = _chot([d], mai=[m])
	la("giữ 4 của người đếm, máy ghi 7 bên cạnh", _o(mai.dong[0], "ton_d2"), (4, TAY, 7))


@ca("ton ngay mai: o da dem RA 0 cung la so dem, chot khong de len 0 do")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, da_dat=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=0, nguon_ton_d2=TAY)
	_nay, mai = _chot([d], mai=[m])
	la("vẫn 0 đếm tay, máy 7 bên cạnh", _o(mai.dong[0], "ton_d2"), (0, TAY, 7))
	la("nhãn Đã kiểm đếm", kiem_banh.trang_thai_o(TAY, 0), "Đã kiểm đếm")


# --------------------------------------- 4. sửa một ô không khoá ô khác


@ca("ton ngay mai: dem mot o thi chi o do thanh Da kiem dem; hai o kia chot van ghi")
def _():
	m = _tao_dong(ma_hang="BAWC00055")
	bang_mai = BangGia(ngay="2026-08-16", dong=[m])
	_dem(bang_mai, "BAWC00055", "ton_d2", 4)
	la("ô đếm mang nguồn tay", m.get("nguon_ton_d2"), TAY)
	la("ô khác chưa có nguồn", (m.get("nguon_ton_cu"), m.get("nguon_ton_d1")), ("", ""))
	# Hôm nay: cũ hơn 2 và hôm kia 6, không bán gì -> ngày mai cũ hơn 2 + 6 = 8, d2 = 0
	# (hôm nay không làm gì: ton_d1 hôm nay là 0), d1 = 0. Đếm tay d2 = 4 giữ.
	d = _tao_dong(ma_hang="BAWC00055", ton_cu=2, ton_d2=6)
	nay = BangGia(ngay="2026-08-15", dong=[d])
	cua = CuaGia(**{"KB-2026-08-15": nay, "KB-2026-08-16": bang_mai})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	with cua:
		kiem_banh.chot_ngay("2026-08-15")
	la("ô cũ hơn máy ghi 8", _o(m, "ton_cu"), (8, MAY, 8))
	la("ô d2 giữ 4 đếm tay, máy 0 bên cạnh", _o(m, "ton_d2"), (4, TAY, 0))
	la("ô d1 máy ghi 0", _o(m, "ton_d1"), (0, MAY, 0))


# ------------------------------------------------- 5. chốt lại không cộng dồn


@ca("ton ngay mai: chot hai lan cho cung ket qua, khong cong don")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, sx=5, da_dat=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=1, nguon_ton_d2=TAY)
	_nay, mai1 = _chot([d], mai=[_tao_dong(**m)], lan=1)
	_nay, mai2 = _chot([d], mai=[_tao_dong(**m)], lan=2)
	for o in kiem_banh.O_TON:
		la("ô %s lần một bằng lần hai" % o, _o(mai1.dong[0], o), _o(mai2.dong[0], o))
	# Hôm nay: d1 = 10 trừ 3 bán còn 7, bếp làm 5. Ngày mai: d2 = 7, d1 = 5.
	la("d2: máy tính 7 (không phải 14) nhưng giữ 1 đếm tay", _o(mai2.dong[0], "ton_d2"), (1, TAY, 7))
	la("d1: bếp làm 5 chuyển sang, không phải 10", _o(mai2.dong[0], "ton_d1"), (5, MAY, 5))
	la("cũ hơn 0", _o(mai2.dong[0], "ton_cu"), (0, MAY, 0))


# ----------------------------------------- 6. đếm và chốt theo hai thứ tự


@ca("ton ngay mai: dem TRUOC roi chot, va chot TRUOC roi dem: so dem khong mat o ca hai thu tu")
def _():
	# Thứ tự A: đếm rồi chốt.
	m = _tao_dong(ma_hang="BAWC00055")
	bang_mai = BangGia(ngay="2026-08-16", dong=[m])
	_dem(bang_mai, "BAWC00055", "ton_d1", 2)
	d = _tao_dong(ma_hang="BAWC00055", sx=9)
	nay = BangGia(ngay="2026-08-15", dong=[d])
	cua = CuaGia(**{"KB-2026-08-15": nay, "KB-2026-08-16": bang_mai})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	with cua:
		kiem_banh.chot_ngay("2026-08-15")
	la("A: đếm 2 giữ, máy 9 bên cạnh", _o(m, "ton_d1"), (2, TAY, 9))
	# Thứ tự B: chốt rồi đếm.
	m2 = _tao_dong(ma_hang="BAWC00055")
	bang_mai2 = BangGia(ngay="2026-08-16", dong=[m2])
	nay2 = BangGia(ngay="2026-08-15", dong=[_tao_dong(ma_hang="BAWC00055", sx=9)])
	cua2 = CuaGia(**{"KB-2026-08-15": nay2, "KB-2026-08-16": bang_mai2})
	cua2.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	with cua2:
		kiem_banh.chot_ngay("2026-08-15")
	la("B: máy ghi 9 trước", _o(m2, "ton_d1"), (9, MAY, 9))
	_dem(bang_mai2, "BAWC00055", "ton_d1", 2)
	la("B: người đếm 2 đè lên số máy, nguồn đổi sang tay, số máy vẫn 9", _o(m2, "ton_d1"), (2, TAY, 9))


# ------------------------------------------- 7. dữ liệu cũ chưa rõ nguồn


@ca("ton ngay mai: du lieu cu khong ro nguon: co so thi giu va Can xac nhan, bang 0 thi may ghi duoc")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, da_dat=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=5, ton_cu=0)   # không có nguồn nào
	_nay, mai = _chot([d], mai=[m])
	r = mai.dong[0]
	la("ô 5 không rõ nguồn: giữ nguyên, nguồn vẫn trống, máy 7 bên cạnh", _o(r, "ton_d2"), (5, "", 7))
	la("nhãn Cần xác nhận", kiem_banh.trang_thai_o(r.get("nguon_ton_d2"), r.get("ton_d2")), "Cần xác nhận")
	la("ô 0 không rõ nguồn: máy ghi được", _o(r, "ton_cu"), (0, MAY, 0))
	# Người đếm lại ô Cần xác nhận thì thành Đã kiểm đếm.
	_dem(mai, "BAWC00055", "ton_d2", 5)
	la("đếm lại 5 thì hết Cần xác nhận", _o(r, "ton_d2"), (5, TAY, 7))


# --------------------------------------------- 8. ghi ai đếm, lúc nào; bang()


@ca("ton ngay mai: luu_o ghi ai dem luc nao cho dung o, va bang() bay nhan, so may, ai, luc")
def _():
	m = _tao_dong(ma_hang="BAWC00055", ton_cu=3, nguon_ton_cu=MAY, may_chuyen_ton_cu=3)
	bang_mai = BangGia(ngay="2026-08-16", dong=[m])
	_dem(bang_mai, "BAWC00055", "ton_d1", 2)
	ghi = json.loads(m.get("kiem_dem_ghi"))
	la("chỉ ô d1 có vết", sorted(ghi.keys()), ["ton_d1"])
	la("ghi đúng người", ghi["ton_d1"]["ai"], frappe.session.user)
	dung("có giờ", bool(ghi["ton_d1"]["luc"]))
	_dem(bang_mai, "BAWC00055", "ton_d2", 0)
	ghi = json.loads(m.get("kiem_dem_ghi"))
	la("đếm 0 cũng có vết", sorted(ghi.keys()), ["ton_d1", "ton_d2"])
	cua = CuaGia(**{"KB-2026-08-16": bang_mai})
	with cua:
		kq = kiem_banh.bang("2026-08-16")
	n = kq["dong"][0]["nguon"]
	la("d1 Đã kiểm đếm", (n["ton_d1"]["trang_thai"], n["ton_d1"]["ai"]), ("Đã kiểm đếm", frappe.session.user))
	la("d2 đếm 0 cũng Đã kiểm đếm", n["ton_d2"]["trang_thai"], "Đã kiểm đếm")
	la("cũ hơn Tự chuyển, số máy 3", (n["ton_cu"]["trang_thai"], n["ton_cu"]["may_chuyen"]), ("Tự chuyển", 3))
	la("khoá số vẫn nguyên", (kq["dong"][0]["ton_cu"], kq["dong"][0]["ton_d1"], kq["dong"][0]["ton_d2"]), (3, 2, 0))


@ca("ton ngay mai: luu_o cot sx/huy KHONG dinh vao nguon o ton")
def _():
	m = _tao_dong(ma_hang="BAWC00055")
	bang_mai = BangGia(ngay="2026-08-16", dong=[m])
	_dem(bang_mai, "BAWC00055", "sx", 4)
	_dem(bang_mai, "BAWC00055", "huy", 1)
	la("sx ghi", m.get("sx"), 4)
	la("không ô tồn nào đổi nguồn", [m.get("nguon_" + o) for o in kiem_banh.O_TON], ["", "", ""])
	la("không có vết đếm", m.get("kiem_dem_ghi"), "")


# ------------------------------------------------------------ 9. khai báo


@ca("ton ngay mai: doctype Kiem Banh Dong co ba o nguon, ba o so may, o ai dem; chi doc")
def _():
	d = json.loads(_doc("vagabond", "doctype", "kiem_banh_dong", "kiem_banh_dong.json"))
	theo_ten = {f["fieldname"]: f for f in d["fields"]}
	for o in kiem_banh.O_TON:
		n = theo_ten.get("nguon_" + o)
		dung("có nguon_%s" % o, n is not None)
		la("Select với hai giá trị", n["options"], "\nTu chuyen\nDa kiem dem")
		la("chỉ đọc", n.get("read_only"), 1)
		may = theo_ten.get("may_chuyen_" + o)
		dung("có may_chuyen_%s" % o, may is not None and may["fieldtype"] == "Int")
		dung("có trong field_order", ("nguon_" + o) in d["field_order"] and ("may_chuyen_" + o) in d["field_order"])
	la("ô ai đếm là Small Text", theo_ten["kiem_dem_ghi"]["fieldtype"], "Small Text")


@ca("ton ngay mai: chot_ngay khong con gan thang m.ton_x = ..., moi o di qua ghi_o_chuyen")
def _():
	"""Điều 18: một nguồn ghi. Dò chuỗi chỉ để chốt 'không còn chỗ nào tự ghi'."""
	src = _doc("kiem_banh.py")
	i = src.find("def chot_ngay(")
	j = src.find("\ndef ", i + 10)
	than = src[i:j]
	for o in kiem_banh.O_TON:
		dung("không còn 'm.%s =' trong chot_ngay" % o, ("m.%s =" % o) not in than)
	la("ba lời gọi ghi_o_chuyen", than.count("ghi_o_chuyen(m,"), 3)
	dung("không còn nhánh continue khi còn 0 mà ngày mai có dòng",
		"if not (cu or lo[2][0] or lo[3][0]):\n\t\t\tcontinue" not in than)
