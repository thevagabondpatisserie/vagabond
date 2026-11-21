# -*- coding: utf-8 -*-
"""Công tắc giao diện mới "Nghệ sĩ công nghệ" của app /bep (PR 1, đặc tả bản 4 mục 2).

MỘT hàm duy nhất tính bật hay tắt: `tinh_bat`. Mọi nơi khác chỉ đọc kết quả.

Ba tầng, tầng trên thắng tầng dưới:
  1. Tắt khẩn cấp (cả tiệm)      bật là mọi tài khoản về giao diện cũ
  2. Lựa chọn riêng (tài khoản)  Theo chung / Luôn bật / Luôn tắt
  3. Tầng chung (cả tiệm)        Tắt / Bật

CÔNG TẮC NÀY CHỈ ĐỔI CÁCH VẼ. Không mô đun kiểm quyền, API, truy vấn hay báo
cáo nào được đọc nó: ca `thu_giao_dien_ui_b` chặn mọi tệp khác nhập mô đun này.

Cách trạng thái tới trình duyệt
-------------------------------
Trang /bep là một Web Page của Frappe. Frappe giữ HTML của trang trong bộ nhớ
đệm CHUNG cho mọi người (30 phút, theo đường dẫn), nên muốn HTML mang trạng
thái riêng từng tài khoản thì phải tắt bộ nhớ đệm cho đúng trang này. Hook
`ngu_canh` làm ba việc, chỉ với trang app:
  - đặt `no_cache` để Frappe không lưu và không trả HTML của người này cho người khác;
  - đặt `Cache-Control: private, no-store` cho trình duyệt và proxy;
  - chèn vào <head> một đoạn script nhỏ chạy TRƯỚC lần vẽ đầu: gắn class
    `ui-b` lên thẻ html (khi bật) và ghi số phiên bản để app đối chiếu.

Hook hỏng ở bất kỳ bước nào thì trả nguyên ngữ cảnh: trang ra giao diện cũ.
Giao diện cũ là đường dự phòng, không bao giờ giấu cả trang.
"""

import os
import re

try:
	import frappe
except ImportError:  # CI tay không: phép thuần vẫn kiểm được
	frappe = None

DOCTYPE = "Vagabond Giao Dien"
TRANG_APP = "bep"

THEO_CHUNG = "Theo chung"
LUON_BAT = "Luôn bật"
LUON_TAT = "Luôn tắt"
LUA_CHON = (THEO_CHUNG, LUON_BAT, LUON_TAT)

# Hai tệp phông tải sớm (bản 4 mục 3): chữ thường và chữ đậm tiếng Việt.
PHONG_TAI_SOM = (
	"/assets/vagabond/fonts/ui/be-vietnam-pro-vietnamese-400-normal.woff2",
	"/assets/vagabond/fonts/ui/be-vietnam-pro-vietnamese-600-normal.woff2",
)
MAU_GIAY = "#F3EFE7"
# Màu vỏ app (vùng đồng hồ, thanh trình duyệt) khi bật: trùng màu đầu trang ui-b
# (--ui-header-tint) và PWA_MAU_UIB ở 00-nen.js. Codex UI01.
MAU_VO_APP = "#EAF4F3"

_GOC = os.path.dirname(os.path.abspath(__file__))
_TEP_APPVER = os.path.join(_GOC, "public", "js", "bep", "12-van-don.js")
_nho_appver = {"mtime": None, "so": ""}


def _la_bat(v):
	"""Ô Check của Frappe: 1, "1", True là bật. None, 0, "0", "" là tắt."""
	if v is None:
		return False
	if isinstance(v, str):
		return v.strip() not in ("", "0")
	return bool(v)


def tinh_bat(tat_khan_cap, bat_chung, rieng=None):
	"""Tài khoản này có thấy giao diện mới không. THUẦN.

	rieng: lựa chọn riêng của tài khoản. None, rỗng hoặc giá trị lạ đều coi là
	"Theo chung": ô chưa đặt không được tự thành bật.
	"""
	if _la_bat(tat_khan_cap):
		return False
	if rieng == LUON_BAT:
		return True
	if rieng == LUON_TAT:
		return False
	return _la_bat(bat_chung)


