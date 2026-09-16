# Quy tắc chung đã được anh Việt duyệt 16/09/2026

Mục này ưu tiên hơn các luật cũ về model, đọc toàn bộ lịch sử, tag và đếm vòng.
Không thay quyền dữ liệu, cổng kiểm, hoặc biến quyền code thành quyền phát hành.

## 1. Giao kết quả nghiệp vụ
Mỗi issue có hồ sơ theo mau-ban-giao.md: kết quả người dùng cần, tình huống
bản cũ sai, bất biến tiền/kho/quyền, phạm vi được sửa và dữ liệu không được
đụng. Kiểm xuyên UI/API/Document/worker/GL/SLE theo tác động, không chỉ helper.
Mỗi việc có một owner ghi code. Trước nhận việc đọc claim và SHA trên GitHub;
owner cũ mất liên lạc phải bàn giao rõ, không coi hết giờ là quyền ghi đè.
Giữ tối đa ba PR tính năng đang triển khai; ưu tiên sự cố production. Đây là
kỷ luật hàng đợi, chưa phải khóa toàn repo của native Codex.

## 2. Khép vòng với Claude
Codex implement, kiểm bench, tích hợp và phát hành trong quyền đã giao.
Claude review độc lập, gom findings có ID, mức độ, bằng chứng và ca tái hiện.
Codex kiểm finding rồi sửa hoặc phản biện, gom một đợt push hợp lý. Review delta
vẫn xét ảnh hưởng dây chuyền. Không coi hai bot đồng ý là bằng chứng nghiệp vụ.
Không tự tạo tác vụ/polling để chờ bên kia. Biên nhận phải phân biệt đã đăng,
đã nhận, đã chạy, đã push. Comment thuần trạng thái không mention.

## 3. Chốt workflow và giới hạn thật
Claude chỉ chạy với dòng riêng `@claude review <40 ký tự SHA>` hoặc
`@claude review delta <40 ký tự SHA>` trên PR mở, không Draft, cùng repo.
Gate yêu cầu các dòng `Base: <SHA đầy đủ>`, `Scope: <phạm vi>`,
`Evidence: <kiểm hoặc ghi rõ chưa kiểm>`; lệnh delta cần thêm
`Previous: <SHA đã review đầy đủ>`. Base phải khớp API hiện tại. Chỉ owner/member/
collaborator hoặc bot Codex đã cho phép được khởi chạy. Không review tự động
mỗi lần push; check Claude Code Review chỉ kiểm gate, KHÔNG chứng minh review.

Workflow tuần tự theo PR, không hủy lượt đang chạy. GitHub có thể thay một
lượt pending bằng lượt mới; không bảo đảm mọi comment đều được xử lý. Owner
đối chiếu biên nhận khi thiếu, không gửi hàng loạt lời gọi.
Chốt tối đa ba lần bắt đầu bước model trên một PR trong 24 giờ, tính cả lỗi
sau khi bắt đầu. Lượt skip không tính; rerun vẫn phải qua gate. Không lặp cùng
head/base trong cửa sổ đó. Quá hạn ghi failure/summary; owner phải giữ chặn phát hành theo quy trình,
không phải branch protection hoặc required check tự khóa nút merge;
owner báo anh bằng một comment [BỊ CHẶN] có finding và link run, không tag bot.
Không xóa lịch sử run để reset giới hạn. Lỗi API đếm phải fail closed.
Gate kiểm quyền/lệnh trước khi đọc lịch sử. Bỏ đọc jobs của run completed
đã cập nhật trước cửa sổ, nhưng vẫn xét rerun cũ vừa cập nhật. Tối đa 80 request
lịch sử mỗi lượt; vượt ngưỡng fail closed, không gọi model.
Mỗi lượt tối đa 20 turn, 25 phút cả job. Reviewer dùng bằng chứng CI có sẵn,
không dựng lại toàn bộ bộ kiểm local; nếu chưa đủ thì báo chưa chốt. Đây là trần lượt/thời gian, KHÔNG
phải trần token hay USD. Chưa có số token provider thì ghi unavailable.

Phạm vi khóa: workflow claude.yml trong repo. Không thể khóa mọi lần gọi native
Codex/cloud/Desktop bằng YAML này. Các tác vụ đó phải theo owner/claim và
hồ sơ; không tuyên bố có khóa ghi code toàn hệ thống. Không mở thêm quyền
credential cho bot chỉ để vượt giới hạn. Hết finding thì dừng; không tag cảm ơn.

## 4. Instruction và bộ nhớ
AGENTS/CLAUDE dẫn tới quy tắc này; tra tài liệu theo nghiệp vụ, không nạp toàn
kho nhật ký mỗi lượt. Desktop kiểm đầu phiên remote/SHA/claim, mạng và quyền
bench cần dùng. API/CLI trước UI khi phù hợp. Lỗi công cụ không chứng minh ERP
lỗi; log fail không tự chứng minh rollback. Ghi điểm dừng trước bàn giao.
Tái dùng bằng chứng chỉ khi code, base và đầu vào liên quan còn phù hợp;
phiên bản tích hợp cuối phải qua cổng tương ứng. GitHub là trạng thái hiện tại.
Cloud cần bản hồ sơ gọn trong repo; nhật ký chi tiết ở máy, không bắt cloud đọc
đường dẫn Mac. Không lưu secret/transcript/dump/log lớn vào Git, không thêm VPS.

## 5. Astra theo độ khó
Giữ Astra gpt-6-astra mặc định low, không bật Fast Mode. Anh đã duyệt chọn
medium cho luồng nhiều bước, high cho tiền/kho/rollback/concurrency/core;
xhigh/max chỉ khi có bế tắc đã ghi dữ liệu và lý do. Chọn effort tường minh
ở bộ khởi chạy hỗ trợ; ghi model/effort thực từ metadata, không nhận lời dặn
là cấu hình đã đổi. .codex/config.toml có profiles là cấu hình đề xuất; phải xác minh bộ khởi chạy đã nạp profile và model metadata. Native bot phải
kiểm cấu hình riêng, không giả định nó đọc profile này.
Astra ưu tiên truy nguyên nguyên nhân và phép thử phản chứng. Đối với fix rủi ro
cao, chứng minh bản cũ fail/bản mới pass, kiểm cả retry/rollback và dữ liệu sót.

## 6. Đo hiệu quả
Hồ sơ issue giữ số vòng model, finding mở lại, lỗi lọt production liên quan,
run ID và thời gian tới hoàn thành. Token dùng số provider nếu có, không ước
lượng bằng số comment; thiếu ghi unavailable. Mỗi kỳ tổng hợp từ hồ sơ/run
bằng script hoặc thao tác theo yêu cầu, không thêm lịch gọi model chỉ để đếm.
Không dùng số commit hoặc tổng ca xanh làm thước đo chất lượng chính.

### Chuyển từ workflow cũ
Sổ đếm v1 bắt đầu khi PR331 được merge và workflow có tên run/bước mới bắt
đầu thi hành. Lượt workflow cũ không có định danh PR đáng tin nên không được
gộp vào sổ v1. Trong 24 giờ đầu, không nhận trần ba lượt bao cả workflow cũ;
owner đối chiếu lượt cũ trước gọi mới. Không đổi prefix run/bước để reset sổ.
