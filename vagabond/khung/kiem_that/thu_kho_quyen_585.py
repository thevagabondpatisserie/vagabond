"""v585: ô kho cấu hình không được ẩn món với người có quyền theo kho.

Ca thật 08/10/2026 (anh Việt): màn Chọn hàng hoá gõ "Chocolatine" ra 5 món
nhưng thiếu "Bánh Chocolatine, Mini size"; gõ đủ tên cũng không ra. Món có
thật, đang bật, cùng nhóm với bản Full size. Khác biệt duy nhất: Khải vừa
khai "Kho nguyên liệu mặc định khi sản xuất" = Baker - Nguyên liệu. Người
dùng có User Permission theo kho (12 tài khoản trên site) nên Frappe áp
quyền kho lên CẢ ô Link Warehouse của Item và ẩn món.

Ca v583 (thu_tim_kiem_583) chạy bằng Administrator nên không thấy lớp quyền
này. Ca dưới dựng ĐÚNG người bị chặn: tài khoản thường, User Permission một
kho, rồi gọi cửa `tim` và `get_list` như màn hình gọi.
"""

import frappe

from vagabond import tim_kiem as tk
from vagabond.khung.kiem_that.nen import ca, la, dung, cong_ty, _DA_TAO


def _ghi(doc):
	doc.insert(ignore_permissions=True)
	_DA_TAO.append((doc.doctype, doc.name))
	return doc


def _hai_kho():
	kho = frappe.get_all("Warehouse", filters={"company": cong_ty(), "is_group": 0, "disabled": 0},
		pluck="name", order_by="creation asc", limit=2)
	if len(kho) < 2:
		frappe.throw("Site thử cần ít nhất hai kho lá để dựng ca quyền theo kho.")
	return kho


@ca("v585 site: người có quyền theo kho vẫn tìm thấy món khai kho sản xuất ngoài quyền của mình")
def _():
	kho_cua_ho, kho_khac = _hai_kho()
	for dt, truong in (("Item", "custom_kho_nguyen_lieu_sx"), ("Warehouse", "custom_kho_nguon"),
			("Warehouse", "custom_kho_nguon_phu")):
		df = frappe.get_meta(dt).get_field(truong)
		dung("có ô %s.%s sau migrate" % (dt, truong), bool(df))
		la("%s.%s bỏ qua User Permission" % (dt, truong), int(df.ignore_user_permissions or 0) if df else None, 1)
	u = _ghi(frappe.get_doc({"doctype": "User", "email": "kt585-kho-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm quyền kho 585", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Stock User"}]}))
	_ghi(frappe.get_doc({"doctype": "User Permission", "user": u.name, "allow": "Warehouse",
		"for_value": kho_cua_ho, "apply_to_all_doctypes": 1}))
	dau = "Kt" + frappe.generate_hash(length=6)
	nhom = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	dvt = frappe.db.get_value("UOM", {}, "name")
	mon = {}
	for nhan, kho in (("khong_kho", None), ("kho_khac", kho_khac), ("kho_cua_ho", kho_cua_ho)):
		d = frappe.get_doc(dict(doctype="Item", item_code="KT585-" + frappe.generate_hash(length=10),
			item_name="Bánh %s Chocolatine %s" % (dau, nhan), item_group=nhom, stock_uom=dvt,
			is_stock_item=0, is_sales_item=1))
		d.set("custom_kho_nguyen_lieu_sx", kho)
		mon[nhan] = _ghi(d).name
	frappe.set_user(u.name)
	try:
		ra = tk.tim("Item", "%s chocolatine" % dau, cot='["name", "item_name"]', fields='["name"]', gioi_han=50)
		la("ô tìm ra đủ ba món, kể cả món khai kho ngoài quyền",
			sorted(r["name"] for r in ra), sorted(mon.values()))
		ds = frappe.get_list("Item", filters={"item_name": ["like", "%" + dau + "%"]}, pluck="name")
		la("danh sách món (get_list) cũng đủ ba", sorted(ds), sorted(mon.values()))
		# Quyền theo kho vẫn giữ nguyên ở chỗ nó cần: danh sách KHO.
		kho_thay = frappe.get_list("Warehouse", filters={"name": ["in", [kho_cua_ho, kho_khac]]}, pluck="name")
		la("danh sách kho vẫn chỉ ra kho của họ", kho_thay, [kho_cua_ho])
	finally:
		frappe.set_user("Administrator")
