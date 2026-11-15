# -*- coding: utf-8 -*-
"""Đơn WEBORDER: khách đặt qua tab Tại quầy trên trang chủ, quầy giao (v662).

Anh Việt chốt 15/11/2026
------------------------
Có những bánh bán tại bàn (O2O, khách quét QR trên bàn) nhưng KHÔNG bán giao
(bánh mong manh khó giao xa). Nên tách hai kênh: O2O chỉ mở bằng QR dán trên
bàn; WEBORDER là tab Tại quầy trên trang chủ, chỉ có món đã tick "Giao" ở Biên
tập menu (bien_tap_menu.ban_o_kenh). Bốn điều đã chọn theo phương án A:

1. Trả trước: chuyển khoản mã VietQR hoặc thẻ OnePay, dùng ĐÚNG luồng thanh
   toán của đơn web (bản ghi Vagabond Don Web, trang biên nhận /banh/xong/...).
   Không nhận tiền mặt. Tiền về (thanh_toan_web.sau_thu) đơn mới vào quầy.
2. Quầy bấm Xác nhận (hẹn 10, 15, 20 phút) hoặc Từ chối; từ chối đơn đã trả
   thì máy đánh dấu cần hoàn tiền và báo nhóm kế toán.
3. Đóng gói xong thu ngân bấm Gọi xe GreenSM ngay trên màn Đơn giao của quầy.
   Đơn WEBORDER KHÔNG thành vận đơn của Sales, để hai bên không lẫn (anh Việt:
   "tách riêng theo điểm bán").
4. Phí giao khách trả theo báo giá GreenSM từ chính quầy đó, miễn phí từ mức
   trong Cài đặt (mặc định 500.000 đ, anh Việt chốt; ô để trống là dùng mặc
   định, gõ 0 là tắt miễn phí).

Đơn không qua Pancake: bản ghi Don Web mang vgb_kenh = WEBORDER, trạng thái
Don Web đặt "Da nhan" ngay lúc lập để nhịp đối soát Pancake (don_web._dang_cho)
không đụng tới. Trạng thái của quầy nằm ở vgb_tt_quay.

Bill: lúc Xác nhận máy lập phiếu tạm tính ở quầy qua ĐÚNG ban_hang.tao_don_tay
(món theo giá điểm, phí giao thành dòng phí, phần giảm thành chiết khấu), để
trừ kho, ghi sổ, hoá đơn đi luồng quầy sẵn có. Thu ngân chốt phiếu bằng cách
khách đã trả trên web (Chuyển khoản hoặc OnePay).

Phần THUẦN nằm trên dòng `import frappe` trong thân hàm; kiểm ở
vagabond/khung/kiem_thu/thu_don_quay_662.py.
"""

import json
import re

KENH = "WEBORDER"
DT = "Vagabond Don Web"

TT_CHO_TRA = "Chờ trả tiền"
TT_CHO_XN = "Chờ quầy xác nhận"
TT_XN = "Đã xác nhận"
TT_GOI_XE = "Đã gọi xe"
TT_XONG = "Đã giao"
TT_TU_CHOI = "Từ chối"
TRANG_THAI = (TT_CHO_TRA, TT_CHO_XN, TT_XN, TT_GOI_XE, TT_XONG, TT_TU_CHOI)
# Đơn còn giữ món trên tủ (chưa giao xong, chưa từ chối). Chờ trả tiền chỉ giữ
# trong PHUT_GIU_CHUA_TRA phút: khách bỏ ngang thì món về lại tủ.
TT_GIU = (TT_CHO_TRA, TT_CHO_XN, TT_XN, TT_GOI_XE)
PHUT_GIU_CHUA_TRA = 30
PHUT_HEN = (10, 15, 20)
LY_DO_TU_CHOI = ("Hết món", "Quầy quá đông", "Ngoài giờ giao", "Khác")

MIEN_PHI_MAC_DINH = 500000
O_MIEN_PHI = "weborder_mien_phi_tu"
# Trả trước bắt buộc: không có tiền mặt.
PT_TRA_TRUOC = ("bank", "card", "atm")

TRUONG_MOI = {
	DT: [
		{"fieldname": "vgb_sec_weborder", "label": "Đơn giao của quầy (WEBORDER)", "fieldtype": "Section Break",
			"insert_after": "vgb_onepay_gd", "collapsible": 1},
		{"fieldname": "vgb_kenh", "label": "Kênh", "fieldtype": "Data", "insert_after": "vgb_sec_weborder",
			"read_only": 1, "no_copy": 1, "in_standard_filter": 1,
			"description": "WEBORDER: khách đặt qua tab Tại quầy trên trang chủ, quầy giao. Trống: đơn đặt bánh gửi Sales."},
		{"fieldname": "vgb_diem", "label": "Điểm bán", "fieldtype": "Data", "insert_after": "vgb_kenh",
			"read_only": 1, "no_copy": 1, "in_standard_filter": 1},
		{"fieldname": "vgb_tt_quay", "label": "Trạng thái ở quầy", "fieldtype": "Select",
			"options": "\n" + "\n".join(TRANG_THAI), "insert_after": "vgb_diem", "read_only": 1, "no_copy": 1,
			"in_standard_filter": 1},
		{"fieldname": "vgb_hen_phut", "label": "Hẹn xong sau (phút)", "fieldtype": "Int", "insert_after": "vgb_tt_quay",
			"read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_cb_weborder", "fieldtype": "Column Break", "insert_after": "vgb_hen_phut"},
		{"fieldname": "vgb_xn_luc", "label": "Quầy xử lý lúc", "fieldtype": "Datetime", "insert_after": "vgb_cb_weborder",
			"read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_xn_boi", "label": "Người xử lý", "fieldtype": "Data", "insert_after": "vgb_xn_luc",
			"read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_ly_do_quay", "label": "Lý do từ chối", "fieldtype": "Data", "insert_after": "vgb_xn_boi",
			"read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_can_hoan", "label": "Cần hoàn tiền", "fieldtype": "Check", "insert_after": "vgb_ly_do_quay",
			"read_only": 1, "no_copy": 1,
			"description": "Quầy từ chối đơn khách đã trả: kế toán hoàn tiền cho khách."},
		{"fieldname": "vgb_bill_quay", "label": "Phiếu tạm tính ở quầy", "fieldtype": "Link", "options": "Sales Invoice",
			"insert_after": "vgb_can_hoan", "read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_gsm_id", "label": "Mã đơn GreenSM", "fieldtype": "Data", "insert_after": "vgb_bill_quay",
			"read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_gsm_link", "label": "Link theo dõi tài xế", "fieldtype": "Data", "insert_after": "vgb_gsm_id",
			"read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_gsm_phi", "label": "Cước GreenSM tiệm trả", "fieldtype": "Currency", "insert_after": "vgb_gsm_link",
			"read_only": 1, "no_copy": 1},
	],
	"Vagabond Settings": [
		{"fieldname": O_MIEN_PHI, "label": "Miễn phí giao đơn giao của quầy (WEBORDER) từ", "fieldtype": "Currency",
			"insert_after": "mien_phi_giao_tu",
			"description": "Đơn đặt qua tab Tại quầy trên trang chủ đạt mức này (sau ưu đãi) thì khách không trả phí giao, "
				"tiệm trả cước GreenSM. Để trống là 500.000 đ. Gõ 0 là tắt miễn phí."},
	],
}


