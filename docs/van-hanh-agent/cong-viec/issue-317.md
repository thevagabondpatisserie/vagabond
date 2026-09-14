# Issue317: thanh toán nội bộ và YCPS

Owner Codex local, Claude review. Nhánh codex/317-thanh-toan-noi-bo từ main6886899d. Anh Việt yêu cầu làm và chờ deploy chung, không deploy riêng. Không sửa dữ liệu production. Bản đầu v493, để v492 cho316; xác nhận lại số ở bước tích hợp.

## Đã code
- Nhãn YCPS trong app, patch naming_series cho phiếu mới, giữ mã cũ và định danh NCC R&D.
- Ngưỡng500.000, một chứng từ/biên nhận một phiếu; cửa before_validate và gửi duyệt. Nháp cũ chỉ áp lúc gửi duyệt. Hoàn ứng kế thừa mã từ tạm ứng đã chi của cùng người, không tin cờ miễn trần từ payload.
- Danh sách có tên người lập, lọc người, tổng theo bộ lọc, quá hạn, nút tạm ứng và Excel qua Frappe make_xlsx.
- Lô theo ngân hàng+số tài khoản. Mã lô riêng, không ghi mã Bank Transaction giả. Xác nhận tạo lô, kế toán chuyển thật trên ngân hàng. Một lô một giao dịch; hai tài khoản nhận cần hai giao dịch.
- Webhook/lượt đối soát nhận lô trước phiếu lẻ, khớp tổng, ghi đủ lô mới commit; retry cùng tập phiếu giữ mã.

## Cổng và việc chưa hoàn tất
- Cổng local trên bản đầu:2988/2988, patch27/27. Có bốn ca mới thuần; không nhận là kiểm API/UI đầy đủ.
- Đã viết ca bench tạo ba phiếu/hai tài khoản, hai sao kê, kiểm trạng thái và Excel. Chưa chạy bench; phải chạy trên SHA cuối ở CI riêng. Không chạy fixture production.
- Cần bổ sung và chạy: hành vi trang TTNB, chốt schema/naming và nhãn Desk, ca old draft/API không lách cờ, lỗi ghi giữa lô, concurrency hai luồng tranh sao kê. Bộ đối soát chung hiện có nhánh hỏi chủ nuốt lỗi và luồng khác chưa dùng cùng khóa Bank Transaction; chưa chứng minh fail-closed toàn hệ, không phát hành khi chưa xử lý.
- Cần xem lại lọc/quyền File, giá trị không hữu hạn/âm, khóa sửa-hủy khi gộp đồng thời và luồng bỏ lô khi kế toán thao tác nhầm. Không tự chốt chi khi chưa có sao kê.
- Chưa merge, deploy, migrate, UAT. Draft để review cùng, không coi cổng local là đã xong issue.
