# -*- coding: utf-8 -*-
"""v570: ô "Cài đặt lõi và API" trên app, sửa trang Vagabond Settings trên điện thoại.

Anh Việt 04/10/2026: *"Mỗi lần em thêm gì trong trang này thì phải thêm cả trên
bản desk và bản app."* Cách giữ lời đó là MỘT nguồn: màn app không có danh sách ô
riêng, máy chủ đọc cấu trúc doctype rồi gửi xuống. Các ca dưới đây chốt:

  - bo_cuc() phủ ĐỦ mọi ô hiện trên Desk, đúng tab, đúng mục (chạy trên JSON thật
    cộng mọi trường tự thêm, xếp bằng chính phép xếp của Frappe ở ca v568);
  - khoá bí mật không bao giờ đi xuống máy;
  - máy chủ chỉ nhận ô sửa được, ép đúng kiểu, chặn ô chỉ đọc, ô ẩn, ô lạ;
  - bảng Nhóm nhận tin Zalo: cột chỉ đọc chỉ ghi được qua hộp chọn đã khai;
  - mã app không tự giữ danh sách ô (dò chuỗi chỉ để chốt điều "không có", điều 16).

Hành vi màn app (mở tab, bật tắt, gõ, lưu, sửa nhóm Zalo) chạy thật trong node ở
hanh_vi/cai_dat_loi_570.js.
"""

import io
import json
import os
import re

from vagabond import cai_dat_loi as cdl
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu import thu_cai_dat_568 as t568

GOI = t568.GOI
JS_APP = os.path.join(GOI, "public", "js", "bep", "51-cai-dat-loi.js")
JS_TRANG_CHU = os.path.join(GOI, "public", "js", "bep", "02-trang-chu.js")
JSON_ZALO = os.path.join(GOI, "vagabond", "doctype", "vagabond_kenh_zalo", "vagabond_kenh_zalo.json")


def _doc(p):
	return io.open(p, encoding="utf-8").read()


def _truong_da_xep():
	"""Danh sách dict trường của Vagabond Settings đúng thứ tự Frappe xếp trên site."""
	d = t568._json()
	tu_them = t568._truong_tu_them()
	theo_ten = {f["fieldname"]: f for f in d["fields"] + tu_them}
	thu_tu, _ = t568._xep(d["fields"], tu_them)
	return [theo_ten[fn] for fn in thu_tu]


def _cot_zalo():
	return json.load(io.open(JSON_ZALO, encoding="utf-8"))["fields"]


@ca("cài đặt lõi v570: màn app có ĐỦ mọi ô hiện trên Desk, đúng tab, đúng mục")
def _():
	truong = _truong_da_xep()
	vi_tri, _ = t568._vi_tri()
	bc = cdl.bo_cuc(truong)
	tren_app = {}
	for t in bc:
		for m in t["muc"]:
			for o in m["o"]:
				la("ô %s chỉ hiện một lần" % o["fn"], o["fn"] in tren_app, False)
				tren_app[o["fn"]] = (t["fn"], m["fn"])
	can = [f["fieldname"] for f in truong
		if f["fieldtype"] not in ("Section Break", "Column Break", "Tab Break") and not f.get("hidden")]
	thieu = [fn for fn in can if fn not in tren_app]
	la("không ô nào hiện trên Desk mà thiếu trên app", thieu, [])
	lech = [fn for fn in can if tren_app.get(fn) != vi_tri[fn]]
	la("mỗi ô nằm đúng tab, đúng mục như Desk", lech, [])
	la("app có đúng 8 tab như Desk", [t["fn"] for t in bc], [x[0] for x in t568.TAB])
	dung("không có tab 'Chung' (nghĩa là không ô nào lọt lên trên tab đầu)",
		all(t["fn"] != "tab_chung" for t in bc))


@ca("cài đặt lõi v570: ô thêm sau này vào trang Desk thì app TỰ có, không phải sửa app")
def _():
	truong = _truong_da_xep()
	i = [f["fieldname"] for f in truong].index("sec_sepay")
	moi = {"fieldname": "o_thu_moi_570", "fieldtype": "Data", "label": "Ô thử mới"}
	bc = cdl.bo_cuc(truong[:i + 1] + [moi] + truong[i + 1:])
	cho = [(t["fn"], m["fn"]) for t in bc for m in t["muc"] for o in m["o"] if o["fn"] == "o_thu_moi_570"]
	la("ô mới hiện ngay trong mục SePay", cho, [("tab_ke_toan", "sec_sepay")])


