"""Nhãn và câu chữ trên web cho marketing tự đổi (v532, anh Việt 27/09/2026).

Vì sao có bộ ca này: trước v532 chữ trên thanh chọn (In season, In store,
Có sẵn hôm nay, Đặt bánh trước), câu "Bếp cần khoảng 4 tiếng...", dòng "N
bánh có sẵn · nhận từ..." và toàn bộ chữ trang đặt bàn nằm cứng trong HTML,
Minh Vũ muốn đổi phải nhờ sửa code. Nay các chữ đó là khoá cố định trong
noi_dung_web.NHAN, đi cùng luồng nháp, xuất bản, lịch sử của trang order.

Ba lớp: phép thuần (chuan_hoa, nhan_day_du), nguồn duy nhất (trang không
còn tự ghép câu, mặc định trong trang trùng mặc định máy chủ), và hành vi
chạy thật trong node (hanh_vi/nhan_web_532.js và gia_lap_trang.js).
"""

import copy
import io
import json
import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.noi_dung_web import chuan_hoa, nhan_day_du, cho_dien, MAC_DINH, NHAN

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	with io.open(os.path.join(GOC, *duong), encoding="utf-8") as f:
		return f.read()


def _bi_chan(nd):
	try:
		chuan_hoa(nd)
	except (ValueError, TypeError):
		return True
	return False


def _nd(nhan):
	nd = copy.deepcopy(MAC_DINH)
	nd["nhan"] = nhan
	return nd


# ------------------------------------------------------------- phép thuần


@ca("v532 nhãn: nhận khoá đúng, để trống là mặc định, giữ nguyên khi lưu")
def _nhan_dung():
	nd = _nd({"tab_today": "Bánh sinh nhật hôm nay", "tab_store": "", "cau_co_san": "Còn {so} chiếc"})
	ra = chuan_hoa(nd)
	la("giữ nguyên nhãn", ra["nhan"], nd["nhan"])
	day = nhan_day_du(ra)
	la("chữ đã sửa", day["tab_today"], "Bánh sinh nhật hôm nay")
	la("để trống thì mặc định", day["tab_store"], "In store")
	la("khoá không gửi cũng có mặc định", day["dat_ban_dong"], NHAN["dat_ban_dong"]["mac_dinh"])
	la("đủ mọi khoá", set(day), set(NHAN))
	la("bản cũ chưa có nhan vẫn đủ", set(nhan_day_du(MAC_DINH)), set(NHAN))
	dung("bản cũ không có nhan vẫn lưu được", not _bi_chan(copy.deepcopy(MAC_DINH)))


@ca("v532 nhãn: chặn khoá lạ, sai kiểu, quá dài, xuống dòng ở nhãn một dòng")
def _nhan_chan():
	for nhan in ({"khoa_la": "x"}, {"tab_today": 5}, {"tab_today": None}, ["tab_today"], "x",
	             {"tab_today": "a" * 301}, {"tab_today": "hai\ndòng"}):
		dung("chặn %r" % (str(nhan)[:40],), _bi_chan(_nd(nhan)))
	dung("trang đặt bàn được xuống dòng", not _bi_chan(_nd({"dat_ban_mo_ta": "hai\ndòng"})))
	dung("đúng 300 ký tự vẫn nhận", not _bi_chan(_nd({"tab_today": "a" * 300})))


@ca("v532 nhãn: câu có chỗ điền phải giữ đủ chỗ điền, không thêm chỗ điền lạ")
def _cho_dien():
	la("đọc chỗ điền", cho_dien("Bếp cần {gio} tiếng, từ {khung} và {khung}"), ["{gio}", "{khung}"])
	dung("mất {khung} thì chặn", _bi_chan(_nd({"cau_chuan_bi": "Bếp cần {gio} tiếng."})))
	dung("mất {so} thì chặn", _bi_chan(_nd({"cau_co_san": "Còn bánh"})))
	dung("chỗ điền lạ thì chặn", _bi_chan(_nd({"cau_co_san": "{so} bánh, giá {gia}"})))
	dung("đổi thứ tự vẫn nhận", not _bi_chan(_nd({"cau_chuan_bi": "Từ khung {khung} hôm nay, bếp cần {gio} tiếng."})))
	dung("câu không có chỗ điền thì tự do", not _bi_chan(_nd({"cau_het_khung": "Hôm nay hết giờ rồi ạ"})))


# ------------------------------------------------------------ nguồn duy nhất


@ca("v532 nhãn: mặc định trong máy chủ trùng chữ đang có trong trang và JS")
def _mac_dinh_trung():
	trang = _doc("vagabond", "trang", "banh.html")
	for khoa in ("tab_season", "tab_store", "tab_today", "tab_order", "nut_dat_ban", "nut_thanh_vien"):
		dung("trang có %s gắn data-vgb-nhan" % khoa,
		     re.search(r'data-vgb-nhan="%s"[^>]*>%s<' % (khoa, re.escape(NHAN[khoa]["mac_dinh"])), trang) is not None)
	# NHAN_MAC_DINH trong trang: đọc bằng node, không đọc bằng regex đoán.
	m = re.search(r"var NHAN_MAC_DINH = (\{[\s\S]*?\n\});", trang)
	dung("trang có NHAN_MAC_DINH", m is not None)
	r = subprocess.run(["node", "-e", "console.log(JSON.stringify(" + m.group(1) + "))"], capture_output=True, text=True, timeout=20)
	la("node đọc được", r.returncode, 0)
	js = json.loads(r.stdout)
	for khoa, chu in js.items():
		la("mặc định %s trùng máy chủ" % khoa, chu, NHAN[khoa]["mac_dinh"])
	la("trang có đủ câu có số", set(js), {k for k in NHAN if k.startswith("cau_")})
	dat_ban_js = _doc("vagabond", "public", "web_order", "dat-ban.js")
	dung("câu đóng dự phòng trong dat-ban.js trùng máy chủ", "'" + NHAN["dat_ban_dong"]["mac_dinh"] + "'" in dat_ban_js)


