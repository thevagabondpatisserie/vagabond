"""Một tờ hoá đơn mua nối vào hồ sơ thanh toán làm hoá đơn đến sau (v530).

Nối ở mức hồ sơ, nhiều tờ phủ nhiều khoản. Chỉ thêm hoặc gỡ qua
vagabond.ho_so_bo_sung.noi_nhieu / go_noi; sửa thẳng thì kiem_bo_sung chặn.
Xem vagabond/hoa_don_sau.py.
"""

from frappe.model.document import Document


class VagabondHoSoTTHDSau(Document):
	pass
