"""v565: ca TÍCH HỢP cho ô ghim nghiệp vụ, ghi THẬT xuống bảng DefaultValue.

Codex đòi trên PR #426 vòng 2: *"Bench xanh hiện tại chưa có ca ghim.lay/luu
trong kiem_that: cần insert/save/read thật DefaultValue qua hai tài khoản khác
nhau, reload/cache và xác nhận không lẫn ghim. Không coi ca thuần chuẩn hoá là
đã kiểm lưu Frappe."*

Đòi hỏi đó đúng. Bộ ca thuần ở `khung/kiem_thu/thu_gom_nhom_565.py` chỉ chứng
minh được phép chuẩn hoá chạy đúng; nó không trả lời được ba câu mà chỉ site
thật mới trả lời:

  1. `frappe.defaults.set_user_default` có thật sự GHI xuống không, hay bị nuốt
     vì Frappe đang giữ một lớp đệm nào đó.
  2. Ghi của người này có lẫn sang người kia không. Đây là câu nặng nhất: cất
     nhầm chỗ thì chị Dung mở app ra thấy ghim của bếp.
  3. Đọc lại SAU KHI XOÁ BỘ ĐỆM có còn đúng không. `frappe.defaults` đọc qua
     cache, nên một bản ghi sai mà cache đang giữ bản đúng thì ca kiểm xanh
     trong khi lần đăng nhập sau người dùng mất sạch ghim.

Mọi thứ chạy trong điểm lưu của `nen.py` rồi lùi lại, nên không để lại gì
trên tài khoản thật.
"""

import json

import frappe

from vagabond import ghim
from vagabond.khung.kiem_that.nen import ca, dung, la


def _nguoi_thu(ten):
	"""Dựng một tài khoản thử. Lùi về cùng điểm lưu nên không ở lại trên site."""
	if frappe.db.exists("User", ten):
		return ten
	u = frappe.get_doc({
		"doctype": "User",
		"email": ten,
		"first_name": ten.split("@")[0],
		"send_welcome_email": 0,
		"enabled": 1,
	})
	u.flags.ignore_permissions = True
	u.insert(ignore_permissions=True)
	return ten


def _xoa_bo_dem(ten):
	"""Xoá bộ đệm defaults của một người, rồi CHỐT là nó đã bị xoá thật.

	Vì sao không gọi thẳng một hàm: mô đun `frappe.defaults` KHÔNG có hàm xoá
	bộ đệm công khai. Bản đầu của bộ ca này gọi một tên không tồn tại và CI
	bench đỏ 4 ca với AttributeError (Codex bắt trên PR #429). Đường đúng là
	`frappe.cache_manager.clear_defaults_cache(user)`, chính là hàm mà
	`frappe.defaults._clear_cache` gọi tới qua `frappe.clear_cache`.

	Và không tin tên hàm: đọc thẳng khoá `defaults::<người>` trong
	`frappe.client_cache` để chốt nó đã trống. Một ca kiểm bộ đệm mà không xoá
	được bộ đệm thì nó đang tự lừa mình, đúng kiểu lỗi CLAUDE.md điều 15.
	"""
	from frappe import cache_manager

	cache_manager.clear_defaults_cache(ten)
	dung("bộ đệm defaults của %s đã trống" % ten,
		frappe.client_cache.get_value("defaults::%s" % ten) is None)


def _nhu_nguoi(ten, ham):
	"""Chạy một phép với tư cách người khác, rồi trả lại người cũ."""
	cu = frappe.session.user
	frappe.set_user(ten)
	try:
		return ham()
	finally:
		frappe.set_user(cu)


@ca("v565 ghim: cất rồi đọc lại trên site thật, qua đúng hai cửa của màn hình")
def _cat_va_doc():
	a = _nguoi_thu("vgb-ghim-a@kiemthu.local")
	ra = _nhu_nguoi(a, lambda: ghim.luu(json.dumps(["POS", "CNPT", "BC:BC05"])))
	la("cửa luu trả về đúng danh sách", ra["ghim"], ["POS", "CNPT", "BC:BC05"])
	la("trần số trả về đúng", ra["toi_da"], ghim.TOI_DA)
	doc = _nhu_nguoi(a, ghim.lay)
	la("đọc lại ra đúng cái vừa cất", doc["ghim"], ["POS", "CNPT", "BC:BC05"])


@ca("v565 ghim: XOÁ BỘ ĐỆM rồi đọc lại vẫn đúng, không phải chỉ đúng trong phiên")
def _qua_bo_dem():
	# frappe.defaults doc qua cache. Khong xoa cache thi ca kiem chi chung minh
	# duoc cai minh vua dat trong bo nho, khong chung minh duoc cai da xuong dia.
	a = _nguoi_thu("vgb-ghim-a@kiemthu.local")
	_nhu_nguoi(a, lambda: ghim.luu(json.dumps(["VD", "SOTAY"])))
	_xoa_bo_dem(a)
	doc = _nhu_nguoi(a, ghim.lay)
	la("qua bộ đệm vẫn đúng", doc["ghim"], ["VD", "SOTAY"])
	# Doc thang tu bang, khong qua lop defaults: chot rang no that su nam o do.
	tho = frappe.db.get_value("DefaultValue",
		{"parent": a, "defkey": ghim.KHOA, "parenttype": "__default"}, "defvalue")
	la("bảng DefaultValue giữ đúng chuỗi", json.loads(tho or "[]"), ["VD", "SOTAY"])


