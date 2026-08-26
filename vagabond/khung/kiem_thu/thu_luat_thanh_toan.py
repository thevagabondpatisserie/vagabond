# -*- coding: utf-8 -*-
"""Ca kiểm cho luật phương thức thanh toán dùng chung mọi màn tính tiền.

Toàn phép thuần, không cần Frappe, không cần requests, không cần site.
`luat_thanh_toan.py` cố ý không import gì cả nên chạy được trên máy CI tay
không - bài học ngày 20/08 khi ba ca CI đỏ vì một ca kiểm kéo theo thư viện
mạng.

Số liệu trong các ca dưới đây lấy từ hai sự cố thật ngày 25 và 26/08/2026.
"""

from vagabond import luat_thanh_toan as L
from vagabond.khung.kiem_thu.nen import ca, dung, la


# --------------------------------------------- luat 1: khong xoa ma nguoi go

@ca("ma tham chieu: man hinh khong gui gi thi GIU nguyen ma cu")
def _giu_ma_cu():
	# Ca that: hoa don 92561 ngay 26/08/2026. Thu ngan da luu ma chuan chi
	# 046327 cho may ShinhanBank. Phan thanh toan khoa lai nen man hinh
	# khong con ve o nhap, bam Ghi so thi gui len chuoi rong. Truoc khi vá,
	# chuoi rong do xoa mat ma va cau bao loi doi ma bat buoc bung ra ngay
	# sau do.
	la("giu ma", L.ma_can_ghi("", "046327", "Thẻ - ShinhanBank", "Thẻ - ShinhanBank"),
		"046327")
	la("None cung giu", L.ma_can_ghi(None, "046327", "Thẻ - ShinhanBank", "Thẻ - ShinhanBank"),
		"046327")
	la("toan khoang trang cung giu",
		L.ma_can_ghi("   ", "046327", "Thẻ - ShinhanBank", "Thẻ - ShinhanBank"), "046327")


@ca("ma tham chieu: go ma moi thi ma moi thang")
def _ma_moi_thang():
	la("de len", L.ma_can_ghi("F62221", "046327", "Thẻ - ShinhanBank", "Thẻ - ShinhanBank"),
		"F62221")
	la("cat khoang trang", L.ma_can_ghi("  F62221  ", "046327", "x", "x"), "F62221")


@ca("ma tham chieu: DOI phuong thuc thi ma cu phai roi")
def _doi_pt_thi_xoa():
	# Ma chuan chi cua may Shinhan ma con nam do khi chuyen sang Tien mat
	# la tro vao mot giao dich khong con lien quan. Giu lai con hai hon xoa.
	la("doi sang tien mat", L.ma_can_ghi("", "046327", "Tiền mặt", "Thẻ - ShinhanBank"), "")
	la("doi va go ma moi", L.ma_can_ghi("GF-689", "046327", "GrabFood", "Thẻ - ShinhanBank"),
		"GF-689")


@ca("ma tham chieu: don chua co phuong thuc cu thi khong coi la doi")
def _chua_co_pt_cu():
	# Don moi ve, chua ai chon phuong thuc. Luc nay pt_cu rong, khong duoc
	# hieu la "vua doi phuong thuc" roi xoa mat ma may vua doc tu Pancake.
	la("giu ma", L.ma_can_ghi("", "MB12345", "Chuyển khoản", ""), "MB12345")
	la("ca hai rong", L.ma_can_ghi("", "", "Tiền mặt", ""), "")


# ------------------------------------- luat 2: nguon don tu suy ra phuong thuc

@ca("nguon don: san giao do chi di mot phuong thuc thi may tu chon")
def _san_tu_chon():
	la("ShopeeFood", L.pt_theo_nguon("", ["ShopeeFood"], True), "ShopeeFood")
	la("GrabFood", L.pt_theo_nguon("", ["GrabFood"], True), "GrabFood")
	dung("tu chon duoc", L.nguon_tu_chon_duoc(True, ["BeFood"]))


@ca("nguon don: chon sai thi may nan ve lua chon hop le duy nhat")
def _nan_lua_chon_sai():
	# Ca that: don 2874 ngay 25/08/2026, nguon ShopeeFood ma ai do de
	# "Chuyen khoan". Phep kiem cu chan thang, chuoi cuoi ngay treo don do
	# lai va khong ai go duoc ngoai viec vao sua tay.
	la("nan ve dung san", L.pt_theo_nguon("Chuyển khoản", ["ShopeeFood"], True),
		"ShopeeFood")
	dung("co ghi nhan da nan", L.may_da_nan("Chuyển khoản", "ShopeeFood"))
	dung("khong nan thi khong ghi", not L.may_da_nan("ShopeeFood", "ShopeeFood"))
	dung("o dang trong khong tinh la nan", not L.may_da_nan("", "ShopeeFood"))


@ca("nguon don: danh sach chung cua quay thi TUYET DOI khong tu chon")
def _quay_khong_tu_chon():
	# Cai bay: ai do tat bot phuong thuc o man Cai dat lam danh sach chung
	# rut xuong con mot cai. Luc do may KHONG duoc tu dien, vi day khong
	# phai danh sach rieng cua nguon ma la danh sach chung dang bi thu hep.
	la("con mot nhung khong rieng", L.pt_theo_nguon("", ["Tiền mặt"], False), "")
	dung("khong tu chon duoc", not L.nguon_tu_chon_duoc(False, ["Tiền mặt"]))
	la("nhieu lua chon thi giu nguyen o dang co",
		L.pt_theo_nguon("Tiền mặt", ["Tiền mặt", "Chuyển khoản"], False), "Tiền mặt")
	la("nhieu lua chon va dang trong thi van trong",
		L.pt_theo_nguon("", ["Tiền mặt", "Chuyển khoản"], False), "")


@ca("nguon don: nguon rieng ma con nhieu phuong thuc thi khong tu chon")
def _nguon_rieng_nhieu_pt():
	# "Khach si" co danh sach rieng nhung gom hai phuong thuc, khong suy
	# ra duoc cai nao.
	la("khach si", L.pt_theo_nguon("", ["Chuyển khoản", "Tiền mặt"], True), "")
	dung("khong tu chon duoc", not L.nguon_tu_chon_duoc(True, ["Chuyển khoản", "Tiền mặt"]))


@ca("nguon don: danh sach rong thi khong bao gio tu chon")
def _danh_sach_rong():
	la("rong", L.pt_theo_nguon("Tiền mặt", [], True), "Tiền mặt")
	dung("khong tu chon", not L.nguon_tu_chon_duoc(True, []))
	dung("chuoi trang khong tinh la mot lua chon", not L.nguon_tu_chon_duoc(True, ["  "]))
