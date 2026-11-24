# Dòng chọn không vỡ chữ trên điện thoại (#613)

## Phạm vi và nguyên nhân

Ảnh anh Việt gửi cho thấy nội dung dài ép nút Chọn tin nhận thành cột ký tự.
`.cdl-val` vừa không xuống hàng flex, vừa đặt `word-break:break-all` cho cả dòng.
Nút không giữ vùng bấm tối thiểu. Đây là lỗi khuôn dòng dùng chung, không phải lỗi Zalo hay dữ liệu tin.

Sửa cả 7 loại ô: tin nhận, nhóm Zalo, loại tin, chủ đề, ngân hàng, liên kết tài khoản/danh mục, khai/đổi/gỡ khoá.
Áp cùng cách xuống hàng cho tiêu đề bộ phận kèm Chọn cả mục trong hộp chọn tin, và địa chỉ hộp thư kèm trạng thái ở Đối soát nhà cung cấp (phần tràn thẻ của UI07).
Không nhận là đã khép toàn bộ UI07: chữ nhỏ ở dải tiến độ thuộc lượt đổi màn sau.

Giữ thứ tự nhãn, giá trị, thao tác, hướng dẫn. Nút xuống hàng khi không đủ chỗ, chữ ngắt theo từ.
Mã hoặc email quá dài được ngắt khi cần. Không ẩn hay cắt giá trị. Không đổi nhãn, cách chọn/lưu,
quyền, danh mục tin, nội dung tin gửi đi hoặc bản ghi nào trên site. Nhánh giao diện cũ giữ markup cũ.

## Bằng chứng

- Bộ kiểm chạy tệp app đã ghép, CSS và phông thật trên Chromium/Chrome, dữ liệu giả hoàn toàn.
  Cửa thử được nối vào bản app trong bộ nhớ để gọi hàm vẽ thật. Không sửa tệp app để kiểm,
  không kết nối ERP. Không thay kiểm máy thật sau deploy.
- 36 lượt: 9 tình huống x 360, 390, 1366, 683 px. Khung 683 là mô phỏng diện tích máy quầy zoom 200%, không thay cỡ chữ điện thoại.
  Có rỗng/1/23 tin, tên và mã dài, ngân hàng lỗi, nhiều nút, 4 trạng thái hộp thư, mở/chọn/đóng hộp tin.
- Đo chữ bị bẻ giữa từ bằng Range, biên thẻ, biên trang, vùng bấm 44x44.
  Chọn một tin phải thay danh sách đã chọn và giữ tên nhóm đang nhập. Không bấm Lưu.
- Bản gốc v685 trượt đúng lỗi; bản sửa đạt 36/36. 36 ảnh PNG chế độ tắt so byte với bản gốc giống hệt.
- Ca DOM Cài đặt: 41/41 chế độ cũ và 41/41 chế độ mới.
- Đột biến: bỏ xuống hàng, bật bẻ chữ giữa từ, thu vùng bấm xuống 20. Cả 3 đều bị bộ kiểm bắt, trả mã 1 vì lỗi bố cục.
- Máy chụp chung: 114 ô, 102 đạt, 0 trượt, 12 chưa chuyển. Đây là các màn/khung có fixture của repo, không phải toàn bộ app đã đạt.
  Các API chưa có fixture trong máy chụp chung trả rỗng và đã được máy ghi riêng; không dùng chúng để chứng nhận nghiệp vụ.
- Đã mở ảnh kiểm ô nhóm, ô tài khoản desktop và hộp chọn tin mobile. Chưa kiểm Safari/iPhone/Android thật hoặc cỡ chữ điện thoại 150/200%.

## Chạy lại

```sh
node cong_cu/ui_b/kiem_dong_chon.cjs --ra /tmp/dong-chon
node cong_cu/ui_b/kiem_dong_chon.cjs --che-do tat --ra /tmp/dong-chon-tat
node cong_cu/ui_b/kiem_dong_chon.cjs --app /tmp/app-goc.js --che-do tat --ra /tmp/dong-chon-goc
node cong_cu/ui_b/kiem_dong_chon.cjs --dot-bien xuong-hang --ra /tmp/dot-bien-1
node cong_cu/ui_b/kiem_dong_chon.cjs --dot-bien be-chu --ra /tmp/dot-bien-2
node cong_cu/ui_b/kiem_dong_chon.cjs --dot-bien nut-nho --ra /tmp/dot-bien-3
node vagabond/khung/kiem_thu/hanh_vi/cai_dat_loi_570.js
VGB_UI_B=1 node vagabond/khung/kiem_thu/hanh_vi/cai_dat_loi_570.js
```

