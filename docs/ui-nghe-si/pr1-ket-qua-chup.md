# Kết quả máy chụp và đo, PR 1 nền

Máy sinh từ `node cong_cu/ui_b/chup.cjs --khung 360x780,390x844,1366x768,683x384` (Chromium, app thật, máy chủ giả, vai quản trị). Mẫu số là các màn máy chụp hiện mở được, chưa phải toàn bộ danh mục 280 màn: mỗi PR nhóm màn bổ sung kịch bản cho màn của mình.

Mỗi ô ghi một trong: Đạt, Trượt, Chưa chuyển. Màn "Chưa chuyển" chỉ được chấm phần đầu trang (khung chung đã chuyển) và không tính là đạt.

## Giao diện mới (bật)

| Màn | 360x780 | 390x844 | 1366x768 | 683x384 |
|---|---|---|---|---|
| trang-chu | Đạt | Đạt | Đạt | Đạt |
| dang-nhap | Đạt | Đạt | Đạt | Đạt |
| tai-khoan | Đạt | Đạt | Đạt | Đạt |
| nhom-ban-hang | Đạt | Đạt | Đạt | Đạt |
| hop-xac-nhan | Đạt | Đạt | Đạt | Đạt |
| nhom-khach-hang | Đạt | Đạt | Đạt | Đạt |
| viec-can-lam | Chưa chuyển | Chưa chuyển | Chưa chuyển | Chưa chuyển |
| tim-nghiep-vu | Đạt | Đạt | Đạt | Đạt |
| ghim-da-co | Đạt | Đạt | Đạt | Đạt |
| so-tay | Chưa chuyển | Chưa chuyển | Chưa chuyển | Chưa chuyển |
| dau-trang-bon-nut | Chưa chuyển | Chưa chuyển | Chưa chuyển | Chưa chuyển |
| tinh-tien-chon-quay | Chưa chuyển | Chưa chuyển | Chưa chuyển | Chưa chuyển |
| nhom-ke-toan | Đạt | Đạt | Đạt | Đạt |

## Giao diện cũ (tắt)

Chấm: mở được, không lỗi JS, không cuộn ngang, không mang class ui-b. Giống main từng điểm ảnh: xem `cong_cu/ui_b/so_che_do_tat.py`.

| Màn | 360x780 | 390x844 | 1366x768 | 683x384 |
|---|---|---|---|---|
| trang-chu | Đạt | Đạt | Đạt | Đạt |
| dang-nhap | Đạt | Đạt | Đạt | Đạt |
| tai-khoan | Đạt | Đạt | Đạt | Đạt |
| nhom-ban-hang | Đạt | Đạt | Đạt | Đạt |
| hop-xac-nhan | Đạt | Đạt | Đạt | Đạt |
| nhom-khach-hang | Đạt | Đạt | Đạt | Đạt |
| viec-can-lam | Đạt | Đạt | Đạt | Đạt |
| tim-nghiep-vu | Đạt | Đạt | Đạt | Đạt |
| ghim-da-co | Đạt | Đạt | Đạt | Đạt |
| so-tay | Đạt | Đạt | Đạt | Đạt |
| dau-trang-bon-nut | Đạt | Đạt | Đạt | Đạt |
| tinh-tien-chon-quay | Đạt | Đạt | Đạt | Đạt |
| nhom-ke-toan | Đạt | Đạt | Đạt | Đạt |

## Tổng

- Bật: 52 ô, 36 Đạt, 0 Trượt, 16 Chưa chuyển.
- Tắt: 52 ô, 52 Đạt, 0 Trượt.
- Chưa kiểm: WebKit (máy làm việc không cài được trình duyệt WebKit), cỡ chữ 150% và 200% trên điện thoại, bàn phím ảo, safe area, máy thật. Các mục này không tính là đạt.
