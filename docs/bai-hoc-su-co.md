# Bài học từ sự cố thật

Mỗi mục dưới đây là một lần repo này hỏng thật, trên hệ thống đang chạy cho cửa
hàng. Ghi lại triệu chứng, nguyên nhân gốc, và cách tránh. Đọc tệp này trước khi
sửa những chỗ có liên quan, vì phần lớn các lỗi đó KHÔNG có lớp nào tự bắt được.

Tệp này chỉ giữ bài học rút gọn. Nhật ký đầy đủ từng ngày nằm ngoài repo.

## 11/09/2026 - Kiểm map mới không được khóa bảo trì SePay (#273)

Review phát hiện validate toàn bộ account_map mỗi lần save sẽ chặn cả enabled/token/mốc đồng bộ khi một Bank Account cũ bị ngưng dùng. Chỉ kiểm tuyến mới hoặc thay đổi; JSON/xung đột mới vẫn chặn. Cửa cấu hình tài chính phải dùng quyền tài chính trực tiếp, không đòi thêm vai bán hàng. Ca bench giữ map cũ rồi vô hiệu hóa Bank Account, lưu công tắc, từ chối tuyến mới sai và cho Accounts Manager độc lập khai map.

## Mất code vì làm trên nền cũ

Ca hoàn tất sản xuất từ app phải gửi cố ý ngày/giờ máy khách sai rồi gọi đúng API, đọc lại SE/SLE và ngày GL. set_posting_time=0 để core lấy giờ site. Tổng GL0=0 không chứng minh gì khi danh sách rỗng: phải kiểm biến động giá trị kho ròng0 hoặc có GL thật, và in mốc trước/sau cùng thời điểm đã lưu khi ca đỏ. Nguồn: PR258, ca _gio_hoan_tat_app, review5637545293.

Đã mất code thật BA lần.

1. Commit của một phiên xoá mất commit của phiên khác đang làm dở.
2. Bản đẩy v201 đè mất phần của v202, số phiên bản app tụt từ 202 về 201. Bắt
   được nhờ chạy đối chiếu mã băm trước khi deploy.
3. Đẩy `patches.txt` qua web đè mất dòng mà phiên kia vừa thêm một phút trước.
   Fetch lúc 15:53, họ đẩy lúc 15:54, mình đẩy lúc 15:55.

Cách tránh: fetch lại NGAY TRƯỚC MỖI LÔ đẩy, không phải một lần đầu buổi. Đẩy
`patches.txt` cuối cùng và một mình. Đối chiếu mã băm từng tệp sau khi đẩy, đừng
chỉ nhìn `git diff`.

## Trùng khoá YAML mà git merge vẫn sạch

Ngày 11/09/2026, hai nhánh cùng thêm một khoá `claude_args` vào
`.github/workflows/claude.yml`, ở hai vị trí khác nhau trong tệp. Git merge sạch,
không báo xung đột. Nhưng YAML lấy khoá cuối cùng, nên giá trị của nhánh thứ nhất
bị vứt đi im lặng.

Cách tránh: với tệp YAML hay JSON, sau khi merge phải kiểm khoá trùng chứ đừng
tin git merge sạch là xong.

```
python3 - <<'EOF'
import re, collections
s=open('.github/workflows/claude.yml',encoding='utf-8').read()
k=[m.group(1) for m in re.finditer(r'^\s{10}([a-z_]+):', s, re.M)]
print([x for x,n in collections.Counter(k).items() if n>1])
EOF
```

## Hook đặt trên "*" làm cả tiệm không gửi được email bốn ngày

Ngày 16/08/2026, một hook `doc_events` đặt trên `"*"` xoá trắng ô `sender` của
Email Queue. Hook trên `"*"` áp lên MỌI doctype, kể cả hạ tầng của Frappe. Kết
quả: 117 trên 118 thư chết trong bốn ngày, không ai phát hiện ngay vì không có
lỗi nào hiện ra.

Cách tránh: hook rộng phải có danh sách chừa hạ tầng ra. Mỗi lần đặt hook, tự hỏi
"hook này chạy trên những doctype nào mình không ngờ tới".

## Thiếu dòng patch mới thì Frappe Cloud không Migrate

Nếu chỉ sửa `.py` hoặc `.js` mà `vagabond/patches.txt` không đổi, Frappe Cloud
chọn "Pull" thay vì "Migrate". `after_migrate` không chạy, trường mới không được
dựng. Đã làm chết màn Báo giá ở v177 và lỗi 500 ở v179.

