"""#351: mẫu BC08 đọc số core đã tính, không nhầm tiền dòng với thực thu.

Gọi hàm báo cáo thật, giả duy nhất cửa đọc dòng. Bench chứng từ thật và
quyền API còn là cổng của cùng PR; các ca này không thay thế bench.
"""
from unittest.mock import patch

import frappe

from vagabond import bao_cao as bc
from vagabond.khung.kiem_thu.nen import ca, la, dung


def _hd(ten, **kw):
	return dict(name=ten, docstatus=1, **kw)


def _dong(cha, **kw):
	return dict(parent=cha, item_code="BANH", item_name="Bánh",
		item_group="Bánh", stock_uom="Cái", stock_qty=2,
		base_net_amount=90, amount=120, **kw)


@ca("BC08 mới: dùng tiền lõi sau giảm giá, không trừ lại hay gọi đã thu")
def _tien_loi():
	d = _dong("HD1")
	with patch.object(bc.frappe, "get_all", return_value=[d]) as doc:
		kq = bc._bc_mon_thuan([_hd("HD1", outstanding_amount=100, discount_amount=10)])
	la("tiền core90, không120 hoặc80", kq["doanh_thu_thuan"], 90)
	dung("không đặt tên tiền đã thu", all("đã thu" not in c["nhan"].lower() for c in kq["cot"]))
	dung("xin trường tiền core", "base_net_amount" in doc.call_args.kwargs["fields"])


@ca("BC08 mới: trả khác kỳ theo tập đã lọc, giữ âm và tách số phiếu")
def _tra_khac_ky():
	d = _dong("TRA"); d.update(stock_qty=-1, base_net_amount=-45)
	with patch.object(bc.frappe, "get_all", return_value=[d]):
		kq = bc._bc_mon_thuan([_hd("TRA", is_return=1, return_against="HD_KY_TRUOC")])
	la("không cần kéo doanh thu hóa đơn kỳ trước", kq["doanh_thu_thuan"], -45)
	la("không đếm phiếu trả như hóa đơn bán", kq["so_hoa_don_ban"], 0)
	la("phiếu trả riêng", kq["so_phieu_tra"], 1)
	la("số lượng trả âm", kq["dong"][0]["sl_tra"], -1)


@ca("BC08 mới: Nháp, hủy và tạm tính không lọt số chính")
def _tach_nhap():
	n = _hd("NHAP", base_grand_total=110); n["docstatus"] = 0
	h = _hd("HUY"); h["docstatus"] = 2
	with patch.object(bc.frappe, "get_all", return_value=[_dong("HD")]) as doc:
		kq = bc._bc_mon_thuan([_hd("HD"), n, h, _hd("TAM", vgb_tam_tinh=1), _hd("HUY_MEM", vgb_huy=1)])
	la("chỉ đọc dòng của tập đã ghi sổ hợp lệ", doc.call_args.kwargs["filters"]["parent"][1], ["HD"])
	la("doanh thu chính", kq["doanh_thu_thuan"], 90)
	la("đếm Nháp riêng", kq["so_nhap"], 1)
	la("giá trị Nháp riêng", kq["gia_tri_hoa_don_nhap"], 110)


@ca("BC08 mới: rỗng không quét dòng toàn site")
def _rong():
	with patch.object(bc.frappe, "get_all") as doc:
		kq = bc._bc_mon_thuan([])
	la("không gọi dữ liệu", doc.call_count, 0)
	la("không có dòng", kq["dong"], [])


@ca("BC08 mới: quy về đơn vị tồn và không cộng lượng khác đơn vị")
def _don_vi():
	a = _dong("HD"); a.update(qty=1, uom="Hộp", stock_qty=6)
	b = _dong("HD"); b.update(stock_uom="Gram", stock_qty=500, base_net_amount=30)
	with patch.object(bc.frappe, "get_all", return_value=[a, b]):
		kq = bc._bc_mon_thuan([_hd("HD")])
	la("không gộp đơn vị", len(kq["dong"]), 2)
	la("đọc lượng đã quy đổi core", kq["dong"][0]["sl"], 6)
	dung("không cộng tổng lượng khác đơn vị", all(c.get("kc") for c in kq["cot"] if c["kieu"] == "so"))


@ca("BC08 mới: chia lô đầy đủ quá400 hóa đơn, không cắt tổng")
def _phan_lo():
	hd = [_hd("HD%s" % i) for i in range(401)]
	def doc(doctype, filters, **kw):
		return [_dong(ten) for ten in filters["parent"][1]]
	with patch.object(bc.frappe, "get_all", side_effect=doc) as goi:
		kq = bc._bc_mon_thuan(hd)
	la("hai lô", goi.call_count, 2)
	la("đủ401", kq["doanh_thu_thuan"], 401*90)


@ca("BC08 mới: cửa đọc xin đủ trường, lọc công ty và gọi đúng chữ ký báo cáo")
def _qua_cua_doc():
	du_lieu = {
		"Sales Invoice": [
			dict(name="HD1", company="Vagabond", docstatus=1,
				posting_date="2026-10-05", is_return=0, base_grand_total=108,
				vgb_tam_tinh=0, vgb_huy=0),
			dict(name="TRA1", company="Vagabond", docstatus=1,
				posting_date="2026-10-06", is_return=1, return_against="HD0",
				base_grand_total=-54, vgb_tam_tinh=0, vgb_huy=0),
			dict(name="NHAP", company="Vagabond", docstatus=0,
				posting_date="2026-10-07", is_return=0, base_grand_total=110,
				vgb_tam_tinh=0, vgb_huy=0),
			dict(name="DEMO", company="Demo", docstatus=1,
				posting_date="2026-10-08", is_return=0, base_grand_total=999,
				vgb_tam_tinh=0, vgb_huy=0),
		],
		"Sales Invoice Item": [],
	}
	tra = _dong("TRA1"); tra.update(stock_qty=-1, base_net_amount=-45)
	demo = _dong("DEMO"); demo.update(base_net_amount=999)
	du_lieu["Sales Invoice Item"] = [_dong("HD1"), tra, demo]

	def doc(doctype, filters=None, fields=None, **kw):
		dong = du_lieu[doctype]
		if doctype == "Sales Invoice":
			dong = [r for r in dong if not filters.get("company")
				or r.get("company") == filters["company"]]
		else:
			dong = [r for r in dong if r["parent"] in filters["parent"][1]]
		# Frappe chỉ trả những trường caller đã xin. Ca này vì thế sẽ đỏ nếu
		# hợp đồng của _hoa_don và _bc_mon_thuan lại lệch nhau.
		return [frappe._dict({f: r.get(f) for f in fields}) for r in dong]

	with patch.object(bc.frappe, "get_all", side_effect=doc) as goi, \
			patch.object(bc.frappe.db, "get_value", return_value="Vagabond"):
		hd = bc._hoa_don("2026-10-01", "2026-10-31")
		kq = bc._bc_mon_thuan(hd, tu="2026-10-01", den="2026-10-31")
	la("lọc công ty ngay tại truy vấn", goi.call_args_list[0].kwargs["filters"]["company"], "Vagabond")
	la("chỉ đếm hóa đơn bán đúng công ty", kq["so_hoa_don_ban"], 1)
	la("đếm phiếu trả", kq["so_phieu_tra"], 1)
	la("giữ lượng trả âm", kq["dong"][0]["sl_tra"], -1)
	la("tách giá trị hóa đơn Nháp", kq["gia_tri_hoa_don_nhap"], 110)
	la("doanh thu thuần", kq["doanh_thu_thuan"], 45)
