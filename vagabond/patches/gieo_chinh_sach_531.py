"""v531: gieo lại bản nháp ba trang chính sách của #367.

Lúc deploy v529 (27/09/2026) patch don_web_367 gieo hỏng: gieo_chinh_sach
dựng bản ghi bằng get_doc(dict) nên is_new() trả False và save() nổ
DoesNotExistError. Site vẫn lên (patch nuốt lỗi, ghi Error Log). v531 sửa
gieo_chinh_sach, patch này chạy lại đúng bước gieo. Chỉ điền chỗ còn trống,
trang nào đã có trong nháp thì giữ nguyên, trang công khai vẫn 404 cho tới
khi marketing bật hiện và xuất bản.

KHÔNG nuốt lỗi (Codex #375, d35b1d2). Patch đã ghi vào Patch Log thì không
chạy lại; nuốt lỗi như v529 là ba trang mất nháp mà deploy vẫn báo xanh, và
không có lần sau để gieo. Để lỗi nổ: migrate dừng, thấy ngay, sửa rồi chạy
lại được.
"""


def execute():
	from vagabond import noi_dung_web

	noi_dung_web.gieo_tu_tep()
