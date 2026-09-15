# Issue 252: nối phiếu nhập, lượt 15/09/2026

Owner Codex, branch codex/pnk-3019-con-lai, base 2b3484e898a5ed9f3fce6617b72bb57739ded4ea.

## Phạm vi

Phân biệt tiền gốc phiếu nhập với phần còn được nối sau hóa đơn khác đã ghi
sổ. Nhãn tiền gốc tại danh sách, bảng giải thích dùng cùng nguồn lượng của
so_sanh; chỉ đường cho kế toán kiểm đầu nối. Giữ nguyên hàng rào lượng.

## Bằng chứng và giới hạn

Cổng local 3030/3030 và patch 27/27 đạt. Thêm khẳng định tiền gốc trong ca
so_sanh có nhiều dòng cùng món và hóa đơn khác đã dùng lượng; thêm ca render
hướng dẫn và escape tên chứng từ. CI/review theo SHA cuối trên PR.

Có trường hợp chứng từ cũ cần kế toán xác nhận đơn vị và đầu nối với nguồn.
Không đưa dữ liệu riêng tư vào đây; không sửa dữ liệu production và không
nhận deploy bản hiển thị là đã giải quyết chứng từ đang kẹt.

## Bước tiếp

Claude review delta, CI/bench trên SHA PR. Codex chờ xác nhận nguồn chứng từ
trong phiên người dùng trước khi đề xuất xử lý dữ liệu đã ghi sổ.

## Sửa review inline sau 0c57543

Claude chốt 0c57543 và bench34930695223 thành công. Review inline4012083523
chỉ ra tiền còn lại còn gồm món thừa/khác đơn vị, không được gọi toàn bộ là
nối được. Đổi nhãn thành Tiền hàng còn lại trên các phiếu và giải thích giới
hạn; bổ sung khẳng định render, giữ nowrap cho tiền gốc theo nit Claude.
Chờ CI/review delta mới; không đổi thuật toán hoặc chứng từ.

## Mở rộng theo yêu cầu ngăn tái diễn

Đã chứng minh code dong_bo_luc_luu thoát khi tổng khớp, không kiểm lượng.
Chưa chứng minh lịch sử thao tác nào gây ca thật. Thêm before_submit kiểm
lượng hàng tồn theo nguồn điện tử và quy đổi NCC, cộng dòng tách cùng tên;
không đoán khi mất tên/nguồn hoặc nhiều mã cùng tên. Chưa tự sửa dữ liệu.
Có ca Document.submit thật yêu cầu đúng thông báo và DB nháp/GL rỗng.
Cần bench, review và đánh giá mức chặn dữ liệu cũ trước merge. Chưa có công
cụ rà toàn hệ thống hoặc sửa đầu nối lịch sử; phần này chưa hoàn tất.

## Review c948fe57

Bench c948fe57 xanh, Claude yêu cầu sửa mất món nguồn và lượng nguồn bị
chuẩn hóa thành1 khi thiếu giá. Đã lặp hợp tên hai phía, loại nguồn có dòng
không quản kho hiện hữu; đọc sluong nguyên gốc, không dùng bộ chuẩn hóa tiền.
Thêm ca thuần và Document.submit mất món. Còn audit nháp trên site, thiếu
quy cách lịch sử và review/bench SHA mới; chưa đủ merge.

## Audit dữ liệu nháp và nhận diện tên cũ

Rà chỉ đọc trên production tìm được dòng cũ giữ tên Item nội bộ thay vì
ten_hang_ncc; phép kiểm tên tuyệt đối có thể chặn oan. Đã thêm fallback chỉ
khi thiếu ten_hang_ncc và mapping NCC xác định duy nhất tên nguồn cho mã
Item trên chính hóa đơn nguồn. Không dùng vị trí, qty/rate hay tổng để đoán.
Có hồi quy giữ chặn lượng và không ghi đè tên nguồn đã khai. Cần audit lại
bằng resolver cuối và bench/review trước merge; số đếm sơ bộ không phải
kết quả chạy toàn bộ guard. Không nhận tất cả nháp đều sai.

## PR321 - chỉ cảnh báo theo chốt anh Việt 15/09/2026

Chỉ dẫn mới thay thiết kế chặn lượng ở các commit trước: kiểm lượng nguồn
không chặn lưu/ghi sổ, kể cả thiếu nguồn hoặc lỗi đọc. Hiện cảnh báo có
đường mở Purchase Invoice để sửa tay theo quyền và vòng đời chứng từ hiện có.
Không tự thay qty/rate/đầu nối hoặc bỏ kiểm lõi ERP. Ca tích hợp được đổi
sang Document.submit thành công, docstatus1 và có GL dù lượng nguồn lệch.
Cảnh báo phiếu nhập còn lại ẩn khi đã khớp. Cần bench và Claude review
trên SHA mới; không dùng cổng xanh của thiết kế chặn cũ để chốt bản này.

PR321 review e6a16cdd: dùng get_url_to_form của Frappe cho đường sửa tay, escape thuộc tính href. Bench e6a16cdd đã xanh; bản sửa URL phải kiểm lại. Cảnh báo popup có giới hạn với submit nền/hàng loạt, chưa có cảnh báo lưu trên chứng từ. Không coi popup là bằng chứng mọi nhân viên đã đọc.
