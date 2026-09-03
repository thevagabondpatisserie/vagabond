# -*- coding: utf-8 -*-
"""Ô NGƯỜI BÁN trên hoá đơn: ai thật sự bán tờ hàng này.

Anh Việt hỏi ngày 02/09/2026: *"theo anh hiểu thì nó sẽ tự map theo tên
đăng nhập của người đang thao tác?"*

Đúng MỘT NỬA, và nửa còn lại chính là chỗ sinh ra rổ 1.071 hoá đơn chưa
gán người bán của tháng 8.

  - Đơn do NGƯỜI lên trong app: đúng, máy lấy ngay tài khoản đang đăng
    nhập. Không phải gõ gì thêm.
  - Đơn do MÁY dựng (nhịp đồng bộ Pancake, GrabFood, ShopeeFood, các
    đường webhook): lúc đó KHÔNG có ai đang đăng nhập cả. Người chạy là
    tài khoản máy. Lấy tài khoản đó làm người bán thì cả nghìn tờ hoá đơn
    mang tên "Hệ thống", mà đó chính là con số 1.071 anh đang thấy.

Nên hàm này CỐ Ý để trống khi người tạo là tài khoản máy, thay vì điền
bừa. Để trống thì tờ đó rơi vào rổ "chưa gán người bán" ở màn KPI, quản lý
gán tay từng đơn. Điền bừa thì nó biến mất khỏi rổ và không ai còn biết là
chưa gán.

KHÔNG ĐỤNG VÀO ĐƠN CŨ

Ô này chỉ điền cho đơn lập TỪ ĐÂY VỀ SAU. Hơn hai mươi nghìn tờ hoá đơn cũ
giữ nguyên, đúng điều anh Việt chốt ngày 13/08/2026: không tự sửa dữ liệu
quá khứ. Muốn gán người bán cho đơn cũ thì gán tay trên màn KPI, mỗi lần
gán là một quyết định của người thật.
"""

import frappe

DT = "Sales Invoice"
O = "vgb_nguoi_ban"

# Tài khoản máy, không phải người bán. `Administrator` chạy mọi nhịp nền;
# `Guest` là khách chưa đăng nhập trên web đặt bánh.
MAY = {"Administrator", "Guest", ""}

TRUONG_MOI = {
	DT: [
		{
			"fieldname": O,
			"label": "Người bán",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "vgb_quay",
			"in_standard_filter": 1,
			"description": (
				"Người thật sự bán tờ hàng này. Máy tự điền khi có người "
				"lên đơn trong app. Đơn do máy đồng bộ về thì để trống, "
				"quản lý gán tay ở màn KPI."
			),
		},
	],
}


def ai_ban(nguoi_dang_lam, dang_chay_nen=False):
	"""Phép THUẦN: tài khoản này có được ghi làm người bán không.

	Trả về mã tài khoản, hoặc chuỗi rỗng nếu không xác định được người.
	Tách riêng khỏi Frappe để kiểm thử được mà không cần site.
	"""
	if dang_chay_nen:
		return ""
	ma = str(nguoi_dang_lam or "").strip()
	if ma in MAY:
		return ""
	return ma


# Ai duoc gan tay nguoi ban. KHONG mo cho thu ngan: o nay quyet dinh doanh
# so va hoa hong roi vao tay ai, nen phai la nguoi co trach nhiem ky. Danh
# sach nay trung voi bo vai xem duoc phan he KPI, vi chinh ho la nguoi phai
# don ro "chua gan nguoi ban" o do.
VAI_GAN = {
	"System Manager", "Giám đốc", "AP Giám đốc",
	"Accounts Manager", "Accounts User", "Kế toán",
	"Sales Manager", "Quản lý cửa hàng", "Bếp trưởng",
}


def duoc_gan(cac_vai):
	"""Phép THUẦN: bộ vai này có được gán tay người bán không."""
	return bool(VAI_GAN & set(cac_vai or ()))


