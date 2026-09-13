# Issue 300: nền chung và lịch sử thành viên

Owner Codex, nhánh `codex/300-members-shared`, nền main `808af6fd`.
Anh Việt giao ngày 14/09: code, mở PR, Claude review, gom chờ deploy sau v489.
Không đổi APPVER hoặc PR 302 đang phát hành.

- Tách chữ/màu/reset/header/tab/title/button từ banh.html sang nen.css; bỏ
  font base64, dùng hai OTF có sẵn. Thành viên/đặt bàn dùng nền chung.
- Đơn của khách có ngày, tiền, ảnh hoặc placeholder. Máy chủ trả nhãn và màu;
  mã 0/6/7 đã đối chiếu luồng hiện tại, tên new/delivered được Việt hoá.
  Trạng thái chưa biết hiện câu đang cập nhật, không đoán đã giao.
- Ảnh Item tra một lô sau lọc số điện thoại. Món cũ ngừng bán vẫn có ảnh;
  không gọi danh mục đang bán với giới hạn 800 làm mất món lịch sử.

## Bằng chứng trước commit

Cổng kiem_truoc_deploy.sh đạt; CI giả lập thiếu requests đạt 2955/2955.
Ba phá thử đều bị bắt: bỏ nhãn máy chủ, bỏ khung ảnh, gắn lại CSS cũ.
Chrome headless qua HTTP local tại 390px: ba trang nền đen, Qualy tải được,
không tràn ngang. Đã xem ảnh hồ sơ và toàn form đặt bàn. Đây là fixture,
không phải nghiệm thu production. Không gửi OTP, không thay hồ sơ thật.

## Còn lại

Claude review SHA trên PR; CI GitHub; kiểm mobile trên site sau deploy.
Chưa có bench/site thật cho lịch sử hồ sơ. Không nhận kiểm thuần là bench.
Issue 301 nối từ nền này trong PR riêng; khi gộp giữ đủ cả hai phạm vi.
