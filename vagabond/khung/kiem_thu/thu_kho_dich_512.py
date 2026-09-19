# -*- coding: utf-8 -*-
"""v512: kho DICH cua lenh san xuat la luat theo chang, khong phai lua chon.

Khai 18/09/2026 chup man Ton kho theo chang: banh thanh pham nam o kho
Pastry - Nguyen lieu ("sai kho"). Truy vet tren site: LSX-180926-000201 co
fg_warehouse = Pastry - Nguyen lieu vi o "Nhap thanh pham vao kho" tren app
cho chon moi kho bep va nho lua chon do. Ba lop sua:
  1. kho_san_xuat.kho_dich_bat_buoc: kho bep sai chang thi tra ve kho dung.
  2. Hook Work Order va Stock Entry (Manufacture) goi ham do, sua va bao.
  3. Man Ton kho theo chang danh dau "sai kho"; app chi cho chon kho Thanh pham.
"""

import io
import os
import re

from vagabond import kho_san_xuat as ks
from vagabond import ton_chang as tc
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("v512: thanh pham chon kho Nguyen lieu cua bep thi tra ve kho Thanh pham")
def _tp_vao_nl():
	la("sửa về kho thành phẩm", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Pastry - Nguyên liệu - TV"),
		"Pastry - Thành phẩm - TV")
	la("chọn nhầm kho bếp khác", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Baker - Thành phẩm - TV"),
		"Pastry - Thành phẩm - TV")
	la("BTP vào kho Thành phẩm cũng sai", ks.kho_dich_bat_buoc(ks.BTP_SAN_SANG, "baker", "Baker - Thành phẩm - TV"),
		"Baker - Nguyên liệu - TV")


@ca("v512: kho dung, kho ngoai bep, thieu du kien thi KHONG dung")
def _khong_dung():
	la("đã đúng", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Pastry - Thành phẩm - TV"), None)
	la("BTP về kho Nguyên liệu là đúng luật 28/08", ks.kho_dich_bat_buoc(ks.BTP_SO_CAP, "pastry", "Pastry - Nguyên liệu - TV"), None)
	la("kho tổng 307 không đụng", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Kho tổng 307 - TV"), None)
	la("kho điểm bán không đụng", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", "Kho Sales Online - TV"), None)
	la("trống thì để hook điền", ks.kho_dich_bat_buoc(ks.THANH_PHAM, "pastry", ""), None)
	la("không rõ chặng", ks.kho_dich_bat_buoc(None, "pastry", "Pastry - Nguyên liệu - TV"), None)
	la("không rõ bếp", ks.kho_dich_bat_buoc(ks.THANH_PHAM, None, "Pastry - Nguyên liệu - TV"), None)


@ca("v512: hook lenh va hook phieu deu di qua kho_dich_bat_buoc")
def _hook():
	s = _doc("vagabond", "kho_san_xuat.py")
	doan = s.split("def gan_kho_lenh")[1].split("\ndef ")[0]
	dung("lệnh: sửa fg_warehouse", "doc.fg_warehouse = dung" in doan and "kho_dich_bat_buoc(chang, bep, doc.get(\"fg_warehouse\"))" in doan)
	doan2 = s.split("def gan_kho_thanh_pham")[1].split("\ndef ")[0]
	dung("phiếu: chỉ Manufacture", '"Manufacture"' in doan2)
	dung("phiếu: sửa t_warehouse dòng thành phẩm", "d.t_warehouse = dung" in doan2 and "is_finished_item" in doan2)
	h = _doc("vagabond", "hooks.py")
	dung("hook Stock Entry đăng ký", '"vagabond.kho_san_xuat.gan_kho_thanh_pham"' in h)
	dung("hook Work Order còn nguyên", '"before_validate": "vagabond.kho_san_xuat.gan_kho_lenh"' in h)


@ca("v512: man Ton kho theo chang danh dau sai kho theo dung luat kho dich")
def _sai_kho():
	dung("TP ở kho NL là sai", tc.kho_sai_chang(ks.THANH_PHAM, ks.NGUYEN_LIEU))
	dung("BTP ở kho NL là đúng", not tc.kho_sai_chang(ks.BTP_SAN_SANG, ks.NGUYEN_LIEU))
	dung("NL ở kho TP là sai", tc.kho_sai_chang(ks.NGUYEN_LIEU, ks.THANH_PHAM))
	dung("chưa phân chặng không kết luận", not tc.kho_sai_chang("", ks.NGUYEN_LIEU))
	ds = [
		{"ma": "BAWC1", "chang": ks.THANH_PHAM, "sl": 10, "kho": [{"kho": "Pastry - Nguyên liệu - TV", "sl": 10}]},
		{"ma": "BTP1", "chang": ks.BTP_SO_CAP, "sl": 3, "kho": [{"kho": "Pastry - Nguyên liệu - TV", "sl": 3}]},
		{"ma": "BAWC2", "chang": ks.THANH_PHAM, "sl": 5, "kho": [{"kho": "Pastry - Thành phẩm - TV", "sl": 5}]},
	]
	so = tc.danh_dau_sai_kho(ds, {"Pastry - Nguyên liệu - TV": ks.NGUYEN_LIEU, "Pastry - Thành phẩm - TV": ks.THANH_PHAM})
	la("đếm đúng 1 mã sai", so, 1)
	la("dòng sai gắn cờ", [d["sai_kho"] for d in ds], [True, False, False])
	dung("kho sai gắn cờ", ds[0]["kho"][0]["sai"] and not ds[1]["kho"][0]["sai"])
	js = _doc("vagabond", "public", "js", "bep", "37-ton-chang.js")
	dung("chip sai kho", "data-tcc=\"sai_kho\"" in js and "(sai kho)" in js)


@ca("v512: app chi cho chon kho Thanh pham o o nhap thanh pham, bo kho da nho sai")
def _app_picker():
	js = _doc("vagabond", "public", "js", "bep", "05-san-xuat.js")
	dung("hàm lọc kho thành phẩm", "function mfgFgOpts()" in js)
	dung("ô fg dùng danh sách lọc", "k === 'src' ? mfgWhOpts() : mfgFgOpts()" in js)
	dung("kho nhớ sai thì bỏ", "if (mfg.fg && !mfgLaKhoThanhPham(mfg.fg) && whFind('thành phẩm')) mfg.fg = '';" in js)
