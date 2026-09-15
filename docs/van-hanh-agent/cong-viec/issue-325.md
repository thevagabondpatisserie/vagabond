# Issue 325 - SePay thủ công

Owner: Codex. Nhánh codex/sepay-325, nền 13bda1b9dceb4924546047029ad294c30892b4bd.

Anh Việt duyệt mở PR: chỉ tài khoản có mapping SePay đang hoạt động; bỏ hoàn toàn danh sách chưa nối. Mapping quyết định phạm vi, không suy từ trường party hoặc tài khoản 141.

Đã sửa API ung_vien lọc tài khoản trước limit 500; mapping rỗng trả rỗng. Giữ nhãn lịch sử cho các caller khác. Chip ngắn, title tên ngân hàng đầy đủ, padding và chiều cao 44px. APPVER/patch 496, bundle sinh bằng công cụ.

Kiểm: ca Python mapping/disabled/lọc query và caller; ca Node gọi hàm màn thật với 0/1/60 dòng. Cổng predeploy chạy local. Chưa có bench CI trên SHA cuối, chưa đo số tài khoản live, chưa ảnh site thật 390x844 sau sửa, chưa đột biến. PR Draft để Claude review; chưa merge/deploy.
