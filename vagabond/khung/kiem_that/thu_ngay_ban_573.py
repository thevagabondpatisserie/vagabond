# -*- coding: utf-8 -*-
"""v573 chạy THẬT: đơn hàng tặng duyệt hôm sau không bị trừ số bán hai lần.

Ca thật Dễ báo 04/10/2026: out bill 1 Croissant bằng Hàng tặng, bảng Kiểm kho
ngày đó trừ 1. Hôm sau anh Việt duyệt, máy đổi ngày bill sang hôm duyệt, bảng
Kiểm kho hôm duyệt trừ thêm 1.

Ca dựng đúng chuỗi: hoá đơn tặng nháp mang ngày hôm qua, ghi quyết định duyệt,
rồi gọi đúng hàm đổi ngày mà nút duyệt gọi (`ban_hang._doi_ngay_ban_nhap`).
Không gọi hàm đếm hay hàm ghi ngày gốc nào khác ngoài chuỗi đó. Quầy dùng mã
riêng KT573 để không lẫn bill thật.
"""

import frappe
from frappe.utils import add_days, today

from vagabond import ban_hang, kiem_kho
from vagabond.khung.kiem_that.nen import ca, la
from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don

QUAY = "KT573"


@ca("v573 thật: đơn tặng nháp hôm qua, duyệt hôm nay đổi ngày ghi sổ, Kiểm kho chỉ trừ hôm qua")
def _duyet_hom_sau():
	hom_qua = add_days(today(), -1)
	hd = _hoa_don()
	hd.db_set({"vgb_quay": QUAY, "posting_date": hom_qua, "set_posting_time": 1, "due_date": hom_qua})
	hd.reload()
	ma = hd.items[0].item_code
	la("trước duyệt: hôm qua trừ 1", kiem_kho.da_ban(QUAY, hom_qua).get(ma, 0), 1)
	la("trước duyệt: hôm nay 0", kiem_kho.da_ban(QUAY, today()).get(ma, 0), 0)
	ban_hang._doi_ngay_ban_nhap(hd, today(), "Ca kiểm v573", "Giám đốc duyệt hàng tặng")
	hd.reload()
	la("ngày ghi sổ đã sang hôm nay", str(hd.posting_date), today())
	la("giữ ngày bán gốc", str(hd.get("vgb_ngay_ban")), hom_qua)
	la("sau duyệt: hôm qua vẫn 1", kiem_kho.da_ban(QUAY, hom_qua).get(ma, 0), 1)
	la("sau duyệt: hôm nay không trừ lại", kiem_kho.da_ban(QUAY, today()).get(ma, 0), 0)
