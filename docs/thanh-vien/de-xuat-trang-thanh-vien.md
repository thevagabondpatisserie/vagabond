# Đề xuất: làm lại trang thành viên và chương trình nhận quà tại quầy

Bản nháp 30/10/2026, chưa có code. Mục đích: xin Codex góp ý trước khi chia việc.
Hai bản phác (4 màn trang thành viên, 6 bước nhận quà tại quầy) đã gửi anh
Việt trong phiên làm việc 30/10, chưa duyệt; mục 3 và 4 mô tả lại bằng chữ.

## 1. Tóm tắt nghiệp vụ

Vấn đề: trang `/thanh-vien` hiện chỉ có đăng nhập bằng mã Zalo, ảnh thẻ hạng,
số điểm và danh sách đơn. Không có ảnh đại diện, không khai được ngày sinh hay
đồng ý nhận tin, không có ví voucher, không có mã cho quầy quét. Giao diện chưa
đồng bộ với web đặt bánh. CRM mới có 1 khách đồng ý nhận tin Zalo nên kịch bản
tin tự động (PR #517) gần như không có ai để gửi.

Việc làm: (a) thu ngân mời khách quét mã lúc tính tiền, khách xác minh số qua
Zalo, khai hồ sơ ngắn, nhận voucher 20.000đ dùng ngay trên hoá đơn đang tính;
(b) làm lại trang thành viên theo bản phác.

Anh Việt đã chốt (30/10/2026):
- Quà là giảm 20.000đ.
- Bắt buộc xác minh số điện thoại bằng mã OTP qua Zalo.
- Voucher dùng ngay trên hoá đơn đang tính.

## 2. Đã có sẵn, dùng lại

| Cần | Đã có | Ghi chú |
|-----|-------|---------|
| OTP qua Zalo | `thanh_vien.gui_ma`, `xac_thuc`, cookie `vgb_thanh_vien` | Mẫu ZNS đã duyệt |
| Mã dùng một lần | doctype `Vagabond Voucher`, `khuyen_mai._sinh_ma_moi` | 6 ký tự, bỏ O/0 và I/1 |
| Thu ngân gõ mã | `khuyen_mai.tra_ma`, `tinh(..., ma=)`, `ghi_su_dung` | Ô mã ở màn quầy đã có |
| Đồng ý nhận tin | `Vagabond Ho So CRM.dy_zalo`, `dy_luc`, `dy_noi` | Có `doi_dong_y` ghi lịch sử |
| Ngày sinh | trường ngày sinh trên Customer, `zalo_kich_ban.qua_sinh_nhat` | Kịch bản sinh nhật dùng ngay |
| Hạng và điểm | `Vagabond Hang Khach`, `diem_otp._so_du` | 1 điểm = 1đ |

## 3. Luồng nhận quà tại quầy

1. Quầy có mã QR riêng (bảng A5 hoặc màn hình phụ): `/qua?q=<mã quầy>`.
2. Khách nhập số có Zalo, nhận mã 6 số (dùng lại `gui_ma`).
3. Khách nhập mã; đủ 6 số tự chuyển bước (dùng lại `xac_thuc`).
4. Hồ sơ ngắn: tên gọi, ngày sinh (năm không bắt buộc), món hay chọn (không
   bắt buộc), ô đồng ý nhận tin Zalo. Ô đồng ý KHÔNG tích sẵn.
5. Máy cấp một `Vagabond Voucher` của chương trình "Quà chào mừng", hạn hết
   ngày hôm nay, `gui_cho` = khách. Màn hiện mã lớn để thu ngân gõ.
6. Thu ngân gõ mã vào ô voucher của hoá đơn đang tính như mọi mã khác. Áp mã
   xong thì hoá đơn gắn với hồ sơ khách để tích điểm luôn.

Quy tắc đề xuất:
- Một số điện thoại nhận quà chào mừng đúng một lần, kể cả khi huỷ mã.
- Số đã là thành viên trước ngày mở chương trình: vẫn vào hồ sơ được; có nhận
  quà hay không do anh Việt chốt (câu hỏi Q-A2).
- Số của nhân viên không nhận quà (dùng lại `_la_sdt_nhan_vien`).
- Trần theo quầy theo ngày (ví dụ 50 mã) để chặn lạm dụng; vượt trần thì báo
  Zalo nhóm quản lý, không chặn khách đang đứng ở quầy.
- Mã không dùng hết ngày: hết hạn hay chuyển thành voucher 7 ngày (Q-A1).

## 4. Trang thành viên mới (4 màn)

1. Trang chính: ảnh đại diện vuông, tên lớn, số điểm khổng lồ, thẻ hạng vẽ theo
   thẻ thật, thanh tiến độ lên hạng kế tiếp, ba con số (đơn bánh, voucher, năm
   gắn bó), quyền lợi hạng, khung mời hoàn thiện hồ sơ khi còn thiếu.
2. Ví quà: mã thành viên dạng QR và chữ cho quầy quét, danh sách voucher
   (dùng được, sắp mở, đã dùng), điểm dùng được.
3. Đơn bánh và tin mới: nút Đặt bánh, Đặt bàn; đơn gần đây kèm trạng thái bếp
   và nút Đặt lại; mục Có gì mới ba tab với lưới ảnh do quản lý tự thay.
4. Hồ sơ: đổi ảnh (tải ảnh hoặc chọn hình bánh có sẵn), họ tên, số đã xác minh
   (khoá), ngày sinh, email, món hay chọn, công tắc nhận tin Zalo, đăng xuất.

## 5. Dữ liệu và API cần thêm

Trường mới (Custom Field có `insert_after`, hoặc thêm vào `Vagabond Ho So CRM`):
- `anh_dai_dien` (Attach Image, tệp riêng tư) và `anh_mau` (mã hình bánh có sẵn).
- `so_thich` (Small Text, danh sách mã cố định, hiển thị bằng chữ có dấu).
- `nguon_dang_ky` (quầy nào, ngày nào) và `qua_chao_mung` (Link Vagabond Voucher)
  để chốt "một số một lần" bằng dữ liệu, không bằng đếm lại.

API mới trong `thanh_vien.py` (thêm tên vào `thu_cua_ngo.py`):
- `cap_nhat_ho_so(ten, ngay_sinh, so_thich, dong_y_zalo, email)`: chỉ sửa hồ sơ
  của cookie hiện tại; chuẩn ngày sinh mọi cách điền hợp lý; đổi đồng ý thì đi
  qua `doi_dong_y` để có lịch sử.
- `doi_anh(tep)`: nhận ảnh tối đa 5 MB, chỉ JPEG/PNG/HEIC, máy thu về 512 px
  vuông, bỏ EXIF; lưu tệp riêng tư, trả về đường dẫn có ký.
- `nhan_qua(quay)`: sau `xac_thuc` và hồ sơ đủ ô bắt buộc thì cấp mã; gọi lại
  lần hai trả đúng mã cũ (idempotent), không cấp mã thứ hai.
- `toi()` thêm: `anh`, `ho_so_thieu` (danh sách ô), `voucher` (mã, giá trị,
  hạn, trạng thái), `tien_do_hang` (đã mua 12 tháng, mốc hạng kế, còn thiếu),
  `ma_thanh_vien` (chuỗi cho QR, không phải số điện thoại).

Màn quầy: ô voucher đã nhận mã 6 ký tự, không cần màn mới. Chỉ thêm: quét QR
thành viên điền sẵn khách vào hoá đơn.

## 6. Chia đợt đề xuất

- Đợt 1 (v622): chương trình Quà chào mừng, trang `/qua`, `cap_nhat_ho_so`,
  `nhan_qua`, bảng A5 in cho quầy. Đây là phần tạo khách đồng ý nhận tin.
- Đợt 2 (v623): giao diện mới của `/thanh-vien` theo bản phác, ảnh đại diện,
  ví quà, mã thành viên QR.
- Đợt 3: mục Có gì mới, Đặt lại đơn, thêm vào ví điện thoại.

## 7. Câu hỏi cho Codex

- Q-C1. Chốt "một số một lần" nên đặt ở đâu để hai lượt bấm cùng lúc không cấp
  hai mã: khoá theo số trên `Vagabond Ho So CRM`, hay ràng buộc duy nhất trên
  một doctype nhỏ "Vagabond Qua Chao Mung" (sdt, voucher)?
- Q-C2. Cấp mã ngay sau OTP mà phiên OTP bị chiếm (máy quầy để mở) thì rủi ro gì?
  Có nên buộc `nhan_qua` trong vòng 10 phút sau `xac_thuc`?
- Q-C3. Ảnh đại diện: lưu `File` riêng tư của Frappe rồi phục vụ qua hàm có
  kiểm cookie, hay ảnh công khai với tên ngẫu nhiên? Khách vãng lai không có
  quyền đọc tệp riêng tư.
- Q-C4. `ma_thanh_vien` cho QR: chuỗi ngẫu nhiên lưu trên hồ sơ, hay ký HMAC
  theo số và có hạn? Quầy quét xong điền khách vào hoá đơn, không được lộ số.
- Q-C5. Trần theo quầy theo ngày và báo Zalo nhóm quản lý: dùng bộ đếm sẵn
  `_dem_da_dung` của CTKM có đủ không?
- Q-C6. Còn trường hợp nào luồng trên làm sai sổ (hoá đơn trả hàng sau khi áp
  mã, huỷ hoá đơn, đơn web dùng mã quà) mà bản đề xuất chưa nói?

## 8. Chờ anh Việt quyết

- Q-A1. Mã quà không dùng trong ngày: mất, hay chuyển thành voucher 7 ngày?
- Q-A2. Khách cũ đã là thành viên có được quà chào mừng không, hay chỉ quà
  "hoàn thiện hồ sơ" khi khai ngày sinh và đồng ý nhận tin lần đầu?
- Q-A3. Duyệt bản phác giao diện, hoặc chỉ ra chỗ muốn đổi.
