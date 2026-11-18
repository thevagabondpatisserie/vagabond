# -*- coding: utf-8 -*-
"""v664 Bài đăng: tự đăng Facebook, Instagram, Threads; Kho bản thảo (anh Việt 16/11/2026).

Ca chốt:
  - trạng thái bài gom từ kênh (Đang đăng tính như Đã hẹn giờ), kênh tự đăng theo kết nối
    và kiểu bài (Story không có Threads), tới giờ, kênh kẹt;
  - Duyệt: kênh đã nối chờ hệ thống đăng (đăng ngay thì xếp lượt), kênh chưa nối đăng tay;
  - lượt đăng: chỉ lượt đổi kênh sang Đang đăng mới gọi Meta; lượt thứ hai chạy chồng
    không gọi lần nữa (H8 loại 1, 4); một kênh lỗi không chặn kênh khác; lỗi thì kênh
    Chờ đăng tay kèm lý do; kết nối mất lúc tới giờ thì chuyển đăng tay;
  - kênh kẹt Đang đăng quá 15 phút chuyển đăng tay, báo chưa rõ, không tự đăng lại;
  - Thử lại: chỉ kênh đang Chờ đăng tay và đã nối; bấm hai lần không đăng hai;
  - đang đăng thì không trả về nháp, không huỷ;
  - chuỗi gọi Meta: Facebook một ảnh, nhiều ảnh, Story; Instagram băng chuyền; Threads;
    mất mạng ở bước công bố là "chưa rõ"; chế độ kiểm không gọi thật; câu lỗi theo mã;
  - chọn Trang theo token; hộp cắt ảnh;
  - Kho bản thảo: chữ trong Word, bảng Excel có và không có dòng tiêu đề cột, ngày giờ
    nhiều kiểu, giờ đã qua bỏ, kênh gõ tay; nhập tệp tạo bản thảo, bấm hai lần không
    nhập hai lần, tệp lạ từ chối;
  - nối: ô cài đặt, chip Cài đặt lõi, nhịp gia hạn Threads, trạng thái kênh trên doctype.
"""

import datetime as dt
import io
import json
import os
import unittest.mock as um
import zipfile

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import bai_dang as x  # noqa: E402
from vagabond import mxh as m  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BAY_GIO = dt.datetime(2026, 11, 16, 19, 30)


def _doc(t):
	return io.open(os.path.join(GOC, t), encoding="utf-8").read()


# ------------------------------------------------------------ phần thuần

@ca("v664 gom trạng thái: đủ đã đăng là Đã đăng; còn kênh tay là Chờ đăng tay; còn kênh hệ thống đăng hay đang đăng là Đã hẹn giờ")
def _gom():
	la("đủ", x.gom_trang_thai(x.TT_HEN, [x.K_XONG, x.K_XONG]), x.TT_XONG)
	la("còn tay", x.gom_trang_thai(x.TT_HEN, [x.K_XONG, x.K_TAY, x.K_HEN]), x.TT_TAY)
	la("tay xong, còn hệ thống đăng: về Đã hẹn giờ", x.gom_trang_thai(x.TT_TAY, [x.K_XONG, x.K_DANG]), x.TT_HEN)
	la("nháp không đổi", x.gom_trang_thai(x.TT_NHAP, [x.K_XONG]), x.TT_NHAP)


@ca("v664 kênh tự đăng: chỉ kênh đã nối; Story bỏ Threads và Zalo OA (v666: Zalo OA nối được thì tự đăng)")
def _tu_dong():
	la("bài", sorted(x.kenh_tu_dong({"fb", "th", "zl"})), ["fb", "th", "zl"])
	la("Story bỏ Zalo OA", sorted(x.kenh_tu_dong({"fb", "zl"}, x.KIEU_STORY)), ["fb"])
	la("Story", sorted(x.kenh_tu_dong({"fb", "ig", "th"}, x.KIEU_STORY)), ["fb", "ig"])
	la("chưa nối", x.kenh_tu_dong(None), set())


@ca("v664 tới giờ, chia kênh, kênh kẹt: không hẹn là tới ngay; kênh tự đăng lúc duyệt mà nay mất nối thì đăng tay; kẹt quá 15 phút")
def _gio():
	la("không hẹn", x.den_gio(None, BAY_GIO), True)
	la("hẹn đúng giờ", x.den_gio("2026-11-16 19:30:00", BAY_GIO), True)
	la("hẹn sau 1 phút", x.den_gio("2026-11-16 19:31:00", BAY_GIO), False)
	d, t = x.chia_kenh_den_gio([("fb", x.K_HEN, 1), ("ig", x.K_HEN, 1), ("zl", x.K_HEN, 0), ("th", x.K_XONG, 1)], {"fb"})
	la("chia", (d, t), (["fb"], ["ig", "zl"]))
	la("chưa tự đăng lúc duyệt thì không tự đăng dù nay đã nối", x.chia_kenh_den_gio([("fb", x.K_HEN, 0)], {"fb"}), ([], ["fb"]))
	la("kẹt 16 phút", x.ket_dang("2026-11-16 19:14:00", BAY_GIO), True)
	la("15 phút chưa kẹt", x.ket_dang("2026-11-16 19:15:00", BAY_GIO), False)


@ca("v664 bảng Kiểm ghi kênh nào hệ thống tự đăng, kênh nào đăng tay")
def _kiem_tu():
	b = {"kieu": x.KIEU_BAI, "kenh_chon": ["fb", "ig", "zl"], "anh": [{"khung": "1:1"}], "hen_luc": "",
		"ban": {"fb": {"chu": "a"}, "ig": {"chu": "b"}, "zl": {"chu": "c", "tieu_de": "T"}}}
	k = [z["chu"] for z in x.kiem_bai(b, BAY_GIO, tu={"fb", "ig"}) if z["muc"] == "ok"]
	dung("có dòng tự đăng", "Hệ thống tự đăng: Facebook, Instagram; Đăng tay: Zalo OA" in k)
	dung("không truyền kết nối thì không có dòng", not any("tự đăng" in z["chu"] for z in x.kiem_bai(b, BAY_GIO)))


