# Issue342 - tiến trình phiếu và dấu duyệt

Owner: Codex local, branch codex/app-tam-ung-tien-trinh.
Base: 2c2942a7d616637ae75457999e06bc01ea0a20f6.

## Đã sửa
- Cùng renderer tiến trình trong khuôn danh sách, dùng cho APP, TTNB và phiếu hoàn tiền. Nhãn bước đọc được trên màn hình, có mô tả accessibility.
- APP hiển thị dấu FIN/GD từ dữ liệu, không suy chữ ký từ trạng thái; phiếu hủy/từ chối không vẽ xanh. Phiếu trả trước dùng luồng khác nên chưa gán các bước APP.
- Lập và gửi ngay dùng cùng cách ghi dấu FIN như gửi hồ sơ nháp. Không ghi bổ sung chữ ký lịch sử, không thay quyền hay số tiền.

## Kiểm
- Ca API tạo hoàn ứng thật với Frappe giả: FIN gửi ngay, người thường gửi, FIN lưu nháp. Khôi phục hành vi cũ làm ca đỏ đúng hai khẳng định dấu/ngày FIN.
- Thêm ca bench insert/reload ở cửa tạo gửi ngay, chờ CI.
- Node57 ca đạt. Kiểm local đầy đủ ghi trên PR theo SHA.

## Chưa hoàn tất
- Cơ chế liên kết khoản cấp trước/đã nộp và quyết toán chưa triển khai trong PR này; không gỡ chốt bằng một số tiền nhập tay.
- Chờ đối chiếu nguồn chứng từ tại site trước chọn cách ghi nhận/khôi phục. Chi tiết dữ liệu chỉ lưu nội bộ, không đăng repo.
- Chưa tăng APPVER/patch để phát hành; chốt số khi hoàn tất phạm vi/tích hợp.
- Chưa review Claude, chưa bench cuối, chưa UAT390px, không merge/deploy.
