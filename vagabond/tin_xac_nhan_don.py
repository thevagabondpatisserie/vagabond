# -*- coding: utf-8 -*-
"""Tin Zalo xác nhận đơn đặt bánh trên web (v684, anh Việt 22/11/2026).

Khách đặt bánh xong (Pancake đã nhận đơn) thì máy gửi một tin Zalo theo mẫu đã
duyệt: mã đơn, ngày nhận, cách nhận, số tiền thanh toán, trạng thái thanh toán, và nút
"Xem trạng thái đơn hàng" mở đúng trang biên nhận của đơn đó (khách chưa trả
thì trả tiếp từ đây).

Luật:
  - Chưa khai mã mẫu ở Cài đặt (`zns_template_xac_nhan_don`) là chưa gửi, đơn
    vẫn chạy như cũ. Mẫu do Zalo duyệt, câu chữ nằm trong mẫu, máy chỉ điền
    tham số, đọc bộ tham số từ chính mẫu đã duyệt (template/info/v2).
  - Một đơn một tin. Trạng thái ghi trên Vagabond Don Web (`vgb_zxn`). Dòng
    "Đang gửi" khoá trước khi gọi Zalo; lượt gọi chết giữa chừng thì KHÔNG gửi
    lại (không biết Zalo đã gửi chưa), để Lỗi kèm lý do.
  - Zalo không nhận tin mẫu từ 22h tới 6h: đơn đặt lúc đó chờ, nhịp 5 phút gửi
    khi tới giờ. Trạng thái thanh toán đọc lúc gửi.
  - Đường dẫn biên nhận mang token mà máy chủ chỉ lưu BĂM (don_web). Token chỉ
    có lúc khách vừa gửi đơn, nên máy cất bản MÃ HOÁ (bảng mật khẩu của Frappe)
    tới lúc gửi xong rồi xoá ngay. Không ghi token vào nhật ký hay câu lỗi.
  - Kiểm thử tích hợp không bao giờ bắn tin ra ngoài (cửa ở zalo.gui_mau).

Phần THUẦN ở đầu tệp để bộ kiểm tầng khung gọi thẳng.
"""

import json
from datetime import timedelta

DT = "Vagabond Don Web"
O_MAU = "zns_template_xac_nhan_don"
O_TT, O_LUC, O_LOI = "vgb_zxn", "vgb_zxn_luc", "vgb_zxn_loi"
O_MA = "vgb_zxn_ma"  # tên ô trong bảng mật khẩu (__Auth), không phải cột

TT_CHO, TT_DANG, TT_GUI, TT_LOI, TT_BO = "Cho gui", "Dang gui", "Da gui", "Loi", "Bo qua"
TT = (TT_CHO, TT_DANG, TT_GUI, TT_LOI, TT_BO)

GIO_TU, GIO_DEN = 6, 22  # luật Zalo cho tin mẫu
HAN_NGAY = 3  # đơn chờ quá 3 ngày (mẫu chưa duyệt, mất mạng dài) thì thôi
TREO_PHUT = 30  # "Đang gửi" quá 30 phút: lượt gọi đã chết

TRUONG_MOI = {
	DT: [
		{"fieldname": "vgb_sec_zxn", "label": "Tin Zalo xác nhận đơn", "fieldtype": "Section Break",
			"insert_after": "vgb_gsm_phi", "collapsible": 1},
		{"fieldname": O_TT, "label": "Tin xác nhận", "fieldtype": "Select",
			"options": "\n" + "\n".join(TT), "insert_after": "vgb_sec_zxn", "read_only": 1, "no_copy": 1,
			"in_standard_filter": 1,
			"description": "Máy gửi tin Zalo xác nhận cho khách sau khi Pancake nhận đơn. Trống: chưa khai mã mẫu lúc khách đặt."},
		{"fieldname": O_LUC, "label": "Gửi lúc", "fieldtype": "Datetime", "insert_after": O_TT,
			"read_only": 1, "no_copy": 1},
		{"fieldname": O_LOI, "label": "Lý do chưa gửi", "fieldtype": "Small Text", "insert_after": O_LUC,
			"read_only": 1, "no_copy": 1},
	],
	"Vagabond Settings": [
		{"fieldname": O_MAU, "label": "Mã mẫu ZNS xác nhận đơn đặt bánh trên web", "fieldtype": "Data",
			"insert_after": "zns_template_otp",
			"description": "Mã mẫu Zalo đã duyệt (ID mẫu ZBS) cho tin gửi khách ngay sau khi đặt bánh trên web, "
				"có nút Xem trạng thái đơn hàng. Để trống là không gửi."},
	],
}

# Nhãn trạng thái thanh toán trong tin (dữ liệu điền vào mẫu, không phải chữ trang web).
NHAN_TT = {"Da thu": "Đã thanh toán", "Thu thieu": "Đã trả một phần"}
NHAN_CHO = "Chờ thanh toán"