Cách tránh: mỗi lần phát hành phải thêm một dòng patch mới, giữ nguyên mọi dòng
cũ của phiên khác.

## Ca kiểm tự che mất lỗi

Ngày 06/09/2026, một ca kiểm gọi thêm một hàm khởi tạo "cho chắc" ngay sau khi
tua đồng hồ. Chính hàm đó có bước đồng bộ lại ngày, nên nó chữa lỗi trước khi ca
kiểm kịp nhìn. Ca xanh, lỗi vẫn còn, và đi thẳng lên main.

Cách tránh: ca kiểm dựng ĐÚNG chuỗi thao tác của người dùng, không gọi thêm hàm
nào ngoài chuỗi đó. Mỗi lần định gọi thêm một hàm cho chắc thì tự hỏi hàm đó có
sửa trạng thái mình sắp kiểm không. Ca nào đã bị phát hiện là che lỗi thì ghi chú
thẳng vào trong ca, để người sau không sửa nó về như cũ.

## Dò chuỗi trong mã nguồn không phải là kiểm thử

Tìm thấy một lời gọi trong tệp không chứng minh được nó chạy đúng thời điểm, đúng
thứ tự, hay chạy hết. Ba lỗi nặng nhất của một issue đều lọt qua kiểu kiểm đó.

Cách tránh: mã chạy trên trình duyệt thì nạp cả trang vào node bằng
`vagabond/khung/kiem_thu/gia_lap_trang.js`, dựng DOM giả lập, chặn mạng, cho đồng
hồ tua được. Phép dò chuỗi chỉ dùng để chốt những thứ KHÔNG chạy được, ví dụ
"không còn chỗ nào tự ghép ngày từ độ lệch nữa".

## Đọc kết quả đột biến cho đúng

Viết xong ca kiểm thì phải cố tình làm hỏng lại chỗ vừa sửa, xem ca kiểm có kêu
không. Nhưng đột biến không làm đổ ca nào thì có ba nguyên nhân khác nhau:

1. Bộ kiểm yếu thật, phải viết thêm ca.
2. Mẫu tìm-thay không khớp nên thật ra chưa đổi gì. Đã xảy ra khi một hàm được
   xuống dòng. LUÔN khẳng định mẫu khớp đúng một lần trước khi tin kết quả.
3. Code có dư một lớp bảo vệ, gỡ một lớp thì lớp kia vẫn đỡ. Chứng minh bằng cách
   gỡ HẾT các lớp cùng lúc rồi chạy lại.

Báo cáo phải ghi đúng như nó là. Nếu 5 đột biến chỉ bắt được 2 thì viết là 2 kèm
giải thích ba cái kia, không làm tròn thành 5 trên 5.

## Sửa bằng cách gom về một nguồn, không phải thêm chỗ nhớ gọi

Một lỗi lệch ngày phải sửa ba lần mới hết, vì hai lần đầu chỉ đi thêm lời gọi
đồng bộ vào những chỗ nhớ ra. Cách đó đúng cho tới khi có một lối vào không nhớ,
và lần cuối có đúng bốn lối như vậy.

Cách tránh: khi thấy cùng một giá trị được tính lại ở nhiều nơi, đừng vá từng
nơi. Tạo MỘT hàm làm nguồn duy nhất rồi cho mọi nơi gọi nó, và thêm một ca kiểm
chốt "không còn chỗ nào tự tính nữa".

## Whitelist bị mất quyền gọi mà không lớp nào báo

Chèn một hàm mới vào giữa dòng `@frappe.whitelist()` và dòng `def` của hàm cũ sẽ
làm hàm cũ mất quyền gọi. Python không báo, kiểm thử không báo, cổng trả về 0,
chỉ lộ khi có người bấm vào màn hình.

Cách tránh: thêm hàm có `@frappe.whitelist()` thì phải thêm tên vào
`vagabond/khung/kiem_thu/thu_cua_ngo.py`, tệp đó chốt danh sách hàm mở ra ngoài.

## Cổng xanh tại máy không có nghĩa CI sẽ xanh

Máy làm việc có sẵn `requests` và nhiều gói khác. Máy chạy CI thì tay không,
Python 3.11. Ngày 20/08/2026 CI đỏ ba ca vì một mô đun kéo theo chuỗi import dẫn
tới `requests`.

