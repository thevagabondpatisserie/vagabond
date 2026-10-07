"""v583 #450: mot phep tim cho moi o tim, chay that tren MariaDB cua site.

Tang khung gia lap collation va chay cau SQL tren bang gia. No khong chung
minh duoc: cau `sql_ung_vien` (replace long nhau, tham so co ten) chay dung
tren MariaDB that, collation that bo dau nhung giu d khac đ, va dieu kien moi
tu nam truoc `limit` (Codex #450 vong 2 phan o tim). Ca duoi tao Item that
trong diem luu cua nen.py roi goi dung ten_khop va cua `tim`.
"""

import frappe

from vagabond import tim_kiem as tk
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO


def _mon(ten):
	d = frappe.get_doc(dict(doctype="Item", item_code="KT583-" + frappe.generate_hash(length=10), item_name=ten,
		item_group=frappe.db.get_value("Item Group", {"is_group": 0}, "name"),
		stock_uom=frappe.db.get_value("UOM", {}, "name"), is_stock_item=0, is_sales_item=1))
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


@ca("v583 site: o tim may chu ra dung mon voi go co dau, khong dau, dinh lien, dao thu tu, d/đ")
def _():
	dau = "Kt" + frappe.generate_hash(length=6)
	mini = _mon("Bánh %s Chocolatine, Mini size" % dau)
	full = _mon("Bánh %s Chocolatine, Full size" % dau)
	den = _mon("Bông lan %s Chuối Đường đen" % dau)
	cot = ["name", "item_name"]
	for q, mong in (("%s chocolatine mini" % dau, [mini]), ("%s mini, chocolatine" % dau, [mini]),
			("%s chocolatinemini" % dau, [mini]), ("%s CHOCOLATINE" % dau, sorted([mini, full])),
			("%s duong den" % dau, [den]), ("%s duongden" % dau, [den]), ("%s bánh" % dau, sorted([mini, full]))):
		la(q, sorted(tk.ten_khop("Item", q, cot) or []), mong)


@ca("v583 site: tu dau pho bien khong lam mat dong chi co o tu sau (dieu kien du ca cum truoc limit)")
def _():
	dau = "Kt" + frappe.generate_hash(length=6)
	for i in range(4):
		_mon("Bánh %s Chocolatine loại %d" % (dau, i))
	mini = _mon("Bánh %s Chocolatine, Mini size" % dau)
	cau, tham = tk.sql_ung_vien("Item", ["name", "item_name"], ["name", "item_name"], "%s chocolatine mini" % dau, gioi_han=3)
	ra = [r["name"] for r in frappe.db.sql(cau, tham, as_dict=True)]
	la("tran 3 dong nhung dieu kien du ca cum: chi con mon mini", ra, [mini])


@ca("v583 site: cua tim giu quyen doc, dau phay trong o go khong lot SQL")
def _():
	dau = "Kt" + frappe.generate_hash(length=6)
	mini = _mon("Bánh %s Chocolatine, Mini size" % dau)
	ra = tk.tim("Item", "%s chocolatine mini" % dau, cot='["name", "item_name"]', fields='["name"]')
	la("cua tim ra mon", [r["name"] for r in ra], [mini])
	ra = tk.tim("Item", "%s' or 1=1 -- " % dau, cot='["name", "item_name"]')
	la("go co dau nhay khong lot SQL", ra, [])
	dung("cot la dang SQL bi loai", tk.cot_hop_le(["item_name", "name; drop"], {"item_name", "name"}) == ["item_name"])