def chua_gan(o_nguoi_ban, nguoi_lap):
	"""Phép THUẦN: tờ hoá đơn này có đang nằm trong rổ chưa gán không.

	Chưa gán nghĩa là ô người bán còn TRỐNG và người lập là tài khoản máy.
	Ô trống mà người lập là người thật thì đó là tờ cũ lập trước khi có ô
	này, màn hình vẫn lấy người lập ra hiển thị nên không coi là thiếu.
	"""
	if str(o_nguoi_ban or "").strip():
		return False
	return str(nguoi_lap or "").strip() in MAY


def _dang_chay_nen():
	"""Đang chạy trong nhịp nền hay trong một lượt bấm của người thật.

	Nhịp nền của Frappe chạy dưới tài khoản Administrator, nhưng có lúc nó
	chạy dưới tài khoản người khác (ví dụ một việc do người bấm rồi đẩy ra
	hàng đợi). Đọc cờ của Frappe chứ không đoán theo tên tài khoản.
	"""
	try:
		if getattr(frappe.flags, "in_migrate", False):
			return True
		if getattr(frappe.flags, "in_install", False):
			return True
		if getattr(frappe.flags, "in_patch", False):
			return True
		# Nhip nen va webhook deu khong co request cua nguoi.
		if getattr(frappe.local, "request", None) is None:
			return True
	except Exception:
		return True
	return False


def truoc_khi_luu(doc, method=None):
	"""Điền người bán lúc tạo tờ hoá đơn. Chỉ điền khi ô còn trống.

	Ô đã có người thì KHÔNG đè: quản lý gán tay xong mà máy đè lại là công
	gán tay đổ sông. Và chỉ chạy lúc TẠO, không chạy mỗi lần lưu: sửa một
	tờ hoá đơn cũ không được biến người sửa thành người bán.
	"""
	try:
		if not doc.get("__islocal") and not doc.is_new():
			return
	except Exception:
		pass
	if doc.get(O):
		return
	ma = ai_ban(frappe.session.user, _dang_chay_nen())
	if ma:
		doc.set(O, ma)


@frappe.whitelist()
def gan(name=None, nguoi=None):
	"""Gán tay người bán cho một tờ hoá đơn. Có ghi vết.

	Dùng cho đơn máy đồng bộ về, và cho trường hợp gán nhầm. KHÔNG đụng
	tới một con số tiền nào, không đụng hoá đơn điện tử, nên gán lại lúc
	nào cũng an toàn.
	"""
	from vagabond.ban_hang import _kiem_quyen
	from vagabond import ten_nguoi

	_kiem_quyen()
	name = (name or "").strip()
	nguoi = (nguoi or "").strip()
	if not name or not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy hoá đơn %s." % name)
	if nguoi and not frappe.db.exists("User", nguoi):
		frappe.throw("Không có tài khoản %s." % nguoi)
	# Chuỗi rỗng nghĩa là GỠ người bán ra, đó là một thao tác hợp lệ khi gán
	# nhầm. Chỉ chặn tài khoản máy.
	if nguoi and nguoi in MAY:
		frappe.throw("Tài khoản máy không phải người bán.")

	cu = frappe.db.get_value(DT, name, O) or ""
	if cu == nguoi:
		return {"ma": name, "nguoi": nguoi, "ten": ten_nguoi.ten(nguoi)}
	frappe.db.set_value(DT, name, O, nguoi, update_modified=False)
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": DT, "reference_name": name,
			"content": "Người bán: %s%s." % (
				ten_nguoi.ten(nguoi) if nguoi else "gỡ bỏ",
				(" (trước đó %s)" % ten_nguoi.ten(cu)) if cu else "",
			),
		}).insert(ignore_permissions=True)
	except Exception:
		# Mat mot dong ghi vet KHONG duoc lam hong viec gan.
		pass
	frappe.db.commit()
	return {"ma": name, "nguoi": nguoi, "ten": ten_nguoi.ten(nguoi)}