# v662 phần 3 (anh Việt 15/11/2026: "làm sẵn đi, Marketing điền sau"): khung bốn
# mã kéo khách từ GrabFood sang đặt thẳng. Gieo một lần ở trạng thái TẮT, mức
# giảm 0; Marketing điền mức trong màn Chương trình khuyến mãi rồi bật (máy chặn
# bật khi chưa có mức). Kênh WEBORDER để mã chỉ áp cho đơn giao của quầy; "Web
# giao" là nguồn phiếu tạm tính ở quầy của chính các đơn đó (ví quà phát sau ghi sổ).
KENH_MA = "WEBORDER\nWeb giao"
NHOM_DO_UONG = "Trà\nCà phê\nMatcha\nCacao"
KHUNG_MA = (
	{"ma_ctkm": "WEB-DON-DAU", "ten": "Đơn giao đầu tiên đặt thẳng trên web", "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "So tien", "cach_ma": "Ma co dinh", "ma_co_dinh": "GIAOLANDAU", "lan_moi_khach": 1, "hien_web": 1,
		"web_mo_ta": "Giảm cho đơn giao đầu tiên đặt thẳng trên web thay vì qua ứng dụng giao hàng."},
	{"ma_ctkm": "WEB-THE-GRAB", "ten": "Thẻ QR trong túi Grab, mã dùng một lần", "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "So tien", "cach_ma": "Ma dung mot lan",
		"web_mo_ta": "Mã in trên thẻ bỏ vào túi đơn GrabFood, mỗi mã dùng một lần."},
	{"ma_ctkm": "WEB-DON-HAI", "ten": "Đơn thứ hai trong 14 ngày (ví quà)", "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "Phan tram", "cach_ma": "Khong can ma", "vi_phat": 1, "vi_han_ngay": 14,
		"web_mo_ta": "Đặt giao xong, khách nhận quà vào ví dùng cho đơn sau trong 14 ngày."},
	{"ma_ctkm": "WEB-GIO-VANG", "ten": "Giờ vắng 14h tới 17h, đồ uống", "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "Phan tram", "cach_ma": "Khong can ma", "gio_tu": "14:00:00", "gio_den": "17:00:00",
		"pham_vi": "Nhom mon chi dinh", "nhom_mon": NHOM_DO_UONG,
		"web_mo_ta": "Đồ uống đặt giao trong khung 14h tới 17h."},
)


def dong_khung_ma(x):
	"""Một dòng khung mã -> dữ liệu bản ghi Vagabond CTKM: luôn TẮT, mức 0, kênh WEBORDER. THUẦN."""
	r = dict(x)
	r.update({"doctype": "Vagabond CTKM", "bat": 0, "gia_tri": 0, "kenh": KENH_MA,
		"ghi_chu": "Khung mã đơn giao của quầy (v662). Marketing điền mức giảm rồi bật."})
	return r


# ------------------------------------------------------------- phần thuần

def chuan_nguong(v):
	"""Ô Miễn phí giao người điền tay -> số đồng. THUẦN.

	Trống, None: mặc định 500.000. "0": tắt. Nhận "500000", "500.000",
	"500,000", "500k", "500 nghìn", "0,5tr", "1tr" (v608: ô cài đặt là đầu vào
	không tin được). Đọc không ra số thì dùng mặc định, không bao giờ tắt oan."""
	if v is None:
		return MIEN_PHI_MAC_DINH
	if isinstance(v, (int, float)):
		return max(0, int(v))
	s = str(v).strip().lower().replace(" ", "")
	if not s:
		return MIEN_PHI_MAC_DINH
	m = re.match(r"^([0-9]+(?:[.,][0-9]+)?)(k|nghìn|nghin|ngàn|ngan|tr|triệu|trieu|đ|d|vnd|vnđ)?$", s)
	if not m:
		so = re.sub(r"\D", "", s)
		return int(so) if so else MIEN_PHI_MAC_DINH
	so, don = m.group(1), m.group(2) or ""
	if don in ("k", "nghìn", "nghin", "ngàn", "ngan"):
		return int(round(float(so.replace(",", ".")) * 1000))
	if don in ("tr", "triệu", "trieu"):
		return int(round(float(so.replace(",", ".")) * 1000000))
	# Không đơn vị: dấu chấm, phẩy là phân cách nghìn ("500.000").
	return int(re.sub(r"\D", "", so) or 0)


def chuan_pt(v):
	"""Cách trả của đơn WEBORDER: chỉ trả trước. Tiền mặt hay giá trị lạ về
	chuyển khoản (biên nhận luôn có mã VietQR để trả ngay). THUẦN."""
	v = str(v or "").strip().lower()
	return v if v in PT_TRA_TRUOC else "bank"


def chuan_hen(v):
	"""Số phút hẹn khi quầy xác nhận: chỉ 10, 15, 20. Sai thì ValueError. THUẦN."""
	try:
		p = int(v)
	except (TypeError, ValueError):
		p = 0
	if p not in PHUT_HEN:
		raise ValueError("Chọn hẹn 10, 15 hoặc 20 phút.")
	return p


def chuan_ly_do(v):
	v = str(v or "").strip()
	return v if v in LY_DO_TU_CHOI else ""


# Chuyển trạng thái hợp lệ ở quầy. Chỉ đổi bản ghi đang ở đúng trạng thái nguồn
# (H8 loại 4): bấm hai lần, hai thu ngân bấm cùng lúc, màn cũ bấm muộn đều dừng.
CHUYEN = {
	"tien_ve": ((TT_CHO_TRA,), TT_CHO_XN),
	"xac_nhan": ((TT_CHO_XN,), TT_XN),
	"tu_choi": ((TT_CHO_TRA, TT_CHO_XN), TT_TU_CHOI),
	"goi_xe": ((TT_XN,), TT_GOI_XE),
	"xong": ((TT_XN, TT_GOI_XE), TT_XONG),
}


def chuyen_duoc(hien, viec):
	"""Trạng thái mới nếu việc này làm được từ trạng thái hiện tại, không thì None. THUẦN."""
	nguon, dich = CHUYEN.get(viec, ((), None))
	return dich if (hien or "") in nguon else None


CAU_DA_XU_LY = {TT_XN: "đã được xác nhận", TT_GOI_XE: "đã gọi xe", TT_XONG: "đã giao xong",
	TT_TU_CHOI: "đã bị từ chối", TT_CHO_TRA: "khách chưa trả tiền", TT_CHO_XN: "đang chờ xác nhận"}


def cau_khong_chuyen(ten, hien):
	return "Đơn %s %s, màn này vừa cũ. Tải lại danh sách." % (ten, CAU_DA_XU_LY.get(hien or "", "đã đổi trạng thái"))


def mon_tu_snapshot(snap):
	"""Các dòng món đơn WEBORDER đã chốt lúc đặt (giá máy chủ). THUẦN."""
	return list(((snap or {}).get("weborder") or {}).get("dong") or [])


def sl_giu(ds_snapshot):
	"""Số mỗi mã đang giữ trên tủ bởi các đơn WEBORDER còn hiệu lực: {mã: sl}.
	Combo tách thành phần; topping không tính (không có tồn). THUẦN."""
	ra = {}
	for snap in ds_snapshot or []:
		for d in mon_tu_snapshot(snap):
			if d.get("thanh_phan"):
				for y in d["thanh_phan"]:
					ra[y["ma"]] = ra.get(y["ma"], 0) + int(d.get("sl") or 0) * int(y.get("sl") or 0)
			elif d.get("loai") == "banh":
				ra[d["ma"]] = ra.get(d["ma"], 0) + int(d.get("sl") or 0)
	return ra


