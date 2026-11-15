"""v660: một bánh nhiều đợt refill. Chuyển đợt đang ghi ở ba ô cũ (so_refill,
refill_tu, refill_den) của bảng BTP thành đợt đầu trong ô refill_dot.

Chỉ nâng dòng còn số ở ba ô cũ và ô mới còn trống; chạy lại không đổi gì thêm.
Đây là số đang chạy của bếp, không phải chứng từ đã ghi sổ.
"""
import frappe


def execute():
	from vagabond import refill

	if not frappe.db.has_column("BTP Banh O Dong", "refill_dot"):
		return
	rows = frappe.db.sql("""select name, so_refill, refill_tu, refill_den, refill_dot from `tabBTP Banh O Dong`
		where ifnull(so_refill, 0) > 0 and ifnull(refill_dot, '') = ''""", as_dict=True)
	for r in rows:
		ds = [dict(x, id=frappe.generate_hash(length=8)) for x in refill.doc_dot(r)]
		if not ds:
			continue
		frappe.db.sql("""update `tabBTP Banh O Dong` set refill_dot = %s, so_refill = 0, refill_tu = null, refill_den = null
			where name = %s""", (refill.ghi_dot(ds), r.name))
