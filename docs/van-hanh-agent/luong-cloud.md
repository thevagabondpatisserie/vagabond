# Luồng cloud của Vagabond

Anh Việt chọn cloud ngày 12/09/2026, Issue 294. Không dùng lịch desktop để
thay thế và không tự thêm dịch vụ API tính phí riêng khi chưa thống nhất.

## Chuỗi cần có

Yêu cầu được anh Việt giao -> claim một việc -> Codex cloud đọc tài liệu,
code và kiểm -> commit đúng nhánh/PR -> Claude review delta -> Codex nhận
finding mới, tái hiện/sửa hoặc phản biện -> đủ cổng -> báo sẵn sàng deploy.
Lượt tự động không tự deploy, migrate hoặc đổi dữ liệu production.

Mỗi bước giữ link nguồn, SHA và chủ việc. Có queued không có nghĩa working;
review không phải giao sửa; commit cục bộ không phải push thành công. Chưa
có acknowledgement thì đọc lại tác vụ/nhánh trước khi gọi lại, tránh chạy đôi.

## Giới hạn và đầu vào

Chỉ xử lý việc đã giao, một việc đang viết code mỗi lượt; tối đa ba PR đang
xử lý, không tính PR cũ ngoài phạm vi thành lý do làm lại. Không tự chọn yêu
cầu nghiệp vụ mới hoặc mở rộng quyền từ lời gọi của bot. Khi phiên khác đã
claim cùng phạm vi thì để chờ. Đọc trạng thái trên GitHub trước mỗi mutation.

Không gọi model chỉ để hỏi trạng thái không đổi. Chỉ review lại có delta
hoặc bằng chứng mới; cùng finding ba vòng không có bằng chứng mới thì dừng
và báo anh. Quy tắc này còn là lời dặn, chưa phải bộ đếm cứng. Khi chọn
worker phải có trần chạy/thời gian và chống trùng bằng event/finding + SHA.

Model và cách xác minh theo mục Model mặc định dành cho Codex trong
[AGENTS.md](../../AGENTS.md); không sao chép cấu hình thành nguồn thứ hai.

## Cổng bật

Trạng thái có mốc nằm ở [Issue 294](https://github.com/thevagabondpatisserie/vagabond/issues/294)
và [bản bàn giao](cong-viec/issue-294.md). Luồng này chỉ quy định điều kiện,
không thay bằng chứng vận hành hiện tại.

Chỉ bật sau khi xác định cơ chế cloud được tài khoản hỗ trợ và thử một việc
nhỏ độc lập: nhận đúng yêu cầu -> link task -> commit trên đúng nhánh -> CI
-> Claude review -> nhận/sửa finding. Thử trùng không tạo thêm tác vụ; lỗi
khởi chạy báo blocked và không retry vô hạn. Báo qua Telegram bằng marker
trên issue/PR theo docs/thong-bao-telegram.md, không dùng bot làm nơi duyệt.
