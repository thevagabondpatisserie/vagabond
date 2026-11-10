# -*- coding: utf-8 -*-
"""v647 (anh Việt 10/11/2026): banner ảnh trên trang đặt bánh (O2O).

Anh Việt muốn có chỗ đặt banner tự thiết kế (ví dụ "Cập nhật ngày sinh để
nhận quà bánh vào sinh nhật") để mời khách đang đặt bánh khai hồ sơ, và Minh
Vũ tự thay ảnh trong trình biên tập. Anh chọn ba chỗ: Đầu trang, Giỏ hàng,
Đặt xong; bấm banner mở trang thành viên.

Ca dưới chạy THẬT các phép của noi_dung_web (chuan_hoa, ap_muc, banner_hien,
trang_thai_muc) và hàm máy chủ thật luu_muc trên site giả của bộ ca v586.
Phần vẽ trên trang (Vue) và trình biên tập kiểm bằng node:
hanh_vi/banner_vue_647.mjs và hanh_vi/bien_tap_586.js.
"""
import copy
import json
import os
import subprocess

from vagabond import noi_dung_web as nw
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _nd(*khoi):
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].extend(copy.deepcopy(list(khoi)))
	return nd


def _bn(**k):
	m = {"id": "banner-sn", "loai": "banner", "vi_tri": "gio_hang", "hien": True, "tieu_de": "Sinh nhật nhận quà",
		"anh": "/files/banner-pc.png", "anh_dt": "/files/banner-dt.png", "mo_ta_anh": "Cập nhật ngày sinh để nhận quà bánh",
		"lien_ket": "/thanh-vien", "bat_dau": "", "ket_thuc": ""}
	m.update(k)
	return m


def _loi(nd):
	try:
		nw.chuan_hoa(nd)
	except (ValueError, TypeError) as e:
		return str(e)
	return ""


@ca("v647 banner: nhận đủ ba chỗ đã chốt, chặn chỗ khác; bật hiện phải có ảnh")
def _cho_va_anh():
	for cho in ("dau_trang", "gio_hang", "dat_xong"):
		la("nhận chỗ " + cho, _loi(_nd(_bn(vi_tri=cho))), "")
	for cho in ("today", "cuoi_trang", "banner", ""):
		dung("chặn chỗ " + repr(cho), "Chọn chỗ đặt banner" in _loi(_nd(_bn(vi_tri=cho))))
	la("bật mà chưa có ảnh thì chặn", _loi(_nd(_bn(anh=""))), "Tải ảnh banner trước khi bật hiện trên web.")
	la("đang ẩn thì chưa cần ảnh (lưu nháp banner)", _loi(_nd(_bn(anh="", hien=False))), "")
	la("không có ảnh điện thoại vẫn được", _loi(_nd(_bn(anh_dt=""))), "")
	dung("banner cần tên", "cần có tên" in _loi(_nd(_bn(tieu_de=" "))))
	dung("ngày ngược thì chặn", "Ngày kết thúc" in _loi(_nd(_bn(bat_dau="2026-11-20", ket_thuc="2026-11-10"))))


@ca("v647 banner: ảnh và link qua cùng cửa an toàn; chỗ Giỏ hàng, Đặt xong và ảnh điện thoại chỉ dành cho banner")
def _an_toan():
	for truong in ("anh", "anh_dt"):
		for xau in ("javascript:alert(1)", "http://x.vn/a.png", "//x.vn/a.png", "/private/files/a.png", "/files/a.svg", "/files/a b.png"):
			dung("%s chặn %r" % (truong, xau), _loi(_nd(_bn(**{truong: xau}))) != "")
	dung("link javascript bị chặn", _loi(_nd(_bn(lien_ket="javascript:alert(1)"))) != "")
	la("link HTTPS ngoài được", _loi(_nd(_bn(lien_ket="https://zalo.me/vagabond"))), "")
	la("không link cũng được", _loi(_nd(_bn(lien_ket=""))), "")
	tiec = {"id": "t1", "loai": "tiec", "vi_tri": "gio_hang", "hien": False, "tieu_de": "Tiệc"}
	dung("tiệc không đặt ở Giỏ hàng", "chỉ dùng cho banner" in _loi(_nd(tiec)))
	khoi = {"id": "k1", "loai": "thong_bao", "vi_tri": "dau_trang", "hien": True, "tieu_de": "x", "anh_dt": "/files/a.png"}
	dung("khối thường không có ảnh điện thoại", "chỉ dùng cho banner" in _loi(_nd(khoi)))


