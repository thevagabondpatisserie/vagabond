
=================== be.md
# Be for Business (Be Group) - bảng kê cước vận tải

Nguồn: Drive `07_BeForBusiness` (5 Google Sheets). Đã đọc kỹ 3 tệp: kỳ 26/05-25/06/2025, 26/08-25/09/2025, 26/05-25/06/2026.

## Tệp và kỳ
- Tên gốc: `CÔNG-TY-TNHH-PATISSERIE-VAGABOND-<YYYYMMDD từ>-<YYYYMMDD đến>-<unix ts lúc xuất>`; trên Drive có thêm tiền tố tùy ý (`Copy of `, `2509_`). Lấy kỳ từ tên tệp HOẶC ô A7, ưu tiên A7.
- Kỳ: ngày 26 tháng trước đến ngày 25 tháng này (không theo tháng dương lịch).
- Định dạng: xlsx của Be đã đổi sang Google Sheets, 1 sheet tên `corp_reconciliation`.
- MỌI ô kể cả số đều là CHUỖI: `"65,000"` (dấu phẩy ngăn nghìn), dòng tổng có khoảng trắng hai đầu `" 21,486,000 "`. Parser phải strip + bỏ `,` rồi ép int.
- Ngày cột B: 2025 là `2025-05-26`, 2026 là `26/05/2026`. Chỉ có ngày, KHÔNG có giờ.

## Định danh
- A1 `CÔNG TY CỔ PHẦN BE GROUP`, A2 `MST: 0108269207` (bên bán), A3 địa chỉ Be.
- A6 `CHI TIẾT CƯỚC PHÍ DỊCH VỤ VẬN TẢI`; A7 `KỲ: từ ngày dd/mm/yyyy đến ngày dd/mm/yyyy`.
- A9 `Kính gửi:` + C9 `CÔNG TY TNHH PATISSERIE VAGABOND`; ô cuối dòng 9 `ĐVT: VND` (cột R ở mẫu 21 cột, Y ở mẫu 33 cột).
- A11 câu dẫn. Không có mã hợp đồng / mã tài khoản doanh nghiệp.

## Hai bố cục (tìm dòng có A=`STT`, hiện là dòng 13)
Bố cục 2025 (21 cột A-U) và bố cục 2026 (33 cột A-AG, chèn 7 cột G-M và thêm 5 cột AC-AG). Map theo TÊN tiêu đề, không theo chữ cái cột. Tiêu đề có xuống dòng và khoảng trắng đôi, cần chuẩn hóa (`\n`->space, gộp space).

| # | Tiêu đề chính xác | Ý nghĩa | Kiểu / ví dụ |
|---|---|---|---|
| 1 | STT | số thứ tự | "1" |
| 2 | Ngày | ngày chuyến | "26/05/2026" |
| 3 | Mã đặt chuyến | ID chuyến | "1000000001" (10 chữ số, giữ dạng chuỗi) |
| 4 | Loại phương tiện | dịch vụ | Giao hàng Siêu tốc, Giao hàng Siêu rẻ 2H, beBike, beBike Plus, beCar 4 chỗ, beCar 7 chỗ, beCar Plus, beCar 4 chỗ đường dài 1 chiều |
| 5 | Điểm đón | địa chỉ đón | "<địa chỉ bếp Tân Bình>" |
| 6 | Điểm đến | địa chỉ trả | "<địa chỉ khách>" |
| 7* | Tên người đi | người đặt/đi | "The Vagabond" hoặc tên nhân viên |
| 8* | Biển kiểm soát | biển số tài xế | "59X1-123.45" |
| 9* | Tên hàng hóa\n(tên hàng hóa gửi hàng) | loại hàng (chỉ đơn giao) | "Đồ đóng gói,Dễ vỡ" |
| 10* | Tên người gửi hàng | | "The Vagabond" |
| 11* | Địa chỉ người gửi hàng | | địa chỉ |
| 12* | MST người gửi hàng | có khi chuyến xe xin HĐ | "0318561568" |
| 13* | Mã Định danh người gửi hàng | luôn trống | |
| 14 | Cước phí vận tải | cước gốc | 65000 |
| 15 | Phí cầu đường (Phí khác) (*) | phí cầu đường, sân bay | 9000 |
| 16 | Phụ phí giờ cao điểm | | 0 |
| 17 | Phí điểm đón (*) | | 0 |
| 18 | Phí bảo hiểm | | 0 |
| 19 | Phí thông báo tình trạng đơn hàng (*) | | 0 |
| 20 | Chiết khấu/Giảm giá | khuyến mại (số dương) | 5000 |
| 21 | Tổng tiền | | 60000 |
| 22 | Cước phí được áp dụng  CKTM | cơ sở chiết khấu thương mại (2 space) | 60000 |
| 23 | Tỷ lệ CKTM | phần trăm, chuỗi "4" | 4 |
| 24 | Chiết khấu thương mại (*) | | 2400 |
| 25 | Tổng tiền thanh toán sau khi trừ CKTM | số phải trả từng chuyến | 57600 |
| 26 | Phí sử dụng ứng dụng (*) | phần phí nền tảng | 6210 |
| 27 | Cước phí vận tải chịu thuế GTGT (*) | phần cước vận tải | 53790 |
| 28 | Driver city ID | mã thành phố tài xế | "189" (HCM), gặp 194, 200 |
| 29* | Thông tin XHĐ - TÊN CÔNG TY | tên xuất HĐ | tên công ty hoặc trống |
| 30* | Thông tin XHĐ - MST | | |
| 31* | Thông tin XHĐ - Địa chỉ | kèm dòng "Email nhận hoá đơn:" trong cùng ô | |
| 32* | Thông tin XHĐ - Email nhận hóa đơn | email nhận HĐ | "<email>" |
| 33* | Driver city ID | TIÊU ĐỀ TRÙNG, thực chứa lại email nhận HĐ | "<email>" |
(*) dấu sao trong tiêu đề là của Be; cột đánh `*` ở cột # chỉ có trong bố cục 2026.

## Phương trình (kiểm trên 1.702 dòng, 0 sai trừ ghi chú)
- `Tổng tiền = Cước + Cầu đường + Cao điểm + Điểm đón + Bảo hiểm + Thông báo - Chiết khấu/Giảm giá`
- `Cước áp dụng CKTM = Tổng tiền - Phí cầu đường` (1 ca có phí sân bay 9.000: 113.000 -> 104.000; còn lại bằng nhau)
- `CKTM = round(Cước áp dụng CKTM x Tỷ lệ/100)`, tỷ lệ luôn 4
- `Tổng tiền thanh toán sau CKTM = Tổng tiền - CKTM`
- `Phí sử dụng ứng dụng + Cước chịu thuế GTGT = Cước áp dụng CKTM`
- Tỷ lệ phí ứng dụng / tổng KHÔNG cố định (10,35% giao hàng, 15,5-16,25% xe ô tô...): đọc, không tự tính.

## Dòng tổng và số kiểm soát
- Dòng A=`Tổng` (A:B gộp): tổng các cột tiền, cột Tỷ lệ để trống.
- 2 dòng sau: A=`Tổng số tiền thanh toán trong kỳ:` (A:E gộp), giá trị ở cột Cước (N hoặc G) = tổng cột "Tổng tiền thanh toán sau khi trừ CKTM". Đây là số công nợ phải trả Be.
- Tiếp theo: đoạn điều khoản (Be gửi bảng kê trong 2 ngày làm việc sau kỳ, im lặng 2 ngày = chấp nhận, Be xuất HĐ GTGT theo bảng kê), dòng `(*): Các chỉ tiêu thể hiện trên hóa đơn GTGT`, chữ ký `Người mua hàng` / `Người bán hàng`.
- Số mẫu: 2026-06: 526 chuyến, Tổng tiền 21.486.000, phải trả 20.626.560. 2025-09: 604 chuyến, phải trả 23.073.600.
- Dừng đọc dữ liệu khi gặp ô A không phải số nguyên.

## Đơn vị, VAT, hóa đơn
- Đơn vị VND: ô `ĐVT: VND` dòng 9; số nguyên, không thập phân.
- Không có cột tiền VAT và không có số hóa đơn điện tử. Be xuất HĐ GTGT gộp cho cả kỳ SAU khi bảng kê được chấp nhận; các cột đánh (*) là chỉ tiêu lên hóa đơn (phí ứng dụng, cước chịu thuế, CKTM, cầu đường...). Số HĐ phải lấy từ m-invoice/hộp thư, nối theo kỳ + tổng tiền.
- Cột XHĐ (2026) chỉ là thông tin người mua để xuất HĐ, không phải số HĐ.

## Khóa duy nhất
- `Mã đặt chuyến` duy nhất trong tệp (526/526, 604/604, 572/572). Khóa đề xuất: `be:<Mã đặt chuyến>`. Chưa thấy điều chỉnh/hoàn tiền dạng dòng âm.

## Trường giúp gắn chuyến với mục đích / người / đơn
- `Loại phương tiện`: "Giao hàng ..." = giao bánh cho khách (đa số, ~86%); beCar/beBike = đi lại.
- `Tên người đi` (2026): "The Vagabond" cho đơn giao, tên nhân viên cho chuyến xe.
- `Điểm đón`/`Điểm đến` + `Ngày`: so khớp với địa chỉ giao của đơn bán (không có giờ, không có mã đơn).
- `Tên hàng hóa`: loại hàng (Thực phẩm tươi, Đồ đóng gói, Dễ vỡ, Khác).
- `MST người gửi hàng` + cột XHĐ có giá trị khi chuyến xe khách xin hóa đơn công ty.
- Không có ghi chú, mã chi phí, phòng ban.

## Quirk
- Tiêu đề `Driver city ID` xuất hiện 2 lần (AB và AG), AG thực chứa email: map theo vị trí tương đối, không dùng dict theo tên.
- Ô số định dạng `#,##0.00` nhưng giá trị là chuỗi.
- Dấu cách đôi trong `Cước phí được áp dụng  CKTM`.
- Dữ liệu không sắp theo giờ trong ngày (sắp theo ngày, trong ngày lộn xộn).
- Vùng sheet thừa rất nhiều dòng trống (dimension tới dòng 753-1000).

## Fixture (CSV, bố cục 2026, đã ẩn danh; bỏ trống cột rỗng)
```csv
STT,Ngày,Mã đặt chuyến,Loại phương tiện,Điểm đón,Điểm đến,Tên người đi,Biển kiểm soát,Tên hàng hóa (tên hàng hóa gửi hàng),Tên người gửi hàng,Địa chỉ người gửi hàng,MST người gửi hàng,Mã Định danh người gửi hàng,Cước phí vận tải,Phí cầu đường (Phí khác) (*),Phụ phí giờ cao điểm,Phí điểm đón (*),Phí bảo hiểm,Phí thông báo tình trạng đơn hàng (*),Chiết khấu/Giảm giá,Tổng tiền,Cước phí được áp dụng  CKTM,Tỷ lệ CKTM,Chiết khấu thương mại (*),Tổng tiền thanh toán sau khi trừ CKTM,Phí sử dụng ứng dụng (*),Cước phí vận tải chịu thuế GTGT (*),Driver city ID,Thông tin XHĐ - TÊN CÔNG TY,Thông tin XHĐ - MST,Thông tin XHĐ - Địa chỉ,Thông tin XHĐ - Email nhận hóa đơn,Driver city ID
1,26/05/2026,1000000001,beCar 7 chỗ,KITCHEN_ADDR,STORE_ADDR,STAFF_A,51X-000.01,,,,0318561568,,"65,000",0,0,0,0,0,0,"65,000","65,000",4,"2,600","62,400","10,075","54,925",189,CÔNG TY TNHH PATISSERIE VAGABOND,0318561568,COMPANY_ADDR,invoice@example.com,invoice@example.com
2,26/05/2026,1000000002,Giao hàng Siêu tốc,KITCHEN_ADDR,CUSTOMER_ADDR_1,The Vagabond,59X-000.02,"Đồ đóng gói,Dễ vỡ",The Vagabond,KITCHEN_ADDR,,,"27,000",0,0,0,0,0,"5,000","22,000","22,000",4,880,"21,120","2,795","19,205",189,,,,,
3,22/06/2026,1000000003,beCar 7 chỗ,CUSTOMER_ADDR_2,AIRPORT_ADDR,STAFF_B,51X-000.03,,,,,,"110,000","9,000",0,0,0,0,"6,000","113,000","104,000",4,"4,160","108,840","16,258","87,742",189,,,,,
Tổng,,,,,,,,,,,,,"202,000","9,000",0,0,0,0,"11,000"," 200,000 "," 191,000 ",," 7,640 "," 192,360 ","29,128","161,872",,,,,,
Tổng số tiền thanh toán trong kỳ:,,,,,,,,,,,,,"192,360",,,,,,,,,,,,,,,,,,,
```

=================== grab_business.md
# Grab for Business - bảng kê tháng

Nguồn: Drive `08_GrabForBusiness` (20 Google Sheets, 2408 đến 2606). Đã đọc 5 tệp: 2408, 2412, 2504, 2512, 2606.

## Tệp và kỳ
- Tên: `YYMM - Bảng kê tháng MM.YYYY - CÔNG TY TNHH PATISSERIE VAGABOND`; một số tệp không dấu (`Bang ke thang`, `CONG TY`). Lấy YYMM từ 4 ký tự đầu.
- Kỳ: tháng dương lịch (01 đến cuối tháng).
- Google Sheets. Có 3 bố cục, phải nhận dạng theo nội dung (tên sheet / tiêu đề), không theo ngày:
  - A (2408, 2412): 4 sheet `tổng quan`, `hóa đơn chi tiết`, `hóa đơn điều chỉnh`, `diễn giải`; VAT một mức.
  - B (2504): như A nhưng tách VAT 8% và 10%.
  - C (2512, 2606): 1 sheet `Sheet1`, xuất thô từ portal, 45 cột tiếng Anh UPPER_SNAKE, tiêu đề dòng 1.
  - Chưa mở 2501-2503, 2505-2511, 2601-2605: mốc chuyển B->C nằm trong khoảng 2505-2512.

## Định danh công ty
- C: cột `COMPANY_NAME` = `CÔNG TY TNHH PATISSERIE VAGABOND` (2512 có hậu tố ` - GFB - Branch`), `PORTAL_ID` = `1000156989` (ổn định, dùng làm mã tài khoản).
- A/B: sheet `tổng quan` dòng 1-5: `CÔNG TY TNHH GRAB`, `Mã số thuế: 0312650437`, `BẢNG KÊ CÁC CHUYẾN ĐI TRONG THÁNG MM/YYYY`, `Từ ngày dd/mm/yyyy đến ngày dd/mm/yyyy`, `Hình thức: Xuất theo tháng`; cột `Tên công ty (Company Name)` trong chi tiết.

## Bố cục C (raw portal export)
Tiêu đề chính xác theo thứ tự (45 cột): TRANSACTION_TIME, CREATION_TIME, COMPLETION_TIME, COMPANY_NAME, PORTAL_ID, EMPLOYEE_NAME, EMPLOYEE_ID, EMPLOYEE_EMAIL_ADDRESS, GROUP_NAME, BOOKING_ID, VERTICAL, TAXI_TYPE, SOURCE, TYPE, TRIP_CODE, TRIP_DESCRIPTION, CITY, PICK_UP, INTERMEDIATE_DROPOFF, DROP_OFF, DISTANCE, DAX_ID, BASE_FARE, PROMO, TOLLS_AND_SURCHARGE, LATE_FEES, OTHER_FEES, AMOUNT, CURRENCY, PAYMENT_METHOD, BILLING_TYPE, PRE_VAT_DELIVERY_FEE, VAT_VALUE_DELIVERY_FEE, PRE_VAT_SERVICE_FEE, VAT_VALUE_SERVICE_FEE, NON_VAT_VALUE, INVOICE_NUMBER, INVOICE_TRACKING_ID, INVOICE_PAYMENT_TYPE, DRIVE_PLATE_NUMBER, GOODS_INFORMATION, ORDER_ID, VAT_INVOICE_DATE, VAT_INVOICE_SERIAL, VAT_TAX_AUTHORITY_CODE.

| Cột | Ý nghĩa | Kiểu / ví dụ |
|---|---|---|
| TRANSACTION_TIME / CREATION_TIME / COMPLETION_TIME | thời điểm ghi nợ / đặt / hoàn thành | `2026-06-01 16:58:04 +07:00` |
| EMPLOYEE_NAME, EMPLOYEE_EMAIL_ADDRESS | người đặt trên portal | "STAFF_A", "staff@example.com" (4 email/tháng) |
| EMPLOYEE_ID, TRIP_CODE, TRIP_DESCRIPTION | mã NV, mã chi phí, mục đích | luôn trống trong mẫu |
| GROUP_NAME | nhóm portal | "General" |
| BOOKING_ID | ID chuyến | `A-9DMETFEGWESRAV` |
| VERTICAL | transport / express | |
| TAXI_TYPE | dịch vụ | Bike, Bike Plus, Car, Car Plus, Car 6 chỗ ngồi, Car Tiết Kiệm, GrabExpress Nhanh/Ưu Tiên/Siêu Tốc |
| SOURCE / TYPE / CITY | App / Portal / Ho Chi Minh, Hanoi | |
| PICK_UP, INTERMEDIATE_DROPOFF, DROP_OFF | địa chỉ | chuỗi |
| DISTANCE | km, dấu phẩy thập phân | "7,4" |
| DAX_ID | mã tài xế | "9520847" |
| BASE_FARE, PROMO, TOLLS_AND_SURCHARGE, LATE_FEES, OTHER_FEES, AMOUNT | tiền, số nguyên không ngăn nghìn; PROMO âm | 39000, -3000, 0, 0, 5000, 41000 |
| CURRENCY | | "VND" |
| PAYMENT_METHOD / BILLING_TYPE | Corporate Billing / `Corp Bill Transaction` hoặc `Admin Fee` | |
| PRE_VAT_DELIVERY_FEE, VAT_VALUE_DELIVERY_FEE | phần cước vận chuyển trước VAT, VAT | 33333, 2667 |
| PRE_VAT_SERVICE_FEE, VAT_VALUE_SERVICE_FEE | phần phí dịch vụ (nền tảng), VAT | 4630, 370 |
| NON_VAT_VALUE | phần không chịu VAT | 0 |
| INVOICE_NUMBER | số HĐĐT RIÊNG cho từng chuyến | "1230732" |
| INVOICE_TRACKING_ID | mã tra cứu HĐ | 15 ký tự "26AAeann7r080mp" |
| INVOICE_PAYMENT_TYPE | | "Postpaid" |
| DRIVE_PLATE_NUMBER | biển số | "59X1-000.00" |
| GOODS_INFORMATION | loại hàng (express) | Khác, Thực phẩm, Dễ vỡ |
| ORDER_ID | mã đơn GrabExpress | `IN-2-00CMBS7Q3G...` (chỉ một số chuyến express) |
| VAT_INVOICE_DATE | ngày HĐ | `2026-06-02` (thường T+1) |
| VAT_INVOICE_SERIAL | ký hiệu HĐ | `1C26MGA` (transport), `1C26TAA` (express + Admin Fee) |
| VAT_TAX_AUTHORITY_CODE | mã CQT | 34 ký tự hex hoặc dạng `M1-25-XXXXX-00600000000` (23 ký tự) |

