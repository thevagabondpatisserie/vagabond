# Danh mục màn app /bep (PR 0, việc Nghệ sĩ công nghệ)

Tệp này do `cong_cu/thong_ke_ui_nghe_si.py` sinh ra. Đừng sửa tay: sửa công cụ rồi chạy lại.
"Đạt 100%" của các PR sau tính trên bảng này (bản 4 mục 6), không tính trên số tệp.

## Tóm tắt

- Số phần nguồn: 82. Số hàm màn (scr...): 280. Hộp thoại riêng ngoài bộ dùng chung: 83 hàm.
- Số ô trang chủ có định tuyến trong vgbGo: 136. Số nhóm trang chủ: 15.
- PR 1 nền: 8 màn.
- PR 2 Bán hàng và Quầy: 72 màn.
- PR 3 Kho, Sản xuất, Thu mua: 82 màn.
- PR 4 Kế toán, Tài chính: 44 màn.
- PR 5 Marketing và các màn còn lại: 69 màn.
- Chưa xếp, cần xếp tay: 5 màn.

Cách đọc cột: **Thành phần** là khung dùng chung màn đó dùng (PR nào sửa khung thì phải kiểm lại màn này). **Hộp thoại** là bộ hỏi dùng chung màn gọi, số trong ngoặc là số bảng trượt tự dựng trong màn. **Vai nhắc trong mã** chỉ để gợi ý chỗ giao diện đổi theo quyền; quyền thật xem docs/quyen-theo-phan-he.md.

## PR 1 nền (8 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrHome | (động) | - | 02 | thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | AP Giám đốc, AP Kiểm soát (FIN), AP Officer, Accounts Manager, Accounts User, Giám đốc, Purchase Manager, Purchase User, Quản lý người dùng, Sales Manager, Sales User, Shipper, System Manager |
| scrVclList | Việc cần làm | - | 02 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrNhom | (động) | - | 02 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrLogin | (không gọi frame) | - | 06 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrAccount | Tài khoản | - | 06 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở | - |
| scrHuongDan | Hướng dẫn chế biến | - | 32 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrSoTay | Sổ tay | - | 50 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrChuong | Chuông thông báo | - | 59 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |

## PR 2 Bán hàng và Quầy (72 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrDoanhSo | Doanh thu Sales | Bán hàng | 08 | thanh đáy, nút đầu trang, thẻ, dòng hub, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDsView | Chi tiết đơn | Bán hàng | 08 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hopKhung, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsNhapTay | Nhập đơn tay | Bán hàng | 08 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPosChonQuay | Tính tiền - hoá đơn bán hàng | Bán hàng | 09 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi | - |
| scrChotCa | Chốt ca | Bán hàng | 09 | thẻ, ô nhập, tiền | baoTin, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDoiSoatCa | Đối soát ca | Bán hàng | 09 | thẻ, bảng, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, số lớn, âm, 0 | - |
| scrPosQuay | Tính tiền ·  | Bán hàng | 09 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPosDs | (động) | Bán hàng | 10 | thẻ, dòng hub, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrPosBill | Hoá đơn ; Hoá đơn | Bán hàng | 10 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiSo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrOtp | Mã OTP quản lý | Bán hàng | 10 | thanh đáy, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCongNo | Công nợ phải thu | Bán hàng | 11 | thanh công cụ ds, thẻ, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrCnPhieu | Phiếu đề nghị thanh toán; Phiếu  | Bán hàng | 11 | thanh đáy, thẻ, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrPosChotCa | Chốt ca ·  | Bán hàng | 11 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrHopDong | Hợp đồng Event | Bán hàng | 11 | nút đầu trang, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrHdView | Chi tiết hợp đồng | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiCo, hopKhung, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdTao | Tạo hợp đồng | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, ô nhập | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMuaVuDs | Kiểm bánh theo mùa | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrMuaVu | Kiểm bánh theo mùa | Bán hàng | 11 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrHdThuTien | Phiếu thanh toán | Bán hàng | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiNhap | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdGhiSo | Ghi sổ hợp đồng | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiNhap, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdPhieu | Phiếu  | Bán hàng | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiNhap, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdSuaSoLieu | Sửa số liệu hợp đồng | Bán hàng | 11 | thanh đáy, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrKhuyenMai | Khuyến mãi - combo | Bán hàng | 13 | nút nổi, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDonTreo | Đơn còn treo | Bán hàng | 18 | thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrNopQuyXem | Phiếu nộp quỹ; Biên nhận nộp tiền mặt | Bán hàng | 21 | thẻ, ô nhập, tiền | baoTin, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNopQuySua | Sửa phiếu nộp quỹ; Sửa phiếu  | Bán hàng | 21 | thẻ, chip, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHopDongHub | Quản lý hợp đồng mua bán | Bán hàng | 22 | thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBaoGia | Báo giá | Bán hàng | 22 | nút đầu trang, thẻ, dòng hub, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrBgXem | Báo giá | Bán hàng | 22 | thanh đáy, thẻ, dòng hub, tiền | baoTin, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrMauBg | Mẫu báo giá | Bán hàng | 22 | thẻ, dòng hub | baoTin, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrBgSua | Sửa báo giá; (động) | Bán hàng | 22 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiSo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrThuVien | Thư viện báo giá | Bán hàng | 22 | nút đầu trang, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTvSua | (động) | Bán hàng | 22 | thanh đáy, thẻ, dòng hub, ô nhập | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrBgCaiDat | Câu chữ khung tờ báo giá | Bán hàng | 22 | thanh đáy, thẻ, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrDonHuy | Đơn đã huỷ chờ hoàn | Bán hàng | 29 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrBntDs | (động) | Bán hàng | 39 | thẻ, chip, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrBntTao | Lập biên nhận nộp tiền | Bán hàng | 39 | thẻ, ô nhập, tiền | baoTin, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPhieuHoanHuy | Danh sách phiếu hoàn tiền | Bán hàng | 40 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrPhLap | Lập phiếu hoàn tiền | Bán hàng | 40 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDuyetTang | (động) | Bán hàng | 41 | thanh đáy, thanh công cụ ds, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTangBaoCao | Báo cáo hàng tặng | Bán hàng | 41 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrSoDuTraTruoc | Số dư trả trước của khách | Bán hàng | 55 | thanh công cụ ds, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrSoDuKhach | Sổ trả trước | Bán hàng | 55 | thẻ, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrSoDuNap | Nạp tiền trả trước | Bán hàng | 55 | thẻ, ô nhập, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDoiSoatCk | (động) | Bán hàng | 56 | thanh công cụ ds, thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDatBan | (động) | Bán hàng | 57 | thanh công cụ ds | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrDonDatTruoc | (động) | Bán hàng | 63 | thanh công cụ ds | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDonDatTruocCt | (động) | Bán hàng | 63 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDonSiWeb | (động) | Bán hàng | 64 | thanh công cụ ds | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDonSiWebCt | (động) | Bán hàng | 64 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrKhachSiWeb | (động) | Bán hàng | 64 | thanh công cụ ds, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrGiaSi | (động) | Bán hàng | 64 | thanh đáy, thẻ, ảnh món, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrGmbInQr | In QR tại bàn | Bán hàng | 66 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBienTapMenu | Biên tập menu | Bán hàng | 68 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBtmNhom | (động) | Bán hàng | 68 | thẻ, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, số lớn, âm, 0, bàn phím ảo | - |
| scrBtmMon | (động) | Bán hàng | 68 | thanh đáy, thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, số lớn, âm, 0, bàn phím ảo | - |
| scrBtmDsBanh | Bánh trên tủ | Bán hàng | 68 | thẻ, ô tìm, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, bàn phím ảo | - |
| scrBtmBanhMon | (động) | Bán hàng | 68 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, số lớn, âm, 0, bàn phím ảo | - |
| scrBtmXuat | Xem và xuất bản | Bán hàng | 68 | thanh đáy, thẻ, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKhachSuKien | (động) | Bán hàng | 74 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrKhachSuKienCt | (động) | Bán hàng | 74 | thẻ, ô tìm, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrDonGiaoQuay | (không gọi frame) | Bán hàng | 76 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi | - |
| scrVanDon | Vận đơn | Giao hàng | 12 | thanh đáy, nút đầu trang, thẻ, dòng hub, ô nhập, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdCod | Đối soát COD | Giao hàng | 12 | thẻ, ô nhập, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdKy | Khách ký nhận | Giao hàng | 12 | thanh đáy, nút đầu trang, thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdView | Chi tiết vận đơn | Giao hàng | 12 | thẻ, ô nhập, tiền | baoTin, hoiNhap, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdTao | Tạo vận đơn | Giao hàng | 12 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdChiPhi | Chi phí xăng xe - sửa xe | Giao hàng | 12 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiNhap, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdGoiXe | Gọi xe  | Giao hàng | 12 | thanh đáy, thẻ, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrVdTuyen | Xếp tuyến | Giao hàng | 12 | thẻ, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrVdPhiApp | Phí giao hàng book app | Giao hàng | 12 | thẻ, ô nhập, bảng | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrCanhBaoTT | Cảnh báo thanh toán | Giao hàng | 21 | thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |

## PR 3 Kho, Sản xuất, Thu mua (82 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrMRList | (động) | Đặt hàng | 03 | nút nổi, chip | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrStep1 | (động) | Đặt hàng | 04 | thanh đáy, thẻ, ô nhập | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrStep2 | (không gọi frame) | Đặt hàng | 04 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi | - |
| scrStep3 | Danh sách đã chọn | Đặt hàng | 04 | thanh đáy, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrStep4 | Xem lại phiếu | Đặt hàng | 04 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, bàn phím ảo | - |
| scrRndList | Mua hàng phát sinh | Đặt hàng | 07 | nút nổi, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrRndNew | Yêu cầu mua hàng phát sinh | Đặt hàng | 07 | thanh đáy, thẻ | pickDate | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrRndDoc | Phiếu mua phát sinh | Đặt hàng | 07 | thanh đáy, thẻ, tiền | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrDeNghiChi | Đề nghị chi | Đặt hàng | 16 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTTNB | Thanh toán nội bộ | Đặt hàng | 16 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrStock | Tra tồn kho | Kiểm kê | 05 | thẻ, chip, tiền | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKkList | Kiểm kê | Kiểm kê | 06 | nút nổi | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrKkNew | Phiếu kiểm kê mới | Kiểm kê | 06 | thanh đáy, thẻ | pickDate, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở | - |
| scrKkDoc | Kiểm kê | Kiểm kê | 06 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrKkPost | Ghi sổ kiểm kê | Kiểm kê | 06 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTonChang | Tồn kho theo chặng | Kiểm kê | 37 | chip, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrHangVeKho | Hàng chuyển về kho tôi | Nhập kho | 03 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrRecvList | Nhập kho | Nhập kho | 06 | nút đầu trang | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrRecvDoc | Nhập kho | Nhập kho | 06 | thanh đáy, nút đầu trang, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNhpDon | Nhận hàng; Nhận hàng đợt  | Nhập kho | 06 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNhanBanh | Nhận bánh | Nhập kho | 31 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrNhanDcXacNhan | Xác nhận nhận hàng | Nhập kho | 45 | ô nhập | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMRView | (động) | Sản xuất | 03 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrRecvTransfer | Nhận hàng ; (động) | Sản xuất | 03 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, bàn phím ảo | - |
| scrKitchen | Bảng bếp; Bảng bếp  | Sản xuất | 05 | thanh đáy, thẻ, chip | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrMfgList | Lệnh sản xuất | Sản xuất | 05 | nút nổi, chip, ảnh món | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrMfgNew | Tạo lệnh sản xuất | Sản xuất | 05 | thanh đáy, chip, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrMfgBtp | Bán thành phẩm cần làm | Sản xuất | 05 | thanh đáy, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrMfgView | Lệnh sản xuất | Sản xuất | 05 | thanh đáy, thẻ, ảnh món | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrMfgDeclare | Khai nguyên liệu | Sản xuất | 05 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrMfgLabel | In tem HACCP | Sản xuất | 05 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, bàn phím ảo | - |
| scrCongThuc | Danh mục công thức | Sản xuất | 26 | thanh đáy, nút nổi, chip, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrCongThucXem | Công thức | Sản xuất | 26 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrCongThucNhatKy | Nhật ký sửa công thức | Sản xuất | 26 | thẻ, chip | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrCongThucDaXoa | Công thức đã xoá | Sản xuất | 26 | thẻ, chip | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCongThucSua | (động) | Sản xuất | 26 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrHuongDanSoan | Hướng dẫn chế biến | Sản xuất | 32 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDonTiec | Đơn tiệc / B2B | Sản xuất | 33 | chip, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTiecXem | Đơn tiệc | Sản xuất | 33 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTiecXuat | Xuất NVL cho tiệc | Sản xuất | 33 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrKeHoachSX | Kế hoạch sản xuất | Sản xuất | 38 | thanh đáy, thẻ, chip, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrKhsxDsPhieu | Các phiếu kế hoạch | Sản xuất | 38 | - | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrDxDs | Phiếu đề xuất công thức | Sản xuất | 72 | nút nổi, thanh công cụ ds | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDxSua | (động) | Sản xuất | 72 | thanh đáy, thẻ, chip, ô nhập, bảng, tiền | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonMua | Đơn mua hàng | Thu mua | 16 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDonMuaXem | Đơn mua hàng | Thu mua | 16 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDuyetYc | Duyệt yêu cầu mua | Thu mua | 16 | thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDuyetYcXem | Duyệt yêu cầu mua; Duyệt  | Thu mua | 16 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNoPhaiTra | Công nợ phải trả | Thu mua | 16 | thanh công cụ ds, thẻ, tiền | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrCntPhiDt | Cấn trừ phí đối tác | Thu mua | 16 | thanh đáy, thẻ, chip | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrCntTruocErp | Đã trả trước khi lên ERP | Thu mua | 16 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHoSoTTView | Hồ sơ  | Thu mua | 19 | thanh đáy, thẻ, dòng hub, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrNoiDungCK | Nội dung chuyển khoản | Thu mua | 19 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, số lớn, âm, 0 | - |
| scrNcc | Nhà cung cấp | Thu mua | 20 | thẻ, dòng hub, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNccXem | Nhà cung cấp; (động) | Thu mua | 20 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNccGan | Gán nhà cung cấp | Thu mua | 20 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChon, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTimGiaoDich | Tìm giao dịch | Thu mua | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBangGia | Bảng giá mua | Thu mua | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrGomMua | Gom yêu cầu mua | Thu mua | 70 | nút đầu trang, thẻ, ô tìm | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrDuChi | Dự chi công nợ | Thu mua | 71 | nút đầu trang, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDuChiXem | Dự chi công nợ; Dự chi  | Thu mua | 71 | thanh đáy, nút đầu trang, thẻ, ô tìm, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDuChiThem | Sửa dự chi; (động) | Thu mua | 71 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrLichChi | (động) | Thu mua | 71 | thanh đáy, thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrLichGoiY | Máy gợi ý lịch chi | Thu mua | 71 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrXkChonHang | Thêm hàng | Xuất kho | 03 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkHuyList | Xuất huỷ | Xuất kho | 03 | nút nổi | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkHuyNew | Lập phiếu xuất huỷ | Xuất kho | 03 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkCkList | Xuất điều chuyển | Xuất kho | 03 | nút nổi | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkCkNew | Lập phiếu điều chuyển | Xuất kho | 03 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkView | Phiếu xuất; (động) | Xuất kho | 03 | - | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrXkNbList | Xuất dùng nội bộ | Xuất kho | 45 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkNbNew | Lập phiếu xuất dùng nội bộ | Xuất kho | 45 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkNbView | Phiếu xuất dùng nội bộ | Xuất kho | 45 | - | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrXkTraList | Xuất trả nhà cung cấp | Xuất kho | 45 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkTraNew | Lập phiếu trả hàng | Xuất kho | 45 | ô nhập | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkTraView | Phiếu trả hàng | Xuất kho | 45 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkSiList | Xuất bán sỉ | Xuất kho | 45 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkSiNew | Lập phiếu giao hàng | Xuất kho | 45 | ô nhập | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkSiView | Phiếu giao hàng | Xuất kho | 45 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkPvList | Xuất kho phục vụ bán hàng | Xuất kho | 46 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkPvNew | Chốt kho điểm bán | Xuất kho | 46 | ảnh món, ô nhập | xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkPvView | Phiếu xuất kho phục vụ bán hàng | Xuất kho | 46 | ô nhập | hoiChu, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |

## PR 4 Kế toán, Tài chính (44 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrPayList | Duyệt phiếu chi | Kế toán | 04 | thẻ, chip, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrPayView | (động) | Kế toán | 04 | thanh đáy, nút đầu trang, thẻ, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | AP Kiểm soát (FIN) |
| scrHoanTien | Phiếu hoàn tiền (Cash-back) | Kế toán | 11 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrNccTao | Tạo nhà cung cấp | Kế toán | 16 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrHdBan | Hoá đơn bán ra | Kế toán | 16 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrHdMua | Hoá đơn mua vào | Kế toán | 16 | thẻ, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrDoiChieuMua | Đối chiếu hoá đơn mua | Kế toán | 18 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDcmXem | Đối chiếu ; Đối chiếu | Kế toán | 18 | thanh đáy, thẻ, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrDcmHachToan | Hạch toán ; Hạch toán | Kế toán | 18 | thanh đáy, thẻ, ảnh món, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrHoSoTT | Hồ sơ thanh toán | Kế toán | 19 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrViSaoThieu | Vì sao thiếu hoá đơn | Kế toán | 19 | thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrHoSoTTTao | (động); Lập hồ sơ thanh toán | Kế toán | 19 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHoanUngTao | Lập hồ sơ hoàn ứng | Kế toán | 19 | thanh đáy, thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHuSepay | Sao kê quỹ tạm ứng | Kế toán | 19 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrChiCongTyTao | Chi từ TK công ty | Kế toán | 19 | thanh đáy, thẻ, ô nhập, bảng, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTaiSan | Tài sản | Kế toán | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTaiSanXem | Tài sản | Kế toán | 21 | thẻ, dòng hub, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKhauHao | Khấu hao | Kế toán | 21 | thẻ, dòng hub, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrButToan | Bút toán | Kế toán | 21 | thẻ, dòng hub, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrBtLap | Lập bút toán | Kế toán | 21 | thẻ, ô nhập, tiền | hoiNgay | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrButToanXem | Bút toán | Kế toán | 21 | thẻ, ô nhập, tiền | baoTin, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKhopSepay | Khớp SePay thủ công | Kế toán | 23 | thẻ, chip, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTraTruocTao | Thanh toán trước cho NCC | Kế toán | 30 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiChon | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTruKho | (động) | Kế toán | 49 | thanh công cụ ds, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDsvn | Đối soát nhà cung cấp | Kế toán | 52 | thanh đáy, thanh công cụ ds, thẻ, chip, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrDsvnBill | Bill chưa khớp đối tác | Kế toán | 52 | thanh công cụ ds, thẻ, chip, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDsvnThu | Hộp thư đối soát | Kế toán | 52 | thẻ, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrDsvnTai | Nhận file đối soát | Kế toán | 52 | thanh đáy, thẻ, chip, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsvnCt | Nguồn đối soát | Kế toán | 52 | thanh đáy, thẻ, chip, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrGiaVonTam | (động) | Kế toán | 53 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrQuyTm | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | hoiChu, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyChotDau | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyKiem | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyNop | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCp242 | (động) | Kế toán | 79 | thanh đáy, thẻ, ảnh món, ô tìm, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrDsMeta | (động) | Kế toán | 80 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDsMetaThang | (động) | Kế toán | 80 | thẻ, ô nhập, tiền | hoiChu, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTcTongQuan | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcTien | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcDong | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcDuBao | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcLaiLo | (động) | Tài chính | 61 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi | - |
| scrTcTiLe | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcCaiDat | (động) | Tài chính | 61 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |

## PR 5 Marketing và các màn còn lại (69 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrBaoCao | Báo cáo | Báo cáo | 14 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrBaoCaoXem | Báo cáo  | Báo cáo | 14 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrBangSang | Việc hôm nay | Báo cáo | 47 | nút đầu trang, thẻ, chip, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrViecGoiY | Việc được giao | Báo cáo | 47 | thanh đáy, thẻ, ô nhập | hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrCaiDatCuoiNgay | Cuối ngày | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDiemBan | Điểm bán | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDiemBanSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrKhoaSo | Khoá sổ | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrPtThanhToan | Phương thức thanh toán | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrPtSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrQuyenQuay | Quyền tại quầy | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrHangKhach | Hạng thành viên | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrHangSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXetLaiHang | Xét lại hạng | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTaiKhoan | Tài khoản nhận tiền | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTaiKhoanSua | (động) | Cài đặt | 17 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở | - |
| scrDanhMuc | Danh mục sản phẩm | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrSePay | SePay | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrNhapSaoKe | Nhập sao kê ngân hàng | Cài đặt | 17 | thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrThongBao | Thông báo trên điện thoại | Cài đặt | 17 | thẻ | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrCaiDatWeb | Trang đặt bánh web | Cài đặt | 17 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCaiDatKho | Ngưỡng kho | Cài đặt | 17 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrMayIn | Máy in | Cài đặt | 18 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrMayIn0 | (không gọi frame) | Cài đặt | 18 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrMayInSua | (động) | Cài đặt | 18 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNguoiDung | Quản lý người dùng | Cài đặt | 20 | thẻ, dòng hub, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrNguoiDungXem | Người dùng | Cài đặt | 20 | thẻ | baoTin, hoiChon, hoiChonNhieu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrQuyen | Quản lý quyền | Cài đặt | 20 | thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrQuyenXem | Gói chức vụ | Cài đặt | 20 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrDonChungTuThu | Dọn chứng từ thử | Cài đặt | 24 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrChuyenPhantom | Chuyển Phantom | Cài đặt | 24 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrBoAo | Bỏ ảo một mã | Cài đặt | 24 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTroLyCaiDat | Trợ lý | Cài đặt | 35 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrMauIn | Mẫu in ấn | Cài đặt | 36 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCaiDatLoi | Cài đặt lõi và API | Cài đặt | 51 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBangGiaDiem | (động) | Cài đặt | 65 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTuDongHoa | Cài đặt tự động hoá | Cài đặt | 69 | nút đầu trang, thẻ, chip | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrKhachHang | Danh sách khách hàng | Khách hàng & Marketing | 11 | thẻ, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrKhachChiTiet | Khách hàng | Khách hàng & Marketing | 18 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTqDot | Tặng quà khách VIP | Khách hàng & Marketing | 34 | nút nổi | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTqDs | (động) | Khách hàng & Marketing | 34 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTqSua | Phiếu tặng quà | Khách hàng & Marketing | 34 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTqThemLoat | Thêm khách vào đợt | Khách hàng & Marketing | 34 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTqLapDot | (động); Đợt tặng quà mới | Khách hàng & Marketing | 34 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrTqDan | (không gọi frame) | Khách hàng & Marketing | 34 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrCrmHoSo | Chăm sóc khách | Khách hàng & Marketing | 58 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrCrmGoi | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCrmNhom | (động) | Khách hàng & Marketing | 58 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCrmDongY | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrCrmCdDs | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCrmCd | (động) | Khách hàng & Marketing | 58 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | System Manager |
| scrCrmHqDs | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrCrmHieuQua | (động) | Khách hàng & Marketing | 58 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrCrmZalo | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCrmZaloTin | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBaiDang | (động) | Khách hàng & Marketing | 75 | thanh đáy, nút đầu trang | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBaiDangSoan | Bài đăng | Khách hàng & Marketing | 75 | thanh đáy, nút đầu trang, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrMonDiKem | (động) | Khách hàng & Marketing | 78 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrQcMeta | (động) | Khách hàng & Marketing | 80 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrKPI | KPI và hoa hồng | Nhân sự | 44 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrKPICt | Phiếu KPI; Phiếu KPI ·  | Nhân sự | 44 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKPICau | Bảng chỉ tiêu; Bảng chỉ tiêu và bậc hoa hồng | Nhân sự | 44 | thẻ, bảng, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrKPIToi | KPI của tôi | Nhân sự | 44 | thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKPITuKhai | Phiếu duyệt commission | Nhân sự | 44 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTuyenDung | (động) | Nhân sự | 60 | thanh công cụ ds, thẻ, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrTdChiTiet | (động) | Nhân sự | 60 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTdViTri | (động) | Nhân sự | 60 | thanh đáy, thẻ, ô nhập | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTdThemHs | (động) | Nhân sự | 60 | thanh đáy, thẻ, ô nhập | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrHhgt | (động) | Nhân sự | 67 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |

## Chưa xếp, cần xếp tay (5 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrKhungDs | Danh sách; (động) | - | 15 | nút nổi, khuôn ds, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrKgTao | (động) | - | 15 | thanh đáy, khuôn ds | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrNopQuy | Nộp quỹ tiền mặt | - | 21 | thẻ, chip, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrNopQuyTao | Lập phiếu nộp quỹ | - | 21 | thẻ, ô nhập, tiền | baoTin, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrMauIn0 | (không gọi frame) | - | 36 | - | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |

## Hộp thoại

Bộ dùng chung (07-hop-thoai.js và 00-nen.js): hopKhung, hoiChon, hoiChonNhieu, hoiChu, hoiSo, hoiNgay, hoiCo, baoTin, hoiNhap, xacNhan, pickDate, sheet, confirmSheet.

| Hộp thoại chung | Số chỗ gọi trong app |
|---|--:|
| hopKhung | 28 |
| hoiChon | 34 |
| hoiChonNhieu | 7 |
| hoiChu | 59 |
| hoiSo | 17 |
| hoiNgay | 5 |
| hoiCo | 67 |
| baoTin | 612 |
| hoiNhap | 39 |
| xacNhan | 51 |
| pickDate | 4 |
| sheet | 121 |
| confirmSheet | 157 |

