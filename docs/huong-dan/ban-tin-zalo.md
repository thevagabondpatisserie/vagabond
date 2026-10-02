# Bắn tin ERP vào nhóm Zalo (v555, issue #410)

Dành cho quản trị. Bản thử: một tin đầu tiên là "Khoản trả trước ERP chờ
duyệt" gửi nhóm Kế toán. Các tin khác thêm dần sau khi chạy ổn.

## 1. Tạo bot (một lần)

1. Vào bot.zaloplatforms.com bằng tài khoản Zalo của công ty, tạo bot.
2. Chép token của bot (dạng `số:chuỗi`). Không gửi token qua chat hay issue.
3. Desk, Vagabond Settings, mục **Bắn tin vào nhóm Zalo (#410)**: dán token,
   tích **Bật bắn tin Zalo**, Lưu.
4. Bấm **Zalo > Nối Zalo Bot** ở góc trên. Máy kiểm token, tự sinh khoá bí
   mật và đăng ký đường nhận. Báo "Đã nối bot ..." là xong.

## 2. Gắn từng nhóm

1. Thêm bot vào nhóm Zalo (ví dụ nhóm Kế toán).
2. Trong nhóm, một người @nhắc bot một lần (gõ @tên bot và một chữ bất kỳ).
3. Tải lại Vagabond Settings: ô **Chat vừa nhắn bot** hiện mã chat và tên
   nhóm. Máy không lưu nội dung tin nhắn.
4. Bảng **Nhóm nhận tin**: thêm dòng, Tên nhóm "Kế toán", dán Mã chat Zalo,
   Loại tin để trống (nhận tất) hoặc ghi `viec, canh_bao`, Chủ đề `cong_no`,
   Giờ im 22:00 đến 07:00 nếu muốn. Lưu.
5. Bấm **Zalo > Gửi thử tới một nhóm**, chọn nhóm. Nhóm thấy tin thử là xong.
   **Zalo > Xem trước tin mẫu** chỉ hiện nội dung, không gửi.

## 3. Năm loại tin

| Mã | Đầu tin | Khi nào |
|---|---|---|
| thong_bao | ℹ️ THÔNG BÁO | Việc đã xảy ra, không cần làm gì |
| viec | ✅ VIỆC CẦN LÀM | Có người phải xử lý, có đường mở đúng màn |
| canh_bao | 🚨 CẢNH BÁO | Bất thường cần xử lý gấp; vẫn gửi trong giờ im |
| ban_tin | 📊 BẢN TIN | Tổng hợp; tin hoãn trong giờ im được gộp thành một bản tin |
| phat_hanh | 🚀 PHÁT HÀNH | Sau mỗi lần deploy đã kiểm site thật |

## 4. Kiểm và xử lý

- Sổ **Vagabond Tin Kenh** (Desk) ghi từng tin: nhóm, loại, trạng thái
  (Đã gửi, Hoãn giờ im, Đã gửi gộp, Lỗi, Chưa rõ), lỗi nếu có.
- "Chưa rõ" là Zalo không trả lời kịp: tin có thể đã tới. Xem nhóm trước khi
  gửi lại, máy không tự gửi lại.
- Zalo lỗi không bao giờ chặn lưu chứng từ.
- Chưa có tài liệu chính thức đọc được của Zalo Bot cho việc gửi vào nhóm
  khi không ai nhắn trước; nếu gửi thử vào nhóm báo lỗi thì thử với chat
  riêng (một người nhắn bot) và báo lại để chỉnh.
