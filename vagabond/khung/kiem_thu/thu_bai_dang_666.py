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


# ---------------------------------------------------------------- v666 phần 2
# Sổ chủ đề, thẻ, sao, chân bài (CTA), AI theo giọng văn Vagabond, gửi giám đốc duyệt
# (anh Việt 17/11/2026: phương án A; Marketing vẫn tự duyệt; giám đốc duyệt thì báo Zalo).

import contextlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _tep(t):
	with open(os.path.join(GOC, t), encoding="utf-8") as f:
		return f.read()


@contextlib.contextmanager
def _ut():
	"""Bản giả frappe.utils của khung thiếu get_fullname, get_url: thêm tạm trong ca."""
	import sys
	ut = sys.modules["frappe.utils"]
	with um.patch.object(ut, "get_fullname", lambda u: "Tên " + str(u), create=True), \
			um.patch.object(ut, "get_url", lambda p="": "https://site" + p, create=True):
		yield


def _chay6(doc, ham, gd=False, chu_de=("CD-001",), **k):
	"""t4._chay cộng: vai giám đốc, chủ đề có thật, ghi lại tin báo giám đốc."""
	bao = []
	with contextlib.ExitStack() as st:
		st.enter_context(_ut())
		st.enter_context(um.patch.object(x, "_la_gd", lambda: gd))
		st.enter_context(um.patch.object(x, "_bao_gd", lambda d, viec, them="": bao.append((viec, them))))
		st.enter_context(um.patch.object(x.frappe.db, "exists", lambda dt, ma=None: ma in chu_de, create=True))
		st.enter_context(um.patch.object(x, "_chu_de_mot", lambda ma: {"ma": ma, "ten": "Bánh ổ", "bt": "🎂", "cta": ["A"]} if ma else None))
		ra, n = t4._chay(doc, ham, **k)
	n["bao_gd"] = bao
	return ra, n


@ca("v666 thẻ và chân bài thuần: thẻ chuẩn hoá không trùng; chân bài thêm, đổi, gỡ đúng dòng, chạy lại không đổi, dòng tự gõ trùng không lặp")
def _thuan_cta():
	la("thẻ", x.chuan_the("#PeachRuby, mille  #ruby;#peachruby"), ["peachruby", "mille", "ruby"])
	la("thẻ lưu", x.chu_the("a #b"), "#a #b")
	la("thẻ trống", (x.chuan_the(""), x.chu_the(None)), ([], ""))
	la("CTA bỏ trống, trùng, gạch dài", x.chuan_cta("A\n\n  B  \nA\nC — D"), ["A", "B", "C - D"])
	a = x.gan_chan_bai("Thân.\n\nĐoạn 2", [], ["A", "B"])
	la("thêm cách một dòng trống", a, "Thân.\n\nĐoạn 2\n\nA\nB")
	b = x.gan_chan_bai(a, ["A", "B"], ["B", "C"])
	la("đổi: gỡ A, giữ B, thêm C nối liền", b, "Thân.\n\nĐoạn 2\n\nB\nC")
	la("chạy lại không đổi", x.gan_chan_bai(b, ["B", "C"], ["B", "C"]), b)
	la("gỡ hết", x.gan_chan_bai(b, ["B", "C"], []), "Thân.\n\nĐoạn 2")
	la("ô trống", x.gan_chan_bai("", [], ["A"]), "A")
	la("dòng tự gõ đúng như CTA thì không lặp", x.gan_chan_bai("Thân\nA", [], ["A"]), "Thân\nA")
	la("câu vẫn tích giữ nguyên chỗ người soạn đã đặt", x.gan_chan_bai("Mở\nA\nThân", ["A"], ["A", "B"]), "Mở\nA\nThân\n\nB")
	la("AI: gắn chân bài từng kênh", x.gan_chan_ai({"fb": {"chu": "F"}, "th": {"chu": "T\n\nA"}}, "A"),
		{"fb": {"chu": "F\n\nA"}, "th": {"chu": "T\n\nA"}})


