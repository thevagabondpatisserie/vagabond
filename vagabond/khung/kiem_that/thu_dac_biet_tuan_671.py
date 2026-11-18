"""v671 bench: món của đợt "Đặc biệt tuần này" lên trang khách theo ĐỢT, chạy trên ERPNext thật.

Tầng khung kiểm phép thuần và cửa tạo đơn với Frappe giả. Ở đây chứng minh trên
bảng thật: kiem_banh.co_the_ban_hom_nay trả món của đợt trong danh sách riêng
dù bánh không có trên tủ, không có Đủ decor (đúng ca Hũ Stollen 18/11/2026);
thẻ Bánh Chờ ảnh mà đợt có Ảnh đứng vẫn lên; mã chưa có giá không lên; món đó
không lọt sang danh sách Đặt bánh trước. Đọc thẻ Bánh, Item bằng đúng cột thật.
"""
from unittest.mock import patch

import frappe

from vagabond import banh_web as bw
from vagabond import dac_biet_tuan as dbt
from vagabond import kiem_banh as kb
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, la


def _mon(duoi, gia):
	from vagabond.khung.kiem_that import nen

	d = frappe.get_doc({"doctype": "Item", "item_code": "BACF-KIEM-671-%s" % duoi,
		"item_name": "Hũ Thử Đợt 671 %s" % duoi, "item_group": nen._mot("Item Group", {"is_group": 0}),
		"stock_uom": nen._mot("UOM", {}), "is_stock_item": 0, "is_sales_item": 1, "standard_rate": gia})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


@ca("v671 bench: Hũ chỉ làm cho đợt (không tủ, không Đủ decor) lên danh sách đợt của trang khách, mã chưa giá không lên, không lọt sang Đặt bánh trước")
def _():
	co_gia, chua_gia = _mon("A", 180000), _mon("B", 0)
	r = bw.dua_len_web(co_gia)
	khoa = r["khoa"]
	ten_the = frappe.db.get_value(bw.DT, {"khoa": khoa}, "name")
	if r.get("moi"):
		_DA_TAO.append((bw.DT, ten_the))
	frappe.db.set_value(bw.DT, ten_the, "ma_hang", co_gia + "\n" + chua_gia)
	la("thẻ mới ở Chờ ảnh", frappe.db.get_value(bw.DT, {"khoa": khoa}, "trang_thai"), bw.CHO_ANH)
	dot = {"id": "dbt-671", "mon_dt": [{"khoa": khoa, "mo_ta": "", "anh": "/files/dung-671.jpg", "nhan_goc": "", "toi_da": "30"}]}
	with patch.object(dbt, "dot_cong_khai", lambda: dot):
		ra = kb.co_the_ban_hom_nay()
	la("món của đợt, chỉ mã có giá, ảnh đứng của đợt", [(g["ten"], [z["ma"] for z in g["sizes"]], g["anh"]) for g in ra.get("dac_biet") or []],
		[(frappe.db.get_value(bw.DT, {"khoa": khoa}, "ten"), [co_gia], "/files/dung-671.jpg")])
	ds_truoc = [z["ma"] for g in (ra.get("dat_truoc") or {}).get("nhom") or [] for z in g["sizes"]]
	la("không lọt sang Đặt bánh trước", [m for m in ds_truoc if m in (co_gia, chua_gia)], [])
	with patch.object(dbt, "dot_cong_khai", lambda: dict(dot, mon_dt=[dict(dot["mon_dt"][0], anh="")])):
		la("không ảnh nào: chưa lên", kb.co_the_ban_hom_nay().get("dac_biet"), [])
	with patch.object(dbt, "dot_cong_khai", lambda: None):
		la("không có đợt: rỗng", kb.co_the_ban_hom_nay().get("dac_biet"), [])
