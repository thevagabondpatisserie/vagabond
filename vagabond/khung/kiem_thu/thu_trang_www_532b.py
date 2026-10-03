"""Trang www có Jinja phải có mô đun Python đúng tên Frappe tìm (v532b).

Đo trên site thật 27/09/2026: /dat-ban và /thanh-vien trả thẻ csrf-token
mang nguyên văn chữ "{{ csrf_token }}". Tức là get_context của hai trang
CHƯA TỪNG chạy: Frappe (website/page_renderers/template_page.py,
set_pymodule) đổi gạch nối thành gạch dưới khi tìm mô đun, nên trang
dat-ban.html cần dat_ban.py, còn repo đặt dat-ban.py. Cùng lỗi v529 đã sửa
cho /bien-tap-web.

v532 (PR #376) đưa chữ đặt bàn vào get_context của đúng tệp đó; Codex bắt
ở vòng 1 và #376 đã đổi dat-ban.py thành dat_ban.py. v532b đổi nốt
thanh-vien.py. Không đổi tên thì trang đặt bàn hiện nguyên văn
"{{ nhan.dat_ban_tieu_de | e }}" cho khách. Bộ ca này DỰNG TRANG như Frappe dựng: tìm mô đun theo luật
gạch dưới, gọi get_context, rồi thay biến trong mẫu theo đúng cách Frappe
làm với DebugUndefined: biến thiếu in ra NGUYÊN VĂN chứ không rỗng.

Máy CI tay không, không có jinja2, nên ca dùng bộ thay biến nhỏ `_render`
chỉ hiểu đúng hai dạng hai trang này dùng: {{ ten }} và {{ a.b | e }}.
Mẫu có dạng khác (thẻ {% %}, lọc khác) thì ca báo hỏng thay vì đoán.
"""

import html as _html
import importlib.util
import io
import os
import re
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WWW = os.path.join(GOC, "vagabond", "www")


class _Ctx(dict):
	"""Giống frappe._dict thật: gán thuộc tính là gán khoá. (Bộ frappe giả
	của tầng khung giữ thuộc tính riêng, render sẽ không thấy biến.)"""
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


def _mo_dun_frappe_tim(html):
	"""Đường mô đun Frappe tìm cho một trang www: cùng thư mục, tên tệp bỏ
	đuôi .html, gạch nối thành gạch dưới (set_pymodule)."""
	thu_muc, ten = os.path.split(html)
	return os.path.join(thu_muc, os.path.splitext(ten)[0].replace("-", "_") + ".py")


_BIEN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\s*(\|\s*e\s*)?\}\}")


class _MauLa(Exception):
	pass


def _render(mau, ctx):
	"""Thay biến như Jinja của Frappe (DebugUndefined, không tự thoát): biến
	có thì in, `| e` thì thoát HTML, biến thiếu thì giữ nguyên văn."""
	if "{%" in mau:
		raise _MauLa("mẫu có thẻ {% %}, bộ thay biến của ca không hỗ trợ")

	def thay(m):
		ten, loc = m.group(1), m.group(2)
		gia = ctx
		for phan in ten.split("."):
			if not isinstance(gia, dict) or phan not in gia:
				return m.group(0)
			gia = gia[phan]
		chu = "" if gia is None else str(gia)
		return _html.escape(chu, quote=True) if loc else chu
	ra = _BIEN.sub(thay, mau)
	sot = [x for x in re.findall(r"\{\{[^}]*\}\}", mau) if not _BIEN.fullmatch(x)]
	if sot:
		raise _MauLa("mẫu có biến dạng lạ: %s" % sot[:3])
	return ra


def _trang_co_jinja():
	ra = []
	for goc, _thu_muc, tep in os.walk(WWW):
		for t in tep:
			if t.endswith(".html"):
				p = os.path.join(goc, t)
				with io.open(p, encoding="utf-8") as f:
					nd = f.read()
				if "{{" in nd or "{%" in nd:
					ra.append(p)
	return sorted(ra)


def _dung_trang(ten_html):
	"""Dựng trang như Frappe: tìm mô đun theo luật, có thì gọi get_context,
	thay biến trong mẫu. Trả (html, đã_tìm_thấy_mô_đun)."""
	import frappe
	html = os.path.join(WWW, ten_html)
	py = _mo_dun_frappe_tim(html)
	ctx = {}
	co = os.path.exists(py)
	if co:
		spec = importlib.util.spec_from_file_location("trang_www_thu_" + os.path.basename(py)[:-3], py)
		md = importlib.util.module_from_spec(spec)
		phien = types.SimpleNamespace(get_csrf_token=lambda: "MA-CSRF-THU")
		with patch.object(frappe, "sessions", phien, create=True):
			spec.loader.exec_module(md)
			context = _Ctx()
			md.get_context(context)
		ctx = dict(context)
	with io.open(html, encoding="utf-8") as f:
		mau = f.read()
	return _render(mau, ctx), co


