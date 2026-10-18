"""v601 (anh Việt 17/10/2026): chuyển trang đặt bánh /banh sang bản Vue.

Không đổi đường dẫn khách đang dùng và không xoá Web Page "banh" cũ. Hook
`page_renderer` của Frappe hỏi bộ dựng `trang_banh_vue.TrangBanhVue` trước mọi
bộ dựng sẵn: công tắc Cài đặt "Dùng trang đặt bánh bản mới" bật thì nó dựng
www/web_moi/banh.html ngay tại /banh, tắt thì từ chối để Frappe dựng trang cũ.
Quay lại không cần deploy.

Ca kiểm chạy THẬT lớp TrangBanhVue với tầng Frappe giả (không có site), và
hàm thuần dung_ban_vue với đủ các nhánh.
"""
import ast
import importlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]


@ca("v601/v603 tráo Vue: chỉ /banh và biên nhận /banh/xong, chỉ khi công tắc bật; ?ban=cu giữ trang cũ, Editor xem trước theo công tắc")
def _():
	from vagabond.web_vue import dung_ban_vue
	for duong, bat, q, mong in (
		("banh", 1, {}, True), ("/banh/", "1", {}, True), ("banh", 0, {}, False), ("banh", None, {}, False),
		("banh", "x", {}, False), ("web_moi/banh", 1, {}, False), ("banh/xong", 1, {}, True), ("banh/xong", 0, {}, False),
		("banh/xong", 1, {"ban": "cu"}, False), ("chinh-sach", 1, {}, False), ("banh/xong/T", 1, {}, False),
		# v603: Editor xem trước đi theo công tắc (trước v603 là False).
		("dat-ban", 1, {}, False), ("banh", 1, {"bien_tap": "1"}, True), ("banh", 0, {"bien_tap": "1"}, False), ("banh", 1, {"bien_tap": "0"}, True),
		("banh", 1, {"ban": "cu"}, False), ("banh", 1, {"ban": "CU "}, False), ("banh", 1, {"ban": "vue"}, True)):
		la("%r bat=%r %r" % (duong, bat, q), dung_ban_vue(duong, bat, q), mong)


def _nap_lop(gia_tri_cong_tac, form=None, loi=False, co_tep=True):
	"""Nạp trang_banh_vue với Frappe giả, trả lớp TrangBanhVue."""
	class TemplatePageGia:
		def __init__(self, path=None, http_status_code=None):
			TAO.append(path)
			self.path = str(path or "").strip("/ ")
			self.http_status_code = http_status_code or 200

		def can_render(self):
			return co_tep and self.path in ("web_moi/banh", "web_moi/xong")

	def doc(dt, truong, cache=False):
		DOC.append(truong)
		if loi:
			raise RuntimeError("chưa migrate")
		assert (dt, truong) == ("Vagabond Settings", "web_ban_vue")
		return gia_tri_cong_tac

	DOC = []
	TAO.clear()
	fr = types.SimpleNamespace(db=types.SimpleNamespace(get_single_value=doc), form_dict=form or {})
	tp = types.ModuleType("frappe.website.page_renderers.template_page")
	tp.TemplatePage = TemplatePageGia
	mods = {"frappe.website": types.ModuleType("frappe.website"),
		"frappe.website.page_renderers": types.ModuleType("frappe.website.page_renderers"),
		"frappe.website.page_renderers.template_page": tp}
	with patch.dict(sys.modules, mods):
		sys.modules.pop("vagabond.trang_banh_vue", None)
		m = importlib.import_module("vagabond.trang_banh_vue")
		sys.modules.pop("vagabond.trang_banh_vue", None)
	m.frappe = fr
	m.TrangBanhVue.DOC = DOC
	return m.TrangBanhVue


TAO = []  # mỗi lần lớp gốc TemplatePage được dựng (tức là có quét tệp)


