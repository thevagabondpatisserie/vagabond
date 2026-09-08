# Issue #206: kho sản xuất và thao tác desktop

Codex triển khai. Claude review, chạy kiểm trên Frappe và phụ trách deploy theo phân công của anh Việt ngày 08/09/2026. Issue #206 tiếp tục mở tới khi chứng minh ca của Khải đã hết lỗi.

## Hành vi trong bản này

- Món thành phẩm có ô **Kho nguyên liệu mặc định khi sản xuất**, chọn từ Warehouse bằng tìm kiếm. Đây là kho lấy nguyên liệu để làm món đó; không phải kho của từng mã nguyên liệu và không đổi kho nhập thành phẩm. Khai một lần cho các lệnh mới.
- Kho chọn riêng trên lệnh được ưu tiên. Lệnh mới chưa có kho lấy mặc định từ Món, rồi mới tới quy tắc bếp đang có. Không sửa hàng loạt Item, BOM hoặc lệnh cũ. Món dùng chung nhiều công ty cần chọn kho đúng công ty trên từng lệnh; một field không biểu diễn nhiều mặc định theo công ty.
- Hook không đè lại kho đã có trên dòng nguyên liệu theo bếp của thành phẩm. Dòng chọn kho khác có chủ ý được giữ. Đổi header bằng giao diện ERPNext vẫn chạy thao tác điền kho dòng của lõi.
- App tạo lệnh hiển thị kho nguồn trên mỗi món. Chọn kho chung bằng tay được nhớ qua lần mở app sau, thẻ ghi rõ chế độ; nút dùng lại kho trên Món cho phép trở lại chế độ mặc định. Thẻ chi tiết đọc tồn theo kho từng dòng, hoặc WIP trong luồng qua WIP. Lỗi đọc tồn không hiện thành tồn 0. Còn lại trừ cả hao hụt.
- Desktop Work Order: chip trạng thái có số đếm, ngày dự kiến hôm nay/ngày mai/7 ngày tới, lọc kho nguồn. Cột món hiển thị tên và mã dạng chữ thuần; tooltip mặc định của Frappe cũng là tên và mã. Mở lệnh có khối kho, đã nhập, hao hụt, còn lại và cảnh báo dòng khác kho.
- Production Plan: chip trạng thái và **ngày lập kế hoạch** (không gọi nhầm là ngày sản xuất). BOM: chip lọc bản dùng/bản còn hiệu lực/bản cũ/nháp/huỷ, giữ chip phiên bản sẵn có. Item Alternative: chip tình trạng cấu hình đã kiểm; không coi đây là xác nhận tồn khả dụng.
- Chip dùng bộ lọc/API đếm có quyền của Frappe, giữ bộ lọc khác, không ghi thiết lập của người khác. Số đếm lỗi là `?`. Trạng thái lệnh không xác nhận đủ nguyên liệu.
- Dòng tự thay nguyên liệu lưu `original_item` để ERPNext cộng `consumed_qty` theo mã gốc; giữ lô/kho của nguyên liệu thực dùng.

## Bằng chứng và giới hạn

Đã đối chiếu mã nguồn ERPNext **16.28.0** (`de591661b9ba0bd3f62ac25b99b5c85c723515f6`) và Frappe **16.27.1** (`f33ac3f00ab818e21b25ddbec93efb653fd9aa1b`) theo phiên bản đọc trên màn Installed Applications của site. Chưa deploy bản này lên site.

Cổng máy chạy với `PATH` có Node và `PYTHONPYCACHEPREFIX=/tmp/vgb206-pycache` vì Python hệ thống trên macOS đặt cache ngoài sandbox:

```sh
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
node vagabond/khung/kiem_thu/hanh_vi/kiem_san_xuat_206.js
```

Unit test chạy hàm Python thật với dữ liệu giả; test Node chạy script danh sách thật với hợp đồng DOM/Frappe giả. Chúng kiểm được chọn kho, giữ bộ lọc, trạng thái chọn, số đếm lỗi và liên kết mã thay thế. Chúng **không chứng minh** tích hợp ERPNext, quyền thực tế của Khải hoặc bố cục browser thật.

