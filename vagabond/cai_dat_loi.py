# -*- coding: utf-8 -*-
"""Ô "Cài đặt lõi và API" trên app: sửa trang Vagabond Settings ngay trên điện thoại.

Anh Việt 04/10/2026: *"đưa luôn cái bảng Vagabond setting này thành 1 ô trong
phân hệ cài đặt trên app ... sau này anh chỉ việc điền trên app. Mỗi lần em thêm
gì trong trang này thì phải thêm cả trên bản desk và bản app."*

Vì sao màn app ĐỌC CẤU TRÚC từ doctype chứ không tự liệt kê ô: nếu app có danh
sách ô riêng thì mỗi lần thêm ô trên Desk lại phải nhớ thêm bên app, và đúng
kiểu lỗi điều 18 đã dạy: đúng cho tới lần quên đầu tiên. Ở đây tab, mục, ô,
nhãn, mô tả, kiểu, chỉ đọc, thu gọn đều lấy từ `frappe.get_meta`, gồm cả trường
tự thêm (Custom Field). Thêm ô vào trang Desk là app tự có.

Ba điều anh chốt: chỉ quản trị (System Manager) mở và sửa; khoá bí mật không
bao giờ gửi xuống máy, chỉ báo đã khai; bảng Nhóm nhận tin Zalo sửa được trên app.

Lưu đi qua `doc.save()` nên mọi kiểm tra của Cài đặt (VagabondSettings.validate,
kenh_zalo.kiem_bang_nhom, kiem_ma_chat, tài khoản BTP) chạy y như khi bấm Lưu
trên Desk. Trang đã bị sửa ở nơi khác sau lúc mở thì từ chối, bắt tải lại.
"""

# phần thuần
import json
import re

DOCTYPE = "Vagabond Settings"
QUYEN = ("System Manager",)

KHONG_GIA_TRI = ("Section Break", "Column Break", "Tab Break", "HTML", "Button", "Heading", "Fold")
SO_NGUYEN = ("Int", "Check")
SO_THUC = ("Float", "Currency", "Percent")
CHU = ("Data", "Small Text", "Text", "Long Text", "Code", "Text Editor", "Select", "Link",
	"Date", "Datetime", "Time", "Password", "Autocomplete")

# Ô trên Desk để chỉ đọc chỉ vì bắt người dùng chọn qua hộp chọn (không gõ tay),
# máy chủ vẫn kiểm lại lúc lưu. App có hộp chọn tương ứng nên được ghi.
GHI_QUA_HOP_CHON = {
	"zalo_nhom": ("chat_id", "loai_tin", "chu_de"),
}
# Ô trên trang để chỉ đọc vì chỉ đổi qua ô chọn ngân hàng (ghi cả hai cùng lúc).
GHI_QUA_HOP_CHON_TRANG = ("ngan_hang_hien_thi",)


def _o(df, k, mac=None):
	v = df.get(k) if isinstance(df, dict) else getattr(df, k, mac)
	return mac if v is None else v


def bo_cuc(truong):
	"""Danh sách trường đã xếp (đúng thứ tự Frappe) -> tab, mục, ô cho màn app.

	Ô ẩn không gửi. Ô ở đầu trang trước tab đầu tiên rơi vào một tab "Chung"
	để không mất ô nào. THUẦN.
	"""
	tabs, tab, muc = [], None, None

	def mo_tab(fn, nhan):
		t = {"fn": fn, "nhan": nhan, "muc": []}
		tabs.append(t)
		return t

	def mo_muc(t, fn, nhan, mo, gon):
		m = {"fn": fn, "nhan": nhan, "mo": mo, "gon": gon, "o": []}
		t["muc"].append(m)
		return m

	for df in truong:
		kieu = _o(df, "fieldtype")
		fn = _o(df, "fieldname")
		if kieu == "Tab Break":
			tab, muc = mo_tab(fn, _o(df, "label", "")), None
			continue
		if kieu == "Section Break":
			if tab is None:
				tab = mo_tab("tab_chung", "Chung")
			muc = mo_muc(tab, fn, _o(df, "label", ""), _o(df, "description", ""), 1 if _o(df, "collapsible") else 0)
			continue
		if kieu == "Column Break" or _o(df, "hidden"):
			continue
		if tab is None:
			tab = mo_tab("tab_chung", "Chung")
		if muc is None:
			muc = mo_muc(tab, fn + "__muc", "", "", 0)
		muc["o"].append({
			"fn": fn, "nhan": _o(df, "label", "") or fn, "mo": _o(df, "description", ""),
			"kieu": kieu, "tuy_chon": _o(df, "options", ""),
			"chi_doc": 1 if (_o(df, "read_only") and fn not in GHI_QUA_HOP_CHON_TRANG) else 0,
			"bat_buoc": 1 if _o(df, "reqd") else 0,
		})
	# Bỏ mục rỗng (ví dụ mục chỉ có ô ẩn), bỏ tab rỗng.
	for t in tabs:
		t["muc"] = [m for m in t["muc"] if m["o"]]
	return [t for t in tabs if t["muc"]]


