# -*- coding: utf-8 -*-
"""v672 Google (anh Việt duyệt 18/11/2026 "làm luôn Google Business và Google Merchant").

Ca chốt:
  - Google Merchant: tệp /google-merchant.xml đúng đặc tả Google (RSS 2.0, không gian
    tên g:), chỉ bánh Đặc biệt tuần này và bánh theo mùa, bỏ bánh không giá, không ảnh
    thật (ảnh nền thương hiệu, ảnh riêng tư); đặt trước thì có ngày mở đặt;
  - MỘT NGUỒN: tệp và trang /mon/<mã> cùng đọc mon_dua_google, giá trên trang trùng giá
    trong tệp; mã ngoài danh sách thì 404; một nhóm lỗi không làm mất nhóm kia;
  - đợt Đặc biệt: chưa mở thì đặt trước kèm giờ mở đơn, đã chốt thì hết; thẻ Bánh đang
    ẩn, món đã tắt không lên Google;
  - đường dẫn: /mon/<mã> mở trên tên miền khách, tệp Google mở trên mọi tên miền;
  - Google Posts: kênh "gg" chỉ The Vagabond, bài mới không bật sẵn; một ảnh
    khung 4:3; chữ có số điện thoại thì chặn duyệt và không gửi Google; thân bài có nút
    Đặt hàng; lỗi Google thành việc cần làm; chọn đúng hồ sơ 9 Trần Cao Vân;
  - ba loại Google Posts (Cập nhật, Ưu đãi, Sự kiện, anh Việt 18/11/2026): thân bài đúng
    topicType của Google, Ưu đãi không có nút (Google tự gắn), Ưu đãi và Sự kiện chặn duyệt
    khi thiếu tiêu đề, giờ, giờ kết thúc trước giờ bắt đầu hay trước giờ bài lên; lưu chi
    tiết vào ô riêng, ô xoá trắng giữ trắng; ô Kênh của bảng con nhận mã gg;
  - nối Google: chỉ quản trị hệ thống; mã trạng thái phải của chính người bấm, dùng một
    lần; nối xong lưu mã kết nối mã hoá và hồ sơ.
"""

import ast
import json
import os
import unittest.mock as um
import xml.etree.ElementTree as ET
from urllib.parse import unquote

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import bai_dang as x  # noqa: E402
from vagabond import google_merchant as gm  # noqa: E402
from vagabond import mxh as m  # noqa: E402
from vagabond import ten_mien as tm  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
G = "{http://base.google.com/ns/1.0}"


def _tep(p):
	with open(os.path.join(GOC, p), encoding="utf-8") as f:
		return f.read()


def _mon(**k):
	d = {"ma": "BASS001", "ten": "Bánh Trung thu Chao đỏ", "mo_ta": "", "anh": "/files/chao.jpg", "gia": 350000,
		"con": gm.CON, "nguon": gm.NGUON_MUA}
	d.update(k)
	return d


@ca("v672 Merchant gộp bánh: bỏ bánh không giá, không ảnh thật, không tên; trùng mã thì nhóm trước thắng; ảnh thành đường dẫn đủ")
def _gop():
	ds = gm.gop_mon([
		[_mon(ma="A", nguon=gm.NGUON_DAC_BIET, gia="420000.0"), _mon(ma="B", gia=0), _mon(ma="C", anh=gm.ANH_NEN),
			_mon(ma="D", anh="/private/files/x.jpg"), _mon(ma="E", ten="  ")],
		[_mon(ma="A", gia=1), _mon(ma="F", anh="https://cdn.x/y.jpg")],
	])
	la("chỉ còn A và F", [z["ma"] for z in ds], ["A", "F"])
	la("A giữ giá nhóm đầu", ds[0]["gia"], 420000)
	la("A giữ nguồn Đặc biệt", ds[0]["nguon"], gm.NGUON_DAC_BIET)
	la("ảnh tương đối thành đường dẫn đủ", ds[0]["anh"], "https://thevagabondpatisserie.com/files/chao.jpg")
	dung("mô tả trống thì có câu mặc định nhắc tên bánh", ds[0]["mo_ta"].startswith("Bánh Trung thu Chao đỏ") and "9 Trần Cao Vân" in ds[0]["mo_ta"])
	la("ảnh nền có tham số vẫn bị bỏ", gm.anh_tuyet_doi(gm.ANH_NEN + "?v=1"), "")
	la("ảnh http không an toàn bị bỏ", gm.anh_tuyet_doi("http://x/y.jpg"), "")
	la("đặt trước thiếu giờ mở đặt thì coi là hết (Google bắt có ngày)", gm.gop_mon([[_mon(con=gm.DAT_TRUOC)]])[0]["con"], gm.HET)
	la("tình trạng lạ thì còn hàng", gm.gop_mon([[_mon(con="xyz")]])[0]["con"], gm.CON)


