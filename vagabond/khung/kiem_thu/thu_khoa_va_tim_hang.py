# -*- coding: utf-8 -*-
"""Hai lỗi Sales báo ngày 26/08/2026, và cái thứ ba lộ ra khi đọc ảnh chụp.

1. *"Bánh Very Berry 18 và Mille Crepe Tiramisu 18cm đã bán nhưng hệ thống
   không cập nhật số đã đặt, load đồng bộ lại Pancake thì nó báo lỗi này."*
   Kèm ảnh: một dòng chữ đỏ giữa màn kiểm bánh, nguyên văn thông điệp của
   thư viện mạng, có cả đường dẫn.

2. *"Bên xuất huỷ đang bị thiếu mã các sản phẩm như bánh ổ, bánh nướng."*
   Không mã nào thiếu. Trần cũ là 60 dòng xếp theo vần chữ cái, mà tên bánh
   nào cũng bắt đầu bằng chữ "Bánh", nên 60 dòng đầu là hết sạch Croissant.

3. LỘ KHOÁ API. Trong đúng dòng chữ đỏ đó có `api_key=...` của tiệm, chữ to,
   ai đứng cạnh cũng đọc được. Sales không hề biết mình vừa chụp cái gì.
   Đây là cái nặng nhất trong ba cái, và không ai báo nó cả.
"""

import io
import os

from vagabond import xuat_kho
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.lib import giau_khoa


def _js(duong):
	goc = os.path.dirname(os.path.dirname(os.path.abspath(xuat_kho.__file__)))
	return io.open(os.path.join(goc, "vagabond", duong), encoding="utf-8").read()