Cách tránh: tái hiện CI tay không trước khi bàn giao.

```
mkdir -p /tmp/chanreq
printf 'raise ImportError("gia lap CI")\n' > /tmp/chanreq/requests.py
PYTHONPATH=/tmp/chanreq python3 vagabond/khung/kiem_thu/chay.py -im
```

Ca kiểm nào kéo theo thư viện mạng là ca kiểm đặt sai tầng.

## Bỏ bắt buộc bằng Property Setter là chưa đủ

Ngày 10/09/2026, hai ô Số séc và Ngày séc trên Payment Entry bị chặn dù đã bỏ
`reqd` và `mandatory_depends_on` bằng Property Setter. Nguyên nhân: ERPNext gọi
`frm.toggle_reqd(["reference_no","reference_date"], ...)` LÚC CHẠY trên trình
duyệt, đè lên Property Setter.

Cách tránh: khi lõi còn đặt lại thuộc tính lúc chạy, phải can thiệp ở đúng tầng
đó. Ở đây là thêm một client script cho doctype. Và nhớ rằng handler `validate`
phía trình duyệt chạy TRƯỚC phép kiểm bắt buộc của Frappe, nên điền ở đó là kịp.

## Merge rồi không có nghĩa là xong

Ngày 06/09/2026, một PR merge lúc 08:48:20, finding chặn được đăng lúc 08:48:27,
lệch bảy giây. Bản có lỗi nằm trên main mà chưa ai deploy.

Cách tránh: sau khi merge vẫn đọc tiếp comment trên PR đã đóng. Lỗi phát hiện sau
merge thì mở PR MỚI từ main mới nhất, không revert main, không sửa lén. Chưa
deploy cho tới khi bản sửa được review đạt.

## Sửa thẳng trên Desk là mất dấu vết

Property Setter và Server Script sửa tay trên Desk nằm trong cơ sở dữ liệu, git
không quản, không có lịch sử để khôi phục. Một Property Setter đặt tay ngày
07/08/2026 biến mất lúc nào không ai hay, và mất rồi thì không truy được.

Cách tránh: mọi thay đổi cấu trúc phải nằm trong mã nguồn, khai lại mỗi lần
Migrate. Trước khi sửa Server Script phải báo chủ repo.

## GitHub App không đẩy được vào .github/workflows/

Đây là luật cứng của GitHub, không phải thiếu quyền, cấp thêm quyền cũng không
qua được. Mọi thay đổi trong thư mục đó phải người thật sửa tay.

## Issue280: lời gọi issue cần biên nhận thật

Review PR281: một user:null hoặc API lỗi ở issue đầu từng làm dừng toàn lượt
quét. Đã thêm ca giữ issue sau vẫn được nhận, nhưng job vẫn đỏ để người trực
biết lỗi. Nhãn queued phải phản ánh biên nhận sống, không POST lại mỗi lượt.

Lệnh review trong body issue thường không đi qua đường comment PR mà tích
hợp Codex hỗ trợ. Workflow Claude skipped không có nghĩa Codex đã tiếp nhận.
Bộ nhận riêng phải lưu mã nguồn yêu cầu, xác nhận queued khác working/done,
đọc lại khi mất phản hồi và không coi marker do người dùng dán là biên nhận.
Nguồn và quy trình kích hoạt: docs/codex-issue-inbox.md. Không bật hàng đợi
khi chưa có worker; không tự gọi model chỉ để xác nhận đã nhận.

## Hai nhánh thêm ca kiểm vào cùng dòng đăng ký

Tích hợp PR265 sau274 trên issue280 gặp xung đột ở hai tệp chạy kiểm.
Một phía thêm combo/cấn trừ, phía kia thêm đối chiếu/cọc/tham chiếu tiền.
Chọn nguyên một phía sẽ làm mất bộ ca của phía còn lại dù mã sản phẩm vẫn còn.
Đối chiếu ba chiều từ base, giữ hợp các đăng ký không trùng và chạy cổng
trên bản kết hợp. Bundle phải dựng lại, không giải quyết bằng chọn một bản ghép.

## Ngoại lệ khóa của SQL chưa chắc được worker tự thử lại

