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
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_cot_huy_kiem_banh import (
	BangGia, CuaGia, _doc, _dong_moi, _tao_dong,
)

MAY, TAY, TRONG = kiem_banh.NGUON_MAY, kiem_banh.NGUON_TAY, kiem_banh.NGUON_TRONG


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
	# Codex P1 vòng 4: KHÔNG suy nguồn từ giá trị. 0 cũ cũng phải xác nhận.
	la("không rõ nguồn và bằng 0 CŨNG là Cần xác nhận", kiem_banh.trang_thai_o("", 0), "Cần xác nhận")
	la("ô mới chưa ghi thì trống", kiem_banh.trang_thai_o(TRONG, 0), "")
	dung("máy ghi được ô Tự chuyển", kiem_banh.may_duoc_ghi(MAY))
	dung("máy ghi được ô MỚI chưa ghi", kiem_banh.may_duoc_ghi(TRONG))
	dung("máy KHÔNG ghi ô đã đếm", not kiem_banh.may_duoc_ghi(TAY))
	dung("máy KHÔNG ghi ô chưa rõ nguồn dù là 0", not kiem_banh.may_duoc_ghi(""))
	dung("máy KHÔNG ghi ô chưa rõ nguồn (None)", not kiem_banh.may_duoc_ghi(None))
	la("dong_moi khai ba ô Chua ghi", [kiem_banh.dong_moi(ma_hang="A")["nguon_" + o] for o in kiem_banh.O_TON], [TRONG] * 3)


# --------------------------------------------- 2. chưa đếm: chuyển dương, về 0


@ca("ton ngay mai: o may chuyen hom truoc, hom nay con hang thi doi sang so moi, nhan Tu chuyen")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, da_dat=3)
	# Dòng do lần chốt trước đẻ ra: cả ba ô đều Tự chuyển.
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=5, nguon_ton_cu=MAY, nguon_ton_d2=MAY, nguon_ton_d1=MAY, may_chuyen_ton_d2=5)
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
	m = _dong_moi(ma_hang="BAWC00055")
	bang_mai = BangGia(ngay="2026-08-16", dong=[m])
	_dem(bang_mai, "BAWC00055", "ton_d2", 4)
	la("ô đếm mang nguồn tay", m.get("nguon_ton_d2"), TAY)
	la("ô khác vẫn Chua ghi", (m.get("nguon_ton_cu"), m.get("nguon_ton_d1")), (TRONG, TRONG))
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
	m = _dong_moi(ma_hang="BAWC00055", ton_d2=1, nguon_ton_d2=TAY)
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
	m = _dong_moi(ma_hang="BAWC00055")
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
	m2 = _dong_moi(ma_hang="BAWC00055")
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


@ca("ton ngay mai: du lieu cu khong ro nguon: co so HAY bang 0 deu giu, Can xac nhan, may chi ghi so ben canh")
def _():
	d = _tao_dong(ma_hang="BAWC00055", ton_d1=10, sx=4, da_dat=3)
	m = _tao_dong(ma_hang="BAWC00055", ton_d2=5, ton_cu=0, ton_d1=0)   # dữ liệu cũ, không có nguồn nào
	_nay, mai = _chot([d], mai=[m])
	r = mai.dong[0]
	la("ô 5 không rõ nguồn: giữ nguyên, nguồn vẫn trống, máy 7 bên cạnh", _o(r, "ton_d2"), (5, "", 7))
	la("nhãn Cần xác nhận", kiem_banh.trang_thai_o(r.get("nguon_ton_d2")), "Cần xác nhận")
	# Codex P1 vòng 4: 0 cũ có thể chính là số người đã đếm. Không đè, chỉ ghi số máy.
	la("ô 0 không rõ nguồn CŨNG giữ, máy 4 bên cạnh", _o(r, "ton_d1"), (0, "", 4))
	la("nhãn 0 cũ cũng là Cần xác nhận", kiem_banh.trang_thai_o(r.get("nguon_ton_d1")), "Cần xác nhận")
	la("ô cũ hơn 0 cũ giữ, máy 0", _o(r, "ton_cu"), (0, "", 0))
	# Người đếm lại ô Cần xác nhận thì thành Đã kiểm đếm.
	_dem(mai, "BAWC00055", "ton_d2", 5)
	la("đếm lại 5 thì hết Cần xác nhận", _o(r, "ton_d2"), (5, TAY, 7))