@ca("v647 banner: lưu theo thẻ giữ ĐÚNG chỗ đặt (mục khác vẫn bị ép vị trí bằng loại)")
def _ap_muc():
	nd = nw.ap_muc(_nd(), _bn(vi_tri="dat_xong"), "")
	la("banner giữ chỗ Đặt xong", [k["vi_tri"] for k in nd["khoi"] if k["id"] == "banner-sn"], ["dat_xong"])
	nd = nw.ap_muc(nd, {"id": "t1", "loai": "tiec", "vi_tri": "dau_trang", "hien": False, "tieu_de": "Tiệc"}, "")
	la("tiệc vẫn về vị trí tiệc", [k["vi_tri"] for k in nd["khoi"] if k["id"] == "t1"], ["tiec"])
	nd = nw.xoa_muc(nd, "banner-sn", nw.dau_van_tay(_bn(vi_tri="dat_xong")))
	la("xoá được banner ở thẻ", [k["id"] for k in nd["khoi"] if k["loai"] == "banner"], [])


@ca("v647 banner: banner_hien chỉ trả banner đang bật, có ảnh, đúng chỗ, trong khoảng ngày, đúng thứ tự, không lộ ô nội bộ")
def _banner_hien():
	hn = "2026-11-10"
	nd = _nd(_bn(id="a", vi_tri="dat_xong"), _bn(id="b", vi_tri="gio_hang"), _bn(id="c", vi_tri="dat_xong", hien=False),
		_bn(id="d", vi_tri="dat_xong", anh=""), _bn(id="e", vi_tri="dat_xong", bat_dau="2026-11-11"),
		_bn(id="f", vi_tri="dat_xong", ket_thuc="2026-11-09"), _bn(id="g", vi_tri="dat_xong", bat_dau="2026-11-10", ket_thuc="2026-11-10"))
	ra = nw.banner_hien(nd, "dat_xong", hn)
	la("đúng hai banner", [b["id"] for b in ra], ["a", "g"])
	la("chỉ ô trang cần", sorted(ra[0]), ["anh", "anh_dt", "id", "lien_ket", "mo_ta_anh", "tieu_de"])
	la("chỗ Giỏ hàng", [b["id"] for b in nw.banner_hien(nd, "gio_hang", hn)], ["b"])
	la("nội dung rỗng", nw.banner_hien({}, "dat_xong", hn), [])
	la("nhãn trình biên tập trùng luật", [nw.trang_thai_muc(k, hn)[0] for k in nd["khoi"] if k.get("loai") == "banner"],
		["dang", "dang", "dang", "dang", "sap", "het", "dang"])


@ca("v647 banner: hàm máy chủ thật luu_muc ghi banner vào bản khách thấy lẫn bản nháp, thẻ Banner nhận lại banner")
def _luu_muc_that():
	from vagabond.khung.kiem_thu.thu_bien_tap_theo_the_586 import _Site, _chay
	cong = _nd()
	site = _Site(copy.deepcopy(cong), cong)
	kq = _chay(site, lambda: nw.luu_muc(_bn(vi_tri="dau_trang"), ""))
	c, n = json.loads(site.doc.ban_cong_khai), json.loads(site.doc.ban_nhap)
	la("khách thấy banner ở Đầu trang", [(k["id"], k["vi_tri"]) for k in c["khoi"] if k["loai"] == "banner"], [("banner-sn", "dau_trang")])
	la("nháp cũng có", [k["id"] for k in n["khoi"] if k["loai"] == "banner"], ["banner-sn"])
	la("thẻ Banner nhận lại banner kèm dấu", [[k["id"] for k in kq["khoi"] if k["loai"] == "banner"], "banner-sn" in kq["dau"]], [["banner-sn"], True])
	try:
		_chay(site, lambda: nw.luu_muc(_bn(id="x2", anh=""), ""))
		dung("phải chặn banner bật mà chưa có ảnh", False)
	except Exception as e:
		dung("câu chặn nói rõ: " + str(e), "Tải ảnh banner" in str(e))


