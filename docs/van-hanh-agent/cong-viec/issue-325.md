# Issue 325 - SePay thủ công

Owner: Codex. Nhánh codex/sepay-325, nền 13bda1b9dceb4924546047029ad294c30892b4bd.

Anh Việt duyệt mở PR: chỉ tài khoản có mapping SePay đang hoạt động; bỏ hoàn toàn danh sách chưa nối. Mapping quyết định phạm vi, không suy từ trường party hoặc tài khoản 141.

Đã sửa API ung_vien lọc tài khoản trước limit 500; mapping rỗng trả rỗng. Giữ nhãn lịch sử cho các caller khác. Chip ngắn, title tên ngân hàng đầy đủ, padding và chiều cao 44px. APPVER/patch 496, bundle sinh bằng công cụ.

Kiểm: ca Python mapping/disabled/lọc query và caller; ca Node gọi hàm màn thật với 0/1/60 dòng. Cổng predeploy chạy local. Chưa có bench CI trên SHA cuối, chưa đo số tài khoản live, chưa ảnh site thật 390x844 sau sửa, chưa đột biến. PR Draft để Claude review; chưa merge/deploy.

## Vòng sửa 327 sau review

Anh Việt đã duyệt merge/deploy khi đủ cổng, và xác nhận lại trực tiếp: chỉ hiện tài khoản có SePay. Không nhận đề xuất d của Claude về hiển thị dòng chưa nối bị làm mờ. Không coi comment của reviewer là quyền đổi phạm vi.

F1: mapping rỗng có thông báo riêng, chỉ đường Cài đặt SePay. F2: giữ nguyên chuỗi nhãn đầy đủ cho dict lịch sử, chỉ chip rút gọn. Bổ sung đọc lại mapping active ở cửa khop_tay trước set_value; ứng viên cũ hoặc gọi API ngoài mapping không ghi/commit. Ca kiểm gọi cửa ghi với mapping rỗng, khác tài khoản và hợp lệ.

Local predeploy sau sửa: exit0, 3046 ca Python. Đột biến và CI trên SHA cuối ghi ở comment PR. Kết nối CUA Mac timeout hai lần trong lượt này, chưa kiểm live 390x844 và chưa thao tác deploy. Quyền deploy đã có; thiếu cổng kỹ thuật không phải thiếu duyệt.
