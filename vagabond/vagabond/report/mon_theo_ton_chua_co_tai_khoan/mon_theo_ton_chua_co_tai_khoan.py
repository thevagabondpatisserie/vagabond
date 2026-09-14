"""Báo cáo "Món theo tồn chưa có tài khoản": cổng bật cờ tài khoản theo món (#307).

VÌ SAO
--------------------------------------------------------------------
Lõi ERPNext de591661 (stock_controller.py:258-270, anh Việt đối chiếu
14/09/2026) khi Company bật `enable_item_wise_inventory_account` mà món
không có tài khoản ở cả ba nấc món, nhóm món, nhãn hiệu thì CHẶN chứng từ,
không quay về tài khoản kho. Kế toán chỉ bật cờ khi báo cáo này RỖNG. Đây
là bước tay bắt buộc ngày cắt, ghi trong docs/van-hanh-agent/cong-viec/issue-307.md.

Tên báo cáo để không dấu vì Frappe lấy tên làm tên thư mục mô đun Python;
nhãn cột và câu chữ vẫn tiếng Việt có dấu. Phần thuần nằm trên vạch
`import frappe` để ca kiểm tầng khung chạy được tay không.
"""

# phần thuần

COT = [
	{"fieldname": "item_code", "label": "Mã món", "fieldtype": "Link", "options": "Item", "width": 160},
	{"fieldname": "item_name", "label": "Tên món", "fieldtype": "Data", "width": 260},
	{"fieldname": "item_group", "label": "Nhóm món", "fieldtype": "Link", "options": "Item Group", "width": 200},
	{"fieldname": "brand", "label": "Nhãn hiệu", "fieldtype": "Link", "options": "Brand", "width": 120},
	{"fieldname": "ton", "label": "Tồn hiện tại", "fieldtype": "Float", "width": 120},
	{"fieldname": "stock_uom", "label": "Đơn vị", "fieldtype": "Data", "width": 80},
]


def loc_chua_co(cac_mon, co_mon, co_nhom, co_nhan, ton):
	"""Món theo tồn mà cả ba nấc đều trống. THUẦN.

	`cac_mon`: dict có name, item_name, item_group, brand, stock_uom.
	`co_mon`, `co_nhom`, `co_nhan`: tập tên Item, Item Group, Brand ĐÃ có
	tài khoản trên Item Default của công ty. Nhóm chỉ tính ĐÚNG nhóm ghi
	trên hồ sơ, không leo cha, đúng như get_item_group_defaults của lõi.
	`ton`: dict mã món -> tổng actual_qty.
	"""
	co_mon, co_nhom, co_nhan = set(co_mon or ()), set(co_nhom or ()), set(co_nhan or ())
	ra = []
	for m in cac_mon or []:
		ma = m.get("name") or m.get("item_code")
		if ma in co_mon:
			continue
		if m.get("item_group") and m["item_group"] in co_nhom:
			continue
		if m.get("brand") and m["brand"] in co_nhan:
			continue
		ra.append({
			"item_code": ma, "item_name": m.get("item_name"), "item_group": m.get("item_group"),
			"brand": m.get("brand"), "ton": float((ton or {}).get(ma) or 0), "stock_uom": m.get("stock_uom"),
		})
	ra.sort(key=lambda r: ((r["item_group"] or ""), r["item_code"] or ""))
	return ra


# phần chạm Frappe
import frappe

from vagabond.tai_khoan_btp import TRUONG_ITEM_DEFAULT, cong_ty_ap_dung, doc_cau_hinh


def execute(filters=None):
	filters = filters or {}
	cong_ty = filters.get("company") or cong_ty_ap_dung(doc_cau_hinh())
	cac_mon = frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0},
		fields=["name", "item_name", "item_group", "brand", "stock_uom"], limit_page_length=0)
	co = {"Item": set(), "Item Group": set(), "Brand": set()}
	for r in frappe.get_all("Item Default", filters={"company": cong_ty,
			"parenttype": ["in", list(co)], TRUONG_ITEM_DEFAULT: ["!=", ""]},
			fields=["parent", "parenttype"], limit_page_length=0):
		co.setdefault(r.parenttype, set()).add(r.parent)
	ton = {}
	for r in frappe.get_all("Bin", fields=["item_code", "sum(actual_qty) as ton"],
			group_by="item_code", limit_page_length=0):
		ton[r.item_code] = r.ton
	dong = loc_chua_co(cac_mon, co["Item"], co["Item Group"], co["Brand"], ton)
	if not dong:
		frappe.msgprint("Mọi món theo tồn đã có tài khoản ở ít nhất một nấc. Có thể bật "
			"tài khoản tồn kho theo món trên Company %s đúng ngày cắt." % cong_ty,
			indicator="green", alert=True)
	return COT, dong