@ca("v666 AI soạn: câu gửi có chủ đề, chân bài (chừa chỗ) và yêu cầu cách viết bọc thẻ; lời dặn có giọng văn Vagabond sau luật của app, cấm bịa trích dẫn")
def _ai():
	c = x.cau_hoi_ai("Croissant", ["fb", "th"], x.KIEU_BAI, 2, "Giới thiệu bánh nướng", ["🛒 Đặt online"], "giọng khoa học")
	dung("chủ đề", "Chủ đề (sổ bản thảo): Giới thiệu bánh nướng." in c)
	dung("chân bài bọc thẻ, có độ dài", "<chan_bai>\n🛒 Đặt online\n</chan_bai>" in c and "dài 14 ký tự" in c)
	dung("yêu cầu bọc thẻ", "<muon_ai_viet>\ngiọng khoa học\n</muon_ai_viet>" in c)
	dung("ý chính vẫn cuối", c.rstrip().endswith("</y_chinh>"))
	dung("không chủ đề, không chân bài: như cũ", "chan_bai" not in x.cau_hoi_ai("A", ["fb"]) and "Chủ đề" not in x.cau_hoi_ai("A", ["fb"]))
	g = x._giong_van()
	dung("tệp giọng văn đi kèm mã", "Chekhov" in g and "J." in g and "—" not in g)
	ld = x.loi_dan_ai(g)
	dung("luật app đứng trước giọng văn", ld.index("CHỈ VIẾT THEO Ý CHÍNH") < ld.index("GIỌNG VĂN THE VAGABOND"))
	dung("cấm bịa trích dẫn", "Không\n  bịa trích dẫn" in x.LOI_DAN_AI or "bịa trích dẫn" in x.LOI_DAN_AI)
	la("không đọc được tệp: chỉ luật app", x.loi_dan_ai(""), x.LOI_DAN_AI)


@ca("v666 tự lưu: chủ đề phải có thật; thẻ chuẩn hoá; đổi chân bài đổi luôn chữ mọi kênh đã chọn (kể cả kênh chưa có chữ), một nguồn ở máy chủ")
def _luu6():
	doc = t4._Bai(chan_bai="", kenh_chon="fb,ig,th")
	doc.kenh = [t4._Dong(ma_kenh="fb", chu="Bánh fb", trang_thai=x.K_CHUA)]
	ra, n = _chay6(doc, x.luu, ma=doc.name, ban_luu=3, thay=json.dumps({"chan_bai": ["A", "B"], "the_bai": "#X, y", "chu_de": "CD-001"}))
	la("chữ ba kênh có chân bài", [(r.ma_kenh, r.chu) for r in doc.kenh], [("fb", "Bánh fb\n\nA\nB"), ("ig", "A\nB"), ("th", "A\nB")])
	la("lưu chân bài, thẻ, chủ đề", (doc.chan_bai, doc.the_bai, doc.chu_de), ("A\nB", "#x #y", "CD-001"))
	la("màn nhận", (ra["bai"]["chan_bai"], ra["bai"]["the"], ra["bai"]["chu_de"]["ma"]), (["A", "B"], ["x", "y"], "CD-001"))
	_chay6(doc, x.luu, ma=doc.name, ban_luu=4, thay=json.dumps({"chan_bai": ["B"]}))
	la("bỏ tích A: gỡ A ở mọi kênh", [r.chu for r in doc.kenh], ["Bánh fb\n\nB", "B", "B"])
	doc2 = t4._Bai(chan_bai="B", kenh_chon="fb")
	doc2.kenh = [t4._Dong(ma_kenh="fb", chu="F\n\nB", trang_thai=x.K_CHUA)]
	_chay6(doc2, x.luu, ma=doc2.name, ban_luu=3, thay=json.dumps({"kenh_chon": ["fb", "th"]}))
	la("thêm kênh chưa có chữ: điền sẵn chân bài", [(r.ma_kenh, r.chu) for r in doc2.kenh], [("fb", "F\n\nB"), ("th", "B")])
	nem("chủ đề không có thật", lambda: _chay6(t4._Bai(), x.luu, ma="BD", ban_luu=3, thay=json.dumps({"chu_de": "CD-999"})), Exception)


@ca("v666 gửi giám đốc duyệt: bài vào Chờ duyệt có cờ chờ giám đốc, ghi người gửi; bài trống chữ chặn; bấm hai lần không đổi gì")
def _gui_gd():
	doc = t4._Bai(ly_do_tra="cũ")
	ra, n = _chay6(doc, x.gui_giam_doc, ma=doc.name, ban_luu=3)
	la("trạng thái", (doc.trang_thai, doc.cho_giam_doc, doc.nguoi_gui_gd, doc.ly_do_tra), (x.TT_CHO, 1, "mkt@x", ""))
	la("màn thấy chờ giám đốc", bool(ra["bai"]["cho_gd"]), True)
	_, n2 = _chay6(doc, x.gui_giam_doc, ma=doc.name, ban_luu=4)
	la("bấm lần hai: không lưu", n2["luu"], [])
	trong = t4._Bai(y_chinh="", kenh=[t4._Dong(ma_kenh="fb", chu="  ", trang_thai=x.K_CHUA)])
	nem("chưa có chữ", lambda: _chay6(trong, x.gui_giam_doc, ma="BD", ban_luu=3), Exception)
	_, n3 = _chay6(t4._Bai(), x.gui_giam_doc, ma="BD", ban_luu=9)
	la("số lần lưu cũ: không ghi", n3["luu"], [])


@ca("v666 giám đốc: đồng ý nội dung về Nháp và báo Zalo; trả lại phải có góp ý, báo kèm góp ý; người không phải giám đốc bị chặn; bài không còn chờ thì không đổi")
def _gd():
	doc = t4._Bai(trang_thai=x.TT_CHO, cho_giam_doc=1)
	nem("không phải giám đốc", lambda: _chay6(doc, x.gd_dong_y, gd=False, ma=doc.name, ban_luu=3), Exception)
	ra, n = _chay6(doc, x.gd_dong_y, gd=True, ma=doc.name, ban_luu=3)
	la("về Nháp, thôi chờ, ghi lúc đồng ý", (doc.trang_thai, doc.cho_giam_doc, bool(doc.gd_dong_y_luc)), (x.TT_NHAP, 0, True))
	la("báo nội dung", n["bao_gd"], [("noi_dung", "")])
	_, n2 = _chay6(doc, x.gd_dong_y, gd=True, ma=doc.name, ban_luu=4)
	la("bấm lần hai: không báo lại", (n2["bao_gd"], n2["luu"]), ([], []))
	doc = t4._Bai(trang_thai=x.TT_CHO, cho_giam_doc=1)
	nem("trả lại thiếu góp ý", lambda: _chay6(doc, x.gd_tra_lai, gd=True, ma=doc.name, ban_luu=3, ly_do="  "), Exception)
	_, n = _chay6(doc, x.gd_tra_lai, gd=True, ma=doc.name, ban_luu=3, ly_do="Đoạn đầu — dài")
	la("trả lại", (doc.trang_thai, doc.cho_giam_doc, doc.ly_do_tra), (x.TT_NHAP, 0, "Đoạn đầu - dài"))
	la("báo kèm góp ý", n["bao_gd"], [("tra", "Đoạn đầu - dài")])
	td, dong = x.tin_giam_doc("tra", "Bánh ổ", "Anh Việt", "Ngắn lại")
	dung("tin trả lại nói việc cần làm", td.startswith("Giám đốc trả lại bài đăng") and "Góp ý: Ngắn lại" in dong)


