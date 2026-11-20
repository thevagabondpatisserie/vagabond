# Danh mục màn app /bep (PR 0, việc Nghệ sĩ công nghệ)

Tệp này do `cong_cu/thong_ke_ui_nghe_si.py` sinh ra. Đừng sửa tay: sửa công cụ rồi chạy lại.
"Đạt 100%" của các PR sau tính trên bảng này (bản 4 mục 6), không tính trên số tệp.

## Tóm tắt

- Số phần nguồn: 82. Số hàm màn (scr...): 280. Hộp thoại riêng ngoài bộ dùng chung: 83 hàm.
- Màn máy chưa dò ra thành phần nào (ghi chưa xác định): 1.
- Số ô trang chủ có định tuyến trong vgbGo: 136. Số nhóm trang chủ: 15.
- PR 1 nền: 8 màn.
- PR 2 Bán hàng và Quầy: 72 màn.
- PR 3 Kho, Sản xuất, Thu mua: 82 màn.
- PR 4 Kế toán, Tài chính: 44 màn.
- PR 5 Marketing và các màn còn lại: 69 màn.
- Chưa xếp, cần xếp tay: 5 màn.

Cách đọc cột: **Thành phần** là khung dùng chung màn đó dùng (PR nào sửa khung thì phải kiểm lại màn này). **Hộp thoại** là bộ hỏi dùng chung màn gọi, số trong ngoặc là số bảng trượt tự dựng trong màn. Ba cột này đọc cả thân màn lẫn các hàm vẽ phụ màn gọi (sâu tối đa 4 tầng, không sang màn khác). Ô ghi **chưa xác định** nghĩa là máy không dò ra gì, KHÔNG có nghĩa là màn không dùng: người làm phải mở màn xem và coi như màn chịu ảnh hưởng của mọi khung chung. **Vai nhắc trong mã** chỉ để gợi ý chỗ giao diện đổi theo quyền; quyền thật xem docs/quyen-theo-phan-he.md.

