"""v526: quyen Repost cho ke toan FIN (sua tai khoan tren hoa don mua da ghi
so). Doc vagabond/quyen_ap.py, muc CAP_THEM.

Them chi muc cho o hoa_don_bo_sung (Codex #368 finding 2): noi va ghi so doc
dau noi bang cau co khoa (for update). Khong co chi muc thi cau do quet va
khoa MOI dong ho so; co chi muc thi chi khoa dung dong dang noi to do.

Khong boc try (Codex #364 v2): loi phai lam hong migrate.
"""


def execute():
	import frappe
	from vagabond import quyen_ap

	frappe.db.add_index("Vagabond Ho So TT Dong", ["hoa_don_bo_sung"],
		index_name="vgb_hoa_don_bo_sung_526")
	return quyen_ap.cap_repost_v526()
