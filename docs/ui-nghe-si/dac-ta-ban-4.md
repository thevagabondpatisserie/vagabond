# Đặc tả giao diện "Nghệ sĩ công nghệ" cho app nghiệp vụ /bep (BẢN 4)

Bản 4 ngày 20/11/2026. Ghép bản 3 của anh Việt, phụ lục Codex đã rà và sáu điểm anh Việt chốt tối 20/11/2026. Thay toàn bộ bản 3 và phụ lục: không còn hai bộ luật song song. Chỗ nào bản 4 khác bản 3 đều ghi "(bản 4)".

Repo: thevagabondpatisserie/vagabond. Phần app: `vagabond/public/js/bep/` (82 phần mã ghép thành `app_bep.js`).
Anh Việt duyệt hướng B ngày 20/11/2026 qua bản thử áp lên app thật: https://claude.ai/artifact/9rVCWuqPBKW9rSCTSFvcYv
Không mở được bản thử thì làm theo đặc tả này. Đặc tả là chuẩn.

## 0. Nguyên tắc

- Làm theo skill chong-ghi-de-code và vagabond-thiet-ke-tien-loi. Chữ theo `docs/quy-tac-chu-erp.md`.
- CHỈ đổi lớp hiển thị. Không đổi: chức năng, quyền, dữ liệu lưu, tên trạng thái, điều kiện xử lý.
- KHÔNG thay chữ hay emoji trong: dữ liệu lưu; giá trị trạng thái; tin gửi khách và nhân viên (Zalo, Telegram, email); mẫu in hoá đơn, tem, Print Format. Việc thay emoji bằng biểu tượng chỉ làm ở lớp vẽ giao diện.
- KHÔNG sửa dữ liệu, chứng từ cũ.
- Công tắc giao diện TUYỆT ĐỐI không ảnh hưởng quyền dữ liệu (mục 2).
- Mục tiêu: nhân viên KHÔNG BAO GIỜ thấy app nửa cũ nửa mới. Đổi xong toàn bộ mới bật, bật bằng công tắc, tắt được.
- (bản 4) Luật "không nửa cũ nửa mới" áp cho site thật và tài khoản người dùng. Nhánh tích hợp và site thử được phép chứa màn chưa chuyển, có danh mục theo dõi, và không mở cho nhân viên dùng thật trước khi hoàn tất.
- Đặc tả và máy kiểm (mục 7) phải khớp nhau. Thấy hai bên vênh thì DỪNG, hỏi anh Việt. Không tự chọn bên nào.
- (bản 4) Chỉ mở lại một quyết định đã chốt khi có bằng chứng từ mã hoặc ảnh cho thấy không thực hiện được. Ghi vào MỘT bảng vấn đề gộp trong PR, không tạo vòng góp ý nối tiếp từ giả định.
- Mọi kích thước dưới đây tính bằng CSS px.

## 1. Cách chia việc và nhánh

- Nhánh chung: `ui-nghe-si`. Cập nhật main vào nhánh bằng MERGE, không rebase rồi đẩy đè, vì nhiều phiên cùng dựa vào nhánh này.
- Mỗi phiên làm một PR con vào `ui-nghe-si`, mời Codex rà, rồi DỪNG chờ anh Việt chốt. Không tự merge vào main, không deploy.
- Ghi rõ trong PR các tệp nguồn mình đang giữ để phiên khác không sửa trùng.
- (bản 4) MỘT người giữ tích hợp: giữ số phiên bản phát hành (APPVER), `patches.txt` và tệp ghép `app_bep.js` trên nhánh chung.
  - PR con không tự tăng số phát hành. PR 6 đọc lại main và các PR đang mở rồi mới chọn số chưa dùng.
  - Không sửa `app_bep.js` bằng tay. PR con nào đụng `bep/` vẫn phải dựng lại tệp ghép bằng `dung_app_bep.py` và đưa vào chính PR đó để cổng `--kiem` xanh. Hai PR con xung đột ở tệp ghép thì người tích hợp dựng lại từ nguồn đã gộp, không chọn bỏ một bên.
  - PR con cần cấu trúc hoặc cấu hình mới (ví dụ công tắc) thì được chuẩn bị bước nâng cấp và kiểm nâng cấp trên site thử. Việc đăng ký dòng patch và số phát hành do người tích hợp làm theo luật repo.
  - Giữ đủ mọi cổng build và nâng cấp của repo. Không bỏ cổng nào để hợp đặc tả.
- Thứ tự:
  - PR 0: DANH MỤC màn, thành phần dùng chung, cổng kiểm hiện có (mục 6). CHƯA đổi giao diện.
  - PR 1: NỀN. Công tắc và bộ nhớ đệm (mục 2); bộ chuẩn và bảng biến có tên (mục 3); phông và biểu tượng nhúng sẵn; khung đầu trang, thanh đáy, thẻ, nút, ô chọn, ô nhập (mục 4); máy chụp và đo (mục 7). Kèm hai JPEG trình anh Việt duyệt (mục 4, "Hai bố cục phải duyệt bằng ảnh"). Các PR sau BẮT BUỘC dùng lại bộ này, không tự dựng kiểu riêng.
  - PR 2: Bán hàng và Quầy (gồm Giao hàng).
  - PR 3: Kho, Sản xuất (gồm Đặt hàng, Nhập kho, Xuất kho, Kiểm kê, Thu mua).
  - PR 4: Kế toán, Tài chính.
  - PR 5: Marketing và các màn còn lại (Khách hàng, Báo cáo, Nhân sự, Danh mục, Cài đặt).
  - PR 6: Gộp `ui-nghe-si` vào main, công tắc ĐANG TẮT. Chờ anh Việt duyệt.