# --------------------------------------------- 8. ghi ai đếm, lúc nào; bang()


@ca("ton ngay mai: luu_o ghi ai dem luc nao cho dung o, va bang() bay nhan, so may, ai, luc")
def _():
	m = _dong_moi(ma_hang="BAWC00055", ton_cu=3, nguon_ton_cu=MAY, may_chuyen_ton_cu=3)
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
	m = _dong_moi(ma_hang="BAWC00055")
	bang_mai = BangGia(ngay="2026-08-16", dong=[m])
	_dem(bang_mai, "BAWC00055", "sx", 4)
	_dem(bang_mai, "BAWC00055", "huy", 1)
	la("sx ghi", m.get("sx"), 4)
	la("không ô tồn nào đổi nguồn", [m.get("nguon_" + o) for o in kiem_banh.O_TON], [TRONG] * 3)
	la("không có vết đếm", m.get("kiem_dem_ghi"), "")


# ------------------------------------------------------------ 9. khai báo


@ca("ton ngay mai: doctype Kiem Banh Dong co ba o nguon, ba o so may, o ai dem; chi doc")
def _():
	d = json.loads(_doc("vagabond", "doctype", "kiem_banh_dong", "kiem_banh_dong.json"))
	theo_ten = {f["fieldname"]: f for f in d["fields"]}
	for o in kiem_banh.O_TON:
		n = theo_ten.get("nguon_" + o)
		dung("có nguon_%s" % o, n is not None)
		# Bench 07/09 bat: ma nguon ghi "Chua ghi" ma Select chua co gia tri do,
		# moi insert bang Kiem banh deu no o _validate_selects. Chot: moi hang so
		# nguon trong ma nguon deu phai nam trong options cua doctype.
		cho_phep = n["options"].split("\n")
		for gt in (kiem_banh.NGUON_TRONG, kiem_banh.NGUON_MAY, kiem_banh.NGUON_TAY):
			dung("Select nguon_%s có giá trị %r" % (o, gt), gt in cho_phep)
		dung("và cho phép trống (dữ liệu cũ)", "" in cho_phep)
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


# ---------------------------------- 10. sửa qua Desk/API cũng phải để lại nguồn


class BangTruoc(BangGia):
	"""Bảng có bản trước khi lưu, như Document thật có get_doc_before_save."""

	def __init__(self, truoc=None, **kw):
		BangGia.__init__(self, **kw)
		self._truoc = truoc

	def get_doc_before_save(self):
		return self._truoc


def _sao(dong):
	return BangGia(ngay="2026-08-16", dong=[_tao_dong(**dict(d)) for d in dong])


@ca("ton ngay mai: sua o ton thang tren Desk/API (khong qua luu_o) thi lop doctype tu danh dau Da kiem dem kem ai va luc, ca sua duong lan sua ve 0")
def _():
	"""Codex P1 vòng 4: 7/Tự chuyển sửa thẳng thành 2, save vẫn 2/Tự chuyển,
	chốt hôm trước ghi lại 7, số người sửa mất."""
	m = _dong_moi(ma_hang="BAWC00055", ton_d1=7, nguon_ton_d1=MAY, may_chuyen_ton_d1=7,
		ton_d2=3, nguon_ton_d2=MAY, may_chuyen_ton_d2=3)
	b = BangTruoc(truoc=_sao([m]), ngay="2026-08-16", dong=[m])
	# Người sửa thẳng trên Desk: gán giá trị rồi save (validate thật chạy).
	m.ton_d1 = 2
	m.ton_d2 = 0
	frappe.flags.vgb_ton_da_co_nguon = False
	b.save()
	la("ô sửa dương thành Đã kiểm đếm, số máy cũ giữ để đối chiếu", _o(m, "ton_d1"), (2, TAY, 7))
	la("ô sửa về 0 cũng thành Đã kiểm đếm", _o(m, "ton_d2"), (0, TAY, 3))
	la("ô không sửa giữ nguồn cũ", m.get("nguon_ton_cu"), TRONG)
	ghi = json.loads(m.get("kiem_dem_ghi"))
	la("ghi ai cho đúng hai ô", sorted(ghi.keys()), ["ton_d1", "ton_d2"])
	la("đúng người", ghi["ton_d1"]["ai"], frappe.session.user)
	# Rồi chốt hôm trước: không được ghi lại 7.
	d = _tao_dong(ma_hang="BAWC00055", sx=9)
	nay = BangGia(ngay="2026-08-15", dong=[d])
	cua = CuaGia(**{"KB-2026-08-15": nay, "KB-2026-08-16": b})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	with cua:
		kiem_banh.chot_ngay("2026-08-15")
	la("chốt không đè số người sửa trên Desk", _o(m, "ton_d1"), (2, TAY, 9))