@ca("cài đặt lõi v570: khoá bí mật KHÔNG BAO GIỜ đi xuống máy, chỉ báo đã khai")
def _():
	truong = _truong_da_xep()
	khoa = [f["fieldname"] for f in truong if f["fieldtype"] == "Password" and not f.get("hidden")]
	dung("trang có nhiều ô khoá bí mật để kiểm", len(khoa) >= 10)
	doc = {fn: "BI-MAT-%s-xyz" % fn for fn in khoa}
	doc["sepay_khoa"] = ""
	gt = cdl.gia_tri(truong, doc)
	ra = json.dumps({"gia_tri": gt, "bo_cuc": cdl.bo_cuc(truong)}, ensure_ascii=False)
	la("không lộ chữ nào của khoá", "BI-MAT-" in ra, False)
	la("khoá đã khai -> da_khai 1", gt[khoa[0]] if khoa[0] != "sepay_khoa" else gt[khoa[1]], {"da_khai": 1})
	la("khoá để trống -> da_khai 0", gt["sepay_khoa"], {"da_khai": 0})
	la("khoá chỉ có khoảng trắng vẫn là chưa khai", cdl.gia_tri(truong, {"sepay_khoa": "   "})["sepay_khoa"], {"da_khai": 0})


@ca("cài đặt lõi v570: máy chủ chặn ô chỉ đọc, ô ẩn, ô lạ, ô bảng; ép đúng kiểu")
def _():
	truong = _truong_da_xep()
	theo = {f["fieldname"]: f for f in truong}
	chi_doc = [fn for fn, f in theo.items() if f.get("read_only") and f["fieldtype"] not in ("Section Break", "Column Break", "Tab Break", "HTML")
		and fn not in cdl.GHI_QUA_HOP_CHON_TRANG]
	dung("trang có ô chỉ đọc để kiểm", len(chi_doc) >= 1)
	ra, loi = cdl.kiem_thay_doi(truong, {chi_doc[0]: "x"})
	la("ô chỉ đọc không ghi", ra, {})
	dung("ô chỉ đọc báo lỗi", len(loi) == 1 and "máy tự ghi" in loi[0])
	ra, loi = cdl.kiem_thay_doi(truong, {"o_khong_co": 1, "zalo_nhom": [], "tab_ke_toan": 1})
	la("ô lạ, ô bảng, ô ngắt tab đều không ghi", ra, {})
	la("ba lỗi cho ba ô", len(loi), 3)
	an = [fn for fn, f in theo.items() if f.get("hidden") and f["fieldtype"] not in ("Section Break", "Column Break", "Tab Break")]
	if an:
		ra, loi = cdl.kiem_thay_doi(truong, {an[0]: "x"})
		la("ô ẩn không ghi", ra, {})
	ra, loi = cdl.kiem_thay_doi(truong, {"sepay_bat": "1", "khoa_so_ngay": "3", "minvoice_host": "https://x.vn"})
	la("Check '1' thành 1, Int '3' thành 3, chữ giữ chữ", ra, {"sepay_bat": 1, "khoa_so_ngay": 3, "minvoice_host": "https://x.vn"})
	la("không lỗi", loi, [])
	ra, loi = cdl.kiem_thay_doi(truong, {"sepay_bat": "co"})
	dung("Check nhận chữ lạ thì lỗi", ra == {} and len(loi) == 1)
	la("Select ngoài danh sách thì lỗi", cdl.kiem_thay_doi(truong, {"diem_chu_ky": "Moi tuan"})[0], {})
	la("Select trong danh sách thì nhận", cdl.kiem_thay_doi(truong, {"diem_chu_ky": "Cuon chieu"})[0], {"diem_chu_ky": "Cuon chieu"})
	try:
		cdl.ep_kieu("Int", "2.5")
		dung("Int 2.5 phải lỗi", False)
	except ValueError:
		pass
	la("Int '3' thành 3", cdl.ep_kieu("Int", "3"), 3)
	la("Float '' thành 0", cdl.ep_kieu("Float", ""), 0)


