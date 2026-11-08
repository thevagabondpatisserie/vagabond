# -*- coding: utf-8 -*-
"""v645 bản 2 (anh Việt 08/11/2026): công tắc ưu đãi đơn đầu tiên trên web
trong màn Khuyến mãi của app, chọn chỗ hiển thị (bước thanh toán, trang Ưu
đãi), chọn có bắt xác thực số bằng mã Zalo hay không, sửa mức giảm và tiền bánh
tối thiểu.

Các ca chạy hàm THẬT: phép thuần của don_dau_web; xem_uu_dai và tao_don nạp từ
don_hang.py trong đúng môi trường các ca #367 và v645 dùng, phần xét trạng thái
chạy bằng trang_thai THẬT với cài đặt, chỉ thay phần đọc site.
"""

import json
import sys
from unittest.mock import patch

from vagabond import don_dau_web as dd
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_don_dau_web_645 import SO, _tao, _xem
from vagabond.khung.kiem_thu.thu_don_web_367 import _dau_gia

_fr = sys.modules["frappe"]


def _dau_that(cai_dat, da_dat=False, phien="", otp=True):
	"""don_dau_web giả mà phần xét trạng thái dùng trang_thai THẬT với cài đặt."""
	dau = _dau_gia(cai_dat=cai_dat, da_dat=da_dat)

	def xet(sdt, tien, ch=None):
		dau.vet.xet.append((sdt, tien))
		return dd.trang_thai(sdt, da_dat, phien, tien, otp, ch)
	dau.xet = xet
	return dau


# ------------------------------------------------------------------ phép thuần

@ca("v645 bản 2 chuan: thiếu ô lấy mặc định bản duyệt mẫu; số gõ kiểu 50.000 đọc được; chuỗi JSON đọc được; bắt mã Zalo thì thẻ thanh toán luôn hiện")
def _():
	la("mặc định", dd.chuan(None), {"bat": 1, "giam": 50000, "toi_thieu": 300000, "can_otp": 1, "hien_thanh_toan": 1, "hien_uu_dai": 1})
	la("số có dấu chấm và chữ đ", (dd.chuan({"giam": "40.000 đ", "toi_thieu": "250,000"})["giam"], dd.chuan({"giam": "40.000 đ", "toi_thieu": "250,000"})["toi_thieu"]), (40000, 250000))
	la("chuỗi JSON", dd.chuan('{"bat": 0, "hien_uu_dai": "0"}')[("bat")], 0)
	la("công tắc chữ", [dd.chuan({"bat": x})["bat"] for x in ("1", "true", "co", "0", "", None, "abc", True, False)], [1, 1, 1, 0, 0, 0, 0, 1, 0])
	la("bắt mã Zalo mà tắt thẻ thanh toán: thẻ vẫn bật", dd.chuan({"can_otp": 1, "hien_thanh_toan": 0})["hien_thanh_toan"], 1)
	la("không bắt mã thì tắt được thẻ", dd.chuan({"can_otp": 0, "hien_thanh_toan": 0})["hien_thanh_toan"], 0)


@ca("v645 bản 2 chuan: lúc LƯU số sai báo câu đọc được; lúc ĐỌC ô hỏng thì về mặc định, không làm gãy trang")
def _():
	for x, cau in (({"giam": 500}, "Mức giảm"), ({"giam": 2000000}, "Mức giảm"), ({"giam": "abc"}, "Mức giảm"),
			({"toi_thieu": -1}, "Tiền bánh tối thiểu"), ({"toi_thieu": 30000000}, "Tiền bánh tối thiểu"),
			({"giam": 100000, "toi_thieu": 100000}, "lớn hơn mức giảm"), ({"giam": 100000, "toi_thieu": 0}, "lớn hơn mức giảm")):
		try:
			dd.chuan(x, nghiem=True)
			dung("phải báo lỗi: %r" % x, False)
		except ValueError as e:
			dung("câu cho %r: %s" % (x, e), cau in str(e))
	nem("JSON hỏng lúc lưu", lambda: dd.chuan("{x", nghiem=True), ValueError)
	la("JSON hỏng lúc đọc", dd.chuan("{x"), dd.chuan(None))
	la("số sai lúc đọc về cặp mặc định", (dd.chuan({"giam": 100000, "toi_thieu": 50000})["giam"], dd.chuan({"giam": 100000, "toi_thieu": 50000})["toi_thieu"]), (50000, 300000))
	la("dữ liệu không phải dict", dd.chuan([1, 2]), dd.chuan(None))


