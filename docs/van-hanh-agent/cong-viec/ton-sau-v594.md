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
