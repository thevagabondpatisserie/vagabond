# -*- coding: utf-8 -*-
"""UI Nghệ sĩ công nghệ, PR 1 nền: công tắc ba tầng và lớp vẽ ui-b.

Điều đắt nhất ở việc này không phải màu sắc mà là ba chỗ dễ hỏng lặng lẽ:

  1. Công tắc tính sai tầng: một tài khoản thấy giao diện mới khi tiệm đang
     tắt khẩn cấp. Ca dưới chạy ĐỦ 12 tổ hợp (khẩn cấp 2 x chung 2 x riêng 3).
  2. Trạng thái của người này lọt sang người khác qua bộ nhớ đệm trang. Ở
     đây chốt phần hook (no_cache, Cache-Control); phần Frappe thật chạy ở
     bench (vagabond/khung/bench_thu/giao_dien_ui_b.py).
  3. Công tắc bị ai đó đem ra dùng trong kiểm quyền. Ca "không ai khác đọc
     công tắc" chặn mọi mô đun Python khác nhập vagabond.giao_dien.

Kèm các ca giữ cho tắt là về đúng giao diện cũ: mọi biến --ui-* dùng trong
kiểu viết thẳng trong thẻ phải có giá trị dự phòng, nhánh khung cũ còn
nguyên, và các tệp máy sinh (biểu tượng, hoạ tiết) khớp nguồn.

Toàn phép thuần, không Frappe, không requests.
"""

import io
import json
import os
import re
import subprocess
import sys

from vagabond import giao_dien as gd
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOC = os.path.dirname(GOI)
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(*duong):
	return io.open(os.path.join(*duong), encoding="utf-8").read()


def _phan():
	return dict((t, _doc(BEP, t)) for t in sorted(os.listdir(BEP)) if re.match(r"^\d\d-[a-z0-9-]+\.js$", t))


# ------------------------------------------------------------ công tắc

@ca("ui-b công tắc: đủ 12 tổ hợp ba tầng, khẩn cấp thắng riêng, riêng thắng chung")
def _():
	mong = {
		# (khẩn cấp, chung, riêng): thấy giao diện mới?
		(0, 0, gd.THEO_CHUNG): False, (0, 0, gd.LUON_BAT): True, (0, 0, gd.LUON_TAT): False,
		(0, 1, gd.THEO_CHUNG): True, (0, 1, gd.LUON_BAT): True, (0, 1, gd.LUON_TAT): False,
		(1, 0, gd.THEO_CHUNG): False, (1, 0, gd.LUON_BAT): False, (1, 0, gd.LUON_TAT): False,
		(1, 1, gd.THEO_CHUNG): False, (1, 1, gd.LUON_BAT): False, (1, 1, gd.LUON_TAT): False,
	}
	la("số tổ hợp", len(mong), 12)
	for (khan, chung, rieng), kq in sorted(mong.items()):
		la("khẩn cấp %s, chung %s, riêng %s" % (khan, chung, rieng), gd.tinh_bat(khan, chung, rieng), kq)


@ca("ui-b công tắc: ô chưa đặt, chuỗi '0', giá trị lạ không tự thành bật")
def _():
	for chua in (None, "", 0, "0", False):
		la("chung = %r" % (chua,), gd.tinh_bat(0, chua, gd.THEO_CHUNG), False)
		la("khẩn cấp = %r không chặn Luôn bật" % (chua,), gd.tinh_bat(chua, 0, gd.LUON_BAT), True)
	for bat in (1, "1", True):
		la("chung = %r" % (bat,), gd.tinh_bat(0, bat, None), True)
		la("khẩn cấp = %r" % (bat,), gd.tinh_bat(bat, 1, gd.LUON_BAT), False)
	la("riêng lạ coi là Theo chung, chung tắt", gd.tinh_bat(0, 0, "Bật luôn"), False)
	la("riêng None, chung bật", gd.tinh_bat(0, 1, None), True)


