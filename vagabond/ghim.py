# -*- coding: utf-8 -*-
"""Ghim nghiệp vụ hay dùng: mỗi người tự chọn tối đa 5 ô trên trang chủ.

Anh Việt giao 03/10/2026: *"thêm tính năng được pin 5 ô hay truy cập nhất
cho từng user được dùng (kế toán pin gì của kế toán hay xài)"*.

Vì sao cất ở MÁY CHỦ chứ không cất trong trình duyệt. Chị Dung mở app trên
điện thoại và trên máy quầy, bạn quầy đổi ca là đổi máy. Cất trong trình
duyệt thì ghim theo cái máy, không theo người, và xoá cache là mất. Cất ở
máy chủ thì ghim đi theo tài khoản, đúng như anh nói "cho từng user".

Chỗ cất là bảng DefaultValue sẵn có của Frappe (frappe.defaults), nên KHÔNG
phải dựng doctype mới, không phải di trú dữ liệu. Một dòng cho một người.

Đối chiếu SAP S/4HANA: màn My Home của họ cũng cất Favorites theo tài khoản
trên máy chủ và cũng đặt trần số ô, không cho ghim vô hạn.
"""

import json
import re

import frappe

TOI_DA = 5
KHOA = "vgb_ghim_nghiep_vu"

# Khoá nghiệp vụ trong app chỉ gồm chữ, số, hai dấu nối và dấu hai chấm
# (ví dụ POS, CNPT, BC:BC05, DM:DMSP). Chặn ở đây để không ai nhét được
# chuỗi lạ vào bảng mặc định của Frappe qua cửa này.
MAU_KHOA = re.compile(r"^[A-Za-z0-9:_-]{1,40}$")


# ------------------------------------------------------------- phép thuần


def chuan(ds):
	"""Bỏ rác, bỏ trùng, cắt còn tối đa TOI_DA. Không chạm Frappe.

	Giữ đúng thứ tự người dùng gửi lên: thứ tự ghim là thứ tự họ muốn thấy
	trên trang chủ, không phải thứ tự máy tự xếp.
	"""
	ra = []
	for k in ds or []:
		if not isinstance(k, str):
			continue
		k = k.strip()
		if not k or not MAU_KHOA.match(k) or k in ra:
			continue
		ra.append(k)
		if len(ra) >= TOI_DA:
			break
	return ra


def doc_chuoi(v):
	"""Đọc chuỗi đã cất thành danh sách khoá. Hỏng thì trả về rỗng.

	Bản cất có thể là chuỗi rỗng (chưa ghim gì), hoặc rác do một bản cũ ghi
	sai. Cả hai trường hợp đều phải ra danh sách rỗng chứ không được nổ, vì
	trang chủ gọi hàm này mỗi lần mở app.
	"""
	if not v:
		return []
	try:
		ds = json.loads(v)
	except Exception:
		return []
	return chuan(ds) if isinstance(ds, list) else []


# ------------------------------------------------------- phần cần Frappe


@frappe.whitelist()
def lay():
	"""Danh sách ghim của người đang đăng nhập."""
	return {
		"ghim": doc_chuoi(frappe.defaults.get_user_default(KHOA, frappe.session.user)),
		"toi_da": TOI_DA,
	}


@frappe.whitelist()
def luu(ghim=None):
	"""Ghi lại danh sách ghim của người đang đăng nhập.

	Trả về bản ĐÃ chuẩn hoá để màn hình vẽ lại theo đúng cái vừa cất, không
	vẽ theo cái nó vừa gửi đi. Hai cái lệch nhau khi người dùng gửi quá năm
	ô hoặc gửi khoá trùng.
	"""
	ds = ghim
	if isinstance(ds, str):
		try:
			ds = json.loads(ds)
		except Exception:
			ds = []
	ra = chuan(ds if isinstance(ds, list) else [])
	frappe.defaults.set_user_default(KHOA, json.dumps(ra), user=frappe.session.user)
	return {"ghim": ra, "toi_da": TOI_DA}
