"""Codex #484, finding P2 trên biên nhận và chính sách Vue (vòng 2 trên 4bbf027, vòng 3 trên 9fe9ccf).

F1 (www/web_moi/xong.py:27, chinh_sach.py): chân trang Vue in nguyên đường dẫn
   chính sách của trang cũ (/chinh-sach-bao-mat...), khách bấm là rời luồng Vue
   thử. Tái hiện trên 4bbf027: href="/chinh-sach-bao-mat". Sau sửa: /web_moi/...
F2 (www/web_moi/xong.py:24): nút "Nhắn Zalo", "Nhắn Messenger" gõ cứng, Marketing
   sửa nhãn bien_nhan_ed312c8e3 / bien_nhan_edbd31524 trong Editor thì trang cũ
   đổi, Vue không. Tái hiện: nhãn đã sửa "Chat Zalo nhé" mà Vue vẫn "Nhắn Zalo".

F3 (trang/app.js:61, vòng 3): cách nhận, thanh toán (cả phí giao, tổng) hiện câu máy
   chủ trả, không qua nhãn Editor như _chu_bien_nhan của trang cũ.
F4 (chinh_sach.py:17, vòng 3): "Tiếng Việt", "English" gõ cứng, trang cũ đọc nhãn
   ngon_ngu_vn / ngon_ngu_en.
Rà thêm cùng lượt (anh Việt: gom sửa một lần): trang biên nhận Vue khi không còn
   token (bốn nhãn bien_nhan_fae8f9966, _37a6f269e, _bbd687e19, _6be58a5f5), tiêu đề
   tab bien_nhan_8d4e8c5d8, và nút "Gọi" mà trang cũ có. Phần chạy trên trình duyệt
   kiểm bằng Chromium ở cong_cu/kiem_web_vue_dom.cjs ca F37.

Ca kiểm gọi get_context THẬT của hai trang, chỉ thay tầng Frappe và nguồn dữ liệu.
"""
import json
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

CS = [{"khoa": "chinh_sach_bao_mat", "ten": "Bảo mật", "duong": "/chinh-sach-bao-mat"},
	{"khoa": "dieu_khoan", "ten": "Điều khoản", "duong": "/dieu-khoan"},
	{"khoa": "la", "ten": "Lạ", "duong": "https://ngoai.example/x"}]
LH = {"zalo": "https://zalo.me/1", "messenger": "https://m.me/2"}


def _xong(nhan):
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach, web_vue
	from vagabond.www.banh.xong import TIEU_DE
	fr = D(local=D(response_headers={}), sessions=D(get_csrf_token=lambda: "c"),
		form_dict={"token": "T"}, PageDoesNotExistError=ValueError)
	dw = D(PHAP_NHAN={"ten": "X"}, lien_he=lambda: dict(LH), pixel_id=lambda: "",
		bien_nhan_theo_token=lambda t: {"ma": "DW-1"})
	nd = D(chinh_sach_dang_hien=lambda: [dict(c) for c in CS], cong_khai=lambda: {"nhan": nhan})
	g = {"frappe": fr, "don_web": dw, "trang_khach": trang_khach, "noi_dung_web": nd,
		"TIEU_DE": TIEU_DE, "web_vue": web_vue}
	c = nap("www/web_moi/xong.py", "get_context", g)(D())
	return c, json.loads(c.du_lieu.replace("\\u003c", "<"))


def _href_chan_trang(html):
	m = re.search(r'<nav class="ct-chinh-sach".*?</nav>', html)
	return re.findall(r'href="([^"]+)"', m.group(0)) if m else []


@ca("Codex #484 F1: chân trang biên nhận Vue giữ chính sách trong /web_moi, bỏ đường ngoài")
def _():
	c, _d = _xong({})
	la("đường chính sách", _href_chan_trang(c.chan_trang), ["/web_moi/chinh-sach-bao-mat", "/web_moi/dieu-khoan"])


@ca("Codex #484 F1: chân trang trang chính sách Vue cũng giữ trong /web_moi")
def _():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach, noi_dung_web, web_vue
	fr = D(local=D(request=D(path="/web_moi/dieu-khoan")), form_dict={},
		sessions=D(get_csrf_token=lambda: "c"), PageDoesNotExistError=ValueError)
	nd = D(khoa_tu_duong=noi_dung_web.khoa_tu_duong, chinh_sach_dang_hien=lambda: [dict(x) for x in CS], nhan_cong_khai=lambda: {},
		trang_chinh_sach=lambda k, n: {"ten": "Điều khoản", "html": "<p>x</p>", "ngon_ngu": "vn", "co_en": False})
	g = dict(frappe=fr, noi_dung_web=nd, web_vue=web_vue, don_web=D(PHAP_NHAN={}, lien_he=lambda: {}), trang_khach=trang_khach)
	c = nap("www/web_moi/chinh_sach.py", "get_context", g)(D())
	la("đường chính sách", _href_chan_trang(c.chan_trang), ["/web_moi/chinh-sach-bao-mat", "/web_moi/dieu-khoan"])


