# Ưu đãi tự động qua Zalo theo hành trình khách (v645)

Anh Việt duyệt 08/11/2026 (bộ ảnh đề xuất ưu đãi theo nhóm khách, và ba ô chốt:
bật tin cảm ơn sau mua cho mọi hoá đơn có số điện thoại; trần một tin ưu đãi mỗi
khách mỗi tuần, giờ gửi 8:00 tới 20:00; thu ngân chỉ hỏi số và chỉ mã QR nhận quà).

## Máy làm gì, người làm gì

| Bước | Ai |
|---|---|
| Quét sự kiện mỗi ngày (5 phút một lần với tin theo hoá đơn), phát mã, gửi tin, nhắc trước hạn | Máy (`zalo_kich_ban.chay_tu_dong`) |
| Chống gửi trùng, trần ngày, trần tuần mỗi khách, giờ gửi, ưu tiên khi hạn mức ít, nhóm đối chứng | Máy |
| Báo cáo thứ Hai 09:07 cho nhóm Marketing | Máy (`zalo_kich_ban.bao_cao_tuan`) |
| Hỏi số điện thoại khi tính tiền, chỉ mã QR nhận quà 20.000đ | Thu ngân |
| Cấp mã đền bù cho đơn gặp sự cố | Quản lý (màn Khuyến mãi) |
| Đăng ký mẫu Zalo, đọc báo cáo | Marketing |
| Chốt mức ưu đãi, chọn chương trình cho từng kịch bản, bật kịch bản | Anh Việt, quản lý Sales |

## Kịch bản (theo thứ tự ưu tiên)

| Mã | Tên trên app | Khi nào | Mặc định |
|---|---|---|---|
| sau_mua | Cảm ơn khi khách nhận đơn, báo điểm | Bill quầy lúc ghi sổ; đơn giao lúc Pancake Đã nhận | BẬT bằng bản vá v645 |
| den_bu_nhe, den_bu_vua, den_bu_nang | Đền bù sự cố ba mức | Quản lý bấm Cấp mã đền bù | Tắt, hạn mã 60 ngày |
| sinh_nhat | Chúc mừng sinh nhật kèm voucher | Trước sinh nhật 3 ngày | Tắt |
| nhac_dip | Nhắc dịp năm sau | Năm ngoái nhận đơn giao từ 300.000đ ngày D, gửi trước D 10 ngày | Tắt |
| don_thu_hai | Đơn thứ hai: Hẹn gặp lại | Khách có đúng một đơn, nhận xong 3 ngày | Tắt, đối chứng 10% |
| gioi_thieu | Cảm ơn khách giới thiệu bạn | Bạn mới gõ số khách ở ô Mã giới thiệu trên web và nhận bánh; tối đa 5 mã mỗi tháng | Tắt |
| quay_lai | Mời khách lâu chưa quay lại | Vắng 45 ngày (dòng cũ trên site giữ số đã đặt) | Tắt, đối chứng 10% |
| quay_lai_2 | Mời khách vắng lâu, mốc hai | Vắng 90 ngày | Tắt, đối chứng 10% |
| nhac_han | Nhắc mã sắp hết hạn | Mã riêng của khách còn 3 ngày chưa dùng | Tắt |

## Mức đề xuất (anh chỉnh trong chương trình khuyến mãi)

| Kịch bản | Ưu đãi | Điều kiện | Hạn |
|---|---|---|---|
| Đơn thứ hai | Tặng 1 bánh nhỏ, hoặc -10% tối đa 40.000đ | Đơn từ 250.000đ | 21 ngày |
| Sinh nhật | Tặng slice hoặc đồ uống, hoặc -10% bánh sinh nhật tối đa 60.000đ | | 14 ngày |
| Nhắc dịp | -10% tối đa 70.000đ | Đặt trước ít nhất 3 ngày | 12 ngày |
| Giới thiệu bạn | Mã 50.000đ cho người giới thiệu | Bạn mới dùng ưu đãi đơn đầu -50.000đ | 30 ngày |
| Mời quay lại mốc 1 | Tặng 1 bánh nhỏ | Đơn từ 300.000đ | 14 ngày |
| Mời quay lại mốc 2 | -15% tối đa 80.000đ | | 10 ngày |
| Đền bù nhẹ, vừa, nặng | 30.000đ; -15% tối đa 100.000đ; -20% tối đa 150.000đ | | 60 ngày |

