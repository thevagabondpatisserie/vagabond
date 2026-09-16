# Issue 325 - SePay thủ công

Owner: Codex. Nhánh codex/sepay-325, nền 13bda1b9dceb4924546047029ad294c30892b4bd.

Anh Việt duyệt mở PR: chỉ tài khoản có mapping SePay đang hoạt động; bỏ hoàn toàn danh sách chưa nối. Mapping quyết định phạm vi, không suy từ trường party hoặc tài khoản 141.

Đã sửa API ung_vien lọc tài khoản trước limit 500; mapping rỗng trả rỗng. Giữ nhãn lịch sử cho các caller khác. Chip ngắn, title tên ngân hàng đầy đủ, padding và chiều cao 44px. APPVER/patch 496, bundle sinh bằng công cụ.

Kiểm: ca Python mapping/disabled/lọc query và caller; ca Node gọi hàm màn thật với 0/1/60 dòng. Cổng predeploy chạy local. Chưa có bench CI trên SHA cuối, chưa đo số tài khoản live, chưa ảnh site thật 390x844 sau sửa, chưa đột biến. PR Draft để Claude review; chưa merge/deploy.

## Vòng sửa 327 sau review

Anh Việt đã duyệt merge/deploy khi đủ cổng, và xác nhận lại trực tiếp: chỉ hiện tài khoản có SePay. Không nhận đề xuất d của Claude về hiển thị dòng chưa nối bị làm mờ. Không coi comment của reviewer là quyền đổi phạm vi.

F1: mapping rỗng có thông báo riêng, chỉ đường Cài đặt SePay. F2: giữ nguyên chuỗi nhãn đầy đủ cho dict lịch sử, chỉ chip rút gọn. Bổ sung đọc lại mapping active ở cửa khop_tay trước set_value; ứng viên cũ hoặc gọi API ngoài mapping không ghi/commit. Ca kiểm gọi cửa ghi với mapping rỗng, khác tài khoản và hợp lệ.

Local predeploy sau sửa: exit0, 3046 ca Python. Đột biến và CI trên SHA cuối ghi ở comment PR. Kết nối CUA Mac timeout hai lần trong lượt này, chưa kiểm live 390x844 và chưa thao tác deploy. Quyền deploy đã có; thiếu cổng kỹ thuật không phải thiếu duyệt.

## 16/09 - F5, F6 và E1

Local sửa F5: tim_gd_ra hoàn tiền chuyển tiếp tai_khoan_sepay; htFormGdRa báo riêng cấu hình rỗng, có ca Node gọi hàm màn thật. E1: ly_do_tai_khoan_sepay dùng chung cho tự động và thủ công ngay trước ghi. Tự động đưa giao dịch không đủ mapping vào xem_lai và không set_value. Ca gọi tu_dong kiểm cả mapping hợp lệ và rỗng.

Phạm vi v496 áp cả TTNB và Hoàn tiền; cong_no có cửa riêng, không nhận là đã phủ. Không xác nhận được mapping thì không ghi, kể cả lỗi đọc Settings; thông báo mới nói chưa xác nhận được, không kết luận chắc chắn do cấu hình. Giữ quyết định anh Việt chỉ hiện tài khoản có SePay.

Local predeploy exit0,3047/3047,Node51/51. Chưa CI/bench trên vòng sửa này. GitHub read/fetch và CUA bị automatic approval review từ chối do Selected model is at capacity, đã thử lại đúng lệnh vẫn lỗi. Chưa push/review/merge/deploy, không phải thiếu quyền người dùng.

## Chốt mới trực tiếp của anh Việt

Anh đã đổi quyết định: hiện tài khoản chưa nối và yêu cầu merge/deploy327. Thay các chốt mapping-only ở trên: chip chỉ mapped; cửa đọc hiển thị dòng chưa nối với dung_duoc=0/vi_sao_khong, xếp cuối. Cả TTNB/Hoàn tiền ghi lý do và bấm không gọi khớp. Cửa ghi tự động/thủ công vẫn kiểm cùng mapping. CUA tiếp tục timeout, chưa UI thật/deploy.