@ca("Codex #484 F2: nút Zalo, Messenger biên nhận Vue đọc nhãn Editor, trống thì chữ mặc định")
def _():
	_c, d = _xong({"bien_nhan_ed312c8e3": "Chat Zalo nhé", "bien_nhan_edbd31524": "  "})
	la("nút", [(x["href"], x["khoa"], x["ten"]) for x in d["lien_he"]],
		[("https://zalo.me/1", "bien_nhan_ed312c8e3", "Chat Zalo nhé"),
		("https://m.me/2", "bien_nhan_edbd31524", "Nhắn Messenger")])


@ca("Codex #484 F2: trang cũ và Vue dùng chung một bảng nút liên hệ; biên nhận trang cũ in y như trước")
def _():
	from vagabond import trang_khach
	html = trang_khach.bien_nhan_html({"ma": "DW-1"}, dict(LH))
	for k, chu in (("bien_nhan_ed312c8e3", "Nhắn Zalo"), ("bien_nhan_edbd31524", "Nhắn Messenger")):
		dung("trang cũ giữ nhãn " + k, '<span data-vgb-chu="%s">%s</span>' % (k, chu) in html)
	la("bảng dùng chung", [x[1] for x in trang_khach.NUT_LIEN_HE_BIEN_NHAN], ["bien_nhan_ed312c8e3", "bien_nhan_edbd31524"])
	from pathlib import Path
	s = (Path(__file__).resolve().parents[2] / "www/web_moi/xong.py").read_text()
	dung("Vue không còn gõ cứng chữ nút", "Nhắn Zalo" not in s and "Nhắn Messenger" not in s)


@ca("Codex #484 F3: bảng câu nghiệp vụ của biên nhận Vue là đúng bảng của trang cũ, máy chủ gửi kèm cả khi không còn token")
def _():
	from vagabond import trang_khach, web_vue
	b = web_vue.bang_bien_nhan()
	la("bảng", b["gia_tri"], {k: list(v) for k, v in trang_khach.GIA_TRI_BIEN_NHAN.items()})
	la("tiền tố tự lấy", b["tien_to"], list(trang_khach.TIEN_TO_TU_LAY))
	for nhan in ({}, {"bien_nhan_tu_lay_tai": "Lấy ở"}):
		_c, d = _xong(nhan)
		la("gửi kèm bảng", d["bang"], b)
	dung("trang cũ vẫn đổi đúng nhãn", 'data-vgb-chu="bien_nhan_chuyen_khoan"' in trang_khach._chu_bien_nhan("Chuyển khoản (mã VietQR)"))


@ca("Codex #484 F4: link đổi ngôn ngữ trang chính sách Vue đọc nhãn ngon_ngu_vn, ngon_ngu_en")
def _():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach, noi_dung_web, web_vue
	for ngon, nhan, mong in (("vn", {"ngon_ngu_en": "In English"}, '?ngon_ngu=en">In English</a>'),
			("en", {"ngon_ngu_vn": "Bản tiếng Việt"}, '>Bản tiếng Việt</a>'), ("vn", {}, '>English</a>')):
		fr = D(local=D(request=D(path="/web_moi/dieu-khoan")), form_dict={"ngon_ngu": ngon},
			sessions=D(get_csrf_token=lambda: "c"), PageDoesNotExistError=ValueError)
		nd = D(khoa_tu_duong=noi_dung_web.khoa_tu_duong, chinh_sach_dang_hien=lambda: [], nhan_cong_khai=lambda n=nhan: dict(n),
			trang_chinh_sach=lambda k, n, ng=ngon: {"ten": "Điều khoản", "html": "<p>x</p>", "ngon_ngu": ng, "co_en": True})
		g = dict(frappe=fr, noi_dung_web=nd, web_vue=web_vue, don_web=D(PHAP_NHAN={}, lien_he=lambda: {}), trang_khach=trang_khach)
		c = nap("www/web_moi/chinh_sach.py", "get_context", g)(D())
		dung("ngôn ngữ %s nhãn %r" % (ngon, nhan), mong in c.doi_ngon_ngu and "/web_moi/dieu-khoan" in c.doi_ngon_ngu)


@ca("Codex #484 rà thêm: biên nhận Vue có nút Gọi như trang cũ, chỉ nhận số điện thoại hợp lệ")
def _():
	from vagabond import web_vue
	ds = web_vue.nut_lien_he_bien_nhan({"dien_thoai_so": "0931224334", "dien_thoai": "0931 224 334"}, {})
	la("nút gọi", ds, [{"href": "tel:0931224334", "khoa": "", "ten": "Gọi 0931 224 334", "lop": "phu"}])
	la("số lạ thì không có nút", web_vue.nut_lien_he_bien_nhan({"dien_thoai_so": "javascript:x"}, {}), [])
