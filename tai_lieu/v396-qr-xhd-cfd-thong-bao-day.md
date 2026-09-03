# v396: QR xuất hoá đơn, màn hình khách (CFD), thông báo đẩy, xuất bán sỉ

Ngày 03/09/2026. Nhánh `v396-qr-xhd-cfd-push`, PR #157, commit cuối 2cf07fd, 14 tệp.
CI "Kiem thu truoc deploy" xanh, "Able to merge".

TRẠNG THÁI: ĐÃ ĐẨY, CHƯA MERGE, CHƯA DEPLOY. Anh Việt dặn "khoan deploy". Chờ anh
Việt duyệt rồi mới merge và bấm Frappe Cloud.

## Bốn lỗi anh Việt duyệt sửa

### 1. QR xuất hoá đơn lúc ra trang nhập, lúc nhảy sang app nội bộ

Nguyên nhân: mã QR in cuối bill lấy địa chỉ theo trình duyệt của thu ngân
(`location.origin`), tức là `app.thevagabondpatisserie.com`. Từ 23/08 luật tên
miền (`ten_mien.py`) coi `/xhd` là trang KHÁCH, nên miền app đá khách về `/bep`,
khách quét xong thấy màn đăng nhập app nội bộ.

Vì sao "lúc được lúc không": luật chạy lúc DỰNG trang, mà Frappe giữ trang đã
dựng trong bộ nhớ đệm cho khách vãng lai. Trang đang nằm trong đệm thì luật không
chạy và khách vào được; mỗi lần deploy xoá đệm là khách đầu tiên lại bị đá. Hai
tuần qua deploy hơn mười lần một ngày nên lúc được lúc không.

Sửa ba tầng:
- `ten_mien.py`: thêm `DUONG_CHUNG = ("/xhd",)`, đường này đi qua MỌI miền, không
  bao giờ bị đá. Thêm hàm thuần `link_khach(duong)` trả địa chỉ tuyệt đối trên
  miền khách `order.thevagabondpatisserie.com`.
- `ban_hang.py` `pos_link_xhd`: trả `url` tuyệt đối trên miền khách kèm `duong`
  tương đối. QR in ra từ nay luôn là miền khách.
- `10-bill-quay.js`: nhận cả địa chỉ tuyệt đối lẫn tương đối.

Bill đã in trước hôm nay (QR trỏ miền app) vẫn quét được nhờ `/xhd` đi qua mọi
miền.

### 2. Màn hình CFD xung đột với màn thu ngân

Hai hiện tượng, hai nguyên nhân khác nhau:
- Mất cảm ứng màn chính: cửa sổ CFD mở bằng `window.open` không chỉ định màn nên
  nằm ĐÈ lên màn thu ngân, hoặc máy đang để chế độ Duplicate (nhân đôi) nên cả
  hai màn là một. Thu ngân chạm vào là chạm vào cửa sổ CFD.
- CFD tối đen: màn phụ không có ai chạm nên Windows tắt màn tiết kiệm điện.

Sửa:
- `25-man-hinh-khach.js`: `cfdMo()` dùng Window Management API
  (`window.getScreenDetails`) để mở cửa sổ đúng lên màn phụ (`cfdChonManPhu`, ưu
  tiên màn có `isPrimary === false`). Máy chỉ thấy MỘT màn (`screen.isExtended
  === false`) thì từ chối mở và báo "bấm Win+P chọn Extend". Trình duyệt không
  có API này thì mở như cũ và báo cho thu ngân tự kéo sang. Mở xong
  `window.focus()` trả tiêu điểm về màn thu ngân.
- `www/man-hinh-khach.html`: giữ màn sáng bằng Screen Wake Lock API, xin lại khi
  tab hiện lại và mỗi 60 giây. Chạm một lần là phóng to toàn màn.

Lưu ý vận hành: Window Management API cần Chrome cho phép "Quản lý cửa sổ trên
mọi màn hình" lần đầu, thu ngân bấm Cho phép một lần là xong.

### 3. Thông báo đẩy chết từ khi máy dựng ảnh Frappe Cloud lên Python 3.14

pywebpush 2.x nhận `vapid_private_key` là chuỗi thì gọi `Vapid.from_string`, chỉ
hiểu base64 raw/DER, KHÔNG hiểu PEM. Code cũ (`_pem`) đổi khoá 32 byte sang PEM
rồi đưa vào, nên mọi thông báo đều lỗi. Sửa: `thong_bao.py` đưa thẳng ĐỐI TƯỢNG
`Vapid` (`Vapid.from_raw` cho khoá 32 byte, `Vapid.from_pem` nếu ai đó dán PEM),
thêm `dang_khoa_rieng()` phân loại raw/pem/hỏng, khoá hỏng thì ghi Error Log và
trả lời rõ thay vì ném lỗi. `kiem_diem_otp.py` (cổng cũ) bỏ ca kiểm chốt PEM,
chính ca kiểm đó đã khoá cái lỗi này lại.