@ca("v672 Merchant tệp XML đúng đặc tả Google: id, giá VND, link trang bánh, ảnh, tình trạng, ngày mở đặt, danh mục Bakery")
def _xml():
	ds = gm.gop_mon([[_mon(ma="BA 1&2", ten="Bánh <đặc biệt> & kem", gia=350000),
		_mon(ma="X2", con=gm.DAT_TRUOC, tu_luc="2026-11-20T08:00", nguon=gm.NGUON_DAC_BIET)]])
	tep = gm.xml_tep(ds)
	goc = ET.fromstring(tep.encode("utf-8"))
	it = goc.findall("./channel/item")
	la("hai bánh", len(it), 2)
	a, b = it
	la("id", a.find(G + "id").text, "BA 1&2")
	la("tên thoát ký tự đặc biệt mà đọc lại đúng", a.find("title").text, "Bánh <đặc biệt> & kem")
	la("giá", a.find(G + "price").text, "350000 VND")
	la("link trang bánh mã hoá đúng", a.find("link").text, "https://thevagabondpatisserie.com/mon/BA%201%262")
	la("còn hàng", a.find(G + "availability").text, "in_stock")
	la("không có ngày mở đặt khi còn hàng", a.find(G + "availability_date"), None)
	la("đặt trước", b.find(G + "availability").text, "preorder")
	la("ngày mở đặt có múi giờ Việt Nam", b.find(G + "availability_date").text, "2026-11-20T08:00+07:00")
	la("danh mục Bakery", a.find(G + "google_product_category").text, "1876")
	la("không có mã vạch", a.find(G + "identifier_exists").text, "no")
	la("nhãn nguồn để lọc trong Merchant", b.find(G + "custom_label_0").text, "dac_biet")
	la("tệp rỗng vẫn hợp lệ", len(ET.fromstring(gm.xml_tep([]).encode()).findall("./channel/item")), 0)


@ca("v672 Merchant trang bánh: dữ liệu có cấu trúc trùng giá và tình trạng của tệp, chữ không làm gãy thẻ script")
def _json_ld():
	mm = gm.gop_mon([[_mon(ten="Bánh </script><script>alert(1)", con=gm.DAT_TRUOC, tu_luc="2026-11-20T08:00")]])[0]
	s = gm.json_ld(mm)
	dung("không còn </script> trần", "</script>" not in s)
	d = json.loads(s)
	la("giá", (d["offers"]["price"], d["offers"]["priceCurrency"]), ("350000", "VND"))
	la("đặt trước", d["offers"]["availability"], "https://schema.org/PreOrder")
	la("ngày mở đặt", d["offers"]["availabilityStarts"], "2026-11-20T08:00+07:00")
	la("chữ tình trạng", gm.chu_tinh_trang(mm), "Mở đặt từ 08:00 ngày 20/11")
	la("giá hiện trên trang", gm.chu_gia(350000), "350.000 ₫")


