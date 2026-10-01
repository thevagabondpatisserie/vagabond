# Khoản đã trả trước ERP: xử lý công nợ nhà cung cấp

Dành cho Uyên và kế toán. Không tạo lại đơn mua hoặc phiếu nhập kho chỉ để
làm giảm công nợ. Không chuyển tiền thêm cho khoản đã trả.

## 1. Uyên chuẩn bị theo từng hóa đơn

Đối chiếu nhà cung cấp/MST (giữ cả mã chi nhánh), ký hiệu và số hóa đơn,
ngày/năm, tổng tiền, số đã trả, ngày trả, người/tài khoản thực trả và bằng
chứng chuyển khoản hoặc phiếu chi. Giữ số hóa đơn có số 0 đầu. Ghi riêng
khoản trả từng đợt, trả hộ, hoàn tiền và bù trừ.

Nhãn “Đã chi” trong bảng dò không thay cho chứng từ kế toán. Công thức dò
MST và số hóa đơn có thể trùng giữa các ký hiệu/năm; cộng các dòng cùng khóa
có thể bao gồm dòng chưa chi. Khoản thiếu MST, sai tiền hoặc thiếu bằng chứng
đưa vào danh sách cần xác minh, không ghi nhận hàng loạt.

## 2. ERP đã có chứng từ thanh toán đã ghi sổ

Kế toán kiểm Payment Entry/Journal Entry và tham chiếu hóa đơn trước. Nếu đã
phân bổ đúng mà báo cáo vẫn còn nợ, kiểm cùng công ty, đồng tiền, ngày báo cáo,
chứng từ hủy và sổ thanh toán; không lập thêm phiếu chi để chữa báo cáo.

Nếu còn tiền chưa phân bổ:

- Trong app sau khi bản sửa được phát hành: Công nợ phải trả → tìm NCC hoặc
  số hóa đơn → Cấn trừ công nợ. Nút này dành cho
  kế toán, dùng lại luồng cấn cọc đã có. Chọn phiếu cọc đã ghi sổ đúng NCC,
  điền số tiền cần cấn (mặc định tối đa phần còn lại). Có UNC thì đính ngay
  trên màn này; nút Chỉ lưu UNC không làm giảm nợ. Bấm Xác nhận cấn, không
  chuyển tiền rồi kiểm lại số tiền và hóa đơn trong hộp xác nhận.
  Không tạo thêm bút toán ngân hàng. Nếu mất phản hồi, chọn Kiểm lần cấn đang
  chờ, không tạo yêu cầu khác.
- Phiếu cũ không có sao kê SePay, Journal Entry hoặc ngoại tệ: chọn Đối chiếu
  thanh toán lõi (kế toán). Có thể mở màn này trên Desk ngay ở bản hiện tại.
  Chọn công ty, loại đối tác Nhà cung cấp, đúng NCC và tài khoản phải trả.
  Lấy chứng từ chưa đối chiếu; chọn khoản thanh toán và hóa đơn, điền số phân
  bổ đúng bằng chứng, xem bảng phân bổ rồi mới Đối chiếu. Kiểm giới hạn lấy
  hóa đơn/thanh toán của màn lõi nếu không thấy tờ cần chọn; không kết luận
  đã hết nợ chỉ từ danh sách bị cắt.

Cấn cọc trong app yêu cầu sao kê theo quy tắc hiện hành; không tạo sao kê giả
để qua cửa này. Công cụ lõi giữ quyền kế toán và kiểm công ty/đối tác/tài khoản.

## 3. ERP chưa có chứng từ thanh toán

Uyên chuyển bộ bằng chứng cho kế toán. Kế toán kiểm số dư chuyển đổi và sổ
cũ trước khi tạo chứng từ, tránh ghi tiền ra lần hai nếu số dư ngân hàng/quỹ
đã mang khoản chi đó sang ERP.

- Khoản thanh toán thực tế còn thiếu trên sổ ERP: lập chứng từ thanh toán lõi
  phù hợp, chọn đúng NCC và tham chiếu hóa đơn sẵn có, theo ngày/tài khoản đã
  được kế toán xác nhận. Không chọn tài khoản đối ứng theo suy đoán của app.
- Khoản đã nằm trong số dư đầu kỳ, trả hộ cá nhân hoặc bù trừ công nợ: kế toán
  xác định chứng từ điều chỉnh/phân bổ phù hợp với sổ chuyển đổi. Không mặc
  định ghi Có ngân hàng lần nữa; không mặc định dùng 141 hay một NCC trung gian.

Không sửa trực tiếp ô outstanding_amount và không dùng hóa đơn giảm giá giả.
Không hủy chứng từ thật chỉ để tổng hiển thị về 0.

## 4. Kiểm sau thao tác

Tải lại đúng hóa đơn, đối chiếu số phân bổ với số giảm dư. Kiểm báo cáo Accounts
Payable và sổ NCC cùng công ty/ngày/đồng tiền. Hết dư hóa đơn không tự chứng
minh có một lần chuyển khoản mới. Có trả trước chưa cấn hoặc bút toán khác
thì dư tổng hợp NCC có thể khác tổng những hóa đơn còn nợ.

Màn app mới ghi “Dư hóa đơn theo bộ lọc”: chỉ hóa đơn mua thường đã ghi sổ,
không gồm hóa đơn trả hàng, dư âm hay Journal Entry. Các đồng tiền cộng riêng.
Lọc ngày hóa đơn là chọn tập hóa đơn, không tính lại dư tại ngày quá khứ.
Excel dùng cùng bộ lọc, đủ dòng mọi trang, có mã NCC, số hóa đơn và nguồn số.

Nguồn: [Payment Reconciliation](https://docs.frappe.io/erpnext/payment-reconciliation),
[Payment Entry](https://docs.frappe.io/erpnext/payment-entry).
