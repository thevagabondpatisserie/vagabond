# Issue 613: Dòng chọn và nút không vỡ chữ

- Nguồn: https://github.com/thevagabondpatisserie/vagabond/issues/613, ảnh và yêu cầu anh Việt ngày 23/11/2026.
- Owner Codex, nhánh `codex/ui-dong-chon-khong-vo-chu`.
- Base `4cbc52607f378312297ddbbf4cfa3f614490e663`, code đã kiểm `ceac3a35334347854ec8d3c9d0892f31a219bc4b`.
- APPVER 688, một dòng patch. Đã đọc main và mọi remote ref: main 685, hai PR mở 611/612 dùng 686/687.

## Kết quả

Nội dung dài ép nút vì flex không xuống hàng và word-break:break-all ở cả dòng. Đã gom 7 kiểu ô cài đặt vào cùng khuôn, giữ nguyên markup cũ khi tắt UI mới. Tiêu đề Chọn cả mục và thẻ Hộp thư đối soát dùng lại CSS xuống hàng. Không đổi API, quyền, tiền, kho, dữ liệu site hoặc nội dung gửi đi.

- [Báo cáo, ảnh và lệnh kiểm](../../ui-nghe-si/sua-dong-chon-613.md).
- 36/36 lượt CSS thật đạt; 36 PNG chế độ cũ so byte giống baseline; 41/41 ca DOM ở mỗi chế độ.
- 3/3 đột biến bị chặn. Máy chụp khung chung: 102 đạt, 0 trượt, 12 chưa chuyển trên 114 ô của fixture repo, không phải toàn bộ app.
- Python 3.12 local: khung 6660/6660; giả lập CI không requests 6660/6660; `dung_app_bep.py --kiem` khớp; `kiem_truoc_deploy.sh` mã 0; `chot_chan.py` không lỗi; kiểm khai báo UI 178 luật, không trượt.
- Lượt Python hệ thống 3.9 đầu tiên không hợp ca AST v631 và cache mặc định bị chặn; không sửa nghiệp vụ để né ca. Dùng Python 3.12 và cache /tmp chạy đủ cổng. GitHub CI dùng Python 3.11, cần xác nhận riêng sau push.
- Tự rà H8: loại 9 (vùng bấm, CSS), 8 (giữ tên nhập dở khi chọn tin), 4 (đóng/mở/chọn lại), 15 (dữ liệu giả); không có đường mới ghi dữ liệu, kế toán hay kho.

## Bàn giao

Commit sau code chỉ thêm bản bàn giao này. Đọc SHA cuối và CI từ PR, không lấy trạng thái local làm bằng chứng CI/bench hay deploy.

Còn lại: review độc lập trên đúng SHA cuối, CI/bench trên GitHub; kiểm Safari và iPhone/Android thật sau khi được phép phát hành. Không tự bật UI cho tài khoản nào. UI07 chỉ khép phần trạng thái tràn thẻ, dải tiến độ chữ nhỏ vẫn thuộc PR đổi màn. Các lỗi điều hướng và số liệu của lượt tester trước không nằm trong bản này.

Claude rà phần khuôn flex, bấm trong vùng chọn, khả năng ngắt mã dài và ảnh tắt UI. Không merge, không deploy khi chưa có lệnh riêng của anh Việt. Thời gian/token provider: unavailable.
