# Mã QR chuyển khoản: dựng tại máy, bỏ phụ thuộc img.vietqr.io

Anh Việt báo ngày 13/10/2026, kèm ảnh màn tính tiền tại quầy: mã QR lại không hiện, chỉ còn chữ "Mã QR chuyển khoản". Anh yêu cầu sửa triệt để. Claude lead và rà, Codex viết code trên nhánh này.

Nền: main `42cb9fb9a`, APPVER 592.

## Số liệu thật (Claude đo 13/10)

- **Ca anh chụp:** bill 160.000 đ, nội dung `TCVG8FRJ`, tài khoản ảo MB `VQRQALEAF2999` của điểm Trần Cao Vân.
- **Tải thử từ trình duyệt máy anh Việt** đúng địa chỉ app đang dùng (`img.vietqr.io/image/MB-VQRQALEAF2999-qr_only.png?...`):
  - lần này tải được (200, image/png);
  - nhưng mất 7,8 giây cho ảnh đầu, các ảnh sau 1,4 đến 2,8 giây.
- **Kết luận:** lỗi không nằm ở số tài khoản hay nội dung. Gốc là ảnh mã QR được TẢI TỪ MÁY CHỦ NGOÀI (img.vietqr.io) mỗi lần hiện. Mạng cửa hàng chậm, dịch vụ đó chậm hay chặn là ảnh vỡ, đúng như ảnh chụp.
- `docs/bai-hoc-su-co.md` (mục 22/09, #352) đã ghi đúng rủi ro này: "Mã QR thanh toán chuyển khoản (img.vietqr.io) vẫn còn phụ thuộc mạng ngoài, chưa xử lý trong đợt này". Đây là lần lỗi lặp lại.
- Repo đã có thư viện vẽ QR tại máy là `vagabond/public/js/vendor/qrcode.js`, đang dùng cho QR xuất hoá đơn trên bill (#352, `27-in-ngam.js`). Chỉ cần dùng lại, không cần thư viện mới.

## Mọi chỗ đang lấy ảnh QR từ mạng ngoài (main `42cb9fb9a`)

| Chỗ | Tệp | Ghi chú |
|---|---|---|
| Tính tiền tại quầy | `public/js/bep/09-tinh-tien-quay.js` `posQrUrl` dòng 1620 | ca anh chụp |
| Doanh số Sales: hoá đơn và nhập tay | `public/js/bep/08-doanh-so-sales.js` `dsvVeQr` dòng 793, `dstVeQr` dòng 1545 | gọi `posQrUrl` |
| Khách, ca, hợp đồng | `public/js/bep/11-khach-ca-hop-dong.js` dòng 489 | tự ghép URL riêng |
| Màn hình phía khách | `www/man-hinh-khach.html` dòng 235 (`g.qr.url`), dòng 330 là dữ liệu mẫu | URL do máy chủ hay màn quầy gửi sang |
| Trang thanh toán đơn web | `trang/tt.html` dòng 117 (`d.qr`), nguồn `thanh_toan.py` `xem` dòng 288 đến 300 (`VIETQR_ANH`) | khách mở trên điện thoại |
| PDF công nợ gửi khách | `cong_no.py` `_qr_data_uri` dòng 1276 | máy chủ tải ảnh rồi nhúng; mạng lỗi là PDF mất QR |

## Việc cần làm

### 1. Một nguồn duy nhất dựng chuỗi VietQR (điều 18)

- **Hàm THUẦN dựng chuỗi** EMVCo VietQR theo chuẩn NAPAS, gồm: BIN ngân hàng, số tài khoản (kể cả tài khoản ảo chữ và số như `VQRQALEAF2999`), số tiền, nội dung, mã kiểm CRC16.
  - Có bản JS cho trình duyệt và bản Python cho máy chủ.
  - Hai bản phải ra cùng một chuỗi cho cùng đầu vào; có ca kiểm đối chiếu chéo.
- **Tên ngân hàng sang BIN:** dùng bảng sẵn có trong `tai_khoan.py` (gần dòng 106), không lập bảng thứ hai.
- **Đơn Pancake:** đã có `qr_text` do Pancake cấp thì dùng nguyên chuỗi đó, không dựng lại.
- **Ca kiểm chốt:** không còn chỗ nào trong mã chạy thật trỏ tới `img.vietqr.io`, `api.vietqr.io/image` hay dịch vụ vẽ QR ngoài. Dò chuỗi được dùng cho ca chốt này (điều 16).

### 2. Vẽ tại máy

- **Trình duyệt:** dùng `vendor/qrcode.js` vẽ ra SVG hoặc data URI ngay trong trang. Màn tính tiền phải hiện mã tức thì khi số tiền đổi, kể cả lúc mạng ra ngoài bị chặn.
- **Hai trang ngoài app:** `www/man-hinh-khach.html` và `trang/tt.html` nạp thư viện từ `/assets/vagabond/js/vendor/qrcode.js` cùng tên miền. Không dùng CDN.
- **PDF công nợ:** máy chủ vẽ QR bằng thư viện Python có sẵn trong môi trường Frappe (kiểm trên bench, ví dụ `pyqrcode` mà Frappe đã cài cho xác thực hai lớp), rồi nhúng data URI. Không tải ảnh ngoài.

### 3. Không bao giờ để ô trống câm

- Không vẽ được mã (thiếu tài khoản, thiếu BIN, lỗi thư viện): hiện câu tiếng Việt nói rõ thiếu gì, kèm đủ số tài khoản, ngân hàng, số tiền, nội dung để khách chuyển tay.
- Không hiện ảnh vỡ trong mọi trường hợp.

### 4. Kiểm bằng ứng dụng ngân hàng thật

- Đây là điều bắt buộc trước khi xin merge. Bộ kiểm chỉ chứng minh chuỗi đúng định dạng, không chứng minh app ngân hàng đọc được.
- Đối chiếu chuỗi tự dựng với chuỗi của img.vietqr.io cho cùng đầu vào: giải mã ảnh của họ ra chuỗi, so từng trường.
- Ghi lên PR kết quả quét bằng app MB (hoặc app bất kỳ hỗ trợ VietQR) cho ba ca:
  - tài khoản ảo của Trần Cao Vân;
  - tài khoản ảo của điểm NVHTN;
  - một tài khoản thường.
- Mỗi ca ghi app nhận đúng số tiền và nội dung không. Phần nào không tự quét được thì ghi rõ, Claude và anh Việt quét thay.

## Ca kiểm bắt buộc

1. **Chuỗi VietQR:** ra đúng cho `VQRQALEAF2999`, 160.000, `TCVG8FRJ`; CRC16 đúng. Đối chiếu với chuỗi giải mã từ ảnh img.vietqr.io (ghi chuỗi mẫu vào ca kiểm, không gọi mạng lúc chạy bộ kiểm).
2. **JS và Python** ra cùng chuỗi cho cùng bộ đầu vào, ít nhất 5 bộ: có dấu tiếng Việt trong nội dung, nội dung dài, số tiền 0, tài khoản thường, tài khoản ảo.
3. **Màn tính tiền (node, `gia_lap_trang.js`, chặn mọi mạng ngoài):** thêm món, chọn Chuyển khoản thì mã hiện ra không cần mạng. Đổi số tiền thì mã đổi theo.
4. **Hai màn Doanh số Sales và màn Khách, ca, hợp đồng:** mã hiện khi mạng ngoài bị chặn.
5. **Màn hình phía khách và trang `tt.html`:** mã hiện khi mạng ngoài bị chặn.
6. **PDF công nợ:** có QR khi chặn mạng ngoài.
7. **Thiếu tài khoản:** hiện câu báo, không có thẻ `img` vỡ.
8. **Ca chốt:** không còn URL vẽ QR ngoài.
9. **Đột biến** theo điều 17: làm sai CRC, bỏ trường số tiền, quay lại URL ngoài. Báo đúng số bắt được.
10. **Bài học:** thêm một mục vào `docs/bai-hoc-su-co.md` khép lại câu "chưa xử lý trong đợt này" của mục #352.

## Ràng buộc

- Không sửa dữ liệu cũ.
- Không hook trên "*". Không dùng em dash hay en dash. Hàm whitelisted mới ghi vào `thu_cua_ngo.py`.
- **Phiên bản:** đọc main và mọi nhánh đang mở ngay trước khi đặt số. 593 đã thuộc PR #471, PR #469 cũng đang cần một số. Lấy số kế tiếp chưa ai dùng, thêm đúng một dòng patch, dựng lại `app_bep.js`.
- **Cổng kiểm:** chạy đủ `chay.py -im`, giả lập CI không có requests, `dung_app_bep.py --kiem`, `kiem_truoc_deploy.sh`.
- **Bàn giao theo INSTRUCTION_VAGABOND:**
  - tự đẩy lên nhánh, đọc lại SHA remote;
  - dòng đầu `[ĐÃ SỬA XONG]` hoặc `[BỊ CHẶN]`, kèm khối telegram-tomtat và `@claude review <SHA>`.
- Không merge, không deploy.

## Bàn giao Codex 13/10/2026

- Phạm vi sáu nhóm màn và in bill đã chuyển sang dựng QR tại máy. `tai_khoan.py` cấp BIN từ bảng duy nhất; `qr_text` Pancake giữ nguyên. Bộ dựng JS/Python kiểm chéo, có fallback chuyển tay.
- APPVER 594, một patch594. Thời điểm chọn: main592; PR474592, PR473593, PR471593, PR469592, PR464589, PR422577, PR401547. PR473 và PR471 đang trùng593 là việc của hai PR đó, bản này không sửa.
- Kiểm chuyên biệt: `thu_qr_chuyen_khoan_474.py`, các harness `qr_*474.js`, `phieu_doi_no_571.js`; bench bổ sung `qr_474.py` dựng SVG và PDF thật, chặn mạng ngoài.
- Tham chiếu TCV giải mã từ ảnh thật: `00020101021238570010A000000727012700069704220113VQRQALEAF29990208QRIBFTTA530370454061600005802VN62120808TCVG8FRJ630450D4`.
- Còn cổng quét app ngân hàng thật TCV/NVHTN/tài khoản thường. Đã hỏi anh Việt xác nhận NVHTN và tài khoản thường để gửi QR thử; chỉ kiểm màn nhận diện, không chuyển tiền. Không merge/deploy.
- Kết quả cổng, SHA remote và bench chính thức nằm trong comment bàn giao trên PR #474; không coi tài liệu này là bằng chứng các cổng chưa chạy đã đạt.
- Tương thích màn khách đang mở trước nâng bản: sender vẫn gửi `url`, nhưng chỉ là data URI tại máy; receiver mới bỏ qua URL và dựng từ trường cấu trúc. Ca sender thật và ca từ chối URL ngoài cùng được kiểm để không đổi giao thức làm tab cũ mất QR.
