# Mẫu nguồn đã tìm lại — 05/10/2026

Anh Việt đã cung cấp nguồn Drive trước đó. Phiên Mac ngày 03/10 có danh mục
329 tài liệu; phiên cloud chỉ tìm trong filesystem riêng nên kết luận thiếu
file là thiếu bàn giao giữa hai môi trường, không phải anh chưa gửi mẫu.

Ngày 05/10 Codex mở lại mẫu của cả bảy nhóm bên dưới bằng kết nối Drive.
Đường dẫn riêng và dữ liệu giao dịch giữ ở nhật ký trên Mac, không đưa vào
repo công khai. Các JSON trong `vagabond/khung/kiem_thu/mau_doi_soat` chỉ có
tiêu đề cột đã quan sát, không chứa giao dịch thật và không phải bản gốc.

| Nguồn | Đã đọc được | Điều phải xử lý trước khi nhận nghiệp vụ |
| --- | --- | --- |
| ShopeeFood | 12 cột, mã đơn/cửa hàng, phí, thực thu; kiểm cả giá trị ô gốc trong Sheet | Có tiền dạng 82.488 với 3 chữ số thập phân trong giá trị số; cần byte CSV hoặc đơn vị nguồn xác thực, không tự nhân 1.000 |
| Payoo QR | 18 cột, mã QR, merchant, phí, ngày giao dịch/thanh toán | Có số tiền lớn bất thường, mã Payoo trống nhưng QR có mã; cần xác minh đơn vị và tổng đối chứng độc lập |
| OnePay | Bảng chi tiết và tổng thanh toán; phí cố định và tổng phí | Không cộng phí cố định thêm lần nữa vào tổng phí; kỳ 17:00–16:59 cần được giữ đúng; đọc cả hoàn tiền |
| Shinhan POS | Bảng merchant và chi tiết 28 cột | Request/Purchase ID đang trống, approval code chưa đủ chứng minh khóa duy nhất; MDF đã gồm VAT |
| GreenSM Ngon | Detail Transactions và Summary, gồm cofund, chiết khấu, thực thu | Không cộng cofund tổng với các cột thành phần; kiểm tổng độc lập từ Summary |
| Be Business | 21 cột, mã chuyến, cước, chiết khấu | Đây là chi phí đi lại; không ánh xạ thành doanh thu bán hàng |
| GrabFood | PDF có đơn hàng, hủy, quảng cáo và tổng | Một số mã đơn bị lỗi ký tự khi trích xuất; không sửa đoán; cần đủ cả phí quảng cáo và đơn tiền mặt/thẻ |

Các file bảng trên Drive đã là Google Sheets chuyển đổi. Xuất raw qua URL
tạm thời chưa tải được về Mac. Đọc được nội dung Sheet không chứng minh đã
kiểm encoding của CSV gốc hoặc đọc được XLS nhị phân gốc.

## Phần đã code ở lượt này

- F1: khóa sự kiện không chứa loại nghiệp vụ. Cùng ID đổi loại thành xung
  đột nội dung cần kiểm, không thành khoản mới.
- F2: lỗi xảy ra sau chuẩn hóa giữ dòng chuẩn để đối chiếu; lỗi trước đó
  không tạo ra dòng chuẩn giả.
- Bộ đọc CSV/TAB nhận bytes, encoding/delimiter khai rõ, giữ số 0 đầu mã,
  tọa độ dòng nhiều dòng, dấu vết SHA256 và cả dòng trống. Sai số cột hoặc
  encoding làm lỗi cả nguồn, không âm thầm nhận phần đã đọc. Có giới hạn
  kích thước/cột/ô/số dòng. Không chạy công thức và không diễn giải tiền.

Đây chưa phải adapter bảy vendor, API upload hay màn hình app. Không có
chứng từ nào được tạo hoặc sửa. `du_nguon` của bộ đọc luôn false: đọc chữ
thành công không chứng minh đủ tiền, đủ kỳ hoặc đã nhận tiền ngân hàng.

## Công việc kế tiếp và chủ việc

Codex tiếp tục adapter theo mẫu, cấu hình merchant/đơn vị/kỳ và tổng nguồn,
lưu File riêng tư qua core, quyền người dùng, khóa chống nhận đồng thời và
màn tải thủ công. Claude review contract và ca lỗi khi có khả năng chạy.
Email để sau theo quyết định hiện tại. Theo yêu cầu tiếp theo của anh Việt, đã đặt APPVER/patch v577 trên nền
v576. Số phiên bản không thay bằng chứng đủ điều kiện phát hành tính năng.
