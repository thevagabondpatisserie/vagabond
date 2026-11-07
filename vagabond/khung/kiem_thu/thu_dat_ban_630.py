# -*- coding: utf-8 -*-
"""v630: trang khách Đặt bàn kiểu mới (anh Việt duyệt mẫu 3, 02/11/2026).

Trang cần thêm ba thứ từ máy chủ, đều qua dat_ban.cau_hinh (không thêm cửa mới):
  - khung_gio_hom_nay: giờ hôm nay còn nhận đặt, CÙNG luật máy chủ chặn lúc gửi
    (qua_han_nhan), để trang không mời khách bấm một giờ sẽ bị từ chối;
  - giờ mở cửa hôm nay và Đang mở / Đã đóng, đọc chữ marketing gõ ở thẻ Cửa hàng;
  - nút Chỉ đường, Gọi, Nhắn Zalo: chỉ khi có dữ liệu và link là https.
Các ca chạy phép THẬT; cau_hinh chạy trên Frappe giả với dữ liệu thẻ Cửa hàng giả.
Ca hành vi node nạp thật trang (hanh_vi/dat_ban_630.js) chạy ở cuối.
"""

import hashlib
import html
import json
import re
import subprocess
import sys
import types
from datetime import datetime
from pathlib import Path
from unittest import mock

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import dat_ban as db  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
THU2 = datetime(2026, 11, 2, 13, 30)  # thứ Hai


@ca("v630 giờ hôm nay còn nhận: đúng mốc 60 phút là hết, trang và máy chủ cùng một luật")
def _con_nhan():
	khung = ["09:00", "14:00", "14:30", "14:31", "18:00", "sai"]
	la("còn nhận", db.khung_con_nhan(khung, "2026-11-02", THU2), ["14:31", "18:00"])
	la("ngày mai còn hết", db.khung_con_nhan(khung, "2026-11-03", THU2), ["09:00", "14:00", "14:30", "14:31", "18:00"])
	cau = dict(bat=True, co_so="TCV", khung_gio=khung[:5], toi_da_khach=8, toi_da_ngay=30)
	for g in khung[:5]:
		nd = dict(ten="Khách", sdt="0912345678", co_so="TCV", ngay="2026-11-02", gio=g, so_khach=2)
		try:
			db.chuan_hoa(nd, cau, THU2)
			nhan = True
		except ValueError:
			nhan = False
		la("máy chủ nhận " + g + " khớp trang", nhan, g in db.khung_con_nhan(khung, "2026-11-02", THU2))


@ca("v630 giờ mở cửa: đọc các cách marketing hay gõ, không đọc được thì không đoán")
def _mo_cua():
	hai_dong = "Thứ 2 - Thứ 6: 7:00 - 21:00\nThứ 7, Chủ nhật: 7:30 - 22:00"
	la("thứ Hai trong giờ", db.mo_cua(hai_dong, THU2), {"dang_mo": True, "gio": "7:00 - 21:00"})
	la("chủ nhật dòng hai", db.mo_cua(hai_dong, datetime(2026, 11, 8, 22, 0)), {"dang_mo": False, "gio": "7:30 - 22:00"})
	la("mỗi ngày", db.mo_cua("9:00 - 21:00 mỗi ngày", datetime(2026, 11, 2, 8, 59)), {"dang_mo": False, "gio": "9:00 - 21:00"})
	la("chữ h", db.mo_cua("Hằng ngày 9h - 21h30", datetime(2026, 11, 2, 21, 29)), {"dang_mo": True, "gio": "9:00 - 21:30"})
	la("Thứ 2 - 6 là tới thứ Sáu", db.mo_cua("Thứ 2 - 6: 8:00 - 22:00", datetime(2026, 11, 6, 10)), {"dang_mo": True, "gio": "8:00 - 22:00"})
	la("thứ Bảy không mở", db.mo_cua("Thứ 2 - 6: 8:00 - 22:00", datetime(2026, 11, 7, 10)), {"dang_mo": False, "gio": ""})
	la("T3-CN vòng qua tuần, thứ Hai nghỉ", db.mo_cua("T3-CN: 9:00 - 21:00", THU2), {"dang_mo": False, "gio": ""})
	la("qua nửa đêm", db.mo_cua("18:00 - 02:00", datetime(2026, 11, 2, 1, 0)), {"dang_mo": True, "gio": "18:00 - 2:00"})
	for x in ("", None, "Lễ Tết nghỉ", "Thứ 2 - 6", "Gọi trước 30 phút"):
		la("không đoán: " + repr(x), db.mo_cua(x, THU2), None)