def con_giu(tt, luc, bay_gio, phut=PHUT_GIU_CHUA_TRA):
	"""Đơn ở trạng thái này, lập lúc `luc`, còn giữ món trên tủ không. THUẦN."""
	if tt not in TT_GIU:
		return False
	if tt != TT_CHO_TRA:
		return True
	try:
		return (bay_gio - luc).total_seconds() < phut * 60
	except TypeError:
		return False


BILL_TAM, BILL_CHOT, BILL_HUY = "tam", "chot", "huy"


def tt_bill(si):
	"""Trạng thái phiếu quầy của đơn theo đúng phép kiem_kho.da_ban: phiếu đã chốt
	(không tạm tính, không huỷ, chưa cancel) đã được tính là đã bán. THUẦN.
	si: dict {docstatus, vgb_tam_tinh, vgb_huy} hoặc None (không còn phiếu)."""
	if not si:
		return None
	if int(si.get("docstatus") or 0) >= 2 or int(si.get("vgb_huy") or 0):
		return BILL_HUY
	return BILL_TAM if int(si.get("vgb_tam_tinh") or 0) else BILL_CHOT


def giu_theo_bill(tt, luc, bay_gio, bill):
	"""Codex #573: mỗi phần bánh trừ ĐÚNG MỘT lần. Phiếu đã chốt thì
	kiem_kho.da_ban đã trừ, đơn thôi giữ (kể cả khi đơn chưa bấm Đã giao); phiếu
	còn tạm tính thì da_ban chưa trừ, đơn phải giữ (kể cả khi đã bấm Đã giao);
	chưa có phiếu hoặc phiếu đã huỷ thì giữ theo trạng thái đơn. THUẦN."""
	if tt == TT_TU_CHOI:
		return False
	if bill == BILL_CHOT:
		return False
	if bill == BILL_TAM:
		return True
	return con_giu(tt, luc, bay_gio)


def so_da_doi(kq, raw):
	"""Codex #573: tổng khách phải trả đổi so với lần khách vừa xem thì không tạo
	đơn: tiền món, phần giảm, phí giao (giao tận nơi) đều phải khớp số đã xem.
	Thiếu số đã xem là đổi (trình duyệt luôn gửi đủ ba số). THUẦN."""
	def so(v):
		if v in (None, ""):
			return None
		try:
			return int(round(float(v)))
		except (TypeError, ValueError):
			return None

	if so(raw.get("tien_hang_da_xem")) != int(kq.get("tien_hang") or 0):
		return True
	if (so(raw.get("giam_da_xem")) or 0) != int(kq.get("giam") or 0):
		return True
	return (not kq.get("tu_lay")) and so(raw.get("phi_da_xem")) != kq.get("phi")


def tong_phai_thu(r, snap):
	"""Tổng khách đã được báo và đã trả cho đơn: tiền món - giảm + phí giao. THUẦN."""
	uu = (snap or {}).get("uu_dai") or {}
	phi = (snap or {}).get("phi") or {}
	return int(r.get("tien_banh") or 0) - int(uu.get("giam") or 0) + int(phi.get("phi_khach") or 0)


def the_don(r, snap, anh=None):
	"""Thẻ một đơn cho màn Đơn giao của quầy. THUẦN (r: dict bản ghi; anh: {mã món: ảnh})."""
	wo = (snap or {}).get("weborder") or {}
	phi = (snap or {}).get("phi") or {}
	uu = (snap or {}).get("uu_dai") or {}
	return {
		"ma": r.get("name"), "tt": r.get("vgb_tt_quay") or "", "luc": str(r.get("creation") or "")[:16],
		"ten": r.get("ho_ten") or "", "sdt": r.get("dien_thoai") or "",
		"tu_lay": 1 if r.get("tu_lay") else 0, "dia_chi": (snap or {}).get("dia_chi") or "",
		"mon": [{"ten": d.get("ten"), "sl": int(d.get("sl") or 0), "tc": d.get("tc_chu") or "",
			"anh": (anh or {}).get(d.get("ma")) or "",
			"tp": [t.get("ten") for t in d.get("tp") or []]} for d in wo.get("dong") or []],
		"tien_hang": int(r.get("tien_banh") or 0), "giam": int(uu.get("giam") or 0),
		"phi": phi.get("phi_khach"), "mien_phi": 1 if phi.get("mien_phi") else 0,
		"da_thu": int(r.get("vgb_tt_da_thu") or 0), "cach_thu": r.get("vgb_tt_cach") or "",
		"hen": int(r.get("vgb_hen_phut") or 0), "ghi_chu": (snap or {}).get("ghi_chu") or "",
		"gsm_link": r.get("vgb_gsm_link") or "", "bill": r.get("vgb_bill_quay") or "",
		"can_hoan": 1 if r.get("vgb_can_hoan") else 0, "ly_do": r.get("vgb_ly_do_quay") or "",
	}


def soan_tin_moi(ten, ten_diem, r, snap, link):
	"""Tin Zalo nhóm cửa hàng khi đơn đã trả tiền và chờ quầy xác nhận. THUẦN."""
	wo = (snap or {}).get("weborder") or {}
	mon = ", ".join("%s x%d" % (d.get("ten"), int(d.get("sl") or 0)) for d in (wo.get("dong") or [])[:6])
	dong = ["Khách: %s" % (r.get("ho_ten") or ""),
		("Tự lấy tại quầy" if r.get("tu_lay") else "Giao tới: %s" % ((snap or {}).get("dia_chi") or "")),
		"Món: %s" % (mon or "xem trên app"),
		"Khách đã trả online. Xác nhận hoặc từ chối trong 5 phút."]
	if link:
		dong.append(link)
	return "Đơn giao mới %s · %s" % (ten, ten_diem), dong


# ------------------------------------------------------------- phần chạm hệ

import frappe  # noqa: E402

try:
	from frappe.rate_limiter import rate_limit  # noqa: E402
except ImportError:  # Frappe giả của bộ kiểm tầng khung
	def rate_limit(**_kw):
		return lambda f: f

NGUON_BILL = "Web giao"


def nguong_mien_phi():
	from vagabond.lib import cfg_o

	try:
		return chuan_nguong(cfg_o(O_MIEN_PHI))
	except Exception:
		return MIEN_PHI_MAC_DINH


def _diem_giao(ma):
	"""Điểm bán có quầy, đang bật, nhận đơn giao: dict của goi_mon_ban._diem."""
	from vagabond import goi_mon_ban

	return goi_mon_ban._diem(ma)


def toa_do_diem(d):
	"""Toạ độ quầy để báo phí GreenSM. Quầy chính (Cửa hàng Sài Gòn) dùng toạ độ
	đã khai trong Cài đặt; quầy khác tra từ địa chỉ trên thẻ Cửa hàng, nhớ một
	ngày. Không có thì None (đơn giao chưa mở cho quầy đó)."""
	from vagabond.lib import cache_get, cache_set, cfg

	c = cfg()
	ck = "vgb:weborder:toa:%s" % d["ma"]
	hit = cache_get(ck)
	if hit:
		try:
			return json.loads(hit)
		except ValueError:
			pass
	dia_chi = (d.get("dia_chi") or "").strip()
	kho = (c.get("store_address") or "").strip()
	if c.get("store_lat") and c.get("store_lng") and (not dia_chi or (kho and kho[:20].lower() == dia_chi[:20].lower())):
		ra = {"lat": float(c.store_lat), "lng": float(c.store_lng), "dia_chi": kho or dia_chi, "ten": d.get("ten_ngan") or d["ten"]}
	elif dia_chi:
		try:
			from vagabond.dia_chi import geocode

			g = geocode(c, dia_chi) or {}
		except Exception:
			frappe.log_error(frappe.get_traceback(), "don_quay: tra toạ độ quầy %s" % d["ma"])
			g = {}
		if not (g.get("lat") and g.get("lng")):
			return None
		ra = {"lat": float(g["lat"]), "lng": float(g["lng"]), "dia_chi": dia_chi, "ten": d.get("ten_ngan") or d["ten"]}
	else:
		return None
	cache_set(ck, json.dumps(ra), 86400)
	return ra


