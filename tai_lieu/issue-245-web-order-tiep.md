# #245: cải thiện trực tiếp trang order

Anh Việt chọn giữ cách chọn bánh của web hiện tại sau khi xem prototype.
Áp dụng branding Figma vào phần chữ, màu, khoảng cách và thao tác; không
đặt landing page dài trước danh mục bánh.

## Phạm vi hiện có trong code

- Giữ tab In season, In store, Có sẵn hôm nay, Đặt bánh trước và checkout.
- CMS sửa tiêu đề mục, lời chào, ảnh/chữ theo từng tab hoặc cuối trang.
  Preview nạp chính /banh?bien_tap=1; chọn khối bằng chạm vào trang.
  Frame chỉ đọc; chặn gửi fetch khác GET/HEAD trước khi code order nạp.
- /dat-ban nhận yêu cầu, chưa tự giữ chỗ. Nhân viên xử lý tại Desk danh sách
  Vagabond Dat Ban. Lưu lịch cơ sở/khung giờ bằng Vagabond Cau Hinh Dat Ban;
  mặc định tắt. Không có quyền xóa phiếu trong các role mới.
- /thanh-vien dùng OTP có sẵn trong dang_nhap.py. Cookie HttpOnly/Secure,
  SameSite Strict, không lưu vé vào localStorage. Hồ sơ lấy theo số đã xác
  thực; số điểm đọc Vagabond So Diem, không dùng Loyalty Point Entry cũ.
- Khóa OTP khi xác thực để hai request không tiêu thụ cùng mã hoặc ghi đè
  số lần nhập sai của nhau.
- Định tuyến nhận apex/www và hai trang mới. Link in/phát ra vẫn giữ order
  tới khi DNS/SSL tên miền chính đã được xác minh.

## Kiểm và điều còn thiếu

Tầng khung 2713/2713 đạt; JS syntax và hai gate repo được chạy ở phiên.
Đã có bộ kiểm DB web_editor_245 và web_khach_245 trong workflow bench.
Chưa nhận là đã bench HTTP, đã review độc lập hoặc đã deploy từ các kiểm
thuần. Không gọi OTP/Pancake thật để kiểm, không tạo yêu cầu khách thật.

Cần kiểm bổ sung: OTP đồng thời qua HTTP, cookie/login/logout thực sự,
đổi cấu hình khi đang gửi, hai yêu cầu cùng khóa chạy đồng thời, reload
và migrate giữ nội dung, preview qua đúng Frappe cache và header iframe.

## Tên miền

Mắt Bão hiện dùng adaline.ns.cloudflare.com và kareem.ns.cloudflare.com.
DNS phải sửa tại tài khoản Cloudflare đang quản lý zone. Đăng nhập lưu sẵn
chưa vào được: different login provider. Chưa thay DNS/Name Server.

Trước cắt tên miền: lấy bản ghi hiện tại làm rollback, giữ MX/TXT/email,
đăng ký apex/www ở Frappe Cloud, kiểm SSL và đường khách, lập chuyển hướng
các URL WordPress cũ. Sau cắt: giữ order và query/hash thanh toán đang dùng,
kiểm app/ERP không đổi, rồi mới đổi link_khach và canonical sang apex.
Không dùng việc chuyển Name Server về Mắt Bão để vượt qua thiếu tài khoản
Cloudflare vì có thể làm mất các bản ghi email/app hiện hành.
