# Quy tắc tiết kiệm token - 14/09/2026

Anh Việt yêu cầu tiếp thu cách phối hợp gọn giữa Codex và Claude. Áp dụng
local, Cowork và cloud; ưu tiên hơn lời dặn cũ về đọc lại toàn bộ hoặc tag
mọi comment. Codex vẫn code/tích hợp/phát hành, Claude review độc lập.

## Đọc và kiểm đúng phần cần thiết

- Mỗi SHA chỉ có một đầu mối review độc lập là Claude bot trên GitHub.
  Cowork đọc kết luận để quyết định, không review lại cùng diff. Codex vẫn
  tái hiện finding, sửa và kiểm phần mình chịu trách nhiệm; thiếu bằng chứng
  hay phát hiện rủi ro mới thì mở lại đúng phần đó, không tin mù kết luận.
- Lưu mốc PR, head SHA, base SHA, phạm vi review, kết luận, link CI/bench,
  finding còn mở, owner và bước tiếp vào một bản bàn giao ngắn. Khi anh hỏi
  lại mà không có sự kiện mới, trả lời từ mốc này và ghi rõ mốc đã biết;
  không mở lại code, PR, checks từ đầu.
- Khi cần trạng thái hiện tại, lấy một lượt GitHub API gọn cho head/base,
  merged/merge_commit_sha, checks và comment mới sau mốc đã đọc. Fetch một
  lần nếu cần đồng bộ code. git fetch không chứng minh PR đã merge qua
  squash/rebase, không cho biết CI hoặc review; không suy đoán các trạng thái.
- Dùng GitHub API/CLI cho đọc và đăng comment. Browser chỉ khi API thiếu
  quyền/chức năng hoặc cần kiểm UI thật. Không chụp màn hình PR để đọc chữ.
- Review delta từ SHA đã review đến SHA mới; ghi cả base khi đổi nền. Không
  đọc lại nguyên repo. Tệp hướng dẫn đã đọc, không đổi thì chỉ dùng lại;
  tra mục lục/từ khóa, không nạp cả nhật ký hoặc toàn bộ log.

## Chờ và giới hạn việc trùng

- Không tự tạo lịch polling/review định kỳ để chờ người khác sửa. Chỉ tiếp
  nhận yêu cầu của anh hoặc sự kiện có hành động qua cơ chế đã được thiết lập.
  Telegram là thông báo, không tự chứng minh đã đánh thức một phiên Codex.
- Trong một việc đang được giao, vẫn theo dõi CI/deploy tới kết quả: ưu tiên
  chờ sự kiện, nếu không có thì polling có backoff, chỉ đọc job/bước đang chờ.
  Không đọc lại review hoặc toàn bộ checks mỗi lượt; không đăng tin trạng
  thái không đổi. Không bỏ dở deploy chỉ để tránh một lần kiểm cần thiết.
- Không tự sửa/tắt các automation đã được anh giao cho việc khác. Quy tắc
  này cấm tạo thêm vòng chờ vô ích; thay lịch hiện có cần đúng phạm vi yêu cầu.
- Một owner mỗi phạm vi, không gọi agent thứ hai khi người đầu đang làm.
  Gom các finding đã biết vào một lượt sửa, kiểm local rồi mới push; không
  push mỗi sửa nhỏ làm khởi động lại cả bench. Finding mới quan trọng vẫn sửa.

## Một sự kiện, một comment, gọi đúng bot

Không còn luật mọi comment phải tag đối ứng. Một comment gộp đủ việc và bằng
chứng trên đúng PR; issue chỉ dẫn tới đầu mối đó khi cần. Không đăng thêm
comment xác nhận/cảm ơn, không lặp lại cùng yêu cầu khi chưa có delta.

Mẫu yêu cầu review (thay các dấu ngoặc bằng giá trị thật):

```text
@claude review delta <FULL_HEAD_SHA>
PR: #<N>; đã review: <FULL_PREVIOUS_SHA>; base: <FULL_BASE_SHA>.
Phạm vi: <tệp/chức năng thay đổi và finding cần đóng>.
Đã kiểm: <kết quả + link>; còn thiếu: <nếu có>.
Codex giữ owner sửa; chỉ review, không code/merge/deploy.
Nếu có finding cần sửa: tag @codex với ID, bằng chứng, tệp và ca hồi quy.
Nếu đạt: chốt SHA, không tag lại, không mở lượt mới.
```

Review lần đầu dùng `@claude review <FULL_HEAD_SHA>` và ghi rõ chưa có mốc
review trước. Muốn giao sửa phải dùng yêu cầu sửa rõ ràng, không chỉ viết
`review`; kèm PR, SHA, ID finding, phạm vi tệp và ca kiểm. Tin kết quả/status
không cần bên kia làm gì thì không mention bot.

Một SHA/phạm vi không gọi review lặp khi đã đạt. Cùng finding không có thêm
bằng chứng sau ba vòng trong 24 giờ thì dừng và báo anh phân xử. Không trả
lời qua lại khi chỉ còn xác nhận. Luật đếm này là lời dặn, không phải khóa máy.

## Giữ cổng chất lượng, giảm báo cáo thừa

- Không chạy lại test đã đạt trên cùng code/môi trường chỉ vì có câu hỏi
  trạng thái. Tái dùng bằng chứng gắn SHA; chạy lại khi code, nền, môi trường
  liên quan đổi, có lỗi mới hoặc cổng phát hành bắt buộc cần xác minh.
- Sát merge/push/deploy phải xác minh head/base và bản đích còn đúng. Sau
  deploy kiểm migrate và đường live liên quan một lần; CI không thay live.
- Chỉ đổi Markdown: kiểm diff, link và mâu thuẫn hướng dẫn; không tự dựng
  bench/local test tài chính. Workflow CI hiện hành vẫn có thể tự chạy;
  tài liệu này không sửa bộ lọc workflow, timeout hay trần lượt chạy.
- Báo anh 3-5 dòng: kết quả, bằng chứng chính, phần còn thiếu, bước tiếp.
  Không kể mọi lần fetch/poll. Lưu kết luận và link nguồn, không chép transcript.

## Giới hạn hiện tại

Đây là quy tắc vận hành, không bảo đảm cắt cứng chi phí. Workflow claude.yml
hiện kích hoạt theo chuỗi mention; max-turns chỉ giới hạn từng lượt, không
chặn số lượt gọi nhau. Không nhận đã tắt lịch hoặc sửa trigger khi chưa làm.
