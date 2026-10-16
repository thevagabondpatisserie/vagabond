"""Codex #484 (4bbf027), hai finding P2 trên biên nhận và chính sách Vue.

F1 (www/web_moi/xong.py:27, chinh_sach.py): chân trang Vue in nguyên đường dẫn
   chính sách của trang cũ (/chinh-sach-bao-mat...), khách bấm là rời luồng Vue
   thử. Tái hiện trên 4bbf027: href="/chinh-sach-bao-mat". Sau sửa: /web_moi/...
F2 (www/web_moi/xong.py:24): nút "Nhắn Zalo", "Nhắn Messenger" gõ cứng, Marketing
   sửa nhãn bien_nhan_ed312c8e3 / bien_nhan_edbd31524 trong Editor thì trang cũ
   đổi, Vue không. Tái hiện: nhãn đã sửa "Chat Zalo nhé" mà Vue vẫn "Nhắn Zalo".

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
	nd = D(khoa_tu_duong=noi_dung_web.khoa_tu_duong, chinh_sach_dang_hien=lambda: [dict(x) for x in CS],
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
