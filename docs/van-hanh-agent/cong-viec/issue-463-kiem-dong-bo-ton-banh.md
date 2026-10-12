# Issue #463 - kiểm đồng bộ tồn bánh lên web

Ngày đo mã nguồn và fixture: 12/10/2026. Phạm vi lượt này chỉ đọc, đo và thêm
ca hồi quy. Không sửa logic, dữ liệu quá khứ hay Server Script.

## Bảng a đến g

| Mục | Sales online | Quầy D1 | Quầy NVHTN |
|---|---|---|---|
| a. Màn nhập nguồn | `Kiem Banh Ngay`, dòng `co_the_ban` | `Vagabond Kiem Kho Diem` của D1 | `Vagabond Kiem Kho Diem` của NVHTN |
| b. Ý nghĩa số | Bếp còn nhận được cho đơn online | Bánh đang còn trong tủ D1 | Bánh đang còn trong tủ NVHTN |
| c. Phép tính fixture cùng mã `BAWC00463` | Giá trị đã chốt ở dòng: `4` | `8 + 2 - 3 - 1 - 1 = 5` | `3 + 4 - 2 - 0 + 1 = 6` |
| d. Cửa máy chủ | `kiem_banh.co_the_ban_hom_nay` | `kiem_kho.con_tren_quay_web` | `kiem_kho.con_tren_quay_web` |
| e. Dạng trả về | `banh[ma]` và `nhom[].sizes[].con` | `quay[ma=D1].mon[].con` | `quay[ma=NVHTN].mon[].con` |
| f. Nơi Vue nhận | `napTon` ghi `S.TODAY`, rồi trộn `nhom` vào `S.CAKES` | `napQuay` ghi `S.STORE.quay` | `napQuay` ghi `S.STORE.quay` |
| g. Kết luận | Không được cộng với tồn quầy | Không được gộp với NVHTN hoặc Sales online | Không được gộp với D1 hoặc Sales online |

Các số 4, 5 và 6 là fixture có chủ đích để chứng minh ba nguồn độc lập, không
phải số liệu vận hành ngày 12/10. Checkout được cấp không có remote `origin`,
thông tin đăng nhập GitHub hay kết nối site, nên lượt này chưa thể đo số thật
và chưa thể đăng phần lệch lên Issue. Đây là giới hạn môi trường, không phải
kết luận rằng dữ liệu thật đang khớp.

## Đường dữ liệu đã đối chiếu

1. `co_the_ban_hom_nay` đọc phiếu `KB-<ngày>`, giữ dòng `co_the_ban > 0`, bỏ
   bánh sỉ và mã bị tắt web, rồi trả đồng thời bản đồ `banh` và nhóm món.
2. `con_tren_quay_web` duyệt từng điểm có quầy, đọc đúng phiếu
   `KKD-<điểm>-<ngày>`, tính `tồn đầu + nhập - đã bán - hỏng + điều chỉnh`, và
   chỉ công khai dòng đang theo dõi còn dương.
3. Vue `napTon` gọi duy nhất cửa Sales online và giữ nguyên bản đồ mã-số trong
   `S.TODAY`. Tồn D1 và NVHTN đi qua `napQuay`, không qua `napTon`.

## Ca hồi quy và lệnh tái hiện

- Python dựng cùng mã ở hai bảng quầy với dữ liệu khác nhau và chốt kết quả
  D1 là 5, NVHTN là 6, không cộng thành 11.
- Node cho `co_the_ban_hom_nay` trả hai size tổng 6, chốt đúng tên API,
  `S.TODAY`, từng cặp mã-số sau khi trộn và computed `banhHomNay`.
- Lệnh: `python3 vagabond/khung/kiem_thu/chay.py -im`.
- Lệnh: `node vagabond/khung/kiem_thu/hanh_vi/web_vue_banh.mjs`.

Không thấy lệch logic trong đường mã đã đọc và fixture trên. Chưa đủ bằng chứng
để kết luận số site thật khớp cho ngày 12/10; cần chạy phép đo đọc-only trên
site rồi bổ sung bảng mã-số thực tế vào #463 trước khi đề xuất sửa.

## Giới hạn nghiệm thu khi gom 12/10

Bảng trên là phân loại a-g của báo cáo cloud, chưa trả lời đủ từng mục a-g
trong đề bài GitHub. Chưa chứng minh đầy đủ bán quầy làm giảm đúng điểm,
web/Pancake giữ rồi ghi sổ không trừ hai lần, loại trừ disabled/is_sales_item,
ranh giới 23:59-00:01, điểm tắt và giỏ đang mở khi tồn giảm. Giữ #463 mở;
Claude cần rà các khoảng trống này và giao Codex bổ sung ca kiểm, không
suy từ hai fixture đạt thành hoàn tất audit tồn. Các hạn chế remote ở trên
là của lượt cloud nguồn; lượt desktop gom có remote và quyền push.
