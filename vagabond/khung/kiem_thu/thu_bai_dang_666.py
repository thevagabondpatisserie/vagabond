# -*- coding: utf-8 -*-
"""v666 Bài đăng: Zalo OA tự đăng thành Bài viết, nút Đăng ngay (anh Việt 17/11/2026).

Ca chốt:
  - thân Bài viết Zalo OA: ảnh đầu làm ảnh bìa, chữ chia đoạn, mô tả gọn 300 ký tự,
    tiêu đề 150; thiếu ảnh hay thiếu tiêu đề báo việc cần làm;
  - câu lỗi Zalo theo mã: -212 chưa duyệt Article API, token hỏng, lỗi khác giữ câu Zalo;
  - chuỗi gọi Zalo: tạo bài (bước công bố) rồi hỏi mã bài tới khi có; mất mạng lúc tạo là
    "chưa rõ"; tạo xong mà xác nhận lỗi cũng "chưa rõ" (không tự đăng lại);
  - kết nối Zalo OA: đủ cấu hình và Zalo cho đọc danh sách bài thì nối; -212 thì chưa nối
    kèm cách sửa;
  - lượt đăng truyền tiêu đề Zalo OA của bài;
  - Đăng ngay: bỏ giờ hẹn TRƯỚC khi kiểm, giờ hẹn đã qua không chặn, kênh đã nối xếp
    lượt ngay; còn điều cần để ý thì trả bài với giờ hẹn cũ (không lưu, không mất giờ);
    lỗi đỏ khác vẫn chặn.
"""

import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import bai_dang as x  # noqa: E402
from vagabond import mxh as m  # noqa: E402
from vagabond.khung.kiem_thu import thu_bai_dang_664 as t4  # noqa: E402


@ca("v666 thân Bài viết Zalo OA: ảnh bìa là ảnh đầu, chữ chia đoạn rồi tới ảnh, mô tả 300 ký tự, tiêu đề 150")
def _than():
	b = m.than_bai_zalo("  Bánh   mới  ", "Đoạn một\ndòng hai\n\n\nĐoạn hai", ["u1", "", "u2"])
	la("ảnh bìa", b["cover"], {"cover_type": "photo", "photo_url": "u1", "status": "show"})
	la("tiêu đề gọn khoảng trắng", b["title"], "Bánh mới")
	la("thân", b["body"], [{"type": "text", "content": "Đoạn một\ndòng hai"}, {"type": "text", "content": "Đoạn hai"},
		{"type": "image", "url": "u1"}, {"type": "image", "url": "u2"}])
	la("mô tả là đoạn đầu", b["description"], "Đoạn một dòng hai")
	la("công khai, cho bình luận, bài thường", (b["status"], b["comment"], b["type"]), ("show", "show", "normal"))
	dai = m.than_bai_zalo("x" * 200, "y" * 400, ["u"])
	la("trần tiêu đề, mô tả", (len(dai["title"]), len(dai["description"]), dai["description"][-1]), (150, 300, "…"))
	la("không chữ thì mô tả là tiêu đề, thân chỉ có ảnh", (m.than_bai_zalo("T", "", ["u"])["description"],
		m.than_bai_zalo("T", "", ["u"])["body"]), ("T", [{"type": "image", "url": "u"}]))
	nem("thiếu ảnh", lambda: m.than_bai_zalo("T", "c", []), m.LoiDang)
	nem("thiếu tiêu đề", lambda: m.than_bai_zalo("  ", "c", ["u"]), m.LoiDang)


@ca("v666 câu lỗi Zalo: -212 nói Nộp xét duyệt Article API; token hỏng nói cấp lại quyền; lỗi khác giữ câu Zalo")
def _loi():
	dung("-212", "Nộp xét duyệt" in m.loi_zalo_de_hieu({"error": -212, "message": "App has not register this api"}))
	dung("token", "hết hạn" in m.loi_zalo_de_hieu({"error": "-216"}))
	c = m.loi_zalo_de_hieu({"error": -201, "message": "Title is invalid"})
	dung("lỗi khác giữ mã và câu", "-201" in c and "Title is invalid" in c)
	dung("thân lạ không vỡ", "mã 0" in m.loi_zalo_de_hieu(None))


class _Tra(object):
	def __init__(self, j, ma=200):
		self.status_code = ma
		self._j = j
		self.content = b"x"

	def json(self):
		return self._j