@ca("v630 thẻ Cửa hàng ứng với cơ sở đặt bàn: theo tên, không có thì theo số nhà và đường")
def _tim_cua_hang():
	ds = [{"ten": "Bếp Tân Sơn Hoà", "dia_chi": "307/1 Nguyễn Văn Trỗi"}, {"ten": "Cửa hàng Sài Gòn", "dia_chi": "9 Trần Cao Vân, P. Sài Gòn"}, "rác"]
	la("theo địa chỉ", db.tim_cua_hang(ds, "The Vagabond District 1", "9 Tran Cao Van, Quận 1")["ten"], "Cửa hàng Sài Gòn")
	la("theo tên", db.tim_cua_hang(ds, "Bếp Tân Sơn Hòa", "")["ten"], "Bếp Tân Sơn Hoà")
	la("không khớp", db.tim_cua_hang(ds, "NVHTN", "21 Phạm Ngọc Thạch"), None)
	la("rỗng", db.tim_cua_hang(None, "", ""), None)


@ca("v630 phần cửa hàng trên trang: ô nào thiếu hoặc link không an toàn thì không có khoá")
def _thong_tin():
	ch = {"hotline": "", "chi_duong": "https://maps.app.goo.gl/x", "gio_mo_cua": "9:00 - 21:00 mỗi ngày"}
	lh = {"dien_thoai": "0931 224 334", "zalo": "https://zalo.me/0931224334"}
	la("đủ", db.thong_tin_trang(ch, lh, THU2), {"hotline": "0931 224 334", "hotline_so": "0931224334", "chi_duong": "https://maps.app.goo.gl/x",
		"zalo": "https://zalo.me/0931224334", "dang_mo": True, "gio_hom_nay": "9:00 - 21:00"})
	la("hotline cửa hàng thắng số chung", db.thong_tin_trang(dict(ch, hotline="028 3823 4567"), lh, THU2)["hotline_so"], "02838234567")
	xau = db.thong_tin_trang({"chi_duong": "javascript:alert(1)", "gio_mo_cua": "liên hệ"}, {"dien_thoai": "12", "zalo": "http://zalo.me/1"}, THU2)
	la("bỏ hết ô xấu", xau, {})
	la("không có gì", db.thong_tin_trang(None, None, THU2), {})
	for u in ("https://a.vn/x y", "https://user@a.vn", "https:///x", " https://a.vn "):
		la("link " + repr(u), db.link_an_toan(u), "https://a.vn" if u == " https://a.vn " else "")


@ca("v630 cau_hinh trả đủ khoá trang cần, đọc thẻ Cửa hàng đã xuất bản; lỗi đọc thì vẫn nhận đặt bàn")
def _cau_hinh():
	ch = {"bat": True, "co_so": "TCV", "ten_co_so": "The Vagabond District 1", "dia_chi": "9 Trần Cao Vân, Quận 1",
		"khung_gio": ["09:00", "18:00"], "khu_vuc": [], "dip": [], "toi_da_khach": 8, "toi_da_ngay": 30, "anh": "/assets/vagabond/images/quay-tcv.jpg"}
	from vagabond import noi_dung_web, don_web
	ban = {"thong_tin": {"cua_hang": [{"id": "cua-hang-sai-gon", "ten": "Cửa hàng Sài Gòn", "dia_chi": "9 Trần Cao Vân, P. Sài Gòn",
		"gio_mo_cua": "Thứ 2 - Chủ nhật: 9:00 - 21:00", "hotline": "", "chi_duong": "https://maps.app.goo.gl/x"}]}}
	loi = []
	with mock.patch.object(db, "_cau_hinh", lambda: dict(ch)), \
		mock.patch.object(_fr.utils, "now_datetime", lambda: THU2, create=True), \
		mock.patch.object(_fr.utils, "nowdate", lambda: "2026-11-02", create=True), \
		mock.patch.object(_fr, "log_error", lambda **k: loi.append(k), create=True), \
		mock.patch.object(noi_dung_web, "_ban_cong_khai", lambda: ban), \
		mock.patch.object(don_web, "lien_he", lambda: {"dien_thoai": "0931 224 334", "zalo": ""}):
		ra = db.cau_hinh()
		la("khoá", {k: ra.get(k) for k in ("hom_nay", "khung_gio_hom_nay", "dang_mo", "gio_hom_nay", "hotline_so", "chi_duong", "anh")},
			{"hom_nay": "2026-11-02", "khung_gio_hom_nay": ["18:00"], "dang_mo": True, "gio_hom_nay": "9:00 - 21:00",
			 "hotline_so": "0931224334", "chi_duong": "https://maps.app.goo.gl/x", "anh": "/assets/vagabond/images/quay-tcv.jpg"})
		dung("không có Zalo rỗng", "zalo" not in ra)
		la("không lỗi", loi, [])
		with mock.patch.object(noi_dung_web, "_ban_cong_khai", lambda: 1 / 0):
			ra = db.cau_hinh()
		dung("lỗi đọc: vẫn bật, vẫn có giờ", ra["bat"] and ra["khung_gio_hom_nay"] == ["18:00"] and "dang_mo" not in ra)
		la("ghi Error Log một dòng", len(loi), 1)


