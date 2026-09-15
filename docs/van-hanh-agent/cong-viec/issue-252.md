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
