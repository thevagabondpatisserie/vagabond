# Luồng cloud của Vagabond

Anh Việt chọn cloud ngày12/09/2026, Issue294. Không dùng lịch desktop để
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

Codex dùng Astra low theo cấu hình dự án, không Fast Mode. Cloud integration
có thể không nạp cấu hình model repo: phải kiểm metadata thực, không tự nhận
model đúng vì file đã ghi. Claude giữ cấu hình đã được anh chọn riêng.

## Hiện trạng và cổng bật

PR281 có receiver nhưng chưa có worker; biến inbox vẫn chưa bật tại lúc rà.
Internet cloud đã được lưu theo nhật ký, chưa thay bằng kiểm fetch/push mới.
Lịch local cũ PAUSED và chứa các PR đã hoàn tất, không resume lịch đó.

Chỉ bật sau khi xác định cơ chế cloud được tài khoản hỗ trợ và thử một việc
nhỏ độc lập: nhận đúng yêu cầu -> link task -> commit trên đúng nhánh -> CI
-> Claude review -> nhận/sửa finding. Thử trùng không tạo thêm tác vụ; lỗi
khởi chạy báo blocked và không retry vô hạn. Báo qua Telegram bằng marker
trên issue/PR theo docs/thong-bao-telegram.md, không dùng bot làm nơi duyệt.
