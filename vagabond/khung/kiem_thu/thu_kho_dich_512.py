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


# ---------------- bon y anh Viet duyet 19/09/2026 ----------------


@ca("v512 y1: bep khong bam duoc o kho thanh pham, chi quan ly san xuat con o chon")
def _y1_khoa_o():
	js = _doc("vagabond", "public", "js", "bep", "05-san-xuat.js")
	doan = js.split("function mfgWhCard")[1].split("\nfunction ")[0]
	dung("có nhánh quản lý mới có data-mw=fg", "mfgQuanLy()" in doan and doan.count('data-mw="fg"') == 1)
	dung("nhánh bếp là chữ đọc, ghi rõ máy tự chọn", "máy tự chọn theo chặng" in doan)


@ca("v512 y2: chuyen kho, nhap tay vao kho bep sai chang thi CHAN; kiem ke chi canh bao")
def _y2_chan():
	from types import SimpleNamespace as NS
	from unittest.mock import patch

	def _phieu(purpose, items, docstatus=0):
		d = NS(docstatus=docstatus, purpose=purpose, items=items)
		d.get = lambda k, _d=d: getattr(_d, k, None)
		return d

	def _dong(**kw):
		o = NS(**kw)
		o.get = lambda k, _o=o: getattr(_o, k, None)
		return o

	nem_ra = []
	f = NS(throw=lambda m, **k: (_ for _ in ()).throw(ValueError(m)), msgprint=lambda *a, **k: nem_ra.append(a[0]),
		log_error=lambda *a, **k: None, get_traceback=lambda: "")
	with patch.object(ks, "frappe", f), patch.object(ks, "_kho_dich_cua_ma",
			lambda ma, kho: "Pastry - Thành phẩm - TV" if ma.startswith("BAWC") and "Nguyên liệu" in kho else None):
		dong = [_dong(item_code="BAWC00046", t_warehouse="Pastry - Nguyên liệu - TV")]
		for muc in ("Material Transfer", "Material Receipt", "Material Transfer for Manufacture"):
			try:
				ks.chan_nhap_sai_kho(_phieu(muc, dong))
				dung("phải chặn " + muc, False)
			except ValueError as e:
				dung("nói rõ kho đúng", "Pastry - Thành phẩm - TV" in str(e))
		# dung kho thi qua
		ks.chan_nhap_sai_kho(_phieu("Material Transfer", [_dong(item_code="BAWC00046", t_warehouse="Pastry - Thành phẩm - TV")]))
		# BTP vao kho nguyen lieu la dung luat, qua
		ks.chan_nhap_sai_kho(_phieu("Material Transfer", [_dong(item_code="NBTP00029", t_warehouse="Pastry - Nguyên liệu - TV")]))
		# Manufacture khong thuoc ham nay (da co gan_kho_thanh_pham tu sua)
		ks.chan_nhap_sai_kho(_phieu("Manufacture", dong))
		# phieu da ghi so khong dung
		ks.chan_nhap_sai_kho(_phieu("Material Transfer", dong, docstatus=1))
		# kiem ke: chi canh bao
		kk = _phieu("", [_dong(item_code="BAWC00046", warehouse="Pastry - Nguyên liệu - TV", qty=3)])
		ks.canh_bao_kiem_ke_sai_kho(kk)
		la("kiểm kê cảnh báo một lần", len(nem_ra), 1)
		dung("cảnh báo chỉ tên kho đúng", "Pastry - Thành phẩm - TV" in nem_ra[0])
	h = _doc("vagabond", "hooks.py")
	dung("hook chặn đăng ký ở validate Stock Entry", '"vagabond.kho_san_xuat.chan_nhap_sai_kho"' in h)
	dung("hook kiểm kê đăng ký", '"vagabond.kho_san_xuat.canh_bao_kiem_ke_sai_kho"' in h)


@ca("v512 y3: kho dung cua dong sai kho, va cua tao phieu chuyen nhap dang ky cua ngo")
def _y3_phieu():
	la("TP ở kho NL Pastry thì về Pastry - Thành phẩm", tc.kho_dung_cua(ks.THANH_PHAM, "pastry"), "Pastry - Thành phẩm - TV")
	la("NL ở kho TP Baker thì về Baker - Nguyên liệu", tc.kho_dung_cua(ks.NGUYEN_LIEU, "baker"), "Baker - Nguyên liệu - TV")
	# Dot bien 19/09: ban dau thieu ca nay nen bo LUAT_KHO_DICH van xanh (dieu 17a).
	la("BTP ở kho TP thì về kho Nguyên liệu theo luật 28/08", tc.kho_dung_cua(ks.BTP_SAN_SANG, "pastry"), "Pastry - Nguyên liệu - TV")
	d = {"chang": ks.THANH_PHAM, "kho": [{"kho": "Pastry - Nguyên liệu - TV", "sl": 3, "sai": True}]}
	la("kho đúng của dòng", tc.kho_dung_cua_dong(d, {"Pastry - Nguyên liệu - TV": "pastry"}), "Pastry - Thành phẩm - TV")
	la("dòng không sai thì None", tc.kho_dung_cua_dong({"chang": ks.THANH_PHAM, "kho": [{"kho": "x", "sai": False}]}, {}), None)
	from vagabond.khung.kiem_thu import thu_cua_ngo
	dung("cửa ngõ đăng ký", "tao_phieu_ve_dung_kho" in (thu_cua_ngo.CUA_NGO.get("ton_chang.py") or []))
	s = _doc("vagabond", "ton_chang.py")
	doan = s.split("def tao_phieu_ve_dung_kho")[1].split("\n@frappe")[0]
	dung("chỉ lập NHÁP, không submit", "se.insert()" in doan and ".submit()" not in doan)
	dung("gác quyền QUYEN_GHI", "QUYEN_GHI" in doan)
	dung("chặn chuyển quá tồn", "không chuyển được" in doan)
	js = _doc("vagabond", "public", "js", "bep", "37-ton-chang.js")
	dung("nút chỉ hiện khi sai kho và có quyền", "x.sai_kho && d.lap_duoc && x.kho_dung" in js)
	dung("hỏi xác nhận rồi mới gọi", "confirmSheet('Chuyển về đúng kho'" in js and "vagabond.ton_chang.tao_phieu_ve_dung_kho" in js)


@ca("v512 y4: Viec can lam co loai sai_kho, dung vai, mo ra man Ton kho theo chang")
def _y4_viec():
	from vagabond import viec_can_lam as v
	dung("có loại sai_kho", any(k == "sai_kho" for k, _, _ in v.LOAI_PHIEU))
	dung("bếp (Stock User) thấy", v.thay_duoc("sai_kho", {"Stock User"}))
	dung("quản lý sản xuất thấy", v.thay_duoc("sai_kho", {"Manufacturing Manager"}))
	dung("kế toán không thấy", not v.thay_duoc("sai_kho", {"Accounts User"}))
	s = _doc("vagabond", "viec_can_lam.py")
	dung("nguồn gom có sai_kho", '("sai_kho", lambda: _viec_sai_kho(vai, bp)),' in s)
	dung("đọc từ cùng một nguồn ton_theo_chang, chip SAI_KHO", "chang=ton_chang.SAI_KHO" in s)
	js = _doc("vagabond", "public", "js", "bep", "02-trang-chu.js")
	dung("app mở màn Tồn kho theo chặng lọc Sai kho", "if (l === 'sai_kho') return go(function () { tch.chang = 'sai_kho';" in js)
	dung("có icon", "sai_kho: '⚠️'" in js)