def lua_chon_cua(ds_rieng, nguoi_dung):
	"""Lựa chọn riêng của một tài khoản trong bảng. THUẦN.

	Một tài khoản có nhiều dòng thì dòng CUỐI thắng (dòng người quản trị thêm
	sau cùng). So email không phân biệt hoa thường.
	"""
	ten = str(nguoi_dung or "").strip().lower()
	kq = THEO_CHUNG
	if not ten:
		return kq
	for d in ds_rieng or []:
		lay = d.get if hasattr(d, "get") else (lambda k, _d=d: getattr(_d, k, None))
		if str(lay("nguoi_dung") or "").strip().lower() == ten:
			lc = lay("lua_chon")
			kq = lc if lc in LUA_CHON else THEO_CHUNG
	return kq


def doc_appver(ma=None):
	"""Số APPVER trong 12-van-don.js. "" nếu không đọc được. THUẦN khi truyền `ma`."""
	if ma is None:
		try:
			mt = os.path.getmtime(_TEP_APPVER)
			if _nho_appver["mtime"] == mt:
				return _nho_appver["so"]
			with open(_TEP_APPVER, encoding="utf-8") as f:
				ma = f.read()
			so = doc_appver(ma)
			_nho_appver.update(mtime=mt, so=so)
			return so
		except Exception:
			return ""
	m = re.search(r"var\s+APPVER\s*=\s*'(\d+)'", ma or "")
	return m.group(1) if m else ""


def dau_trang_html(bat, appver):
	"""Đoạn chèn vào <head> của trang app. THUẦN.

	Chỉ nhận số phiên bản là chữ số: chuỗi này đi thẳng vào thẻ script.
	Không có số phiên bản thì KHÔNG bật: app không đối chiếu được thì dùng
	giao diện cũ (bản 4 mục 2, lệch phiên bản về trọn giao diện cũ).
	"""
	v = appver if re.match(r"^\d{1,6}$", str(appver or "")) else ""
	bat = bool(bat) and bool(v)
	dong = ['<script>window.__VGB_UI={b:%d,v:"%s"};%s</script>' % (
		1 if bat else 0, v, "document.documentElement.classList.add('ui-b');" if bat else "")]
	if bat:
		dong.append("<style>html.ui-b,html.ui-b body{background:%s!important}</style>" % MAU_GIAY)
		dong.append('<meta name="theme-color" content="%s">' % MAU_VO_APP)
		for p in PHONG_TAI_SOM:
			dong.append('<link rel="preload" as="font" type="font/woff2" crossorigin href="%s">' % p)
	return "\n".join(dong)


def la_trang_app(context):
	"""Ngữ cảnh này có phải của trang app /bep không. THUẦN."""
	try:
		return (context.get("doctype") == "Web Page" or context.get("doc") is not None) and context.get("route") == TRANG_APP
	except Exception:
		return False


def doc_cai_dat():
	"""(tat_khan_cap, bat_chung, bảng riêng) từ doctype Cài đặt giao diện."""
	d = frappe.get_cached_doc(DOCTYPE)
	return d.get("tat_khan_cap"), d.get("bat_chung"), (d.get("rieng") or [])


def dang_bat(nguoi_dung=None):
	"""Tài khoản đang đăng nhập (hoặc tài khoản truyền vào) có thấy giao diện mới không.

	Chưa đăng nhập (Guest) thì chỉ theo tầng khẩn cấp và tầng chung. Đọc hỏng
	thì trả False: giao diện cũ.
	"""
	try:
		nd = nguoi_dung or frappe.session.user
		khan, chung, ds = doc_cai_dat()
		return tinh_bat(khan, chung, lua_chon_cua(ds, nd))
	except Exception:
		return False


def ngu_canh(context=None):
	"""Hook update_website_context. Chỉ đụng trang app; trang khác trả nguyên."""
	if context is None or not la_trang_app(context):
		return context
	try:
		# Trạng thái là RIÊNG từng tài khoản: không lưu đệm chung, không cho
		# trình duyệt hay proxy giữ lại.
		context["no_cache"] = 1
		frappe.local.no_cache = 1
		frappe.local.response_headers["Cache-Control"] = "private, no-store"
		them = dau_trang_html(dang_bat(), doc_appver())
		context["head_include"] = (context.get("head_include") or "") + "\n" + them
	except Exception:
		try:
			frappe.log_error(title="Giao diện ui-b: không gắn được trạng thái, dùng giao diện cũ")
		except Exception:
			pass
	return context