@ca("ui-b công tắc: tìm lựa chọn riêng theo email, không phân biệt hoa thường, dòng sau thắng")
def _():
	class Dong(object):
		def __init__(self, nd, lc):
			self.nguoi_dung, self.lua_chon = nd, lc
	ds = [{"nguoi_dung": "Viet@Vagabond.vn", "lua_chon": gd.LUON_BAT}, Dong("quay@vagabond.vn", gd.LUON_TAT),
		{"nguoi_dung": "la@vagabond.vn", "lua_chon": "gì đó"}, {"nguoi_dung": "hai@vagabond.vn", "lua_chon": gd.LUON_BAT},
		{"nguoi_dung": "hai@vagabond.vn", "lua_chon": gd.LUON_TAT}]
	la("khớp không phân biệt hoa thường", gd.lua_chon_cua(ds, "viet@vagabond.vn"), gd.LUON_BAT)
	la("dòng là đối tượng", gd.lua_chon_cua(ds, "quay@vagabond.vn"), gd.LUON_TAT)
	la("giá trị lạ", gd.lua_chon_cua(ds, "la@vagabond.vn"), gd.THEO_CHUNG)
	la("hai dòng, dòng sau thắng", gd.lua_chon_cua(ds, "hai@vagabond.vn"), gd.LUON_TAT)
	la("không có trong bảng", gd.lua_chon_cua(ds, "khac@vagabond.vn"), gd.THEO_CHUNG)
	la("Guest", gd.lua_chon_cua(ds, "Guest"), gd.THEO_CHUNG)
	la("bảng rỗng", gd.lua_chon_cua(None, "viet@vagabond.vn"), gd.THEO_CHUNG)
	la("không có tên", gd.lua_chon_cua(ds, ""), gd.THEO_CHUNG)


# ------------------------------------------------------ đoạn chèn đầu trang

@ca("ui-b đầu trang: bật thì gắn class trước lần vẽ đầu kèm số phiên bản; tắt thì không gắn")
def _():
	bat = gd.dau_trang_html(True, "677")
	dung("bật: có lệnh gắn class", "document.documentElement.classList.add('ui-b')" in bat)
	dung("bật: ghi số phiên bản", 'window.__VGB_UI={b:1,v:"677"}' in bat)
	dung("bật: nền giấy trước khi JS chạy", "html.ui-b,html.ui-b body{background:#F3EFE7" in bat)
	la("bật: tải sớm đúng hai tệp phông", bat.count('rel="preload"'), 2)
	dung("bật: script đứng trước mọi thứ khác", bat.startswith("<script>"))
	tat = gd.dau_trang_html(False, "677")
	dung("tắt: không gắn class", "classList" not in tat)
	dung("tắt: vẫn ghi phiên bản, b bằng 0", 'window.__VGB_UI={b:0,v:"677"}' in tat)
	dung("tắt: không tải phông, không đổi nền", "preload" not in tat and "<style>" not in tat)


@ca("ui-b đầu trang: không đọc được phiên bản thì không bật; chuỗi lạ không lọt vào thẻ script")
def _():
	for hong in ("", None, "abc", '1";alert(1);//', "12345678"):
		h = gd.dau_trang_html(True, hong)
		dung("phiên bản %r: không gắn class" % (hong,), "classList" not in h)
		dung("phiên bản %r: không lọt chuỗi lạ" % (hong,), "alert" not in h and 'v:""' in h)


@ca("ui-b đầu trang: đọc đúng số APPVER của bản đang nằm trong repo; tệp phông tải sớm có thật")
def _():
	ma = _doc(BEP, "12-van-don.js")
	that = re.search(r"var APPVER = '(\d+)'", ma).group(1)
	la("đọc từ chuỗi", gd.doc_appver(ma), that)
	la("đọc từ tệp", gd.doc_appver(), that)
	la("chuỗi không có APPVER", gd.doc_appver("var KHAC = '1';"), "")
	for p in gd.PHONG_TAI_SOM:
		dung("có tệp " + p, os.path.exists(os.path.join(GOI, "public", p.replace("/assets/vagabond/", ""))))


# ------------------------------------------------------------- hook

class _Local(object):
	def __init__(self):
		self.response_headers = {}


class _FrappeGia(object):
	def __init__(self, cai_dat=None, nguoi="Guest", no=False):
		self.local = _Local()
		self.session = type("S", (), {"user": nguoi})()
		self._cai_dat, self._no, self.da_ghi_loi = cai_dat or {}, no, 0

	def get_cached_doc(self, dt):
		if self._no:
			raise RuntimeError("đọc cài đặt hỏng")
		la("đọc đúng doctype cài đặt", dt, gd.DOCTYPE)
		return self._cai_dat

	def log_error(self, **kw):
		self.da_ghi_loi += 1


def _voi(gia, ham):
	that = gd.frappe
	gd.frappe = gia
	try:
		return ham()
	finally:
		gd.frappe = that


