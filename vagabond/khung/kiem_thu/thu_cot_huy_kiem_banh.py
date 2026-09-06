# -*- coding: utf-8 -*-
"""Cột Huỷ trên bảng Kiểm bánh hôm nay.

Anh Việt chốt ngày 06/09/2026, hướng A của issue #216: *"Em thêm cột huỷ trên
màn kiểm bánh cho các bạn nhập tay theo dõi là được."*

Vì sao cửa hàng không đi qua phiếu xuất huỷ kho: `xuat_kho.tim_hang` chỉ liệt
kê mã còn tồn ERPNext trong kho đã chọn, mà Kho D1 không được nạp bánh hàng
ngày - 218 mã bánh thành phẩm chỉ 30 mã có tồn ở đó, và không mã nào trong số
Dễ báo thiếu từng có một dòng sổ kho nào ở D1. Gốc rễ là Sổ nhận bánh cố ý
không sinh Stock Entry (quyết định 23/08/2026, lý do đầy đủ trong
`vagabond/nhan_banh.py`). Nên bánh giao ra quầy nằm ngoài tồn ERPNext.

BA CHỖ CÓ THỂ HỎNG ÂM THẦM, mỗi chỗ một ca chặn:

  1. Huỷ không trừ vào "bán được" -> quầy vẫn bán con bánh đã vứt.
  2. Huỷ không ăn vào lô hàng lúc chốt ngày -> mỗi ngày huỷ bao nhiêu thì tồn
     đầu ngày mai phình ảo bấy nhiêu, cộng dồn mãi.
  3. Huỷ không nằm trong SO_PHAI_RONG -> dấu x xoá dòng ăn mất số huỷ đã ghi.

Các ca dưới đây CHẠY THẬT hàm và lớp doctype, không dò chuỗi trong mã nguồn.
Phép dò chuỗi chỉ dùng đúng một chỗ: chốt rằng không còn nơi nào tự cộng lại
"đã tiêu" thay vì gọi `so_da_tieu` (điều 18).
"""

import io
import os

from vagabond import kiem_banh
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la
from vagabond.vagabond.doctype.kiem_banh_ngay.kiem_banh_ngay import KiemBanhNgay

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*ten):
	with io.open(os.path.join(GOI, *ten), encoding="utf-8") as f:
		return f.read()


def _dong(**kw):
	"""Một dòng bảng kiểm bánh, mọi cột mặc định 0."""
	d = Doi({
		"ma_hang": "BAWC00001", "ten_banh": "Bánh thử",
		"ton_cu": 0, "nsx_cu": None, "ton_d2": 0, "nsx_d2": None,
		"ton_d1": 0, "nsx_d1": None, "sx": 0, "huy": 0,
		"da_dat": 0, "phat_sinh": 0, "don_khac": 0, "cho_chot": 0,
		"giu_cho": 0, "co_the_ban": 0,
	})
	d.update(kw)
	return d


def _tinh(**kw):
	"""Chạy THẬT validate của doctype rồi trả về "có thể bán"."""
	doc = KiemBanhNgay()
	d = _dong(**kw)
	doc.dong = [d]
	doc.validate()
	return d.co_the_ban


# --------------------------------------------------- 1. trừ vào "bán được"


@ca("huỷ trừ thẳng vào bán được, không đụng các cột khác")
def _():
	la("chưa huỷ gì", _tinh(ton_d1=10, sx=5), 15)
	la("huỷ 3", _tinh(ton_d1=10, sx=5, huy=3), 12)
	la("huỷ hết", _tinh(ton_d1=10, sx=5, huy=15), 0)
	# Huy nhieu hon ton la con so AM co that, khong duoc kep ve 0: bang phai
	# to do de nguoi doi chieu, giong het cot ban duoc am san co.
	la("huỷ quá tồn thì âm, không kẹp về 0", _tinh(ton_d1=2, huy=5), -3)