def giu_cua_diem(ma_diem, bo_ten=None):
	"""{mã: sl} món đang giữ trên tủ bởi đơn WEBORDER còn hiệu lực của điểm.
	MỘT nguồn cho bảng món gọi được (goi_mon_ban.bang_mon) của cả hai kênh."""
	from frappe.utils import add_days, now_datetime

	bay = now_datetime()
	try:
		# Đã giao mà phiếu còn tạm tính vẫn phải giữ (giu_theo_bill): đọc cả đơn Đã
		# giao trong hai ngày gần nhất, phần còn lại do phiếu quyết định.
		ds = frappe.get_all(DT, filters={"vgb_kenh": KENH, "vgb_diem": ma_diem,
			"vgb_tt_quay": ["in", list(TT_GIU) + [TT_XONG]], "creation": [">=", add_days(bay, -2)]},
			fields=["name", "vgb_tt_quay", "creation", "snapshot", "vgb_bill_quay"], limit_page_length=0,
			ignore_permissions=True)
	except Exception:
		# Site chưa có ô (chưa migrate xong): chưa có đơn WEBORDER nào.
		return {}
	ten_bill = sorted({r.get("vgb_bill_quay") for r in ds if r.get("vgb_bill_quay")})
	bill = {}
	if ten_bill:
		for si in frappe.get_all("Sales Invoice", filters={"name": ["in", ten_bill]},
				fields=["name", "docstatus", "vgb_tam_tinh", "vgb_huy"], limit_page_length=0, ignore_permissions=True):
			bill[si["name"]] = tt_bill(si)
	snaps = []
	for r in ds:
		b = bill.get(r.get("vgb_bill_quay")) if r.get("vgb_bill_quay") else None
		if r.get("vgb_bill_quay") and b is None:
			b = BILL_HUY  # phiếu đã bị xoá: như phiếu huỷ, giữ theo trạng thái đơn
		if r["name"] == bo_ten or not giu_theo_bill(r.get("vgb_tt_quay"), r.get("creation"), bay, b):
			continue
		try:
			snaps.append(json.loads(r.get("snapshot") or "{}"))
		except ValueError:
			continue
	return sl_giu(snaps)


def _khoa(ten, giay=10):
	return bool((frappe.db.sql("select get_lock(%s, %s)", (ten, giay)) or [[0]])[0][0])


def _nha(ten):
	try:
		frappe.db.sql("select release_lock(%s)", (ten,))
	except Exception:
		pass


def _bao_phi(d, dia_chi, lat, lng):
	"""Báo giá GreenSM từ quầy tới khách (giao_hang.phi_giao với điểm lấy là quầy)."""
	from vagabond.giao_hang import phi_giao

	toa = toa_do_diem(d)
	if not toa:
		return {"ok": 0, "ly_do": "chua_dien_toa_do_diem_lay"}
	return phi_giao(addr=dia_chi, lat=lat, lng=lng, diem_lay=toa)


def _uu_dai(dong, ma, sdt):
	"""Ưu đãi theo bộ tính chung (khuyen_mai.ap_web) ở kênh WEBORDER. Giỏ là các
	dòng đã chốt giá máy chủ, topping thành dòng riêng như hoá đơn quầy."""
	from vagabond import goi_mon_ban, khuyen_mai

	gio = [{"item_code": x["item_code"], "qty": int(x["qty"]), "rate": float(x["rate"])} for x in goi_mon_ban.dong_hoa_don(dong)]
	try:
		return khuyen_mai.ap_web(gio, ma=ma, sdt=sdt, nguon=KENH)
	except Exception:
		frappe.log_error(title="Vagabond: ưu đãi đơn giao của quầy", message=frappe.get_traceback())
		if ma:
			return {"tong_giam": 0, "ap": [], "ly_do": "Chưa kiểm được mã lúc này. Quý khách thử lại sau ít phút."}
		return {"tong_giam": 0, "ap": [], "ly_do": ""}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=60)
def xem_gia(don=None):
	"""Khách xem tổng trước khi gửi: tiền món, giảm, phí giao (đã áp miễn phí).
	Chỉ đọc. Số máy chủ trả lại ở tao_don mới là số chốt."""
	kq, loi = _tinh(don, chi_xem=True)
	return kq if not loi else {"ok": 0, "cau": loi}


def _doc_don(don):
	if isinstance(don, str):
		try:
			don = json.loads(don or "{}")
		except ValueError:
			return None
	return don if isinstance(don, dict) else None


def _tinh(don, chi_xem=False):
	"""(kết quả, câu lỗi). Dùng chung cho xem_gia và tao_don: một phép tính tiền."""
	from vagabond import bien_tap_menu, don_web, goi_mon_ban

	don = _doc_don(don)
	if don is None:
		return None, "Đơn không đọc được. Quý khách tải lại trang."
	d = _diem_giao(don.get("diem"))
	if not d:
		return None, "Quầy này chưa nhận đơn giao. Quý khách chọn quầy khác."
	try:
		bang = goi_mon_ban.bang_mon(d, kenh=bien_tap_menu.KENH_GIAO)
		dong, tien_hang = goi_mon_ban.chuan_gio(don.get("mon"), bang)
	except ValueError as e:
		return None, str(e)
	tu_lay = bool(don.get("tu_lay"))
	dia_chi = str(don.get("dia_chi") or "").strip()[:300]
	sdt = re.sub(r"\D", "", str(don.get("dien_thoai") or ""))
	ma = str(don.get("ma_uu_dai") or "").strip().upper()[:40]
	uu = _uu_dai(dong, ma, sdt)
	if ma and uu.get("ly_do") and not chi_xem:
		return None, uu["ly_do"]
	giam = int(uu.get("tong_giam") or 0) if not uu.get("ly_do") else 0
	bao_phi = None
	if not tu_lay:
		if len(dia_chi) < 8:
			if chi_xem:
				return {"ok": 1, "tien_hang": tien_hang, "giam": giam, "phi": None, "trang_thai_phi": "thieu_dia_chi",
					"nguong": nguong_mien_phi(), "loi_ma": uu.get("ly_do") or ""}, None
			return None, "Quý khách điền địa chỉ giao."
		bao_phi = _bao_phi(d, dia_chi, don.get("lat"), don.get("lng"))
		if bao_phi.get("ly_do") == "ngoai_vung_giao":
			return None, "Địa chỉ ngoài vùng giao của quầy. Quý khách chọn Tự lấy tại quầy."
	phi = don_web.quyet_phi_giao(tien_hang - giam, nguong_mien_phi(), tu_lay, bao_phi)
	if not tu_lay and phi.get("trang_thai") == "chua_ro" and not chi_xem:
		# Trả trước thì phải biết đúng số: không nhận đơn giao khi chưa báo được phí.
		return None, "Chưa báo được phí giao tới địa chỉ này. Quý khách thử lại sau ít phút hoặc chọn Tự lấy tại quầy."
	return {"ok": 1, "diem": d, "dong": dong, "tien_hang": tien_hang, "giam": giam, "uu": uu, "phi": phi.get("phi_khach"),
		"phi_day_du": phi, "trang_thai_phi": phi.get("trang_thai"), "nguong": nguong_mien_phi(),
		"tu_lay": tu_lay, "dia_chi": dia_chi, "sdt": sdt, "ma": ma, "loi_ma": uu.get("ly_do") or ""}, None