@ca("v532b mọi trang www có Jinja đều có mô đun đúng tên Frappe tìm (gạch nối thành gạch dưới), không còn .py gạch nối")
def _ten_mo_dun():
	ds = _trang_co_jinja()
	dung("có trang để kiểm", len(ds) >= 5)
	for html in ds:
		la("%s có mô đun" % os.path.relpath(html, WWW), os.path.exists(_mo_dun_frappe_tim(html)), True)
	for goc, _thu_muc, tep in os.walk(WWW):
		for t in tep:
			if t.endswith(".py") and t != "__init__.py":
				dung("%s không có gạch nối" % t, "-" not in t)


@ca("v532b dựng /dat-ban như Frappe: get_context chạy, có mã CSRF, chữ đặt bàn ra đúng, không còn {{ nguyên văn")
def _dat_ban():
	from vagabond import noi_dung_web
	with patch.object(noi_dung_web, "nhan_cong_khai", return_value=noi_dung_web.nhan_day_du({})):
		ra, co = _dung_trang("dat-ban.html")
	dung("tìm thấy mô đun", co)
	dung("không còn {{", "{{" not in ra)
	dung("thẻ csrf có mã", 'content="MA-CSRF-THU"' in ra)
	for khoa in ("dat_ban_nhan", "dat_ban_tieu_de", "dat_ban_mo_ta", "dat_ban_nut", "dat_ban_ho_tro"):
		dung("chữ %s hiện ra" % khoa, noi_dung_web.NHAN[khoa]["mac_dinh"] in ra)


@ca("v532b dựng /dat-ban: chữ marketing sửa có ký tự HTML thì được thoát, không chèn thẻ vào trang")
def _dat_ban_thoat():
	from vagabond import noi_dung_web
	nhan = noi_dung_web.nhan_day_du({})
	nhan["dat_ban_tieu_de"] = '<img src=x onerror="alert(1)">'
	with patch.object(noi_dung_web, "nhan_cong_khai", return_value=nhan):
		ra, _co = _dung_trang("dat-ban.html")
	dung("không có thẻ img chèn vào", "<img src=x" not in ra)
	dung("hiện dạng đã thoát", "&lt;img src=x" in ra)


@ca("v532b bộ thay biến của ca giống Jinja: biến thiếu giữ nguyên văn, | e thoát HTML, dạng lạ thì báo")
def _render_giong_jinja():
	la("biến thiếu", _render("<b>{{ a.b | e }}</b>", {}), "<b>{{ a.b | e }}</b>")
	la("có biến", _render("{{ x }}", {"x": "<i>"}), "<i>")
	la("thoát", _render("{{ a.b | e }}", {"a": {"b": '<"&>'}}), "&lt;&quot;&amp;&gt;")
	for mau in ("{% if x %}1{% endif %}", "{{ x | safe }}"):
		try:
			_render(mau, {})
			ket = "không báo"
		except _MauLa:
			ket = "báo"
		la("dạng lạ %r" % mau, ket, "báo")


@ca("v532b dựng /thanh-vien như Frappe: get_context chạy, thẻ csrf có mã, không còn {{ nguyên văn")
def _thanh_vien():
	ra, co = _dung_trang("thanh-vien.html")
	dung("tìm thấy mô đun", co)
	dung("không còn {{", "{{" not in ra)
	dung("thẻ csrf có mã", 'content="MA-CSRF-THU"' in ra)


@ca("v532b nút thêm nhanh trên trang đặt bánh: vùng bấm ít nhất 44x44 (AGENTS.md điều 13), vòng kính 40px vẽ bằng ::before")
def _nut_them_44():
	# Codex #376 (db188239): v532 thu nút .c-them còn 40x40, vùng bấm duy nhất
	# của nút thêm nhanh ở cả bánh lẫn hàng mùa. CSS không chạy được ở tầng
	# khung nên chốt bằng đọc luật CSS của đúng lớp đó.
	with io.open(os.path.join(GOC, "vagabond", "trang", "banh.html"), encoding="utf-8") as f:
		trang = f.read()
	m = re.search(r"\.c-them\{([^}]*)\}", trang)
	dung("có luật .c-them", bool(m))
	kieu = m.group(1) if m else ""
	for thuoc in ("width", "height", "min-width", "min-height"):
		v = re.search(r"(?:^|;)" + thuoc + r":(\d+(?:\.\d+)?)px", kieu)
		dung("%s ít nhất 44px" % thuoc, bool(v) and float(v.group(1)) >= 44)
	dung("không có luật .c-them nào khác thu nhỏ lại", len(re.findall(r"\.c-them\{", trang)) == 1)
	vong = re.search(r"\.c-them::before\{([^}]*)\}", trang)
	dung("vòng kính vẽ ở ::before, cách mép 2px", bool(vong) and "inset:2px" in vong.group(1))
	dung("hai nơi dựng nút đều dùng lớp c-them", trang.replace('\\"', '"').count('class="c-them"') >= 2)