@ca("v664 câu lỗi Meta nói việc cần làm theo mã: token hỏng, thiếu quyền, bị chặn tạm, quá nhịp, câu của Meta")
def _loi():
	dung("190", m.loi_de_hieu("Facebook", {"error": {"code": 190, "message": "x"}}).startswith("Token Facebook hết hạn hoặc bị thu hồi"))
	dung("10 thiếu quyền", "thiếu quyền" in m.loi_de_hieu("Instagram", {"error": {"code": "10"}}))
	dung("368 chặn tạm", "tạm chặn" in m.loi_de_hieu("Facebook", {"error": {"code": 368}}))
	dung("4 quá nhịp", "15 phút" in m.loi_de_hieu("Threads", {"error": {"code": 4}}))
	la("câu của Meta", m.loi_de_hieu("Instagram", {"error": {"code": 9004, "error_user_msg": "Ảnh quá nhỏ"}}), "Instagram từ chối bài: Ảnh quá nhỏ")
	dung("rỗng", "Thử lại" in m.loi_de_hieu("Facebook", None))


@ca("v664 hộp cắt giữa ảnh: ngang cắt hai bên, dọc cắt trên dưới, đúng khung giữ nguyên, số hỏng None")
def _cat():
	la("1:1 thành 4:5", m.hop_cat(1080, 1080, "4:5"), (108, 0, 972, 1080))
	la("2:3 thành 4:5", m.hop_cat(1000, 1500, "4:5"), (0, 125, 1000, 1375))
	la("đúng khung", m.hop_cat(1080, 1350, "4:5"), (0, 0, 1080, 1350))
	la("hỏng", (m.hop_cat(0, 10, "4:5"), m.hop_cat(10, 10, "x")), (None, None))


@ca("v664 chọn Trang: có mã thì đúng mã (bỏ dấu cách); không mã chỉ nhận khi thấy một Trang; nhiều Trang hay không Trang thì báo cách sửa")
def _trang():
	ds = [{"id": "111", "name": "A"}, {"id": "222", "name": "B"}]
	la("mã có dấu cách", m.chon_trang(ds, " 22 2 ")[0]["name"], "B")
	dung("nhiều Trang báo", "2 Trang" in m.chon_trang(ds)[1])
	la("một Trang", m.chon_trang(ds[:1])[0]["id"], "111")
	dung("không Trang báo gán", "gán Trang" in m.chon_trang([])[1])
	dung("mã lạ báo", "333" in m.chon_trang(ds, "333")[1])
	la("chữ cắt ở trần", m.chu_cho_kenh("  abc  ", 2), "ab")


# ------------------------------------------------------------ luồng có khoá, bản giả

class _Dong(object):
	def __init__(self, **k):
		self.__dict__.update({"name": None, "idx": 0, "chu": "", "tieu_de": "", "ai_soan": 0, "dang_luc": None, "link": "",
			"tu_dong": 0, "loi": "", "ma_bai": "", "file_url": "", "rong": 0, "cao": 0, "khung": "", "ma_bam": ""})
		self.__dict__.update(k)

	def get(self, k, d=None):
		return getattr(self, k, d)


class _Bai(object):
	def __init__(self, **k):
		self.name = "BD-26-11-0007"
		self.trang_thai = x.TT_NHAP
		self.kieu = x.KIEU_BAI
		self.y_chinh = "Cheesecake"
		self.kenh_chon = "fb,ig,th"
		self.hen_luc = None
		self.ban_luu = 3
		self.tieu_de = "Cheesecake"
		self.nguoi_duyet = None
		self.duyet_luc = None
		self.modified = "2026-11-16 19:00:00"
		self.anh = [_Dong(name="a1", idx=1, file_url="/f/1.jpg", rong=1080, cao=1080, khung="1:1")]
		self.kenh = [_Dong(ma_kenh=k, chu="Bánh " + k, trang_thai=x.K_CHUA) for k in ("fb", "ig", "th")]
		self.__dict__.update(k)

	def get(self, k, d=None):
		return getattr(self, k, d)

	def set(self, k, v):
		setattr(self, k, v)

	def append(self, k, v):
		r = _Dong(**v)
		getattr(self, k).append(r)
		return r

	def dong(self, k):
		return [r for r in self.kenh if r.ma_kenh == k][0]


class _KhoaGia(object):
	def __enter__(self):
		return self

	def __exit__(self, *a):
		return False


def _chay(doc, ham, noi=(), bay_gio=BAY_GIO, dang=None, noi_theo=None, **k):
	"""Chạy một hàm của bai_dang với bản giả. dang: hàm thay mxh.dang (ghi lại lời gọi).
	noi_theo (v672): kênh đang nối theo từng thương hiệu, thay cho noi."""
	nhat = {"luu": [], "xep": [], "bao_tay": [], "bao_loi": [], "commit": 0, "goi": []}

	def _dang(kenh, ma_bai, chu, anh, story=False, tieu_de="", hieu="vagabond"):
		nhat["goi"].append((kenh, chu, len(anh), story))
		nhat.setdefault("tieu_de", []).append((kenh, tieu_de))
		nhat.setdefault("hieu", []).append((kenh, hieu))
		if dang:
			return dang(kenh)
		return ("ID-" + kenh, "https://x.com/" + kenh)

	def _commit():
		nhat["commit"] += 1
	with um.patch.object(x, "_kiem_soan", lambda: None), um.patch.object(x, "_kiem_duyet", lambda: None), \
			um.patch.object(x, "_la_duyet", lambda: True), um.patch.object(x, "_doc_khoa", lambda ma: doc), \
			um.patch.object(x, "_khoa_lich", lambda: _KhoaGia()), um.patch.object(x, "_noi", lambda *a: (nhat.setdefault("noi_hieu", []).append(a[1] if len(a) > 1 else "vagabond"),
				set(noi_theo.get(a[1] if len(a) > 1 else "vagabond", ()) if noi_theo else noi))[1]), \
			um.patch.object(x, "_hieu_ma", lambda ma: x.hieu_bai(doc)), \
			um.patch.object(x, "_luu", lambda d: nhat["luu"].append([(r.ma_kenh, r.trang_thai) for r in d.kenh])), \
			um.patch.object(x, "_bay_gio", lambda: bay_gio), um.patch.object(x, "_trung_gio", lambda d: []), \
			um.patch.object(x, "_anh_cu", lambda d: []), um.patch.object(x, "gio_vang", lambda: list(x.GIO_VANG_MAC_DINH)), \
			um.patch.object(x, "_xep_dang", lambda ma: nhat["xep"].append(ma)), \
			um.patch.object(x, "_bao_den_gio", lambda d, ten: nhat["bao_tay"].append(ten)), \
			um.patch.object(x, "_bao_loi_dang", lambda d, kenh, chu, mot_phan=False: (nhat["bao_loi"].append((kenh, chu)),
				nhat.setdefault("mot_phan", []).append((kenh, mot_phan)))), \
			um.patch.object(m, "dang", _dang), \
			um.patch.object(x.frappe.db, "commit", _commit, create=True), um.patch.object(x.frappe.db, "rollback", lambda: None, create=True), \
			um.patch.object(x.frappe, "log_error", lambda *a, **kk: None, create=True), \
			um.patch.object(x.frappe, "session", type("S", (), {"user": "mkt@x"})(), create=True):
		ra = ham(**k)
	return ra, nhat


