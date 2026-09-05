# Vagabond Control Tower

Lớp điều phối cho Claude, Codex và người duyệt. Mục tiêu là không sửa chồng,
không deploy thiếu kiểm tra và không để quyết định nhạy cảm nằm trong chat.

## Nguồn sự thật

1. GitHub Issue có owner, branch, phạm vi tệp và trạng thái `In progress` là
   lock giữa các máy và agent.
2. Pull Request là nơi review, CI và quyết định merge.
3. `state/locks.json` chỉ là bản kiểm tra cục bộ trong cùng một checkout,
   không thay GitHub Issue.
4. `state/releases.md` chỉ ghi deploy đã kiểm tra site thật.

## Quy trình một việc

1. Tạo Issue theo mẫu.
2. Claim Issue: đặt `status:in-progress`, `agent:claude` hoặc `agent:codex`,
   ghi owner, branch, phạm vi tệp và hạn xử lý.
3. Chạy preflight rồi mới sửa.
4. Agent implementer chỉ sửa phạm vi đã claim. Agent còn lại review, test hoặc
   phân tích, không sửa chồng.
5. Ghi handoff, tạo PR, chạy CI và review chéo.
6. Chỉ người trực tiếp phụ trách theo `AGENTS.md` được deploy. Agent không tự
   merge, deploy hay sửa dữ liệu ERP cũ.

## Lệnh

```sh
python3 vgb-control-tower/scripts/vgb_control.py preflight --repo .
python3 vgb-control-tower/scripts/vgb_control.py claim \
  --repo . --task VGB-123 --owner claude \
  --branch vgb-123-ten-viec --scope vagabond/duong_dan.py
python3 vgb-control-tower/scripts/vgb_control.py list-locks --repo .
python3 vgb-control-tower/scripts/vgb_control.py release-lock \
  --repo . --task VGB-123 --owner claude
```

`claim` là kiểm tra cục bộ bổ sung. Trước khi chạy, phải cập nhật GitHub Issue
vì lock trong Issue mới được agent ở checkout khác nhìn thấy.

## Cổng an toàn

- Không có Issue hoặc claim: không code.
- Preflight lỗi, working tree bẩn hoặc local thiếu `origin/main`: dừng.
- Có xung đột phạm vi: dừng, mô tả xung đột, không tự chọn bên giữ lại.
- Thiếu test, CI đỏ hoặc review: không merge.
- HĐĐT, dữ liệu cũ, Chart of Accounts, Server Script: cần xác nhận nghiệp vụ.

## Cài GitHub

Đưa `templates/github-issue-form.yml` vào
`.github/ISSUE_TEMPLATE/vagabond-engineering.yml`, rồi tạo labels:

`status:triage`, `status:in-progress`, `agent:claude`, `agent:codex`,
`needs-business-approval`, `release:ready`.

Đọc `prompts/claude.md` và `prompts/codex.md` khi khởi tạo agent. Có thể chép
nội dung tương ứng vào cấu hình Claude và `AGENTS.md` của Codex.