@ca("ui-b hook: trang khác không bị đụng; trang app tắt bộ nhớ đệm chung và cấm trình duyệt giữ lại")
def _():
	gia = _FrappeGia({"tat_khan_cap": 0, "bat_chung": 1, "rieng": []}, "quay@vagabond.vn")
	khac = {"doctype": "Web Page", "route": "banh", "head_include": "<meta x>"}
	ra = _voi(gia, lambda: gd.ngu_canh(khac))
	la("trang khác giữ nguyên", ra, {"doctype": "Web Page", "route": "banh", "head_include": "<meta x>"})
	la("trang khác không có header", gia.local.response_headers, {})
	dung("trang khác không tắt đệm", not getattr(gia.local, "no_cache", 0))
	la("không có ngữ cảnh", _voi(gia, lambda: gd.ngu_canh(None)), None)

	app = {"doctype": "Web Page", "route": "bep", "head_include": "<meta x>"}
	ra = _voi(gia, lambda: gd.ngu_canh(app))
	la("no_cache trong ngữ cảnh", ra.get("no_cache"), 1)
	la("no_cache của yêu cầu", gia.local.no_cache, 1)
	la("Cache-Control", gia.local.response_headers.get("Cache-Control"), "private, no-store")
	dung("giữ phần head có sẵn", ra["head_include"].startswith("<meta x>"))
	dung("chung bật thì gắn class", "classList.add('ui-b')" in ra["head_include"])


@ca("ui-b hook: mỗi tài khoản một trạng thái; khẩn cấp thắng; đọc cài đặt hỏng thì ra giao diện cũ")
def _():
	cd = {"tat_khan_cap": 0, "bat_chung": 0, "rieng": [{"nguoi_dung": "viet@vagabond.vn", "lua_chon": gd.LUON_BAT}]}

	def dau(nguoi, cai_dat, no=False):
		gia = _FrappeGia(cai_dat, nguoi, no)
		ra = _voi(gia, lambda: gd.ngu_canh({"doctype": "Web Page", "route": "bep"}))
		return ra, gia
	ra, _g = dau("viet@vagabond.vn", cd)
	dung("tài khoản thử thấy mới khi cả tiệm tắt", "classList.add('ui-b')" in ra["head_include"])
	ra, _g = dau("quay@vagabond.vn", cd)
	dung("tài khoản khác vẫn cũ", "classList" not in ra["head_include"] and "{b:0," in ra["head_include"])
	ra, _g = dau("Guest", cd)
	dung("chưa đăng nhập vẫn cũ", "classList" not in ra["head_include"])
	ra, _g = dau("viet@vagabond.vn", dict(cd, tat_khan_cap=1))
	dung("tắt khẩn cấp thắng Luôn bật", "classList" not in ra["head_include"])
	ra, gia = dau("viet@vagabond.vn", cd, no=True)
	dung("đọc cài đặt hỏng: giao diện cũ, trang vẫn ra", "classList" not in ra["head_include"] and "{b:0," in ra["head_include"])
	la("đọc hỏng vẫn không cho lưu đệm", ra.get("no_cache"), 1)


@ca("ui-b hook: hỏng giữa chừng thì trả nguyên ngữ cảnh, không ném lỗi ra trang")
def _():
	class NgCanhHong(dict):
		def __setitem__(self, k, v):
			raise RuntimeError("không ghi được")
	gia = _FrappeGia({"tat_khan_cap": 0, "bat_chung": 1, "rieng": []})
	ng = NgCanhHong(doctype="Web Page", route="bep")
	ra = _voi(gia, lambda: gd.ngu_canh(ng))
	dung("trả lại đúng ngữ cảnh", ra is ng)
	la("có ghi log", gia.da_ghi_loi, 1)


@ca("ui-b hook: đã nối vào update_website_context đúng một lần")
def _():
	la("số lần khai", _doc(GOI, "hooks.py").count('"vagabond.giao_dien.ngu_canh"'), 1)


# ------------------------------------------- công tắc không dính quyền

@ca("ui-b quyền: không mô đun Python nào khác đọc công tắc giao diện")
def _():
	vi_pham = []
	for goc, _thu_muc, tep in os.walk(GOI):
		if os.sep + "kiem_thu" in goc or os.sep + "bench_thu" in goc or "__pycache__" in goc:
			continue
		for t in tep:
			if not t.endswith(".py"):
				continue
			d = os.path.join(goc, t)
			if d == os.path.join(GOI, "giao_dien.py"):
				continue
			ma = _doc(d)
			if d == os.path.join(GOI, "hooks.py"):
				ma = ma.replace('"vagabond.giao_dien.ngu_canh"', "")
			if re.search(r"\bgiao_dien\b", ma) or "Vagabond Giao Dien" in ma:
				vi_pham.append(os.path.relpath(d, GOC))
	la("tệp Python khác nhắc tới công tắc", vi_pham, [])


