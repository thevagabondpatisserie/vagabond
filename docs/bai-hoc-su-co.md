# Bài học từ sự cố thật

Mỗi mục dưới đây là một lần repo này hỏng thật, trên hệ thống đang chạy cho cửa
hàng. Ghi lại triệu chứng, nguyên nhân gốc, và cách tránh. Đọc tệp này trước khi
sửa những chỗ có liên quan, vì phần lớn các lỗi đó KHÔNG có lớp nào tự bắt được.

Tệp này chỉ giữ bài học rút gọn. Nhật ký đầy đủ từng ngày nằm ngoài repo.

## 27/10/2026 - Thêm trường cho tin Zalo phải đi qua MỌI đường gửi, kể cả xả giờ im (#504)

v613 thêm ảnh bảng cho tin, đường gửi ngay đã truyền ảnh nhưng đường gộp tin hoãn
giờ im chỉ đọc chữ: ảnh mất mà sổ vẫn ghi "Đã gửi gộp". Cách phòng: thêm cột cho
Vagabond Tin Kenh thì dò mọi nơi đọc dòng tin (_nhan_mot, _nhan_lo) và mọi lời gọi
_gui_zalo; bản giả get_all trong ca kiểm phải chỉ trả các cột được hỏi. Đổi chữ ký
hàm thì sửa cả bản giả trong khung/kiem_that: CI máy không chạy thư mục này, chỉ
bench bắt được (#504 bench đỏ vì bản giả _gui_zalo hai tham số).
Cùng PR: tính nguyên liệu theo công thức phải nổ bán thành phẩm phantom như lệnh
sản xuất, và ngày cần của YCSX lọc trên từng dòng, không theo đầu phiếu.

## 12/10/2026 - Kiểm lại tổng sau tạo đơn và biên nhận cảnh báo (#465)

Giảm giá gửi đúng trường vẫn cần đọc lại số phải thu của hệ nhận đơn. Lỗi
đọc lại sau khi đã tạo không được biến thành lỗi tạo đơn, khiến khách thử lại.
Cảnh báo GET cần worker riêng; bao() nuốt lỗi ghi thì commit thành công chưa
chứng minh đã có tin. Chỉ đặt khoá ngày khi có tên tin đã ghi. Ca hồi quy phải
thử timeout, JSON hỏng và nhánh không ghi được tin, không chỉ HTTP 200.

## 12/10/2026 - HTTP lỗi vẫn phải đi qua cùng cửa cảnh báo dịch vụ ngoài (#465)

Ahamove trả 401, 429 hoặc 5xx không ném exception, nên nhánh chỉ ghi Error Log
đã bỏ qua cảnh báo cho Sales dù phí giao đang hỏng. Cách phòng: mọi kết quả
HTTP khác thành công phải đi qua cùng helper cảnh báo chống trùng như lỗi mạng;
cảnh báo có mã trạng thái và thân phản hồi rút gọn, đồng thời che khoá API và
token. Ca hồi quy phải gọi hai lần cho cả 401 và 500 rồi chốt chỉ có một cảnh
báo trong ngày. Nguồn: finding review PR #465 trên SHA ef756a4.

## 12/10/2026 - Chuỗi giờ không múi giờ bị hệ nhận đơn hiểu là UTC (#462 follow-up)

Biên nhận web hiện đúng 19 giờ nhưng Pancake hiện 2 giờ sáng hôm sau. Nguyên
nhân là trình duyệt gửi giờ Việt Nam không kèm múi giờ và máy chủ chuyển nguyên
chuỗi sang Pancake, nơi đọc chuỗi đó như UTC. Cách phòng: chuẩn hoá tại một cửa
máy chủ sang UTC trước khi gửi hệ ngoài; ca kiểm phải chốt cả giờ tối và 7 giờ
sáng để bắt lỗi đổi ngày. Không sửa từng trang và không sửa ngược đơn đã tạo.

## 12/10/2026 - Lỗi dịch vụ ngoài lặp theo từng khách phải có cảnh báo chống trùng (#462 follow-up)

Phí giao hỏng từ 27/09 nhưng 1.158 Error Log giống nhau không đưa ra việc cần
làm. Cấu hình chạy thật vẫn trỏ máy chủ Ahamove chạy thử. Cách phòng: màn Cài
đặt phải tô đỏ địa chỉ `apistg`; lỗi gọi dịch vụ chỉ ghi và gửi kênh cảnh báo
một lần mỗi ngày, kèm đúng ô cần kiểm. Không tự đổi cấu hình vận hành trong code.

## 12/10/2026 - Không coi ảnh máy chép vào Item là ảnh ERP người chọn (#462)

Hannari trên web hiện bộ ảnh cũ dù Pancake đã có bộ ảnh mới. Nguyên
nhân là các tệp `sp-<mã>*` do `doi_soat.keo_anh` chép từ Pancake vào
`Item.image` được xếp như ảnh hồ sơ ERP người chọn, nên luôn đè ảnh
Pancake sống. Cách phòng: nhận diện bản chép bằng tên tệp tại một
nguồn chọn ảnh chung; có ảnh Pancake thì xếp bản chép ra sau, không có
thì vẫn giữ nó làm dự phòng. Ảnh Item không theo mẫu `sp-` vẫn đứng
đầu. Ca hồi quy phải có cả nhóm nhiều size dùng chung một tệp.

## 12/10/2026 - Lý do mã hỏng phải ưu tiên hơn phép so số giảm (#462)

Khách đã thấy giảm, nhưng mã vừa hết lượt hoặc đã dùng thì lần gửi
đầu chỉ nhận `uu_dai_doi`, không biết mã đã hỏng. Nguyên nhân là so
`giam_da_xem` trước khi trả `uu.ly_do`. Cách phòng: vẫn tìm đơn trùng
trước mọi từ chối, nhưng sau khi tính lại thì lý do của mã phải ưu tiên;
cả hai trang hiện nguyên câu và bỏ mã hỏng khỏi ô. Ca kiểm phải chốt
ngay lần gửi đầu không ghi đơn, không gọi Pancake.

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

## PR #295: bàn giao dùng chung và tra cứu

Chỉ owner sửa bản bàn giao issue trên nhánh đã claim, reviewer gửi delta
trên PR. Mẫu mới thay mẫu cũ, không giữ hai nguồn song song. Hiện trạng có
ngày/SHA nằm trong bản issue, không chép vào quy trình bền. Giữ dấu cách
trước số (Issue 294, PR 281) để rg theo tên thông thường không bỏ sót.

### 12/09/2026 - Lời nhắc quyền cấn cọc issue 247

Ẩn nút trái quyền là đúng nhưng người lập vẫn cần biết ai thực hiện bước tiếp. Thêm lời nhắc thụ động, không biến thành nút giả. Kiểm cả hai màn với hai vai: kế toán có nút, người lập có lời nhắc.
### 12/09/2026 - Combo issue 283: giữ lý do từ máy chủ

Lọc bỏ dung_duoc=0 phía quầy làm mất lý do hết giờ/sai quầy rồi báo nhầm thiếu cấu hình. Giữ kết quả và chặn ở đường bấm chung. Thẻ xám vẫn bấm để giải thích nhưng không thêm món; kiểm cả mã KMCB lẫn thẻ, thiếu cấu hình và combo hợp lệ.
## #290: tách đơn nháp kẹt khỏi nghĩa vụ HĐĐT đã ghi sổ

Nháp kẹt kho/duyệt không được giữ cả ngày sau không phát hành. Chỉ tờ đã ghi sổ chưa có HĐĐT giữ hàng rào ngày cũ; các cờ đối chiếu và lỗi đọc vẫn giữ nguyên. Combo nháp cũ cần lưu trước submit vì core đặt docstatus=1 trước validate. Khi chuẩn bị có thể ghi DB, lỗi chuẩn bị cũng phải rollback trước khi chạy đơn kế. Thời điểm modified cùng lịch đồng bộ chưa chứng minh trường người nhập bị hàm đồng bộ xóa; cần ca gọi thật và Version diff.

### 12/09/2026 - B1 issue 290: ca kiểm phải giữ đường máy ghi đè

Ca giữ dữ liệu quà tặng đặt vgb_pt_do_may=0 và mock bảng thanh toán đã che sự cố. Lý do vẫn ở DB nhưng phương thức bị đổi khiến UI giấu nó. Phải đi qua thao tác người chọn, giữ nguồn máy trả dữ liệu có thật, chạy validate và reload; kiểm cả phương thức lẫn lý do. Không nhận modified cùng giờ là bằng chứng cột nào đã bị xóa.

### 12/09/2026 - PR291 B1-3: cửa ghi tắt phải đi qua chốt nghiệp vụ

Chốt validate không bảo vệ được API dùng db.set_value. Chuyển sang Hàng tặng phải qua Document.save để chặn dòng tiền tay trước DB, thay vì ghi trạng thái kẹt cho lần sau. Không dùng helper đọc nuốt lỗi làm hàng rào an toàn.

### 12/09/2026 - Tắt chính sách không được che trạng thái cần dọn (#291)

Nháp tặng đã mang kho/64181, khi tắt công tắc cùng lúc đổi thành thu tiền, hạ dấu trước làm nhánh return bỏ qua dọn kho. Dọn chuyển loại trước khi tính dấu mới; ca thuần bắt update_stock còn 1, ca bench lưu-ghi sổ-hủy và đọc GL/SLE/Bin. Nguồn finding 3996732355, cùng lỗi 3996733712 trên nhánh tích hợp #293.


### #296: gom cửa lưu không được làm yếu đối soát quầy

Quầy kiểm cả tiền SePay và quyền sở hữu dòng giao dịch, trong khi đường Sales có nguồn đối chiếu khác. Khi gom điều kiện vào _chuan_bi_ghi_so, giữ nhánh nguồn và kiểm bằng lời gọi API thật. Cửa Lưu đơn chỉ save nháp; quyết định duyệt được commit riêng trước bước ghi sổ có savepoint để lỗi kho/GL không xoá quyết định. Ca bench mới cố tình lỗi sau GL/SLE, phải đọc lại nháp và hai sổ rỗng. Chưa coi ca mô phỏng là bằng chứng đã chạy bench.

### #296 ngày 13/09: hộp mùa vụ và khôi phục bill hủy

- Hộp nhận vỏ từ nhà in; ruột đã tính ở bánh lẻ. Ẩn Bếp làm ở dòng hộp và chặn cả hai tên ô API, vẫn cho sửa về 0. Không tự sửa dữ liệu lịch sử.
- Bill hủy có thể đã được thay thế bằng bill nhận cùng sao kê. Gỡ dấu hủy phải kiểm chủ trước, giữ dấu và lịch sử nếu giao dịch đã có bill khác nhận.
- Kiểm quyền UI bằng cách chạy màn Doanh thu Sales thật trong DOM giả với Sales User và ba vai kế toán/quản trị; kiểm nút đã render, không chỉ helper quyền.

### #299: chốt ca chỉ đếm tiền mặt cần nhận biết phiên bản máy chủ

JSON chỉ có Tiền mặt vẫn hợp cú pháp của backend cũ nhưng biến chuyển khoản/thẻ thành thiếu tiền. UI phải đọc chi_dem_tien_mat trước khi cho chốt. Không dùng flt để xác nhận số đếm: chữ sai biến thành0, NaN/Infinity qua so sánh âm; chuỗi5.000 phải đọc là5000 hoặc chặn, không âm thầm nhận5. Giữ các phương thức được cấu hình dù số máy bằng0. Ca API mở-chốt-reload giữ số nộp quỹ, Node kiểm backend cũ và payload. #290D2: báo cáo CK đọc cùng mã Pancake với ghi sổ, chọn một đường khớp, không cộng hai lần cùng tiền.

### #298 thư NCC: đầy đủ người nhận và không nhận xếp hàng là đã gửi

Email Supplier, Contact chính và mọi Contact Email liên kết đúng NCC phải được gom, bỏ trùng rồi chia To/CC. Gửi thử chỉ một địa chỉ. Bản sao kế toán là queue riêng, tiêu đề có BAN SAO; UNC mang mã APP và không gửi khi không đọc được tệp. Frappe 16.27.1 email.sendmail tạo Queue trong transaction; dùng delayed=True, giữ hai queue và dấu hồ sơ nguyên tử, không SMTP trong POST. Retry không tạo lại queue. Bằng chứng phải đọc recipient status; cờ email_da_gui lịch sử không chứng minh Sent. Bench đọc MIME/queue thật, stub duy nhất cấu hình SMTP và cấm EmailQueue.send.

Email CC gõ sai chỉ chặn gửi thật, không chặn tạo/đọc APP. Snapshot email chính giữ riêng; danh sách đã gửi dùng Small Text để không mất địa chỉ khi vượt 140 ký tự. Xem thử thiếu UNC vẫn mở kèm cảnh báo. Validation dự kiến không tạo Error Log/popup thừa; thư Error phải xử lý queue cũ. Bench dựng Email Account object đầy đủ, không thay bằng None vì lõi đọc always_bcc. Nguồn: review 5650925436 và run 34736267340.

### #298: quyền kế toán không phải giao của hai nhóm vai

Gọi _kiem_quyen bán hàng rồi kiểm Accounts làm kế toán độc lập thấy nút nhưng bị từ chối. Bỏ lớp bán hàng khỏi cửa ghi sổ riêng; Sales/Guest vẫn bị chặn. Ca cũ stub _kiem_quyen nên xanh giả: nạp hàm thật làm bản cũ đỏ hai assertion (Accounts User/Manager); thêm bench User thật, ghi sổ và đọc GL. Nguồn review3998728970.

Cửa ghi sổ qua được chưa đủ: nút từng đơn còn gọi luu_xhd trước chot_mot_don, màn danh sách/cấu hình/tìm đơn cũng qua quyền đọc. Review5651172671 dẫn tới ca kiểm 8 API ở 6 vai; bản cũ đỏ16 assertion của kế toán. Dùng cửa đọc/lưu riêng cho Sales hoặc Accounts, giữ ghi sổ chỉ Accounts và OTP đổi ngày như cũ; bench đi luu_thanh_toan -> luu_xhd -> chot_mot_don, đọc GL thật.
# Quyền kế toán sau ghi sổ

- PR298: kiểm trọn cả bước phát hành lại khi lần tự động chưa gửi được. Cổng lưu và ghi sổ đúng vẫn chưa đủ nếu nút phát hành lại còn dùng tập Sales. Kiểm User Accounts độc lập tới cửa mạng bị chặn trong bench, không gửi hóa đơn thật.

## 13/09/2026 - Lô thiếu số lượng không chứng minh giá vốn sai (#206)

Ảnh cũ PSX-2026-00061 báo thiếu 102.862 g ở một lô; đọc site mới thấy phiếu nháp đã chia đúng hai lô. Phải đọc lại chứng từ trước khi sửa theo ảnh. ERPNext v16.28.0 `serial_batch_bundle.py:prepare_batches` hỗ trợ giữ Batch và dùng Moving Average qua `do_not_use_batchwise_valuation`; không kết luận phải bỏ Batch từ lỗi số lượng. Kiểm riêng SLE theo lô và giá trị xuất với hai giá nhập khác nhau, có đối chứng cờ tắt/bật. Nguồn: Issue206 comment5651811587 và ba ca Khải trong `thu_san_xuat_206.py`. Chưa có quyền đổi cấu hình/danh mục từ lời khuyên của bot.

## 13/09/2026 - Cảnh báo hạn phải khớp loại chứng từ (#206)

Mở chốt HSD riêng StockEntry không đồng nghĩa mở Purchase Receipt hoặc API nhận mua. Mỗi cửa cần ca insert/submit riêng. Dùng câu cảnh báo trung tính khi mở rộng từ xuất sang nhập, giữ tương thích tiền tố ghi chú cũ để không lặp câu qua save. Bản thử PR302 giữ công tắc và kiểm serial/lô tắt; không đổi HSD hoặc sổ lịch sử để né core.

F4 review5652321851: core miễn HSD cho cả Material Issue và Material Transfer. Mở rộng danh sách wrapper không được vô tình siết lại khi bật công tắc. Kiểm ma trận loại phiếu x công tắc x lô tắt ở cả hai wrapper, thêm SLE/huỷ thật cho hai luồng. Câu cảnh báo không nói công tắc tắt khi luồng được miễn hạn với công tắc bật.

### #302: chặn hạn có thể nằm ở lúc tạo Batch

Chuyển cảnh báo ở Stock Entry và API nhận mua chưa đủ: ERPNext de591661 Batch.set_expiry_date còn ép HSD khi Item.has_expiry_date bật, hoặc tự cộng shelf life. Phải kiểm tới Batch vừa tạo và SLE, không lấy thuộc tính han_su_dung gắn tạm lên Purchase Receipt Item làm bằng chứng HSD đã lưu. Khi đọc sổ kho thô để thấy lô disabled, phải trừ lại cả giữ POS và Stock Reservation Entry.
## 13/09/2026 - #303: kiểm lại phantom Gelatine trước khi đổi mã

Triệu chứng được báo là Mass sai nhóm. Repo đã từng sửa chính thức phantom bằng is_phantom_bom/is_phantom_item và dựng lại bảng nổ. Không chỉ đổi is_stock_item hoặc tên Powder: phải đọc BOM con/cha, bảng nổ và tiêu hao thật. Công cụ chẩn đoán chỉ nhận mã cụ thể, thiếu mã dừng, không chạy truy vấn bảng con không lọc khi BOM rỗng.

Ngày13/09 đối chiếu live #303: Mass đã là phantom,34/34 dòng cha hoạt động đúng và không còn lá Mass trong bảng nổ. Không lấy ảnh/cấu hình cũ làm lý do tạo mã mới. Báo cáo phải gắn trạng thái BOM đã huỷ/đang chạy để tránh nhận lịch sử là lỗi hiện tại; ca công cụ phải được đăng ký vào chay.py, không chỉ chạy riêng.

### #300: ảnh lịch sử không lấy từ danh mục đang bán

Nguồn chọn món lọc disabled/is_sales_item và giới hạn số dòng, nên không dùng
nguyên danh sách ấy để tìm ảnh đơn cũ. Tra Item.image theo đúng mã ở các đơn
đã lọc số điện thoại, gom một lô; tập rỗng không truy vấn. Ca kiểm đưa đơn của
số gần giống và số rác vào cùng phản hồi Pancake để giữ ranh giới khách.

### 13/09/2026 - Lô và HSD chỉ cảnh báo, tồn kho không bao giờ âm

Đổi chính sách thì phải đổi ca đối chứng đúng đại lượng: 50 tốt + 280 quá hạn + 100 lô tắt nay là 430 khả dụng. Xin500 vẫn phải thiếu70; xin400 cần dùng70 từ lô tắt và lưu cảnh báo. Gói Desk cấp chưa đủ lượng dòng phải được bù, không biến kiểm tổng lượng gói thành một chốt mới chặn người dùng.

### 13/09/2026 - HSD ở phiếu nhập nháp, #302 F16

Thuộc tính han_su_dung trên dict PR Item không có trong meta nên nhập/xóa ngày trên app không tới Batch. Kiểm payload UI chưa đủ: phải đọc Batch.expiry_date sau submit. Cửa mới phải giữ quyền Document, retry cùng phiếu và rollback lô nếu submit lỗi; không sửa HSD lô có sổ kho. Đọc cả inline review mới sau khi chuyển Ready, không coi biên nhận cũ là chốt cuối.

- #302 F17: get_doc(dict) rồi đặt name không có nghĩa là bản mới được save theo đường insert. Bench ném Batch not found trước submit. Phải insert rõ nhánh mới. Hai số qty và sl cùng payload vẫn cần một nguồn chốt; một Batch không thể nhận hai hạn theo thứ tự dòng. Không dùng throw cho lô lịch sử/gói nếu chỉ cần giữ nguyên ngày và cảnh báo.

- #302 F24: đọc dữ liệu thất bại không phải giá trị rỗng. API cần trạng thái giữ riêng với xóa chủ động; kiểm cả lô chưa có SLE vì guard lịch sử không bảo vệ nó. Ca UI mock lỗi/thiếu phải theo tới payload, ca bench đọc lại ngày DB.

- #302 F26: khóa bản DB rồi vẫn get_doc(payload) chưa bảo vệ giá/quy cách/ngày. Dùng bản DB, chỉ áp trường thao tác đã cho phép; giá tạm tính từ nguồn cùng công ty/tiền tệ trên máy chủ. Câu cảnh báo quá hạn ngưỡng0 phải đổi cả trạng thái dat trước khi gọi hàm dựng câu.


## 14/09/2026 - Issue287: một pending làm đứng Telegram gần9giờ

Dấu gửi lúc15:54 ngày13/09 không có receipt; mọi lượt sau dừng toàn kênh.
Run34772786863 sau gỡ đúng pending theo duyệt đã gửi30tin, giữ cursor/seen.
Bản sửa cho phép một lần gửi lại sau10phút bằng đồng hồ ghi_luc; at là giờ
sự kiện nên dùng nó với backlog sẽ gửi trùng sớm. Telegram OK phải ghi mã
biên nhận trước khi đóng pending; PUT lỗi chỉ retry cùngSHA hoặc nhận đúng
nội dung đã ghi. Hai lần mất phản hồi giữ vết cần đối chiếu, không gửi vô hạn.
Seen/entity/cursor/receipt nhóm tách riêng để nhóm lỗi không làm mất tin riêng
và ngược lại. Đây chỉ là đánh đổi cho thông báo đã duyệt, không dùng choHĐĐT.


Issue287/PR312, review F1: nguồn release bị sửa hoặc gỡ làm key cũ mất.
Nhóm chỉ nhận features hợp lệ nên không dùng fallback kỹ thuật như chat
riêng; giữ vết cần đối chiếu và kiểm cả đường lỗi nhóm, không chỉ lỗi riêng.
#300 review: ngày Pancake phải qua ngay_pancake.ngay_tu_iso, không cắt chuỗi
UTC tại trình duyệt. Ảnh mã có hậu tố size phải thử mã gốc sau mã thô; ca kiểm
giữ riêng ảnh chính xác và ảnh dự phòng. Nguồn Claude run34771893366.

### #301: callback sau commit và danh từ trẻ em

Frappe enqueue_after_commit chỉ chuyển lệnh xếp Redis vào callback; lỗi ở
callback không nằm trong try của after_insert. Bao đúng callback sau commit
để không trả lỗi đặt bàn sau khi phiếu đã lưu. HTTP200 từ Lark vẫn có thể
mang mã lỗi nghiệp vụ; cần đọc cả mã trước khi nhận gửi thành công.
Bộ soi xưng hô từng bắt nhầm tre_em và "trẻ em". Chỉ loại danh từ/tên trường,
vẫn có đối chứng bắt "trẻ em cần ghế, báo em nhé", không miễn cả tệp.

### 14/09: tag trạng thái cũng khởi động bot

Workflow claude.yml kiểm contains(body, '@claude'); câu chỉ báo trạng thái
vẫn vào lượt bot. Không giải quyết bằng thêm câu "không cần làm" sau mention.
Chỉ mention khi giao việc; đạt thì chốt SHA không gọi lại. Một comment mỗi
sự kiện, delta review và bằng chứng theo SHA theo docs/van-hanh-agent/tiet-kiem-token.md.
Đây là quy tắc vận hành, chưa thay trigger hoặc khóa số lượt bằng workflow.

## 14/09/2026 - Issue 308: kiểm đủ vòng vét mã thay

Một hàm có vét lô cảnh báo cho mã gốc chưa chứng minh mã thay cũng được vét.
Ca kiểm phải gọi gan_lo qua trường hợp mã gốc hết và mã thay chỉ có lô cảnh
báo, giữ thử cả giới hạn kho, mã được duyệt và tồn đã chọn tay. Trước sửa
ba ca đỏ; sau sửa các ca thuần đạt. Chứng từ thật/SLE/giá vốn/huỷ phải chờ
bench riêng, không suy ra từ ca thuần.

- Issue308 bench: tạo Item Alternative thật cần Item gốc cho phép thay thế
  (allow_alternative_item). Lỗi fixture trước insert/submit không chứng minh
  luồng ghi sổ. Ca chống trừ trùng chọn tay cần nhu cầu vượt phần còn lại;
  chỉ thử vừa đủ không bắt được việc bỏ phép trừ.

- Kiểm giá trị kho sau huỷ: cộng stock_value_difference của cả dòng SLE đã
  huỷ không tương đương tồn hiệu lực. Đọc is_cancelled theo core và đối
  chiếu Bin actual_qty/stock_value; không bỏ assertion giá trị để cổng xanh.

## 14/09/2026 - Issue 307: máy GitHub Actions không clone được lõi ERPNext

Bản Claude chạy trên Actions bị chặn mọi đường ra mạng (git clone, gh api,
WebFetch), nên không dán được nguyên văn hàm lõi như AGENTS.md mục 5 đòi.
Không được suy từ trí nhớ thay cho trích dẫn. Cách làm: đặt tên ô lõi ở
một hằng duy nhất, hook kiểm meta trước khi ghi, patch dừng migrate nếu ô
không có, và ghi rõ trên PR điểm nào chưa đối chiếu để người có bench
(checkout pinned) đối chiếu trước khi merge. Nguồn: #307, PR A.

## 14/09/2026 - Issue 307: tài khoản theo món không quay về kho, nhóm không leo cha

Anh Việt đọc lõi de591661: bật `enable_item_wise_inventory_account` thì
lõi tìm Item Default, Item Group Default, Brand rồi CHẶN chứng từ, không
lấy tài khoản kho làm dự phòng. `get_item_group_defaults` chỉ đọc đúng
nhóm trên hồ sơ món, không leo nhóm cha. Hệ quả: lưới đỡ phải gán cho từng
nhóm LÁ có món theo tồn, và trước ngày bật cờ phải có báo cáo "món ba nấc
đều trống" rỗng. Không đặt tài khoản ở nhóm gốc rồi tin là đủ. Bảng tên
nhóm và tài khoản thật phải đọc từ site bằng lệnh chỉ đọc và dán lên PR
duyệt, không suy từ trí nhớ. Nguồn: PR #316 comment anh Việt 14/09 chiều.

### #316: không suy công ty đích từ Account đầu vào
Validator truyền None vào kiểm công ty đã nhận Account Demo trong cấu hình BTP. Nếu lại suy công ty đích từ chính Account này, phép kiểm sau cũng tự hợp thức hóa lựa chọn sai. Lấy công ty mặc định độc lập, lọc cùng công ty ở patch và có ca gọi cửa validate thật với Account khác công ty.

## PR316: nhóm mua vào không đồng nghĩa tài khoản152

Theo chốt 14/09, công cụ và văn phòng phẩm dùng153; tài sản/dịch vụ không gán tài khoản tồn kho. Không tự bỏ theo tồn nếu đã có SLE kể cả đã huỷ. Lưu cấu hình BTP phải truyền giá trị mới vào bước nạp nhóm, tránh đọc lại cache cấu hình cũ; không đè tài khoản khai tay. Cổng phải giữ ngoại lệ có lịch sử cho Khải xử lý.

### PR316: fixture Item Default đã có dòng công ty

Bench48ffd469 chặn hai ca trước GL vì fixture append dòng công ty đã được Item.insert dựng. Dùng lại dòng hiện hữu hoặc thêm khi chưa có; đọc validate_item_defaults của lõi. Không gọi lỗi này là sai GL hay bỏ validation để làm xanh.


### PR316: kiểm chức năng tự điền trước khi kiểm GL

Bench gán tài khoản tay chỉ chứng minh lõi ERPNext đọc Item Default, không chứng minh Settings và chặng BTP chạy đúng. Ca phải lưu Settings thật và đọc lại món trước khi ghi GL. Khi đổi cấu hình cần giữ cấu hình cũ để nhận ra giá trị cần cập nhật; xoá trắng là lựa chọn phải giữ qua lần lưu tiếp theo. Patch không được báo hoàn tất nếu bộ nạp còn lỗi. Nguồn review4005553556/3564 và4005662193/2200.


### PR316: lưu Settings thật cần cả cấu hình nền

Bench3c31739d chưa tới BTP vì fixture thiếu tọa độ bếp mà Settings.validate bắt buộc. Khi kiểm on_update bằng save thật, dựng cả điều kiện nền của document thay vì tắt validator. Audit phải nói đổi cấu hình khi chặng giữ nguyên, không dùng chung câu đổi chặng. Nguồn run34853835218 và review5665332461.


### PR316: truy vấn tổng hợp trên Frappe mới
Bench e06eaa2c chặn lưu Settings vì get_all không nhận hàm SQL dạng chuỗi trong fields. Dùng SQL cố định với tham số cho phép đếm nhóm; giữ ca bench đi qua Settings.save để kiểm truy vấn thật, không chỉ helper. Hai lượt cũ 217/219, rollback sạch; chưa dùng làm bằng chứng GL đạt.

PR316 bổ sung: rà toàn app các fields có SUM/COUNT khi gặp lỗi hàm gộp. Báo cáo cổng còn SUM dạng chuỗi, đã sửa và thêm bench execute đọc tồn từ Bin sau nhập/huỷ thật. Scan 14/09 không còn mẫu này trong code chạy, chỉ còn chuỗi đối chứng test.
### #317: lô chuyển khoản không phải mã giao dịch ngân hàng
`ma_gd` là Link Bank Transaction. Ghi mã tạm vào đây làm lẫn việc chuẩn bị chuyển và tiền đã ra. Dùng `lo_chuyen` riêng; một tài khoản thụ hưởng một lô, chỉ ghi mã giao dịch thật khi khớp tổng. Các phiếu đã vào lô không được khớp lẻ. Cần bench thử lại và lỗi giữa chừng trước phát hành.

### #317: cấp duyệt phải đi theo loại nghiệp vụ, không chỉ theo số tiền

Một hàm chỉ nhận tổng tiền đã đẩy cả Chi phí và Hoàn ứng lớn lên giám đốc, dù quy trình mới chỉ giữ cấp này cho Tạm ứng. Hàm chọn bước phải nhận cả loại nghiệp vụ; patch chỉ chuyển các phiếu chưa chi đang Chờ giám đốc, ghi lý do và không chạm phiếu Đã chi hoặc Đã huỷ. Uỷ nhiệm chi cũng phải chốt đồng thời đúng người nhận và phương thức: chỉ trả nhà cung cấp bằng chuyển khoản mới bắt buộc, hoàn tiền nhân viên dùng chứng từ mua. Nguồn: Issue #317 và PR #318.

## PR318: bàn giao Cloud và nút quay lại

Có commit trong tác vụ Cloud chưa đồng nghĩa nhánh PR đổi. Ngày 14/09, bản Cloud chỉ lên GitHub sau thao tác Update branch; phải kiểm SHA remote. Bản đó còn APPVER493 trong khi patch492 và chỉ sửa nút chân màn. Kiểm lại bundle/patch và chạy cả nút đầu màn, chân màn, API lỗi; không nhận có chuỗi nút là bằng chứng điều hướng.

### PR318: biên nhận khác với số tệp và chuyển bước phải chuyển việc

Một biên nhận có thể nhiều ảnh; số URL không phải số chứng từ. Giữ kiểm cùng số hoá đơn/MST/ngày, yêu cầu ít nhất một tệp, không chặn hai mặt của cùng biên nhận. Patch chuyển trạng thái phải giao lại ToDo bằng cửa giao việc chung (không bắn chuông migrate), không chỉ sửa nhãn. Hướng dẫn duyệt và dữ liệu người lập phải đúng cả danh sách chính lẫn lịch sử. Nguồn inline review4005492308/4005492320/4005492328/4005635209.


### PR318: hoàn ứng cũ và quyền YCPS
Ngoại lệ dựa trên phiếu nguồn đọc từ DB (đã chi, cùng người, quy tắc cũ, thiếu YCPS), không nhận cờ client. Kế toán phải ghi lý do trước đổi trạng thái. Picker chỉ trả thông tin cần chọn của owner hiện tại, không cấp quyền đọc toàn bộ DocType để chữa lỗi chọn phiếu.

PR318 F7/F8: tổng hoàn ứng có thể vượt số ứng nhỏ hợp lệ. Kiểm số ứng từ bảng kê nguồn, cho kế toán xử lý có lý do, không mở ngoại lệ mọi nguồn mới thiếu YCPS. Tham chiếu bị xoá không được làm màn chi tiết chết; trả không hợp lệ và giữ đường sửa.

### PR318 F12 - fixture bị chính luật mới chặn
Ngày15/09, bench332733a6 có4ca chưa tới assertion vì helper tạo Chi phí mới trên500k. Dựng snapshot thử dưới trần rồi cập nhật dòng trong savepoint, xác nhận số tiền saureload, giữ save/duyet thật ở bước được kiểm. Không tắt validator, không nhận ca đỏ lúc dựng là bằng chứng nghiệp vụ.

### PR318 - kiểm tồn tại trước nạp chứng từ đã mất
Bench cd453810 đạt220/221: get_doc nạp controller trước khi báo thiếu phiếu, DocType stub không có module gâyImportError. Kiểmexists trướcget_doc để đường thiếuphiếu hoạt động; không bắtmọiImportError vì sẽ che DocType cònphiếu nhưng cấu hìnhhỏng.

### PR318 F13 - đường thay phải có nút và xoá dữ liệu sót
Máy chủ cho thay YCPS không đủ nếu Hoàn ứng không có picker. Cờ nguồn không hợp lệ phải từ máy chủ, hiện nút theo cờ, xoá lựa chọn khi đổi loại/đổi nguồn. Ca DOM bấm chip thật và kiểm cả hiện/ẩn theo cờ, không chỉ dò chuỗi HTML.

### PR318: chốt duyệt phải bảo vệ cả đối soát chung

Phiếu Chờ kế toán từng có thể đi tới khớp tiền qua cửa chung dù cửa duyệt yêu cầu lý do ngoại lệ. Chỉ lọc danh sách không đủ vì API theo mã bỏ qua danh sách. Thêm kiểm trạng thái chứng từ tại cửa khớp tay chung và tự động, trước khi đọc/ghi giao dịch; bench gọi cả cửa riêng lẫn cửa chung, chốt trạng thái chưa đổi. Không sửa luật các luồng khác khi bổ sung callback tùy chọn.
### Telegram xin duyệt: link không thay phương án
Anh Việt không biết tìm quyết định trong comment kỹ thuật. Khối telegram-approval
chỉ chuyển nội dung chủ repo soạn riêng (việc, đề xuất, ảnh hưởng, câu hỏi),
không tự sao chép toàn comment hoặc log. Kênh vẫn một chiều; không nhận là đã
có phê duyệt từ việc gửi tin hay phản hồi chưa được xử lý.

### PR318 F20/F21: thay điều kiện phải có đường chỉ dẫn

Ẩn khớp sao kê trước duyệt phải giải thích bước tiếp cho kế toán. Patch cấu hình series phải kiểm trường tồn tại trước truy cập options, vì DocType tồn tại không chứng minh trường còn tồn tại. Hai đường có ca hồi quy trong delta F20/F21.

### PR316/318: tích hợp phát hành phải giữ cổng của cả hai

Khi cùng thêm import bench hoặc patch cuối tệp, giữ cả hai suite và thứ tự phiên bản. Đợt này YCPS thuộc v492, mapping nhóm món thuộc v493. Ca kiểm patch307 phải xác nhận đứng trước v493, không còn bám v492; dựng bundle từ nguồn và chạy lại toàn cổng trên nhánh tích hợp.

### PR316/318: quyền tệp mới khác quyền xử lý chứng từ cũ

Kiểm người tải trên mọi lần đọc/duyệt làm kế toán bị chặn bởi biên nhận nhân viên đã lưu trước. So URL với bảng kê persisted từ DB; chỉ URL mới chưa gắn chứng từ cần đối chiếu chủ tải. Không lấy danh sách cũ từ client. Giao việc không có người nhận không phải lỗi cấu trúc dữ liệu: patch giữ trạng thái và dấu vết cảnh báo, không làm sập cả migrate chỉ vì giao=0.

### PR316 inline4011368627: chuyển bàn khi danh sách nhận rỗng

Giao việc trả sớm khi không có người nhận nên chưa đóng ToDo cũ. Patch đổi trạng thái cần gọi go_giao ở nhánh này để ToDo và _assign không còn trỏ giám đốc; giữ dấu vết Closed và cảnh báo cần giao lại.

## SePay: đổi generator vẫn có thể ghi đè dữ liệu cũ (#322)

Khi duyệt phiếu, code cũ sinh lại nội dung chuyển khoản vô điều kiện. Muốn đổi định dạng chỉ cho nội dung mới phải giữ trường đã lưu ở cả caller này, không chỉ tránh patch dữ liệu. Nhãn tài khoản cần gắn từng kết quả, số phiếu khớp không nói được nguồn tiền.

## PR323 - review F1/F2

Đẩy lọc bank_account xuống truy vấn trước limit500; ca dựng501 dòng của
tài khoản đông và một dòng tài khoản ít, kiểm dòng ít vẫn được lấy.
Chip dùng CSS chips/chip/on có sẵn. Chưa xử lý F3-F7 (quyền chẩn đoán,
escape kép, trạng thái/fallback, giới hạn danh sách, truy vấn nhãn trùng).
Không chốt sẵn sàng phát hành chỉ vì CI trước xanh.

## PR323 F3-F7

Chẩn đoán tài khoản chưa nối chỉ trả vai kế toán/quản trị. Truyền nhãn
đã đọc vào truy vấn sao kê, không đọc lại. Ca gọi ung_vien kiểm hai vai,
tham số lọc và nhãn dùng chung. Bỏ escape kép ở nội dung đưa vào baoTin,
giữ câu Đã chi kể cả response cũ thiếu nhãn. Trả tối đa5 dòng đã khớp,
UI chỉ liệt kê khi tổng không quá5; các số đếm toàn lô giữ nguyên.
Cần Claude review và bench SHA mới, chưa phát hành.
## 15/09/2026: tiền gốc phiếu nhập không phải phần còn được nối (#252)

Màn so sánh đã trừ lượng hóa đơn khác ghi sổ nhưng danh sách phiếu vẫn in
số tiền gốc không có nhãn. Người dùng cộng các số đó và tưởng bộ nối chặn sai.
Giữ hàng rào lượng, ghi rõ tiền gốc và phần còn từ cùng nguồn lượng máy chủ;
hướng dẫn kiểm đầu nối hóa đơn đã dùng trước. Không lấy triệu chứng này làm
căn cứ tự sửa chứng từ đã ghi sổ hoặc bù thêm kho.

PR321 review inline: số tiền còn lại trên phiếu có thể gồm món thừa hoặc khác đơn vị. Không gọi tổng này là số nối được; phải phân biệt số dư với điều kiện ghép từng dòng.

PR321: bộ chuẩn hóa tiền có thể đặt qty1 khi thiếu đơn giá; không tái sử dụng qty đó làm lượng nguồn. Kiểm nguồn phải xét cả dòng bị bỏ khỏi chứng từ, không chỉ những dòng còn lại.

PR321 audit: tên Item cũ khác tên NCC không chứng minh mất dòng. Chỉ phục hồi căn cứ bằng mapping duy nhất, và vẫn kiểm lượng; không dùng tổng tiền để suy tên.

## PR321 - chỉ cảnh báo theo chốt anh Việt 15/09/2026

Chỉ dẫn mới thay thiết kế chặn lượng ở các commit trước: kiểm lượng nguồn
không chặn lưu/ghi sổ, kể cả thiếu nguồn hoặc lỗi đọc. Hiện cảnh báo có
đường mở Purchase Invoice để sửa tay theo quyền và vòng đời chứng từ hiện có.
Không tự thay qty/rate/đầu nối hoặc bỏ kiểm lõi ERP. Ca tích hợp được đổi
sang Document.submit thành công, docstatus1 và có GL dù lượng nguồn lệch.
Cảnh báo phiếu nhập còn lại ẩn khi đã khớp. Cần bench và Claude review
trên SHA mới; không dùng cổng xanh của thiết kế chặn cũ để chốt bản này.

PR321 review e6a16cdd: dùng get_url_to_form của Frappe cho đường sửa tay, escape thuộc tính href. Bench e6a16cdd đã xanh; bản sửa URL phải kiểm lại. Cảnh báo popup có giới hạn với submit nền/hàng loạt, chưa có cảnh báo lưu trên chứng từ. Không coi popup là bằng chứng mọi nhân viên đã đọc.

### Cảnh báo phải hướng dẫn đúng nguyên nhân

Không nhận diện được tên/mã nguồn chưa chứng minh lượng hay giá sai.
Hướng dẫn sửa lượng chung cho mọi lý do có thể khiến nhân viên sửa một
chứng từ đúng. Nêu món, hướng dẫn đối chiếu nguồn/ánh xạ cho nhóm này;
khử lặp và giới hạn số mục. PR323 F8/F9, bắt nguồn từ audit PR321.

### Nhóm nguyên nhân không phụ thuộc câu chữ

Không dò chuỗi tiếng Việt để chọn hướng dẫn: sửa văn phong có thể làm mất
hướng dẫn cho đúng nguyên nhân. Giữ nhóm có cấu trúc cùng câu hiển thị;
ca kiểm thay câu vẫn nhận đúng nhóm và lỗi đọc nguồn có hướng dẫn riêng.
PR323 F12.

### Tách cảnh báo thao tác khỏi báo cáo chất lượng dữ liệu

Thiếu ánh xạ tên nguồn không nên bật popup mỗi lần ghi sổ. Theo duyệt
F10, chỉ nhóm lượng/quy cách bật popup; báo cáo chung đọc lại dữ liệu hiện
tại và giữ quyền chứng từ. Phân trang phải báo rõ còn dữ liệu, không gọi
trang rỗng là toàn hệ thống đã sạch. PR323.

### Catching an exception does not clear Frappe messages

frappe.throw can append a client dialog before raising. A read-only scan
that catches it must mute messages in a scoped try/finally and restore
the prior flag. Test message_log on the real resolver, not only returned
errors. Applies to source report and advisory submit hook, PR323 F16.

## Issue 325 và PR 327: chip lọc theo mapping, nhưng KHÔNG giấu dòng sao kê

Màn khớp SePay thủ công từng in cả danh sách tài khoản chưa nối bằng join, dài ba màn hình và đẩy dòng sao kê xuống dưới. Bản sửa đầu đi quá tay: lọc luôn ứng viên theo mapping ngay trong truy vấn. Đó lại đúng hình dạng lỗi ngày 14/09/2026 với phiếu TTNB-26-09-02113, dòng có thật biến mất mà màn báo là không có giao dịch nào.

Luật chốt: cửa ĐỌC không giấu dòng nào. Dòng chưa dùng được vẫn trả về kèm dung_duoc = 0 và vi_sao_khong, để mờ và xếp cuối bảng. Chặn nằm ở cửa GHI, dùng CHUNG một hàm cho cả khớp tự động lẫn khớp tay: hai đường ghi áp hai luật khác nhau còn khó hiểu hơn cả việc giấu dòng. Chip chỉ là bộ lọc người dùng tự chọn, không phải bộ lọc ngầm của máy.

## 16/09/2026 - Đếm vòng agent bằng lượt thực thi
Không dùng comment hay run created_at làm bằng chứng model đã chạy: skipped
không tiêu lượt, rerun của run cũ có thể bắt đầu hôm nay. Gate đọc mọi attempt
và started_at bước model theo PR; API lỗi chặn chạy. Khóa này chỉ bao workflow
được tích hợp, không mặc định bao native Codex. Nguồn: PR sáu thay đổi agent.

### 16/09/2026 - PR327: kiểm đủ cửa ghi SePay và phản hồi UI
- Sau khi khóa ba đường đối soát cũ, `hoan_tien.sepay_tien_ra` vẫn là cửa trực tiếp chưa kiểm mapping. Cùng sao kê có thể bị chặn ở màn chọn mà vẫn ghi đã hoàn qua endpoint này.
- Endpoint nay phải đọc Bank Transaction tiền ra hợp lệ từ `ma_gd`, dùng nội dung/số tiền trong DB và qua phép kiểm tài khoản chung trước mọi ghi/sinh chứng từ. Không dùng payload làm bằng chứng tiền ra.
- Ba handler UI phải phân biệt lý do cấu hình với lệch tiền và trùng giao dịch. Kiểm callback thật bằng Node; kiểm endpoint thiếu sao kê, đã hủy, tiền vào, mapping tắt, hợp lệ và payload giả. Bench dùng tài khoản/mapping/hồ sơ thật, chỉ thay bước sinh chứng từ trong ca kiểm ranh giới này.

## #328: chip có ngân hàng nhưng danh sách bị giấu ở bộ lọc nghiệp vụ

MB0615 có35 dòng tiền ra trong45 ngày, API TTNB trả0 vì `ung_vien` dùng lỗi nguồn chi làm `continue`. Không suy ra thiếu đồng bộ từ bảng rỗng. Tầng đọc phải giữ dòng và lý do; cửa ghi vẫn kiểm nguồn. Trần500 trước tìm kiếm có thể bỏ mất dòng đúng: đọc trong khoảng/tài khoản đã chọn, tìm và xếp trước phân trang60, trả tổng và trang tiếp. Gợi ý tiền không được biến thành xếp độ lệch tiền rồi bỏ qua ngày. Ba màn TTNB/APP/hoàn tiền dùng cùng cửa đọc và cùng màn chọn, giữ cửa ghi riêng.

### 16/09/2026 - Webhook phải báo lỗi khi chưa lưu sao kê (#335)

Không dùng success để dừng retry sau lỗi insert/submit: như vậy SePay không
biết cần gửi lại, còn Frappe có thể commit POST đã bị nuốt exception. Rollback
trước khi trả 503; sao kê Nháp cùng mã không phải bằng chứng nhận thành công.
Không có mapping phải báo chưa tiếp nhận. Frappe bọc return trong message,
nên cờ success cần có ở gốc phản hồi theo giao thức SePay. Ca giả lập kiểm
submit lỗi, rollback, gửi lại, replay và gói sai; chưa thay cho kiểm HTTP/DB
đồng thời trên bench. Không suy từ danh sách UI rỗng là webhook thiếu dữ liệu.

## v500: gán thẳng workflow_state lên chứng từ MỚI là hỏng cả lượt lập
Bản v408 (03/09/2026 19:00) đặt `pe.workflow_state = "Chờ FIN kiểm tra"` ngay
trước `insert` trong `tra_truoc._dung_phieu`. Frappe soi đường duyệt lúc lưu,
mà với chứng từ MỚI thì nó không nhận bất kỳ bước chuyển nào, nên ném "Không
được phép chuyển trạng thái quy trình từ Nháp sang Chờ FIN kiểm tra". Hàm ném
lỗi thì cả giao dịch lùi: mất phiếu, mất tệp vừa đính. Màn Thanh toán trước
cho NCC chết đúng 13 ngày mà cổng kiểm vẫn xanh, vì không ca nào gọi thật
`tao_phieu`. Đo trên site: phiếu cuối lập được là APP-26-09-050 lúc 03/09
17:38, tức trước bản đó một tiếng rưỡi; sau đó 0 phiếu.
Luật: chứng từ MỚI thì lưu ở bước mặc định rồi gọi `apply_workflow(doc, <tên
nút>)`, không gán tay. Gán tay chỉ đúng với chứng từ ĐÃ CÓ. Và đẩy bước không
được thì GIỮ chứng từ lại, nói thật bước nó đang nằm, đừng ném lỗi huỷ sạch
việc người ta vừa làm.

PR336 review: apply_workflow trên Frappe16.27.1 nhận JSON/dict và nạp Document khác từ DB. Không truyền Document rồi đọc object cũ. Chuyển lỗi phải rollback savepoint riêng, phục hồi callbacks, reload DB và giao Nháp cho AP Officer; FIN chỉ nhận khi thực sự chuyển thành công. Ca bench tra-truoc-336 kiểm cả lỗi sau save.

## Issue339 - phân biệt hóa đơn được nối và hóa đơn được sinh

Khi cancel/amend PI, rà cả APP đang giữ liên kết, không chỉ PE/JE. Trả lại hồ sơ NCC không đồng nghĩa hủy PI. Guard chống bỏ rơi PI do hoàn ứng sinh phải xét nguồn, không chỉ docstatus của mọi dòng. Test xuyên nút/API/Document: PI hủy sau lập, trả lại, đổi sang bản amend và gửi lại, giữ nguyên GL và dư nợ.
## 16/09/2026 - TTNB trả nhân viên bằng quỹ 141 không phải công ty hoàn ứng

Triệu chứng: SePay đã có giao dịch, tài khoản cá nhân đã gắn quỹ 141 và đúng
chủ, nhưng nút khớp TTNB từ chối vì chỉ nhận tài khoản công ty. Luồng thực tế
anh Việt xác nhận trên #328 có hai lần chuyển: người ứng trả nhân viên, sau
đó công ty hoàn người ứng. Phân loại theo cờ công ty đơn lẻ làm chặn sai.
Phòng: kiểm tài khoản sổ cái và chủ quỹ; giữ riêng chứng cứ ở dòng APP với
giao dịch công ty trả ở đầu APP. Mã tham chiếu FT và tên Bank Transaction
phải được kiểm như cùng một dòng tiền để không hoàn trùng qua hai cách nhập.
Bằng chứng local và trạng thái bench nằm trong docs/pr-ttnb-hoan-ung-502.md;
không coi thay đổi quy tắc này là đã chứng minh toàn bộ sổ cái.
### 16/09/2026 - Ngưỡng một đồng: hai đường dựng chứng từ, hai cách tính (v502)

Hoá đơn ALOIN C26TAA số 1144, 260 x 1.576,92, thành tiền 410.000. Chứng từ
HDM-26-09-00040 vào sổ 442.799 trong khi hoá đơn ghi 442.800. Thiếu đúng một
đồng, không lớp nào kêu.

Hai chỗ cùng để lọt, sửa một chỗ vẫn sai:

- `minvoice_chung_tu.dung_hoa_don_mua` (đường DỰNG MỚI) cân tổng bằng cách
  nhân thẳng `qty * rate`, ra 409.999,2. Phần hụt chỉ thành một đồng SAU KHI
  máy lưu, vì ô đơn giá chỉ giữ hai số lẻ. Đường DỰNG LẠI trong
  `dung_lai_hddt` đã học bài này từ 27/08/2026 và dùng `tien_dong_may_ghi`,
  nhưng hàm đó chỉ nằm ở tệp dựng lại nên đường dựng mới không với tới.
- Phép nắn so bằng `chenh < -NGUONG_KHOP` với ngưỡng 1.0, mà -1,0 < -1,0 là
  sai. Ngưỡng ĐÓNG thì chênh đúng một đồng bị gọi là khớp.

Luật rút ra: khi phát hiện hai đường cùng làm một việc, đừng chỉ sửa đường
đang hỏng, hãy dọn phép tính về một hàm chung rồi cho cả hai gọi. Ba hàm
`tien_dong_may_ghi`, `muc_tieu_truoc_thue`, `ten_dong_bu` nay nằm ở
`minvoice_chung_tu` và `dung_lai_hddt` nhập lại.

Luật thứ hai: ngưỡng phải nói rõ HỞ hay ĐÓNG. `NGUONG_KHOP` của phép nắn là
ngưỡng hở (chênh một đồng là phải nắn) vì hai vế đem so đều đã là số nguyên
đồng máy sẽ ghi. `mua_dich_vu.NGUONG_LECH` của cổng chặn ghi sổ vẫn đóng, vì
nó soi một tờ đã có, có thể do người gõ tay, nới một đồng để đừng chặn oan.
Hai cái cùng giá trị 1.0 mà khác nghĩa, đừng gộp.

Bẫy khi chạy đột biến: bộ chạy đột biến phải khôi phục tệp trong `finally`.
Ngày 16/09 lượt đột biến thứ năm bị timeout giết giữa chừng và để nguyên bản
đã bóp trong cây làm việc, suýt nữa đẩy lên.

### 16/09/2026 - PR #337: tổng đã cân che mất đơn giá bị cắt

Bench precision #259 từng tắt policy rồi chờ tổng sai bốn đồng. Khi #337
cân cả phần chênh đó bằng giảm giá, tổng đúng nhưng đơn giá vẫn bị cắt.
Đối chứng phải kiểm chính đơn giá, thành tiền dòng và khoản giảm giá; không
chỉ nhìn tổng hoặc nhận mọi exception là bằng chứng. Giữ luồng bật policy
kiểm save/submit/GL/hủy, bổ sung hóa đơn lệch một đồng cả dấu dương và âm.

## Issue342 - dấu duyệt giữa hai cửa gửi
Đường lập và gửi ngay chỉ đặt trạng thái chờ GD, còn gửi nháp mới ghi dấu FIN. Dùng chung bước chuyển có dấu người/thời gian và kiểm tại cửa API trước insert. Thanh tiến trình không được suy chữ ký từ trạng thái sau cùng hoặc coi Hoàn tất là bằng chứng tiền đã ra.


## Issue342 - cấn đủ không được quay về tổng phải chi

Triệu chứng: sau khi cấn hết, nhánh xuất nội dung chuyển khoản dùng `con_lai or tong_tien` có thể yêu cầu trả lại toàn bộ. Chỉ dùng tổng khi giá trị còn lại thật sự thiếu; số 0 phải giữ nguyên và không sinh lệnh chi. Nguồn cấn phải có JE đã ghi sổ, cùng sổ141 và đúng công ty; việc đổi ánh xạ Bank Account không được mang nguồn cũ sang sổ mới. Kiểm cả JE + PE, PI outstanding, huỷ và retry trên bench. Ô nhập cấn dùng hàm đọc tiền chung giữ dấu âm, không biến khoản âm thành khoản dương.

### 16/09/2026 - Hàng vào điểm bán đều đặn mà không có đường ra (v507)

Quét sổ kho hai kho điểm bán trong một tháng: hàng ra khỏi Kho D1 và Kho Sales
Online chỉ có đúng 18 dòng, và cả 18 đều là điều chuyển sang kho khác. Không một
dòng nào là hàng đã dùng hay đã bán. Bao bì, công cụ dụng cụ, nguyên liệu pha
chế, bán thành phẩm đều không có đường ra. Khoảng 320 triệu treo lại.

Không ai báo lỗi, vì không có lỗi nào để báo. Nhân viên không bấm sai nút, họ
không có nút nào để bấm. Bài học: khi một phân hệ có cửa VÀO mà không có cửa RA,
sai sót không hiện ra dưới dạng lỗi, nó hiện ra dưới dạng một con số lớn dần
trong báo cáo tồn kho mà không ai nhìn. Trước khi dựng một màn nhập liệu mới,
nên đếm thử số dòng đi ra của đúng phân hệ đó trong một tháng.

Ba cái bẫy khi viết màn Xuất kho phục vụ bán hàng, đã chốt bằng ca kiểm:

- Ô `vgb_muc_dich_xuat` nay do BA màn dùng chung, vì cả ba đều đẻ ra Material
  Issue. Màn Xuất dùng nội bộ trước đây lọc kiểu "ô này có giá trị", giữ nguyên
  cách đó là danh sách của nó kéo luôn phiếu của màn mới sang. Mỗi màn phải lọc
  đúng mã của mình, và mã nằm ở một chỗ duy nhất là `xuat_kho.MA_PHUC_VU_BAN`.
- Nhóm món quyết định tài khoản ghi sổ, nên phải đọc THẲNG từ danh mục Món chứ
  không nhận nhóm app gửi lên. Tin app là mở đường cho một dòng bánh thành phẩm
  đi vào phiếu với nhãn "Bao bì".
- Đếm ra nhiều hơn số trên sổ không phải là tiêu dùng, đó là sai sót nhập hoặc
  sai sót đếm. Biến nó thành một dòng xuất âm là làm hỏng sổ kho và làm hỏng cả
  giá vốn bình quân. Chặn lại và chỉ đường sang Kiểm kê.

Và một bẫy của chính bộ kiểm: cổng kiểm có ca soi mọi chuỗi JS xem còn xưng "em"
không. Thẻ HTML `<em>` và bộ chọn CSS `.xpvo em` làm ca đó đỏ dù không có chữ
"em" nào trong lời thoại. Dùng `<span class="dd">` thay cho `<em>`.

## 18/09/2026: món dịch vụ trong danh mục bị bấm như món đếm cái

Phí giao hàng có sẵn trong danh mục là item "Phí Dịch Vụ Vận Chuyển" giá 1.000 đ.
Màn quầy chỉ cho cộng số lượng (giá không sửa tay theo luật 09/08), nên thu ngân
bấm 4 x 1.000 để ra 4.000 đ phí giao và hoá đơn điện tử chép y nguyên "4 cái".
Bài học: khoản tiền không đếm cái (phí giao, phụ thu) không được đi chung đường
với món; máy chủ gom về một dòng qty 1 ở MỌI đường ghi (`vagabond/phi_giao.py`),
màn hình hỏi số tiền thay vì thêm dòng. Sửa ở màn thôi là chưa đủ vì còn màn
Sales và màn sửa bill cùng gửi món.

## 16/09/2026 (#332, PR #333 và PR thay thế): tiền đúng lúc đồng bộ vẫn có thể sai sau khi thay dòng

Hoá đơn mua có liên kết hoá đơn điện tử gốc: người dùng xoá dòng rồi thêm dòng
để sửa mã, dòng mới mất tên NCC, kéo giá và quy cách của mã mới, ánh xạ cũ lại
trỏ vào Món đã ngừng dùng. Cách chữa: một cửa "Sửa mã theo hoá đơn gốc" chọn rõ
dòng nguồn và quy cách, giữ số lượng và đơn giá của nguồn, lưu ánh xạ và tờ
trong cùng savepoint, reload rồi kiểm cả dòng lẫn TỔNG TIỀN tờ trước khi báo
xong (hook dựng lại dòng có quyền đổi cả tờ, xem sự cố 27/08). Dòng nguồn gửi
kèm tên đã thấy lúc chọn, không tin chỉ số qua hai lượt gọi. Bài học kiểm thử:
ca kiểm mà doc.save chỉ ghi nhật ký thì khối kiểm sau lưu không bao giờ chạy
vào nhánh throw, phải cho save PHÁ doc rồi mới tin ca kiểm.

## 18/09/2026: ô chọn kho trên app nhớ lựa chọn sai, thành phẩm về kho Nguyên liệu

Khải chụp màn Tồn kho theo chặng: ba mã bánh thành phẩm nằm ở kho Pastry -
Nguyên liệu. Truy vết: lệnh LSX-180926-000201 có kho đích là Nguyên liệu vì ô
"Nhập thành phẩm vào kho" trên màn Tạo lệnh liệt kê MỌI kho bếp và nhớ lựa chọn
cuối vào localStorage; một người chọn nhầm một lần là mọi lệnh sau đều sai, mà
hook máy chủ chỉ điền ô trống, không sửa ô đã chọn. Bài học: giá trị do LUẬT quyết
(kho đích theo chặng) thì máy chủ phải tự sửa ở mọi đường ghi và nói rõ, ô chọn
trên app chỉ được đưa ra các lựa chọn hợp luật; màn theo dõi phải tự đánh dấu
"sai kho" chứ không chờ kế toán chụp ảnh hỏi.

Vòng 2 (19/09, Codex + bench CI): hook ghép tên kho đích với hậu tố " - TV" cứng,
rồi `if dung and frappe.db.exists(...)` mới đổi. Trên bench CI công ty là " - VK"
nên kho đích "không tồn tại", hook im lặng, phiếu đi tiếp vào kho sai, ca kiểm
thật đỏ mà ca kiểm thuần vẫn xanh. Hai bài học: (1) hằng số hậu tố công ty
không được ghép cứng trong luật, đọc từ chính tên kho đang xét; (2) một hook
sửa-cho-đúng mà gặp điều kiện không sửa được thì phải DỪNG chứ không được bỏ
qua, vì "bỏ qua" ở đây chính là cái lỗi hook sinh ra để chặn. Ca kiểm thuần
phải chạy thật hàm với db.exists trả False, không chỉ dò chuỗi.

Quyết định 20/09 (anh Việt): *"không cần chặn gì cả. Anh sợ chặn lắm rồi lại
phát sinh vấn đề. Cứ để hàng hoá thoải mái tự do lưu chuyển."* Nên: chuyển kho
tay, nhập tay vào kho bếp khác chặng chỉ NHẮC, không chặn; máy không đổi bếp
của hàng (món Pastry nằm ở kho Baker là việc của hai bếp), chỉ sửa chặng trong
cùng bếp và chỉ trên lệnh/phiếu sản xuất. Bài học: hàng rào "chặn" phải do
chủ tiệm chốt, mặc định của kỹ thuật là nhắc và làm hiện ra, không chặn.

## Sửa xong mà người dùng vẫn không tìm ra: đặt lối sửa ngay chỗ báo thiếu (v515, 21/09/2026)

v509 cho nhập số tài khoản nhà cung cấp, nhưng chỉ ở app, mục Danh mục > Nhà
cung cấp. Ba ngày sau Uyên vẫn báo "chưa tìm được chỗ nhập": màn Thanh toán
trước chỉ in dòng "chưa có số tài khoản" mà không có nút, còn form Desk thì
thẻ "Tài khoản ngân hàng" ở tab Kết nối không có nút thêm. Claude lại hướng
dẫn theo đường app trong khi anh Việt đang mở Desk, thành hướng dẫn sai chỗ.
Bài học: (1) màn nào báo thiếu một thứ thì màn đó phải có nút sửa thứ đó (nếu
người xem có quyền), hoặc nói rõ ai sửa và sửa ở đâu; (2) tính năng nhập liệu
phải có ở cả app lẫn Desk; (3) trước khi hướng dẫn, hỏi hoặc nhìn ảnh xem
người dùng đang ở Desk hay ở app.

## 21/09/2026 (#351): giao việc qua `assign_to.add` kiểm quyền của NGƯỜI GIAO

Khi dựng màn Việc hôm nay, đọc mã nguồn Frappe v16 trước khi dùng lại
`giao_viec.giao`: hàm đó gọi `frappe.desk.form.assign_to.add`, mà `_add` chạy
`frappe.get_doc(doctype, name).check_permission()` với quyền người đang bấm,
rồi `frappe.share.add` kiểm quyền CHIA SẺ của người đó (`add_docshare`:
`if not flags.get("ignore_share_permission"): check_share_permission`). Quản lý
cửa hàng, marketing không có vai Projects User nên cả hai bước đều hỏng trên
Task, và `giao_viec.giao` nuốt lỗi trả `{"giao": 0}`: màn sẽ báo "đã giao" mà
không ai nhận việc. Cách phòng: kiểm quyền nghiệp vụ ở cửa của mình, rồi tự ghi
ToDo và DocShare bằng quyền hệ thống (`phan_tich._gan_nguoi`), và coi số người
gắn được khác số người chọn là LỖI. Bài học chung: một hàm "không bao giờ ném
lỗi" là hàm mà người gọi phải tự đọc kết quả; gọi nó từ một nút bấm thì phải
kiểm số trả về, không được coi không lỗi là xong.

## 21/09/2026 (#356): User kiểm thử không vai bị Frappe hạ xuống Website User

Bench CI trên 0a8754e đỏ hai ca giao việc: tài khoản kiểm thử tạo với
`"user_type": "System User"` nhưng không có vai nào, và Frappe khi lưu User tự
đặt lại loại tài khoản theo vai (không có vai vào bàn làm việc là Website
User). Luật mới "chỉ giao cho tài khoản nội bộ" chặn đúng, nên ca kiểm đỏ
chứ code không sai. Cách phòng: User kiểm thử cần là nội bộ thì gắn vai thật
(ví dụ Projects User) và khẳng định `user_type` ngay sau khi tạo, để lần sau
lỗi dựng dữ liệu hiện ra ở dòng tạo User chứ không ở ca nghiệp vụ.

## 21/09/2026 - Đồng bộ đầu vào: lỗi đã bắt vẫn hiện modal

Frappe đưa local.message_log vào response dù caller đã bắt exception. Khi từng tờ lỗi đã được chuyển vào báo cáo, phải giữ log trước lượt và loại log riêng của tờ đó; không xóa thông báo toàn request. Rollback lỗi phải nổi lên, không để caller commit phần dở. Với hóa đơn âm, qty âm và rate0 cho tích -0; không dùng tích <0 làm tiêu chí duy nhất quyết dấu. Kiểm cả dòng quà0tiền và dòng mô tả trống trên PI thật. Nguồn issue227, nhánh codex/fix-minvoice-sync-20260921.


### PR352: lỗi giao dịch phải đi tới worker
Helper đẩy lỗi rollback nhưng wrapper scheduler bắt rồi trả bình thường vẫn có thể khiến worker commit. Kiểm hành vi ở điểm gọi scheduler: rollback và ném lỗi tiếp, kể cả rollback không thành công; không chỉ kiểm helper từng tờ.

## 22/09/2026 (#352): ảnh trong tờ in tải từ mạng ngoài thì có ngày mất, chữ vẫn in

Bill HDB-26-09-04366 in câu "Quý khách vui lòng quét mã QR ... để nhập thông
tin xuất hoá đơn" mà không có mã QR. Ảnh mã khi đó lấy từ api.qrserver.com;
đường in ngầm chỉ chờ khung tối đa 6 giây rồi chụp, đường trình duyệt gọi in
sau 0,9 giây, nên mạng ra ngoài chậm hay bị chặn là tờ in mất ảnh mà câu dẫn
vẫn còn. Cách phòng: thứ gì in ra giấy phải dựng được TẠI MÁY (thư viện nằm
trong repo, ảnh nhúng data:), và câu dẫn chỉ in khi có đúng thứ nó dẫn tới.
Mã QR thanh toán chuyển khoản (img.vietqr.io) vẫn còn phụ thuộc mạng ngoài,
chưa xử lý trong đợt này.

## 22/09/2026 (#358): máy chặn cả tờ hoá đơn chỉ vì đoán không ra một dòng

Hoá đơn 287914 (Kamereo) không thành phiếu mua suốt nhiều ngày chỉ vì dòng "Phí
dịch vụ" map vào một Món chưa khai đơn vị "Lần". Cách viết cũ ném lỗi ở bước
tra đơn vị, cả tờ bị chặn, người dùng không có đường tự làm. Hoá đơn điện tử
Việt Nam có quá nhiều cách ghi, luật đoán sẽ luôn có ca sót.
Cách phòng: máy chỉ GỢI Ý. Dòng đoán không chắc vẫn vào phiếu nháp, để trống mã
và ghi lời đoán trong mô tả (đặt TRƯỚC "(dvt)" để dvt_tren_hoa_don vẫn đọc được).
Người chốt Món và hệ số, hệ số được ghi vào bảng quy đổi của Món để lần sau tự
map. Không bao giờ lặng lẽ lấy hệ số 1 cho hàng tồn kho.
Codex bắt thêm hai lỗ trên chính bản sửa: (1) dòng trống mã được ERPNext coi
như dịch vụ và vẫn ghi sổ được, nên dòng mang lời đoán phải có gác
before_submit riêng; (2) hệ số người gõ là câu trả lời cho MỘT Món, đổi Món
sau khi được hỏi thì phải hỏi lại, máy chủ nhận kèm `he_so_cho` và từ chối
khi lệch.

## 22/09/2026 (v518): ba lỗi tiền đã đi mà phiếu không khép được

- APP-26-09-799: `tdkDs` trả mảng CHUỖI đường dẫn, màn xác nhận chuyển tiền
  lại lấy `x.url` nên gửi `[null]` từ v414. Tệp UNC đã tải lên mà máy chủ báo
  "Chưa đính uỷ nhiệm chi"; chưa phiếu nào qua được cửa này. Ca kiểm cũ chỉ dò
  chuỗi `tdkKhoi('pvunc'`, không bấm thật nên không thấy.
- Cùng phiếu: `co_ma` chặn chữ số ở hai đầu cho MỌI mã. Nội dung "HD 1840 APP
  26 09 799" gọt thành "1840APP2609799", chữ 0 đứng trước chữ A nên bị loại.
  Chỉ chặn chữ số ở phía mã cũng là chữ số.
- HT-2026-02900: hoàn một phần trên đơn có chiết khấu tổng. Tỷ lệ lấy trên
  tổng SAU chiết khấu mà vẫn chép chiết khấu tổng sang tờ trả hàng, ERPNext
  từ chối. Tính tỷ lệ trên tổng TRƯỚC chiết khấu và bỏ chiết khấu tổng.

## 22/09/2026 (#358): chốt chặn tự đặt ra lại chặn nhầm chính mình

Đợt này thêm phép soát cột sau khi khai ô tự thêm (`truong_tu_them._dung_nhom`):
ô có bản ghi mà bảng thiếu cột thì mọi lần lưu doctype đó nổ "Unknown column",
nên thà để Migrate đỏ. Phép soát đó làm bench CI đỏ ba lượt liên tiếp, mỗi lượt
một kiểu ô không có cột thật: ô chia màn hình (Section Break), ô bảng con
(Table), DocType kiểu Single cất giá trị ở `tabSingles`, và cuối cùng là
"Phieu Kiem Ke" - một doctype TỰ TẠO TRÊN DESK, nằm trong cơ sở dữ liệu chứ
không trong git, nên site mới dựng không hề có nó.
Bài học: một chốt chặn đặt trên đường Migrate chặn nhầm là chặn cả lần phát
hành, hại hơn cái nó định chặn. Trước khi đặt, liệt kê hết những trường hợp
"không có cột mà vẫn đúng", và nhớ rằng site CI dựng từ git KHÔNG có các
doctype và ô người ta tạo tay trên site thật.

## 22/09/2026 (#358): đừng chỉ người dùng sang một cửa đang đóng

Dòng hàng tồn kho mà hoá đơn gốc không ghi đơn vị thì máy trả cờ mời người sang
cửa "Sửa mã theo hoá đơn gốc". Nhưng `sua_ma_hoa_don.lua_chon` trả `co_nguon`
sai cho MỌI tờ trả hàng (`is_return`), nên tờ trả hàng bị đẩy tới một cửa đóng
rồi đứng lại chỗ cũ: đường cụt.
Bài học: chỗ nào mời người dùng sang một cửa khác thì phải hỏi ĐÚNG phép mà cửa
đó dùng để mở, chép lại phép là hai nơi lệch nhau (`cua_nguon_mo` nay là nguồn
duy nhất). Và mỗi ngõ cụt phải có một đường ra mở cho mọi tờ: ở đây là để người
gõ thẳng đơn vị nhà cung cấp và hệ số.

## 22/09/2026 (#358): tổng đúng không chứng minh các phần bên trong đúng

Tờ trả hàng hoàn một phần được nắn bằng cách hạ đơn giá cho tới khi TỔNG bằng
đúng số tiền hoàn. Dòng thuế kiểu "Actual" ghi thẳng số tiền thì ERPNext giữ
nguyên khi đơn giá hạ, nên phép nắn đó hội tụ về một tờ có tổng đúng mà chia
sai: đơn 1.010.000 gồm 1.000.000 tiền hàng và 10.000 thuế, hoàn đúng một nửa
505.000, ra tiền hàng 495.000 và thuế 10.000, tức là đảo ĐỦ 100% tiền thuế
trong khi chỉ đảo 49,5% doanh thu.
Cách phòng: hạ MỌI phần tiền trong cùng một hàm ("Actual" và "On Item Quantity"
và dòng bật `dont_recompute_tax` phải hạ tay), và phép soát cuối phải soát TỶ LỆ
giữa thuế và tiền hàng chứ không chỉ soát tổng. Ca kiểm cho lớp soát đó phải
dựng thẳng một tờ có tiền thuế không chịu hạ, không thì gỡ lớp soát đi bộ kiểm
vẫn xanh (đã xảy ra, điều 17a).

## 23/09/2026 (v519): giữ chỗ bằng một cái mã đổi mỗi lượt là đường lành chết

Bước kéo M-Invoice gặp dòng nguồn chỉ có `_id`, không có `shdon` và không có
`tdlap`, thì lưu một bản ghi rỗng để "giữ mã, lượt sau kéo lại cho đầy". Lý
lẽ nghe đúng, và đường lành có thật cho tờ vỏ ruột (tờ có ngày lập, chưa kịp
có số). Nhưng đo trên site thật thì bảng 61.424 bản ghi tách sạch làm hai:
mọi bản ghi có số hoá đơn đều mang mã UUID, mọi bản ghi không số đều mang mã
ObjectId 24 ký tự, không một ngoại lệ ở cả hai chiều. 5.507 bản ghi ObjectId,
trong đó 234 đầu vào, và cả 234 tờ có `modified` đúng bằng `creation`: hai
tháng nằm im, không tờ nào lành. Giải dấu thời gian nhúng trong ObjectId thì
nó rơi vào 5 tới 10 phút TRƯỚC lúc mình kéo, tức là vật tạm bên họ sinh ra
ngay lúc phục vụ lời gọi của mình, mã mới mỗi lượt.
Hậu quả không phải tốn chỗ, mà là thanh báo trên màn Hoá đơn mua hàng nói
"234 hoá đơn đầu vào đã nhận nhưng chưa thành phiếu mua" trong khi nợ thật vì
lý do đó là 0, và con số giả che mất các tờ nợ vì lý do khác.
Bài học: trước khi lưu một bản ghi giữ chỗ, hỏi "cái khoá mình giữ có ổn định
qua các lượt không". Khoá đổi mỗi lượt thì đường lành không bao giờ chạy, và
cách kiểm rẻ nhất là đếm xem trong dữ liệu đã có bao nhiêu bản giữ chỗ từng
lành thật; ở đây con số đó là 0 trên 234.

## 23/09/2026 (v520 -> v521): hàm standard_queries phải whitelist, bộ kiểm gọi thẳng hàm thì không thấy

v520 đăng ký `standard_queries = {"UOM": "vagabond.tim_don_vi.tim_uom"}` mà
hàm đó thiếu `@frappe.whitelist()`. Frappe v16 `search_widget` chạy
`is_whitelisted(frappe.get_attr(query))` trước khi gọi, thiếu là trả trang
"Invalid Method" 404. Kết quả: ô chọn đơn vị tính chết TOÀN HỆ, gõ "Gram"
cũng không ra, khoảng một tiếng sau deploy mới phát hiện khi kiểm site thật.
Bộ kiểm xanh vì ca kiểm gọi thẳng `tim_uom`, không đi qua cửa của Frappe.
Cách phòng: ca `cửa ngõ` nay đọc `hooks.py`, lấy mọi hàm trong
`standard_queries` và chốt từng hàm phải có whitelist. Nói chung: hàm nào
Frappe gọi qua một cửa có gác (whitelist, allow_guest, hook) thì ca kiểm
phải chốt được cái gác đó, gọi thẳng hàm là bỏ qua đúng chỗ hay hỏng.
Và kiểm site thật ngay sau deploy là bắt buộc: lần này nó cứu được.

## 23/09/2026 (v521 -> v522): doctype được dịch thì Frappe lọc lại kết quả standard_queries

Sau v521 hết 404 nhưng gõ "Box", "Nos", "Set" trong ô chọn UOM vẫn rỗng, dù
gọi thẳng `tim_uom` với "box" trả đúng `[["Box", "Hộp"]]`. Lý do: UOM có
`translated_doctype = 1`, nên `search_widget` gọi hàm standard_queries với
txt RỖNG, lấy hết, rồi tự lọc lại bằng `filter_translated`: dịch từng ô
qua `_()` rồi dò chữ người gõ. "Box" dịch thành "Hộp" nên dòng bị loại. Hàm
tìm đúng mà người dùng vẫn không thấy. Cách chữa: mô tả giữ tên lưu, dạng
"Box (Hộp)", chuỗi này không có bản dịch nên đi qua bộ lọc nguyên vẹn.
Cách phòng: ca `#522` dựng lại đúng ba bước search_widget,
filter_translated, build_for_autosuggest. Nói chung: gọi thẳng hàm mình
viết chưa đủ, phải dựng lại cả phần khung chạy SAU hàm đó, vì khung có thể
sửa hoặc xoá kết quả. Đây là lần thứ hai trong một ngày cùng một ô chọn lọt
qua kiểu kiểm gọi thẳng.

## 23/09/2026 (v523): câu hướng dẫn trên màn chỉ tới một nút không làm được việc đó

HT-2026-02900 kẹt hai ngày dù phép tính đã sửa từ v518. Tiền đã ra và đã khớp
sao kê, tờ trả hàng hỏng, phiếu ghi "Nhờ kế toán bấm lại nút Đối soát lệnh
chi". Nhưng nút đó chỉ quét hồ sơ CHƯA đối soát và còn thoát sớm khi không có
hồ sơ nào chờ, nên bấm bao nhiêu lần cũng không chạm tới hồ sơ này. Màn chi
tiết lại ghi "bước còn lại là đính uỷ nhiệm chi" trong khi chưa có phiếu chi,
nên nút đính cũng không hiện. Người dùng tưởng mất tệp, mất nút.
Cách phòng: câu lỗi hướng dẫn bấm nút nào thì phải có ca kiểm chạy ĐÚNG nút
đó trên đúng trạng thái của hồ sơ đang lỗi (ca #523 "bấm Đối soát lệnh chi khi
không còn phiếu nào chờ"). Sửa phép tính mà không kiểm lối vào lại phép tính
đó là chưa sửa xong. Cùng ngày: ánh xạ NCC trỏ vào Món đã tắt chặn luôn món
đúng, và phép học mã hàng "không bao giờ đè" giữ ánh xạ chết mãi mãi. Món đã
tắt thì mọi ghi nhớ trỏ vào nó phải coi như trống.

## 24/09/2026 (v524): chặn ở chỗ ĐỌC dữ liệu chết, quên chặn ở chỗ SINH ra nó

v523 cho mọi lối đọc bỏ qua ánh xạ NCC trỏ Món đã tắt. Anh Việt hỏi lại: sao
máy để người ta chọn được? Tra lịch sử thì không ai chọn nhầm: ánh xạ Kahlua
lập 07/09 khi NVLT00325 còn dùng, 15/09 món bị tắt, hệ không nói gì về ánh xạ
còn trỏ vào. Chỗ sinh ra ánh xạ chết là thao tác TẮT MÓN, không phải lúc lưu
ánh xạ. Thêm nữa, cửa lưu ánh xạ chỉ chặn món tắt khi ô đơn vị có điền.
Cách phòng: gặp dữ liệu "trỏ vào thứ đã chết", hỏi cả hai phía: ai đọc nó
(v523) và thao tác nào làm nó chết (v524, chặn tắt món còn ánh xạ). Và khi
chặn, kiểm cả nhánh ô tuỳ chọn để trống.

## 24/09/2026 (v525): anh Việt duyệt HƯỚNG, không phải duyệt mọi chi tiết tự thêm

v524 được duyệt "làm hướng CCDC dùng ngay", phiên tự thêm một nhóm món mới,
một loại hàng mới và tiền tố mã CCDN, rồi deploy luôn. Anh Việt không muốn tạo
mã mới: "Sao em không báo anh hướng mà tự làm? Làm sao tối giản nhất". v525
gỡ cả ba, thay bằng một ô tick trên mã cũ, giống ô Chặng của bánh.
Cách phòng: trước khi thêm cấu trúc mới người dùng phải thao tác (nhóm, loại,
tiền tố mã, màn mới), trình phương án tối giản nhất bằng lời cho anh Việt
chọn. Nhất là khi dữ liệu thật cho thấy phương án có ngoại lệ (ở đây: 101 mã
đã có sổ kho không đổi được, và tiền nhập kho đi theo tài khoản của KHO).

Bài học đi kèm (Codex #365 v3): "gỡ" cấu trúc đã lên site thật KHÔNG có
nghĩa là xoá. Bản đầu của v525 cho patch xoá nhóm "CCDC dùng ngay" vì nhóm
rỗng, trái QT-20 (không `delete_doc` dữ liệu nghiệp vụ, kể cả mặc định tài
khoản của nhóm). Cách đúng là cho nó NGỪNG: ẩn khỏi màn chọn, chặn dữ liệu
mới đi vào, giữ nguyên bản ghi cũ. Kiểm "rỗng thì xoá" không đủ lý do.

## 24/09/2026 (v526): nút ghi sổ không được giấu hạch toán

Nút "Ghi sổ thẳng, không nối phiếu" ghi sổ ngay mà không cho xem dòng nào đi
tài khoản nào. Hoá đơn xăng không gắn Món nên ERPNext lấy tài khoản chi phí
mặc định của công ty, là 632 giá vốn. Kế toán chỉ biết sau khi đã ghi sổ, lúc
đó muốn sửa lại vướng quyền Repost.
Cách phòng: mọi nút ghi sổ trên app phải cho thấy, và cho đổi, tài khoản của
dòng chi phí TRƯỚC khi ghi. Hook tự đặt tài khoản (khai trên Món, tài khoản
đầu phiếu) phải chừa dòng người vừa chọn, và sau khi ghi đọc lại SỔ CÁI (GL
Entry của đúng tờ), không chỉ ô tài khoản trên dòng. Codex #368: ô trên dòng
đúng mà bút toán Nợ chỗ khác thì phép soát chỉ đọc dòng vẫn chốt.

Cùng đợt: dấu nối "hoá đơn đến sau" chỉ là chứng từ. Khoản chi đã ghi chi phí
qua hồ sơ, nên tờ hoá đơn đã nối phải bị CHẶN ghi sổ ở before_submit, không
chỉ giấu nút, vì Desk và API vẫn ghi được.

Chặn "tờ đã nối" ở before_submit mà đọc dấu nối bằng select thường là chưa đủ
(Codex #368, tái hiện trên MariaDB thật hai kết nối): REPEATABLE READ cho
giao dịch ghi sổ thấy ảnh chụp lúc mở tờ, không thấy dấu nối hồ sơ khác vừa
chốt; hai hồ sơ cùng nối một tờ cũng lọt. Chỉ thêm khoá tờ vẫn lọt 2 trên 3
thứ tự đan xen. Cách phòng: mọi đường quyết định (nối, ghi sổ) khoá CÙNG một
dòng (tờ hoá đơn) trước, rồi đọc trạng thái và dấu nối bằng câu có khoá
(for update), không lấy docstatus từ get_doc.

Tờ hoá đơn mua NHÁP còn có trạng thái "đã đánh dấu huỷ" (vgb_huy 1,
docstatus vẫn 0). Luật nào chỉ xét docstatus là nhận nhầm tờ đã bỏ (Codex
#368 vòng 2: nối tờ đó làm hoá đơn đến sau thì hồ sơ thành chi phí hợp lệ
tính thuế bằng một chứng từ đã bỏ). Mọi luật "tờ còn hiệu lực" phải xét cả
dấu huỷ, và xét cả chiều ngược: tờ đang làm chứng từ thì không cho huỷ mềm.

Phép soát tiền một chiều ("được Nợ ít nhất bằng") luôn đạt với số âm. Tờ trả
hàng có tiền âm, sổ cái ghi Có, nên luật đó để lọt bút toán Có sai tài khoản
(Codex #368 vòng 3). So tiền sổ cái phải theo DẤU: cùng chiều và đủ số.

Hồ sơ "Từ chối" KHÔNG phải trạng thái cuối: người lập sửa rồi gửi duyệt lại
được. Luật nào coi Từ chối như Huỷ để trả lại chứng từ đang giữ là mở đường
cho chứng từ đó bị dùng lần hai trong lúc chờ (Codex #368 vòng 4). Chỉ Huỷ mới
là cuối; trước khi coi một trạng thái là "hết hiệu lực", kiểm xem có bước nào
đưa nó sống lại không.

Luật mới cho một loại hồ sơ phải khoá đúng loại đó. v526 viết luật "hoá đơn
đến sau chỉ nối tờ nháp, tờ đã nối không ghi sổ" cho hồ sơ Chi từ TK công ty
nhưng áp lên mọi hồ sơ; hồ sơ trả NCC vốn nối tờ ĐÃ ghi sổ (tờ tạo công nợ)
nên sẽ gãy luồng trả NCC. Bộ kiểm khung không thấy vì mọi ca dựng hồ sơ TK
công ty; chỉ bench chạy ca tích hợp cũ #263 mới bắt được. Viết luật theo loại
thì phải có ca cho CẢ loại không áp luật.

Luật theo loại thì ô loại phải đứng yên khi luật đã áp. Sau khi khoá luật hoá
đơn đến sau theo loại hồ sơ, ô loại vẫn sửa được trên Desk/API: đổi TK công ty
sang Hoàn ứng cùng lần sửa số tiền là mọi luật đọc loại mới đều bỏ qua, rồi
tờ nháp ghi sổ được, chi phí vào sổ hai lần (Codex #368 vòng 10). Đừng vá từng
luật cho đọc loại cũ; giữ một bất biến: đang nối chứng từ thì không đổi loại.
Mỗi ô dùng để CHỌN luật phải tự hỏi: ai sửa được ô này sau khi luật đã áp?

Khoá dòng rồi mà vẫn đọc bằng get_value là chưa khoá. v526 vòng 11: lần nối hoá
đơn đến sau khoá tờ trong validate, nhưng số tổng tiền dùng để quyết "Hợp lệ
tính thuế" lại đọc bằng get_value ở bước trước, tức ảnh chụp REPEATABLE READ.
Người sửa tờ chốt tổng mới trong lúc đó thì quyết định dựa trên số cũ. Mọi giá
trị dùng để QUYẾT phải đọc bằng câu có khoá, từ một hàm nguồn duy nhất.

## 25/09/2026 (v527): hàng rào chặn cả ngày vì một tờ không ai được gọi xử

Hàng rào thứ tự hoá đơn (m-invoice đánh số theo ngày lập) bảo vệ MỌI tờ đã
ghi sổ của hôm qua chưa có HĐĐT, kể cả tờ giữ cờ "chưa rõ kết quả gửi".
Nhưng lượt tự xuất ngày cũ chỉ gửi tập hẹp, không gồm tờ giữ cờ. Tập bảo vệ
rộng hơn tập máy tự rút được, nên một tờ giữ cờ đứng chặn cả ngày hôm sau
tới nửa đêm, lúc ngày cũ hết hạn, rồi nhịp bù 00:15 mới xuất cả ngày: 18/09
và 23/09 cả ngày ký sang hôm sau. Thư báo "hoãn phát hành" có gửi, nhưng
không ai coi đó là việc phải làm trong ngày.

Bài học: mọi hàng rào chặn theo một tập phải có một đường TỰ ĐỘNG rút đúng
tập đó, không chỉ một nút cho người bấm. Nếu tập chặn lớn hơn tập máy tự xử
được, phần chênh là một cái bẫy chờ ngày. Kiểm bằng câu: "tờ nào nằm trong
tập chặn mà không đường tự động nào đụng tới?".

Hai nguồn sinh cờ cũng phải tắt: nhịp chạm m-invoice nào có thể chạy quá 300
giây thì phải chạy trên hàng đợi dài (bài 03/09 mới áp cho chuỗi cuối ngày,
xuất rải và nhịp bù vẫn ở hàng đợi thường), và nhịp nào lấy khoá chỉ đợi vài
giây thì phải có nhịp khác đợi lâu hơn trước mốc hết ngày.

Và: màn báo cáo phải so được với nguồn bên ngoài theo đúng đơn vị người dùng
đếm (tờ theo ngày lập trên m-invoice), không chỉ đếm trong ERP. Tờ lập thẳng
trên cổng (thay thế, tách đơn) chỉ lộ ra khi đặt hai con số cạnh nhau.

Ba bẫy Codex bắt ở vòng 1 của cùng PR (#369), cả ba đều im lặng:
- Đọc cấu hình lỗi hay trống mà trả chuỗi rỗng rồi "không lọc" là mở cửa
  cho dữ liệu khác loại (dải Fabi C26MVO) đếm lẫn vào. Cấu hình dùng để LỌC
  thì thiếu là DỪNG có lời, không bao giờ coi rỗng là "lấy hết".
- Hàm báo cáo tự cắt `[:300]` bảng phụ thì nút "Xuất Excel đầy đủ" cũng mất
  dòng, vì Excel gọi lại đúng hàm đó. Cắt cho màn hình chỉ làm ở MỘT chỗ
  (`bao_cao.chay`), có cờ và lời báo, và bỏ qua khi xuất đủ.
- Báo cáo không chia theo điểm bán mà vẫn hiện chip điểm bán thì người xem
  bấm chip, đầu trang đổi mà bảng không đổi. Báo cáo nào không nhận một bộ
  lọc thì máy chủ bỏ bộ lọc đó và màn hình ẩn chip, nói rõ vì sao.

Vòng 2 (#369) thêm một bẫy về NGÀY: một tờ có hai ngày, ngày sổ và ngày lập
hoá đơn (`vgb_hddt_ngay_xuat`, khác ngày sổ khi tờ đã được kéo ngày). Hạn ký,
cửa m-invoice và phép đếm theo ngày của hoá đơn phải xét theo NGÀY LẬP. Xét
theo ngày sổ thì tờ kéo ngày bị coi là quá hạn mãi và không đường tự động nào
chạm tới nó, còn báo cáo theo ngày thì lọt mất nó. Lọc theo ngày sổ trước rồi
mới tính ngày lập (`posting_date between ... - 3 ngày`) là lọc sai tập, phải
hỏi theo cả hai ô rồi gộp.

Lượt TỰ ĐỘNG đi lại đường của người bấm tay thì phải thu hẹp đúng phạm vi của
nó: người bấm "kéo ngày" là kéo cả ngày sổ đó, còn máy tự đối chiếu chỉ được
đụng tờ đang giữ cờ (`chi_giu_co=1`).

Vòng 3 (#369): kế hoạch chia lượt theo cặp khoá (ngày sổ, ngày lập) thì
bộ chọn BÊN TRONG mỗi lượt cũng phải lọc theo đúng cặp đó. Chia ngoài mà
chọn trong theo một nửa khoá là lượt đầu nuốt việc của lượt sau. Và câu ghi
có điều kiện xong thì phải đọc lại trước khi ghi nhật ký hay trả "đã xong":
không dòng nào khớp điều kiện mà vẫn báo thành công là ghi nhật ký sai.

Vòng 4 (#369): tập CHẶN và tập mà lượt tự động XỬ ĐƯỢC phải dùng cùng một
khoá ngày. Hàng rào chặn theo ngày sổ còn lượt tự đối chiếu ngày cũ bỏ tờ có
ngày lập hôm nay, nên tờ ngày sổ cũ đã kéo sang hôm nay nằm trong tập chặn mà
không lượt nào gỡ được: chặn cả ngày. Mỗi lần thêm điều kiện loại cho một
lượt, tìm tập chặn tương ứng và loại cùng điều kiện. Cùng vòng: nhật ký là
một phần của lần ghi, ghi nhật ký hỏng thì phải ném để câu ghi rollback,
không nuốt lỗi rồi báo xong; và đơn là danh mục có sẵn thì chọn trong danh
sách có tìm (QT-31), không mở ô gõ mã.

## v528 (#370, 25/09/2026): khoản trả tiện ích không mang mã hồ sơ

Triệu chứng: hồ sơ APP.26.09.100 (tiền nước Bến Thành, 1.144.382 đ) trả bằng
tính năng thanh toán hoá đơn của app MB. Dò SePay báo "chưa thấy giao dịch nào
mang mã", ô tìm màn khớp tay gõ số tiền ra 0 dòng, dù sao kê ACC-BTN-2026-06151
đã về đúng tiền, đúng tài khoản.

Nguyên nhân: tự khớp chỉ tìm mã APP trong nội dung, mà thanh toán hoá đơn của
ngân hàng không cho gõ nội dung ("WATER BT WATER 1032865688 e0Vh5pp20ek.BP1").
Ô tìm chỉ so chữ. Dãy số dài trong nội dung ĐỔI mỗi lần trả (tờ Tân Hoà cùng
ngày mang 1032865615), nên không dùng làm mã khách hàng được.

Cách phòng:
- Nhớ MẪU ĐẦU DÒNG theo nhà cung cấp, không nhớ dãy số. Tự khớp theo mẫu phải
  đủ: mẫu + đúng tiền + đúng tài khoản + trong khoảng ngày + chỉ một dòng còn
  dùng được. Dòng mang mã APP của hồ sơ KHÁC thì loại khỏi cả tự khớp lẫn gợi
  ý: có mã là đã có chủ, dù chưa ai ghi ô chủ.
- Không có mẫu thì chỉ gợi ý cho người bấm, máy không tự gán theo số tiền.
- Ô tìm của màn chọn sao kê nhận cả số tiền.
- Kiểm "mẫu đã thuộc ai" phải làm lại DƯỚI KHOÁ bằng current read ngay trước
  khi ghi. Kiểm trước rồi mới khoá là hai lượt đồng thời cùng qua.

## v529 (#367, 25/09/2026): trang www có gạch nối thì get_context KHÔNG BAO GIỜ chạy

Triệu chứng: Minh Vũ mở /bien-tap-web khi chưa đăng nhập thấy bảng trống và
câu "chưa được whitelist", không có nút đăng nhập. Trên issue đoán là do bộ
nhớ đệm trang.

Đo trên site thật: thẻ `<meta name="csrf-token">` của /bien-tap-web, /dat-ban,
/thanh-vien mang NGUYÊN VĂN chữ `{{ csrf_token }}`. Tức là get_context chưa
từng chạy. Frappe (website/page_renderers/template_page.py, `set_pymodule`)
đổi gạch nối thành gạch dưới khi tìm mô đun: trang `bien-tap-web.html` cần
`bien_tap_web.py`, còn repo đặt `bien-tap-web.py`. Không lỗi, không cảnh báo:
trang vẫn hiện, chỉ là không có cửa kiểm quyền và không có mã CSRF, nên lưu
nháp bị Frappe chặn.

Cách phòng:
- Mô đun Python của trang www đặt tên bằng gạch dưới. Ca kiểm
  `thu_don_web_367.py` mục N chặn tên có gạch nối, không còn ngoại lệ:
  dat-ban đã đổi thành dat_ban.py ở v532 sau khi Codex bắt trên PR #376
  (trang bắt đầu dùng get_context thì tên sai làm in nguyên văn
  `{{ nhan... }}` cho khách); thanh-vien đổi ở v532b vì site thật 27/09 cũng
  in nguyên văn `{{ csrf_token }}`. `thu_trang_www_532b.py` dựng trang như
  Frappe (tìm mô đun theo luật gạch dưới, gọi get_context, thay biến giữ
  nguyên văn khi thiếu) để bắt lỗi này, không chỉ dò tên tệp.
- Jinja của Frappe dùng DebugUndefined: biến thiếu in ra nguyên văn chứ không
  rỗng. Thấy `{{ ... }}` trên trang thật là get_context không chạy.
- Jinja của Frappe không tự thoát ký tự. Trang khách mới dựng HTML ở Python
  (`vagabond/trang_khach.py`) và thoát mọi chuỗi ở đó.

Cùng đợt, ba bẫy khác của trang đặt bánh:
- Phí giao hỏi nhiều lần chồng nhau (chọn khu vực rồi gõ địa chỉ): kết quả của
  lần hỏi CŨ về muộn đè số mới. Mỗi lần hỏi mang số thứ tự, bỏ kết quả cũ.
- Meta Pixel tự gửi địa chỉ trang trong PageView. Trang biên nhận có token
  trên đường dẫn phải `history.replaceState` về /banh/xong TRƯỚC khi nạp Pixel,
  và máy chủ trả `Referrer-Policy: no-referrer`.
- Tất cả token biên nhận đi vào CÙNG một đường trang `banh/xong`: chỉ cần một
  lần bị bộ nhớ đệm trang của Frappe giữ lại là khách sau thấy biên nhận của
  khách trước. Tắt đệm ở cả mô đun, `frappe.local.no_cache` và Cache-Control.

## v530 (25/09/2026): hoá đơn đến sau đã ghi sổ, chi phí hai lần

Triệu chứng: chị Dung không nối được hoá đơn đến sau cho ba hồ sơ chi từ TK
công ty (APP.26.09.009 Adecco, APP.26.09.102 Mobifone, APP.26.08.016 Văn An).
Ô chọn hiện tờ không liên quan, có tờ hiện hai lần, và mỗi dòng có một dấu chấm
nằm riêng một hàng phía trên tên.

Nguyên nhân:
- Tờ đúng ĐÃ GHI SỔ (máy đồng bộ m-invoice ghi sổ trước khi ai nối), mà luật
  v526 chỉ cho nối tờ nháp nên ô chọn giấu nó. Hồ sơ đã ghi Nợ chi phí qua bút
  toán của nó, tờ cũng ghi Nợ chi phí và Có 331: chi phí hai lần, công nợ treo
  hiện "trễ hạn" ở màn Công nợ phải trả, người khác có thể trả lần nữa.
- Mô hình một tờ một khoản không chứa được hai ca thật: một tờ tách ba khoản
  theo bộ phận (Adecco), sáu tờ theo số thuê bao gom một lần trả (Mobifone).
- Nhà cung cấp có nhiều chi nhánh (MST đuôi -002, -096) là nhiều hồ sơ nhà
  cung cấp khác nhau; lọc đúng tên thì không ra tờ.
- Dấu chấm: `vgbNoiOTim` hiện lại mục bằng `style.display = ''`, tức XOÁ
  luôn `display:flex` ghi trên thẻ. Hàm chạy lọc một lần ngay lúc nối, nên mọi
  hộp chọn có ô tìm (từ 7 mục) đều vỡ bố cục từ lần mở đầu. DOM giả của bộ
  kiểm không đọc thuộc tính style nên không ca nào thấy.

Cách phòng:
- Nối ở mức HỒ SƠ, so TỔNG tờ với tổng khoản chờ; nhóm nhà cung cấp theo MST
  gốc 10 số. Tờ đã ghi sổ còn nợ thì lập MỘT bút toán bù trừ Nợ 331 (tham
  chiếu tờ) / Có đúng tài khoản chi phí hồ sơ đã ghi, soát lại với sổ chi của
  hồ sơ trước khi Có. Bút toán bù trừ mang ô riêng `vgb_bu_tru_ho_so`, KHÔNG
  mang `vgb_ho_so_tt`: mọi phép "bút toán chi của hồ sơ" đọc ô kia.
- Máy gợi ý phải thử khớp ĐÚNG TỪNG ĐỒNG trước rồi mới nới ngưỡng: với ngưỡng
  1.000 đ ngay từ đầu, ca Mobifone ra tổ hợp 5 tờ lệch 609 đ trước tổ hợp 6 tờ
  đúng.
- Ẩn hiện phần tử: nhớ giá trị display gốc rồi trả đúng giá trị đó, đừng gán
  chuỗi rỗng. DOM giả nay đọc thuộc tính style như trình duyệt.
- Danh sách lấy bằng get_list kèm luật quyền có thể trùng dòng: bỏ trùng theo
  tên trước khi vẽ.
- Chặn một thao tác đua với thao tác khác thì CẢ HAI phía phải khoá cùng một
  dòng rồi đọc bằng câu có khoá. Codex #374 vòng 3: huỷ bút toán chi của hồ
  sơ đua với nối hoá đơn đến sau. Chỉ thêm khoá hồ sơ vào hook huỷ (đúng lời
  gợi ý) vẫn hỏng 2 trên 3 thứ tự đan xen trên MariaDB thật, vì phía chờ khoá
  xong vẫn đọc ảnh chụp cũ. Khoá hồ sơ ở hook, đọc bù trừ bằng for update, và
  phía nối đọc bút toán chi bằng for update thì 0 trên 3. Thứ tự khoá chéo
  (huỷ đã giữ dòng bút toán, nối đã giữ hồ sơ) có thể thành deadlock: MariaDB
  lùi một bên, dữ liệu vẫn đúng, người dùng bấm lại.

## 27/09/2026 (v531): mã hồ sơ nằm trong ô số hoá đơn, và nhánh tạo mới không ai kiểm

- Luồng Hoàn ứng tự điền mã hồ sơ (APP.26.08.004) vào ô số hoá đơn khi khoản
  không có số. Tờ đó trông như có số, rồi được nối làm hoá đơn đến sau và đẩy
  hồ sơ lên "hợp lệ tính thuế" sai (APP.26.08.005 Cấp nước Tân Hoà). Cách
  phòng: ô số hoá đơn chỉ chứa số của nhà cung cấp; không có thì để trống. Mọi
  luật "tờ này làm căn cứ thuế được không" đi qua MỘT hàm (to_khong_hoa_don),
  và hook tờ chặn ghi mã hồ sơ vào ô đó.
- Patch #367 gieo nháp chính sách hỏng ngay lúc deploy: dựng bản ghi bằng
  frappe.get_doc(dict) thì is_new() trả False, nhánh save() nổ "not found".
  Ca kiểm cũ chỉ đi nhánh "đã có bản ghi". Cách phòng: bản ghi mới luôn dùng
  frappe.new_doc; hàm có hai nhánh tạo mới / đã có thì ca kiểm phải đi cả hai,
  với Doc giả giữ đúng luật is_new() của Frappe.
- Patch một lần mà nuốt lỗi (log_error rồi đi tiếp) thì Frappe vẫn ghi vào
  Patch Log là đã chạy, không bao giờ chạy lại. v529 lên xanh mà ba trang mất
  nháp. Patch gieo dữ liệu một lần phải để lỗi nổ cho migrate dừng (Codex
  #375). Chỉ dong_bo_cau_truc, loại chạy lại mỗi bản, mới được nuốt lỗi.
- Doctype có on_trash chặn xoá (Nội dung web) thì ca bench muốn đi nhánh
  "chưa có bản ghi" không được gọi delete_doc (force=True không bỏ hook),
  và cũng không được xoá thẳng dòng bằng frappe.db.delete: đó là sửa dữ liệu
  thật, chỉ dựa vào điểm lưu (Codex #375 vòng 3). Site đã có bản ghi thì bỏ
  qua; nhánh tạo mới kiểm ở tầng khung bằng Doc giả.
- Luật "toàn số 0" đừng liệt kê dấu ngăn: sửa hai lần vẫn sót "000,000",
  "00:00". Xét thẳng "không có chữ cái hay chữ số nào khác 0".

## 27/09/2026 (v533): tự lưu phiếu đang soạn, hai cái bẫy khi bọc khung

- Loan Anh soạn báo giá trên app, lỡ thoát hoặc máy sập nguồn là mất cả tờ.
  Cách làm: MỘT phần `48-ban-soan-do.js` bọc mọi màn lập phiếu, bọc `api`,
  `frame` và `vgbGomNhom` một lần; bản nháp nằm trong localStorage của máy
  theo từng tài khoản. Màn lập phiếu mới phải khai một dòng `sdKhai` và một
  dòng `sdBoc` trong 48; ca `thu_ban_soan_do_533.py` sẽ báo nếu quên.
- Bẫy 1: ghi nốt bản nháp lúc rời màn mà hỏi "màn trên chồng có còn là màn
  đang soạn không" thì với nút Back của trình duyệt câu trả lời luôn là KHÔNG:
  `back()` đã cắt nấc rồi mới gọi `frame` của màn cha. Kết quả là gõ xong vuốt
  lùi ngay thì mất đúng đoạn cuối. Ca kiểm bằng cú bấm nút ‹ không thấy vì
  cú bấm đã ghi trước. Cách phòng: lúc rời màn ghi thẳng, không hỏi chồng; ca
  kiểm gọi `back()` không qua cú bấm (đường popstate).
- Bẫy 2: đừng gọi hàm đọc ô nhập của màn (`dsTayDoc`, `hdTaoDoc`...) từ bên
  ngoài để chụp trạng thái. Vài hàm gán '' cho ô không tìm thấy, mà lúc màn
  đang vẽ tạm đồng hồ cát thì chưa có ô nào: gọi vào là xoá trắng phiếu thật.
  Chụp trạng thái và giá trị ô riêng rồi điền lại ô sau khi vẽ.
- Màn dựng trạng thái ngay trong hàm của nó (nhập kho theo phiếu, form hoàn
  tiền) không đặt trạng thái từ ngoài được; phải có móc `sdGhep` ngay sau chỗ
  dựng. `hoanMoFormDu`/`hoanMoFormHuy` phải TRẢ promise, không thì bản bọc
  không chờ được tới lúc form vẽ xong.
- Bẫy 3 (Codex #378): hàm máy chủ trả thành công CHƯA chắc đã có phiếu.
  `nop_quy.tao` và `tao_theo_ngay` trả `{can_ly_do: 1}` trước khi insert để
  màn hỏi lý do lệch rồi gọi lại. Xoá nháp ngay khi promise xong là mất cả
  bảng kê nếu người dùng huỷ hộp lý do. Chỉ xoá khi `sdDaTaoPhieu(kq)` đúng.

## 28/09/2026 (v534, #380): phiếu thu kẹt nháp im lặng sáu tuần, và công cụ danh sách chung

- Triệu chứng: khách đã chuyển đủ tiền vẫn nằm trong Công nợ phải thu. Gốc:
  script tự lập phiếu thu từ giao dịch SePay `insert()` rồi `submit()` trong
  `try`, `except` nuốt lỗi vào một biến, cuối cùng vẫn `commit()`. Submit hỏng
  (chốt đính kèm 16/08 áp cả chiều thu) nên bản NHÁP được lưu, không dòng nào
  vào Error Log, và lần chạy sau thấy hoá đơn đã có phiếu nên không thử lại.
  Tới 28/09 đã là 1.428 phiếu, 1,33 tỷ. Cách phòng: script nào tạo chứng từ
  thì lỗi submit phải ra chỗ con người đọc được (Việc hôm nay, Error Log), và
  không commit bản dở; chuyển logic đó về repo để có ca kiểm (#380 mục 1C).
- Đừng tách một khoản ra khỏi "còn phải đòi" chỉ vì có phiếu thu nháp (Codex
  #381 F4): phiếu nhập tay, phiếu lỗi cũng là nháp. Chỉ tách khi giao dịch
  ngân hàng đã xác minh độc lập (`thu_tien.xac_minh_tien_ve`).
- Ghi sổ phiếu thu có workflow: KHÔNG đặt tay `workflow_state` từ "Nháp"
  sang bước đã ghi sổ (không khai bước chuyển đó). Cứ `submit()`, Frappe tự
  đặt bước ứng với docstatus 1 (`set_workflow_state_on_action`).
- Màn danh sách mới: dùng `dsCongCu` (15-khuon-danh-sach.js) cho chip chặng,
  chip lọc, chip ngày, ô tìm, Excel; Excel khai MỘT adapter trong
  `khung/cong_cu_ds.MAN_XUAT`. Ca `thu_cong_cu_ds_534.py` đỏ nếu màn danh sách
  mới không dùng công cụ mà không khai miễn kèm lý do.
- DOM giả (`dom_gia.js`) trước v534 không bỏ lần đăng ký trùng của cùng một
  hàm nghe như trình duyệt; màn gắn `root.addEventListener(..., hamCoTen)` mỗi
  lần vẽ thì ca kiểm thấy sự kiện chạy hai lần. Đã sửa cho khớp trình duyệt.
- Điều kiện "phải có tệp X" thì đếm tệp NẰM TRONG Ô X, không đếm mọi File
  gắn vào chứng từ (Codex #382). Đếm cả chứng từ là để một ảnh chụp bất kỳ ở
  mục khác mở khoá ghi sổ; chính ca bench đầu tiên của v534 đã vô tình đi
  qua lỗ đó vì gắn tệp chung chung. Phép chung: `thu_tien.dem_tep_unc`.
- Một hoá đơn trả bằng nhiều lần chuyển thì CỘNG các phiếu đã xác minh; lấy
  phiếu lớn nhất là để hoá đơn đã trả đủ nằm lại "Đang nợ" (Codex #382,
  `thu_tien.gom_tien_da_ve`). Nhưng chống trùng phải theo GIAO DỊCH trên toàn hệ
  thống, không theo cặp (hoá đơn, giao dịch): khoá có chứa hoá đơn thì một lần
  tiền về chia cho hai phiếu hai hoá đơn được tính hai lần (Codex #382 vòng 2).
  Chọn phiếu thắng ở MỘT chỗ (`mot_phieu_moi_giao_dich`), trên mọi phiếu cùng
  mã giao dịch chứ không trên tập màn đang lọc.
- Luật chứng từ đặt ở NÚT BẤM thì Desk đi vòng được: mọi đường gọi `submit()`
  (Desk, script, tác vụ nền) chỉ đi qua hook `before_submit`. Luật nghiệp vụ
  bắt buộc phải có một hook, nút trên app chỉ báo sớm (Codex #382 vòng 3).
- Bench mặc định có tài khoản Bank không mang số hiệu 112, nên mọi hook soi
  ngân hàng theo số hiệu (`la_ngan_hang`) lọt qua trong ca kiểm. Ca kiểm luồng
  ngân hàng phải dựng tài khoản 112 như site thật (`_tai_khoan_cong_ty_moi`).
- Đổi tham số lọc cho màn mà vẫn nhận tham số cũ "để app cũ không vỡ" thì phải
  chép ĐÚNG phép lọc cũ, không quy gần đúng về khái niệm mới (Codex #382:
  "Đã duyệt" cũ = chờ ghi sổ + đã ghi sổ, không trùng chặng nào).
- Payment Entry có HAI số tiền: `paid_amount` là tiền phía bên kia (khách
  với phiếu thu), `received_amount` là tiền vào tài khoản nhận. So với giao
  dịch ngân hàng thì phải dùng phía tài khoản ngân hàng, hoặc chặn hẳn phiếu
  ngoại tệ và tỉ giá khác 1 (Codex #382 vòng 5, `thu_tien.tien_phia_ngan_hang`).
  Tiệm chỉ dùng tiền đồng nên hai số luôn bằng nhau trên dữ liệu thật, và vì
  thế không ca kiểm nào dựng từ dữ liệu thật bắt được lỗi này.
- Cổng "phải có tệp ở ô X" phải xét tệp GẮN QUA ô X (`attached_to_field`),
  không chỉ xét đường dẫn nằm trong ô. `tep_dinh_kem.gan_vao` coi tệp đã gắn
  vào chứng từ là xong mà không xét ô, nên một ảnh kẹp giấy có sẵn đổi nhãn
  được thành tệp bắt buộc, cả trên app lẫn qua ô Attach trên Desk (Codex #382
  vòng 7, `thu_tien.url_trong_o_unc`).
- Xuất Excel bằng `make_xlsx`: xlsxwriter ghi chuỗi mở đầu bằng "=" và dạng
  "{=...}" thành công thức. Dữ liệu từ khách (tên, lý do, mã đơn) phải qua
  `khung.cong_cu_ds.chu_an_toan` trước khi ghi (Codex #382 vòng 7).
- Ô Attach trên Desk KHÔNG chứng minh tệp được tải lên qua ô đó: khi lưu,
  Frappe `attach_files_to_document` chép một đường dẫn có sẵn thành dòng File
  mới gắn qua ô. Cổng "tệp phải nằm ở ô X" phải xét cả các dòng khác cùng
  đường dẫn (`thu_tien.url_unc_that`). Ca thuần giả lập không thấy được hành
  vi này; chỉ bench mới bắt (#382 vòng 8).
# 30/09/2026 - So công nợ phải giữ cùng phạm vi

PI outstanding dương, AP/AR có credit chưa phân bổ và Sổ đối tác từ GL
không phải ba cách gọi cùng một chỉ tiêu. Purchase Receipt có Party trên
tài khoản chờ hóa đơn có thể vào Sổ NCC mà không có PLE/AP. Truy đến
voucher/account trước khi nhận là thiếu thanh toán; không tạo PE hay đổi
outstanding để ép số bằng nhau. Purchase Register có bill_date không có
nghĩa đã có payment_date. Incoming/Outgoing trong Payment Period là chiều
tiền, không phải chiều hóa đơn. Nguồn và ca nghiệm thu:
[hồ sơ đối chiếu](van-hanh-agent/cong-viec/doi-chieu-cong-no-20260930.md).

## 29/09/2026 (v540): phiếu ghi lùi ngày mà máy chọn lô theo tồn hôm nay

- Khải làm phiếu sản xuất cuối tháng ghi ngày 31/08. Máy chọn lô sữa
  LO-260914-000105 vì hôm nay lô đó còn hàng, nhưng lô đó sinh 14/09. ERPNext
  kiểm tồn lô TẠI NGÀY GHI SỔ nên chặn "negative stock", lần nào lưu cũng
  chặn vì dòng đã mang sẵn lô sai và phép bù lô cũng đọc tồn hôm nay.
- Mọi phép đọc tồn lô cho một phiếu phải đi qua `lo_hang.luc_cua_phieu(doc)`
  (một nguồn) rồi `_ton_tung_lo(..., luc=)`. Phiếu ghi lùi: lấy số NHỎ HƠN
  giữa tồn tại ngày ghi và tồn hôm nay, để vừa có hàng vào ngày đó vừa không
  làm âm các phiếu đã ghi sau.
- Vòng 2: tồn khả dụng là số dư THẤP NHẤT của lô từ ngày ghi tới nay (đọc
  biến động sổ kho sau ngày ghi), vì lô có thể về 0 giữa chừng rồi được nhập
  lại. Hạn dùng cũng xét theo NGÀY GHI: get_batch_qty mặc định bỏ lô hết hạn
  tính tới hôm nay, nên trứng còn hạn ngày 31/08 từng bị coi là không có.
- Chỉ tin ngày trên phiếu khi `set_posting_time` bật; không bật thì ERPNext
  đặt lại ngày giờ hiện tại SAU hook before_validate (Codex #388 F1).
- Ca kiểm tầng khung phải có ca giữ đúng đường nối, không giả hết các hàm
  con: đột biến "bỏ biến động sau" từng không làm đổ ca nào vì ca duy nhất
  đi qua đó đã giả nó rỗng.
- Bấm Gửi thẳng trên nháp ĐÃ LƯU: Frappe đặt docstatus=1 TRƯỚC before_validate
  và đánh dấu `_action="submit"`. Hook nào chặn theo `docstatus != 0` sẽ bỏ qua
  đúng lượt Gửi này (Codex #390). Ca thật dựng bằng insert() rồi submit() không
  bắt được, vì insert() đã chạy hook ở docstatus 0 và chữa trước; phải dựng
  nháp đã lưu sẵn trạng thái sai rồi mới Gửi.

## 29/09/2026 (v536): đơn không phải là sổ hoá đơn, và mã cấp trước khi nạp danh mục

- Chị Dung tìm tờ thay thế 14576 trên danh sách hoá đơn bán không ra: tờ đó
  chỉ nằm dưới dạng chữ "1C26MPV 14576" trong ô ghi tay của đơn gốc, còn tên
  công ty thì đơn đứng tên người đặt Pancake. Mọi lần "đồng bộ hoá đơn" trước
  đều lấy ĐƠN làm gốc rồi cố gắn số tờ lên đơn, nên tờ thay thế, tờ tách, tờ
  lập tay không bao giờ có dòng riêng. Sổ kế toán phải lấy TỜ (bảng MInvoice
  Invoice, bản chụp 1:1 của m-invoice) làm gốc và trỏ về đơn, không phải
  ngược lại. Báo cáo `So hoa don dien tu ban ra` làm đúng chiều đó.
- Mã khách kế toán: máy cấp mã nối tiếp mã lớn nhất, nhưng danh mục Fast của
  chị Dung đã đi trước ERP (KH001588 so với KH001382). Cấp mã trước khi nạp
  tệp của chị là hai công ty chung một mã mà không ai thấy. Vì vậy
  `ma_ke_toan.cap_ma` chỉ cấp sau khi cờ `vgb_ma_ke_toan_da_nap` được bật ở
  lượt `nap_danh_muc_fast` đầu tiên; trước đó ô để trống chứ không tạm ghi
  MST (anh Việt chốt 29/09/2026).
- Patch cần cột mới thì phải tự dựng cột trong patch: `after_migrate` (nơi
  `truong_tu_them` dựng ô) chạy SAU `patches.txt`. Bench mới còn thiếu cả
  doctype khai trên site (MInvoice Invoice) và ô do lần deploy trước dựng
  (vgb_don_erp), nên patch soát `has_column` rồi dừng êm, không nổ migrate.
- Nhãn "Hoá đơn đầu ra do Fabi xuất" từng gắn cho cả 5.697 tờ tháng 9 trong
  khi phần lớn do ERP xuất. Một nhãn sai nhưng vô hại lâu ngày thành sự thật
  trong đầu người đọc; nhịp kéo nay nối tờ ERP về đơn ngay lúc kéo và ghi
  đúng lý do.

## PR389 - Giữ xung đột qua mọi đường đọc và điền mã
Sửa đường ghi chưa đủ: bảng tra để hiển thị và backfill SQL vẫn có thể lấy
bản ghi đầu khi MST hoặc mã tờ trùng. Giữ tập ứng viên, chỉ suy mã/liên kết
khi duy nhất; xung đột phải còn trong hàng chờ xử lý. Ô dẫn xuất phải xóa
khi đầu vào mới không phân giải được, kể cả tra lỗi, tránh giữ mã khách lẻ
cho hóa đơn doanh nghiệp. Ca backfill phải chạy UPDATE thật trên MariaDB,
không chỉ khẳng định chuỗi SQL có WHERE. Nguồn PR389/comment5903869461.

### 30/09/2026 - PR389: chuẩn MST ở mọi cửa, giữ mọi bản ghi trùng
Chỉ chuẩn hóa đầu vào rồi WHERE tax_id IN hai dạng gạch/không gạch vẫn bỏ
MST có khoảng trắng mà bộ chuẩn chấp nhận. Dùng cùng chuẩn phía dữ liệu
đọc, cả tra/cấp mã lẫn báo cáo. Nạp danh mục phải nhìn toàn bộ mã trên mọi
bản ghi cùng MST, kể cả bản đầu trống. Ca hồi quy phải đảo thứ tự bản ghi.

## 30/09/2026 (v543): hạ độ lẻ tiền dòng mà không hạ độ lẻ tổng thì chiết khấu chia lệch

- Hoá đơn GSM C26TBB/77683, 889 dòng cước và một dòng chiết khấu, dựng ra thiếu
  21 đồng rồi "Không nhận". Dựng thử trên site thật (System Console, không
  commit): KHÔNG gắn nguồn MInvoice thì đúng tuyệt đối, gắn nguồn thì lệch -21.
- Nguyên nhân: `do_chinh_xac_mua` gán độ lẻ nguồn (0) cho cả `net_amount` của
  dòng, trong khi `net_total` của tờ vẫn 2. ERPNext `apply_discount_amount` làm
  tròn net từng dòng theo độ lẻ DÒNG rồi bù phần chênh theo độ lẻ TỔNG, phần bù
  dưới nửa đồng bị làm tròn mất ở dòng nhưng vẫn cộng vào tổng, dồn qua nhiều
  dòng thành hàng chục đồng.
- Luật: độ lẻ tiền sau giảm của dòng không được thấp hơn độ lẻ tổng của tờ.
  Muốn đổi độ lẻ một trường thì soát mọi phép tính ERPNext trộn trường đó với
  trường khác độ lẻ.

## 30/09/2026 (v544, #395/#397): hạch toán kho bật theo ngày thì mọi lối không áp dụng phải trả về luồng cũ

- Triệu chứng (review Codex và bench): tờ nháp lưu khi ngày bật chưa tới, ghi
  sổ sau khi bật mà lõi báo lỗi kho thì bị reload mất cờ và chặn bán (F5); nháp
  Sản xuất lưu lúc đang bật mang sẵn 621/154 trong dòng, kế toán xoá ngày để
  tắt khẩn thì hook chỉ return sớm nên lần ghi sổ sau vẫn đi 621/154; bench đặt
  ngày về trống mà không dọn cache Settings nên ngày cũ vẫn được đọc.
- Nguyên nhân: giá trị tính lúc lưu nháp được lưu xuống dòng, còn điều kiện
  bật/tắt đổi được giữa lúc lưu và lúc ghi sổ. Return sớm không gỡ những gì lần
  lưu trước đã ghi. Quyết định lùi dựa trên cờ trong bộ nhớ thì phải chốt trước
  khi rollback/reload.
- Cách phòng: công tắc theo ngày phải có đường TẮT tường minh, trả dòng về giá
  trị lõi tự điền; ca bench phải dựng chuỗi lưu lúc bật, tắt, rồi ghi sổ và
  đọc GL. Đổi Single Settings trong ca kiểm thì luôn dọn cache sau khi đặt,
  cả lúc tắt lẫn lúc bật. Nguồn: PR #395, PR #397.

## 01/10/2026 (v546, #398/#400): gỡ một vai khỏi quyền bán hàng phải rà cổng chung, mô đun thu tiền và cửa ngõ nhận `loai`

- Triệu chứng (Codex bốn vòng liên tiếp): gỡ "Bộ phận đặt hàng" khỏi
  `QUYEN_BAN_HANG` thì khoá bếp, kho, thu mua khỏi Việc cần làm (cổng này là
  cổng chung của hơn 150 hàm). Giữ vai trong cổng chung thì các hàm ghi hoá đơn
  bán, công nợ, hoàn tiền vẫn gọi thẳng API được. Cửa ngõ SePay chung nhận
  `loai` từ người gọi và chỉ kiểm cổng chung, nên đi vòng được cửa riêng của
  luồng hoàn tiền. Hai kế toán chỉ vào được màn bán hàng nhờ chính vai đó.
- Nguyên nhân: một tập quyền làm hai việc (cổng chung vận hành và cổng bán
  hàng), và quyền đi theo tên hàm chứ không theo luồng nghiệp vụ.
- Cách phòng: tách một cổng bán hàng riêng (`_kiem_quyen_ban`, tập
  `QUYEN_BAN_VA_KE_TOAN`) cho mọi mô đun bán hàng, công nợ, dòng tiền quầy, hoàn
  tiền; cửa ngõ dùng chung nhận `loai` phải kiểm quyền do luồng đó khai. Trước
  khi gỡ vai, đọc trên site ai đang giữ vai đó mà không có vai thay thế (đã bắt
  được hai kế toán). Ca kiểm quyền đọc đúng tập quyền trong tệp, không tự gõ lại.
  Nguồn: PR #398, PR #400.

## 01/10/2026 - Dư hóa đơn và nhãn Đã chi ngoài ERP (#391)

Màn công nợ cộng PI còn nợ dễ bị hiểu là tổng phải chuyển thêm, dù còn tiền
trả trước/JE chưa phân bổ. File dò chỉ bằng MST và số hóa đơn có thể gộp khác
ký hiệu/năm hoặc dòng chưa chi. Phòng tái diễn: ghi rõ nguồn/phạm vi của tổng,
giữ tiền tệ riêng, đối chiếu chứng từ trước cấn; không tạo DMH/PNK để sửa nợ.
Màn và Excel dùng một bộ lọc và không cắt tổng theo trang. Giảm dư không đồng
nghĩa đã chuyển tiền; dùng “Giảm một phần” thay cho suy đoán “Đã trả”.

### 01/10/2026 - PR402: kiểm đúng đơn vị của dư nợ, cập nhật bằng chứng ngay

Review cho rằng PI ngoại tệ lưu dư theo tiền hóa đơn. Mã core pinned
`accounts/utils.py:update_voucher_outstanding` và ca insert-submit-reload
PI USD100/TK VND xác nhận dư theo tiền tài khoản. Không đổi logic chỉ dựa
nhãn field; ca bench kiểm số 2.500.000 VND và trạng thái chưa giảm một phần.
Đính UNC là tác vụ riêng với cấn tiền: lỗi lưu phải dừng trước phân bổ,
Chỉ lưu UNC không gọi phân bổ. Cập nhật số/link UNC ngay sau lưu để không
hiện nhãn 0 cũ khiến người dùng tải trùng. Có ca Node giữ ba hành vi này.

## 01/10/2026 - v550: lọc "khác giá trị" trên ô Select để trống

Ô Select mới thêm (`vgb_tru_bu`) để trống là NULL trên các hoá đơn cũ. Lọc
`["!=", "Gỡ tay"]` bằng SQL sẽ loại luôn mọi dòng NULL, tức là loại đúng những
tờ chưa trừ bù lần nào, và nhịp trừ bù tự động lặng lẽ không làm gì. Cách
phòng: lọc "khác" trên ô có thể NULL bằng Python sau khi đọc, hoặc dùng
`ifnull`. Bộ chạy đột biến tự viết phải đọc kết quả qua `nen.chay_het` (các
hàm `la`/`dung` ghi lỗi vào danh sách chứ không ném), không đếm ngoại lệ:
lần đầu đếm ngoại lệ ra 0 trên 14 đột biến, tưởng bộ kiểm yếu. Nguồn: v550.
## 02/10/2026 (v551): chi trước hoá đơn về sau thì ghi trả trước NCC, không ghi chi phí rồi đảo bằng bút toán tay

- Ca thật: Adecco hoá đơn 5802 (686.810.159 đ). Hồ sơ APP.26.09.009 chi từ
  TK công ty ghi Nợ 621/6411/6421 / Có 1121 lúc chi (gồm cả VAT), hoá đơn về
  ghi Nợ 6271/6417/6427 + 1331 / Có 331, rồi máy lập bút toán tay
  PKT-2026-00043 Nợ 331 / Có lại chi phí. Số dư cuối đúng nhưng chị Dung bác:
  phiếu kế toán chỉ cho trích lương, khấu hao, phân bổ, trích trước, kết
  chuyển, điều chỉnh; trả tiền NCC phải là phiếu chi Nợ 331 / Có 1121.
- Hệ quả của đường cũ: sổ chi tiết chi phí phát sinh hai chiều, VAT nằm trong
  chi phí trong lúc chờ, hồ sơ chi tháng này mà hoá đơn về tháng sau thì báo
  cáo tháng chi dư chi phí.
- Từ v551: khoản chờ hoá đơn của hồ sơ TK công ty có NCC ghi MỘT phiếu chi
  trả trước (Payment Entry chưa phân bổ). Nối tờ đã ghi sổ thì phân bổ phiếu
  vào tờ qua bộ đối chiếu thanh toán lõi; tờ nháp thì ghi sổ tờ là máy tự
  phân bổ. Khoản mang dấu `tra_truoc` đặt lúc chi: đã chi rồi thì KHÔNG suy
  lại từ cờ chờ hoá đơn, vì cờ đó còn đổi được sau và hồ sơ cũ không có
  phiếu trả trước nào (suy lại là bộ chứng từ hồ sơ cũ bỗng "thiếu phiếu").
- 8 bút toán bù trừ cũ (PKT-2026-00043..00050, 724.316.246 đ) giữ nguyên,
  chỉ liệt kê cho kế toán, không tự sửa.
- Bẫy bench vòng 2: dòng tờ nối có ô `but_toan` là Link tới Journal Entry.
  Ghi tên phiếu chi (Payment Entry) vào đó thì lưu hồ sơ ném "Could not find
  Row #1". Ca tờ nháp vẫn xanh vì đường đó ghi bằng `frappe.db.set_value`,
  vốn BỎ QUA kiểm link. Chứng từ khác loại phải có ô Link riêng (`phieu_chi`),
  và ca kiểm phải đi qua `save()` thật ít nhất một đường, đừng chỉ set_value.

## 02/10/2026 (v552): khai mặt hàng thay thế xong vẫn bị chặn thiếu hàng

- Ca thật: lệnh sản xuất ở kho Baker - Nguyên liệu cần 1.248 ml whipping
  Lescure (NVLT00002), tồn 0. Whipping Pauls (NVLT00329) còn 87.915 ml cùng
  kho, Khải đã khai cặp thay thế hai chiều. Bấm Hoàn tất vẫn bị ERPNext chặn
  "Cần 1248.113 đơn vị".
- Gốc: đường lấy mã thay thế chỉ nằm trong `lo_hang.gan_lo`, mà hàm đó chỉ
  xét dòng THEO LÔ. Cả 15 cặp thay thế đang khai trên site đều là mã không
  theo lô, tức chức năng thay thế chưa từng chạy cho cặp nào. Ca kiểm cũ của
  #206 đều dựng mã theo lô nên không lộ.
- Từ v552: `lo_hang.thay_ma_khong_lo` chạy ngay trước `gan_lo`, cùng luật
  (chỉ luồng sản xuất, mã thay đã khai, cùng đơn vị, món gốc bật cho phép
  thay, mã gốc dùng trước, cùng kho, một túi tồn cho cả phiếu), dòng thay
  mang `original_item` để lệnh vẫn tính đã dùng nguyên liệu gốc.
- Bài học: một tính năng có hai nhánh (theo lô, không theo lô) thì ca kiểm
  phải dựng cả hai nhánh. Trước khi viết ca, đếm dữ liệu thật đang rơi vào
  nhánh nào; ở đây 15 trên 15 rơi vào đúng nhánh chưa có code.

## 03/10/2026 (v565, Zalo #410/#413/#417/#423/#425): gửi tin ra ngoài từ hook chứng từ

- Ca thật: bản tin Zalo cho nhóm bộ phận qua tám vòng Codex review. Mỗi vòng
  lộ một đường làm mất tin hoặc gửi trùng mà ca kiểm cũ không thấy.
- Gốc 1, mất tin: hook xếp việc nền (`frappe.enqueue`) rồi mới ghi sổ. Hàng
  đợi hỏng lúc xếp thì chứng từ vẫn lưu mà không còn dấu vết tin nào.
  Phòng: ghi hộp thư "Chờ gửi" TRONG giao dịch của chứng từ (mỗi dòng một
  savepoint để trùng khoá không làm hỏng giao dịch chính), xếp việc nền sau
  commit, và có lịch 5 phút gửi bù dòng Chờ gửi quá hạn. Worker chết giữa
  chừng thì phải biết đã gọi ra ngoài chưa: đổi sang "Chưa rõ" và commit NGAY
  TRƯỚC lời gọi, nhờ vậy dòng kẹt ở trạng thái trước đó được gửi bù an toàn,
  dòng "Chưa rõ" thì để người xem. Mọi đường gửi đều phải có mốc này (vòng 10
  lộ đường gửi gộp sau giờ im còn thiếu). Lỗi mạng cũng phải chia hai: chưa mở
  được kết nối (DNS, từ chối kết nối) là chắc chắn chưa gửi, trả về chờ gửi
  lại; đứt giữa chừng, hết giờ chờ trả lời, phản hồi 5xx hay không đọc được là
  Chưa rõ (vòng 11 đến 13). Tắt hay gỡ người nhận thì dọn cả tin đang hoãn của họ.
- Gốc 7, nuốt lỗi chết giao dịch (#428): bao() bọc try rộng để Zalo không chặn
  lưu chứng từ, nhưng deadlock khi ghi hộp thư thì MariaDB đã rollback cả giao
  dịch, kể cả savepoint; nuốt lỗi đó là chứng từ báo thành công mà không còn gì
  trong sổ. Phòng: mọi try rộng quanh lệnh ghi cơ sở dữ liệu phải để lỗi chết
  giao dịch (deadlock, chờ khoá quá hạn, mất kết nối) đi lên.
- Gốc 2, gửi trùng: hai tiến trình cùng nhận một dòng. Phòng: nhận bằng
  UPDATE có điều kiện trạng thái kèm mã lô, commit, đọc lại mã lô mới gửi.
- Gốc 3, cài đặt bị đè: webhook ghi mã chat mới vào Vagabond Settings đọc
  qua cache rồi ghi lại cả chuỗi, hai tin tới cùng lúc thì mất một. Phòng:
  khoá dòng Singles (select for update) và đọc thẳng bảng, không qua cache.
- Gốc 4, nối bot "thành công" giả: setWebhook lưu URL dù xác minh hỏng, và
  bot chưa bật quyền vào nhóm thì không nhận tin nhóm. Phòng: đọc kết quả
  xác minh, gọi getMe kiểm can_join_groups, báo rõ cho người cài.
- Gốc 5, ô gõ tay: mã chat, loại tin, chủ đề, giờ im gõ sai thì nhóm bị bỏ
  lặng lẽ. Phòng: chỉ chọn từ danh mục hoặc từ nhóm đã nhắn bot, kiểm lại
  lúc lưu.
- Gốc 6, ca kiểm bắn tin thật: bench kiểm thật gọi tới Zalo. Phòng: cờ chế
  độ kiểm chặn mọi lời gọi ra ngoài.
- Bài học chung: tác dụng phụ ra ngoài hệ (Zalo, email, Telegram) phải đi qua
  hộp thư ghi cùng giao dịch, có người nhận độc quyền và có đường gửi bù.
  Nguồn: PR #413, #417, #423, #425.


## 03/10/2026 - Chữ web, font gốc và tra địa chỉ (#367)

- Headline tiếng Việt từng bị rẽ sang font hệ thống. Kiểm cmap font gốc và
  computed style trên 390 px trước khi quyết định fallback; Vagabond Sans
  hiện có đủ dấu của câu đã duyệt.
- Chỉ thay chữ tĩnh không làm mọi câu sửa được: các renderer giỏ/chi tiết,
  lỗi OTP và biên nhận còn tự tạo chuỗi. Dùng khóa chung, giữ biến số và
  escape đúng sink; kiểm nhãn chứa thẻ qua renderer thật, không chỉ grep.
- Không chốt nhãn động vào object trước khi tải CMS. Dùng getter hoặc đợi
  nhãn có giới hạn thời gian; thử sửa tên bánh trong Editor và Undo thật.
- Che địa chỉ ở UI không bảo vệ response API. tra_khach phải kiểm số trong
  phiên OTP trước HTTP Pancake, no-store và bỏ response nếu người dùng đã
  chuyển sang số khác. Ca Guest/sai số/đúng số gọi thân hàm thật với HTTP stub.
- Khi phát hành chữ được duyệt, chuyển nháp và công khai riêng, giữ snapshot
  lịch sử; không lấy nguyên bản nháp để đẩy công khai trong migration.
- Nhãn CMS phải escape cả nhánh lỗi/không có dữ liệu; chỉ thử happy path
  không đủ. Ca canary dùng đúng renderer lỗi thuế, phí giao, địa chỉ và quầy.
- Preview cần làm mới hộp đang mở mà giữ lựa chọn và scroll. Đối chiếu
  finding với sự kiện thật trước khi sửa: cards/cart đã cập nhật, phần còn
  thiếu là phụ kiện/tình trạng và chi tiết hàng mùa.


## 01/10/2026 (#401 vòng 4): giá kiểm kê phải có mốc và lỗi tra giá cần đường thử lại

- Item.last_purchase_rate và valuation_rate là giá hiện tại, không chứng minh
  được giá tại ngày giờ kiểm kê, kể cả phiếu ghi sớm hơn trong cùng ngày.
  Chỉ tự gợi ý từ SLE đúng kho hoặc kho khác cùng công ty tới mốc phiếu.
  Không có thì kế toán nhập giá đã xác minh, không tự lấy giá Item.
- Core ERPNext tại SHA bench de591661, StockReconciliation.validate_data,
  còn lấy Item Price/Item khi giá trống. Hook phải báo thiếu giá trước đường
  đó; chỉ bỏ fallback trong helper vẫn chưa đủ bảo vệ Desk.
- Lỗi API khác với đọc thành công nhưng chưa có giá: khi API lỗi, ẩn ô nhập
  tay và nút ghi sổ, hiện lỗi cùng nút Thử lại. Giữ chặn trong submit để
  không thể gọi vòng. Ca DOM chạy lỗi, thử lại thành công rồi ghi sổ.
- Hai ca hồi quy mới đỏ trên 70741d06. Cổng local đạt sau khi dùng đúng
  Python/Node runtime; lượt đầu thiếu Node trong PATH không phải lỗi code.
- Bench nền 70741d06 đỏ 3/325 ca ở mỗi lượt: một ca nhập tồn mới dùng tài
  khoản chi phí; hai ca qty không đổi + giá 0 bị core de591661 loại là không
  thay đổi. Fixture mới dùng Opening Stock/tài khoản Temporary cho tồn mới,
  và đếm 9 từ tồn 10 cho hai ca giữ giá 0. Không khẳng định core bench hỗ trợ
  định giá về 0 khi số lượng không đổi.


## 04/10/2026 - Phạm vi soạn chữ pháp lý website (#367)

Anh Việt trực tiếp yêu cầu mở sửa toàn bộ chữ, gồm pháp nhân/MST/địa chỉ.
Đây là override quyết định khóa ở #431, không là thay dữ liệu công ty ERP.
Giữ kiểm HTML injection, revision và quyền Marketing; đổi ca kiểm cấm sửa
thành kiểm nội dung được lưu/xuất đúng và fallback, không giữ luật cũ trái duyệt.
## 04/10/2026 (v573): đếm "đã bán trong ngày" theo posting_date bị đếm hai lần khi bill đổi ngày

- Dễ báo: hàng tặng out bill tối ngày 1, bảng Kiểm kho ngày 1 trừ 1 cái; anh
  Việt duyệt sáng ngày 2 thì ngày 2 trừ thêm 1 cái. Nút duyệt (và OTP kế toán)
  đi qua `_doi_ngay_ban_nhap`, đổi `posting_date` sang ngày ghi sổ cho đúng
  ngày HĐĐT. Ngày 1 thường đã chốt nên không đo lại, ngày 2 đếm thêm.
- Ngày ghi sổ và ngày bánh rời quầy là hai việc khác nhau. Bill đổi ngày lần
  đầu thì giữ ngày bán gốc ở `vgb_ngay_ban`; mọi chỗ đếm số bán dùng một nguồn
  `ngay_ban.dk_sql`. Thêm chỗ đếm mới thì gọi hàm đó, không lọc thẳng
  `posting_date`.
- Ca kiểm chạy SQL thật của hai hàm đếm trên sqlite (chỉ đổi cú pháp tham số),
  không dò chuỗi. Ca dò chuỗi "không còn chỗ lọc thẳng" lúc đầu khớp cả
  docstring nên đột biến không đổ; phải dò đúng lời gọi.
- Codex #438: ô `read_only` chỉ khoá giao diện, Desk/API vẫn ghi được. Ô
  quyết định số liệu (ở đây là ngày trừ bánh) phải có hook validate chỉ cho
  máy ghi (cờ trên doc), giá trị ngoài gửi vào trả về giá trị đang lưu; hàm
  máy ghi cũng phải đọc giá trị đang lưu trong cơ sở dữ liệu, không đọc giá
  trị trên đối tượng.


## 05/10/2026 (v574): "chưa được whitelist" có thể chỉ là phiên đăng nhập đã mất

- Loan Anh đính UNC ở màn Công nợ thì nhận "You are not permitted to access
  this resource. Login to access ... nap_tam is not whitelisted". Hàm có
  `@frappe.whitelist()` và có trong danh sách cửa ngõ. Gốc: tài khoản để 2 phiên
  cùng lúc, đăng nhập lần thứ ba đẩy văng phiên của máy đang mở màn.
- Frappe trả 403 PermissionError (không phải 401) cho lời gọi của khách, nên app
  coi là thiếu quyền. Câu báo đổi theo ngôn ngữ site, đừng dò chữ. App hỏi lại
  `frappe.auth.get_logged_user` khi gặp 403 PermissionError để phân biệt.
- Gặp báo "chưa whitelist" thì kiểm Activity Log đăng nhập và số phiên cùng lúc
  của tài khoản TRƯỚC khi đi tìm lỗi quyền hay cấp thêm vai trò.


## 05/10/2026 (v576): ca kiểm node có lời hứa treo mãi thì thoát mã 0, cổng tưởng là đạt

- Codex #441: lời hỏi "tôi là ai" không có hạn giờ. Dựng lại bằng mạng giả treo
  mãi thì bộ kiểm hành vi KHÔNG báo hỏng: node hết việc trong hàng đợi là tự
  thoát với mã 0, không in dòng tổng nào. kiem_truoc_deploy.sh chỉ nhìn mã thoát.
- Bộ kiểm hành vi có chờ lời hứa thì đặt cờ "đã chạy tới cuối" và bắt sự kiện
  exit: chưa tới cuối thì in HONG và đặt mã 1 (xem hanh_vi/phien_mat_574.js).
- Codex #442: thêm kiểu phiếu mới (gom nhiều pháp nhân) phải rà MỌI đường xử lý
  phiếu đó, kể cả đường khớp tay theo giao dịch. Phiếu thu ERPNext chỉ một khách.
  Lần đầu cho đi đường từng hoá đơn như SePay tự khớp thì sai: đường đó ghi sổ
  thẳng, bị hook UNC chặn, lỗi bị nuốt mà phiếu đòi nợ vẫn báo đã thu. Cách đúng:
  mỗi khách một phiếu thu NHÁP cùng giao dịch, chung mã nhóm `vgb_nhom_gd`; luật
  "một giao dịch một phiếu" chỉ nới cho phiếu cùng nhóm (`cung_nhom_da_noi`).
- Đường SePay tự khớp và khớp tay KHÔNG chọn giao dịch (`ghi_thu_cho_phieu`) lập
  phiếu thu ghi sổ thẳng, sẽ bị `chan_thieu_dinh_kem` chặn với phiếu lập sau
  16/08. Tồn đọng có sẵn từ trước, chưa sửa trong v576.

## 05/10/2026 - Web order: xem giỏ như một khách thật (#367/436)

- Thẻ đúng giá không đảm bảo hộp chi tiết đúng cỡ: cả hai phải theo cùng
  nguồn today/order; giữ nguồn đó khi sửa giỏ sau reload.
- Nến 60x240 bị crop bởi nút thấp có overflow:hidden; đo cả bounding box
  ảnh và nút tại390px. object-fit không đủ nếu chiều cao ảnh vẫn cố định lớn.
- Thêm nhanh cần đường sửa chính dòng giỏ, không hướng dẫn mở bánh để thêm
  lần nữa. Khóa gộp phải chuẩn hóa dụng cụ 0 để không tách dòng giống nhau.
- Promotion/recruitment CMS là nội dung; coupon tài chính và hồ sơ ứng viên
  không được suy ra từ số mẫu/biểu mẫu prototype. Dùng nháp ẩn, ảnh thay được,
  ngày Việt Nam, chống URL/thẻ HTML, và giữ luồng revision sẵn có.
- GET phí giao ok0/ahamove_loi cần log server; không tuyên bố sửa bằng nút
  thử lại và không biến lỗi báo giá thành phí0.

## 05/10/2026 (v577): thêm luật chặn ở hook mà không rà lối "nuốt lỗi" thì lối đó chết im lặng

- Hook `chan_thieu_dinh_kem` (16/08) bắt phiếu thu ngân hàng có UNC mới ghi sổ.
  `ghi_thu_cho_phieu` (04/09) lập và ghi sổ thẳng, lại cố tình NUỐT lỗi từng hoá
  đơn "để không làm rớt việc đánh dấu". Ghép hai thứ: phiếu đòi nợ DNTT-26-10-00004
  thành "Đã thu đủ", 17 phiếu thu hỏng hết, 17 nháp hỏng ở lại giữ phần nợ, bill
  vẫn ở Đang nợ. Thêm luật chặn mới thì grep mọi lối gọi `submit()` của doctype đó
  và mọi `except` nuốt lỗi quanh nó.
- Lối có `try/except` nuốt lỗi quanh `insert()` rồi `submit()` mà không có điểm
  lưu thì để lại bản nháp. Bản nháp đó vẫn được tính là "đã phủ nợ" ở nơi khác.
  Dùng `frappe.db.savepoint` và lùi đúng lần làm hỏng, hoặc ném hẳn ra.
- Hộp chọn lọc ĐÚNG số tiền thì giấu mất giao dịch thật khi khách trả gộp (Kiệt
  Tác chuyển 9.550.000 cho phiếu 8.450.000), người dùng bị đẩy sang lối thoát
  hiểm. Hộp chọn để đưa ra mọi ứng viên, xếp khoản khớp lên đầu, có ô tìm.
- DOM giả (`hanh_vi/dom_gia.js`): chữ sau thẻ đóng dồn vào chữ của thẻ cha, nên
  textContent đổi thứ tự quanh `<b>`. Dò câu thì chọn đoạn KHÔNG vắt qua thẻ.
  Đừng viết điều kiện "hoặc" cho dễ đạt: ca v577 đã xanh oan vì vế hoặc khớp nhãn nút.
- Chạy đột biến Python nhiều lần liên tiếp: đột biến GIỮ NGUYÊN độ dài dòng
  (đổi `dung + khac` thành `khac + dung`) có thể chạy trên bytecode cũ trong
  `__pycache__` và báo LỌT oan (v577, M10). Chạy đột biến với
  `PYTHONDONTWRITEBYTECODE=1` và xoá `__pycache__` trước mỗi đột biến.
- QT-20 áp cả cho phiếu NHÁP máy tự lập hỏng (Codex #444 vòng 2): không
  `delete_doc`, gỡ khỏi hoá đơn, đổi khoá, ghi vết lên chính phiếu.
- Thư "đã nhận thanh toán" gửi từ giữa request chưa commit (ghi sổ phiếu thu)
  phải xếp hàng (`delayed=True`) trong cùng giao dịch, không gửi ngay.
- Việc phải xảy ra "sau khi ghi sổ" (gửi thư báo khách) mà chỉ gọi từ NÚT của
  app thì kế toán ghi sổ thẳng trên Desk là việc đó không bao giờ chạy (Codex
  #444 vòng 4). Đặt ở hook `on_submit` của doctype, nút app không gọi riêng.
- Luật "chỉ gửi khi sổ sạch" đặt ở hàm gọi tự động thì nút gửi tay vẫn lách
  qua. Đặt điều kiện trong CỬA gửi chung mà mọi lối đều đi qua.
- "Lập hỏng thì vẫn ghi nhận tiền, ghi lý do" chỉ đúng khi còn đường làm lại.
  SePay gạch giao dịch LỚN hơn phiếu: khớp lại hỏng y như cũ, huỷ thì bị cấm vì
  đã có `ma_gd`, phiếu kẹt vĩnh viễn (Codex #444 vòng 5). Luật cấm huỷ phải
  hỏi giao dịch đã sinh chứng từ chưa, không chỉ "đã gạch hay chưa".
- Hook chạy trong `on_submit` mà nuốt mọi lỗi thì deadlock, chờ khoá, mất kết
  nối cũng bị nuốt: bút toán đã lùi mà màn báo ghi sổ xong. Dùng
  `vagabond.loi_csdl.chet_giao_dich` để ném lại các lỗi đó.
- Việc phụ sau ghi sổ (thư báo) mà chạy NGAY trong `on_submit` thì phải soát
  mọi `except` của cả chuỗi hàm dựng thư dùng chung, sót một chỗ là deadlock
  bị nuốt (Codex #444 vòng 6 bắt ở `db_set` dấu đã gửi). Cách gọn: `on_submit`
  chỉ `frappe.db.after_commit.add(...)`, việc nền tự đọc lại sổ rồi mới làm,
  như `can_tru_san`, `tru_kho_bu`, `thu_tien.gui_thu_khi_ghi_so`.
- Dời việc phụ ra sau commit thì phải có lưới gửi bù: lời xếp việc nền nằm
  trong Redis, Redis lỗi đúng lúc đó là mất hẳn (Codex #444 vòng 7). Thêm nhịp
  quét theo chứng từ GẦN ĐÂY (không quét cả lịch sử kẻo gửi cho phiếu cũ).


## 06/10/2026 (v581, Zalo #410, PR #447): bảng con chật trên Desk và nút trùng lối vào

- Triệu chứng: anh Việt gửi ảnh mục "Nhóm nhận tin" trên Cài đặt. Bảng con
  (Table) nằm trong nửa cột nên mỗi ô chỉ còn vài chữ ("ERP ...", "zgr-d...",
  "thong..."), lộ mã nội bộ, rất khó nhập và thêm dòng. Nút Gửi thử có sẵn từ
  v565 nhưng giấu trong menu Zalo trên thanh công cụ nên anh không thấy.
- Nguyên nhân: bảng con của Frappe chỉ hiện vài cột hẹp, ô Select/Data hiện
  nguyên giá trị lưu là mã. Đặt bảng có ô mã nhiều lựa chọn vào mục hai cột là
  chắc chắn chật. Nút quan trọng chỉ để trong menu thanh công cụ thì người dùng
  không tìm ra.
- Cách phòng: bảng con có mã lựa chọn hoặc mã máy thì ẨN lưới trên Desk, vẽ mỗi
  dòng thành thẻ đọc được (tên tiếng Việt, trạng thái, nút Sửa) trong một trường
  HTML, và sửa qua hộp thoại có ô tích kèm dòng giải thích. Bảng gốc vẫn là nơi
  lưu, giá trị lưu giữ đúng định dạng cũ. Nút hay dùng đặt ngay trong mục.
- Codex #447 vòng 1: thêm hàng nút mới có chặn "chưa lưu" mà để menu cũ trên
  thanh công cụ gọi cùng máy chủ KHÔNG chặn thì menu cũ chạy trên cấu hình cũ
  rồi reload_doc xoá bản nháp. Hai lối vào cho một việc phải đi qua MỘT hàm
  (`zaloTacVu`), và ca kiểm phải chạy thật mọi hàm refresh đã đăng ký rồi bấm
  từng nút trên thanh công cụ, đếm số nút cùng tên để lộ khối đăng ký cũ còn sót.

## 06/10/2026 - PR436: dữ liệu đến trễ và nút nổi

- Giá giỏ lấy từ catalog nhúng lúc reload vẫn có thể cũ: phải đồng bộ dòng
  giỏ khi API catalog trả về, kiểm phản hồi trễ và giá 0 bằng hành vi.
- Danh sách vị trí Editor phải khớp renderer. Đổi loại chiến dịch về loại
  thường cần trả vị trí hợp lệ, backend cũng chặn vị trí làm mất khối.
- CSS clamp mới không có tác dụng nếu rule cũ html body .h1 thắng; đo
  computed font trên390 và sửa tại rule gốc, đừng cộng thêm override.
- Escape ở popup phụ phải dừng handler đóng sheet/điều hướng của trang.
  Chỉ nhìn popup đóng chưa đủ: kiểm URL và focus sau phím Escape.
- Ẩn khối mặc định trong code không đổi CMS đã xuất bản. Patch cần xử lý
  nháp/công khai riêng, giữ lịch sử, không xuất bản nháp để sửa phần lặp.
- Link Zalo số điện thoại không phải bằng chứng OA. Thiếu mã thì giữ nút
  ẩn, cho nhập link OA trong Editor; không gán nhầm tài khoản.

### 06/10/2026 - PR436: OA có đường dẫn theo tên

Ảnh OA anh Việt cung cấp có zalo.me/thevagabondsaigon; mở browser xác nhận
đúng The Vagabond Pâtisserie. Bộ kiểm chỉ nhận ID số sẽ loại oan OA hợp lệ.
Nhận cả tên công khai và ID dài, giữ HTTPS/đúng host/không credentials;
kiểm renderer và mobile390. Cấu trúc URL không chứng minh tài khoản đã xác
thực: danh tính OA lấy từ nguồn chủ sở hữu và trang công khai.

### 06/10/2026 - PR436: logo kênh bán phải biên tập được

Dùng chữ viết tắt thay logo làm popup kênh thiếu nhận diện. Logo cần là ảnh
CMS, tách logo nút mở khỏi logo từng kênh; tên trợ năng vẫn có khi bỏ chữ
trên nút. Kiểm cả đổi ảnh trong iframe, ảnh hỏng và mobile; ảnh tải thành
công chưa chứng minh đọc được (logo trắng trên nền trắng đã gặp khi thử).

## 03/10/2026 - #420: đủ tổng nguồn chưa phải đủ tiền về (Codex, mang sang v579)

Báo cáo vendor ngày/tháng có thể chứa cùng sự kiện; tên file và hash byte
không đủ chống trùng kinh tế. Khóa cần phạm vi công ty/vendor/merchant/tiền
tệ và ID ổn định; nội dung thay đổi phải giữ lỗi để kiểm bản điều chỉnh.
Phép xem trước dùng snapshot chỉ bắt trùng đã biết, không thay khóa DB ở cửa
ghi. Nhận phần hợp lệ phải chặn cả nhóm ID lặp, không để bản đầu còn Mới.

## 05/10/2026 - Mẫu Drive không tự có trong filesystem của cloud (#422)

Trước kết luận người dùng chưa gửi mẫu, tra hồ sơ issue và nguồn Drive đã
được cấp. Sheet chuyển đổi có thể đọc được nhưng không chứng minh byte CSV/XLS
gốc hay đơn vị tiền. Không nhân/chia 1.000 chỉ để làm tổng khớp. Khóa sự kiện
không chứa loại có thể thay đổi: cùng ID đổi loại phải vào luồng xung đột.

## 05/10/2026 - Nhóm ID và cột nguồn (#422 v577 của Codex)

Gom căn cước sự kiện trước kiểm nội dung: nếu đợi tiền hợp lệ mới đăng ký
ID thì bản lỗi không giữ được bản trùng, nút nhận phần hợp lệ vẫn lọt.
Reader thô giữ mảng cột theo vị trí; header trống/trùng không đồng nghĩa
nguồn hỏng. Kiểm mọi schema fixture, không chỉ hai mẫu đơn giản.

## 06/10/2026 - #450: bộ giả lập trang cắt mất bước khôi phục giỏ

`gia_lap_trang.js` cắt cả đuôi khởi động của `banh.html` (để bỏ gọi mạng),
nên cắt luôn `phucHoiGio()`. Mọi ca "tải lại giữ giỏ" vì thế đặt
sessionStorage SAU khi trang chạy rồi tự gọi lại `phucHoiGio()`, tức là không
bao giờ đi đúng thứ tự tải trang thật. Nay bộ giả lập giữ riêng bước đó và
nhận tham số nạp sẵn sessionStorage trước khi mã trang chạy. Ca tải lại phải
dùng tham số đó, không tự gọi hàm khôi phục.

Ca kiểm trên bench tải PDF giả (`%PDF-1.4` + chữ) chết ở `File.check_content`
của Frappe (mở thử PDF để dò mã chạy ngầm) trước khi tới phần cần kiểm. Ca
kiểm site dùng PDF đúng cấu trúc; cửa tải lên phải đổi lỗi thư viện đọc PDF
thành lời người dùng. Tầng khung không thấy được lỗi này vì không có Frappe.

## 07/10/2026 - v583: màn Đối soát lỗi 417 ngay sau deploy

`ds()` gọi `frappe.get_all(..., order_by="coalesce(den_ngay, creation) desc")`.
Frappe v16 chỉ nhận tên trường trong `order_by` của `get_all`/`get_list`, có
hàm là trả ValidationError 417, nên danh sách đối soát không mở được trên site
thật. Tầng khung giả lập `get_all` nên không thấy; ca bench duy nhất gọi `ds()`
là ca thu ngân, bị chặn quyền TRƯỚC truy vấn nên cũng không chạm tới. Phòng:
mỗi cửa danh sách mới phải có một ca bench gọi thật bằng người CÓ quyền; tầng
khung có ca dò cấm `order_by` có dấu ngoặc trong mọi tệp .py của app. Cần sắp
xếp theo biểu thức thì dùng `frappe.qb`, không nhét vào `order_by`.

Ca dò mã nguồn đầu tiên viết cho lỗi này xanh mà không dò gì: đường dẫn gốc
`.../kiem_thu/../..` tự chứa chữ `kiem_thu`, nên phép bỏ thư mục kiểm bỏ qua
cả app. Dùng `abspath` và so từng phần của đường dẫn tương đối, và chốt số tệp
đã dò phải lớn hơn 0.

## 07/10/2026 - #452: cài nhóm Zalo nhận tin Phát hành mà không có tin nào

Anh Việt bật bot Zalo, thêm nhóm và tích loại tin Phát hành, nhưng sổ tin
kênh không có dòng nào. Nguyên nhân: bản tin phát hành chỉ có đường Telegram
(bot GitHub đọc comment `[ĐÃ DEPLOY]`), còn trong app không chỗ nào gọi
`kenh_zalo.bao("phat_hanh")`. Màn cài đặt vẫn cho chọn loại tin đó nên trông
như đã chạy. Phòng: mỗi loại tin hiện cho người dùng chọn phải có ít nhất một
nơi phát thật và một ca kiểm chốt nơi phát đó; thêm kênh mới cho một loại tin
thì đọc từ ĐÚNG nguồn của kênh cũ (ở đây là khối `telegram-release`) để hai
kênh không lệch nội dung. Ở #452 còn gặp pháp nhân demo của ERPNext
(`Global Defaults.demo_company`) lọt vào hộp chọn pháp nhân: danh sách pháp
nhân cho người dùng chọn phải bỏ công ty demo, trừ khi nó là mặc định hoặc
là công ty duy nhất.

## 08/10/2026 - #452: ô kho cấu hình làm món biến mất khỏi ô tìm

Người có User Permission theo kho tìm "Chocolatine" không ra "Bánh
Chocolatine, Mini size", dù món có thật và cùng nhóm với bản Full size.
Nguyên nhân: món vừa được khai "Kho nguyên liệu mặc định khi sản xuất"
(Link Warehouse), và Frappe áp User Permission lên MỌI ô Link tới doctype bị
giới hạn, kể cả ô chỉ để cấu hình, nên món khai kho ngoài danh sách của họ bị
ẩn khỏi `get_list`. Ca bench của ô tìm v583 chạy bằng Administrator nên không
thấy lớp quyền này. Phòng: ô Link do app thêm mà chỉ để cấu hình (kho nguồn,
kho mặc định) phải có `ignore_user_permissions: 1`; tầng khung có ca dò mọi
khai báo Link Warehouse trong mã nguồn. Ca bench cho ô tìm hay danh sách phải
có một lượt chạy bằng tài khoản thường có User Permission, không chỉ Administrator.
## 08/10/2026 - v586: đăng ký tiệc vượt số vé dù đã khoá hàng

Cửa đăng ký tiệc khoá hàng nội dung web rồi mới đếm vé, nhưng câu đếm là đọc
thường. MariaDB REPEATABLE READ giữ ảnh chụp từ lần đọc đầu (tra mã lần gửi),
nên khách thứ hai chờ khoá xong vẫn thấy tổng cũ. Tái hiện hai kết nối thật:
tiệc 40 vé, đã có 38, hai khách mỗi người 2 vé, ghi được 42/40. Khoá thôi
chưa đủ: MỌI phép đọc sau khoá phải là đọc hiện tại (`for update`), kể cả đọc
lại mã lần gửi. Bài học trùng #368 và đặt bàn, ghi lại vì lặp lại lần ba.

Ca kiểm cũ của cửa này thay hẳn `dem_ve` bằng hàm giả để đếm thứ tự, nên
không bao giờ nhìn thấy câu SQL đếm vé. Ca kiểm thứ tự khoá phải giữ hàm thật
và soi đúng câu nó chạy, không thay chính chỗ đang kiểm.

Cũng PR đó: điểm nhận bánh "danh sách rỗng thì về điểm cũ" là sai, vì rỗng là
marketing đã tắt hết. Phân biệt "chưa tải" với "đã tải mà rỗng", và máy chủ
chặn lại lúc gửi đơn theo đúng một luật (`noi_dung_web.diem_nhan`).

Vòng 2 cùng PR (Codex #453): giỏ trong trình duyệt nhớ điểm nhận theo SỐ THỨ
TỰ, nên khi marketing xoá một điểm thì khách bị chuyển lặng lẽ sang điểm đứng
sau; máy chủ tra điểm theo TÊN nên hai cửa hàng trùng tên lấy nhầm địa chỉ.
Thứ gì người dùng chọn từ một danh sách người khác sửa được thì phải giữ bằng
mã ổn định; mã mất thì bắt chọn lại, không tự chọn hộ. Ca bench web #245 cũng
phải sửa khi API công khai thêm phần dẫn xuất, vì nó so nguyên tập khoá.

Vòng 3 (Codex #454): đã sửa đếm vé là đọc hiện tại nhưng cấu hình tiệc (số
vé, ẩn hiện) vẫn đọc thường sau khoá. Marketing giảm 40 xuống 20 vé lúc khách
đang chờ khoá thì khách vẫn thấy trần 40 trong ảnh chụp: tái hiện ghi được
21/20. Cách sửa gọn: cho phép khoá đọc luôn dữ liệu cần dùng
(`_ban_cong_khai(khoa=True)`), không khoá một câu rồi đọc ở câu khác. Ca kiểm
cũ thay `_ban_cong_khai` bằng hàm giả nên lại che đúng chỗ này; trang giả nay
phân biệt đọc thường (ảnh chụp) với đọc `for update` (bản hiện tại).

Vòng 4 (Codex #454, cùng ngày): đơn tự lấy kiểm điểm nhận bằng phép đọc
thường, không xếp hàng với Marketing, nên điểm vừa tắt vẫn có thể vào sổ.
Không thể khoá từ đầu `tao_don` vì giữa đó còn gọi Pancake tra mã hàng;
cách đúng là giữ phép chặn sớm (đọc thường) và thêm phép QUYẾT ĐỊNH đọc có
khoá ngay trước khi ghi, trong khoá ghi, rồi commit. Cùng vòng: máy chủ nâng
trần khối 30 lên 80 nhưng bảng Nâng cao vẫn chép cứng 30, nên chặn sớm. Trần
nay đi kèm `doc_bang`; JS không tự đặt số.

## 08/10/2026 - v587: thẻ tiệc chữ dài kéo tuột, tên ưu đãi chìm

Minh Vũ thử thẻ Tiệc với bài giới thiệu dài và thực đơn 12 món: thẻ hai cột
kéo dài theo chữ, nút Đăng ký rơi xuống đáy, ảnh bị kéo giãn. Tên ưu đãi dùng
màu xanh thương hiệu bằng chữ viết tay nét mảnh trên nền xanh đen, tương phản
khoảng 4:1, nhìn như chữ chìm. Bài học: khi marketing được tự nhập chữ thì
mọi khung phải chịu được chữ dài gấp mười lần mẫu; thiết kế xong phải thử
với bài thật của marketing chứ không chỉ dữ liệu mẫu ngắn. Sửa: chữ gấp 5
dòng có Đọc tiếp, thực đơn thành nhãn, hộp thông tin nổi trên ảnh ngang,
tên mục chữ trắng. Ngưỡng gấp tính theo số ký tự để trang khách và khung
"Khách sẽ thấy" vẽ giống nhau và kiểm được bằng node.

## 08/10/2026 - #457: Excel vendor khai kích thước sheet sai, openpyxl đọc một ô

Tệp doanh thu Xanh SM tải từ cổng là xlsx hợp lệ, mở Excel thấy đủ bảng, nhưng
phần `<dimension ref="A1"/>` trong sheet khai sai. openpyxl tin lời khai nên
`iter_rows` trả đúng một ô trống, máy kết luận "Chưa nhận ra mẫu" trong khi mẫu
đã có từ v579. Mất gần một ngày vì kế toán và kỹ thuật đều nhìn Excel thấy
đúng. Cách phòng: `doc_xlsx` gọi `ws.reset_dimensions()` trước khi đọc mọi
tệp; ca kiểm dựng xlsx thật có dimension sai. Bài học rộng hơn: khi người dùng
gửi tệp "máy không nhận" thì in ba dòng đầu máy đọc được ra màn, lỗi này lộ
ngay từ dòng đầu là trống.

## 10/10/2026 - v589: bộ giả lập trang chỉ chờ setTimeout, ca xem trước ưu đãi treo

Trang đặt bánh hỏi máy chủ mức giảm mỗi lần vẽ lại giỏ. Gọi thẳng `fetch` thì
ca kiểm node đọc tóm tắt trước khi câu trả lời về, vì `CHO_XONG` trong
`gia_lap_trang.js` chỉ chờ các việc đặt qua `setTimeout`. Không phải lỗi của
trang mà là giới hạn của bộ giả lập, nhưng nó che được lỗi thật nếu ca kiểm
"cho chắc" gọi thêm hàm. Cách làm: lời gọi mạng từ sự kiện vẽ lại đi qua
`setTimeout` (cũng là debounce, bớt gọi máy chủ khi khách bấm liên tục), và
mức giảm chỉ hiện khi khoá giỏ của câu trả lời trùng giỏ hiện tại. Đột biến
bỏ kiểm khoá giỏ lúc đầu KHÔNG làm đổ ca nào; đã thêm ca đổi giỏ rồi đọc tóm
tắt NGAY, trước khi máy chủ trả lời.

Thêm (Codex #460): hạn mức chương trình (tổng lượt, lượt mỗi ngày) soát ở
bước tính nhưng ghi lượt SAU khi gọi Pancake, nên hai đơn tranh lượt cuối cùng
lọt. Cách phòng: trong khoá ghi, commit trước rồi khoá hàng chương trình
(FOR UPDATE), tính lại, ghi lượt, commit, rồi mới gọi dịch vụ ngoài; bị từ chối
thì trả lượt. Commit trước khoá là bắt buộc: trong REPEATABLE READ, lần đọc sau
khoá vẫn thấy ảnh chụp cũ từ đầu yêu cầu nếu giao dịch đã đọc gì trước đó.
Lượt ghi theo đúng ngày đã dùng để soát (ngày nhận bánh), không theo hôm nay.
Vòng 2 cùng PR: (1) so lần tính lại bằng CẢ số tiền lẫn bộ chương trình đã
khoá, vì hai chương trình bằng giá có thể đổi chỗ cho nhau; (2) phép giữ
lượt trước dịch vụ ngoài phải là phép CHẶT (lỗi là ném, rollback, không gửi),
không dùng lại hàm ghi vết kiểu "lỗi chỉ log"; (3) phép trả lại khi bị từ
chối có thể lỗi, nên cần việc định kỳ dọn theo trạng thái đơn chứ không chỉ
một lần thử. Và: chạy đột biến ở tiền cảnh mà bị cắt giữa chừng thì tệp có
thể kẹt ở bản đột biến; luôn chạy đột biến ở nền và soát `git diff` sau đó.
Vòng 3: khoá chỉ có tác dụng khi MỌI đường ghi lượt cùng xin khoá đó; quầy
và web dùng chung chương trình nên quầy cũng phải khoá rồi ghi lượt trước
commit (`tinh_co_khoa`). "Lấy bộ có lợi nhất" phải thử cả bộ chương trình
cộng dồn được, không chỉ tất cả hoặc từng cái lẻ.
Vòng 4: "trả lượt" là huỷ mềm (ô `da_tra`), không xoá dòng (QT-20); mọi chỗ
đếm hạn mức, báo cáo và việc dọn định kỳ phải bỏ dòng đã trả.

## 11/10/2026 - Web Vue: mô đun ES né mất ?v= nên phải có import map

Site trả `/assets` với cache immutable (#310), trang cũ ghi tay `?v=<băm>`
trên từng thẻ link/script. Mô đun ES nạp nhau bằng `import './x.js'`, đường
đó không gắn được `?v=`: deploy xong khách cũ vẫn chạy mô đun cũ mãi mãi, và
trộn mô đun cũ với mới là lỗi khó đoán. Cách phòng: trang khai import map ánh
xạ từng URL mô đun sang URL có `?v=<băm>`, do `cong_cu/ma_bam_web_vue.py` sinh;
ca `thu_web_vue.py` gọi `--kiem` để quên chạy là CI đỏ. Và: node trên máy CI
(bản 20) không tự nhận mô đun ES trong tệp `.js`, cần `web_vue/package.json`
khai `"type": "module"`, thiếu là ca kiểm chết ngay ở dòng `import`.



Vòng 5 (PR #461): khoá xem trước ở trình duyệt chỉ cho biết giỏ có đổi, không
chứng minh hạn mức ưu đãi trên máy chủ còn nguyên. Triệu chứng là khách thấy
giảm 50.000 nhưng đơn có thể được ghi với mức khác nếu lượt cuối vừa hết.
Cách phòng: trình duyệt gửi `giam_da_xem`, máy chủ vẫn tự tính lại rồi từ chối
cả trường hợp giảm tăng lẫn giảm xuống khi hai số khác nhau; trả bảng mới để
khách xem và tự bấm lại. Phép so phải sau tìm trùng để lần gửi lại cùng nonce
luôn nhận biên nhận cũ. Liên kết lượt dùng với hoá đơn cũng không được chỉ thử
một lần trong hook: lỗi tạm thời cần việc đối soát idempotent theo lịch, giới
hạn bằng dấu dữ liệu v589 để không chạm bản ghi cũ.

## 12/10/2026 - PR #462: đổi giao diện nhưng dùng chung kho nháp phải giữ hai chiều

Trang `/banh` cũ ghi các ô trong `vgb-gio-v1.truong` bằng id DOM như
`f-phone`, còn bản Vue ban đầu chỉ đọc tên trạng thái như `phone`. Giỏ vẫn
về nhưng thông tin liên hệ, giao hàng, hoá đơn và mã ưu đãi biến mất; nếu
Vue ghi kiểu mới thì quay lại trang cũ cũng mất các ô đó. Cách phòng: tầng
đọc nhận cả hai lược đồ, tầng ghi tiếp tục dùng lược đồ cũ trong thời gian
hai trang chạy song song, và ca hành vi phải dựng nháp cũ rồi kiểm đủ mọi ô.

## 12/10/2026 - Ba chữ "tồn bánh" không phải một nguồn (#463)

Sales online đọc `Kiem Banh Ngay` để biết bếp còn nhận được bao nhiêu bánh cho
đơn online. Tab In store đọc hai bảng kiểm kho quầy riêng để biết D1 và NVHTN
đang còn bao nhiêu bánh trong tủ. Trang Vue phải giữ nguyên ranh giới đó:
`napTon` chỉ nạp nguồn Sales online, còn `napQuay` nạp tồn từng quầy. Gộp ba số
vì cùng mã hàng sẽ làm khách thấy sai nơi có bánh. Ca hồi quy phải dùng cùng một
mã với ba số khác nhau và chốt cả tên API lẫn cặp mã-số, không chỉ dò chuỗi.

## 12/10/2026 - PR #462: thông báo giống nhau làm mất trạng thái bàn giao

Tin Telegram của comment chỉ có người viết và link nên một loạt tin trông giống
nhau; anh Việt không biết việc nào đã sửa xong nếu không mở từng link. Nguyên
nhân là sender chỉ phân loại bốn nhãn và cố ý không đọc thân comment, nhưng chưa
có khối tóm tắt an toàn. Cách phòng: comment bàn giao có nhãn trạng thái cùng
khối `telegram-tomtat` giới hạn hai trường ngắn; sender chỉ đọc khối của chủ repo,
còn comment Codex chỉ lấy ý đầu của Summary và tuyệt đối không lấy Testing/log.

## 12/10/2026 - Ảnh fixture phải là bằng chứng tự động của từng PR web

Sau v590, ảnh giao diện ở cloud không đến được PR vì môi trường thiếu Chromium,
nên người duyệt chỉ còn mô tả chữ và lỗi nút dính đáy có thể lọt. Nguyên nhân là
việc chụp phụ thuộc máy của từng phiên thay vì là cổng của PR. Cách phòng: PR
đổi trang đặt bánh hoặc sổ nhãn tự dựng fixture không chứa dữ liệu khách, chụp
đủ hai bề rộng và các trạng thái chính, so pixel với main rồi lưu artifact.
Comment phải nói rõ đây chưa phải site thật; ảnh fixture không thay phép kiểm
site thật sau deploy. Nguồn: yêu cầu v590 của anh Việt ngày 12/10/2026.

## 12/10/2026 - v591: Zalo không gửi tên nhóm, hộp chọn đọc bản cũ

Anh Việt thêm bot vào nhóm thứ hai, @nhắc bot, nhưng hộp "Chọn nhóm đã nhắn
bot" chỉ có một dòng "Viet Nguyen". Nhóm mới thật ra đã vào danh sách, nhưng:
cập nhật của Zalo Bot không có tên nhóm (chỉ có tên người nhắc), nên mọi nhóm
mang tên người nhắc; hộp chọn đọc bản Cài đặt tải lúc mở màn; chọn xong máy
lấy tên người nhắc làm tên nhóm. Ca kiểm cũ dựng dữ liệu có sẵn `title` nên
không thấy lỗi.

Cách phòng: gọi nhóm bằng mã nhóm (4 ký tự cuối mã chat) và cho bot trả lời
mã đó ngay trong nhóm; danh sách chọn hỏi máy chủ mỗi lần bấm; dữ liệu mẫu
trong ca kiểm lấy đúng hình dạng đọc trên site, không tự thêm trường mà nguồn
thật không gửi.
## 12/10/2026 - #445: ẩn nút không chứng minh quyền tải tệp

Ca DOM chỉ chốt Sales không thấy liên kết UNC không bắt được lỗi quyền máy chủ.
Ca bench phải tạo File riêng gắn phiếu thật, đổi sang Sales và gọi chính
frappe.utils.response.download_private_file; kế toán phải nhận 200, Sales
thiếu quyền phải bị từ chối. Danh sách 12 UNC chỉ hiện hai liên kết và mục
mở thêm để không đẩy nút Ghi sổ ra xa. Không thay quyền File của core.

## 12/10/2026 - #392: thiết kế cũ phải đối chiếu với chức năng đã phát hành

#402/#403/#407 đã có lọc/Excel và JE xử lý khoản trả trước ERP từng hóa đơn,
nhưng chưa có snapshot AP/AR/PLE/GL lịch sử. Không suy một đầu đã làm là cả
thiết kế đã xong; ngược lại không dựng công cụ ghi trùng vì tài liệu cũ nói
chưa triển khai. Ghi riêng bằng chứng code, số site và phạm vi còn thiếu.

### #465: mock GET Pancake không được trả tổng đã trừ giảm

Đọc chỉ đọc GET `/shops/{shop_id}/orders/{id}` trên pos.pages.fm ngày
13/10/2026: 91853 trả total_price 8.230.000, total_discount cấp đơn 0,
shipping_fee 0; ba dòng có lượng 2/4/1, discount_each_product 5/5/0,
cờ phần trăm true/true/false và total_discount dòng 220.000/190.000/0.
91391 trả total_price 3.850.000, total_discount cấp đơn 50.000, phí 0,
cả hai dòng không giảm. Tổng thanh toán lần lượt 7.820.000 và 3.800.000.

Mock cũ tự trừ giảm vào total_price rồi bỏ items, khiến công thức sai vẫn
xanh và đơn web đúng bị cảnh báo Sales. Dùng giảm tiền total_discount từng
dòng (đã nhân lượng), trừ thêm giảm cấp đơn, cộng phí khách. Không coi
con số discount_each_product luôn là đồng và không nhân lượng lần hai.
Ca kiểm giữ cả fixture thật, không cảnh báo khi đủ giảm, cảnh báo khi thiếu
giảm. Khôi phục công thức cũ phải làm hỏng 2 ca với 5 khẳng định.

## 12/10/2026 - Commit cloud chưa phải bàn giao GitHub

Các vòng #462/#465 có code và ca kiểm trong cloud nhưng head PR không đổi.
Instruction phải chốt SHA remote, gói task/diff khi thiếu quyền và đường tiếp
nhận desktop. Model trong TOML cũng là yêu cầu cấu hình, phải kiểm metadata
trước khi nhận bot thực sự dùng model đó. Không chữa thiếu quyền bằng PR trùng.

### 13/10/2026, PR #474: khép phần QR chuyển khoản còn phụ thuộc mạng ở #352

- Ảnh QR tại quầy tải từ dịch vụ ngoài mất 7,8 giây dù tài khoản và nội dung đúng. Cùng phụ thuộc đó còn ở Sales, công nợ, màn khách, trang thanh toán web và PDF.
- Dựng VietQR bằng hàm thuần JS/Python, tra BIN từ bảng hiện có trong `tai_khoan.py`. Bộ dựng và thư viện QR có sẵn được ghép trước app để lần vẽ đầu không đợi tải script. Hai trang độc lập nạp cùng asset nội bộ. PDF dùng PyQRCode có sẵn trong Frappe, không tải ảnh ngoài.
- QR Pancake là chuỗi nguyên bản; không lấy các trường ra rồi dựng lại. Phiếu công nợ chỉ mã hoá phần còn thiếu. Thư viện hỏng hoặc thiếu tài khoản phải hiện chuyển tay, không bỏ ô trống.
- Ca TCV 160000/TCVG8FRJ khớp từng byte với PNG tham chiếu giải mã độc lập. DOM mô phỏng chạy chuỗi thêm món, chọn chuyển khoản, tăng số lượng; ba đột biến CRC/số tiền/URL ngoài đều bị bắt.
- Quét bằng công cụ, kiểm DOM và bench PDF không thay thế quét app ngân hàng. Ba ca ngân hàng thật vẫn là cổng riêng trước merge; xem biên nhận PR để biết trạng thái, không suy ra đã deploy từ mục này.

### PR #474, vòng sửa 13/10: kiểm hợp đồng dữ liệu và nhánh QR lỗi

Không chỉ kiểm helper BIN: gọi `tk_cho` cho cả tài khoản riêng và mặc định rồi đưa payload thật vào JS. Màn khách cũ chỉ hiểu ảnh, nên sender chỉ phát khối QR sau khi dựng được ảnh. Tiền rỗng bị từ chối ở cả JS/Python; số 0 tường minh dùng 01=11. Các đường in bill, phiếu công nợ, bảng QR và Sales phải kiểm cả thư viện hỏng, vẫn giữ thông tin chuyển tay. Chín đột biến riêng của vòng này bị bắt 9/9; ca PDF kiểm khung của nhánh lỗi bằng HTML thật.

## 13/10/2026 (#472): ô bị che không phải số 0

Đếm mù trả `ton_he_thong=None`; màn lưu ép số thành 0 và gửi nguyên document
về server, làm mất ảnh chụp. Bộ lọc ghi sổ dựa vào ảnh chụp đó lại loại dòng
đếm 0. Giữ ảnh chụp bằng hook server và chỉ quyết định điều chỉnh bằng tồn
core tại posting_date/time. Không dùng dữ liệu trình bày đã che làm nguồn ghi.
Ca phải đi từ lưu/chốt số 0 tới payload ghi sổ; khôi phục bộ lọc cũ phải đỏ.
Tạo SR, submit và đóng phiếu nguồn cần cùng giao dịch, có khoá nguồn để retry
không sinh phiếu trùng. Chỉ coi core EmptyStockReconciliationItemsError ở insert
là no-op, không gom lỗi submit vào nhánh thành công. Bench xác minh SLE/GL riêng.

### PR #473: xoá ô đếm phải gỡ cờ đã đếm

Ô trống sau gõ số không phải số0: cả input và change phải gỡ da_dem. Ca DOM gọi handler thật gõ5/xoá/gõ0; ca tầng khung gọi ghi_so với hai dòng cạnh nhau, chỉ dòng đếm0 được đưa vào Stock Reconciliation. Không chỉ có fixture một dòng. Ba đột biến (hai handler và bộ lọc server) bị bắt3/3.

# 13/10/2026 - Lịch sử BOM phải lọc bảng khai triển và bù đường ghi thẳng

- Triệu chứng: Version của BOM có nhiều dòng `exploded_items`, còn các lần đổi cờ bằng `db.set_value` không tạo Version nên người xem không biết ai chốt bản nào.
- Nguyên nhân: ERPNext dựng lại bảng khai triển khi lưu, trong khi cập nhật thẳng cơ sở dữ liệu không đi qua cơ chế theo dõi thay đổi của Document.
- Cách phòng: dịch Version theo danh sách trường nghiệp vụ được phép hiện, bỏ toàn bộ `exploded_items`; đường ghi sổ bằng `db.set_value` phải thêm Comment trên cả bản mới và bản cũ. Ca hồi quy dùng Version có đồng thời nhiễu bảng khai triển và thay đổi số lượng.
- Nguồn: PR #469.

- Bổ sung kiểm core: `row_changed` dùng index trước child.name. Chỉ đổi qty thì diff không chứa tên/UOM; phải đọc metadata dòng, không dùng fixture tự thêm tên để che lỗi. Slug màn mới phải khai tại `duong_app.py` để lần dựng không xoá mất.

### #470: kiểm kê Vue phải tách code, kiểm kho và kiểm trang

`web_vue_banh.mjs` chạy kho Vue thật nhưng không mount DOM; môi trường
`suKien` là no-op. 25 ca xanh không chứng minh các nút, Pixel, Editor
xem trước Vue hay metadata cho crawler. Bảng đối chiếu phải ghi nguồn hàm,
ca kiểm hiện có và phần chưa chứng minh. Biên nhận chuyển sang trang cũ
không có nghĩa đã có biên nhận Vue. Nguồn: docs/web-vue/470-doi-chieu-tinh-nang.md.


### 13/10/2026 - #471: lời hứa gửi đơn và phản hồi địa chỉ

- Nhấp kép có thể lọt trong lúc kiểm ưu đãi trước POST: khóa cả lời hứa gửi,
  trả cùng kết quả cho hai lượt, giữ nonce khi mất phản hồi.
- Gợi ý/tọa độ cũ trả muộn có thể ghi đè địa chỉ vừa sửa: đánh số lượt địa chỉ,
  bỏ kết quả cũ ở cả thành công và lỗi; không chỉ chống muộn ở phép tính phí.
- Tải tồn lỗi lần đầu cần câu báo lỗi và nút thử lại, không để màn trống.
- Ca kho Vue và Chromium fixture kiểm hai tầng khác nhau. Không nhận nonce
  Map giả hoặc lời gọi AST là bằng chứng cạnh tranh DB hay tồn production.
- Nguồn PR #471; thay từng hàng rào trong bản sao làm đỏ đúng1ca/lượt.


### 13/10/2026 - F21 nguồn tồn khi gửi đơn

Danh mục công khai bỏ dòng0 nên không dùng việc vắng món để suy ra hết. Đọc
KB đúng ngày hoặc dòng Dư decor gốc cho cửa sổ ba ngày, giữ nguyên đặt xa.
Tìm nonce đã nhận trước mọi kiểm tồn có thể thay đổi. Lỗi đọc chỉ cảnh báo,
không biến thành hết hàng. Báo đúng webhook_don_web của Sales, không suy kênh
Zalo chung là Sales. DOM phải kiểm cả trang cũ và Vue giữ giỏ/tải lại tồn.
Đột biến phải đối chiếu nền xanh và mã thực sự đổi; chuỗi thay không khớp
không phải một lần kiểm đột biến. Ca Document thật nằm ở cổng bench, không
gọi fixture trên production.

### F21 review 13/10: decor0 là dòng giữ chỗ

Chỉ decor gốc lớn hơn0 mới là nguồn tồn hữu hạn cho ba ngày tới. Decor gốc dương bị đơn dùng hết vẫn phải trả tồn0 để chặn. Ca đi qua cửa tạo đơn cho cả ba ngày; đồng hồ giả chỉ thay thời điểm, giữ hàm hom_nay thật để bắt lệch ngày UTC/Sài Gòn. Ngày nhận trống trả về trước khi đọc nguồn, không tạo cảnh báo Sales giả.

### v594: gom nhánh và sửa bốn điểm BOM sau review

Chip Tất cả gửi null phải giữ nguyên tới nguồn danh sách và dòng bộ lọc Excel;
không dùng giá trị mặc định của màn để thay bộ lọc người vừa chọn. Ca quyền phải
gọi cửa API thật, không chỉ helper. Nhật ký lấy ngày Sài Gòn kể cả máy ở múi giờ
khác. Comment lưu HTML an toàn, khi trả câu thuần thì bỏ thẻ rồi giải mã entity
một lần, để màn escape khi vẽ. Chỉ ghi trường nghiệp vụ bằng nhãn tiếng Việt,
bỏ giá vốn tính lại. Tám đột biến của các nhánh này đều bị bắt trong bản gom.
Nguồn: comment giao gom v594 trên PR #474; không kéo phần Vue của #471 vào.


### #476: bộ sao kê phải giữ phần tiền ở cả cửa mới lẫn cửa một dòng cũ

Khi một hồ sơ dùng nhiều dòng sao kê, trường mã giao dịch cũ chỉ còn giữ dòng đầu để tương thích. Chỉ kiểm trường đó sẽ bỏ sót dòng thứ hai ở các cửa webhook và khớp tay cũ. Phải đọc bộ đang giữ trong cùng giao dịch khóa, kiểm phần tiền còn lại tại máy chủ, và bảo vệ cả lúc core lưu Bank Transaction. Không lấy tổng trên màn hình làm quyền ghi tiền.

Đổi bộ cũng không được ghi trường giữ mới trước khi controller gỡ bộ cũ: controller có thể xóa nhầm phần vừa chọn. Gỡ và kiểm bộ cũ trước, chọn mới trong cùng transaction; chọn mới hỏng thì rollback giữ nguyên dữ liệu trước lượt. Ca bench phải kiểm tình huống đổi bộ này riêng với ca gán lần đầu. PR #476 bổ sung ca tầng khung và DOM; bằng chứng bench cập nhật theo SHA trên PR.

### PR476: bộ sao kê và cửa webhook

- Khi đổi chọn một dòng thành chọn bộ, bài kiểm trình duyệt phải bấm Gán trước xác nhận; giữ cả bước đọc lại chứng từ sau ghi. Timeout ở hộp xác nhận chưa đủ để kết luận lỗi backend.
- Callback webhook hợp lệ có thể vẫn chạy dưới Guest. Dùng cửa nội bộ kiểm nguồn và số tiền cho tác vụ đã xác thực, còn API chọn tay phải kiểm quyền. Không đổi người dùng toàn request để vượt lỗi quyền.
- Tự dò bắt lỗi rồi đi phiếu kế tiếp thì phần ghi trước lỗi phải có savepoint; nếu không sẽ giữ tiền mồ côi khi phiếu sau commit.
- Sau đột biến Python sửa và phục hồi nhanh, dùng thư mục pycache mới để tránh timestamp cache khiến bản đúng chạy bytecode của bản hỏng.

### PR476: khóa chủ sao kê và giữ tồn web phải có phạm vi chỉ mục

Triệu chứng: đối chiếu BT không liên quan và tạo APP mới đều chờ khoảng2giây
trong probe giữ2giây; đảo thứ tự có deadlock1213. Nguyên nhân: tìm chủ bằng
LIKE FOR UPDATE trên bảng phiếu khóa cả các hàng không liên quan. Khắc phục:
chủ giữ nằm trên BT hiện có, tra khóa chính; mọi cửa ghi khóa BT theo tên
trước phiếu, kể cả khóa ngầm check_if_latest của Frappe. Probe sau sửa tại
1c59da60f còn0,03-0,06giây, không deadlock. Bench tổng vẫn phải kiểm riêng.

Giữ tồn web cũng có truy vấn OR/JSON/LIKE FOR UPDATE làm hook cập nhật đơn
khác chờ2,066giây. Tách ngày nguồn có chỉ mục và ID Pancake có chỉ mục thành
hai truy vấn. Không xem unit kiểm câu SQL là bằng chứng hết chờ: phải đo lại
hai kết nối và chạy ca tranh chiếc bánh cuối trên bench đúng SHA.

Hồ sơ hoàn tiền có thể có PE Receive và PE Pay độc lập. Cửa bỏ bộ tiền ra
chỉ kiểm PE Pay còn sống, không chặn vì PE Receive nháp. Hủy PE chi không tự
đổi trạng thái hồ sơ từ Da chi; kiểm chứng từ/liên kết lõi thật trước nhả bộ.
Nguồn: review PR476 và bench38549666430/38617438497.

### PR476: đọc lại sau khóa phải là current read

Một SELECT thường sau SELECT FOR UPDATE vẫn có thể đọc snapshot cũ ở
REPEATABLE READ. Đường lập phiếu thu phải lấy cả trạng thái/dư nợ ngay trong
locking read, và đọc phần nháp vừa commit dưới khóa hóa đơn. Các cửa save
PE cùng thứ tự BT/chủ bộ, SI theo tên, rồi PE để tránh đảo khóa với factory.
Ba ca tầng khung bắt3/3đột biến; bằng chứng hai tiến trình theo run PR476,
không dùng bộ giả để khẳng định thời gian chờ thực tế.

### v595: nhịp đồng bộ Pancake đè người mua "Không có MST Việt Nam"

Triệu chứng: Loan Anh lưu đơn #95605 (HDB-26-10-02615) với tên COCO
INVESTMENTS PTE. LTD, địa chỉ Singapore, email, không mã số thuế. Hoá đơn
19621 vẫn ra "Bán cho người tiêu dùng". Version trên site: 22:32 nhịp đồng bộ
đổi tên thành câu mặc định; 23:00 tên đã mặc định nên nhịp sau xoá địa chỉ và
email; 23:07 xuất hoá đơn.

Nguyên nhân: `_upsert_hoa_don` đọc lại người mua "chừng nào còn thiếu mã số
thuế" (bài học 91476). Người mua không MST thì thiếu mãi, và `_thong_tin_xhd`
không ra gì thì trả câu mặc định, một chuỗi KHÔNG rỗng nên lọt qua lớp "đọc
lại rỗng thì giữ nguyên". Bản sửa #456 (v588) chỉ chốt màn Sales và tờ gửi
m-invoice, kết luận "máy chủ đã đúng" mà không chạy nhịp đồng bộ trên một tờ
có tên không MST. Từ 01/08 có 35 lần đè; ba tờ đã xuất cho người tiêu dùng.

Khắc phục: gom luật vào hàm thuần `gop_nguoi_mua_dong_bo`. Tên thật đã có thì
máy không đụng tên, MST, địa chỉ, chỉ bù email trống; chỉ khi tên trống hoặc
mặc định mới ghi kết quả đọc lại. Ca kiểm chạy đúng `_upsert_hoa_don` thật hai
nhịp liền.

Bài học: sửa một lỗi người mua phải chạy MỌI đường ghi vào bốn ô `vgb_xhd_*`
(màn Sales, bill quầy, nhịp đồng bộ, cuối ngày), không chỉ đường người dùng
nhìn thấy. Lưu tay dùng `ignore_version` nên Version không có dòng của sales;
thấy Administrator đổi ô người mua lúc :00 hoặc :30 là nhịp đồng bộ.

### v596: màn Cài đặt lõi vỡ thành ô to vì dòng flex mang lớp .card

Triệu chứng: anh Việt chụp màn Cài đặt lõi ngày 15/10, mỗi nhóm là một ô to,
biểu tượng nằm trên, chữ căn giữa, 8 nhóm phải cuộn hai màn. Nguyên nhân: dòng
nhóm khai `class="card cdl-tab"` với `.cdl-tab{display:flex}`, nhưng 00-nen.js
ép `.card{display:block}` để chống Bootstrap của Frappe, và luật đó thắng tuỳ thứ
tự nạp CSS. Ca DOM không tính CSS nên không bắt được. Khắc phục: dòng và khối
của màn dùng lớp riêng (`cdl-nhom`, `cdl-khoi`), không dùng `.card` cho phần tử
cần flex; ca kiểm chốt "dòng nhóm không mang lớp card". Bài học: thấy một màn
dùng `.card` làm hàng ngang thì kiểm ngay bằng ảnh chụp, đừng tin ca DOM.

### v600 (Codex #486): màn lập phiếu mới lọt khỏi lưới bản nháp vì tên không theo mẫu scr*

Triệu chứng: màn Phiếu tính giá thử (`gvtManPhieu`) là màn lập phiếu, mà bản
đầu không khai bản nháp tự lưu; sập nguồn là mất hết nguyên liệu đã gõ. Ca
`_khong_sot` của v533 chỉ dò hàm tên `scr*Tao/New/Sua...`, nên màn đặt tên khác
lọt qua mà cổng vẫn xanh. Cùng PR, nút Xoá phiếu gọi `delete_doc` trên dữ liệu
nghiệp vụ, trái QT-20. Khắc phục: khai `gia_thu` trong 48, thêm `gvtManPhieu`
vào `MAN_LAP_PHIEU`, ca hành vi gõ, sập nguồn, mở lại từ thẻ; bỏ phiếu thành
bỏ mềm. Bài học: thêm màn có nút Lưu tạo chứng từ thì TỰ thêm vào 48 và
`MAN_LAP_PHIEU`, đừng chờ ca dò tên bắt hộ; thêm nút xoá thì hỏi trước "QT-20
cho xoá cứng không", gần như luôn là không.

### v602 (sự cố 17/10, Codex #488): một lượt làm cả lô dưới một khoá, và "đã xếp" không phải "đã xong"

Triệu chứng: đêm 17/10/2026 chuỗi 23h ghi sổ xong 4 đơn lúc 23:03 rồi đứng
tới khi hàng đợi cắt ở 3600 giây, giữ khoá đơn Sales suốt thời gian đó; 62 đơn
Sales và 28 bill quầy đủ điều kiện nằm nháp sang hôm sau. Đây là lần thứ năm
chuỗi này hỏng cùng một gốc: MỘT lượt chạy làm lần lượt mọi đơn, một đơn kẹt là
cả lô kẹt. Khắc phục: mỗi đơn một lượt hàng đợi riêng (trần 180 giây, chờ khoá
dòng 20 giây, mã lượt cố định chống trùng), báo động Zalo 23:20 nếu còn đơn.
Bẫy thứ hai, Codex bắt ở vòng 1: xếp lượt nền xong rồi đi thẳng sang phát hành
và ghi nhật ký "ghi sổ N đơn" theo số đã XẾP. Nay một lượt chờ đợi các lượt
riêng xong (có trần, dừng trước 23:45), đọc lại docstatus thật rồi mới phát
hành. Lượt dài đọc lặp trên MariaDB phải commit trước mỗi lần đọc, không thì
REPEATABLE READ trả mãi ảnh chụp cũ. Bài học: chuyển việc sang lượt nền thì
mọi bước SAU nó phải đợi hoặc đếm lại từ cơ sở dữ liệu, không dùng số đã xếp.

### v604 (anh Việt 18/10/2026): chuyển tin sang "nhóm tích đúng tin" thì mọi nơi phát phải mang mã

Bỏ thư cảnh báo nội bộ, mỗi nhóm Zalo tích đúng tin cần nhận (`kenh_zalo.TIN`).
Bẫy: nhóm đã tích Tin nhận chỉ nhận tin có mã khớp, nên một lời gọi `bao()` quên
`ma_tin` là tin đó lặng lẽ không tới nhóm nào, `bao()` vẫn trả rỗng như khi chưa
gán nhóm. Rà bằng grep lúc làm còn lộ hai tin Zalo có sẵn mà danh sách duyệt chưa
ghi (lệch tổng Pancake, phí giao Ahamove). Phòng: ca `thu_tin_zalo_604` dò AST mọi
lời gọi `bao`/`bao_hoac_ghi_loi`, đòi có `ma_tin` trong danh mục và mỗi tin có
nơi phát. Bẫy thứ hai: nhịp lặp gọi lại cùng khoá thì `bao()` trả rỗng vì tin đã
nằm trong sổ; `bao_hoac_ghi_loi` nay chỉ ghi Error Log khi thật sự không có nhóm.

### v607 (anh Việt 20/10/2026, đơn #95631): hai nút lưu trên một màn, một nút lưu thiếu

Triệu chứng: cửa hàng chọn Hàng tặng, gõ lý do, bấm "Lưu phương thức thanh
toán". Nút đó chỉ lưu phương thức; ô lý do nằm trong khối Hàng tặng có nút
lưu riêng, nên lý do mất trắng mà không ai được báo. Giám đốc mở màn duyệt bấm
Duyệt mới thấy "Không duyệt được". Màn Doanh thu Sales còn không có ô lý do nào.
Khắc phục: chọn Hàng tặng thì chỉ còn MỘT nút (`hang_tang.luu_tang`) lưu phương
thức, loại, lý do chọn sẵn và ảnh cùng một lần, thiếu là không lưu gì; bốn cửa
cũ (`pos_chot`, `pos_luu_don`, `pos_sua_don`, `luu_thanh_toan`) gặp Hàng tặng
thiếu lý do thì dừng và chỉ đúng nút cần bấm. Không chặn ở hook validate vì
nhịp đồng bộ Pancake lưu lại đơn. Bài học: một màn có hai nút cùng lưu một tờ
thì mỗi nút phải lưu ĐỦ mọi ô bắt buộc mà nó có thể làm đổi, hoặc nút kia phải
ẩn; và hàng rào phải đặt ở mọi cửa máy chủ, không chỉ ở nút trên màn.

### v607 (Codex #493 vòng 3): nới ca kiểm thứ tự mà quên khai bản nháp

Triệu chứng: thêm phần 55 có màn lập phiếu Nạp tiền trả trước, đứng sau 48.
Ca `thu_ban_soan_do_533._thu_tu` đỏ, và cách sửa lúc đó là thêm 54, 55 vào
danh sách phần được đứng sau 48. Ca xanh, nhưng màn nạp không có bản nháp tự
lưu: tải lại trang là mất khách, số tiền, nguồn đã chọn. Ca `_khong_sot` cũng
không bắt vì tên `scrSoDuNap` không khớp mẫu Tao/New/Lap/Nhap. Khắc phục: khai
`sdKhai` + `sdBoc` trong 48, duyệt tên qua `SAU_48_DUOC_BOC`, thêm ca hành vi
sập nguồn rồi mở lại. Bài học: ca kiểm đỏ vì phần mới thì đọc lý do nó canh
gì trước khi nới; phần mới có màn lập phiếu là phải có bản nháp, không phải
chỉ được phép đứng chỗ đó.

### v607 (Codex #493 vòng 6): khối lưu riêng xong mà chế độ sửa còn nhớ lựa chọn cũ

Triệu chứng: Bill quầy đang Sửa hoá đơn, bấm chip Số dư trả trước rồi áp số dư
một phần trong khối riêng. Máy chủ đã tách đơn, nhưng `posSua` vẫn giữ phương
thức và dấu "vừa bấm chip" của lần trước; bấm Lưu thay đổi là gửi lại lựa chọn
cũ và máy chủ bỏ bảng tách vừa áp. Cùng vòng: Doanh thu Sales chọn Số dư trả
trước rồi Lưu thì cửa lưu ghi thẳng bằng `set_value`, bỏ qua hook kiểm khách
và số dư. Khắc phục: khối riêng lưu xong gọi một hàm chung xoá lựa chọn tạm của
chế độ sửa để màn đọc lại từ đơn; chọn Số dư trả trước luôn đi đường Document.
Bài học: trạng thái tạm của một chế độ (sửa, nháp) phải được xoá ở MỌI lối lưu
làm đổi đúng ô đó trên máy chủ, kể cả lối lưu của khối con; và ô có hook kiểm
thì không được ghi bằng `set_value`.

### v607 (Codex #493 vòng 7): bảng tách dựng theo tổng lúc áp, tổng đổi sau đó

Triệu chứng: Bill quầy đang Sửa hoá đơn, thêm món chưa lưu rồi áp số dư một
phần. `ap_dung` tách theo tổng cũ trên máy chủ; Lưu thay đổi tính lại tổng
mới nhưng hai dòng vẫn cộng ra tổng cũ, tới lúc ghi sổ bị chặn lệch tổng. Cùng
lỗi xảy ra khi đơn đã áp số dư rồi sửa món ở bất kỳ lần nào sau đó. Khắc phục:
hook validate chỉnh lại bảng tách do `ap_dung` dựng: giữ phần trừ số dư, phần
còn lại theo tổng mới. Vòng 8 (Codex): bản đầu nhận bảng theo HÌNH DẠNG (hai
dòng, một dòng số dư) nên bảng kế toán nhập tay cùng hình dạng cũng bị viết lại,
ghi sổ thu tiền mặt chưa hề thu. Sửa: `ap_dung` ghi dấu bền `vgb_ky_tach_so_du`,
hook chỉ chỉnh khi bảng còn đúng dấu, nhập tay thì xoá dấu. Bài học: bảng dòng
tiền máy tự dựng từ tổng đơn phải được dựng lại mỗi khi tổng đơn đổi; và việc
máy tự sửa số tiền phải dựa trên dấu nguồn gốc bền, không bao giờ suy từ hình
dạng dữ liệu, vì người nhập tay có thể tạo ra đúng hình dạng đó.

### v607 (anh Việt 21/10/2026): cấu hình hiện trên màn mà không có dòng code nào áp

Triệu chứng: hạng AMBASSADOR 10%, FAMILY 20%, OWNER 100% khai từ 16/08 ở Cài
đặt hạng khách, màn ghi "Áp cho mọi hoá đơn của khách hạng này", màn tính tiền
còn hiện chip "giảm 10%", nhưng không chỗ nào tính số tiền đó vào hoá đơn. Thêm
hai lỗ: `tao_don_tay` chỉ truyền khách công nợ cho phần khuyến mãi nên khách
chọn qua số điện thoại không bao giờ được xét theo hạng; và gõ số vào ô Số điện
thoại mà không chọn trong danh sách thì hoá đơn không biết khách là ai. Khắc
phục: ưu đãi hạng tính trong `khuyen_mai.tinh` (một công thức cho xem trước và
chốt), truyền khách vừa chọn, ô Số điện thoại tự gắn khi khớp đúng một hồ sơ.
Bài học: mỗi ô cấu hình có chữ "áp cho..." phải có ca kiểm chạy thật chứng minh
nó áp; hiện con số lên màn không phải là đã áp.

### v608 (anh Việt 21/10/2026): ô cài đặt điền tay làm hỏng địa chỉ API, web mất phí giao hai tuần

Triệu chứng: từ 06/10 web báo "ahamove_loi", không có phí giao; khách đặt đơn
từ 1.000.000 thấy "Miễn phí giao" (đúng cài đặt), nhưng đơn sang Pancake chỉ
có phí giao 0 và không chữ nào nói là miễn phí, sales tưởng chưa tính nên thu
thêm, khách phản ứng. Gốc: ô Địa chỉ API Ahamove được điền
"https://partner-api.ahamove.com/v3", mã ở bốn chỗ tự nối "/v3/..." thành
".../v3/v3/accounts/token", Ahamove trả 404; Error Log có ghi nhưng không ai
đọc. Khắc phục: một hàm lib.aha_url chịu mọi kiểu điền (có hay không "/",
có hay không đuôi "/v3"), bốn chỗ gọi đều đi qua nó, ca kiểm AST chốt không
còn chỗ nào tự ghép; đơn miễn phí giao gửi Pancake cờ is_free_shipping và
dòng ghi chú in đậm cho sales. Bài học: ô cài đặt người điền tay là đầu vào
không tin được, mã phải chịu được mọi cách điền hợp lý; và một trạng thái
"miễn phí" máy đã quyết phải hiện thành CHỮ ở màn người thu tiền, con số 0
đứng một mình ai cũng đọc thành "chưa tính".

### v607 (Dễ 21/10/2026): câu báo lỗi chỉ đường tới màn không có nút đó

Triệu chứng: nhân viên mở "Hàng chuyển về kho tôi" thì máy báo "chưa khai Kho
phụ trách... Báo anh Việt khai giúp ở màn Quản lý người dùng". Quản lý cửa hàng
có quyền Quản lý người dùng vào đúng màn đó tìm mãi không thấy chỗ khai, vì ô
Kho phụ trách chỉ có trên Desk (form User), màn app chưa từng hiện hay sửa nó.
Hệ quả: việc một quản lý tự làm được trong một phút phải chờ anh Việt. Khắc
phục: màn Quản lý người dùng hiện dòng Kho phụ trách và nút Đổi kho phụ trách
(chọn nhiều kho, tên ngắn, có dòng giải thích), câu báo ở hai chỗ chặn nói đúng
nút cần bấm và ai bấm được. Bài học: câu báo "sửa ở màn X" phải được kiểm bằng
cách mở màn X đúng vai của người đọc câu đó và bấm được tới ô; viết ca kiểm
chốt câu báo nhắc đúng tên nút đang có trên màn, để sau này đổi tên nút thì ca
đỏ.

### v609 (anh Việt 22/10/2026): tắt webhook email rồi mà thư giao việc vẫn tới, vì thư đó của Frappe lõi

Triệu chứng: anh Việt đã bỏ email khỏi phần webhook và tắt thư cảnh báo nội bộ
(v604), nhưng hộp mail vẫn nhận hàng chục thư "đã phân công nhiệm vụ mới" trong
vài phút. Nguyên nhân: hàm giao việc của app gọi
frappe.desk.form.assign_to.add(), mà bản Frappe v16 của hàm đó không có tham số
tắt báo và luôn gọi notify_assignment, tức ghi Notification Log rồi gửi email
theo cấu hình người nhận. Thư này không đi qua webhook hay bất kỳ cài đặt nào
của app, nên tắt mọi thứ trong app cũng không hết. Khắc phục: ghi ToDo thẳng
(một dòng mỗi người, đủ ô tham chiếu, ưu tiên, hạn, người giao), chia sẻ quyền
đọc chứng từ khi người nhận chưa đọc được; ca kiểm AST chốt tệp không còn import
hay gọi assign_to. Bài học: trước khi gọi một hàm tiện của Frappe thay cho ghi
bản ghi, đọc hàm đó xem nó còn gửi gì ra ngoài (email, thông báo, webhook); mọi
đường gửi ra ngoài của app phải đi qua đúng một chỗ (kenh_zalo), không để thư
nào sinh ra từ lớp lõi mà cài đặt của app không tắt được.

### v609 (anh Việt 22/10/2026): tin báo về hàng hoá phải có tên hàng, và tiền chỉ cho đúng bộ phận

Bối cảnh: thêm 21 tin Zalo cho kho, thu mua, sản xuất, đơn web. Anh Việt duyệt
mẫu với hai luật: tin về hàng hoá phải kê TÊN HÀNG, số lượng, đơn vị (tối đa 5
món rồi "+N món khác"), và số tiền chỉ xuất hiện ở tin của Thu mua và Kế toán,
không ở tin cho Kho, Bếp, Bán hàng. Cách giữ luật: mỗi tin một hàm phát duy
nhất (ca thu_tin_zalo_604 chốt NOI_PHAT), hai tin cùng một chứng từ (xuất huỷ
cho kho và giá vốn cho kế toán) tách hai hàm, hàm hook chỉ điều phối; ca kiểm
chạy hàm thật và soi từng dòng tin kho không có mẫu "số đ". Bẫy đã gặp khi viết
ca: dò chữ " đ" bắt nhầm " đơn", phải dò bằng mẫu "chữ số, khoảng trắng, đ, hết
từ". Bài học: luật trình bày tin cho người dùng phải có ca kiểm máy đọc được,
không để người viết tin sau nhớ bằng miệng.

### v609 (22/10/2026): đột biến "không bắt" vì Python chạy tệp .pyc cũ

Triệu chứng: đột biến đổi khoá sắp xếp "han" thành "ghi" (cùng độ dài) rồi chạy
ca kiểm trong cùng giây với lần khôi phục trước, máy báo KHÔNG BẮT; chạy tay
lại thì bắt ngay. Nguyên nhân: Python quyết định dùng .pyc theo mốc thời gian
giây và kích thước tệp nguồn; thay chuỗi cùng độ dài trong cùng giây thì cả hai
không đổi, nên nó nạp bản biên dịch của mã CHƯA đột biến. Đây là trường hợp
thứ tư của điều 17 (ngoài bộ kiểm yếu, mẫu không khớp, lớp bảo vệ dư): mã
chạy không phải mã trên đĩa. Cách phòng: kịch bản đột biến xoá __pycache__
trước mỗi lần chạy, hoặc chạy python3 -B; và một đột biến "không bắt" phải
được chạy tay lại một lần trước khi ghi vào báo cáo.

### v610 (anh Việt 24/10/2026): "SePay không ghi nhận" thường là màn hình không soi tới

Triệu chứng: Dễ báo bill TCVEHQHG chuyển khoản 1.875.000 đ "SePay không ghi
nhận nên không ghi sổ tự động được". Đọc bảng sao kê trên site: SePay CÓ ghi,
dòng ACC-BTN-2026-08831 lúc 13:27, trước cả lúc lập bill. Khách xin số tài
khoản công ty rồi chuyển thẳng vào MB 31561568, nội dung không mang dấu tài
khoản ảo nào. Nút Dò tiền lọc sao kê theo dấu tài khoản ảo của điểm, nên khoản
đó không bao giờ hiện ra để chọn, và người dùng kết luận là ngân hàng không về.

Sửa: chip tài khoản (của điểm / vào thẳng tài khoản chính / tất cả) và chip
ngày trong bảng Dò tiền, màn Đối soát chuyển khoản cho quản lý và kế toán. Khoản
ngoài tài khoản điểm chỉ quản lý cửa hàng và kế toán gắn được, và phải hỏi chủ
TOÀN HỆ (công nợ, hoàn tiền, bộ sao kê, hoá đơn đã ghi sổ, Đối chiếu ngân hàng)
vì tài khoản chính còn nhận tiền khách sỉ trả nợ.

Bài học: một bộ lọc ở cửa NHÌN biến dữ liệu thật thành "không có" trong mắt
người dùng. Khi nghe "hệ thống không ghi nhận", đọc bảng gốc trên site trước
rồi mới sửa. Lọc sẵn theo phạm vi hẹp thì luôn phải có chip mở rộng ra, như
điều đã chốt ngày 14/09/2026 cho mọi màn khớp giao dịch thủ công.

Vòng 2 (Codex #497): khi gộp "ai đang giữ dòng này" từ nhiều nguồn, phải loại
chính chứng từ đang xem NGAY ở nguồn của nó rồi mới gộp. Gộp trước rồi xoá mục
của chính mình thì `setdefault` đã bỏ qua chủ thật ở nguồn sau, và dòng vừa
thuộc bill này vừa thuộc phiếu công nợ ra "không ai giữ". Và một ô bị ghi đè
(mã tham chiếu đổi thành số ngân hàng sau khi gắn) không còn là danh tính của
chứng từ: so danh tính bằng mọi mã chứng từ từng mang.

Vòng 3 (Codex #497 4367048767): phiếu công nợ ghi CỘNG DỒN nhiều mã giao dịch
vào một ô văn bản, nên lọc `in` nguyên ô bỏ sót dòng nằm giữa danh sách. Trước
v610 chỉ cửa bộ sao kê mới tách ô, các cửa khác (Dò tiền, ghi sổ bill quầy)
mù với phiếu công nợ cũ nhiều mã. Phiếu cũ còn có thể lưu SỐ THAM CHIẾU ngân
hàng thay vì tên dòng. Hỏi chủ phải dùng cả hai khoá rồi quy về tên dòng, và
cách đọc ô nhiều mã phải nằm trong một hàm chung cho mọi cửa, không theo cờ.

## 25/10/2026 (v611): lỗi chỉ nằm trong Error Log là lỗi không ai biết

Bill Pancake 95914 (HDB-26-10-04205) nằm nháp ba ngày. Máy tự ghi sổ mỗi lượt,
m-invoice mỗi lượt từ chối vì email nhận hoá đơn "_quynhntm@ocb.com.vn" có dấu
gạch dưới ở đầu, và máy chỉ ghi Error Log. Sales không đọc Error Log, nên đơn
treo cho tới khi kế toán đi tìm. Cùng ngày, Tài nhận YCDC-2026-00059 thì ERPNext
ném câu dịch máy "Tỷ giá định giá cho Mặt hàng ... là bắt buộc", thật ra là Kho
tổng 307 chưa từng có món BTP đó.

Sửa: chặn email sai ngay lúc nhập (cả hai cửa: Sales sửa bill, khách tự điền);
m-invoice chê thông tin người mua thì báo Zalo nhóm Bán hàng; nhận hàng mà kho
xuất thiếu thì lùi về điểm lưu, báo Zalo Kho, rồi nói câu dễ hiểu.

Bài học: (1) Lỗi nào cần NGƯỜI sửa dữ liệu thì phải tới đúng người đó, Error Log
chỉ là nơi lưu cho kỹ thuật. (2) Chặn dữ liệu sai ở cửa NHẬP, đừng để cửa GHI SỔ
phát hiện muộn. (3) Câu lỗi thô của ERPNext (bản dịch máy) phải được dịch lại
thành việc cần làm ở chỗ người dùng bấm.

Ca kiểm (thu_dat_ban_zalo_611, dat_ban_611.js): đột biến lần chạy đầu bắt
16/18. Hai cái lọt đều vì có lớp đỡ thứ hai (điều 17c): tìm SĐT không có nhánh
số thì phép tìm chung vẫn ra, vì dữ liệu mẫu không có ca hai cụm số đủ mà không
liền nhau; bản vá không xét kênh thì danh sách tên vẫn đỡ. Thêm đúng ca đó thì
bắt đủ 18/18. Khi viết dữ liệu mẫu cho phép tìm số, kiểm cả ca trùng tình cờ:
"0912 345" là dãy con của "0909 123 456".

Vòng 2 (Codex #498 4371298484): bench CI chạy ERPNext thật bắt được điều
mock không thấy. Kho có 30, nhận 50, câu báo ra "kho đang có 0": Bin đọc ngay
sau `submit()` hỏng là Bin của giao dịch dở, ERPNext đã trừ tồn trước khi ném
lỗi. Bắt lỗi ghi sổ xong muốn đọc lại sổ thì phải LÙI ĐIỂM LƯU TRƯỚC rồi mới
đọc. Và khi thay câu lỗi lõi bằng câu dễ hiểu, giữ nguyên lớp lỗi gốc
(NegativeStockError...) vì màn hình và ca kiểm có thể đang bắt theo lớp đó.

Vòng 3 (Codex #498, bench CI 58b0ccb): ca kiểm ERPNext thật dựng đúng ca Tài
cho thấy câu "Valuation Rate ... is required" ném ngay ở `insert()` (lúc
validate tính giá xuất), chưa tới `submit()`. Bắt lỗi chỉ quanh submit là bỏ
sót đúng ca gốc. Và chỉ thay câu LÕI ERPNext: câu đã dễ hiểu của app (lo_hang
"còn thiếu ...") phải đi nguyên, không thì mất thông tin người dùng cần.

## 27/10/2026 (v614): đếm trên bảng nối một-nhiều, và hàm có commit theo lô

Màn Hiệu quả chiến dịch đếm "Sales đã gọi xong bao nhiêu khách" bằng
`sum(k.trang_thai = 'Đã xong')` trong câu đã `left join` hoá đơn của khách.
Khách có ba hoá đơn trong 14 ngày đo thì bị đếm ba lần. Lớp Frappe giả không
chạy SQL nên không ca tầng khung nào thấy. Sửa: `count(distinct case when ...
then k.khach end)`.

Bài học: (1) Câu nào đã nối bảng con một-nhiều (hoá đơn, dòng hàng) thì mọi
`sum(...)`, `count(*)` trên bảng cha phải đổi thành `count(distinct ...)`, đọc
lại từng cột trước khi giao. (2) Hàm chạy đêm ghi theo lô có `commit` sau mỗi
lô thì bench CI (chạy trong điểm lưu, khoá commit) không gọi được: thêm tham số
`luu=False` cho ca kiểm, và ca tầng khung phải chốt cả hai nhánh (có commit,
không commit). (3) Lượt đêm ghi đè cả bảng bằng `ON DUPLICATE KEY UPDATE` thì
liệt kê cột được cập nhật TƯỜNG MINH, loại các cột do người nhập (đồng ý nhận
tin, Danh sách không quảng cáo), và có ca chạy hai lượt liền để chứng minh lời
khách đã nói không bị xoá.

Vòng Codex #505: (4) Danh sách chốt cố định để ĐO, nhưng quyền LIÊN HỆ phải đọc
đồng ý hiện tại: khách rút đồng ý sau lúc chốt mà nút Gọi vẫn hiện là quảng cáo
trái ý khách. (5) Mốc đo bắt đầu từ GIỜ chốt, không phải đầu ngày: so cả
`posting_time` của hoá đơn. (6) Luật "sửa kịch bản là mất duyệt" đặt trong hàm
app thì Desk đi vòng được; đặt ở `validate` của doctype để mọi đường lưu đều qua.

Vòng 2 (rà 9ffd042): (7) Máy chủ đổi quyền của một khách thì danh sách đang giữ
trên máy cũng phải đổi theo, ở MỌI dòng của khách đó, kể cả dòng thuộc chiến dịch
khác: ghi "không nhận tin nữa" xong mà sang chip khác nút Gọi hiện lại là sửa nửa
vời. (8) Nút hành động chỉ gửi mã (Duyệt, Chốt) thì máy chủ làm trên bản ĐÃ LƯU;
màn đang có chữ sửa dở phải bắt Lưu trước, kiểm lại ngay lúc bấm vì gõ chữ không
vẽ lại nút. (9) Sổ làm bằng chứng mà chỉ trả N dòng mới nhất thì phải có ô tìm
hỏi máy chủ và nút Xem thêm; lọc trên số dòng đã tải không tìm ra khách cũ.
Vòng 3 (rà 808a738): (10) Danh sách nào trả N dòng mới nhất (chiến dịch, sổ)
thì ô tìm và chip phải hỏi máy chủ, có nút Xem thêm; lọc trên trang đã tải là
mất bản ghi cũ. (11) Màn mới mở rộng quyền xem (CRM cho Marketing, quản lý cửa
hàng) mà dẫn sang màn cũ có cổng hẹp hơn (hồ sơ bán hàng) thì phải rẽ theo vai,
không nới cổng cũ; giữ danh sách vai hai bên trùng nhau bằng ca kiểm.
Vòng 4 (rà fe4ddf4): (12) Màn có bản nháp tự lưu mà Lưu xong vẫn ở lại sửa
tiếp thì phải mở lại màn qua bản bọc của 48 với mã vừa có (thay nấc đang đứng),
vì lời gọi lưu đã làm 48 thôi theo dõi. Ca kiểm phải chạy 48 thật và kiểm khoá
bản nháp sau khi lưu, không chỉ lúc mở màn.
Vòng 5 (rà 3a79937): (13) Codex nêu một chỗ vi phạm luật chung (ô tìm ở đầu
mọi danh sách, có tên món thì có ảnh) thì rà CẢ mô đun theo luật đó trong cùng
vòng, không chỉ sửa đúng dòng được chỉ: vòng 3, 4, 5 lần lượt lộ thêm từng chỗ
cùng loại (Hiệu quả, món giới thiệu, bộ lọc đã lưu, món trong bộ lọc).

## 26/10/2026 (v612): đối tác báo "gửi curl xem", lỗi nằm ở thân yêu cầu mình đoán

GreenSM sandbox trả 400 "missing required fields" suốt từ 21/10 vì khung cũ
ĐOÁN tên trường (`pickup`/`dropoff` số ít, `lat`/`lng`, `contact_name`) khi
tài liệu chưa có. Tài liệu ra rồi thì đúng là `pickups`/`dropoffs` (mảng),
`service_ids` + `points` (`latitude`, `longitude`, `phone_number` dạng +84).
Bài học: (1) khung viết theo đoán phải ghi rõ là ĐOÁN và có ca kiểm chốt
không còn sót chỗ đoán khi đã có tài liệu; (2) sandbox của đối tác thường
là dữ liệu GIẢ (mọi địa chỉ cùng một giá): không bao giờ để giá sandbox lọt
ra cho khách, và không gọi xe sandbox cho vận đơn thật; (3) đột biến "lọt"
lần đầu (M6) là do tệp .pyc cũ, cùng bẫy với v609: chạy đột biến luôn với
PYTHONDONTWRITEBYTECODE=1 và xoá __pycache__ của tệp vừa đổi.

Vòng Codex #499 (v616): (4) Giữ một bản giá ở máy chủ để "tạo đơn từ chính
bản đó" thì phải giữ kèm DẤU của mọi đầu vào làm ra bản giá (nơi giao, người
nhận, số điện thoại, tiền thu hộ, điểm lấy) và so lại lúc tạo đơn. Vận đơn bị
đồng bộ Pancake đổi địa chỉ, COD giữa hai lần bấm là chuyện thường; chỉ so loại
xe và dịch vụ thêm thì tài xế được gọi tới địa chỉ cũ và thu tiền khách đã trả.
(5) Nút thêm bằng `add_custom_button` trên Desk không tự xuống app (app chỉ đọc
cấu trúc ô của doctype): thêm nút trên Desk là phải thêm thao tác tương đương ở
màn app và ca hành vi bấm nó.
(6) Bản giá giữ chung theo vận đơn thì lần Xem giá sau (người khác, tab khác)
ghi đè lần trước: màn phải giữ MÃ bản giá mình đã hiện và gửi kèm khi Gọi xe;
máy chủ khác mã thì bắt xem lại, không âm thầm đặt theo cước người kia thấy.
(7) Trên màn, chốt dữ liệu người dùng xác nhận vào biến riêng TRƯỚC khi mở hộp
xác nhận, và khoá nút hành động trong lúc đang chờ mạng: phản hồi về muộn khi hộp
còn mở sẽ thay biến chung, gửi đi thứ người dùng chưa từng thấy.

## 28/10/2026 (v617): Bootstrap lật thẻ thành cột, và danh sách cắt trước khi xếp

(1) Frappe nạp Bootstrap, mà Bootstrap đặt `.card{display:flex;flex-direction:column}`.
App `/bep` dùng lại tên lớp `.card` và nhiều chỗ tự đặt `display:flex` để xếp ngang
(hàng tab Vận đơn, ô tổng Danh sách khách hàng): thiếu `flex-direction` là bị lật
thành cột, chữ dồn xuống, ô cao bất thường. Thẻ của app nay ghi rõ hướng hàng
ngang trong 00-nen.js. Dựng bố cục ngang trong `.card` thì nhớ lớp này có từ trước.

(2) Màn ghi "chi nhiều nhất lên đầu" nhưng máy chủ lấy 400 khách ĐẦU BẢNG CHỮ CÁI
rồi mới xếp theo tiền: khách chi nhiều mà tên bắt đầu bằng chữ T không bao giờ
hiện, và dòng tổng chỉ là tổng của 400 người đó. Danh sách nào hứa một thứ tự
thì phải xếp và cộng NGAY TRONG CÂU TRUY VẤN trên đủ nhóm, rồi mới cắt. Ca kiểm
chốt câu SQL (khach_thuan.py) và chốt màn chỉ hiện số máy chủ cộng.

(3) Ô tìm dùng lại lớp `.tin` (ô gõ số tiền) thì chữ 22px canh giữa, đậm, nhìn
lệch hẳn với các ô khác. Ô tìm dùng `class="tin tim" type="search"`.

(4) Kênh gửi ra ngoài mà phiên làm việc không đọc được tài liệu gốc (trang tài
liệu Zalo là ứng dụng một trang, không đọc bằng công cụ được): để kênh TẮT sẵn
trong Cài đặt, có nút Gửi thử vào tài khoản của chính mình, và ghi rõ trong PR
là định dạng thân tin chưa đối chiếu trên OA thật. Không bật cho khách trước khi
Gửi thử thành công.

(5) Bench tích hợp đỏ hai lượt liền (878fb55, 4ac5204) mà bàn giao vẫn ghi "cổng
đạt", vì chỉ chạy bốn cổng ở máy rồi đọc mỗi kết luận của Codex. Ca bench v614
gọi lưu chiến dịch mà không gửi mốc sửa (hợp đồng mới của v617) và còn chờ câu
chặn cũ "Kịch bản gọi chưa được duyệt". Đổi câu chặn hay đổi tham số bắt buộc
của một hàm thì `grep` cả `vagabond/khung/kiem_that/`, và trước mỗi bàn giao đọc
cột kiểm `bench` của đúng SHA trên PR: chỉ ghi "bench đạt" khi đã thấy nó xanh.
Phần mới chạm cơ sở dữ liệu (câu SQL tự viết, bulk_insert, bảng mới) phải có ca
trên bench, vì lớp Frappe giả của tầng khung không chạy câu SQL.

(6) GreenSM: tài liệu ghi `order_time` = 0 là "giao ngay", nhưng đo trên sandbox
28/10/2026 thì 0 bị trả 400 "missing required fields", giờ hiện tại thì báo giá và
tạo đơn được. Lớp Frappe giả và bench không gọi đối tác thật nên không thấy; nút
Thử kết nối chạy trên site mới lộ ra (đúng ngày deploy v616). Mã gọi đối tác phải
chạy một chuỗi thật trên sandbox trước khi bàn giao, không chỉ khớp tài liệu.
## 28/10/2026 (v618): nửa đồng làm tròn hai kiểu thành một dòng không mã hàng

- Hoá đơn An Phú C26MYY/8345: bưởi 7,7 kg x 45.065 = 347.000,5. Người bán làm
  tròn nửa đồng lên (347.001), ERPNext làm tròn nửa đồng về số chẵn (347.000).
  Phép nắn cả tờ thấy thiếu 1 đồng nên thêm dòng "Chênh lệch làm tròn" không mã
  hàng vào 632; tờ HDM-26-10-00298 kẹt "Thiếu mã hàng", giá trị hàng hụt 1 đồng.
- Luật: thành tiền từng dòng trên hoá đơn là số gửi cơ quan thuế. Lệch dưới một
  đồng ở một dòng thì đơn giá dòng chịu theo thành tiền (số lẻ đơn giá 9 chứa
  được), không đẩy ra dòng bù. Dòng bù chỉ còn cho phần không đặt được vào dòng
  nào (phí ngoài dòng hàng, số lẻ đơn giá không đủ chứa).
- Mọi đường đọc dòng để tính tiền (dựng mới, dựng lại, ghim lại theo gốc, dự
  kiến tổng) đi qua một hàm `dong_may_ghi`. Ghim lại theo gốc mà kéo về giá in
  trên hoá đơn là lật đi lật lại giữa hai đơn giá mỗi lần lưu.
- Codex #512: đơn giá lẻ thì một dòng chia qua nhiều phiếu nhập, mỗi dòng con
  làm tròn riêng (2 x 3,85 kg ra 173.501 + 173.501 = 347.002). Chia TIỀN của
  dòng gốc cho các dòng con trước (phần dư vào dòng lẻ lớn nhất) rồi mới ra
  đơn giá từng dòng con; lượt ghim lại theo gốc phải dùng cùng phép chia đó.
- Màn Hoá đơn hôm nay (chị Dễ báo cùng ngày): v617 trả `.card` về hàng ngang để
  chữa các thẻ muốn hàng ngang, nhưng ba thẻ ở màn này lâu nay "đúng nhờ cột" của
  Bootstrap. Nút `.btn` width:100% với flex:none chiếm trọn hàng, chữ bên cạnh co
  còn 0 điểm và dựng đứng từng ký tự. Đổi mặc định của một lớp dùng chung là phải
  rà MỌI chỗ dùng lớp đó theo cả hai chiều: chỗ được chữa và chỗ đang sống nhờ
  mặc định cũ. Nay luật viết: thẻ `.card` khai display:flex ghi rõ
  flex-direction, nút `.btn` khai flex:none ghi rõ chiều rộng (ca
  thu_the_flex_618 soát toàn bộ bep/).

## 28/10/2026 (v619): lịch sử sửa phình vì máy dựng lại bảng con

Cơ sở dữ liệu 1,62 GB trên trần 2 GB. Bảng lịch sử sửa (Version) chiếm 545 MB,
riêng hoá đơn bán hơn 1 GB dữ liệu thô, 97% do Administrator ghi. Nguyên nhân:
nhịp đồng bộ Pancake 30 phút một lần gán `si.items = []` rồi thêm lại mọi món
của hoá đơn nháp, và ERPNext dựng lại bảng thuế theo dòng mỗi lần lưu. Dòng mới
mang tên mới, nên mỗi lần lưu lịch sử chụp lại TOÀN BỘ dòng cũ (removed) lẫn dòng
mới (added) dù nội dung y hệt (đo 111 trên 111 lần dựng lại có bảng món giống
hệt). Lệnh dọn đêm vẫn chạy đều nhưng không thấy, vì lịch sử chứng từ nằm trong
diện bảo vệ không xoá.

Sửa tận gốc (cùng PR): nhịp đồng bộ gắn tên dòng món cũ cho dòng dựng lại cùng
vị trí (`giu_ten_dong`), nên ERPNext cập nhật đúng dòng đó và lịch sử chỉ ghi
trường đổi. Bảng thuế theo dòng do ERPNext tự dựng lại thì vẫn chụp; nhịp gọn
đêm lo phần đó.

Cách phòng: đo dung lượng theo `ref_doctype` và theo khoá trong `data` trước
khi đề xuất dọn. Muốn bớt mà vẫn giữ dấu vết thì gọn đúng phần chụp lặp lại,
giữ ai đổi, lúc nào, trường nào. Bản giả lập cơ sở dữ liệu phải đọc chính câu
lệnh chứ không tự lọc theo tham số: đột biến đổi "and" thành "or" trong câu xoá
đã lọt qua bản giả lập tự lọc. Ảnh và tệp nằm ở ổ đĩa (trần riêng 50 GB), xoá
ảnh không làm tụt con số cơ sở dữ liệu.

Link trong tin Zalo (cùng PR v619, anh Việt 28/10/2026): hơn bốn mươi nơi phát
tin tự ghép "/app/<loại>/<mã>" bằng `get_url`, nên tin ra link Desk trên tên
miền mặc định của site, nhân viên bấm trên điện thoại vào nhầm bản desktop.
Cửa ghi tin (`kenh_zalo._ghi_hop_thu`) nay đổi mọi đường Desk sang màn app qua
`lien_ket_app` (một bảng loại chứng từ -> màn). Tham số `link` đổi nguyên cả
chuỗi (có đường mang dấu cách như "Stock Balance"); chữ trong nội dung thì đổi
theo từng đường. Phiếu xuất PXD dùng chung tiền tố cho xuất huỷ và xuất dùng
nội bộ, nên nơi phát hai tin đó tự ghi màn đúng. Nơi phát tin mới chỉ cần đưa
đường Desk hay đường app đều được, cửa ghi tin lo phần còn lại; loại chưa có
màn app thì về trang chủ app, thêm dòng vào bảng `BANG` khi có màn mới.

Link sâu mất khi phải đăng nhập (cùng PR v619, Codex 4402066952): `reset()`
của khung app tự đặt lại địa chỉ theo màn đang vẽ, nên `reset(scrLogin)` đổi
`/hang-chuyen-ve-kho-toi?mo=...` thành `/bep` TRƯỚC khi nhân viên kịp đăng nhập;
đăng nhập xong `hardNav()` tải lại `location.pathname` (lúc đó là `/bep`), mất cả
màn lẫn phiếu. Phiên hết giữa chừng cũng vậy. Nay `reset(scrLogin)` ghi địa chỉ
đang mở vào kho phiên ngay trước khi đổi, đăng nhập xong `hardNavDich()` đọc ra,
xoá rồi tải lại đúng chỗ. Chỉ nhận đường của một màn trong `VGB_DUONG`. Bài học:
link vào app phải kiểm cả nhánh CHƯA đăng nhập; ca hành vi phải nạp app hai lần
(lần khách, lần sau đăng nhập) theo đúng địa chỉ mà lần một tải lại.

Tin "Dữ liệu hao hụt" (cùng PR v619): hoàn tất lệnh trừ nguyên liệu ĐÚNG theo
công thức, nên phiếu sản xuất không bao giờ cho thấy hao hụt nguyên liệu; chỉ
kiểm kê kho bếp mới đo được thực dùng. Đừng dựng báo cáo hao hụt từ phiếu sản
xuất. Mã tin truyền vào `bao()` phải là chuỗi viết thẳng, không qua hằng số:
ca v604 dò mã nguồn để chốt mỗi tin có nơi phát.

DOM giả: `innerHTML` của thẻ con nằm trong HTML đã đọc luôn RỖNG (cùng PR v619).
`dom_gia.js` chỉ giữ chuỗi `_html` ở thẻ được gán `innerHTML` trực tiếp (thường là
`#vgb`); thẻ con như `#vgbBody` đọc `innerHTML` ra chuỗi rỗng. Ca kiểm "không thấy
chữ X" trên chuỗi rỗng sẽ xanh mà không kiểm gì. Đọc chữ trên màn bằng
`textContent` (hoặc `outerHTML`), và với mỗi khẳng định "không thấy" phải có một
khẳng định "thấy" đi cặp trên cùng nguồn đọc.

### Đếm "lần kiểm kê" phải đọc phiếu kiểm kê, không đọc Stock Reconciliation (v619, Codex 4403241208)

ERPNext bỏ các món khớp sổ khỏi Stock Reconciliation (`remove_items_with_no_change`); kiểm khớp hết thì `kiem_ke.ghi_so` không tạo Stock Reconciliation nào mà phiếu kiểm kê vẫn "Đã ghi sổ". Site 28/10/2026: Pastry nguyên liệu 13/10 đếm 15 món, Stock Reconciliation chỉ còn 9 dòng. Muốn biết bếp đã đếm bao nhiêu và khi nào thì đọc `Phieu Kiem Ke` (dòng `da_dem`), điều chỉnh tồn làm thẳng trên Desk vẫn tính, nhưng cùng ngày với phiếu thì lấy số lớn hơn chứ không cộng.

### Ba bẫy của chuông thông báo và tin hao hụt (v619, Codex 4404477889, 4404477900, 4404477923, 4407978621, 4407978626, 4408086813)

- Hai ô của phiếu hoàn tất lệnh bằng nhau KHÔNG có nghĩa là bếp chép số: `kho_san_xuat.so_hoan_tat` cân dư thì ghi số cân vào cả hai ô (kế hoạch 100, cân 110 lưu 110 và 110). Muốn biết bếp có cân không thì so số nhập kho với số của lệnh (Work Order), con số không bị ghi đè.
- Sổ "Vagabond Tin Kenh" giữ cả tin chờ, hoãn, lỗi, chưa rõ và "Bỏ qua (đã xử lý)". Màn nào nói "tin đã gửi" thì phải lọc `Đã gửi` và `Đã gửi gộp`.
- "Đã đọc" lưu bằng MỘT mốc thời gian thì không được cắt danh sách tin chưa đọc, và mốc chỉ đẩy tới tin mới nhất đã hiện, không tới "bây giờ": cắt ở 60 rồi đẩy mốc là tin thứ 61 thành đã đọc mà không ai thấy.
- Mốc đã đọc của tin Zalo phải so theo LÚC GỬI (`luc_gui`), không theo lúc tạo dòng: tin hoãn giờ im tạo 07:00 gửi 08:30 sẽ thành đã đọc nếu mốc là 08:00 (Codex 4407978621). Tin gửi nhiều nhóm có nhiều dòng sổ; chia trang theo dòng thì bản sao rơi sang trang sau, nên gộp lại khi nối trang (Codex 4407978626). Gộp ở màn thì mốc trang sau phải lấy từ máy chủ (dòng sổ cũ nhất đã đọc), không từ tin cuối đang hiện: trang chỉ toàn bản sao bị gộp hết sẽ giữ nguyên mốc và kẹt mãi một trang (Codex 4408086813).

## 29/10/2026 (v620): cookie Facebook dài hơn ô Data, đơn web không gửi được

Khách bấm quảng cáo Facebook vào web thì đường dẫn có `fbclid` dài; web ghép thành `_fbc` khoảng 180 đến 222 ký tự. Bộ lọc `don_web.fb_hop_le` nhận tới 222 ký tự và `tao_don` cắt ở 250, nhưng ô `fbp`, `fbc` của Vagabond Don Web là Data (varchar 140). Frappe ném `CharacterLengthExceededError` (mã 417, không vào Error Log), cả giao dịch lùi, khách chỉ thấy "Không gửi được đơn lúc này", dãy số đơn nhảy (05714 tới 05737 là các lần hỏng).

- Mọi ô Data nhận chuỗi từ bên ngoài (cookie, mã của dịch vụ khác, đường dẫn) phải có sức chứa không nhỏ hơn số ký tự mã cắt, hoặc dùng Small Text. Ca `thu_fbc_620` tính sức chứa từ chính tệp doctype theo luật Frappe và cho đi giá trị dài nhất bộ lọc nhận.
- Lỗi độ dài cột không vào Error Log: khách báo "không gửi được" mà Error Log trống thì thử gửi lại đúng gói của khách và đọc mã HTTP, đừng kết luận là mạng.

## 29/10/2026 (v621): Zalo đổi luật gửi tin từ 01/03/2026, mã cũ âm thầm hỏng

- ZNS gộp vào ZBS Template Message (01/01/2026). Từ 01/03/2026 tin UID Giao dịch và Truyền thông kiểu cũ ngừng: mọi tin gửi qua API phải theo MẪU đã duyệt, trừ tin tư vấn trong 7 ngày sau tương tác. Kênh "Zalo OA" của Chiến dịch (v617) gọi `message/promotion` kiểu cũ nên không gửi được nữa; đổi sang mẫu là PR riêng.
- `GET /template/info` trả -106 "Method unsupported"; đường đúng là `/template/info/v2` (trả thêm `price_sdt`, `price_uid`, `reason`). Đọc trạng thái mẫu và bộ tham số từ đây rồi mới điền dữ liệu: sai kiểu hay dài quá một tham số là Zalo từ chối CẢ tin.
- Tin khuyến mãi (tag 3, có voucher) cần hạn mức tháng của OA (`/message/quota`, `monthlyPromotionQuota`), bằng 1/6 số tin tag 1 và 2 đã gửi hai tháng trước; site 29/10 là 0. Hạn mức 0 thì KHÔNG phát voucher rồi mới gửi, vì mã sẽ nằm im mà khách không biết.
- Mẫu voucher sinh nhật để tag 2 bị từ chối ("Nội dung gửi thông tin ưu đãi - tag 3"): nội dung ưu đãi luôn là tag 3.
- Tạo mẫu qua API được (`/template/create`, cần ảnh logo 400x96 tải lên `/upload/image` trước), không cần đăng nhập trang quản lý.
- Codex rà PR #517 bắt ba bẫy của việc gửi theo lượt nền: (1) kết quả kiểm lưu theo một khoá (trạng thái duyệt, bộ tham số của mã mẫu) phải xoá ngay khi đổi khoá, nếu không lần hỏi lại lỗi mạng là máy gửi mẫu mới bằng dữ liệu của mẫu cũ; (2) khung giờ phải đọc lại trước TỪNG lời gọi mạng trong vòng gửi, không chỉ một lần đầu lượt; (3) phát voucher thì đọc cả thời hạn chương trình như quầy đọc (`_hop_thoi_gian`) và kẹp hạn mã theo ngày kết thúc, không thì khách nhận quà quầy từ chối; (4) mã lỗi của chính máy (`-1`: mất mạng, không lấy được khoá, phản hồi không đọc được) là lỗi CẢ LƯỢT, dừng lượt và để dòng chờ, vì đánh Lỗi từng dòng thì khoá chống trùng chặn quét lại và một lần mất mạng xoá cả hàng đợi.
- v621 trang thành viên (30/10/2026): `web_order/thanh-vien.css` dùng chung cho trang Đặt bàn. Đổi quy tắc chung (nút, ô nhập, `.nhan`, lề `main`) là đổi luôn giao diện đặt bàn; quy tắc mới đặt dưới lớp riêng của trang (`.tv`) và đổi mã băm `?v=` ở MỌI trang trỏ tới tệp (ca #310 bắt `dat-ban.html` còn mã cũ).
- Codex PR #503: chương trình phát "Mã dùng một lần" mà máy chủ vẫn nhận khi gửi thẳng tên chương trình (không mã) là đường vòng qua mã một lần, OTP và luật một số một lần. Ẩn trên màn quầy chưa đủ; `khuyen_mai.tinh` phải tự chặn. Mã gắn người nhận (`danh_cho`) mà hoá đơn chưa chọn khách thì gắn người nhận vào hoá đơn, không thì hoá đơn thành khách lẻ, không tích điểm đúng người.
- Codex PR #517 vòng 8: trang thành viên chạy với phiên Guest (khách đăng nhập OTP chỉ có cookie riêng), nên mọi hàm mô đun khác mà trang gọi KHÔNG được có cổng quyền nhân viên. Gọi `khach_hang.ds_hang()` (có `_kiem_quyen_ban`) làm trang đổ với mọi khách. Phần đọc dùng chung tách thành hàm không whitelist (`bang_hang`), API nhân viên giữ cổng. Ca kiểm chạy thật cổng quyền với vai Guest và dò mọi lời gọi từ `thanh_vien.py`.
- Bench PR #517 vòng 9: ô `vgb_*` của Customer là Custom Field tạo trên site thật, không nằm trong doctype JSON nên bench chỉ có những ô `nen_bench.py` dựng. Trang thành viên đọc thêm `vgb_sinh_nhat` là cửa `toi` trả 500 trên bench (site thật vẫn chạy). Đọc ô Custom Field mới thì thêm vào `nen_bench.py` cùng PR; ca kiểm `thu_thanh_vien_621` chốt cho trang thành viên và tin Zalo. Ca HTTP bench nên in thân lỗi khi mã khác 200.
- Codex PR #517 vòng 10: khung mời trên trang thành viên hứa "khai đủ là nhận voucher" nhưng nút Lưu hồ sơ chỉ lưu, không cấp quà; hồ sơ đủ thì khung mời tự ẩn nên khách mất luôn đường nhận. Mỗi lời hứa trên giao diện phải có thao tác thật đi kèm ở MỌI trạng thái (thiếu hồ sơ, đã đủ mà chưa nhận, đã nhận); ca hành vi dựng đúng chuỗi khách bấm và đếm lời gọi máy chủ.

## 30/10/2026 (v622): phân hệ Tuyển dụng, ba bẫy gặp khi dựng

- Tệp trang khách trong `public/web_order/` không được cổng nào đọc cú pháp: `kiem_truoc_deploy.sh` chỉ `node --check` app_bep.js. Bản đầu `ung-tuyen.js` khai trùng một biến `const` trong cùng hàm, trình duyệt bỏ cả tệp và trang trắng, mà mọi cổng vẫn xanh. Chỉ ca hành vi nạp thật trang (`hanh_vi/ung_tuyen_622.js`) mới bắt được. Nay công đoạn 2 đọc cả `web_order/*.js`; tệp trang khách mới vẫn phải có ca hành vi nạp thật.
- Đưa một loại khối web sang "ERP là nguồn duy nhất" (ưu đãi v589, tuyển dụng v622) thì các ca cơ chế lưu của trình biên tập đang dùng loại đó làm mẫu sẽ đỏ hàng loạt. Chuyển các ca đó sang loại còn gõ tay (tiệc), đừng xoá ý của ca; ca riêng của form không còn mở được thì ghi rõ đã bỏ vì sao.
- Ô người ngoài gõ vào (đường dẫn CV) dài hơn 140 ký tự thì không được là Data (bài học v620). Ca `thu_tuyen_dung_622._doctype` đưa giá trị dài nhất mã chuẩn hoá nhận qua phép thật rồi so với sức chứa đúng kiểu ô trong JSON.
- Codex rà #518: (1) luật dữ liệu cá nhân (đồng ý lưu, hạn lưu) đặt ở cửa ngõ whitelist là chưa đủ, Desk và REST API của Frappe tạo bản ghi không qua đó; phải đặt ở `validate` của controller doctype. (2) Doctype chứa dữ liệu cá nhân mà bật `track_changes` thì bảng Version giữ bản cũ của tên, số sau khi đã xoá theo hạn; tắt `track_changes` (nhật ký trên hồ sơ thay thế) và xoá Version khi xoá theo hạn. (3) Nhịp đêm chọn lô rồi mới ghi phải khoá và đọc lại từng dòng (`for_update`) trước khi xét điều kiện, vì người dùng có thể đổi trạng thái giữa hai bước.
- Codex rà #518 vòng 2: (1) xoá dữ liệu cá nhân theo hạn phải tìm cả BẢN CHÉP ở bảng khác (tin Zalo chép tên, số vào sổ tin Vagabond Tin Kenh); (2) mọi cửa ghi vào hồ sơ đã xoá theo hạn phải chặn, kể cả phiếu chấm mở từ trước; (3) lọc rồi mới cắt trang: điều kiện lọc mà để sau limit thì vài trăm dòng không còn hợp lệ chiếm hết lô, dòng hợp lệ phía sau không bao giờ tới lượt. Bản giả get_all trong ca kiểm phải giữ đúng limit như Frappe thật, không thì lỗi này không lộ.
- Codex rà #518 vòng 3: chặn ghi lại dữ liệu đã xoá theo hạn ở cửa ngõ app là chưa đủ, Desk vẫn sửa được; luật phải nằm ở `validate` của controller (không ghi lại ô cá nhân, không bỏ cờ đã xoá). Công tắc vẽ 28 điểm thì vùng bấm vẫn phải 44 (bọc trong nút trong suốt cao 44).
- Codex rà #518 vòng 4: màn chỉ đọc "hồ sơ 120 ngày hoặc còn đang xử lý" thì khoản còn nợ (công làm thử chưa trả) của hồ sơ cũ đã Dừng biến mất cùng nút ghi đã trả. Việc còn treo (nợ, chờ duyệt) phải có câu hỏi riêng không theo tuổi hay trạng thái. Bản giả get_all phải giữ cả or_filters, không thì lọc theo tuổi không bao giờ lộ.

## 30/10/2026 (v623): một chương trình phát mã qua hai kênh (Ví quà thành viên và tin Zalo)

- Hai kênh cùng phát mã dùng một lần cho MỘT chương trình thì phải đọc chung một phép "khách đã nhận trong kỳ chưa" (`thanh_vien.ma_vi_trong_ky`), tính mọi trạng thái của mã (đã dùng, đã huỷ, gửi qua kênh kia). Kiểm riêng từng kênh là khách nhận hai mã.
- Kênh gửi tin mà dùng lại mã khách đang giữ thì nhánh "gửi lỗi, huỷ mã" chỉ được huỷ mã do chính lượt đó phát. Huỷ theo biến "mã đang gửi" là một lần Zalo từ chối xoá mất quà trong ví của khách.
- Codex PR #520: kênh thứ hai phát mã mới cũng phải theo đúng luật của kênh thứ nhất (dịp phát, hạn tới cuối tháng sinh nhật, chặn số nhân viên), gom về một phép (`thanh_vien.xet_vi`); và hai kênh phải khoá CÙNG một dòng (hồ sơ CRM của khách, `khoa_ho_so`) trước khi xét "đã nhận trong kỳ", không thì trang thành viên và lượt gửi Zalo chạy cùng lúc ra hai mã. Ghi sổ mã ngay sau khi phát để nhả khoá trước lời gọi mạng.
- Thêm ô vào phiếu Chương trình khuyến mãi thì kiểm cả ba nơi đọc cột theo danh sách cố định: `khuyen_mai.TRUONG_CTKM` (lưu từ app), `zalo_kich_ban.COT_CTKM` (tin Zalo), `thanh_vien.COT_CTKM_VI` (trang thành viên). Thiếu ở một nơi là ô đó im lặng không áp ở kênh đó.
- Codex PR #520 vòng 4: luật "chỉ người nhận dùng" suy từ công tắc hiện tại của chương trình (Phát vào Ví quà) thì tắt công tắc để ngừng phát mới là mở luôn mã cũ cho khách khác. Thuộc tính của mã đã phát phải ghi lên chính mã lúc phát (ô chi_nguoi_nhan), không đọc lại từ cấu hình đang sống.
- Codex PR #520 vòng 5: nhánh "gửi lại mã khách đang giữ" bỏ qua mọi phép xét của nhánh phát mới, nên chương trình đã tắt hay hết hạn vẫn được gửi mã quầy sẽ từ chối. Đường dùng lại phải xét lại đúng điều kiện quầy xét khi tra mã (đang bật, chưa qua ngày kết thúc).

## 31/10/2026 (v625): tuyển dụng đợt 2, form câu hỏi sửa được và AI đọc CV

- Đoán "tên mục" trong mô tả công việc theo độ dài dòng (ngắn, không dấu chấm cuối) là sai với dữ liệu thật: dòng việc "Thu tiền đơn hàng qua chuyển khoản, cà thẻ,..." bị biến thành tiêu đề. Chỉ nhận tên mục khi có dấu hiệu chắc (dấu hai chấm cuối, viết hoa toàn bộ, hoặc trùng tên mục quen thuộc). Phép đoán định dạng chữ người gõ phải chạy thử trên bản ghi THẬT của site trước khi giao.
- Phép "đã xoá theo hạn thì không ghi lại thông tin cá nhân" so `str(giá trị) != giá trị xoá`. Thêm ô ngày, ô tiền vào bộ xoá với giá trị None hay 0 thì phép so luôn lệch và hồ sơ đã xoá không lưu lại được nữa (đổi trạng thái cũng hỏng). So hai vế cùng qua `str(x or "")`.
- Gửi CV cho dịch vụ AI là chuyển dữ liệu cá nhân ra bên thứ ba: câu đồng ý phải nói rõ trước khi gửi, câu giới tính và sinh nhật không bao giờ tới AI (chặn ở cả cấu hình form lẫn bộ lọc dòng gửi), và nội dung CV là dữ liệu chứ không phải lệnh (điểm tổng do máy tính từ tiêu chí cố định, kẹp 0 đến 100).
- Trang Vue đọc nội dung bất đồng bộ: chưa tải xong mà vẽ ngay "chưa có vị trí" là khách thấy câu sai vài trăm mili giây (đo 31/10 tưởng là lỗi dữ liệu). Mục nào đọc từ máy chủ phải có trạng thái "đang tải" riêng (`ND.daTai`).
- Trạng thái "đang tải" phải có lối ra khi tải LỖI (`ND.loiTai`), không thì mục kẹt "Đang tải" mãi. CI ảnh của PR #523 báo cảnh lỗi tải đổi nên mới soi ra.
- Codex #523, bốn lỗ cùng một gốc "chặn ở chỗ này mà quên chỗ kia": công tắc "Cho AI dùng" chỉ lọc câu trả lời chữ, tệp CV đi đường riêng nên vẫn bị gửi; phép chặn ghi lại sau khi xoá theo hạn có ở hàm thuần nhưng `validate` của phiếu không đưa bảng con câu trả lời vào; việc nền kiểm "đã xoá" lúc bắt đầu rồi ghi không điều kiện lúc kết thúc (ghi cuối phải là một câu UPDATE có điều kiện `da_an_danh = 0`); trần chi phí đếm số hồ sơ có `ai_luc` trong tháng nên Chấm lại một hồ sơ 301 lần vẫn tính 1. Trần chi phí phải đếm từng LƯỢT gọi, giữ lượt trước khi gọi (ghi trước, đếm sau, vượt thì gỡ dòng của mình).
- Thêm một khoá mới vào `noi_dung_web.cong_khai()` là bench ERPNext `web_editor_245` đỏ ("Guest không đọc được nháp"), vì ca đó so bản công khai bỏ các phần dẫn xuất với nội dung mặc định. Mọi khoá ghép thêm phải vào `DAN_XUAT` của ca bench; ca `_bench_245_thuan` trong bộ kiểm thuần chạy đúng phép so đó để không phải chờ bench mới thấy.
- Giới hạn của một câu cụ thể (ngày sinh không quá hôm nay, từ 1940) không được đặt theo LOẠI câu: Minh Vũ thêm câu Ngày khác ("ngày có thể bắt đầu làm") là ứng viên chọn ngày tương lai bị chặn. Giới hạn riêng theo mã câu, loại câu chỉ giữ phép kiểm chung.

## 31/10/2026 (v626): phân hệ Tài chính, ba bẫy gặp khi dựng

- Số dư lấy từ sổ cái là sai: 11211 MB đang âm 5,8 tỷ, 1111 âm 249 triệu vì chưa nhập số dư đầu và tiền bán tại quầy không đi qua 1111. Số dư phải là mốc chốt người đếm hoặc sao kê đưa vào, cộng phát sinh sau ngày chốt.
- SePay `userapi/bankaccounts/list` có ô `accumulated` nhưng MB, OCB, ACB luôn trả 0; chỉ Shinhan trả số dư thật. Đối chiếu chỉ khi SePay báo số dương; báo 0 thì ghi "không báo", không được kết luận khớp hay lệch.
- Chạy đột biến bằng lệnh có trần thời gian: lệnh bị cắt giữa chừng thì tệp đang bị làm hỏng KHÔNG được trả lại (khối `finally` không chạy khi tiến trình bị giết). Lần chạy sau thấy "mẫu không khớp" là dấu hiệu tệp còn đột biến cũ; kiểm `git diff` ngay. Chạy đột biến chỉ với bộ ca của tính năng cho nhanh, rồi chạy lại cả bộ.
- (Codex #524) Ghép chuyển nội bộ chỉ theo "cùng ngày, cùng số tiền, khác tài khoản" là sai: site có 99 cặp như vậy từ 01/08, chỉ 33 cặp là chuyển thật; còn lại là khách chuyển vào MB công ty và quỹ tạm ứng trả NCC đúng số đó. Phải có bằng chứng cùng lệnh: chung mã tham chiếu FT, hoặc hai nội dung chung một đoạn liền từ 20 ký tự (chuyển thật chung từ 25, cặp trùng tiền chung nhiều nhất 13).
- (Codex #524) Màn tổng hợp nhiều nguồn: nguồn đọc hỏng không được thay bằng 0 rồi vẫn ra kết luận. Ghi "Chưa đọc được" ở đúng ô đó và không đưa ra con số cuối cùng.
- (Codex #524) Một đồng tiền chỉ thuộc MỘT nguồn: phiếu thu tại quầy (Payment Entry mang ô `vgb_quay`) đã cộng vào két qua phép Chốt ca, nên câu đọc sổ cái quỹ công ty phải loại nó cùng với hoá đơn bán. Gom điều kiện vào một hằng dùng chung cho mọi câu đọc quỹ.
- (Codex #524 vòng 3) "Chưa có số" có hai nghĩa phải tách: CHƯA CHỐT (người dùng chưa nhập, cộng 0 là đúng) và TÍNH HỎNG (không biết số, mọi kết luận cộng dồn phải dừng). Gắn cờ `loi` ở chỗ bắt lỗi, đếm riêng, và đừng lưu bộ nhớ đệm một kết quả còn thiếu phần đọc hỏng.
- (Codex #524 vòng 4) Đọc sổ cái cho dòng tiền phải đọc CẢ Nợ lẫn Có của cùng tài khoản: chỉ đọc cột Có thì khoản thu thẳng vào quỹ làm số dư tăng mà dòng tiền không thấy. Ca kiểm dựng cả hai chiều trong cùng một ngày và có sẵn tiền két để bắt cả lỗi ghi đè.
- (Codex #524) Ô "tong" của màn Công nợ là số CÒN GOM ĐƯỢC (bỏ tờ đã nằm trong phiếu đòi nợ chờ thu), không phải tổng khách nợ. Nơi nào cần tổng nợ thật thì đọc `tong_ca_phieu`. Site 31/10: 13 phiếu Chờ thu giữ 27 hoá đơn, nợ sổ cái 64.138.500 đ, nằm ngoài "tong".

## 01/11/2026 (v627): Tài chính báo "Chưa đọc được SePay" trên site thật

- `frappe.make_get_request` chỉ có trong System Console và Server Script (Frappe tiêm vào không gian tên đó). Mã của app gọi nó là AttributeError, bị khối bắt lỗi nuốt, màn báo "Chưa đọc được SePay" mãi. Bài học này đã gặp ngày 19/08 ở `sepay.py` mà vẫn lặp ở `tai_chinh.py`. Trong mã app luôn dùng `from frappe.integrations.utils import make_get_request`.
- Mọi ca v626 thay `_sepay_so_bao` bằng bản giả nên hàm gọi mạng thật chưa chạy lần nào trong kiểm thử. Hàm chạm dịch vụ ngoài phải có ít nhất một ca chạy HÀM THẬT với frappe giả giống site thật (không có thứ chỉ Console mới có), chỉ thay tầng HTTP.
- Đừng lưu bộ nhớ đệm kết quả rỗng của một lần gọi ngoài: lỗi tạm thời thành lỗi kéo dài suốt thời gian đệm.

## 02/11/2026 (v628): tính năng có trên máy chủ mà app không gọi thì người dùng coi như không có

- Lịch kiểm kê xoay vòng (`kiem_ke.lich_hom_nay`, `tao_phieu_hom_nay`) có từ 02/08 nhưng không màn nào gọi. Bếp chỉ có phiếu cả kho (Pastry 205 món) nên hai tháng gần như không đếm, hao hụt tháng 10 ra 162%. Mỗi hàm mở ra ngoài phải có đường bấm thật trên app; rà `thu_cua_ngo.py` thấy hàm không màn nào gọi thì báo.
- Mã "APP.26.10.123" trong nội dung chuyển khoản KHÔNG trùng tên phiếu APP-26-10-123 trên ERP (site 02/11: APP-26-10-123 là 875.000 đ, ngân hàng chi 15.725.120 đ). Đừng khớp tiền ra với phiếu chi theo chuỗi này; đọc ô tiền chưa gắn (`unallocated_amount`) của giao dịch ngân hàng.
- Tin Zalo mới phải được tích ở Tin nhận của nhóm mới tới. Site 02/11: tin "Tiền vào tài khoản công ty chưa gắn chứng từ" (v611) chưa nhóm nào tích nên chưa từng tới ai. Mỗi tin mới kèm bản vá tích sẵn cho nhóm mốc như v619, v628.
- Một luật "ai giữ khoản tiền" phải giống nhau ở MỌI cửa hỏi chủ. Site 02/11 (bill SOL3D4A9 bấm nhầm điểm, đã huỷ): `doi_soat_sepay.chu_cua_giao_dich` đã coi nháp huỷ mềm là không giữ tiền, nhưng `_gd_da_co_chu` và `_chu_ma_bill` của nút Dò tiền vẫn tính nó là chủ, nên bill lập lại không gắn được 1.130.000. Bill huỷ chỉ nhả tiền khi CHƯA có phiếu hoàn tiền; luật thuần nằm ở `doi_soat_ck.bill_huy_nha`.
- Mã bill trong nội dung chuyển khoản mà không bill nào lưu không phải lúc nào cũng "của bill khác": app tải lại trước khi lưu là bill mất hẳn (ca NVHCXVC4). Cửa gắn coi mã mồ côi là tiền chưa thuộc ai sau 15 phút; trước 15 phút vẫn giữ cho bill đang hiện mã QR.
- Mọi cửa làm ĐỔI số quỹ (kiểm quỹ, nộp ngân hàng, Giám đốc duyệt chênh lệch, huỷ phiếu) phải lấy CÙNG một khoá quỹ trước khi đọc. Khoá riêng dòng phiếu không đủ: kế toán kiểm lại chạy chen lúc Giám đốc đang duyệt sẽ đọc số máy chưa trừ khoản đang duyệt và lập thêm một phiếu thiếu cùng số (Codex #527 vòng 4, mô phỏng: hai bút toán thiếu 3 triệu, quỹ còn 4 triệu thay vì 7). Với MariaDB REPEATABLE READ còn phải kết thúc giao dịch đọc trước khi xin khoá, không thì đọc sau khoá vẫn là ảnh chụp cũ.
- Phiếu kiểm kê KHÔNG khoá nhập xuất (phiếu Đếm hôm nay của bếp) phải ghi sổ đúng mốc bếp chốt đếm, không theo giờ quản lý bấm ghi sổ. Kiểm kê đặt tồn tuyệt đối tại mốc của nó: đếm 10 kg lúc 09:00, xuất 3 kg lúc 10:00, duyệt 11:00 mà ghi lúc 11:00 thì tồn quay lại 10 thay vì 7 (Codex #527 vòng 5). Phiếu thường đã khoá mã từ lúc lập nên không bị.
## 02/11/2026 (v630): thẻ "chỉ xem" lấy từ ERP vẫn phải chừa việc của người không vào được app

- Tuyển dụng thành "ERP là nguồn duy nhất" (v622) thì thẻ Tuyển dụng của trình biên tập thành chỉ xem, nút "Mở Tuyển dụng trên app". Nhưng người làm ảnh là Marketing, không có vai Tuyển dụng nên không mở được màn sửa vị trí; màn đó lại chỉ cho chọn bốn ảnh có sẵn. Kết quả: không ai trong bộ phận Marketing đổi được ảnh thẻ (Minh Vũ báo 02/11). Khi chuyển một loại nội dung sang ERP, liệt kê từng ô theo NGƯỜI hay sửa nó; ô của người không có vai bên ERP (ảnh, chữ quảng bá) phải có cửa ghi hẹp đúng ô đó ở trình biên tập, chặn quyền ở máy chủ.
- Bảng Nâng cao vẫn mở được khối Tuyển dụng, Ưu đãi gõ tay cũ với ô "Tải ảnh" và câu "ảnh có thể thay bất cứ lúc nào", trong khi máy chủ giữ nguyên các khối đó khi lưu. Ô sửa không có tác dụng còn tệ hơn không có ô: thay bằng câu chỉ đường tới đúng chỗ sửa.
- Hai cửa tải ảnh công khai (trình biên tập, app) dùng chung một phép kiểm ảnh (`luu_anh_cong_khai`); mỗi cửa tự kiểm vai của mình TRƯỚC khi gọi. Ca kiểm vai nhớ: `System Manager` nằm trong cả hai nhóm vai, lấy nó làm "vai Tuyển dụng" thì ca chặn Marketing không bao giờ đỏ.

## 02/11/2026 (v631): giá do máy chủ chốt thì mọi lối miễn cũng phải do máy chủ chốt

- Lối miễn giá theo nhãn do máy khách gửi là lỗ hổng: `ap_gia_diem` từng bỏ qua dòng có ô `combo` (chữ tự do), nên gửi `{TEA, rate 1, combo: "bất kỳ"}` vẫn lưu giá 1 đồng ở điểm giá 70.000 (Codex #532, tái hiện: trước 1 đ, sau 70.000 đ). Chỉ miễn dòng mà máy chủ đã xác nhận: có mã combo vừa kiểm thành phần, hoặc dòng gốc trên hoá đơn mang dấu combo.
- Màn quầy giữ tham chiếu tới MỘT đối tượng cấu hình (`posQuay`) lấy lúc chọn điểm. Cấu hình đọc lại thì là đối tượng mới, còn tham chiếu cũ vẫn mang giá cũ: giỏ thu 140.000 trong khi máy chủ lưu 130.000. Đọc lại cấu hình thì phải thay tham chiếu và đặt lại giá giỏ; máy chủ tự sửa giá mà không báo thì chặn ở màn mới (cờ `gia_theo_diem`) để thu ngân không thu theo tổng cũ.
- Bản nháp chưa lưu của một màn nhiều "đối tượng" (bảng giá từng điểm) phải gắn với đối tượng đó. Chặn ở MỘT lối đổi (chip) không đủ khi còn lối khác (nút ở Cài đặt): cho mọi lối đổi đi qua một hàm duy nhất.
- Hàm lọc nhận một tham số phụ ngoài đối tượng lọc (ngày hôm nay cho chip Hẹn hôm nay) thì mọi chỗ đếm chép lại đối tượng lọc đều quên truyền nó: danh sách đúng mà số trên chip về 0, chip nguồn biến mất (Codex #532). Cho tham số đó đi trong chính đối tượng lọc, và so ngày thì chặn trường hợp hai chuỗi rỗng coi là khớp.
- Thêm một bảng giá bán ra mới (Price List "Giá riêng <điểm>") là đổi kết quả của MỌI câu đọc Item Price không lọc `price_list`. `khuyen_mai._gia_ban` (giá món tặng) và `vagabond_combo.gia_ban_mon` (giá gốc thành phần combo) lấy giá mới sửa gần nhất của bất kỳ bảng nào, nên giá NVH có thể lọt sang District 1. Dùng chung `diem_ban.loc_bo_bang_rieng()`. Thêm bảng giá thì `grep '"Item Price"'` và rà từng câu.
- Máy chủ chốt giá phải chốt cả giá CHUNG, không chỉ giá riêng: món vừa bị bỏ giá riêng (hay bảng giá điểm vừa tắt) mà giỏ cũ còn giá riêng thì phép "chỉ sửa món có trong bảng giá điểm" để lọt (Codex #532 vòng 3). Chỉ đối chiếu ở màn gửi cờ (quầy); màn nhập đơn tay giữ giá gõ.
- Đặt lại giá ở máy chủ cho một bill ĐÃ LƯU thì phải có chính sách rõ cho dòng cũ: sửa ghi chú bill nháp mà máy chủ lặng lẽ đưa hai ly trà 70.000 lên 80.000 là lưu 160.000 trong khi thu ngân vừa xác nhận 140.000 (Codex #532 vòng 5). Chính sách v631: dòng đã lưu giữ giá đã chốt với khách, chỉ món thêm mới theo giá hiện hành, và màn sửa bill bị chặn để xem tổng mới nếu món thêm mới mang giá cũ.
- Tên dòng gốc (`dong_goc`) máy khách gửi lên chỉ là con trỏ, không phải bằng chứng: miễn kiểm giá vì "dòng gốc có thật" thì gửi dòng gốc của ly trà kèm mã bánh khác giá 1 đồng vẫn lọt (Codex #532 vòng 6). Miễn gì theo dòng gốc thì phải so cả mã món với dòng gốc trên máy chủ.
- Mã combo thật cũng chỉ chứng minh món thuộc combo, không chứng minh giá: gửi ly trà kèm mã combo thật giá 1 đồng vẫn lọt (Codex #532 vòng 7). Dòng combo phải lấy giá thành phần từ cấu hình combo trên máy chủ; combo không khai giá cho món thì tính như món thường.
- "Bỏ giá riêng" không phải xoá dòng giá (QT-20, Codex #532 vòng 8): bản đầu gọi `delete_doc` lên Item Price khi quản lý xoá trắng ô giá NVH, và cả khi dọn dòng trùng. Bỏ giá thì khoá hạn `valid_upto` tới hôm qua (dòng khai hôm nay thì lùi cả `valid_from`, như `banh_si.bo_gia`), đặt lại giá thì thêm dòng mới. Khoá hạn rồi thì MỌI câu đọc bảng đó phải lọc hiệu lực, nên đọc gom về một chỗ (`diem_ban._dong_gia_diem` rồi `gia_dang_ap`), ca kiểm chốt chỉ còn một câu `get_all("Item Price")` trong mô đun. Bộ giả trả toàn dòng còn hạn thì đột biến "đọc thô không lọc hạn" lọt; phải có dòng đã khoá hạn trong dữ liệu giả.

## 02/11/2026 (v630): trang Đặt bàn kiểu mới, hai bẫy khi kiểm
- Trang gọi `crypto.randomUUID()` cho khoá lần gửi; hàm này chỉ có ở ngữ cảnh an toàn (https hoặc localhost). Chụp thử bằng Playwright trên một tên miền http giả (ví dụ http://vagabond.test) thì trang đứng ở "Đang tải lịch" mà không báo gì. Xem thử trang khách thì mở qua http://localhost hoặc https.
- DOM giả (`hanh_vi/dom_gia.js`) vẫn phát click vào nút đang `disabled`, trình duyệt thật thì không. Ca hành vi kiểm "giờ đã qua không bấm được" phải tự bỏ click vào nút tắt (hàm `bam` của `dat_ban_630.js`), nếu không ca đo một đường trình duyệt không bao giờ đi. Nút trừ cộng đã tắt ở mức trần thì phép kẹp chỉ thử được bằng đường gõ tay vào ô số (đột biến M6 lần đầu sót vì lý do này).

## 02/11/2026 (v630): bánh thiết kế riêng, cọc 50% qua luồng đặt bánh của app

- Hoá đơn lập từ phiếu đặt bằng `make_sales_invoice`: nếu `allocate_advances_automatically` bật, `validate` của lõi gọi `set_advances()` với `include_unallocated` và vơ MỌI khoản ứng trước chưa phân bổ của khách (tiền nạp số dư, tiền chuyển dư cũ), không chỉ tiền của phiếu đặt đó (erpnext/controllers/accounts_controller.py, nhánh `if cint(self.allocate_advances_automatically)`). Tắt cờ, tự dựng bảng advances chỉ từ phiếu thu đã ghi sổ trỏ đúng phiếu đặt (`thiet_ke_rieng.chon_ung_truoc`). Tầng khung không bắt được lỗi này (đột biến M13 lọt), chỉ ca bench `kiem_that/thu_thiet_ke_rieng_630` đọc lại khoản ứng trước khác của khách.
- Phiếu thu tiền chuyển khoản do máy lập khi khớp SePay phải chiếm dòng sao kê qua sổ đối soát chung (`doi_soat_sepay.khai`, ô trên chính phiếu thu, phiếu huỷ nhả dòng), không thì nhịp 5 phút và lượt khách hỏi trạng thái cùng lúc lập hai phiếu cho một lần chuyển. Khớp chạy trong khoá hàng của phiếu đặt.
- Phương thức "Trả trước" cố ý không hiện ở nguồn đơn nào, nên phép so phương thức với nguồn ở `ban_hang.kiem_truoc_khi_luu` chặn nhầm hoá đơn ngày giao của phiếu đặt. Miễn chỉ khi MỌI dòng trỏ phiếu đặt (`dat_banh.la_hoa_don_tra_truoc`).
- Web Vue: tab chỉ hiện sau khi nội dung về (`:hidden`) thì `scrollIntoView` lúc mở link thẳng không làm gì; theo dõi cả điều kiện hiện tab, không chỉ `S.tab`.

## 02/11/2026 (v630): bánh sỉ trên web, giá riêng từng khách và hàm trùng tên

- Item Price có ô `customer` và lõi ERPNext lọc đúng theo khách, nhưng ba chỗ của app đọc bảng giá bán mặc định mà KHÔNG lọc khách (`chon_mon._gia_ban` lấy giá hiện trên web, `pancake_sp._gia_niem_yet` lấy giá đẩy Pancake, `doi_soat` ghi đè giá theo mã). Thêm dòng giá riêng của một khách vào bảng mặc định là giá sỉ của quán đó có thể thành giá công khai. Giá riêng để ở bảng giá bán RIÊNG ("Giá sỉ theo khách"), đọc qua một hàm `banh_si.gia_cua_khach`; ca `thu_banh_si_630` chốt không mô đun nào khác chạm bảng đó.
- Một hàm thuần `trang_thai_don(tra_truoc, tong, ...)` bị cửa whitelist cùng tên `trang_thai_don(ma)` khai SAU trong cùng tệp đè lặng lẽ: Python không báo, `tom_tat` gọi nhầm cửa API. Chỉ ca chạy thật mới thấy (TypeError). Tệp có cả phép thuần lẫn cửa API thì đặt tên khác hẳn nhau; ca kiểm dò tên hàm trùng trong tệp (`_trung_ten`).
- Hoá đơn ngày giao của đơn sỉ lập TỪ phiếu giao (phiếu giao lập từ phiếu đặt), không lập thẳng từ phiếu đặt: `hach_toan_kho.du_dieu_kien_ban` bỏ qua tờ có phiếu giao nên kho chỉ trừ một lần ở phiếu giao. Nguồn "Khách sỉ" ở quầy chỉ cho Chuyển khoản, Tiền mặt; tờ Công nợ của đơn sỉ web do máy lập được miễn phép so nguồn CHỈ khi phiếu đặt mang đúng mã BSI (`banh_si.la_hoa_don_si_web`).


## 02/11/2026 (v631, Codex #531): khoá rồi mà vẫn đọc ảnh chụp, và cổng đính tệp chỉ nhận ảnh

- Lần thứ tư cùng một bẫy (sau #368, v586 đặt tiệc, PR476): `ung_truoc_don.khop` khoá hàng phiếu đặt rồi đọc phiếu thu (`get_all`) và chủ dòng sao kê (`chu_cua_giao_dich`, cũng `get_all`) bằng phép đọc thường. Lượt khách hỏi trạng thái đã đọc phiếu đặt TRƯỚC lúc khoá, nên sau khi chờ khoá nó vẫn thấy ảnh chụp cũ và lập phiếu thu thứ hai cho cùng dòng sao kê: cọc 50% (3.780.000) thành 7.560.000, đơn hiện "đã thu đủ". Cách sửa: sau khoá đọc phiếu thu bằng `for update` qua bảng tham chiếu (có chỉ mục), khoá các dòng sao kê theo tên TRƯỚC khi đọc chủ, đọc chủ của chính luồng bằng `for update` trên ô `vgb_gd_tkr` (đã thêm `search_index`). `get_all` của Frappe v16 không có `for_update`; đọc có khoá trên ô KHÔNG có chỉ mục là khoá cả bảng, nên ô dùng để khoá phải có chỉ mục.
- Không đặt ràng buộc duy nhất cho ô dòng sao kê đã chiếm: phiếu thu tiền mặt để trống ô (chuỗi rỗng trùng nhau), và phiếu đã huỷ phải nhả dòng cho phiếu mới. Ô mã lần gửi thì đặt được (`unique`, Frappe đổi chuỗi rỗng của ô unique thành NULL) vì ô mới chưa lên site; ô đã có dữ liệu thì phải dọn chuỗi rỗng trước như `khoa_ma_pancake`.
- Mã lần gửi tra lại sau khoá cũng phải là đọc hiện tại (`_da_gui(..., khoa=True)`), cả ở `banh_si.dat` nơi phép đọc phiên khách đã chụp ảnh trước lúc khoá hàng khách.
- Ca kiểm tầng khung mô phỏng được bẫy này: MariaDB giả trong `thu_codex_531.py` cho mỗi yêu cầu một luồng thật, đọc thường thấy ảnh chụp lấy ở lần đọc thường đầu tiên, đọc `for update` thấy bản đã commit và giữ khoá tới hết yêu cầu, thứ tự đan xen đặt bằng điểm dừng. Bộ giả cũ trả cùng một danh sách cho mọi kiểu đọc nên không bao giờ đỏ.
- `tra_truoc_khach._dinh_tep` chỉ nhận ảnh (`hang_tang.la_anh`) và trả 0 khi bỏ tệp; màn Đơn đặt trước, Đơn sỉ web cho chọn PDF giấy báo Có rồi ghi sổ luôn, hook `chan_thieu_dinh_kem` chặn với câu "Uỷ nhiệm chi" và bánh không giao được. Đường đính chứng từ ngân hàng phải nhận cả PDF (luật đuôi lấy từ `tep_dinh_kem.loi_tu_choi`), kiểm số tệp đã đính TRƯỚC khi gọi `submit()` và nói rõ cần ảnh hay PDF. Thấy một hàm trả số đếm mà nơi gọi bỏ qua giá trị đó thì đọc kỹ nhánh trả 0.
- Vòng 3 (Codex #531): sửa phép tra mã lần gửi thành đọc hiện tại vẫn chưa đủ; hàm dựng phản hồi ngay sau đó (`_ket_qua`, `tom_tat`) đọc lại phiếu đặt bằng phép thường, không thấy phiếu của lần gửi trước vừa commit và nổ `'NoneType' object has no attribute 'rounded_total'`. Đọc hiện tại phải đi XUYÊN SUỐT tới khi trả phản hồi (`_ket_qua(..., khoa=True)`, kể cả dòng hàng). Ca kiểm vòng trước đã thay `_ket_qua` bằng hàm giả nên che đúng chỗ này; ca kiểm đường đồng thời phải giữ thật mọi hàm đọc dữ liệu tới hết phản hồi.
- Vòng 4 (Codex #531): màn Công nợ hiện số CÒN PHẢI ĐÒI nhưng `lap_phieu_doi_no` lấy nguyên `grand_total` làm số dòng phiếu, nên hoá đơn 1.000.000 đã trả 600.000 thì phiếu và QR (cả Sales lẫn khách sỉ tự bấm) đòi 1.000.000. Màn và phiếu phải đọc CÙNG một phép tính (`cong_no.tinh_con_doi`: dư nợ sổ cái, dòng thanh toán, trừ tiền đã về đã xác minh); con số người dùng nhìn thấy trước khi bấm phải là con số máy ghi sau khi bấm. Phiếu đã lập trước đó giữ nguyên số của nó.
- Vòng 5 (Codex #531): (1) `limit 20` trên câu đọc phiếu đòi nợ còn mở làm phiếu thứ 21 trở đi biến mất khỏi tổng công nợ và danh sách QR, vì tờ trong phiếu đã bị loại khỏi phần chưa gom: 21 phiếu 100.000 ra 2.000.000. Câu đọc dùng làm NGUỒN tính tiền không được có LIMIT; muốn gọn thì cắt ở phần hiển thị. Bộ giả phải tôn trọng LIMIT trong câu SQL, không thì không bao giờ đỏ. (2) Lần thứ năm cùng bẫy ảnh chụp: khoá hàng khách và đọc dòng phiếu có khoá để quyết định lập phiếu, nhưng phần dựng phản hồi (`no_cua_khach`) vẫn đọc thường, nên lượt bấm thứ hai báo thành công mà danh sách QR rỗng. Sau khoá, đọc hiện tại cả danh sách phiếu, nội dung phiếu và dòng phiếu (`frappe.get_doc(..., for_update=True)` đọc cả bảng con có khoá).
  Lần hai (vòng 8): `banh_si._don_cua_khach` cắt 30 đơn mới nhất TRƯỚC khi chia đơn đang mở và lịch sử, nên đơn chờ chuyển khoản cũ biến mất khỏi "Đơn sắp giao" cùng nút mở lại QR; màn Đơn sỉ web, Đơn đặt trước còn cắt theo cửa sổ ngày giao (đơn quá hạn chưa giao biến mất), nhịp khớp tiền cắt 500 đơn. Cách rà: grep mọi `limit`, `limit_page_length`, `page_length`, `[:n]`, `.slice(0, n)` trong mô đun, mỗi chỗ hỏi "phần bị cắt có phải việc đang chờ hay nguồn tính tiền, trạng thái, nút không". Có thì đọc đủ bằng một câu riêng cho phần đang mở (điều kiện lấy từ một nguồn `ung_truoc_don.dk_don_mo`, khớp hàm phân loại), chỉ cắt phần lịch sử; chỉ hiển thị thì cắt được nhưng phải nói "còn N".
- Bench #531 (v631): khai một luồng mới vào sổ đối soát (`doi_soat_sepay.khai`) với loại chứng từ KHÔNG có cột bộ sao kê (phiếu thu cọc thiết kế riêng là Payment Entry) làm `doi_chieu_app._chu_khac(bo=True)` thêm điều kiện `vgb_bo_sao_ke` lên Payment Entry, MariaDB báo "Unknown column" và cửa gắn bộ sao kê hỏng. Bộ giả không có lược đồ cột nên không thấy; chỉ bench ERPNext thật bắt được. Mọi vòng lặp qua sổ đối soát phải chỉ lọc cột bộ sao kê trên `bo_sao_ke_db.PHIEU` (như `chu_cua_giao_dich` đã làm). Khai luồng mới thì rà mọi chỗ duyệt `dss._SO`.
- Bench #531 (v631) lần hai: form thiết kế riêng và bánh sỉ tự viết phép đọc số điện thoại (`0[35789]xxxxxxxx`) trong khi phép tạo khách (`lib.sdt`) đọc theo đầu số nhà mạng. Số đầu 095 qua form, tới lúc lập phiếu thì `khach_cho_don` trả rỗng (không ném, không Error Log) và đơn báo "Chưa ghi nhận được thông tin khách" sau khi khách đã gửi. Ca bench dùng số ngẫu nhiên "09xxxxxxxx" nên đỏ lúc có lúc không. Form nào dẫn tới tạo khách phải đọc số bằng chính `lib.sdt`; ca bench dùng số cố định hợp lệ. Bench cũng phải có dữ liệu nền như site thật (nhóm "Khách lẻ", khu vực "Vietnam", món bán theo tồn kho), không thì ca mới đỏ vì đề bài chứ không vì hệ.
- Vòng 6 (Codex #531), lần thứ sáu cùng bẫy ảnh chụp: thu tiền mặt, giao bánh, huỷ đơn (thiết kế riêng) và giao hàng, huỷ đơn (sỉ) đều khoá phiếu đặt rồi gọi `tom_tat` đọc thường. Lượt thu tiền mặt chờ khoá trong lúc lượt khớp lập phiếu cọc 3.780.000 vẫn thu 7.560.000 (phiếu ngân hàng còn nháp nên lõi không chặn). Luật rà một lần cho cả mô đun: liệt kê MỌI chỗ gọi hàm khoá (`_khoa_don`, `for update`) rồi theo từng phép đọc phía sau cho tới lúc ghi; hàm tóm tắt dùng chung có tham số `khoa` và cửa quyết định truyền `khoa=True` (phiếu đặt, phiếu thu, hoá đơn, phiếu giao). Phản hồi trả SAU `commit()` thì đã là giao dịch mới, đọc thường được. Bộ giả hai kết nối phải mô phỏng cả phép đọc thường đầu yêu cầu (vai, cấu hình), không thì ca không bao giờ đỏ.
- Vòng 9 (Codex #531): lọc trước khi cộng dồn. Bộ khớp sao kê chọn dòng và cộng dồn số đã nhận TRƯỚC, rồi mới bỏ dòng ở tài khoản không được khớp (hoặc tài khoản chưa gắn sổ cái) trong vòng lập phiếu. Đơn sỉ 3.780.000 có dòng cũ đúng số ở tài khoản không được phép và dòng đúng ở tài khoản được phép: dòng sai chiếm hết phần còn thu, dòng đúng bị loại vì "thừa", dòng sai bị bỏ ở vòng lập phiếu, ra 0 phiếu (thiết kế riêng cũng vậy với dòng trả đủ 7.560.000). Luật: mọi điều kiện loại một dòng (chiều tiền, docstatus, tiền tệ, tài khoản được khớp, tài khoản sổ cái, đã đối chiếu ở nơi khác) gom vào MỘT phép lọc thuần (`ung_truoc_don.loc_dong_sao_ke`) chạy TRƯỚC phép chọn; phép chọn chỉ còn mã đơn, dòng có chủ và số tiền. Phép lọc quyết trên bản đọc trong khoá dòng sao kê, không trên ảnh chụp lúc tìm. Khi rà một vòng lặp có biến cộng dồn, mọi `continue` nằm SAU dòng cộng là lỗi.
- Vòng 10 (Codex #531), lần thứ bảy cùng bẫy ảnh chụp: bộ khớp khoá dòng sao kê rồi hỏi chủ bằng `doi_soat_sepay.chu_cua_giao_dich`, nhưng hàm đó đọc thường (`_cac_bo` không khoá, `frappe.get_all`). Phiên khác giữ BT-1 cho phiếu công nợ (bộ sao kê) trong lúc mình chờ khoá thì mình vẫn lập phiếu thu cho BT-1. Rà thêm thì thấy bộ khớp còn mù hẳn ba nguồn chủ kể cả khi không đua: hồ sơ thanh toán APP (`ma_giao_dich` ở đầu hồ sơ và ở dòng), phần đã đối chiếu (Bank Transaction Payments), và chứng từ cũ ghi MÃ THAM CHIẾU ngân hàng thay cho tên dòng. Cách rà nguồn chủ: liệt kê mọi nơi một dòng sao kê có thể bị giữ (ô trên chính dòng sao kê, mọi luồng trong `dss._SO`, phiếu nộp tiền mặt, hoá đơn bán, phiếu thu đơn đặt trước, APP, bảng đối chiếu), rồi với từng nguồn hỏi (1) đã đọc chưa, (2) đọc có khoá chưa, (3) hỏi theo cả tên dòng lẫn mã tham chiếu chưa, (4) lỗi đọc có bị nuốt không. Nay `chu_cua_giao_dich(..., khoa=True)` chỉ bộ khớp dùng: đọc có khoá mọi nguồn và ném lỗi thay vì nuốt; cửa cũ (khoa mặc định False) giữ nguyên hành vi. Ngoại lệ có chủ ý: hoá đơn bán vẫn đọc ảnh chụp vì cửa ghi của nó (`ban_hang._chiem_gd_bill`) không khoá dòng sao kê, đọc có khoá không đóng được cuộc đua mà lại khoá cả bảng hoá đơn (ô văn bản không chỉ mục). Đọc có khoá một ô không chỉ mục là khoá cả bảng trong REPEATABLE READ: trước khi thêm `for update`, xem ô đó có chỉ mục không và bảng đó nóng tới đâu.

## 03/11/2026 (v633): mã trả thẻ in trên phiếu sống lâu, cổng thanh toán chỉ dùng một lần

- Liên kết thanh toán của cổng thẻ (OnePay) gắn với MỘT mã giao dịch và một số tiền cố định; khách trả hỏng, trả một phần hay mở lại sau một tuần thì liên kết đó vô dụng hoặc đòi sai số. Phiếu đề nghị thanh toán in ra giấy sống hàng tuần, nên QR trên phiếu không được là liên kết cổng. QR trỏ về trang của tiệm (`/tra-the/<mã phiếu>?k=<khoá>`), trang đọc SỐ CÒN PHẢI TRẢ lúc khách mở và mỗi lần bấm tạo một giao dịch mới (`<mã phiếu>-<lần>`) ghi vào nhật ký phiếu. Khoá `k` là HMAC mã phiếu bằng khoá mã hoá của site, không lưu, tính lại được; thiếu khoá thì trang báo không thấy phiếu.
- Ghi tiền chỉ từ kết quả có chữ ký đúng, mã 0, giao dịch có trong nhật ký phiếu, đúng số đã gửi cổng, chưa ghi. IPN và trang về có thể tới cùng lúc hay lặp lại: khoá phiếu rồi đọc lại nhật ký, khoá chống trùng ở phiếu thu theo mã giao dịch. Trả trùng (hai giao dịch cùng thành công) chỉ ghi phần còn nợ, phần dư báo kế toán hoàn.
- Hook `chan_thieu_dinh_kem` đòi chứng từ đính kèm cho phiếu thu ngân hàng. Phiếu thu máy tự lập từ cổng thẻ không có ảnh UNC, nên phải đính biên nhận do máy dựng (tệp HTML riêng tư) TRƯỚC `submit()`, không được nới hook.
- Hàm đọc cài đặt gọi trong lúc in phiếu (`onepay.dung_duoc`) phải trả False khi đọc hỏng: lỗi đọc cài đặt của một tính năng phụ không được làm hỏng việc in phiếu đòi nợ. Ca QR474 dựng `_phieu_html` trên Frappe giả đã đỏ đúng chỗ này.
- Codex #534 vòng 1: (1) số ghi nhận phải là số phiếu thu ĐÃ GHI SỔ đọc lại từ sổ, không phải số dự kiến: hoá đơn bị trả bớt chỗ khác sau khi khách mở trang thẻ thì phép lập phiếu thu chỉ lập tới dư nợ còn lại, cộng số dự kiến vào "đã thu" làm phiếu thành "Đã thu đủ" và mất 600.000 đ tiền dư không ai hoàn. (2) Vòng quét có `limit` mà phần tử không bao giờ rời tập lọc (giao dịch "chờ" quá hạn) thì phần sau trang đầu không bao giờ được quét: phải cho hết hạn VÀ đi theo trang (khoá `name >`). (3) Mức tối thiểu của một cách trả chỉ được ẩn cách trả đó; câu "đã thanh toán đủ" chỉ dành cho số 0, không được dùng chung ngưỡng.
- Codex #534 vòng 2: cờ "chặt" (`chat=True`) của `ghi_thu_cho_phieu` vừa ném khi lập chứng từ HỎNG vừa ném khi KHÔNG CÒN GÌ ĐỂ LẬP. Với khớp tay thì cả hai đều là lỗi, nhưng với tiền thẻ đã về thật thì trường hợp sau là chuyện bình thường (hoá đơn đã được trả hết ở chỗ khác): ném ở đó làm IPN lỗi mãi, giao dịch kẹt "chờ", không ai được báo hoàn tiền. Một hàm dùng chung có hai lớp lỗi khác bản chất thì tách bằng tham số rõ nghĩa (`rong_duoc`), và ca kiểm phải chứng minh lớp kia vẫn ném.
- Codex #534 vòng 3: `kenh_zalo.bao` chỉ ghi dòng "chờ gửi" trong giao dịch HIỆN TẠI và xếp hàng sau commit. Hàm tự commit rồi mới gọi `bao` thì chỉ an toàn khi có người commit sau (yêu cầu POST); trang web GET (trang về của cổng thanh toán) không ai commit, tin bị rollback lặng lẽ, và lượt gọi lại thấy "đã ghi" nên không báo lại. Gọi `bao` TRƯỚC commit cuối của chính hàm; bắt lỗi quanh `bao` phải ném lại lỗi giao dịch chết (`loi_csdl.chet_giao_dich`), không thì commit một giao dịch đã bị MariaDB lùi và trả "thành công" cho cổng.
- Codex #534 (tự phát hiện trên CI): ca kiểm dựng trang bằng `import jinja2` đạt ở máy làm việc nhưng đỏ trên CI tay không (không có jinja2), làm bench bị huỷ hai vòng mà cổng ở máy vẫn xanh. Giả lập CI phải chặn CẢ jinja2 lẫn requests (`printf 'raise ImportError' > /tmp/chanj/jinja2.py`, `PYTHONPATH=/tmp/chanj:/tmp/chanreq`); ca cần xét khối nào của mẫu hiện thì dùng bộ dựng if/elif/else nhỏ trong ca (`thu_onepay_633._ve`), báo hỏng khi gặp thẻ lạ.

## 03/11/2026 (v636): chữ trong nút khác chữ thường dù cùng font-family

- Anh Việt gửi ảnh màn Đơn đặt trước trên Mac: chip lọc và ô đếm (đều là `<button>`) vẽ bằng nét khác hẳn chữ thường cùng độ đậm. Giả thuyết đầu "nút chưa nhận font-family" là SAI: đọc trên site thật thì Bootstrap của Frappe đã trả `font-family: inherit` cho nút. So TRỌN bộ thuộc tính chữ đã tính giữa nút và một div cạnh bên mới ra chỗ khác duy nhất: `font-variation-settings` (Frappe đặt `"opsz" 24` trên html, body; phần tử biểu mẫu không kế thừa, ở lại `normal`). Bài học: lỗi hiển thị thì đọc computed style của phần tử LỖI và phần tử ĐẸP trên site thật rồi diff toàn bộ, đừng đoán từ mã nguồn.
- Trình duyệt của Claude (Chromium) không tái hiện được nét vỡ dù cùng máy Mac; chỉ tái hiện được khác biệt computed style. Sửa ở quy tắc gốc (button, input, select, textarea nhận trọn bộ chữ, không đụng cỡ và độ đậm), bằng chứng trình duyệt thật ở `cong_cu/kiem_font_nut_636.py` (trước 1 khác biệt, sau 0). Nghiệm thu mắt thường cần anh Việt mở lại đúng trình duyệt đã chụp.

## 03/11/2026 (v635): màn báo "chưa làm X, làm X ở màn Y" mà người đọc không mở được màn Y

- Màn Quỹ tiền mặt công ty mở cho kế toán (vai ký nhận quỹ) nhưng khi quỹ chưa có mốc chỉ hiện "Đếm quỹ rồi chốt ở Cài đặt tài chính", mà Cài đặt tài chính chỉ mở cho Giám đốc và người Giám đốc chọn xem. Chị Dung đứng trước màn không bấm được gì. Câu chỉ đường sang màn khác phải kiểm cùng QUYỀN: ai thấy câu này có mở được màn kia không. Không chắc thì đặt nút làm việc đó ngay tại màn đang đứng, dùng quyền của màn này (`quy_tien_mat.chot_dau`), và để hai màn ghi qua MỘT cửa (`tai_chinh.ghi_moc`).
- Codex #536 vòng 1: mốc chốt số dư là số CUỐI ngày chốt, khoản mang ngày sau mốc mới cộng trừ. Bản đầu ghi mốc HÔM NAY khi hôm nay đã có khoản, nên chốt 5 triệu lúc 10 giờ rồi chiều ký nhận thêm 1 triệu thì app vẫn hiện 5 triệu, mãi mãi; câu dặn "nên đếm đầu ngày" không chặn được gì. Mốc có độ phân giải NGÀY thì số đếm giữa ngày phải quy về cuối hôm qua: số mốc = số đếm trừ phần vào, cộng lại phần ra đã ghi hôm nay tới lúc đếm (đọc bằng chính phép tính quỹ). Ca kiểm phải chạy phép tính quỹ THẬT trên một sổ giả theo ngày, qua đúng chuỗi sáng có khoản, đếm, chiều thêm khoản; thay phép tính quỹ bằng hàm trả số cố định thì không bao giờ đỏ.

- v634: địa chỉ tra cứu giao dịch (QueryDR) của cổng OnePay paygate là `<máy chủ cổng>/msp/api/v1/vpc/invoices/queries`, KHÔNG phải `.../Vpcdps.op` của tài liệu nội địa cũ. Bản v633 đoán theo tài liệu cũ; lệnh quét trên site thật chạy không báo lỗi vì `onepay.vn` trả trang HTML 200 và phép đọc coi là "không có giao dịch". Phép gọi dịch vụ ngoài phải phân biệt "trả lời là không" với "không hiểu câu trả lời": thiếu khoá bắt buộc (`vpc_DRExists`) thì ném kèm phản hồi đã che mật khẩu. Địa chỉ dịch vụ đoán theo tài liệu thì ghi vào VIỆC CHƯA LÀM và hỏi nhà cung cấp, đừng coi lệnh chạy xanh là đã đúng.
- Codex #535: che bí mật trong phản hồi lạ bằng một biểu thức "tới dấu phân cách" là không đủ: JSON `"vpc_Password": "a,b"` còn lộ phần sau dấu phẩy, `<input name=vpc_Password value=...>` lọt hẳn. Phải xoá NGUYÊN VĂN các giá trị bí mật đã biết (lấy từ cấu hình) ở mọi chỗ, rồi mới che theo tên ô cho trọn chuỗi trong ngoặc. Ca kiểm phải có một phản hồi chữ tự do chứa bí mật, vì chỉ lớp xoá nguyên văn bắt được dạng đó.

## 04/11/2026 (v638): link Zalo theo số điện thoại mở ra trang lỗi

- Nút "Nhắn Zalo" ở biên nhận đặt bánh trỏ `https://zalo.me/0931224334` (ô Zalo trong Settings). Số đó không cho người lạ tìm, Zalo trả "Trang này không tìm thấy hoặc không hợp lệ" ngay lúc khách vừa đặt xong và muốn hỏi thanh toán. Khối "Zalo OA" trên web đã có link OA đúng (`zalo.me/thevagabondsaigon`) nhưng nút biên nhận không đọc nó: hai nơi cùng một ý nghĩa mà hai nguồn.
- Bài học: link liên hệ ra khách phải đi qua MỘT hàm chọn (`don_web.chon_link_zalo`), ưu tiên link luôn mở được (OA), và cửa nhập ở Editor chặn dạng link biết trước là hỏng. Kiểm link liên hệ bằng cách MỞ nó thật, đừng chỉ kiểm dạng https.

## 04/11/2026 (v638): thanh toán ngay trên web, câu hứa trên màn phải là việc máy chủ làm thật

- Bước đặt bánh hứa "gửi link OnePay hoặc VietQR sau xác nhận, hiệu lực 15 phút, quá hạn tự huỷ" trong khi máy chủ không gửi gì, không huỷ gì; biên nhận ghi "chưa thu tiền". Câu cảnh báo ở màn khách là một lời hứa: đổi luồng thì đọc lại mọi câu nói về bước sau và chỉ giữ điều máy chủ thực sự làm.
- Nội dung chuyển khoản tự sinh phải là chuỗi mà bộ khớp sẵn có nhận ra (`ban_hang._sepay_theo_don`: S<shop>O<mã Pancake>T), không thì chốt ghi sổ hoá đơn Chuyển khoản chặn đơn đã trả. Đơn chưa có mã Pancake lúc khách chuyển (nội dung theo mã Don Web) thì chốt `_soat_sepay` đọc thêm số đã khớp trên bản ghi đơn web, lấy số LỚN hơn chứ không cộng (hai đường có thể cùng thấy một dòng).
- Ghi tiền đã trả lên Pancake: ô `charged_by_onepay` không bao giờ có trong dữ liệu Pancake trả về (đo 15/08/2026), ghi vào đó có thể bị bỏ qua lặng lẽ và người giao thu tiền lần hai. Ghi ô có thật (`transfer_money`, `prepaid`), ĐỌC LẠI đơn sau PUT để chắc Pancake nhận; không nhận thì tin Sales nói ghi tay.
- Tin Zalo bộ phận Bán hàng bị cấm số tiền ở cửa ghi sổ tin (`kenh_zalo.bo_dong_tien`, luật v613): soạn tin "đã thanh toán" có số tiền cho Sales thì dòng đó biến mất khi gửi. Soạn tin theo luật bộ phận ngay từ đầu, số tiền để trên bản ghi.


## 04/11/2026 (v638): hoa hồng giới thiệu, hai bẫy của ô mới trên Cài đặt và cờ miễn chặn

- Ô Check hoặc Percent mới khai bằng Custom Field trên Vagabond Settings (doctype Single) có `default` nhưng site chưa từng lưu giá trị: lần ĐẦU ai đó bấm Lưu trang Cài đặt, Frappe nạp Single từ `tabSingles` (thiếu dòng thì None), `_fix_numeric_types` ép None thành 0 rồi ghi xuống. Công tắc "mặc định bật" tự tắt, % "mặc định 2" về 0, không ai bấm gì (frappe/model/document.py, nhánh `issingle` của load_from_db). `lib.cfg_o` cũng trả "" cho cả 0 lẫn chưa lưu nên không phân biệt được. Cách phòng: sau `_dung_nhom` thì gieo giá trị mặc định cho ô CHƯA có dòng (`gioi_thieu.gieo_mac_dinh`), và đọc bằng phép đọc thô `tabSingles` khi cần phân biệt 0 với chưa lưu.
- Hàm gắn dữ liệu cho một doc rồi bật `doc.flags.<cờ>` để hook chặn sửa tay bỏ qua: cờ DÍNH trên đối tượng đó, lần lưu sau của chính đối tượng (thu ngân sửa ô) lọt qua chặn. Doc đã có trong cơ sở dữ liệu thì ghi xuống bằng `set_value` là đủ, lần lưu sau tự so khớp với `get_doc_before_save`; đừng bật cờ miễn chặn trên doc người khác còn giữ. Ca `thu_gioi_thieu_638` (đột biến M15) chốt chỗ này.

## 04/11/2026 (v638): gọi món tại bàn qua QR, bốn bẫy khi dựng

- Nhận đơn bằng `ban_hang.tao_don_tay` là đi qua một hàm TỰ COMMIT giữa chừng, nên khoá hàng `for update` của bản ghi đơn không giữ được tới lúc lập xong phiếu. Cách đúng: khoá, đọc hiện tại, đổi trạng thái sang Đã nhận rồi commit NGAY (giành đơn), sau đó mới lập phiếu; lập hỏng thì trả về Chờ nhận. Ca kiểm dựng hai luồng thật cùng bấm Nhận trên một kho giả có khoá theo luồng (`thu_goi_mon_ban_638._hai_thu_ngan`).
- Nguồn đơn mới trên hoá đơn ("QR tại bàn") mà không có trong danh sách nguồn của điểm thì màn bill quầy (`ptTheoNguon`) rơi về danh sách phương thức ĐƠN ONLINE, còn máy chủ rơi về phương thức quầy: thu ngân bấm Tiền mặt bị chặn. Nguồn mới phải được khai cả hai bên (máy chủ qua `NGUON_CU`, app qua `nguon_qr`/`pt_quay` của cấu hình bán hàng).
- Khuôn Vue có `&&` (hay bất kỳ dấu `&`) trong thuộc tính hoặc chữ thì bộ dịch khuôn gọi `decodeEntities`, cần `document`; ca node nổ "document is not defined" dù trình duyệt chạy đúng. Đưa biểu thức có `&&` vào computed. `v-model` hỏi `document.activeElement` lúc cập nhật ô, ca node cấp đúng ô đó, không dựng DOM giả.
- Bộ sinh số ngẫu nhiên giả trả cùng dãy số mỗi lần thì hai lần gửi có cùng mã lần gửi (nonce), ca kiểm "gọi thêm món là đơn mới" đỏ oan. Bộ giả phải sinh số khác nhau mỗi lần như máy thật.

## 04/11/2026 (v638, Codex và bench PR #541): bốn chỗ ca kiểm bộ nhớ không thấy

- Custom Field tạo tay trên Desk ngày trước (ở đây `Sales Invoice.vgb_so_ban`, app ghi từ v293) không có trong bench CI nếu chưa khai ở `bench_thu/nen_bench.py`. Ca bộ nhớ giả SQL nên xanh, bench ERPNext thật nổ `Unknown column` ngay bước thu ngân nhận đơn. Thêm câu SQL đọc một ô có sẵn trên site: đọc Custom Field trên site trước, rồi khai ô đó trong `nen_bench.py` cùng PR.
- `make_sales_return` chép cả mã đơn (`custom_pancake_id`) của hoá đơn gốc. Khoá "một mã đơn một hoá đơn" chặn tờ trả hàng thử. Ca bench lập tờ trả phải xoá hai ô mã đơn như ca #265.
- Số đã bán của bảng kiểm kho bỏ mọi phiếu tạm tính. Vì vậy một đơn gọi món "đã nhận" nằm trên phiếu tạm tính phải được giữ tiếp đến khi phiếu chốt. Chốt rồi thì thôi giữ, để không trừ hai lần. Bất kỳ trạng thái trung gian nào nằm ngoài phép đếm chung đều phải tự giữ chỗ.
- Hook `before_validate` của tờ MỚI không được tin ô người dùng gửi lên chỉ vì giao diện đặt ô đó chỉ đọc. Gọi API tạo Sales Invoice kèm người giới thiệu tự chọn và % 100 thì ghi sổ ra hoa hồng 100%. Tờ mới chỉ nhận giá trị máy chủ vừa đặt. Giá trị đó ghi trong sổ của lượt gọi (`frappe.flags`), giữ chính đối tượng doc. Một giao dịch ngân hàng mang mã hai đơn cũng thế: không tự cộng cho đơn nào, đưa Sales đối soát tay. Khoá dòng sao kê rồi mới đọc xem đơn khác đã dùng dòng đó chưa.
- Codex PR #541 vòng 2. Đơn gọi món tại bàn kiểm số bánh rồi mới ghi giữ. Hai bàn gửi cùng lúc thì cùng đọc "còn 2" trước khi đơn kia ghi. Đọc tồn, kiểm và ghi phải nằm trong một khoá theo điểm bán (`get_lock` của MariaDB), commit xong mới nhả. Ca kiểm dùng hai luồng thật dừng ngay sau bước đọc. Nhật ký tiền của một đơn có thể có cả chuyển khoản lẫn thẻ, nên mọi chỗ ghi ra ngoài (Pancake, phương thức hoá đơn) phải cộng theo LOẠI từng dòng, không gán một cách thu cho cả tổng.
- Codex PR #541 vòng 3: khoá hàng của MỘT đơn không tuần tự hoá được hai đơn KHÁC nhau cùng nhắm vào một phiếu chung. Ở đây là phiếu tạm tính của một bàn: hai thu ngân nhận hai đơn cùng lúc, cả hai tìm không thấy phiếu và cả hai lập phiếu. Mọi bước kiểu "tìm, chưa có thì lập" phải khoá theo khoá của thứ được lập, ở đây là điểm bán và số bàn. Lối dự phòng của khách (đơn chọn thẻ nhưng cổng tắt thì hiện VietQR) cũng phải nằm trong mọi nhịp quét.
- Codex PR #541 vòng 4: một lịch quét đọc danh sách "đang chờ" rồi đổi trạng thái từng dòng thì đè mất trạng thái mà người khác vừa ghi giữa hai bước, ở đây là thu ngân vừa nhận đơn. Đổi trạng thái theo lịch phải có điều kiện ngay trong câu UPDATE (`... where name = x and trang_thai = 'Chờ nhận'`). Bench chạy qua nửa đêm thì tờ trả hàng thử mang ngày của tờ gốc và bị ERPNext chặn. Ca bench lập chứng từ "lúc này" phải đặt thời điểm lúc này.

## 05/11/2026 (v639): hai lỗi bố cục trang bàn anh Việt chụp trên iPhone, và vì sao ca kiểm xanh

- Dải tab dính `top:64px` (mobile 68px, `cua-hang.css`) tính theo một thanh đầu trang SẼ dính, nhưng `banh.css` đặt `header{position:relative}` để nâng nội dung lên trên hoạ tiết nền, thanh đầu trang trôi đi và dải tab lơ lửng giữa màn với nội dung chui lên trên nó. Một quy tắc vị trí dính luôn đi kèm giả định về phần tử bên trên; đổi `position` của phần tử đó thì phải dò mọi `top:` đang trông vào nó. Sửa: dải tab dính ở `top:0`.
- `main` có `position:relative;z-index:2` nên là một ngữ cảnh xếp lớp riêng: bảng `position:fixed;z-index:60` nằm TRONG main vẫn thua dải tab `z-index:35` và nút nổi `z-index:45` ở ngoài. Bảng nổi, thanh giỏ phải là con trực tiếp của gốc, không nằm trong main (thành phần `GoiTaiBanNoi`). Ca node không bắt được vì bộ dựng cây tối giản không có CSS; cách bắt là chụp trang thật bằng Playwright với API giả (`scratchpad/o2o/h/chup.js`, xem PR v639), nhìn ảnh trước khi bàn giao.
- `thao-tac.css` bỏ lề của `.sheet>.wrap:first-child` (vì bảng bánh mở đầu bằng ảnh hero) và chia hai cột khi màn rộng: mọi bảng dùng lại khung `.sheet` mà không có ảnh hero đều bị mất lề. Dùng lại một khung thì đọc hết mọi quy tắc đang áp lên khung đó ở mọi tệp CSS, không chỉ tệp đang sửa.
- Codex rà PR #542 vòng 1 bắt thêm ba chỗ: (1) khối "Món đã gọi" in nguyên từng đơn kèm dòng món nối bằng join đứng TRƯỚC thực đơn, vi phạm AGENTS.md 2b.17 (khối chỉ để đọc không được lấn chỗ khối để bấm); sửa thành một dòng đếm số kèm trạng thái đơn mới nhất, bấm mới mở, đơn bị từ chối tự mở, dòng món hai món đầu rồi "và N nữa". (2) nonce của chuông sinh lúc mở bảng và giữ tới khi gửi thành công: khách gửi lỗi mạng rồi đổi lý do, máy chủ nhận cùng nonce và trả lời cũ; nonce phải gắn với NỘI DUNG, đổi nội dung thì nonce mới, thử lại cùng nội dung thì giữ. (3) trần 3 lần/10 phút đếm rồi ghi ngoài khoá: hai khách cùng bàn bấm cùng lúc cùng qua; đếm, kiểm, ghi, commit phải tuần tự theo bàn bằng khoá tên MariaDB như đơn gọi món. Ca đua giả lập hai lượt xen kẽ (`_chuong_dua`) tái hiện 4 lời trước, 3 lời sau.
- Nút cuộn tới một ô (`scrollIntoView`) dưới dải tab dính: ô chui đúng dưới dải tab (đo Playwright: ô tìm ở top 0, dải tab cao 49px). Phần tử nào là đích cuộn trên trang có dải dính thì đặt `scroll-margin-top` bằng chiều cao dải. Ca node không thấy; chỉ phép đo trên trang thật thấy.
- Lựa chọn đá, đường khai "áp mọi nhóm" (nhom_mon trống) thì chai đóng sẵn cũng bị hỏi "thay sữa yến mạch". Món đóng sẵn nhận ra theo tên (", chai", ", lon", ", hũ", "set trà", "lon 330"), còn "Chai" đứng đầu tên là trà chai, không bắt. Dữ liệu danh mục không có cờ thì phải nói rõ luật đoán trong mã và có ca kiểm từng tên.

## 05/11/2026 (v639): "chỉ ghi lời khai" của màn Xác nhận nhận hàng làm tồn kho sai mà không ai sửa

- Phương án A (v352): nhận thiếu chỉ ghi lời khai và treo việc cho thủ kho, sổ kho giữ số giao. Chạy thật: cửa hàng khai thiếu 1 Shiopan rồi tưởng xong, việc treo không ai làm, tồn kho cửa hàng dư 1 mãi. Một màn hình sinh "việc cho người khác" mà không có ai được giao rõ và không có hạn thì việc đó không bao giờ xong. Anh Việt chọn cách 1: máy tự lập phiếu điều chuyển trả phần thiếu về kho đi, báo Zalo bếp kiểm lại; bếp giữ cách lập phiếu huỷ như cũ. Phần thừa vẫn chỉ ghi lời khai.
- Codex PR #542 vòng 2 bắt thêm ở luồng này: (1) hai người cùng bấm xác nhận một phiếu trước khi lượt đầu commit thì cả hai đọc lời khai trống, cùng qua, cùng lập phiếu trả: lệch tồn hai kho. Cửa xác nhận chạy tuần tự theo phiếu bằng khoá tên MariaDB, và trong khoá đọc lại trạng thái bằng locking read (`for_update=True`) chứ không tin bản doc đã đọc trước khoá (InnoDB có thể trả ảnh chụp cũ của giao dịch); lớp hai: đã có phiếu trả thì không lập phiếu thứ hai. (2) Phiếu vừa thiếu A vừa thừa B: trả A xong mà đánh dấu cả phiếu đã xử lý thì phần thừa B biến mất khỏi Việc cần làm. Chỉ đóng việc khi không còn chênh lệch nào chưa xử lý. (3) Đổi sổ kho thật mà chỉ có ca giả `PhieuMoi.submit()` bật cờ là chưa đủ (AGENTS.md mục 6): phải có ca tích hợp trong `khung/kiem_that/` dựng phiếu thật, submit thật, đọc lại Stock Ledger Entry (`thu_tra_thieu_639.py`).
- Lập phiếu trả phải đi SAU khi lời khai đã commit và trong giao dịch riêng: trả hỏng (cửa hàng đã bán mất phần đó, vượt tồn) thì rollback phiếu trả, giữ lời khai, treo việc như cũ và nói rõ lý do trên màn. Ca `thu_xuat_kho_them._tra_phan_thieu` chạy cả ba nhánh: trả được, trả hỏng, nhận thừa.

## 05/11/2026 (v640): vẽ lại bảng gọi món tại bàn và màn Biên tập menu

- `thao-tac.css` nạp SAU `banh.css` và có luật rộng trên `.sheet>.wrap:first-child`, `.sheet .close` (fixed) và một nhóm `:is(.close,.qty button,...)` bo tròn có viền. Bảng gọi món v639 dùng lại các lớp đó nên ra khung chữ nhật bọc ba vòng tròn, chữ sát mép, nút đóng đè ảnh. Cách phòng: bảng mới dùng lớp riêng (`gb-*`) và chặn bằng `html body .sheet.gb-sheet`; đo bằng Playwright ở 320, 375, 390, 430 px (không phần tử có chữ nào cách mép dưới 16 px, dấu tick lệch tâm 0 px), không tin ảnh mắt nhìn.
- Tên lớp `.gb-dau` đã là băng đầu trang "District 1 · Bàn 5"; đặt cùng tên cho đầu bảng là ăn luật của nhau. Tìm tên lớp trong cả `banh.css` lẫn `thao-tac.css` trước khi đặt.
- Một menu cho mọi điểm là sai: NVHTN chỉ 20 m2 nên menu ít món hơn hẳn. Menu lưu theo điểm, và `menu_hien_hanh(diem)` là nguồn duy nhất cho trang bàn, cửa gọi món và màn Tính tiền. Chưa xuất bản thì dựng menu mặc định từ dữ liệu cũ để deploy xong không trang nào trống.
- DOM giả của bộ kiểm trả `innerHTML` rỗng cho thẻ dựng từ HTML của cha, nên `cu.innerHTML = moi.innerHTML` xoá trắng thanh trạng thái trong ca kiểm dù trình duyệt thật chạy đúng. Đã sửa `dom_gia.js` đọc ra từ các con như trình duyệt.
- Ca kiểm Python nạp `ban_hang` là đỏ CI (tệp đó `import requests` ở đầu, `thu_ma_vach` chặn). Logic mới cần kiểm thì đặt ở mô đun nhẹ (`bien_tap_menu.tc_theo_quay`), `ban_hang` chỉ gọi sang; ca kiểm đọc thân hàm của `ban_hang` để chốt nó không tự tính lần hai.

## 06/11/2026 (v641): đối soát tự động qua hộp thư doisoat@

- Ô "người gửi" (From) của thư ai cũng ghi giả được. Lối email cũ của đối soát vendor (v579) nhận ra đối tác chỉ bằng tên miền người gửi, nên nhận được số liệu giả. Từ v641 số liệu từ thư chỉ vào khi thư có chữ ký DKIM hợp lệ của CHÍNH tên miền đối tác (`doi_soat_thu.quyet_dinh`); chữ ký của dịch vụ gửi thư hộ không tính. Lối email cũ và tải tay đều mang nhãn "Chờ duyệt" cho tới khi giám đốc duyệt.
- Chữ ký DKIM chọn tiêu đề theo h= từ DƯỚI lên: chèn thêm một dòng From giả lên đầu thư thật thì chữ ký vẫn ĐẠT, mà phần mềm thư lại hiện From giả. Phải chặn thư có hơn một ô From (ca `thu_doi_soat_thu_641`, "hai From"). Thẻ l= (chỉ ký một phần thân thư) cũng cho nối thêm tệp vào sau: thân thư dài hơn l= thì không nhận.
- dkimpy chỉ phát hành mã nguồn, dựng gói hỏng trên setuptools mới (`install_layout`, thử 06/11/2026). Một phụ thuộc dựng hỏng là cả lần deploy Frappe Cloud hỏng ở bước Pre-build. Đã tự viết bộ kiểm hẹp (`doi_soat_dkim.py`, RSA bằng `pow` của Python, không cần thư viện) và lấy thư do dkimpy KÝ THẬT làm mẫu kiểm, để bộ ký và bộ kiểm độc lập nhau.
- Ô `nguon`, `kiem`, `khoa` của sổ tin Zalo (`Vagabond Tin Kenh`) là Data 140 ký tự. Nhét danh sách dài vào đó thì chèn dòng hỏng, tin lặng lẽ không gửi (chỉ để Error Log). Truyền mốc ngắn và để hàm điều kiện tự tính lại.
- Codex PR #544 vòng 1: (1) lượt đọc hộp thư ghi mốc UID đã đọc cả khi xử lý thư đó lỗi, nên thư lỗi bị bỏ qua vĩnh viễn mà trạng thái vẫn báo lành. Mốc chỉ vượt qua thư đã xử lý xong; lỗi thì dừng lượt, thử lại, quá 3 lần mới ghi sổ "Lỗi xử lý" kèm bản gốc rồi đi tiếp. Lượt nhận tệp commit giữa chừng nên dòng sổ thư phải có cờ "xong", không lấy "đã có dòng" làm "đã xử lý". (2) Danh sách mới (thư bị chặn, chờ duyệt, số đếm) phải lọc cùng phạm vi pháp nhân với danh sách cũ (`_cong_ty_xem`). (3) Nguồn bị từ chối vẫn còn "bản sửa chờ chọn" trong dữ liệu: mọi thao tác ghi trên nguồn phải kiểm trạng thái duyệt TRONG khoá, không trông vào chỗ chặn ở bước đối chiếu sau.
- Codex PR #544 vòng 2: (1) UIDVALIDITY đổi (hộp thư làm lại, đổi máy chủ) thì UID cũ vô nghĩa. Ghi mốc mới (UID 0) NGAY khi thấy đổi, trước khi đọc thư nào; nếu chỉ ghi khi đọc xong một thư thì thư đầu lỗi để lại cặp "validity mới, UID cũ" và lượt sau bỏ qua cả hộp thư mới. Máy chủ thư không trả nội dung một thư cũng là lỗi của thư đó, không được vượt im lặng. (2) "Không có khoá" và "chưa tra được khoá" là hai kết luận khác nhau: DNS hết giờ, SERVFAIL, mất mạng phải ném lỗi tạm (`LoiDnsTam`) để thư được đọc lại (tới 24 giờ), chỉ NXDOMAIN hoặc không có bản ghi TXT mới là chặn. (3) Trạng thái cuối do người duyệt chốt (Từ chối) phải kiểm ở MỌI lối ghi lại nguồn (tải lại, thư kênh cũ, thư không chữ ký, xem trước), đặt hàm chung `da_tu_choi_khoa` và thêm lớp chặn ở cửa ghi `_ghi_nguon`; chặn ở một nút (Dùng bản sửa) là chưa đủ.
- Thêm điều kiện bắt buộc vào một hàm mở ra ngoài (v641: `nhan` đòi lý do tải tay, `doc_tep` nhận thêm mật khẩu) thì grep cả `vagabond/khung/kiem_that/`: ca bench gọi hàm đó không đi qua bộ kiểm khung, nên bộ kiểm khung xanh mà bench đỏ (PR #544, 5 ca v579).
- Codex PR #544 vòng 3: (1) UIDVALIDITY chỉ có nghĩa trong MỘT thư mục của một máy chủ; hộp thư khác có thể trùng số. Mốc đọc phải gắn với danh tính (máy chủ thật đã dùng, cổng, tài khoản, thư mục: `danh_hop`), đổi danh tính là mốc về 0. (2) Duyệt, từ chối, xác nhận đọc trạng thái TRƯỚC khi chờ khoá đối chiếu là kết luận cũ: lượt đọc hộp thư có thể vừa nâng nguồn lên Từ thư trong lúc chờ. Mọi thao tác đổi trạng thái phải đọc lại và kiểm điều kiện TRONG khoá (`_doc_lai_trong_khoa`), ca kiểm dựng đúng thứ tự xen kẽ bằng khoá giả đổi dữ liệu lúc vào khoá.
- Codex PR #544 vòng 4: xác nhận của người (kế toán khép nguồn) phải gắn với ĐÚNG kết quả đã xác nhận, không chỉ một mốc giờ. Đối chiếu lại có thể gỡ nối (hoá đơn huỷ) rồi nối chứng từ thay mà số đếm y như cũ, nên kiểm theo số dòng không bắt được. Lưu dấu kết quả (`dau_doi_chieu`: trạng thái, tiền về, giao dịch ngân hàng, từng dòng nối chứng từ nào) lúc xác nhận; mọi lối đối chiếu lại và nối tay gọi `kiem_xac_nhan`, dấu khác thì gỡ xác nhận và ghi nhận xét để tra.
- v642 (sau deploy v641 06/11/2026): `frappe.db.has_column` trên doctype Single (Cài đặt lõi) NÉM TableMissingError trên ERPNext thật vì Single không có bảng riêng; bản Frappe giả của bộ kiểm khung trả về bình thường nên cổng xanh mà site không gieo được dòng mặc định nào (after_migrate nuốt lỗi vào Error Log). Với Single chỉ hỏi `get_meta(...).has_field`; muốn chắc doctype con đã có bảng thì `db.table_exists` trên doctype con. Ca bench nay kiểm thẳng kết quả after_migrate trên site thật dựng lại.
- v642 O2O vòng 2: phông thương hiệu Vagabond Sans không có ký tự "·". Nhãn chữ web mới có dấu này phải mang khoá tự sinh đuôi `_<9 hex>` (bộ kiểm v532 bỏ qua nhóm đó) như các nhãn "{so} món · {tien}" có sẵn; đặt khoá dễ đọc là ca phông đỏ.
- v642: combo bán tại bàn được rã thành món lúc LƯU phiếu tạm tính, mà phiếu lập lần đầu mang nguồn Tại chỗ, các lượt gọi sau thêm vào phiếu đã đổi sang nguồn QR tại bàn. Luật kênh của combo vì vậy phải qua cho cả hai nguồn (`goi_mon_ban.doc_combo_ban`), không thì trang bày combo mà lượt gọi thứ hai bị hoá đơn chặn. Bánh trong combo phải giữ trên tủ theo từng món thành phần (`sl_dang_cho`), không theo mã combo.
- v642 hoàn ứng có hoá đơn: nút nằm TRONG một dòng bấm được (dòng hoá đơn bấm là bỏ tick) phải được loại tên ra ở trình nghe của dòng, không trông vào `stopPropagation` ở trình nghe pha bắt: DOM giả của bộ kiểm hành vi không dừng trình nghe pha nổi trên cùng phần tử, ca kiểm bấm nút "Nối sao kê" làm mất tick hoá đơn. Liệt kê rõ `[data-hsphieu]`, `[data-hsgd]` trong danh sách bỏ qua của dòng.
- Codex PR #545 vòng 1: (1) danh sách tài khoản "đoán" (`ds_tk_hoan_ung` cờ `doan`, khi người được hoàn ứng chưa gắn tài khoản quỹ 141) chỉ để CHỌN tài khoản nhận tiền; đem nó làm danh sách chủ sở hữu thì khoản chi của người khác thành chứng từ cho người này. Kiểm chứng từ phải đòi tài khoản đứng tên đúng người và từ chối bản đoán. (2) Trang khách giữ các lượt gọi trong bộ nhớ trình duyệt: khi bill của bàn đã chốt, máy chủ phải báo (`da_tra`) để trang bỏ lượt cũ, không thì khách trả xong gọi tiếp thấy tổng cộng dồn cả bill đã trả.
- Codex PR #545 vòng 2: thêm một biến trạng thái mới vào màn lập phiếu (ví dụ `hsGdCua`) thì PHẢI thêm vào dòng khai bản nháp của màn đó trong `48-ban-soan-do.js` (cả `lay` lẫn `dat`, bản nháp cũ không có thì về rỗng). Quên là mở lại bản nháp rồi Lập thì mất phần đó mà không ai hay. Ca `hanh_vi/ban_soan_do_533.js` đọc, đặt biến cục bộ trong vỏ app qua `__sdKiem.chay`.
- Codex PR #545 vòng 6: quầy nhận lượt gọi tại bàn thì nhập vào phiếu tạm tính CHUNG của bàn, phiếu đó có cả món máy khác cùng bàn gọi và món thu ngân thêm. Trang khách cộng tạm tính các lượt của chính máy mình thì "Cần thanh toán" hụt. Số cần trả phải lấy từ phiếu trên máy chủ (`trang_thai` kèm `bill`: khoá băm và tổng), hai lượt cùng phiếu tính một lần; tổng của máy này chỉ được ghi đúng là "Món gọi từ máy này".
- Codex PR #545 vòng 7: (1) nhiều lượt cùng trỏ một phiếu mà nhịp hỏi tự động chỉ hỏi lượt còn chờ, thì ảnh chụp phiếu của các lượt có tuổi khác nhau; chọn "lượt đứng cuối danh sách" là lấy nhầm số cũ. Đóng số thứ tự cho mỗi lần hỏi và chọn số mới nhất. (2) Đọc phụ (tổng phiếu) lỗi thì vẫn trả DANH TÍNH (khoá phiếu) với giá trị rỗng, đừng bỏ cả mục: bỏ mục là trang tưởng lượt chưa vào phiếu và cộng trùng. (3) Nút ba nấc mới vẫn phải đủ 44 điểm cao và chữ 13 điểm (AGENTS 2b.13); máy hẹp thì cho cụm nút xuống dòng dưới tên thay vì ép nhỏ.
- Codex PR #545 vòng 8: sửa cỡ nút cho một màn thì phải rà cả PR một lượt: lọc mọi dòng THÊM trong `git diff origin/main` có `font-size` dưới 13px, `min-height` dưới 44px, và mọi phần tử bấm được (`cursor:pointer`, `<button>`, `<summary>`) không khai `min-height`. Vòng 7 chỉ sửa màn Biên tập menu nên nút "Nối sao kê" của hồ sơ hoàn ứng (11.5px, cao chừng 26px) phải thêm một vòng rà.

## 07/11/2026 (v643): gom việc tồn đọng, và ưu đãi khách tự chọn tại bàn

- Đồng bộ kiểm bánh (`kiem_banh.dong_bo`) chạy cùng lúc ở hai máy (hai quầy mở bảng kiểm, hay một nhịp lịch) thì lượt sau va `TimestampMismatchError` và ghi Error Log mỗi lần, dù dữ liệu không sai. Lỗi "bị chen" thì lùi (`rollback`), làm lại một lần trên bản mới, lần hai vẫn chen thì trả bảng đang có; không phải lỗi người cần sửa nên không vào Error Log.
- Bản tin phát hành Zalo đọc GitHub mỗi nhịp: GitHub giới hạn lượt (403/429, `Retry-After`, `X-RateLimit-Reset`) hay hết giờ thì NGHỈ tới lúc GitHub cho phép (kẹp 5 đến 60 phút) và chỉ ghi Error Log khi lỗi kéo dài quá 12 giờ. Ghi lỗi mỗi nhịp là Error Log đầy những dòng không ai làm được gì.
- Thanh đơn trang bàn chỉ hỏi lại khi còn lượt chờ, nên món máy khác gọi hay quầy thêm không đổi số. Mỗi hoá đơn còn mở chọn MỘT lượt đại diện để nhịp thưa (30 giây) hỏi lại; hoá đơn đã chốt thì thôi hỏi.
- Phần giảm không do thu ngân gõ (điểm thành viên, ưu đãi khách chọn tại bàn) phải nằm ở trường RIÊNG và mọi chỗ dựng lại `discount_amount` cộng qua MỘT hàm (`ban_hang._giam_rieng`), có ca AST chốt không còn chỗ nào tự cộng. Màn sửa bill quầy trước v643 nạp cả `discount_amount` vào ô Giảm giá, lưu lại thì máy chủ cộng phần riêng lần nữa (giảm điểm bị trừ hai lần); ô Giảm giá chỉ được là phần tay.
- Ưu đãi khách chọn trên trang bàn KHÔNG ghi lượt dùng lúc chọn: khách đổi hay bỏ thì không phải trả lượt. Lượt (tiêu mã voucher, đếm lượt chương trình) ghi lúc thu ngân chốt bill, tính lại trên giỏ cuối cùng có khoá chương trình; số đổi so với số khách đang thấy thì lưu số mới và DỪNG chốt để thu ngân báo khách. Dòng "ưu đãi hạng" mà khuyen_mai.tinh tự thêm khi biết khách không được tính vào ưu đãi khách chọn.
- Bản Frappe giả của bộ kiểm khung có `frappe.throw` luôn ném ValidationError, bỏ qua `exc=`. Ca kiểm cần bắt đúng lớp lỗi riêng (ví dụ `UuDaiDoi`) phải thay `throw` bằng bản ném đúng lớp, không thì ca không phân biệt được "dừng vì số đổi" với lỗi khác.
- Codex PR #546 vòng 1: (1) `khuyen_mai.tinh` chỉ BÁO cờ `can_otp`, không chặn; cửa nào cho khách tự áp (trang bàn, web) phải tự từ chối kết quả có `can_otp`, kể cả khi đi qua mã trong Ví quà chứ không chọn chương trình. (2) Số đã KẸP lưu trên hoá đơn (phần giảm khác gần hết bill) phải so với số đã kẹp, không với số chương trình tính ra; so lệch là chốt bill dừng mãi "đổi từ 5.000 đ thành 5.000 đ". Lượt dùng ghi theo số thật đã trừ.
- Codex PR #546 vòng 2: (1) tính lại một phần giảm phụ thuộc phần giảm khác (ưu đãi bị kẹp theo giảm tay) phải chạy SAU khi áp giảm tay mới của chính lượt gọi đó, không thì chốt bill theo giảm tay cũ (thu 180.000 đ thay vì 166.500 đ). Đặt sau cửa OTP giảm tay, trước mọi thay đổi khác. (2) Kiểm mã voucher (`khuyen_mai._tra_ma`) NÉM lỗi chứ không trả "không đủ điều kiện"; đường chốt phải bắt lỗi đó, lưu 0 kèm lý do để lần sau qua được, không thì bill kẹt mãi.
- Codex PR #546 vòng 3: `kenh_zalo.bao()` nuốt lỗi ghi và trả rỗng khi không nhóm nào nhận. Nhịp lịch nào đánh dấu "đã xong" (cache, cờ) sau khi gọi bao() phải kiểm tin đã thật nằm trong hộp thư (tên dòng trả về, hoặc dòng đã có theo khoá chống trùng); không thì để nhịp sau thử lại, đừng chặn bảy ngày.
- Hộp thư đối soát 07/11: thư GreenSM thật bị chặn "chữ ký không khớp" trong khi SpamAssassin lúc thư vào account@ ghi DKIM_VALID. Không phải bộ kiểm sai chuẩn: bộ lọc chuyển account@ sang doisoat@ gửi lại thư như thư nội bộ và gỡ ô Sender mà Mailgun đã ký. Cách khoanh: mở .eml đã cất trên trình duyệt, kiểm chữ ký bằng WebCrypto với khoá DNS thật; khối mã hoá hợp lệ (đúng khoá) thì lỗi nằm ở dữ liệu, rồi thử thêm hay bớt từng ô. Chặng chuyển tiếp của CHÍNH tiệm cũng là một chặng có thể sửa thư.
- Hạn chữ ký x= phải so với giờ máy chủ tiệm nhận thư, không phải giờ bấm đọc lại: Mailgun ký hạn 2 giờ, đọc lại sáng hôm sau là thư thật thành "hết hạn".
- ShopeeFood đổi bản CSV gửi qua email sang ghi ĐỒNG có dấu phân cách ("1,095,000") trong khi mẫu cũ ghi nghìn đồng ("140", "72,48"). 17 trên 18 dòng vẫn ra đúng số vì "160,000" đọc kiểu nghìn với dấu phẩy thập phân cũng là 160.000 đồng; chỉ đơn trên một triệu lộ ra. Đơn vị phải chọn cho CẢ TỆP theo dấu hiệu chắc chắn (hai nhóm nghìn là đồng, một hai số lẻ là nghìn, đơn dưới 1.000 hay từ 20.000 khi là số trơn), không đọc từng ô theo một giả định.
- Bộ đẩy tệp qua trình duyệt (`tao_goi.py`) đọc tệp bằng `open(..., encoding="utf-8")` nên Python đổi CRLF thành LF; mã băm tính trên bản đã đổi nên lô vẫn báo "ok" mà thư mẫu .eml lên GitHub mất CR (chữ ký số tính trên CRLF). Đọc tệp phải có `newline=""`, và đối chiếu sha1 từng tệp giữa nhánh và máy (kiem_nhanh) là lớp duy nhất bắt được.
- Codex PR #546 vòng 4: lối "lùi và trả bảng hiện có" khi đồng bộ bị chen hai lần là đúng cho nhịp nền và màn hình, nhưng SAI cho người gọi dùng kết quả để chốt sổ (chốt ngày kiểm bánh chuyển tồn sang mai trên số bán cũ). Lối mềm phải có cờ để người chốt nhận lỗi rõ ràng và dừng.
- Đọc lại thư ĐÃ xác thực sau nhiều ngày (để đọc lại tệp khi sửa mẫu): đối tác có thể đã đổi khoá DKIM, kiểm lại không đạt. Không được hạ thư thật thành "Bị chặn" hay báo thư giả; dừng trước mọi lần ghi và giữ kết quả cũ.
- Bench PR #546: cửa cho khách (Guest) lưu Hoá đơn bán dù có `ignore_permissions=True` vẫn hỏng, vì `set_missing_values` của ERPNext gọi `get_party_account` rồi `account_perm_check` theo NGƯỜI ĐANG ĐĂNG NHẬP ("User don't have permissions to select/read this account"). Bản Frappe giả không có lớp này nên khung xanh. Bước lưu phải chạy bằng quyền hệ thống trong khối trả lại đúng người gọi (cùng cách `thu_tien.nang_quyen_lap_phieu`), sau khi đã kiểm link, phiên và khoá.
- Luật định tuyến web (`website_route_rules`) chỉ được Frappe áp khi có request web (`evaluate_dynamic_routes` đọc `frappe.local.request.environ`). Ca bench chạy từ dòng lệnh phải tự dựng request (`werkzeug EnvironBuilder`) rồi gọi `frappe.website.serve.get_response`, không thì `resolve_path` trả nguyên đường dẫn và ca đỏ oan.
- Sau deploy v643 (07/11/2026), nút Đọc lại thư gốc trên site thật hỏng "Column 'tong_tep' cannot be null". Ghi mới bằng `insert()` thì Frappe tự đổi None thành 0 cho ô số; ghi lại bằng `db_set` / `frappe.db.set_value` là câu UPDATE thẳng nên None chạm cột số NOT NULL của MariaDB. Lỗi nằm từ v583 trên mọi mẫu không in dòng tổng, chỉ lộ khi có người đọc lại. Bản Frappe giả nhận None im lặng; ca khung phải soi chính dict `db_set` nhận theo kiểu ô trong JSON doctype, và bench phải chạy lối ghi lại trên cơ sở dữ liệu thật. Mọi lối ghi lại cả bản ghi bằng `db_set` đi qua `so_khong_rong`.
- Anh Việt 07/11/2026 (v644): trang bánh trên iPhone (1) ảnh lớn lệch trái 20px, hở dải đen bên phải: `thao-tac.css` đặt khung ảnh `width:100%` trên điện thoại mà `banh.css` cũ còn `margin:0 -20px`; hai luật cùng đúng riêng lẻ, chồng lên nhau thì lệch. Ca DOM phải ĐO khung (getBoundingClientRect ở 390 và 800 px), nhìn mã CSS không thấy. (2) Very Berry 4 ảnh giống nhau: ảnh web ghép từ hồ sơ món TỪNG SIZE (người tải cùng một tấm cho mỗi size, Frappe đổi tên tệp) cộng Pancake, và chỉ loại trùng theo đường dẫn. Ảnh của một bánh phải gắn theo BÁNH (khoá tên không size) ở một nơi (thẻ Bánh, banh_web.py), chống trùng theo nội dung ảnh (dHash), không theo tên tệp.
- Ẩn sản phẩm theo một bảng mới thì phải có đường "bảng chưa dùng": trước lần gieo đầu (việc nền sau migrate) bảng rỗng, nếu coi rỗng là "không bánh nào được hiện" thì web trắng trơn tới khi việc nền chạy xong. so_ghi() trả None khi bảng rỗng và web chạy đường cũ.
- Codex PR #547 (07/11/2026) bắt ba lỗ của chính đường "bảng chưa dùng" trên: (1) lấy "bảng có thẻ" làm dấu đã gieo thì một người bấm Đưa lên web trước lúc việc nền chạy là đủ làm việc gieo bỏ qua và web ẩn mọi bánh khác, migrate sau cũng không tự hồi phục: dấu đã gieo phải là một giá trị riêng chỉ đặt khi gieo xong. (2) Đọc bảng lỗi mà trả đúng giá trị "chưa dùng" thì đường cũ hiện lại bánh Marketing đã ẩn: lỗi đọc phải ra "không bánh nào", không ra đường cũ. (3) Máy chủ lọc hết thành danh sách rỗng mà trang khách coi rỗng là "chưa có dữ liệu" rồi đưa danh mục mặc định ra: máy chủ phải báo rõ đang lọc (chi_hien), trang phân biệt "đã tải, rỗng" với "chưa tải".

## 08/11/2026 (v645): đơn web trả thẻ OnePay về Pancake thành Tiền mặt, và ưu đãi đơn web đầu tiên

- Anh Việt 08/11: đơn web khách trả thẻ OnePay (Pancake 97077, 97098, 97113) mang hình thức Tiền mặt. Lịch sử đơn Pancake cho thấy lệnh ghi CHỈ ô `prepaid` của khoá API làm Pancake tự điền `cash` bằng đúng số đó. Đơn khách trả bằng link của chính Pancake thì lịch sử ghi `charged_by_onepay` CÙNG `prepaid`, `cash` giữ 0. Ghi một ô số tiền lên Pancake phải đối chiếu với một đơn mẫu do chính Pancake tạo đúng hình thức, không suy từ tên ô. Pancake không trả `charged_by_onepay` khi đọc lại đơn, nên phép kiểm sau khi ghi đọc `cash`: còn tiền mặt thì báo Sales đổi tay, COD vẫn đúng.
- Cùng sự cố, hoá đơn ERP đồng bộ ra "Tiền mặt": phép đoán hình thức thanh toán từ đơn Pancake có kết quả nên KHÔNG hỏi bản ghi đơn web (chỉ hỏi khi đoán rỗng). Nguồn chắc chắn hơn (đơn web đã ghi nhận thu online) phải được hỏi TRƯỚC và thắng phép đoán, không chỉ làm lối dự phòng.
- Thêm một hàm vào `tao_don` thì mọi ca kiểm dựng `tao_don` bằng `nap()` (thu_don_web_367 `_moi_truong_tao_don`) phải có tên mới trong từ điển toàn cục, không thì hàng chục ca cũ đổ NameError. Ưu đãi mới mặc định "không áp" trong môi trường giả để ca cũ giữ nguyên nghĩa.
- Codex PR #548 (08/11): dựng mục Ưu đãi theo khuôn Tuyển dụng nhưng chỉ chép nhánh "đang tải", quên nhánh `ND.loiTai` (bài học 31/10 ở trên), nên link chi tiết kẹt "Đang tải ưu đãi..." khi nội dung lỗi 503, còn danh sách báo "chưa có ưu đãi" trong lúc chờ. Mục mới đọc nội dung web phải có đủ ba trạng thái đang tải, tải lỗi, đã tải, và ca kiểm chạy `napNoiDung` thật với phản hồi lỗi.
- Codex PR #548 (08/11), hai vòng về cùng một ô cài đặt: (1) `lib.cfg_o` nuốt lỗi đọc và trả chuỗi rỗng, nên "đọc lỗi" thành "chưa lưu" rồi chạy theo mặc định ĐANG BẬT; ô cần phân biệt hai trường hợp phải đọc thẳng `tabSingles` để lỗi nổi lên. (2) Sửa xong, đường tính tiền đúng là coi lỗi như tắt, nhưng cửa đọc cho màn quản lý dùng lại hàm đó nên trả cấu hình dự phòng như thể đã lưu: màn hiện "Đang tắt" sai, bấm bật là ghi đè mức giảm thật. Giá trị dự phòng an toàn cho đường chạy KHÔNG được trả cho cửa đọc mà người dùng sẽ sửa rồi lưu lại; cửa đó phải báo lỗi để màn hiện thẻ Thử lại.
- Anh Việt 08/11 (v645 đợt 4): tin "cảm ơn sau mua" chạy theo lúc CỘNG ĐIỂM, tức hoá đơn ghi sổ. Bill quầy thì đúng, nhưng đơn giao ghi sổ cuối ngày nên khách nhận bánh buổi trưa mà sáng hôm sau mới có tin. "Sau mua" phải là lúc khách nhận: đồng bộ Pancake chỉ dựng hoá đơn nháp khi đơn đã Đã nhận, nên hoá đơn nháp có mã Pancake chính là mốc đó. Điểm của đơn chưa ghi sổ thì tính bằng đúng phép của hook cộng điểm (khach_hang.diem_cua_don), và tổng điểm trong tin phải cộng trước phần đó.
- Cùng ngày: sổ tay của trợ lý đứng ở v631 trong khi app đã lên v644, vì không cổng kiểm nào nhắc (mọi cổng chỉ soi mã). Việc "phải làm mỗi lần phát hành" mà chỉ nằm trong lời dặn thì sẽ bị quên: biến nó thành ca kiểm đọc APPVER (`thu_so_tay_phien_ban_645` với sổ đối chiếu `vagabond/so_tay/_phien-ban.md`).
- Codex PR #548 (08/11, b4b18d5), ba finding đều nằm trong câu SQL: đổi mốc "sau mua" từ dòng tích điểm sang `si.creation` làm rơi bill quầy lưu nháp rồi ghi sổ muộn; quà giới thiệu không kiểm người mua là khách mới; báo cáo "Hiệu quả 30 ngày" lấy cả nhóm mới nhận tin 7 ngày. Bộ kiểm cũ thay `frappe.db.sql` bằng dữ liệu dựng sẵn nên câu sai vẫn xanh. Việc làm: đổi mốc thời gian hay điều kiện trong câu SQL thì chạy CÂU THẬT trên sqlite (khuôn `thu_zalo_645_sql.Kho`, dịch `%(x)s`, bộ giá trị `in`, `concat`, `date_add`), dựng đúng chuỗi thao tác (nháp tạo trước lúc bật, ghi sổ sau). Khi đổi mốc, liệt kê mọi đường dữ liệu đi vào mốc cũ (ở đây: hook cộng điểm lúc ghi sổ) và giữ lại đường nào mốc mới không phủ.
- Bếp Pastry báo 09/11 (v646): "Đếm hôm nay" chia đúng 10 món giống nhau năm sáng liền (KK-26-00072 tới KK-26-00080). Bếp đếm và chốt đều, phiếu sang "Chờ duyệt" rồi nằm chờ quản lý ghi sổ; lịch xoay vòng chỉ coi "Đã chốt", "Đã ghi sổ" là đã đếm, nên món vừa cân lại thành "chưa đếm bao giờ" và lên đầu. Bài học: trạng thái chờ người khác duyệt là việc của BƯỚC SAU, không được xoá công việc của bước trước. Khi thêm một trạng thái trung gian vào luồng (ở đây v628 thêm "Chờ duyệt"), grep mọi câu lọc theo danh sách trạng thái (`trang_thai in (...)`) và quyết từng chỗ trạng thái mới thuộc phía nào; gom danh sách thành một hằng (`kiem_ke.TRANG_THAI_DA_DEM`).
- Cùng ngày (v646 Cài đặt tự động hoá), đột biến gỡ cổng "tắt việc thì nhịp 0h không lập kế hoạch" mà ca vẫn xanh. Ca dựng pha BẬT với `set_user`, `logger` giả đủ, còn pha TẮT thì không; pha tắt ném lỗi ở `set_user` ngay trước lời gọi `lap`, khối `try` nuốt lỗi, nên `lap` không được gọi dù cổng đã bị gỡ. Ca so sánh bật/tắt phải dựng CÙNG một môi trường cho cả hai pha, chỉ khác đúng công tắc; pha "không làm gì" mà môi trường thiếu thì chứng minh được nhầm. Cũng vậy với nhịp có `try/except`: ca phải chứng minh lời gọi bên trong thật sự tới được (pha bật có kết quả), không chỉ chứng minh pha tắt im lặng.
- Minh Vũ báo 09/11 (v646): gửi thử tin "Cảm ơn khi khách nhận đơn" bị Zalo từ chối "tong_tien has invalid format (mã -1124)", trong ngày 20 khách không nhận tin mà không ai được báo. Ô tiền của mẫu đã duyệt có kiểu CURRENCY, máy chỉ đổi số trơn cho NUMBER nên gửi "450.000đ". Bộ kiểm cũ tự đặt kiểu tham số (tong_tien NUMBER, ngay_mua STRING) khác mẫu thật nên xanh. Bài học: dữ liệu giả cho một hệ ngoài (mẫu Zalo, đơn Pancake) phải CHÉP NGUYÊN VĂN từ bản ghi thật trên site (ở đây ô "Tham số mẫu" máy đã đọc từ Zalo), không tự soạn theo trí nhớ. Lỗi dữ liệu không khớp mẫu (-1121, -1122, -1124) là lỗi của máy, khách nào cũng hỏng y hệt: phải dừng lượt, để tin chờ và báo người, không loại từng khách như lỗi của riêng khách.
- Bếp báo 09/11 (v646, Roman De La Rose 18): bánh đặt xa ngày lọt hẳn khỏi bảng kiểm bánh, và cửa nhận đơn web cho qua MỌI ngày nhận quá 3 ngày tới (`ton_don_web.kiem` trả rỗng) vì nguồn tồn duy nhất là Đủ decor cho 3 ngày. Một nguồn tồn có phạm vi ngày thì cửa nhận đơn phải nói rõ ngoài phạm vi là "không kiểm" hay "không nhận", không để rỗng ngầm hiểu là cho qua. Refill thêm nguồn thứ hai có khoảng ngày riêng; đơn trong khoảng refill KHÔNG được trừ thêm vào Đủ decor (bốn chỗ cùng tự trừ decor: `btp`, `kiem_banh._dat_truoc_theo_decor`, `ton_don_web`, `giu_ton_web`, đều gọi chung `refill.ngay_cua_refill`). Đếm đơn từ Pancake lỗi thì refill phải hiện "chưa đếm được" và ẩn trên web, không coi là 0 đơn.
- Codex PR #549 (09/11, 43956a7), bốn góp ý cho đợt "việc máy soạn sẵn": (1) dọn nháp yêu cầu mua máy soạn lọc theo `owner = Administrator` và `modified_by = Administrator`, khớp luôn phiếu tay của quản trị và phiếu sản xuất, chuyển kho của luồng khác, nên bật việc là xoá nhầm chứng từ thật (tái hiện: 4 phiếu bị xoá, đúng ra 1). Chứng từ máy tạo mà máy sẽ đếm, nhắc hay xoá phải mang DẤU riêng (`vgb_may_soan`) và mọi chỗ lọc qua một hàm (`loc_may_soan`), không suy từ người tạo. (2) Việc mời "sửa số rồi bấm Gửi duyệt" nhưng màn mở ra chỉ đọc, nút gửi nguyên phiếu máy: lời mời trên việc phải được một ca chạy thật đi đúng chuỗi đó. (3) Ô nhà cung cấp là ô gõ mã (vi phạm QT-31). (4) Màn lập chứng từ mới đứng sau phần 48 vẫn phải khai bản nháp; trạng thái mà số máy điền sẵn có thể đổi giữa hai lần mở thì chỉ lưu phần người đã sửa (`khongO`), không điền lại cả ô cũ đè lên số mới.
- Codex PR #549 (09/11, 1eefda8), năm góp ý cho Refill và Gom yêu cầu mua: (1) số còn của một mẻ có khoảng ngày phải đếm đơn từ NGÀY ĐẦU MẺ, không từ hôm nay; đếm từ hôm nay là mở bán lại mẻ đã hết khi sang ngày. (2) Kiểm số còn bằng một lần đếm từ hệ ngoài (Pancake) ngoài transaction thì hai khách cùng lấy suất cuối đều qua: phải kiểm và giữ suất trong CÙNG transaction tạo đơn, sau khoá tuần tự hoá, và trừ suất các đơn web chưa có trong lần đếm (đối chiếu theo mã đơn của CHÍNH lần đếm đó, không theo trạng thái). (3) Một mã có hai nguồn số (decor và refill) thì giới hạn phải chọn theo ngày nhận khách đang chọn, không gộp thành một số. (4) Ràng buộc của nguồn tương lai không được áp lên dòng giỏ lấy từ nguồn hôm nay. (5) Chốt xong một nhóm thì xoá số đã sửa của món đó cả trong bộ nhớ lẫn bản nháp, không thì phiếu xin mới của cùng món mang số cũ.
- Codex PR #549 (58ba797), hai góp ý tiếp: (1) hàm "đang giữ chỗ" (phiếu đặt chưa giao) KHÔNG dùng được để đo phần đã tiêu thụ của một mẻ: giao xong là số giữ chỗ về 0 và mẻ lại "còn đủ". Đo tiêu thụ phải đọc cả phiếu đã giao và đã đóng trong khoảng ngày (phiếu mở tính đủ số đặt, phiếu đóng tính phần đã giao). (2) Sửa ràng buộc ngày cho dòng giỏ hôm nay mà quên ràng buộc SỐ LƯỢNG cùng nguồn: mỗi giới hạn theo nguồn phải nhận nguồn của dòng giỏ, không đoán theo mã.
- Codex PR #549 (4204048): (1) ô bắt buộc nhập mà có nút đổi đơn vị hay nút cộng trừ thì MỌI nút đó phải giữ ô TRỐNG khi đang trống (vòng sau Codex bắt thêm nút trừ: `Math.max(0, v('') - 1)` cũng ra 0); rà hết các nút chạm vào ô, không chỉ nút được báo; quy đổi `parseFloat('') || 0` biến trống thành 0 là lách được luật bắt buộc nhập (máy chủ còn thay 0 bằng số theo lệnh). (2) Màn danh sách mới (Gom yêu cầu mua) quên ô tìm nhanh của AGENTS.md 2b.5: khi thêm màn danh sách, rà đủ bảy điều của mục 2b trước khi bàn giao.
- Đối soát chuyển khoản thiếu điểm Sales Online (chị Dung báo 09/11/2026, v646): màn lọc bill "có quầy" và chỉ vẽ chip cho điểm có bill, mà điểm Sales Online để TRỐNG ô quầy theo quy ước cũ (`diem_ban.ma_theo_quay`: quầy rỗng là Sales). Cả điểm biến mất, khoản khách Sales chuyển không theo mã QR không có chỗ khớp. Luật: màn chia theo điểm bán lấy DANH MỤC từ `diem_ban.ds()` (mọi điểm đang bật luôn có chip, số 0 vẫn hiện), không suy danh mục từ dữ liệu trong ngày; không lọc theo `vgb_quay` khi muốn "mọi điểm"; bill không đoán được điểm thì hiện ở chip Chưa rõ điểm chứ không bỏ.
- Banner trang đặt bánh (v647, anh Việt 10/11/2026): "Đặt xong" KHÔNG phải trạng thái giỏ hàng. Gửi đơn thành công là trang chuyển sang biên nhận riêng /banh/xong/<token> (www/web_moi/xong.py + web_vue/trang/app.js); khối đặt trong giỏ với điều kiện S.guiXong chỉ hiện ở lối hiếm không có đường biên nhận. Nội dung muốn khách thấy sau khi đặt phải đưa qua get_context của biên nhận. Mục theo thẻ ở trình biên tập mặc định bị ép vi_tri = loai (ap_muc); loại nào cần vị trí thật (banner) phải miễn ép và kiểm vị trí riêng. Biên nhận gỡ token khỏi đường dẫn ngay lần mở đầu, nên lần tải lại vào nhánh không token và khôi phục từ phiên: dữ liệu công khai (banner) phải gửi cả khi không token, đừng lấy token làm điều kiện (Codex PR #550).
- Đối soát ShopeeFood báo "Lệch tiền về" sai (bot Zalo 08:33 ngày 10/11/2026, v647): báo cáo 09/11 báo chuyển 1.613.010 nhưng máy so với 2.771.246, là tiền của báo cáo 08/11 về ngân hàng ngày 09/11. Tiền của 09/11 về trưa 10/11, mà máy chỉ dò lúc đọc báo cáo nên nguồn còn kẹt. Luật: chưa có tiền ĐÚNG KỲ thì là CHỜ, không phải lệch. Nguồn ghi ngày kỳ trong nội dung chuyển khoản (ShopeeFood "thanh toan tu dong DD MM YYYY") chỉ so với giao dịch mang đúng ngày đó, giao dịch kỳ khác không là ứng viên kể cả trùng số; nguồn không ghi ngày chỉ báo lệch khi có đúng MỘT ứng viên. Tiền về muộn là chuyện thường của đối tác: trạng thái "chờ" nào cũng phải có lượt dò lại định kỳ (doi_soat_vendor.do_lai_tien_ve mỗi giờ), không chỉ dò một lần lúc nhận tệp. Tin cảnh báo khoá theo nguồn, không theo con số, để lượt dò lại không gửi lặp. Cùng ngày anh Việt yêu cầu áp nguyên lý cho mọi nguồn: "đúng kỳ" là DẤU trong nội dung chuyển khoản, mỗi đối tác một kiểu (Payoo khoảng ngày "ngay 02.10 04.10.2026", OnePay mã đợt trả PVS do chính thông báo tạm ứng in ra và khung giờ kỳ có thể bị cắt, GrabFood tên cửa hàng); khoảng ngày của nội dung và kỳ báo cáo phải LỒNG NHAU (kỳ OnePay 17h hôm trước tới 17h hôm sau dài hơn kỳ báo cáo tính theo ngày giao dịch), không so bằng nhau. Khi chưa đọc được sao kê thật trên site, lấy mẫu từ đặc tả nguồn đã khảo sát (docs/doi-soat-vendor/schema) và chú thích mẫu sao kê trong mã, đừng đoán.
- Codex PR #550 (c0c114ef5): ô "Tự nhập" khổ standee chỉ kiểm khoảng 40..200 x 40..287 mm, nên 200 x 40 lọt qua và bố cục tính cạnh mã QR -95,94: miếng in không có mã quét được. Kiểm khoảng của từng ô không đủ khi kết quả là thứ được TÍNH từ cả hai ô (tỉ lệ, diện tích còn lại). Cửa nhập phải kiểm chính đại lượng cuối cùng (ở đây cạnh mã QR in ra từ 20 mm) bằng CÙNG hàm bố cục mà bản vẽ dùng (gmbBoCucVuong, gmbCanhQrMm), báo người dùng con số cần sửa; ca kiểm quét lưới mọi khổ được cho qua và đo trên SVG vẽ thật.
- Đối soát chỉ một chiều là chưa triệt để (anh Việt 10/11/2026, v647): máy đã nối từng dòng báo cáo đối tác với bill (chiều xuôi), nhưng bill thu ngân bấm Shinhan POS kèm mã chuẩn chi mà đối tác không có giao dịch thì không ai thấy, vì không có dòng đối tác nào đi tìm nó. Mỗi đối soát phải chạy CẢ HAI CHIỀU trên cùng một tập: chiều ngược (bill_doi_tac, du_lieu_bill) dùng đúng tập ứng viên của chiều xuôi (_ung_vien_hd) và kết quả nối của nó làm căn cứ duy nhất, không dò lại riêng. "Không có" chỉ kết luận khi báo cáo của ngày đó (và ngày sau, với thẻ có thể vào lô hôm sau) đã về; chưa về là Chờ báo cáo, không báo động giả.
- Codex PR #550 (4f0894ab21, a6af8eabd4), bốn góp ý cho chiều ngược "Bill chưa khớp đối tác": "báo cáo đã về chưa" phải xét đúng PHẠM VI của bill, cả pháp nhân lẫn cửa hàng đối tác. Phạm vi lấy từ DANH MỤC (danh sách pháp nhân, bảng ánh xạ cửa hàng `doi_soat_mau.GRAB_DIEM`, `SHOPEE_DIEM`, `GREENSM_DIEM` qua `doi_soat_vendor.diem_doi_tac`), không suy từ những báo cáo tình cờ đã nhận trong khoảng ngày: chỉ có báo cáo GrabFood của SALES thì bill TCV phải là Chờ báo cáo, không phải Không có. Cùng lần: "Chờ kế toán chọn" chỉ cho bill thật sự là ứng viên của dòng mơ hồ (cùng phép so `la_ung_vien` của chiều xuôi), và màn danh sách có trần dòng thì phải có phân trang, ô tìm, chip kỳ để mở được dòng cuối.
- Codex PR #550 (4704bb902d): nguồn đối soát có thể KHÔNG có dòng riêng (tệp gửi lại toàn giao dịch đã nhận chỉ ghi quan hệ ở bảng Trùng). Suy phạm vi cửa hàng từ dòng của chính nguồn thì nguồn đó rỗng, và nhánh dự phòng "rỗng là phủ mọi cửa hàng" biến tệp SALES gửi lại thành báo cáo của cả TCV. Luật: phạm vi đọc qua bảng Trùng về giao dịch gốc; kênh có cửa hàng riêng mà vẫn chưa rõ phạm vi thì nguồn không phủ cửa hàng nào (bill chờ), không bao giờ mặc định phủ hết. Hai lớp này che nhau, nên mỗi lớp có ca riêng và có đột biến gỡ cả hai cùng lúc. Phạm vi qua bảng Trùng phải HỢP cho mọi nguồn, kể cả nguồn có dòng riêng: một tệp ShopeeFood có thể gộp nhiều cửa hàng, dòng mới của SALES và dòng trùng của TCV (Codex cc38b234b5).
- Codex PR #550 (4331d0a91a): lượt nền mới (dò lại tiền về mỗi giờ) gọi đúng hàm ghi của luồng cũ (`_tien_ve`) nhưng quên khoá mà mọi lối ghi cũ đều giữ (`khoa_doi_chieu`), nên chạy cùng lượt nhận tệp thì hai nguồn cùng nhận một giao dịch ngân hàng. Thêm một lối gọi vào hàm ghi dùng chung thì rà xem lối cũ giữ khoá, giao dịch, điểm lưu gì và giữ y như vậy; đọc lại bản ghi SAU khi có khoá (khoá commit để mở ảnh dữ liệu mới) và bỏ qua nếu trạng thái đã đổi trong lúc chờ. Ca kiểm chạy HAI LUỒNG thật với khoá thật (threading.Lock thay get_lock), cộng một ca AST chốt "mọi nơi gọi _tien_ve đều trong khoá".
- PR #550 (10/11/2026): đổi kiểu ô "bàn" từ Int sang Data (tên bàn theo khu) làm một ca bench `kiem_that/thu_goi_mon_ban_638` đỏ (mong 87, nhận "87"), và bench đỏ suốt tám lượt đẩy mà các comment bàn giao chỉ ghi bốn cổng máy local. Bộ `kiem_that` chỉ chạy trên bench CI, cổng local không chạm tới. Luật: đổi kiểu một trường thì grep cả `vagabond/khung/kiem_that/` và `bench_thu/`; trước khi ghi "cổng kiểm đạt" hay merge, đọc kết luận job bench của ĐÚNG SHA cuối (log thô: /commit/<sha>/checks/<job>/logs, tìm dòng "Lượt 1:" và ca có "dat": 0).
- v648 (11/11/2026): bill sàn bị báo "Lệch tiền" sai 856 trên 860 dòng vì phép so tiền chỉ biết một cách ghi bill (giá menu), trong khi thu ngân đã chuyển sang ghi khuyến mại, rồi ghi thực nhận lên bill. Khi một số liệu bên ngoài (cách thu ngân ghi bill, mẫu tệp đối tác) có thể thay đổi, đo trên site thật TRƯỚC khi viết luật so: gom các dòng lệch theo "khớp được bằng cách nào" (tổng trước giảm, sau giảm, tiền hàng, thực nhận) rồi mới chọn luật; giữ MỘT hàm so tiền (`doi_soat_khop.cung_tien`) cho mọi chỗ, kể cả màn chiều ngược.
- Codex PR #551 (231aeef5bd), hai góp ý: (1) thêm một con số vào phép so (thực nhận) mà một câu truy vấn chiều ngược (dòng "Nhiều chứng từ" chờ chọn) không lấy cột đó, nên bill ShopeeFood chỉ khớp theo thực nhận thành "Không có trên báo cáo". Kho giả của ca cũ trả nguyên dòng bất kể `fields` nên không thấy. Luật: dòng dữ liệu dùng cho phép so đi qua MỘT hàm chiếu (`doi_soat_vendor._tien_dong`, thiếu trường là lỗi, không âm thầm thành 0), và kho giả của ca kiểm chỉ trả đúng các cột được hỏi. (2) Lệnh con tự làm (cấp 1, cấp 2) phải có ca tích hợp thật trên Work Order, Stock Entry, SLE, GL (`kiem_that/thu_tu_lam_cap_duoi_648`). Viết ca đó lộ thêm một lỗ: lệnh con ghi sổ bằng giờ điện thoại còn món chính bằng giờ máy chủ, điện thoại nhanh vài giây là phiếu món chính đứng trước phiếu nhập bánh khuôn. Mọi phiếu hoàn tất lệnh, kể cả lệnh con máy tự làm, đi một cửa `kho_san_xuat.hoan_tat_phieu`.
- Codex PR #551, lượt bench 37c4961: `mon_tu_lam` hỏi thẳng cột `custom_lam_tuoi` (ô tự thêm trên site, bench không có) nên ca tích hợp nổ "Unknown column", trong khi ca tầng một xanh vì kho giả trả đủ mọi thuộc tính và `has_field` luôn đúng. Ô tự thêm nào cũng phải hỏi `meta.has_field` trước khi đưa vào `fields`, và kho giả của ca kiểm phải có một ca "site thiếu ô" ném đúng lỗi MariaDB.
- v648 (anh Việt xem bản vẽ 11/11/2026): hộp xác nhận "Máy làm luôn giúp bếp" đọc một cấp công thức nên ruột bánh cấp 1 thiếu tồn hiện chip ĐỎ "thiếu" kèm câu "báo thiếu", trong khi máy sẽ tự làm nốt. Khi một tính năng tự động hoá một bước, mọi màn đang báo "thiếu" cho bước đó phải đổi theo (một hàm `mfgChipNvl` quyết chữ và màu). Vẽ bản minh hoạ theo đúng số liệu ví dụ là cách nhanh nhất để thấy loại lệch này.
- Codex PR #551 vòng 3 (`7476bd53be`): món chính cần cả ruột C1 lẫn bánh khuôn C2, mà C2 cũng ăn C1. Máy làm C1 cho món chính, rồi lệnh C2 thấy số C1 đó là "có tồn" và ăn hết, món chính báo thiếu sau khi hai lệnh con đã ghi sổ. Ca hành vi xanh vì kho giả chỉ CỘNG thành phẩm khi ghi sổ lệnh con, không TRỪ nguyên liệu. Kho giả cho chuỗi sản xuất phải trừ nguyên liệu như ERPNext, và khi lập kế hoạch nhiều cấp phải giữ phần tồn của lệnh cấp trên (`mfgGiuCuaLenh`).
- Codex PR #551 vòng 5 (`24e6375e96`): việc tự động có hậu quả (máy lấy nguyên liệu từ Kho tổng 307) được bật theo "có kế hoạch máy làm", trong khi chế độ hoàn tất theo lô bỏ qua đúng cái hộp xin bếp đồng ý. Cờ đồng ý phải gắn với việc hộp đó THẬT SỰ hiện và được bấm, không suy ra từ dữ liệu. Cùng vòng: hộp hỏi nối cả danh sách nguyên liệu bằng join đẩy nút xác nhận ra khỏi màn; câu hỏi luôn là đếm số, vài mục đầu, "và N nữa" (AGENTS.md mục 17).
- Codex PR #551 vòng 6 (`19b56c0b22`): bếp bấm đồng ý ở hộp "Máy làm luôn giúp bếp" là đồng ý ĐÚNG những gì hộp đó hiện (lệnh con và phần lấy kho tổng của lệnh con), nhưng app coi đó là đồng ý lấy bù cho cả món chính, mà hộp không hề xét nguyên liệu của món chính. Một lần đồng ý chỉ phủ đúng nội dung đã hiện; việc có hậu quả mà hộp chưa nêu (ở đây phiếu điều chuyển của món chính) phải hỏi riêng. Ca hành vi dựng đúng ca biên: lệnh con đủ nguyên liệu, món chính thiếu một nguyên liệu khác.
- Codex PR #551 vòng 7 (`b251b4547c`): sửa riêng từng đường (món chính, rồi lệnh con lồng nhau) là đuổi theo triệu chứng. Gốc là cờ đồng ý dạng có/không. Đổi thành SỐ ĐÃ DUYỆT theo từng nguyên liệu (`bu.duyet`, lấy đúng từ phần "lấy kho tổng" hộp đã hiện), mọi lệnh ghi sổ qua một cửa (`mfgGhiLenh`): máy chủ hỏi trước, phần thiếu nằm trong số đã duyệt thì lấy và trừ dần, vượt thì hỏi riêng. Hộp xác nhận cũng phải cộng nguyên liệu của phần máy làm thêm (đọc công thức lồng nhau như lúc chạy), không thì số duyệt luôn nhỏ hơn số máy cần.
- Codex PR #551 vòng 8 (`54ef513cd7`): số đã duyệt giữ ở app là chưa đủ, vì giữa lượt hỏi và lượt ghi đơn khác có thể dùng bớt kho bếp, máy chủ tính lại phần thiếu lớn hơn rồi lấy luôn. Ràng buộc về số lượng phải nằm ở cửa máy chủ (QT-19): lượt ghi mang số đã duyệt (`lay_toi_da`), máy chủ chỉ ghi khi phần tính lại không vượt (`kho_san_xuat.trong_han_lay`), vượt thì trả câu hỏi mới, không ghi; thiếu số duyệt cũng không ghi.

## 11/11/2026 (v649): GrabFood đổi mẫu không báo, lệnh cấp dưới trùng, câu chặn bị cắt

- Bộ đọc báo cáo đối tác KHÔNG được bỏ qua lặng lẽ một dòng có dạng giao dịch. Mục Marketing của GrabFood từ 11/2026 in Mã giao dịch là "-" thay cho ADS-số; mẫu cũ `continue` khi không khớp nên mất mọi phí quảng cáo, tổng thu nhập lệch đúng bằng phí đó (NVHTN 10/11: 447.292 so với 398.153) và gần hết nguồn GrabFood nằm ở Cần xử lý. Luật: dòng MỞ ĐẦU như một giao dịch ("10 Th11, 12:04 PM") mà không khớp mẫu thì báo LoiDong; căn cước khi đối tác bỏ mã phải ghép đủ giờ, tiền và mô tả (hai khoản cùng giờ cùng tiền khác mô tả).
- PDF có ô bảng căn giữa theo chiều dọc: ô xuống hai dòng (mã đơn dài GD-3O7K2M7B) làm tiền tố nằm TRÊN dòng đơn, phần sau nằm DƯỚI, PyMuPDF trả ba mảnh theo thứ tự không đoán được. Ca kiểm v579 giả định một thứ tự nên không bắt được. Khi chưa có tệp gốc chạy PyMuPDF, đọc toạ độ chữ của PDF thật (giải nén luồng nội dung trong trình duyệt) để biết bố cục, và viết ca cho MỌI thứ tự mảnh.
- Thư thông báo kỹ thuật của đối tác (bảo trì ngân hàng) có chữ "thanh toán" trong thân nên bị coi là thư báo cáo. Lọc theo TIÊU ĐỀ trước: tiêu đề là thông báo kỹ thuật mà không nói tới báo cáo, sao kê, đối soát thì không phải báo cáo.
- Tin Zalo gửi theo từng nguồn phải phân biệt được nguồn trong tiêu đề: ba báo cáo GrabFood cùng ngày của ba cửa hàng ra ba tin giống hệt nhau.
- Hai lối tạo lệnh cho cùng một việc (Chốt kế hoạch tạo sẵn lệnh cấp 1, cấp 2; v648 hoàn tất món chính tự tạo lệnh cấp dưới) thì lối sau phải DÙNG lệnh đang mở của lối trước, không tạo song song. Lệnh dùng lại lớn hơn phần làm thì nguyên liệu cấp dưới phải nhân tỷ lệ phần làm, không lấy nguyên số của lệnh.
- Codex PR #552: lối "dùng lệnh đang mở trước khi tạo mới" phải (1) lọc đủ điều kiện ngay ở máy chủ và không cắt 20 dòng, không thì lệnh hợp lệ thứ 21 bị bỏ sót; (2) đọc hỏng thì DỪNG, vì đọc hỏng không chứng minh là không có lệnh mở, mà tạo được là thành lệnh trùng không ai biết; (3) có ca bench chạy ERPNext thật trên lệnh lớn hơn phần làm và lệnh đã làm dở.
- Codex PR #552 vòng 2: số còn phải làm của một lệnh là `qty - produced_qty - process_loss_qty` (ERPNext đóng lệnh khi làm cộng hao đủ số). App từng tự tính ở bốn chỗ, hai chỗ quên trừ hao: nút Hoàn tất cho nhập quá phần còn lại, Kế hoạch đếm dư hàng đang làm. Gom về một hàm `mfgConLai`, ai đọc lệnh phải xin cả cột `process_loss_qty` (máy chủ chỉ trả cột được xin), có ca chốt "chỉ một chỗ tự tính".
- v649 Loan Anh (11/11/2026): đổi lúc trừ vỏ BTP từ chốt sổ (theo số bán) sang lúc bếp nhập ô Bếp làm. Đặt phép trừ ở `KiemBanhNgay.on_update` (chênh so với bản trong CSDL) chứ không ở `luu_o`, vì Desk và API cũng sửa được ô này; trừ bằng một câu UPDATE cộng dồn, không kẹp về 0, để sửa bớt cộng lại đúng; bỏ hẳn phép trừ lúc chốt, không thì mỗi bánh bị trừ hai lần. Bàn giả kiểm thử phải ghi vào khoá dict (`d["so_btp"]`), gán thuộc tính trên `Doi` tạo thuộc tính riêng và che mất phép ghi.
- v649 web: tab Đặt bánh trước hiện số BTP của bếp nên không được cho chọn Hôm nay; máy chủ không biết dòng giỏ đến từ tab nào (items chỉ có mã), nên chặn theo nguồn tồn: đơn nhận hôm nay chỉ nhận bánh BTP có dòng trong Kiểm bánh hôm nay.
- Câu lỗi máy chủ dùng <br> mà app xoá thẻ thì chữ dính nhau ("Nguyên liệu - TVĐếm"); app lại cắt 180 ký tự nên mất đúng phần việc cần làm. Câu chặn phải có mã chứng từ gây chặn ở ĐẦU câu, và app đổi <br> thành xuống dòng.