@ca("v645 bản 2 trang_thai: tắt thì Không; không bắt mã Zalo thì không cần phiên Thành viên và không cần cấu hình gửi mã; ngưỡng theo cài đặt")
def _():
	khong_otp = {"can_otp": 0, "toi_thieu": 200000, "giam": 30000}
	la("tắt", dd.trang_thai(SO, False, SO, 500000, True, {"bat": 0}), dd.KHONG)
	la("không bắt mã, chưa đăng nhập, chưa mở Zalo: vẫn đủ", dd.trang_thai(SO, False, "", 200000, False, khong_otp), dd.DU)
	la("không bắt mã, dưới ngưỡng mới", dd.trang_thai(SO, False, "", 199999, False, khong_otp), dd.CHUA_DU_TIEN)
	la("không bắt mã, số đã có đơn web", dd.trang_thai(SO, True, "", 500000, False, khong_otp), dd.KHONG)
	la("bắt mã như bản duyệt mẫu", (dd.trang_thai(SO, False, "", 500000, True, None), dd.trang_thai(SO, False, SO, 500000, True, None),
		dd.trang_thai(SO, False, SO, 500000, False, None)), (dd.CAN_XAC_THUC, dd.DU, dd.CHUA_MO))


@ca("v645 bản 2 tron và phan_hoi: mức giảm theo cài đặt; mã lớn hơn vẫn giữ mã; trang nhận cờ bắt mã và cờ hiện thẻ")
def _():
	ma = lambda g: {"tong_giam": g, "ap": [{"ma": "SN", "ten": "Mã", "giam": g}], "ma": "SN", "ly_do": ""}
	uu, bo = dd.tron(ma(20000), dd.DU, True, 30000)
	la("30.000 thắng mã 20.000", (uu["tong_giam"], uu["ap"][0]["giam"], bo), (30000, 30000, True))
	uu, bo = dd.tron(ma(40000), dd.DU, True, 30000)
	la("mã 40.000 giữ", (uu["tong_giam"], bo), (40000, False))
	la("giảm 0 thì không đụng", dd.tron(ma(0), dd.DU, False, 0)[0]["tong_giam"], 0)
	la("phan_hoi", dd.phan_hoi(dd.DU, {"giam": 30000, "toi_thieu": 200000, "can_otp": 0, "hien_thanh_toan": 0}),
		{"trang_thai": dd.DU, "giam": 30000, "toi_thieu": 200000, "can_otp": 0, "hien": 0})


@ca("v645 bản 2 thẻ trang Ưu đãi: chỉ có khi đang bật và chọn hiện ở trang Ưu đãi; dòng đầu là mức giảm; nhắc mã Zalo chỉ khi bắt mã; trình biên tập thấy trạng thái")
def _():
	la("tắt", dd.the_uu_dai({"bat": 0}), None)
	la("không chọn trang Ưu đãi", dd.the_uu_dai({"hien_uu_dai": 0}), None)
	t = dd.the_uu_dai({"giam": 30000, "toi_thieu": 200000, "can_otp": 0})
	dk = t["dieu_kien"].split("\n")
	la("mã thẻ, nhóm, đơn tối thiểu", (t["id"], t["loai"], t["nhom"], t["don_toi_thieu"], t["dung_web"], t["ma_uu_dai"]), ("don-dau-web", "uu_dai", "Ưu đãi", 200000, 1, ""))
	la("dòng đầu là mức giảm", dk[0], "Giảm 30.000đ")
	dung("không bắt mã thì không nhắc mã Zalo", not any("Zalo" in x for x in dk))
	dung("bắt mã thì nhắc", any("mã Zalo" in x for x in dd.the_uu_dai(None)["dieu_kien"].split("\n")))
	la("biên tập: đang thấy", (dd.dong_bien_tap(None)["khach_thay"], dd.dong_bien_tap(None)["trang_thai_erp"]), (1, "Khách đang thấy"))
	la("biên tập: tắt vẫn liệt kê để biết sửa ở đâu", (dd.dong_bien_tap({"bat": 0})["khach_thay"], dd.dong_bien_tap({"bat": 0})["tieu_de"]), (0, dd.TEN))
	la("biên tập: không ở trang Ưu đãi nhưng còn ở bước thanh toán", dd.dong_bien_tap({"hien_uu_dai": 0})["trang_thai_erp"],
		"Không hiện trên trang Ưu đãi (vẫn hiện ở bước thanh toán)")


