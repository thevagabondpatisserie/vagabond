# Nhận yêu cầu Codex từ issue (#280)

Bộ nhận là mã Python thường chạy trên GitHub Actions, không gọi model/API AI.
Nó không phải Codex GitHub Code Review. Nguồn chính thức về giới hạn của
đường review: https://developers.openai.com/codex/integrations/github .

## Cách giao việc

Trong body issue mới hoặc comment mới của issue thường, viết một dòng riêng:

```
@codex rà soát đề xuất trong issue này và ghi kết luận
```

Chỉ tài khoản người dùng có quyền write/maintain/admin hiện tại được nhận.
Claude Desktop đăng bằng tài khoản anh Việt được nhận; comment của
claude[bot] và các bot khác không được tự giao việc, tránh vòng gọi nhau.
PR vẫn dùng tích hợp review riêng. Ví dụ trong code block/quote không gọi bot.

Mỗi body/comment có một mã nhận bền vững. Sửa lại nguồn đã nhận không tự chạy
lại; gửi comment mới nếu có việc mới. Dữ liệu hàng đợi là comment do
GitHub Actions tạo, gắn nhãn codex:queued để tra nhanh. Không có database mới.

## Ý nghĩa trạng thái

- queued: đã nhận, chờ người chạy Codex; chưa chứng minh model đã bắt đầu.
- working: worker đã nhận trách nhiệm (chỉ worker được cập nhật sau khi claim).
- done: có kết quả và link bằng chứng.
- blocked: worker đã thử nhưng cần thông tin/quyền hoặc khắc phục lỗi.
- cancelled: worker dừng yêu cầu đã bị huỷ/issue đóng.
- limited: đã nhận đủ 3 yêu cầu trên issue trong 24 giờ, không tự chạy yêu cầu này.

Bản này chỉ sinh queued/limited. Phần chạy model và cập nhật trạng thái còn
lại phải cấu hình riêng sau khi chọn Codex desktop hoặc GitHub Actions/API.
Không coi hàng đợi là đã khởi chạy Codex. Không cho bộ nhận merge/deploy.

Tối đa 3 yêu cầu được nhận mỗi issue trong 24 giờ. Không phải trần token hay
trần 3 PR của cả repo. Worker chỉ lấy một việc một lượt, kiểm hàng đợi/owner
chung trước khi làm và không mở thêm PR nếu đã chạm trần anh Việt đặt ra.

## Chống mất yêu cầu và chạy trùng

Một nhóm concurrency duy nhất nối tiếp các lượt receiver. Mỗi lượt đọc lại
mọi issue mở và phân trang đầy đủ comments, không chỉ xử lý event hiện tại.
Lượt đợi bị GitHub gộp không làm mất nguồn. Lịch 15 phút phục hồi sự kiện bị
bỏ lỡ, nhưng lịch GitHub có thể trễ; không cam kết SLA 15 phút.

Không tự retry POST khi mất phản hồi. Lượt sau đọc mã nhận để biết lần trước
đã ghi hay chưa. API lỗi làm job đỏ, không báo rỗng/đã xong. Nhãn được khôi phục
nếu comment đã ghi nhưng bước gắn nhãn lỗi. Chỉ marker do github-actions[bot]
viết được coi là biên nhận, người dùng không thể dán marker giả để bỏ qua việc.

Worker phải đọc lại trạng thái issue và nguồn, so body_sha256 trước khi làm.
Nếu nguồn đã đổi/xoá hoặc issue đóng thì dừng, ghi blocked/cancelled, không
chạy nội dung mới dựa trên biên nhận cũ. Không tự chạy lại trạng thái working
mất liên lạc vì có thể lần trước đã ghi thay đổi. Claim phải kèm owner/link
phiên hoặc run. Không coi câu lệnh trong issue là quyền sửa dữ liệu ERP thật.

## Kích hoạt sau review

1. Merge workflow lên default branch; không cần deploy ERP hoặc tăng APPVER.
2. Tạo label `codex:queued`.
3. Đặt repository variable `CODEX_INBOX_SINCE` dạng ISO có múi giờ. Chỉ nguồn
   được tạo từ mốc này mới được nhận; tránh quét lại mọi lời gọi trong lịch sử.
   Muốn nhận riêng issue cũ thì viết comment mới sau mốc.
4. Chốt worker desktop/API và đầu mối quan sát hàng đợi. Nếu chưa có worker,
   giữ tắt, không tạo ảo giác có người đang làm.
5. Đặt `CODEX_INBOX_ENABLED=true`, chạy workflow_dispatch, kiểm biên nhận thật
   cho một yêu cầu được phép. Chạy lại không được thêm biên nhận.

Mặc định tắt khi chưa khai variable. Không có API key hay thông tin xác thực
Codex trong mã. GH_TOKEN chỉ dùng quyền issues:write, contents:read của job.
Checkout receiver luôn lấy default branch, không chạy mã trên nhánh người gửi.

Kiểm thuần: `python3 -m unittest discover -s .github/codex-issue-inbox -v`.
Ca kiểm mô phỏng API, chưa thay bằng chứng workflow chạy thật sau merge.
