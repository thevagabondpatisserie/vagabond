# Bài học từ sự cố thật

Mỗi mục dưới đây là một lần repo này hỏng thật, trên hệ thống đang chạy cho cửa
hàng. Ghi lại triệu chứng, nguyên nhân gốc, và cách tránh. Đọc tệp này trước khi
sửa những chỗ có liên quan, vì phần lớn các lỗi đó KHÔNG có lớp nào tự bắt được.

Tệp này chỉ giữ bài học rút gọn. Nhật ký đầy đủ từng ngày nằm ngoài repo.

## 11/09/2026 - Kiểm map mới không được khóa bảo trì SePay (#273)

Review phát hiện validate toàn bộ account_map mỗi lần save sẽ chặn cả enabled/token/mốc đồng bộ khi một Bank Account cũ bị ngưng dùng. Chỉ kiểm tuyến mới hoặc thay đổi; JSON/xung đột mới vẫn chặn. Cửa cấu hình tài chính phải dùng quyền tài chính trực tiếp, không đòi thêm vai bán hàng. Ca bench giữ map cũ rồi vô hiệu hóa Bank Account, lưu công tắc, từ chối tuyến mới sai và cho Accounts Manager độc lập khai map.

## Mất code vì làm trên nền cũ

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