@ca("v647 banner: biên nhận Đặt xong nhận banner từ máy chủ, kể cả khi khách tải lại trang (không còn token trên đường dẫn, Codex PR #550)")
def _bien_nhan():
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach, web_vue
	from vagabond.www.banh.xong import TIEU_DE
	nd_cong = _nd(_bn(id="a", vi_tri="dat_xong"), _bn(id="b", vi_tri="gio_hang"))
	nd_cong["nhan"] = {}

	def chay(token):
		fr = D(local=D(response_headers={}), sessions=D(get_csrf_token=lambda: "c"), form_dict={"token": token},
			PageDoesNotExistError=ValueError, utils=D(nowdate=lambda: "2026-11-10"))
		dw = D(PHAP_NHAN={"ten": "X"}, lien_he=lambda: {}, pixel_id=lambda: "", bien_nhan_theo_token=lambda t: {"ma": "DW-1"})
		ndw = D(chinh_sach_dang_hien=lambda: [], cong_khai=lambda: copy.deepcopy(nd_cong), banner_hien=nw.banner_hien)
		g = {"frappe": fr, "don_web": dw, "trang_khach": trang_khach, "noi_dung_web": ndw, "TIEU_DE": TIEU_DE, "web_vue": web_vue}
		c = nap("www/web_moi/xong.py", "get_context", g)(D())
		return json.loads(c.du_lieu.replace("\\u003c", "<"))
	la("có token: đúng banner Đặt xong", [b["id"] for b in chay("T")["banner"]], ["a"])
	# Codex PR #550: biên nhận gỡ token khỏi đường dẫn ngay lần mở đầu, tải lại là
	# vào nhánh không token và khôi phục biên nhận từ phiên. Trước bản sửa máy chủ
	# trả [] nên banner biến mất. Banner là nội dung công khai như trang đặt bánh.
	lai = chay("")
	la("tải lại (không token): vẫn đúng banner Đặt xong", [b["id"] for b in lai["banner"]], ["a"])
	la("tải lại: không lộ biên nhận nào từ máy chủ", [lai.get("khong_token"), lai.get("bien_nhan")], [1, None])


@ca("v647 banner: chạy thật phần vẽ banner trên trang đặt bánh và biên nhận trong node")
def _vue():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond", "khung", "kiem_thu", "hanh_vi", "banner_vue_647.mjs")],
		capture_output=True, text=True, timeout=120, cwd=GOC)
	la("banner_vue_647.mjs chạy xanh", (r.returncode, (r.stderr or "")[-400:], (r.stdout or "")[-400:] if r.returncode else ""), (0, "", ""))


@ca("v647 banner: chạy thật thẻ Banner của trình biên tập (thêm, chặn thiếu ảnh, link mặc định trang thành viên)")
def _bien_tap():
	# Đột biến B10, B11 trước đây chỉ bị ca mã băm bắt vì bien_tap_586.js chỉ
	# chạy trong kiem_truoc_deploy.sh; nay chạy cả trong chay.py.
	r = subprocess.run(["node", os.path.join(GOC, "vagabond", "khung", "kiem_thu", "hanh_vi", "bien_tap_586.js")],
		capture_output=True, text=True, timeout=120, cwd=GOC)
	la("bien_tap_586.js chạy xanh", (r.returncode, (r.stderr or "")[-400:], (r.stdout or "")[-600:] if r.returncode else ""), (0, "", ""))


@ca("v647 trang thành viên mẫu A: chạy thật luồng quà quét QR (số đã xác minh kèm Đổi số, năm sinh giấu, nền sáng)")
def _thanh_vien_mau_a():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond", "khung", "kiem_thu", "hanh_vi", "thanh_vien_647.js")],
		capture_output=True, text=True, timeout=120, cwd=GOC)
	la("thanh_vien_647.js chạy xanh", (r.returncode, (r.stderr or "")[-400:], (r.stdout or "")[-600:] if r.returncode else ""), (0, "", ""))
