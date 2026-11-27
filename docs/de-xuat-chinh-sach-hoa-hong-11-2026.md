# Đề xuất chính sách hoa hồng và thưởng toàn tiệm, máy tự tính

Bản 2, 27/11/2026. Chưa có code. Bản 1 (17/11) nằm ở PR #582, Codex đã rà và chỉ ra 10 điểm; PR đó đã đóng vì nhánh quá cũ, bản này dựng lại trên main. Bàn ở issue #583.

Repo này công khai nên tài liệu không ghi tên người, không ghi lương từng người. Số trong ví dụ là số tròn.

## 1. Tóm tắt cho anh Việt

- **Vấn đề:** hiện chỉ 3 vị trí có hoa hồng (Sales, Quản lý cửa hàng, Marketing), phần lớn là phiếu tự khai: người nhận tự tính bằng Excel, kế toán tính lại tay. Sales và Marketing dùng hai con số doanh thu bánh ổ khác nhau cho cùng một tháng.
- **Việc sẽ làm:** một chính sách cho mọi bộ phận, một nguồn số liệu. Ngày 1 hằng tháng máy tự dựng phiếu KPI cho từng người, đi theo đường duyệt 5 bước đang có. Cuối quý máy tính lại phần của Sales và Marketing trên tổng quý.
- **Kết quả sẽ thấy:** mỗi người mở app thấy số của mình đang chạy trong tháng, kèm từng dòng tính. Kế toán chỉ soát ngoại lệ.
- **Anh đã chốt:** mốc 600 triệu cho Marketing, trần 6 triệu/người/tháng, thưởng mùa vụ riêng, ngày ghi sổ hoá đơn, giờ công theo bảng chấm công bên làm lương (17/11). Ngày 27/11 anh đồng ý 4 điểm mới: quyết toán theo quý, tại bàn tính 10% phần gọi thêm đã trả tiền, mức chuẩn cho bộ phận hỗ trợ, thẻ "D1" trên Pancake.
- **Còn chờ anh:** Q5 danh sách người theo bộ phận, Q6 foodapp (mục 8).

## 2. Bốn nguyên tắc

1. **Trả cho phần làm thêm được**, không trả cho doanh thu vốn đã có.
2. **Không có bậc nhảy, không lợi khi dời đơn.** Tỷ lệ tăng giảm trơn. Mốc tính theo tháng để chi tạm, quyết toán trên tổng quý (mục 3.0). Bảng bậc hiện tại trong `kpi.CAU_HINH_MAC_DINH` có bậc nhảy ở mốc 600 triệu, sẽ thay.
3. **Một trần cho khoản thường, một trần cho mùa vụ.** Mục 3.7.
4. **Luật mới áp từ kỳ sau.** Không sửa phiếu, bảng lương, hoá đơn của kỳ đã chi. Chênh lệch chi bổ sung hoặc trừ ở kỳ sau, có dòng ghi rõ (mục 5, F2).

## 3. Chính sách theo bộ phận

### 3.0 Quyết toán theo quý (Sales và Marketing)

- Mỗi tháng máy tính theo công thức tháng và **chi tạm**.
- Tháng cuối quý máy tính lại công thức trên **tổng doanh thu quý**: mốc quý bằng 3 lần mốc tháng (1,8 tỷ), trần quý bằng 3 lần trần tháng (18 triệu). Phiếu tháng cuối quý = số đúng của quý trừ tổng đã chi tạm hai tháng trước. Âm thì là khoản trừ, đi theo F2 (không trừ lương cứng).
- Marketing: tỷ lệ r của quý tính trên tỷ lệ chi phí quảng cáo cả quý.
- Ví dụ: hai cách bán ra cùng tổng quý 1,9 tỷ.

| | Bán đều 600, 600, 700 | Dời 50 triệu: 650, 550, 700 |
|---|---|---|
| Tạm chi tháng 1, 2, 3 | 0; 0; 3,0 tr | 1,5 tr; 0; 3,0 tr |
| Cộng tạm chi | 3,0 tr | 4,5 tr |
| Đúng theo quý: 3% x (1,9 tỷ trừ 1,8 tỷ) | 3,0 tr | 3,0 tr |
| Phiếu tháng 3 | 3,0 tr | 1,5 tr |

