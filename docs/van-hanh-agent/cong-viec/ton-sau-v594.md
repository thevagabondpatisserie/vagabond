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
