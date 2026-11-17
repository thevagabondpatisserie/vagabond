# Đề xuất chính sách hoa hồng và thưởng toàn tiệm, máy tự tính

Bản bàn trước khi làm, 17/11/2026. Chưa có code. Mục đích: soát cho thật kỹ luật tính trước khi viết PR, vì hoa hồng đụng tới sự công bằng giữa nhân viên.

Repo này công khai nên tài liệu không ghi tên người, không ghi lương từng người. Số liệu dùng làm ví dụ đã làm tròn.

## 1. Tóm tắt cho anh Việt

- **Vấn đề:** hiện chỉ 3 vị trí có hoa hồng (Sales, Quản lý cửa hàng, Marketing), và phần lớn là phiếu tự khai: người nhận tự tính bằng Excel, kế toán tính lại tay. Có tháng số trên phiếu và số chi trong bảng lương lệch nhau. Sales và Marketing đang dùng hai con số doanh thu bánh ổ khác nhau cho cùng một tháng.
- **Việc sẽ làm:** một chính sách cho mọi bộ phận, một nguồn số liệu. Ngày 1 hằng tháng máy tự dựng phiếu KPI cho từng người. Phiếu đi theo đường duyệt 5 bước đang có. Bảng gửi bên làm lương lấy từ phiếu đã duyệt.
- **Kết quả sẽ thấy:** mỗi người mở app thấy số của mình đang chạy trong tháng, kèm từng dòng tính. Kế toán chỉ soát ngoại lệ.
- **Anh cần quyết:** các câu ở mục 8. Anh đã chọn: mốc 600 triệu cho Marketing, trần 6 triệu/người/tháng, thưởng mùa vụ riêng, hoa hồng tại bàn theo phương án A (chỉ khi bàn có gọi thêm).

## 2. Bốn nguyên tắc

1. **Trả cho phần làm thêm được**, không trả cho doanh thu vốn đã có.
2. **Không có bậc nhảy.** Tỷ lệ tăng giảm trơn. Không ai lợi khi dồn đơn qua tháng. Bảng bậc hiện tại trong `kpi.CAU_HINH_MAC_DINH` có bậc nhảy ở mốc 600 triệu (màn KPI đang tự cảnh báo điều này), sẽ thay.
3. **Trần 6 triệu/người/tháng** cho hoa hồng tháng. Phần vượt trần dồn vào thưởng quý. Thưởng mùa vụ có trần riêng.
4. **Luật mới áp từ kỳ sau.** Không sửa phiếu, bảng lương, hoá đơn của kỳ đã chi. Chênh lệch phát sinh thì chi bổ sung ở kỳ sau, có dòng ghi rõ.

## 3. Chính sách theo bộ phận

### 3.1 Sales (đặt bánh online)
- Hoa hồng = 3% x (doanh thu bánh ổ online trong tháng trừ 600 triệu). Không âm. Trần 6 triệu, tức chạm trần ở 800 triệu.
- Bánh ổ online = dòng hàng nhóm "Bánh ổ sinh nhật" trên hoá đơn đơn Pancake đã ghi sổ, trừ hàng tặng, trừ đơn có người giới thiệu là nhân viên cửa hàng D1. Hiện chưa có dấu nào khác để tách đơn D1 (anh Việt xác nhận 17/11). Từ nay nhân viên D1 nhập số điện thoại của mình vào ô Mã giới thiệu khi nhận đơn bánh ổ, đó là dấu tách duy nhất.
- Thưởng bán kèm: 5% trên phần món bán kèm trong đơn có bánh ổ (bánh nướng, hộp quà, nến, phụ kiện). Không tính phí giao. Nâng size bánh đã nằm trong 3% bánh ổ.
- Thưởng mùa vụ: 0,3% doanh thu nhóm bánh theo mùa (Trung thu, Giáng sinh, Tết).

