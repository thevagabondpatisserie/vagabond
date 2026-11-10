"""v638: khách gọi món tại bàn qua QR, quầy nhận, chạy trên ERPNext thật.

Đi ĐÚNG các cửa: khách (phiên Guest) gọi `goi_mon_ban.goi` với link ký bằng
khoá mã hoá THẬT của site, bản ghi Vagabond Goi Mon Ban lập thật (doctype mới,
cột nonce duy nhất); thu ngân gọi `goi_mon_ban.nhan`, máy lập phiếu tạm tính
qua `ban_hang.tao_don_tay` thật (ERPNext chạy trọn validate của Sales Invoice
nháp), đọc lại phiếu: đủ món, đúng giá điểm, đúng bàn, nguồn "QR tại bàn". Đơn
gọi thêm của cùng bàn vào CÙNG phiếu. Không ghi sổ, không gửi gì ra ngoài (cờ
kiểm thật chặn tin Zalo). Giờ mở cửa cố định "đang mở" để ca không phụ thuộc
giờ chạy.
"""
import json
from unittest.mock import patch

import frappe
from frappe.utils import flt

from vagabond import ban_hang, diem_ban
from vagabond import goi_mon_ban as g
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen


def _nhom_tra():
	if not frappe.db.exists("Item Group", "Trà"):
		ng = frappe.get_doc({"doctype": "Item Group", "item_group_name": "Trà",
			"parent_item_group": frappe.db.get_value("Item Group", {"is_group": 1}, "name"), "is_group": 0})
		ng.insert(ignore_permissions=True)
		_DA_TAO.append((ng.doctype, ng.name))
	return "Trà"


def _tra(gia):
	d = frappe.get_doc(dict(doctype="Item", item_code="KT638T-" + frappe.generate_hash(length=8), item_name="Trà kiểm 638",
		item_group=_nhom_tra(), stock_uom=frappe.db.get_value("UOM", {}, "name"), is_stock_item=0, is_sales_item=1,
		standard_rate=gia))
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


@ca("v638 gọi món tại bàn: khách (Guest) gọi qua link ký thật, thu ngân nhận, phiếu tạm tính của bàn có đủ món đúng giá; gọi thêm vào cùng phiếu")
def _vong_doi():
	cty, _tk, _mau = _nen()
	quay = next((d for d in diem_ban.ds(chi_bat=True) if d["quay"] and d["ma"] in diem_ban.diem_cua_nguon(g.NGUON_TAO)), None)
	dung("có điểm bán có quầy nhận Tại chỗ", quay)
	if not quay:
		return
	ma = _tra(45000)
	gia = g.gia_mon(ma, diem_ban.gia_rieng(quay["ma"]), 45000)
	ban = 87
	k = g.khoa_ban(g._bi_mat(), quay["ma"], ban)
	kh = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name")
	with patch.object(g, "_gio_mo_cua", return_value={"dang_mo": True, "gio": "7:00 - 22:00"}), \
			patch.object(ban_hang, "_cong_ty", return_value=cty), patch.object(ban_hang, "_khach_le", return_value=kh):
		truoc = frappe.session.user
		try:
			frappe.set_user("Guest")
			sai = g.goi(diem=quay["ma"], ban=ban, k="0" * 16, nonce="KT638" + frappe.generate_hash(length=24),
				mon=json.dumps([{"ma": ma, "sl": 1}]))
			r1 = g.goi(diem=quay["ma"], ban=ban, k=k, nonce="KT638" + frappe.generate_hash(length=24),
				mon=json.dumps([{"ma": ma, "sl": 2, "gia": 1}]), ten="Khách 638", ghi_chu="ít ngọt")
		finally:
			frappe.set_user(truoc)
		la("link sai không ghi", sai.get("ok"), 0)
		la("khách gọi được (câu máy chủ nếu không: %s)" % (r1 or {}).get("cau"), (r1 or {}).get("ok"), 1)
		if not (r1 or {}).get("ok"):
			return
		_DA_TAO.append((g.DT, r1["ma"]))
		b = frappe.db.get_value(g.DT, r1["ma"], ["trang_thai", "tam_tinh", "diem", "ban"], as_dict=True)
		# v647: ô bàn đổi Int sang Data (tên bàn theo khu, như A1); số 87 lưu thành chữ "87".
		la("bản ghi chờ, tạm tính theo giá máy chủ", (b.trang_thai, flt(b.tam_tinh), b.diem, b.ban), (g.TT_CHO, float(2 * gia), quay["ma"], str(ban)))
		kq = khong_nem("thu ngân nhận đơn", lambda: g.nhan(r1["ma"]))
		if not kq:
			return
		_DA_TAO.append(("Sales Invoice", kq["hoa_don"]))
		si = frappe.get_doc("Sales Invoice", kq["hoa_don"])
		la("phiếu tạm tính nháp của đúng bàn", (si.docstatus, si.vgb_tam_tinh, si.vgb_quay, si.vgb_so_ban, si.custom_nguon),
			(0, 1, quay["quay"], str(ban), g.NGUON_QR))
		la("đủ món đúng giá", [(x.item_code, flt(x.qty), flt(x.rate)) for x in si.items], [(ma, 2.0, float(gia))])
		# get_value nhiều ô trả tuple; ép list để so (bench PR #541 vòng 2 đỏ vì tuple khác list).
		la("bản ghi đã nhận, trỏ phiếu", list(frappe.db.get_value(g.DT, r1["ma"], ["trang_thai", "hoa_don"]) or []), [g.TT_NHAN, si.name])

		try:
			frappe.set_user("Guest")
			r2 = g.goi(diem=quay["ma"], ban=ban, k=k, nonce="KT638" + frappe.generate_hash(length=24),
				mon=json.dumps([{"ma": ma, "sl": 1}]))
		finally:
			frappe.set_user(truoc)
		la("gọi thêm được", (r2 or {}).get("ok"), 1)
		if not (r2 or {}).get("ok"):
			return
		_DA_TAO.append((g.DT, r2["ma"]))
		kq2 = khong_nem("nhận đơn gọi thêm", lambda: g.nhan(r2["ma"]))
		if not kq2:
			return
		la("gọi thêm vào CÙNG phiếu tạm tính", (kq2["hoa_don"], kq2["them_vao"]), (si.name, 1))
		si.reload()
		la("phiếu có hai dòng", [(x.item_code, flt(x.qty)) for x in si.items], [(ma, 2.0), (ma, 1.0)])
		la("tổng phiếu", flt(si.total), float(3 * gia))
		truoc_tt = g.trang_thai(r2["ma"], r2["token"])
		la("khách thấy đã nhận", truoc_tt.get("trang_thai"), g.TT_NHAN)