def _zl(goi_mang, cfg=None):
	"""Chạy dang_zl với mạng giả. goi_mang(phuong_thuc, url, than) trả _Tra hoặc ném."""
	nhat = []

	def req(pt, url, params=None, timeout=None, headers=None, data=None):
		import json as js
		than = js.loads(data.decode("utf-8")) if data else None
		nhat.append((pt, url.rsplit("/", 1)[-1], than, headers.get("access_token")))
		return goi_mang(pt, url, than)
	c = cfg if cfg is not None else {"zalo_app_id": "1", "zalo_app_secret": "s", "zalo_refresh_token": "r"}
	with um.patch.object(m, "_cfg", lambda: c), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
			um.patch.object(m, "_zl_token", lambda c: "TOK"), um.patch.object(m, "anh_jpeg", lambda u, k=None, t=None: b"jpg:" + u.encode()), \
			um.patch.object(m, "url_cong_khai", lambda ma, nd: "https://pub/" + nd.decode()[4:]), \
			um.patch.object(m, "requests", type("R", (), {"request": staticmethod(req)})), \
			um.patch.object(m.time, "sleep", lambda s: None), \
			um.patch.object(m.frappe, "log_error", lambda *a, **k: None, create=True), \
			um.patch.object(m.frappe, "flags", type("F", (), {"get": lambda self, k, d=None: None})(), create=True):
		try:
			ra = m.dang_zl("BD-1", "Tiêu đề", "Chữ", [{"url": "/f/1.jpg", "khung": "16:9", "cat": 1}, {"url": "/f/2.jpg"}])
		except m.LoiDang as e:
			ra = e
	return ra, nhat


@ca("v666 đăng Zalo OA: tạo bài với ảnh công khai và mã OA, hỏi mã bài tới khi có; mất mạng lúc tạo hay xác nhận lỗi là chưa rõ")
def _dang_zl():
	lan = {"v": 0}

	def mang(pt, url, than):
		if url.endswith("create"):
			return _Tra({"error": 0, "data": {"token": "T1"}})
		lan["v"] += 1
		return _Tra({"error": 0, "data": {} if lan["v"] < 3 else {"id": "A9"}})
	ra, n = _zl(mang)
	la("kết quả", ra, ("A9", ""))
	la("chuỗi gọi", [(g[0], g[1]) for g in n], [("POST", "create"), ("POST", "verify"), ("POST", "verify"), ("POST", "verify")])
	la("ảnh bìa là ảnh đầu đã công khai", n[0][2]["cover"]["photo_url"], "https://pub//f/1.jpg")
	la("hỏi bằng mã tiến trình, gửi mã OA", (n[1][2], n[0][3]), ({"token": "T1"}, "TOK"))

	def dut(pt, url, than):
		raise IOError("mất mạng")
	ra, _ = _zl(dut)
	dung("mất mạng lúc tạo: chưa rõ", isinstance(ra, m.LoiDang) and ra.ro is False)

	def xac_nhan_hong(pt, url, than):
		if url.endswith("create"):
			return _Tra({"error": 0, "data": {"token": "T1"}})
		return _Tra({"error": -201, "message": "x"})
	ra, n = _zl(xac_nhan_hong)
	dung("xác nhận lỗi sau khi tạo: chưa rõ, không tạo lại", isinstance(ra, m.LoiDang) and ra.ro is False and [g[1] for g in n].count("create") == 1)

	def tu_choi(pt, url, than):
		return _Tra({"error": -212, "message": "App has not register this api"})
	ra, _ = _zl(tu_choi)
	dung("chưa duyệt API: rõ ràng, nói cách sửa", isinstance(ra, m.LoiDang) and ra.ro and "Nộp xét duyệt" in ra.chu)
	ra, n = _zl(mang, cfg={})
	dung("thiếu cấu hình: không gọi Zalo", isinstance(ra, m.LoiDang) and not n)


@ca("v666 kết nối Zalo OA: đọc được danh sách bài thì nối; -212 thì chưa nối kèm cách sửa; thiếu cấu hình thì chưa nối")
def _ket_noi():
	def chay(tra, cfg):
		with um.patch.object(m, "_cfg", lambda: cfg), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
				um.patch.object(m, "_zl_token", lambda c: "TOK"), um.patch.object(m, "_goi_zl", tra), \
				um.patch.object(m.frappe, "cache", lambda: type("C", (), {"get_value": lambda s, k: None, "set_value": lambda s, *a, **k: None})(), create=True):
			return m.trang_thai(lam_moi=True)["zl"]
	du = {"zalo_app_id": "1", "zalo_app_secret": "s", "zalo_refresh_token": "r"}
	la("nối", chay(lambda *a, **k: {"error": 0}, du)["ok"], 1)

	def hong(*a, **k):
		raise m.LoiDang(m.loi_zalo_de_hieu({"error": -212}))
	z = chay(hong, du)
	dung("-212 chưa nối, nói cách sửa", z["ok"] == 0 and "Nộp xét duyệt" in z["chu"])
	la("thiếu cấu hình", chay(lambda *a, **k: {"error": 0}, {})["ok"], 0)


