# Issue 332: đổi mã hàng trên hóa đơn nguồn

- Owner Codex; nhánh codex/hoa-don-nguon-doi-ma, base f78ab97b.
- Nguồn: issue332 và yêu cầu anh Việt ngày16/09/2026; Claude review độc lập.
- Không sửa chứng từ production; quyền deploy sau đủ cổng không cho phép hủy/sửa tờ cũ.

## Nguyên nhân đã đo
Đọc Version và nguồn trên site: tiền từng đúng, sau khi xóa/thêm dòng thì mất
tên NCC, giá/quy cách theo mã khác. Ánh xạ cũ trỏ Item disabled, traceback ở
quy_cach_ncc._kiem_uom làm hook dựng lại không hoàn tất. Có một hồ sơ cùng
số/NCC đã ghi sổ nhưng không mang mã nguồn. Chưa chứng minh thao tác UI nào
đã tạo hồ sơ đó; không suy ra copy hay lỗi đồng bộ chỉ từ thời gian tạo.
Dữ liệu chi tiết giữ local; không đưa dump/chứng từ thật lên GitHub.

## Code
- Cửa sửa tay trên Desk: chọn dòng hiện tại, dòng nguồn duy nhất, Item/UOM.
  Giữ tiền nguồn, xác nhận và ghi nhớ mapping mới; kiểm write + role, khóa PI,
  check modified, savepoint bao mapping và PI, reload rồi kiểm kết quả trước
  báo thành công. Đã nối kho/mua hoặc tên nguồn trùng/tách thì hướng dẫn đối
  chiếu, không đoán và không nắn chứng từ cũ tự động.
- Dòng nguồn map Item disabled được nhập ở trạng thái thiếu mã; không lấy
  mã/giá khác. Hook không dựng được phải nói đường sửa, không chỉ log.
- Tờ thiếu source ID có cảnh báo cùng bill/NCC/company nếu người dùng đọc
  được hồ sơ liên quan; không tự gắn nguồn hoặc chặn ghi sổ.
- Frappe16.27.1 Document.run_before_save_methods chạy before_validate trước
  validate. ERPNext16.28.0 BuyingController.validate tính stock_qty sau
  AccountsController.validate. Autocomplete hỗ trợ label/value nhưng render
  label bằng HTML nên escape tên nguồn. Dialog kiểm hành vi bằng Node.

## Kiểm và giới hạn
Local3048/0, Node50/0, predeploy rc0, bundle khớp. Đột biến bỏ kiểm
Item disabled: ca tương ứng đỏ, bản nguyên5/5. Gate cuối trên SHA PR.
Bench thêm API thật save/reload, retry stale, lỗi on_update sau db_update
phải rollback PI và mapping; chưa chạy khi ghi hồ sơ này.
Chưa có chứng minh browser thật 390px/Desk hoặc deploy. Không coi Node là UAT.
Phiên bản497 dự kiến sau PR327/v496; tích hợp giữ cả patch496/497 và chạy lại.

## Bước tiếp
CI/bench và Claude review SHA đầu. Đặc biệt review quyền ghi mapping, nguồn
trùng/tách, tránh báo xong khi DB lệch, case mất source ID. Còn audit lỗi
đồng bộ/trạng thái toàn luồng, không nhận một PR đã chữa mọi loại sai lệch.
Model/effort runtime chưa xác minh, token provider unavailable; review0 lượt.