Đã kiểm ở máy làm việc với pywebpush 2.x tải về: `Vapid.from_raw` ký được.

### 4. Xuất bán sỉ (v387) đọc trường không có

Lỗi của phiên v387 (em nhận): `xuat_ban.py` đọc và ghi `remarks` trên Delivery
Note, mà Delivery Note KHÔNG có cột này (Sales Invoice, Purchase Receipt, Stock
Entry thì có). Sáng 03/09 ba lỗi thật trong Error Log, màn danh sách hiện "chưa
có phiếu nào" vì JS nuốt lỗi.

Sửa: trường mới `vgb_dien_giai` (Small Text) trên Delivery Note, đặt sau
`vgb_hop_dong`; `xuat_ban.py` ghi và đọc trường này. `45-xuat-kho-them.js`: ba
màn danh sách (nội bộ, trả NCC, bán sỉ) hiện KHỐI LỖI ĐỎ khi máy chủ trả lỗi
thay vì "chưa có phiếu nào".

## Hai việc không phải code

- Goong 403: khoá Goong bị từ chối. Anh Việt xem lại tài khoản Goong (hết hạn
  hay đổi gói). Em chỉ báo, không đụng.
- Đơn 92862: ghi sổ lỗi vì bán công nợ nhưng chọn khách lẻ. Báo Loan Anh chọn
  khách công nợ đúng tên rồi ghi sổ lại. Không sửa dữ liệu cũ (điều 11).
- Error Log "Session Stopped" từ sw.js trong lúc migrate: nhiễu, bỏ qua.

## TRANH SỐ PHIÊN BẢN VỚI PHIÊN KHÁC, ĐỌC TRƯỚC KHI MERGE

Nhánh `v394-khuon-thu-dien-tu` (phiên khác, khuôn thư điện tử) đẩy lúc 13:04
đến 13:07 ngày 03/09 các commit "v396 lo 6..9": APPVER 396 và dòng patch #v396.
Nhánh này (v396-qr-xhd-cfd-push) đẩy lô 1 lúc 13:04:48. Hai nhánh CÙNG CHIẾM số
396, cả hai đều chưa merge (main đang ở 38cc4b0 = v395).

Tệp trùng giữa hai nhánh: ban_hang.py (tự ghép được, vùng khác nhau), chay.py
(cả hai cùng thêm mô đun vào một dòng, xung đột kiểu cộng thêm, giữ CẢ HAI),
patches.txt và 12-van-don.js (nội dung giống hệt nên git không báo, NHƯNG đó
chính là vấn đề: hai bản cùng số 396 thì Frappe Cloud chỉ chạy migrate một lần).

Cách gỡ đề nghị (chờ anh Việt chốt): nhánh nào merge SAU phải đổi sang v397:
APPVER 397, dòng patch `#v397` thêm dưới dòng #v396, chay.py giữ cả hai mô đun,
ghép lại app_bep.js, chạy lại hai cổng. Phiên này sẵn sàng đổi sang 397 nếu phiên
khuôn thư merge trước.

## Kiểm ở máy làm việc

- 1934 ca khung xanh, 2311/2311 cổng, 105 màn, `dung_app_bep.py --kiem` khớp
  từng byte, `kiem_truoc_deploy.sh` trả 0, giả lập CI không requests xanh.
- 16 ca mới trong `thu_qr_xhd_cfd_push.py`: link_khach, /xhd qua mọi miền, bill
  nhận link tuyệt đối, cfdChonManPhu và cfdDacTinhCuaSo (chạy bằng node),
  dang_khoa_rieng, xuat_ban không còn remarks, danh sách hiện lỗi.

## Sau khi deploy phải kiểm trên site thật

1. In một bill thử, quét QR bằng điện thoại KHÔNG đăng nhập: phải ra trang nhập
   thông tin trên order.thevagabondpatisserie.com.
2. Quét lại một bill in từ hôm qua (QR miền app): cũng phải ra trang nhập.
3. Máy thu ngân: bấm chip CFD, cửa sổ phải hiện trên màn khách, màn thu ngân vẫn
   chạm được. Để yên 15 phút, màn khách không tối.
4. Bật thông báo đẩy trên một máy, gửi thử: phải nhận được, Error Log không có
   dòng thong_bao.
5. Mở màn Xuất bán sỉ: danh sách phiếu hiện ra, không còn "chưa có phiếu nào"
   khi máy chủ lỗi.
6. Patch Log có dòng v396 (hoặc v397 nếu đổi số). Customize Form Delivery Note
   có trường vgb_dien_giai.
