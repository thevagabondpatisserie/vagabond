"""v638: khách đặt bánh trên web trả thẻ OnePay ngay trên biên nhận, chạy trên ERPNext thật.

Đi ĐÚNG các cửa: bản ghi Vagabond Don Web lập bằng `don_web.tao_ban_ghi` (như
tao_don), trang /tra-the đọc đơn bằng khoá riêng, `onepay.tao_gd` (phiên khách)
tạo giao dịch cho số còn phải trả với vpc_CardList theo cách khách chọn, OnePay
gọi `ipn` với PHIÊN KHÁCH và chữ ký HMAC. Đọc lại Don Web: các ô thu online mới
(Custom Field thật, có cột), nhật ký thẻ; IPN lặp không cộng thêm. Rồi hoá đơn
Sales của đơn đó lấy phương thức OnePay từ bản ghi đơn web, qua `_chuan_bi_ghi_so`
và GHI SỔ thật (không bị chốt chuyển khoản chặn), sổ cái cân. Khoá OnePay là giá
trị bịa trong điểm lưu, không phải khoá thật của tiệm. Không gọi Pancake: đơn
chưa có mã Pancake trong ca (ghi Pancake trả "cho_ma_don"), cờ kiểm thật chặn tin.
"""
import json
from unittest.mock import patch

import frappe
from frappe.utils import flt, now_datetime

from vagabond import ban_hang, don_web
from vagabond import onepay as op
from vagabond import thanh_toan_web as tw
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _mon, _nen
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_onepay_633 import KHOA, _bat_onepay, _goi_ipn, _ket_qua, _pt_onepay
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi


def _don_web(tien, ma_pc):
	snap = {"mon": [], "nguoi_dat": {"ho_ten": "Khách kiểm 638", "dien_thoai": "0909638638"},
		"thanh_toan": "atm", "phi": {"trang_thai": "tu_lay", "phi_khach": 0}, "gioi_thieu_sdt": ""}
	b = don_web.tao_ban_ghi("KiemThat638" + frappe.generate_hash(length=16), {
		"ho_ten": "Khách kiểm 638", "dien_thoai": "0909638638", "ngay_nhan": now_datetime(), "tu_lay": 1,
		"thanh_toan": "atm", "tien_banh": tien, "phi_khach": 0, "phi_ahamove": 0, "tiem_chiu_phi": 0,
		"mien_phi_giao": 0, "trang_thai_phi": "tu_lay", "khoa_chong_trung": "kt638" + frappe.generate_hash(length=20),
		"snapshot": json.dumps(snap, ensure_ascii=False)})
	_DA_TAO.append((b.doctype, b.name))
	frappe.db.set_value(don_web.DOCTYPE, b.name, {"trang_thai": "Da nhan", "pancake_display_id": ma_pc}, update_modified=False)
	return b.name


