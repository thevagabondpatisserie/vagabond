"""Kiem thu luat duyet tung dong tren Phieu yeu cau mua hang (v293).

Vi sao den bay gio moi co
-------------------------
Man Duyet yeu cau mua chay tu 15/08/2026, doi luat ba lan (su co 17/08 ve
`sl_duyet` kieu Float khong giu duoc gia tri trong, nut "Duyet tat ca cac
mon con lai", roi luat noi long 24/08), ma khong co lay MOT ca kiem nao.
Moi lan sua la mot lan doan mo: sua xong chi biet dung hay sai khi Uyen mo
man ra bam.

Ngay 24/08/2026 anh Viet yeu cau bo tran "khong duyet qua so nhan vien
xin". Go mot rang buoc di thi ba rang buoc con lai cang can duoc chot lai
bang ca kiem, nen dung luon dip nay.

Cac ca duoi day chi goi `soat_so_duyet`, la phep THUAN: khong doc co so du
lieu, khong can site, chay duoc tren may CI tay khong.
"""

from vagabond.duyet_ycmh import (
	CAT_BOT, DUYET_DU, DUYET_THEM, TU_CHOI, soat_so_duyet,
)
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _soat(sl, xin, da_dat=0, ly_do="", ten="Bơ lạt"):
	return soat_so_duyet(sl, xin, da_dat, ly_do, ten)


@ca("duyệt đúng số nhân viên xin thì là duyệt đủ")
def _():
	loi, loai = _soat(5, 5)
	la("không vướng gì, xếp là duyệt đủ", [loi, loai], [[], DUYET_DU])


@ca("duyệt ít hơn số xin là cắt bớt, không cần lý do")
def _():
	loi, loai = _soat(3, 5)
	la("cắt bớt vẫn lưu được", [loi, loai], [[], CAT_BOT])


@ca("duyệt 0 mà không ghi lý do thì bị chặn")
def _():
	loi, loai = _soat(0, 5)
	dung("có báo lỗi", len(loi) == 1)
	dung("nói đúng chuyện phải ghi lý do", "ghi lý do" in loi[0])
	la("vẫn xếp là từ chối", loai, TU_CHOI)


@ca("duyệt 0 có ghi lý do thì qua")
def _():
	loi, loai = _soat(0, 5, ly_do="Kho tổng còn 20 kg")
	la("từ chối kèm lý do thì lưu được", [loi, loai], [[], TU_CHOI])


@ca("số duyệt âm bị chặn")
def _():
	loi, _loai = _soat(-1, 5, ly_do="gõ nhầm")
	dung("có chặn", any("không được âm" in x for x in loi))


@ca("không cắt xuống dưới số đã lên đơn mua")
def _():
	# Hang da tren duong ve roi, cat so tren giay khong lam hang quay dau.
	loi, _loai = _soat(2, 10, da_dat=6)
	dung("có chặn", len(loi) == 1)
	dung("nhắc tới đơn mua", "đơn mua" in loi[0])


@ca("cắt xuống đúng bằng số đã lên đơn thì được")
def _():
	loi, loai = _soat(6, 10, da_dat=6)
	la("không vướng", [loi, loai], [[], CAT_BOT])


@ca("duyệt cao hơn số nhân viên xin thì được, và xếp riêng là duyệt vượt")
def _():
	# Anh Viet 24/08/2026: quan ly xin 5, Uyen sua thanh 6 de mua chan thung.
	loi, loai = _soat(6, 5)
	la("cho vượt, không còn chặn", [loi, loai], [[], DUYET_THEM])


@ca("duyệt vượt vẫn phải theo luật đã lên đơn mua")
def _():
	# Vuot len tren thi khong bao gio dung phai tran nay, nhung de chac.
	loi, loai = _soat(9, 5, da_dat=7)
	la("vượt mà vẫn trên số đã đặt thì qua", [loi, loai], [[], DUYET_THEM])


@ca("sai số lẻ không bị hiểu nhầm thành duyệt vượt")
def _():
	# So co phan le (kg, lit) hay le ra phan nghin sau khi doi don vi. Neu
	# EPS khong duoc dung o day thi 5.00005 se hien nhan tim "Duyet vuot".
	loi, loai = _soat(5.00005, 5)
	la("vẫn là duyệt đủ", [loi, loai], [[], DUYET_DU])


@ca("vượt một phần lẻ thật thì vẫn tính là vượt")
def _():
	loi, loai = _soat(5.5, 5)
	la("nửa ký cũng là vượt", [loi, loai], [[], DUYET_THEM])


# --------- v327: don mua PHAI theo so thu mua duyet, bam tu dau cung vay

@ca("don mua: luat nam o hook chu khong nam trong tung cai nut")
def _luat_o_hook():
	import inspect

	from vagabond import duyet_ycmh as D

	dung("co ham dong bo don mua", hasattr(D, "dong_bo_don_mua_theo_duyet"))
	ma = inspect.getsource(D.dong_bo_don_mua_theo_duyet)
	dung("bo dong bi tu choi", "cho <= EPS" in ma)
	dung("ha so ve dung so duyet", "r.qty = cho" in ma)
	dung("khong tu nang so len", "r.qty = cho" in ma and "r.qty = flt(m" not in ma)
	dung("co ke ra cho nguoi bam nhin thay", "msgprint" in ma)
	dung("co ghi vao chinh to don", "doc.remarks" in ma)
	dung("don rong thi nem loi chu khong luu", "Đơn mua rỗng" in ma)
	dung("chua duyet thi de hang rao duoi bao", "_da_duyet(m)" in ma)


@ca("don mua: hook dat o before_validate cua Purchase Order")
def _hook_dat_dung_cho():
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	hooks = open(os.path.join(goc, "hooks.py"), encoding="utf-8").read()
	doan = hooks.split('"Purchase Order": {', 1)[1].split("}", 1)[0]
	dung("before_validate goi ham dong bo",
		"dong_bo_don_mua_theo_duyet" in doan and "before_validate" in doan)
	dung("validate van giu hang rao cu",
		"chan_don_mua_trai_duyet" in doan and '"validate"' in doan)
