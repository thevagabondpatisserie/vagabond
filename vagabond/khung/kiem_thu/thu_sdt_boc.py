# -*- coding: utf-8 -*-
"""Kiem thu boc so dien thoai ra khoi o go tu do (v304).

Du lieu kiem KHONG bia ra: 18 o duoi day chep NGUYEN VAN tu bang tinh
"Danh sach tang banh khach VIP" cua chi Loan Anh, doc ngay 25/08/2026.

Vi sao chep nguyen van chu khong nghi ra ca kiem cho dep
--------------------------------------------------------
Ca kiem tu nghi ra thi bao gio cung xanh, vi nguoi viet ca kiem va nguoi
viet ham la mot. Chi co du lieu THAT moi cai duoc. Ba lop loi o day deu
tim ra bang cach chay ham cu tren 18 o nay chu khong bang cach doc lai code.

Ba lop phai giu bang moi gia:
  1. So co dinh doc ra duoc, khong bi bo qua.
  2. O co nhieu so thi KHONG tu chon, phai bao nguoi.
  3. So cua tro ly, quan gia, bao ve phai bi danh dau chinh_chu = 0.

Lop 3 la lop dat nhat. Mat no la mot khach VIP nhan tin nhan chuc mung
mang ten nguoi khac.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.sdt_boc import boc

# (o nguyen van, sdt mong doi, loai mong doi, chinh_chu mong doi)
#
# Chep tu bang tinh, khong sua mot ky tu nao ke ca dau cach thua.
O_THAT = (
	("0908255045", "0908255045", "di_dong", 1),
	("0913919169", "0913919169", "di_dong", 1),
	("0972741266 - Na (Trợ Lý)", "0972741266", "di_dong", 0),
	("093 2554338 (chị Linh quản gia)", "0932554338", "di_dong", 0),
	("0908875668 - Mr. Hai Anh (Trợ Lý)", "0908875668", "di_dong", 0),
	("078 9513499 - Cô Nương (Quản Gia)", "0789513499", "di_dong", 0),
	("0838621093 (Trợ lý - Thuỳ Vân)", "0838621093", "di_dong", 0),
	("0918868778 - Nhân viên", "0918868778", "di_dong", 0),
	("Hoàng Phương Nam +84 90 8415976", "0908415976", "di_dong", 1),
	("0 96 3149900", "0963149900", "di_dong", 1),
	("0913 112345 - anh Bình", "0913112345", "di_dong", 1),
	("096 9098264 gặp Trang Đào", "0969098264", "di_dong", 1),
	("0904195027 chị Thi", "0904195027", "di_dong", 1),
	("0917055639 - Thùy Duyên.", "0917055639", "di_dong", 1),
	("0379696248 (Ngọc Uyên)", "0379696248", "di_dong", 1),
	("028 39322722 gặp chị Thư", "02839322722", "co_dinh", 1),
	("02839322722 (Số bàn người giúp việc)", "02839322722", "co_dinh", 0),
	("bấm chuông", "", "", 1),
)


@ca("sdt boc: 18 o nguyen van tu bang tinh Loan Anh")
def _o_that():
	for tho, mong_sdt, mong_loai, mong_cc in O_THAT:
		r = boc(tho)
		la("sdt của %r" % tho[:34], r["sdt"], mong_sdt)
		la("loại của %r" % tho[:34], r["loai"], mong_loai)
		la("chính chủ của %r" % tho[:34], r["chinh_chu"], mong_cc)


@ca("sdt boc: hai lop ma ham cu bo sot deu phai doc duoc")
def _lop_ham_cu_sot():
	# Lop 1: so co dinh. lib.sdt() tra rong vi bang dau so chi co di dong.
	r = boc("028 39322722 gặp chị Thư")
	la("số bàn đọc ra", r["sdt"], "02839322722")
	la("nhận đúng là số cố định", r["loai"], "co_dinh")
	dung("có nhắc là không gửi được tin Zalo", "Zalo" in r["canh_bao"])

	# Lop 2: so nam trong mot cau co san chu so khac. lib.sdt() ep ca o
	# thanh mot day chu so nen tong vuot chin va tra rong.
	r = boc("25 hộp cho Sen Vàng gửi cùng 1 địa chỉ - Thông tin liên hệ: "
			"0903015001 - Thi")
	la("số nằm trong câu vẫn đọc ra", r["sdt"], "0903015001")
	la("đọc luôn tên người nghe máy", r["nguoi_nghe"], "Thi")


@ca("sdt boc: o CO NHIEU SO thi khong duoc tu chon")
def _nhieu_so():
	# Day la ca dat nhat. May khong co cach nao biet so nao la cua khach.
	r = boc("0913112345 hoặc 0908280338")
	la("vẫn gợi ý số đầu", r["sdt"], "0913112345")
	la("nhưng khoá lại, không coi là chính chủ", r["chinh_chu"], 0)
	dung("cảnh báo nói rõ có mấy số", "2 số" in r["canh_bao"])
	dung("cảnh báo nói việc phải làm", "chọn giúp" in r["canh_bao"])


@ca("sdt boc: so cua nguoi nhan thay phai bi danh dau")
def _khong_chinh_chu():
	# Nhom nay la nhom sinh ra ca tep sdt_boc.py. So doc ra HOAN TOAN DUNG,
	# nhung dung cua nguoi khac. Khong co co nay thi ZNS bay nham may.
	for tho, ai in (
		("0972741266 - Na (Trợ Lý)", "trợ lý"),
		("093 2554338 (chị Linh quản gia)", "quản gia"),
		("0918868778 - Nhân viên", "nhân viên"),
		("0901234567 - anh Tuấn bảo vệ", "bảo vệ"),
		("0901234567 (thư ký chị Hà)", "thư ký"),
	):
		r = boc(tho)
		la("%s: chính chủ" % ai, r["chinh_chu"], 0)
		dung("%s: có câu cảnh báo" % ai, bool(r["canh_bao"]))
		dung("%s: cảnh báo nói tin nhắn đã khoá" % ai,
			"khoá" in r["canh_bao"] or "gọi tay" in r["canh_bao"])

	# O that co chu "bao ve" dung o DAU o, cach con so hon ba muoi ky tu, con
	# phan chu ngay canh so lai la "( da tang)". Soi moi phan canh so thi o
	# nay lot luoi, va so cua chi Huong se nhan tin nhan mang ten anh Binh.
	r = boc("Gửi bảo vệ cho anh Bình hoặc alo chị Hương 0908280338( đã tặng)")
	la("chữ bảo vệ nằm xa số vẫn bắt được", r["chinh_chu"], 0)
	la("số vẫn đọc ra để còn gọi tay", r["sdt"], "0908280338")


@ca("sdt boc: khong doc ra thi bao ro viec phai lam, khong doan bua")
def _khong_doan():
	for tho in ("bấm chuông", "Thiên Ân", "Gọi", "", "   ", "Pick d1"):
		r = boc(tho)
		la("%r trả rỗng" % tho, r["sdt"], "")
	# O rong that su thi khong can canh bao, con o co chu ma khong co so
	# thi phai bao.
	dung("ô có chữ mà không có số thì có cảnh báo",
		bool(boc("bấm chuông")["canh_bao"]))
	dung("ô rỗng thì không cần cảnh báo", not boc("")["canh_bao"])


@ca("sdt boc: doc ra ten nguoi nghe may o ca ba the")
def _ten_nguoi_nghe():
	la("dấu gạch sau số", boc("0972741266 - Na (Trợ Lý)")["nguoi_nghe"],
		"Na (Trợ Lý)")
	la("ngoặc đơn sau số", boc("093 2554338 (chị Linh quản gia)")["nguoi_nghe"],
		"chị Linh quản gia")
	la("tên đứng TRƯỚC số", boc("Hoàng Phương Nam +84 90 8415976")["nguoi_nghe"],
		"Hoàng Phương Nam")
	la("có từ dẫn gặp", boc("096 9098264 gặp Trang Đào")["nguoi_nghe"],
		"Trang Đào")


@ca("sdt boc: boc lai duoc khong gioi han lan, ket qua khong doi")
def _lap_lai_duoc():
	# Phai lap lai duoc thi vá luat xong moi quet lai ca so duoc.
	for tho, _a, _b, _c in O_THAT:
		mot = boc(tho)
		hai = boc(boc(tho)["tho"])
		la("bóc lại %r ra cùng kết quả" % tho[:30], hai, mot)


@ca("sdt boc: TUYET DOI khong sua o goc")
def _giu_o_goc():
	# Sau thang nua con tra lai duoc may da hieu sai cho nao.
	for tho, _a, _b, _c in O_THAT:
		la("giữ nguyên %r" % tho[:30], boc(tho)["tho"], tho)


@ca("sdt boc: khong nhan bua ma vung khong co that")
def _ma_vung_bia():
	# Cung ly do da ghi trong lib.py: trong tep Fabi tung co ma so thue bi
	# go nham vao o so dien thoai.
	la("0300136435 là mã số thuế, không phải số", boc("0300136435")["sdt"], "")
	la("0100109106 không phải số", boc("0100109106")["sdt"], "")