def _tt(doc):
	return [(r.ma_kenh, r.trang_thai) for r in doc.kenh]


@ca("v664 Duyệt đăng ngay: Facebook, Instagram đã nối chờ hệ thống đăng và xếp MỘT lượt; Threads chưa nối đăng tay ngay")
def _duyet_ngay():
	doc = _Bai()
	ra, n = _chay(doc, x.duyet, noi={"fb", "ig"}, ma=doc.name, ban_luu=3)
	la("kênh", _tt(doc), [("fb", x.K_HEN), ("ig", x.K_HEN), ("th", x.K_TAY)])
	la("tự đăng ghi trên kênh", [r.tu_dong for r in doc.kenh], [1, 1, 0])
	la("bài Chờ đăng tay (còn Threads)", doc.trang_thai, x.TT_TAY)
	la("xếp một lượt", n["xep"], [doc.name])
	la("màn nhận kênh tự đăng được thử lại", [(z["k"], z["tu"], z["dang_duoc"]) for z in ra["bai"]["kenh"]], [("fb", 1, 0), ("ig", 1, 0), ("th", 0, 0)])


@ca("v664 Duyệt có giờ hẹn: mọi kênh Đã hẹn giờ, chưa xếp lượt; chưa nối kênh nào thì như v662")
def _duyet_hen():
	doc = _Bai(hen_luc="2026-11-17 07:30:00")
	_, n = _chay(doc, x.duyet, noi={"fb"}, ma=doc.name, ban_luu=3)
	la("kênh", (_tt(doc), [r.tu_dong for r in doc.kenh], doc.trang_thai), ([("fb", x.K_HEN), ("ig", x.K_HEN), ("th", x.K_HEN)], [1, 0, 0], x.TT_HEN))
	la("chưa xếp", n["xep"], [])
	doc2 = _Bai()
	_, n2 = _chay(doc2, x.duyet, ma=doc2.name, ban_luu=3)
	la("chưa nối: đăng tay ngay, không xếp", (doc2.trang_thai, set(t for _, t in _tt(doc2)), n2["xep"]), (x.TT_TAY, {x.K_TAY}, []))


def _da_duyet(**k):
	doc = _Bai(**dict({"trang_thai": x.TT_HEN, "duyet_luc": "2026-11-16 19:29:00"}, **k))
	for r in doc.kenh:
		r.trang_thai = x.K_HEN
		r.tu_dong = 1
	return doc


@ca("v664 lượt đăng: Facebook lên có link; Instagram lỗi thì Chờ đăng tay kèm lý do và nhắn Marketing; Threads vẫn đăng (một kênh lỗi không chặn kênh khác)")
def _dang():
	doc = _da_duyet()

	def dang(k):
		if k == "ig":
			raise m.LoiDang("Instagram từ chối bài: Ảnh quá nhỏ")
		return ("ID-" + k, "https://x.com/" + k)
	_, n = _chay(doc, x.dang_bai, noi={"fb", "ig", "th"}, dang=dang, ma=doc.name)
	la("gọi đủ ba kênh, chữ đúng kênh", [(g[0], g[1]) for g in n["goi"]], [("fb", "Bánh fb"), ("ig", "Bánh ig"), ("th", "Bánh th")])
	la("lần lưu đầu: cả ba Đang đăng", n["luu"][0], [("fb", x.K_DANG), ("ig", x.K_DANG), ("th", x.K_DANG)])
	la("kết quả", _tt(doc), [("fb", x.K_XONG), ("ig", x.K_TAY), ("th", x.K_XONG)])
	la("link, mã bài", (doc.dong("fb").link, doc.dong("fb").ma_bai), ("https://x.com/fb", "ID-fb"))
	la("lý do", doc.dong("ig").loi, "Instagram từ chối bài: Ảnh quá nhỏ")
	la("nhắn lỗi", n["bao_loi"], [("ig", "Instagram từ chối bài: Ảnh quá nhỏ")])
	la("bài Chờ đăng tay", doc.trang_thai, x.TT_TAY)
	dung("chốt giao dịch trước khi gọi Meta và sau mỗi kết quả", n["commit"] >= 4)