@ca("v565 ghim: hai người cất khác nhau thì KHÔNG lẫn sang nhau")
def _hai_nguoi():
	a = _nguoi_thu("vgb-ghim-a@kiemthu.local")
	b = _nguoi_thu("vgb-ghim-b@kiemthu.local")
	_nhu_nguoi(a, lambda: ghim.luu(json.dumps(["POS", "DTREO"])))
	_nhu_nguoi(b, lambda: ghim.luu(json.dumps(["KK", "STOCK", "TONCHANG"])))
	_xoa_bo_dem(a)
	_xoa_bo_dem(b)
	la("người A giữ đúng của mình", _nhu_nguoi(a, ghim.lay)["ghim"], ["POS", "DTREO"])
	la("người B giữ đúng của mình", _nhu_nguoi(b, ghim.lay)["ghim"],
		["KK", "STOCK", "TONCHANG"])
	# Va cat lai cua A khong duoc dung toi B.
	_nhu_nguoi(a, lambda: ghim.luu(json.dumps(["VD"])))
	_xoa_bo_dem(a)
	_xoa_bo_dem(b)
	la("A đổi thì A đổi", _nhu_nguoi(a, ghim.lay)["ghim"], ["VD"])
	la("A đổi thì B KHÔNG đổi", _nhu_nguoi(b, ghim.lay)["ghim"],
		["KK", "STOCK", "TONCHANG"])


@ca("v565 ghim: cất đè lên bản cũ thì THAY, không cộng dồn thành nhiều dòng")
def _cat_de():
	# frappe.defaults co ca add_default (cong don) lan set_default (thay). Dung
	# nham ham la moi lan cat lai them mot dong, va doc ra mot danh sach lon
	# dan cho toi khi vo tran.
	a = _nguoi_thu("vgb-ghim-a@kiemthu.local")
	for lan in (["POS"], ["CNPT"], ["VD", "KK"]):
		_nhu_nguoi(a, lambda d=lan: ghim.luu(json.dumps(d)))
	_xoa_bo_dem(a)
	la("chỉ còn bản cuối", _nhu_nguoi(a, ghim.lay)["ghim"], ["VD", "KK"])
	so = frappe.db.count("DefaultValue",
		{"parent": a, "defkey": ghim.KHOA, "parenttype": "__default"})
	la("và chỉ một dòng trong bảng", so, 1)


@ca("v565 ghim: người chưa ghim gì thì đọc ra rỗng, không nổ")
def _chua_ghim():
	c = _nguoi_thu("vgb-ghim-c@kiemthu.local")
	doc = _nhu_nguoi(c, ghim.lay)
	la("rỗng", doc["ghim"], [])
	la("vẫn trả về trần số", doc["toi_da"], ghim.TOI_DA)


@ca("v565 ghim: cất quá trần hoặc cất rác thì máy chủ tự cắt, không tin màn hình")
def _may_chu_tu_cat():
	# Man hinh da chan tran 5, nhung cua nay mo ra ngoai nen khong duoc tin
	# cai gui len. Ai goi thang cua cung khong nhet duoc 9 o hay mot chuoi la.
	a = _nguoi_thu("vgb-ghim-a@kiemthu.local")
	ra = _nhu_nguoi(a, lambda: ghim.luu(json.dumps(
		["a", "b", "c", "d", "e", "f", "g", "h", "i"])))
	la("cắt còn đúng trần", len(ra["ghim"]), ghim.TOI_DA)
	ra2 = _nhu_nguoi(a, lambda: ghim.luu(json.dumps(["POS", "o la<script>", "POS", 7])))
	la("bỏ rác, bỏ trùng", ra2["ghim"], ["POS"])
	_xoa_bo_dem(a)
	la("và cất đúng cái đã cắt", _nhu_nguoi(a, ghim.lay)["ghim"], ["POS"])


@ca("v565 ghim: hai cửa chỉ mở cho người đã đăng nhập, khách vãng lai không gọi được")
def _khong_cho_khach():
	# Cua nay ghi vao bang mac dinh cua Frappe. Mo cho khach vang lai la cho
	# bat ky ai tren Internet ghi vao do.
	for ham in (ghim.lay, ghim.luu):
		dung("%s đã whitelist" % ham.__name__, ham in frappe.whitelisted)
		dung("%s KHÔNG mở cho khách" % ham.__name__, ham not in frappe.guest_methods)
