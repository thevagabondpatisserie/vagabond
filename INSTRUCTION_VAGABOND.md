# Instruction chung: Codex và Claude trên GitHub

Hiệu lực 12/10/2026 theo yêu cầu trực tiếp của anh Việt. Đây là cửa vào chung
cho desktop, CLI và cloud trong repository. Các quy tắc nghiệp vụ và cổng kiểm
vẫn ở [instruction nghiệp vụ](tai_lieu/INSTRUCTION_VAGABOND.md),
[AGENTS](AGENTS.md) và [quy tắc vận hành](docs/van-hanh-agent/van-hanh-chung.md).
Mục cũ mâu thuẫn về model, rebase nhánh chung hoặc bàn giao cloud được thay
bằng tài liệu này. Chỉ dẫn trực tiếp mới nhất của anh Việt có ưu tiên cao hơn.
Không chép dữ liệu riêng, bí mật hay nhật ký toàn máy vào repository.

## 1. Phân vai và đầu việc

Codex viết code, kiểm thử, sửa qua review, tích hợp nhánh và đẩy bản sửa.
Claude chốt hướng và review độc lập. Mỗi phạm vi một owner; không sửa chồng.
Đọc comment cấp PR mới nhất và review chưa xử lý trước khi bắt đầu.
Lệnh review chỉ rà; lệnh sửa mới giao thay đổi. Không tự tạo PR trùng cho cùng
việc chỉ vì cloud không push được. Tiếp tục đúng nhánh PR đang được giao.
Quyền push không thay quyền merge/deploy, cổng kiểm hay quyền sửa dữ liệu thật.

## 2. Kiểm kết nối ngay đầu phiên

1. Đọc AGENTS, tài liệu nghiệp vụ liên quan và PR hiện tại. Ghi nhánh, owner,
   base SHA và head SHA remote. Giữ thay đổi chưa commit của phiên khác.
2. Kiểm remote đúng `thevagabondpatisserie/vagabond`, khả năng đọc GitHub và
   credential sẵn có của môi trường. Không in token/cookie vào log hoặc comment.
3. `git fetch origin`, đọc origin/main và head nhánh PR. Nếu origin thiếu,
   chỉ thêm URL khi đã xác minh repo đích từ PR; không suy fetch được là push được.
4. Khi nhánh chung cần cập nhật nền, merge main/nhánh được giao; không rebase
   lịch sử đã công bố, không force push. Xung đột logic cần đọc và giải quyết
   theo phạm vi được giao. Patch giữ lịch sử; app_bep.js luôn dựng lại từ bep/.

Không tự đổi sandbox, chính sách mạng, scope token hay nhét credential vào repo.
Instruction không cấp thêm quyền GitHub và không tự khởi chạy desktop.

## 3. Kết thúc sửa phải có bản trên GitHub

Trong phạm vi được giao, Codex chủ động làm đủ: sửa -> kiểm -> commit -> push
lên nhánh PR -> đọc lại SHA remote -> bàn giao cho Claude. Không dừng ở
commit local hoặc nút đề xuất tạo PR nếu đã có công cụ push hợp lệ.

Trước push, fetch lại cả main và nhánh đích; nếu có người đẩy mới thì tích hợp
và kiểm lại thay đổi liên quan. Push bình thường, không ghi đè nhánh người khác.
Xác minh SHA bằng `git ls-remote origin refs/heads/<nhanh>` hoặc API PR. Push
mất phản hồi thì đọc remote trước khi thử lại. Không báo đã đẩy từ log local.
Nếu được giao PR mới: push nhánh `codex/...`, mở đúng một PR và lưu link.

Kiểm local/CI/bench/review/merge/deploy/migrate/live là các trạng thái riêng.
`[ĐÃ SỬA XONG]` chỉ dùng khi bản sửa đúng phạm vi đã lên remote và kiểm bắt buộc
cho vòng sửa đã đạt; nếu bench đang chạy, ghi `[ĐÃ ĐẨY - CHỜ KIỂM]`. Không nhận
sẵn sàng deploy chỉ từ tổng ca local hoặc check workflow Claude màu xanh.