- (anh Việt chốt 20/11/2026) THỬ SỚM SAU PR 1: sau khi PR 1 được duyệt, phần nền được gộp riêng vào main và deploy với Tắt khẩn cấp không bật, tầng chung TẮT, chỉ đặt "Luôn bật" cho tài khoản anh Việt (và tài khoản anh chỉ định). Anh chấp nhận thấy app nửa mới nửa cũ trên tài khoản của mình trong lúc PR 2 đến 5 chưa xong; nhân viên không thấy gì khác. Bước gộp này là một PR riêng vào main, đủ cổng kiểm, bench, sổ tay, số phiên bản và dòng patch do người tích hợp đặt; merge và deploy vẫn chờ anh cho phép riêng. Từ đó mỗi PR 2 đến 5 sau khi duyệt cũng được gộp vào main theo cùng cách nếu anh muốn thử tiếp.
- (anh Việt chốt 20/11/2026) Hai trang nằm ngoài app mở từ ô trang chủ, Kiểm bánh (`/kiem-banh`) và BTP (`/btp`), ĐỂ ĐỢT SAU. Không thuộc PR 2 và PR 3.

## 2. Công tắc (ba tầng; tầng trên thắng tầng dưới)

1. TẮT KHẨN CẤP (cả tiệm). Bật lên là MỌI tài khoản về giao diện cũ, bỏ qua hai tầng dưới. Chỉ quản trị hệ thống đổi được.
2. LỰA CHỌN RIÊNG (theo tài khoản): Theo chung / Luôn bật / Luôn tắt. Mặc định "Theo chung". CHỈ quản trị hệ thống đặt, nhân viên không tự đổi. Trong thời gian thử chỉ cấp "Luôn bật" cho tài khoản thử nghiệm (tài khoản anh Việt và tài khoản anh Việt chỉ định).
3. TẦNG CHUNG (cả tiệm): Tắt / Bật. Chỉ quản trị hệ thống đổi được.

Cả tiệm đang tắt mà tài khoản thử đặt "Luôn bật" thì vẫn thấy giao diện mới. Đã bật Tắt khẩn cấp thì không ai thấy.

- Ba tầng đặt ở mục cài đặt giao diện, KHÔNG nằm trong Vagabond Settings.
- Một hàm duy nhất phía máy chủ tính bật hay tắt theo đúng thứ tự trên. Mọi nơi khác chỉ đọc kết quả của hàm này.

### Cách áp

- (bản 4) Trạng thái bật hay tắt và bộ tài nguyên đi kèm phải được quyết định nhất quán TRƯỚC lần vẽ đầu tiên. Ưu tiên máy chủ chọn HTML và tài nguyên cùng phiên bản, gắn class `ui-b` lên thẻ html ngay trong HTML trả về.
- (bản 4) Nếu phải kiểm phiên bản bằng script thì script đó chạy ở đầu trang, trước khi cho vẽ. Không bật giao diện mới rồi gỡ class sau khi đã vẽ. Không loé giao diện cũ rồi mới đổi, và cũng không loé mới rồi về cũ.
- (bản 4) "Sẵn sàng đồng bộ" không có nghĩa tải hết phông trước khi mở app hay chờ vô hạn. PR nền xác định tài nguyên tối thiểu và đường dự phòng, chứng minh đường dự phòng chạy khi thiếu cấu hình hoặc thiếu tài nguyên. Không giấu cả trang khi lỗi. Bộ CSS và JS dự phòng cũng phải tương thích với HTML đang trả.
- Không tự tải lại trang khi đổi công tắc. Thay đổi có hiệu lực ở lần mở hoặc tải lại trang kế tiếp. Tuyệt đối không ngắt nhân viên đang nhập đơn hay thu tiền.
- Mọi CSS mới nằm dưới `html.ui-b`. Mọi phần JS vẽ khác đi (biểu tượng, màu trạng thái lúc chạy) đọc cùng một trạng thái lấy từ class trên thẻ html của chính trang đó.
- Tắt là về giao diện cũ, gồm cả phần do JS tạo ra. Class, bố cục DOM và biểu tượng mới đều phải có nhánh cũ.
- Giao diện cũ giữ nguyên trong code cho tới khi anh Việt chốt bỏ.

### Kiểu viết trong thẻ và đường về giao diện cũ (bản 4)

- Kiểu viết thẳng trong thẻ (`style="..."`, 8.401 chỗ) thắng CSS thường đặt dưới `html.ui-b`. Không giải quyết bằng rải `!important` toàn app.
- Với khai báo trình bày phù hợp, dùng biến theo vai trò, ví dụ `color: var(--ui-text-2, #64748b)`. Giá trị dự phòng giữ NGUYÊN giá trị cũ của đúng chỗ đó; biến mới chỉ khai dưới `html.ui-b`.
- Đây không phải phép thay chuỗi hàng loạt. Phải xét trạng thái, khai báo gộp, chỗ JS ghi lại style, cách kế thừa biến và mọi chỗ mã đang đọc giá trị style. Không biến một màu đang mang nhiều nghĩa thành một biến chung.

### Tắt khẩn cấp và tab đang mở (bản 4)

- Tắt khẩn cấp có hiệu lực ở lần mở hoặc tải lại kế tiếp, không tự tải lại giữa thao tác.
- App được hiện lời nhắc "Giao diện đã được cập nhật. Tải lại khi hoàn tất thao tác" với nút tải lại do người dùng chủ động bấm. Dùng kênh cấu hình hoặc thông báo sẵn có, không thêm một vòng hỏi máy chủ liên tục riêng.
- Chỉ mời tải lại khi đã xác nhận không có biểu mẫu chưa lưu, yêu cầu đang gửi, đang thu tiền hay giao dịch chưa rõ kết quả. Không xác định chắc thì hoãn lời nhắc, không đoán là an toàn chỉ vì đang ở màn khác.

