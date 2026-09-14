# Issue 308: lô cảnh báo của mã thay thế

- Nguồn: https://github.com/thevagabondpatisserie/vagabond/issues/308
- Codex làm chính, nhánh `codex/308-lo-thay-canh-bao`, nền main `1f01cf5bae3716c4f8761c4add6fa96cb9f458cc` (v490).
- Anh Việt yêu cầu tiếp tục các issue sản xuất của Khải ngày 14/09. Giữ chính sách v489: HSD/lô tắt chỉ cảnh báo, không cho âm kho.

## Kết quả

`gan_lo` trước đây vét lô cảnh báo của mã gốc nhưng bỏ mã thay. Ba ca gọi gan_lo thật với cửa DB giả đỏ vì thiếu hàng; sau sửa 2982/2982 ca thuần đạt.

Đã thêm vòng vét mã thay sau vòng vét mã gốc. Giữ danh sách mã đã duyệt, đúng kho, đơn vị gốc, original_item và túi tồn dùng chung có trừ phần chọn tay. Không thay chính sách phê duyệt mã thay (issue305 xử lý riêng).

Thêm hai ca bench Manufacture: mã gốc không tồn, mã thay chỉ còn lô quá hạn hoặc lô tắt; insert/save/submit, cảnh báo, SLE đúng mã/kho/lô, giá vốn 1700, consumed_qty theo mã gốc, huỷ trả tồn 10 và giá trị 17000. Chỉ fixture trong savepoint, không chạy trên production.

Mã nguồn core đã đối chiếu: stock_entry.get_matched_items và work_order.get_consumed_qty dùng original_item; stock_ledger.make_sl_entries đảo lượng khi huỷ. Bản sửa không thay core.

## Còn lại

Chờ Claude review và bench CI hai lượt sạch trên SHA cuối. Local không có site; hai ca tích hợp mới chưa được chứng minh. V491 dành cho lần phát hành này, phải xác minh main chưa chiếm số trước merge. Chưa merge, deploy, migrate hoặc kiểm live. SHA và link cổng cuối ghi trên PR.
