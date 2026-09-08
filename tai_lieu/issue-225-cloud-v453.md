# Cửa xử lý PKT trên Frappe Cloud, v453

v452 đã deploy, chỉ thiếu đường chạy công cụ. PR này không tự sửa PKT lúc
migrate. Chọn API có quyền + nút Desk để kế toán đọc bản xem hiện tại rồi
xác nhận đúng hash, không cần console Python hoặc patch tự duyệt bản xem.

Sales Invoice HDB-26-09-00710 có nút Sửa PKT hàng tặng, chỉ hiện khi còn
trỏ PKT-2026-00012 và người dùng có Accounts Manager/System Manager.
Nút xem đúng một PKT năm dòng đã chốt rồi gọi POST; không nhận mã phiếu
hoặc số tiền từ client. Backend kiểm vai trò trước gọi lõi, lõi vẫn kiểm
quyền từng chứng từ/hash/GL/PLE và rollback. Frontend chỉ báo xanh khi
response và Link/công nợ sau reload khớp. HTTP request của Frappe commit
khi thành công; không còn bước phải chạy commit trong console.

Hai cửa đăng ký thu_cua_ngo:
- vagabond.cong_cu_tang_cu.xem: đọc bản xem, Manager/System Manager.
- vagabond.cong_cu_tang_cu.thay: POST với ma_xac_nhan, cùng quyền.

Không cấp quyền cho Accounts User/Guest, không mở hàm lõi hay lựa chọn
chứng từ tùy ý. Hash cũ lỗi thì xem lại; retry sau đã sửa dừng không sinh
bù. Không sửa HĐĐT12165 hoặc tự gửi lại, không sửa4 tờ khác.

Fixture: thêm131/5111/6428 trong nen_bench có khóa bench thử; cấp cost
center cho SI fixture và factoryGL. Không tạo tài khoản trên site thật.

Claude trước merge: gate/CI đúng SHA, bench4ca #225 trên nền sạch; kiểm
HTTP GET vào thay bị405, Accounts User/Guest bị chặn, hash cũ không ghi.
Sau deploy/migrate453: mở đúngHDB bằng Manager, xem5 dòng và thực hiện;
đọc lại PKT cũ cancel, PKT mới5 dòng, SI vẫndocstatus1/HĐĐT12165, Link
hai chiều, Unreconcile giữ nguyên, outstanding0, GL chỉVAT64182/33311.
Nếu thực hiện lỗi thì báo nguyên lỗi, không đổi quyền hoặc bỏ kiểm.

Làm tròn/thuế từng dòng là phần riêng còn mở: ba bộ tính hiện khác nhau,
không lấy việc có nút thayPKT làm bằng chứng SI/GL/payload đã khớp. Codex
đang rà theo exactcore de59166; không đổi currency_precision toàn hệ.