Có thêm `thu_san_xuat_206.py` trong bộ `vagabond.khung.kiem_that`: insert/save/reload Work Order, ghi hai lần Manufacture, đọc SLE/GL/consumed_qty. Chỉ tạo mã thử ngẫu nhiên; dùng savepoint, khoá commit, cấm thông báo của khung sẵn có. **Chưa chạy** vì máy Codex không có site/bench Frappe. Hai ca ban đầu không theo lô; Claude đã chạy đạt trên ae147a6, theo review 5580151608. Bốn ca mới của vòng sửa này kiểm Manufacture theo lô hết hạn, cần chạy lại trên SHA cuối. Ca Bacardi/ISC vẫn cần nghiệm thu cấu hình thật.

## Claude cần review và cung cấp bằng chứng trước phát hành

1. Đồng bộ với main mới nhất, chọn số APPVER của đợt release, dựng lại bằng `dung_app_bep.py`. Main 17ec12f đã là v450 và đã gộp vào nhánh này; không coi v450 là số release riêng của #206.
2. Chạy migration schema `vagabond.patches.san_xuat_206` hai lần trên bench kiểm thử. Kiểm field tồn tại đúng Link Warehouse, patch log đúng, không thay giá trị Item/WO cũ. Patch riêng này báo lỗi nếu thiếu cột; không dựa vào hàm đồng bộ chung vốn nuốt lỗi.
3. Chạy bộ tích hợp trên bench có đúng Frappe/ERPNext trước production. Bằng chứng phải có kết quả ca, `chung_tu_con_sot=[]`, `so_luong_lech={}`. Không gọi commit hoặc sửa dữ liệu lịch sử để làm test xanh.
4. Test quyền của Khải: danh sách/đếm/chi tiết/kho; kho bị tắt, nhóm kho, sai công ty, không đủ quyền phải bị chặn rõ. Kiểm API insert/save/submit, không chỉ bấm UI. Hai món khác kho trong cùng lượt tạo phải dùng đúng mặc định; lựa chọn tay phải thắng.
5. Test màn desktop thực với tài khoản Khải, màn rộng và cửa sổ hẹp: Work Order, Production Plan, BOM, Item Alternative. Kiểm bộ lọc đang có, chọn nhiều chip, đổi route, count lỗi/chậm, tooltip và khối dashboard không che tiến độ lõi. Chụp kết quả sau deploy.
6. Dựng lại ca Bacardi/ISC trên dữ liệu thử: gốc hết ở Pastry, ISC còn ở Pastry, Baker không có. Kiểm kho dòng sau save/submit, mã/lô/số lượng/UOM thực bị trừ, `original_item`, consumed_qty, SLE và GL. Test thiếu cả hai thì rollback, không có phiếu/lô mồ côi. Không thử trực tiếp bằng việc sửa lệnh quá khứ của Khải.
7. Sau review/test đạt mới merge và deploy theo phân công. Ghi SHA, CI, Cloud build, migrate, Patch Log, phiên bản app và kiểm UI thực. CI xanh không phải bằng chứng đã deploy.

## Các hạng mục còn mở để làm triệt để

Các mục dưới đây được ghi để Codex tiếp tục xử lý nếu review xác nhận cần; **chưa được triển khai hoặc chứng minh trong PR này**, không giao Claude âm thầm viết tiếp trong lúc review:

- Kiểm thiếu nguyên liệu trước hoàn tất theo đúng kho/lô/UOM, phân biệt gốc thiếu nhưng có mã thay thế với thật sự thiếu. Chỉ thêm chip “Đủ nguyên liệu” khi có phép kiểm có quyền, có thời điểm kiểm và kiểm lại trong giao dịch ghi sổ.
- Tôn trọng đầy đủ `allow_alternative_item` trên WO/BOM, mã không theo lô, lô chọn tay/bundle, dùng nhiều dòng cùng mã, hết hạn và hai chiều thay thế. Hook hiện tại chỉ xử lý dòng cần tự gán lô; thêm `original_item` chưa giải quyết tất cả các nhánh này.
- Hoàn tất an toàn khi mất mạng/bấm lại: server xử lý nhất quán, khoá lệnh, mã lần thao tác, tra lại kết quả trước khi tạo lần nữa. App còn các đường insert/submit riêng và tạo lệnh/lô phụ trước phiếu cha; chưa có bằng chứng chống trùng/rollback toàn bộ. Không quảng bá là đã chống trùng triệt để.
- Luồng làm tươi có nguyên liệu ở nhiều kho: phần tính kế hoạch phụ còn dùng kho chung; cần kiểm/sửa trước khi hỗ trợ dòng đa kho trong luồng này. Thông tin tồn của màn chi tiết đã sửa không đồng nghĩa toàn bộ preflight làm tươi đã sửa.
- Lệnh cũ bị sai kho: lập báo cáo chỉ đọc gồm header, từng dòng, phiếu chuyển/tiêu hao/hoàn tất, rồi đề xuất sửa từng nhóm cho anh Việt duyệt. Tuyệt đối không update đồng loạt theo mặc định mới.
- Bộ lọc việc cần xử lý như “Quá ngày dự kiến”, “Chưa khai kho”, “Làm dở” có thể bổ sung sau khi thống nhất điều kiện; không dùng màu trạng thái để suy đoán thiếu hàng.


## Vòng sửa sau Claude review 5580151608, ngày 08/09/2026

### B1: lớp kiểm hạn dùng thứ hai

- Căn nguyên: `StockEntry.validate()` gọi `validate_batch()`, tạo gói xuất, rồi gọi `validate_serialized_batch()` kế thừa từ `StockController`. Bản v406 chỉ thay hàm thứ nhất. ERPNext 16.28.0 `controllers/stock_controller.py:321-357` vẫn kiểm `expiry_date < posting_date` với qty dương, docstatus < 2; đây là câu Row #2 trong ảnh Khải.
- `lo_het_han.mo_chot` nay thay thêm phương thức thứ hai trên **riêng StockEntry**, không thay controller chung của chứng từ mua/bán. Giữ nguyên phép kiểm Serial No thuộc Batch từ đúng bản lõi. Không đổi purpose để đánh lừa lõi, không sửa Batch.expiry_date, không bắt rồi bỏ qua ngoại lệ của cả vòng lặp.
- Chỉ bốn mục đích hiện đã cho mở chốt: Manufacture, Material Transfer for Manufacture, Repack, Send to Subcontractor. Mục đích khác đi nguyên hàm lõi. Huỷ ở lớp serial đi nguyên lõi.
- Ô chặn tắt: kiểm lô bị tắt, đọc cả ô batch_no và Serial and Batch Bundle, ghi dòng/mã/lô/ngày hết hạn trong remarks, giữ ghi chú người dùng và không nhân câu qua save/submit. Hỏng đọc Batch/gói thì dừng, không mất vết im lặng. Kiểm tồn, kho, mã hàng, gói và hạch toán vẫn do lõi chạy.
- Ô chặn bật: chặn lô/gói quá hạn với câu tiếng Việt có lô và ngày, vẫn giữ hàm gốc. Lô bị tắt luôn chặn.
- Đã chạy lại **nguyên phương thức core 16.28.0 trích AST**, dữ liệu giả: cả bốn mục đích đỏ trước, xanh sau; Material Receipt vẫn đỏ; bật chốt vẫn đỏ có ngày. Đây chỉ là kiểm phương thức, không thay bằng chứng insert/submit trên Frappe.
- Bốn ca tích hợp mới trong `thu_san_xuat_206.py`: chọn tự động, chọn tay, chọn gói; bật chốt/tắt lô với cả tay và gói. Ca đạt đọc SLE, đúng lô, kho, consumed_qty, GL, sản lượng và remarks; ca chặn lùi savepoint, kiểm không thêm phiếu/sổ/gói. Tạo lô mới còn hạn, nhận thật rồi lùi ngày của chính lô thử trong savepoint. **Chưa chạy các ca mới trên bench của Codex vì máy này không có bench.** Claude cần chạy đỏ-trước/xanh-sau trên bench trước merge/deploy; không lấy kết quả cũ làm bằng chứng cho SHA mới.

