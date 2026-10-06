# Quyền theo phân hệ (anh Việt đã chốt 6/8 điểm, 06/10/2026)

Số liệu site thật 06/10/2026: 37 tài khoản, chỉ 7 người được gán gói, 30 người gán quyền lẻ. Hệ đã có màn Quản lý người dùng với các gói chức vụ (`vagabond/nguoi_dung.py`), nên làm trên màn đó, không dựng cơ chế mới.

**Nguyên tắc:** mỗi người nhận gói theo bộ phận, kiêm việc thì nhận 2 gói và quyền được CỘNG DỒN. Không gán quyền lẻ.

## Bảng 1. Chín gói

| Gói | Ai | Làm được | Không làm được |
|---|---|---|---|
| 1. Bếp | 13 người bếp | Lệnh sản xuất, đặt hàng nội bộ, kiểm kê | Tiền, công nợ, giá vốn |
| 2. Quản lý sản xuất | Thịnh | Gói 1 + duyệt sản xuất, mua R&D | Tiền, công nợ |
| 3. Quầy | 8 bạn quầy | Bán quầy, tạo đơn bán, nhận hàng điều chuyển, đặt hàng, kiểm kê | Công nợ, tiền ngân hàng |
| 4. Sales | 7 bạn Sales | Đơn bán, khách hàng và bảng giá, khuyến mãi, công nợ phải thu (gom phiếu, khớp tay theo giao dịch, đính UNC), báo cáo bán | Ghi sổ phiếu thu, giá vốn |
| 5. Quản lý cửa hàng | Dễ, Loan Anh | Gói 3 + 4 + ca, đơn treo; Dễ giữ quyền quản lý người dùng | Ghi sổ kế toán, duyệt chi cấp giám đốc |
| 6. Kho | Trung Kiên | Nhập xuất kho, danh mục món | Tiền, công nợ |
| 7. Thu mua | Nhã Uyên | Đơn mua, hồ sơ thanh toán, nối phiếu kho | Duyệt chi, ghi sổ |
| 8. Kế toán | Dung, Khải (chung gói) | Mọi màn kế toán: ghi sổ, phiếu thu chi, công nợ thu và trả, giá vốn, xem mọi tệp đính kèm | Quản trị hệ thống |
| 9. Giám đốc | Thành Sơn | Duyệt chi cấp cuối, xem mọi báo cáo, công nợ, doanh số, giá vốn | Sửa chứng từ |
| Chủ công ty | anh Việt | Toàn quyền | |

Minh Vũ giữ gói Marketing như hiện tại.

## Bảng 2. Anh Việt đã chốt

| # | Câu hỏi | Chốt |
|---|---|---|
| 1 | Quầy tạo đơn bán | Cho tất cả quầy |
| 2 | Sales sửa bảng giá, khách hàng | Giữ |
| 3 | Khuyến mãi | Cho tất cả Sales và Quản lý cửa hàng |
| 4 | Dễ: duyệt chi cấp giám đốc, quản lý người dùng | Bỏ duyệt chi, giữ quản lý người dùng |
| 5 | Khải và Dung | Chung gói Kế toán |
| 6 | Quyền thừa của Dung (quản lý cửa hàng, khuyến mãi, mua R&D) | Bỏ |

## Bảng 3. Còn 2 điểm (từ góp ý Codex)

| # | Câu hỏi | Đề xuất |
|---|---|---|
| 7 | Kế toán cần mở chứng từ kho và sản xuất (từ màn giá vốn, màn kho). Cho CHỈ XEM, hay cho cả chốt kiểm kê và duyệt xuất huỷ (Dung đang có)? | Chỉ xem, chốt kiểm kê để Quản lý cửa hàng và Kho |
| 8 | Giám đốc: hệ thống đang rào chỉ duyệt và xem, không sửa. Giữ rào hay mở toàn quyền? | Giữ rào như Bảng 1 |

## Việc kỹ thuật (không cần anh chốt)

1. Màn gán gói hiện tại gán gói thứ hai sẽ XOÁ quyền của gói đầu. Sửa để cộng dồn trước khi áp cho người kiêm việc (Codex).
2. Sửa nội dung các gói trên màn Quản lý người dùng cho khớp Bảng 1, thêm gói Quầy và Quản lý cửa hàng.
3. Thử từng gói bằng tài khoản thử, rồi mới gán cho người thật.
4. App: nút bị khoá thì báo "cần gói X".