@ca("ton ngay mai: chot_ngay va luu_o giuong co nen lop doctype KHONG danh dau nham o may vua ghi la tay")
def _():
	m = _dong_moi(ma_hang="BAWC00055", ton_d1=7, nguon_ton_d1=MAY, may_chuyen_ton_d1=7)
	b = BangTruoc(truoc=_sao([m]), ngay="2026-08-16", dong=[m])
	d = _tao_dong(ma_hang="BAWC00055", sx=9)
	nay = BangGia(ngay="2026-08-15", dong=[d])
	cua = CuaGia(**{"KB-2026-08-15": nay, "KB-2026-08-16": b})
	cua.btp = Doi({"dong": [], "cap_nhat_luc": None, "save": lambda *a, **k: None})
	with cua:
		kiem_banh.chot_ngay("2026-08-15")
	la("máy đổi 7 thành 9 và vẫn là Tự chuyển", _o(m, "ton_d1"), (9, MAY, 9))
	la("cờ đã hạ sau khi chốt", bool(frappe.flags.get("vgb_ton_da_co_nguon")), False)
	# luu_o qua cửa: một lần đánh dấu, ai/lúc một lần.
	b2 = BangTruoc(truoc=_sao([m]), ngay="2026-08-16", dong=[m])
	_dem(b2, "BAWC00055", "ton_d1", 4)
	la("luu_o vẫn Đã kiểm đếm", _o(m, "ton_d1"), (4, TAY, 9))
	la("cờ đã hạ sau luu_o", bool(frappe.flags.get("vgb_ton_da_co_nguon")), False)


@ca("ton ngay mai: dong MOI chua khai nguon thi lop doctype khai Chua ghi; dong cu nguon trong thi de yen")
def _():
	moi = _tao_dong(ma_hang="BAWC00099")
	del moi["name"]          # chưa có name: dòng vừa append
	cu = _tao_dong(ma_hang="BAWC00055", ton_d2=4)   # dữ liệu cũ, nguồn trống
	b = BangTruoc(truoc=_sao([cu]), ngay="2026-08-16", dong=[cu, moi])
	b.save()
	la("dòng mới được khai Chua ghi", [moi.get("nguon_" + o) for o in kiem_banh.O_TON], [TRONG] * 3)
	la("dòng cũ vẫn nguồn trống (Cần xác nhận)", [cu.get("nguon_" + o) for o in kiem_banh.O_TON], ["", "", ""])


# ---------------------------------------- 11. đếm 0 rồi không xoá được dòng


@ca("ton ngay mai: dem ra 0 roi thi xoa_dong bi CHAN (API truc tiep) va bang() bao xoa_duoc = 0; dong moi chua ghi gi van xoa duoc")
def _():
	"""Codex P1 vòng 4: mọi số bằng 0 nhưng có Đã kiểm đếm và ai/lúc, xoa_dong
	vẫn ok = 1 và mất luôn dấu vết."""
	m = _dong_moi(ma_hang="BAWC00055")
	b = BangGia(ngay="2026-08-16", dong=[m])
	_dem(b, "BAWC00055", "ton_d2", 0)
	dung("có dấu vết", kiem_banh.co_dau_vet(m))
	cua = CuaGia(**{"KB-2026-08-16": b})
	with cua:
		nem("xoa_dong phải ném", lambda: kiem_banh.xoa_dong("2026-08-16", "BAWC00055"))
		la("dòng vẫn còn", len(b.dong), 1)
		kq = kiem_banh.bang("2026-08-16")
	la("bang() báo không xoá được", kq["dong"][0]["xoa_duoc"], 0)
	# Dòng mới chưa ghi gì thì vẫn gỡ được (gõ nhầm mã).
	m2 = _dong_moi(ma_hang="BAWC00077")
	b2 = BangGia(ngay="2026-08-16", dong=[m2])
	dung("chưa có dấu vết", not kiem_banh.co_dau_vet(m2))
	cua2 = CuaGia(**{"KB-2026-08-16": b2})
	with cua2:
		la("bang() báo xoá được", kiem_banh.bang("2026-08-16")["dong"][0]["xoa_duoc"], 1)
		la("xoá được", kiem_banh.xoa_dong("2026-08-16", "BAWC00077"), {"ok": 1})
	la("đã gỡ", len(b2.dong), 0)
	# Máy đã chuyển số vào (kể cả 0) cũng là dấu vết đối chiếu.
	m3 = _dong_moi(ma_hang="BAWC00088", nguon_ton_d1=MAY, may_chuyen_ton_d1=0)
	dung("máy chuyển 0 chưa tính là dấu vết (chưa có số để đối chiếu)", not kiem_banh.co_dau_vet(m3))
	m4 = _dong_moi(ma_hang="BAWC00089", nguon_ton_d1=MAY, may_chuyen_ton_d1=3)
	dung("máy chuyển 3 là dấu vết", kiem_banh.co_dau_vet(m4))