@ca("v672 Merchant MỘT NGUỒN: tệp Google và trang /mon cùng đọc mon_dua_google; trang chỉ mở mã có trong danh sách")
def _mot_nguon():
	for p in ("vagabond/www/vgb_google_merchant.py", "vagabond/www/mon.py"):
		goi = [n.func.attr for n in ast.walk(ast.parse(_tep(p))) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
		dung("%s đọc mon_dua_google" % p, "mon_dua_google" in goi)
	mon = _tep("vagabond/www/mon.py")
	dung("trang tìm đúng mã trong danh sách, không có thì 404", "gm.tim(gm.mon_dua_google(), ma)" in mon and "PageDoesNotExistError" in mon)
	dung("trang lấy giá từ cùng bản ghi", 'gm.chu_gia(m["gia"])' in mon)
	la("tìm mã", gm.tim([{"ma": "A"}, {"ma": "B"}], " B ")["ma"], "B")
	la("mã lạ", gm.tim([{"ma": "A"}], "Z"), None)
	h = _tep("vagabond/hooks.py")
	dung("luật đường tệp Google", '{"from_route": "/google-merchant.xml", "to_route": "vgb-google-merchant.xml"}' in h)
	dung("luật đường trang bánh", '{"from_route": "/mon/<ma>", "to_route": "mon"}' in h)


@ca("v672 Merchant gom nhóm: một nhóm lỗi không làm mất nhóm kia; nội dung Marketing sửa ở Trang từng bánh được dùng")
def _gom():
	def hong():
		raise RuntimeError("Pancake hỏng")
	with um.patch.object(gm, "_dac_biet", hong), \
			um.patch.object(gm, "_theo_mua", lambda: [_mon(ma="M1")]), \
			um.patch.object(gm, "_noi_dung_ma", lambda: {"M1": {"ten": "Chao đỏ hộp 4", "mo_ta": "Bốn bánh"}}):
		ds = gm.mon_dua_google(lam_moi=True)
	la("nhóm theo mùa vẫn lên", [z["ma"] for z in ds], ["M1"])
	la("tên Marketing sửa", ds[0]["ten"], "Chao đỏ hộp 4")
	la("mô tả Marketing sửa", ds[0]["mo_ta"], "Bốn bánh")


class _D(dict):
	__getattr__ = dict.get


@ca("v672 Merchant Đặc biệt tuần này: mở đặt thì còn hàng, chưa mở thì đặt trước kèm giờ mở, đã chốt thì hết; thẻ ẩn, món tắt bị bỏ")
def _dac_biet():
	from vagabond import banh_web, dac_biet_tuan as dbt
	dot = {"mo_don": "2026-11-20T08:00", "chot_don": "2026-11-21T20:00",
		"mon_dt": [{"khoa": "very berry", "mo_ta": "Dâu rừng", "anh": ""}, {"khoa": "an", "mo_ta": "", "anh": ""}]}
	the = [_D(khoa="very berry", ten="Very Berry", trang_thai=banh_web.DANG_HIEN, anh='[{"url": "/files/vb.jpg"}]', mo_ta="", ma_hang="VB16\nVB18"),
		_D(khoa="an", ten="Ẩn", trang_thai=banh_web.DA_AN, anh='[{"url": "/files/an.jpg"}]', mo_ta="", ma_hang="AN1")]
	item = [_D(item_code="VB16", item_name="Very Berry, size 16cm", standard_rate=520000, disabled=0, is_sales_item=1),
		_D(item_code="VB18", item_name="Very Berry, size 18cm", standard_rate=680000, disabled=1, is_sales_item=1),
		_D(item_code="AN1", item_name="Ẩn", standard_rate=1, disabled=0, is_sales_item=1)]
	ks = types_kiem_banh()

	def get_all(dt, **k):
		return the if dt == banh_web.DT else item
	for luc, mong, tu in (("2026-11-20T09:00", gm.CON, ""), ("2026-11-19T09:00", gm.DAT_TRUOC, "2026-11-20T08:00"),
			("2026-11-22T09:00", gm.HET, "")):
		with um.patch.object(dbt, "dot_cong_khai", lambda: dot), um.patch.object(dbt, "luc_vn", lambda luc=luc: luc), \
				um.patch.object(gm_frappe(), "get_all", get_all, create=True), um.patch.dict("sys.modules", {"vagabond.kiem_banh": ks}):
			ds = gm._dac_biet()
		la("lúc %s chỉ size 16 của thẻ đang hiện" % luc, [z["ma"] for z in ds], ["VB16"])
		la("lúc %s tình trạng" % luc, (ds[0]["con"], ds[0]["tu_luc"]), (mong, tu))
	la("tên kèm size", ds[0]["ten"], "Very Berry 16cm")
	la("mô tả của đợt", ds[0]["mo_ta"], "Dâu rừng")
	la("ảnh của thẻ", ds[0]["anh"], "/files/vb.jpg")


def gm_frappe():
	import frappe
	return frappe


def types_kiem_banh():
	import re
	import types
	ks = types.ModuleType("vagabond.kiem_banh")
	ks._tach_ten_size = lambda t: (t, int((re.search(r"(\d+)cm", t) or [0, 0])[1]))
	return ks


@ca("v672 tên miền: /mon/<mã> mở trên tên miền khách, đá về app khi vào nhầm miền app; tệp Google mở trên mọi miền")
def _ten_mien():
	la("miền chính", tm.dich_chuyen_huong(tm.MIEN_CHINH, "/mon/BASS001"), "")
	la("miền app đá về /bep", tm.dich_chuyen_huong(tm.MIEN_APP, "/mon/BASS001"), "/bep")
	la("tệp Google trên miền chính", tm.dich_chuyen_huong(tm.MIEN_CHINH, "/google-merchant.xml"), "")
	la("tệp Google trên miền app", tm.dich_chuyen_huong(tm.MIEN_APP, "/google-merchant.xml"), "")
	la("màn Món đi kèm của app không bị nhầm là trang bánh", tm.dich_chuyen_huong(tm.MIEN_CHINH, "/mon-di-kem"), "")


@ca("v672 Google Posts: kênh gg chỉ The Vagabond; bài mới không bật sẵn; nhập tệp gõ 'Google' nhận ra kênh")
def _kenh():
	dung("The Vagabond có gg", "gg" in x.KENH_HIEU[x.HIEU_VGB])
	dung("Sonneto không có gg", "gg" not in x.KENH_HIEU[x.HIEU_SO])
	dung("gg tự đăng được", "gg" in x.KENH_TU_DONG)
	dung("bài mới không bật sẵn gg", "gg" not in x.KENH_MAC_DINH)
	la("kênh của thương hiệu Sonneto bỏ gg", x.kenh_cua_hieu("fb,gg", hieu=x.HIEU_SO), ["fb"])
	la("ô Kênh gõ tay", x.doc_kenh_chu("Facebook, Google"), ["fb", "gg"])
	la("Story không có gg", x.chuan_kenh("fb,gg", x.KIEU_STORY), ["fb"])
	la("AI cắt chữ gg ở 1.500", len(x.doc_tra_loi_ai(json.dumps({"gg": {"chu": "a" * 2000}}), ["gg"])["gg"]["chu"]), 1500)
	dung("lời dặn AI có luật kênh gg", "gg (Google Posts)" in x.LOI_DAN_AI and "không số điện thoại" in x.LOI_DAN_AI)
	dung("lời dặn Sonneto cùng khối TỪNG KÊNH (máy chủ bỏ gg khỏi kênh Sonneto)", "gg (Google Posts)" in x.LOI_DAN_SO)


@ca("v672 Google Posts: một ảnh khung 4:3; nhiều ảnh thì báo chỉ đăng ảnh đầu, không chặn; số điện thoại thì chặn duyệt")
def _kiem():
	anh = [{"url": "/f/1.jpg", "khung": "4:3"}, {"url": "/f/2.jpg", "khung": "4:5"}, {"url": "/f/3.jpg", "khung": "1:1"}]
	la("ảnh cho gg", x.anh_cho_kenh(anh, "gg"), [{"ten": None, "url": "/f/1.jpg", "khung": "4:3", "cat": False}])
	la("ảnh 4:3 nhận ra khung", x.doc_khung(1200, 900), "4:3")
	k = x.kiem_bai({"kieu": x.KIEU_BAI, "kenh_chon": "gg", "anh": anh, "ban": {"gg": {"chu": "Bánh mới ra lò."}}}, None)
	dung("không chặn", not [z for z in k if z["muc"] == "chan"])
	dung("báo chỉ ảnh đầu", any("ảnh đầu tiên" in z["chu"] for z in k))
	k2 = x.kiem_bai({"kieu": x.KIEU_BAI, "kenh_chon": "gg,fb", "anh": anh[:1],
		"ban": {"gg": {"chu": "Gọi 0901 234 567 đặt bánh"}, "fb": {"chu": "Gọi 0901 234 567 đặt bánh"}}}, None)
	chan = [z for z in k2 if z["muc"] == "chan"]
	la("chặn đúng kênh gg", [z["chu"] for z in chan], ["Chữ Google Posts có số điện thoại"])
	la("nút sửa chữ gg", chan[0]["nut"], ["chu:gg", "Sửa chữ"])
	for chu, mong in (("Hotline +84 28 3822 1234", True), ("0283.822.1234", True), ("Giá 350000 đồng", False),
			("Ngày 20/11/2026, size 16cm", False), ("Mã BAWC00104", False)):
		la("số điện thoại: %s" % chu, m.co_so_dien_thoai(chu), mong)


@ca("v672 Google Posts đăng: thân bài có nút Đặt hàng và một ảnh; số điện thoại không gửi Google; Sonneto không có kênh gg")
def _dang():
	cfg = {"gg_client_id": "ID", "gg_client_secret": "S", "gg_refresh_token": "R", "gg_dia_diem": "accounts/1/locations/2",
		"gg_ten_dia_diem": "The Vagabond"}
	goi = []

	def goi_gg(pt, url, tok=None, than=None, **k):
		goi.append((pt, url, tok, than, k.get("cong_bo")))
		return {"name": "accounts/1/locations/2/localPosts/9", "searchUrl": "https://local.google.com/p/9"}
	with um.patch.object(m, "_cfg", lambda: cfg), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
			um.patch.object(m, "_gg_token", lambda c: "TOK"), um.patch.object(m, "_goi_gg", goi_gg), \
			um.patch.object(m, "anh_jpeg", lambda u, k=None, t=None: b"J"), \
			um.patch.object(m, "url_cong_khai", lambda ma, nd: "https://app/files/bd.jpg"):
		la("trả mã bài và link", m.dang("gg", "BD-1", "Bánh mới", [{"url": "/f/1.jpg", "khung": "4:3", "cat": True}]),
			("accounts/1/locations/2/localPosts/9", "https://local.google.com/p/9"))
		pt, url, tok, than, cb = goi[-1]
		la("đúng đường localPosts của hồ sơ", (pt, url, tok, cb), ("POST", m.GG_BAI + "/accounts/1/locations/2/localPosts", "TOK", True))
		la("nút Đặt hàng mở trang đặt bánh", than["callToAction"], {"actionType": "ORDER", "url": "https://thevagabondpatisserie.com/banh"})
		la("một ảnh", than["media"], [{"mediaFormat": "PHOTO", "sourceUrl": "https://app/files/bd.jpg"}])
		la("tiếng Việt", than["languageCode"], "vi")
		n = len(goi)
		nem("chữ có số điện thoại không gửi", lambda: m.dang("gg", "BD-1", "Gọi 0901234567", []), m.LoiDang)
		la("không gọi Google", len(goi), n)
		nem("Sonneto không có kênh gg", lambda: m.dang("gg", "BD-1", "x", [], hieu="sonneto"), m.LoiDang)
		dung("bài không ảnh thì không gửi media", "media" not in m.than_bai_gg("x", ""))
	with um.patch.object(m, "_cfg", lambda: {}), um.patch.object(m, "_khoa", lambda c, o: ""):
		nem("chưa nối thì đăng tay", lambda: m.dang("gg", "BD-1", "x", []), m.LoiDang)


@ca("v672 Google Posts: lỗi Google thành việc cần làm; chọn đúng hồ sơ 9 Trần Cao Vân")
def _loi_chon():
	dung("mã kết nối hết hiệu lực", "Kết nối Google lại" in m.loi_gg_de_hieu(400, {"error": "invalid_grant"}))
	dung("sai khoá ứng dụng", "Khoá ứng dụng" in m.loi_gg_de_hieu(401, {"error": "invalid_client"}))
	dung("401 API", "Kết nối Google lại" in m.loi_gg_de_hieu(401, {"error": {"status": "UNAUTHENTICATED"}}))
	dung("hạn mức 0 khi chưa được duyệt API", "chờ Google duyệt" in m.loi_gg_de_hieu(429, {"error": {"status": "RESOURCE_EXHAUSTED"}}))
	dung("không có quyền", "không quản lý địa điểm" in m.loi_gg_de_hieu(403, {"error": {"status": "PERMISSION_DENIED"}}))
	dung("lỗi khác kèm câu Google", "từ chối bài: Bad" in m.loi_gg_de_hieu(400, {"error": {"message": "Bad"}}))
	tcv = {"ma": "accounts/1/locations/1", "ten": "The Vagabond Pâtisserie & Café", "dia_chi": "9 Trần Cao Vân Quận 1"}
	so = {"ma": "accounts/1/locations/2", "ten": "Sonneto Lab", "dia_chi": "307/1 Nguyễn Văn Trỗi Tân Bình"}
	la("một hồ sơ thì lấy luôn", m.chon_dia_diem([so])[0], so)
	la("hai hồ sơ lấy hồ sơ Trần Cao Vân", m.chon_dia_diem([so, tcv])[0], tcv)
	d, loi = m.chon_dia_diem([so, dict(so, ma="accounts/1/locations/3")])
	dung("không nhận ra thì báo, không đoán", d is None and "2 hồ sơ" in loi)
	dung("không hồ sơ nào", m.chon_dia_diem([])[0] is None)
	u = m.url_duyet_gg("ID", "TT")
	dung("xin mã dài hạn, hỏi đồng ý lại, đúng phạm vi và đường về", all(z in u for z in (
		"access_type=offline", "prompt=consent", "business.manage", "state=TT",
		"redirect_uri=https%3A%2F%2Fapp.thevagabondpatisserie.com%2Fapi%2Fmethod%2Fvagabond.mxh.gg_ket_noi_xong")))


@ca("v672 nối Google: chỉ quản trị hệ thống; mã trạng thái phải của chính người bấm, dùng một lần; nối xong lưu mã kết nối và hồ sơ")
def _noi():
	import frappe
	bo = {}
	cache = type("C", (), {"get_value": lambda s, k: bo.get(k), "set_value": lambda s, k, v, **kw: bo.__setitem__(k, v),
		"delete_value": lambda s, k: bo.pop(k, None)})()
	luu, dat = [], {}
	pw = type("M", (), {})()
	pw.set_encrypted_password = lambda dt, ten, gt, o: luu.append((o, gt))
	cfg = {"gg_client_id": "ID", "gg_client_secret": "S"}
	with um.patch.object(frappe, "cache", lambda: cache), um.patch.object(frappe, "get_roles", lambda *a: ["Marketing"]):
		nem("Marketing không được nối", m.gg_bat_dau, Exception)
	with um.patch.object(frappe, "cache", lambda: cache), um.patch.object(frappe, "get_roles", lambda *a: ["System Manager"]), \
			um.patch.object(m, "_cfg", lambda: cfg), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
			um.patch.dict("sys.modules", {"frappe.utils.password": pw}), \
			um.patch.object(frappe.db, "set_single_value", lambda dt, o, v: dat.__setitem__(o, v), create=True), \
			um.patch.object(frappe.local, "response", {}, create=True), \
			um.patch.object(m, "_gg_doi_ma", lambda c, **k: {"refresh_token": "RT", "access_token": "AT"}), \
			um.patch.object(m, "_gg_ds_dia_diem", lambda tok: [{"ma": "accounts/1/locations/1", "ten": "The Vagabond", "dia_chi": "9 Tran Cao Van"}]), \
			um.patch.object(m, "_gg_token", lambda c: "AT"):
		u = m.gg_bat_dau()["url"]
		tt = u.split("state=")[1].split("&")[0]
		la("mã trạng thái gắn người bấm", bo[m.GG_KHOA_TRANG_THAI + tt], frappe.session.user)
		with um.patch.object(frappe.session, "user", "khac@vagabond"):
			m.gg_ket_noi_xong(code="C", state=tt)
		dung("người khác dùng mã trạng thái: không lưu", not luu and "không phải của bạn" in unquote(frappe.local.response["location"]))
		m.gg_ket_noi_xong(code="C", state="la")
		dung("mã trạng thái lạ: không lưu", not luu)
		m.gg_ket_noi_xong(code="C", state=tt)
		la("lưu mã kết nối mã hoá", luu, [("gg_refresh_token", "RT")])
		la("lưu hồ sơ", (dat.get("gg_dia_diem"), dat.get("gg_ten_dia_diem")), ("accounts/1/locations/1", "The Vagabond"))
		dung("đưa về màn Bài đăng kèm câu báo", frappe.local.response["location"].startswith(m.GG_MAN_VE + "?gg=")
			and frappe.local.response["type"] == "redirect")
		m.gg_ket_noi_xong(code="C", state=tt)
		la("mã trạng thái dùng một lần", len(luu), 1)


@ca("v672 Google Posts trạng thái kết nối: chưa dán mã thì đăng tay; nối được thì tự đăng; token hỏng thì báo lỗi")
def _trang_thai():
	cfg = {"gg_client_id": "ID", "gg_client_secret": "S", "gg_refresh_token": "R", "gg_dia_diem": "accounts/1/locations/2",
		"gg_ten_dia_diem": "The Vagabond Pâtisserie"}

	def hong(c):
		raise m.LoiDang(m.CAU_NOI_LAI_GG)
	for c, tok, mong in (({}, lambda c: "T", 0), (cfg, lambda c: "T", 1), (cfg, hong, 0)):
		with um.patch.object(m, "_cfg", lambda c=c: c), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
				um.patch.object(m, "_gg_token", tok):
			la("trạng thái %s" % mong, m.trang_thai(True)["gg"]["ok"], mong)
	with um.patch.object(m, "_cfg", lambda: cfg), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
			um.patch.object(m, "_gg_token", hong):
		la("lỗi có câu nối lại", m.trang_thai(True)["gg"], {"ok": 0, "chu": m.CAU_NOI_LAI_GG, "loi": 1})
	with um.patch.object(m, "_cfg", lambda: cfg), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""):
		dung("Sonneto: gg không nối", m.trang_thai(True, "sonneto")["gg"]["ok"] == 0)


