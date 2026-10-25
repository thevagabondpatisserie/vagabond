# -*- coding: utf-8 -*-
"""Thư gửi khách khi cửa hàng xác nhận hoặc huỷ yêu cầu đặt bàn.

Anh Việt 25/10/2026: quản lý cửa hàng xác nhận đơn đặt bàn trên app thì máy
gửi email cho khách. Hai mẫu thư dựng trên khung thư chung (thu_khung), cùng
bộ nhận diện với mọi thư khác của tiệm.

THUẦN: không chạm Frappe, để xem trước và kiểm thử trên máy CI tay không.
Phần gửi thật nằm ở dat_ban.py.
"""

from datetime import datetime

from vagabond import thu_khung as tk

WEB_DAT_BAN = "https://thevagabondpatisserie.com/dat-ban"
THU = ("CN", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy")


def ngay_vn(ngay):
	"""'2026-10-26' -> 'Thứ Hai, 26/10/2026'. THUẦN."""
	d = datetime.strptime(str(ngay)[:10], "%Y-%m-%d")
	thu = "Chủ Nhật" if d.weekday() == 6 else THU[d.weekday() + 1]
	return "%s, %s" % (thu, d.strftime("%d/%m/%Y"))


def _so_khach(d):
	so = int(d.get("so_khach") or 0)
	tre = int(d.get("tre_em") or 0)
	return "%d khách%s" % (so, (", trong đó %d trẻ em" % tre) if tre else "")


def _cap_dat_ban(d):
	"""Các dòng thông tin bàn, bỏ dòng khách không điền."""
	ra = [
		("Ngày", tk.h(ngay_vn(d.get("ngay")))),
		("Giờ đến", "<b>%s</b>" % tk.h(d.get("gio"))),
		("Số khách", tk.h(_so_khach(d))),
		("Chi nhánh", "%s<br>%s" % (tk.h(d.get("ten_co_so") or d.get("co_so")), tk.h(d.get("dia_chi") or ""))),
	]
	if d.get("khu_vuc"):
		ra.append(("Khu vực mong muốn", tk.h(d.get("khu_vuc"))))
	if d.get("dip") and d.get("dip") != "Không có dịp riêng":
		ra.append(("Dịp", tk.h(d.get("dip"))))
	if d.get("banh_kem_theo"):
		ra.append(("Bánh đặt sẵn", tk.h(d.get("banh_kem_theo"))))
	return ra


def tieu_de_thu(loai, d):
	"""Dòng tiêu đề email. THUẦN."""
	ngay = datetime.strptime(str(d.get("ngay"))[:10], "%Y-%m-%d").strftime("%d/%m")
	if loai == "xac_nhan":
		return "Xác nhận đặt bàn %s lúc %s · %s" % (ngay, d.get("gio"), tk.TEN_TIEM)
	return "Về yêu cầu đặt bàn %s lúc %s · %s" % (ngay, d.get("gio"), tk.TEN_TIEM)


def thu_xac_nhan(d, loi_nhan="", goc_anh="", cac_quay=None):
	"""HTML thư xác nhận. d: các ô của phiếu đặt bàn kèm ten_co_so, dia_chi."""
	than = (
		tk.doan("Chào %s," % tk.h(d.get("ten")))
		+ tk.doan("Cảm ơn anh chị đã chọn The Vagabond Pâtisserie. Tiệm đã giữ bàn "
			"cho anh chị theo thông tin dưới đây.")
		+ tk.o_kem(tk.cap(_cap_dat_ban(d)), goc_anh)
	)
	if (loi_nhan or "").strip():
		than += tk.nhan_hoa("Lời nhắn từ cửa hàng") + tk.doan(tk.h(loi_nhan.strip()), 14)
	than += tk.o_canh_bao(
		"Nếu anh chị đến trễ, muốn đổi giờ hoặc không đến được, xin gọi "
		"<b>%s</b> để tiệm sắp xếp lại bàn kịp thời." % tk.h(tk.HOTLINE))
	than += tk.doan("Hẹn gặp anh chị tại tiệm.", 4)
	nut = tk.nut("https://www.google.com/maps/search/?api=1&query=" + _q(d.get("dia_chi") or ""),
		"Xem đường đến tiệm", goc_anh=goc_anh)
	return tk.khung_thuan("Bàn của anh chị đã được giữ", than, nut, "khach",
		"Xác nhận đặt bàn", goc_anh, cac_quay)


def thu_huy(d, ly_do, goc_anh="", cac_quay=None):
	"""HTML thư báo tiệm không giữ được bàn, kèm lý do quản lý ghi."""
	than = (
		tk.doan("Chào %s," % tk.h(d.get("ten")))
		+ tk.doan("Cảm ơn anh chị đã gửi yêu cầu đặt bàn tại The Vagabond Pâtisserie. "
			"Rất tiếc, lần này tiệm chưa giữ được bàn cho anh chị.")
		+ tk.o_kem(tk.cap(_cap_dat_ban(d)[:4] + [("Lý do", tk.h((ly_do or "").strip()))]), goc_anh)
		+ tk.doan("Anh chị có thể chọn một khung giờ khác trên trang đặt bàn, hoặc gọi "
			"<b>%s</b> để tiệm tư vấn giờ còn chỗ." % tk.h(tk.HOTLINE))
		+ tk.doan("Mong sớm được đón anh chị.", 4)
	)
	nut = tk.nut(WEB_DAT_BAN, "Chọn giờ khác", goc_anh=goc_anh)
	return tk.khung_thuan("Tiệm chưa giữ được bàn lần này", than, nut, "khach",
		"Đặt bàn", goc_anh, cac_quay)


def _q(s):
	from urllib.parse import quote
	return quote(str(s or ""))