@ca("v601 tráo Vue: bộ dựng thật nhận /banh và dựng tệp web_moi/banh khi bật; tắt, đọc lỗi hay đường khác thì nhường trang cũ")
def _():
	L = _nap_lop(1)
	r = L("banh", None)
	la("bật: nhận /banh", r.can_render(), True)
	la("dựng đúng tệp Vue", r.path, "web_moi/banh")
	la("trang chủ tên miền order (Frappe đã đổi thành banh)", L("/banh/").can_render(), True)
	la("đường khác không nhận", L("dat-ban").can_render(), False)
	la("tắt: nhường trang cũ", _nap_lop(0)("banh").can_render(), False)
	la("chưa có trường (đọc lỗi): nhường trang cũ", _nap_lop(1, loi=True)("banh").can_render(), False)
	# v603: Editor xem trước đi theo công tắc, để Marketing xem đúng bản khách đang thấy.
	la("bật: Editor xem trước ra bản Vue", _nap_lop(1, {"bien_tap": "1"})("banh").can_render(), True)
	la("tắt: Editor xem trước ra trang cũ", _nap_lop(0, {"bien_tap": "1"})("banh").can_render(), False)
	x = L("banh/xong")
	la("bật: nhận biên nhận /banh/xong", x.can_render(), True)
	la("biên nhận dựng đúng tệp Vue", x.path, "web_moi/xong")
	la("tắt: biên nhận về trang cũ", _nap_lop(0)("banh/xong").can_render(), False)
	la("?ban=cu: biên nhận trang cũ", _nap_lop(1, {"ban": "cu"})("banh/xong").can_render(), False)
	la("?ban=cu giữ trang cũ", _nap_lop(1, {"ban": "cu"})("banh").can_render(), False)
	la("thiếu tệp Vue (bản cài lỗi): nhường trang cũ, không ra 404", _nap_lop(1, co_tep=False)("banh").can_render(), False)


@ca("v601 tráo Vue: request đường khác /banh không quét tệp, không đọc Cài đặt (bộ dựng chạy trên MỌI request web)")
def _():
	L = _nap_lop(1)
	for d in ("dat-ban", "assets/x.js", "web_moi/banh", "banh/xong/T", "", "app/bep"):
		r = L(d, None)
		la("đường %r: không nhận" % d, r.can_render(), False)
		la("đường %r: giữ path cho Frappe" % d, r.path, d)
	la("không dựng lớp gốc lần nào", TAO, [])
	la("không đọc Cài đặt lần nào", L.DOC, [])
	L("banh").can_render()
	la("đường /banh mới dựng lớp gốc", TAO, ["web_moi/banh"])
	la("và mới đọc Cài đặt", L.DOC, ["web_ban_vue"])


@ca("v601 tráo Vue: hook page_renderer trỏ đúng lớp, công tắc Cài đặt mặc định tắt và có lời giải thích")
def _():
	cay = ast.parse((GOC / "hooks.py").read_text())
	gan = [n for n in cay.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "page_renderer" for t in n.targets)]
	la("một lần gán page_renderer", len(gan), 1)
	la("trỏ lớp", ast.literal_eval(gan[0].value), ["vagabond.trang_banh_vue.TrangBanhVue"])
	dung("lớp có trong tệp", "class TrangBanhVue(TemplatePage)" in (GOC / "trang_banh_vue.py").read_text())
	d = json.loads((GOC / "vagabond/doctype/vagabond_settings/vagabond_settings.json").read_text())
	o = next(x for x in d["fields"] if x["fieldname"] == "web_ban_vue")
	la("kiểu và mặc định", (o["fieldtype"], o.get("default")), ("Check", "0"))
	dung("nhãn tiếng Việt", o["label"] == "Dùng trang đặt bánh bản mới")
	dung("lời giải thích nói cách quay lại", "không cần deploy" in o.get("description", ""))
	fo = d["field_order"]
	la("nằm ngay dưới mục Trang đặt bánh", fo[fo.index("sec_web_dat_banh") + 1], "web_ban_vue")
	la("field_order khớp danh sách trường", sorted(fo), sorted(x["fieldname"] for x in d["fields"]))


@ca("v601 tráo Vue: tại /banh trang cho máy tìm kiếm đọc, ở đường thử /web_moi/banh vẫn noindex")
def _():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	for duong, mong in (("/banh", True), ("/", True), ("/web_moi/banh", False)):
		fr = D(local=D(request=D(path=duong)), sessions=D(get_csrf_token=lambda: "c"))
		c = D()
		nap("www/web_moi/banh.py", "get_context", {"frappe": fr, "seo_banh": lambda: {}})(c)
		la("cong_khai tại " + duong, c.cong_khai, mong)
	html = (GOC / "www/web_moi/banh.html").read_text()
	dung("robots chỉ khi không công khai", '{% if not cong_khai %}<meta name="robots" content="noindex,nofollow">{% endif %}' in html)
	la("không còn robots cứng", html.count('name="robots"'), 1)