Phương trình (C, 177 dòng chuyến, 0 sai):
- `AMOUNT = BASE_FARE + PROMO + TOLLS_AND_SURCHARGE + LATE_FEES + OTHER_FEES`
- `AMOUNT = PRE_VAT_DELIVERY_FEE + VAT_VALUE_DELIVERY_FEE + PRE_VAT_SERVICE_FEE + VAT_VALUE_SERVICE_FEE + NON_VAT_VALUE`
- `DELIVERY (gồm VAT) = BASE_FARE + PROMO + LATE_FEES`; `SERVICE (gồm VAT) = OTHER_FEES + TOLLS_AND_SURCHARGE` (ca phí cầu đường 10.000 nằm trong service)
- VAT 8% trên cả hai phần (làm tròn từng phần).
- Dòng `Admin Fee`: không có BOOKING_ID, TRANSACTION_TIME = `YYYY-MM-<cuối tháng> 23:59:59 +07:00`, AMOUNT = 5% tổng AMOUNT các chuyến (2606: 197.600 = 5% x 3.952.000; 2512: 293.750 = 5% x 5.875.000). Có số HĐ riêng. 2606 tách 182.963 + 14.637 vào cột DELIVERY; 2512 để trống các cột VAT.
- Không có dòng tổng. Số phải trả tháng = tổng AMOUNT mọi dòng (chuyến + Admin Fee). Mẫu: 2606 82 dòng = 4.149.600; 2512 95 dòng = 6.168.750.

## Bố cục A/B (4 sheet)
- `tổng quan`: bảng 3 cột `Hạng Mục | Chuyến xe công nợ (VNĐ) | Chuyến xe dã được thanh toán trực tiếp bằng Tiền mặt/Chuyển khoản (VNĐ)`. Các dòng số kiểm soát: `(1) = (2) + (3)` số trên hóa đơn; `(2)` trước VAT; `(3)` VAT; `(4)` GrabTaxi không HĐ; `(5) = (1) + (4)`; `(6)` Phí Quản Lý; `(7)` Chiết khấu; [2412 có thêm `Chiết khấu Quý 3 (8)` và tổng thành `(9)`]; `Tổng cộng (8) = (5) + (6) - (7)`; `Phụ phí không có Hóa đơn`; `Tổng số tiền phải thanh toán cho Grab:`. Số dạng "2,106,000", "-" nghĩa là 0.
- `hóa đơn chi tiết`: dòng 3 là ghi chú, tiêu đề ở dòng 5, dữ liệu từ dòng 6. Tiêu đề (có xuống dòng):
  - A: `Mã Chuyến xe\n(Booking Code)`, `booking_code_for_business_grab_com`, `Tên nhóm\n(Group Name)`, `Mã nhân viên\n(Employee Id)`, `Dịch vụ\n(Vertical)`, `Tên công ty\n(Company Name)`, `Payment Type`, `Tiền trước VAT`, `Tiền VAT`, `Tổng thanh toán`, `Phụ phí không có Hóa đơn`, `Chuyến xe điều chỉnh`, `Số hóa đơn vận chuyển`, `Mã tra cứu`, `Hình thức thanh toán trên Hóa đơn vận chuyển` [+ 2412: `Số hóa đơn điều chỉnh`, `Mã tra cứu`, `Payment Type`].
  - B: thay `Tiền trước VAT`, `Tiền VAT` bằng `Tiền trước thuế 8%`, `Tổng tiền VAT 8%`, `Tiền trước thuế 10%`, `Tổng tiền VAT 10%`; 3 cột cuối `Số hóa đơn điều chỉnh`, `Mã tra cứu HĐĐC`, `Hình thức thanh toán HĐĐC`.
  - `Payment Type`: `Chuyến xe công nợ` (nợ Grab) hoặc `Chuyến xe đã được thanh toán trực tiếp bằng Tiền mặt/Chuyển khoản` (đã trả tài xế, vẫn có HĐ, không cộng vào số phải trả).
  - Phương trình: `Tổng thanh toán = tổng các cột trước VAT + VAT` (0 sai ở 2408, 2504; 2412 lệch 1 dòng có phụ phí không HĐ 9.000).
  - Dòng phí quản lý ở cuối hoặc giữa: cột A `Phí quản lý tháng MM/YYYY`, cột Vertical `ADMIN MM.YYYY`, VAT 10% (105.300 = 95.727 + 9.573 = 5% tổng chuyến).
  - Số HĐ: GỘP, một số HĐ cho cả tháng theo Payment Type (2408: 71 chuyến cùng `1752698`; 2504: 2 số cho chuyến công nợ, 1 số cho chuyến trả trực tiếp, 1 số cho phí quản lý).
- `hóa đơn điều chỉnh`: `Mã Chuyến xe (Booking Code) | booking_code_for_business_grab_com | Số hóa đơn cần điều chỉnh | Số hóa đơn điều chỉnh | remark` (trống trong mẫu).
- `diễn giải`: định nghĩa thuật ngữ, bỏ qua.

## Đơn vị, VAT, HĐĐT
- VND: cột CURRENCY (C), `(VNĐ)` trong tiêu đề tổng quan (A/B).
- C: số HĐ, ký hiệu, ngày, mã tra cứu, mã CQT có cho TỪNG chuyến. Khóa HĐ: `(VAT_INVOICE_SERIAL, INVOICE_NUMBER)`. Chuyến cuối tháng có thể mang ký hiệu năm sau (2512 có 1C26...).
- A/B: số HĐ + mã tra cứu gộp, không có ký hiệu và ngày HĐ.

## Khóa duy nhất
- C: `BOOKING_ID` duy nhất (82/82, 95/95). Dòng Admin Fee: khóa `grab-admin:<PORTAL_ID>:<YYYYMM>`.
- A/B: cột A `Mã Chuyến xe` duy nhất (374/374); cột B `booking_code_for_business` có thể lặp (353/374) với đơn express nhiều điểm (cột A dạng `IN-2-...`, `MS-2-...`, `SD-2-...`). Dùng cột A.

## Gắn chuyến với mục đích / người / đơn
- C: EMPLOYEE_NAME + EMPLOYEE_EMAIL_ADDRESS (tốt nhất để gắn người); VERTICAL express = giao hàng; ORDER_ID, GOODS_INFORMATION, DROP_OFF + COMPLETION_TIME để khớp đơn bán; TRIP_CODE / TRIP_DESCRIPTION có sẵn nhưng nhân viên chưa điền (nên yêu cầu điền mã đơn vào đây).
- A/B: chỉ có dịch vụ và mã chuyến; Group Name, Employee Id trống.

## Quirk
- DISTANCE dùng dấu phẩy thập phân, tiền thì số nguyên thuần; khác hẳn A/B dùng "1,234,000".
- C có 1 dòng không phải chuyến (Admin Fee) với phần lớn cột trống.
- COMPANY_NAME đổi giữa các tháng; dùng PORTAL_ID.
- Tên tệp lẫn có dấu / không dấu.

## Fixture C (CSV, đã ẩn danh, cắt bớt cột trống ở cuối dòng Admin)
```csv
TRANSACTION_TIME,CREATION_TIME,COMPLETION_TIME,COMPANY_NAME,PORTAL_ID,EMPLOYEE_NAME,EMPLOYEE_ID,EMPLOYEE_EMAIL_ADDRESS,GROUP_NAME,BOOKING_ID,VERTICAL,TAXI_TYPE,SOURCE,TYPE,TRIP_CODE,TRIP_DESCRIPTION,CITY,PICK_UP,INTERMEDIATE_DROPOFF,DROP_OFF,DISTANCE,DAX_ID,BASE_FARE,PROMO,TOLLS_AND_SURCHARGE,LATE_FEES,OTHER_FEES,AMOUNT,CURRENCY,PAYMENT_METHOD,BILLING_TYPE,PRE_VAT_DELIVERY_FEE,VAT_VALUE_DELIVERY_FEE,PRE_VAT_SERVICE_FEE,VAT_VALUE_SERVICE_FEE,NON_VAT_VALUE,INVOICE_NUMBER,INVOICE_TRACKING_ID,INVOICE_PAYMENT_TYPE,DRIVE_PLATE_NUMBER,GOODS_INFORMATION,ORDER_ID,VAT_INVOICE_DATE,VAT_INVOICE_SERIAL,VAT_TAX_AUTHORITY_CODE
2026-06-01 16:58:04 +07:00,2026-06-01 16:20:32 +07:00,2026-06-01 16:55:05 +07:00,CÔNG TY TNHH PATISSERIE VAGABOND,1000156989,STAFF_A,,staff_a@example.com,General,A-TESTEXPRESS0001,express,GrabExpress Nhanh,App,Portal,,,Ho Chi Minh,KITCHEN_ADDR,,CUSTOMER_ADDR,"7,4",1000001,39000,-3000,0,0,5000,41000,VND,Corporate Billing,Corp Bill Transaction,33333,2667,4630,370,0,1000001,26AAtest0000001,Postpaid,59X1-000.01,Thực phẩm,IN-2-TESTORDER0001,2026-06-02,1C26TAA,00AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
2025-12-04 14:27:48 +07:00,2025-12-04 13:59:13 +07:00,2025-12-04 14:25:58 +07:00,CÔNG TY TNHH PATISSERIE VAGABOND - GFB - Branch,1000156989,STAFF_B,,staff_b@example.com,General,A-TESTCAR00000002,transport,Car 6 chỗ ngồi,App,Portal,,,Ho Chi Minh,HOME_ADDR,KITCHEN_ADDR,AIRPORT_ADDR,"5,79",1000002,87000,-9000,10000,0,6000,94000,VND,Corporate Billing,Corp Bill Transaction,72222,5778,14815,1185,0,1000002,25GAtest0000002,Postpaid,50X-000.02,Khác,,2025-12-05,1C25MGA,M1-25-XXXXX-00601000002
2026-06-30 23:59:59 +07:00,,,CÔNG TY TNHH PATISSERIE VAGABOND,1000156989,,,,,,,,,,,,,,,,,,,,,,,6750,VND,,Admin Fee,6250,500,,,,1000003,26AAtest0000003,Postpaid,,,,2026-07-06,1C26TAA,00BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
```

=================== grabfood.md
# GrabFood - daily settlement PDF spec

Surveyed 2026-10-06 from Drive folder `02_Grabfood` (3 store subfolders). Files read in full:
`5-C4E1NPWGG2WZFA-20260710.pdf` (TCV, 58 orders, ads), `5-C4E1NPWGG2WZFA-20260717.pdf`
(TCV, cancellations + adjustments), `5-C4E1NPWGMGBGNX-20260710.pdf` (NVT, 1 cancel, 4 ad lines),
`5-C8BKA3MZMEW1CA-20260714.pdf` (NVHTN, narrow layout). ~15 more seen via search snippets.
Text below is Google Drive's extraction; pdfplumber/pypdf output will be close but VERIFY
line breaks on a real file before freezing regexes (see quirks).

## 1. Files

- Name: `5-<MERCHANT_ID>-<YYYYMMDD>.pdf`. `5-XXXXXXXXXXXXXX` is the Grab merchant ID:
  - `5-C4E1NPWGG2WZFA` = Trần Cao Vân, `5-C4E1NPWGMGBGNX` = Nguyễn Văn Trỗi,
    `5-C8BKA3MZMEW1CA` = Nhà Văn Hóa Thanh Niên.
- Period: one business day (2026-07-10 .. 2026-07-30 seen). 1 file per store per day. ~57-70 KB.
- Merchant ID is NOT printed inside the PDF. Inside, the store is identified only by the
  display name on line 3-5:
  - `The Vagabond Pâtisserie & Café - Trần Cao Vân`
  - `The Vagabond Delivery Kitchen` (this is the NVT store)
  - `The Vagabond Pâtisserie Brasserie - Nhà Văn Hóa Thanh Niên`
  Use filename merchant ID as primary key, name as cross-check.
- Title: `Báo cáo kinh doanh hàng ngày`. Report date line: `10 tháng 7 2026, thứ sáu`
  (D tháng M YYYY, weekday). Order rows carry only a time, so take the date from here.

## 2. Page layout, top to bottom

1. Header: title, date line, link `https://grb.to/hotrodoitacnhahang` (twice), store name and
   Grab support phone `+842871098466` (order of name/phone varies; TCV prints `\+84...` first).
2. `Tóm tắt thông tin` then one line:
   `Tổng thu nhập Còn thiếu Grab Tổng số đơn hàng VND 11.918.672 VND 0 58 đơn hàng`
   -> payout total, outstanding owed to Grab, order count (count INCLUDES cancelled rows).
3. `Thu nhập` + payout sentence `... chuyển cho bạn vào ngày<weekday>, tháng 7 11. ...`
   (note missing space after `ngày`; month/day order is `tháng M D`).
4. SUMMARY: a header line of labels, then ONE line of numbers. Columns are dynamic:
   `Trị giá đơn hàng | GTGT | Phí dịch vụ của quán | Khuyến mãi từ người bán |`
   `Tổng chiết khấu cho Grab | Tài trợ giảm giá phí giao hàng | [Điều chỉnh] | [Phí quảng cáo] |`
   `Tổng thu nhập | Còn thiếu Grab`
   - `Điều chỉnh` appears only if adjustments exist; `Phí quảng cáo` only if ads exist.
   - So the number line has 8, 9 or 10 tokens. Detect optional columns by searching the
     label line for `Điều chỉnh` and `quảng` (labels wrap in narrow layout, see quirks).
5. `Đơn hàng từ ứng dụng và web` + column header line:
   `Thời gian giao hàng Mã đơn hàng Phương thức thanh toán Trị giá đơn hàng GTGT Phí dịch vụ của quán Khuyến mãi từ người bán Tổng chiết khấu cho Grab Tài trợ giảm giá phí giao hàng Thu nhập`
6. Sub-section `Đơn hàng Delivery`, then order lines (newest first).
7. Orders total: a number line followed by `Tổng cộng` (value BEFORE label in extraction).
8. Optional `Marketing` section: header `Thời gian giao hàng Mã giao dịch Mô tả Phí quảng cáo Thuế Tổng cộng`, then ad lines.
9. Optional `Điều chỉnh` section: header `Thời gian giao hàng Mã giao dịch Mã đơn hàng Mô tả Tổng cộng`, then adjustment lines.
10. `Hướng dẫn đọc hiểu báo cáo` glossary to end of document. STOP parsing here. It also
    repeats section totals out of place (`VND 12.264.272`, `VND-345.600`, `VND144.976`).

Glossary names other possible sections NOT seen in samples: `Đơn hàng ăn tại quán`,
`Phí giao hàng` (Shop Online), `Khoản bồi hoàn`, `Số tiền đã hoàn lại`. Parser must fail
loudly on any unknown section/sub-section header before the glossary.

## 3. Line patterns

Money: `-?\d{1,3}(\.\d{3})*` with `.` as THOUSANDS separator, or `-` = n/a. Integer VND.

Order line (7 money columns):
```
<time> <code> <payment> <gross> <vat> <svc> <promo> <commission> <ship_subsidy> <income>
9:43 PM GF-680 Trả thẻ / Ví 320.000 0 - 0 -44.897 -15.000 260.103
5:50 PM GF-691 Tiền mặt 700.000 0 - 0 -99.510 -24.000 576.490
6:41 PM GD- 76XITFBB Trả thẻ / Ví 350.000 0 - -60.000 -42.689 0 247.311
```
Cancelled line (payment + 7 money columns all `-`):
```
Đã hủy GF-986F - - - - - - - -
```
Suggested regex:
```
^(?P<time>\d{1,2}:\d{2} [AP]M|Đã hủy)\s+(?P<code>G[A-Z]-\s?[A-Z0-9]+)\s+
(?P<pay>Trả thẻ / Ví|Tiền mặt|-)\s+(?P<rest>(?:-?[\d.]+|-)(?:\s+(?:-?[\d.]+|-)){6})$
```
Ad line (`Marketing`):
```
10 Th07, 12:31 PM ADS-748 Quảng cáo GrabFood Tiêu Chuẩn \#347JNDFG - 2026-07-09 -320.000 -25.600 -345.600
```
-> `<D Th MM, h:mm AM/PM> ADS-<n> <description> <fee> <tax> <total>`; take the LAST 3 numbers,
description is everything between ID and them (it contains ` - YYYY-MM-DD` = campaign day,
usually the previous day). Tax = 8% of fee. Small co-fund lines exist (`-700 -56 -756`).
Adjustment line (`Điều chỉnh`):
```
17 Th07, 4:54 PM MPA-677 GF-201 Canceled Order Compensation 72.488
```
-> `<datetime> MPA-<n> <order code> <description> <amount>`; positive = paid to merchant,
links back to a cancelled order code in the same file.

## 4. Columns (order line)

| Field | Meaning | Notes |
|---|---|---|
| Thời gian giao hàng | delivery time `h:mm AM/PM` | or `Đã hủy` for cancelled |
| Mã đơn hàng | short booking code | `GF-NNN`, `GF-NNNF`, `GD-XXXXXXXX` (see IDs) |
| Phương thức thanh toán | `Trả thẻ / Ví` (card/wallet) or `Tiền mặt` (cash) | |
| Trị giá đơn hàng | gross menu value incl. VAT | positive |
| GTGT | VAT passed to merchant | 0 in all samples |
| Phí dịch vụ của quán | restaurant service fee | always `-` in samples |
| Khuyến mãi từ người bán | merchant-funded promo | negative or 0, may be odd (`-227.200`) |
| Tổng chiết khấu cho Grab | Grab commission | negative |
| Tài trợ giảm giá phí giao hàng | merchant-funded delivery discount | negative or 0 |
| Thu nhập | net per order | sum of the previous 6 money columns |

## 5. Unit and equations

- Unit: whole VND; `.` is a thousands separator (`320.000` = 320,000 VND). Evidence: glossary
  says `Tất cả các trị giá tiền đều được tính bằng VND`; orders 45k..995k.
  `72.488` (adjustment) also means 72,488 VND, not 72.488.
- Per order: `income = gross + vat + promo + commission + ship_subsidy` (negatives signed).
  Exact on every row checked (e.g. 320000 - 44897 - 15000 = 260103).
- Commission ~= 14.72% x (gross - |promo| - |ship_subsidy|), all 3 stores, +/- 2 VND
  (e.g. (490000-115000-30000) x 0.1472 = 50784 -> printed 50.785; 340000 x 0.1472 = 50048 ->
  printed 50.050). Never recompute it; take the printed value.
- Orders total line = sum(income). Summary:
  `Tổng thu nhập = gross + vat + svc + promo + commission + ship + adjustments + ads`.
  Verified: 17.345.000 - 2.499.750 - 2.116.978 - 464.000 - 345.600 = 11.918.672 (TCV 07-10);
  12.360.000 - 848.000 - 1.645.747 - 332.000 + 144.976 - 394.740 = 9.284.489 (TCV 07-17);
  1.246.531 - 51.732 = 1.194.799 (NVT 07-10, ads = 49.140+1.080+756+756).
- Summary promo/commission/ship = column sums of order lines; ads = sum of Marketing totals
  (fee + tax); adjustments = sum of Điều chỉnh lines.
- Cash orders are included in income totals. Whether the bank transfer nets out cash
  collected by drivers is NOT shown in the file: confirm against bank data.