# ------------------------------------------------------------------ chạm site (giả)

@ca("v645 bản 2 xet: không bắt mã Zalo thì KHÔNG đọc phiên Thành viên và cấu hình gửi mã; tắt thì không đọc gì")
def _():
	vet = []
	cu = (dd.da_dat_web, dd.sdt_phien, dd.otp_mo)
	dd.da_dat_web = lambda s: (vet.append("da_dat"), False)[1]
	dd.sdt_phien = lambda: (vet.append("phien"), "")[1]
	dd.otp_mo = lambda: (vet.append("otp"), False)[1]
	try:
		a = dd.xet(SO, 500000, {"can_otp": 0})
		v1 = list(vet)
		del vet[:]
		b = dd.xet(SO, 500000, {"bat": 0})
		v2 = list(vet)
	finally:
		dd.da_dat_web, dd.sdt_phien, dd.otp_mo = cu
	la("không bắt mã: đủ, chỉ đọc đã có đơn web chưa", (a, v1), (dd.DU, ["da_dat"]))
	la("tắt: không đọc gì", (b, v2), (dd.KHONG, []))


def _sql_o(gia_tri):
	"""frappe.db.sql giả trả đúng dòng Singles của ô cài đặt (None: chưa lưu)."""
	def sql(cau, ts=None, *a, **k):
		la("hỏi đúng ô", tuple(ts or ()), ("Vagabond Settings", dd.O_CAI_DAT))
		return [] if gia_tri is None else [(gia_tri,)]
	return sql


@ca("v645 bản 2 cau_hinh: đọc thẳng ô Cài đặt trong Singles; ô chưa lưu ra mặc định; đọc lỗi thì coi như TẮT và ghi Error Log")
def _():
	log = []
	with patch.object(_fr.db, "sql", _sql_o(json.dumps({"giam": 30000, "toi_thieu": 200000, "can_otp": 0})), create=True):
		la("đọc đúng ô", (dd.cau_hinh()["giam"], dd.cau_hinh()["can_otp"]), (30000, 0))
	with patch.object(_fr.db, "sql", _sql_o(None), create=True):
		la("ô chưa lưu", dd.cau_hinh(), dd.chuan(None))
	with patch.object(_fr.db, "sql", _sql_o(""), create=True):
		la("ô rỗng", dd.cau_hinh(), dd.chuan(None))

	def hong(*a, **k):
		raise RuntimeError("db")
	with patch.object(_fr.db, "sql", hong, create=True), patch.object(_fr, "log_error", lambda *a, **k: log.append(k.get("title"))):
		la("lỗi: tắt", dd.cau_hinh()["bat"], 0)
	la("có Error Log", len(log), 1)


@ca("Codex #548 (b238ff0bf8): cơ sở dữ liệu lỗi khi đọc cài đặt (cả đường Singles lẫn đường dự phòng) thì coi như TẮT, không rơi về mặc định đang bật")
def _():
	from vagabond import lib

	def hong(*a, **k):
		raise RuntimeError("mất kết nối cơ sở dữ liệu")
	log = []
	with patch.object(_fr.db, "get_single_value", hong, create=True), patch.object(_fr.db, "sql", hong, create=True), \
			patch.object(lib, "cfg", hong), patch.object(_fr, "log_error", lambda *a, **k: log.append(k.get("title"))):
		ch = dd.cau_hinh()
	la("tắt, không giảm oan", (ch["bat"], len(log)), (0, 1))