@ca("ui-b quyền: phía app không gửi trạng thái giao diện lên máy chủ, không dùng nó cạnh kiểm vai")
def _():
	vi_pham = []
	for ten, ma in _phan().items():
		if ten == "81-ui-b.js":
			continue
		for i, dong in enumerate(ma.split("\n")):
			if "uiB" in dong and re.search(r"\bapi\(|hasRole\(|coQuyen\w*\(", dong):
				vi_pham.append("%s:%d" % (ten, i + 1))
	la("dòng trộn trạng thái giao diện với gọi máy chủ hoặc kiểm vai", vi_pham, [])
	ui = _phan()["81-ui-b.js"]
	dung("lớp vẽ không gọi máy chủ", not re.search(r"\bapi\(|\bfetch\(|XMLHttpRequest", ui))
	dung("lớp vẽ không đọc bộ nhớ máy", not re.search(r"localStorage|sessionStorage|document\.cookie", re.sub(r"/\*.*?\*/", "", ui, flags=re.S)))


# ----------------------------------------------------- doctype cài đặt

@ca("ui-b doctype: cài đặt là bản ghi đơn, chỉ quản trị hệ thống đổi được, ba lựa chọn riêng đúng chữ")
def _():
	d = os.path.join(GOI, "vagabond", "doctype")
	cha = json.loads(_doc(d, "vagabond_giao_dien", "vagabond_giao_dien.json"))
	con = json.loads(_doc(d, "vagabond_giao_dien_rieng", "vagabond_giao_dien_rieng.json"))
	la("tên doctype", cha["name"], gd.DOCTYPE)
	la("bản ghi đơn", cha.get("issingle"), 1)
	la("quyền", [(p["role"], p.get("read"), p.get("write")) for p in cha["permissions"]], [("System Manager", 1, 1)])
	o = dict((f["fieldname"], f) for f in cha["fields"])
	for ten in ("tat_khan_cap", "bat_chung"):
		la(ten + " là ô đánh dấu, mặc định tắt", (o[ten]["fieldtype"], o[ten].get("default")), ("Check", "0"))
	la("bảng riêng trỏ đúng bảng con", (o["rieng"]["fieldtype"], o["rieng"]["options"]), ("Table", con["name"]))
	la("bảng con", con.get("istable"), 1)
	oc = dict((f["fieldname"], f) for f in con["fields"])
	la("ba lựa chọn", tuple(oc["lua_chon"]["options"].split("\n")), gd.LUA_CHON)
	la("mặc định Theo chung", oc["lua_chon"]["default"], gd.THEO_CHUNG)
	la("tài khoản trỏ User", (oc["nguoi_dung"]["fieldtype"], oc["nguoi_dung"]["options"]), ("Link", "User"))


# ------------------------------------------- tắt là về đúng giao diện cũ

@ca("ui-b về cũ: biến --ui-* dùng ngoài lớp vẽ mới luôn có giá trị dự phòng là giá trị cũ")
def _():
	thieu = []
	for ten, ma in _phan().items():
		if ten == "81-ui-b.js":
			continue
		for m in re.finditer(r"var\(\s*--ui-[a-z0-9-]+\s*(,?)", ma):
			if not m.group(1):
				thieu.append("%s: %s" % (ten, ma[m.start():m.start() + 40]))
	la("biến --ui-* thiếu giá trị dự phòng", thieu, [])


