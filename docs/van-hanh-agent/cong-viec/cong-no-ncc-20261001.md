# Công nợ NCC và khoản đã trả trước ERP (#391)

Owner code: Codex. Reviewer: Claude. Branch codex/cong-no-ncc, nền 8841c639.
Tiếp triển khai phần màn hình của phương án #392; không đóng #391/#392 vì
snapshot PLE/GL theo ngày, báo cáo thu chi và xử lý dữ liệu cũ còn việc riêng.

## Phạm vi và bất biến

- App đọc PI đã ghi sổ theo quyền get_list, chọn một công ty; mã NCC chỉ đọc.
- Dư PI hiện tại là một chỉ tiêu riêng, không nhận là dư thuần NCC/GL.
  Return/credit/JE xem ở báo cáo lõi, không âm thầm tự bù vào từng hóa đơn.
- Tiền tệ theo Account, không cộng VND với ngoại tệ. Giảm dư không gọi là đã chi.
- Bộ lọc trạng thái/ngày hóa đơn/nhóm/tìm dùng chung màn và Excel. Màn 30 dòng,
  xuất đủ tập; không dùng số trang hoặc số hiển thị làm tổng.
- Dùng lại hsMoCanCoc và hsThuLaiCanCoc, quyền FIN và khóa/idempotency cũ giữ
  nguyên. Không thêm API ghi tiền; không đọc Excel để tạo chứng từ.
- Chứng từ cũ không có sao kê: hướng dẫn kế toán dùng Payment Reconciliation
  lõi hoặc kiểm chứng từ chuyển đổi. Không nới cửa cấn cọc/khớp sao kê.

## Giao diện

Khung frame/card/dsCongCu/dsCongCuNoi/sheet/tienTrinhPhieu có sẵn. Thứ tự:
nhãn nguồn + tổng → công ty → trạng thái/ngày/tìm/Excel → nhóm NCC → hướng dẫn
khoản đã trả → danh sách → trang trước/sau → báo cáo lõi. Nút mỗi dòng là
“Xem và xử lý”, không có “xóa nợ”. Chặng ghi sổ có chứng từ; hai bước kiểm và
phân bổ không giả màu xanh vì dư giảm; hết dư không được suy thành chuyển tiền.
0 dòng có chỉ dẫn đổi bộ lọc; 1 dòng mở xử lý; nhiều dòng tối đa 30 mỗi trang.
Mạng lỗi có Tải lại. UI readonly cũng có hướng dẫn; chỉ FIN có cửa cấn.

## Kiểm và giới hạn

Có ca Python cho tập lọc, ngày, zero, nhiều tiền tệ, quyền/công ty, phân trang,
Excel đủ dòng/chống công thức. Ca Node chạy màn/khung thật, bấm chip, tìm,
xuất, phân trang, quyền thu mua, gọi cửa cấn, retry, lỗi và rỗng. Dữ liệu giả.
Bản xem local dùng CSS và khung thật, dữ liệu giả, đo 390x844: nút Xem và xử lý nằm từ y698 đến y752.5, chiều rộng trang 390px. Không thay thế
UAT trên site có API mới. Đã mở đọc màn đối chiếu lõi trên production; không
bấm phân bổ/ghi sổ. Chưa chỉnh khoản nào trong file rà soát.

Cổng trước merge: CI/bench trên SHA cuối, Claude review và UAT bằng vai Thu
mua/Kế toán (bao gồm get_list Company/Supplier). Quyền xem dữ liệu không được
nới nếu UAT lỗi; tìm đúng permission nguồn. Chưa merge/deploy.
