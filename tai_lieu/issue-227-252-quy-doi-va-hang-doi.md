# Quy đổi nguyên liệu và hàng đợi hóa đơn, #227/#252

Anh Việt duyệt ngày09/09/2026: đúng14 nguyên liệu trong `gram_bom_252.MA_NGUYEN_LIEU`
dùng quy ước1ML=1Gram. Đây là quy ước vận hành riêng, không phải mật độ đo
được và không thêm quy đổi Gram/ML toàn hệ thống.

- Item giữ đơn vị kho ML, thêm Gram hệ số1. Kiểm tại Document không cho
  âm thầm đổi quy ước hoặc đơn vị kho của14mã.
- BOM mới chuẩn hóa ML sang Gram trước khi core tính số. BOM hiện có chỉ
  đổi nhãn uom khi CF1 và qty=stock_qty, bỏ BOM đã hủy, giữ mọi số và bảng
  khai triển. Patch kiểm toàn bộ kế hoạch trước ghi, thêm căn cứ Comment,
  chạy lại không thêm dấu vết. SLE/GL và chứng từ kho cũ không bị viết lại.
- Ba hóa đơn Ngon50845/52022/52590 đã có dữ liệu nguồn nhưng bị đánh dấu
  đã tạo chứng từ dù không có PI; lỗi thuế cũ vẫn nằm trên nguồn. Hàng đợi
  mới đối chiếu chứng từ thật, mở lại dấu sai trong khóa dựng, giữ lý do cũ
  và số lần thử. Tờ có chứng từ kể cả đã hủy không tự tạo lại. HĐĐT bị hủy
  hoặc bị thay thế không được mở lại; không phát hành HĐĐT thật.
- Khi kéo nguồn, một tờ hỏng chỉ rollback tờ đó, các tờ/trang sau tiếp tục.
  Payload sai, trang rỗng giữa chừng, vượt giới hạn trang đều báo chưa đủ.
  Nếu rollback savepoint lỗi thì rollback cả trang, không commit phần dở.
- Tài khoản đầu phiếu Mua dịch vụ áp xuống các dòng dịch vụ không nối PNK,
  kể cả tổng đã khớp. Không ghi đè tài khoản hàng kho/PNK. Chạy ở server
  trước tính và sau mặc định Món, kiểm tài khoản bằng hàm core. Desk phản
  ánh lựa chọn ngay trên dòng; đổi lựa chọn trong lúc tra Món không áp giá
  trị cũ. Không đổi số lượng, đơn giá hoặc tổng tiền để làm khớp tài khoản.

Phạm vi kiểm: hồi quy vòng kéo bằng hàm thật với DB giao dịch giả; integration
Item/BOM/WO/Manufacture/SLE/GL/hủy, BOM hai cấp, patch lặp; PI dịch vụ2/8dòng
save-submit-GL; mở lại dấu xong sai trên nguồn thử và giữ PI đã có. Chỉ khi
bench đúng SHA và kiểm site thật đạt mới ghi nhận đã phát hành.

Giới hạn: không tự đoán bao bì HYGI/ôliu; bản ghi nguồn có số nhưng thiếu
chi tiết chưa có chính sách ghi đè toàn bộ dữ liệu. Không nhận là đã sửa
hóa đơn người dùng chỉ vì thêm một ca kiểm hoặc CI xanh. Sim Ba cần xử lý
phiếu cũ riêng theo300Gram/Túi đã đối chiếu với Item và PNK.
