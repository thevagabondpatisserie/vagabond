# Issue 308: lô cảnh báo của mã thay thế

- Nguồn: https://github.com/thevagabondpatisserie/vagabond/issues/308
- Codex làm chính, nhánh `codex/308-lo-thay-canh-bao`, nền main `1f01cf5bae3716c4f8761c4add6fa96cb9f458cc` (v490).
- Anh Việt yêu cầu tiếp tục các issue sản xuất của Khải ngày 14/09. Giữ chính sách v489: HSD/lô tắt chỉ cảnh báo, không cho âm kho.

## Kết quả

`gan_lo` trước đây vét lô cảnh báo của mã gốc nhưng bỏ mã thay. Ba ca gọi gan_lo thật với cửa DB giả đỏ vì thiếu hàng; sau sửa đầu 2982/2982 ca thuần đạt. Bổ sung một ca nhiều dòng đã bắt lỗi lô cảnh báo còn dư bị tính thành hàng tốt ở dòng sau; thêm bộ lọc chi_tot ở vòng hàng tốt để giữ đúng thứ tự. Cổng SHA mới phải chạy lại.

Đã thêm vòng vét mã thay sau vòng vét mã gốc. Giữ danh sách mã đã duyệt, đúng kho, đơn vị gốc, original_item và túi tồn dùng chung có trừ phần chọn tay. Không thay chính sách phê duyệt mã thay (issue305 xử lý riêng).

Thêm hai ca bench Manufacture: mã gốc không tồn, mã thay chỉ còn lô quá hạn hoặc lô tắt; insert/save/submit, cảnh báo, SLE đúng mã/kho/lô, giá vốn 1700, consumed_qty theo mã gốc, huỷ trả tồn 10 và giá trị 17000. Chỉ fixture trong savepoint, không chạy trên production.

Mã nguồn core đã đối chiếu: stock_entry.get_matched_items và work_order.get_consumed_qty dùng original_item; stock_ledger.make_sl_entries đảo lượng khi huỷ. Bản sửa không thay core.

## Còn lại

Chờ Claude review và bench CI hai lượt sạch trên SHA cuối. Local không có site; hai ca tích hợp mới chưa được chứng minh. V491 dành cho lần phát hành này, phải xác minh main chưa chiếm số trước merge. Chưa merge, deploy, migrate hoặc kiểm live. SHA và link cổng cuối ghi trên PR.

## Review và bench 14/09, lượt tiếp

Claude5658338207: F1 thiếu đối chứng trừ chọn tay, F2 gọi lại danh sách mã,
F4 chưa chịu lực cờ chi_tot trên túi gốc. Đã thêm nhánh tay2/máy5 phải chặn,
tay2/máy4 cấp đúng4; dùng lại cac_ma_thay khi báo thiếu.

F4 dùng tình huống khả thi: dòng A vét B-cu, dòng B tiếp theo phải lấy
C-moi được duyệt trước B-cu còn dư. Không dùng tình huống hai dòng A mà
B-moi tự dư ra sau khi vòng trước đã vét hết hàng tốt B.

Đột biến chạy thật trên6ca308: bỏ trừ tay đỏ1; bỏ lọc chi_tot đỏ2; bỏ cờ
chi_tot riêng lời gọi túi gốc đỏ1. Khôi phục code xanh6/6.

Bench34800696060 ở b8d1edcd: cả hai lượt214/216, hai ca mới chết lúc tạo
Item Alternative vì Item thử chưa bật allow_alternative_item. Chưa tới
Manufacture; không phải bằng chứng code ghi sổ đạt. Core
item_alternative.has_alternative_item yêu cầu cờ này. Đã save cờ trên Item
thử trước khi tạo cặp, không đổi dữ liệu thật. Chờ bench mới.

Đã tích hợp main5cf2e073 (PR312), không đổi phiên bản491.
