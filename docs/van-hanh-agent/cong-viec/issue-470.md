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
Anh Việt đã chốt cách B ngày 13/10; phần F21 bên dưới thay trạng thái chờ này.
Còn một số nhánh DOM (gallery/sửa dòng/storage lỗi/qua nửa đêm/phản hồi muộn),
đối chiếu production/bench và ảnh. GĐ3/GĐ4 chưa làm.
Claude review delta code mới; Codex tiếp tục bổ sung kiểm theo bảng, giữ một PR.


## F21 cách B - 13/10/2026

Owner Codex; delta từ `f820a19dce0a61123dbb9bf8ba12af9dcad59507`.
Đã đọc API site thật và ghi phạm vi **trước khi sửa** tại
https://github.com/thevagabondpatisserie/vagabond/pull/471#issuecomment-6144541606.
Ngày đọc 13/10: CANDLE/Epi12 mỗi món1, Roman16 còn2; Dư decor cho14-16/10.
Món không có dòng nguồn hoặc ngày từ17/10 trở đi không bị chặn bằng tồn này.

- `tao_don`: nonce trước tồn; đọc KB đúng hôm nay hoặc Dư decor trừ đã đặt
  trong ba ngày kế tiếp. Dòng0 có kiểm, thiếu dòng không suy thành0.
- Lỗi đọc vẫn nhận; ghi Error Log và gửi đúng webhook_don_web của Sales.
  Lỗi gửi cảnh báo cũng không chặn đơn. Mùa vụ lỗi bên trong có callback cảnh báo.
- Trang cũ/Vue giữ giỏ, nonce; hiện tên/số còn; nạp tồn và gợi ý giảm/đổi ngày/Sales.
- 8 ca backend tập trung đạt; kho Vue29/29; DOM10 nhóm đạt (gồm hai trang F21).
  Fullgate exit0, framework4459/0, bundle khớp. CI giả thiếu requests cũng4459/0.
- `python3 cong_cu/kiem_f21_dot_bien.py`: nền backend8/0, Vue29/0;
  bốn biến thể đều đỏ: bỏ tồn, hỏi tồn trước nonce, xóa giỏ, bỏ tải lại tồn.
- Đã nối hai ca Document thật vào cổng bench; kết quả SHA cuối cập nhật trên PR.
  Local không được nhận là bench thật hoặc thử đơn trên production.
- APPVER593, một patch593. Giữ Draft, không merge/deploy. Claude review delta.

Giới hạn: kiểm theo nguồn vận hành tại thời điểm gửi, không thêm cơ chế giữ
chỗ nguyên tử giữa nhiều khách; chưa nghiệm thu production. F21 không đồng nghĩa
đóng toàn bộ GĐ2/GĐ3/GĐ4 của PR471.

## Vòng review F21 13/10

Chỉ sửa F21 trên nền3f2ad0b70. Loại dòng decor0 khỏi nguồn; giữ kiểm hết/thiếu của decor dương. Thêm ca cửa tạo đơn decor0, decor2 đã đặt2, decor2 đã đặt1 xin2, mỗi ca cả ba ngày. Đồng hồ23:30/00:30 Sài Gòn dùng hom_nay thật; thiếu ngày nhận không báo Sales. Bỏ dấu gạch dài trong nội dung F21. Không đổi phiên bản/patch hoặc phần Vue khác. Cổng và SHA xem biên nhận PR.