def _py(ten):
	goc = os.path.dirname(os.path.abspath(xuat_kho.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


# ----------------------------------------------------------- giấu khoá API


@ca("giấu khoá: khoá API không bao giờ lọt ra thông điệp cho người đọc")
def _():
	# Nguyên văn dòng Sales chụp được, chỉ đổi khoá đi.
	that = (
		"requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: "
		"https://pos.pages.fm/api/v1/shops/67355/orders?api_key=KhoaThat123%40"
		"&updateStatus=estimate_delivery_date&page_number=1"
	)
	ra = giau_khoa(that)
	dung("không còn khoá trong chuỗi", "KhoaThat123" not in ra)
	dung("vẫn đọc được là lỗi gì", "403" in ra and "Forbidden" in ra)
	dung("vẫn đọc được là gọi tới đâu", "pos.pages.fm" in ra)
	dung("các ô khác giữ nguyên", "updateStatus=estimate_delivery_date" in ra)
	# Vài cách viết khác cũng phải chặn được.
	dung("chặn access_token", "abc" not in giau_khoa("x?access_token=abc&y=1"))
	dung("chặn chữ hoa", "abc" not in giau_khoa("x?API_KEY=abc"))
	la("không có khoá thì không đổi gì", giau_khoa("chào anh"), "chào anh")
	la("chuỗi rỗng ra rỗng", giau_khoa(None), "")


@ca("giấu khoá: kiểm bánh không còn chỗ nào ném thẳng lỗi mạng lên màn hình")
def _():
	src = _py("kiem_banh.py")
	dung("có lớp lỗi riêng", "class LoiPancake(Exception):" in src)
	dung("có câu tiếng Việt cho từng mã", "def _loi_theo_ma(ma):" in src)
	dung("bắt lỗi khi kéo đơn", "except LoiPancake as e:" in src)
	dung("giấu khoá trước khi ghi nhật ký",
		'frappe.log_error(_giau_khoa(frappe.get_traceback())' in src)
	dung("ô chẩn đoán cũng giấu khoá",
		'ra["_loi"] = _giau_khoa(frappe.get_traceback()[-400:])' in src)
	# `raise_for_status` la cho da nem nguyen van thong diep co khoa.
	la("không còn raise_for_status trong kiểm bánh", src.count("raise_for_status"), 0)


@ca("giấu khoá: màn hình kiểm bánh có lớp chặn thứ hai của riêng nó")
def _():
	src = _js("trang/kiem-banh.js")
	dung("có hàm làm sạch", "function sach(t)" in src)
	dung("có hàm đổi lỗi sang tiếng Việt", "function loiNguoiDoc(t)" in src)
	dung("dòng báo đi qua hàm làm sạch", "el.textContent = sach(t);" in src)
	# Khong duoc con cho nao in thang e.message ra man.
	la("không còn chỗ nào in thẳng lỗi máy chủ", src.count("bao(e.message, true)"), 0)


# ------------------------------------------------ nghỉ sau khi Pancake từ chối


@ca("kiểm bánh: Pancake từ chối thì nghỉ một lát, không đập cửa đều tay")
def _():
	src = _py("kiem_banh.py")
	dung("có mốc nghỉ", "NGHI_SAU_TU_CHOI = 180" in src)
	dung("có hàm bắt đầu nghỉ", "def _bat_dau_nghi(ngay):" in src)
	dung("có hàm đếm ngược", "def _con_nghi(ngay):" in src)
	dung("đang nghỉ thì trả bảng cũ", "con = _con_nghi(ngay)" in src)
	# Giãn cách phải NỚI RA chứ không siết lại: nhiều máy cùng mở là nguyên
	# nhân gốc, mà 12 giây thì gần như không chặn được lượt nào.
	dung("giãn cách đã nới lên 45 giây", "GIAN_CACH_DONG_BO = 45" in src)
	man = _js("trang/kiem-banh.js")
	dung("màn hình cũng nghỉ theo", "if (NGHI_DEN && Date.now() < NGHI_DEN) return;" in man)
	dung("vòng tự động giãn lên hai phút", "}, 120000);" in man)
	# Còn ĐÚNG MỘT vòng ba mươi giây, và nó là vòng đọc bảng BTP của bếp -
	# vòng đó chỉ hỏi cơ sở dữ liệu của mình, không gọi Pancake. Đếm số lần
	# thay vì tìm chuỗi, để mai này ai thêm một vòng ba mươi giây gọi Pancake
	# nữa thì ca kiểm này đỏ.
	la("chỉ còn một vòng ba mươi giây, là vòng đọc BTP", man.count("}, 30000);"), 1)
	dung("và vòng đó không gọi Pancake",
		"if (DANG_SUA === null) taiBTP(); }, 30000);" in man)


@ca("kiểm bánh: kéo hết mười trang mà vẫn còn đơn thì phải nói ra, không nuốt")
def _():
	src = _py("kiem_banh.py")
	# Ngay dong don ma lang le bo phan con lai thi dung la "banh da ban ma
	# cot Da dat khong nhuc nhich" - loi Sales bao.
	dung("có ngoại lệ khi chạm trần trang",
		"Ngày này có hơn %d đơn" in src)
	dung("thử lại trước khi chịu thua", "THU_LAI = (2, 5)" in src)
	dung("chỉ thử lại với mã đáng thử",
		"if r.status_code not in (403, 408, 429, 500, 502, 503, 504):" in src)


# --------------------------------------------------------- tìm hàng xuất huỷ


def _kho_mau():
	"""Một kho nhỏ đủ để dựng lại đúng tình huống Sales gặp."""
	return [
		{"ma": "BANU00012", "ten": "Bánh Croissant Avocado, Mini size", "ton": 1},
		{"ma": "BANU00013", "ten": "Bánh Croissant Cherry, Mini size", "ton": 5},
		{"ma": "BANU00047", "ten": "Bánh Croissant nhân Cherry, Full size", "ton": 2},
		{"ma": "BAWC00066", "ten": "Bánh Ổ Roman De La Rose, size 12cm", "ton": 3},
		{"ma": "BAWC00025", "ten": "Bánh Ổ Hokkaido, size 16cm", "ton": 2},
		{"ma": "BANU00090", "ten": "Bánh nướng Patechaud", "ton": 7},
	]


@ca("xuất huỷ: gõ không dấu vẫn tìm ra bánh ổ và bánh nướng")
def _():
	kho = _kho_mau()
	ra = xuat_kho.loc_va_xep(kho, "banh o")
	ma = [d["ma"] for d in ra]
	dung("tìm ra Roman De La Rose", "BAWC00066" in ma)
	dung("tìm ra Hokkaido", "BAWC00025" in ma)
	dung("không lôi Croissant vào", "BANU00012" not in ma)

	ra = xuat_kho.loc_va_xep(kho, "banh nuong")
	la("gõ không dấu ra đúng một mã bánh nướng", [d["ma"] for d in ra], ["BANU00090"])


@ca("xuất huỷ: gõ các từ theo thứ tự nào cũng ra")
def _():
	kho = _kho_mau()
	xuoi = [d["ma"] for d in xuat_kho.loc_va_xep(kho, "o roman")]
	nguoc = [d["ma"] for d in xuat_kho.loc_va_xep(kho, "roman o")]
	la("hai thứ tự cho cùng kết quả", xuoi, nguoc)
	la("và ra đúng mã đó", xuoi, ["BAWC00066"])


@ca("xuất huỷ: gõ mã cũng ra, và mã khớp sát đứng trước")
def _():
	kho = _kho_mau()
	ra = xuat_kho.loc_va_xep(kho, "BAWC")
	la("lọc đúng theo tiền tố mã", sorted(d["ma"] for d in ra), ["BAWC00025", "BAWC00066"])
	# Go dung ca ma thi ma do phai la dong DAU, khong duoc nam duoi mot ma
	# khac chi vi ten no van A.
	ra = xuat_kho.loc_va_xep(kho, "BANU00047")
	la("gõ đúng mã thì mã đó đứng đầu", ra[0]["ma"], "BANU00047")


@ca("xuất huỷ: không gõ gì thì vẫn xếp theo tên, và cắt đúng số đã hẹn")
def _():
	kho = _kho_mau()
	ra = xuat_kho.loc_va_xep(kho, "")
	la("không lọc thì giữ đủ mã", len(ra), len(kho))
	la("xếp theo tên", [d["ten"] for d in ra], sorted(d["ten"] for d in kho))
	la("cắt đúng giới hạn", len(xuat_kho.loc_va_xep(kho, "", 2)), 2)


@ca("xuất huỷ: trần cũ 60 dòng đã được nới, và màn hình nói ra khi bị cắt")
def _():
	src = _py("xuat_kho.py")
	dung("trần mặc định đã nới lên 200", "def tim_hang(kho=None, tu_khoa=None, gioi_han=200):" in src)
	dung("phép lọc tách riêng để kiểm được", "def loc_va_xep(tho, tu_khoa, gioi_han=200):" in src)
	man = _js("public/js/bep/03-kho-chung-tu.js")
	dung("màn hình dùng cùng con số", "var XK_TRAN = 200;" in man)
	dung("bị cắt thì nói ra", "đây mới là ' + XK_TRAN + ' mã đầu" in man)


@ca("xuất huỷ: tìm ngay khi gõ, không bắt chờ bấm Enter")
def _():
	man = _js("public/js/bep/03-kho-chung-tu.js")
	dung("có bắt sự kiện gõ", "q.oninput = function () {" in man)
	dung("có chờ một nhịp rồi mới hỏi", "choTim = setTimeout(tim, 320);" in man)
	dung("bấm Enter thì hỏi ngay", "if (e.key !== 'Enter') return;" in man)
	# Go tiep trong luc dang hoi thi ket qua cu khong duoc ve de len ket qua
	# moi hon - loi kinh dien cua o tim go den dau hoi den do.
	dung("bỏ kết quả cũ khi người dùng gõ tiếp", "if ((q.value || '') !== dang) return;" in man)