@ca("v672 Google Posts ba loại: thân bài đúng topicType, lịch theo giờ Việt Nam, Ưu đãi không gắn nút và có mã giảm giá")
def _ba_loai():
	la("Cập nhật", (m.than_bai_gg("a", "", ct={"loai": "cap_nhat"})["topicType"], "event" in m.than_bai_gg("a", "")), ("STANDARD", False))
	ev = m.than_bai_gg("a", "", ct={"loai": "su_kien", "tieu_de": "Workshop bánh Trung thu", "bat_dau": "2026-11-20T08:00",
		"ket_thuc": "2026-11-21T17:30"})
	la("Sự kiện", ev["topicType"], "EVENT")
	la("lịch sự kiện", ev["event"], {"title": "Workshop bánh Trung thu", "schedule": {
		"startDate": {"year": 2026, "month": 11, "day": 20}, "startTime": {"hours": 8, "minutes": 0},
		"endDate": {"year": 2026, "month": 11, "day": 21}, "endTime": {"hours": 17, "minutes": 30}}})
	dung("Sự kiện có nút Đặt hàng", ev["callToAction"]["actionType"] == "ORDER")
	uu = m.than_bai_gg("a", "", ct={"loai": "uu_dai", "tieu_de": "Giảm 10% bánh ổ", "bat_dau": "2026-11-20T08:00",
		"ket_thuc": "2026-11-30T22:00", "ma_giam": "VGB10", "dieu_khoan": "Áp dụng đơn online"})
	la("Ưu đãi", uu["topicType"], "OFFER")
	dung("Ưu đãi không có nút (Google tự gắn)", "callToAction" not in uu)
	la("mã và điều khoản", uu["offer"], {"redeemOnlineUrl": m.GG_LINK_DAT, "couponCode": "VGB10", "termsConditions": "Áp dụng đơn online"})
	dung("Ưu đãi không mã thì không gửi mã rỗng", "couponCode" not in m.than_bai_gg("a", "", ct={"loai": "uu_dai", "tieu_de": "x",
		"bat_dau": "2026-11-20T08:00", "ket_thuc": "2026-11-21T08:00"})["offer"])
	la("loại lạ thành Cập nhật", m.than_bai_gg("a", "", ct={"loai": "abc"})["topicType"], "STANDARD")


