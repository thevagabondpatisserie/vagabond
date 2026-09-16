# Issue N: tên việc

- Nguồn: link issue, PR, yêu cầu/phạm vi đã duyệt.
- Owner, nhánh, SHA code đã kiểm, thời điểm kiểm trạng thái GitHub.
- Mục tiêu và tiêu chí nghiệm thu.

## Kết quả có bằng chứng

Triệu chứng -> nguyên nhân -> sửa ở đâu. Dẫn code, run hoặc comment gốc.
Ghi rõ ca bắt được bản cũ và kết quả bản mới khi có sửa lỗi.
Tách code/local/push/CI/bench/review/merge/deploy/migrate/live.

## Còn lại và bàn giao

Finding ID/link, đã tái hiện hay chưa, owner, bước tiếp cụ thể và ca cần chạy.
Quyền hoặc đầu vào còn thiếu; không suy ra quyền từ comment bot.
Không ghi secret, dữ liệu cá nhân, transcript hoặc log đầy đủ.

## Hợp đồng nghiệp vụ và phối hợp
- Người dùng cần làm được gì; input và kết quả mong đợi.
- Bất biến tiền/kho/quyền; dữ liệu ngoài phạm vi; cửa UI/API/worker cần kiểm.
- Claim owner, phạm vi tệp, PR phụ thuộc, trạng thái queued/working/review/blocked/ready.
- SHA head/base, run review, finding ID và ca old-fail/new-pass.
- Model/effort thực tế (hoặc chưa xác minh); số lượt, thời gian, token provider
  (hoặc unavailable), finding mở lại/lỗi production liên quan.
- Bước tiếp, người làm, quyền có sẵn/đầu vào còn thiếu.