def _cong_khai(kq):
	"""Phần kết quả tính tiền được trả cho trình duyệt (không lộ dict điểm, dòng)."""
	return {k: kq[k] for k in ("ok", "tien_hang", "giam", "phi", "trang_thai_phi", "nguong", "loi_ma") if k in kq}


def _ds_ctkm(kq):
	"""Mã các chương trình bộ tính đã áp cho đơn (để khoá hàng), đã xếp."""
	return sorted({str(a.get("ma")) for a in ((kq or {}).get("uu") or {}).get("ap") or [] if a.get("ma")}) \
		if int((kq or {}).get("giam") or 0) else []


def ghi_chu_don(ten):
	"""Sợi dây nối lượt ưu đãi, mã dùng một lần với đơn (cùng mẫu đơn đặt bánh,
	để khuyen_mai.tra_luot_web, gan_hoa_don_web và việc dọn định kỳ dùng chung)."""
	from vagabond import don_web

	return don_web.GHI_CHU_DON_WEB % ten


def _giu_uu_dai(kq, ten, ho_ten, sdt):
	"""Codex #573: giữ mã dùng một lần và ghi lượt chương trình CÙNG giao dịch với
	bản ghi đơn (chưa commit), như đơn đặt bánh. Trả câu lỗi cho khách hoặc ""."""
	from vagabond import khuyen_mai

	if not int(kq.get("giam") or 0):
		return ""
	gc = ghi_chu_don(ten)
	try:
		ma = kq.get("ma") or ""
		if ma and khuyen_mai.ma_dung_mot_lan(ma) and not khuyen_mai.giu_ma_mot_lan(ma, gc):
			return "Mã %s vừa được dùng cho một đơn khác." % ma
		khuyen_mai.giu_luot_web((kq.get("uu") or {}).get("kq") or {}, khach=ho_ten, sdt=sdt, ghi_chu=gc)
	except Exception:
		frappe.log_error(title="Vagabond: giữ ưu đãi đơn giao của quầy", message=frappe.get_traceback())
		return "Chưa giữ được ưu đãi lúc này. Quý khách thử gửi lại sau ít phút."
	return ""


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=60)
def tao_don(don=None):
	"""Khách gửi đơn WEBORDER: kiểm món trên tủ trong khoá điểm, ghi bản ghi Don
	Web (kênh WEBORDER, Chờ trả tiền), trả đường biên nhận để khách trả ngay."""
	from vagabond import don_web, goi_mon_ban, khuyen_mai

	raw = _doc_don(don)
	if raw is None:
		return {"ok": 0, "cau": "Đơn không đọc được. Quý khách tải lại trang."}
	nonce = str(raw.get("nonce") or "")
	if not don_web.nonce_hop_le(nonce):
		return {"ok": 0, "cau": "Trang đã cũ. Quý khách tải lại trang rồi đặt lại."}
	if raw.get("dong_y") is not True:
		return {"ok": 0, "cau": "Quý khách chọn ô đồng ý ngay trên nút gửi."}
	ten = str(raw.get("ho_ten") or "").strip()[:80]
	sdt = re.sub(r"\D", "", str(raw.get("dien_thoai") or ""))
	if not ten or len(sdt) < 9:
		return {"ok": 0, "cau": "Quý khách điền tên và số điện thoại."}
	d = _diem_giao(raw.get("diem"))
	if not d:
		return {"ok": 0, "cau": "Quầy này chưa nhận đơn giao. Quý khách chọn quầy khác."}
	from frappe.utils import now_datetime

	if not goi_mon_ban._gio_mo_cua(d, now_datetime()):
		return {"ok": 0, "cau": "Quầy đang đóng cửa. Quý khách đặt lại trong giờ mở cửa."}
	# Chống trùng theo nonce một lần mở giỏ: gửi lại cùng nonce nhận lại đúng đơn cũ.
	hang_khoa = [{"variation_id": str(x.get("ma") or ""), "quantity": int(x.get("sl") or 0)}
		for x in (raw.get("mon") if isinstance(raw.get("mon"), list) else [])
		if isinstance(x, dict)] if isinstance(raw.get("mon"), list) else []
	khoa_trung = don_web.khoa_chong_trung(sdt, hang_khoa, "WEBORDER:" + d["ma"], nonce)
	trung = don_web.tim_trung(khoa_trung)
	if trung:
		return don_web.phan_hoi(trung, nonce, trung=True)
	# Kết thúc giao dịch đọc từ đầu yêu cầu rồi mới khoá điểm: đọc tủ SAU khoá
	# phải là ảnh chụp mới (H8 loại 1), không thì hai khách cùng lấy chiếc bánh cuối.
	frappe.db.commit()
	ten_khoa = "vagabond:weborder:%s" % d["ma"]
	if not _khoa(ten_khoa):
		return {"ok": 0, "cau": "Quầy đang nhận nhiều đơn cùng lúc. Quý khách bấm gửi lại sau vài giây."}
	try:
		trung = don_web.tim_trung(khoa_trung)
		if trung:
			return don_web.phan_hoi(trung, nonce, trung=True)
		kq, loi = _tinh(raw)
		if loi:
			return {"ok": 0, "cau": loi, "tai_lai": 1}
		ds_km = _ds_ctkm(kq)
		if ds_km:
			# Codex #573 (H8 loại 1): khoá hàng các chương trình sắp áp rồi TÍNH LẠI
			# trên ảnh chụp mới, như đơn đặt bánh (don_hang._giu_luot_uu_dai). Commit
			# trước để kết thúc ảnh chụp đọc cũ; khoá điểm get_lock vẫn giữ qua commit.
			frappe.db.commit()
			khuyen_mai.khoa_ctkm(ds_km)
			kq2, loi = _tinh(raw)
			if loi:
				return {"ok": 0, "cau": loi, "tai_lai": 1}
			if _ds_ctkm(kq2) != ds_km or kq2["giam"] != kq["giam"]:
				return dict(_cong_khai(kq2), ok=0, ly_do="gia_doi",
					cau="Ưu đãi vừa thay đổi (chương trình đã hết lượt hoặc vừa tắt). Quý khách xem lại tổng tiền rồi gửi lại.")
			kq = kq2
		if so_da_doi(kq, raw):
			# Số đổi trong lúc khách đọc giỏ (tiền món, giảm hay phí giao): cho
			# khách xem tổng mới rồi tự bấm lại.
			return dict(_cong_khai(kq), ok=0, ly_do="gia_doi",
				cau="Tổng tiền vừa cập nhật. Quý khách xem lại rồi bấm gửi.")
		pt = chuan_pt(raw.get("thanh_toan"))
		try:
			from vagabond import onepay as _op

			if pt in ("card", "atm") and not _op.dung_duoc():
				pt = "bank"
		except Exception:
			pt = "bank"
		phi = kq["phi_day_du"]
		snapshot = {
			"mon": [{"ma": x["ma"], "ten": x["ten"], "sl": int(x["sl"]), "gia": int(goi_mon_ban.gia_dong(x))} for x in kq["dong"]],
			"nguoi_dat": {"ho_ten": ten, "dien_thoai": sdt, "email": ""},
			"nguoi_nhan": None, "tu_lay": kq["tu_lay"],
			"dia_chi": kq["dia_chi"] if not kq["tu_lay"] else (d.get("dia_chi") or ""),
			"diem_lay_ten": (d.get("ten_ngan") or d["ten"]) if kq["tu_lay"] else "",
			"ngay_nhan": "", "ghi_chu": str(raw.get("ghi_chu") or "").strip()[:300], "ghi_chu_in": "", "the": [],
			"hoa_don": None, "thanh_toan": pt, "gioi_thieu_sdt": "", "phi": phi, "thieu_gia": [],
			"uu_dai": {"ma": kq["ma"], "giam": kq["giam"], "ap": kq["uu"].get("ap") or []} if kq["giam"] else None,
			"weborder": {"diem": d["ma"], "ten_diem": d.get("ten_ngan") or d["ten"],
				"dong": [dict(x, tc_chu=goi_mon_ban.mo_ta_tc(goi_mon_ban.tc_hien(x))) for x in kq["dong"]],
				"lat": raw.get("lat"), "lng": raw.get("lng")},
		}
		ban_ghi = don_web.tao_ban_ghi(nonce, {
			"ho_ten": ten, "dien_thoai": sdt, "tu_lay": 1 if kq["tu_lay"] else 0, "thanh_toan": pt,
			"tien_banh": kq["tien_hang"], "phi_khach": phi.get("phi_khach") or 0,
			"phi_ahamove": phi.get("phi_ahamove") or 0, "tiem_chiu_phi": phi.get("tiem_chiu") or 0,
			"mien_phi_giao": 1 if phi.get("mien_phi") else 0, "trang_thai_phi": phi.get("trang_thai"),
			"khoa_chong_trung": khoa_trung, "snapshot": json.dumps(snapshot, ensure_ascii=False),
			"vgb_kenh": KENH, "vgb_diem": d["ma"], "vgb_tt_quay": TT_CHO_TRA,
		})
		loi_giu = _giu_uu_dai(kq, ban_ghi.name, ten, sdt)
		if loi_giu:
			frappe.db.rollback()
			return {"ok": 0, "cau": loi_giu, "tai_lai": 1}
		# Không qua Pancake: đánh dấu đã nhận để nhịp đối soát Pancake bỏ qua.
		frappe.db.set_value(DT, ban_ghi.name, "trang_thai", "Da nhan", update_modified=False)
		ban_ghi.trang_thai = "Da nhan"
		frappe.db.commit()
	finally:
		_nha(ten_khoa)
	return don_web.phan_hoi(ban_ghi, nonce)


