"""Cửa chạy bộ kiểm thử tích hợp trên site thật.

	bench --site <site> execute vagabond.khung.kiem_that.cua.chay

hoặc gọi qua API từ Desk. Chỉ giám đốc và System Manager mở được: bộ này
ghi chứng từ thật xuống cơ sở dữ liệu (rồi lùi lại), không phải thứ để mở
cho cả tiệm bấm.

Đọc `nen.py` trước khi thêm ca kiểm mới. Ba lớp bảo vệ dữ liệu thật nằm ở
đó, và ca kiểm nào tự ý gọi `frappe.db.commit` là phá cả ba lớp.
"""

import frappe

from vagabond.khung.kiem_that import nen

# Nạp các mô đun ca kiểm. Thêm bộ ca mới thì thêm tên vào đây, giống cách
# `khung/kiem_thu/chay.py` làm.
from vagabond.khung.kiem_that import thu_don_huy  # noqa: F401,E402
from vagabond.khung.kiem_that import thu_nhap_kho  # noqa: F401,E402

QUYEN = ("System Manager", "Giám đốc", "AP Giám đốc")


def _chan():
	if not set(frappe.get_roles()) & set(QUYEN):
		frappe.throw("Chỉ giám đốc hoặc quản trị hệ thống mới chạy được bộ "
			"kiểm thử tích hợp, vì nó ghi chứng từ thử xuống cơ sở dữ liệu.")


@frappe.whitelist()
def chay(im=1):
	"""Chạy hết ca kiểm tích hợp. Trả về bảng kết quả, không sửa gì lâu dài.

	`im=1` chỉ trả về ca hỏng. `im=0` trả về cả ca đạt.

	Đọc kỹ hai khoá `chung_tu_con_sot` và `so_luong_lech` trong kết quả:
	chúng phải RỖNG. Không rỗng nghĩa là điểm lưu đã không lùi hết và có
	chứng từ thử nằm lại trong sổ thật, phải đi dọn ngay.
	"""
	_chan()
	kq = nen.chay_het(im=int(im or 0))
	if not kq["sach"]:
		frappe.log_error(frappe.as_json(kq),
			"vagabond: kiem thu tich hop de lai vet trong co so du lieu")
	return kq
