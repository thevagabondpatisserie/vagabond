"""v619: nhịp đồng bộ Pancake dựng lại bảng món mà lịch sử không chụp lại cả bảng.

Đo trên site 28/10/2026: mỗi nhịp 30 phút dựng lại bảng món của hoá đơn nháp
bằng dòng mang tên mới, nên lịch sử sửa của ERPNext ghi "xoá hết dòng cũ, thêm
dòng mới" và chụp lại cả hai bên dù món y hệt. Ca này chạy ĐÚNG hàm đồng bộ
trên một hoá đơn nháp thật, chỉ thay phần đọc đơn Pancake, rồi đọc lịch sử
ERPNext thật ghi ra. Không gọi thêm hàm nào ngoài chuỗi của nhịp đồng bộ.
"""

import json
from contextlib import ExitStack
from unittest.mock import patch

import frappe
from vagabond import ban_hang
from vagabond.khung.kiem_that.nen import ca, dung, la
from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don


def _dong_bo(hd, dong):
	# Nhịp đồng bộ thật bật cờ vgb_dong_bo quanh mỗi lượt (ban_hang._dong_bo_doanh_so),
	# để hàng rào lưu của quầy không chặn tờ Pancake chưa có phương thức.
	with ExitStack() as st:
		st.enter_context(patch.object(frappe.local, "vgb_dong_bo", True, create=True))
		st.enter_context(patch.object(ban_hang, "_dong_hang", return_value=(dong, [])))
		st.enter_context(patch.object(ban_hang, "_lech_pancake", return_value=0))
		st.enter_context(patch.object(ban_hang, "_doan_thanh_toan", return_value=("", "")))
		st.enter_context(patch.object(ban_hang, "dong_thanh_toan_pancake", return_value=[]))
		return ban_hang._upsert_hoa_don({"id": hd.custom_pancake_id, "display_id": "THU619"},
			hd.posting_date, hd.company, hd.customer)


def _lich_su(hd, bo_qua):
	ds = frappe.get_all("Version", filters={"ref_doctype": "Sales Invoice", "docname": hd.name},
		fields=["name", "data"], order_by="creation asc")
	return [(v.name, json.loads(v.data or "{}")) for v in ds if v.name not in bo_qua]


def _bang(d, khoa):
	return sorted({x[0] for x in (d.get(khoa) or [])})


@ca("v619 site: đồng bộ Pancake dựng lại bảng món giữ tên dòng, lịch sử không chụp lại cả bảng món")
def _():
	hd = _hoa_don(False)
	hd.custom_pancake_id = "THU619-" + frappe.generate_hash(length=10)
	hd.custom_pancake_display_id = "THU619"
	# Tờ của nhịp đồng bộ luôn mang nguồn Pancake (hàm đồng bộ tự đặt); hàng rào
	# lưu chặn tờ thiếu nguồn, nên fixture đặt như tờ thật trước lần lưu đầu.
	hd.custom_nguon = "Pancake"
	with patch.object(frappe.local, "vgb_dong_bo", True, create=True):
		hd.save(ignore_permissions=True)
	hd.reload()
	mon, kho = hd.items[0].item_code, hd.items[0].warehouse
	ten_dau = hd.items[0].name
	dong = [dict(item_code=mon, qty=1, rate=1900000, warehouse=kho), dict(item_code=mon, qty=2, rate=1900000, warehouse=kho)]
	la("lượt 1 cập nhật đúng tờ", _dong_bo(hd, dong), ("cap_nhat", hd.name))
	hd.reload()
	la("dòng đầu giữ tên cũ", hd.items[0].name, ten_dau)
	ten = [d.name for d in hd.items]
	la("hai dòng", len(ten), 2)
	da_co = {n for n, _ in _lich_su(hd, set())}

	_dong_bo(hd, [dict(r) for r in dong])
	hd.reload()
	la("lượt 2 món y hệt: tên dòng không đổi", [d.name for d in hd.items], ten)
	moi = _lich_su(hd, da_co)
	for n, d in moi:
		dung("lượt 2 không chụp bảng món (thêm)", "items" not in _bang(d, "added"))
		dung("lượt 2 không chụp bảng món (bớt)", "items" not in _bang(d, "removed"))
	da_co |= {n for n, _ in moi}

	doi = [dict(dong[0]), dict(dong[1], qty=3)]
	_dong_bo(hd, doi)
	hd.reload()
	la("lượt 3 đổi số lượng: tên dòng không đổi", [d.name for d in hd.items], ten)
	la("số lượng mới đã ghi", [d.qty for d in hd.items], [1, 3])
	la("thành tiền tính lại theo số lượng mới", [d.amount for d in hd.items], [d.rate * d.qty for d in hd.items])
	moi = _lich_su(hd, da_co)
	dung("lượt 3 có lịch sử", bool(moi))
	for n, d in moi:
		dung("lượt 3 không chụp bảng món", "items" not in _bang(d, "added") + _bang(d, "removed"))
	doi_mon = [x for _, d in moi for x in (d.get("row_changed") or []) if x[0] == "items"]
	dung("lượt 3 ghi đúng dòng món đổi số lượng", any(x[2] == ten[1] and any(c[0] == "qty" for c in x[3]) for x in doi_mon))

	_dong_bo(hd, [dict(dong[0])])
	hd.reload()
	la("lượt 4 bớt món: còn đúng dòng đầu, giữ tên", [d.name for d in hd.items], ten[:1])
	la("dòng bớt đã xoá khỏi cơ sở dữ liệu", frappe.db.exists("Sales Invoice Item", ten[1]), None)