@ca("v666 Duyệt bài đang chờ giám đốc: giám đốc duyệt thì báo Zalo; Marketing tự duyệt vẫn được, thôi chờ giám đốc, không báo")
def _duyet_gd():
	doc = t4._Bai(trang_thai=x.TT_CHO, cho_giam_doc=1, ly_do_tra="cũ")
	_, n = _chay6(doc, x.duyet, gd=True, noi={"fb"}, ma=doc.name, ban_luu=3)
	la("thôi chờ, xoá góp ý cũ", (doc.cho_giam_doc, doc.ly_do_tra), (0, ""))
	la("báo giám đốc đã duyệt", [v for v, _ in n["bao_gd"]], ["duyet"])
	doc = t4._Bai(trang_thai=x.TT_CHO, cho_giam_doc=1)
	_, n = _chay6(doc, x.duyet, gd=False, noi={"fb"}, ma=doc.name, ban_luu=3)
	la("Marketing tự duyệt: không báo", (doc.cho_giam_doc, n["bao_gd"], bool(n["xep"])), (0, [], True))


@ca("v666 gắn sao: đổi cờ sao, không tăng số lần lưu (màn đang sửa không bị báo xung đột); bấm lại cùng giá trị không lưu")
def _sao():
	doc = t4._Bai(gan_sao=0)
	ra, n = _chay6(doc, x.gan_sao, ma=doc.name, sao=1)
	la("sao", (ra, doc.gan_sao, doc.ban_luu, len(n["luu"])), ({"ma": doc.name, "sao": 1}, 1, 3, 1))
	_, n = _chay6(doc, x.gan_sao, ma=doc.name, sao=1)
	la("bấm lại không lưu", n["luu"], [])


@ca("v666 Kho bản thảo lọc chủ đề, sao, chưa chủ đề, thẻ ngay trong câu đọc trước LIMIT 200")
def _loc_bt():
	cau = []

	def sql(q, gt=None, as_dict=False):
		cau.append((q, gt))
		return []
	with um.patch.object(x.frappe.db, "sql", sql, create=True), _ut():
		for cd, the in (("*", ""), ("-", ""), ("CD-001", "#Mille"), ("", "")):
			x._ban_thao(cd, the)
	dung("sao", "b.gan_sao = 1" in cau[0][0])
	dung("chưa chủ đề", "b.chu_de is null" in cau[1][0])
	q, gt = cau[2]
	dung("chủ đề và thẻ là tham số", "b.chu_de = %s" in q and gt[-2:] == ("CD-001", "% #mille %"))
	for q, _ in cau:
		dung("lọc đứng trước limit", q.index("where") < q.index("limit 200"))
	la("tất cả: chỉ hai điều kiện gốc", cau[3][1], (x.TT_SUA_DUOC,))


@ca("v666 Việc cần làm: giám đốc thấy bài chờ mình (lọc trong câu đọc), Marketing thấy bài bị trả lại; loại bai_dang nằm trong việc hệ trọng của giám đốc")
def _viec():
	loc = []

	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=None):
		loc.append(filters)
		return [type("R", (), {"name": "BD-1", "tieu_de": "Bánh", "nguoi_gui_gd": "", "gui_gd_luc": "2026-11-17 10:00", "ly_do_tra": "Ngắn lại", "modified": "2026-11-17"})()]
	import sys
	vtd = type(sys)("vagabond.viec_tu_dong")
	vtd.dong_viec = lambda loai, ma, nhom, phu, ngay, qua_han: {"loai": loai, "ma": ma, "nhom": nhom, "phu": phu, "ngay": ngay, "tt": "cho_lam"}
	with um.patch.object(x.frappe, "get_all", get_all, create=True), _ut(), um.patch.dict(sys.modules, {"vagabond.viec_tu_dong": vtd}):
		gd = x.viec({"Giám đốc"})
		mk = x.viec({"Marketing"})
		kho = x.viec({"Stock User"})
	la("giám đốc", [(v["loai"], v["ma"], v["tt"]) for v in gd], [("bai_dang", "BD-1", "cho_duyet")])
	la("lọc trong câu đọc", loc[0], {"trang_thai": x.TT_CHO, "cho_giam_doc": 1})
	la("Marketing: bài bị trả", [(v["loai"], v["tt"]) for v in mk], [("bai_dang", "ban_nhap")])
	dung("Marketing thấy góp ý", "Ngắn lại" in mk[0]["phu"])
	la("kho không thấy", kho, [])
	from vagabond import viec_can_lam as v
	dung("việc hệ trọng của giám đốc", "bai_dang" in v.VIEC_HE_TRONG)
	dung("giám đốc, AP giám đốc, Marketing thấy; kho không", v.thay_duoc("bai_dang", {"Giám đốc"}) and v.thay_duoc("bai_dang", {"AP Giám đốc"})
		and v.thay_duoc("bai_dang", {"Marketing"}) and not v.thay_duoc("bai_dang", {"Stock User"}))
	dung("có chip loại", any(k == "bai_dang" for k, _, _ in v.LOAI_PHIEU))
	js = _tep("vagabond/public/js/bep/02-trang-chu.js")
	dung("Việc cần làm mở thẳng bài", "if (l === 'bai_dang') return go(function () { return scrBaiDangSoan(x.ma); });" in js)


