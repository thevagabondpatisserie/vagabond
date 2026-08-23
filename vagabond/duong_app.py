"""Bảng đường dẫn của app Bếp: một địa chỉ thật cho mỗi màn hình.

VÌ SAO CÓ TỆP NÀY
-----------------
Anh Việt 23/08/2026: *"click vào bất kỳ menu nào URL cũng đứng im, F5 là bị
văng về trang chủ"*.

Đúng như vậy, và đây là lý do. App Bếp KHÔNG dùng Vue, cũng không có Vue
Router. Nó là JavaScript thuần, ghép từ các phần trong `public/js/bep/`. Việc
đi lại giữa các màn do một chồng hàm `S.stack` lo, và `go()` có gọi
`history.pushState` nhưng luôn truyền `location.href`, tức là ĐỊA CHỈ KHÔNG
ĐỔI. Nhờ vậy nút Back của trình duyệt lui đúng từng màn, nhưng địa chỉ trên
thanh vẫn là `/bep`, nên F5 chỉ nạp lại `/bep` và về màn chủ.

Muốn F5 đứng nguyên màn thì cần hai vế, thiếu một vế là hỏng:
  1. Máy khách phải ĐỔI địa chỉ khi mở màn (xem `vgbDatDuong` trong
     02-trang-chu.js).
  2. Máy chủ phải TRẢ VỀ chính app đó khi trình duyệt hỏi địa chỉ mới. Không
     có vế này thì F5 ra trang 404.

Bảng dưới đây là vế thứ hai, và cũng là nguồn sự thật cho vế thứ nhất.

VÌ SAO LIỆT KÊ TỪNG ĐƯỜNG CHỨ KHÔNG BẮT TẤT
-------------------------------------------
Bắt tất kiểu `/<path:duong>` thì mọi địa chỉ lạ trên site đều rơi vào app
Bếp, kể cả các trang khách như `banh`, `btp`, `kiem-banh`, `tt`, và cả những
trang chưa ai dựng. Đó đúng là loại hook rộng mà quy tắc 6 của repo cấm.
Liệt kê từng đường thì va chạm lộ ra ngay lúc chạy ca kiểm, không lộ trên
máy khách hàng.

QUY ƯỚC ĐẶT TÊN: không dấu, gạch nối, đọc được, và KHÔNG trùng route của
Web Page nào đang có. Ca kiểm `thu_duong_app.py` canh chuyện trùng này.
"""

# slug -> khoa man hinh trong vgbGo()
#
# Chi khai nhung man co the mo THANG tu trang chu, dung sau nhau. Man con
# nam sau mot man cha (vi du chi tiet mot phieu) thi khong khai o day: mo
# thang vao do ma khong co du lieu cha la vo man.
DUONG = {
	"don-da-huy": "DTREO",
	"ho-so-thanh-toan": "APPTT",
	"cong-no-phai-tra": "CNPT",
	"hoa-don-mua": "HDMUA",
	"hoa-don-ban": "HDBAN",
	"doi-chieu-mua": "DCM",
	"don-mua-hang": "PO",
	"duyet-yeu-cau": "DUYETYC",
	"nha-cung-cap": "NCC",
	"bang-gia": "BGIA",
	"nhap-kho": "RCV",
	"kiem-ke": "KK",
	"san-xuat": "MFG",
	"cong-thuc": "CTBOM",
	"ton-kho": "STOCK",
	"doanh-so": "DS",
	"bao-cao": "BCHUB",
	"cong-no": "CN",
	"hoan-tien": "HT",
	"nop-quy": "NQ",
	"khach-hang": "KH",
	"van-don": "VD",
	"khuyen-mai": "KM",
	"hop-dong": "HDG",
	"thanh-toan": "PAY",
}

# Web Page dang co tren site, KHONG duoc dat slug trung. Ca kiem doi chieu
# danh sach nay; them Web Page moi thi them vao day.
ROUTE_DA_CO = (
	"banh", "btp", "cuon-ma", "in-tem", "kho-moi", "kiem-banh", "bep",
	"kho-v2", "ong-trang", "sop-san-xuat", "suc-khoe", "tt", "xhd",
)

# Web Page chua chinh app Bep. F5 tai bat ky slug nao o tren deu duoc tra ve
# trang nay, roi may khach doc location.pathname de mo dung man.
TRANG_APP = "bep"


def luat_dinh_tuyen():
	"""Danh sách cho hook `website_route_rules`. THUẦN, không chạm Frappe."""
	return [{"from_route": "/" + s, "to_route": TRANG_APP} for s in sorted(DUONG)]