### Bộ nhớ đệm và nhiều tài khoản

- HTML trang app (có hoặc không có `ui-b`) là RIÊNG cho từng người. Đặt Cache-Control private, no-store (hoặc tương đương). Không để proxy, CDN hay service worker trả HTML của người này cho người khác.
- (bản 4) Một bản kê phát hành ràng buộc HTML, CSS, JS, phông, biểu tượng với cùng một số phiên bản (APPVER). Tài nguyên đổi theo bản thì gắn số phiên bản trong đường dẫn; tài nguyên không đổi (tệp phông) được dùng đường dẫn theo mã băm nội dung, không cần đổi tên ở mỗi phiên bản.
- JS khi chạy so phiên bản của mình với phiên bản ghi trong HTML. Lệch thì KHÔNG áp `ui-b` cho lần tải đó, dùng trọn giao diện cũ, ghi log. Phép so này chạy trước lần vẽ đầu (xem "Cách áp"). Không bao giờ vẽ HTML mới với CSS hoặc JS cũ hay ngược lại.
- Không dùng localStorage, sessionStorage hay cookie dùng chung máy làm nguồn quyết định bật hay tắt. Đăng xuất rồi đăng nhập tài khoản khác trên cùng máy thì trạng thái tính lại theo tài khoản mới.
- Nhiều tab: mỗi tab nhất quán từ lúc mở. Đổi công tắc thì tab đang mở giữ nguyên tới lần tải sau. Trong một tab không bao giờ có nửa cũ nửa mới.
- QUYỀN: không đọc công tắc trong kiểm quyền, API, truy vấn, báo cáo. Cùng một tài khoản, bật hay tắt `ui-b` thì thấy đúng cùng dữ liệu, cùng nút được phép, cùng kết quả API.

## 3. Bộ chuẩn (tệp biến dùng chung --ui-*)

### Màu nền và chữ

| Biến | Giá trị | Dùng cho |
|---|---|---|
| --ui-paper | #F3EFE7 | nền giấy |
| --ui-glass | rgba(255,255,255,.72) | thẻ kính, blur --ui-blur-card |
| --ui-glass-solid | #FEFEFD | nền ĐẶC thay kính |
| --ui-glass-line | viền 1px rgba(255,255,255,.95) | viền thẻ kính |
| --ui-glass-shadow | 0 10px 30px rgba(18,22,25,.06) | bóng thẻ kính |
| --ui-bar | rgba(243,239,231,.86) | thanh đáy, blur --ui-blur-bar |
| --ui-bar-solid | #F3EFE7 | nền ĐẶC thay thanh đáy (giữ viền trên mảnh để tách lớp) |
| --ui-header-tint | #EAF4F3 | dải chuyển đầu trang (từ màu này sang --ui-paper) |
| --ui-blur-card | 14 | độ mờ thẻ |
| --ui-blur-bar | 16 | độ mờ thanh đáy |
| --ui-ink | #121619 | mực: chữ chính, nút chính |
| --ui-text-2 | #4B5359 | chữ thường |
| --ui-text-3 | #656D73 | chú thích, nhãn mục |
| --ui-robin | #4FDBF2 | điểm nhấn, mặt trăng nút |
| --ui-robin-text | #0A7186 | chữ xanh trên nền sáng |
| --ui-midnight | #23245C | thẻ nổi bật |

Quầng màu nền trang (radial-gradient): Robin egg 38% ở góc trên phải; Marigold 22% ở giữa trái; Indigo 14% ở dưới phải.

Khi không hỗ trợ backdrop-filter (@supports), máy yếu, hoặc prefers-reduced-transparency: dùng các biến *-solid.

### Màu trạng thái (giữ đúng nghĩa luật chip AGENTS 2b)

| Nghĩa | Màu |
|---|---|
| Xong / Đã ghi sổ / Đã duyệt | #116B4A |
| Chờ | #9C4A08 |
| Cần xử lý / lỗi | #C2361F |
| Huỷ / không hoạt động | #656D73 |

### Màu nhóm (cố định theo nhóm, không luân phiên)

| Nhóm | Màu |
|---|---|
| Đặt hàng | Robin egg #4FDBF2 |
| Sản xuất | Marigold #FDB738 |
| Nhập kho | Vermilion #F36E3E |
| Xuất kho | Emerald nhạt #5FD69B |
| Kiểm kê | Indigo nhạt #8E9BFF |
| Bán hàng | Gold nhạt #E8C98A |
| Khách hàng & Marketing | Robin egg |
| Giao hàng | Marigold |
| Báo cáo | Indigo nhạt |
| Thu mua | Emerald nhạt |
| Kế toán | Robin egg |
| Tài chính | Gold nhạt |
| Nhóm mới sau này | lấy theo vòng thứ tự trên |

### Tương phản

- Mọi chữ dưới 24px thường hoặc dưới 18.66px đậm: từ 4.5:1 trở lên (chữ 17px đậm VẪN cần 4.5:1).
- Chữ từ 24px thường hoặc từ 18.66px đậm trở lên: từ 3:1 trở lên.
- Chữ trên kính mờ hoặc gradient: đo trên nền xấu nhất, và mở ảnh tự xem lại.
- (bản 4) Chữ --ui-text-3 trên nền giấy đạt khoảng 4,59:1 theo phép tính màu đặc. Không suy ra mọi quầng màu đều đạt hay đều trượt. Giữ chữ nhỏ trên lớp nền ổn định; nơi không đủ tương phản thì dùng --ui-text-2 hoặc --ui-ink đã có trong bộ chuẩn. Đo màu thực sau khi hoà nền và mở ảnh xem; không đổi cả bảng màu chỉ vì một vị trí.

