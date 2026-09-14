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
   snapshot item/bot-comment/release giữ30ngày. Sau30ngày im lặng có thể báo lại một
   snapshot trạng thái ở lần chạm đầu. Nếu tệp vượt1MB, đọc blob cùng SHA.
   Khởi tạo dở: kiểm ref và tệp; không xoá mốc đang dùng để “sửa nhanh”.
5. Đặt Actions variable `TELEGRAM_ENABLED=true`, dispatch `doi-soat`. Đăng
   comment thử được anh cho phép, kiểm run và tin nhận thật rồi mới báo đã bật.
   Tắt bằng `TELEGRAM_ENABLED=false`.

Không dùng ciphertext artifact từ PR khác. Không tự đổi chat đang hoạt động;
muốn ghép lại phải xác nhận đúng người qua mã mới và đọc lại secret metadata.

## Đối chiếu tin chưa rõ kết quả

Dấu `pending` được ghi bền trước sendMessage. Theo duyệt Issue287 ngày14/09,
thông báo được phép gửi lại đúng một lần sau10phút với nhãn `(gửi lại)`;
đây là tin thông báo, tuyệt đối không áp dụng cách này cho chứng từ/HĐĐT.

- Đồng hồ lấy `ghi_luc` (giờ ghi dấu), không lấy `at` (giờ sự kiện). Pending
  cũ thiếu đồng hồ bắt đầu đếm từ lần nâng cấp đầu, không giả nhận đã đủ hạn.
- Sau Telegram OK: log chỉ mã tin/message_id/kênh, lưu receipt vào pending,
  rồi ghi seen. PUT mất phản hồi đọc lại: cùng nội dung coi thành công; cùng
  SHA mới thử PUT lại một lần; SHA khác dừng, không ghi đè trạng thái khác.
- Pending có receipt: chỉ đóng dấu, không gửi lại. Chưa có receipt và đủ
  10phút: đọc lại nguồn để gửi có nhãn. Nguồn không còn: kênh riêng dùng tin ngắn chỉ rõ mất phản hồi; nhóm
  chuyển thẳng sang can_doi_chieu, không gửi câu kỹ thuật thay features; không lưu nội dung tin trong nhánh trạng thái.
- Lần gửi lại cũng mất phản hồi: sau10phút chuyển vết sang `can_doi_chieu`,
  không gửi lần ba, nhường kênh cho tin mới. Đây KHÔNG phải bằng chứng đã gửi;
  người vận hành đối chiếu mã trong Actions và chat. Không tự xóa vết này.
- Receipt giữ30ngày, không chứa token/chat ID/nội dung tin. Lỗi HTTP nêu nguồn
  GitHub hoặc Telegram, không in URL hay response body.

Việc mở kẹt legacy ngày14/09 đã được anh Việt giao theo comment5654964136:
chỉ gỡ pending c4636da5a05da85d73c053d2, giữ cursor/seen. Run34772786863 gửi30tin.
Không reset cả mốc để xử lý một tin mất phản hồi.

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
vẫn dùng pending trước HTTP và theo đúng chính sách ở mục "Đối chiếu tin chưa
rõ kết quả": mất phản hồi thì gửi lại đúng một lần sau 10 phút với nhãn
`(gửi lại)`, lần hai vẫn mất phản hồi thì chuyển sang `can_doi_chieu` và
không gửi lần ba. Vì vậy một bản tin có thể xuất hiện tối đa hai lần trong
chat, lần sau có nhãn; người vận hành đối chiếu chứ không nhận là đã gửi.
Nhánh trạng
thái chỉ chứa SHA/hash/mốc, không lưu nội dung tính năng. Snapshot giữ30ngày;
đăng lại một bản rất cũ sau thời hạn đó có thể báo lại.


