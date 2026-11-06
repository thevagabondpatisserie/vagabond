# Đối soát tự động qua hộp thư doisoat@ (v641)

Anh Việt duyệt 06/11/2026 (8 ảnh mẫu và 10 tin Zalo, PR v641). Tài liệu này cho
kế toán, giám đốc và người làm kỹ thuật sau.

## Luồng

1. Đối tác gửi thư báo cáo tới hộp thư công ty.
2. Bộ lọc Roundcube gửi BẢN SAO nguyên vẹn sang `doisoat@thevagabondpatisserie.com`.
3. Máy chủ ERP đọc hộp doisoat@ mỗi 15 phút qua IMAP: chỉ đọc, không đánh dấu, không xoá. Thư gốc (.eml) lưu chỉ đọc.
4. Xác thực: thư phải có chữ ký số DKIM hợp lệ của đúng tên miền đối tác (bảng "Người gửi tin cậy" ở Cài đặt lõi). Sai thì chặn, giữ để tra, báo Zalo.
5. Đọc tệp đính kèm bằng các mẫu sẵn có (`doi_soat_mau`), qua đúng một lối với tải tay.
6. Khớp tiền với ngân hàng (SePay), nối chứng từ.
7. Kế toán bấm "Xác nhận đã đối soát" khi năm bước trước xanh.

Sáu bước trên app: 1 Nhận thư, 2 Xác thực, 3 Đọc tệp, 4 Khớp tiền, 5 Nối chứng từ, 6 Kế toán xác nhận.

## Tải tay

Vẫn giữ, nhưng "có duyệt": người tải ghi lý do, nguồn mang nhãn "Chờ duyệt" và
vào Việc cần làm của giám đốc. Người tải không tự duyệt được. Từ chối thì các
dòng thôi tính (giữ để tra). Khi thư thật của đối tác về với cùng tệp, nguồn
tải tay tự chuyển thành "Từ thư".

Nguồn tải tay trước v641 giữ nguyên, hiện là "Trước khi có thư". Không xoá, không sửa.

## Cài đặt (Cài đặt lõi, tab Hoá đơn và kế toán, mục Hộp thư đối soát)

- Địa chỉ, mật khẩu hộp thư (anh tự dán), máy chủ IMAP (để trống là dùng máy chủ của hộp erp@), cổng, thư mục.
- Mật khẩu mở PDF sao kê thẻ Shinhan, mật khẩu ZIP Shinhan POS.
- Bảng Người gửi tin cậy: đối tác, tên miền, bắt buộc chữ ký (tắt là vẫn nhận nhưng giám đốc duyệt từng thư).
- Bảng Lịch thư dự kiến: nguồn, hằng ngày hay hằng tháng, hạn giờ, hạn ngày, chỉ ngày làm việc.
- Biểu phí thẻ Shinhan POS theo hợp đồng (nội địa mặc định 1,44%), ngưỡng báo phí, ngưỡng báo lệch tiền.

Bật "Bật đọc hộp thư đối soát" sau khi khai đủ, rồi bấm "Thử kết nối hộp thư" trên màn Đối soát nhà cung cấp.

## Tin Zalo (tích nhóm nhận ở Cài đặt, mục Zalo)

| Mã | Tin | Khi nào |
|---|---|---|
| kt_ds_thu_gia_danh | Thư đối soát giả danh bị chặn | Ngay khi đọc thư |
| kt_ds_thieu_thu | Thư đối soát chưa về | 12:30, nhắc 17:00 |
| ht_ds_hop_thu_loi | Không đọc được hộp thư | Lỗi 2 lần liên tiếp |
| kt_ds_tep_loi | Tệp từ thư không đọc được | Ngay khi đọc |
| kt_ds_lech_tien | Tiền về khác số đối tác báo | Ngay khi đối chiếu |
| kt_ds_chua_thay_tien | Chưa thấy tiền về | 08:30 |
| kt_ds_phi_cao | Phí cao hơn biểu phí hợp đồng | Ngay khi đọc báo cáo Shinhan POS |
| kt_ds_don_thieu_erp | Giao dịch đối tác đã thu mà ERP chưa có đơn | 08:30 |
| bgd_ds_tai_tay | Tệp tải tay chờ giám đốc duyệt | Ngay khi tải |

Tin "lần quẹt thẻ thiếu chứng từ" (ảnh 7) chưa làm ở v641: cần màn nối chứng từ
cho từng lần quẹt thẻ trước, nếu không tin nhắc mà không có chỗ làm.

## Kỹ thuật

- `vagabond/doi_soat_thu.py`: đọc IMAP, quyết định nhận thư, sáu bước, thư chưa về, biểu phí, tin Zalo.
- `vagabond/doi_soat_dkim.py`: kiểm chữ ký DKIM tự viết (rsa-sha256, simple/relaxed), không phụ thuộc thư viện.
- Doctype mới: `Vagabond Doi Soat Thu` (sổ thư), hai bảng con của Cài đặt.
- Ca kiểm: `thu_doi_soat_thu_641.py` (thư mẫu dkimpy ký thật trong `mau_doi_soat/dkim/`), `hanh_vi/doi_soat_hop_thu_641.js`.