- Quý đầu tiên áp: tháng 1 đến 3/2027. Tháng 12/2026 chạy theo tháng như cũ.
- Người nghỉ giữa quý: quyết toán tới tháng cuối đã làm đủ, không đòi lại phần tạm chi đã nhận (giống F6).

### 3.1 Sales (đặt bánh online)

- Hoa hồng tháng = 3% x (doanh thu bánh ổ online trừ 600 triệu). Không âm. Quyết toán quý theo 3.0.
- Bánh ổ online = dòng hàng nhóm "Bánh ổ sinh nhật" trên hoá đơn đơn Pancake đã ghi sổ, trừ hàng tặng, trừ đơn của D1 (mục 3.8).
- Bán kèm: 5% trên phần món bán kèm trong đơn có bánh ổ (bánh nướng, hộp quà, nến, phụ kiện). Không tính phí giao.
- Mùa vụ: 0,3% doanh thu nhóm bánh theo mùa (Trung thu, Giáng sinh, Tết). Tính riêng, có trần riêng (3.7), nên tháng 12 vẫn có phần mùa vụ dù bánh ổ không qua mốc.

### 3.2 Marketing

- Hoa hồng bánh ổ = r x (doanh thu bánh ổ toàn bộ, cả online và D1, trừ 600 triệu). Không âm. Quyết toán quý theo 3.0.
- r theo tỷ lệ chi phí quảng cáo trên doanh thu bánh ổ: từ 10% trở xuống r = 1,5%; từ 10% đến 15% giảm đều về 0,75%; trên 15% r = 0,75%.
- **Chi phí quảng cáo tính theo ngày quảng cáo chạy thật** (báo cáo theo ngày của nền tảng), không theo ngày xuất hoá đơn hay ngày nạp tiền. Dời ngày thanh toán không đổi được r.
- **Chi phí dùng chung phải chia trước.** Chiến dịch chạy cho cả bánh ổ và bánh mùa vụ thì ghi tỷ lệ chia lúc tạo chiến dịch; không sửa tỷ lệ sau khi chiến dịch đã chạy. Chiến dịch không ghi tỷ lệ thì tính cả vào bánh ổ.
- Chi quảng cáo trên 100 triệu/tháng phải xin giám đốc duyệt trước, kèm ngân sách và mục tiêu. **Đã duyệt vẫn tính vào tỷ lệ chi phí.** Bản 1 có ngoại lệ "khoản đã duyệt không làm giảm r", bỏ vì nó thưởng cho việc xin loại chi phí ra khỏi phép tính.
- Foodapp giữ bảng hiện tại: tỷ lệ 1%, 0,6%, 0,3%, 0 theo chi phí khuyến mãi app (dưới 15%, 15 đến 18%, 18 đến 21%, trên 21%), điều kiện huỷ đơn từ 3% trở xuống và điểm đánh giá từ 4,7. Xem Q6.
- Mùa vụ 0,3% như Sales.

### 3.3 Quản lý cửa hàng

- 5% doanh thu đơn bánh ổ của D1 (đơn có thẻ "D1", mục 3.8), cộng 1% phần doanh thu Shopee vượt chỉ tiêu tháng.

### 3.4 Nhân viên quầy và bar

**Mã giới thiệu đơn bánh ổ D1:** nhân viên nhập số điện thoại của mình vào ô Mã giới thiệu, nhận 2% tiền hàng. Đã có (`gioi_thieu.py`).

