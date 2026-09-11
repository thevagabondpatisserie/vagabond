# CLAUDE.md

Hướng dẫn cho Claude khi chạy trong repo này, kể cả khi chạy trên GitHub Actions.
Tệp này chỉ giữ những luật hay bị quên nhất. Chi tiết nằm trong hai tệp bắt buộc
đọc dưới đây.

## ĐỌC BẮT BUỘC TRƯỚC DÒNG CODE ĐẦU TIÊN

Chạy đúng ba lệnh này trước khi sửa bất cứ tệp nào, kể cả khi thấy việc nhỏ:

```
cat AGENTS.md
cat docs/bai-hoc-su-co.md
ls docs/
```

- `AGENTS.md` là quy ước kỹ thuật của repo: cấu trúc app `/bep`, nguyên tắc thiết
  kế màn hình, quy ước viết code, các quy tắc nghiệp vụ đã chốt, bộ kiểm thử hai
  tầng, trình tự deploy, cách phối hợp với Codex. Không đọc nó là chắc chắn làm
  sai một quy ước nào đó.
- `docs/bai-hoc-su-co.md` là các sự cố ĐÃ XẢY RA THẬT và cách phòng. Mỗi mục là
  một lần mất code, mất email, hoặc một ca kiểm xanh mà lỗi vẫn lên production.
  Đọc để không lặp lại, vì mọi lỗi trong đó đều từng lọt qua cổng kiểm.
- `ls docs/` để thấy các tài liệu chuyên đề. Trước khi sửa một mảng nghiệp vụ,
  `grep -rl <từ khoá>  docs/ AGENTS.md` để xem mảng đó đã có ghi chép chưa.

Nhật ký làm việc đầy đủ theo từng phiên nằm ngoài repo, trong Claude Project
"Vận hành - Operation", nên bản chạy trên GitHub không đọc được. Những bài học
còn giá trị lâu dài đã được rút về `docs/bai-hoc-su-co.md`. Vì vậy: khi phát hiện
một cái bẫy mới mà hai tệp trên chưa ghi, THÊM một mục ngắn vào
`docs/bai-hoc-su-co.md` ngay trong PR đang làm. Đó là cách bản chạy trên GitHub
tích luỹ kinh nghiệm.

## Bối cảnh

The Vagabond Pâtisserie, tiệm bánh ở TP HCM. Repo này là app ERPNext v16 đang chạy
thật cho cửa hàng. Chủ repo là anh Việt. Hai agent cùng làm trên repo: Claude và
Codex (`@codex`). Ngôn ngữ làm việc là tiếng Việt.

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

Muốn Codex tự đẩy bản sửa lên nhánh thì phải dùng `@codex fix`, và mô tả phải đủ
cụ thể để làm được ngay, ví dụ:

    @codex fix dat lai APPVER thanh 478 va them dong patch #v478 vao cuoi patches.txt

chứ không phải `@codex fix cái lỗi ở trên`.

### BA LỆNH TRÊN CHỈ CHẠY TRONG PULL REQUEST

Codex không nhận lệnh từ comment trong Issue. Vì vậy:

- Finding nào cần sửa code thì phải viết vào comment của ĐÚNG PR chứa code đó,
  kèm `@codex fix`. Viết trong issue là việc nằm im.
- Trong issue chỉ dùng để bàn hướng đi và chờ anh Việt quyết. Nếu trong issue có
  finding, ghi rõ nó thuộc PR số mấy rồi sang PR đó mà giao việc.

### Khi nào KHÔNG gọi Codex

Chỉ trả lời một câu hỏi thuần thông tin của anh Việt, hoặc việc đang chờ anh Việt
quyết chứ không chờ kỹ thuật. Im lặng cũng là một lựa chọn đúng.

### Một nhắc nhỏ hay quên

PR còn ở trạng thái Draft thì không bấm merge được, dù mọi cổng đã xanh. Bàn giao
xong nhớ nói rõ PR còn Draft hay đã Ready for review.

## Luật dừng, tránh hai bên gọi nhau vô tận

Trước khi viết bất kỳ lệnh `@codex` nào, ĐẾM số comment trên PR đó có chứa chuỗi
`@codex` do Claude viết, tính trong 24 giờ qua. Đếm CẢ `review`, `fix` và lệnh
tự do, không chỉ đếm `review`.

- Đã có 3 lần: KHÔNG gọi nữa. Thay vào đó viết một đoạn ngắn nói rõ hai bên đang
  bất đồng chỗ nào và mời anh Việt phân xử. Ghi rõ mỗi bên đang lập luận gì.