@ca("cài đặt lõi v570: khoá để trống là GIỮ NGUYÊN, muốn gỡ phải nói rõ")
def _():
	truong = _truong_da_xep()
	ra, loi = cdl.kiem_thay_doi(truong, {"sepay_khoa": "", "minvoice_password": "  "})
	la("khoá trống không đè khoá cũ", ra, {})
	la("không lỗi", loi, [])
	ra, loi = cdl.kiem_thay_doi(truong, {"sepay_khoa": "moi123"})
	la("khoá mới thì ghi", ra, {"sepay_khoa": "moi123"})
	ra, loi = cdl.kiem_thay_doi(truong, {}, ["sepay_khoa"])
	la("gỡ khoá rõ ràng thì ghi chuỗi rỗng", ra, {"sepay_khoa": ""})
	ra, loi = cdl.kiem_thay_doi(truong, {}, ["sepay_bat"])
	dung("không gỡ được ô không phải khoá", ra == {} and len(loi) == 1)


@ca("cài đặt lõi v570: ô ngân hàng hiển thị chỉ đọc trên Desk nhưng ghi được qua ô chọn ngân hàng")
def _():
	truong = _truong_da_xep()
	theo = {f["fieldname"]: f for f in truong}
	for fn in cdl.GHI_QUA_HOP_CHON_TRANG:
		dung("%s có thật và để chỉ đọc trên Desk (ngoại lệ có nghĩa)" % fn, theo.get(fn, {}).get("read_only") == 1)
	ra, loi = cdl.kiem_thay_doi(truong, {"ngan_hang_hien_thi": "Agribank"})
	la("ghi được tên ngân hàng", ra, {"ngan_hang_hien_thi": "Agribank"})
	o = [o for t in cdl.bo_cuc(truong) for m in t["muc"] for o in m["o"] if o["fn"] == "ngan_hang_hien_thi"]
	la("app không khoá ô này", [x["chi_doc"] for x in o], [0])


@ca("cài đặt lõi v570: bảng Nhóm nhận tin Zalo - cột chỉ đọc chỉ ghi qua hộp chọn đã khai")
def _():
	cot = _cot_zalo()
	theo = {f["fieldname"]: f for f in cot}
	for fn in cdl.GHI_QUA_HOP_CHON["zalo_nhom"]:
		dung("cột %s có thật và chỉ đọc trên Desk" % fn, theo.get(fn, {}).get("read_only") == 1)
	ra, loi = cdl.kiem_dong_bang(cot, {"name": "abc", "ten_nhom": "Vận hành", "chat_id": "123", "loai_tin": "canh_bao\nban_tin",
		"bat": "1", "im_tu": "22:00"}, cdl.GHI_QUA_HOP_CHON["zalo_nhom"])
	la("dòng hợp lệ", ra, {"ten_nhom": "Vận hành", "chat_id": "123", "loai_tin": "canh_bao\nban_tin", "bat": 1, "im_tu": "22:00"})
	la("không lỗi", loi, [])
	ra, loi = cdl.kiem_dong_bang(cot, {"chat_id": "123"}, ())
	la("không khai hộp chọn thì cột chỉ đọc bị bỏ", ra, {})
	ra, loi = cdl.kiem_dong_bang(cot, {"cot_la": 1}, ())
	dung("cột lạ báo lỗi", len(loi) == 1)
	tb = cdl.tom_bang(cot)
	la("mô tả cột không có ô ngắt cột", [c["fn"] for c in tb], ["ten_nhom", "chat_id", "loai_tin", "chu_de", "im_tu", "im_den", "bat"])


@ca("cài đặt lõi v570: dòng Zalo đã có giữ nguyên cột app không gửi")
def _():
	cot = _cot_zalo() + [{"fieldname": "lan_gui_cuoi", "fieldtype": "Datetime", "read_only": 1}]
	cu = {"ten_nhom": "Kế toán", "chat_id": "9", "lan_gui_cuoi": "2026-10-01 08:00:00", "name": "r1", "doctype": "x"}
	goc = cdl.gop_dong(cot, cu)
	moi, _ = cdl.kiem_dong_bang(cot, {"name": "r1", "ten_nhom": "Kế toán mới", "lan_gui_cuoi": "2020-01-01"}, ())
	d = dict(goc, **moi)
	la("cột máy tự ghi giữ nguyên", d["lan_gui_cuoi"], "2026-10-01 08:00:00")
	la("cột đã sửa lấy giá trị mới", d["ten_nhom"], "Kế toán mới")
	dung("không mang name, doctype của dòng cũ", "name" not in d and "doctype" not in d)