@ca("v664 H8 loại 1, 4: lượt đăng thứ hai chạy chồng (lúc lượt đầu đang gọi Meta) KHÔNG gọi Meta lần nữa")
def _chong():
	doc = _da_duyet(kenh_chon="fb")
	doc.kenh = [doc.dong("fb")]
	goi_trong = []

	def dang(k):
		_, n2 = _chay(doc, x.dang_bai, noi={"fb"}, ma=doc.name)
		goi_trong.append(len(n2["goi"]))
		return ("ID-fb", "https://x.com/fb")
	_, n = _chay(doc, x.dang_bai, noi={"fb"}, dang=dang, ma=doc.name)
	la("lượt đầu gọi một lần", len(n["goi"]), 1)
	la("lượt chồng không gọi", goi_trong, [0])
	la("Đã đăng", (_tt(doc), doc.trang_thai), ([("fb", x.K_XONG)], x.TT_XONG))
	_, n3 = _chay(doc, x.dang_bai, noi={"fb"}, ma=doc.name)
	la("chạy lại sau khi xong: không gọi, không lưu", (n3["goi"], n3["luu"]), ([], []))


@ca("v664 lượt đăng: chưa tới giờ hẹn thì không làm gì; tới giờ mà Instagram mất nối thì chuyển đăng tay, ghi lý do, nhắn nhóm Marketing")
def _den_gio_mat_noi():
	doc = _da_duyet(hen_luc="2026-11-16 20:00:00")
	_, n = _chay(doc, x.dang_bai, noi={"fb", "ig", "th"}, ma=doc.name)
	la("chưa tới giờ", (n["goi"], n["luu"]), ([], []))
	doc2 = _da_duyet(hen_luc="2026-11-16 19:30:00")
	_, n2 = _chay(doc2, x.dang_bai, noi={"fb", "th"}, ma=doc2.name)
	la("Instagram đăng tay", (doc2.dong("ig").trang_thai, "chưa nối" in doc2.dong("ig").loi), (x.K_TAY, True))
	la("nhắn", n2["bao_tay"], [["Instagram"]])
	la("hai kênh kia đăng", [g[0] for g in n2["goi"]], ["fb", "th"])


@ca("v664 lỗi lạ khi đăng (không phải lỗi Meta): kênh Chờ đăng tay, báo chưa rõ đã lên chưa")
def _loi_la():
	doc = _da_duyet(kenh_chon="fb")
	doc.kenh = [doc.dong("fb")]

	def dang(k):
		raise RuntimeError("hỏng")
	_chay(doc, x.dang_bai, noi={"fb"}, dang=dang, ma=doc.name)
	la("Chờ đăng tay", doc.dong("fb").trang_thai, x.K_TAY)
	dung("chưa rõ", "chưa rõ" in doc.dong("fb").loi)


@ca("v664 kênh kẹt Đang đăng: quá 15 phút thì Chờ đăng tay, báo chưa rõ, không tự đăng lại; chưa quá thì để yên; đã có kết quả thì không ghi đè")
def _ket():
	doc = _da_duyet(kenh_chon="fb")
	doc.kenh = [doc.dong("fb")]
	doc.dong("fb").trang_thai = x.K_DANG
	doc.dong("fb").dang_luc = "2026-11-16 19:00:00"
	with um.patch.object(x, "_kenh_ket", lambda b: [(doc.name, "fb")]):
		_, n = _chay(doc, x.go_ket)
	la("chuyển tay", (doc.dong("fb").trang_thai, "Chưa rõ" in doc.dong("fb").loi, n["goi"]), (x.K_TAY, True, []))
	doc2 = _da_duyet(kenh_chon="fb")
	doc2.kenh = [doc2.dong("fb")]
	doc2.dong("fb").trang_thai = x.K_DANG
	doc2.dong("fb").dang_luc = "2026-11-16 19:20:00"
	with um.patch.object(x, "_kenh_ket", lambda b: [(doc2.name, "fb")]):
		_, n2 = _chay(doc2, x.go_ket)
	la("mới 10 phút: để yên", (doc2.dong("fb").trang_thai, n2["luu"]), (x.K_DANG, []))
	_, n3 = _chay(doc, x._ghi_ket_qua, ma=doc.name, kenh="fb", tt=x.K_XONG, link="https://x.com/1")
	la("kết quả đến muộn sau khi đã chuyển tay: không ghi đè", (doc.dong("fb").trang_thai, n3["luu"]), (x.K_TAY, []))


@ca("v664 Thử lại: kênh Chờ đăng tay đã nối thì về chờ hệ thống đăng và xếp lượt; bấm hai lần không xếp thêm; chưa nối thì báo; đang đăng thì không trả về nháp, không huỷ")
def _thu_lai():
	doc = _da_duyet(trang_thai=x.TT_TAY)
	doc.dong("ig").trang_thai = x.K_TAY
	doc.dong("ig").loi = "Instagram từ chối bài"
	_, n = _chay(doc, x.thu_lai, noi={"fb", "ig"}, ma=doc.name, kenh="ig")
	la("về chờ đăng", (doc.dong("ig").trang_thai, doc.dong("ig").loi, doc.trang_thai, n["xep"]), (x.K_HEN, "", x.TT_HEN, [doc.name]))
	_, n2 = _chay(doc, x.thu_lai, noi={"fb", "ig"}, ma=doc.name, kenh="ig")
	la("bấm lần hai", (n2["xep"], n2["luu"]), ([], []))
	doc.dong("th").trang_thai = x.K_TAY
	nem("Threads chưa nối", lambda: _chay(doc, x.thu_lai, noi={"fb", "ig"}, ma=doc.name, kenh="th"))
	doc.dong("fb").trang_thai = x.K_DANG
	nem("đang đăng thì không trả về nháp", lambda: _chay(doc, x.tra_ve, ma=doc.name))
	nem("đang đăng thì không huỷ", lambda: _chay(doc, x.huy, ma=doc.name))


@ca("v664 nhịp 5 phút: gỡ kênh kẹt trước, rồi xếp mỗi bài tới giờ một lượt riêng")
def _quet():
	thu = []
	with um.patch.object(x, "go_ket", lambda b=None: thu.append("go_ket")), um.patch.object(x, "_bai_den_gio", lambda b: ["A", "B"]), \
			um.patch.object(x, "_xep_dang", lambda ma: thu.append(ma)), um.patch.object(x, "_bay_gio", lambda: BAY_GIO):
		x.quet_den_gio()
	la("thứ tự", thu, ["go_ket", "A", "B"])


