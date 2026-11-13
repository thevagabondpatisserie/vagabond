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

v654: tin lặp lại dù số không đổi (anh Việt 13/11/2026, ảnh tin 09:32)
---------------------------------------------------------------------
Đo trên site 13/11: 13 tin từ 08:02 tới 11:03, nhiều cặp liền nhau giống hệt
từng dòng (08:32, 08:48, 09:02, 09:20, 09:32 cùng 12 loại 23 bánh). Tin 09:02
đi chỉ 13 phút sau tin 08:48, tức lúc đó máy không còn nhớ cả giờ gửi trước:
"lần gửi trước" chỉ nằm trong bộ nhớ đệm Redis, mất là gửi lại; khoá chống
trùng lại có giờ phút nên sổ tin không chặn được. Từ v654 lần gửi trước đọc
từ chính SỔ TIN (dòng Vagabond Tin Kenh mới nhất hôm nay, ô `dau`), ghi cùng
giao dịch với tin, có khoá có tên để hai lượt chạy chồng không cùng gửi.
Dấu chỉ gồm mã bánh (mỗi cỡ một mã) và số bán được: giờ cập nhật, thứ tự hiện,
ảnh vẽ lại không làm đổi dấu. Zalo chậm trả lời thì dòng tin vẫn đã có dấu
(trạng thái "Chưa rõ"), nhịp sau không gửi lại.

Tin đầu ngày: chỉ gửi khi bảng Kiểm bánh hôm nay đã có ít nhất một bánh bán
được. Bảng còn trống thì im (không báo "hết bánh" lúc chưa ra lò). Đã từng
báo có bánh mà nay hết sạch thì báo một tin "đã hết".
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


def can_gui(vt, so_loai, cu, bay_gio, lan_cuoi=None):
	"""Quyết định gửi một tin. THUẦN.

	vt: dấu trạng thái bây giờ; so_loai: số loại còn bán; cu: dấu lần gửi gần
	nhất hôm nay (None là chưa gửi tin nào hôm nay, "" là dòng cũ chưa có dấu);
	lan_cuoi: giờ lần gửi đó. Trả (gửi hay không, lý do ngắn)."""
	if cu is None and not so_loai:
		return False, "đầu ngày, bảng chưa có bánh bán được"
	if cu is not None and cu == vt:
		return False, "số bán được không đổi"
	if not nen_gui(bay_gio, lan_cuoi):
		return False, "chưa đủ %d phút hoặc ngoài giờ" % PHUT_GIUA
	return True, "số bán được đổi" if cu else "tin đầu ngày"


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


MA_TIN = "bh_banh_co_san"
KHOA_CHAY = "vgb_banh_co_san_quet"


def khoa_tin(ngay, vt, luc_truoc):
	"""Khoá chống trùng của một tin: ngày, dấu mới và giờ của tin đứng trước nó.
	Hai lượt chạy chồng cùng thấy một tin trước thì ra cùng khoá, sổ tin chỉ nhận
	một dòng (lớp chặn thứ hai sau khoá có tên). Trạng thái quay lại giống một
	lần trước thì tin trước đã khác nên vẫn gửi được. THUẦN."""
	return "banh-co-san:%s:%s:%s" % (ngay, vt, str(luc_truoc or "dau-ngay")[:19])


def lan_gui_cuoi(ngay):
	"""(dấu, giờ) của dòng tin Bánh có sẵn mới nhất hôm nay trong sổ tin, hay
	(None, None) khi hôm nay chưa có. Một nguồn: chính sổ tin, không phải bộ
	nhớ đệm (v654)."""
	import frappe

	r = frappe.get_all("Vagabond Tin Kenh", filters={"ma_tin": MA_TIN, "creation": [">=", "%s 00:00:00" % ngay]},
		fields=["dau", "creation"], order_by="creation desc", limit_page_length=1, ignore_permissions=True)
	if not r:
		return None, None
	return (r[0].get("dau") or ""), r[0].get("creation")


def quet():
	"""Nhịp 5 phút. Không bao giờ ném lỗi ra ngoài (trừ lỗi làm chết giao dịch)."""
	import frappe

	k = frappe.db.sql("select get_lock(%s, 0)", (KHOA_CHAY,))
	if not k or k[0][0] != 1:
		# Lượt trước chưa xong (vẽ ảnh, Zalo chậm): lượt này nhường, không gửi chồng.
		return None
	try:
		return _quet()
	finally:
		try:
			frappe.db.sql("select release_lock(%s)", (KHOA_CHAY,))
		except Exception:
			pass


def _quet():
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
		cu, luc = lan_gui_cuoi(ngay)
		if cu is None:
			# Chưa có dòng nào trong sổ hôm nay (nhóm chưa tích tin này thì không có
			# dòng): nhớ tạm trong bộ nhớ đệm để không ghi lỗi "chưa có nhóm" mỗi 5 phút.
			dem = frappe.cache().get_value(_khoa_cache(ngay)) or {}
			if dem.get("vt") == vt:
				return None
		bay = now_datetime()
		gui, _ly_do = can_gui(vt, len(ds), cu, bay, get_datetime(luc) if luc else None)
		if not gui:
			return None
		so_het = sum(1 for d in dong if int(d.get("co_the_ban") or 0) <= 0)
		gio = bay.strftime("%H:%M")
		chu = chu_tin(ds, so_het, gio)
		anh = anh_bang.anh_luoi("co-san", "Bánh có sẵn hôm nay %s" % bay.strftime("%d/%m"),
			"Cập nhật %s · số trên ảnh là số còn bán được" % gio,
			[{"ten": x["ten"], "so": x["so"], "anh": x["anh"]} for x in ds]) if ds else None
		kenh_zalo.bao_hoac_ghi_loi("ban_tin", "ban_hang", "Bánh có sẵn hôm nay", chu,
			link=kenh_zalo_url("/kiem-banh"), khoa=khoa_tin(ngay, vt, luc), ma_tin="bh_banh_co_san", anh=anh, dau=vt)
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