@ca("Codex #548 (d49ece60cf): cửa đọc cho quản lý doc_cai_dat gặp lỗi đọc Singles thì BÁO LỖI (app hiện thẻ Thử lại), không trả cấu hình dự phòng như đã lưu; đường tính tiền vẫn coi như tắt")
def _():
	from vagabond import khuyen_mai

	class Loi(Exception):
		pass

	def nem_loi(m, *a, **k):
		raise Loi(m)

	def hong(*a, **k):
		raise RuntimeError("lỗi đọc SQL")
	log = []
	with patch.object(khuyen_mai, "_kiem_quyen", lambda: None), patch.object(_fr.db, "sql", hong, create=True), \
			patch.object(_fr, "throw", nem_loi), patch.object(dd, "otp_mo", lambda: True), \
			patch.object(_fr, "log_error", lambda *a, **k: log.append(k.get("title"))):
		try:
			r = dd.doc_cai_dat()
			dung("phải báo lỗi, không trả cấu hình dự phòng: " + json.dumps(r.get("cai_dat")), False)
		except Loi as e:
			dung("câu dễ hiểu: " + str(e), "chưa đọc được cài đặt" in str(e))
		la("ghi Error Log", len(log), 1)
		la("đường tính tiền vẫn tắt", dd.cau_hinh()["bat"], 0)
	with patch.object(khuyen_mai, "_kiem_quyen", lambda: None), patch.object(dd, "otp_mo", lambda: False), \
			patch.object(_fr.db, "sql", _sql_o(json.dumps({"giam": 30000, "can_otp": 0})), create=True):
		r = dd.doc_cai_dat()
	la("đọc được thì trả đúng ô đã lưu", (r["cai_dat"]["giam"], r["cai_dat"]["can_otp"], r["otp_mo"]), (30000, 0, 0))
	with patch.object(khuyen_mai, "_kiem_quyen", lambda: None), patch.object(dd, "otp_mo", lambda: False), \
			patch.object(_fr.db, "sql", _sql_o(None), create=True):
		la("ô chưa lưu thì mặc định", dd.doc_cai_dat()["cai_dat"], dd.chuan(None))


@ca("v645 bản 2 luu_cai_dat: kiểm quyền sửa khuyến mãi; số sai không lưu và báo câu; lưu đúng thì ghi JSON vào ô và đọc lại ra đúng")
def _():
	from vagabond import khuyen_mai
	ghi, quyen = {}, []

	class Loi(Exception):
		pass

	def nem_loi(m, *a, **k):
		raise Loi(m)
	with patch.object(khuyen_mai, "_kiem_quyen_sua", lambda: quyen.append(1)), \
			patch.object(_fr.db, "set_single_value", lambda dt, o, v: ghi.update({(dt, o): v}), create=True), \
			patch.object(_fr.db, "commit", lambda: None, create=True), patch.object(_fr, "throw", nem_loi), \
			patch.object(dd, "otp_mo", lambda: False):
		try:
			dd.luu_cai_dat(json.dumps({"giam": 100000, "toi_thieu": 50000}))
			dung("phải báo", False)
		except Loi as e:
			dung("câu: " + str(e), "lớn hơn mức giảm" in str(e))
		la("số sai không ghi", ghi, {})
		r = dd.luu_cai_dat(json.dumps({"bat": 1, "giam": "30.000", "toi_thieu": 200000, "can_otp": 0, "hien_thanh_toan": 0, "hien_uu_dai": 1}))
	la("đã kiểm quyền hai lần", len(quyen), 2)
	la("trả cài đặt sạch", (r["cai_dat"]["giam"], r["cai_dat"]["hien_thanh_toan"], r["otp_mo"]), (30000, 0, 0))
	o = ghi[("Vagabond Settings", dd.O_CAI_DAT)]
	with patch.object(_fr.db, "sql", _sql_o(o), create=True):
		la("đọc lại ra đúng", dd.cau_hinh(), r["cai_dat"])


