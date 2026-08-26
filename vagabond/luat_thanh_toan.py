# -*- coding: utf-8 -*-
"""Luật phương thức thanh toán và mã tham chiếu, dùng chung cho MỌI màn.

Anh Việt chốt 26/08/2026:

    *"MỌI MÀN TÍNH TIỀN PHẢI GIỐNG NHAU HẾT, KỂ CẢ SAU NÀY CÓ MỞ THÊM CHI
    NHÁNH MỚI THÌ CHỈ VIỆC BÊ NGUYÊN XI NHƯ VẬY SANG."*

Tệp này KHÔNG import gì cả, kể cả Frappe. Toàn phép thuần, chạy được trên
máy CI tay không. Mọi màn tính tiền (Sales, quầy D1, quầy NVHTN, và bất kỳ
quầy nào mở sau này) đều đi qua đây, nên sửa luật một chỗ là mọi màn đổi
theo, không màn nào bị bỏ quên.


HAI LUẬT TRONG TỆP NÀY
======================

**Luật 1: máy không được xoá mã người ta đã gõ.**

Hoá đơn 92561 ngày 26/08/2026. Thu ngân chốt bill với Thẻ ShinhanBank và mã
chuẩn chi 046327, lưu xong. Bill chuyển sang trạng thái đã thu tiền nên phần
thanh toán KHOÁ LẠI, và màn hình không còn vẽ ô nhập mã nữa. Bấm Ghi sổ thì
màn hình đọc ô nhập đó, không thấy nên gửi lên chuỗi RỖNG. Máy nhận chuỗi
rỗng, hiểu là "xoá mã đi", ghi đè mất 046327. Ngay câu lệnh kế tiếp, phép
kiểm ghi sổ đòi mã bắt buộc, không thấy nên chặn:

    "Phương thức Thẻ - ShinhanBank bắt buộc phải có: Số tham chiếu hoặc mã
    chuẩn chi trên bill ShinhanBank"

Trên màn hình thì mã vẫn hiện rành rành. Nhân viên đọc câu báo lỗi đó không
thể nào hiểu nổi, và bill không ghi sổ được.

Đây cùng một họ lỗi với hai chỗ đã vá trước đây trong `ban_hang.py`: nhịp
đồng bộ ghi đè giảm giá từ điểm thành viên, và ghi đè bản dịch Gemini. Cùng
một câu trả lời: **máy không đè lên chữ người thật.** Màn hình không gửi gì
không có nghĩa là người ta muốn xoá.

Chỉ có đúng một trường hợp được xoá mã: khi ĐỔI phương thức thanh toán. Mã
chuẩn chi của máy Shinhan mà để nguyên khi chuyển sang Tiền mặt thì mã đó
trỏ vào một giao dịch không còn liên quan, giữ lại còn hại hơn.


**Luật 2: nguồn đơn chỉ đi được một phương thức thì máy tự chọn.**

Đơn GrabFood thì tiền về từ Grab, đơn ShopeeFood thì tiền về từ Shopee.
Không có lựa chọn nào khác, nên bắt thu ngân bấm chọn là bắt bấm một nút chỉ
có một đáp án - vừa mất thì giờ vừa tạo cơ hội bấm nhầm.

Luật này đã chạy ở quầy D1 và NVHTN từ trước nhưng chưa có ở màn Sales, nên
đơn sàn bên Sales cứ treo "chưa chọn phương thức" cho tới khi có người vào
bấm tay. Đưa về đây thì cả ba nơi tính tiền dùng chung một luật.

Đơn 2874 ngày 25/08 là ca ngược lại: nguồn ShopeeFood mà ai đó đã chọn
"Chuyển khoản". Phép kiểm cũ chặn thẳng và không ai gỡ được ngoài việc vào
sửa tay. Nay máy tự nắn về ShopeeFood. Nắn một lựa chọn KHÔNG HỢP LỆ về lựa
chọn hợp lệ duy nhất không phải là đè lên chữ người thật, vì lựa chọn kia
vốn đã bị chặn, để nguyên thì đơn treo mãi.

Cẩn thận chỗ này: chỉ tự chọn khi nguồn có danh sách phương thức RIÊNG của
nó và danh sách đó còn đúng một cái. Nguồn dùng danh sách chung của quầy thì
tuyệt đối không tự chọn, kể cả khi ai đó tắt bớt phương thức ở màn Cài đặt
làm danh sách chung rút xuống còn một.
"""


def ma_can_ghi(ma_moi, ma_cu, pt_moi, pt_cu):
	"""Mã tham chiếu sẽ ghi vào đơn. THUẦN.

	`ma_moi` là thứ màn hình vừa gửi lên, `ma_cu` là thứ đang nằm trong đơn.

	Trả về chuỗi. Rỗng nghĩa là đơn không còn mã nào.
	"""
	moi = str(ma_moi or "").strip()
	cu = str(ma_cu or "").strip()
	a = str(pt_moi or "").strip()
	b = str(pt_cu or "").strip()
	if a and b and a != b:
		# Đổi phương thức: mã cũ thuộc về phương thức cũ, không mang sang.
		return moi
	if moi:
		return moi
	return cu


def nguon_tu_chon_duoc(co_pt_rieng, ds_pt_hop_le):
	"""Nguồn đơn này có tự suy ra được phương thức không. THUẦN."""
	if not co_pt_rieng:
		return False
	ds = [str(x).strip() for x in (ds_pt_hop_le or []) if str(x).strip()]
	return len(ds) == 1


def pt_theo_nguon(pt_dang_co, ds_pt_hop_le, co_pt_rieng=False):
	"""Phương thức thanh toán sẽ dùng cho đơn. THUẦN.

	Nguồn chỉ đi được một phương thức thì trả về đúng phương thức đó, bất kể
	ô đang để trống hay đang để một lựa chọn khác. Còn lại thì trả về đúng
	thứ đang có, không đoán thêm.
	"""
	ds = [str(x).strip() for x in (ds_pt_hop_le or []) if str(x).strip()]
	if nguon_tu_chon_duoc(co_pt_rieng, ds):
		return ds[0]
	return str(pt_dang_co or "").strip()


def may_da_nan(pt_dang_co, pt_ket_qua):
	"""Máy có nắn lựa chọn của người ta không. THUẦN.

	Dùng để ghi một dòng vào ghi chú đối soát: nắn âm thầm thì kế toán cuối
	tháng thấy con số lạ mà không biết vì sao.
	"""
	cu = str(pt_dang_co or "").strip()
	moi = str(pt_ket_qua or "").strip()
	return bool(cu) and bool(moi) and cu != moi