Review PR265 phát hiện nhánh worker bắt lỗi nghiệp vụ nuốt lỗi khóa. Đọc đúng
core Frappe f33ac3f cho thấy database.sql bọc lỗi khóa thành QueryDeadlockError
và QueryTimeoutError, nhưng execute_job chỉ vào nhánh retry với InternalError
hoặc RetryBackgroundJobError. Chỉ đổi sang raise vẫn chưa đủ tự thử lại.
Phải kiểm cả nơi đổi loại lỗi và nơi xử lý cuối; ca giả ném lỗi chỉ chứng minh
nhánh xử lý, không thay phép hai kết nối DB thật.


### 11/09/2026 - File trong ca kiểm và phân loại PLE (#265)

Savepoint chỉ lùi DB; Frappe f33ac3f database.rollback(save_point) không chạy after_rollback của File. Ca tạo tệp có content phải dùng nội dung riêng và tự dọn qua File.delete trong finally, kiểm đường dẫn đã mất kể cả khi submit lỗi. Không coi đếm chứng từ sạch là đĩa sạch.

ERPNext de591661 reconcile_against_document sửa phân bổ PLE nhưng giữ GL gốc. Ca thu trước rồi phân bổ sau tái hiện được GL join thiếu tiền; PE đã phân bổ ngay khi submit không đủ làm đối chứng. PLE của credit note/POS/write-off cũng mang voucher_type Sales Invoice. Chỉ dòng Nợ tự thân của SI bán là gross; các dòng còn lại vào điều chỉnh có giải thích, không âm thầm trừ gross.

### 11/09/2026 - Combo phải kiểm cả dòng đã bị xóa (#265)

Review C1 chỉ ra: lặp qua payload chỉ thấy món còn lại nên không bắt được món combo đã bị xóa. Cửa lưu phải so nhóm trong DB với nhóm được gửi, giữ đủ hoặc xóa hết. Cửa sửa bill không được coi món thiếu dong_goc là món lẻ nếu nó đang thuộc combo. Cần ca gọi cửa lưu/API, không chỉ gọi helper kiểm nhóm.

Sao chép, sửa đổi và trả hàng có ý nghĩa khác nhau: bản sao là lần bán mới, tính lại cấu hình combo hiện tại; sửa đổi giữ phân bổ đã lưu của hóa đơn đã hủy; trả hàng lấy dòng gốc qua sales_invoice_item của mapper ERPNext. Không chỉ bỏ metadata rồi nhân lại rate đã làm tròn: combo155000 có phần107308/3 sẽ mất một đồng. Ca tích hợp phải đo cả trả toàn phần, trả từng bánh, hủy trả và amend trước khi phát hành.

### 11/09/2026 - Khóa duy nhất chưa đủ cho retry HTTP (#246)

Ca HTTPS trên SHA3c30b41 cho hai request đặt bàn cùng đọc chưa tồn tại trước khi insert: chỉ có một phiếu nhưng phản hồi là200/409. Cần bắt riêng DuplicateEntryError, lùi savepoint, đọc current for_update và so hash rồi trả mã cũ. Snapshot REPEATABLE READ từ lần đọc đầu không đủ. SHA6fb7473 đạt17/17 cửa HTTPS, gồm OTP dùng một lần, cookie, logout và booking đồng thời. db_insert của Frappe còn đẩy Duplicate Name vào message_log; khi retry đã đối chứng thành công phải bỏ thông báo của insert vừa lùi, giữ thông báo trước đó.

## PR281/282: review không tự giao sửa finding

Ngày 11/09/2026, Claude đăng finding trên PR #281 rồi kết bằng lệnh review;
không có bằng chứng tác vụ sửa đã được nhận. Review chỉ yêu cầu rà soát, còn
việc sửa cần một yêu cầu tác vụ riêng. Sửa lời dặn không tự cài bộ thực thi.

Cách phòng: theo mục Bàn giao trong `CLAUDE.md`, gửi đúng PR/SHA/finding và
phạm vi; kiểm xác nhận/link tác vụ, commit đúng nhánh và checks/review SHA cuối.
Không gọi sửa trùng khi người khác đang làm cùng phạm vi, không coi thiếu
phản hồi là chưa có commit. Chưa có log thì không kết luận lỗi đồng bộ/quota.
Luật dừng theo từng việc trong `CLAUDE.md` là nguồn chung; tài liệu Codex phải
đồng bộ, không giữ cách đếm tổng comment cũ làm chặn các finding độc lập.
Nguồn: PR #281, review và sửa tài liệu PR #282; chưa có nghiệm thu bot-to-bot.