@ca("v645 bản 2 xem_uu_dai: tắt trong Khuyến mãi thì không thẻ, không giảm; không bắt mã Zalo, giảm 30.000 thì giỏ trừ 30.000 ngay, trang nhận cờ")
def _():
	xem, dau, _km, _log = _xem(dau=_dau_that({"bat": 0}))
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": SO})
	la("tắt", (r["giam"], r["don_dau"]["trang_thai"], r["don_dau"]["ap_dung"]), (0, dd.KHONG, 0))
	xem, dau, _km, _log = _xem(dau=_dau_that({"can_otp": 0, "giam": 30000, "toi_thieu": 200000, "hien_thanh_toan": 0}, otp=False))
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": SO})
	la("giảm 30.000 không cần xác thực", (r["giam"], r["ap"]), (30000, [{"ten": dd.TEN, "giam": 30000}]))
	la("cờ cho trang", (r["don_dau"]["trang_thai"], r["don_dau"]["can_otp"], r["don_dau"]["hien"], r["don_dau"]["ap_dung"]), (dd.DU, 0, 0, 1))


@ca("v645 bản 2 tao_don: giảm theo cài đặt (30.000) tới Pancake và ảnh chụp; tắt thì đơn đi giá đủ")
def _():
	dau = _dau_that({"can_otp": 0, "giam": 30000, "toi_thieu": 200000})
	r, vet = _tao(dau, don={"giam_da_xem": 30000})
	la("đơn thành", r.get("ok"), 1)
	sn = json.loads(vet.truong["snapshot"])
	la("ảnh chụp", (sn["uu_dai"]["giam"], sn["uu_dai"]["don_dau"]), (30000, 1))
	la("Pancake nhận 30.000", sum(x.get("discount_each_product", 0) * x["quantity"] for x in vet.body["items"]), 30000)
	r2, vet2 = _tao(_dau_that({"bat": 0}), don={"giam_da_xem": 0})
	la("tắt: đơn thành, không giảm", (r2.get("ok"), sum(x.get("discount_each_product", 0) * x["quantity"] for x in vet2.body["items"])), (1, 0))


@ca("v645 bản 2 trang Ưu đãi: thẻ đơn đầu đứng trước thẻ ERP; đơn đầu hỏng không kéo mất ưu đãi ERP; trình biên tập liệt kê cả đơn đầu")
def _():
	from vagabond import khuyen_mai
	from vagabond import noi_dung_web as nw
	log = []
	with patch.object(dd, "doc_o", lambda: ""), patch.object(khuyen_mai, "the_web_dang_hien", lambda *a: [{"id": "erp-SN10"}]), \
			patch.object(khuyen_mai, "ds_web_bien_tap", lambda *a: [{"id": "erp-SN10"}]):
		la("thứ tự", [x["id"] for x in nw._the_uu_dai_erp()], ["don-dau-web", "erp-SN10"])
		la("biên tập", [x["id"] for x in nw._uu_dai_erp_bien_tap()], ["don-dau-web", "erp-SN10"])
	with patch.object(dd, "doc_o", lambda: json.dumps({"hien_uu_dai": 0})), patch.object(khuyen_mai, "the_web_dang_hien", lambda *a: [{"id": "erp-SN10"}]):
		la("không chọn trang Ưu đãi", [x["id"] for x in nw._the_uu_dai_erp()], ["erp-SN10"])
	with patch.object(dd, "the_uu_dai", lambda *a: 1 / 0), patch.object(khuyen_mai, "the_web_dang_hien", lambda *a: [{"id": "erp-SN10"}]), \
			patch.object(_fr, "log_error", lambda *a, **k: log.append(k.get("title"))):
		la("đơn đầu hỏng vẫn còn ERP", [x["id"] for x in nw._the_uu_dai_erp()], ["erp-SN10"])
	la("ghi Error Log", len(log), 1)


@ca("v645 bản 2 màn Khuyến mãi trong app chạy thật bằng node (hanh_vi/km_don_dau_645.js)")
def _():
	import os
	import subprocess
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/km_don_dau_645.js"], cwd=goc, capture_output=True, text=True, timeout=60)
	dung("node: " + r.stdout[-1500:] + r.stderr[-800:], r.returncode == 0)
	dung("đủ số ca", "ca dat, 0 ca hong" in r.stdout and int(r.stdout.split(" ca dat")[0].split()[-1]) >= 4)

