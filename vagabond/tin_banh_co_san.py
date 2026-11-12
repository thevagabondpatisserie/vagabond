# -*- coding: utf-8 -*-
"""v653: tin Zalo "Bánh có sẵn hôm nay" kèm ảnh bánh và số lượng.

Anh Việt 12/11/2026 23:23: *"mỗi khi có thay đổi số có thể bán phát sinh hôm nay
trên bảng kiểm bánh thì máy lại báo tự động vào nhóm để mọi người nắm xem còn
bánh gì mà tư vấn. Tin này cần tạo ảnh gửi kèm nhé. Hiển thị cả ảnh bánh và số
lượng"*.

Cách chạy:
  - Nhịp 5 phút (cùng nhịp đồng bộ Kiểm bánh) đọc cột BÁN ĐƯỢC của bảng Kiểm bánh
    hôm nay. Một nguồn: đúng số co_the_ban mà màn Kiểm bánh và web dùng.
  - Danh sách bánh còn bán và số lượng đổi so với lần gửi trước thì gửi tin mới;
    không đổi thì im.
  - Chống tin dồn: hai tin cách nhau ít nhất PHUT_GIUA phút, chỉ trong giờ mở
    cửa GIO_TU tới GIO_DEN; thay đổi trong lúc chờ gom vào tin sau, không mất.
  - Ảnh: lưới ảnh bánh (ảnh Pancake trên bảng Kiểm bánh), số to ở góc. Vẽ hỏng
    thì tin vẫn đi bằng chữ, chú thích tự đủ ý.

Nhóm nhận: nhóm Zalo đã tích tin "Bánh có sẵn hôm nay" (bh_banh_co_san) ở Cài
đặt lõi, mục Bắn tin vào nhóm Zalo.
"""

import hashlib

GIO_TU = "08:00"
GIO_DEN = "21:30"
PHUT_GIUA = 15
TOI_DA_DONG_CHU = 25


# ------------------------------------------------------------------ THUẦN

def danh_sach(dong):
	"""Bánh còn bán hôm nay từ dòng Kiểm bánh: [{ma, ten, so, anh}], số nhiều trước.
	THUẦN. Số âm hay 0 là hết, không liệt kê."""
	ra = []
	for d in dong or []:
		try:
			so = int(d.get("co_the_ban") or 0)
		except (TypeError, ValueError):
			so = 0
		if so <= 0 or not d.get("ma_hang"):
			continue
		ra.append({"ma": d.get("ma_hang"), "ten": (d.get("ten_banh") or d.get("ma_hang") or "").strip(),
			"so": so, "anh": (d.get("hinh") or "").strip()})
	ra.sort(key=lambda x: (-x["so"], x["ten"]))
	return ra


def dau_van_tay(ds):
	"""Dấu của trạng thái: đổi khi có bánh mới còn, bánh hết, hay số đổi. THUẦN."""
	chuoi = "|".join("%s:%s" % (x["ma"], x["so"]) for x in sorted(ds, key=lambda x: x["ma"]))
	return hashlib.sha1(chuoi.encode("utf-8")).hexdigest()[:12]


def phut(gio):
	h, m = str(gio or "00:00")[:5].split(":")
	return int(h) * 60 + int(m)


def nen_gui(bay_gio, lan_cuoi=None):
	"""Đủ điều kiện gửi lúc `bay_gio` (datetime): trong giờ mở cửa, cách lần trước
	ít nhất PHUT_GIUA phút. THUẦN."""
	p = bay_gio.hour * 60 + bay_gio.minute
	if not (phut(GIO_TU) <= p <= phut(GIO_DEN)):
		return False
	if lan_cuoi is None:
		return True
	return (bay_gio - lan_cuoi).total_seconds() >= PHUT_GIUA * 60


def chu_tin(ds, so_het, gio):
	"""Các dòng chú thích, đủ ý khi ảnh không tải được. THUẦN."""
	tong = sum(x["so"] for x in ds)
	dong = ["Cập nhật %s: còn %d loại, tổng %d bánh bán được hôm nay." % (gio, len(ds), tong)]
	dong += ["%s: %d" % (x["ten"], x["so"]) for x in ds[:TOI_DA_DONG_CHU]]
	if len(ds) > TOI_DA_DONG_CHU:
		dong.append("... và %d loại nữa" % (len(ds) - TOI_DA_DONG_CHU))
	if not ds:
		dong.append("Hôm nay đã hết bánh có sẵn. Khách hỏi thì mời đặt trước cho ngày mai.")
	if so_het:
		dong.append("%d loại trên bảng đã hết." % so_het)
	return dong


# ------------------------------------------------------------- CHẠM HỆ

def _khoa_cache(ngay):
	return "vgb_banh_co_san:%s" % ngay


def quet():
	"""Nhịp 5 phút. Không bao giờ ném lỗi ra ngoài (trừ lỗi làm chết giao dịch)."""
	import frappe
	from frappe.utils import get_datetime, now_datetime, nowdate

	from vagabond import anh_bang, kenh_zalo

	try:
		ngay = nowdate()
		ten = "KB-%s" % ngay
		if not frappe.db.exists("Kiem Banh Ngay", ten):
			return None
		dong = frappe.get_all("Kiem Banh Dong", filters={"parent": ten, "parenttype": "Kiem Banh Ngay"},
			fields=["ma_hang", "ten_banh", "hinh", "co_the_ban"], limit_page_length=0, ignore_permissions=True)
		ds = danh_sach(dong)
		vt = dau_van_tay(ds)
		cu = frappe.cache().get_value(_khoa_cache(ngay)) or {}
		if cu.get("vt") == vt:
			return None
		bay = now_datetime()
		lan = get_datetime(cu["luc"]) if cu.get("luc") else None
		if not nen_gui(bay, lan):
			return None
		so_het = sum(1 for d in dong if int(d.get("co_the_ban") or 0) <= 0)
		gio = bay.strftime("%H:%M")
		chu = chu_tin(ds, so_het, gio)
		anh = anh_bang.anh_luoi("co-san", "Bánh có sẵn hôm nay %s" % bay.strftime("%d/%m"),
			"Cập nhật %s · số trên ảnh là số còn bán được" % gio,
			[{"ten": x["ten"], "so": x["so"], "anh": x["anh"]} for x in ds]) if ds else None
		kenh_zalo.bao_hoac_ghi_loi("ban_tin", "ban_hang", "Bánh có sẵn hôm nay", chu,
			link=kenh_zalo_url("/kiem-banh"), khoa="banh-co-san:%s:%s:%s" % (ngay, bay.strftime("%H%M"), vt), ma_tin="bh_banh_co_san", anh=anh)
		frappe.cache().set_value(_khoa_cache(ngay), {"vt": vt, "luc": str(bay)}, expires_in_sec=36 * 3600)
		frappe.db.commit()
		return vt
	except Exception as e:
		from vagabond.loi_csdl import chet_giao_dich

		if chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "Vagabond: tin bánh có sẵn hôm nay")
		return None


def kenh_zalo_url(duong):
	import frappe

	try:
		return frappe.utils.get_url(duong)
	except Exception:
		return duong
