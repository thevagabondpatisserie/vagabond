# -*- coding: utf-8 -*-
"""v653 tin Zalo "Bánh có sẵn hôm nay" kèm ảnh (anh Việt 12/11/2026 23:23).

Ca chốt:
  - danh sách lấy đúng cột BÁN ĐƯỢC của bảng Kiểm bánh hôm nay, bỏ bánh hết;
  - số đổi thì gửi, không đổi thì im; hai tin cách nhau ít nhất 15 phút, chỉ
    trong giờ mở cửa; thay đổi trong lúc chờ gom vào tin sau;
  - trạng thái quay lại giống một lần trước vẫn gửi (khoá chống trùng có giờ);
  - tin đúng mã tin, đúng chủ đề, có ảnh; vẽ ảnh hỏng thì vẫn gửi chữ;
  - ảnh lưới vẽ được thật (khi máy có Pillow): mỗi bánh một ô, tên hai dòng.
"""

import datetime as dt
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

fr = gia_lap()
if not hasattr(fr.utils, "get_url"):
	fr.utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import anh_bang  # noqa: E402
from vagabond import tin_banh_co_san as t  # noqa: E402

D = lambda **k: dict(k)  # noqa: E731


def _dong(*cap):
	return [D(ma_hang=m, ten_banh=ten, hinh="https://anh/%s.jpg" % m, co_the_ban=so) for m, ten, so in cap]


@ca("v653 THUẦN: bánh còn bán từ cột BÁN ĐƯỢC, bỏ bánh hết, số nhiều trước; dấu đổi khi số đổi")
def _thuan():
	ds = t.danh_sach(_dong(("A", "Tira 18", 2), ("B", "Epi 12", 0), ("C", "Kankin 16", 5), ("D", "Roman", -1)))
	la("chỉ bánh còn, số nhiều trước", [(x["ma"], x["so"]) for x in ds], [("C", 5), ("A", 2)])
	v1 = t.dau_van_tay(ds)
	la("thứ tự không đổi dấu", t.dau_van_tay(list(reversed(ds))), v1)
	dung("số đổi thì dấu đổi", t.dau_van_tay(t.danh_sach(_dong(("A", "Tira 18", 1), ("C", "Kankin 16", 5)))) != v1)
	la("trong giờ, lần đầu", t.nen_gui(dt.datetime(2026, 11, 13, 9, 0)), True)
	la("trước giờ mở cửa", t.nen_gui(dt.datetime(2026, 11, 13, 7, 59)), False)
	la("sau 21:30", t.nen_gui(dt.datetime(2026, 11, 13, 21, 31)), False)
	la("mới 10 phút", t.nen_gui(dt.datetime(2026, 11, 13, 9, 10), dt.datetime(2026, 11, 13, 9, 0)), False)
	la("đủ 15 phút", t.nen_gui(dt.datetime(2026, 11, 13, 9, 15), dt.datetime(2026, 11, 13, 9, 0)), True)
	c = t.chu_tin(ds, 2, "09:15")
	la("chú thích đủ ý", c[:3], ["Cập nhật 09:15: còn 2 loại, tổng 7 bánh bán được hôm nay.", "Kankin 16: 5", "Tira 18: 2"])
	dung("báo số loại đã hết", c[-1] == "2 loại trên bảng đã hết.")
	dung("hết sạch thì mời đặt trước", "đặt trước" in " ".join(t.chu_tin([], 3, "20:00")))
	do = lambda s: len(s) * 10  # noqa: E731
	la("tên hai dòng ngắt theo từ", anh_bang.chia_hai_dong("Bánh Ổ Tira Missing U 3.0", 130, do), ["Bánh Ổ Tira", "Missing U 3.0"])
	la("dòng hai dài thì cắt có dấu", anh_bang.chia_hai_dong("Bánh Ổ Tira Missing U 3.0 18cm", 130, do)[1][-1], "…")
	la("tên ngắn một dòng", anh_bang.chia_hai_dong("Epi 12", 120, do), ["Epi 12"])
	la("quá 30 ô thì báo còn", (len(anh_bang.xep_luoi(range(35))[0]), anh_bang.xep_luoi(range(35))[1]), (30, 5))


class Bo(object):
	def __init__(self):
		self.d = {}

	def get_value(self, k):
		return self.d.get(k)

	def set_value(self, k, v, expires_in_sec=None):
		self.d[k] = v