@ca("huỷ cộng dồn đúng với các cột đang có, không thay chỗ cột nào")
def _():
	chung = dict(ton_cu=4, ton_d2=3, ton_d1=2, sx=10, da_dat=5, phat_sinh=1,
		cho_chot=2, don_khac=1, giu_cho=1)
	la("chưa có cột huỷ", _tinh(**chung), 9)
	la("thêm huỷ 4", _tinh(huy=4, **chung), 5)


# --------------------------------------------------- 2. ăn vào lô lúc chốt


@ca("so_da_tieu gộp bán ra và huỷ, bỏ qua giữ chỗ")
def _():
	la("trống trơn", kiem_banh.so_da_tieu(), 0)
	la("chỉ bán", kiem_banh.so_da_tieu(3, 2, 1, 0), 6)
	la("bán và huỷ", kiem_banh.so_da_tieu(3, 2, 1, 4), 10)
	la("chỉ huỷ", kiem_banh.so_da_tieu(0, 0, 0, 7), 7)
	la("None cũng chịu được", kiem_banh.so_da_tieu(None, None, None, None), 0)
	la("không bao giờ âm", kiem_banh.so_da_tieu(-5, 0, 0, 0), 0)


@ca("bánh huỷ ăn vào lô cũ trước, KHÔNG chạy sang tồn ngày mai")
def _():
	# Bon lo xep tu cu toi moi: ton_cu, ton_d2, ton_d1, sx.
	lo = [[2, "cu"], [3, "d2"], [4, "d1"], [10, "sx"]]
	du = kiem_banh.tru_theo_lo(lo, kiem_banh.so_da_tieu(0, 0, 0, 6))
	la("không dư", du, 0)
	la("lô cũ nhất hết trước", lo[0][0], 0)
	la("lô d2 hết theo", lo[1][0], 0)
	la("lô d1 còn 3", lo[2][0], 3)
	la("lô bếp làm còn nguyên", lo[3][0], 10)


@ca("huỷ và bán cùng ngày thì cộng lại rồi mới ăn vào lô")
def _():
	lo = [[5, "cu"], [0, None], [0, None], [8, "sx"]]
	kiem_banh.tru_theo_lo(lo, kiem_banh.so_da_tieu(4, 0, 0, 3))
	la("lô cũ hết", lo[0][0], 0)
	la("ăn tiếp 2 vào lô bếp làm", lo[3][0], 6)


@ca("tiêu nhiều hơn tồn thì báo phần dư, không để lô âm")
def _():
	lo = [[2, "cu"], [1, "d1"]]
	du = kiem_banh.tru_theo_lo(lo, 9)
	la("dư 6", du, 6)
	la("lô không âm", [c[0] for c in lo], [0, 0])


@ca("KHÔNG còn chỗ nào tự cộng lại đã tiêu thay vì gọi so_da_tieu")
def _():
	"""Điều 18: lỗi kiểu này phải sửa bằng cách gom về một nguồn.

	Trước 06/09/2026 phép "đã tiêu" gõ tay ở hai chỗ trong chot_ngay - một
	chỗ trừ lô hàng, một chỗ trừ vỏ BTP. Thêm cột Huỷ mà chỉ sửa một chỗ là
	số vỏ BTP lệch âm thầm. Ca này chốt để người sau không gõ lại lần ba.
	"""
	src = _doc("kiem_banh.py")
	i = src.find("def chot_ngay(")
	than = src[i:src.find("\ndef ", i + 10)]
	dung("không còn phép cộng tay trong chot_ngay",
		"(d.da_dat or 0) + (d.phat_sinh or 0)" not in than)
	la("gọi so_da_tieu đúng hai lần", than.count("so_da_tieu("), 2)


# --------------------------------------------------- 3. các cửa chặn khác


