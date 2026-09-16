# Quỹ tạm ứng trả nhân viên và APP hoàn người ứng

## Phạm vi đã được duyệt

Anh Việt ngày 16/09/2026 xác nhận: nhân viên mua bằng petty, người ứng
trả nhân viên qua tài khoản cá nhân đã gắn quỹ 141. TTNB xác nhận lần trả
nhân viên. APP hoàn ứng giữ chứng cứ đó; công ty hoàn cho đúng người ứng
bằng một giao dịch khác. Không biến Bank Account cá nhân thành tài khoản
công ty và không tạo bút toán tại bước khớp TTNB.

Owner: Codex. Issue #328. Nền 8d134e747acd6db4387b5df070bba38acbf945fc.
Bản này xếp cùng đợt với #334/#336 đã merge, chưa phát hành riêng.

## Thay đổi

- Nguồn chi TTNB nhận tài khoản công ty hoặc quỹ 141 còn hoạt động, có
  Supplier chủ quỹ. Không nhận tài khoản cá nhân thường/thiếu chủ.
- APP nối TTNB kiểm cùng người ứng, đúng tiền, đúng sao kê; chứng cứ đầu
  vào nằm ở dòng APP, không dùng làm giao dịch công ty hoàn ở đầu hồ sơ.
- Khóa chứng từ lúc giữ phiếu. Mã FT và tên Bank Transaction là hai cách
  gọi một dòng tiền, không được dùng để hoàn hai lần.
- Gợi ý phiếu trước khi cắt giới hạn danh sách: cùng sao kê, đúng mã TTNB,
  đúng tiền, rồi mới nhất. Người lập xem và xác nhận, không tự nối.
- Không sửa chứng từ thật, không cập nhật lịch sử nội dung chuyển khoản.

## Giao diện

Giữ khung sheet có ô tìm kiếm, danh sách và nút đóng. Mỗi dòng gồm tên và
số tiền; dòng phụ mở đầu bằng Cùng giao dịch / Đúng mã phiếu / Đúng số tiền
nếu có. Không có gợi ý thì vẫn hiện phiếu mới nhất. 0 dòng giữ câu hướng
dẫn hiện hành; lỗi API nói không đọc được, không coi là danh sách rỗng.
1 dòng vẫn cần chọn và xác nhận. Danh sách tối đa 60 dòng mặc định, lọc và
xếp gợi ý từ toàn bộ phiếu hợp lệ trong 180 ngày trước khi cắt giới hạn.
Không đổi nút nối thành thao tác tự ghi chứng từ.

## Cổng và việc còn phải kiểm

Local: 3075 ca đạt, hành vi giao diện 56 ca đạt. Bộ kiểm tích hợp bổ sung
luồng TTNB 141 -> APP cùng chủ, chuẩn hóa FT/BT và chống hoàn trùng.
Chưa được coi là bench đạt cho tới khi run trên SHA cuối báo thành công.
Cần phủ tiếp chuỗi duyệt/ghi sổ/hoàn từ ngân hàng công ty, retry và hủy,
đối chiếu GL không sinh chi phí hai lần. Chưa có ảnh site sau sửa 390px.
Không dùng ảnh giả lập thay bằng chứng site và không merge khi thiếu cổng.
