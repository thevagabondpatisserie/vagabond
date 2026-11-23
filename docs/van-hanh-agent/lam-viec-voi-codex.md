# Làm việc với Codex: lệnh, xác nhận, luật dừng

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 10 tới 33. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Phân công và báo review ngay (anh Việt chốt 15/10/2026)

Mục này ưu tiên mọi phân công cũ mâu thuẫn bên dưới và trong tài liệu liên kết.
Codex rà PR; anh Việt nhận kết luận rồi giao Claude sửa và làm tiếp. Codex
không tự chuyển từ review sang sửa hoặc gọi vòng review trả qua lại, trừ khi
anh Việt giao rõ. Quyền merge/deploy vẫn theo lệnh riêng và đủ cổng.

Ngay khi kết thúc mỗi vòng rà, trước khi chuyển việc hoặc kết thúc phiên:
- Đăng kết luận trên đúng PR, ghi full SHA đã rà, đạt/chưa đạt, finding còn
  lại, link bằng chứng và người cần làm tiếp. CI/bench xanh không thay review.
- Dùng `[BỊ CHẶN]` khi còn finding chặn; dùng `[CẦN DUYỆT]` khi rà đạt và cần
  anh giao bước tiếp. Không gọi review xong là `[ĐÃ SỬA XONG]`.
- Kèm đúng một khối `telegram-tomtat`: nói rõ kết luận bằng lời nghiệp vụ và
  "Anh Việt giao Claude làm tiếp" cùng việc cụ thể. Gửi ngay cả khi chưa đạt;
  không chờ Claude, bản phát hành, merge hoặc deploy mới báo.