def _cap_chu():
	js = (GOC / "vagabond/public/web_order/dat-ban.js").read_text()
	ht = (GOC / "vagabond/www/dat-ban.html").read_text()
	cap = re.findall(r'chuWeb\("([^"]+)", "([^"]*)"', js)
	cap += [(k, html.unescape(v)) for k, v in re.findall(r'data-vgb-chu="([^"]+)">([^<]*)<', ht)]
	for the in re.findall(r"<[^>]+>", ht):
		for t in ("placeholder", "aria-label", "alt", "title"):
			k = re.search(r'data-vgb-%s="([^"]+)"' % t, the)
			v = re.search(r'\s%s="([^"]*)"' % t, the)
			if k and v:
				cap.append((k.group(1), html.unescape(v.group(1))))
	return js, ht, cap


@ca("v630 chữ trang đặt bàn: mọi khoá có trong sổ nhãn, chữ mặc định trùng sổ nhãn, không gạch dài")
def _nhan():
	from vagabond import noi_dung_web
	js, ht, cap = _cap_chu()
	dung("đủ nhiều chữ", len(cap) > 50)
	for k, v in cap:
		dung("có khoá " + k, k in noi_dung_web.NHAN)
		la("mặc định " + k, v, noi_dung_web.NHAN[k]["mac_dinh"])
	mau = json.loads((GOC / "vagabond/public/web_order/chu-mac-dinh.json").read_text())
	moi = [k for k in mau if k.startswith("db630_")]
	dung("khoá mới thuộc nhóm đặt bàn", moi and all(mau[k]["nhom"] == "dat_ban" for k in moi))
	dung("khoá mới đều được dùng", all(any(k == x for x, _ in cap) for k in moi))
	for tep in ("vagabond/public/web_order/dat-ban.js", "vagabond/public/web_order/dat-ban.css", "vagabond/www/dat-ban.html",
			"vagabond/khung/kiem_thu/hanh_vi/dat_ban_630.js"):
		s = (GOC / tep).read_text()
		dung(tep + " không gạch dài", chr(0x2014) not in s and chr(0x2013) not in s)


@ca("v630 trang trỏ đúng mã băm tệp mới; CSS riêng nằm dưới main.db, không đụng thanh-vien.css")
def _ma_bam():
	ht = (GOC / "vagabond/www/dat-ban.html").read_text()
	for tep in ("dat-ban.js", "dat-ban.css", "thanh-vien.css", "nen.css", "chu.js"):
		bam = hashlib.sha256((GOC / "vagabond/public/web_order" / tep).read_bytes()).hexdigest()[:12]
		dung("dat-ban.html trỏ %s?v=%s" % (tep, bam), "/assets/vagabond/web_order/%s?v=%s" % (tep, bam) in ht)
	css = (GOC / "vagabond/public/web_order/dat-ban.css").read_text()
	luat = [x.strip() for x in re.sub(r"/\*.*?\*/", "", css, flags=re.S).replace("@media(max-width:700px){", "").split("}") if x.strip()]
	ngoai = [x for x in luat if not all(c.strip().startswith(".trang-dich-vu .db") or c.strip().startswith(".trang-dich-vu main.db")
		for c in x.split("{")[0].split(","))]
	la("mọi quy tắc dưới main.db", ngoai, [])
	# v643 (còn tồn v611, đo 07/11 trên site ở 360px: nút gửi bị cắt "GỬI YÊU CẦU ĐẶT B..."):
	# trên điện thoại nút được xuống dòng, không cắt chữ bằng dấu ba chấm.
	dt = css[css.index("@media(max-width:700px)"):]
	nut = [x for x in re.sub(r"/\*.*?\*/", "", dt, flags=re.S).split("}") if "button#gui" in x]
	dung("nút gửi trên điện thoại xuống dòng, không cắt chữ", nut and "white-space:normal" in nut[0] and "ellipsis" not in nut[0])
	dung("thanh-vien.css không có lớp db-", "db-" not in (GOC / "vagabond/public/web_order/thanh-vien.css").read_text())


@ca("v630 trang thật trên DOM giả: dải ngày, số khách, giờ đã qua, gửi đúng thân (hanh_vi/dat_ban_630.js)")
def _hanh_vi():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/dat_ban_630.js"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-3000:] + r.stderr[-2000:], r.returncode, 0)
