# #262 - Cấn trừ phí sàn theo chứng từ

Theo hướng anh Việt và chị Dung duyệt 10/09/2026:
131 cuối kỳ = đầu kỳ + gross MTT - tiền nhận - phí gồm VAT đã bù.
Không ép số dư về 0. Dư Nợ cần đối chiếu Merchant và chuyển kỳ; dư Có hoặc
lệch nhỏ cần truy chứng từ. Dấu số dư không tự chứng minh nguyên nhân.

## Cách dùng bản PR

1. Kế toán mở **Vagabond Can Tru San** trong Desk, chọn công ty, sàn, điểm
   bán, Customer đang giữ 131 và Supplier xuất phí. Đính bảng đối soát, mã kỳ.
2. Chọn PI phí (có thể còn nháp) và SI MTT; khai phần phí thực sự đã bị sàn
   giữ, gồm VAT, và phần bù vào từng SI. Tổng hai bảng phải bằng nhau.
3. Accounts Manager/System Manager xác nhận đúng pháp nhân và duyệt phiếu.
4. Nếu đủ chứng từ, máy tạo JE Nợ 331/Có 131 ngay. Nếu PI chưa ghi sổ hoặc
   SI chưa có số MTT thì giữ Chờ đối soát. Khi PI/SI ghi sổ/cập nhật số MTT,
   máy tự thử lại. Hàng đợi mỗi giờ kiểm thêm nguồn cập nhật trực tiếp DB. Nút Kiểm lại đối soát dùng khi căn cứ đã được bổ sung.
5. Hủy phiếu đối soát để đảo JE và hồi công nợ. Không hủy riêng nguồn hoặc
   JE khi phiếu còn hiệu lực; giữ toàn bộ vết, không xóa phiếu.

Một phiếu giữ một Supplier/MST; Grab và GrabVN lập riêng, không tự ghép tên.
Việc xác nhận đối soát là căn cứ cho bù chéo pháp nhân, không mặc định rằng
mọi hóa đơn quảng cáo đều bị Grab giữ. Chưa có đối soát thì không tự bù.

## Máy chủ

Khóa bản ghi đối soát và hóa đơn trước đọc outstanding; số tiền không vượt
còn nợ; cùng NCC/số/ngày PI trùng thì chờ kiểm. Mỗi căn cứ có khóa duy nhất,
retry trả cùng JE. Insert/submit lỗi nổi ra để giao dịch rollback. Core pin
ERPNext de591661b9ba0bd3f62ac25b99b5c85c723515f6, JournalEntry.validate_reference_doc
và validate_invoices yêu cầu đúng party/account, đã submit và đủ outstanding.
Không ghi GL hoặc Payment Ledger bằng SQL, không tạo/đổi tài khoản.

## Báo cáo và giới hạn cần nghiệm thu

Nút Xem công nợ sàn đọc GL gắn với SI theo sàn/điểm bán, tách đầu kỳ, doanh
thu, Payment Entry nhận tiền, phí đã bù và điều chỉnh khác. Khoản tiền chưa
phân bổ vào SI không suy điểm bán; phải đối chiếu riêng. JE thu tiền khác
được xếp điều chỉnh để không báo là tiền ngân hàng đã khớp khi chưa có căn cứ.

PR cung cấp luồng Desk và hooks tự động; chưa có nhập tự động báo cáo Merchant,
chưa tự đọc tệp/OCR và chưa có màn /bep riêng. Không thay mã 131 của bill cũ:
phải xác minh Customer/tài khoản sàn đang được sử dụng trước phát hành.

Kiểm trước merge: GL/Payment Ledger/outstanding/hủy và retry trên bench đúng
SHA; quyền kế toán/thu ngân; chạy đồng thời; lỗi giữa insert và submit; kỳ
chuyển tháng và ngân hàng chưa phân bổ; mapping từng sàn và pháp nhân thật.
Không dùng tài liệu này làm bằng chứng đã deploy hoặc đã sửa công nợ cũ.

## Sửa theo review PR265

Hook ghi sổ hóa đơn chỉ đăng ký việc sau commit. Redis lỗi ở callback
được ghi log và scheduler thử lại, không báo bill đã lưu thành thất bại.
Worker khóa từng phiếu, dùng savepoint và bỏ callback thuộc phần đã lùi;
lỗi sau JE submit phải lùi cả JE/GL/công nợ rồi ghi Cần kiểm tra. Lỗi DB
đi ra worker để core rollback/retry. Kế toán vẫn có nút Thử lại.

Thứ tự tích hợp là PR264 rồi PR265. Nhánh PR265 nhận bản sửa combo của
PR264, giữ đủ patch471/472 và dựng lại bundle từ nguồn. Không merge main,
không deploy trong phiên này.

## Tích hợp theo issue280 ngày 11/09/2026

Anh Việt giao Codex tích hợp tuần tự và giữ deploy chung. PR265 đã chứa
toàn bộ HEAD PR264 (71cf0d95d16f25a5e1b083af1e37447820f6dc30), nên chỉ
merge265 rồi đóng264 theo thay thế, không merge264 riêng. Đồng bộ main
ad397a7f9bcd31437ea3bd35a6bb1b1cdd5010ac sau274/279, chuẩn bịv477.
Giữ trọn lịch sử patch main và thêm477; các đăng ký ca combo/cấn trừ và
APP/tham chiếu tiền đều được giữ. Bundle dựng từ nguồn.
Cổng trên SHA cũ không thay kiểm bản tích hợp. Concurrency/quyền/mapping
thật và UAT vẫn cần kết luận riêng trước phát hành; chưa deploy.

## Review F1-F5 trên a6d9c7a

Báo cáo ánh xạ mã quầy qua cùng danh mục điểm bán như cửa cấn trừ.
Trạng thái ghi bằng Document.db_set; on_submit đọc lại Document để phản hồi
Desk mang đúng bút toán/trạng thái, hủy đọc liên kết bút toán từ DB.
Scheduler chỉ tự chạy phiếu đang chờ; Cần kiểm tra dành cho xử lý thủ công.
Ba whitelist được đăng ký vào bộ canh cửa ngõ.

Core Frappe f33ac3f: database.py đổi deadlock/timeout thành QueryDeadlockError
và QueryTimeoutError, nhưng background_jobs.execute_job chỉ retry tự động
InternalError hoặc RetryBackgroundJobError. Worker chuyển hai lỗi khóa
sang RetryBackgroundJobError, giữ cause và không rollback savepoint đã mất.
Ca exception giả lập chưa chứng minh cạnh tranh hai kết nối DB.
Job chạy dưới người enqueue, owner JE không tự đồng nghĩa người duyệt.