@ca("ui-b về cũ: nhánh khung cũ còn nguyên, lớp vẽ mới chỉ chạy khi trang mang class ui-b")
def _():
	khung = _doc(BEP, "01-khung-app.js")
	for cu in ("""(showBack ? '<button class="ic" id="vgbBack">&#8249;</button>' :""",
			"""'<button class="ic" id="vgbHome" aria-label="Ve trang chu">&#127968;</button>'""",
			"""'<button class="ic" id="vgbAcc" aria-label="Tai khoan">&#128100;</button>'""",
			"""(opt.fab ? '<button class="fab" id="vgbFab">+</button>' : '');"""):
		dung("khung cũ còn: " + cu[:44], cu in khung)
	dung("khung mới chỉ dựng khi uiB()", "var uiDau = (typeof uiB === 'function' && uiB()) ? uiBKhungDau(title, showBack, opt) : '';" in khung)
	ui = _doc(BEP, "81-ui-b.js")
	dung("uiB đọc class trên thẻ html", "document.documentElement.classList.contains('ui-b')" in ui)
	dung("lệch phiên bản thì gỡ class trước khi vẽ", "html.classList.remove('ui-b')" in ui and "String(ui.v || '') !== String(APPVER)" in ui)
	boot = _doc(BEP, "12-van-don.js")
	a, b = boot.find("try { uiBNap(); } catch (e) { }"), boot.find("await whoAmI()")
	dung("nạp lớp vẽ trước lần vẽ đầu của app", 0 < a < b)


# --------------------------------------------- tệp máy sinh và khai báo

def _chay(*lenh):
	ra = subprocess.run([sys.executable, "-B"] + list(lenh), capture_output=True, cwd=GOC)
	return ra.returncode, (ra.stdout + ra.stderr).decode("utf-8", "replace")[-600:]


@ca("ui-b tệp sinh: khối biểu tượng, bảng đối chiếu và bốn hoạ tiết khớp nguồn")
def _():
	ma, ra = _chay("cong_cu/ui_b/sinh_bieu_tuong.py", "--kiem")
	dung("biểu tượng khớp nguồn: " + ra, ma == 0)
	ma, ra = _chay("cong_cu/ui_b/sinh_hoa_tiet.py", "--kiem")
	dung("hoạ tiết khớp bản gốc design system: " + ra, ma == 0)


@ca("ui-b khai báo: màu, cỡ chữ, bo góc, khoảng cách, phông của lớp vẽ mới đúng bộ chuẩn")
def _():
	ma, ra = _chay("cong_cu/ui_b/kiem_khai_bao.py")
	dung("kiểm khai báo: " + ra, ma == 0)


@ca("ui-b khai báo: phép kiểm bắt được màu lạ, cỡ chữ lạ, khoảng lẻ, bo góc trần, bộ chọn lọt ra ngoài")
def _():
	import importlib.util
	spec = importlib.util.spec_from_file_location("kiem_khai_bao", os.path.join(GOC, "cong_cu", "ui_b", "kiem_khai_bao.py"))
	k = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(k)
	la("khai báo sạch", k.kiem("html.ui-b .a{color:#121619;font-size:15px;padding:12px 16px;border-radius:var(--ui-r-24);margin:var(--ui-moon-inset)}"), [])
	for xau, ten in (("html.ui-b .a{color:#ff00aa}", "màu lạ"), ("html.ui-b .a{background:rgba(1,2,3,.5)}", "màu rgba lạ"),
			("html.ui-b .a{font-size:14px}", "cỡ chữ lạ"), ("html.ui-b .a{padding:10px}", "khoảng lẻ"),
			("html.ui-b .a{border-radius:12px}", "bo góc trần"), (".a{color:#121619}", "bộ chọn ngoài ui-b"),
			("html.ui-b .a{font-family:Arial}", "phông lạ"),
			("@media (min-width:900px){html.ui-b .a{margin-top:6px}}", "khoảng lẻ trong @media")):
		dung("phải bắt " + ten, len(k.kiem(xau)) == 1)


@ca("ui-b tài nguyên: mọi tệp phông và hoạ tiết lớp vẽ trỏ tới đều có trong repo; biểu tượng khung có nét")
def _():
	ui = _doc(BEP, "81-ui-b.js")
	phong = sorted(os.listdir(os.path.join(GOI, "public", "fonts", "ui")))
	can = ["be-vietnam-pro-%s-%d-normal.woff2" % (b, w) for b in ("latin", "vietnamese") for w in (400, 500, 600, 700)] + ["doto-latin-800-normal.woff2"]
	la("tệp phông", [p for p in phong if p.endswith(".woff2")], sorted(can))
	for h in re.findall(r"UIB_HOA = \[([^\]]+)\]", ui)[0].replace("'", "").split(","):
		dung("có hoạ tiết " + h.strip(), os.path.exists(os.path.join(GOI, "public", "images", "ui", "hoa-tiet-%s.svg" % h.strip())))
	for ten in re.findall(r"uiBSvg\('([a-z0-9-]+)'", "\n".join(_phan().values())):
		dung("biểu tượng %s có nét" % ten, ('"%s": "' % ten) in ui)
	dung("Doto chỉ nhận chữ số và dấu của số", "unicode-range:U+0020,U+0025,U+002B-002E,U+0030-0039,U+2212" in ui)


