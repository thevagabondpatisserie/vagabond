# Codex: model và bài học dùng chung

Tiếp nối PR #278: Claude đọc bài học trong repo, Codex cũng phải đọc và bổ sung
cùng một nguồn. `AGENTS.md` là cửa vào của Codex; không dựa vào việc Codex tự
nạp `CLAUDE.md`.

## Model anh Việt chọn

Mặc định trong `.codex/config.toml`:

```toml
model = "gpt-6-astra"
model_reasoning_effort = "low"
```

Anh Việt gọi mức này là Light. Giá trị kỹ thuật dùng ở đây là `low`.
Không tự đổi sang model khác, tăng effort hoặc bật Fast Mode để chữa lỗi.
Nếu model không khả dụng, báo lỗi truy cập và phạm vi bị chặn.

Cấu hình dự án chỉ được nạp khi runtime hỗ trợ và repo được tin cậy. Tham số
khởi chạy hoặc lựa chọn model tường minh có thể ghi đè mặc định này. Phiên đang
chạy không tự đổi model chỉ vì commit thêm tệp. Khi bắt đầu việc, kiểm metadata
phiên hoặc `/status` trên CLI để xác nhận model và effort thực tế. Kiểm Fast
Mode ở cấu hình hiệu lực; tệp này không xoá thiết lập Fast từ lớp khác.

Bot `@codex review` do tích hợp GitHub quản lý riêng. Chưa có bằng chứng bot
này dùng `.codex/config.toml` để chọn model; không báo nó đang dùng Astra chỉ
vì tệp đã có trong git. Nếu sau này chạy Codex CLI qua workflow riêng, phải
kiểm model/effort thực tế ở runtime trước khi công nhận cấu hình có hiệu lực.

### Cách dùng thật và nguồn đã đối chiếu ngày 11/09/2026

Codex hiện hỗ trợ tự nạp `.codex/config.toml` trong repo đã tin cậy. Mở CLI
ở checkout này rồi dùng `/status` để kiểm model/effort. Có thể chọn tường minh:

```sh
codex --model gpt-6-astra -c 'model_reasoning_effort="low"'
```

Không đổi `CODEX_HOME` sang repo: biến này đổi cả nơi lưu trạng thái của Codex,
không cần thiết để nạp cấu hình dự án. Chưa chạy một phiên model mới để xác minh
metadata trong PR này; kiểm TOML không thay bằng chứng model thực tế.

Nguồn chính thức đã mở ngày 11/09/2026:
- https://developers.openai.com/codex/config-basic chuyển hướng tới
  https://learn.chatgpt.com/docs/config-file/config-basic, mục Configuration
  precedence ghi project config đứng sau CLI overrides, chỉ nạp repo tin cậy.
- https://developers.openai.com/codex/config-reference chuyển hướng tới
  https://learn.chatgpt.com/docs/config-file/config-reference.

## Trước và sau mỗi phiên

1. Đọc `AGENTS.md`, instruction trong repo và `docs/bai-hoc-su-co.md`.
2. Tra tài liệu nghiệp vụ bằng `rg`, kiểm main, SHA, comment và scope đang làm.
3. Sau khi tái hiện được lỗi mới, ghi bài học ngắn vào tệp chung, có Issue/PR
   nguồn; giữ bằng chứng chi tiết trên PR hoặc nhật ký local.
4. Không biến đề xuất chưa kiểm thành sự thật. Ghi riêng code, kiểm local,
   CI, bench, review, merge, deploy, migrate và kiểm site thật.

## Phối hợp review

Codex làm chính, Claude review. Chỉ mời lại khi có sửa đổi hoặc bằng chứng mới
cần rà; không tag vì cảm ơn, xác nhận hoặc vì bot vừa trả lời. Dừng khi đã đạt
hoặc chỉ còn bất đồng lặp lại để anh Việt quyết định. Trước khi mời, kiểm các
lượt gần nhất trên PR và giới hạn đang được anh Việt duyệt. Đếm trong lời dặn
không phải khoá cứng trong workflow; không nhận hai cơ chế là một.

Nhật ký chi tiết của hai agent có thể ở hai môi trường khác nhau; chỉ
`docs/bai-hoc-su-co.md` là nguồn bài học chung. Theo quy tắc trong `CLAUDE.md`,
Claude đếm tối đa 3 comment mời Codex review trong 24 giờ trên mỗi PR rồi dừng.
Đây là giới hạn lời dặn hiện hành; chưa chứng minh workflow có bộ đếm cứng.