# ------------------------------------------------------------ chuỗi gọi Meta

class _Goi(object):
	"""Thay mxh._goi: ghi lại lời gọi, trả lời theo đường dẫn."""

	def __init__(self, tra=None):
		self.ds = []
		self.tra = tra or {}
		self.so = 0

	def __call__(self, pt, url, tok, data=None, files=None, params=None, cong_bo=False, ten_kenh="Meta"):
		self.so += 1
		duong = url.split(".net/v1.0")[-1].split("v21.0")[-1]
		self.ds.append((pt, duong, dict(data or {}), sorted((files or {}).keys()), cong_bo))
		for k, v in self.tra.items():
			if duong.endswith(k):
				return v(data, params) if callable(v) else v
		if params and params.get("fields"):
			return {params["fields"]: "FINISHED" if params["fields"] in ("status_code", "status") else "https://link/" + duong}
		return {"id": "C%d" % self.so, "post_id": "P%d" % self.so}


def _meta(goi):
	return um.patch.object(m, "_goi", goi), um.patch.object(m, "anh_jpeg", lambda url, khung=None: b"JPG"), \
		um.patch.object(m, "url_cong_khai", lambda ma, nd: "https://site/files/bd.jpg"), um.patch.object(m.time, "sleep", lambda s: None)


def _voi(goi, ham, *a):
	p = _meta(goi)
	with p[0], p[1], p[2], p[3]:
		return ham(*a)


@ca("v664 Facebook: một ảnh đăng thẳng kèm chữ; nhiều ảnh tải ẩn rồi gắn vào một bài; Story qua photo_stories; bước cuối là bước công bố")
def _fb():
	tr = {"id": "PG", "token": "PT"}
	g = _Goi()
	ma, link = _voi(g, m.dang_fb, tr, "Chữ", [{"url": "/1"}])
	la("một ảnh", [(z[1], z[2].get("message"), z[3], z[4]) for z in g.ds[:1]], [("/PG/photos", "Chữ", ["source"], True)])
	dung("có link", link.startswith("https://link/"))
	g = _Goi()
	_voi(g, m.dang_fb, tr, "Chữ", [{"url": "/1"}, {"url": "/2"}])
	la("nhiều ảnh", [(z[1], z[2].get("published"), z[4]) for z in g.ds[:3]], [("/PG/photos", "false", False), ("/PG/photos", "false", False), ("/PG/feed", None, True)])
	la("gắn đủ hai ảnh", json.loads(g.ds[2][2]["attached_media"]), [{"media_fbid": "C1"}, {"media_fbid": "C2"}])
	g = _Goi()
	_voi(g, m.dang_fb, tr, "", [{"url": "/1"}], True)
	la("Story", [z[1] for z in g.ds], ["/PG/photos", "/PG/photo_stories"])


@ca("v664 Instagram băng chuyền: từng ảnh là mục băng chuyền, chờ xử lý xong, rồi CAROUSEL kèm chữ, công bố một lần; đang xử lý thì hỏi lại; lỗi xử lý thì báo")
def _ig():
	tr = {"id": "PG", "token": "PT", "ig": {"id": "IG"}}
	lan = {"n": 0}

	def trang_thai(d, p):
		lan["n"] += 1
		return {"status_code": "IN_PROGRESS" if lan["n"] == 1 else "FINISHED"}
	g = _Goi({"/C1": trang_thai})
	anh = [{"url": "/1", "khung": "4:5", "cat": True}, {"url": "/2", "khung": "4:5", "cat": False}]
	_voi(g, m.dang_ig, "BD", tr, "Chữ", anh)
	dang = [z for z in g.ds if z[0] == "POST"]
	la("chuỗi POST", [(z[1], z[2].get("is_carousel_item"), z[2].get("media_type"), z[4]) for z in dang],
		[("/IG/media", "true", None, False), ("/IG/media", "true", None, False), ("/IG/media", None, "CAROUSEL", False), ("/IG/media_publish", None, None, True)])
	la("CAROUSEL đủ con và chữ", (dang[2][2]["children"], dang[2][2]["caption"]), ("C1,C4", "Chữ"))
	la("hỏi lại khi đang xử lý", lan["n"], 2)
	g2 = _Goi({"status_code": lambda d, p: {"status_code": "ERROR"}})
	nem("lỗi xử lý ảnh", lambda: _voi(_Goi({"/C1": {"status_code": "ERROR"}}), m.dang_ig, "BD", tr, "Chữ", anh[:1]))
	dung("chưa nối Instagram thì báo", "doanh nghiệp" in _bat(lambda: _voi(g2, m.dang_ig, "BD", {"id": "PG", "token": "PT"}, "Chữ", anh)))


def _bat(f):
	try:
		f()
	except m.LoiDang as e:
		return e.chu
	return ""


@ca("v664 Threads: một ảnh IMAGE kèm chữ; không ảnh là TEXT; công bố qua threads_publish")
def _th():
	g = _Goi()
	_voi(g, m.dang_th, "BD", "TK", "Chữ", [{"url": "/1", "khung": "4:5", "cat": False}])
	dang = [z for z in g.ds if z[0] == "POST"]
	la("chuỗi", [(z[1], z[2].get("media_type"), z[4]) for z in dang], [("/me/threads", "IMAGE", False), ("/me/threads_publish", None, True)])
	g = _Goi()
	_voi(g, m.dang_th, "BD", "TK", "Chỉ chữ", [])
	la("TEXT", [z[2].get("media_type") for z in g.ds if z[0] == "POST"][:1], ["TEXT"])


class _Res(object):
	def __init__(self, ma, j):
		self.status_code = ma
		self._j = j
		self.content = b"x"

	def json(self):
		return self._j