**Thưởng gọi thêm tại bàn (đổi so với bản 1, anh chốt 27/11):**
- Thưởng = **10% tiền hàng của các lượt gọi thêm** (lượt thứ hai trở đi trên cùng bill), **chỉ phần khách đã trả tiền**. Không còn 2% cả bill. Bàn chỉ gọi một lượt thì 0.
- Lượt gọi thêm được tính khi gửi sau lượt trước ít nhất 15 phút. Mỗi bill tối đa 20.000 đ.
- Người nhận: người có số điện thoại ở lượt gọi thêm đó. Lượt không có số thì không ai nhận phần của lượt đó.
- Món quầy bỏ khỏi bill (khách không nhận, không trả) thì không tính. Nhờ vậy nhân viên tự cầm máy quét QR gọi món cũng không ra tiền nếu khách không trả.
- Ví dụ: bàn gọi 300.000 đ, nhân viên mời thêm một Canelé 65.000 đ, khách trả đủ. Bản 1: 2% x 365.000 = 7.300 đ. Bản 2: 10% x 65.000 = 6.500 đ.

**Quỹ đội quầy và bar (đổi so với bản 1):**
- Quỹ tháng của mỗi điểm = 5% x (doanh thu tại chỗ của điểm trong tháng trừ mức nền tháng của điểm). Không âm. Trần 8 triệu/điểm/tháng.
- Doanh thu tại chỗ = hoá đơn đã ghi sổ nguồn Tại chỗ, QR tại bàn, Mang về của điểm, trừ hàng tặng, nội bộ, giảm giá.
- Mức nền ban đầu = bình quân doanh thu tại chỗ tháng 9 đến 11/2026 của điểm. Giám đốc đặt lại mỗi quý, nâng theo đúng mức tăng giá bán. Đổi mức nền áp từ quý sau.
- Gộp hay tách bill không đổi doanh thu, nên không đổi quỹ. Bản 1 tính theo bill bình quân nhân số bill: gộp hai bàn thành một bill làm quỹ tăng, đã bỏ.
- **Huỷ và hoàn tiền giảm quỹ dần, không còn vách 3%:** hệ số quỹ = 1 khi tỷ lệ huỷ hoàn từ 2% trở xuống, giảm đều về 0 ở 6%. Ví dụ 3,2% thì nhận 70% quỹ. Tỷ lệ = tiền hàng huỷ và hoàn trên tổng tiền hàng tại chỗ của điểm đó trong tháng, theo ngày ghi sổ.
- Chia theo giờ công (F11).

**Món chỉ định:** mỗi tháng giám đốc chọn 3 đến 5 món, 3.000 đến 5.000 đ mỗi phần bán ra, ghi theo người bán trên bill.

### 3.5 Bếp

- Quỹ bếp = 0,5% x (doanh thu bánh ổ cộng bánh theo mùa) x hệ số chất lượng.
- Hệ số 1 khi hàng lỗi phải làm lại từ 2% trở xuống VÀ hao hụt trong định mức; 0,5 khi trượt một điều; 0 khi trượt cả hai.
- Bếp trưởng chia theo giờ công.

### 3.6 Kế toán, Thu mua, Thiết kế, Chụp ảnh, Giao hàng (anh chốt 27/11)

- Thưởng hiệu quả = **mức chuẩn** x hệ số xếp loại (`kpi.XEP_LOAI`). Mức chuẩn: nhân viên 1 triệu, người phụ trách 1,5 triệu. Đây là mức chuẩn, không phải trần: xuất sắc được nhiều hơn.

| Xếp loại (điểm) | Hệ số | Nhân viên | Người phụ trách |
|---|---|---|---|
| Xuất sắc (từ 100) | 1,25 | 1.250.000 | 1.875.000 |
| Tốt (85 đến 99) | 1,10 | 1.100.000 | 1.650.000 |
| Đạt (70 đến 84) | 1,00 | 1.000.000 | 1.500.000 |
| Chưa đạt (dưới 70) | 0 | 0 | 0 |

- Người vào giữa tháng tính theo số ngày công. Chi qua khoản "Hiệu quả công việc" có sẵn trong quy chế lương thưởng.
- Tiêu chí ưu tiên cái máy đo được:

| Bộ phận | Máy đo | Quản lý chấm |
|---|---|---|
| Kế toán | Đơn treo cuối kỳ, hoá đơn điện tử xuất đủ đúng hạn, giao dịch ngân hàng chưa khớp | Hồ sơ đủ, tiết kiệm chi phí |
| Thu mua | Phiếu nhận thiếu, giá nhập so bảng giá, đơn trên 10 triệu có 3 báo giá | Không để hết nguyên liệu chính |
| Thiết kế | Món đang bán thiếu ảnh hoặc ấn phẩm trên web | Đúng hạn, đúng nhận diện, số lần sửa |
| Chụp ảnh | Món mới có ảnh trước ngày mở bán | Ảnh dùng được, bộ ảnh mùa vụ đúng lịch |
| Giao hàng | Đơn giao đúng giờ, đơn hỏng, thu tiền đủ | Thái độ, phối hợp |

### 3.7 Thứ tự áp trần (đổi so với bản 1)

1. Tính từng khoản thường của người đó: hoa hồng bánh ổ, foodapp, bán kèm, mã giới thiệu đơn D1, thưởng gọi thêm tại bàn, món chỉ định, phần chia quỹ đội.
2. **Cộng tất cả khoản thường rồi mới chặn ở 6 triệu/tháng** (18 triệu/quý khi quyết toán quý). Hiện `kpi.day_chi` cộng tiền giới thiệu ngoài trần; sẽ đưa vào trong trần.
3. Thưởng mùa vụ tính riêng, **trần 4 triệu/người/mùa** (một mùa có thể trải qua hai tháng, trần tính trên cả mùa).
4. Thưởng hiệu quả bộ phận hỗ trợ (3.6) không thuộc hai trần trên.
5. Phần bị chặn ghi vào sổ vượt trần của người đó để minh bạch. Không tự chi bổ sung; giám đốc có thể duyệt chi thưởng riêng.

### 3.8 Tách đơn D1 (anh chốt 27/11)

- Mã giới thiệu cho biết **ai được thưởng**, không cho biết **nơi nào nhận đơn**. Bản 1 dùng mã giới thiệu làm dấu tách duy nhất, có hai lỗi: nhân viên D1 quên nhập số thì đơn D1 tính cho Sales; khách đặt online dùng số nhân viên D1 thì đơn bị trừ khỏi Sales oan.
- Dấu nơi nhận đơn: **thẻ "D1" trên đơn Pancake**, nhân viên D1 gắn khi tạo đơn bánh ổ ở quầy.
- Máy xếp mỗi đơn bánh ổ Pancake đã ghi sổ:
  - Có thẻ "D1": đơn của D1. Quản lý cửa hàng 5%, nhân viên có số ở Mã giới thiệu 2%. Không vào doanh thu của Sales.
  - Không có thẻ nhưng có dấu hiệu D1 (số nhân viên D1 ở Mã giới thiệu, hoặc tài khoản Pancake của nhân viên D1 tạo đơn): **chờ đối soát**. Không cộng cho ai. Quản lý cửa hàng và Sales xác nhận trong 5 ngày đầu tháng sau; quá hạn thì giám đốc chốt.
  - Không thẻ, không dấu hiệu D1: đơn online, tính cho Sales.
- Marketing tính trên cả hai nhóm nên không bị ảnh hưởng bởi việc xếp.

## 4. Số liệu nền (làm tròn)

- Doanh thu toàn tiệm tháng thường khoảng 2 tỷ: đơn online khoảng 1,1 tỷ, tại quầy khoảng 0,5 tỷ, app giao hàng khoảng 0,45 tỷ.
- Đơn online có hai đỉnh: Trung thu (tháng 9) và Giáng sinh (tháng 12). Tháng 12/2025 gần một nửa doanh thu online là bánh theo mùa, bánh ổ sinh nhật lại thấp hơn tháng thường. Vì vậy cần thưởng mùa vụ riêng.
- Thưởng hiện chiếm khoảng 21% đến 24% tổng thu nhập của 3 vị trí đang có hoa hồng. Chính sách mới giữ mặt bằng này.
- Chi phí dự kiến khoảng 24 triệu tháng thường, 30 triệu tháng 12, tức khoảng 1,1% đến 1,2% doanh thu.

## 5. Luật công bằng và chống lách

