# -*- coding: utf-8 -*-
"""Công tắc tay: tạm ngừng bán một mã trên web đặt bánh.

Anh Việt 27/08/2026: *"mỗi bánh trong màn kiểm bánh (cả kiểm bánh hôm nay lẫn
màn kiểm mùa vụ) thì em cho thêm nút bật/tắt trên web bán hàng để có thể bật
tắt thủ công việc hiển thị bánh đó trên web order.thevagabondpatisserie.com
chứ không chỉ hiển thị auto theo số tồn vì có vài trường hợp bất khả kháng,
còn tồn nhưng phải tắt, không bán được hôm đó."*

VÌ SAO LƯU MỘT CÁI NGÀY CHỨ KHÔNG PHẢI MỘT Ô CÓ / KHÔNG
--------------------------------------------------------
Một ô có / không thì tắt xong nó tắt mãi. Ngày mai bếp làm được bánh đó, số
tồn lên, mà web vẫn không hiện - và không ai nhớ ra là hôm kia có người bấm
tắt. Bánh biến mất khỏi web hàng tuần liền mà không ai hay: hỏng nặng hơn
đúng cái mà nút này sinh ra để chữa.

Nên ô này lưu NGÀY TẮT ĐẾN HẾT. Bấm tắt hôm nay là tắt hết hôm nay, sáng mai
tự bán lại. Muốn tắt dài hơn thì bấm tắt lại, hoặc gõ ngày khác. Màn hình
luôn nói rõ mai có bán lại hay không, không bắt ai phải nhớ.

VÌ SAO ĐẶT TRÊN MẶT HÀNG CHỨ KHÔNG PHẢI TRÊN DÒNG CỦA BẢNG KIỂM BÁNH
--------------------------------------------------------------------
Hai màn hỏi cùng một câu: "hôm nay mã này có bán trên web không". Màn kiểm
bánh hằng ngày và màn kiểm mùa vụ lưu dòng ở hai chỗ khác nhau, nên nếu để ô
này trên từng dòng thì phải khai hai lần, sửa hai nơi, và hai nơi sẽ lệch
nhau vào một ngày nào đó. Đặt trên mặt hàng thì chỉ có một sự thật.
"""

import frappe
from frappe.utils import getdate, nowdate

TRUONG = "custom_tat_ban_web_den"

TRUONG_MOI = {
	"Item": [
		{
			"fieldname": TRUONG,
			"label": "Tạm ngừng bán trên web đến hết ngày",
			"fieldtype": "Date",
			"insert_after": "is_stock_item",
			"description": (
				"Để trống là đang bán bình thường. Có ngày thì web đặt bánh "
				"không hiện mã này cho tới hết ngày đó, dù kho vẫn còn tồn. "
				"Bật tắt ngay trên màn Kiểm bánh, không cần vào đây."
			),
		}
	]
}


# ------------------------------------------------------------- phần thuần


def dang_tat(den_ngay, hom_nay=None):
	"""Mã này có đang bị tắt bán không. Hàm THUẦN: vào là hai giá trị, ra là 1 hoặc 0.

	Ô trống, ngày hỏng định dạng, hay ngày đã qua đều là ĐANG BÁN. Nghiêng về
	phía bán chứ không nghiêng về phía tắt: một cái ô hỏng không được phép
	lặng lẽ gỡ bánh khỏi web.
	"""
	if not den_ngay:
		return 0
	try:
		den = getdate(den_ngay)
		nay = getdate(hom_nay or nowdate())
	except Exception:
		return 0
	return 1 if den >= nay else 0


# --------------------------------------------------------- chạm hệ thống


def bang(ds_ma, hom_nay=None):
	"""{mã: {tat, den_ngay}} cho một loạt mã, hỏi cơ sở dữ liệu đúng một lượt."""
	ds_ma = [str(m).strip() for m in (ds_ma or []) if str(m or "").strip()]
	if not ds_ma:
		return {}
	tho = frappe.get_all(
		"Item",
		filters={"item_code": ["in", ds_ma]},
		fields=["item_code", TRUONG],
		limit_page_length=0,
	)
	ra = {}
	for r in tho:
		den = r.get(TRUONG)
		ra[r["item_code"]] = {
			"tat": dang_tat(den, hom_nay),
			"den_ngay": str(den or ""),
		}
	return ra


@frappe.whitelist()
def dat(ma_hang=None, tat=1, den_ngay=None):
	"""Bật hoặc tắt bán một mã trên web.

	tat=1 mà không nói ngày thì tắt đến hết HÔM NAY. tat=0 thì xoá ô đi, mã
	bán lại ngay lập tức.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ma = str(ma_hang or "").strip()
	if not ma:
		frappe.throw("Thiếu mã hàng.")
	if not frappe.db.exists("Item", ma):
		frappe.throw("Không có mã hàng %s." % ma)
	if frappe.utils.cint(tat):
		den = getdate(den_ngay or nowdate())
		if den < getdate(nowdate()):
			frappe.throw("Ngày tắt bán đã qua rồi, chọn hôm nay hoặc ngày sau.")
		gt = str(den)
	else:
		gt = None
	frappe.db.set_value("Item", ma, TRUONG, gt)
	frappe.db.commit()
	_ghi_vet(ma, gt)
	return {"ma": ma, "tat": 1 if gt else 0, "den_ngay": gt or ""}


def _ghi_vet(ma, den):
	"""Ai tắt, tắt mã nào, đến bao giờ. Tắt bán là quyết định có hậu quả tiền bạc."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Item",
				"reference_name": ma,
				"content": (
					("Tạm ngừng bán trên web đến hết %s" % den) if den
					else "Cho bán lại trên web"
				) + " - " + frappe.session.user,
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass
