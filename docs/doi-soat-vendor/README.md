# Đối soát vendor, thiết kế đã duyệt

Nguồn công việc: [Issue #420](https://github.com/thevagabondpatisserie/vagabond/issues/420).
Anh Việt duyệt giao diện ngày 03/10/2026, giao Codex làm chính và Claude review
để cùng hoàn thiện tới merge. Đây là PR đang triển khai, chưa phải bản phát hành.

## Có trong vòng đầu

- [Maquette HTML](maquette.html) tái dựng đủ 8 màn mobile và màn trung tâm
  desktop của 9 JPEG anh đã duyệt. Dữ liệu hoàn toàn minh họa; không gọi API.
  Mở file bằng trình duyệt với `?s=01` tới `?s=08`; màn `?s=03` có bố cục desktop.
- `vagabond/doi_soat_nguon.py`: kiểm thuần báo cáo tiền bán đã được adapter
  chuẩn hóa. Chưa có adapter đọc Excel/PDF/email, endpoint hoặc lưu cơ sở dữ liệu.
- `thu_doi_soat_nguon.py`: ca hành vi đã gắn vào cổng tầng khung.
- Thiết kế, ranh giới và các cổng còn thiếu bên dưới. Bản sửa review đặt
  APPVER/patch v577 theo yêu cầu anh Việt; chưa nối API/UI hoặc đổi chứng từ,
  thông tin tài khoản, lịch chạy hay quyền production.

Ảnh JPEG gốc được gửi trực tiếp cho anh trước khi duyệt. Repo giữ nguồn HTML
nhẹ để reviewer dựng lại, không nhân bản ảnh/log/tệp nghiệp vụ thật vào lịch sử.
`python3 -m http.server 8772 --bind 127.0.0.1 --directory docs/doi-soat-vendor`
cho phép mở `http://127.0.0.1:8772/maquette.html?s=03` ở 430px và 1280px.
Ảnh maquette không thay kiểm màn thật ở 390x844 sau khi viết UI.

## Kết quả nghiệp vụ cần đạt

Mỗi sáng kế toán biết nguồn nào đã về, khoản nào chưa khớp và ai cần làm gì.
Một file hỏng không làm mất hoặc chặn các file khác. Nguồn không về phải hiện
thiếu/lỗi, không được dùng số 0 để ngụ ý không có giao dịch.

Trên hóa đơn bán, nút **Đối soát** mở phần tiền của đúng hóa đơn trong cùng
trung tâm Kế toán. Hóa đơn 270.000, phí 54.000, phần tiền ròng 216.000 trong
đợt trả gộp 2.160.000 của 10 đơn chỉ được nhận phần 216.000 của nó. Đã nhận
đủ tiền nhưng chưa nối chứng từ phí vẫn là **Chờ hạch toán**.

Ba lớp không được gộp làm một: **đủ nguồn**, **khớp tiền**, **đủ chứng từ**.
Hóa đơn quầy đánh dấu đã thu không chứng minh vendor đã chuyển hoặc sổ cái
đã tất toán. Báo cáo vendor cũng không phải sao kê tiền vào ngân hàng.

## Nhóm nguồn và cách đối chiếu

| Nhóm | Nguồn dự kiến | Đối chiếu |
|---|---|---|
| Tiền bán | GreenSM Ngon, GrabFood, ShopeeFood, OnePay, Payoo, Shinhan POS | Đơn ERP, báo cáo gốc, ngân hàng, chứng từ phí/cấn trừ |
| Chuyến đi | Be Business, Grab Business, GreenSM Taxi | Chuyến, mục đích, người đi, đơn liên quan, hóa đơn mua, APP đã có |
| Thẻ tín dụng | Sao kê thẻ Shinhan | Dư đầu + phát sinh/phí/lãi - trả nợ/hoàn = dư cuối; tiền trả sau ngày chốt tách riêng |

Không coi chuyến trả trực tiếp là công nợ cần trả lần nữa. Không ghi chi phí
lần hai khi trả nợ thẻ. Không suy phương thức kế toán từ tên ngân hàng: tài
khoản công ty và tài khoản cá nhân/141 đi qua đúng luật đã cấu hình.

## Thiết kế đầu nhận chung

Email hoặc tải tay -> lưu bản gốc riêng tư -> nhận diện mẫu/merchant/kỳ ->
chuẩn hóa -> kiểm dòng và tổng -> xem trước -> nhận phần hợp lệ vào hàng
đợi -> gợi ý nối -> kế toán xác nhận qua cửa core hiện có.

1. Core `Email Account`/`Communication`/`File` giữ nguồn và căn cứ. Email
   dùng hộp thư ERP đã khai, không mặc định là Gmail. Mẫu có báo cáo trong
   thân thư phải đọc phần đó; file `.xls.zip` mã hóa cần bí mật riêng tư.
2. Bộ nhận cùng dùng một khóa file và khóa sự kiện, kèm phiên bản adapter.
   Hash byte phát hiện tải lại đúng tệp; ID kinh tế bắt trùng giữa Excel,
   Sheets, báo cáo ngày và tháng. Không lấy tên tệp, dòng số hoặc số tiền
   làm ID. File sửa lại phải giữ hai phiên bản và yêu cầu chọn căn cứ.
   (v583) Sự kiện đã nhận mà báo cáo sau ghi khác nội dung được giữ làm
   "bản sửa"; kế toán bấm "Dùng bản sửa" thì dòng cũ thành Đã thay (giữ để
   tra, trỏ tới dòng mới) và cả hai nguồn đối chiếu lại. Sự kiện một báo cáo
   có nhưng đã nhận ở nguồn khác được ghi quan hệ riêng, để tổng thực nhận
   của bất kỳ tập nguồn nào cũng tính mỗi sự kiện đúng một lần.
3. Merchant lấy từ nội dung nguồn và cấu hình máy chủ; tên thư mục/tệp chỉ
   là gợi ý. File nhiều merchant phải chia phạm vi rõ. Hàng thiếu ánh xạ
   xuất hiện trong hàng đợi, không biến mất khi dựng chứng từ thất bại.
4. Schema khai rõ locale, tiền tệ, đơn vị, múi giờ, kỳ và chiều dấu. Không
   đoán nhân 1.000, lấy số lỗi thành 0 hoặc đoán phí từ hợp đồng cũ. Lỗi
   đơn vị giữ nguồn **Cần xử lý**, vẫn cho xem căn cứ.
5. Nhận phần hợp lệ chỉ là staging. Kỳ chỉ đủ nguồn khi đúng số dòng và
   tổng kiểm soát, không có nhóm xung đột. Lỗi toàn file phải được caller
   lưu trạng thái để tiếp tục file sau, không chỉ trả popup.
6. Chạy đề xuất 07:00 giờ Việt Nam; quét cửa sổ chồng lấn, có watermark bền
   và thử lại có giới hạn. Không phụ thuộc thư chưa đọc. Hạn nguồn theo
   vendor/kỳ/lịch, phân biệt thiếu file với job không chạy; cảnh báo sức
   khỏe cần đường giám sát độc lập. CHƯA bật lịch trong vòng đầu.

### Mô hình lưu cần review trước khi nối API

Ưu tiên tái sử dụng core; chưa tạo DocType mới. Cần đọc schema và thử bench
`Data Import` + `Data Import Log` cho phiên nhận và lỗi, `File` riêng tư cho
payload chuẩn hóa, `Communication` cho thư gốc, `ToDo` cho việc cần xử lý.
Không dùng Bank Transaction giả để giữ dòng vendor hoặc ép dữ liệu hàng đợi
vào GL. Nếu core không giữ được phiên bản, khóa duy nhất và audit cần thiết,
ghi cụ thể chỗ thiếu trên PR trước khi đề xuất bổ sung cấu trúc.

Đây là điểm thiết kế còn mở, KHÔNG phải khẳng định Data Import phù hợp. Claude
review mô hình trước, Codex chọn bằng bằng chứng core và ca insert/reload.
Việc có trạng thái trên maquette không tự tạo quyền bổ sung một DocType.

## Nối vào phần đang có

- `nhap_sao_ke.py`: dùng lại đường File riêng tư khi thích hợp; không dùng
  bộ đọc float nuốt lỗi cho tiền chuẩn hóa, không nhập báo cáo vendor thành
  sao kê ngân hàng. Core upload hiện chưa hỗ trợ tất cả mẫu ZIP/PDF/XLS.
- `khop_sao_ke.py`, `doi_soat_sepay.py`, `chiem_sao_ke.py`: đọc quyền sở hữu
  giao dịch và allocation từ DB, khóa khi ghi, không nhận trạng thái do
  client hoặc snapshot xem trước gửi lên.
- `can_tru_san.py` / `Vagabond Can Tru San`: nối chứng từ phí đã có, công ty,
  NCC/MST, tiền tệ và phần còn chưa cấn. Không lập một luồng bút toán song song.
- `hop_thu.py`: cấu hình thư qua core và quyền quản trị. Không lưu mật khẩu
  trong JS, nguồn Git, tin nhắn lỗi hoặc log.
- `phan_tich.dung_bang_sang_tu_dong`: khảo sát ghép việc sáng vào cửa sẵn có.
- `doi_soat.py` hiện là đối chiếu mã hàng Pancake, không phải mô đun này.

## Giao diện và nghiệm thu

| Màn maquette | Thứ tự khối, nhãn và tác vụ |
|---|---|
| 01 | Chi tiết đơn -> vùng tiền/phương thức hiện có -> Đối soát, giữ thông tin nguồn hiện tại |
| 02 | Tóm tắt hóa đơn -> 4 bước nguồn/tiền/chứng từ -> phần tiền của tờ -> đợt gộp -> Nối chứng từ phí |
| 07 | Kế toán -> ô Đối soát, phân biệt Đối soát hóa đơn điện tử |
| 03 | 3 nhóm -> việc sáng -> tổng -> tìm -> 3 hàng chip -> danh sách -> Tải file |
| 08 | Sức khỏe nhận nguồn -> nguồn lỗi và lý do -> Thử lại / Tải file, nguồn đã nhận vẫn xem được |
| 04 | Chọn nguồn/file -> xem trước tổng/dòng -> lỗi/trùng -> Nhận dòng hợp lệ; giữ phần lỗi |
| 05 | Chuyến -> mục đích/đơn -> hóa đơn -> trả trực tiếp hoặc công nợ -> nối hồ sơ hiện có |
| 06 | Kỳ thẻ -> phương trình số dư -> phát sinh -> chứng từ -> trả nợ sau kỳ riêng |

Khung dùng `frame`, `card`, chips, sheet, `confirmSheet`; ô danh mục có tìm.
Nút chính dính đáy, chạm 44px; khối giải thích tối đa hai dòng rồi mở rộng;
không để cảnh báo đẩy nút ra khỏi màn đầu 390x844. Maquette đang là ảnh dài,
triển khai phải đo điều kiện này bằng màn thật. Không có sửa UI runtime ở vòng đầu.

Trạng thái 0 dòng: “Chưa có nguồn đối soát. Nhận từ email hoặc tải file.”
Một dòng: rõ căn cứ, ba lớp trạng thái và nút bước tiếp. Nhiều dòng: tìm/lọc
trước phân trang, số/tổng cùng phạm vi, giữ dòng thiếu cấu hình. Lỗi mạng:
“Không nhận được nguồn. Thử lại hoặc tải file; các nguồn đã nhận vẫn xem được.”
Không đếm dữ liệu của công ty/điểm bán ngoài quyền rồi chỉ ẩn ở trình duyệt.

## Hợp đồng module vòng đầu

`xem_truoc(nguon, cac_dong, da_nhan)` chỉ nhận dữ liệu đã chuẩn hóa từ adapter
tương lai. `nguon` gồm cong_ty/vendor/merchant/tien_te, tu_ngay/den_ngay ISO,
dinh_dang chuan/vi/en, so_dong và tong_thuc_nhan từ tổng kiểm soát nguồn.
Không tự tính tổng kỳ từ đúng các dòng vừa đọc rồi gọi đó là đối chứng.

Mỗi dòng giữ lại phạm vi, ngay, loai ban/hoan/dieu_chinh, ma_su_kien ổn định,
ma_don có số 0 đầu, tien_hang/phi/dieu_chinh/thuc_nhan. Phương trình có dấu:
tiền hàng - phí + điều chỉnh = thực nhận. Loại điều chỉnh cần mã căn cứ do
adapter xác minh; chưa tự suy sự kiện nào là hoàn tiền. Chưa hỗ trợ dòng
phí cấp kỳ không có mã căn cứ, ngoại tệ hoặc tiền hơn hai chữ số lẻ.

`du_nguon` chỉ nói đủ kiểm dữ liệu nguồn trong một snapshot; KHÔNG phải đã
nhận, đã khớp tiền, đã ghi sổ hoặc an toàn trước hai worker. Snapshot
`da_nhan` do máy chủ đọc; khóa DB/unique key phải bổ sung tại cửa ghi trước
khi có endpoint nhận file. Không expose helper trực tiếp cho client tự khai
công ty/merchant/snapshot và coi đó là quyền nhập.

## v579: Claude làm trọn vòng đầu (06/10/2026)

Anh Việt giao Claude dẫn đầu, Codex rà soát. Phạm vi anh chốt: đủ mười
nguồn trong một lần, nối từng hoá đơn, nhận từ email, và khi kế toán bấm
nhận thì CHỈ LƯU VÀ ĐỐI CHIẾU (không lập phiếu, không bút toán phí).

| Lớp | Tệp | Việc |
|-----|-----|------|
| Đọc tệp | `vagabond/doi_soat_doc.py` | CSV/XLSX/XLS/PDF/ZIP thành lưới hoặc dòng chữ; giới hạn 20 MB, 20.000 dòng, ZIP một tầng 20 tệp, ZIP có mật khẩu bị từ chối. |
| Mẫu | `vagabond/doi_soat_mau.py` | Mười nguồn, mười bốn mẫu; mỗi mẫu tự nhận diện, đọc, kiểm phương trình từng dòng và tổng in trên tệp. Đặc tả: `schema/dac-ta-10-nguon.md`. |
| Đối chiếu | `vagabond/doi_soat_khop.py` | Thuần: xem trước (mới, đã có, lỗi), nối hoá đơn bán theo mã rồi theo tiền, tiền về theo nội dung sao kê, phương trình số dư thẻ. |
| Máy chủ | `vagabond/doi_soat_vendor.py` | Tải tay, xem trước, nhận, đối chiếu lại, danh sách, chi tiết, khối trên hoá đơn, sức khoẻ nguồn, hook thư vendor và lượt quét mỗi giờ. |
| Lưu | doctype `Vagabond Doi Soat Nguon` (khoá duy nhất `sha256`), `Vagabond Doi Soat Dong` (khoá duy nhất `khoa`, cùng công thức `chuan_dong`) | Không xoá được. |
| Màn | `52-doi-soat-vendor.js`, ô trên trang chủ nhóm Kế toán, khối trên Chi tiết đơn | Trung tâm, nhận file, chi tiết ba lớp. |

Đã kiểm trên 38 tệp thật (không đưa vào repo): mọi tệp nhận đúng mẫu, 0 dòng
lỗi, mọi tổng khớp, trừ bản Payoo xuất lại từ Google Drive dạng ô số Excel
(bị từ chối có chủ ý, cần tải tệp CSV gốc).

Việc còn chờ anh Việt: MID Shinhan nào thuộc cửa hàng nào; khai Email Account
cho các hộp thư nhận báo cáo (anh tự gõ mật khẩu); xác nhận định dạng CSV
Payoo gửi qua email; bảng kê Grab for Business kiểu cũ (4 tab) chưa đọc.

## v588: hai tệp kế toán gửi mà máy chưa nhận (#457, 08/10/2026)

Chị Dung gửi hai tệp, máy đều báo "Chưa nhận ra mẫu". Cả hai đều là tệp thật,
không phải mẫu mới hoàn toàn:

- Xanh SM Ngon `Revenue_Report...xlsx` tải từ cổng Xanh SM: tệp CÓ đủ tab Detail
  Transactions và Summary, nhưng khai kích thước sheet là `A1` nên openpyxl đọc
  mỗi sheet đúng một ô. `doi_soat_doc.doc_xlsx` nay gọi `ws.reset_dimensions()`
  trước khi đọc, để máy dò lại từ ô thật. Tệp 06/10 đọc ra 4 đơn, thực nhận
  752.550 đúng bằng Summary.
- Thẻ tín dụng Shinhan: ngân hàng gửi sao kê dạng ảnh, chị Dung gõ tay sang
  Excel. Mẫu mới `the_shinhan_bang` nhận bằng bộ tiêu đề cột (Ngày giao dịch,
  Ngày bút toán, Đơn vị chấp nhận thẻ, Số tiền gốc, Số tiền (VND)), lấy bốn số
  cuối thẻ từ dòng `Card Number`, coi dòng sau `Your Spend For This Month` là
  phí, giữ nguyên tiền gốc ngoại tệ (ví dụ `USD 8.42`) trong `them`, kiểm tổng
  bằng Spend + Fees = Billing, và suy kỳ là tháng của ngày bút toán lớn nhất
  (có cảnh báo vì bảng gõ tay không có ô kỳ sao kê). Phương trình số dư thẻ
  không chạy được vì thiếu Đến hạn, `ky_the` ghi rõ lý do thay vì tính sai.
  Dòng thẻ gõ tay đánh dấu `go_tay=1` để sau này phân biệt với PDF gốc.

Mục 3 của issue: khi chưa nhận ra mẫu, màn không liệt kê tên các mẫu nữa (người
dùng không làm gì được với danh sách đó) mà nói việc cần làm: bấm Lưu nguồn để
máy giữ tệp với tên nguồn "Mẫu chưa nhận", gửi tệp cho kỹ thuật, không cần làm
gì thêm. Kèm ba dòng đầu máy đọc được (`doi_soat_mau.dau_tep`) ở cả màn xem
trước và chi tiết nguồn, để kỹ thuật biết lấy tệp nào làm mẫu.

Tệp thật của chị Dung có số thẻ và tên chủ thẻ nên không đưa vào repo; ca kiểm
dựng tệp xlsx nhỏ cùng cấu trúc (kể cả khai kích thước sai) ngay trong
`thu_doi_soat_mau_579.py`.

## Các cổng còn phải làm trước phát hành

- [x] Anh Việt duyệt maquette, ghi phạm vi và issue, tạo nền kiểm nguồn.
- [ ] Claude review kiến trúc, module thuần và ca kiểm; sửa findings theo SHA.
- [ ] Chốt persistence bằng core, quyền đọc/ghi/file và unique key có bench.
- [x] Adapter các biến thể, bộ file giả đại diện từng schema; sai mẫu hiện lỗi (v579).
- [x] Hai cửa email/tải tay, lỗi từng file, retry/backfill, giới hạn ZIP/PDF (v579).
- [x] UI đã duyệt, nối cùng nguồn trên từng hóa đơn và trung tâm, phân quyền (v579).
- [ ] Ghép gợi ý dựa ID/phạm vi, phân bổ gộp/từng phần/hoàn đúng bằng core.
- [ ] Bench trên SHA cuối: mất phản hồi, đồng thời, rollback, không dư dữ liệu;
  không tái dùng Bank Transaction; cross-company; chứng từ bị hủy/đổi sau preview.
- [ ] Cổng CI, ảnh UI thật 390x844/desktop, reviewer kết luận và release gates.

Không chuyển tiền, gửi biên bản chấp thuận vendor hoặc tự ghi sổ chỉ vì file
đã khớp. Mỗi vòng push gom một nhóm sửa; gọi Claude đúng full SHA, không lặp
tag khi chưa có thay đổi. Không tự mở lịch polling chờ review.