def gia_tri(truong, doc):
	"""Giá trị gửi xuống máy. Khoá bí mật CHỈ gửi cờ đã khai, không gửi chữ. THUẦN."""
	ra = {}
	for df in truong:
		kieu, fn = _o(df, "fieldtype"), _o(df, "fieldname")
		if kieu in KHONG_GIA_TRI or kieu == "Table" or _o(df, "hidden"):
			continue
		v = doc.get(fn)
		if kieu == "Password":
			ra[fn] = {"da_khai": 1 if (v not in (None, "") and str(v).strip()) else 0}
		else:
			ra[fn] = v
	return ra


def ep_kieu(kieu, v, tuy_chon=""):
	"""Ép một giá trị gửi lên về đúng kiểu ô, sai thì ném ValueError. THUẦN."""
	if kieu == "Check":
		if v in (0, 1, "0", "1", True, False):
			return 1 if v in (1, "1", True) else 0
		raise ValueError("chỉ nhận bật hoặc tắt")
	if kieu == "Int":
		if v in (None, ""):
			return 0
		try:
			f = float(v)
		except (TypeError, ValueError):
			raise ValueError("phải là số nguyên")
		if f != int(f):
			raise ValueError("phải là số nguyên")
		return int(f)
	if kieu in SO_THUC:
		if v in (None, ""):
			return 0
		try:
			return float(v)
		except (TypeError, ValueError):
			raise ValueError("phải là số")
	if kieu == "Select":
		cho = [x for x in str(tuy_chon or "").split("\n")]
		v = "" if v is None else str(v)
		if v not in cho:
			raise ValueError("chỉ được chọn trong danh sách")
		return v
	if kieu in CHU:
		if v is None:
			return ""
		if isinstance(v, (dict, list)):
			raise ValueError("phải là chữ")
		return str(v)
	raise ValueError("kiểu ô này chưa sửa được trên app")


def kiem_thay_doi(truong, thay, xoa_khoa=None):
	"""Lọc và ép kiểu các ô gửi lên. Trả (dict ô -> giá trị, danh sách lỗi). THUẦN.

	Chỉ nhận ô có trên trang, không ẩn, không chỉ đọc, không phải bảng. Khoá bí
	mật để trống là GIỮ NGUYÊN; muốn gỡ thì gửi tên ô trong `xoa_khoa`.
	"""
	theo_ten = {_o(df, "fieldname"): df for df in truong}
	ra, loi = {}, []
	for fn, v in (thay or {}).items():
		df = theo_ten.get(fn)
		if df is None:
			loi.append("Ô %s không có trên trang Cài đặt." % fn)
			continue
		kieu = _o(df, "fieldtype")
		nhan = _o(df, "label", "") or fn
		if kieu in KHONG_GIA_TRI or kieu == "Table" or _o(df, "hidden"):
			loi.append("Ô %s không sửa ở đây được." % nhan)
			continue
		if _o(df, "read_only") and fn not in GHI_QUA_HOP_CHON_TRANG:
			loi.append("Ô %s do máy tự ghi, không sửa tay." % nhan)
			continue
		if kieu == "Password" and (v is None or str(v).strip() == ""):
			continue
		try:
			ra[fn] = ep_kieu(kieu, v, _o(df, "options", ""))
		except ValueError as e:
			loi.append("Ô %s %s." % (nhan, e))
	for fn in xoa_khoa or []:
		df = theo_ten.get(fn)
		if df is None or _o(df, "fieldtype") != "Password" or _o(df, "read_only"):
			loi.append("Không gỡ được khoá ở ô %s." % fn)
			continue
		ra[fn] = ""
	return ra, loi


def kiem_dong_bang(truong_con, dong, cho_ghi=()):
	"""Lọc một dòng bảng con gửi lên. Trả (dict, lỗi). THUẦN."""
	ra, loi = {}, []
	theo_ten = {_o(df, "fieldname"): df for df in truong_con}
	for fn, v in (dong or {}).items():
		if fn in ("name", "idx"):
			continue
		df = theo_ten.get(fn)
		if df is None:
			loi.append("Cột %s không có trong bảng." % fn)
			continue
		kieu = _o(df, "fieldtype")
		if kieu in KHONG_GIA_TRI or _o(df, "hidden"):
			continue
		if _o(df, "read_only") and fn not in cho_ghi:
			continue
		try:
			ra[fn] = ep_kieu(kieu, v, _o(df, "options", ""))
		except ValueError as e:
			loi.append("Cột %s %s." % (_o(df, "label", "") or fn, e))
	return ra, loi


