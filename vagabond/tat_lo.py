# -*- coding: utf-8 -*-
"""v545: tắt quản lý theo lô cho mọi mã hàng.

Anh Việt chốt 30/09/2026 sau lần thứ ba lô chặn người dùng (PSX-2026-00116
ở v540, rồi màn Ghi sổ kiểm kê của Khải báo "Vui lòng thêm Gói Số seri và
Lô" cho Bánh Chocolatine Mini đếm ra 0): tắt lô cho cả 770 mã, gồm bánh,
bán thành phẩm, nhân và nguyên liệu thô.

ERPNext không cho bỏ tick "Quản lý theo mẻ" trên form Item khi mã đã có phát
sinh kho, nên phải ghi thẳng ba cờ bằng db.set_value. Hệ quả đã nói với anh:
- Chứng từ cũ giữ nguyên, lô và gói lô cũ vẫn nằm đó, không xoá gì.
- Từ nay nhập, xuất, sản xuất, kiểm kê không cần lô. Tồn cũ ở các lô được
  coi là tồn chung của mã, giá tính theo bình quân như mã thường.
- Huỷ một chứng từ CŨ có lô về sau có thể bị ERPNext báo lỗi, khi đó xử lý
  từng tờ.

Danh sách mã đã tắt được ghi vào một Note để bật lại được nếu cần.
"""

TRUONG_LO = ("has_batch_no", "has_expiry_date", "create_new_batch")
TIEU_DE_NOTE = "Mã hàng đã tắt quản lý theo lô (v545)"


def can_tat(dong):
	"""THUẦN: mã còn bật một trong ba cờ lô thì phải tắt."""
	for t in TRUONG_LO:
		try:
			if int(dong.get(t) or 0):
				return True
		except (TypeError, ValueError):
			return True
	return False


def chon_ma(ds):
	"""THUẦN: lọc các mã phải tắt, giữ thứ tự, bỏ trùng."""
	ra, da = [], set()
	for d in ds or []:
		ma = d.get("name")
		if ma and ma not in da and can_tat(d):
			da.add(ma)
			ra.append(ma)
	return ra


def dieu_kien_loc(ma=None):
	"""THUẦN: điều kiện tìm mã phải tắt. Mã còn bật BẤT KỲ cờ nào trong ba cờ.

	Codex #399: bản đầu chỉ lọc has_batch_no = 1, nên mã đã bỏ tick lô mà còn
	cờ hạn dùng hay cờ tự sinh lô không bao giờ tới được can_tat(). Site thật
	30/09/2026 có 1 mã còn cờ hạn dùng và 1 mã còn cờ tự sinh lô như vậy."""
	loc = [["name", "in", list(ma)]] if ma else []
	hoac = [[t, "=", 1] for t in TRUONG_LO]
	return loc, hoac


def tat_lo(ma=None):
	"""Tắt ba cờ lô. `ma` là danh sách mã; để trống là mọi mã đang bật lô.

	Chỉ ghi Item, không đụng chứng từ, Batch hay gói lô. Trả về danh sách mã
	đã tắt."""
	import frappe

	loc, hoac = dieu_kien_loc(ma)
	ds = frappe.get_all("Item", filters=loc, or_filters=hoac, fields=["name"] + list(TRUONG_LO),
		limit_page_length=0)
	cac_ma = chon_ma(ds)
	for m in cac_ma:
		frappe.db.set_value("Item", m, {t: 0 for t in TRUONG_LO}, update_modified=False)
		frappe.clear_document_cache("Item", m)
	return cac_ma


def ghi_note(cac_ma):
	"""Ghi danh sách mã đã tắt vào Note, để bật lại được nếu cần."""
	import frappe

	if not cac_ma:
		return None
	noi = "<p>Tắt ngày %s, %s mã. Bật lại: tick Quản lý theo mẻ trên từng mã.</p><p>%s</p>" % (
		frappe.utils.nowdate(), len(cac_ma), ", ".join(cac_ma))
	n = frappe.new_doc("Note")
	n.title = TIEU_DE_NOTE
	n.public = 1
	n.content = noi
	n.flags.ignore_permissions = True
	n.insert(ignore_permissions=True)
	return n.name