def sau_thu(ten):
	"""thanh_toan_web.sau_thu gọi khi đơn WEBORDER đã thu đủ: đơn vào quầy (Chờ
	quầy xác nhận) và báo nhóm cửa hàng. Chạy một lần (đóng dấu vgb_tt_bao_luc)."""
	from frappe.utils import now_datetime

	r = frappe.db.sql("select name, vgb_tt_quay, vgb_diem, ho_ten, tu_lay, snapshot from `tab%s` where name=%%s for update" % DT,
		(ten,), as_dict=True)
	if not r:
		return
	r = r[0]
	moi = chuyen_duoc(r.get("vgb_tt_quay"), "tien_ve")
	frappe.db.set_value(DT, ten, dict({"vgb_tt_bao_luc": now_datetime(), "vgb_tt_pancake": "weborder"},
		**({"vgb_tt_quay": moi} if moi else {})), update_modified=False)
	if moi:
		try:
			snap = json.loads(r.get("snapshot") or "{}")
		except ValueError:
			snap = {}
		try:
			from vagabond import kenh_zalo
			from vagabond.lien_ket_app import goc_app

			d = _diem_giao(r.get("vgb_diem")) or {"ten": r.get("vgb_diem") or ""}
			tieu_de, dong = soan_tin_moi(ten, d.get("ten_ngan") or d.get("ten"), r, snap, goc_app() + "/ban-tai-quay")
			kenh_zalo.bao("viec", "ban_hang", tieu_de, dong, khoa="weborder-moi:%s" % ten,
				kiem="weborder_cho", nguon=ten, ma_tin="bh_weborder_moi")
		except Exception:
			frappe.log_error(frappe.get_traceback(), "don_quay: báo đơn giao mới %s" % ten)


def con_cho_xac_nhan(ten):
	"""Điều kiện nhắc lại của tin đơn giao mới: còn chờ quầy xác nhận không."""
	return frappe.db.get_value(DT, ten, "vgb_tt_quay") == TT_CHO_XN


def _kiem_quyen():
	from vagabond import goi_mon_ban

	goi_mon_ban._kiem_quyen_quay()


def _doc_khoa(ten):
	"""Đọc HIỆN TẠI bản ghi WEBORDER dưới khoá hàng (for update)."""
	r = frappe.db.sql("select * from `tab%s` where name=%%s and vgb_kenh=%%s for update" % DT, (ten, KENH), as_dict=True)
	if not r:
		frappe.throw("Không có đơn giao %s." % ten)
	return r[0]


def _snap(r):
	try:
		return json.loads(r.get("snapshot") or "{}")
	except ValueError:
		return {}


NGAY_XEM = (1, 7)


def chuan_ngay_xem(v):
	"""Khoảng ngày màn Đơn giao của quầy: 1 (24 giờ) hoặc 7 ngày; lạ thì 1. THUẦN."""
	try:
		n = int(v)
	except (TypeError, ValueError):
		return NGAY_XEM[0]
	return n if n in NGAY_XEM else NGAY_XEM[0]


@frappe.whitelist()
def danh_sach(diem=None, ngay=None):
	"""Màn Đơn giao của quầy: đơn chờ xác nhận, đang làm, đã gọi xe; đơn đã giao
	hay từ chối xếp cuối. Khoảng ngày 24 giờ hoặc 7 ngày (chip trên màn). Đơn
	chưa trả tiền không hiện. Món kèm ảnh danh mục (AGENTS.md 2b.4)."""
	from frappe.utils import add_days, now_datetime

	from vagabond import goi_mon_ban

	_kiem_quyen()
	so_ngay = chuan_ngay_xem(ngay)
	from vagabond import bien_tap_menu

	cac = bien_tap_menu._diem_co_quay()
	d = _diem_giao(diem) or (_diem_giao(cac[0]["ma"]) if cac else None)
	if not d:
		return {"ds": [], "diem": "", "cac_diem": []}
	ds = frappe.get_all(DT, filters={"vgb_kenh": KENH, "vgb_diem": d["ma"], "vgb_tt_quay": ["!=", TT_CHO_TRA],
		"creation": [">=", add_days(now_datetime(), -so_ngay)]},
		fields=["name", "creation", "ho_ten", "dien_thoai", "tu_lay", "tien_banh", "snapshot", "vgb_tt_quay", "vgb_hen_phut",
			"vgb_tt_da_thu", "vgb_tt_cach", "vgb_gsm_link", "vgb_bill_quay", "vgb_can_hoan", "vgb_ly_do_quay"],
		order_by="creation asc", limit_page_length=0)
	thu_tu = {TT_CHO_XN: 0, TT_XN: 1, TT_GOI_XE: 2, TT_XONG: 3, TT_TU_CHOI: 4}
	snaps = [(r, _snap(r)) for r in ds]
	try:
		anh = goi_mon_ban._anh_mon(sorted({x.get("ma") for _, sn in snaps for x in mon_tu_snapshot(sn) if x.get("ma")}))
	except Exception:
		anh = {}
	the = sorted((the_don(r, sn, anh) for r, sn in snaps), key=lambda x: (thu_tu.get(x["tt"], 9), x["luc"]))
	return {"ds": the, "diem": d["ma"], "ten_diem": d.get("ten_ngan") or d["ten"], "hen": list(PHUT_HEN), "ngay": so_ngay,
		"ly_do": list(LY_DO_TU_CHOI), "cac_diem": [{"ma": x["ma"], "ten": x.get("ten_ngan") or x["ten"]} for x in cac]}


