# Bàn giao: Telegram, phiên cloud, đẩy code

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 738 tới 780. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Báo việc cần anh Việt xem qua Telegram

Theo Issue #287 và [hướng dẫn Telegram](/docs/thong-bao-telegram.md), khi cần
anh duyệt, bị chặn, sẵn sàng phát hành hoặc đã kiểm deploy thật, đăng comment
ngắn trên đúng Issue/PR với dòng đầu tương ứng `[CẦN DUYỆT]`, `[BỊ CHẶN]`,
`[ĐÃ SỬA XONG]`, `[SẴN SÀNG DEPLOY]`, `[ĐÃ DEPLOY]`. Kèm việc cụ thể, bằng chứng/SHA và link
nơi duyệt. Không tag agent chỉ để báo tin. Không coi Telegram là native
approval; nếu không đăng được comment thì báo trực tiếp và ghi rõ giới hạn.
Chỉ báo kênh đang hoạt động sau khi đã xác minh bật và gửi thật; lời dặn này
không tự bật hệ thống hoặc chứng minh anh đã nhận tin.

Mọi comment bàn giao sửa xong, review đạt hoặc không đạt, bị chặn hay cần duyệt
phải có nhãn ở dòng đầu và đúng một khối `telegram-tomtat` theo
`docs/thong-bao-telegram.md`. Viết tóm tắt tiếng Việt theo nghiệp vụ, không tên
hàm hoặc tệp, tối đa hai câu. Comment không cần anh đọc thì không gắn nhãn.


Sau mỗi đợt deploy đã kiểm site thật, tự soạn 1-5 ý tính năng bằng tiếng Việt
và thêm khối `telegram-release` theo docs/thong-bao-telegram.md vào biên nhận
`[ĐÃ DEPLOY]`, dùng SHA thực tế đã lên site. Đây là nội dung dành riêng cho
Telegram của anh Việt, không chép log/chứng từ; cùng đợt chỉ một bản tin,
không gọi model trong sender. Quyền này không phải quyền gửi email nhân viên.
Biên nhận `[ĐÃ DEPLOY]` viết theo docs/mau-tin-phat-hanh.md: mỗi bộ phận một
khối Trước đây / Từ nay / Bạn cần làm, phần Đã kiểm trên site thật ghi tên
màn và con số, phần Còn tồn ghi thật; không tên hàm, tệp, trường, nhánh.

Khối chỉ được gửi khi comment do tài khoản chủ repo đăng với association
OWNER. Codex local dùng kết nối GitHub của chủ repo đã được xác minh, có thể
đăng trực tiếp trong quyền đã giao. Phiên chạy bằng tài khoản bot chỉ soạn
khối và chuyển cho phiên phát hành có kết nối phù hợp; không nhận là đã gửi.
Sau đăng phải kiểm dấu release trong trạng thái sender hoặc phản hồi gửi,
không coi comment được tạo là tin Telegram đã tới.

## Bàn giao bền cho phiên cloud

Đọc [mục lục công việc](/docs/van-hanh-agent/README.md) trước khi làm; tìm
đúng issue và chỉ đọc tài liệu liên quan. Sau lượt có thay đổi thực chất,
cập nhật một bản bàn giao ngắn cho issue trong PR hiện tại, kèm SHA code,
bằng chứng, finding còn lại và bước tiếp. Theo mẫu và quy tắc dung lượng
trong mục lục; không đưa transcript/log/secret vào git. Repo là nguồn bàn
giao chung với Claude, không thay trạng thái GitHub hoặc nhật ký local.

Theo yêu cầu anh Việt 14/09/2026: mỗi PR vừa đủ cổng deploy phải chủ động đăng `[SẴN SÀNG DEPLOY]` trên PR để báo Telegram, kể cả đang gom đợt. Áp dụng điều kiện, chống lặp và xác minh gửi trong docs/thong-bao-telegram.md; không chờ cả đợt mới báo.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 330 tới 346. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Bàn giao chung với Codex trên cloud

Đọc docs/van-hanh-agent/README.md và bản issue liên quan trước khi nhận việc.
Khi kết thúc lượt có thay đổi thực chất, dùng cùng mẫu bàn giao và cùng tệp
issue, không lập kho nhật ký Claude riêng. Reviewer không sửa chồng nhánh
Codex đang claim: ghi bổ sung trên PR để owner cập nhật bản bàn giao chung.
Không chép toàn bộ hội thoại/log vào git; xác minh trạng thái hiện tại từ
GitHub, không nhận ghi chú cũ là bằng chứng đã deploy.

## Đẩy code là một phần của hoàn thành

Anh Việt chốt 12/10/2026: làm xong bản sửa phải tự đẩy ngay lên nhánh GitHub
của PR, không chờ nhắc. Chỉ tính bàn giao khi SHA đã có trên GitHub. Codex
cloud thiếu quyền đẩy không được báo "đã xong"; comment dòng đầu `[BỊ CHẶN]`
và khối `telegram-tomtat` phải ghi đúng "bản sửa nằm ở cloud, chưa lên
GitHub". Codex local thấy bản cloud chưa đẩy thì tự gom nguyên diff, kiểm và
đẩy lên nhánh PR, không chờ anh Việt.
