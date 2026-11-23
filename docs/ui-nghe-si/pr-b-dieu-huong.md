# PR B: điều hướng nhanh (vòng 2 kiểm giao diện, 22/11/2026)

Nguồn việc: báo cáo vòng 2 của Codex trên v683 (nội bộ, có dữ liệu thật, không đính ở đây).
Trên site thật, bấm Trang chủ từ Báo cáo, Đối soát COD, Đơn còn treo, Đặt bàn, Tính tiền:
lưới hiện sau 2.268 tới 3.585 ms, 20 tới 21 lời gọi máy chủ. Nút lùi 51 tới 68 ms.
Một lần đang ở Đối soát COD thì màn Vận đơn quay lại.

## Đã làm

1. Trang chủ dựng ngay bằng số đếm lần trước (bộ nhớ trong phiên, gắn tài khoản), đếm lại
   SONG SONG ở nền, rồi chỉ thay con số trên ô. Số còn mới dưới 15 giây thì không đếm lại.
   Lượt đếm hỏng giữ số cũ. Đổi tài khoản là bỏ bộ nhớ. Con số chỉ để hiện, không dùng cho
   quyền, tiền, ghi sổ.
2. `vgbManNay()` (phần 01): màn async hỏi lại sau khi chờ máy chủ, đã có điều hướng khác thì
   bỏ lượt vẽ. Gắn cho Vận đơn, chi tiết vận đơn, Đối soát COD và khuôn danh sách dùng chung.
3. Lùi về giữ vị trí cuộn và bộ lọc như trước (đã có sẵn trong app, nút lùi đo 51 tới 68 ms nên
   không đổi). Nút Trang chủ nay nhanh nên không cần giữ lại màn trước đó.

## Đo trước và sau (tệp trong repo, máy chủ giả, mỗi lời gọi trễ 150 ms, Chromium 390x844)

`node cong_cu/ui_b/do_dieu_huong.cjs [--app <app_bep.js của main>]`

| Màn xuất phát | Main f8c11c9: lưới hiện | Main: lời gọi | PR B: lưới hiện | PR B: lời gọi | PR B: số đếm xong |
|---|---:|---:|---:|---:|---:|
| Báo cáo | 2348 ms | 22 | 36 ms | 22 (ở nền) | 183 ms |
| Báo cáo, lần hai liền tay | 2352 ms | 22 | 36 ms | 4 | 183 ms |
| Đối soát COD | 2348 ms | 22 | 42 ms | 22 (ở nền) | 195 ms |
| Đơn còn treo | 2360 ms | 22 | 48 ms | 22 (ở nền) | 192 ms |
| Đặt bàn | 2348 ms | 22 | 46 ms | 22 (ở nền) | 202 ms |
| Tính tiền | 2354 ms | 22 | 70 ms | 22 (ở nền) | 208 ms |

Số trên ô lớn sau khi đếm xong giống hệt main (Đặt hàng 5, Sản xuất 24, Kế toán 2).
Màn cũ vẽ đè (mở Vận đơn, danh sách trả chậm 1,5 giây, lùi rồi mở Đối soát COD): main TRƯỢT
(màn đang hiện là Vận đơn), PR B ĐẠT (vẫn là Đối soát COD).

Số tuyệt đối khác site thật: máy chủ thật xử lý song song có giới hạn số tiến trình, nên 20
lời gọi cùng lúc có thể xếp hàng ở máy chủ. Lưới không còn chờ các lời gọi này.

## Chưa kiểm

- Đo lại trên site thật sau deploy, cùng 5 màn, cùng cách đo của Codex (EventTiming, LCP).
- Vuốt lùi trên iPhone thật.