def dem_cho(ma_diem):
	"""Số đơn giao chờ xác nhận của điểm, cho dải chờ trên mọi màn (goi_mon_ban.dem_cho)."""
	try:
		return frappe.db.count(DT, {"vgb_kenh": KENH, "vgb_diem": ma_diem, "vgb_tt_quay": TT_CHO_XN})
	except Exception:
		return 0


def _nguon_bill(d):
	"""Nguồn đơn cho phiếu tạm tính: "Mang về" nếu điểm có, không thì "Tại chỗ"."""
	ds = [str(x) for x in d.get("nguon") or []]
	for n in ds:
		if n.startswith("Mang về"):
			return n
	from vagabond import goi_mon_ban

	return goi_mon_ban.NGUON_TAO


@frappe.whitelist(methods=["POST"])
def xac_nhan(ma=None, hen=None):
	"""Quầy nhận đơn: hẹn 10, 15, 20 phút, lập phiếu tạm tính ở quầy.

	Codex #573: tao_don_tay tự commit giữa chừng, nên khoá hàng (for update)
	nhả ra trước khi đơn đổi trạng thái. Khoá phiên get_lock theo mã đơn giữ
	suốt lượt (qua các lần commit): hai thu ngân bấm cùng lúc thì người sau
	chờ, rồi đọc lại thấy đơn đã xác nhận, không lập phiếu thứ hai.
	Phiếu giữ ĐÚNG giá khách đã trả (giá chốt lúc đặt), không lấy lại bảng giá
	điểm; tổng phiếu lệch số khách đã trả thì xoá phiếu nháp và dừng."""
	_kiem_quyen()
	try:
		phut = chuan_hen(hen)
	except ValueError as e:
		frappe.throw(str(e))
	return _mot_luot(ma, _xac_nhan_trong_khoa, ma, phut)


def _mot_luot(ma, ham, *args):
	"""Codex #573 (H8 loại 1, 4): mọi việc đổi trạng thái một đơn ở quầy chạy
	trong khoá phiên get_lock theo mã đơn, giữ qua các lần commit giữa chừng
	(tao_don_tay, GreenSM). Hai máy bấm cùng lúc: máy sau chờ rồi đọc lại."""
	ten_khoa = "vagabond:weborder-don:%s" % (ma or "")
	frappe.db.commit()
	if not _khoa(ten_khoa, 15):
		frappe.throw("Đơn %s đang được một máy khác xử lý. Đợi vài giây rồi tải lại danh sách." % ma)
	try:
		return ham(*args)
	finally:
		_nha(ten_khoa)


def _xac_nhan_trong_khoa(ma, phut):
	from frappe.utils import now_datetime

	from vagabond import ban_hang, goi_mon_ban, khuyen_mai

	r = _doc_khoa(ma)
	moi = chuyen_duoc(r.get("vgb_tt_quay"), "xac_nhan")
	if not moi:
		frappe.throw(cau_khong_chuyen(ma, r.get("vgb_tt_quay")))
	d = _diem_giao(r.get("vgb_diem"))
	if not d:
		frappe.throw("Điểm bán của đơn không còn quầy đang bật.")
	snap = _snap(r)
	dong = mon_tu_snapshot(snap)
	uu = snap.get("uu_dai") or {}
	phi = snap.get("phi") or {}
	mong = tong_phai_thu(r, snap)
	import random

	sr = random.SystemRandom()
	gc = ("Đơn giao web %s (%s), khách đã trả trước %s đ qua %s. Chốt phiếu bằng đúng cách đó." % (
		ma, "tự lấy" if r.get("tu_lay") else "giao tận nơi", "{:,}".format(int(r.get("vgb_tt_da_thu") or 0)).replace(",", "."),
		r.get("vgb_tt_cach") or "chuyển khoản"))[:300]
	# Cờ chỉ máy chủ đặt được (không đi qua lời gọi của trình duyệt): giữ giá dòng.
	frappe.flags.vgb_gia_chot = True
	try:
		kq = ban_hang.tao_don_tay(
			nguon=_nguon_bill(d), quay=d["ma"], ma_don=goi_mon_ban.ma_bill_moi(d["ma"], sr.choice),
			ten_khach=r.get("ho_ten") or "Khách đặt web", dien_thoai=r.get("dien_thoai") or "",
			items=goi_mon_ban.dong_hoa_don(dong), tam_tinh=1, so_ban=("Web " + str(ma))[-12:], ghi_chu=gc,
			giam_gia=int(uu.get("giam") or 0), phi_ship=int(phi.get("phi_khach") or 0))
	finally:
		frappe.flags.vgb_gia_chot = False
	bill = (kq or {}).get("name") or ""
	if bill and int(round(float((kq or {}).get("grand_total") or 0))) != mong:
		# Không để thu ngân chốt một phiếu khác số khách đã trả.
		try:
			frappe.delete_doc("Sales Invoice", bill, ignore_permissions=True, force=1)
			frappe.db.commit()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "don_quay: xoá phiếu lệch tổng %s" % bill)
		frappe.throw("Phiếu tạm tính ra %s đ, khác số khách đã trả %s đ cho đơn %s. Máy chưa xác nhận đơn; báo quản lý kiểm giá món." % (
			"{:,}".format(int(round(float(kq.get("grand_total") or 0)))).replace(",", "."), "{:,}".format(mong).replace(",", "."), ma))
	if bill:
		# Cùng cách phiếu gọi món tại bàn (goi_mon_ban.NGUON_QR): nguồn riêng để
		# báo cáo tách được đơn giao web, thanh toán đi như "Mang về" (ban_hang.NGUON_CU).
		frappe.db.set_value("Sales Invoice", bill, "custom_nguon", NGUON_BILL, update_modified=False)
		if int(uu.get("giam") or 0):
			# Codex #573: lượt ưu đãi và mã đã giữ lúc đặt nối với phiếu.
			khuyen_mai.gan_hoa_don_web(ghi_chu_don(ma), bill)
	frappe.db.set_value(DT, ma, {"vgb_tt_quay": moi, "vgb_hen_phut": phut, "vgb_xn_luc": now_datetime(),
		"vgb_xn_boi": frappe.session.user, "vgb_bill_quay": bill or None}, update_modified=False)
	frappe.db.commit()
	return {"ok": 1, "tt": moi, "bill": bill}


@frappe.whitelist(methods=["POST"])
def tu_choi(ma=None, ly_do=None):
	"""Quầy từ chối: đơn đã trả thì đánh dấu cần hoàn tiền và báo nhóm kế toán."""
	_kiem_quyen()
	ly = chuan_ly_do(ly_do)
	if not ly:
		frappe.throw("Chọn lý do từ chối.")
	return _mot_luot(ma, _tu_choi_trong_khoa, ma, ly)