### Phông (tự lưu trong app, không tải Google lúc chạy; preload hai tệp chính)

- Be Vietnam Pro 400/500/600/700: mọi chữ và số. font-feature-settings "tnum" để số thẳng cột.
- Doto 800: CHỈ cho số lớn (số việc tồn trên ô nhóm, doanh thu, tổng tiền lớn).
- Không còn phông nào khác.
- (bản 4) PR nền kiểm đúng tệp Doto sẽ nhúng với các ký tự: 0, dấu trừ, dấu chấm, dấu phẩy và ký hiệu tiền. Được tách đơn vị tiền sang Be Vietnam Pro. Không để trình duyệt âm thầm thay bằng phông thứ ba.
- (bản 4) Màu số Doto: số trên ô nhóm nền sáng dùng --ui-ink; số trên thẻ Việc cần làm (Midnight) dùng Robin egg như bản thử. Đây là đề xuất, anh Việt duyệt bằng ảnh ở PR nền.

### Cỡ chữ

Be Vietnam Pro (5 cỡ): 13 chú thích, nhãn mục in hoa (giãn .12em), số đếm nhỏ; 15 chữ thường, ô nhập, tên dòng danh sách; 17 tên nhóm, chữ trên nút; 20 tiêu đề màn; 24 tiêu đề lớn, số lớn khi Doto không vừa.

Doto (3 cỡ): 30 số trên ô nhóm; 40 doanh thu; 48 Việc cần làm.

Không có chữ nào dưới 13 (tính ở cỡ chữ mặc định của trình duyệt).

### Bo góc (6 mức có tên)

14 ô nhỏ, ô số bàn; 16 viên biểu tượng; 18 ô chọn, ô nhập; 24 thẻ; 26 ô nhóm trang chủ; 999 nút, viên.

### Khoảng cách

(bản 4) Luật bội số của 4 áp cho KHAI BÁO margin, padding, gap (lề màn 12, khe thẻ 12, đệm thẻ 16 đến 20). Luật này không tự áp cho chiều rộng, chiều cao, đường kính, nét viền hay vị trí đã được đặc tả riêng; mỗi nhóm đó có bảng biến riêng ở PR nền. Khoảng rộng theo %, grid/fr, auto và khi tăng cỡ chữ được phép ra số lẻ khi đo trên màn.

Ngoại lệ khoảng cách BẮT BUỘC viết bằng biến có tên. Các giá trị đã duyệt theo đo trên bản thử:

| Biến | Giá trị | Lý do |
|---|--:|---|
| --ui-tile-inset | 15 | lề biểu tượng và số trong ô nhóm |
| --ui-tile-icon-top | 17 | mép trên biểu tượng ô nhóm |
| --ui-tile-title-top | 87 | mép trên tên nhóm |
| --ui-todo-inset | 18 | lề phải số Việc cần làm |
| --ui-todo-text-gap | 96 | lề chữ chừa cho số Việc cần làm |
| --ui-header-min-h | 66 | chiều cao tối thiểu đầu trang |
| --ui-bar-pad-y | 10 | đệm trên thanh đáy |
| --ui-bar-pad-bottom | 14 | (bản 4) đệm đáy thanh đáy, cộng safe-area MỘT lần |
| --ui-moon-inset | 6 | khoảng cách mặt trăng tới mép nút chính |
| --ui-pay-gap | 10 | khe giữa cột logo và tên trong ô thanh toán |

Kiểm khai báo chỉ chấp nhận giá trị trong thang hoặc trong bảng này. Ngoại lệ mới phải thêm vào bảng (tên, giá trị, lý do) trong PR và được duyệt. Không viết số trần ngoài thang. Bảng ngoại lệ không được dùng để che lỗi tràn hoặc vùng bấm quá nhỏ.

### Vùng bấm

Mọi phần tử bấm được có vùng bấm từ 44x44 trở lên. Hình nhìn thấy có thể nhỏ hơn (ví dụ nút tròn 42), nhưng vùng bấm vẫn 44.

### Biểu tượng

- Bộ Lucide (giấy phép ISC), nét 1.6, nhúng SVG trong app, không tải ngoài.
- Thay emoji ở LỚP HIỂN THỊ. Một chức năng một biểu tượng. Bảng gốc:

| Emoji | Lucide | Emoji | Lucide | Emoji | Lucide |
|---|---|---|---|---|---|
| 🔔 | bell | 👤 | circle-user-round | 🏠 | house |
| 📌 | pin | 🛒 | shopping-cart | 🧑‍🍳 | chef-hat |
| 📥 | package-plus | 📤 | package-minus | 🧮 | calculator |
| 🎂 | cake | 💝 | heart-handshake | 🚚 | truck |
| 📈 | chart-line | 🧾 | receipt | 💰 | wallet |
| 📋 | clipboard-list | 📄 | file-text | ✅ | circle-check |
| 🕐 | clock | 🖥 | monitor | 🏬 🏪 | store |
| 🥡 | shopping-bag | 🖨 | printer | 💵 | banknote |
| ➕ | plus | 📒 | book-open | 🎁 | gift |
| 💳 | credit-card | 🎫 | ticket | 🎟 | ticket-percent |
| ⏳ | hourglass | 🏦 | landmark | 🛵 | bike |
| 💬 | message-circle | ⚠ | triangle-alert | ✎ ✏ 📝 | pencil |
| 🔎 🔍 | search | ✕ | x | ✓ | check |
| 📷 🖼 | image | 👥 | users | 🔒 | lock |
| 📦 | package | | | | |

