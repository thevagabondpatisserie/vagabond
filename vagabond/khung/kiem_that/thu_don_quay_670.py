"""v670 ca TÍCH HỢP: combo trong đơn giao của quầy (WEBORDER) qua phiếu tạm tính thật.

Tầng khung chốt luật nguồn và cờ kênh bằng bản giả. Tầng này hỏi điều bản giả không
trả lời: phiếu tạm tính quầy lập khi xác nhận đơn giao (ban_hang.tao_don_tay với
tam_tinh=1 và cờ giữ giá dòng vgb_gia_chot, đúng đường don_quay._xac_nhan_trong_khoa)
có rã dòng combo KMCB thành món thật mà GIỮ ĐÚNG tổng khách đã trả không. Lệch tổng
thì quầy không xác nhận được đơn (don_quay chặn), nên ca này chốt tổng.
Mọi thứ lùi về điểm lưu, xem nen.py.
"""

from unittest.mock import patch

import frappe

from vagabond import ban_hang, diem_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _mon, _nen


@ca("v670 thật: phiếu tạm tính đơn giao có combo (giữ giá dòng) rã thành món, tổng đúng giá combo khách đã trả")
def _combo_giao():
	ct, tk, _ = _nen()
	mon = _mon(tk)
	cha = frappe.copy_doc(frappe.get_doc("Item", mon))
	cha.item_code = "KMCB-KIEM670-" + frappe.generate_hash(length=8)
	cha.item_name = "Combo kiểm đơn giao"
	cha.insert(ignore_permissions=True)
	nen._DA_TAO.append((cha.doctype, cha.name))
	cb = frappe.get_doc(dict(doctype="Vagabond Combo", ten="Combo kiểm đơn giao", ma_hang=cha.name, bat=1,
		kieu="Gia tron goi", gia_combo=89000, dong=[dict(item_code=mon, so_luong=2, gia_goc=50000)]))
	cb.insert(ignore_permissions=True)
	nen._DA_TAO.append((cb.doctype, cb.name))
	kh = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name")
	cac_diem = diem_ban.diem_cua_nguon("GrabFood")
	quay = cac_diem[0] if cac_diem else ""

	def lap():
		frappe.flags.vgb_gia_chot = True
		try:
			with patch.object(ban_hang, "_cong_ty", return_value=ct), patch.object(ban_hang, "_khach_le", return_value=kh):
				return ban_hang.tao_don_tay(nguon="GrabFood", quay=quay, ma_don="KT670-" + frappe.generate_hash(length=8),
					items=[dict(item_code=cha.name, qty=1, rate=89000)], tam_tinh=1)
		finally:
			frappe.flags.vgb_gia_chot = False
	ra = khong_nem("lập phiếu tạm tính", lap) or {}
	if not ra.get("name"):
		return
	nen._DA_TAO.append(("Sales Invoice", ra["name"]))
	hd = frappe.get_doc("Sales Invoice", ra["name"])
	la("rã thành món thật", [(d.item_code, d.qty) for d in hd.items if d.item_code == mon], [(mon, 2)])
	la("không còn dòng mã combo", [d.item_code for d in hd.items if d.item_code == cha.name], [])
	la("tổng đúng giá combo khách đã trả", int(round(hd.grand_total)), 89000)
