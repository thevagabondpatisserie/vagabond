# PR334 - phát hành quyền soạn công thức

Bản gộp v501 gồm PR336 v500. Giữ các dòng patch lịch sử v498, v499, v500 và v501.

## Gán quyền sau migrate

Đo chỉ đọc trên production ngày 16/09/2026: người dùng quầy bar đang có hồ sơ
`VGB - Nhân viên đặt hàng`, chưa có vai `Quầy Bar`. Chỉ deploy chưa hoàn tất.

Frappe 16.27.1 `User.populate_role_profile_roles` dựng lại quyền từ tất cả
`role_profiles`, nên append vai trực tiếp sẽ bị mất khi lưu User. Sau migrate:

1. Tạo hồ sơ bổ sung `VGB - Quầy Bar`, chỉ chứa vai `Quầy Bar`.
2. Gắn hồ sơ bổ sung cho đúng tài khoản Nguyễn Hữu Tài đã đối chiếu trên site;
   giữ toàn bộ hồ sơ hiện có. Không thêm vai vào hồ sơ Nhân viên đặt hàng chung.
3. Lưu lại người dùng lần hai, kiểm vai vẫn còn và không xuất hiện Manufacturing
   Manager hoặc System Manager. Kiểm màn công thức thấy nút soạn, không có Ghi sổ.

Không đưa email hoặc ánh xạ nhân sự riêng của production vào mã nguồn.
Ca bench `cong_thuc_334` gọi tạo/sửa/bỏ BOM thật bằng hai vai, xác nhận không ghi sổ.