@ca("v666 lượt đăng gửi tiêu đề Zalo OA của bài cho kênh Zalo OA")
def _tieu_de():
	doc = t4._da_duyet(kenh_chon="fb,zl")
	doc.kenh = [t4._Dong(ma_kenh="fb", chu="Bánh fb", trang_thai=x.K_HEN, tu_dong=1),
		t4._Dong(ma_kenh="zl", chu="Bánh zl", tieu_de="Tiêu đề OA", trang_thai=x.K_HEN, tu_dong=1)]
	_, n = t4._chay(doc, x.dang_bai, noi={"fb", "zl"}, ma=doc.name)
	la("tiêu đề theo kênh", n["tieu_de"], [("fb", ""), ("zl", "Tiêu đề OA")])
	la("hai kênh lên", t4._tt(doc), [("fb", x.K_XONG), ("zl", x.K_XONG)])


@ca("v666 Đăng ngay: bài hẹn giờ đã qua vẫn đăng, bỏ giờ hẹn, kênh đã nối xếp lượt ngay; lỗi đỏ khác vẫn chặn")
def _dang_ngay():
	doc = t4._Bai(hen_luc="2026-11-16 19:00:00")
	nem("Duyệt thường: giờ hẹn đã qua chặn", lambda: t4._chay(doc, x.duyet, noi={"fb"}, ma=doc.name, ban_luu=3), Exception)
	doc = t4._Bai(hen_luc="2026-11-16 19:00:00")
	_, n = t4._chay(doc, x.duyet, noi={"fb", "ig"}, ma=doc.name, ban_luu=3, dang_ngay=1)
	la("bỏ giờ hẹn", doc.hen_luc, None)
	la("kênh", t4._tt(doc), [("fb", x.K_HEN), ("ig", x.K_HEN), ("th", x.K_TAY)])
	la("xếp lượt ngay", n["xep"], [doc.name])
	doc = t4._Bai(hen_luc="2026-11-17 08:00:00")
	_, n = t4._chay(doc, x.duyet, noi={"fb"}, ma=doc.name, ban_luu=3, dang_ngay=1)
	la("giờ hẹn còn tới mà bấm Đăng ngay: vẫn đăng ngay", (doc.hen_luc, n["xep"]), (None, [doc.name]))
	doc = t4._Bai(hen_luc="2026-11-17 08:00:00", anh=[])
	nem("thiếu ảnh vẫn chặn", lambda: t4._chay(doc, x.duyet, noi={"fb"}, ma=doc.name, ban_luu=3, dang_ngay=1), Exception)


@ca("v666 Đăng ngay mà còn điều cần để ý: chưa lưu, trả bài giữ giờ hẹn cũ để bấm Thôi không mất giờ")
def _dang_ngay_nhac():
	doc = t4._Bai(hen_luc="2026-11-17 08:00:00",
		anh=[t4._Dong(name="a1", idx=1, file_url="/f/1.jpg", rong=1080, cao=1080, khung="1:1"),
			t4._Dong(name="a2", idx=2, file_url="/f/2.jpg", rong=1080, cao=1350, khung="4:5")])
	ra, n = t4._chay(doc, x.duyet, noi={"fb"}, ma=doc.name, ban_luu=3, dang_ngay=1)
	dung("hỏi điều cần để ý", bool(ra.get("can_doc_nhac")))
	la("không lưu, không xếp", (n["luu"], n["xep"]), ([], []))
	la("giờ hẹn giữ nguyên trên bài và trên màn", (str(doc.hen_luc), ra["bai"]["hen_luc"]), ("2026-11-17 08:00:00", "2026-11-17 08:00"))
	ra, n = t4._chay(doc, x.duyet, noi={"fb"}, ma=doc.name, ban_luu=3, dang_ngay=1, da_doc_nhac=1)
	la("đã đọc: đăng ngay", (doc.hen_luc, n["xep"]), (None, [doc.name]))