- Chưa tới 3: gọi bình thường, và ghi rõ đây là vòng thứ mấy.

Cũng KHÔNG trả lời nếu comment mới nhất của Codex không mang finding mới nào, chỉ
là xác nhận hay cảm ơn.

## Ba việc tuyệt đối không làm

1. KHÔNG merge Pull Request. KHÔNG deploy lên Frappe Cloud. Hai việc đó do anh
   Việt quyết, kể cả khi mọi cổng đều xanh.
2. KHÔNG đề xuất sửa hay xoá dữ liệu quá khứ đã ghi sổ, nhất là hoá đơn điện tử
   đã gửi cơ quan thuế. Phát hiện sai sót thì LIỆT KÊ ra, không tự sửa.
3. KHÔNG sửa Server Script trên Desk. Thứ đó nằm trong cơ sở dữ liệu, git không
   quản, mất là không khôi phục được.

## Khi Codex báo lỗi

Tái hiện TRƯỚC, đừng phản biện trước. Qua bốn vòng của issue #205, mọi finding
của Codex đều tái hiện được, kể cả những cái ban đầu nghe như bắt bẻ.

Trình tự bắt buộc: dựng lại đúng chuỗi thao tác Codex mô tả trên đúng SHA họ nói,
chạy và ghi số liệu thật, sửa, rồi trả lời kèm số liệu TRƯỚC và SAU khi sửa.

Chỉ khi tái hiện không ra mới được nói "không tái hiện được TRONG CÁC ĐIỀU KIỆN
ĐÃ KIỂM", và phải liệt kê đã kiểm những điều kiện nào.

## Cổng kiểm bắt buộc trước khi bàn giao

```
python3 vagabond/khung/kiem_thu/chay.py -im
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```

Và giả lập CI tay không, vì máy chạy CI không có sẵn `requests`:

```
mkdir -p /tmp/chanreq
printf 'raise ImportError("gia lap CI")\n' > /tmp/chanreq/requests.py
PYTHONPATH=/tmp/chanreq python3 vagabond/khung/kiem_thu/chay.py -im
```

## Cách viết code trong repo này

- Tách phép THUẦN (không chạm Frappe) khỏi phần chạm hệ, để kiểm thử được không
  cần site.
- Mọi tính năng mới phải có ca kiểm trong `vagabond/khung/kiem_thu/` và đăng ký
  trong `chay.py`.
- Thêm hàm có `@frappe.whitelist()` thì PHẢI thêm tên vào
  `vagabond/khung/kiem_thu/thu_cua_ngo.py`. Quên là hàm cũ mất quyền gọi mà không
  có lớp nào báo.
- Hook đặt trên `"*"` là cực kỳ nguy hiểm, nó áp lên mọi doctype kể cả hạ tầng
  Frappe. Ngày 16/08/2026 một hook như vậy làm cả tiệm không gửi được email suốt
  bốn ngày.
- `APPVER` trong `vagabond/public/js/bep/12-van-don.js` chỉ được TĂNG. Đọc
  `origin/main` ngay trước khi đặt số.
- `vagabond/patches.txt` phải thêm dòng mới mỗi lần phát hành, giữ nguyên mọi
  dòng cũ của phiên khác.
- `app_bep.js` là tệp máy ghép ra từ `vagabond/public/js/bep/`. Nguồn sự thật là
  thư mục `bep/`.

## Ca kiểm có thể tự che mất lỗi

Ca kiểm phải dựng ĐÚNG chuỗi thao tác của khách, không gọi thêm hàm nào "cho
chắc", vì hàm đó có thể chữa lỗi ngay trước khi ca kiểm kịp nhìn.

Dò chuỗi trong mã nguồn KHÔNG phải là kiểm thử. Mã chạy trên trình duyệt thì nạp
cả trang vào node bằng `vagabond/khung/kiem_thu/gia_lap_trang.js`.

Chạy đột biến xong phải đọc trung thực. Nếu 5 đột biến chỉ bắt được 2 thì viết là
2 kèm giải thích, không làm tròn thành 5 trên 5.

Ba mục trên là bản rút gọn. Lý do đầy đủ và ca thật nằm trong
`docs/bai-hoc-su-co.md`, đọc trước khi viết ca kiểm.

## Quy ước trình bày

Không dùng dấu em dash hay en dash trong bất kỳ nội dung nào, chỉ dùng dấu gạch
ngang thường. Áp dụng cho mọi comment, mọi tệp soạn ra, mọi nội dung ghi vào
ERPNext.