@ca("v672 Google Posts Ưu đãi, Sự kiện: bảng Kiểm chặn thiếu tiêu đề, thiếu giờ, giờ ngược, đã kết thúc trước giờ bài lên, tiêu đề quá 58")
def _kiem_loai():
	import datetime as dtm
	now = dtm.datetime(2026, 11, 18, 10, 0)
	def k(gg, hen=None):
		return [z["chu"] for z in x.kiem_gg(gg, now, hen)]
	la("Cập nhật không cần gì", k({"loai": "cap_nhat"}), [])
	la("thiếu tiêu đề và giờ", k({"loai": "su_kien"}), ["Sự kiện Google Posts chưa có tiêu đề", "Sự kiện Google Posts chưa có giờ bắt đầu và kết thúc"])
	la("giờ ngược", k({"loai": "uu_dai", "tieu_de": "x", "bat_dau": "2026-11-21T08:00", "ket_thuc": "2026-11-20T08:00"}),
		["Giờ kết thúc ưu đãi phải sau giờ bắt đầu"])
	la("đã kết thúc trước giờ hẹn đăng", k({"loai": "su_kien", "tieu_de": "x", "bat_dau": "2026-11-19T08:00", "ket_thuc": "2026-11-20T08:00"},
		"2026-11-20 09:00"), ["Sự kiện đã kết thúc trước giờ bài lên"])
	la("hợp lệ", k({"loai": "su_kien", "tieu_de": "x", "bat_dau": "2026-11-19T08:00", "ket_thuc": "2026-11-20T08:00"}), [])
	la("tiêu đề quá 58", k({"loai": "uu_dai", "tieu_de": "a" * 59, "bat_dau": "2026-11-19T08:00", "ket_thuc": "2026-11-20T08:00"}),
		["Tiêu đề ưu đãi dài 59/58 ký tự"])
	b = x.kiem_bai({"kieu": x.KIEU_BAI, "kenh_chon": "gg", "anh": [{"url": "/f/1.jpg", "khung": "4:3"}],
		"ban": {"gg": {"chu": "Bánh mới", "loai": "su_kien"}}}, now)
	dung("bảng Kiểm của bài chặn Sự kiện thiếu giờ", any(z["muc"] == "chan" and "chưa có giờ" in z["chu"] for z in b))


