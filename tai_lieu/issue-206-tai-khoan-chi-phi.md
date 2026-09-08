# Issue 206: tài khoản chi phí bổ sung

## Sự cố và bằng chứng ngày 08/09/2026

Comment 5582455637 có ảnh LSX-080926-000125 (Triple Chocolatine, 59)
và LSX-080926-000126 (Plain Croissant, 11), cùng báo “Bắt buộc nhập Tài khoản”.

Đọc site bằng Administrator, chỉ SELECT:

- Company Vagabond: `default_operating_cost_account` đang trống;
  `enable_perpetual_inventory=1`, `enable_item_wise_inventory_account=0`.
- Kho Baker nguyên liệu có tài khoản152, thành phẩm1551; Company có152 và632.
  Không có bằng chứng lỗi thiếu tài khoản kho ở hai lệnh này.
- Hai lệnh hiện đã hoàn tất. PSX-2026-00056 lập16:09, PSX-2026-00057 lập16:12,
  đều đã ghi sổ. Phí “MH không quản kho” lần lượt1091,06 và6110,71 ghi Có621.
  Không chạy lại hai lệnh đã hoàn tất, không sửa chứng từ lịch sử.
- Chưa xác minh ai/cách nào điền621 cho hai phiếu thành công. Đã hỏi anh Việt.

## Nguyên nhân có thể tái diễn

Đối chiếu đúng ERPNext16.28.0 (de591661b9ba0bd3f62ac25b99b5c85c723515f6),
Frappe16.27.1 (f33ac3f00ab818e21b25ddbec93efb653fd9aa1b):

1. `bom.py:add_additional_cost` đọc Company.default_operating_cost_account.
2. `add_non_stock_items_cost` tính phí từ BOM, thêm dòng dù tài khoản trống.
   Chi phí vận hành cũng dùng mặc định này nếu chưa có tài khoản công đoạn.
3. `StockEntry.validate_difference_account` kiểm tài khoản trên dòng hàng,
   không kiểm bảng additional_costs. Server Script hiện có cũng chỉ sửa dòng hàng.
4. `StockEntry.get_gl_entries` dùng trực tiếp tài khoản dòng phí.
   `GLEntry.check_mandatory` chỉ báo Account is required, không nói thiếu ở đâu.
5. Child DocType Landed Cost Taxes and Charges chỉ đặt mandatory_depends_on
   phía giao diện. Lưu cha qua API không có chốt tài khoản tương đương.

Đây là đường mã khớp cấu hình hiện tại và triệu chứng. Chưa có traceback
của chính lần Khải bấm lỗi để khẳng định lịch sử thao tác đầy đủ.

## Thay đổi

`tai_khoan_chi_phi.kiem` dùng chung qua before_validate và before_submit
của Stock Entry, Subcontracting Order, Subcontracting Receipt, Landed Cost Voucher.
Kiểm từng dòng phí khác0, kể cả âm hoặc tổng phí triệt tiêu; tài khoản phải
tồn tại, cùng công ty, không tổng hợp, không bị tắt. Báo dòng và cách sửa.
Giữ nguyên tài khoản chọn tay; không tự gán621 hoặc lấy tài khoản phiếu cũ.

Không ép chế độ sổ kho liên tục lên công ty không dùng nó. Với Stock Entry
không có dòng nhập kho, để lõi bỏ bảng phí như distribute_additional_costs.
Không đổi cách tính tiền, không nới validation GL, không đổi Server Script,
không có patch hồi tố tài khoản hay chứng từ. Không thay đổi app bundle/version.

## Cấu hình cần chốt để Khải chạy lâu dài

Anh Việt/kế toán xác nhận tài khoản cho Company.default_operating_cost_account.
Đã trình621 vì hai phiếu thành công dùng tài khoản này; đây chưa phải phê duyệt.
Lưu ý mặc định dùng cả chi phí món không quản kho và vận hành chưa có tài khoản
công đoạn riêng. Không chọn tài khoản chỉ vì giúp vượt lỗi.

Sau khi được duyệt, người phụ trách cấu hình một lần trên Công ty, đọc lại
giá trị đã lưu. Lệnh mới qua bộ tạo phiếu lõi sẽ lấy tài khoản này. Phiếu nháp
đã tạo trước đó phải kiểm lại dòng phí; sửa cấu hình không tự sửa các phiếu cũ.

## Kiểm chứng và cổng phát hành

Local: cổng kiem_truoc_deploy đạt2653 ca tầng khung,0 hỏng; kiểm bundle khớp
từng byte. Bảy ca mới giữ chốt cho bốn nghiệp vụ, dữ liệu lỗi, câu báo và hooks.

Ba ca tích hợp mới đăng ký trong cua.py, CHƯA CHẠY trên bench ở phiên Codex:

- Bộ tạo phiếu BOM thật với ô cấu hình trống: insert bị chặn, không thêm
  Stock Entry/SLE/GL và không tăng produced_qty.
- Có cấu hình: hoàn tất2 lần từng phần, phí Có đúng tài khoản, SLE đúng lượng
  và giá trị tăng đúng phí, GL cân.
- Nhập kho trực tiếp có phí chọn tay: xoá tài khoản qua save/submit bị chặn,
  bản nháp trong DB không đổi; tài khoản hợp lệ vẫn ghi SLE/GL đúng.

Ca tích hợp chỉ giả lập giá trị đọc của một ô Company trong lúc gọi bộ tạo
phiếu, không sửa Company thật. Chứng từ, insert/submit và SLE/GL đều thật,
được rollback bởi nen.py; không commit, không gửi thông báo.

Claude review đúng SHA, chạy bench cùng phiên bản, yêu cầu chung_tu_con_sot
và so_luong_lech đều rỗng. Kiểm thêm phiếu gia công/phân bổ có phí trên bench
vì ba ca mới chưa chứng minh đầy đủ happy path của hai nhóm đó. Nếu fixture
hoặc code hỏng, trả traceback để Codex sửa; không coi local xanh là đủ deploy.

Sau release, kiểm bằng tài khoản Khải với lệnh mới được phép làm; không hoàn
tất lại125/126. Giữ issue206 mở cho đến khi có nghiệm thu ca thật và các mục
retry/làm tươi nhiều kho còn tồn từ vòng trước.
