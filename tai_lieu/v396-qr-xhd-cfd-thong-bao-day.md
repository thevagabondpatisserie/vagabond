# v400 (khởi đầu là v396): QR xuất hoá đơn, màn hình khách (CFD), thông báo đẩy, xuất bán sỉ, đồng bộ Pancake giữ khách

Ngày 03/09/2026. Nhánh `v400-qr-xhd-cfd-push-khach-pancake` (tách từ main v399),
PR #161, commit cuối 42dde83, 15 tệp. CI "Kiem thu truoc deploy" xanh, "Ready to
merge", merge sạch với main.

TRẠNG THÁI: ĐÃ ĐẨY, CHƯA MERGE, CHƯA DEPLOY. Anh Việt dặn "khoan deploy". Chờ anh
Việt duyệt rồi mới merge và bấm Frappe Cloud.

VÌ SAO SỐ NHẢY 396 -> 400 TRONG MỘT BUỔI: bốn phiên làm song song. Trong lúc em
đẩy v396, phiên khuôn thư cũng lấy 396 (rồi đổi 398), phiên ba màn xuất kho lấy
397 và merge, phiên sửa giỏ hàng lấy 399 và merge. Mỗi lần main nhảy là em ghép
lại và tăng số. PR #157 (nhánh cũ tách từ v395) đã đóng vì dính xung đột lịch
sử; PR #162 là PR NGƯỢC (main vào nhánh của em, thay nút Update branch), đã merge,
main không đổi. Nhánh `v396-qr-xhd-cfd-push` giờ là nhánh rác, xoá được.

## Năm lỗi đã sửa (bốn lỗi anh Việt duyệt sáng 03/09 cộng một lỗi tìm ra lúc soi đơn 92862)

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

### 5. Đồng bộ Pancake XOÁ khách đã gán, đơn công nợ phải chọn tay lại

Anh Việt hỏi 03/09: "Đơn chưa chọn khách công nợ thì em viết code để đồng bộ bên
Pancake về để đỡ chọn tay được không?". Soi lịch sử đơn 92862 (HDB-26-09-00154):

- 18:32 nhịp đồng bộ TẠO đơn, gán đúng khách KL028403 (Ms.Dung Masterpiece) theo
  số điện thoại 0933331308. Máy đã làm đúng việc anh hỏi từ 13/08.
- 18:33 Loan Anh chọn phương thức Công nợ.
- 19:00 nhịp đồng bộ tiếp theo ĐỔI khách về "Khách lẻ Online". Version ghi rõ
  `["customer", "KL028403", "Khách lẻ Online"]`.
- 23:32 vét cuối ngày chặn "bán công nợ phải chọn khách", Loan Anh phải chọn tay
  lại đúng người máy đã tìm ra lúc 18:32.

Nguyên nhân trong `_upsert_hoa_don` (ban_hang.py, có từ 13/08): khối tìm khách chỉ
chạy khi đơn MỚI hoặc đang mang giỏ chung. Đơn đã có khách thật thì khối bị bỏ
qua, biến `khach_don` vẫn là giỏ chung mặc định, rồi `si.update` đặt lại
customer. Nghĩa là nhịp đầu gán đúng, nhịp sau 30 phút xoá đi, với MỌI đơn
Pancake còn nháp. Không ai thấy vì cuối ngày ghi sổ vẫn được (khách lẻ ghi sổ
bình thường), chỉ đơn công nợ mới lộ.

Sửa: hàm thuần `giu_khach_cua_don(cu, khach_dang_co, la_gop)`: đơn đã có và đang
mang khách thật thì GIỮ, không tìm lại, không đặt về giỏ. Hai ca kiểm mới.

Trả lời câu hỏi của anh: không cần viết thêm đồng bộ, đồng bộ đã có sẵn; chỉ là
nó tự xoá công sức của chính nó. Sau bản này đơn công nợ có số điện thoại khớp
khách trong danh mục sẽ tự có khách, Loan Anh chỉ còn chọn tay khi Pancake không
ghi số điện thoại hoặc số đó chưa có trong danh mục khách.

## Hai việc không phải code

- Goong 403: khoá Goong bị từ chối. Anh Việt xem lại tài khoản Goong (hết hạn
  hay đổi gói). Em chỉ báo, không đụng.
- Đơn 92862: đã ghi sổ xong (Loan Anh chọn tay). Gốc rễ là lỗi 5 ở trên, không
  phải Loan Anh quên. Không sửa dữ liệu cũ (điều 11).
- Error Log "Session Stopped" từ sw.js trong lúc migrate: nhiễu, bỏ qua.

## Ghép với v397 và v399 của phiên khác

- v397 viết lại ba màn xuất kho (`45-xuat-kho-them.js`) thành một hàm vẽ chung
  `xktManDanhSach`. Khối báo lỗi đỏ của em gắn lại qua `cfg.loi`, hàm chung vẽ
  `xktLoiHtml(cfg.loi)` khi máy chủ lỗi. Ba chỗ `catch (e) { }` của v397 vẫn
  nuốt lỗi, đã đổi thành giữ `loiDs`.
- chay.py giữ CẢ HAI mô đun mới (`thu_nguyen_tac_man_hinh` của v397 và
  `thu_qr_xhd_cfd_push` của em).
- patches.txt: 167 dòng của main (tới #v399) cộng dòng #v400. APPVER 400.

## Kiểm ở máy làm việc

- 1940 ca khung xanh trên nền v399, `dung_app_bep.py --kiem` khớp từng byte,
  `kiem_truoc_deploy.sh` trả 0, giả lập CI không requests xanh.
- 18 ca mới trong `thu_qr_xhd_cfd_push.py`: link_khach, /xhd qua mọi miền, bill
  nhận link tuyệt đối, cfdChonManPhu và cfdDacTinhCuaSo (chạy bằng node),
  dang_khoa_rieng, xuat_ban không còn remarks, danh sách hiện lỗi,
  giu_khach_cua_don và _upsert_hoa_don đi qua hàm đó.
- 15 tệp trên nhánh đối chiếu mã băm từng tệp với cây local: 15/15 trùng.

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
6. Patch Log có dòng v400. Customize Form Delivery Note có trường vgb_dien_giai.
7. Đơn Pancake còn nháp có khách thật: chờ qua hai nhịp đồng bộ (1 giờ), mở lại
   vẫn phải còn đúng khách, không bị về "Khách lẻ Online".