### 3.2 Marketing
- Hoa hồng bánh ổ = r x (doanh thu bánh ổ toàn bộ, cả online và D1, trừ 600 triệu). Không âm.
- r theo tỷ lệ chi phí quảng cáo trên doanh thu bánh ổ: từ 10% trở xuống thì r = 1,5%; từ 10% đến 15% giảm đều về 0,75%; trên 15% thì r = 0,75%.
- Chi quảng cáo trên 100 triệu/tháng phải xin giám đốc duyệt trước. Khoản đã duyệt không làm giảm r.
- Foodapp giữ bảng hiện tại: tỷ lệ 1%, 0,6%, 0,3%, 0 theo chi phí khuyến mãi app (dưới 15%, 15 đến 18%, 18 đến 21%, trên 21%), điều kiện huỷ đơn từ 3% trở xuống và điểm đánh giá từ 4,7. Sẽ đổi thành giảm trơn như phần bánh ổ, xem Q6.
- Thưởng mùa vụ 0,3% như Sales.
- Trần 6 triệu cho tổng hoa hồng tháng (bánh ổ cộng foodapp).

### 3.3 Quản lý cửa hàng
- Giữ cách hiện tại: 5% doanh thu đơn bánh ổ D1, cộng 1% phần doanh thu Shopee vượt chỉ tiêu tháng.

### 3.4 Nhân viên quầy và bar
- **Mã giới thiệu đơn bánh ổ D1:** nhân viên nhập số điện thoại của mình vào ô Mã giới thiệu, nhận 2% tiền hàng. Đã có (`gioi_thieu.py`).
- **Mã giới thiệu tại bàn, phương án A (anh đã chọn):** 2% tiền hàng cả bill, CHỈ khi bàn có lượt gọi thêm hợp lệ từ lượt thứ hai trở đi. Bàn chỉ gọi một lượt thì 0. Hiện máy tính 2% ngay từ lượt đầu, sẽ đổi.
- Lượt gọi thêm hợp lệ (đề xuất mặc định, chờ Codex soát ở C3): tiền hàng của lượt từ 30.000 đ trở lên, và gửi sau lượt trước ít nhất 10 phút. Mục đích: không tách một lượt thành hai để ăn 2% cả bill.
- Người nhận: người có số điện thoại ở lượt gọi thêm hợp lệ ĐẦU TIÊN. Lượt thêm không có số thì người nhập số ở lượt đầu nhận. Lý do: thưởng cho người tạo ra phần bán thêm.
- **Quỹ đội quầy và bar:** quỹ tháng = 10% x (bill bình quân thực tế trừ mốc nền) x số bill. Mốc nền ban đầu TCV 225.000 đ, NVHTN 90.000 đ. Trần 8 triệu/điểm/tháng. Chia theo giờ công. Điều kiện: huỷ và hoàn tiền từ 3% trở xuống. Đổi giá bán thì nâng mốc nền theo đúng mức tăng giá.
- **Món chỉ định:** mỗi tháng giám đốc chọn 3 đến 5 món, 3.000 đến 5.000 đ mỗi phần bán ra, ghi theo người bán trên bill.

### 3.5 Bếp
- Quỹ bếp = 0,5% x (doanh thu bánh ổ cộng bánh theo mùa) x hệ số chất lượng.
- Hệ số 1 khi hàng lỗi phải làm lại từ 2% trở xuống VÀ hao hụt trong định mức; 0,5 khi trượt một điều; 0 khi trượt cả hai.
- Bếp trưởng chia theo giờ công.

### 3.6 Kế toán, Thu mua, Thiết kế, Chụp ảnh, Giao hàng
- Thưởng hiệu quả = mức tối đa x hệ số xếp loại (`kpi.XEP_LOAI`: 1,25 / 1,10 / 1,00 / 0).
- Mức tối đa: nhân viên 1 triệu, người phụ trách 1,5 triệu. Chi qua khoản "Hiệu quả công việc" có sẵn trong quy chế lương thưởng của công ty.
- Tiêu chí ưu tiên cái máy đo được:

| Bộ phận | Máy đo | Quản lý chấm |
|---|---|---|
| Kế toán | Đơn treo cuối kỳ, hoá đơn điện tử xuất đủ đúng hạn, giao dịch ngân hàng chưa khớp | Hồ sơ đủ, tiết kiệm chi phí |
| Thu mua | Phiếu nhận thiếu, giá nhập so bảng giá, đơn trên 10 triệu có 3 báo giá | Không để hết nguyên liệu chính |
| Thiết kế | Món đang bán thiếu ảnh hoặc ấn phẩm trên web | Đúng hạn, đúng nhận diện, số lần sửa |
| Chụp ảnh | Món mới có ảnh trước ngày mở bán | Ảnh dùng được, bộ ảnh mùa vụ đúng lịch |
| Giao hàng | Đơn giao đúng giờ, đơn hỏng, thu tiền đủ | Thái độ, phối hợp |