## Mẫu tin Zalo đề xuất cho Marketing đăng ký (loại Hậu mãi)

Mọi mẫu dùng chung bộ tham số máy điền: `<ten_khach>`, `<ten_uu_dai>`,
`<dieu_kien>`, `<han_dung>`, `<ma_voucher>`. Zalo duyệt 2 tới 3 ngày làm việc.

- Đơn thứ hai: "Cảm ơn <ten_khach> đã chọn The Vagabond Pâtisserie lần đầu. Hẹn gặp lại với <ten_uu_dai> (<dieu_kien>), mã <ma_voucher>, dùng tới <han_dung>."
- Nhắc dịp: "<ten_khach> ơi, năm ngoái ngày này Vagabond được làm bánh cho dịp đặc biệt của bạn. Năm nay đặt sớm để nhận <ten_uu_dai>: mã <ma_voucher>, tới <han_dung>."
- Giới thiệu bạn: "Cảm ơn <ten_khach> đã giới thiệu bạn tới Vagabond. Quà của bạn: <ten_uu_dai>, mã <ma_voucher>, dùng tới <han_dung>."
- Mời quay lại mốc hai: "Vagabond nhớ <ten_khach>. <ten_uu_dai> dành riêng cho bạn (<dieu_kien>), mã <ma_voucher>, hết hạn <han_dung>."
- Nhắc hạn: "<ten_khach> ơi, mã <ma_voucher> (<ten_uu_dai>) sẽ hết hạn ngày <han_dung>."
- Đền bù: "Vagabond xin lỗi <ten_khach> vì đơn vừa rồi chưa trọn vẹn. Xin gửi <ten_uu_dai> cho lần tới, mã <ma_voucher>, dùng tới <han_dung>."

## Luật Zalo phải theo (zalo.solutions, đọc 08/11/2026)

- Mọi tin gửi tự động phải theo mẫu ZBS đã duyệt; mẫu đã duyệt không sửa được.
- Nội dung ưu đãi là loại Hậu mãi (tag 3). Khách chỉ nhận được nếu 6 tháng qua đã
  nhận một tin Giao dịch hay Chăm sóc (lỗi -140). Mỗi khách tối đa 1 tin Hậu mãi
  một ngày, 30 tin một tháng mỗi OA.
- Hạn mức tin Hậu mãi mỗi tháng = 1/6 số tin Giao dịch và Chăm sóc đã gửi hai
  tháng trước. Vì vậy tin cảm ơn sau khi nhận đơn phải chạy trước.
- Zalo khuyên tỉ lệ báo xấu dưới 0,1% mỗi ngày; nhiều thì OA bị hạ hạn mức.
- Zalo cho nhận 24/24 từ 30/12/2025 nhưng tiệm không gửi sau 20:00.
- Gửi qua API cần OA doanh nghiệp xác thực, gói Tăng trưởng hoặc Toàn diện.

Nguồn: https://zalo.solutions/news/thong-bao-ra-mat-zbs-template-message-giai-phap-tin-nhan-doanh-nghiep-theo-mau/cp1zx4bq8mzhhszgz0br1ocd ,
https://zalo.solutions/blog/co-che-danh-gia-chat-luong-va-quyen-loi-gui-zns/qsuhj60o4oteiy7rnrf0ohpe ,
https://zalo.solutions/oa/pricing

## Chưa làm trong v645

- Mốc 150 ngày "tin cuối không mã" của mời quay lại: tin Hậu mãi không có ưu đãi dễ
  bị báo xấu, để sau khi có số báo cáo.
- Điều kiện "đặt trước ít nhất N ngày" cho chương trình khuyến mãi (cần đưa ngày
  nhận vào phép tính giá ở cả web, quầy, Sales).
- Hạn mã sinh nhật dài hơn theo hạng: hiện cài bằng hai chương trình Ví quà theo hạng.
