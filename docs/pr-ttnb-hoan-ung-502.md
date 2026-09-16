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
Không đổi nút nối thành thao tác tự ghi chứng từ. Đếm chỉ đọc trên site
ngày 16/09: 22 phiếu hợp lệ trong phạm vi này.

## Cổng và việc còn phải kiểm

Local: 3078 ca đạt, hành vi giao diện 56 ca đạt. Bench 35084543547 trên
b0cc6a0bfd99dd53abc30cf0290ce971e053a2bd SUCCESS: 230/230 ở cả hai lượt,
sach=1, không chứng từ sót và không lệch số lượng. Ca mới chạy thật TTNB
141 -> APP -> duyệt -> Purchase Invoice -> Payment Entry -> retry, giữ
chứng cứ trả nhân viên riêng với sao kê công ty hoàn. Hai cách nhập FT/BT
không tạo được hồ sơ thứ hai hoặc hai khoản trong một hồ sơ.

Bổ sung sau SHA đó chỉ có ca kiểm hủy/gửi lại và tài liệu, không đổi mã
nghiệp vụ. Cần kiểm CI SHA cuối trước khi ghép. Kiểm hủy/gửi lại hiện là
logic local; chưa có phép đo hai kết nối DB đồng thời. Chưa có ảnh sheet
gợi ý sau sửa trên site 390px. Smoke trình duyệt chung của bench đạt nhưng
không thay bằng chứng màn gợi ý riêng. Không merge khi thiếu cổng.

PR337 cũng dùng số dự kiến 502; phải chốt lại APPVER/patch khi tích hợp.

Tám ca tập trung đạt; đột biến bỏ kiểm chủ quỹ làm đỏ 1 ca, bỏ kiểm phiếu
đã giữ làm đỏ 2 ca, bỏ ưu tiên cùng giao dịch làm đỏ 1 ca. Khôi phục code
thì tám ca đạt. Đây là kiểm logic tại máy, không thay kiểm site.

## Tích hợp v503 - 16/09/2026

Bench SHA ad6d45eccfba3297b9ffda16f1abe01649f7da17 đã SUCCESS trong run35085888539.
Gộp PR337 SHA513d68d8be0b2fc69fdf5ae245b6723693277455 vào nhánh; giữ đủ bài học hai bên, patch502 và thêm503, APPVER503. Không xung đột hàm nghiệp vụ.
Bản gộp local3092/0, precheckrc0, bundle8e73877bf04f5f2d1b987fea2a7a37cb6a096f7be8113c7bc1b69ca3476122ce. Cần bench SHA tích hợp mới trước merge.
