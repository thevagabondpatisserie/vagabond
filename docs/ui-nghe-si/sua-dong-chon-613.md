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