### PR281 - lỗi HTTP không cùng họ OSError

IncompleteRead kế thừa HTTPException nên tuple lỗi cũ không cô lập được issue hỏng. Bắt Exception tại ranh giới từng issue, giữ BaseException cho ngắt chủ động, báo lỗi cuối lượt. Log phải giữ file/dòng/hàm và mã HTTP nhưng không in payload hoặc thông điệp ngoại lệ tùy ý; ca kiểm chốt issue kế tiếp được nhận và log không rò payload.


### PR281 - hoàn tất chẩn đoán N1/N2/N3

Dùng TranPhanTrang thay so thông điệp ở hai nơi, kiểm qua GitHub.pages thật tới đủ100 trang. Kiểm riêng thông điệp ngoại lệ có dữ liệu kín và frame reconcile. Với HTTP403 chỉ in metadata trong danh sách cho phép và đúng định dạng: số lượt còn lại, thời gian chờ, request ID. Thiếu metadata không được tự kết luận là thiếu quyền. Không in body hoặc header tùy ý.


### PR281 - chẩn đoán phải phủ cả bước khởi chạy

Lỗi đọc nhãn hoặc danh sách issue xảy ra trước sweep. Dùng chan_doan chung ở main, vẫn thất bại toàn lượt; thay lỗi cuối bằng thông báo sạch và from None để traceback không in lại thông điệp gốc. Ca kiểm dựng HTTPError ở từng lời gọi tiên quyết, header thật không phân biệt hoa thường, và kiểm cả traceback cuối. Bổ sung thời điểm reset trần; không suy thiếu quyền từ403.

### #266 tái phát 12/09: hàng rào phát hành không được chặn ghi sổ

Tập chặn có đơn nháp nhưng tập tự gửi chỉ có tờ đã submit và được chọn ngày. Return trước ghi sổ làm cả ngày mới thành backlog. Tách quyết định phát hành khỏi ghi sổ, giữ cửa chung HTTP; đọc script After Submit hiện hành trước khi chốt vì core vẫn gọi script trong submit. Còn nợ nhưng vòng gửi rỗng vẫn phải giữ mốc lỗi và báo riêng, không trông chờ bộ đếm chỉ gồm tờ đã submit.

Công cụ đặt phiên bản phải giữ nguyên lịch sử patches.txt. Không tin docstring: dat_phien_ban.py cũ ghi "giữ nguyên" nhưng lọc xóa mọi dòng cũ. Ca tạm file phải kiểm nội dung từng byte và gọi lần hai không nhân dòng.

### #266 ngày 12/09: mock DB quá dễ tính che cột không tồn tại

Email Queue không có subject (email_queue.json Frappe 16.27.1); lọc theo cột đó ném Unknown column trước khi xếp thư. Fake exists nhận mọi filter đã làm ca kiểm xanh giả. Phải đối chiếu schema thật và cho fake từ chối filter lạ. Lỗi đếm hóa đơn không được biến thành 0; cache giảm thư lặp bị hỏng không được làm mất cảnh báo.
### PR210 - dấu chống tạo trùng phải bền trước HTTP

Khoá Redis có TTL và trạng thái chỉ nằm trong phản hồi không chặn được reload hoặc worker chết sau POST. Ghi ý định DB và enqueue sau commit; worker commit dang_gui trước HTTP, job trùng không nhận lại. Sau kết quả chưa rõ, tìm rỗng không chứng minh chưa tạo. Integration Request có dọn log30ngày nên không dùng làm hàng rào lâu dài. Kiểm bằng tiến trình chết và hai worker trên DB CI, không chỉ mock helper. Cả mã mới/mã cũ dùng cùng handler và xác nhận giá0.


## PR210: khóa khi gọi mạng và dấu vết lúc gộp nhánh

Worker giữ khóa xuyên HTTP để cửa đối soát không chen vào, nhưng request người dùng phải NOWAIT và trả câu chờ. Khóa Item chỉ tuần tự hóa việc tạo dấu đầu tiên, cũng NOWAIT; không được giữ nó để chờ worker. Ghi kết quả bằng điều kiện mã lần/trạng thái để worker cũ không ghi đè. Bench phải cho đối soát chen đúng lúc POST, không chỉ cho hai worker đua ở đầu.