Cần Playwright và Chrome. Ba lệnh đột biến mong đợi mã 1, không phải 0.
Dùng cùng môi trường, phông, dữ liệu và phiên bản bundle để so ảnh cũ. Không dùng ảnh lỗi làm chuẩn mới.

## Ảnh dữ liệu giả, được phép công khai

| Tình huống | Trước | Sau |
|---|---|---|
| Nhóm nhận tin 390 px | [Ảnh](anh-613/truoc-nhom-23-390.jpg) | [Ảnh](anh-613/sau-nhom-23-390.jpg) |
| Các ô chọn 1366 px | [Ảnh](anh-613/truoc-khac-1366.jpg) | [Ảnh](anh-613/sau-khac-1366.jpg) |
| Hộp thư địa chỉ dài 390 px | [Ảnh](anh-613/truoc-hop-chay-390.jpg) | [Ảnh](anh-613/sau-hop-chay-390.jpg) |

[Bảng số đo](anh-613/ket-qua.json). Ảnh từ site thật và ảnh anh gửi không đưa lên repo.

## Vòng tiếp theo trong cùng PR (v691, Claude nhận PR theo chỉ dẫn anh Việt 24/11/2026)

Anh Việt thấy sau bản 690 "vẫn còn nhiều emoji cũ bị lẫn", nút bị ép, xuống hàng xấu. PR này nhận thêm phần sửa theo loại, ở lớp vẽ chung (`81-ui-b.js`), không vá từng màn.

**Đo trước khi sửa.** Máy chụp chỉ có kịch bản cho khung chung (19 ô), nên thêm `cong_cu/ui_b/quet_man.cjs`. Công cụ đọc mọi mã màn trong `vgbGo` (134 màn), mở từng màn từ trang chủ ở giao diện mới, 390 px, máy chủ giả. Hàm chưa có dữ liệu thử thì trả "rỗng vô hạn" để màn đi tới trạng thái rỗng thay vì nổ. Sau đó dùng lại đúng phép đo của máy chụp. Bản 690:

- 206 chỗ còn emoji ở 58 màn;
- 373 nút, chip, ô dưới 44 điểm;
- 22 nhãn xuống dòng.

**Ba loại đã sửa:**

| Loại | Nguyên nhân | Sửa | Sau sửa (134 màn) |
|---|---|---|---|
| Emoji sót | Máy quét chỉ phủ ô một biểu tượng và đầu nhãn `.btn`/`.chip`. Nút trơn, chip tự vẽ, nhãn, dòng cảnh báo, lựa chọn của ô chọn đều lọt. | `uiBQuetChu`: quét mọi nút chữ trong vùng app và hộp. Emoji có trong bảng đối chiếu thành biểu tượng cùng cỡ chữ, chấm màu thành chấm trạng thái. Lựa chọn trong ô chọn chỉ bỏ emoji. Chừa ô nhập, ô soạn, xem trước bài đăng và vùng đánh dấu rõ `[data-giu-emoji]` (xem trước lời chúc in lên thiệp, bảng chèn biểu tượng của Bài đăng, theo Codex vòng 1). Không đoán theo `white-space: pre`: khung pre đặt qua lớp CSS thì lọt, còn hộp thoại và ghi chú dùng pre-line lại là lớp vẽ. | 0 chỗ |
| Vùng bấm dưới 44 | Chip `posChipNut` (259 chỗ gọi), `.chip`, ô nhập, ô chọn cao 30 tới 37. | Lớp `posc` cho chip chung. Chiều cao tối thiểu 44 cho chip, ô nhập, ô chọn, ô soạn ở giao diện mới. Ô tích 22 điểm. | 45 chỗ còn lại, đều là chip tự vẽ riêng từng màn |
| Nút ép chữ | Hàng flex: đoạn giải thích `flex:1;min-width:0` cạnh một nút không xuống dòng, máy hẹp thì đoạn chữ thành cột 4, 5 dòng (thẻ Đền bù khách ở Khuyến mãi). | `uiBGoEp`: đo thật sau mỗi lần vẽ. Khối chữ hẹp hơn 45% hàng mà cao từ 4 dòng thì cho nút xuống hàng riêng, rộng cả hàng. | Thẻ Đền bù như ảnh dưới |