## 6. Cancellations / refunds / ads

- Cancelled orders: line `Đã hủy <code> - - - - - - - -`, contribute 0, but are counted in
  `Tổng số đơn hàng`. Compensation (if any) arrives as a separate `Điều chỉnh` line
  `Canceled Order Compensation` referencing the same code (positive).
- Ads: own `Marketing` section, fee + 8% VAT, deducted from payout, NOT tied to orders.
- `Còn thiếu Grab` (amount owed to Grab) was 0 everywhere; parse it anyway.

## 7. IDs and uniqueness

- Order code is a SHORT display code: `GF-` + 3 digits, sometimes with `F` suffix
  (`GF-138F`), or `GD-` + 8 alnum. NOT globally unique: `GF-897` and `GF-916` both occur on
  2026-07-10 at TCV and NVT; `GF-820` occurs at TCV on 07-10 and 07-17.
- Dedup key: `(merchant_id, report_date, code, time, gross)`; within one file no duplicate
  code was seen. Flag (do not drop) any duplicate within a file.
- Ad ID `ADS-<n>` and adjustment ID `MPA-<n>` are 3-digit display IDs too; key them with
  merchant_id + report_date.

## 8. Quirks (text extraction)

1. Space inside codes: `GD- 76XITFBB`, `GF- 816F`, `GF- 086F`. Normalize by removing
   whitespace after the hyphen. Codes may be truncated in the PDF (likely source of `F`).
2. Narrow layout (NVT, NVHTN) wraps header labels and interleaves them:
   `Khuyến mãi từ người Tổng chiết khấu cho Tài trợ giảm giá phí giao Phí quảng bán Grab hàng cáo Tổng thu Còn thiếu nhập Grab`.
   Do not split labels by text; use keyword presence + token count.
3. Store name and phone order differs; phone may be escaped `\+84...` in Drive text.
4. Total value printed BEFORE `Tổng cộng`.
5. Glossary at the end repeats totals; stop at `Hướng dẫn đọc hiểu báo cáo`.
6. Long reports may span pages; page breaks can fall inside the order list.
7. Weekday/payout sentence lacks spaces (`vào ngàythứ bảy`).

## 9. Fixture (plain-text excerpt mimicking extracted PDF, anonymized codes)

```
Báo cáo kinh doanh hàng ngày
17 tháng 7 2026, thứ sáu https://grb.to/hotrodoitacnhahang
https://grb.to/hotrodoitacnhahang
\+842871098466 The Vagabond Pâtisserie & Café - Trần Cao Vân
Tóm tắt thông tin
Tổng thu nhập Còn thiếu Grab Tổng số đơn hàng VND 668.915 VND 0 4 đơn hàng
Thu nhập
Tổng tiền thanh toán sẽ được chuyển cho bạn vào ngàythứ bảy, tháng 7 18. Tài khoản của bạn có thể phải đợi vài ngày trước khi ghi nhận số tiền này.
Trị giá đơn hàng GTGT Phí dịch vụ của quán Khuyến mãi từ người bán Tổng chiết khấu cho Grab Tài trợ giảm giá phí giao hàng Điều chỉnh Phí quảng cáo Tổng thu nhập Còn thiếu Grab
830.000 0 0 -60.000 -111.433 -13.000 72.488 -49.140 668.915 0
Đơn hàng từ ứng dụng và web
Thời gian giao hàng Mã đơn hàng Phương thức thanh toán Trị giá đơn hàng GTGT Phí dịch vụ của quán Khuyến mãi từ người bán Tổng chiết khấu cho Grab Tài trợ giảm giá phí giao hàng Thu nhập
Đơn hàng Delivery
9:28 PM GF-101 Trả thẻ / Ví 260.000 0 - 0 -36.359 -13.000 210.641
Đã hủy GF-102 - - - - - - - -
5:14 PM GD- AAAA1111 Trả thẻ / Ví 400.000 0 - -60.000 -50.050 0 289.950
12:42 PM GF- 103F Tiền mặt 170.000 0 - 0 -25.024 0 144.976
645.567
Tổng cộng
Marketing
Thời gian giao hàng Mã giao dịch Mô tả Phí quảng cáo Thuế Tổng cộng
17 Th07, 10:30 PM ADS-001 Từ khóa thủ công - 2026-07-17 -45.500 -3.640 -49.140
Điều chỉnh
Thời gian giao hàng Mã giao dịch Mã đơn hàng Mô tả Tổng cộng
17 Th07, 6:16 PM MPA-001 GF-102 Canceled Order Compensation 72.488
Hướng dẫn đọc hiểu báo cáo
Tất cả các trị giá tiền đều được tính bằng VND. Để tiện cho việc tính toán, tổng trị giá trong báo cáo này có thể được làm tròn khi cần thiết.
```
Fixture control checks: order incomes sum 645.567 = 830.000 - 60.000 - 111.433 - 13.000;
payout 668.915 = 645.567 + 72.488 - 49.140; count 4 includes the cancelled GF-102.

=================== greensm_ngon.md
# Xanh SM Ngon (GreenSM Ngon) - settlement report spec

Surveyed 2026-10-06 from Drive folder `01_GreenSM Ngon` (TCV + NVT subfolders).
Files read in full: `..._20260124`, `..._20260205`, `..._20260327` (TCV store),
`Revenue_Report_01K23YRC3K35J07ZYBVADZZSYK_20260315` (NVT store, misfiled in TCV folder).
Ignore `Hợp Đồng Merchant ...pdf` and `Thỏa thuận cấp quyền ...pdf` in the vendor root.

## 1. Files

- Name: `Revenue_Report_<STORE_ID>_<YYYYMMDD>` (no extension in Drive, Google Sheet).
  - `STORE_ID` = 26-char ULID (Crockford base32), same value as column `ID cửa hàng`.
  - Seen: `01K23YRC2F21BG1DP3P8T4KV7Q` = Trần Cao Vân, `01K23YRC3K35J07ZYBVADZZSYK` = Nguyễn Văn Trỗi.
  - `YYYYMMDD` = business day. Range seen: 2026-01-06 .. 2026-04-10. One file per store per day
    (days with no orders have no file).
- Period: one calendar day (all rows share that date in column F).
- Raw format: native Google Sheet (mimeType `application/vnd.google-apps.spreadsheet`),
  originally an xlsx with 2 sheets. Export as xlsx to get both sheets; `text/csv` export
  returns ONLY the first sheet (`Detail Transactions`).
- Store identity INSIDE file: columns D `ID cửa hàng` (ULID) and E `Tên cửa hàng`
  (`The Vagabond Patisserie & Café - Trần Cao Vân` / `... - Nguyễn Văn Trỗi`).
  Route by column D, never by folder: a NVT file sits in the TCV folder.

## 2. Sheet `Detail Transactions`

No preamble. Row 1 = header, rows 2.. = one row per order. No total row.
Exact header order (A..S, 19 columns):

```
STT | Mã Đơn Hàng | Mã Rút Gọn | ID cửa hàng | Tên cửa hàng | Thời gian hoàn thành/ huỷ đơn |
Trạng thái | Giá trị đơn hàng | Khuyến mại từ quán | Giảm giá món | Tổng tiền cofund KM |
Tổng tiền cofund KM Giao hàng | Tổng tiền cofund KM Món ăn | Voucher Cofunds |
Doanh thu ròng | Chiết khấu | VAT | PIT | Thực thu
```
Note the literal `hoàn thành/ huỷ đơn` (space after slash, `huỷ` with old-style accent).

| Col | Header | Meaning | Type / format | Example (anonymized) |
|---|---|---|---|---|
| A | STT | row number 1..n | int | 1 |
| B | Mã Đơn Hàng | platform order ID | 26-char ULID string | 01KFAAAAAAAAAAAAAAAAAAAAA1 |
| C | Mã Rút Gọn | short display code | 4-digit TEXT, keep leading zeros | 0010 |
| D | ID cửa hàng | store ID | ULID string | 01K23YRC2F21BG1DP3P8T4KV7Q |
| E | Tên cửa hàng | store name | string | The Vagabond Patisserie & Café - Trần Cao Vân |
| F | Thời gian hoàn thành/ huỷ đơn | completion (or cancel) time | `DD-MM-YYYY HH:MM:SS`, local time (ICT) | 24-01-2026 21:35:58 |
| G | Trạng thái | status | string; only `Completed` observed | Completed |
| H | Giá trị đơn hàng | gross menu value | int VND | 115000 |
| I | Khuyến mại từ quán | merchant promo (per row) | always BLANK in samples | |
| J | Giảm giá món | item discount set by merchant | int VND | 40000 |
| K | Tổng tiền cofund KM | total cofunded voucher = L + M | int VND | 16000 |
| L | Tổng tiền cofund KM Giao hàng | voucher part on delivery fee | int VND | 4000 |
| M | Tổng tiền cofund KM Món ăn | voucher part on food (charged to merchant) | int VND | 12000 |
| N | Voucher Cofunds | voucher breakdown `CODE:amount`, several separated by LF inside the cell | string, may be blank | `2026XANH20:12000\n2026XANHSHIP8:4000` |
| O | Doanh thu ròng | net revenue = H - J - M | int VND | 63000 |
| P | Chiết khấu | platform commission = 13% x O | int VND | 8190 |
| Q | VAT | VAT withheld | int, 0 in all samples | 0 |
| R | PIT | PIT withheld | int, 0 in all samples | 0 |
| S | Thực thu | payout for the order = O - P - Q - R | int VND | 50810 |

Raw cell values (csv export): plain integers, no thousand separators, CRLF line ends,
the multi-line voucher cell is quoted and contains a bare LF.

## 3. Sheet `Summary`

No header row; 2 columns (label, value), range A1:B9:

| Row | Label (A) | Value (B) = control total |
|---|---|---|
| 1 | Tổng số đơn hàng | count of detail rows |
| 2 | Tổng giá trị đơn hàng | sum H |
| 3 | Khuyến mại từ quán | sum M (NOT sum I, NOT sum K) |
| 4 | Khuyến mại món | sum J |
| 5 | Doanh thu ròng | sum O |
| 6 | Tổng chiết khấu | sum P |
| 7 | Tổng thực thu | sum S |
| 8 | PIT | blank |
| 9 | (blank) | blank |

Match labels by text, not row number. Verified on 3 files:
20260124: 3 / 515000 / 12000 / 107000 / 396000 / 51480 / 340520.
20260205: 5 / 735000 / 78000 / 275000 / 382000 / 49660 / 320340.
20260327: 6 / 1175000 / 138000 / 175000 / 862000 / 112060 / 749940.

## 4. Unit and equation

- Unit: whole VND, integer. Evidence: order values 70000..285000 (typical bakery basket),
  commission exactly 13% of net on every row (22100 = 13% of 170000; 8190 = 13% of 63000;
  15600 = 13% of 120000).
- Per order: `O = H - J - M` and `S = O - P - Q - R`, `P = 0.13 * O`. Holds exactly on
  all 15 rows checked.
- Per file: `Tổng giá trị - Khuyến mại món - Khuyến mại từ quán = Doanh thu ròng` and
  `Doanh thu ròng - Tổng chiết khấu = Tổng thực thu`. Holds exactly.
- Cofund: K is a TOTAL of L + M. Never add K to L or M. Only M (food part) reduces merchant
  revenue; L (delivery part) does not appear in O. N is an informational breakdown of K.
- Column I is blank per row, yet Summary row 3 with the same label carries sum(M).
  Treat Summary "Khuyến mại từ quán" as merchant-borne voucher cost = sum(M).

## 5. Cancellations / refunds / ads

- Header F says "hoàn thành/ huỷ" and G is a status, so cancelled rows are possible,
  but every sampled row is `Completed` and a Drive full-text search for
  `Cancelled|Canceled|Cancel|Refunded` in these files returned nothing.
  Parser: accept only `Completed` into revenue; log and fail-soft on any other status.
- No ads, adjustments or refund lines exist in this report.

## 6. IDs and uniqueness

- `Mã Đơn Hàng` (ULID) is the stable unique key; ULID prefix encodes creation time.
- `Mã Rút Gọn` is a 4-digit display code; reused across days, NOT unique.
- Dedup key: `("GREENSM", Mã Đơn Hàng)`.

## 7. Quirks

1. File for NVT store found in the TCV folder; use column D / filename ULID.
2. CSV export drops `Summary`; download as xlsx or read both sheets via API.
3. `Mã Rút Gọn` must be read as text (`0010`).
4. Voucher cell is multi-line; Drive's text view shows it space-joined.
5. `Khuyến mại từ quán` meaning differs between detail (blank) and Summary (sum M).
6. Commission 13% seen Jan..Apr 2026; read it from data, do not hard-code.
7. Store name uses `Patisserie` without accent here (Grab/Shopee use `Pâtisserie`).

## 8. Fixture (anonymized, Detail Transactions as CSV)

```csv
STT,Mã Đơn Hàng,Mã Rút Gọn,ID cửa hàng,Tên cửa hàng,Thời gian hoàn thành/ huỷ đơn,Trạng thái,Giá trị đơn hàng,Khuyến mại từ quán,Giảm giá món,Tổng tiền cofund KM,Tổng tiền cofund KM Giao hàng,Tổng tiền cofund KM Món ăn,Voucher Cofunds,Doanh thu ròng,Chiết khấu,VAT,PIT,Thực thu
1,01KFAAAAAAAAAAAAAAAAAAAAA1,7001,01K23YRC2F21BG1DP3P8T4KV7Q,The Vagabond Patisserie & Café - Trần Cao Vân,24-01-2026 16:23:45,Completed,170000,,0,0,0,0,,170000,22100,0,0,147900
2,01KFAAAAAAAAAAAAAAAAAAAAA2,0010,01K23YRC2F21BG1DP3P8T4KV7Q,The Vagabond Patisserie & Café - Trần Cao Vân,24-01-2026 21:35:58,Completed,115000,,40000,16000,4000,12000,"2026XANH20:12000
2026XANHSHIP8:4000",63000,8190,0,0,50810
3,01KFAAAAAAAAAAAAAAAAAAAAA3,1834,01K23YRC2F21BG1DP3P8T4KV7Q,The Vagabond Patisserie & Café - Trần Cao Vân,24-01-2026 21:40:08,Completed,230000,,67000,0,0,0,,163000,21190,0,0,141810
```

Summary sheet for the same fixture (label,value):

```csv
Tổng số đơn hàng,3
Tổng giá trị đơn hàng,515000
Khuyến mại từ quán,12000
Khuyến mại món,107000
Doanh thu ròng,396000
Tổng chiết khấu,51480
Tổng thực thu,340520
PIT,
,
```

=================== onepay.md
# OnePay - settlement report schema (for adapter)

Source: Drive folder `03_OnePay` (1A_wktKInOtr1Go7cgxJ6UUQTRqJRoRag), surveyed 06/10/2026. Read only.
Contract 212626/HCM/ECOM, Merchant ID `VAGABOND`, payout to MB (MILITARYBANK) account in header.
Channels: `QT` (international card via payment link) and `VIETQR` (bank QR). One report per channel, never mixed.

## 0. What is in the folder
- 24 daily notices, each alone in a subfolder `<YYYYMMDD>_<Entry>thongbaotamung/` (2 more sit at root): 20260604 to 20260731.
- Monthly: `BB_CHI TIET GD_...` (detail) and `BBDS_...` (summary) for QT 06/2026 and VIETQR 05/2026, plus BBDS PDFs.
- ALL spreadsheets are Google Sheets (converted). No original .xlsx/.xls is kept. PDFs are originals.
- CSV export (`text/csv`) gives DISPLAYED strings in vi-VN locale and only the FIRST tab.
  The daily notice has 2 tabs: `Indebtedness` (detail, first) and `Summary` (second, not in CSV export).
  The production adapter will most likely get OnePay's original .xlsx from email: read cells as numbers
  when possible; treat the string forms below as the fallback.
- Every sheet: column A is empty (CSV rows start with `,`), except BBDS which uses column A.

## 1. Number, date, unit conventions (all report types)
- Unit = whole VND (dong), NOT thousands. Evidence:
  - 300.000 x 2,40% + 4.000 = 11.200 = Total fee; 300.000 - 11.200 = 288.800 = Advance amount (daily 30/07).
  - Amount in words: "Hai Trăm Tám Mươi Tám Nghìn, Tám Trăm Đồng" = 288.800 dong.
  - All 23 rows of QT June satisfy fee = fix + amount x pct exactly; sums = BBDS totals to the dong.
- Sheet strings: thousands `.`, decimal `,`: `"1.180.000,00"`, `1.180.000`, `"2,40%"`, `"1,00"`.
  Same column may show with or without `,00`. Parse: strip spaces and `VND `, drop `.`, `,`->`.`.
- PDF (BBDS) uses the OTHER locale: `715,000` (comma thousands). Do not reuse the sheet parser on PDF text.
- Percent fee is a rate string `"3,60%"` -> 0.036. Fix fee is VND per transaction (seen 4.000 QT, 1.760 VietQR).
- Total fee is rounded to whole dong (715.000 x 0,33% + 1.760 = 4.119,5 -> 4.120). Recompute with tolerance 1.
- Fees INCLUDE 10% VAT ("Phí trên đã bao gồm VAT 10%"). VAT = round(total_fee / 11) (11.200 -> 1.018; 29.740 -> 2.704; 4.182 -> 380).
- FEE RULE, do not double count: `Total fee = Fix fee + Amount x Percent fee`. Fix fee is a COMPONENT of
  Total fee. Book Total fee only. Never add Fix fee + Total fee.
- Net: `Advance amount = Amount - Total fee` (QT), `Total amount after charge fee = Amount - Total fee` (VietQR).
- Dates `dd/mm/yyyy HH:MM:SS` (daily) or `dd/mm/yyyy HH:MM` (monthly QT, no seconds). Local time (UTC+7).
- Refunds: no refund row in any sample. Notice footer says "Giao dịch hoàn tiền mang giá trị âm
  (Refund transaction value is negative)": expect Transaction Type != PURCHASE and negative amount/advance.
  BBDS has columns "amount held for refund" / "release amount" (all 0 in samples). Handle sign, do not abs().

## 2. Cut-off windows (critical)
- QT: cycle 17:00:00 day D to 16:59:59 next cycle day. A cycle can span several days before a payout
  (e.g. 17:00 11/06 to 16:59 13/06, paid Mon 15/06). Monthly QT window = 17:00:00 last day of prev month
  to 16:59:59 last day of month, although the filename says 01.06.2026_30.06.2026.
- VIETQR: calendar days 00:00 to 23:59 (weekend batched: 00:00 10/07 to 23:59 12/07). Monthly = calendar month.
- Payout T+1 business day. Filename date of a daily notice = payout date; Summary "Create Date" can be earlier
  (file 20260608 has Create Date 07/06/2026).