@ca("v666 cấu trúc: trường mới của bài, doctype chủ đề chỉ sửa qua app, tin Zalo mới có ở máy chủ và Cài đặt, bản vá gieo chủ đề trước dòng đồng bộ")
def _cau_truc():
	bd = json.loads(_tep("vagabond/vagabond/doctype/vagabond_bai_dang/vagabond_bai_dang.json"))
	ten = [f["fieldname"] for f in bd["fields"]]
	for f in ("chu_de", "the_bai", "gan_sao", "chan_bai", "cho_giam_doc", "nguoi_gui_gd", "gui_gd_luc", "gd_dong_y_luc", "ly_do_tra", "yeu_cau_ai"):
		dung("trường " + f, f in ten and f in bd["field_order"])
	dung("mốc modified mới", bd["modified"] >= "2026-11-17")
	cd = json.loads(_tep("vagabond/vagabond/doctype/vagabond_chu_de_bai/vagabond_chu_de_bai.json"))
	la("chủ đề", (cd["name"], [f["fieldname"] for f in cd["fields"]]), ("Vagabond Chu De Bai", ["ten", "bieu_tuong", "thu_tu", "cta"]))
	dung("tên không trùng", [f for f in cd["fields"] if f["fieldname"] == "ten"][0].get("unique") == 1)
	dung("chặn sửa ngoài app", "vgb_bai_dang" in _tep("vagabond/vagabond/doctype/vagabond_chu_de_bai/vagabond_chu_de_bai.py"))
	dung("tin máy chủ", '"mkt_bai_gd_duyet": ("Marketing",' in _tep("vagabond/kenh_zalo.py"))
	dung("tin trong Cài đặt", "mkt_bai_gd_duyet:" in _tep("vagabond/public/js/cai_dat_loi_chung.js"))
	from vagabond.patches import v666_so_chu_de_bai as p
	la("tích tin cho nhóm đang nhận tin bài chờ duyệt", p.tin_them("mkt_banh_cho_anh, mkt_bai_cho_duyet"), "mkt_banh_cho_anh, mkt_bai_cho_duyet, mkt_bai_gd_duyet")
	la("chạy lại, nhóm khác, nhóm nhận tất cả: không đổi", (p.tin_them("mkt_bai_cho_duyet, mkt_bai_gd_duyet"), p.tin_them("hd_dau_vao"), p.tin_them("")), (None, None, None))
	pt = _tep("vagabond/patches.txt").split("[post_model_sync]")[1]
	dung("bản vá trước dòng đồng bộ v666", pt.index("vagabond.patches.v666_so_chu_de_bai") < pt.index("dong_bo_cau_truc #v666"))
	la("mười hai chủ đề gieo, bốn câu chân bài", (len(x.CHU_DE_GIEO), len(x.CTA_GIEO)), (12, 4))
