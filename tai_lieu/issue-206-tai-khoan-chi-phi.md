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
- Comment 5583472911 và ảnh Khải ghi rõ: Khải chọn tay621 trên Desktop.
  App Bếp không có bước chọn tài khoản, nên bị chặn dù Desktop chạy được.

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

Đường mã khớp cấu hình lúc báo lỗi và thao tác chọn tay mà Khải xác nhận.

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

Theo yêu cầu mới, patch mac_dinh_san_xuat_206 chỉ chỉnh metadata:
đưa item_name có sẵn ngay sau production_item, nhãn Tên sản phẩm, chỉ đọc;
mặc định skip_transfer=1 cho lệnh mới, giữ giá trị0 khi người dùng bỏ tick;
giữ các mẫu số phiếu cũ và thêm PSX-.YYYY.- nếu thiếu. JS Desk gợi ý PSX khi
tạo phiếu Manufacture và rút gợi ý khi đổi nghiệp vụ. Server Script hiện có
đã chốt PSX theo purpose trước insert, không sửa hoặc thay thế script này.
Tên phiếu cuối cùng vẫn theo quy tắc máy chủ hiện có của site.

## Cấu hình đã thực hiện theo comment 5583472911

Đã lưu Company.default_operating_cost_account của công ty Vagabond thành
621 - Chi phí nguyên liệu, vật liệu trực tiếp - TV bằng form Company trên
Desk, theo yêu cầu anh Việt chuyển trong issue. Version 2gdvhd7oo1 ghi nhận
từ trống sang621. Đọc lại DB xác nhận đúng; không sửa công ty Demo, Server
Script, biểu đồ tài khoản hoặc chứng từ lịch sử. Mặc định dùng cả chi phí
món không quản kho và vận hành chưa có tài khoản công đoạn riêng.

Đã gọi đúng API make_stock_entry mà Bếp dùng để XEM TRƯỚC LSX-080926-000129,
Plain Croissant, qty23. Dòng MH không quản kho trả sẵn tài khoản621,
amount/base_amount2281,30, currencyVND. Không insert/submit. Số lượng trước
và sau đều giữ nguyên: Stock Entry252, SLE3386, GL13091, Bundle2077.
Đây là kiểm API bằng Administrator, chưa phải nghiệm thu hoàn tất lệnh trên
app bằng tài khoản Khải. Thử xem trước lệnh125 đã bị lõi chặn đúng vì có
PSX57; không sửa hoặc cố vượt chốt chống trùng.

Khải mở lại app và thử lệnh chưa hoàn tất. Không làm lại125/126. Phiếu nháp
đã tạo trước cấu hình phải kiểm lại dòng phí; cấu hình không hồi tố phiếu cũ.

## Kiểm chứng và cổng phát hành

Local: cổng kiem_truoc_deploy đạt2654 ca tầng khung,0 hỏng; kiểm bundle khớp
từng byte. Có kiểm hành vi JS PSX, đổi mục đích, chọn tay, phiếu cũ và phản
hồi muộn; kiểm patch lặp giữ trường riêng và đúng loại Property Setter.

Bốn ca tích hợp mới, CHƯA CHẠY trên bench ở phiên Codex:

- Bộ tạo phiếu BOM thật với ô cấu hình trống: insert bị chặn, không thêm
  Stock Entry/SLE/GL và không tăng produced_qty.
- Có cấu hình: hoàn tất2 lần từng phần, phí Có đúng tài khoản, SLE đúng lượng
  và giá trị tăng đúng phí, GL cân.
- Nhập kho trực tiếp có phí chọn tay: xoá tài khoản qua save/submit bị chặn,
  bản nháp trong DB không đổi; tài khoản hợp lệ vẫn ghi SLE/GL đúng.
- Migrate metadata lặp lại; tên cạnh mã, mặc định lệnh mới và giữ bỏ tick
  chủ động khi lưu Work Order thật.

Ca tích hợp chỉ giả lập giá trị đọc của một ô Company trong lúc gọi bộ tạo
phiếu, không sửa Company thật. Chứng từ, insert/submit và SLE/GL đều thật,
được rollback bởi nen.py; không commit, không gửi thông báo.

Claude review đúng SHA, chạy bench cùng phiên bản, yêu cầu chung_tu_con_sot
và so_luong_lech đều rỗng. Kiểm thêm phiếu gia công/phân bổ có phí trên bench
vì các ca mới chưa chứng minh đầy đủ happy path của hai nhóm đó. Nếu fixture
hoặc code hỏng, trả traceback để Codex sửa; không coi local xanh là đủ deploy.

Sau release, kiểm bằng tài khoản Khải với lệnh mới được phép làm; không hoàn
tất lại125/126. Giữ issue206 mở cho đến khi có nghiệm thu ca thật và các mục
retry/làm tươi nhiều kho còn tồn từ vòng trước.
