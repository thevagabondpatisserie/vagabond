# Issue #470 / PR #471

Owner: Codex. Nhánh `codex/470-web-vue`, main `42cb9fb9a9310c2c7a03d9e2f19e26dd17dd0375`.
GĐ1 Claude đã PASS; GĐ2 đang làm, giữ Draft. Không merge/deploy.

## Code lượt GĐ2

Commit code `1a914c0fc` (đọc SHA đầy đủ ở PR).
- Biên nhận Vue, ba chính sách Vue theo nội dung công khai; SSR SEO/OG/noindex.
- Khóa cả lời hứa gửi đơn; chống địa chỉ cũ trả muộn; lỗi tải tồn có thử lại.
- Route `/web_moi` song song và kiểm whitelist; chưa đụng live route/Editor.
- APPVER593 và patch593 giữ nguyên từ GĐ1.

## Bằng chứng

Framework4451/0, CI giả chặn requests4451/0, bundle khớp, fullgate exit0.
Kho Node28/0; Chromium9nhóm/0 qua `cong_cu/kiem_web_vue_dom.cjs`, không dùng
hồ sơ Chrome cá nhân, chỉ fixture localhost. DOM là lệnh riêng, chưa nối vào CI.
Đột biến3hàng rào (nhấp kép, địa chỉ cũ, token Pixel): mỗi lượt27đạt/1hỏng.
Không tạo đơn thật, không gọi Meta. Hai ca PDF thiếu pypdf bỏ, không tính đạt.

## Còn lại

Chưa chốt GĐ2. Xem từng ô còn thiếu trong
[35 tính năng](../../web-vue/470-doi-chieu-tinh-nang.md), không suy9nhóm DOM
là mọi nhánh đã nghiệm thu. F21 đã đo cửa tạo đơn trong code và đăng PR:
nhận yêu cầu bánh thường, hết hạn mức mùa vụ chặn, lỗi kiểm mùa vụ vẫn nhận.
Đã hỏi anh Việt về đổi chính sách; chưa có câu trả lời, chưa đổi backend tồn.
Còn một số nhánh DOM (gallery/sửa dòng/storage lỗi/qua nửa đêm/phản hồi muộn),
đối chiếu production/bench và ảnh. GĐ3/GĐ4 chưa làm.
Claude review delta code mới; Codex tiếp tục bổ sung kiểm theo bảng, giữ một PR.