- Kiểm workflow Telegram và biên nhận `message_id` của đúng comment. Hễ chưa
  có biên nhận cho đúng comment đó thì dispatch `telegram.yml` chế độ
  `doi-soat`, kể cả khi đã có lượt chạy xong và báo thành công: lượt đó có thể
  không thu được gì vì một lượt khác vừa đẩy con trỏ dưới 180 giây trước
  (Codex #478). Cơ chế chống trùng sẵn có lo phần gửi lặp; không gửi tay lặp
  hoặc đợi lịch 15 phút.
- Chỉ báo đã gửi khi có biên nhận. Nếu gửi lỗi, báo trực tiếp anh kèm link
  kết luận và lỗi gửi. Không coi biên nhận là anh đã đọc hoặc đã duyệt.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 92 tới 102. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Model mặc định dành cho Codex

Cấu hình mặc định dự án từ 12/10/2026: **Astra medium**,
`model = "gpt-6-astra"`, `model_reasoning_effort = "medium"`.
Đọc `docs/codex-trong-repo.md` để phân biệt cấu hình yêu cầu với runtime thật.
Không tự nhận bot GitHub đã đổi model chỉ vì sửa tệp cấu hình.



---

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 631 tới 686. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 9. Phối hợp Claude và Codex

Khi có nhiều agent, đọc `vgb-control-tower/README.md` trước khi nhận việc.
GitHub Issue đang `In progress`, có owner, branch và phạm vi tệp là nguồn
khóa chung. Không sửa vào phạm vi agent khác đã claim. Chạy preflight trước
khi sửa, bàn giao theo docs/van-hanh-agent/README.md (thay mẫu handoff
cũ), và review chéo trước khi tạo PR.

### 9b. Luật gọi bot giữa hai agent

Đối xứng cho cả hai chiều: Claude gọi Codex bằng `@codex`, Codex gọi Claude
bằng `@claude`. Cùng một bộ luật, không bên nào có ngoại lệ. Nguồn đầy đủ về
bàn giao và luật dừng là `CLAUDE.md`; mục này nêu phần đối ứng để Codex đọc
được mà không phải nạp `CLAUDE.md`. Bổ sung sau review PR #281, 12/09/2026.

**Chọn đúng loại lời gọi.** Rà soát và giao sửa là hai việc khác nhau.
`@codex review` hoặc `@claude review` CHỈ yêu cầu rà soát, không giao sửa gì.
Muốn bên kia sửa thì viết yêu cầu tác vụ rõ ràng, kèm đủ năm ô: số PR, SHA
hiện tại, link hoặc ID finding, phạm vi tệp, ca tái hiện hoặc hồi quy. Nêu
finding rồi kết bằng `review` là việc sửa không ai nhận. Đã xảy ra thật ngày
11/09/2026 trên PR #281.

**Đặt lời gọi trong comment của đúng PR chứa code cần sửa.** Finding nằm ở
issue thì dẫn link nó sang comment trên PR, không dựa vào mention trong issue
để giao việc tự động. Bộ nhận issue ở `.github/codex-issue-inbox/` là cơ chế
khác và mặc định đang tắt; biên nhận `queued` không phải là bên kia đã bắt
đầu làm.

**KHÔNG tag lại khi** comment mới nhất của bên kia chỉ là xác nhận, cảm ơn
hoặc không mang finding mới; khi đó là câu hỏi thuần thông tin của anh Việt;
hoặc khi việc đang chờ anh Việt quyết chứ không chờ kỹ thuật. Im lặng cũng là
một lựa chọn đúng.

**Xác nhận bàn giao, không chỉ gửi lệnh.** Gửi xong thì ghi link comment yêu
cầu rồi đi tìm xác nhận nhận việc, phân biệt bốn trạng thái: chưa nhận, đang
làm, bị chặn, đã có commit. Review hoàn tất không chứng minh tác vụ sửa đã
chạy hay có quyền push. Mất phản hồi cũng không chứng minh lượt trước chưa ghi
commit; đọc lại nhánh trước khi giao lại. Đang có người làm cùng finding hoặc
cùng phạm vi thì bổ sung bằng chứng vào đầu mối hiện tại, không mở tác vụ sửa
thứ hai.

**Luật dừng đếm theo từng việc.** Đếm số vòng trên CÙNG một finding hoặc cùng
một điểm bất đồng trong 24 giờ mà lượt sau không mang thêm số liệu hay bằng
chứng mới. Đủ 3 vòng như vậy thì dừng gọi và mời anh Việt phân xử. Mỗi finding
độc lập có bộ đếm riêng: ba finding khác nhau không cộng thành ba vòng, và
việc thứ tư vẫn được giao bình thường. Giữ ID hoặc link finding nhất quán để
đối chiếu, không đổi tên cùng một việc để né bộ đếm. Đây là giới hạn mềm do
agent tự đếm, không phải khoá trong workflow và không phải trần token; không
có bằng chứng workflow thì không nhận là đã chặn cứng.

**Lỗi khởi chạy không phải bất đồng kỹ thuật.** Bị chặn mạng, thiếu quyền hoặc
không dựng được môi trường thì báo đúng là lỗi khởi chạy, kèm bằng chứng còn
thiếu. Không mô tả thành hai bên bất đồng, và không tự kết luận là hết token
hay lỗi đồng bộ khi chưa đọc log.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 94 tới 186. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Bàn giao cho Codex: CHỌN ĐÚNG LỆNH, không phải lúc nào cũng review

Đây là luật quan trọng nhất của tệp này. Codex hiểu ba lệnh khác nhau, và chọn sai
lệnh là việc bị treo mà không ai biết.

| Tình huống | Lệnh phải viết |
|------------|----------------|
| Claude vừa làm xong việc của mình, muốn Codex soi lại | `@codex review` |
| Claude tìm ra lỗi và muốn Codex SỬA | `@codex fix <mô tả lỗi thật ngắn và cụ thể>` |
| Claude muốn Codex làm một việc cụ thể (rebase, đặt lại số phiên bản, chạy bench) | `@codex <việc cụ thể>` |

`@codex review` CHỈ là yêu cầu rà soát. Nó không bảo Codex sửa gì cả. Nêu một
finding rồi kết bằng `@codex review` là Codex chỉ rà soát thêm rồi trả lời, việc
sửa không ai nhận. Đã xảy ra thật ngày 11/09/2026 trên PR #281.

Muốn giao sửa, dùng yêu cầu rõ ràng như `@codex fix`; `fix` không phải từ
khoá duy nhất để giao tác vụ. Kèm PR, SHA hiện tại, link/ID finding, phạm vi tệp,
hành vi cần đạt và ca tái hiện/hồi quy. Ví dụ mẫu (điền các ô trước khi gửi):

    @codex fix finding <link> trên PR <số>, SHA <SHA>: sửa <hành vi> trong <tệp>, kiểm bằng <ca hồi quy>; đẩy vào nhánh PR hiện tại.

Không ghim số phiên bản hoặc patch trong mẫu dùng lâu dài. Nếu công việc thực
sự cần tăng phiên bản, fetch main và đọc phiên bản/patch hiện hành trước; giữ
lịch sử patch và không hạ phiên bản. Sửa tài liệu không tự sinh patch ERP.

### Đường nhận lệnh của tích hợp GitHub đang dùng

Tài liệu OpenAI hướng dẫn đặt lệnh trong **comment của đúng PR**:
https://developers.openai.com/codex/integrations/github (đối chiếu 11/09/2026).
Review chỉ rà soát; yêu cầu tác vụ ngoài review tạo cloud chat theo PR và chỉ
có thể đẩy bản sửa khi được cấp quyền. Không coi chữ `fix` là bảo đảm push.

- Với tích hợp này, không dựa vào mention trong issue để giao việc tự động.
  Nếu finding nằm ở issue, dẫn link nó trong comment trên PR chứa code cần sửa.
- Issue đang `In progress` kèm owner, branch và phạm vi tệp vẫn là NGUỒN KHOÁ
  CHUNG theo `AGENTS.md` mục 9. Phải claim trong issue, bàn giao khi chưa có PR
  và không sửa phạm vi agent khác đang nhận.
- Bộ nhận issue riêng ở PR #281 là cơ chế khác. Chỉ dựa vào nó sau khi đã kiểm
  trạng thái phát hành, bật cấu hình và có worker; biên nhận queued không phải
  Codex đã bắt đầu làm. Không suy ra nó hoạt động từ việc PR đã được mở.

### Xác nhận bàn giao, không chỉ gửi lệnh

Sau khi gửi, ghi link comment yêu cầu và tìm xác nhận nhận việc/link tác vụ
Codex. Phân biệt: chưa nhận, đang làm, bị chặn, đã có commit. Review hoàn tất
không chứng minh tác vụ sửa đã chạy hoặc có quyền push. Không có xác nhận thì
kiểm danh tính người gọi, môi trường/quyền và trạng thái cloud; báo chỗ thiếu,
không gọi lại liên tục. Không tự kết luận là hết token hay lỗi đồng bộ.

Nếu một tác vụ đang sửa cùng finding/phạm vi trên PR, bổ sung bằng chứng vào
đầu mối hiện tại, không mở tác vụ sửa thứ hai. Mất phản hồi không chứng minh
lượt trước chưa ghi commit; đọc lại nhánh trước khi giao lại.

Để nhận luồng tự động đã hoạt động, cần một lần kiểm sửa nhỏ được phép từ đúng
caller `claude[bot]`: có tác vụ Codex được nhận, có commit trên đúng nhánh PR,
rồi checks/review đúng SHA cuối. Đổi Markdown hoặc sửa thủ công từ desktop
không thay bằng chứng này; lời gọi GitHub cũng không tự đánh thức phiên desktop.

### Khi nào KHÔNG gọi Codex

Chỉ trả lời một câu hỏi thuần thông tin của anh Việt, hoặc việc đang chờ anh Việt
quyết chứ không chờ kỹ thuật. Im lặng cũng là một lựa chọn đúng.

### Một nhắc nhỏ hay quên

PR còn ở trạng thái Draft thì không bấm merge được, dù mọi cổng đã xanh. Bàn giao
xong nhớ nói rõ PR còn Draft hay đã Ready for review.

## Luật dừng, tránh hai bên gọi nhau vô tận

Đếm theo VÒNG LẶP TRÊN CÙNG MỘT VIỆC, không đếm tổng số lệnh. Trước khi viết một
lệnh `@codex`, đếm xem Claude đã gọi Codex bao nhiêu lần cho ĐÚNG finding hoặc
đúng điểm bất đồng đó trong 24 giờ qua, mà lần sau không mang thêm số liệu hay
bằng chứng mới nào so với lần trước.

- Đã có 3 vòng như vậy: KHÔNG gọi nữa. Thay vào đó viết một đoạn ngắn nói rõ hai
  bên đang bất đồng chỗ nào và mời anh Việt phân xử. Nếu chỉ bị lỗi khởi chạy,
  báo lỗi khởi chạy và bằng chứng còn thiếu, không mô tả thành bất đồng kỹ thuật.
- Chưa tới 3: gọi bình thường, và ghi rõ đây là vòng thứ mấy của việc đó.

Một PR có ba bốn việc độc lập thì mỗi việc có bộ đếm riêng. Một lần review rồi hai
lần `@codex fix` cho ba finding KHÁC NHAU không phải là ba vòng, và việc thứ tư
vẫn được giao bình thường. Chặn nhầm ở đây là quay lại đúng cái lỗi mà luật này
sinh ra để chữa: lỗi mới không ai nhận.

Đây là giới hạn mềm do agent tự đếm, không phải khoá workflow hay trần tổng
chi phí. Đổi finding/đính thêm bằng chứng không làm hệ thống có một trần chi
phí cứng. Dùng ID/link finding nhất quán để đối chiếu; không đổi tên cùng một
việc để né bộ đếm. Không có bằng chứng workflow thì không nhận đã chặn cứng.

Cũng KHÔNG trả lời nếu comment mới nhất của Codex không mang finding mới nào, chỉ
là xác nhận hay cảm ơn.

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ CLAUDE.md dòng 207 tới 219. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## Khi Codex báo lỗi

Xác minh nhận xét trên đúng SHA bằng chuỗi thao tác và bằng chứng nghiệp vụ.
Áp H10 và hướng dẫn H3/H5/H8.1 trong AGENTS.md: sau khoảng 15 phút chưa chứng
minh được thì nêu điều kiện còn thiếu và chọn phép kiểm quyết định. Chỉ phá
thử trong bản kiểm cô lập; ghi nhận lớp bảo vệ khác vẫn giữ đúng kết quả.

Trình tự bắt buộc: dựng lại đúng chuỗi thao tác Codex mô tả trên đúng SHA họ nói,
chạy và ghi số liệu thật, sửa, rồi trả lời kèm số liệu TRƯỚC và SAU khi sửa.

Chỉ khi tái hiện không ra mới được nói "không tái hiện được TRONG CÁC ĐIỀU KIỆN
ĐÃ KIỂM", và phải liệt kê đã kiểm những điều kiện nào.
