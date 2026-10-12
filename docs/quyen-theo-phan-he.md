# Quyền theo phân hệ (anh Việt chốt đủ 8 điểm, 06/10/2026)

Số liệu site thật 06/10/2026: 37 tài khoản, chỉ 7 người được gán gói, 30 người gán quyền lẻ. Làm trên màn Quản lý người dùng sẵn có (`vagabond/nguoi_dung.py`), không dựng cơ chế mới.

**Nguyên tắc:** mỗi người nhận gói theo bộ phận, kiêm việc thì nhận nhiều gói, quyền CỘNG DỒN (từ v582). Không gán quyền lẻ.

## Bảng 1. Các gói

| Gói | Ai | Làm được | Không làm được |
|---|---|---|---|
| Bếp | 13 người bếp | Lệnh sản xuất, đặt hàng nội bộ, kiểm kê | Tiền, công nợ, giá vốn |
| Quản lý sản xuất | Thịnh | Bếp + duyệt sản xuất, mua R&D | Tiền, công nợ |
| Quầy | 8 bạn quầy | Bán quầy, tạo đơn bán, nhận hàng điều chuyển, đặt hàng, kiểm kê | Công nợ, tiền ngân hàng |
| Sales | 7 bạn Sales | Đơn bán, khách hàng và bảng giá, khuyến mãi, công nợ phải thu, báo cáo | Ghi sổ phiếu thu, giá vốn |
| Quản lý cửa hàng | Dễ, Loan Anh | Quầy + Sales + ca, đơn treo, chốt kiểm kê, xuất huỷ | Ghi sổ kế toán, duyệt chi giám đốc |
| Kho | Trung Kiên | Nhập xuất kho, danh mục món, chốt kiểm kê | Tiền, công nợ |
| Thu mua | Nhã Uyên | Đơn mua, hồ sơ thanh toán, nối phiếu kho | Duyệt chi, ghi sổ |
| Marketing | Minh Vũ | Việc Marketing, đặt hàng, kiểm kê | Tiền, công nợ |
| Kế toán | Dung, Khải | Mọi màn kế toán + TOÀN QUYỀN kho và sản xuất | Quản trị hệ thống |
| Quản lý người dùng | Dễ (kiêm) | Mời tài khoản, xếp gói, bật tắt | Cấp quyền quản trị |
| Giám đốc | Thành Sơn | TOÀN QUYỀN nghiệp vụ mọi gói + duyệt chi cấp cuối + quản lý người dùng | Cấu hình hệ thống |
| Chủ công ty | anh Việt | Toàn quyền | |

## Bảng 2. Anh Việt đã chốt

| # | Câu hỏi | Chốt |
|---|---|---|
| 1 | Quầy tạo đơn bán | Cho tất cả quầy |
| 2 | Sales sửa bảng giá, khách hàng | Giữ |
| 3 | Khuyến mãi | Cho tất cả Sales và Quản lý cửa hàng |
| 4 | Dễ: duyệt chi giám đốc, quản lý người dùng | Bỏ duyệt chi, giữ quản lý người dùng |
| 5 | Khải và Dung | Chung gói Kế toán |
| 6 | Quyền thừa của Dung | Bỏ |
| 7 | Kế toán với chứng từ kho và sản xuất | Toàn quyền chỉnh sửa |
| 8 | Giám đốc | Mở toàn quyền nghiệp vụ |

## Trình tự áp dụng

1. v582: sửa nội dung gói theo Bảng 1, cho một người giữ nhiều gói (cộng dồn). Xong.
2. Sau deploy: thử từng gói bằng tài khoản thử, rồi mới xếp gói cho người thật theo cột "Ai".
3. Việc hôm nay của Giám đốc vẫn lọc gọn theo yêu cầu 31/08 của anh. Đó là lọc danh sách việc, không phải quyền.
