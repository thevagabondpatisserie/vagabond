"""Đọc ngày từ dữ liệu Pancake. MỘT hàm cho cả tiệm, không ai được viết lại.

VÌ SAO CÓ TỆP NÀY
-----------------
Pancake trả ngày theo GIỜ UTC và phần lớn trường hợp KHÔNG khai múi giờ. Một
đơn giao ngày 24/08 giờ Việt Nam được Pancake ghi là:

	estimate_delivery_date : 2026-08-23T17:00:00
	tags                   : ["13h - 15h"]

17:00 UTC cộng 7 tiếng là 00:00 ngày 24/08. Cắt thẳng mười ký tự đầu thì ra
23/08, LÙI ĐÚNG MỘT NGÀY.

Lỗi này đã xảy ra HAI LẦN, ở hai tệp khác nhau, vì mỗi tệp tự viết lấy một
hàm đọc ngày:

  19/08/2026  `van_don.py` cắt thẳng. 75 vận đơn bị đẩy lùi một ngày và 27
              đơn của hôm đó biến mất khỏi màn Vận đơn. Đã sửa tại chỗ.
  23/08/2026  `mua_vu.py` vẫn cắt thẳng, vì hàm của nó là một hàm khác. Đơn
              hàng trung thu đặt cho 24/08 hiện ở tab 23/08, và ô "Đã đặt"
              của 23/08 nuốt mất 37 hộp của ngày hôm sau.

Sửa tại chỗ lần nữa thì lần thứ ba sẽ lại xảy ra ở tệp thứ ba. Nên từ nay
CHỈ CÓ MỘT hàm, nằm ở đây, và có ca kiểm quét chặn tệp khác tự viết lại.

BA ĐIỀU PHẢI NHỚ KHI SỬA TỆP NÀY
--------------------------------
1. Hàm THUẦN, không chạm Frappe. Kiểm thử được không cần site.
2. Đọc không được thì trả về RỖNG. Bên gọi phải coi rỗng là "không biết",
   TUYỆT ĐỐI không được coi là hôm nay. Coi là hôm nay thì đơn không rõ ngày
   dồn hết vào hôm nay và bảng báo thừa.
3. Phần GIỜ trong `estimate_delivery_date` KHÔNG phải giờ giao. Hai đơn cùng
   mang 17:00 mà một đơn khung 13h-15h, một đơn khung 17h-19h. Giờ giao thật
   nằm ở thẻ khung giờ. Hàm này chỉ trả về NGÀY.
"""

from datetime import datetime, timedelta, timezone

MUI_VN = "Asia/Ho_Chi_Minh"

# Cac truong Pancake mang ngay, xep theo thu tu tin cay giam dan.
TRUONG_NGAY_GIAO = ("estimate_delivery_date", "time_delivery_at", "inserted_at")

# Moc unix hop le: tu 2000-01-01 den 2100-01-01. Ngoai khoang nay thi con so
# do khong phai moc thoi gian, dung doan bua.
UNIX_NHO_NHAT = 946684800
UNIX_LON_NHAT = 4102444800


def _lech_mui(duoi):
	"""Phần khai múi giờ ở đuôi chuỗi ISO, đổi ra số PHÚT. None là không khai."""
	s = str(duoi or "").strip()
	if not s:
		return None
	if s in ("Z", "z"):
		return 0
	dau = s[0]
	if dau not in "+-":
		return None
	so = s[1:].replace(":", "")
	if len(so) != 4 or not so.isdigit():
		return None
	phut = int(so[:2]) * 60 + int(so[2:])
	return -phut if dau == "-" else phut


def ngay_hop_le(ngay):
	"""Chuỗi yyyy-mm-dd có ra hồn không. Không hợp lệ thì trả rỗng."""
	t = str(ngay or "")
	if len(t) != 10 or t[4] != "-" or t[7] != "-":
		return ""
	try:
		y, m, d = int(t[:4]), int(t[5:7]), int(t[8:10])
	except ValueError:
		return ""
	if 2000 <= y <= 2100 and 1 <= m <= 12 and 1 <= d <= 31:
		return t
	return ""


def _tu_unix(giay):
	"""Mốc unix giây -> ngày giờ Việt Nam."""
	from zoneinfo import ZoneInfo

	try:
		g = int(float(giay))
	except (TypeError, ValueError):
		return ""
	# Pancake co cho tra moc bang MILI giay. Xem v266: moc quet phai la giay.
	if g > UNIX_LON_NHAT and g // 1000 <= UNIX_LON_NHAT:
		g = g // 1000
	if not (UNIX_NHO_NHAT <= g <= UNIX_LON_NHAT):
		return ""
	t = datetime.fromtimestamp(g, tz=timezone.utc)
	return ngay_hop_le(t.astimezone(ZoneInfo(MUI_VN)).strftime("%Y-%m-%d"))


def ngay_tu_iso(s):
	"""Ngày THEO GIỜ VIỆT NAM, đọc từ một giá trị ngày Pancake trả về. THUẦN.

	Nhận được cả ba dạng Pancake đang dùng:

	  "2026-08-23T17:00:00"        ISO không khai múi giờ -> hiểu là UTC
	  "2026-08-24T00:00:00+07:00"  ISO có khai -> tôn trọng phần khai
	  1755954000                   mốc unix giây (hoặc mili giây)

	Chuỗi chỉ có phần ngày, không có giờ, thì trả thẳng phần ngày đó: không
	có giờ thì không quy đổi được, và đoán bừa không làm nó đúng hơn.
	"""
	from zoneinfo import ZoneInfo

	if isinstance(s, bool):
		return ""
	if isinstance(s, (int, float)):
		return _tu_unix(s)
	t = str(s or "").strip()
	if not t:
		return ""
	# Chuoi toan so la moc unix goi duoi dang chuoi.
	if t.isdigit():
		return _tu_unix(t)
	if len(t) < 10 or t[4] != "-" or t[7] != "-":
		return ""
	if len(t) < 19:
		return ngay_hop_le(t[:10])
	try:
		goc = datetime.strptime(t[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
	except ValueError:
		return ""
	lech = _lech_mui(t[19:])
	if lech is None:
		lech = 0
	utc = (goc - timedelta(minutes=lech)).replace(tzinfo=timezone.utc)
	return ngay_hop_le(utc.astimezone(ZoneInfo(MUI_VN)).strftime("%Y-%m-%d"))


def ngay_giao(don, truong=TRUONG_NGAY_GIAO):
	"""Ngày giao của một đơn Pancake, theo giờ Việt Nam. Rỗng là không biết.

	Lần lượt thử từng trường trong `truong`. Trường nào đọc ra ngày hợp lệ
	thì lấy, không đọc được thì thử trường sau.
	"""
	for o_ten in truong:
		ra = ngay_tu_iso((don or {}).get(o_ten))
		if ra:
			return ra
	return ""


def ngay_tao(don):
	"""Ngày TẠO đơn, theo giờ Việt Nam. Rỗng là không biết.

	Dùng để tách "Phát sinh" khỏi "Đã đặt": đơn giao hôm nay mà cũng tạo
	trong hôm nay là PHÁT SINH, tạo từ hôm trước là ĐÃ ĐẶT.
	"""
	return ngay_tu_iso((don or {}).get("inserted_at"))
