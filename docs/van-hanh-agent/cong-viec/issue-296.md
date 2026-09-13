# Issue 296: lưu đơn, duyệt hàng tặng, chốt ca và thư NCC

- Nguồn: [Issue 296](https://github.com/thevagabondpatisserie/vagabond/issues/296), [PR 298](https://github.com/thevagabondpatisserie/vagabond/pull/298), [PR 299](https://github.com/thevagabondpatisserie/vagabond/pull/299).
- Owner Codex local, nhánh codex/296-luu-duyet. Anh Việt giao sửa, merge/deploy sau cổng; Claude review. Anh bỏ tính năng xuất ngay riêng khách MST, yêu cầu đủ To/CC các email NCC đã khai. Không gửi lại thư cũ hoặc sửa hóa đơn thật.
- Ngày 13/09/2026: main b1d17f31 đã gồm PR 295, 297, 299; runtime PR 298 chưa merge/deploy.

## Kết quả có bằng chứng

Lưu đơn chỉ lưu nháp qua chung điều kiện; duyệt hàng tặng giữ quyết định rồi ghi sổ trong savepoint, lỗi không mất duyệt. Phục hồi bill hủy kiểm sao kê đã bị bill thay thế nhận. Hộp mùa vụ không cho nhập sản xuất như bánh. PR 299 giữ số máy chuyển khoản/thẻ, chỉ đếm tiền mặt, không nhận số sai/NaN.

Thư NCC trước đây chỉ lấy địa chỉ đầu; nay gom Supplier.email_id/email_cc và Contact Email liên kết đúng NCC, bỏ trùng To/CC, bản sao kế toán riêng và UNC đọc thật. Khóa APP, hai queue nguyên tử, delayed=True; không SMTP trong POST. Queue chưa phải Sent. Gửi thử đúng một địa chỉ, không dấu gửi thật.

- SHA 8b57f49 tích hợp nghiệp vụ: local 2944/0, CI/bench xanh, Claude chốt comment5650286616.
- SHA 99434a87 thêm thư: bench34736267340 đỏ vì mock outgoing None thiếu always_bcc, không phải bằng chứng queue đạt.
- SHA 0d970c6: sửa F1-F5 review5650925436; local2946/0/gate rc0, Claude chốt5651020223; bench34736765830 đạt 187/188 hai lượt, sạch. Ca rollback và email sai đạt; ca gửi đủ đã qua số queue/4 địa chỉ/143 ký tự/retry, còn lệch kỳ vọng header bản sao (placeholder lõi) và dấu chấm mã APP đã đổi thành gạch trong tên tệp. Bản sau cho header To bản sao rõ và sửa kỳ vọng tên tệp đúng quy tắc.
- Code c5e09d422cff9ca72761583f8877d83cf14ffc8f thêm kiểm quyền đọc Email Queue cho link xử lý lỗi, tích hợp main cuối. Cổng trước delta tài liệu rc0. Commit bàn giao này chỉ thêm tài liệu, CI cuối đọc trực tiếp trên PR.

## Còn lại và bàn giao

Codex kiểm bench SHA cuối, đọc Claude delta quyền, Ready/merge PR 298, deploy một lần v488 (patch487 rồi488). Bắt buộc chọn site để migrate email_gui_toi từ Data sang Small Text. Kiểm Patch Log, schema, bundle và màn liên quan trên site thật. Console đã xác minh email_cc có và hộp Purchasing bật outgoing; chưa gửi thư thật, chưa chứng minh hộp nhận đã nhận.

Theo review5651020223 còn việc không chặn: bang_chung parse MIME khi mở hồ sơ có UNC lớn, cần đo/tối ưu ở lượt sau; API gọi tay retry vẫn kiểm UNC trước da_co. Không mở quyền Email Queue cho kế toán, ai thiếu quyền được hướng dẫn nhờ quản trị viên.

Review tự động3998728970 bắt giao vai bán hàng/kế toán. Ca quyền cũ stub _kiem_quyen; thay bằng hàm thật làm đỏ hai assertion trên e562c202. Sửa cửa ghi sổ chỉ yêu cầu vai kế toán, thêm bench User Accounts độc lập và Sales bị chặn. Bench e562c202 trước delta đã đạt188/188 hai lượt sạch và browser success (34737358134), cần bench mới cho delta quyền. Chưa merge/deploy PR298.

Review5651172671: trước chot_mot_don còn luu_xhd chặn Accounts. Rà cả mở màn/cấu hình/tìm đơn/đơn treo/lưu khách và đổi ngày; 8 cửa đọc/lưu dùng Sales hoặc Accounts, cửa ghi sổ chỉ Accounts, chốt OTP và ngày giữ nguyên. Ca quyền mới bắt16 assertion trên47682f49; mở rộng bench đúng chuỗi lưu phương thức -> XHD -> chốt đơn Sales, đọc GL và giữ Sales không ghi được.
