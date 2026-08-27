# -*- coding: utf-8 -*-
"""Dịch lỗi của nhà cung cấp mô hình ra câu người vận hành hiểu được.

PHÉP THUẦN. Không nạp Frappe, không nạp requests, không chạm mạng. Đặt riêng
ra một tệp để ca kiểm nạp được trên máy chạy CI tay không.


VÌ SAO PHẢI CÓ TỆP NÀY
======================

Ngày 26/08/2026 anh Việt báo trợ lý không trả lời được dù đã dán khoá API.
Màn hình chỉ hiện đúng một câu: "Trợ lý đang không gọi được. Vui lòng thử lại
sau ít phút." Câu đó đúng nhưng vô dụng, nó khiến người ta đi dò khoá, dò
mạng, dò quyền, trong khi nguyên nhân thật nằm ở chỗ khác hẳn: tài khoản
Anthropic của tiệm hết số dư.

Một câu báo lỗi không chỉ ra được việc cần làm thì tốn thời gian đúng bằng
việc không báo gì. Mỗi loại lỗi ở đây đều dẫn tới một việc khác nhau: nạp
tiền, dán lại khoá, sửa tên mô hình, hay chỉ là chờ. Cho nên phải tách ra.

Lưu ý riêng cho chỗ hết số dư: gói Claude Pro hay Max mua theo tháng KHÔNG
dùng chung số dư với API. Đây là chỗ dễ nhầm nhất nên câu báo lỗi phải nói
thẳng ra.
"""

CHUNG = ("Trợ lý đang không gọi được. Vui lòng thử lại sau ít phút.")


def _lay(than, *duong):
	"""Móc một giá trị trong lớp lồng nhau, thiếu tầng nào thì trả chuỗi rỗng."""
	cho = than
	for buoc in duong:
		if not isinstance(cho, dict):
			return ""
		cho = cho.get(buoc)
	return cho if isinstance(cho, str) else ""


def doc_loi(than):
	"""Rút (kiểu lỗi, lời lỗi) từ thân trả về của nhà cung cấp.

	Thân có thể là chữ thô chứ không phải từ điển, vì lúc hỏng nặng thì
	người ta trả về HTML của máy chủ vòng ngoài.
	"""
	if isinstance(than, str):
		return "", than
	return _lay(than, "error", "type"), _lay(than, "error", "message")


def loi_mo_hinh(ma_trang_thai, than, mo_hinh=""):
	"""Câu báo lỗi gửi ra màn hình, theo đúng việc người dùng cần làm.

	`ma_trang_thai` là mã HTTP, `than` là thân trả về đã đọc thành từ điển
	hoặc còn nguyên dạng chữ.
	"""
	kieu, loi = doc_loi(than)
	ma = 0
	try:
		ma = int(ma_trang_thai)
	except Exception:
		ma = 0
	thap = (loi or "").lower()

	if "credit balance" in thap or "insufficient" in thap:
		return ("Tài khoản Anthropic của tiệm đã hết số dư nên trợ lý không "
			"gọi được mô hình. Vào console.anthropic.com, mục Billing, nạp "
			"thêm rồi hỏi lại. Lưu ý gói Claude Pro hay Max trả theo tháng "
			"KHÔNG dùng chung số dư với khoá API.")

	if ma == 401 or kieu == "authentication_error":
		return ("Khoá API của trợ lý không đúng hoặc đã bị thu hồi. Vào màn "
			"Cài đặt, mục Trợ lý, dán lại khoá mới rồi lưu.")

	if ma == 403 or kieu == "permission_error":
		return ("Khoá API này không được phép gọi mô hình. Kiểm tra lại quyền "
			"của khoá trong console.anthropic.com.")

	if kieu == "not_found_error" and (mo_hinh or "model" in thap):
		return ("Không có mô hình tên \"%s\". Sửa ô Mô hình trong màn Cài đặt, "
			"hoặc để trống ô đó để dùng bản mặc định." % (mo_hinh or "?"))

	if ma == 429 or kieu == "rate_limit_error":
		return ("Trợ lý đang gọi quá nhanh so với hạn mức. Chờ khoảng một phút "
			"rồi hỏi lại.")

	if ma == 529 or kieu == "overloaded_error":
		return ("Mô hình đang quá tải phía nhà cung cấp. Thử lại sau ít phút.")

	if ma >= 500:
		return ("Nhà cung cấp mô hình đang lỗi (mã %d). Thử lại sau ít phút."
			% ma)

	if loi:
		return ("Trợ lý không gọi được mô hình (mã %d). Nhà cung cấp báo: %s"
			% (ma, loi.strip()[:200]))

	return CHUNG