# ---------------------------------------------------------------- phần thuần


def trong_gio(luc):
	"""Zalo nhận tin mẫu trong [6h, 22h). THUẦN."""
	return GIO_TU <= luc.hour < GIO_DEN


def nhan_thanh_toan(trang_thai_thu):
	"""Trạng thái thu online của đơn -> chữ điền vào tin. THUẦN."""
	return NHAN_TT.get(str(trang_thai_thu or "").strip(), NHAN_CHO)


def cat(s, n):
	s = " ".join(str(s or "").split())
	return s if len(s) <= n else s[: max(n - 1, 0)].rstrip() + "…"


def gia_tri(ban_ghi, snap, tom_tat, token):
	"""Giá trị nghiệp vụ cho mẫu. THUẦN. `tom_tat` là don_web.tom_tat_bien_nhan
	(MỘT nguồn cho ngày nhận, cách nhận với trang biên nhận); số tiền là số
	thanh toán online (ttt.tien_ban_ghi["online"], cùng phép cổng thanh toán và
	trang biên nhận). Phí giao chưa tính được thì đó là tiền bánh, phí trả lúc nhận.
	Mẫu khai ô tiền kiểu Tiền tệ thì zalo_kich_ban.chuan_tham_so lấy chữ số."""
	from vagabond import thanh_toan_web_thuan as ttt

	ban_ghi, snap, tt = ban_ghi or {}, snap or {}, tom_tat or {}
	ngay = " ".join(x for x in (tt.get("ngay_nhan"), tt.get("khung_gio")) if x)
	so_tien = ttt.tien_ban_ghi(ban_ghi, snap)["online"]
	return {
		"ten_khach": cat((snap.get("nguoi_dat") or {}).get("ho_ten") or "quý khách", 30),
		"ma_don": str(ban_ghi.get("pancake_display_id") or ban_ghi.get("name") or ""),
		"ngay_nhan": ngay,
		"cach_nhan": tt.get("cach_nhan") or "",
		"so_tien": int(round(float(so_tien or 0))),
		"trang_thai": nhan_thanh_toan(ban_ghi.get("vgb_tt_trang_thai")),
		"ma_xem": token or "",
	}


def ly_do_bo(ban_ghi, sdt84, co_mau, co_token):
	"""Đơn này có còn gửi được không. Trả câu lý do (rỗng là gửi được). THUẦN."""
	if (ban_ghi or {}).get("trang_thai") == "Da huy":
		return "Đơn đã huỷ trước khi tới giờ gửi."
	if not co_mau:
		return "Chưa khai mã mẫu Zalo xác nhận đơn ở Cài đặt."
	if not sdt84:
		return "Đơn không có số điện thoại hợp lệ."
	if not co_token:
		return "Không còn đường dẫn biên nhận của đơn để gắn vào nút."
	return ""


def treo(luc_bat_dau, bay_gio):
	"""Lượt "Đang gửi" bắt đầu quá TREO_PHUT phút trước: coi như đã chết. THUẦN."""
	if not luc_bat_dau:
		return True
	return bay_gio - luc_bat_dau > timedelta(minutes=TREO_PHUT)


# ---------------------------------------------------------------- chạm hệ


def _bay_gio():
	from frappe.utils import now_datetime

	return now_datetime()


def _mau():
	from vagabond.lib import cfg

	return str(cfg().get(O_MAU) or "").strip()


def xep(ban_ghi, nonce):
	"""Gọi ngay sau khi Pancake nhận đơn (don_hang.tao_don). KHÔNG BAO GIỜ làm
	hỏng đơn: mọi lỗi chỉ ghi Error Log. Chưa có mã mẫu thì không cất token.

	Token biên nhận tính lại từ nonce của lần gửi này (don_web.token_cua), cùng
	phép với đường dẫn trả về trình duyệt."""
	import frappe

	try:
		if not _mau() or not nonce:
			return False
		from vagabond import don_web

		token = don_web.token_cua(ban_ghi, nonce)
		ten = ban_ghi.name
		if not token or frappe.db.get_value(DT, ten, O_TT):
			return False  # lần gửi trùng của khách: đơn đã có tin
		from frappe.utils.password import set_encrypted_password

		set_encrypted_password(DT, ten, token, O_MA)
		frappe.db.set_value(DT, ten, {O_TT: TT_CHO, O_LOI: ""}, update_modified=False)
		frappe.db.commit()
		frappe.enqueue("vagabond.tin_xac_nhan_don.gui", queue="short", ten=ten, enqueue_after_commit=True)
		return True
	except Exception:
		try:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "tin_xac_nhan_don: xếp tin %s" % getattr(ban_ghi, "name", ""))
		except Exception:
			pass
		return False


def _token(ten):
	import frappe
	from frappe.utils.password import get_decrypted_password

	try:
		return get_decrypted_password(DT, ten, O_MA, raise_exception=False) or ""
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tin_xac_nhan_don: đọc mã biên nhận %s" % ten)
		return ""