@ca("v672 Google Posts lưu chi tiết: gộp ô vừa sửa, ô xoá trắng giữ trắng, giờ sai dạng bỏ, đọc lại đúng loại")
def _luu_gg():
	cu = x.ap_gg("", {"loai": "uu_dai", "bat_dau": "2026-11-20 08:00:00", "ket_thuc": "2026-11-21T08:00", "ma_giam": "  VGB 10 "})
	la("chuẩn hoá", json.loads(cu), {"loai": "uu_dai", "bat_dau": "2026-11-20T08:00", "ket_thuc": "2026-11-21T08:00", "ma_giam": "VGB 10", "dieu_khoan": ""})
	moi = json.loads(x.ap_gg(cu, {"ma_giam": ""}))
	la("xoá trắng mã giữ trắng, ô khác giữ nguyên", (moi["ma_giam"], moi["loai"], moi["bat_dau"]), ("", "uu_dai", "2026-11-20T08:00"))
	la("giờ sai dạng bỏ", json.loads(x.ap_gg(cu, {"ket_thuc": "mai"}))["ket_thuc"], "")
	la("chi tiết hỏng đọc ra Cập nhật", x.chuan_gg("{hỏng")["loai"], "cap_nhat")
	r = _D(ma_kenh="gg", chu="c", tieu_de="Giảm 10%", ai_soan=0, chi_tiet=cu)
	r.get = lambda k, d=None: dict.get(r, k, d)
	doc = _D(kenh=[r]); doc.get = lambda k, d=None: dict.get(doc, k, d)
	ban = x._ban_doc(doc)["gg"]
	la("đọc lại cho màn", (ban["loai"], ban["tieu_de"], ban["ma_giam"]), ("uu_dai", "Giảm 10%", "VGB 10"))
	la("đăng gửi đủ chi tiết", m.than_bai_gg(ban["chu"], "", ct=ban)["offer"]["couponCode"], "VGB 10")


