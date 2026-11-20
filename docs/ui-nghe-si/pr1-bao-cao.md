# PR 1: nền của giao diện "Nghệ sĩ công nghệ"

Ngày 21/11/2026. Nền: `ui-nghe-si` tại `f2fbb8db1` (main `2ae8e6a35`, v677). PR con không tăng APPVER, không thêm dòng `patches.txt`.

## Tóm tắt cho anh Việt

- **Vấn đề.** Muốn đổi giao diện cả app mà nhân viên không thấy nửa cũ nửa mới thì trước hết cần một công tắc an toàn và một bộ khung chung để mọi màn dùng lại.
- **Việc đã làm.** Dựng công tắc ba tầng (Tắt khẩn cấp, lựa chọn riêng từng tài khoản, tầng chung). Dựng bộ màu, phông, biểu tượng, hoạ tiết vũ trụ và khung chung: đầu trang, thanh đáy, thẻ, nút, ô nhập, bảng chọn. Chuyển xong bốn màn nền: Trang chủ, màn phân hệ, Đăng nhập, Tài khoản. Dựng máy chụp và đo tự động.
- **Kết quả anh sẽ thấy.** Khi công tắc tắt, app giống hệt bản đang chạy: so 39 ảnh với main, không khác điểm ảnh nào. Khi bật: giao diện mới ở bốn màn nền và đầu trang của mọi màn; thân các màn khác còn kiểu cũ cho tới PR 2 đến 5.
- **Anh cần duyệt hai ảnh** trước khi em áp rộng: `anh/de-xuat-may-tinh-quay.jpg` và `anh/de-xuat-dau-trang-dien-thoai-hep.jpg`. Và bảng biểu tượng đề xuất (`bang-bieu-tuong.md`) khi anh có thời gian.

## Công tắc

- Đặt ở Desk, mục **Vagabond Giao Dien** (tên hiển thị: Cài đặt giao diện), chỉ quản trị hệ thống mở được. Ba ô: "Tắt khẩn cấp", "Bật giao diện mới cho cả tiệm", bảng "Tài khoản có lựa chọn riêng" (Theo chung, Luôn bật, Luôn tắt).
- Một hàm tính duy nhất: `vagabond.giao_dien.tinh_bat`. Đủ 12 tổ hợp có ca kiểm.
- Trạng thái đi theo HTML của trang /bep: máy chủ chèn một đoạn script vào đầu trang, gắn `ui-b` lên thẻ html trước lần vẽ đầu. Trang /bep từ nay không còn nằm trong bộ nhớ đệm chung của Frappe và mang `Cache-Control: private, no-store` (xử lý V2 của PR 0).
- App đối chiếu số phiên bản của HTML với số của chính nó trước khi vẽ gì; lệch thì dùng trọn giao diện cũ cho lần tải đó.
- Không tự tải lại trang. Đăng nhập và đăng xuất vốn đã tải lại trang nên trạng thái tính lại theo tài khoản mới.
- Không mô đun nào khác đọc công tắc (có ca kiểm chặn). Lớp vẽ không gọi máy chủ, không đọc bộ nhớ máy.

## Lớp vẽ

- Toàn bộ nằm trong `vagabond/public/js/bep/81-ui-b.js`, mọi luật CSS dưới `html.ui-b`. Phông Be Vietnam Pro (4 độ đậm) và Doto 800 nằm trong `vagabond/public/fonts/ui/` (giấy phép OFL), 156 KB. Biểu tượng Lucide 1.77.0 (ISC) nhúng trong mã.
- Doto chỉ nhận chữ số và dấu của số. Tệp Doto không có ký hiệu "₫" và chữ "đ" nằm ở tệp phụ, nên đơn vị tiền đi bằng Be Vietnam Pro có chủ ý, không để trình duyệt chọn phông thứ ba.
- Hoạ tiết vũ trụ: bốn hình 10c, 10d, 14b, 14f chép nguyên từng byte từ design system (đối chiếu SHA-256 trong `cong_cu/ui_b/sinh_hoa_tiet.py`); bản cho app chỉ đổi màu tô và bỏ đường elip ngang của 14b như đặc tả.
- Emoji thành biểu tượng ở lớp vẽ: các ô chỉ chứa một biểu tượng được máy quét thay; chữ lẫn emoji thay từng chỗ qua `uiBKy`. Bảng đối chiếu đủ 244 ký tự: 48 của bảng gốc, 189 đề xuất, 8 chấm màu trạng thái.
- Kiểu viết thẳng trong thẻ: đã chuyển theo cách `var(--ui-x, giá trị cũ)` ở màn Tài khoản và hai hộp xác nhận, làm mẫu cho PR 2 đến 5. Có ca kiểm buộc mọi biến `--ui-*` ngoài lớp vẽ phải có giá trị dự phòng.
- Nút Trợ lý lên đầu trang; nút nổi cũ ẩn khi bật. Nút chỉ có hình đều có nhãn đọc tiếng Việt.

