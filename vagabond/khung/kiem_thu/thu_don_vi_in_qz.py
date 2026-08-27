# -*- coding: utf-8 -*-
"""Don vi cua kho giay va mat do diem khi day ban in xuong QZ Tray.

LOI THAT, anh Viet bao 26/08/2026 kem hai tam anh: in hoa don ra mot mau
giay mini, in tem ra ca dai tem trang.

Nguyen nhan: ban cu khai `units: 'mm'` kem `density: 203`. Trong QZ, mat do
diem tinh THEO CHINH DON VI dang khai - xem chu thich trong thu vien da nap
san, vagabond/public/js/vendor/qz-tray.js:

    @param {number} [options.density=0] Pixel density (DPI, DPMM, or DPCM
           depending on [options.units]).
    @param {string} [options.units='in'] Page units, applies to paper size,
           margins, and density.

Nen hai o do ghep lai co nghia la 203 diem MOI MI LI MET, gap 25,4 lan y
dinh. To bill 80mm bi nen con hon 3mm, con tem 40 x 30mm bi nen con
1,6 x 1,2mm - nhin bang mat thuong la tem trang.

Ca kiem duoi day chot lai hai dieu, de khong ai lo tay khai lai bang mi li
met lan nua:

  1. Trong ca tep khong con mot cho nao khai `units` bang mi li met.
  2. Kho giay duoc doi tu mi li met sang inch ngay tai cho dung cau hinh,
     nen ben app van khai bang mi li met nhu cu.
"""

import io
import os

from vagabond import may_in
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _js(ten):
	goi = os.path.dirname(os.path.abspath(may_in.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


@ca("in ngầm: không còn chỗ nào khai đơn vị trang bằng mi li mét")
def _():
	src = _js("27-in-ngam.js")
	# Chi soi phan MA, bo phan chu thich ra: chu thich co ke lai loi cu nen
	# no chua chuoi do mot cach co y.
	ma = "\n".join(
		d for d in src.split("\n")
		if not d.lstrip().startswith(("*", "/*", "//"))
	)
	la("không còn units: 'mm' trong mã", ma.count("units: 'mm'"), 0)
	la('không còn units: "mm" trong mã', ma.count('units: "mm"'), 0)
	dung("có khai bằng inch", "units: 'in'," in src)


@ca("in ngầm: cấu hình in dựng ở MỘT chỗ, hai đường in dùng chung")
def _():
	src = _js("27-in-ngam.js")
	dung("có hàm dựng cấu hình", "function inCauHinh(may, rongMm, caoMm, dpi)" in src)
	dung("có hàm đổi mi li mét sang inch", "function inMmSangInch(mm)" in src)
	dung("chia đúng 25.4", "return (Number(mm) || 0) / 25.4;" in src)
	dung("mật độ điểm đi thẳng vào ô density", "density: d," in src)
	dung("khổ giấy được đổi sang inch", "width: inMmSangInch(rongMm)," in src)
	# Hai duong in - to app tu dung, va ban in do may chu dung - deu phai
	# goi chung ham nay. Con mot cho tu dung cau hinh la cho do se lech lai.
	la("số lần gọi hàm dựng cấu hình", src.count("= inCauHinh(may,"), 2)
	la("không còn ai tự gọi qz.configs.create", src.count("qz.configs.create("), 1)


@ca("in ngầm: giấy cuộn để trống chiều cao, tem thì khai chiều cao")
def _():
	src = _js("27-in-ngam.js")
	dung("chiều cao 0 nghĩa là để trống",
		"height: (Number(caoMm) > 0) ? inMmSangInch(caoMm) : null" in src)
	dung("bản in của máy chủ không khai chiều cao", "inCauHinh(may, rongMm, 0, dpi)" in src)


@ca("in ngầm: mỗi con tem một trang, không in cả xấp thành một dải")
def _():
	src = _js("27-in-ngam.js")
	dung("có hàm cắt trang", "function inCatTrang(canvas, tailieu, catTheo, ti_le)" in src)
	# Do bang hop bo cuc chu khong bang getBoundingClientRect: hai cai khac
	# nhau khi the bi xoay.
	dung("đo bằng offsetTop", "offsetTop * ti_le" in src)
	dung("đo bằng offsetHeight", "offsetHeight * ti_le" in src)
	dung("chỉ cắt cho tem", "(vaiTro === 'tem' && caoMm > 0 && !xoay)" in src)
	dung("khổ xoay 90 độ thì không cắt", "var xoay = !!(k && Number(k.xoay) === 90);" in src)
	dung("giấy cuộn thì không cắt", "!k.cuon && Number(k.cao) > 0" in src)
	dung("đẩy cả xấp xuống một lần", "await qz.print(cfg, xap);" in src)
	# Mot the thi khong phai cat, tra ve nguyen anh - tranh de cong them
	# mot buoc ve canvas vo ich cho ban in mot tem.
	dung("dưới hai thẻ thì thôi không cắt", "if (!the || the.length < 2)" in src)
