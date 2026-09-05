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
	# v333 tach lam doi: o go tim len TREN bang chip vi no loc cai nam duoi,
	# duong tao moi o lai DUOI cung. Ban cu de ca hai o duoi, tuc la o loc
	# nam duoi cai no loc.
	dung("có hàm dựng ô tìm", "function hsOTimNcc(" in js)
	dung("có hàm dựng đường tạo mới", "function hsKhungTimNcc(" in js)
	dung("có hàm nối nút", "function hsNoiNutTaoNcc(" in js)
	dung("nút mang tên vừa gõ sang màn tạo", "nccTaoNhanh(" in js)
	# O tim dung chung cua ca app, khong tu che rieng mot ban o day.
	dung("ô tìm dùng đồ chung của app", "vgbOTim(" in js)


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


@ca("tìm NCC: màn nào CÒN chọn nhà cung cấp thì phải có nút tạo mới")
def _():
	js = _js("19-ho-so-tt.js")
	# Truoc 22/08/2026 co BA man chon nha cung cap. Nay con HAI.
	#
	# `scrHoanUngTao` (hoan ung khong hoa don) da bo han o chon nha cung
	# cap: anh Viet chot khoan hoan ung khong hoa don khong thuoc ve nha
	# cung cap nao ca, tien tra ve dung mot trong hai tai khoan ung, nen man
	# do gio chon TAI KHOAN. Day KHONG phai lo sot - dung khoi phuc lai o
	# chon nha cung cap o man ay.
	dung("hai chỗ dựng ô tìm", js.count("hsOTimNcc(") >= 3)
	dung("hai chỗ dựng đường tạo mới", js.count("hsKhungTimNcc(") >= 3)
	dung("hai chỗ nối nút", js.count("hsNoiNutTaoNcc(") >= 3)
	# Ve o tim ma quen noi loc thi o do go vao khong lam gi ca, con te hon
	# la khong co o.
	dung("hai chỗ nối lọc", js.count("vgbNoiOTim(") >= 2)
	for man in ("scrChiCongTyTao", "scrHoSoTTTao"):
		than = js.split("function " + man)[1].split("\nasync function ")[0]
		dung("%s có nối nút tạo" % man, "hsNoiNutTaoNcc(" in than)
	# Chot nguoc lai: man hoan ung khong hoa don KHONG duoc chon NCC nua.
	than_hu = js.split("function scrHoanUngTao")[1].split("\nasync function ")[0]
	dung("scrHoanUngTao KHÔNG còn chọn nhà cung cấp", "hsNoiNutTaoNcc(" not in than_hu)
	dung("scrHoanUngTao chọn tài khoản thay vào đó", "ds_tk_hoan_ung" in than_hu)


@ca("tìm NCC: tạo xong thì chọn luôn người vừa tạo, không bắt tìm lại")
def _():
	js = _js("19-ho-so-tt.js")
	# Man nao con chon nha cung cap thi tao xong phai gan luon ma vua tao.
	dung("gán vào huNguoi", js.count("if (ma) { huNguoi = ma;") >= 1)
	dung("gán vào hsTaoNguoiUng", "hsTaoNguoiUng = ma;" in js)


@ca("tìm NCC: màn người được hoàn ứng phải nạp lại danh sách sau khi tạo")
def _():
	# `hsTaoDsUng` duoc cache mot lan. Khong xoa cache thi nguoi vua tao
	# khong co trong danh sach va chip moi khong bao gio hien ra - nguoi
	# dung tuong may khong luu duoc.
	js = _js("19-ho-so-tt.js")
	# Cua so noi rong tu 600 len 1400 ky tu ngay 05/09/2026 (Issue #196):
	# giua hai moc da chen them doan noi lai o tim hoa don. Dieu can canh
	# khong doi, van la `hsTaoDsUng = null;` phai co truoc luc ve lai.
	than = js.split("vgbNoiOTim(b, 'hsUngTim'")[1][:1400]
	dung("xoá cache trước khi vẽ lại", "hsTaoDsUng = null;" in than)


@ca("tìm NCC: màn người được hoàn ứng bày ĐỦ người, không cắt còn tám")
def _():
	# Ban cu chi bay tam chip dau roi loc bang cach VE LAI MAN moi lan go.
	# Hai cai deu hong: ai khong nam trong tam nguoi thi go mai khong ra, va
	# ve lai man thi ban phim dien thoai tut xuong sau MOI chu.
	js = _js("19-ho-so-tt.js")
	than = js.split("function scrHoSoTTTao")[1].split("\nasync function ")[0]
	dung("có ô tìm", "hsOTimNcc('hsUngTim'" in than)
	dung("có nối lọc trên DOM", "vgbNoiOTim(b, 'hsUngTim'" in than)
	# Chot nguoc lai: khong duoc cat danh sach nua.
	dung("KHÔNG cắt còn tám người", ".slice(0, 8)" not in than)
	# Va khong duoc ve lai man moi lan go.
	dung("KHÔNG vẽ lại màn khi gõ", "hsUngTim = " not in than)


@ca("tìm NCC: nút tạo mới mang cái ĐANG gõ, không mang biến đã lưu")
def _():
	# Nguoi ta go ten xong bam thang nut Tao moi, chua he roi khoi o nen
	# bien da luu van con rong. Doc thang gia tri trong o moi dung.
	js = _js("19-ho-so-tt.js")
	dung("màn hoàn ứng đọc thẳng ô", "hsNoiNutTaoNcc(oUt ? oUt.value.trim()" in js)
	dung("màn chi công ty đọc thẳng ô", "hsNoiNutTaoNcc(ot ? ot.value.trim()" in js)


# ------------------------------------------------------- quyen tao ho so


@ca("tìm NCC: kế toán phải tự tạo được nhà cung cấp")
def _():
	# Bay nut ra ma bam vao bi tu choi quyen thi con te hon la khong co
	# nut. Chi Dung mang vai Accounts Manager va Accounts User.
	from vagabond import nha_cung_cap as ncc

	dung("Accounts Manager tạo được", "Accounts Manager" in ncc.VAI_SUA)
	dung("Accounts User tạo được", "Accounts User" in ncc.VAI_SUA)
	dung("thu mua tạo được", "Purchase Manager" in ncc.VAI_SUA)