Đối chiếu API12/09: owner.type của repo là User; biên nhận deploy do Codex
local đăng có user.login=thevagabondpatisserie và author_association=OWNER.
Kết nối này đăng bản tin trực tiếp, không bắt anh Việt dán lại. Phiên bot
không có danh nghĩa đó phải bàn giao khối cho phiên phát hành đang kết nối
chủ repo. Nếu có khối sai/schema/người đăng không hợp lệ, tin metadata báo
rõ chưa gửi tóm tắt, không in nội dung bị từ chối. Khoảng trắng đầu/cuối nhãn
được bỏ qua như nhánh metadata. Bản tin chỉ lấy từ comment chung của Issue/PR,
không lấy khối trong góp ý trên dòng code.


## Nhóm bộ phận chỉ nhận bản tin tính năng

Secret tùy chọn `TELEGRAM_CHAT_ID_BO_PHAN`. Trống thì chỉ gửi riêng như cũ.
Chỉ khối release hợp lệ của chủ repo gửi cả hai kênh. Nhóm chỉ nhận tiêu đề,
ngày và features, không SHA/link GitHub/tin review/CI. Trạng thái nhóm nằm
trong `bo_phan` của cùngstate, có cursor/seen/entities/pending/receipt riêng;
không lưu chat ID trong git. Lỗi một kênh vẫn thử kênh còn lại. Khi ghép mới,
nhóm bắt đầu từ mốc kích hoạt, không phát hàng loạt bản tin lịch sử.

### Anh Việt làm trên Telegram

1. Tạo nhóm “Vagabond cập nhật ERP”, thêm trưởng bộ phận và VagabondERPBot,
   cho bot quyền gửi tin. Báo Codex khi nhóm đã sẵn sàng; không gửi token.
2. Codex cấp mã một lần `VGB-LINK-` kèm chuỗi ngẫu nhiên. Chính tài khoản
   Telegram đã ghép riêng của anh gửi nguyên mã trong nhóm, không forward.
   Nếu bot bật privacy mode, trả lời một tin của bot bằng mã để bot đọc được.
3. Codex chạy workflow `telegram-ghep.yml`, chọn `loai_chat=bo-phan`, mã mới,
   public key và key ID repository. Không đổi quyền workflow hoặc webhook.
   Script chỉ nhận group/supergroup âm, đúng mã trong24giờ, đúng người gửi
   là chủ private chat đã ghép; hai nhóm khớp thì dừng.
4. Artifact `chat-encrypted.json` chỉ ciphertext. Kiểm đúng run/SHA/loại ghép,
   PUT ciphertext vào secret `TELEGRAM_CHAT_ID_BO_PHAN` bằng key ID tương ứng.
   Không đưa chat ID/token ra log, không đặt đè secret private.
5. Chạy đối soát để tạo mốc nhóm, rồi bản tin release được duyệt kế tiếp.
   Kiểm receipt từng kênh trước khi nói nhóm đã nhận. Tin ghép thử không chứng
   minh bản tin release thật đã chạy. Chưa có nhóm thì code sẵn, chưa bật nhóm.

## Phương án cần duyệt phải đọc được ngay trên Telegram

Theo anh Việt 14/09/2026, không bắt anh mở GitHub để tìm phương án. Chủ repo
soạn riêng khối sau trong comment có dòng đầu `[CẦN DUYỆT]`:

```text
<!-- telegram-approval
{"van_de":"Việc đang vướng","de_xuat":"Phương án đề xuất","anh_huong":"Ảnh hưởng cần biết","cau_hoi":"Anh duyệt phương án này nhé?"}
-->
```

Bot chỉ gửi khối hợp lệ do OWNER là chủ repo đăng, mỗi ô tối đa 500 ký tự;
không sao chép phần log/comment bên ngoài. Nội dung này chỉ tới kênh riêng
của anh. Kèm link nguồn và nhắc trả lời trong Codex: bot Telegram hiện chưa
nhận lệnh duyệt. Codex tự ghi quyết định của anh lên PR, không hỏi lại.
Khối sai định dạng chỉ nhận thông báo metadata như trước, không tự đoán.
