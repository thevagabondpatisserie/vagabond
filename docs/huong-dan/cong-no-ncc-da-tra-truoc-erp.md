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

### Đã trả TRƯỚC KHI LÊN ERP (từ v549)

Ví dụ hóa đơn Printeco 04/04/2026: tiền đã ra khỏi ngân hàng trước khi ERP
chạy, số dư ngân hàng mang sang ERP đã trừ khoản này. Anh Việt chốt 01/10/2026
cách ghi: **Nợ 331 (đúng NCC, đúng hóa đơn) / Có tài khoản tạm chờ xử lý đầu
kỳ** (tài khoản loại Temporary của công ty). Không Có 1121, vì sẽ trừ ngân
hàng hai lần. Kế toán kết chuyển tài khoản tạm khi chốt số dư đầu kỳ.

Trên app: Công nợ phải trả → dòng hóa đơn → **Cấn trừ công nợ**. Hóa đơn
không có phiếu chi nào trên ERP thì vào thẳng màn **Đã trả trước khi lên
ERP**; có phiếu chi thì chọn dòng cùng tên ở cuối danh sách.

- Uyên: điền số tiền, ngày đã trả, đính UNC hoặc phiếu chi (bắt buộc), bấm
  **Gửi kế toán duyệt**. Máy lập bút toán NHÁP, dư hóa đơn chưa giảm; dòng
  hóa đơn hiện "Chờ kế toán duyệt". Uyên có thể Rút lại nháp của mình.
- Kế toán: bấm **Duyệt ghi sổ** ngay trên dòng (hoặc Từ chối). Kế toán tự
  lập thì nút là **Ghi sổ cấn trừ**, ghi sổ luôn, UNC không bắt buộc.
- Mất mạng giữa chừng: bấm lại, máy nhận ra lần gửi cũ, không ghi hai lần.
- Ghi nhầm sau khi đã ghi sổ: kế toán hủy bút toán đó trên Desk, dư hóa đơn
  trở lại như cũ.

### Chi trước trên ERP, hóa đơn về sau (từ v551)

Ví dụ Adecco T08/2026 (chị Dung chốt 01/10/2026): hồ sơ Chi từ TK công ty có
khoản đánh dấu **Hóa đơn đến sau**.

- Lúc lập hồ sơ: khoản hóa đơn đến sau KHÔNG cần chọn tài khoản Nợ. Tài
  khoản chi phí đi theo tờ hóa đơn khi về.
- Lúc ghi nhận đã thanh toán: máy lập **phiếu chi trả trước** Nợ 331 đúng
  NCC / Có ngân hàng. Không ghi chi phí, không bút toán tay.
- Hóa đơn về, đã ghi sổ (Nợ chi phí + 1331 / Có 331): trên hồ sơ bấm **Nối
  hóa đơn**, máy phân bổ phiếu chi vào tờ, 331 của tờ về 0.
- Hóa đơn về còn nháp: nối vào hồ sơ, rồi ghi sổ tờ như mọi tờ khác. Lúc ghi
  sổ máy tự phân bổ phiếu chi, không phải bấm gì thêm.
- Nối nhầm: bấm **Gỡ** trên hồ sơ, máy gỡ phần phân bổ, công nợ tờ trở lại,
  phiếu chi trở lại khoản trả trước (không hủy phiếu chi).
- Khoản không có hóa đơn (phí, biên lai nội bộ) vẫn ghi bút toán theo tài
  khoản Nợ đã chọn như trước.
- Hồ sơ đã chi trước v551 (chi phí ngay, bù trừ khi nối) giữ nguyên đường cũ.

### Các trường hợp khác

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
