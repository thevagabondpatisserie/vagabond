# -*- coding: utf-8 -*-
"""Moi cho chon nha cung cap deu phai co duong TAO MOI ngay tai cho.

Anh Viet 21/08/2026: chi Dung lap phieu dong BHXH, go "BHXH CO SO TAN DINH"
roi go tiep "bao hiem xa hoi", ca hai lan deu khong ra gi. Man hinh bao
"Chua chon ben nhan tien" va het duong. Kiem lai tren site that: ca tiem co
520 nha cung cap, khong cai nao la ben bao hiem.

Loi khong nam o phep tim - `ds_nguoi_ung` co tim theo `supplier_name like`
dang hoang. Loi nam o cho: KHONG TIM THAY thi khong lam gi duoc nua.

Nen luat cua tep nay: man nao cho chon nha cung cap thi phai co du ba thu.

  1. Mot o de go tim.
  2. Cau noi ro la khong tim thay, chu khong im lang de danh sach rong.
  3. Nut tao moi, va nut do phai mang SAN cai ten vua go sang man tao.

Diem thu ba de bi bo qua nhat, ma no la diem quan trong nhat: bat nguoi ta
go lai lan thu ba cai ten ho vua go hai lan khong ra gi la cach nhanh nhat
de ho bo cuoc va di nhan tin hoi.
"""

import io
import os

from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_thu.nen import ca, dung


def _js(ten):
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


# ------------------------------------------------------ dung cu dung chung


@ca("tìm NCC: có khung dùng chung, không rải mỗi màn một kiểu")
def _():
	js = _js("19-ho-so-tt.js")
	dung("có hàm dựng khung tìm", "function hsKhungTimNcc(" in js)
	dung("có hàm nối nút", "function hsNoiNutTaoNcc(" in js)
	dung("nút mang tên vừa gõ sang màn tạo", "nccTaoNhanh(" in js)


@ca("tìm NCC: màn tạo nhà cung cấp nhận được việc phải làm sau khi lưu")
def _():
	js = _js("16-mua-hang.js")
	dung("có chỗ để màn gọi cài lại việc", "var nccXongThi = null;" in js)
	dung("có cửa mở nhanh", "function nccTaoNhanh(" in js)
	dung("điền sẵn tên vừa gõ", "nccF.ten = g;" in js)
	# Phai XOA sau khi dung: de lai la lan sau ai mo man tao tu man Mua
	# hang cung bi nem di cho khac.
	than = js.split("var cb = nccXongThi;")[1]
	dung("lấy ra xong thì xoá ngay", "nccXongThi = null;" in than[:120])


# --------------------------------------------------- du ba man deu co nut


@ca("tìm NCC: cả ba màn chọn nhà cung cấp đều có nút tạo mới")
def _():
	js = _js("19-ho-so-tt.js")
	# Ba man: hoan ung khong hoa don, chi tu TK cong ty, va o chon nguoi
	# duoc hoan ung cua man hoan ung co hoa don.
	dung("có ba chỗ dựng khung tìm", js.count("hsKhungTimNcc(") >= 4)
	dung("có ba chỗ nối nút", js.count("hsNoiNutTaoNcc(") >= 4)
	for man in ("scrHoanUngTao", "scrChiCongTyTao", "scrHoSoTTTao"):
		than = js.split("function " + man)[1].split("\nasync function ")[0]
		dung("%s có nối nút tạo" % man, "hsNoiNutTaoNcc(" in than)


@ca("tìm NCC: tạo xong thì chọn luôn người vừa tạo, không bắt tìm lại")
def _():
	js = _js("19-ho-so-tt.js")
	# Ba lan goi deu phai gan ma vua tao vao bien dang chon.
	dung("gán vào huNguoi", js.count("if (ma) { huNguoi = ma;") >= 2)
	dung("gán vào hsTaoNguoiUng", "hsTaoNguoiUng = ma;" in js)


@ca("tìm NCC: màn người được hoàn ứng phải nạp lại danh sách sau khi tạo")
def _():
	# `hsTaoDsUng` duoc cache mot lan. Khong xoa cache thi nguoi vua tao
	# khong co trong danh sach va chip moi khong bao gio hien ra - nguoi
	# dung tuong may khong luu duoc.
	js = _js("19-ho-so-tt.js")
	than = js.split("hsNoiNutTaoNcc(hsUngTim")[1][:400]
	dung("xoá cache trước khi vẽ lại", "hsTaoDsUng = null;" in than)


@ca("tìm NCC: màn người được hoàn ứng có ô gõ tìm, không chỉ tám chip")
def _():
	# Ban cu chi bay tam chip dau. Ai khong nam trong tam nguoi do la
	# khong co duong nao chon.
	js = _js("19-ho-so-tt.js")
	dung("có biến từ khoá riêng", "hsUngTim" in js)
	dung("có lọc theo từ khoá", "dsu = dsu.filter(" in js)
	dung("ô tìm có nối sự kiện", "getElementById('hsUngTim')" in js)


# ------------------------------------------------------- quyen tao ho so


@ca("tìm NCC: kế toán phải tự tạo được nhà cung cấp")
def _():
	# Bay nut ra ma bam vao bi tu choi quyen thi con te hon la khong co
	# nut. Chi Dung mang vai Accounts Manager va Accounts User.
	from vagabond import nha_cung_cap as ncc

	dung("Accounts Manager tạo được", "Accounts Manager" in ncc.VAI_SUA)
	dung("Accounts User tạo được", "Accounts User" in ncc.VAI_SUA)
	dung("thu mua tạo được", "Purchase Manager" in ncc.VAI_SUA)