# ------------------------------- Codex #599 vòng 1: cổng kiểm không được xanh khi chưa kiểm đủ

def _nap(ten):
	import importlib.util
	spec = importlib.util.spec_from_file_location(ten, os.path.join(GOC, "cong_cu", "ui_b", ten + ".py"))
	m = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(m)
	return m


@ca("ui-b so chế độ tắt (Codex #599): máy chụp trả lỗi, thiếu ảnh hay thừa ảnh thì không được kết luận giống nhau")
def _():
	s = _nap("so_che_do_tat")
	mong = ["a__tat__390x844__chromium.png", "b__tat__390x844__chromium.png"]
	la("đủ ảnh, hai lượt trả 0, không khác", s.ket_luan(0, 0, mong, mong, mong, []), [])
	# Đúng tình huống Codex dựng: cả hai lượt chụp trả 1 nhưng còn một cặp ảnh giống nhau.
	dung("hai lượt chụp trả 1 mà còn một cặp ảnh giống nhau: phải chặn", len(s.ket_luan(1, 1, mong[:1], mong[:1], mong[:1], [])) == 2)
	dung("lượt gốc trả 1: chặn", s.ket_luan(1, 0, mong, mong, mong, []) != [])
	dung("lượt mới trả 1: chặn", s.ket_luan(0, 1, mong, mong, mong, []) != [])
	dung("bản mới thiếu một màn: chặn", s.ket_luan(0, 0, mong, mong[:1], mong, []) != [])
	dung("bản gốc thiếu một màn: chặn", s.ket_luan(0, 0, mong[:1], mong, mong, []) != [])
	dung("ảnh cũ còn sót trong thư mục (thừa so với mong đợi): chặn", s.ket_luan(0, 0, mong + ["cu.png"], mong + ["cu.png"], mong, []) != [])
	dung("không có ảnh mong đợi nào: chặn", s.ket_luan(0, 0, [], [], [], []) != [])
	dung("có ảnh khác: chặn", s.ket_luan(0, 0, mong, mong, mong, [("a", "3 điểm ảnh")]) != [])
	la("tên ảnh mong đợi đọc từ bảng kết quả", s.anh_mong_doi([{"man": "a", "che_do": "tat", "khung": "390x844", "may": "chromium"}]), mong[:1])
	ma = _doc(GOC, "cong_cu", "ui_b", "so_che_do_tat.py")
	dung("dọn thư mục đầu ra trước khi chụp", "shutil.rmtree(os.path.join(ra, ten), ignore_errors=True)" in ma)


@ca("ui-b máy chụp (Codex #599): không còn tuỳ chọn cỡ chữ giả; gõ sai tên màn thì trượt, không chạy 0 ô rồi báo xong")
def _():
	chup = os.path.join(GOC, "cong_cu", "ui_b", "chup.cjs")

	def node(*them):
		r = subprocess.run(["node", chup] + list(them), capture_output=True, cwd=GOC)
		return r.returncode, r.stdout.decode("utf-8", "replace")
	ma, ra = node("--co-chu", "200", "--man", "trang-chu")
	la("--co-chu bị từ chối", ma, 1)
	dung("nói rõ lý do và cách thay", "KHÔNG HỖ TRỢ --co-chu" in ra and "683x384" in ra)
	ma, ra = node("--man", "man-khong-co")
	la("tên màn lạ: mã 1", ma, 1)
	dung("nêu tên màn lạ", "man-khong-co" in ra)
	ma, ra = node("--man", "trang-chu", "--khung", "to")
	la("khung sai dạng: mã 1", ma, 1)
	nguon = _doc(chup)
	dung("không còn đổi cỡ chữ gốc của trang", "html{font-size:" not in nguon)
	dung("không ô nào được chụp thì trượt", "KHÔNG có ô nào được chụp" in nguon)


@ca("ui-b khai báo (Codex #599, cùng loại): chuỗi CSS rỗng không được coi là đạt")
def _():
	k = _nap("kiem_khai_bao")
	dung("CSS rỗng: có lỗi", len(k.kiem("")) == 1)
	dung("chỉ có @font-face: có lỗi", len(k.kiem("@font-face{font-family:X}")) == 1)
	dung("có danh sách luật khung chung phải có", "html.ui-b .vh" in k.PHAI_CO and "html.ui-b .gt" in k.PHAI_CO)
