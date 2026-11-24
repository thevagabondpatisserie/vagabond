"""v692 (anh Việt 24/11/2026): bỏ "/banh#" trong mọi link của trang đặt bánh.

Trên tên miền khách, mỗi màn có đường sạch: /, /dat-truoc, /tuyen-dung/<mã>,
/uu-dai/<mã>, /banh/<bánh>, /gio-hang... Máy chủ phát cùng trang đặt bánh cho
mọi đường đó; link cũ /banh#/<màn> và QR bàn cũ vẫn mở đúng.

Ca thuần: không cần Frappe. Phần trình duyệt chạy thật bằng node
(hanh_vi/duong_sach_692.mjs)."""
import subprocess
import types
import unittest.mock as um
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
CHINH = "thevagabondpatisserie.com"


@ca("v692 đường sạch: màn của trang đặt bánh nhận ra đúng, biên nhận và đường lạ thì không")
def _la_duong_spa():
	from vagabond.ten_mien import la_duong_spa
	for d in ("/", "", "/banh", "/banh/", "/dat-truoc", "/in-season", "/in-season/MUA1", "/in-store", "/uu-dai",
			"/uu-dai/km-1", "/tuyen-dung", "/tuyen-dung/VT-1/", "/ve-su-kien", "/tiec", "/dac-biet-tuan-nay",
			"/thiet-ke-rieng", "/thiet-ke-rieng/TP-2", "/gio-hang", "/banh/bo-mon"):
		la("màn trang đặt bánh " + repr(d), la_duong_spa(d), True)
	for d in ("/banh/xong", "/banh/xong/abc", "/bep", "/app", "/api/method/x", "/assets/a.js",
			"/thanh-vien", "/dat-ban", "/ung-tuyen", "/mon/TART", "/banh/a/b", "/tuyen-dungx"):
		la("không phải màn " + d, la_duong_spa(d), False)


@ca("v692 đường sạch chỉ trên tên miền khách; app và Desk giữ màn nội bộ /tuyen-dung")
def _mien():
	from vagabond.ten_mien import la_trang_dat_banh_khach, dich_chuyen_huong
	for h in (CHINH, "www." + CHINH, "order." + CHINH, "ORDER.%s:443" % CHINH):
		la("khách " + h, la_trang_dat_banh_khach(h, "/tuyen-dung/VT-1"), True)
		la("khách không chuyển " + h, dich_chuyen_huong(h, "/tuyen-dung/VT-1", ("tuyen-dung", "kho-v2")), "")
	for h in ("app." + CHINH, "erp." + CHINH, "erpnext-qwy-acq.s.frappe.cloud", "localhost:8000", ""):
		la("nội bộ " + h, la_trang_dat_banh_khach(h, "/tuyen-dung"), False)
	la("app vẫn mở màn tuyển dụng nội bộ", dich_chuyen_huong("app." + CHINH, "/tuyen-dung", ("tuyen-dung",)), "")


@ca("v692 tên miền chính: / là trang đặt bánh khi bật bản mới; WordPress cũ về /; tắt bản mới thì như cũ")
def _chuyen():
	from vagabond.ten_mien import chuyen_ten_mien
	la("/ ở lại", chuyen_ten_mien(CHINH, "/", "GET", "utm_source=fb", 1, True), None)
	la("/dat-truoc ở lại", chuyen_ten_mien(CHINH, "/dat-truoc", "GET", "", 1, True), None)
	la("WordPress về /", chuyen_ten_mien(CHINH, "/shop/", "GET", "", 1, True), ("/", 301))
	la("tắt bản mới: / về /banh", chuyen_ten_mien(CHINH, "/", "GET", "", 1, False), ("/banh", 302))
	la("tắt bản mới: WordPress về /banh", chuyen_ten_mien(CHINH, "/shop/", "GET", "", 1, False), ("/banh", 301))
	la("order giữ đường sạch khi sang tên miền chính", chuyen_ten_mien("order." + CHINH, "/tuyen-dung/VT-1", "GET", "", 1, True),
		("https://%s/tuyen-dung/VT-1" % CHINH, 301))


@ca("v692 bộ dựng trang: màn đường sạch trên tên miền khách dựng trang đặt bánh, tên miền app thì không")
def _bo_dung():
	from vagabond import trang_banh_vue as tbv
	cu = getattr(tbv.frappe, "local", None)
	try:
		for host, duong, mong in ((CHINH, "/tuyen-dung", True), (CHINH, "/", True), ("order." + CHINH, "/uu-dai/k1", True),
				("app." + CHINH, "/tuyen-dung", False), (CHINH, "/banh/xong/t", False), (CHINH, "/thanh-vien", False)):
			tbv.frappe.local = types.SimpleNamespace(request=types.SimpleNamespace(host=host, path=duong))
			la("%s%s" % (host, duong), tbv.duong_khach_spa(), mong)
		# Luật định tuyến đã đổi /tuyen-dung thành trang app "bep" trước khi tới bộ dựng:
		# bộ dựng vẫn phải nhận ra màn trang đặt bánh theo đường thật của request.
		dung_that = []
		with um.patch.object(tbv.TemplatePage, "__init__", lambda self, p, c=None: dung_that.append(p)):
			tbv.frappe.local = types.SimpleNamespace(request=types.SimpleNamespace(host=CHINH, path="/tuyen-dung/VT-1"))
			la("khách: dựng trang đặt bánh", tbv.TrangBanhVue("bep").duong_goc, "banh")
			tbv.frappe.local = types.SimpleNamespace(request=types.SimpleNamespace(host="app." + CHINH, path="/tuyen-dung"))
			la("app: giữ màn app", tbv.TrangBanhVue("bep").duong_goc, "bep")
		la("dựng đúng tệp trang đặt bánh một lần", dung_that, [tbv.TEP_VUE["banh"]])
		tbv.frappe.local = types.SimpleNamespace()
		la("không có request", tbv.duong_khach_spa(), False)
	finally:
		if cu is not None:
			tbv.frappe.local = cu


@ca("v692 QR bàn mới dùng đường sạch /in-store, không còn banh#")
def _qr():
	from vagabond import goi_mon_ban as g
	la("đường trang", g.DUONG_TRANG, "/in-store")
	src = (GOC / "goi_mon_ban.py").read_text()
	dung("không còn tạo link #/in-store", "#/in-store\"" not in src and "+ \"#/" not in src)


@ca("v692 trang khách không còn link /banh# nào; trang ứng tuyển về /tuyen-dung")
def _khong_banh_thang():
	html = (GOC / "www/ung-tuyen.html").read_text()
	la("ứng tuyển không còn /banh#", html.count("/banh#"), 0)
	la("ứng tuyển về danh sách vị trí", html.count('href="/tuyen-dung"'), 3)
	for p in ("public/web_vue/banh/noi-dung.js", "public/web_vue/banh/mau.js"):
		s = (GOC / p).read_text()
		la(p + " không còn href cứng #/", s.count("href: '#/") + s.count('href="#/'), 0)


@ca("v692 hàm đường sạch phía trình duyệt chạy thật bằng node đều đạt")
def _node():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/duong_sach_692.mjs"], cwd=REPO, capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	dung("đủ số ca", "7 ca dat, 0 ca hong" in r.stdout)