def _xoa_token(ten):
	import frappe
	from frappe.utils.password import remove_encrypted_password

	try:
		remove_encrypted_password(DT, ten, O_MA)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tin_xac_nhan_don: xoá mã biên nhận %s" % ten)


def _xong(ten, tt, loi=""):
	import frappe

	gt = {O_TT: tt, O_LOI: cat(loi, 500)}
	if tt == TT_GUI:
		gt[O_LUC] = _bay_gio()
	frappe.db.set_value(DT, ten, gt, update_modified=False)
	if tt in (TT_GUI, TT_LOI, TT_BO):
		_xoa_token(ten)
	frappe.db.commit()


def gui(ten):
	"""Gửi tin cho MỘT đơn đang Chờ gửi. Khoá dòng, đổi sang Đang gửi rồi mới
	gọi Zalo (hai lượt chạy cùng lúc không gửi hai tin)."""
	import frappe

	from vagabond import zalo, zalo_kich_ban
	from vagabond.lib import cfg, sdt84

	bay_gio = _bay_gio()
	if not trong_gio(bay_gio):
		return "ngoai_gio"
	row = frappe.db.sql("select name, %s, trang_thai, dien_thoai, snapshot, pancake_display_id, vgb_tt_trang_thai, "
		"thanh_toan, tien_banh, trang_thai_phi from `tab%s` where name = %%s for update" % (O_TT, DT), (ten,), as_dict=True)
	if not row or row[0].get(O_TT) != TT_CHO:
		frappe.db.rollback()
		return "khong_cho"
	d = row[0]
	mau = _mau()
	so = sdt84(d.get("dien_thoai") or "")
	token = _token(ten)
	ly = ly_do_bo(d, so, bool(mau), bool(token))
	if ly:
		_xong(ten, TT_BO, ly)
		return "bo"
	frappe.db.set_value(DT, ten, {O_TT: TT_DANG, O_LUC: bay_gio, O_LOI: ""}, update_modified=False)
	frappe.db.commit()
	try:
		from vagabond import don_web

		snap = json.loads(d.get("snapshot") or "{}")
		gt = gia_tri(d, snap, don_web.tom_tat_bien_nhan(d, snap), token)
		info = zalo.doc_mau(mau)
		if not info.get("ok"):
			# Đọc mẫu không được (mất mạng, token Zalo): chưa gọi gửi, trả về Chờ gửi.
			frappe.db.set_value(DT, ten, {O_TT: TT_CHO, O_LOI: cat("Chưa đọc được mẫu Zalo: %s" % info.get("loi"), 500)},
				update_modified=False)
			frappe.db.commit()
			return "cho"
		data, thieu = zalo_kich_ban.du_lieu_mau(gt, info.get("tham_so"))
		if thieu:
			_xong(ten, TT_LOI, "Mẫu Zalo đòi tham số máy không có: %s. Kiểm lại mã mẫu ở Cài đặt." % ", ".join(thieu))
			return "loi"
		j = zalo.gui_mau(cfg(), so, mau, data, "vgb-xn-%s" % ten)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "tin_xac_nhan_don: gửi %s" % ten)
		_xong(ten, TT_LOI, "Máy lỗi khi gửi, không biết Zalo đã nhận chưa nên không gửi lại.")
		return "loi"
	ma, cau = zalo_kich_ban.y_nghia_loi(j)
	if ma == 0:
		_xong(ten, TT_GUI)
		return "da_gui"
	_xong(ten, TT_LOI, cau)
	return "loi"


def quet():
	"""Nhịp 5 phút: gửi đơn đang chờ (đặt lúc 22h tới 6h, lần trước hỏng mạng),
	dọn đơn chờ quá hạn và lượt Đang gửi đã chết."""
	import frappe

	bay_gio = _bay_gio()
	moc = bay_gio - timedelta(days=HAN_NGAY)
	for r in frappe.get_all(DT, filters={O_TT: TT_DANG}, fields=["name", O_LUC], limit_page_length=500):
		if treo(r.get(O_LUC), bay_gio):
			_xong(r.name, TT_LOI, "Lượt gửi trước dừng giữa chừng, không biết Zalo đã nhận chưa nên không gửi lại.")
	for r in frappe.get_all(DT, filters={O_TT: TT_CHO, "creation": ["<", moc]}, fields=["name"], limit_page_length=500):
		_xong(r.name, TT_BO, "Chờ quá %d ngày chưa gửi được." % HAN_NGAY)
	if not trong_gio(bay_gio):
		return 0
	n = 0
	for r in frappe.get_all(DT, filters={O_TT: TT_CHO}, fields=["name"], order_by="creation asc", limit_page_length=200):
		try:
			n += 1 if gui(r.name) == "da_gui" else 0
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "tin_xac_nhan_don: quét %s" % r.name)
	return n