| # | Tình huống | Luật |
|---|---|---|
| F1 | Đơn ghi sổ tháng này, giao tháng sau | Tính theo ngày ghi sổ hoá đơn (anh chốt 17/11) |
| F2 | Đơn huỷ hoặc hoàn tiền SAU khi đã chi | Xem F2a đến F2d dưới bảng |
| F3 | Khách đặt bằng chính số của người giới thiệu | Không tính. Đã có (`tu_gioi_thieu`) |
| F4 | Hai nhân viên cùng phục vụ một bàn | Mỗi lượt gọi thêm một người, theo số ở lượt đó. Chỉ quản lý đổi người, có lý do và vết (`doi_nguoi` đã có) |
| F5 | Dời đơn qua tháng để ăn mốc | Quyết toán quý (3.0) |
| F6 | Nhân viên nghỉ việc | Nhận phần đã ghi sổ tới ngày nghỉ. Không đòi lại tạm chi và khoản hoàn về sau |
| F7 | Nhân viên mới, thử việc | Có hoa hồng như nhân viên chính thức. Thưởng hiệu quả tính theo ngày công |
| F8 | Hàng tặng, nội bộ, khách sỉ, hợp đồng B2B | Không vào doanh thu tính hoa hồng |
| F9 | Doanh thu có VAT hay chưa | Mốc đặt theo giá có VAT. Máy đọc giá trị có VAT, trừ giảm giá, trừ phí giao |
| F10 | Giảm giá, điểm thành viên, ưu đãi | Trừ khỏi doanh thu tính hoa hồng (`tien_tinh` đã làm vậy) |
| F11 | Chia quỹ theo giờ công | Giờ công lấy từ bảng chấm công bên làm lương gửi mỗi tháng (anh chốt 17/11) |
| F12 | Một người thuộc hai bộ phận | Mỗi người một phiếu một kỳ. Ghi theo bộ phận chính, dòng phụ cộng vào, chung trần |
| F13 | Minh bạch | Mỗi người xem số của mình đang chạy. Có 5 ngày sau kỳ gửi ý kiến trước khi kế toán soát |
| F14 | Cài đặt sai | Chặn ở ô cài đặt. Đổi cài đặt áp từ kỳ sau (mức nền quỹ đội: từ quý sau) |
| F15 | Tách sẵn giỏ thành hai lượt tại bàn | Lượt sau phải cách 15 phút, tối đa 20.000 đ/bill, chỉ tính phần đã trả |
| F16 | Gộp hoặc tách bill để đổi quỹ đội | Quỹ theo doanh thu, không theo số bill (3.4) |

**F2, thu hồi khi huỷ hoặc hoàn tiền:**
- F2a. Ba trạng thái tách bạch: phiếu **đã duyệt**, **đã đẩy đề nghị chi** (hiện `kpi.day_chi` chỉ tạo nháp đề nghị chi), **đã chi** (kế toán đánh dấu khi bên làm lương đã trả). Đơn hoàn trước khi phiếu đã chi thì tính lại phiếu, không thu hồi.
- F2b. Sau khi đã chi: thu hồi đúng người **đã nhận tiền** của đơn đó, đọc từ dòng phiếu đã chi, không đọc người giới thiệu hiện tại trên hoá đơn (quản lý có thể đã đổi người sau đó).
- F2c. Mỗi đơn hoàn chỉ thu hồi một lần, khoá theo mã đơn và mã phiếu. Hoàn một phần thì thu theo tỷ lệ tiền hoàn.
- F2d. Trừ vào hoa hồng các kỳ sau của người đó, không trừ lương cứng, không trừ âm quá số được nhận kỳ đó. Sau 3 kỳ chưa trừ hết thì giám đốc duyệt xoá phần còn lại.

## 6. Dữ liệu máy cần, đã có hay chưa

