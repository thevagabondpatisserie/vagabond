# Bắn tin ERP vào nhóm Zalo (v562, issue #410)

Dành cho quản trị. Bản thử: một tin đầu tiên là "Khoản trả trước ERP chờ
duyệt" gửi nhóm Kế toán. Các tin khác thêm dần sau khi chạy ổn.

## 1. Tạo bot (một lần)

1. Vào bot.zaloplatforms.com bằng tài khoản Zalo của công ty, tạo bot.
2. Chép token của bot (dạng `số:chuỗi`). Không gửi token qua chat hay issue.
3. Desk, Vagabond Settings, mục **Bắn tin vào nhóm Zalo (#410)**: dán token,
   tích **Bật bắn tin Zalo**, Lưu.
4. Bấm **Zalo > Nối Zalo Bot** ở góc trên. Máy kiểm token, tự sinh khoá bí
   mật, đăng ký đường nhận và đọc kết quả Zalo gọi thử. Chỉ khi báo xanh
   "Đã nối bot ... gọi thử thành công" mới là xong. Báo cam (thất bại hoặc
   chưa rõ) thì bấm **Zalo > Kiểm lại đường nhận** sau ít phút; ô **Kết quả
   xác minh đường nhận** ghi lần kiểm gần nhất.

## 2. Gắn từng nhóm

1. Thêm bot vào nhóm Zalo (ví dụ nhóm Kế toán).
2. Trong nhóm, một người @nhắc bot một lần (gõ @tên bot và một chữ bất kỳ).
3. Tải lại Vagabond Settings: ô **Chat vừa nhắn bot** hiện mã chat và tên
   nhóm. Máy không lưu nội dung tin nhắn.
4. Bảng **Nhóm nhận tin**: thêm dòng, bấm vào dòng để mở khung dòng, rồi:
   - bấm **Chọn nhóm đã nhắn bot**, chọn nhóm (máy điền mã chat, và tên
     nhóm nếu còn trống; sửa Tên nhóm cho dễ nhận, ví dụ "Kế toán"). Mã chat
     không gõ tay được và chỉ nhận nhóm, không nhận chat riêng;
   - bấm **Chọn loại tin**, tích các loại nhóm này nhận (ví dụ Việc cần làm
     `viec` và Cảnh báo `canh_bao`), bấm Xong;
   - bấm **Chọn chủ đề**, tích chủ đề (ví dụ `cong_no`), bấm Xong.
   Hai ô này không gõ tay được. Không tích gì là nhóm nhận TẤT CẢ tin.
   Giờ im (nếu muốn) gõ đủ hai đầu dạng HH:MM, ví dụ 22:00 và 07:00. Lưu;
   gõ sai mã hay giờ thì máy báo lỗi và không lưu.
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

- Sổ **Vagabond Tin Kenh** (Desk) ghi từng tin: nhóm, loại, trạng thái, lỗi
  nếu có. Trạng thái: Chờ gửi, Đang gửi, Đã gửi, Hoãn giờ im, Đang gửi gộp,
  Đã gửi gộp, Bỏ qua (đã xử lý), Lỗi, Chưa rõ.
- Tin được ghi "Chờ gửi" cùng lúc lưu chứng từ, rồi mới gửi đi. Nếu lúc đó
  máy gửi nền trục trặc, cứ 5 phút máy tự gửi bù các dòng Chờ gửi quá 2 phút,
  nên tin không bị mất. Nhóm đã tắt hoặc bị gỡ thì ghi "Bỏ qua", kể cả tin
  đang hoãn giờ im (bật lại nhóm không bắn tin cũ).
- Dòng kẹt "Đang gửi" quá 10 phút nghĩa là máy dừng TRƯỚC khi gọi Zalo; máy
  tự đưa về Chờ gửi và gửi bù. Ngay trước khi gọi Zalo máy đổi sang "Chưa rõ",
  nên dòng kẹt "Chưa rõ" thì xem nhóm trước, máy không tự gửi lại.
- Hết giờ im, các tin hoãn được gộp; nhiều việc thì chia thành vài tin, mỗi
  việc nằm trọn trong một tin, không việc nào bị cắt.
- Trước khi gửi (kể cả sau giờ im) máy hỏi lại việc còn mở không. Khoản trả
  trước đã được duyệt, từ chối hay rút lại thì ghi "Bỏ qua (đã xử lý)", không
  nhắc nữa.
- Dòng kẹt ở "Đang gửi gộp" quá 10 phút cũng là máy dừng TRƯỚC khi gọi Zalo:
  máy tự đưa về Hoãn giờ im và gửi lại ở lượt xả sau. Phần đang gọi Zalo lúc
  máy dừng thì nằm "Chưa rõ", máy không tự gửi lại.
- "Chưa rõ" là Zalo không trả lời kịp: tin có thể đã tới. Xem nhóm trước khi
  gửi lại, máy không tự gửi lại.
- Zalo lỗi không bao giờ chặn lưu chứng từ.
- Nối bot báo bot "chưa được phép vào nhóm": vào bot.zaloplatforms.com bật
  quyền tham gia nhóm cho bot rồi bấm Nối Zalo Bot lại. Zalo ghi nhóm của bot
  đang ở giai đoạn thử (Beta).
