# Hướng dẫn marketing và Sales: trang đặt bánh (#367)

Trang đặt bánh: https://order.thevagabondpatisserie.com/banh
Bảng biên tập: https://order.thevagabondpatisserie.com/bien-tap-web

## Vào bảng biên tập

Mở /bien-tap-web. Chưa đăng nhập thì trang tự chuyển sang đăng nhập rồi quay
lại. Đăng nhập rồi mà thấy "chưa có quyền soạn nội dung" thì nhờ anh Việt cấp
vai Marketing trên Desk (User, thêm dòng Marketing). Góc phải có tên người
đang đăng nhập và nút Đăng xuất.

## Ảnh bánh

Ảnh trên web lấy theo thứ tự: ảnh trong hồ sơ món trên ERP, rồi ảnh Pancake,
rồi ảnh nền của tiệm. Muốn đổi ảnh một bánh: Desk, mở món (Item), tải ảnh vào
ô Hình ảnh, lưu. Ảnh phải công khai (không tick "Riêng tư"). Web đổi theo
trong vòng nửa giờ. Bánh nhiều size: tải ảnh ở size nhỏ nhất là đủ.

## Ba trang chính sách

Trong bảng biên tập, mục "Trang chính sách" có ba nút: bảo mật, điều khoản,
giao hàng và đổi trả. Bản nháp anh Việt đã duyệt đã nằm sẵn trong đó.

1. Bấm vào một trang, điền mọi chỗ trong ngoặc vuông, ví dụ [số điện thoại],
   [email], [ngày]. Ô cảnh báo màu vàng đếm số chỗ còn thiếu.
2. Tick "Hiện trang này trên website và chân trang".
3. Bấm Xuất bản. Còn chỗ trong ngoặc vuông thì máy không cho xuất bản và nói
   rõ trang nào còn thiếu.

Chưa xuất bản thì đường dẫn trang đó trả "không tìm thấy" và chân trang không
hiện đường dẫn. Bản tiếng Anh để trống thì trang chỉ có tiếng Việt.

## Cài đặt (anh Việt, Desk, Vagabond Settings)

Mục "Trang đặt bánh và quảng cáo Meta":
- Miễn phí giao từ (đ): mặc định 1.000.000. Để trống hoặc 0 là tắt.
- Số điện thoại, email, Zalo, Messenger, Facebook, Instagram, TikTok cho chân
  trang. Zalo để trống thì dùng zalo.me/<số điện thoại>.
- Webhook nhóm Sales đơn web (Lark): nhận tin khi đơn web quá 30 phút chưa
  vào Pancake.

Mục "Meta Pixel và Conversions API":
- Meta Pixel ID. Để trống thì trang không nạp Pixel, máy không gửi gì.
- Meta CAPI token: ô mật khẩu, chỉ máy chủ đọc, không bao giờ ra trình duyệt.
- Mã sự kiện thử: chỉ điền khi thử trong Events Manager, chạy thật thì xoá.

Sự kiện ghi nhận: PageView, ViewContent (mở chi tiết bánh), AddToCart,
InitiateCheckout (mở giỏ), GuiDon (khách gửi đơn, trình duyệt và máy chủ cùng
event_id), Purchase (chỉ máy chủ, khi hoá đơn của đơn đó được ghi sổ). Giai
đoạn đầu cho quảng cáo tối ưu theo InitiateCheckout rồi GuiDon.

## Sales: đơn web Chờ đối soát

Desk, danh sách "Vagabond Don Web". Chip đỏ Chờ đối soát nghĩa là Pancake mất
phản hồi lúc khách gửi, đơn có thể đã vào Pancake hoặc chưa. Máy tự tìm 5 phút
một lần theo số điện thoại, giờ và món. Quá 30 phút chưa tìm ra thì máy nhắn
nhóm Lark.

Xử lý tay: gọi khách xác nhận. Tìm được đơn bên Pancake thì điền "Mã đơn
Pancake" rồi chọn trạng thái Đã nhận, lưu (yêu cầu hoá đơn công ty tự tạo
theo mã đó). Khách không đặt nữa thì chọn Đã huỷ. Không ai chọn tay được
"Đã ghi sổ": trạng thái đó chỉ đến từ hoá đơn thật.