@ca("v672 Google Posts: ô Kênh của bảng con nhận mọi mã kênh (Frappe từ chối mã ngoài danh sách khi lưu); JS và máy chủ cùng ba loại")
def _cot_kenh():
	d = json.loads(_tep("vagabond/vagabond/doctype/vagabond_bai_dang_kenh/vagabond_bai_dang_kenh.json"))
	o = [f for f in d["fields"] if f["fieldname"] == "ma_kenh"][0]["options"].split("\n")
	la("mọi mã trong KENH có trong ô Kênh", sorted(set(x.KENH) - set(o)), [])
	dung("có cột chi tiết", any(f["fieldname"] == "chi_tiet" for f in d["fields"]) and "chi_tiet" in d["field_order"])
	js = _tep("vagabond/public/js/bep/75-bai-dang.js")
	import re
	la("ba loại JS trùng máy chủ", re.findall(r"\{ k: '(cap_nhat|uu_dai|su_kien)', ten: '([^']+)'", js), list(x.GG_LOAI))
	m2 = um.MagicMock()
	with um.patch.object(m, "_cfg", lambda: {"gg_client_id": "I", "gg_client_secret": "S", "gg_refresh_token": "R"}), \
			um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), um.patch.object(m, "_goi_gg", m2):
		nem("Sự kiện thiếu giờ không gửi Google", lambda: m.dang("gg", "BD", "x", [], chi_tiet={"loai": "su_kien", "tieu_de": "t"}), m.LoiDang)
	dung("không gọi Google", not m2.called)