**Không đổi:**

- Giao diện cũ: so 60 ảnh chế độ tắt với main, 0 điểm ảnh khác.
- Chữ lưu và chữ gửi đi.
- Cách bấm: biểu tượng không nhận cú bấm, đích bấm vẫn là nút.

**Kiểm:**

- Kịch bản `chu-lan-emoji` của máy chụp kiểm các điểm sau:
  - nút trơn, dòng cảnh báo hai emoji, lựa chọn của ô chọn đã đổi;
  - pre-line, `data-giu-emoji`, ô soạn giữ nguyên;
  - hàng bị ép đã gỡ;
  - bấm đúng biểu tượng vẫn chạy hành động.
- Hai ca trong `thu_giao_dien_ui_b.py`:
  - ca thuần tra biểu tượng;
  - ca chạy hàm thật `tqVeForm`, `bdSheetBieuTuong`: mọi emoji của lời chúc và bảng chèn nằm trong vùng giữ. Bỏ đánh dấu thì hỏng: 2 trên 33 emoji lọt ra.
- Kịch bản `chu-lan-emoji` có thêm hai chỗ: xem trước pre-wrap qua lớp CSS giữ nguyên, hai tim ❤️ 🤍 giữ nguyên.
- Cố tình làm hỏng 7 chỗ, bắt 5. Hai chỗ lọt là lớp thừa ở lựa chọn của ô chọn: trình duyệt tự bỏ khoảng trắng và thẻ con của lựa chọn. Đã bỏ phần cắt khoảng trắng thừa.

| Màn 390 px | Bản 690 | Bản 691 |
|---|---|---|
| Vận đơn | [Ảnh](anh-614/truoc-van-don-390.jpg) | [Ảnh](anh-614/sau-van-don-390.jpg) |
| Khuyến mãi | [Ảnh](anh-614/truoc-khuyen-mai-390.jpg) | [Ảnh](anh-614/sau-khuyen-mai-390.jpg) |

Ảnh dữ liệu giả của máy chủ thử.

**Tên truy cập (Codex vòng 2).** Nút chỉ có ký tự hình (✓, ✕, 📷, 🔍, 🗑) lấy chính ký tự làm tên với trình đọc màn hình. Đổi thành SVG `aria-hidden` thì nút mất tên. Sửa hai tầng:

- 23 nút trong nguồn có tên thao tác (`aria-label` "Xoá dòng", "Quét mã", "Hoàn tất lệnh", "Ngày trước", "Tra mã số thuế"...). Nút Quay lại của khung cũ giữ nguyên từng byte, vì giao diện mới có nút riêng đã có tên.
- Lưới đỡ `uiBGiuTen`: nút nào hết chữ sau khi đổi và chưa có tên thì giữ ký tự cũ làm `aria-label`, bằng tên cũ.
- Ca chốt nguồn không còn nút chỉ ký tự mà thiếu tên. Trên mã trước khi sửa ca đỏ với 24 chỗ. Kịch bản `chu-lan-emoji` kiểm lưới đỡ: bỏ lưới thì trượt.

**Còn lại, chưa sửa trong vòng này:**

- 45 chip tự vẽ dưới 44.
- 22 nhãn ngắn xuống dòng: chip có số dính chữ như "Chờ xác nhận0 bàn" ở Đặt bàn, nút "Tải mẫu Excel" hai dòng ở Bảng giá mua.
- Hàng chip lọc của Vận đơn xếp dọc từng chip một.
- Tiêu đề màn dài gãy hai dòng.

Chờ báo cáo rà độc lập của Codex để gom theo loại.

```
node cong_cu/ui_b/quet_man.cjs --ra /tmp/quet --anh
node cong_cu/ui_b/chup.cjs --ra /tmp/anh --man chu-lan-emoji --khung 390x844
python3 cong_cu/ui_b/so_che_do_tat.py --ra /tmp/so-tat
```