@ca("v638 đơn web trả thẻ ATM qua OnePay: tao_gd phiên khách gửi DOMESTIC, IPN ghi Don Web đúng một lần, hoá đơn Sales lấy OnePay và GHI SỔ được")
def _vong_doi():
	cty, tk, _mau = _nen()
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	acc = frappe.db.get_value("Bank Account", ba, "account")
	_pt_onepay(cty, acc)
	_bat_onepay()
	dung("cấu hình đọc được và đủ", op.dung_duoc())
	tien = 650000
	ma_pc = "KT638" + frappe.generate_hash(length=8).upper()
	ten = _don_web(tien, ma_pc)
	ma = ten.replace("-", "")
	k = op.khoa_phieu(ma)
	la("khoá sai thì không thấy đơn", op.thong_tin_trang(ma, "0" * 16), None)
	la("trang thẻ thấy đúng số còn phải trả", (op.thong_tin_trang(ma, k) or {}).get("con"), float(tien))
	truoc = frappe.session.user
	try:
		frappe.set_user("Guest")
		url = op.tao_gd(ma, k)["url"]
	finally:
		frappe.set_user(truoc)
	dung("sang cổng OnePay, thẻ nội địa", url.startswith("https://mtf.onepay.vn/paygate/vpcpay.op?") and "vpc_CardList=DOMESTIC" in url)
	nk = op.doc_nhat_ky(frappe.db.get_value(don_web.DOCTYPE, ten, tw.O_NK))
	la("một giao dịch chờ, đúng số", [(g["trang_thai"], flt(g["so_tien"])) for g in nk], [("cho", float(tien))])
	gd = nk[0]["ma"]
	la("chữ ký giả: từ chối", _goi_ipn(_ket_qua(gd, tien, khoa="FFFF" + KHOA[4:])), op.DAP_IPN_SAI)
	la("chữ ký giả không ghi", frappe.db.get_value(don_web.DOCTYPE, ten, "vgb_tt_trang_thai") or "", "")
	la("IPN thành công: xác nhận", _goi_ipn(_ket_qua(gd, tien)), op.DAP_IPN_OK)
	la("IPN lặp: vẫn xác nhận", _goi_ipn(_ket_qua(gd, tien)), op.DAP_IPN_OK)
	d = frappe.db.get_value(don_web.DOCTYPE, ten, ["vgb_tt_trang_thai", "vgb_tt_da_thu", "vgb_tt_cach", "vgb_tt_ma_gd",
		"vgb_tt_pancake", "vgb_tt_bao_luc"], as_dict=True)
	la("Don Web đã thu đúng một lần", (d.vgb_tt_trang_thai, flt(d.vgb_tt_da_thu), d.vgb_tt_cach), ("Da thu", float(tien), "OnePay"))
	la("một giao dịch ghi nhận", [g["gd"] for g in json.loads(d.vgb_tt_ma_gd)], [gd])
	la("chưa có mã Pancake hệ thống: chờ ghi Pancake", d.vgb_tt_pancake, "cho_ma_don")
	dung("đã đóng dấu báo Sales", bool(d.vgb_tt_bao_luc))
	la("trang thẻ báo đã trả", op.thong_tin_trang(ma, k)["con"], 0.0)

	pt, ma_tc = ban_hang._pt_don_web("", ma_pc)
	la("hoá đơn lấy phương thức từ đơn web", (pt, ma_tc), ("OnePay", gd))
	from vagabond import diem_ban
	cac_diem = diem_ban.diem_cua_nguon("GrabFood")
	quay = next((m for m in cac_diem if not diem_ban.theo_ma(m)["quay"]), cac_diem[0])
	with patch.object(ban_hang, "_cong_ty", return_value=cty):
		ra = khong_nem("lập hoá đơn nháp", lambda: ban_hang.tao_don_tay(nguon="GrabFood", quay=quay, ma_don="KT638-" + frappe.generate_hash(length=8),
			items=[dict(item_code=_mon(tk), qty=1, rate=tien)], tam_tinh=1))
	if not ra:
		return
	_DA_TAO.append(("Sales Invoice", ra["name"]))
	si = frappe.get_doc("Sales Invoice", ra["name"])
	si.vgb_tam_tinh = 0
	si.custom_nguon = "Pancake"
	si.custom_pancake_display_id = ma_pc
	si.vgb_pt_thanh_toan = pt
	si.vgb_ma_tham_chieu = ma_tc
	si.save(ignore_permissions=True)
	si.reload()
	khong_nem("chuẩn bị ghi sổ (không bị chốt chuyển khoản chặn)", lambda: ban_hang._chuan_bi_ghi_so(si))
	khong_nem("ghi sổ hoá đơn", lambda: si.submit())
	si.reload()
	la("hoá đơn đã ghi sổ, phương thức OnePay", (si.docstatus, si.vgb_pt_thanh_toan), (1, "OnePay"))
	gl = frappe.get_all("GL Entry", filters={"voucher_type": "Sales Invoice", "voucher_no": si.name, "is_cancelled": 0},
		fields=["debit", "credit"], limit_page_length=0)
	dung("có sổ cái", len(gl) >= 2)
	la("sổ cái cân", round(sum(flt(r.debit) for r in gl) - sum(flt(r.credit) for r in gl)), 0)