@ca("v664 gọi Meta: mất mạng ở bước công bố là 'chưa rõ đã lên chưa'; ở bước khác là lỗi rõ; Meta báo lỗi thì câu theo mã; chế độ kiểm không gọi thật")
def _goi_that():
	class R(object):
		@staticmethod
		def request(*a, **k):
			raise IOError("mất mạng")
	with um.patch.object(m, "requests", R), um.patch.object(m.frappe, "log_error", lambda *a, **k: None, create=True), \
			um.patch.object(m.frappe, "get_traceback", lambda: "access_token=BIMAT", create=True):
		try:
			m._goi("POST", "u", "t", cong_bo=True, ten_kenh="Instagram")
			ro = None
		except m.LoiDang as e:
			ro = (e.ro, "chưa rõ" in e.chu)
		la("công bố mất mạng", ro, (False, True))
		try:
			m._goi("POST", "u", "t", ten_kenh="Instagram")
		except m.LoiDang as e:
			ro = e.ro
		la("bước khác", ro, True)

	class R2(object):
		@staticmethod
		def request(*a, **k):
			return _Res(400, {"error": {"code": 190}})
	with um.patch.object(m, "requests", R2):
		dung("token hỏng", "hết hạn" in _bat(lambda: m._goi("GET", "u", "t", ten_kenh="Facebook")))
	m.frappe.flags.vagabond_kiem_that = True
	try:
		dung("chế độ kiểm", "kiểm thử" in _bat(lambda: m._goi("GET", "u", "t")))
	finally:
		m.frappe.flags.vagabond_kiem_that = None


@ca("v664 token người dùng hệ thống: lấy Trang và token Trang trong /me/accounts; token thấy hai Trang mà không điền mã thì báo")
def _token():
	g = _Goi({"/me/accounts": {"data": [{"id": "1", "name": "Vagabond", "access_token": "PT", "instagram_business_account": {"id": "IG", "username": "vgb"}}]}})
	with um.patch.object(m, "_thu_goi", g), um.patch.object(m, "_goi", g):
		t = m._trang_cua_token("U", "")
	la("Trang", (t["id"], t["token"], t["ig"]["id"]), ("1", "PT", "IG"))
	g2 = _Goi({"/me/accounts": {"data": [{"id": "1"}, {"id": "2"}]}})
	with um.patch.object(m, "_thu_goi", g2), um.patch.object(m, "_goi", g2):
		dung("hai Trang", "2 Trang" in _bat(lambda: m._trang_cua_token("U", "")))


# ------------------------------------------------------------ Kho bản thảo

def _docx(*doan):
	nd = io.BytesIO()
	xml = ('<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' +
		"".join("<w:p>%s</w:p>" % d for d in doan) + "</w:body></w:document>")
	with zipfile.ZipFile(nd, "w") as z:
		z.writestr("word/document.xml", xml)
	return nd.getvalue()


@ca("v664 Word: lấy chữ từng đoạn, ghép nhiều mẩu trong một đoạn, ngắt dòng, bỏ dòng trống thừa; tệp hỏng trả None")
def _word():
	nd = _docx("<w:r><w:t>Cheesecake </w:t></w:r><w:r><w:t>trái mọng</w:t></w:r>", "", "", "",
		"<w:r><w:t>Dòng 1</w:t><w:br/><w:t>Dòng 2</w:t></w:r>")
	la("chữ", x.chu_docx(nd), "Cheesecake trái mọng\n\nDòng 1\nDòng 2")
	la("hỏng", x.chu_docx(b"khong phai docx"), None)
	la("tên tệp", x.ten_tep_sach("Bai_dang_Giang_sinh.docx"), "Bai dang Giang sinh")


@ca("v664 Excel có dòng tiêu đề cột (không dấu, viết hoa): Nội dung bắt buộc; Tiêu đề, Ngày, Giờ, Kênh điền sẵn; giờ đã qua bỏ; dòng trống bỏ")
def _excel():
	hang = [["Lịch nội dung tháng 12"], ["NGAY", "Gio", "Kenh", "Tieu de", "Noi dung"],
		[dt.datetime(2026, 12, 1), dt.time(7, 30), "Facebook, IG", "Bánh khúc cây", "Bánh khúc cây sô cô la"],
		["17/11/2026", "19h", "threads", "", "Matcha"], [None, None, None, None, None],
		["15/11/2026", "08:00", "", "", "Hôm qua"], ["", "", "zalo oa", "", "Không ngày"]]
	r = x.ban_thao_tu_bang(hang, BAY_GIO)
	la("bốn bản thảo", [(z["y_chinh"], z["tieu_de"], z["hen_luc"], z["kenh"]) for z in r], [
		("Bánh khúc cây sô cô la", "Bánh khúc cây", "2026-12-01 07:30:00", ["fb", "ig"]),
		("Matcha", "", "2026-11-17 19:00:00", ["th"]),
		("Hôm qua", "", "", []),
		("Không ngày", "", "", ["zl"])])


@ca("v664 Excel không có dòng tiêu đề cột: mỗi dòng gộp các ô có chữ thành nội dung, không đoán ngày")
def _excel_tron():
	r = x.ban_thao_tu_bang([["Ý 1", "thêm"], ["", None], [3, "Ý 2"]], BAY_GIO)
	la("hai bản", [(z["y_chinh"], z["hen_luc"]) for z in r], [("Ý 1\nthêm", ""), ("3\nÝ 2", "")])


@ca("v664 ngày giờ gõ tay: 17/11/2026 07:30, 2026-11-17T07:30, ngày kiểu Excel kèm giờ; ngày sai, thiếu giờ thì trống")
def _ngay():
	la("dd/mm/yyyy giờ", x.doc_ngay_gio("17/11/2026 07:30"), "2026-11-17 07:30:00")
	la("iso", x.doc_ngay_gio("2026-11-17T07:30"), "2026-11-17 07:30:00")
	la("ngày Excel có giờ", x.doc_ngay_gio(dt.datetime(2026, 11, 17, 8, 15)), "2026-11-17 08:15:00")
	la("ngày Excel + ô giờ", x.doc_ngay_gio(dt.date(2026, 11, 17), "7h"), "2026-11-17 07:00:00")
	la("thiếu giờ", x.doc_ngay_gio("17/11/2026"), "")
	la("ngày sai", x.doc_ngay_gio("31/02/2026 07:00"), "")
	la("kênh gõ tay", (x.doc_kenh_chu("Face + Insta"), x.doc_kenh_chu("tất cả")), (["fb", "ig"], []))


