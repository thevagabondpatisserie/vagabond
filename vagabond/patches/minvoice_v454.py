"""#225 v454: cập nhật Server Script đã chạy v449 qua đường migrate thật.

Mốc dong_bo_cau_truc chỉ dựng trường, không cập nhật Server Script.
Giữ lỗi từ dong_bo để migrate dừng nếu script trên site khác bản đã biết.
"""


def execute():
	from vagabond.minvoice_kich_ban import dong_bo

	dong_bo()
