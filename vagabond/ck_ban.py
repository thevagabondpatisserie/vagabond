# -*- coding: utf-8 -*-
"""Khách tại bàn chuyển khoản ngay trên điện thoại (v678).

ANH VIỆT 20/11/2026
-------------------
*"khi mà khách nhấn vào nút chuyển khoản thì sẽ cho chọn ngân hàng, rồi nó
sẽ nhảy sang cái app ngân hàng ở trên điện thoại của khách luôn ... Máy sẽ tự
điền số tiền, nội dung chuyển khoản, khách chỉ việc quét Face ID là xong."*
rồi chốt *"hệ thống sẽ tự chốt luôn"*.

Bảng Thanh toán của trang gọi món tại bàn có thêm cách "Chuyển khoản ngay":
  - thong_tin: số tiền của hoá đơn tạm tính của bàn, tài khoản nhận (tài khoản
    ảo của điểm bán, như mã QR thu ngân đưa), nội dung là MÃ BILL, ảnh VietQR
    dựng tại máy chủ và đường mở từng app ngân hàng (pt_ck.link_app).
  - trang_thai: trang hỏi lại vài giây một lần; bill còn tạm tính thì thử tự
    chốt (tu_chot_ck.thu_chot, lưới an toàn khi hàng đợi webhook chậm).

Không lộ mã hoá đơn nội bộ (HDB-...): trang chỉ biết mã bill in trên tờ tạm
tính, cũng là nội dung chuyển khoản.
"""

import re

import frappe
from frappe.utils import cint, flt

try:
	from frappe.rate_limiter import rate_limit
except ImportError:  # Frappe giả của bộ kiểm tầng khung
	def rate_limit(**_kw):
		return lambda f: f

from vagabond import ma_bill, pt_ck

SI = "Sales Invoice"
RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------ THUẦN


def noi_dung_ck(ma, diem, rieng):
	"""Nội dung chuyển khoản của một bill. CÙNG LUẬT với posNoiDungCk của màn
	tính tiền (09-tinh-tien-quay.js): tài khoản riêng của điểm, hay mã đã mang
	tiền tố điểm, thì chỉ mã bill; mã cũ VGB trên tài khoản chung thì kèm mã
	điểm ở đầu. THUẦN."""
	b = str(ma or "").strip().upper()
	if rieng or not b:
		return b
	tt, _ = ma_bill.tach_tien_to(b)
	if tt and tt != ma_bill.TIEN_TO_CU:
		return b
	d = str(diem or "").strip().upper()
	return (d + " " + b) if d else b


def ds_app(tk, tien, noi_dung, ma_nh):
	"""Các nút mở app ngân hàng cho trang khách. THUẦN. Bỏ nút không dựng
	được đường dẫn (thiếu số tài khoản hay mã ngân hàng)."""
	ra = []
	for app, ten, tu_dien in pt_ck.APP_NGAN_HANG:
		link = pt_ck.link_app(app, (tk or {}).get("stk"), ma_nh, tien, noi_dung)
		if link:
			ra.append({"ma": app, "ten": ten, "tu_dien": tu_dien, "link": link})
	return ra


def tt_cho_khach(b, ket_qua_chot=None):
	"""Trạng thái chuyển khoản gửi trang khách. THUẦN.

	b  dict bill: vgb_huy, vgb_tam_tinh, docstatus, vgb_pt_thanh_toan
	Trả "da_tra" (bill đã chốt bằng chuyển khoản, hay máy vừa tự chốt),
	"da_chot" (thu ngân chốt bằng cách khác), "huy", hoặc "cho"."""
	if cint(b.get("vgb_huy")) or cint(b.get("docstatus")) == 2:
		return "huy"
	if (ket_qua_chot or {}).get("ok"):
		return "da_tra"
	if cint(b.get("vgb_tam_tinh")) and cint(b.get("docstatus")) == 0:
		return "cho"
	return "da_tra" if pt_ck.la_ck(b.get("vgb_pt_thanh_toan")) else "da_chot"


# ------------------------------------------------------------ phần chạm hệ


def _bill_ban(d, n):
	from vagabond import uu_dai_ban

	return uu_dai_ban._hoa_don_ban(d, n)