## 4. Số liệu nền (làm tròn)

- Doanh thu toàn tiệm tháng thường khoảng 2 tỷ: đơn online khoảng 1,1 tỷ, tại quầy khoảng 0,5 tỷ, app giao hàng khoảng 0,45 tỷ.
- Đơn online có hai đỉnh: Trung thu (tháng 9) và Giáng sinh (tháng 12). Tháng 12/2025 gần một nửa doanh thu online là bánh theo mùa, bánh ổ sinh nhật lại thấp hơn tháng thường. Vì vậy cần thưởng mùa vụ riêng, nếu không thì tháng bận nhất Sales gần như không có hoa hồng.
- Hiện thưởng chiếm khoảng 21% đến 24% tổng thu nhập của 3 vị trí đang có hoa hồng. Khoảng 15% đến 30% là hợp lý cho bán hàng. Chính sách mới giữ mặt bằng này.
- Chi phí dự kiến khoảng 24 triệu tháng thường, 30 triệu tháng 12, tức khoảng 1,1% đến 1,2% doanh thu.

## 5. Luật công bằng và chống lách (cần soát kỹ nhất)

| # | Tình huống | Luật đề xuất |
|---|---|---|
| F1 | Đơn ghi sổ tháng này, giao tháng sau | Tính theo ngày ghi sổ hoá đơn (anh Việt chốt 17/11) |
| F2 | Đơn huỷ hoặc hoàn tiền SAU khi phiếu tháng đã chi | Không sửa kỳ đã chi. Trừ vào kỳ kế tiếp của đúng người đó, có dòng ghi mã đơn. Không trừ âm quá số được nhận kỳ đó, phần còn lại chuyển tiếp |
| F3 | Khách đặt bằng chính số của người giới thiệu | Không tính. Đã có (`tu_gioi_thieu`) |
| F4 | Hai nhân viên cùng phục vụ một bàn | Một bill một người. Số nhập đầu tiên được giữ, trừ lượt gọi thêm ở F5. Chỉ quản lý đổi, có lý do và vết (`doi_nguoi` đã có) |
| F5 | Người khác mời lượt gọi thêm, không phải người nhập số lượt đầu | Người có số ở lượt gọi thêm hợp lệ đầu tiên nhận (mục 3.4). Anh Việt giao em quyết, 17/11 |
| F6 | Nhân viên nghỉ việc giữa tháng | Nhận hoa hồng phần đơn đã ghi sổ tới ngày nghỉ. Trừ hoàn tiền về sau không đòi lại |
| F7 | Nhân viên mới, thử việc | Có hoa hồng như nhân viên chính thức. Thưởng hiệu quả bộ phận hỗ trợ tính theo số ngày công |
| F8 | Hàng tặng, nội bộ, đơn khách sỉ, hợp đồng B2B | Không vào doanh thu tính hoa hồng |
| F9 | Doanh thu có VAT hay chưa VAT | Các mốc 600 và 800 triệu đặt theo giá có VAT. Máy đọc giá trị có VAT, trừ giảm giá, trừ phí giao |
| F10 | Giảm giá, điểm thành viên, ưu đãi | Trừ khỏi doanh thu tính hoa hồng (`tien_tinh` đã làm vậy) |
| F11 | Quỹ đội chia theo giờ công | Giờ công lấy từ bảng chấm công bên làm lương gửi mỗi tháng (anh Việt chốt 17/11). Chấm công trên ERP làm sau |
| F12 | Một người thuộc hai bộ phận trong tháng | Mỗi người một phiếu một kỳ. Ghi theo bộ phận chính, dòng phụ cộng vào |
| F13 | Minh bạch | Mỗi người xem số của mình đang chạy trong tháng. Có 5 ngày sau kỳ để gửi ý kiến trước khi kế toán soát |
| F14 | Cài đặt sai (mốc, tỷ lệ gõ nhầm) | Chặn ngay ở ô cài đặt. Đổi cài đặt giữa tháng thì áp từ kỳ sau, không áp lùi |