Gộp nhánh không được bỏ dấu vết lỗi. Lưu thời điểm bắt đầu bền trước HTTP, mã HTTP/loại lỗi/hash và độ dài phản hồi trên dấu cùng Error Log. Không lưu nguyên URL/ngoại lệ/thân phản hồi có thể chứa khóa; người đối soát cần dấu vết nhưng không cần bí mật trong log.

## 12/09/2026 - Dọn nhật ký cần đọc đúng cơ chế của khung (#284)

Cloud đọc trực tiếp ngày12/09: database1,25GB trên hạn1GB. Không suy từ
việc thiếu cấu hình mặc định rằng một bảng không được khung hỗ trợ dọn.
Trong Frappe16.27.1, LogType là runtime_checkable Protocol, kiểm cấu trúc
method chứ không đòi kế thừa danh nghĩa. DeletedDocument và NotificationLog
có clear_old_logs nên được Log Settings hỗ trợ; Version không có.
Tiền đề ban đầu của PR rằng cả ba không thể dùng Log Settings là sai.

Nhịp riêng có mục đích chia lô, giới hạn mỗi lượt và giữ lịch sử/payload
chứng từ thuộc KHONG_DUOC_DON (kể cả loại chưa xác định). Dọn phẳng theo
tuổi sẽ làm mất dấu vết dù không DELETE trực tiếp bảng chứng từ. Phải có
phê duyệt mốc lưu trước bật lịch; không lấy bình luận do tác giả viết làm
bằng chứng anh Việt đã duyệt. Ước tính dung lượng trước khi loại chứng từ
bảo vệ không được dùng làm số sẽ thu hồi.

ROW_COUNT phải đọc ngay sau DELETE và trước commit. Khi đọc lỗi hoặc âm,
rollback lô đang mở và báo chưa xác định; lô đã commit trước đó không tự
lùi. API dọn chỉ POST. Ca bench dùng MariaDB thật kiểm rollback/số đếm,
giữ dòng mới, lịch sử và payload bảo vệ; không chạy trên production.

OPTIMIZE có thể trả result rows error/status Operation failed mà không
ném exception. Chỉ nhận thành công khi status OK và không có error; lỗi
phải ghi log, không đổi số dòng đã DELETE. Ca riêng kiểm cả phản hồi lỗi
và thành công. Không suy từ DELETE rằng tệp đã co hoặc quota đã giảm.
## Issue287 - thông báo của bot cần đối soát nguồn và dấu gửi bền

Sự kiện do GITHUB_TOKEN tạo không luôn kích hoạt workflow tiếp; chỉ nghe
comment event sẽ bỏ sót tin workflow. Đọc lại nguồn GitHub theo mốc với lịch
bù, chỉ chạy code default branch. Lưu pending trước gửi Telegram, sau phản hồi
đúng mới ghi seen. Unit test tái hiện mất phản hồi và lỗi lưu kết quả: lượt
sau dừng đối chiếu, không gửi lặp. Secret token không hiện trong API đọc
metadata; ghép chat dùng mã riêng và artifact ciphertext, không in URL lỗi
Telegram vì URL có token. Nguồn: Issue #287; chưa coi unit test là kết nối thật.


Issue287 bổ sung: UI thật cho thấy secret ở Agents nhưng Actions API không
thấy. Hai namespace riêng, cần chọn đúng Actions, không đổ lỗi người dùng chưa
lưu. Mã ghép cấp trước có10ký tự hex; ca kiểm phải dùng cả độ dài đó, không
chỉ mẫu12ký tự tự đặt trong test. Tái hiện mẫu10đỏ trên bản cũ, sửa và kiểm
entry point mã hoá/giải mã PyNaCl thật bằng fixture, không chép mã riêng vào git.


PR288 review: băm updated_at vào trạng thái gây tin trùng, nhưng chỉ bỏ ngày
cũng làm mất thông báo mở lại. So snapshot trạng thái lần cuối, sau gửi mới
cập nhật snapshot; key sự kiện vẫn tách từng lần chuyển. Tỉa seen phải đi đôi
với cửa đọc nguồn (review cũ có thể quay lại nếu vẫn quét toàn bộ). Đọc blob
cùng SHA khi Contents API không trả nội dung lớn. Ca kiểm hai comment, đóng/
mở lại, bot đổi checkbox so với finding mới, tỉa rồi chạy lại review đều đạt.


### Frappe Check trên Desk có checkbox hiển thị riêng

