# PR401: Codex tiếp tục vòng 4

Owner: Codex, theo yêu cầu anh Việt khi Claude hết token.
PR: https://github.com/thevagabondpatisserie/vagabond/pull/401
Nền review: 70741d0664296f3b42363ede5077a21c79c51f00.

## Hành vi cuối

- Gợi ý giá theo SLE đúng kho, rồi kho khác cùng công ty tới ngày giờ phiếu.
  Bỏ cả hai giá Item không có lịch sử thời gian. Nếu chưa có SLE, kế toán
  nhập giá đã xác minh, hoặc chủ ý bật cho phép giá 0 theo core.
- Hook báo rõ dòng/món thiếu giá, trước khi core có thể lấy Item Price/Item
  hiện tại cho dòng giá trống. Giá người dùng nhập và ý định giá 0 vẫn giữ.
- API tra giá lỗi: màn riêng báo lỗi + Thử lại, không mời nhập tay hoặc
  ghi sổ. Thử lại thành công khôi phục màn thường; submit vẫn chặn lỗi.
- Fixture bench dùng tài khoản Temporary cho tồn đầu kỳ; ca định giá 0 đếm
  từ 10 xuống 9 vì core pinned bỏ qua qty không đổi + giá 0.

## Bằng chứng và giới hạn

- Ca hồi quy nguồn giá: nền cũ sai cả ba mốc (lùi ngày, cùng ngày, không ngày).
- Ca DOM mới đỏ trên nền cũ ở nút ghi sổ khi lookup lỗi; bản mới đạt cả
  đường thường và lỗi -> thử lại -> ghi sổ đúng ngày giờ vừa tra.
- Cổng local đã đạt 3773/0; sau chỉnh fixture/nhãn đang chạy lại cổng cuối.
- Bench nền cũ run36805385790: 322/325 hai lượt, ba ca đỏ đã phân tích trong
  docs/bai-hoc-su-co.md. Bench SHA cuối chưa có kết quả tại lúc commit này.
- Chưa merge/deploy/migrate/live. Không sửa phiếu thật để thử.
- Frappe bench f33ac3f00ab818e21b25ddbec93efb653fd9aa1b; ERPNext bench
  de591661b9ba0bd3f62ac25b99b5c85c723515f6. Không tuyên bố core site thật
  trùng bench khi chưa đọc được site. Chrome đang timeout.

Tiếp theo: đọc bench trên SHA chứa tài liệu này, sửa nếu đỏ; review delta
và phát hành chỉ sau đủ cổng. Không đẩy commit chỉ để cập nhật kết quả CI;
kết quả cuối ghi một comment PR cùng full SHA.

Rà cuối phát hiện can_dien nhận cả giá âm: sửa chỉ nhận trống/0, giữ giá âm
để core từ chối. Ca insert thật chứng minh không đổi tồn/không để nháp dở.