def _tu_choi_trong_khoa(ma, ly):
	from frappe.utils import now_datetime

	r = _doc_khoa(ma)
	moi = chuyen_duoc(r.get("vgb_tt_quay"), "tu_choi")
	if not moi:
		frappe.throw(cau_khong_chuyen(ma, r.get("vgb_tt_quay")))
	da_tra = int(r.get("vgb_tt_da_thu") or 0)
	frappe.db.set_value(DT, ma, {"vgb_tt_quay": moi, "vgb_ly_do_quay": ly, "vgb_xn_luc": now_datetime(),
		"vgb_xn_boi": frappe.session.user, "vgb_can_hoan": 1 if da_tra else 0}, update_modified=False)
	# Codex #573: đơn không thành thì trả lượt ưu đãi và mã dùng một lần đã giữ,
	# cùng giao dịch với việc đổi trạng thái (khoá hàng của đơn đang giữ).
	from vagabond import khuyen_mai

	khuyen_mai.tra_luot_web(ghi_chu_don(ma))
	if da_tra:
		try:
			from vagabond import kenh_zalo

			kenh_zalo.bao("viec", "cong_no", "Hoàn tiền đơn giao web %s" % ma,
				["Quầy từ chối: %s." % ly, "Khách %s đã trả %s đ qua %s." % (r.get("ho_ten") or "",
					"{:,}".format(da_tra).replace(",", "."), r.get("vgb_tt_cach") or "chuyển khoản"),
					"Kế toán liên hệ khách để hoàn tiền."],
				khoa="weborder-hoan:%s" % ma, nguon=ma, ma_tin="kt_hoan_tien")
		except Exception:
			frappe.log_error(frappe.get_traceback(), "don_quay: báo hoàn tiền %s" % ma)
	frappe.db.commit()
	return {"ok": 1, "tt": moi, "can_hoan": 1 if da_tra else 0}


@frappe.whitelist(methods=["POST"])
def xong(ma=None):
	"""Quầy bấm Đã giao xong (khách đã nhận hoặc tài xế đã giao)."""
	_kiem_quyen()
	return _mot_luot(ma, _xong_trong_khoa, ma)


def _xong_trong_khoa(ma):
	r = _doc_khoa(ma)
	moi = chuyen_duoc(r.get("vgb_tt_quay"), "xong")
	if not moi:
		frappe.throw(cau_khong_chuyen(ma, r.get("vgb_tt_quay")))
	frappe.db.set_value(DT, ma, "vgb_tt_quay", moi, update_modified=False)
	frappe.db.commit()
	return {"ok": 1, "tt": moi}


def _gsm_diem(c, r, d):
	from vagabond import greensm

	toa = toa_do_diem(d)
	if not toa:
		frappe.throw("Chưa có toạ độ quầy để gọi xe. Báo kỹ thuật khai địa chỉ quầy.")
	snap = _snap(r)
	wo = snap.get("weborder") or {}
	if not (wo.get("lat") and wo.get("lng")):
		from vagabond.dia_chi import geocode

		g = geocode(c, snap.get("dia_chi") or "") or {}
		wo = dict(wo, lat=g.get("lat"), lng=g.get("lng"))
	if not (wo.get("lat") and wo.get("lng")):
		frappe.throw("Không tìm được toạ độ địa chỉ khách. Gọi xe bằng app GreenSM.")
	lay = greensm.diem("PICK UP", toa["lat"], toa["lng"], toa["ten"], c.get("ahamove_mobile"), toa["dia_chi"], hang=True)
	giao = greensm.diem("DROP OFF", float(wo["lat"]), float(wo["lng"]), r.get("ho_ten") or "Khách", r.get("dien_thoai"),
		snap.get("dia_chi") or "")
	return lay, giao


@frappe.whitelist(methods=["POST"])
def gsm_bao_gia(ma=None):
	"""Giá GreenSM cho đúng đơn này (giữ bản giá phía máy chủ 30 phút)."""
	import time

	from vagabond import greensm
	from vagabond.lib import cache_set, cfg

	_kiem_quyen()
	r = frappe.db.get_value(DT, {"name": ma, "vgb_kenh": KENH}, ["name", "vgb_diem", "vgb_tt_quay", "ho_ten", "dien_thoai",
		"snapshot", "tu_lay"], as_dict=True)
	if not r or r.get("tu_lay"):
		frappe.throw("Đơn này khách tự lấy, không gọi xe.")
	if r.get("vgb_tt_quay") != TT_XN:
		frappe.throw(cau_khong_chuyen(ma, r.get("vgb_tt_quay")))
	c = cfg()
	if not greensm.co_khoa(c):
		frappe.throw("Chưa khai khoá GreenSM trong Cài đặt, mục GreenSM Express.")
	if greensm.dang_thu(c):
		frappe.throw("GreenSM đang ở môi trường thử, gọi xe sẽ không có tài xế thật.")
	lay, giao = _gsm_diem(c, r, _diem_giao(r.get("vgb_diem")) or {"ma": r.get("vgb_diem"), "ten": ""})
	try:
		bg, than = greensm.bao_gia(c, lay, giao, int(time.time()))
	except greensm.LoiGsm as e:
		frappe.throw("GreenSM chưa báo được giá: %s" % str(e)[:200])
	cache_set("vgb:weborder:gsm:%s" % ma, json.dumps({"bg": bg, "than": than}), 1800)
	return {"ok": 1, "tong": bg["tong"], "km": bg.get("km"), "ma_gia": str(bg.get("fee_id") or "")}


@frappe.whitelist(methods=["POST"])
def goi_xe(ma=None, ma_gia=None):
	"""Gọi xe GreenSM từ bản giá vừa xem. Chỉ một lần cho một đơn (khoá đơn)."""
	_kiem_quyen()
	return _mot_luot(ma, _goi_xe_trong_khoa, ma, ma_gia)


def _goi_xe_trong_khoa(ma, ma_gia):
	from vagabond import greensm
	from vagabond.lib import cache_get, cache_set, cfg

	r = _doc_khoa(ma)
	moi = chuyen_duoc(r.get("vgb_tt_quay"), "goi_xe")
	if not moi or r.get("vgb_gsm_id"):
		frappe.throw(cau_khong_chuyen(ma, r.get("vgb_tt_quay")))
	hit = cache_get("vgb:weborder:gsm:%s" % ma)
	if not hit:
		frappe.throw("Giá GreenSM đã hết hạn. Bấm Xem giá lại rồi Gọi xe.")
	giu = json.loads(hit)
	if not ma_gia or str(ma_gia) != str(giu["bg"].get("fee_id") or ""):
		frappe.throw("Giá GreenSM của đơn này vừa được xem lại ở màn khác. Bấm Xem giá lại rồi Gọi xe.")
	c = cfg()
	try:
		kq = greensm.goi(c, "/create-order", greensm.than_tao_don(giu["bg"], giu["than"], ma, int(r.get("tien_banh") or 0)))
	except greensm.LoiGsm as e:
		frappe.log_error(title="Vagabond: GreenSM gọi xe đơn giao quầy", message=str(e)[:1000])
		frappe.throw("GreenSM từ chối: %s" % str(e)[:200])
	cache_set("vgb:weborder:gsm:%s" % ma, "", 1)
	dd = (kq or {}).get("data") or {}
	frappe.db.set_value(DT, ma, {"vgb_tt_quay": moi, "vgb_gsm_id": str(dd.get("id") or ""),
		"vgb_gsm_link": str(dd.get("tracking_url") or ""), "vgb_gsm_phi": float(giu["bg"].get("tong") or 0)},
		update_modified=False)
	frappe.db.commit()
	return {"ok": 1, "tt": moi, "link": str(dd.get("tracking_url") or "")}


def gieo_khung_ma():
	"""Gieo khung bốn mã (tắt, mức 0) một lần. Mã đã có thì để nguyên: Marketing
	có thể đã điền mức, bật hay đổi tên. Bỏ qua bước kiểm mức giảm của chương
	trình vì mức để trống là chủ ý (bật lên mới bắt điền)."""
	da = 0
	for x in KHUNG_MA:
		if frappe.db.exists("Vagabond CTKM", x["ma_ctkm"]):
			continue
		doc = frappe.get_doc(dong_khung_ma(x))
		doc.flags.ignore_validate = True
		doc.flags.ignore_permissions = True
		doc.insert()
		da += 1
	return da
