# Issue #206: kho sản xuất và thao tác desktop

Codex triển khai. Claude review, chạy kiểm trên Frappe và phụ trách deploy theo phân công của anh Việt ngày 08/09/2026. Issue #206 tiếp tục mở tới khi chứng minh ca của Khải đã hết lỗi.

## Hành vi trong bản này

- Món thành phẩm có ô **Kho nguyên liệu mặc định khi sản xuất**, chọn từ Warehouse bằng tìm kiếm. Đây là kho lấy nguyên liệu để làm món đó; không phải kho của từng mã nguyên liệu và không đổi kho nhập thành phẩm. Khai một lần cho các lệnh mới.
- Kho chọn riêng trên lệnh được ưu tiên. Lệnh mới chưa có kho lấy mặc định từ Món, rồi mới tới quy tắc bếp đang có. Không sửa hàng loạt Item, BOM hoặc lệnh cũ. Món dùng chung nhiều công ty cần chọn kho đúng công ty trên từng lệnh; một field không biểu diễn nhiều mặc định theo công ty.
- Hook không đè lại kho đã có trên dòng nguyên liệu theo bếp của thành phẩm. Dòng chọn kho khác có chủ ý được giữ. Đổi header bằng giao diện ERPNext vẫn chạy thao tác điền kho dòng của lõi.
- App tạo lệnh hiển thị kho nguồn trên mỗi món. Chọn kho chung bằng tay áp cho lượt đang thao tác; nút dùng lại kho trên Món cho phép trở lại chế độ mặc định. Thẻ chi tiết đọc tồn theo kho từng dòng, hoặc WIP trong luồng qua WIP. Lỗi đọc tồn không hiện thành tồn 0. Còn lại trừ cả hao hụt.
- Desktop Work Order: chip trạng thái có số đếm, ngày dự kiến hôm nay/ngày mai/7 ngày tới, lọc kho nguồn. Cột món hiển thị tên và mã; rê chuột có kho đầu lệnh và tiến độ. Mở lệnh có khối kho, đã nhập, hao hụt, còn lại và cảnh báo dòng khác kho.
- Production Plan: chip trạng thái và **ngày lập kế hoạch** (không gọi nhầm là ngày sản xuất). BOM: chip lọc bản dùng/bản còn hiệu lực/bản cũ/nháp/huỷ, giữ chip phiên bản sẵn có. Item Alternative: chip tình trạng cấu hình đã kiểm; không coi đây là xác nhận tồn khả dụng.
- Chip dùng bộ lọc/API đếm có quyền của Frappe, giữ bộ lọc khác, không ghi thiết lập của người khác. Số đếm lỗi là `?`. Trạng thái lệnh không xác nhận đủ nguyên liệu.
- Dòng tự thay nguyên liệu lưu `original_item` để ERPNext cộng `consumed_qty` theo mã gốc; giữ lô/kho của nguyên liệu thực dùng.

## Bằng chứng và giới hạn

Đã đối chiếu mã nguồn ERPNext **16.28.0** (`de591661b9ba0bd3f62ac25b99b5c85c723515f6`) và Frappe **16.27.1** (`f33ac3f00ab818e21b25ddbec93efb653fd9aa1b`) theo phiên bản đọc trên màn Installed Applications của site. Chưa deploy bản này lên site.

Cổng máy chạy với `PATH` có Node và `PYTHONPYCACHEPREFIX=/tmp/vgb206-pycache` vì Python hệ thống trên macOS đặt cache ngoài sandbox:

```sh
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
node kiem_san_xuat_206.js
```

Unit test chạy hàm Python thật với dữ liệu giả; test Node chạy script danh sách thật với hợp đồng DOM/Frappe giả. Chúng kiểm được chọn kho, giữ bộ lọc, trạng thái chọn, số đếm lỗi và liên kết mã thay thế. Chúng **không chứng minh** tích hợp ERPNext, quyền thực tế của Khải hoặc bố cục browser thật.

Có thêm `thu_san_xuat_206.py` trong bộ `vagabond.khung.kiem_that`: insert/save/reload Work Order, ghi hai lần Manufacture, đọc SLE/GL/consumed_qty. Chỉ tạo mã thử ngẫu nhiên; dùng savepoint, khoá commit, cấm thông báo của khung sẵn có. **Chưa chạy** vì máy Codex không có site/bench Frappe. Ca mới không theo lô; ca Bacardi/ISC vẫn cần nghiệm thu riêng.

## Claude cần review và cung cấp bằng chứng trước phát hành

1. Đồng bộ với main mới nhất, chọn số APPVER của đợt release, dựng lại bằng `dung_app_bep.py`. v449 đã được nhánh #227 sử dụng trong lúc Codex làm #206; không coi v449 là số release riêng của #206.
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