@ca("huỷ là cột người gõ tay, và luu_o nhận nó")
def _():
	dung("huỷ sửa tay được", "huy" in kiem_banh.SUA_DUOC)
	for cot in ("ton_cu", "ton_d2", "ton_d1", "sx"):
		dung("vẫn giữ %s" % cot, cot in kiem_banh.SUA_DUOC)
	# Cac cot may dem van phai dong: do la ca ly do phan he nay ton tai.
	for cot in ("da_dat", "phat_sinh", "don_khac", "cho_chot", "giu_cho", "co_the_ban"):
		dung("%s vẫn không sửa tay được" % cot, cot not in kiem_banh.SUA_DUOC)


@ca("dòng đang có số huỷ thì dấu x không xoá được")
def _():
	dung("huỷ nằm trong danh sách phải rỗng", "huy" in kiem_banh.SO_PHAI_RONG)
	for cot in ("ton_cu", "ton_d2", "ton_d1", "sx", "da_dat", "phat_sinh",
			"cho_chot", "don_khac"):
		dung("vẫn giữ %s" % cot, cot in kiem_banh.SO_PHAI_RONG)


@ca("cột huỷ đã khai trong doctype, đặt ngay sau Bếp làm")
def _():
	import json

	d = json.loads(_doc("vagabond", "doctype", "kiem_banh_dong",
		"kiem_banh_dong.json"))
	ten = [f["fieldname"] for f in d["fields"]]
	dung("có ô huy", "huy" in ten)
	la("nằm ngay sau sx", ten[ten.index("sx") + 1], "huy")
	la("cũng đứng đúng chỗ trong field_order",
		d["field_order"][d["field_order"].index("sx") + 1], "huy")
	o = [f for f in d["fields"] if f["fieldname"] == "huy"][0]
	la("là số nguyên", o["fieldtype"], "Int")


@ca("máy chủ trả cột huỷ xuống màn hình")
def _():
	src = _doc("kiem_banh.py")
	i = src.find("def bang(")
	than = src[i:src.find("\nSUA_DUOC", i)]
	dung("bảng có trả huy", '"huy": d.huy or 0' in than)


# --------------------------------------------------- 4. màn hình


@ca("màn kiểm bánh vẽ ô Huỷ, gõ tay được, nằm sau Bếp làm")
def _():
	js = _doc("trang", "kiem-banh.js")
	i = js.find('+ o(d, "sx", "Bếp làm "')
	dung("tìm thấy ô Bếp làm", i > 0)
	sau = js[i:i + 900]
	j = sau.find('o(d, "huy"')
	dung("ô Huỷ nằm sau ô Bếp làm", j > 0)
	dung("ô Huỷ đứng trước ô Đã đặt", j < sau.find('o(d, "da_dat"'))
	dung("gõ tay được", 'o(d, "huy", "Huỷ", d.huy, true, "huy")' in js)
	dung("dòng có số huỷ thì không xoá được", "d.huy ||" in js)


@ca("lưới đủ chỗ cho ô mới và các mốc màu đã dịch theo")
def _():
	"""Lưới là grid cố định 16 cột và tô màu theo nth-child. Thêm một ô mà
	quên hai chỗ này thì cả bảng lệch màu một cột, nhìn là nhầm cột ngay."""
	css = _doc("trang", "kiem-banh.html")
	dung("lưới 17 cột", "grid-template-columns:repeat(17,1fr)" in css)
	dung("không còn lưới 16 cột", "repeat(16,1fr)" not in css)
	dung("khối đơn máy đếm dịch sang 6..12",
		"nth-child(n+6):nth-child(-n+12)" in css)
	dung("ô BÁN ĐƯỢC dịch sang 13", "nth-child(13){background:#fff}" in css)
	dung("hai ô BTP dịch sang 14 và 15",
		"nth-child(14),#kb .kb-so .kb-o:nth-child(15){background:#fefce8}" in css)
	dung("ô Huỷ có màu riêng", ".kb-o.huy" in css)