Hàm tự dựng bảng trượt (lớp `sh`) hoặc gọi hopKhung, không phải hàm màn:

| Hàm | Phần | Số bảng trượt tự dựng |
|---|---|--:|
| promptSheet | 00 | 1 |
| loadTemplate | 04 | 1 |
| goiYSheet | 04 | 1 |
| stkSheetHtml | 05 | 1 |
| qtySheet | 05 | 1 |
| mfgPickItem | 05 | 1 |
| mfgSheetHoanTat | 05 | 1 |
| mfgSheetKe | 05 | 1 |
| kkCountSheet | 06 | 1 |
| rndLineSheet | 07 | 1 |
| timDonChay | 08 | 0 |
| themMonSheet | 08 | 1 |
| posSheetMon | 09 | 1 |
| sheetTimKhach | 09 | 1 |
| posSheetKhachNo | 09 | 1 |
| posMoGhiChuMon | 09 | 1 |
| posMoTuyChon | 09 | 1 |
| posSheetDoTien | 09 | 1 |
| posQrSheet | 09 | 1 |
| posLuuDon | 09 | 1 |
| posSheetOtp | 10 | 1 |
| posHuyCoTien | 10 | 1 |
| cnMoUnc | 11 | 0 |
| khSheetHang | 11 | 1 |
| hoanVeForm | 11 | 0 |
| hdFormNguoiKy | 11 | 0 |
| htFormTuChoi | 11 | 0 |
| htMbBiz | 11 | 0 |
| mvXemNgay | 11 | 0 |
| hdKhacBietHop | 11 | 0 |
| hdXemLichSu | 11 | 0 |
| paChiTiet | 12 | 0 |
| posSheetChonKm | 13 | 1 |
| posSheetCombo | 13 | 1 |
| posSheetMaVc | 13 | 1 |
| kmSheetDenBu | 13 | 1 |
| kmSheetDonDau | 13 | 1 |
| kmSheetCtkm | 13 | 1 |
| kmSheetCombo | 13 | 1 |
| kmSheetXuatLo | 13 | 1 |
| kmSheetLo | 13 | 1 |
| posSheetChonCombo | 17 | 1 |
| khSheetSua | 18 | 1 |
| khSheetSoDiem | 18 | 1 |
| dcmChonDonVi | 18 | 1 |
| hsMoChonBenNhan | 19 | 1 |
| huXemVaNoiPhieu | 19 | 0 |
| hsChonHdSau | 19 | 0 |
| nccTkHop | 20 | 0 |
| cnHoiUnc | 21 | 0 |
| nqKyTay | 21 | 0 |
| vgbChonMon | 22 | 1 |
| bgHoiLoiNhan | 22 | 1 |
| bgTaoKhach | 22 | 0 |
| bgFormHopDong | 22 | 0 |
| bgMoiHoi | 22 | 1 |
| bgChonKhach | 22 | 1 |
| hqMo | 28 | 1 |
| dhMo | 29 | 1 |
| nbChonMon | 31 | 1 |
| ttnSheet | 42 | 1 |
| xktSheetTimKhach | 45 | 1 |
| bsGiao | 47 | 0 |
| bsBoQua | 47 | 0 |
| cdlChonZalo | 51 | 1 |
| cdlChonTinZalo | 51 | 1 |
| gvtSuaHeSo | 53 | 1 |
| gvtChiTiet | 53 | 1 |
| gvtChonNhom | 53 | 1 |
| gvtThemNl | 53 | 1 |
| sdtChonTkGd | 55 | 1 |
| dbMoSheet | 57 | 1 |
| crmMoSheet | 58 | 1 |
| tdMoSheet | 60 | 1 |
| ddtMoSheet | 63 | 1 |
| bsiMoSheet | 64 | 1 |
| bsiSheetTimKhach | 64 | 1 |
| bsiSheetThemMon | 64 | 1 |
| gmbMoDs | 66 | 1 |
| gmbTuChoi | 66 | 1 |
| tdhSua | 69 | 1 |
| dqMoHop | 76 | 1 |
| gmbMoChonChuong | 77 | 1 |

## Ô trang chủ trỏ ra ngoài app hoặc qua khuôn danh sách

Các khoá sau không mở hàm scr trực tiếp (mở trang khác, khuôn danh sách kgMo, hoặc chỉ báo tin): KBD, BTPO, KHPO, KHHDM.

Hàm tổng đài bị bỏ khỏi phép dò đường (nhắc quá 25 màn): sdGhepDong, sdKhai, vgbGo.

