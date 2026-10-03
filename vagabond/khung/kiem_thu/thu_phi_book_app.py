"""Màn "Phí giao hàng book app" - gộp phí trả cho app giao ngoài.

Anh Việt 03/10/2026: thêm nút trên màn Giao hàng, tổng hợp phí giao hàng đặt
qua app trên các vận đơn, chia theo app và theo tháng, có nút xuất Excel.

Hai quyết định phạm vi anh Việt đã chốt, bộ ca này chốt lại để lần sau không
ai nới ra mà không biết:

1. CHỈ đếm vận đơn trạng thái "Đã giao". Đơn huỷ hay giao không được thì bên
   app không thu tiền, cộng vào là số không khớp tiền thật phải trả.
2. CHỈ đếm kênh ngoài. "Shipper nội bộ" và "Khách tự lấy" không phải tiền trả
   ra ngoài nên không thuộc màn này.

Phần gộp tháng là phép THUẦN (`_phi_app_thang`), không chạm Frappe, nên kiểm
thẳng được. Phần lọc trạng thái và kênh nằm ở `_phi_app_quet` vốn phải hỏi cơ
sở dữ liệu; chỗ đó kiểm bằng cách đọc bộ lọc chứ không gọi thật, và có ca tích
hợp riêng trên site chạy đường đầy đủ.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _ham():
	from vagabond.van_don import _phi_app_thang

	return _phi_app_thang


def _don(ngay, app, tien):
	return {"ngay_giao": ngay, "kenh": app, "phi_giao": tien}


# ------------------------------------------------------------- gộp theo tháng


@ca("Phí book app: gộp đúng theo tháng và theo app")
def _():
	gop = _ham()
	ra = gop([
		_don("2026-09-02", "Ahamove", 30000),
		_don("2026-09-15", "Ahamove", 20000),
		_don("2026-09-20", "GreenSM", 45000),
		_don("2026-10-01", "Ahamove", 25000),
	])
	la("tổng số chuyến", ra["tong_don"], 4)
	la("tổng phí", ra["tong_tien"], 120000.0)
	la("hai tháng", len(ra["bang"]), 2)
	la("tháng mới nhất đứng trước", ra["bang"][0]["thang"], "2026-10")
	la("tháng 9 có ba chuyến", ra["bang"][1]["don"], 3)
	la("tháng 9 cộng đúng tiền", ra["bang"][1]["tien"], 95000.0)


@ca("Phí book app: app xếp theo tiền giảm dần, không theo bảng chữ cái")
def _():
	gop = _ham()
	# Phải chọn dữ liệu mà hai cách sắp cho kết quả KHÁC nhau, nếu không ca
	# này xanh cả khi code sắp theo bảng chữ cái. Ahamove đứng TRƯỚC GreenSM
	# theo bảng chữ cái, nên cho Ahamove ít tiền: đúng thì GreenSM phải lên
	# đầu. Lần đầu viết ca này đã chọn ngược và đột biến không bắt được.
	ra = gop([
		_don("2026-09-02", "Ahamove", 10000),
		_don("2026-09-03", "GreenSM", 90000),
	])
	la("app tiêu nhiều tiền nhất đứng đầu", ra["apps"][0]["app"], "GreenSM")
	la("app thứ hai", ra["apps"][1]["app"], "Ahamove")
	# Cột trong mỗi dòng tháng phải theo đúng thứ tự đó, không được lệch.
	la("cột đầu của bảng cũng là GreenSM", ra["bang"][0]["o"][0]["app"], "GreenSM")


@ca("Phí book app: ô trống của một app trong tháng vẫn hiện số không")
def _():
	gop = _ham()
	ra = gop([
		_don("2026-09-02", "Ahamove", 30000),
		_don("2026-10-05", "GreenSM", 40000),
	])
	# Mỗi dòng tháng phải có đủ ô của MỌI app, kể cả app tháng đó không chạy.
	# Thiếu ô thì bảng lệch cột, người đọc tưởng app kia ngừng dùng.
	for d in ra["bang"]:
		la("dòng %s đủ hai cột app" % d["thang"], len(d["o"]), 2)
	t9 = [d for d in ra["bang"] if d["thang"] == "2026-09"][0]
	o_green = [x for x in t9["o"] if x["app"] == "GreenSM"][0]
	la("tháng 9 GreenSM không chuyến nào", o_green["don"], 0)
	la("tháng 9 GreenSM không tốn tiền", o_green["tien"], 0.0)


# ------------------------------------------------------- bình quân một chuyến


@ca("Phí book app: bình quân một chuyến tính theo số chuyến thật")
def _():
	gop = _ham()
	ra = gop([
		_don("2026-09-02", "Ahamove", 30000),
		_don("2026-09-03", "Ahamove", 50000),
	])
	la("bình quân chung", ra["bq_chung"], 40000.0)
	la("bình quân của app", ra["apps"][0]["bq"], 40000.0)


@ca("Phí book app: không chuyến nào thì bình quân là 0, không chia cho 0")
def _():
	gop = _ham()
	ra = gop([])
	la("không chuyến", ra["tong_don"], 0)
	la("không tiền", ra["tong_tien"], 0.0)
	la("bình quân bằng 0 chứ không nổ", ra["bq_chung"], 0.0)
	la("bảng rỗng", len(ra["bang"]), 0)


@ca("Phí book app: chuyến quên khai phí vẫn đếm chuyến và được đếm riêng")
def _():
	gop = _ham()
	# Quên điền phí là chuyện xảy ra thật. Bỏ hẳn chuyến đó khỏi bảng thì số
	# chuyến sai; cộng như bình thường mà không nói gì thì bình quân bị kéo
	# xuống và không ai biết vì sao. Nên vẫn đếm, và đếm riêng để màn nhắc.
	ra = gop([
		_don("2026-09-02", "Ahamove", 30000),
		_don("2026-09-03", "Ahamove", 0),
	])
	la("vẫn đủ hai chuyến", ra["tong_don"], 2)
	la("tiền chỉ cộng chuyến có khai", ra["tong_tien"], 30000.0)
	la("đếm riêng chuyến quên khai phí", ra["khong_khai_phi"], 1)


@ca("Phí book app: đơn thiếu ngày giao bị bỏ, không rơi vào tháng rỗng")
def _():
	gop = _ham()
	ra = gop([
		_don("2026-09-02", "Ahamove", 30000),
		_don("", "Ahamove", 99000),
		_don(None, "GreenSM", 88000),
	])
	la("chỉ đếm chuyến có ngày", ra["tong_don"], 1)
	la("tiền không dính đơn thiếu ngày", ra["tong_tien"], 30000.0)
	la("không sinh tháng rỗng", len(ra["bang"]), 1)


@ca("Phí book app: ngày giao có cả giờ vẫn cắt đúng tháng")
def _():
	gop = _ham()
	ra = gop([_don("2026-09-30 23:45:00", "Ahamove", 30000)])
	la("cắt đúng tháng", ra["bang"][0]["thang"], "2026-09")


# ------------------------------------------------------------- phạm vi đã chốt


@ca("Phí book app: chỉ quét vận đơn Đã giao, không đếm đơn huỷ hay giao lỗi")
def _():
	import inspect

	from vagabond import van_don

	nguon = inspect.getsource(van_don._phi_app_quet)
	dung("lọc theo hằng trạng thái", "PHI_APP_TT" in nguon)
	la("hằng trạng thái đúng là Đã giao", van_don.PHI_APP_TT, "Đã giao")
	# Chốt bằng giá trị hằng chứ không bằng chuỗi trong mã: đổi hằng là ca đổ.
	dung("không tự gán trạng thái khác", '"Huỷ"' not in nguon)


@ca("Phí book app: chỉ quét kênh ngoài, không đếm shipper nội bộ hay khách tự lấy")
def _():
	from vagabond import van_don

	ngoai = set(van_don.KENH_NGOAI.keys())
	dung("không có shipper nội bộ", "Shipper nội bộ" not in ngoai)
	dung("không có khách tự lấy", "Khách tự lấy" not in ngoai)
	dung("có đủ các app đang dùng",
		{"Ahamove", "GreenSM", "BE", "Grab", "Lalamove"} <= ngoai)