### B2: đã đọc trực tiếp site, có khoảng trống cấu hình

Nguồn: UI Item và Item Alternative, phiên Administrator, site `vagabond.s.frappe.cloud`, ngày 08/09. Chỉ đọc, không lưu.

| Món | Mã | Đơn vị gốc | Theo lô | Cho thay thế |
|---|---|---|---|---|
| Bacardi | NVLT00153 | ML | 1 | 0 |
| ISC | NVLT00154 | ML | 1 | 0 |

Danh sách Item Alternative không lọc hiển thị 14/14 bản ghi, không có cặp trên ở cả hai chiều. **Không phải Bacardi thiếu theo lô. Cấu hình thật chưa có cặp thay thế** trong khi fixture Claude đã dựng cặp. `ItemAlternative.has_alternative_item` của ERPNext đòi bật cờ trên mã gốc trước khi lưu cặp; hai chiều cần cờ trên cả hai mã.

UI tồn ISC: Baker - Nguyên liệu: thực 0 ML; Pastry - Nguyên liệu: thực 7.100 ML; Kho tổng 307: thực 700 ML và chờ 3.500 ML. Đã đọc tooltip để tách tồn thực khỏi số đặt/chờ (22.792 ở Baker là số đã đặt, không phải tồn thực). Chưa xác nhận từng lô khả dụng của số tồn này.

Claude cần hoàn tất cấu hình Bacardi -> ISC đúng chiều nghiệp vụ đã chốt cùng anh Việt/Khải, rồi nghiệm thu lệnh mới đúng kho. Không tự suy cặp theo tên và không tự bật hai chiều. Codex chưa thay cấu hình hoặc chứng từ lịch sử trên site. Bằng chứng read-only đã ghi ở issue comment 5580494537.

### P2 và các điểm nhỏ

- Thông báo thiếu hàng nêu mã thay thế có tồn tại kho khác và hướng dẫn kiểm kho nguồn/chuyển kho; không khẳng định cả hệ hết hàng. Tồn Bin là gợi ý, có câu chưa xác nhận lô dùng được.
- Chuyển test chip vào `hanh_vi/kiem_san_xuat_206.js`, gọi trực tiếp trong `kiem_truoc_deploy.sh`; bỏ wrapper Python chạy trùng. Bản trước thực ra đã chạy qua wrapper Python, nay cổng hiển thị rõ.
- Patch `san_xuat_206` ở cuối sau các patch v450.
- Thêm chip Đã đóng cho Work Order; lưu cờ kho chung cùng kho, khôi phục khi mở app, ghi rõ Kho chung do bạn chọn; có test đóng/mở lại và kho không còn hợp lệ.
- Bỏ gán WIP vô hiệu vì core xoá khi skip_transfer.

### Bàn giao Claude

Review SHA mới, chạy lại migration và sáu ca tích hợp #206 trên bench (hai cũ + bốn mới), giữ `chung_tu_con_sot=[]`, `so_luong_lech={}`. Ghi rõ phiên bản Frappe/ERPNext, kết quả đỏ-trước/xanh-sau lỗi hết hạn, rồi kiểm lại fixture Bacardi/ISC và thiếu/sai kho. Đối chiếu cấu hình site theo B2 và quyền/UI thực của Khải. Nếu phát hiện blocker, trả về Codex sửa; không vừa review vừa âm thầm đổi phạm vi. Chỉ chốt release và deploy khi bằng chứng SHA cuối đạt. Issue #206 tiếp tục mở tới khi ca thật của Khải được nghiệm thu.
