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

## Bổ sung cấn quỹ
- Nút ghi nhận tiền mặt đã cấp: kế toán chọn tiền vào, nguồn111 cùng công ty, NQ tùy chọn. JE Nợ141/Có111 và đối chiếu Bank Transaction lõi cùng giao dịch; retry trả cùng JE.
- Cấn sau duyệt bằng nguồn đã cấp còn dư, khóa quỹ chung. JE Nợ331 theo từng PI/Có141. APP giữ tổng chi, phần còn lại mới tạo PE/khớp sao kê112. Bộ kiểm chứng từ xác minh cả JE và PE.
- Bỏ cấn trả nguồn, công nợ và APP; phải xử lý khoản chi thêm trước. Không sửa dữ liệu cũ, không dùng toàn bộ số dư cá nhân để suy tiền công ty.
- Màn lập không còn ô gõ số trừ không có chứng từ. Dùng nút Cấn trên hồ sơ đã duyệt.
- APPVER506 dự kiến, main504; PR341 đang đề xuất505 nên để nguyên số đó.

## Chưa hoàn tất
- Unit3099/0, Node61/0 sau kiểm tiền âm. Bench đầu0106a49b đã xanh; ca cấp/cấn mới chưa có kết quả.
- Đã thêm ca bench lỗi sau submit JE, rollback và hai APP nối tiếp tranh một nguồn. Chưa có bằng chứng hai kết nối đồng thời; khóa Bank Account/current read giữ thứ tự. Chưa kiểm390px (browser từ chối URL preview cục bộ).
- Chưa tự review cuối, không có review Claude (user cho tự review), chưa merge/deploy.
- Đường ghi nhận cấp hiện dành nộp tiền mặt111. Khoản chuyển từ112 cần kiểm chứng từ chuyển khoản lõi và đường nhận nguồn riêng trước khi nhận là đã hỗ trợ.

- Tự review bắt thêm đường xuất chuyển khoản dùng 0-or-tổng, đã sửa và thêm hồi quy tại cửa API. Cấn đủ dùng nhãn quyết toán, không đòi UNC/sao kê mới; đổi tài khoản nhận phải bỏ cấn trước.

- Bench2ed81f0: hai lượt239/240, sạch; lỗi thật ở Bỏ cấn do truyền list cho ERPNext on_cancel nối tuple. Đã đổi tuple theo core, chờ bench SHA mới. Cấn một phần và rollback đã đạt cả hai lượt.