## 4. Khi cloud không có quyền push

Hoàn tất phần có thể kiểm, giữ commit và diff đầy đủ, rồi đăng `[BỊ CHẶN]` trên
PR nếu công cụ cho phép. Bàn giao một lần, có đủ:

- Repo, PR, nhánh đích, base SHA, head remote đã đọc và commit local đầy đủ.
- Link/task ID cloud, đường dẫn artifact hoặc patch đầy đủ có thể lấy lại;
  danh sách file, kết quả kiểm và lỗi push đã che bí mật.
- Phần chưa xong, owner tiếp nhận, câu rõ: “Bản sửa còn ở cloud, chưa lên GitHub”.

Nếu không đăng comment được, trả cùng gói bàn giao trong chat. Không giả nhận
đã ping Claude. Không mở nhiều task/PR để né lỗi quyền.

Khi phiên desktop đang được giao việc nhận gói này, tự lấy diff bằng công cụ
cloud hỗ trợ, so base và nhánh hiện tại, tránh áp lại cùng bản sửa; kiểm diff
và chạy cổng phù hợp rồi push đúng PR. Bản cloud có merge nhiều nhánh thì giữ
ancestry bằng merge các nhánh thật, chỉ áp phần sửa còn thiếu. Không chép lại
code theo lời tóm tắt nếu còn lấy được diff. Xác minh SHA remote rồi mới báo.
Quy trình này cần một phiên thực sự được khởi chạy; không hứa tự thức cả đêm.

## 5. Model và effort

Mặc định dự án: `gpt-6-astra`, `model_reasoning_effort = "medium"` trong
[.codex/config.toml](.codex/config.toml). Profile erp-standard cũng là medium;
profile erp-risk high giữ cho phạm vi rủi ro đã được duyệt. Không bật Fast Mode.

Runtime phải hỗ trợ và nạp cấu hình dự án. CLI có thể chọn tường minh:

```sh
codex --model gpt-6-astra -c 'model_reasoning_effort="medium"'
```

Xác minh model/effort bằng metadata phiên hoặc /status, không bằng lời nhắc.
Bot tích hợp GitHub và cloud có thể dùng cấu hình dịch vụ riêng; sửa Markdown
hoặc TOML không chứng minh chúng đã chuyển model. Nếu không chọn được model
ở môi trường đó, ghi rõ giới hạn, không tự đổi sang model khác hay nhận đã đổi.
Nguồn: [OpenAI config reference](https://developers.openai.com/codex/config-reference).

## 6. Bàn giao cho Claude và Telegram

Một comment trên đúng PR, không đẩy anh Việt thành người chuyển thông tin.
Mời review khi có delta mới và còn lượt theo quy tắc chung:

```text
[ĐÃ ĐẨY - CHỜ KIỂM]
@claude review delta <FULL_HEAD_SHA>
Base: <FULL_BASE_SHA>
Previous: <FULL_PREVIOUS_REVIEWED_SHA>
Scope: <việc đã sửa, PR gộp nếu có, phần còn thiếu>
Evidence: <kiểm đã chạy, chưa chạy, link CI/bench và xác minh remote>
Không merge, không deploy, mời Claude rà.
<!-- telegram-tomtat {"tom_tat":"Kết quả dễ hiểu","tiep_theo":"Ai làm bước gì tiếp"} -->
```

Review lần đầu dùng `@claude review <FULL_HEAD_SHA>`, bỏ Previous. Không giả
mốc đã review; không tag ở comment chỉ báo trạng thái. Findings có bằng chứng
mới thì Claude giao sửa trên PR, Codex tiếp tục vòng sửa đúng nhánh. Không tự
mở lịch polling hoặc gửi lặp cùng head/base. Telegram gửi được phải có biên
nhận riêng; comment có khối tóm tắt chưa chứng minh người dùng đã nhận tin.

Cuối phiên ghi bài học tái sử dụng vào docs/bai-hoc-su-co.md, nhật ký local
nếu có workspace. Cloud không thấy nhật ký máy Mac thì dùng PR làm bàn giao,
không tự tạo database hoặc giả nhận đã ghi trên máy.
