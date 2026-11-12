# -*- coding: utf-8 -*-
"""Một nguồn gửi tin cho KHÁCH có đường phụ: Zalo ZNS trước, hỏng mới WhatsApp.

Anh Việt chốt 12/11/2026 (không đổi):
  - Với MỌI số điện thoại, kể cả số Việt Nam, luôn gửi Zalo ZNS trước. Chỉ khi
    Zalo gửi THẤT BẠI (số không có Zalo, ZNS từ chối, lỗi gọi ZNS) mới gửi
    WhatsApp. Không phải "số nước ngoài thì gửi WhatsApp": nhiều người ở Việt
    Nam không dùng Zalo.
  - Zalo gửi được thì không gửi thêm WhatsApp (không trùng hai kênh).
  - Cả hai hỏng: mã xác thực báo khách câu dễ hiểu, kỹ thuật đọc Error Log.
  - Ưu đãi chỉ gửi WhatsApp cho khách ĐÃ đồng ý nhận tin.

Mọi cửa gửi mã xác thực (dang_nhap.gui_ma cho trang thành viên, bánh sỉ, gọi
món tại bàn, ưu đãi đơn đầu; diem_otp cho mã trừ điểm) và kịch bản ưu đãi Zalo
đều đi qua đây. Ca kiểm chốt "không còn chỗ nào tự gọi ZNS mã xác thực riêng".

Phần THUẦN trước, phần chạm hệ sau. Không nạp thư viện mạng ở đầu tệp.
"""

ZALO = "zalo"
WHATSAPP = "whatsapp"
KHONG = "khong"


# ------------------------------------------------------------------ THUẦN

def nen_gui_wa(zns_ok, wa_san_sang, dong_y=True):
	"""Có gửi WhatsApp không, theo kết quả Zalo. THUẦN."""
	return (not zns_ok) and bool(wa_san_sang) and bool(dong_y)


def che_so(so84):
	"""84703418349 -> "0703 418 349" để hiện trên màn khách (số của chính họ)."""
	x = "".join(ch for ch in str(so84 or "") if ch.isdigit())
	if x.startswith("84") and len(x) == 11:
		x = "0" + x[2:]
	return (x[:4] + " " + x[4:7] + " " + x[7:]) if len(x) == 10 else x


def noi_dung_uu_dai(ten_uu_dai, ma=None, dieu_kien=None):
	"""Tham số {{2}} của mẫu vgb_uu_dai: tên ưu đãi, kèm mã và điều kiện. THUẦN."""
	ra = str(ten_uu_dai or "").strip()
	if dieu_kien:
		ra += " (" + str(dieu_kien).strip() + ")"
	if ma:
		ra += ", mã " + str(ma).strip()
	return ra[:900]


# ------------------------------------------------------------- CHẠM HỆ

def _wa():
	from vagabond import whatsapp

	return whatsapp


def wa_san_sang(c, loai):
	"""WhatsApp đủ ô để thử gửi loại tin này (otp / uu_dai)."""
	from vagabond.lib import key

	h = _wa().cau_hinh(c)
	mau = h["mau_otp"] if loai == "otp" else h["mau_uu_dai"]
	return bool(h["phone_id"] and mau and key(c, "wa_token"))


def gui_otp(c, so84, ma, gui_zns):
	"""Gửi mã xác thực: `gui_zns()` trả (được, lỗi). Trả (kênh, lỗi Zalo, lỗi WA)."""
	import frappe

	ok, loi_z = gui_zns()
	if ok:
		return ZALO, "", ""
	if not nen_gui_wa(ok, wa_san_sang(c, "otp")):
		frappe.log_error(title="Vagabond: không gửi được mã xác thực", message="Zalo: %s\nWhatsApp: chưa khai" % loi_z)
		return KHONG, loi_z, "WhatsApp chưa khai"
	w = _wa()
	h = w.cau_hinh(c)
	ok_w, loi_w = w.gui_mau(c, so84, h["mau_otp"], None, h["ngon_ngu"], components=w.comp_otp(ma))
	if ok_w:
		return WHATSAPP, loi_z, ""
	frappe.log_error(title="Vagabond: không gửi được mã xác thực", message="Zalo: %s\nWhatsApp: %s" % (loi_z, loi_w))
	return KHONG, loi_z, loi_w


def gui_uu_dai(c, so84, ten, noi_dung, han, dong_y):
	"""Đường phụ của tin ưu đãi khi Zalo đã hỏng cho riêng khách này. Chỉ gửi khi
	khách đã đồng ý nhận tin. Trả (được, lỗi)."""
	if not nen_gui_wa(False, wa_san_sang(c, "uu_dai"), dong_y):
		return False, ("khách chưa đồng ý nhận tin" if not dong_y else "WhatsApp chưa khai")
	w = _wa()
	h = w.cau_hinh(c)
	return w.gui_mau(c, so84, h["mau_uu_dai"], None, h["ngon_ngu"], components=w.comp_uu_dai(ten, noi_dung, han))