@ca("ton ngay mai: man kiem banh an nut xoa theo xoa_duoc cua may chu, khong tu suy tu so")
def _():
	js = _doc("trang", "kiem-banh.js")
	dung("trongTron nhìn xoa_duoc", "d.xoa_duoc" in js)
	dung("them_dong đi qua dong_moi", "dong_moi(ma_hang=ma_hang" in _doc("kiem_banh.py"))
	dung("dong_bo thêm dòng đi qua dong_moi", _doc("kiem_banh.py").count("dong_moi(") >= 4)


@ca("ton ngay mai: dong moi tren parent moi va parent cu giu so nhap Desk, ke ca xac nhan 0")
def _():
	for parent_moi in (True, False):
		for so in (2, 0):
			m = _tao_dong(ma_hang="BAWC00055", ton_d2=so, __islocal=1)
			if so == 0:
				m.nguon_ton_d2 = TAY
			b = BangTruoc(truoc=None if parent_moi else _sao([]), dong=[m])
			frappe.flags.vgb_ton_da_co_nguon = False
			b.save()
			la("nguồn tay", m.nguon_ton_d2, TAY)
			dung("có audit", bool(json.loads(m.kiem_dem_ghi)["ton_d2"]["ai"]))
			kiem_banh.ghi_o_chuyen(m, "ton_d2", 7, None)
			la("máy không đè", m.ton_d2, so)


@ca("ton ngay mai: Desk go child da dem 0 hoac co so bi chan, dong trang van go duoc")
def _():
	for kw in ({"nguon_ton_d1": TAY}, {"may_chuyen_ton_d1": 3}, {"sx": 5}, {"huy": 1}, {"giu_cho": 2}):
		m = _tao_dong(ma_hang="BAWC00055", **kw)
		b = BangTruoc(truoc=_sao([m]), dong=[])
		nem("không được gỡ dòng có nghiệp vụ", b.save)
	m = _dong_moi(ma_hang="BAWC00055")
	b = BangTruoc(truoc=_sao([m]), dong=[])
	b.save()
	la("dòng trắng gỡ được", b.dong, [])


@ca("ton ngay mai: bang va API dung cung dieu kien xoa cho cac cot nghiep vu")
def _():
	for cot in kiem_banh.SO_PHAI_RONG:
		m = _dong_moi(ma_hang="BAWC00055", **{cot: 5})
		b = BangGia(ngay="2026-08-16", dong=[m])
		with CuaGia(**{"KB-2026-08-16": b}):
			la("ẩn xoá khi có " + cot, kiem_banh.bang("2026-08-16")["dong"][0]["xoa_duoc"], 0)
			nem("API chặn " + cot, lambda: kiem_banh.xoa_dong("2026-08-16", "BAWC00055"))