@ca("v672 lượt đăng Google Posts: kênh gg nhận đủ chi tiết Ưu đãi đã lưu; kênh khác không nhận thêm gì")
def _luot_gg():
	from vagabond.khung.kiem_thu import thu_bai_dang_664 as t4
	ct = x.ap_gg("", {"loai": "uu_dai", "bat_dau": "2026-11-20T08:00", "ket_thuc": "2026-11-21T08:00", "ma_giam": "VGB10"})
	doc = t4._da_duyet(kenh_chon="fb,gg", kenh=[
		t4._Dong(ma_kenh="fb", chu="Bánh fb", trang_thai=x.K_HEN, tu_dong=1),
		t4._Dong(ma_kenh="gg", chu="Bánh gg", tieu_de="Giảm 10%", chi_tiet=ct, trang_thai=x.K_HEN, tu_dong=1)])
	_, n = t4._chay(doc, x.dang_bai, noi={"fb", "gg"}, ma=doc.name)
	them = dict(n.get("them") or [])
	la("Facebook không nhận chi tiết", them.get("fb"), {})
	g = (them.get("gg") or {}).get("chi_tiet") or {}
	la("Google Posts nhận loại, tiêu đề, giờ, mã", (g.get("loai"), g.get("tieu_de"), g.get("bat_dau"), g.get("ma_giam")),
		("uu_dai", "Giảm 10%", "2026-11-20T08:00", "VGB10"))
	la("hai kênh Đã đăng", t4._tt(doc), [("fb", x.K_XONG), ("gg", x.K_XONG)])


@ca("v672 Merchant (Codex #587): bánh Đặc biệt hết suất khi đợt vẫn mở thì hết hàng trên Google, khớp trang đặt bánh khoá món")
def _het_suat():
	la("đợt mở, còn suất", gm.con_theo_suat(gm.CON, "2", 1), gm.CON)
	la("đợt mở, hết suất", gm.con_theo_suat(gm.CON, "2", 2), gm.HET)
	la("không giới hạn", gm.con_theo_suat(gm.CON, "", 99), gm.CON)
	la("đợt chưa mở giữ đặt trước", gm.con_theo_suat(gm.DAT_TRUOC, "2", 0), gm.DAT_TRUOC)
	from vagabond import banh_web, dac_biet_tuan as dbt
	dot = {"mo_don": "2026-11-20T08:00", "chot_don": "2026-11-21T20:00",
		"mon_dt": [{"khoa": "a", "mo_ta": "", "anh": "", "toi_da": "2"}, {"khoa": "b", "mo_ta": "", "anh": "", "toi_da": ""}]}
	the = [_D(khoa="a", ten="A", trang_thai=banh_web.DANG_HIEN, anh='[{"url": "/files/a.jpg"}]', mo_ta="", ma_hang="A1"),
		_D(khoa="b", ten="B", trang_thai=banh_web.DANG_HIEN, anh='[{"url": "/files/b.jpg"}]', mo_ta="", ma_hang="B1")]
	item = [_D(item_code="A1", item_name="A", standard_rate=1, disabled=0, is_sales_item=1),
		_D(item_code="B1", item_name="B", standard_rate=1, disabled=0, is_sales_item=1)]
	with um.patch.object(dbt, "dot_cong_khai", lambda: dot), um.patch.object(dbt, "luc_vn", lambda: "2026-11-20T09:00"), \
			um.patch.object(dbt, "ma_theo_khoa", lambda d: {"a": {"A1"}, "b": {"B1"}}), \
			um.patch.object(dbt, "da_dat", lambda d, mk: {"a": 2, "b": 50}), \
			um.patch.object(gm_frappe(), "get_all", lambda dt, **k: the if dt == banh_web.DT else item, create=True), \
			um.patch.dict("sys.modules", {"vagabond.kiem_banh": types_kiem_banh()}):
		ds = gm._dac_biet()
	la("A hết suất, B không giới hạn còn hàng", [(z["ma"], z["con"]) for z in ds], [("A1", gm.HET), ("B1", gm.CON)])