def tom_bang(truong_con):
	"""Mô tả cột của bảng con cho màn app. THUẦN."""
	return [{
		"fn": _o(df, "fieldname"), "nhan": _o(df, "label", "") or _o(df, "fieldname"),
		"mo": _o(df, "description", ""), "kieu": _o(df, "fieldtype"),
		"tuy_chon": _o(df, "options", ""), "chi_doc": 1 if _o(df, "read_only") else 0,
		"bat_buoc": 1 if _o(df, "reqd") else 0,
	} for df in truong_con if _o(df, "fieldtype") not in KHONG_GIA_TRI and not _o(df, "hidden")]


def gop_dong(truong_con, dong_cu):
	"""Giá trị các cột có dữ liệu của một dòng bảng con đang lưu. THUẦN."""
	return {_o(df, "fieldname"): dong_cu.get(_o(df, "fieldname")) for df in truong_con
		if _o(df, "fieldtype") not in KHONG_GIA_TRI}


MAU_TIM = re.compile(r"[%_\\]")


# ------------------------------------------------------- phần cần Frappe

import frappe  # noqa: E402


def _chi_quan_tri():
	if not set(QUYEN) & set(frappe.get_roles()):
		frappe.throw("Chỉ quản trị hệ thống mới mở được Cài đặt lõi và API.", frappe.PermissionError)


def _truong():
	return list(frappe.get_meta(DOCTYPE).fields)


@frappe.whitelist()
def lay():
	"""Bố cục, giá trị và bảng con của trang Cài đặt cho màn app."""
	_chi_quan_tri()
	doc = frappe.get_single(DOCTYPE)
	truong = _truong()
	bang = {}
	for df in truong:
		if df.fieldtype != "Table" or df.hidden:
			continue
		con = list(frappe.get_meta(df.options).fields)
		bang[df.fieldname] = {
			"cot": tom_bang(con),
			"dong": [dict(gia_tri(con, r), name=r.name) for r in (doc.get(df.fieldname) or [])],
			"ghi_qua_hop_chon": list(GHI_QUA_HOP_CHON.get(df.fieldname, ())),
		}
	return {
		"bo_cuc": bo_cuc(truong),
		"gia_tri": gia_tri(truong, doc),
		"bang": bang,
		"modified": str(doc.modified),
	}


@frappe.whitelist()
def luu(thay=None, bang=None, xoa_khoa=None, modified=None):
	"""Ghi các ô đã đổi và (nếu có) bảng con, qua doc.save() để mọi kiểm tra chạy."""
	_chi_quan_tri()
	thay = json.loads(thay) if isinstance(thay, str) else (thay or {})
	bang = json.loads(bang) if isinstance(bang, str) else (bang or {})
	xoa_khoa = json.loads(xoa_khoa) if isinstance(xoa_khoa, str) else (xoa_khoa or [])
	doc = frappe.get_single(DOCTYPE)
	if modified and str(doc.modified) != str(modified):
		frappe.throw("Cài đặt vừa được sửa ở nơi khác sau khi anh chị mở màn này. Tải lại rồi sửa tiếp.")
	truong = _truong()
	ra, loi = kiem_thay_doi(truong, thay, xoa_khoa)
	theo_ten = {df.fieldname: df for df in truong}
	for fn, rows in (bang or {}).items():
		df = theo_ten.get(fn)
		if df is None or df.fieldtype != "Table" or df.hidden:
			loi.append("Bảng %s không sửa ở đây được." % fn)
			continue
		con = list(frappe.get_meta(df.options).fields)
		cu = {r.name: r for r in (doc.get(fn) or [])}
		sach = []
		for r in rows or []:
			d, l = kiem_dong_bang(con, r, GHI_QUA_HOP_CHON.get(fn, ()))
			loi.extend(l)
			# Dòng đã có: giữ nguyên các cột app không gửi (cột chỉ đọc máy tự
			# ghi mà sau này mới thêm), chỉ đè cột đã lọc ở trên.
			goc = cu.get((r or {}).get("name"))
			if goc is not None:
				d = dict(gop_dong(con, goc.as_dict()), **d)
			sach.append(d)
		if not loi:
			doc.set(fn, [])
			for d in sach:
				doc.append(fn, d)
	if loi:
		frappe.throw("<br>".join(frappe.utils.escape_html(x) for x in loi))
	for fn, v in ra.items():
		doc.set(fn, v)
	doc.save()
	return lay()


@frappe.whitelist()
def tim_lien_ket(o, tu=""):
	"""Gợi ý giá trị cho một ô Liên kết trên trang Cài đặt (theo quyền đọc của người gọi)."""
	_chi_quan_tri()
	df = {d.fieldname: d for d in _truong()}.get(o)
	if not df or df.fieldtype != "Link":
		frappe.throw("Ô này không phải ô chọn từ danh mục.")
	tu = MAU_TIM.sub("", str(tu or ""))[:60]
	dk = {"name": ["like", "%%%s%%" % tu]} if tu else {}
	return [r.name for r in frappe.get_list(df.options, filters=dk, fields=["name"], limit_page_length=20 if tu else 200, order_by="name asc")]