@ca("ton ngay mai: cong dong thoi khong xanh khi ca hai loi, bo chot hoac thieu audit")
def _():
	from vagabond.khung.kiem_dong_thoi import _vong_dem_dat
	ra = {"dem": {"ok": 1}, "chot": {"ok": 1}}
	d = {"ton_d1": 2, "nguon_ton_d1": TAY, "may_chuyen_ton_d1": 9,
		"kiem_dem_ghi": json.dumps({"ton_d1": {"ai": "Administrator", "luc": "2026-09-07"}})}
	nay = {"tinh_trang": "Da chot", "chot_luc": "2026-09-07"}
	dung("ca đúng đạt", _vong_dem_dat(ra, d, nay, TAY))
	dung("cả hai lỗi phải đỏ", not _vong_dem_dat({"dem": {"ok": 0}, "chot": {"ok": 0}}, d, nay, TAY))
	dung("bỏ chốt phải đỏ", not _vong_dem_dat(ra, d, {"tinh_trang": "Dang ban"}, TAY))
	dung("thiếu audit phải đỏ", not _vong_dem_dat(ra, dict(d, kiem_dem_ghi="{}"), nay, TAY))
	dung("lỗi lạ phải đỏ", not _vong_dem_dat(dict(ra, dem={"ok": 0, "loi": "ValueError: loi"}), d, nay, TAY))
	dung("retry lỗi cạnh tranh được chấp nhận khi số cuối đúng", _vong_dem_dat(dict(ra, dem={"ok": 0, "loi": "TimestampMismatchError: thu lai"}), d, nay, TAY))


@ca("ton ngay mai: API khong xoa nguon va audit cua o da dem khi so khong doi")
def _():
	m = _dong_moi(ma_hang="BAWC00055")
	kiem_banh.ghi_dem_tay(m, "ton_d1", 0, "nguoi-dem", "2026-09-07")
	b = BangTruoc(truoc=_sao([m]), dong=[m])
	m.nguon_ton_d1 = TRONG
	m.kiem_dem_ghi = ""
	b.save()
	la("giữ nguồn", m.nguon_ton_d1, TAY)
	la("giữ người đếm", json.loads(m.kiem_dem_ghi)["ton_d1"]["ai"], "nguoi-dem")


@ca("ton ngay mai: dong_bo giu dong ma la co so hoac audit, don dong trang va van luu duoc")
def _():
	# Chạy dong_bo và validate thật. Chỉ thay I/O Pancake, cache và DB.
	# Trước bản sửa, lọc mã lạ làm mất dòng rồi chính validate từ chối lưu.
	from contextlib import ExitStack
	from unittest.mock import Mock, patch
	for kw in ({"sx": 5}, {"da_dat": 1}, {"nguon_ton_d1": TAY}):
		la_co_so = _tao_dong(ma_hang="MA-LA", **kw)
		la_trang = _dong_moi(ma_hang="MA-TRANG")
		hop_le = _dong_moi(ma_hang="BAWC00055", sx=3)
		b = BangTruoc(truoc=_sao([la_co_so, la_trang, hop_le]),
			ngay="2026-08-16", dong=[la_co_so, la_trang, hop_le])
		nhat_ky = Mock()
		with ExitStack() as cua:
			for ten, gia in {
				"cfg": lambda: Doi({"pancake_shop_id": "thu"}),
				"key": lambda *a: "khoa-thu", "_con_nghi": lambda *a: 0,
				"_keo_don": lambda *a: [], "_lay_hoac_tao": lambda *a: b,
				"_dem_banh": lambda *a: ({}, {}, {}, {}),
				"_ghi_don_khac": lambda *a: None, "_ghi_giu_cho": lambda *a: None,
				"bang": lambda *a: {"dong": b.dong},
			}.items():
				cua.enter_context(patch.object(kiem_banh, ten, gia))
			cua.enter_context(patch.object(kiem_banh.pancake_nhip, "ghi_ok", lambda: None))
			cua.enter_context(patch.object(frappe.db, "exists", lambda *a: False))
			cua.enter_context(patch.object(frappe.db, "commit", lambda: None))
			cua.enter_context(patch.object(frappe, "cache", lambda: Mock(get_value=lambda *a: True), create=True))
			cua.enter_context(patch.object(frappe, "log_error", nhat_ky))
			kiem_banh.dong_bo("2026-08-16")
		la("đồng bộ lưu thành công", b.so_lan_luu, 1)
		la("giữ dòng có số/audit và dòng hợp lệ", [d.ma_hang for d in b.dong], ["MA-LA", "BAWC00055"])
		la("có thông báo mã cần đối chiếu", nhat_ky.call_count, 1)
		dung("nhật ký nêu mã", "MA-LA" in nhat_ky.call_args[1]["message"])
		if "sx" in kw:
			la("số sản xuất còn nguyên", la_co_so.sx, 5)
		if "nguon_ton_d1" in kw:
			la("dấu đếm 0 còn nguyên", la_co_so.nguon_ton_d1, TAY)