- Emoji còn lại: đề xuất biểu tượng gần nghĩa nhất, ghi bảng đối chiếu đầy đủ trong PR 1.
- Nút chỉ có biểu tượng PHẢI có aria-label tiếng Việt (ví dụ "Quay lại", "Trang chủ", "Trợ lý").
- Logo đối tác (Grab, MB, Payoo, Shinhan, OnePay, BeFood, GreenSM, ShopeeFood...) GIỮ NGUYÊN ẢNH GỐC.

### Hoạ tiết vũ trụ (bản vẽ gốc của Gạo Muối)

- Lấy từ design system "The Vagabond Pâtisserie", thư mục "Họa tiết vũ trụ". Dùng 4 hình: 10c-elip-kinh-tuyen, 10d-qua-cau-luoi, 14b-nguyen-tu, 14f-quy-dao-elip-lech. Không lấy được thì hỏi anh Việt file Vagabond_hoa_tiet_vu_tru_SVG.zip.
- Dùng làm mask, tô màu đậm của nhóm, độ mờ .28, xoay -11 độ, đặt ở góc dưới phải ô nhóm và thẻ doanh thu.
- Hình 14b: bỏ đường viền elip mỏng nằm ngang (path đơn không có vòng trong), vì khi làm mask nó bị tô đặc thành vệt đen.

## 4. Khung chung (theo bản thử đã duyệt)

### Đầu trang (.vh)