| Dữ liệu | Có chưa | Ghi chú |
|---|---|---|
| Dòng hàng theo nhóm món trên hoá đơn đã ghi sổ | Có | Nhóm "Bánh ổ sinh nhật", "Hộp bánh theo mùa" |
| Nguồn đơn (Pancake, Tại chỗ, QR tại bàn, app) | Có | `custom_nguon` |
| Hàng tặng, huỷ, hoàn tiền | Có | `vgb_qua_tang`, `vgb_huy`, phiếu hoàn |
| Người giới thiệu và loại đơn | Có | `vgb_nguoi_gioi_thieu`, `vgb_gt_loai` |
| Lượt gọi của một bàn, giờ gửi, tiền từng lượt | Có, cần đọc | Doctype `Vagabond Goi Mon Ban`, lượt sau cộng vào cùng bill |
| Thẻ "D1" và người tạo đơn trên Pancake | Chưa | Cần tạo thẻ trên Pancake và đồng bộ thẻ, người tạo vào hoá đơn |
| Người bán trên bill quầy | Có ô, ít dùng | `vgb_nguoi_ban`. Khoảng 80% bill một điểm đang chung một tài khoản |
| Chi phí quảng cáo theo ngày chạy | Chưa | Nối Meta Ads (anh tự tạo mã truy cập) hoặc nhập tay kèm báo cáo |
| Giảm giá, huỷ, điểm đánh giá của app | Chưa | Nạp báo cáo cửa hàng của app mỗi tháng |
| Giờ công | Chưa | Nạp bảng chấm công bên làm lương gửi mỗi tháng |
| Hàng lỗi, hao hụt bếp | Một phần | Phiếu huỷ hàng có; định mức hao hụt trên công thức |
| Trạng thái "đã chi" của phiếu | Chưa | Kế toán đánh dấu khi bên làm lương đã trả |

## 7. Phạm vi kỹ thuật dự kiến cho PR sau

- Cài đặt chính sách trong một bản ghi (mốc, tỷ lệ, trần, mức nền quỹ, danh sách bộ phận và người), có ngày hiệu lực.
- Hàm THUẦN cho từng công thức, ca kiểm cho từng luật ở mục 3 và 5: quyết toán quý, trần gộp, hệ số huỷ hoàn, xếp đơn D1, lượt gọi thêm, sổ thu hồi.
- Mỗi tháng máy dựng phiếu cho từng người. Phiếu tự khai giữ làm đường dự phòng.
- Sổ thu hồi và sổ vượt trần theo người.
- Bảng xuất cho bên làm lương lấy từ phiếu đã duyệt.

## 8. Câu hỏi

**Cho anh Việt**
- Đã chốt 17/11: tính theo ngày ghi sổ; giờ công theo bảng chấm công bên làm lương; người nhận tại bàn em quyết.
- Đã chốt 27/11: quyết toán theo quý; tại bàn 10% phần gọi thêm đã trả; mức chuẩn cho bộ phận hỗ trợ; thẻ "D1" trên Pancake, đơn chưa rõ chờ đối soát.
- Q5. Danh sách người theo bộ phận, ai là người phụ trách.
- Q6. Foodapp đổi sang giảm trơn hay giữ bậc như hiện tại?

**Cho Codex, vòng 2.** Bản 1 Codex chỉ ra 10 điểm. Đối chiếu:

| Góp ý bản 1 | Sửa ở |
|---|---|
| Dời đơn qua tháng quanh mốc 600 triệu | 3.0, F5 |
| Quỹ đội tăng khi gộp bill | 3.4 quỹ đội, F16 |
| Tách giỏ hai lượt để ăn 2% cả bill | 3.4 gọi thêm, F15 |
| C1 "mức tối đa" nhân 1,25 vượt tối đa | 3.6 đổi thành mức chuẩn |
| C2 dời chi phí quảng cáo, ngoại lệ đã duyệt | 3.2 |
| C3 nhân viên tự quét QR | 3.4: chỉ tính phần khách đã trả |
| C4 vách huỷ hoàn 3% | 3.4 hệ số giảm dần, định nghĩa tỷ lệ |
| C5 thu hồi sai người, khoản treo | F2a đến F2d |
| C6 thứ tự trần, giới thiệu ngoài trần | 3.7 |
| C7 mã giới thiệu không chứng minh nơi nhận đơn | 3.8 |

Nhờ rà: các luật mới có tạo kẽ hở mới nào không, nhất là quyết toán quý khi người đổi bộ phận giữa quý, mức nền quỹ đội, và trạng thái chờ đối soát của đơn D1.