@ca("cài đặt lõi v570: ba cửa máy chủ đều chỉ cho quản trị, đã khai trong thu_cua_ngo")
def _():
	s = _doc(os.path.join(GOI, "cai_dat_loi.py"))
	for ten in ("lay", "luu", "tim_lien_ket"):
		m = re.search(r"@frappe\.whitelist\(\)\ndef %s\(.*?\n(?=\n@|\Z)" % ten, s, re.S)
		dung("có cửa %s" % ten, m is not None)
		dung("cửa %s kiểm quyền quản trị trước tiên" % ten, m and "\t_chi_quan_tri()\n" in m.group(0).split('"""')[-1][:40])
	la("quyền là System Manager", cdl.QUYEN, ("System Manager",))
	from vagabond.khung.kiem_thu import thu_cua_ngo
	dung("thu_cua_ngo có đủ ba cửa", "cai_dat_loi.py" in _doc(thu_cua_ngo.__file__)
		and '"cai_dat_loi.py": ["lay", "luu", "tim_lien_ket"]' in _doc(thu_cua_ngo.__file__))


@ca("cài đặt lõi v570: ô trên trang chủ chỉ hiện cho quản trị, có đường dẫn và mở đúng màn")
def _():
	s = _doc(JS_TRANG_CHU)
	m = re.search(r"\(hasRole\('System Manager'\)\n\s*\? card\('🔑', 'Cài đặt lõi và API'.*?'CDLOI'\)", s)
	dung("ô Cài đặt lõi và API chỉ trong nhánh System Manager", m is not None)
	dung("có trong phân hệ Cài đặt", re.search(r"k: 'KHAC'.*?keys: \['CDLOI'", s, re.S) is not None)
	dung("có đường dẫn", "'cai-dat-loi-va-api': 'CDLOI'" in s)
	dung("bấm ô mở màn Cài đặt lõi", "if (k === 'CDLOI') return go(scrCaiDatLoi);" in s)


@ca("cài đặt lõi v570: màn app KHÔNG tự giữ danh sách ô, Desk và app dùng chung một tệp")
def _():
	# Dò chuỗi chỉ để chốt điều "không có" (điều 16): app không gõ tay tên ô nào
	# của trang Cài đặt, nên thêm ô trên Desk là app tự có.
	app = _doc(JS_APP)
	truong = [f["fieldname"] for f in _truong_da_xep()
		if f["fieldtype"] not in ("Section Break", "Column Break", "Tab Break")]
	# Được gõ: bảng Zalo và cặp ô ngân hàng có hộp chọn riêng; ô HTML thẻ tóm tắt
	# dữ liệu app tự ghi được vẽ bằng hàm chung thay cho HTML của Desk.
	cho_phep = {"zalo_nhom", "ngan_hang_hien_thi", "ngan_hang_bin", "zalo_chat_moi", "html_du_lieu_app"}
	go_tay = sorted(fn for fn in truong if fn not in cho_phep and re.search(r"['\"]%s['\"]" % re.escape(fn), app))
	la("không ô nào gõ tay trong màn app", go_tay, [])
	dung("app nạp tệp chung", "/assets/vagabond/js/cai_dat_loi_chung.js" in app)
	dung("Desk nạp tệp chung", "/assets/vagabond/js/cai_dat_loi_chung.js" in _doc(t568.JS_DESK))
	dung("app lưu qua cửa máy chủ", "vagabond.cai_dat_loi.luu" in app and "vagabond.cai_dat_loi.lay" in app)


def _goi_may_chu(ham, truong=None, ban_ghi=None, quyen=("System Manager",), doc=None):
	"""Gọi một cửa của cai_dat_loi trên frappe giả, ghi lại lời gọi get_list/get_all."""
	import types
	import frappe as fr
	nk = []
	moc = {k: getattr(fr, k, None) for k in ("get_roles", "get_list", "get_all", "get_meta", "get_single", "defaults")}
	tr = truong if truong is not None else _truong_da_xep()

	def get_list(dt, filters=None, **k):
		nk.append((dt, dict(filters or {})))
		ds = [r for r in (ban_ghi or {}).get(dt, []) if all(
			(r.get(a) == b) for a, b in (filters or {}).items() if not isinstance(b, list))]
		return [r["name"] for r in ds] if k.get("pluck") == "name" else [types.SimpleNamespace(name=r["name"]) for r in ds]
	fr.get_roles = lambda *a: list(quyen)
	fr.get_list = get_list
	fr.get_all = get_list
	fr.get_meta = lambda dt: types.SimpleNamespace(fields=[types.SimpleNamespace(**f) for f in tr])
	fr.get_single = lambda dt: doc
	fr.defaults = types.SimpleNamespace(get_global_default=lambda k: "TV")
	try:
		return ham(), nk
	finally:
		for k, v in moc.items():
			if v is None:
				if hasattr(fr, k):
					delattr(fr, k)
			else:
				setattr(fr, k, v)


