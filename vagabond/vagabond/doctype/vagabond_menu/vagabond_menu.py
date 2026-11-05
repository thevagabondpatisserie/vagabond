"""Menu theo điểm bán (v640). Xem vagabond/bien_tap_menu.py.

Mỗi điểm một bản Nháp (quản lý sửa trên màn Biên tập menu) và các bản Xuất
bản đánh số phiên; bản Xuất bản phiên lớn nhất là menu đang chạy cho trang
bàn và màn Tính tiền. Không xoá bản cũ: quay về một bản trước là xuất bản
lại nội dung đó thành phiên mới.
"""
from frappe.model.document import Document


class VagabondMenu(Document):
	pass