## 3. Daily notice - QT ("THÔNG BÁO TẠM ỨNG / ADVANCE PAYMENT NOTICE")
File `<YYYYMMDD>_<Entry>VAGABOND`, e.g. `20260730_5321728VAGABOND`; Entry (7 digits) = "Bút toán/Entry".
Tab `Indebtedness`, 20 cols (A..T). Preamble rows 1-13:
- r2-4 OnePay name/address; r6 `THÔNG BÁO TẠM ỨNG`; r7 `ADVANCE PAYMENT NOTICE`
- r8 `ĐVCNT (Company):` value in col F; r9 `Hợp đồng số (Contract No):` F, `ký ngày (signed): dd/mm/yyyy` in I
- r10 account no (F), r11 bank name (F)
- r12 `Thời gian giao dịch thẻ quốc tế (International Card Transaction date): ` F=`Từ ngày (from): 17:00 28/07/2026`, I=`Đến ngày (to): 16:59 29/07/2026`
Header = 3 rows: r14 Vietnamese (cell Q contains a newline: `"Phí XLGD\n(VND)"`), r15 formula row
`(1),,(2),(3)=(1)*(2),(4),(5),(6)=(4)+(3)*(5),(7)=(3)-(6)`, r16 English. Detect header by EN row containing `Transaction ID`.
EN header (B..T), trim + case-fold (it has padded names like ` Transaction Amount `):

| col | EN header | VN | type / example | meaning |
|---|---|---|---|---|
| B | No | STT | int `1` | row no |
| C | Merchant ID | Merchant Id | `VAGABOND` | |
| D | Transaction ID | Mã giao dịch | 9 digit int `246000001` | OnePay txn id, KEY |
| E | Order Reference | Mã đơn hàng | `PL_VAGABOND_260729042259` | payment-link order; time part is 12h clock |
| F | Merchant Trans. Ref. | Mã thanh toán | `PL_VAGABOND_xxxxxxxxxx` (10 char) | merchant ref, KEY for matching our order |
| G | Transaction date | Thời gian giao dịch | `29/07/2026 16:23:53` | |
| H | Transaction Type | Loại giao dịch | `PURCHASE` | refund expected otherwise |
| I | Card Type | Loại thẻ | VISA, MASTERCARD, AMEX, CUP | |
| J | Status | Trạng thái giao dịch | `SUCCESS` | |
| K | Bin Country | Bin Country | `VN`/`AU` (Jul) or `VIET NAM` (Jun) | drives rate |
| L | Pay Channel | Loại dịch vụ | `QT` | |
| M | Transaction Amount (1) | Giá trị GD | `"300.000,00"` | original currency |
| N | Currency | Loại tiền tệ | `VND` | |
| O | Exchange Rate (2) | Tỷ giá | `"1,00"` | |
| P | Successful Amount (VND) (3) | Giá trị GD thành công (VND) | `300.000` | gross VND |
| Q | Fix fee (4) | Phí XLGD (VND) | `"4.000,00"` | per-txn fixed fee, part of S |
| R | Percent fee (5) | Phí TTT | `"2,40%"` | rate |
| S | Total fee (6)=(4)+(3)*(5) | Tổng phí | `"11.200,00"` | the ONLY fee to book |
| T | Advance amount (7)=(3)-(6) | Số tiền tạm ứng | `288.800` | net per txn |

Observed rates: VN cards 2,40%; foreign Visa/MC/CUP 3,60%; AMEX VN 3,00%, AMEX foreign 3,10%; fix 4.000.
Footer (control totals): row after data, label `Tổng cộng (Total)` in col D (not B), totals in P, S, T.
Then label/value rows (label col B, value col F): `Tổng số lượng GD thành công ...` count;
`Tổng giá trị GD thành công ...` gross; `Tổng số lượng GD không thành công ...` failed count;
`Tổng phí (Total fees):`; `Giá trị tạm ứng bằng số (Total of Advance Amount): ` value `VND 288.800`;
amount in words; refund note; "see Summary"; place/date `Hà Nội, Ngày 30 tháng 7 năm 2026`.
Tab `Summary` (A..N): Company, Contract, Merchant IDs; `Loại dịch vụ/ Pay channel:` QT; `Bút toán/ Entry:` 5321728;
`Ngày tạo/ Create Date:` dd/mm/yyyy; `Kỳ bút toán` `T+1`; account, bank; `TW tổng cuối/ Final total amount:` 288.800
(= bank credit); `Nội dung chuyển tiền/ Transfer content: PVS1365757 OnePay tam ung VAGABOND QT 17h 28 07 26 den 17...`
(this string, esp. `PVS#######`, is what appears on the MB bank statement -> match key bank line <-> notice).
Then a table: header `A | QUỐC TẾ International Card | Mã số Code | Number of Trans | Transaction Amount (USD) |
Transaction Amount (VND) | Merchant Discount | Partner Discount | Total transaction Amount (VND) |
Total fee (Included VAT) | VAT amount | Total amount after charge fee | Advance amount`, rows `A=A1` and
`A1 Quốc tế trong kỳ (Từ 17:00:00 28/07/2026 đến 16:59:59 29/07/2026)`. Control: Advance amount here = detail total T.

## 4. Daily notice - VIETQR (same file name pattern, e.g. `20260713_5257571VAGABOND`)
Detect channel by preamble r12 text `Thời gian giao dịch VietQR (VietQR Transaction date):` (values in G and N:
`Từ ngày (from): 00:00 10/07/2026`, `Đến ngày (to): 23:59 12/07/2026`) or Summary Pay channel `VIETQR`.
Labels in col B, values in col G (one column further right than QT). r13 col T `ĐVT/Currency: VNĐ`.
Header: r14 VN, r15 EN, r16 formula `(1),(2),(3),(4)=(2)+(1)*(3),(5)=(1)-(4)` (EN before formula, unlike QT).
EN columns B..T: No, Merchant ID, Transaction ID (`PAY-` + 22 char, e.g. `PAY-xxxxxxxxxxxxxxxxxxxxxx`), Order Reference,
Merchant Trans. Ref., Virtual Account (19 digit VA), Virtual Account Name (`VAGABOND`), Bank Trans Ref (`INV...` 25 char),
Transaction date (`12/07/2026 13:08:31`), Bank ID (`MSB`), Remark (payer bank transfer text: CONTAINS PAYER ACCOUNT
NO + NAME = personal data, do not store, mask), Transaction Type (`PURCHASE`), Pay Channel (`VietQR`, mixed case),
Transaction Amount (1) `"734.000,00"`, Fix fee (2) `"1.760,00"`, Percent fee (3) `"0,33%"`, Total fee (4) `"4.182,00"`,
Total amount after charge fee (5) `729.818`, Advance amount `729.818`.
Footer: `Tổng cộng (Total)` in col D, totals in O (amount), R, S, T. Then only `Giá trị tạm ứng bằng số` (`VND 729.818`),
in words, "see Summary" (no count/failed/fee lines, no refund note). Summary tab same as QT with `N`/`N1` instead of
`A`/`A1` and `VietQR trong kỳ (Từ 00:00:00 ... đến 23:59:59 ...)`; transfer content `PVS... OnePay tam ung VAGABOND VIETQR 0h 10 07 26 den 23h5...`.

## 5. Monthly detail QT - `BB_CHI TIET GD_VAGABOND_<dd.mm.yyyy>_<dd.mm.yyyy>_QT_<epoch ms>`
Epoch suffix = generation time (1783164031227 = 04/07/2026). 21 cols A..U. r2-4 OnePay header; r6 `DANH SÁCH CHI TIẾT GIAO DỊCH`; r7 blank.
Header: r8 VN (last col `Payment Date`), r9 formula, r10 EN. Same 19 columns as daily QT (B..T) with these differences:
`Transaction Date` capitalised, `Fix Fee`/`Percent Fee`/`Total Fee`/`Advance Amount`; date has NO seconds
(`02/06/2026 17:33`); Bin Country full name (`VIET NAM`, `JAPAN`); extra col U `Payment Date` (EN header cell empty,
VN cell `Payment Date`) = payout date `dd/mm/yyyy` = filename date of the daily notice that paid it.
Footer: `Tổng cuối` in col B; totals in P (`"22.780.000,00"`), S (`"813.103,00"`), T (`"21.966.897,00"`). No count row.

## 6. Monthly detail VIETQR - `BB_CHI TIET GD_VAGABOND_01.05.2026_31.05.2026_VIETQR_<epoch ms>`
22 cols A..V. r6 title; r7 col V `ĐVT/Currency: VNĐ`; r8 VN; r9 EN; r10 formula `(1),(2),(3),(4)=(1)*(2)+(3),(5)=(1)-(4)`.
EN: No, Merchant Id, Transaction ID (`PAY-...`), Merchant Trans. Ref., Virtual Account, Virtual Account Name,
Bank Trans Ref, Transaction Date, Bank ID (EMPTY in sample), Remark (PII), Transaction Type, Pay Channel (`VIETQR`),
Transaction Amount (1), Percent Fee (2), Fix Fee (3) [order swapped vs daily], Total Fee (4), Total amount after charge fee (5),
Total Advance Amount, Total fee collected, Total fee receivable, Advance Date (`13/05/2026`).
No `Order Reference` column (daily has it). `Total fee collected` = fee netted at payout; `Total fee receivable` = 0 in
sample (if >0, OnePay will bill it separately; then Advance != Amount - Total fee).
Footer `Tổng cuối (Total)` in col B; totals from Total Fee onward (Transaction Amount NOT totalled).