@ca("Codex #439 V1: mọi ô Liên kết trên trang đều đã khai phạm vi chọn, ô mới chưa khai thì ca đỏ")
def _():
	lk = [f["fieldname"] for f in _truong_da_xep() if f["fieldtype"] == "Link" and not f.get("hidden")]
	dung("trang có ô Liên kết để kiểm", len(lk) >= 3)
	la("không ô Liên kết nào thiếu phạm vi", [fn for fn in lk if cdl.loc_lien_ket(fn, "TV") is None], [])
	la("ô lạ không có phạm vi (người gọi phải từ chối)", cdl.loc_lien_ket("o_lien_ket_moi", "TV"), None)
	la("tài khoản chi hoàn tiền: chỉ tài khoản công ty còn dùng", cdl.loc_lien_ket("tk_hoan_tien", "TV"),
		{"company": "TV", "is_company_account": 1, "disabled": 0})
	la("tài khoản BTP: đúng luật tai_khoan_btp.loi_tai_khoan",
		cdl.loc_lien_ket("tk_ton_btp_cap1", "TV"),
		{"company": "TV", "is_group": 0, "disabled": 0, "account_type": "Stock", "account_currency": "VND"})


@ca("Codex #439 V1: hộp chọn Tài khoản chi hoàn tiền chỉ trả tài khoản công ty còn dùng")
def _():
	# Tái hiện trên e067a75: tim_lien_ket gửi bộ lọc rỗng, nên tài khoản ngân hàng
	# của NCC, của khách, tài khoản đã tắt đều hiện trong hộp chọn.
	bg = {"Bank Account": [
		{"name": "MB - TV", "company": "TV", "is_company_account": 1, "disabled": 0},
		{"name": "NCC Bot Mi - VCB", "company": "TV", "is_company_account": 0, "disabled": 0},
		{"name": "OCB cu - TV", "company": "TV", "is_company_account": 1, "disabled": 1},
	]}
	kq, nk = _goi_may_chu(lambda: cdl.tim_lien_ket("tk_hoan_tien"), ban_ghi=bg)
	la("chỉ tài khoản công ty còn dùng", kq, ["MB - TV"])
	la("bộ lọc gửi xuống đúng phạm vi", nk[-1][1], {"company": "TV", "is_company_account": 1, "disabled": 0})


@ca("Codex #439 V1: lưu từ app một giá trị ngoài phạm vi thì máy chủ từ chối, bỏ chọn thì được")
def _():
	tr = _truong_da_xep()
	co = lambda dt, loc: loc["name"] == "MB - TV"
	la("giá trị đúng phạm vi: không lỗi", cdl.kiem_lien_ket(tr, {"tk_hoan_tien": "MB - TV"}, "TV", co), [])
	loi = cdl.kiem_lien_ket(tr, {"tk_hoan_tien": "NCC Bot Mi - VCB"}, "TV", co)
	dung("ngoài phạm vi: báo lỗi có tên giá trị", len(loi) == 1 and "NCC Bot Mi - VCB" in loi[0])
	la("bỏ chọn (chuỗi rỗng): không lỗi", cdl.kiem_lien_ket(tr, {"tk_hoan_tien": ""}, "TV", co), [])
	la("ô không phải Liên kết: không xét", cdl.kiem_lien_ket(tr, {"minvoice_host": "x"}, "TV", co), [])

	class DocGia(dict):
		modified = "m1"
		def get(self, k, d=None):
			return dict.get(self, k, d)
		def set(self, k, v):
			self[k] = v
		def save(self):
			self["_da_luu"] = 1
	d = DocGia()
	bg = {"Bank Account": [{"name": "MB - TV", "company": "TV", "is_company_account": 1, "disabled": 0}]}
	try:
		_goi_may_chu(lambda: cdl.luu(thay='{"tk_hoan_tien": "NCC Bot Mi - VCB"}', modified="m1"), ban_ghi=bg, doc=d)
		dung("luu phải từ chối", False)
	except Exception as e:
		dung("câu từ chối nêu giá trị sai", "NCC Bot Mi - VCB" in str(e))
	dung("không lưu gì", "_da_luu" not in d and "tk_hoan_tien" not in d)