def _ghi_hoa_don(si, hd):
	"""Lưu mã số thuế hay email xuất hoá đơn khách gõ, khi bill còn trống ô đó."""
	from vagabond import ban_hang, uu_dai_ban

	hd = str(hd or "").strip()[:80]
	if not hd:
		return False
	if RE_EMAIL.match(hd):
		o, gt = "vgb_xhd_email", hd
	else:
		o, gt = "vgb_xhd_mst", ban_hang._chuan_mst(hd)
	if not gt or (si.get(o) or "").strip():
		return False
	si = frappe.get_doc(SI, si.name, for_update=True)
	if si.docstatus != 0 or (si.get(o) or "").strip():
		return False
	si.set(o, gt)
	with uu_dai_ban._luu_bang_quyen_he_thong():
		si.flags.ignore_permissions = True
		si.save(ignore_permissions=True)
	return True


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=600)
def thong_tin(diem=None, ban=None, k=None, hd=""):
	"""Thông tin để khách chuyển khoản hoá đơn tạm tính của bàn."""
	from vagabond import goi_mon_ban, qr_chuyen_khoan, tai_khoan
	from vagabond import thanh_toan_nhieu as ttn

	d, n = goi_mon_ban._kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": "Link bàn không đúng, quý khách quét lại mã QR trên bàn."}
	si = _bill_ban(d, n)
	if not si:
		return {"ok": 0, "cau": "Bàn chưa có hoá đơn. Quý khách chờ quầy nhận món rồi chuyển khoản."}
	if ttn.dong_cua(si.name):
		return {"ok": 0, "cau": "Hoá đơn của bàn đang chia nhiều cách trả. Quý khách báo nhân viên để thanh toán."}
	tien = int(round(flt(si.grand_total)))
	ma = str(si.get("custom_pancake_display_id") or "").strip().upper()
	if tien <= 0 or not ma_bill.hop_le(ma):
		return {"ok": 0, "cau": "Hoá đơn chưa có số tiền. Quý khách báo nhân viên để thanh toán."}
	tk = tai_khoan.tk_cho(si.get("custom_nguon"), si.get("vgb_quay"))
	nd = noi_dung_ck(ma, si.get("vgb_quay"), cint(tk.get("rieng")))
	anh = qr_chuyen_khoan.anh_qr(tk, tien, nd)
	ma_nh = pt_ck.ma_nh_vietqr(tk.get("bank"))
	try:
		_ghi_hoa_don(si, hd)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ck_ban: lưu thông tin xuất hoá đơn lỗi")
	return {
		"ok": 1, "ma": ma, "tien": tien, "noi_dung": nd,
		"ngan_hang": tai_khoan._ten_ngan_hang(tk.get("bank")), "stk": tk.get("stk") or "",
		"chu_tk": tk.get("ten") or "", "anh": anh,
		"app": ds_app(tk, tien, nd, ma_nh),
	}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=150, seconds=600)
def trang_thai(diem=None, ban=None, k=None, ma=None):
	"""Trang khách hỏi tiền đã về chưa. Bill còn tạm tính thì thử tự chốt."""
	from vagabond import goi_mon_ban, tu_chot_ck, uu_dai_ban

	d, n = goi_mon_ban._kiem_link(diem, ban, k)
	ma = str(ma or "").strip().upper()
	if not d or not ma_bill.hop_le(ma):
		return {"ok": 0}
	r = frappe.db.get_value(SI, {"custom_pancake_display_id": ma, "vgb_quay": d["ma"], "vgb_so_ban": str(n)},
		["name", "docstatus", "vgb_tam_tinh", "vgb_huy", "vgb_pt_thanh_toan"], as_dict=True)
	if not r:
		return {"ok": 0}
	kq = None
	if cint(r.get("vgb_tam_tinh")) and cint(r.get("docstatus")) == 0 and not cint(r.get("vgb_huy")):
		try:
			with uu_dai_ban._luu_bang_quyen_he_thong():
				kq = tu_chot_ck.thu_chot(r["name"])
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "ck_ban: tự chốt khi khách hỏi lỗi")
	tt = tt_cho_khach(r, kq)
	ra = {"ok": 1, "tt": tt}
	if tt == "cho":
		# Bàn gọi thêm món sau khi lấy mã: trang thấy số mới thì lấy mã mới.
		ra["tien"] = int(round(flt(frappe.db.get_value(SI, r["name"], "grand_total"))))
	return ra