@ca("v532 nhãn: trang order không còn tự ghép câu, mọi câu có số đi qua cauNhan")
def _mot_nguon():
	trang = _doc("vagabond", "trang", "banh.html")
	than = trang.split("var NHAN_MAC_DINH")[1]
	dung("không còn chữ 'Bếp cần khoảng' ghép tay", "Bếp cần khoảng <b>" not in than)
	dung("không còn 'bánh</b> có sẵn' ghép tay", "bánh</b> có sẵn" not in than)
	dung("không còn 'nhận từ <b>' ghép tay", "nhận từ <b>" not in than)
	la("cauNhan gọi ở đúng 5 chỗ câu có số", len(re.findall(r"cauNhan\('cau_", than)), 5)
	dung("cauNhan escape trước khi thay số", "esc(nhanWeb(khoa))" in trang)
	html = _doc("vagabond", "www", "dat-ban.html")
	for khoa in ("dat_ban_nhan", "dat_ban_tieu_de", "dat_ban_mo_ta", "dat_ban_dong", "dat_ban_nut", "dat_ban_ho_tro"):
		dung("dat-ban.html in %s có escape" % khoa, "{{ nhan.%s | e }}" % khoa in html)
	dung("dat-ban.html không còn chữ cứng", "HẸN MỘT BUỔI" not in html and "Gửi yêu cầu đặt bàn</button>" not in html)


# -------------------------------------------------------- hành vi màn hình


def _gia_lap(gio, kich_ban):
	js = os.path.join(GOC, "vagabond", "khung", "kiem_thu", "gia_lap_trang.js")
	trang = os.path.join(GOC, "vagabond", "trang", "banh.html")
	r = subprocess.run(["node", js, trang, gio, kich_ban], capture_output=True, text=True, timeout=60)
	if r.returncode != 0:
		raise AssertionError("gia lập trang lỗi: " + (r.stderr or "").strip()[:600])
	return json.loads((r.stdout or "").strip().splitlines()[-1])


@ca("v532 nhãn: trang order chạy thật, câu giờ chuẩn bị lấy chữ marketing và điền số, không thành HTML")
def _cau_chuan_bi():
	ra = _gia_lap("2026-09-27T08:00:00+07:00", """
		renderToday();
		var truoc = EL('#prepNote').innerHTML;
		window.vgbNhan = {cau_chuan_bi: 'Bếp làm mất {gio} tiếng <script>x</script>, sớm nhất là {khung} nhé', cau_co_san: 'Còn {so} chiếc'};
		renderToday();
		RA({truoc: truoc, sau: EL('#prepNote').innerHTML, tt: EL('#dongTrangThai').innerHTML});
	""")
	dung("trước khi có nhãn: câu mặc định có số tiếng", "Bếp cần khoảng <b>4 tiếng</b>" in ra["truoc"] or "Bếp cần khoảng <b>4</b> tiếng" in ra["truoc"])
	dung("sau: chữ marketing", ra["sau"].startswith("Bếp làm mất <b>4</b> tiếng"))
	dung("sau: có khung giờ in đậm", re.search(r"sớm nhất là <b>\d{1,2}h[^<]*</b> nhé", ra["sau"]) is not None)
	dung("thẻ script thành chữ", "&lt;script&gt;" in ra["sau"] and "<script>" not in ra["sau"])
	dung("dòng trạng thái chưa nạp tồn thì không đoán số", "Còn" not in ra["tt"])


@ca("v532 nhãn: cua-hang.js chạy thật trong node, tab và nút đổi theo nhãn đã xuất bản")
def _hanh_vi_cua_hang():
	js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hanh_vi", "nhan_web_532.js")
	r = subprocess.run(["node", js], capture_output=True, text=True, timeout=30, cwd=GOC)
	la(r.stdout + r.stderr, r.returncode, 0)
	dung("đủ 4 ca", "PASS 4" in r.stdout)


@ca("v532 nhãn: cong_khai trả bộ nhãn đầy đủ cho trang, nhan_cong_khai cho trang đặt bàn, không lộ chính sách")
def _cong_khai_du_nhan():
	from vagabond import noi_dung_web as ndw
	goc = ndw._ban_cong_khai
	ban = copy.deepcopy(MAC_DINH)
	ban["nhan"] = {"tab_today": "Bánh sinh nhật hôm nay", "dat_ban_nut": ""}
	ban["chinh_sach"] = {"dieu_khoan": {"hien": True, "vn": "x", "en": ""}}
	ndw._ban_cong_khai = lambda: copy.deepcopy(ban)
	try:
		ra = ndw.cong_khai()
		dung("không lộ chính sách", "chinh_sach" not in ra)
		la("đủ khoá nhãn", set(ra["nhan"]), set(NHAN))
		la("chữ đã sửa", ra["nhan"]["tab_today"], "Bánh sinh nhật hôm nay")
		la("để trống thì mặc định", ra["nhan"]["dat_ban_nut"], "Gửi yêu cầu đặt bàn")
		la("trang đặt bàn cùng một nguồn", ndw.nhan_cong_khai(), ra["nhan"])
		ndw._ban_cong_khai = lambda: copy.deepcopy(MAC_DINH)
		la("bản cũ chưa có nhãn vẫn đủ khoá", set(ndw.cong_khai()["nhan"]), set(NHAN))
	finally:
		ndw._ban_cong_khai = goc