## PR 1 nền (8 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrHome | (động) | - | 02 | nút đầu trang, thẻ, dòng hub, ô nhập, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Giám đốc, AP Kiểm soát (FIN), AP Officer, Accounts Manager, Accounts User, Bếp phó, Bếp trưởng, Giám đốc, Kế toán, Manufacturing Manager, Manufacturing User, Mua hàng R&D, Purchase Manager, Purchase User, Quản lý cửa hàng, Quản lý người dùng, Quầy Bar, Sales Manager, Sales User, Shipper, Stock Manager, Stock User, System Manager, Thu mua, VGB - Quản lý công thức, VGB - Quản lý cửa hàng |
| scrVclList | Việc cần làm | - | 02 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChu, hoiCo (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNhom | (động) | - | 02 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200% | - |
| scrLogin | (không gọi frame) | - | 06 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrAccount | Tài khoản | - | 06 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrHuongDan | Hướng dẫn chế biến | - | 32 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrSoTay | Sổ tay | - | 50 | chip, ô nhập, bảng | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrChuong | Chuông thông báo | - | 59 | thẻ, chip | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |

## PR 2 Bán hàng và Quầy (72 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrDoanhSo | Doanh thu Sales | Bán hàng | 08 | thanh đáy, nút đầu trang, thẻ, dòng hub, ô nhập, tiền | baoTin, hopKhung, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsView | Chi tiết đơn | Bán hàng | 08 | thanh đáy, thẻ, ô nhập, bảng, tiền | baoTin, confirmSheet, hopKhung, sheet, xacNhan (+4) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Giám đốc, AP Kiểm soát (FIN), Accounts Manager, Accounts User, Giám đốc, Purchase Manager, Purchase User, System Manager, Thu mua |
| scrDsNhapTay | Nhập đơn tay | Bán hàng | 08 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, sheet, xacNhan (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPosChonQuay | Tính tiền - hoá đơn bán hàng | Bán hàng | 09 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi | Sales Manager, Sales User, System Manager |
| scrChotCa | Chốt ca | Bán hàng | 09 | thẻ, ô nhập, tiền | baoTin, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDoiSoatCa | Đối soát ca | Bán hàng | 09 | thẻ, bảng, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, số lớn, âm, 0 | - |
| scrPosQuay | Tính tiền ·  | Bán hàng | 09 | thanh đáy, thẻ, dòng hub, ảnh món, ô nhập, bảng, tiền | baoTin, confirmSheet, hoiSo (+15) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPosDs | (động) | Bán hàng | 10 | thẻ, dòng hub, ảnh món, ô nhập, tiền | baoTin, hopKhung (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPosBill | Hoá đơn ; Hoá đơn | Bán hàng | 10 | thanh đáy, thẻ, ô nhập, bảng, tiền | baoTin, confirmSheet, hoiSo, hopKhung, sheet (+6) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Accounts Manager, Accounts User, System Manager |
| scrOtp | Mã OTP quản lý | Bán hàng | 10 | thanh đáy, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCongNo | Công nợ phải thu | Bán hàng | 11 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, confirmSheet, hopKhung, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCnPhieu | Phiếu đề nghị thanh toán; Phiếu  | Bán hàng | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChu, hoiCo, hoiSo, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPosChotCa | Chốt ca ·  | Bán hàng | 11 | thanh đáy, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrHopDong | Hợp đồng Event | Bán hàng | 11 | nút đầu trang, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrHdView | Chi tiết hợp đồng | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, chip, ô nhập, tiền | baoTin, confirmSheet, hoiChu, hoiCo, hopKhung, sheet (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Giám đốc, Bếp phó, Giám đốc, Manufacturing Manager, System Manager |
| scrHdTao | Tạo hợp đồng | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, ô nhập | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMuaVuDs | Kiểm bánh theo mùa | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiNhap | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrMuaVu | Kiểm bánh theo mùa | Bán hàng | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiCo, hoiNhap, hopKhung, sheet, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdThuTien | Phiếu thanh toán | Bán hàng | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiNhap | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdGhiSo | Ghi sổ hợp đồng | Bán hàng | 11 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiNhap, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdPhieu | Phiếu  | Bán hàng | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiNhap, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHdSuaSoLieu | Sửa số liệu hợp đồng | Bán hàng | 11 | thanh đáy, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrKhuyenMai | Khuyến mãi - combo | Bán hàng | 13 | nút nổi, thẻ, ô nhập, tiền | baoTin, confirmSheet, sheet (+7) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonTreo | Đơn còn treo | Bán hàng | 18 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiNhap, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNopQuyXem | Phiếu nộp quỹ; Biên nhận nộp tiền mặt | Bán hàng | 21 | nút đầu trang, thẻ, ô nhập, tiền | baoTin, hoiChu, hoiCo, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNopQuySua | Sửa phiếu nộp quỹ; Sửa phiếu  | Bán hàng | 21 | thẻ, chip, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHopDongHub | Quản lý hợp đồng mua bán | Bán hàng | 22 | thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrBaoGia | Báo giá | Bán hàng | 22 | nút đầu trang, thẻ, dòng hub, ô nhập, tiền | baoTin, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBgXem | Báo giá | Bán hàng | 22 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChu, hoiCo, hoiNgay, hopKhung, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrMauBg | Mẫu báo giá | Bán hàng | 22 | thẻ, dòng hub | baoTin, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrBgSua | Sửa báo giá; (động) | Bán hàng | 22 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChu, hoiCo, hoiSo, hopKhung, sheet (+4) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrThuVien | Thư viện báo giá | Bán hàng | 22 | nút đầu trang, thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTvSua | (động) | Bán hàng | 22 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiCo (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBgCaiDat | Câu chữ khung tờ báo giá | Bán hàng | 22 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrDonHuy | Đơn đã huỷ chờ hoàn | Bán hàng | 29 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, confirmSheet, hopKhung, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBntDs | (động) | Bán hàng | 39 | thẻ, chip, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrBntTao | Lập biên nhận nộp tiền | Bán hàng | 39 | nút đầu trang, thẻ, ô nhập, tiền | baoTin, hoiChu, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrPhieuHoanHuy | Danh sách phiếu hoàn tiền | Bán hàng | 40 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrPhLap | Lập phiếu hoàn tiền | Bán hàng | 40 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, hopKhung, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDuyetTang | (động) | Bán hàng | 41 | thanh đáy, thanh công cụ ds, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTangBaoCao | Báo cáo hàng tặng | Bán hàng | 41 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrSoDuTraTruoc | Số dư trả trước của khách | Bán hàng | 55 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrSoDuKhach | Sổ trả trước | Bán hàng | 55 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrSoDuNap | Nạp tiền trả trước | Bán hàng | 55 | thẻ, ô nhập, tiền | baoTin, xacNhan (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDoiSoatCk | (động) | Bán hàng | 56 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDatBan | (động) | Bán hàng | 57 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonDatTruoc | (động) | Bán hàng | 63 | thanh công cụ ds, thẻ, ảnh món, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonDatTruocCt | (động) | Bán hàng | 63 | thanh đáy, thẻ, ảnh món, ô nhập, tiền |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonSiWeb | (động) | Bán hàng | 64 | thanh công cụ ds, thẻ, ảnh món, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonSiWebCt | (động) | Bán hàng | 64 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKhachSiWeb | (động) | Bán hàng | 64 | thanh công cụ ds, thẻ, ảnh món, ô tìm, ô nhập, tiền | baoTin (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrGiaSi | (động) | Bán hàng | 64 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | confirmSheet (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrGmbInQr | In QR tại bàn | Bán hàng | 66 | thanh đáy, thẻ, ô nhập | hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrBienTapMenu | Biên tập menu | Bán hàng | 68 | nút đầu trang, thẻ, ô nhập, bảng, tiền | confirmSheet, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBtmNhom | (động) | Bán hàng | 68 | nút đầu trang, thẻ, ô tìm, ô nhập, tiền | confirmSheet, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBtmMon | (động) | Bán hàng | 68 | thanh đáy, thẻ, ô nhập, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBtmDsBanh | Bánh trên tủ | Bán hàng | 68 | thẻ, ô tìm, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrBtmBanhMon | (động) | Bán hàng | 68 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBtmXuat | Xem và xuất bản | Bán hàng | 68 | thanh đáy, thẻ, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKhachSuKien | (động) | Bán hàng | 74 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrKhachSuKienCt | (động) | Bán hàng | 74 | thẻ, ô tìm, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrDonGiaoQuay | Đơn giao của quầy ·  | Bán hàng | 76 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | confirmSheet (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVanDon | Vận đơn | Giao hàng | 12 | thanh đáy, nút đầu trang, thẻ, dòng hub, ô nhập, bảng, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Accounts User, Purchase User, Sales Manager, Sales User, Shipper, System Manager |
| scrVdCod | Đối soát COD | Giao hàng | 12 | thẻ, ô nhập, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Accounts User, Purchase User, Sales Manager, Sales User, System Manager |
| scrVdKy | Khách ký nhận | Giao hàng | 12 | thanh đáy, nút đầu trang, thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrVdView | Chi tiết vận đơn | Giao hàng | 12 | thẻ, ô nhập, tiền | baoTin, hoiNhap, sheet, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Accounts User, Purchase User, Sales Manager, Sales User, Shipper, System Manager |
| scrVdTao | Tạo vận đơn | Giao hàng | 12 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Sales Manager, Sales User, System Manager |
| scrVdChiPhi | Chi phí xăng xe - sửa xe | Giao hàng | 12 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiNhap, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Sales Manager, Sales User, Shipper, System Manager |
| scrVdGoiXe | Gọi xe  | Giao hàng | 12 | thanh đáy, thẻ, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrVdTuyen | Xếp tuyến | Giao hàng | 12 | thẻ, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrVdPhiApp | Phí giao hàng book app | Giao hàng | 12 | thẻ, ô nhập, bảng | baoTin, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrCanhBaoTT | Cảnh báo thanh toán | Giao hàng | 21 | thẻ, dòng hub, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |

## PR 3 Kho, Sản xuất, Thu mua (82 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrMRList | (động) | Đặt hàng | 03 | nút nổi, chip, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrStep1 | (động) | Đặt hàng | 04 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrStep2 | Chọn hàng hoá; (động) | Đặt hàng | 04 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrStep3 | Danh sách đã chọn | Đặt hàng | 04 | thanh đáy, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrStep4 | Xem lại phiếu | Đặt hàng | 04 | thanh đáy, nút đầu trang, thẻ, ô nhập, tiền | baoTin, confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrRndList | Mua hàng phát sinh | Đặt hàng | 07 | nút nổi, nút đầu trang, ô nhập, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrRndNew | Yêu cầu mua hàng phát sinh | Đặt hàng | 07 | thanh đáy, nút đầu trang, thẻ, ô nhập | confirmSheet, pickDate (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrRndDoc | Phiếu mua phát sinh | Đặt hàng | 07 | thanh đáy, nút đầu trang, thẻ, ô nhập, tiền | confirmSheet, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Accounts User, Purchase User, System Manager |
| scrDeNghiChi | Đề nghị chi | Đặt hàng | 16 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTTNB | Thanh toán nội bộ | Đặt hàng | 16 | thanh đáy, thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, confirmSheet, hoiChu, hoiCo, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrStock | Tra tồn kho | Kiểm kê | 05 | thẻ, chip, ô nhập, tiền | confirmSheet, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKkList | Kiểm kê | Kiểm kê | 06 | nút nổi, nút đầu trang, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrKkNew | Phiếu kiểm kê mới | Kiểm kê | 06 | thanh đáy, nút đầu trang, thẻ, ô nhập | confirmSheet, pickDate, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | Stock Manager, System Manager |
| scrKkDoc | Kiểm kê | Kiểm kê | 06 | thanh đáy, nút đầu trang, thẻ, chip, ô nhập | confirmSheet (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | Stock Manager, System Manager |
| scrKkPost | Ghi sổ kiểm kê | Kiểm kê | 06 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTonChang | Tồn kho theo chặng | Kiểm kê | 37 | chip, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrHangVeKho | Hàng chuyển về kho tôi | Nhập kho | 03 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrRecvList | Nhập kho | Nhập kho | 06 | nút đầu trang, thẻ, ô nhập | baoTin, confirmSheet, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrRecvDoc | Nhập kho | Nhập kho | 06 | thanh đáy, nút đầu trang, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNhpDon | Nhận hàng; Nhận hàng đợt  | Nhập kho | 06 | thanh đáy, thẻ, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNhanBanh | Nhận bánh | Nhập kho | 31 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNhanDcXacNhan | Xác nhận nhận hàng | Nhập kho | 45 | ô nhập | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMRView | (động) | Sản xuất | 03 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrRecvTransfer | Nhận hàng ; (động) | Sản xuất | 03 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrKitchen | Bảng bếp; Bảng bếp  | Sản xuất | 05 | thanh đáy, thẻ, chip, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMfgList | Lệnh sản xuất | Sản xuất | 05 | nút nổi, nút đầu trang, chip, ảnh món, ô nhập | confirmSheet (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | Giám đốc, Manufacturing Manager, System Manager |
| scrMfgNew | Tạo lệnh sản xuất | Sản xuất | 05 | thanh đáy, thẻ, chip, ô nhập | confirmSheet, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | Giám đốc, Manufacturing Manager, System Manager |
| scrMfgBtp | Bán thành phẩm cần làm | Sản xuất | 05 | thanh đáy, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrMfgView | Lệnh sản xuất | Sản xuất | 05 | thanh đáy, thẻ, ảnh món, ô nhập | confirmSheet (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMfgDeclare | Khai nguyên liệu | Sản xuất | 05 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | Giám đốc, Manufacturing Manager, System Manager |
| scrMfgLabel | In tem HACCP | Sản xuất | 05 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, bàn phím ảo | - |
| scrCongThuc | Danh mục công thức | Sản xuất | 26 | thanh đáy, nút nổi, chip, ô nhập |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | AP Giám đốc, Bếp phó, Giám đốc, Manufacturing Manager, Quầy Bar, System Manager, VGB - Quản lý công thức |
| scrCongThucXem | Công thức | Sản xuất | 26 | thanh đáy, thẻ, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | AP Giám đốc, Bếp phó, Giám đốc, Manufacturing Manager, Quầy Bar, System Manager, VGB - Quản lý công thức |
| scrCongThucNhatKy | Nhật ký sửa công thức | Sản xuất | 26 | thẻ, chip | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrCongThucDaXoa | Công thức đã xoá | Sản xuất | 26 | thẻ, chip | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCongThucSua | (động) | Sản xuất | 26 | thanh đáy, thẻ, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrHuongDanSoan | Hướng dẫn chế biến | Sản xuất | 32 | thanh đáy, thẻ, chip, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | AP Giám đốc, Bếp phó, Giám đốc, Manufacturing Manager, System Manager |
| scrDonTiec | Đơn tiệc / B2B | Sản xuất | 33 | nút đầu trang, chip, ô nhập, tiền | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTiecXem | Đơn tiệc | Sản xuất | 33 | thanh đáy, thẻ, ô nhập, tiền |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTiecXuat | Xuất NVL cho tiệc | Sản xuất | 33 | thanh đáy, thẻ, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrKeHoachSX | Kế hoạch sản xuất | Sản xuất | 38 | thanh đáy, thẻ, chip, ảnh món, ô nhập | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | AP Giám đốc, Giám đốc, Manufacturing Manager, System Manager |
| scrKhsxDsPhieu | Các phiếu kế hoạch | Sản xuất | 38 | chưa xác định | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrDxDs | Phiếu đề xuất công thức | Sản xuất | 72 | nút nổi, thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Giám đốc, Giám đốc, Manufacturing Manager, System Manager, VGB - Quản lý công thức |
| scrDxSua | (động) | Sản xuất | 72 | thanh đáy, thẻ, chip, ô nhập, bảng, tiền | confirmSheet, sheet (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDonMua | Đơn mua hàng | Thu mua | 16 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDonMuaXem | Đơn mua hàng | Thu mua | 16 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDuyetYc | Duyệt yêu cầu mua | Thu mua | 16 | thẻ, dòng hub | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDuyetYcXem | Duyệt yêu cầu mua; Duyệt  | Thu mua | 16 | thanh đáy, thẻ, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNoPhaiTra | Công nợ phải trả | Thu mua | 16 | thanh đáy, thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, confirmSheet, hoiChon, sheet, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Kiểm soát (FIN), Accounts Manager, Accounts User, System Manager |
| scrCntPhiDt | Cấn trừ phí đối tác | Thu mua | 16 | thanh đáy, thẻ, chip, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrCntTruocErp | Đã trả trước khi lên ERP | Thu mua | 16 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHoSoTTView | Hồ sơ  | Thu mua | 19 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, hoiChon, hoiCo, hoiNhap, hopKhung, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNoiDungCK | Nội dung chuyển khoản | Thu mua | 19 | thanh đáy, nút nổi, thẻ, ô nhập, tiền | hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNcc | Nhà cung cấp | Thu mua | 20 | thẻ, dòng hub, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNccXem | Nhà cung cấp; (động) | Thu mua | 20 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNccGan | Gán nhà cung cấp | Thu mua | 20 | thanh đáy, thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChon, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTimGiaoDich | Tìm giao dịch | Thu mua | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBangGia | Bảng giá mua | Thu mua | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChu, hoiCo, hoiSo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrGomMua | Gom yêu cầu mua | Thu mua | 70 | nút đầu trang, thẻ, chip, ảnh món, ô tìm, ô nhập, tiền | confirmSheet, hoiChon | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | Accounts Manager, Accounts User, Giám đốc, Purchase Manager, Purchase User, Sales Manager, Sales User, System Manager, Thu mua |
| scrDuChi | Dự chi công nợ | Thu mua | 71 | nút đầu trang, thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDuChiXem | Dự chi công nợ; Dự chi  | Thu mua | 71 | thanh đáy, nút đầu trang, thẻ, chip, ô tìm, ô nhập, tiền | confirmSheet, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDuChiThem | Sửa dự chi; (động) | Thu mua | 71 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrLichChi | (động) | Thu mua | 71 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrLichGoiY | Máy gợi ý lịch chi | Thu mua | 71 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrXkChonHang | Thêm hàng | Xuất kho | 03 | ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkHuyList | Xuất huỷ | Xuất kho | 03 | nút nổi | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkHuyNew | Lập phiếu xuất huỷ | Xuất kho | 03 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkCkList | Xuất điều chuyển | Xuất kho | 03 | nút nổi | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrXkCkNew | Lập phiếu điều chuyển | Xuất kho | 03 | ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkView | Phiếu xuất; (động) | Xuất kho | 03 | ô nhập | baoTin, confirmSheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkNbList | Xuất dùng nội bộ | Xuất kho | 45 | nút nổi, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkNbNew | Lập phiếu xuất dùng nội bộ | Xuất kho | 45 | ảnh món, ô nhập | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkNbView | Phiếu xuất dùng nội bộ | Xuất kho | 45 | ảnh món, ô nhập | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkTraList | Xuất trả nhà cung cấp | Xuất kho | 45 | nút nổi, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkTraNew | Lập phiếu trả hàng | Xuất kho | 45 | ảnh món, ô nhập | baoTin, sheet, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkTraView | Phiếu trả hàng | Xuất kho | 45 | ảnh món, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkSiList | Xuất bán sỉ | Xuất kho | 45 | nút nổi, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkSiNew | Lập phiếu giao hàng | Xuất kho | 45 | ảnh món, ô nhập | baoTin, sheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkSiView | Phiếu giao hàng | Xuất kho | 45 | ảnh món, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkPvList | Xuất kho phục vụ bán hàng | Xuất kho | 46 | nút nổi, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrXkPvNew | Chốt kho điểm bán | Xuất kho | 46 | ảnh món, ô nhập | sheet, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrXkPvView | Phiếu xuất kho phục vụ bán hàng | Xuất kho | 46 | ảnh món, ô nhập | hoiChu, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |

## PR 4 Kế toán, Tài chính (44 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrPayList | Duyệt phiếu chi | Kế toán | 04 | thẻ, chip, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrPayView | (động) | Kế toán | 04 | thanh đáy, nút đầu trang, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, sheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Kiểm soát (FIN), Accounts Manager, Accounts User, System Manager |
| scrHoanTien | Phiếu hoàn tiền (Cash-back) | Kế toán | 11 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChu, hoiCo, hopKhung, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrNccTao | Tạo nhà cung cấp | Kế toán | 16 | thanh đáy, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrHdBan | Hoá đơn bán ra | Kế toán | 16 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrHdMua | Hoá đơn mua vào | Kế toán | 16 | thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDoiChieuMua | Đối chiếu hoá đơn mua | Kế toán | 18 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrDcmXem | Đối chiếu ; Đối chiếu | Kế toán | 18 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, sheet (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDcmHachToan | Hạch toán ; Hạch toán | Kế toán | 18 | thanh đáy, thẻ, ảnh món, tiền | baoTin, confirmSheet, hoiChon | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrHoSoTT | Hồ sơ thanh toán | Kế toán | 19 | nút đầu trang, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, hoiChon, hoiNhap, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrViSaoThieu | Vì sao thiếu hoá đơn | Kế toán | 19 | thẻ, dòng hub, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrHoSoTTTao | (động); Lập hồ sơ thanh toán | Kế toán | 19 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, sheet, xacNhan (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Kiểm soát (FIN), Accounts Manager, Accounts User, Giám đốc, Purchase Manager, Purchase User, Sales Manager, Sales User, System Manager, Thu mua |
| scrHoanUngTao | Lập hồ sơ hoàn ứng | Kế toán | 19 | thanh đáy, thẻ, ô tìm, ô nhập, bảng, tiền | baoTin, hoiChon, hopKhung, sheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHuSepay | Sao kê quỹ tạm ứng | Kế toán | 19 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin, hoiChon, hopKhung, sheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrChiCongTyTao | Chi từ TK công ty | Kế toán | 19 | thanh đáy, thẻ, dòng hub, ô tìm, ô nhập, bảng, tiền | baoTin, hoiChon, hopKhung, sheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | AP Kiểm soát (FIN), Accounts Manager, Accounts User, Giám đốc, Purchase Manager, Purchase User, Sales Manager, Sales User, System Manager, Thu mua |
| scrTaiSan | Tài sản | Kế toán | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChon, hoiChu, hoiCo, hoiNgay, hoiSo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTaiSanXem | Tài sản | Kế toán | 21 | thẻ, dòng hub, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKhauHao | Khấu hao | Kế toán | 21 | thẻ, dòng hub, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrButToan | Bút toán | Kế toán | 21 | thẻ, dòng hub, ô nhập, tiền | baoTin, hoiChon | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBtLap | Lập bút toán | Kế toán | 21 | thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChu, hoiCo, hoiNgay | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrButToanXem | Bút toán | Kế toán | 21 | thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKhopSepay | Khớp SePay thủ công | Kế toán | 23 | thẻ, chip, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTraTruocTao | Thanh toán trước cho NCC | Kế toán | 30 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiChon, hopKhung, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTruKho | (động) | Kế toán | 49 | thanh công cụ ds, thẻ, ô tìm, ô nhập, bảng, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsvn | Đối soát nhà cung cấp | Kế toán | 52 | thanh đáy, thanh công cụ ds, thẻ, chip, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsvnBill | Bill chưa khớp đối tác | Kế toán | 52 | thanh công cụ ds, thẻ, chip, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsvnThu | Hộp thư đối soát | Kế toán | 52 | thẻ, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrDsvnTai | Nhận file đối soát | Kế toán | 52 | thanh đáy, thẻ, chip, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsvnCt | Nguồn đối soát | Kế toán | 52 | thanh đáy, thẻ, chip, ô nhập, tiền | baoTin, confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrGiaVonTam | (động) | Kế toán | 53 | thanh đáy, thẻ, chip, ảnh món, ô nhập, tiền | baoTin, confirmSheet (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyTm | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | hoiChu, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyChotDau | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyKiem | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQuyNop | (động) | Kế toán | 62 | thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCp242 | (động) | Kế toán | 79 | thanh đáy, thẻ, ảnh món, ô tìm, ô nhập, tiền | hoiChu, sheet, xacNhan (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDsMeta | (động) | Kế toán | 80 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrDsMetaThang | (động) | Kế toán | 80 | thẻ, ô nhập, tiền | hoiChu, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTcTongQuan | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcTien | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcDong | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcDuBao | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcLaiLo | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcTiLe | (động) | Tài chính | 61 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrTcCaiDat | (động) | Tài chính | 61 | thẻ, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |

## PR 5 Marketing và các màn còn lại (69 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrBaoCao | Báo cáo | Báo cáo | 14 | thẻ, ô nhập, tiền | baoTin, hoiChon, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBaoCaoXem | Báo cáo  | Báo cáo | 14 | thanh đáy, thẻ, ảnh món, ô nhập, bảng, tiền | baoTin, hoiChon, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBangSang | Việc hôm nay | Báo cáo | 47 | nút đầu trang, thẻ, chip, ảnh món, ô nhập, tiền | confirmSheet, hopKhung, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrViecGoiY | Việc được giao | Báo cáo | 47 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCaiDatCuoiNgay | Cuối ngày | Cài đặt | 17 | thanh đáy, thẻ, ô nhập, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrDiemBan | Điểm bán | Cài đặt | 17 | thanh đáy, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrDiemBanSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, sheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKhoaSo | Khoá sổ | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrPtThanhToan | Phương thức thanh toán | Cài đặt | 17 | thanh đáy, thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrPtSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrQuyenQuay | Quyền tại quầy | Cài đặt | 17 | thanh đáy, thẻ | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrHangKhach | Hạng thành viên | Cài đặt | 17 | thanh đáy, thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrHangSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrXetLaiHang | Xét lại hạng | Cài đặt | 17 | thanh đáy, thẻ, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrTaiKhoan | Tài khoản nhận tiền | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTaiKhoanSua | (động) | Cài đặt | 17 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrDanhMuc | Danh mục sản phẩm | Cài đặt | 17 | thanh đáy, thẻ, ảnh món, ô nhập, tiền | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrSePay | SePay | Cài đặt | 17 | thẻ, ô nhập | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNhapSaoKe | Nhập sao kê ngân hàng | Cài đặt | 17 | thẻ, ô nhập, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrThongBao | Thông báo trên điện thoại | Cài đặt | 17 | thẻ | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrCaiDatWeb | Trang đặt bánh web | Cài đặt | 17 | thẻ | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi | - |
| scrCaiDatKho | Ngưỡng kho | Cài đặt | 17 | nút nổi, thẻ, ô nhập | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, bàn phím ảo | - |
| scrMayIn | Máy in | Cài đặt | 18 | thanh đáy, thẻ, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMayIn0 | Máy in | Cài đặt | 18 | thanh đáy, thẻ, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMayInSua | (động) | Cài đặt | 18 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNguoiDung | Quản lý người dùng | Cài đặt | 20 | thẻ, dòng hub, ô nhập | baoTin, hoiChonNhieu, hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNguoiDungXem | Người dùng | Cài đặt | 20 | thẻ, dòng hub, ô nhập | baoTin, confirmSheet, hoiChon, hoiChonNhieu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrQuyen | Quản lý quyền | Cài đặt | 20 | thẻ, dòng hub | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrQuyenXem | Gói chức vụ | Cài đặt | 20 | thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrDonChungTuThu | Dọn chứng từ thử | Cài đặt | 24 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrChuyenPhantom | Chuyển Phantom | Cài đặt | 24 | thanh đáy, thẻ | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở | - |
| scrBoAo | Bỏ ảo một mã | Cài đặt | 24 | thanh đáy, thẻ, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTroLyCaiDat | Trợ lý | Cài đặt | 35 | thanh đáy, thẻ, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrMauIn | Mẫu in ấn | Cài đặt | 36 | thẻ, ô nhập, bảng, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCaiDatLoi | Cài đặt lõi và API | Cài đặt | 51 | thanh đáy, chip, ô nhập | confirmSheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrBangGiaDiem | (động) | Cài đặt | 65 | thanh đáy, thẻ, ảnh món, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTuDongHoa | Cài đặt tự động hoá | Cài đặt | 69 | nút đầu trang, thẻ, chip, ô nhập | confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | AP Giám đốc, Accounts Manager, Giám đốc, Manufacturing Manager, Purchase Manager, Sales Manager, Stock Manager, System Manager, VGB - Quản lý cửa hàng |
| scrKhachHang | Danh sách khách hàng | Khách hàng & Marketing | 11 | thẻ, chip, ô tìm, ô nhập, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrKhachChiTiet | Khách hàng | Khách hàng & Marketing | 18 | thẻ, ảnh món, ô nhập, tiền | baoTin (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTqDot | Tặng quà khách VIP | Khách hàng & Marketing | 34 | nút nổi, ô nhập | hoiChu, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTqDs | (động) | Khách hàng & Marketing | 34 | nút nổi, nút đầu trang, ô nhập | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTqSua | Phiếu tặng quà | Khách hàng & Marketing | 34 | thanh đáy, ô nhập | confirmSheet, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTqThemLoat | Thêm khách vào đợt | Khách hàng & Marketing | 34 | thanh đáy, ô nhập | confirmSheet, hoiCo, hoiSo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTqLapDot | (động); Đợt tặng quà mới | Khách hàng & Marketing | 34 | thanh đáy, ô nhập | sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTqDan | Dán danh sách vào đợt; (động) | Khách hàng & Marketing | 34 | thanh đáy, ô nhập | confirmSheet, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrCrmHoSo | Chăm sóc khách | Khách hàng & Marketing | 58 | thẻ, ảnh món, ô nhập, tiền |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmGoi | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmNhom | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, dòng hub, ảnh món, ô tìm, ô nhập, tiền | baoTin (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmDongY | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmCdDs | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmCd | (động) | Khách hàng & Marketing | 58 | thẻ, ảnh món, ô nhập, tiền | baoTin, confirmSheet, hoiChon, hoiChonNhieu (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | System Manager |
| scrCrmHqDs | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, dòng hub, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmHieuQua | (động) | Khách hàng & Marketing | 58 | thẻ, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrCrmZalo | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, hoiCo, sheet (+3) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrCrmZaloTin | (động) | Khách hàng & Marketing | 58 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrBaiDang | (động) | Khách hàng & Marketing | 75 | thanh đáy, nút đầu trang, thẻ, chip, ô tìm, ô nhập |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrBaiDangSoan | Bài đăng | Khách hàng & Marketing | 75 | thanh đáy, nút đầu trang, thẻ, ô tìm, ô nhập, tiền | confirmSheet, hoiChu (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrMonDiKem | (động) | Khách hàng & Marketing | 78 | thanh đáy, thẻ, ảnh món, ô tìm, ô nhập, tiền | baoTin, hoiChon, hoiChonNhieu (+2) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrQcMeta | (động) | Khách hàng & Marketing | 80 | thanh đáy, thẻ, tiền |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKPI | KPI và hoa hồng | Nhân sự | 44 | thanh đáy, thẻ, tiền | baoTin, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở | - |
| scrKPICt | Phiếu KPI; Phiếu KPI ·  | Nhân sự | 44 | thanh đáy, thẻ, ô nhập, tiền | baoTin, confirmSheet, hoiChu | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKPICau | Bảng chỉ tiêu; Bảng chỉ tiêu và bậc hoa hồng | Nhân sự | 44 | thẻ, ô nhập, bảng, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrKPIToi | KPI của tôi | Nhân sự | 44 | thẻ, ô nhập, tiền | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrKPITuKhai | Phiếu duyệt commission | Nhân sự | 44 | thanh đáy, thẻ, ô nhập, tiền | baoTin, hoiCo | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTuyenDung | (động) | Nhân sự | 60 | thanh công cụ ds, thẻ, ô tìm, ô nhập, tiền | baoTin, confirmSheet (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTdChiTiet | (động) | Nhân sự | 60 | thẻ, ô nhập, tiền |  (+1) | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrTdViTri | (động) | Nhân sự | 60 | thanh đáy, thẻ, ô nhập | baoTin, confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrTdThemHs | (động) | Nhân sự | 60 | thanh đáy, thẻ, ô nhập | confirmSheet, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrHhgt | (động) | Nhân sự | 67 | thanh đáy, thẻ, ô tìm, ô nhập, tiền | baoTin, hoiChu, hoiCo, sheet | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |

## Chưa xếp, cần xếp tay (5 màn)

| Màn | Tiêu đề | Nhóm | Phần | Thành phần | Hộp thoại | Trạng thái cần kiểm | Vai nhắc trong mã |
|---|---|---|---|---|---|---|---|
| scrKhungDs | Danh sách; (động) | - | 15 | nút nổi, khuôn ds, thẻ, ô nhập, bảng, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, bàn phím ảo | - |
| scrKgTao | (động) | - | 15 | thanh đáy, khuôn ds, ô nhập | baoTin | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, hộp thoại mở, bàn phím ảo | - |
| scrNopQuy | Nộp quỹ tiền mặt | - | 21 | thẻ, chip, tiền | - | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0 | - |
| scrNopQuyTao | Lập phiếu nộp quỹ | - | 21 | nút đầu trang, thẻ, ô nhập, tiền | baoTin, hoiChu, hopKhung | có dữ liệu, tên dài, cỡ chữ 150% và 200%, rỗng, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |
| scrMauIn0 | Mẫu in ấn | - | 36 | thẻ, ô nhập, bảng, tiền | baoTin, xacNhan | có dữ liệu, tên dài, cỡ chữ 150% và 200%, đang tải, lỗi, số lớn, âm, 0, hộp thoại mở, bàn phím ảo | - |

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