## 6. Dữ liệu máy cần, đã có hay chưa

| Dữ liệu | Có chưa | Ghi chú |
|---|---|---|
| Dòng hàng theo nhóm món trên hoá đơn đã ghi sổ | Có | Nhóm "Bánh ổ sinh nhật", "Hộp bánh theo mùa" |
| Nguồn đơn (Pancake, Tại chỗ, QR tại bàn, app) | Có | `custom_nguon` |
| Hàng tặng, huỷ, hoàn tiền | Có | `vgb_qua_tang`, `vgb_huy`, phiếu hoàn |
| Người giới thiệu và loại đơn | Có | `vgb_nguoi_gioi_thieu`, `vgb_gt_loai` |
| Số lượt gọi của một bàn trên một bill | Có, cần đọc | Doctype `Vagabond Goi Mon Ban`, lượt sau cộng vào cùng bill |
| Đơn bánh ổ do D1 nhận | Chưa có | Chỉ tách được khi nhân viên D1 nhập số vào ô Mã giới thiệu, bắt đầu từ nay |
| Người bán trên bill quầy | Có ô, ít dùng | `vgb_nguoi_ban`. Khoảng 80% bill TCV đang chung một tài khoản |
| Chi phí quảng cáo Meta | Chưa | Cần nối Meta Ads hoặc nhập tay kèm ảnh hoá đơn |
| Giảm giá, huỷ, điểm đánh giá của app | Chưa | Nạp báo cáo cửa hàng của app mỗi tháng |
| Giờ công | Chưa | Nạp bảng chấm công bên làm lương gửi mỗi tháng |
| Hàng lỗi, hao hụt bếp | Một phần | Phiếu huỷ hàng có; định mức hao hụt trên công thức |

## 7. Phạm vi kỹ thuật dự kiến cho PR sau

- Cài đặt chính sách trong một bản ghi (mốc, tỷ lệ, trần, mốc nền quỹ, danh sách bộ phận và người), có ngày hiệu lực.
- Hàm THUẦN cho từng công thức, ca kiểm cho từng luật ở mục 3 và mục 5.
- Mỗi tháng máy dựng phiếu cho từng người theo bộ phận. Phiếu tự khai giữ lại làm đường dự phòng.
- Bảng xuất cho bên làm lương lấy từ phiếu đã duyệt.

## 8. Câu hỏi cần chốt

**Cho anh Việt**
- Đã chốt 17/11: Q1 tách đơn D1 bằng mã giới thiệu của nhân viên D1; Q2 tính theo ngày ghi sổ; Q3 em quyết như mục 3.4; Q4 giờ công theo bảng chấm công bên làm lương.
- Q5. Danh sách người theo bộ phận, ai là người phụ trách (mức 1,5 triệu).
- Q6. Foodapp đổi sang giảm trơn hay giữ bậc như hiện tại?

**Cho Codex**
- C1. Rà mục 5: còn tình huống nào làm một người được lợi không công bằng, hoặc bị thiệt oan, mà bảng chưa có?
- C2. Công thức Marketing: r giảm theo tỷ lệ chi phí quảng cáo có tạo động cơ xấu nào không (ví dụ dồn chi phí qua tháng, cắt quảng cáo cuối tháng)?
- C3. Phương án A tại bàn: ngưỡng 30.000 đ và 10 phút cho lượt gọi thêm có đủ chặn việc tách một lượt thành hai không? Còn cách lách nào khác (khách bàn bên gọi giúp, quầy tự bấm lượt thêm)?
- C7. Tách đơn D1 chỉ bằng mã giới thiệu: Sales có động cơ nào để không nhắc nhân viên D1 nhập số (vì đơn D1 không nhập số sẽ tính cho Sales) không? Nên chặn thế nào?
- C4. Quỹ đội quầy theo bill bình quân: có bị lách bằng gộp bill hai bàn, hay chuyển bill nhỏ sang kênh khác không?
- C5. F2 trừ kỳ sau: cách nào để không tạo khoản âm treo mãi, và không trừ nhầm người?
- C6. Thứ tự áp trần, thưởng mùa vụ, bán kèm: tính trước rồi chặn trần, hay chặn trần từng phần?