## 7. Monthly BBDS summary - `BBDS_VAGABOND_<dd.mm.yyyy>_<dd.mm.yyyy>_<QT|VIETQR>_<epoch ms>` (+ `.pdf`, signed copy, different epoch)
"BIÊN BẢN XÁC NHẬN ĐỐI SOÁT SỐ LIỆU DỊCH VỤ / MONTHLY FEE REPORT" = the monthly fee confirmation (basis for OnePay's fee VAT invoice).
11 cols A..K, col A used. r9 `CÔNG TY TNHH PATISSERIE VAGABOND - QT - VAGABOND` (company - channel - merchant);
r10/r11 contract sentence VN/EN; r13 QT only: `Quốc tế/International Card: From 17:00:00 31/05/2026 To 16:59:59 30/06/2026`
(empty for VIETQR); r14 col K `ĐVT/Currency: VNĐ`. Header = ONE row, each cell `"VN\nEN"`:
No | Transaction date | Pay channel | Number of Trans | Count success | Count failed | Transaction Amount |
The amount held for refund transactions | Release amount | Advance amount | Total fee.
Data row = one payout cycle: `1,02/06/26 - 03/06/26,QT,2,2,0,1.450.000,0,0,1.397.720,52.280`
("Transaction date" = cycle start - end date `dd/mm/yy`, VietQR `12/05/26 - 12/05/26`).
Total row `TỔNG CỘNG/Total` in col A; then `Phí Dịch Vụ (Total fee):` value col D, words, VAT note, date
`Hà Nội, Ngày 04 tháng 07 năm 2026`, signature block. Row check: Amount - held + release - fee = Advance.

## 8. How the reports relate (control totals)
- Bank credit (MB statement) == daily notice Summary `Final total amount` == Indebtedness total `Advance amount`.
  Match via transfer content `PVS#######` / entry no / payout date.
- Each BBDS row == one daily notice (same cycle, count, gross, fee, advance). June QT: 14 BBDS rows == 14 notices
  20260604..20260701 (cycle 29/06-30/06 paid 01/07). Verified 20260608: cycle 17:00 05/06-16:59 06/06, 715.000 / 29.740 / 685.260 == BBDS row 2.
- Monthly detail rows grouped by `Payment Date`/`Advance Date` == daily notice detail rows (same Transaction ID).
- BBDS Total == monthly detail Total (QT June 22.780.000 / 813.103 / 21.966.897; VIETQR May 715.000 / 4.120 / 710.880) == sum of daily notices.
- So: daily notice = source of truth per payout; monthly detail = completeness check; BBDS = monthly fee control (fee invoice).
- Month assignment: QT txn at 30/06 17:05 belongs to JULY report (17:00 cut-off) but its calendar date is June.

## 9. Keys
- Primary: (`Pay Channel`, `Transaction ID`). QT = 9 digit numeric (store as string), VietQR = `PAY-...`. Never blank in samples.
  Unique within and across files; the same ID appears in daily notice and in monthly detail (dedupe on import).
- Link to our order: `Merchant Trans. Ref.` (`PL_VAGABOND_` + 10 char). Order Reference is secondary (12h clock, collisions possible).
- VietQR also has `Bank Trans Ref` (`INV...`) unique per transfer.
- Payout key: Entry number (`Bút toán`, 7 digit, increasing) / `PVS` code.

## 10. Quirks checklist
- Locate header by EN text, not row index; preamble length and column offsets differ by type/channel.
- Header row order QT: VN, formula, EN; VietQR: VN, EN, formula. Header cells padded with spaces and contain newlines.
- Total-row label sits in col D (daily) or col B (monthly) or col A (BBDS); stop data at first row whose `No` is not an int.
- Bin Country format changed between June (full name) and late July (ISO2).
- Monthly QT timestamps lack seconds; daily have seconds -> compare on minute when cross-matching.
- Filename date range for QT monthly is calendar, content window is 17:00 shifted.
- VietQR Remark and Virtual Account fields carry payer data: drop or mask.
- Summary tab missing from CSV export; it holds Entry, Create Date, transfer content and VAT.

## 11. Fixtures (anonymized, raw CSV export form; column A empty)
Daily QT (rows from header EN row):
```csv
,No,Merchant ID,Transaction ID,Order Reference,Merchant Trans. Ref.,Transaction date,Transaction Type,Card Type,Status,Bin Country,Pay Channel, Transaction Amount , Currency , Exchange Rate , Successful Amount (VND) ,Fix fee,Percent fee,Total fee,Advance amount
,1,VAGABOND,240000001,PL_VAGABOND_260729042259,PL_VAGABOND_AAAAAAAAA1,29/07/2026 16:23:53,PURCHASE,VISA,SUCCESS,VN,QT,"300.000,00",VND,"1,00",300.000,"4.000,00","2,40%","11.200,00",288.800
,2,VAGABOND,240000002,PL_VAGABOND_260729073033,PL_VAGABOND_AAAAAAAAA2,29/07/2026 19:31:40,PURCHASE,MASTERCARD,SUCCESS,AU,QT,"420.000,00",VND,"1,00",420.000,"4.000,00","3,60%","19.120,00",400.880
,,,Tổng cộng (Total),,,,,,,,,,,,720.000,,,"30.320,00",689.680
```
Daily VietQR:
```csv
,No,Merchant ID,Transaction ID,Order Reference,Merchant Trans. Ref.,Virtual Account,Virtual Account Name,Bank Trans Ref,Transaction date,Bank ID,Remark,Transaction Type,Pay Channel, Transaction Amount ,Fix fee,Percent fee,Total fee,Total amount after charge fee,Advance amount
,,,,,,,,,,,,,, (1) ,(2),(3),(4)=(2)+(1)*(3),(5)=(1)-(4),
,1,VAGABOND,PAY-AAAAAAAAAAAAAAAAAAAAA1,PL_VAGABOND_260712010827,PL_VAGABOND_BBBBBBBBB1,9688660000000000001,VAGABOND,INVAAAAAAAAAAAAAAAAAAAAA01,12/07/2026 13:08:31,MSB,"NHAN TU 0000000000 NGUYEN VAN A_TMCP Bank X",PURCHASE,VietQR,"734.000,00","1.760,00","0,33%","4.182,00",729.818,729.818
,,,Tổng cộng (Total),,,,,,,,,,,  734.000 ,,,"4.182,00","729.818,00","729.818,00"
```
Monthly QT:
```csv
,No,Merchant Id,Transaction ID,Order Reference,Merchant Trans. Ref.,Transaction Date,Transaction Type,Card Type,Status,Bin Country,Pay Channel,Transaction Amount,Currency,Exchange Rate,Successful Amount (VND),Fix Fee,Percent Fee,Total Fee,Advance Amount,
,1,VAGABOND,210000001,PL_VAGABOND_260602052833,PL_VAGABOND_CCCCCCCCC1,02/06/2026 17:33,PURCHASE,VISA,SUCCESS,VIET NAM,QT,"660.000,00",VND,"1,00",660.000,"4.000,00","2,40%","19.840,00",640.160,04/06/2026
,2,VAGABOND,210000002,PL_VAGABOND_260611080120,PL_VAGABOND_CCCCCCCCC2,11/06/2026 20:11,PURCHASE,AMEX,SUCCESS,VIET NAM,QT,"755.000,00",VND,"1,00",755.000,"4.000,00","3,00%","26.650,00",728.350,15/06/2026
,Tổng cuối,,,,,,,,,,,,,,"1.415.000,00",,,"46.490,00","1.368.510,00",
```
Monthly VIETQR:
```csv
,No,Merchant Id,Transaction ID,Merchant Trans. Ref.,Virtual Account,Virtual Account Name,Bank Trans Ref,Transaction Date,Bank ID,Remark,Transaction Type,Pay Channel,Transaction Amount,Percent Fee,Fix Fee,Total Fee,Total amount after charge fee,Total Advance Amount,Total fee collected,Total fee receivable,Advance Date
,,,,,,,,,,,,,(1),(2),(3),(4)=(1)*(2)+(3),(5)=(1)-(4),,,,
,1,VAGABOND,PAY-AAAAAAAAAAAAAAAAAAAAA2,PL_VAGABOND_DDDDDDDDD1,9688660000000000002,VAGABOND,INVAAAAAAAAAAAAAAAAAAAAA02,12/05/2026 14:52:34,,NHAN TU 0000000000 VND-TGTT-CUSTOMER_TMCP Bank Y,PURCHASE,VIETQR,"715.000,00","0,33%","1.760,00","4.120,00","710.880,00","710.880,00","4.120,00","0,00",13/05/2026
,Tổng cuối (Total),,,,,,,,,,,,,,,"4.120,00","710.880,00","710.880,00","4.120,00","0,00",
```
BBDS (QT):
```csv
"STT
No","Thời gian giao dịch
Transaction date","Loại dịch vụ
Pay channel","Số lượng GD
Number of Trans","Giao dịch thành công
Count success","Giao dịch không thành công
Count failed","Tổng Giá trị GD
Transaction Amount","Tổng giá trị khoanh hoàn trả
The amount held for refund transactions","Tổng giá trị nhả khoanh hoàn trả
Release amount","Giá trị đã tạm ứng
Advance amount","Tổng phí
Total fee"
1,02/06/26 - 03/06/26,QT,2,2,0,1.450.000,0,0,1.397.720,52.280
2,05/06/26 - 06/06/26,QT,1,1,0,715.000,0,0,685.260,29.740
TỔNG CỘNG/Total,,,3,3,0,2.165.000,0,0,2.082.980,82.020
```

=================== payoo.md
# Payoo POS settlement reports - parser spec

Surveyed 06/10/2026, Drive folder `04_Payoo` (1okn1FEJu-qchJLZFbV7yRYG7AMmYX5jV), read-only.
Files read in full: card 23/02, 24/02, 25/02, 26/02, 26/03, 13/04, 17-19/04 (multi-day), 28/04, 15/07;
QR 13-15/03, 20-22/03, 17-19/04 (both copies), 05-07/06. Plus Payoo VAT invoices (PDF) for fee cross-check.

## 0. What is in Drive (source format)

- Subfolders `1. Trần Cao Vân` (1G87l9fc...) and `2. Nguyễn Văn Trỗi` (12VvEhEn...). Contents: Google Sheets,
  monthly "BIEN BAN DOI SOAT" PDFs (screenshots of an Outlook mail, no extractable figures), Payoo fee VAT
  invoices `K26TVU_<so>_<id>.pdf`, one contract PDF. **No csv/xls/xlsx/zip original exists anywhere** (searched
  all non-Sheets/non-PDF files titled "Payoo": none).
- Every Sheet's single tab is named `<file title>.csv`, so the original e-mail attachment was a **CSV**; Drive
  converted it on upload. The raw Payoo bytes are therefore NOT available; what we can see is Google's re-export.
- Google `text/csv` export of these sheets: UTF-8 (no BOM, NFC precomposed Vietnamese), delimiter `,`,
  no quoting, line ending CRLF, **no newline after the last row**.
- **Folder is not the store.** Every file is the master-account report `VAGABOND_TONG` covering all stores.
  Files in the NVT folder contain `VAGABOND_9TCV` rows; QR 17-19/04 and 24/03 exist in BOTH folders with
  identical rows. Adapter must dedupe by event ID, never by file.

## 1. File naming

```
Payoo-POS-Card_<ACCOUNT>_Doisoatkytongket<ddmmyyyy>-<ddmmyyyy>.235959[.csv]
Payoo-POS-QRCode_<ACCOUNT>_Doisoatky<ddmmyyyy>-<ddmmyyyy>.235959[.csv]
```
- Regex: `^Payoo-POS-(Card|QRCode)_([A-Z0-9_]+)_Doisoatky(?:tongket)?(\d{8})-(\d{8})\.235959(?:\.csv)?$`
- `<ACCOUNT>` = master account, always `VAGABOND_TONG` (note: contains `_`, so match greedily up to `_Doisoat`).
- Period = from date 00:00:00 to to-date 23:59:59 (the `.235959` is the end time, not an extension).
  Single day = same date twice. Multi-day files cover weekends/holidays: Fri-Sun (17-19/04, 13-15/03,
  20-22/03), Fri-Mon over a holiday (24-27/04). Card reports are "kỳ tổng kết" (batch-close period),
  QR reports are "kỳ" (transaction period). Drive title has no `.csv`; the raw attachment has it.
- Seen range: card 23/02/2026 to 19/07/2026, QR 06/03/2026 to 19/07/2026. Days with no transactions have no file.

## 2. Layout (both types)

- Row 1: header. Row 2: **numbering row** `1,2,...,25` (card) / `1,...,18` (QR) - must be skipped.
- Row 3..n: one transaction per row. **No preamble, no title row, no total/summary row, no blank trailer.**
- Smallest file seen: 1 data row (card 26/03). Largest: 100 data rows (card 17-19/04).
- Detect type by header (column 12 name) rather than file name: `Số Tiền Giao Dịch Thẻ` = card, `Mã GD QR` col 7 = QR.

## 3. CARD report - 25 columns (exact header text, in order)

| # | Header | Meaning | Type / format | Example (anonymized) |
|---|---|---|---|---|
| 1 | Tài Khoản Payoo Tổng/Quản lý | master account | text | VAGABOND_TONG |
| 2 | Chi Nhánh/Đơn Vị Nhận Tiền Dịch Vụ | receiving unit | text, always = col 1 so far | VAGABOND_TONG |
| 3 | Tài Khoản Payoo Thực Hiện Giao Dịch | **store sub-account** | text | VAGABOND_9TCV / VAGABOND_307NVT |
| 4 | Ngày Giao Dịch | transaction time (local, ICT) | `dd/mm/yyyy hh:mm:ss` | 28/04/2026 09:27:12 |
| 5 | Chi Tiết H.Thức T.Toán | card scheme class | `Thẻ quốc tế` / `Thẻ nội địa` | Thẻ quốc tế |
| 6 | Hình Thức Phát Hành | issuer location | `Phát hành trong nước` / `Phát hành nước ngoài` | Phát hành nước ngoài |
| 7 | Ngân Hàng Phát Hành | issuer bank | bank name or placeholder `NHPHVN` (domestic, unnamed), `NHPHNN` (foreign), `NAPAS` | Techcombank |
| 8 | Kỳ Hạn Trả Góp | installment term | **always blank** | |
| 9 | Mã giao dịch Payoo | Payoo txn id | **always blank** in every row seen | |
| 10 | Số Tham Chiếu | RRN (retrieval ref.) | 12-digit **string, keep leading zeros** | 611800000001 / 001311000999 |
| 11 | Mã Chuẩn Chi | auth code | 6 chars, alnum, keep leading zeros; `000000` on NAPAS | A1B2C3 |
| 12 | Số Tiền Giao Dịch Thẻ | gross card amount | amount, see §5 | 1.900.000.000 (= 1,900,000 VND) |
| 13 | Phí Xử Lý Thẻ | MDR fee | amount | 52.250.000 (= 52,250) |
| 14 | Phí Chuyển Đổi Trả Góp | installment conversion fee | amount, always `0` | 0 |
| 15 | Số Tiền Payoo Thanh Toán | net payout | amount | 1.847.750.000 (= 1,847,750) |
| 16 | Ngày Tổng Kết GD Thẻ | batch-close date | `dd/mm/yyyy`; = date of col 4 in all rows seen | 28/04/2026 |
| 17 | Ngày Payoo Thanh Toán | **settlement/payout date** | `dd/mm/yyyy`; next business day | 29/04/2026 |
| 18 | Mã thiết bị | POS terminal id | text | P6A91696 |
| 19 | Mã đơn hàng đối tác | partner order id | **always blank** (POS has no order link) | |
| 20 | Loại Tác Nghiệp | operation type | only `Thanh toán` seen | Thanh toán |
| 21 | Loại thẻ | funding | `Credit` / `Debit` | Credit |
| 22 | Ghi Chú | note | always blank | |
| 23 | Tổng tiền đơn hàng | order total | amount; = col 12 in every row | 1.900.000.000 |
| 24 | Số tiền giảm giá | discount | amount; always `0` | 0 |
| 25 | Phí xử lý GD khuyến mãi | promo fee | **always blank** (not 0) | |

## 4. QR report - 18 columns

| # | Header | Meaning | Format / example |
|---|---|---|---|
| 1 | Tài Khoản Payoo Tổng/Quản lý | master account | VAGABOND_TONG |
| 2 | Chi Nhánh/Đơn Vị Nhận Tiền Dịch Vụ | receiving unit | VAGABOND_TONG |
| 3 | Tài Khoản Payoo Thực Hiện Giao Dịch | store sub-account | VAGABOND_9TCV (only value seen in QR) |
| 4 | Ngày Giao Dịch | transaction time | `dd/mm/yyyy hh:mm:ss` |
| 5 | Chi Tiết H.Thức T.Toán | channel | always `Tài khoản ngân hàng` |
| 6 | Mã giao dịch Payoo | Payoo txn id | **always blank** |
| 7 | Mã GD QR | QR transaction code | `QR` + 6 upper alnum, e.g. `QR3MF2WR` |
| 8 | Số Tiền Giao Dịch | gross amount | amount |
| 9 | Phí Xử Lý Giao Dịch QR | fee | amount |
| 10 | Số Tiền Payoo Thanh Toán | net payout | amount |
| 11 | Ngày Payoo Thanh Toán | settlement date | `dd/mm/yyyy` |
| 12 | Mã thiết bị | terminal | P6A91696 |
| 13 | Mã đơn hàng đối tác | partner order id | blank |
| 14 | Loại Tác Nghiệp | operation | `Thanh toán` |
| 15 | Ghi Chú | note | blank |
| 16 | Tổng tiền đơn hàng | order total | = col 8 |
| 17 | Số tiền giảm giá | discount | `0` |
| 18 | Phí xử lý GD khuyến mãi | promo fee | blank |

QR has NO batch-close date, NO card/bank columns, NO RRN/auth code. QR settlement is next business day
(13-15/03 -> 16/03, 20/03 -> 23/03, 17-19/04 -> 20/04, 05-07/06 -> 08/06).

## 5. Amounts and the VND unit (conclusion: displayed value / 1000)

- In the Sheets and in their CSV export every amount appears as `d.ddd.ddd.ddd` (dot thousands grouping),
  zero as plain `0`. Every non-zero amount ends in `.000`.
- **True VND = digits with dots removed, divided by 1000.** `1.900.000.000` = 1,900,000 VND. Evidence:
  1. Order size: the smallest card sale is `350.000.000`, typical `750.000.000`-`7.650.000.000`. At /1000 this
     is 350k-7.65M VND, matching cake orders; at face value it would be 350M-7.6B VND per cake (impossible).
     Largest: `36.000.000.000` at VAGABOND_307NVT (= 36M VND, a wholesale order at the production site).
  2. Fee granularity: fees are rounded to 10 VND only at /1000 (2.75% x 7,650,000 = 210,375 -> `210.380.000`).
  3. QR fee floor `20.000.000` = 20,000 VND; QR fee = max(0.22% x amount, 20,000): 11,200,000 x 0.22% = 24,640
     -> `24.640.000`. A 20-million-VND minimum fee would be absurd.
  4. Payoo VAT invoices (same folder) for monthly fees are in the low millions VND (card fee 02/2026:
     3,724,505 + VAT; 03/2026: 4,098,668 + VAT; QR fee 02/2026: 27,975 + VAT), i.e. same order of magnitude as
     the /1000 reading (23-26/02 fees sum to 5,076,260 VND at /1000), and 1000x smaller than face value.
     NOTE: invoices do NOT reconcile exactly with row fee sums (5.08M for 4 days of Feb vs 4.10M incl. VAT
     for the month) - do not use invoices as a control total until Payoo explains the basis.
- Most likely the raw Payoo CSV holds `1900000.000` (3 decimals) and the vi-VN Sheets import read `.` as a
  grouping separator (that also explains `0.000` -> `0`). Leading zeros in cols 10/11 survived, so those columns
  were kept as text. **Unconfirmed: no raw attachment is in Drive.** Get one raw CSV from the Payoo e-mail
  before finalizing.
- Adapter rule (handles both shapes): strip spaces; if value matches `^\d{1,3}(\.\d{3})+$` with >= 2 dots,
  remove dots and divide by 1000 (Sheets artefact); if it matches `^\d+\.\d{1,3}$` (one dot) parse as a decimal
  (raw Payoo); `0`/`0.000` -> 0; blank -> None (cols 25/18 are blank, not zero). Then require an integer VND
  result, else raise.
- Fee rates observed (unit-independent ratios): foreign-issued 2.75%; domestic-issued international card
  1.65%; `Thẻ nội địa` (NAPAS/PVCombank) 0.77%; QR 0.22% min 20,000 VND.

## 6. Equations (checked)

- Card: `col12 - col13 - col14 = col15` holds on **all 37 rows of 28/04** (computed) and every row inspected in
  the other card files; col14 always 0. `col23 = col12`, `col24 = 0` everywhere.
  Daily check 28/04: gross 115,400,000; fee 2,267,970; payout 113,132,030 VND.
- QR: `col8 - col9 = col10` on all 9 distinct QR rows read; `col16 = col8`, `col17 = 0`.
- No row breaks these rules. No refunds, voids, reversals, negative amounts or installment rows were seen
  (col 20 always `Thanh toán`). The adapter should still reject/flag any other col 20 value instead of
  guessing the sign.

## 7. Event ID

- Card: `Mã giao dịch Payoo` is always blank, so not usable. Use **`Số Tham Chiếu` (RRN)**: present on every row,
  unique across all rows read (incl. the 100-row file). RRN encodes Y+julian day of the txn
  (`6118...` = 2026 day 118 = 28/04), but rows routed via Vietcombank use another series (`0013110003xx`,
  `0012110003xx`, `0020110006xx`) - sequential per acquirer, so not globally unique forever.
  Recommended key: `payoo-card:{col3}:{col18}:{col10}:{col4 date}` (RRN + store + terminal + txn date).
  `Mã Chuẩn Chi` is NOT unique (`000000` on all NAPAS rows).
- QR: **`Mã GD QR`** (col 7), always present, unique in all rows read. Key: `payoo-qr:{col7}`.
- Duplicates across files/folders are real (same QR file in both store folders) -> upsert on key.

## 8. Stores, terminals, dates

| Sub-account (col 3) | Store | Terminal (col 18) |
|---|---|---|
| VAGABOND_9TCV | 9 Trần Cao Vân, Q.1 | P6A91696 |
| VAGABOND_307NVT | 307/1 Nguyễn Văn Trỗi, Tân Bình | P6A91697 |
Map store by col 3 (or terminal), never by Drive folder or file name. 307NVT is rare (1 card row in 17-19/04).
Settlement date for bank matching = col 17 (card) / col 11 (QR); one payout per file period is expected
(sum of col 15 / col 10 per settlement date).

## 9. Quirks

- Numbering row 2 (`1,2,3...`) looks like data to naive parsers.
- Trailing empty fields: lines end with `,` (col 25 / col 18 blank) -> 25 / 18 fields after split.
- Cols 8, 9, 19, 22, 25 (card) and 6, 13, 15, 18 (QR) are empty in every file; do not require them.
- Bank names are free text (`Shinhan Bank`, `Standard Chartered`, `Public Bank`, `PVCombank`, ...).
- Auth codes may be all letters (`SUDHYK`) or end in a letter (`06185I`); read every ID column as string.
- Header has precomposed (NFC) Vietnamese; normalise both sides with NFC before comparing header names.
- Multi-day files: col 16 (card) differs per row (17/04, 18/04, 19/04) while col 17 is one date.

## 10. Test fixtures (Google CSV-export shape: UTF-8, CRLF, no final newline; IDs are fake)

`payoo_card_fixture.csv` (name: `Payoo-POS-Card_VAGABOND_TONG_Doisoatkytongket28042026-28042026.235959.csv`)
```csv
Tài Khoản Payoo Tổng/Quản lý,Chi Nhánh/Đơn Vị Nhận Tiền Dịch Vụ,Tài Khoản Payoo Thực Hiện Giao Dịch,Ngày Giao Dịch,Chi Tiết H.Thức T.Toán,Hình Thức Phát Hành,Ngân Hàng Phát Hành,Kỳ Hạn Trả Góp,Mã giao dịch Payoo,Số Tham Chiếu,Mã Chuẩn Chi,Số Tiền Giao Dịch Thẻ,Phí Xử Lý Thẻ,Phí Chuyển Đổi Trả Góp,Số Tiền Payoo Thanh Toán,Ngày Tổng Kết GD Thẻ,Ngày Payoo Thanh Toán,Mã thiết bị,Mã đơn hàng đối tác,Loại Tác Nghiệp,Loại thẻ,Ghi Chú,Tổng tiền đơn hàng,Số tiền giảm giá,Phí xử lý GD khuyến mãi
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,28/04/2026 09:27:12,Thẻ quốc tế,Phát hành nước ngoài,NHPHNN,,,611800000001,A1B2C3,1.900.000.000,52.250.000,0,1.847.750.000,28/04/2026,29/04/2026,P6A91696,,Thanh toán,Credit,,1.900.000.000,0,
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,28/04/2026 12:24:44,Thẻ quốc tế,Phát hành trong nước,Vietcombank,,,001311000999,012345,800.000.000,13.200.000,0,786.800.000,28/04/2026,29/04/2026,P6A91696,,Thanh toán,Debit,,800.000.000,0,
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_307NVT,28/04/2026 15:24:41,Thẻ nội địa,Phát hành trong nước,NAPAS,,,611815000999,000000,3.600.000.000,27.720.000,0,3.572.280.000,28/04/2026,29/04/2026,P6A91697,,Thanh toán,Debit,,3.600.000.000,0,
```
Expected VND: (1,900,000 / 52,250 / 1,847,750), (800,000 / 13,200 / 786,800), (3,600,000 / 27,720 / 3,572,280).

`payoo_qr_fixture.csv` (name: `Payoo-POS-QRCode_VAGABOND_TONG_Doisoatky20032026-22032026.235959.csv`)
```csv
Tài Khoản Payoo Tổng/Quản lý,Chi Nhánh/Đơn Vị Nhận Tiền Dịch Vụ,Tài Khoản Payoo Thực Hiện Giao Dịch,Ngày Giao Dịch,Chi Tiết H.Thức T.Toán,Mã giao dịch Payoo,Mã GD QR,Số Tiền Giao Dịch,Phí Xử Lý Giao Dịch QR,Số Tiền Payoo Thanh Toán,Ngày Payoo Thanh Toán,Mã thiết bị,Mã đơn hàng đối tác,Loại Tác Nghiệp,Ghi Chú,Tổng tiền đơn hàng,Số tiền giảm giá,Phí xử lý GD khuyến mãi
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,20/03/2026 14:02:21,Tài khoản ngân hàng,,QRTEST01,7.200.000.000,20.000.000,7.180.000.000,23/03/2026,P6A91696,,Thanh toán,,7.200.000.000,0,
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,20/03/2026 15:58:49,Tài khoản ngân hàng,,QRTEST02,11.200.000.000,24.640.000,11.175.360.000,23/03/2026,P6A91696,,Thanh toán,,11.200.000.000,0,
VAGABOND_TONG,VAGABOND_TONG,VAGABOND_9TCV,22/03/2026 17:24:54,Tài khoản ngân hàng,,QRTEST03,1.600.000.000,20.000.000,1.580.000.000,23/03/2026,P6A91696,,Thanh toán,,1.600.000.000,0,
```
Expected VND: (7,200,000 / 20,000 / 7,180,000), (11,200,000 / 24,640 / 11,175,360), (1,600,000 / 20,000 / 1,580,000).
When writing the fixture files: join lines with `\r\n` and omit the final newline to mirror the export.

=================== shinhan_pos.md
# Shinhan Bank POS acquiring - Merchant settlement reports (MSR_*)

Source: Drive folder `06_Shinhan` (1cdpLWNm-oOYwTizcyj8t2nIBW5toVWZI). Surveyed 2026-10-06, read-only.
Inventory: 30 Google Sheets (27 daily `MSR_40019_...`, 3 monthly `MSR_40021_...`), plus 3 PDFs
(card payment contract, a POS e-mail change form, a 2024 doc) that are not reports.
Files parsed in full: daily 20260413, 20260626, 20260720, 20260803 (259 detail rows);
monthly 20260301, 20260601 (summary only), 20260701 (315 detail rows).

## 1. File naming, report types, merchant

`MSR_<RPT>_GID_<GID>_<TPL>_<YYYYMMDD>_<SEQ>`

| Part | Seen | Meaning (evidence) |
|---|---|---|
| `MSR` | always | Merchant Settlement/Statement Report |
| `<RPT>` | `40019`, `40021` | **Report type, NOT store.** 40019 = daily "MERCHANT STATEMENT REPORT" (sheets `Summary_40019_enhance`, `Detail_40019_enhance`); 40021 = "MONTHLY DETAIL REPORT" (sheets `Monthly_Summary`, `Monthly_Detail`). The same MID 71000298209 appears in both. |
| `GID_<GID>` | `20000414` (with 40019), `20006881` (with 40021) | Report subscription / merchant-group id at the bank. Always paired 1:1 with RPT. Scope differs: GID 20000414 daily contains **both** MIDs; GID 20006881 monthly contains **only** MID 71000298209 (July monthly: 119 rows, all MID ...209; daily 20260720 rows for MID ...209 = 22/22 found in monthly, MID ...426 = 0/41). |
| `<TPL>` | `421` (daily), `425` (monthly) | Template / job id; constant per RPT. Treat as opaque. |
| `<YYYYMMDD>` | e.g. 20260720 | Daily: report date = payment (settlement) date. Monthly: first day of covered month (20260601 covers 01/06/2026-30/06/2026). |
| `<SEQ>` | `_1` | Run sequence; only `_1` seen. |

Merchant (header block, identical in all files): legal name `CONG TY TNHH PATISSERIE VAGABOND`, TIN `0318561568`,
address `9 TRAN CAO VAN, PHUONG DA KAO, QUAN 1,` / `THANH PHO HO CHI MINH, VIET NAM` (daily only; monthly has no address).
Two acceptance points (1 TID per MID), same settlement account (masked `700000****00`), branch `SAIGON BRANCH`:

| MID | TID | Merchant Name (DBA) | First seen |
|---|---|---|---|
| 71000298209 | 73003868 | THE VAGABOND | March 2026 |
| 71000435426 | 73005422 | THE VAGABOND 1 | July 2026 (daily only) |

The report does not say which physical store each MID is; the header address is the legal entity address. Confirm with the user.

## 2. Raw format

- Drive holds **converted Google Sheets only**. Each subfolder named `MSR_..._1.xls` contains exactly one Google Sheet of
  the same name (checked 2 folders); no original .xls kept. Originals were evidently BIFF `.xls` from the bank portal/e-mail.
  A parser should accept `.xls` (xlrd) and `.xlsx`; locate by cell content, not by fixed row, but positions below were stable in all files.
- 2 sheets per file, Summary first. Drive CSV export returns **only the first (Summary) sheet**.
- Every cell is text (`@`) except money/count cells (numeric, format `#,##0`). Unicode (Vietnamese diacritics) in labels; data values are ASCII.
- Bilingual headers: one cell = Vietnamese + `\n` + English. Header label typos are verbatim: `Paymen date`, `Indentification`, `báo nơ`.
- Rows 1000 / many blank columns are Sheets padding; stop at the total row.
- CSV export (if used): UTF-8, no BOM, CRLF row ends, LF inside quoted header cells, numbers rendered with vi-VN grouping (`14.457.000`).

## 3. Daily report (RPT 40019) - two sheets, 28 columns A..AB

### 3a. Preamble (both sheets, rows 1-18)
B2 `SAO KÊ CHI TIẾT GIAO DỊCH`; B4 `MERCHANT STATEMENT REPORT`; label in A (VN row n, EN row n+1), value in F:
F6 report date `dd/mm/yyyy`; F8 TIN; F10 legal name; F12 address1; F14 address2; F16 address3 (blank).

### 3b. `Summary_40019_enhance` - header row 19, data from row 20, one row per MID
| Col | Header (VN \n EN) | Type / format | Example |
|---|---|---|---|
| A (A:B merged) | `No.` | text int | `1` |
| C | `Ngày thanh toán\nPaymen date` | text `YYYYMMDD` | `20260720` |
| D | `Mã Đại lý\nMID` | text 11 digits | `71000000001` |
| E (E:H) | `Tên Kinh Doanh\nMerchant Name` | text | `THE VAGABOND` |
| I | `Số tài khoản\nAccount No.` | masked text | `700000****00` |
| J (J:K) | `Số lượng giao dịch\nCount of trxn` | number | `22` |
| L | `Số tiền giao dịch\nTrxn amount (VND)` | number | `1792000` |
| M | `Phí dịch vụ (Bao gồm VAT)\nMDF (include VAT)` | number | `26006` |
| N | `Phí xử lý giao dịch (Bao gồm VAT)\nProcessing fee (include VAT)` | number | `0` |
| O | `Số tiền thanh toán\nPayment amount` | number | `1765994` |

Total row: A = `TỔNG/TOTAL`, values in J, L, M, N, O (= column sums).

### 3c. `Detail_40019_enhance` - rows 19/20 caption `Chi tiết giao dịch báo có/báo nợ` / `Credit/Debit Detail`; header row 21; data from 22
**Header labels and data values are NOT in the same columns for VAT** (merge offset): header `Processing fee` is merged S21:T21 and
header `VAT` sits in U21, but data merges are T:U, so the VAT value is in **T**. Map by the positions below, not by header text.

| Data col | Header text (header cell) | Meaning | Type / format | Anonymized example |
|---|---|---|---|---|
| A (A:B) | `No.` | row seq in file | text int | `1` |
| C | `Ngày thanh toán\nPaymen date` | settlement date | text `dd-mm-yyyy` | `20-07-2026` |
| D | `Mã Đại lý\nMID` | merchant id | text | `71000000001` |
| E (E:H) | `Mã Thiết bị\nTID` | terminal id | text 8 digits | `73000001` |
| I | `Tên Kinh Doanh\nMerchant Name` | DBA name | text | `THE VAGABOND` |
| J | `Tài khoản báo có\nAccount No.` | credited account (masked) | text | `700000****00` |
| K (K:L) | `Số thẻ\nCard No.` | PAN masked by bank | `9999-99**-****-9999`; 19-digit Napas: `9999-99**-****-***9-999` | `4111-11**-****-1111` |
| M | `Thời gian giao dịch\nTrxn date` | authorization time (local) | text `HH:MM:SS dd-mm-yyyy` | `09:44:15 19-07-2026` |
| N | `Mã yêu cầu\nRequest ID` | - | **always blank** (0/574) | |
| O | `Mã tham chiếu giao dịch\nPurchase ID` | - | **always blank** (0/574) | |
| P | `Số tiền giao dịch\nTrxn amount (VND)` | gross | number | `200000` |
| Q | `Mức phí dịch vụ (%)\nMDR (%)` | MDR percent | **text** `d.ddd`, dot = decimal (`1.440` = 1.44 %) | `1.440` |
| R | `Phí dịch vụ (Bao gồm VAT)\nMDF (include VAT)` | MDF incl. VAT | number | `2880` |
| S | `Phí xử lý giao dịch \n(Bao gồm VAT)\nProcessing fee\n(include VAT)` (S:T) | processing fee | number, always 0 so far | `0` |
| T (T:U) | `Thuế \nVAT` (header in U) | VAT portion of MDF, informational | number | `262` |
| V | `Số tiền báo có/ báo nơ\nPayment amount` | net credited | number | `197120` |
| W | `Mã chuẩn chi\nApproval code` | auth code | text **with literal leading apostrophe**, 6 alnum chars after it | `'123456`, `'F01234`, `'12345Z` |
| X | `Hoàn/Hủy\nReversal/Refund \n(Y/N)` | reversal/refund flag | `Y`/`N` | `N` |
| Y | `Loại thẻ\nBrand Card` | scheme | `Visa`, `MasterCard`, `JCB`, `Napas` | `Visa` |
| Z | `Kênh giao dịch\nChannel` | channel | `POS` only | `POS` |
| AA | `Thẻ trong nước/ nước ngoài\nDomestic/ International Card` | card origin | `DOMESTIC`/`INTERNATIONAL` | `DOMESTIC` |
| AB | `Chi nhánh quản lý\nBranch Name` | managing branch | text | `SAIGON BRANCH` |

Total row: label `Tổng/Total` in **O** (not A), sums in P, R, S, T, V. No count cell. Rows are not sorted by time.

## 4. Monthly report (RPT 40021) - two sheets
Preamble: A2 `\nCHI TIẾT GIAO DỊCH TRONG THÁNG` (leading LF), A4 `MONTHLY DETAIL REPORT`; labels in A.
`Monthly_Summary`: F6 name, F8 TIN, F10 period from `dd/mm/yyyy`, I10 `-`, J10 period to; Q13 `Đơn vị tính: VND`.
`Monthly_Detail`: **shifted one column right**: G6 name, G8 TIN, G10 from, I10 `-`, K10 to; AD13 `Đơn vị tính: VND`.

### 4a. `Monthly_Summary` - header row 15, one row per (payment date, MID)
A `No.`; B `Ngày thanh toán\nPaymen date` (`dd/mm/yyyy`); C `Mã Đại lý\nMID`; D (D:F) `Tên Kinh Doanh\nMerchant Name`;
G (G:J) `Số tài khoản\nAccount No.`; K (K:L) `Số lượng giao dịch\nCount of trxn`; M `Số tiền giao dịch\nTrxn amount ` (trailing space, no "(VND)");
N `Phí dịch vụ (Bao gồm VAT)\nMDF (include VAT)`; O `Phí xử lý giao dịch (Bao gồm VAT)\nProcessing fee (include VAT)`;
P (header P:Q, data P:R) `Số tiền báo có/ báo nợ\nPayment amount`. Total row A = `TỔNG/TOTAL`, sums in K, M, N, O, P.

### 4b. `Monthly_Detail` - header row 14, 30 columns A..AD
Same 22 fields as daily detail, different positions; payment date format `dd/mm/yyyy` (daily uses `dd-mm-yyyy`):
A No.; B payment date; C MID; D (D:E) TID; F (F:I) Merchant Name; J (J:L) Account No.; M Card No.; N Trxn date;
O Request ID; P Purchase ID; Q Trxn amount (VND); R MDR (%); S MDF; T (header T:U) Processing fee; **U VAT (data U:V, header in V)**;
W Payment amount; X Approval code; Y Reversal/Refund; Z Brand; AA Channel; AB Domestic/International; AC (AC:AD) Branch.
Total row: `Tổng/Total` in **P**, sums in Q, S, T, U, W.

## 5. Amount unit: whole VND (not thousands)
- Headers say `(VND)`; monthly sheets carry `Đơn vị tính: VND`.
- Gross amounts are integers, all multiples of 1,000, range 15,000-980,000 per ticket (bakery basket sizes), daily totals 0.36-32.5 M.
- Fees are exact integers that only make sense in VND: MDF = round(amount x MDR/100) holds for 574/574 rows (200,000 x 1.44 % = 2,880).
- Numeric cells, no decimals. Beware: in CSV exports `.` is the thousands separator (`1.792.000`) while in the MDR text column `.` is the decimal point (`1.440`).

## 6. Equations (verified on every row and total of all parsed files)
- `Payment amount = Trxn amount - MDF - Processing fee` : 574/574 rows. **No separate VAT deduction** - MDF already includes VAT.
- `VAT = round(MDF / 11)` (10 % VAT inside MDF): 574/574. Do not subtract VAT again; book MDF as fee incl. VAT, VAT column only for the input-VAT split.
- `MDF = round(Trxn amount x MDR / 100)`: 574/574. MDR seen: Visa/MC domestic 1.440, Visa/MC international 2.500, JCB domestic 2.200, JCB international 2.600, Napas 0.780.
- Control totals: detail column sums = detail total row = summary total row (e.g. 20260720: 63 trxn, 14,457,000 / 237,585 / 0 / 14,219,415). Summary per-MID rows = detail grouped by MID.
- Settlement timing: payment date = next business day; Friday-Sunday transactions settle Monday (20260720 holds 17,18,19-07; 20260803 holds 31-07, 01-08, 02-08).

## 7. Transaction identity
- Request ID and Purchase ID: blank in 100 % of rows. Unusable.
- Approval code alone is NOT unique: `'000000` appears twice in daily 20260803 (two Napas trxns, MID ...426) and twice in monthly 20260701 (Napas, MID ...209). Napas/domestic switch returns 000000.
- `No.` is only a row counter.
- Recommended natural key: `MID | TID | trxn_datetime | approval_code(stripped) | card_mask | amount`. Zero duplicates in every file; `(approval, trxn_datetime)` and `(MID, trxn_datetime, card last4, amount)` were also each duplicate-free.
- The same transaction appears in both the daily and the monthly report (22/22 overlap checked) -> dedupe across RPT types with this key, or ingest only one report type (daily 40019 covers both MIDs; monthly 40021 currently covers MID ...209 only).

## 8. Transaction types and signs
- All 574 parsed rows: `Reversal/Refund = N`, channel `POS`, all amounts positive. No void/refund/chargeback sample exists.
- Header wording "báo có / báo nợ" (credit/debit) implies a refund row would be a debit; sign convention unknown. Parser should: accept negative numbers,
  treat `X='Y'` as reversal/refund, and fail loudly (or quarantine) on `Y` until a real sample confirms the sign.

## 9. Quirks checklist
1. Header text is in a different column than its data for VAT (daily U vs T; monthly V vs U) and Processing fee header spans two columns.
2. Daily vs monthly detail columns are offset (28 vs 30 cols); preamble value cells also shift (F vs G).
3. Three date formats: `YYYYMMDD` (daily summary), `dd-mm-yyyy` (daily detail), `dd/mm/yyyy` (monthly, report date), plus `HH:MM:SS dd-mm-yyyy`.
4. Approval code carries a literal `'` prefix and can contain letters (`'F62221`, `'01480G`, `'JKRTOC`); keep as string.
5. MDR is text with decimal dot; amounts are numbers (or dot-grouped strings in CSV).
6. Total-row label lives in A (summaries) but in the Purchase ID column (details).
7. IDs (MID, TID, TIN, No.) are text; keep leading zeros (TIN `0318561568`).
8. Two GIDs give different MID coverage (see 1); do not sum daily + monthly.
9. Card numbers already masked by the bank; never store more than mask. 19-digit Napas mask has an extra group.

## 10. Fixtures (anonymized; empty cells kept to reproduce raw column positions; preamble omitted)

Daily summary (`Summary_40019_enhance`, A19:O22):
```csv
No.,,"Ngày thanh toán
Paymen date","Mã Đại lý
MID","Tên Kinh Doanh
Merchant Name",,,,"Số tài khoản
Account No.","Số lượng giao dịch
Count of trxn",,"Số tiền giao dịch
Trxn amount (VND)","Phí dịch vụ (Bao gồm VAT)
MDF (include VAT)","Phí xử lý giao dịch (Bao gồm VAT)
Processing fee (include VAT)","Số tiền thanh toán
Payment amount"
1,,20260720,71000000001,THE VAGABOND,,,,700000****00,2,,295000,3621,0,291379
2,,20260720,71000000002,THE VAGABOND 1,,,,700000****00,1,,240000,6000,0,234000
TỔNG/TOTAL,,,,,,,,,3,,535000,9621,0,525379
```

Daily detail (`Detail_40019_enhance`, A21:AB25):
```csv
No.,,"Ngày thanh toán
Paymen date","Mã Đại lý
MID","Mã Thiết bị
TID",,,,"Tên Kinh Doanh
Merchant Name","Tài khoản báo có
Account No.","Số thẻ
Card No.",,"Thời gian giao dịch
Trxn date","Mã yêu cầu
Request ID","Mã tham chiếu giao dịch
Purchase ID","Số tiền giao dịch
Trxn amount (VND)","Mức phí dịch vụ (%)
MDR (%)","Phí dịch vụ (Bao gồm VAT)
MDF (include VAT)","Phí xử lý giao dịch 
(Bao gồm VAT)
Processing fee
(include VAT)",,"Thuế 
VAT","Số tiền báo có/ báo nơ
Payment amount","Mã chuẩn chi
Approval code","Hoàn/Hủy
Reversal/Refund 
(Y/N)","Loại thẻ
Brand Card","Kênh giao dịch
Channel","Thẻ trong nước/ nước ngoài
Domestic/ International Card","Chi nhánh quản lý
Branch Name"
1,,20-07-2026,71000000001,73000001,,,,THE VAGABOND,700000****00,4111-11**-****-1111,,09:44:15 19-07-2026,,,200000,1.440,2880,0,262,,197120,'123456,N,Visa,POS,DOMESTIC,SAIGON BRANCH
2,,20-07-2026,71000000001,73000001,,,,THE VAGABOND,700000****00,9704-00**-****-***0-001,,20:25:35 18-07-2026,,,95000,0.780,741,0,67,,94259,'000000,N,Napas,POS,DOMESTIC,SAIGON BRANCH
3,,20-07-2026,71000000002,73000002,,,,THE VAGABOND 1,700000****00,5555-55**-****-4444,,07:33:45 17-07-2026,,,240000,2.500,6000,0,545,,234000,'F01234,N,MasterCard,POS,INTERNATIONAL,SAIGON BRANCH
,,,,,,,,,,,,,,Tổng/Total,535000,,9621,0,874,,525379,,,,,,
```

Monthly summary (`Monthly_Summary`, A15:R18):
```csv
No.,"Ngày thanh toán
Paymen date","Mã Đại lý
MID","Tên Kinh Doanh
Merchant Name",,,"Số tài khoản
Account No.",,,,"Số lượng giao dịch
Count of trxn",,"Số tiền giao dịch
Trxn amount ","Phí dịch vụ (Bao gồm VAT)
MDF (include VAT)","Phí xử lý giao dịch (Bao gồm VAT)
Processing fee (include VAT)","Số tiền báo có/ báo nợ
Payment amount",,
1,01/07/2026,71000000001,THE VAGABOND,,,700000****00,,,,2,,295000,3621,0,291379,,
2,02/07/2026,71000000001,THE VAGABOND,,,700000****00,,,,1,,240000,6000,0,234000,,
TỔNG/TOTAL,,,,,,,,,,3,,535000,9621,0,525379,,
```

Monthly detail (`Monthly_Detail`, A14:AD17):
```csv
No.,"Ngày thanh toán
Paymen date","Mã Đại lý
MID","Mã Thiết bị
TID",,"Tên Kinh Doanh
Merchant Name",,,,"Tài khoản báo có
Account No.",,,"Số thẻ
Card No.","Thời gian giao dịch
Trxn date","Mã yêu cầu
Request ID","Mã tham chiếu giao dịch
Purchase ID","Số tiền giao dịch
Trxn amount (VND)","Mức phí dịch vụ (%)
MDR (%)","Phí dịch vụ (Bao gồm VAT)
MDF (include VAT)","Phí xử lý giao dịch 
(Bao gồm VAT)
Processing fee
(include VAT)",,"Thuế 
VAT","Số tiền báo có/ báo nơ
Payment amount","Mã chuẩn chi
Approval code","Hoàn/Hủy
Reversal/Refund 
(Y/N)","Loại thẻ
Brand Card","Kênh giao dịch
Channel","Thẻ trong nước/ nước ngoài
Domestic/ International Card","Chi nhánh quản lý
Branch Name",
1,01/07/2026,71000000001,73000001,,THE VAGABOND,,,,700000****00,,,4111-11**-****-1111,10:06:32 30-06-2026,,,200000,1.440,2880,0,262,,197120,'123456,N,Visa,POS,DOMESTIC,SAIGON BRANCH,
2,01/07/2026,71000000001,73000001,,THE VAGABOND,,,,700000****00,,,9704-00**-****-***0-001,15:38:53 30-06-2026,,,95000,0.780,741,0,67,,94259,'000000,N,Napas,POS,DOMESTIC,SAIGON BRANCH,
3,02/07/2026,71000000001,73000001,,THE VAGABOND,,,,700000****00,,,5555-55**-****-4444,07:33:45 01-07-2026,,,240000,2.500,6000,0,545,,234000,'F01234,N,MasterCard,POS,INTERNATIONAL,SAIGON BRANCH,
,,,,,,,,,,,,,,,Tổng/Total,535000,,9621,0,874,,525379,,,,,,,
```
Fixture arithmetic follows section 6 (MDF = round(amt x MDR), VAT = round(MDF/11), net = amt - MDF).

=================== shopeefood.md
# ShopeeFood - daily income details spec

Surveyed 2026-10-06 from Drive folder `05_ShopeeFood`. Files read in full:
`Shopeefood_Income_Details_Merchant_25-11-2024` (old 11-col schema, TCV only),
`..._27-04-2025` (12 cols, TCV + NVT), `..._28-03-2026` (12 cols, TCV + NVT),
`..._27-07-2026` (12 cols, TCV only; also exported as raw CSV).
Ignore in vendor root: `SHOPEEFOOD_VN_..._Phu luc 1/2_...pdf`; in NVHTN folder:
`Hop dong_SHOPEEFOOD_...pdf` (that folder has NO reports). The TCV folder also holds VAT
invoices from Foody (`<so>_C26TCS_<DDMMYYYY>.pdf`, e.g. `257712_C26TCS_07072026.pdf`,
seller CÔNG TY CỔ PHẦN FOODY, buyer Vagabond): not settlement data, skip in this parser.

## 1. Files

- Name: `Shopeefood_Income_Details_Merchant_<DD-MM-YYYY>` (Google Sheet converted from a
  `.csv`; the single sheet is named `Shopeefood_Income_Details_Merchant_<DD-MM-YYYY>.csv`).
- Period: one day (all rows have that date). Range seen: 2024-11-15 .. 2026-08-01.
- Scope: MERCHANT level, not store level. One file can mix stores (28-03-2026 has rows for
  both `10322362` and `10332477`), yet all files sit in the `1. Trần Cao Vân` folder.
- Store identity INSIDE file: column `ID cửa hàng` (8-digit Shopee store ID) and
  `Tên cửa hàng`:
  - `10322362` = `The Vagabond Pâtisserie & Café - Trần Cao Vân`
  - `10332477` = `The Vagabond Pâtisserie & Café - Nguyễn Văn Trỗi`
  No ShopeeFood data seen for Nhà Văn Hóa Thanh Niên.
- Raw format: one sheet, row 1 header, no preamble, no total/summary row, no status column.

## 2. Header (exact text, in order)

Current schema (12 columns, seen 2025-04 onward):
```
STT | Mã Đơn Hàng | ID cửa hàng | Tên cửa hàng | Thời gian hoàn thành/ huỷ đơn |
Giá trị đơn hàng | Khuyến mại từ quán | Phí dịch vụ | Phí vận chuyển trả cho quán |
Chiết khấu | Thuế khấu trừ | Thực thu
```
Old schema (11 columns, seen 2024-11): same but WITHOUT `Thuế khấu trừ`.
Map columns by header text, treat a missing `Thuế khấu trừ` as 0.

| Col | Header | Meaning | Type / format | Example (anonymized) |
|---|---|---|---|---|
| A | STT | row number | int | 1 |
| B | Mã Đơn Hàng | Shopee order code | text `DDMMY-NNNNNNNNN` | 27076-100000001 |
| C | ID cửa hàng | store ID | 8-digit int, read as text | 10322362 |
| D | Tên cửa hàng | store name | text | The Vagabond Pâtisserie & Café - Trần Cao Vân |
| E | Thời gian hoàn thành/ huỷ đơn | completion time | `DD/MM/YYYY HH:MM:SS`, ICT | 27/07/2026 09:28:22 |
| F | Giá trị đơn hàng | gross menu value | THOUSAND VND, integer | 280 |
| G | Khuyến mại từ quán | merchant-funded promo | thousand VND, up to 3 dp | 39,2 |
| H | Phí dịch vụ | service fee | thousand VND, 0 in all samples | 0 |
| I | Phí vận chuyển trả cho quán | delivery fee paid to merchant | thousand VND, 0 in all samples | 0 |
| J | Chiết khấu | Shopee commission | thousand VND, 3 dp | 41,244 |
| K | Thuế khấu trừ | tax withheld (new schema only) | thousand VND, 0 in all samples | 0 |
| L | Thực thu | net payout for the order | thousand VND, 3 dp | 238,756 |

Rows are ordered by order code, not by time (times go 14:19, 14:34, 14:30 ...).

## 3. Raw cell values and THE UNIT

Drive CSV export of 27-07-2026 (bytes): header, then
`1,27076-...,10322362,The Vagabond ...,27/07/2026 09:28:22,280,0,0,0,"41,244",0,"238,756"\r\n`
- Decimal separator is `,` (vi-VN locale of the sheet); values with a fraction are quoted.
  CRLF line ends, no trailing newline. If the original Shopee CSV or an en-US view is used
  the same value shows as `41.244` / `82.488`.
- **Unit = thousand VND (nghìn đồng), 3 decimal places = exact VND.**
  `41,244` = 41.244 thousand = 41,244 VND; `280` = 280,000 VND.
- Evidence:
  1. Gross values 45..655 only make sense as 45k..655k VND bakery baskets
     (same menu sells 100k..700k on Grab/Xanh SM).
  2. Commission is an exact rate of (gross - promo) at 3 dp:
     (280 - 0) x 0.1473 = 41.244; (190 - 20) x 0.1473 = 25.041; (655 - 104.2) x 0.1473 =
     81.133 (2026 files). 2024/2025 rate is 15%: (60 - 11) x 0.15 = 7.35; (190 - 20) x 0.15 = 25.5.
  3. Net payouts like 238.756 -> 238,756 VND are plausible, 238.756 VND is not.
- Trailing zeros are dropped: `72,48` = 72.480 thousand = 72,480 VND, `39,2` = 39,200 VND,
  `115,25` = 115,250 VND. NEVER parse by deleting separators (that gives 7,248 and 392).
- Parse rule: `vnd = round(Decimal(cell.replace(',', '.')) * 1000)` when the cell came from
  the vi-VN export; if reading the original Shopee CSV, `.` is already the decimal point.
  Detect by locale/source, not by guessing per cell (`41.244` is ambiguous on its own).

## 4. Equation

- Per order: `Thực thu = Giá trị - Khuyến mại từ quán - Phí dịch vụ + Phí vận chuyển trả cho quán - Chiết khấu - Thuế khấu trừ`
  (H, I, K were 0 in every sample, so their signs are inferred from names; verify when non-zero).
- Holds to +/- 0.001 (1 VND) on every row spot-checked (about 20 rows over 4 files), e.g.
  280 - 0 - 41.244 = 238.756; 190 - 39.2 - 22.213 = 128.587; 465 - 0 - 68.495 = 396.505 vs
  printed 396.506; 85 - 12.521 = 72.479 vs printed 72.48 (Shopee rounds the unrounded value).
- Commission rate: 15% (2024-11 .. 2025-04), 14.73% (2026-03 .. 2026-07). Read, do not compute.
- No file-level totals exist. Control totals must come from bank receipts or Shopee's
  merchant portal; within the file, only per-row identity can be checked.

## 5. Cancellations / refunds / ads

- No status column; header text says "hoàn thành/ huỷ" but every sampled row is a normal
  positive completed order. No negative rows, no ads lines, no adjustment lines seen.
- Parser: reject rows where L > F or any amount is negative, and log them for review.

## 6. IDs and uniqueness

- `Mã Đơn Hàng` is the stable unique ID. Shape `DDMMY-NNNNNNNNN`: first 4 digits = day and
  month, 5th = last digit of year (`27076` = 27-07-2026, `25114` = 25-11-2024), then 9 digits.
- Dedup key: `("SHOPEEFOOD", Mã Đơn Hàng)`. Store ID is an attribute, not part of the key.
- Year digit wraps every 10 years; derive the date from column E, not from the code.

## 7. Quirks

1. Thousand-VND unit with comma decimal (the "82.488" issue) - see section 3.
2. Merchant-level files mix TCV and NVT; folder name is wrong for NVT rows.
3. Two schemas (11 vs 12 columns); match by header names.
4. Times not sorted; codes are sorted.
5. Drive file size metadata (1024) is not row count; small files still contain data.
6. Store ID is numeric, keep as text to avoid int/float drift in sheets.

## 8. Fixture (anonymized; as exported by Drive CSV, vi-VN decimals)

```csv
STT,Mã Đơn Hàng,ID cửa hàng,Tên cửa hàng,Thời gian hoàn thành/ huỷ đơn,Giá trị đơn hàng,Khuyến mại từ quán,Phí dịch vụ,Phí vận chuyển trả cho quán,Chiết khấu,Thuế khấu trừ,Thực thu
1,28036-100000001,10322362,The Vagabond Pâtisserie & Café - Trần Cao Vân,28/03/2026 09:31:10,140,60,0,0,"11,784",0,"68,216"
2,28036-100000002,10322362,The Vagabond Pâtisserie & Café - Trần Cao Vân,28/03/2026 10:43:38,315,"115,25",0,0,"29,423",0,"170,327"
3,28036-100000003,10332477,The Vagabond Pâtisserie & Café - Nguyễn Văn Trỗi,28/03/2026 11:42:39,100,15,0,0,"12,521",0,"72,48"
4,28036-100000004,10332477,The Vagabond Pâtisserie & Café - Nguyễn Văn Trỗi,28/03/2026 11:22:34,355,"87,25",0,0,"39,44",0,"228,31"
```
Expected VND after parsing row 3: gross 100000, promo 15000, commission 12521, net 72480.

Old schema fixture (11 cols):
```csv
STT,Mã Đơn Hàng,ID cửa hàng,Tên cửa hàng,Thời gian hoàn thành/ huỷ đơn,Giá trị đơn hàng,Khuyến mại từ quán,Phí dịch vụ,Phí vận chuyển trả cho quán,Chiết khấu,Thực thu
1,25114-100000001,10322362,The Vagabond Pâtisserie & Café - Trần Cao Vân,25/11/2024 11:36:32,60,11,0,0,"7,35","41,65"
2,25114-100000002,10322362,The Vagabond Pâtisserie & Café - Trần Cao Vân,25/11/2024 20:04:48,160,0,0,0,24,136
```

=================== the_tin_dung_shinhan.md
# Thẻ tín dụng Shinhan - sao kê tháng (PDF)

Nguồn: Drive `10_Thẻ Tín Dụng Shinhan`: 2 PDF (`sao ke thang 06 2026 shinhan.pdf`, `sao ke thang 07 2026 shinhan.pdf`), đã tải và chạy pdfplumber cả hai. Sheet `VGB - PHÍ THẺ SHINHAN 2026 (Auto)` mô tả ở cuối: nó KHÔNG theo dõi thẻ tín dụng này.

## Tệp và kỳ
- Tên do người dùng đặt: `sao ke thang MM YYYY shinhan.pdf`. Không tin tên tệp, lấy kỳ trong PDF.
- PDF 1 trang A4 (595 x 842 pt), có lớp chữ (không cần OCR), Producer `iText 4.2.0 by 1T3XT`.
- Kỳ: `Chu kỳ sao kê 01/06/2026 ~ 30/06/2026` (tháng 7: `01/07/2026 ~ 30/07/2026`). `Ngày sao kê` 01/07/2026 và 31/07/2026 (không cố định ngày), `Ngày đến hạn thanh toán` 15 tháng sau.
- Giao dịch thuộc kỳ theo NGÀY BÚT TOÁN, không theo ngày giao dịch: giao dịch 29-06 hạch toán 01-07 nằm ở sao kê tháng 7.

## Định danh tài khoản
- `Tên khách hàng : BAN GIAM DOC` (tên đăng ký), `Tài khoản thanh toán : 700******585` (ngân hàng đã che giữa).
- Dòng đầu mỗi thẻ trong bảng chi tiết: `Card Number 5xxx-xxXX-XXXX-<4 số cuối>` + tên chủ thẻ in hoa (bị ngắt 2 dòng). Khóa thẻ: 4 số cuối. Mẫu chỉ có 1 thẻ; có thể có thẻ phụ (khối Card Number thứ 2), parser phải lặp theo khối.

## Bố cục pdfplumber
`page.extract_tables()` trả đúng 4 bảng (thứ tự cố định):
1. Thông tin khách: 2 dòng 1 cột `Tên khách hàng : ...`, `Tài khoản thanh toán : ...` (tách bằng ` : `).
2. `Yêu cầu thông tin` 4 cột:
   - `['Ngày sao kê', 'dd/mm/yyyy', 'Ngày đến hạn thanh toán', 'dd/mm/yyyy']`
   - `['Chu kỳ sao kê', 'dd/mm/yyyy ~ dd/mm/yyyy', None, None]`
   - `['Khoản tiền chưa thanh toán\ntháng trước', 'VND 0.00', 'Phí chậm trả', 'VND 0.00']`
   - `['Đến hạn thanh toán của\ntháng này', 'VND 38,384,995.00', None, None]`
   - `['Đến hạn thanh toán', 'VND 38,384,995.00', None, None]`
3. Điểm thưởng (`Tên điểm thưởng`, `Ưu đãi hiện có`, `Điểm tích lũy`, `Điểm thưởng`): bỏ qua cho kế toán.
4. `Chi tiết sao kê`, 6 cột, tiêu đề chính xác: `Ngày giao\n&#x0A;dịch` (có chuỗi rác `&#x0A;` thật trong PDF), `Ngày bút toán`, `Đơn vị chấp nhận thẻ`, `Quốc gia/ Thành\nphố`, `Số tiền gốc`, `Số tiền(VND)`.
   - Dòng `['Card','Number','<số thẻ che>','<TÊN CHỦ THẺ>','','']` mở khối thẻ.
   - Dòng giao dịch: `['dd-mm-yyyy','dd-mm-yyyy','<merchant>','<QG/TP>','VND 1,018,559.00','1,018,559']`.
   - Dòng tổng chi tiêu: `['','','Your Spend For This Month','','','38,164,995']`.
   - Dòng phí: `['15-05-2026','30-06-2026','Annual Fee','','VND 200,000.00','220,000']` rồi `['','','Fees','','','220,000']`.
   - Dòng cuối: `['','','Billing Amount of the Current Month','','','38,384,995']`.
- Dự phòng khi extract_tables lỗi: `extract_words()` gom theo `top`; cột x0 xấp xỉ: ngày GD 32, ngày bút toán 92, merchant 145, quốc gia 356-377 (căn phải), số tiền gốc 434-465, số tiền VND 531-542 (căn phải). Regex dòng: `^(\d{2}-\d{2}-\d{4}) (\d{2}-\d{2}-\d{4}) (.+?) ([A-Z]{2}/\S.*?) ([A-Z]{3}) ([\d,]+\.\d{2}) ([\d,]+)$` (khớp cả 11 dòng giao dịch mẫu). Dòng phí KHÔNG có cột quốc gia nên cần regex riêng: `^(\d{2}-\d{2}-\d{4}) (\d{2}-\d{2}-\d{4}) (.+?) ([A-Z]{3}) ([\d,]+\.\d{2}) ([\d,]+)$` và chỉ áp dụng cho dòng nằm sau `Your Spend For This Month`.
- Chân trang `- 1 / 1 -`.

## Cột chi tiết
| Cột | Ý nghĩa | Kiểu / ví dụ |
|---|---|---|
| Ngày giao dịch | ngày quẹt | `dd-mm-yyyy` |
| Ngày bút toán | ngày ngân hàng ghi nợ (quyết định kỳ) | `dd-mm-yyyy`, thường T+1 đến T+4 |
| Đơn vị chấp nhận thẻ | merchant | "FACEBK *5G2YEURPJ2", "ZaloPay*ZALOBUSINESSSO", "Annual Fee" |
| Quốc gia/ Thành phố | mã nước + thành phố bị cắt | "VN/HO CHI MIN", "IE/DUBLI", "IE/fb.me/ad" |
| Số tiền gốc | `<mã tiền> <số 2 lẻ>` | "VND 16,500,000.00" (giao dịch ngoại tệ sẽ có mã khác VND; chưa gặp) |
| Số tiền(VND) | số ghi nợ VND, không lẻ | "16,500,000" |

## Phương trình và số kiểm soát (đã kiểm 2 kỳ)
- `Your Spend For This Month = tổng Số tiền(VND) các dòng giao dịch` (38,164,995; 52,345,037).
- `Fees = tổng dòng phí`; `Billing Amount of the Current Month = Spend + Fees` (38,164,995 + 220,000 = 38,384,995).
- `Đến hạn thanh toán của tháng này = Billing Amount of the Current Month`.
- `Đến hạn thanh toán = Khoản tiền chưa thanh toán tháng trước + Phí chậm trả + Đến hạn thanh toán của tháng này`.
- Phí thường niên: Số tiền gốc 200,000 nhưng ghi nợ 220,000 = gồm VAT 10%.

## Ánh xạ quy tắc nghiệp vụ (đầu kỳ + phát sinh - thanh toán/hoàn = cuối kỳ)
- Cuối kỳ (closing) = `Đến hạn thanh toán`.
- Phát sinh nợ (charges) = Spend; phí = Fees; lãi: chưa thấy dòng nào (nếu có sẽ là dòng phí kiểu `Interest`, cần dò theo cột ngày trống/merchant không phải đơn vị bán); phí chậm trả = ô `Phí chậm trả`.
- Đầu kỳ (opening) và thanh toán (payments) KHÔNG in riêng. Sao kê chỉ in `Khoản tiền chưa thanh toán tháng trước` = đầu kỳ - các khoản đã trả trước ngày sao kê. Vì vậy:
  - opening = `Đến hạn thanh toán` của sao kê kỳ trước (phải nối chuỗi sao kê);
  - payments trong kỳ = opening - `Khoản tiền chưa thanh toán tháng trước` (kỳ 7: 38,384,995 - 0 = 38,384,995 đã trả cho kỳ 6);
  - kiểm: opening + Spend + Fees + Phí chậm trả - payments = closing.
- Hoàn tiền (refund): chưa gặp; dự kiến là dòng Số tiền âm hoặc có chữ CR, parser phải nhận số âm.
- Thanh toán sau ngày sao kê (từ Ngày sao kê đến Ngày đến hạn): không có trên sao kê này, chỉ lộ ra ở sao kê sau qua ô `Khoản tiền chưa thanh toán tháng trước`. Đối chiếu bằng sao kê ngân hàng tài khoản trả nợ thẻ (SePay), không đợi sao kê thẻ.

## VAT / hóa đơn
- Không có số HĐĐT. Phí thường niên có VAT 10% (cần HĐ từ Shinhan riêng). FACEBK (Meta Ireland) là nhà cung cấp nước ngoài, không có HĐĐT Việt Nam; chuỗi sau `FACEBK *` có vẻ là mã biên lai quảng cáo Meta (chưa đối chiếu).

## Khóa duy nhất
- Không có mã giao dịch / mã chuẩn chi. Khóa đề xuất: `shb:<4 số cuối>:<ngày GD>:<ngày bút toán>:<merchant>:<Số tiền VND>:<thứ tự trùng>`. Hai dòng FACEBK cùng 16,500,000 khác nhau nhờ mã sau `*`.

## Gắn giao dịch với mục đích
- Chỉ có merchant + quốc gia: FACEBK = quảng cáo (marketing), nhà hàng = tiếp khách, chợ/siêu thị = nguyên liệu, ZaloPay = dịch vụ Zalo. Không có ghi chú, cost center. Cần bảng quy tắc merchant -> tài khoản chi phí.

## Quirk
- Header có chuỗi `&#x0A;` (HTML entity không giải mã).
- Thành phố bị cắt ở ~11 ký tự.
- Ngày sao kê và cuối chu kỳ lệch nhau (30/06 vs 01/07; 30/07 vs 31/07).
- Dòng phí có Ngày giao dịch là ngày kỷ niệm thẻ, cách xa kỳ.

## Sheet `VGB - PHÍ THẺ SHINHAN 2026 (Auto)` (cách kế toán làm hiện nay)
Đây là sheet theo dõi phí CHẤP NHẬN THẺ (POS Shinhan ở cửa hàng, khách quẹt thẻ), không phải nợ thẻ tín dụng công ty. 5 tab:
- `Tổng hợp`: bảng điều khiển có bộ lọc (Năm, Kỳ Tháng/Quý/Năm/Tùy chọn, Từ ngày, Đến ngày, Cửa hàng) và số: Tổng số giao dịch, Tổng doanh thu bán, Tổng phí NH, Tổng tiền về, Phí hiệu dụng (%); phân tích theo cửa hàng và theo loại thẻ x kênh.
- `Chi tiết GD`: ghi chú `Tự động cập nhật từ mail Shinhan. Không sửa tay cột KEY.`; tiêu đề dòng 5: `STT | Ngày TT | Ngày GD | Cửa hàng | Số thẻ | Mã chuẩn chi | Loại thẻ | Nội địa/QT | Doanh thu (VND) | Phí NH (VND) | Phí tính (VND) | Tiền về NH (VND) | Lệch phí | MID | KEY`. ~2.640 dòng, `KEY = MID|Mã chuẩn chi|Doanh thu|giờ ngày`. `Tiền về = Doanh thu - Phí NH`; `Lệch phí = Phí tính - Phí NH` (JCB bị thu 2,2% so với biểu 1,44% nên lệch âm). Số kiểu Việt `1.345.000`; Ngày GD `HH:MM:SS dd-mm-yyyy`.
- `Chi tiết lọc`: bản lọc theo tab Tổng hợp, dòng cuối `TỔNG (n GD)`.
- `Cửa hàng`: MID -> cửa hàng có hiệu lực theo thời gian (một MID chuyển từ cửa hàng này sang điểm bán khác vào 17/07/2026 17:40).
- `Bảng phí`: MDR gồm VAT theo Loại thẻ x Kênh (Visa/MasterCard nội địa 1,44%, quốc tế 2,5%; JCB nội địa 1,44%; Napas 0,78%).
=> Hiện chưa có sheet nào trong các nguồn này theo dõi sao kê thẻ tín dụng; parser sao kê là nguồn mới. Có thể dùng lại ý tưởng KEY và cột "lệch" của sheet này.

## Fixture (văn bản extract_text đã ẩn danh)
```text
Sao Kê
Tên khách hàng : BAN GIAM DOC
Tài khoản thanh toán : 700******000
Ngày sao kê 01/07/2026 Ngày đến hạn thanh toán 15/07/2026
Chu kỳ sao kê 01/06/2026 ~ 30/06/2026
Khoản tiền chưa thanh toán
VND 0.00 Phí chậm trả VND 0.00
tháng trước
Đến hạn thanh toán của
VND 2,320,000.00
tháng này
Đến hạn thanh toán VND 2,320,000.00
Chi tiết sao kê
Card Number XXXX-XXXX-XXXX-0000
CARD HOLDER
05-06-2026 08-06-2026 TEST RESTAURANT VN/HO CHI MIN VND 1,000,000.00 1,000,000
19-06-2026 22-06-2026 FACEBK *TESTREF001 IE/fb.me/ad VND 1,100,000.00 1,100,000
Your Spend For This Month 2,100,000
15-05-2026 30-06-2026 Annual Fee VND 200,000.00 220,000
Fees 220,000
Billing Amount of the Current Month 2,320,000
- 1 / 1 -
```

=================== xanh_taxi.md
# Xanh SM (GSM) doanh nghiệp - bảng kê chuyến đi

Nguồn: Drive `09_GreenSM Taxi`: 4 Google Sheets (bảng kê tháng 4, 5, 6, 7/2026) + 1 PDF phụ lục hợp đồng. Đã đọc tháng 4, 5, 7 và PDF.

## Tệp và kỳ
- Tên: `Bảng kê CÔNG TY TNHH PATISSERIE VAGABOND THÁNG <M> <YYYY>` (M không có số 0 đầu).
- Kỳ hợp đồng doanh nghiệp: 26 tháng trước đến 25 tháng này (dòng 3: `Thời gian: Từ 26/03/2026- 25/04/2026`, `Từ 26/06/2026 - 25/07/2026`, khoảng trắng quanh `-` không ổn định).
- Ngoại lệ tháng 5: bảng kê `TRẢ TRƯỚC`, kỳ theo tháng dương lịch (`Thời gian: Từ 01.05-31.05.2026`, dấu chấm).
- 1 sheet `Sheet1`. Dòng 2 tiêu đề, dòng 3 kỳ, dòng 5 tiêu đề cột, dữ liệu từ dòng 6.
- Số là CHUỖI kiểu Việt: `"53.000,00"` (chấm ngăn nghìn, phẩy thập phân, 2 số lẻ). Quãng đường `"2,6"`. Tỷ lệ: `"4.0%"` (T4, dấu chấm!) hoặc `"0,05"` (T7, số thập phân).
- Thời gian: `2026-04-01 21:18:27`, giờ UTC+7 (ghi trong tiêu đề).

## Định danh
- Dòng 2: `BẢNG KÊ CHUYẾN ĐI DOANH NGHIỆP THÁNG 04` / `... THÁNG 07.2026` / `BẢNG KÊ CHUYẾN ĐI TRẢ TRƯỚC THÁNG 05.2026`.
- Cột `Công ty` = `CÔNG TY TNHH PATISSERIE VAGABOND` trên từng dòng. Không có MST, số hợp đồng trong tệp. Hợp đồng: `1032/2026/HĐMB/GSM-VAGABOND` ký 10/03/2026 (bên A: CTCP Di chuyển Xanh và Thông minh GSM, MST 0110269067).
- `Mã thẻ` (16 số, thẻ ảo doanh nghiệp) xác định tài khoản con: 1 thẻ cho Giám đốc, 1 thẻ cho Sale. Che khi lưu/hiển thị.

## Ba bố cục (tiêu đề dòng 5; map theo tên đã upper() và bỏ dấu `'` đầu)
- T5 trả trước (26 cột): STT, Mã đặt chuyến, Công ty, Phòng ban, Mã NV, SĐT gán thẻ, PTTT, Tên khách hàng, SĐT khách hàng, Nguồn, Dịch vụ (M), Điểm đón, Điểm trả, Quãng đường, Bắt đầu (UTC+7), Kết thúc (UTC+7), Ghi chú, Mã chuyến, Mục đích chuyến, Giá cước, Phụ phí, Tổng khuyến mại, Bảo hiểm, Phí Nền tảng, Tổng thanh toán, Số hóa đơn.
- T4 doanh nghiệp (38 cột): STT, Mã đặt chuyến, Công ty, Phòng ban, Mã thẻ, Tên trên thẻ, Mã NV, SĐT gán thẻ, PTTT, Tên khách hàng, SĐT khách hàng, Nguồn, `'Nhóm dịch vụ` (có dấu nháy đơn đầu), Dịch vụ (M), Điểm đón, Điểm trả, Quãng đường, Bắt đầu (UTC+7), Kết thúc (UTC+7), Ghi chú, Mã chuyến, Mục đích chuyến, Giá cước, Phụ phí, Tổng khuyến mại, Mức chiết khấu, Chiết khấu (Doanh nghiệp), Giá cước trước VAT, VAT Giá cước, Phụ phí trước VAT, VAT Phụ phí, Chiết khấu trước VAT, VAT Chiết khấu, Phí Nền tảng, Tổng thanh toán, Bảo hiểm, Lý do lỗi, BKS.
- T7 doanh nghiệp (48 cột, CHỮ HOA): STT ... MỤC ĐÍCH CHUYẾN (như T4 viết hoa), GIÁ CƯỚC, PHỤ PHÍ, TỔNG KHUYẾN MẠI, ĐIỂM VPOINT TIÊU, ĐIỂM VPOINT TIÊU(QUY ĐỔI), PHÍ QUẢN LÝ, MỨC CHIẾT KHẤU, SỐ TIỀN CHIẾT KHẤU, GIÁ CƯỚC TRƯỚC VAT, VAT GIÁ CƯỚC, PHỤ PHÍ TRƯỚC VAT, VAT PHỤ PHÍ, CHIẾT KHẤU/KHUYẾN MẠI TRƯỚC VAT, VAT CHIẾT KHẤU/KHUYẾN MẠI, PHÍ QUẢN LÝ TRƯỚC VAT, VAT PHÍ QUẢN LÝ, `PHÍ NỀN TẢNG trước VAT` (chữ thường lẫn), VAT PHÍ NỀN TẢNG, VPOINT CƯỚC PHÍ TRƯỚC VAT, VAT VPOINT CƯỚC PHÍ, VPOINT PHÍ NỀN TẢNG TRƯỚC VAT, VAT VPOINT PHÍ NỀN TẢNG, TỔNG THANH TOÁN, BẢO HIỂM, GHI CHÚ LÝ DO CÁC CUỐC LỖI, BSX.

## Cột chung
| Cột | Ý nghĩa | Ví dụ ẩn danh |
|---|---|---|
| Mã đặt chuyến | ID chuyến, ULID 26 ký tự | `01KN4PHW53KXBWZMXHW9CTGCK9` |
| Phòng ban | phòng ban gán thẻ | Giám đốc, Sale |
| Mã thẻ / Tên trên thẻ | thẻ ảo DN / tên thẻ | `1000XXXXXXXX2352` / "Sale Admin" |
| Mã NV | trống | |
| SĐT gán thẻ, SĐT khách hàng | SĐT (có hoặc không `+`) | `+8490XXXXXXX` |
| PTTT | VIRTUAL (DN) / INTERNATIONAL_CARD (trả trước) | |
| Tên khách hàng | người đi | "STAFF_A", "The Vagabond" |
| Nguồn | CAR, CAR_PLATFORM, BIKE, EXPRESS (T7 viết thường: Car, Car_platform, Bike, Express) | |
| Nhóm dịch vụ / Dịch vụ (M) | Green SM Express/Limo/Bike/Premium/Car, GF VIP / Green Express, Green Van, Limo - 6 seater... | |
| Điểm đón / Điểm trả | địa chỉ; Điểm trả có tiền tố `(1) ` (thứ tự điểm dừng) | |
| Ghi chú | ghi chú của người đặt cho tài xế | "Lấy bánh ..." |
| Mã chuyến / Mục đích chuyến | mã chi phí, mục đích | luôn trống |
| BKS / BSX | biển số | `50H-XXXXX` |
| Lý do lỗi / GHI CHÚ LÝ DO CÁC CUỐC LỖI | ghi chú điều chỉnh của GSM | "Bổ sung CK tháng 03" |

## Phương trình (đã kiểm)
T4 (104 dòng, 1 dòng điều chỉnh ngoại lệ):
- `Tổng thanh toán = Giá cước + Phụ phí - Tổng khuyến mại - Chiết khấu (Doanh nghiệp)`
- `Chiết khấu (DN) = Mức chiết khấu x (Giá cước + Phụ phí - KM)`; mức 4% (xe GSM vận hành) hoặc 0% (bike, car_platform)
- `Giá cước trước VAT + VAT Giá cước + Phí Nền tảng = Giá cước - Tổng khuyến mại`
- `Phụ phí trước VAT + VAT = Phụ phí`; `Chiết khấu trước VAT + VAT = Chiết khấu (DN)`; VAT 8%.
T7 (497 dòng):
- `TỔNG THANH TOÁN = GIÁ CƯỚC + PHỤ PHÍ - TỔNG KHUYẾN MẠI - SỐ TIỀN CHIẾT KHẤU + (PHÍ QUẢN LÝ TRƯỚC VAT + VAT PHÍ QUẢN LÝ)` (0 sai)
- `PHÍ QUẢN LÝ (tiền) = 0,05 x (GIÁ CƯỚC + PHỤ PHÍ)` tính trên giá TRƯỚC khuyến mại (496/497)
- `GIÁ CƯỚC TRƯỚC VAT + VAT + PHÍ NỀN TẢNG trước VAT + VAT = GIÁ CƯỚC`
- `CHIẾT KHẤU/KHUYẾN MẠI trước VAT + VAT = TỔNG KHUYẾN MẠI + SỐ TIỀN CHIẾT KHẤU`; VAT 8% mọi phần.
T5: `Tổng thanh toán = Giá cước + Phụ phí - Tổng khuyến mại` (ghi rõ ở dòng tổng).

## Dòng tổng / số kiểm soát
- T4, T7: dòng sau dữ liệu (cách 1 dòng trống) có A=`Total`, chỉ điền các cột trước VAT, VAT, Phí nền tảng (`NaN` ở T4) và Tổng thanh toán. Mẫu: T4 = 7.384.600,00 (104 dòng); T7 = 23.834.000,00 (497 dòng).
- T5: A=`TỔNG THANH TOÁN(Giá cước + Phụ phí - Tổng khuyến mại)`, giá trị 150.000,00 ở cột Tổng thanh toán.
- Không có dòng tổng số phải trả sau cọc / hạn mức. PDF phụ lục 02 (18/07/2026): hạn mức kỳ 30.000.000 VNĐ, cọc 15.000.000 VNĐ, khuyến mãi theo mức chi tiêu 5% đến 10%.

## Đơn vị, VAT, HĐĐT
- Đơn vị VND (không ghi trong tệp; suy ra từ hợp đồng và độ lớn số).
- VAT 8% tách theo cấu phần. Số hóa đơn: CHỈ có ở T5 (`Số hóa đơn` = `C26TBC#00014389`, dạng `<ký hiệu>#<số 8 chữ số>`, một HĐ cho cả 3 chuyến). T4, T7 không có số HĐ: GSM xuất HĐ gộp cho kỳ, phải lấy từ m-invoice.

## Khóa duy nhất
- `Mã đặt chuyến` duy nhất trong tệp (104/104, 497/497, 3/3).
- Dòng điều chỉnh có thể mang Mã đặt chuyến của kỳ TRƯỚC (T4 có chuyến ngày 24/03/2026, Giá cước 0, Tổng TT -4.080, lý do "Bổ sung CK tháng 03"). Khóa đề xuất: `gsm:<Mã đặt chuyến>:<kỳ>` hoặc tách loại dòng `adjustment` khi Giá cước = 0 và Tổng TT âm.

## Gắn chuyến với mục đích / người / đơn
- Phòng ban + Tên trên thẻ + Tên khách hàng (Sale = giao bánh/đi việc bán hàng; Giám đốc = đi lại).
- Nguồn = EXPRESS / Green Express = giao hàng; Ghi chú có thể chứa mô tả hàng.
- Điểm trả + Bắt đầu/Kết thúc (có giờ) để khớp đơn bán.
- `Mã chuyến` và `Mục đích chuyến` có sẵn nhưng trống: nên yêu cầu người đặt nhập mã đơn.

## Quirk
- 3 bố cục trong 4 tháng; tiêu đề đổi hoa/thường, `'Nhóm dịch vụ` có nháy, `PHÍ NỀN TẢNG trước VAT` lẫn hoa thường.
- Số định dạng Việt `1.234,56` nhưng tỷ lệ T4 lại `4.0%` (dấu chấm thập phân).
- Tiền có phần lẻ (17.153,70): làm tròn chỉ ở tổng.
- `Phí Nền tảng` T4 = `NaN` ở dòng Total.
- SĐT lúc có `+84`, lúc `84`.
- Chuyến trả trước (T5) trả bằng thẻ quốc tế cá nhân, không qua công nợ DN.

## Fixture (bố cục T7, CSV, đã ẩn danh)
```csv
STT,MÃ ĐẶT CHUYẾN,CÔNG TY,PHÒNG BAN,MÃ THẺ,TÊN TRÊN THẺ,MÃ NV,SĐT GÁN THẺ,PTTT,TÊN KHÁCH HÀNG,SĐT KHÁCH HÀNG,NGUỒN,NHÓM DỊCH VỤ,DỊCH VỤ (M),ĐIỂM ĐÓN,ĐIỂM TRẢ,QUÃNG ĐƯỜNG,BẮT ĐẦU (UTC+7),KẾT THÚC (UTC+7),GHI CHÚ,MÃ CHUYẾN,MỤC ĐÍCH CHUYẾN,GIÁ CƯỚC,PHỤ PHÍ,TỔNG KHUYẾN MẠI,ĐIỂM VPOINT TIÊU,ĐIỂM VPOINT TIÊU(QUY ĐỔI),PHÍ QUẢN LÝ,MỨC CHIẾT KHẤU,SỐ TIỀN CHIẾT KHẤU,GIÁ CƯỚC TRƯỚC VAT,VAT GIÁ CƯỚC,PHỤ PHÍ TRƯỚC VAT,VAT PHỤ PHÍ,CHIẾT KHẤU/KHUYẾN MẠI TRƯỚC VAT,VAT CHIẾT KHẤU/KHUYẾN MẠI,PHÍ QUẢN LÝ TRƯỚC VAT,VAT PHÍ QUẢN LÝ,PHÍ NỀN TẢNG trước VAT,VAT PHÍ NỀN TẢNG,VPOINT CƯỚC PHÍ TRƯỚC VAT,VAT VPOINT CƯỚC PHÍ,VPOINT PHÍ NỀN TẢNG TRƯỚC VAT,VAT VPOINT PHÍ NỀN TẢNG,TỔNG THANH TOÁN,BẢO HIỂM,GHI CHÚ LÝ DO CÁC CUỐC LỖI,BSX
1,01TESTULID00000000000000A1,CÔNG TY TNHH PATISSERIE VAGABOND,Sale,1000XXXXXXXX9785,Sale Admin,,+8477XXXXXXX,VIRTUAL,The Vagabond,+8477XXXXXXX,Express,Green SM Express,Green Express,KITCHEN_ADDR,(1) CUSTOMER_ADDR,"6,81",2026-06-26 09:00:50,2026-06-26 09:29:53,,,,"33.000,00","0,00","0,00",0,0,"0,05","0,00","0,00","28.508,33","2.280,67","0,00","0,00","0,00","0,00","1.527,78","122,22","2.047,22","163,78","0,00","0,00","0,00","0,00","34.650,00","0,00",,50X00001
2,01TESTULID00000000000000A2,CÔNG TY TNHH PATISSERIE VAGABOND,Sale,1000XXXXXXXX9785,Sale Admin,,+8477XXXXXXX,VIRTUAL,The Vagabond,+8477XXXXXXX,Express,Green SM Express,Green Express,KITCHEN_ADDR,(1) CUSTOMER_ADDR,"6,82",2026-06-26 09:48:12,2026-06-26 10:13:58,,,,"35.000,00","0,00","6.000,00",0,0,"0,05","0,00","0,00","30.236,11","2.418,89","0,00","0,00","5.555,56","444,44","1.620,37","129,63","2.171,30","173,70","0,00","0,00","0,00","0,00","30.750,00","0,00",,50X00002
Total,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,"58.744,44","4.699,56","0,00","0,00","5.555,56","444,44","3.148,15","251,85","4.218,52","337,48","0,00","0,00","0,00","0,00","65.400,00",,,
```