def _chay(bay, dong, bo, tin, anh="https://anh/luoi.png"):
	from vagabond import kenh_zalo

	vs = [um.patch.object(fr.db, "exists", lambda *a, **k: True), um.patch.object(fr, "get_all", lambda *a, **k: [dict(x) for x in dong]),
		um.patch.object(fr, "cache", lambda: bo, create=True),
		um.patch("frappe.utils.now_datetime", lambda: bay), um.patch("frappe.utils.nowdate", lambda: str(bay.date())),
		um.patch("frappe.utils.get_datetime", lambda v: dt.datetime.fromisoformat(str(v)), create=True),
		um.patch.object(anh_bang, "anh_luoi", lambda *a, **k: anh),
		um.patch.object(kenh_zalo, "bao_hoac_ghi_loi", lambda *a, **k: tin.append((a, k)))]
	for v in vs:
		v.start()
	try:
		return t.quet()
	finally:
		for v in reversed(vs):
			v.stop()


@ca("v653 nhịp 5 phút: đổi thì gửi, không đổi thì im, cách 15 phút, gom thay đổi lúc chờ, trạng thái cũ quay lại vẫn gửi")
def _nhip():
	bo, tin = Bo(), []
	A = _dong(("A", "Tira 18", 2), ("C", "Kankin 16", 5))
	B = _dong(("A", "Tira 18", 1), ("C", "Kankin 16", 5))
	h = lambda gio, phut: dt.datetime(2026, 11, 13, gio, phut)  # noqa: E731
	_chay(h(9, 0), A, bo, tin)
	la("lần đầu trong ngày gửi", len(tin), 1)
	a, k = tin[0]
	la("đúng loại, chủ đề, mã tin, có ảnh", (a[0], a[1], k["ma_tin"], k["anh"]), ("ban_tin", "ban_hang", "bh_banh_co_san", "https://anh/luoi.png"))
	_chay(h(9, 5), A, bo, tin)
	la("không đổi thì im", len(tin), 1)
	_chay(h(9, 10), B, bo, tin)
	la("đổi mà mới 10 phút: chờ", len(tin), 1)
	_chay(h(9, 15), B, bo, tin)
	la("đủ 15 phút: gửi số mới", (len(tin), tin[-1][0][3][2]), (2, "Tira 18: 1"))
	_chay(h(9, 30), A, bo, tin)
	la("quay lại đúng trạng thái cũ vẫn gửi", len(tin), 3)
	dung("khoá chống trùng có giờ", tin[2][1]["khoa"] != tin[0][1]["khoa"])
	_chay(h(22, 0), B, bo, tin)
	la("ngoài giờ không gửi", len(tin), 3)
	_chay(h(9, 45), B, bo, tin, anh=None)
	la("vẽ ảnh hỏng vẫn gửi chữ", (len(tin), tin[-1][1]["anh"]), (4, None))


@ca("v653 ảnh lưới vẽ được thật: mỗi bánh một ô ảnh vuông, số to ở góc, tên hai dòng (máy có Pillow)")
def _ve():
	try:
		from PIL import Image
	except ImportError:
		return
	import io

	o = [{"ten": "Bánh Ổ Tira-Missing-U 3.0, 18cm", "so": 2, "anh": "x"}, {"ten": "Kankin 16", "so": 12, "anh": ""},
		{"ten": "Epi 12", "so": 1, "anh": "y"}, {"ten": "Roman De La Rose 18", "so": 3, "anh": "hong"}]

	def anh_cua(url):
		if url == "hong":
			raise IOError("tải hỏng")
		return Image.new("RGB", (640, 480), (200, 160, 120))
	png = anh_bang.ve_luoi("Bánh có sẵn hôm nay 13/11", "Cập nhật 09:15", o, anh_cua)
	h = Image.open(io.BytesIO(png))
	la("rộng 1080, hai hàng ô", (h.size[0], h.size[1] > 2 * anh_bang.O_LUOI), (1080, True))
	dung("ô có ảnh lấy màu ảnh bánh", h.getpixel((anh_bang.LE + 5, 200)) == (200, 160, 120))



@ca("v653 bản vá tích tin mới: nhóm nhận đơn web mới thêm Bánh có sẵn, nhóm gom mua thêm Dự chi; nhóm trống không đụng; chạy lại không đổi")
def _tich():
	from vagabond import kenh_zalo
	from vagabond.patches import v653_tin_zalo_moi as p

	la("nhóm Sales", p.tin_them("bh_don_web_moi, bh_dat_ban"), "bh_don_web_moi, bh_dat_ban, bh_banh_co_san")
	la("nhóm Thu mua", p.tin_them("tm_gom_mua"), "tm_gom_mua, tm_du_chi")
	la("nhóm trống nhận mọi tin, không đụng", p.tin_them(""), None)
	la("chạy lại không đổi", p.tin_them("bh_don_web_moi, bh_banh_co_san"), None)
	la("nhóm khác không đụng", p.tin_them("kho_da_nhap"), None)
	dung("mã có thật", all(m in kenh_zalo.TIN for _, m in p.THEO_MOC))