- Nền trong suốt trên dải chuyển --ui-header-tint sang --ui-paper. Cao tối thiểu --ui-header-min-h, đệm 12.
- Trái: nút quay lại hoặc chuông. Giữa: tiêu đề 20 đậm, căn trái, tối đa 2 dòng (xem "Tên và số dài"). Phải: các nút tròn.
- Nút tròn đầu trang: hình 42, vùng bấm 44, nền kính, biểu tượng 20 chính giữa.
- Nút trợ lý chat (#tlNut) chuyển LÊN ĐẦU TRANG thành nút tròn như trên, đứng trước nút cuối bên phải. Không nổi ở góc dưới nữa.

### Thanh đáy (.vf)

- Chạm đúng mép dưới. margin 0. Đệm trên --ui-bar-pad-y, hai bên 12, đáy --ui-bar-pad-bottom cộng env(safe-area-inset-bottom) một lần.
- Nền --ui-bar có blur (nền --ui-bar-solid khi không hỗ trợ), viền trên mảnh.
- Nút phụ (Tạm tính...): rộng 38%, cao 52, viền mực 1px, bo 999, chữ 17.
- Nút chính (Thu tiền...): phần còn lại, cao 52, nền mực, chữ trắng 17. "Mặt trăng" tròn 40 Robin egg bên phải, mũi tên chéo màu mực, cách mép --ui-moon-inset.
- Hai nút cùng chiều cao. Chữ và biểu tượng trong nút giữa theo chiều dọc.

### Thẻ (.card)

- Kính mờ, bo 24.
- Thẻ nổi bật (Việc cần làm, doanh thu): nền Midnight có quầng Robin egg, Marigold, Indigo; chữ trắng.

### Trang chủ (.gwrap/.gt)

- Ô nhóm lưới 2 cột, khe 12, cao tối thiểu 150, bo 26. Quầng màu nhóm góc trên phải, hoạ tiết góc dưới phải.
- Biểu tượng: đĩa trắng 46 tại (--ui-tile-inset, --ui-tile-icon-top) tính từ góc ô.
- Số việc tồn (Doto 30): tâm dọc TRÙNG tâm biểu tượng, cách mép phải --ui-tile-inset.
- Khối tên nhóm cách mép trên CỐ ĐỊNH --ui-tile-title-top. Tên 2 dòng không đẩy lệch hàng tên ô bên cạnh.
- Ô Việc cần làm: thẻ Midnight rộng cả hàng. Số Doto 48 màu Robin egg, căn giữa theo chiều dọc, cách mép phải --ui-todo-inset. Chữ chừa lề phải --ui-todo-text-gap.

### Danh sách nghiệp vụ (.hub)

- Biểu tượng trên viên 46 bo 16, nền chuyển trắng sang màu nhóm, căn giữa dọc dòng.
- Tên 15 đậm 600, mô tả 13 màu --ui-text-3.
- Số việc tồn: viên mực, chữ trắng 13, chấm Vermilion phía trước. Mép phải các viên thẳng hàng.

### Màn Tính tiền

- Thẻ "Quầy đang bán / Ngày bán": hai cột căn TRÊN. Nhãn hai cột cùng hàng, giá trị cùng hàng. Cột phải căn phải, mũi tên giữa theo chiều dọc.
- Thẻ "Danh sách hoá đơn trong ngày" thành thẻ doanh thu Midnight: nhãn "DOANH THU HÔM NAY"; số tiền Doto 40; "N hoá đơn · bấm để xem danh sách"; viên "x chưa ghi sổ" (chấm Marigold) và viên "y đã ghi sổ" (chấm xanh); nút tròn mũi tên góc trên phải. Bấm vẫn mở danh sách hoá đơn như cũ.
- Thẻ doanh thu hiện cho mọi tài khoản mở màn này, TRONG PHẠM VI dữ liệu tài khoản đó vốn được xem. Màn hiện tại đã hiện tổng tiền trong ngày trên thẻ này. Nếu kiểm ra có tài khoản quầy hiện CHƯA được xem tổng doanh thu thì DỪNG, hỏi anh Việt. Không tự mở rộng quyền.
- Ô nguồn đơn: lưới 3 cột đều.
- Ô thanh toán: lưới 2 cột. Mỗi ô là grid 2 cột, khe --ui-pay-gap: cột 1 rộng CỐ ĐỊNH 48, chứa logo hoặc biểu tượng, giữa cả hai chiều (logo cao tối đa 28, object-fit contain; biểu tượng 24); cột 2 chứa tên, căn trái. Tên ở mọi ô bắt đầu cùng một vạch.
- Ô số bàn: lưới 5 cột đều (repeat(5,minmax(0,1fr))), khe 8, cao 44, bo 14, chữ giữa ô.
- Ô đang chọn: viền mực 1.5, nền trắng có quầng Robin egg, chấm Robin egg 8 ở góc trên phải.

### Ô nhập

- Nền kính, bo 18, chữ 15. Khi đang gõ: viền và quầng Robin egg.

### Tên và số dài, người dùng tăng cỡ chữ

- Số Doto: số dài thì xuống cỡ Doto kế dưới (48, 40, 30), cuối cùng chuyển Be Vietnam Pro 24 đậm. Vẫn không vừa thì ĐỔI BỐ CỤC (đưa số xuống hàng riêng rộng cả thẻ) hoặc MỞ RỘNG vùng chứa. KHÔNG cắt số, KHÔNG thu nhỏ dưới 24, KHÔNG dùng scale hay ép chữ. Kiểm riêng: 0, số âm, 9 chữ số trở lên (ví dụ 1.234.567.890 đ).
- Tiêu đề màn: tối đa 2 dòng. Vượt 2 dòng thì cuối dòng 2 hiện "…" và bấm vào tiêu đề để mở rộng tại chỗ xem đủ (bấm lần nữa thu lại). aria-label chứa đủ tên. Đầu trang cao lên theo, không đè nội dung.
- Tên trong danh sách, ô chọn, thẻ: xuống dòng, không cắt.
- Chữ trên nút: ở cỡ chữ mặc định không xuống dòng. Khi người dùng tăng cỡ chữ thì được xuống 2 dòng, nút cao lên, không cắt chữ.
- Tăng cỡ chữ: kiểm ở 150% và 200% (cài đặt cỡ chữ của trình duyệt điện thoại; phóng to 200% trên máy tính quầy). Không mất chữ, không đè nhau, không cuộn ngang cả trang. Bảng dữ liệu rộng được cuộn ngang trong khung riêng của nó.

### Hai bố cục phải duyệt bằng ảnh (bản 4)

Trình JPEG ở PR nền, anh Việt duyệt TRƯỚC khi áp rộng:

- Máy tính quầy 1366x768: chỉ rõ bề rộng nội dung, số cột theo loại màn, vị trí thanh thao tác và cách bảng rộng cuộn trong vùng riêng. Không kéo giãn máy móc bản điện thoại.
- Điện thoại hẹp 360: tiêu đề dài cùng đầy đủ nút đầu trang. Hướng đề xuất: tiêu đề có hàng riêng khi thiếu chỗ. Không tự giấu hành động vào menu, không bỏ nút.

Ảnh làm theo skill vagabond-anh-jpeg: dựng trên ảnh chụp thật của app.

## 5. Đổi màu, emoji, cỡ chữ: theo vai trò, không theo "gần nhất"

- Bước 1, thống kê: công cụ quét toàn bộ mã màu, emoji, cỡ chữ, bo góc, khoảng cách trong các phần. Ghi kèm ngữ cảnh: phần nào, phần tử nào, vai trò gì (chữ, nền, viền, trạng thái, nút xoá, trang trí...). Số đếm ban đầu đã có ở PR 0 (`docs/ui-nghe-si/thong-ke-kieu.md`).
- Bước 2, ánh xạ: đề xuất bảng ánh xạ THEO VAI TRÒ, đưa vào PR để duyệt. Ví dụ cùng một màu đỏ, chỗ là lỗi thì sang "Cần xử lý", chỗ là nút xoá thì sang kiểu nút xoá, chỗ trang trí thì sang màu nhóm.
- Bước 3: mới chuyển, theo nhóm màn.
- Phạm vi chuyển: chỉ phần hiển thị. Không đụng chuỗi dữ liệu, tên trạng thái, điều kiện xử lý, nội dung gửi đi, mẫu in.
- Màu trạng thái tô trong JS lúc chạy đổi qua hàm dùng chung, có nhánh cho giao diện cũ.
- Kiểu viết thẳng trong thẻ: chuyển theo cách ở mục 2 ("Kiểu viết trong thẻ và đường về giao diện cũ"), gom dần vào lớp dùng chung, ưu tiên khung lặp nhiều.
- Ca kiểm nghiệp vụ chạy ở CẢ HAI chế độ (`ui-b` tắt và bật). Phải xanh cả hai.

## 6. Danh mục màn (PR 0, trước khi đổi gì)

Lập bảng gồm:

- Mọi màn và hộp thoại của app, kể cả màn ít dùng. Mỗi màn ghi thuộc nhóm nào (PR 2 đến 5) và dùng những thành phần chung nào, để biết PR nào sửa thì phải kiểm lại màn nào.
- Tài khoản và quyền thấy màn đó: thu ngân, bếp, kho, kế toán, quản lý, quản trị.
- Các trạng thái cần kiểm: có dữ liệu; rỗng; đang tải; lỗi; tên dài; số tiền lớn, số âm, số 0; hộp thoại mở; bàn phím ảo đang mở (với màn có ô nhập); cỡ chữ 150% và 200%.

(bản 4) Kiểm đủ nhưng không nhân vô ích:

- Mỗi màn và hộp thoại đều phải nằm trong danh mục. Trạng thái không áp dụng phải ghi lý do.
- Chỉ nhân theo quyền ở nơi giao diện hoặc phạm vi dữ liệu khác nhau theo quyền. Nhóm quyền coi là tương đương phải có căn cứ ghi trong danh mục. Các phép kiểm quyền phía máy chủ giữ nguyên, không rút gọn theo ảnh.
- "Đạt 100%" tính trên bảng này, không tính trên số tệp. Mỗi lần báo phải ghi tử số, mẫu số và SHA của danh mục. Không bỏ ca khó rồi nhận đã đủ.

## 7. Máy chụp và đo (làm trong PR 1, chạy cho mọi PR)

- Chạy trên SITE THỬ hoặc dữ liệu thử có kiểm soát. KHÔNG mở hàng loạt màn trên site thật.
- Khung kiểm: 360x780 điện thoại hẹp; 390x844 điện thoại chuẩn; 1366x768 máy tính quầy Windows (màn Tính tiền đang chạy ở quầy trên Windows); 683x384 là máy tính quầy phóng to 200%; WebKit (Safari điện thoại) cho các màn chính: Trang chủ, Bán hàng, Tính tiền, Đơn giao, Kho.
- (PR 1) Tăng cỡ chữ 150% và 200% trên ĐIỆN THOẠI là cài đặt của hệ điều hành và trình duyệt, máy chụp tự động không giả lập đúng được: ghi "Chưa kiểm" cho tới khi chụp trên máy thật.

### Hai loại kiểm tách riêng (bản 4)

- Kiểm KHAI BÁO trong mã nguồn (lint): biến, tên màu, cỡ chữ, bo góc, khoảng cách margin/padding/gap, biểu tượng, aria-label.
- Kiểm KẾT QUẢ trên màn (máy đo DOM): hình học, vùng bấm, tương phản, phông thực dùng, tràn chữ, cuộn ngang.
- Không đem mọi khoảng cách đo được của bố cục co giãn so với thang bội số 4.

### Phạm vi chạy và mức phải đạt theo giai đoạn (bản 4)

- PR 1 (nền): chạy TOÀN BỘ danh mục để lấy đường chuẩn và bắt lỗi do nền chung gây ra. Chỉ thành phần ĐÃ CHUYỂN phải đạt chuẩn mới. Màn chưa chuyển ghi trạng thái "Chưa chuyển"; KHÔNG ghi "Không áp dụng" để nhận đủ 100%.
- PR 2 đến 5: toàn bộ màn của nhóm, cộng mọi màn dùng thành phần chung mà PR đó sửa (tra theo danh mục mục 6), cộng kiểm hồi quy chế độ tắt tương ứng. Phần đã chuyển phải đạt đầy đủ.
- PR nào đụng công tắc, bộ chuẩn (mục 3) hay khung chung (mục 4): mở rộng ra TOÀN APP.
- PR 6 (gộp): TOÀN BỘ danh mục phải đạt chuẩn mới.
- Mọi giai đoạn vẫn giữ kiểm nghiệp vụ, quyền và giao diện cũ.

### Đánh trượt khi

- Phần tử bấm được đè nhau, hoặc bị đầu trang hay thanh đáy che. Ngoại lệ có chủ ý: biểu tượng trong nút, chấm trạng thái trên chip, nút + trên ảnh.
- Chữ tràn khung, bị cắt (trừ tiêu đề có cách mở rộng ở mục 4). Chữ dưới 13. Vùng bấm dưới 44. Cuộn ngang cả trang.
- So vị trí CHỈ giữa các ô cùng cột (mép trái) hoặc cùng hàng (mép trên, chiều cao) trong một lưới: lệch quá 2 thì trượt. Trong ô chọn có cột biểu tượng: tâm biểu tượng và mép trái tên phải cùng vạch.
- Trong phần `html.ui-b` đã chuyển: còn emoji trong nút, tiêu đề, nhãn; có màu ngoài bộ chuẩn; có phông khác Be Vietnam Pro và Doto; có khai báo khoảng cách, bo góc, cỡ chữ ngoài thang và ngoài bảng biến có tên. Ngoại lệ màu: logo đối tác, ảnh sản phẩm, gradient và hoạ tiết đã khai.
- Tương phản dưới mức ở mục 3.

### Kiểm giao diện cũ (chế độ tắt) (bản 4)

- So chế độ tắt với main tại SHA nền của nhánh, trong MỘT môi trường cố định: cùng dữ liệu thử, trình duyệt, hệ điều hành, phông, khung nhìn; cố định giờ và chuyển động. Chỉ che các vùng động đã liệt kê, không che phần đang sửa.
- Không đặt luật 0 điểm ảnh cho mọi ảnh trên mọi môi trường. Ảnh ổn định trong cùng môi trường thì đặt 0; sai khác do dựng chữ có ngưỡng nhỏ, đo và duyệt trước ở PR nền.
- Mọi khác biệt về bố cục, chữ, số, nút hoặc quyền phải được giải thích. Không tự cập nhật ảnh chuẩn để qua cổng. Khác biệt nghiệp vụ cho phép: 0.
- Máy kiểm chuẩn mới (màu, phông, emoji) KHÔNG quét giao diện cũ.

### Ca kiểm công tắc và bộ nhớ đệm (bắt buộc ở PR 1 và PR 6)

- Đăng xuất tài khoản A (bật) rồi đăng nhập tài khoản B (tắt) trên cùng trình duyệt: B thấy giao diện cũ trọn vẹn. Làm cả chiều ngược lại.
- Hai tab cùng tài khoản, đổi công tắc giữa chừng: mỗi tab nhất quán; tải lại thì theo trạng thái mới.
- Sau khi lên bản mới: mở lại app từ bộ nhớ đệm (quay lại trang, mở lại tab, mạng chập chờn). Không có HTML mới chạy với CSS/JS cũ hay ngược lại. Lệch phiên bản thì phải về trọn giao diện cũ.
- (bản 4) Đủ 12 tổ hợp của ba tầng: khẩn cấp 2 x chung 2 x riêng 3. Sáu tổ hợp khẩn cấp bật đều về cũ; sáu tổ hợp còn lại theo tầng riêng rồi tầng chung. Đây là 12 ca logic của hàm tính, không nhân 12 lần ảnh mọi màn.
- Cùng một tài khoản, bật và tắt `ui-b`: cùng dữ liệu, cùng nút được phép, cùng kết quả API.

### Chữ trên kính mờ và gradient

- Phép đo chưa đủ. Mở ảnh chụp tự xem, ghi kết luận trong PR.

### Máy thật

- WebKit mô phỏng KHÔNG thay máy thật cho: bàn phím ảo; thanh đáy (safe area, thanh địa chỉ co giãn).
- Kiểm trên 1 iPhone Safari và 1 điện thoại Android Chrome thật. Màn kiểm: Tính tiền, Bán hàng, Đơn giao, Kho, và các màn có ô nhập.
- (bản 4) Kiểm máy thật làm trong đợt thử riêng sau deploy thử (bước 3 mục 10) và phải HOÀN TẤT trước khi bật chung (bước 4). PR 6 không bị buộc nhận 100% gồm ca máy thật; ca máy thật còn thiếu ghi "Chưa kiểm" và CHẶN bật chung.
- Phiên làm việc không có máy thật: ghi "Chưa kiểm", viết sẵn danh sách bước để anh Việt hoặc người được chỉ định chụp, ảnh đính vào PR.

### Kết quả

- Bảng theo danh mục mục 6: màn x quyền x trạng thái x khung (nhân theo luật rút gọn ở mục 6).
- (bản 4) Mỗi ô ghi đúng MỘT trong năm: Đạt / Trượt / Chưa kiểm / Chưa chuyển / Không áp dụng. "Không áp dụng" phải có lý do. "Chưa chuyển" chỉ dùng trước PR 6.
- "Chưa kiểm" và "Chưa chuyển" KHÔNG tính là đạt. 100% nghĩa là mọi ô đều Đạt hoặc Không áp dụng có lý do; báo kèm tử số, mẫu số và SHA danh mục.
- Kèm thư mục ảnh, đính vào PR.

## 8. Tốc độ

- Đo tốc độ mở và cuộn ở: Trang chủ, Bán hàng, Tính tiền, Thanh toán. Trên điện thoại phổ thông và máy tính quầy.
- Kính mờ làm giật thì giảm số lớp blur, hoặc dùng các biến *-solid. Tôn trọng prefers-reduced-transparency và prefers-reduced-motion.
- Ghi số đo trước và sau trong PR.

## 9. Khoá lại sau khi bật cho cả tiệm

Thêm vào cổng kiểm giao diện. Áp cho phần `ui-b`, và cho toàn app khi giao diện cũ đã được gỡ. Chặn PR mới nếu:

- thêm màu ngoài bộ chuẩn (trừ ngoại lệ đã khai)
- thêm emoji vào nút, tiêu đề, nhãn
- thêm cỡ chữ ngoài 5 cỡ Be Vietnam Pro và 3 cỡ Doto
- thêm khai báo khoảng cách, bo góc ngoài thang mà không khai biến có tên
- thêm biểu tượng ngoài bộ Lucide đã nhúng
- thêm nút chỉ có biểu tượng mà thiếu aria-label

## 10. Thứ tự phát hành

1. PR 0 đến PR 5 vào `ui-nghe-si`. Máy chụp đo đạt ở phạm vi và mức của từng PR (mục 7). Ca kiểm nghiệp vụ xanh ở cả hai chế độ.
2. PR 6 gộp vào main, chạy toàn bộ danh mục. (bản 4) Bộ kiểm tự động phải đạt trên đúng SHA của PR 6 trước khi deploy thử. Trạng thái khi gộp: Tắt khẩn cấp không bật; Tầng chung TẮT; mọi lựa chọn riêng "Theo chung". Anh Việt duyệt, deploy. Nhân viên chưa thấy gì khác.
3. Quản trị đặt "Luôn bật" cho tài khoản anh Việt (và tài khoản thử anh Việt chỉ định). Tầng chung vẫn TẮT. Dùng thật vài ngày. Hoàn tất kiểm máy thật (mục 7).
4. Kiểm máy thật đã đủ và anh Việt đồng ý thì quản trị hệ thống bật tầng chung. Mỗi nhân viên thấy giao diện mới ở lần mở trang kế tiếp. Không ép tải lại khi đang làm việc.
   Riêng đợt thử sớm (mục 1): bước 3 bắt đầu ngay sau khi phần nền của PR 1 lên main, không chờ PR 6; bước 4 vẫn chỉ làm sau PR 6 và sau khi kiểm máy thật đã đủ.
5. Có sự cố: bật TẮT KHẨN CẤP. Mọi tài khoản về giao diện cũ ở lần mở trang kế tiếp; tab đang mở nhận lời nhắc tải lại theo mục 2.

BÁO CÁO TRONG CHAT: ngắn, nói kết quả nghiệp vụ (bao nhiêu màn đã đổi; bao nhiêu Đạt, Trượt, Chưa kiểm). Chi tiết kỹ thuật để trong PR.

## Nguồn kỹ thuật

- MDN, mức ưu tiên của kiểu viết trong thẻ: https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Handling_conflicts
- Playwright, khác biệt ảnh theo môi trường: https://playwright.dev/docs/test-snapshots