class _Tep(object):
	def __init__(self, ten, nd):
		self.name = "F1"
		self.file_name = ten
		self.nd = nd
		self.da_xoa = 0
		self.flags = type("F", (), {})()

	def get_content(self):
		return self.nd

	def delete(self, **k):
		self.da_xoa += 1


def _nhap(tep, con=True, chu_tep="mkt@x"):
	tao = []

	class _Moi(object):
		def __init__(self, d):
			self.__dict__.update(d)
			self.flags = type("F", (), {})()

		def insert(self, **k):
			self.name = "BD-%d" % (len(tao) + 1)
			tao.append(self)

	def get_doc(a, b=None):
		if isinstance(a, dict):
			return _Moi(a)
		return tep
	f = type("R", (), {"name": "F1", "owner": chu_tep})()
	with um.patch.object(x, "_kiem_soan", lambda: None), um.patch.object(x, "_bay_gio", lambda: BAY_GIO), \
			um.patch.object(x.frappe.db, "get_value", lambda *a, **k: f, create=True), \
			um.patch.object(x.frappe.db, "sql", lambda *a, **k: [["F1"]] if con else [], create=True), \
			um.patch.object(x.frappe, "get_doc", get_doc, create=True), \
			um.patch.object(x.frappe, "session", type("S", (), {"user": "mkt@x"})(), create=True):
		ra = x.nhap_tep(file_url="/private/files/a")
	return ra, tao


@ca("v664 nhập tệp: Word thành một bản thảo Nháp chưa hẹn giờ đủ kênh, tệp gốc xoá; tệp đã nhập (bấm hai lần) thì báo; tệp lạ, tệp của người khác từ chối")
def _nhap_tep():
	tep = _Tep("Giang_sinh.docx", _docx("<w:r><w:t>Bánh khúc cây</w:t></w:r>"))
	ra, tao = _nhap(tep)
	la("một bản", (ra["so"], tao[0].trang_thai, tao[0].hen_luc, tao[0].kenh_chon, tao[0].y_chinh, tao[0].tieu_de),
		(1, x.TT_NHAP, None, "fb,ig,th,zl", "Bánh khúc cây", "Giang sinh"))
	la("xoá tệp gốc", tep.da_xoa, 1)
	nem("lần hai: tệp đã nhập", lambda: _nhap(tep, con=False))
	nem("tệp lạ", lambda: _nhap(_Tep("a.pdf", b"x")))
	nem("tệp người khác", lambda: _nhap(_Tep("a.txt", b"x"), chu_tep="khac@x"))
	nem("tệp rỗng", lambda: _nhap(_Tep("a.txt", b"   ")))
	ra2, tao2 = _nhap(_Tep("ghi chu.txt", "Ý tưởng tuần sau".encode("utf-8")))
	la("tệp chữ", (ra2["so"], tao2[0].y_chinh), (1, "Ý tưởng tuần sau"))


@ca("v664 nhập Excel thật (openpyxl, có trên máy chủ): mỗi dòng một bản thảo, bản có giờ hẹn đếm riêng")
def _nhap_xlsx():
	try:
		import openpyxl
	except ImportError:
		dung("CI không có openpyxl: phần đọc bảng đã kiểm ở ca ban_thao_tu_bang", True)
		return
	wb = openpyxl.Workbook()
	ws = wb.active
	for h in (["Ngày", "Giờ", "Nội dung"], [dt.datetime(2026, 12, 1), "07:30", "A"], ["", "", "B"]):
		ws.append(h)
	nd = io.BytesIO()
	wb.save(nd)
	ra, tao = _nhap(_Tep("lich.xlsx", nd.getvalue()))
	la("hai bản, một có giờ", (ra["so"], ra["hen"], [t.y_chinh for t in tao], tao[0].hen_luc), (2, 1, ["A", "B"], "2026-12-01 07:30:00"))


@ca("v664 Codex #576: Excel có dòng trống xen giữa vẫn đọc tới hết; quá 200 bản thảo thì từ chối rõ, không cắt im lặng")
def _excel_trong():
	hang = [["Nội dung"], ["A"]] + [[None, ""]] * 210 + [["B"]]
	la("bỏ dòng trống, giữ B", [h[0] for h in x.hang_co_chu(iter(hang))], ["Nội dung", "A", "B"])
	nhieu = [["Nội dung"]] + [["Ý %d" % i] for i in range(300)]
	la("dừng khi đã quá trần", len(x.hang_co_chu(iter(nhieu))), x.TOI_DA_NHAP + 6)
	try:
		import openpyxl
	except ImportError:
		dung("CI không có openpyxl: phần bỏ dòng trống đã kiểm ở trên", True)
		return
	wb = openpyxl.Workbook()
	ws = wb.active
	ws["A1"] = "Nội dung"
	ws["A2"] = "A"
	ws["A213"] = "B"
	nd = io.BytesIO()
	wb.save(nd)
	ra, tao = _nhap(_Tep("lich.xlsx", nd.getvalue()))
	la("hai bản thảo, có cả dòng 213", (ra["so"], [t.y_chinh for t in tao]), (2, ["A", "B"]))
	wb2 = openpyxl.Workbook()
	ws2 = wb2.active
	ws2.append(["Nội dung"])
	for i in range(201):
		ws2.append(["Ý %d" % i])
	nd2 = io.BytesIO()
	wb2.save(nd2)
	tep = _Tep("nhieu.xlsx", nd2.getvalue())
	nem("201 bản thảo: từ chối", lambda: _nhap(tep))
	la("tệp gốc chưa xoá khi từ chối", tep.da_xoa, 0)