## Đề xuất chờ duyệt bằng ảnh

1. Máy tính quầy (từ 900 trở lên): nội dung giữa màn rộng tối đa 1160; trang chủ 4 cột; màn phân hệ 2 cột; hộp xác nhận và bảng chọn thành hộp giữa màn rộng 560. Màn Tính tiền trên máy quầy trình ảnh riêng ở PR 2.
2. Đầu trang điện thoại hẹp: tiêu đề tối đa 2 dòng cạnh các nút; không đủ chỗ thì tiêu đề xuống hàng riêng; không giấu nút nào.
3. Màu số Doto: mực trên ô nhóm nền sáng, Robin egg trên thẻ Việc cần làm.
4. Bốn màn lẻ (Việc cần làm, Chuông, Sổ tay, Hướng dẫn chế biến) chuyển cùng PR 5 thay vì PR 1, để PR nền gọn. Danh mục đã cập nhật.

## Cổng kiểm mới

| Công cụ | Việc |
|---|---|
| `cong_cu/ui_b/chup.cjs` | Máy chụp và đo: chạy app thật với máy chủ giả, 4 khung, hai chế độ; đo cuộn ngang, vùng bấm 44, chữ 13, bị che, emoji sót, phông thực dùng, tương phản |
| `cong_cu/ui_b/so_che_do_tat.py` | So chế độ tắt với main từng điểm ảnh, cùng một môi trường |
| `cong_cu/ui_b/kiem_khai_bao.py` | Kiểm khai báo CSS của lớp vẽ: màu, cỡ chữ, bo góc, khoảng cách, phông |
| `vagabond/khung/kiem_thu/thu_giao_dien_ui_b.py` | 19 ca: công tắc, hook, quyền, doctype, đường về giao diện cũ, tệp máy sinh |
| `vagabond/khung/bench_thu/giao_dien_ui_b.py` | Trên Frappe thật: trạng thái theo từng tài khoản, không qua bộ nhớ đệm, khẩn cấp thắng |

Kết quả máy chụp: `pr1-ket-qua-chup.md`.

## Tệp đang giữ

`81-ui-b.js` (mới), và các đoạn nhỏ trong `00-nen.js` (hai hộp xác nhận), `01-khung-app.js` (frame), `02-trang-chu.js` (khối ghim, màn phân hệ), `06-nhap-kho-kiem-ke.js` (màn Tài khoản), `12-van-don.js` (một dòng trong __boot). Phiên khác sửa các phần này thì báo trên PR để gộp tay.

## Bảng vấn đề gộp

| Mã | Bằng chứng | Hướng xử lý |
|---|---|---|
| V7 | 26 bộ kiểm hành vi nạp `01-khung-app.js` một mình, không có phần 81 | Các chỗ gọi lớp vẽ mới ở phần cũ viết kiểu "có thì dùng" (`typeof uiB === 'function'`), không sửa 26 bộ kiểm |
| V8 | Ca v533 chỉ cho các phần đã duyệt đứng sau phần 48 | Đã thêm 81 vào danh sách: phần này không có màn lập phiếu, không gán lại frame hay api |
| V9 | Máy làm việc không cài được WebKit | Ghi Chưa kiểm; đề nghị chạy WebKit trên CI ở PR sau |
| V10 | Số Doto 30 nét chấm mảnh, đặt trên quầng màu nhóm nhìn nhạt hơn chữ thường dù phép đo tương phản đạt | Xem ảnh; nếu anh thấy khó đọc thì chuyển số lên nền trắng của đĩa hoặc tăng lên Doto 40 |

## Việc chưa làm

- Lời nhắc "tải lại khi xong việc" cho tab đang mở khi đổi công tắc (bản 4 cho phép, chưa bắt buộc).
- Đo tốc độ mở và cuộn (mục 8): cần máy thật.
- WebKit, cỡ chữ 150% và 200% trên điện thoại, bàn phím ảo, safe area, máy thật: Chưa kiểm.
- Bảng màn x quyền: máy chụp mới chạy vai quản trị; vai quầy và bếp đã có dữ liệu thử nhưng chưa chạy thành bảng.
- Thanh đáy hai nút (Tạm tính, Thu tiền) với tỉ lệ 38%: khung chung đã có kiểu nút và "mặt trăng", bố cục hai nút làm cùng màn Tính tiền ở PR 2.
- Bước gộp phần nền vào main để anh thử sớm: PR riêng sau khi PR này được duyệt, kèm số phiên bản, dòng patch và mục sổ tay.