Log bench PR210 cho hai input checkbox trong cùng wrapper: input thao tác có data-fieldname trên chính thẻ input, còn disabled-deselected không có. Chọn hậu duệ wrapper, kể cả lọc type=checkbox, vẫn khớp hai phần tử. Neo locator vào input[data-fieldname] và kiểm trên DOM thật, không dùng nth(0) để che sai lựa chọn.


### #266: trả trước cửa xuất vẫn có thể quá muộn

Hook After Submit production đã tự gọi MInvoice bên trong submit. Ca chỉ dựng
API script và kiểm helper không thấy điều này. Phải snapshot/hash hook sống,
đưa vào nền migrate CI và bật cả công tắc nhánh cần kiểm. Cờ hoãn đặt trước
submit, trả trong finally; không tắt toàn bộ hook hoặc hàng rào thuế.
Chế độ `thu` của một script phát hành không đồng nghĩa chỉ đọc: bản này vẫn
login và nạp Pancake. Phép đếm nợ phải đọc ERP, chốt cùng phạm vi cho số và tiền.


## 12/09/2026 - Hai cửa phát hành và lớp cách ly bench (#266)

Hook After Submit có thể đã ghi ID trước bước `_tu_xuat_hddt`. Khi cả hai
bật, cửa sau bị `da_gui` chặn, trả cảnh báo đã gửi và ghi Error Log, không
phát hành lần hai. Production đọc ngày12/09 có `tu_xuat_hddt=0`; lưu ý
`khoa_ma_pancake.bat_cai_dat` đặt1 nếu ô còn NULL. Ca `kiem_hddt_266.py`
đo cả cấu hình0/1 với hàm thật và đúng1POST cho mỗi tờ.

Không suy từ lời gọi commit rằng bench đã commit thật. `nen._cach_ly`
tăng `_disable_transaction_control`; Frappe16.27.1 Database.commit trả
ngay khi cờ này bật, còn rollback có save_point vẫn chạy SQL. Ca kiểm đọc
cả ba công tắc trước/sau bằng DB không cache để chốt đã hoàn nguyên.

## #290: tách đơn nháp kẹt khỏi nghĩa vụ HĐĐT đã ghi sổ

Nháp kẹt kho/duyệt không được giữ cả ngày sau không phát hành. Chỉ tờ đã ghi sổ chưa có HĐĐT giữ hàng rào ngày cũ; các cờ đối chiếu và lỗi đọc vẫn giữ nguyên. Combo nháp cũ cần lưu trước submit vì core đặt docstatus=1 trước validate. Khi chuẩn bị có thể ghi DB, lỗi chuẩn bị cũng phải rollback trước khi chạy đơn kế. Thời điểm modified cùng lịch đồng bộ chưa chứng minh trường người nhập bị hàm đồng bộ xóa; cần ca gọi thật và Version diff.

### 12/09/2026 - B1 issue 290: ca kiểm phải giữ đường máy ghi đè

Ca giữ dữ liệu quà tặng đặt vgb_pt_do_may=0 và mock bảng thanh toán đã che sự cố. Lý do vẫn ở DB nhưng phương thức bị đổi khiến UI giấu nó. Phải đi qua thao tác người chọn, giữ nguồn máy trả dữ liệu có thật, chạy validate và reload; kiểm cả phương thức lẫn lý do. Không nhận modified cùng giờ là bằng chứng cột nào đã bị xóa.

### 12/09/2026 - PR291 B1-3: cửa ghi tắt phải đi qua chốt nghiệp vụ

Chốt validate không bảo vệ được API dùng db.set_value. Chuyển sang Hàng tặng phải qua Document.save để chặn dòng tiền tay trước DB, thay vì ghi trạng thái kẹt cho lần sau. Không dùng helper đọc nuốt lỗi làm hàng rào an toàn.

### 12/09/2026 - Tắt chính sách không được che trạng thái cần dọn (#291)

Nháp tặng đã mang kho/64181, khi tắt công tắc cùng lúc đổi thành thu tiền, hạ dấu trước làm nhánh return bỏ qua dọn kho. Dọn chuyển loại trước khi tính dấu mới; ca thuần bắt update_stock còn 1, ca bench lưu-ghi sổ-hủy và đọc GL/SLE/Bin. Nguồn finding 3996732355, cùng lỗi 3996733712 trên nhánh tích hợp #293.
