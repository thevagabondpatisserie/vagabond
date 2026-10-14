# Việc tồn sau v594

Codex chịu trách nhiệm triển khai. PR duy nhất trên `codex/ton-sau-594`, từ main `df22c3dcd`. Đích phát hành v595, chưa đặt phiên bản khi các cửa ghi chưa hoàn thiện. Không sửa chứng từ cũ.

## A1. Tách và gộp tiền ngân hàng

Nguồn: [giao việc 4 trên PR469](https://github.com/thevagabondpatisserie/vagabond/pull/469#discussion_r4257062044).

### Đã có trong bản đầu

- Phép thuần `bo_sao_ke.phan_con`: số dư sau phân bổ lõi và phần tiền phiếu khác đang giữ; không trừ hai lần khi phần giữ chuyển thành liên kết lõi. Dữ liệu âm, vô hạn, trùng chủ, trùng chứng từ, hoặc vượt tiền phải báo lỗi.
- Hai ca bench dùng chứng từ thật: một PE chia hai BT (450.000.000 và 264.138.056); một BT trả hai PE. Đây là ca chứng minh khả năng lõi, CHƯA chứng minh cửa app đã gỡ kẹt.
- Chưa dựng trường giữ tiền, chưa gắn phép thuần vào thao tác đang chạy. Không có API ghi mới trong bản đầu.

### Đợt nối cửa APP và màn chung, đang kiểm

- Màn Khớp SePay nhận cờ chọn bộ từ máy chủ: nhiều dòng, thanh tổng, cùng tài khoản, chỉ Gán khi đủ; giữ lựa chọn qua trang và không gửi hai lần khi đang ghi. Mười ca DOM chạy đạt trên bản local.
- APP nhận bộ chọn tay và tự dò các dòng cùng mã có tổng đủ; vẫn giữ cửa kiểm nguồn chi. Phần giữ nằm trong trường ẩn trên chứng từ sẵn có, không thêm DocType. Bỏ bộ chưa ghi sổ và đổi bộ đi qua controller.
- Bank Transaction kiểm phần giữ trước lưu phân bổ; các cửa khớp một dòng cũ phải đọc lại phần đang giữ. Chưa coi đây là bằng chứng tranh chấp song song trên bench.
- Bổ sung bốn ca bench cửa APP: tự dò lệnh tách, chọn/bỏ bộ, một BT trả hai hồ sơ, đổi bộ/rollback. Chờ bench của SHA đẩy mới, không dùng kết quả xanh của bản nền thay thế.
- Kiểm đột biến local: bỏ kiểm tổng bị 2 ca bắt; bỏ kiểm số dư bị 2 ca bắt; bật Gán sớm bị 5 ca DOM bắt; cho cộng khác tài khoản bị 1 ca DOM bắt. Đã khôi phục code đúng.
- A1 còn các adapter nghiệp vụ và các ca cạnh tranh; A2 chưa triển khai. Chưa bàn giao hoàn thành, chưa sẵn sàng merge/deploy.

### Còn phải làm trước khi phát hành

- [ ] APP tự nhận cả bộ cùng mã, cùng tài khoản, tổng đủ. Chuyển sang PE/JE và nối đủ BT trong cùng transaction.
- [ ] TTNB, hoàn tiền, công nợ tiền vào, tạm ứng, hoàn ứng dùng cùng bộ; rà cả callback cũ ngoài registry.
- [ ] Giữ theo số tiền trên chứng từ hiện có; không tạo DocType. Mọi cửa kể cả Desk/API phải kiểm cùng chỗ giữ.
- [ ] Khóa BT/phiếu và current read; hai người cùng chọn chỉ một người dùng phần tiền còn lại. Không lấy snapshot trước khóa làm căn cứ.
- [ ] Một BT chia nhiều phiếu, phiếu thứ ba không được vượt phần còn lại.
- [ ] UI nhiều dòng, thanh tổng, nút Gán chỉ sáng khi đủ, giữ lựa chọn qua tìm kiếm/phân trang.
- [ ] Bỏ nối cả bộ; không gỡ phần của phiếu khác. Nếu còn bút toán sống phải xử lý qua lõi, không tự huỷ.
- [ ] Accounts Manager: Ghi nhận kèm lý do; Accounts User/AP FIN không có quyền này; hồ sơ vào Chờ đối chiếu sau.
- [ ] Sổ tay và tìm kiếm câu hỏi thật; đủ mười nhóm ca của Claude, DOM và đột biến.

Core đã đọc: `erpnext/accounts/doctype/bank_transaction/bank_transaction.py` tại `de591661b9ba0bd3f62ac25b99b5c85c723515f6`, `allocate_payment_entries` phân bổ min(phần chứng từ còn lại, phần BT còn lại). Không ghi tay `allocated_amount` để giả vờ đã đối chiếu. Cần kiểm trường hợp người chọn phần tiền nhỏ hơn mức core tự phân bổ và đọc lại GL/BT sau submit.

### Câu thật của kế toán cần tìm được trong sổ tay

> thanh toán lương 714.138.056 mà ngân hàng tách làm 2 lệnh 450.000.000 + 264.138.056 nên không ghi nhận thanh toán được

Luồng đích: mở hồ sơ, chọn cả hai dòng trong Khớp SePay, tổng đủ thì Gán, sau đó ghi nhận thanh toán. Hướng dẫn này CHƯA áp dụng cho bản đang chạy; chờ hoàn thiện UI/backend và nghiệm thu.

## A2. Giữ tồn đơn web

- [ ] Kiểm và giữ trong giao dịch tạo đơn. Nhả khi Pancake từ chối; không nhả chỉ vì timeout chưa biết kết quả.
- [ ] Giữ cách B: lỗi kiểm tồn vẫn nhận và báo Sales; bánh làm theo đơn ngày sau không chặn.
- [ ] Chống trừ hai lần khi đơn Pancake đã được đồng bộ vào tồn; hai kết nối song song tranh chiếc bánh cuối trên bench.

## A3. Lịch sử công thức

- [x] Ô Đang dùng ghi Bật/Tắt; Mặc định và Công thức ảo ghi Có/Không. Chặng sản xuất giữ chữ thật.
- [x] Không ghi lịch sử giả khi DB trả chuỗi 0/1 nhưng API gửi số 0/1.
- [ ] Cổng cuối và review cùng bản phát hành.

## A4. Dữ liệu chỉ bàn giao

`APP.26.09.009`: hồ sơ lương tháng 8, hai dòng sao kê chưa đối chiếu theo giao việc. Chỉ liệt kê, chưa đọc hoặc sửa chứng từ này trên site trong PR này.

## Các phần làm sau A

B: PR471 web Vue giữ Draft và công tắc tắt. Merge main không rebase, giữ F21 main; làm B0-B7 theo chỉ dẫn anh Việt. C: PR464 báo cáo nếu còn thời gian. Không trộn B/C vào PR này.

### Đợt TTNB, hoàn tiền và ngoại lệ APP

- Đã nối chọn bộ cho TTNB/hoàn tiền vào màn chung, cửa tự dò và callback webhook. Hoàn tiền vẫn sinh phiếu nháp; khi ghi sổ mới dùng phân bổ lõi, lấy đúng tài khoản trong bộ.
- Lỗi ghi bằng chứng trước commit phải rollback phần giữ. Cửa webhook đã xác thực dùng hàm nội bộ, không đòi Guest có vai kế toán; cửa chọn tay vẫn kiểm quyền riêng.
- APP có nút Ghi nhận kèm lý do theo quyền Accounts Manager/System Manager đã có. Chip Chờ đối chiếu sau dựa vào tổng phân bổ lõi, không biến mã giao dịch hoặc lý do thành bằng chứng đã khớp.
- APP tự dò đọc hết dòng cùng mã trước, không chọn riêng một dòng vừa tổng khi vẫn còn lệnh khác cùng mã.
- Thêm bench TTNB/hoàn tiền/ngoại lệ, hai tiến trình tranh phần 60.000 của BT 100.000, rồi kiểm phần 40.000 còn lại. Các ca mới phải đợi CI chạy thật.
- Bench SHA 22c5b038170d12cf9cb8dbfe10192dd2c2381556 đạt bước tích hợp máy chủ hai lượt, đỏ bước staging: ca cũ chọn dòng rồi chờ hộp xác nhận mà thiếu bấm Gán. Đã sửa thao tác kiểm, chưa coi bench tổng là xanh.
- A1 vẫn còn cửa công nợ tiền vào, bỏ bộ ngoài APP, rà phân bổ nhiều phần đang giữ và các đường tạm ứng/hoàn ứng; A2 chưa làm. Không dùng đợt này làm biên nhận hoàn thành A1.

### Kiểm bench và sửa phân bổ phần tiền

- Bench SHA 06225d89e2ab0cffee0b789509146286f8ddb48c đạt ca hai tiến trình tranh cùng số dư; một tiến trình giữ được 60.000, tiến trình kia bị từ chối, phần 40.000 còn lại vẫn dùng được.
- Bench bắt lỗi tự dò gom nguồn cá nhân thiếu chủ quỹ vào nguồn công ty hợp lệ cùng mã. Đã lọc nguồn trước khi dựng bộ; giữ thông báo nguồn chi cụ thể. Chờ bench của commit mới xác nhận sửa.
- Khi phiếu chỉ giữ một phần của BT, truyền hạn mức đó vào phép phân bổ lõi trước lưu. Bổ sung ca một PE 80.000 dùng 40.000 từ mỗi BT 100.000, trong khi mỗi BT có phiếu khác giữ 60.000. Không tự ghi allocated_amount.
- Local và giả lập CI không requests: 4.508/4.508. Cổng trước deploy mã 0. Đột biến bỏ hạn mức phân bổ bị 1/1 ca bắt. A1/A2 chưa hoàn thành.

### Đợt giữ tồn web, chưa nghiệm thu bench

- Kiểm cuối dùng mã hàng gốc, khóa hàng cấu hình và current read tồn/chỗ giữ; snapshot của đơn mới giữ số lượng trong cùng transaction. Gộp dòng trùng mã trước kiểm. Không thêm DocType.
- Đơn bị Pancake từ chối không còn giữ; timeout vẫn giữ. Đồng bộ Kiểm bánh đánh dấu đơn thực sự đã tính vào cột nguồn, tránh trừ hai lần. Hôm nay tính cả Cho chốt; nguồn decor ngày sau tính Đã đặt. Không chỉnh dữ liệu đơn cũ.
- 9 ca tầng khung mới kiểm giữ, tổng dòng, không trừ hai lần, decor0/cùng nguồn ba ngày, không ngày, đồng bộ, snapshot cũ, cửa tạo đơn và cách B. Hai đột biến: bỏ trừ giữ bị3ca bắt; trừ lần hai bị1ca bắt.
- Đã thêm bench hai tiến trình gọi cửa tạo đơn cùng chiếc cuối, chỉ một POST Pancake; sau đó từ chối nhả và timeout giữ. Chưa có kết quả bench SHA mới, chưa xác nhận A2 hoàn thành.
- Màn sao kê hiển thị phần được gán và phần còn lại của từng dòng. Sổ tay kiểm câu thật chị Dung qua bộ tìm kiếm thật.
- Bench21e001542 đã qua bước tích hợp máy chủ; staging đỏ do ca kiểm chuỗi cũ Sao kê/Bộ sao kê. Sửa ca giữ phần lý do chung và vẫn kiểm ValidationError/HTTP thất bại.
- A1 còn công nợ tiền vào, bỏ bộ ngoài APP, rà tạm ứng/hoàn ứng; A2 còn nghiệm thu và rà concurrency với đồng bộ. Giữ Draft, không phát hành.

### Đợt gỡ bộ và hoàn ứng nối TTNB

- Bench SHA 8e9882d100537ee84583f310bd3237eff927ffcc đã đạt tích hợp máy chủ, gồm hai tiến trình tranh chiếc bánh cuối: chỉ một đơn và một POST Pancake; từ chối nhả giữ, timeout giữ. Bench tổng vẫn đỏ vì bước staging chọn lại sao kê chưa bấm Gán. Đã sửa lần chọn thứ hai, chờ chạy lại.
- Bổ sung bỏ cả bộ TTNB/hoàn tiền, xác nhận trên màn, kiểm quyền và khóa hiện hành. Còn APP hoàn ứng hoặc PE/JE nháp/đã ghi sổ thì chỉ dẫn xử lý chứng từ liên quan trước; không tự hủy. Ca DOM kiểm hủy, lỗi, thành công và nút theo quyền.
- Hoàn ứng từ TTNB đọc tổng cả bộ, giữ đúng người ứng. Hai TTNB được giữ hai phần của một BT và nối hai APP riêng; không cho lấy nguyên BT đã giữ để hoàn thêm. Bổ sung bench thực đi qua tao_hoan_ung, chờ CI xác nhận.
- Local 4.520 ca đạt. Chưa hoàn thành A1: còn cửa công nợ tiền vào và kiểm trọn các đường còn lại. Chưa chuyển B/C, chưa đặt phiên bản, chưa merge/deploy.

### Điểm nối công nợ tiền vào còn thiếu (đã rà cửa thật)

- `cong_no.khop_tay` hiện đi `_giu_gd` và `_lap_theo_gd`; `thu_tien.lap_phieu_thu_theo_gd` vẫn độc quyền nguyên một BT và từ chối khi BT lớn hơn nợ. Không chỉ thay danh sách chọn trên màn.
- Phải giữ phân bổ trên phiếu công nợ, lập PE nháp bằng lõi theo từng Customer, lưu liên kết các PE vào cùng bộ. Phiếu nháp không phải đã ghi sổ.
- `thu_tien.ghi_so_phieu_thu`, `_thuoc_tap_unc`, `phieu_thu_nhap` và hook trước/ sau submit phải cùng đọc chủ bộ từ DB, kiểm UNC thật, nguồn công ty và phân bổ lõi. Không dùng mã tham chiếu giả hoặc flags từ máy khách làm quyền bỏ kiểm.
- Một phiếu công nợ có nhiều Customer tạo nhiều PE: ghi sổ PE đầu chỉ phân bổ đúng phần PE đó và giữ phần còn lại cho các PE nháp. `bo_sao_ke_db.noi` hiện yêu cầu cả bộ đã ghi sổ, nên chưa dùng nguyên hàm này cho ghi từng PE.
- Giữ đường không thấy sao kê cho kế toán đính UNC; sửa đường tự dò/callback để không vượt cửa bộ. Kiểm thêm trả góp, hủy PE, bỏ cả bộ và retry. Chưa triển khai các điểm này, không coi A1 đã hoàn thành.

Đột biến hoàn ứng đọc riêng BT đầu: ca thấy 60 thay vì tổng 100 và bắt 1/1 đột biến; khôi phục đúng thì 2/2 ca mới đạt. Bổ sung ca chủ APP/TTNB đúng, sai chủ, sai BT, metadata trống và cửa cũ chưa kiểm phần.

### Review trên 2e89ab30d và bench tiếp

- Bench38520517474: 415/416 ca tích hợp đạt trong cả hai lượt. Ca hoàn ứng chia TTNB đạt; ca hoàn tiền chỉ hỏng lúc hủy PE do đối tượng trong ca kiểm chưa reload sau khi lõi cập nhật clearance_date. Đã bổ sung reload, không bỏ kiểm hủy và nhả cả bộ.
- P1 review: APP chuyển Từ chối/Hủy vẫn giữ bộ vì mã không đổi. Sửa controller nhả qua cửa kiểm bút toán, xóa mã cùng transaction; thêm ca thật gọi duyet rồi phiếu sau giữ lại cả hai dòng. APP hoàn ứng đã từ chối không còn phải kiểm giữ TTNB như hồ sơ đang yêu cầu hoàn.
- P2 review: Pancake dời ngày nhận thì đồng bộ theo ID và ghi ngày nguồn vào metadata chỗ giữ; không sửa ngày trên biên nhận cũ. Đồng bộ ngày cũ không xóa dấu của ngày mới. Truy vấn đọc thêm ID đang đồng bộ và ngày nguồn để không bỏ sót đơn dời ngày. Thêm ca tầng khung và bench thật.
- Hai đột biến review: bỏ nhả bộ bị1ca bắt; quay lại lọc ngày cũ bị1ca bắt. Khôi phục đúng2/2ca đạt. Sổ tay đã bổ sung đúng tên nút và chia mục theo giới hạn1600ký tự.
- Chưa hoàn thành A1 công nợ tiền vào; bench bản sửa mới phải chạy lại, không dùng kết quả cũ thay thế.

### 15/10: tái hiện P2 và bản sửa đang kiểm

- Baseline runtime `035e35e6c`, commit chỉ thêm probe `e3bbb5d5f75865f2cb3c7a2517b2723962c5d933`, [bench 38549666430](https://github.com/thevagabondpatisserie/vagabond/actions/runs/38549666430), MariaDB REPEATABLE-READ. BT không liên quan chờ 2,072067 giây; đảo thời điểm có QueryDeadlockError 1213; tạo APP mới chờ 2,043181 giây. Mỗi ca dùng hàng rào giữ 2 giây, thao tác và phân bổ lõi thật trên bench dùng một lần.
- Bản sửa dùng trường ẩn trên BT hiện có, đọc chủ giữ theo khóa chính. Không quét LIKE FOR UPDATE bốn bảng phiếu. Khóa BT theo tên trước phiếu; current read phát hiện bộ đổi trong lúc chờ thì yêu cầu thử lại. Mixin Document chạy trước khóa ngầm của Frappe `_save/check_if_latest`, không đợi đến validate.
- Ba đột biến local: khôi phục quét LIKE FOR UPDATE; bỏ khóa/kiểm bộ thay đổi; bỏ bảo vệ trường chủ BT. Mỗi đột biến bị 1 trong 3 ca P2 bắt, tổng 3/3 đột biến. Đây chưa thay số liệu bench sau sửa.
- Hoàn tiền: hook on_submit PE đặt hồ sơ thành `Da chi`; hủy PE không tự đổi lại. Bỏ bộ nhận trạng thái này và `Hoan thanh`, nhưng vẫn từ chối PE nháp/đã ghi sổ hoặc BT còn liên kết. Khi bỏ hợp lệ, xóa dấu hoàn thành để không hiển thị kết quả cũ.
- Đã bổ sung `bo_sao_ke_luong.bo` vào cửa ngõ. Còn đo khóa đơn web P3, rà toàn bộ thứ tự khóa cửa ghi/hoàn ứng, công nợ tiền vào và tạm ứng, bench tổng/staging đúng SHA. Chưa hoàn thành A1/A2, chưa merge/deploy.

### Số đo sau P2 tại 1c59da60f và P3 trước sửa

[Bench38617438497](https://github.com/thevagabondpatisserie/vagabond/actions/runs/38617438497), đúng `1c59da60fa6d1216925682183b06e029d8df7b51`:

| Ca | Trước | Sau |
| --- | --- | --- |
| BT không liên quan | 2,072067 giây | 0,037852 giây |
| Đảo thời điểm | Deadlock1213 | Hai lượt đạt, B0,061670 giây |
| Tạo APP trong lúc B giữ | 2,043181 giây | 0,031920 giây |

- Cả ba ca giữ hàng rào2giây, phân bổ lõi thật. JSON `do-khoa-476.json` trong artifact.
- P3 tái hiện: hook cập nhật trạng thái đơn web khác chờ2,066342giây khi tao_don giữ _don. Hook cập nhật DB thật; tắt riêng hàng đợi quảng cáo và nối ưu đãi; không giả phép UPDATE. JSON `do-khoa-web-476.json`.
- Bench tổng chưa xanh:414/417 mỗi lượt. Ca247 đòi mọi dòng danh sách bằng tổng tiền không còn đúng màn chọn bộ; ca giả deadlock cần ném từ cửa khóa mới trước _ho_so. Ca hoàn tiền còn bị phiếu THU nháp của cùng hồ sơ chặn bỏ bộ tiền RA: thu/chi là hai chứng từ khác nhau. Đang sửa, không bỏ kiểm PE chi còn sống.
- P3 sửa bằng cột ngày nguồn giữ tồn có chỉ mục trên DocType đơn web hiện có, cập nhật cùng snapshot. Đọc riêng khoảng4ngày và ID Pancake có chỉ mục; không OR/JSON/LIKE làm quét cả bảng. Không hồi tố dữ liệu cũ. Ca giữ tồn dời ngày vẫn phải đạt.
- Rà thêm: chỉ mục mã giao dịch cho chủ APP cũ; hoàn ứng chỉ đọc chứng cứ TTNB đã khóa, không ghi lại bộ; PE hoàn tiền khóa bộ trước _save/load_from_db. Tất cả còn cần bench SHA mới, không lấy số đo1c59 thay cho kết quả bản sau.

### Cửa ghi từng phiếu thu A1 đang triển khai

- Thêm helper nội bộ noi_tung_phieu_thu: đọc chủ/CT/hạn mức từ DB, chỉ nối
  PE Receive đã ghi sổ bằng phép phân bổ lõi, giữ PE nháp và hạn mức từng BT.
  Retry không thêm liên kết. Chưa nối helper này vào app/factory/hook PE.
- Unit một bộ hai BT, hai PE, phần BT còn dành phiếu khác; bỏ hạn mức BT
  làm PE đầu ăn60 thay vì40 và bị1ca bắt. Thêm bỏ kiểm PE nháp và bỏ kiểm chủ DB: mỗi đột biến bị1ca bắt, tổng3/3. Khôi phục ca đạt.
- Bổ sung bench riêng helper: ghi từng PE thật qua hai BT, retry, hủy PE đầu
  trả lại nợ đúng khách trong khi PE sau còn nguyên. Chưa có kết quả SHA mới.
- Còn bắt buộc: chủ PE từ DB có chỉ mục, khóa trước PE cho mọi cửa;
  khop_tay/factory/UNC/ghi_so_phieu_thu/DS nháp/callback chung đường bộ;
  UI nhiều dòng, trả góp, bỏ cả bộ, tạm ứng, đủ10nhóm và DOM. A1 chưa xong.
- Hai ca PDF local trước thiếu pypdf đã chạy lại bằng Python bundled có
  pypdf6.10.0:13/13ca module đạt; toàn bộ fakeCI bundled4530/4530 tại d6ff.

- Local lượt helper:4529/4529 bằng Python hệ thống; fakeCI bundled có pypdf4531/4531; cổng đầy đủ mã0. Chưa có bench helper, không gọi A1 đạt.

### P2/P3 chốt bằng chứng d6ff và A1 nối chủ phiếu thu

- SHA d6ff21bd821fe7451950f890a19bb15eb8e6ca07: CI38620297433 và
  bench38620297359 đều SUCCESS, gồm staging.417/417 mỗi lượt, sạch rollback.
  P2 lần lượt0,044130136giây; đảo thứ tự B0,041298030giây không deadlock;
  tạo APP0,037878483giây. P3 từ2,066341873giây xuống0,192433728giây.
- ad001975d đã đẩy helper ghi từng PE. Lượt tiếp thêm Link chủ CN trên PE
  hiện có, bảo vệ bằng DB, khóa trước Document và kiểm không sửa khách,
  hóa đơn, tiền của PE đang thuộc bộ qua payload. Không thêm DocType.
- Factory thu_tien có nhánh bộ nội bộ: đọc lại nguồn/hạn mức từ DB, mỗi
  Customer một PE, bind sau khi lưu danh sách CT. Tab nháp và ghi sổ app
  đọc cùng chủ DB; hook submit phân bổ qua lõi. UNC vẫn bắt buộc như cũ.
- Bench mới đổi ca helper sang tạo hai Customer/PE bằng factory, tab nháp,
  ghi_so_phieu_thu với tệp thật, hai BT, retry và cancel. Chưa có kết quả
  trên SHA lượt nối này; không lấy bench d6ff thay.
- Cửa cong_no.khop_tay chưa nhận bộ; UI, callback tự động, trả góp và bỏ
  bộ CN, tạm ứng vẫn còn. Chưa có bàn giao ĐÃ SỬA XONG, chưa chuyển B/C.

- Cửa cong_no.khop_tay đã thêm nhánh dong nội bộ có mã lần thao tác, khóa
  BT trước CN, cộng kỳ thu nhưng không giảm phần cũ đã gắn PE. Factory bỏ
  tổng client, đọc lại hạn mức DB. Ca bench mới gọi cửa này thật và retry.
  Chưa nối UI/callback, chưa kiểm đủ trả góp/bỏ bộ CN, nên chưa mở phát hành.
- Chủ cũ không có bộ vẫn phải giữ: đọc danh sách mã CN nhiều dòng; chủ bộ
  mới không chiếm nguyên BT khi kiểm đường chia phần. Lỗi đọc registry/chủ
  trong đường ghi mới nổi lỗi, không nuốt để nhận nhầm tiền.

### Nối lại phiên: công nợ bộ và trả góp đang kiểm

- Bench ad001975d đã SUCCESS cả staging (run38622885452); không thay cho
  bench bản nối cửa nghiệp vụ mới dưới đây.
- Cửa khớp tay nhận bộ sao kê, factory lập PE riêng mỗi Customer, từng PE
  ghi sổ qua lõi và giữ phần của PE còn nháp. Chủ bộ trên PE lấy từ DB.
- Màn Khớp tay thêm chọn nhiều giao dịch/thu một phần, dùng chung màn SePay.
  Kỳ mới chỉ thấy phần chưa giữ của kỳ trước. Mất phản hồi gửi lại đúng
  payload/mã lần; không dùng số tiền client để thay số máy chủ.
- Bỏ cả bộ CN chỉ cho kế toán, từ chối nếu PE nháp/đã ghi sổ còn hiệu lực.
  Không tự hủy chứng từ. Khi hợp lệ, giữ nguyên bộ của phiếu khác dùng cùng BT.
- Thêm bench nhóm6: hai kỳ thu cùng BT, phần dư cho phiếu khác, bỏ bộ/retry;
  thêm ca hai Customer, hai BT, UNC thật, ghi từng PE, hủy trả nợ đúng khách.
  Chưa chạy bench trên commit của lượt này.
- DOM mới14/14. Hai đột biến mới: tin chủ PE từ payload và quên trừ phần kỳ
  trước, mỗi đột biến bị1ca bắt (2/2); khôi phục2/2đạt. Probe đầu đọc nhầm
  harness tích lũy lỗi thành exception nên ghi0/2, đã sửa bộ chạy và đo lại.
- VIỆC CHƯA LÀM: tự dò/callback CN và đường một dòng cũ chưa chuyển cùng
  cửa bộ; còn rà cạnh tranh SI/PE, tạm ứng, đủ10nhóm và bench tổng SHA cuối.
  Không báo A1 xong, không chuyển B/C, không merge/deploy hoặc sửa dữ liệu cũ.