def _sua_kich_thuoc(nd, ref):
	"""Ghi lại tệp xlsx với <dimension ref> khai sai (như tệp xuất từ công cụ ngoài Excel, #457)."""
	vao = zipfile.ZipFile(io.BytesIO(nd))
	ra = io.BytesIO()
	with zipfile.ZipFile(ra, "w") as z:
		for it in vao.infolist():
			du = vao.read(it.filename)
			if it.filename.startswith("xl/worksheets/sheet"):
				import re as _re
				du = _re.sub(rb'<dimension ref="[^"]*"/>', ('<dimension ref="%s"/>' % ref).encode(), du)
			z.writestr(it, du)
	return ra.getvalue()


@ca("v664 Codex #576 vòng 2 (bài học #457): tệp Excel khai kích thước sheet nhỏ hơn bảng thật vẫn đọc đủ dòng")
def _excel_kich_thuoc():
	try:
		import openpyxl
	except ImportError:
		src = _doc("vagabond/bai_dang.py")
		dung("CI không có openpyxl: _hang_xlsx còn gọi reset_dimensions", "ws.reset_dimensions()" in src.split("def _hang_xlsx(")[1].split("\ndef ")[0])
		return
	wb = openpyxl.Workbook()
	ws = wb.active
	ws["A1"] = "Nội dung"
	ws["A2"] = "A"
	ws["A40"] = "B"
	nd = io.BytesIO()
	wb.save(nd)
	sai = _sua_kich_thuoc(nd.getvalue(), "A1:A2")
	ra, tao = _nhap(_Tep("lich.xlsx", sai))
	la("đủ hai bản thảo dù sheet khai A1:A2", (ra["so"], [t.y_chinh for t in tao]), (2, ["A", "B"]))


@ca("v664 bài học #301: xếp lượt đăng SAU commit, lỗi khi xếp nằm trong callback được bọc, không làm hỏng lời gọi")
def _xep_sau_commit():
	cb = []

	class _Sau(object):
		def add(self, f):
			cb.append(f)
	loi = []

	def _enq(*a, **k):
		raise RuntimeError("redis chết")
	with um.patch.object(x.frappe.db, "after_commit", _Sau(), create=True), um.patch.object(x.frappe, "enqueue", _enq, create=True), \
			um.patch.object(x.frappe, "log_error", lambda *a, **k: loi.append(a), create=True), \
			um.patch.object(x.frappe, "get_traceback", lambda: "tb", create=True):
		x._xep_dang("BD-1")
		la("chưa xếp trước commit", (len(cb), loi), (1, []))
		cb[0]()
	la("lỗi xếp được ghi, không ném ra", len(loi), 1)


def _jpeg_xoay():
	from PIL import Image
	im = Image.new("RGB", (200, 100), (200, 30, 30))
	ex = Image.Exif()
	ex[0x0112] = 6
	nd = io.BytesIO()
	im.save(nd, "JPEG", exif=ex)
	return nd.getvalue()


@ca("v664 Codex #576: ảnh điện thoại có EXIF xoay 90 độ: xoay đúng chiều trước khi cắt và tính khung (ảnh 200x100 xoay thành 100x200)")
def _exif():
	try:
		from PIL import Image
	except ImportError:
		dung("CI không có Pillow", True)
		return
	nd = _jpeg_xoay()
	with um.patch.object(m, "_noi_dung_anh", lambda url: nd):
		la("không cắt: đứng", Image.open(io.BytesIO(m.anh_jpeg("/f/1.jpg"))).size, (100, 200))
		la("cắt 4:5 theo chiều đã xoay", Image.open(io.BytesIO(m.anh_jpeg("/f/1.jpg", "4:5"))).size, (100, 125))
	tep = type("F", (), {"get_content": lambda self: nd, "content_hash": "h"})()
	with um.patch.object(x.frappe.db, "get_value", lambda *a, **k: "F1", create=True), \
			um.patch.object(x.frappe, "get_doc", lambda *a, **k: tep, create=True):
		do = x._do_anh("/f/1.jpg")
	la("khung khi gắn ảnh tính theo chiều đã xoay", (do["rong"], do["cao"], x.doc_khung(do["rong"], do["cao"])), (100, 200, "1:2"))  # v668: 1:2 là khung 2 ảnh dọc của Facebook


# ------------------------------------------------------------ nối

@ca("v664 nối: ô token trên Cài đặt lõi (Password), chip trạng thái, nhịp gia hạn Threads, trạng thái Đang đăng trên doctype, màn có màu Đang đăng")
def _noi():
	cd = json.loads(_doc("vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json"))
	o = {f["fieldname"]: f for f in cd["fields"]}
	la("ô", [o[k]["fieldtype"] for k in ("sec_mxh", "mxh_token", "mxh_page_id", "th_token", "th_het_han", "th_gia_han_luc")],
		["Section Break", "Password", "Data", "Password", "Date", "Datetime"])
	dung("ô có trong thứ tự", all(k in cd["field_order"] for k in ("sec_mxh", "mxh_token", "th_token")))
	ch = _doc("vagabond/public/js/cai_dat_loi_chung.js")
	dung("chip", "muc: 'sec_mxh'" in ch and "can: ['mxh_token']" in ch and "can: ['th_token']" in ch)
	from vagabond import hooks
	dung("nhịp gia hạn", "vagabond.mxh.gia_han_threads" in hooks.scheduler_events["cron"]["17 3 * * *"])
	kn = json.loads(_doc("vagabond/vagabond/doctype/vagabond_bai_dang_kenh/vagabond_bai_dang_kenh.json"))
	tt = [f for f in kn["fields"] if f["fieldname"] == "trang_thai"][0]["options"].split("\n")
	dung("Đang đăng", x.K_DANG in tt and all(k in kn["field_order"] for k in ("tu_dong", "ma_bai", "loi")))
	js = _doc("vagabond/public/js/bep/75-bai-dang.js")
	dung("màu Đang đăng", "'Đang đăng': {" in js)
	dung("không dấu gạch dài", not any(c in js + _doc("vagabond/mxh.py") + _doc("vagabond/bai_dang.py") for c in ("–", "—")))
	dung("không in token ra nhật ký", "giau_khoa" in _doc("vagabond/mxh.py"))
