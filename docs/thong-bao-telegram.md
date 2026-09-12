# Telegram cho anh Việt - Issue #287

Bot: [VagabondERPBot](https://t.me/VagabondERPBot). Thông báo là mã Python
chạy trên GitHub Actions, không gọi Claude/Codex/model, không tốn token AI.
Actions vẫn sử dụng phút chạy theo gói GitHub của repository.

## Anh dùng trên điện thoại

- Mở bot, bấm Start. Gửi mã ghép một lần do Codex đưa trong tác vụ riêng.
- Token BotFather lưu ở repository Actions secret `TELEGRAM_BOT_TOKEN`.
  Phải chọn **Secrets and variables > Actions**, không phải **Agents**.
  Secret ở Agents không cấp cho workflow Actions.
  Mã ghép mới sinh12ký tự hex ngẫu nhiên;10ký tự chỉ để nhận mã cũ đã cấp.
  Không gửi token qua comment, chat Codex hoặc ảnh chụp.
- Sau khi ghép và bật thành công, tin có link tới đúng PR/comment/workflow.
  Bấm link để đọc nội dung đầy đủ hoặc duyệt đúng nơi.
- Nhắn “đồng ý” cho bot chưa thực thi lệnh nào. Bot này chỉ thông báo;
  không có cửa ghi sổ, merge, deploy hoặc phê duyệt thay anh.

## Phạm vi thông báo

Đọc comment mới/sửa (cả bot), góp ý trên dòng code, review mới gửi, trạng thái
Issue/PR và CI lỗi/timeout/cần xử lý. Merge được ghi rõ chưa chứng minh deploy.
Comment thường chỉ gửi metadata và link, không chép log/chứng từ. Riêng bản tin
phát hành được chủ repo soạn cho Telegram dùng khối bên dưới.

Sự kiện GitHub gọi lượt đối soát, cách nhau tối thiểu3phút để giảm request. Lượt định kỳ mỗi15phút bù
comment dùng GITHUB_TOKEN không kích hoạt workflow khác. GitHub có thể trì hoãn
schedule; đây không phải cam kết giao tức thì. Mỗi lượt tối đa30tin và không bắt đầu gửi mới sau5phút; phần còn
lại giữ mốc để lượt sau gửi. Nếu đọc nguồn quá5phút mà còn tin và chưa gửi
được tin nào, workflow báo lỗi thay vì xanh giả. Chùm comment liên tiếp có
thể chờ tới lượt bù15phút, và có thể chậm thêm nếu GitHub trì hoãn lịch. Không phát lại toàn bộ lịch sử trước lúc bật.

Comment bot chỉ đổi checkbox tiến độ thì im lặng; đổi nội dung thực hoặc
nhãn vẫn báo, kể cả thêm finding dưới cùng tiêu đề. Trạng thái Issue/PR chỉ
báo khi state, nhãn, draft, merged hoặc tiêu đề đổi; mở lại vẫn báo dù từng mở.

Giới hạn: theo dõi review mới gửi của PR mở và PR vừa cập nhật; sửa/dismiss
review có submitted_at cũ ngoài cửa đối soát không được báo lại. Quét lỗi workflow tạo trong7ngày hoặc từ mốc bị gián
đoạn nếu lâu hơn; chạy lại workflow rất cũ có thể nằm ngoài cửa này. API quá
1000bản ghi thì báo lỗi và giữ mốc, không âm thầm bỏ phần thừa. Lần gửi chưa rõ
kết quả dừng cả hàng đợi để đối chiếu. Khi Telegram hỏng, phải xem Actions;
không thể dùng chính kênh đang hỏng để đảm bảo báo lỗi cho anh.
Người vận hành phải kiểm workflow Telegram mỗi ngày, hoặc anh bật email
thông báo Actions thất bại trong GitHub Settings > Notifications > Actions.
PR này không tự đổi cài đặt email cá nhân của anh.

## Codex và Claude báo cần duyệt, bị chặn, phát hành

Đăng comment trên đúng Issue/PR, dòng đầu chọn đúng một trong bốn nhãn:

```
[CẦN DUYỆT]
[BỊ CHẶN]
[SẴN SÀNG DEPLOY]
[ĐÃ DEPLOY]
```

Dưới dòng đầu viết việc cụ thể, bằng chứng, SHA/link và nơi anh cần duyệt.
Bot phân loại theo dòng đầu, chỉ gửi người viết và link; nhãn là báo cáo của
người viết, không phải máy xác minh nghiệp vụ. `[ĐÃ DEPLOY]` chỉ dùng sau khi
phiên phát hành đã kiểm site thật. Chỉ xanh CI thì chưa dùng nhãn này.

Không có bằng chứng về hook đọc mọi popup native của Codex/Claude. Vì vậy
phiên gặp chặn phải đăng comment có link nếu còn quyền làm việc; nếu app đã
ngắt trước khi đăng thì kênh này không tự nhìn thấy. Cần duyệt vẫn thực hiện
ở GitHub/Codex/Claude tương ứng, không coi phản hồi Telegram là native approval.

## Kỹ thuật ghép và bật

1. Merge sau kiểm/review. Workflow gửi luôn checkout default branch, không
   checkout PR, nhánh trạng thái, artifact hay code từ workflow kích hoạt.
2. Lấy `GET /repos/thevagabondpatisserie/vagabond/actions/secrets/public-key`.
   Dispatch `telegram-ghep.yml` với public key, key_id và mã ghép riêng.
   Script kiểm username, private chat, mã chính xác trong24giờ, chặn mơ hồ.
   Nếu đã có webhook khác thì dừng, không xoá. Không xác nhận/xoá update cũ.
3. Tải artifact `telegram-chat-encrypted` của đúng run đã kiểm. Chỉ chứa
   `encrypted_value`/`key_id`; PUT nguyên ciphertext vào repository secret
   `TELEGRAM_CHAT_ID`. Không in chat ID hay token ra log. Artifact tự hết1ngày.
4. Dispatch `telegram.yml` chế độ `khoi-tao`, chỉ một lần. Tạo nhánh riêng
   `codex/telegram-state`, lưu `.telegram/state.json` gồm mốc/key sự kiện;
   không có nội dung comment, token hoặc chat ID. Nhánh đã tồn tại thì dừng.
   Dấu gửi được tỉa theo cửa nguồn: comment/item/review120giây, run7ngày;
   snapshot item/bot-comment giữ30ngày. Sau30ngày im lặng có thể báo lại một
   snapshot trạng thái ở lần chạm đầu. Nếu tệp vượt1MB, đọc blob cùng SHA.
   Khởi tạo dở: kiểm ref và tệp; không xoá mốc đang dùng để “sửa nhanh”.
5. Đặt Actions variable `TELEGRAM_ENABLED=true`, dispatch `doi-soat`. Đăng
   comment thử được anh cho phép, kiểm run và tin nhận thật rồi mới báo đã bật.
   Tắt bằng `TELEGRAM_ENABLED=false`.

Không dùng ciphertext artifact từ PR khác. Không tự đổi chat đang hoạt động;
muốn ghép lại phải xác nhận đúng người qua mã mới và đọc lại secret metadata.

## Đối chiếu tin chưa rõ kết quả

Dấu `pending` được ghi bền trước sendMessage; `seen` chỉ ghi sau phản hồi
đúng chat/message. PUT lỗi/mất mạng/worker chết không được tự gửi lại.

Người vận hành đọc code của `pending` trong nhánh trạng thái rồi hỏi anh tin
có `Mã tin` đó đã tới chưa. Nếu có: thêm `seen[pending.key]=pending.at`, xoá
pending bằng PUT có SHA hiện tại. Nếu pending có entity/signature thì cập
nhật thêm entities[pending.entity] với signature và at đó trước khi xoá. Nếu chắc chưa tới và được yêu cầu gửi lại:
chỉ xoá pending bằng PUT có SHA hiện tại rồi chạy đối soát. Nếu chưa rõ, giữ
nguyên. Không reset cả mốc, không xoá toàn bộ seen. Mọi sửa chữa ghi trên Issue.

Nguồn: [Telegram Bot API](https://core.telegram.org/bots/api),
[GitHub - sự kiện không kích hoạt tiếp khi dùng GITHUB_TOKEN](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).


## Tóm tắt tính năng sau mỗi đợt deploy

Theo yêu cầu anh Việt12/09, phiên phụ trách phát hành tự thêm khối này vào
MỘT comment `[ĐÃ DEPLOY]` sau khi đã kiểm Cloud, migrate và site thật. Viết
1-5 ý ngắn bằng ngôn ngữ nhân viên, mỗi ý tối đa220ký tự. Chỉ kể tính năng
trong bản vừa phát hành; không đưa log, dữ liệu khách, số chứng từ hoặc bí mật.

```text
[ĐÃ DEPLOY]
Bằng chứng kiểm phát hành và link có thể viết ngoài khối.
<!-- telegram-release
{"version":"v483","sha":"1e07f3d5be4308f26ff0fb72426df273067fb7fc","live_verified":true,"features":["Tìm mã hàng cũ theo mã hoặc tên.","Ghi sổ vẫn tiếp tục khi phát hành hóa đơn tạm hoãn."]}
-->
```

Bot chỉ nhận khối đúng cấu trúc trong comment của tài khoản chủ repo có
`author_association=OWNER`. Comment bot/người ngoài, thiếu xác nhận live hoặc
schema sai vẫn chỉ báo metadata, không chép nội dung. `live_verified` là
xác nhận của người phát hành; bot không tự truy cập Cloud để chứng minh.
Không phát tin tính năng chỉ vì CI xanh hoặc PR merge.

Tin gửi tự động qua kênh đã ghép cho anh Việt, dùng lịch đối soát hiện tại,
không gọi model. Cùng SHA và nội dung ở nhiều PR chỉ tạo một tin. Đổi nội dung
tính năng tạo tin đính chính; không sửa comment chỉ để phát lại. Bản tin
vẫn dùng pending trướcHTTP và không tự retry khi mất phản hồi. Nhánh trạng
thái chỉ chứa SHA/hash/mốc, không lưu nội dung tính năng. Snapshot giữ30ngày;
đăng lại một bản rất cũ sau thời hạn đó có thể báo lại.
